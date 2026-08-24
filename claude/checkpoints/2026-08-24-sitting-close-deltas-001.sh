#!/usr/bin/env bash
# Blind checkpoint — sitting-close deltas (sub-master sitting)
# Authored at the 2026-08-18-continue-plan-008 desk, from the request,
# before implementation. v1.
#
# All probes pin desk-authored block text (preserved class), split
# around the one worker-filled sid token; wrap-tolerant (whitespace-
# normalized). Dry-run at the desk against base: all FAIL, exit 1.
set -u
M=claude/MASTER.md
[ -f "$M" ] || { printf '[FAIL] missing %s\n' "$M"; exit 1; }
FAILS=0
fail() { printf '[FAIL] %s\n' "$1"; FAILS=$((FAILS+1)); }
pass() { printf '[PASS] %s\n' "$1"; }
N=$(tr -s '[:space:]' ' ' < "$M")
has() { printf '%s' "$N" | grep -qF "$1"; }

# D1 — Block A landed: spans either side of the sid token, plus a
# conforming contract-doc sid between the sitting record's bounds.
if has "Landed 2026-08-18, the sub-master sitting (master \`2026-08-18-continue-plan-008\`, read-only): opened on board 49 as packed" \
   && has "landed at the sitting's contract-doc session" \
   && has "Sitting closed at the milestone; the resumed 49 arc (49a-i first) heads the next sitting's agenda." \
   && printf '%s' "$N" | grep -qE "2026-08-18-submaster-doctrine-[0-9]{3}"; then
  pass "D1 sitting-record-landed-with-contract-doc-sid"
else
  fail "D1 sitting-record-landed-with-contract-doc-sid"
fi

# D2 — Block A's withdrawal record (the load-bearing rationale).
if has "include mass is not consumed budget; the worker decides what it reads, and the drill-down doctrine is load-bearing"; then
  pass "D2 withdrawal-rationale-landed"
else
  fail "D2 withdrawal-rationale-landed"
fi

# D3 — Block A's HOLD-attribution carry-forward.
if has "Fourth checkpoint-desk miss specimen: the pytest runner, the wrap-blind grep, the phrase-pinned authored text, and the notes-region-sourced probe token."; then
  pass "D3 hold-attribution-landed"
else
  fail "D3 hold-attribution-landed"
fi

# D4 — Block B bracket inside row 49.
if has "[2026-08-18: bracketed at the sub-master sitting" \
   && has "49a-i (bundle format + pack-side deny-list"; then
  pass "D4 row-49-bracket-landed"
else
  fail "D4 row-49-bracket-landed"
fi

# D5 — row 53 landed verbatim (its identity line and closing line).
if has "53. **Checkpoint amendment as a first-class verb** — queued 2026-08-18" \
   && has "the sequencing call is the next desk's."; then
  pass "D5 row-53-landed"
else
  fail "D5 row-53-landed"
fi

# D6 — row 54 landed.
if has "54. **Arc-level dual-stream mechanics** — queued 2026-08-18" \
   && has "arc claim/verdict telemetry so reconciliation pairs the sub-master's summed validation with the arc verdict."; then
  pass "D6 row-54-landed"
else
  fail "D6 row-54-landed"
fi

# D7 — evidence 82 landed.
if has "82. **A flat authorship line routed oracle authoring to the operator"; then
  pass "D7 evidence-82-landed"
else
  fail "D7 evidence-82-landed"
fi

# D8 — both registry annotations landed.
if has "[2026-08-18: struck — subsumed, with its §3.4 pair rider, by the sub-master landing" \
   && has "[2026-08-18: struck — re-routed at the desk from board 49 to the sub-master contract-doc session"; then
  pass "D8 registry-annotations-landed"
else
  fail "D8 registry-annotations-landed"
fi

# D9 — header updated: stale sid gone, a same-day sid in its place.
hdr=$(grep "Last landed by:" "$M" | head -1)
if printf '%s' "$hdr" | grep -q "2026-08-18-sitting-close-deltas-007"; then
  fail "D9 header-updated: stale -007 sid still present"
elif printf '%s' "$hdr" | grep -qE "2026-08-18-[a-z-]+-[0-9]{3}"; then
  pass "D9 header-updated"
else
  fail "D9 header-updated: no conforming sid on the header line: $hdr"
fi

if [ "$FAILS" -gt 0 ]; then
  printf 'checkpoint: %d probe(s) failed\n' "$FAILS"
  exit 1
fi
printf 'checkpoint: all probes passed\n'
exit 0
