# orchestration.md — working orchestration doctrine

> Project explainer, per ADR-0009 step 2. The working home of
> orchestration doctrine until the step-3 promotion.
> Section numbers are stable (`DOCS.md` §6.4): future work — the
> escalation-record schemas first — cites this doc by section, and
> those anchors do not renumber.

---

## 1. Status and promotion path

This doc exists because ADR-0009's step-2 trigger fired: harness
work has started, so the doctrine skeleton recorded in that ADR
moves into a project explainer that lives alongside the harness it
governs. ADR-0012 ratifies the destination this doctrine serves:
bale is a substrate an orchestrating agent can drive — decompose a
goal at seams, spawn concurrent worker sessions, validate their
output mechanically, and escalate to the human where judgment
matters.

**No orchestration harness exists yet.** Per ADR-0012, the manual
workflow is the present tense: everything harness-dependent below is
written in the future tense, as doctrine the harness will implement,
not as a description of current operation. Where a sentence is
present-tense, it describes behavior that already ships (the
clarification response, the disjointness gates, revert, the
telemetry records) — proven by hand before any harness consumes it,
which is the standing commitment: the manual path remains fallback
and ground truth.

Language is role-neutral throughout (ADR-0012): *planner*, *worker*,
and *operator* name roles, and any role can be held by a human or an
agent. *Master* (or *orchestrator*) names the planning agent of the
harness era; *architect* names the human. Evidence citations of the
form "(evidence N)" point at `MASTER.md` §6, the live-traffic
evidence pile this doctrine is earned from; the entries are cited,
not restated.

Promotion: when orchestration is real — a session driven end-to-end
by an orchestrator rather than a human — this content promotes to an
injected global doc in a dedicated session, per ADR-0009 step 3.
Until then, this file is the doctrine's one home.

---

## 2. The foundational principle: minimize specification friction

Ratified by the architect at the board-10 spec-intake sitting, and
stated here as a load-bearing principle ranking with the four
controls (§3), not below them. The ratified kernel:

Ambiguity is the enemy, not capability.

The dominant observed failure class in this workflow is
misunderstanding — the `MASTER.md` §1 floor already says so, and the
evidence pile keeps confirming it: mechanical validation passes
cleanly on work that answers the wrong question (evidence 32, 53),
and a wrong fact in a brief costs more than a missing one (evidence
21). As model capability grows, the binding constraint on "seed
document in, application out" is not what a worker can build; it is
the specification gap between what the architect meant and what the
request transported. The scarce resource that closes that gap is
architect attention.

Therefore: minimizing friction on specification clarification is a
foundational design principle of the harness era. Every design
decision — schema, queue, control surface, telemetry field — will be
tested against two questions: *does this maximize spec-decisions per
unit of architect attention,* and *does every decision made accrete
durably into the spec?* An answer that lives only in a chat is not
accreted (evidence 40); an answer paraphrased on its way into a
request is not the answer (evidence 49). The escalation contract
(§8) is this principle made concrete; the four controls (§3) are the
attention budget it spends.

---

## 3. The four controls

The ratified floor (`MASTER.md` §1, restated here so this doc stands
alone for its future citers): human checkpoints converge on four
"what"-shaped controls —

1. **Ratify decompositions** — before workers spawn.
2. **Answer escalations** — the questions only the spec's author can
   answer.
3. **Review final merges** — before the integrated result is
   accepted.
4. **Grant trust expansions** — the deliberate step that moves a
   work class up the §11 phasing ladder.

Everything below these four goes autonomous per work class as the
trust ledger earns it. The controls exist because misunderstanding
is the dominant failure class and mechanical validation structurally
cannot catch it; they are the misunderstanding control surface, and
the specification-friction principle (§2) governs how cheaply each
one spends the architect's attention. They are deliberately
heavyweight and ceremonially distinct from the quick clarification
queue (§8): a control is a judgment point the architect prepares
for, not a notification stream.

---

## 4. Decomposition at seams

The orchestrator will split a large goal along real boundaries into
worker sessions that each fit a context window — `CLAUDE.md` §11.2's
seam discipline, promoted from self-rescoping to planning. A worker
refusing an oversized goal and returning seams is the happy path;
the orchestrator, not the worker, weighs split economics plan-wide
(evidence 3). The decomposition is also the disjointness proof that
the mechanical gates (§6) then make load-bearing: forecasts are
declared per session at pack time, and a decomposition whose
forecasts collide is wrong before anything spawns.

What live traffic has earned about the craft of packing, all of it
binding on an orchestrator because every instance was committed by a
planner role:

- **Decision context ships into the request; the packer never
  assumes the worker shares its conversation** (evidence 1). The
  request is the whole interface.
- **Include sets are a completeness obligation.** The
  missing-context class — load-time imports, runtime-loaded files,
  brief-referenced unshipped text — has recurred with the architect,
  the master, a worker, and a sub-master as packer (evidence 13,
  58). The execution-context manifest is the countermeasure; the
  class is why packing is graded (evidence 6).
- **A wrong fact in a brief is worse than a missing fact** (evidence
  21). Missing facts trigger probes; wrong facts trigger
  investigations the worker cannot decline, at context prices.
  Corollaries: read files whole before making claims about them;
  pin doc touches only against structure actually read (evidence
  24, 34).
- **Transported decisions ship verbatim, never paraphrased**
  (evidence 49). A constraint that flattens a prior proposal's
  conditional transports a different decision.
- **Scope statements ride the artifact, not the chat.** The
  `resolved_scope` stamp closed the class of workers inferring scope
  from the shipped file list (evidence 41, 44); chat-delivered
  commands and briefs are convention-only artifacts, and the durable
  row is the spec (evidence 40, 45, 47).
- **Ordering constraints are claims.** Serialization the
  orchestrator imposes between sessions is stated with rationale so
  it can be contested (evidence 23); a delegated-to gate is named
  with its firing condition, not presumed to fire (evidence 42).
- **The orchestrator's own session packs scopeless** — empty
  recorded scope, forecasting nothing, so its read set locks no
  worker out (evidence 36, 46). Masters end sittings at milestones
  rather than resolving open questions on a tired context (evidence
  15).

---

## 5. Blind checkpoints

The orchestrator will author each worker's validation checkpoint
from the request, before any implementation exists. The worker never
authors the oracle it is graded by — ADR-0002's rejection of
self-oracles, promoted to the workflow level, and the standing test
generalizes: for any new mechanism, ask whether the entity under
evaluation authors the input its evaluation rests on, and where it
does, split mechanical from self-reported and weight the mechanical
(evidence 16).

The mechanics already ship on the manual path: a planner-authored
checkpoint pinned at pack time runs in staging beside the worker's
`validation.sh` — checkpoint first, both always run — and the worker
neither reads, ships, nor declares it. Checkpoint blindness is keyed
to the write forecast (ADR-0015), with a read-side ships-the-oracle
refusal backing it. The two streams coexist by design: the blind
checkpoint is the misunderstanding control; the worker's
`validation.sh` is the calibration stream; neither replaces the
other, and the trust ledger (§11) consumes both.

Harness-era prerequisite, already ratified as doctrine: checkpoint
and validation scripts will run sandboxed for unattended execution —
network off, writes confined to staging (ADR-0016). Attended applies
under a human reader are the present-tense exception that made the
bare-subprocess era tolerable; autonomy does not inherit it.

---

## 6. Disjointness enforcement

Mechanical, and already shipping: pack refuses a new session whose
write forecast intersects an open session's forecast, and apply
rejects a response whose changes cross a sibling's forecast — the
one refusal that takes no override (ADR-0015, superseding ADR-0007's
include-keyed form). The read/write separation matters to
orchestration specifically: read context no longer locks
(evidence 25, closed by evidence 60), so concurrency is bounded by
genuine write collisions, not by shared reading.

Two earned rules ride on the gates. **Predicted refusals are control
flow; surprise refusals are incidents** (evidence 43): a
decomposition whose plan names each gate firing in advance walks
through refusals as sequencing, while the same refusal unstated
invites an unlock that throws a session away. An orchestrator will
plan with the gates, not around them. And **queues go stale under
concurrency** (evidence 61): a worker verifies the shipped tree
against its goal before building, because an intervening sibling may
have closed the queued item — the drill-down doctrine catching at
zero cost what scheduling cannot.

---

## 7. HOLD judgment

A HOLD is well-formed wrongness: the tarball is mechanically sound,
staged, and inspectable on its `bale/<sid>` branch, and a judgment
still says *don't merge this*. The orchestrator will triage a HOLD
into one of two paths: **correctable** — revert, repack with the
failure context shipped into the new request, `corrects:` pointer
preserving the lineage — versus **escalate** to the architect, when
the wrongness traces to the spec rather than the work.

The triage judgment is itself graded input: packer errors are a
grading signal on the planner, not (only) on the worker (evidence
6, 11), and a correction round that repairs a ratified-but-
underspecified decision is flagged for ratification, never shipped
silently (evidence 2, 10). The misunderstanding-control doctrine has
functioned live on this surface: a worker receiving a stale
redundant goal verified the tree, refused to fabricate a change set,
and asked (evidence 53) — the behavior HOLD triage exists to reward.

---

## 8. Escalation and the clarification queue

The escalation contract is the specification-friction principle
(§2) made concrete, and it subsumes an existing channel rather than
inventing one. Today, a blocking intent gap flows worker → architect
→ master → architect → worker via the clarification response
(TARBALL.md §5.9, ADR-0011), with the architect as transport. The
harness era moves the architect from transport to overseer: the
master will answer what its own context can answer and escalate the
rest — the same artifact, a different courier, exactly the
courier-agnostic framing the clarification was designed under. The
first delegated arc's structured upward report — partitioned landed
/ ratified / escalated / on-watch — is the working prototype of this
contract's shape (evidence 50).

The escalation-record schemas inherit the following as requirements;
this section is their doctrine home, and detailed design stays with
the harness spec-intake, as does the rest of this doc's mechanism
detail.

- **Dedup before the architect sees anything.** Concurrent workers
  will ask overlapping questions; the master dedupes them, and the
  schema carries the dedup lineage — which worker questions a
  surfaced question answers — so one architect answer fans back out
  to every asker.
- **Answers accrete into the spec, mechanically.** An answer lands
  in the seed document or in a decisions ledger beside it, and ships
  verbatim into future requests — the answer-to-amendment path is
  schema, not convention. This is §2's accretion test enforced at
  the record level, with the verbatim-transport rule (evidence 49)
  built in rather than relied on.
- **Questions arrive answerable.** The shape is
  options-plus-recommendation — the asker's read of the choices and
  its recommended default, extending the clarification response's
  load-bearing `default_assumption` — so the cheapest possible
  architect answer ("your recommendation is correct") is always
  available.
- **Priority classes.** Only critical-path blockers interrupt the
  architect; non-blocking questions batch. Workers never idle on a
  parked question: a worker whose question is non-blocking proceeds
  on its named assumption, and a worker whose question blocks is
  suspended the way a clarification already suspends a session —
  the spawn schedule routes around it.
- **The answer-fatigue guard.** Answer-latency telemetry will
  measure what the queue costs the architect; question classes whose
  answers have become predictable are retired into autonomy — the
  trust ledger (§11) applied to questions. And the four heavyweight
  controls (§3) stay ceremonially distinct from the quick queue: a
  trust expansion never rides in as one more batched question.

---

## 9. Worker refresh

The inter-session failure surface: what the orchestrator does when a
worker session ends wrong. The protocol is strong exactly where a
worker is honest about its own failure — the probe, the
clarification, and the bailout give honest gaps a respectable wire
shape, HOLD triage (§7) covers well-formed wrongness, and the
compaction-recovery discipline has held three times in live traffic
(evidence 12, 59). It is weak where the failure corrupts the
failure-reporting channel itself: a worker damaged enough to produce
a malformed response is damaged enough that its account of the
damage is worthless. The named gaps, each future-tense doctrine for
the harness:

- **Malformed response → respawn from the original request, with a
  master-authored failure note.** The respawned worker gets the
  master's account of what came back broken — never the failed
  worker's self-report, which is the self-oracle constraint
  (evidence 16) applied one level up: the entity whose output was
  malformed does not author the context its successor plans by.
- **Bounded retries, escalating to re-decomposition.** Retry is not
  free and not unbounded. Clustered failures on the same work signal
  scoping, not discipline — `CLAUDE.md` §11.5's doctrine, held at
  the orchestrator level: after bounded retries the move is
  re-decompose the goal, not respawn harder.
- **Silence.** A worker that never responds is a failure mode with
  no artifact at all; timeouts and a `no_response` closure reason
  give it a durable record. The closure vocabulary lands CLI-side
  ahead of the harness, empty until a harness produces the events.
- **Base-tree poisoning.** A bad merge that later work built on is
  the expensive failure. Recovery is revert plus the applied-tags
  lineage — the mechanical path that already exists — and the real
  control is upstream: final-merge review (§3) is the human control
  automated away last, if ever.

---

## 10. Cost governance

Every spawn will be a spending decision, made by an agent, with the
architect's money. The doctrine:

- **Cost fields ride the mechanical telemetry stream from harness
  day one.** The schema lands CLI-side ahead of the harness and sits
  empty until a harness fills it — the same pattern as the closure
  vocabulary (§9), and the same dual-stream discipline as the rest
  of telemetry: spend is mechanical-stream data, never a worker
  self-estimate. The apply-only corpus lesson (evidence 38) applies
  in advance: cost records must cover every session exit, or the
  aggregate computes rates over a numerator-only dataset.
- **A hard spend cap is a harness-level gate: refuse loudly, never
  degrade silently.** A harness at its cap does not quietly shrink
  scope, drop verification, or downgrade models to keep going —
  silent degradation is the silent-skip bug at fleet scale.
- **A mid-arc cap breach has bailout semantics.** Stop spawning;
  in-flight workers hand off rather than being killed mid-build;
  validated work commits; the operator receives partial-but-sound
  work plus a resumption plan. The arc ends the way a session
  bails: early, cleanly, with the artifact that lets a fresh budget
  resume.
- **Effort policy is budget × trust ledger.** Verification
  redundancy, exploration breadth, retry budget, and model tier are
  allocated per work class: spent where the ledger shows a class
  miscalibrated, cheap where autonomy is earned. Effort is not
  uniform, and not a vibe — it reads the same longitudinal signal
  trust phasing (§11) reads.
- **The dashboard renders `bale stats`; it never owns it.** Any
  cost-visibility surface is a renderer over the CLI's aggregation,
  which stays exercisable by hand — the transport-agnostic
  commitment (ADR-0012) applied to money.

---

## 11. Trust phasing

Autonomy is granted per work class, in phases, on longitudinal
evidence — never as a vibe. The ladder: **manual** (every step
human-operated, the present tense) → **orchestrated decomposition**
(the master plans and packs; a human runs the mechanical steps) →
**mechanical inner loop** (the harness runs pack/apply/validate
unattended inside an arc; humans hold the §3 controls) →
**autonomous spawn** (the master spawns workers within budget and
trust bounds without per-spawn review). Recursion depth —
sub-masters spawning sub-masters — is earned last.

Transitions are gated by the longitudinal signal the diagnostics and
telemetry records were built to carry: bailout and HOLD clustering
per work class, claim/verdict calibration, clarification clustering
per packer. The grant itself is one of the four controls (§3) —
deliberate, per class, and revocable the same way. The evidence
weighting is the §5 rule again: mechanical-stream data over
self-report (evidence 16), across every exit path, not only the
applies (evidence 38). A first delegated arc has already run
end-to-end at the orchestrated-decomposition rung under a human
operator (evidence 50); each further rung is proven by hand on the
manual path before the harness inherits it (ADR-0012).

---

## 12. What this doc is not

Not a harness design: mechanism detail — schemas, queue transport,
sandbox mechanism, cap enforcement, dashboard — lives with the
harness spec-intake and its sessions, which cite this doc for the
doctrine they implement. Not a worker contract: `CLAUDE.md` and
`TARBALL.md` already are that contract, worker-agnostic by design
(ADR-0009), and a worker session behaves identically whether a human
or an orchestrator packed its request. Not a replacement for the
ADRs it elaborates: ADR-0009 holds the skeleton and the promotion
plan, ADR-0011 the clarification contract, ADR-0012 the ratified
direction; where this doc and an ADR disagree, that is a bug to fix
here, not a supersession.
