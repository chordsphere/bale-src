# notes — 2026-10-06-sitting-close-deltas-22-005

Close 22 is in `claude/MASTER.md`, one file. I inserted 335 lines in
twelve blocks and edited the `Last landed by:` line in place. Nothing
else moved. `validation.sh` removes exactly those blocks, restores the
header line, and hashes the result to the request's base sha256
(`7748ce44…431e`). I ran it in a simulated staging tree, where it
passed. On the unmodified tree every session assertion fails except
the board guard, and that one is meant to pass on both trees (see
Validation).

My base matched what close 21 left. It is 13,941 lines, which is close
21's 13,305 plus its 636. Its header names close 21, §6 ends at 224, the
board ends at 135, and the hash is `provenance.base_files`. So nothing
the desk didn't know about landed in §1, §2 or §8, and no clarification
was needed.

## Where each of the brief's twelve outcomes landed

1. **Header**, line 14.
2. **The wave block**: a new §3 block after the close desk's block. It
   follows close 21's form:
   - the landing record, field by field from the two records;
   - what landed, from the two notes.md;
   - the ratifications and the routings;
   - what this close verified in the bytes;
   - the no-upward-report line;
   - the light-block ledger;
   - where the brief and the records part;
   - the deltas.
3. **Ratifications**, in that block:
   - close 21's seven decisions, each by its bold lead-in, lifted from
     its notes.md;
   - the row-99 bracket and the §7 bullet, both kept;
   - no bracket on §5's "recorded by the next close" line;
   - the bump as shipped.
4. **§5**: one block at the end, dated 2026-10-06 with the bounds the
   records give. It carries Appendix A's three rows joined by " / " and
   the operator's reply, both verbatim.
5. **Routings**:
   - the bump's first Proposal is a new entry at the end of the ruling
     queue;
   - its second is a dated bracket at the end of the 99b routing entry;
   - one dispositions entry at the end of the registry, above `Landed
     2026-08-05, non-board`.

   Both Proposals are lifted from the bump's notes.md and flattened.
   The archived copy of close 21's notes.md has no Proposals section, and
   the dispositions entry says so.
6. **C's "eight keys"**: there are two dated brackets, one after C's set
   in the 99b routing entry and one at the end of the wave2-004 desk
   block's "What landed" bullet. I found no other place in the document
   that says eight keys. Each bracket names `suggest_wizard_values`,
   lists the seven keys, and says whether C landed eight is not
   recorded.
7. **The `bale status` row**: a dated bracket under close 21's in the
   registry. See the first item under "Things to look at closely".
8. **§6 entry 225**, after 224. §6 now runs 10 to 225.
9. **No upward report**: one bullet in the wave block. It quotes
   PLANNER.md §20.2's first sentence.
10. **The WSL `clip.exe` watch**: a dated bracket. It quotes the four
    specimens from the brief, and the watch stays open.
11. **The close desk's record**: a dated bracket under that block's
    light-block ledger bullet. See decisions below.
12. **§7**: one bullet with the version landmark (lead-in "Version
    landmark: 0.4.46", as the earlier landmark bullets do), the bump's
    suite counts, the `contract_docs` and model identities, and this
    base.

## Decisions to ratify

- **The close desk's bracket sits under its ledger bullet, not after
  the block.** §3's sitting blocks have never carried a bracket before.
  The registry and Watches indent a bracket under the item it qualifies.
  The ledger bullet ("zero light blocks, zero probes") is the line it
  supersedes, so I put it there.
- **C's seven-keys bracket in the 99b entry sits right after C's set**,
  in the middle of the entry, not at the end with the other brackets.
  The brief says "at each place this document says eight", and that
  place is C's set.
- **The `bale status` bracket says the label is still unread.** See the
  first item under "Things to look at closely". I didn't probe for
  `bin/bale`, because the brief's outcome is to say what the shipped
  bytes show, and they show that. Entry 225 carries the same refinement
  in one sentence.
- **§5's block carries the light block's three question rows, not its
  sentinel lines or its `Reply:` line.** Closes 20 and 21 did the same.
  If you want the full block, it is a one-bullet change.
- **One §5 pointer bullet and no headed bullets.** None of the three
  items changes a contract. [1] and [2] ratify and [3] routes, so the
  bullet points to their homes and says so. Close 21 used headed bullets
  only for rulings that minted something.
- **References say "of close 22", not "of this date".** Close 21's
  blocks, brackets and ruling-queue entries are also dated 2026-10-06.
  "of this date" would have been ambiguous, and the reviewer caught it
  in my first draft.
- **The WSL bracket adds one observation of my own, marked as mine.**
  This session's opener reached my chat as "no network access ΓÇö
  conveniences". That is its only non-ASCII character, and it arrived
  mangled. The bracket says this was seen by close 22's worker and not
  by the brief.

## Where the brief and the records part

Nowhere on the records. The brief's table held: tags by relay,
checkpoint PASS, worker PASS, no admissions. So did its counts: 636
lines, §6 at 224, the board at 135, 64 rows and eight sessions, and 1866
tests with 47 skips. The wave block lists what rests on the brief's word
alone, because no record of the close desk shipped:

- the tags;
- the desk still being open;
- its `packed_at`, as close 21 recorded it;
- the light block and the reply;
- the block's timing, inferred;
- the chat answer;
- the relay mangling.

## Things to look at closely

- **The `bale status` label is not in `bin/bale_report.py`.** That file
  holds `describe_clipboard_state`, the row's value, and its docstring
  calls it the row "labelled `clipboard`". It also holds the `--json`
  `clipboard` object. But no code in it emits the label. The 0.4.46
  record attributes "the status row is labelled `clipboard`" to
  `bin/bale`, which this pack didn't ship. So the value and the JSON are
  read now, and the label's own bytes still aren't. A probe that greps
  `bin/bale` for the row would settle it.
- **The wave block's intervals to the desk's pack** (43 min 18 s and
  1 h 37 min 25 s) are counted from 19:11:37Z, which rests on close
  21's brief. The block says so.
- **Version stamps.** This request is stamped `bale_version` 0.4.46. By
  the day's counter (-003, -004, then -005) it is the first pack after
  the bump. The §7 bullet calls it the first stamped 0.4.46.

## Validation

- `validation.sh` ran in a simulated staging tree. The tree held:
  - this `claude/MASTER.md`;
  - the two archived notes.md under `claude/responses/`;
  - the two records under `claude/telemetry/`;
  - `claude/changelog/0.4.46.json`;
  - the two `bin/` files;
  - the request's `PLANNER.md` as `docs/PLANNER.md`, whose sha256
    matches `contract_docs`;
  - the manifest as `.bale-manifest.json`.
- **With the change:** all nine checks pass, exit 0, and all eight
  claims agree.
- **On the unmodified tree:** these all fail, exit 1:
  - reversal, header, §6, anchors;
  - verbatim (every block absent);
  - seven keys;
  - width.

  File syntax passes, as a mechanical check should. The board check
  passes on both trees by design. It is a guard that this close adds no
  board row, like the bump's "existing records unchanged" guard.
- **The insertion ledger is embedded**, as closes 20 and 21 embedded
  theirs. The script writes `checks.py`, `ledger.json` and `run.log`
  under `.validation-logs/<ts>/`, and says so on its first line.
- **Verbatim, by construction and by check.** Every carried quote was
  lifted from its source bytes by line range and flattened, never
  retyped. That covers both Proposals, the seven lead-ins, Appendix A's
  rows and close 21's `includes_missing`. The script checks 19 quotes:
  - 16 against their sources in the tree: the notes.md, a record, the
    changelog, `bin/bale_report.py` and `docs/PLANNER.md`;
  - 3 from the brief for presence only, since the brief isn't in the
    tree.
- **Seven keys.** The check parses `suggest_wizard_values` in the
  tree's `bin/bale_config.py`. It asserts that both brackets name
  exactly those seven keys.
- **Independent review.** A reviewer who hadn't seen the drafting
  checked the insertions against the records, the notes.md, the
  changelog, both `bin/` files, PLANNER.md, the manifest, the brief and
  the base. Every interval, count, hash, boolean and verbatim quote held.
  It found three errors and five wordings, all fixed:
  - a WSL-bracket sentence presented as the brief's that was my own
    observation;
  - the "rests on the brief's word" list, which was too short;
  - close 21's Proposal split, which miscounted the riders by including
    `contract-doc`;
  - the ambiguous "of this date" references;
  - "provenance" for the brief hash, which sits under `readme`;
  - the §7 lead-in form;
  - two wordings in the `bale status` bracket;
  - an uncheckable clause in the checklist bracket.
- Inserted lines wrap at 72. Code spans are never split across lines,
  so no quote's whitespace changes inside backticks.

## Light-block ledger for this close

Zero light blocks, zero probes, zero clarification rounds.

## About the request's tools

I read both tools' module headers, their imports, every file-write site
and `--help`. They are stdlib only, with no `subprocess`, socket or HTTP.
The lint writes nothing. The crafter writes into the response directory
only under `--write`. I used the crafter for the manifest skeleton, the
`apply.sh` no-op and the validation epilogue, and the lint over the
finished directory with `--request`.

## Things I'm unsure of

- Whether you want the label settled by a probe of `bin/bale` before
  the relabel counts as verified. As it stands, the bracket says
  exactly what was and wasn't read.
- `model_identity` is the configured id, `anthropic:claude-opus-5-5`.
  This surface says the serving model can differ.
