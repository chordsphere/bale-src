# notes — 2026-09-17-sitting-close-deltas-11-007

## Re-attempt (corrects the held attempt of this session)

The first attempt HELD with the blind checkpoint 11/11 PASS and my own
`validation.sh` exiting 1 on "every cited sid has a telemetry
record": no record for `2026-09-16-continue-plan-006`. That sid is the
sitting's master, still open at pack; the request carried its
working-tree record, but target-base staging (`d61d6f5`) has no
committed one. The content was right and the check was wrong. My
rehearsal copied every shipped record into staging instead of
mirroring target-base, so it never produced this branch — §6 entry
143's lesson, repeated by the worker at the close that records it.

The fix is only in `validation.sh`. The check now tolerates by name the
two sessions open at pack — this one and the master — and prints each
tolerance as an `[info]` line. Every other cited sid must still have
a record on disk. I rehearsed against a staging with the master's
record removed: it passes, and a typo'd non-open sid still FAILs by
name. `files/claude/MASTER.md` is byte-identical to the held attempt,
so the checkpoint verdict carries over. `notes.md` and `manifest.json`
changed (this section, `corrects`, the self-report).

Sitting close 11 landed into `claude/MASTER.md`: one in-place line
edit (header line 14), everything else insertions. The second named
in-place edit (the "New, ratified 2026-09-16" heading) is an inserted
heading paragraph above close-10's two contracts, so the diff against
base removes exactly one line. Close-10-005 was the model for block
shapes; `validation.sh` proves the insertions-only shape against
`git HEAD` when HEAD is the stamped base and SKIPs by name otherwise.

## Where the brief and the telemetry parted, and what I did

1. **Row 108 closed before this pack.** The brief said to record
   guard-maintenance's outcome if it had closed. Its record shows
   `2026-09-17-guard-maintenance-006` applied, checkpoint PASS, at
   2026-09-17T13:01:19Z — 28 seconds before this request was packed.
   So the sitting record says it closed, and row 108 is written as the
   brief's row plus a DONE bracket from the record. I did not write
   "open at close". Its notes.md was never before the desk, so I
   queued its ratification to the next open rather than folding it into
   this brief's wholesale ratification. Please confirm that reading.
2. **106's attempt chain is longer than the brief's summary.** The
   record shows HOLD (02:35Z), HOLD on an unchanged retry (02:56Z),
   a rejected apply (11:53Z), HOLD (11:54Z), then the landing retry
   (11:58Z) on a changed checkpoint sha (`stamp_matched: false`, i.e.
   the v2 oracle under `--accept-checkpoint-change`). I kept the
   brief's wording and added one clause with the tally; nothing about
   causes, which the record doesn't carry.
3. **"105 proposals 1–3" by number.** The worker notes.md files weren't
   shipped, so I can't enumerate 105's three proposals individually.
   The dispositions registry entry names every proposal the brief
   names, each marked consumed or carried, and says anything else
   stands as shipped. If 105's third proposal is none of the brief's
   named items, that entry under-records it.
4. **Registry brackets beyond the brief's list.** The brief's dispositions
   implied changes to five existing entries, so each got a dated
   bracket rather than a duplicate new entry (one home): the dossier
   wiring (consumed, stats micro), `normalize()` (carrier row 109),
   pack-json `sweep`/`include_group` (carrier 47b), and the
   post-epoch fixture entry (gains the two records, named by path from
   the stats micro's `change_paths`). Two more I bracketed from
   telemetry rather than brief text: the light-tier INDEX-row rider
   (consumed at 105 — its validation ran "CLAUDE.md light-tier row
   names crafter path, hand fallback", and the injected CLAUDE.md now
   reads that way) and the crafter single-quoted clipboard rider
   (consumed at 69 — its judgment call says the single-quoted form is
   accepted). Strike either if the desk reads them differently.
5. **Row 44 bracket.** The brief says the row-44 dossier wiring was
   consumed; I bracketed row 44 as well as the registry entry so the
   row doesn't read as still waiting.

## Judgment calls

- The "New, ratified 2026-09-17" heading names the master by full sid,
  `2026-09-16-continue-plan-006`, because "the continue-plan-006
  sitting" already means 2026-09-14's elsewhere in this file. The
  09-16 heading uses close-10's own short form ("the continue-plan-009
  sitting"), which is unambiguous.
- Contract titles are mine, in the §5 bold-sentence style; bodies are
  the brief's rulings with a "Landed at row N" or §6 pointer where the
  brief or telemetry grounds one. The "bumpless-under" contract notes
  that 004 and 005 both flagged the term undefined — from their
  self-reported assumptions.
- No "Sequencing for the next desk" bullet: close-10 had one, but the
  brief rules no sequence, and inventing one would be writing without
  ground.
- The 0.4.35 version landmark is named in the board-deltas bullet only;
  §7 was not in the brief's section list, so no §7 line landed. If §7's
  version ladder should carry it, that's a one-line follow-up.
- Evidence entries carry close-10's attribution suffix ("Desk-side,
  this sitting." / "Worker-side, …"); where an attribution wasn't in
  the brief I chose by whose act the entry describes.

## Proposals

- **What:** add the 0.4.35 version landmark to §7 at the next MASTER.md
  touch. **Why:** every close since v5 has recorded its landmark there
  (close-10 recorded 0.4.34); this brief's section list omitted §7, so
  the ladder now lags one version. **Scope hints:** `claude/MASTER.md`
  §7 only; insertion.
