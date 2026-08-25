#!/usr/bin/env bash
# Blind checkpoint — sitting-close deltas, the 49b sitting
# Authored at the 2026-08-24-continue-plan-008 desk (its close), from
# the request, before implementation. v1 (derived from the 49a v1
# skeleton).
#
# Contract: runs in staging (cwd = staging root) beside validation.sh;
# [PASS]/[FAIL]/[SKIP <reason>] per probe; exit 0 all-pass, 1 any-fail,
# 2 script error. Outcome-only probes by design: bundle-format internals,
# placement mechanics, wrap seams, and token-stream tooling are
# deliberately unprobed — they are spec in the brief, and pinning them
# would bind mechanism. Dry-run at the desk against base: all 4 FAIL.
set -u
FAILS=0
p() { printf '%s\n' "$1"; }
fail() { p "[FAIL] $1"; FAILS=$((FAILS+1)); }
pass() { p "[PASS] $1"; }

if ! command -v python3 >/dev/null 2>&1; then
  p "[SKIP] all probes: python3 not found"
  exit 0
fi

norm() { tr -s '[:space:]' ' ' < "$1"; }

M="claude/MASTER.md"

# P1 — the header's last-landed-by line names this landing: a
# sitting-close-deltas sid (date-agnostic pattern) and no longer the
# prior literal. Both conditions, so a stale header FAILs either way.
hdr=$(grep "Last landed by:" "$M" 2>/dev/null | head -n 1)
if printf '%s' "$hdr" | grep -Eq "sitting-close-deltas-[0-9]{3}" \
   && ! printf '%s' "$hdr" | grep -q "2026-08-24-sitting-close-deltas-007"; then
  pass "P1 header-last-landed-by-updated"
else
  fail "P1 header-last-landed-by-updated: header is missing or still names the prior close: $hdr"
fi

# P2 — the row-49 arc-complete bracket landed (fixed payload phrase,
# whitespace-normalized).
if [ -f "$M" ] && norm "$M" | grep -q "the desk types neither"; then
  pass "P2 row-49-arc-complete-bracket-landed"
else
  fail "P2 row-49-arc-complete-bracket-landed: bracket phrase absent"
fi

# P3 — the section-7 version landmark reads 0.4.14 (fixed payload
# phrase, whitespace-normalized).
if [ -f "$M" ] && norm "$M" | grep -q "VERSION 0.4.14 at"; then
  pass "P3 version-landmark-0-4-14"
else
  fail "P3 version-landmark-0-4-14: landmark phrase absent"
fi

# P4 — the clipboard registry entry carries its consumed bracket
# (fixed payload phrase, whitespace-normalized).
if [ -f "$M" ] && norm "$M" | grep -q "crafter half consumed"; then
  pass "P4 clipboard-rider-consumed-bracket-landed"
else
  fail "P4 clipboard-rider-consumed-bracket-landed: bracket phrase absent"
fi

if [ "$FAILS" -gt 0 ]; then
  p "checkpoint: $FAILS probe(s) failed"
  exit 1
fi
p "checkpoint: all probes passed"
exit 0
