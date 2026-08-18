# notes.md — 2026-08-18-board-46-doc-deltas-006

All ten cargo items landed; the three guard suites pass against the
changed set and validation.sh's negative test confirmed the landing
probes actually fail when a landing is broken. Base pins verified
against the shipped bytes before any edit — all three matched. The
latitude calls, per the flagged-deviation loop:

## Placement and voice calls

- **Item 9 (hooks rule) → PLANNER.md §2.** I read it as
  authoring-surface doctrine — what an authored artifact may rely
  on — rather than harness tool-design doctrine, so it landed as a
  core §2 bullet beside the other "author around the environment"
  rules, phrased at the artifact level ("an authored artifact that
  relies on a hook firing has delegated part of its contract to a
  surface no gate reads"). If you read it as tool-design doctrine
  instead, §17's transport-agnostic thread is the alternate home;
  moving it is a clean lift.
- **Item 3 (calibration sitting) → one bullet in §6, nothing past
  the banner.** The brief offered a deliberate split with the
  stats-digest input side landing harness-side. I kept the doctrine
  whole: sittings are present-tense core practice, the digest line
  is one clause, and splitting a single ratified paragraph across
  the banner would have fragmented the closing-the-loop mechanism
  it describes. The digest's queued status is marked inline
  ("queued tool-side machinery").
- **Item 8 (bad-oracle correction) → §5 in full, one sentence at
  §14.** The six steps landed as a numbered list in §5 (the
  protocol is sequential; prose would bury the forks), and §14
  gained a single sentence routing the fixture-evidence case into
  it. "PLANNER.md at its next churn" is satisfied; the MASTER-side
  record's conversion to record-plus-pointer stays with the sitting
  close, untouched here.
- **Item 5 (scopeless-goal exemption).** Landed on §3.2's goal
  bullet only. §3.4's goal row already ends "(§3.2)", so the
  one-home rule is satisfied by the existing pointer and I made no
  parallel touch — recorded in `deferred` so the decision is
  visible, not silent.
- **Item 1 (hot-file sentence)** landed as the closing sentence of
  §11's disjointness-proof paragraph rather than a new bullet — it
  is the same thought's flip side, and the bullet list below is
  reserved for the evidence-cited packing rules.

## Genericizations (self-containment)

Sources referenced project-local structures; the landings
genericize per the goal-over-enumeration precedent the brief cites:

- Item 3: "board 38 is the queued machinery" → "queued tool-side
  machinery"; "board 44's epoch read side" → "the epoch read the
  records were built to carry"; "a board item" → "a queued work
  item"; the source's "PLANNER.md §6" self-cite dropped (the
  landing *is* §6).
- Item 8: "the board-6 provenance gate" → "the provenance gate";
  "stamp_matched false" → "the recorded stamp mismatch" (I did not
  have the telemetry schema in the include set to confirm the
  field name is stable doc surface, so the concept landed instead);
  "the §5 blindness watch" → "the standing fixture-defect watch"
  citing PLANNER.md's own §4, where that watch already lives.
- Item 10: "§3 watches and fold-in riders" → "watch lists and
  queued fold-in riders", as the brief directed.
- Item 2: the motivating HOLD is cited by concept ("a live
  fixture-defect HOLD"), no evidence number — the brief said cite
  by concept, and I don't hold the ledger entry number.

## Item 6: forecast_departures — deliberately a mention, not a
contract

The rider's own text says the schema description "carries the full
contract meanwhile," so the landed paragraph names the field, gives
its concept-level meaning (the structured record of `changes[]`
paths outside the stamped forecast, twin of the §5.4 enumeration),
and defers stream placement, shape, and fill semantics to
`response-manifest.schema.json` explicitly. I did not assert which
stream the field rides because `response-manifest.schema.json` was
not in the include set and mechanical-vs-self-reported is exactly
the kind of fact that must not be guessed (it is recorded in
`feedback.self_reported.includes_missing`). If the schema puts it
in one stream and you want the walk-through to say so, that is a
one-clause follow-up touch.

## Item 7: the fifth pair and the guard tests

The registration is phrased generically — the project-side member
is "the project-side planning record that ratified it," unnamed —
which holds `test_global_doc_selfcontainment` (verified: suite
passes). The known wrinkle resolved as the brief's suggested shape;
no clarification needed. But note what the registration does *not*
do: `test_sanctioned_pairs` pins `len(PAIRS) == 4` and its
docstring calls DOCS.md §9's enumeration the source of truth. The
suite still passes (it counts its own table, not the doc), so
nothing breaks mechanically — the enumeration and the table are
now deliberately out of step until the sibling session lands. See
Proposals.

## Verbatim clause mechanics

"never a connective-phrase grep" sits unbroken on its own line in
the §4 bullet so a fixed-string pin matches raw bytes, not just
whitespace-normalized text — the wrap in that bullet is therefore
slightly short of the ~70-column fill; deliberate, the same class
of exception as unbroken sids. validation.sh carries the byte-exact
self-check §2's corollary requires.

## Proposals

- **What:** Update `tests/test_sanctioned_pairs.py` for the fifth
  pair: bump the enumeration-count pin to 5 and add a PLANNER.md
  §10-side extract (e.g. "The ratified floor, restated here so this
  half stands alone for its citers"); the project-side twin cannot
  be pinned by that suite (it reads `docs/` only), so the pin is
  one-sided by construction and the comment should say so.
  **Why:** The suite's count pin and DOCS.md §9's enumeration are
  now deliberately out of step; the suite's own docstring says the
  table must not silently cover fewer pairs than the doc.
  **Scope hints:** `tests/test_sanctioned_pairs.py`; expected
  sibling-forecast territory this sitting (the board-49 bundle).
- **What:** Consider a self-containment sweep for bare board-number
  references already in the globals — e.g. TARBALL.md §3.2's
  "(bale v0.3.21, board 33)" — which pass the substring guard but
  dangle conceptually in every other project.
  **Why:** Noticed while landing item 5 in the same section; same
  class as the genericizations this session performed, but outside
  the cargo and not mine to sweep opportunistically under a pinned
  scope.
  **Scope hints:** all five globals; grep `board [0-9]`.
