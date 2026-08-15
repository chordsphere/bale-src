#!/usr/bin/env bash
# Blind checkpoint — tarball-riders
# Planner-authored, blind. Thin outcome contract; the doc-integrity
# suite is the load-bearing check. Wording-proxy checks are marked —
# amend rather than loosen silently if a HOLD looks like phrasing.
set -uo pipefail
fail=0
check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "[PASS] $label"; else echo "[FAIL] $label"; fail=1; fi
}
F=docs/TARBALL.md
[ -f "$F" ] || { echo "[FAIL] missing $F"; exit 1; }

# Rider 1: the repo-local phrasing is gone; install phrasing present.
if grep -Fq "in bale's repo" "$F"; then
  echo "[FAIL] no remaining 'in bale's repo' phrasing"; fail=1
else
  echo "[PASS] no remaining 'in bale's repo' phrasing"
fi
check "install-local phrasing present at both sites (>= 2)" \
  bash -c "[ \"\$(grep -ci 'installation' '$F')\" -ge 2 ]"   # wording proxy

# Rider 2: the emission is named.
check "--doc-assertions named in TARBALL.md" \
  grep -Fq -- "--doc-assertions" "$F"

# Rider 3: the race-safety half exists.                      # wording proxy
check "race-safety doctrine present" \
  bash -c "grep -Eqi 'race-safe|race reasoning|structurally lands nothing' '$F'"

# The load-bearing check: guard, cross-refs, and pair pins all green.
if python3 -m unittest discover -s tests -p "test_*.py" >/dev/null 2>&1; then
  echo "[PASS] full doc-integrity suite green in staging"
else
  echo "[FAIL] full doc-integrity suite green in staging"; fail=1
fi

exit $fail
