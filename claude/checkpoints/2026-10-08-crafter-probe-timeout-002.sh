#!/usr/bin/env bash
# Blind checkpoint, crafter-probe-timeout (v1). Authored by the read-only
# desk 2026-10-08-continue-plan-001 from the request, before the work
# exists. Outcome-only, over the crafter's emissions and the tree: the
# --probe scaffold bounds its wall clock (BALE_PROBE_TIMEOUT; 0 lifts it;
# a cut block still closes with a marker, a true trailer and both
# sentinels; the body's stdin is closed), the two fragment emitters print
# `python3 -I -B -`, the epilogue carries no registry citation,
# TARBALL.md 4.2 and 4.3 carry the two bullets by their bold leads and
# the other four global docs are byte-identical to the request's,
# bin/VERSION is 0.4.52 with its changelog record. Nothing here reads
# how the worker bounded the body.
# Runs from the tree root. Writes only under a mktemp directory it
# removes; runs the crafter and bash with PATH holding no bale, from a
# directory with no bale.toml in reach, so no clipboard is touched.
# Exit 0: every probe passed. Exit 1: a probe failed (the work).
# Exit 2: a control failed or the oracle's own machinery broke.
set -u
export PYTHONDONTWRITEBYTECODE=1
ORACLE_TMP="$(mktemp -d 2>/dev/null || mktemp -d -t ckpt)"
trap 'rm -rf "$ORACLE_TMP"' EXIT

python3 -B -I - "$PWD" "$ORACLE_TMP" <<'PYEOF'
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

DOCS = json.loads(r'''{
 "docs/AGENT.md": "5124250b3d6362ae362801f89e2c0498a6e493c638a398de2f4c3d13d6c12285",
 "docs/DOCS.md": "90cc9aad0670610b7865a54db33975103580cdd3354d000b8db07f8a6e956d0c",
 "docs/CODE.md": "49a145323bfc472a22dd8be56565d6e7767fd1ffbd33c36cda95e7e3e149ab75",
 "docs/PLANNER.md": "22c4f52e73fde726b3ffab8256e2a957a18378093757f8882331315bbb2af82c"
}''')
PLACEHOLDER = [
    '  echo "--- section: TODO-example ---"',
    '  echo "TODO(worker): unfilled probe placeholder — not ready to paste"',
]
BEGIN = "=== PROBE BEGIN ckpt-probe ==="
END = "=== PROBE END ckpt-probe ==="
TRAILER = re.compile(r"^--- integrity: (\d+) lines ---$")
HARD_WALL = 25  # seconds: every behavioural run is itself bounded here

root = Path(sys.argv[1])
tmp = Path(sys.argv[2])
failed = []


def excepthook(exc_type, exc, tb):
    print(f"[CONTROL] the oracle raised {exc_type.__name__}: {exc}")
    sys.exit(20)


sys.excepthook = excepthook


def say(ok, label, why=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + ("" if ok else f": {why}"))
    if not ok:
        failed.append(label)


# --- the detectors ---------------------------------------------------------

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def clean_env():
    """PATH without any directory that holds a `bale`; no PYTHON* leaks."""
    keep = []
    for d in os.environ.get("PATH", "/usr/bin:/bin").split(os.pathsep):
        if d and not (Path(d) / "bale").exists():
            keep.append(d)
    env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
    env["PATH"] = os.pathsep.join(keep) or "/usr/bin:/bin"
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def craft(*args):
    """Run the tree's crafter from a config-free cwd; return stdout. The
    fragment modes take a response directory first; `resp/files` is an
    empty scratch one under the config-free cwd."""
    cwd = tmp / "nocfg"
    (cwd / "resp" / "files").mkdir(parents=True, exist_ok=True)
    r = subprocess.run([sys.executable, "-B", "-I", str(root / "tools" / "craft_response.py"), *args],
                       cwd=cwd, env=clean_env(), capture_output=True, text=True, timeout=HARD_WALL)
    return r.returncode, r.stdout, r.stderr


def splice(scaffold, body_lines):
    """The scaffold with the two placeholder lines replaced by `body_lines`.
    Returns None when the placeholder pair is not there verbatim, in order,
    as the last two lines of probe()'s body."""
    lines = scaffold.split("\n")
    for i in range(len(lines) - 2):
        if lines[i] == PLACEHOLDER[0] and lines[i + 1] == PLACEHOLDER[1] and lines[i + 2] == "}":
            return "\n".join(lines[:i] + list(body_lines) + lines[i + 1 + 1:])
    return None


def run_script(text, name, env_extra=None, stdin_mode="devnull", wall=HARD_WALL):
    """bash the script under a hard wall; return (elapsed, rc, stdout).
    rc is None when the wall hit; the script's whole process group is
    then killed (the oracle signals only what it started)."""
    path = tmp / name
    path.write_text(text, encoding="utf-8")
    env = clean_env()
    env.update(env_extra or {})
    start = time.monotonic()
    feeder = None
    if stdin_mode == "openpipe":
        # a pipe nobody closes: a body that reads inherited stdin would hang
        feeder = subprocess.Popen(["sleep", str(HARD_WALL + 30)], stdout=subprocess.PIPE,
                                  start_new_session=True)
        stdin = feeder.stdout
    else:
        stdin = subprocess.DEVNULL
    proc = subprocess.Popen(["bash", str(path)], stdin=stdin, env=env, cwd=tmp,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            start_new_session=True)
    try:
        out, _ = proc.communicate(timeout=wall)
        rc = proc.returncode
    except subprocess.TimeoutExpired:
        os.killpg(proc.pid, 9)
        proc.wait()
        rc, out = None, b""
    finally:
        if feeder is not None:
            os.killpg(feeder.pid, 9)
            feeder.wait()
    return time.monotonic() - start, rc, out.decode("utf-8", "replace")


def block_shape(out):
    """(ok, why, inner_lines) for a stdout that must hold exactly one
    well-formed block with a true trailer."""
    lines = out.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    if lines.count(BEGIN) != 1 or lines.count(END) != 1:
        return False, "sentinels absent or repeated", []
    b, e = lines.index(BEGIN), lines.index(END)
    if not b < e:
        return False, "END before BEGIN", []
    inner = lines[b + 1:e]
    if not inner:
        return False, "nothing between the sentinels", []
    m = TRAILER.match(inner[-1])
    if not m:
        return False, "last line inside the sentinels is not the integrity trailer", inner
    if int(m.group(1)) != len(inner) - 1:
        return False, f"trailer says {m.group(1)} lines, block holds {len(inner) - 1}", inner
    return True, "", inner[:-1]


# --- control: every detector proves itself on planted input -----------------
try:
    planted = "\n".join([
        "#!/usr/bin/env bash", "probe() {", "  echo x", *PLACEHOLDER, "}", "tail"])
    assert splice(planted, ["  echo y"]) == "\n".join(
        ["#!/usr/bin/env bash", "probe() {", "  echo x", "  echo y", "}", "tail"])
    assert splice(planted.replace(PLACEHOLDER[1], "  echo z"), ["  echo y"]) is None
    good = "\n".join([BEGIN, "a", "b", "--- integrity: 2 lines ---", END, ""])
    assert block_shape(good)[0] and block_shape(good)[2] == ["a", "b"]
    assert not block_shape(good.replace("2 lines", "3 lines"))[0]
    assert not block_shape(good.replace(END, ""))[0]
    quick = "\n".join(["#!/usr/bin/env bash", f'echo "{BEGIN}"', "echo one",
                       "echo '--- integrity: 1 lines ---'", f'echo "{END}"', ""])
    el, rc, out = run_script(quick, "control.sh")
    assert rc == 0 and block_shape(out)[0] and el < HARD_WALL
    hang = "#!/usr/bin/env bash\nread -r x\necho got\n"
    el, rc, out = run_script(hang, "control-hang.sh", stdin_mode="openpipe", wall=3)
    assert rc is None, "the open-pipe stdin did not hang a reading script"
    fake = tmp / "fakebin"
    fake.mkdir(exist_ok=True)
    (fake / "bale").write_text("#!/bin/sh\nexit 0\n")
    os.environ["PATH"] = str(fake) + os.pathsep + os.environ.get("PATH", "/usr/bin:/bin")
    for d in clean_env()["PATH"].split(os.pathsep):
        assert not (Path(d) / "bale").exists(), f"clean_env kept {d}, which holds a bale"
    assert str(fake) not in clean_env()["PATH"]
except AssertionError as e:
    print(f"[CONTROL] a detector failed its planted case: {e!r}")
    sys.exit(20)
print("[CONTROL] splice, block_shape and the bounded runner each catch their planted cases; PATH holds no bale")

# --- 1. version and record -------------------------------------------------
ver = (root / "bin" / "VERSION").read_text(encoding="utf-8").strip() if (root / "bin" / "VERSION").exists() else ""
say(ver == "0.4.52", "bin/VERSION reads 0.4.52", f"reads {ver!r}")
rec_path = root / "claude" / "changelog" / "0.4.52.json"
rec = None
if rec_path.exists():
    try:
        rec = json.loads(rec_path.read_text(encoding="utf-8"))
    except Exception as e:
        rec = {"_error": repr(e)}
ok = (isinstance(rec, dict) and rec.get("version") == "0.4.52"
      and "crafter-probe-timeout" in str(rec.get("session_id", ""))
      and any("tools/craft_response.py" in json.dumps(s) for s in rec.get("surfaces", [])))
say(ok, "claude/changelog/0.4.52.json names this session and tools/craft_response.py",
    "absent" if rec is None else "version, session_id or surfaces do not match")

# --- 2. the scaffold's text --------------------------------------------------
rc, scaffold, err = craft("--probe", "ckpt-probe")
say(rc == 0 and bool(scaffold), "the crafter emits a --probe scaffold", f"rc {rc}, stderr: {err[-200:]}")
header = re.split(r"(?m)^probe\(\) \{", scaffold, maxsplit=1)[0] if scaffold else ""
say("BALE_PROBE_TIMEOUT" in header, "the scaffold's header names BALE_PROBE_TIMEOUT", "absent above probe()")
say("# Read-only: writes nothing anywhere; stdout is the only output." in scaffold,
    "the read-only declaration line is unchanged", "absent")
say(BEGIN in scaffold and END in scaffold and "--- integrity: %s lines ---" in scaffold,
    "the sentinel and trailer lines are unchanged", "one of them is absent or respelled")
say("bale clipboard --block" in scaffold, "the clipboard tail is still emitted", "absent")
say(splice(scaffold, ["  :"]) is not None,
    "the two placeholder lines are byte-identical, in order, last in probe()", "splice found no placeholder pair")

# --- 3. the scaffold's behaviour ---------------------------------------------
spliceable = splice(scaffold, ["  :"]) is not None
if spliceable:
    slow = splice(scaffold, ['  echo "--- section: s1 ---"', "  echo one", "  sleep 30",
                             '  echo "--- section: s2 ---"', "  echo two"])
    el, rc, out = run_script(slow, "slow.sh", {"BALE_PROBE_TIMEOUT": "2"})
    shape_ok, why, inner = block_shape(out)
    say(rc is not None and el < 20, "a body past BALE_PROBE_TIMEOUT=2 returns promptly",
        "still running at the hard wall" if rc is None else f"took {el:.1f}s")
    say(shape_ok, "the cut block is well-formed with a true trailer", why)
    say("one" in inner and "--- section: s1 ---" in inner and "two" not in inner,
        "the cut block keeps the lines printed before the cut and nothing after",
        f"inner: {inner[:6]}")
    say(any("BALE_PROBE_TIMEOUT" in l for l in inner),
        "the cut block carries a marker line naming BALE_PROBE_TIMEOUT", "no such line inside the block")

    free = splice(scaffold, ["  echo alpha", "  sleep 3", "  echo omega"])
    el, rc, out = run_script(free, "free.sh", {"BALE_PROBE_TIMEOUT": "0"})
    shape_ok, why, inner = block_shape(out)
    say(rc == 0 and shape_ok and "omega" in inner and not any("BALE_PROBE_TIMEOUT" in l for l in inner),
        "BALE_PROBE_TIMEOUT=0 runs the body unbounded, no marker",
        f"rc {rc}, shape {why or 'ok'}, inner {inner[:4]}")

    reader = splice(scaffold, ["  read -r x", '  echo "got:${x:-nothing}"'])
    el, rc, out = run_script(reader, "reader.sh", {"BALE_PROBE_TIMEOUT": "0"}, stdin_mode="openpipe")
    shape_ok, why, inner = block_shape(out)
    say(rc is not None and el < 20 and shape_ok and any(l.startswith("got:") for l in inner),
        "a body that reads stdin does not block on an open pipe (stdin is closed for the body)",
        "hung" if rc is None else f"rc {rc}, shape {why or 'ok'}, inner {inner[:4]}")

    quick = splice(scaffold, ["  echo quick"])
    el, rc, out = run_script(quick, "quick.sh")
    shape_ok, why, inner = block_shape(out)
    say(rc == 0 and shape_ok and inner == ["quick"],
        "the default path is unchanged for a quick body", f"rc {rc}, shape {why or 'ok'}, inner {inner}")
else:
    for label in ("a body past BALE_PROBE_TIMEOUT=2 returns promptly",
                  "the cut block is well-formed with a true trailer",
                  "the cut block keeps the lines printed before the cut and nothing after",
                  "the cut block carries a marker line naming BALE_PROBE_TIMEOUT",
                  "BALE_PROBE_TIMEOUT=0 runs the body unbounded, no marker",
                  "a body that reads stdin does not block on an open pipe (stdin is closed for the body)",
                  "the default path is unchanged for a quick body"):
        say(False, label, "not run: no placeholder pair to splice")

# --- 4. the fragment emitters ------------------------------------------------
rc, epi, err = craft("resp", "--validation-epilogue")
say(rc == 0 and epi.count("python3 -I -B -") == 1 and "python3 -B -" not in epi.replace("python3 -I -B -", ""),
    "the epilogue's heredoc runs python3 -I -B - (once, no bare -B)", f"rc {rc}")
say(rc == 0 and "fold-in" not in epi and "008" not in epi,
    "the epilogue carries no registry citation", "fold-in or 008 still emitted")
(tmp / "nocfg" / "claude" / "context" / "adr").mkdir(parents=True, exist_ok=True)
(tmp / "nocfg" / "claude" / "INDEX.md").write_text("# INDEX\n", encoding="utf-8")
rc, docs_out, err = craft("resp", "--doc-assertions", "--index", "claude/INDEX.md", "--prune-reasons")
n_i = docs_out.count("if ! python3 -I -B -")
say(rc == 0 and n_i >= 2 and "if ! python3 -B -" not in docs_out,
    "every --doc-assertions block runs python3 -I -B -", f"rc {rc}, -I blocks {n_i}, stderr: {err[-160:]}")

# --- 5. the docs ---------------------------------------------------------------
tb = (root / "docs" / "TARBALL.md").read_text(encoding="utf-8") if (root / "docs" / "TARBALL.md").exists() else ""
s42 = tb.split("### 4.3 ")[0].split("### 4.2 ")[-1] if "### 4.2 " in tb else ""
s43 = tb.split("### 4.4 ")[0].split("### 4.3 ")[-1] if "### 4.3 " in tb else ""
say("**Bounded wall clock.**" in s42 and "BALE_PROBE_TIMEOUT" in s42,
    "TARBALL.md 4.2 carries the Bounded wall clock bullet naming BALE_PROBE_TIMEOUT", "absent")
say("**Never waits on a terminal.**" in s43, "TARBALL.md 4.3 carries the Never waits on a terminal bullet", "absent")
for rel, h in DOCS.items():
    p = root / rel
    say(p.exists() and sha(p) == h, f"{rel} byte-identical to the request's copy", "bytes differ or file absent")

sys.exit(10 if failed else 0)
PYEOF
rc=$?
# The interpreter's own exits are 0 (pass), 10 (a probe failed) and 20
# (a control failed, or the oracle raised); anything else is the oracle
# breaking, never a verdict on the work.
case "$rc" in
  0) exit 0 ;;
  10) exit 1 ;;
  20) exit 2 ;;
  *) echo "[CONTROL] the oracle's interpreter exited $rc unexpectedly"; exit 2 ;;
esac
