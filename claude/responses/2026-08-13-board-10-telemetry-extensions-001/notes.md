# notes — 2026-08-13-board-10-telemetry-extensions-001 (correction)

This corrects the first response after its HOLD (blind checkpoint
exit 1, worker validation PASS). The two checkpoint findings split
cleanly: one was a real defect in my response, fixed here; one is a
checkpoint↔record-shape mismatch only you can resolve. Corpus and
suite: 114 records / zero regressions, 376 tests green (~89–97s).

## Finding 1 — fixed here, and it was a fair catch

`[ckpt] FAIL: closure_reason definitely_not_a_reason :: accepted but
should reject`

Reproduced exactly: the first response's validator rejected invented
reasons only at the schema's one named spot
(`attempts[].closure_reason`); a `closure_reason` key at any un-named
depth — I reproduced with the envelope, `rec["closure_reason"]` —
sailed through `additionalProperties: true`. The checkpoint mutated at
a spot I didn't constrain, and it was right to: I had built exactly
this placement-robustness for `claim_basis` (the record-wide walk) and
then trusted a single schema spot for the closure vocabulary. The
inconsistency was mine.

The fix generalizes the walk to both closed vocabularies
(`_walk_closed_vocabularies`): any `claim_basis` key at any depth must
be `predicted` | `observed`; any `closure_reason` key at any depth
must be a known reason **or null** (apply/retry attempts record honest
nulls — the null asymmetry between the two vocabularies is deliberate
and documented in the walk's docstring). The walk derives the closure
set from the schema's own enum rather than importing
`CLOSURE_REASONS`, so the vocabulary keeps its one home with no new
import edge; the existing parity test pins schema ↔ tuple ↔ CLI
together. The exact reproduced mutation now rejects; `no_response` /
`malformed_response` / legacy reasons still pass at any placement.
Two new tests pin it, including a nested-past-the-schema case.

## Finding 2 — not worker-addressable; this is the one for your desk

`[ckpt] FAIL: no claims/validation rows in fixture to carry claim_basis`

The checkpoint never reached its claim_basis pass/fail assertions — it
found no rows to annotate in the fixture it built. My best hypothesis,
flagged as such because the checkpoint is off-limits to me: it builds
fixtures on the brief's row model — "rows in the record's claim-bearing
arrays (`validation_will_run` and any sibling that carries claims)" —
and **zero of the 114 corpus records carry a `validation_will_run` key
at any depth** (verified mechanically; it's a response-manifest
structure that is not promoted into the record). The record's actual
claim-bearing rows are `attempts[].validation.claims` (promoted
verbatim from the manifest) and `attempts[].validation.claim_verdict`
(the parsed §7.3 reconciliation), and on those rows my enforcement is
live and staging-proven: the worker validation you saw pass drove
predicted/observed accepts and an invented-value reject on both row
kinds, through the same library-import posture the checkpoint uses.

A secondary possibility worth one glance: if the checkpoint selects
"youngest" by mtime, target-base staging (`git checkout` into staging)
normalizes every mtime to checkout time, making the pick arbitrary —
it may then land on a record with `validation: null` (an unlock close),
which also has no rows. Sorting by filename or by the records' own
`created_at` would make the pick stable and land on
`2026-08-12-board-10-wave1-deltas-002`, which carries five claims rows.

Either way, no in-forecast change can clear this finding: the corpus
lives under `claude/` (out of scope), the checkpoint is yours by
contract, and inventing a `validation_will_run` surface inside the
record would be a design decision the brief never made — I won't guess
it into the wire format. Two resolution paths, both yours:

1. **Amend the checkpoint's fixture builder** to annotate the record's
   actual claim-bearing rows (`validation.claims` values — bare string
   or the annotated `{"value": ..., "claim_basis": ...}` form — and/or
   `claim_verdict` rows), picking a base record that has a validation
   block. This retry should then go green end to end.
2. **Ratify a different record shape** — if the sitting's intent was
   that the record itself gains claim-bearing rows under a
   `validation_will_run` name, say so and I'll land it as a follow-on;
   it touches the promotion path in `build_telemetry_attempt`, so it's
   a small but real design change, not a fixture tweak.

The first response's open interpretation question (where `claim_basis`
lives, and the manifest-side carrier proposal) stands unchanged — this
finding is that same transport gap surfacing mechanically, which is
oddly satisfying: the measurement gap the field closes was itself
first measured by the checkpoint built to assert it.

## Claim basis, disclosed

As before, every `pass` in `claims` is **observed**: fixture set,
corpus sweep, parity, version, and the full suite all ran green against
the corrected tree in this session's container before packing.
