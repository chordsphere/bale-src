#!/usr/bin/env bash
# Blind checkpoint, board 104b (pack-side telemetry riders), v1.
# Authored by the master 2026-09-20-continue-plan-006 from the request,
# before any implementation exists. Outcome probes only.
#
# Runs from the staging root (the tree with the response applied).
# Drives the real CLI in fresh scratch repos under one scratch directory
# beside the tree, isolated HOME, python3 -B, removed on exit.
#
# Verdict grammar: "[PASS] label" / "[FAIL] label" / "[SKIP] label", the
# label alone on the verdict line; any detail on a following
# "  detail:" line (labels travel to the worker on a HOLD, detail does
# not).
# Exit: 0 all probes pass; 1 at least one probe failed; 2 the oracle
# itself could not run (a missing anchor, or the control failed).
set -u
exec python3 -B - "$@" <<'PY'
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TREE = Path.cwd()
BALE = TREE / "bin" / "bale"
results = []          # (verdict, label, detail)


def verdict(ok, label, detail=""):
    results.append(("PASS" if ok else "FAIL", label, detail))


def oracle_error(msg):
    print(f"ORACLE ERROR: {msg}")
    sys.exit(2)


# --- anchors: surfaces this oracle reads; absence is the oracle's error
ANCHORS = [
    "bin/bale", "bin/bale_pack.py", "bin/bale_report.py",
    "schemas/telemetry-record.schema.json", "tools/craft_response.py",
    "tools/response_lint.py", "validate.sh", "bin/VERSION",
    "claude/changelog", "tests",
]
for rel in ANCHORS:
    if not (TREE / rel).exists():
        oracle_error(f"anchor missing: {rel}")

SCRATCH = Path(tempfile.mkdtemp(prefix=".ckpt-104b-", dir=str(TREE)))
HOME = SCRATCH / "home"
HOME.mkdir()
ENV = {
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    "HOME": str(HOME),
    "LANG": "C.UTF-8",
    "PYTHONDONTWRITEBYTECODE": "1",
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "ckpt", "GIT_AUTHOR_EMAIL": "ckpt@example.invalid",
    "GIT_COMMITTER_NAME": "ckpt",
    "GIT_COMMITTER_EMAIL": "ckpt@example.invalid",
}


def cleanup():
    shutil.rmtree(SCRATCH, ignore_errors=True)


def sh(args, cwd, stdin=None, timeout=120):
    return subprocess.run(args, cwd=str(cwd), env=ENV, stdin=stdin,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          text=True, timeout=timeout)


def new_repo(name, toml=""):
    repo = SCRATCH / name
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "a.txt").write_text("alpha\n")
    (repo / "notes.txt").write_text("notes\n")
    (repo / ".gitignore").write_text(".bale/\n")
    if toml:
        (repo / "bale.toml").write_text(toml)
    for cmd in (["git", "init", "-q", "-b", "main"],
                ["git", "add", "-A"],
                ["git", "commit", "-q", "-m", "base"]):
        r = sh(cmd, repo)
        if r.returncode != 0:
            oracle_error(f"scratch repo setup failed: {' '.join(cmd)}: "
                         f"{r.stderr.strip()[:300]}")
    return repo


def pack_piped(repo, extra):
    """A piped pack: stdin is not a TTY, so every prompt declines."""
    return sh([sys.executable, "-B", str(BALE), "pack"] + extra, repo,
              stdin=subprocess.DEVNULL)


def pack_tty(repo, extra, feed=b"\n" * 8):
    """A pack whose stdin is a pty (so prompts run and Enter takes each
    default); stdout and stderr stay pipes, so the one JSON line is
    clean."""
    import pty
    master, slave = pty.openpty()
    try:
        p = subprocess.Popen(
            [sys.executable, "-B", str(BALE), "pack"] + extra,
            cwd=str(repo), env=ENV, stdin=slave,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        os.write(master, feed)
        try:
            out, err = p.communicate(timeout=120)
        except subprocess.TimeoutExpired:
            p.kill()
            out, err = p.communicate()
        return p.returncode, out.decode("utf-8", "replace"), \
            err.decode("utf-8", "replace")
    finally:
        os.close(master)
        os.close(slave)


def json_line(stdout):
    for line in reversed(stdout.splitlines()):
        line = line.strip()
        if line.startswith("{"):
            try:
                return json.loads(line)
            except ValueError:
                return None
    return None


def record(repo, sid):
    path = repo / "claude" / "telemetry" / f"{sid}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text())
    except ValueError:
        return None


RO = ["--read-only", "--no-readme", "--json"]

try:
    # ------------------------------------------------------------------
    # Control: a piped read-only pack works and reports one JSON line.
    # ------------------------------------------------------------------
    repo0 = new_repo("s0-plain")
    r0 = pack_piped(repo0, ["control pack", "--slug", "ctl"] + RO)
    j0 = json_line(r0.stdout)
    if r0.returncode != 0 or not j0 or j0.get("outcome") != "packed" \
            or not j0.get("sid"):
        print("control failed: a plain piped read-only pack did not "
              "report outcome packed")
        print(f"  detail: exit {r0.returncode}; stderr tail: "
              f"{r0.stderr.strip()[-400:]}")
        cleanup()
        sys.exit(2)
    sid0 = j0["sid"]

    # --- A. the pack-json keys ---------------------------------------
    verdict("sweep" in j0 and isinstance(j0.get("sweep"), list)
            and j0.get("sweep") == [],
            "pack --json carries a sweep key, an empty list when the pack "
            "closed nothing",
            f"sweep={j0.get('sweep', '<absent>')!r}")
    verdict("include_group" in j0 and j0.get("include_group") is None,
            "pack --json carries an include_group key, null when no group "
            "is configured",
            f"include_group={j0.get('include_group', '<absent>')!r}")

    group_toml = ('[pack]\ninclude_group = "grp"\n'
                  'include_group_triggers = ["src"]\n'
                  'include_group_pulls = ["notes.txt"]\n')
    repo1 = new_repo("s1-group", toml=group_toml)
    r1 = pack_piped(repo1, ["group pack", "--slug", "grp", "--include",
                            "src"] + RO)
    j1 = json_line(r1.stdout) or {}
    verdict(r1.returncode == 0 and j1.get("include_group") is not None,
            "pack --json include_group is non-null when the configured "
            "group engages",
            f"exit {r1.returncode}; include_group="
            f"{j1.get('include_group', '<absent>')!r}")

    # --- B. packed_at on the opened attempt ---------------------------
    man_path = repo0 / ".bale" / "sessions" / sid0 / "manifest.json"
    packed_at = None
    if man_path.is_file():
        packed_at = (json.loads(man_path.read_text())
                     .get("provenance") or {}).get("packed_at")
    rec0 = record(repo0, sid0)
    if not packed_at or rec0 is None:
        cleanup()
        oracle_error("control session left no stamped manifest "
                     "packed_at or no telemetry record to read")
    opened = [a for a in rec0.get("attempts", [])
              if a.get("outcome") == "opened"]
    found = []
    if opened:
        a = opened[0]
        found = [rec0.get("packed_at"), a.get("packed_at"),
                 (a.get("provenance") or {}).get("packed_at")]
    verdict(packed_at in found,
            "a pack's telemetry record carries the request manifest's "
            "packed_at at its open",
            f"manifest packed_at={packed_at!r}; record candidates={found!r}")

    schema = json.loads(
        (TREE / "schemas/telemetry-record.schema.json").read_text())

    def has_property(node, name):
        if isinstance(node, dict):
            props = node.get("properties")
            if isinstance(props, dict) and name in props:
                return True
            return any(has_property(v, name) for v in node.values())
        if isinstance(node, list):
            return any(has_property(v, name) for v in node)
        return False

    verdict(has_property(schema, "packed_at"),
            "the telemetry record schema declares a packed_at property")

    # --- C. the sweeping pack's sid on a swept attempt -----------------
    sweep_toml = "[apply]\nsweep = true\n"
    repo2 = new_repo("s2-sweep", toml=sweep_toml)
    ra = pack_piped(repo2, ["first master", "--slug", "m-one"] + RO)
    ja = json_line(ra.stdout) or {}
    sid_a = ja.get("sid")
    code_b, out_b, err_b = pack_tty(
        repo2, ["second master", "--slug", "m-two"] + RO)
    jb = json_line(out_b) or {}
    sid_b = jb.get("sid")
    rec_a = record(repo2, sid_a) if sid_a else None
    closed = [a for a in (rec_a or {}).get("attempts", [])
              if a.get("closure_reason") == "closed-read-only"]
    if not (sid_a and sid_b and code_b == 0 and closed):
        # The sweep is 0.3.21 behavior; if it did not fire the oracle
        # could not drive the prompt. That is the oracle's problem.
        print("control failed: the second read-only pack did not sweep "
              "the first")
        print(f"  detail: sid_a={sid_a!r} sid_b={sid_b!r} exit={code_b} "
              f"closed_attempts={len(closed)}; stderr tail: "
              f"{err_b.strip()[-400:]}")
        cleanup()
        sys.exit(2)

    names_b = any(isinstance(v, str) and v == sid_b
                  for v in closed[-1].values())
    verdict(names_b,
            "a read-only sweep's closure attempt names the sweeping "
            "pack's session id",
            f"closure attempt keys carrying a sid-like value: "
            f"{[k for k, v in closed[-1].items() if isinstance(v, str) and v.startswith('20')]!r}")

    sweep_b = jb.get("sweep")
    entry_ok = (isinstance(sweep_b, list) and any(
        isinstance(e, dict) and e.get("sid") == sid_a and "status" in e
        for e in sweep_b))
    verdict(entry_ok,
            "the sweeping pack's --json sweep list has an entry for the "
            "session it closed, keyed sid, with a status",
            f"sweep={sweep_b!r}")

    st = sh(["git", "status", "--porcelain", "--",
             f"claude/telemetry/{sid_a}.json"], repo2)
    verdict(st.returncode == 0 and st.stdout.strip() == "",
            "with the auto-sweep on, the swept session's record is left "
            "committed and clean after the sweeping pack",
            f"porcelain={st.stdout.strip()!r}")

    # --- D. the tools' stdlib-only pin ----------------------------------
    K = ["-m", "unittest", "discover", "-s", "tests", "-t", ".", "-k",
         "stdlib_only"]
    ran_re = re.compile(r"^Ran (\d+) tests? in", re.M)

    def run_pin(root):
        r = sh([sys.executable, "-B"] + K, root, timeout=600)
        m = ran_re.search(r.stderr)
        return r.returncode, int(m.group(1)) if m else 0, r.stderr

    code, ran, err = run_pin(TREE)
    pin_ok = code == 0 and ran >= 1
    verdict(pin_ok,
            "a suite selected by -k stdlib_only runs and passes on the "
            "tree",
            f"exit {code}; ran {ran}")

    mirror = SCRATCH / "mirror"
    skip = {".git", ".bale", "claude", SCRATCH.name}
    mirror.mkdir()
    for child in TREE.iterdir():
        if child.name in skip or child.name.startswith(".ckpt-"):
            continue
        if child.is_dir():
            shutil.copytree(child, mirror / child.name, symlinks=True)
        else:
            shutil.copy2(child, mirror / child.name)

    def mutated(rel, line):
        target = mirror / rel
        original = target.read_bytes()
        target.write_bytes(original + line.encode() + b"\n")
        try:
            return run_pin(mirror)
        finally:
            target.write_bytes(original)

    for rel, line, what in (
            ("tools/response_lint.py", "import socket",
             "a network import"),
            ("tools/craft_response.py", "import yaml",
             "a non-stdlib import")):
        if not pin_ok:
            verdict(False,
                    f"that suite fails when {rel} gains {what}",
                    "not run: the pin did not pass on the tree")
            continue
        mcode, mran, _ = mutated(rel, line)
        verdict(mcode != 0 and mran >= 1,
                f"that suite fails when {rel} gains {what}",
                f"exit {mcode}; ran {mran}")

    # --- E. riders -------------------------------------------------------
    def string_constants(rel):
        tree = ast.parse((TREE / rel).read_text())
        return {n.value for n in ast.walk(tree)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)}

    word = "context-packed"
    verdict(word in string_constants("bin/bale_report.py")
            and word not in string_constants("bin/bale_pack.py"),
            "the context-packed outcome word is a string constant in "
            "bin/bale_report.py and no longer one in bin/bale_pack.py")

    repo3 = new_repo("s3-context")
    r3 = sh([sys.executable, "-B", str(BALE), "pack", "--context",
             "--json"], repo3, stdin=subprocess.DEVNULL)
    j3 = json_line(r3.stdout) or {}
    verdict(r3.returncode == 0 and j3.get("outcome") == word
            and all(k in j3 for k in ("tarball", "directory",
                                      "context_files")),
            "bale pack --context --json still reports context-packed "
            "with its tarball, directory and context_files keys",
            f"exit {r3.returncode}; keys={sorted(j3)!r}")

    vlines = (TREE / "validate.sh").read_text().splitlines()
    verdict(any("--context" in ln and "pack" in ln and "--help" in ln
                for ln in vlines),
            "validate.sh checks that pack --help mentions --context")

    # --- F. release -----------------------------------------------------
    def vtuple(s):
        return tuple(int(x) for x in s.strip().split("."))

    version = (TREE / "bin/VERSION").read_text().strip()
    others = []
    for p in (TREE / "claude/changelog").glob("*.json"):
        try:
            others.append((vtuple(p.stem), p))
        except ValueError:
            pass
    own = TREE / "claude/changelog" / f"{version}.json"
    try:
        bumped = vtuple(version) > (0, 4, 39)
        top_other = max(v for v, p in others if p != own)
        successor = vtuple(version) == top_other[:2] + (top_other[2] + 1,)
    except ValueError:
        bumped = successor = False
    own_ok = False
    if own.is_file():
        try:
            rec = json.loads(own.read_text())
            own_ok = rec.get("version") == version and any(
                s.get("path") == "bin/bale_report.py"
                for s in rec.get("surfaces", []))
        except ValueError:
            own_ok = False
    verdict(bumped and successor and own_ok,
            "bin/VERSION is the patch successor of the highest other "
            "changelog record, past 0.4.39, and its own record exists and "
            "lists bin/bale_report.py among its surfaces",
            f"version={version!r} bumped={bumped} successor={successor} "
            f"own_record_ok={own_ok}")
finally:
    cleanup()

failed = 0
for v, label, detail in results:
    print(f"[{v}] {label}")
    if detail and v != "PASS":
        print(f"  detail: {detail}")
    failed += v == "FAIL"
print(f"{len(results) - failed} of {len(results)} probes passed")
sys.exit(1 if failed else 0)
PY
