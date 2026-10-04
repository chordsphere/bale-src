# notes — 2026-10-03-wizard-defaults-006 (session C, wave 2)

Everything landed inside the forecast. Five of the six forecast files changed;
`tests/test_layout_and_formats.py` needed nothing, because its walk tests find
items by key, not position, and the renderer still emits `[probe]` before
`[layout]`. There are no forecast departures, and none of the out-of-forecast
wizard suites (`test_archive_dir`, `test_auto_sweep`, `test_blind_checkpoint`,
`test_required_check_gate`, `test_sandbox_wrapper`) needed an edit: they are
Enter-through plus key-name checks, and they pass unchanged. No light block,
probe or clarification was used.

## Handoff to session D (brief §5)

- **Spelling and section: unchanged.** The key is still `[probe]
  clipboard_command`. I kept it rather than moving to a new section with an
  alias. The crafter reads exactly this line from the project file, so a
  project that sets it today keeps working with no migration. An
  Enter-through `bale config init` re-renders the same line (as a basic
  string), which the crafter reads. This is pinned twice: in-process in
  validation.sh, and through a real pty in
  `test_crafter_still_reads_the_project_key_after_enter_through`, with a
  different global value present. If you'd rather it lived under a neutral
  section name (it now covers every paste block, not only probes), that is a
  Proposal below, not something I did.
- **Layering: global, project override, suppress.** It is the `[identity]
  packer` mechanics exactly. `merged_config` now inherits `[probe]` per key;
  the global wizard walks it (11/11); the project wizard shows the inherited
  value and offers `x`, which writes `clipboard_command = ""` and suppresses
  the inherited value. In the walk order it sits last among the both-layer
  keys, so it is 11/19 in project mode.
- **The accessor bale code should call:** `bale_config.effective_clipboard_command(repo)`,
  with `repo` set to `None` outside a repo (it then reads the global file
  only). It returns the stripped command, or `None` for "no copy". It is fatal
  on content the crafter can't read (backslash, double quote, control
  character), and on a supplying file that spells the key triple-quoted, as a
  dotted key, or as an inline table. Use it rather than
  `get_probe_clipboard_command(merged_config(repo))`: that dict-level accessor
  still works, but it can't see spelling. For the `bale status` row,
  `bale_config.clipboard_command_source(repo)` returns `"project"`,
  `"global"`, or `None`. `"project"` includes the suppressed case, so pair it
  with the effective value to say "suppressed here".
- **A project's `[probe] clipboard_command`:** nothing happens to it. It stays
  where it is, it is still the crafter's only input for probes, and for bale it
  now overrides any global value.
- **Help text you'll want to touch:** the key's `?` description says the probe
  scaffold sees only the project file "until bale copies paste blocks itself",
  and that setting the key is the opt-in to that copying "once it lands". Both
  phrases become past tense when D lands. The short summary and the
  `(unset — no clipboard copy)` effective line are already worded for D's
  world.

## Decisions to ratify

1. **Detected means detected and runnable.** A clipboard command is marked
   detected only when the environment points at it *and* its program is on
   PATH (`shutil.which`). The mapping is: macOS → pbcopy; Windows or WSL →
   clip.exe; `WAYLAND_DISPLAY` → wl-copy; `DISPLAY` → xclip, then xsel. A
   Wayland session with no wl-copy installed marks nothing; the five
   alternatives are still listed.
2. **Digits on a key with alternatives are picks.** A value made only of
   digits is read as a number, and one out of range re-asks, following the
   checkpoint picker's rule. The trade-off: on those keys you can't type a
   pure-number value (for example a packer named "42"). Keys without
   alternatives are untouched, so bools still take `0`/`1`, and the
   `.baleignore` add prompt still takes a digit pattern when nothing is
   suggested. In a list key each colon-separated entry may be a number:
   `1:2` takes two, and `1:inbox` mixes a pick with a typed path.
3. **The triple-quote rider lives in the reader, not the loader.** The
   refusal is in `effective_clipboard_command`, plus a warning on the key's
   wizard screen. It is not in `load_config`, because putting it there would
   make `bale config init` itself refuse to open the one file it can fix:
   Enter-through rewrites the key as a basic string. It applies at both layers,
   so the key has one spelling everywhere. Today nothing in `bin/` calls the
   reader, so the refusal bites only when D wires it in. Until then the
   wizard's warning is the visible half. 005/69's disclosure in the crafter's
   note stays true.
4. **`bin/` restates the crafter's scan rather than importing it.**
   `_scan_clipboard_line` and `_one_line_quoted_value` restate the crafter's
   one-line scan, because `bin/` never imports `tools/`. `SpellingTwinTest`
   pins the two against one corpus of lines.
5. **Detector failures are visible.** A detector that can't run (git missing,
   a timeout, a non-repo) leaves its key with only the static alternatives, or
   none, and prints one dim `detection skipped: …` line on that screen. It
   never fails the wizard. Finding nothing is silent, which is the specified
   degrade.
6. **Which .baleignore signals count** (brief §4.3, my judgment):
   - Files are counted over exactly what pack would list (`git ls-files
     --cached --others --exclude-standard`), minus pack's baked-in excluded
     directories (read lazily from `bale_pack.BAKED_IN_EXCLUDE_DIRS`; if
     that name ever moves, the suggestions just get noisier).
   - Three signals, in precedence order per file: a directory named `data`,
     `datasets`, `vendor`, `third_party`, `.idea` or `.vscode` on its path,
     suggested as `name/`; a bulky or binary extension (data and model
     formats, archives, media, compiled objects; the list is
     `BALEIGNORE_SUGGEST_EXTENSIONS`), suggested as `*.ext`; or any single
     file of 1 MiB or more, suggested as its own anchored path.
   - Heaviest first, at most six. Each aside gives the file count and size.
     Kept patterns are never re-offered.
7. **Other alternatives and what marks them detected.**
   - `validation.base` always lists both conventions; one is marked detected
     when its directory (`<agent_dir>/checkpoints/`) or file
     (`scripts/validation.base.sh`) is already in the repo.
   - `apply.archive_dir` is marked detected when `<agent_dir>/responses`
     exists. `<agent_dir>` comes from the project file's `[layout]` when it's
     usable.
   - `staging.strategy` marks nothing: there is no signal to detect.
   - Under WSL I offer every Windows profile's Downloads that exists (at
     most three, the profile matching `$USER` first), because the Windows and
     Linux user names often differ. Home Downloads is offered as the literal
     `~/Downloads`, since search_paths expands tildes at use time.
   - The project wizard also offers the absolute WSL path. That's odd in a
     committed file, but the brief asks for it.
8. **Help, grammar and docstring updates.** The grammar table gained an
   "a number" row, and each `?` help with alternatives names the gesture. I
   rewrote `validation.base`'s and the clipboard key's descriptions, because
   their old text was now wrong or incomplete (session A's "descriptions
   untouched" ruling was about its own move). `bale_config`'s docstring index
   was already stale before this session, and now carries real line numbers.

## Places to look closely

- `bale_wizard.WizardUI.ask_choice` decides one thing itself: an
  out-of-range number re-asks. Everything else comes back raw, as the
  extension-point note asked. Check that this sits right with B, who builds on
  the layer.
- Every walk now runs detection unless the caller passes `suggestions=`. In
  practice that is one or two `git` subprocesses per walk, each capped at 5 s.
  In-process test drivers that call `walk_configurables` without it see the
  test machine's environment on screen. That's harmless, because Enter
  semantics don't change. My tests pass explicit `WizardSuggestions` wherever
  they assert on screens.

## The test run

- The changed tree's full suite runs 1739 tests (45 new). It has the same six
  failures as the pristine tree, which runs 1694. All six come from context
  that wasn't shipped: `claude/changelog/0.4.45.json` (two
  `test_changelog_record` cases), ADR 0013 (`test_doc_crossrefs`), and the
  repo's own `bale.toml` include group (three `test_include_group` errors).
  They should pass in your tree.
- I ran validation.sh against a simulated staging tree with the change
  applied: everything passed and all three claims agree (observed). Against
  the unmodified tree the session assertions fail, as they should.

## Proposals

- **BALE.md sentences for the 99b true-up.**
  - What: say that `[probe] clipboard_command` is per-machine (both layers,
    `x` suppresses, `effective_clipboard_command` is the reader), and that
    `bale config init` offers numbered alternatives on eight keys and in the
    `.baleignore` step, with Enter unchanged.
  - Why: the brief routes `BALE.md` truing here as a Proposal, and BALE.md
    wasn't in this request.
- **A neutral section name for the clipboard key.**
  - What: consider moving the key to a neutral section, e.g. `[clipboard]
    command`, with `[probe] clipboard_command` read as a legacy alias.
  - Why: once D copies every paste block, "probe" undersells the key.
  - Scope hints: it costs a two-key precedence rule in bale and a crafter
    change, so it belongs with or after D, never before it.
- **Point `walkthrough_baleignore` at pack's real filters.**
  - What: when B or a later session settles `bale_pack`'s public surface,
    have the suggestions use pack's actual filter chain (secrets,
    `.baleignore`, checkpoint exclusion) instead of only the baked-in
    directory set.
  - Why: the counts would then be exactly "what this pack would ship".
