# notes.md — 2026-09-15-board-89-decline-cause-006

Bumped: `bin/VERSION` 0.4.30 → 0.4.31 (apply- and pack-path behavior
change, per the brief). One-apply-behind: the apply that lands this
runs the 0.4.30 apply code one last time, so the new decline lines at
the apply-side prompts show from the *next* apply; the pack-side lines
show from the next pack.

Every `bin/` path is inside the write forecast. `bin/bale` is
untouched (`confirm_yn_decision`, `ConfirmDecision`, the
`CONFIRM_BRANCH_*` names, and `HOOK_DECLINE_LINES` are consumed as row
83 landed them, never edited). The seven `tests/` paths are outside the
forecast — enumerated under "Out-of-forecast paths" below for per-path
admission at apply.

## Chat asides, for the record

Before building I asked one non-blocking question in chat rather than
through `bale relay`: whether the sandbox-unavailable decline's
`fail()` line should also carry the cause parenthetical, or only the
`[bale]` log line that precedes it. You answered "go" with no
preference, so the default I named stands: the cause is on the log
line, the `fail()` text is byte-for-byte what it was. I read this as
a detail call (the brief says the wording is mine) rather than a
blocking intent gap, which is why it stayed in chat; correct me if you
want that kind of question in the exchange record.

## 1. The five prompts and their decline lines

All five switch from `confirm_yn` to `confirm_yn_decision`, keep their
prompt text, default, and every non-TTY behavior byte-for-byte, and
render one of three literal lines on decline. The shape is the row-83
retry's: a module-level table per prompt holding the three FULL lines
(never a cause phrase assembled at runtime — the retry note explains
why: a blind checkpoint greps the file for the rendered line), keyed by
the branch names `ConfirmDecision.decline_branch` returns, rendered by
one small helper, `bale_report.format_decline_line(lines, decision,
**fields)`. The `answered` line quotes the operator's stripped,
lowercased answer in explicit single quotes (not `!r`), as the hook's
does.

The wording, verbatim (the cause parenthetical is the only addition
to each site's pre-existing text; `{sid}`/`{path}` are filled):

**bare-apply confirmation** (`bale_apply.resolve_bare_apply_tarball`;
still exits through `fail()`, exit 1, remedy unchanged):

    bare apply declined at the confirmation (stdin closed or interrupted); nothing applied. Name the tarball explicitly if the resolution picked the wrong file: bale apply <path>.
    bare apply declined at the confirmation (empty answer at a decline default); nothing applied. Name the tarball explicitly if the resolution picked the wrong file: bale apply <path>.
    bare apply declined at the confirmation (answered 'n'); nothing applied. Name the tarball explicitly if the resolution picked the wrong file: bale apply <path>.

**per-path drift admission** (`apply_pipeline`, step 14; the tail is
the line the refusal has always logged and the e2e suite pins):

    admission prompt declined at lib/c.txt (stdin closed or interrupted); nothing admitted at the prompt, nothing lands partially
    admission prompt declined at lib/c.txt (empty answer at a decline default); nothing admitted at the prompt, nothing lands partially
    admission prompt declined at lib/c.txt (answered 'n'); nothing admitted at the prompt, nothing lands partially

**sandbox-unavailable admission** (`apply_pipeline`, pre-staging; the
`fail()` that follows keeps its remedy text):

    sandbox admission prompt declined (stdin closed or interrupted); nothing staged, nothing ran
    sandbox admission prompt declined (empty answer at a decline default); nothing staged, nothing ran
    sandbox admission prompt declined (answered 'n'); nothing staged, nothing ran

**`--supersedes` exchange** (`bale_pack._resolve_supersession`):

    supersession of <sid> declined at the prompt (stdin closed or interrupted); nothing closed
    supersession of <sid> declined at the prompt (empty answer at a decline default); nothing closed
    supersession of <sid> declined at the prompt (answered 'n'); nothing closed

**read-only sweep** (`bale_pack._run_readonly_sweep`):

    read-only sweep: close of <sid> declined (stdin closed or interrupted); it stays open for the next read-only pack or `bale unlock <sid>`
    read-only sweep: close of <sid> declined (empty answer at a decline default); it stays open for the next read-only pack or `bale unlock <sid>`
    read-only sweep: close of <sid> declined (answered 'n'); it stays open for the next read-only pack or `bale unlock <sid>`

Calls I made (ratify or correct):

- **The sweep's empty-answer line is unreachable.** The sweep is an
  accept default (`[Y/n]`), so Enter closes and only two branches can
  decline there. The table holds all three anyway: the vocabulary has
  three names, the parity test asserts every table covers all three,
  and if the default were ever flipped the decline would still name
  itself rather than raise. The suite pins the two reachable ones.
- **The piped supersession path keeps its cause-less line.** Piped
  stdin never reaches a prompt, so there is no branch to name; that
  path logs its existing "decline default applies without a prompt"
  line and, beneath it, the plain `supersession of <sid> declined;
  nothing closed` it always logged. The TTY path replaced that plain
  line with the cause-naming one (there is no longer a second, generic
  line after it). The sweep's piped path was already its own line and
  is unchanged. Pinned both ways.
- **Tables are keyed by string literals, not by `bin/bale`'s
  constants.** A `bin/` sibling imports nothing from `__main__` at
  module scope (the checkpoint-import posture the suites rely on), so a
  module-level table cannot name `CONFIRM_BRANCH_STDIN_CLOSED`. The
  mirror is `bale_report.CONFIRM_DECLINE_BRANCHES`, and
  `DeclineLineTableTest.test_branch_vocabulary_has_three_homes_that_agree`
  reads `bin/bale`'s constants with `ast` and asserts the tuple and all
  five tables match them — a rename fails a test, not an operator's
  terminal. `validation.sh` runs the same comparison.
- **`format_decline_line` raises on misuse** (an accepted decision, a
  table missing the branch): both are caller bugs and a `ValueError`
  is louder than a `KeyError` from inside a `.format`.
- **The bare-apply remedy keeps its `<path>` placeholder.** The brief
  says keep the remedy text, and the placeholder is semantically right
  there — the remedy is for when resolution picked the *wrong* file,
  so no real path fits. Left as is; see Proposals if you disagree.
- **The wizard's two `confirm_yn` uses stay.** The README y/N and the
  config-setup y/N are flow prompts: a decline there is the operator
  answering a question, not a gate refusing work, and there is no
  "nothing happened" to explain. `validation.sh` asserts exactly those
  two `confirm_yn(` calls survive in `bale_pack.py` and none in
  `bale_apply.py`.

## 2. The composed drift line

One expression: `allow_out_of_scope=[*allow_norm, *drift_paths]` —
typed values as the gate normalized them (`scope_path`, sorted),
first, then every drifted path, admitted and refused alike;
`compose_admission_command` dedups, so a path that is both typed and
drifting rides once. The JSON face's `drift.remedy` is the same
variable and follows. Pinned in `test_admission_prompts_e2e.py` beside
the existing composed-line cases: `./lib/zzz.txt` (typed, no effect)
rides as `lib/zzz.txt` before the drift, and the json case asserts the
same. This matches the row-81 lines' `typed + refused` order exactly.

## 3. The move

`format_config_hooks_json` is cut from `bale_config.py` and pasted
directly after `format_status_json` in `bale_report.py` (validation
asserts the adjacency by reading the `def` order). The body is
unchanged; the docstring now reads like its siblings' (family, version,
stability rule, emission path) and points at `bale_config`'s
`CONFIG_HOOKS_OUTCOME_*` constants, which stay with the verb that
speaks them. `cmd_config_hooks` calls
`bale_report.format_config_hooks_json(...)` — it already imported
`bale_report` lazily for `enable_json_mode`/`emit_json_line`, so no new
import. The "lives here because bale_report was frozen" header comment
in `bale_config.py` is rewritten to say where it went. The emitted line
is byte-identical (same six keys, same order); `validation.sh` runs
the live verb (`bale config hooks --json` from a scratch HOME) and
checks one stdout line with `outcome: listed`, `version: 0.4.31`.

## 4. The docstring rider

`persist_pack_session`'s `command` paragraph no longer says
`cmd_handoff` passing `"handoff"` is "proposed but not yet wired"; it
says handoff passes it (wired since rows 63/73) so a handoff open
stamps the command that opened it. I confirmed the call in `bin/bale`
(`persist_pack_session(..., command="handoff")`) before rewording.

## Out-of-forecast paths (admit per path at apply)

Tests ship with code, and none of these are in the forecast:

- `tests/test_admission_prompts.py` — `DeclineLineTableTest`: the
  three-home vocabulary parity, the renderer's contract, and each
  table's literal lines. The natural home for the unit tier (the brief
  names it for the composed-line tests).
- `tests/test_admission_prompts_e2e.py` — the drift line's typed-value
  carry (human + json), and one case per decline cause at the drift
  prompt and the sandbox prompt under a pty (the brief's named suite).
- `tests/test_apply_preflight.py` — `BareApplyResolutionTest`: one case
  per cause at the bare-apply confirmation, asserting the `fail()`
  posture and remedy survived (the brief's named suite).
- `tests/test_supersession_pack.py` — one case per cause at the
  exchange, plus the piped path's unchanged line (the brief's named
  suite).
- `tests/test_readonly_pack.py` — the sweep's two reachable causes; the
  accept-default case already there still pins Enter (the brief's
  named suite).
- `tests/test_hook_acceptance.py` — `test_json_report_shape` now loads
  the renderer from `bale_report` and asserts it left `bale_config`;
  the move breaks this test as shipped, so the fix rides with the move.
- `tests/test_pre_answered_intents.py` — its `__main__` stub supplied
  `confirm_yn`; `_resolve_supersession` now imports
  `confirm_yn_decision`, so the stub is renamed and returns a decision
  (six cases errored on `ImportError` without this — caught by the
  whole-tree run, not the touched suites, which is exactly why the
  brief says to run the tree).

The e2e drives the "stdin closed" branch with `^D` (`"\x04"`) written
to the pty: the line discipline makes `input()` raise `EOFError` at a
TTY prompt. I verified that in isolation before relying on it, and no
harness change was needed. Each new e2e case was also run against the
*unmodified* `bin/` to confirm it fails there (9 of 9 did), so the pins
are real.

## Claims

- `session assertions` — **observed**: rehearsed in a staging-shaped
  copy of the shipped `context/` with `files/` overlaid and the
  manifest placed as `.bale-manifest.json`, run from outside the tree;
  45 assertion lines green.
- `unittest: touched suites` — **observed**: 179 tests across the seven
  files, green (run one discovery per file — `unittest discover -p` is
  not repeatable, only the last pattern runs; my first draft of the
  script had that bug and reported 15 tests).
- `unittest: full discovery (--slow)` — **observed** with
  `BALE_TEST_SLOW=1`: 1006 tests, 1 skipped, and exactly the **two
  pre-existing failures** below. The check passes only when the failure
  set is exactly those two, named verbatim in the script; any other
  failure, or a change in those two, fails it. Read the `[PASS]` line
  with that caveat — it prints the two names each run.

## Pre-existing failures (not mine, not taken)

The shipped `context/` tree does not run green before any file here is
touched: `python3 -m unittest discover -s tests` on the untouched tree
gives 978 tests with **2 failures**, both in
`test_checkpoint_provenance.HandoffBlindnessGateTest`
(`test_handoff_empty_plan_whole_tree_refuses`,
`test_handoff_refuses_covering_reading_plan`). They expect the phrase
`write forecast covers the blind checkpoint`; `bin/bale`'s handoff
refusal now says `pack includes name the blind checkpoint explicitly
(board 6 blindness contract, ADR-0015 read side) …`. The test file is
dated 09-01 and `bin/bale` 09-15 — a message rewording that outran its
assertion. Nothing in this row touches that gate or that file, and
`bin/bale` is out of forecast, so I left it and named it in
`validation.sh`'s `--slow` allowlist rather than masking it. Proposal
below.

## Surprises

- `unittest discover` silently takes only the last `-p` — worth knowing
  for anyone writing a multi-suite `validation.sh` (the harness docstring
  shows single-pattern use, which is why nobody hit it).
- `bale config hooks` refuses to run with cwd == `$HOME` (system-dir
  parity with `config init --global`, per the row-83 notes). The live
  check in `validation.sh` runs from a subdirectory of its scratch HOME.
- `bale_report` and `bale_pack` import cleanly through
  `harness._load_module` with no `__main__` stubs, which is what let the
  table-parity test stay in the unit tier.

## Proposals

- **What:** update the two `HandoffBlindnessGateTest` assertions in
  `tests/test_checkpoint_provenance.py` to the handoff gate's current
  refusal phrase (or fold both into one sentinel constant beside the
  suite's others). **Why:** the tree does not run green as shipped, and
  every session that follows the brief's "run the whole tree" will
  re-discover these two and have to explain them, as this one did.
  **Scope hints:** `tests/test_checkpoint_provenance.py` only; a
  one-sentinel fix once the desk confirms the new phrase is the
  intended one (the test may be pinning a wording the desk wanted
  kept).
- **What:** decide whether the bare-apply decline remedy should name
  the resolved file (`bale apply <real path>`) instead of `<path>`.
  **Why:** it is the last placeholder remedy on the apply path; every
  other refusal since row 78 composes a real line. Against: the remedy
  is for the case where resolution picked the *wrong* file, so a real
  path is the one the operator does not want. I kept the brief's
  "remedy text unchanged". **Scope hints:** one table in
  `bin/bale_apply.py`, plus `BareApplyResolutionTest`.
- **What:** one sentence in `BALE.md`'s apply and pack sections saying
  every admission y/N names its decline cause. **Why:** row 90 (doc
  residue) is running beside this session and this is the doc half of
  the same rider; the hook section's sentence from row 83 is the
  model. **Scope hints:** `BALE.md`; row 90's lane, not a new session.
