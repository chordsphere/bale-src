# Notes: 2026-11-12-probe-scaffold-002 (bale 0.4.60)

All five outcomes are in, inside the forecast, no departures. The
crafter's probe scaffold has a run-line slot and a secrets note with a
masked `git remote -v` line, `--bundle`'s help carries the successor
sentence, the no-bale fallback copy is `bale clipboard`'s copy, and
bin/VERSION is 0.4.60 with its changelog record.

## Decisions to ratify

- **What `--run-line` refuses.** A LINE holding any line break (LF, CR,
  and the rarer separators Python's `splitlines` knows), a blank LINE,
  and a LINE starting `#` (the sitting's guess, taken, so the header
  never reads `# # ...`). Each exits 2 with nothing on stdout.
  `--run-line` without `--probe` is refused too rather than ignored.
- **How the fallback masks.** The scaffold carries
  `PROBE_FALLBACK_MASK_PY`, a python3 program in a single-quoted bash
  variable, run with `-I -B -c`. It runs twice over the same block:
  once to get the notice's aside (which is also the check that python3
  works), then once into the request's command. A heredoc was out
  because the block itself is on python's stdin. The program holds no
  `'` and no `!`, and a test checks that. The encoding is picked at
  craft time by `clip_command_is_clip_exe`, a twin of
  `bale_report.clipboard_command_is_clip_exe`, because the command is
  fixed at craft time too.
- **The fallback's success line.** It still starts `[clipboard] probe
  output copied with the request's bale.toml clipboard command, read at
  craft time`, so anything matching the old line still matches. After
  that it adds `, as 'bale clipboard' copies it`, then ` (UTF-16LE with
  no byte-order mark, for clip.exe)` when the command is clip.exe, then
  bale's own aside (`; masked 1 URL password and 1 GitHub token before
  copying`, and the U+FFFD clause when it applies).
- **Failure order.** When the request's command exits without reading
  (`false`), the mask gets a broken pipe. The script reads the
  command's status first, so the line blames the command, as before,
  and not the mask. The copy pass's own stderr is discarded. That
  removed a `BrokenPipeError` traceback the old test caught.
- **The snippet is a display mask, not bale's byte rule.** It is `sed
  -E` with `#` as the delimiter. A comma clashed with `{36,}`, and I
  caught that by running it. It has no `\b`, which BSD sed lacks, and
  no 255 upper bound. So it masks the same two kinds as bale, slightly
  more eagerly, and keeps name, user, host and path. It sits in the
  placeholder's comments under a `Secrets (TARBALL.md 4.3)` note,
  right after the worked `git ls-files` line.
- **bin/bale_report.py: a comment only.** The masking section now names
  its twin in the crafter and the suite that pins the two. No code
  changed there.

## Look closely at

- `PROBE_FALLBACK_MASK_PY` beside `bale_report._url_password_spans` /
  `mask_clipboard_credentials`. `MaskProgramParityTest` runs both over a
  28-item corpus (bale's own edge cases, tokens, bytes that are not
  UTF-8, a BOM in the input, and the scheme-window edge) for clip.exe
  and for a UTF-8 command. `FallbackMatchesBaleClipboardTest` compares
  the fallback's capture with the real `bin/bale clipboard --block
  "probe block"`'s, byte for byte, for both commands.
- bale-src's own bale.toml still sets `[probe] clipboard_command =
  "clip.exe"`. So a probe crafted in this repo and run on the WSL
  machine without bale on PATH now copies UTF-16LE, masked. Before
  this, that copy was UTF-8 and unmasked.

## The suite

The whole suite ran here on the changed tree (`python3 -m unittest
discover -s tests`): 2208 tests, 48 skipped, clean, in about 9.5
minutes. That is 0.4.59's 2183 plus this session's 25. The first run
had one failure, and it was my fault, not the change's: I had run
Python on bin/ without `-B` while checking the changelog record, and
the stray `bin/__pycache__` got copied into the test install. I
removed it and the rerun was clean. validation.sh gates the full
suite behind `--slow`, so I claim it `untested`. The targeted modules
and the session assertions are claimed `pass`, observed: I ran
validation.sh on a staged copy before packing, and its byte assertions
fail on the 0.4.59 tree.

## Walkthrough

### What changed

- **tools/craft_response.py.** `--probe SLUG --run-line LINE` writes
  `# LINE` as a fifth header line, between `# Read-only:` and
  `# Bound:`. The scaffold's placeholder comments now carry a secrets
  note and a masked `git remote -v | sed -E ...` line. The no-bale
  fallback copy masks credentials and re-encodes for clip.exe the way
  `bale clipboard` does, through `PROBE_FALLBACK_MASK_PY`. `--bundle`'s
  help (and the module docstring) says a successor's bundle takes a
  stem no earlier bundle of its slug had.
- **docs/TARBALL.md.** 4.2 names `--run-line`. 4.3's Secrets-aware rule
  names remote URLs and `git remote -v`, and its fallback paragraph
  says the no-bale copy is bale's copy.
- **Tests.** tests/test_probe_scaffold.py is new.
  tests/test_craft_response.py follows the fallback's new pipe text.
- **Release.** bin/VERSION is 0.4.60, and claude/changelog/0.4.60.json
  is its record. claude/context/bale-internals.md and a comment in
  bin/bale_report.py name the new twin.

### Why

- The office runs a probe with a line like `office probe 43 --sid S`.
  Until now that line lived outside the block, so a copied block lost
  it.
- A probe printed a remote URL with a personal access token. The
  secrets rule only named files and variables.
- A sitting that dated its successor's stem from its own id got the
  same stem as the bundle it was opened from. The consumer then took
  the new bundle for the old one.
- Without bale on PATH, the probe's copy went out raw: UTF-8 (garbled
  by clip.exe) and unmasked, the one copy bale's 0.4.59 mask never saw.

### How to explain each piece

- **Run line.** "Pass `--run-line` and the probe's header says how to
  run it, on the line after Read-only. Leave it off and nothing
  changes."
- **Secrets note.** "The scaffold now reminds the worker that remote
  URLs can hold passwords and tokens, and gives one `git remote -v`
  line that prints remotes with those blanked."
- **Bundle help.** "The help now says a successor needs a fresh stem,
  and why."
- **Fallback.** "Without bale, the probe copies exactly what `bale
  clipboard` would have: passwords and GitHub tokens blanked, and
  UTF-16LE when the command is clip.exe. If python3 isn't there, it
  copies nothing and says so."

### Questions a reviewer will ask

- *Why python3 and not sed for the fallback?* The copy has to be
  bale's byte for byte, including the UTF-16LE transcode and bale's
  exact rules (the last `@` of the authority, the `xxx` not counted
  twice). A python3 copy of bale's code can be pinned to bale's by a
  parity test. A sed copy could not.
- *What if the mask and bale drift?* tests/test_probe_scaffold.py runs
  the program and bale's functions over one corpus, and runs the real
  `bale clipboard` end to end. Either drifting turns it red.
- *Does a probe with bale on PATH change?* No. The `bale clipboard`
  pipe and its 0/1 contract are untouched. Only `clip_fallback`'s body
  changed, and only when the request named a command.
- *Why refuse a run line starting `#`?* The scaffold writes the `# `
  itself, so the header would read `# # ...`.
- *Is the git snippet the same mask as bale's?* It masks the same two
  kinds and keeps the same parts. It is a sed display mask, a little
  more eager (no word boundary, no length cap), so it runs the same on
  GNU and BSD sed.

### A hand test

1. In the bale-src checkout on the WSL machine, run
   `python3 tools/craft_response.py --probe hand-test --run-line "office: probe 43 --sid S" > /tmp/p.sh`.
   Open /tmp/p.sh. Line 5 should be `# office: probe 43 --sid S`,
   between the Read-only and Bound lines.
2. In /tmp/p.sh, replace the `TODO(worker): unfilled probe placeholder`
   echo with `echo "https://alice:SECRET@example.com/x — café"`.
3. Run it with bale off PATH but clip.exe on it, for example
   `env PATH=/usr/bin:/bin:/mnt/c/Windows/System32 bash /tmp/p.sh`
   (assuming bale lives outside those). The last stderr line should say
   `probe output copied ... (UTF-16LE with no byte-order mark, for
   clip.exe); masked 1 URL password before copying`.
4. In PowerShell, run `Get-Clipboard -Raw`. It should show
   `https://alice:xxx@example.com/x — café`, with the em dash and é
   whole and no stray character at the start.
5. Copy the scaffold's `git remote -v | sed -E ...` line (without its
   `#`) and run it in the checkout. It should list origin as
   `git remote -v` does, with any password or token shown as `xxx`.
6. Run `python3 tools/craft_response.py --help | grep successor`. It
   should print `A successor's bundle takes a stem no earlier bundle of
   its slug had.` on one line.

## Handbook

### bale-src

- Since 0.4.60, `tools/craft_response.py --probe SLUG --run-line LINE` writes `# LINE` as the probe header's line after `# Read-only:` and before `# Bound:`; a LINE with a line break, a blank LINE or one starting `#` is refused with nothing on stdout.
- Since 0.4.60, the probe scaffold's placeholder comments carry a secrets note naming secret files, remote URLs and `git remote -v`, and one comment line that is a masked `git remote -v | sed -E ...` command that runs as written.
- Since 0.4.60, a crafted probe's no-bale fallback copy (a request bale.toml clipboard command, bale not on PATH) is byte for byte what `bale clipboard --block "probe block"` copies: credentials masked and UTF-16LE with no byte-order mark for clip.exe; it needs python3, and without it copies nothing and says so.
- The crafter's fallback mask (`PROBE_FALLBACK_MASK_PY`) and clip.exe rule (`clip_command_is_clip_exe`) are restated twins of bin/bale_report.py's, pinned by tests/test_probe_scaffold.py; a change to bale's mask or encoding rule must change the twin in the same session.
- Since 0.4.60, `craft_response.py --help` says under `--bundle`: "A successor's bundle takes a stem no earlier bundle of its slug had."

## Structure

- title: Fix bale-src for the slips about bale, in eleven sessions
- size: high
- goal: Land the fixes to bale-src for the slips about bale in the office's suggestion box, one release per session, in the ratified order
