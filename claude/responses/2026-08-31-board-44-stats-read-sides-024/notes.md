# notes.md — 2026-08-31-board-44-stats-read-sides-024

The four read sides landed in one session — the honest pre-flight said
they fit, and they did, mostly because the reading was front-loaded
and every surface turned out to be additive projection over data the
records already carry. Three things below need your judgment; the rest
is color.

## Out-of-forecast path — admit at apply

- **`tests/test_stats_drilldown.py`** (created). The forecast names
  `tests/test_stats_aggregation.py` and the fixtures directory, but
  the right home for this coverage is a separate suite over its own
  synthetic corpora — the pattern `test_stats_linkage.py` names as
  ratified, and the only shape that leaves the shared corpus (and
  therefore the riders, below) untouched. Tests ship with code; a new
  suite file was the goal's requirement, so it ships and surfaces here
  for per-path admission.

That is the only drift. Everything else lands inside the forecast.

## Two assumptions I proceeded on (the recoverable-risk posture)

1. **The "empty-claims-with-nonempty-validation_will_run" cut ships in
   its computable form.** The telemetry record does not persist
   `validation_will_run` — I checked `build_telemetry_attempt` (it
   promotes claims, change_paths, feedback only) and every fixture.
   So the literal count is not computable from the corpus, which
   collides with the row's own "no-new-fields" premise. What ships:
   `empty_claims_validated_attempts` — validated attempts whose
   promoted claims map is empty. Validation *ran* on every such
   attempt, so this is the §5.3 wasted-signal shape the cut hunts;
   the one divergence from the literal wording is that a session whose
   declared checks were all mechanical (the TARBALL.md §6 typo-session
   shape, where empty claims are *correct*) counts too. That residual
   is small, constant-ish, and washes out of exactly the aggregate
   trends the row says the ledger reads — but if you want the literal
   cut, the write side must land first (Proposals). The docstrings and
   BALE.md both state the divergence rather than papering over it.
2. **The dossier's corrects lineage reads tolerantly and is null
   today.** `corrects` is likewise never promoted into the record. The
   dossier reads it at both depths wherever a record carries it (so it
   lights up the day the write side lands, and hand-carried values
   already resolve — tested), scans the corpus for the converse
   `corrected_by` edge the same way, and renders "none recorded"
   honestly otherwise. The `superseded_by` lineage is real today, both
   directions. The HOLD→retry arc itself never needed corrects — it
   reads end to end from one record's attempts[].

If either assumption misses your intent, the clean recourse is the
write-side proposal below plus a one-line read change; nothing here
forecloses the literal forms.

## Where to look on review

- **The checkpoint "catch" definition** (`_class_row` docstring, the
  `CheckpointCatchTest` shapes): catch = stamp state HOLD ∧ stamp exit
  1 ∧ worker's own `validation.exit_code` 0. I read "catch" as *the
  blind oracle saw what the worker's own script missed* — so both-HOLD
  is not a catch (the worker also saw it) and an errored checkpoint
  (exit 2) is a tooling fact, outside catches but still inside the
  HOLD count. The fixture corpus computes catch 1/6 for code (the
  checkpoint-alone HOLD), which matched my hand-derivation.
- **Membership bucket choice.** The anomaly buckets that got sid sets:
  held, disagreeing checks, unparsed, drift refusals, rejected,
  required-check refusals, checkpoint HOLDs and catches, forecast
  drift, bailouts, empty-claims (per class); in-flight, read-only,
  crash-debris, the clarification cross-check disagreement sets, the
  forecast-departure smells, bailed-with-pressure-none (corpus level).
  Applied closures and agreeing checks deliberately carry none —
  nominate, never curate. Easy to widen if a count you drill on is
  missing its set.
- **Human-mode ordering.** Every new line renders *after* the
  pre-existing ones (extras append after linkage; membership, packer,
  and doc-epoch lines sit between the cross-checks and the summary),
  which is what keeps the existing suites' exact-substring assertions
  green — I treated that ordering as part of the human surface.
- **Doc-epoch key.** A 12-hex sha256 digest over the sorted name=hash
  lines, with the full map reported beside it so the digest is an
  identifier, not the only record. The shared corpus has no
  `contract_docs` in its echoes, so it reads as one `unstamped` epoch
  — the A/B read begins accruing with real post-echo records.

## Compaction disclosure (CLAUDE.md §11.6)

A runtime compaction landed mid-session, after the module edits were
substantially in place. Per §11.6 this is disclosed rather than worked
through silently, and the recovery ritual ran before this tarball was
sealed: the request `manifest.json` was re-read from disk (goal,
out_of_scope, and the resolved write forecast all match what was
built), the brief's pinned epoch sentence was re-compared
byte-for-byte between `README.md` and the shipped `BALE.md` (identical),
and the §10.1 step 10 set was re-derived against the real `files/` —
the crafter recomputed every hash from present bytes after the last
file edit, and the lint's changes-mirror and claims-subset checks
re-verified them (CLEAN). No hash, claim, or expectation in this
response is carried from pre-compaction memory; everything was
re-read or re-run from the durable artifacts this turn.

## Verification honesty

Everything unit-level ran here: the new suite's 20 unit cases, the
linkage suite's unit half, and a direct additivity diff — every
pre-existing key of `compute_stats` over the shipped fixture corpus is
byte-identical between the shipped module and this one. What did NOT
run here: anything needing `bin/bale` (my environment has only the
shipped context) — the new suite's two E2E cases and the two existing
E2E suites. Their claims are `pass` with `claim_basis: "predicted"`,
grounded in the additivity diff and the substring-by-substring check
of every human-mode assertion those suites make; `validation.sh` runs
all of them in staging, so the verdicts will say.

## Proposals

### Promote `validation_will_run` and `corrects` into the telemetry attempt

**What:** two one-line additions in `build_telemetry_attempt`
(bin/bale_report.py): carry `manifest.validation_will_run` inside the
attempt's `validation` object, and `manifest.corrects` on the attempt,
both with the established key-presence semantics.
**Why:** this session's read sides had to ship computable proxies for
two of the row's asks (assumptions above) because neither field
reaches the record. Both promotions are additive under the schema's
`additionalProperties: true` — but they are new fields in spirit, and
this session's brief cut new fields out of scope, so they are proposed
rather than made. Once landed, the literal empty-claims cut is a
two-line read change and the dossier's corrects lineage goes live with
zero read-side changes (the tolerant read already resolves the field).
**Scope hints:** bin/bale_report.py (build_telemetry_attempt),
telemetry-record.schema.json descriptions if you want the fields
documented; independent of everything else here.

### Wire the session dossier into `bale stats --sid`

**What:** `bale stats --sid SID` swaps the aggregate report for the
dossier — call `compute_session_dossier`, render via
`format_session_dossier_report` / `format_session_dossier_json` under
the existing `--json` stream discipline, fail() on an unusable
telemetry dir; the not-found case renders the honest miss (already
built and tested). Then promote the new suite's dossier coverage to
E2E.
**Why:** the compute and render halves are done and unit-covered; only
the wiring is missing, and it lives in bin/bale — out of scope here
and inside an open sibling's forecast, so it could not land in this
response even as admitted drift.
**Scope hints:** bin/bale (the stats subcommand's argparse and
dispatch), tests/test_stats_drilldown.py (E2E extension); only after
the sibling session holding bin/bale closes.

### The queued riders remain queued

**What:** the brief's riders — the post-epoch fixture additions and
board 65's linkage-shape fixture extension — did not fire.
**Why:** this session never touches `test_stats_aggregation.py`'s
expectations (the separate-suite path above), which is the brief's own
stated condition for leaving them queued; and the fold-in registry
carrying their verbatim texts was not in this request's context, so a
firing here would have needed a clarification round anyway. The next
session that must perturb the whole-corpus expectations should carry
the registry.
**Scope hints:** tests/fixtures/stats_corpus,
tests/test_stats_aggregation.py; needs the fold-in registry shipped.
