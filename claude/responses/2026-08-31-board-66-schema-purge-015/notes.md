# notes.md — 2026-08-31-board-66-schema-purge-015

Description strings only, verified mechanically: I stripped every
`description` key from each edited file and its shipped original and
compared the remainders — all five are structure-identical. No key,
type, enum, required list, or constraint moved.

Judgment calls to ratify:

1. **ADR citations stayed.** ADR-0015/0016/0017 references remain in
   the descriptions. They're not in the ratified deny set, and the
   five global docs cite ADRs by number the same way, so I read them
   as house style rather than dangle. If the board wants them out
   too, that's a follow-up sweep, not this one.
2. **S-digit epoch labels became version anchors, not deletions.**
   Several telemetry descriptions use the sitting label as an epoch
   boundary ("absent only on pre-S5 records"). Deleting the label
   outright would have deleted the boundary, so I anchored each to
   the version that landed it: S2 → v0.4.5, S5 → v0.4.6, B1 →
   v0.3.8, B2 → the v0.3.9 launch. "S6 design" (a future sitting)
   became "future harness-era design". The load-bearing meaning
   survives; the label doesn't.
3. **One dated sitting citation rewrote beyond the literal deny
   set.** telemetry's claim_basis description cited "the section 3
   watch's closure, ratified 2026-08-03's claim-basis precedent" — a
   sitting-date citation, not an S-digit or session-letter form. It
   dangles identically from any other project's vantage and the
   string was already under edit, so it now reads "the closure of a
   standing calibration watch, under the ratified claim-basis
   precedent". Kick it back if the board wants dated forms kept.
4. **BALE.md pointers resolved to the unnamed form.** Where a
   description leaned on a BALE.md section for tool-side mechanics
   (relay contract, apply gates, provenance verification), I used
   TARBALL.md's own idiom — "the bale tool's own documentation" —
   or folded the meaning in, rather than inventing a new global
   home. orchestration.md citations all had a real global home and
   went to PLANNER.md sections 15/16/17 by topic.
5. **Validation's deny sweep is deliberately broad.** Beyond the
   brief's named shapes it also rejects any standalone
   letter-digit token (`\b[A-Z][0-9]\b`), which is what catches
   residue like a stray "B2" or "D1" once its surrounding board
   citation is gone. Nothing legitimate in these five files matches
   that shape today.

## Proposals

- **Teach the self-containment guard the deny shapes.** The purge
  holds only until the next schema edit reintroduces a BALE.md
  pointer or a board number. The tests-side self-containment guard
  (a sibling's territory this wave) should learn this session's
  deny set — the seven patterns in this response's `validation.sh`
  are paste-ready. Why: the shapes are regular, the guard already
  walks doc/schema text, and this session's validation only proves
  the five files clean at apply time, not forever. Only after the
  board 59 sibling lands, to avoid forecast collision on the tests
  tree.
