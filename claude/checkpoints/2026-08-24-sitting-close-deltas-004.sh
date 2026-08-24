#!/usr/bin/env bash
# Blind checkpoint — 2026-08-24 sitting-close deltas
# Authored at the 2026-08-24 master sitting desk, from the request,
# before implementation. v1 for this session.
#
# Contract: runs in staging (cwd = staging root) beside validation.sh;
# [PASS]/[FAIL]/[SKIP <reason>] per probe; exit 0 all-pass, 1 any-fail,
# 2 script error. Probes are whitespace-normalized (wrap-blind by
# construction) and pin phrases from the brief's desk-authored blocks —
# preserved text the worker must carry token-identically, so fixed-
# string pins are provenance-correct. Placement is asserted by the
# worker's own anchor-window validation per the brief; this oracle
# grades presence and the header edit. No sid patterns; nothing
# date-pinned to the pack date (the standing date-agnostic rule).
# Dry-run at the desk against base: all 7 FAIL.
set -u
FAILS=0
p() { printf '%s\n' "$1"; }
fail() { p "[FAIL] $1"; FAILS=$((FAILS+1)); }
pass() { p "[PASS] $1"; }

M="claude/MASTER.md"
if [ ! -f "$M" ]; then
  p "[FAIL] P0 master-doc-present: $M missing from staging"
  p "checkpoint: 1 probe(s) failed"
  exit 1
fi

NORM=$(tr -s '[:space:]' ' ' < "$M")
has() { printf '%s' "$NORM" | grep -qF "$1"; }

# P1 — header edited in place: the Last-landed-by line no longer
# carries the predecessor sid, and carries a sitting-close-deltas sid
# (date-agnostic; only the slug family is pinned).
HDR=$(grep "^Last landed by:" "$M" | head -n 1)
if printf '%s' "$HDR" | grep -q "sitting-close-deltas-" \
   && ! printf '%s' "$HDR" | grep -qF "2026-08-24-sitting-close-deltas-001"; then
  pass "P1 header-last-landed-by-replaced"
else
  fail "P1 header-last-landed-by-replaced: line reads: $HDR"
fi

# P2 — Block B (unconsumed-intents watch) present.
if has "Unconsumed pre-answered intents (ratified 2026-08-24)"; then
  pass "P2 watch-unconsumed-intents-present"
else
  fail "P2 watch-unconsumed-intents-present: Block B phrase absent"
fi

# P3 — Block C (validate.sh rider strike) present.
if has "consumed — the 49a-i session's validate.sh true-up"; then
  pass "P3 foldin-validate-loop-struck"
else
  fail "P3 foldin-validate-loop-struck: Block C phrase absent"
fi

# P4 — Block D (apply-side bundle backstop entry) present.
if has "Apply-side bundle backstop (accepted 2026-08-24"; then
  pass "P4 foldin-apply-backstop-present"
else
  fail "P4 foldin-apply-backstop-present: Block D phrase absent"
fi

# P5 — Block E (dated sitting record) present: opener and the
# fifth-specimen line both land.
if has "Landed 2026-08-24 (the resumed-49 sitting" \
   && has "Fifth checkpoint-desk miss specimen"; then
  pass "P5 sitting-record-present"
else
  fail "P5 sitting-record-present: Block E opener or specimen line absent"
fi

# P6 — Block E carries the standing rule verbatim (token stream).
if has "sid patterns in oracles are date-agnostic from now on"; then
  pass "P6 date-agnostic-rule-recorded"
else
  fail "P6 date-agnostic-rule-recorded: standing-rule phrase absent"
fi

# P7 — Block F (row-49 bracket) present.
if has "49a-i DONE"; then
  pass "P7 board-row-49-bracket-present"
else
  fail "P7 board-row-49-bracket-present: Block F phrase absent"
fi

if [ "$FAILS" -gt 0 ]; then
  p "checkpoint: $FAILS probe(s) failed"
  exit 1
fi
p "checkpoint: all probes passed"
exit 0
