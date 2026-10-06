# notes — 2026-10-06-sitting-close-deltas-21-004

Close 21 is in `claude/MASTER.md`, one file: 636 lines inserted in
thirteen blocks, plus the `Last landed by:` line edited in place.
`validation.sh` removes exactly those blocks, restores the header line,
and hashes the result to the request's base sha256 (`b1ed2936…ddf2`).
It passed that way in a simulated staging tree. On the unmodified tree
every session assertion failed, which is what they should do.

My base matched the close desk's carried copy: 13,305 lines,
`b1ed2936…ddf2`, header naming close 20. `provenance.base_files` stamps
the same hash, so nothing landed in §1, §2 or §8 that the desk didn't
know about.

## Where each of the brief's nine outcomes landed

1. **Header**, line 14: `Last landed by:` names this sid.
2. **The cleanup desk's wave**: one §3 block after close 20's
   cleanup-desk block, in close 20's form. It covers:
   - each of the four landings, field by field from its record;
   - the desk's `closed-read-only` at 19:11:36Z by the close desk's pack
     (`swept_by`);
   - the light-block ledger in the desk's words, with the dating note
     on close 20's "light blocks 0; probes 1";
   - the workers' `clarification.rounds` and `light_blocks`;
   - pointers to every ratification and routing.
3. **Ratifications**, in that block. All 27 decisions (5, 7, 8 and 7)
   are named by their own heading or lead-in, verbatim, and close 20's
   §7 bullet is kept.
4. **Rulings**: one §5 block at the end. Light blocks two and four are
   verbatim, with rows joined by " / ". Two headed bullets cover the
   rulings I judged contract-level: the warning-only board rows, and the
   bump as its own version.
5. **Routings**:
   - **Ruling queue:** three entries after the BALE.md entry.
   - **Registry riders:** four at the list's end, above `Landed
     2026-08-05, non-board`: the y/N keyword, the FORCE queue, PackWalk,
     and `contract-doc`.
   - **The dispositions entry:** covers all thirteen Proposals. The
     alias retirement is carried verbatim as record only.
   - **BALE.md sets:** the three new sets sit inside close 20's 99b
     routing entry as a dated bracket, so all eight sets have one home.
   - **Board:** rows 134 and 135, verbatim, warnings only. Row 134 says
     it is the row entry 223 lacked.
   - **Consumed brackets:** the non-exiting accessor, D's help-suite
     and internals rider, the `bale status` row, and close 20's
     dispositions entry.
6. **Watch**: the rename's decision 2 split, the second paragraph
   verbatim, with the brief's re-trigger and remedy. Close 20's four
   watches are untouched.
7. **§6 entry 224**: the missed changelog obligation. It cites `CODE.md`
   §8.5 by name and number, quotes its sentence, and carries the cleanup
   desk's words and the desk-side attribution the brief gave.
8. **The close desk's block**: §3, after the wave block. It is Appendix
   C flattened, and names the bump as dispatched by its stem with the
   three full hashes.
9. **§7**: one bullet. It has the bumpless version with 0.4.46
   dispatched, the suite counts, TARBALL.md's hash movement, the
   `bale.toml` spelling, the four model identities and this base.

Beyond the nine I added a bracket on row 99, as close 20 did. 99b's
inputs grew again, and the key 99a landed as `[probe]
clipboard_command` is now the legacy spelling. It is one insertion, so
cutting it is one block.

## Decisions to ratify

- **The §5 block is dated "by 2026-10-06", with the bounds spelled
  out.** The records don't date the operator's answers. Block two came
  after close 20 applied (2026-10-05T01:03:02Z), and block four after
  convergence applied (2026-10-06T19:07:41Z). I first wrote
  "2026-10-05/06" in the 2026-10-03/04 block's style. The reviewer
  pointed out that the "05" half is a guess, so the heading now says
  what the records support.
- **The three new BALE.md sets go inside close 20's routing entry, as
  a bracket**, not as a new entry at the list's end. The brief allowed
  either. Inside keeps all eight 99b sets in one home. The bracket also
  notes that C's and D's sentences predate the rename's spelling.
- **The `bale status` relabel is recorded as consumed without reading
  `bin/bale_report.py`.** The brief said to check that file, but it
  didn't ship in this request. The evidence I used instead:
  - the rename's decisions 3 and 4;
  - its record's agreed assertion "status row label and json clipboard
    object";
  - the shipped internals file, which says the row reads
    `clipboard_command_reading`.

  The bracket says the file's bytes were not read here. A probe would
  settle it, and I judged that not worth a round trip at a close,
  which is close 20's call on a similar point.
- **D's help-suite and internals rider is recorded as consumed at
  log-hold**, after checking the shipped internals file as the brief
  asked. It carries cluster 20 (`cmd_clipboard`, `bin/bale` banner
  section 30) and the `bale_report` paste-block copy paragraph.
  Log-hold's record lists both paths in `change_paths` and the rider's
  assertion in `validation_will_run`.
- **Headed §5 bullets for two rulings only**: block two [3] and block
  four [2]. Both change something beyond routing: a new warning surface
  and a minted version. The ratifications and routings get a pointer
  bullet, not headed bullets.
- **The ratifications name all 27 decisions in one bullet.** Each is
  quoted with its number, which makes the bullet long. A table would
  have been easier to scan, but the §3 blocks are prose bullets
  throughout, so I kept to that.
- **`contract-doc` sits in the close desk's deltas, not the wave's.**
  It is that desk's rider, and the reviewer caught me counting it in
  both blocks.

## Where the brief and the records part

Nowhere on the records. Everything the brief's table and Appendix C
state about the four records and the cleanup desk's record held:
- times
- checkpoint and worker states
- stamps and admissions
- the decision counts
- `light_blocks`
- `swept_by` and the closure time

Two things rest on the brief's word, and the blocks say so: the close
desk's own `packed_at` (no record of that desk shipped) and the tags
(no record carries one). The cleanup desk's record reads top-level
`outcome: unlocked` with `closure_reason: closed-read-only` on `command:
pack`. The wave block records both, so nobody reads "unlocked" as an
operator unlock.

## Validation

- `validation.sh` was run in a simulated staging tree:
  `claude/MASTER.md`, the four archived notes.md under
  `claude/responses/`, `docs/CODE.md`, and the manifest as
  `.bale-manifest.json`.
  - With the change, every check passes, exit 0.
  - On the unmodified tree, the reversal, header, §6 numbering, board
    numbering, anchors and verbatim checks all fail, exit 1.
  - File syntax passes on both, as a mechanical guard should.
  - The claims are `observed`.
- The insertion ledger is embedded, as close 20's was. The script
  writes `checks.py` and a run log under `.validation-logs/<ts>/` and
  says so on its first line. Its size (about 70 KB) is the ledger.
- **Verbatim, by construction and by check:**
  - Every transported text was lifted from its source bytes by line
    range and flattened (list markers dropped, whitespace collapsed),
    never retyped. That covers the thirteen Proposals' carried texts,
    the watch paragraph, the 27 headings, both light blocks row by row,
    the Appendix C and D passages, and CODE.md §8.5.
  - The script checks 70 quotes against `claude/MASTER.md`. The 42 from
    notes.md and CODE.md are also checked against the tree's own copies.
  - The brief isn't in the tree, so the brief-sourced quotes are
    checked for presence only.
  - One whitespace-visible change: convergence's `` `noun=
    "suggestion"` `` was wrapped inside its backticks in the source, and
    lands as `` `noun="suggestion"` ``.
- §6 runs 10 to 224 and the board 1 to 135, both contiguous.
- A separate reader who hadn't seen the drafting checked the insertions
  against the five records, the four notes.md, the brief and MASTER.md.
  It recomputed every interval, count, hash and boolean, and all held.
  It found five slips, all fixed before packing:
  - the §5 date (above);
  - the wave block and §5 disagreeing on that date;
  - a §5 sentence describing the bump's rows as if they had landed (it
    now says the bump's brief asks for them);
  - `contract-doc` counted in both blocks' deltas;
  - a rider assertion cited to log-hold's `validation.sh` when its
    source is the record's `validation_will_run`.
- The response lint is clean with `--request`.
- Line width: inserted prose wraps at 72. The long verbatim quotes are
  re-wrapped too, so no inserted line runs past 72.

## Light-block ledger for this close

Zero light blocks, zero probes, zero clarification rounds.

## Things I'm unsure of

- Whether you want the row-99 bracket and the §7 bullet. Each is one
  removable block.
- §5's 2026-10-03/04 block still says log-hold was "applied by the
  brief's word; recorded by the next close". This close records it in
  §3. I didn't bracket the §5 line, because the brief's outcomes don't
  name it. §5 does carry an occasional dated bracket (two exist), so if
  you want one there, it is a single added line.
- `model_identity` is the configured id, `anthropic:claude-opus-5-5`.
  This surface says the serving model can differ.
