# notes.md — 2026-09-14-doc-lane-74-76-002

Three files change: `docs/TARBALL.md`, `schemas/response-manifest.schema.json`,
`tools/response_lint.py`. Nothing under `tests/`, nothing under `bin/`,
no VERSION bump. `tools/craft_response.py` is in the forecast but
unchanged — see below.

## Row 76 — what landed

- The echo node gains `base_files`: `object`, `additionalProperties:
  {string, minLength 1}` (the request schema's definition, byte-for-
  byte on the two shape keys), **not** required, description in the
  file's own idiom citing v0.4.23 only. Inserted after
  `checkpoint_scope_admitted`, matching the request file's key order.
- The lint's `RESPONSE_MANIFEST_SCHEMA_JSON` embed was refreshed by
  splicing the new schema bytes in verbatim — it was byte-identical
  to the file before and is byte-identical after (stricter than the
  suite's JSON-equality; `validation.sh` asserts both). The lint's
  diff is exactly the five new lines.
- §5.2.2 keeps "echoed verbatim" and gains one clause: the echo's
  schema admits every key the request block can carry, `base_files`
  included.

**The defect, reproduced and closed mechanically.** A synthetic
response whose echo carries `base_files` fails the shipped lint with
`additional property 'base_files' not allowed` and passes the
refreshed one; `validation.sh` re-runs that check in staging.

## The crafter: no change, and why

The brief said to stop the crafter dropping `base_files` from the
echo it seeds — only if no test pins the skeleton's key set. Neither
branch applies: `tools/craft_response.py`'s skeleton emits no
`feedback` block at all (verified by running it; `--help` and a grep
for `provenance` agree). The echo is worker-authored end to end, per
§5.2.2's "the optional `linkage` and `provenance` members are the
worker's to add". So there is nothing to stop dropping, and I did not
touch the crafter. If the desk wants the crafter to *seed* the echo
from the request manifest, that is a feature, not this row — proposed
below.

## Ratify: this response's own echo omits `base_files`

Look at this one closely. `feedback.mechanical.provenance` here
carries every request-side key **except** `base_files`, which is the
exact thing this session admits. Reason: bale's apply pre-flight
validates the whole response manifest, feedback block included,
against the *installed* `schemas/response-manifest.schema.json`
(`bin/bale_validate.py`, `validate_response_manifest` →
`_load_schema_lib`, which reads `SCHEMAS_DIR` in the install). The
install applying this response is v0.4.26 with the pre-change schema,
so an echo carrying the key would bounce at pre-flight. This is the
one-apply-behind bootstrap case the schema already documents for
PLANNER.md in `contract_docs`; the wiring session's own response is
the last one that has to drop the stamp. Rows 71, 75, 73A dropped it
for the same reason without saying so; this note says so.

## Row 74 — placement calls

1. **Single-line commands.** §3.4's existing "Commands are
   single-line" paragraph is extended in place (the sentence widens
   to every emitted command and carries the reason: continuations do
   not survive chat copy-paste). §1 Conventions gains a one-bullet
   pointer — §1 is a bullet list of cross-cutting conventions, so it
   is where a pointer belongs. No board number, no project doc, no
   mention of the specimen's origin.
2. **Both transports.** Landed in §5.9.2's worker-side-flow paragraph
   (the sentence after the `--emit-block` input description), and
   §10.3 step 4 changed from "Deliver by either courier — the
   tarball, or…" to "Deliver both couriers — the tarball, and…", now
   naming `tools/craft_response.py --emit-block`. Leaving step 4 as
   "either" would have contradicted the new rule, so the derived
   checklist had to follow the section it compresses. The two
   surviving "the operator's choice" sentences (§2, §5.9.1) still
   read correctly: the worker ships both, the operator chooses which
   to carry. Step 4's closing "Never in chat." became "Never as a
   chat aside (§5.9.1)" — the paste block *is* delivered through
   chat, so the old wording read as a contradiction once both
   couriers ship; the new wording is `CLAUDE.md`'s INDEX phrasing.
3. **The blocking-ask path in §10.1.** Landed as step 2's own second
   sentence, not step 1's: step 1 is about a hand-rolled request
   missing a global (pause-and-ask is right there), whereas the
   planning step is where a worker discovers it cannot list the
   files or decide the deferrals without the planner. The sentence
   names `--kind clarification`, `--emit-block`, `bale relay`, and
   the telemetry consequence (`clarification.rounds` in
   `schemas/telemetry-record.schema.json` reads zero against real
   rounds). Step count in §10.1 is 11 before and after; step 10 keeps
   its number; the heading set is identical.

## Verified

Both shipped suites green on the shipped copy and on a staged copy
with `files/` overlaid; `validation.sh` dry-run exit 0 in that copy
with `.bale-manifest.json` simulated, so all four claims are
`observed`. Full discovery was not run — suites not shipped are not
claimed.

## Proposals

**Pin the echo/request key parity.** A test asserting
`set(request provenance keys) ⊆ set(response echo keys)` across the
two schemas, so the next request-side stamp cannot land without its
echo. This session could not add it (no edit under `tests/`); it
belongs in `tests/test_schema_embeds.py` or beside it. `validation.sh`
here runs that exact assertion once; the test makes it durable.

**Crafter seeds the provenance echo.** `tools/craft_response.py`
could read the request `manifest.json` (when given `--request`) and
seed `feedback.mechanical.provenance` verbatim plus an empty
`model_identity`, so "echoed verbatim" is mechanized rather than
hand-copied. Only after the new schema has applied — a seeded
`base_files` would bounce on a one-apply-behind install.
