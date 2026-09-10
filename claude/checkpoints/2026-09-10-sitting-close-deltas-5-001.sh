#!/usr/bin/env bash
# sitting-close-deltas-5 blind checkpoint v1. Outcome contracts on
# MASTER.md's post-close content. Contradiction-pass done against
# the brief: no probe asserts absence of anything the brief keeps.
# Exit 0 all pass; 1 HOLD; 2 checkpoint-error.
set -u
fail_count=0
probe() {
  local label="$1" rc="$2"
  if [ "$rc" -eq 0 ]; then echo "[PASS] $label"
  else echo "[FAIL] $label"; fail_count=$((fail_count + 1)); fi
}
M=claude/MASTER.md
[ -f "$M" ] || { echo "[CHECKPOINT-ERROR] missing $M"; exit 2; }
normM() { tr -s ' \n' '  ' < "$M"; }

# P1 — row 70 is on the board, carrying its landing sid.
normM | grep -q "board-70-doc-reachability-007"; probe "P1-row-70-recorded" "$?"
# P2 — row 71 is on the board, carrying its landing sid.
normM | grep -q "board-71-lifecycle-resolution-008"; probe "P2-row-71-recorded" "$?"
# P3 — the version landmark moved to 0.4.25.
normM | grep -q "0\.4\.25"; probe "P3-landmark-0.4.25" "$?"
# P4 — row 73 exists with its reproduce-first shape.
normM | grep -qi "reproduce-first"; probe "P4-row-73-reproduce-first" "$?"

if [ "$fail_count" -gt 0 ]; then
  echo "checkpoint: HOLD ($fail_count probe(s) failed)"; exit 1
fi
echo "checkpoint: PASS (4/4)"; exit 0
