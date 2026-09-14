#!/usr/bin/env bash
# Blind checkpoint — sitting close deltas 7 (continue-plan-006), v1.
# Outcome-only probes on claude/MASTER.md: the sitting's sids are
# recorded, the version landmark moved, the strikes landed, the new
# rows and evidence entries exist and numbering did not overrun.
set -u
status=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; status=1; }
M=claude/MASTER.md
[ -f "$M" ] || { echo "[FAIL] $M missing — run at the repo root"; exit 2; }
norm() { tr -s '[:space:]' ' ' < "$M"; }
has() { if norm | grep -Fq -- "$1"; then pass "$2"; else fail "$2 (missing: $1)"; fi; }
gone() { if norm | grep -Fq -- "$1"; then fail "$2 (still present: $1)"; else pass "$2"; fi; }

for sid in 2026-09-14-continue-plan-006 2026-09-14-board-80-tests-only-pins-008 \
           2026-09-14-board-73b-handoff-modernize-007 2026-09-14-doc-lane-87-88-009 \
           2026-09-14-apply-side-81-87-010 2026-09-14-board-83-hook-store-and-decline-cause-011; do
  has "$sid" "records $sid"
done
has "0.4.29" "version landmark 0.4.29 present"
gone '\"' "backslash-escaped quotes struck"
gone "the naming variance is what defeats its matching" "row 87's wrong desk clause struck"
has "Landed 2026-09-14" "a Landed 2026-09-14 block opens"
section() { awk -v h="$1" '$0 ~ "^## "h"\\." {p=1; next} /^## [0-9]+\./ {p=0} p' "$M"; }
if section 6 | grep -Eq '^131\. \*\*'; then pass "evidence entry 131 present in §6"; else fail "evidence entry 131 missing from §6"; fi
if section 6 | grep -Eq '^132\. \*\*'; then fail "evidence numbering overran (132 in §6)"; else pass "evidence numbering stops at 131"; fi
for r in 89 90 91 92 93; do
  if section 4 | grep -Eq "^$r\. \*\*"; then pass "board row $r present in §4"; else fail "board row $r missing from §4"; fi
done
if section 4 | grep -Eq "^94\. \*\*"; then fail "board numbering overran (94 in §4)"; else pass "board numbering stops at 93"; fi
exit "$status"
