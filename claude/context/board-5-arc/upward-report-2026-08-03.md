# Board 5 arc — upward report (2026-08-03, from the board-5 design/orchestration session)

Session `2026-08-01-board-5-ledger-design-004` (read-only), reporting
on the split it handled. Board 5 is complete and closeable on the
record. Version moved 0.3.22 → 0.3.27 across the arc. Everything
below is either landed, ratified at this level, on watch with a named
re-trigger, or escalated to you.

## What landed (six sessions, all applied, none reverted)

1. `2026-08-01-board-5-telemetry-promotion-005` — write paths:
   bailout diagnostics embedded verbatim in telemetry; clarification
   summary stamped at every closing outcome; `superseded_by` lineage
   stamped by pack; rollback guard now disregards untracked telemetry
   (unblocks rollback/--undo without interleaved commits); §8.9
   sentence folded in; the deferred HOLD multi-attempt E2E landed.
2. `2026-08-01-board-5-bale-stats-006` — `bale stats` itself:
   `bin/bale_stats.py` (eighth sibling), per-work-class rates over
   the telemetry corpus, `--work-class` / `--since` / `--json`,
   dual-stream cross-checks, honest-buckets throughout.
3. `2026-08-01-stats-packaging-closeout-007` — release/install lists
   for the new sibling, the version-tag drift guard in build.sh, the
   bale-internals eighth-sibling recording. Also caught and fixed a
   real SIGPIPE flake in three pre-existing pre-flight checks.
4. `2026-08-03-stats-residual-bucket-002` — the n/a agreement bucket
   named in json and human output (three checks were in denominators
   under an unnamed value); validate.sh rows for the new sibling.
5. `2026-08-03-preserved-at-and-retag-003` — clarification records
   carry `preserved_at` (mtime becomes fallback); the v0.3.25 tag
   collision repaired (one-tag-one-session restored).
6. This session's brief (rev A ratified, rev B incorporating 005's
   landed behavior) shipped verbatim into 005 and 006 via
   --readme-file.

## The ledger is operational and already signaling

First live run (61 records, 54 classed): doc work is the first
autonomy-grant candidate (60/60 agreement, zero holds/drift/bailouts
across 13 sessions); code close behind (98%); contract-doc is where
the noise concentrates (91% agreement, 20% hold rate) — consistent
with misunderstanding-as-dominant-failure-class. Board 10 has its
consumer surface (`stats --json`, additive key contract owned by
`format_stats_json`'s docstring) and its grant-order signal.

## Ratified at this level (contest any; one is precedent-setting)

Banner-order alignment for bailout; lineage stamp as a same-invocation
second write; clarification stamping keyed on closing outcome, not
command; VERSION skip to 0.3.24 (no backfill); closure-mix membership
reading (mix sums to rate-membership sessions); filter reach (epoch/
coverage stay whole-corpus); stats diagnostics stderr-direct;
out-of-vocabulary agreement values warn-and-count-in-checks-only;
sidecar key over wrapper for preserved_at; presence-only validate.sh
row (bin siblings are 644 imports).

**Precedent-setting, flagged for your attention:** a validation claim
of `pass` grounded in prediction rather than observation was ratified
in session 003 — acceptable because the grounds were structural, the
basis fully disclosed in notes, and the claim is mechanically graded
at apply (a wrong prediction now lands as a `disagree` in the ledger
at cost to the class's agreement rate). Predicted-pass-with-disclosed-
grounds: fine. Predicted-pass-presented-as-observed: not. If you read
the line differently, say so before it hardens.

## Escalated to you (the sitting's two ratifications)

1. **Close board 5 on the record.**
2. **The version-ladder §13 delta.** BALE.md §13 still says "v0.3 is
   not yet cut" at constant 0.3.27 — counter and phase model have
   decoupled. Proposed: re-couple. 0.4.0 = close the --verbose thread
   (pack, revert, §7.4 pass-through) + a read-only audit diffing
   §13's v0.4 selftest checklist against the actual suite (rollback
   conflict/merge-commit cases were explicitly deferred to v0.4 and
   never picked up), then cut. 1.0.0 = defined for the first time:
   contracts become promises (wire format, record_version, --json
   keys go breaking-change-costs-major), gated on boards 6 and 10
   landing and the first work class earning and exercising a real
   autonomy grant. Explicitly not gated on: the API-harness transport
   (separate component per §1) or lifting the solo-project
   assumption (documented scope).

## On watch (named re-triggers, no work)

- Emitter-parser reconciliation drift: all three unparsed-
  reconciliation records are 2026-07-31 consolidation-day straddlers;
  everything post-consolidation parses. Re-trigger: any non-zero
  unparsed share in `stats --since 2026-08-01`.
- Drift-guard tag-reuse blindness (fires on tag-ahead, not reuse);
  bit once (002/007 collision, repaired). Re-trigger: third
  occurrence earns the guard a per-session-bump check.
- Mixed `at` provenance in clarification records (pre-0.3.27 read
  via mtime). Re-trigger: a stats consumer comparing per-record `at`.
- Closure-mix membership revisit. Re-trigger: real unlock-closure
  stamp accrual.

## Process findings against my own orchestration (two, same class)

Two `includes_missing` entries in worker feedback trace to my pack
authoring, not worker judgment: (1) the execution-context manifest
set omitted from the closeout pack (worker synthesized a partial
tree; prediction held); (2) a queued proposal transcribed into a
constraint instead of shipped verbatim — the paraphrase flattened a
conditional and the worker had to reconstruct the original intent
from first principles (it did, correctly). Corrective pattern adopted
and exercised in the final two packs: constraints citing prior
proposals ship the proposal's notes.md text verbatim; the full
execution-context set rides any session whose validation runs the
suite. Recommend this ride the orchestration-doctrine evidence pile.

## Corrections to standing text discovered in passing

- Rev A of the board 5 brief mis-derived the closure_reason
  first-carrier example (`continue-plan-005`; actual:
  `split-supersession-002`, 30 prior lacking). The worker correctly
  implemented rule over example; recorded in 006's notes. No brief
  revision — its job is done.
- §13's "v0.3 is not yet cut" is stale against a 0.3.27 constant;
  subsumed by the ladder ratification above.

## Residual close-out

This design session closes read-only
(`bale unlock 2026-08-01-board-5-ledger-design-004 --read-only`)
as the arc's final registry action. After it: nothing open, nothing
queued, four watches armed, two ratifications on your desk.

[End of verbatim report. Master's note: the close-out command above
was corrected in the sitting chat — unlock has no --read-only flag at
the 0.3.22 surface; the bare form relies on the closed-read-only
inference from the [] scope.]
