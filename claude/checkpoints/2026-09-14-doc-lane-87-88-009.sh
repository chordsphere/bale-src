#!/usr/bin/env bash
# Blind checkpoint — doc lane rows 88 + 87 (naming half), v1.
# Authored at the 2026-09-14-continue-plan-006 sitting from the
# request, before implementation. Outcome contracts only:
#   1. the three doc-pin suites run green;
#   2. the two VERBATIM passages the brief hands the worker are
#      present, whitespace-normalized (preserved text, so fixed
#      strings are legitimate);
#   3. the three retired strings are gone;
#   4. CLAUDE.md's "Deciding what's next" row names PLANNER.md.
# Writes: nothing.
set -u
status=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; status=1; }

for f in docs/PLANNER.md docs/CLAUDE.md docs/TARBALL.md; do
  if [ ! -f "$f" ]; then
    echo "[FAIL] checkpoint must run at the repo root ($f missing)"
    exit 2
  fi
done

norm() { tr -s '[:space:]' ' ' < "$1"; }

# 1. Suites.
for suite in test_sanctioned_pairs test_doc_crossrefs test_global_doc_selfcontainment; do
  out="$(python3 -m unittest discover -s tests -p "$suite.py" 2>&1)"
  if [ $? -eq 0 ] && echo "$out" | grep -q '^OK'; then
    pass "$suite green"
  else
    echo "$out" | tail -n 8
    fail "$suite not green"
  fi
done

# 2. VERBATIM passages.
P88='A sitting runs forecast-disjoint sessions beside each other by default and serializes only on a real dependency; disjointness is a property of the write forecasts alone, so each session still ships every read it needs — includes gate nothing, and a suite ships with the modules it imports.'
if norm docs/PLANNER.md | grep -Fq -- "$P88"; then
  pass "PLANNER.md carries the row-88 practice sentence verbatim"
else
  fail "PLANNER.md lacks the row-88 practice sentence (whitespace-normalized match)"
fi
if grep -Fq -- 'tar -czf response-<sid>.tar.gz response-NNN/' docs/TARBALL.md; then
  pass "TARBALL.md 10.1 carries the sid-bearing response tar command"
else
  fail "TARBALL.md lacks 'tar -czf response-<sid>.tar.gz response-NNN/'"
fi

# 3. Retired strings.
retired() {  # file, string (matched whitespace-normalized, so wrapping can't hide it)
  if norm "$1" | grep -Fq -- "$2"; then
    fail "$1 still contains '$2'"
  else
    pass "$1 no longer contains '$2'"
  fi
}
retired docs/PLANNER.md 'When split sessions are meant to run concurrently'
retired docs/TARBALL.md 'response-NNN.tar.gz'
retired docs/TARBALL.md 'request-NNN.tar.gz'

# 4. CLAUDE.md §4 row pointer (a table row is one line).
if grep -E "^\|[[:space:]]*Deciding what's next" docs/CLAUDE.md | grep -q 'PLANNER.md'; then
  pass "CLAUDE.md 'Deciding what's next' row points at PLANNER.md"
else
  fail "CLAUDE.md 'Deciding what's next' row does not name PLANNER.md"
fi

exit "$status"
