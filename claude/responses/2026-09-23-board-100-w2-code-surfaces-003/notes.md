# notes — 2026-09-23-board-100-w2-code-surfaces-003

W2 of the 100 arc, as briefed: every surface in the brief's "work, by
surface" list landed, bin/VERSION is 0.4.42 with its changelog record,
the tree is green (1500 tests, 32 new, 47 skipped — same skip profile
as the 0.4.41 baseline; validate.sh 92/92), and W1's files were never
touched.

## The rulings, as ratified

1. **The noun** — swept per hat: *the agent* where either hat could hold
   the sentence, *the worker* where the sentence means the builder,
   "I/me" left alone. Zero capitalized `Claude` words remain in `bin/`,
   `tools/`, `schemas/`; BALE.md's 26 lines swept; every `CLAUDE.md`
   cross-reference (BALE.md, `GLOBAL_DOCS`, the opener text at
   bale_pack.py:4300-4312) stays, because the file has not moved.
2. **Depth** — 1–3 done; 4 landed as the key only (`[layout] agent_dir`,
   default `claude`), renaming nothing anywhere.
3. **Compatibility, for good** — `claude-decides` stays in the enum and
   the choices; the `CLAUDE.md`-keyed `contract_docs` set stays a valid
   branch on both schemas. The validate.sh refusal of a leftover
   `docs/CLAUDE.md` is W3's and untouched.
4. **model_identity** — `type: string` kept; description names
   `<vendor>:<model>` verbatim, lowercase, spaces→hyphens, `unknown` as
   the model token, no suffix; `pattern`
   `^[a-z0-9]+(?:-[a-z0-9]+)*:[a-z0-9]+(?:[.-][a-z0-9]+)*$`. Accepts
   `anthropic:claude-fable-5.1` and `anthropic:unknown`; rejects all
   three live corpus spellings (the new suite reads them out of
   `claude/telemetry/` when present and carries the literals as the
   fallback). The telemetry schema's rider clause is retired in
   description text only; the three stamps are untouched.
   `includes_missing` stays a string array; the description names the
   path form and the `decision:` form (marker verbatim).
   `linkage.depends_on` — no change, as ruled.
5. **The spellings** — `agent-decides` byte-exact; `[layout]` /
   `agent_dir` byte-exact in bale.toml syntax; **`CARRIED_TOOLS` as
   ruled, no deviation.**
6. **Amendment A** — admitted, not flipped: schema enum and argparse
   choices take `agent-decides` (the `--expects-probe` help names both);
   bin/bale:4191 (handoff) and :6100 (pack default) still say
   `claude-decides`; bale_pack.py's session-only-flags table still
   carries the old value as its parser default, with a comment noting
   the alias differs from the default and so refuses beside `--context`
   like any typed value. Smoke-tested through the harness: a pack typed
   without the flag stamps `claude-decides`, one typed with
   `--expects-probe agent-decides` stamps that.

## Decisions to ratify

- **`[layout]` is project-layer only.** The brief named the walked
  surface but not the layer. I applied the `[validation]` ruling's
  reasoning: the value names a directory of *this* repo's tree, and a
  global default would silently reroute every repo's telemetry the
  moment one operator set it. So `merged_config` never inherits it, the
  global wizard never walks it, and `layout_agent_dir(repo)` reads the
  project file only. If you want a global layer later, it is one
  `elif key in g_layout` branch and a wizard `inherited=` — but I
  would not.
- **The subset validators gained `pattern` and `oneOf`.** Neither
  bin/bale_validate.py nor the lint's `_schema_walk` supported either
  keyword (the changelog schema's own description said so). Without
  them the brief's schema shapes would have been decoration: the lint
  and apply would have walked past `oneOf` and `pattern` silently. Both
  validators gained both keywords in step — `pattern` is an unanchored
  `re.search` (JSON Schema semantics; the schema anchors), `oneOf` is
  exactly-one with zero matches naming each branch's first failure.
  Existing schemas use neither elsewhere, so nothing else's behavior
  changes; the new suite pins the two implementations against each
  other.
- **Stale "no oneOf / no pattern" remarks corrected.** Three schema
  descriptions (the response `claims` field, changelog-record's
  header and `version`) and three bale_validate.py comments justified
  Python-side checks by the validator lacking the keyword. Once it has
  them the sentence is false; I reworded each to say the split predates
  the keyword and stays. The Python checks themselves are unchanged.
  Look at these if you'd rather the historical wording stood.
- **`layout_agent_dir(repo)` short-circuits without a bale.toml.**
  `load_config` does `from __main__ import fail` on every call, which
  raises under a unit runner. `telemetry_record_path` is reached
  in-process by several suites on tmp repos with no config file, so the
  convenience accessor returns the default before touching the loader
  when the file is absent. With a file present it goes through the
  strict accessor and fails loud on a misshape, as the siblings do.
- **Vocabulary residues, deliberately kept.** (a) *prompt injection* in
  bale_pack.py's opener rationale and BALE.md §7.7 — a term of art, not
  the carriage sense. (b) In the owned tests, the Python-harness idiom:
  `path-injected sibling import`, `__main__-injection precedent`,
  release-packaging's git "tags injected" — a third sense. Say the word
  if you want those swept too; it is a five-line sed.
- **Messages that still spell `claude/telemetry/`.** The brief classed
  every non-path hit as docstring or message and named only the three
  path sites; I left the prose on the default spelling and BALE.md now
  says so. Listed under `deferred`; see Proposals.
- **One `.baleignore` wizard line** said the model reads the file when
  packing. Bale does; it now says bale. Flagging because it is a
  meaning change, not just the noun.
- **bale_config's `_PROJECT_TOML_HEADER`** and bale-src's own
  `bale.toml` are untouched: the header points at the wizard rather
  than listing sections, and this repo has no reason to set the key.

## Drift — paths outside the forecast (ADR-0015; also in `forecast_departures`)

- `tests/test_layout_and_formats.py` — **created**. The brief left "a
  new test for the regex and the key set" to my call; it pins those,
  plus the `[layout]` accessor/merge/renderer/wizard/consumers and the
  `pattern`/`oneOf` keywords across both validators, none of which any
  owned test covered.
- `tests/test_forecast_ledger.py` — **one fixture spelling**,
  `"model_identity": "fixture"` → `"fixture:model"`. The new pattern
  refuses free text, so its end-to-end lint assertion failed; this is
  the only change needed to keep it green — exactly the enumeration the
  brief anticipated.

Three owned tests took the same one-token fixture change for the same
reason (test_craft_response.py ×3, test_response_lint.py ×1,
test_planner_admission.py ×1); they are in-forecast and in `changes[]`.
`tests/test_stats_*.py` carry `"model_identity": "fixture"` in
in-process records that never meet the schema; left alone.

## Where to look on review

- `bin/bale_config.py` — the `[layout]` block is the largest new code:
  `LAYOUT_VALUES` / `DEFAULT_AGENT_DIR` after `PROBE_VALUES`, the
  accessor trio after `get_probe_clipboard_command`, the walk block
  after the probe block, the renderer branch last.
- `bin/bale_rollback.py` — `_split_untracked_disregarded` gained a
  third parameter (`agent_dir`, default `"claude"`); the guard passes
  it from the merged config it already read for `archive_dir`.
- `schemas/*-manifest.schema.json` — the two `oneOf` blocks are
  hand-laid to the files' existing formatting; the lint's embed is
  byte-for-byte the same text and `test_schema_embeds` still passes.
- `validation.sh` — 21 session assertions fail on the unmodified tree
  and pass with the change (run both ways); the suite is behind
  `--slow` (~5 min against the 2-minute target), and I ran it there
  too, which is the `observed` basis on both claims.

## Proposals

- **Render the configured directory in messages.** ~20 docstrings and
  user-facing lines in `bale_report.py`, `bale_stats.py`,
  `bale_apply.py` (the json key docstrings) and `bale_pack.py` still
  say `claude/telemetry/`. Under a configured `agent_dir` they would
  name the wrong path. Worth a small pass once W3 lands and the
  spelling is settled; the one home for the path is
  `bale_report.telemetry_dir`, so each message can derive from it.
- **`bale config init` could offer to `git mv`** when `agent_dir` is
  set to a name whose directory does not exist while `claude/` does.
  Today the prompt says to rename in git and set the key in one commit;
  doing it for the operator is a few lines, but it is a write to the
  working tree from a config wizard, which I did not want to introduce
  under this goal.
- **A `pattern` for `packer`** (`provenance.packer`) would consolidate
  the other free-text identity the retired rider named. Same mechanism
  as `model_identity`, one description and one regex; needs a ruling on
  the format first.
