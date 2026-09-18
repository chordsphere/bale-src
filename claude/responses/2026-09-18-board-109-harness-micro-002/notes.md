# Notes — 2026-09-18-board-109-harness-micro-002

Board 109, narrowed per the desk ruling: `_load_cli()` and `normalize()`
into `tests/harness.py`, plus the §5.10 shape-sentence pin that rode
here. `SubcommandHelpLayoutTest` did not move; `tests/test_apply_preflight.py`
and `tests/test_cli_help.py` are untouched and uncreated.

## Out-of-forecast path (admit at apply)

- **`tests/test_harness_cli_loader.py`** (created). The loader's own test —
  tests ship with code, and the brief asked for one that uses the loader
  on at least one real `bin/bale` function. It needed a home: none of the
  three forecast files is about the harness itself, and putting loader
  tests into a doc-pin suite would have been the wrong lane. Also carries
  `normalize()`'s unit test, which neither doc-pin suite had. Declared in
  `feedback.self_reported.forecast_departures` too.

## Look closely here

**§5.10's copy of the shape sentence is not CLAUDE.md's wording.** The
brief says §5.10 "carries the sentence today, second half included",
and that's right for the second half. The first half differs: §5.10 says
"Every turn *the worker* ends in tarball mode takes one
machine-recognizable shape *—* … a probe block *(§4.2)* … or a
clarification response *(§5.9)*", where CLAUDE.md §3 (and
`EVERY_TURN_SENTENCE`) say "Every turn *Claude* … shape*:* …" with no
pointers. So pinning `EVERY_TURN_SENTENCE` against §5.10 would fail on
the shipped bytes for a reason that isn't drift. I read 105's proposal
("pin TARBALL.md §5.10's *copy*") as §5.10's own wording, and pinned
that as `TARBALL_SHAPE_SENTENCE`, against the `### 5.10` body only
(new `subsection()` helper, with a self-test on synthetic headings so
"5.1" never matches "5.10"). A third test holds both pinned constants
to one shared second half, so a future edit to one copy that forgets the
other trips before either doc is read. Mutation-checked: rewording the
sentence, or moving it out of §5.10 but leaving it in TARBALL.md, each
fails exactly the new pin. No doc edit — none was needed, and `docs/` is
read-only for me. If you'd rather the three homes converge on one
wording, that's a doc session's call.

**The doc-pin suites gained a `tests/` path guard.** Their docstrings
advertise `python3 -m unittest tests.<suite>` first, and that form does
not put `tests/` on `sys.path` — a bare `from harness import` breaks
under it (I verified: `test_admission_prompts`, an existing harness
consumer, errors in that form at baseline). Both suites ran in all three
forms before `normalize` moved, so I kept that with a four-line guard
rather than silently narrowing their run modes. `validation.sh` runs both
suites in all three forms.

## The loader, briefly

`_load_cli()` follows the two ad-hoc copies already in the tree
(`test_thread_status.load_bale_module`,
`test_craft_response.ExchangeBlockParity.setUpClass`): an explicit
`SourceFileLoader`, registered under `bale_cli` (never `__main__`, so the
guarded `main()` doesn't run; registered at all so dataclasses resolve).
I chose that over the proposal's `runpy.run_path` because `run_path` with
a non-`__main__` name hands back a globals dict and drops its temporary
module from `sys.modules` afterwards — workable for pure functions,
awkward for a shared helper. What it adds over the two copies:

- **Fresh module per call**, so module state (`_log_file`, constants) a
  test mutates can't leak. Siblings are *not* fresh — they resolve by
  bare name, so a sibling a suite already loaded with `_load_module` is
  the very instance `bin/bale` binds (pinned).
- **`sys.path` hygiene.** `bin/bale` inserts its `bin/` unconditionally;
  the loader undoes that duplicate, so no number of loads grows the path.
  My first draft pinned "exactly one `bin/` entry" and the full run
  proved that wrong — `test_craft_response` and `test_thread_status`
  insert `bin/` themselves. The docstring and test now claim only the
  relative property.
- **A failed load leaves `bale_cli` as it was**, and `bin/bale`'s
  import-time `sys.exit` (empty/missing VERSION) surfaces as a named
  `RuntimeError` chained to the `SystemExit`. Tested against a scratch
  `bin/` with an empty VERSION.

**The limit**, as the brief asked, is in the docstring and pinned by a
test: siblings reach back with `from __main__ import fail` inside their
functions, and `__main__` is the test runner (or the suite file), never
the loaded CLI. So only functions whose call path stays in `bin/bale`
and the siblings' eager surface are in reach. `fail()` still raises
`SystemExit`, as the CLI would.

Unit-tested through the loader: `fail_not_found` (bare, search-miss,
verb-with-no-candidates byte-identity, near-name listing newest-first
with shlex quoting) and `SubcommandHelpFormatter._fill_text` (paragraphs
and literal blocks kept, wrapping, and byte-for-byte parity with the
default formatter on unstructured text). `compose_retry_successor` is
deferred: it reads held-tarball state from a repo, not a pure call.

## Suite counts (full default run, `unittest discover -s tests`)

| | Ran | Failures | Errors | Skipped |
|---|---|---|---|---|
| Before | 1247 | 2 | 3 | 48 |
| After | 1270 | 2 | 3 | 48 |

+23 = 20 in the new loader suite, 3 in `test_doc_crossrefs`. The failing
set is identical before and after:

- The 3 `test_include_group.TestThisRepoGroup` errors — the brief's known
  baseline, confirmed by my own run rather than trusted.
- **2 `test_changelog_record` failures the brief didn't list**
  (`test_corpus_is_not_empty`, `test_current_version_has_a_valid_record`).
  Same class: they read `claude/changelog`, a repo-root path the request
  doesn't place. They should pass in real staging; worth adding to the
  known-baseline sentence in future briefs.

Wall time ~210 s both runs, so the full suite sits behind `--slow` in
`validation.sh` (TARBALL.md §7.6); the default tier runs the targeted
suites plus the harness consumers co-loaded in one process, including
both other `bin/bale` loaders.

## Proposals

- **What:** adopt `_load_cli()` in `tests/test_thread_status.py`
  (`load_bale_module`) and `tests/test_craft_response.py`
  (`ExchangeBlockParity.setUpClass`), retiring the two ad-hoc copies.
  **Why:** they are the second and third copies of the same loader, and
  the harness's doctrine is one home per helper; both also leak a
  duplicate `bin/` onto `sys.path` per load, which the shared form does
  not. **Scope hints:** those two files only; check neither is held by
  an open sibling. Behavior-preserving except the attribute namespace
  (`bale_cli` vs their own names), which neither suite reads.
- **What:** a unit test for `compose_retry_successor` via the loader.
  **Why:** board 106 named it, and it's the one of the three I didn't
  reach — it needs a scratch repo with held-tarball state, which the
  sandbox makers already build. **Scope hints:** a new test file or the
  retry suite, whichever is free.
- **What:** add `test_changelog_record`'s two cases to the briefs'
  known-in-request-baseline sentence beside `TestThisRepoGroup`.
  **Why:** a worker running the full suite inside a request sees five
  red tests where the brief warns of three. **Scope hints:** brief
  template / planner desk, no code.
