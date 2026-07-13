# ADR-0006: Session registry — per-sid open sessions plus one integration lock

- **Status:** Accepted
- **Date:** 2026-07-06
- **Supersedes:** —
- **Superseded by:** —

## Context

The motivating goal (master-session design conversation, 2026-07-06; this
is the first of its four ADRs): evolve bale from a human-driven
request/response loop into a substrate an orchestrating Claude can drive —
decompose a large goal at seams, spawn worker sessions (sequentially at
first, concurrently later), validate their output mechanically, and
escalate to the human at the two points where judgment matters
(decomposition review and final merge review). Two axes are independent
and must stay independent: **scheduling** (sequential vs. concurrent
sessions), which the CLI changes in ADRs 0006–0008 unlock, and
**transport** (human-carried tarballs vs. a future API harness — a
separate runner that *uses* bale, not part of `bin/bale`). The CLI stays
transport-agnostic so the manual workflow remains the fallback and the
ground truth.

The mechanical blocker is the lock. `.bale/current_session` holds one sid
(BALE.md §3.4); pack pre-flight refuses while it is populated (§7.1 step
5, §11 row 3). That serializes at *pack* time — parallel worker sessions
cannot even receive their requests, regardless of how applies are
sequenced. The lock is also load-bearing well beyond pack: apply verifies
it and matches `responds_to` against it (§8.1 steps 4 and 6, §11 rows 7
and 9), and revert/retry/unlock/handoff all resolve "the" session through
it (§9.3, §9.5).

Alternatives considered:

- **Keep the single lock and queue packs.** Rejected: it serializes the
  *build* phase, which is where the wall-clock win of concurrent workers
  lives. Queueing delivery while workers idle solves nothing.
- **Per-session repo clones.** Rejected for now: heavier machinery, and
  staging (§8.3) already isolates validation per session. Clones may
  return as an option if a future need (e.g. concurrent *integration*)
  arises; nothing here forecloses them.

## Decision (proposed — for ratification)

Replace the single-sid lock with a **registry of open sessions**, keyed
per sid — the natural home is the existing `.bale/sessions/<sid>/` state
directories, promoted from "state for the one locked session" to "the
authoritative set of open sessions" — plus **one repo-level integration
lock** guarding the short git merge step of apply (the §8.6–§8.8 window).
Multiple sessions may be open concurrently; integrations serialize under
the integration lock.

Constraints (architect-approved):

- **Single-session equivalence.** With exactly one open session, the
  observable per-session behavior matches the current lock semantics
  exactly: the same §9.5 lifecycle states and transitions, the same
  apply-side verifications, the same terminal actions. (The one deliberate
  behavioral delta lives in ADR-0007 and is pack-side: a *second* pack is
  gated on scope disjointness rather than refused unconditionally — that
  delta is that ADR's entire point, not an accident of this one.)
- **No CLI surface removals.** pack/apply/retry/revert/unlock/handoff all
  remain. Commands that today resolve "the" session implicitly may need a
  sid argument when more than one session is open; with exactly one open,
  they resolve it exactly as today.
- **Default-on, no config gate.** The registry with one open session *is*
  today's behavior, so nothing needs feature-flagging.

## Consequences

- BALE.md §9.5's lock lifecycle becomes a **per-session** lifecycle: the
  three states and their transitions hold per sid rather than per repo.
  §11's lock rows re-read against the registry — row 3 ("session lock
  empty" at pack) becomes ADR-0007's disjointness gate rather than a
  global mutex; row 7 ("session lock exists" at apply) becomes "the sid
  this response names is open"; row 9 (`responds_to` matches) generalizes
  to a registry lookup instead of a comparison against the single sentinel.
- The **integration lock is new state** and needs a stale-lock story
  analogous to today's `bale unlock` (crash mid-merge leaves it held).
  Its critical section is seconds of git work, so serializing under it
  costs nothing observable.
- `bale unlock`, `revert`, and `retry` gain a disambiguation path (which
  sid?) that only engages with 2+ open sessions — single-session users
  never see it.
- This ADR removes the *serialization*; it does not by itself make
  concurrency *safe*. The correctness precondition is scope disjointness,
  ADR-0007 — the two land as a pair (0006 without 0007 is a loaded
  footgun; 0007 without 0006 is unreachable).
- One-apply-behind (meta-sessions §2): this rewires the pack and apply
  pipelines, so the session that lands it will itself run under the
  single-lock code, and the first registry-native session is its
  successor. Expect one final dose of the old refusal behavior on the way
  in.

## Notes

`.bale/sessions/<sid>/` already persists per-session state (the request
manifest, `origin_branch`, the response manifest — BALE.md §3.4, §8.2),
which is why the registry is a promotion of existing structure rather
than a new mechanism. What actually retires is the `current_session`
sentinel as a *mutex*; whether the file itself survives in some
compatibility role (e.g. as a convenience pointer when exactly one
session is open) is an implementation choice, not contract.

2026-07-13 — implemented in bin/bale by v0.3.6; exercised 2026-07-13 with three concurrent scope-disjoint doc sessions; recorded per the audit cleanup session (2026-07-13-multi-agent-docs-007).
