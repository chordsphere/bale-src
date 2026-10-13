# notes.md — 2026-10-13-twine-surface-row-002

## What landed, and how it was checked

All four brief items, in the two forecast files only. The six text
blocks in the brief are in place byte-for-byte. The two table rows
are one physical line each. The §11.7 lead clause, the §5.2.2
passage and the §7.1 paragraph are re-wrapped at the files' 70
columns. No heading line moved in either file. DOCS.md, CODE.md,
PLANNER.md and bin/VERSION are untouched, and there's no version bump.

**The self-containment guard accepted the twine row as written.** I
read `tests/test_global_doc_selfcontainment.py` whole before landing.
The row hits none of its three deny halves, and nothing in it trips
`tests/test_global_doc_noun.py`: the row has no capitalized `Claude`,
and `claude-opus-5-5` / `claude-opus-5.5` in the new claude.ai cell
are lowercase. So the brief's fallback (a light question block
carrying the guard's refusal line) never came into play. No light
block was emitted (`light_blocks: 0`).

**The `RelayParagraphPins` concern.** `test_doc_crossrefs.py` reads
TARBALL.md §7's lead only up to `### 7.1`, so a paragraph inserted
inside §7.1 can't reach it. The suite's other pins in this area are
EMITTER_RIDER in §5.2.2, section 5's heading list, and the "no `v0.`
token in section 5" rule. All three still hold, because the §5.2.2
edit only extends one clause.

**validation.sh, run twice per TARBALL.md §7.2:**
- *Changed tree:* all nine checks pass and the claim reconciles
  `[agree]`.
- *Unmodified tree:* the six change assertions fail. The three
  invariant guards still pass: headings, untouched-file hashes, and
  the suite run. That's by design, since the brief requires them and
  they guard constraints rather than test the change.
- *Mutation run:* I renamed one heading, appended a byte to DOCS.md
  and altered one word of the PID paragraph. The heading guard, the
  hash guard and the §7.1 assertion each turned `[FAIL]`.

The script writes to `.validation-logs/<UTC stamp>/` in staging,
including its `checks.py` helper, and announces that path. The suites'
own tempfile dirs are announced too. No `__pycache__` was written in
either run.

**Whole suite (`python3 -m unittest discover -s tests`).** I ran it
from the request's `context/` tree as the repo root, under
`PYTHONDONTWRITEBYTECODE=1`, on both trees:
- *Base tree:* `Ran 2002 tests … OK (skipped=48)`.
- *Changed tree:* the same.
- *Comparison:* every test's outcome is identical between the two
  runs. There were no failures or errors, so none of the arc's known
  missing-file baseline failures appeared.
- *Skips:* 47 are the slow gate ("generation-heavy; set
  BALE_TEST_SLOW=1"). The other one is
  `CorpusZeroRegressionTest.test_checked_in_corpus_validates_clean`,
  skipped with "claude/telemetry/ absent in this checkout". The
  request doesn't carry that directory, and the suite says so rather
  than failing.
- *Wall time:* about 11.5 minutes per run. That's why
  `validation.sh` runs only the four doc-pin suites (TARBALL.md
  §7.6's two-minute target).

## Readings I took (ratify or correct)

- **Heading lines.** The brief says "every line beginning with `#`
  followed by a space". Read literally, that matches only the two H1
  titles. I pinned every line matching `#+ ` (fenced examples
  included): 30 lines in AGENT.md, 58 in TARBALL.md. No heading line
  changed under either reading, so the checkpoint's reading can't
  disagree with the landed bytes.
- **`model_identity`.** I reported `anthropic:claude-opus-5-5`. This
  surface is the Claude app hosting a cloud worker session, and its
  system prompt has a model line naming the API string
  `claude-opus-5-5`. Under the ruling this session landed, the API
  spelling wins. The same prompt also warns that the serving model
  can differ from the configured one, so the usual self-report caveat
  holds more than usually here.
- **Registry rider.** This response lands the "picker" half of the
  MASTER.md §3 rider ("AGENT.md §11.7's 'picker' wording…"). The W3
  half was already recorded on 2026-09-24. The rider can close once
  this applies.

## Proposals

**What:** Bring the `model_identity` field description in
`schemas/response-manifest.schema.json` in line with the ruling, and
update the copy vendored into `tools/response_lint.py` in the same
change. Name `unknown` as the vendor token too when the provider is
withheld (`unknown:unknown`). Prefer the API spelling in the example:
`anthropic:claude-fable-5.1` is the picker form, and the ruling now
says the API string `…-5-1` wins when the session sees one.
Optionally, give `tools/craft_response.py`'s `--request` log line and
help an `unknown:unknown` example beside `anthropic:unknown`.
**Why:** The schema description is the field's contract of record
(TARBALL.md §5.2.2 defers to it). Today it says `unknown` only "as the
model token", and its one concrete model example uses the spelling the
ruling demotes. A worker who reads the schema rather than §11.7 will
spell it the old way. The pattern already accepts `unknown:unknown`,
so this is a description-only change.
**Scope hints:** `schemas/response-manifest.schema.json`,
`tools/response_lint.py` (the embedded copy, which must stay
JSON-equal: `validate.sh` and `tests/test_schema_embeds.py` hold
them together), and optionally `tools/craft_response.py`. These are
out of this session's scope by the manifest.

**What:** Revisit the twine row's second cell when twine ships window
accounting that warns the worker as a tool result.
**Why:** The cell's last sentence is conditional on that ("Until
twine's window accounting warns…"). Once twine has it, §11.3's
bail-early discipline is no longer "the whole defense", and the row
will overstate the gap.
**Scope hints:** `docs/AGENT.md` §11.7 only, as a rider on the next
`docs/AGENT.md` holder after that twine release.
