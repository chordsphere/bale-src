# ADR-0012: Bale is a substrate for agent-driven orchestration

- **Status:** Accepted
- **Date:** 2026-07-13
- **Supersedes:** —
- **Superseded by:** —

## Context

ADR-0006's Context carries the motivating goal of the concurrency
set (master-session design conversation, 2026-07-06): evolve bale
from a human-driven request/response loop into a substrate an
orchestrating Claude can drive. That goal steered ADRs 0006–0009,
but it was never itself recorded as a ratified direction — it lived
as motivation folded into 0006's Context and as a Proposed doc plan
in ADR-0009.

Two things changed on 2026-07-13, and together they are this ADR's
ratification. First, the architect stated the direction directly:
bale is a substrate for agent-driven orchestration, no longer a
single user-to-Claude tool (the request README of session
2026-07-13-multi-agent-docs-007 is the durable record of that
statement). Second, the concurrency mechanics were confirmed live:
three scope-disjoint sessions were packed, built, and applied
concurrently on bale 0.3.6, exercising the ADR-0006 registry and
both ADR-0007 gates end to end under a human operator.

Relation to ADR-0009: that ADR (Proposed) plans *where orchestration
doctrine lives and when* — skeleton in the ADR now, project
explainer when harness work starts, global doc when orchestration is
real. This ADR **complements** 0009 rather than superseding it: it
ratifies the destination that 0009's staging serves, and changes
nothing about the staging or its promotion triggers.

## Decision

Bale evolves into a substrate an orchestrating Claude can drive:
decompose a goal at seams, spawn concurrent worker sessions,
validate their output mechanically, and escalate to the human at the
two points where judgment matters — decomposition review and final
merge review.

**No orchestration harness exists yet.** This ADR records the
destination and the standing commitments below — not a description
of current operation. The manual workflow is the present tense
throughout this repo and the docs; anything harness-dependent stays
future-tense until the harness exists.

Standing commitments, binding from now on:

1. **The CLI stays transport-agnostic.** `bin/bale` never assumes a
   courier. Scheduling (sequential vs. concurrent sessions) and
   transport (human-carried tarballs vs. a future API harness) are
   independent axes, per ADR-0006; the harness, when it exists, is a
   separate runner that *uses* bale, not part of `bin/bale`.
2. **Docs and workflow language are role-neutral.** Planner, worker,
   and operator name the roles, and any role can be held by a human
   or an agent. TARBALL.md §1's role definitions already anchor
   this; new doc language follows it.
3. **The manual workflow remains fallback and ground truth.** Every
   capability the orchestrated path will rely on must stay
   exercisable by a human operator, and the manual path is where
   contract behavior is defined and verified. The 2026-07-13
   three-session concurrent exercise is the model: shipped behavior
   proven by hand before any harness consumes it.

## Consequences

- The direction is now a citable record rather than motivation
  buried in another ADR's Context. Future orchestration ADRs cite
  this one for the destination and ADR-0009 for the doc plan.
- ADR-0009's promotion triggers are unchanged and still gate any
  standalone orchestration doc. Documenting *shipped* concurrency
  behavior in the global docs (the session-registry scope contract
  and its planning consequence) is not the deferred orchestration
  doctrine — 0009's deferral covers doctrine for a reader that
  doesn't exist yet, not tool behavior that already ships.
- Foreclosed: doc or workflow language that hard-codes a specific
  role-holder ("the human", "Claude" where a role is meant), and CLI
  behavior reachable only through a harness.
- Trust phasing, blind checkpoints, HOLD triage, and escalation
  doctrine remain ADR-0009's skeleton, untouched here.

## Notes

Origin: ADR-0006's Context (the motivating goal). Ratification: the
architect's direction of 2026-07-13 plus the live three-session
concurrent exercise on bale 0.3.6, both carried in request
2026-07-13-multi-agent-docs-007's README. Status is Accepted at
creation — the direction was stated by the architect directly;
review at apply is the check.
