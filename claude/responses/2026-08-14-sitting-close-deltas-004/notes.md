# notes.md — 2026-08-14-sitting-close-deltas-004

Everything in the revB brief landed; nothing new was decided. Both
changed paths are inside the forecast, and `claude/INDEX.md` —
forecast, shipped — lands nothing: MASTER.md's section map didn't
shift, so the brief's "updated if the section map shifts"
conditional never fired. One brief-vs-source discrepancy needs your
ruling; the rest is placement calls you should be able to find
without reading the diff.

## Flag: the handoff-parity rider's attribution

The brief says the dropped stretch item returns to the registry
with "proposer's scope hints preserved in the oneshot notes." The
proposal carrying those scope hints (What/Why/Scope hints) actually
lives in `2026-08-14-bare-pack-excl-waiver-002`'s Proposals; the
oneshot notes record only the drop, not the hints. I applied the §5
verbatim-proposal contract: the registry entry carries the
excl-waiver proposal text verbatim, attributes it there, and
records the drop at the oneshot session's §11.2 pre-flight. If the
master desk meant a different artifact, the entry's attribution is
the thing to correct — the rider's substance is unaffected.

## Placement and phrasing calls (recording, not deciding)

- **The engraved principle** sits at the end of `docs/CLAUDE.md` §4
  (Division of Labor), framing paragraph first, then the sentence
  as its own unwrapped physical line — no markdown emphasis
  touching the line, so a byte-exact `grep -Fx` holds (the
  evidence-71 countermeasure applied to this landing's own
  verbatim cargo; `validation.sh` asserts it). The framing cites
  the blind-checkpoint doctrine via `TARBALL.md` §7, never
  BALE.md, per INDEX.md's no-BALE.md-citations rule for globals.
- **MASTER.md's §5 record** identifies the principle by its opening
  clause only ("Mechanism authority sits with the session that has
  the code in context") — enough to identify, short of a second
  copy; `validation.sh` asserts the full sentence appears nowhere
  in MASTER.md.
- **The queued planner-doctrine extraction** is a board-10 agenda
  item ("feeds S6"), not a new board row — the brief said record
  the queue entry, and board rows are cross-referenced identities I
  didn't want to mint for an unpacked session. The doc itself is
  deliberately undrafted, as instructed.
- **The sitting's landings** follow the §3 precedent shapes: a
  "Landed …, non-board" narrative block (goal commandeering, both
  landings, the supersession chain with its cost accounting) plus a
  dated "Ratified judgment calls, one line each" block (3 from
  excl-waiver, 7 from oneshot). Contract-level ratifications — the
  bare-pack mechanism with the forecast-declared reconciliation,
  the engraved principle's record-and-pointer, the blindness
  reaffirmation with thinness pinned — are a dated §5 block.
- **The sweep-order rider's carrier** is my phrasing ("rides the
  next session touching the supersession close/sweep path") — the
  brief named evidence but no carrier. Restate it if you want a
  file-named carrier instead.
- **Evidence numbering** continues 68–75 under one dated header;
  wording mine, substance per the brief; `validation.sh` asserts
  each number appears exactly once and no 76 crept in.
- **The dead-checkpoint-files note** landed as a watch (where the
  brief listed it) even though it reads more like a cleanup rider;
  it names no re-trigger beyond "any future sweep session," which
  matches its no-urgency posture.

## Claims basis

Both claims are `observed`: `validation.sh` ran end-to-end against
a staging simulation (shipped context + `files/` overlay +
`apply.sh`, manifest at `.bale-manifest.json`) — every assertion
`[PASS]`, both reconciliation rows `[agree]`. The lint ran CLEAN
after the feedback block was pasted from its own emission.
