#!/usr/bin/env bash
# Blind checkpoint — bale-src session `pack-apply-ux` — v1.
# Authored blind at the read-only sitting 2026-10-06-twine-slip-sitting-006
# (its second wave), from the session's brief, before the worker exists.
# Outcome-only: it grades the retry line a HOLD composes, how `bale retry`
# resolves a numbered sibling, and whether `bale pack --context` offers the
# post_pack hook with the tarball in its environment — never how.
#
# Runs with the tree under test as the working directory. Writes ONLY under
# one fresh `mktemp -d` scratch root (scratch HOME, scratch repositories and
# directories); nothing under the tree; no interpreter cache. Reads no
# session, no manifest and not its own path. Starts only its own processes
# (the hook it configures is never accepted: stdin is closed, so every
# prompt declines).
#
# Exit codes (TARBALL.md §7.5): 0 all probes pass; 1 a probe failed (label
# alone on the [FAIL] line, detail on `  detail:` lines); 2 the oracle is
# defective — a control could not fire its own detector, or an unexpected
# exception.
set -u
export PYTHONDONTWRITEBYTECODE=1
echo "[oracle] pack-apply-ux v1 — tree: $PWD"
echo "[oracle] writes: one fresh mktemp -d scratch root only (scratch HOME, scratch repos); nothing under the tree"
exec python3 -B - "$PWD" <<'ORACLE'
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
BALE = TREE / "bin" / "bale"
EXPECTED_VERSION = "0.4.51"
SID = "2026-10-07-oracle-hold-001"

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

SCRATCH = Path(tempfile.mkdtemp(prefix="oracle-pack-apply-ux-"))
HOME = SCRATCH / "home"
HOME.mkdir()
(HOME / ".gitconfig").write_text(
    "[user]\n\tname = Bale Oracle\n\temail = oracle@example.invalid\n"
    "[init]\n\tdefaultBranch = main\n", encoding="utf-8")
(SCRATCH / "tmp").mkdir()
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


def fresh_repo(*, hook=False):
    COUNTER[0] += 1
    repo = SCRATCH / f"repo{COUNTER[0]}"
    repo.mkdir()
    sh(["git", "init", "-q", "-b", "main"], repo)
    sh(["git", "config", "user.name", "Bale Oracle"], repo)
    sh(["git", "config", "user.email", "oracle@example.invalid"], repo)
    (repo / "hello.txt").write_text("hello\n", encoding="utf-8")
    toml = "[sandbox]\nenabled = false\n"
    if hook:
        (repo / "scripts").mkdir()
        (repo / "scripts" / "hook.sh").write_text("#!/bin/sh\necho HOOK RAN\n", encoding="utf-8")
        (repo / "scripts" / "hook.sh").chmod(0o755)
        toml += '\n[hooks]\npost_pack = "scripts/hook.sh"\n'
    (repo / "bale.toml").write_text(toml, encoding="utf-8")
    (repo / ".gitignore").write_text(".bale/\n", encoding="utf-8")
    sh(["git", "add", "-A"], repo)
    sh(["git", "commit", "-q", "-m", "init"], repo)
    return repo


def bale(args, cwd):
    return subprocess.run([sys.executable, "-B", str(BALE), *args],
                          cwd=str(cwd), env=ENV, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=120)


def load_report():
    sys.path.insert(0, str(TREE / "bin"))
    spec = importlib.util.spec_from_file_location("bale_report", TREE / "bin" / "bale_report.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bale_report"] = mod
    spec.loader.exec_module(mod)
    return mod


# -------------------------------------------------------------- detectors
def retry_targets(forks):
    """The tarball argument of every fork's last line (a `bale retry` command)."""
    targets = []
    for fork in forks:
        last = fork["lines"][-1]
        toks = shlex.split(last)
        if len(toks) < 3 or toks[:2] != ["bale", "retry"]:
            targets.append(None)
        else:
            targets.append(toks[2])
    return targets


def numbered_sibling_defects(targets, held, expected_name):
    d = []
    if not targets:
        return ["no forks composed"]
    for t in targets:
        if t is None:
            d.append("a fork's last line is not a `bale retry <tarball>` command")
        elif Path(t).name != expected_name:
            d.append(f"retry line names {Path(t).name!r}, expected {expected_name!r}")
        elif Path(t).parent != Path(held).parent:
            d.append(f"retry line's directory {Path(t).parent} is not the held tarball's")
    return d


def resolved_sibling_defects(output, resolved_name, *, must_not_contain=()):
    d = []
    if resolved_name not in (output or ""):
        d.append(f"the run never names the resolved sibling {resolved_name!r}")
    for frag in must_not_contain:
        if frag in (output or ""):
            d.append(f"the run still says {frag!r}")
    return d


def hook_offer_defects(text, tarball_name):
    d = []
    if "post_pack" not in (text or ""):
        d.append("the run never mentions the post_pack hook")
    m = re.search(r"BALE_TARBALL=(\S+)", text or "")
    if not m:
        d.append("the hook prompt does not show BALE_TARBALL")
    elif Path(m.group(1)).name != tarball_name:
        d.append(f"BALE_TARBALL names {m.group(1)!r}, expected the tarball {tarball_name!r}")
    return d


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
    held = "/x/response-s.tar.gz"
    forks = [{"lines": ["bale retry '/x/response-s.tar.gz' --sid s"]}]
    if not numbered_sibling_defects(retry_targets(forks), held, "response-s (1).tar.gz"):
        oracle_broken("numbered_sibling_defects accepted the held path itself")
    good = [{"lines": ["note", "bale retry '/x/response-s (1).tar.gz' --sid s"]}]
    if numbered_sibling_defects(retry_targets(good), held, "response-s (1).tar.gz"):
        oracle_broken("numbered_sibling_defects rejected a conforming line")
    if not numbered_sibling_defects(retry_targets([{"lines": ["echo hi"]}]), held, "x"):
        oracle_broken("numbered_sibling_defects accepted a fork not ending in bale retry")
    if not resolved_sibling_defects("[bale] error: tarball not found: /x/r (2).tar.gz", "r (1).tar.gz", must_not_contain=("not found",)):
        oracle_broken("resolved_sibling_defects accepted today's not-found text")
    if resolved_sibling_defects("[bale] retry: resolved r (1).tar.gz (newest sibling)", "r (1).tar.gz", must_not_contain=("not found",)):
        oracle_broken("resolved_sibling_defects rejected a conforming resolution line")
    if not hook_offer_defects("[bale] wrote context tarball: /x/context-p.tar.gz", "context-p.tar.gz"):
        oracle_broken("hook_offer_defects accepted a context pack that never offered the hook")
    if hook_offer_defects("  hook:   post_pack (project)\n  env:    BALE_HOOK=post_pack\n          BALE_TARBALL=/x/context-p.tar.gz\n", "context-p.tar.gz"):
        oracle_broken("hook_offer_defects rejected a conforming offer")
    if not version_defects("0.4.50\n", EXPECTED_VERSION):
        oracle_broken("version_defects accepted 0.4.50")
    if not record_defects({"version": EXPECTED_VERSION}, EXPECTED_VERSION, ["bin/bale"], lambda r: ["x"]):
        oracle_broken("record_defects accepted a record the validator rejects")
    if not tokens_defects("abc", ["BALE_TARBALL"], "x"):
        oracle_broken("tokens_defects accepted text lacking the token")
    print("[oracle] controls: every detector fires on its known-bad input")


# ----------------------------------------------------------------- probes
def probe_retry_line():
    br = load_report()
    d1 = SCRATCH / "downloads1"
    d1.mkdir()
    held = d1 / f"response-{SID}.tar.gz"
    held.write_bytes(b"held")
    forks = br.compose_hold_successors(sid=SID, judge_case=br.HOLD_JUDGE_WORKER,
                                       held_tarball=str(held))
    verdict("HOLD retry line names the next numbered sibling: (1) when none exists",
            numbered_sibling_defects(retry_targets(forks), str(held), f"response-{SID} (1).tar.gz"))
    d2 = SCRATCH / "downloads2"
    d2.mkdir()
    held2 = d2 / f"response-{SID}.tar.gz"
    held2.write_bytes(b"held")
    for n in (1, 2):
        (d2 / f"response-{SID} ({n}).tar.gz").write_bytes(b"older retry")
    forks = br.compose_hold_successors(sid=SID, judge_case=br.HOLD_JUDGE_BOTH,
                                       held_tarball=str(held2))
    verdict("HOLD retry line names the next numbered sibling: (3) after (1) and (2)",
            numbered_sibling_defects(retry_targets(forks), str(held2), f"response-{SID} (3).tar.gz"))


def probe_retry_resolution():
    repo = fresh_repo()
    d = SCRATCH / "downloads3"
    d.mkdir()
    old = d / f"response-{SID}.tar.gz"
    old.write_bytes(b"old")
    newer = d / f"response-{SID} (1).tar.gz"
    newer.write_bytes(b"newer")
    now = time.time()
    os.utime(old, (now - 600, now - 600))
    os.utime(newer, (now - 60, now - 60))
    r = bale(["retry", str(d / f"response-{SID} (2).tar.gz")], repo)
    defects = resolved_sibling_defects(r.stdout + r.stderr, f"response-{SID} (1).tar.gz",
                                       must_not_contain=("tarball not found",))
    if r.returncode == 0:
        defects.append("retry exited 0 on a junk tarball")
    verdict("bale retry on a missing numbered name resolves the newest response-<sid> sibling", defects)
    d4 = SCRATCH / "downloads4"
    d4.mkdir()
    r = bale(["retry", str(d4 / f"response-{SID} (2).tar.gz")], repo)
    defects = [] if r.returncode != 0 and "not found" in (r.stdout + r.stderr) else [
        f"exit {r.returncode}; stderr {r.stderr[-200:]!r}"]
    verdict("bale retry with no sibling to resolve still refuses as not found", defects)


def probe_context_pack_hook():
    repo = fresh_repo(hook=True)
    r = bale(["pack", "--context"], repo)
    out = r.stdout + r.stderr
    defects = hook_offer_defects(out, f"context-{repo.name}.tar.gz")
    if r.returncode != 0:
        defects.append(f"exit {r.returncode} != 0")
    if not (repo / ".bale" / "outbox" / f"context-{repo.name}.tar.gz").is_file():
        defects.append("the context tarball was not written")
    if "HOOK RAN" in out:
        defects.append("the hook ran without an accept (stdin was closed)")
    verdict("pack --context offers the configured post_pack hook, BALE_TARBALL naming the context tarball", defects)
    r = bale(["pack", "fixture", "--slug", "oracle-hook", "--read-only", "--no-readme"], repo)
    out = r.stdout + r.stderr
    sid_m = re.search(r"session id:\s+(\S+)", out)
    name = f"request-{sid_m.group(1)}.tar.gz" if sid_m else "request-?.tar.gz"
    verdict("a session pack's hook prompt shows BALE_TARBALL naming the request tarball",
            hook_offer_defects(out, name))
    repo2 = fresh_repo(hook=False)
    r = bale(["pack", "--context"], repo2)
    out = r.stdout + r.stderr
    verdict("pack --context with no hook configured stays silent about hooks",
            [] if r.returncode == 0 and "hook" not in out.lower() else [f"exit {r.returncode}; {out[-300:]!r}"])


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
                                          ["bin/bale", "bin/bale_pack.py", "bin/bale_report.py"],
                                          mod.validate_changelog_record))
        except json.JSONDecodeError as e:
            bad(label, f"record is not JSON: {e}")
    verdict("BALE.md documents BALE_TARBALL and the context pack's hook offer",
            tokens_defects((TREE / "BALE.md").read_text(encoding="utf-8"),
                           ["BALE_TARBALL"], "BALE.md"))


def main():
    if not BALE.is_file():
        oracle_broken("bin/bale missing — not run from the tree root?")
    controls()
    for probe in (probe_retry_line, probe_retry_resolution, probe_context_pack_hook,
                  probe_version_record_docs):
        probe()
    shutil.rmtree(SCRATCH, ignore_errors=True)
    print(f"[oracle] {len(FAILS)} failed probe(s)")
    sys.stdout.flush()
    os._exit(1 if FAILS else 0)


main()
ORACLE
