# Notes — 2026-10-04-log-hold-003

All five outcomes landed. Every changed path is inside the write
forecast, so nothing here needs admitting at apply. The full suite
passes in my tree, apart from seven tests that need files this request
doesn't carry (more at the end).

## Decisions to ratify

**1. The hold journals at log time; only the print waits.**
`WalkLogHold` replayed a held line through the real `log()` at
release, so the journal entry was written at release time. The native
hold works the other way. While held, `log()` journals the line (or
FORCE-queues it when no session log is open) when the line is logged,
and only the `print` waits for `release_log()`. That is exactly what an
unheld line gets, and the journal timestamp records when the event
happened, not when the walk ended. In the pack span these are the same
thing in practice, since everything is pre-sid and no log file opens
inside it. Shape: `hold_log()` / `release_log()` / `log_holding()`,
plus a `log_held()` context manager for callers whose span is a single
block. `cmd_pack`'s span crosses an `if`, so it pairs the calls itself
rather than re-indenting 80 lines that the queued
`choice-prompt-convergence` session will also touch. `fail()` calls
`release_log()` first. `atexit.register(release_log)` sits at module
level, so a held line can be delayed but never lost. The hold is one
level deep: a second `hold_log()` is a no-op.

**2. `WalkLogHold` is deleted, not thinned.** It had no other users,
and with `fail()` releasing natively, `cmd_pack`'s two
`walk_logs.fail(...)` calls become plain `fail(...)`. Nothing under
`bin/` assigns a `log` or `fail` attribute any more; a unit test and a
validation assertion both scan for it. One side effect: `cmd_pack`'s
own top-of-function `log` is now held too, where B's rebinding missed
it. `cmd_pack` logs nothing itself inside the span today, so nothing
moves.

**3. Display wrapping is opt-in, and today only pack's pre-walk lines
use it. Look closely here.** I first built it the way B framed it: on a
terminal, `log()` wraps every verb's lines. The full suite then lost 18
pty assertions across four suites (`test_hook_acceptance`,
`test_admission_prompts_e2e`, `test_readonly_pack`,
`test_supersession_pack`). Each one reads a fixed decline line whole
off a terminal, and those lines are ~120–150 columns. The sweep's
decline line ("close of <sid> declined (answered 'n'); …") is the one a
blind checkpoint for this session might plausibly grep in a pty
transcript, and a global wrap breaks it at "(answered / 'n')". So the
mechanism lives in bin/bale section 2 (`set_log_display_wrap`,
`wrap_log_line`, `log_display_width`), but it is off by default.
`cmd_pack` turns it on right after its context/dry-run branches and
restores it just before the wizard block. On the fully specified path
that is the same point in the pipeline, so its pre-exchange lines fit
too. Everything else, including the held lines replayed after the walk
and the sweep's decline lines, prints exactly as before. The
supersession exchange's lines are pre-walk lines ("any other line pack
prints before the walk's first question"), so they now wrap. Their four
pty pins in `test_supersession_pack.py` compare words in order
(`on_terminal`, over `harness.normalize`) instead of one whole line.
That is the only existing assertion I loosened.

What the wrap does: it applies only when stdout is a terminal. Width is
`$COLUMNS`, else the tty's own width, else 80, floored at 40, so it
adapts to a wider terminal; on an 80-column terminal it is 80.
Continuation lines hang 7 spaces, under the text after `[bale] `. Words
and hyphens never break, so sids, flags and paths stay whole, and a
token wider than the width runs long, like the wizard layer's
absolute-path exception. Piped output is byte-identical; a pty-free
test pins the 187-column gates line still printing whole when piped.
Under `--json`, `[bale]` lines go to stderr (json mode rebinds
`sys.stdout`), so they wrap when stderr is a terminal; the JSON line on
stdout is untouched. The journal always gets the line as logged, one
entry per `log()` call. A test pins that too. `fail()`'s error line is
not wrapped.

I left the lines' text alone: the gates line and the tree echo still
say what they said, so the journal and every pin of their wording are
unchanged.

**4. The sweep's y/N: a keyword only the sweep passes.**
`confirm_yn_decision(..., wrap=True)` lays the prompt out with
`layout_yn_prompt`. It prints every wrapped line but the last, then
calls `input()` with the last line, so the answer is still typed right
after `[Y/n] `. The text wraps at the width minus 4, which keeps a
typed `yes` inside 80. Words never break, and the suffix rides the last
wrapped line; at today's sid lengths it lands on a line of its own,
`  [Y/n] `. The answer is read by the same unchanged lines below, and
an in-process test checks 13 answers (Enter, y, Y, yes, YES, " yes ",
n, no, nope, maybe, yess, EOF, ^C) decide identically with `wrap=True`
and without, with exactly one `input()` call each. The piped decline
never reaches the prompt. **No other prompt's layout changed**: no
other caller passes the keyword, and a validation assertion holds the
count at one.

**5. Clipboard rider: `clipboard_command_reading(repo)` →
`ClipboardCommandReading(command, source, refusal)`.** It reads the
same bytes in the same order as `effective_clipboard_command`: project
file, global file, the deciding layer's value, then that file's
spelling. It returns any refusal as a value, with no `fail()`, no
print, and no journal entry. `effective_clipboard_command` stays fatal
for other callers as a three-line wrapper. To share one implementation
rather than restate messages, I split two things: the dict-level judging
out of `get_probe_clipboard_command` into `_probe_clipboard_value`, and
the two config loaders' parse into `read_config_file`. Both keep their
exact fail texts, and a test asserts the fatal message equals the
reading's refusal for each refusal class. `resolve_clipboard_command`
no longer captures stderr or catches `SystemExit`. Its unplanned-
exception fallback still goes through `_refusal_reason`, whose unit
test is unchanged. `_clipboard_source_or_none` and `bale_report`'s
`contextlib`/`io` imports had no remaining callers and are gone. Exit
codes are unchanged, and the "NOT copied" notice and its reason are
unchanged (the reason is the same text, one-lined). An end-to-end test
packs with a triple-quoted global key and checks the session log has
the notice and no `[bale] error:` entry. It fails on the unmodified
tree.

## Where to look on review

- `bin/bale` section 2: the hold and the wrap, about 150 lines,
  mostly comments.
- `cmd_pack`: the two `set_log_display_wrap` calls bracketing the
  pre-walk region, and `hold_log()` / `release_log()` where
  `WalkLogHold` was.
- The sweep prompt's look on an 80-column terminal, as the pty run
  shows it:

  ```
  Close open read-only session 2026-10-04-desk-001 as closed-read-only? A
    read-only session lands nothing, so no work is lost; its registry entry
    and .bale/sessions/ state are removed and a closure record is written.
    [Y/n]
  ```

## Validation

`validation.sh` runs a syntax pass, the exec-bit check, five
session-specific assertions, and ten scoped suites (about 90s). The
full suite is gated behind `--slow`. I ran the script twice. On the
unmodified tree all five assertions fail; with the change everything
passes. Every new test also fails on the unmodified tree, except two
that are deliberate no-change pins: piped lines staying whole, and the
`("clipboard",)` help entry, which already rendered cleanly. The full
suite (`--slow`, discover form, 1796 tests) passes in my tree except
the seven failures it also has on the unmodified tree. All seven need
files this request doesn't ship: `bale.toml` (test_include_group ×3),
`claude/changelog/` (test_changelog_record ×2), the ADR-0013 file
(test_doc_crossrefs), and a repo-root `README.md`
(test_global_doc_noun). Hence the full-suite claim is `predicted`, and
the scoped one is `observed`.

## Proposals

- **Display wrapping for every verb.**
  *What:* call `set_log_display_wrap(True)` once in `main()`, so every
  verb's `[bale]` lines fit the terminal. Then update the pty pins that
  read fixed decline lines whole: the hook, admission, and sweep
  decline lines in `test_hook_acceptance`, `test_admission_prompts_e2e`
  and `test_readonly_pack`. The `on_terminal` helper this session added
  to `test_supersession_pack` is the pattern; it belongs in
  `tests/harness.py` if a second suite adopts it.
  *Why:* the same 80-column friction exists on apply, retry, relay and
  status. I measured the cost: 18 assertions in 4 suites. Any blind
  checkpoint that greps a decline line off a pty would need the same
  tolerance.
  *Scope hints:* `bin/bale` `main()` plus those three suites. Rule
  first on whether checkpoint authors should be told that terminal
  transcripts wrap.
- **The other long y/N prompts.**
  *What:* pass `wrap=True` at the supersession, drift-admission and
  bare-apply prompts.
  *Why:* the supersession prompt is a pre-walk line in all but name,
  and it still runs long on an 80-column terminal. The keyword is
  layout-only by construction, but the operator's ruling covered only
  the sweep.
  *Scope hints:* one argument per call site, in `bale_pack` and
  `bale_apply`.
- **BALE.md true-up sentences** (BALE.md wasn't in this request):
  - Where BALE.md describes the goal-less walk's quiet span: "From
    the walk's first question through its README question, bale holds
    its `[bale]` lines (bin/bale's `hold_log`/`release_log`): each line
    is journaled when logged and printed after the README question, in
    order; a refusal prints the held lines before its error line."
  - In §7.7 (the tree-position echo) or wherever pack's pre-walk output
    is described: "On a terminal, the `[bale]` lines pack prints before
    the walk are word-wrapped to the terminal's width (80 on an
    80-column terminal), continuation lines indented under the text;
    piped output and the session log keep each line whole."
  - Where the read-only sweep's prompt is described: "On a terminal
    the sweep's y/N wraps to the terminal's width; Enter accepts, y or
    yes in any case accepts, any other answer declines without
    re-asking, EOF or ^C declines, and piped stdin declines without a
    prompt."
  - Where the paste-block copy's unreadable-key behavior is described:
    "An unreadable key skips the copy with one `NOT copied` notice
    naming the reason; it is not an error of the command and is not
    journaled as one."
- **Retire the FORCE-queue `__main__` reach-ins.**
  *What:* give bin/bale's logging section two small accessors for its
  FORCE queue: a count, and a drop-since-mark. Then have `bale_pack`'s
  `_pending_force_line_count` and `_drop_force_lines_queued_since` call
  them instead of reading and truncating `__main__._pending_log_lines`.
  *Why:* B called the rebinding "the second bale_pack reach into
  `__main__` state". With it gone, these two are the last, and the
  second one mutates bin/bale's state from outside.
  *Scope hints:* bin/bale section 2 and those two `bale_pack` helpers,
  a few lines each.
