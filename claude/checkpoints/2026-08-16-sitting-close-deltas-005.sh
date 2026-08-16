#!/usr/bin/env bash
# checkpoint-sitting-close-v2.sh
# Blind checkpoint for the 2026-08-16 sitting-close-deltas session.
# v2 AMENDMENT (HOLD->correction, 2026-08-16): the engraved-clause
# probe was wrap-blind — the clause hard-wraps in MASTER.md, so the
# v1 single-line grep counted 0 at base and would HOLD any response.
# That one probe is now wrap-tolerant; every other probe is
# byte-identical to v1 (all passed against the landed bytes).
#
# Writes to: nothing. Read-only assertions against the staging copy.

set -u
M=claude/MASTER.md
fails=0

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf '[PASS] %s\n' "$label"
  else
    printf '[FAIL] %s\n' "$label"
    fails=$((fails + 1))
  fi
}

# --- The records landed (anchors verbatim from the brief's blocks) --
check "section-5 lift: fifth-global-doc entry"   grep -q "PLANNER.md is the fifth global doc" "$M"
check "section-5 lift: one-doc merge entry"      grep -q "One doc: orchestration.md merges into PLANNER.md" "$M"
check "queue-reorder record present"             grep -q "by exercise" "$M"
check "oracle-authorship judgment call present"  grep -q "Master-desk oracle authorship affirmed" "$M"
check "board-10 EXECUTED bracket present"        grep -q "EXECUTED at" "$M"
check "bracket names the birth sid"              grep -q "planner-birth-003" "$M"
check "section-6 accretion line present"         grep -q "now lives in docs/PLANNER.md" "$M"

# --- Nothing ratified was rewritten ----------------------------------
check "engraved clause appears exactly once (wrap-tolerant)" bash -c 'test "$(tr -s "[:space:]" " " < claude/MASTER.md | grep -o "Mechanism authority sits with the session that has the code in context" | wc -l)" -eq 1'
check "TODO(brief) literal count unchanged (1)"  bash -c 'test "$(grep -c "TODO(brief)" claude/MASTER.md)" -eq 1'
check "prior block survives: bare-pack entry"    grep -q "bare-pack restoration mechanism" "$M"
check "prior section survives: findings register" grep -q "Foundation-audit findings register" "$M"

# --- Verdict ----------------------------------------------------------
if [ "$fails" -eq 0 ]; then
  printf 'checkpoint: PASS\n'
  exit 0
else
  printf 'checkpoint: FAIL (%d)\n' "$fails"
  exit 1
fi
