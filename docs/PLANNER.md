# PLANNER.md

> Planner authoring doctrine and orchestration doctrine.
> Read when `CLAUDE.md`'s INDEX says so — when authoring is the work.
> For the *why* behind the workflow itself, see `CLAUDE.md`.

---

## META

### What this doc is

The planner's practice manual: how to author the artifacts the
planner role produces — pack commands, request briefs, blind
checkpoints, rescope offers, and the master sittings that produce
them — so that what the worker receives transports what the planner
meant. `CLAUDE.md` §4 sets the authority split; `TARBALL.md` carries
the wire format those artifacts ride. This doc covers the *craft*:
the practices, earned from live traffic, that keep authored
artifacts honest.

The doc is one file with two halves. The **core** (sections 1–7,
and §20 — later-numbered, core-placed; the core banner carries the
note) is authoring doctrine — project-agnostic planner practice,
binding wherever a planner authors. Past the core banner sits
**orchestration doctrine** (sections 8–19): the working doctrine for
orchestration — the exchange shapes, present tense on the manual
path, and the scheduling and courier-automation layer the harness
era adds (§8 draws that line) — relocated here as the conditional
layer it always was. The banner between them is a deliberate,
pre-marked seam — see its own text.

### Who reads this, and when

This doc triggers when **authoring is the work**: a pack command, a
request brief, a checkpoint oracle, a rescope offer, or a sitting.
A worker session building a response has a mandatory read of zero —
this file sits unread exactly like `DOCS.md` in a session that
touches no docs. An authoring task arriving mid-session is an
ordinary `CLAUDE.md` §11.2 pre-flight event: estimate whether the
authoring fits the remaining budget, and read this doc before
producing if it does.

The worker→planner transition this doc serves is a role transition
(§20), and one line bounds it. The transition grants full
spawn-material authorship — commands, briefs, and, for a session's
own children, checkpoints; what it never grants is authorship of
an oracle the authoring session builds against. The
blind-checkpoint contract in `TARBALL.md` §7 is unchanged by
anything here: the entity that builds against a checkpoint never
authors it, and a worker asked to author a pack or a brief is
still never asked to author the oracle that grades its own
session.

### Conflict resolution

If something here conflicts with what Claude remembers from a prior
session, **this file wins.** On the wire format itself,
`TARBALL.md` wins; on values and the authority split, `CLAUDE.md`
wins; this file wins on authoring practice.

---

## INDEX

### Read paths

| Situation | Load |
|-----------|------|
| Authoring a pack command or assembling a request | Sections 1, 2; `TARBALL.md` §3.4 for the flag surface |
| Authoring a request brief (README) | Sections 1, 3 |
| Authoring a blind checkpoint | Sections 1, 4 |
| A HOLD landed; deciding what the retry session sees | Section 5 |
| Running a master sitting | Section 6 |
| A split fired (`CLAUDE.md` §11.2): authoring a subtree's spawn materials as sub-master | Sections 1, 20; §4 per child checkpoint |
| Hard rules / what counts as an authoring violation | Section 7 |
| Planning orchestration or harness work | Sections 8–19 (past the core banner) |

---

## 1. The Planner's Surface

The planner authors five artifact kinds, and each has one governing
practice section here:

- **Pack commands** (§2) — the runnable `bale pack` line. The flag
  surface and the solicited/unsolicited line live in `TARBALL.md`
  §3.4; this doc does not restate them.
- **Request briefs** (§3) — the prose context a request ships as its
  README, authored by the planner directly or by a worker on
  request.
- **Blind checkpoints** (§4) — the planner-authored oracle a
  configured project pins per session. The blindness contract is
  `TARBALL.md` §7's; this doc carries the authoring craft on top of
  it.
- **Post-HOLD retries** (§5) — the repack after judgment said
  *don't merge*: what the retry request carries, and what it never
  carries.
- **Sittings** (§6) — the master-session practice inside which the
  other four get authored.

A split fired mid-session authors all of the above at once, for a
subtree — the sub-master transition, §20.

The authority boundary under all five is `CLAUDE.md` §4's engraved
principle: intent authority is the planner's, mechanism authority is
the worker's, and the flagged-deviation-plus-ratification loop is
the joint. Authoring doctrine never overrides that split — it is the
practice of exercising the planner's half well.

---

## 2. Command and Request Authoring

- **Derive, don't rewrite.** A revised command, brief, or request is
  derived mechanically from its predecessor — edit the prior
  artifact — never re-authored fresh from memory. Live traffic's
  clearest lesson: a brief derived through five successive revisions
  preserved its load-bearing content; the one rewritten fresh
  dropped a section and caused the HOLD. The corollary
  generalizes to the receiving side: **verbatim-marked content gets
  a byte-exact assertion wherever it lands** — the worker that lands
  a must-be-verbatim line adds a byte-exact self-check on the landed
  line in its validation.
- **Commands are single-line and space-tolerant.** One line, no
  continuations, pasteable as-is (`TARBALL.md` §3.4 states the
  form); authored so that incidental whitespace differences don't
  change what the command does. A command that breaks when a paste
  normalizes spacing is authored fragile.
- **Assume first-match path resolution, and author around it.**
  Relative file arguments (a brief via its file flag, a checkpoint
  via its delivery flag) resolve against a search path, first match
  wins — and undated near-duplicates in a downloads directory get
  picked silently. Practice: give delivered files
  distinct, session-identifying names; and at pack time, glance at
  the pack report's echoed identity — resolved path, first heading,
  sha256 — before shipping. The echo exists to be compared.
- **A wrong fact is worse than a missing fact.** A missing fact in a
  request triggers a probe; a wrong one triggers an investigation
  the worker cannot decline, at context prices. Never state a claim
  about a file or the environment the authoring session hasn't
  verified this sitting; label pre-flight guesses about unread code
  as guesses.
- **Transported decisions ship verbatim.** A constraint or brief
  passage carrying a prior session's decision or proposal carries
  its text verbatim, never a paraphrase — a paraphrase once
  flattened a conditional into an unconditional and shipped a
  different decision than the one made.
- **The desk default is smaller sessions.** Default toward smaller,
  pre-split sessions: a split costs one extra paste; an oversized
  session costs a round-trip. Ratified at the desk, 2026-08-18; the
  split the default produces is a role transition, and §20 carries
  what the offering session then authors.
- **Concurrent splits forecast narrowly.** When split sessions are
  meant to run concurrently, each pack carries a narrow `--write`
  forecast — the declared forecasts are the decomposition's
  disjointness proof, and a default forecast intersects everything.
- **Hooks never carry load-bearing protocol behavior.** They are
  for environment-local conveniences. Verification, telemetry, and
  refusal surfaces integrate into the tool or they don't exist — an
  authored artifact that relies on a hook firing has delegated part
  of its contract to a surface no gate reads and no other
  environment runs.
- **Open question, noted rather than engraved:** how much of
  `TARBALL.md` §3.4's planner-facing detail should migrate here — a
  charter-widening question deliberately left open for a future
  sitting, not settled by this doc's birth.

---

## 3. Brief Authoring

A brief is a transport surface, and transport surfaces fail
silently. The practices:

- **Briefs open by naming the session and sitting they serve.** The
  first lines identify which request the brief belongs to, so a
  stale near-duplicate is recognizable on sight and the pack
  report's echoed heading is checkable against intent.
- **Inline registry state verbatim, or state its absence.** When a
  brief cites session-registry items — open sessions, forecasts,
  closures — it carries the registry text verbatim, or says plainly
  that none is included. A worker reasoning about concurrency from a
  brief's paraphrase of the registry is reasoning from a copy of a
  copy. When a brief cites registry items, ship the registry context
  the citations need.
- **Re-verify section cites at authoring time.** Section-numbered
  citations into project files are checked against the applied tree
  as the brief is authored — or, when the authoring desk's copy is
  known-stale (a sibling session's rewrite supersedes the desk's
  shipped bytes), the brief cites by **stable phrase** instead of by
  section number and says why. The worker's ratified default on a
  cite/phrase conflict: unambiguous-phrase-match wins over section
  number, flagged in `notes.md`, never silently.
- **Digest over dump.** A master-authored pack prefers a stats
  digest plus the notes relevant to its deltas over wholesale
  telemetry: the worker's budget is the scarce resource the brief
  spends, and an undigested record pile spends it on the planner's
  behalf.
- **Ship decision context into the request.** The packer never
  assumes the worker shares its conversation — the request is the
  whole interface. What resolved in chat and matters to the work
  goes in the brief; the rest of the chat stays behind.
- **Unfilled scaffold slots are loud.** A worker-authored brief
  marks anything left for the planner with the sentinel form
  `TARBALL.md` §3.4 names, and fills or removes every such line
  before the brief is delivered as ready to pack — a half-authored
  brief must refuse to ship, not ship quietly.

---

## 4. Checkpoint Authoring

The blindness contract — the checkpoint is authored from the
request, before implementation exists, never by the worker building
against it — is `TARBALL.md` §7's and is not restated here. On top
of it, the authoring craft:

- **Checkpoint authoring is part of pack authoring** — done in the
  same motion as the command and the brief, not deferred until a
  pack-time gate refuses and reminds. An oracle authored as an
  afterthought is authored from a colder read of the request than
  the request itself got.
- **Thin, outcome-only oracles.** Checkpoints assert **outcome
  contracts, never mechanisms**: what must be true of the applied
  tree, never how the worker got there. Thinness is the pinned
  authoring lever — a checkpoint that asserts mechanism binds the
  builder the blindness doctrine says it must not bind, and it HOLDs
  correct work for taking a different valid path. The standing
  watch: HOLDs clustering on checkpoint-fixture defects rather than
  worker misunderstanding means the authoring practice, not the
  worker, is the defect.
- **The imagined-surfaces failure class.** The recurring planner
  defect is a fixture built against a surface *imagined* rather than
  *read* — a wire-format detail assumed from memory.
  The practice that ended it: read the format the fixture touches,
  and **dry-run every checkpoint fixture path against the corpus
  with the graded surface stubbed** before first commit. Blind
  checkpoints exercising not-yet-built features cannot be dry-run
  end to end — which is why the fixture hygiene below is
  conservative by construction, not optional.
- **Rehearse against the brief's bytes, never a stub.** A checkpoint
  dress rehearsal derives its rehearsal landing from the brief's
  extracted block bytes, mechanically — never from a hand-written
  stub; a stub is the desk's paraphrase, and an oracle dry-run
  against a paraphrase is the oracle grading itself. Earned at a
  live rehearsal-stub correction.
- **Per-scenario fixture isolation.** One fresh fixture (repo,
  sandbox, dataset) per scenario, always. A shared fixture leaks one
  scenario's residue into the next — a leftover open session from
  scenario A tripping a gate in scenario B is the canonical instance —
  and with dry-runs structurally unavailable, the
  leak surfaces as a false HOLD in production.
- **The checkpoint tracks the scope.** Any scope change — a split, a
  narrowed forecast, a rescope — invalidates the authored oracle:
  assertions can fall outside the new scope and HOLD a good session.
  Standing rule: **re-derive the checkpoint whenever scope changes**, in
  the same motion as the rescope.
- **Locators are strict line anchors.** A checkpoint that locates
  content does it by exact, byte-stable anchors, never by fuzzy
  match — a fuzzy locator that drifts passes the wrong content or
  HOLDs the right one.
- **Split probes by the text's provenance.** Preserved text may be
  pinned as fixed strings — the worker must carry it byte-verbatim
  anyway — but authored text gets a verbatim-required marker in the
  brief or an invariant-shaped probe,
  never a connective-phrase grep.
  Earned from a live fixture-defect HOLD: a connective phrase
  pinned on authored-not-preserved text HOLDs correct work for
  phrasing the worker was free to choose.
- **Version-suffixed filenames; publish the hash; compare the
  echo.** Checkpoint files carry a version suffix in the filename so
  revisions never collide under first-match resolution (§2);
  delivery publishes the file's sha256; and the delivering planner
  compares the tool's echoed hash against the published one before
  proceeding. One file, one identity, verified at both ends. In a
  checkpoint-pinning project, spawn materials are delivered as one
  crafter-emitted bundle — brief, blind checkpoint, and pack argv
  with published hashes — beside its emitted `bale open` line, so
  the desk hand-composes neither; the bundle format itself lives in
  the bale tool's documentation, not here.
- A brief or oracle claim about any surface — tree, reach, or
  ruling — is verified against bytes or the sitting record at
  authoring time, and an oracle authored before a ruling is
  re-verified against every ruling made after it.

---

## 5. Post-HOLD Authoring

When a HOLD traces to content the worker never received — a brief
gap, an untransported decision — the retry request gets **the
missing specification prose, never the checkpoint's mechanics**:
reveal the spec, never the oracle. The retry must not
be taught to the test. A retry that passes because it saw the
oracle's assertions has learned the grader, not the goal, and the
blindness contract is spent for every session after it.

The inverse failure has its own protocol: **the bad-oracle
correction**, for the HOLD whose cause is the fixture, not the
work. When a blind checkpoint HOLDs and the worker's evidence
points at the fixture, the flow — exercised and ratified from live
traffic — is the contract:

1. The worker diagnoses from the reveal label alone, verifies the
   intended invariant mechanically on its own side, and requests
   the spec — reveal the spec, never the script: target, scope,
   expected value, and nothing of the oracle's mechanics.
2. The desk re-verifies mechanically against real bytes before
   ruling — never from memory.
3. The ruling forks. A fixture defect means an amendment at the
   desk and a HOLD→correction, no retry tarball from the worker; a
   real violation means the worker fixes and ships a retry
   tarball; and a fix that would override the request's own brief
   needs an explicit desk ruling either way.
4. Amendment discipline is minimal: only the failing probe changes
   — passing probes are empirically validated anchors and stay
   byte-identical — and the amendment is version-suffixed, dry-run
   against real bytes before delivery, its sha256 published, and
   the echoed hash compared by the operator (§4's delivery
   practice).
5. The operator commits the amended bytes at the session's
   checkpoint path — `bale amend-checkpoint` is the verb that
   performs it, verifying the delivered file against the published
   sha256 before committing — and retries the same response
   tarball; the provenance gate refuses on the stamp mismatch, the
   operator
   accepts deliberately with the per-invocation flag, and the
   recorded stamp mismatch plus a prose mention at the next doc
   landing is the truthful double record.
6. Every fixture defect is a ledger specimen, feeding the standing
   fixture-defect watch and the checkpoint-authoring practice (§4).

The rest of the retry follows the wire format: the failure context
ships into the new request, and the response's `corrects` pointer
preserves the lineage. HOLD *triage* — correctable versus escalate —
is orchestration doctrine, §14.

---

## 6. Sitting Practice

- **One master per sitting.** A sitting has exactly one authoring
  desk: one master session authors the sitting's commands, briefs,
  and checkpoints. Split authorship inside a sitting produced
  compounding misses — an artifact hand-written by the wrong role
  because a refusal's wording pointed at the wrong actor. The corollary
  binds tooling: refusals name their real actor.
- **End at milestones.** Masters end sittings at natural milestones
  rather than resolving open questions on a tired context — the
  sitting-level form of `CLAUDE.md` §11's bail-early discipline.
- **Authoring practice accretes into doctrine, or it evaporates.**
  Planner practice keeps living in ephemeral chats until a gate
  refuses. When a sitting resolves an authoring
  question, the answer lands somewhere durable — this doc, a
  decision record, a brief convention — in the same sitting.
- **Calibration sittings are trigger-fired, never calendar-fired.**
  The calibration sitting is a named sitting kind assembled from
  the existing machinery — sitting-close deltas, ratification
  microdeltas, evidence-ledger curation, the trust grant as a
  stats-reading judgment point — with no new ceremony; a calendar
  cadence is rejected as the over-formalization `CLAUDE.md` §7
  warns against. The triggers: clarification clustering against
  one packer crossing threshold; DISAGREE clusters on one check
  class; HOLD clustering per work class; a pending trust grant; N
  sessions since the evidence ledger was last read. The default
  threshold, deliberately crude and ratified as a starting point:
  three same-class events inside a rolling window — and the first
  calibration sitting recalibrates its own trigger. The input side
  is the stats digest at sitting-open (queued tool-side machinery).
  The output constraint is the teaching half: workers are
  stateless, so the only teaching channel is the injected docs and
  the request — a calibration sitting's outputs are constrained by
  construction to durable artifacts: a doc delta, a mechanical
  gate, a queued work item, an evidence entry, or a trust grant. The
  loop closes measurably: every session record
  pins the injected docs' hashes (`contract_docs`), so the next
  calibration sitting can check whether the previous one's doc
  delta moved the rates — the epoch read the records were built to
  carry. A calibration sitting also sweeps fired, stale, and
  superseded watch lists and queued fold-in riders — trigger-fired
  pruning, no new ceremony.

---

## 20. The Sub-Master Transition

A split is a role transition: the session that proposes it becomes
a master for its own subtree — a tighter-scoped master with a
parent to answer to, holding the same doctrine at narrower scope.
Roles are hats, not identities: the session that was a worker the
moment before the split gate fired is, from the split onward, the
planner of the sessions the split creates.

In practice: a session that hits the split gate (`CLAUDE.md` §11.2)
in a checkpoint-configured project does not emit an offer and hand
authoring back to the operator. It authors its children's spawn
materials in full — commands, briefs, and checkpoints — under
META's grant, because it never builds against its children's
oracles; its children do. `TARBALL.md` §7's blindness contract is
met in its own terms: each child's checkpoint is authored blind,
from that child's request, before the child's implementation
exists, by a session that will not build against it — and
re-derived for the narrowed scope, per §4's standing rule. The
operator carries the authored artifacts between sessions; the
operator does not author them.

### 20.1 The upward contract

The parent authors the arc oracle — blind, from the arc request,
before the decomposition exists — grading the summed outcome of
the subtree; the sub-master ships its own validation of the sum.
Neither replaces the other, at any altitude.
This is the session-level dual stream (§12) repeated one level up,
unchanged: the blind stream is the misunderstanding control, the
self-validation is the calibration stream, and the trust ledger
consumes both.

A sub-master's children's checkpoints collectively grade its own
decomposition — the self-oracle shape at one remove; the parent's
ratification of the decomposition, before anything spawns, is the
control.
The ratification is one of the four controls (§10), already there —
the transition adds no new ceremony.

Two boundary facts, one sentence each. The read-only-waiver
collision: a sub-master's own session packs read-only while its
subtree lands plenty, so the arc oracle cannot live in the
per-response checkpoint slot — the mechanical home for arc-level
grading is queued tool-side. And
one-master-per-sitting (§6) is preserved by recursion: each
subtree's sitting has exactly one desk.

### 20.2 The upward report

A sub-master closes its arc with a structured upward report — the
shape §15 records as prototyped, restated here as
the required sections:

- **The partition** — every item of the arc's work sorted landed /
  ratified / escalated / on-watch.
- **An arc claims block** — the summed validation of the subtree
  stated as claims, so reconciliation has something to pair with
  the arc oracle's verdict.
- **Consumed vs deferred scope** — what of the arc's forecast was
  spent, and what remains.
- **Proposals** — follow-on work the subtree's vantage revealed, as
  prose with rationale (`TARBALL.md` §5.4.1's shape).

---

## 7. Hard Rules

All rows are **policy** (labels per `CLAUDE.md` §6): no mechanical
gate reads an artifact's craft. The enforcement surface is the
longitudinal record — HOLD and clarification clustering per packer
grade the planner the way claim/verdict calibration grades the
worker — plus review.

| Rule | Type | Enforcement |
|------|------|-------------|
| Revisions derive from the predecessor artifact, never rewritten fresh | policy | review; HOLD clustering on dropped content |
| No session authors an oracle it builds against — spawn-material authorship (§20) reaches children's checkpoints, never the authoring session's own | policy | review; `TARBALL.md` §7's mechanical half backs it |
| Checkpoints assert outcomes, never mechanisms | policy | review; the fixture-defect HOLD watch (§4) |
| Re-derive the checkpoint whenever scope changes | policy | review; a stale oracle surfaces as a false HOLD |
| Post-HOLD retries receive spec, never oracle mechanics | policy | review — nothing downstream can un-teach a taught test |
| Transported decisions and registry state ship verbatim | policy | review; clarification clustering per packer |
| One master per sitting authors commands, briefs, and checkpoints | policy | the sitting's own discipline; review |

---

> **PAST THE CORE.** Sections above this banner — 1 through 7, and
> 20 — are the authoring core: read when authoring is the work.
> (§20 is numbered past the orchestration half but placed in the
> core: numbers are stable per `DOCS.md` §6.4, and placement
> follows readers.) Everything
> below — sections 8 through 19 — is orchestration doctrine: read
> when planning orchestration or harness work. The banner is a
> deliberate, pre-marked seam: if a physical re-split of this doc is
> ever wanted, it is a transport-relative decision that defers to
> the injection-model question like every other split of the global
> set, and it happens here.

---

## 8. Orchestration Doctrine — Standing

The sections below this one are the working orchestration doctrine:
how an orchestrating planner decomposes goals, authors checkpoints
at fleet scale, enforces disjointness, judges HOLDs, escalates, and
how trust in it is phased up. They relocated here from the project
explainer that was their working home, carrying their ratified
standing with them; the ratification records stay project-side.

**No orchestration harness exists yet, and no exchange shape waits
on one.** Every shape a worker and a planner exchange — the
request, the probe, the response, and the clarification thread
(`TARBALL.md` §2) — is present tense on the manual path, exercised
by hand, recorded by bale, and identical whoever holds the roles.
The manual path is where contract behavior is defined and verified,
and it remains fallback and ground truth: a harness inherits every
shape as it stands and changes none of them. What is genuinely
harness-era is narrower than it once read: *scheduling* (who spawns
what, when, within what budget) and *courier automation* (a program
carrying the pastes the operator carries by hand today). Only
passages about those two things are written for the harness, and
only they are **provisional-until-S6** — S6 being the harness
spec-intake, which inherits "ratify and churn the orchestration half
of this doc." Sections below that are wholly about scheduling or
courier automation carry the marker inline; a section that
describes an exchange shape does not, because the shape is already
the present tense.

Language is role-only throughout: *planner* (intent authority),
*worker* (mechanism authority), *operator* (runs pack/apply), and
*courier* (carries pastes between sessions) name roles
(`TARBALL.md` §1), any role can be held by a human or a session,
and no doctrine keys on which. *Master* (or *orchestrator*) names a
planning session — a planner that is itself a session; *architect*
names the human, used where a sentence needs the person rather than
the role. The doctrine below was earned from live traffic; the
evidence ledger recording that traffic is a project-side record,
deliberately not referenced here, because this doc travels to every
project and the ledger does not. Every lesson stands self-contained
as written; provenance stays project-side.

---

## 9. The Foundational Principle: Minimize Specification Friction

Ratified by the architect at the spec-intake sitting, and stated
here as a load-bearing principle ranking with the four controls
(§10), not below them. The ratified kernel:

Ambiguity is the enemy, not capability.

The dominant observed failure class in this workflow is
misunderstanding — the ratified floor (§10) already says so, and the
evidence pile keeps confirming it: mechanical validation passes
cleanly on work that answers the wrong question,
and a wrong fact in a brief costs more than a missing one. As model
capability grows, the binding constraint on "seed
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
accreted; an answer paraphrased on its way into a
request is not the answer. The escalation contract
(§15) is this principle made concrete; the four controls (§10) are
the attention budget it spends.

---

## 10. The Four Controls

The ratified floor, restated here so this half stands alone for its
citers: human checkpoints converge on four "what"-shaped controls —

1. **Ratify decompositions** — before workers spawn.
2. **Answer escalations** — the questions only the spec's author can
   answer.
3. **Review final merges** — before the integrated result is
   accepted.
4. **Grant trust expansions** — the deliberate step that moves a
   work class up the §18 phasing ladder.

Everything below these four goes autonomous per work class as the
trust ledger earns it. The controls exist because misunderstanding
is the dominant failure class and mechanical validation structurally
cannot catch it; they are the misunderstanding control surface, and
the specification-friction principle (§9) governs how cheaply each
one spends the architect's attention. They are deliberately
heavyweight and ceremonially distinct from the quick clarification
queue (§15): a control is a judgment point the architect prepares
for, not a notification stream.

---

## 11. Decomposition at Seams

The orchestrator will split a large goal along real boundaries into
worker sessions that each fit a context window — `CLAUDE.md` §11.2's
seam discipline, promoted from self-rescoping to planning. A worker
refusing an oversized goal and returning seams is the happy path;
the orchestrator, not the worker, weighs split economics plan-wide. The
decomposition is also the disjointness proof that
the mechanical gates (§13) then make load-bearing: forecasts are
declared per session at pack time, and a decomposition whose
forecasts collide is wrong before anything spawns. The proof's flip
side is the hot file: file-granularity forecasts serialize hot
files — every session that forecasts one waits on every other — so
a decomposition routes around them or serializes through them
deliberately, never by accident.

What live traffic has earned about the craft of packing, all of it
binding on an orchestrator because every instance was committed by a
planner role (the sentence-scale practices live in the core, §2–§3;
the fleet-scale rules below are this half's):

- **Decision context ships into the request; the packer never
  assumes the worker shares its conversation**. The
  request is the whole interface.
- **Include sets are a completeness obligation.** The
  missing-context class — load-time imports, runtime-loaded files,
  brief-referenced unshipped text — has recurred with the architect,
  the master, a worker, and a sub-master as packer. The
  execution-context manifest is the countermeasure; the
  class is why packing is graded.
- **A wrong fact in a brief is worse than a missing fact**. Missing
  facts trigger probes; wrong facts trigger
  investigations the worker cannot decline, at context prices.
  Corollaries: read files whole before making claims about them;
  pin doc touches only against structure actually read.
- **Transported decisions ship verbatim, never paraphrased**. A
  constraint that flattens a prior proposal's
  conditional transports a different decision.
- **Scope statements ride the artifact, not the chat.** The
  manifest's scope stamp closed the class of workers inferring scope
  from the shipped file list; chat-delivered
  commands and briefs are convention-only artifacts, and the durable
  row is the spec.
- **Ordering constraints are claims.** Serialization the
  orchestrator imposes between sessions is stated with rationale so
  it can be contested; a delegated-to gate is named
  with its firing condition, not presumed to fire.
- **The orchestrator's own session packs scopeless** — empty
  recorded scope, forecasting nothing, so its read set locks no
  worker out. Masters end sittings at milestones
  rather than resolving open questions on a tired context.

---

## 12. Blind Checkpoints

The orchestrator will author each worker's validation checkpoint
from the request, before any implementation exists. The worker never
authors the oracle it is graded by — the workflow-level rejection of
self-oracles, and the standing test generalizes: for any new
mechanism, ask whether the entity under evaluation authors the input
its evaluation rests on, and where it does, split mechanical from
self-reported and weight the mechanical.

The mechanics already ship on the manual path: a planner-authored
checkpoint pinned at pack time runs in staging beside the worker's
`validation.sh` — checkpoint first, both always run — and the worker
neither reads, ships, nor declares it (`TARBALL.md` §7). Checkpoint
blindness is keyed to the write forecast (ADR-0015), with a
read-side ships-the-oracle refusal backing it. The two streams
coexist by design: the blind checkpoint is the misunderstanding
control; the worker's `validation.sh` is the calibration stream;
neither replaces the other, and the trust ledger (§18) consumes
both. The authoring craft that keeps checkpoints thin, isolated, and
scope-tracked is the core's §4.

*Provisional-until-S6:* the harness-era prerequisite, already
ratified as doctrine — checkpoint and validation scripts will run
sandboxed for unattended execution: network off, writes confined to
staging (ADR-0016). Attended applies under a human reader are the
present-tense exception that made the bare-subprocess era tolerable;
autonomy does not inherit it.

---

## 13. Disjointness Enforcement

Mechanical, and already shipping: pack refuses a new session whose
write forecast intersects an open session's forecast, and apply
rejects a response whose changes cross a sibling's forecast — the
one refusal that takes no override (ADR-0015; `TARBALL.md` §3.2
carries the worker-facing contract). The read/write separation
matters to orchestration specifically: read context no longer locks, so
concurrency is bounded by
genuine write collisions, not by shared reading.

Two earned rules ride on the gates. **Predicted refusals are control
flow; surprise refusals are incidents**: a
decomposition whose plan names each gate firing in advance walks
through refusals as sequencing, while the same refusal unstated
invites an unlock that throws a session away. An orchestrator will
plan with the gates, not around them. And **queues go stale under
concurrency**: a worker verifies the shipped tree
against its goal before building, because an intervening sibling may
have closed the queued item — the drill-down doctrine catching at
zero cost what scheduling cannot.

---

## 14. HOLD Judgment

A HOLD is well-formed wrongness: the tarball is mechanically sound,
staged, and inspectable, and a judgment still says *don't merge
this*. The orchestrator will triage a HOLD into one of two paths:
**correctable** — revert, repack with the failure context shipped
into the new request, `corrects:` pointer preserving the lineage
(and the retry authored per the core's §5: spec, never oracle) —
versus **escalate** to the architect, when the wrongness traces to
the spec rather than the work. The correctable path itself forks on
the worker's evidence: evidence pointing at the fixture rather than
the work routes into the core §5's bad-oracle correction — an
amendment at the desk, no retry tarball from the worker.

The triage judgment is itself graded input: packer errors are a
grading signal on the planner, not (only) on the worker, and a
correction round that repairs a ratified-but-
underspecified decision is flagged for ratification, never shipped
silently. The misunderstanding-control doctrine has
functioned live on this surface: a worker receiving a stale
redundant goal verified the tree, refused to fabricate a change set,
and asked — the behavior HOLD triage exists to reward.

---

## 15. Escalation and the Clarification Queue

The escalation contract is the specification-friction principle
(§9) made concrete, and it is built on an existing channel rather
than a new one. A blocking intent gap is a **thread**: the worker
opens it with a clarification response (`TARBALL.md` §5.9,
ADR-0011); the courier carries it; `bale relay` records the round
and emits the planner-facing paste block; the planner answers as an
exchange record; `bale relay` records the answer and emits the
worker-facing block; the courier carries it back, and the worker
continues under the same session. Every party in that sentence is a
role (§8): the planner is whoever holds intent authority for the
request — the architect at the desk, or a master session answering
from its own context and escalating upward what it cannot — and the
courier is whoever carries the paste, the operator by hand or a
harness in its stead. The shape is the same in every case; only the
holders change. A planner that is itself a session escalates the
questions it cannot answer to its own planner by the same shape one
level up — the master→architect distillation is the escalation
record, which coexists with the exchange record and shares its
`amendment_target` field and meaning. The first delegated arc's
structured upward report — partitioned landed / ratified / escalated
/ on-watch — is the working prototype of that upward contract's
shape.

This section is the doctrine home for what the exchange and
escalation records inherit; the records' schemas and the relay verb
are the bale tool's, and this section names the doctrine they
implement rather than restating their fields.

- **Dedup before the architect sees anything.** Concurrent workers
  ask overlapping questions; a master planner dedupes them before
  escalating, and the escalation record carries the dedup lineage —
  which worker questions a surfaced question answers — so one
  answer fans back out to every asker, each as its own thread's
  next round.
- **Answers accrete into the spec, mechanically.** An answer lands
  in the seed document or in a decisions ledger beside it, and ships
  verbatim into future requests. This is mechanized: an answer names
  its `amendment_target` — the repo-relative path it accretes into —
  on the record itself, so the answer-to-amendment path is schema,
  not convention. This is §9's accretion test enforced at the record
  level, with the verbatim-transport rule built in
  rather than relied on.
- **Questions arrive answerable.** This is mechanized: a question
  row carries `options` and a `recommendation` — the asker's read of
  the choices and its recommended default, extending the
  load-bearing `default_assumption` — so the cheapest possible
  answer is always available, and the answer records it as a
  disposition of `as-recommended` rather than restating it.
- **Priority classes.** Only critical-path blockers interrupt the
  planner; non-blocking questions batch. This is mechanized on the
  question row's `priority` (`blocking` | `batched`). A worker never
  idles on a parked question: a worker whose question is `batched`
  proceeds on its named assumption, and a worker whose question
  `blocking` is suspended the way a clarification already suspends a
  session — the schedule routes around it. Non-blocking mid-work
  inquiry is not a thread; the `batched` doctrine stands as written.
- **The answer-fatigue guard.** Answer-latency telemetry measures
  what the queue costs the planner who answers; question classes
  whose answers have become predictable are retired into autonomy —
  the trust ledger (§18) applied to questions. And the four
  heavyweight controls (§10) stay ceremonially distinct from the
  quick queue: a trust expansion never rides in as one more batched
  question.

---

## 16. Worker Refresh

*Provisional-until-S6 — harness-era doctrine.*

The inter-session failure surface: what the orchestrator does when a
worker session ends wrong. The protocol is strong exactly where a
worker is honest about its own failure — the probe, the
clarification, and the bailout give honest gaps a respectable wire
shape, HOLD triage (§14) covers well-formed wrongness, and the
compaction-recovery discipline has held repeatedly in live traffic. It
is weak where the failure corrupts the
failure-reporting channel itself: a worker damaged enough to produce
a malformed response is damaged enough that its account of the
damage is worthless. The named gaps, each future-tense doctrine for
the harness:

- **Malformed response → respawn from the original request, with a
  master-authored failure note.** The respawned worker gets the
  master's account of what came back broken — never the failed
  worker's self-report, which is the self-oracle constraint applied one
  level up: the entity whose output was
  malformed does not author the context its successor plans by.
- **Bounded retries, escalating to re-decomposition.** Retry is not
  free and not unbounded. Clustered failures on the same work signal
  scoping, not discipline — `CLAUDE.md` §11.5's doctrine, held at
  the orchestrator level: after bounded retries the move is
  re-decompose the goal, not respawn harder.
- **Silence.** A worker that never responds is a failure mode with
  no artifact at all; timeouts and a `no_response` closure reason
  give it a durable record. The closure vocabulary lands tool-side
  ahead of the harness, empty until a harness produces the events.
- **Base-tree poisoning.** A bad merge that later work built on is
  the expensive failure. Recovery is revert plus the applied-tags
  lineage — the mechanical path that already exists — and the real
  control is upstream: final-merge review (§10) is the human control
  automated away last, if ever.

---

## 17. Cost Governance

*Provisional-until-S6 — harness-era doctrine.*

Every spawn will be a spending decision, made by an agent, with the
architect's money. The doctrine:

- **Cost fields ride the mechanical telemetry stream from harness
  day one.** The schema lands tool-side ahead of the harness and
  sits empty until a harness fills it — the same pattern as the
  closure vocabulary (§16), and the same dual-stream discipline as
  the rest of telemetry: spend is mechanical-stream data, never a
  worker self-estimate. The apply-only corpus lesson
  applies in advance: cost records must cover every session exit, or
  the aggregate computes rates over a numerator-only dataset.
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
  trust phasing (§18) reads.
- **The dashboard renders the stats; it never owns them.** Any
  cost-visibility surface is a renderer over the tool's own
  aggregation, which stays exercisable by hand — the
  transport-agnostic commitment applied to money.

---

## 18. Trust Phasing

Autonomy is granted per work class, in phases, on longitudinal
evidence — never as a vibe. The rungs describe **who decides and
who carries**, never which shapes exist: every exchange shape is
mechanized and identical on every rung (§8), and what a rung grants
is a change of role-holder. The ladder: **manual** (the architect
holds the planner role and the operator carries; the present tense)
→ **orchestrated decomposition** (a master session holds the
planner role — plans, packs, answers threads — and the operator
carries) → **mechanical inner loop** (a harness carries: it runs
pack/apply/relay/validate unattended inside an arc, and humans hold
the §10 controls) → **autonomous spawn** (the master spawns workers
within budget and trust bounds without per-spawn review). Recursion
depth — sub-masters spawning sub-masters — is earned last.

Transitions are gated by the longitudinal signal the diagnostics and
telemetry records were built to carry: bailout and HOLD clustering
per work class, claim/verdict calibration, clarification clustering
per packer. The grant itself is one of the four controls (§10) —
deliberate, per class, and revocable the same way. The evidence
weighting is the §12 rule again: mechanical-stream data over
self-report, across every exit path, not only the
applies. A first delegated arc has already run
end-to-end at the orchestrated-decomposition rung under a human
operator; each further rung is proven by hand on the
manual path before the harness inherits it.

---

## 19. What This Half Is Not

Not a harness design: mechanism detail — schemas, queue transport,
sandbox mechanism, cap enforcement, dashboard — lives with the
harness spec-intake and its sessions, which cite this doc for the
doctrine they implement. Not a worker contract: `CLAUDE.md` and
`TARBALL.md` already are that contract, worker-agnostic by design,
and a worker session behaves identically whether a human or an
orchestrator packed its request. Not a replacement for the project's
own decision records: where this half and a ratified project
decision disagree, that is a bug to fix here, not a supersession —
the ratification records stay project-side, and this doc carries the
doctrine, not the history.
