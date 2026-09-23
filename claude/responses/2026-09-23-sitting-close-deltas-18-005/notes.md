# Notes — 2026-09-23-sitting-close-deltas-18-005 (close 18)

Close 18 is in `claude/MASTER.md`: line 14 edited, 894 lines inserted,
nothing else touched. `validation.sh` proves the insertion-only claim
by removing its declared ranges, restoring line 14 and hashing back to
the stamped base `a8bbbeee…70a9`. The base matched before I started:
10816 lines, the same sha256.

What landed, by section:

- §3: four sitting blocks after close 17's last one: 001, 004,
  design-001 and 005, in the brief's order. Plus the new watch on the
  unswept successor sid.
- Registry:
  - ten retirement brackets on the nine entries wave 10 consumed;
  - a "stays" bracket on the §5.9 courier entry;
  - fifteen new entries in the brief's order, ending on the
    dispositions entry.
- §4: DONE brackets on rows 77, 100, 116 and 118, and rows 121 to 128.
- §5: the 2026-09-22 cadence block and the 2026-09-23 block of nine
  rulings.
- §6: entries 205 to 212, and pointer brackets on 119 and 188.
- §7: the 0.4.43 landmark and five more bullets.

## Where the brief and the records part

- **Rider micro claim count.** The brief says "nine claims each
  `observed`". The record carries thirteen, all observed and all
  `agree`: nine `tests.*` module claims and four session assertions.
  §3 records thirteen and says why the two counts differ.
- **W3's apply.** The brief left W3's `applied` attempt to the record.
  The record reads 03:07:57Z, `command: retry` on the same tarball
  name, checkpoint v2 PASS with `stamp_matched: false`, no admissions.
  That is the operator's retry of the held tarball against the amended
  oracle, not a new worker response. The brief's "no worker retry"
  holds.
- **The 004 record.** It carries one `opened` attempt for the two
  desks. Row 123 uses that as its specimen.

Everything else I checked against the records held, including every
`packed_at`, `created_at`, sweep and bundle hash the brief gives.

## What did not travel, and what I did instead

- **The upward report's "Follow-on rows" list and its (b)
  recommendation.** The brief asks for the list to be quoted verbatim
  on row 100's bracket, but only the report's name and hash reached
  this request. I did not paraphrase it as if quoting.
  - Row 100's bracket places (a) to (f) and Proposals 1 to 4 by the
    brief's own mapping, and says the text did not travel.
  - Row 126 says the same of the recommendation.
  - A desk holding `claude/context/board-100-arc/` can bracket the
    quote in.
  - Listed in `includes_missing`.
- **Close 17's notes.md.** Its Proposals 1 and 2 got registry entries
  worded from the brief, with no quoted text, and they say so.
- **The blind checkpoint.** It is not in the request, by design, so I
  could not "run it twice" as the brief's last section asks. My
  `validation.sh` asserts every outcome the brief says the oracle
  grades. I ran it on the landing (exit 0, 14 PASS) and on the base
  (exit 1: every session assertion FAILs, only the file-syntax check
  passes). A negative that drops one period from VERBATIM-1 in §5
  fails exactly the VERBATIM check.

## Judgment calls to ratify

1. **Bracket dates.** Every bracket I wrote is dated 2026-09-23, the
   close's date from its sid. The landing date of each event is in the
   bracket's text.
2. **Opener dates.** Each §3 opener is dated from its own sitting's
   sid, so 001, 004 and 005 read 2026-09-22 and design-001 reads
   2026-09-23.
3. **Line shape of verbatim text.**
   - One unwrapped line each, byte-exact: VERBATIM-1 and VERBATIM-2,
     the nine rulings, the nine signed items, and the operator's two
     messages. `validation.sh` checks each byte-exact; the two
     VERBATIM sentences are checked by `cmp` in §5 and in the registry
     rider.
   - Light block one is wrapped at 72 columns, words verbatim, as close
     17 carried its blocks; validation compares it word for word.
   - The operator's reply broke across two lines in the brief. I read
     the break as one space, the 008 desk's convention.
4. **The nine signed items sit verbatim in the 004 block.** The brief
   quoted them but did not say where they land. §3 is their natural
   home, and it lets rows 121 to 123 and the registry point at "item
   N" rather than re-quote.
5. **Item 2's interim doctrine.** Item 2 ends: "Until it lands,
   PLANNER.md §4 doctrine: a desk with `bin/` in context rehearses the
   line in a fixture before delivery." The brief gives no placement.
   I named it on row 122 and gave it no registry entry. If you want it
   to reach PLANNER.md before the verbs land, it is a one-line rider
   for the next `docs/PLANNER.md` holder, beside the item-5/8 entry.
6. **Ruling landings, finer than the brief's map.** The brief maps
   rulings 2 and 3 to W3.
   - Ruling 2: layer 4's key, `[layout] agent_dir`, landed at W2.
   - Ruling 3: the alias and the `contract_docs` `oneOf` landed at W2.
   - Ruling 4: landed at W1 in the docs as well as at W2 in the
     schema.

   Each bullet says so; all of it is from the brief's own W1/W2
   landing lists.
7. **A "stays" bracket on the §5.9 courier entry.** The brief says it
   stays. I bracketed that, with the pointer to the tools micro's
   Proposal 3 beside it, rather than leave the entry silent.
8. **Evidence entries.** Entries 205 to 212 are my own text from the
   brief's candidates and the records, one candidate each. I kept to
   the brief and the records. The notes.md shipped in `context/` I
   used only to check wording, never as a source, and I removed one
   phrase that came from them.
9. **Specimens on row 116.** Row 116's bracket names the two wave-10
   micros' pre-ruling `model_identity` spellings as the last specimens
   of the old format; every W record spells it
   `anthropic:claude-fable-5.1`.
10. **My own `model_identity`.** It is `anthropic:claude-opus-5.5`, from
    the model picker as shown to this session (AGENT.md §11.7).

## Light-block ledger (ruling 6's practice)

This session:

- zero light blocks, zero probes, zero clarification rounds;
- one tool-use pause, resumed on "Continue" with full context;
- no compaction.

The 005 desk's ledger for the four sittings is carried in §3's 005
block.

## Proposals

1. **A close brief that asks for a verbatim quote carries the text.**
   - What: when a brief tells the close to quote something verbatim,
     the brief carries that text or the request ships the file.
   - Why: this close was asked to quote the upward report's
     "Follow-on rows" and to quote row 126's recommendation from it,
     and neither traveled; the 005 desk had the file in hand. The same
     gap left close 17's Proposal texts unquotable. A brief that
     carries its quotations never meets this.
   - Scope hints: `docs/PLANNER.md` §3, one sentence, for its next
     holder. Or just desk practice.
2. **Prove insertion-only by reversal.**
   - What: a close's oracle or `validation.sh` can prove "insertions
     only, but for line 14". Remove the declared inserted ranges,
     restore the old line 14, and compare the sha256 against
     `provenance.base_files`.
   - Why: it is one exact check in place of many heuristic ones, and
     it catches any stray edit anywhere in a 10k-line file.
   - Scope hints: desk practice for close oracles; the `c_insertions`
     check in this response's `validation.sh` is a working copy.
