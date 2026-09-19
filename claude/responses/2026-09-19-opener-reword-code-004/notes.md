# Notes — 2026-09-19-opener-reword-code-004

All three Parts landed inside the forecast. No path outside it, no
`bin/bale` edit (handoff stamps `readme: null` through the shared
builder's default, as the brief expected), and it stayed bumpless
(`bin/VERSION` still 0.4.36, no changelog record).

This session's turn was split by a tool-use pause mid-build. That was
a pause, not a compaction: context stayed intact, and every hash and
claim here was recomputed after the pause.

## Decisions to ratify

These are mechanism calls where the brief left the how to me, or where
I deviated a little.

- **Wrapping moved from pinned words-per-line to `textwrap`.** It
  wraps at 70 columns with `break_on_hyphens=False` and
  `break_long_words=False`.
  - Board 106's fixed layout existed so the old bytes wouldn't move.
    The reword moves them anyway, so the layout constants went with
    the sentences they described.
  - The authoring session's `stdlib-only` warning is honored and
    pinned: the unit test puts a hyphenated word at the wrap boundary
    and checks it moves whole to the next line.
- **Opener paragraph grouping.**
  - Authority, reading and tools form one wrapped paragraph after the
    goal line.
  - `Packed at` and the clock sentence are then one line each.
  - Ask and deliverable form the closing paragraph.
  - Read the rendered variants in `tests/test_pack_opener.py`'s
    expectations, or run pack once, if you want to judge it by eye.
- **Scaffold strip is keyed on the comment's marker, not an exact
  match.**
  - Any HTML comment opening with `This README is OPTIONAL` is removed
    whole, even if the packer edited inside it.
  - A comment of the packer's own ships untouched.
  - An exact-bytes match would have let a lightly edited comment ship,
    which is the failure the brief was closing.
  - A pin keeps the marker and the scaffold from drifting apart.
- **The strip applies to editor output only.**
  - That covers `--edit`, including when it's seeded from
    `--readme-file`, and the wizard's y.
  - `--readme-file` alone still ships the planner's file verbatim, as
    it did before; the brief scoped Part 2 to the editor paths.
- **Scaffold-only buffer means no README (the desk's preference).**
  - This didn't fight the no-readme guard.
    - On the wizard path, a scaffold-only save is exempt like an `n`.
    - On `--edit`, which requires a TTY, it lands on the TTY-warning
      branch, the same as an emptied buffer does today.
  - I reworded the guard's log line from "declined at the wizard
    prompt" to "declined at the wizard prompt, or the editor buffer
    held no prose", since both now land there.
  - Nothing pinned the old text.
  - "Untouched" means the buffer holds only the `# <goal>` heading
    line. Edit the heading and it counts as prose and ships.
- **`README.md` is now written with `write_bytes`.** It was written
  with `write_text` before.
  - The bytes are hashed once and written once, so the manifest stamp
    and the shipped file can't disagree.
  - It also removes a latent mismatch: `write_text` translates
    newlines on Windows while the echo hashed untranslated text. That
    never mattered on WSL, but it's gone.
- **Defense-in-depth stamp check in `build_request_tarball`.**
  - A README with no stamp, a stamp with no README, or a sha
    disagreement raises before the tarball exists.
  - A manifest with no `readme` key at all is not checked. That keeps
    `test_craft_response.py`'s injection driver working, since it
    calls the builder with a one-key manifest.
- **One helper, `shipped_readme_text`, defines the shipped bytes.**
  The tarball write, the manifest stamp and the `readme sha256` echo
  all use it, instead of repeating the trailing-newline normalization
  in two places.
- **Schema pins `path` with a one-member enum and `sha256` with
  `minLength: 64`.** bale's validator subset has no `const` and no
  `maxLength`, so this is the tightest shape it can express. The
  description cites only TARBALL.md §3.1 and `bale pack`/`bale
  handoff`, and carries no version number (bumpless).

## Places to look closely

- `session_opener_block` and the `opener_has_readme` line just above
  the report. Both surfaces read that one value; the E2E pins the
  human and `--json` blocks byte-identical once the sid and pack
  instant are normalized.
- The read-only identity two-liner runs 73 columns with a full sid.
  It already did, it's unchanged, and it's outside the wrapped
  paragraphs. My first draft of the width pin caught it, and I scoped
  the pin back to the lines after the goal line, as board 106 had it.

## Test run, for calibration

- **Full `unittest discover` here:** 1319 tests, 1317 pass, 48
  slow-skipped.
- **The two failures** are `test_changelog_record`'s corpus and
  current-version tests.
  - They fail identically on the untouched request tree.
  - The cause is that `claude/changelog/` wasn't shipped in the
    request, so it's environmental and not a bump forced by this
    change.
  - In your repo they should pass. That's why the `--slow`
    full-discovery claim is `pass` with `claim_basis: predicted`.
- **Under `BALE_TEST_SLOW=1`**, the pack-adjacent slow suites were
  green: pack_guards, checkpoint_provenance, per_sid_checkpoint,
  release_packaging, escalation_schemas, auto_sweep and base_drift.
- **Mutation check:** disabling the strip turns 8 of the new scaffold
  pins red, including all three pty E2Es.

## For the sibling doc session

These are the global-doc sentences this half's changes make stale.
They're proposed, not made, since `docs/` is out of scope here.

- **`CLAUDE.md` META "Reading order" item 3** says "the session prompt
  and any project docs". The opener and the manifest's `readme` key
  now name `README.md` as the brief, so the reading order can name it.
- **`TARBALL.md` §3.2's manifest field list** has no `readme` entry.
  The wire shape is in `schemas/request-manifest.schema.json`'s
  description, which cites §3.1 for the file's placement.
- **`TARBALL.md`'s README guidance** still says most sessions skip the
  README. The opener now tells the worker to read it whenever it ships.
- **`tests/test_doc_crossrefs.py` line 166** has a comment saying
  `EVERY_TURN_SENTENCE` moves "in step with the opener's
  OPENER_SHAPE_SENTENCE". That constant is retired: the opener no
  longer carries the shape rule and states the ask as its own
  sentence. The doc pin itself is unaffected; only the comment's
  cross-reference dangles.
- **The planner closing's contract** could get a sentence in
  `PLANNER.md` or `CLAUDE.md` §3: a read-only session owes an answer
  plus, on request, crafter bundles, and never a response tarball.
  That's the doc half of the "what each session mode owes back" goal.

## Proposals

- **What:** Let `tools/response_lint.py` warn when a request's
  `readme` key is non-null but the response's `feedback.self_reported
  .docs_read` doesn't list `README.md`.
  - **Why:** The key exists so a worker learns a brief exists. The
    specimen that motivated this session never opened the README, and
    the lint could make that visible in telemetry.
  - **Scope hints:** Touches `tools/`, which is out of scope here, and
    only makes sense after this lands and requests carry the key.
