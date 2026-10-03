# notes — 2026-10-03-config-wizard-ui-002

`bale config init` now draws through a new shared layer,
`bin/bale_wizard.py`. Every section gets a heading, every key gets one
screen with its `n/19` and dotted key, the default view is short with
the full text one `?` away, the answer grammar is explained once,
everything fits 80 columns, color shows only on a TTY, and a review
runs before anything is written. What it writes is unchanged. I
checked that three ways, below.

## How "no semantic change" was established

1. **Differential, old vs new.** Before shipping, I loaded the
   pre-session `bin/bale_config.py` (v0.4.45, from the request) beside
   the new one. I drove both `walk_configurables` with identical
   per-key answers over 6000 randomized cases: both layers; random
   existing and inherited configs, misshapen values included; and
   answers drawn from Enter, `-`, `x`, the bool spellings, colon
   lists, the three reject-with-hint inputs, EOF and ^C. The returned
   dicts and the rendered TOML were equal in every case. Each case
   was then re-run with `?` typed before every answer, and gave the
   same result. A second differential did the same for
   `walkthrough_baleignore` over 4000 random files (CRLF and
   no-trailing-newline included) and answer sequences, comparing the
   resulting file bytes. The new confirm got Enter, or EOF once stdin
   had closed.
2. **Frozen in the tests.** `tests/test_wizard_ui.py` carries the
   differential's evidence as a table (`SEMANTICS`): answers →
   resulting config, each also run with `?` first.
3. **Byte-for-byte in `validation.sh`.** A real piped
   `bale config init` runs from a scratch install over a fixture that
   touches all 19 keys, an inherited global layer, a hand-edited
   unknown key, and a CRLF `.baleignore`. The written files' sha256s
   are compared against what v0.4.45 wrote for the same fixture; I
   computed them by running the old tree. This check passes on the
   unmodified tree too, by design: it is the invariant, not the
   change. The other session assertions fail on the old tree and pass
   on the new; I ran the script against both.

The full suite (1621 tests) matches its pre-session baseline exactly:
the same 4 failures and 3 errors before and after. All seven come from
files this request's `context/` doesn't carry (repo `README.md`, ADRs,
the changelog corpus, the repo's own `bale.toml`). They should pass in
the real checkout, which is why `validation.sh --slow` claims pass as
`predicted`.

## Decisions to ratify

- **The confirm gate's ^C.** Before writing `bale.toml` (and before
  writing or removing `.baleignore` when patterns changed), the wizard
  asks `Write bale.toml? [Y/n]`. Enter writes, as the brief required. A
  closed stdin also writes, which keeps scripted and piped runs
  landing the file exactly as before. A typed `n` leaves the file
  alone. **^C at the gate also leaves the file alone.** The brief's
  "EOF or ^C keeps" is about item prompts, where ^C keeps the value.
  At a write gate, "keep" most naturally means keep the file on disk,
  and a user who hits ^C there is trying to stop. No pre-session input
  reaches this prompt, so nothing that used to write stops writing.
  Flip it to "^C writes" if you read the brief the other way; it's one
  argument (`interrupt=`) at the two call sites.
- **No rewrite when nothing would change.** If the file on disk
  already equals the rendering byte for byte, the review says "no
  changes", nothing is asked, and nothing is rewritten. The summary
  line says `unchanged` where it used to say `updated`. The bytes are
  the same either way. When only the layout differs (a hand-written
  file without the header, say), the review says "no value changes",
  explains the rewrite, and Enter writes.
- **`?` is now the help gesture, never a value.** Typing a bare `?` at
  an item prompt used to set the key to the literal string `?`. Now it
  shows the full description and asks again. The brief asked for the
  gesture; I'm flagging it because it is the one answer whose meaning
  changed. No plausible value for any of the 19 keys is a lone `?`.
- **Color policy.** Color only when stdout is a TTY, `NO_COLOR` is
  absent (any value counts as set, empty included, since the brief
  says "never when NO_COLOR is set"), and `TERM` is set and not
  `dumb`. That last rule means a bare pty with no `TERM`, like the
  test harness's env, is plain. Color is decoration only. Each code
  wraps a whole line or a whole field, so substring checks like the
  pty suites' never straddle an escape.
- **Import style.** `bale_config` imports `bale_wizard` at module top
  rather than lazily via `__main__`. The brief allowed either. The
  layer is a leaf (stdlib only, nothing from `bin/`), so there is no
  cycle to sidestep, and `validation.sh` plus a test pin the leaf
  property. `bale_pack` can do the same.
- **Walk order as data.** `WIZARD_WALK_ORDER_BOTH_LAYERS` and
  `WIZARD_WALK_ORDER_PROJECT_ONLY` declare the 10 + 9 keys. Positions
  and section headings are derived from them. `Walk.begin` refuses a
  key that isn't listed, and a test pins that the walk visits exactly
  that order and that the order equals the declared `*_VALUES` tuples.
  So a key added to `walk_configurables()` without its order entry
  fails loudly, rather than showing a wrong `n/N`.
- **Summaries are new text; descriptions are untouched.** Each key got
  a one- or two-line summary, written fresh. The existing descriptions
  stay word for word (BALE.md citations included, per the open
  ruling). They show on `?`, re-wrapped to 80 columns.
- **`test_sandbox_wrapper` pins "NEVER silent" in the default view.**
  That file is outside my forecast, so I kept the phrase whole by
  giving `sandbox.enabled` a two-line summary. Summaries accept
  explicit lines for exactly this.
- **Git identity is restyled for pack too.** `walkthrough_git_identity`
  is shared with `bale_pack`'s git-init walkthrough, so that step now
  draws with the layer's heading there as well. Its signature is
  compatible (`repo, ui=None`). Nothing else in the pack path changed.

## Out-of-forecast paths (admit at apply)

Both are new files the pack could not have named (ADR-0014). Both are
recorded in `feedback.self_reported.forecast_departures`.

- **`bin/bale_wizard.py`** — the shared presentation layer itself.
  The brief's outcome 1 asks for "one place" `bale_pack` can import,
  which makes it a new `bin/` module. The three release lists in the
  forecast (`scripts/build.sh`, `install.sh`, `validate.sh`) list it.
- **`tests/test_wizard_ui.py`** — the layer's test file, which the
  brief expects. 49 tests: the layer primitives, the walk order, the
  frozen semantics table, the review gate, the `.baleignore` step,
  and pty end-to-end runs for width, color, piped output, and prompt
  count.

## Places to look closely

- `bin/bale_config.py` §3: `_prompt_value` / `_prompt_bool` /
  `_prompt_path_list`. The decision logic is the old code with `print`
  swapped for `ui.*`. The diff is large mostly because every call site
  gained `walk`, `kind`, and `summary` arguments.
- `review_and_write_config` and the `.baleignore` phase 3 in
  `walkthrough_baleignore`: the only new control flow.
- Prompt count for the pty suites: a fresh project walk is 19 items,
  the bale.toml gate, and one additions prompt, 21 in all, well under
  the 40 newlines the suites send. `test_wizard_ui` pins that number.
- Layout of a fresh Enter-through run: about 205 lines, prompt lines
  included, against the desk's ~320 measured the same way (326 for
  v0.4.45 in this sandbox). Every line is within 80 columns except lines naming an
  absolute path. Those print whole, label included, never broken
  mid-path.
- `model_identity` is `anthropic:claude-opus-5-5`, the identifier this
  session was configured with. The surface says the serving model can
  differ, so read it as self-reported, as the field already is.

## Proposals

- **What:** Add `bin/bale_wizard.py` to `upgrade.sh`'s
  `REQUIRED_RELEASE_MEMBERS`, and while there, true up the other
  load-time imports that list lacks (`bin/bale_relay.py`,
  `bin/bale_open.py`, `bin/bale_sandbox.py`).
  **Why:** `upgrade.sh`'s own comment says the list is "the members
  whose absence bricks the install". `bale_wizard` is a load-time
  import of `bale_config`, which `bin/bale` imports at load. The list
  is a deliberate subset, so leaving it out breaks no build. It only
  weakens the pre-wipe check against hand-made tarballs. `upgrade.sh`
  was outside this session's forecast.
  **Scope hints:** `upgrade.sh` only; `build.sh`'s subset assertion
  already holds.

- **What:** Finish truing up bale-internals.md §1 for the siblings it
  never describes (`bale_sandbox`, `bale_open`, `bale_relay`).
  **Why:** I corrected the file count (now thirteen) and added
  `bale_wizard`, but the heading list and the per-module paragraphs
  still skip those three.
  **Scope hints:** `claude/context/bale-internals.md` §1; a doc-only
  session.

- **What (for the 99b true-up; BALE.md is out of scope here):**
  §3.6 step 2 should mention the review before writing and the `?`
  help. The §2 install-layout block (around line 186) lists
  `bin/bale_config.py` but neither `bin/bale_wizard.py` nor the other
  newer siblings. The command table row for `bale config init` (around
  line 500) could say "reviews the changes, then writes".
  **Why:** they describe the wizard's flow, which now includes a
  review gate.
  **Scope hints:** BALE.md §2, §3.6, the commands table.

- **What (for session E, `bale-cli-reference`):** The
  `bale config init` description in `bin/bale`'s parser could mention
  the review gate and `?`. That text is what `bale help config init`
  prints, and it now carries into requests.
  **Why:** it is the user-facing help for the flow this session
  changed. `bin/bale` is E's forecast, so I didn't touch it.

- **What (for session B, `pack-wizard-ui`):** Use the layer this way:
  `WizardUI` for drawing, `Walk(order, sections)` if the pack wizard
  wants `n/N`, `ask` for free text, and `confirm(default=..., eof=False,
  interrupt=False)` for its y/N exchanges. That keeps `confirm_yn`'s
  decline-on-EOF exactly. Drive in-process tests by
  `bale_wizard.ITEM_HEADER_RE` (see the two updated drivers).
  **Why:** these are the seams I left for it. The pack wizard's
  decline defaults differ from config init's write gate, and `confirm`
  takes them as arguments rather than assuming.

- **What (for session C, `wizard-defaults`):** Add the
  detected-default-plus-alternatives prompt as `ask_choice` beside
  `ask_item` in `bale_wizard`. Render the alternatives as numbered
  `state` rows (the table already supports per-row asides), return the
  raw answer, and let `bale_config` map a number to its value, the
  same split as today. Mind `?`: it is taken, and a bare digit would
  be the natural pick syntax.
  **Why:** the module docstring's "Extension points" names this slot.
  Keeping meaning out of the layer is what let this session prove "no
  semantic change" in one file.
