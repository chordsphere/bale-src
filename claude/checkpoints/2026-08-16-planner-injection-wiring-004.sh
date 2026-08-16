#!/usr/bin/env bash
# checkpoint-planner-wiring-v1.sh
# Blind checkpoint for the planner-injection-wiring session.
# Authored at the planner desk, 2026-08-16 master sitting, from the
# request alone. Outcome-only.
#
# Writes to: nothing. Read-only assertions against the staging copy.

set -u
fails=0

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf '[PASS] %s\n' "$label"
  else
    printf '[FAIL] %s\n' "$label"
    fails=$((fails + 1))
  fi
}

# --- The tool knows the fifth doc -----------------------------------
check "bin/ names PLANNER.md"                grep -rq "PLANNER.md" bin/

# --- The two deferred BALE.md sites are trued up --------------------
check "BALE.md: inject-all-four gone"        bash -c '! grep -q "Inject all four" BALE.md'
check "BALE.md: four-real-files note gone"   bash -c '! grep -q "four global docs are real files" BALE.md'

# (Deliberately unasserted: the version bump. VERSION's post-
# extraction location is not in front of this desk, and an imagined
# anchor is a fixture defect waiting to HOLD. The worker's
# validation and the operator's review cover it.)

# --- The guards hold, on the runner this repo actually uses ---------
check "self-containment guard passes" python3 -m unittest tests.test_global_doc_selfcontainment
check "crossref guard passes"         python3 -m unittest tests.test_doc_crossrefs

# --- Verdict ---------------------------------------------------------
if [ "$fails" -eq 0 ]; then
  printf 'checkpoint: PASS\n'
  exit 0
else
  printf 'checkpoint: FAIL (%d)\n' "$fails"
  exit 1
fi
