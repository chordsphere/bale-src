# Notes — 2026-09-16-board-96-crafter-85-light-block-002

## The light question block this session emitted (TARBALL.md §5.10 trail)

I ended one turn on a light block, before anything was packed. The
questions and the packer's answers:

1. **Keep `--sid` assert-only, never filling a missing session_id?**
   Would assume: yes. **Answer: as assumed.** Assert-only, on
   `--round`'s record-path precedent; a manifest with no session_id
   refuses.
2. **Refuse a rendered field value containing a line break?** Would
   assume: yes, exit 2 naming the field, never flattened. **Answer: as
   assumed**, with a correction to my framing. I had called it a
   second rule beside the count. The packer ruled that it is the count
   rule's "fits on one line" half, which a tool can check, and that
   the refusal text should point at the clarification path. The code
   comment, docstrings and refusal message now say that. The message
   names TARBALL.md 5.10, calls the set a clarification response, and
   points at `--emit-block` of the same manifest. A new test pins that
   across all four fields and three line-break spellings.
3. **Leave §10.4 step 2's "Author the block by hand" untouched?** Would
   assume: yes, as a Proposal. **Answer: no.** Edit §10.4 too; the doc
   must not argue with itself, and the one granted sentence was a
   floor. Step 2 now names `tools/craft_response.py --light-block
   <file>` as the path, with hand-authoring as the fallback where the
   crafter is unreachable.

   While there I also dropped "today" from §5.10's opening paragraph.
   "so a worker can author it by hand today" read as if no render
   existed, one sentence before the sentence naming the render. It now
   says "wherever the crafter is unreachable". The two byte-pinned
   §5.10 sentences (admission, three replies) are untouched, and
   `test_doc_crossrefs` passes.

## The two counts, and this manifest's own values

The honest values for this session are `light_blocks: 1` and
`paste_carried_rounds: 0`. **My manifest omits both keys, deliberately.**
Apply's pre-flight validates the response manifest against the
*installed* `schemas/response-manifest.schema.json`
(`bin/bale_validate.py`'s `SCHEMAS_DIR` is the install root). Until
this response lands and the install picks it up, that schema's
`self_reported` is closed without the two keys. Carrying them would
refuse the tarball at pre-flight.

I checked rather than inferred. Pre-change `bin/bale_validate.py`'s
`validate_response_manifest` accepts this manifest as shipped, and the
same manifest with `light_blocks: 1` added is refused ("unknown key
'light_blocks'"). The brief said this manifest "may carry them"; with
that evidence I chose absence. Absence is the contract's "reported no
count", and this paragraph is where the count actually lives. If the
install you apply with already carries the new schema, adding the two
keys is a two-line edit.

## Judgment calls worth a look

- **`--light-block` accepts only a clarification manifest.** It takes
  neither an exchange record nor a bare rows file. The brief said
  "a filled clarification manifest". An exchange record is a thread
  artifact, and the light tier opens no thread, so a record refuses
  with a message saying that.
- **Refusal order.** Parse and shape come first, then the `--sid`
  agreement, then the row count, then row structure (the same
  `question_row_problems` `--emit-block` uses), then the one-line
  half. So a four-row set with a malformed row gets the count refusal
  first, since the count is the cheaper diagnosis.
- **Optional row keys never render.** `options`, `recommendation`,
  `priority` and `origin` stay out of the block. stderr names which
  rows carry them and says they travel if the packer replies
  "formal", so nothing is dropped silently.
- **The `--help` pin needed a formatter.** argparse rewraps help text
  by `COLUMNS`, so the verbatim stem clock sentence would break
  somewhere at some width. `CraftHelpFormatter` overrides
  `_split_lines` to keep sentences listed in `UNWRAPPED_HELP_SENTENCES`
  whole on their own line; everything else wraps as before.
  `_split_lines` is technically private argparse API. It has been the
  per-argument wrapping hook throughout argparse's stdlib life. The
  suite pins the outcome at 40, 80 and 200 columns, so a future
  argparse that stops calling it fails by name.
- **The rider sentence in §5.2.2 carries no code-span backticks.** The
  brief asked for it verbatim with whitespace collapsed. Backticks
  around `--request`, `model_identity` and `self_reported` would have
  broken a literal match. That makes it the one sentence in the
  paragraph with bare identifiers.
- **`test_schema_embeds.py` keeps its JSON-level equality doctrine.**
  Its docstring says formatting is free to differ. The embed is in
  fact byte-identical to the source (`"\n" + file`), and
  `validation.sh` asserts byte identity as a session check rather than
  rewriting the suite's stated doctrine. The suite gains a shape pin
  for the two counts instead: optional, integer, minimum 0, inside a
  closed `self_reported`.
- **Schema descriptions tag the counts "v0.4.34".** That is the release
  this wave ships as, and the tag follows the "v0.4.24" precedent on
  `docs_read`. `bin/VERSION` is untouched; the bump is
  `board-47a-hold-card-triage`'s.
- **Crafter sections renumbered.** The new section 6 (light block)
  sits between the exchange block and path handling, so 6–9 became
  7–10. The index header's line numbers were recomputed and checked
  against the banners. No test or doc cites the crafter's sections by
  number.
- **Two stale strings fixed in passing.** The crafter's "response dir
  is required" error said only `--probe` and `--bundle` run without
  one. The positional argument's help said only `--probe`. Both were
  already stale for `--emit-block`, and both now list all four modes.
  `test_missing_response_dir_still_an_error_without_probe` still
  matches.

## Which suites are "the four doc-pin suites"

The brief names them by count, not by name, and no file in the request
lists them. `validation.sh` runs `test_doc_crossrefs`,
`test_global_doc_selfcontainment`, `test_sanctioned_pairs` and
`test_clock_discipline`: the suites I found that pin doc or schema
prose. If a different four were meant, the full suite covered them
anyway.

## What I ran, and one environment caveat

- **Full suite before the change**, in a reconstruction of the repo
  from the request's `context/`: 1058 tests, 3 errors, 48 skipped.
- **Full suite on the final tree** (the pre-change tree with this
  response's `files/` overlaid, byte-compared against the mirror
  first): 1077 tests, the same 3 errors, the same 48 skips.
- **The three errors are `test_include_group.TestThisRepoGroup`**,
  reading a repo-root `bale.toml` the request doesn't ship. That is
  my reconstruction's gap, not a regression. I expect them to pass in
  the real tree; they have nothing to do with this change set.
- **`validation.sh` was rehearsed on three branches.**
  - The changed tree: exit 0, about 20 s.
  - The pre-change crafter, lint and doc: exit 1, every targeted check
    FAILs.
  - A one-space change to the value column: exit 1. The byte-pin
    check and the suite both catch it.
- Every needle is asserted on an exit code or a produced string,
  never inferred.

## Out-of-forecast paths

None. All seven `changes[]` paths are in the stamped write forecast.
No sibling path is touched.

## Proposals

- **What:** update `docs/CLAUDE.md`'s INDEX read-paths row for the
  light tier. It currently says the block is "authored by hand per
  `TARBALL.md` §5.10"; it would name the crafter's `--light-block` as
  the path, with hand-authoring as the fallback.
  **Why:** the packer's ruling here was that the docs must not argue
  with each other once §5.10 names the flag. TARBALL.md now doesn't,
  but CLAUDE.md's row still reads by-hand-only. CLAUDE.md is held by
  nobody this wave, but it isn't in this session's forecast, and the
  brief routes CLAUDE.md shape-paragraph changes to a Proposal.
  **Scope hints:** `docs/CLAUDE.md` INDEX row only. The §3 shapes
  paragraph points at §5.10, which now names the flag, so it can
  likely stay as is.
- **What:** let `bale stats` read the two new counts, the way
  `forecast_departures` is read today.
  **Why:** the counts exist so the light tier and paste-carried rounds
  stop reading as zero. Until something aggregates them, they are
  write-only. The obvious consumer is the clarification-rounds
  view: a paste-carried round would add to `clarification.rounds`
  rather than hide under it.
  **Scope hints:** `bin/bale_stats.py` (not this wave's to touch).
  Only after this lands and responses start carrying the keys.
