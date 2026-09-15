#!/usr/bin/env bash
# Blind checkpoint — sitting close deltas 8 (claude/MASTER.md landing).
# Authored at the desk from the brief's own bytes, before landing.
# Reads MASTER.md with all whitespace collapsed, so the doc's wrapping
# cannot help or hurt a probe. Exit 0 pass, 1 a check failed, 2 oracle error.
set -u
[ -f claude/MASTER.md ] || { echo "[ERROR] claude/MASTER.md missing from the applied tree"; exit 2; }
fails=0
N=$(tr -s '[:space:]' ' ' < claude/MASTER.md)
has() { case "$N" in *"$2"*) echo "[PASS] $1";; *) echo "[FAIL] $1 — phrase absent: $(printf %s "$2" | cut -c1-60)…"; fails=$((fails+1));; esac; }

has '§3 block header' 'Landed 2026-09-15, the continue-plan-001 sitting (master `2026-09-15-continue-plan-001`, read-only;'
has '§3 wave record' 'one session, `2026-09-15-board-94-clock-discipline-002`, 0.4.30, one clarification round'
has '§3 clock finding' 'the machine'\''s local date is the UTC date and the skew is chat-versus-bale, four hours a night'
has '§3 sequencing' '91 and 95 beside each other (91 holds `schemas/` and a pin;'
has 'row 94 DONE' '94. **Clock discipline + the `context/` prefix** — DONE.'
has 'row 95' '95. **Handoff-gate tests fail on shipped bytes** — queued 2026-09-15'
has 'row 96' '96. **Terminal shapes: the light question tier, and the chat invitations struck** — queued 2026-09-15'
has 'row 96 admission' 'admitted when the set holds at most three questions, none multi-tiered'
has 'row 97' '97. **Where ADRs live: one spelling** — queued 2026-09-15'
has 'row 98' '98. **Stats read-side `context/` normalization** — queued 2026-09-15'
has 'row 91 grown' 'Grown 2026-09-15: board 94 re-found the gap from the other side'
has 'row 84 grown' 'Fourth specimen 2026-09-15: board 94'\''s `includes_missing` named the `HandoffFixture` consumer suites'
has '§5 one clock' '**One clock (2026-09-15, this sitting).**'
has '§5 terminal shapes' '**Terminal shapes (2026-09-15, this sitting; lands at row 96).**'
has '§6 132' '132. **A surface named from memory, twice in one sitting.**'
has '§6 135' '135. **The registry consulted at close, not at dispatch.**'
has '§7 include rule' 'Include-authoring rule, accreted 2026-09-15:'
has '§7 applied convention' 'The "applied" report convention, recorded once:'

# header edited in place: exactly one "Last landed by" line, naming a close-8 sid
c=$(grep -c "^Last landed by:" claude/MASTER.md)
if [ "$c" -eq 1 ] && grep -q '^Last landed by: `2026-09-15-sitting-close-deltas-8-[0-9][0-9][0-9]`\.' claude/MASTER.md; then
  echo "[PASS] header last-landed-by line edited in place to a close-8 sid"
else
  echo "[FAIL] header last-landed-by line: count=$c or not a close-8 sid"; fails=$((fails+1))
fi
# and the close-7 sid no longer holds the header (the edit is in place, not appended)
case "$N" in *'Last landed by: `2026-09-14-sitting-close-deltas-7-012`'*) echo "[FAIL] header still names close-7"; fails=$((fails+1));; *) echo "[PASS] header no longer names close-7";; esac

echo "checkpoint: $fails failing"
[ "$fails" -eq 0 ] && exit 0 || exit 1
