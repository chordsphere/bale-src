# notes — 2026-09-19-sitting-close-deltas-13-010

Sitting close 13 landed into `claude/MASTER.md`. There is one in-place
edit, the header's last-landed-by line (line 14). Everything else is
an insertion: 407 lines added against the stamped base (`5bc53cce…`).
`validation.sh` proves that shape against `git HEAD` when HEAD holds
the stamped base, and SKIPs the three diff-derived checks by name
otherwise. Close 12's block and notes.md were the shape model. The
pinned line shapes are at column one where the brief put them:

- Two `Landed 2026-09-19` blocks end §3: 002's sitting first, then 006's.
- `112. **` and `113. **` follow row 111 and end §4.
- `New, ratified 2026-09-19` ends §5, over four contracts.
- `164. **` through `170. **` follow entry 163 and end §6.
- `- Version landmark: 0.4.37 (` is in §7.

Every row check in `validation.sh` is scoped to §4, since §6's entries
112 and 113 share the `NNN. **` shape.

This session's turn was split by a tool-use pause just before packing.
That was a pause, not a compaction: context stayed intact. The last
edit before the pause changed the file's bytes, so the manifest's size
and sha256 were recomputed after it. The rehearsal and the lint were
re-run on the final bytes.

## Where the brief and the telemetry records parted

The records won in each case below, per the constraint.

1. **Wave-5 pack instants.** The brief gives 110 as packed 02:29:07Z
   and 111 as packed 02:29:48Z. Those are the records' `created_at`
   values. Each record's `provenance.packed_at` reads one second
   earlier: 02:29:06Z and 02:29:47Z. The landing-record bullet uses
   `packed_at`. The "41 seconds apart" statement still holds.
2. **The 006 master's pack second.** Its record reads `created_at`
   02:09:04Z and carries no `packed_at`, as the brief said.
   - Close 12's item 3 treated a one-second pack-to-record lag as the
     norm. This sitting's records show that lag is not constant:
     - 004 and 005 have `packed_at` equal to `created_at`;
     - 007 and 008 lag by one second.
   - So the heading says "opened 2026-09-19T02:09:04Z per its record"
     and does not name a pack second.
3. **Who swept 002, and who swept 006.** No record names which pack
   closed which master:
   - 002's closing attempt is a `pack` at 02:09:02Z, two seconds
     before 006's record was written;
   - 006's closing attempt is a `pack` at 03:12:18Z.

   Block A therefore says 002 was closed "by a pack two seconds before
   the 006 master's record was written". Block B says 006 was closed
   "by a pack, the 009 pack by the desk's account". The brief's
   attributions are very likely right; the records just don't carry
   them.
4. **The gap after 003's split.** 003 closed `superseded-by-split` at
   01:26:54Z, and its record's `superseded_by` names 004. But 004's
   record opens at 01:36:19Z, nine and a half minutes later. The brief
   does not mention the gap. Entry 165 states it and does not guess at
   a cause, as the brief asked for the series-not-beside question.
5. **Sitting-open version.** I can't see 006's request. Both of its
   workers' provenance stamps read 0.4.36, so the heading says both
   things (close 12's item 4 form).
6. **"Answered in five words."** "As assumed on both." is four words.
   Entry 169 says four.

Everything else the brief states about how the five sessions landed
matches the records and the four workers' notes:

- open, apply and close times;
- one apply attempt each, checkpoint and worker PASS, no HOLD;
- 110's two prompt admissions;
- the untouched forecast files;
- 003's forecast equal to the exact union of 004's and 005's;
- 0.4.37 and its changelog record's session id;
- bumpless under 0.4.36 for 004, 005 and 008.

## Where the brief and the doc parted (not telemetry; flagged anyway)

7. **The `_section_29` renames are already recorded as done.** The
   brief closes the registry entry "as stale". But the neighbouring
   entry (the section-29 string literal) already carries a 2026-09-16
   bracket, "consumed at …-011, with the two `_section_29` renames".
   The renames entry itself was simply never bracketed to match. The
   new bracket keeps "closed as stale" and the three greps, and points
   at that earlier bracket.
   - The 011 sid is not cited by name. That keeps the cited-sid check
     to records I could see on disk in this request.
8. **004's Proposal, one code span.** The notes.md source reads
   `` `feedback.self_reported` `` then `` `.docs_read` ``. That is a
   line wrap in the middle of a span. I joined it as
   `feedback.self_reported.docs_read` in the registry entry.
   Otherwise the quote is verbatim, with nested bullet markers
   flattened to inline bold markers (close 12's practice).
9. **111's Proposal 1 has quotations inside the quotation.** I kept its
   inner double quotes verbatim rather than converting them.

## Judgment calls to ratify

- **Block order.** The brief says "close each block with the
  board-deltas and registry-deltas bullets". Close 12's block ended on
  its sequencing bullet instead. I took the brief literally:
  - both blocks close on board deltas, then registry deltas;
  - block B's verbatim sequencing sits just before them;
  - `validation.sh` asserts that close.

  Block B's order is: landing record, the cut, desk verification, the
  light block, worker judgment calls, the 009-open ratifications (the
  sitting's last event), ratification debt, sequencing, deltas.
- **Block B's sequencing bullet gains one sentence.** After the
  verbatim quote it says that re-scoping rows 104 and 37 is the 009
  desk's ruling, recorded at close 14. That is the manifest's
  `out_of_scope` wording. Row 104's bracket says the same for 104 in
  the brief's one added sentence.
- **Where the deltas split.** "Which sitting's work each delta
  records":
  - **Block A:**
    - row 112;
    - row 104's consumed parts;
    - contracts one to three;
    - entries 164, 165 and 170 (170 is 004's pause, worker-side, in
      002's sitting);
    - the three-homes moot close;
    - 004's lint entry, though it was accepted at the 009 open.
  - **Block B:** everything else. The dispositions entry covers both
    sittings, and block B's registry bullet names it.
- **Where the §7 bullets sit.** The sandbox bullet sits directly under
  the scratch-repo checkpoint note, mid-§7, as the brief said "beside".
  The other four end §7 with the 0.4.37 landmark first, in close 12's
  manner.
  - **The dispatch-check bullet.** It repeats entry 166's rule rather
    than pointing at it, and adds "the pinning suite joins the
    forecast" from 166. It does not sit beside the older "Dispatch
    check, grown" bullet; consolidating the two is regeneration work.
- **Row 109's bracket omits "the completion pins".** Row 109 moved the
  class "with the completion pins". 007's notes say only "same four
  tests, same names", so the bracket says that and nothing more.
- **Homes for contracts three and four.** The brief gave no home for
  either, and §5 wants one:
  - the `readme` key → `docs/TARBALL.md` §3.2 (005's notes);
  - held admissions → BALE.md §8.8 (the 0.4.37 changelog record).
- **Row 113's closing sentence.** Its desk count is written as "The
  desk counts 55 suites …", so the number stays attributed.

## Taken on the desk's word (nothing shipped lets me check)

- 110's defect reproduction and the three-way checkpoint dry runs;
- the `OPENER_SHAPE_SENTENCE` grep;
- `resolve_write_forecast`'s `--read-only`-only `[]`;
- BALE.md carrying the scaffold comment;
- the three `_section_29` greps (111's notes confirm one of them);
- the 55-suite count;
- the `[sandbox] enabled = false` fact. 110's apply record does show
  `sandbox_confined: true`, which is consistent with it.

## Validation

`validation.sh` was rehearsed against a staging that mirrors the
target base:

- the base `MASTER.md` committed as HEAD;
- every shipped telemetry record committed (none exists for this
  session or for 009);
- the `files/` overlay applied;
- `.bale-manifest.json` placed.

All twelve checks PASS in about a second, and every claim agrees. The
cited-sid check prints its two tolerances by name, this session and
`2026-09-19-continue-plan-009`. The other nine cited sids each have a
record on disk.

I also ran four negative rehearsals:

- a HEAD that is not the base → the three diff-derived checks SKIP by
  name, exit 0;
- one existing line in row 110 reworded → insertions-only FAILs,
  naming the base line;
- a typo'd cited sid → the sid check FAILs, naming it;
- a stray `Landed 2026-09-19` line before close 12's block → the block
  check FAILs.

The request's two tools: I read `tools/response_lint.py`'s header and
`main()`, and grepped both files' imports and write sites. Both are
stdlib-only, with no subprocess and no network. The lint writes
nothing. I did not run the crafter; the manifest was assembled by
hand, with size and sha256 computed from the bytes.

## Proposals

- **What:** stamp `packed_at` into a pack's `opened` telemetry attempt,
  or into the record's top level.
  **Why:** closes 12 and 13 both had to reason about a master's pack
  second from `created_at`. This sitting showed the gap between them
  is sometimes zero and sometimes one second, so no fixed lag
  recovers it. Worker records carry `packed_at` only inside
  `feedback.mechanical.provenance`, which a read-only master never
  produces.
  **Scope hints:** `bin/bale_pack.py`'s telemetry open; the telemetry
  record schema. It is additive, and needs a named consumer per
  DOCS.md §9's telemetry rule: the close desk's reconstruction.
- **What:** when a pack closes a session as a side effect (the
  read-only sweep, a supersession close), stamp the closing pack's
  own sid on the closed attempt.
  **Why:** 002's and 006's closures are attributed to "a pack" in this
  close, because no record says which. The brief's attributions come
  from desk memory, which is exactly what an unrecorded sitting lacks
  (entry 164).
  **Scope hints:** the pack path's sweep and supersession close (in
  `bin/bale_pack.py` or `bin/bale`; I have not seen the code); one
  optional field on the attempt.
