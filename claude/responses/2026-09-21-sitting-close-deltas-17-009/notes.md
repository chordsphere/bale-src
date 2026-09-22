# notes — 2026-09-21-sitting-close-deltas-17-009

Sitting close 17 is landed in `claude/MASTER.md`. It covers the
`2026-09-21-continue-plan-002` and `2026-09-21-continue-plan-005`
sittings, wave 10 so far (the doc lane and the split-transition fix),
and row 103's arc. It cites `2026-09-21-continue-plan-008` for three
things only: the desk that authored this close, its ratifications, and
its unruled calls. It does not close that desk's sitting; that is close
18.

Line 14 is edited in place. Everything else is an insertion: 1265 lines
against the stamped base (`3cda112d…51ee`, 9551 lines, verified before
anything was built). The landed file is 10816 lines, sha256
`a8bbbeee…70a9`. Bumpless.

The turn was split by one tool-use pause, before anything was written to
the response directory. It was a pause, not a compaction, and my context
stayed intact. On resume I built everything by script from the base and
the sources.

Where the brief put each pinned shape:

- **§3.** The 002 block, then the 005 block, between close 16's 009
  block and `## 4.`. Each block closes on sequencing, board deltas and
  registry deltas, in that order. The 005 block carries:
  - the `- Ratified at the `2026-09-21-continue-plan-008` desk:` bullet,
  - wave 10's dispatch and landing record,
  - the fix as a non-board landing,
  - its debt bullet closing on the convention sentence, which sits whole
    on one line.
- **Registry.**
  - The two pinned brackets, each inside its entry.
  - Pointer brackets on the three rider-micro entries. These are my own
    and were not pinned.
  - The eight pinned entries, in order, directly before the 2026-08-05
    line. I needed no entry of my own ahead of them.
- **Board.** Row 103's 2026-09-21 bracket, after its 2026-09-20 one.
  Rows 114–120 follow row 113, and nothing comes after them.
- **§5.** The home bracket sits right after the exit-2 sentence. A new
  2026-09-21 block closes the section with the one contract.
- **§6.**
  - Entry 191's pinned bracket, last in the entry.
  - My own brackets on entries 173, 179 and 194.
  - Entries 195–204, with no gaps.
- **§7.** The landmark bullet is first after the `base_files` bullet.
  Eight fact bullets follow it.

## Where the briefs and the records parted

They did not part anywhere I could find. Every record fact the brief
states checks out by key, second for second, and so does every fact in
the two quoted briefs that a record on this tree holds. I also added
facts from the records and fills that the desks could not see:

1. **The 005 master's sweep.** Its brief says what its pack swept "is
   not known here". The records say it swept 003 at 12:20:31Z and 002
   at 12:20:35Z. Your brief already had this fill; it lands in the 005
   block's opener and in entry 194's bracket.
2. **The fix's request was not stale; the desk's copy was.** The fix's
   applied attempt echoes CLAUDE.md `214639ce…` and TARBALL.md
   `29ecbbae…`. Close 16 and the doc lane echo `52c8771d…` and
   `b7265475…`. So the fix was packed on the doc lane's landed docs. The
   staleness the 005 desk named belonged to its own tarball and not to
   the worker's request. This is in the 005 block and in entry 204.
3. **What the relays did not carry.** Both wave-10 applies ran confined
   with the network grant exercised. All sixteen claims are
   `claim_basis: observed`, and both workers report
   `budget_pressure: none`.
4. **Close 16's notes.md.** The 002 desk read it from the relay and did
   not hash it. The archived copy is 15620 bytes, sha256 `29847ba4…6201`,
   matching the probe's figure.
5. **The 008 master's timing.** Its `created_at` is 13:23:35Z against a
   `packed_at` of 13:23:33Z. The 005 master's closure came at 13:23:32Z,
   a second before that `packed_at`.

Taken on a desk's word, because no record here holds them:

- the `bale status` counts (301 applied, two uncommitted changes);
- the 3-of-72 mode-755 count;
- every brief and bundle sha other than the checkpoint shas, which the
  records confirm.

## Judgment calls to ratify

**§6, by candidate.** There were twenty-four candidates: the 002 desk's
eight, the 005 desk's eleven, and five from your desk. I made ten new
entries and three brackets, plus entry 191's pinned bracket.

| Candidate | Where it went |
|---|---|
| 002: a third careless read, plus two more errors of that family | the first half was already landed in 192 and is declined as new; "seventeen for fifteen" and the cleared-context cascade count → 198 |
| 002: pause with bundle built; four blocks, one answer a question | pause → bracket on 173; the blocks → bracket on 179 and 197 |
| 002: two oracle cascades caught by rehearsal, and close 16's worker's | 199 |
| 002: a bundle superseded unopened, twice | 196 |
| 002: close 16's Proposal 1 needed before it exists | bracket on 194 |
| 002: attachment announced and absent (turn four) | 195 |
| 002: a findings file that carries an oracle | 200 |
| 002: asked to close its own sitting; advised against | 201 |
| 005: attachment absent, third time | 195 |
| 005: pause with bundle built, used to ask before delivery | bracket on 173 |
| 005: late fact after delivery, not superseded | 196 |
| 005: stop condition ruled in advance, then invoked | 201 |
| 005: an unanswered block treated as unanswered | 197, and the bracket on 179 |
| 005: a worker's finding verified and shipped whole; four rulings in one row | 202 |
| 005: a required spelling refused a draft; five VERBATIM sentences held | 203 |
| 005: a pin that held a misreading in place | 202 |
| 005: a number stated uncounted, twice, caught before sending | 198 |
| 005: two doc sessions from one desk, one against a stale base | 204 |
| 005: the role-transition miss itself | 202, and §5's "Why it was needed" |
| 008: attachment absent, fourth time | 195 |
| 008: an unknown filled from `swept_by` at the very next desk | bracket on 194 |
| 008: `model_identity` three ways in one day | row 116 only; declined as an entry, since the row is its home and it teaches nothing on its own |
| 008: three desks' debt cleared in one row, calls enumerated in the reply | 197 |
| 008: a desk that built nothing ahead of its block | bracket on 173, as the contrast case |

**Rule sentences in my words.** Entries 195 to 204 each end on one, and
the three brackets end on observations. Please strike any that
overreach. The ones I am least sure of:

- **196:** "a late fact supersedes a delivered bundle when it makes
  pinned text false, not when the text could have been fuller". This
  generalises from one case each way.
- **197:** "a reply ratifies what the question enumerated in text the
  operator could see".
- **201:** its second half, about stop conditions.

**Where I followed the brief's latitude:**

- **No §5 line for row 103's standing-test ruling.** The ruling lives on
  the row and in the standing line. A contract line would restate the row
  with nothing to enforce. This is recorded in the manifest's `deferred`.
- **No pointer bracket inside close 16's 009 block's debt bullet.** Its
  last line is the convention sentence, which your brief says closes
  that bullet. A bracket after it would break that shape. The 002
  block's debt bullet points at the 008 ratification instead, as the
  brief asked.
- **Pointer brackets on three registry entries, not two.** I bracketed
  "A cause on a `rejected` attempt", the `swept_by` dossier entry, and
  110's `format_hold_relay_planner` entry. The last bracket says that
  entry's own ride condition still binds the micro, because the 002
  desk's second-job section lists it.
- **The 002 desk's second small call** was taking close 17's base facts
  from notes and probes. I recorded it as moot rather than ratified: the
  005 and 008 desks verified those facts, and so did I on the file.
- **Operator messages.** I quoted each one whole on one physical line,
  as pinned. I did not re-quote row 103's long message inside the 002
  block. The block points at the row, which is the pinned home, so the
  500-character line appears once.
- **Paraphrase instead of quoting fragments of operator messages.** In
  the 002 block, "Reauthor close 16 if you need, I haven't packed yet"
  is paraphrased. A partial quote would have looked like a whole one.
- **Light blocks.** All nine are flattened by script from the brief's
  bytes, with rows joined by " / " as close 16 did. The 005 desk's block
  one is carried as retyped and labelled RETYPED.
- **The 1426-test figure.** I left out the fix worker's 1426-test run,
  since it is that worker's sandbox's number, not your tree's.
- **The findings file.** Row 103's bracket carries only what your
  "Row 103's arc" section gives, by section number. It names the four
  packet labels and the two models, because your brief's header item
  does. Nothing of the kit's task, bait or canned answer appears, and I
  never had any of it.
- **The brief's "the three doc suites".** In §7 I named them as
  `test_doc_crossrefs`, `test_global_doc_selfcontainment` and
  `test_sanctioned_pairs`, from the 005 desk's verification section. No
  record lists the three.

## Validation

`validation.sh` runs twelve checks, all claimed and all observed. This
doc has no lint, typecheck, build or test surface, so the claims are the
session-specific assertions (TARBALL.md §5.3).

- Every comparison is made on bytes inside Python, with `-B`.
- The script writes nothing and says so first.
- The pinned and verbatim strings are lifted from the brief and the
  archived notes by the same generator that built the landing. The
  Proposal check re-flattens the three notes.md on the tree itself.
- The reconciliation is the crafter's `--validation-epilogue` fragments,
  pasted unchanged.
- The base-relative checks take the base from `git show HEAD:` and use
  it only at the stamped sha. The sid check tolerates exactly this
  session and the 008 desk.

I rehearsed it in a scratch git repo whose HEAD held the shipped
`claude/` tree, with the overlay and `apply.sh` applied and the manifest
placed as `.bale-manifest.json`. All twelve checks passed with twelve
`[agree]`, exit 0, and `git status` showed no other writes.

**On the unmodified tree:** exit 1, with nine checks failing. Three pass
on both trees because they are guards, not change tests: insertions-only
(the base is trivially itself), byte discipline, and the sid check.

**Negative landings** each exited 1 and each failed only the check it
targets, except where noted:

| Mutation | What failed |
|---|---|
| a base line altered | insertions-only fails; the sid check SKIPs by name, since it needs a clean insertions-only result |
| line 14 naming close 16 | the line-14 check |
| a closing bullet reworded | the §3 structure check |
| the standing line wrapped | the §3 structure check, and the 72-column check on the overlong fragment the wrap leaves |
| a light-block row edited | the §3 verbatim check |
| a registry label edited | the registry order check |
| one character of a Proposal | the Proposal check |
| a row 121 | the board check |
| the §5 bracket's opener edited | the §5 check |
| an entry renumbered | the §6 check |
| entry 191's count edited | the §6 check |
| the landmark reworded | the §7 check |
| a counter added to the doc-lane bundle stem | the sid check |
| an inserted line pushed past 72 columns | the byte-discipline check |

Rehearsal caught three defects, all in my script and none in the doc:

- A base-line mutation cascaded into the 72-column check. The column
  check now waits on a clean insertions-only result. This is entry 199's
  lesson, applied to my own script the day I wrote the entry.
- The Proposal check SKIPped on the unmodified tree with a misleading
  reason, instead of failing. It now fails there.
- Two of my first mutations did not bite, because the phrase they
  targeted was split across a line break. I rewrote both to target
  whole lines.

**The tools.** I read the crafter's header, imports, write sites and
`--help`, and the lint's imports and `--help`, before running either.
Both are stdlib-only. The crafter wrote only `manifest.json` and
`apply.sh`, under `--write`, and the lint writes nothing.

**Reading.** I read the core of CLAUDE.md, the whole brief, TARBALL.md
§1, §2, §5.1–§5.5, §7 and §10.1, plus the §3.4 and §5.10 passages the
contract cites. I read DOCS.md and PLANNER.md only as far as their
INDEX tables, since no row fired, plus the PLANNER.md §3, §4 and §20
passages the §5 contract states. I did not read CODE.md.

## Proposals

1. **A close's registry entries want a stable anchor.**
   - **What:** give the §3 registry a heading of its own, or a
     one-line marker at its end, instead of "the list that ends
     directly before the line 'Landed 2026-08-05, non-board'".
   - **Why:** three closes running have located the registry's end by
     the first line of an unrelated block that happens to follow it. My
     generator had to assert that the pinned predecessor entry sits ten
     lines above that block. One regeneration that moves the 2026-08-05
     block would silently break every close's oracle and builder.
   - **Scope hints:** `claude/MASTER.md`. It is a rewording, so it
     belongs to the next regeneration, beside the §7 consolidation
     entry already on the registry.
2. **Record which light blocks a desk emitted, and their answers.**
   - **What:** a master's self-report, or a bale-side trail, that
     counts light blocks and marks each one answered, unanswered or
     answered-with-a-question.
   - **Why:** entry 179 has counted blocks at three closes running, every
     one reconstructed from briefs that are archived nowhere. The
     one miss this close records (the 005 desk's block two) is known
     only because that desk said so. `light_blocks` exists in
     `self_reported`, but read-only masters return no response, so
     nothing carries it for them.
   - **Scope hints:** the telemetry record schema, and possibly the 100
     arc's design sitting (row 116's neighbour). I have not read the
     code.
