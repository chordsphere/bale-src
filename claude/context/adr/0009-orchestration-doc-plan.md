# ADR-0009: Defer ORCHESTRATION.md; record the doctrine skeleton here until promotion

- **Status:** Proposed
- **Date:** 2026-07-06
- **Supersedes:** —
- **Superseded by:** —

## Context

Fourth of the four concurrency ADRs (see ADR-0006's Context for the
motivating goal and the scheduling/transport axis split).

Orchestration needs doctrine: how the orchestrator decomposes a goal at
seams, authors validation checkpoints, enforces disjointness, judges
HOLDs, escalates to the human, and how trust in it is phased up. One
premise anchors all of it: the observed failure class in the manual
workflow is **misunderstanding, not code defects** — so validation
checkpoints must be authored *blind*: from the request, before any
implementation exists, by the orchestrator, never by the worker that
builds against them. This is ADR-0002's rejection of self-oracles,
promoted from the test harness to the workflow level.

The question this ADR answers is **where that doctrine lives and when**
— the same shape as ADR-0001 (defer `TESTS.md`, house the doctrine, name
the promotion trigger). The same DOCS.md pressure applies: there is no
harness, no orchestrator, and no operator to read a standalone doc yet;
a global `ORCHESTRATION.md` today would also pay ADR-0001's named extra
cost (a fifth entry in `GLOBAL_DOCS` and the pack-time injection change
in `bin/bale`) before any content justifies it.

## Decision (proposed — for ratification)

**Defer a standalone global `ORCHESTRATION.md`**, per the ADR-0001
precedent, and stage the doctrine in three steps:

1. **Now:** record the doctrine's skeleton in this ADR (below), so the
   decisions already made have a durable home.
2. **When harness work starts:** draft a project explainer
   (`claude/context/orchestration.md`, per DOCS.md §4.3–§4.4) carrying
   the working doctrine alongside the harness it governs.
3. **When orchestration is real** — concretely, when a session has been
   driven end-to-end by an orchestrator rather than a human: promote to
   an injected global doc, paying the `GLOBAL_DOCS`/injection cost in a
   dedicated session, exactly as ADR-0001 scopes the `TESTS.md`
   promotion.

The worker-agent contract needs almost nothing new: **CLAUDE.md and
TARBALL.md already are that contract.** What they eventually need is a
thin addendum covering an orchestrator (not a human) on the far side of
probes, HOLDs, and handoffs — same artifacts, different reader. The
global docs stay **worker-agnostic**: a worker session behaves
identically whether a human or an orchestrator packed its request.

One rule is already earned in practice and binds from now on: **the
orchestrator ships decision context into the request — it never assumes
the worker shares its conversation.** (The manual-workflow analogue is
this very session: the design conversation was folded into the request's
README rather than assumed remembered.)

### The doctrine skeleton

1. **Decomposition at seams.** The orchestrator splits a large goal
   along real boundaries into worker sessions that each fit a context
   window — CLAUDE.md §11.2's seam discipline, promoted from
   self-rescoping to planning. The decomposition is also the
   disjointness proof (ADR-0007) that the mechanical gates then make
   load-bearing.
2. **Blind checkpoints.** The orchestrator authors each worker's
   validation checkpoint from the request, before implementation exists.
   The worker never authors the oracle it is graded by (workflow-level
   ADR-0002).
3. **Disjointness enforcement.** Mechanical, per ADR-0007 — pack-time
   intersection refusal, apply-time collision rejection.
4. **HOLD judgment.** The orchestrator triages a HOLD: correctable
   (revert, repack with failure context, `corrects:` pointer per BALE.md
   §8.8) versus escalate to the human.
5. **Escalation.** Two human judgment points, by design: decomposition
   review (before workers spawn) and final merge review (before the
   integrated result is accepted).
6. **Trust phasing.** Manual → orchestrated decomposition → mechanical
   inner loop → autonomous spawn. Transitions are gated by
   `diagnostics.json` bailout/HOLD clustering **per work class** — the
   longitudinal signal TARBALL.md §5.8 was built to carry decides when a
   class of work is trusted at the next level, not a vibe.

## Consequences

- No new doc ships this session; the skeleton above is the durable
  record, and INDEX.md gains only this ADR.
- Both promotion triggers are observable events, not vibes: "harness
  work starts" (step 2) and "a session ran end-to-end under an
  orchestrator" (step 3). Until the first fires, the answer to *"should
  orchestration.md exist?"* is no.
- The step-3 promotion inherits ADR-0001's cost shape knowingly: a
  documentation split plus the `bin/bale` injection change, one
  dedicated session. Whether the promoted doc injects into *worker*
  requests (workers may not need orchestrator doctrine) is a question
  for that session — the worker-agnostic rule above is the constraint it
  must satisfy either way.
- Out of scope, restated from the design brief: the API harness itself
  (a separate runner that uses bale, not part of `bin/bale`), concurrent
  scheduling policy beyond disjointness, and any wire-format change.

## Notes

ADR-0001 deferred a doc because the content didn't exist yet; this ADR
defers one because the *reader* doesn't exist yet. Same discipline,
different missing ingredient — in both cases the skeleton is scaffolded,
the trigger is named, and the file waits.
