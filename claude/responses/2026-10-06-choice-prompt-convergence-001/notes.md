# notes — 2026-10-06-choice-prompt-convergence-001

Both halves of the goal landed. The pack walk's shape question (all
three forms) and its checkpoint picker now draw their rows and ask
through `bale_wizard`'s choice primitive. `bale config init`'s
`.baleignore` suggestions now count only files that pack's own filter
chain would ship. Every path I touched is inside the write forecast, so
there are no departures to admit.

## The tree I built on

The brief expected two sessions to land before this one. Both are in
the bytes you shipped:

- **log-hold.** `bin/bale` has the native hold (`log_holding`), and
  `WalkLogHold` is gone.
- **clipboard-key-rename.** `bale_config` walks `[clipboard] command`.

Every `base_files` sha256 matched what I unpacked. The brief's
section 3 described the shape question, the picker, `ask_choice`, and
the suggestion filter, and all four matched the code. So I acted on the
carried proposals as written (constraint 3).

## Decisions to ratify

1. **The layer grew options, not a sibling primitive.**
   - `Alternative` gains `key` (lettered rows: `[c] code`) and `enter`
     (the aside says "Enter").
   - `ask_choice` gains:
     - `letters`: names the letters on the prompt and judges nothing,
       so the shape question keeps its own answer set and lowercasing.
     - `show_help=None`: `?` is an ordinary answer and the prompt offers
       no `? help`.
     - `noun` / `typed`: the words in the warning.
     - `number`: what counts as a number.
     - `out_of_range_ok`: the picker's literal-file exception.
   - Every default is config init's current behavior. `validation.sh`
     pins that with a sha256 over a full in-process config init walk:
     every project key with alternatives, answered with `?`,
     out-of-range numbers, in-range numbers, a list pick, `x`, `-` and
     Enter, plus the `.baleignore` step. The digest was computed on the
     packed tree and matches the new one. I also checked that a
     one-character change to the layer's warning moves the digest.
   - Outcome 4 (C's out-of-range note): config init keeps C's rule
     exactly (`out_of_range_ok` defaults to None). The picker passes
     `lambda e: (cwd / e).is_file()`, which is today's rule.

2. **What the picker's screen now says.** These are presentation
   changes only. No answer means anything different.
   - The prompt was `1-2, a path, or Enter = none > `. It is now
     `Enter = none · 1-2 picks > `, in config init's grammar with no
     `? help`. The notice line just above it still says a typed path
     resolves like `--readme-file`.
   - The warning was `… type a path, or press Enter for none.` It is
     now `… type a path, or press Enter.` (the layer's wording).
   - Each candidate's detail line is now the layer's aside, in
     parentheses: `(modified … UTC, sha256 …)`.
   - With no candidates there is nothing to pick, so that prompt is
     unchanged: `a path, or Enter = none > `.

3. **The picker still reads digits the way it did.** Today's test is
   `raw.isdigit()` then `int(raw)`, so a Unicode decimal digit such as
   `٢` picks candidate 2. I kept that (`picker_number`) rather than
   adopting the layer's ASCII-only `pick_number`, because the
   constraint is every answer.
   - One thing did change. `²` passes `isdigit()` but `int()` cannot
     read it, so the old picker died on an uncaught `ValueError`. It is
     now an ordinary path answer. The new
     `test_other_answers_are_paths` errors on the packed code for
     exactly this reason, which is how I confirmed it.

4. **`?` at the shape question.** It used to re-ask with "Type c, d, …".
   It now shows the item's help and asks again. I wrote the help text
   myself: one paragraph on the work class, one on read-only, and an
   answers line.
   - Nothing that ships defines `contract-doc`, so the help names it
     without explaining it.
   - The help says telemetry and the trust ledger aggregate by work
     class, which is TARBALL.md §3.4's own wording.
   - Digits re-ask with the old hint. Lettered rows offer no numbers,
     so `1` still does not pick the first row.

5. **One filter chain.** I moved walk_for_pack's per-path chain into
   `bale_pack.pack_drop_reason`, and walk_for_pack now calls it. The
   order, the `--verbose` trail's words, and the loud checkpoint and
   bundle lines are unchanged. `bale_config._pack_drops` calls the
   same function. I chose this over calling `walk_for_pack` from the
   wizard because that function logs the checkpoint drop loudly and
   wants caps. C's lazy posture is kept: if `pack_drop_reason` or
   `checkpoint_exclusion_basis` moves, the suggestions fall back to the
   baked-in directories (more files counted, never fewer).

6. **What now stops a file from counting toward a suggestion.**
   - The brief's four drops: baked-in directories, secret patterns and
     secret paths (a token-bearing `.npmrc` too), the configured
     checkpoint's exclusion basis, and patterns the `.baleignore` keeps.
   - Planner bundles. The brief's list didn't name them, but they are
     in pack's chain, and the goal says "only what pack's filter chain
     would ship".
   - Paths git lists that are not regular files.

7. **Three edge rulings in the suggestions.**
   - The checkpoint base is read from the project file without
     `fail()` (`_configured_checkpoint_basis`), so a malformed config
     never ends config init. In that case the checkpoint files are
     counted, as before this session.
   - A kept `.baleignore` line that pack cannot parse (a negation the
     phase-1 walk kept) skips the suggestions with the reason. Pack
     would refuse that file outright, so the counts would be
     meaningless.
   - The matcher is bin/bale's `BaleignoreMatcher`, reached lazily
     through `__main__` like every other bin/bale helper. Without it
     (an in-process caller that didn't provide one), kept patterns are
     not applied but are still never re-offered.

## Places to look closely

- `walk_for_pack`'s loop is a refactor of the filter chain every pack
  runs. `PackDropReasonTest` pins each reason in chain order and checks
  that the walk ships exactly what the predicate lets through, with the
  trail words intact. The `--slow` neighbors (`test_pack_guards`,
  `test_context_pack`, `test_verbose_thread`, and others) passed on my
  run.
- `_configured_checkpoint_basis` is a second reader of
  `[validation] base`. It deliberately skips `get_validation_base`'s
  refusals. It only diverges from pack for configs that pack refuses.
- `CheckpointPickerAnswersTest` patches `sys.modules["bale_config"]` at
  setUp, not the module object it imported. When the suites run
  together, `test_wizard_ui` re-registers `bale_config`. I hit this,
  and the setUp comment says why.
- The picker's in-process table stands in for `merged_config`, the
  Enter outcome, and path resolution. The real path is pinned by the
  new pty case in `test_checkpoint_file_flag`: `?` misses and re-asks,
  and `7` commits `./7`.

## Validation

- Default `validation.sh` takes about a minute serially: syntax, three
  assertions, and the five suites that pin these screens.
  - The config init digest is a preservation pin, so it passes on both
    trees by design.
  - The `format_checkpoint_candidates` assertion fails on the packed
    tree, as it should.
- `--slow` adds the pty-heavy pack suites. I ran them, and the whole
  test directory, before shipping. The only red I saw was my own: a
  `bin/__pycache__` that my scratch rendering left in the working
  copy, which the harness then copied into a test install. I removed
  it and nothing ships it.

## Proposals

- **BALE.md true-up (out of scope here).**
  - *What:* §7.3's description of the session-shape exchange and the
    checkpoint picker should say that both draw config init's
    alternatives. The shape rows are lettered (`[c] code` … `[x] mixed
    (Enter)`, `[r] read-only`), and the prompt offers `? help`, which
    shows the item's description. The picker's numbered candidates and
    prompt (`Enter = none · 1-N picks >`) offer no help, because `?` is
    a path there. Wherever BALE.md describes `bale config init`'s
    `.baleignore` suggestions, it should say they count only files
    pack's filter chain would ship. That means not secrets, not the
    configured checkpoint's subtree, not planner bundles, and not
    files a kept pattern already matches.
  - *Why:* the prose would otherwise describe the hand-built rows and
    the all-files count this session replaced.
  - *Scope hints:* `BALE.md` §7.3, and the §6.4 or wizard passage on
    `.baleignore`.
- **Drop two of the picker's three exceptions.** As the brief asked, I
  kept all three.
  - *What:* make the picker read numbers with the layer's ASCII
    `pick_number` and drop the `number` option. Also consider dropping
    the cwd literal-file rule, and with it `out_of_range_ok`. Keep `?`
    as a path, on B's ratified reasoning.
  - *Why:* the Unicode-digit pick is an accident of `str.isdigit`, not
    a design. The literal-file rule only serves a checkpoint saved
    under a bare number in cwd, beside a list that already offers
    numbers, and the file stays reachable as `./7`. Dropping both
    would make the picker's number rule exactly config init's.
  - *Scope hints:* `bin/bale_pack.py` (`picker_number`,
    `_wizard_input_checkpoint_file`), `bin/bale_wizard.py`
    (`ask_choice`), and the picker tables in `test_pack_wizard_ui`.
- **PackWalk as a `bale_wizard.Walk` configuration** (B's second
  addition, deferred).
  - *What:* give `Walk` a shrinkable plan (`drop`) and plain-word
    section headings, then make PackWalk a configuration of it.
  - *Why:* the choice move did not need it. Today the only differences
    are those two features plus PackWalk's abort-on-EOF `ask` and
    `choose`, which would become a Walk option too.
  - *Scope hints:* `bin/bale_wizard.py`, `bin/bale_pack.py`, and
    `PackWalkTest`.
- **Config init's `.baleignore` add prompt.**
  - *What:* move its numbered picks onto `ask_choice` (`noun=
    "suggestion"`, `typed="a pattern"`).
  - *Why:* it is the last hand-built numbered choice in either wizard.
    It still runs its own "no suggestion N" loop.
  - *Scope hints:* it would change that screen's prompt text, which
    this session's constraint froze, so it needs a ruling first.
