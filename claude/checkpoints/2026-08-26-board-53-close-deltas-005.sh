#!/usr/bin/env bash
# blind checkpoint — board-53-close-deltas, v1
# Contract: TARBALL.md 7.5 — exit 0 all pass, exit 1 any fail.
# Outcome-only probes on claude/MASTER.md; wrap-tolerant where a
# phrase could wrap (normalize newlines before matching); sid and
# flag tokens are single unbroken tokens by the doc's convention.
set -u
fails=0
doc=claude/MASTER.md
norm=$(tr '\n' ' ' < "$doc" 2>/dev/null | tr -s ' ')

# P1: the board-53 landing sid is recorded in the doc.
if grep -qF "2026-08-26-board-53-amend-checkpoint-004" "$doc" 2>/dev/null; then
  echo "[PASS] P1 landing-sid: board-53 landing sid recorded"
else
  echo "[FAIL] P1 landing-sid: board-53 landing sid absent"
  fails=$((fails+1))
fi

# P2: the accounting contract's flag token is recorded.
if grep -qF -- "--accept-unaccounted-oracle" "$doc" 2>/dev/null; then
  echo "[PASS] P2 contract: accept-unaccounted-oracle flag recorded"
else
  echo "[FAIL] P2 contract: accept-unaccounted-oracle flag absent"
  fails=$((fails+1))
fi

# P3: the section-7 version landmark moved off the 0.4.16 base
# (wrap-tolerant, inverted: the stale phrase must be gone).
if printf '%s' "$norm" | grep -qF "VERSION 0.4.16 at"; then
  echo "[FAIL] P3 landmark: section-7 version landmark still reads 0.4.16"
  fails=$((fails+1))
else
  echo "[PASS] P3 landmark: section-7 version landmark moved off 0.4.16"
fi

[ "$fails" -gt 0 ] && exit 1
exit 0
