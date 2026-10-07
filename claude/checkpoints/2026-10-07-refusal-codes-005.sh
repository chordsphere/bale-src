#!/usr/bin/env bash
# Blind checkpoint — bale-src session `refusal-codes` — v1.
# Authored blind at the read-only sitting 2026-10-06-twine-slip-sitting-006
# (its second wave), from the session's brief, before the worker exists.
# Outcome-only: it grades what `bale open --json`, `bale relay --json` and
# `bale revert --json` print on a refusal, and what the second-desk line
# carries, never how the codes are attached.
#
# Runs with the tree under test as the working directory. Writes ONLY under
# one fresh `mktemp -d` scratch root (scratch HOME, scratch repositories,
# scratch bundles); nothing under the tree; no interpreter cache. Reads no
# session, no manifest and not its own path. Starts only its own processes.
#
# Exit codes (TARBALL.md §7.5): 0 all probes pass; 1 a probe failed (label
# alone on the [FAIL] line, detail on `  detail:` lines); 2 the oracle is
# defective — a control could not fire its own detector, or an unexpected
# exception.
set -u
export PYTHONDONTWRITEBYTECODE=1
echo "[oracle] refusal-codes v1 — tree: $PWD"
echo "[oracle] writes: one fresh mktemp -d scratch root only (scratch HOME, scratch repos, scratch bundles); nothing under the tree"
exec python3 -B - "$PWD" <<'ORACLE'
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
BALE = TREE / "bin" / "bale"
CRAFT = TREE / "tools" / "craft_response.py"
EXPECTED_VERSION = "0.4.50"
OPEN_REASONS = ("not-a-repo", "not-found", "not-a-bundle", "manifest-invalid",
                "member-mismatch", "no-validation-base", "gate-refused",
                "defective-oracle", "desk-refused")
RELAY_REASONS = ("not-open", "held-branch", "not-found", "not-an-object",
                 "trailer-mismatch", "wrong-session", "schema", "stale-round",
                 "skipped-round", "planner-round-one", "unresolved-answer",
                 "no-rounds", "unreadable-record")
REVERT_REASONS = ("not-a-repo", "none-open", "several-open", "no-metadata",
                  "no-branch")
REVERT_KEYS = ("outcome", "sid", "log", "closure_reason", "origin_branch",
               "branch_deleted", "lock_cleared", "staging_state", "staging_path",
               "telemetry", "sweep", "reason", "cause")

FAILS = []


def ok(label):
    print(f"[PASS] {label}")


def bad(label, detail):
    FAILS.append(label)
    print(f"[FAIL] {label}")
    for line in str(detail).splitlines() or ["(no detail)"]:
        print(f"  detail: {line}")


def verdict(label, defects):
    bad(label, "\n".join(defects)) if defects else ok(label)


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

SCRATCH = Path(tempfile.mkdtemp(prefix="oracle-refusal-codes-"))
HOME = SCRATCH / "home"
HOME.mkdir()
(HOME / ".gitconfig").write_text(
    "[user]\n\tname = Bale Oracle\n\temail = oracle@example.invalid\n"
    "[init]\n\tdefaultBranch = main\n", encoding="utf-8")
(SCRATCH / "tmp").mkdir()
BUNDLES = SCRATCH / "bundles"
BUNDLES.mkdir()
ENV = {
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    "HOME": str(HOME), "EDITOR": "/bin/true", "VISUAL": "/bin/true",
    "LANG": os.environ.get("LANG", "C.UTF-8"),
    "PYTHONDONTWRITEBYTECODE": "1",
    "BALE_INSTALL": str(SCRATCH / "install-sandbox"),
    "TMPDIR": str(SCRATCH / "tmp"),
}
print(f"[oracle] scratch root: {SCRATCH}")
COUNTER = [0]


def sh(cmd, cwd):
    r = subprocess.run(cmd, cwd=str(cwd), env=ENV, capture_output=True,
                       text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"setup command failed: {cmd}\n{r.stderr}")
    return r


def fresh_repo(*, validation_base=False):
    COUNTER[0] += 1
    repo = SCRATCH / f"repo{COUNTER[0]}"
    repo.mkdir()
    sh(["git", "init", "-q", "-b", "main"], repo)
    sh(["git", "config", "user.name", "Bale Oracle"], repo)
    sh(["git", "config", "user.email", "oracle@example.invalid"], repo)
    (repo / "hello.txt").write_text("hello\n", encoding="utf-8")
    toml = "[sandbox]\nenabled = false\n"
    if validation_base:
        toml += '\n[validation]\nbase = "claude/checkpoints/{sid}.sh"\n'
        (repo / "claude" / "checkpoints").mkdir(parents=True)
        (repo / "claude" / "checkpoints" / ".keep").write_text("")
    (repo / "bale.toml").write_text(toml, encoding="utf-8")
    (repo / ".gitignore").write_text(".bale/\n", encoding="utf-8")
    sh(["git", "add", "-A"], repo)
    sh(["git", "commit", "-q", "-m", "init"], repo)
    return repo


def bale(args, cwd):
    return subprocess.run([sys.executable, "-B", str(BALE), *args],
                          cwd=str(cwd), env=ENV, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=120)


def one_line(stdout):
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    return json.loads(lines[0])


def pack_read_only(repo, slug):
    r = bale(["pack", f"fixture {slug}", "--slug", slug, "--read-only",
              "--no-readme", "--json"], repo)
    if r.returncode != 0:
        raise RuntimeError(f"fixture pack failed:\n{r.stderr}")
    return one_line(r.stdout)["sid"]


def craft_bundle(slug, *, pack_args, checkpoint_text=None):
    COUNTER[0] += 1
    stem = f"2026-10-07-oracle-{slug}-{COUNTER[0]}"
    brief = BUNDLES / f"brief-{stem}.md"
    brief.write_text(f"# Brief — oracle fixture {stem}\n\nA fixture brief.\n", encoding="utf-8")
    argv = [sys.executable, "-B", "-I", str(CRAFT), "--bundle", stem, "--brief",
            str(brief), "--out-dir", str(BUNDLES)]
    if checkpoint_text is not None:
        cp = BUNDLES / f"checkpoint-{stem}.sh"
        cp.write_text(checkpoint_text, encoding="utf-8")
        argv += ["--checkpoint", str(cp)]
    for tok in pack_args:
        argv.append(f"--pack-arg={tok}" if tok.startswith("-") else "--pack-arg")
        if not tok.startswith("-"):
            argv.append(tok)
    r = subprocess.run(argv, cwd=str(BUNDLES), env=ENV, capture_output=True,
                       text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"crafter failed:\n{r.stderr}")
    return BUNDLES / f"{stem}.bale-bundle"


def clarification_manifest(repo, sid):
    p = repo / "m.json"
    p.write_text(json.dumps({
        "response_kind": "clarification", "session_id": sid,
        "questions": [{"question": "Which?", "context": "wiring",
                       "default_assumption": "the first",
                       "why_blocked": "ambiguous"}]}) + "\n", encoding="utf-8")
    return p


# -------------------------------------------------------------- detectors
def parse_one_json_line(stdout):
    lines = [ln for ln in (stdout or "").splitlines() if ln.strip()]
    if len(lines) != 1:
        return None, [f"stdout holds {len(lines)} non-empty line(s), expected "
                      f"exactly one JSON line: {stdout[:300]!r}"]
    try:
        payload = json.loads(lines[0])
    except json.JSONDecodeError as e:
        return None, [f"stdout line is not JSON ({e}): {lines[0][:200]!r}"]
    if not isinstance(payload, dict):
        return None, [f"stdout line is not a JSON object: {lines[0][:200]!r}"]
    return payload, []


def refused_line_defects(payload, *, outcome, reason, vocabulary, sid="any",
                         required_keys=()):
    d = []
    if payload is None:
        return ["no JSON payload to grade"]
    if payload.get("outcome") != outcome:
        d.append(f"outcome {payload.get('outcome')!r} != {outcome!r}")
    if payload.get("reason") != reason:
        d.append(f"reason {payload.get('reason')!r} != {reason!r}")
    if payload.get("reason") not in vocabulary:
        d.append(f"reason {payload.get('reason')!r} outside the closed vocabulary")
    cause = payload.get("cause")
    if not (isinstance(cause, str) and cause.strip()):
        d.append(f"cause is not a non-empty string: {cause!r}")
    if sid != "any" and payload.get("sid") != sid:
        d.append(f"sid {payload.get('sid')!r} != {sid!r}")
    for k in required_keys:
        if k not in payload:
            d.append(f"key {k!r} missing from the refused line")
    return d


def success_line_defects(payload, outcome, *, keys):
    d = []
    if payload is None:
        return ["no JSON payload to grade"]
    if payload.get("outcome") != outcome:
        d.append(f"outcome {payload.get('outcome')!r} != {outcome!r}")
    for k in keys:
        if k not in payload:
            d.append(f"key {k!r} missing")
    if payload.get("reason") is not None:
        d.append(f"reason should be null on {outcome!r}: {payload.get('reason')!r}")
    return d


def exact_line_defects(stderr, expected_line):
    lines = (stderr or "").splitlines()
    return [] if expected_line in lines else [
        f"expected the exact stderr line {expected_line!r}; got {lines[-3:]!r}"]


def no_json_defects(stdout):
    return ["human-mode stdout carries a JSON report line"] if any(
        ln.startswith('{"outcome"') for ln in (stdout or "").splitlines()) else []


def version_defects(text, expected):
    return [] if (text or "").strip() == expected else [
        f"bin/VERSION reads {text.strip()!r}, expected {expected!r}"]


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
    good = {"outcome": "open-refused", "reason": "not-found", "cause": "bundle not found: x", "sid": None}
    if refused_line_defects(good, outcome="open-refused", reason="not-found", vocabulary=OPEN_REASONS):
        oracle_broken("refused_line_defects rejected a conforming refused line")
    if not refused_line_defects({"outcome": "open-refused"}, outcome="open-refused", reason="not-found", vocabulary=OPEN_REASONS):
        oracle_broken("refused_line_defects accepted a line without reason/cause")
    if not refused_line_defects(dict(good, reason="bogus"), outcome="open-refused", reason="bogus", vocabulary=OPEN_REASONS):
        oracle_broken("refused_line_defects accepted a reason outside the vocabulary")
    if not refused_line_defects(dict(good, cause=""), outcome="open-refused", reason="not-found", vocabulary=OPEN_REASONS):
        oracle_broken("refused_line_defects accepted an empty cause")
    p, d = parse_one_json_line("")
    if p is not None or not d:
        oracle_broken("parse_one_json_line accepted empty stdout")
    if not success_line_defects({"outcome": "reverted"}, "reverted", keys=("reason",)):
        oracle_broken("success_line_defects accepted a reverted line without reason")
    if not exact_line_defects("[bale] error: other\n", "[bale] error: expected"):
        oracle_broken("exact_line_defects accepted a different line")
    if not no_json_defects('{"outcome": "x"}\n'):
        oracle_broken("no_json_defects accepted a JSON line on human stdout")
    if not version_defects("0.4.49\n", EXPECTED_VERSION):
        oracle_broken("version_defects accepted 0.4.49")
    if not record_defects({"version": EXPECTED_VERSION}, EXPECTED_VERSION, ["bin/bale"], lambda r: ["x"]):
        oracle_broken("record_defects accepted a record the validator rejects")
    if not tokens_defects("abc", ["open-refused"], "x"):
        oracle_broken("tokens_defects accepted text lacking the token")
    print("[oracle] controls: every detector fires on its known-bad input")


# ----------------------------------------------------------------- probes
def probe_open_refusals():
    repo = fresh_repo()
    cases = []
    r = bale(["open", str(BUNDLES / "no-such.bale-bundle"), "--json"], repo)
    cases.append(("open --json: missing bundle -> open-refused/not-found", r, "not-found"))
    plain = BUNDLES / "plain.tar.gz"
    plain.write_bytes(b"not a bundle")
    r = bale(["open", str(plain), "--json"], repo)
    cases.append(("open --json: wrong suffix -> open-refused/not-a-bundle", r, "not-a-bundle"))
    COUNTER[0] += 1
    plain_dir = SCRATCH / f"plain{COUNTER[0]}"
    plain_dir.mkdir()
    b = craft_bundle("norepo", pack_args=["oracle", "--slug", "oracle-norepo", "--read-only"])
    r = bale(["open", str(b), "--json"], plain_dir)
    cases.append(("open --json: outside a repo -> open-refused/not-a-repo", r, "not-a-repo"))
    b = craft_bundle("gate", pack_args=["oracle", "--slug", "oracle-gate", "--read-only",
                                        "--include", "no-such-file.txt"])
    r = bale(["open", str(b), "--json"], repo)
    cases.append(("open --json: argv gate refusal -> open-refused/gate-refused", r, "gate-refused"))
    cp_bundle = craft_bundle("oracle2", pack_args=["oracle", "--slug", "oracle-oracle2",
                                                   "--write", "hello.txt"],
                             checkpoint_text="#!/usr/bin/env bash\necho '[oracle] broken'\nexit 2\n")
    r = bale(["open", str(cp_bundle), "--json"], repo)
    cases.append(("open --json: no [validation] base -> open-refused/no-validation-base", r, "no-validation-base"))
    repo2 = fresh_repo(validation_base=True)
    r = bale(["open", str(cp_bundle), "--json"], repo2)
    cases.append(("open --json: oracle exits 2 -> open-refused/defective-oracle", r, "defective-oracle"))
    for label, res, reason in cases:
        payload, d = parse_one_json_line(res.stdout)
        d += refused_line_defects(payload, outcome="open-refused", reason=reason,
                                  vocabulary=OPEN_REASONS, required_keys=("bundle", "members"))
        if res.returncode != 1:
            d.append(f"exit {res.returncode} != 1")
        if "[bale] error:" not in res.stderr:
            d.append("stderr lacks the [bale] error: line")
        verdict(label, d)
    h = bale(["open", str(BUNDLES / "no-such.bale-bundle")], repo)
    d = [] if h.returncode == 1 and h.stdout == "" else [f"exit {h.returncode}, stdout {h.stdout!r}"]
    verdict("open refusal without --json: nothing on stdout, exit 1 (unchanged)", d)


def probe_second_desk_tarball():
    repo = fresh_repo()
    b = craft_bundle("desk", pack_args=["oracle", "--slug", "oracle-desk", "--read-only",
                                        "--include", "hello.txt"])
    r1 = bale(["open", str(b), "--json"], repo)
    r2 = bale(["open", str(b), "--json"], repo)
    p1, d = parse_one_json_line(r1.stdout)
    p2, d2 = parse_one_json_line(r2.stdout)
    d += d2
    if p1 and p2:
        if p2.get("outcome") != "second-desk":
            d.append(f"second open outcome {p2.get('outcome')!r}")
        if not (isinstance(p2.get("tarball"), str) and p2["tarball"] == p1.get("tarball")
                and Path(p2["tarball"]).is_file()):
            d.append(f"second-desk tarball {p2.get('tarball')!r} is not the outbox tarball {p1.get('tarball')!r}")
        for k in ("log", "session_dir", "context_files", "branch"):
            if p2.get(k) is not None:
                d.append(f"{k} should still be null on second-desk")
    verdict("open --json second-desk: tarball names the outbox tarball; other pack keys still null", d)


def probe_relay_refusals():
    repo = fresh_repo()
    sid = pack_read_only(repo, "oracle-relay")
    m = clarification_manifest(repo, sid)
    cases = []
    r = bale(["relay", "no-such-sid", str(m), "--json"], repo)
    cases.append(("relay --json: not open -> relay-refused/not-open", r, "not-open"))
    r = bale(["relay", sid, "--json"], repo)
    cases.append(("relay --json: no recorded rounds -> relay-refused/no-rounds", r, "no-rounds"))
    bad_file = repo / "bad.json"
    bad_file.write_text('{"nope": 1}\n', encoding="utf-8")
    r = bale(["relay", sid, str(bad_file), "--json"], repo)
    cases.append(("relay --json: record fails the schema -> relay-refused/schema", r, "schema"))
    block = repo / "block.txt"
    block.write_text(f"BALE EXCHANGE BEGIN {sid}\n# header\n{m.read_text()}# sha256 "
                     + "0" * 64 + "\nBALE EXCHANGE END\n", encoding="utf-8")
    r = bale(["relay", sid, str(block), "--json"], repo)
    cases.append(("relay --json: trailer disagrees with the body -> relay-refused/trailer-mismatch", r, "trailer-mismatch"))
    for label, res, reason in cases:
        payload, d = parse_one_json_line(res.stdout)
        d += refused_line_defects(payload, outcome="relay-refused", reason=reason,
                                  vocabulary=RELAY_REASONS, required_keys=("block", "telemetry", "log"))
        if res.returncode != 1:
            d.append(f"exit {res.returncode} != 1")
        verdict(label, d)
    r = bale(["relay", sid, str(m), "--json"], repo)
    payload, d = parse_one_json_line(r.stdout)
    d += success_line_defects(payload, "relayed", keys=("reason", "cause", "block"))
    verdict("relay --json relayed: the line carries reason (null)", d)


def probe_revert_refusals():
    repo = fresh_repo()
    cases = []
    r = bale(["revert", "--json"], repo)
    cases.append(("revert --json: nothing open -> revert-refused/none-open", r, "none-open", None))
    a = pack_read_only(repo, "oracle-rv-a")
    r = bale(["revert", a, "--json"], repo)
    cases.append(("revert --json: no bale/<sid> branch -> revert-refused/no-branch", r, "no-branch", a))
    bb = pack_read_only(repo, "oracle-rv-b")
    r = bale(["revert", "--json"], repo)
    cases.append(("revert --json: several open, no sid -> revert-refused/several-open", r, "several-open", None))
    COUNTER[0] += 1
    plain_dir = SCRATCH / f"plain{COUNTER[0]}"
    plain_dir.mkdir()
    r = bale(["revert", "--json"], plain_dir)
    cases.append(("revert --json: outside a repo -> revert-refused/not-a-repo", r, "not-a-repo", None))
    for label, res, reason, sid in cases:
        payload, d = parse_one_json_line(res.stdout)
        d += refused_line_defects(payload, outcome="revert-refused", reason=reason,
                                  vocabulary=REVERT_REASONS, sid=sid, required_keys=REVERT_KEYS)
        if res.returncode != 1:
            d.append(f"exit {res.returncode} != 1")
        verdict(label, d)
    expected = (f"[bale] error: no branch bale/{a}. If the session was already applied, "
                f"use `bale rollback {a}` to undo a merged session (v0.2+).")
    h = bale(["revert", a], repo)
    d = exact_line_defects(h.stderr, expected) + no_json_defects(h.stdout)
    if h.returncode != 1:
        d.append(f"exit {h.returncode} != 1")
    verdict("revert refusal without --json: stderr text unchanged, no JSON on stdout", d)


def probe_version_record_docs():
    d = version_defects((TREE / "bin" / "VERSION").read_text(encoding="utf-8"), EXPECTED_VERSION)
    v = bale(["--version"], SCRATCH)
    if v.stdout.strip() != f"bale {EXPECTED_VERSION}":
        d.append(f"`bale --version` printed {v.stdout.strip()!r}")
    verdict(f"bin/VERSION minted {EXPECTED_VERSION}", d)
    label = f"claude/changelog/{EXPECTED_VERSION}.json exists, validates, names the surfaces"
    rec_path = TREE / "claude" / "changelog" / f"{EXPECTED_VERSION}.json"
    if not rec_path.is_file():
        bad(label, f"{rec_path.relative_to(TREE)} is missing")
    else:
        spec = importlib.util.spec_from_file_location("bale_validate", TREE / "bin" / "bale_validate.py")
        mod = importlib.util.module_from_spec(spec)
        sys.path.insert(0, str(TREE / "bin"))
        spec.loader.exec_module(mod)
        try:
            record = json.loads(rec_path.read_text(encoding="utf-8"))
            verdict(label, record_defects(record, EXPECTED_VERSION,
                                          ["bin/bale", "bin/bale_open.py", "bin/bale_relay.py",
                                           "bin/bale_report.py"], mod.validate_changelog_record))
        except json.JSONDecodeError as e:
            bad(label, f"record is not JSON: {e}")
    report = (TREE / "bin" / "bale_report.py").read_text(encoding="utf-8")
    verdict("bin/bale_report.py declares the three outcomes and every reason code",
            tokens_defects(report, ("open-refused", "revert-refused", "relay-refused")
                           + OPEN_REASONS + RELAY_REASONS + REVERT_REASONS, "bin/bale_report.py"))
    for verb, token in (("open", "open-refused"), ("relay", "relay-refused"), ("revert", "revert-refused")):
        h = bale([verb, "--help"], SCRATCH)
        verdict(f"`bale {verb} --help` names {token}", tokens_defects(h.stdout, [token], f"bale {verb} --help"))
    verdict("BALE.md names open-refused and revert-refused",
            tokens_defects((TREE / "BALE.md").read_text(encoding="utf-8"),
                           ["open-refused", "revert-refused"], "BALE.md"))


def main():
    if not BALE.is_file() or not CRAFT.is_file():
        oracle_broken("bin/bale or tools/craft_response.py missing — not run from the tree root?")
    controls()
    for probe in (probe_open_refusals, probe_second_desk_tarball, probe_relay_refusals,
                  probe_revert_refusals, probe_version_record_docs):
        probe()
    shutil.rmtree(SCRATCH, ignore_errors=True)
    print(f"[oracle] {len(FAILS)} failed probe(s)")
    sys.stdout.flush()
    os._exit(1 if FAILS else 0)


main()
ORACLE
