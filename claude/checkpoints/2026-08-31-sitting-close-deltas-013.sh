#!/usr/bin/env bash
# Blind checkpoint — sitting-close-deltas (rev1).
# Authored at the 2026-08-31-continue-plan-012 sitting, from the
# request, before implementation. Outcome contracts only.
# Runs with cwd = the staged (applied) tree. Exit: 0 pass, 1 a probe
# failed, 2 this script itself errored.
set -u

TARGET="claude/MASTER.md"
fails=0

if [ ! -f "$TARGET" ]; then
  echo "[CKPT ERROR] target file missing: $TARGET"
  exit 2
fi

probe() { # label, fixed-string the target must contain
  local label="$1" needle="$2"
  if grep -qF -- "$needle" "$TARGET"; then
    echo "[CKPT PASS] $label"
  else
    echo "[CKPT FAIL] $label"
    fails=$((fails + 1))
  fi
}

# Outcome 1-3: the three wave sessions are recorded as closed on the
# board (each sid is absent from the base tree's MASTER.md).
probe "row-62-close-recorded" "2026-08-31-board-62-planner-doctrine-008"
probe "row-64-close-recorded" "2026-08-31-board-64-release-surface-group-009"
probe "row-65-close-recorded" "2026-08-31-board-65-linkage-rollup-010"

# Outcome 4: the 011 close rider is recorded.
probe "rider-011-recorded" "2026-08-31-board-64-65-close-rider-011"

# Outcome 5: the lane-reconciliation kernel landed verbatim,
# contiguous on one unwrapped line (pinned in the brief).
probe "lane-reconciliation-kernel" "Board 64's documentation cargo landed at its own session; the close rider's deferred-doc premise was stale, and the drift was the rider brief's, not the board's."

# Outcome 6: the calibration-ruling kernel landed verbatim,
# contiguous on one unwrapped line (pinned in the brief).
probe "calibration-ruling-kernel" "Master-authored forecasts stop pre-seeding the packaging trio; the release-surface include group carries the read side, and a needed packaging change travels ship-enumerate-admit."

if [ "$fails" -gt 0 ]; then
  echo "[CKPT] $fails probe(s) failed"
  exit 1
fi
echo "[CKPT] all probes passed"
exit 0
