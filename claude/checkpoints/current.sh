#!/usr/bin/env bash
# claude/checkpoints/current.sh - blind checkpoint, board-10 wave 1
# Sessions gated: board-10-sandbox-wrapper (S1), board-10-orchestration-doc (S3)
# Sitting: 2026-08-10-continue-plan-001 (board-10 spec-intake repack)
#
# Planner-authored from the requests, before any implementation existed
# (BALE.md 8.5). Single-path mechanism note: [validation] base is one
# committed path per project, and every apply executes the bytes at its
# own base tip - so concurrent sessions share this file. This wave ships
# guarded blocks: each block arms only when its session's work is present
# in the applied tree, so either session's apply passes vacuously on the
# other's guard. Per-session checkpoints are a named S6 agenda item.
#
# Runs with cwd = staging (the applied tree). Exit: 0 pass, 1 check
# failed, 2 script error.

set -u
status=0
note() { printf '[ckpt] %s\n' "$*"; }
failck() { printf '[ckpt] FAIL: %s\n' "$*"; status=1; }

ran_any=0

# ---------- S1 guard: sandbox confinement properties ----------
# The brief pins the surface this block exercises: bin/bale_sandbox.py
# exposing run_confined(argv, *, staging, log_path, ...) returning an
# object with .returncode. The assertions are properties, not
# implementation: writes work only inside the staging it is handed,
# network is off, the operator environment does not leak.
if [ -f bin/bale_sandbox.py ]; then
  ran_any=1
  note "S1 guard armed: bin/bale_sandbox.py present"
  workdir=$(mktemp -d) || { note "ERROR: mktemp failed"; exit 2; }
  trap 'rm -rf "$workdir"' EXIT
  mkdir -p "$workdir/staging" "$workdir/outside"

  probe() {
    # probe <name> <shell-line> -> exits with the confined child's code
    python3 - "$workdir" "$1" "$2" <<'PYEOF'
import sys, os
sys.path.insert(0, "bin")
import bale_sandbox
workdir, name, cmd = sys.argv[1], sys.argv[2], sys.argv[3]
staging = os.path.join(workdir, "staging")
log = os.path.join(workdir, "ckpt.log")
res = bale_sandbox.run_confined(["bash", "-c", cmd],
                                staging=staging, log_path=log)
sys.exit(res.returncode)
PYEOF
  }

  # 1. A write inside the handed staging succeeds.
  if probe inwrite 'echo ok > inside-canary && test -f inside-canary'; then
    note "in-staging write: ok"
  else
    failck "a write inside staging did not succeed under confinement"
  fi

  # 2. A write outside it is denied - judged by the filesystem, not the
  #    child's exit code.
  probe outwrite "echo leak > '$workdir/outside/canary' 2>/dev/null" || true
  if [ -e "$workdir/outside/canary" ]; then
    failck "an out-of-staging write landed: confinement is not holding"
  else
    note "out-of-staging write: denied"
  fi

  # 3. Network is off.
  if probe net 'exec 3<>/dev/tcp/1.1.1.1/80' 2>/dev/null; then
    failck "a network connection succeeded under confinement"
  else
    note "network: off"
  fi

  # 4. The operator environment is scrubbed.
  export BALE_CKPT_CANARY=leaked
  if probe env 'test -z "${BALE_CKPT_CANARY:-}"'; then
    note "environment: scrubbed"
  else
    failck "an operator environment variable leaked into the confined child"
  fi
  unset BALE_CKPT_CANARY
fi

# ---------- S3 guard: orchestration doc shape ----------
if [ -f claude/context/orchestration.md ]; then
  ran_any=1
  note "S3 guard armed: claude/context/orchestration.md present"
  if grep -qF "Ambiguity is the enemy, not capability." claude/context/orchestration.md; then
    note "specification-friction anchor: present"
  else
    failck "the specification-friction anchor sentence is missing or wrapped"
  fi
  for h in "Blind checkpoints" "Escalation" "Trust phasing" "Worker refresh" "Cost governance"; do
    if grep -q "$h" claude/context/orchestration.md; then
      note "section present: $h"
    else
      failck "required section missing: $h"
    fi
  done
  if grep -q "orchestration.md" claude/INDEX.md; then
    note "INDEX.md lists the doc"
  else
    failck "claude/INDEX.md does not list orchestration.md"
  fi
fi

if [ "$ran_any" = 0 ]; then
  note "no wave-1 guard armed in this tree; checkpoint passes vacuously"
fi

exit "$status"
