# notes — 2026-10-05-clipboard-key-rename-002

The rename landed as the brief drew it, with the desk's precedence pin
implemented as written. Read the tree, not this note, wherever they
differ — but these are the places I'd look first.

## Decisions to ratify

1. **How the two spellings merge.** `merged_config` no longer copies the
   `[probe]` table key by key. It asks each layer file what it says about
   the clipboard command (`_layer_clipboard_tables`: the `[clipboard]`
   and/or `[probe]` entries it sets, nothing else from either section)
   and lays the *deciding* layer's spelling(s) in under their own
   section names — project when it sets either spelling, else global.
   Nothing from the other layer is mixed in, so a project
   `[probe] clipboard_command` beside a global `[clipboard] command` is
   one project decision, not two keys. The typed accessor then applies
   the in-file precedence (`[clipboard] command` first) and can name
   the dotted key a file actually used in a refusal
   (`probe.clipboard_command must be a string`, not a made-up name).
   `CLIPBOARD_SPELLINGS` is the one place the order lives; every reader
   walks it.

2. **An unreadable new key never falls through to the legacy one**, on
   either side. bale: a triple-quoted `[clipboard] command` beside a
   readable `[probe] clipboard_command` is a refusal naming
   `clipboard.command` (the parser decided by the new key, so its
   spelling is what's judged). Crafter: a `[clipboard] command` line that
   is *there* — set, empty, or in a shape the scan cannot read — decides,
   and the legacy line is scanned only when there is none. So both
   readers judge a file by the same spelling. `SpellingTwinTest` pins
   the two scans on a corpus that now includes both headers and mixed
   files.

   The one known split this leaves (an edge of the pre-existing one): a
   *dotted* `clipboard.command = "x"` beside a readable
   `[probe] clipboard_command = "y"`. bale's parser sees the new key and
   refuses its spelling (loud, nothing copied, `bale status` shows
   UNREADABLE with the remedy); the crafter's scan cannot see dotted
   keys at all, so its no-bale fallback would tee into `y`. bale is loud
   first, so an operator meets the refusal before any probe runs; I did
   not teach the scan dotted keys. Pinned as a refusal case in
   `EffectiveAccessorTest.test_other_unseen_spellings_are_refused`.

3. **The row's exact words for the spelling.** It is named only when a
   reader would want it:
   - `pbcopy (project layer) — every paste block is copied` — a lone
     `[clipboard] command`, byte-identical to D's row apart from the
     label.
   - `pbcopy (global layer; via the legacy [probe] clipboard_command) —
     every paste block is copied` — the file still uses the old spelling
     (bale-src's own `bale.toml` reads this way today).
   - `pbcopy (project layer; [clipboard] command, which wins over the
     same file's [probe] clipboard_command — ignored) — every paste
     block is copied` — both set. The suppress and global-empty rows
     carry the same aside, and name the spelling in `sets … = ""`.
   `describe_clipboard_state` takes the two spellings by keyword, so the
   pre-rename triple call still renders.

4. **`bale status --json` says which spelling.** The object is
   `clipboard: {command, source, key, shadowed, problem}` — D's three
   plus `key` (`"clipboard.command"` | `"probe.clipboard_command"` |
   null) and `shadowed` (the other spelling the same file also sets,
   ignored under the precedence, or null). Always present, in and out
   of a repo, nulls when nothing is set. The existing keys are
   untouched (`test_existing_keys_are_untouched`). `resolve_clipboard`
   carries the five facts; `resolve_clipboard_command` still returns
   the triple for every caller that unpacks three.

5. **The wizard's carry-over.** `clipboard.command` is the only screen
   (the walk order's eleventh both-layer key, where
   `probe.clipboard_command` sat, so the `n/19` numbering is unchanged).
   Its current row is read through the precedence: a legacy-only file
   shows its value as current with the aside *read from this file's
   legacy [probe] clipboard_command; the write moves it to [clipboard]
   command*, and Enter returns `{"clipboard": {"command": …}}`. The
   inherited row is read the same way from the global file, so `x`
   suppresses a legacy global value too. A file setting both gets a
   `!` warning on the screen naming the winner and what the write
   drops. `render_bale_toml` never writes `[probe]` — even a dict that
   carries only the legacy key (a parsed pre-rename file handed
   straight to the renderer) comes out as `[clipboard] command`.

6. **The review names the move.** `config_changes` renders a legacy line
   the walk writes back as one `~` row —
   `probe.clipboard_command → clipboard.command = "pbcopy"  (the legacy
   spelling moves; same value)` — never as a `+`/`-` pair or the
   *not walked at this layer; dropped* stranger; a cleared legacy line
   reads `(cleared)`, and a legacy line shadowed by a `clipboard.command`
   the file already had says why it goes. The PTY tests in
   `test_probe_clipboard_config` and `test_wizard_ui` pin the rendered
   row.

7. **D's `--block` notice wording.** I read this as the copy path's
   notice that named the key — the project-suppress remedy in
   `copy_paste_block`, which now says `its bale.toml sets [probe]
   clipboard_command = ""` or `… [clipboard] command = ""` as the file
   has it. The `--block NAME` flag's own help (*e.g. 'probe block'*) is
   still right and was left alone. If D meant something else by it,
   say so and I'll follow.

8. **Names.** `get_probe_clipboard_command` and
   `probe_clipboard_command_problem` stay as aliases of
   `get_clipboard_command` / `clipboard_command_problem` (nothing in
   `bin/` called the dict accessor, but a test or a script might).
   `ClipboardCommandReading` gains `key` and `shadowed` with defaults,
   so the positional triple still constructs. The config-trio suite
   keeps its file name, `tests/test_probe_clipboard_config.py`
   (renaming it would have been a delete+create for no reader's
   benefit); its docstring points at the new suite,
   `tests/test_clipboard_key_rename.py`, which holds the rename's own
   outcomes.

## Where to look on review

- `bin/bale_config.py`: `_layer_clipboard_tables`, `_clipboard_value`,
  `_scan_clipboard_line` over `_scan_toml_text_key`,
  `clipboard_command_spelling_problem(path, dotted=None)` (the default
  now parses the file to find the deciding spelling, and reports a
  file that will not parse), `clipboard_command_reading`, the
  `clipboard.command` block in `walk_configurables`, the `[clipboard]`
  branch of `render_bale_toml`, and `config_changes`.
- `tools/craft_response.py` section 3: `scan_clipboard_command` over
  `find_bale_toml` + `scan_toml_text_key`; `scan_bale_toml_key` (which
  `read_validation_base` still uses) is now composed from the same two
  pieces — behavior unchanged, one file read.
- `bin/bale_report.py`: `ClipboardResolution` / `resolve_clipboard`,
  `describe_clipboard_state`, the `clipboard` object in
  `format_status_json` and its docstring entry.

## What I checked

- The six touched/new suites: 415 tests pass. Full default discovery:
  1834 tests pass (47 slow-gated skips); with `BALE_TEST_SLOW=1`: 1834
  pass. `validate.sh`: 94 checks pass.
- `validation.sh` runs in ~75 s here (the full discovery is behind
  `--slow`). Run on the unmodified tree, the clipboard suites and
  every session-specific assertion fail; on the staged tree everything
  passes. The `bale.toml`-untouched assertion passes on both by design
  (it pins the out-of-scope constraint by hash).
- `bale status` against a repo carrying bale-src's own
  `[probe] clipboard_command = "clip.exe"` reads
  `clip.exe (project layer; via the legacy [probe] clipboard_command) —
  every paste block is copied`, and `--json` reports
  `key: "probe.clipboard_command"`. The committed file is untouched.

## Proposals

- **A changelog row for this rename, with the version bump.**
  - What: when `bin/VERSION` next moves, that version's
    `claude/changelog/<version>.json` should carry rows for
    `bin/bale_report.py` (`bale status --json` gains the additive
    `clipboard` object: command, source, key, shadowed, problem) and
    `bin/bale_config.py` (`[clipboard] command` is the key; `[probe]
    clipboard_command` read as a legacy alias; the in-file precedence).
  - Why: CODE.md §8.5 asks the session that changes a machine-readable
    surface to write the entry in the same response, but this arc's
    sessions (C, D, log-hold) landed without a bump — `bin/VERSION` is
    still 0.4.45 with board-122's record — so I followed the arc rather
    than mint a version in a session whose forecast does not name
    `bin/VERSION` or `claude/changelog/`.
  - Scope hints: `claude/changelog/`, `bin/VERSION`; the sitting-close
    session, or whichever session bumps next.
- **BALE.md true-up sentences** (BALE.md is out of this request; the
  wording belongs wherever it names the key):
  - §5's `clipboard` row and §8.9's clipboard notes, if they name
    `[probe] clipboard_command`: "the key is `[clipboard] command` at
    both layers; `[probe] clipboard_command` is read as a legacy alias,
    `[clipboard] command` winning inside one file".
  - The `bale status` row: "labelled `clipboard`; `--json` carries it as
    the `clipboard` object (`command`, `source`, `key`, `shadowed`,
    `problem`)".
  - Why: the brief routes BALE.md wording here as Proposals.
- **Drop the legacy alias one day, or not.**
  - What: nothing now. If the alias is ever retired, the retirement
    needs `clipboard_command_reading` to refuse `[probe]
    clipboard_command` with a remedy, the crafter's scan to stop
    reading it, and bale-src's own `bale.toml` moved first.
  - Why: every reader walks `CLIPBOARD_SPELLINGS`, so the retirement is
    a one-tuple change plus the refusal text; I note it so the pin is
    visible rather than because anything asks for it. `TARBALL.md`
    §3.2's precedent for `claude-decides` is "accepted for good", and
    that reads right here too.
