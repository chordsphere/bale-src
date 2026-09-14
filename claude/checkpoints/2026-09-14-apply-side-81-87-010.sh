#!/usr/bin/env bash
# Blind checkpoint — apply-side session, rows 81 + 87 (resolver half), v1.
# Authored at the 2026-09-14-continue-plan-006 sitting from the
# request, before implementation. Outcome contracts only:
#   1. the three affected suites run green;
#   2. bare `bale apply` resolves and applies with a read-only session
#      and a scoped session both open (the desk's own shape);
#   3. the multi-open refusal text and the two remedy templates are
#      gone (retired preserved text);
#   4. bin/VERSION reads 0.4.29.
# Writes: nothing outside the suites' and the probe's temp dirs.
set -u
status=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; status=1; }
if [ ! -f bin/VERSION ] || [ ! -d tests ]; then
  echo "[FAIL] checkpoint must run at the repo root"; exit 2
fi

# 1. Suites.
for suite in test_apply_preflight test_base_drift test_required_check_gate; do
  out="$(python3 -m unittest discover -s tests -p "$suite.py" 2>&1)"
  if [ $? -eq 0 ] && echo "$out" | grep -q '^OK'; then
    pass "$suite green"
  else
    echo "$out" | tail -n 8; fail "$suite not green"
  fi
done

# 2. End-to-end: two sessions open, bare apply lands the worker's response.
probe_out="$(python3 - <<'PYEOF' 2>&1
import sys, tempfile, shutil
from pathlib import Path
sys.path.insert(0, "tests")
from harness import (make_sandbox_home, make_install, make_repo, git_env,
                     bale_env, run_checked, run_bale, run_bale_pty,
                     build_response_dir, tar_response_dir)
tmp = Path(tempfile.mkdtemp(prefix="ckpt-bare-apply-"))
try:
    home = make_sandbox_home(tmp); install = make_install(tmp)
    repo = make_repo(tmp, home); genv = git_env(home); env = bale_env(home, tmp)
    (repo / "bale.toml").write_text("[sandbox]\nenabled = false\n", encoding="utf-8")
    run_checked(["git", "add", "bale.toml"], cwd=repo, env=genv)
    run_checked(["git", "commit", "-m", "sandbox off"], cwd=repo, env=genv)
    r = run_bale(install, ["pack", "desk session", "--slug", "desk", "--read-only",
                           "--no-readme"], cwd=repo, env=env)
    assert r.returncode == 0, "read-only pack failed:\n" + r.stdout + r.stderr
    r = run_bale(install, ["pack", "worker session", "--slug", "worker",
                           "--include", "hello.txt", "--no-readme"], cwd=repo, env=env)
    assert r.returncode == 0, "scoped pack failed:\n" + r.stdout + r.stderr
    sessions = repo / ".bale" / "sessions"
    open_sids = sorted(d.name for d in sessions.iterdir() if (d / "open").is_file())
    assert len(open_sids) == 2, f"expected two open sessions, saw {open_sids}"
    worker = [s for s in open_sids if "-worker-" in s][0]
    rdir = build_response_dir(tmp / "resp", worker, summary="bare apply probe",
        entries=[{"path": "hello.txt", "action": "modified", "reason": "probe",
                  "data": b"hello from bare apply\n"}])
    tarball = tar_response_dir(rdir)
    shutil.copy(tarball, repo / tarball.name)
    code, out = run_bale_pty(install, ["apply"], cwd=repo, env=env, answers="y\n\n")
    print(out[-1500:])
    assert code == 0, f"bare apply exited {code}"
    assert not (sessions / worker / "open").is_file(), "worker session still open"
    assert (sessions / open_sids[0] / "open").is_file() if "-desk-" in open_sids[0] \
        else (sessions / open_sids[1] / "open").is_file(), "desk session was closed"
    print("PROBE-OK")
finally:
    shutil.rmtree(tmp, ignore_errors=True)
PYEOF
)"
if echo "$probe_out" | grep -q '^PROBE-OK$'; then
  pass "bare apply resolves and lands with a read-only and a scoped session open"
else
  echo "$probe_out" | tail -n 12
  fail "bare apply did not land with two sessions open"
fi

# 3. Retired strings (preserved text).
# Source strings may wrap across adjacent literals; join them before matching.
joined() { python3 -c "import re,sys; print(re.sub(r'\"\s*\n\s*\"','',open(sys.argv[1]).read()))" "$1"; }
retired() { if joined "$1" | grep -Fq -- "$2"; then fail "$1 still contains '$2'"; else pass "$1 no longer contains '$2'"; fi; }
retired bin/bale_apply.py 'is ambiguous with more than one session'
retired bin/bale_report.py '`bale apply <tarball> --accept-base-drift <path>`'
retired bin/bale_report.py '`bale apply <tarball> --allow-missing-required-check'

# 4. Version.
v="$(tr -d '[:space:]' < bin/VERSION)"
if [ "$v" = "0.4.29" ]; then pass "bin/VERSION reads 0.4.29"; else fail "bin/VERSION reads '$v', expected 0.4.29"; fi

exit "$status"
