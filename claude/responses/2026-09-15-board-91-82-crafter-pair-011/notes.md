# notes.md — 2026-09-15-board-91-82-crafter-pair-011

Two small rows on one file, as billed. Nothing outside the forecast;
three of the six forecast entries went unused (why, below). Bumpless:
`bin/VERSION` untouched.

## Row 91 — what changed, and the one thing I checked twice

The desk read was exact: bale's `validate_clarification_questions`
admits `origin` and refuses `bogus`; the crafter's `--emit-block` exited
2 with `questions[0]: unknown key 'origin'`. The fix is the shape you'd
expect — a `QUESTION_ORIGINS` tuple re-declared from
`bale_validate.CLARIFICATION_ORIGINS` (the same re-declaration posture
as `QUESTION_PRIORITIES`), `origin` appended to `QUESTION_OPTIONAL_KEYS`,
a string check at the named spot, and `origin` added to the row-wide
closed-vocabulary walk so an invented class refuses at any depth,
matching the library.

The thing I checked twice: byte-identity with `bale relay` for rows
*without* `origin`. Admitting a key changes nothing about rendering —
the record is serialized as given — and `ExchangeBlockParity`'s
execution-based comparison still passes over the whole corpus, now
including a row that carries `origin`. So the rows-without-origin pin
holds trivially and rows-with-origin are pinned too.

## Row 82 — the mechanism, for ratification

The brief left "how the rest of `feedback.mechanical` is scaffolded so
the lint's emitter still composes with it" to me. Before choosing I
ran the lint against every candidate shape, and one fact decided it:
**the lint's `--emit-feedback-mechanical` recomputes `schema_valid`
from the manifest as it stands at emit time.** A seeded `feedback`
block with any schema gap — a missing required key, a `null`
placeholder, an absent `self_reported`, an empty `model_identity` —
poisons the emitted `schema_valid` to `false`, and the worker then
pastes a wrong value, fills the rest, re-lints, gets a mismatch, and
has to emit again. Two rounds instead of one. So the seed has to be
schema-valid at the moment the worker runs the emitter, which forced
these choices:

- **The four lint-owned members are present and schema-valid.**
  `response_kind` is filled from `--kind` (the crafter already writes
  that value at the top level; it is mechanical and the crafter's
  own). The three verdicts — `schema_valid`, both `mirror_agreement`
  directions, `claims_subset` — are seeded `false`, the pessimistic
  placeholder. On a clean response the lint's feedback-block check
  flags all four as `FEEDBACK_MECHANICAL_MISMATCH` until the emitter's
  output is pasted over them, so the unfilled seed cannot pass — by
  the mismatch check rather than the schema check. `true` placeholders
  would have made the emit step skippable on a clean response, which
  defeats "fill by running the lint"; `null` poisons the emitter.
- **`self_reported` is seeded with its five required keys** because
  the block requires it and an absent stream is a schema gap at emit
  time. Two of its slots are deliberately schema-INVALID sentinels —
  `budget_pressure: ""` (off-enum) and `compaction_occurred: {}`
  (missing `occurred`) — the `diagnostics.json` `bail_trigger: ""`
  posture, so a block the worker never looked at cannot pass. The
  three arrays are `[]`, which is also the honest empty; there is no
  invalid spelling for "unfilled array" short of a wrong type, and the
  two sentinels already guarantee the block fails unfilled. **This
  means the worker fills `self_reported` and `model_identity` BEFORE
  running the emitter**, whereas §5.2.2's prose orders "paste
  mechanical, then fill self_reported". The reorder is harmless (the
  lint checks `self_reported` for shape only, so filling it early
  changes no mechanical value) and the crafter's stderr line says so
  explicitly. If you'd rather the doc's order be honored literally,
  the alternative is a seed that costs two emit rounds; I judged the
  one-pass composition worth the reorder. TARBALL.md is
  `board-96-doc-97`'s this wave, so I have not touched its §5.2.2
  prose; a one-clause note there ("fill `self_reported` before the
  emit when the crafter seeded the block") is in Proposals.
- **`model_identity: ""`** as the brief says. The schema's
  `minLength: 1` makes the seed lint-invalid until the worker names
  its model — the same unfilled-cannot-pass signal as `summary: ""`.
- **`linkage` is not seeded.** It applies only to a session that went
  through a probe or clarification round; the crafter can't know, and
  the schema admits its absence.
- **Null echo when the request carries no provenance** — the echo
  schema's own case for a pre-0.3.8 pack — with a stderr line saying
  so. Not an error: a worker on a one-apply-behind install should
  still get a skeleton.
- **`--request` is admitted on all three kinds**, not only normal. The
  brief spoke of the normal-kind skeleton, but neither the schema nor
  the lint restricts `feedback` by kind, a bailout is telemetry-
  persisted too, and a kind-specific refusal would be a rule with no
  contract behind it. Easy to narrow if you disagree.
- **The request's `session_id` must equal `--sid`; otherwise refuse.**
  Argument hygiene in the tool's usual style: the lint verifies the
  echo's *shape*, not which request it came from, so a wrong-session
  echo would land in telemetry with no downstream catch. A request
  manifest with no `session_id` at all (hand-rolled) skips the check
  rather than refusing.
- Stray-flag refusals match the surface's existing pattern:
  `--request` with any manifest-less mode (`--changes-only`,
  `--apply-only`, `--validation-epilogue`, `--doc-assertions`) exits
  2, and it rides the exclusion lists of `--probe`, `--bundle`, and
  `--emit-block`.

Dogfooded: this response's own skeleton was crafted with the
response's crafter and `--request request-011/manifest.json`. The
workflow went exactly as designed — one emit, four mismatches flagged
on the placeholders, paste, `result: CLEAN`. The provenance you see in
this manifest's `feedback.mechanical.provenance` is the mechanized
echo, `base_files` and `packed_at` included. Worth saying: I used the
crafter shipped *in* this response rather than the request-carried
one; the `changes[]` computation path is unchanged code, and the lint
recomputed every hash independently.

## Forecast entries that went unused, and why

- **`schemas/exchange-record.schema.json`** — the `$ref` says
  everything. Its `questions` description already reads "the
  clarification question row of response-manifest.schema.json's
  questions.items — by reference, so the row has one home", and the
  top-level description repeats the one-home rule. A sentence naming
  `origin` there would be a second, prose home for the row's field set
  — the exact thing the file says it avoids — and it would go stale on
  the next additive key. The parity is pinned in
  `test_schema_embeds.py` instead, which is where the brief wanted it.
- **`tests/test_exchange_record.py`** and **`tests/test_relay_verb.py`**
  — bale's side does not change. Both suites already exercise `origin`
  implicitly through `validate_clarification_questions` (which admitted
  it in v0.4.24), and neither has a crafter-facing surface to extend.
  Adding an `origin` case to `test_exchange_record.py` would duplicate
  what `test_craft_response.py`'s verdict-parity corpus now pins on
  both sides. Left alone.

`bin/bale_relay.py` and `bin/bale_validate.py` needed no touch, as the
desk read said.

## Registry riders — both consumed

- The `assertEqual` message in `test_rendering_is_byte_identical` now
  names `bin/bale_relay.py`. The remaining "section 29" mentions in the
  file are the two "until the v0.4.21 extraction" history lines (module
  and class docstrings), which are accurate and can't be read as the
  section still existing; I kept them.
- `test_constants_match_section_29` → `test_constants_match_bale_relay`,
  `test_normalization_matches_section_29` →
  `test_normalization_matches_bale_relay`. The grep of the shipped tree
  (`bin/`, `scripts/`, `validate.sh`, `install.sh`, `upgrade.sh`,
  `tests/`, `tools/`) found no consumer selecting either id by name —
  `validate.sh` names the *class* `ExchangeBlockParity` in a comment,
  nothing names the ids. The docstrings that used to explain the names
  are gone with the names.

## Where to look on review

- `build_feedback` in `tools/craft_response.py` — the placeholder
  choices above, in code, with the reasoning in its docstring.
- `CraftRequestProvenance.test_seed_composes_with_the_emitter_in_one_pass`
  — the proof of the one-pass claim against a real lint run, including
  the assertion that the emitter's first-run `schema_valid` is `true`.
- `QuestionRowKeyParity` in `tests/test_schema_embeds.py` — I ran it
  against the shipped (pre-91) crafter to confirm it fails naming
  `origin` as schema-only; it does.

## Proposals

- **A one-clause note in TARBALL.md §5.2.2 for the seeded block.**
  *What:* after "fill `self_reported` honestly", add that when the
  crafter seeded the block (`--request`), `model_identity` and
  `self_reported` are filled *before* the emit, and the emitter's
  object is pasted key-for-key over the four placeholders rather than
  replacing the `mechanical` object (which would drop the echo).
  *Why:* the crafter's stderr says it, but the doc's prose order is
  the one a careful worker follows, and the two now differ by one
  step. *Scope hints:* `docs/TARBALL.md` only; held by
  `board-96-doc-97-terminal-shapes` this wave, so after it lands.
- **Retire the lint docstring's "not emitted; the worker adds them by
  hand" for `provenance`.** *What:* `tools/response_lint.py`'s module
  docstring and `_recompute_mechanical`'s docstring say the two
  optional members are added by hand; `provenance` is now seeded by
  the crafter when `--request` is given. *Why:* a worker reading the
  lint's `--help` is told to hand-copy something the crafter already
  mechanized. *Scope hints:* two docstrings in
  `tools/response_lint.py`; outside this session's forecast and
  explicitly held out of it by the brief, so its own lane.
