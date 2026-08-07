# board-13 separation — implementation decomposition — revA

Companion to the design brief (same session,
`2026-08-07-board-13-read-write-design-003`). Scope hints are prose,
per the design-only constraint — no runnable commands. Briefs
authored for these sessions, when the design is ratified, follow the
placeholder convention at TARBALL.md §3.4's convention line for any
slot left to the planner.

Serialization is a claim the architect can contest; every ordering
below states its rationale so it can be contested precisely.

## Session A — pack surface, record semantics, and the pack-side gates

**The load-bearing session.** Lands: the `--write` flag family and
its arg-parse rules (requires ≥1 path; contradicts `--read-only`);
the forecast-defaults-to-includes resolution; the wizard's
where-will-changes-land follow-up with its Enter default; the
reinterpretation of `sessions/<sid>/scope.json` as the forecast (a
change to what `persist_pack_session` is handed, not to the
helpers); the `resolved_scope` stamp fed from the forecast (one
source preserved); the pack-time disjointness gate's re-base (it
already reads `scope.json`, so this is mostly the refusal text and
the doc rows); the checkpoint covering refusal keyed to the forecast
(plus the read-side ships-the-oracle check if E3 ratifies that way);
handoff's mirrored behavior for its reading-plan-derived forecast;
schema description edits on `resolved_scope`; tests for all of the
above; BALE.md §7/§11 row updates and the ADR landing per the
docs-land-with-the-ADR practice.

**Scope hint (prose):** the pack module, the main CLI file (shared
helpers, handoff path), the request-manifest schema, BALE.md, the
ADR directory, INDEX.md and STATE.md touch-ups, the test suite
directory. A directory-shaped seam over the tests is the ADR-0014
way to admit the new test files nobody pre-names.

**Predicted gate firings:** packed under the *old* model
(one-apply-behind, the ADR-0006 precedent — the session landing the
separation runs under conflated scope; expect one final dose of the
old lock breadth). Its include set will be broad (bin/, schemas/,
docs), so it is concurrency-exclusive while open: any sibling pack
fires the pack-time gate. No drift expected if the seam includes the
directories above; new test files land under the tests directory
include or arrive as enumerated drift for per-path admission.

## Session B — apply-side doctrine text, telemetry epoch, stats rows

Lands: the drift-gate refusal text updated to forecast vocabulary
(mechanics untouched — the gate already reads `scope.json`); the
`scope_kind` epoch key on telemetry attempts; the
`forecast_departures` feedback field (if E2 ratifies) and its
verbatim persistence; `bale stats` rows for forecast drift rate,
admission rate, forecast precision, and the
departures-vs-admissions cross-check; `bale status` labeling;
telemetry and response-manifest schema edits; BALE.md §8.9/§5.5/§5.6
updates.

**Scope hint (prose):** the apply module, the stats module, the
report module, the main CLI file, the two schemas, BALE.md, the test
suite directory.

**Ordering claim: B after A, serialized.** Rationale, twofold. Real
dependency: B's epoch key marks attempts whose `scope` *is* a
forecast, which is only true once A's pack lands — stamping the
epoch before the record semantics change would poison the
disambiguation it exists for. Mechanical: A and B both need the main
CLI file and BALE.md in scope, so their forecasts intersect and the
pack-time gate serializes them anyway. Contest point: the schemas
could split out of both into a doc-class session, but the
schema-edits-land-with-the-code practice argues against.

**Predicted gate firings:** first session packed under the *new*
model. If packed with a narrow forecast (apply/stats/report modules,
schemas, BALE.md) and generous read includes (the whole bin/ tree
for context), it is itself the first live demonstration of the
thesis: broad reading, narrow locking. Expect zero gate firings if
nothing else is open; expect the sibling-collision gate to protect
it if a concurrent doc session forecasts BALE.md — which is the
serialization-by-contention the model intends, now scoped to the one
genuinely shared file instead of the whole read set.

## Session C — contract-doc propagation (post-ratification)

Lands: CLAUDE.md §6's revised lane rule, TARBALL.md §3.2/§3.4's
forecast doctrine and flag table rows. Global docs, bale-src
sessions only, wording ratified at the master desk first (E1).

**Scope hint (prose):** the two global docs in the installation docs
directory, plus their test fixtures if any assert doc content.

**Ordering claim: C after A lands and E1 ratifies; C and B may run
concurrently** — their write sets are file-disjoint (C touches
global docs; B touches modules, schemas, BALE.md), which under the
new model is exactly the condition for concurrency. This pair is a
deliberate candidate for the first concurrent post-separation
sitting: cheap, real, and diagnostic. Contest point: if the desk
prefers doctrine text to land before the ledger reads it, flip B and
C — nothing mechanical objects.

## Explicitly not sessions

- **No migration session.** Old open sessions read conservatively as
  over-forecasts and self-clear (brief I.2). No registry rewrite, no
  backfill.
- **No telemetry backfill.** Pre-epoch records stay unstamped; key
  absence is the pre-epoch signal, per doctrine.
- **The read-staleness watch (brief I.6)** is data-gated: proposed
  only if post-epoch HOLDs cluster in that class. Not scheduled.
