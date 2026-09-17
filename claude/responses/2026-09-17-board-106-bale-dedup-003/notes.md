# Notes — 2026-09-17-board-106-bale-dedup-003

All seven changed paths are inside the forecast, so there is nothing to
admit at apply. `bin/bale_apply.py`, `bin/bale_report.py` and `bin/VERSION`
are untouched, and `tests/test_hold_retry_e2e.py` needed no edit. Five
things want your ratification; the first is a real deviation from the brief.

## To ratify

**1. Rider 5 is a `RawDescriptionHelpFormatter` subclass, not the plain class.**
The plain class stops wrapping descriptions altogether. Fourteen of the 17
subparser descriptions are written as one long string, so under it
`bale pack --help` would print its description as a single 646-character
line, and `apply`'s paragraphs as lines up to 875 characters (measured).
"Reflowing" those by hand would mean hard-coding line breaks into about
10 KB of prose that then no longer tracks terminal width.

`SubcommandHelpFormatter` (bin/bale, section 26) keeps the raw class's
contract for authored structure: blank-line paragraph breaks survive, and
a block whose lines are all indented is emitted verbatim. Prose inside a
paragraph is still filled exactly as `HelpFormatter` fills it. The result:
14 of 17 subcommand helps are byte-identical at every width (I diffed
widths 50, 80 and 132). Only `apply`, `retry` and `completion` change, and
only in whitespace. `completion --help` now shows `source <(bale completion
bash)` and the install line on their own lines, with blank lines around
them. The top-level parser keeps the default formatter.

If a blind checkpoint tests `formatter_class is argparse.RawDescriptionHelpFormatter`
it will fail, while `issubclass` passes. If you want the literal class, the
swap is one line, but the long-line problem above comes with it.

**2. Rider 1's mechanism: the resolver owns the check for verb callers.**
The desk's correction says all the not-found lines live in `bin/bale`.
`bale apply`'s post-resolution check, though, is in `bin/bale_apply.py`
(line 3763), which is frozen. `cmd_apply` imports `resolve_inbound_path`
from `bin/bale`, so the resolver now runs `is_file()` itself whenever a
verb is passed, and refuses through `fail_not_found`. That is how `apply`
gets the listing without its module changing.

This is equivalent for every existing caller. The first line is the old
`tarball not found: <resolved path>` byte for byte. The callers' own checks
ran immediately after resolution anyway, and are now unreachable for verb
callers but kept. Verb-less callers (`pack --readme-file`, `open`) still get
the unchecked path, and their refusals are unchanged; a test pins both with
a twin present. amend-checkpoint's two refusals route through
`fail_not_found` with no verb, byte-identical.

**3. Rider 3 changes one phrase on the amend surface.**
Delegating to `compose_hold_successors` makes the amend report's degrade
note the card's text: "substitute the held response's path below" becomes
"substitute the path below". That's unavoidable with `bale_report.py`
frozen, and it is the point of the rider (one composer). The composed
retry line and both log lines are unchanged; I checked all three in
process against the base.

If the composer ever stops returning a fixture fork shaped
`[amend line] + retry lines`, `compose_retry_successor` fails loudly rather
than guess. That fail fires after the amendment commit, and its message says
so.

**4. 105: pinned words-per-line, plus one new constant.**
I expected to derive the lines with `textwrap`, but no width reproduces
them: board 105 hand-wrapped the voice paragraph (line 1 runs to 70
columns, line 2 to 65). So `_opener_lines` cuts the constants at pinned
word counts, and any words past the counts become one final line, so a
reworded sentence reflows but never loses a word.

I also added `OPENER_EXAMINE_SENTENCE`, so every sentence in the block has
one copy in the file. My first set of counts was wrong, and the byte-hash
comparison caught it before anything shipped; `validation.sh` carries that
hash for both shapes.

**5. Rider 4 wording.** The session refusal now reads `invalid session exclude
pattern (this pack's --exclude flags or its wizard-collected excludes): …`.
`load_baleignore` keeps its file-path prefix, which is what names
`.baleignore` there. Change the parenthetical freely; the tests key on the
old marker plus `--exclude`.

## Where to look on review

- **`resolve_inbound_path` / `fail_not_found`.** Read the two early returns
  together. The search-miss branch passes the typed argument plus
  `search_paths`; the other branches pass the resolved path and no search
  block. Candidate scanning for an absolute path relies on
  `cwd / absolute == absolute` inside `near_name_candidates`; a test pins
  that the scan stays in the path's own directory.
- **Claims.** Three suites are claimed pass as *observed*:
  `test_pack_opener` 15, `test_pack_guards` 38 (2 skipped),
  `test_apply_preflight` 77 (6 skipped). Three are *predicted*, because
  `tests/test_per_sid_checkpoint.py` and `tests/test_handoff_fixture.py`
  weren't in the request, so those modules can't import here.

  I did what I could around the gap. The new handoff class passed with a
  stub fixture on a scratch path. The amend test's comparison logic ran
  against the real `compose_retry_successor` output in process. Every new
  test was also run against the base bytes: all the behavioral ones fail
  there and pass on the new tree. If one of the three predicted suites
  disagrees, the new code in it is `test_degraded_successor_is_the_card_composers_output`
  and `HandoffExistenceGateOneHomeTest`.
- **`validation.sh` invariants are relative, on purpose.** Bumpless-under is
  checked as "no `bin/VERSION`, `bale_apply.py` or `bale_report.py` in
  `changes[]`", not as a version string. 56+57 may land first and must not
  read as drift here.

  Help byte-identity is also computed, not pinned: each subparser is
  rendered twice in the same interpreter, once with the new formatter and
  once with `argparse.HelpFormatter`. argparse's own headings differ across
  3.10–3.13, so a pinned hash would break on your Python.

  A rehearsal of the script in a mode-stripped staging copy caught a bug
  in my own check: hyphen line breaks make word-list comparison lie. It
  now compares text with whitespace removed.

## Smaller things

- **The opener rule, honestly.** Turn one of this session ended at a
  tool-use limit, with a prose status and no block. It asked nothing, and
  CLAUDE.md §11.1 treats that as a pause, but it wasn't one of the four
  shapes. No light question blocks were emitted.
- **Stale version marker.** `from_lines`' sentence still says "at v0.1". I
  left the bytes alone beyond dropping "in .baleignore".

## Proposals

- **A home for CLI-help pins.**
  - *What:* move `SubcommandHelpLayoutTest` out of
    `tests/test_apply_preflight.py` into a `tests/test_cli_help.py`, which
    could also host the completion generator's pins.
  - *Why:* help layout has nothing to do with apply's pre-flight rows. It
    landed there only because the forecast named suites individually and
    the brief put new files out of bounds.
  - *Scope:* tests only; no ordering dependency.
- **An in-process loader for `bin/bale` in the harness.**
  - *What:* a `_load_cli()` beside `_load_module`, so functions that live
    only in `bin/bale` (`fail_not_found`, `SubcommandHelpFormatter._fill_text`,
    `compose_retry_successor`) can get unit tests.
  - *Why:* this session wanted exactly those unit tests and pinned
    everything end to end instead, rather than invent a loader in three
    test files. `validation.sh` shows `runpy.run_path("bin/bale",
    run_name=...)` works for pure functions.
  - *Scope:* `tests/harness.py`; any suite could adopt it afterward.
- **`compose_hold_successors`' docstring, when 56+57 releases
  `bale_report.py`.**
  - *What:* say that `compose_retry_successor` now delegates to this
    function, instead of "rendered on the degrade line in
    compose_retry_successor's shape".
  - *Why:* the docstring still describes two composers agreeing by shape,
    which stopped being true in this response.
  - *Scope:* one docstring; only after 56+57 applies.
