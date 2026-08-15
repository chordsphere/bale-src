#!/usr/bin/env bash
# Blind checkpoint — doc-mechanization (v2: count floor re-baselined
# after sibling 006 landed the guard test; 34 -> 35 pre-session)
# Planner-authored at the 2026-08-14 improvement sitting, blind to any
# response. Thin outcome contract; the suite run is the load-bearing
# check — mechanization that breaks the suite is not mechanization.
set -uo pipefail
fail=0
check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "[PASS] $label"; else echo "[FAIL] $label"; fail=1; fi
}

# 1. The crafter's surface grew: help now speaks to doc assertions.
check "crafter --help mentions the doc-assertion surface" \
  bash -c 'python3 tools/craft_response.py --help 2>&1 | grep -Eqi "INDEX|ADR|assert"'

# 2. Two new integrity tests landed as their own files (35 -> >= 37).
check "tests/ gained two test files (>= 37)" \
  bash -c '[ "$(ls tests/test_*.py 2>/dev/null | wc -l)" -ge 37 ]'

# 3. Prose deletion landed: DOCS.md strictly shrank from 24419 bytes.
check "docs/DOCS.md shrank (< 24419 bytes)" \
  bash -c '[ "$(wc -c < docs/DOCS.md)" -lt 24419 ]'

# 4. Judgment prose untouched: the recognition-level sections survive.
check "DOCS.md 4.1 introduction table intact"  grep -q "^### 4\.1" docs/DOCS.md
check "CODE.md section 13 testing intact"      grep -q "^## 13\."  docs/CODE.md
check "CODE.md foreign-code section intact"    grep -q "^## 7\."   docs/CODE.md

# 5. The whole suite is green with the changes staged (hermetic per
#    ADR-0005; wall time is the planner-accepted cost of this check).
if python3 -m unittest discover -s tests -p "test_*.py" >/dev/null 2>&1; then
  echo "[PASS] full test suite green in staging"
else
  echo "[FAIL] full test suite green in staging"; fail=1
fi

exit $fail
