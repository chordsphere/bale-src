# notes — 2026-09-19-sitting-close-deltas-12-001

Sitting close 12 landed into `claude/MASTER.md`. There is one in-place
edit, the header's last-landed-by line (line 14). Everything else is
an insertion: 337 lines added and 1 line removed against the stamped
base (`ef5b4591…`). `validation.sh` proves that shape against `git
HEAD` when HEAD holds the stamped base, and SKIPs the three
diff-derived checks by name otherwise. Close 11's block was the shape
model. The four pinned line shapes are at column one where the brief
put them:

- `Landed 2026-09-18` ends §3.
- `110. **` and `111. **` follow row 109 and end §4.
- `New, ratified 2026-09-18` ends §5.
- `155. **` through `163. **` follow entry 154 and end §6.

**Heads-up for anyone grepping those shapes:** §6 already has evidence
entries numbered 110 and 111 ("Frame-vs-content respawn boundary",
"Probe-before-remedy…"). So `^110\. \*\*` matches twice in the file.
It matches once inside §4. My `validation.sh` scopes the row checks to
§4 for that reason. If the blind checkpoint greps the whole file, it
will see two.

## Where the brief and the telemetry records parted

The records won in each case below, per the constraint.

1. **No HOLDs.** All three sessions landed on a single apply attempt.
   Worker validation and the blind checkpoint both PASSed each time,
   `corrects` is null throughout, and every record's `failed_probes`
   is empty. The apply order, from the records:
   - 107 at 2026-09-18T23:52:21Z;
   - 109 at 23:53:32Z;
   - 47b at **2026-09-19T00:01:45Z**, past UTC midnight.

   The block's heading keeps `Landed 2026-09-18`, the pinned shape.
   The 09-19 apply time is stated in the landing-record bullet instead
   of being folded into the heading's date.
2. **The previous master did not close at this sitting's open.** The
   record for `2026-09-16-continue-plan-006` shows `unlocked`,
   `closed-read-only`, at 2026-09-17T15:24:21Z. That is 34 seconds
   after close 11's landing retry, and the day before this sitting
   opened. The heading says so.
3. **The master's pack second.** The brief says 23:04:16Z. The
   master's record carries no `packed_at`, and its `created_at` is
   23:04:17Z. Close 11's own record shows the same one-second lag
   between pack and record (packed 13:01:47, created 13:01:48). So I
   wrote 23:04:16Z as the pack instant and did not treat this as a
   real conflict. Correct it if the desk's 23:04:16Z came from
   somewhere else.
4. **The sitting-open version.** The master's record carries no
   version. All three workers' provenance stamps read 0.4.35, which is
   consistent with the brief. The block says both things.
5. **109's admission.** The admission of
   `tests/test_harness_cli_loader.py` was prompt-admitted
   (`overridden_path_sources: prompt`). The landing record says "at
   the prompt".

Everything else the brief states about how the sessions landed matches
the records and the three workers' notes:

- 47b's bump and its changelog record;
- 107's five tests with three failing on 0.4.35;
- 47b's four riders consumed;
- the proposals' numbering.

## Where the brief and the doc parted (not telemetry; flagged anyway)

6. **"Include-authoring rule, the fifth."** §7 already carries "rules,
   standing, now four" plus a separate rule "accreted 2026-09-15" (the
   fixture-consumer rule). By the doc's own count the new rule is the
   sixth. I dropped the ordinal and wrote "accreted 2026-09-18", which
   matches the 09-15 bullet's form. Consolidating the three bullets is
   a Proposal below.
7. **Entry 161's "for a month."** The interim planner-first rule is in
   row 47's 2026-09-10 bracket, which was grown at the 2026-09-01/02
   close. That puts it at roughly one to two and a half weeks old, so
   the title says "for weeks".
8. **"Exactly as its worker warned."** Close 11's item 3 named 105's
   *third* proposal as the one that might be under-recorded. The one
   actually missed was the second. The registry entry says "as its
   worker warned it might (item 3 of close 11's notes.md)".

## Judgment calls to ratify

- **Two registry brackets beyond the brief's list:**
  - `run_hook`'s placeholder-less f-strings → carrier row 110.
  - `from_lines`' "at v0.1" marker → carrier row 110.

  The brief names both as row 110 riders, and both already have
  registry entries. Following close 11's one-home practice, they get
  carrier brackets rather than being left as two homes. This makes
  nine brackets, not seven. Strike them if the desk reads it
  differently.
- **Row 110's forecast parenthetical.** It adds "and tests —
  `HoldCardUnitTest` in `tests/test_apply_preflight.py` among them".
  The brief's own sequencing bullet says 110 wants that file, and §7's
  forecast rule says a code row that changes tests forecasts them.
  - The brief said "Riders, all `bin/bale`" but its fourth rider (the
    `compose_retry_successor` unit test) lives in `tests/`.
  - So the row reads "Riders on `bin/bale`: …; and a
    `compose_retry_successor` unit test through `_load_cli()`".
- **47b's Proposal 1 on row 110.** It is carried verbatim in words, but
  its nested bullet markers are flattened into inline `*Why:*` /
  `*Scope hints:*` so it reads as one quotation inside the row, which
  is how earlier rows quote proposals.
- **107's Proposal 2 sentence** (the §8.8 registry entry) is verbatim.
  So are the sentinels and the sweep-commit subject on rows 47 and
  107. Each code span stays on one physical line so a later grep
  matches it.
- **Row 47's DONE bracket** adds three details from 47b's notes that
  were not in the brief:
  - the blocks print before the card;
  - each block closes on its `RELAY END` twin;
  - the planner block inlines this attempt's log bands.

  It also says the worker block carries the judge line and the quoted
  retry line, as TARBALL.md §7 now states.
- **§3 board-deltas bullet** names §5's addition as "the heading 'New,
  ratified 2026-09-18' over four contracts", in close 11's manner.

## Validation

`validation.sh` was rehearsed against a staging that mirrors the
target base:

- the base `MASTER.md` committed as HEAD;
- the request's telemetry committed, minus the master's record (open
  at pack);
- the `files/` overlay applied;
- `.bale-manifest.json` placed.

All twelve checks PASS in about a second. The "every cited sid" check
prints two tolerances by name: this session and the master. Every
other cited sid (six) has a record on disk. That is close 11's
re-attempt lesson, applied in advance.

I also ran three negative rehearsals:

- a HEAD that is not the base → the three diff-derived checks SKIP by
  name, exit 0;
- one existing line in row 47 reworded → insertions-only FAILs,
  naming the line;
- a typo'd cited sid → the sid check FAILs, naming it.

## Proposals

- **What:** consolidate §7's include-authoring rules into one bullet at
  the next MASTER.md regeneration. Today they are spread across three
  bullets: the four standing, the 09-15 fixture-consumer rule, and
  this close's `bale.toml`/`claude/changelog` rule.
  **Why:** the brief counted "the fifth" and the doc holds six. A
  desk that counts from one bullet will miscount again.
  **Scope hints:** `claude/MASTER.md` §7 only. This is a rewording, so
  it belongs to a regeneration rather than an insertions-only close.
- **What:** scope any blind-checkpoint grep for board rows to §4, or
  anchor it past `## 4.`.
  **Why:** evidence entries 110 and 111 in §6 share the `NNN. **`
  shape with the new rows. Entries 112 onward will collide with future
  rows 112+ the same way, since the board and the pile number
  independently and the board has now caught up.
  **Scope hints:** the desk's checkpoint template for close sessions;
  no code.
