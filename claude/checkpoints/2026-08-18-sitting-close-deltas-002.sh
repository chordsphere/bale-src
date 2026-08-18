#!/usr/bin/env bash
# Blind checkpoint — sitting-close-deltas — v1 (2026-08-18)
# Authored at the cleanup-master sitting desk, from the request,
# before implementation. Outcome contracts only, wrap-tolerant
# (whitespace-normalized stream, fixed-string grep). Provenance-split
# rule honored: every probed phrase is preserved-from-brief text
# (VERBATIM blocks or the enumerated Block B clause), never
# worker-authored prose. Exit 0 = pass, 1 = HOLD, 2 = error.
set -u

MD="claude/MASTER.md"
if [ ! -f "$MD" ]; then
  echo "[checkpoint] ERROR: $MD not found from $(pwd)" >&2
  exit 2
fi
NMD="$(tr -s '[:space:]' ' ' < "$MD")" || exit 2

FAILED=0
probe() {
  # probe <label> <present|absent> <fixed-string phrase>
  local label="$1" mode="$2" phrase="$3" found=no
  if printf '%s' "$NMD" | grep -qF -- "$phrase"; then found=yes; fi
  if { [ "$mode" = present ] && [ "$found" = no ]; } || \
     { [ "$mode" = absent ] && [ "$found" = yes ]; }; then
    echo "[checkpoint] HOLD probe failed: $label" >&2
    FAILED=1
  fi
}

# --- The sitting block landed (Block A anchors) ---
probe blockA-head        present "Ratified at the 2026-08-16/18 cleanup-master sitting"
probe blockA-attribution present "third checkpoint-desk miss"
probe blockA-deviation   present "must not score this HOLD against the worker"
probe blockA-relay       present "the one actor who cannot adjudicate them"

# --- Block B: the sanctioned clause swap, both directions ---
probe blockB-new present "the working copies live in v4, in git"
probe blockB-old absent  "board 10's queue entry keeps the working copies"

# --- Blocks C-F landed ---
probe row47 present "HOLD-card triage surface"
probe row48 present "Pack-time checkpoint dry-run echo"
probe blockD present "provenance-split probe rule"
probe blockE present "two live specimens accrued at the cleanup-master sitting"
probe blockF present "Row 33 hazard-bracket retirement decision"

# --- Spot integrity: v5 live content untouched ---
probe keep-s5-disposal present "No field without a named consumer"
probe keep-row41       present "base-drift stamp + gate"

if [ "$FAILED" -ne 0 ]; then
  exit 1
fi
echo "[checkpoint] PASS: all sitting-close outcome probes hold"
exit 0
