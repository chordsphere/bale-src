# notes.md — 2026-09-14-sitting-close-deltas-7-012 (retry)

## Why this is a retry

`corrects` names the first attempt, held at commit 82e8661: worker
validation passed, the blind checkpoint failed one of eighteen —
"row 87's wrong desk clause struck (still present)". My row-87
bracket *quoted* the struck clause verbatim while recording the
correction, so the phrase was still in the file. My own assertion
grepped for the clause with its trailing semicolon and passed
against my reading of "struck"; the checkpoint grepped the bare
phrase. Evidence 130's shape, one entry after it was written: the
rehearsal validated to the worker's own reading, and the blind
checkpoint was the second reader. The fix is one line in the row-87
bracket (the clause is now named as the "naming variance defeats
matching" clause, not quoted) and `validation.sh` now greps the
bare phrase the way the checkpoint does; re-run against the held
file it fails, against this one it passes. Nothing else changed:
the other 22 edits are byte-identical. Add this to the ratification
queue as a specimen — a close that records a struck phrase must not
re-quote it.

One file, `claude/MASTER.md`, 544 diff lines (530 added, 14
removed), additive except three in-place spans: the header's
last-landed-by line, the §7 VERSION landmark sentence, and the
struck clause on row 87 (the brief's own instruction). The 14
removed lines are exactly those three spans plus the seven lines
that carried backslash-escaped quotes (re-emitted without them) and
the hook-store bullet's last line (re-emitted with the new sentence
appended). Twenty-three anchored replacements, each required to
match exactly once, driven by a script that refuses on any other
count; the diff is all prose and worth a skim end to end.

Base file hash matched the manifest's `base_files` stamp before I
touched it. No CRLF, no trailing whitespace, before or after. No
chat round with the desk: nothing rose to a blocking intent gap
(§10.1 step 2, evidence 127 being the specimen I would have become),
so every call below is flagged for ratification or correction.

DOCS.md and PLANNER.md were not drilled: DOCS.md's triggers
(INDEX/STATE/ADR/split/prune/naming) don't cover a MASTER.md close,
and PLANNER.md's "a sitting" trigger is for the desk authoring one,
not the worker recording it. TARBALL.md core plus §10.1; CLAUDE.md
core in full.

## Brief defects the desk should record

- **Row 84's "same `includes_missing` shape" is not what telemetry
  says.** Row 80's record has `includes_missing: []`. The worker
  named the `bin/` gap only in its notes ("rightly — it's in row
  73B's forecast") and shipped three suites `predicted` (all graded
  `agree`). The row-84 bracket and evidence 126 record the specimen
  with that difference stated: this is the one the ledger does not
  carry.
- **"73A's proposals 2 (the two checkpoint suites shipped together)
  — 1 and 3 became rows 92/93" matches neither notes file.** 73A's
  proposals are (1) the `caller` kwarg — landed at 73B by the row-73
  ruling; (2) the stats drill-down row — already row 86; (3) ship
  `test_per_sid_checkpoint.py` beside `test_checkpoint_file_flag.py`
  — desk practice. Rows 92, 93, and 91 are 73B's three proposals, as
  the brief's own row text says. The close block's registry bullet
  records it that way.
- **The "consumed" registry riders have no registry entries.**
  Board 78's three proposals, s34's pair proposal, 74–76's parity
  pin, and 73A's all rode board rows (row 80's Sources line, row
  78's disposition line), never the §3 registry. Their consumption
  is recorded in the close block against those rows (close-6's
  row-47 precedent); nothing in the registry is struck for them.
- **"Seven" backslash-escaped quotes are fourteen sequences** — each
  quoted token opens and closes. All fourteen are struck; the
  validation assertion counts sequences, not lines.
- **Row 51's close-6 bracket carries the same wrong clause** the
  brief strikes on row 87 ("the naming variance … is what defeats
  this row's matching"). The brief names only row 87's strike, so
  that clause stands on row 51 and is corrected inside 51's new
  bracket. Strike it there too if you'd rather (two lines).

## Facts trued up against telemetry rather than the brief

- Timeline, from the records: 73B opened 21:43:53Z and 80 opened
  21:43:58Z (beside each other); 80 applied 21:55:45Z; the doc lane
  opened 22:06:47Z beside 73B; 73B applied 22:14:14Z, the doc lane
  22:14:48Z; the apply-side opened 22:21:17Z and 83 at 22:21:22Z
  (beside each other); the apply-side held 22:52:44Z and applied on
  retry 22:55:45Z; 83 held 23:30:47Z and applied on retry
  23:37:09Z. "Up to two open beside the desk" holds; the landing
  order the brief gives is the applied-time order.
- Exchange rounds: the brief's "one relayed round" on 73B and on 83
  is telemetry `clarification.rounds: 2` on each (record n=1 from
  the worker, n=2 from the planner). Both spellings are in the
  block and the watch stamp so the next reader can reconcile them
  against the exchange-adoption watch's own `rounds: 0` vocabulary.
- HOLD causes match: the apply-side's first attempt is `validation:
  HOLD, exit 1` with `checkpoint: PASS`; 83's first attempt is
  `validation: PASS, exit 0` with `checkpoint: HOLD, exit 1`. Both
  retries `stamp_matched: true`.
- Versions: 73B's and the apply-side's `change_paths` carry
  `bin/VERSION`; the apply-side's and 83's requests stamp 0.4.28,
  and this close's request stamps 0.4.29 — the corroboration chain
  the §7 landmark cites. 80, the doc lane, and 83 carry no
  `bin/VERSION`.
- 73B's drift: one path, `bin/bale_report.py`,
  `overridden_path_sources: prompt` — admitted at the y/N, as the
  brief says.
- Not verifiable from the shipped files, recorded as the brief
  states: the master's sitting-open version check at 0.4.27 (the
  master's record has no version field) and the previous master
  closing `closed-read-only` at this session's pack (no record for
  `2026-09-11-continue-plan-001` shipped). Both say so in the block.
- The apply-side retry's tarball is recorded as
  `response-2026-09-14-apply-side-81-87-010 (1).tar.gz` — a
  Downloads-collision rename, not the sid form. Not a MASTER.md
  fact; noted here only because the resolver row is about naming.

## VERBATIM handling

- The operator's bare-apply ruling lands byte-exact modulo
  wrapping; `validation.sh` asserts it whitespace-normalized. It
  contains no inner quotes, so the backslash question doesn't
  arise.
- Rows 92 and 93 carry 73B's two proposals VERBATIM from its
  notes.md, wrapped, with the bold `**What:**` / `**Why:**` /
  `**Scope hints:**` leads intact (the registry's convention).
- The 88 §6 sentence is cited, not re-quoted, in §5 as the brief
  asked.
- The two escapes in the registry's `persist_pack_session` entry
  (`"handoff"`, `"pack"`) are struck in the same pass. That
  passage quotes a Python docstring, where the backslashes could in
  principle be the source's own; the brief calls them the same
  artifact class and I followed it. **Flagged for the next open:**
  if the docstring bytes really carry `\"`, restore the two.

## Placement calls (ratify or correct)

- **§7 VERSION landmark edited in place** (close-5 and close-6
  precedent, both ratified): 0.4.29 at the apply-side session,
  with 0.4.28 at 73B and the earlier trail retained; the bumpless
  sessions of this sitting named in the same parenthetical.
- **Headings untouched** on rows 73, 80, 81, 83, 87, 88 — DONE
  rides the dated bracket (rows 51/52 precedent; close-6 changed
  only the heading the brief named). Row 73's heading still reads
  "opened"; its bracket says "session B DONE — row DONE".
- **Two unasked marks**, both additive: the registry's
  `gather_files_for_pack` verbose rider bracketed consumed at 73B
  (its own text said row 73 consumes it when touched, and 73B
  did); §7's desk emission rule gains one sentence for row 81's
  two gates, so the rule doesn't read as stopping at row 78.
  Strike either if the close should carry only what the brief
  names.
- **Not marked**: the registry's `persist_pack_session` docstring
  entry. 73B corrected five `bale_pack.py` docstring sentences but
  its notes don't name the command paragraph; unverifiable, so it
  stands (also in `deferred`).
- **The Landed block's wave record** repeats the two HOLD causes in
  one sentence each even though the rows carry them in full —
  they're the sitting's checkpoint-thinness datum and the watch
  stamp points at them.
- **Row 89's caller list** names the four callers 83's proposal
  names and the per-file counts (×3, ×2) without assigning callers
  to files; the proposal doesn't, and I can't see the code.
- **Row 90** says "ships the doc-pin suites per the
  include-authoring rules" — it touches `docs/TARBALL.md`, so §7's
  fourth rule applies. The brief's scope line didn't say it; one
  clause.
- **Evidence 124** cross-cites entry 119 (rehearsal catching
  imagined surfaces) as the oracle-side twin of the brief's "briefs,
  not just oracles" lesson. Cut the parenthetical if unwanted.
- **Row 84's bracket** names the three suites that couldn't run;
  the brief said "three of seven" without naming them. From row
  80's notes.
- **Row 87's bracket** says the request-side line "mirrors it (edit
  5)" rather than naming §3.1 — the doc-lane notes describe edit 5
  by its style, not its section number.

## Things I did not do

- No edit to the §3 "In flight" bullets, §2, §8, or any prior
  close block (the continue-plan-001 block's sequencing bullet is
  history; the new block replaces it).
- No version-header bump (v-numbers mark regenerations).
- No renumbering, no reflow outside edited spans.
- No test suites run: the request shipped none, and
  `claude/MASTER.md` is a project doc outside the doc-pin suites'
  reach.

## Verified

`validation.sh` rehearsed in a staging-shaped copy (the edited file
at `claude/MASTER.md`, the manifest at `.bale-manifest.json`): exit
0, every claim `[agree]`. Against the unedited base it fails all
nine claimed assertions (only the two unclaimed line-ending checks
pass), so nothing claimed is tautological. Claims annotated
`observed`. Nothing needs `--slow`; the flag is accepted and
ignored. The provenance echo carries `base_files` and `checkpoint`
verbatim from the request.

## Ratification queue (for the next sitting's open)

This response's calls above, and the registry-passage backslash
strike in particular. Every other notes.md of the sitting was
ratified in-sitting per the brief.
