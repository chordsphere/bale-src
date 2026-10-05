# notes — 2026-10-05-sitting-close-deltas-20-001

The friction-points arc's record is in `claude/MASTER.md`, one file,
829 lines inserted and one line edited in place. `validation.sh`
removes exactly those insertions, restores the header line, and hashes
the result to the request's base sha256 (`4b45a684…3eb8`); it passed
that way in a simulated staging tree and failed on the unmodified
tree, as every session assertion should. Nothing else in the file
moved, which is what the reversal proves.

## Where each of the brief's eight outcomes landed

1. Header, line 14: `Last landed by:` names this sid.
2. Three sitting blocks at the end of §3, in close 19's form, one per
   desk: the 001 desk with wave 1's landing record (A, E), the
   wave2-004 desk with waves 2 and 3 (B, C, D), and the cleanup desk
   with its four bundles recorded as dispatched only. The landing
   records are from the eight telemetry records, field by field.
3. Rulings in §5 as two dated blocks (2026-10-03: rulings [1] to [3],
   the three contract-level ones as headed bullets, the light block
   verbatim; 2026-10-03/04: the wave2-004 desk's two blocks, block two
   verbatim). Ratifications in the §3 blocks, the desks' lists
   verbatim. The brief correction in the wave2-004 block and §6 entry
   220.
4. Registry: consumed brackets under the `bale status` row rider (D)
   and the triple-quote refusal (C), each entry's text kept; a stale
   bracket under "BALE.md riders for 99b's true-up"; the five BALE.md
   sentence sets verbatim in one routing entry; the PLANNER.md §4
   lesson as a queued rider for the next `docs/PLANNER.md` holder,
   verbatim; two log-hold riders (the non-exiting accessor, D's
   `test_cli_help` and internals line); a dispositions entry for every
   Proposal of the five sessions. New entries sit at the registry's
   end, above `Landed 2026-08-05, non-board`, where closes 18 and 19
   put theirs.
5. Ruling queue: a dated bracket under the BALE.md entry with the
   recount. I recounted against the `BALE_HELP.md` this request
   carries before landing the figures: every number in the brief
   holds (24 occurrences, 9 of 19 sections, 23 citations and one bare
   mention, 11 or 12 distinct sections, 9 board mentions naming 10
   numbers in 5 sections). The one line E classified differently is
   `handoff --verbose`'s `(BALE.md §5.4)`, wrapped across two lines.
6. Four watches at the end of §3 Watches, the three from the brief in
   the desk's words plus the stale open session, each with a
   re-trigger.
7. §6 entries 220 to 223: the unverified fact in B's brief, the hash
   typed before computing, D's two oracle defects with the exit-code
   lesson, the include miss. Numbering is contiguous from 10 to 223;
   validation checks it.
8. Light-block ledgers in each §3 block: the 001 desk one block of
   three questions, "as assumed"; the wave2-004 desk two, both "as
   assumed"; the cleanup desk zero and one probe. The workers:
   `clarification.rounds: 0` on all five records, and no record
   carries a `light_blocks` key at all.

Beyond the eight: a bracket on row 99 (99b's inputs grew, and its
2026-09-16 "project layer only" is history now), and one §7 bullet of
standing facts (bumpless 0.4.45, the suite counts, `BALE_HELP.md`,
`contract_docs` movement, model identities, this close's base). Both
follow what closes 18 and 19 did; both are single insertions the
reversal covers, so dropping either is a one-block cut.

## Decisions to ratify

- **The stale key is bracketed, not edited, in three places.** The
  99b riders entry (the one the brief named), the config-side carrier
  entry's 2026-09-16 consumption bracket, and row 99's 2026-09-16
  bracket all say "project layer only". Each is a true record of what
  99a landed, so I added a dated bracket under each saying the rule
  reversed at C, and left the text. The brief said to look for other
  places; those are the other two. Line 5231's "project layer only" is
  W2's `[layout]`, unrelated.
- **Rulings in §5, ratifications in §3.** Close 18 and 19's split. The
  three 2026-10-03 rulings are contract-level, so each has a headed
  bullet saying what it changed and where it landed; the block itself
  is carried verbatim as a fourth bullet, rows joined by " / ", the
  way close 18 carried the 005 desk's block.
- **The wave2-004 desk's brief correction is not a §5 line.** I
  drafted one ("a brief states only what it verified") and took it
  out: the operator ratified the worker, not a contract. It lives in
  the desk's §3 block, verbatim, and in entry 220.
- **E's unreconciled claims are a records finding, not a defect.**
  See below. Deferred in the manifest with the reason.
- **The dispositions entry says what the records bear out and no
  more.** A's `bale-internals.md` §1 true-up was routed to C; C's
  record carries the file among its `change_paths` and C's notes
  don't say what changed in it, so the entry says that rather than
  "consumed". A probe of the file would settle it; it was not worth a
  probe at a close.
- **The cleanup sessions are recorded as dispatched only**, with
  log-hold's apply stated on the brief's word, since no record of it
  shipped. The next close records them.
- **`validation.sh` embeds the insertion ledger.** The reversal is
  exact string removal of each declared block plus restoring the
  header line, then a sha256 compare; the ledger is the same data that
  built the file. The script also checks the five BALE.md sentence
  sets against `claude/responses/*/notes.md` in the tree, skipping
  when the archive is absent. It is 67 KB because of the ledger; the
  checks themselves are short.

## Where the sources and MASTER.md disagree, or the brief and the records

- The brief's Appendix A table gives A's admissions as
  `bin/bale_wizard.py` alone; A's record carries two,
  `tests/test_wizard_ui.py` too. It gives E's as "not recorded at this
  desk"; E's record carries three, at the prompt
  (`tests/test_cli_reference.py` new, `tests/test_craft_response.py`
  and `tests/test_install_precheck.py` modified out of forecast). Both
  are in the 001 desk's block under "Where the brief and the records
  part".
- E's record has `claim_verdict: {}` and `reconciliation_parsed:
  false`: no claim of E's is paired with a verdict, though its
  validation state is PASS and its notes describe a two-tree run. The
  other four records parsed. I can't tell from the record whether E's
  script printed a block bale couldn't parse or printed none; recorded
  as a finding, deferred as a possible entry.
- A's notes count seven baseline failures (4 failures, 3 errors, the
  repo `README.md` among the missing files); E, B, C, and D count six.
  The record says "six; seven in A's count" where it matters.
- The brief carries "E's proposal to mention the review gate and `?`
  in `bin/bale`'s `config init` description", and D's notes call it
  E's; it is A's notes' proposal "for session E". The dispositions
  entry says so.
- The wave2-004 brief called A's and E's notes unreachable; they were
  in `claude/responses/` all along (the cleanup desk's finding) and
  shipped here, so their BALE.md sentences land verbatim.
- The brief's Appendix A §4 count for E ("24 across 9 of 18") is E's
  own and is superseded by the recount; both are in the ruling queue's
  bracket.
- Close 19's block cites `light_blocks: 0` on row 122's record. None
  of this arc's five records carries the key; the blocks say so.
- Nothing in the brief's description of the eight records failed to
  hold: every sid, outcome, tag, checkpoint state, hash prefix, and
  version matched.

## Validation

- `validation.sh` ran in a simulated staging tree (`claude/MASTER.md`
  plus `claude/responses/`) with the change: every check PASS, exit 0.
  On the unmodified tree: the reversal, header, numbering, anchors,
  and verbatim checks all FAIL, exit 1; the file-syntax check passes
  on both, as a mechanical guard should. Claims are `observed`.
- The claims reconciliation printed `[SKIP]` outside bale staging, as
  the crafted epilogue does without `.bale-manifest.json`.
- Pre-ship, every transported quote (30 of them: the goal, the
  decomposition table, the findings, the paste-point sentence, the
  scope reading, the desk's ruling 1, both light blocks, the five
  ratification lists, the two desk pins, the lesson, the correction,
  the three watch texts, the include miss, the five BALE.md sets plus
  E's board-citation proposal, D's `fail()` paragraph, D's fourth
  Proposal, D's `pbcopy` paragraph) was compared to its source with all whitespace
  removed and bullet markers dropped. All matched. The one
  whitespace-visible change is inside E's §6.1 shape line, where a run
  of spaces before `# generated by bale` collapsed to one.
- A separate review of the three §3 blocks, the §5 blocks, entries
  220 to 223 and the §7 bullet against the eight records, the five
  notes.md and the brief, by a reader who had not seen the drafting,
  found two slips, both fixed before packing: log-hold's brief sha256
  suffix (`cd22`, I had typed `fd22`) and D's suite growth (39 more
  tests, the new file's 35 among them; I had written "35 new"). Every
  time, count and hash it recomputed otherwise held.
- The response lint is clean with `--request`.
- Line widths: 72-column wrap on prose; the five decomposition table
  rows and the long verbatim rows run past 80 as MASTER.md's own
  tables and quotes do.

## Light-block ledger for this close

Zero light blocks, zero probes, zero clarification rounds. The brief
and the context carried everything the goal needed; the two facts I
could not verify (log-hold's apply, the May sid) were out of scope and
are recorded on the brief's word, marked as such.

## Things I'm unsure of

- Whether you want the §7 bullet. It records nothing a block or
  bracket does not, except the suite counts and the `contract_docs`
  movement in one place.
- The watch for the May sid guesses at a remedy (`bale unlock` with a
  reason). I have no record of what that session was.
- `model_identity` is the configured id, `anthropic:claude-fable-5-1`;
  this surface says the serving model can differ.

## Proposals

- **What:** a board row for a pack-time include warning: when an
  included suite's module imports or fixture reads (`bale.toml`,
  `claude/changelog/`, `claude/context/adr/`, the repo `README.md`)
  fall outside the request's includes, `bale pack` says so, never
  refuses. **Why:** §6 entry 223 is the class's fourth occurrence (215
  had two, row 131 one); every worker of this arc reported the same
  six or seven baseline failures from the same files, and C's record
  put them in `includes_missing`, so the signal was already in the
  telemetry before the cleanup desk repeated the miss. **Scope hints:**
  `bin/bale_pack.py`'s include gate and the `includes_missing`
  corpus as the seed list; a desk decision first on whether the list
  is static or derived from `tests/` imports.
- **What:** surface `reconciliation_parsed: false` at apply as a
  warning line beside the worker PASS, and in `bale stats`. **Why:**
  E's record passed with no claim paired to a verdict and nothing
  said so; the calibration signal the claims field exists for was
  lost silently, which is the silent-skip class. **Scope hints:**
  `bin/bale_apply.py` where the reconciliation is parsed,
  `bin/bale_stats.py`'s claim counts; one line each.
