# Session 2026-11-12-clipboard-001: what bale puts on the clipboard (0.4.59)

All three slips are in, as one release. clip.exe now gets every copy as
UTF-16LE with no byte-order mark. A clarification's landing prints the
planner-facing exchange block and copies it. `bale clipboard` masks URL
passwords (and GitHub tokens) and its notice says so. Nothing else is
masked. bin/VERSION reads 0.4.59 and claude/changelog/0.4.59.json is the
release's record. Every changed path is inside the write forecast.

## Decisions to ratify

These are the open choices the brief left to me, and two places where I
departed from its words.

- **Where the encoding rule lives.** It sits in `copy_paste_block`, through a
  new pure `clipboard_payload(command, data)`, so every paste point gets it at
  once. `run_clipboard_command` is unchanged and still runs whatever bytes it
  is handed. "Is this clip.exe" is `clipboard_command_is_clip_exe`: the
  command's first word, split the way the shell will split it (shlex, POSIX
  rules, so a quoted path with spaces stays one word), with its base name taken
  across either slash and compared case-insensitively.
- **Mixed case counts.** `CLIP.EXE` and `Clip.Exe` count as clip.exe. WSL interop
  on /mnt/c finds the same program under any case, and that program wants the
  same bytes. The checkpoint grades only the lowercase spelling, and counting
  more spellings can't break that one.
- **What doesn't count.** A command that reaches clip.exe only further along
  (`cmd.exe /c clip`, an `env A=1 clip.exe` prefix, `echo x | clip.exe`) is fed
  UTF-8, as before. The brief's rule is about the first word, and I didn't try
  to second-guess a pipeline.
- **Non-UTF-8 bytes bound for clip.exe are replaced, and the notice says so.**
  UTF-16LE can't carry raw bytes. The only other choice was the very mangling
  the slip is about. The notice gains "; input that was not valid UTF-8 reached
  clip.exe as U+FFFD". Only `bale clipboard` can be handed such bytes. Every
  other paste block is a str bale rendered.
- **The clip.exe notice is otherwise unchanged.** I thought about adding "as
  UTF-16LE" to the copied line. I left it out so the pinned notice shape, and
  outcome 2's "the notice is relay's", stay exact on every machine.
- **The mask is `xxx`, as the slip writes it.** It covers the whole password,
  so nothing of it survives. The edges:
  - A password holding a raw `@` ends at the authority's last `@`.
  - A userinfo with no colon (`https://TOKEN@host`, `ssh://git@host`) is a
    user name and is left alone, because outcome 3 says the user name stays.
  - A password that already reads `xxx` is not counted again.
  - An authority ends at `/ ? #`, whitespace, a quote, `< > \` or a backtick.
  - The scan is linear: it finds each `://` and looks back at most 64 bytes
    for a scheme.
- **GitHub tokens are masked too** (ghp_, gho_, ghu_, ghs_, ghr_, github_pat_),
  with the prefix kept: `ghp_xxx`. This is the office's other masked kind, and
  it also covers the token-as-user form `https://ghp_...@github.com`. The
  notice counts the two kinds apart: "; masked 2 URL passwords and 1 GitHub
  token before copying". If you'd rather `bale clipboard` mask only what the
  brief names, the token half is one regex and one count, and easy to pull.
- **The landing's block comes before the `[CLARIFICATION]` banner.** The order
  is: the round is preserved, a `[bale]` line says the block follows, the block
  prints, its clipboard notice prints, and then the unchanged summary,
  questions and banner. The verdict and the next step stay last, as the
  banner's layout rule wants. The trailer is word for word what 0.4.58 printed,
  and it still names `bale relay <sid>`.
- **Under `bale apply --json` the landing's block goes to stderr.** Stdout there
  is the one report line, and `format_apply_json`'s keys are pinned. The block
  is still copied, and still byte for byte relay's. Outcome 2 says "on stdout".
  I read that as the human run's stdout, and this is the one place I bent it.
- **One rendering for both blocks.** `bale_relay.render_recorded_round` is
  `_cmd_reemit`'s rendering, lifted out unchanged, with its refusals now raised
  as `UnreadableRound` and turned back into the same `fail()` lines and the
  same reason codes. The landing renders the record from disk, as preserved,
  so its bytes and relay's later re-emit match by construction (tested both
  ways). One consequence: bale_apply now imports bale_relay, lazily and inside
  the function. The relay module's docstring said that never happens, so I
  amended it.
- **A landing whose block can't be rendered still lands.** It logs why and
  names `bale relay <sid>`, and the exit code is unchanged. The round is
  already preserved at that point, and a crash would be worse than a missing
  print.

## BALE.md has no clipboard paragraphs

The brief points the wording at "BALE.md's clipboard paragraphs". BALE.md
mentions the clipboard once, at the opener's `--json` key (around line 2468).
The clipboard prose is in claude/context/bale-internals.md (cluster 20 and the
paste-block copy section), and that's where I wrote it. BALE.md got the
landing's paragraph in 8.10.2, as a new paragraph after the numbered list.
I didn't renumber the list, because "§8.10.2 step 4" is cited from code and
from the handbook. docs/TARBALL.md 4.3 and `bale help clipboard` carry the
rest.

## The console half of the second slip

I found no path that mangles bale's own console output. bale writes str to
Python's stdout and `[bale]` lines through `print`. Nothing in bin/ calls
`reconfigure`, sets `errors=`, or writes a code page. On the occupant's
terminal (LANG=C.UTF-8, stdout utf-8, Windows Terminal) those bytes reach a
UTF-8 renderer. The probe's U+0393 U+00C7 U+00F6 is exactly UTF-8 read as code
page 437, which is clip.exe's reading. That matches answer [1]: the garbled
text came through the clipboard. So outcome 1 is the whole fix.

## Where to look closely

- `bin/bale_report.py`: `_url_password_spans` and `mask_clipboard_credentials`,
  for the mask's edges. `clipboard_payload`, for the not-UTF-8 path.
- `bin/bale_apply.py`: `_print_landed_exchange_block`. It writes through
  `sys.stdout` as the process has it. That's the real stdout on a human run
  and stderr under `--json`, because `enable_json_mode` rebinds it.
- `bin/bale_relay.py`: `_cmd_reemit`'s refusal lines. They should match 0.4.58
  word for word. `tests.test_refusal_codes` and `tests.test_relay_verb` agree.

## Validation

- validation.sh, as shipped, ran on a staged copy (the request's base, files/
  overlaid, apply.sh run, the manifest at .bale-manifest.json). Every check
  passed, the whole suite skipped without `--slow`, and it took about 1m50s.
- On the unmodified tree, every session assertion fails and the regression
  suites pass, which is what they're for.
- The whole suite (`python3 -m unittest discover -s tests`) ran clean on the
  staged tree: 2183 tests, 48 skipped, about 8.7 minutes. That is the last
  session's 2147 plus this module's 36. An earlier run, before the module's
  last two tests, was also clean (2181).
- The new suite is tests/test_clipboard_utf16_mask.py (36 tests). Its
  end-to-end cases drive a fake `clip.exe` on PATH. The fake is an sh script
  that writes its stdin to a capture file. The suite named it both bare and
  by full path.
- Each case checks that the capture is the printed block in UTF-16LE with no
  BOM. It does this for pack's opener, `bale open`'s opener, relay's ingest
  and re-emit, apply's HOLD block, retry's APPLIED block, the landing's block,
  and `bale clipboard`.

## Proposals

- **What:** make the probe scaffold's craft-time fallback copy match bale's.
  That copy is `PROBE_CLIPBOARD_FALLBACK_EPILOGUE` in tools/craft_response.py,
  which runs only when bale is not on PATH. It should transcode for clip.exe
  (`iconv -f UTF-8 -t UTF-16LE`, or python3) and mask the way
  `bale clipboard` does.
  **Why:** today it still pipes UTF-8, unmasked, into the request's clipboard
  command. On a machine with the project's `[probe] clipboard_command =
  "clip.exe"` and no bale on PATH, it mangles and leaks exactly as the slips
  describe. I left it alone because outcome 1 is about copies bale makes, and
  this one is the scaffold's.
  **Scope hints:** tools/craft_response.py and its parity tests. It's small,
  and it could ride with any later session that touches the crafter.
- **What:** have `bale status`'s clipboard row say "fed UTF-16LE" when the
  command is clip.exe.
  **Why:** the occupant's row reads "clip.exe (project layer; via the legacy
  [probe] clipboard_command)". Nothing in it tells him the encoding rule is
  now in force. One clause in `describe_clipboard_state` would. I didn't add
  it because the row's words were pinned by earlier sessions and this one
  didn't ask to move them.

## Walkthrough

### What changed

- **bin/bale_report.py.** `copy_paste_block` asks `clipboard_payload` what to
  feed the configured command. For clip.exe that is UTF-16LE with no BOM; for
  anything else it is the UTF-8 bytes as before. The new
  `mask_clipboard_credentials` (with `MaskedCopy` and `masking_aside`) replaces
  URL passwords and GitHub tokens in bytes.
- **bin/bale.** `bale clipboard` masks its stdin before copying and passes the
  count to the notice. Its help text names the landing's copy, the clip.exe
  rule and the mask.
- **bin/bale_apply.py.** The clarification landing prints and copies the
  exchange block for the round it preserved, before its banner.
- **bin/bale_relay.py.** `render_recorded_round` is the one rendering of a
  preserved round, shared by relay's re-emit and the landing.
- **Docs and release.** BALE.md 8.10.2, docs/TARBALL.md 4.3 and
  claude/context/bale-internals.md describe the three changes. bin/VERSION is
  0.4.59, and claude/changelog/0.4.59.json is its record.
- **Tests.** tests/test_clipboard_utf16_mask.py is new.

### Why

- On WSL, clip.exe reads UTF-8 through the console's code page, so every em
  dash bale copied arrived as three wrong characters. Only UTF-16LE with no
  mark arrived whole (probe clipexe-encoding).
- The planner-facing exchange block only reached the clipboard if someone ran
  `bale relay <sid>` as a second command. The landing, where the block is
  first needed, printed only a banner.
- A probe's output piped into `bale clipboard` is the one copy the office
  cannot mask, so a credential in a URL went to the clipboard whole.

### How to explain each piece

- **clip.exe.** "bale now speaks clip.exe's language. If the clipboard command
  is clip.exe, by name or by path, bale hands it UTF-16LE, which it keeps
  exactly. Any other command gets the same UTF-8 it always did."
- **The landing.** "When a clarification lands, bale prints the block you
  carry to the planner and puts it on the clipboard. It's the same block
  `bale relay <sid>` prints. The banner and its next step haven't changed."
- **The mask.** "`bale clipboard` blanks the password in any URL (and any
  GitHub token) before it copies, and the clipboard line says how many it
  blanked. Nothing else is masked, because the other blocks carry a hash of
  their body and a masked body would fail it."

### Questions a reviewer will ask

- *Why not mask the exchange block too?* Its body is hashed. A masked body
  fails its trailer on ingest. The occupant's answer [2] settled it.
- *Does a pipeline that ends in clip.exe get UTF-16LE?* No. Only the first
  word counts. `cmd.exe /c clip` and `echo | clip.exe` are fed UTF-8, as
  before.
- *What if the landing's block can't be rendered?* The landing logs why,
  names `bale relay <sid>`, and exits as it would have. The round is already
  preserved.
- *Does `--json` still print one line?* Yes. The block goes to stderr there.
- *Why are GitHub tokens masked when the slip only names URLs?* The office
  masks both kinds in its own copies. A token is as much a credential as a
  URL's password. The notice counts the two apart.
- *Was bale's console output itself mangled?* No path was found. The garbling
  came through clip.exe.

### A hand test

1. On the WSL machine, with the project's clipboard command still `clip.exe`,
   run `printf 'A—B·Cé\n' | bale clipboard --block test` in the
   bale-src checkout.
2. In PowerShell, run `Get-Clipboard -Raw`. It should read `A—B·Cé` (an em
   dash and a middle dot, not `ΓÇö`).
3. Run `printf 'https://alice:SECRET@example.com/x\n' | bale clipboard`. The
   notice line should end "masked 1 URL password before copying". Pasting
   should give `https://alice:xxx@example.com/x`.
4. The next time a clarification lands, look for the BALE EXCHANGE block
   printed above the `[CLARIFICATION]` banner. Paste the clipboard into a
   planner chat: it should be that block, em dashes intact.

## Handbook

### bale-src

- Since 0.4.59, when the clipboard command's first word has the base name clip.exe (a bare name or a path, any letter case), every copy bale makes is fed to it as UTF-16LE with no byte-order mark; any other command still gets the UTF-8 bytes unchanged.
- Since 0.4.59, a clarification's landing in `bale apply` prints the planner-facing exchange block for the round it preserved, before the `[CLARIFICATION]` banner, byte for byte the block `bale relay <sid>` re-emits, and copies it as the landing's last copy; under `--json` the block rides stderr.
- Since 0.4.59, `bale clipboard` masks each URL's password (as `xxx`) and each GitHub token (prefix kept) before copying, and its notice line says how many; no other paste block is masked, since their bodies are hashed.
- No path mangles bale's own console output: the garbled em dashes the occupant saw came through clip.exe reading UTF-8 as code page 437.
- The whole unit suite runs clean in a worker sandbox at 0.4.59, with the new tests/test_clipboard_utf16_mask.py: 2183 tests, 48 skipped, about 9 minutes.

#### Front sheet

bale-src is the source of bale, the occupant's command-line tool for
handing work to an agent session and taking the result back. bale packs
a request tarball, carries the worker's questions and the planner's
answers through `bale relay`, checks the response tarball the session
returns, and lands it on a branch in the project only after validation
passes. On 2026-11-12 it stands at 0.4.59 once this session lands, the
third of eleven releases planned in folder 43 for the slips about bale;
from this release bale's own copies reach clip.exe whole.

## Structure

- title: Fix bale-src for the slips about bale, in eleven sessions
- size: high
- goal: Land the fixes to bale-src for the slips about bale in the office's suggestion box, one release per session, in the ratified order
