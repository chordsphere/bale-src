#!/usr/bin/env bash
# Blind checkpoint — board 73, session A (handoff: reproduce-first).
# Authored blind at the 2026-09-10 master sitting from the request,
# before any implementation exists (TARBALL.md §7; PLANNER.md §4).
# Outcome contracts only — nothing here asserts how the worker got
# there. Runs with cwd = the staged applied tree, confined.
#
# Probes:
#   new-handoff-test-file      a non-empty tests/test_handoff_*.py beyond
#                              tests/test_handoff_happy.py exists
#   handoff-pattern-discovery  python3 -m unittest discover over the
#                              test_handoff_* pattern exits 0 (an
#                              expectedFailure-marked reproduction keeps
#                              discovery green; a fixed-under-your-feet
#                              unexpected success does not, by design)
#
# Exit: 0 all probes pass; 1 a probe failed; 2 the script itself errored.
set -u

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 not on PATH — checkpoint cannot run"
  exit 2
fi
if [ ! -d tests ] || [ ! -f tests/harness.py ]; then
  echo "[ERROR] tests/harness.py absent — not the bale-src tree"
  exit 2
fi

failed=0

# --- probe 1: a new handoff test file exists -------------------------
new_files=$(find tests -maxdepth 1 -type f -name 'test_handoff_*.py' \
  ! -name 'test_handoff_happy.py' -size +0c | sort)
if [ -n "$new_files" ]; then
  echo "[PASS] new-handoff-test-file: $(echo "$new_files" | tr '\n' ' ')"
else
  echo "[FAIL] new-handoff-test-file: no non-empty tests/test_handoff_*.py beyond tests/test_handoff_happy.py"
  failed=1
fi

# --- probe 2: discovery over the handoff pattern is green ----------------
out=$(python3 -m unittest discover -s tests -p 'test_handoff_*.py' 2>&1)
rc=$?
if [ "$rc" -eq 0 ]; then
  echo "[PASS] handoff-pattern-discovery: $(echo "$out" | grep -E '^Ran ' | head -1)"
else
  echo "[FAIL] handoff-pattern-discovery: unittest exited $rc"
  echo "$out" | tail -25
  failed=1
fi

exit $failed
