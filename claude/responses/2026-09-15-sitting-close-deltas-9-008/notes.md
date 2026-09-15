# notes.md — 2026-09-15-sitting-close-deltas-9-008

Landed as briefed: the header edit plus thirteen pure-insertion hunks
in `claude/MASTER.md`, nothing else. The diff against the shipped base
has exactly one removed line (the old `Last landed by:` line) and 325
added lines. Verified at build with difflib: the only non-`insert`
opcode is the one-line `replace` at the header. `bin/VERSION`
untouched at 0.4.32.

## Where each block landed

- Header, line 14: `Last landed by:` now names this session; the one
  removed line.
- Block A: §3, after close-8's block, directly before `## 4. The
  board` — paragraph, blank line, nine bullets without blank lines,
  matching close-8's block.
- Block B: §4, rows 99–103 after row 98, a blank line between rows.
- Block C: bracketed growths on rows 47, 77, 89, 90, 95, each on a
  fresh 4-space-indented line after the row's last line (row 47's
  sits under its 2026-09-14 bracket; row 95's under "Desk guess,
  labelled: the order is intended.").
- Block D: §5, after the 2026-09-14 preamble's list (which close-8's
  two 2026-09-15 contracts already ended), before `## 6.` — preamble,
  blank line, four bullets without blank lines.
- Block E: §6, entries 136–140 after entry 135, blank line between.
- Block F: §7, five bullets directly after the 0.4.30 landmark line,
  no blank lines, so they sit between that landmark and "The pack
  machine's clock".
- Block G: four new registry entries appended after the `normalize()`
  entry (the list's last); the two consumption notes as bracketed
  2-space-indented lines after the `persist_pack_session` entry and
  the "§7/§7.2 includes-as-scope" entry respectively.

## How verbatim was kept

Close-8's method, unchanged. A script slices each `### Block` out of
the brief's README.md by header, substitutes `<your-sid>`, and wraps
with `textwrap` at width 70, `break_on_hyphens=False`,
`break_long_words=False`, with the spaces inside backtick code spans
masked before wrapping so no span straddles a line. Checked at build:
every code span and every hyphen-bearing token from the brief sits
intact on one landed line; no added line exceeds 70 columns; and
every landing paragraph (41 of them) appears in the landed doc at its
expected count with whitespace collapsed. `validation.sh`'s
`master-verbatim` check embeds the collapsed paragraphs with those
counts and `master-placement` asserts each sits between the anchors
the brief named, so the blind checkpoint and my own checks test the
same property from independent copies. The script was rehearsed on a
scratch staging with the landed file (exit 0) and on the unmodified
base (exit 1, `master-verbatim` naming every missing paragraph), so
both branches are observed, not predicted (§6 entry 138).

## Calls to ratify

- **Bullet spacing.** The brief separates block A's, D's, and G's
  bullets with blank lines; §3, §5, §7 and the registry run bullets
  without them, and close-8's identical call was ratified at the
  open. Followed the doc. Block B's rows and block E's entries keep
  a blank line between items, as §4 and §6 do.
- **Growths bracketed, as briefed.** Block C's five growths and the
  two registry notes land inside `[…]` because the brief's bytes are
  bracketed this time; nothing was added or removed.
- **A second bracket on the includes-as-scope entry.** That registry
  entry already carries `[2026-08-31: consumed — landed as a rider at
  … board-60 …]`. The brief's `[2026-09-15: closed at … board-90 …
  nothing to fix.]` note now sits beneath it as a second bracket. Not
  a conflict — the earlier bracket covers the `--read-only` and
  `--supersedes` bullets, the new one the include bullets — but the
  entry now reads as consumed twice, and block A's registry-deltas
  bullet says the same. If the desk would rather the note read as a
  confirmation than a consumption, that is a desk sentence.
- **The registry list's end.** In the shipped base the list's last
  entry runs straight into the line "Landed 2026-08-05, non-board
  (…)" with no blank line between them (a pre-existing quirk from an
  earlier landing). The four new entries went in ahead of that line
  and the missing blank line was left as it was — adding one would
  be a byte the brief did not carry, and every hunk is pure
  insertion.
- **One paragraph lands a third time by coincidence.** Block A's
  "Ratification debt carried forward" bullet is, whitespace collapsed,
  identical to close-7's and close-8's. The landed doc contains that
  string three times; `master-verbatim` asserts the count of 3.
- **Two count mismatches inside the brief's own prose, left alone.**
  The manifest goal and block A's "Board deltas" bullet say "rows 47,
  77 grown" and "five row growths"; block C carries five (47, 77, 89,
  90, 95). Block A's "Board deltas" bullet names four §7 items; block
  F carries five (the bare-apply cost mechanism is the fifth). Landed
  all of it as briefed; nothing in the text is wrong as a landing,
  and the goal string is not in MASTER.md.

## Places to look at review

- Header, line 14: the only removed line.
- Block A's opening paragraph wraps `close recorded by` and the sid
  onto two lines, as close-8's block does.
- Block F's five bullets sit between the 0.4.30 landmark and the
  pack-machine-clock bullet — the brief's stated position, so §7's
  landmark bullets are adjacent; the four 2026-09-15 facts that
  close-8 landed follow them.

## Not asserted in validation.sh

The pure-insertion property (nothing outside the placements changed)
was verified at build time by diffing against the shipped base; the
base bytes aren't in staging, so `validation.sh` asserts the header,
placement, and verbatim only. Bale's `base_files` stamp catches base
drift on its own.
