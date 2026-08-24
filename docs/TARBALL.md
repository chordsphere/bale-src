# TARBALL.md

> The mechanical contract for tarball mode.
> Read when entering tarball mode (per `CLAUDE.md`).
> For the *why* behind any of this, see `CLAUDE.md`.

---

## META

### What this doc is

The wire-format contract for tarball mode. `CLAUDE.md` covers the
*why* and *when*; this doc covers the *exact shape* of each artifact
and how the bale tool and `validation.sh` enforce it between them.
If something here conflicts with what Claude remembers from a prior
session, **this file wins.**

Bale injects this file into every request, so it is always present.
If it is missing (a hand-rolled request), Claude pauses and asks
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
| Producing a normal response tarball — the default whenever work landed | Core: sections 1, 2, 5, 7 |
| Orienting in the received request needs more than the manifest itself — a field's semantics, what belongs where in `context/`, or how `expects_probe` binds | Section 3 |
| Asked to draft a `bale pack` command, or offering a rescope split (`CLAUDE.md` §11.2) | Section 3.4 |
| An environment fact the response depends on is missing, stale, or unclear — returning a probe instead of building | Sections 1, 2, 4 |
| The goal won't fit this session's context budget (`CLAUDE.md` §11 triggered) — returning a bailout | Sections 1, 2, 5.6, 5.7, 5.8 |
| A blocking intent gap in the request prevents trustworthy work — returning a clarification | Sections 1, 2, 5.9 |
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
  NNN is a per-day monotonic counter maintained by bale.
- **Artifact directories.** `request-NNN/` and `response-NNN/` use
  the same NNN as the session ID, zero-padded to three digits. A
  response is numbered to match the request it answers. Probes
  produce no artifact directory (§4.2).
- **Roles.** Three roles recur here and in `CLAUDE.md`: the
  **planner** decomposes goals, authors packs, and reviews — today
  the human architect; the **worker** builds responses — Claude; the
  **operator** runs pack/apply and holds the mechanical steps
  between them — today the same human as the planner, later possibly
  a harness. "Architect" and "planner", "Claude" and "worker" are
  synonyms throughout; the docs use whichever a sentence inherited.
- **Examples are examples.** Schemas below reference Vue/Vite/etc. to
  make shapes concrete. They are illustrative, not normative.
  Substitute the project's actual stack.

---

## 2. Three Exchanges

| Exchange | Direction | When |
|----------|-----------|------|
| Request tarball | planner → worker | start of a tarball-mode session |
| Probe | worker → planner | whenever an environment-specific fact is missing, stale, or unclear (§4.1) |
| Response tarball | worker → planner | every tarball-mode response |

The two tarballs are artifacts; the probe is not — it is a
paste-back script and its pasted output, chat-ephemeral by design
(§4.2).

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
  validation.sh        # Claude's hypothesis test on the changes (required)
  files/               # mirrors the project tree from repo root (required when changes[] has created/modified entries)
    src/...
    package.json
    ...
  README.md            # optional; color/context beyond manifest.summary
  notes.md             # optional; include when there's something to surface
```

`files/` mirrors the project structure from the repo root. If Claude
touches `src/components/Foo.vue` and `package.json`, they appear at
`files/src/components/Foo.vue` and `files/package.json`. Apply is
then `cp -r response-NNN/files/. <project>/` — no path translation
required. The mirror is enumerated by its files: an empty directory
under `files/` declares nothing and is ignored — by the §10.1
correspondence and by the §5.6.1/§5.9.2 "absent or empty" test
alike.

**`files/` carries source, never generated artifacts.** No bytecode
(`__pycache__/`, `*.pyc`, `*.pyo`), no dependency trees
(`node_modules/`), no build output (`dist/`, `build/`). This is a
**contract** rule (label per `CLAUDE.md` §6): bale's apply
pre-flight rejects a response whose `changes[]` paths include one,
naming the offending paths, before any staging happens. The deny
list is exactly the names above — not a heuristic — so a legitimate
source file that merely resembles one (a script named `build`, a
`pyc_utils.py`) passes (rationale: ADR-0013). `.bale/` paths are
also never shipped, but that rejection belongs to path safety, not
to this rule.

The two optional artifacts (README, notes) follow the stub-averse
principle: include them when there's content; omit them otherwise.
Absence carries meaning — no extra prose, no surprises, no proposal
queued. Bale shows them in the apply walkthrough if present and
stays silent if absent. (`next-prompt.md`, a third optional artifact
in earlier versions of this contract, is retired — §5.5.)

**File changes go inside the tarball, not alongside it.** When the
response delivers code or content changes, those changes belong in
`files/` and `apply.sh`, declared in the manifest — not pasted into
chat as a preview or as a courtesy copy (rationale: ADR-0013).

This rule is narrow on purpose. Tarball mode does not mean *only*
tarballs come out of it: a probe (section 4) is the right response
to a missing, stale, or unclear environment fact; a conversational
reply is the right response to a scope question, a concern, or a
quick clarification — and when such an intent gap is *blocking*,
the clarification response (§5.9) is that ask given a durable wire
shape. The constraint is on the *deliverable's shape*: when code is
the response, the tarball is the response, without a parallel copy
in chat.

A **bailout** response (§5.6) has a distinct shape: no `files/`,
no-op `apply.sh` and `validation.sh`, plus mandatory `handoff.md`
and `diagnostics.json`. It is the response Claude returns when the
session can't fit the goal within its context budget — see
`CLAUDE.md` §11. Bale's apply step treats bailouts as informational
rather than applicable.

A **clarification** response (§5.9) is the bailout's structural
sibling for a different failure: the *request* is blocking — an
intent gap, not a budget or environment gap. Same empty change
surfaces, but its payload rides in the manifest as a `questions[]`
block, and unlike a bailout it does not consume the session: the
lock stays held, the architect answers, and the same session
continues to a normal response.

### 5.1.1 apply.sh

`apply.sh` ships operations beyond the cp-and-overwrite that `files/`
already provides — primarily deletes. Renames are decomposed into a
`created` entry under `files/` (the new path with its full content)
plus an `rm` of the old path in `apply.sh`; `apply.sh` itself never
performs `mv` operations, because the commit step in bale is driven
per-manifest-entry from `changes[]`, not from a tree-level diff.

Executable mode bits are the parallel case the cp-mirror can't
carry: bale's `files/` overlay strips mode, so a `created` or
`modified` entry meant to be executable arrives at staging with the
exec bit cleared. `apply.sh` restores it with a per-path `chmod +x`
after the overlay applies — `chmod +x scripts/release.sh`, one line
per file. The responsibility sits on Claude because the overlay
can't infer intent (failure analysis: ADR-0013). The
validation-side guard that catches a forgotten `chmod` — an
exec-bit assertion in `validation.sh` — is §7.7.

Bale runs `apply.sh` in a staging copy of the project before
`validation.sh`, then verifies the resulting state matches the
manifest: every file removed from staging must be in
`manifest.changes` as `action: deleted`; every file added must be
`action: created`; every modified file's sha256 must match. A
malformed `apply.sh` that touches files not declared in the manifest
fails verification and the tarball is rejected.

`apply.sh` is minimal — only the operations the cp-mirror can't
express. A session with no deletes, renames, or executable bits to
restore ships a no-op script:

```bash
#!/usr/bin/env bash
# No additional operations for this session.
exit 0
```

Typical contents for a delete:

```bash
#!/usr/bin/env bash
set -euo pipefail
# Remove src/legacy/Bar.vue — superseded by Foo.vue.
rm -f src/legacy/Bar.vue
```

`apply.sh` runs with cwd set to the staging directory. It never
touches files outside the staging tree (bale's path-safety check
catches escapes; the post-run manifest reconciliation catches
unauthorized writes within the tree). Claude does not use `apply.sh`
to install dependencies, run builds, or perform side effects beyond
file-tree operations — those are out of scope for the apply
contract.

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

Field semantics:

- **`changes`** — may be empty: a no-op change set is `changes: []`
  with no files under `files/`; the §10.1 correspondence then holds
  vacuously, and a file under `files/` beside an empty `changes[]`
  is an undeclared file, not an implied change.
- **`changes[].reason`** — non-empty for every entry. Bale rejects
  empty strings. The reason is read later by someone who wasn't
  around for the session.
- **`changes[].action`** — `created`, `modified`, or `deleted`.
  `deleted` entries have `size_bytes: 0` and `sha256: null`; the
  file does not exist under `files/`. The actual removal happens in
  `apply.sh`.
- **`deferred`** — explicit list of things Claude considered but
  didn't do. Each has a `why`. The list is how I know what's not
  here.
- **`validation_will_run`** — declarative list of what
  `validation.sh` is configured to do. Lets me predict the cost
  before running it.
- **`claims`** — Claude's prediction for each project-level check,
  distinct from what validation actually finds. See 5.3.
- **`responds_to`** — the session ID of the request this response
  answers (full form: `YYYY-MM-DD-<slug>-NNN`). Bale verifies it
  matches the locked session. `session_id` equals `responds_to` for
  normal and bailout responses alike (both answer the request they
  were built for), and for a clarification too — a clarification
  suspends rather than consumes its session (§5.9), so it carries
  the same sid the eventual normal response will.
- **`corrects`** — optional, default `null`. If this response is a
  re-attempt at a previous response whose validation failed or
  whose application revealed a problem, this is the session ID of
  the response it replaces (e.g., `"2026-05-10-foo-014"`). The
  replaced response's tarball stays in `claude/responses/` as
  history; the pointer is how someone reading later traces what
  happened.
- **`response_kind`** — `"normal"` (default) for an ordinary
  response. `"bailout"` when Claude could not fit the goal in this
  session's context budget (see `CLAUDE.md` §11); bailout responses
  follow the distinct shape in section 5.6. `"clarification"` when a
  blocking intent gap in the request prevents trustworthy work;
  clarification responses follow the distinct shape in section 5.9.
- **`feedback`** — optional dual-stream session feedback (v0.3.8+).
  The two streams, the trust split behind them, and the
  fill-by-running-the-lint workflow are §5.2.2. Apply persists the
  block verbatim into the session's telemetry record, which is what
  makes filling it honestly worth the two minutes.

The skeleton itself is mechanized: `tools/craft_response.py`, shipped
in every request per §3.1, emits the manifest skeleton for any
response kind (`--kind {normal,bailout,clarification}`, default
`normal`) with the computed fields filled and the judgment fields —
`action`, `reason`, `summary`, `deferred`, `validation_will_run`,
`claims` — left for the worker, plus the `apply.sh` scaffold of
§5.1.1 (the no-op, or `rm` lines for deletions and per-path
`chmod +x` lines for files the worker names executable). The two
non-normal kinds' full artifact sets are §5.6.1 and §5.9.2. The
crafter never validates its own output: fill the judgment fields,
then the lint judges (§5.2.2's workflow). Sizes and hashes: §5.2.1.

### 5.2.1 Computing size_bytes and sha256

`size_bytes` and `sha256` are computed, never transcribed
(rationale: ADR-0013): bale's pre-flight rejects any tarball whose
manifest sha256 disagrees with the bytes under `files/` (§7). Run
the values off the real files.

The computation is the crafter's: `tools/craft_response.py` (shipped
in every request per §3.1) walks `files/`, computes every
`size_bytes` and `sha256`, and emits the `changes[]` skeleton with
the mirror prefix stripped, paste-ready — `--changes-only` for the
array alone; `--help` for the full surface. `deleted` entries carry
no file under `files/`; their two literals (`size_bytes: 0`,
`sha256: null`) are the only size or hash values not computed from
bytes, and the tool writes them too (`--deleted PATH`). Nothing in
this field set is ever produced from memory — a hash recalled rather
than recomputed is exactly what §10.1 step 10 and `CLAUDE.md` §11.6
exist to catch.

### 5.2.2 The feedback block

An optional top-level `feedback` object (v0.3.8; shape in
`response-manifest.schema.json`) carries the session's own account of
itself. Bale's apply persists it verbatim into the session's
telemetry record, where it aggregates across sessions.
Pre-v0.3.8 manifests omit it and still validate; new responses
include it.

The block is **two streams split by trust level** (rationale:
ADR-0013):

- **`mechanical`** — values the lint (`tools/response_lint.py`,
  shipped in every request per §3.1) can recompute and verify:
  `response_kind` (echo of the manifest's effective kind),
  `schema_valid`, `mirror_agreement` (the §10.1 both-directions
  `files/` ↔ `changes[]` result, split by direction), and
  `claims_subset` (the §5.3 subset rule). Two optional members ride
  here because their *shape* is fixed even where their content is
  self-reported: `linkage` (present when the session went through a
  probe or clarification round — which recourse, and whether the gap
  surfaced pre-read, pre-build, or mid-build) and `provenance` (the
  request's provenance block echoed verbatim plus `model_identity`,
  which is self-reported and unverifiable today — recorded for
  aggregation, read with that caveat; null when the request carried
  no provenance).
- **`self_reported`** — worker-authored judgment the lint cannot
  check: `assumptions` proceeded on without confirmation (the §3.3 /
  §5.9.1 recoverable-risk posture), `judgment_calls` the planner
  should find without reading the diff, `budget_pressure` (`none` |
  `tight` | `bailed` — the session's own read of `CLAUDE.md` §11),
  `includes_missing` (files the session wanted but the request didn't
  ship — packing signal), and `compaction_occurred` (with a
  `disclosure_ref` pointing at where the `CLAUDE.md` §11.6 disclosure
  lives when true). Honest empties are meaningful: `[]` asserts
  *none arose*, and the lint checks shape only, never content.

One member has been documented by its schema description alone
until now: `forecast_departures` — the block's structured record of
`changes[]` paths landing outside the request's stamped write
forecast, the machine-readable twin of the `notes.md` enumeration
(§5.4). Its stream placement, shape, and fill semantics follow
`response-manifest.schema.json`'s description, which remains the
field's full contract; this walk-through names the field so the
schema is no longer its only documentation.

**Fill the mechanical stream by running the lint, not by hand.** The
workflow: build the response through §10.1 steps 1–9, run
`python3 tools/response_lint.py <response-dir>
--emit-feedback-mechanical`, paste the printed object in as
`feedback.mechanical` (every field is that run's own computation;
the optional `linkage` and `provenance` members are the worker's to
add when they apply), fill `self_reported`
honestly, then run the lint once more — its feedback-block check
recomputes every mechanical value against the directory as packed and
flags any disagreement. A mismatch is the tell of a hand-filled or
stale block (an edit made after the values were copied), and the fix
is to re-run, not to adjust the values until the check goes quiet
(rationale: ADR-0013).

### 5.3 Claims vs verdict

Claude doesn't run validators. What Claude says about an outcome is a
**claim**; what `validation.sh` produces is a **verdict**. They're
separate fields so disagreement is itself diagnostic.

`claims` values per project-level check:

| Value | Meaning |
|-------|---------|
| `pass` | Claude predicts this check will pass |
| `fail` | Claude knows this check will fail (e.g. a deliberate WIP) |
| `untested` | The check will be skipped in my environment |
| `unknown` | Claude genuinely can't tell |

A claim value takes one of two forms (v0.4.7). The bare string from
the table above remains the default and every earlier manifest keeps
validating. The **annotated object form** —
`{"value": "pass", "claim_basis": "predicted"}` — lets the worker
additionally declare, at ship time, the claim's basis: `predicted`
from structural grounds, or `observed` from a real run before
shipping. `value` carries the same vocabulary as the bare string;
`claim_basis` is optional and its enum is closed (omit the key when
the basis is unknown — null is not a basis). Apply's verbatim
promotion of the claims map into the session's telemetry record
carries the object through unchanged, which is what makes the
record-side calibration split measurable from ship-time declarations.

One rule scopes the block: `claims` covers the project-level checks
(lint, typecheck, build, tests), and when the project has none — no
lint, typecheck, build, or test surface yet — it covers the
response's session-specific assertions (§7.2 item 6) instead. Either
way the keys are genuine predictions about non-tautological checks;
an empty block while claimable checks ran wastes the calibration
signal the field exists for. The mechanical checks the worker wrote
the manifest for (manifest consistency, file syntax) are tautological
— a `pass` claim adds no information — and are never claimed.

A `claims` key is not free text: it is the check's **canonical
identifier** — its `validation_will_run` entry, reused **verbatim**
(same characters, same spacing) as the `claims` key and again as the
verdict label §7.3 reconciles against. That one shared string is
what makes the reconciliation well-defined; a key with no verbatim
match in `validation_will_run` is unpairable — a prediction about a
check the manifest never says will run.

The match is one-directional, and the scoping is the point:
`set(claims) ⊆ set(validation_will_run)`, never the converse.
`validation_will_run` also lists the mechanical checks excluded from
`claims` above, and those entries stand as run-but-unclaimed —
correct, not a gap. This subset relation is what §10.1 self-checks
before packing and `CLAUDE.md` §11.6 re-derives after a compaction.

A claim disagreeing with the verdict doesn't reject the tarball; it's
flagged in validation's end-of-run report (what the disagreement
pattern is for: ADR-0013).

If Claude marks a check `unknown`, that itself is a finding worth a
line in `notes.md`: *what would Claude need to know to predict?*

### 5.4 notes.md (optional)

Include `notes.md` when there's something to surface. Skip the file
when there isn't — omission is the canonical signal for *"nothing
needed saying."*

Conversational when included. Use it for:

- Decisions Claude made that I should ratify (especially when a probe
  wasn't possible and Claude had to choose).
- Places I should look closely on review.
- Anything surprising Claude found in the existing code.
- Honest uncertainty — *"I'm not sure whether X should live in
  `composables/` or `utils/`; I put it in `composables/` because it
  uses reactive state. Move it if that's wrong."*
- Any `unknown` entry in `claims` — what Claude would need to predict
  with confidence.
- Things the manifest's structured `reason` field couldn't carry.
- Every `changes[]` path outside the session's write forecast — a
  new file the pack could not have named, or a modification the
  goal turned out to require, that no forecast entry covers. List
  each such path explicitly, with why the goal required it, so the
  operator can admit it at apply (§3.2). An unenumerated
  out-of-forecast path surfaces as a refusal instead of a decision.
- Follow-up work worth suggesting — as a Proposals section (§5.4.1).

If a session has any of the above, write the file. If a session is
small enough that none of the above apply, don't write a stub.

#### 5.4.1 The Proposals section

When a session surfaces follow-up work worth suggesting — a seam
visible only from inside the code, an out-of-scope fix worth doing
(rationale: ADR-0013) — `notes.md` carries it under a
`## Proposals` heading. Each proposal is a short block:

- **What** — the suggested follow-up, in one or two sentences.
- **Why** — the rationale, grounded in something this session
  actually saw. A proposal without a reason is a wish, not a signal.
- **Scope hints** — optional: the files or seams involved, and any
  ordering dependency on other work ("only after X lands").

Proposals are prose suggestions with rationale, **never ready-to-run
commands** — no `bale pack` line, no literal paste-this text; §3.4
carries the reasoning. The planner (the architect today, an
orchestrator later) reads proposals as *input*, decides sequencing,
and authors its own pack commands (§3.4) from its own understanding.

Proposals are distinct from the manifest's `deferred` list (§5.2):
`deferred` names in-goal work the session considered and didn't do;
Proposals name work the session's vantage point revealed, whether or
not the goal asked for it. An item can appear in both — deferred for
the record, proposed with the rationale — when the worker thinks it
should be near the top of the queue.

If nothing is worth proposing, omit the section, the same way an
uneventful session omits the file: absence means *no suggestion*.

### 5.5 next-prompt.md (retired)

Retired as of session `2026-07-06-retire-next-prompt-006`. Responses
do not ship `next-prompt.md`; the worker does not produce it. The
artifact carried a ready-to-run `bale pack` command inside the
response tarball — an *unsolicited, post-work* runnable command,
exactly the shape §3.4 confines to the pre-flight rescope offer
(hazards: ADR-0013). Follow-up flows as prose Proposals in
`notes.md` (§5.4.1); the retirement does not touch bailouts, whose
unfinished work was always `handoff.md`'s job (§5.7). This section
number is kept so older cross-references stay resolvable.

Transition tolerance: response tarballs produced before the
retirement may still contain `next-prompt.md`. Bale's apply
walkthrough tolerates them — the body is surfaced, labeled
deprecated — so pre-retirement archives stay reviewable. Nothing new
ships the file.

### 5.6 Bailout response

A bailout response is what Claude returns when `CLAUDE.md` §11
triggers have fired — the goal won't fit in this session's context
budget and Claude is handing off to a fresh session instead of
pushing through; the *why* lives in `CLAUDE.md` §11.

#### 5.6.1 Shape

The bailout's artifact set is mechanized: when the §11 triggers have
fired and a bailout is the response, `tools/craft_response.py --kind
bailout --write` (shipped in every request per §3.1) emits the whole
set — the manifest with its empty change surfaces (§5.6.2) and no
`files/` (absent or empty), the no-op `apply.sh` and `validation.sh`
the kind fixes (nothing changed, nothing to test), the required
`handoff.md` as a scaffold of §5.7's sections (the content under
each header is judgment and stays the worker's), and the required
`diagnostics.json` skeleton (§5.8). `notes.md` remains optional,
addressed to me rather than the next Claude. The crafter never
validates its own output; the lint judges the finished response, and
an unfilled skeleton is deliberately lint-invalid.

`response_kind: "bailout"` in the manifest is the canonical marker.
Bale's apply step branches on it: instead of applying changes, it
displays the handoff summary and prompts the user to run
`bale handoff <response-NNN>` to package a fresh session.

`README.md` is absent in bailouts — `handoff.md` carries the
forward-looking content for the next Claude, and `notes.md` (if
present) carries the user-facing commentary. (`next-prompt.md` is
retired everywhere, §5.5.)

#### 5.6.2 Manifest specifics for bailouts

When `response_kind: "bailout"`, every change surface is empty:
nothing changed, nothing ran, nothing is claimable. The empty
surfaces are mechanized — the crafter (§5.6.1) emits them and the
lint rejects a bailout that violates them — so only the judgment
halves remain here: `summary` is one paragraph on what was
attempted, which trigger fired (per `CLAUDE.md` §11.3), and what
the handoff prescribes for the next session; and deferred work
lives in `handoff.md`'s prescription, never as a flat `deferred`
list.

The `responds_to` field still names the request this answers. The
new session that the user packs after running `bale handoff` will
have its own fresh `session_id` (same slug, new date+NNN), and its
`depends_on.previous_response` will point at the bailout.

#### 5.6.3 Apply-time UX (moved)

Moved to the bale tool's own design documentation — the apply-time
behavior is a contract on the bale implementation, not on the
worker, and nothing that binds response authoring left this file.
This section number is kept so older cross-references stay
resolvable.

### 5.7 handoff.md (required in bailout responses)

Written for the **next Claude session**, not for me. Voice is
terse and instructional — no hedging, no conversational softening,
no "I" reflection beyond what the next Claude needs to plan its
budget.

Required sections, in this order:

```markdown
# Handoff

## Original goal

[Verbatim copy of `manifest.goal` from the request this bailed on.
The next session should not have to re-extract this.]

## What I loaded

[Every doc and source file Claude actually read this session, with
a verdict on whether it earned its budget cost:
- `path/to/doc.md` — necessary | wasted | partial
The next Claude uses this to skip what wasted budget last time.]

## What I explored

[Reasoning paths Claude pursued — drill-downs, hypotheses, design
options — with a verdict:
- `did X` — productive | dead end | inconclusive
Concrete enough that the next Claude can avoid repeating dead
ends.]

## What I learned

[Concrete observations that compress the next session's reading.
Example: "The relevant logic for goal X lives in `composables/`,
not `utils/`." "Skip `src/legacy/` — nothing in it is reachable
from the current entry points." If nothing useful was learned,
state that.]

## Reading plan for the next session

[A specific drill-down prescription for the next Claude, given the
original goal. INDEX-table-compatible paths. If reading order
matters, number it. This is the most important section — its job
is to put the next Claude on the right track in one read, not
ten.

When the bailing Claude has a clear recommendation for what the next
session should do, the reading plan is written for *that* piece —
concrete, single-track, ready to execute. Alternatives worth
preserving are framed as *overrides* ("if the architect picks X
instead, the reading plan is Y"), not as equal candidates in a
menu. Defaulting to a menu when a recommendation existed loses the
recommendation to a "which piece?" round-trip in the next session.

The multiple-choice shape is reserved for genuine close calls where
the bailing Claude couldn't pick. When that case applies, the
handoff also declares that **the next session opens in
conversational mode** and transitions to tarball mode after the
architect picks.]

## Salvageable work

[Any partial decisions, sketches, or code stubs that should not be
discarded. Verbatim where possible. If nothing is salvageable,
write: "Nothing to salvage — restart from the reading plan."]
```

The next Claude reads `handoff.md` as the first `context/` doc. Its
reading plan is high-value input, ratified by the planner at
`bale handoff` time — the request manifest remains authoritative,
and where the two disagree the manifest wins.

### 5.8 diagnostics.json (required in bailout responses)

Structured longitudinal data, aggregated across sessions to
calibrate where budget actually goes. The shape is mechanized: the
schema of record is `schemas/diagnostics.schema.json` (in the bale
installation — the schemas tree ships with the install, reachable
from any project the same way the `tools/` pair is), the crafter
(§5.6.1) emits the skeleton carrying its
required keys — `session_id` filled, everything else empty — and
the lint validates the filled file against it. Structural detail
(required keys, enum values, entry shapes) lives in the schema,
not here.

What the judgment fields want:

- **`bail_trigger`** — the first two enum values match the
  Claude-detected triggers in `CLAUDE.md` §11.3. The third
  (architect-requested bailouts — test sessions, deliberate
  checkpoints; see `CLAUDE.md` §11.3's third bullet) uses `"other"`
  and surfaces the specifics in `bail_narrative` rather than minting
  a new enum value (enum design: ADR-0013).
- **`bail_narrative`** — Claude's honest paragraph on the bail
  decision. The retrospective complement to the prescriptive
  `handoff.md`.
- **`context_loaded[].verdict`** — the verdict is qualitative;
  Claude can't measure token-spend per doc precisely.
- **`what_would_save_next_time`** — each entry a concrete
  prescription. Overlaps with `handoff.md`'s "What I learned"
  section; that's intentional — `handoff.md` is for the next
  Claude, `diagnostics.json` is for the user's longitudinal
  analysis.

The schema is intentionally loose: new fields can be added in
future sessions without breaking earlier aggregation, and values
are honest estimates rather than measurements. Aggregation across
sessions is left to the user (jq, notebook, eventual `bale stats`
command).

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

The mechanics keying (design rationale: ADR-0011) is what makes the
edge case well-defined: a blocking environment gap under
`expects_probe: no` (§3.3) may take the clarification shape, because
with scripting forbidden, questions to the planner — who can read
their own environment — are the recourse that remains.

#### 5.9.1 When it engages

Canonical intent-gap triggers: an undefined term in the goal; a
constraint that conflicts with an included file; a decision the
packer made but did not transport into the request. No script
against the environment can answer these — which is exactly why
they are not probes. The converse admission also holds: when
probing is unavailable (`expects_probe: no`, §3.3), a blocking
environment gap is admissible here — the taxonomy keys on
mechanics (§5.9), and questions to the planner, who can read the
environment the worker can't script against, are the recourse that
remains.

**Questions must be blocking.** A clarification response asserts:
*this session cannot produce trustworthy work without these
answers.* Nice-to-know questions go in `notes.md` Proposals on a
full response (§5.4.1), not here (precedent: ADR-0011).

Which surface carries the ask defaults on the **courier**. In a
human-attended session, chat is the default — even for a blocking
gap (`CLAUDE.md` §3: ask, in one sentence). In an orchestrated
session, the artifact is the default: the apply walkthrough
surfaces it, the record persists for aggregation (§5.9.4), and a
programmatic courier can carry it where a chat aside cannot go.
When a blocking ask resolves in chat, the eventual response's
`notes.md` records the question and its answer — the §4.5
provenance rule applied to clarifications: chat is ephemeral, and
the record is how the answer survives it.

The same default-to-ask doctrine that governs probes (§4.1)
governs clarifications: proceeding on a guessed intent is the
confidently wrong response this workflow exists to prevent, and
asking beats guessing. `expects_probe: no` does **not** forbid a
clarification — that flag governs probes against the environment
(§3.2), not questions about the request. For a gap too small to
earn the artifact, the lightweight fallbacks stand: ask in chat, or
proceed on the most plausible assumption named explicitly in
`notes.md` and flagged for review — the same recoverable-risk
posture §3.3 takes.

#### 5.9.2 Shape and manifest specifics

Unlike the bailout there are no companion artifacts: the payload is
the manifest's own `questions[]` block — required and non-empty on
this kind, forbidden (or empty) on every other. `README.md` is
absent on a clarification in either direction — the questions are
the payload and `notes.md` (optional, addressed to me) is the prose
channel.

The shape is mechanized: when the ask takes the artifact shape,
`tools/craft_response.py --kind clarification` (shipped in every
request per §3.1) emits the manifest skeleton — `response_kind:
"clarification"`, the same empty change surfaces as §5.6.2 (nothing
was applied, nothing ran, nothing to claim; bale rejects a
clarification that violates these), no `files/` (absent or empty),
and `questions[]` seeded with four-field entry stubs (`--questions
N` for more than one) — plus, under `--write`, the no-op `apply.sh`
and `validation.sh` the kind fixes. The entry fields' schema of
record is `response-manifest.schema.json` (in the bale
installation, beside §5.8's); the lint judges the
finished response, and an unfilled skeleton is deliberately
lint-invalid.

Two judgment notes survive the tool: `summary` is one paragraph on
what the session was asked to do and that it is blocked on the
questions below; and the `default_assumption` field is load-bearing
— it lets the planner answer with a single *"your assumption is
correct"* and surfaces the worker's reasoning for audit.

A question row may additionally carry three optional fields
(v0.4.7); legacy four-field rows keep validating. **`options`** —
candidate answers, at least one when present. **`recommendation`**
— the worker's pick among them. **`priority`** — enum exactly
`blocking` | `batched`: only critical-path blockers interrupt;
everything else batches. The doctrine behind all three — why
questions arrive answerable, and what the two priority classes mean
for the asker — has one home in the bale tool's own orchestration
documentation; this section names the fields and stops there.

#### 5.9.3 Apply-time UX (moved)

Moved to the bale tool's own design documentation — the apply-time
behavior is a contract on the bale implementation, not on the
worker; the worker-facing consequence (the session suspends and
continues to a normal response) stays in §5.9's own prose and
§5.9.4. This section number is kept so older cross-references stay
resolvable.

#### 5.9.4 Posture and the answer path

A clarification is respectable, not a failure — the intent-gap
analog of a probe (posture: ADR-0011). It is also a signal about
the *request*: clarifications clustering against one packer or one
kind of request indicate a packing or decomposition problem. The
preserved manifests under `.bale/clarifications/` are the
aggregation surface for that signal (jq across
`.bale/clarifications/*/*.json`), parallel to the role
`diagnostics.json` plays for bail triggers.

The answer path is courier-agnostic, mirroring the probe's §4.6:
manual today (the architect reads the questions in the apply
walkthrough, answers in the worker's chat, and the session
continues — or repacks if the framing was wrong), programmatic
later (the orchestrator receives the clarification, answers from
its own context or escalates to the human, and re-prompts the
worker). The artifact is identical in both worlds; only the
courier changes.

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
Claude claims they do?"* It is Claude's per-session hypothesis test,
written fresh for each response — not a fixed project pipeline.
Claude chooses what to invoke based on what this session actually
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
write to. No surprise writes.

### 7.2 Check sequence

Each check prints `[PASS]`, `[FAIL]`, or `[SKIP] <reason>` on its own
line. Silent skip is a bug.

Claude chooses which checks to include based on what this session
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
   Claude wrote for this response — assertions that a new function
   returns what the goal called for, that a removed feature really
   is gone, that an INDEX entry exists for a new doc, etc. These
   are inline in `validation.sh` rather than invocations of
   external tooling. When the session enforces a project's
   doc-contract rows, `tools/craft_response.py --doc-assertions`
   (shipped in every request per §3.1) emits those blocks
   paste-ready; the rows' full homes remain `DOCS.md` §9 and
   `CODE.md` §10.

If a check's tool isn't installed, it prints `[SKIP] <check>: <tool>
not found`. Never silently passes. Never installs anything.

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

Claim/verdict disagreement alone does not flip the exit code.

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
  CLAUDE.md            # injected by bale
  TARBALL.md           # injected by bale
  DOCS.md              # injected by bale
  CODE.md              # injected by bale
  PLANNER.md           # injected by bale
  tools/
    response_lint.py   # injected by bale (v0.3.8): the worker's pre-pack self-check
    craft_response.py  # injected by bale (v0.3.19): the response-skeleton crafter (§5.2)
  context/             # everything the user chose to include
    <project files and any project docs the user named>
  README.md            # optional; prose context beyond the manifest's structured fields — authored by either party
```

The first six slots are reserved for bale-injected global docs and
the manifest; the `tools/` pair rides beside them (also
bale-injected, from the install — `INJECTED_TOOLS` in `bin/bale` is
the one source for the list): the lint, so the worker can run the
§10.1 step-10 self-check mechanically against its response directory
before packing, without bale installed, and the crafter, so every
response kind's skeleton is emitted rather than retyped (§5.2). Everything else the user
wants Claude to see —
including project-specific docs like `INDEX.md`, `STATE.md`, ADRs,
schemas, and prior probe output — lives under `context/`. No top-
level slots are reserved for project docs; bale is project-agnostic.

`README.md` is optional prose context: whatever is worth keeping
that doesn't reduce cleanly to the manifest's `goal`, `constraints`,
or `out_of_scope` fields. Either party authors it. The planner
writes it directly — the pack wizard offers `$EDITOR` to opt in —
or the worker writes it on request, delivering the brief as a
downloadable file the planner ships with `--readme-file` (§3.4),
whose search-path resolution lets a brief in the planner's downloads
directory pack by bare name. Most sessions skip the README
entirely.

A project that has adopted the DOCS.md workflow might fill `context/`
with paths like:

```
context/
  INDEX.md             # the project's doc map
  charter-brief.md
  STATE.md             # current snapshot, if relevant
  decisions/           # ADRs I think are in play
  sessions/            # prior response notes, if directly relevant
  probe-output/        # if a prior probe ran
  ...
```

The contents of `context/` are whatever the user named in the pack
request.

Schema files in `context/` may be partial extracts when the full file
isn't relevant — pull only the sections touched by the session, and
name the extract in `manifest.context_included` so the omission is
visible.

Tar with: `tar -czf request-NNN.tar.gz request-NNN/`

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
  "expects_probe": "yes | no | claude-decides",
  "context_included": [
    "context/charter-brief.md",
    "context/STATE.md"
  ],
  "resolved_scope": [
    "STATE.md",
    "charter-brief.md"
  ]
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
- **`constraints`** — things I commit to up front. Claude stays
  within them or surfaces a conflict in `notes.md`.
- **`out_of_scope`** — explicit list of *near-by* concerns Claude
  should not address (rationale: ADR-0013).
- **`expects_probe`** — `yes` forces a probe before any build work.
  `no` forbids probing this session (see 3.3). `claude-decides`
  (default) means Claude probes whenever a §4.1 trigger fires.
- **`context_included`** — declarative list of what's in `context/`.
  If Claude needs something not listed, it checks `INDEX.md`, then
  names it in the response (either in a probe request or in
  `notes.md` if Claude proceeded with an assumption). This list is
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
  registry records it (bale v0.3.21, board 33), and since bale
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

### 3.3 When `expects_probe: no` collides with a real gap

If the request forbids probing but the worker finds an environment-
specific gap documentation can't fill, the worker does not probe and
does not silently guess. The worker either:

1. **Stops and asks in chat** — if the gap is small enough to resolve
   inline.
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
authoring is always the worker's job (`CLAUDE.md` §4), with the same
flags and the same single-line form as a planner-authored pack.
Unsolicited, the worker emits a runnable command in exactly one
place: the rescope offer, when the pre-flight scope check
(`CLAUDE.md` §11.2) decides a goal needs splitting. Inside response
tarballs, follow-ups are prose Proposals in `notes.md` (§5.4.1),
never runnable commands.

The hazards that confine unsolicited runnable commands to that one
place — blind firing, and the self-oracle problem of the entity
under review framing its own follow-up — are ADR-0013's; sequencing
authority belongs to the planner (`CLAUDE.md` §4). An orchestration
layer consuming rescope offers should still re-derive the command
from the proposed seam rather than fire the worker's verbatim —
doctrine for when an orchestrator exists, not a change to the human
path, which needs the paste-ready command.

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
| `--expects-probe {yes\|no\|claude-decides}` | Sets `manifest.expects_probe` (§3.2; default `claude-decides`). |
| `--readme-file PATH` | Reads the request README's prose from PATH (UTF-8 text) instead of the `$EDITOR` step — the non-interactive way to ship prose context, including a worker-authored brief (§3.1). A relative PATH resolves like apply's tarball argument: cwd first, then each configured `apply.search_paths` directory in order; an absolute path bypasses the search; not-found names every directory consulted. Fails loudly on a missing, unreadable, or empty file — omit the flag to pack without a README. Also fails loudly when the resolved brief still contains an **unfilled placeholder**: any line containing the sentinel `TODO(brief)` (v0.3.21) — the convention a worker-authored brief uses to scaffold slots it hasn't filled, so a half-generated brief never ships; a worker authoring a brief writes exactly that form for anything left for the planner to complete, and fills or removes every such line before delivering a brief meant to pack. The pack report echoes the resolved README's identity — path, first heading line, and sha256 of the shipped bytes (v0.3.21; path + heading alone proved insufficient identity). Combines with `--edit` to review the file before packing. |
| `--checkpoint-file PATH` | Delivers the planner-authored blind checkpoint (§7) for a project that pins one: bale commits the file's bytes at the project's configured per-session checkpoint path and proceeds with the pack in the same invocation. A relative PATH resolves exactly like `--readme-file` (cwd first, then each configured search directory in order; an absolute path bypasses the search), and a missing, unreadable, or empty file fails loudly, same posture. Idempotent when the resolved path is already committed with identical bytes (the re-run of an aborted pack); differing bytes refuse loudly — the flag never silently replaces a committed checkpoint. Contradicts `--read-only` at arg-parse time: a read-only pack's empty write forecast waives the checkpoint requirement — the session can land nothing, so there is nothing for a checkpoint to grade and nothing to install. |
| `--edit` | Forces the README `$EDITOR` step even when `goal` and `--slug` are fully specified (where the wizard never engages). Seeded with `--readme-file`'s content when both are given, the standard scaffold otherwise; saving an empty buffer omits the README. Needs a TTY; conflicts with `--no-edit`. |
| `--no-edit` | In the wizard, skips the README y/N prompt and `$EDITOR` entirely — for automation that still wants the wizard's structured-field walk. Compatible with `--readme-file` (the file's prose still ships; no editor opens); conflicts with `--edit`; a no-op on the fully specified path. |
| `--no-readme` | Packs with no README, explicitly — the acknowledgment the no-brief guard demands when neither the wizard nor `--readme-file` supplies prose context; the guard's TTY/piped split is covered in the bale tool's own documentation. |
| `--json` | Emits the end-of-run pack report as one line of JSON on stdout — stable keys for downstream tooling — with informational lines and prompts moved to stderr. Packing behavior, prompts, caps, and hooks are unchanged. |
| `--packer NAME` | Sets `manifest.provenance.packer` — the pack's author identity, stamped so telemetry can attribute packer-side failures as well as worker-side ones. |
| `--work-class {code\|doc\|contract-doc\|meta\|mixed}` | Sets `manifest.provenance.work_class` — the work class telemetry and the trust ledger aggregate rates by. On the wizard path the session-shape question asks for it when the flag is absent (v0.3.15). |
| `--read-only` | Opens the session with the **empty write forecast** (v0.3.15, as the empty recorded scope; the degenerate case of the forecast model since v0.4.1, ADR-0015, and its only spelling — `--write` with zero paths refuses, and the two flags together contradict) — the read-only session shape for discussion, orchestration, or audit. The empty forecast intersects nothing (sibling packs and applies are admitted alongside it) and covers nothing (the own-forecast drift gate refuses every `changes[]` path a response under this sid ships — any `[]`-forecast session is structurally sweep-safe, and race-safe as well: an open `[]`-forecast sibling can be disregarded in re-landing and race reasoning, because it structurally lands nothing). `--include` still selects what ships in `context/` — the session reads files; it cannot land changes to them. Since v0.3.21 (board 33) a read-only pack also **sweeps**: finding an open session with recorded forecast `[]` (same registry record, same key), it offers to close it — `closed-read-only`, command `pack` — at a prompt whose default is **accept** (a read-only session structurally cannot lose work; piped stdin declines without a prompt, so automation never silently closes a session). Scoped packs and apply never sweep. The open banner names the session's own close-out: the next read-only pack, or `bale unlock <sid>` now. Bare boolean; full semantics in the bale tool's own documentation. |
| `--supersedes <sid>` | Declares the pack a split supersession of the named open session (v0.3.17): after a y/N exchange with a **decline default** (piped stdin takes the decline without a prompt), the parent closes as superseded-by-split, the child's manifest stamps `depends_on.superseded_session`, and exactly that one collision clears at the pack-time disjointness gate — every other open session still gates as usual. A sid that is not open is accepted only when its telemetry history shows a superseded-by-split closure (the idempotent re-run of a pack that aborted after the close). **Worker-authored only, by contract**: this flag appears in worker-emitted rescope commands — this table's §11.2 offer being the one sanctioned unsolicited-runnable site — and the architect pastes them; full flow in the bale tool's own documentation. |
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
intersects nothing — and lands nothing.

**Split supersession.** When a pre-flight split (`CLAUDE.md` §11.2)
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
architect's, or the one Claude emits in a rescope offer (`CLAUDE.md`
§11.2) — is written as one line with no backslash continuations, so
it pastes into a terminal directly. Repeatable flags repeat inline on
the same line; they do not wrap.

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
proposed, as Claude would emit it in a `CLAUDE.md` §11.2 offer, with
the deferred half named in `--out-of-scope`:

```
bale pack "Migrate the auth module to the new token format — types and store only" --slug auth-token-types --include src/auth/types.ts --include src/auth/store.ts --out-of-scope "endpoint wiring" --out-of-scope "tests for the endpoint layer" --expects-probe no
```

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
  what the goal means, which option the architect prefers, or whether
  something is in scope, no script against the environment can answer
  it. Quick, non-blocking questions resolve in chat; a gap of this
  kind that *blocks* trustworthy work takes the clarification response
  (§5.9) — the intent-gap sibling of the probe, same default-to-ask
  doctrine, different recourse.
- **`expects_probe: no` still forbids probing** (§3.3). The doctrine
  sets the default; the manifest overrides it per session, and the
  collision path in §3.3 is unchanged.

### 4.2 The paste-back probe (default shape)

Probes are session-scoped only: no `claude/probes/` directory, no
bale subcommand, no artifact in the project tree. The default
transport is a **single copy-pasteable shell block**. The architect
pastes it into a terminal and pastes stdout back into the chat; the
worker reads the paste and proceeds. No files change hands.

The block Claude returns is one fenced, self-contained script with
these required properties:

- **Strictly read-only — zero writes.** stdout is the only output
  channel. No `probe-output/`, no temp files, no state mutation of
  any kind — writes belong exclusively to the §4.4 fallback
  (rationale: ADR-0010).
- **Purpose header.** A comment block at the top stating what the
  probe asks, why the session needs it, and confirming the script is
  read-only. The architect audits this before pasting.
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

`probe.ps1` is conditional. Most environments (Linux container,
macOS, WSL) run the bash variant natively. Offer a PowerShell variant
only when the request or `STATE.md` indicates Windows-native
execution.

### 4.4 The file-based fallback

For genuinely large or binary output — a full dependency tree, a
generated fixture, anything past what a terminal paste carries
intact — the earlier file-based shape remains valid, explicitly as
the fallback: the script writes to `./probe-output/` and the
architect returns the contents (pasted as text if small enough, or
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

In the orchestrated workflow, the probe becomes a tool call the
harness executes and feeds back automatically. The paste-back shape
is the manual-transport analog of that: **same contract, different
courier**. Nothing in this section assumes the courier is human —
the sentinels, bounded output, and integrity trailer are exactly the
properties a harness needs to validate a machine round-trip too.

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
(labels per `CLAUDE.md` §6): caught at the planner's review, or held
by the operator's own procedure with no downstream catch — not by
bale.

| Rule | Type | Enforcement |
|------|------|-------------|
| The tarball is the contract — no side commands, no pasted snippets, no hand-edits | policy | review |
| Validate before apply, always | operator discipline | the operator's own procedure; no downstream catch |
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

1. Confirm the bale-injected globals are present: `CLAUDE.md`,
   `TARBALL.md`, `DOCS.md`, `CODE.md`, `PLANNER.md`. The first two
   are the minimum
   for building a response — pause and ask if either is missing.
2. Plan: list every file that will change, decide deferrals up front,
   decide what to claim for each project-level check.
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
   the file otherwise.
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
11. Tar: `tar -czf response-NNN.tar.gz response-NNN/`.

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
   architect.
4. Stop. The answers arrive in the chat; the session stays open and
   continues to a normal response against the same request. Do not
   guess ahead of the answers.
