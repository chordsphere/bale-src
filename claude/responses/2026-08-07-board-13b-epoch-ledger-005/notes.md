# notes — 2026-08-07-board-13b-epoch-ledger-005

Everything in the charge landed: the epoch key, the forecast rows and
cross-check, the apply-side vocabulary, the E2 schema field, and the
duplicate-path rider. 295 tests pass (289 baseline + 6 new). Two
one-apply-behind consequences below need your awareness at apply; one
path is enumerated drift for per-path admission.

## Out-of-forecast path (admit per path at apply)

- **`tools/response_lint.py`** — the lint embeds a verbatim copy of
  `response-manifest.schema.json`, and `tests/test_schema_embeds.py`
  asserts JSON-equality between embed and source. The ratified E2
  field (`forecast_departures`) edits the source schema, so the embed
  must move in the same response or the suite fails. The path is
  outside my forecast (BALE.md, bin/…, schemas/…, tests) and outside
  session C's (docs/CLAUDE.md, docs/TARBALL.md), so it lands as
  ADR-0014/0015 admitted drift, not a G2 collision:
  `--allow-out-of-scope tools/response_lint.py` at apply. This is the
  generalized-modified-file admission path's first live use, three
  hours after it was ratified — fitting.

## One-apply-behind (standing practice, two concrete consequences)

This session modifies apply-path code, so the apply that lands it runs
the **old** apply one final time. Two things follow:

1. **My own manifest omits `forecast_departures`.** The old installed
   schema validator rejects unknown `self_reported` keys
   (`additionalProperties: false`), so declaring my one departure in
   the structured field would bounce this very tarball. The departure
   is enumerated above in prose — which *is* the pre-epoch mechanism —
   and the field becomes usable from the next session on. I put this
   in `deferred` too so the record carries it.
2. **This session's telemetry attempt won't carry `scope_kind`.** The
   stamp is written by the new `build_telemetry_attempt`; the old one
   runs at my apply. The epoch therefore begins with the first apply
   *after* this lands — the same boundary shape session A's landing
   had, and the conservative direction (my attempt aggregates
   pre-epoch, where its admitted drift can't perturb the forecast
   rates).

## Where to look on review

- **`bin/bale_stats.py`** — the containment mirror. The module's
  importability contract (no `bin/bale` import) forces a stdlib-pure
  duplicate of `scope_path`/`scope_covers_path`. I disliked the
  second home enough to pin it with a subprocess drift guard
  (`ContainmentMirrorTest.test_mirror_agrees_with_bin_bale` runs both
  homes over one case matrix), but if you'd rather restructure —
  e.g. lift the helpers into a shared sibling — that's a layout
  decision I deliberately did not make unilaterally.
- **Rate-unit choices** (also in the feedback block's assumptions):
  admission is path-granular; precision is entry-granular, per
  attempt, excluding empty change sets. The design brief named the
  rates without fixing units; every numerator and denominator ships
  beside its rate so you can re-weight without a code change if you
  want different definitions.
- **The duplicate gate's basis** is identical path *strings* (the
  lint's DUPLICATE_PATH basis), not normalized paths. Two spellings
  of one file (`a.txt` vs `./a.txt`) would still pass this gate and
  fail later at the mirror checks. Matching the lint felt more
  valuable than being maximally aggressive; widen it later if you
  disagree.
- **A small behavior change inside the rider**: a *conflicting*
  duplicate (same path, different sha256) previously limped to the
  step-9 sha-mismatch rejection; it now refuses at the duplicate gate
  with the clearer message. Same outcome class (rejected,
  pre-staging), earlier and better-named. The old behavior pin in
  `test_apply_preflight.py` is rewritten as the row-32 test.

## Coordination with session C

`TARBALL.md §5.2.2` (the feedback block's field walk-through) should
eventually mention `forecast_departures`. TARBALL.md is C's forecast
— mechanically refused at my apply while C is open — and C's E1
charge is CLAUDE.md §6 and TARBALL.md §3.2/§3.4, which may not cover
§5.2.2. If C's wording is already frozen, this is a one-sentence
follow-up for a later doc session; the schema description carries the
full contract meanwhile.

## Proposals

### Post-epoch fixture records for the shared stats corpus

**What:** Add one or two post-epoch fixture records (carrying
`scope_kind`, a forecast, drift, an admission, and a
`forecast_departures` block) to `tests/fixtures/stats_corpus/` and
extend `test_stats_aggregation.py`'s hand-derived assertions to
cover them.

**Why:** The full-corpus test whole-dict-asserts the corpus counts,
so adding fixtures perturbs nearly every expectation in that file —
too invasive to ride along this session. My new suite seeds its own
synthetic corpus instead, which covers the semantics but leaves the
shared corpus wholly pre-epoch. Folding the shapes in when that file's
expectations are next touched anyway keeps the one-corpus doctrine
whole.

**Scope hints:** `tests/fixtures/stats_corpus/`,
`tests/test_stats_aggregation.py`; no source changes.

### Early forecast-signal shapes worth knowing before reading the first rates

**What:** Three observations about how the new rows will read in
their first weeks, queued per the README's ask; no code change
proposed yet, all three are data-gated.

**Why (grounded in what this session built and tested):**

1. *Refusal-then-admit double-counts drift.* A drift refusal followed
   by an admitted retry is two response attempts with the same drift
   set, so the drift rate counts that judgment twice. Honest under
   D2's attempt-history doctrine (the E2E pins exactly this shape:
   2/3 attempts drifting for one drifted change set), but a reader
   comparing drift rates across classes should know refusal-heavy
   workflows read higher. If it distorts, a per-session drift variant
   is derivable without schema changes.
2. *Default packs are invisible to the imprecision signal.* A
   whole-tree forecast is the single entry `.`, which any landed
   change touches — precision 1.0 by construction. The entry-granular
   definition is the ratified one and it's right for narrow
   forecasts; just don't read high precision in a class full of
   default packs as evidence of good forecasting.
3. *Per-attempt precision over-weights retried sessions* (the
   forecast is re-counted per attempt). Symmetric with the drift
   denominators, so ratios stay comparable, but absolute entry counts
   aren't session counts.

**Scope hints:** none yet — watch the rows; `bin/bale_stats.py` if
any variant is later ratified.
