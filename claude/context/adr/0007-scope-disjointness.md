# ADR-0007: Scope disjointness as a mechanical contract, pack-time and apply-time

- **Status:** Proposed
- **Date:** 2026-07-06
- **Supersedes:** —
- **Superseded by:** —

## Context

Second of the four concurrency ADRs (see ADR-0006's Context for the
motivating goal). ADR-0006 lets multiple sessions be open at once; this
ADR is the correctness precondition that makes that safe.

bale's overlay model is **whole-file replacement, not a diff**: apply
overlays `files/` onto a staging copy and commits per-manifest-entry with
a per-file `cp` (BALE.md §8.3, §8.6). Two sessions packed from the same
HEAD that both touch a file therefore do not conflict the way git
branches do — there is no merge conflict to catch it. The later apply
silently clobbers the earlier session's change with a whole-file copy
authored against a stale snapshot, and the `--no-ff` merge lands clean.
Disjoint scope is a hard correctness precondition for concurrent
sessions, not a nicety.

## Decision (proposed — for ratification)

Enforce disjointness mechanically, with two faces:

- **Pack-time (conservative early gate).** Refuse a new `bale pack`
  whose declared scope intersects any open session's scope. A session's
  scope is its resolved include set, recorded in the session registry at
  pack time; includes are a *proxy* for change scope, so this gate is
  deliberately conservative — it can false-positive (a session rarely
  changes everything it was shown), but a pack it admits is one whose
  workers were never shown overlapping files.
- **Apply-time (the real guard).** Reject a response whose declared
  `changes[]` paths collide with **another** open session's scope. This
  is the check that actually prevents the clobber: whatever the worker
  did, its changes may not land on files a sibling session has in scope.

Intersection is over paths, with directory includes covering their
subtrees.

**Policy (architect-approved): hard-refuse now.** A "queue behind session
X" behavior is deferred until an orchestrator exists to consume it — for
a human operator, the refusal message *is* the queue. Workflows that only
ever hold one session open see no change in practice: with one session
open there is nothing to collide with at apply, and the pack gate engages
only when a second pack is attempted (where it replaces today's
unconditional lock refusal with a scope-aware one — the deliberate delta
noted in ADR-0006).

**Relation to orchestration:** the orchestrator's seam-finding
decomposition (ADR-0009 skeleton, step 1) is the disjointness *proof*;
this check is what makes that proof load-bearing rather than advisory. A
decomposition that wasn't actually disjoint fails at pack, before any
worker budget is spent on it.

## Consequences

- Two new bale-enforced contract rows in the BALE.md §11 sense: the
  pack-time scope-intersection refusal (pack pre-flight, where §11 row 3's
  lock check lived) and the apply-time cross-session collision rejection
  (apply pre-flight, alongside rows 10–14). Recording them in BALE.md
  belongs to the implementing session.
- The registry (ADR-0006) must **persist per-session scope** — the
  resolved include set at pack time — since both gates read it. This is
  local session state, not a wire-format change; the request manifest
  already declares `context_included`, and the registry records the
  resolved form.
- **Include-everything packs intersect everything.** bale's default scope
  is the whole working tree (BALE.md §7.2), so a default-scoped pack
  conflicts with any other open session. That is correct and intended —
  the conservative gate makes broad scope and concurrency mutually
  exclusive. Concurrency in practice requires narrow `--include` sets,
  which is exactly what an orchestrator's decomposition produces.
- The false-positive path is cheap: rescope the pack with narrower
  includes (or wait for the intersecting session to close). The
  false-negative path — a worker changing a file outside its own declared
  scope, which the cross-session check cannot see if no sibling claims
  it — remains what it is today: stay-in-the-lane policy, caught at
  review (BALE.md §2.2, TARBALL.md §8). This ADR adds cross-*session*
  enforcement; own-scope drift is unchanged.

## Notes

Out of scope for this ADR: any scheduling policy beyond disjointness
(ordering, priorities, queueing), and any wire-format change. The
deferred queue-behind behavior, when an orchestrator exists to want it,
is a superseding or extending ADR, not a reinterpretation of the
hard-refuse policy here.
