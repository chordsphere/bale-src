# notes — 2026-08-31-board-65-linkage-rollup-010

## Out-of-forecast paths (per-path admission at apply)

Two of the three changes land outside the stamped write forecast
(`bin/bale_stats.py`, `tests/test_stats_aggregation.py`). Both are
work the goal genuinely required; enumerated here per TARBALL.md §5.4,
mirrored machine-readably in `feedback.self_reported.forecast_departures`.

- **`bin/bale_report.py` (modified).** Outcome contract 1 requires the
  `linkage` label in stats output, and the brief pins "extend
  whichever output modes stats already ships — both." The `--json`
  mode picks the new per-class key up for free (`format_stats_json`
  splats the whole payload), but the human report renders explicit
  keys only — no renderer touch, no linkage label in default output.
  The touch is deliberately thin: one extras entry per stamped class,
  projecting the computed dicts, plus the `format_stats_json`
  docstring addition the one-home rule forces (that docstring owns the
  wire key contract; adding a key without recording it there would
  violate the contract doc's own rule). No numbers are computed in the
  renderer. Note this is *not* a doc edit in the brief's lane sense —
  the BALE.md stats line still rides the desk's close rider, and
  nothing in the sibling's forecast (`BALE.md bin/bale_pack.py
  bin/bale_config.py validate.sh scripts/build.sh install.sh`) is
  touched.
- **`tests/test_stats_linkage.py` (created).** The separate-suite path
  the brief names as equally legitimate (precedent:
  `test_forecast_ledger.py`). The forecast's second entry names
  `tests/test_stats_aggregation.py` specifically, not a directory, so
  a new suite is drift by construction. Why this path: the shared
  suite whole-dict-asserts `corpus`, `closure_mix`, and the
  cross-checks, so the rider's fixture additions would perturb nearly
  every expectation there — exactly the invasiveness the registry
  entry itself records. The new suite's synthetic corpus covers the
  semantics precisely and cheaply instead.

## Rider status

**The queued fold-in does not fire.** I did not touch
`tests/test_stats_aggregation.py` (verified: its bytes ship nowhere in
this response), so per the brief the registry entry stays queued. For
what it's worth to the desk: the new keys are additive, and the full
suite — that file's whole-dict assertions included — is green over the
changed tree, so the rollup itself adds no pressure to fold early.

## Judgment calls to ratify

- **The legacy `surfaced` spelling is read beside `point`.** The
  current response-manifest schema spells the placement key `point`;
  the two linkage-bearing records in the shared fixture corpus spell
  it `surfaced`, and telemetry persists feedback verbatim, so both
  spellings exist in real corpora. Without the fallback the placement
  dimension would report real recorded placements as "unspecified" —
  dishonest given the data is present under the old key. `point` wins
  when both appear. The normalization is key-level only; values pass
  through verbatim. If you'd rather the rollup report the legacy
  spelling as its own bucket (strict-schema posture), the change is
  one helper (`_linkage_point`) and two test expectations.
- **Every attempt is scanned, not just response attempts.** Mirrors
  the existing clarification cross-check's read
  (`_self_reported_clarification`, now sharing the same
  `_attempt_linkage` home). Realistically stamps only ride
  apply/retry attempts; the scan-all posture just reports whatever a
  record carries, wherever it carries it.
- **"unspecified" is the honest bucket name** for a stamp omitting
  kind or placement, following the `closure_reason` "unspecified"
  precedent. Unexpected kind *values* form their own verbatim row
  (the module's honest-row doctrine), so vocabulary growth needs no
  code change.
- **Per-class surface only.** The rollup is a `linkage` sub-dict on
  each class row; the per-work-class split is the classes keying
  itself (the brief's "if it falls out naturally" — it does). No
  corpus-wide total block shipped — see `deferred` in the manifest.
- **The human line renders only for stamped classes** — no fabricated
  zeros, matching every other extras entry (the forecast rows'
  precedent).

## Validation runtime

The full-suite check runs ~2 minutes (688 pre-existing + 9 new tests;
the harness's slow gate stays closed). It is not gated behind `--slow`
because outcome contract 2 makes full-suite green a required outcome,
not an optional deep check. Everything else is sub-second.

## Proposals

- **What:** When the queued fixture fold-in fires (the next session
  that must touch `test_stats_aggregation.py`'s expectations anyway),
  extend its fixture set with linkage shapes the shared corpus
  currently lacks: a probe-kind stamp, and a `point`-keyed stamp
  beside the existing two `surfaced`-keyed ones.
  **Why:** The shared corpus today carries only clarification-kind,
  legacy-spelled stamps; folding both spellings and both kinds in
  keeps the one-corpus doctrine's coverage honest for the rollup this
  session added, at near-zero marginal cost once that file's
  expectations are being recomputed anyway.
  **Scope hints:** `tests/fixtures/stats_corpus/`,
  `tests/test_stats_aggregation.py`; rides the already-queued entry,
  no source changes.
