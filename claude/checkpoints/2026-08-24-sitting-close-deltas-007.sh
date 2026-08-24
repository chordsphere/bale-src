#!/usr/bin/env bash
# Blind checkpoint — sitting-close deltas, the 49a-ii sitting
# Authored at the 2026-08-24-continue-plan-005 desk, from the
# request, before implementation. v1 of this session's lineage.
#
# Doc-only session; all probes read claude/MASTER.md. Block text in
# the brief is desk-authored preserved text, so distinctive phrases
# from it are pinnable as fixed strings (the provenance-split rule);
# all matching is whitespace-normalized (wrap-tolerant, standing
# desk rule). Sid patterns are date-agnostic: the session's own sid
# is matched by slug substring only; the one dated sid probed (P1's
# stale value) is a fixed historical string, not a pattern.
# Dry-run at the desk against the base at
# 2026-08-24-sitting-close-deltas-004: all 5 probes FAIL.
set -u
FAILS=0
p() { printf '%s\n' "$1"; }
fail() { p "[FAIL] $1"; FAILS=$((FAILS+1)); }
pass() { p "[PASS] $1"; }

M="claude/MASTER.md"
if [ ! -f "$M" ]; then
  p "[FAIL] P0 $M missing from tree"
  exit 1
fi
NORM=$(tr -s '[:space:]' ' ' < "$M")

# P1 — the header's last-landed-by line was edited in place: the
# stale sid is gone from that line and a sitting-close sid is
# seated. The line is single-line by the doc's own convention.
hdr=$(grep "Last landed by:" "$M" | head -1)
if printf '%s' "$hdr" | grep -q "sitting-close-deltas" \
   && ! printf '%s' "$hdr" | grep -q "sitting-close-deltas-004"; then
  pass "P1 header-last-landed-by-updated"
else
  fail "P1 header-last-landed-by-updated: line is: $hdr"
fi

# P2 — the row-49 bracket records the arc position.
if printf '%s' "$NORM" | grep -q "49a-ii DONE"; then
  pass "P2 row-49-bracket-records-49a-ii-done"
else
  fail "P2 row-49-bracket-records-49a-ii-done: '49a-ii DONE' absent"
fi

# P3 — the §3 sitting block landed and hands the agenda forward.
if printf '%s' "$NORM" | grep -q "49b heads the next desk's agenda"; then
  pass "P3 sitting-block-present-agenda-handed-to-49b"
else
  fail "P3 sitting-block-present-agenda-handed-to-49b: phrase absent"
fi

# P4 — the §7 modules enumeration gained the new sibling.
if printf '%s' "$NORM" | grep -q "bale_open"; then
  pass "P4 modules-enumeration-carries-bale_open"
else
  fail "P4 modules-enumeration-carries-bale_open: 'bale_open' absent"
fi

# P5 — the §7 version landmark trued up.
if printf '%s' "$NORM" | grep -q "VERSION 0.4.13 at"; then
  pass "P5 version-landmark-trued-to-0.4.13"
else
  fail "P5 version-landmark-trued-to-0.4.13: 'VERSION 0.4.13 at' absent"
fi

if [ "$FAILS" -gt 0 ]; then
  p "checkpoint: $FAILS probe(s) failed"
  exit 1
fi
p "checkpoint: all probes passed"
exit 0
