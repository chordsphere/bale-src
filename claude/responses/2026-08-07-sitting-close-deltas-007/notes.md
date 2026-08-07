# notes — 2026-08-07-sitting-close-deltas-007

All brief items landed (H, V, F, W, R, C5, J, E, S). Relay to the
master per the standing constraint. No stop-and-clarify disagreements
arose: everything the brief asserts checked out against the archived
notes, the board-13-arc artifacts, and the shipped tree. The items
below are readings I made and two things worth a close look.

## Verification the brief asked for

The version endpoint was read from the shipped bin/bale constant
(line 225: `VERSION = "0.4.2"`) and the request's own provenance
stamp (`bale_version: 0.4.2`) agrees — the brief's arithmetic also
happened to agree, but the landed value is the read one. The four
fold-in verbatim blocks were fingerprint-checked against the archived
notes normalized (lines joined, per the DOCS.md §9 habit) and match
byte-for-byte modulo wrapping.

## Readings I made (say if any is wrong)

- **The watches parenthetical.** Adding two entries falsified the
  list intro's "the last from `2026-08-05-auto-sweep-009`'s notes,"
  so I trued it up ("one from ..., and the last two from the
  board-13 arc"). One sentence beyond the brief's letter, on the
  same surface the brief edits — flagging under "nothing else
  changes" discipline.
- **Board row 13 condensed** per the arc-close precedent (rows 34,
  6, 5): the five evidence-25 tallies and the architect's ratified
  design-input bracket dropped to git, with the row saying so. The
  design input's content now lives in ADR-0015 (the §5 one-home
  contract), and evidence 25 keeps its own annotated entry, so
  nothing normative was orphaned.
- **Board row 35's ranked gap list kept verbatim** — the row itself
  claims "verbatim from `2026-08-06-v04-selftest-audit-006`'s
  notes," so striking gaps 1–2 from it would break that claim. Only
  the spent "First session:" proposal paragraph was replaced with
  the session-1 DONE record; the DONE paragraph governs status.
- **R entries' `>` markers** read as the brief's quoting device, not
  shipped bytes (the 008-session precedent); the What/Why/Scope
  paragraphs joined inline per the registry's handoff-`--verbose`
  entry idiom. Characters unchanged.
- **E59 recorded as a new numbered entry**, per the brief's "three
  §6 entries" — the doc's prior idiom bracketed the *second* §11.6
  recovery onto entry 12, so a third bracket there was the
  alternative shape. I followed the brief and added "(entry 12
  carries the first two)" so the thread stays traceable from either
  end.
- **The J block header** sid-maps 004/005/006 following the
  2026-08-06 block's idiom, per the bare-NNN-collides convention.

## Look closely

- **§3's first bullet (the board-10 tidy-up sitting) is left
  byte-untouched** per "Nothing else in MASTER.md changes" — but it
  ends "The sitting-close deltas — this landing — carried the
  cargo," and with a newer landing now in the doc, "this landing"
  reads ambiguously (it means the 08-06 one). Reported, not fixed;
  proposal below.
- **Commit `d4874ae` in board row 13 is carried from the brief.** A
  MASTER.md-only request ships no git, so the hash is unverifiable
  from here; I verified the `claude/context/board-13-arc/` files
  exist as shipped and carried the hash as brief-sourced.

## Proposals

- **Retire the closed tidy-up bullet from §3 In flight.** What: drop
  (or collapse to one line) the "board-10 tidy-up sitting ... is
  closed" bullet at the next MASTER.md-touching session. Why: a
  closed sitting is not in-flight — DOCS.md §3.2's move-or-delete
  rule — and its facts already live in the board rows, §5, and §6
  entries 55–57; leaving it also strands the ambiguous
  "this landing" phrase flagged above. Scope hints: MASTER.md §3
  only; a natural rider on the next sitting-close deltas.
