# notes.md — 2026-08-13-board-10-escalation-schemas-002

The three surfaces landed as pinned; suite green at 405 (376 + 29 new).
Per your caution I verified the wire shapes against shipped bytes
before building: the annotated claims form in the brief matches what
`telemetry-record.schema.json` and `test_telemetry_extensions.py`
already carry (`{"value": ..., "claim_basis": ...}`), so unlike S5
there was no brief-vs-tree naming disagreement to flag.

## Out-of-forecast paths (each needs admitting at apply)

Four `changes[]` paths sit outside the forecast (`schemas`, `bin`,
`tests`, `docs/TARBALL.md`, `BALE.md`). All four are mechanical
consequences of the in-forecast work, not new scope:

- **`tools/response_lint.py`** — the lint embeds a verbatim copy of
  `response-manifest.schema.json`; `test_schema_embeds.py` and
  `validate.sh` both pin JSON-equality, so editing the schema without
  refreshing the embed fails the suite by name. The refresh is
  byte-verbatim (the guard's own comparison passes).
- **`tools/craft_response.py`** — the crafted §7.3 reconciliation
  epilogue did `claim == verdict` on raw claims values; an annotated
  object would print as a dict and false-`[DISAGREE]`. The fix
  unwraps to `claim["value"]` before comparing, keeping the printed
  line byte-shaped as before so `parse_claim_verdict_block` in
  `bale_report.py` needed no change at all.
- **`scripts/build.sh`** — its tree-coverage pre-flight fails the
  release build for any file under `schemas/` missing from
  `RELEASE_FILES`; the new schema had to be listed.
- **`install.sh`** — `test_release_packaging.py` pins
  `INSTALL_LAYOUT` set-equal to `RELEASE_FILES`, so the two lists
  move together.

## Decisions worth ratifying

- **The walk refactor shape.** The brief said "reuse or extend the
  `_walk_closed_vocabularies` pattern." I generalized it to a
  table-driven walk (key → checker) rather than adding a third
  hardcoded key: the telemetry record passes its
  claim_basis/closure_reason table, the escalation surfaces pass a
  priority table. Rationale in the docstring: the walk is the shared
  pattern, the vocabulary table is the per-record-family part, and a
  telemetry record should not be policed for a `priority` key that
  means nothing in its family (nor an escalation record for
  `closure_reason`). Public entry-point behavior is unchanged.
- **The bare-string claim enum moved from schema to Python.** Bale's
  stdlib schema-validator subset has no `oneOf`, so once a claims
  value is "string or object" the string enum can't stay in the
  schema. It now lives in `validate_response_manifest` beside the
  other cross-field invariants, one home (`CLAIM_VALUES`), with the
  schema still pinning the object form's shape (`value` enum,
  `claim_basis` enum, no unknown keys, `value` required). One of the
  two new e2e tests drives the moved check through the installed
  apply path to prove nothing regressed.
- **`claim_basis` stays optional on the object form**, mirroring the
  record side exactly ("S5's record-side enforcement already accepts
  exactly that shape") — `{"value": "pass"}` is legal. Requiring the
  basis would have been stricter than the shape S5 ratified.
- **Escalation-record craft fields.** Beyond the pinned six I added
  optional `record_version`, `escalation_id`, `session_id`,
  `created_at`, `updated_at`, `status` (`open`|`answered`|`withdrawn`),
  and `answer`, following the telemetry record's conventions. Only
  the six core fields are required — the pinned minimal record
  validates — and the envelope is `additionalProperties: true` so
  the harness era can extend without a schema session. I kept
  `recommendation`-must-be-one-of-`options` as documented convention,
  not contract: the S5 HOLD history's lesson cuts against inventing
  strictness the pins don't name.
- **`validate_clarification_questions` derives its sub-schema** from
  `response-manifest.schema.json`'s own `questions.items` rather than
  duplicating it — one home, so a row valid here is valid inside a
  full clarification manifest by construction.

## One-apply-behind note

This response's own manifest uses bare-string claims only: the
installed 0.4.6 validates it, and the annotated carrier it ships is
for manifests that come after. (I did observe the suite pass before
shipping — the basis I could not declare in this manifest is exactly
the field the next session's worker can.)

## Review pointers

- `bin/bale_validate.py` — the walk refactor and the two entry
  points are the judgment-bearing diff; everything else is additive
  plumbing.
- The priority double-report at schema-named spots (schema enum plus
  walk, two error strings for one bad value) matches the existing S5
  claim_basis behavior at named spots; I left it consistent rather
  than deduplicating in one family only.

## Proposals

- **Extend `validate.sh`'s schema presence loop.** It checks three of
  the five schemas (`request-manifest`, `response-manifest`,
  `diagnostics`); `telemetry-record` was left out at S5 and
  `escalation-record` follows that precedent this session. A one-line
  session could make the loop derive from the shipped set (or list
  all five) so install validation covers every schema bale ships.
  Scope hint: `validate.sh` only.
- **S6 producer alignment.** When the harness-era escalation producer
  lands (out of scope here), the `subsumes` entry notation (bare sid
  vs sid#index) should be fixed at that point; the schema deliberately
  pins only "non-empty string" today so the producer's choice isn't
  pre-empted.
