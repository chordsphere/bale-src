# DOCS.md

> Documentation philosophy and patterns.
> Read whenever docs are the work, regardless of project shape.
> For the *why* behind any of this, see `CLAUDE.md`.

---

## META

### What this doc is

The vocabulary and philosophy of documentation decisions: when
content earns a doc of its own, what categories of doc exist and
how each behaves, when to introduce structure, and how to keep what
exists honest. `CLAUDE.md` covers *when* to engage this file; this
file covers *how* to think about docs once engaged.

The specific files this doc references — `INDEX.md`, `STATE.md`,
ADRs, schemas, explainers — are **instances** of the patterns, not
mandates. A casual project may have none of them. A mature project
may have all. Most projects sit somewhere between, growing
structure as it earns its place. Claude reads `DOCS.md` regardless
of project shape, to understand the vocabulary; what gets
instantiated is a per-project judgment guided by section 4.1's
introduction signals.

The file that owns a topic owns the rules for that topic. If
something here conflicts with what Claude remembers from a prior
session, **this file wins.**

---

## INDEX

### Read paths

| Situation | Load |
|-----------|------|
| Deciding whether to introduce a doc category (INDEX, STATE, ADRs) | Section 4.1 |
| Deciding whether something needs to become a doc | Sections 1, 4 |
| Adding a new doc (any category) | Sections 1, 4, plus 5 (ADR), 4.4 (path/name) |
| Updating `INDEX.md` | Section 2 |
| Updating `STATE.md` | Section 3 |
| Writing an ADR | Section 5 |
| Splitting a doc | Section 6 |
| Pruning or archiving | Section 7 |
| Naming a new file | Section 8 |
| Hard rules / what counts as a violation | Sections 9, 10 |

---

## 1. The Document Inventory

The vocabulary of documentation patterns. Each category below has
a purpose, a lifecycle (how it changes over time), a canonical
location, and a naming convention.

A project may have all of these in active use, some, or none — the
inventory is what Claude reasons *with*, not a checklist every
project must satisfy. Section 4.1 covers when to introduce a new
category; this section just names the categories and how each
behaves once present.

| Category | Examples | Lifecycle | Location | Naming |
|----------|----------|-----------|----------|--------|
| **Workflow** | `CLAUDE.md`, `TARBALL.md`, `DOCS.md`, `CODE.md` | Rarely changed; project-agnostic; always injected by bale into every request | global (in the bale tool's installation) | `ALL_CAPS.md` |
| **Project map** | `INDEX.md` | Edited whenever the inventory changes | `claude/` | `ALL_CAPS.md` |
| **Project snapshot** | `STATE.md` | Edited after sessions that move state; never appended | `claude/` | `ALL_CAPS.md` |
| **Charter / product** | `charter.md`, `charter-brief.md` | Edited rarely, when product direction shifts | `claude/context/` | `lowercase-hyphenated.md` |
| **Architectural decisions** | `0001-vue-over-react.md` | Append-only; new file per decision; old files never edited (superseded instead) | `claude/context/adr/` | `NNNN-lowercase-hyphenated.md` |
| **Schemas / data contracts** | `dist-api.openapi.yaml`, `dist-meta.schema.json` | Edited when the underlying contract changes | `claude/context/schemas/` | `lowercase-hyphenated.<ext>` |
| **Long-form explainers** | `surface-modes.md` | Edited when the subject evolves | `claude/context/` | `lowercase-hyphenated.md` |
| **Session notes** | `notes.md`, `next-prompt.md` | Write-once; archived, never edited | `claude/responses/response-NNN/` | conventional |

If a needed document doesn't fit any row, that's a signal — either it
belongs in a category Claude didn't recognize, or it's the seed of a
new category. **Don't quietly invent a new category;** propose it in
`notes.md` and let me ratify.

---

## 2. INDEX.md — Source of Truth

This section applies when the project maintains an `INDEX.md`. If
it doesn't yet, section 4.1 covers when to introduce one.

`INDEX.md` is the project's table of contents. Its job is to make the
drill-down pattern work: when the read-paths table in `CLAUDE.md`
points Claude at a project-specific doc, INDEX.md is how Claude finds
the file.

### 2.1 The non-negotiable rule

**A document isn't real until it's listed in `INDEX.md`.** Adding a
file to `claude/context/` without updating `INDEX.md` is the same as
not adding it at all — Claude won't find it via drill-down. Every
tarball that adds, moves, or removes a doc also modifies `INDEX.md`
in the same response. A project that wants this rule mechanically
enforced has Claude include the INDEX-coherence assertion in each
response's `validation.sh`; bale itself is project-agnostic and
does not enforce this.

### 2.2 Format

```markdown
# INDEX.md

> Drill-down map for this project's documentation.
> Updated whenever the inventory changes.

## Project state
- `INDEX.md` — this file.
- `STATE.md` — current project snapshot. Pull when the task depends
  on current state.

## Charter & product
- `context/charter-brief.md` — compressed charter. Default inclusion.
- `context/charter.md` — full charter. Pull when a decision hits
  scope or voice and the brief doesn't resolve it.

## Architectural decisions
- `context/adr/0001-vue-over-react.md` — framework choice.
- `context/adr/0002-no-pinia-yet.md` — state management deferral.

## Schemas
- `context/schemas/dist-api.openapi.yaml` — full API spec. Pull when
  touching API client code. Don't include wholesale; pull only the
  relevant sections.

## Explainers
- `context/surface-modes.md` — how the mockup's mode colors map to
  route segments.
```

INDEX.md does not list the global docs (`CLAUDE.md`, `TARBALL.md`,
`DOCS.md`, `CODE.md`) — those are injected by bale from its own
installation and are not part of the project's inventory.

### 2.3 Entry format

Every INDEX.md entry has three parts:

1. **Path** — relative to `INDEX.md`'s own location (typically
   `claude/`, so an entry like `context/charter-brief.md` resolves
   to `claude/context/charter-brief.md` from repo root).
   Backtick-quoted.
2. **One-line summary** — what the doc is, in the shortest honest
   form.
3. **When to pull this in** — the drill-down hint. *"Pull when X"* or
   *"Default inclusion"* or *"Pull only the relevant sections."*

Entries are grouped by category, matching the inventory table. Within
a category, order is logical (alphabetical for ADRs,
most-referenced-first for explainers).

---

## 3. STATE.md — The Project Snapshot

This section applies when the project maintains a `STATE.md`. If
it doesn't yet, section 4.1 covers when to introduce one.

`STATE.md` describes the project as it currently is. It is **not** a
log. It is **not** a changelog. It is a picture, edited (not
appended) every time the picture changes.

### 3.1 Sections

```markdown
# STATE.md

> Current snapshot of the project. Edited, not appended.

## What exists
[Current shape of the project: what's been built, what's in the
working tree, what dependencies are installed, what conventions are
in active use.]

## In flight
[What's being worked on but not yet landed. Items move from here to
"What exists" when finished, or get dropped if abandoned.]

## Open seams
[Known unfinished edges, places where the design is deliberately
incomplete, deferred decisions. Items leave this list when they're
either closed (move to "What exists") or escalated to an ADR.]

## Recent decisions
[Pointers to the most recent ADRs, reverse chronological, with
one-line summaries. Older ADRs live in adr/ and are reachable via
INDEX.md — they don't stay in STATE.md forever.]
```

### 3.2 Edit, don't append

The single rule that distinguishes STATE.md from a log:

- When something in "In flight" finishes, **move the line** into
  "What exists"; don't add a new line saying *"finished X on date Y."*
- When an "Open seam" gets closed, **delete the line** from "Open
  seams" and reflect the resolution in "What exists" or "Recent
  decisions." Don't strike it through or annotate.
- When a recent decision ages out of relevance, **remove it** from
  "Recent decisions." It's still in `context/adr/` for reference.

If Claude finds itself adding a dated section to STATE.md, stop. The
date goes in git. The change is captured in `notes.md` for that
session. STATE.md is the *current picture*, not the history of how
the picture changed.

### 3.3 Update cadence

STATE.md is updated in any tarball that meaningfully changes what the
project is. Adding a new top-level module, finishing a deferred seam,
closing a decision — these move state. Bug fixes and small internal
refactors usually don't.

When in doubt: if a future session would benefit from knowing this
change happened, update STATE.md. If the change is invisible from
outside the file that changed, skip it.

---

## 4. Adding a Document

Decision tree, in order.

### 4.1 Has the project crossed the threshold for this category?

Most categories don't engage until the project has enough scale to
need them. Adding the first doc of any category is also the moment
to introduce that category's machinery.

| Category | Introduce when |
|----------|----------------|
| `INDEX.md` | The project has ~3+ docs that need to be findable by topic. Below that, a one-line note in `STATE.md` or a top-level `README.md` is enough. |
| `STATE.md` | The project has state worth snapshotting — multiple modules in active development, an "in flight" surface, or deferred decisions ("open seams") accumulating in conversation. A single-script project rarely needs one. |
| ADRs | The first real decision lands that someone might want to reconsider later. "We chose framework X" doesn't need an ADR until there's a question of whether to switch. The ADR captures the moment the question was first answered. |
| Charter / charter-brief | Product direction is being discussed and Claude has been answering the same scope questions across multiple sessions. The brief is the consolidated answer. |
| Schemas | A data contract exists and is referenced by code (or by another doc). |
| Explainers | A non-obvious thing in the project has been explained more than once. Write it down so the next session doesn't redo the explanation. |

If a category's threshold hasn't been crossed, the answer to "should
I create this file?" is *no*, and the content lives somewhere else
(in the relevant file's comments, in a `notes.md`, in a section of
an existing doc) until the threshold is met.

If a category's threshold *has* been crossed but the file doesn't
exist yet, introducing it is part of the work — the manifest
declares both the new file (e.g., `INDEX.md`) and the content that
prompted introducing it.

### 4.2 Does this need to exist as its own file?

Most explanations don't. A clear comment in the relevant code, a
section in an existing doc, or an entry in `notes.md` covers most
cases. **A new file is the right answer only when:**

- The content has multiple distinct readers (someone reading topic A
  will skip topic B, or vice versa).
- The content will be referenced from multiple other docs.
- The content is large enough that embedding it would bury whatever
  doc it lives in.
- The content has a different lifecycle than its would-be host (e.g.
  an ADR is append-only; a charter is edited).

If none apply, add the content to an existing doc and update INDEX.md
if the existing doc got a new section worth pointing to.

### 4.3 Which category does it belong to?

Use the inventory table in section 1. Most new docs are:

- **An ADR** — a decision was made. Use ADR format (section 5).
- **An explainer** — a non-obvious aspect of the project needs
  written explanation. Goes in `context/`.
- **A schema** — a data contract. Goes in `context/schemas/`.

If it doesn't fit any category, surface that in `notes.md` and let me
ratify a new category before inventing one.

### 4.4 What's the path and name?

Per the inventory table:

- Project-state docs: `ALL_CAPS.md` at `claude/`.
- ADRs: `claude/context/adr/NNNN-lowercase-hyphenated.md`, where
  `NNNN` is the next sequential number.
- Schemas: `claude/context/schemas/lowercase-hyphenated.<ext>`.
- Explainers: `claude/context/lowercase-hyphenated.md`.

### 4.5 Update INDEX.md (if the project has one)

When `INDEX.md` exists, always update it. Same tarball, same
response, same manifest. If §4.1 just decided to introduce
`INDEX.md`, this is when it gets created — with the new doc as
one of its first entries.

### 4.6 Update STATE.md, if relevant

If the new doc reflects a state change (an ADR closing an open seam,
an explainer of a newly-built module), STATE.md gets updated too —
when STATE.md exists. If §4.1 decided to introduce STATE.md, this
is when it gets created.

---

## 5. ADR Format

ADRs are append-only records of decisions. Each ADR is one decision,
captured at the moment it was made. When a decision is overturned,
write a new ADR that supersedes it; **never edit the old one.**

Standard format:

```markdown
# ADR-0007: Defer state management until module count exceeds 8

- **Status:** Accepted
- **Date:** 2026-05-12
- **Supersedes:** —
- **Superseded by:** —

## Context

[The situation that prompted the decision. What was the question?
What were the options on the table? What constraints applied?]

## Decision

[The decision itself, in plain language. What did we choose, and
what's its scope?]

## Consequences

[What this decision enables, what it forecloses, what becomes
harder, what becomes easier, what we'll need to revisit later.]

## Notes

[Optional. Anything that didn't fit above.]
```

Status values:

- **Proposed** — written up but not yet ratified.
- **Accepted** — current.
- **Superseded** — replaced by a later ADR. The "Superseded by"
  field points to it.
- **Deprecated** — no longer relevant but not replaced. Rare.

The newest 3–5 ADRs appear in `STATE.md`'s "Recent decisions" section
by reference. Older ones live only in `adr/` and INDEX.md.

---

## 6. Splitting a Document

### 6.1 Signals that a split is due

- The doc covers **multiple distinct topics that don't share
  readers.** Someone reading for topic A has to scroll past topic B.
- The doc contains **drill-down content** — schemas, contract
  details, mechanics — that's not always needed but is always loaded
  with the doc.
- The doc is **getting hard to scan.** Sections start needing their
  own subsections.

Length alone isn't a signal. A 600-line doc on one tight topic is
fine. A 200-line doc that mixes philosophy and mechanics isn't.

### 6.2 The split pattern

1. **Identify the seam.** Usually between *when* something engages
   and *how* it works; or between *what* a thing is and *the schema*
   for it; or between *philosophy* and *reference*.
2. **The lighter doc keeps the trigger.** It tells Claude *when* to
   read the heavier doc. It does not duplicate the heavier doc's
   contents.
3. **The heavier doc opens with its own META + INDEX.** *"This file
   is open because X happened. The rules below are authoritative."*
   This is how the heavier doc stands alone.
4. **Cross-reference, never duplicate.** The lighter doc points to
   the heavier; the heavier points back for *why* questions. Each
   rule has one home.
5. **Update INDEX.md** with the new doc, its summary, and its
   when-to-pull hint.
6. **Mention the split in `notes.md`** of the tarball that does it.

### 6.3 When a split would be wrong

- The two halves would always be read together. No drill-down
  benefit, just two files instead of one.
- The proposed lighter doc would be too thin (under 50 lines) and not
  gaining anything by being separate.
- The seam isn't real. If Claude struggles to decide which file a
  given rule goes in, the seam is wrong and the doc shouldn't split
  yet.

---

## 7. Pruning a Document

Documentation that no longer pays for itself should leave, the same
way unused code does. Pruning is the easiest place to do quiet damage
— removing something that turns out to have been load-bearing — so
it's always explicit, never silent.

### 7.1 What's prunable

- **Stale explainers** — describe something that no longer exists, or
  whose meaning has shifted past recognition.
- **Outdated schemas** — replaced by a newer version, no remaining
  importers.
- **Old session notes** — far enough in the past that nothing
  references them and the project has moved past what they describe.
- **Duplicate content** — same explanation in two places; consolidate,
  remove the weaker copy.

### 7.2 What's not prunable

- **ADRs. Ever.** They are append-only history. A decision that was
  overturned is marked `Superseded` with a pointer to its
  replacement; never deleted, never edited.
- **Active session notes** — recent notes, or anything referenced by
  `STATE.md`'s "Recent decisions."
- **Charter documents** — these get edited, not pruned. If the
  charter shifts, the shift is captured in a new ADR.

Lack of recent reference is **not** sufficient on its own. Some docs
are infrequently needed but critical when they are.

### 7.3 Archive vs. delete

Default to archive. Delete only when content has zero remaining value
(scratch files committed by accident, fully-superseded docs whose
unique content was already consolidated).

- **Archive** — move to `claude/archive/`, remove from INDEX.md's
  main body. Optionally list under an `## Archived` appendix with a
  one-line note on why and when.
- **Delete** — actually remove from the repo. The manifest `reason`
  must explain why the content has zero future value, not just no
  current use.

When in doubt, archive. The cost of an archive is near zero; the cost
of a wrong delete is reconstructing the knowledge.

### 7.4 Procedure

1. **List candidates in `notes.md`** with the criterion for each.
   Don't act yet.
2. **Check for backlinks.** Search the docs and codebase for
   references. A doc with live references is not prunable until those
   references are addressed.
3. **Consolidate first.** Move any unique content into a doc that's
   staying.
4. **Choose archive or delete** per candidate.
5. **Update INDEX.md** — remove the entry; optionally list under
   `## Archived`.
6. **Update STATE.md** if pruning is material (e.g. closes a tracked
   item under "Open seams").
7. **Manifest entries** — every pruned file gets its own `action:
   deleted` entry with a `reason` distinguishing archive from delete.
   The actual file removal happens via `apply.sh`.

### 7.5 When to prune

- **Periodic sweeps** on a cadence; whole session dedicated to
  pruning, no feature work mixed in.
- **On-demand** — I ask for a cleanup pass.
- **Opportunistic** — during a tarball already touching a doc, an
  obviously stale neighbor gets removed in the same response. Always
  declared in the manifest.
- **Not during active feature work** — pruning while building risks
  removing something needed twenty minutes later.

---

## 8. Naming Conventions

Strict enough to be predictable; loose enough not to be a tax.

- **Project-state files** — `ALL_CAPS.md`. Limited set:
  `INDEX.md`, `STATE.md`. (Global docs `CLAUDE.md`, `TARBALL.md`,
  `DOCS.md`, `CODE.md` follow the same convention but live in the
  bale tool, not in the project.)
- **Content files** — `lowercase-hyphenated.md`. Everything in
  `context/` that isn't an ADR or a schema.
- **ADRs** — `NNNN-lowercase-hyphenated.md`, numbered sequentially
  starting at 0001. Never renumbered.
- **Schemas** — `lowercase-hyphenated.<format>` (`.openapi.yaml`,
  `.schema.json`, etc.).
- **Session artifacts** — `request-NNN`, `probe-NNN`, `response-NNN`,
  3-digit zero-padded, sequential per project.

If tempted to invent a new naming pattern, **don't.** Use the closest
existing pattern and note the awkwardness in `notes.md`.

---

## 9. Hard Rules

Bale is project-agnostic and does not enforce doc-inventory rules
itself. The mechanical checks in the table below run in the
response's `validation.sh` — Claude includes the corresponding
assertions per-session for projects that adopt the DOCS.md
workflow. The universal bale-enforced rules (manifest agreement,
sha256, reason populated, path safety, out-of-scope, `apply.sh`
reconciliation) live in `TARBALL.md` section 8.

| Rule | Type | Enforcement |
|------|------|-------------|
| INDEX.md lists every doc — a doc isn't real until INDEX lists it | contract | response's `validation.sh`: every doc in `files/` has an INDEX entry; every INDEX entry resolves to a file |
| STATE.md is edited, not appended — no dated sections | policy | review |
| ADRs are append-only — old ADRs are superseded, never rewritten | contract | response's `validation.sh`: modifications to existing ADR files are rejected unless the only changes are flipping `Status` to `Superseded` and populating `Superseded by` |
| Cross-reference, don't duplicate — every rule has one home | policy | review |
| Pruning is always declared — every removal distinguishes archive from delete in its `reason` | contract | response's `validation.sh`: deletes have non-empty reasons matching one of the two patterns |
| Don't invent doc categories silently — surface in `notes.md` first | policy | review |
| New ADR numbers are sequential and never reused | contract | response's `validation.sh`: ADR filename N is the max existing number + 1 |

Rule labels follow `CLAUDE.md` section 6. A project that wants these
rules enforced asks Claude to include the corresponding assertions
in each response's `validation.sh`; a project that doesn't adopt
the DOCS.md inventory simply omits them. Claude should surface
policy concerns in `notes.md` precisely because mechanical checks
won't catch them.

---

## 10. Hard Nots

- **Not a wiki.** Every doc has a job and a trigger condition. Pages
  don't accumulate just because they could.
- **Not append-everything.** Most docs edit; only ADRs and session
  notes are append-only.
- **Not over-architected.** Build a new doc category when you need
  it, not when you anticipate needing it.
- **Not a changelog system.** Git is the changelog. Session notes are
  the per-session record. STATE.md is the current picture.

---

## 11. The Meta-Principle

Documentation is treated like code. It earns its place — a doc that
isn't read isn't worth maintaining. It gets refactored — when it
grows mixed-purpose, it splits. It gets deleted — when it's stale and
isn't serving any session, it goes.

The check for *"should this become a doc?"* is: will a future session
reference it, and would referencing it be faster than rebuilding the
knowledge? If yes, write it. If unsure, write it as a section in an
existing doc; whether it deserves its own file can wait until it's
been read a few times.
