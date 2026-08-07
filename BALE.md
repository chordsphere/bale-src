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
3. **Apply** — validate the response mechanically, run the response's
   `apply.sh` and `validation.sh` in a staging copy, commit the result
   to a session branch with git plumbing (the user's checkout is never
   consumed — ADR-0008), walk through merge/inspect/revert.
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
- Revert committed-not-merged snaps (discard the session branch).
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
- Log / blame / diag commands. Inspection beyond `bale status`'s
  read-only dashboard (§5.5) is a Claude session: ask Claude what's
  going on and paste output of `git log` or similar. Bale does not
  duplicate git's read commands; `bale status` reports bale's own
  state (sessions, outbox, staging, config), not git's history.
- Probe handling. Probes are session-scoped only — Claude returns a
  script in chat, the user runs it, the user pastes output back into
  the next message. Bale does not see probes.
- Out-of-scope enforcement, in the prose sense. The request's
  `out_of_scope` field is prose, not glob patterns; bale does not
  mechanically check paths against it. Drift against that prose
  field is a policy concern, surfaced at review under the
  stay-in-the-lane rule (`CLAUDE.md` §6) — distinct from own-scope
  *path* drift, which §11 row 22 enforces mechanically.

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
      origin_branch            # the session's integration target,
                               # stamped at pack/handoff time
                               # (ADR-0008, §7.6); required — apply
                               # hard-refuses a session with a
                               # missing or empty stamp (§8.1
                               # step 5); pack and handoff refuse
                               # a detached HEAD up front (§7.1
                               # step 4a, §11 rows 23–24) so
                               # neither can skip the stamp
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
   every `<repo>/bale.toml`. The key names the machine's inbound
   directories, consulted by every relative inbound-file argument:
   apply/retry/handoff's tarball and pack's `--readme-file` (§7.3).

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
| `bale pack` | Build a request tarball from the project + user-specified scope. `--read-only` opens the read-only session shape — empty recorded scope; locks nothing, lands nothing (v0.3.15) — and, since v0.3.21, also sweeps: offers (accept default; piped stdin declines) to close an open read-only session as `closed-read-only`. `--supersedes <sid>` declares a split supersession of an open session (v0.3.17); all in §7.2. | v0.0.1 |
| `bale apply <tarball>` | Validate and apply a response tarball. Terminal — the wizard ends in merge, revert, or (on HOLD) leaves the session commit on `bale/<sid>` for inspection. The checkout is never consumed (ADR-0008). | v0.0.1 |
| `bale retry <tarball> [--sid]` | Re-attempt a HOLDed session with a corrected response tarball, keeping the session open so the new attempt lands in the same session id. The sid resolves implicitly with one session open; `--sid` picks when several are (ADR-0006). Takes apply's per-attempt flags — `--verbose`, `--no-interact`, `--allow-out-of-scope`, `--json` (parity as of v0.3.14) — since retry reruns the same pipeline; apply's inspection flags (`--show-validator`, `--show-apply-script`, `--dry-run`) are deliberately retry-absent, because they never touch the HOLD state and work verbatim through `bale apply`. | v0.0.x |
| `bale revert [sid]` | Discard a held bale branch (validation failed and inspection is done, or user changed their mind). Sid optional with one session open, required with several. `--reason` (v0.3.16) and `--json` (v0.3.19) per §5.4; flow in §9.1. | v0.0.1 |
| `bale rollback [sid]` | `git revert` an applied bale. Defaults to most recent. `--undo` / `--list` / `--stash`. Clean rollback and clean `--undo` append to the session's telemetry record (v0.3.18, §9.2). | v0.2 |
| `bale unlock [sid]` | Close an abandoned session (sid optional with one open, required with several), or `--integration` to clear a stale integration lock. `--reason` (v0.3.16) and `--json` (v0.3.18) per §5.4; flow in §9.3. | v0.0.5 |
| `bale handoff <tarball>` | Repackage a bailout response (TARBALL.md §5.6) into a fresh request tarball that inherits the bailed-on session's goal. Stamps the new session's integration target the same way pack does (§7.6), and refuses a detached HEAD in its pre-flight the same way pack does (§7.1 step 4a, §11 row 24) — before any tarball resolution, prompt, or session state; remedy: check out the branch the new session should integrate into, then re-run the handoff. Since v0.3.33 it also runs the checkpoint blindness gate pack runs (§7.1 step 4b, §11 row 30) against its reading-plan scope — pre-sid, one gate implementation shared with pack — refusing a handoff whose scope covers the configured blind checkpoint; `--allow-checkpoint-in-scope` (per-invocation, flag-only, mirroring pack's spelling) admits it, FORCE-logged, with `checkpoint_scope_admitted: true` stamped into the new request's provenance through the shared builder. | v0.0.6 |
| `bale config init` | Walk through every configurable at the chosen layer (project or `--global`) and write the resulting `bale.toml`. The canonical discoverable surface for configurables; see `claude/context/bale-internals.md` §4. | v0.0.3 |
| `bale status` | Read-only summary of the repo's bale state: session lifecycle, outbox, applied pointer, config. Takes no lock, writes nothing, always exits 0 on a successful read. `--json` for the stable machine contract. See §5.5. | v0.2.3 |
| `bale stats` | Read-only aggregation of the tracked `claude/telemetry/` corpus into the trust ledger's rates: per-work-class claim/verdict agreement, HOLD, checkpoint-HOLD, drift-refusal, bailout, and clarification rates, the required-check refusal/override counts, closure mix, epoch and coverage rows, and the dual-stream cross-checks. `--work-class`, `--since`, `--json`. See §5.6. | v0.3.24 |

No `log`, no `blame`, no `diag`. Inspection beyond `bale status`'s
read-only dashboard (§5.5) and `bale stats`'s corpus aggregation
(§5.6) is a Claude session — bale does not duplicate git's read
commands.

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

- `--force` — bypass a command's overridable safety refusals; the
  override is logged prominently with a `FORCE:` prefix. Per command:
  pack and handoff bypass the home-directory refusal and the
  threshold caps; rollback bypasses its dirty-tree refusal (without
  stashing) and the already-reverted / already-re-applied refusals
  (§9.2); unlock bypasses the branch-exists refusal (§9.3). The
  system-directory refusal has no override anywhere (§7.1), the
  detached-HEAD refusal likewise has no `--force` override on either
  request-building command (pack: §7.1 step 4a; handoff: §11 row 24),
  and `bale apply` takes no `--force` at all — the narrow
  dirty-on-target rule (§8.1 step 5) has no bypass; its remedies are
  stash, commit, or switch branches.
- `--verbose` — stream validation output and other long-running
  command output to stdout in addition to the log file. (Landed
  apply-scoped in v0.2.1 — `bale apply --verbose` streams `validation.sh`
  output live — extended to `bale retry --verbose` in v0.3.14 via flag
  parity, and closed across the surface in v0.3.35: `bale pack
  --verbose` streams the filter-chain drop decisions and the tarball
  build trail, `bale revert --verbose` streams the discard's captured
  git output, and on the apply/retry verbose path the flag is also
  forwarded onto `validation.sh`'s own argv so the script's TARBALL.md
  §7.4 verbose mode engages inside it, not just around it. The
  remaining commands carry no captured long-running surface warranting
  the flag — handoff's tarball build is the one candidate, deliberately
  left quiet until a session asks for it.)
- `--no-interact` — non-TTY mode. Skips prompts; the default action
  (Enter key equivalent) is taken at every prompt point. (Landed
  apply-scoped in v0.2.5 — `bale apply --no-interact` and `bale retry
  --no-interact`, also enable-able per config via `apply.no_interact`
  in bale.toml; wiring it across the other commands listed here is
  future work. In this mode the pre-hook confirmation resolves from
  `apply.hook_auto_accept` — unset/false takes the prompt's decline
  default — and every bypassed prompt logs the decision taken and its
  source to the terminal and the session log.)
- `--allow-out-of-scope <path>` — apply-scoped, repeatable (one path
  per flag): admit exactly the named `changes[]` path(s) past the
  own-scope drift gate (§8.1 step 14, §11 row 22); any other
  out-of-scope path still refuses. Per-invocation only — there is
  deliberately no config key, so an override never becomes standing
  policy — and every use is logged prominently and stamped into the
  session's telemetry record (§8.9). `bale retry` takes the same flag
  (v0.3.14): a retry attempt runs the same drift gate, and the
  override is never carried forward from the failed apply attempt —
  the operator re-states it at retry, so an overridden apply that
  HOLDs is not iced out of its own session. Overrides admitted on any
  attempt, apply or retry, are stamped per-attempt (§8.9).
- `--allow-missing-required-check <name>` — apply-scoped, repeatable
  (one check name per flag; board 6 session B): admit exactly the
  named required check(s) past the required-check superset gate
  (§8.1 step 15, §11 row 26) despite their absence from the
  manifest's `validation_will_run`; any other missing required name
  still refuses. The override's unit is the check name — the gate's
  own unit. Per-invocation only — there is deliberately no config
  key, per the ratified override contract (a standing config opt-out
  is the rejected self-oracle-adjacent silent bypass) — and every
  effective use is logged prominently (FORCE: line) and stamped into
  the session's telemetry record as `required_check_overrides`
  (§8.9). `bale retry` takes the same flag: the gate reruns on retry
  and the override is never carried forward from the failed attempt
  — the operator re-states it, exactly as with
  `--allow-out-of-scope`.
- `--json` — swap the command's end-of-run report for one line of
  JSON on stdout, under a shared stream discipline: `[bale] `
  informational lines and the human block go to stderr, stdout
  carries exactly the JSON line, and refusal paths stay
  fail()-shaped — stderr, non-zero exit, nothing on stdout. Landed
  per command: pack (v0.2.7), apply (v0.2.8), status (v0.2.9), retry
  (v0.3.14), unlock (v0.3.18), revert (v0.3.19); `bale unlock
  --integration --json` is refused, that report being
  session-shaped (§9.3). Each report's key contract is owned by its
  `format_*_json` docstring in `bin/bale_report.py` — stable keys,
  additions only — never by a copy in this doc.
- `--reason <choice>` — on `bale unlock` and `bale revert`
  (v0.3.16): stamp why the session closed into its telemetry record
  as `closure_reason` (§8.9 owns the vocabulary and the inference
  that runs when the flag is absent). An explicit reason beats
  unlock's read-only inference; revert without the flag records
  null.
- `--staging-dir <path>` — override the default
  `<repo>/.bale/staging/<sid>/` location (section 8.3). The override
  is used verbatim — no `<sid>` suffix — and refused if it exists.
- `--clean` — remove the staging directory after a successful apply.
  Default keeps it for inspection.
- `--max-files <N>` / `--max-size <bytes>` / `--max-depth <N>` —
  override the pack threshold caps. See section 7.4.
- `--no-gitignore` — disable `.gitignore`-based exclusion during
  pack. See section 6.4.

Flags scoped to a single command are documented in that command's
section.

### 5.5 `bale status`

Read-only dashboard for the working directory's bale (v0.2.3). It
takes no lock, makes no git or filesystem writes, has no clean-tree
requirement, and degrades gracefully outside a git repository or in
a repo that has never run bale. It always exits 0 on a successful
read: problems — an abandoned lock, a malformed `bale.toml`, stale
staging leftovers — surface as rows, not as a failing exit code, so
it stays usable as the first thing run when a repo's bale state is
unclear.

The human output is one summary block, rows emitted only for facts
that apply: the tool version; the repo (root, branch, working-tree
cleanliness); the open session and its lifecycle state (the §9.5
per-session lifecycle, classified for the oldest open session, with
a per-sid listing carrying recorded scopes when several are open);
the integration lock, only when sighted (it is held only across
apply's git window, so a sighting is a concurrent apply or a stale
lock); the stamped request's goal and `expects_probe`; the
classified session's recorded scope (a read-only session's empty
scope renders as such — "locks nothing, lands nothing" — never as an
empty string or a whole-tree reading; v0.3.15) and effective staging
posture; the classified session's clarification facts when preserved
records exist (v0.3.22 — a dedicated `clarification` row: rounds,
blocking-question count, latest record path under
`.bale/clarifications/<sid>/`), with a clarification-suspended
session (§8.10.2) classified as its own lifecycle state —
distinct from packed and, critically, from orphan, whose
`bale unlock` hint would discard the suspension — and the trailing
next-step hint saying so: answer the questions, then apply the
follow-up normal response; the outbox (capped, newest first, the open session's own tarball
pinned to the front); a light pointer at applied history, deferring
the full applied/reverted view to `bale rollback --list`; and the
config summary. A `[STATUS] <sid>` headline appears when a session
is open, and the next-step hint is the trailing line.

`--json` (v0.2.9) swaps the block for one line of JSON on stdout,
under the same stream discipline pack and apply use: `[bale] ` lines
go to stderr and stdout carries exactly the JSON line. **The
`format_status_json` docstring in `bin/bale_report.py` owns the key
contract** — the stable key set (existing keys never renamed or
removed; additions only), including the per-session staging-posture
keys added in v0.3.11. This doc deliberately does not duplicate the
key list; consult the docstring, not a copy here.

### 5.6 `bale stats`

The trust ledger's read side (v0.3.24, board 5): aggregate the
tracked telemetry corpus into the per-work-class rates that autonomy
grants (board 10) will be judged against.

`bale stats [--work-class CLS] [--since DATE] [--json]`

**Posture.** Read-only, the `bale status` family: no lock, no git or
filesystem writes, no clean-tree requirement, exit 0 on a successful
read. An absent or empty `claude/telemetry/` is an honest empty
report, not an error. The command reads **`claude/telemetry/` only —
never `.bale/`**: everything the rates consume lives on the tracked
side, so a fresh clone computes the same numbers as the original
machine, minus only records not yet committed there. The reader is
the filesystem, matching §8.9's write-to-working-tree posture —
uncommitted records count; git history is the corpus's timeline, not
its reader.

**What it reports.** One row per work class present in the filtered
corpus — sessions resolve to the class on their latest
feedback-bearing attempt, with an `unclassed` bucket for sessions
carrying none — with the headline rates: claim/verdict agreement
over checks, the unparsed-reconciliation share (a parse miss is a
tooling fact, never folded into agreement), HOLD rate, the blind
checkpoint's rows (v0.3.29, board 6 session D) — the
checkpointed-attempt count (validated attempts whose `checkpoint`
stamp reads `configured: true`; key absence is pre-epoch, the
known-zero `configured: false` form is post-epoch-unconfigured, and
neither enters the denominator) and the checkpoint-HOLD count and
rate over it, keyed on the stamp's own per-source `state` so a
checkpoint objection is counted whatever the worker's verdict was —
drift-refusal rate with override incidence beside it, the
required-check refusal and override counts beside the drift pair
(the step-15 gate's `required-check-refused` attempts and the
attempts carrying a non-empty `required_check_overrides` list; like
drift's, override incidence is a count, not a rate), rejection and
bailout figures, and the clarification rate over the sessions whose
closing attempt carries the promoted stamp (key presence with
`rounds: 0` is a known zero; key absence is pre-epoch unknown).
Blind-checkpoint outcomes never enter the claim/verdict counts: the
checkpoint has no claims by construction (§8.5), so agreement is the
worker's calibration stream alone.
Read-only sessions — detected by `closure_reason ==
"closed-read-only"`, never by an empty scope, whose `[]` reading is
overloaded by pre-ADR-0007 records — and crash-debris sessions are
excluded from every rate and reported as context and hygiene counts.
Around the table: the corpus epoch (first sid and date; pre-epoch
sessions exist only in git and are not counted — stats does not mine
git), the key-presence coverage rows for the `closure_reason`,
`clarification`, and `checkpoint` sub-epochs (the last since
v0.3.29 — the blind checkpoint stamp is present on every validated
attempt post-session-A, so presence detection is exact there too), the closure mix over closed sessions
(with `unlocked` broken out by reason — superseded-by-split parents
show there), the post-close churn counts (`rolled-back` /
`re-applied`; the applied attempt stays in every mechanical
denominator, and v1 deliberately does not reinterpret a rollback as
a defect signal), the in-flight count beside the mix, and the two
dual-stream cross-checks (self-reported clarification linkage vs the
promoted stamp; the `budget_pressure` distribution vs bailout
outcomes) reported beside the mechanical rates, never blended in.
Corrupt records are skipped, counted, and named on stderr; records
with `record_version > 1` are filtered and counted.

**Flags.** `--work-class CLS` filters the classed rows to one
resolved class (the §7 work classes plus `unclassed`) — the surface
board 10's per-class grant evaluation reads. `--since DATE` (ISO
date, inclusive, against `created_at`) restricts membership to the
recent corpus; the epoch and coverage rows remain whole-corpus facts,
and the filters in effect are echoed in the report. `--json` swaps
the human report for one line of JSON on stdout under the shared
§5.4 stream discipline. **The `format_stats_json` docstring in
`bin/bale_report.py` owns the key contract** — stable keys, additions
only (the same rule every `format_*_json` surface carries); this doc
deliberately does not duplicate the key list. Aggregation semantics
live in `bin/bale_stats.py`, whose docstrings restate the unit model
and every rate's numerator and denominator.

The human report renders the rate table and corpus rows as the
reference body and ends on the standard summary block — corpus
totals and the filters in effect — with no trailing next-step hint:
stats is terminal, not a lifecycle step.

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
  tools/
    response_lint.py   # injected by bale (v0.3.8): worker-side lint
    craft_response.py  # injected by bale (v0.3.19): response-skeleton crafter
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
  manifest.json
  apply.sh             # deletes + exec-bit restores; never mv (renames decompose into files/ + rm)
  validation.sh        # Claude's session-scoped checks against staging
  files/               # mirrors project tree from repo root
  README.md            # optional
  notes.md             # optional
```

`manifest.json` schema is `TARBALL.md` section 5.2. Bale enforces it.
`next-prompt.md` is retired (TARBALL.md §5.5); nothing new ships it. A
pre-retirement response that still carries one is tolerated at apply —
the walkthrough surfaces the body labeled deprecated (§8.7) rather
than rejecting the tarball or blending it in silently.

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
4a. **Detached-HEAD refusal.** Refuse if the repo's HEAD is detached.
   The session's integration target is stamped from the currently
   checked-out branch at persist time (§7.6, ADR-0008), and apply
   hard-refuses a session without the stamp (§8.1 step 5) — a
   detached-HEAD pack would create a session doomed to refuse at
   apply, discovered only after the tarball shipped. The refusal
   names the remedy: check out the branch this session should
   integrate into, then re-pack. No override flag — no session state
   a detached pack could produce would ever be applyable. (The
   git-init walkthrough path always lands on a branch, so this fires
   only for a pre-existing detached checkout.) (Labeled 4a: this
   check landed between steps 4 and 5 after steps 5–6 below were
   already cross-referenced externally, and cross-referenced numbers
   never renumber — DOCS.md §6.4 — so the insertion takes an
   interstitial label and the sequence keeps its original meanings.)
4b. **Checkpoint blindness pre-flight** (v0.3.28, board 6 session C;
   §11 row 27). When the merged config pins a blind checkpoint
   (`[validation] base`, §8.5), two refusals run before the step-5
   gate, on both of its firing paths (pre-flight when the forecast is
   final on the command line; post-wizard otherwise, beside the
   deferred gate): **dangling at the tip** — the checkpoint path has
   no committed file at HEAD (the §8.5 committed-is-ratified rule,
   caught at request-build time so a broken oracle reference never
   produces a session doomed to refuse at apply); **the write
   forecast covers
   the checkpoint** (re-based per ADR-0015) — the pack's resolved
   write forecast (`--write`, or its include-set default) covers the
   checkpoint's path, by the same containment semantics as the
   own-forecast drift gate (directory entries cover subtrees, `.`
   covers everything; a read-only pack's empty forecast covers
   nothing
   and passes vacuously); and **the read includes would ship the
   checkpoint** (the ADR-0015 read-side half, board-13 E3, §11 row
   31) — the resolved include set covers the checkpoint's path, so
   its bytes would ship in `context/` to the very worker the oracle
   grades. The covering refusal is the board-6
   blindness contract's pack-time layer: the checkpoint is the
   planner's oracle, authored blind, and keeping it out of the
   forecast
   here is what lets the §8.1 step-14 drift gate do the rest at
   apply time; the read-side refusal closes the other face of the
   self-oracle shape, which separation newly exposes — under the
   conflated model shown-and-forecast were one set, so a shipped
   oracle was always also a refused forecast; once reads stop
   gating, the graded entity could otherwise be handed its oracle
   with every forecast-keyed gate passing clean. (A default pack —
   neither `--write` nor `--include` — covered the checkpoint under
   the conflated model too, so unflagged packs refuse exactly as
   before; the read side newly bites only the pack whose forecast
   excludes the oracle while its includes cover it.) The refusal
   names its successors: narrow the offending declaration (`--write`
   for the forecast half, `--include` for the read half);
   update the checkpoint directly (planner action — edit,
   commit, no session needed, the sanctioned ordinary path); or,
   planner authority, `--allow-checkpoint-in-scope` (per-invocation,
   flag-only — no config key, per the ratified override contract),
   which admits whichever half fired — one flag, one delegation
   decision — logs a FORCE: line, and stamps
   `checkpoint_scope_admitted: true` into the manifest's provenance
   (§7.2) so the session's telemetry carries the admission via the
   response's provenance echo. bale.toml itself is deliberately not
   added to the refusal at v1 — it is legitimately session-editable,
   in-flight retargeting is inert (apply reads the merged config
   from the repo working tree, never the staged overlay), and a
   merged bale.toml edit is a one-line, review-visible diff; the
   accepted residue's re-trigger is the first observed worker edit
   to `[validation]` keys in a merged session.
5. Forecast-disjointness gate (ADR-0015, re-basing ADR-0007's
   pack-time gate), read from the session
   registry (ADR-0006). With no session open, proceed — unchanged
   behavior. With open sessions, admit the pack exactly when its
   resolved **write forecast** — normalized `--write` paths; the
   resolved include set when `--write` is absent (`.`, the whole
   tree, for a default pack); `[]` under `--read-only` — is disjoint
   from every open session's recorded forecast
   (`sessions/<sid>/scope.json`).
   Intersection is over paths, with directory entries covering their
   subtrees and `.` covering everything; a session without a recorded
   scope reads as whole-tree (conservative), and a session packed
   before the separation reads its recorded include set as its
   forecast — an over-forecast, the same conservative direction,
   self-clearing at close. On intersection, refuse
   with a message naming the colliding session(s) and entries and the
   remedies: a narrower `--write` forecast, apply the open session's
   response,
   `bale unlock` an abandoned one, or — when this pack splits and
   supersedes the colliding session — re-run with `--supersedes <sid>`
   (§7.2, v0.3.17), whose accepted exchange closes that parent as
   superseded-by-split *before* this gate evaluates, clearing exactly
   that one collision; the pack still gates against every other open
   session. Read includes participate in nothing here (ADR-0015):
   broad *reading* and concurrency stop being mutually exclusive;
   broad *forecasting* and concurrency remain so. A pack that never
   types `--write` forecasts its include set, so a default whole-tree
   pack still intersects
   every open session — no behavior change for anyone not using the
   flag. An **empty** recorded forecast (a read-only
   session, `--read-only` or the wizard's read-only answer — §7.2,
   v0.3.15) intersects nothing: the gate admits any pack alongside
   it, and admits it alongside any open session.
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
  Since ADR-0015 the include set is the **read set** and nothing
  more: it selects what ships in `context/` and participates in no
  gate — generous shipping no longer costs locks.
- **write forecast** (ADR-0015) — `--write PATH...`, the `--include`
  grammar exactly (repeatable, multiple paths per flag, directory
  entries cover their subtrees), declaring where this session is
  expected to land changes. This — not the include set — is the
  session's recorded scope: persisted to
  `sessions/<sid>/scope.json`, stamped as the manifest's
  `resolved_scope`, and read by the disjointness (§7.1 step 5),
  sibling-collision (§8.1 step 7), and own-forecast drift (§8.1 step
  14) gates. Entries name existing paths (ADR-0014's rule held on
  this surface: nobody pre-names the response's new files — forecast
  the directory they will land under); at least one path is
  required, since the empty forecast has exactly one spelling
  (`--read-only`), and combining the two flags refuses as
  contradictory at arg-parse, before any prompt. Entries need not be
  a subset of the includes. **Absent `--write`, the forecast is the
  resolved include set** — the load-bearing compatibility default: a
  pack that never types the flag behaves byte-for-byte as before the
  separation, so separation is opt-in per pack. The forecast is a
  forecast, not a wall: out-of-forecast work ships enumerated and is
  admitted per path at apply (§8.1 step 14), and the ledger grades
  the drift.
- **excludes** (list of patterns) — appended to the always-excluded
  set for this session only.
- **readme prose** (optional) — the request's `README.md` body.
  Suppliable non-interactively via `--readme-file <path>`, or
  interactively via the wizard's `$EDITOR` step (§7.3); `--edit`
  forces the editor step on a fully specified command. A relative
  `--readme-file` path resolves through the configured inbound
  directories exactly like apply's tarball argument (§7.3).
- **provenance identity** (v0.3.8) — two stamps for the manifest's
  `provenance` block, alongside the ones bale computes itself
  (`bale_version`; the sha256 of each injected global doc, hashed
  from the install at pack time so a contract-doc edit between two
  packs is visible in the longitudinal record; and, since v0.3.28 —
  board 6 session C, the contract_docs precedent extended — the
  **checkpoint stamp**: `provenance.checkpoint` carries `{path,
  sha256}` of the configured `[validation] base` script's committed
  bytes at the pack-time tip, or explicit null when no checkpoint is
  configured, so absence of the KEY remains the pre-v0.3.28 /
  hand-rolled-request signal; apply verifies the base-tree bytes
  about to run against this stamp, §8.5 — plus
  `provenance.checkpoint_scope_admitted`, the boolean record of a
  covering-scope admission past the blindness gate on either
  request-building path (pack: §7.1 step 4b; handoff: §11 row 30,
  v0.3.33), false on every unadmitted pack and handoff):
  - `--packer <name>` names who authored this pack. Precedence:
    the flag > `[identity].packer` in `<repo>/bale.toml` > the global
    `bale.toml`'s `[identity].packer` (either set via `bale config
    init`) > the literal `"unconfigured"`, stamped rather than
    omitted so the block's shape stays uniform, with a logged hint
    pointing at the config.
  - `--work-class {code|doc|contract-doc|meta|mixed}` is the coarse
    class of the session's intended work, defaulting to `mixed`
    rather than being required. The enum is a seed set — extending it
    is a schema edit, not a code change. On the wizard path the
    session-shape question (§7.3, v0.3.15) asks for it when the flag
    is absent; a read-only session that never names one stamps `meta`
    (inferred and logged — a session that lands nothing is doing
    orchestration, discussion, or audit work).
- **allow-checkpoint-in-scope** (v0.3.28, board 6 session C) —
  `--allow-checkpoint-in-scope`, a bare boolean admitting a resolved
  include set that covers the configured blind checkpoint's path past
  the §7.1 step-4b blindness refusal. The override exists for the
  deliberate exception — a checkpoint-maintenance session the planner
  chooses to delegate — and its contract is the ratified override
  shape: per-invocation, flag-only, no config key (a standing opt-out
  is the rejected self-oracle-adjacent silent bypass). Every use logs
  a FORCE: line and stamps `checkpoint_scope_admitted: true` into the
  manifest's provenance, which the response's provenance echo carries
  into telemetry — loud and recorded, the same species as
  `--allow-out-of-scope`. `bale handoff` mirrors the flag against its
  reading-plan scope since v0.3.33 (§11 row 30) — same gate
  implementation, same per-invocation contract, same stamp.
- **read-only** (v0.3.15) — `--read-only`, a bare boolean, opens the
  session with an **empty recorded scope**: the read-only session
  shape for discussion, orchestration, or audit. The session opens
  normally in the registry (sid, `origin_branch` stamp, status row,
  unlock — everything §7.6 does), but its scope locks nothing (the
  ADR-0007 gates admit sibling packs and applies alongside it, §7.1
  step 5) and may land nothing (the own-scope drift gate refuses
  every `changes[]` path a response under this sid ships, §8.1 step
  14). `--include` still selects what ships in `context/` — a
  read-only session reads files; it just cannot land changes to
  them. On the wizard path the same shape is reachable as the
  session-shape question's read-only answer (§7.3). Two lifecycle
  behaviors ride the shape (v0.3.21, board 33):
  - **The read-only sweep.** A read-only pack — and only a read-only
    pack — that finds an open session with recorded scope `[]`
    offers to close it: `closure_reason` `closed-read-only`,
    `command` `"pack"`, through the shared close-with-record
    sequencing (`close_session_with_record` — the same machinery
    unlock and the supersession close use; both values were already
    in the telemetry schema's enums). The sweep runs once the
    session shape is final on every path (post-wizard, since the
    session-shape answer can turn the pack read-only), pre-sid like
    the supersession exchange, with the outcome journaled into the
    new session's log. The prompt is the §5.2 wizard idiom with an
    **accept default** — deliberately inverting `--supersedes`'
    decline default, because a read-only session structurally cannot
    lose work (its empty scope means the drift gate refuses
    everything a response under it could ship, so nothing appliable
    is abandoned). **Piped stdin declines without a prompt** —
    automation never silently closes a session, the same posture as
    the supersession exchange, with only the interactive default
    flipped. A swept session whose `bale/<sid>` branch exists
    (paths were admitted past the drift gate and apply reached
    HOLD) is skipped with a logged `bale revert` remedy rather than
    stranding the branch. Worker (scoped) packs and apply never
    trigger the sweep, and `bale unlock` remains the no-successor
    escape hatch.
  - **The open banner names its own close-out** — per the
    every-command-names-its-successor contract, the read-only pack's
    opening log line and its end-of-run trailer both name the two
    exits: the next read-only pack's sweep, or `bale unlock <sid>`
    now.
- **supersedes** (v0.3.17, board 26) — `--supersedes <sid>` declares
  this pack a **split supersession** of the named session: the split's
  parent closes and this pack becomes one of its narrower children,
  with the lineage stamped as `depends_on.superseded_session` in the
  child's manifest (child → parent, one-directional — the child's sid
  does not exist when the parent closes, so the parent's closure
  record carries no successor pointer). Resolution and flow, in
  pipeline order, all of it *before* the §7.1 step-5 gate evaluates on
  either path (pre-flight on the fully specified path; still ahead of
  the deferred post-wizard gate on the wizard path):
  - The sid resolves against the registry. **Open** → the exchange
    below (after a refusal if the session reached HOLD — its
    `bale/<sid>` branch exists, and `bale revert` is the command that
    knows how to discard that state). **Not open** with a latest
    telemetry closure of `superseded-by-split` → proceed with a
    logged note and stamp the lineage anyway: the **idempotent
    re-run** of a supersession pack that aborted after the close (a
    cap refusal, an editor abort, a gate refusal against a second
    open session) must be re-runnable without manual repair.
    Anything else → refuse: nothing open to supersede, and the sid's
    history doesn't say a supersession already closed it.
  - **The exchange** is the §5.2 wizard idiom: on a TTY, a y/N prompt
    with a **decline default**, naming the cost (close `<sid>` as
    superseded-by-split; its registry entry and session state are
    removed). Piped stdin takes the decline default without a prompt
    — pack has no `--no-interact`; the piped path *is* the
    non-interactive form, the same posture as the no-readme guard —
    so a non-interactive supersession never closes anything.
  - **On accept**, the parent closes through the shared
    close-with-record sequencing (`close_session_with_record`, the
    one implementation `bale unlock` also uses): closure record with
    outcome `unlocked`, `closure_reason` `superseded-by-split`, and
    `command` `"pack"` — the record honestly names the command that
    produced the event. Telemetry stays best-effort, never fatal to
    the pack. The close preceding the §7.4 caps means an abort after
    acceptance leaves the parent closed; that window is accepted (the
    parent was being abandoned by declared intent) and the idempotent
    re-run above is its repair path.
  - **On decline**, nothing closes and the pack refuses: via the
    step-5 gate when the still-open parent's scope collides (the
    refusal names the declined supersession and the remedies —
    re-run accepting the prompt, or `bale unlock <sid>`), via an
    explicit refusal when the scopes happen to be disjoint (a
    `--supersedes` pack that closes nothing and stamps no lineage
    would not be the pack asked for), and immediately at the decline
    on the wizard path, before any prompt collects throwaway answers.
  - **The gate still runs.** Supersession clears exactly one
    collision; the pack is evaluated against every other open session
    as usual.

  By contract (TARBALL.md §3.4) the flag is
  **worker-authored only**: it appears in worker-emitted rescope
  commands that the architect pastes. Nothing enforces this in code —
  the doc carries the policy. The flag is never overloaded for
  master-continuation or general related-to linkage; if the ledger
  later wants that lineage, it is a different `depends_on` field.

The flag-to-manifest mapping lives in `TARBALL.md` §3.4 — cited
both by the architect authoring a pack by hand and by Claude when
emitting a `CLAUDE.md` §11.2 rescope offer.

Bale also fills `manifest.project` automatically as
`basename $(git rev-parse --show-toplevel)`.

### 7.3 Wizard flow when args missing

If `bale pack` is invoked without CLI args (or with only a subset),
the wizard prompts:

```
Goal (one sentence)? > implement the foo widget per ADR-0007
Short slug (kebab-case)? > foo-widget
Will this session land changes, and of what kind?
  [c] code   [d] doc   [t] contract-doc   [m] meta   [x] mixed (default)
  [r] read-only — nothing lands (discussion, orchestration, audit)
> c
Where will changes land? [Enter = same as the includes]
  (space-separated paths; a write forecast, not a wall — out-of-forecast work
  surfaces at apply for per-path admission. Directory entries cover subtrees.)
> src/widgets
Anything to exclude from the default-include-everything? > data/
Any constraints? (one per line, blank to finish)
> no breaking changes to the public API
>
Any out-of-scope concerns? (one per line, blank to finish)
> backend
>
Add a README with prose context? [y/N] >
```

**The session-shape question** (v0.3.15) resolves two facts in one
exchange: whether the session lands changes at all, and — when it
does — its `--work-class` for the provenance stamp (§7.2). Bare
Enter takes `mixed`, exactly the pre-v0.3.15 stamp, so the cost of
not caring is one keystroke; the delta is that a bare cold-start
pack no longer resolves to whole-tree scope by *silent omission* —
the whole-tree default is now an answered default. The `[r]` answer
opens the session read-only (empty recorded scope — §7.2, §7.6);
its work class, absent an explicit `--work-class`, is inferred as
`meta` and logged. Per-field skip applies as everywhere in the
wizard: `--read-only` on the CLI skips the exchange entirely,
`--work-class` alone reduces it to the binary
lands-changes-or-read-only half, and a typed `--write` (a non-empty
forecast IS the lands-changes declaration) reduces it to the
work-class half.

**The where-will-changes-land follow-up** (ADR-0015) rides the
exchange's lands-changes branch — the cold-start pack is the one
command with no Claude author, so this prompt is where the
separation meets a user who has never heard of it. It accepts a
space-separated path list; each entry must name an existing path
(the ADR-0014 rule, re-prompted interactively on a miss); and bare
Enter takes the forecast-defaults-to-includes resolution — the
cold-start user presses Enter and gets exactly the pre-separation
pack. The prompt names its own semantics in one line (a forecast,
not a wall — out-of-forecast work surfaces at apply for per-path
admission). Skipped when the shape resolved read-only or `--write`
already answered it. Because the shape answer can empty the
pack's forecast and the follow-up can narrow it, the §7.1 step 5
disjointness gate defers to just
after the wizard on this path (only when neither `--read-only`, nor
`--write`, nor
a fully specified command already fixed the forecast) — otherwise a
whole-tree provisional forecast would refuse a pack the user was
about
to declare read-only or forecast narrowly, before the question
could be asked. On every
fully specified path the gate fires in pre-flight, before any
prompt, exactly as before.

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
  relative path resolves through the same inbound search paths as
  apply's tarball argument (`apply.search_paths`, v0.3.6): absolute
  paths bypass search, cwd is tried first, then each configured
  directory in order, first existing file wins, and a name that
  matches nowhere fails naming every directory consulted — so a
  worker can author `--readme-file request-brief.md` without knowing
  where the architect's downloads land. With no search paths
  configured, resolution is against cwd, as before. A missing,
  unreadable, or empty file fails loudly before any prompt
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

A third flag (v0.3.8) closes the loop on the no-prose case:

- **`--no-readme`** declares the pack deliberately ships no README
  prose. It skips the wizard's README y/N prompt (the flag is the
  answer) and conflicts with `--readme-file` and `--edit` — asking
  for prose and declaring its absence in one command is a
  contradiction, refused up front.

**The no-readme guard.** A pack that resolves no prose is either
deliberate or an oversight, and the two must not look the same.
`--no-readme` is the deliberate spelling; a wizard-path user who
answered `n` at the README prompt (or saved an empty buffer) made
the choice interactively and is exempt. What remains is the un-asked
case, and the guard splits on the courier:

- **On a TTY: warn.** The user is watching and can Ctrl-C and
  repack; a stderr warning is a real check when someone reads it.
- **Piped: refuse.** Nobody reads a stderr warning in automation —
  the same posture as §7.4's piped soft-breach refusal. The caller
  supplies prose via `--readme-file` or passes `--no-readme` to
  declare the omission deliberate.

The wizard exemption is scoped to paths where a prompt actually ran:
the wizard with `--no-edit` suppresses the README prompt, so that
combination is *not* exempt — it hits the guard like any other
un-asked pack.

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
   `DOCS.md`, `CODE.md`) from bale's installation `docs/` directory,
   **and the worker-side tools** under `tools/` — each member of
   `bin/bale`'s `INJECTED_TOOLS` tuple (the one source for the list:
   the lint and, since v0.3.19, the crafter), copied from the
   install's `tools/` with mode preserved so each arrives executable.
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
   manifest, for `bale apply` to verify the response against),
   `.bale/sessions/<sid>/scope.json` (the resolved **write forecast**,
   ADR-0015 — the `--write` set, its include-set default, or `[]` for
   a read-only session, v0.3.15 — which the gates read; step 5 of
   §7.1 and
   step 7 of §8.1. The record is reinterpreted, not reshaped: same
   file, same JSON form, same helpers, and an open session recorded
   pre-separation reads its include set back as an over-forecast —
   conservative, self-clearing. A
   recorded **empty** forecast is a distinct third state that reads
   back
   as exactly that — locks nothing, may land nothing — never falling
   through to the conservative whole-tree read reserved for a
   *missing or malformed* scope.json; since v0.3.21 the same value is
   also stamped into the request manifest as `resolved_scope`, board
   33 — one source, so the registry record and the worker-visible
   stamp cannot disagree), and `.bale/sessions/<sid>/origin_branch` (the
   branch checked out at pack time — the session's integration
   target, ADR-0008). The stamp is required: apply hard-refuses a
   session with a missing or empty stamp (§8.1 step 5), and the
   pre-flights of both request-building paths — pack, and handoff
   (§11 row 24) — refuse a detached HEAD (§7.1 step 4a) before any
   of this runs, so every session reaching this step has a real
   branch to stamp. The target is fixed at pack because the pack's content
   was gathered from that branch and integration no longer consumes
   the checkout — the user may be on any branch, clean or dirty, when
   the response is applied (§8.1 step 5).
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

**The tree-position echo** (v0.3.31, board-6 upward report — operator
state legibility at the pack surface). Pack names where the tree is
at the moment of paste, on two surfaces:

- **A pre-flight banner line** — `tree position: branch <branch>;
  latest applied <sid>` (or `none yet`) — emitted immediately after
  the §7.1 step-4a detached-HEAD refusal: after every earlier
  pre-flight refusal, so reject-early is intact (a doomed command
  still fails before any echo or prompt), and before the §7.2
  supersession exchange and the §7.3 wizard, so a re-pasted stale
  command becomes visible before the operator invests any answers.
- **The end-of-run report** — the same two facts as summary rows
  (`branch`, `latest applied`) and, under `--json`, as the additive
  keys `branch` and `applied_latest`. The json key contract's one
  home is `format_pack_json`'s docstring in `bale_report.py`
  (DOCS.md's one-home rule), as for every other pack-report key.

The latest-applied fact is the same one the status applied row
renders, read from the same source (`applied_tags` in `bin/bale`;
most recent `applied/<sid>` tag by creation date). The echo is
legibility, not enforcement: pack cannot know a goal is stale; the
operator can, once the fact is in front of them. `bale status`
remains the ground-truth consultation surface (its applied row also
carries the count and the `bale rollback --list` pointer, which the
echo deliberately does not duplicate).

---

## 8. Apply pipeline

`bale apply <response-tarball>` is the workhorse. It validates,
stages, runs the response's `apply.sh` and `validation.sh`, commits
or holds, and walks the user through the result.

The pipeline below describes a normal response. Bailout and
clarification responses branch off after pre-flight and are never
staged, validated, or committed — their apply-time contract is
§8.10.

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
5. The narrow dirty-on-target rule (ADR-0008; replaces the blanket
   clean-tree requirement). Resolve the session's integration target
   (the pack-time `origin_branch` stamp, §7.6 — required; refuse a
   missing or empty stamp, with the remedy: `bale unlock` and re-pack
   against the intended target, and refuse a stamp naming a branch
   that no longer exists, with the remedies: recreate the branch, or
   `bale unlock` and re-pack against the intended target). Then refuse only the one genuinely entangled
   case: the checkout is on the target branch AND has **tracked**
   changes (staged or unstaged; untracked files never block) — moving
   the branch ref under a dirty checkout of that same branch would
   desynchronize the user's tree from its own branch. The refusal
   names the dirty paths and the remedies: stash, commit, or switch
   branches. Every other state proceeds: on-target and tracked-clean
   (the checkout is fast-forwarded to the new ref at merge, §8.8), or
   on any other branch or detached, dirty or not — integration never
   touches the checkout. This check is here — adjacent to the
   registry check, before any tarball-specific work — because it
   concerns the user's state, not the tarball, and it's the cheapest
   failure to resolve. `bale retry` runs the same rule (a HOLD no
   longer dirties the worktree, §8.6).
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
   session's own scope that no sibling claims — is this check's
   sibling gate, step 14 below (v0.3.10; policy-only before that).
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
    the tarball. `README.md` and `notes.md` are optional per
    `TARBALL.md` 5.1, and a legacy `next-prompt.md` is tolerated
    (§6.2); none of the three is required to exist.
13. Verify no `changes[]` path names a generated artifact: no
    `__pycache__`, `node_modules`, `dist`, or `build` directory
    component, and no `*.pyc` / `*.pyo` basename. Response tarballs
    ship source, never generated artifacts (`TARBALL.md` §5.1 carries
    the builder-side rule); the deny list is deliberately a short,
    obvious set rather than a heuristic, because the failure costs are
    asymmetric — a false refusal costs the worker a repack, a false
    pass costs nothing new (review still exists). The rejection names
    the offending paths. `.bale/` paths are an obvious offender too
    but are already rejected by step 10's path safety (§11 row 14)
    and are not duplicated here. Manifest-only, so it runs under
    `--dry-run` (the plan report predicts the rejection) and passes
    vacuously for bailout and clarification manifests, whose
    `changes[]` is empty.
14. Own-scope drift gate (v0.3.10 — the drift-to-contract conversion
    of the stay-in-the-lane rule; runs adjacent to step 7, its
    cross-session sibling, and listed here to keep steps 1–13 stable).
    Every `changes[]` path must lie inside **this** session's own
    declared scope — the pack-time resolved include set recorded in the
    registry (`sessions/<sid>/scope.json`; same path semantics as
    step 7: directory entries cover subtrees, `.` covers everything, a
    missing or unreadable scope reads as whole-tree, which also keeps
    default whole-tree packs entirely clear of this gate; a recorded
    **empty** scope — a read-only session, §7.2/v0.3.15 — covers
    nothing, so this gate refuses every `changes[]` path such a
    session ships, and the refusal names the session as read-only:
    masters-never-self-land is mechanical contract here, not policy
    prose). Created
    paths are rejected the same as modified paths — the audit's clobber
    scenario is precisely two sessions creating or overlaying the same
    unclaimed file, and each ADR-0007 gate checks declared scope
    against declared scope, so unclaimed drift sails past both. The
    refusal names every offending path and the sid's declared scope;
    like every other refusal it is pre-staging — no git side effects —
    and the session stays open, so the response can be regenerated or
    the apply re-run. `--allow-out-of-scope <path>` (repeatable,
    per-invocation only — deliberately no config key) admits exactly
    the named paths past the gate while any *other* drift still
    refuses; every use is logged prominently (a FORCE: session-log
    line) and the admitted paths are stamped into the session's
    telemetry record (§8.9). In `--json` mode the refusal is the
    one-line report with outcome `scope-drift-refused` and a `drift`
    detail object — emitted on the exit-1 path like held/reverted, so
    an orchestrating operator dispatches on the key instead of parsing
    prose. Manifest-only, so it runs under `--dry-run` (same report and
    exit; no telemetry record, since no outcome occurred) and passes
    vacuously for bailout and clarification manifests. `bale retry`
    takes the same override flag (v0.3.14) and runs the same gate: the
    override is per-invocation and per-path on retry exactly as on
    apply, never carried forward from the failed attempt — a retry
    that needs it re-states it, and a retry that omits it refuses
    here. The refusal is pre-staging either way, so the session stays
    open and recoverable.
15. Required-check superset gate (board 6 session B — the
    drift-to-contract conversion's declaration-side sibling; appended
    as step 15 so steps 1–14 stay stable, and sited beside step 14 in
    the pipeline). When the project's `[validation] required` set
    (bale.toml, project layer only — the same `[validation]` section
    as §8.5's checkpoint key, wizard-walked by `bale config init`)
    resolves non-empty AND the manifest's `changes[]` is non-empty:
    every required name must appear **verbatim** in the manifest's
    `validation_will_run` (exact string match — the TARBALL.md §5.3
    canonical-identifier rule's unit). The declaration is what claims
    hang off (row 15: `claims ⊆ validation_will_run`), so an
    under-declared set starves the calibration stream on exactly the
    checks that matter; this gate converts a floor of that declaration
    to contract — partially, since name membership cannot verify a
    check's content, which stays review policy. A declared check may
    still `[SKIP]` with a reason at runtime (TARBALL.md §7.2), grading
    `n/a` (TARBALL.md §7.3) — honest and visible rather than forced
    work. The refusal renders BOTH sets (required and declared) so a
    near-miss is visible, keeps the session open pre-staging with no
    git side effects, records telemetry outcome `required-check-refused`
    (`validation: null` — nothing ran), and in `--json` mode is the
    one-line report with that outcome and a `required_checks` detail
    object. `--allow-missing-required-check <name>` (repeatable,
    per-invocation only, per-**name** — the gate's own unit;
    deliberately no config key, per the ratified override contract: a
    standing config opt-out is the rejected self-oracle-adjacent
    silent bypass) admits exactly the named names past the gate while
    any other missing name still refuses; every effective use logs a
    FORCE: session-log line and the admitted names are stamped into
    the attempt's `required_check_overrides` (§8.9). A named-but-not-
    missing name logs a no-effect line, mirroring step 14's unused
    override handling. Manifest-and-config-only, so it runs under
    `--dry-run` (same report and exit; no telemetry record, since no
    outcome occurred) and passes vacuously for bailout and
    clarification manifests, whose `changes[]` is empty; read-only
    sessions never reach it — step 14 refuses their changes first —
    and unconfigured projects are entirely outside its blast radius.
    `bale retry` takes the same flag and runs the same gate: the
    override is re-stated per invocation exactly as step 14's is,
    never carried from the failed attempt.

If any of 1–15 fails: log the failure with a clear `[REJECT] <rule>:
<detail>` line, clean up the temp directory, exit non-zero. No
staging branch, no file modifications. (The step-14 and step-15
refusals additionally report through their structured surfaces above;
their telemetry attempts record outcomes `scope-drift-refused` and
`required-check-refused` respectively rather than `rejected`.)

### 8.2 Stamp session

1. Resolve the integration target (ADR-0008): the session's pack-time
   `origin_branch` stamp (§7.6), required — a missing or empty stamp
   was already refused at §8.1 step 5. Record it as
   `.bale/sessions/<sid>/origin_branch`. This is the branch the apply
   wizard will merge into (on PASS); `bale revert` reads it too.
2. Record the **target branch's tip** as `git_head_at_apply` in
   `.bale/sessions/<sid>/`. This is the base the session branch, the
   session commit, and the merge are all built against; it equals the
   checkout's `HEAD` only when the user happens to be on the target.
   When the checkout has diverged from the target, apply logs a note
   that validation (which runs in the staging copy, built per §8.3's
   strategy) exercised the checkout's content.
3. Persist the response manifest at
   `.bale/sessions/<sid>/response-manifest.json`.

### 8.3 Stage

1. Resolve the staging directory. The default is per-session:
   `<repo>/.bale/staging/<sid>/`, where `<sid>` is the open session
   the response answers (the `responds_to` resolution of §8.1). Stale
   cleanup is per-session too: under the staging root
   (`.bale/staging/`), the sid's own directory is removed if present
   (rebuilding it is correct on a retry of an errored stage and on a
   HOLD the user is moving past — re-invoking apply is the signal),
   and any entry no *open* session owns is removed with a log line
   (closed sessions' preserved-for-inspection leftovers, and a bare
   pre-per-session tree at the root itself, which no session under
   this layout can own). A sibling open session's staging directory
   is never touched — with the shared pre-per-session default, a
   second session's apply would have removed the first session's
   live HOLD staging as "stale".
   `--staging-dir <path>` overrides: the path is used verbatim (no
   `<sid>` suffix), resolves relative to cwd, and if it exists the
   apply fails loudly — bale never removes a user-specified
   directory. Two open sessions both overriding to the same
   directory is therefore the user's collision to own.
2. Build the staging base per the project's staging strategy —
   `bale.toml`'s `[staging] strategy`, resolved from the merged config
   at stage time by both `bale apply` and `bale retry` (so a retry
   re-stages under the same strategy and exercises identical content):
   - **`working-tree`** (default): `cp -r <project>/. staging/` (full
     project state minus `.bale/`) — byte-identical to the historical
     behavior, and the documented fallback and ground truth.
   - **`target-base`** (opt-in): materialize the **target branch tip's
     tree** (`git archive` of the §8.2 base, streamed through stdlib
     tarfile) into staging; copy `.git` alongside it, so git
     invocations from `validation.sh` resolve inside staging rather
     than discovering upward into the real repo; then overlay each
     entry of `[staging] untracked_inputs` from the working tree —
     the declared untracked build and dependency state validation
     needs (a pure git-archive tree carries none, so the declaration
     mechanism is load-bearing, not polish). Each declared input must
     be a safe repo-relative path (no globs; no `..`, `.git/`, or
     `.bale/`), present in the working tree, and untracked at the
     target tip — any violation fails the stage loudly, per the
     silent-skip rule; nothing is skipped. A pre-overlay snapshot of
     this materialized base is recorded as the §8.4 reconciliation
     baseline, since the manifest's changes are authored against the
     target tip and diffing against a diverged working tree would
     misreport the divergence as undeclared changes.
3. `cp -r response-NNN/files/. staging/` (overlay the changes).
4. Run `bash apply.sh` with `cwd=staging/`. This handles deletes and
   any non-cp operations. If `apply.sh` exits non-zero, bale captures
   the exit code and output to the session log, wipes staging, and
   rejects the tarball — no git side effects, no reconciliation
   attempted.

**Validation-fidelity rationale (why the default stays
`working-tree`).** The default stages the **working tree** while the
session commit and the merge are built against the **target branch's
tip** (§8.2, §8.6). The two coincide only when the checkout sits at
the target tip; when it has diverged, `validation.sh` exercises the
checkout's content while the commit lands the manifest's entries on
the target base, and apply logs a note saying so (§8.2 step 2) rather
than letting the mismatch pass silently. Copying the working tree is
a deliberate default — untracked build and dependency state has to
ride into staging for validation to run at all, and the working-tree
copy carries it without any declaration. The `target-base` strategy
closes the fidelity gap for projects that opt in: validation then
exercises exactly the content the commit lands, with untracked state
riding via the explicit `untracked_inputs` declaration, and the
divergence note reports that fidelity instead of the caveat.

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
the target branch's tip (§8.2) and is never checked out — under
ADR-0008 the commit and merge are built with plumbing, so the user's
working tree is untouched regardless of outcome.

**Blind checkpoint (board 6).** A project may pin a planner-authored
**blind checkpoint** script via `bale.toml`'s `[validation] base` — a
single repo-relative path key, wizard-walked by `bale config init` at
the **project layer only** (the global wizard does not walk it, and
the merge never inherits it from the global file; ratified
disposition 1 — a global key would let the same value silently name a
different oracle in every repo it touches). Absent key = no blind
checkpoint: today's worker-validation-only behavior, byte-identical.
Configured but absent at the base tree = loud refusal before staging
(committed-is-ratified: a working-tree-only checkpoint the planner
has not committed is not yet the project's oracle; the remedy is to
commit it at the named path or clear the key via `bale config init`).
`bale apply --dry-run` predicts the dangling refusal too (board 6
session B, the sanctioned session-A rider): when a checkpoint is
configured, the dry-run resolves the session's target base
read-only — rev-parse and cat-file only, no session-dir stamps — and
refuses with the same message a real apply would; unconfigured
projects' dry-run behavior is unchanged.

**Provenance stamp verification** (v0.3.28, board 6 session C; §11
row 28). Pack stamped the oracle's identity into the request
manifest — `provenance.checkpoint = {path, sha256}` of the committed
tip bytes, or explicit null when none was configured (§7.2) — and
apply reads it back from the registry's persisted copy
(`.bale/sessions/<sid>/manifest.json`, the one the operator's own
pack wrote, so a doctored response tarball cannot carry a forged
stamp past it). Before execution, beside the dangling check and
equally pre-staging: hash the base-tree bytes about to run and
compare to the stamp. Divergence — a hash mismatch, a retargeted
path, or a null stamp where a checkpoint is configured now — means
the oracle changed between pack and apply; a legitimate planner edit
and interference look identical from here, and either is worth
stopping for. The refusal names its successors: re-pack against the
current tip, or `--accept-checkpoint-change` (per-invocation,
flag-only — the ratified override shape; `bale retry` takes the same
flag and re-states it per invocation, never carrying it from a
failed attempt), which executes the **current** base-tree version —
the planner's latest committed oracle, never the stale stamped
bytes — logs a FORCE: line, and records `stamp_matched: false` in
the attempt's §8.9 telemetry stamp. A verified match records
`stamp_matched: true`; a request carrying no `provenance.checkpoint`
key at all (hand-rolled, or packed pre-v0.3.28) verifies nothing —
logged, never silent — and records `stamp_matched: null`, keeping
older requests on today's behavior. The dry-run rider above predicts
this refusal too, with the same message plus a prediction trailer.
One residue is logged rather than refused — the accepted config-edit
residue of the blindness design (re-trigger: the first observed
worker edit to `[validation]` keys in a merged session): an oracle
removed between pack and apply (an object stamp beside a
now-unconfigured project) has no about-to-run bytes to verify, so
the attempt validates with the worker's script only, with a loud
note naming the removal.

When configured, **both scripts always run, separately invoked and
separately captured; checkpoint first.** The executed checkpoint
bytes come from the **base tree** — `git show <git_head_at_apply>:
<path>`, materialized to a temporary location outside staging and run
with `cwd=staging/` — never the staged overlay, whose copy is the
worker's post-overlay version whenever the response touched it. A
response that modifies the checkpoint is therefore checked against
the old one: in-flight self-grading is structurally impossible, not
policy-refused. `git show` emits blob bytes only, so the runner
restores the exec bit explicitly from the tree entry's mode AND
invokes via the interpreter — silent non-execution is outside the
contract. A checkpoint failure does not skip the worker's run and a
worker failure does not skip the checkpoint: a checkpoint FAIL
beside a worker PASS is precisely the misunderstanding-with-
calibrated-worker signal the dual stream exists to surface.

1. Create the bale branch: `git branch bale/<sid>
   <git_head_at_apply>`.
2. When a blind checkpoint is configured: materialize and run it
   from base-tree bytes as above; stream its output into the session
   log under a banded header — `=== blind checkpoint (<path>,
   <sha256 prefix>) ===` — closed by a `=== worker validation.sh
   ===` band, so the two invocations' output is attributed. The
   checkpoint does not read the manifest and produces no TARBALL.md
   §7.3 claims block: claims are the worker's predictions, and the
   checkpoint has no claims by construction.
3. Place the response manifest at `staging/.bale-manifest.json` so
   `validation.sh` can read the claims for the reconciliation block.
4. Run `bash validation.sh` with `cwd=staging/`. Capture stdout,
   stderr, exit code, and the claims-vs-verdict reconciliation block
   (the reconciliation parse reads the worker script's captured
   output only — the checkpoint's never interleaves with it).
5. Stream output to `.bale/logs/<sid>.log` and (if `--verbose`) to
   the terminal.

Validation exit codes (per `TARBALL.md` 7.5), **per script** —
each keeps the vocabulary individually:

- `0` — passed.
- `1` — at least one check failed.
- `2` — the script itself errored. Surfaced distinctly in the
  walkthrough: *"validation script itself errored; inspect the
  script"* for the worker's, and *"the planner's checkpoint itself
  errored; inspect the checkpoint script"* for the checkpoint's —
  the remedy differs, because the planner's artifact broke, not the
  worker's.

### 8.6 Commit or hold

The commit step is driven per-manifest-entry from `changes[]` rather
than by a tree-level diff. The manifest is the contract; the commit
shape follows it directly.

The **integration lock** (`.bale/integration.lock`, ADR-0006) is
acquired before the commit build below and held across the §8.6–§8.8
window — the stretch where bale mutates refs (`bale/<sid>`, and on
merge the target branch, plus the clean-on-target checkout
fast-forward). Integrations serialize under it; with one open session
it is uncontended. It releases at each terminal action once the git
work is done. A crash inside the window leaves it held, and the
acquire-time refusal message is the stale-lock story: it names the
recorded holder (sid, pid, acquire time) and the clear surface —
`bale unlock --integration` removes the stale file through the tool
(removing it by hand is equally safe whenever no apply is running). A
mid-window crash never leaves the user's checkout mid-mutation — the
checkout is not consumed by the pipeline (ADR-0008).

Both validation outcomes build the session commit the same way, with
plumbing, never through a checkout:

1. In a temporary index (`GIT_INDEX_FILE`) seeded from the base tree
   (`git read-tree <git_head_at_apply>`), apply each
   `manifest.changes[]` entry with content from the validated staging
   copy:
   - `created` or `modified`: `git hash-object -w` the staging file
     (mode from the staging copy's own bits — `100755` when
     executable, `120000` for a symlink), then
     `git update-index --add --cacheinfo <mode> <blob> <path>`.
   - `deleted`: `git update-index --force-remove <path>` (a no-op
     when the path isn't in the base tree, mirroring the old
     `--ignore-unmatch` tolerance).
2. `git write-tree`, then `git commit-tree <tree> -p
   <git_head_at_apply> -m "[bale <sid>] <summary>"` where `<summary>`
   is `manifest.summary`.
3. Move the branch onto the commit with a compare-and-swap:
   `git update-ref refs/heads/bale/<sid> <commit>
   <git_head_at_apply>`.

If validation exited 0 — **and, when a blind checkpoint ran, its exit
code was also 0 (§8.5: PASS requires both)** — mark the branch as
`[PASS]` for the walkthrough. Otherwise mark as `[HOLD]`, attributed
per source everywhere the outcome renders — the banded session log,
the walkthrough summary (`checkpoint: PASS · worker validation: HOLD
(exit 1)`), the `--json` report's additive `checkpoint` key, and the
telemetry stamp (§8.9). The envelope vocabulary stays PASS/HOLD; the
attribution is additive. A HOLD is a commit on `bale/<sid>` —
inert, since nothing has the branch checked out — and inspection is
identical in UX to PASS inspection: `git diff <origin>..bale/<sid>`,
`git log bale/<sid>`, plus the per-sid staging directory, which is
preserved for open sessions (§8.3).

### 8.7 Walkthrough

Both outcomes print the same summary, built by
`bale_report.format_walkthrough_summary`: **reference material first,
crisp verdict last**, so the eye lands on the verdict and the prompt
instead of scrolling back for them past a long `notes.md`.

The reference block, in order:

- The **claims table** — each `claims` key with Claude's prediction,
  plus a pointer to `.bale/logs/<sid>.log` for the verdicts. The
  per-check `[PASS] / [FAIL] / [SKIP]` lines and the TARBALL.md
  §7.3-style claims-vs-verdict reconciliation live in that log,
  streamed there while `validation.sh` ran (§8.5 step 4); the
  walkthrough surfaces the claims side so review is self-contained.
- A **diffstat** over `origin..bale/<sid>` — the same rev range as
  the inspection command below. PASS and HOLD alike are commits on
  the session branch (§8.6), so one range covers both outcomes.
- **`notes.md`**, inline, if the response shipped one (skipped
  silently otherwise — absence means nothing needed surfacing). A
  legacy `next-prompt.md`, if a pre-retirement response carries one,
  is surfaced with its header labeled deprecated (TARBALL.md §5.5) —
  tolerated for old archives, never blended in silently.
- The **inspection commands**, naming both surfaces of the committed
  session: the branch (`git diff <origin>..bale/<sid>`,
  `git log bale/<sid>`), the session log
  (`cat .bale/logs/<sid>.log`), and the per-sid staging directory
  (`ls .bale/staging/<sid>/`, §8.3 — or the `--staging-dir` override).

Then the verdict block — `[PASS]`/`[HOLD]` headline with the sid, the
origin branch, the branch state (*committed; ready to merge*, or
*committed; held for inspection — checkout untouched*),
`manifest.summary`, and a one-line validation roll-up — and the
prompt:

**If passed (`[PASS]`):**
```
[Enter/m] merge into origin (default)   [r] revert — discard branch
```

**If held (`[HOLD]`):**
```
[Enter/i] inspect — hold for review (default)   [r] revert — discard branch
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

- **Merge** (PASS only). Checkout-free (ADR-0008): build the merge
  commit with `git commit-tree <session-tree> -p <old-target-tip> -p
  <session-commit>` — the exact two-parent, first-parent-is-old-tip
  topology and `"Merge bale <sid>"` message a `git merge --no-ff`
  would produce — then advance the target ref. If the user's checkout
  is on the target branch (tracked-clean by pre-flight), the advance
  goes through the checkout as `git merge --ff-only <merge-commit>`,
  so ref, index, and working tree move together under git's own
  safety checks and the post-apply state matches the old pipeline's
  (logged as a fast-forward). Otherwise `git update-ref
  refs/heads/<origin> <merge-commit> <old-tip>` advances the ref
  without touching the checkout. Both advances are compare-and-swap:
  if the target moved during the apply (or the fast-forward is
  declined), bale refuses, releases the lock, and leaves the session
  commit on `bale/<sid>` with the session open — recoverable with
  `bale retry <tarball>` or `bale revert <sid>`. On success:
  `git tag applied/<sid> <merge-commit>`, close the session in the
  registry (marker removed, pointer cleared — ADR-0006), clean up
  `.bale/sessions/<sid>/`, release the integration lock, delete
  `bale/<sid>` (force-delete — the merge commit and tag anchor the
  history; `-d`'s merged-into-HEAD check is meaningless when HEAD may
  be an unrelated checkout). The `applied/<sid>` tag is the durable
  record. The closing `[PASS]` banner names the tag, the merged
  branch with how it advanced (*checkout fast-forwarded* on-target,
  *checkout on '<branch>' untouched* otherwise — the line that keeps
  a first checkout-free apply from reading as a malfunction: the
  merge landed even though the files in front of the user didn't
  move), the change count, the preserved staging path, and the
  rollback hint: *"To roll back this bale: `bale rollback <sid>`, or
  `bale rollback` for the most recent."*
  When `bale.toml` sets `[apply] archive_dir` (v0.3.30, the landed
  §13 v0.5 candidate; valid at both config layers like the sibling
  `[apply]` keys, repo-relative only), the merge path additionally
  copies whichever of the response's prose artifacts the tarball
  actually included — `README.md`, `notes.md`, plus a legacy
  `next-prompt.md` (§6.2) — into `<archive_dir>/<sid>/` as
  **untracked working-tree files**, after the merge has durably
  landed and before the `post_apply_pass` hook (so a hook that
  consumes the archive sees it on disk). Committing the copies stays
  the operator's job; bale never auto-commits. The per-sid directory
  uses the full sid, so paths are collision-free across same-day
  sessions and include-ready for later packs as-is. Applied outcome
  only: HOLD, revert, bailout, and clarification archive nothing,
  and the key unset preserves the pre-archival behavior
  byte-identically. A copy failure after the merge **logs loudly and
  reports in the closing banner but is never fatal** — it cannot
  un-apply or HOLD the merged session. The banner gains an `archive`
  row only when the key is configured (copied count and destination,
  the copy-FAILED form, or an explicit nothing-to-archive line), and
  the `--json` report gains the additive `archive` key — object on
  this outcome when configured, null otherwise; the key list's one
  home is `format_apply_json`'s docstring (§5.4's owner rule).
- **Inspect** (HOLD only). The session stays open in the registry;
  branch persists with the committed session changes; the user's
  checkout was never switched. The integration
  lock releases — this invocation's git mutation is over, and the
  held state is guarded by the registry entry plus the branch
  itself. The user investigates the failure,
  then chooses: discard via `bale revert <sid>` (branch deleted,
  session closed in the registry; the checkout was never moved, so
  there is nothing to switch back), send a
  corrected response through `bale retry <tarball>` in the same
  session, or send Claude the failure
  context and request a corrected response as a fresh session. That
  fresh-session path is: `bale revert <sid>` first, then `bale pack` a new
  request that includes the failure context, then apply the new
  response. That new response's manifest sets `corrects: <held_sid>`
  as a history pointer — the corrected work itself runs as a fresh
  session against origin, not layered onto the discarded branch.
  The closing `[HOLD]` banner names both inspection surfaces — the
  committed branch with its diff command (`git diff
  <origin>..bale/<sid>` — checkout untouched) and the preserved
  per-sid staging path — plus the session log and the two ways
  forward (`bale retry <new-tarball>`, `bale revert <sid>`).
- **Revert.** Delete the branch (forcefully), wipe
  `.bale/sessions/<sid>/`, close the session in the registry, release
  the integration lock. Same operation regardless
  of whether validation passed or held.

**Auto-sweep commits** (`[apply] sweep`, v0.3.32; valid at both
config layers like the sibling `[apply]` keys, default false). When
enabled, after bale finishes writing files it owns at a
closure-shaped event, it stages **exactly those files** and commits
them — the mechanized form of the manual git dance that previously
landed bale-written bookkeeping. The owned set for a given
invocation: the telemetry record(s) it wrote or updated this
invocation (§8.9), and the archive copies `archive_dir` made this
invocation. The trigger moments are the closure-shaped events:
apply's terminal outcomes (merge, the walkthrough revert, a
bailout), `bale revert`, `bale unlock` (including its crash-debris
record), pack's session closes (the read-only sweep and the
supersession close, §7.2), and rollback's clean success paths
(`rolled-back` / `re-applied`, §9.2). Held states and refusals sweep
nothing — the session continues, and the record rides to its
eventual closure. A sweep commit **never interleaves with the
merge**: every trigger runs after the parent event's git mutation is
durably complete, so the sweep is always its own commit on top, on
the current branch — where the manual sweep would have landed it.
The staging is pathspec-only (`git add -- <paths>`, `git commit
-- <paths>`): never a directory glob, never `git add -A`, and an
operator's unrelated dirty files — staged or not — are untouched by
construction. The commit message is one conventioned shape carrying
the sid and event: `[bale sweep <sid>] <event>`, joining `[bale
<sid>]` (§8.6) and `[bale rollback <sid>]` (§9.2) in the message
family. Loud either way: `sweep: committed <n> file(s) as
<short-sha>` or `sweep: nothing to commit` (an event that wrote
nothing sweeps nothing), plus a `sweep` banner row on the applied
outcome when the key is set. Degenerate git states — an in-progress
merge, a detached HEAD, or a git identity that cannot commit — skip
loudly and leave the files for a manual sweep; a sweep failure after
a successful apply **can never convert the apply into a failure**
(the archive-dir loud-never-fatal precedent; on the apply pipeline
the key is resolved at pre-flight through the strict accessor, so a
malformed value refuses before staging, never post-merge). Unset or
false, every path is byte-identical to today: bale writes the files
untracked and never commits.

### 8.9 Telemetry record at session close

Every apply close writes (or updates) a durable per-session telemetry
record — `claude/telemetry/<sid>.json`, shape in
`schemas/telemetry-record.schema.json` (v0.3.9, session B2). The
record promotes to a durable, aggregable surface the facts that
previously lived only in the transient `.bale/logs/<sid>.log` and the
short-lived `.bale/sessions/<sid>/` directory:

- the response manifest's **feedback block, verbatim** (TARBALL.md
  §5.2.2) — the worker's dual-stream self-account;
- **claim/verdict agreement per check**, parsed from `validation.sh`'s
  TARBALL.md §7.3 reconciliation block in the captured validation
  output (with a `reconciliation_parsed` flag, since the block is an
  authoring convention, not an enforced contract — a parse miss is
  recorded, never silently skipped);
- **validation exit state** (PASS/HOLD and the TARBALL.md §7.5 exit
  code);
- the **blind checkpoint stamp** (board 6): an `attempts[].checkpoint`
  object on every validated attempt post-epoch — key presence is
  epoch membership, `{"configured": false}` is the known-zero form,
  and an executed checkpoint records its per-source state, exit code,
  and the executed base-tree bytes' `{path, sha256}` (§8.5). Blind
  outcomes never merge into `claim_verdict`: the checkpoint has no
  claims by construction;
- **includes shipped vs paths changed** — the session's recorded
  scope (`sessions/<sid>/scope.json`) and every `changes[].path`,
  both raw; aggregation computes the drift;
- the **outcome**.

**Every terminal outcome records.** `applied` (merge), `held`
(inspect), `reverted` (the walkthrough's revert and `bale revert`
alike), `rejected` (any apply/retry that exits through a `fail()`
path — the record is minimal there, since a rejected tarball's
manifest is unvalidated; detail stays in the session log),
`scope-drift-refused` (the own-scope drift gate's refusal at apply
pre-flight, §8.1 step 14 — the session stays open, so a later
attempt supersedes it the way a HOLD's does),
`bailout` (the session is consumed, and the feedback block's
`budget_pressure: "bailed"` is precisely the signal worth keeping),
and — since v0.3.16 — `unlocked` (`bale unlock`, §9.3: the close
with no git side effects, which previously left no durable trace
and made the corpus structurally apply-only). The unlock event
appends to the same one-file-per-sid record as every apply-close
event; command is `unlock`, tarball and validation are null, and
the scope is read before the session-dir wipe destroys it.
A clarification writes nothing: it suspends the session rather than
closing it, and the eventual normal response records. `--dry-run`
writes nothing: no outcome occurred.

**closure_reason: why a session closed.** Unlock and revert events
carry a nullable `closure_reason` (v0.3.16, additive):
`abandoned`, `superseded-by-split`, `reframed-after-clarification`,
`master-closeout`, `crash-debris`, or `closed-read-only`. Unlock
stamps it always — the operator's `--reason` when given; else
`closed-read-only` when the recorded scope is exactly `[]` (the
§7.2 read-only session shape; the inference keys on `[]`, never on
a missing scope, which reads back conservative whole-tree); else
`abandoned`. An explicit `--reason` beats the read-only inference:
the operator knows more than the heuristic — a read-only session
can itself be superseded or abandoned-in-fact. The read-only sweep
stamps `closed-read-only` with command `"pack"` (v0.3.21, board
33): a read-only pack that finds an open `[]`-scope session and
closes it at its accept-default prompt (§7.2) writes the same
value, so `closed-read-only` is both unlock's inferred reason and
a pack-stamped one. Unlock's no-sid
sweep, when it clears a stale compatibility pointer naming a sid,
best-effort appends `crash-debris` to that sid's record (§9.3
step 2). Revert stamps `--reason` when given and null otherwise —
`reverted` already names the event, and a null reason is honest
rather than a guessed one. Apply and retry attempts record null:
they are apply-close events, not closures.

**Update semantics: one file per sid, append per event.** The first
apply-close event creates the record; every later one against the
same sid — a retry after a HOLD, a `bale revert` after either —
appends an entry to `attempts[]` rather than duplicating or
overwriting. The envelope's `outcome` and `updated_at` mirror the
latest attempt; the history is deliberate, because a HOLD attempt's
claim/verdict disagreement is calibration data even after a later
attempt merges. An existing record that no longer parses is moved
aside to `<sid>.json.corrupt-<stamp>` (logged) and a fresh record
starts — corruption must neither block the apply that found it nor
be overwritten unexamined. `record_version` (currently 1) is the
evolution hook: additive fields don't bump it; shape breaks do.

**Why `claude/telemetry/`, not `.bale/`.** `.bale/` is gitignored by
construction (§7.1 step 6) and transient by convention — a record
there dies with a clone or a fresh checkout and can never use git
history as its substrate. The record's whole purpose is longitudinal
aggregation across sessions (board 5 reads it), so it lives on the
tracked side, riding the repo the way the project's own docs do. The
cost is one small JSON file of diff noise per session; the benefit is
that `git log claude/telemetry/` *is* the aggregation timeline.

**The record is written to the working tree, not the merge commit.**
The session commit is built per-manifest-entry from `changes[]`
(§8.6); injecting a bale-generated file would desync the manifest
from the commit and break the §8.4 reconciliation contract. So the
record lands untracked at apply close, and the user commits it with
their next ordinary commit — or, when `[apply] sweep` is enabled
(§8.8), bale commits it immediately as its own `[bale sweep <sid>]
<event>` commit on top, which keeps the manifest/commit contract
intact: the sweep is a separate commit, never an injection into the
session or merge commit. Telemetry can never break an apply: a
write failure is logged loudly and the apply's outcome stands.

**Rendering.** One summary-block row (`telemetry: recorded <path>`,
or an honest `write failed — see log`) at each terminal banner, and
one additive `telemetry` key (path or null) in the `--json` report —
`bale_report` owns both, and the json stream discipline is unchanged.

### 8.10 Non-normal response kinds: bailout and clarification

Two response kinds besides `"normal"` reach apply —
`response_kind: "bailout"` (TARBALL.md §5.6) and
`"clarification"` (TARBALL.md §5.9) — and apply branches on the
kind after pre-flight instead of staging, validating, or committing
anything. This section is the normative apply-time contract for
both. The wire shapes, manifest specifics, and the doctrine of when
the worker returns each kind stay in TARBALL.md; this content moved
here from TARBALL.md §5.6.3 and §5.9.3, which now point back at
this section, because it is a contract on the bale implementation
rather than on response authoring.

#### 8.10.1 Bailout

When apply encounters `response_kind: "bailout"`, it:

1. Prints a clear banner identifying the response as a bailout. No
   changes will be applied; `apply.sh` and `validation.sh` are not
   run against the project.
2. Prints the `manifest.summary` and the first section of
   `handoff.md`.
3. Prints the explicit next-step: *"Run `bale handoff
   <response-NNN>` to package the handoff into a fresh session."*
4. Skips the staging diff and validation invocation entirely.

A bailout consumes its session — post-bailout the session is closed
(§9.5) — and its apply close records telemetry with outcome
`bailout` (§8.9).

#### 8.10.2 Clarification

When apply encounters `response_kind: "clarification"`, it:

1. Prints a clear banner identifying the response as a
   clarification. No changes are applied; `apply.sh` and
   `validation.sh` are not run against the project.
2. Prints the `manifest.summary` and the questions inline — each
   question with its context, default assumption, and why it
   blocked — as it does bailout handoffs.
3. Preserves the manifest under
   `.bale/clarifications/<sid>/NNN.json`. Deliberately *not* under
   `.bale/sessions/<sid>/`: the eventual normal-PASS merge wipes
   the session dir, and the clarification record must outlive the
   session it suspended (its longitudinal value is precisely
   aggregation across completed sessions, TARBALL.md §5.9.4). `NNN`
   increments so a session that clarifies more than once keeps
   every round. The preserved copy carries a `preserved_at` sidecar
   key stamped at write time (v0.3.27) — the record's own timestamp,
   preferred over file mtime by the close-time summary, since mtime
   survives normal use but not every copy/restore path. Pre-v0.3.27
   records have no stamp and read via the mtime fallback; they are
   deliberately not backfilled.
4. **Retains the lock — the session stays open.** This is the one
   deliberate divergence from the bailout, and it is the point: a
   bailout consumes its session (next step `bale handoff`, fresh
   sid); a clarification suspends it. The explicit next step is
   answering the questions in the worker's chat; the session then
   continues to a normal response applied against this same sid.
   If the gap invalidates the request's framing, the recourse is
   `bale unlock` and a repack — the architect's call.

A clarification writes no telemetry record: it suspends the session
rather than closing it, and the eventual normal response records
(§8.9). The rounds still reach the ledger (v0.3.23, board 5): every
closing event — apply/retry terminal closes, `bale revert`, and
every unlock-outcome close, whatever command drives it — stamps a
bale-computed `clarification` summary (`{rounds, records[]}`, read
from `.bale/clarifications/<sid>/` at close time) onto its closing
attempt, and `{rounds: 0, records: []}` when the directory is
absent. The always-stamp rule is the disambiguation: post-epoch, key
presence with `rounds: 0` means *known zero*, key absence means
*pre-epoch unknown* — so aggregation never conflates "no
clarifications" with "no data". The stamp lives on closing attempts
only (a `held`, `scope-drift-refused`, `rejected`, or rollback
attempt is not a closure), and it is what makes step 3's
survives-the-session preservation pay off: the directory outlives
the session by design, and the close happens on the machine that
holds it (§3.5) — a close on a different checkout stamps that
checkout's honest `rounds: 0`, an accepted, self-announcing residual
loss. Field shape: `telemetry-record.schema.json`.

The suspension is visible in `bale status` (v0.3.22): a session with
preserved records under `.bale/clarifications/<sid>/` and no
`bale/<sid>` branch classifies as **clarification-suspended** — its
own lifecycle state, never the packed or abandoned-lock reading —
with a dedicated row (rounds, blocking-question count, latest record
path) and a next-step hint mirroring step 4 above (§5.5; the json
report carries the state on the session enum and the facts under the
additive `session.clarification` key).

---

## 9. Rollback, revert, unlock

Three commands cover three distinct "undo" cases. The distinctions
matter because they operate on different git states.

The line between unlock and revert is whether an apply ran: a session
abandoned **before** any apply — packed, never applied, no
`bale/<sid>` branch — closes with `bale unlock`; a session whose
apply left a commit on `bale/<sid>` — a HOLD under inspection, or a
refused merge — is discarded with `bale revert`. Unlock refuses when
the branch exists and points at revert (§9.3 step 3); the checkout is
never part of the question, since integration doesn't touch it
(ADR-0008).

Since v0.3.17 a third exit closes an open session without either
command: an accepted `bale pack --supersedes <sid>` closes the named
parent as superseded-by-split (§7.2) through the same
close-with-record sequencing unlock uses — closure record per §8.9,
`closure_reason` `superseded-by-split`, `command` `"pack"`, the
record honestly naming the command that produced the event. It is a
close of the no-branch state only: a parent that reached HOLD
refuses supersession and routes through `bale revert` first, the
same branch-exists posture as unlock's step-3 refusal.

### 9.1 `bale revert [sid]` — committed to the bale branch, not yet merged

For a bale branch that exists but hasn't been merged into the origin
branch yet. The common case is a held branch after a failed
validation when inspection is done — since ADR-0008 a HOLD is a
session commit on `bale/<sid>` and the user's checkout was never
switched, so revert has strictly less to undo: force-delete the
branch, close the session. Passed-and-kept is no longer a
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
3. If currently on `bale/<sid>` (a manual checkout during inspection),
   `git checkout <origin_branch>`, logged — switch only, never a
   reset. If the checkout is dirty and git refuses the switch, the
   discard refuses loudly with the remedy (commit, stash, or reset
   your changes on `bale/<sid>`, then re-run) rather than clobber
   WIP. Otherwise the checkout is not touched — under ADR-0008 the
   apply never switched it.
4. `git branch -D bale/<sid>` (force delete).
5. Wipe the session's recorded staging directory (the `staging_path`
   the apply stamped under `.bale/sessions/<sid>/` — since the
   per-session default, `.bale/staging/<sid>/`, or the `--staging-dir`
   override if one was used; only this sid's directory, never a
   sibling session's), then wipe `.bale/sessions/<sid>/` itself.
6. Close the session in the registry if it was open: remove its
   `open` marker (already gone with step 5's wipe; the close is what
   reconciles the compatibility pointer, repointing it to the oldest
   remaining open session or clearing it). The close targets this
   sid, never whichever session the pointer happens to name.

The function owns the full flow — the user doesn't switch branches
or run any preliminary command. A single `bale revert <sid>` leaves
them on their origin branch with the bale branch gone. `--reason`
(v0.3.16) optionally stamps why into the session's telemetry record
as `closure_reason` (§8.9) — same vocabulary and flag spelling as
`bale unlock`'s; omitted records null, since the `reverted` outcome
already names the event.

`--json` (v0.3.19) emits the end-of-run revert report as one line of
JSON on stdout under the shared stream discipline (`[bale] ` lines
and the human block to stderr; human mode unchanged; refusals stay
fail()-shaped with empty stdout); the key contract is owned by
`format_revert_json`'s docstring in `bin/bale_report.py`.

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
   `git stash` before running and `git stash pop` after. Untracked
   paths bale itself leaves behind are disregarded when judging
   cleanliness: the telemetry record under `claude/telemetry/`
   (§8.9; v0.3.23, board 5), and — when `[apply] archive_dir` is
   configured — archived response artifacts matching exactly the
   `<archive_dir>/<sid>/<artifact>` shape apply writes at merge
   (§8.8; v0.3.30 — shape-matched rather than whole-prefix, because
   archive_dir is user-configured ground where unrelated untracked
   work may sit). The rationale is shared: `git revert` rewrites
   tracked content only, and the one collision case (a revert that
   would materialize a file at an untracked path) is refused loudly
   by git itself. When such entries were the only dirt, rollback
   proceeds with a log line naming them — which is what lets a
   rollback → `--undo` toggle complete without an interleaved
   commit. A *modified tracked* file at the same locations still
   refuses (a real conflict surface); `--stash` and `--force`
   behavior is unchanged. Under `[apply] sweep` (§8.8) the carve-out
   is unchanged and the sweep runs entirely post-guard-window: the
   guard judges the tree before any git mutation, and the sweep
   commits only after the revert has landed. What preserves the
   toggle there is the rollback trigger itself — each clean rollback
   and `--undo` commits its own telemetry append immediately, so the
   record (tracked once swept) never sits modified when the next
   guard runs; a skipped sweep leaves it modified-tracked, and the
   next guard's refusal is the loud manual-sweep prompt, exactly the
   conservatism the modified-tracked rule exists for.
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

On the two clean-success paths — a completed rollback and a completed
`--undo` — bale appends the attempt to the session's telemetry record
(§8.9), v0.3.18: outcome `rolled-back` (or `re-applied`), command
`rollback`, `closure_reason` null (rollback closes no session — the
outcome names the event), everything tarball- and validation-shaped
null, and the scope as `[]` when the session directory is long gone at
rollback time (never a fabricated whole-tree). The write is best-effort
and never changes the command's exit; the success output carries the
same `recorded <path>` / `write failed — see log` telemetry row unlock
and revert carry. The conflict and empty-revert paths record nothing,
for the same reason they tag nothing: a record would claim a rollback
that hasn't happened, and `git revert --continue` completes outside
bale's bookkeeping by design.

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
   which `bale handoff`'s lineage chase still reads. Since v0.3.16
   the clear also best-effort appends an `unlocked` /
   `crash-debris` entry to the named sid's telemetry record (§8.9)
   — a registry trace ended, so it records; a telemetry miss is
   logged and swallowed, and the benign no-op contract is
   untouched. An empty pointer writes nothing: there is no session
   to record.
3. Resolve the target session (explicit sid, or the single open
   one). If the sid has a corresponding `bale/<sid>` branch: refuse.
   This means apply ran but didn't reach a terminal state. The user
   should use `bale revert <sid>` instead.
4. Read the session's recorded scope — before the wipe in step 5
   destroys it — and determine the `closure_reason` (§8.9):
   `--reason` when given (choices are the §8.9 vocabulary); else
   `closed-read-only` when the recorded scope is exactly `[]` (a
   §7.2 read-only session, whose exits are unlock and the read-only
   sweep — the next `bale pack --read-only`'s accept-default offer,
   v0.3.21/board 33; the inference keys on `[]`, never on a missing
   scope, which reads conservative whole-tree); else `abandoned`.
   An explicit `--reason` beats the read-only inference.
5. Close the session in the registry (its `open` marker
   is removed and the compatibility pointer reconciled — repointed
   to the oldest remaining open session, or cleared), then remove
   `.bale/sessions/<sid>/`, then write the telemetry record:
   outcome `unlocked`, command `unlock`, the scope as read, the
   `closure_reason` from step 4, everything tarball- and
   validation-shaped null (§8.9). The write is best-effort and
   never changes the command's exit; the summary block reports
   `recorded <path>` or an honest `write failed — see log`, the
   same telemetry row revert's summary carries. Done. No git
   operations.

`--force` overrides the step-3 refusal, but with a prominent warning
and a note in the log; it records identically — branch-preserved is
a summary-row fact, not a closure reason.

`--json` (v0.3.18) emits the end-of-run unlock report as one line of
JSON on stdout — session-close path and benign no-op alike — under the
shared stream discipline (`[bale] ` lines and the human block to
stderr; human mode unchanged); the key contract is owned by
`format_unlock_json`'s docstring in `bin/bale_report.py`, and
`--integration --json` is refused, the report being session-shaped.

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
them differently makes the cost visible. Finer intent distinctions
within a close — abandoned vs superseded vs a master close-out —
are recorded via `--reason` (§8.9), not new commands: the trio
stays intact.

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
| Closed | no `open` marker | none | initial, post-merge, post-revert, post-unlock, post-bailout, post-supersession (an accepted `bale pack --supersedes`, §7.2) | `bale pack` |
| Open, no branch | marker present | none | post-`bale pack` / post-`bale handoff`, before `bale apply` | `bale apply` (any walkthrough path), `bale unlock [sid]`, or closure as superseded-by-split by an accepted `bale pack --supersedes <sid>` (§7.2) |
| Open, with HOLD branch | marker present | `bale/<sid>` w/ the session commit (checkout untouched — ADR-0008) | `bale apply` hit validation failure; user chose inspect | `bale revert [sid]`, `bale retry <tarball> [--sid]` with a corrected response, or apply a corrected response (after `bale revert [sid]`) |

Passed-and-kept is not a state. The apply walkthrough resolves
PASS to either merge (→ empty + `applied/<sid>` tag) or revert
(→ empty) before returning control.

Clarification-suspension (§8.10.2) is a sub-state of the middle row
— marker present, no branch — marked by preserved records under
`.bale/clarifications/<sid>/`. It does not change the table's git
transitions, but `bale status` classifies it distinctly (v0.3.22,
§5.5) so a suspended session never reads as an abandoned lock.

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
performs. After this, bale's git surface is all session-related:
branch creation and force-deletion (`git branch` / `branch -D`), the
plumbing that builds session and merge commits (`read-tree`,
`hash-object`, `update-index`, `write-tree`, `commit-tree` under a
temporary index — §8.6, §8.8), compare-and-swap ref advances
(`update-ref`), the clean-on-target fast-forward
(`git merge --ff-only`, §8.8), tags (`git tag`), rollback's
`git revert` (§9.2), the legacy-HOLD `git checkout` in revert's
transition path (§9.1 step 3), and read-only queries (`status`,
`rev-parse`, `diff`, `log`).

---

## 11. Bale-enforced contract (full list)

Every check below runs mechanically inside bale. Failure → reject
before staging (steps 1–15 of section 8.1) or before commit (sections
8.4 and 8.5). Nothing project-specific.

| # | Check | Phase |
|---|-------|-------|
| 1 | Path-location refusal (cwd / repo root not a system directory) | pack pre-flight |
| 2 | Home-directory refusal (cwd not exactly `$HOME`, unless `--force`) | pack pre-flight |
| 3 | Forecast disjointness (ADR-0015, re-basing ADR-0007's pack-time gate): the pack's resolved write forecast — `--write`, its include-set default, or `[]` under `--read-only` — is disjoint from every open session's recorded forecast; directory entries cover subtrees, `.` covers everything, read includes participate in nothing, and a pre-separation session's recorded include set reads as an over-forecast (conservative) | pack pre-flight |
| 4 | Threshold caps (file count, size, depth) within configured limits | pack scope projection |
| 5 | Tar archive integrity (extractable, no path-traversal entries) | apply pre-flight |
| 6 | Manifest schema valid (all required keys, no unknowns) | apply pre-flight |
| 7 | An open session exists in the registry (ADR-0006) | apply pre-flight |
| 8 | Narrow dirty-on-target refusal (ADR-0008): no **tracked** changes while the checkout is on the session's integration target branch (untracked files never block; any other branch or detached never blocks — integration doesn't touch the checkout) | apply pre-flight |
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
| 20 | No `changes[]` path names a generated artifact — no `__pycache__` / `node_modules` / `dist` / `build` directory component, no `*.pyc` / `*.pyo` basename; conservative deny-list, rejection names the offending paths (§8.1 step 13; `TARBALL.md` §5.1 carries the builder-side rule) | apply pre-flight |
| 21 | Declared-input violations fail the stage loudly (target-base strategy): every `staging.untracked_inputs` entry must exist in the working tree and be untracked at the target tip at stage time — a missing or tracked entry stops the stage rather than being silently skipped | apply stage |
| 22 | Own-scope drift (v0.3.10): every `changes[]` path lies inside the session's **own** recorded scope (`sessions/<sid>/scope.json`; created paths rejected the same as modified). Per-invocation `--allow-out-of-scope PATH` (repeatable; no config key) admits exactly the named paths — any other drift still refuses. The refusal names every offending path and the declared scope, keeps the session open with no git side effects, records telemetry outcome `scope-drift-refused`, and in `--json` mode is the one-line report with that outcome (§8.1 step 14) | apply pre-flight |
| 23 | Detached-HEAD refusal: `bale pack` refuses when the repo's HEAD is detached, before any prompt, tarball, or session state — the integration-target stamp requires a real branch (§7.1 step 4a; the apply-side stamp requirement is row 8's resolution step, §8.1 step 5); listed here out of phase order to keep rows 4–22 stable | pack pre-flight |
| 24 | Detached-HEAD refusal, handoff side: `bale handoff` refuses when the repo's HEAD is detached, before any tarball resolution, prompt, or session state — the new session's integration-target stamp requires a real branch, the same requirement as row 23's pack side (§7.1 step 4a applied to handoff's pre-flight; the stamp itself per §7.6); appended after row 23 per the appended-row precedent of rows 19–23, so rows 1–23 stay stable | handoff pre-flight |
| 25 | Non-normal response-kind shape (ADR-0011, v0.2.10): apply forks on `response_kind` before staging, and the manifest's cross-field rules are enforced there — on a `"clarification"`, every change surface is empty (`changes`, `deferred`, `validation_will_run`, `claims`) and `questions[]` is required non-empty; on every other kind `questions[]` is forbidden (or empty); a `"bailout"` carries the same empty change surfaces (TARBALL.md §5.6.2, §5.9.2; apply-time behavior §8.10). Appended after row 24 per the same appended-row precedent, so rows 1–24 stay stable | apply pre-flight |
| 26 | Required-check superset (board 6 session B): when the project's `[validation] required` set is non-empty and `changes[]` is non-empty, every required name appears verbatim in the manifest's `validation_will_run`. Per-invocation `--allow-missing-required-check NAME` (repeatable; no config key, per the ratified override contract) admits exactly the named names — any other missing name still refuses. The refusal renders both sets, keeps the session open with no git side effects, records telemetry outcome `required-check-refused`, and in `--json` mode is the one-line report with that outcome and a `required_checks` detail object (§8.1 step 15); appended after row 25 per the appended-row precedent, so rows 1–25 stay stable | apply pre-flight |
| 27 | Checkpoint blindness, write side (v0.3.28, board 6 session C; re-based onto the forecast by ADR-0015): when `[validation] base` pins a blind checkpoint, pack refuses a configured-but-dangling checkpoint at the pack-time tip (committed-is-ratified, caught at request-build time) and refuses a resolved write forecast that covers the checkpoint's path (drift-gate containment semantics; a read-only pack's empty forecast covers nothing — its read side is row 31's business). Per-invocation `--allow-checkpoint-in-scope` (flag-only; no config key, per the ratified override contract) admits the covering forecast — FORCE-logged, and the admission stamped as `provenance.checkpoint_scope_admitted` in the request manifest (§7.1 step 4b); appended after row 26 per the appended-row precedent, so rows 1–26 stay stable | pack pre-flight |
| 28 | Checkpoint provenance stamp verification (v0.3.28, board 6 session C): when the request manifest carries `provenance.checkpoint` (stamped by pack: the oracle's `{path, sha256}` at the pack-time tip, or explicit null) and a checkpoint is configured at apply, the base-tree bytes about to run must match the stamp; divergence refuses pre-staging with the session open and no git side effects. Per-invocation `--accept-checkpoint-change` (apply and retry, re-stated each invocation) admits the change — the CURRENT base-tree version runs, FORCE-logged, `stamp_matched: false` recorded in the attempt's telemetry stamp; a verified match records true, a stampless request verifies nothing and records null. `--dry-run` predicts the refusal (§8.5); appended after row 27 per the appended-row precedent, so rows 1–27 stay stable | apply pre-flight |
| 29 | Dangling-checkpoint refusal, apply side (board 6 session A): when `bale.toml`'s `[validation] base` names a blind checkpoint with no committed file at that path in the session's base tree, apply refuses before staging — no staging tree, no `bale/<sid>` branch, session open (committed-is-ratified: a working-tree-only checkpoint is not yet the project's oracle; remedies: commit the checkpoint at the named path, or clear the key via `bale config init`). `--dry-run` predicts the refusal when a checkpoint is configured (the session-B rider; §8.5), and pack's own earlier catch is row 27's dangling half — this row is the apply-side backstop that also covers hand-rolled requests and post-pack config edits. Contract prose in §8.5; row appended after row 28 in v0.3.29 (board 6 session D, the session-C notes' proposed backfill) per the appended-row precedent, so rows 1–28 stay stable | apply pre-flight |
| 30 | Checkpoint blindness, handoff side (v0.3.33): when `[validation] base` pins a blind checkpoint, `bale handoff` runs the same gate implementation as rows 27 and 31 — the dangling refusal and the covering refusal — against its reading-plan-derived forecast (the resolved set of files the bailout's reading plan pre-packs, which on this path is both the read set and the conservative forecast, so one value covers both halves; a plan citing no files resolves to the whole tree, which covers any configured checkpoint), pre-sid, so a refused handoff burns no NNN and leaves no session state. Per-invocation `--allow-checkpoint-in-scope` (mirroring pack's spelling; flag-only, no config key, per the ratified override contract) admits the covering scope — FORCE-logged, and the admission stamped as `provenance.checkpoint_scope_admitted` in the new request manifest through the shared provenance builder, so a bailed checkpoint-maintenance session's handoff renews its admission deliberately rather than inheriting pack's silently; appended after row 29 per the appended-row precedent, so rows 1–29 stay stable | handoff pre-flight |
| 31 | Checkpoint blindness, read side (ADR-0015, board 13 E3): when `[validation] base` pins a blind checkpoint, pack refuses a resolved include set that would ship the checkpoint's content in `context/` to the worker the oracle grades — containment on the resolved include set, same semantics as row 27, conservative by construction (an exclude that would drop the file at walk time still refuses; the remedies are cheap). Same per-invocation `--allow-checkpoint-in-scope` override, same FORCE log, same `provenance.checkpoint_scope_admitted` stamp — one flag admits whichever half fired, since the delegation decision is one decision (§7.1 step 4b). A default pack (no `--include`) covered the checkpoint under the conflated model too, so unflagged packs refuse exactly as before; the row newly bites only a pack whose forecast excludes the oracle while its includes cover it. Appended after row 30 per the appended-row precedent, so rows 1–30 stay stable | pack pre-flight |

Project policy checks (INDEX coherence, ADR sequential, doc inventory
rules) live in the response's `validation.sh` — Claude includes them
per-session, not bale. Bale is project-agnostic.

Bale also does not enforce the request's `out_of_scope` field. That
field carries prose concerns, not glob patterns; mechanical path
matching against it isn't well-defined. Drift against that prose
field is a policy concern, reviewed manually under the
stay-in-the-lane rule (`CLAUDE.md` §6) — distinct from own-scope
*path* drift, which row 22 above enforces mechanically. Projects
wanting mechanical enforcement of prose exclusions add a glob
deny-list to `validation.sh`.

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

*(`bale status` (§5.5) also landed in this phase, at v0.2.3 — net-new
surface beyond the phase's planned scope, recorded in §5's command
table.)*

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
  the other commands the §5.4 global-flags list anticipates, and the
  TARBALL.md §7.4 pass-through of `--verbose` into `validation.sh`
  itself, closed in v0.3.35 — pack and revert gained the flag and the
  verbose path forwards it onto the script's argv; status per §5.4's
  updated bullet.)*
- Optional bash completion (`source` it from shell rc — not required
  for any functionality). *(Landed in v0.2.2 as `bale completion bash`,
  which walks `build_parser()` once and emits a self-contained bash
  function that does pure-shell dispatch — no subprocess back to bale per
  Tab press. Both the help command and the completion script read the
  same source of truth, the argparse parser, so adding a flag in one
  place propagates to both surfaces automatically.)*

The counter and this phase model decoupled during the 0.3.x line:
this paragraph long closed "v0.3 is not yet cut" while the shipped
constant ran ahead — 0.3.27 at the 2026-08-03 ratification of the
ladder below (version per that session's request provenance stamp).
The ratified re-coupling held: **v0.3 is the shipped series**, and
0.4.0 was gated on two items — the `--verbose` thread residue (the
commands still without the flag, plus the TARBALL.md §7.4
pass-through of `--verbose` into `validation.sh` itself) and a
read-only audit diffing the v0.4 selftest checklist below against
the actual suite. Both closed on 2026-08-06: the thread at v0.3.35
(the parenthetical above), and the audit in
`2026-08-06-v04-selftest-audit-006` — doc-only, findings recorded
in that session's notes, the gap list riding forward as post-cut
work under the v0.4 phase. **Cut 2026-08-06 at 0.4.0.** The
ratified ladder superseded the earlier escape hatch (an explicit
architect's call to cut early and track the remainder under v0.3b);
that clause stays retired.

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
  whichever of `README.md` and `notes.md` (plus a legacy
  `next-prompt.md`, §6.2) the response actually included into the
  project's archive convention. *(Landed in v0.3.30 as
  `[apply] archive_dir`, ahead of the phase's own cut — behavior in
  §8.8, rollback-guard interplay in §9.2 step 3, wizard trio in
  `bale_config` per the contract below.)*

Any addition extends `bale_config.walk_configurables()` and
`render_bale_toml()` in the same session — the wizard owns the
discoverable surface (bale-internals.md §2.5).

### v1.0 — contracts become promises

Defined for the first time at the 2026-08-03 ratification. At 1.0.0
the contracts become promises: the wire format (§6),
`record_version` (§8.9), and the `--json` key contracts (§5.4) go
breaking-change-costs-major — from the cut on, a breaking change to
any of them costs a major version.

Gates — both must hold before the cut:

- boards 6 and 10 landing; and
- the first work class earning **and exercising** a real autonomy
  grant.

Explicitly not gated on:

- the API-harness transport — a separate component (MASTER.md §1),
  not part of bale's own 1.0 surface; and
- lifting the solo-project assumption — documented scope (§3.5),
  not debt.

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
