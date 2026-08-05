# notes.md — 2026-08-05-board-6-stats-read-side-001

## The sanctioned constraints, honored

- **VERSION is 0.3.29, tagged "board 6 session D."** New surfaces are
  tagged `v0.3.29, board 6 session D` in comments, docstrings, and
  BALE.md, continuing C's cadence.
- **Both session-C riders landed, per their proposal text.** BALE.md
  §11 gains row 29 for session A's apply-side dangling refusal (one
  appended row; rows 1–28 untouched), and
  `tests/test_checkpoint_provenance.py` gains the retry-path E2E for
  `--accept-checkpoint-change`, built on test_hold_retry_e2e's
  HOLD-then-retry scaffolding as the proposal's scope hint named.
- **Wire names stayed home.** This session fixed the names the brief
  deliberately left open, in the one place that owns them
  (`format_stats_json`'s docstring): per class row
  `checkpointed_attempts`, `checkpoint_hold_attempts`,
  `checkpoint_hold_rate`, `required_check_refused_attempts`,
  `required_check_override_attempts`; corpus-level, the `coverage`
  object's third row keys on `checkpoint`.

## Decisions to ratify

- **The required-check surfaces are counts, not rates.** The brief's
  D4.2 wording is "required-check refusal count and override count
  beside the drift rows," and the drift precedent already treats
  override incidence as a count. I read that literally: two counts, no
  rate. If board 10 wants a refusal rate, it is a one-line additive
  follow-up under the key contract.
- **The checkpoint-HOLD numerator keys on the stamp's own `state`.**
  A checkpoint exit 2 (the planner's artifact erroring) therefore
  counts as a checkpoint-HOLD in the stats, exactly as it holds the
  attempt; the exit-2 distinction stays visible in the walkthrough,
  log, and telemetry stamp, but v1 does not give it its own stats
  bucket. Proposed below rather than invented here.
- **The retry rider pins the §8.9 wrapper's real behavior.** My first
  draft asserted the refused retry records *no* attempt; observed
  behavior is that cmd_retry's rejected-path telemetry wrapper (same
  as cmd_apply's) records a `rejected` attempt — command `retry`,
  `validation: null`, and, by the always-stamp rule's other half, no
  `checkpoint` key. The landed test asserts that documented shape.
  Note the apply-side divergence test never asserted telemetry either
  way, so this is a new pin, not a behavior change.
- **Coverage line wording: "earlier" dropped.** The human renderer
  said "(N earlier records lack it)", but `records_lacking` counts
  records lacking the key *anywhere*, date-independent — and the new
  corpus makes the imprecision visible (the required-check-refused
  record postdates the first checkpoint carrier and lacks the key by
  design, not by age). The line now reads "(N records lack it)". The
  human rows are D's declared surface; no test pinned the old phrase.
- **Fixture dating and classing.** The nine new records are dated
  2026-06-21..29 — inside the corpus, before the 2026-07-01 record —
  so the `--since` filter test's membership stays one session, and
  all are work-class `code`, so the doc/mixed/unclassed rows stay
  numerically untouched and doc doubles as the pre-epoch contrast
  (zero counts, `checkpoint_hold_rate` null on the zero denominator).
  Pre-epoch key absence (the tenth D7 shape) is the original eighteen
  records, which the coverage row counts as lacking.

## Look closely on review

- `tests/test_stats_aggregation.py`, the full-corpus expectations:
  every number was hand-derived from the fixture set before running,
  then observed to match on the first run — but the arithmetic is the
  review surface (27 records, 25 classed, code at 18 sessions / 22
  checks / 6 checkpointed / 3 checkpoint-HOLDs, clarification epoch
  8, closure mix applied 16, pressure none 21).
- `bin/bale_stats.py`, `_class_row`: the checkpoint counting sits
  inside the validated-attempt branch, so a non-validated attempt can
  never enter the denominator even if a stray record carried the key
  there; the required-check refusal count joins the existing outcome
  ladder as an `elif`. The pre-session-D paths are byte-identical by
  construction (new counters only).
- The new fixtures were validated against
  `telemetry-record.schema.json` with jsonschema in my sandbox; the
  suite additionally exercises them through the real loader.

## Environment notes

- Full baseline ran green before any edit: 203 tests (the pack's
  execution-context set was complete, as in C — nothing baseline-red,
  no predicted claims). Final tree: 204 green (the retry rider is the
  one new test; the stats suite extended in place). validation.sh was
  rehearsed end to end against a staged copy — overlay, apply.sh,
  the full script — exit 0, every claim `[agree]`.
- `bale.toml` is absent from the shipped tree, as in A–C — harmless
  again; the smoke and test fixtures write their own.
- This session paused once at a tool-use limit and resumed via
  Continue with full context intact — a §11.1 pause, not a
  compaction; no recovery path was needed and none was taken.

## Proposals

- **Split the checkpoint exit-2 count when grant evaluation wants
  it.** What: an additive `checkpoint_errored_attempts` count (stamp
  `exit_code == 2`) beside the HOLD count. Why: v1 folds "the
  planner's artifact broke" into checkpoint-HOLD, which is right for
  the misunderstanding rate but hides oracle fragility from the
  ledger; the stamp already preserves `exit_code`, so the read side
  can split later with no write-side change. Scope hints:
  `bin/bale_stats.py` `_class_row`, the `format_stats_json`
  docstring, one fixture assertion; additive under the key contract,
  only if board 10's harness asks the question.
