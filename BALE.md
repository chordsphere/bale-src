# BALE.md — bale tool design

> Design document for the bale CLI.
> Read alongside `CLAUDE.md`, `TARBALL.md`, `DOCS.md`.
> Read in full when implementing or modifying bale.

---

## META

### What this doc is

The design document for the **bale** command-line tool. bale is the
mechanical machinery that makes the workflow described in
`CLAUDE.md`, `TARBALL.md`, `DOCS.md`, and `CODE.md` operate. It
packs request tarballs to send to Claude, applies response tarballs
Claude returns, and handles the git-side bookkeeping (staging,
validating, committing, rolling back).

This doc captures architecture decisions, the command surface, the
wire-format details bale enforces, and the build phases. It is meant
to be uploaded into a Claude session as the source for implementing
the tool.

### How this relates to the global docs

- `CLAUDE.md` is the working agreement and the operating manual.
  Bale injects it into every request.
- `TARBALL.md` is the wire format. Bale implements its contract and
  injects it into every request.
- `DOCS.md` is project-side doc-management policy. Bale injects it
  into every request but does not enforce it; projects that adopt
  the workflow have Claude include the corresponding assertions in
  each response's `validation.sh`.
- `CODE.md` is project-side code-layout philosophy — extraction,
  splitting, indexing, pruning, plus the rules for human-authored
  and meta code. Bale injects it into every request but does not
  enforce it; projects that adopt the philosophy have Claude
  include the corresponding assertions in each response's
  `validation.sh`.
- This doc (`BALE.md`) is the design of the tool itself. It is not
  injected into project requests; it lives in the bale tool's source
  repo and is read when modifying bale.

### Amendment rule

Changes to this doc go through bale sessions on bale's own
repository. Hand-edits are expected only during bootstrap (section
13).

---

## INDEX

### Read paths

| Situation | Sections |
|-----------|----------|
| Building v0.0.1 (bootstrap) | 1, 2, 3, 5, 6, 7, 13 |
| Implementing v0.1 | All sections |
| Adding a new command | 4, 5, 6 |
| Debugging an apply | 7, 8 |
| Debugging a rollback | 9 |
| Understanding lock-state transitions | 9.5 |
| Understanding what bale does NOT do | 2 |
| Self-applicability questions | 12 |
| Decisions still open | 14 |

### Sections

| # | Section | Tier |
|---|---------|------|
| 1 | Purpose | core |
| 2 | Scope and non-scope | core |
| 3 | Architecture and deployment | core |
| 4 | Project assumptions | core |
| 5 | Command surface | core |
| 6 | Wire format | core |
| 7 | Pack pipeline | core |
| 8 | Apply pipeline | core |
| 9 | Rollback, revert, unlock | core |
| 10 | Git init walkthrough | drill-down |
| 11 | Bale-enforced contract (full list) | core |
| 12 | Self-applicability | drill-down |
| 13 | Build phases | reference |
| 14 | Open decisions | reference |

---

## 1. Purpose

Bale is a project-agnostic CLI that handles Claude sessions end to
end. It does one thing: orchestrate the round trip between a project
directory and Claude via tarballs.

A session is:

1. **Pack** — bundle the global docs from bale's installation plus a
   slice of the project into a request tarball. Hand the tarball to
   Claude (via copy-paste, upload, whatever).
2. **Receive** — Claude returns a response tarball.
3. **Apply** — validate the response mechanically, stage the changes
   to a git branch, run the response's `apply.sh` and `validation.sh`
   in a staging copy, commit if clean, walk through merge/keep/revert.
4. **Rollback** (later, if needed) — undo an applied bale via
   `git revert`, tracked and itself undoable.

That's the entire job. Bale doesn't lint, build, test, or analyze.
Those live in the response's `validation.sh`. Bale doesn't know what
an ADR is, what an INDEX is, what STATE.md is. Those are project
policy enforced in the response's `validation.sh` or by review.

Bale is uniquely positioned to let Claude work on **any** directory:
a directory with one script and a data folder, or an enterprise Vue
app, or anything in between. The user shapes what's in scope; bale
moves bytes safely.

---

## 2. Scope and non-scope

### 2.1 In scope

- Pack request tarballs (inject global docs + bundle user-specified
  files + goal/constraints/scope from CLI or wizard).
- Apply response tarballs (validate manifest, path-safety, staging
  copy, run `apply.sh` + `validation.sh`, commit or hold).
- Rollback applied snaps (`git revert`, tagged, undoable).
- Revert staged-not-merged snaps (discard the branch).
- Unlock abandoned sessions (clear lock, no git side effects).
- Git-init walkthrough for first-time users in non-git directories.
- Session-registry enforcement (per-session open markers, ADR-0006;
  concurrent sessions admitted only with disjoint scopes, ADR-0007;
  every session easily abortable via revert/unlock).

### 2.2 Out of scope

- INDEX.md coherence checks.
- ADR sequential numbering.
- Doc-inventory categorization or detection.
- Project structure assumptions beyond "must be a git repo."
- Linting, typechecking, building, testing — all in `validation.sh`.
- Status / log / blame / diag commands. Inspection is a Claude
  session: ask Claude what's going on and paste output of `git log`
  or similar. Bale does not duplicate git's read commands.
- Probe handling. Probes are session-scoped only — Claude returns a
  script in chat, the user runs it, the user pastes output back into
  the next message. Bale does not see probes.
- Out-of-scope enforcement. The request's `out_of_scope` field is
  prose, not glob patterns; bale does not mechanically check paths
  against it. Out-of-scope drift is a policy concern, surfaced at
  review and by `TARBALL.md` §8's "stay in the lane" rule.

### 2.3 Why these are out of scope

Bale is a tool, not a workflow. The workflow lives in the global
docs. A project that wants the full structured workflow (INDEX, ADRs,
schemas) asks Claude to include the corresponding assertions in each
response's `validation.sh`. A project that doesn't want any of that
just uses bale to pack/apply/rollback arbitrary file changes.

The "anything else is out of scope" rule is load-bearing. Every
feature bale doesn't have is a feature that can't go wrong, and a
feature a casual project doesn't need to learn.

---

## 3. Architecture and deployment

### 3.1 Multi-file deployment via release tarball

Bale ships as a **release tarball** that extracts in place to a
self-contained directory. Source lives in a normal package layout;
a build step (planned for v0.1+) packages that layout into
`bale-vX.Y.Z.tar.gz`. The released directory has this shape:

```
bale/
  bin/bale            # the Python entrypoint with shebang
  bin/bale_config.py  # configurables loader/merger + `bale config init` wizard
  docs/
    CLAUDE.md
    TARBALL.md
    DOCS.md
    CODE.md
  install.sh          # finalize the install (chmod, symlink, run validate)
  validate.sh         # sanity-check this install's layout and CLI surface
  upgrade.sh          # in-place upgrade to a newer release, preserving user/
  README.md           # install and usage notes for first-time users
```

This is the **install layout** — what `~/bale/` (or wherever the
user extracts) contains right after install. One additional
location matters for runtime but is *not* in the release tarball:
`<install>/user/`, the user-owned subtree that holds the global
`bale.toml` and any global hook scripts. It's absent on a fresh
install; `bale config init --global` creates it on first write.
`upgrade.sh` preserves it across release swaps. Keeping it inside
the install dir (rather than under `$XDG_CONFIG_HOME` or `~/`) is
deliberate: the install dir stays portable as a unit — copy
`<install>/` anywhere and the global config travels with it.

This is distinct from the **bale-src layout** (the source repo):
bale-src has the same release-shaped top-level items plus this
design doc (`BALE.md`), `bale.toml`, `scripts/`, and `claude/`
(project-local configurables, hook scripts, and bale-src's own doc
map). The extras are bale-src's own use of the bale workflow and
are not part of the release. See section 13 for why bale-src has
this shape.

Install is one extract + one script:

```bash
tar -xzf bale-vX.Y.Z.tar.gz -C ~/
~/bale/install.sh
```

Upgrade is one extra script that preserves the user-owned subtree:

```bash
~/bale/upgrade.sh path/to/new-bale-release.tar.gz
```

`upgrade.sh` is the canonical install-preserving path: moves
`user/` aside, wipes the install dir clean, extracts the new
release, moves `user/` back, runs the new `install.sh`. The
`README.md` documents two manual alternatives (tar-over-top, `rm
-rf` + extract) and their tradeoffs; both exist primarily for the
"no `user/` subtree to preserve" case.

The destination is the user's choice: `~/bale/`,
`~/.local/share/bale/`, `/opt/bale/`, anywhere writable. The script
locates its sibling docs via `Path(__file__).resolve().parent.parent
/ 'docs'` — wherever the directory landed, `bin/bale` finds
`../docs/` (and `../user/` for global config).

`install.sh` is intentionally thin: it verifies layout, restores
executable bits (some filesystems strip them on extract), offers a
PATH symlink, and runs `validate.sh`. It does NOT create `user/` —
that's `bale config init --global`'s job, on opt-in. No virtualenv,
no pip, no sourcing in shell rc. Two optional conveniences exist
on top of the bare install, and each must remain optional:

- Symlink `bin/bale` into a PATH directory (`ln -s ~/bale/bin/bale
  ~/.local/bin/bale`) so `bale` works as a bare command. Without it,
  invoke by full path: `~/bale/bin/bale pack`. The script resolves
  `__file__` through the symlink, so docs are still found via the
  real `bale/docs/` location.
- Source a bash-completion script in shell rc. Completion is a v0.3
  feature; even when it lands, sourcing is opt-in.

The release-tarball form has two virtues over a single-file build
(e.g. PEP 441 zipapp):

1. **Editable docs.** When you run a bale session against the bale
   repo itself, the four global docs are real files you can edit
   directly. Closing the loop doesn't require rebuilding a bundle —
   change a doc, save, the next `bale pack` injects the new version.
2. **Consistent with bale's own output.** Bale moves tarballs;
   shipping bale itself as a tarball means the install model matches
   the wire format users already understand.

### 3.2 Requirements

- Python 3.10+ on the host (modern Ubuntu and macOS both ship this; 3.10 is
  also the floor on several security-hardened/LTS distros).
- `git` on `PATH`.
- `bash` on `PATH` (Windows users need Git Bash or WSL — this is
  documented but not engineered around).
- Standard POSIX tools (`tar`, `cp`, `rm`, `mkdir`) on `PATH`.
- No third-party Python dependencies to install — nothing touches pip or a
  virtualenv. Stdlib only on Python 3.11+. On 3.10, which has no stdlib TOML
  parser, bale uses a pure-Python TOML reader vendored in-tree
  (`bin/_bale_toml.py`); it ships inside the distribution, so the "no pip"
  property is unchanged.

### 3.3 Global docs live in the bale installation

`CLAUDE.md`, `TARBALL.md`, `DOCS.md`, and `CODE.md` live as regular
files at `<install>/docs/` alongside the script. `bale pack` reads
them from that location and injects them into the request tarball.
They are never read from the project being snapped.

To edit a global doc: run bale on bale's own repo, where the docs
are the same files bale reads at runtime — no separate
"source-of-truth" copy. Apply the response, re-package a release
tarball (or, during development, just keep using the working tree
directly — the layout bale reads from is the layout bale ships).
Every project sees the new docs on its next pack.

### 3.4 Per-project state lives in `.bale/` at repo root

```
<repo>/
  .bale/
    current_session            # compatibility pointer: informational;
                               # names the most recently opened session
                               # (ADR-0006)
    integration.lock           # present only while apply's git merge
                               # window (§8.6–§8.8) is running, or stale
                               # after an interrupted apply (ADR-0006;
                               # clear with `bale unlock --integration`)
    sessions/<sid>/
      open                     # session-registry marker: present ⇔ the
                               # session is open (ADR-0006)
      manifest.json            # persisted inbound manifest
      scope.json               # the session's resolved scope, read by
                               # the ADR-0007 disjointness gates — the
                               # include set for a pack, the
                               # reading-plan file set for a handoff;
                               # absent (pre-threading sessions) reads
                               # as whole-tree
      origin_branch            # branch user was on before staging
    logs/<sid>.log             # structured log
    archive/                   # past session manifests (optional)
```

The **session registry** (ADR-0006) is the authoritative record of
open sessions: a session is open exactly while its
`sessions/<sid>/open` marker exists. The marker — not the directory —
defines openness, because a consumed bailout keeps its session
directory for `bale handoff`'s lineage chase. `current_session`
survives as a compatibility pointer kept in lockstep with the
registry: empty when nothing is open, otherwise naming one open
session — the most recently opened, repointed to the oldest remaining
open session when the named one closes. Every command resolves
sessions through the registry: pack, apply, and status since the
registry landed, and revert, retry, unlock, and handoff since the
threading session — the three that target "the" session take an
optional sid, resolving implicitly when exactly one session is open
and requiring the sid (listing the candidates) when several are. The
pointer is therefore informational only; the one operational reader
left is `bale unlock`'s stale-pointer sweep, which clears a non-empty
pointer with no matching open marker (the benign half-state an
interrupted pack can leave, §9.3).

`.bale/` is gitignored. The git-init walkthrough adds it to
`.gitignore` automatically. The tool offers to add it on any first
invocation in a repo that doesn't have the entry.

There's also one piece of *per-install* user state, distinct from
per-project: `<install>/user/`. It holds the global (install-wide)
`bale.toml` and any global hook scripts the user has set up via
`bale config init --global`. Per-project state stays in `<repo>/.bale/`;
per-install user state stays in `<install>/user/`. The former is
gitignored project state; the latter is user-owned install state that
survives `upgrade.sh`. Neither is in the release tarball. See
`claude/context/bale-internals.md` §2 for the layering rules.

### 3.5 Solo-project assumption

This tool is for solo projects. No shared-branch detection, no
upstream/origin tracking, no concurrent-session-on-different-machines
handling. The rollback story relies on this: `git revert` works
cleanly on local-only branches and the user doesn't have to think
about pushed history.

### 3.6 First-time user flow

The intended onboarding is two-to-three steps:

1. Extract the release tarball and run `install.sh`. `install.sh`
   leaves a working `bale` binary on `PATH` (assuming the symlink
   step was accepted) and points the user at step 2.
2. `cd` into a project (any git repo). Run `bale config init`. The
   wizard walks every configurable that exists — git identity,
   hooks, search paths — and writes `<repo>/bale.toml`. It is
   idempotent and entirely optional past git identity; pressing
   Enter through each prompt leaves the project in a perfectly
   usable state.
3. *(Optional)* Run `bale config init --global` from anywhere. This
   walks the same configurables (minus git identity, which is
   per-repo) and writes `<install>/user/bale.toml` — the install-
   wide layer that every project inherits per-key. Useful when you
   want, e.g., `~/Downloads` in `apply.search_paths` once for every
   bale-using project on the machine, rather than re-typing it in
   every `<repo>/bale.toml`.

After step 2 (and optionally 3), `bale pack` / `bale apply` /
`bale retry` / `bale revert` work normally. The wizard is the
**single canonical discoverable surface** at both layers for
everything `bale.toml` controls; a configurable that isn't walked
by `bale config init` is a contract violation (see
`claude/context/bale-internals.md` §4.1).

A user who skips step 2 sees no errors. `bale pack` in a non-git
directory triggers the git-init walkthrough (section 10) and asks
for the same identity info inline; hooks and search paths just
stay opt-out. Step 2 exists so the first-time user can opt *in* to
everything bale can do in one walk, without having to discover
each surface piecemeal. Step 3 exists so a user with multiple
bale-using projects can set machine-wide defaults once.

---

## 4. Project assumptions

The only hard requirement: the project must be (or be willing to
become) a git repository.

- If `cwd` is inside a git repo: bale proceeds.
- If `cwd` is not inside a git repo: bale offers the git-init
  walkthrough (section 10). The user can accept (bale initializes and
  proceeds) or decline (bale exits cleanly with a one-line
  explanation).

Beyond git, bale assumes:

- A writable `.bale/` at the repo root (bale creates it on first
  use).
- Either `.gitignore` already has `.bale/`, or bale appends it (with
  one-line user confirmation).
- A writable `.baleignore` (optional; user-managed) for project-
  specific exclusions during pack.

That's it. No required directory structure. No required docs. No
required tooling. A directory with one script and a data folder
works. An enterprise Vue app works. A research repo with a notebook
and some data works.

Bale operates on whatever repo `cwd` resolves to via `.git/`. In a
monorepo, that's the whole tree. Monorepo users who want per-
subproject scoping either bale the whole tree (broad scope per
session, narrow `--include` paths) or treat sub-packages as separate
repos with their own `.git`. Multi-root sessions are out of scope
for v0.1.

---

## 5. Command surface

The full target surface. Phases in §13 govern which commands land in
which release; until a command's phase ships, the row stays here as a
forward-looking entry.

| Command | Purpose | Phase |
|---------|---------|-------|
| `bale pack` | Build a request tarball from the project + user-specified scope. | v0.0.1 |
| `bale apply <tarball>` | Validate and apply a response tarball. Terminal — the wizard ends in merge, revert, or (on HOLD) leaves the branch staged for inspection. | v0.0.1 |
| `bale retry <tarball> [--sid]` | Re-attempt a HOLDed session with a corrected response tarball, keeping the session open so the new attempt lands in the same session id. The sid resolves implicitly with one session open; `--sid` picks when several are (ADR-0006). | v0.0.x |
| `bale revert [sid]` | Discard a held bale branch (validation failed and inspection is done, or user changed their mind). Sid optional with one session open, required with several. | v0.0.1 |
| `bale rollback [sid]` | `git revert` an applied bale. Defaults to most recent. `--undo` / `--list` / `--stash`. | v0.2 |
| `bale unlock [sid]` | Close an abandoned session (sid optional with one open, required with several), or `--integration` to clear a stale integration lock. | v0.0.5 |
| `bale handoff <tarball>` | Repackage a bailout response (TARBALL.md §5.6) into a fresh request tarball that inherits the bailed-on session's goal. | v0.0.6 |
| `bale config init` | Walk through every configurable at the chosen layer (project or `--global`) and write the resulting `bale.toml`. The canonical discoverable surface for configurables; see `claude/context/bale-internals.md` §4. | v0.0.3 |

No `status`, no `log`, no `blame`, no `diag`. Inspection is a Claude
session.

### 5.1 Help and version

- `bale help` — top-level usage with one-line summaries.
- `bale help <cmd>` — detail for one command.
- `bale --version` — print the bale version.

### 5.2 Interactive default

When required args aren't piped in, bale drops into a wizard that
asks for them. The wizard never requires more than the user knows
right now; defaults are sane. The user idiom: *"functions that ask
for user input when arguments haven't been piped in."*

### 5.3 Tarball mode is the only mode

Bale doesn't have "conversational mode" — that's a property of the
Claude session, not the tool. Bale only runs when the user has
decided code or files should land. Asking Claude a question requires
no tool.

### 5.4 Global flags

The following flags apply across multiple commands:

- `--force` — bypass safety refusals (system-dir, home-dir,
  threshold caps, dirty-tree checks). Logged prominently.
- `--verbose` — stream validation output and other long-running
  command output to stdout in addition to the log file. (Landed
  apply-scoped in v0.2.1 — `bale apply --verbose` streams `validation.sh`
  output live; wiring it across the other commands listed here is future
  work.)
- `--no-interact` — non-TTY mode. Skips prompts; the default action
  (Enter key equivalent) is taken at every prompt point. (Landed
  apply-scoped in v0.2.5 — `bale apply --no-interact` and `bale retry
  --no-interact`, also enable-able per config via `apply.no_interact`
  in bale.toml; wiring it across the other commands listed here is
  future work. In this mode the pre-hook confirmation resolves from
  `apply.hook_auto_accept` — unset/false takes the prompt's decline
  default — and every bypassed prompt logs the decision taken and its
  source to the terminal and the session log.)
- `--staging-dir <path>` — override the default `./staging/`
  location.
- `--clean` — remove the staging directory after a successful apply.
  Default keeps it for inspection.
- `--max-files <N>` / `--max-size <bytes>` / `--max-depth <N>` —
  override the pack threshold caps. See section 7.4.
- `--no-gitignore` — disable `.gitignore`-based exclusion during
  pack. See section 6.4.

Flags scoped to a single command are documented in that command's
section.

---

## 6. Wire format

Bale reads and writes `tar.gz` archives via Python's stdlib
`tarfile` module.

### 6.1 Request tarball

Per `TARBALL.md` section 3.1:

```
request-NNN/
  manifest.json        # structured metadata (required)
  CLAUDE.md            # injected by bale
  TARBALL.md           # injected by bale
  DOCS.md              # injected by bale
  CODE.md              # injected by bale
  context/             # everything the user chose to include
    <project files and any project docs>
  README.md            # optional; user's voice beyond manifest.goal
```

`manifest.json` schema is `TARBALL.md` section 3.2. Bale fills the
schema from CLI args and/or wizard input.

### 6.2 Response tarball

Per `TARBALL.md` section 5.1:

```
response-NNN/
  README.md
  manifest.json
  apply.sh             # deletes; never mv (renames decompose into files/ + rm)
  validation.sh        # Claude's session-scoped checks against staging
  files/               # mirrors project tree from repo root
  notes.md
  next-prompt.md
```

`manifest.json` schema is `TARBALL.md` section 5.2. Bale enforces it.

### 6.3 Session ID

Format: `YYYY-MM-DD-<slug>-NNN`, per `TARBALL.md` 1. The slug is
kebab-cased and user-supplied (or wizard-prompted). NNN is the
per-day monotonic counter bale maintains in `.bale/`.

Example: `2026-05-12-vue-scaffold-001`.

### 6.4 No wire-format size cap

There is no enforced tarball size cap at the wire-format level. Big
projects bundle big tarballs and that is fine.

The accidental-bloat protection lives in `bale pack`, not in the
wire format. See section 7.4 (scope projection and threshold check)
for the file-count, size, and depth caps that protect against
running `bale pack` in the wrong directory.

The baked-in always-excluded paths apply regardless of explicit
`--include`:

- Bale and git internals: `.git/`, `.bale/`
- Common big-build dirs: `node_modules/`, `__pycache__/`, `.venv/`,
  `target/`, `dist/`, `build/`, `.next/`, `.nuxt/`, `out/`, `.cache/`
- Common secret patterns: `.env`, `.env.*`, `*.pem`, `*.key`, `*_rsa`,
  `*_dsa`, `*.p12`, `*.pfx`, `id_rsa`, `id_dsa`, `.aws/credentials`,
  `.npmrc` (when it contains `_authToken`), `.pypirc`.

The secret patterns are non-negotiable. There is no flag to disable
them. A user who genuinely needs to ship `.env` (e.g., to debug a
dotenv-loader bug) renames or copies the file outside the pattern.

Bale also honors `.gitignore` at the repo root by default — files
matched by `.gitignore` are excluded from packs. `--no-gitignore`
disables this for projects whose gitignore overshoots (e.g., excludes
generated source the user wants Claude to see).

`.baleignore` at the repo root (gitignore-style syntax) lets the
user add project-specific permanent exclusions on top of the above.

### 6.5 No probe handling in the file format

Probes are not part of bale's wire format. They are a session-level
concept: Claude returns a script in chat, the user runs it, the user
pastes output back. Bale does not have a `probe-apply` or
`probe-output/` directory anywhere.

---

## 7. Pack pipeline

`bale pack` builds a request tarball. The pipeline:

### 7.1 Pre-flight

1. **Path-location check.** Refuse if cwd (or the would-be repo
   root) matches a hardcoded system-directory list: `/`, `/home`,
   `/Users`, `/usr`, `/var`, `/etc`, `/bin`, `/sbin`, `/lib`,
   `/lib64`, `/opt`, `/srv`, `/proc`, `/sys`, `/dev`, `/tmp`,
   `/var/tmp`, `/private/tmp`. No override flag — the user should
   `cd` somewhere appropriate. `bale pack` in `/` was almost
   certainly a typo.
2. **Home-directory check.** If cwd is exactly `$HOME` (not a child
   of it), refuse with an explanation. `--force` overrides — the one
   legitimate case is a dotfiles repo, where the user knows what
   they're doing.
3. Resolve repo root (walk up from cwd looking for `.git/`).
4. If not in a git repo: run the git-init walkthrough (section 10).
   The walkthrough re-applies the path-location and home-directory
   refusals before initializing.
5. Scope-disjointness gate (ADR-0007), read from the session
   registry (ADR-0006). With no session open, proceed — unchanged
   behavior. With open sessions, admit the pack exactly when its
   declared scope — the resolved include set: normalized `--include`
   paths, or `.` (the whole tree) for a default pack — is disjoint
   from every open session's recorded scope (`sessions/<sid>/scope.json`).
   Intersection is over paths, with directory entries covering their
   subtrees and `.` covering everything; a session without a recorded
   scope reads as whole-tree (conservative). On intersection, refuse
   with a message naming the colliding session(s) and entries and the
   remedies: narrower `--include`, apply the open session's response,
   or `bale unlock` an abandoned one. Includes are a deliberately
   conservative proxy for change scope, so the gate can
   false-positive; a pack it admits is one whose workers were never
   shown overlapping files. A default whole-tree pack intersects
   every open session — broad scope and concurrency are mutually
   exclusive by design.
6. Ensure `.bale/` exists and is in `.gitignore`. If `.gitignore`
   exists but doesn't list `.bale/`, bale appends `.bale/` to it with
   a single-line user confirmation in interactive mode (or auto-
   appends with a logged note in piped mode).

### 7.2 Gather inputs

CLI args take precedence; missing args trigger wizard prompts.

The inputs:

- **goal** (one sentence) — used as `manifest.goal` and as the
  opening line of `README.md`.
- **slug** (kebab-cased, short) — used in the session ID.
- **constraints** (list, optional).
- **out_of_scope** (list, optional).
- **expects_probe** (`yes` | `no` | `claude-decides`, default
  `claude-decides`).
- **includes** (list of file or directory paths) — defaults to the
  entire working tree (minus baked-in and `.baleignore` exclusions).
- **excludes** (list of patterns) — appended to the always-excluded
  set for this session only.
- **readme prose** (optional) — the request's `README.md` body.
  Suppliable non-interactively via `--readme-file <path>`, or
  interactively via the wizard's `$EDITOR` step (§7.3); `--edit`
  forces the editor step on a fully specified command.

The flag-to-manifest mapping lives in `TARBALL.md` §3.4 — cited
both by the architect authoring a pack by hand and by Claude when
emitting a `CLAUDE.md` §11.2 rescope offer.

Bale also fills `manifest.project` automatically as
`basename $(git rev-parse --show-toplevel)`. This is overridable via
`.bale.toml` in v0.5+ for users who want a different name than the
repo directory.

### 7.3 Wizard flow when args missing

If `bale pack` is invoked without CLI args (or with only a subset),
the wizard prompts:

```
Goal (one sentence)? > implement the foo widget per ADR-0007
Short slug (kebab-case)? > foo-widget
Anything to exclude from the default-include-everything? > data/
Any constraints? (one per line, blank to finish)
> no breaking changes to the public API
>
Any out-of-scope concerns? (one per line, blank to finish)
> backend
>
Add a README with prose context? [y/N] >
```

`README.md` is optional (per `TARBALL.md` 3.1). The wizard defaults
to skipping it — the manifest's `goal`, `constraints`, and
`out_of_scope` fields already capture the structured intent. Choose
`y` only when there's prose worth keeping that doesn't fit those
fields.

If the user answers `y`, `$EDITOR` (falling back to `$VISUAL`, then to
`/usr/bin/editor` — the Debian alternatives entry, which catches most
no-EDITOR-set installs) opens with a scaffold pre-populated from the
wizard answers. The user expands in prose, saves, and bale proceeds.
Saving an empty buffer omits the file. The fallback chain matches
`bale handoff --edit-goal` on purpose — they share one `open_in_editor`
helper, so users see one editor-resolution behavior across the tool.

`--no-edit` forces skip regardless.

Two flags (v0.2.4) give the README a CLI surface beyond the wizard:

- **`--readme-file <path>`** packs the file's contents (UTF-8 text)
  as the request's `README.md` — the non-interactive way to ship
  prose context, e.g. from an orchestrator or a pre-written note. A
  missing, unreadable, or empty file fails loudly before any prompt
  runs; deliberate omission is spelled "don't pass the flag."
  Compatible with `--no-edit` (the prose ships, no editor opens) and
  with the wizard (the README y/N prompt is skipped, since content
  is already supplied).
- **`--edit`** forces the `$EDITOR` step even on a fully specified
  command (goal and `--slug` present, where the wizard never
  engages). Seeded with `--readme-file`'s content when both are
  given — a review-then-pack flow — and with the standard scaffold
  otherwise. Saving an empty buffer omits the file, same as the
  wizard's step. Requires a TTY (use `--readme-file` for
  non-interactive prose); contradicts `--no-edit`, and passing both
  is an error.

Resolution precedence, first match wins: `--edit` → `--readme-file`
alone → the wizard's y/N prompt (when the wizard engaged and
`--no-edit` is absent) → no README. With none of these flags, the
interactive flow is exactly the pre-v0.2.4 wizard.

### 7.4 Scope projection and threshold check

Before building the tarball, bale walks the included paths with all
exclusions applied (baked-in + `.baleignore` + user-supplied for this
session) and projects:

- **File count** — total files that would be bundled.
- **Total size** — bytes that would be bundled.
- **Max depth** — deepest path level from the repo root.

Then it checks against thresholds. Behavior depends on whether the
run is interactive or piped.

**Defaults:**

| Threshold | Default | Behavior on breach |
|-----------|---------|---------------------|
| File count (soft) | 10,000 | Interactive: prompt; piped: refuse (v0.2.4) |
| File count (hard) | 100,000 | Interactive: refuse, offer override; piped: refuse |
| Size (soft) | 100 MB | Same as above |
| Size (hard) | 1 GB | Same as above |
| Depth (hard) | 20 levels | Same — short-circuits the walk |

**Short-circuit walk.** The projection stops walking the moment a
hard cap is exceeded. Bale does not walk a million-file tree to tell
you it's too big; it walks until it knows, then stops and reports
what triggered the stop.

**CLI flags to tune thresholds:**

- `--max-files <N>` — set the hard file count.
- `--max-size <bytes>` — set the hard size cap (accepts `1G`, `500M`).
- `--max-depth <N>` — set the hard depth cap.
- `--force` — bypass all caps. Logged prominently in `.bale/logs/`.

**Interactive prompt on soft-cap breach:**

```
This pack would include:
  Files:      12,847
  Size:       234 MB
  Max depth:  8 levels

Largest directories:
  data/       180 MB   8,200 files
  build/       42 MB   3,100 files
  src/         12 MB   1,547 files

[y] continue
[e] edit excludes
[n] abort
```

If `e`: bale takes new patterns and re-walks. Loop until the user is
satisfied or aborts.

**Piped-mode behavior (stdin not a TTY):**

- Soft breach: print the projection block and a refusal to stderr;
  exit non-zero (v0.2.4 — previously warn-and-proceed). No prompt can
  run, and a stderr warning nobody reads is not a check: proceeding
  silently ships exactly the oversized pack the cap exists to catch,
  in the one context (automation) where nobody is watching. The
  caller narrows the scope with `--exclude` / `.baleignore`, or
  re-runs with `--force` to proceed at that scope deliberately —
  `--force` is the explicit, logged "I mean it" that the silent
  proceed never was.
- Hard breach: print a refusal with the projection block to stderr;
  exit non-zero. The user re-runs with `--max-*` or `--force`.

The cap exists to catch obvious mistakes — `bale pack` accidentally
in `~`, or in a project root that contains a 50GB dataset that
should have been in `.baleignore`. It is **not** about wire-format
efficiency. There is no wire-format size cap. The tool is happy to
ship a 500MB tarball if the user has confirmed that's intentional.

### 7.5 Build the request

1. Generate session ID. Reserve next NNN for the slug + date.
2. Build `request-NNN/` skeleton.
3. **Inject all four global docs** (`CLAUDE.md`, `TARBALL.md`,
   `DOCS.md`, `CODE.md`) from bale's installation `docs/` directory.
4. Write `manifest.json` with the gathered fields.
5. Walk the include paths; apply exclusions (baked-in, `.baleignore`,
   user-supplied for this session); copy matching files into
   `context/`.
6. If README prose was resolved — from `--readme-file`, from
   `$EDITOR` (the wizard's y-path or `--edit`), or the combination —
   include it as `README.md`. Otherwise omit the file entirely (the
   manifest's `goal`, `constraints`, and `out_of_scope` fields carry
   the structured intent); `--no-edit`, an `n` at the wizard prompt,
   and an emptied editor buffer all land here.
7. Tar with `tar -czf request-NNN.tar.gz request-NNN/`.

### 7.6 Persist session state

After the tarball is on disk and validated for structure:

1. Write `.bale/sessions/<sid>/manifest.json` (the request's
   manifest, for `bale apply` to verify the response against) and
   `.bale/sessions/<sid>/scope.json` (the resolved include set — the
   session's scope, which the ADR-0007 gates read; step 5 of §7.1 and
   step 7 of §8.1).
2. Open the session in the registry (ADR-0006): write the
   `.bale/current_session` compatibility pointer, then the
   `.bale/sessions/<sid>/open` marker.
3. Log to `.bale/logs/<sid>.log`.

The registry open happens **last**, after the tarball is built and
validated — and within it the authoritative marker is written after
the pointer, so an interrupted pack can only leave the benign
pointer-without-marker state. If pack fails earlier, no session is
open and the user can just retry — no `bale unlock` required.

### 7.7 Output

Print the absolute path to `request-NNN.tar.gz` and the sid. The
user copy-pastes or uploads from there.

---

## 8. Apply pipeline

`bale apply <response-tarball>` is the workhorse. It validates,
stages, runs the response's `apply.sh` and `validation.sh`, commits
or holds, and walks the user through the result.

Pipeline steps:

### 8.1 Pre-flight (reject without staging on any failure)

1. Tar integrity. Open the archive, list members; reject on corrupt
   archive.
2. Extract to a temp directory.
3. Read `manifest.json`. Validate against the schema in `TARBALL.md`
   5.2: every key present, no unknown keys, every `changes[]` entry
   complete, every `reason` non-empty.
4. Verify an open session exists in the registry (ADR-0006): at
   least one `.bale/sessions/<sid>/open` marker. If none, reject —
   no session was open to receive this response. With exactly one
   open, it is the session this apply runs against, as before. With
   several open (ADR-0007), resolve which session the response
   answers from the tarball manifest's own `responds_to`: bale reads
   that one member in memory pre-pipeline, requires it to name an
   open session, and rejects otherwise. The pipeline re-checks
   `responds_to` against the resolved sid after its own extraction
   (step 6).
5. Verify the working tree is clean. Run `git status --porcelain`;
   if non-empty, reject with a message naming the dirty paths and
   pointing the user at `git stash` / `git commit` / `--force`. This
   check is here — adjacent to the registry check, before any tarball-
   specific work — because it concerns the user's state, not the
   tarball, and it's the cheapest failure to resolve. `--force`
   overrides (logged prominently); the per-file `cp` in section 8.6
   will overwrite without warning when overridden.
6. Verify `responds_to` in the manifest names an open session in the
   registry (ADR-0006 — the generalization of the old "matches the
   locked sid" comparison; with a single open session the two are
   the same check, and with several it re-checks the step-4
   resolution against the pipeline's own extraction).
7. Cross-session scope collision (ADR-0007): verify no `changes[]`
   path intersects **another** open session's recorded scope
   (`sessions/<sid>/scope.json`; same path semantics as §7.1 step 5 —
   directory entries cover subtrees, `.` covers everything, a missing
   scope reads as whole-tree). This is the real guard against the
   whole-file clobber: bale's overlay is whole-file replacement, so a
   response authored against a stale snapshot would silently
   overwrite a sibling session's work and the `--no-ff` merge would
   land clean. With at most one session open there are no siblings
   and the check is a no-op. Own-scope drift — a change outside this
   session's own scope that no sibling claims — remains a policy
   concern caught at review (§2.2, `TARBALL.md` §8), unchanged.
8. Verify every `changes[]` path appears in `files/` exactly when it
   should (created/modified ⇒ present in `files/`; deleted ⇒ absent
   from `files/`). Verify every file in `files/` is declared in
   `changes[]`.
9. Verify every `changes[].sha256` matches the actual sha256 of the
   corresponding `files/` entry.
10. Verify path safety on every `changes[].path`: no `..` escape, no
    `.git/` prefix, no `.bale/` prefix, no `.baleignore` match.
11. Verify `claims` is a subset of `validation_will_run`: every key in
    `claims` appears in `validation_will_run`. The reverse is not
    required — `validation_will_run` may list tautological checks
    (e.g., file syntax) that are omitted from `claims` per
    `TARBALL.md` 5.3.
12. Verify `manifest.json`, `apply.sh`, and `validation.sh` exist in
    the tarball. `README.md`, `notes.md`, and `next-prompt.md` are
    optional per `TARBALL.md` 5.1 and not required to exist.

If any of 1–12 fails: log the failure with a clear `[REJECT] <rule>:
<detail>` line, clean up the temp directory, exit non-zero. No
staging branch, no file modifications.

### 8.2 Stamp session

1. Record current `HEAD` as `git_head_at_apply` in
   `.bale/sessions/<sid>/manifest.json`.
2. Record the current branch as
   `.bale/sessions/<sid>/origin_branch`. This is the branch the apply
   wizard will merge into (on PASS) and the branch `bale revert`
   returns to.
3. Persist the response manifest at
   `.bale/sessions/<sid>/response-manifest.json`.

### 8.3 Stage

1. Create staging directory (default `./staging/`, overridable with
   `--staging-dir`). If it exists, fail loudly — don't overwrite.
2. `cp -r <project>/. staging/` (full project state minus `.bale/`).
3. `cp -r response-NNN/files/. staging/` (overlay the changes).
4. Run `bash apply.sh` with `cwd=staging/`. This handles deletes and
   any non-cp operations. If `apply.sh` exits non-zero, bale captures
   the exit code and output to the session log, wipes staging, and
   rejects the tarball — no git side effects, no reconciliation
   attempted.

### 8.4 Verify apply.sh outcome against manifest

After `apply.sh` completes, bale recomputes the staging tree state
and reconciles it against the manifest:

- Every file in staging that does not exist in the pre-apply project
  state: must be in `manifest.changes` as `action: created`.
- Every file removed (in pre-apply, absent in staging): must be in
  `manifest.changes` as `action: deleted`.
- Every file whose sha256 changed: must be in `manifest.changes` as
  `action: modified` with matching sha256.

If the reconciliation fails (apply.sh touched an undeclared file, or
failed to perform a declared delete), bale rejects the tarball, wipes
staging, and exits non-zero. The branch has not been created at this
point — no git side effects.

### 8.5 Validate

Validation runs in the staging copy. The bale branch is created at
HEAD but not checked out until validation passes — this keeps the
working tree clean on failure.

1. Create the bale branch: `git branch bale/<sid> HEAD`. Do not check
   it out yet.
2. Place the response manifest at `staging/.bale-manifest.json` so
   `validation.sh` can read the claims for the reconciliation block.
3. Run `bash validation.sh` with `cwd=staging/`. Capture stdout,
   stderr, exit code, and the claims-vs-verdict reconciliation block.
4. Stream output to `.bale/logs/<sid>.log` and (if `--verbose`) to
   the terminal.

Validation exit codes (per `TARBALL.md` 7.5):

- `0` — passed.
- `1` — at least one check failed.
- `2` — the script itself errored. Surfaced distinctly in the
  walkthrough: *"validation script itself errored; inspect the
  script."*

### 8.6 Commit or hold

The commit step is driven per-manifest-entry from `changes[]` rather
than by a tree-level diff. The manifest is the contract; the commit
shape follows it directly.

The **integration lock** (`.bale/integration.lock`, ADR-0006) is
acquired before the checkout below and held across the §8.6–§8.8
window — the stretch where bale mutates the user's checkout.
Integrations serialize under it; with one open session it is
uncontended. It releases at each terminal action once the git work is
done. A crash inside the window leaves it held, and the acquire-time
refusal message is the stale-lock story: it names the recorded holder
(sid, pid, acquire time) and the clear surface — `bale unlock
--integration` removes the stale file through the tool (removing it by
hand is equally safe whenever no apply is running).

If validation exited 0:

1. `git checkout bale/<sid>` (the branch was created at the original
   HEAD in 8.5).
2. For each `manifest.changes[]` entry, apply per-file to the working
   tree:
   - `created` or `modified`:
     `cp staging/<path> <project>/<path>; git add <path>`
   - `deleted`:
     `git rm <path>` (removes the file and stages the deletion)
3. `git commit -m "[bale <sid>] <summary>"` where `<summary>` is
   `manifest.summary`.
4. Mark the branch as `[PASS]` for the walkthrough.

If validation exited 1 or 2:

1. The branch already exists at HEAD (from 8.5). `git checkout
   bale/<sid>`.
2. Apply changes to the working tree using the same per-manifest-entry
   approach as the PASS path above, but **do not commit**. The branch
   carries staged-but-uncommitted changes so the user can inspect
   exactly what would have landed.
3. Mark as `[HOLD]` with the reason from validation output.

### 8.7 Walkthrough

Print a summary block:

- The sid, the origin branch, and `manifest.summary`.
- Each validation check with its `[PASS] / [FAIL] / [SKIP]` status.
- The claims-vs-verdict reconciliation table.
- A diffstat between `origin_branch` and `bale/<sid>`.
- `notes.md` contents if the file exists (skipped silently otherwise).
- `next-prompt.md` contents if the file exists (skipped silently
  otherwise — absence means no follow-up).
- Inspection commands for the user (`git diff <origin>..bale/<sid>`,
  `git log bale/<sid>`, `cat staging/.validation-logs/...`).

Then prompt:

**If passed (`[PASS]`):**
```
[Enter/m] merge into <origin> (default)
[r]       revert — discard branch and commits
```

**If held (`[HOLD]`):**
```
[Enter/i] inspect — exit with branch held for review; clean up
                    later with `bale revert <sid>` or send a
                    corrected response
[r]       revert — discard branch and staged patches now
```

In `--no-interact` mode (or non-TTY): on PASS, auto-merge. On HOLD,
exit non-zero with the branch held for inspection.

In `--no-interact` mode (per invocation, or per config via
`apply.no_interact = true`) the post-apply hook confirmation is
likewise not prompted: it resolves from `apply.hook_auto_accept` in
bale.toml (unset or false = decline, the prompt's default), and every
bypassed prompt — walkthrough and hook alike — logs the decision taken
and its source. Plain non-TTY without the mode keeps the pre-existing
behavior: walkthrough defaults taken silently, hook prompts declined
on EOF.

### 8.8 Terminal actions

- **Merge** (PASS only). `git checkout <origin>; git merge --no-ff
  bale/<sid>`, then `git tag applied/<sid>`, close the session in the
  registry (marker removed, pointer cleared — ADR-0006), clean up
  `.bale/sessions/<sid>/`, release the integration lock, delete
  `bale/<sid>` branch. The `applied/<sid>` tag is the durable record.
  Final line to the user: *"To roll back this bale: `bale rollback
  <sid>` or `bale rollback` for the most recent."*
- **Inspect** (HOLD only). The session stays open in the registry;
  branch persists with staged uncommitted changes. The integration
  lock releases — this invocation's git mutation is over, and the
  held state is guarded by the registry entry plus the branch
  itself. The user investigates the failure,
  then chooses: discard via `bale revert <sid>` (branch deleted,
  session closed in the registry, project back to origin), send a
  corrected response through `bale retry <tarball>` in the same
  session, or send Claude the failure
  context and request a corrected response as a fresh session. That
  fresh-session path is: `bale revert <sid>` first, then `bale pack` a new
  request that includes the failure context, then apply the new
  response. That new response's manifest sets `corrects: <held_sid>`
  as a history pointer — the corrected work itself runs as a fresh
  session against origin, not layered onto the discarded branch.
  Final line: *"Branch `bale/<sid>` is held for inspection. Run
  `bale revert <sid>` when done. If sending a corrected response,
  the new response should set `corrects: <this_sid>` for history."*
- **Revert.** Delete the branch (forcefully), wipe
  `.bale/sessions/<sid>/`, close the session in the registry, release
  the integration lock. Same operation regardless
  of whether validation passed or held.

---

## 9. Rollback, revert, unlock

Three commands cover three distinct "undo" cases. The distinctions
matter because they operate on different git states.

### 9.1 `bale revert [sid]` — staged, not yet merged

For a bale branch that exists but hasn't been merged into the origin
branch yet. The common case is a held branch after a failed
validation when inspection is done. Passed-and-kept is no longer a
state in the current design — passing snaps merge or revert within
the apply walkthrough.

The sid is optional (ADR-0006 threading): with exactly one session
open it resolves implicitly, and with several open an explicit sid is
required — the refusal lists the candidates. An explicit sid may also
name a session the registry no longer shows open; revert's own
metadata and branch checks below then decide whether there is
anything to discard.

Steps:
1. Read `origin_branch` from `.bale/sessions/<sid>/origin_branch`.
2. Verify `bale/<sid>` is **not** an ancestor of `origin_branch`. If
   it is, that means it was already merged; redirect the user to
   `bale rollback <sid>`.
3. Refuse on a dirty working tree by default (a dirty tree would
   block the checkout in step 4 anyway). `--force` overrides.
4. If currently on `bale/<sid>`, `git checkout <origin_branch>`. Log
   the checkout.
5. `git branch -D bale/<sid>` (force delete).
6. Wipe `.bale/sessions/<sid>/`.
7. Close the session in the registry if it was open: remove its
   `open` marker (already gone with step 6's wipe; the close is what
   reconciles the compatibility pointer, repointing it to the oldest
   remaining open session or clearing it). The close targets this
   sid, never whichever session the pointer happens to name.

The function owns the full flow — the user doesn't switch branches
or run any preliminary command. A single `bale revert <sid>` leaves
them on their origin branch with the bale branch gone.

### 9.2 `bale rollback [sid]` — applied, merged into origin

For a bale that has been merged (tagged `applied/<sid>`). Uses
`git revert` (history-preserving), tagged, and itself reversible.

**Default behavior (no sid):** identify the most recent `applied/<sid>`
tag on the current branch and roll it back.

Steps:
1. Find the `applied/<sid>` tag. If no sid is passed, scan
   `applied/*` tags reachable from HEAD and pick the most recent by
   tagger date (or, equivalently, by commit date of the tagged
   commit).
2. Find the commit the tag points to. Determine if it's a merge
   commit (`git rev-parse --verify <commit>^2` succeeds) or a normal
   commit.
3. Refuse on a dirty working tree by default. Offer `--stash` to
   `git stash` before running and `git stash pop` after.
4. Refuse if `reverted/<sid>` already exists, unless `--force`.
5. Run `git revert --no-edit -m 1 <commit>` (merge) or
   `git revert --no-edit <commit>` (normal). Conflicts leave the
   revert in progress; bale prints the affected files and exits
   non-zero, instructing the user to resolve and
   `git revert --continue`.
6. On clean revert: amend the commit message to
   `[bale rollback <sid>] <original summary>`.
7. `git tag reverted/<sid>` at the new commit.

**`--undo`:** finds the most recent `reverted/<sid>` and reverts that
revert commit. Tags `re-applied/<sid>`. Symmetric — the user can
toggle freely.

**`--list`:** show recent `applied/<sid>` tags with rollback status
(reverted, re-applied, untouched).

### 9.3 `bale unlock [sid]` — abandoned session

For when the user ran `bale pack`, got distracted, and never sent or
applied the tarball. The session is open in the registry but there's
no git side effect to undo.

The sid is optional (ADR-0006 threading): with exactly one session
open it resolves implicitly, with several open an explicit sid is
required (the refusal lists the candidates), and an explicit sid must
name an open session.

Steps:
1. Read the session registry.
2. If no sid was given and nothing is open: benign no-op, exit
   cleanly — after one cleanup duty. A non-empty `current_session`
   pointer with no matching open marker is the crash-debris
   half-state an interrupted pack can leave (§7.6's write ordering
   confines interruptions to exactly this benign shape); unlock
   clears the stale pointer and says so. The named sid's session
   directory, if any, is left alone: with no open marker it is
   either the same inert debris or a consumed bailout's record,
   which `bale handoff`'s lineage chase still reads.
3. Resolve the target session (explicit sid, or the single open
   one). If the sid has a corresponding `bale/<sid>` branch: refuse.
   This means apply ran but didn't reach a terminal state. The user
   should use `bale revert <sid>` instead.
4. Otherwise: close the session in the registry (its `open` marker
   is removed and the compatibility pointer reconciled — repointed
   to the oldest remaining open session, or cleared), then remove
   `.bale/sessions/<sid>/`. Done. No git operations.

`--force` overrides the step-3 refusal, but with a prominent warning
and a note in the log.

**`bale unlock --integration`** is the second unlock surface: it
clears the repo-level integration lock (§8.6) left stale by an
interrupted apply — the stale-lock story ADR-0006 called for, and
the command the acquire-time refusal names. It takes no sid (passing
one is an error: the integration lock is repo-level state, not a
session), reports the recorded holder it cleared, is a benign no-op
when the lock isn't held, and reminds the user it is only safe while
no `bale apply` is running. It touches no session and no git state.

### 9.4 Why three commands instead of one smart command

A smart `bale undo` that figures out what to do is tempting but
dangerous. Each of the three operations has different consequences:

- `revert` destroys a local branch (no shared history at risk).
- `rollback` writes new history that anyone pulling will see.
- `unlock` touches only bale's local state.

The user benefits from knowing which one they're running. Naming
them differently makes the cost visible.

### 9.5 Lock state lifecycle

With ADR-0006 the lifecycle below holds **per session**: each state
row reads against a session's registry entry (its
`sessions/<sid>/open` marker) rather than the repo-wide sentinel. The
`current_session` compatibility pointer tracks the registry in
lockstep (naming the most recently opened session, repointed on
close — §3.4) but is informational only; every command resolves
sessions through the registry itself, with revert/retry/unlock taking
an optional sid that is required only when several sessions are open.
While at most one session is open, the table is observably identical
to the old single-lock reading; with several open (admitted since
ADR-0007's gate landed) each session moves through the same states
independently, and integrations serialize under the §8.6 integration
lock. The three reachable states per session:

| State | Registry | Branch | How you got here | How you leave |
|-------|---------------|--------|-------------------|----------------|
| Closed | no `open` marker | none | initial, post-merge, post-revert, post-unlock, post-bailout | `bale pack` |
| Open, no branch | marker present | none | post-`bale pack` / post-`bale handoff`, before `bale apply` | `bale apply` (any walkthrough path) or `bale unlock [sid]` |
| Open, with HOLD branch | marker present | `bale/<sid>` w/ uncommitted staged changes | `bale apply` hit validation failure; user chose inspect | `bale revert [sid]`, `bale retry <tarball> [--sid]` with a corrected response, or apply a corrected response (after `bale revert [sid]`) |

Passed-and-kept is not a state. The apply walkthrough resolves
PASS to either merge (→ empty + `applied/<sid>` tag) or revert
(→ empty) before returning control.

`bale unlock` is for the middle state only — it refuses on the
third state (use `bale revert` instead). `bale rollback` operates
on the durable record (`applied/<sid>` tags) and doesn't touch the
registry at all.

---

## 10. Git init walkthrough

When `bale pack` is invoked in a directory that is not a git repo,
bale offers to set it up.

The walkthrough applies the same path-location and home-directory
refusals from section 7.1 (steps 1 and 2) **before** initializing.
`git init` at `/`, `/home`, or other system roots would be
catastrophic; bale refuses such locations categorically with no
override. The home directory itself requires `--force` to proceed.

Flow:

```
$ bale pack

This directory isn't a git repository. Bale needs git for branch
staging and the rollback story.

Would you like me to set it up? [Y/n] > Y

Initializing repository...
  ✓ git init

Git identity (used for commit attribution on bale apply)
  git user.name: (unset)
  enter your name (Enter to skip): > Alice Example
  wrote user.name = Alice Example to repo-local git config
  git user.email: (unset)
  enter your email (Enter to skip): > alice@example.com
  wrote user.email = alice@example.com to repo-local git config

  ✓ Created .gitignore with bale's default exclusion set
  ✓ Staging all files in this directory
  ✓ Initial commit: "Initial commit (bale)"

Done. Continuing with bale pack...
```

Details:

- **Step order: init → identity → gitignore → commit.** `git init`
  runs first so the identity prompt has a repo to write into (next
  bullet). The single "Initializing repository..." header opens the
  block; the four steps print in order beneath it, with the identity
  prompts interleaved between `✓ git init` and `✓ Created .gitignore`.
- **user.name / user.email** — the two fields are checked
  independently. Each is read with `git config --get <key>` (no scope
  flag, so any scope — system, global, or repo-local — counts as
  set). A value found in any scope is reported as `(set)` and left
  alone. An unset field is prompted; a non-empty response is written
  to **repo-local** git config (`.git/config` in the new repo) and
  never to `--global`. An empty response (Enter alone, EOF, or ^C)
  is honored as a skip; bale prints a note that commits during this
  session may fall back to git's default attribution until the value
  is set. A repo whose identity is already set globally sees the
  `(set)` lines and no prompts at all.
- **`.gitignore`** — append bale's full baked-in exclusion set from
  §6.4 (bale/git internals, common build dirs, secret patterns) with
  a one-line note. If the file is absent, create it with the same
  patterns. The single bullet handles all of bale's default
  exclusions in one pass; the initial commit then just stages
  whatever's left.
- **Initial commit** — `git add -A` (everything not excluded by the
  newly-populated `.gitignore`). Commit message:
  `Initial commit (bale)`. This is the baseline rollback target.
- **Non-TTY fast-fail** — when stdin is not a TTY (piped input, CI
  runner, non-interactive shell), bale aborts before `git init`
  rather than attempting an unattended initialization. The
  walkthrough needs a TTY for both the confirmation prompt and the
  identity prompts; auto-initializing a repo in a non-interactive
  context risks landing one somewhere unexpected, which is a worse
  failure than refusing. The error names the recovery: re-run from
  an interactive shell, or run `git init && git add -A && git commit
  -m initial` manually and then retry `bale pack`.
- **Empty-initial-commit failure** — if `git commit` exits non-zero
  after `git add -A` (most commonly because every file in the
  directory matched the newly-populated `.gitignore` — e.g., a folder
  of nothing but `.env` files), bale fails the walkthrough explicitly
  rather than retrying with `--allow-empty`. An empty baseline would
  silently mask that every file got ignored, leaving the user with
  an apparently-initialized bale workspace that has nothing for bale
  to track. Failing loudly surfaces the mismatch. The repo is left
  in the init'd-but-uncommitted state; the error names the recovery
  (add a trackable file such as `README.md` and re-run `bale pack`).
  The subsequent run finds the repo via `repo_root` and skips the
  walkthrough entirely.
- **Decline path** — if the user answers `n`, bale prints
  *"bale requires a git repo. Re-run after `git init` or accept the
  walkthrough."* and exits 0.

The walkthrough is the **only** non-bale-related git action bale
performs. After this, bale only runs `git branch`, `git checkout`,
`git commit`, `git merge`, `git revert`, `git tag` — all session-
related.

---

## 11. Bale-enforced contract (full list)

Every check below runs mechanically inside bale. Failure → reject
before staging (steps 1–12 of section 8.1) or before commit (sections
8.4 and 8.5). Nothing project-specific.

| # | Check | Phase |
|---|-------|-------|
| 1 | Path-location refusal (cwd / repo root not a system directory) | pack pre-flight |
| 2 | Home-directory refusal (cwd not exactly `$HOME`, unless `--force`) | pack pre-flight |
| 3 | Scope disjointness (ADR-0007): the pack's resolved include set is disjoint from every open session's recorded scope — directory entries cover subtrees, `.` covers everything, includes as a conservative proxy for change scope | pack pre-flight |
| 4 | Threshold caps (file count, size, depth) within configured limits | pack scope projection |
| 5 | Tar archive integrity (extractable, no path-traversal entries) | apply pre-flight |
| 6 | Manifest schema valid (all required keys, no unknowns) | apply pre-flight |
| 7 | An open session exists in the registry (ADR-0006) | apply pre-flight |
| 8 | Working tree clean (`git status --porcelain` empty), unless `--force` | apply pre-flight |
| 9 | `responds_to` names an open session in the registry (ADR-0006; with one open session, identical to the old locked-sid match — with several, it is the resolution key per §8.1 step 4) | apply pre-flight |
| 10 | Every `changes[]` path is in `files/` per its action (or absent for deletes) | apply pre-flight |
| 11 | Every `files/` entry is declared in `changes[]` | apply pre-flight |
| 12 | Every `changes[].sha256` matches the actual file | apply pre-flight |
| 13 | Every `changes[].reason` is non-empty | apply pre-flight |
| 14 | Path safety: no escape, no `.git/`, no `.bale/`, no `.baleignore` match | apply pre-flight |
| 15 | Every key in `claims` appears in `validation_will_run` (subset rule per TARBALL.md 5.3) | apply pre-flight |
| 16 | `manifest.json`, `apply.sh`, and `validation.sh` exist in the tarball (README/notes/next-prompt are optional) | apply pre-flight |
| 17 | `apply.sh` exits 0 | apply stage |
| 18 | Post-`apply.sh` staging state matches the manifest — every created/deleted/modified path matches a `changes[]` entry, no undeclared writes/deletes (this is where `apply.sh` operations are constrained: no `mv`, no untracked file changes) | apply post-stage |
| 19 | Cross-session scope collision (ADR-0007): no `changes[]` path intersects another open session's recorded scope — the apply-time guard against the whole-file clobber (§8.1 step 7; listed here out of phase order to keep rows 5–18 stable) | apply pre-flight |

Project policy checks (INDEX coherence, ADR sequential, doc inventory
rules) live in the response's `validation.sh` — Claude includes them
per-session, not bale. Bale is project-agnostic.

Bale also does not enforce the request's `out_of_scope` field. That
field carries prose concerns, not glob patterns; mechanical path
matching against it isn't well-defined. Out-of-scope drift is a
policy concern, reviewed manually and surfaced by `TARBALL.md` §8's
"stay in the lane" rule. Projects wanting mechanical enforcement
add a glob deny-list to `validation.sh`.

---

## 12. Self-applicability

Bale is its own project. The bale repo contains a `claude/` doc
directory (its own `INDEX.md`, `STATE.md`, ADRs) and uses bale to
modify itself. There is no special "meta mode."

### 12.1 The hot-swap question

Patches to bale's own code take effect on the next invocation:
Python has loaded the old code into memory, so validation runs with
the old apply code against the new files on disk, and the HOLD path
recovers if the new code is broken. For v0.1, bale does not attempt
to exec the new code mid-apply; a `validation.sh` that wants to
invoke the new bale (e.g., to selftest) does so by absolute path.

### 12.2 Bootstrap

A two-stage bootstrap, classic chicken-and-egg.

**Stage 0 — hand-write v0.0.1.** A single Python file (`bin/bale`)
plus the three global docs as siblings under `docs/`, packaged as
the same `bale/` directory shape v0.1+ ships. The bootstrap script
can:
- pack a request tarball (minimum: inject all three global docs —
  `CLAUDE.md`, `TARBALL.md`, `DOCS.md` — read from `docs/` adjacent
  to the script, take a goal, include named files);
- apply a response tarball (minimum: manifest validation, sha256
  check, staging, run `validation.sh`, commit per-manifest-entry or
  hold);
- revert a staged branch.

v0.0.1 has no rollback, no wizard, no walkthrough niceties, no
release-tarball packaging script. It ignores `apply.sh` entirely —
does not validate its presence, does not execute it — and handles
`action: deleted` entries by running `rm` against staging based on
the manifest. This is forward-compatible with v0.1: responses still
ship `apply.sh` per `TARBALL.md`, v0.0.1 just doesn't look at it.
v0.1 picks up proper `apply.sh` handling and the post-run
reconciliation check. It's the smallest tool that can apply its own
first response tarball.

The `bale/` directory layout (`bin/bale` + `docs/*.md`) is fixed
from v0.0.1; v0.1 adds the packaging step that turns that layout
into a distributable release tarball, but the layout itself doesn't
restructure.

v0.0.1 is hand-written and predates any Claude session, so
`CLAUDE.md` section 6's "tests ship with code" rule (which governs
Claude's tarball output) doesn't strictly apply. The same gap
extends through v0.3, however: the test harness itself doesn't
arrive until v0.4. Each session producing v0.1–v0.3 carries a
`notes.md` deferral explicitly naming this — *"tests deferred to
v0.4 (harness lands there)"* — rather than silently shipping
untested code. v0.4 closes the gap retroactively by exercising the
prior versions' code paths through the selftest harness.

**Stage 1 — apply the first response.** A tarball Claude returns
fleshes out the rest of v0.1: wizard, walkthrough, apply.sh, rollback,
the release-tarball packaging script. From this point forward, every
change to bale is a bale session on its own repo.

### 12.3 Why no `bale meta` subcommand

The reference implementation that informed this design had a
`bale meta` mode for self-application. We don't need it. The bale
tool's repo is just another project; sessions on it work exactly like
sessions on any other project. The only subtlety is the hot-swap
behavior in section 12.1, which is documented but doesn't require
machinery.

---

## 13. Build phases

### v0.0.1 — bootstrap

Single Python file (`bin/bale`) plus sibling `docs/` directory,
hand-written. Just enough to apply its own first tarball:

- `bale pack <goal> --include <paths>` — minimum viable; no wizard,
  no `.baleignore` handling, no exclusion-of-large-files.
  **Baked-in secret-pattern exclusions from section 6.4 ship in
  v0.0.1** — the cost of a leaked `.env` once is higher than the
  engineering cost of including the pattern list at bootstrap.
- `bale apply <tarball>` — manifest validation, sha256, path safety,
  staging, ignore `apply.sh` if present (deletes handled directly
  from the manifest), run `validation.sh`, commit per-manifest-entry
  or hold, no walkthrough (just print pass or hold).
- `bale revert <sid>` — discard a held branch.

No rollback, no unlock, no release-tarball packaging script. The
working layout is the install layout: `bin/bale` (with shebang and
`chmod +x`), the three global docs at `docs/CLAUDE.md`,
`docs/TARBALL.md`, `docs/DOCS.md`, plus `install.sh`, `validate.sh`,
and the user-facing `README.md` at the top. `install.sh` finalizes
an install (chmod, optional PATH symlink, runs `validate.sh`);
`validate.sh` sanity-checks an install's layout and CLI surface.
The user runs `bin/bale` directly by path or symlinks it onto
`PATH` via `install.sh`. The release-tarball *packaging* script
(a build target that turns this layout into a versioned
`bale-vX.Y.Z.tar.gz`) is v0.1's job; at v0.0.1 a release is just
`tar -czf bale.tar.gz bale/` against this layout.

bale-src — the source repo for the bale tool — has the same six
top-level items as the release plus `BALE.md`, `bale.toml`,
`scripts/`, and `claude/`. Those extras are this design doc, a
per-repo configuration file, hook scripts wired through that file,
and bale-src's project doc map. They are not part of the release
tarball and are not mirrored by `scripts/reinstall.sh`. A user who
only installs the release tarball never sees them.

### v0.1 — usable v1

Apply a tarball from Claude that adds:

- The full pack pipeline: wizard, `$EDITOR` integration, baked-in
  exclusions, `.baleignore`. *(Wizard and `$EDITOR` for the README
  step landed in v0.0.9. `.baleignore` plus the wizard's excludes
  prompt and the §7.4 soft-cap `[e]` edit-excludes branch landed in
  v0.0.10. Baked-in exclusions landed in v0.0.1.)*
- The full apply pipeline: `apply.sh` handling, manifest
  reconciliation after staging, walkthrough. *(All landed in v0.0.2.)*
- `bale unlock`. *(Landed in v0.0.5.)*
- The release-tarball packaging script (`scripts/build.sh` in the
  bale repo) that bundles `bin/` and `docs/` into
  `bale-vX.Y.Z.tar.gz`. *(Landed in bale-src ahead of the v0.1.0
  cut; v0.1.0 is the first release built with it.)*
- Git-init walkthrough. *(Landed in v0.0.8.)*

v0.1.0 is the cut: VERSION bumped from 0.0.10 to 0.1.0, with two
small quality-of-life touch-ups landed alongside the bump
(`--include` / `--exclude` now accept multiple paths per flag;
TARBALL.md §5.2's example aligned to the literal-string preflight
in §11 row 15).

### v0.2 — rollback

`bale rollback`, `--undo`, `--list`, `--stash`. Its own phase because
of the conflict and merge-commit edge cases that deserve careful
selftest coverage. *(Landed in v0.2.0 as the sibling `bin/bale_rollback.py`
module — net-new code, not an extraction. Tests deferred to v0.4 with the
rest of the v0.1–v0.3 line, since the selftest harness lands there; the
conflict and merge-commit paths were exercised manually in the landing
session, noted in that session's `notes.md`.)*

### v0.3 — polish

- Inline help (`bale help <cmd>`). *(Landed in v0.2.2 as the `help` and
  `completion` subparsers in `bin/bale` section 25, dispatching through a
  small introspection layer in the new section 24. `bale help` and `bale
  help <cmd>` both work, plus the two-level `bale help config init`; the
  unknown-command path prints the available list and exits non-zero.)*
- `--show-validator`, `--show-apply-script`, `--dry-run`. *(Landed in
  v0.2.1 on the `apply` subparser — the show flags are pure tarball
  inspection needing no open session, `--dry-run` runs the read-only
  validation half against the open session and prints the plan without
  touching the worktree or git. The behavioral paths were exercised
  manually in the landing session plus a temp-repo show-script check in
  that response's `validation.sh`; full coverage waits on the v0.4
  harness.)*
- `--verbose` mode for apply (stream validation output live). *(Landed in
  v0.2.1, apply-scoped: `run_validation_sh` now routes `validation.sh`
  output to the session log only by default and live-streams to the
  terminal under `--verbose`, per §8.5 step 4. Wiring `--verbose` across
  the other commands the §5.4 global-flags list anticipates, and the §7.4
  pass-through of `--verbose` into `validation.sh` itself, remain open.)*
- Optional bash completion (`source` it from shell rc — not required
  for any functionality). *(Landed in v0.2.2 as `bale completion bash`,
  which walks `build_parser()` once and emits a self-contained bash
  function that does pure-shell dispatch — no subprocess back to bale per
  Tab press. Both the help command and the completion script read the
  same source of truth, the argparse parser, so adding a flag in one
  place propagates to both surfaces automatically.)*

v0.3 is not yet cut: the four apply flags above and apply-scoped
`--verbose` landed in v0.2.1, inline help and bash completion landed in
v0.2.2, and one thread remains open — the `--verbose` extension to
commands beyond `apply` and the §7.4 pass-through of `--verbose` into
`validation.sh` itself. The cut waits on that thread, or on an explicit
architect's call to cut now and track the remainder under v0.3b.

### v0.4 — selftest

End-to-end harness. Spin up a temp git repo. Pack, apply, validate,
rollback through every code path. Held states. Conflicts. Stale
locks. Reverts. Re-apply.

### v0.5+ — extensions to `bale.toml`

Per-project and global configurables already exist (`bale.toml` at
both layers, with the `[hooks]` and `[apply]` sections shipped through
the v0.0.x line — see `claude/context/bale-internals.md`). v0.5+ is
where additional keys earn their place under that mechanism if a use
case argues for them. Candidates that have come up in conversation
but not landed:

- Staging directory override (currently `--staging-dir` on the
  command line only).
- Tuning the baked-in exclude set (adding to it; removing requires
  more care since the secret patterns are non-negotiable per §6.4).
- An optional response-archive location (e.g.
  `archive_dir = "claude/responses"`) so the apply pipeline can copy
  whichever of `README.md`, `notes.md`, and `next-prompt.md` the
  response actually included into the project's archive convention.

Any addition extends `bale_config.walk_configurables()` and
`render_bale_toml()` in the same session — the wizard owns the
discoverable surface (bale-internals.md §2.5).

---

## 14. Resolved decisions

Decisions that were open during design but have since been settled
by the implementation. Recorded here as a historical trace; there
are no currently-open items in this section. New decisions go in an
ADR (`claude/context/adr/`) per DOCS.md §5.

### 14.1 Bootstrap approach — option (a) chosen

Two options were on the table for v0.0.1:

- **(a)** Hand-write the smallest possible bale and use it to apply
  the first tarball that fleshes out v0.1.
- **(b)** Hand-write the entire v0.1 and treat the snapshot system
  as the workflow for future changes only.

Implementation took (a). The v0.0.x line bears it out: every
v0.0.N>1 patch has been a bale session on the previous version.
The bootstrap discipline paid off on the first session that
surfaced an exec-bit-stripping bug in the apply path (see
`claude/context/meta-sessions.md` §2), which is exactly the class
of issue the meta-sessions framing predicted.

### 14.2 Tarball file naming — option (b) chosen

Two options were on the table:
- **(a)** `request-NNN.tar.gz` / `response-NNN.tar.gz` (matches the
  directory inside).
- **(b)** Include the sid: `request-2026-05-12-foo-001.tar.gz`.

Implementation took (b) for the outbound tarball name: `bale pack`
writes `.bale/outbox/request-<sid>.tar.gz`, and `bale handoff`
follows the same convention. The directory inside still uses
`request-NNN/` / `response-NNN/` for the cleaner archive structure.

---

## 15. Hard nots

- **Not a project workflow tool.** Bale orchestrates sessions, not
  workflows. The workflow is in `CLAUDE.md` / `TARBALL.md` /
  `DOCS.md` / `CODE.md`, applied at the user's discretion.

For the implementation-scope list (what bale does NOT do), see
section 2.2.

---

End of BALE.md.
