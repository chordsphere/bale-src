# Notes — 2026-08-26-board-53-close-deltas-005

## Derived-from-bytes facts (per the brief's ground rules)

- `<VERSION>` filled as **0.4.17**, read from `context/bin/VERSION`.
- The -004 attempt shape, read from
  `claude/telemetry/2026-08-26-board-53-amend-checkpoint-004.json`:
  **one attempt, outcome `applied`, validation PASS, checkpoint PASS,
  `stamp_matched: true`** — a single applied attempt, so the brief's
  "DONE — ... at <VERSION>" framing stands unmodified in groups A and
  B. No HOLD→retry substitution was needed.

## Deviations from verbatim, flagged

1. **Group B's anchor doesn't exist in the shipped bytes.** The brief
   says to append the §3 block "after the harness spec-intake block",
   but §3 has no landed block for the harness spec-intake sitting —
   its records live in §5 (the 2026-08-25 block) and on the board-10
   row bracket; §3's landed blocks end with the continue-plan-003
   block. I landed the new block at the end of §3's landed blocks
   (after continue-plan-003, before §4), which is its chronological
   position under the section's own ordering. If the intent was
   somewhere else, say so and I'll move it.
2. **Two brief-internal cross-references reworded.** Group B's text
   contains "(delta group E below)" and "(delta group F)" — pointers
   into the brief's own structure that would dangle inside MASTER.md.
   Landed as "(its 2026-08-26 bracket)" and "(the §3 watch)"
   respectively; every other word of the block is verbatim.
3. **Re-wrapping only, otherwise verbatim.** All delta texts were
   re-wrapped to the doc's ~72-column convention with sids kept on
   their own unbroken lines; indentation follows each landing site's
   local style (4-space row continuation for the row-53 bracket and
   §6 entries, 2-space bullet continuation elsewhere).
4. **Group F lands as an in-bullet continuation.** The watch entry's
   first and second data are sentences inside the one bullet, so the
   third datum continues the same sentence flow directly after
   "watch stands." rather than opening a new bullet — that is the
   entry's accrual style the brief named.
5. **Group G's displaced parenthetical dropped, not reworded.** The
   0.4.16 line's parenthetical (rider bump detail) is gone per the
   brief's "needs no preservation"; the per-bump-trail sentence's
   lines are byte-identical to before, so the diff there is exactly
   three lines replaced by two.

## Review pointers

- The whole change is one file, `claude/MASTER.md` — the declared
  write forecast, no out-of-forecast paths.
- Top-level section headings are unchanged (asserted in
  validation.sh check 1 against the shipped heading set verbatim).
- Claims carry `claim_basis: "observed"` — validation.sh was run
  against a staged copy of the edited doc before packing, all three
  checks PASS.
