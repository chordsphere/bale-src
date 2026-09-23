#!/usr/bin/env bash
# Blind checkpoint — sitting close 18 (v2: probes 12 and 13-15 look for DONE anywhere in the row, the board's bracket convention; v1 pinned the head line, a mechanism — fixture defect, amended after the HOLD of 2026-09-23T04:06Z). Authored 2026-09-22 at the
# read-only master 2026-09-22-continue-plan-005 from the brief, before the
# landing exists. Grades outcomes of the applied claude/MASTER.md only;
# never how the worker got there. Exit 0 all probes pass; 1 any probe
# fails; 2 the oracle itself is broken (control or extractor failure).
set -u
F="claude/MASTER.md"
status=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; status=1; }
die2() { echo "[ERROR] $1"; exit 2; }

[ -f "$F" ] || die2 "no $F at $(pwd)"

# extractor: lines of one top-level section, by its '## N.' opener
section() { # section <N>
  awk -v n="$1" '
    $0 ~ "^## "n"\\. " {on=1; next}
    on && /^## [0-9]+\. / {exit}
    on {print}' "$F"
}
# registry span: from the fold-in registry header to the 2026-08-05 line
registry() {
  awk '/^\*\*Fold-in registry\*\*/{on=1} on && /^Landed 2026-08-05, non-board/{exit} on{print}' "$F"
}
# one board row's span: from "^NNN. " to the next "^[0-9]+. " row
row() { awk -v n="$1" '$0 ~ "^"n"\\. " {on=1} on && $0 !~ "^"n"\\. " && /^[0-9]+\. \*\*/ {exit} on{print}' "$F"; }

# ---- control: the extractors work on this file (exit 2 if not) ----
section 5 | grep -q "Carried forward: JSON vocabulary" || die2 "control: section extractor found no §5 lead"
registry | grep -q "run_hook's three placeholder-less f-strings" || die2 "control: registry extractor found no first entry"
row 101 | grep -q "Bare \`bale apply\` bounded resolution" || die2 "control: row extractor missed row 101"
[ "$(section 4 | grep -c '^120\. ')" -eq 1 ] || die2 "control: row 120 not found once in §4"
echo "[PASS] control: extractors self-test"

# ---- probes ----
# 1 header line 14 names a close-18 sid
if sed -n 14p "$F" | grep -Eq '^Last landed by: `2026-09-2[0-9]-sitting-close-deltas-18-[0-9]{3}`\.$'; then pass "header-last-landed-by-close-18"; else fail "header-last-landed-by-close-18"; fi

V1='Closes are per wave, not per master. A master'"'"'s last job is the wave'"'"'s close, after its project work is dispatched.'
V2='More project work, less master grooming: an arc'"'"'s design sitting authors its own wave'"'"'s bundles once the operator ratifies the decomposition; no master sits between it and its workers.'
# 2-3 the cadence sentences, byte-verbatim, in §5
if section 5 | grep -qF -- "$V1"; then pass "s5-cadence-verbatim-1"; else fail "s5-cadence-verbatim-1"; fi
if section 5 | grep -qF -- "$V2"; then pass "s5-cadence-verbatim-2"; else fail "s5-cadence-verbatim-2"; fi
# 4-5 the same sentences in the registry rider
if registry | grep -qF -- "$V1"; then pass "registry-cadence-rider-verbatim-1"; else fail "registry-cadence-rider-verbatim-1"; fi
if registry | grep -qF -- "$V2"; then pass "registry-cadence-rider-verbatim-2"; else fail "registry-cadence-rider-verbatim-2"; fi
# 6 §5 gains the design sitting's rulings block
if section 5 | grep -q "^New, ratified 2026-09-23" && section 5 | grep -q "2026-09-23-board-100-design-001"; then pass "s5-rulings-block-2026-09-23"; else fail "s5-rulings-block-2026-09-23"; fi
# 7-10 §3 carries the four sittings' sids
for sid in 2026-09-22-continue-plan-001 2026-09-22-board-100-design-004 2026-09-23-board-100-design-001 2026-09-22-continue-plan-005; do
  if section 3 | grep -q "$sid"; then pass "s3-sitting-$sid"; else fail "s3-sitting-$sid"; fi
done
# 11 §3 records the successor watch
if section 3 | grep -qi "swept" && section 3 | grep -q "2026-09-23-board-100-design-001"; then pass "s3-successor-unswept-watch"; else fail "s3-successor-unswept-watch"; fi
# 12 row 100 is DONE and carries the wave and the v2 oracle
r100="$(row 100)"
if printf '%s\n' "$r100" | grep -q "DONE" && printf '%s\n' "$r100" | grep -q "2026-09-23"; then pass "row-100-done"; else fail "row-100-done"; fi
ok=1; for w in 2026-09-23-board-100-w1-doc-sweep-002 2026-09-23-board-100-w2-code-surfaces-003 2026-09-23-board-100-w3-file-rename-004 b8c69ae8; do printf '%s\n' "$r100" | grep -q "$w" || ok=0; done
if [ "$ok" -eq 1 ]; then pass "row-100-wave-and-v2-oracle"; else fail "row-100-wave-and-v2-oracle"; fi
if printf '%s\n' "$r100" | grep -q "board-100-arc"; then pass "row-100-archive-home"; else fail "row-100-archive-home"; fi
# 13-15 rows 77, 116, 118 closed
for n in 77 116 118; do if row "$n" | grep -q "DONE" && row "$n" | grep -q "2026-09-23"; then pass "row-$n-done"; else fail "row-$n-done"; fi; done
# 16 new rows from 121; 17 evidence from 205
if section 4 | grep -Eq '^12[1-9]\. \*\*'; then pass "board-row-121-plus"; else fail "board-row-121-plus"; fi
if section 6 | grep -Eq '^205\. \*\*'; then pass "evidence-entry-205"; else fail "evidence-entry-205"; fi
# 18 §7 landmark
if section 7 | grep -q "0\.4\.43"; then pass "s7-landmark-0-4-43"; else fail "s7-landmark-0-4-43"; fi
# 19 registry brackets: at least ten new dated brackets beyond the base's 21
n="$(registry | grep -Ec '\[2026-09-2[0-9]:')"
if [ "$n" -ge 31 ]; then pass "registry-brackets-ge-31 ($n)"; else fail "registry-brackets-ge-31 ($n)"; fi

exit "$status"
