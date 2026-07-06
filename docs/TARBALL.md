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
| Returning a bailout response (`CLAUDE.md` §11 triggered) | Sections 1, 2, 5.6, 5.7, 5.8 |
| Handling a request tarball I received | Sections 1, 2, 3 |
| Authoring a request, or citing a `bale pack` rescope (`CLAUDE.md` §11.2) | Section 3.4 |
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
  CODE.md              # injected by bale
  context/             # everything the user chose to include
    <project files and any project docs the user named>
  README.md            # optional; user's voice beyond the manifest's `goal` field
```

The first five slots are reserved for bale-injected global docs and
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

### 3.4 Authoring a request with `bale pack`

`bale pack` is the command that produces a request tarball — the §3.1
shape, with a `manifest.json` (§3.2) assembled from its flags. It's
documented here so its callers can cite a real command instead of
guessing. By default that caller is Claude: authoring `bale pack`
commands is Claude's responsibility (`CLAUDE.md` §4), and Claude
emits a runnable one in exactly one place — the rescope offer, when
the pre-flight scope check (`CLAUDE.md` §11.2) decides a goal needs
splitting. That emission is pre-work and conversational: the session
has declined to build anything, so the command is a scoping proposal
the architect reads and fires deliberately, not an artifact riding
beside reviewed output. Post-work is the opposite case — once a
session has landed work, its follow-up suggestions flow as prose
Proposals in `notes.md` (§5.4.1), never as a runnable command; §5.5
carries the reasoning for that line. The architect authoring a
session by hand is fully supported, with the same flags and the same
single-line form — the normal case for sequencing packs the architect
composes from a response's proposals.

The flags below are the stable surface; each maps to a manifest field
or a packing behavior:

| Flag | Maps to / does |
|------|----------------|
| `goal` (positional) | `manifest.goal`. One sentence — if it needs two, the scope is wrong (§3.2). |
| `--slug <kebab>` | The `<slug>` in `session_id` (`YYYY-MM-DD-<slug>-NNN`); bale assigns the date and the `NNN` counter. |
| `--include PATH...` | Adds files/dirs under `context/` and lists them in `manifest.context_included`. Repeatable, or space-separated. |
| `--exclude PATTERN...` | Prunes paths an `--include` would otherwise pull in (e.g. a vendored subdir). |
| `--constraint TEXT` | Appends one entry to `manifest.constraints[]`. Repeatable — one flag per constraint. |
| `--out-of-scope TEXT` | Appends one entry to `manifest.out_of_scope[]`. Repeatable — one flag per item. |
| `--expects-probe {yes\|no\|claude-decides}` | Sets `manifest.expects_probe` (§3.2; default `claude-decides`). |
| `--no-edit` | Skips the optional `$EDITOR` step for `README.md` (§3.1) — pack non-interactively with no prose beyond the structured fields. |
| `--max-*` | A family of guard-rail caps (e.g. on included-file count or total context size) that make bale refuse an oversized pack rather than ship it. The specific caps are bale's; this reference does not enumerate them. |
| `--force` | Override the `--max-*` guard rails when the architect knowingly wants a pack past a cap. |

**Commands are single-line.** Every `bale pack` invocation — the
architect's, or the one Claude emits in a rescope offer (`CLAUDE.md`
§11.2) — is written as one line with no backslash continuations, so
it pastes into a terminal directly. Repeatable flags repeat inline on
the same line; they do not wrap.

**No backticks in the goal string.** The goal is a double-quoted shell
argument, and double quotes do not protect backticks: the shell treats
text between backticks as command substitution and runs it before
`bale` ever sees the goal. Wrapping a code symbol in backticks — the
reflex when writing about code — makes the shell try to execute that
symbol as a command and pack whatever it prints, usually an error.
Name code symbols in plain prose inside the goal (*the useAuth hook*,
not the backticked form); `$(...)` and an unescaped `$` carry the same
hazard. This is why none of the example goals here use backticks.

A basic pack:

```
bale pack "Add a debounced search box to the catalog page" --slug catalog-search --include src/components/Catalog.vue --include src/composables --constraint "no new dependencies" --expects-probe no
```

A rescope pack — the first session of a split the pre-flight check
proposed, as Claude would emit it in a §11.2 offer, with the deferred
half named in `--out-of-scope`:

```
bale pack "Migrate the auth module to the new token format — types and store only" --slug auth-token-types --include src/auth/types.ts --include src/auth/store.ts --out-of-scope "endpoint wiring" --out-of-scope "tests for the endpoint layer" --expects-probe no
```

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
```

`files/` mirrors the project structure from the repo root. If Claude
touches `src/components/Foo.vue` and `package.json`, they appear at
`files/src/components/Foo.vue` and `files/package.json`. Apply is
then `cp -r response-NNN/files/. <project>/` — no path translation
required.

The two optional artifacts (README, notes) follow the stub-averse
principle: include them when there's content; omit them otherwise.
Absence carries meaning — no extra prose, no surprises, no proposal
queued. Bale shows them in the apply walkthrough if present and
stays silent if absent. (`next-prompt.md`, a third optional artifact
in earlier versions of this contract, is retired — §5.5.)

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

A **bailout** response (§5.6) has a distinct shape: no `files/`,
no-op `apply.sh` and `validation.sh`, plus mandatory `handoff.md`
and `diagnostics.json`. It is the response Claude returns when the
session can't fit the goal within its context budget — see
`CLAUDE.md` §11. Bale's apply step treats bailouts as informational
rather than applicable.

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
per file. Forgetting the chmod is a confidently silent breakage:
content lands correct, validation that only inspects content can
pass straight past it, and the next invocation of the script meets
`Permission denied`. The responsibility sits on Claude precisely
because the overlay can't infer intent — a script and a config file
look the same to a copy. The validation-side guard that catches a
forgotten `chmod` — an exec-bit assertion in `validation.sh` — is
§7.7.

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
- **`response_kind`** — `"normal"` (default) for an ordinary
  response. `"bailout"` when Claude could not fit the goal in this
  session's context budget (see `CLAUDE.md` §11). Bailout responses
  follow the distinct shape in section 5.6.

### 5.2.1 Computing size_bytes and sha256

`size_bytes` and `sha256` are computed, never transcribed. A
hand-written hash is wrong with near-certainty, and bale's pre-flight
rejects any tarball whose manifest sha256 disagrees with the bytes
under `files/` (§7) — so a guessed value doesn't save a step, it
guarantees a bounced tarball. Run the values off the real files.

From inside the response directory, this emits the manifest path,
size, and hash for every file under `files/` — exactly the `created`
and `modified` entries, in the `path` form `changes[]` expects:

```bash
cd response-NNN
find files -type f | sort | while read -r f; do
  printf '%s\t%s\t%s\n' \
    "${f#files/}" \
    "$(wc -c < "$f")" \
    "$(sha256sum "$f" | cut -d' ' -f1)"
done
```

`${f#files/}` strips the mirror prefix, so `files/src/Foo.vue` reports
as `src/Foo.vue`, paste-ready into `changes[].path`. On a host without
`sha256sum` (macOS, say), use `shasum -a 256` in its place.

`deleted` entries have no file under `files/`, so the snippet never
emits them: set their `size_bytes` to `0` and `sha256` to `null` by
hand per §5.2. Those two literals are the only size or hash values
ever written rather than computed.

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

A `claims` key is not free text: it is the **canonical identifier**
of the check it predicts, and that identifier is the check's
`validation_will_run` entry. The two must verbatim-match — same
characters, same spacing — so the entry string is the single
canonical name a check is known by, reused unchanged as the `claims`
key and again as the verdict label §7.3 reconciles against. That one
shared string is what makes the reconciliation well-defined: a claim
and its verdict pair because they name the check identically, not
because anything matches a paraphrase. A `claims` key with no
verbatim match in `validation_will_run` is unpairable — a prediction
about a check the manifest never says will run.

The match is one-directional, and the scoping is the point. Every
`claims` key must appear in `validation_will_run`, so
`set(claims) ⊆ set(validation_will_run)`; the converse does not hold.
`validation_will_run` also lists the mechanical checks (file syntax,
manifest consistency) the paragraph above excludes from `claims`, and
those entries therefore stand as run-but-unclaimed — correct, not a
gap. So the invariant binds only the claimable project-level checks:
claimed checks are always a subset of run checks, never a superset.
This subset relation is what §10.1 self-checks before packing and
`CLAUDE.md` §11.6 re-derives after a compaction.

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
- Follow-up work worth suggesting — as a Proposals section (§5.4.1).

If a session has any of the above, write the file. If a session is
small enough that none of the above apply, don't write a stub.

#### 5.4.1 The Proposals section

Workers discover things at completion that a top-down planner cannot
know: a seam visible only from inside the code, an out-of-scope fix
worth doing, a test deferred and exactly why. When a session surfaces
follow-up work worth suggesting, `notes.md` carries it under a
`## Proposals` heading. Each proposal is a short block:

- **What** — the suggested follow-up, in one or two sentences.
- **Why** — the rationale, grounded in something this session
  actually saw. A proposal without a reason is a wish, not a signal.
- **Scope hints** — optional: the files or seams involved, and any
  ordering dependency on other work ("only after X lands").

Proposals are prose suggestions with rationale, **never ready-to-run
commands** — no `bale pack` line, no literal paste-this text. The
planner (the architect today, an orchestrator later) reads proposals
as *input*, decides sequencing, and authors its own pack commands
(§3.4) from its own understanding. This is deliberate: the worker
that built a session does not frame the scope or the includes of the
session that follows it — §5.5 carries the full reasoning.

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
do not ship `next-prompt.md`; Claude does not produce it. The section
number is kept so older cross-references stay resolvable.

The artifact carried "the literal text to paste next" — usually a
ready-to-run `bale pack` command for session N+1, authored by the
worker that had just built session N. That shape had two problems.
It invited blind firing: the command arrived inside a response
tarball at apply time, surfaced in the walkthrough beside a diff and
a PASS banner — exactly the moment a satisfied reviewer is primed to
paste and go. And it let the entity under review frame the scope and
includes of the follow-up that extends or judges its own work — a
soft version of the self-oracle problem. Sequencing authority belongs
to the planner: deciding what's next is the architect's call, with
Claude's suggestion (`CLAUDE.md` §4).

What survives is the channel, not the file. Worker-side discoveries
that a top-down planner can't know flow through `notes.md`'s
Proposals section (§5.4.1) as prose suggestions with rationale, never
runnable commands; the planner authors its own pack commands (§3.4)
from its own understanding, with the proposals as input.

The line this retirement draws is pre-work vs post-work, not command
vs no-command. Claude still authors `bale pack` commands (`CLAUDE.md`
§4) and still emits a runnable one in exactly one place: the
pre-flight rescope offer (`CLAUDE.md` §11.2). That emission has
neither hazard above — it is pre-work, so the session has built
nothing the command could frame, and it arrives as the whole point of
a conversational reply, so the planner cannot fire it without reading
it. Once work has landed, follow-up flows only as prose proposals.
An orchestration layer consuming rescope offers should re-derive the
command from the proposed seam rather than fire the worker's verbatim
— doctrine for when an orchestrator exists, not a change to the human
path, which needs the paste-ready command.

Transition tolerance: response tarballs produced before the
retirement may still contain `next-prompt.md`. Bale's apply
walkthrough tolerates them — the body is surfaced, labeled deprecated
— so pre-retirement archives stay reviewable. Nothing new ships the
file.

The retirement does not touch bailouts. Queued follow-up after a
*successful* session was this artifact's job; unfinished work from a
*bailed* session was always `handoff.md`'s (§5.7), and that path is
unchanged.

### 5.6 Bailout response

A bailout response is what Claude returns when `CLAUDE.md` §11
triggers have fired — the goal won't fit in this session's context
budget and Claude is handing off to a fresh session instead of
pushing through. The bailout artifact is the safety net for
context-budget exhaustion; the *why* lives in `CLAUDE.md` §11.

#### 5.6.1 Shape

```
response-NNN/
  manifest.json        # response_kind: "bailout"
  apply.sh             # no-op
  validation.sh        # no-op
  handoff.md           # required: instructions for the next Claude (§5.7)
  diagnostics.json     # required: structured diagnostics (§5.8)
  files/               # absent or empty
  notes.md             # optional, addressed to me (not the next Claude)
```

`response_kind: "bailout"` in the manifest is the canonical marker.
Bale's apply step branches on it: instead of applying changes, it
displays the handoff summary and prompts the user to run
`bale handoff <response-NNN>` to package a fresh session.

`README.md` is absent in bailouts — `handoff.md` carries the
forward-looking content for the next Claude, and `notes.md` (if
present) carries the user-facing commentary. (`next-prompt.md` is
retired everywhere, §5.5.)

#### 5.6.2 Manifest specifics for bailouts

When `response_kind: "bailout"`:

- **`summary`** — one paragraph: what was attempted, which trigger
  fired (per `CLAUDE.md` §11.3), what the handoff prescribes for
  the next session.
- **`changes`** — empty array. Nothing changed.
- **`deferred`** — empty. Deferred work lives in `handoff.md`'s
  prescription, not as a flat list.
- **`validation_will_run`** — empty array. No checks to run.
- **`claims`** — empty object. Nothing to claim.

The `responds_to` field still names the request this answers. The
new session that the user packs after running `bale handoff` will
have its own fresh `session_id` (same slug, new date+NNN), and its
`depends_on.previous_response` will point at the bailout.

#### 5.6.3 Apply-time UX (contract for bale)

When bale's apply step encounters `response_kind: "bailout"`, it:

1. Prints a clear banner identifying the response as a bailout. No
   changes will be applied; do not run `apply.sh` or
   `validation.sh` against the project.
2. Prints the `manifest.summary` and the first section of
   `handoff.md`.
3. Prints the explicit next-step: *"Run `bale handoff
   <response-NNN>` to package the handoff into a fresh session."*
4. Skips the staging diff and validation invocation entirely.

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
menu. Defaulting to a multiple-choice menu when a recommendation
existed is the failure mode that produces "which piece?" misfires
in the next session — the next Claude reads the menu, asks the
architect to pick, and the recommendation gets lost.

The multiple-choice shape is reserved for genuine close calls where
the bailing Claude couldn't pick. When that case applies, the
handoff also declares that **the next session opens in
conversational mode** and transitions to tarball mode after the
architect picks — saving the next Claude from re-discovering that
shape on every chained handoff.]

## Salvageable work

[Any partial decisions, sketches, or code stubs that should not be
discarded. Verbatim where possible. If nothing is salvageable,
write: "Nothing to salvage — restart from the reading plan."]
```

The next Claude reads `handoff.md` as the first `context/` doc and
treats its reading plan as authoritative for that session, unless
the request manifest overrides it.

### 5.8 diagnostics.json (required in bailout responses)

Structured longitudinal data, aggregated across sessions to
calibrate where budget actually goes. Schema:

```json
{
  "session_id": "2026-05-14-context-limit-005",
  "bail_trigger": "reading-path-inflation",
  "bail_narrative": "one paragraph in Claude's voice: what was noticed, when, why bailing beat pushing through.",
  "context_loaded": [
    {
      "path": "context/docs/CLAUDE.md",
      "verdict": "necessary",
      "note": "the operating manual; can't skip"
    },
    {
      "path": "context/docs/TARBALL.md",
      "verdict": "wasted",
      "note": "drilled prematurely; the session turned out to be conversational"
    }
  ],
  "exploration_paths": [
    {
      "what": "considered putting the budget premise in §1 directly",
      "verdict": "dead_end",
      "note": "renumbering cost too high; chose a forward-reference instead"
    }
  ],
  "tool_calls_summary": {
    "view": 6,
    "bash_tool": 4,
    "str_replace": 0
  },
  "what_would_save_next_time": [
    "concrete, prescriptive advice for the next Claude — what reading paths to skip, what decisions are already made"
  ]
}
```

Field semantics:

- **`bail_trigger`** — one of `"reading-path-inflation"`,
  `"mid-build-budget-panic"`, or `"other"`. The first two match the
  Claude-detected triggers in `CLAUDE.md` §11.3. The third
  (architect-requested bailouts — test sessions, deliberate
  checkpoints; see `CLAUDE.md` §11.3's third bullet) uses `"other"`
  and surfaces the specifics in `bail_narrative` rather than minting
  a new enum value. The enum stays small for clean longitudinal
  filtering across sessions; the narrative is searchable when a
  finer cut is needed (e.g., `jq 'select(.bail_narrative |
  test("test"))'`).
- **`bail_narrative`** — Claude's honest paragraph on the bail
  decision. The retrospective complement to the prescriptive
  `handoff.md`.
- **`context_loaded[].verdict`** — `"necessary"`, `"wasted"`, or
  `"partial"`. The verdict is qualitative; Claude can't measure
  token-spend per doc precisely.
- **`exploration_paths[].verdict`** — `"productive"`, `"dead_end"`,
  or `"inconclusive"`.
- **`tool_calls_summary`** — map of tool name to call count.
  Captured from Claude's own count, not measured externally.
- **`what_would_save_next_time`** — array of strings, each a
  concrete prescription. Overlaps with `handoff.md`'s "What I
  learned" section; that's intentional — `handoff.md` is for the
  next Claude, `diagnostics.json` is for the user's longitudinal
  analysis.

The schema is intentionally loose: new fields can be added in
future sessions without breaking earlier aggregation, and values
are honest estimates rather than measurements. Aggregation across
sessions is left to the user (jq, notebook, eventual `bale stats`
command).

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
syntax). `apply.sh` is the no-op script — no deletes, no renames, and
no executable bits to restore (see §5.1.1). `README.md` and
`notes.md` are absent — nothing surprising happened, nothing needed
surfacing and no proposal was worth queuing (§5.4.1), and the
manifest's `summary` field covers what the response delivers.

The protocol still applies. The floor is the floor.

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
  eslint:                    claim=pass    verdict=pass    [agree]
  vue-tsc --noEmit:          claim=pass    verdict=fail    [DISAGREE]
  vite build (staging only): claim=pass    verdict=skip    [n/a]
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

### 7.7 Asserting executable bits

A session that ships an executable — a `created` or `modified` file
meant to run, typically a script with a shebang — asserts its exec bit
in `validation.sh`. This is the verify side of the restore in §5.1.1:
the `files/` overlay strips mode, `apply.sh` restores it with `chmod
+x`, and a forgotten `chmod` is the silent breakage that content-only
checks sail past. The assertion is what turns that into a `[FAIL]`.

By the time `validation.sh` runs, bale has overlaid `files/` and run
`apply.sh` in staging (§7.1), so the file sits at its repo-relative
path with the mode `apply.sh` left it. Test that path directly — not
the `files/` copy, whose mode was already stripped:

```bash
if [ -x scripts/release.sh ]; then
  echo "[PASS] scripts/release.sh is executable"
else
  echo "[FAIL] scripts/release.sh not executable — apply.sh chmod omitted?"
  exit_code=1
fi
```

This is a session-specific assertion (§7.2 item 6): it ships only when
the session ships an executable, and names the exact path rather than
scanning the tree. A session shipping no executables omits it, the
same way it omits a build check when nothing built.

---

## 8. Hard Rules (Tarball-Specific)

Contract rules — the mechanical checks bale enforces at pack and
apply time — are not re-listed here: bale applies them automatically
and rejects a malformed tarball before `validation.sh` runs, so the
builder's job is to satisfy them, not to recite them. They cover
manifest schema and field agreement, sha256 and size match against
`files/`, a non-empty `reason` on every change, path safety, the
`files/`↔`changes[]` correspondence, and the post-`apply.sh`
reconciliation of §5.1.1. The rules below are instead *policy*:
caught at review, not by bale.

| Rule | Enforcement |
|------|-------------|
| The tarball is the contract — no side commands, no pasted snippets, no hand-edits | review |
| Validate before apply, always | my discipline |
| Tarballs are immutable once delivered | my discipline |
| `validation_will_run` is honest and complete | review |
| Tarball mode without `TARBALL.md` loaded — pause and ask | Claude's own check at the start of a response |
| Probe is read-only outside `./probe-output/` | probe self-check + my review |
| `apply.sh` operations limited to deletes and other manifest-declared file ops — no `mv`, no installs, no builds | review (with bale's post-`apply.sh` reconciliation against the manifest, §5.1.1, catching tree violations) |

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
4. Build `manifest.json` with reasons, sizes, sha256s (computed via
   §5.2.1, never by hand), deferrals, `validation_will_run`, and
   `claims`.
5. Write `apply.sh` for deletes (or a no-op script if none).
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
    - **`set(claims) ⊆ validation_will_run`.** Every `claims` key
      verbatim-matches a `validation_will_run` entry (§5.3). A key
      with no match is the tell of a renamed or paraphrased check; the
      fix is the key, not a new entry.
    Bale's pre-flight (§8) independently re-checks the first two and
    bounces a tarball that fails either, so catching them here turns a
    rejected tarball into a fix before packing. The third is the
    builder's to keep: bale treats claims as diagnostic, not
    gatekeeping (§7.3), so a stray claims key sails through pre-flight
    and surfaces only as an unpairable line in the §7.3 reconciliation
    — this self-check is the one place it's caught before then.
11. Tar: `tar -czf response-NNN.tar.gz response-NNN/`.

### 10.2 Returning a probe instead

1. Confirm the gap is real and environment-specific, not conceptual.
2. Write the probe script inline in chat (bash; PowerShell variant
   if Windows-native is in play).
3. List in the chat preamble what the probe writes to (only
   `./probe-output/`) and every tool it invokes.
4. Stop. The probe's output is needed before any response can be
   built.
