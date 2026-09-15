# notes.md — 2026-09-15-sitting-close-deltas-8-003

Landed as briefed: the header edit plus seven pure-insertion hunks
in `claude/MASTER.md`, nothing else. The diff against the shipped
base has exactly one removed line (the old `Last landed by:` line)
and 281 added lines. Verified at build with difflib: every non-equal
opcode is `insert`. `bin/VERSION` untouched at 0.4.30.

## How verbatim was kept

The landing text was never retyped. A script slices each `### Block`
out of the brief's README.md by header, substitutes `<your-sid>`,
and wraps with `textwrap` at width 70, `break_on_hyphens=False`,
`break_long_words=False`. I also masked the spaces inside backtick
code spans before wrapping so a span like `` `date -u` `` never
straddles a line. Checked afterwards: all 150 hyphen-bearing tokens
and code spans from the brief sit intact on a single output line, and
every landing paragraph appears in the landed doc exactly once with
whitespace collapsed (once each, except the one noted below).
`validation.sh`'s `master-verbatim` check embeds the collapsed
paragraphs with their expected counts, so the blind checkpoint and
my own check test the same property from independent copies.

## Calls to ratify

- **Bullet spacing.** The brief separates block A's, E's, and G's
  bullets with blank lines; MASTER.md's convention (close-7's block,
  §5, §7) runs bullets without them. I followed the doc, under
  "whitespace is yours". Block B's rows and block F's entries keep a
  blank line between items, as §4 and §6 do.
- **Row growths start on a fresh line.** Blocks C and D are appended
  to rows 91 and 84 as new 4-space-indented lines directly after
  each row's last line, the way row 84's existing bracketed growth
  starts on its own line. Neither growth is wrapped in `[...]`; the
  brief's bytes aren't bracketed and adding brackets would be adding
  bytes.
- **Block E has no "New, ratified 2026-09-15" preamble.** §5's
  earlier landings each open with such a line; the brief's block E
  is two bullets only, so the two 2026-09-15 contracts land under
  the 2026-09-14 preamble's list. If you want a preamble, that is a
  desk sentence, not something I should author under a VERBATIM
  brief.
- **One paragraph lands twice by coincidence.** Block A's
  "Ratification debt carried forward" bullet is, whitespace
  collapsed, a prefix of close-7's identical sentence. The landed
  doc therefore contains that string twice (once pre-existing, once
  new) — expected, and `master-verbatim` asserts the count of 2.
- **Block G is five bullets, not four.** The manifest goal and the
  §3 board-deltas bullet say "four standing facts"; block G carries
  five (version landmark, pack-machine clock, include-authoring
  rule, "applied" report convention, registry-riders-at-dispatch).
  Landed all five, as briefed. Nothing in the brief's text is wrong
  as written — the goal string's "four" is the only mismatch, and
  it is not in MASTER.md.

## Places to look at review

- Header, line 14: the only removed line.
- Row 94's body carries one unbreakable 73-column line
  (`HandoffBlindnessGateTest.test_handoff_empty_plan_whole_tree_refuses`).
  Every other added line is within 72.
- Block A's opening paragraph in §3 wraps `close recorded by` / the
  sid onto two lines, matching close-7's block exactly.

## Not asserted in validation.sh

The pure-insertion property (nothing outside the placements changed)
was verified at build time by diffing against the shipped base; the
base bytes aren't in staging, so `validation.sh` asserts placement
and verbatim only. Bale's `base_files` stamp catches base drift on
its own.
