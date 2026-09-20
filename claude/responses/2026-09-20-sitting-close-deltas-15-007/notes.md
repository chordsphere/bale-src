# notes — 2026-09-20-sitting-close-deltas-15-007

Sitting close 15 landed into `claude/MASTER.md`. It covers the
`2026-09-20-continue-plan-001` and `2026-09-20-continue-plan-004`
sittings.

The header's last-landed-by line (line 14) is edited in place. Everything
else is an insertion: 596 lines against the stamped base (`77efdd47…`).
The model was close 14's block and notes.md, with close 13's two-block
split.

The pinned shapes are where the brief put them:

- **§3 blocks.** Two blocks, 001 then 004, sit between the 009 block and
  `## 4. The board`. Each closes on sequencing, then board deltas, then
  registry deltas.
- **The 004 block** carries:
  - the `- Ratified at the `2026-09-20-continue-plan-006` desk:` bullet;
  - the 004 desk's light block and "as assumed, and both applied:",
    verbatim;
  - the debt bullet, closing on the convention sentence.
- **Registry.** The pinned brackets are on their entries. The three new
  entries end the list in the pinned order, directly before the
  2026-08-05 line.
- **Board.** Row 37 ends on its DONE bracket. Row 104 has its second
  2026-09-20 bracket (`cut in two`), and row 99 has its bracket. §4
  still ends at row 113.
- **§5.** The calibration ruling ends on `  [2026-09-20: the fifteen is a
  hand count`. §5 then ends on the `New, ratified 2026-09-20 (` block
  with its two pinned bullets.
- **§6.** Entry 176 has its `close 14 parsed` bracket. Entries 177–187
  end the section, with no gaps.
- **§7.** It ends on four bullets, the first opening
  `- Version landmark: 0.4.39`.

The turn was split by one tool-use pause, after `validation.sh` was
written and before the manifest existed. That was a pause, not a
compaction, and my context stayed intact. On resume I rebuilt
`MASTER.md` from the base by the same script and got the same sha
(`e5b80f83…`). Everything after the pause ran on the final bytes: the
manifest, the rehearsal, the lint and the tar.

## Where the brief and the records parted

The records won in each case below, per the constraint.

1. **The 004 sitting did not end before its wave landed.** The brief says
   both sittings "ended before its wave landed". That is true of 001: it
   closed at 00:50:20Z, and its wave applied at 01:10:00Z and 01:16:21Z.
   It is not true of 004:
   - 104a applied at 02:35:51Z, and the 004 master closed at 02:41:52Z,
     six minutes later.
   - The 004 desk's own brief has a "104a landed" section.

   The 004 block's opener says the desk read 104a's notes.md and handed
   the close forward. A bullet names the parting.
2. **The 001 desk's standing line never reached me.** The brief asks the
   001 block's sequencing bullet to quote "that desk's standing line from
   its brief". Part 2 quotes the 001 brief only from "Wave 7, as
   dispatched" to the line before "Second job". The line is not in that
   range, and it is not in anything else shipped.
   - The bullet says so. It then quotes the line that did travel: the
     009 desk's, verbatim as close 14 records it.
   - The 004 desk's line is "verbatim from the 009 desk", so the 001
     desk's line was probably the same one. I did not attribute a quote
     I can't see.
   - Entry 177 takes this as its second specimen. If you have the 001
     brief, a one-bracket correction at close 16 fixes it.

Everything else the brief states from the records checks out:

- **37.** Four attempts. The failed-probe label is as quoted. Checkpoint
  exit 1 on the HOLD with the stamp matched, and worker exit 0. The
  `rejected` attempt used command `apply` on the ` (1)` tarball, with no
  cause, no validation and no admission. The retry has `corrects` set to
  its own sid. Nine claims parsed on both scored attempts.
- **Close 14.** Opened 00:49:57Z and applied 01:10:00Z in one attempt.
  Ten claims, all `agree`, parsed. `claude/MASTER.md` alone.
- **104a.** `created_at` is one second after its `packed_at`, with a
  0.4.38 stamp. Seven `change_paths`, eleven claims, parsed.
- **The two masters.** 001 opens one second after its brief's
  `packed_at`. It closes at 00:50:20Z, the second 004 opens.
- **Stamps.** 37's and close 14's provenance stamps are both 0.4.37.
- **Checkpoint shas.** 37's (`1713fb62…`) and close 14's (`87a18ffd…`)
  match the 001 desk's delivery record.

## Judgment calls to ratify

- **Entry 187, the rejected attempt: taken.** The entry gives two
  readings the record fits and does not pick one:
  - the corrected tarball given to `apply` where a held session wants
    `retry`;
  - the new suite refused for want of an admission.

  The session log would settle it. Proposal 1 below is the remedy.
- **Four brackets the brief did not pin.**
  - Stale-comment entry: consumed at 104a. The brief's dispatch rulings
    say so, but it pinned no bracket.
  - Path-guards entry: 37 did not hold `tests/test_craft_response.py`,
    so the guard rides that file's next holder.
  - The older "Pack-json `sweep` key" entry (§3, ~line 402): pointed at
    the newer `sweep`/`include_group` entry. It is the same work, and a
    desk reading only the older one would still see "row 104".
  - 105's stdlib-only pin: bracketed with its carrier unconfirmed. The
    004 desk's cut put it in 104b, but the 006 desk's dispatch names
    three other entries for 104b and not this one.

  None of these reuses the pinned phrases "carrier now 104b" or
  "consumed at" in a way that would change the count on the pinned
  entries. One exception: the stale comment does use "consumed at", on
  its own entry.
- **The 006 desk's rulings recorded.** The manifest puts "the
  2026-09-20-continue-plan-006 sitting beyond its one ruling" out of
  scope. The brief pins the 104b dispatch brackets and the reworded ride
  condition, which are that desk's dispatch-check rulings. I followed the
  brief, since the same desk wrote both. I kept 006 content to what the
  pins require: no 006 block, no 104b landing record. Say if you read
  the line more strictly.
- **Entry 179.** It merges the two answered-first-time candidates, as
  asked. I added the 006 desk's own block as a counter-specimen: three
  questions, answered first time at a named pause. So "one question,
  alone" is not the whole story. The entry says the records don't say
  what the variable is.
- **Block split.**
  - 001 block: 37, close 14's parse (176), entries 177–181, the §5
    hand-count bracket and the stats contract.
  - 004 block: 104a, row 104's cut, entries 182–187 and the
    context-pack contract.
  - Both: 179 and the §7 landmark.
- **One-line verbatims.** "as assumed, and both applied:" in the 004
  block and the debt bullet's convention sentence are each on one
  physical line, the latter at 105 characters. §6 entry 176 already has
  a 96-character line. I chose this so a raw-substring probe finds
  them. Rewrap if the width bothers you.
- **Row 37's bracket** says the §11.4 pointer was not built, "as the
  bracket above allowed". 37's forecast did not hold `docs/CLAUDE.md`.
- **The post-epoch bracket** notes that 37 changed one whole-dict
  expectation. It records that as not meeting the condition, which is
  the worker's reading, ratified by [1]. A stricter desk could argue the
  change touched the expectations. It added no fixtures, though, which
  is the entry's point.

## Taken on the desk's word (nothing shipped lets me check)

- These seconds: 001's `packed_at` (00:17:07Z), 004's `packed_at`, and
  006's (02:41:53Z).
- The pack that closed each master.
- Every desk's pauses, light blocks and replies, including the operator's
  "as assumed" to the 006 block.
- Both desks' oracle anchor and probe counts and their rehearsals.
- The 006 desk's code read on `superseded_by` since 0.3.23.
- 104b's forecast and dispatch stem, `2026-09-20-board-104b-pack-telemetry`.
- The 26 bare-bool fixture records.
- The 001 desk's 274.

## Validation

`validation.sh` runs ten session-specific assertions. The
reconciliation block is the crafter's `--validation-epilogue` emission,
pasted unchanged. The labels are plain ASCII: I spelled "§" as "section"
and swapped a semicolon for a comma, to take variables out of entry 176.

I rehearsed it in a scratch git repo:

- HEAD held the base `MASTER.md` and all eight shipped records.
- The `files/` overlay was applied, then `apply.sh` ran, and the manifest
  was placed as `.bale-manifest.json`.

All ten checks PASS, every claim `[agree]`, exit 0. The sid check
tolerates this session and `2026-09-20-continue-plan-006` by name.

Negative rehearsals:

- One existing base line altered → insertions-only FAILs, naming base
  line 3705.
- The 001 block's board-deltas bullet reworded → the §3 check FAILs.
- HEAD not the base → insertions-only SKIPs by name, and the script
  exits 0.

The other checks locate the new text by structure, so they don't need
git.

The tools: I read the crafter's header, imports, write sites, `main()`
tail and `--help`, and the lint's imports. Both are stdlib-only, with no
network. The crafter wrote only `manifest.json` and `apply.sh`, under
`--write`. The lint writes nothing.

## Proposals

1. **Stamp a cause on a `rejected` attempt.**
   - What: when apply refuses a tarball, record why on the attempt, e.g.
     the refusal's first line or a short code.
   - Why: 37's `rejected` attempt carries no cause, admission or
     validation. Close 15 had to leave it as two readings (§6 entry
     187), and it is entry 174's gap on the apply side.
   - Scope hints: the apply refusal path and the telemetry record schema.
     It is additive. Named consumer: the close desk's reconstruction,
     per DOCS.md §9's telemetry rule. I haven't seen the code. It would
     sit naturally beside 104b's `packed_at` and closing-pack-sid
     riders, but 104b is pack-side, so this probably wants an
     apply-side carrier.
