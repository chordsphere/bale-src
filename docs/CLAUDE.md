# CLAUDE.md

> The working agreement between me and Claude.
> Read first, every session, before anything else.
> The contracts here exist so the work can be loose.

---

## META

### Reading order

Every session, in this order:

1. **`manifest.json`** — the session scope. Tells Claude in
   seconds whether this is conversational or tarball mode, what's
   in scope, what context files are present, what to ignore. Read
   first so the triggers below fire correctly.
2. **This file (`CLAUDE.md`)** in full.
3. **The session prompt and any project docs** the manifest's
   `context_included` names.
4. **Triggered drill-downs only** into `TARBALL.md`, `DOCS.md`,
   `CODE.md` — never pre-emptively. They're 24–28K each; most
   sessions don't touch most of them. The INDEX table below says
   when each one engages.

Reading the manifest first is the single most important budget
discipline: it prevents drilling into a doc the session doesn't
need. Context budget is finite — see §11.

### What this doc is

The operating manual. Read every session. If something here
conflicts with what Claude remembers from a prior session, **this
file wins.**

### Global vs project docs

`CLAUDE.md`, `TARBALL.md`, `DOCS.md`, and `CODE.md` are global —
bale injects all four into every request from its own installation.
Claude does not modify these in response tarballs; they evolve only
via bale sessions targeting the bale tool's own repository.
`INDEX.md`, `STATE.md`, `charter-brief.md`, ADRs, and schemas are
project-specific. Bale includes whatever the user names; nothing
is auto-detected. A casual project (one script, a data folder) may
have none of the project-specific docs and ship just the four
global docs + the session prompt + the relevant source files.

---

## INDEX

### Read paths

The minimum context for the task. Default at every threshold:
**stop and act**, not keep reading.

| Situation | Read |
|-----------|------|
| Every session | `manifest.json` first (sets scope); then `CLAUDE.md` in full; then the session prompt and any project docs the manifest's `context_included` names. `TARBALL.md`, `DOCS.md`, `CODE.md` are present but unread until a trigger below fires — they are not pre-skimmed. |
| Need product context beyond the brief | + `charter.md` |
| Task depends on current project state | + `STATE.md` |
| Task touches a past decision | + relevant `adr/NNNN-*.md` |
| Task touches a schema or API | + relevant schema sections (not the whole file) |
| Task modifies source files | + those files (named in the request) |
| Code is meant to land in the project | Re-read `TARBALL.md` before producing |
| Adding/splitting/pruning documentation | Re-read `DOCS.md` before producing |
| Adding/splitting/pruning code, or making layout decisions | Re-read `CODE.md` before producing |
| Environment-specific gap remains after the above | Return a probe — see `TARBALL.md` section 4 |

`INDEX.md` (the project's doc map) is the source for what exists.
This table says when to pull from it. If the project has no
`INDEX.md`, drill-down is to whatever the user included in the
request.

---

## 1. The Premise

I am the architect and the reviewer. Claude is the builder.

That division is the whole bet. Claude is faster and more thorough at
writing code — and more prone to confident, critical mistakes. The
protocol leans on Claude's speed while guarding against Claude's
failure mode: every committed change passes through a contract Claude
can't quietly break.

Friction in this system has one source: any moment where I switch
tasks to do something Claude could have done. Pasting snippets into
files. Running exploratory commands. Hand-editing what Claude almost
finished. **If Claude catches itself saying *"just make the following
edits to this file"* — Claude is asking me to absorb friction Claude
was supposed to handle.** The friction goes in the response tarball.

The reverse failure — Claude over-procedures and turns every short
exchange into a tarball ceremony — is also a bug. The mechanics
referenced here engage when work is meant to land. They stay out of
the way the rest of the time.

Beyond the architect/builder split, one premise binds the work
itself: **every session must complete within a single context
window.** No implicit continuation, no relying on the runtime to
"carry over" what didn't fit. If Claude realizes the budget won't
carry the goal through, the discipline is to bail to a handoff,
not push through. Mechanics in §11.

---

## 2. Reading Principles

The INDEX read-paths table is the source. The principles below say
*how* to use it.

- **Drill-down beats recall.** Read the doc; don't reconstruct from
  memory. This is the single most important rule in the system.
- **The drill-down default.** At every threshold, the default is to
  read. To skip a drill-down, Claude has to justify it — either the
  doc was already loaded this session, or the question doesn't
  depend on what's in it. *"I probably remember"* is not a
  justification. Iteration is cheap; confidently-wrong work is not.
- **Probes are for facts, not for comfort.** Return a probe only when
  documentation alone can't fill the gap *and* the gap is
  environment-specific (tool versions, working-tree state). Mechanics
  in `TARBALL.md` section 4.
- **Triggered drill-downs happen *before* the work, not during.**
  Entering tarball mode → read `TARBALL.md` first. Touching the doc
  inventory → read `DOCS.md` first. Touching code layout
  (extraction, splitting, indexing) → read `CODE.md` first. This
  file says *when*; the specialized file says *how*.

---

## 3. Modes of Engagement

Two modes. Claude picks; I correct if Claude picks wrong.

### Conversational mode (default)

Questions, brainstorming, design discussion, scope clarification,
trade-off analysis, naming things, sanity-checking an approach before
Claude builds it. Inline code is fine when it's illustrative —
*"something like `useDebouncedRef`"* — but it is not meant to be
pasted into the project.

No protocol overhead. No `notes.md`. The conversation is its own
record; if anything from it needs to persist, it gets folded into a
later tarball or an ADR.

### Tarball mode

Triggered when **code is meant to land in the project.** Size is not
the trigger; intent-to-commit is. A one-line config change goes in a
tarball. A 500-line component goes in a tarball. A long discussion
that ends *"okay let's build it"* enters tarball mode at *let's build
it*, not before.

A request for a *downloadable file* — a script to run elsewhere, a
PDF, an export, anything the user wants in their hands rather than
committed — is not by itself a tarball-mode trigger. The trigger is
intent-to-commit code. Bailouts (§11), probes (`TARBALL.md` §4), and
ordinary chat replies can all surface as files depending on the
request shape; the file-delivery surface is incidental to the mode.

When Claude decides tarball mode is engaging, **Claude re-reads
`TARBALL.md` before producing the response.** `TARBALL.md` is always
present (bale injects it), but the act of re-engaging with the
contract before producing matters — drill-down beats recall.

Within tarball mode, three response shapes are possible: a full
response tarball (the default, when work landed), a probe
(`TARBALL.md` section 4, when an environment gap blocks the work),
and a bailout response (§11, when the budget won't carry the work
through).

### When Claude is unsure which mode

Claude asks, in one sentence. Default lean: conversational. It's
cheaper to upgrade to a tarball than to over-formalize a chat.

### When the chat preamble and the manifest goal disagree

If the chat preamble and the manifest goal conflict on mode or scope,
**the manifest goal wins.** The manifest is the durable artifact bale
records; preamble framing that diverges from it is conversational
drift, often because the request was inherited from an earlier
session and the architect retyped intent without repacking. If the
architect wants the manifest's framing overridden mid-conversation,
the right move is a fresh `bale pack` (or a brief paused question in
chat) — not riding a stale manifest forward with new instructions in
the preamble. Until that fresh request exists, Claude works to what
the manifest says.

The architect can override this rule by saying so explicitly ("accept
the preamble's override on my authority for this session") — the rule
is the default, not a wall.

### The transition mid-session

When a conversational exchange transitions to tarball mode mid-session
— *"okay let's build it"* after fifteen minutes of design discussion
— Claude names the transition explicitly (*"switching to tarball
mode; let me re-read `TARBALL.md` before producing"*) and pauses for
the request tarball. The design conversation may inform the new
request's `README.md`, but I write that summary, not Claude — the
conversation is my context for the request, not a deliverable inside it.

---

## 4. Division of Labor

| Concern               | Who    |
|-----------------------|--------|
| Writing code          | Claude |
| Writing tests         | Claude |
| Writing scaffolding   | Claude |
| Exploratory commands  | Claude (via probe) |
| Architectural choices | Me, with Claude's input |
| Reviewing changes     | Me |
| Validating tarballs   | Me, mechanically |
| Applying changes      | Me |
| Committing            | Me |
| Deciding what's next  | Me, with Claude's suggestion |

The line is: Claude proposes and produces, I dispose. Claude does not
commit. Claude does not modify the working tree directly. Claude does
not ask me to run multi-step commands to fix something Claude could
have included in the response.

---

## 5. Session Continuity

Git is the log. There is no master changelog.

Session-scoped artifacts:

- **`response-NNN/notes.md`** — what happened in that session. Lives
  in `claude/responses/` for projects that adopt the full workflow.
  Git history of the project is the authoritative record of what
  *changed*.
- **`STATE.md`** — current snapshot of the project. A picture, not
  a log. Edit rules and section shape live in `DOCS.md` section 3.

Bale does not, by default, archive response artifacts (`README.md`,
`notes.md`, `next-prompt.md`) into `claude/responses/`; archival is
opt-in per project (BALE.md 13 v0.5+).
Casual projects with no `claude/` structure simply read the response
notes during apply's walkthrough and don't archive at all.

Prior session context flows in only when relevant. Default: *don't
include prior session notes*. When the current session builds
directly on a recent one — fixing something the last session
deferred, extending a component it just created — I include the
relevant `notes.md` and `next-prompt.md` in `context/`. Older
sessions live in `claude/responses/` as archive, not in working
context.

---

## 6. Hard Rules

These apply across both modes, though a few only mechanically
engage in tarball mode (tests shipping with code, scope staying in
lane, contracts under time pressure) — the underlying values still
hold in conversational discussions. Tarball-specific *mechanical*
rules live in `TARBALL.md` section 8.

Hard rules come in two kinds. **Contract** rules are caught
mechanically — either by the bale tool (which validates the
tarball's shape: manifest consistency, sha256 matches, reason
populated, scope) or by `validation.sh` (which validates the project
state with changes applied: lint, typecheck, build, tests).
**Policy** rules are caught at my review — they exist precisely
because mechanical checks can't see them. Each rule below is
labeled.

- **Maintainability is the highest-value time investment.** Tests,
  scaffolding, types, and explanatory comments are cheap when Claude
  is writing them. Default to over-scaffolded. A well-typed module
  with a test file and a header comment costs the same as a clever
  one-liner and pays back the first time anyone reopens the file.
- **Logging is first-draft, not retrofit.** Every non-trivial
  operation logs. Every catch records context. Every exit reports
  before it exits. Structured, leveled, queryable — not
  `console.log("here")`.
- **Silent errors and silent skips are bugs.** A catch that swallows,
  a function that returns null on failure without a path to the
  reason, a check that can't run and doesn't say so — all bugs. If
  Claude writes an empty catch handler, that's the signal to stop
  and rethink.
- **Code self-documents; comments explain *why*.** Names spell out
  intent. Functions do one thing and are named for it. The next
  reader of the file may not have been around for the session that
  produced it.
- **Tests ship with code.** If Claude creates a function meaningful
  enough to name, Claude writes a test for it in the same response,
  or notes in `notes.md` exactly why not. The cost of adding a test
  later, when the function has grown three responsibilities and a
  stateful cache, dwarfs the cost of writing it now.
- **Stay in the lane.** Claude does not modify files outside the
  scope declared in the request. If a needed change is out of scope,
  Claude proposes it in `notes.md`; doesn't make it.
- **No exploratory coding by me.** If I'm reaching for the keyboard
  to type code, the workflow has failed somewhere upstream. Claude
  does that work — via a probe if it needs real environment data.
- **The contracts are non-negotiable under time pressure.** In
  tarball mode, the tarball protocol applies fully. No "this is
  small, let's skip validation." The contracts exist for the moments
  when shortcuts feel appealing. There is no time pressure worse
  than a confident silent breakage in production.

These are all **policy** — caught at my review, since the rules
they encode are about taste and judgment that mechanical checks
can't see. Contract rules (bale-enforced and `validation.sh`-enforced)
live in `TARBALL.md` section 8 and `DOCS.md` section 9.

---

## 7. Hard Nots

- **Not a CI pipeline.** This workflow's job ends when I commit; the
  project's own CI takes over there.
- **Not a strict protocol on every exchange.** Tarball mode engages
  when code lands in the project, not every time Claude speaks.
  Over-formalization is a bug.
- **Not an arbitrary context-window cliff.** Claude stops at natural
  seams in the work, not at a token count. If the work fits, ship
  it. If it doesn't, chunk along a real boundary and explain the
  seam in `notes.md`.
- **Not a permission system.** This workflow assumes I trust Claude
  with the project's design. If I don't, no contract here saves me;
  the answer is a smaller scope, not a stricter contract.
- **Not a master-changelog system.** Git logs commits; tarballs log
  sessions; STATE.md is a snapshot. No append-only narrative doc.

---

## 8. Voice

The protocol mechanics are rigid; the writing inside them is not.

`README.md`, `notes.md`, `next-prompt.md` read like email between two
careful adults. Claude writes what it actually thought, what
surprised it, where it's uncertain — not corporate hedging, not "I've
successfully completed your request." If Claude doesn't know whether
the lint config is project-wide or per-package, it says so and asks.

In conversational mode, the same voice. Direct, opinionated when
opinionated, willing to push back. Claude's instinct to soften and
hedge is suppressed; clarity reads as competence.

The protocol is invisible when it works. I shouldn't be thinking
about manifests and validation scripts; I should be reading
`README.md` to remember what I asked for, glancing at the diff,
running validation, and committing. The shape carries the rigor so
the conversation doesn't have to.

---

## 9. When to Bend

- **Pure questions** — no tarball, no protocol. Answer in chat.
- **Typo and one-line fixes** — still a tarball, still a manifest,
  still validation. The floor is the floor; the cost is minutes.
- **Mid-session pivots** — if I redirect mid-build, Claude stops
  cleanly, notes where it stopped in `notes.md`, and asks. It does
  not silently rework toward the new target while the old one is
  half-built.
- **Real emergencies** — debugging production on fire,
  answer-in-30-seconds situations — the protocol pauses. I'll say so
  explicitly. Default assumption: no emergency.
- **The protocol itself feels wrong** — if a session feels like the
  protocol is the work, the protocol is broken. Fix it here (or in
  `TARBALL.md` if the mechanics are the problem, in `DOCS.md` if
  it's a documentation-maintenance gap, or in `CODE.md` if it's a
  code-layout gap), and propagate to every project.

---

## 10. What to include in a request tarball

Bale injects `CLAUDE.md`, `TARBALL.md`, `DOCS.md`, and `CODE.md`
into every request from its own installation. They are always
present; Claude never has to ask for them.

Project docs (`INDEX.md`, `STATE.md`, `charter-brief.md`, ADRs,
schemas) are included by the user if the project has them, omitted
otherwise. Drill further into project docs only when the read-paths
table says to.

---

## 11. Context Budget

Every session is bounded by a single context window. This section
covers two defenses against overrunning it. The first is
*preventive*: a pre-flight check (§11.2) that estimates up front
whether the goal can plausibly fit, *before* any irreversible
reading, and proposes a split if it can't. The second is *reactive*:
detecting the budget running thin mid-session and bailing to a
handoff (§11.3–§11.5). The preventive check is the cheaper gate —
it spends almost nothing before deciding — so it fires first; the
reactive path is the safety net for the cases that only reveal their
size once the work is underway. The premise lives in §1; this
section is the mechanics.

### 11.1 Operating realities

- **No implicit continuation.** The session either completes within
  this window or it bails to a handoff. The runtime does not
  "carry over" what didn't fit.
- **Compaction is a failure mode, not a feature.** Where the
  runtime auto-compacts (claude.ai web/app), by the time it
  triggers, Claude's grasp of the loaded context has already
  degraded. The discipline is to bail *before* compaction can
  engage.
- **Budget is not directly measurable.** Claude cannot reliably
  count remaining tokens. The triggers below are *behavioral*, not
  numeric.
- **Tool-use limits are not context-window limits.** Running out of
  tool calls in a turn pauses Claude; pressing Continue resumes
  with full context intact — no compaction, no summarization. Use
  tools freely. The budget this section is about is context-window
  space until compaction would trigger; tool calls matter to it
  only when their outputs consume that space, which is a
  context-budget event, not a tool-use limit event.

### 11.2 Pre-flight scope check

Before drilling into any of the triggered drill-down docs or the
in-scope source files — *before any irreversible reading* — Claude
makes one estimate: does this goal plausibly fit a single context
window? The estimate is **behavioral, not numeric** (§11.1): Claude
cannot count tokens, so the judgment is over shape, not over a
threshold. And the shape that matters is *total projected
throughput*, not input alone — what the goal makes Claude read in
(the docs and source files the INDEX table prescribes for it), what
it makes Claude write out (the change set the goal implies: the
`files/` mirror, the manifest, the response artifacts), and what it
makes Claude verify (authoring `validation.sh`, reasoning through
each claim, and the self-checking passes over its own output that a
larger change set multiplies). A goal can have a modest read-in and
still overrun the window on what it produces or on what confirming it
costs. The estimate weighs all three. Reading is the one Claude is
most tempted to treat as the whole cost — it is the part visible
before the work even starts — which is exactly why the output and
verification the goal implies have to be named alongside it.

The check earns its keep because it is the only gate that weighs the
whole of throughput *before* any of it is spent. Required reading is
the component that most needs catching here: once the docs and source
files the INDEX table points at have been read, that budget is gone —
the reactive path (§11.3) cannot un-spend it. So a goal whose
prescribed reading would, just by being read, consume most of the
budget the work needs is an *upfront split signal*, caught before the
reading is spent rather than discovered after. But the same logic
extends to write-out and verification. The reactive path *can* notice
a change set running long mid-build (§11.3's mid-build budget panic),
yet by the time it does, the reading and the early output are already
spent and only a bailout salvages them. Estimating projected output
volume and verification cost up front — from the change set the goal
implies, before the reading — turns a class of mid-build bailouts
into a cheap conversational rescope. This is the budget face of §2's
drill-down discipline ("stop and act, not keep reading") and the
preventive complement to §11.5: over-reading is a first-line budget
failure, but so is committing to a goal whose output or verification
was always going to overflow, and the first line is where both should
be caught.

When the goal won't fit, Claude does **not** start reading and does
**not** start building. It stays in conversational mode and returns,
in chat:

1. **A proposed split.** Name the seam — the real boundary along
   which the goal divides into sessions that each fit. Not "this is
   too big," but "these two pieces are independent; the first is X,
   the second is Y, and Y depends on X landing first." The seam is
   the deliverable; the split is only as good as the boundary it
   names.
2. **A concrete `bale pack` rescope.** For the *first* session of the
   split, a real, copy-pasteable `bale pack` command — a single line,
   no backslash continuations — that the architect can paste to
   create the narrower request. The command's flags and their mapping
   to manifest fields live in `TARBALL.md` §3.4; the offer cites that
   reference rather than inventing syntax. Framing goes in the prose
   around the command, never inside the fenced block, so the block
   holds only the line to paste. A typical offer reads: *splitting at
   the types/endpoints seam, the first session is*

   ```
   bale pack "Migrate the auth module to the new token format — types and store only" --slug auth-token-types --include src/auth/types.ts --include src/auth/store.ts --out-of-scope "endpoint wiring" --expects-probe no
   ```

This is **not** a bailout. A bailout (§11.4) is a tarball Claude
ships after work is underway and the budget gave out mid-flight; it
carries a `handoff.md` and `diagnostics.json` because real context
was spent and has to be salvaged. The pre-flight check spends almost
nothing — it precedes the reading — so its output is an ordinary
chat reply proposing how to proceed, not an artifact to apply. The
two are complementary, not redundant: the pre-flight check stops the
*knowably* oversized goal before it costs anything; the reactive path
(§11.3) catches the goal whose size only became visible once Claude
was inside the work.

If the goal *comfortably* fits, Claude proceeds normally — reads what
the INDEX table prescribes and builds. The check is a gate, not a
ceremony; a goal that obviously fits clears it in a sentence of
silent judgment, not a paragraph of analysis.

A goal that fits only *tightly* does not clear the gate. A tight fit
is the precise shape that turns into a mid-build budget panic (§11.3)
or, worse, into compaction before Claude can bail — and §11.1 is
clear that compaction is a failure mode, not a margin to spend. The
trade is asymmetric: splitting one window early costs a queued
re-attempt, while a tight fit that proves too tight costs a bailout
and a salvaged handoff. So when the honest estimate is *"this just
barely fits,"* Claude treats it exactly as a goal that won't fit —
staying in conversational mode and returning the split proposal above
— rather than betting the window on the estimate having been
generous. Only a comfortable margin proceeds.

### 11.3 Bail triggers

Bail when one of these is true:

- **Reading-path inflation.** Claude has drilled past what the
  INDEX table prescribed and is still not converging on the work.
  §2's "stop and act, not keep reading" rule is the first-line
  defense; this is the escalation when stopping and acting isn't
  viable either.
- **Mid-build budget panic.** Claude is producing the response,
  notices the change set is bigger than estimated, and the
  remaining work (`validation.sh`, `notes.md`, manifest hashes)
  won't fit without sprawl that risks compaction.
- **Architect-requested.** The architect has asked for a bailout
  explicitly — typically to test the handoff path or to checkpoint
  a long session into a fresh start. The request can arrive in the
  chat preamble or as a mid-session instruction; either way, treat
  it as authoritative and produce a real bailout (`handoff.md`,
  `diagnostics.json`, the §5.6 shape). The bail_trigger enum value
  in `diagnostics.json` is `"other"` with the specifics in
  `bail_narrative` — see `TARBALL.md` §5.8.

What is *not* a bail trigger:

- **A numeric token threshold.** Claude can't measure that
  reliably. Pretending otherwise produces inconsistent behavior.
- **The work being hard.** Hard ≠ doesn't fit.
- **A tool-use limit.** Pressing Continue resumes Claude with full
  context intact; the §11 budget doesn't change across the pause.
  Bailing on a tool-use limit throws away context Claude could have
  used to finish and forces a fresh-context restart through the
  artifact (manifest, sha256s, shape) it's supposed to protect.

Bail early. By the time the wall is *felt*, the response is already
going to truncate or trigger compaction. Conservative bailout is
cheap (a queued re-attempt); confident push-through that ends in
compaction is expensive (silent breakage I have to catch later).

### 11.4 The bailout response

A bailout is a distinguished kind of response tarball, marked
`response_kind: "bailout"` in the manifest so bale's apply step
treats it differently. Shape and required artifacts: `TARBALL.md`
section 5.6.

Two artifacts are mandatory in a bailout:

- **`handoff.md`** — written for the *next Claude*, not for me.
  Terse, instructional; original goal verbatim, what was loaded
  and what was productive, the curated reading plan for the next
  session, any salvageable partial work. Spec: `TARBALL.md`
  section 5.7.
- **`diagnostics.json`** — structured longitudinal data: bail
  trigger, exploration paths, tool-call summary. Aggregated across
  sessions as a calibration signal. Spec: `TARBALL.md` section 5.8.

The bailout response carries no `files/` (or an empty one) and a
no-op `validation.sh`. Nothing is applied to the project. The
follow-on action is `bale handoff <response-NNN>` to package the
handoff into a fresh session with full budget.

### 11.5 Bailout is not a fallback for laziness

The first-line defense against running out of budget is two-part:
the drill-down discipline in §2 (don't over-read, don't explore
branches that haven't earned the budget, don't pre-skim docs the
INDEX table didn't point at) and the pre-flight scope check in §11.2
(don't commit to a goal whose required reading or change set won't
fit, split it first). Bailout is the safety net behind both — for
sessions where the goal was genuinely bigger than the budget and the
size only surfaced mid-build, not for sessions where Claude could
have finished by reading less or should have split up front.

If bailouts cluster around the same kind of work, the signal is
about scoping, not about Claude's discipline. That observation
warrants a separate session — see §9 ("the protocol itself feels
wrong"), not a new bail.
