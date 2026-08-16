#!/usr/bin/env bash
# Blind checkpoint — rider-foldin-deltas — v1 (2026-08-16)
# Authored at the cleanup-master sitting desk, from the request,
# before implementation. Outcome contracts only; no mechanism
# assertions. Probe phrases are matched wrap-tolerant per the
# 2026-08-16 desk rule (whitespace-normalized stream, fixed-string
# grep). Exit 0 = pass, 1 = HOLD, 2 = checkpoint-side error.
set -u

TARGET="claude/MASTER.md"
if [ ! -f "$TARGET" ]; then
  echo "[checkpoint] ERROR: $TARGET not found from $(pwd)" >&2
  exit 2
fi

# Whitespace-normalized stream: hard wraps and indent collapse to
# single spaces, so long phrases match regardless of wrap point.
NORM="$(tr -s '[:space:]' ' ' < "$TARGET")" || exit 2

FAILED=0
probe() {
  # probe <label> <present|absent> <fixed-string phrase>
  local label="$1" mode="$2" phrase="$3"
  if printf '%s' "$NORM" | grep -qF -- "$phrase"; then
    local found=yes
  else
    local found=no
  fi
  if { [ "$mode" = present ] && [ "$found" = no ]; } || \
     { [ "$mode" = absent ] && [ "$found" = yes ]; }; then
    echo "[checkpoint] HOLD probe failed: $label" >&2
    FAILED=1
  fi
}

# Outcome 1: the six rider board rows exist by their headline names.
probe "row-41-base-drift"      present "base-drift stamp + gate"
probe "row-42-telemetry-wave1" present "telemetry field additions, wave 1"
probe "row-43-compression"     present "compression pilot"
probe "row-44-stats-drilldown" present "stats drill-down read sides"
probe "row-45-hostile-repo"    present "hostile-foreign-repo arc"
probe "row-46-small-deltas"    present "small doc deltas, one carrier"

# Outcome 2: the 008 contract block landed in section 5.
probe "disposal-doctrine"      present "No field without a named consumer"
probe "calibration-trigger"    present "trigger-fired, never calendar-fired"
probe "nominate-never-curate"  present "Nominate, never curate"

# Outcome 3: the single-window premise rider reached board 37.
probe "premise-bet"            present "revisitable bet"

# Outcome 4: the five-doc true-up executed both ways.
probe "five-doc-trueup"        present "the five global docs under docs/"
probe "four-doc-gone"          absent  "the four global docs under docs/"

# Outcome 5: the version landmark is current.
probe "version-landmark"       present "bin/bale VERSION 0.4.11"

if [ "$FAILED" -ne 0 ]; then
  exit 1
fi
echo "[checkpoint] PASS: all rider-foldin outcome probes hold"
exit 0
