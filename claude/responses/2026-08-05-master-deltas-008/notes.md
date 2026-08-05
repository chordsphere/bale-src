# notes.md — 2026-08-05-master-deltas-008

All ten deltas landed; both changed paths sit inside the session's
recorded scope, so no drift admissions are needed at apply. VERSION
untouched per the constraint. What follows is the judgment residue.

## Decisions to ratify

- **The stale close-out-vehicles bullet was removed from §3.** Delta
  2 names only the board-6 design/spawn items, but §3's first bullet
  still described the 2026-08-01→03 sitting's close-out vehicles and
  called `2026-08-03-master-deltas-005` "this deltas session" — false
  beside this landing's header line, and "In flight" is a current
  picture by the v4 convention. I removed it rather than leave the
  doc self-contradicting. If you want a current-sitting vehicles
  bullet instead, say the word and a micro-delta restores one; I
  leaned on the header convention (sittings no longer accrete
  narrative) and recorded nothing in its place.
- **The "Next master sitting: pack itself read-only; keep the habit"
  lead-in went with its bullet.** The habit is now mechanical
  (board 33's stamp and sweep; evidence 46's closing note says the
  streak is broken and the check is mechanical) and the §5 scopeless
  contract carries the rule, so I did not re-home the sentence.
- **Delta 10's "§2 milestones" wording had no §2 anchor.** I
  verified before editing, as the brief instructs: §2 carried no
  1.0.0-gate wording (the gate's definition lives in §5's ladder
  contract). The minimal compliant edit was a new §2 arc-milestone
  block for board 6 — the trust-ledger precedent — carrying the
  "board-6 dependency satisfied; waits on board 10" sentence. §5's
  ratified ladder wording is untouched: "gated on boards 6 and 10
  landing" remains accurate as a gate definition now that board 6
  has landed.
- **Delta 3's verbatim scope.** The watch quotes D4.3's decision
  sentence verbatim ("board 10 owns it, for three recorded reasons")
  and cites D4.3 for the reasons rather than paraphrasing them
  inline — the verbatim-proposal contract read as: quote what the
  disposition turns on, point at the rest. I also appended the one
  live datum the report ties to that desk (session A's predicted
  claim graded `agree`); strike it if the watch should stay minimal.
- **§6 numbering and grouping.** The four new entries landed as
  51–54 under one arc heading, findings first (51–53) and the
  version/cadence finding last (54), since 54 is the entry other
  edits cross-reference (§2's arc block, board row 6).

## Classification note, contestable at apply (delta 8's own flag)

The two new fold-in registry entries — the `bale-internals.md` §2.5
true-up and the checkpoint exit-2 stats split — carry named carriers,
which is the registry's shape; the arc report listed them under
on-watch. The brief classifies them into the registry and marks the
classification contestable here. If you read them as watches instead,
the move is two bullets between adjacent §3 lists.

## Look closely on review

- The §3 diff is the response's largest judgment surface: the two
  removed bullets, the one successor bullet, the re-ownered watch,
  and the three verbatim watch carries. `validation.sh` fingerprints
  the three carries against the shipped upward report (normalized
  per DOCS.md §9), so a wording drift there fails mechanically.
- Board row 6's escalation-disposition sentence compresses four
  dispositions into one clause each; confirm it reads as the record
  you want the row to carry.

## Validation and claims basis

Every claim is observed, not predicted: the full pipeline was
rehearsed in this sandbox against a simulated staging (shipped
originals + the `files/` overlay + the no-op `apply.sh` + this
manifest at `.bale-manifest.json`) — exit 0, all three claims
`[agree]`. The project test suite was not run and is not claimed:
the change set is two markdown docs (the §6 worked-example
precedent), the shipped tree carries no `bin/` or `tests/`, and no
test pins these docs' content. The reverse-transform check embeds
the shipped `docs/TARBALL.md` hash — the same value as the request's
`provenance.contract_docs` stamp — so the insertion-only claim is
anchored to the ratification instrument's own baseline. The fidelity
half of check 3 reads the arc sources from the applied tree
(`claude/context/board-6-arc/`) and `[SKIP]`s with a reason if a
source is absent rather than guessing.
