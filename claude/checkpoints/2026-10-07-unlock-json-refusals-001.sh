#!/usr/bin/env bash
# Blind checkpoint — bale-src session `unlock-json-refusals` — v1.
# Authored blind at the read-only sitting 2026-10-06-twine-slip-sitting-006,
# from the session's brief, before the worker exists. Outcome-only: it
# grades what `bale unlock --json` prints and exits, never how.
#
# Runs with the tree under test as the working directory (bale's checkpoint
# contract). Writes ONLY under one fresh `mktemp -d` scratch root (a scratch
# HOME, scratch git repositories, scratch non-repo directories); nothing is
# written under the tree, and no interpreter cache is written anywhere
# (PYTHONDONTWRITEBYTECODE, `python3 -B`). It reads no session, no manifest
# and not its own path, so `bale open --dry-run` can run it before any
# session exists.
#
# Exit codes (TARBALL.md §7.5, read for the checkpoint too): 0 every probe
# passed; 1 at least one probe failed (its label alone on the [FAIL] line,
# detail on the following `  detail:` line); 2 the oracle itself is broken —
# a control that could not make its own detector fire, or any unexpected
# exception.
set -u
export PYTHONDONTWRITEBYTECODE=1
echo "[oracle] unlock-json-refusals v1 — tree: $PWD"
echo "[oracle] writes: one fresh mktemp -d scratch root only (scratch HOME, scratch repos); nothing under the tree"
exec python3 -B - "$PWD" <<'ORACLE'
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import importlib.util
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
BALE = TREE / "bin" / "bale"
EXPECTED_VERSION = "0.4.47"
REASONS = ("hold-branch", "not-open", "several-open", "not-a-repo",
           "integration-json")
OLD_KEYS = ("outcome", "sid", "log", "closure_reason", "session_dir_wiped",
            "branch_preserved", "telemetry", "debris", "sweep")
NEW_KEYS = ("reason", "message", "open_sessions")
NULL_ON_REFUSAL = ("log", "closure_reason", "session_dir_wiped",
                   "telemetry", "debris", "sweep")

# ---------------------------------------------------------------- harness
FAILS = []


def ok(label):
    print(f"[PASS] {label}")


def bad(label, detail):
    FAILS.append(label)
    print(f"[FAIL] {label}")
    for line in str(detail).splitlines() or ["(no detail)"]:
        print(f"  detail: {line}")


def oracle_broken(why):
    print(f"[oracle] CONTROL FAILED — the oracle is defective: {why}")
    sys.stdout.flush()
    os._exit(2)


def excepthook(exc_type, exc, tb):
    import traceback
    print("[oracle] unexpected exception — exit 2, not a verdict on the work")
    traceback.print_exception(exc_type, exc, tb, file=sys.stdout)
    sys.stdout.flush()
    os._exit(2)


sys.excepthook = excepthook

SCRATCH = Path(tempfile.mkdtemp(prefix="oracle-unlock-json-"))
HOME = SCRATCH / "home"
HOME.mkdir()
(HOME / ".gitconfig").write_text(
    "[user]\n\tname = Bale Oracle\n\temail = oracle@example.invalid\n"
    "[init]\n\tdefaultBranch = main\n", encoding="utf-8")
ENV = {
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    "HOME": str(HOME),
    "EDITOR": "/bin/true", "VISUAL": "/bin/true",
    "LANG": os.environ.get("LANG", "C.UTF-8"),
    "PYTHONDONTWRITEBYTECODE": "1",
    "BALE_INSTALL": str(SCRATCH / "install-sandbox"),
    "TMPDIR": str(SCRATCH / "tmp"),
}
(SCRATCH / "tmp").mkdir()
print(f"[oracle] scratch root: {SCRATCH}")
COUNTER = [0]


def sh(cmd, cwd):
    r = subprocess.run(cmd, cwd=str(cwd), env=ENV, capture_output=True,
                       text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"setup command failed: {cmd}\n{r.stderr}")
    return r


def fresh_repo():
    COUNTER[0] += 1
    repo = SCRATCH / f"repo{COUNTER[0]}"
    repo.mkdir()
    sh(["git", "init", "-q", "-b", "main"], repo)
    sh(["git", "config", "user.name", "Bale Oracle"], repo)
    sh(["git", "config", "user.email", "oracle@example.invalid"], repo)
    (repo / "hello.txt").write_text("hello\n", encoding="utf-8")
    (repo / "bale.toml").write_text("[sandbox]\nenabled = false\n",
                                    encoding="utf-8")
    (repo / ".gitignore").write_text(".bale/\n", encoding="utf-8")
    sh(["git", "add", "-A"], repo)
    sh(["git", "commit", "-q", "-m", "init"], repo)
    return repo


def bale(args, cwd):
    return subprocess.run([sys.executable, "-B", str(BALE), *args],
                          cwd=str(cwd), env=ENV, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=120)


def pack_read_only(repo, slug):
    r = bale(["pack", f"fixture {slug}", "--slug", slug, "--read-only",
              "--no-readme", "--json"], repo)
    if r.returncode != 0:
        raise RuntimeError(f"fixture pack failed:\n{r.stderr}")
    return json.loads([ln for ln in r.stdout.splitlines() if ln.strip()][0])["sid"]


# -------------------------------------------------------------- detectors
# Pure functions: text in, defect list out. The probes feed them real
# output; the controls feed them known-bad input and expect defects.

def parse_one_json_line(stdout):
    """(payload, defects): stdout must be exactly one non-empty line that
    parses as a JSON object."""
    lines = [ln for ln in (stdout or "").splitlines() if ln.strip()]
    if len(lines) != 1:
        return None, [f"stdout holds {len(lines)} non-empty line(s), "
                      f"expected exactly one JSON line: {stdout!r}"]
    try:
        payload = json.loads(lines[0])
    except json.JSONDecodeError as e:
        return None, [f"stdout line is not JSON ({e}): {lines[0]!r}"]
    if not isinstance(payload, dict):
        return None, [f"stdout line is not a JSON object: {lines[0]!r}"]
    return payload, []


def error_headline(stderr):
    """The text after the first `[bale] error: ` on stderr, first line."""
    for ln in (stderr or "").splitlines():
        if ln.startswith("[bale] error: "):
            return ln[len("[bale] error: "):].strip()
    return None


def refusal_line_defects(payload, *, reason, sid, open_sessions, stderr):
    d = []
    if payload is None:
        return ["no JSON payload to grade"]
    if payload.get("outcome") != "unlock-refused":
        d.append(f"outcome {payload.get('outcome')!r} != 'unlock-refused'")
    if payload.get("reason") != reason:
        d.append(f"reason {payload.get('reason')!r} != {reason!r}")
    if payload.get("reason") not in REASONS:
        d.append(f"reason {payload.get('reason')!r} outside the closed "
                 f"vocabulary {REASONS}")
    if payload.get("sid") != sid:
        d.append(f"sid {payload.get('sid')!r} != {sid!r}")
    if payload.get("open_sessions") != open_sessions:
        d.append(f"open_sessions {payload.get('open_sessions')!r} != "
                 f"{open_sessions!r}")
    msg = payload.get("message")
    headline = error_headline(stderr)
    if not isinstance(msg, str) or not msg.strip():
        d.append(f"message is not a non-empty string: {msg!r}")
    elif headline is None:
        d.append("stderr carries no `[bale] error: ` line")
    elif msg.strip() != headline:
        d.append(f"message {msg!r} != stderr headline {headline!r}")
    for k in OLD_KEYS + NEW_KEYS:
        if k not in payload:
            d.append(f"key {k!r} missing from the refusal line")
    for k in NULL_ON_REFUSAL:
        if k in payload and payload[k] is not None:
            d.append(f"key {k!r} should be null on a refusal, got "
                     f"{payload[k]!r}")
    if "branch_preserved" in payload and payload["branch_preserved"] is not False:
        d.append(f"branch_preserved should be false on a refusal, got "
                 f"{payload['branch_preserved']!r}")
    return d


def success_line_defects(payload, outcome):
    d = []
    if payload is None:
        return ["no JSON payload to grade"]
    if payload.get("outcome") != outcome:
        d.append(f"outcome {payload.get('outcome')!r} != {outcome!r}")
    for k in OLD_KEYS + NEW_KEYS:
        if k not in payload:
            d.append(f"key {k!r} missing from the {outcome} line")
    for k in ("reason", "message"):
        if payload.get(k) is not None:
            d.append(f"{k} should be null on {outcome!r}, got {payload.get(k)!r}")
    os_ = payload.get("open_sessions")
    if os_ is not None and not isinstance(os_, list):
        d.append(f"open_sessions on {outcome!r} must be null or a list, got {os_!r}")
    return d


def stderr_defects(stderr, must_contain):
    d = []
    if "[bale] error:" not in (stderr or ""):
        d.append("stderr carries no `[bale] error:` line")
    for frag in must_contain:
        if frag not in (stderr or ""):
            d.append(f"stderr lacks the unchanged text {frag!r}")
    return d


def exact_line_defects(stderr, expected_line):
    lines = (stderr or "").splitlines()
    if expected_line not in lines:
        return [f"expected the exact stderr line {expected_line!r}; got "
                f"{lines!r}"]
    return []


def version_defects(text, expected):
    if (text or "").strip() != expected:
        return [f"bin/VERSION reads {text.strip()!r}, expected {expected!r}"]
    return []


def record_defects(record, version, required_paths, validator):
    d = []
    if not isinstance(record, dict):
        return ["changelog record is not a JSON object"]
    errors = validator(record)
    if errors:
        d.append("record fails validate_changelog_record: " + "; ".join(map(str, errors)))
    if record.get("version") != version:
        d.append(f"record version {record.get('version')!r} != {version!r}")
    paths = {row.get("path") for row in record.get("surfaces", []) if isinstance(row, dict)}
    for p in required_paths:
        if p not in paths:
            d.append(f"no surfaces row for {p}")
    return d


def tokens_defects(text, tokens, where):
    return [f"{where} does not mention {t!r}" for t in tokens if t not in (text or "")]


# --------------------------------------------------------------- controls
def controls():
    old_style_unlocked = {"outcome": "unlocked", "sid": "x", "log": "/l",
                          "closure_reason": "abandoned", "session_dir_wiped": True,
                          "branch_preserved": False, "telemetry": None,
                          "debris": None, "sweep": None}
    if not refusal_line_defects(old_style_unlocked, reason="not-open", sid="x",
                                open_sessions=[], stderr="[bale] error: x\n"):
        oracle_broken("refusal_line_defects accepted a 0.4.46-shaped unlocked line")
    payload, defects = parse_one_json_line("")
    if payload is not None or not defects:
        oracle_broken("parse_one_json_line accepted an empty stdout")
    payload, defects = parse_one_json_line('{"a":1}\n{"b":2}\n')
    if not defects:
        oracle_broken("parse_one_json_line accepted two lines")
    good = dict(old_style_unlocked, outcome="unlock-refused", reason="not-open",
                message="session x is not open", open_sessions=[], log=None,
                closure_reason=None, session_dir_wiped=None)
    if refusal_line_defects(good, reason="not-open", sid="x", open_sessions=[],
                            stderr="[bale] error: session x is not open\n"):
        oracle_broken("refusal_line_defects rejected a conforming refusal line: "
                      + "; ".join(refusal_line_defects(good, reason="not-open", sid="x", open_sessions=[], stderr="[bale] error: session x is not open\n")))
    if not refusal_line_defects(dict(good, reason="bogus"), reason="bogus", sid="x",
                                open_sessions=[], stderr="[bale] error: session x is not open\n"):
        oracle_broken("refusal_line_defects accepted a reason outside the vocabulary")
    if not success_line_defects(old_style_unlocked, "unlocked"):
        oracle_broken("success_line_defects accepted an unlocked line without the three new keys")
    if not stderr_defects("nothing here", ["[bale] error:"]):
        oracle_broken("stderr_defects accepted stderr without an error line")
    if not exact_line_defects("[bale] error: other text\n", "[bale] error: expected text"):
        oracle_broken("exact_line_defects accepted a different line")
    if not version_defects("0.4.46\n", EXPECTED_VERSION):
        oracle_broken("version_defects accepted 0.4.46")
    if not record_defects({"version": EXPECTED_VERSION}, EXPECTED_VERSION,
                          ["bin/bale"], lambda r: ["missing surfaces"]):
        oracle_broken("record_defects accepted a record the validator rejects")
    if not tokens_defects("abc", ["unlock-refused"], "x"):
        oracle_broken("tokens_defects accepted text lacking the token")
    print("[oracle] controls: every detector fires on its known-bad input")


# ----------------------------------------------------------------- probes
def probe_not_open():
    repo = fresh_repo()
    a = pack_read_only(repo, "oracle-a")
    expected_line = (f"[bale] error: session no-such-sid is not open; nothing "
                     f"to unlock. Open session(s): {a}.")
    r = bale(["unlock", "no-such-sid", "--json"], repo)
    label = "unlock-refused-not-open: json line, exit 1"
    payload, d = parse_one_json_line(r.stdout)
    d += refusal_line_defects(payload, reason="not-open", sid="no-such-sid",
                              open_sessions=[a], stderr=r.stderr)
    d += exact_line_defects(r.stderr, expected_line)
    if r.returncode != 1:
        d.append(f"exit {r.returncode} != 1")
    bad(label, "\n".join(d)) if d else ok(label)
    h = bale(["unlock", "no-such-sid"], repo)
    label = "unlock-refused-not-open: human mode byte-identical"
    d = exact_line_defects(h.stderr, expected_line)
    if h.stdout != "":
        d.append(f"human-mode stdout not empty: {h.stdout!r}")
    if h.returncode != 1:
        d.append(f"exit {h.returncode} != 1")
    bad(label, "\n".join(d)) if d else ok(label)


def probe_several_open():
    repo = fresh_repo()
    a = pack_read_only(repo, "oracle-a")
    b = pack_read_only(repo, "oracle-b")   # piped stdin declines the sweep
    r = bale(["unlock", "--json"], repo)
    label = "unlock-refused-several-open: json line, exit 1"
    payload, d = parse_one_json_line(r.stdout)
    d += refusal_line_defects(payload, reason="several-open", sid=None,
                              open_sessions=[a, b], stderr=r.stderr)
    d += stderr_defects(r.stderr, ["sessions are open"])
    if r.returncode != 1:
        d.append(f"exit {r.returncode} != 1")
    bad(label, "\n".join(d)) if d else ok(label)
    h = bale(["unlock"], repo)
    label = "unlock-refused-several-open: human mode prints nothing on stdout"
    d = [] if h.stdout == "" and h.returncode == 1 else [
        f"stdout {h.stdout!r}, exit {h.returncode}"]
    bad(label, "\n".join(d)) if d else ok(label)


def probe_hold_branch():
    repo = fresh_repo()
    a = pack_read_only(repo, "oracle-a")
    sh(["git", "branch", f"bale/{a}"], repo)
    r = bale(["unlock", a, "--json"], repo)
    label = "unlock-refused-hold-branch: json line, exit 1, text unchanged"
    payload, d = parse_one_json_line(r.stdout)
    d += refusal_line_defects(payload, reason="hold-branch", sid=a,
                              open_sessions=[a], stderr=r.stderr)
    d += stderr_defects(r.stderr, [f"branch bale/{a} exists"])
    if r.returncode != 1:
        d.append(f"exit {r.returncode} != 1")
    bad(label, "\n".join(d)) if d else ok(label)
    f = bale(["unlock", a, "--force", "--json"], repo)
    label = "unlock --force still unlocks; the line carries the new keys null"
    payload, d = parse_one_json_line(f.stdout)
    d += success_line_defects(payload, "unlocked")
    if payload and payload.get("branch_preserved") is not True:
        d.append("branch_preserved should be true on --force with a branch")
    if f.returncode != 0:
        d.append(f"exit {f.returncode} != 0")
    bad(label, "\n".join(d)) if d else ok(label)


def probe_not_a_repo():
    COUNTER[0] += 1
    d_ = SCRATCH / f"plain{COUNTER[0]}"
    d_.mkdir()
    r = bale(["unlock", "--json"], d_)
    label = "unlock-refused-not-a-repo: json line, exit 1"
    payload, d = parse_one_json_line(r.stdout)
    d += refusal_line_defects(payload, reason="not-a-repo", sid=None,
                              open_sessions=None, stderr=r.stderr)
    d += stderr_defects(r.stderr, ["not in a git repo"])
    if r.returncode != 1:
        d.append(f"exit {r.returncode} != 1")
    bad(label, "\n".join(d)) if d else ok(label)


def probe_integration_json():
    repo = fresh_repo()
    a = pack_read_only(repo, "oracle-a")
    r = bale(["unlock", "--integration", "--json"], repo)
    label = "unlock-refused-integration-json: json line, exit 1"
    payload, d = parse_one_json_line(r.stdout)
    d += refusal_line_defects(payload, reason="integration-json", sid=None,
                              open_sessions=[a], stderr=r.stderr)
    if r.returncode != 1:
        d.append(f"exit {r.returncode} != 1")
    bad(label, "\n".join(d)) if d else ok(label)
    r2 = bale(["unlock", a, "--integration", "--json"], repo)
    label = "unlock-refused-integration-json with a sid: sid echoed"
    payload, d = parse_one_json_line(r2.stdout)
    d += refusal_line_defects(payload, reason="integration-json", sid=a,
                              open_sessions=[a], stderr=r2.stderr)
    if r2.returncode != 1:
        d.append(f"exit {r2.returncode} != 1")
    bad(label, "\n".join(d)) if d else ok(label)
    h = bale(["unlock", "--integration"], repo)
    label = "unlock --integration without --json is untouched (human, exit 0)"
    d = [] if h.returncode == 0 and '"outcome"' not in h.stdout else [
        f"exit {h.returncode}, stdout {h.stdout!r}"]
    bad(label, "\n".join(d)) if d else ok(label)


def probe_success_lines():
    repo = fresh_repo()
    a = pack_read_only(repo, "oracle-a")
    r = bale(["unlock", a, "--json"], repo)
    label = "unlocked line carries reason, message, open_sessions (null)"
    payload, d = parse_one_json_line(r.stdout)
    d += success_line_defects(payload, "unlocked")
    if payload and payload.get("sid") != a:
        d.append(f"sid {payload.get('sid')!r} != {a!r}")
    if r.returncode != 0:
        d.append(f"exit {r.returncode} != 0")
    bad(label, "\n".join(d)) if d else ok(label)
    n = bale(["unlock", "--json"], repo)
    label = "no-op line carries reason, message, open_sessions (null)"
    payload, d = parse_one_json_line(n.stdout)
    d += success_line_defects(payload, "no-op")
    if n.returncode != 0:
        d.append(f"exit {n.returncode} != 0")
    bad(label, "\n".join(d)) if d else ok(label)


def probe_argparse_unchanged():
    repo = fresh_repo()
    r = bale(["unlock", "--no-such-flag", "--json"], repo)
    label = "argparse error still exits 2 with nothing on stdout"
    d = [] if r.returncode == 2 and r.stdout == "" else [
        f"exit {r.returncode}, stdout {r.stdout!r}"]
    bad(label, "\n".join(d)) if d else ok(label)


def probe_version_and_record():
    label = f"bin/VERSION minted {EXPECTED_VERSION}"
    d = version_defects((TREE / "bin" / "VERSION").read_text(encoding="utf-8"),
                        EXPECTED_VERSION)
    v = bale(["--version"], SCRATCH)
    if v.stdout.strip() != f"bale {EXPECTED_VERSION}":
        d.append(f"`bale --version` printed {v.stdout.strip()!r}")
    bad(label, "\n".join(d)) if d else ok(label)
    label = f"claude/changelog/{EXPECTED_VERSION}.json exists, validates, names the surfaces"
    rec_path = TREE / "claude" / "changelog" / f"{EXPECTED_VERSION}.json"
    if not rec_path.is_file():
        bad(label, f"{rec_path.relative_to(TREE)} is missing")
        return
    spec = importlib.util.spec_from_file_location(
        "bale_validate", TREE / "bin" / "bale_validate.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(TREE / "bin"))
    spec.loader.exec_module(mod)
    try:
        record = json.loads(rec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        bad(label, f"record is not JSON: {e}")
        return
    d = record_defects(record, EXPECTED_VERSION, ["bin/bale", "bin/bale_report.py"],
                       mod.validate_changelog_record)
    bad(label, "\n".join(d)) if d else ok(label)


def probe_docs_and_help():
    h = bale(["unlock", "--help"], SCRATCH)
    label = "`bale unlock --help` names the refusal line (unlock-refused)"
    d = tokens_defects(h.stdout, ["unlock-refused"], "bale unlock --help")
    bad(label, "\n".join(d)) if d else ok(label)
    report = (TREE / "bin" / "bale_report.py").read_text(encoding="utf-8")
    label = "bin/bale_report.py declares unlock-refused and the five reason codes"
    d = tokens_defects(report, ("unlock-refused",) + REASONS, "bin/bale_report.py")
    bad(label, "\n".join(d)) if d else ok(label)
    bale_md = (TREE / "BALE.md").read_text(encoding="utf-8")
    label = "BALE.md names the unlock-refused line"
    d = tokens_defects(bale_md, ["unlock-refused"], "BALE.md")
    bad(label, "\n".join(d)) if d else ok(label)


def main():
    if not BALE.is_file():
        oracle_broken(f"{BALE} is not a file — not run from the tree root?")
    controls()
    for probe in (probe_not_open, probe_several_open, probe_hold_branch,
                  probe_not_a_repo, probe_integration_json,
                  probe_success_lines, probe_argparse_unchanged,
                  probe_version_and_record, probe_docs_and_help):
        probe()
    shutil.rmtree(SCRATCH, ignore_errors=True)
    print(f"[oracle] {len(FAILS)} failed probe(s)")
    sys.stdout.flush()
    os._exit(1 if FAILS else 0)


main()
ORACLE
