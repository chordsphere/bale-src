#!/usr/bin/env bash
# checkpoint-2026-08-18-continue-plan-005-close-v2.sh
# v2 amendment (desk, HOLD->correction): the pairs-rider probe's
# expected string was a token from the notes' discussion, not from
# Block F's verbatim Proposal text, so it failed every correct
# landing. Only that probe's expected string changes; every other
# probe is byte-identical to v1. Fixture defect, desk-attributed.
# Blind checkpoint for the 2026-08-18 continue-plan-005
# sitting-close deltas session. Authored at the master desk from
# the request, before any implementation exists. Outcome-only
# probes over claude/MASTER.md: preserved tokens (sids) pinned as
# fixed strings; authored text probed invariant-shaped; struck
# content probed by absence. Wrap-tolerant: the file is
# newline-joined before matching. Dry-run at the desk against the
# unedited base: all six probes FAIL there. Exit 0 = all pass,
# 1 = probe failure(s), 2 = the script or tree itself is broken
# (planner-artifact error, not a violation).
set -u
fail_count=0

M=claude/MASTER.md
if [ ! -f "$M" ]; then
  echo "[checkpoint ERROR] expected file missing: $M"
  exit 2
fi

NORM="$(tr '\n' ' ' < "$M" | tr -s ' ')"

probe_present() {
  label="$1"; fixed="$2"
  if printf '%s' "$NORM" | grep -Fq -- "$fixed"; then
    echo "[probe PASS] $label"
  else
    echo "[probe FAIL] $label"
    fail_count=$((fail_count+1))
  fi
}

probe_absent() {
  label="$1"; fixed="$2"
  if printf '%s' "$NORM" | grep -Fq -- "$fixed"; then
    echo "[probe FAIL] $label"
    fail_count=$((fail_count+1))
  else
    echo "[probe PASS] $label"
  fi
}

probe_present "board-46 landing sid recorded (row 46 + sitting block)" \
  "2026-08-18-board-46-doc-deltas-006"
probe_absent "contract-of-record deferrals all converted or replaced" \
  "contract of record until"
probe_absent "consumed forecast_departures rider struck from the registry" \
  'gains a `forecast_departures` sentence'
probe_absent "consumed pair-registration rider struck from the registry" \
  "sanctioned-parallelism registration"
probe_present "pairs-pin rider queued onto board 49" \
  "fifth-pair pin bump"

# Header probe: the last-landed-by line names a continue-plan-005
# sitting successor, not the two-landings-stale 002 sid.
HDR="$(grep '^Last landed by:' "$M" || true)"
if [ -n "$HDR" ] && ! printf '%s' "$HDR" | grep -q "sitting-close-deltas-002"; then
  echo "[probe PASS] last-landed-by header updated off the stale 002 sid"
else
  echo "[probe FAIL] last-landed-by header updated off the stale 002 sid"
  fail_count=$((fail_count+1))
fi

if [ "$fail_count" -gt 0 ]; then
  echo "[checkpoint] $fail_count probe(s) failed"
  exit 1
fi
echo "[checkpoint] all probes passed"
exit 0
