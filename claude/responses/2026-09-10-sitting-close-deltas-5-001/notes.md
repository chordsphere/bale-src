# notes.md — 2026-09-10-sitting-close-deltas-5-001

One file, `claude/MASTER.md`, 334 diff lines, additive except three
in-place edits (header last-landed-by line, the §7 VERSION landmark,
one registry sentence re-wrapped around its new bracket). Every edit
went in as an anchored replacement that had to match exactly once;
the diff is worth a skim end to end — it's all prose, no code.

Base file hash matched the manifest's `base_files` stamp before I
touched it. The chat round with the desk (three questions, three
answers) is the source for everything below marked "desk answer".

## Brief defects the desk conceded (record, per the brief's own ask)

- **"Bump the doc's version header one step" — overridden** (desk
  answer 2). v-numbers mark regenerations, not closes; close-004
  set the precedent. The header stays `v5 — 2026-08-16` and its
  supersession sentence is untouched; only the last-landed-by line
  changed. Flagged here as the brief defect the desk conceded.

## Facts trued up against telemetry rather than the brief

- **Board 70 had a `rejected` retry** (16:56:31) between the HOLD
  and the PASS retry — the brief omitted it. Recorded on the row in
  the desk's wording as designed control flow: one gate-refused
  retry (accept flag omitted; the refusal named it), then the
  accepted retry — the predicted sequence (desk answer 3).
- Both amendment accepts are in telemetry as `stamp_matched: false`
  on PASS retries with a changed checkpoint sha (70: 1670fec…→
  439489b…; 71: 7bb83e…→5ffdf5…). The prose records went on each
  row ("this sentence is its prose record", the §3 wave-3
  precedent), and the §3 amendment-accept watch gained both sids so
  HOLD-clustering reads don't misread them as oracle overrides.
- Board 70's record carries `work_class: mixed`; the row says so.
- Board 71's record carries `includes_missing:
  tests/test_per_sid_checkpoint.py` and `clarification.rounds: 0` —
  i.e. the fixture arrived by informal ask, not the exchange. That's
  the live specimen for evidence 112, so I cited it there and on
  the row rather than leaving the brief's claim unsupported.
- Board 71's worker record sites the bundle-backstop step at
  BALE.md §8.1; the brief's VERBATIM text says "§11 row 37 / step
  18". I kept the VERBATIM string exactly and added the §8.1 siting
  in a parenthetical attributed to the worker's record. Same
  pattern at one other spot in row 70: "(the §3 registry)" inserted
  after "standing convergence question" so the pointer resolves.
  Both are additions inside VERBATIM-marked prose — strike them if
  you read the VERBATIM rule as forbidding any insertion.

## Placement calls (the brief's "flag anything you had to interpret")

- **Close block** at the §3 tail, in close-004's shape: pointers to
  row homes, only homeless facts restated. The sitting paragraph
  from the brief is folded into the block's lead-in rather than
  landing as a separate narrative (the v4 convention: no per-sitting
  narrative accretes in §2).
- **Sequencing for the next desk** lives in the close block as a
  bullet (precedent: 004's "Sequencing rider"), not as a separate
  §3 subsection. Row 73 also carries a one-clause pointer to it.
- **Row 72** is a born-resolved row — the brief said "opened or
  resolved" and the doc's identities-not-sequence rule (§4
  preamble) means a resolved report still gets its number.
- **Row 75** recorded IN FLIGHT with the sid and the mid-flight
  drift ratification from desk answer 1; its landing facts are the
  manifest's one `deferred` entry, since they can't be placed yet.
- **Interim operator rule** (HOLD material → planner first) is on
  row 47's new bracket, because its lifetime is "until board 47
  lands" (precedent: row 55's interim rule on its own row).
- **Desk emission rules** are a §7 standing fact (working-style
  bullet), with row 47/74 pointing at them — one home.
- **The purge's unnamed-form repair**: fact on row 70, a pointer
  bracket on row 66 where the original call was ratified.
- **Thinness watch FIRED**: bracket on the §3 watch entry itself
  (it names its own re-trigger), with the three-specimen record in
  evidence 109 and a cross-pointer to entry 95's threshold.
- **Registry strikes** use the existing `[date: consumed — …]`
  bracket form. The stats-dossier hold-back is a bracket *inside*
  the entry's closing parenthesis run, which needed one sentence
  re-wrapped — the only non-additive registry edit.
- **Board 68's "committed-vs-dirt"**: kept the brief's spelling
  ("dirt" is house vocabulary in this doc); if it was a typo for
  "dirty", it's one word.
- Evidence entries 107–112 map 1:1 onto the brief's six; §7-class
  records all found homes. **Nothing landed under an "unplaced"
  note** — every item in the brief has a placement above.

## Things I did not do

- No edit to the §3 "In flight" bullets at the top of the section
  or to §2 milestones — the going-forward convention says sittings
  don't accrete there.
- No renumbering, no reflow of untouched prose, no CRLF/whitespace
  changes outside the edited spans.

## Ratification queue (for the next sitting's open, per the close block)

This response's judgment calls above, plus row 75's notes.md when
it lands — neither is ratified by the retiring desk; the close block
says so in §3.
