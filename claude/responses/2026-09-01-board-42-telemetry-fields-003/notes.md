# notes — 2026-09-01-board-42-telemetry-fields-003

## The delegation, verified against real bytes

The brief's "one home, free propagation" anchor holds as packed and
still holds with the change applied. `validate_clarification_questions`
(bin/bale_validate.py) derives its row schema live from
`response-manifest.schema.json`'s `properties.questions` — no
duplicated shape — and `validate_exchange_record` delegates its
`questions[]` to that same function, with the exchange schema's `$ref`
pointing at the same spot for human readers. So `origin` landed in the
one home and exchange rounds inherited it with no second edit. Not
assumed: `test_exchange_record_delegation_carries_origin` in the new
suite validates an origin-tagged row inside a full exchange record and
asserts an invented origin gets byte-identical row-validator verdicts
on both surfaces. The `priority` parity behavior was reproduced first
(two verdicts for an invented value: the schema's named spot plus the
walk) and `origin` matches it exactly, including the null asymmetry —
null rejects; a pre-vocabulary row omits the key.

## One path outside the write forecast

`tools/response_lint.py` (modified) is the single out-of-forecast
path. Why the goal required it: the lint vendors a verbatim embed of
`response-manifest.schema.json`, and both `tests/test_schema_embeds.py`
and `validate.sh` assert embed/source JSON-equality — the schema edit
without the embed refresh fails the suite this response's own
validation runs, and the self-containment suite's docstring pins that
a response-manifest change must land on the vendored copy in the same
change. The refresh was done by splicing the source file's bytes into
the embed string and asserting JSON-equality programmatically, then
letting the suite confirm it. Declared in
`feedback.self_reported.forecast_departures` for admission at apply.

## The recorded stop: no stats read side

Per the brief, this is the deliberate floor, written down so it reads
as a decision and not an omission: `docs_read` and `origin` land
write-only. No `bale stats` rollup, no extras-line entry, no members
bucket ships in this session — the established deferral precedent for
new telemetry fields (read side lands when data accrues), and
`docs_read`'s named downstream reader is explicitly out of this
session's scope. The existing suite already asserts stats *tolerates*
new-shape fields' mere presence, and this session's full-suite run
(786 tests OK) exercises that tolerance over the corpus.

## Rider home

Constraint 3 offered the telemetry schema description or the project
doc. I chose the schema description: it is the surface that already
enumerates every other writer epoch, so the one non-writer belongs
beside them, and a doc echo would have been a second home for the same
fact (left as a `deferred` entry for your call). The wording was
written against the self-containment guard's schema-group deny tables
— no project-doc literals, no numbered board/evidence citations, no
session-letter forms — and the guard passes in the suite run. The new
text cites v0.4.24 as the documenting version and v0.4.21 as the
behavior's origin; `bin/VERSION` bumps to 0.4.24 accordingly, which
also keeps the release surface's version-tag drift guard satisfied.

## docs_read and this very manifest

This response's own feedback block cannot carry `docs_read`: the
request-injected lint validates against the pre-change embedded schema
(`additionalProperties: false` on `self_reported`), so the key would
fail the very lint that fills the mechanical stream. The field is
usable from the next request packed against this landing. For the
record, in the field's own spirit, this session's reading was:
manifest.json; CLAUDE.md core (META–11.2); TARBALL.md sections 1, 2,
5, 7 plus 5.9 and 10.1; the README brief; the two edited schemas in
full; the relevant regions of bin/bale_validate.py, bin/bale_pack.py,
bin/bale, bin/bale_stats.py, bin/bale_report.py, tools/response_lint.py,
validate.sh, and the test-suite conventions
(test_schema_embeds, test_global_doc_selfcontainment,
test_telemetry_extensions, test_exchange_record,
test_release_packaging, harness.py headers).

## Small mechanics worth a glance at review

- `apply.sh` restores the exec bit on `tools/response_lint.py` (the
  repo copy is executable; the overlay strips mode), and
  `validation.sh` carries the matching per-path assertion — both
  emitted from the same `--executable` list via the crafter.
- `validation.sh`'s full-suite check ran ~105s here, so wall time
  approaches the 2-minute target; noted in the script header, no
  `--slow` gate at that margin.
- Claims use the annotated object form with `claim_basis: "observed"`
  throughout — every claimed check was actually run in the build
  environment before shipping.

## Proposals

**Seed `docs_read` in the crafter's self_reported skeleton.**
What: have `tools/craft_response.py`'s manifest skeleton include a
`docs_read: []` stub (or a commented nudge) in the `self_reported`
block it emits.
Why: grounded in this session — the skeleton names only the required
self_reported keys, and an optional field with no scaffold presence
tends to go unfilled; the field's value is longitudinal, so early fill
rates decide whether the read side ever accrues the data it is
deferred on.
Scope hints: tools/craft_response.py (and its embed-parity tests if
the skeleton is asserted anywhere); only after this session lands.
