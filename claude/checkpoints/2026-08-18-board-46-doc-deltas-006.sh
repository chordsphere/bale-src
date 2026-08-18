#!/usr/bin/env bash
# checkpoint-board-46-doc-deltas-v2.sh
# Blind checkpoint for the 2026-08-18 board-46 small-doc-deltas
# session. Authored at the master desk from the request, before any
# implementation exists. v2 derives from v1: the six v1 probes are
# byte-identical; two probes added for the cargo grown at the
# smoothing sitting (row 46's bracket). Dry-run against the base
# tree at the continue-plan-005 desk: all eight probes FAIL there.
# Outcome-only probes: each asserts a concept token any correct
# landing must contain (invariant-shaped), plus one
# fixed string sanctioned by the brief's VERBATIM-REQUIRED marker.
# Wrap-tolerant by construction: files are newline-joined before
# matching. Exit 0 = all pass, 1 = probe failure(s), 2 = the script
# or tree itself is broken (planner-artifact error, not a violation).
set -u
fail_count=0

for f in docs/PLANNER.md docs/TARBALL.md docs/DOCS.md; do
  if [ ! -f "$f" ]; then
    echo "[checkpoint ERROR] expected file missing: $f"
    exit 2
  fi
done

norm() { tr '\n' ' ' < "$1" | tr -s ' '; }

probe() {
  label="$1"; file="$2"; pattern="$3"
  if norm "$file" | grep -Eiq -- "$pattern"; then
    echo "[probe PASS] $label"
  else
    echo "[probe FAIL] $label"
    fail_count=$((fail_count+1))
  fi
}

probe "hot-file forecast sentence lands in PLANNER.md" \
      docs/PLANNER.md "hot[- ]?file"
probe "calibration-sitting doctrine lands in PLANNER.md" \
      docs/PLANNER.md "calibration sitting"
probe "provenance-split rule clause lands in PLANNER.md (VERBATIM-REQUIRED per brief)" \
      docs/PLANNER.md "connective-phrase grep"
probe "scopeless-goal exemption lands in TARBALL.md" \
      docs/TARBALL.md "scopeless"
probe "disposal-policy rows land in DOCS.md" \
      docs/DOCS.md "named consumer"
probe "forecast_departures sentence lands in TARBALL.md" \
      docs/TARBALL.md "forecast_departures"
probe "hooks rule lands in PLANNER.md (grown cargo)" \
      docs/PLANNER.md "hooks?"
probe "calibration pruning duty lands in PLANNER.md (grown cargo)" \
      docs/PLANNER.md "prun"

if [ "$fail_count" -gt 0 ]; then
  echo "[checkpoint] $fail_count probe(s) failed"
  exit 1
fi
echo "[checkpoint] all probes passed"
exit 0
