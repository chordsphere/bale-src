# notes — 2026-09-16-board-pack-ux-micro-004

## Retry: what the HOLD showed and what changed

The held attempt (commit d8bf656, applied with
`--accept-checkpoint-change` over the amended oracle cc6b44200d8d)
passed six of the eight blind checks and my own validation.sh in full.
Two checks failed, and both failures were mine.

- **"verbose names gitignored include entries as not-tracked drops".**
  I built item 3 on a per-path `git ls-files --others --ignored
  --directory` listing. Rehearsing the entry shapes afterward showed
  three defects. A gitignored directory entry printed as git renders it
  (`gen/`), not as typed (`gen`). A directory whose contents are all
  ignored but which isn't ignored itself (`logs` under `*.log`) printed
  two lines (`logs/` and `logs/x.log`). And it reported ignored files
  under entries the walk did reach, which is broader than both row 92's
  text and ratified answer [1] ("gitignored include entries and entries
  matching no git ls-files path"). My rehearsal only exercised a file
  under a reached directory, which is exactly the shape that hid all
  three. The fix is one rule per include entry, printed as typed: it
  drops when no listed path equals it or lies under it. That covers
  every shape [1] names with no second git call, and the error branch
  for that call is gone with it.
- **"opener shape pin lives in test_pack_opener".** The brief said
  *move `OpenerShapeSentenceTest`*, and I moved the test while
  dissolving the class into a `PackOpenerBase` method, so the class
  existed nowhere. It is now `class OpenerShapeSentenceTest` in
  `tests/test_pack_opener.py`. It inherits from a new test-less
  `PackOpenerFixture` (setUp plus helpers), so it doesn't re-run
  `PackOpenerBase`'s seven tests, whose name and ids are unchanged.

Both validation.sh checks were tightened to the contracts that failed.
The rehearsal packs a gitignored file entry, a gitignored directory
entry, an all-ignored-contents directory and a shipping untracked file,
and compares the exact drop lines. The assertion requires the class by
name and runs `test_pack_opener.OpenerShapeSentenceTest` by class id.
Against the base files both fail, and against the held response's
shapes they fail by construction. Nothing else changed: items 1, 2, 4
and 5 carry the same bytes and checks as the held attempt.

## Light question block (the trail)

One light block went out before the tarball, after the build and while
the tool limit paused the turn; nothing shipped ahead of the reply.
Answers:

- **[1]** Item 3's drop lines cover gitignored include paths and include
  entries matching no `git ls-files` path; an untracked-not-ignored file
  ships and gets no line. **Answered: as built.** The brief's
  `src/untracked.py` example was the desk's error (rehearsed here: that
  file ships today); the planner reports the oracle was amended to match.
- **[2]** Item 4 warns on bare-sibling imports (`from harness import X`,
  `import harness`) as well as `tests.x`. **Answered: as assumed**, with
  the rule stated as "warns when `tests/<name>.py` exists and is absent
  from the shipped set". My build resolved bare names only against the
  importer's own directory; that is identical for files directly in
  `tests/` but missed a nested importer, so after the answer I added the
  `tests/` root as a second resolution site, with a nested-importer test.
- **[3]** Items 2 and 4 judge against the shipped set after excludes, so
  a `--write` file dropped by `--exclude` warns. **Answered: as assumed.**

## What I found that the brief didn't say

- **Row 92's own text was right; the brief's rehearsal line wasn't.**
  `list_git_files` walks `--cached --others --exclude-standard`, so the
  invisible drops are include entries nothing in that listing reaches
  (gitignored, empty, or nonexistent). The nonexistent case is the
  handoff typo case the row names:
  `bale handoff` feeds unfiltered reading-plan paths straight into
  `gather_files_for_pack`. On `bale pack` a nonexistent `--include`
  refuses before walking, so there the entry case is only an empty
  directory, which is what the pack-side test pins.
- **This repo has zero `tests.`-prefixed imports.** Its idiom is bare
  siblings (`from harness import` in 49 files, `from test_handoff_fixture
  import` in 4), so a literal `tests.x` scan would never fire on bale-src.
- **Item 1's residual wording.** The refusal's tail still says negation
  is "not supported in .baleignore at v0.1" for a `--exclude` pattern too,
  because that sentence is the `ValueError` text raised by
  `BaleignoreMatcher.from_lines` in `bin/bale` (board-99a's path this
  wave). The prefix now attributes correctly in both directions; the tail
  is proposed below.

## Look closely on review

- `untracked_include_entries` reuses the walk's own listing (no extra
  git call) and runs only under `--verbose` with includes set; the quiet
  path's import surface and output are unchanged (pinned).
- Both new warnings print pre-sid, so like every pre-sid line they reach
  the terminal (stderr under `--json`) without a session-journal copy.
- The candidate picker lists every `.sh` in cwd, so in bale-src's root
  `install.sh`, `upgrade.sh` and `validate.sh` will appear. Newest-first
  keeps a just-downloaded checkpoint at `[1]`, and the brief specifies
  `.sh` by name, so I left it.

## Validation

`validation.sh` runs the five touched suites plus `test_crlf_tolerance`
(which imports `PackGuardsBase`), five piped scratch-repo rehearsals of
items 1–4 against the staged tree, and the item-6 class assertion. The
full discover run is gated behind `--slow`; on the retry tree it took
220 s (1078 tests, 48 skipped, all green). Claims are `observed`.

## Proposals

- **What:** a BALE.md sentence for the two new pack-time warnings
  (forecast-not-included; included test importing an excluded test
  module), near the §7.4/§6.4 pack guard prose.
  **Why:** both are new operator-visible output with a "warning, never
  refusal" posture worth stating; the brief routed it here.
  **Scope hints:** `BALE.md` (board-47a's path this wave), after that
  session closes.
- **What:** split the `ValueError` text in `BaleignoreMatcher.from_lines`
  so it stops naming `.baleignore` itself; let each caller prefix its
  source, as `build_pack_matcher` now does.
  **Why:** the source-attributed prefix is correct, but a `--exclude`
  refusal still ends "not supported in .baleignore at v0.1".
  **Scope hints:** `bin/bale` (board-99a's path this wave); pins in
  `tests/test_pack_guards.py`.
- **What:** an E2E pin for `bale handoff --verbose` naming a typo'd
  reading-plan path as `verbose: drop <path> (not tracked)`.
  **Why:** it is the case row 92 was written for. The code path is the
  one pinned here via the empty-directory entry, but the handoff surface
  itself is unpinned.
  **Scope hints:** `tests/test_verbose_thread.py` or a handoff suite;
  no source change expected.
