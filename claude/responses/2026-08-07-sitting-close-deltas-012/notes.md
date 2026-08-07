# notes.md — 2026-08-07-sitting-close-deltas-012

## Where the shipped MASTER.md disagreed with the brief's assumptions

Per the brief's closing ask, everything below is a place I diverged
from the brief's letter because the shipped text said to; the master
desk should confirm each reading.

- **The version trail landed in §7, not §2.** The brief's item 3 is
  titled "§2 version paragraph," but the shipped §2 paragraph is a
  one-home pointer ("Current version: one home — §7's bin/bale
  landmark, collapse ratified 2026-08-07"), so the trail's home is
  §7's bin/bale VERSION sentence and I edited it there. §2 is
  untouched, which also satisfies the no-per-sitting-narrative
  constraint by the strictest reading.
- **The 0.4.3 value is relayed, not verified.** The old §7 sentence
  said the version was "read from the constant in the copy shipped
  read-only with this ... request." This request ships no bin/bale,
  so I could not read the constant; I rewrote the provenance clause
  to say the trail is recorded from the sitting's ratified cargo and
  that the standing verify-at-sitting-open rule (§2) is the next
  check. If bin/bale was meant to ride this pack for that
  verification, that is an includes gap to note, not a blocker — the
  §7 landmark precedent already tolerates MASTER.md-only relays when
  marked as such, and this one is marked.
- **Session 1's "Gaps 3–7 remain queued, ordering-free." is
  retained.** It sits inside session 1's dated DONE record, and the
  brief's appended "Remaining queue" line now carries the current
  picture directly below it. The two read consistently as
  record-then-current, but if the desk prefers the stale sentence
  trued up, that is a one-line follow-on edit I did not make
  unprompted (the brief enumerated appends only).
- **INDEX.md's "last Proposed set before that" sentence dropped.**
  With no ADR Proposed, the sentence's "before that" dangled; the
  surviving closing sentence (each ADR file carries its own flip
  record; narrative in git) covers the history. Flagging because it
  is a removal the brief didn't name, made inside the true-up the
  brief did name.
- **The appended ADR Notes line is verbatim from the brief**,
  including "sitting sid 2026-08-07-sandbox-adr-009" — that sid
  names the session that authored the ADR rather than a sitting
  record; relayed as given since the brief quoted the line.

## Verification notes

- Evidence numbering verified from the shipped MASTER.md: max
  existing entry is 60, so the new entry is 61 (the brief's
  verify-don't-trust instruction, followed).
- The ADR-flip confinement is asserted by the evidence-35
  reverse-transform: validation.sh reconstructs the pre-flip file
  from the staged bytes (strip the appended line, un-flip Status)
  and requires sha256 equality with the request's shipped copy
  (hash embedded). Any edit outside the sanctioned shape breaks it.
- INDEX coherence resolves every `- `path`` entry (BALE.md at repo
  root, the rest relative to claude/) and asserts both changed docs
  are listed. All grep anchors are single-line fixed strings per
  DOCS.md §9's rewrapping note.
- The verbatim fold-in quotes (011's two proposals) were copied from
  the archived notes files shipped in context/, not from the brief's
  restatement, per the §5 verbatim-proposal contract; they agree
  with the brief's summaries.
