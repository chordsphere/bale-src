# notes.md — 2026-10-28-gitignore-already-ignored-001

The fix is small and lands where the brief hoped: one helper,
`ensure_bale_gitignored` in `bin/bale` section 7, keeps its name,
signature and both callers, and now asks git before it touches
anything. The question itself went into a new helper beside it,
`git_check_ignore(repo, path) -> (verdict, detail)`, with the slashed
query named once as `BALE_DIR_IGNORE_QUERY`. Verdict `True` carries the
rule `check-ignore -v` printed (`.git/info/exclude:7:.bale/`), so the
log line says where the ignore comes from; `None` carries the reason
git could not answer, so the caller logs that before it falls back to
the old text rule. `bin/bale_pack.py` changes in a comment only.

## The one thing to know before reading further

**I could not run the test suite in this session.** The request ships
`bin/bale` and `bin/bale_pack.py` but not the other twelve modules
`bin/bale` imports at module scope (`bale_config`, `bale_apply`,
`bale_report`, ...), so neither `bin/bale` nor any test that drives it
can start here. That was knowable only after opening the tree, and a
probe cannot carry twelve modules back through a paste, so I proceeded
under TARBALL.md §3.3 item 3 and did the next best things:

- The helper itself, extracted from the shipped `bin/bale` by AST with
  its own `run`, `git` and `log`, ran against real git repos (git
  2.43.0, sandbox HOME) on every branch: exclude file, tracked
  `.gitignore` with `.bale/`, bare `.bale` line, `core.excludesFile`,
  nothing ignores (create; append with the newline courtesy; second
  call then says already ignored), a listed-but-negated `.gitignore`,
  exit 128 (a non-repo), git missing from PATH, and an existing
  `.bale/` directory. 23 of 23 assertions held.
- The in-process class `GitCheckIgnoreUnitTest` in the new module ran
  for real through the harness's `_load_cli`, against the real
  `bin/bale` with name-only stubs standing in for the missing siblings
  (lab copy only; nothing of that ships). 8 of 8 passed, and the
  module imports under the bare, dotted and discovery forms.
- `validation.sh` ran here on the modified tree (sections 1 to 3 pass;
  4 and 5 fail only on `ModuleNotFoundError: bale_config`) and on the
  unmodified tree (every session assertion fails there, as §7.2 asks).

So the `unittest discover` claim and the two staged-pack claims are
`predicted`, not `observed`, and the manifest says so. `validation.sh`
runs the full suite in staging and additionally packs two throwaway
repos with the staged `bin/bale`, one per row, written independently
of the checkpoint. If a test fixture of mine is wrong, the HOLD block
will say which; the behavior itself is checked twice over.

## Facts relied on

From the brief's probe, each re-checked here where it could be:

- The git fact, re-verified with git 2.43.0: `git check-ignore -q
  .bale` exits 1 before the directory exists even when an ignore file
  holds `.bale/`; `git check-ignore -v -- .bale/` exits 0 and prints
  the rule, for a `.bale/` or a bare `.bale` pattern alike, whether or
  not the directory exists. With `-v`, a negated last match prints
  nothing and exits 1. `-v` and `-q` cannot be combined, so the helper
  uses `-v` and reads the exit code. The new in-process test
  `test_bare_bale_does_not_match_a_directory_pattern_before_it_exists`
  pins the fact so a future git that changes it shows up in the suite.
- The guard runs pre-sid in both callers, before the forecast gates
  (`bin/bale_pack.py` around line 6808, `bin/bale` cmd_handoff around
  line 4468); nothing before either call refuses on tree state.
- A session open writes `claude/telemetry/<sid>.json` on the tracked
  side (`_persist_open_provenance`; BALE.md §8.9 says the record lands
  untracked until the user's next commit). So "the tree is as clean
  after the pack as before" cannot mean an empty `git status
  --porcelain`; the tests and `validation.sh` assert that nothing about
  `.gitignore` appears in the status and that HEAD did not move. The
  checkpoint, per the brief, reads `.gitignore` and the commit, so this
  reading should agree with it.
- Changelog records live at `claude/changelog/<version>.json`
  (`schemas/changelog-record.schema.json`, CODE.md §8.5). Neither
  `tests/test_changelog_record.py` nor the 0.4.55 record shipped, so
  the 0.4.56 record follows the schema and the Python-side rules its
  description names (X.Y.Z version, ISO 8601 `at` with a UTC offset,
  repo-relative surface paths). It validated against the schema here
  with `jsonschema`, and `validation.sh` re-checks the core with the
  stdlib and the schema when `jsonschema` is present.

## Outside the forecast

- `claude/changelog/0.4.56.json` (created). Brief row 7 asks for the
  record; the forecast is `bin tests BALE.md
  claude/context/bale-internals.md` and the record's home is
  `claude/changelog/`. Declared in `forecast_departures` too. Admit it
  at apply.

## Decisions to ratify

- **A listed-but-negated `.gitignore` is left alone.** When git says
  "not ignored" but `.gitignore` already lists `.bale/` (so a later
  `!.bale/` or similar wins), the guard logs a note and returns False
  rather than append a second `.bale/` line, which would also commit
  `bale: ignore .bale/` on every pack. The old code wrote nothing
  there either (it found the line); the new code says why. If you
  would rather bale re-ignore it, that is a one-branch change.
- **A new test module** rather than more cases in
  `tests/test_pack_guards.py`. That file's docstring is about caps,
  excludes and the soft-breach prompt, and its gitignore cases are
  about the `--verbose` drop line, not this guard. The new
  `tests/test_gitignore_guard.py` holds the pack, handoff and
  in-process classes over one fixture base, and its docstring says
  what each row pins. The handoff row-2 case removes the pack's own
  `.gitignore` in a commit (after staging apply's telemetry leftover,
  while `.bale/` is still ignored) so that the handoff's guard is the
  one that writes and commits.
- **BALE.md beyond step 6.** Two other sentences stated the old rule
  (§6's "`.bale/` is gitignored" paragraph: "offers to add it on any
  first invocation in a repo that doesn't have the entry"; the "Beyond
  git, bale assumes" list). Both now follow step 6. Step 6 and that
  list also claimed a "single-line user confirmation" the code never
  had (the helper's docstring calls it a later enhancement); they now
  say "a logged note" and keep the confirmation as the later
  enhancement. Say so if you would rather the doc keep describing the
  intended behavior.
- **The callers' comments** were trued up (`bin/bale_pack.py`'s
  "Ensure .bale/ is in .gitignore" block, cmd_handoff's "must already
  be excluded" block), which is why `bin/bale_pack.py` appears in the
  change set at all.

## Where to look on review

- `bin/bale` section 7, the two new definitions and the rewritten
  helper. The fallback order: `True` returns early; `None` logs and
  then applies the text rule; `False` with the line already listed
  logs the note and returns; everything else appends as before.
- `tests/test_gitignore_guard.py::HandoffGitignoreGuardTest` for the
  fixture dance described above, since that is the part I could not
  run.
- `validation.sh` section 4: the two throwaway repos. It uses `env -i`
  with the real PATH, a sandbox HOME holding only a `.gitconfig`, and
  `BALE_INSTALL` pointed at a non-existent directory (as the harness
  does) so no global `bale.toml` hook engages during the staged pack.
  Wall time should be a few seconds plus the suite.
- The suite's wall time. The harness says the default discover run
  stays under two minutes; the new module adds nine subprocess E2E
  cases (each copies the install trees and runs one or two bale
  verbs). If the run now crosses the target, the fix is to `@slow`-gate
  the handoff class, which is the heaviest.

## What the command would have been

Brief row 8 asks me to name the command I ran. The run form the tree
documents is `python3 -m unittest discover -s tests` from the repo
root (`tests/harness.py`'s docstring; `tests/__init__.py` adds the
dotted form). That is what `validation.sh` runs. Here I ran
`python3 -m unittest tests.test_gitignore_guard.GitCheckIgnoreUnitTest
-v` against the stubbed lab copy (8 passed) and the AST-extracted
helper against real git (23 assertions).

## Proposals

### Record bale's ignore in `.git/info/exclude` by default

- **What.** When nothing ignores `.bale/`, write the line to
  `.git/info/exclude` instead of the repo's `.gitignore`, and drop the
  auto-commit and its dirty-tree branch.
- **Why.** The brief asked for a view only if the code's shape made one
  obvious, and it does: after this session the guard has one decision
  (ask git) and one write; the commit block that follows it exists only
  because the write is to a tracked file. Writing to the exclude file
  removes the commit, the "modified but not auto-committed" warning,
  the `bale: ignore .bale/` entries in every project's history, and
  the whole class of surprise this session fixed. The cost is the
  tracked `.gitignore`'s one advantage: a collaborator's fresh clone
  ignores `.bale/` before bale ever runs there. On the first pack in
  that clone bale would write the exclude line itself, so the window is
  "between clone and first pack", which only matters if someone runs
  `git add -A` with a `.bale/` present and no pack yet. The git-init
  walkthrough (`_write_initial_gitignore`) is a separate question: it
  writes a whole baked-in exclusion set for the project's benefit, and
  that one belongs in `.gitignore`.
- **Scope hints.** `ensure_bale_gitignored` and the two caller blocks;
  BALE.md §6, §7.1 step 6, §8.9's "gitignored by construction"
  sentence; `claude/context/bale-internals.md` section 7; the new test
  module's row-2 cases flip to assert the exclude file. The occupant's
  decision, as the brief says.

### Route the context pack's check-ignore through the new helper

- **What.** `bin/bale_pack.py` around line 6079 runs its own
  `git check-ignore -q` on the context tarball's path. It could call
  `git_check_ignore` (reached back from `__main__` like the other
  shared helpers) and name the source in its note.
- **Why.** Two spellings of one question in two files is the drift the
  brief's row 3 worried about for the guard; this one is harmless today
  but the same shape. Left alone here to keep `bale_pack.py` at a
  comment-only change.
- **Scope hints.** `bin/bale_pack.py` cmd_pack's `--context` tail;
  `tests/test_context_pack.py` already asserts the "not gitignored"
  note.

## Walkthrough

### What changed

- `bin/bale`, section 7 (".gitignore handling for the .bale/
  directory"): a constant `BALE_DIR_IGNORE_QUERY = ".bale/"`; a helper
  `git_check_ignore(repo, path)` that runs `git check-ignore -v --
  <path>` and returns `(True, "<source>:<line>:<pattern>")`,
  `(False, "")`, or `(None, "<why git could not answer>")`; and
  `ensure_bale_gitignored(repo)`, which now calls it first and writes
  `.gitignore` only on a `False` verdict (or on `None` when the file
  does not already list the line). The handoff caller's comment states
  the new rule.
- `bin/bale_pack.py`: the comment above the pack caller states the new
  rule. No code change.
- `tests/test_gitignore_guard.py`, new: pack row 1 from each source
  (`.git/info/exclude`, a tracked `.gitignore`, a `core.excludesFile`),
  pack row 2 on a clean and a dirty tree, handoff rows 1 and 2, and
  in-process cases for the verdict shapes, the cannot-answer fallback,
  the negation note and the trailing-slash fact.
- `claude/context/bale-internals.md` section 7 line and `BALE.md`
  (§6 paragraph, "Beyond git" list, §7.1 step 6): the new rule in a
  sentence each.
- `bin/VERSION` 0.4.56 and `claude/changelog/0.4.56.json`.

### Why

On its first pack in a clone, bale decided whether `.bale/` was
ignored by reading the repo's `.gitignore`. A clone whose owner had put
`.bale/` in `.git/info/exclude` (the office's `projects add --prepare`
does this) therefore got a tracked `.gitignore` written and committed
as `bale: ignore .bale/`, which is a change to a file that belongs to
the project's audience, made for bale's own convenience. Git is the
only party that knows whether a path is ignored, since the answer can
come from any of several files; so bale now asks git, and writes only
when the answer is no.

### How to explain each piece

- `git_check_ignore`: "ask git, read the exit code, keep the rule it
  names." 0 is ignored, 1 is not, anything else is "could not answer".
  The trailing slash on the query is because a directory-only pattern
  does not match a bare name that does not exist yet, and on a first
  pack `.bale/` does not exist.
- `ensure_bale_gitignored`: "same name, same callers, one new question
  at the top." Already ignored: one log line naming the source, no
  write, no commit. Not ignored: the old append, then the callers'
  unchanged commit block. Git mute: log it, decide from the text, as
  before.
- The tests: one case per row of the outcome contract, each in a fresh
  repo under a sandbox HOME so the machine's global excludes cannot
  decide a verdict.
- The docs: three sentences that said "bale appends when `.gitignore`
  lacks the line" now say "bale asks git and appends when nothing
  ignores it."

### Questions a reviewer will ask

- *Why not `git check-ignore -q`, which bale already uses for context
  packs?* `-q` suppresses the output that names the source, and the
  brief welcomed naming it; `-q` and `-v` cannot be combined. The exit
  code is the same either way.
- *Why `-- .bale/` and not `.bale`?* The directory does not exist on a
  first pack, and a directory-only pattern does not match a bare name
  that is not a directory. Verified with git 2.43.0 and pinned by a
  test.
- *What happens on a machine without git?* `run` raises
  `FileNotFoundError`; the helper returns `None` with "git not found on
  PATH"; the guard logs "could not ask git whether .bale/ is ignored"
  and decides from the `.gitignore` text as before. (In practice bale
  has already refused earlier: `repo_root` fails without git.)
- *Why does `.gitignore` stay untouched when it lists `.bale/` but git
  says not ignored?* A later negation line means the project chose to
  un-ignore it. Appending again would also commit on every pack. Bale
  logs a note and leaves it.
- *Does the context pack path change?* No; it never edited `.gitignore`
  and already asked git.
- *Why is there a `claude/changelog/0.4.56.json` outside the forecast?*
  Every landed session bumps `bin/VERSION` and writes its record there;
  the brief said to ship it and enumerate it.

### A hand test

1. `git clone <any repo> /tmp/t && cd /tmp/t`, then
   `printf '.bale/\n' >> .git/info/exclude`. Confirm with
   `git check-ignore -v -- .bale/` (prints the exclude rule, exits 0)
   and `git log -1 --format=%s` (note the subject).
2. `bale pack "hand test" --slug hand --include README.md --no-readme`
   (or any tracked file). Among the log lines expect
   `.bale/ is already ignored (.git/info/exclude:N:.bale/); leaving
   .gitignore alone`.
3. `git log -1 --format=%s`: the same subject as before, not
   `bale: ignore .bale/`. `git status --porcelain`: no `.gitignore`
   line (the session's telemetry record under `claude/` is the one
   expected untracked path). `ls .gitignore` fails if the repo had
   none, or `git diff --stat .gitignore` is empty if it had one.
4. For the other row, repeat in a second clone without the exclude
   line: `.gitignore` gains `.bale/` and `git log -1 --format=%s` reads
   `bale: ignore .bale/`.

## Delivery

- to: the occupant

### Commit

bale: ask git before writing .bale/ to .gitignore

On a first pack or handoff in a clone, the .bale/ gitignore guard
decided from the repo's .gitignore text alone, so a clone that already
ignored .bale/ through .git/info/exclude got a tracked .gitignore
written and committed as "bale: ignore .bale/". A tracked .gitignore
belongs to the project's audience, not to bale.

The guard now asks git with "git check-ignore -v -- .bale/" (the
trailing slash matters: a directory-only pattern does not match a
bare .bale that does not exist yet). When .bale/ is already ignored
from any source (a tracked .gitignore, .git/info/exclude, a
core.excludesFile) nothing is written and nothing is committed, and
one log line names the source. When nothing ignores it, behavior is
unchanged: .bale/ is appended to .gitignore and committed on a clean
tree. When git cannot answer, the guard logs that and the .gitignore
text decides as before. The fix lives in ensure_bale_gitignored, the
one helper pack and handoff share; a new git_check_ignore helper
beside it carries the question.

tests/test_gitignore_guard.py pins each case on the pack path, both
on the handoff path, and the fallback in process. BALE.md and
bale-internals.md state the new rule. bin/VERSION goes to 0.4.56 with
its changelog record.

### Review

bale 0.4.56: leave .gitignore alone when git already ignores .bale/

What to look at: bin/bale section 7, where the guard gained
git_check_ignore and the early return on an already-ignored verdict.
Both callers (bale pack in bin/bale_pack.py, bale handoff in bin/bale)
are unchanged apart from their comments, so the two cannot drift.

What to try by hand: a fresh clone with .bale/ in .git/info/exclude,
then a first pack. git log should show no "bale: ignore .bale/"
commit and git status should show no .gitignore. In a clone with
nothing ignoring .bale/, the pack should still add the line and
commit it.

Deliberately untouched: whether bale should record its ignore in
.git/info/exclude by default instead of a tracked .gitignore. That is
a separate decision with every bale project as its audience; the
response notes carry a proposal and nothing more. The context pack
path, which never edited .gitignore, is also unchanged.

## Structure

- title: bale leaves .gitignore alone when git already ignores .bale/
- size: small
- goal: On its first pack or handoff in a clone, bale asks git whether .bale/ is already ignored from any source and appends and commits the .bale/ line only when nothing ignores it

## Handbook

### bale-src

#### Front sheet

bale-src is the occupant's own CLI for the request and response
tarball workflow: bale pack builds a request, bale apply lands a
response through staging and validation, bale handoff repackages a
bailout. It ships one release per landed session (bin/VERSION plus a
record in claude/changelog/). At 0.4.56 the first-pack gitignore guard
asks git before writing, so a clone prepared with .bale/ in
.git/info/exclude keeps its tracked .gitignore untouched.

- 2026-10-28: `git check-ignore -q .bale` exits 1 before the directory exists even when an ignore file holds `.bale/`; ask with the trailing slash, `git check-ignore -v -- .bale/`, or with a path inside the directory (git 2.43.0) (2026-10-28-gitignore-already-ignored-001)
- 2026-10-28: with `-v`, a negated last match prints nothing and exits 1; `-v` and `-q` cannot be combined, so a caller that wants the source reads the exit code of `-v` (2026-10-28-gitignore-already-ignored-001)
- 2026-10-28: a session open writes `claude/telemetry/<sid>.json` on the tracked side, untracked until the next commit, so `git status --porcelain` is never empty right after a first pack; assert on `.gitignore` and HEAD instead (2026-10-28-gitignore-already-ignored-001)
- 2026-10-28: `bin/bale` imports twelve siblings at module scope (`bale_config`, `bale_validate`, `bale_rollback`, `bale_report`, `bale_stats`, `bale_pack`, `bale_apply`, `bale_open`, `bale_relay` and the modules they pull in); a request that ships only part of `bin/` cannot run any bale verb or the test suite, so a session asked to run the suite needs all of `bin/` in its includes (2026-10-28-gitignore-already-ignored-001)
- 2026-10-28: changelog records live at `claude/changelog/<version>.json` and every landed session bumps `bin/VERSION` and writes one; the directory is outside a forecast of `bin tests BALE.md claude/context/bale-internals.md`, so such a session ships the record as enumerated drift (2026-10-28-gitignore-already-ignored-001)
- 2026-10-28: `tests/harness.py`'s `_load_cli` loads `bin/bale` in process; a function that stays inside `bin/bale` (calls only its own `run`, `git`, `log`) is unit-testable there with `run` patched, which is how the git-cannot-answer branch of the gitignore guard is pinned (2026-10-28-gitignore-already-ignored-001)
- 2026-10-28: the `.bale/` gitignore guard runs pre-sid in both `bale pack` (bin/bale_pack.py, before the walk) and `bale handoff` (bin/bale cmd_handoff, before the tarball is opened), before the forecast gates; nothing earlier in either verb refuses on tree state (2026-10-28-gitignore-already-ignored-001)
- 2026-10-28: the test suite's documented run form is `python3 -m unittest discover -s tests` from the repo root; `BALE_TEST_SLOW=1` opens the generation-heavy cases (2026-10-28-gitignore-already-ignored-001)
