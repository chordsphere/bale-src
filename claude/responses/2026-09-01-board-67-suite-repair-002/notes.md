# notes.md — 2026-09-01-board-67-suite-repair-002

Green under both gate positions, unconfined and in the confined
grading topology. Everything below is the per-file disposition the
brief asked for, plus one constraint-2 finding that shipped as an
out-of-forecast source fix, and the provenance record for the
exchange round.

## What the exchange round established (TARBALL.md §4.5 provenance)

Round 2's answer (verified against its sha256 trailer) established:
the confined delta is exactly the 11 test_sandbox_wrapper ids (10
PrologueUnitTest, 1 ConfinementBehavioralTest), identical under both
gates; the grading log carries ids and summary only, so no per-id
tracebacks exist to relay; and — binding alongside constraint 3 —
every capability guard must print what it probed, what it found, and
its run/skip decision. All three shaped the work below. The round
also ratified proceeding on the unconfined 17 while it traveled, and
my reading of the brief's clarification-exchange instruction as the
pre-chosen courier despite `expects_probe: yes`.

## Per-file repair classes

Stale-assertion re-encodes against the v0.4.21 open-time record
(each states the new invariant — which attempt is which, what the
`opened` attempt carries — never a loosened count):

- `tests/test_hold_retry_e2e.py` — HOLD/retry lifecycle is
  opened+held(+applied); the opened attempt's shape (outcome,
  command pack, validation null, created_at = the open stamp) is
  asserted, not skipped past.
- `tests/test_checkpoint_provenance.py` — retry lifecycle is
  opened+held+rejected+applied; the opened attempt carries no
  checkpoint key (the always-stamp rule's other half).
- `tests/test_supersession_pack.py` — accept: two attempts, the
  superseded_by stamp enriching the closure only; declines: the
  record stays exactly open-time (one attempt, envelope 'opened',
  no lineage key anywhere).
- `tests/test_readonly_pack.py` — "no closure record" became "the
  open-time record holds only the opened attempt" (empty forecast
  asserted on it) for the declined sweeps and the sibling apply.
- `tests/test_relay_verb.py` — assert_untouched now pins "relay
  appends no telemetry attempt and mutates no envelope".
- `tests/test_required_check_gate.py` — a dry-run refusal appends
  no attempt; envelope stays 'opened'.
- `tests/test_auto_sweep.py` — fixture repair: assert the open-time
  record exists, rmtree claude/telemetry, then plant the blocker
  file; the blocked-write intent is unchanged.
- `tests/test_forecast_ledger.py` — stamp-first class resolution
  (board 44): the fixture packs declare `--work-class code`, and the
  test pins the opened attempt's stamp as what `classes.code`
  resolves from. This was the KeyError: the default 'mixed' stamp
  was outranking the feedback echo.

Capability guard:

- `tests/test_sandbox_wrapper.py` — `writable_non_tmp_base()` is now
  a cached capability probe with a printed
  `[capability-probe] writable-non-tmp-base: ...; decision: run|skip`
  line and a counted `unittest.SkipTest` when the capability is
  absent. One deliberate change of posture: the old helper's
  docstring argued fail-loud-not-skip on the premise that a confined
  run always has a writable non-/tmp staging cwd. The grading
  topology broke that premise (dry-run staging under /tmp), so the
  absence is a legitimately missing capability, not a broken
  contract — flagging this for your ratification since I reversed a
  written rationale.

## Per confinement-only id: the capability its guard probes

All 11 ids probe the same capability — **a writable directory
outside /tmp** (probed as: mkdir in HOME, else mkdir in a
non-/tmp-resident cwd; never an environment name). The 10
PrologueUnitTest ids hit it in setUp (their fixture base must
exercise build_prologue's non-/tmp branch);
`test_confinement_properties_hold` hits it in-body for its staging
fixture. I reproduced your confined enumeration id-for-id (23F+3E)
by running the suite confined with a /tmp-resident cwd: the old
helper's AssertionError surfaces as FAIL (not ERROR) even from
setUp, which is why all 11 read as failures in the grading log. The
next grading run prints the labeled capability map you asked for.

## Constraint-2 finding: retry's spurious 'opened' attempt

While re-encoding test_hold_retry_e2e I found the record after
HOLD→retry held FOUR attempts: opened, held, **opened**, applied.
`bale retry` re-persists session records via `persist_pack_session`
(a pre-v0.4.21 call site), which since v0.4.21 also appends an
`opened` telemetry attempt — so every retry injects a mid-session
'opened' event. That contradicts the telemetry schema's own enum
contract ("'opened' = ... no close or apply event has landed yet"),
transiently mirrors 'opened' onto the envelope over a real held
attempt, and double-counts opens in attempt-level aggregation. Per
constraint 2 I did not encode the broken count; per the brief's
"(constraint 2 first)" source-change path I fixed it:

- `bin/bale_pack.py` — `open_telemetry: bool = True` threaded
  through `persist_pack_session` → `_persist_open_provenance`; False
  skips the telemetry append with a logged line; registry effects
  untouched; both request-building call sites (pack, handoff) keep
  the default.
- `bin/bale` — the retry re-persist call passes
  `open_telemetry=False` with a comment stating why.

**Both paths are outside the `tests` forecast — please admit them
per path at apply.** If you'd rather leave the source untouched,
decline the two paths: the response then refuses at the drift gate
and the session stays open; the honest alternative is those two
hold_retry/checkpoint_provenance tests red, not re-encoded to the
defective counts.

## Packing signal

`includes_missing`: the repo's `tools/` tree. `tests/harness.py`
hard-requires it (`INSTALL_TREES`), and the request's `context/`
didn't ship it; I reconstructed it from the request-root injected
pair and my counts then matched yours id-for-id. Future packs of
this family should include `tools/`.

## Proposals

- **Document the retry/open telemetry rider.** What: a line in the
  telemetry schema description (or BALE.md §8.9) stating that
  retry's registry re-open appends no 'opened' attempt, naming
  `open_telemetry`. Why: the fix is currently documented only in
  code comments; the schema's description enumerates every other
  writer epoch. Scope hints: schemas/telemetry-record.schema.json,
  BALE.md; docs are out of this session's forecast, and the schema
  is explicitly out_of_scope here ("any change to the telemetry
  record shape") — this is a description-text change, but it should
  be its own reviewed session.
- **Skip-count pin for the grading environment.** What: if you want
  the guard's skip set pinned, a follow-up could assert the
  capability map's exact line in the blind checkpoint. Why: the
  oracle currently reads exit code and enumeration only; the probe
  line makes a stronger per-id oracle possible. Yours to sequence.

One loose end I could not verify from here: your confined dry-run
counted skipped=42 where my environments count 43 — one
environment-conditional skip differs somewhere outside the failing
set. It never affected the failing enumeration or the repairs, but
if the grading oracle pins skip counts, expect 42+11=53 there, not
54.
