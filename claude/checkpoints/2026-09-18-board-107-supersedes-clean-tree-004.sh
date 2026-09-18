#!/usr/bin/env bash
# Blind checkpoint v1 — board row 107 (--supersedes leaves main dirty).
# Authored by the desk (master 2026-09-18-continue-plan-001) from the
# request, before any implementation exists. Outcome-only: it drives a
# real accepted supersession in a scratch repo and reads the tree.
# Writes only under a mktemp dir. Exit 0 PASS, 1 HOLD, 2 fixture error.
set -u
ROOT="$(pwd)"
exec python3 - "$ROOT" <<'PY'
import json, subprocess, sys, tempfile
from pathlib import Path

root = Path(sys.argv[1])
fails = 0

def verdict(ok, label):
    global fails
    print(("[PASS] " if ok else "[FAIL] ") + label, flush=True)
    if not ok:
        fails += 1

def fixture_error(msg):
    print("[ERROR] fixture: " + msg, flush=True)
    sys.exit(2)

try:
    sys.path.insert(0, str(root / "tests"))
    import harness as H
except Exception as e:  # the pty harness is the fixture's one dependency
    fixture_error(f"cannot import tests/harness.py from the staged tree: {e!r}")

tmp = Path(tempfile.mkdtemp(prefix="cp107-"))
try:
    home = H.make_sandbox_home(tmp)
    install = H.make_install(tmp)
    repo = H.make_repo(tmp, home)
    env = H.bale_env(home, tmp)
except Exception as e:
    fixture_error(f"scratch fixture did not build: {e!r}")

def git(*args):
    return subprocess.run(["git", *args], cwd=repo, env=env,
                          capture_output=True, text=True)

# Repo-local identity (bale's own commits need one under a scrubbed env).
git("config", "user.name", "Checkpoint 107")
git("config", "user.email", "cp107@example.invalid")

# The row's scenario: a [validation] base pin, the auto-sweep on, a
# tracked telemetry dir, .bale/ ignored; all committed, tree clean.
(repo / "bale.toml").write_text(
    '[validation]\nbase = "claude/checkpoints/{sid}.sh"\n\n'
    '[apply]\nsweep = true\n', encoding="utf-8")
(repo / ".gitignore").write_text(".bale/\n", encoding="utf-8")
(repo / "claude" / "telemetry").mkdir(parents=True)
(repo / "claude" / "telemetry" / ".gitkeep").write_text("", encoding="utf-8")
git("add", "-A")
if git("commit", "-m", "fixture config").returncode != 0:
    fixture_error("could not commit the fixture config")

def oracle_stub(name):
    p = tmp / name
    p.write_text("#!/usr/bin/env bash\necho '[FAIL] stub'\nexit 1\n",
                 encoding="utf-8")
    return str(p)

def open_sids():
    sroot = repo / ".bale" / "sessions"
    if not sroot.is_dir():
        return []
    return sorted(d.name for d in sroot.iterdir() if (d / "open").is_file())

parent_run = H.run_bale(
    install,
    ["pack", "parent goal", "--slug", "cp107-parent", "--include",
     "hello.txt", "--no-readme", "--checkpoint-file",
     oracle_stub("stub-parent.sh")],
    cwd=repo, env=env)
if parent_run.returncode != 0 or len(open_sids()) != 1:
    fixture_error("the parent pack did not open exactly one session:\n"
                  + parent_run.stdout[-800:] + parent_run.stderr[-800:])
parent = open_sids()[0]

# Commit the parent's 'opened' record, as the operator's tree has it
# (tracked telemetry): the tree is clean going into the supersession.
git("add", "--", "claude/telemetry")
git("commit", "-m", "fixture: track the parent's opened record")
if git("status", "--porcelain").stdout.strip():
    fixture_error("tree not clean before the supersession:\n"
                  + git("status", "--porcelain").stdout)

code, out = H.run_bale_pty(
    install,
    ["pack", "child goal", "--slug", "cp107-child", "--include",
     "hello.txt", "--no-readme", "--checkpoint-file",
     oracle_stub("stub-child.sh"), "--supersedes", parent],
    cwd=repo, env=env, answers="y\n")

verdict(code == 0, "accepted-supersession-pack-exits-0")
children = [s for s in open_sids() if s != parent]
child = children[0] if len(children) == 1 else None
verdict(child is not None and parent not in open_sids(),
        "parent-closed-and-exactly-one-child-open")

rec_rel = f"claude/telemetry/{parent}.json"

def stamped(text):
    try:
        rec = json.loads(text)
    except ValueError:
        return False
    return any(a.get("closure_reason") == "superseded-by-split"
               and a.get("superseded_by") == child
               for a in rec.get("attempts", []))

wt = repo / rec_rel
verdict(child is not None and wt.is_file()
        and stamped(wt.read_text(encoding="utf-8")),
        "parent-record-carries-superseded-by-child")

tracked_dirt = git("status", "--porcelain", "--untracked-files=no").stdout
verdict(tracked_dirt.strip() == "",
        "no-tracked-file-left-modified-after-supersession")
if tracked_dirt.strip():
    print("       tracked dirt: " + tracked_dirt.strip().replace("\n", " | "))

head = git("show", f"HEAD:{rec_rel}")
verdict(child is not None and head.returncode == 0 and stamped(head.stdout),
        "committed-parent-record-carries-superseded-by-child")

sys.exit(1 if fails else 0)
PY
