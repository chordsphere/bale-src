# TARBALL.md

> The mechanical contract for tarball mode.
> Read when entering tarball mode (per `AGENT.md`).
> For the *why* behind any of this, see `AGENT.md`.

---

## META

### What this doc is

The wire-format contract for tarball mode. `AGENT.md` covers the
*why* and *when*; this doc covers the *exact shape* of each artifact
and how the bale tool and `validation.sh` enforce it between them.
If something here conflicts with what the agent remembers from a prior
session, **this file wins.**

Bale ships this file in every request, so it is always present.
If it is missing (a hand-rolled request), the agent pauses and asks
(rationale: ADR-0013).

The doc's physical order is core-first: the every-read core —
sections 1, 2, 5, and 7 — reads before the triggered reference
sections (3, 4, 6, 8, 9, 10), which sit past a marked banner.
Section numbers are stable (`DOCS.md` §6.4) and did not renumber;
relocated sections left one-line pointers at their old positions.

---

## INDEX

### Read paths

Sections 1, 2, 5, and 7 are the **core** — the every-read spine for
a session producing a response, and the doc's physical order puts
them first. Everything past the core banner is **triggered
reference**: each row's Situation column below is the trigger, and
if it doesn't describe this session, the section stays unread.

| Situation (trigger) | Load |
|-----------|------|
| Producing a normal response tarball — the default in a worker session whenever work landed (a read-only, planner session produces none, §2) | Core: sections 1, 2, 5, 7 |
| Orienting in the received request needs more than the manifest itself — a field's semantics, what belongs where in `context/`, or how `expects_probe` binds | Section 3 |
| Asked to draft a `bale pack` command, or offering a rescope split (`AGENT.md` §11.2) | Section 3.4 |
| An environment fact the response depends on is missing, stale, or unclear — returning a probe instead of building | Sections 1, 2, 4 |
| The goal won't fit this session's context budget (`AGENT.md` §11 triggered) — returning a bailout | Sections 1, 2, 5.6, 5.7, 5.8 |
| A blocking intent gap in the request prevents trustworthy work — returning a clarification | Sections 1, 2, 5.9 |
| A short, non-blocking question set — at most three, each with a one-word default — returning a light question block | Section 5.10 |
| Writing or debugging `validation.sh` | Sections 5, 7 |
| Writing or debugging `apply.sh` — a delete, a rename's removal half, or an exec-bit restore is in play | Section 5.1.1 |
| Unsure whether something is a violation, or which enforcement layer (bale, `validation.sh`, review) catches it | Section 8 |
| Tempted to stretch the workflow into an adjacent job — sync, CI, installs, writes to the real tree | Section 9 |
| Sanity-checking that the contract isn't heavier than a small change — the smallest viable response | Section 6 |
| Session end — the pack checklists for response, probe, and clarification | Section 10 |

---

## 1. Conventions

- **Session IDs.** `YYYY-MM-DD-<slug>-NNN`, e.g.
  `2026-05-12-vue-scaffold-001`. The slug is short and kebab-cased.
  NNN is a per-day monotonic counter maintained by bale, where the
  day is the UTC day — the date is minted on the same clock as
  every timestamp bale writes, never the packing machine's local
  date. The request manifest's `provenance.packed_at` records the
  pack instant on that clock, and the emitted session opener names
  it. The chat interface shows its own date, the operator's local
  calendar day, which the session id and the tarball's timestamps
  may run a day ahead of.
- **The clock.** Every date bale mints — the session id, its per-day counter, a handoff re-mint — and every timestamp it writes are UTC; a session dates what it writes from the session id, never from the date its chat shows.
- **Artifact directories.** `request-NNN/` and `response-NNN/` use
  the same NNN as the session ID, zero-padded to three digits,
  while the tarball that carries each is named by the full session
  id — `request-<sid>.tar.gz`, `response-<sid>.tar.gz` (§3.1, §10.1
  step 11). A response is numbered to match the request it answers.
  Probes produce no artifact directory (§4.2).
- **Roles.** Four roles recur here and in `AGENT.md`, and every
  one is a role, never a species: the **planner** holds intent
  authority for a request — decomposes goals, authors packs, answers
  the worker's questions, and reviews; the **worker** holds
  mechanism authority — builds responses; the **operator** runs
  pack/apply and the mechanical steps between them; the **courier**
  carries pastes between sessions — a probe's output, an exchange
  record's paste block. Any role can be held by a human or a
  session, and no rule in these docs keys on which. The same party
  commonly holds several hats (the planner who also operates and
  carries), and the shape of an exchange never depends on that.
  "Architect" names the human where a sentence needs the person
  rather than the role. "The agent" is the role-neutral noun for
  the session these docs address — whichever hat it wears — and a
  hat noun (worker, planner) is used where a sentence means one
  hat; in worker-facing prose "the agent" and "the worker" read as
  the same party. A rule stated for a role binds whoever holds it.
- **Examples are examples.** Schemas below reference Vue/Vite/etc. to
  make shapes concrete. They are illustrative, not normative.
  Substitute the project's actual stack.
- **Emitted commands are single physical lines.** Every command a
  request-carried doc or tool emits — a `bale pack` line, a `bale
  open` line, a probe's paste line, a remedy line — is one line with
  no backslash continuations; §3.4 carries the rule and its reason.

---

## 2. Four Exchanges

| Exchange | Direction | When |
|----------|-----------|------|
| Request tarball | planner → worker | start of a tarball-mode session |
| Probe | worker → planner | whenever an environment-specific fact is missing, stale, or unclear (§4.1) |
| Response tarball | worker → planner | once per worker session — any pack with a write forecast — carrying the finished work; a read-only pack returns none |
| Exchange | planner ⇄ worker | a thread opened by the worker's clarification response (§5.9) — both directions travel as the same exchange record, and the session stays suspended until the thread resolves |

The two tarballs are artifacts. The probe is not — it is a
paste-back script and its pasted output, chat-ephemeral by design
(§4.2). The exchange is a record in both directions: the worker's
clarification manifest opens it and the planner's answer continues
it, each round preserved by bale under the session (§5.9.2), and
each carried by a courier of the operator's choosing — a tarball or
a paste block (§5.9.2). Chat carries conversation and never a
blocking ask (§5.9.1); the one ask it does carry is the light
question block (§5.10) — a shape, not conversation, whose trail is
the eventual response rather than a thread.

What a session owes back follows from how it was packed: a worker
session, any pack with a write forecast, owes one response tarball
carrying the finished work; a planner session, a read-only pack,
lands nothing and returns no response tarball, not even an empty
one — it owes its answer in chat and, for each session it is asked
to author, a crafter bundle beside its `bale open` line.
The request manifest says which kind a session is: the empty
forecast, `resolved_scope: []`, is the read-only pack's stamp
(§3.2, §3.4). An empty response tarball is not a receipt — the
planner reads a planner session's answer in chat, and a tarball
with nothing in it only adds a no-op to apply. A planner session
that needs a fact or a decision still asks through the probe, the
light question block, or the clarification response, like any
other session (§5.10).

---

> Sections 3 (Request Tarball) and 4 (Probe) are triggered
> reference — relocated past the core banner, below section 7
> (core-first order; numbering unchanged).

---

## 5. Response Tarball

### 5.1 Shape

```
response-NNN/
  manifest.json        # every change, structured (required)
  apply.sh             # operations beyond the files/ mirror (required; no-op script if none)
  validation.sh        # the worker's hypothesis test on the changes (required)
  files/               # mirrors the project tree from repo root (required when changes[] has created/modified entries)
    src/...
    package.json
    ...
  README.md            # optional; color/context beyond manifest.summary
  notes.md             # optional; include when there's something to surface
```

`files/` mirrors the project tree from the repo root —
`src/components/Foo.vue` ships as `files/src/components/Foo.vue` —
so apply is `cp -r response-NNN/files/. <project>/` with no path
translation. The mirror is enumerated by its files: an empty
directory under `files/` declares nothing and is ignored, by the
§10.1 correspondence and the §5.6.1/§5.9.2 "absent or empty" test
alike.

**`files/` carries source, never generated artifacts** — no
`__pycache__/`, `*.pyc`, `*.pyo`, `node_modules/`, `dist/`, or
`build/`. A **contract** rule (`AGENT.md` §6): bale's apply
pre-flight rejects a response whose `changes[]` paths include one,
naming them, before any staging. The deny list is exactly those
names, not a heuristic, so a source file that merely resembles one
(a script named `build`, a `pyc_utils.py`) passes (rationale:
ADR-0013 §5.1). `.bale/` paths are never shipped either, but that
rejection is path safety's, not this rule's.

`README.md` and `notes.md` ship when they have content and are
omitted otherwise — absence means nothing more needed saying, and no
stub is written. Bale shows them in the apply walkthrough when
present. (`next-prompt.md` is retired, §5.5.)

**File changes go inside the tarball, not alongside it**: in
`files/` and `apply.sh`, declared in the manifest, never pasted into
chat as a preview or a courtesy copy (rationale: ADR-0013 §5.1). The
rule binds the deliverable's shape only — when code is the response,
the tarball is the response — and it does not make every
tarball-mode reply a tarball. A missing, stale, or unclear
environment fact takes a probe (section 4); a short, non-blocking
question set takes a light question block (§5.10); a *blocking*
intent gap takes the clarification response (§5.9). A concern or a
scope observation that asks nothing is said in prose; an ask is
never prose.

Two further response kinds share one set of empty change surfaces —
no `files/`, a no-op `apply.sh` and `validation.sh` — and §5.9's
recourse table is how the worker picks between them. A **bailout**
(§5.6) answers a budget gap: the session can't fit the goal in its
context window (`AGENT.md` §11); it adds the mandatory `handoff.md`
and `diagnostics.json`, and apply treats it as informational rather
than applicable. A **clarification** (§5.9) answers an intent gap:
the *request* blocks trustworthy work; its payload rides in the
manifest's `questions[]`, and unlike a bailout it does not consume
the session — the lock stays held, the planner answers through the
exchange thread (§5.9.4), and the same session continues to a normal
response.

### 5.1.1 apply.sh

`apply.sh` carries only what the cp-mirror can't express. A delete
is an `rm` of the path. A rename is a `created` entry under `files/`
(the new path, full content) plus an `rm` of the old path — never an
`mv`, because bale's commit step is driven per `changes[]` entry,
not from a tree-level diff. An executable bit is restored with a
per-path `chmod +x` (`chmod +x scripts/release.sh`, one line per
file), because the `files/` overlay strips mode and can't infer
which `created` or `modified` file was meant to be executable — the
worker's responsibility (failure analysis: ADR-0013 §5.1.1), with
§7.7's exec-bit assertion as the validation-side guard.

Bale runs `apply.sh` with cwd set to the staging copy, before
`validation.sh`, then reconciles the result against the manifest:
every file removed must be a `deleted` entry, every file added a
`created` one, and every modified file's sha256 must match. An
`apply.sh` that touches an undeclared file fails reconciliation and
the tarball is rejected; bale's path-safety check catches escapes
from the staging tree. The script installs nothing, builds nothing,
and has no side effects beyond file-tree operations.

The scaffold is the crafter's (§5.2): the verbatim no-op when
nothing needs the script —

```bash
#!/usr/bin/env bash
# No additional operations for this session.
exit 0
```

— otherwise an `rm -f` line per `--deleted` path, each under a
reason comment the worker fills, then the `chmod +x` lines for the
paths named with `--executable`.

### 5.2 manifest.json

```json
{
  "session_id": "2026-05-12-vue-scaffold-001",
  "responds_to": "2026-05-12-vue-scaffold-001",
  "corrects": null,
  "response_kind": "normal",
  "summary": "one-paragraph summary of what this response delivers",
  "changes": [
    {
      "path": "src/components/Foo.vue",
      "action": "created",
      "reason": "implements the foo widget called out in the goal",
      "size_bytes": 1842,
      "sha256": "abc123..."
    },
    {
      "path": "package.json",
      "action": "modified",
      "reason": "adds @vueuse/core for useDebouncedRef",
      "size_bytes": 2104,
      "sha256": "def456..."
    },
    {
      "path": "src/legacy/Bar.vue",
      "action": "deleted",
      "reason": "superseded by Foo.vue; no remaining importers",
      "size_bytes": 0,
      "sha256": null
    }
  ],
  "deferred": [
    {
      "what": "tests for Foo.vue",
      "why": "test setup not yet decided — proposed in notes.md (§5.4.1)"
    }
  ],
  "validation_will_run": [
    "file syntax (vue, ts, json)",
    "eslint",
    "vue-tsc --noEmit",
    "vite build (staging only)"
  ],
  "claims": {
    "eslint": "pass",
    "vue-tsc --noEmit": "pass",
    "vite build (staging only)": "pass"
  }
}
```

The skeleton is mechanized: `tools/craft_response.py`, shipped in
every request per §3.1, emits it for any kind (`--kind
{normal,bailout,clarification}`, default `normal`) with the computed
fields filled — `session_id` and `responds_to` from `--sid`,
`response_kind` from `--kind`, sizes and hashes per §5.2.1 — plus
the §5.1.1 `apply.sh` scaffold; the two non-normal kinds' full
artifact sets are §5.6.1 and §5.9.2. The crafter never validates its
own output: the worker fills the judgment fields, then the lint
judges (§5.2.2's workflow). The identity fields' semantics —
`session_id` equal to `responds_to` on every kind, `corrects`
naming the response this one re-attempts or null, `response_kind`
selecting the shape — are `response-manifest.schema.json`'s field
descriptions (in the bale installation). The judgment fields:

- **`summary`** — one paragraph on what the response delivers.
- **`changes`** — may be empty: a no-op change set is `changes: []`
  with no files under `files/`; the §10.1 correspondence then holds
  vacuously, and a file under `files/` beside an empty `changes[]`
  is an undeclared file, not an implied change.
- **`changes[].action`** — `created`, `modified`, or `deleted`. A
  `deleted` entry has `size_bytes: 0` and `sha256: null` and no file
  under `files/`; the removal itself is `apply.sh`'s.
- **`changes[].reason`** — non-empty for every entry (bale rejects
  empty strings), written for a reader who wasn't around for the
  session.
- **`deferred`** — the in-goal work the worker considered and didn't
  do, each with a `why`: the list is how the planner knows what's
  not here. How it differs from a Proposal is §5.4.1.
- **`validation_will_run`** — what `validation.sh` is configured to
  do, so the planner can predict the cost before running it; each
  entry is a check's canonical identifier (§5.3).
- **`claims`** — the worker's prediction per claimable check,
  distinct from what validation finds (§5.3).
- **`feedback`** — optional session feedback (§5.2.2).

### 5.2.1 Computing size_bytes and sha256

`size_bytes` and `sha256` are computed, never transcribed
(rationale: ADR-0013 §5.2.1): bale's pre-flight rejects any tarball
whose manifest sha256 disagrees with the bytes under `files/` (§7).
The computation is the crafter's: `tools/craft_response.py` walks
`files/`, computes every value, and emits the `changes[]` skeleton
with the mirror prefix stripped, paste-ready (`--changes-only` for
the array alone; `--help` for the full surface), and writes the
`deleted` literals too (`--deleted PATH`). Nothing in this field set
is produced from memory — a hash recalled rather than recomputed is
exactly what §10.1 step 10 and `AGENT.md` §11.6 exist to catch.

### 5.2.2 The feedback block

An optional top-level `feedback` object carries the session's own
account of itself; apply persists it verbatim into the session's
telemetry record, where it aggregates across sessions. A manifest
without the block still validates; a new response includes it. Its
field-by-field contract — every member, its shape, and what an
empty value asserts — is `response-manifest.schema.json`'s field
descriptions, and this section does not restate them.

The block is **two streams split by trust level** (rationale:
ADR-0013 §5.2.2). **`mechanical`** holds what the lint
(`tools/response_lint.py`, shipped in every request per §3.1)
recomputes — `response_kind`, `schema_valid`, `mirror_agreement`,
`claims_subset` — plus two members whose shape is fixed though their
content is the worker's: `linkage`, present when the session went
through a probe or clarification round, and `provenance`, the
request's provenance block echoed verbatim plus `model_identity`,
spelled `<vendor>:<model>` with `unknown` as the model token when
the surface does not show the string (`AGENT.md` §11.7's table says
which do). **`self_reported`** holds the worker's judgment, which
the lint checks for shape only, never content. Honest empties there
are meaningful — `[]` asserts *none arose* — with one exception:
`docs_read` is seeded `[]` by the crafter for scaffold presence, so
a shipped `[]` is indistinguishable from an unfilled stub and the
lint warns `DOCS_READ_EMPTY_STUB`; fill the list, or delete the key.
`forecast_departures` is §5.4's twin record.

**Fill the mechanical stream by running the lint, not by hand.**
Build the response through §10.1 steps 1–9; when the crafter seeded
the block from the request (`--request`), fill `model_identity` and
`self_reported` first. Then run `python3 tools/response_lint.py
<response-dir> --emit-feedback-mechanical`, paste its object in as
`feedback.mechanical` — over a seeded block's four placeholders key
for key, never replacing the whole object, which would drop the
seeded `provenance`; the emitter computes the four values only, and
`linkage` is the worker's to add — and run the lint once more:
its feedback-block check recomputes every mechanical value against
the directory as packed. A mismatch is the tell of a hand-filled or
stale block, and the fix is to re-run, never to adjust values until
the check goes quiet.

The emitter exits 0 once it has written the block and 1 when there was nothing to paste, so a worker chaining it with `&&` never skips the paste; `--request` lets the lint read `resolved_scope` and warn on an undeclared forecast departure, and lets the crafter seed the departure stubs §5.4 names.

### 5.3 Claims vs verdict

The worker doesn't run validators. What the worker says about an
outcome is a **claim**; what `validation.sh` produces is a
**verdict**. They're separate fields so disagreement is itself
diagnostic.

`claims` values per check:

| Value | Meaning |
|-------|---------|
| `pass` | The worker predicts this check will pass |
| `fail` | The worker knows this check will fail (e.g. a deliberate WIP) |
| `untested` | The check will be skipped in my environment |
| `unknown` | The worker genuinely can't tell |

A claim is the bare string, or the annotated object
`{"value": "pass", "claim_basis": "observed"}`, which adds the
claim's basis at ship time — `predicted` from structural grounds, or
`observed` from a real run before shipping; the bare string stays
valid, and the object's shape is the schema's.

One rule scopes the block: `claims` covers the project-level checks
(lint, typecheck, build, tests), and when the project has none it
covers the response's session-specific assertions (§7.2 item 6)
instead. Either way every key is a genuine prediction about a
non-tautological check; an empty block while claimable checks ran
wastes the calibration signal the field exists for. The mechanical
checks the manifest was written against (manifest consistency, file
syntax) are tautological — a `pass` adds nothing — and are never
claimed.

A `claims` key is the check's **canonical identifier**: its
`validation_will_run` entry, reused **verbatim** (same characters,
same spacing) as the key and again as the verdict label §7.3
reconciles against. A key with no verbatim match in
`validation_will_run` is unpairable — a prediction about a check the
manifest never says will run. The match is one-directional:
`set(claims) ⊆ set(validation_will_run)`, never the converse, since
`validation_will_run` also lists the unclaimed mechanical checks,
which stand as run-but-unclaimed. This subset relation is what §10.1
self-checks before packing and `AGENT.md` §11.6 re-derives after a
compaction.

A claim disagreeing with its verdict doesn't reject the tarball;
it's flagged in validation's end-of-run report (what the
disagreement pattern is for: ADR-0013 §5.3). A check claimed
`unknown` earns a line in `notes.md`: *what would the worker need to
know to predict?*

### 5.4 notes.md (optional)

Include `notes.md` when there's something to surface. Skip the file
when there isn't — omission is the canonical signal for *"nothing
needed saying."*

Conversational when included. Use it for:

- Decisions the worker made that I should ratify (especially when a
  probe wasn't possible and the worker had to choose).
- Places I should look closely on review.
- Anything surprising the worker found in the existing code.
- Honest uncertainty — *"I'm not sure whether X should live in
  `composables/` or `utils/`; I put it in `composables/` because it
  uses reactive state. Move it if that's wrong."*
- Any `unknown` entry in `claims` — what the worker would need to
  predict with confidence.
- Things the manifest's structured `reason` field couldn't carry.
- Every `changes[]` path outside the session's write forecast — a
  new file the pack could not have named, or a modification the
  goal turned out to require, that no forecast entry covers. List
  each such path explicitly, with why the goal required it, so the
  operator can admit it at apply (§3.2); an unenumerated
  out-of-forecast path surfaces as a refusal instead of a decision.
  Each path listed here is also recorded in the manifest as
  `forecast_departures` under `feedback.self_reported`: one object
  per path, with exactly two keys — `path`, the `changes[]` path,
  and `why`, the same reason in a sentence. Given `--request`, the
  crafter seeds one such object per `changes[]` path outside the
  request's `resolved_scope`, its `why` left empty — an unfilled stub
  cannot pass the lint — so the `why` is the worker's to fill; a
  session with no such path omits the key.
- Follow-up work worth suggesting — as a Proposals section (§5.4.1).

If a session is small enough that none of the above apply, don't
write a stub.

#### 5.4.1 The Proposals section

When a session surfaces follow-up work worth suggesting — a seam
visible only from inside the code, an out-of-scope fix worth doing
(rationale: ADR-0013 §5.4.1) — `notes.md` carries it under a
`## Proposals` heading. Each proposal is a short block:

- **What** — the suggested follow-up, in one or two sentences.
- **Why** — the rationale, grounded in something this session
  actually saw. A proposal without a reason is a wish, not a signal.
- **Scope hints** — optional: the files or seams involved, and any
  ordering dependency on other work ("only after X lands").

Proposals are prose suggestions with rationale, **never ready-to-run
commands** — no `bale pack` line, no literal paste-this text; §3.4
carries the reasoning. The planner reads proposals as *input*,
decides sequencing, and authors its own pack commands (§3.4).

Proposals are distinct from the manifest's `deferred` list (§5.2):
`deferred` names in-goal work the session considered and didn't do;
Proposals name work the session's vantage point revealed, whether or
not the goal asked for it. An item can appear in both — deferred for
the record, proposed with the rationale — when the worker thinks it
should be near the top of the queue. If nothing is worth proposing,
omit the section: absence means *no suggestion*.

### 5.5 next-prompt.md (retired)

Retired by session `2026-07-06-retire-next-prompt-006`: nothing new
ships `next-prompt.md` (apply still surfaces one found in an older
archive, labeled deprecated), follow-up flows as `notes.md`
Proposals (§5.4.1), and why the shape went is ADR-0013 §5.5.

### 5.6 Bailout response

A bailout is what the worker returns when `AGENT.md` §11's triggers
have fired — the goal won't fit this session's context budget, and
the worker hands off to a fresh session instead of pushing through;
the *why* lives in `AGENT.md` §11.

#### 5.6.1 Shape

The artifact set is mechanized: `tools/craft_response.py --kind
bailout --write` emits it whole — the manifest with its empty change
surfaces (§5.6.2) and no `files/` (absent or empty), the no-op
`apply.sh` and `validation.sh` the kind fixes, the required
`handoff.md` scaffolded with §5.7's section headers (the content
under each is the worker's), and the required `diagnostics.json`
skeleton (§5.8). `README.md` is absent in bailouts: `handoff.md`
carries the forward-looking content for the next agent, and
`notes.md`, optional, carries commentary addressed to me. The lint
judges the finished response, and an unfilled skeleton is
deliberately lint-invalid.

`response_kind: "bailout"` is the canonical marker: apply branches on
it, displaying the handoff summary instead of applying changes and
prompting for `bale handoff <response-NNN>` to package a fresh
session.

#### 5.6.2 Manifest specifics for bailouts

Every change surface is empty — nothing changed, nothing ran,
nothing is claimable — and the crafter emits them that way while the
lint rejects a bailout that violates them. The judgment halves: `summary`
is one paragraph on what was attempted, which trigger fired
(`AGENT.md` §11.3), and what the handoff prescribes; deferred work
lives in `handoff.md`'s prescription, never as a flat `deferred`
list. `responds_to` still names the request this answers; the
session packed after `bale handoff` gets its own fresh `session_id`
(same slug, new date and NNN), and its
`depends_on.previous_response` points at the bailout.

#### 5.6.3 Apply-time UX (moved)

Moved beside the bale implementation: apply-time behavior is a
contract on the bale tool, not on the worker, and nothing that binds
response authoring left with it.

### 5.7 handoff.md (required in bailout responses)

Written for the **next agent's session**, not for me: terse and
instructional — no hedging, no conversational softening, no "I"
reflection beyond what the next agent needs to plan its budget. The
crafter's scaffold carries the required sections in their required
order; what goes under each:

- **`# Handoff`** — the title line.
- **`## Original goal`** — `manifest.goal` from the request this
  bailed on, verbatim, so the next session need not re-extract it.
- **`## What I loaded`** — every doc and source file actually read,
  each with a verdict on whether it earned its budget:
  `path/to/doc.md` — necessary | wasted | partial.
- **`## What I explored`** — the reasoning paths pursued
  (drill-downs, hypotheses, design options), each productive | dead
  end | inconclusive, concretely enough that dead ends aren't
  repeated.
- **`## What I learned`** — concrete observations that compress the
  next session's reading ("the logic for goal X lives in
  `composables/`, not `utils/`"; "skip `src/legacy/`, nothing in it
  is reachable"); if nothing useful was learned, say so.
- **`## Reading plan for the next session`** — the most important
  section: a specific, INDEX-table-compatible drill-down
  prescription, numbered where order matters, whose job is to put
  the next agent on track in one read, not ten. When the bailing
  agent has a recommendation, the plan is written for *that* piece —
  concrete, single-track, ready to execute — with alternatives
  framed as overrides ("if the architect picks X instead, the plan
  is Y"), never as an equal-candidate menu, which loses the
  recommendation to a "which piece?" round-trip. A multiple-choice
  plan is reserved for a genuine close call, and then the handoff
  also declares that **the next session opens in conversational
  mode** and moves to tarball mode after the architect picks.
- **`## Salvageable work`** — partial decisions, sketches, or code
  stubs worth keeping, verbatim where possible; otherwise "Nothing
  to salvage — restart from the reading plan."

The next agent reads `handoff.md` as the first `context/` doc. Its
reading plan is high-value input, ratified by the planner at
`bale handoff` time — the request manifest remains authoritative,
and where the two disagree the manifest wins.

### 5.8 diagnostics.json (required in bailout responses)

Structured longitudinal data, aggregated across sessions to
calibrate where budget actually goes. The shape is mechanized: the
schema of record is `schemas/diagnostics.schema.json` (in the bale
installation, reachable from any project the way the `tools/` pair
is), whose field descriptions say what each judgment field wants;
the crafter (§5.6.1) emits the skeleton with its required keys —
`session_id` filled, everything else empty — and the lint validates
the filled file against it. Two notes the schema doesn't carry: a
`bail_trigger` for an architect-requested bailout is `"other"`, with
the specifics in `bail_narrative`, rather than a new enum value
(enum design: ADR-0013 §5.8); and each `context_loaded[].verdict`
is qualitative, since the worker can't measure token spend per doc.
Aggregation is `bale stats`'s job: apply keeps each bailout's
diagnostics with the session's record, and the stats verb reads the
accumulated records.

### 5.9 Clarification response

A clarification response is what the worker returns when a
**blocking intent gap** in the request prevents trustworthy work. It
is the third distinguished response kind, structurally the bailout's
sibling, and it completes a taxonomy of recourses keyed on
**mechanics — what can answer the gap — not on where the gap
originated**:

| Recourse | Mechanics | Typical gap |
|----------|-----------|-------------|
| probe (§4) | a read-only script run against the environment | an environment fact — file contents, versions, tree state |
| clarification (§5.9) | questions put to the planner | an intent gap — the request is ambiguous, contradictory, or assumes knowledge the worker was never given |
| bailout (§5.6) | a budget handoff to a fresh session | the goal won't fit the context window |

The mechanics keying's design rationale is ADR-0011.
A gap met under `expects_probe: no` is §3.3's: its one home.

#### 5.9.1 When it engages

Canonical intent-gap triggers: an undefined term in the goal; a
constraint that conflicts with an included file; a decision the
packer made but did not transport into the request. No script
against the environment can answer these — which is exactly why
they are not probes.
A gap met under `expects_probe: no` is §3.3's: its one home.

**Questions must be blocking.** A clarification response asserts:
*this session cannot produce trustworthy work without these
answers.* Nice-to-know questions go in `notes.md` Proposals on a
full response (§5.4.1), not here (precedent: ADR-0011). The same
default-to-ask doctrine that governs probes (§4.1) governs
clarifications: proceeding on a guessed intent is the confidently
wrong response this workflow exists to prevent. For a gap that does
not block — a preference the work can proceed without — two
lightweight paths stand, and neither is prose: the light question
block (§5.10), when the set passes its count test, or proceeding on
the most plausible assumption, named explicitly in `notes.md` and
flagged for review — the recoverable-risk posture §3.3 takes. The
test is *blocking*, not *size*: a small question that blocks
trustworthy work is still the artifact, and a non-blocking set is
admitted to the light tier by its count, never by how small it
looks.

**The artifact is the ask shape, on every path.** A blocking ask is
a clarification response — the manifest with its `questions[]` —
whoever is at the other end. The shape does not depend on the
counterparty (§1): the worker always emits the formal record, bale
always preserves it and emits the next paste block, and a harness,
where one exists, only stops the operator from being the one who
pastes. Which courier carries the record is the operator's choice
(§5.9.2), and either way the record persists for aggregation
(§5.9.4). Chat is not a surface for a blocking ask on any path. If
that rule is broken and a blocking ask resolves in chat anyway, the
eventual response's `notes.md` records the question and its answer —
the §4.5 provenance rule applied as the fallback, since chat is
ephemeral; that fallback is provenance for a breach, not a
sanctioned path.

#### 5.9.2 Shape and manifest specifics

Unlike the bailout there are no companion artifacts: the payload is
the manifest's own `questions[]` block — required and non-empty on
this kind, forbidden (or empty) on every other. `README.md` is
absent on a clarification in either direction; `notes.md`, optional
and addressed to the planner, is the prose channel.

Two couriers, one record: the tarball carries the manifest, the empty change surfaces and an optional `notes.md`; the paste block carries the manifest JSON alone; a question row's `context` rides both.

The operator picks the courier; the record is the same either way.
**The tarball** is the response tarball shape with the empty change
surfaces, which apply ingests. **The paste block** wraps the same
JSON for a courier who pastes rather than uploads: a fenced,
self-delimited block with the probe's four properties (§4.2) —
sentinel lines `BALE EXCHANGE BEGIN <sid>` and `BALE EXCHANGE END`,
the record's JSON as the body, a purpose header stating the
direction and the round, and an integrity trailer carrying the
body's sha256 so a truncated paste is detected and re-requested
instead of reasoned from. `bale relay <sid> <file|->` ingests the
block (§5.9.4); run without the file argument it re-emits the
thread's latest recorded round, byte-identical, and records nothing,
so a lost paste is recovered by re-emission rather than by a new
round.

Each round of the thread is an **exchange record**,
`exchange-record.schema.json` (in the bale installation): one schema
for both directions, whose field descriptions are the record's
contract. A preserved clarification manifest reads as the thread's
`from: worker` record for its round, so round one is this manifest
and the thread continues from it.

The shape is mechanized: `tools/craft_response.py --kind
clarification` emits the manifest skeleton — `response_kind:
"clarification"`, the same empty change surfaces as §5.6.2 (bale
rejects a clarification that violates them), no `files/` (absent or
empty), and `questions[]` seeded with four-field entry stubs
(`--questions N` for more than one) — plus, under `--write`, the
no-op `apply.sh` and `validation.sh` the kind fixes. The row's
schema of record is `response-manifest.schema.json`; the lint judges
the finished response, and an unfilled skeleton is deliberately
lint-invalid. Two judgment notes survive the tool: `summary` is one
paragraph on what the session was asked to do and that it is
blocked on the questions below; and `default_assumption` is
load-bearing — it lets the planner answer with a single *"your
assumption is correct"* and surfaces the worker's reasoning for
audit.

**The worker-side flow, when the courier is the paste block.**
Scaffold (`--kind clarification`), fill the judgment fields, render
the filled file with `tools/craft_response.py --emit-block <file|->`,
hand the block to the courier. The input is either shape the thread
carries: a filled clarification manifest, rendered in its `from:
worker` reading — `round` from `--round` (an integer at least 1,
default 1, valid only with `--emit-block`), `created_at` stamped at
emission — or a filled worker exchange record, rendered as it stands
once it validates. A formal ask ships both transports: the
clarification tarball **and** the `--emit-block` rendering of the
same manifest, so the operator chooses the courier at carry time and
the paste route stays first-class. The record is validated before
anything is rendered; a `from: planner` record refuses (the
planner's side is `bale relay`'s to emit, since it holds the
thread), and a `--round` that contradicts a record's own `round`
refuses rather than rewrites it. stdout is the block and only the
block.

The block reaches chat as a file: redirect `--emit-block` to a file
and present that file. A block typed inline instead must keep every
`\uXXXX` escape as an escape, because the body is ASCII-escaped and
the trailer hashes those bytes; and on a trailer refusal the worker
re-presents the file and never retypes the block.

The worker's emission and `bale relay`'s are byte-identical for the
same record — a pinned property, held by parity tests, because the
trailer hashes the body — so this section describes the flow, never
the bytes.

A question row may also carry `options`, `recommendation`, and
`priority` (`blocking` | `batched`); a row without them still
validates, their shapes are the schema's, and their doctrine is
planner-side (`PLANNER.md` §15), a pointer the worker filling them
does not follow. What the asker needs is this: a `batched` question
leaves the worker proceeding on its named `default_assumption`, and
a `blocking` one suspends the session the way a clarification
already does (§5.9.4).

#### 5.9.3 Apply-time UX (moved)

Moved beside the bale implementation: the apply-time ingest and the
thread it opens are bale's contracts, and the worker-facing
consequence stays in §5.9.4.

#### 5.9.4 Posture and the answer path

A clarification is respectable, not a failure — the intent-gap
analog of a probe (posture: ADR-0011). It is also a signal about
the *request*: clarifications clustering against one packer or one
kind of request indicate a packing or decomposition problem. The
preserved manifests under `.bale/clarifications/` are the
aggregation surface for that signal (jq across
`.bale/clarifications/*/*.json`), parallel to the role
`diagnostics.json` plays for bail triggers.

The answer path is the thread, and it is one path, mirroring the
probe's §4.6. The planner reads the questions — in the apply
walkthrough or from the paste block — and answers as an exchange
record (§5.9.2): an `answers[]` row per question, `as-recommended`
when the worker's recommendation or `default_assumption` stands.
`bale relay` records the answer as the thread's next round, keeps
the session suspended, and emits the worker-facing paste block; the
courier carries it to the worker, who continues under the same
session id and ships the normal response the clarification
deferred. A planner that cannot answer from its own context
escalates upward and answers when it can; a planner that answers and
needs to ask back does both in one record. The artifact is identical
whoever holds the planner and courier roles. If the gap invalidates
the request's framing, the recourse is `bale unlock` and a repack —
the planner's call.

### 5.10 The light question block

The light question block is the one ask chat carries, and it is a
shape, not conversation. A turn that needs something from the
packer, an environment fact or a decision, ends in the matching
shape: a probe block, a light question block, or a clarification
response; a question asked as prose is not a shape, because it gets
lost. Every other turn is ordinary prose. The probe block's format
is §4.2's and the clarification response's is §5.9's. The light tier
exists because a sufficiently short question set is faster to read
and answer in chat than to relay through the exchange, and its
audit trail is the eventual response, not the thread. The block is
specified here format-first so a worker can author it by hand
wherever the crafter is unreachable; `tools/craft_response.py
--light-block <file>` is a convenience render over this shape, from
the same filled clarification manifest `--emit-block` takes.

**Admission is a count, not a judgment.** A question set is
admitted to the light tier when it holds at most three questions,
none multi-tiered, and each carries a default the packer can ratify
with a word or an answer that fits on one line; the worker counts,
never judges. *Multi-tiered* means options that need explaining, or
a `why_blocked` that needs a paragraph. Anything else — a fourth
question, a tiered one, a default with no one-word ratification —
is a clarification response (§5.9), however non-blocking the set
feels; and a question that *blocks* trustworthy work is a
clarification response however short it reads (§5.9.1). Size never
admits. The count does.

**The block.** Sentinel-bracketed and human-readable, one numbered
entry per question. The sentinels are `=== LIGHT BEGIN <sid> ===`
and `=== LIGHT END <sid> ===`, on the probe block's model (§4.2),
with the session id in place of the slug so the block names the
session it suspends. Each entry renders a clarification question
row's four fields (§5.9.2) under four fixed labels — `[n] question`
/ `while doing` / `would assume` / `why blocked` — mapping in order
onto `question`, `context`, `default_assumption`, and `why_blocked`,
so one question row feeds either courier: a light block the packer
sends formal becomes a clarification with no rewriting.

```
=== LIGHT BEGIN 2026-05-12-vue-scaffold-001 ===
[1] question:     Debounce in the composable or the component?
    while doing:  wiring useDebouncedRef into SearchBox.vue
    would assume: the composable; the component stays presentational
    why blocked:  the brief names both files, neither as owner
[2] question:     Keep the prototype's 300 ms delay?
    while doing:  setting the default in the composable's signature
    would assume: yes, 300 ms
    why blocked:  the prototype's value may have been a placeholder
Reply: answer inline, "as assumed", or "formal".
=== LIGHT END 2026-05-12-vue-scaffold-001 ===
```

The block ends with the packer's three replies, every time. The
packer replies in one of three ways: answer inline; "as assumed" to
ratify every default at once; or "formal" to have the same questions
returned as a clarification response. An inline answer may mix the
first two — "[1] the component; [2] as assumed". "Formal" moves the
same rows onto the thread: the worker re-emits them through §10.3's
path as round one of a clarification, and from there the exchange
record (§5.9.2) is the trail.

**The trail is the eventual response, not the thread.** A light
block opens no exchange record and makes no telemetry attempt; the
session's `clarification.rounds` stays zero, correctly. Instead the
eventual response's `notes.md` names each question and its answer —
the §4.5 provenance rule, here as the sanctioned path — and a block
answered "as assumed" is recorded the same way, each default noted
as ratified; silence in `notes.md` about an emitted block is the
tell of a lost answer.

**The worker does not idle.** With a light block emitted, the turn
ends; nothing is built ahead of the reply, and the session resumes
on the packer's answer exactly as a clarification suspends and
resumes (§5.9.4) — same session id, same request, the normal
response still owed. A packer who has not replied has not answered;
the worker does not read silence as "as assumed".

---

> Section 6 (Worked Example) is triggered reference — relocated
> past the core banner, below section 7 (core-first order;
> numbering unchanged).

---

## 7. Validation

Two validations run on every response tarball, and they answer
different questions.

**Bale's pre-flight** (the contract rules in section 8 below)
answers *"is this tarball well-formed?"* — manifest schema, sha256
agreement, path safety, out-of-scope, `apply.sh` reconciliation. It
runs first and rejects malformed tarballs before any other work; if
it rejects, `validation.sh` never runs.

**The response's `validation.sh`** answers *"do the changes do what
the worker claims they do?"* It is the worker's per-session
hypothesis test, written fresh for each response — not a fixed
project pipeline. The worker chooses what to invoke based on what
this session actually
touched: typically the project's lint, typecheck, and build against
the modified files, plus session-specific assertions for behaviors
that changed. The project's CI plays the regression-prevention role
after the bale is merged; `validation.sh` does not duplicate it.

Some projects additionally pin a planner-authored **blind
checkpoint** that bale runs in staging beside `validation.sh`
(checkpoint first; both always run). It is authored blind — by the
planner from the request, never by the worker building against it —
and the worker neither writes, edits, nor declares it:
`validation_will_run` and `claims` describe the worker's own script
only. A project may also pin required check names the worker's
`validation_will_run` must include; apply refuses an omission, and a
declared check may still `[SKIP]` with a reason at runtime.

A HOLD reaches the worker as one addressed block that `bale apply`
prints between the whole-line sentinels `=== RELAY BEGIN <sid> to
worker ===` and `=== RELAY END <sid> to worker ===`: the judge line
naming which judgment held, the failed checkpoint probes by label
alone, the worker's own `validation.sh` output, and the `bale retry`
line a re-attempt ends its turn with. That block is the whole of the
failure context — it carries nothing else of the checkpoint's output,
by construction — so the worker diagnoses from it and never asks for
the session log; if the labels point at the checkpoint rather than the
work, the ask is for the spec from those labels (`PLANNER.md` §5).

### 7.1 The staging-copy approach

Validation never writes to the real project. The full pipeline:

1. Bale creates a staging directory (default: `<repo>/.bale/staging/`,
   configurable via `--staging-dir`).
2. Bale copies the current project state into staging.
3. Bale applies `files/` over the staging copy, then runs `apply.sh`
   in staging for the operations the mirror can't express — deletes,
   the removal half of renames, exec-bit restores (§5.1.1).
4. Bale reconciles the post-`apply.sh` staging tree against the
   manifest: every created/deleted/modified path must match a
   manifest entry, and no others. Mismatches reject the tarball
   before `validation.sh` runs.
5. `validation.sh` runs the check sequence inside staging.
6. Reports pass/fail; leaves staging in place for inspection unless
   `--clean` is passed.

The script prints, at the top of its output, every location it will
write to. No surprise writes. The usual offender is an interpreter
cache: a Python suite run in staging leaves `__pycache__/`
directories beside the sources it imports. Suppress the cache —
`PYTHONDONTWRITEBYTECODE=1` in the script's environment, or
`python3 -B` — or announce it with the other locations. The
reconciliation of step 4 has already run by the time the script
does, so nothing mechanical catches a write the script did not
announce; the printed list is the whole of the check.

### 7.2 Check sequence

Each check prints `[PASS]`, `[FAIL]`, or `[SKIP] <reason>` on its own
line. Silent skip is a bug.

The worker chooses which checks to include based on what this session
touched. A markdown typo session ships file-syntax only; a session
touching component logic includes lint, typecheck, and likely tests
plus session-specific assertions. The list below is typical, not
mandatory:

1. **Per-file syntax**: appropriate per-extension check (e.g.
   `vue-tsc --noEmit` for `.vue`, `tsc --noEmit` for `.ts`,
   `node --check` for `.js`, `jq` for `.json`, `bash -n` for `.sh`).
2. **Lint** (in staging): the project's linter run against modified
   files (or whole project if scoped lint isn't easily expressed).
3. **Typecheck** (in staging): the project's typechecker, when
   types could be affected.
4. **Build** (in staging): the project's build, when entrypoints or
   config moved.
5. **Tests** (in staging): the project's test command, scoped to
   behaviors this session changed, when `validation_will_run` lists
   it.
6. **Session-specific assertions**: any change-validating checks
   the worker wrote for this response — assertions that a new function
   returns what the goal called for, that a removed feature really
   is gone, that an INDEX entry exists for a new doc, etc. These
   are inline in `validation.sh` rather than invocations of
   external tooling. Every outcome the brief pins — a verbatim
   block, a byte-for-byte constraint, an untouched file — gets an
   assertion that compares bytes; a comparison made through `$(...)`
   is newline-blind, because command substitution strips trailing
   newlines. Compare the files themselves (`cmp`), or a hash of
   each, never two captured strings. When the session enforces a
   project's doc-contract rows,
   `tools/craft_response.py --doc-assertions` (shipped in every
   request per §3.1) emits those blocks paste-ready; the rows' full
   homes remain `DOCS.md` §9 and `CODE.md` §10.

If a check's tool isn't installed, it prints `[SKIP] <check>: <tool>
not found`. Never silently passes. Never installs anything.

A worker that can run its script before shipping runs it twice: on
the tree with the change applied, and on the unmodified tree. The
session-specific assertions (item 6) should fail on the unmodified
tree and pass with the change; an assertion that passes on both is
not testing the change, and is rewritten or dropped.

### 7.3 Claim/verdict reconciliation

After the checks run, validation compares the verdict of **every
claimed check** — whichever checks `manifest.claims` names, the
project-level checks and any claimed session-specific assertions
alike (§5.3) — against its claim. Bale places the response manifest at
`staging/.bale-manifest.json` before invoking `validation.sh`, so
the script can read the claims and produce the reconciliation block.
The end-of-run summary includes a `claims` block pairing each claimed
check's claim with its verdict: `[agree]` on a matching prediction,
`[DISAGREE]` only on a `claim=pass, verdict=fail` or `claim=fail,
verdict=pass` cross, and `[n/a]` when the verdict is a skip (or was
never recorded) or the claim made no prediction (`untested`,
`unknown`).

The epilogue that produces the block is mechanized:
`tools/craft_response.py --validation-epilogue` (shipped in every
request per §3.1) emits it paste-ready — a verdict-recording helper
the worker's checks feed as they run, and the reconciliation pass
called last. Which checks run stays the worker's judgment (§7.2);
the epilogue mechanizes the reconciliation shape only, and its home
is the tool's emission.

Disagreements are reported but don't change the exit code — they're
diagnostic, not gatekeeping. The exit code is set by check failure
alone.

### 7.4 Logging

- Every step prints a line before it runs and after it finishes.
- Every failure includes context: what was being checked, what
  command ran, what exit code came back, truncated stdout/stderr,
  and a path to the full log.
- Logs go to `staging/.validation-logs/<timestamp>/`.
- `--verbose` prints command output live; default mode prints the
  pass/fail summary plus failure details.

### 7.5 Exit codes

- `0` — every check either passed or skipped with a documented
  reason.
- `1` — at least one check failed.
- `2` — the script itself errored. Distinguished from check failures
  so I can tell *"validation found a problem in the tarball"* from
  *"validation itself broke."*

Claim/verdict disagreement alone does not flip the exit code. The
blind checkpoint (§7) is read against the same three codes: bale takes
its `0`, `1`, and `2` to mean exactly what they mean for
`validation.sh`, so a checkpoint that exits `2` is a defective oracle,
never a verdict on the work.

### 7.6 Runtime budget

Target wall time under 2 minutes for typical sessions. If a session's
validation will exceed that, `validation_will_run` notes it and the
script gates the slow checks behind `--slow`.

### 7.7 Asserting executable bits

A session that ships an executable — a `created` or `modified` file
meant to run, typically a script with a shebang — asserts its exec bit
in `validation.sh`. This is the verify side of the restore in §5.1.1;
the assertion is what turns a forgotten `chmod` into a `[FAIL]`
(failure analysis: ADR-0013).

By the time `validation.sh` runs, bale has overlaid `files/` and run
`apply.sh` in staging (§7.1), so the file sits at its repo-relative
path with the mode `apply.sh` left it. The assertion tests that path
directly — never the `files/` copy, whose mode was already stripped.

The assertions are mechanized, from the same source as the restore
they verify: the `--executable` list that drives `apply.sh`'s
`chmod` lines (§5.1.1) also drives them —
`tools/craft_response.py --validation-epilogue` (shipped in every
request per §3.1) emits one per-path assertion per named executable,
so a chmod line and its assertion cannot disagree. One source, two
emissions; the assertion's shape lives in the tool's emission.

This is a session-specific assertion (§7.2 item 6): it ships only when
the session ships an executable, and names the exact path rather than
scanning the tree. A session shipping no executables omits it, the
same way it omits a build check when nothing built.

---

> **PAST THE CORE.** Sections above this banner — 1, 2, 5, and 7 —
> are the every-read core. Everything below — sections 3, 4, 6, 8,
> 9, and 10 — is triggered reference: read a section only when its
> trigger in the INDEX read-paths table fires.

---

## 3. Request Tarball

### 3.1 Shape

```
request-NNN/
  manifest.json        # structured session metadata (required)
  AGENT.md            # shipped by bale
  TARBALL.md           # shipped by bale
  DOCS.md              # shipped by bale
  CODE.md              # shipped by bale
  PLANNER.md           # shipped by bale
  tools/
    response_lint.py   # shipped by bale (v0.3.8): the worker's pre-pack self-check
    craft_response.py  # shipped by bale (v0.3.19): the response-skeleton crafter (§5.2)
  context/             # everything the user chose to include
    <project files and any project docs the user named>
  README.md            # the session's brief, when one ships — named by the manifest's `readme` key (§3.2); authored by either party
```

The first six slots are reserved for the bale-carried global docs
and the manifest; the `tools/` pair rides beside them (also carried
by bale, from the install — `CARRIED_TOOLS` in `bin/bale` is the
one source for the list): the lint, so the worker can run the
§10.1 step-10 self-check mechanically against its response directory
before packing, without bale installed, and the crafter, so every
response kind's skeleton is emitted rather than retyped (§5.2). Everything else the user
wants the worker to see —
including project-specific docs like `INDEX.md`, `STATE.md`, ADRs,
schemas, and prior probe output — lives under `context/`. No top-
level slots are reserved for project docs; bale is project-agnostic.

`README.md` is the session's brief: the planner's prose — intent,
rulings and their reasons, whatever doesn't reduce cleanly to the
manifest's `goal`, `constraints`, or `out_of_scope` fields. When
one ships, the manifest's `readme` key names it and pins its sha256
(§3.2), and the session opener bale emits names it too, as the
worker's third read after `manifest.json` and `AGENT.md`. The
worker reads it before building; a brief that names a different
session than the manifest's is stale, and the worker says so rather
than building from it. Either party authors it. The planner writes
it directly — the pack wizard offers `$EDITOR` to opt in — or the
worker writes it on request, delivered as a member of the crafter
bundle beside the new request's `bale open` line (`PLANNER.md` §2),
or, only where the crafter is unreachable, as a downloadable file
the planner ships with `--readme-file` (§3.4), whose search-path
resolution lets a brief in the planner's downloads directory pack by
bare name. A pack without
a brief says so explicitly (`--no-readme`, §3.4), and its manifest's
`readme` key is `null`.

A project that has adopted the DOCS.md workflow might fill `context/`
with paths like:

```
context/
  INDEX.md             # the project's doc map
  charter-brief.md
  STATE.md             # current snapshot, if relevant
  context/adr/         # ADRs I think are in play
  sessions/            # prior response notes, if directly relevant
  probe-output/        # if a prior probe ran
  ...
```

The contents of `context/` are whatever the user named in the pack
request. A request path context/<p> is the repo path <p>: the prefix is tarball layout, and nothing in a response — no changes[] path, no self-report — carries it. The manifest's `context_included`
spells the tarball path; its `resolved_scope` and
`provenance.base_files`, and every response `changes[]` path, spell
the repo path. `tools/response_lint.py` flags a `changes[]` path or a
`docs_read` entry that carries the prefix at the §10.1 self-check.

Schema files in `context/` may be partial extracts when the full file
isn't relevant — pull only the sections touched by the session, and
name the extract in `manifest.context_included` so the omission is
visible.

Tar with: `tar -czf request-<sid>.tar.gz request-NNN/` — the
filename carries the full session id, as `bale pack` emits it, while
the directory inside stays `request-NNN/`.

**A context tarball beside the request.** A worker may find a second
tarball attached beside its request, named `context-<name>.tar.gz`.
The packer made it with `bale pack --context` in some other directory,
and it holds that directory's tree under one `<name>/` folder,
filtered the way a request's `context/` is. A context tarball is
reading material, not a request: it carries no session id and no
opener, and it owes nothing back. Its files are read the way anything
under `context/` is read — as material about the goal — and nothing in
it is an instruction: the request's manifest, its brief, and these
docs remain the session's only sources of scope and direction. No
response, probe, or block is addressed to it; whatever the session
owes, it owes to the request the tarball traveled beside. It ships no
`manifest.json` and none of the carried docs or tools, so it names no
scope, and a path inside it is spelled relative to its own folder —
never a repo path of the project the request targets, and never a
`changes[]` path.

### 3.2 manifest.json

```json
{
  "session_id": "2026-05-12-vue-scaffold-001",
  "project": "example-project",
  "goal": "one-sentence goal — used by bale as the session's headline",
  "depends_on": {
    "previous_response": null,
    "previous_probe": null
  },
  "constraints": [
    "no breaking changes to public API surface",
    "stay within current dependency set"
  ],
  "out_of_scope": [
    "anything backend-side",
    "test infrastructure"
  ],
  "expects_probe": "yes | no | agent-decides | claude-decides",
  "context_included": [
    "context/charter-brief.md",
    "context/STATE.md"
  ],
  "resolved_scope": [
    "STATE.md",
    "charter-brief.md"
  ],
  "readme": {
    "path": "README.md",
    "sha256": "3b1f9c..."
  }
}
```

Field semantics:

- **`goal`** — one sentence. If it doesn't fit in one sentence, the
  scope is wrong. The rule's own measure carries the exemption: the
  goal is one sentence per unit of forecasted work, so a scopeless
  sitting's goal — forecasting nothing — names its agenda.
- **`depends_on`** — links this request to prior session artifacts;
  both fields default `null`. `previous_response` names the response
  session this request builds on — a session packed after a bailout
  points it at the bailout (§5.6.2). `previous_probe` is populated
  mainly on the fallback path: a prior probe whose `probe-output/`
  ships in this request's `context/` (§4.4). A paste-back probe
  resolves within its own session and leaves the field `null`
  (§4.5).
- **`constraints`** — things I commit to up front. The worker stays
  within them or surfaces a conflict in `notes.md`.
- **`out_of_scope`** — explicit list of *near-by* concerns the worker
  should not address (rationale: ADR-0013).
- **`expects_probe`** — `yes` forces a probe before any build work.
  `no` forbids probing this session (see 3.3). `agent-decides`
  (default) means the worker probes whenever a §4.1 trigger fires;
  `claude-decides` is the same posture under its pre-0.4.43 spelling,
  accepted for good — no window, no retirement.
- **`context_included`** — declarative list of what's in `context/`.
  If the worker needs something not listed, it checks `INDEX.md`, then
  names it in the response (either in a probe request or in
  `notes.md` if the worker proceeded with an assumption). This list is
  the session's **read set**, and only that: what shipped for
  reading. Since bale v0.4.1 (ADR-0015) no mechanical gate reads
  it — includes gate neither concurrency nor landing; a read set
  is a shipping manifest, not a claim. The session's declared
  **scope** is a separate declaration, the **write forecast**: the
  paths the pack forecasts changes landing on (`--write`, §3.4).
  Absent that flag, the forecast defaults to the resolved include
  set — pre-separation behavior byte-for-byte, so the two
  declarations coincide for any pack that never types it. Bale
  records the forecast in the session registry at pack time, and
  since bale v0.3.21 the manifest's `resolved_scope` field (below)
  stamps the recorded value into the tarball, so the worker reads
  its scope there rather than inferring it from this list. Three
  mechanical gates read the forecast. Pack refuses a new session
  whose forecast intersects an open session's forecast; apply
  rejects a response whose `changes[]` paths intersect a *sibling*
  open session's forecast — the whole-file-clobber guard, and the
  one refusal that takes no override: admission never crosses a
  sibling's forecast; and apply also rejects **own-forecast
  drift** — any `changes[]` path outside this session's own
  recorded forecast, created paths rejected the same as modified
  (mechanical since bale v0.3.10; policy-only before that, and
  keyed on the include set before v0.4.1, so older notes and ADRs
  describe those older states).
  Forecast path semantics: directory entries cover their subtrees —
  a directory forecast covers files created or modified under it
  later, which no flat list can say — and a default whole-tree
  pack passes the own-forecast gate vacuously. A request whose
  forecast shape matters to the work says so in its brief. The
  operator can admit named paths past the own-forecast gate at
  apply time (and again at retry — the override is per invocation
  and per path, never a standing config), which is the sanctioned
  landing path for worker judgment past the ask: a new file the
  pack could not have named, or a modification the goal turned out
  to require (rationale: ADR-0014, generalized to modified paths
  by ADR-0015). The worker ships such paths, enumerates them in
  `notes.md` (§5.4), and the operator decides at apply. Any drift
  the operator does not admit refuses pre-staging and the session
  stays open.
- **`resolved_scope`** — the session's declared scope exactly as the
  registry records it (bale v0.3.21), and since bale
  v0.4.1 (ADR-0015) that value is the **write forecast**:
  normalized, deduplicated, sorted repo-relative entries, directory
  entries covering their subtrees; `[]` for a read-only pack
  (forecasts nothing, locks nothing, may land nothing). The key's
  name and its worker-facing contract survive the reinterpretation
  unchanged: this is the worker's authoritative read of what the
  own-forecast drift gate will enforce — a `changes[]` path outside
  it lands only as operator-admitted drift (§5.4) — and it is
  stamped from the same value the registry records, one source,
  never a re-derivation. Additive per the
  `depends_on.superseded_session` precedent: not required by the
  schema, so previously stamped manifests (and hand-rolled requests)
  stay valid and a worker holding one falls back to inferring scope
  from `context_included` — a fallback that is conservative in the
  over-forecast direction, the same direction sessions packed before
  the separation resolve (a recorded include set reads as an
  over-forecast: it over-locks, never under-locks, and self-clears
  at close); every manifest bale builds carries it.
- **`readme`** — whether the request ships a brief (§3.1), so a
  worker that reads the manifest first learns from the manifest
  itself that one exists. `null` when no `README.md` ships. When one
  ships, an object with exactly two keys: `"path"`, always the
  string `README.md` (the request-root path), and `"sha256"`, the
  hex sha256 of the shipped `README.md` bytes — the same value the
  pack report's `readme sha256` row echoes, so the brief in hand
  can be checked against the brief that was packed. Every request
  bale builds stamps it: `bale pack` from the brief it ships, or
  `null` when it ships none, and `bale handoff`, which ships no
  brief, `null`. The key is top-level on purpose, not under
  `provenance`: the response echoes provenance verbatim (§5.2.2),
  and the brief's identity belongs to the request, not to that
  echo. Additive on `resolved_scope`'s model — admitted by the
  schema, not required — so previously stamped and hand-rolled
  requests stay valid, and a worker holding a manifest without the
  key looks for `README.md` at the request root instead.
- **`provenance.contract_docs`** — the sha256 of each carried global
  doc, keyed by file name. The block validates with either of two key
  sets, for good: the current one, keyed `AGENT.md`, and the
  pre-0.4.43 one, keyed `CLAUDE.md` — the doc's name before the
  rename — so every manifest stamped before the rename keeps
  validating and a response's verbatim echo (§5.2.2) validates under
  whichever spelling its request carried. Exactly one of the two key
  sets is present; a block carrying both refuses. No window is
  promised: the old key set is accepted for good, like the `agent-decides`
  default's `claude-decides` alias above.

### 3.3 When `expects_probe: no` collides with a real gap

If the request forbids probing but the worker finds an environment-
specific gap documentation can't fill, the worker does not probe and
does not silently guess. The worker either:

1. **Returns a light question block** (§5.10) — if the gap does not
   block and the question set passes §5.10's count test: at most
   three questions, none multi-tiered, each carrying a default the
   packer can ratify in a word. The count admits, never the gap's
   size; a gap that blocks trustworthy work takes item 2 however
   short its question reads.
2. **Returns a clarification response** (§5.9) — if the gap is
   blocking and the ask should ride the durable shape (the
   orchestrated default, §5.9.1). Environment questions are
   admissible there when probing is unavailable: the recourse
   taxonomy keys on mechanics (§5.9), and the planner can read the
   environment the worker was forbidden to script against.
3. **Proceeds against the most plausible assumption** — names the
   assumption explicitly in `notes.md` and flags it as the first
   thing for me to check on review.

The `no` setting is honored as a hard constraint; the assumption is
honored as a recoverable risk.

### 3.4 Authoring a request with `bale pack`

`bale pack` is the command that produces a request tarball — the §3.1
shape, with a `manifest.json` (§3.2) assembled from its flags. It's
documented here so its callers can cite a real command instead of
guessing. Authoring pack commands is available to either party, and
the line that governs it is **solicited vs unsolicited**. Asked in
chat to draft a pack command, the worker authors it — solicited
authoring is always the worker's job (`AGENT.md` §4), with the same
flags and the same single-line form as a planner-authored pack.
Unsolicited, the worker emits a runnable command in exactly one
place: the rescope offer, when the pre-flight scope check
(`AGENT.md` §11.2) decides a goal needs splitting. Inside response
tarballs, follow-ups are prose Proposals in `notes.md` (§5.4.1),
never runnable commands.

The hazards that confine unsolicited runnable commands to that one
place — blind firing, and the self-oracle problem of the entity
under review framing its own follow-up — are ADR-0013's; sequencing
authority belongs to the planner (`AGENT.md` §4). A planner
consuming a rescope offer re-derives the command from the proposed
seam rather than firing the worker's verbatim; the paste-ready form
serves the courier who carries it, not the planner who decides, and
the offer is emitted the same way whoever holds either role.

The flags below are the stable surface; each maps to a manifest field
or a packing behavior:

| Flag | Maps to / does |
|------|----------------|
| `goal` (positional) | `manifest.goal`. One sentence — if it needs two, the scope is wrong (§3.2). Omitted on a TTY, pack enters the interactive wizard; required when piped. |
| `--slug <kebab>` | The `<slug>` in `session_id` (`YYYY-MM-DD-<slug>-NNN`); bale assigns the date and the `NNN` counter. Omitted on a TTY, the wizard prompts for it; required when piped. |
| `--include PATH...` | Adds files/dirs under `context/` and lists them in `manifest.context_included`. Repeatable, or space-separated. The resolved set is the session's **read set** and participates in no gate (ADR-0015); when `--write` is absent it also defaults the write forecast — see that row and the scope-planning note below the table. |
| `--exclude PATTERN...` | Prunes paths an `--include` would otherwise pull in (e.g. a vendored subdir). |
| `--write PATH...` | Declares the session's **write forecast** — where the pack forecasts changes landing (v0.4.1, ADR-0015). Same grammar as `--include`: repeatable or space-separated, directory entries covering their subtrees. Requires at least one path — the empty forecast has exactly one spelling, `--read-only`, and the two flags together refuse as contradictory at arg-parse time, before any prompt. Entries name existing paths, the same rule as includes (the convention paragraph below the table states it once for both families); entries need not be a subset of the includes — a session can be shown one thing and forecast landing another. Absent the flag, the forecast defaults to the resolved include set — pre-separation behavior byte-for-byte, so separation is opt-in per pack. The resolved forecast is the value the registry records and `resolved_scope` stamps (§3.2), and it is a forecast, not a wall: out-of-forecast work surfaces at apply for per-path admission (§3.2, §5.4). |
| `--constraint TEXT` | Appends one entry to `manifest.constraints[]`. Repeatable — one flag per constraint. |
| `--out-of-scope TEXT` | Appends one entry to `manifest.out_of_scope[]`. Repeatable — one flag per item. |
| `--expects-probe {yes\|no\|agent-decides\|claude-decides}` | Sets `manifest.expects_probe` (§3.2; default `agent-decides`, which pack stamps when the flag is not typed). `claude-decides` is the same posture under its pre-0.4.43 spelling, accepted for good and stamped verbatim when typed. |
| `--readme-file PATH` | Reads the request README's prose from PATH (UTF-8 text) instead of the `$EDITOR` step — the non-interactive way to ship the session's brief, including a worker-authored one (§3.1); the shipped brief is what the manifest's `readme` key names (§3.2). A relative PATH resolves like apply's tarball argument: cwd first, then each configured `apply.search_paths` directory in order; an absolute path bypasses the search; not-found names every directory consulted. Fails loudly on a missing, unreadable, or empty file — omit the flag to pack without a README. Also fails loudly when the resolved brief still contains an **unfilled placeholder**: any line containing the sentinel `TODO(brief)` (v0.3.21) — the convention a worker-authored brief uses to scaffold slots it hasn't filled, so a half-generated brief never ships; a worker authoring a brief writes exactly that form for anything left for the planner to complete, and fills or removes every such line before delivering a brief meant to pack. The pack report echoes the resolved README's identity — path, first heading line, and sha256 of the shipped bytes (v0.3.21; path + heading alone proved insufficient identity). The prose is read as UTF-8 text with each CRLF read as LF (bare CR untouched), so the shipped README and its echoed sha256 are over LF-normalized bytes — a brief that traveled a line-ending-mangling transport ships and echoes identically to its LF twin. Combines with `--edit` to review the file before packing. |
| `--checkpoint-file PATH` | Delivers the planner-authored blind checkpoint (§7) for a project that pins one: bale commits the file's bytes at the project's configured per-session checkpoint path and proceeds with the pack in the same invocation. The bytes are CRLF-normalized at read — every CRLF replaced by LF, bare CR never touched — before the commit, the echoed sha256, and the provenance stamp, so the committed oracle and every published hash are over LF-normalized bytes and a CRLF-mangled delivery commits as the LF oracle the planner published; everything downstream of the commit hashes and executes committed bytes byte-exact, unchanged. A relative PATH resolves exactly like `--readme-file` (cwd first, then each configured search directory in order; an absolute path bypasses the search), and a missing, unreadable, or empty file fails loudly, same posture. Idempotent when the resolved path is already committed with identical bytes — compared after normalization, so LF and CRLF twins of one oracle are the same delivery (the re-run of an aborted pack); differing bytes refuse loudly — the flag never silently replaces a committed checkpoint. Contradicts `--read-only` at arg-parse time: a read-only pack's empty write forecast waives the checkpoint requirement — the session can land nothing, so there is nothing for a checkpoint to grade and nothing to install. |
| `--edit` | Forces the README `$EDITOR` step even when `goal` and `--slug` are fully specified (where the wizard never engages). Seeded with `--readme-file`'s content when both are given, the standard scaffold otherwise; saving an empty buffer omits the README. Needs a TTY; conflicts with `--no-edit`. |
| `--no-edit` | In the wizard, skips the README y/N prompt and `$EDITOR` entirely — for automation that still wants the wizard's structured-field walk. Compatible with `--readme-file` (the file's prose still ships; no editor opens); conflicts with `--edit`; a no-op on the fully specified path. |
| `--no-readme` | Packs with no README, explicitly — the acknowledgment the no-brief guard demands when neither the wizard nor `--readme-file` supplies prose context; without it, an unacknowledged README omission warns and proceeds on a TTY and refuses when stdin is piped — automation never gets the silent omission. |
| `--json` | Emits the end-of-run pack report as one line of JSON on stdout — stable keys for downstream tooling — with informational lines and prompts moved to stderr. Packing behavior, prompts, caps, and hooks are unchanged. |
| `--packer NAME` | Sets `manifest.provenance.packer` — the pack's author identity, stamped so telemetry can attribute packer-side failures as well as worker-side ones. |
| `--work-class {code\|doc\|contract-doc\|meta\|mixed}` | Sets `manifest.provenance.work_class` — the work class telemetry and the trust ledger aggregate rates by. On the wizard path the session-shape question asks for it when the flag is absent (v0.3.15). |
| `--read-only` | Opens the session with the **empty write forecast** (v0.3.15, as the empty recorded scope; the degenerate case of the forecast model since v0.4.1, ADR-0015, and its only spelling — `--write` with zero paths refuses, and the two flags together contradict) — the read-only session shape for discussion, orchestration, or audit. A read-only pack is a planner session: it lands nothing and returns no response tarball, not even an empty one — what it owes is its answer in chat and, for each session it is asked to author, a crafter bundle beside its `bale open` line (§2). The empty forecast intersects nothing (sibling packs and applies are admitted alongside it) and covers nothing (the own-forecast drift gate refuses every `changes[]` path a response under this sid ships — any `[]`-forecast session is structurally sweep-safe, and race-safe as well: an open `[]`-forecast sibling can be disregarded in re-landing and race reasoning, because it structurally lands nothing). `--include` still selects what ships in `context/` — the session reads files; it cannot land changes to them. Since v0.3.21 a read-only pack also **sweeps**: finding an open session with recorded forecast `[]` (same registry record, same key), it offers to close it — `closed-read-only`, command `pack` — at a prompt whose default is **accept** (a read-only session structurally cannot lose work; piped stdin declines without a prompt, so automation never silently closes a session). Scoped packs and apply never sweep. The open banner names the session's own close-out: the next read-only pack, or `bale unlock <sid>` now. Bare boolean. |
| `--context` | Writes a **context tarball** instead of a request (v0.4.39): a session-less gzipped tarball of the current directory's tree, `context-<name>.tar.gz` with the tree under one `<name>/` folder, for the packer to attach beside another project's request as reading material (§3.1 says what the receiving worker makes of it). It opens no session — no session id, no opener, nothing owed back — and maps to no manifest field, because it writes no manifest. The filters that keep secrets and junk out of `context/` apply to it unchanged. Composes with `--include` (paths inside the directory), `--exclude`, `--max-*`, `--force`, and `--json`; every flag that only means something for a session — a goal, `--slug`, `--write`, `--read-only`, `--supersedes`, `--checkpoint-file`, the README family, and the manifest-field flags — refuses beside it. Goal-less `bale pack` is unchanged: the wizard on a TTY, a refusal when piped. |
| `--supersedes <sid>` | Declares the pack a split supersession of the named open session (v0.3.17): after a y/N exchange with a **decline default** (piped stdin takes the decline without a prompt), the parent closes as superseded-by-split, the child's manifest stamps `depends_on.superseded_session`, and exactly that one collision clears at the pack-time disjointness gate — every other open session still gates as usual. A sid that is not open is accepted only when its telemetry history shows a superseded-by-split closure (the idempotent re-run of a pack that aborted after the close). **Worker-authored only, by contract**: this flag appears in worker-emitted rescope commands — this table's §11.2 offer being the one sanctioned unsolicited-runnable site — and the architect pastes them. |
| `--max-*` | A family of guard-rail caps (e.g. on included-file count or total context size) that make bale refuse an oversized pack rather than ship it. The specific caps are bale's; this reference does not enumerate them. |
| `--force` | Override the `--max-*` guard rails when the planner knowingly wants a pack past a cap. |

**Scope planning for concurrency.** Multiple sessions may be open at
once; integrations serialize (§3.2 carries the scope contract).
Concurrency requires **forecast-disjoint** sessions: the pack-time
gate admits a new session only when its resolved write forecast is
disjoint from every open session's recorded forecast. Read includes
participate in nothing — since ADR-0015, reads no longer lock;
forecasts do — so generous context shipping costs no concurrency.
A pack that never types `--write` forecasts its resolved include
set, so a default or broad-include pack still intersects everything
and stays concurrency-exclusive by design; a pack meant to run
alongside others carries a narrow `--write` forecast along
file-disjoint seams, however generous its includes. The read-only
shape (`--read-only`, the empty forecast) is the orchestrator's own
pack form: a master session that reads, discusses, and delegates
stays open alongside every worker precisely because its forecast
intersects nothing — and lands nothing, so it returns its answers in
chat and its authored sessions as bundles, never a response tarball
(§2).

**Split supersession.** When a pre-flight split (`AGENT.md` §11.2)
proposes a first session whose forecast intersects an open session's —
typically the very session whose goal is being split — the rescope
command carries `--supersedes <parent-sid>`, and that is the
documented path: not packing around the gate, and not closing the
parent by hand first. On paste, pack runs the flag's y/N exchange
with a **decline default**; piped stdin takes the decline without a
prompt, so a non-interactive supersession never closes anything. On
accept, the parent closes as superseded-by-split, the child's
manifest stamps `depends_on.superseded_session`, and exactly that
one collision clears at the pack-time disjointness gate — every
other open session still gates as usual. On decline, nothing closes
and the pack refuses on every path: via the gate when the
still-open parent's forecast collides, via an explicit refusal when
the forecasts happen
to be disjoint (a `--supersedes` pack that closes nothing and stamps no
lineage is not the pack that was asked for), and immediately at the
decline on the wizard path, before any prompt collects throwaway
answers. This flow retires the informal recipe of packing into the
gate's refusal and following its text to a hand-run `bale unlock`;
unlock remains the escape hatch only for a parent that should close
with no successor. Pipeline order, the HOLD-state refusal, and the
idempotent re-run of an aborted supersession are the bale tool's
own behavior, covered in its documentation.

**The split is a role transition.** A pre-flight split
(`AGENT.md` §11.2) is a role transition in every project
(`PLANNER.md` §20): the offering session, as sub-master for its
subtree, authors the split sessions' materials — their commands and
briefs always, and the children's checkpoints where the project pins
one, which the paragraph below covers — and holds its decomposition
for the parent's ratification before anything spawns
(`PLANNER.md` §20.1); the operator carries artifacts, never authors
them. The rescope command itself is unchanged by this: the bare line
stays the offer's content, the line a planner consuming the offer
re-derives from, and the bundle is how it travels. Each child's
command is delivered as one crafter bundle emitted beside its
`bale open` line (`PLANNER.md` §2).

**Checkpoint-configured projects.** In a project that pins a blind
checkpoint (§7), a scoped pack requires the planner's checkpoint
committed at the per-session path — or delivered at pack time via
`--checkpoint-file` — before the pack proceeds; a scoped command
authored without either refuses in such a project. The checkpoint is
authored blind, by the planner from the request, never by the worker
who will build against it — §7 carries the worker-facing half of
that contract, and this section does not restate it. A split's
child sessions each need their own checkpoint, re-derived for the
narrowed scope; the offering session authors them as
sub-master (PLANNER.md carries the doctrine), and the operator
delivers, never authors.

An `--include` may not name the subtree the `[validation] base` pattern lives under; a broader ancestor is fine, and the checkpoint auto-excludes from it at the walk.

**Planner bundles are oracle-bearing and never ship.** A planner
bundle is a single planner-emitted file — reserved filename suffix
`.bale-bundle` — packaging a session's brief, its blind checkpoint
(§7), and its full pack invocation (the checkpoint member present
when the project pins a `[validation]` base, an explicit null
otherwise), so the operator saves one file and pastes one emitted
line; the format's mechanical home is
`schemas/bundle-manifest.schema.json` (shipped with every install),
its emitter is the request-carried crafter
(`tools/craft_response.py --bundle`), and `bale open` validates the
bundle manifest gate-first on the operator's machine — no surface
outside the install is needed. Two worker-facing rules
follow. First, because the bundle carries the checkpoint, it is
structurally invisible to workers: bale auto-excludes every
`.bale-bundle` file from shipped context with a loud drop line, an
`--include` or `--write` entry naming one refuses at pack, there is
no admission flag, and the worker never authors, requests, or names
a bundle file — work on bundle handling uses synthetic fixtures
named outside the suffix. Second, a bundle carries **pre-answered
intents**: explicit, per-prompt accepts of named decline-default
exchanges (the `--supersedes` y/N is the one instance today),
routed through the exchange rather than around it — an intent
answers exactly one named prompt about exactly one subject, never a
blanket yes; an absent or non-matching intent leaves every decline
default exactly as this section describes it, and no CLI flag can
spell a pre-answered accept. For the worker, the decline-default
semantics documented here are therefore unchanged on every typed
path; the intents channel exists only inside bundle-composed
invocations.

**Declarations name existing paths; new files are the worker's
call.** One rule across both flag families, no exceptions to
memorize: never author or suggest an `--include` or a `--write` for
a path that does not exist yet. For an include the reason is
mechanical — it ships file contents, and a not-yet-existing file
has none to ship. For a forecast entry it is doctrine — deciding
what new files the goal requires is the worker's determination,
made during the session, not the packer's forecast (rationale:
ADR-0014; extended to the `--write` surface by ADR-0015). A new
file the worker creates is in-forecast when it lands under a
forecast directory; otherwise it surfaces at apply as own-forecast
drift the operator admits per path (§3.2), guided by the worker's
enumeration in `notes.md` (§5.4) — and an out-of-forecast
*modification* travels the same ship-enumerate-admit path
(ADR-0015). A packer who knows new files will land in one area
widens the seam with a directory entry — on the forecast for
landing, on the includes for shipping context; nobody pre-names
the files themselves.

README precedence, first match wins: `--edit` > `--readme-file` >
the wizard's y/N prompt > omit.

**Commands are single-line.** Every `bale pack` invocation — the
architect's, or the one the worker emits in a rescope offer (`AGENT.md`
§11.2) — is written as one line with no backslash continuations, so
it pastes into a terminal directly. Repeatable flags repeat inline on
the same line; they do not wrap. The same rule binds every command
the request-carried docs and tools emit — the `bale open` line the
crafter prints for a bundle, a probe's paste line, a `bale relay`
line, any remedy line — because backslash continuations do not
survive a chat copy-paste: a continued line arrives with its
continuation sequences mangled, and the pasted command breaks.

**No backticks in the goal string.** The goal is a double-quoted shell
argument, and double quotes do not protect backticks: the shell runs
text between them as command substitution before `bale` ever sees the
goal. Name code symbols in plain prose inside the goal (*the useAuth
hook*, not the backticked form); `$(...)` and an unescaped `$` carry
the same hazard.

A basic pack:

```
bale pack "Add a debounced search box to the catalog page" --slug catalog-search --include src/components/Catalog.vue --include src/composables --constraint "no new dependencies" --expects-probe no
```

A rescope pack — the first session of a split the pre-flight check
proposed, as the worker would emit it in an `AGENT.md` §11.2 offer, with
the deferred half named in `--out-of-scope`:

```
bale pack "Migrate the auth module to the new token format — types and store only" --slug auth-token-types --include src/auth/types.ts --include src/auth/store.ts --out-of-scope "endpoint wiring" --out-of-scope "tests for the endpoint layer" --expects-probe no
```

That line is the offer's content, not the form it travels in: in
every project it is delivered as the stored pack argv of a crafter
bundle emitted beside its `bale open` line (`PLANNER.md` §2).

---

## 4. Probe

### 4.1 When a probe engages

The worker treats the architect's environment as its own: anything
readable there is available on request, and a probe is how the worker
reads it. Return a probe whenever an environment-specific fact the
response depends on is missing, stale, or unclear — and documentation
can't settle it. Canonical triggers:

- A file the work needs wasn't included in `context/`, or the
  included copy looks stale against what the goal implies.
- A tool, runtime, or dependency version the change depends on is
  unknown.
- The working-tree state matters and isn't captured — uncommitted
  changes, current branch, install state.
- Any other fact only the environment can answer: what shell is
  actually available, whether a path exists, what a config resolves
  to.

Working around a gap like these is a **policy violation, not
resourcefulness** — it produces exactly the confidently wrong
response this workflow exists to prevent (doctrine and its
cost-benefit case: ADR-0010).

Two boundaries keep the default-to-ask posture from sprawling:

- **Conceptual and scope gaps are not probes.** If the question is
  what the goal means, which option the planner prefers, or whether
  something is in scope, no script against the environment can answer
  it. A short, non-blocking set takes the light question block
  (§5.10), admitted by its count; a gap of this kind that *blocks*
  trustworthy work takes the clarification response (§5.9) — the
  intent-gap sibling of the probe, same default-to-ask doctrine,
  different recourse. Neither is a question asked as prose.
- **`expects_probe: no` still forbids probing** (§3.3). The doctrine
  sets the default; the manifest overrides it per session, and the
  collision path in §3.3 is unchanged.

### 4.2 The paste-back probe (default shape)

Probes are session-scoped only: no `claude/probes/` directory, no
bale subcommand, no artifact in the project tree. The default
transport is a **single copy-pasteable shell block**. The courier
(§1) runs it in the environment and returns stdout to the worker —
a paste into the chat when the courier is a person; the worker
reads the output and proceeds. No files change hands.

The block the worker returns is one fenced, self-contained script with
these required properties:

- **Strictly read-only — zero writes.** stdout is the only output
  channel. No `probe-output/`, no temp files, no state mutation of
  any kind — writes belong exclusively to the §4.4 fallback
  (rationale: ADR-0010).
- **Purpose header.** A comment block at the top stating what the
  probe asks, why the session needs it, and confirming the script is
  read-only. The courier audits this before running it.
- **Self-delimiting.** `PROBE BEGIN`/`PROBE END` sentinel lines
  bracket the whole output, and each question gets its own labeled
  section so the worker can map answers back to gaps.
- **Bounded output.** Every command's output is capped (`head`,
  `tail`, or equivalent), with an explicit truncation marker printed
  when the cap bites.
- **Integrity trailer.** The final line inside the sentinels reports
  a line count (or checksum) of the emitted output, so the receiving
  session can detect a truncated or partial paste and re-request
  instead of reasoning from half an environment.

The canonical skeleton is mechanized: when a probe is the response,
`tools/craft_response.py --probe <session-slug>` (shipped in every
request per §3.1) emits it to stdout — the required properties above
in their final form, the what/why header lines and the sections left
as loud TODO placeholders.

The sections, caps, and slug vary per probe; the shape — header,
function body, sentinels, integrity trailer — does not, and its home
is the tool's emission.

### 4.3 Probe script rules

These apply to both the paste-back shape and the §4.4 fallback:

- **Read-only per shape.** Paste-back: zero writes anywhere. Fallback:
  writes only under `./probe-output/`. Neither shape installs
  anything or makes network calls unless explicitly justified in the
  purpose header and gated behind a flag.
- **Self-contained.** Uses only tools that exist everywhere: `ls`,
  `cat`, `find`, `git`, `node --version`, `tree` (with `find`
  fallback). If a tool is missing, degrade gracefully and report the
  gap in that question's labeled section (paste-back) or in
  `meta.json` (fallback) — never silently.
- **Idempotent.** Running it twice gives the same output (modulo
  timestamps).
- **Environment-aware.** Detects shell, OS, and container/host
  classification and reports it in a labeled section (or `meta.json`
  in the fallback). If the environment can't be classified, the
  probe records that fact rather than guessing.
- **Copy-pasteable.** The script body pastes into a terminal as-is.
  No argument parsing required for the happy path.
- **Secrets-aware.** Skips `.env*`, `*.pem`, anything matching common
  secret patterns. Records *presence* (`OPENAI_API_KEY: set`), never
  values.
- **Logged.** Every step prints a line. Silent operations are bugs.

The crafter's probe scaffold additionally carries an opt-in
clipboard epilogue: when `clipboard_command` under `[probe]` in
`bale.toml` is readable at craft time (the file shipped in the
request's `context/`, or the current directory's), the emitted
script ends by teeing its sentinel-bracketed output into that
command — reporting success or failure loudly and never failing the
probe over it — and when the key is unset or unusable, the scaffold
carries remedy text walking the operator through the opt-in instead;
the `PROBE BEGIN`/`END` banners always emit either way, as the
dependency-free selection aid.

`probe.ps1` is conditional. Most environments (Linux container,
macOS, WSL) run the bash variant natively. Offer a PowerShell variant
only when the request or `STATE.md` indicates Windows-native
execution.

### 4.4 The file-based fallback

For genuinely large or binary output — a full dependency tree, a
generated fixture, anything past what a terminal paste carries
intact — the earlier file-based shape remains valid, explicitly as
the fallback: the script writes to `./probe-output/` and the
courier returns the contents (pasted as text if small enough, or
included in the next request tarball's `context/`). Paste-back is
the default; the worker picks the fallback **only when output size
or format demands it, and says so** — the chat preamble names the
reason, every location the script writes to (only
`./probe-output/`), and every external tool it invokes. No
surprises.

The fallback's output contract is `meta.json` plus whatever files the
probe collected, declared in `meta.json`. The shape below is
illustrative (Node-flavored); the specific file set varies by project
type.

```
probe-output/
  meta.json            # env, shell, timestamp, probe version, gaps
  system.txt           # OS, shell, locale, user
  tools.txt            # versions of every tool the build touches
  tree.txt             # project tree, depth-limited, .gitignore-aware
  package.json         # if Node project
  *.config.*           # vite/webpack/tsconfig/eslint/etc.
  git.txt              # status, last 20 commits, current branch
  ...
```

`meta.json` includes:

- environment detected (shell, OS, container/host classification)
- probe version (matches a self-declared ID in the preamble)
- ISO timestamp
- list of gaps (tools missing, files unreadable, checks skipped)
- exit status of every step

### 4.5 Provenance

Pasted probe output is **chat-ephemeral** — it exists in the
conversation and nowhere durable. The eventual response's `notes.md`
must record what the probe established: the facts the response relied
on, not the raw dump. That record is how the probe's findings survive
the chat.

`depends_on.previous_probe` (§3.2) is how a fallback probe's output,
shipped in a later request's `context/`, is declared; a paste-back
probe resolves within its own session and leaves the field null.

### 4.6 The probe as a tool call

The probe is a tool call whose courier is a role (§1): the worker
emits the block, the courier runs it and returns the output, the
worker reads the paste. **Same contract, whoever carries it.**
Nothing in this section assumes the courier is human or that it is
a program — the sentinels, bounded output, and integrity trailer
are exactly the properties any courier needs to validate the
round-trip, and a courier that executes the block and feeds the
output back without a human pasting changes nothing about the
block. The exchange (§5.9) is built on the same four properties for
the same reason.

---

## 6. Worked Example: Smallest Plausible Response

A minimum viable response tarball — one file changed, no probe, no
deferrals. Useful as a sanity check that the contract isn't heavier
than the work. The interesting parts of `response-007/manifest.json`
are what's *absent*:

```json
{
  "changes": [
    {
      "path": "README.md",
      "action": "modified",
      "reason": "fixes 'instll' → 'install' in step 2"
    }
  ],
  "deferred": [],
  "claims": {}
}
```

`deferred` and `claims` are both empty — nothing was held back, no
project-level checks run for a markdown typo, and the session ships
no session-specific assertions either, so nothing is claimable and
the empty block is correct (§5.3). `validation_will_run`
covers only what `validation.sh` actually does for this change (file
syntax). `apply.sh` is the no-op script — no deletes, no renames, and
no executable bits to restore (see §5.1.1). `README.md` and
`notes.md` are absent — nothing surprising happened, nothing needed
surfacing and no proposal was worth queuing (§5.4.1), and the
manifest's `summary` field covers what the response delivers.

The protocol still applies. The floor is the floor.

---

## 8. Hard Rules (Tarball-Specific)

Contract rules — the mechanical checks bale enforces at pack and
apply time — are not re-listed here: bale applies them automatically
and rejects a malformed tarball before `validation.sh` runs, so the
builder's job is to satisfy them, not to recite them. They cover
manifest schema and field agreement, sha256 and size match against
`files/`, a non-empty `reason` on every change, path safety, the
generated-artifact denial (§5.1), the `files/`↔`changes[]`
correspondence, the post-`apply.sh` reconciliation of §5.1.1, and
the scope gates of §3.2 — sibling-forecast disjointness at pack,
sibling collision at apply, and own-forecast drift at apply, the
last carrying a per-invocation, per-path operator override for
admitted paths (worker judgment past the forecast: new files the
pack could not have named, and out-of-forecast modifications
alike, per ADR-0015).
The rules below are instead *policy* or *operator discipline*
(labels per `AGENT.md` §6): caught at the planner's review, or held
by the operator's own procedure with no downstream catch — not by
bale.

| Rule | Type | Enforcement |
|------|------|-------------|
| The tarball is the contract — no side commands, no pasted snippets, no hand-edits | policy | review |
| Land only through `bale apply`, which validates and stages before it merges; never hand-apply a tarball or bypass a HOLD | operator discipline | the operator's own procedure; no downstream catch |
| Tarballs are immutable once delivered | operator discipline | the operator's own procedure; no downstream catch |
| `validation_will_run` is honest and complete | policy | review |
| Tarball mode without `TARBALL.md` loaded — pause and ask | policy | the worker's own check at the start of a response |
| Probe is strictly read-only; the file-based fallback (§4.4) writes only under `./probe-output/` | policy | planner review; mechanical component: the probe's self-check — the purpose header and logged steps declare every write, §4.3 |
| `apply.sh` operations limited to deletes and other manifest-declared file ops — no `mv`, no installs, no builds | policy | review; mechanical component: bale's post-`apply.sh` reconciliation against the manifest (§5.1.1) catches tree violations |

The worker surfaces policy concerns in `notes.md` precisely because
mechanical checks won't catch them.

---

## 9. Hard Nots

- **Not a sync engine.** Request/response, not bidirectional state.
  The project is the source of truth.
- **Not a CI pipeline.** Validation proves *this tarball* is good
  against the project's current state. The project's CI runs on
  every commit and is the authoritative check after I apply.
- **Not a backdoor to the real project.** The validation script
  never writes outside the staging directory; `apply.sh` follows
  the same rule.
- **Not an installer.** If a tool is missing, validation reports it
  missing. No `npm install`, `apt install`, or equivalents.

---

## 10. Quick Reference

> Derived checklists. Where a step compresses a section, the cited
> section wins.

### 10.1 Building a response tarball

A worker session's checklist. A read-only (planner) session builds
no response tarball and skips it (§2).

1. Confirm the bale-carried globals are present: `AGENT.md`,
   `TARBALL.md`, `DOCS.md`, `CODE.md`, `PLANNER.md`. The first two
   are the minimum
   for building a response — pause and ask if either is missing.
2. Plan: list every file that will change, decide deferrals up front,
   decide what to claim for each project-level check. If the plan
   cannot be made without an answer only the planner can give — a
   blocking intent gap (§5.9.1) — stop here and take §10.3's path:
   `tools/craft_response.py --kind clarification`, then
   `--emit-block` for the paste courier, with the round carried by
   `bale relay`; asking in chat instead leaves the exchange
   unrecorded — the session's telemetry `clarification.rounds`
   (`schemas/telemetry-record.schema.json`) reads zero against real
   rounds.
3. Build `files/` mirroring the project tree (when there are
   created/modified entries). Build the mirror by copying the shipped
   originals and editing in place with tools — never retype large
   files through context; hashes are recomputed per step 10
   regardless.
4. Build `manifest.json` with reasons, sizes, sha256s (computed via
   §5.2.1, never by hand), deferrals, `validation_will_run`, and
   `claims`. `changes[]` paths are unique; a duplicated path is
   invalid (it makes the mirror correspondence below ambiguous — the
   lint's DUPLICATE_PATH row).
5. Write `apply.sh` for the operations the `files/` mirror can't
   express — deletes, the removal half of renames, exec-bit restores
   (§5.1.1) — or the no-op script if there are none.
6. Write `validation.sh` honoring the contract in section 7.
7. Optionally write `notes.md` if there are surprises, decisions,
   `unknown` claims, or follow-up proposals (§5.4.1) to surface. Skip
   the file otherwise. A `changes[]` path outside the write forecast
   makes the file required, and the path is declared twice:
   enumerated here with its reason, and recorded in the manifest's
   `forecast_departures` as a `path` and `why` pair (§5.4).
8. Do not write `next-prompt.md` — retired (§5.5). Follow-up
   suggestions go in the Proposals section of `notes.md`, as prose
   with rationale, never as a pack command.
9. Optionally write `README.md` if there's color beyond
   `manifest.summary` worth keeping. Skip otherwise.
10. **Self-check the manifest's internal consistency** — a computed
    pass over the finished manifest against the real `files/`, not a
    recollection of what was intended. The set is:
    - **Recomputed hashes.** Re-run the §5.2.1 computation against
      the bytes now under `files/` and confirm every `size_bytes` and
      `sha256` matches — recomputed, never transcribed.
    - **`files/` ↔ `changes[]`, both directions.** Every `created`/
      `modified` entry has a file under `files/`, and every file under
      `files/` has a matching entry — no declared-but-absent file, no
      undeclared file. (`deleted` entries carry no `files/` member by
      §5.1.1.)
    - **`set(claims) ⊆ validation_will_run`** — per §5.3's
      canonical-identifier rule. A key with no match is the tell of a
      renamed or paraphrased check; the fix is the key, not a new
      entry.
    Bale's pre-flight (§8) independently re-checks the first two and
    bounces a tarball that fails either. The third is the builder's
    to keep: bale treats claims as diagnostic, not gatekeeping
    (§7.3), so this self-check is the one place a stray claims key is
    caught before it surfaces as an unpairable line in the §7.3
    reconciliation.
11. Tar: `tar -czf response-<sid>.tar.gz response-NNN/`. The
    filename carries the full session id — the `responds_to` value —
    while the directory inside stays `response-NNN/`: the directory
    is wire format that `bale apply` peeks for, and it does not
    change.

### 10.2 Returning a probe instead

1. Confirm a §4.1 trigger fired — the gap is environment-specific,
   not conceptual or scope — and the manifest doesn't set
   `expects_probe: no` (§3.3).
2. Write the paste-back block per §4.2: purpose header, sentinels,
   labeled sections, bounded output, integrity trailer. Bash by
   default; PowerShell variant only when Windows-native is in play.
3. Only if output size or format demands the file-based fallback
   (§4.4): say so, and list in the chat preamble every location the
   script writes to (only `./probe-output/`) and every tool it
   invokes.
4. Stop. The probe's output is needed before any response can be
   built. When it arrives, the eventual response's `notes.md` records
   what the probe established (§4.5).

### 10.3 Returning a clarification instead

1. Confirm the gap is one only the planner can answer — an intent
   gap per §5.9.1, or an environment gap when probing is unavailable
   (`expects_probe: no`, §3.3) — not an environment fact a probe can
   fetch (§4) and not a budget problem (§5.6) — and that it is
   **blocking**. Nice-to-know goes in `notes.md` Proposals on a full
   response (§5.4.1).
2. Build the manifest: `response_kind: "clarification"`; `changes`,
   `deferred`, `validation_will_run`, `claims` all empty; a
   non-empty `questions[]` with all four fields per entry —
   question, context, default_assumption, why_blocked (§5.9.2).
3. Ship no `files/`, a no-op `apply.sh`, and a no-op
   `validation.sh`. `notes.md` is optional, addressed to the
   planner — and it rides the tarball only. The paste courier
   carries the question rows and nothing else, so anything the
   planner must see before answering goes in a row's `context`
   (§5.9.2).
4. Deliver both couriers — the tarball, and the same manifest
   wrapped in a `BALE EXCHANGE BEGIN <sid>` / `BALE EXCHANGE END`
   paste block with its purpose header and sha256 trailer, rendered
   by `tools/craft_response.py --emit-block` (§5.9.2) — so the
   operator picks the route at carry time. Never as a chat aside
   (§5.9.1). The paste block itself reaches chat as a file —
   `--emit-block` redirected and the file presented, never retyped
   into the reply; §5.9.2 says why, and what a trailer refusal
   calls for.
5. Stop. The answers arrive as an exchange record's paste block,
   emitted by `bale relay` (§5.9.4); verify its trailer before
   reading it. The session stays suspended and continues to a
   normal response against the same request. Do not guess ahead of
   the answers.

### 10.4 Returning a light question block instead

1. Confirm the set is non-blocking — the work could proceed on the
   named defaults — and count it against §5.10: at most three
   questions, none multi-tiered, each with a default the packer can
   ratify in a word. A set that fails the count is §10.3's path; a
   blocking question is §10.3's path at any count.
2. Render the block per §5.10: fill the rows as a clarification
   manifest and run `tools/craft_response.py --light-block <file>`,
   which prints `=== LIGHT BEGIN <sid> ===`, one `[n]` entry per
   question with its four labeled rows, the three-reply line, and
   `=== LIGHT END <sid> ===`, and refuses a set that fails the count.
   Where the crafter is unreachable, author the same block by hand.
3. Stop. The turn ends on the block; nothing is built ahead of the
   reply, and no exchange record or telemetry is written.
4. On the reply, continue under the same session: an inline answer
   or "as assumed" resumes the work, and the eventual response's
   `notes.md` names each question and its answer; "formal" re-emits
   the same rows as a clarification response through §10.3.
