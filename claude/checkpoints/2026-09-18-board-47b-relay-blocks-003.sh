#!/usr/bin/env bash
# Blind checkpoint v1 — board row 47b (the HOLD card's addressed relay
# blocks, the happy-path desk block, the third ruling). Authored by the
# desk (master 2026-09-18-continue-plan-001) from the request, before
# any implementation exists. Outcome-only: three real applies, one
# fresh scratch fixture each, and the operator-facing stdout is read.
# Writes only under mktemp dirs. Exit 0 PASS, 1 HOLD, 2 fixture error.
set -u
ROOT="$(pwd)"
export PYTHONDONTWRITEBYTECODE=1
python3 - "$ROOT" <<'PY'
import subprocess, sys, tempfile
from pathlib import Path

root = Path(sys.argv[1])
fails = 0
ORACLE_SECRET = "ORACLE-MECHANICS-SECRET-7731"
WORKER_MARK = "WORKER-BAND-MARKER-4412"
NOTES_MARK = "NOTES-MARKER-9921"
LABEL = "oracle-probe-alpha"

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
except Exception as e:
    fixture_error(f"cannot import tests/harness.py from the staged tree: {e!r}")

def scenario(slug, cp_verdict, cp_exit, worker_exit, notes=None):
    """One fresh fixture: pack a checkpointed session, apply a response,
    return (apply exit code, stdout, sid)."""
    tmp = Path(tempfile.mkdtemp(prefix=f"cp47b-{slug}-"))
    home = H.make_sandbox_home(tmp)
    install = H.make_install(tmp)
    repo = H.make_repo(tmp, home)
    env = H.bale_env(home, tmp)
    def git(*a):
        return subprocess.run(["git", *a], cwd=repo, env=env,
                              capture_output=True, text=True)
    git("config", "user.name", "Checkpoint 47b")
    git("config", "user.email", "cp47b@example.invalid")
    (repo / "bale.toml").write_text(
        '[validation]\nbase = "claude/checkpoints/{sid}.sh"\n',
        encoding="utf-8")
    (repo / ".gitignore").write_text(".bale/\n", encoding="utf-8")
    git("add", "-A")
    if git("commit", "-m", "fixture config").returncode != 0:
        fixture_error(f"{slug}: could not commit the fixture config")
    oracle = tmp / f"oracle-{slug}.sh"
    oracle.write_text(
        "#!/usr/bin/env bash\n"
        f'echo "[{cp_verdict}] {LABEL}"\n'
        f'echo "{ORACLE_SECRET} expected=42 got=41"\n'
        f"exit {cp_exit}\n", encoding="utf-8")
    p = H.run_bale(install,
                   ["pack", f"relay block fixture {slug}", "--slug", slug,
                    "--include", "hello.txt", "--no-readme",
                    "--checkpoint-file", str(oracle)],
                   cwd=repo, env=env)
    sroot = repo / ".bale" / "sessions"
    sids = sorted(d.name for d in sroot.iterdir()
                  if (d / "open").is_file()) if sroot.is_dir() else []
    if p.returncode != 0 or len(sids) != 1:
        fixture_error(f"{slug}: pack did not open one session:\n"
                      + p.stdout[-600:] + p.stderr[-600:])
    sid = sids[0]
    wv = "FAIL" if worker_exit else "PASS"
    rdir = H.build_response_dir(
        tmp / "held dir", sid, summary=f"fixture {slug}",
        entries=[{"path": "hello.txt", "action": "modified",
                  "reason": "fixture rewrite",
                  "data": b"fixture rewrite\n"}],
        validation_sh=("#!/usr/bin/env bash\n"
                       f'echo "{WORKER_MARK}"\n'
                       f'echo "[{wv}] fixture check"\n'
                       f"exit {worker_exit}\n"))
    if notes is not None:
        (rdir / "notes.md").write_text(notes, encoding="utf-8")
    tarball = H.tar_response_dir(rdir)
    r = H.run_bale(install, ["apply", str(tarball)], cwd=repo, env=env)
    return r.returncode, r.stdout, sid

def block(stdout, sid, addressee):
    """The lines strictly between the addressed sentinels, or None when
    the pair is absent, duplicated, or out of order. Strict line
    anchors: a sentinel is a whole line, surrounding whitespace aside."""
    begin = f"=== RELAY BEGIN {sid} to {addressee} ==="
    end = f"=== RELAY END {sid} to {addressee} ==="
    lines = [ln.strip() for ln in stdout.splitlines()]
    b = [i for i, ln in enumerate(lines) if ln == begin]
    e = [i for i, ln in enumerate(lines) if ln == end]
    if len(b) != 1 or len(e) != 1 or e[0] <= b[0]:
        return None
    return "\n".join(lines[b[0] + 1:e[0]])

def send_first(stdout):
    hits = [ln.strip() for ln in stdout.splitlines()
            if ln.strip().startswith("send first:")]
    return hits[0][len("send first:"):].strip() if len(hits) == 1 else None

# -- scenario A: the checkpoint holds, the worker passes ---------------
code, out, sid = scenario("relay-cp-held", "FAIL", 1, 0)
if code != 1:
    fixture_error(f"A: expected a HOLD (exit 1), got exit {code}:\n{out[-800:]}")
desk = block(out, sid, "planner")
wrk = block(out, sid, "worker")
verdict(desk is not None, "A-hold-emits-one-planner-addressed-block")
verdict(desk is not None and LABEL in desk,
        "A-planner-block-names-the-failed-probe")
verdict(desk is not None and ORACLE_SECRET in desk and WORKER_MARK in desk,
        "A-planner-block-inlines-both-log-bands")
verdict(wrk is not None, "A-hold-emits-one-worker-addressed-block")
verdict(wrk is not None and LABEL in wrk and WORKER_MARK in wrk,
        "A-worker-block-carries-label-and-its-own-band")
verdict(wrk is not None and ORACLE_SECRET not in wrk,
        "A-worker-block-leaks-no-checkpoint-output")
verdict(send_first(out) is not None and send_first(out).startswith("planner"),
        "A-checkpoint-hold-routes-planner-first")
verdict(any(ln.strip().startswith("base defect")
            for ln in out.splitlines()),
        "A-next-step-offers-a-base-defect-ruling")

# -- scenario B: the worker's own validation holds ---------------------
code, out, sid = scenario("relay-wk-held", "PASS", 0, 1)
if code != 1:
    fixture_error(f"B: expected a HOLD (exit 1), got exit {code}:\n{out[-800:]}")
desk = block(out, sid, "planner")
wrk = block(out, sid, "worker")
verdict(desk is not None and wrk is not None,
        "B-worker-hold-emits-both-addressed-blocks")
verdict(wrk is not None and WORKER_MARK in wrk and ORACLE_SECRET not in wrk,
        "B-worker-block-has-its-band-and-no-checkpoint-output")
verdict(send_first(out) is not None and send_first(out).startswith("worker"),
        "B-worker-only-hold-routes-worker-first")

# -- scenario C: the happy path ----------------------------------------
code, out, sid = scenario("relay-applied", "PASS", 0, 0,
                          notes=f"# notes\n\n{NOTES_MARK} a judgment call.\n")
if code != 0:
    fixture_error(f"C: expected a clean apply (exit 0), got {code}:\n{out[-800:]}")
desk = block(out, sid, "planner")
verdict(desk is not None and NOTES_MARK in desk,
        "C-applied-emits-a-planner-block-carrying-notes-md")
verdict(block(out, sid, "worker") is None
        and f"RELAY BEGIN {sid} to worker" not in out,
        "C-applied-emits-no-worker-block")

sys.exit(1 if fails else 0)
PY
