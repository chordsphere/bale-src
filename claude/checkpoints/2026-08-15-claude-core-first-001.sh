#!/usr/bin/env bash
# Blind checkpoint — claude-core-first
# Planner-authored at the 2026-08-14 improvement sitting, blind to any
# response. Thin outcome contract on docs/CLAUDE.md's restructure.
set -uo pipefail
fail=0
check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then echo "[PASS] $label"; else echo "[FAIL] $label"; fail=1; fi
}
F=docs/CLAUDE.md
[ -f "$F" ] || { echo "[FAIL] missing $F"; exit 1; }

# 1. A core banner exists (brief prescribes mirroring TARBALL.md's).
check "core banner present" grep -qi "past the core" "$F"

# 2. Every section-11 subsection heading survives, exactly once.
for n in 1 2 3 4 5 6; do
  check "heading 11.$n appears exactly once" \
    bash -c "[ \"\$(grep -c '^### 11\.$n' '$F')\" -eq 1 ]"
done

# 3. Placement: 11.1–11.2 before the banner, 11.3–11.6 after it.
banner=$(grep -in "past the core" "$F" | head -1 | cut -d: -f1)
if [ -n "${banner:-}" ]; then
  for n in 1 2; do
    line=$(grep -n "^### 11\.$n" "$F" | head -1 | cut -d: -f1)
    if [ -n "$line" ] && [ "$line" -lt "$banner" ]; then
      echo "[PASS] 11.$n sits before the banner"
    else echo "[FAIL] 11.$n sits before the banner"; fail=1; fi
  done
  for n in 3 4 5 6; do
    line=$(grep -n "^### 11\.$n" "$F" | head -1 | cut -d: -f1)
    if [ -n "$line" ] && [ "$line" -gt "$banner" ]; then
      echo "[PASS] 11.$n sits after the banner"
    else echo "[FAIL] 11.$n sits after the banner"; fail=1; fi
  done
else
  echo "[FAIL] banner line not found; placement checks unrunnable"; fail=1
fi

# 4. The self-containment sentence landed in the doc.
check "self-containment sentence present" \
  grep -Eqi "cite only each other|self-contained" "$F"

# 5. No content deletion: relocation plus additions never shrinks the file.
check "size floor (>= 32037 bytes, the pre-change size)" \
  bash -c '[ "$(wc -c < docs/CLAUDE.md)" -ge 32037 ]'

exit $fail
