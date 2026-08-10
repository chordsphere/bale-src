# notes.md — 2026-08-10-board-10-orchestration-doc-003

Doc-only session; both changed paths sit inside the write forecast
(`claude/context` covers the new file; `claude/INDEX.md` is named).
No out-of-forecast paths to enumerate. Things worth your eyes:

## Judgment calls

1. **Skeleton item 5 and the escalation-queue addition are folded
   into one section (§8, "Escalation and the clarification queue").**
   The brief said the board-10 additions land "as sections, not
   addenda," and two sibling sections both named Escalation would
   have split one subject across two anchors right before S4 starts
   citing anchors. The two human judgment points from the skeleton
   survive inside §3 (the four controls) and §8/§9; nothing from
   item 5 was dropped. If you want the queue material under its own
   separate anchor instead, that's a small re-split — say so before
   S4 packs.

2. **INDEX.md's closing inventory sentence updated ("two explainers"
   → "three explainers") — one line beyond the brief's "touch
   nothing else in INDEX.md."** Adding the entry while leaving the
   count falsified the same file twenty lines apart, and INDEX
   honesty is a DOCS.md contract rule; I read the brief's
   constraint as guarding against restructuring, not against
   keeping the index self-consistent. Flagged rather than shipped
   silently; validation asserts the count agrees with the listed
   entries, so kicking this back would need the entry change
   reworked too.

3. **The four controls are restated in §3, sourced from MASTER.md
   §1's ratified floor.** The ratified passage ranks the
   spec-friction principle "with the four controls," and MASTER.md
   is deliberately kept out of ordinary worker sessions — so a
   future citer holding only this doc needs the controls named or
   the ranking claim dangles. That's a deliberate cross-doc
   restatement of master-context material into worker-reachable
   doctrine, DOCS.md §9's sanctioned-parallelism shape: if MASTER.md
   §1's floor ever changes, §3 here must change in the same session.
   Note also the controls' four-item form (ratified floor) is richer
   than ADR-0009's skeleton item 5 (two judgment points); the doc
   follows the ratified floor and presents the two points as members
   of the four.

4. **Explainer ordering in INDEX.md: appended after
   meta-sessions.md.** DOCS.md says explainers order
   most-referenced-first; historically that's bale-internals.md.
   The harness era will likely make orchestration.md the
   most-pulled entry — reorder in a later doc touch if that plays
   out; I kept this session's INDEX diff minimal.

5. **Evidence citations are by entry number only** (e.g. "(evidence
   50)"), per the brief, with §1 of the doc telling readers the
   numbers resolve in MASTER.md §6. Since MASTER.md stays out of
   ordinary worker requests, a worker holding only this doc can't
   dereference them — acceptable, I think, because the citations
   are provenance for the doctrine, not required reading to apply
   it. If that's wrong, the alternative is one-clause inline
   summaries per citation, at real length cost.

6. **"Escalation" as a bare grep anchor is satisfied many times
   over** (§3, §8 heading, prose). The checkpoint string can't
   distinguish which occurrence it wanted; I assumed presence
   anywhere in the doc is the contract, matching how the brief
   phrased it ("these strings must each appear in the doc").

## Claims

The unclaimed `file presence and encoding` row in
`validation_will_run` is deliberate: it's near-tautological given
bale's own hash pre-flight, so it runs unclaimed per §5.3.

No Proposals this session — S4/S5/S6 already carry the follow-on
work this doc feeds, and queueing them again here would just be
noise.
