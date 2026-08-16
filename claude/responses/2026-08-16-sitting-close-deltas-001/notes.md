# notes.md — 2026-08-16-sitting-close-deltas-001

Everything in the brief landed; nothing new was decided. Both
changed paths are the forecast exactly. Substance is per the brief
and the three cited notes.md files (quoted or near-verbatim where
the brief said verbatim matters); wording of the record blocks is
mine. A handful of placement calls to glance at, roughly in order
of how much I'd want you to look — none changes substance, all are
one-edit reversible.

## Placement and convention calls (recording, not deciding)

- **Discharges stayed on the registry list, bracket-annotated in
  place**, rather than being removed and recorded only in a
  "Cleared at this landing" paragraph (the sitting-close-004
  precedent removed its cleared entry). I read this request's
  constraint — "append and annotate, never rewrite ratified prose"
  — as forbidding the removal, and the brief's own "Discharge with
  dated brackets" as confirming annotation-in-place. The new
  cleared paragraph still exists (newest-first, per convention) and
  points back at the brackets, so both discharge surfaces agree. If
  the desk prefers the removal convention, the fix is deleting the
  two bracket-annotated entries — their content survives in the
  paragraph and the sitting record.
- **The three TARBALL.md riders were never registry entries** (they
  were queued and consumed inside the sitting, between the 08-14
  landing and this pack), so there was nothing to bracket; their
  discharge is recorded in the cleared paragraph with an explicit
  "never carried on this list" note.
- **Board rows 36–39 were minted as numbered rows**, not agenda
  bullets, because the brief says "board-queue entry/entries" three
  times — a deliberate departure from the 004 precedent's
  reluctance to mint rows for unpacked sessions (that reluctance
  was about the planner-doctrine extraction specifically, which
  stays an agenda item as before). Numbers are identities: if you'd
  rather these ride as agenda items, the rows should be tombstoned
  to pointers, not renumbered.
- **The judgment-calls block is dated 2026-08-14/15**, a range,
  where every precedent block carries a single date — the sitting's
  ratification rounds span both days (006 landed 08-14; the second
  and third chat rounds are dated 08-15 in the brief) and I didn't
  want to invent a single day. Restate if the desk keeps single
  dates.
- **The fifth-global-doc charter resolution lives inside the
  PLANNER.md queue entry's bracket** (board 10), not in §5's
  contracts. The brief's enumeration routes it to "PLANNER.md brief
  inputs," and the entry is where the extraction session will read
  from — but it is charter-shaped, and if the desk wants it
  re-litigation-protected the §5 record is a follow-up append (the
  bracket's text is written to lift cleanly). Same for the one-doc
  / orchestration.md-merge ruling, which sits in the new S6 agenda
  block with its quotable rationale.
- **The ahead-of-S6 queue move is recorded as recommended, NOT
  ratified**, with "ratify at next sitting open" — exactly the
  brief's status. The board ordering itself is untouched.
- **Evidence 79 cites "board 37"** (the bail-recalibration row
  minted in this same landing) and the row cites entry 79 back —
  self-consistent within the response, but if the rows are demoted
  per the bullet above, both cites need the same edit.
- **The HOLD-triage S6 item is one line** ("ranked high", routed
  from README item 2) because the brief carried no further
  substance for it; I didn't invent scope for an S6 agenda item the
  spec-intake will define.

## Verification notes

- Append-and-annotate held mechanically: the diff against the
  shipped MASTER.md removes exactly five lines — the header's
  last-landed-by line (edited in place per its own recorded
  convention) and four lines that reappear verbatim with a dated
  bracket appended at the wrap point. `validation.sh` asserts the
  survival of the prior sitting's blocks, the engraved-principle
  opening clause (exactly once — the full sentence still appears
  nowhere in MASTER.md), the untouched registry entries, and that
  the `TODO(brief)` literal count is unchanged (the board-33 row's
  known inline carry; nothing new trips the placeholder refusal).
- INDEX.md: the reworded sentence names the guard test by path per
  the brief; the note's other content (`bin/bale`-references
  sentence, not-injected sentence, routing note, category-of-one
  paragraph) is asserted intact.
- Fitting detail: this response's own claims reconciliation runs
  the label-column cap ratified at this sitting — the long
  assertion labels overflow past 40 in full, per
  overflow-not-truncate.

## Claims basis

Both claims are `observed`: `validation.sh` ran end-to-end against
a staging simulation (shipped `claude/` copies + `files/` overlay +
no-op `apply.sh`, manifest at `.bale-manifest.json`) — every
assertion `[ok]`, both reconciliation rows `[agree]`, exit 0. The
lint ran clean after the feedback block was pasted from its own
emission.
