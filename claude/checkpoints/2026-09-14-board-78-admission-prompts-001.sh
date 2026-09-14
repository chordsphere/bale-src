#!/usr/bin/env bash
# Blind checkpoint — board 78 (admission prompts, composed remedies,
# hook default). Authored blind at the 2026-09-14 master sitting from
# the request, before any implementation exists (TARBALL.md §7;
# PLANNER.md §4). Outcome contracts only; nothing here asserts how.
# Runs with cwd = the staged applied tree, confined, stdin not a TTY.
#
# Probes (each drives the shipped harness on a fresh scratch fixture):
#   drift-remedy-composed        a scope-drift refusal renders a pasteable
#                                remedy: the real tarball filename and a
#                                --allow-out-of-scope per refused path, and
#                                no <tarball>/<path> placeholder anywhere
#   piped-drift-declines         with stdin not a TTY the refusal still
#                                refuses (exit 1) and HEAD is unchanged —
#                                automation never admits silently
#   global-hook-default-accept   a global-layer hook's confirmation prompt
#                                renders with the accept default ([Y/n]);
#                                a project-layer hook, never accepted
#                                before, still renders [y/N]
#
# Exit: 0 all probes pass; 1 a probe failed; 2 the script itself errored.
set -u
command -v python3 >/dev/null 2>&1 || { echo "[ERROR] python3 missing"; exit 2; }
[ -f tests/harness.py ] || { echo "[ERROR] tests/harness.py absent — not the bale-src tree"; exit 2; }

python3 - <<'PYEOF'
import os, re, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, "tests")
from harness import (bale_env, build_response_dir, make_install, make_repo,
                     make_sandbox_home, run_bale, tar_response_dir, run_checked,
                     git_env)

failed = 0
def report(ok, label, detail=""):
    global failed
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f": {detail}" if detail else ""))
    if not ok:
        failed = 1

def head(repo, env):
    r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, env=env,
                       capture_output=True, text=True)
    return r.stdout.strip()

# ---- fixture A: a forecast-narrow session and a drifting response -------
with tempfile.TemporaryDirectory(prefix="cp78-drift-") as td:
    tmp = Path(td)
    home = make_sandbox_home(tmp); install = make_install(tmp)
    repo = make_repo(tmp, home); env = bale_env(home, tmp); genv = git_env(home)
    (repo / "other.txt").write_text("other\n", encoding="utf-8")
    run_checked(["git", "add", "other.txt"], cwd=repo, env=genv)
    run_checked(["git", "commit", "-m", "add other"], cwd=repo, env=genv)
    packed = run_bale(install, ["pack", "cp78 drift fixture goal", "--slug", "cp78-drift",
                                "--include", "hello.txt", "--write", "hello.txt",
                                "--no-readme", "--expects-probe", "no"],
                      cwd=repo, env=env)
    m = re.search(r"(\d{4}-\d{2}-\d{2}-cp78-drift-\d{3})", packed.stdout + packed.stderr)
    if packed.returncode != 0 or not m:
        print("[ERROR] fixture pack failed:", (packed.stdout + packed.stderr)[-800:])
        sys.exit(2)
    sid = m.group(1)
    rdir = build_response_dir(tmp, sid, summary="drifts onto other.txt",
        entries=[{"path": "other.txt", "action": "modified",
                  "reason": "cp78 probe: out-of-forecast edit",
                  "data": b"changed\n"}])
    tarball = tar_response_dir(rdir)
    before = head(repo, genv)
    applied = run_bale(install, ["apply", str(tarball)], cwd=repo, env=env)
    out = applied.stdout + applied.stderr
    after = head(repo, genv)

    # probe 1: composed remedy
    lines = [ln.strip() for ln in out.splitlines()]
    cmd_lines = [ln for ln in lines
                 if "bale apply" in ln and tarball.name in ln
                 and "--allow-out-of-scope" in ln and "other.txt" in ln]
    placeholders = [ln for ln in lines if "<tarball>" in ln or "<path>" in ln]
    report(bool(cmd_lines) and not placeholders, "drift-remedy-composed",
           (f"composed line present ({cmd_lines[0][:90]}...)" if cmd_lines and not placeholders
            else f"composed={bool(cmd_lines)} placeholder-lines={len(placeholders)}"))

    # probe 2: piped decline lands nothing
    report(applied.returncode == 1 and before == after, "piped-drift-declines",
           f"exit={applied.returncode} head-unchanged={before == after}")

# ---- fixture B: global-layer vs project-layer hook prompt defaults -----
with tempfile.TemporaryDirectory(prefix="cp78-hook-") as td:
    tmp = Path(td)
    home = make_sandbox_home(tmp); install = make_install(tmp)
    repo = make_repo(tmp, home); env = bale_env(home, tmp); genv = git_env(home)
    user_dir = install / "user"   # global layer = <install>/user/ (bale_config.GLOBAL_USER_DIR)
    user_dir.mkdir(parents=True, exist_ok=True)
    hook = user_dir / "cp78-hook.sh"
    hook.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8"); hook.chmod(0o755)
    (user_dir / "bale.toml").write_text('[hooks]\npost_pack = "cp78-hook.sh"\n', encoding="utf-8")
    p1 = run_bale(install, ["pack", "cp78 hook fixture goal", "--slug", "cp78-hook",
                            "--include", "hello.txt", "--write", "hello.txt",
                            "--no-readme", "--expects-probe", "no"], cwd=repo, env=env)
    o1 = p1.stdout + p1.stderr
    global_seen = "post_pack (global)" in o1
    global_accept = global_seen and "[Y/n]" in o1
    # project-layer hook, never accepted: still decline-default
    run_bale(install, ["unlock"], cwd=repo, env=env)
    (user_dir / "bale.toml").write_text("", encoding="utf-8")
    phook = repo / "cp78-project-hook.sh"
    phook.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8"); phook.chmod(0o755)
    (repo / "bale.toml").write_text('[hooks]\npost_pack = "cp78-project-hook.sh"\n', encoding="utf-8")
    run_checked(["git", "add", "bale.toml", "cp78-project-hook.sh"], cwd=repo, env=genv)
    run_checked(["git", "commit", "-m", "project hook"], cwd=repo, env=genv)
    p2 = run_bale(install, ["pack", "cp78 hook fixture goal two", "--slug", "cp78-hook2",
                            "--include", "hello.txt", "--write", "hello.txt",
                            "--no-readme", "--expects-probe", "no"], cwd=repo, env=env)
    o2 = p2.stdout + p2.stderr
    project_seen = "post_pack (project)" in o2
    project_decline = project_seen and "[y/N]" in o2 and "[Y/n]" not in o2
    report(global_accept and project_decline, "global-hook-default-accept",
           f"global-seen={global_seen} global-[Y/n]={global_accept} "
           f"project-seen={project_seen} project-[y/N]={project_decline}")

sys.exit(failed)
PYEOF
rc=$?
[ "$rc" -eq 0 ] || [ "$rc" -eq 1 ] || { echo "[ERROR] probe driver exited $rc"; exit 2; }
exit $rc
