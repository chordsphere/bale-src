# notes — 2026-09-20-sitting-close-deltas-14-002

Sitting close 14 landed into `claude/MASTER.md`: the
`2026-09-19-continue-plan-009` sitting. There is one in-place edit, the
header's last-landed-by line (line 14). Everything else is an insertion:
366 lines against the stamped base (`522152da…`). Close 13's second block
and notes.md were the shape model. The pinned line shapes are where the
brief put them:

- One `Landed 2026-09-19, the continue-plan-009 sitting (master` block
  ends §3. It closes on sequencing, then board deltas, then registry
  deltas.
- `  [2026-09-19: consumed at ` on the `CLI_PATH` registry entry. The four
  new entries end the list in the pinned order, directly before the
  2026-08-05 line.
- Rows 37 and 113 end on a `    [2026-09-19: ` bracket, row 104 on a
  `    [2026-09-20: ` bracket. §4 still ends at row 113.
- Entries `171. **` through `176. **` end §6. 176 is the optional sixth.
- Four bullets end §7, and the first opens
  `- Version landmark: unchanged at 0.4.37`.

This session's turn was split by a tool-use pause, after `manifest.json`
was filled and before any rehearsal. That was a pause, not a compaction:
context stayed intact. Everything after it was run on the final bytes:
the rehearsal, the lint, the mechanical block, and the hash, which the
lint recomputed.

## Where the brief and the records or notes.md parted

The records won in each case below, per the constraint.

1. **113's claims at apply.** The brief says "every claim `agree`". 113's
   record shows six `agree` and two `n/a`: the two `--slow` checks (full
   discovery, every suite dotted per process) were claimed pass and
   skipped at apply. The landing record says so.
2. **The desk's init, four lines or five.** The 009 desk's brief, quoted
   by this brief, says "a five-line `tests/__init__.py`". 113's notes.md
   says it shipped "the desk's four lines plus a docstring".
   - The verbatim quote in the block keeps "five", because it is a quote.
   - The next sentence of the block says four, and so do entry 172 and
     row 113's bracket.

Everything else the brief states from the records checks out:

- the `packed_at`/`created_at` values for 010 and 011, and the 11-second
  gap between them;
- the apply times, about twenty hours after packing (20h05m and 20h22m);
- one attempt each, checkpoint PASS with the stamp matched, worker PASS;
- 011's two prompt admissions and its `change_paths`;
- 009's `created_at` of 03:12:21Z and its `closed-read-only` pack at
  2026-09-20T00:17:07Z;
- 006's close at 03:12:18Z;
- the `reconciliation_parsed` pattern across closes 11, 12 and 13.

I also checked two of the brief's doc claims against the shipped
`TARBALL.md`, and both hold:

- §5.6.1 names `tools/craft_response.py --kind bailout --write`;
- the stale §5.8 sentence reads as quoted.

## Judgment calls to ratify

- **Entry 176, the sixth evidence entry.** I took it. The findings:
  - Close 11's and close 13's apply records read
    `reconciliation_parsed: false` with an empty `claim_verdict`.
  - Close 12's and 113's parsed.
  - Close 13's notes.md says it did not run the crafter. Close 12's
    `docs_read` lists the crafter.

  That correlation is suggestive, not proven, and the entry says the
  records don't give the cause. My own reconciliation block is the
  crafter's emission, pasted unchanged, and my labels carry no colons of
  their own. Close 12's labels had colons and still parsed, so colons
  aren't the cause either; I just removed a variable. If this close parses
  at apply, that is one more data point for 176.
- **Block bullet order.** The order is:
  1. the landing record;
  2. the open's ratification (a pointer only, per the brief);
  3. 113's dispatch;
  4. desk verification;
  5. the pauses;
  6. the light block and the 2026-09-20 ruling;
  7. the two notes.md rulings;
  8. the re-scopes;
  9. ratification debt;
  10. sequencing;
  11. board deltas, then registry deltas.
- **The light-block bullet.** It summarizes the three questions in
  shortened form and quotes each reply separately, verbatim. The inner
  double quotes in reply 2 are kept (close 13's item 9 practice).
- **Where the collision cut is dated.** Row 37's bracket is pinned to
  2026-09-19, but the `docs/TARBALL.md` cut happened on 2026-09-20 at the
  001 desk. The bracket keeps its pinned date and dates the cut in its
  text.
- **Entry 173 counts specimens.** It calls itself entry 163's class,
  with the desk's second pause and close 13's worker pause as further
  specimens, rather than numbering them.
- **Entry 175 states a rule:** "A desk that emits a block and gets an
  apply report back re-asks the block." Drop the sentence if you'd rather
  the entry stay descriptive.
- **Entry 171 attributes the miss** to "Desk-side, the 006 and 009
  sittings". The brief doesn't say which three desks grepped. Correct the
  attribution if it was different desks.
- **Registry "accepted at the 009 sitting".** The four new entries say
  they were accepted there, by [3] ratified as assumed. The
  `test_craft_response.py` conditional ("if row 37's cut holds that
  file") is this brief's wording.

## Taken on the desk's word (nothing shipped lets me check)

- 009's pack second, 03:12:19Z;
- the 001 desk's own `packed_at` of 00:17:07Z;
- both pauses;
- the light-block exchanges and the ruling's wording;
- the in-process `read_bundle`/`compose_pack_argv` gate check;
- the 009 desk's verification of rows 37 and 104 on the tree;
- closes 6–10 parsing their reconciliation.

## Validation

I rehearsed `validation.sh` in a scratch git repo:

- HEAD held the base `MASTER.md` and the six shipped records.
- There were `{}` stubs for three sids already cited in the doc but not
  shipped. Only `…-110-held-admissions-007` is cited in my insertions,
  and the brief says its record exists in the tree.
- The `files/` overlay was applied and the manifest placed as
  `.bale-manifest.json`.

All ten checks PASS, every claim `[agree]`, exit 0. The sid check prints
its two tolerances by name: this session and
`2026-09-20-continue-plan-001`.

I also ran three negative rehearsals:

- One existing line in row 37 altered → insertions-only FAILs, naming
  base line 3215.
- The board-deltas bullet's opening altered → the block check FAILs.
- HEAD not the base → insertions-only SKIPs by name, and the script
  exits 0.

The other checks don't depend on git. They locate the new text by
structure, so they run even when HEAD isn't the base.

The request's two tools:

- I read `tools/craft_response.py`'s header, imports, write sites and
  the tail of `main()` before running it.
- I read `tools/response_lint.py`'s header and imports.
- Both are stdlib-only and neither touches the network. The crafter
  writes only under `--write`, into the response directory. The lint
  writes nothing.
- The crafter produced the manifest skeleton, `apply.sh` and the
  epilogue fragments. The lint is CLEAN, and its mechanical block was
  pasted in unedited.

No Proposals.
