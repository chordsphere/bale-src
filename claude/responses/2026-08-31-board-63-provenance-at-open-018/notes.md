# notes — response-018 (board 63: provenance at open)

## Out-of-forecast paths (TARBALL.md §5.4 — admit per path at apply)

The forecast was `bin/bale_pack.py` + `schemas/telemetry-record.schema.json`.
Two test paths ship outside it; both are the tests-ship-with-code hard
rule doing its job, and both are disjoint from board 58's and board 60's
forecasts (board 60 claims `tests/test_relay_verb.py` specifically —
neither of these):

- **`tests/test_provenance_at_open.py` (created).** The new behavior
  needed its own pinned contract: open-time record shape, verbatim
  stamp, registry provenance.json, append-on-close with created_at
  preserved, schema agreement via validate_telemetry_record, and stats
  in-flight tolerance. The pack could not have named it (ADR-0014).
- **`tests/test_closure_telemetry.py` (modified).** Three of its tests
  pinned `attempts[0]` as the unlock event and `len(attempts) == 1`
  after pack-then-unlock. With the opened attempt landing first, those
  assertions are now wrong about the intended behavior, not just
  failing — leaving them would make the suite reject the feature. They
  re-index to `attempts[-1]`, and pinned-behavior 1 now also asserts
  the append shape (len 2, opened stamp intact). Shipping the two test
  files in `context/` reads, in hindsight, like the packer anticipated
  this.

## What the probe established (TARBALL.md §4.5)

The response leans on these facts from the paste-back probe (bale-src
checkout, branch main, Python 3.12.3):

- `write_telemetry_record` (bale_report.py:2770) loads an existing
  parseable record, **appends** the attempt, updates only
  `outcome`/`updated_at`, preserves `created_at` and unknown keys, and
  moves a corrupt file aside rather than clobbering. Contract 3 holds
  with no change outside my forecast.
- `close_session_with_record` (bale, :966) and every close path route
  through that writer; `stamp_superseded_by` targets by
  `closure_reason == "superseded-by-split"`, which opened attempts
  omit, so lineage stamping is unaffected.
- `validate_telemetry_record` (bale_validate.py:469) is driven by the
  schema **file** plus a closed-vocab walk over `claim_basis` and
  `closure_reason` only — so the shipped schema edit *is* the
  validation change, and neither strict vocabulary is touched.
- The session dir is read per-file and wiped by rmtree; nothing
  enumerates it strictly, so `provenance.json` beside `scope.json` is
  safe. The only record-existence inference
  (`_resolve_supersession`) runs on not-open sids only.

## Decisions to ratify

- **The stamp rides the opened attempt, not the envelope.** Envelope
  extras would also survive appends (the writer preserves unknown
  keys), but attempt placement keeps the open event flowing through
  `build_telemetry_attempt` — so the epoch stamps (`scope_kind`,
  `sandbox_escaped`, `network_grant_exercised`, `cost`) stay uniform
  with every other event and no envelope-assembly logic is duplicated
  in pack. Readers resolve the pair the same way `session_work_class`
  already scans attempts for feedback.
- **The write lives in `persist_pack_session`.** Both request-building
  call sites go through it, so handoff-opened sessions get the stamp
  with zero bin/bale changes. Cost: the stamp lands before
  `register_session`, so a crash between the two can leave an `opened`
  record for a sid that never opened — documented in the docstring;
  same half-state family the crash-debris machinery already tolerates,
  and the record honestly reads as in-flight.
- **Handoff opens stamp command `pack` for now.** persist_pack_session
  takes `command` (default `"pack"`); `"handoff"` is reserved in the
  schema enum, but the one-word cmd_handoff change is in bin/bale —
  out_of_scope, so proposed below rather than made. A bounded, flagged
  inaccuracy until ratified.
- **Registry file carries exactly the two fields.** The ask was the
  pair; the full provenance block (contract_docs, checkpoint stamp)
  survives in the request tarball and, for responding sessions, the
  feedback echo. Widening the registry stamp is cheap later if wanted.
- **Rider deferred: normalize-at-stamp for packer/model_identity.**
  One sentence, per the brief: normalizing ~10 packer and ~62
  model_identity spellings without the corpus in hand and a ratified
  canonical map risks silent mis-attribution, and the verbatim stamp
  loses nothing — normalization can land later at read time or as its
  own stamp-time session with the map agreed.

## Assumption proceeded on (flagged)

`build_telemetry_attempt`'s body was truncated in the probe at the
docstring boundary; I proceeded on its documented "records what it is
handed" posture — i.e. it does not reject the new `opened` outcome
string. Everything visible supports this (the vocabulary enforcement
points are the schema and the closure/claim-basis walk; the extensions
suite calls the builder with arbitrary-looking kwargs), and the new
suite exercises it E2E in staging on the first check, so if the
assumption is wrong, validation fails loudly on test 1 rather than
anything landing.

## Stats-side noise, known and accepted

Until a read side lands, every `bale stats` run warns once per open
session ("unrecognized envelope outcome 'opened'; counting the session
as in-flight") — the reader's own designed unknown-vocabulary path,
counting correctly. The new suite pins that the count is right. The
warn removal is one frozenset entry, proposed below rather than shipped:
the manifest names read-side aggregation beyond optional-field
tolerance out of scope, and vocabulary membership is a judgment call I
kept on the review-only side of that line.

## Proposals

- **What:** cmd_handoff passes `command="handoff"` to
  `persist_pack_session`.
  **Why:** the record's honest-command posture; the enum value and the
  parameter are already in place, so this is a one-word bin/bale
  change. **Scope hints:** bin/bale (cmd_handoff's
  persist_pack_session call); only after this session lands.
- **What:** add `"opened"` to `IN_FLIGHT_OUTCOMES` in
  bin/bale_stats.py, and have `session_work_class` (or its board-44
  successor) resolve from the opened attempt's provenance stamp before
  falling back to the feedback echo.
  **Why:** removes the per-open-session stats warning and actually
  closes the read half of the blind spot — the data now exists for the
  49 unlocked-session records' successors; the write side alone only
  makes it reachable. **Scope hints:** bin/bale_stats.py; fits
  board 44's drill-down read sides; only after this session lands.
- **What:** consider widening `.bale/sessions/<sid>/provenance.json`
  (or the opened attempt) to the full provenance block.
  **Why:** the manifest copy dies at close, so contract-doc hashes and
  the checkpoint stamp vanish for never-responding sessions the same
  way work_class did; low cost while the seam is open. Not done now —
  the ask was the pair, and block-width is the planner's call.
