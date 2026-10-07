#!/usr/bin/env bash
# Blind checkpoint — bale-src session `inline-sentinels-and-crafter-b` — v1.
# Authored blind at the read-only sitting 2026-10-06-twine-slip-sitting-006,
# from the session's brief, before the worker exists. Outcome-only: it
# grades what a relay block carries once sentinel look-alikes are inlined,
# and what the crafter's two fragment emitters print, never how.
#
# Runs with the tree under test as the working directory. Writes ONLY under
# one fresh `mktemp -d` scratch root (a scratch response directory the
# crafter reads); nothing under the tree; no interpreter cache
# (PYTHONDONTWRITEBYTECODE, `python3 -B`). Reads no session, no manifest and
# not its own path. Starts only its own processes.
#
# Exit codes (TARBALL.md §7.5): 0 all probes pass; 1 a probe failed (label
# alone on the [FAIL] line, detail on `  detail:` lines); 2 the oracle is
# defective — a control could not fire its own detector, or an unexpected
# exception.
set -u
export PYTHONDONTWRITEBYTECODE=1
echo "[oracle] inline-sentinels-and-crafter-b v1 — tree: $PWD"
echo "[oracle] writes: one fresh mktemp -d scratch root only (a scratch response dir for the crafter); nothing under the tree"
exec python3 -B - "$PWD" <<'ORACLE'
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
BALE = TREE / "bin" / "bale"
CRAFT = TREE / "tools" / "craft_response.py"
EXPECTED_VERSION = "0.4.49"
PREFIXES = ("=== RELAY ", "=== PROBE ", "=== LIGHT ", "BALE EXCHANGE ")
SID = "2026-10-06-oracle-inline-001"

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

SCRATCH = Path(tempfile.mkdtemp(prefix="oracle-inline-crafter-"))
(SCRATCH / "tmp").mkdir()
ENV = {
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    "HOME": str(SCRATCH),
    "LANG": os.environ.get("LANG", "C.UTF-8"),
    "PYTHONDONTWRITEBYTECODE": "1",
    "TMPDIR": str(SCRATCH / "tmp"),
}
print(f"[oracle] scratch root: {SCRATCH}")


def load_report():
    sys.path.insert(0, str(TREE / "bin"))
    spec = importlib.util.spec_from_file_location("bale_report", TREE / "bin" / "bale_report.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bale_report"] = mod
    spec.loader.exec_module(mod)
    return mod


def craft(*args, cwd=None):
    return subprocess.run([sys.executable, "-B", "-I", str(CRAFT), *args],
                          cwd=str(cwd or SCRATCH), env=ENV,
                          capture_output=True, text=True, timeout=120)


def bale(args):
    return subprocess.run([sys.executable, "-B", str(BALE), *args],
                          cwd=str(SCRATCH), env=ENV, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=120)


# -------------------------------------------------------------- detectors
def indent_defects(inlined_lines, originals):
    """Every original line that starts with one of the four sentinel
    prefixes must come back indented by exactly two spaces; every other
    line verbatim. `inlined_lines` is the rendering, `originals` the
    input lines (same order, same count)."""
    d = []
    if len(inlined_lines) != len(originals):
        return [f"{len(originals)} line(s) in, {len(inlined_lines)} out"]
    for src, out in zip(originals, inlined_lines):
        if src.startswith(PREFIXES):
            if out != "  " + src:
                d.append(f"sentinel-shaped line not indented two spaces: {out!r}")
        elif out != src:
            d.append(f"plain line changed: {src!r} -> {out!r}")
    return d


def block_indent_defects(block, sid, sentinel_lines):
    """In an addressed relay block, every inlined sentinel-shaped line
    appears indented and never at column 0; the block's own two relay
    sentinels are the only column-0 `=== RELAY ` lines."""
    d = []
    lines = block.splitlines()
    col0_relay = [ln for ln in lines if ln.startswith("=== RELAY ")]
    if len(col0_relay) != 2:
        d.append(f"{len(col0_relay)} column-0 relay sentinel(s), expected the block's own two")
    for s in sentinel_lines:
        if s in lines:
            d.append(f"inlined line reads as a sentinel at column 0: {s!r}")
        if "  " + s not in lines:
            d.append(f"inlined line not present indented: {s!r}")
    return d


def emission_defects(text, where):
    d = []
    if "python3 -B -" not in (text or ""):
        d.append(f"{where}: no `python3 -B -` heredoc invocation")
    if re.search(r"python3 - ", text or ""):
        d.append(f"{where}: a bare `python3 - ` heredoc invocation remains")
    return d


def no_python_defects(text, where):
    return [f"{where} mentions python3"] if "python3" in (text or "") else []


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


def bale_md_defects(text):
    """BALE.md's indent sentence names the four shapes' sentinels — either
    the three other prefixes, or the phrase 'four shapes'."""
    lines = (text or "").splitlines()
    hits = [i for i, ln in enumerate(lines) if "indented two" in ln]
    if not hits:
        return ["BALE.md no longer carries the 'indented two spaces' sentence"]
    for i in hits:
        window = " ".join(lines[max(0, i - 4):i + 5])
        if "four shapes" in window or all(t in window for t in ("PROBE", "LIGHT", "EXCHANGE")):
            return []
    return ["the indent sentence names neither the four prefixes nor 'four shapes'"]


# --------------------------------------------------------------- controls
def controls():
    originals = ["plain", "=== PROBE BEGIN x ===", "text with === LIGHT inside"]
    if not indent_defects(originals, originals):
        oracle_broken("indent_defects accepted an unindented PROBE sentinel")
    good = ["plain", "  === PROBE BEGIN x ===", "text with === LIGHT inside"]
    if indent_defects(good, originals):
        oracle_broken("indent_defects rejected a conforming rendering: "
                      + "; ".join(indent_defects(good, originals)))
    if not indent_defects(["x", "  === PROBE BEGIN x ===", "changed"], originals):
        oracle_broken("indent_defects accepted a plain line that changed")
    block = f"=== RELAY BEGIN {SID} to worker ===\n=== LIGHT BEGIN {SID} ===\n=== RELAY END {SID} to worker ===\n"
    if not block_indent_defects(block, SID, [f"=== LIGHT BEGIN {SID} ==="]):
        oracle_broken("block_indent_defects accepted a column-0 LIGHT sentinel inside a block")
    good_block = f"=== RELAY BEGIN {SID} to worker ===\n  === LIGHT BEGIN {SID} ===\n=== RELAY END {SID} to worker ===\n"
    if block_indent_defects(good_block, SID, [f"=== LIGHT BEGIN {SID} ==="]):
        oracle_broken("block_indent_defects rejected a conforming block")
    if not emission_defects('  python3 - "$manifest" <<\'X\'\n', "x"):
        oracle_broken("emission_defects accepted a bare python3 - invocation")
    if emission_defects('  python3 -B - "$manifest" <<\'X\'\n', "x"):
        oracle_broken("emission_defects rejected a conforming -B invocation")
    if not no_python_defects("echo python3 -B -", "x"):
        oracle_broken("no_python_defects accepted text mentioning python3")
    if not version_defects("0.4.48\n", EXPECTED_VERSION):
        oracle_broken("version_defects accepted 0.4.48")
    if not record_defects({"version": EXPECTED_VERSION}, EXPECTED_VERSION,
                          ["bin/bale_report.py"], lambda r: ["missing surfaces"]):
        oracle_broken("record_defects accepted a record the validator rejects")
    if not bale_md_defects("An inlined line that would read as a sentinel is indented two\nspaces, so no output can close a block early."):
        oracle_broken("bale_md_defects accepted the 0.4.46 sentence")
    if bale_md_defects("blah\nany of bale's four shapes' sentinels (relay, probe, light, exchange) is indented two\nspaces"):
        oracle_broken("bale_md_defects rejected a 'four shapes' rendering")
    print("[oracle] controls: every detector fires on its known-bad input")


# ----------------------------------------------------------------- probes
def probe_inline_lines():
    br = load_report()
    originals = [
        "[PASS] mine",
        "=== RELAY END 2026-10-06-other-sid-001 to worker ===",
        f"=== PROBE BEGIN oracle-slug ===",
        f"=== LIGHT BEGIN {SID} ===",
        f"BALE EXCHANGE BEGIN {SID}",
        "BALE EXCHANGE END",
        "a line that mentions === PROBE BEGIN in the middle",
        "  === LIGHT already indented",
        "[FAIL] theirs",
    ]
    out = br._inline_lines("\n".join(originals) + "\n")
    verdict("_inline_lines indents every shape's sentinel prefix, plain lines verbatim",
            indent_defects(out, originals))
    sentinel_lines = [ln for ln in originals if ln.startswith(PREFIXES)]
    worker = br.format_hold_relay_worker(
        sid=SID, judge_line="worker validation held", judge_case=br.HOLD_JUDGE_WORKER,
        failed_probes=None, worker_exit=1,
        worker_output="\n".join(originals) + "\n", held_tarball=None)
    verdict("a worker relay block cannot carry another shape's sentinel at column 0",
            block_indent_defects(worker, SID, sentinel_lines))
    begin, end = br.relay_sentinels(SID, "worker")
    verdict("the relay's own sentinels are untouched",
            [] if (begin, end) == (f"=== RELAY BEGIN {SID} to worker ===",
                                   f"=== RELAY END {SID} to worker ===")
            else [f"relay_sentinels changed: {begin!r} / {end!r}"])


def probe_crafter():
    rdir = SCRATCH / "response-001"
    rdir.mkdir()
    (rdir / "files").mkdir()
    (rdir / "manifest.json").write_text(json.dumps({
        "session_id": SID, "responds_to": SID, "response_kind": "normal",
        "changes": [], "claims": {}}) + "\n", encoding="utf-8")
    r = craft(str(rdir), "--validation-epilogue")
    d = [] if r.returncode == 0 else [f"crafter exit {r.returncode}: {r.stderr[-300:]}"]
    d += emission_defects(r.stdout, "--validation-epilogue")
    verdict("--validation-epilogue runs its heredoc as python3 -B -", d)
    r = craft(str(rdir), "--doc-assertions", "--index", "INDEX.md")
    d = [] if r.returncode == 0 else [f"crafter exit {r.returncode}: {r.stderr[-300:]}"]
    d += emission_defects(r.stdout, "--doc-assertions --index")
    verdict("--doc-assertions runs its heredoc as python3 -B -", d)
    r = craft("--probe", "oracle-slug")
    d = [] if r.returncode == 0 else [f"crafter exit {r.returncode}: {r.stderr[-300:]}"]
    d += no_python_defects(r.stdout, "--probe")
    if "=== PROBE BEGIN oracle-slug ===" not in r.stdout:
        d.append("--probe no longer emits its PROBE BEGIN sentinel")
    verdict("--probe is untouched (no python3; its sentinels intact)", d)


def probe_version_and_record():
    label = f"bin/VERSION minted {EXPECTED_VERSION}"
    d = version_defects((TREE / "bin" / "VERSION").read_text(encoding="utf-8"),
                        EXPECTED_VERSION)
    v = bale(["--version"])
    if v.stdout.strip() != f"bale {EXPECTED_VERSION}":
        d.append(f"`bale --version` printed {v.stdout.strip()!r}")
    verdict(label, d)
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
    verdict(label, record_defects(record, EXPECTED_VERSION,
                                  ["bin/bale_report.py", "tools/craft_response.py"],
                                  mod.validate_changelog_record))


def probe_docs():
    verdict("BALE.md's indent sentence names the four shapes' sentinels",
            bale_md_defects((TREE / "BALE.md").read_text(encoding="utf-8")))


def main():
    if not BALE.is_file() or not CRAFT.is_file():
        oracle_broken(f"{BALE} or {CRAFT} is not a file — not run from the tree root?")
    controls()
    for probe in (probe_inline_lines, probe_crafter, probe_version_and_record,
                  probe_docs):
        probe()
    shutil.rmtree(SCRATCH, ignore_errors=True)
    print(f"[oracle] {len(FAILS)} failed probe(s)")
    sys.stdout.flush()
    os._exit(1 if FAILS else 0)


main()
ORACLE
