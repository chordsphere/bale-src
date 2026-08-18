#!/usr/bin/env bash
# Blind checkpoint — master-v5-regeneration — v1 (2026-08-16)
# Authored at the cleanup-master sitting desk, from the request,
# before implementation. Outcome contracts only. Probes are
# wrap-tolerant (whitespace-normalized stream, fixed-string grep)
# per the 2026-08-16 desk rule. Exit 0 = pass, 1 = HOLD,
# 2 = checkpoint-side error.
set -u

MD="claude/MASTER.md"
IX="claude/INDEX.md"
for f in "$MD" "$IX"; do
  if [ ! -f "$f" ]; then
    echo "[checkpoint] ERROR: $f not found from $(pwd)" >&2
    exit 2
  fi
done
NMD="$(tr -s '[:space:]' ' ' < "$MD")" || exit 2
NIX="$(tr -s '[:space:]' ' ' < "$IX")" || exit 2

FAILED=0
probe() {
  # probe <stream> <label> <present|absent> <fixed-string phrase>
  local stream="$1" label="$2" mode="$3" phrase="$4" found=no
  if printf '%s' "$stream" | grep -qF -- "$phrase"; then found=yes; fi
  if { [ "$mode" = present ] && [ "$found" = no ]; } || \
     { [ "$mode" = absent ] && [ "$found" = yes ]; }; then
    echo "[checkpoint] HOLD probe failed: $label" >&2
    FAILED=1
  fi
}

# --- Preservation: live items survive the condensation ---
probe "$NMD" keep-row1-title       present "staging-from-target-base"
probe "$NMD" keep-row5-title       present "bale stats / the trust ledger"
probe "$NMD" keep-row13-title      present "read-vs-write separation"
probe "$NMD" keep-row35-title      present "Selftest gap-closure arc"
probe "$NMD" keep-row35-residual   present "handoff-under-pattern E2E"
probe "$NMD" keep-row41-title      present "base-drift stamp + gate"
probe "$NMD" keep-row46-title      present "small doc deltas, one carrier"
probe "$NMD" keep-watch-refusal    present "Forecast-refusal per-path counter"
probe "$NMD" keep-watch-deadckpt   present "Dead ceremony checkpoint files"
probe "$NMD" keep-foldin-negation  present "Negation-refusal wording split"
probe "$NMD" keep-foldin-superseq  present "Supersession writes its closure record BEFORE the sweep"
probe "$NMD" keep-s5-mechanism     present "Mechanism authority sits with the session"
probe "$NMD" keep-s5-disposal      present "No field without a named consumer"
probe "$NMD" keep-s5-badoracle     present "reveal-spec-not-script"
probe "$NMD" keep-ev79-tail        present "the motivating datum for board 37"
probe "$NMD" keep-row33-hazard     present "carries the literal it names inline"

# --- Regeneration outcomes ---
probe "$NMD" v5-header             present "v5 — 2026-08-16"
probe "$NMD" cleared-paras-gone    absent  "Cleared at this landing"
probe "$NMD" four-docs-still-gone  absent  "four global docs under docs/"
probe "$NMD" landmark-current      present "0.4.11 at"
probe "$NIX" index-v5-trueup       present "v5 as of 2026-08-16"
probe "$NIX" index-v4-gone         absent  "v4 as of 2026-07-31"

if [ "$FAILED" -ne 0 ]; then
  exit 1
fi
echo "[checkpoint] PASS: all v5-regeneration outcome probes hold"
exit 0
