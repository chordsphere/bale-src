#!/usr/bin/env bash
# checkpoint-ratification-microdeltas-v2.sh
# Blind checkpoint for the 2026-08-16 ratification-microdeltas
# session, v2: rev2 brief adds Block E (the wiring landing); three
# probes added for it, everything else identical to v1. Authored at the planner desk under the two rules this
# very landing records: every phrase probe is wrap-tolerant, and the
# file was dry-run against real bytes before delivery.
#
# Writes to: nothing. Read-only assertions against the staging copy.

set -u
M=claude/MASTER.md
# Whitespace-normalized copy of the doc: wrap-tolerant matching.
W="$(tr -s '[:space:]' ' ' < "$M")"
fails=0

wt() {
  # wt <label> <phrase> [expected-count]  (default: at least 1)
  local label="$1" phrase="$2" expect="${3:-}"
  local n
  n=$(printf '%s' "$W" | grep -o -F "$phrase" | wc -l | tr -d ' ')
  if [ -n "$expect" ]; then
    if [ "$n" -eq "$expect" ]; then printf '[PASS] %s\n' "$label"
    else printf '[FAIL] %s (count %s, expected %s)\n' "$label" "$n" "$expect"; fails=$((fails+1)); fi
  else
    if [ "$n" -ge 1 ]; then printf '[PASS] %s\n' "$label"
    else printf '[FAIL] %s (absent)\n' "$label"; fails=$((fails+1)); fi
  fi
}

# --- The records landed ----------------------------------------------
wt "block A: landing record present"        "with one HOLD"
wt "block A: wrap-tolerant desk rule"       "matched wrap-tolerant"
wt "block A: dry-run desk rule"             "dry-run against real bytes before delivery"
wt "block A: closure-kind blemish recorded" "undercounts supersessions by one"
wt "block A: stamp record mentioned"        "stamp_matched false"
wt "block B: protocol contract entry"       "The bad-oracle correction protocol."
wt "block B: reveal-spec line"              "reveal-spec-not-script"
wt "block C: mechanization mandate"         "Session-interaction mechanization mandate"
wt "block C: architect-as-transport clause" "route through the architect as transport"
wt "block D: transport-integrity row"       "readme/brief transport integrity"

wt "block E: wiring landing record"         "planner-injection-wiring-006"
wt "block E: five-doc era named"            "five-doc era"
wt "block E: exactly-the-set call recorded" "Exactly-the-set assertions ratified"

# --- Nothing ratified was rewritten ----------------------------------
wt "engraved clause appears exactly once" "Mechanism authority sits with the session that has the code in context" 1
wt "fifth-global-doc lift survives"       "PLANNER.md is the fifth global doc" 
wt "one-doc lift survives"                "One doc: orchestration.md merges into PLANNER.md"
wt "EXECUTED bracket survives"            "EXECUTED at"
check_todo=$(grep -c "TODO(brief)" "$M")
if [ "$check_todo" -eq 1 ]; then printf '[PASS] TODO(brief) literal count unchanged (1)\n'
else printf '[FAIL] TODO(brief) literal count unchanged (count %s, expected 1)\n' "$check_todo"; fails=$((fails+1)); fi

# --- Verdict ----------------------------------------------------------
if [ "$fails" -eq 0 ]; then
  printf 'checkpoint: PASS\n'
  exit 0
else
  printf 'checkpoint: FAIL (%d)\n' "$fails"
  exit 1
fi
