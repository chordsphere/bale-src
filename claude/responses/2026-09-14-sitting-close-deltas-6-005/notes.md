# notes.md — 2026-09-14-sitting-close-deltas-6-005

One file, `claude/MASTER.md`, 443 diff lines (435 added, 8 removed),
additive except three in-place spans: the header's last-landed-by
line, row 75's heading, and the §7 VERSION landmark sentence. Every
edit went in as an anchored replacement that had to match exactly
once — twenty of them, driven by a script that refuses on any other
count. It's all prose; the diff is worth a skim end to end.

Base file hash matched the manifest's `base_files` stamp before I
touched it. No CRLF anywhere, before or after. No chat round with
the desk this time: nothing in the brief rose to a blocking intent
gap (§10.1 step 2, and evidence 115 is exactly the specimen I would
have become), so every call below is flagged here for ratification
or correction rather than asked.

## Brief defects the desk should record

- **The registry strike for the "row 74 rides board 47's TARBALL.md
  touch" carrier has no registry entry to strike.** That carrier
  lives in exactly two places: row 47's 2026-09-10 bracket and
  close-5's sequencing bullet in §3. I struck it where it lives —
  a dated bracket on row 47 — and left the close-5 block untouched
  (closed blocks are history). The §3 close block's board-deltas
  bullet says "row 47's carrier clause struck" rather than
  claiming a registry strike.
- **"0.4.26 → 0.4.27 — a claim; verify from telemetry."** Verified,
  but indirectly: row 78's own record stamps the *request's*
  provenance at 0.4.26 and carries `bin/VERSION` in `change_paths`
  with no version assertion in its claims; the corroboration is
  this request's provenance stamp, 0.4.27. The row and the §7
  landmark say so in those words.
- **Row 75's attempt story: "retry `applied`".** Telemetry says the
  `retry` command was the *refused* attempt (02:29,
  `scope-drift-refused`); the applied attempt (02:45) is `command:
  apply` on the retry tarball (`response-002-retry.tar.gz`). The row
  reads "`retry` `scope-drift-refused` once → the retry tarball's
  apply `applied`". Same story, correct verb.

## Facts trued up against telemetry rather than the brief

- Row 75: opened 2026-09-10T13:32Z, applied 2026-09-11T02:45Z; the
  request stamp is 0.4.25 and the applied attempt's `assert:
  bin/VERSION reads 0.4.26` passed — so 0.4.25 → 0.4.26 as the brief
  said. Both graded attempts `stamp_matched: true`; the applied
  attempt `clarification.rounds: 0`. The brief's "checkpoint PASS
  3/3" is not in telemetry (only `state: PASS, exit_code: 0`); the
  3/3 comes from the worker's notes and I kept it.
- Row 73A: opened 2026-09-11T03:57Z, applied 2026-09-14T19:51Z,
  request stamp 0.4.26, checkpoint PASS on first apply,
  `stamp_matched: true`, `rounds: 0`, `includes_missing:
  tests/test_per_sid_checkpoint.py`. The row says "applied
  2026-09-14 at 0.4.26 (tests-only, no bump)". The brief's
  "seventeen tests" is the worker's own count of *new* tests; the
  record's claim key says "20 tests" because discovery includes the
  happy suite's three — consistent, so I kept seventeen.
- Row 78: opened 2026-09-14T20:05Z, applied 20:38Z, checkpoint PASS
  first apply, `stamp_matched: true`, `rounds: 0`.
- The brief's "sitting-open version check was satisfied by the
  request's provenance stamp, 0.4.26" is about the master session's
  own request, whose record did not ship; recorded as the brief
  states it, unverified.

## VERBATIM handling

- All seven VERBATIM passages land byte-exact modulo line wrapping
  (`validation.sh` asserts each whitespace-normalized). That
  includes the brief's `\"` escapes inside the three operator quotes
  on rows 87 and 88 — the doc already carries that spelling in a
  verbatim-carried registry entry (the `\"handoff\"` / `\"pack\"`
  lines), so I kept the brief's bytes. If those backslashes are the
  brief's rendering rather than the operator's keystrokes, strike
  them: six characters across two rows.
- The row-75 supersession quote is the brief's rendering (single
  quotes around 'deliberately no config key', no bold); the worker's
  notes use double quotes and bold the clause. I landed the brief's
  bytes, since that's what carried the VERBATIM mark.
- No pointer-resolving parentheticals were needed inside any
  VERBATIM span this time.

## Placement calls (the brief's "flag anything you had to interpret")

- **§7 VERSION landmark edited in place**, not additively — the
  manifest constraint names only the header line and named
  brackets as in-place edits, but close-5 edited this same sentence
  in place and flagged it, and an appended parenthetical would have
  left "VERSION 0.4.25" standing as a false statement. The sentence
  now reads 0.4.27 at board 78, with 0.4.26 at row 75 and 0.4.25 at
  row 71 as the trail, and the four doc/contract-doc sessions
  bumpless. Strike back to additive if you read the constraint
  strictly.
- **Rows 73, 74, 76 closed by dated brackets**, headings untouched
  (rows 51/52 precedent: `[date: DONE — sid …]`). Only row 75's
  heading changed, because the brief named it and the checkpoint
  grades it. Row 73's heading still says "opened" — session B is
  queued, so the row isn't DONE.
- **Rows 78 and 79 born DONE** with the DONE marker in the heading
  (rows 67/70/71 precedent for rows that open and land in-sitting).
- **Rows 80–88** — the brief said one to three sentences each; 87
  and 88 run longer because their VERBATIM quotes are long and the
  desk notes were asked for. I did not trim the desk notes.
- **Two new §3 watches** appended at the end of the Watches list,
  before the Ruling queue: the two-prompts watch and the
  exchange-adoption watch. The brief speaks of "the
  exchange-adoption watch" as if it existed; it didn't as a §3
  entry (only evidence 112 named the gap), so I opened it, dated,
  with the brief's re-trigger.
- **Registry brackets**, both additive: the `--sid` entry marked
  consumed (disposed deferred by 73A, record on row 73); and the
  `gather_files_for_pack` rider's premise corrected — the entry's
  verbatim text says the function "already carries" a `verbose`
  kwarg, and 73A found it does not (only `walk_for_pack` does). The
  brief didn't ask for that second bracket; it's the factual
  correction the desk ruling's "three-line rider" wording implies.
  Strike it if the registry should carry only what the brief names.
- **Pointer brackets on rows 51 and 68.** The brief's "verified for
  you" list named both anchors without saying what to do there; I
  read that as an invitation. Row 51 gets a one-sentence pointer to
  row 87 (the naming variance defeats its matching); row 68 gets a
  pointer to row 78's ordering pin (evidence 122). Both are
  cross-references, not new facts. Strike either if unwanted.
- **Row 47's strike** is a bracket saying the 2026-09-10 clause is
  struck, with the rest of that bracket's cargo explicitly standing.
- **§7 working-style clause** appended to the existing
  Master-session working style bullet as a new sentence after
  "(ADR-0015)." — it supersedes the bullet's older "briefs delivered
  as downloadable files for --readme-file" without editing it; the
  old words now read as the named fallback. The desk emission rule
  gained its extension as a sentence in the same bullet. The
  include-authoring rules and the hook acceptance store are two new
  bullets at §7's tail.
- **§5 block** in the established "New, ratified <date> (…):" shape
  with bold-lead bullets; each contract points at its row home.
- **Row 78's verification note** (the operator's global post-apply
  hook ask, no row) sits on row 78 as the brief said, ending in the
  defect-row instruction.
- **The row-73 bracket carries the seven findings** at the brief's
  length rather than compressing them — it's the decision record
  session B will be packed from.
- The one-line "row 88 / row 79 same gap class" cross-pointers are
  on both rows and in evidence 118.
- **Evidence 113–122** map 1:1 onto the brief's ten; 114 says "the
  third include-authoring rule" (the `schemas/` rule) rather than
  the fourth, because the guard that caught 75 is the schema
  self-containment guard. If you meant the fourth, it's one word.

## Things I did not do

- No edit to the §3 "In flight" bullets, the §2 milestones, or any
  prior close block (close-5's sequencing bullet still names the
  row-74/board-47 ride; it is history, and the new block replaces
  it).
- No version-header bump — v-numbers mark regenerations.
- No renumbering, no reflow outside edited spans, no CRLF or
  trailing-whitespace changes.
- No test suites run: the request shipped none, and `claude/MASTER.md`
  is a project doc outside the doc-pin suites' reach.

## Verified

`validation.sh` was rehearsed in a staging-shaped copy (the new file
at `claude/MASTER.md`, the manifest placed at `.bale-manifest.json`)
and exited 0 with every claim `[agree]`; run against the unedited
base it fails seven of eight assertions (the version-header check is
unchanged by design), so the checks are not tautological. Claims are
annotated `observed`. The response-manifest provenance echo carries
`base_files` this time — row 76 has applied, and the shipped lint
accepts it.

## Ratification queue (for the next sitting's open, per the close block)

This response's judgment calls above. Every other notes.md of the
sitting was ratified in-sitting per the brief; this is the only debt
the close block carries forward.
