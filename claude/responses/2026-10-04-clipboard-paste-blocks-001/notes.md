# Notes — 2026-10-04-clipboard-paste-blocks-001

Session D is done. With a clipboard command configured, every
operator-side paste block bale prints is copied automatically, the
probe copies through the installed bale, and `bale status` has the
row. With nothing configured, nothing changes: no copy, no new line,
and no clipboard program is detected.

## What lands on the clipboard, per paste point

| Paste point | Copied text | Where it's wired |
|---|---|---|
| `bale pack` session opener (human and `--json`) | the lines strictly between the scissor lines, LF-joined, one trailing LF | `bale_pack.cmd_pack`, after the report prints |
| `bale open`, desk one | the same, through the replayed pack | (cmd_pack) |
| `bale open`, second desk | that desk's own opener, desk paragraph included | `bale_open.open_second_desk` |
| `bale relay` ingest and no-file re-emit | the block exactly as emitted, BEGIN through END | `bale_relay`, both emit sites |
| `bale apply` / `bale retry` HOLD | the block the card names under `send first:`; the notice names the other block and says it stayed printed | `bale_apply`, after both blocks print |
| `bale apply` / `bale retry` PASS | the APPLIED relay block, BEGIN through END | `bale_apply`, before the `[PASS]` banner |
| probe script | the PROBE BEGIN/END block, piped into `bale clipboard` | `tools/craft_response.py` scaffold tail |

Every site calls one helper, `bale_report.copy_paste_block`. It reads
the command through `effective_clipboard_command` for the repo the
command runs in. If a command comes back, it runs it with the block on
stdin, sends the command's stdout to /dev/null, stops it after 10s,
and prints one `[bale] clipboard: …` line on stderr. It never raises
and never changes an exit code. When the accessor refuses (triple
quotes, dotted key, forbidden content, or malformed TOML), the reason
goes into that notice instead of ending the command.
`resolve_clipboard_command` captures the `[bale] error:` line `fail()`
prints, so stderr doesn't show it as an error of the command. `fail()`
still journals that line into an open session log. That is an honest
record of what bale read, but you'll see it in the log above the
"NOT copied" notice.

## Decisions to ratify

- **Piped and `--json` runs copy too** (the brief's flagged call). The
  key is an explicit per-machine opt-in. Gating on a tty would make
  `bale pack` and `bale pack | less` behave differently with no line
  saying why, which is the silent-skip class. If a machine context
  doesn't want copies, it shouldn't set the key, or the project can
  suppress it with `""`.
- **How the probe asks bale: a new verb, `bale clipboard`.** It reads
  stdin and copies through the same helper. Exit 0 means copied. Exit 1
  means not copied, with a stderr line saying why. Exit 2 means a
  terminal stdin. I chose "bale runs the copy" over "bale prints the
  command and the script runs it" so the probe and the other paste
  points share one runner, one timeout and one notice vocabulary. The
  script trusts 0 and 1. Any other exit means "this bale has no such
  verb" (argparse exits 2 on an older bale), and the script says so.
- **The request's project key still bakes in, but only as a fallback.**
  If the crafter can read `[probe] clipboard_command` at craft time,
  the scaffold's `clip_fallback` tees into it. Otherwise `clip_fallback`
  prints remedy text naming `bale config init --global`. `clip_fallback`
  runs only when bale is not on PATH or predates the verb. When bale
  answers 0 or 1, the script never second-guesses it, because bale saw
  the machine's real config (a suppress, an unreadable key, the global
  value). The request's key is the project layer, which also wins when
  bale answers, so the fallback never contradicts bale.
- **No "configure a clipboard" nudge on pack, relay or apply when the
  key is unset** (outcome 5 left this to me). Those commands stay
  exactly as they were for anyone who never opted in. The nudge shows
  up where someone actually wanted a copy: `bale clipboard` (and so
  the probe), the probe's no-bale remedy, and the status row.
- **The helper lives in `bale_report.py`**, beside the stream-discipline
  helpers it has to respect. A new `bin/` sibling would have pulled
  `scripts/build.sh`'s RELEASE_FILES and the upgrade member list out
  of the forecast.
- **The status row is labelled `probe clipboard`**, following the
  rider's wording and the key's current section. Its values: `pbcopy
  (global layer) — every paste block is copied` / `suppressed here
  (…)` / `unset — …; bale config init --global sets one…` /
  `UNREADABLE — nothing is copied until it is fixed: <reason>`. Status
  still exits 0 in every case.
- **Every copied text ends in one LF.** For the opener this is a choice;
  the sentinel blocks already end that way when printed. It matches
  what the old probe tee put on the clipboard.

## Edits outside the strict letter of the forecast notes

- `bin/bale_config.py` was forecast as "help text only". Besides the
  `?` description (C's two tense changes, now present tense), I also
  rewrote the `PROBE_VALUES` comment paragraph that said "Until then a
  global value configures bale-side readers only". It became false
  this session, and a stale comment is a bug. No code changed in that
  file.
- `config init`'s description in `bin/bale` still listed `[probe]` among
  the project-layer-only sections. Session C made it both-layer, and
  `_PROJECT_ONLY_SECTIONS` actually lists `[layout]`, which the
  sentence omitted. I fixed the list while adding E's proposal (the
  review gate and `?`) and the numbered alternatives.

## Forecast departure (admit at apply)

- `tests/test_clipboard_paste_blocks.py` (new). The copy at every
  paste point, the HOLD send-first choice, exit and stdout invariance,
  no detection when unset, the status row, the verb's exit codes, and
  the probe through a real installed bale are all new behavior with no
  existing suite. Tests ship with code. It has 35 tests, about 20s, and
  imports `_OpenVerbBase` and `PerSidFixture`. Both are test-less bases,
  so nothing re-runs.

No existing suite outside the forecast needed an edit. `test_relay_verb`,
`test_pack_opener`, `test_apply_preflight`, `test_hold_retry_e2e`,
`test_open_verb`, `test_cli_help` and the doc-pin suites pass unchanged.

## Validation and what I could and couldn't observe

- I ran the full discover on this request's `context/` tree: 1778
  tests (1739 before). There are six failures, and the untouched
  baseline has exactly the same six. They are context gaps, not
  regressions: no `claude/changelog/`, no `claude/context/adr/`, and no
  repo-root `bale.toml` shipped (`test_changelog_record`,
  `test_doc_crossrefs`' ADR-0013 pin, `test_include_group`'s
  this-repo trio). That's why I claim `unit tests: touched suites` and
  the `--slow` discover as predicted rather than observed. The
  touched-suites run includes `test_doc_crossrefs`, which can only
  pass where the ADRs exist.
- I ran `validation.sh` twice in a simulated staging tree, once with
  the change and once without. With the change, it took 74s (106s with
  another suite running beside it) and everything passed except that one ADR pin. On the old tree, every
  session assertion fails except `unset key copies nothing with
  clipboard programs on PATH`. That one is a guard on a constraint,
  not a change test, and it's meant to hold before and after.
- The install-side `validate.sh` passes 94/94, and `scripts/build.sh
  --skip-verify` builds.
- I checked the runner against forking selection owners (xclip and
  wl-copy keep the stderr pipe open; bale returns in about 0.2s), a
  hung command (stopped at 10s, reported), and a command that never
  reads 4MB of stdin (no deadlock). All three have units.
- A separate review against the brief, by a reviewer who hadn't seen
  the work, found no bugs or spec misses. I fixed two of its nits: a
  timeout now stops the command's whole process group, not just the
  shell (the command runs with `start_new_session`), and a command that
  exits 0 while a child still holds the block unread is reported as
  not copied rather than "copied". Both have units. Two nits I left
  alone. First, a command that writes more than 64KB to stderr before
  exiting would show up as a timeout rather than its real error; real
  clipboard commands don't do that. Second, a `bale clipboard` that
  crashes exits 1, which the probe reads as "bale said why". That's
  true enough, because the traceback is on stderr.

## Things I'm unsure of

- I believe `pbcopy` doesn't care about `setsid`, since the pasteboard
  lookup goes through the bootstrap namespace, not the session. But I
  couldn't run macOS here. If a Mac operator sees "copied" with an
  unchanged clipboard, look at `start_new_session=True` in
  `run_clipboard_command` first.

- `clip.exe` reads stdin in the console codepage, so non-ASCII in a
  block may come out mangled on Windows. The old probe tee had the same
  issue. bale writes UTF-8 and doesn't try to transcode.
- `model_identity` is the configured id (`claude-opus-5-5`). This
  surface says the model actually serving a turn can differ.

## Proposals

- **What:** BALE.md true-up sentences for session 99b (BALE.md was out
  of scope here). Proposed sentences: "When `[probe]
  clipboard_command` resolves to a command for the repo a command runs
  in (project value, else global; `\"\"` at the project suppresses),
  bale copies every operator-side paste block as it prints it: pack's
  session opener (the lines between the scissor lines), `bale open`'s
  second-desk opener, `bale relay`'s exchange block, and `bale apply` /
  `bale retry`'s HOLD relay block named under `send first:` and its
  APPLIED relay block. Each copy prints one `[bale] clipboard:` line on
  stderr. A missing, failing, slow (10s) or unreadable command only
  skips the copy and never changes output or exit codes. Nothing is
  detected at run time." And: "`bale clipboard [--block NAME]` copies
  standard input the same way (exit 0 copied, 1 not copied, 2 on a
  terminal stdin); the probe scaffold pipes its PROBE BEGIN/END block
  into it." And: "`bale status` shows a `probe clipboard` row: the
  command and its layer, suppressed, unset, or UNREADABLE with the
  accessor's reason." **Why:** the brief routes BALE.md wording to
  99b. **Scope hints:** BALE.md's status and probe sections, plus a
  verb entry for `clipboard`.
- **What:** when the neutral `[clipboard] command` rename lands, rename
  the status row label to `clipboard` and update the `--block` notice
  wording. **Why:** the label follows the key's section today on
  purpose. **Scope hints:** `bin/bale` `_render_status`, `bale_report`
  `describe_clipboard_state`, and this session's suite.
- **What:** an additive `clipboard` object in `bale status --json`
  (`command`, `source`, `problem`). **Why:** the human row exists; a
  machine consumer has no equivalent. I deferred it (it's in the
  manifest's `deferred`) because the JSON key is better named after the
  rename. **Scope hints:** `bale_report.format_status_json` docstring
  and body; the StatusReport fields already exist.
- **What:** add `("clipboard",)` to `tests/test_cli_help.py`'s
  `COMMANDS` tuple, and give `claude/context/bale-internals.md` a line
  on `bale_report`'s copy section and `bin/bale` section 30. **Why:**
  both enumerate surfaces this session added. They were outside the
  forecast and aren't needed for the goal (this session's suite covers
  the verb's help). **Scope hints:** a tests-only or docs-only rider on
  the next session that touches either file.
