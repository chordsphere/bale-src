#!/usr/bin/env bash
# Blind checkpoint — 2026-08-31-board-67-suite-repair (v2)
# Outcome contract: the repo's test suite is green under both gate
# positions, in the environment this script runs in (for the real
# grading run, bale's confined dry-run sandbox). Exit: 0 PASS, 1 HOLD,
# 2 defective environment.
#
# v2 over v1: (a) the FULL failing enumeration prints to stdout, so
# the open log captures the grading environment's authoritative
# failing set — the one place it is observable; (b) each discovery
# pass runs under a 20-minute timeout so an environment-bound hang
# becomes a diagnosable FAIL, never a stuck open.
set -u

ROOT=""
for d in "$PWD" "$PWD/.." "$PWD/../.."; do
  if [ -f "$d/bin/bale" ] && [ -f "$d/tests/harness.py" ]; then
    ROOT="$(cd "$d" && pwd)"
    break
  fi
done
if [ -z "$ROOT" ]; then
  echo "CHECKPOINT ERROR: cannot locate tree root (bin/bale + tests/harness.py) from $PWD" >&2
  exit 2
fi

fail=0

run_pass() {
  local label="$1"; shift
  local logf="$1"; shift
  echo "PROBE $label: running full discovery..."
  ( cd "$ROOT" && timeout 1200 env "$@" python3 -m unittest discover -s tests >"$logf" 2>&1 )
  local rc=$?
  if [ "$rc" -eq 0 ]; then
    echo "PROBE $label: PASS ($(tail -n 3 "$logf" | grep -E '^(OK|Ran )' | tr '\n' ' '))"
    return 0
  fi
  if [ "$rc" -eq 124 ]; then
    echo "PROBE $label: FAIL (TIMEOUT at 1200s — the suite hung in this environment; last lines follow)"
    tail -n 10 "$logf"
  else
    echo "PROBE $label: FAIL (discovery exit $rc); full failing enumeration:"
    grep -E "^(FAIL|ERROR): " "$logf" | sort
    tail -n 2 "$logf" | grep -E "^(FAILED|OK)" || true
  fi
  fail=1
}

run_pass suite-green-default    /tmp/ckpt67v2-default.log BALE_TEST_SLOW=
run_pass suite-green-slow-gated /tmp/ckpt67v2-slow.log    BALE_TEST_SLOW=1

exit $fail
