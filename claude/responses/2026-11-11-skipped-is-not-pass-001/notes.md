# Notes: 2026-11-11-skipped-is-not-pass-001 (bale 0.4.57)

Both slips are done. The crafter's epilogue now tags a pass claim beside a
skip or an unrecorded verdict `[DISAGREE]`. At apply, bale names each such
check in the walk and in the planner relay and prints `N of M checks ran`.
bale also puts the response's notes.md into staging as `.bale-notes.md`
before validation.sh runs. Nothing changes an exit code or a verdict. A
validation.sh that exits 0 with skipped claimed checks still lands PASS
and merges; the difference is that you are now told.

Everything is inside the forecast. No out-of-forecast paths, nothing to
admit.

## Decisions for you to ratify

These are the open choices the brief left to me, and one more:

1. **A `fail` claim beside a skip or a missing verdict stays `[n/a]`.** I
   took the sitting's guess. A deliberate failure that never ran hides
   nothing; the danger the slip names is a false PASS. Both twins and
   TARBALL.md 7.3's table say this.

2. **bale derives agreement itself for the walk and the relay. The record
   keeps the printed tag.** This is a split, and it's the call I'd most
   like you to look at.
   - The walk and the relay read the table from the manifest's claim and
     the row's verdict (`bale_report.claim_agreement`). A printed
     `[DISAGREE]` is also honoured, so a hand-rolled block can't be
     downgraded. That means a validation.sh made with an older crafter,
     which prints `[n/a]` beside a pass and a skip, is still named. The
     line then adds `validation.sh tagged it [n/a]`, so you can see where
     bale and the script differ.
   - The telemetry record's `claim_verdict[].agreement` stays exactly what
     the script printed (`parse_claim_verdict_block` is untouched). So it
     means "what the session's own validation.sh said", and the stats
     rates move only for sessions packed after 0.4.57. That's what the
     brief's outcome 4 asks for.
   - The alternative was to re-derive the record too. That would move
     rates for in-flight sessions applied after the reinstall, and the
     record would disagree with the log it was parsed from. I didn't want
     either.

3. **A claimed check with no row in a printed block** reads as verdict
   `missing`, so it's a disagreement beside a pass claim. Its line says
   "no row in the claims block" rather than "no verdict recorded", so the
   two cases stay apart.

4. **Claims, but validation printed no claims block at all.** The line
   reads: `claimed checks: validation.sh printed no claims vs verdict
   block, so how many of the M claimed checks ran is unknown`. It names
   no disagreements, because bale can't see a verdict. I chose not to
   print a number bale didn't see. With no claims at all, the line is
   `claimed checks: 0 of 0 checks ran (the manifest claims no checks)`.

5. **Placement.** In the walk, the claims table now shows claim, verdict
   and bale's tag. The `N of M` line and one `disagree: <claims key>
   (...)` line per check come right under the table. The verdict block's
   validation row also gains `; K claim/verdict disagreement(s), named
   above`, because that's the line the eye lands on. In both planner
   relays the rows go after `admissions:`. On the HOLD block they had to
   go there anyway, because an existing test pins `admissions:` directly
   under `held tarball:`. The worker relay is unchanged: it already
   carries the whole validation.sh output.

6. **`.bale-notes.md` is placed beside the manifest in `run_validation_sh`,
   so after the blind checkpoint runs.** Same moment as the manifest. The
   checkpoint never saw `.bale-manifest.json` either, and giving it notes
   wasn't my call. If you want the oracle to grade notes, that's a planner
   decision (see Proposals).

## What to look at closely

- `bin/bale_report.py`: the new block after `parse_claim_verdict_block`
  (`claim_agreement`, `summarize_claimed_checks`, the three line
  builders). The rest of that file's diff is optional `claims_summary`
  keywords. With `None` they render the old bytes, and a test pins that.
- `bin/bale_staging.py`, `place_response_notes`: byte-for-byte copy;
  removes a stale copy first; doesn't follow a symlinked notes.md. It
  returns its log line instead of importing `log` from `__main__`, so the
  suite can test it in-process.
- The new log line in apply reads `claimed checks: ...`, never
  `claims vs verdict: ...`. That keeps it from ever looking like the
  header `parse_claim_verdict_block` scans for.
- One small fix the rehearsal turned up. When there are claims but no
  block, the walk falls back to the old claim-only table. That table used
  to print an annotated claim as a raw Python object
  (`claim={'value': 'pass', 'claim_basis': ...}`). It now prints the word.
  Bare-string claims print the same bytes as before.
- The two twins of the table, `RECONCILE_EPILOGUE` in the crafter and
  `claim_agreement` in bale. `tests/test_skipped_is_not_pass.py` drives
  both over every row of one table.

## This response's own apply

The apply that lands this runs on your installed 0.4.56. So the walk and
relay you see for this session are the old ones, and staging gets no
`.bale-notes.md` this time. The new behaviour starts once
`scripts/reinstall.sh` runs after the merge. Nothing in my validation.sh
depends on the new behaviour.

## Validation, and what I could and couldn't run here

- The full suite on the changed tree: 2133 tests, 23 of them new. Six
  failures and errors, every one also failing on the untouched baseline
  here, all because the request doesn't carry `README.md`, `bale.toml` or
  `claude/context/adr/0013-*.md` (`test_include_group` x3,
  `test_clipboard_key_rename`, `test_doc_crossrefs`' ADR-0013 pin,
  `test_global_doc_noun`'s file list). The baseline had a seventh, a
  `__pycache__` assertion in `test_clipboard_paste_blocks`, which didn't
  recur under `python3 -B`.
- validation.sh runs eleven targeted modules unconditionally (about 95
  seconds here). Two of them, `test_doc_crossrefs` and
  `test_global_doc_noun`, fail here only for those missing files. That's
  why the claim is annotated `predicted` rather than `observed`. If either
  fails in staging, it's about files I never saw, not this change.
- The full suite is about 7.5 minutes, past TARBALL.md 7.6's budget, so
  it's gated behind `--slow` and claimed `untested`. At a plain apply it
  SKIPs, and the reconciliation tags it `[n/a]` under either crafter. To
  include it, run `bash validation.sh --slow` in the staging directory.
- I ran validation.sh on the tree with the change applied (everything
  passes but those two modules) and on the untouched tree (every session
  assertion fails, as it should).

## Proposals

- **What:** let the blind checkpoint see `.bale-notes.md` (and the
  manifest) when the planner wants a notes section graded.
  **Why:** this session places both after the checkpoint runs, so an
  oracle can't check notes today. A notes-format outcome, like the
  office's Structure section, is the kind of thing a planner would want
  to grade blind.
  **Scope hints:** `bin/bale_staging.py` `run_blind_checkpoint` and the
  materialized checkpoint's cwd. It's a doctrine question first
  (PLANNER.md 5 and TARBALL.md 7), so it's the planner's to rule.

- **What:** record the derived count in telemetry (claimed, ran, derived
  disagreements) beside the printed `claim_verdict`.
  **Why:** the record now means "what the script said", which is right,
  but `bale stats` still can't see a skipped pass claim from an older
  crafter. The summary already exists at apply; persisting it is a small,
  additive schema field.
  **Scope hints:** `build_telemetry_attempt` in `bin/bale_report.py`,
  `schemas/telemetry-record.schema.json`, and a stats row.

## Walkthrough: A pass claim beside a skip is a disagreement, and staging carries notes.md

### What changed

- `tools/craft_response.py`: the reconciliation epilogue's tag rule. A
  `pass` claim beside `verdict=skip` or `verdict=missing` prints
  `[DISAGREE]` where it printed `[n/a]`. A `fail` claim beside either
  stays `[n/a]`. Everything else is unchanged: row shape, tag words,
  interface.
- `bin/bale_report.py`: bale's own copy of the table, plus a summary of
  the claimed checks built from the manifest and validation's output. It
  prints `claimed checks: N of M checks ran; K disagree with their claim`
  and one `disagree: <claims key> (claim=..., verdict=...: ...)` line per
  disagreeing check. Those lines appear in the apply walk (under a claims
  table that now shows verdicts too) and in the planner relay block, on
  both an applied landing and a HOLD.
- `bin/bale_apply.py`: builds that summary once after validation.sh and
  hands it to the walk and the relays. Logs one line.
- `bin/bale_staging.py`: before validation.sh runs, copies the response's
  notes.md to `staging/.bale-notes.md`, beside `.bale-manifest.json`.
- Docs: TARBALL.md 7.3 has the table and names `.bale-notes.md`. 5.3
  points at it. BALE.md's apply steps, walk, relays and telemetry
  paragraphs follow. The telemetry schema's `agreement` description and a
  stats comment explain when the rates move.
- Release: `bin/VERSION` 0.4.57 and `claude/changelog/0.4.57.json`.
- Tests: a new `tests/test_skipped_is_not_pass.py`, and one updated case
  in `tests/test_craft_response.py`.

### Why

The first slip: a validation.sh whose every check skipped (no
node_modules) landed as PASS, with claims of pass beside verdicts of skip,
and nothing said so. A check claimed to pass that never ran is exactly the
false PASS a reviewer needs to hear about. So it's now a disagreement,
named where the operator and the planner look, with a count of how many
claimed checks actually ran.

The second slip: validation.sh had no way to read the session's own
notes.md at apply, so a check on the notes sections could only SKIP. Now
the notes sit beside the manifest.

### How to explain each piece

- **The tag rule:** "claimed to pass, didn't run" is a disagreement. "No
  prediction" (untested or unknown) still isn't. A deliberate fail that
  didn't run still isn't.
- **The count:** M is how many checks the manifest claims; N is how many
  of those recorded pass or fail. Skipped or unrecorded checks don't
  count as ran.
- **Why bale has its own copy of the rule:** the crafter runs inside the
  worker's script; bale reads the result. Keeping a copy lets bale catch a
  script made with an older crafter. A test keeps the two copies equal.
- **Why the record keeps the printed tag:** telemetry records what the
  session's script said. The rates in `bale stats` move only for sessions
  packed after this release.
- **The notes file:** a byte-for-byte copy in staging. It's never
  committed, and it's absent when the response ships no notes.

### Questions a reviewer will ask

- *Does a disagreement ever block a merge?* No. Exit codes, PASS or HOLD,
  and the merge are untouched. It's reported, not enforced (TARBALL.md 7.3
  and 7.5).
- *Will old telemetry records change?* No. Records are never rewritten,
  and new records keep the tag the script printed.
- *What if validation.sh prints no claims block?* The line says the count
  is unknown and names nothing.
- *Can `.bale-notes.md` end up in a commit?* No. The session commit is
  built from the manifest's `changes[]` entries only, and the file is
  never one. The new end-to-end test checks the applied tree.
- *Why is the full suite not run at apply?* It takes about 7.5 minutes.
  It's behind `--slow` and claimed `untested`, and eleven targeted
  modules run instead.

### A hand test

After this lands and the reinstall has run:

1. In a scratch repo, pack a session and build a response whose
   validation.sh uses the new crafter's epilogue. Claim four checks as
   pass: run one, `record_verdict` two as `skip`, and never record the
   fourth. Ship a notes.md.
2. `bale apply` it. Look at the walk's claims table: three rows tagged
   `[DISAGREE]`, a line reading `1 of 4 checks ran; 3 disagree with their
   claim`, three `disagree:` lines, and `3 claim/verdict disagreement(s)`
   on the validation row. The verdict is still `[PASS]` and it merges.
3. Look at the `=== RELAY BEGIN ... to planner ===` block: the same
   `1 of 4 checks ran` line and the three `disagree:` lines, after
   `admissions:`.
4. Run `cmp` on the staging directory's `.bale-notes.md` and the
   response's notes.md: identical. Then run `git ls-tree -r applied/<sid>`:
   no `.bale-notes.md`.

## Handbook

### bale-src

- Since 0.4.57 the planner relay and the apply walk print a line holding `N of M checks ran` for the response's claimed checks, and name each claim that disagrees with its verdict; a pass claim beside a skip or an unrecorded verdict is a disagreement, diagnostic only.
- Since 0.4.57 bale places the response's notes.md at staging/.bale-notes.md, beside staging/.bale-manifest.json, before validation.sh runs; a response with no notes.md gets none.
- The full unit suite (python3 -m unittest discover -s tests) takes about 7.5 minutes on a worker sandbox; a validation.sh gates it behind --slow and runs targeted modules instead.
- A request that carries bin, tests and tools but not README.md, bale.toml and claude/context/adr leaves six suite cases failing in the worker sandbox for those absent files alone (test_include_group, test_clipboard_key_rename, test_doc_crossrefs, test_global_doc_noun).

## Structure

- title: Fix bale-src for the slips about bale, in eleven sessions
- size: high
- goal: Land the fixes to bale-src for the slips about bale in the office's suggestion box, one release per session, in the ratified order
