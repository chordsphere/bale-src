# Notes — 2026-09-24-sitting-close-deltas-19-001 (close 19)

Close 19 lands in `claude/MASTER.md` only: line 14 is edited in place and
766 lines are inserted in 22 ranges; nothing else is touched. Before I
started, the base matched the stamp: 11,710 lines, sha256
`2f64cbff…d879d`.

`validation.sh` puts close 18's Proposal 2 into practice. It deletes the
22 declared ranges, restores the old line 14, and hashes the result back
to that stamp.

## What landed, by section

- **§3, Watches.** A dated bracket on the unswept-sid watch. It fired
  twice in wave 11, in shapes the watch did not name (see "A question for
  you" below).
- **§3, registry: retirement brackets.**
  - Retired: the §5.9 courier, the declared-departure lint, the handoff
    stamp, the dossier colon, and the checkpoint include rule (both
    halves).
  - Kept open: the §5.2.2 emitter entry, for its `--fragment` clause
    alone, which row 43's Proposal 2 merges into.
  - W3's half of the §11.7 entry is recorded from row 43's notes.md; the
    "picker" half stays.
- **§3, registry: new entries.**
  - The fence-aware `top_level_section` entry sits physically beside the
    phrase-pins entry, as the brief asked.
  - The rest are at the list's end in the brief's order: close 18's
    Proposal 1; the call-5 rider together with row 122's Proposal 2; the
    fixture rule; the micro's Proposals 1 and 2; row 43's Proposal 1;
    row 122's Proposals 1 and 3; the report's five Proposals, each naming
    S6; the held stemwell Proposals; and the dispositions entry, which
    now sits directly above `Landed 2026-08-05`.
- **§3, sitting blocks.** Two blocks after close 18's four: the 006
  master, which carries wave 11's dispatch and landing record, and
  design-010, which carries the stemwell arc.
- **§4, the board.**
  - DONE brackets on rows 43, 121, 122, 123, 124 and 125.
  - Row 45's bracket: first wave complete, findings by watch item, the
    second wave gated on S6.
  - New rows 129 to 133, from the report's Proposals, each quoted
    verbatim, with S6 as consumer.
- **§5.** A 2026-09-23/24 block holding the 006 desk's eight rulings,
  including reversal as close practice.
- **§6.** Entries 213 to 219. The first four follow the HOLD ledger's
  four items; then come the clustering entry, the two design-desk
  defects, and the arc's numbers.
- **§7.** The 0.4.45 landmark, the rehearsal verbs, the read-only
  `base_files: {}` fact, the adr/bin include fact, the two
  model-identity spellings, and stemwell's facts.

## The probe (TARBALL.md §4.5)

The brief says `context-stemwell.tar.gz` ships beside the request, but it
did not reach the chat, so I built nothing and sent one paste-back probe,
`stemwell-context-locate`. It came back whole: trailer 30 lines, and 30
lines counted.

What it established:
- The snapshot is at
  `/home/chordsphere/stemwell/.bale/outbox/context-stemwell.tar.gz`: 39,012
  bytes, mode 0600, sha256 `330b928d…513f`, 48 members.
- Its record members are exactly the seven notes.md and nine telemetry
  records the brief names.
- The shell is bash 5.2 on WSL2.

You attached the file with the paste. Its sha256 matched the probe's, so
everything about the arc here comes from that copy.

This is a fifth specimen for row 117: an attachment that did not arrive,
answered with a probe plus the file on the reply (Proposals).

## Where I overrode the brief (the records win)

1. **"retry, applied" (the wave table, micro row).** The micro's record
   has a `rejected` retry at 13:27:11Z before the applied one. It was
   refused at the provenance gate because the checkpoint had changed
   since pack. I landed it (§3's 006 block, §6 entry 214).
2. **"Three of this desk's oracles held…" (HOLD ledger, last paragraph).**
   - The records carry two checkpoint HOLDs: row 43's v1 and the micro's
     v1.
   - Row 43's v2 was amended away before it ran. It would have held the
     corrected tarball, which carries two mentions of the flag where v2
     wanted zero.
   - §6 entry 217 lands the records' count, says so, and names the
     clustering as the 006 desk's authoring practice, as you asked.
3. **The design-010 row ("read-only, opened 2026-09-23").**
   - Its record closed `abandoned` on `command: unlock` at 00:57:39Z. That
     is 41 seconds before stemwell's seed v1 was unlocked `abandoned` at
     00:58:20Z.
   - The desk went on to author seed v2 and the wave, so the closure
     reason misdescribes the sitting.
   - I recorded the facts on the watch bracket and in the design-010
     block without guessing at intent.
4. **The report's note on wave2a's model string ("the report's own
   note", Facts for §7).** Ruling 4 applied to the picker's name "Claude
   Opus 5.5" gives exactly `anthropic:claude-opus-5.5`. The other records
   carry the API string's spelling, `claude-opus-5-5`, and so does row
   122's bale-src record. Both spellings appear in bale-src too, since the
   micro and row 43 used `5.5`. So I recorded two sources rather than one
   slip (§7, the design-010 block, and the §11.7 registry bracket).

The upward report itself also parts from the records in two places,
recorded in the design-010 block:
- Wave3's probe *is* in its record, as `linkage` `{kind: probe, point:
  pre-build}`; only its timing is missing, which row 133 now says.
- "Five parked worker proposals" lists six. The stemwell notes carry
  seven, of which one (the trailing space) is moot.

Everything else I checked against the records held: every sid, time,
outcome, admission, claim count (57 rows: 54 agree, 1 n/a, 2 disagree),
interval, and the 22 min 25 s and 45 min 52 s figures.

## Judgment calls to ratify

1. **"Drops the dossier colon" retires the entry.** I read block one [3]
   as taking the entry's own "droppable", so the bracket says "dropped.
   Retired". If you meant only "not in this micro", strike "Retired" and
   the entry rides on.
2. **The §5.2.2 entry stays open, for `--fragment` alone.** Row 43 landed
   the rest (VERBATIM-3). "43's `--fragment` question merges into its
   existing entry" only works if that entry still exists.
3. **Close 18's call-5 rider and 122's Proposal 2 share one entry.** The
   interim doctrine is quoted verbatim, the entry says 0.4.45 has
   overtaken it, and the holder lands 122's replacement sentence. The
   fixture rule from HOLD 2 is its own entry beside it, both on
   PLANNER.md §4.
4. **The micro's Proposal 4 is recorded as consumed**, across row 43's
   §3.4 sentence and row 122's BALE.md §6.7/§8.9 paragraphs (0.4.45's
   changelog names it). The brief doesn't list it.
5. **The report's Proposals are quoted in full on rows 129 to 133.** Their
   registry entries point at the rows rather than quoting twice. This is
   close 18's Proposal 1 applied: the text travels with the record.
6. **The refused wording, both lists.**
   - The brief lists "hostile", "hazards", "the architect must not know";
     the report lists "hostile", "planted", "must stay ignorant".
   - I have neither brief's text, so §6 entry 218 carries both lists,
     attributed.
   - My own prose calls stemwell a "small messy codebase" and avoids
     that register, per Proposal 4.
7. **§4 bracket style and §6 indentation.** Brackets follow close 18's
   style; rows and entries use the existing 4-space continuation.
8. **Dates.** Brackets are dated 2026-09-24 from this sid. The two block
   openers are dated 2026-09-23 from their sittings' sids.
9. **Sequencing.** No new standing line was ruled at the 006 desk, so the
   006 block states where 43 and 45 now stand and writes no line.
10. **My `model_identity`** is `anthropic:claude-opus-5.5`, taken from the
    model name this session's own system prompt shows. I can't see the
    picker (AGENT.md §11.7).

## Validation

Seven checks, each claimed `pass` and `observed`:
- the reversal to the base hash;
- line 14;
- all 14 sids from the brief's two tables;
- §6 continuous 212 → 213…219;
- §4 continuous 128 → 129…133;
- the heading list unchanged;
- the registry's end.

Results:
- **On the landing:** all seven PASS.
- **On the unmodified base:** six FAIL. The headings check passes there
  too, deliberately: it is a preservation guard the brief asks for, not a
  test of the change.
- **Negative:** changing one character on an untouched line (5000) fails
  exactly the reversal check.

My first run failed the registry-end check on a wrap in my own assertion.
It compared the entry's last physical line; it now compares the joined
entry.

Runtime is under a second. The script writes only `.validation-logs/`
and a mktemp dir it removes, and it runs Python with `-B`.

The blind checkpoint is not in the request, by design.

About the tools: I did not read `tools/response_lint.py` line by line.
- I read its usage docstring.
- I audited its imports: stdlib only, no subprocess or socket.
- I checked its write sites: none.

I then used it for `--emit-feedback-mechanical` and a plain run. I did not
use the crafter; the response is hand-assembled and the lint checks it.

## Session ledger

- One probe, complete.
- Zero light blocks, zero clarification rounds.
- One tool-use pause, resumed on "Continue" with full context.
- No compaction.

## Proposals

1. **Row 117 has a fifth specimen.**
   - **What:** record this session's opener on row 117. The brief's
     "attached by the operator" file did not reach the chat; a probe
     located and fingerprinted it, and the file arrived on the reply.
   - **Why:** the probe here did one real job the row's other shapes
     don't: it gave the attachment a hash to verify against. That is an
     argument for the row's eventual shape.
   - **Scope hints:** MASTER.md row 117, a bracket at the next close.
2. **Ask about design-010's unlock.**
   - **What:** a one-line operator answer on whether the 00:57:39Z
     `unlock` of `2026-09-23-board-45-hostile-repo-design-010` was meant
     for it or for stemwell's seed v1.
   - **Why:** if it was stray, the record's `abandoned` misdescribes a
     sitting that delivered. The watch's question, when a design
     sitting's sid should close, now has a specimen of it closing by
     hand at the wrong moment.
   - **Scope hints:** none in the tree; a desk ruling.
3. **Reversal ranges from the builder, not by hand.**
   - **What:** a close's `validation.sh` could take its insertion ranges
     from a small sidecar the build step writes, rather than a literal
     string.
   - **Why:** the literal is exact but brittle to any rebuild. I
     regenerated mine from the build script, not by hand.
   - **Scope hints:** desk practice for close oracles; a tool only if
     closes keep growing.
