# notes — 2026-09-21-sitting-close-deltas-16-004

Sitting close 16 landed into `claude/MASTER.md`. It covers the
`2026-09-20-continue-plan-006` and `2026-09-20-continue-plan-009`
sittings and wave 8's landing (close 15; 104b at 0.4.40). It cites
`2026-09-21-continue-plan-002` only as the desk that authored this close
and found what your section 4 lists.

Line 14 is edited in place. Everything else is an insertion: 773 lines
against the stamped base (`e5b80f83…dcfc`, 8778 lines, the sha close
15's notes.md gives for its landing). The model was close 15's two
blocks and its notes.md.

The pinned shapes are where the brief put them:

- **§3 blocks.** 006 then 009, between the 004 block and
  `## 4. The board`. Each closes on sequencing, board deltas, registry
  deltas. The 006 block has the `- Ratified at the
  `2026-09-20-continue-plan-009` desk:` bullet and wave 8's dispatch and
  landing record. The 009 block has both light blocks flattened (rows
  joined by " / "), the operator's three messages each on one physical
  line, and the debt bullet closing on the convention sentence, WHOLE.
- **Registry.** Five `consumed at` brackets, each inside its entry. Six
  new entries in the pinned order, directly before the 2026-08-05 line.
  I had no entry of my own to put before them.
- **Board.** Row 103's bracket; row 104 ends on the 104b DONE bracket;
  §4 still ends at row 113.
- **§5.** One new block ends the section, the two contracts in order,
  each with its `Home:` sentence.
- **§6.** Entry 187's bracket, which says it does not settle the entry.
  Entries 188–194 end the section, no gaps.
- **§7.** Six new bullets, the first the 0.4.40 landmark.

The turn was split by one tool-use pause, after `validation.sh` and the
manifest skeleton were written and before anything had been rehearsed.
It was a pause, not a compaction; my context stayed intact, and I said
at the pause that no tarball existed yet. On resume I rebuilt the file
from the base by the same script and got the same bytes
(`3cda112d…51ee`) before doing anything else.

## Where the briefs and the records parted

The records won each time, and each parting is named in the file.

1. **The `base_files` map is 115 entries, not 100.** Your section 4
   calls the map in 008's record a 100-entry map. The echo in its
   applied attempt holds 115. Entry 192 and the 009 block give both
   numbers. I counted it and did not print it.
2. **The 006 desk's sequencing never reached me.** The pin asks for a
   `- Sequencing for the next desk` bullet in the 006 block. Part 2
   quotes the 006 brief only from "Wave 8, as dispatched" to the line
   before its "Second job", which is the range that lost the 001 desk's
   standing line at close 15 (entry 177). The bullet says so, and
   carries what the range does hold: the condition "If close 15 has not
   landed when you open, do not author close 16…", verbatim, which the
   009 desk then met. The standing line that traveled is in the 009
   block, verbatim from the 009 brief. I did not bracket entry 177 for a
   third specimen: nobody told me to quote the missing line this time.
   Proposal 2 below is about the pattern.
3. **The 009 desk's NOT-knowns, answered.** 0.4.40 is confirmed by
   `claude/changelog/0.4.40.json`. One apply attempt each, no hold, no
   admissions. Both are in the 006 block's landing record and the 009
   block's partings bullet.
4. **The sweep.** Part 2 says the operator had been told to decline;
   the record shows your pack swept
   `2026-09-21-board-103-probe-design-001` at 02:59:37Z. Recorded as a
   fact beside the operator's later "as assumed" and the arrival of his
   103 notes, both on your word, and not as a finding.
5. **"The third sitting running … at a pause."** The 006 desk's
   candidate counts three sittings running where a light block at a
   pause was answered first time. Landed entry 179 says the 004 desk's
   block had no pause, and the 001 desk emitted no block at all. 179's
   bracket says the run is of first-time answers, not of pauses, and
   counts four blocks.
6. **"Whether either was opened … is NOT known to this desk."** Not a
   parting, a fill: by the records both wave-8 sessions opened in the
   006 master's last thirteen seconds (03:07:54Z, 03:08:02Z; it closed
   03:08:07Z). The block's opener says so.

Everything else you stated from the records in section 3 checks out,
second for second: both workers' packs, applies, checkpoint shas and
stamp matches, claim counts, `change_paths`; the four master and 103
records' opens, closes, commands and `swept_by` values; the
three-second and one-second `packed_at` lags.

## Judgment calls to ratify

**§6, by candidate.** Fourteen candidates (the 006 desk's five, the 009
desk's six, your three). Seven new entries, four brackets.

| Candidate | Where it went |
|---|---|
| 006: a Proposal about code nobody had read | entry 188, merged with the next row |
| 009: two desk artifacts contradicted within one wave | entry 188 |
| 006: 37's rejected attempt, found by script | last sentence of 187's pinned bracket; declined as an entry, since 187 already is that finding |
| 006: a pause with nothing built; answered first time | bracket on 179; the pause clause is also in the 006 block |
| 009: two more blocks answered first time, the mixed reply | bracket on 179 |
| 006: dress rehearsal under the real sandbox, with a pty | entry 190 |
| 006: three oracle defects, no brief defects | entry 191 |
| 009: row 103 names a home the code reserves | entry 189, with the row's "identical argv" finding |
| 009: a heading-number range over a core-first doc | entry 192 |
| 002: a third desk's careless read | entry 192 |
| 009: an unexplained planner bundle | entry 193 |
| 009: a master ending with its first job unbuilt | bracket on 182 (its second specimen) |
| 002: the first live `swept_by` | entry 194, with a pointer bracket on 174 |
| 002: `packed_at`'s three-second lag | entry 194 |

- Entry 191 counts **four** rehearsal-caught defects: three in close
  15's oracle and the `import requests` mutation in 104b's. The
  candidate says three; the 006 desk's own verification section lists
  the fourth.
- Entries 188, 189, 191, 192 and 193 each end on a rule sentence in my
  words. 182's bracket ends on one too ("A master opened beside its wave
  can dispatch; the close falls to the desk packed after the landing").
  Strike any that overreach.
- 192 names the 002 desk as its third specimen, on your word.

**A sid I refused to write.** The 006 desk's third oracle defect reads,
in Part 2, as the sid regex matching a literal that is a date, the slug
`board` and the digits 104. That literal has a sid's shape and no
telemetry record, which is exactly what your invariant forbids. The 006
block and entry 191 paraphrase it ("taking the row number inside 104b's
bundle stem for a counter"). The block says "in the 006 desk's words,
shortened", so the paraphrase is covered, but it is a departure from
verbatim and you should know why.

**Bundle stems.** I wrote five stems as the briefs give them: 103's two,
the stray one, and wave 8's two. None carries a counter. If the blind
checkpoint's sid probe reads `…board-103` inside a stem as a sid, that
is the defect the 006 desk already caught once, and the HOLD would be
the oracle's. My own sid check uses a look-ahead and passes them.

**Ruling 1's reach.** The 009 desk ratified the 001 and 004 desks' calls
sight unseen and asked this close to cite them from close 15's landed
blocks or say they are not there. They are there: the 004 block's debt
bullet lists four of the 001 desk's and seven of the 004 desk's as
unruled. The 009 block says ruling 1 ratifies "the eleven as that bullet
lists them". If the operator meant something narrower by "as assumed",
that sentence is the one to correct.

**The 006 block, not the 009 block, carries wave 8's dispatch and
landing**, as you ruled. The block split otherwise: what each desk did,
found and verified is in its own block; ruling 4's dispositions are in
the 009 block; entry 188 and 179's bracket are shared and both
board-delta bullets say so.

**The 002 desk's judgment calls are not in the file.** Your section 6
says the 009 block's successor carries them, and the manifest puts your
sitting out of scope. The 009 block's debt bullet lists the 009 desk's
eight calls as unruled, says wave 8's two notes.md carry nothing
forward, and says your calls belong to your sitting's close. Request
briefs are archived nowhere, so they now live only in your brief to me
and in whatever you hand your successor.

**Brackets you did not pin.**

- The older "Pack-json `sweep` key" entry: a two-line pointer at the
  consumed entry. It opens `[2026-09-20: landed with 104b`, so lines
  opening with the pinned `consumed at` string still number exactly
  five. My `validation.sh` counts them.
- Entry 174: two lines, the remedy landed, see 194.
- Entries 179 and 182, above.

**§5's block header** reads "(the `2026-09-20-continue-plan-009` desk,
the second as that desk ratified 104b's landing; …; recorded at close
16)". The second contract states the shapes from 104b's notes.md and
the changelog record, and says the six-key entry was "ratified at the
009 desk as a floor met". Its `Homes:` sentence is attributed to 104b's
notes.md, since I have not seen BALE.md or the schema.

**The §11.4 registry entry** cites the 2026-09-19 light block's [2] for
what the pointer was (a pointer at the crafter's bailout kind) and
quotes row 37's bracket only for "shrinks to at most a clause and may be
nothing". For what it is worth, the `CLAUDE.md` shipped in this request
routes §11.4 to TARBALL.md §5.6 for the shape and does not name the
crafter. I did not read §5.6.1. The next holder decides.

**The relays' wording is paraphrased.** Part 2 quotes each relay as
"verdict: checkpoint: PASS · worker validation: PASS". The 009 block
says "each reading PASS on both judgments with no admissions, as the
records do". I did not want a desk's quotation of bale's output landing
as if I had seen the output.

**One-line verbatims.** The third operator message is 150 characters on
one physical line, and the convention sentence 104. Everything else I
inserted wraps at 72 characters. Short backticked spans are kept whole
on a line.

**Record facts I added beyond your section 3**, all checked by key: all
six of 104b's claims carry `claim_basis: observed`; its record reports
`budget_pressure: tight` and close 15's `none`;
`tests/test_pack_telemetry_104b.py` is absent from 104b's `base_files`,
so it is the new suite; every attempt in all six records carries the
cost block all-null (entry 189 leans on this).

## Taken on a desk's word (nothing shipped lets me check)

- Both masters' `packed_at` seconds (02:41:53Z, 03:08:07Z) and bale
  0.4.39 at their opens; the pack that closed the 006 master.
- Every turn, pause, light block and reply at both desks, including the
  operator's three messages and his "as assumed" to the 006 desk.
- Both desks' oracle counts, rehearsals and dress rehearsals; `unshare`
  and the pty control; the 31-test background run.
- The 006 desk's code read (`superseded_by` since 0.3.23; the sweep
  running before the mint), and the 009 desk's
  (`bin/bale_report.py`'s cost block and the quoted comment; the
  disjointness gate).
- All four brief shas, the stray bundle's two shas and its 03:25:14Z;
  the stems.
- From 104b's notes.md, not from code: board 69 (d) and
  `ToolsHermeticPin`; the suite and `validate.sh` counts; BALE.md's
  section numbers. MASTER.md's row 69 lists parts (a) and (b) only, so
  "(d)" is 104b's word, and the file says "by 104b's notes.md" each
  time.
- From you: that `2026-09-21-continue-plan-002` has a record; the
  operator's ratification of the sweep; that his 103 notes arrived; that
  103's first wave ran on 2026-09-21 as four runs outside this repo;
  that neither wave-8 session met the reworded
  `format_hold_relay_planner` condition.

## Validation

`validation.sh` runs eleven checks, ten of them claimed. There is no
lint, typecheck or build surface for this doc, so the claims are the
session-specific assertions (TARBALL.md §5.3). The reconciliation block
is the crafter's `--validation-epilogue` emission, pasted unchanged.

The insertions-only check takes the base from `git show HEAD:` and uses
it only if its sha256 is the stamped `e5b80f83…`. It walks the new file
against the base in order with line 14 taken out, requires lines 1–13
unchanged, and checks the line arithmetic closes. The sid check reads
inserted lines only, looks each sid up under `claude/telemetry/`, and
tolerates two by name: this session and your desk. The verbatim check
re-flattens both Proposals from the archived notes.md and looks for the
exact quoted text.

Rehearsed in a scratch git repo whose HEAD held the base and the shipped
records and notes, with the `files/` overlay applied, `apply.sh` run and
the manifest placed as `.bale-manifest.json`: eleven PASS, ten `[agree]`,
exit 0.

Negative landings, each exit 1 and each failing the check it should:

- a base line altered → insertions-only FAILs, naming base line 101;
- a pinned closing bullet reworded → the §3 check;
- the third operator message wrapped onto two lines → the §3 check;
- an invented sid (a counter on the stray stem) → the sid check;
- entry 190 renumbered → the §6 check;
- a sixth `consumed at` bracket → the registry check;
- a row 114 → the board check.

HEAD not the base → both base-relative checks SKIP by name, exit 0.

The rehearsal caught one defect, in my script and not in the doc: the
sid check failed a second time off a lost base line. That is the defect
the 006 desk caught in its own oracle, recorded in the block I had just
written. It now SKIPs by name and leaves the finding to the
insertions-only check.

The tools: I read the crafter's header, imports, write sites, `main()`
tail and `--help`, and the lint's imports and `--help`, before running
either. Both are stdlib-only, with no network. The crafter wrote only
`manifest.json` and `apply.sh`, under `--write`. The lint writes
nothing.

## Proposals

1. **Record the bundle an `opened` attempt came from.**
   - What: when a session is opened from a bundle, stamp the bundle's
     stem, or its brief's sha256, on the `opened` attempt.
   - Why: row 103's bracket has to say that which revision either open
     used "is in no record". Two revisions and a stray bundle sat side
     by side at the 009 desk, and the two 103 records cannot say which
     one ran. `packed_at` and `swept_by` closed the same kind of gap one
     wave ago and were read at the very next close (entry 194).
   - Scope hints: `bale open`'s pack replay and the telemetry record
     schema. Additive. Named consumer: the close desk's reconstruction,
     per DOCS.md §9's telemetry rule. I have not seen the code.
2. **Give the standing line a fixed place in a master's brief.**
   - What: a brief convention: a master's brief carries the standing
     line inside its sitting record, not under "Second job".
   - Why: two closes running, the byte-for-byte quotation of a
     predecessor's brief has stopped at "the line before its Second
     job", and the standing line sat past it (entry 177's second
     specimen, and this close's 006 block). It cost nothing this time
     only because the line has not changed since 2026-09-19.
   - Scope hints: `docs/PLANNER.md` §3 or §6, one sentence, or just the
     desks' practice. It could ride the same `docs/PLANNER.md` holder as
     the exit-2 rider.
