#!/usr/bin/env bash
# checkpoint-planner-birth-v1.sh
# Blind checkpoint for the planner-birth session. Authored at the
# planner desk, 2026-08-16 master sitting, from the request alone.
# Outcome-only: asserts what must be true of the staging tree after
# apply, never how the worker got there.
#
# Writes to: nothing. Read-only assertions against the staging copy.

set -u
fails=0

check() {
  # check <label> <command...>
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf '[PASS] %s\n' "$label"
  else
    printf '[FAIL] %s\n' "$label"
    fails=$((fails + 1))
  fi
}

# --- The doc exists and is a real doc, not a stub -------------------
check "docs/PLANNER.md exists"            test -f docs/PLANNER.md
check "docs/PLANNER.md size floor (12k)"  test "$(wc -c < docs/PLANNER.md 2>/dev/null || echo 0)" -ge 12000

# --- Ratified shape: core-first, one doc ----------------------------
check "core banner present (past-the-core seam)" grep -qi "past the core" docs/PLANNER.md
check "provisional-until-S6 marking present"     grep -qi "provisional-until-S6" docs/PLANNER.md

# --- Self-containment: a global doc points at no project-local doc --
check "no MASTER.md reference in PLANNER.md"     bash -c '! grep -q "MASTER.md" docs/PLANNER.md'
check "no claude/context path in PLANNER.md"     bash -c '! grep -q "claude/context" docs/PLANNER.md'

# --- The merge: orchestration.md relocated, tombstone left ----------
check "orchestration.md tombstone exists"        test -f claude/context/orchestration.md
check "tombstone points at the new home"         grep -q "PLANNER.md" claude/context/orchestration.md
check "tombstone is a tombstone (under 5k)"      test "$(wc -c < claude/context/orchestration.md 2>/dev/null || echo 99999)" -lt 5000

# --- Four-to-five true-up, CLAUDE.md side ----------------------------
# (BALE.md's true-up is deliberately unasserted: its wording is not in
# front of the desk, and an imagined anchor is a planner-fixture
# defect waiting to HOLD. The worker's validation covers it.)
check "CLAUDE.md no longer says injects-all-four" bash -c '! grep -q "injects all four" docs/CLAUDE.md'
check "CLAUDE.md no longer says the-four-injected" bash -c '! grep -q "The four injected docs" docs/CLAUDE.md'
check "CLAUDE.md names PLANNER.md"                grep -q "PLANNER.md" docs/CLAUDE.md

# --- The guards hold with five docs in the set ----------------------
if command -v pytest >/dev/null 2>&1; then
  check "self-containment guard passes" pytest -q tests/test_global_doc_selfcontainment.py
  check "crossref guard passes"         pytest -q tests/test_doc_crossrefs.py
else
  printf '[SKIP] guard tests: pytest not found\n'
fi

# --- Verdict ---------------------------------------------------------
if [ "$fails" -eq 0 ]; then
  printf 'checkpoint: PASS\n'
  exit 0
else
  printf 'checkpoint: FAIL (%d)\n' "$fails"
  exit 1
fi
