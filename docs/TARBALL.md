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
The defensive case — a hand-rolled request where it's missing —
Claude pauses and asks; a malformed tarball is more expensive than
a paused session.

---

## INDEX

### Read paths

| Situation | Load |
|-----------|------|
| Producing a normal response tarball | Sections 1, 2, 5, 7 |
| Returning a probe instead of a response | Sections 1, 2, 4 |
| Handling a request tarball I received | Sections 1, 2, 3 |
| Writing or debugging `validation.sh` | Sections 5, 7 |
| Writing or debugging `apply.sh` | Section 5.1.1 |
| Hard rules / what counts as a violation | Sections 8, 9 |
| Quick reference at session end | Section 10 |
| Smallest viable response (sanity check) | Section 6 |

---

## 1. Conventions

- **Session IDs.** `YYYY-MM-DD-<slug>-NNN`, e.g.
  `2026-05-12-vue-scaffold-001`. The slug is short and kebab-cased.
  NNN is a per-day monotonic counter maintained by bale.
- **Artifact directories.** `request-NNN/`, `response-NNN/`,
  `probe-NNN/` use the same NNN as the session ID, zero-padded to
  three digits. A response is numbered to match the request it
  answers; a probe shares the session's NNN.
- **Examples are examples.** Schemas below reference Vue/Vite/etc. to
  make shapes concrete. They are illustrative, not normative.
  Substitute the project's actual stack.

---

## 2. Three Artifacts

| Artifact | Direction | When |
|----------|-----------|------|
| Request tarball | me → Claude | start of a tarball-mode session |
| Probe | Claude → me | only when Tier 1+2 reading left a real gap |
| Response tarball | Claude → me | every tarball-mode response |

---

## 3. Request Tarball

### 3.1 Shape

```
request-NNN/
  manifest.json        # structured session metadata (required)
  CLAUDE.md            # injected by bale
  TARBALL.md           # injected by bale
  DOCS.md              # injected by bale
  context/             # everything the user chose to include
    <project files and any project docs the user named>
  README.md            # optional; user's voice beyond the manifest's `goal` field
```

The first four slots are reserved for bale-injected global docs and
the manifest. Everything else the user wants Claude to see —
including project-specific docs like `INDEX.md`, `STATE.md`, ADRs,
schemas, and prior probe output — lives under `context/`. No top-
level slots are reserved for project docs; bale is project-agnostic.

`README.md` is optional. Include it only when the user has prose
worth keeping that doesn't fit the manifest's `goal`, `constraints`,
or `out_of_scope` fields — typically when the session has a story
that wouldn't reduce cleanly to structured fields. Most sessions
will skip it; the wizard offers `$EDITOR` for the user to opt in.

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
  ]
}
```

Field semantics:

- **`goal`** — one sentence. If it doesn't fit in one sentence, the
  scope is wrong.
- **`constraints`** — things I commit to up front. Claude stays
  within them or surfaces a conflict in `notes.md`.
- **`out_of_scope`** — explicit list of *near-by* concerns Claude
  should not address. The list exists because absence is harder to
  reason about than presence.
- **`expects_probe`** — `yes` forces a probe before any build work.
  `no` forbids probing this session (see 3.3). `claude-decides`
  (default) means Claude uses judgment.
- **`context_included`** — declarative list of what's in `context/`.
  If Claude needs something not listed, it checks `INDEX.md`, then
  names it in the response (either in a probe request or in
  `notes.md` if Claude proceeded with an assumption).

### 3.3 When `expects_probe: no` collides with a real gap

If the request forbids probing but Claude finds an environment-
specific gap documentation can't fill, Claude does not probe and does
not silently guess. Claude either:

1. **Stops and asks in chat** — if the gap is small enough to resolve
   inline.
2. **Proceeds against the most plausible assumption** — names the
   assumption explicitly in `notes.md` and flags it as the first
   thing for me to check on review.

The `no` setting is honored as a hard constraint; the assumption is
honored as a recoverable risk.

---

## 4. Probe

### 4.1 When a probe engages

Return a probe instead of a response when, and only when:

1. The request's Tier 1 + Tier 2 reading left a gap Claude can't fill
   from documentation alone.
2. The gap is environment-specific or working-tree-specific — facts
   that documentation couldn't capture (tool versions, current file
   contents, install state, what shell is actually available).
3. Proceeding without the gap filled risks a confidently wrong
   answer.

If the gap is conceptual or scope-related, that's a conversation in
chat, not a probe.

### 4.2 Probe shape

Probes are session-scoped only. They are not archived in the project
file structure; the script is pasted into the user's terminal and
the output is pasted back into the next message. No `claude/probes/`
directory, no bale subcommand for probes.

The probe Claude returns is a fenced script in chat:

```bash
#!/usr/bin/env bash
# What this probe asks, why, and what it writes.
# Only writes to ./probe-output/. Read-only outside that dir.

mkdir -p probe-output
# checks here, each line logged to stdout
```

`probe.ps1` is conditional. Most environments (Linux container,
macOS, WSL) run the bash variant natively. Offer a PowerShell
variant only when the request or `STATE.md` indicates Windows-native
execution.

The probe's preamble in chat explicitly lists every location the
probe will write to (should only be `./probe-output/`) and every
external tool it invokes. No surprises.

### 4.3 Probe script rules

- **Read-only outside `./probe-output/`.** No writes anywhere else.
  No installs. No network calls unless explicitly justified in the
  preamble and gated behind a flag.
- **Self-contained.** Uses only tools that exist everywhere: `ls`,
  `cat`, `find`, `git`, `node --version`, `tree` (with `find`
  fallback). If a tool is missing, degrade gracefully and record the
  gap in `probe-output/meta.json`.
- **Idempotent.** Running it twice gives the same output (modulo
  timestamps).
- **Environment-aware.** Detects shell, OS, and container/host
  classification and records it in `meta.json`. If the environment
  can't be classified, the probe records that fact rather than
  guessing.
- **Copy-pasteable.** The script body should be pasteable into a
  terminal as-is. No argument parsing required for the happy path.
- **Secrets-aware.** Skips `.env*`, `*.pem`, anything matching common
  secret patterns. Records *presence* (`OPENAI_API_KEY: set`), never
  values.
- **Logged.** Every step prints a line: `[probe] checking node…
  found v20.11.0`. Silent operations are bugs.

### 4.4 Probe output shape

The actual contract is `meta.json` plus whatever files the probe
collected, declared in `meta.json`. The shape below is illustrative
(Node-flavored); the specific file set varies by project type.

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

I paste `probe-output/` contents into the next message as text, or
include the directory in the next request tarball if it's large.

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
  next-prompt.md       # optional; include when there's a follow-up queued
```

`files/` mirrors the project structure from the repo root. If Claude
touches `src/components/Foo.vue` and `package.json`, they appear at
`files/src/components/Foo.vue` and `files/package.json`. Apply is
then `cp -r response-NNN/files/. <project>/` — no path translation
required.

The three optional artifacts (README, notes, next-prompt) follow the
stub-averse principle: include them when there's content; omit them
otherwise. Absence carries meaning — no extra prose, no surprises,
no follow-up. Bale shows them in the apply walkthrough if present
and stays silent if absent.

**File changes go inside the tarball, not alongside it.** When the
response delivers code or content changes, those changes belong in
`files/` and `apply.sh`, declared in the manifest — not pasted into
chat as a preview or as a courtesy copy. Pasted files aren't
applicable: the user can't `cp` from a chat snippet into the project,
and the tarball would have to be extracted to compare anyway, so the
duplicate is pure friction.

This rule is narrow on purpose. Tarball mode does not mean *only*
tarballs come out of it. A probe (section 4) is the right response
when Tier 1+2 reading left an environment-specific gap. A
conversational reply is the right response when a scope question
needs answering, a concern needs surfacing, or a clarification needs
asking before any code lands. The constraint is on the *deliverable's
shape*: when code is the response, the tarball is the response,
without a parallel copy in chat.

### 5.1.1 apply.sh

`apply.sh` ships operations beyond the cp-and-overwrite that `files/`
already provides — primarily deletes. Renames are decomposed into a
`created` entry under `files/` (the new path with its full content)
plus an `rm` of the old path in `apply.sh`; `apply.sh` itself never
performs `mv` operations, because the commit step in bale is driven
per-manifest-entry from `changes[]`, not from a tree-level diff.
Bale runs `apply.sh` in a staging copy of the project before
`validation.sh`, then verifies the resulting state matches the
manifest: every file removed from staging must be in
`manifest.changes` as `action: deleted`; every file added must be
`action: created`; every modified file's sha256 must match. A
malformed `apply.sh` that touches files not declared in the manifest
fails verification and the tarball is rejected.

`apply.sh` is minimal — only the operations the cp-mirror can't
express. A session with no deletes or renames ships a no-op script:

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
      "why": "test setup not yet decided — see next-prompt.md"
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
    "vue-tsc": "pass",
    "vite build": "pass"
  }
}
```

Field semantics:

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
  matches the locked session.
- **`corrects`** — optional, default `null`. If this response is a
  re-attempt at a previous response whose validation failed or
  whose application revealed a problem, this is the session ID of
  the response it replaces (e.g., `"2026-05-10-foo-014"`). The
  replaced response's tarball stays in `claude/responses/` as
  history; the pointer is how someone reading later traces what
  happened.

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

`claims` covers project-level checks (lint, typecheck, build, tests)
only. The mechanical checks Claude wrote the manifest for (manifest
consistency, file syntax) are tautological — a `pass` claim adds no
information and they're omitted.

A claim disagreeing with the verdict doesn't reject the tarball; it's
flagged in validation's end-of-run report. The pattern of
disagreements over time is the signal worth catching — it tells me
where Claude's calibration is off, and which checks I should be
tightening.

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

If a session has any of the above, write the file. If a session is
small enough that none of the above apply, don't write a stub.

### 5.5 next-prompt.md (optional)

If more work is queued, include `next-prompt.md` with the literal
prompt I should paste into my next message — including which files
to include in the next request tarball and whether a probe should
run first.

If nothing's queued, omit the file. Absence means *"no follow-up;
this session stands alone."*

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

`deferred` and `claims` are both empty — nothing was held back, and
no project-level checks run for a markdown typo. `validation_will_run`
covers only what `validation.sh` actually does for this change (file
syntax). `apply.sh` is the no-op script. `README.md`, `notes.md`, and
`next-prompt.md` are absent — nothing surprising happened, no
follow-up is queued, and the manifest's `summary` field covers what
the response delivers.

The protocol still applies. The floor is the floor.

---

## 7. Validation

Two validations run on every response tarball, and they answer
different questions.

**Bale's pre-flight** (the full list in `BALE.md` section 11, also
the contract rules in section 8 below) answers *"is this tarball
well-formed?"* — manifest schema, sha256 agreement, path safety,
out-of-scope, `apply.sh` reconciliation. It runs first and rejects
malformed tarballs before any other work; if it rejects,
`validation.sh` never runs.

**The response's `validation.sh`** answers *"do the changes do what
Claude claims they do?"* It is Claude's per-session hypothesis test,
written fresh for each response — not a fixed project pipeline.
Claude chooses what to invoke based on what this session actually
touched: typically the project's lint, typecheck, and build against
the modified files, plus session-specific assertions for behaviors
that changed. The project's CI plays the regression-prevention role
after the bale is merged; `validation.sh` does not duplicate it.

### 7.1 The staging-copy approach

Validation never writes to the real project. The full pipeline:

1. Bale creates a staging directory (default: `<repo>/.bale/staging/`,
   configurable via `--staging-dir`).
2. Bale copies the current project state into staging.
3. Bale applies `files/` over the staging copy, then runs `apply.sh`
   in staging to handle deletes.
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
   external tooling.

If a check's tool isn't installed, it prints `[SKIP] <check>: <tool>
not found`. Never silently passes. Never installs anything.

### 7.3 Claim/verdict reconciliation

After checks 2-5 run, validation compares each verdict against
`manifest.claims`. Bale places the response manifest at
`staging/.bale-manifest.json` before invoking `validation.sh`, so
the script can read the claims and produce the reconciliation block.
The end-of-run summary includes a `claims` block:

```
claims vs verdict:
  eslint:     claim=pass    verdict=pass    [agree]
  vue-tsc:    claim=pass    verdict=fail    [DISAGREE]
  vite build: claim=pass    verdict=skip    [n/a]
```

Disagreements (`claim=pass, verdict=fail` or `claim=fail,
verdict=pass`) are reported but don't change the exit code — they're
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

---

## 8. Hard Rules (Tarball-Specific)

Contract rules — the mechanical checks bale enforces — are listed in
**BALE.md section 11**, which is canonical. The rules below are
*policy*: caught at review, not by bale.

| Rule | Enforcement |
|------|-------------|
| The tarball is the contract — no side commands, no pasted snippets, no hand-edits | review |
| Validate before apply, always | my discipline |
| Tarballs are immutable once delivered | my discipline |
| `validation_will_run` is honest and complete | review |
| Tarball mode without `TARBALL.md` loaded — pause and ask | Claude's own check at the start of a response |
| Probe is read-only outside `./probe-output/` | probe self-check + my review |
| `apply.sh` operations limited to deletes and other manifest-declared file ops — no `mv`, no installs, no builds | review (with bale's post-run reconciliation in BALE.md 11 row 18 catching tree violations) |

Rule labels follow `CLAUDE.md` section 6. Claude should surface
policy concerns in `notes.md` precisely because mechanical checks
won't catch them.

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

### 10.1 Building a response tarball

1. Confirm `CLAUDE.md` and `TARBALL.md` are in the request, or pause
   and ask.
2. Plan: list every file that will change, decide deferrals up front,
   decide what to claim for each project-level check.
3. Build `files/` mirroring the project tree (when there are
   created/modified entries).
4. Build `manifest.json` with reasons, sizes, sha256s, deferrals,
   `validation_will_run`, and `claims`.
5. Write `apply.sh` for deletes (or a no-op script if none).
6. Write `validation.sh` honoring the contract in section 7.
7. Optionally write `notes.md` if there are surprises, decisions, or
   `unknown` claims to surface. Skip the file otherwise.
8. Optionally write `next-prompt.md` if work is queued. Skip the file
   otherwise.
9. Optionally write `README.md` if there's color beyond
   `manifest.summary` worth keeping. Skip otherwise.
10. Tar: `tar -czf response-NNN.tar.gz response-NNN/`.

### 10.2 Returning a probe instead

1. Confirm the gap is real and environment-specific, not conceptual.
2. Write the probe script inline in chat (bash; PowerShell variant
   if Windows-native is in play).
3. List in the chat preamble what the probe writes to (only
   `./probe-output/`) and every tool it invokes.
4. Stop. The probe's output is needed before any response can be
   built.
