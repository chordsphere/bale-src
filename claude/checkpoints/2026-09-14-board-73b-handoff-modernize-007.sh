#!/usr/bin/env bash
# Blind checkpoint — row 73 session B (handoff modernization), v1.
# Authored at the 2026-09-14-continue-plan-006 sitting from the
# request, before implementation. Outcome contracts only:
#   1. the four handoff suites plus the happy suite run green, with
#      no expected failures and no unexpected successes left;
#   2. no method-level @unittest.expectedFailure remains in the three
#      suites that carried the six reproductions;
#   3. bin/VERSION reads 0.4.28.
# Writes: nothing outside the suites' own temp dirs.
set -u
status=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; status=1; }

if [ ! -f bin/VERSION ] || [ ! -d tests ]; then
  echo "[FAIL] checkpoint must run at the repo root (bin/VERSION, tests/ missing)"
  exit 2
fi

# 1. Suites green, no residual expected failures / unexpected successes.
out="$(python3 -m unittest discover -s tests -p 'test_handoff_*.py' 2>&1)"
rc=$?
echo "$out" | tail -n 6
if [ "$rc" -eq 0 ]; then
  pass "handoff suites: exit 0"
else
  fail "handoff suites: exit $rc"
fi
if echo "$out" | grep -Eq 'expected failures=|unexpected successes='; then
  fail "handoff suites: residual expected failures / unexpected successes reported"
else
  pass "handoff suites: no expected failures, no unexpected successes"
fi

# 2. Decorators stripped (preserved text: the decorator line itself).
for f in tests/test_handoff_registry_gate.py \
         tests/test_handoff_forecast.py \
         tests/test_handoff_checkpoint_gates.py; do
  if [ ! -f "$f" ]; then
    fail "$f: missing"
    continue
  fi
  n="$(grep -Ec '^[[:space:]]*@unittest\.expectedFailure[[:space:]]*$' "$f")"
  if [ "$n" -eq 0 ]; then
    pass "$f: no @unittest.expectedFailure decorator remains"
  else
    fail "$f: $n @unittest.expectedFailure decorator(s) remain"
  fi
done

# 3. Version bump.
v="$(tr -d '[:space:]' < bin/VERSION)"
if [ "$v" = "0.4.28" ]; then
  pass "bin/VERSION reads 0.4.28"
else
  fail "bin/VERSION reads '$v', expected 0.4.28"
fi

exit "$status"
