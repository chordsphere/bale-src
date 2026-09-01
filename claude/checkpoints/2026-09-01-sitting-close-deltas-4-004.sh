#!/usr/bin/env bash
# Blind checkpoint — 2026-09-01-sitting-close-deltas-4 (v1)
# Outcome probes on claude/MASTER.md for the pinned landing tokens the
# brief mandates verbatim. Exit: 0 PASS, 1 HOLD, 2 defective env.
set -u
ROOT=""
for d in "$PWD" "$PWD/.." "$PWD/../.."; do
  if [ -f "$d/claude/MASTER.md" ]; then ROOT="$(cd "$d" && pwd)"; break; fi
done
if [ -z "$ROOT" ]; then
  echo "CHECKPOINT ERROR: cannot locate claude/MASTER.md from $PWD" >&2
  exit 2
fi
M="$ROOT/claude/MASTER.md"
fail=0
probe() { # label, fixed string
  if grep -qF "$2" "$M"; then
    echo "PROBE $1: PASS (token present)"
  else
    echo "PROBE $1: FAIL (missing pinned token: $2)"
    fail=1
  fi
}
probe row-41-landed        "board-41-base-drift-027"
probe row-67-landed        "board-67-suite-repair-002"
probe row-42-landed        "board-42-telemetry-fields-003"
probe ruling-in-contracts  "accepted as the de facto primary defense on auto-compacting surfaces"
probe corpus-tolerance     "open_telemetry"
probe falsified-claims     "Two falsified desk environment claims"
probe forecast-lesson      "guard-forced sibling"
exit $fail
