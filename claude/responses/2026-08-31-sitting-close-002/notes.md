# notes.md — 2026-08-31-sitting-close-002

The close document landed as ratified; everything below is either a
placeholder resolution the brief delegated to me or a place where the
live MASTER.md's conventions forced a departure from the embedded
wording. Nothing else in the three files changed.

## Placeholder resolutions

- **Board numbers: 58, 59, 60.** The live board's highest row is 57,
  so `<next>` = 58 (exchange constants, install-side parity),
  `<next+1>` = 59 (the `bin/bale_relay.py` extraction), `<next+2>` =
  60 (the re-emit path). The ADR-0017 Notes entry accordingly ends
  "see board row 60" per the brief's substitution instruction. I
  treated the shipped `context/claude/MASTER.md` as the live board —
  the request's own constraint distinguishes it from the stale desk
  copy, and bale packs from the live tree — so no probe was needed.
- **ADR Notes entry wording.** The brief's §1 instruction quotes the
  entry with an em-dash after the date ("2026-08-31 — implemented…");
  the embedded document's §5 uses a colon. I followed the §1
  instruction, which is the operative one and postdates the draft.

## Convention-forced departures (check these on review)

- **Arc table "below" pointers resolved.** The embedded table's
  outcome cells say "cause below" and "(bad oracle, below)",
  pointing at the close document's own §4. Landed in MASTER.md those
  pointers would dangle, so they resolve to "§6 entry 90, specimen
  b" (the packaging correction's cause — the worker-reach specimen)
  and "§6 entry 88" (the crafter retry). If I mapped the packaging
  session's cause to the wrong specimen, the fix is one cell.
- **Ledger entry 90 tense.** The embedded text says the rule is
  "proposed for PLANNER.md §4's checklist"; this same response lands
  it, so the entry reads "landed on PLANNER.md §4's checklist at
  this close" — "proposed" would have been stale at birth.
- **Routing reversal landed at three sites.** The 2026-08-25 routing
  is recorded in three places on board 10's row (the main S6 bracket
  and the two item-level brackets). The full §3 narrative landed as
  one new dated bracket after the main one; the two item-level sites
  got one-line pointer brackets so no stale "routes to the harness
  project" statement survives un-annotated. If the desk prefers the
  item-level sites untouched, the two pointer brackets are
  self-contained deletions.
- **Sitting record contents.** The brief says "the §1 arc table
  lands with the sitting's record"; I read that as §1's content —
  the table plus its live-traffic-evidence paragraph, which has no
  other home — and the record otherwise follows the §3 "Landed …"
  form: a Proposals-dispositions bullet carrying the embedded §2's
  fourth bullet (crafter index header, §5.9.2 two-audiences), a
  one-bullet pointer to the routing reversal (full text on board 10,
  not duplicated), and the convention-supplied closing line
  ("Sitting closed at the milestone; sequencing of the new rows
  among the smalls is the next desk's call") — that last sentence is
  mine, not the document's.
- **Crafter-index-header fold-in rule recorded twice, deliberately.**
  Once on row 59 (where its brief-author will read it) and once in
  the sitting record's dispositions bullet (which points at row 59
  rather than restating the rule).
- **Header line.** MASTER.md's "Last landed by:" line edited in
  place to this sid, per the line's own stated convention — an edit
  beyond the embedded document's list but required by the doc.
- **No §3 watch added for the vacuous-passes item.** Entry 89 calls
  itself a "standing watch item," but the close document queues no
  §3 Watches entry and I did not invent one; the ledger entry is its
  record. Say the word if it should also get a named re-trigger in
  the §3 list.

## Validation note

The generic ADR guard (`craft_response.py --doc-assertions
--adr-dir`) is deliberately absent from `validation.sh`: its
sanctioned-flip reverse-transform admits status flips only, and
would `[FAIL]` on the desk-ratified dated Notes append this session
lands. In its place is a stricter session-specific reverse-transform
— stripping the exact appended entry must reproduce the shipped
baseline's sha256 — plus byte-identity pins on ADRs 0001–0016
(0010–0012 covered by the constraint, the rest by append-only). Both
claims are `observed`: the full script ran green against a simulated
staging overlay before packing.
