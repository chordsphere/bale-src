# notes.md — 2026-08-31-board-64-65-close-rider-011 (corrected, for retry)

## The ruling, recorded

The first response landed 1 of 3 sentences and flagged S2/S3
(premise falsified: the shipped BALE.md already carried the board-64
documentation; S3's "naming its additions" contradicted the
count-only report row). The blind checkpoint HELD on exactly those
two probes, and the ruling arrived by chat relay:

- **S2: dropped.** Its content already sits in the §7.2 board-64
  bullet.
- **S3: replaced** by the desk's corrected sentence, verbatim:
  "When the `release-surface` group engages, pack output carries an
  include-group row."

This round resolved in chat rather than through the formal exchange
thread, so per the TARBALL.md §5.9.1 provenance fallback this file
is the durable record of the question and its answer. The feedback
block stamps it (kind=clarification, point=mid-build).

## What this response ships

Same session, `corrects` pointing at the first response. S1
unchanged in §5.6; S3' landed in §7.7 Output as its own short
paragraph beside the tree-position and checkpoint-identity echo
material ("near where pack output is documented"), with a bolded
lead-in matching the section's pattern — the lead-in is connective
prose, the sentence itself verbatim modulo hard wrap. S3' verified
against bale_pack.py before landing: `group_report` is set on both
engagement branches and the row is appended to the report whenever
it is set, so engagement ⇒ row holds.

## Check before accepting: the moved base

Main moved 64b68b4 → 6038941 under this session (the amended
checkpoint, presumably). This mirror's `files/BALE.md` was built
from the shipped base copy. If anything else in BALE.md changed at
the new tip, this whole-file mirror overwrites it silently —
reconciliation won't catch it because the manifest legitimately
declares BALE.md modified. `git diff 64b68b4..6038941 --stat`
settles it in seconds: checkpoint-only ⇒ clean; BALE.md in the diff
⇒ stop and tell me what landed, and I'll rebuild against current
bytes.

## Suite

Green on the corrected tree: 709 tests, 41 skips in my container
(your environment runs 40 — one tool present there that mine
lacks; environmental, not behavioral). No version-literal pin
reddened; the lone 0.4.19 in the suite remains fixture provenance
data in test_stats_linkage.py.

## Proposals

### Reconcile the lane record for board 64's doc cargo

**What:** Determine how the board-64 BALE.md documentation landed
while the lane record said it was deferred, and correct whichever
side drifted.

**Why:** This session's brief inherited the drift as a falsified
premise; carried forward it will misprice the next close rider too.
(Carried over from the first response — still open as far as I can
see.)

**Scope hints:** Planner-side; the pair's session records
(-009/-010) and the board/lane state. No code.
