#!/usr/bin/env bash
# Blind checkpoint — global-doc-selfcontainment (v2: adds the 3.4 surface check)
# Planner-authored at the 2026-08-14 improvement sitting, blind to any
# response. Thin outcome contract: asserts the staged tree's outcomes,
# not the worker's mechanism. Runs in staging beside validation.sh.
set -uo pipefail
fail=0
check() { # check <label> <cmd...>
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "[PASS] $label"; else echo "[FAIL] $label"; fail=1; fi
}
neg() { # neg <label> <cmd...> — passes when cmd finds nothing
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "[FAIL] $label"; fail=1; else echo "[PASS] $label"; fi
}

DOCS="docs/CLAUDE.md docs/TARBALL.md docs/DOCS.md docs/CODE.md"
for d in $DOCS; do
  [ -f "$d" ] || { echo "[FAIL] missing $d"; fail=1; }
done

# 1. Core outcome: zero project-local citations across the injected docs.
neg  "no BALE.md reference in any injected doc"   grep -l "BALE\.md" $DOCS
neg  "no MASTER.md reference in any injected doc" grep -l "MASTER\.md" $DOCS

# 2. Numbering stability: the relocation tombstones survive in place.
check "TARBALL.md 5.6.3 tombstone heading present" grep -q "^#### 5\.6\.3" docs/TARBALL.md
check "TARBALL.md 5.9.3 tombstone heading present" grep -q "^#### 5\.9\.3" docs/TARBALL.md
check "TARBALL.md 3.4 section still present"       grep -q "^### 3\.4"     docs/TARBALL.md

# 3. No mass deletion: stripping ~12 citations costs well under 2KB.
check "TARBALL.md size floor (>= 85500 bytes)" \
  bash -c '[ "$(wc -c < docs/TARBALL.md)" -ge 85500 ]'

# 4. Doctrine stated in BALE.md (soft wording proxy — planner may amend).
check "BALE.md states the self-containment doctrine" \
  grep -Eqi "self-contained|cite only each other" BALE.md

# 5. Guard landed: the test inventory grew by at least one file.
check "tests/ gained at least one test file (>= 35)" \
  bash -c '[ "$(ls tests/test_*.py 2>/dev/null | wc -l)" -ge 35 ]'

check "TARBALL.md 3.4 documents the checkpoint-file surface" \
  grep -q -- "--checkpoint-file" docs/TARBALL.md

exit $fail
