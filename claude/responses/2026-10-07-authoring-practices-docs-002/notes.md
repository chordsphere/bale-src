# notes — 2026-10-07-authoring-practices-docs-002

Seventeen practices, three riders, two docs, nothing removed. Every
edit is a pure insertion: `diff` against the shipped base shows no
deleted or changed line in either doc, and both heading lists are
unchanged. The doc suites are green, and `validation.sh` was run twice,
as the brief asked (results at the end).

## Decisions to ratify

**Placement and phrasing, PLANNER.md §3 (seven bullets).**

- Bullet 7 ("A pointer stays unique…") goes right after "Re-verify
  section cites at authoring time": both are about anchors a brief
  locates by.
- Bullets 2 and 1 follow it, in that order. The mangling bullet names
  the hazard, and the grading bullet is the rule built on it. I put 2
  first because 1 reads better once the reader knows why text needs
  reconstructing. The mojibake forms (`ΓÇö`, `┬º`, `ΓÇª`) are in the doc
  inside backticks, so a reader can recognize them.
- Bullets 3, 4, 5, 6 go after "Ship decision context into the request"
  and before "Unfilled scaffold slots are loud", which stays last.
  Bullet 3's body points at §4's floor bullet as its complement; the
  brief's "4.4 below" read as that bullet (11), and I cite it as "§4's
  floor rule", not by a number.

**Placement and phrasing, PLANNER.md §4 (seven bullets plus the
rider).** One cluster sits right after "Rehearse against the brief's
bytes, never a stub", in this order: bullet 9, the rehearsal sentence,
then bullet 10.

- Bullet 9 opens with "This is the bullet above, carried to the
  landing the brief cannot supply". It then splits the two cases: a doc
  insertion means the landing is derived and no stub is written; code
  means a stub written from the brief and discarded is the only
  rehearsal. That reconciles it with "never a stub" instead of
  contradicting it.
- The rehearsal sentence is the ruling's text word for word, with only
  the first letter capitalized. It is an **unbolded bullet** so that no
  authored lead competes with the seventeen verbatim ones. Precedent:
  §4's last bullet is unbolded.
- Bullet 10 points forward to bullet 12. Without an excepthook, an
  oracle that reads its manifest at `bale open` time tracebacks with
  exit 1, which bale reads as an expected HOLD, not a defective oracle.
  So the two bullets depend on each other, and the text says so.
- Bullet 11 sits after "Per-scenario fixture isolation" (fixtures).
- Bullets 13 and 14 sit after "Locators are strict line anchors" (where
  an oracle gets its data, and what it may act on).
- Bullets 8 and 12 sit after "A failed control exits 2", the rule they
  each extend.

**PLANNER.md §6.**

- The cadence sentences are **appended to the "End at milestones"
  bullet** as two continuation lines, each sentence whole on its own
  physical line after the two-space list indent. The brief allowed
  either form. Appending keeps the sentences byte-exact without
  inventing a bold lead for a bullet of their own, and it adds lines
  without editing the bullet's existing ones.
- Bullet 15 follows the light-block ledger bullet. It says the ledger
  records such a question as "resolved by events". I did **not** add
  that phrase to the ledger bullet's disposition list ("answered,
  as-assumed, formal, or unanswered"), because that would reword an
  existing bullet. See Proposals.

**16 and 17: one paragraph, one bullet.**

- 16 landed as a **bold-lead paragraph at the end of TARBALL.md §7.1**,
  right after the announced-writes paragraph. Reads now sit beside
  writes. I kept it out of §7.2, whose numbered list is pinned at items
  1–6, and out of §7's lead, which is pinned too. It names the base the
  way §3.4's include rider does: "the subtree the project's
  `[validation] base` pattern lives under".
- 17 landed as a bullet in §4.3, right after "Read-only per shape".

**Where I departed from the brief's rationale for 17.** The brief says
a dry run "still stages and logs". The code says it doesn't stage. It
logs, and it extracts:

- `cmd_apply` calls `set_log_file(.bale/logs/<sid>.log)` before the
  dry-run branch, and `set_log_file` appends to that file.
- `apply_pipeline` extracts the tarball into a `tempfile` directory.
- The dry-run returns before staging.

So the bullet says it "extracts the tarball into a temporary directory
and appends to the session's log under `.bale/`". The rule itself is
unchanged. (`bale_apply.py`'s comment at the dry-run branch claims it
"touches neither the working tree nor `.bale/`", which the log write
contradicts. See Proposals.)

**TARBALL.md §3.4 riders.**

- **The `--dry-run` row** sits directly after `--json`, matching
  `bale help pack`'s order. Its refusals are `--json`, `--context`, and
  outside a git repository. `--context` is beyond the brief's list:
  `BALE_HELP.md` names it, and `cmd_pack_dry_run` refuses outside a
  repo. The row points at `bale help pack` for the full gate list
  instead of copying it.
- **The `bale open` sentence** is a paragraph of its own after the
  final pinned sentence ("…in every project it is delivered as the
  stored pack argv…"). The pinned paragraph is byte-identical, and
  `validation.sh` asserts that it still ends there.
- The AGENT.md §11.2 / TARBALL.md §3.4 sanctioned pair needs no twin
  edit. AGENT.md delegates "form, flags, and their mapping" to §3.4,
  and none of its pinned extracts moved.

**Heading counts.** The brief's "29 headings (`##` and `###`)" and
"57" only hold if you count every heading line: the `#` title and
TARBALL.md's `####` subsections included, fenced code excluded (the
`apply.sh` scaffold has a `# No additional…` comment line). Counting
only `##`/`###` gives 28 and 48. `validation.sh` compares the full
fence-aware lists against the base, in order, so either reading is
covered.

**Not landed, as the brief directs.**

- "When a checkpoint HOLDs, the planner block goes to the planner
  first" is already mechanized: it is the HOLD card's `send first:`
  line (`relay_send_first`), and TARBALL.md §7 already describes the
  addressed blocks. Nothing added.
- The fourth registry rider ("three planner practices": ledger tagging
  in §3, a GUESS-label sentence in §2, transcripts as a `--context`
  tarball) is declined at this holder. No verbatim text travels with
  it, and two of its three items are harness-era. It stays on the
  registry.

**Nothing the suites made me reword.** All five doc suites passed on
the first staged run. The suites did shape where things went: nothing
lands inside §7.2's list or §7's lead, and the §3.4 sentence is not
appended to a pinned sentence.

## Validation, run twice

`validation.sh` writes only under `.validation-logs/<stamp>/`. That
includes its assertion helper, written there and run from there.
Every Python runs under `-B`, and it reads `docs/` and runs `tests.*`
by module name, so it never walks `claude/checkpoints/` or
`claude/responses/`.

- **Staged (change applied):** all 11 checks pass.
- **Unmodified base:** the 5 doc suites pass, as they should: they
  guard against regressions and don't detect this change. These 4 session assertions
  fail: the seventeen leads, the cadence sentences, the rehearsal
  riders, and the `--dry-run` row. These 2 pass on both by design,
  because they are invariants, not change detectors: the untouched-doc
  hashes and the heading lists. The "pinned paragraph stands
  unextended" sub-assertion inside the riders check is an invariant
  too.

I also ran the whole `tests/` suite (`python3 -B -m unittest
discover`) on both trees.

On both trees: 1866 tests, OK, 48 skipped. The counts and skips are
identical, so nothing outside the doc suites reads these docs in a
way the insertions disturbed.

## Proposals

- **What:** add "resolved by events" to the dispositions the
  light-block ledger bullet (PLANNER.md §6) lists.
  **Why:** bullet 15 now records that disposition, but the ledger
  bullet's list still names four ("answered, as-assumed, formal, or
  unanswered"). A reader of the ledger rule alone won't know the fifth
  exists. Extending the list is a reword of an existing bullet, which
  this session's scope forbade.
  **Scope hints:** `docs/PLANNER.md` §6, one clause.
- **What:** correct the comment at `bale_apply.py`'s dry-run branch
  (and, if wanted, `bale help apply`'s `--dry-run` text) to say the
  dry run appends to the session log.
  **Why:** the comment says it "touches neither the working tree nor
  `.bale/`", but `set_log_file` has already pointed logging at
  `.bale/logs/<sid>.log`, and the dry run logs there. TARBALL.md §4.3
  now states the true behavior, so the code comment is the outlier.
  **Scope hints:** `bin/bale_apply.py` near `if args.dry_run:` in
  `cmd_apply`; possibly the help string in `bin/bale`. Out of scope
  here (`bin/` is read-only).
