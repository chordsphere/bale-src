# bale-internals.md

> How `bin/bale` is structured. Schemas and contracts for the per-repo
> configurables mechanism. Pull when a session touches `bin/bale`,
> `bale.toml`, or anything in the hook surface.

---

## 1. The shape of `bin/bale`

A single Python file (`bin/bale`) with no third-party dependencies. The
top of the file declares constants (paths, exclusions, version, hook
names); the rest is organized as roughly-flat sections, each named with
a banner comment. Read top-to-bottom:

1. **Imports + constants.** `VERSION`, `INSTALL_ROOT`, `GLOBAL_DOCS`,
   `BAKED_IN_EXCLUDE_DIRS`, `SECRET_PATTERNS`, `SECRET_PATH_EXCLUDES`,
   `SYSTEM_DIRS`, `BALE_CONFIG`, `HOOK_NAMES`.
2. **Logging.** `log()` and `fail()`. Logging is first-draft, not
   retrofit — every non-trivial action goes through them.
3. **Shell / git helpers.** `run()`, `git()`, `repo_root()`. Subprocess
   wrappers with capture-and-text defaults.
4. **Hashing.** `sha256_file()`, `sha256_bytes()`.
5. **Session IDs + the per-day counter.** `next_session_id()` —
   `YYYY-MM-DD-<slug>-NNN`.
6. **Lock handling.** `.bale/current_session` is the active-session
   sentinel; one lock per repo.
7. **`.gitignore` for `.bale/`.** Bale auto-appends `.bale/` to
   `.gitignore` on first `pack` if missing.
8. **Path-safety checks.** `refuse_system_dir()`, `is_path_safe()`.
9. **Pack pipeline.** File enumeration, slug validation, manifest
   construction, tarball construction.
10. **`cmd_pack`.**
11. **Apply pipeline.** Manifest validation, file presence + sha256
    + path safety, staging, validation, commit-or-hold logic.
12. **`cmd_apply`.**
13. **`cmd_revert`** and **`cmd_retry`.** Revert discards a HOLDed
    session entirely (and clears the lock); retry discards the same
    HOLD state but preserves the lock and reruns the apply pipeline
    against a corrected response tarball. Both call a shared
    `_discard_hold_state()` helper for the destructive cleanup; the
    lock-clear and post-cleanup steps are caller policy. The apply
    pipeline body itself is extracted as `_apply_pipeline()` so both
    `cmd_apply` and `cmd_retry` invoke it without duplication.
14. **`bale.toml` configurables.** `load_config()`, `get_hook()`.
15. **Hook invocation.** `confirm_yn()`, `run_hook()`.
16. **`bale config init` wizard.** `_prompt_value()`,
    `walkthrough_git_identity()`, `walk_configurables()`,
    `render_bale_toml()`, `cmd_config_init()`.
17. **CLI parser + `main`.**

Two-level subparsing only — `bale <verb>` for the four top-level
commands, plus `bale config <subcommand>` for the config family. At
v0.0.1 the only `config` subcommand is `init`; `set`, `get`, `edit` are
deliberately out of scope until they earn a place.

---

## 2. `bale.toml` — the configurables file (two layers)

### 2.1 Location and lifecycle

Two files share the same TOML schema, differing only in layer:

- **Project layer:** `<repo>/bale.toml`, repo root.
  - **Source of truth:** committed, team-shared. Every clone of the repo
    gets the same wiring.
  - **Lifecycle:** written by `bale config init`. Hand-edits work, but
    re-running the wizard rewrites the file from its walked surface, so
    unrecognized keys you hand-edit in are dropped on re-run.
- **Global (install) layer:** `<install>/user/bale.toml`.
  - **Source of truth:** user-owned, never in the release tarball. Lives
    inside `<install>/user/` (the only user-owned subtree of the install)
    so the install dir stays portable as a unit — copy `<install>/`
    anywhere and the global config travels with it. `upgrade.sh` preserves
    `user/` across release swaps; `install.sh` never creates it (does
    nothing on absent, reports state on present).
  - **Lifecycle:** written by `bale config init --global`. The wizard
    creates `<install>/user/` (and `user/scripts/`-style subdirs as
    needed) on first write. Same idempotency contract as the project file.

At v0.0.x there are no `set/get/edit` subcommands at either layer; `init`
plus hand-edits is the entire surface. If the need is real, they land later.

### 2.2 Layering rules — project overrides global per-key

`merged_config(repo)` produces the effective config bale operates on:

- **Per-key replacement.** Project wins on any key it sets; project absent
  means inherit from global. There is no append semantics across layers.
- **Empty value at project = explicit suppression.** A key present but
  empty at the project layer (`post_pack = ""` for scalars, `search_paths
  = []` for lists) wins as "no value" — the inherited global is NOT
  consulted. The typed accessors (`get_hook`, `get_apply_search_paths`)
  already treat empty as unset, so this falls out of the merge mechanically.
- **List-shaped configs use replace semantics.** When project sets
  `search_paths`, its list wins fully (including the empty-list suppress
  form). No mixed-list semantics — append across machines would mean
  unpredictable order, and order matters for first-match-wins lookups.
- **Hook paths resolve at merge time** against the layer that owns them.
  Project hooks resolve against `<repo>/`; global hooks resolve against
  `<install>/user/`. `merged_config` returns absolute filesystem paths so
  callers (`get_hook`, `run_hook`) don't track provenance.

### 2.3 Absence is silent (at both layers)

The whole mechanism is opt-in:

- Both files absent → bale behaves exactly as it did pre-configurables.
- File absent at one layer → that layer contributes nothing; merge is
  whatever the other layer says.
- Both files present but a key absent in both → that configurable is
  silently skipped.

Bale never nags about an unconfigured configurable.

### 2.4 Malformed files are fatal

A typo at either layer is fatal — `load_config`/`load_global_config`
raise through `fail()` with the parser's line/column. We never want a
typo to silently disable a hook the user thought was wired up.

### 2.5 Schema at v0.0.x

```toml
[hooks]
post_pack = "scripts/copy-request-to-downloads.sh"
post_apply_pass = "scripts/reinstall.sh"

[apply]
search_paths = ["~/Downloads"]
```

The schema is identical at both layers. The only thing that differs is
what hook paths resolve against (the file's own directory). Future
sessions add more keys under `[hooks]` and (potentially) new top-level
sections; each new key extends `walk_configurables()` in the same session
so the discoverable surface stays in sync.

The wizard owns the discoverable surface at both layers. If you add a key
without extending `walk_configurables()`, there is no canonical way for a
user to set it.

---

## 3. The hook contract

### 3.1 What a hook is

A hook is a path to a user-supplied executable script. Bale invokes it
at a specific moment in its lifecycle. Bale never embeds install or copy
logic; the script is the consumer's responsibility.

Hook paths resolve relative to whichever layer's `bale.toml` they live in:

- Project-layer hooks (`<repo>/bale.toml`) resolve against the repo root.
  Place the script under `<repo>/scripts/foo.sh`, reference it as
  `"scripts/foo.sh"` in the config.
- Global-layer hooks (`<install>/user/bale.toml`) resolve against
  `<install>/user/`. Place the script under `<install>/user/scripts/foo.sh`,
  reference it the same way: `"scripts/foo.sh"`.

`merged_config` resolves these to absolute filesystem paths at merge time,
so `get_hook` and `run_hook` always work with absolute paths and don't
need to know the originating layer. `run_hook` does identify the layer
in its pre-invocation prompt — "hook: post_pack (global)" vs "(project)"
— so the user sees what's about to run.

### 3.2 Always-prompt

Bale prompts the user before invoking any hook. The reason is that a
hook script can do anything its author chose, including writes outside
the repo, software installs, network calls, and so on — bale can't
classify these ex ante. The prompt is the safety net.

Decline at the prompt is silent and logged but not an error. The
bale operation that triggered the hook (e.g. a PASS apply) has already
succeeded; declining the hook just means "skip the post-step."

### 3.3 Environment

Bale exports three environment variables to every hook:

| Variable | Value |
|----------|-------|
| `BALE_HOOK` | the hook name, e.g. `post_apply_pass` |
| `BALE_SESSION_ID` | the full session id that triggered the hook |
| `BALE_REPO_ROOT` | absolute path to the repo |

The script runs with cwd set to the repo root and inherits the user's
environment (including `PATH`, `HOME`, etc.).

### 3.4 Exit codes

- `0` → logged as success.
- non-zero → logged as a hook-side issue. **Bale's primary operation is
  not failed by a non-zero hook exit.** By the time `post_apply_pass`
  runs, the session is already committed, merged, and tagged —
  unwinding it because a reinstall script burped is the wrong move.
  The user sees the non-zero log line and can fix the script.

### 3.5 Stdout/stderr

Not captured. The hook's output streams to the user's terminal so a
long-running install can show progress. The session log records the
invocation (`[hook X] invoking ...`) and the exit summary, but not the
hook's output — that's the hook's job to log on its own if it cares.

### 3.6 Hooks defined at v0.0.1

**`post_apply_pass`** — invoked after `bale apply` succeeds (PASS path,
post-merge). Used by bale-src itself to reinstall the just-merged
version of bale into `$BALE_INSTALL` (default `~/bale`). The reinstall
script lives at `scripts/reinstall.sh` and is wired up via this repo's
`bale.toml`. Never fires on revert.

**`post_pack`** — invoked after `bale pack` writes the request tarball
and acquires the session lock. Same opt-in/prompted contract as
`post_apply_pass`. Use cases: copying the tarball to a shared folder,
opening Claude in the browser with the tarball ready to drag in,
pinging chat that a request is queued. Lifecycle ordering matters for
the wizard — `post_pack` is walked before `post_apply_pass` (pack
happens before apply), and `render_bale_toml()` emits TOML keys in
the same order.

### 3.7 Hooks coming in follow-up sessions

These are listed here to make the design rationale visible — they are
not implemented yet.

- **Apply search paths** — not a hook but a configurable under the
  same mechanism. A `[apply]` table (working name) with a list of
  directories `bale apply` should look in when given a bare session
  id rather than a path. Lets `bale apply 2026-05-13-foo-003` find
  the tarball wherever it landed without retyping the path.

This extension slots into the existing mechanism: a new branch in
`walk_configurables()` and `render_bale_toml()`. No new hook entry, no
new bale command.

---

## 4. `bale config init` — the wizard

### 4.1 Canonical interface

The wizard is the single way to opt in to the configurables mechanism,
at either layer. A user who only ever runs `bale config init` (and
`bale config init --global`) should be able to discover every configurable
that exists; conversely, a configurable bale knows about but the wizard
doesn't walk through is a contract violation.

### 4.2 Two modes, one surface

`bale config init` runs against the project layer (`<repo>/bale.toml`).
`bale config init --global` runs against the global layer
(`<install>/user/bale.toml`). Both modes call the same
`walk_configurables()`; what differs:

| Aspect | Project mode (default) | Global mode (`--global`) |
|---|---|---|
| Target file | `<repo>/bale.toml` | `<install>/user/bale.toml` |
| Requires git repo? | Yes (refuses if not in one) | No |
| Walks git identity? | Yes | No (identity is per-repo) |
| Shows inherited values? | Yes — global is below, displayed as inherited | No — no layer below |
| Hook-path hint | "Path relative to `<repo>/`" | "Path relative to `<install>/user/`" |
| Header in generated file | project-flavored | global-flavored |

### 4.3 Walkthrough (project mode)

1. Resolve repo root; refuse system dirs and non-git-repos.
2. Load existing `<repo>/bale.toml` (if present) AND the global config
   from `<install>/user/bale.toml` (if present) — the latter becomes the
   `inherited` argument to `walk_configurables`.
3. Walk git identity:
   - For each of `user.name`, `user.email`, check `git config --get`.
     If already set (anywhere — repo-local or global), report and leave
     alone.
   - If unset everywhere, prompt. Non-empty input is written to the
     **repo-local** git config (`git config <key> <value>`, no
     `--global`). Empty input is treated as a skip.
4. Walk every configurable in `walk_configurables()`. For each, display
   shows the current at this layer AND any inherited-from-global value
   AND the effective value the merge would produce. Input semantics:
   - Empty input → keep current at this layer.
   - Non-empty value → set at this layer (overrides any inherited).
   - Literal `-` → clear at this layer (revert to inheriting if a global
     value exists, else unset).
   - Literal `x` (offered only when an inherited value is shown) →
     write empty string / empty list — explicit suppression of the
     inherited value.
5. Render via `render_bale_toml(cfg, layer="project")` and write to
   `<repo>/bale.toml`.

### 4.4 Walkthrough (global mode)

1. Don't resolve a repo; refuse only system-dir cwd.
2. Load existing `<install>/user/bale.toml` (if present). No inherited
   layer below.
3. No git-identity walk.
4. Walk every configurable. Display shows only the current value (no
   "inherited" line, no `x` option — nothing to suppress). Input
   semantics:
   - Empty input → keep current.
   - Non-empty value → set.
   - Literal `-` → clear.
5. Create `<install>/user/` if it doesn't exist (this is the global
   layer's first write).
6. Render via `render_bale_toml(cfg, layer="global")` and write to
   `<install>/user/bale.toml`.

### 4.5 Idempotency

Re-running at either layer shows the current value for each configurable
and accepts Enter to keep. The output file after a re-run-with-all-Enters
equals the input file modulo trailing whitespace — the wizard is safe
to run on a whim.

### 4.6 Headers in the generated files

`render_bale_toml(cfg, layer=...)` prepends a layer-specific fixed header
comment that points back at the wizard. The header makes it instantly
obvious which file you're reading (project vs global) and warns that
hand-edited unknown keys are dropped on re-run.

---

## 5. End-to-end: a bale-on-bale PASS

The full loop with everything wired up:

1. User runs `bale pack ... --slug X` in `bale-src/`. Request tarball
   lands in `.bale/outbox/`, lock acquired, session sid issued.
2. User ships the tarball to Claude.
3. Claude returns a response tarball.
4. User runs `bale apply <response.tar.gz>`:
   1. Tarball validated, manifest schema-checked, `apply.sh` and
      `validation.sh` syntax-checked, sha256s verified.
   2. Project state copied into `.bale/staging/`, response files
      overlaid, deletes applied.
   3. `validation.sh` runs in staging. PASS or HOLD.
   4. PASS path: changes applied to working tree on `bale/<sid>`
      branch, committed, merged into origin with `--no-ff`, tagged
      `applied/<sid>`, lock cleared, session dir wiped.
   5. **`run_hook(repo, merged_config(repo), "post_apply_pass", sid)`**
      — `merged_config` layers `<install>/user/bale.toml` under
      `<repo>/bale.toml`, resolves hook paths against their owning
      layer's root, and yields absolute paths. Looks up
      `[hooks].post_apply_pass`, finds `scripts/reinstall.sh` (a project
      hook in this case, resolving to `<repo>/scripts/reinstall.sh`),
      prompts the user.
   6. User accepts. `scripts/reinstall.sh` runs with `BALE_HOOK`,
      `BALE_SESSION_ID`, `BALE_REPO_ROOT` exported. It mirrors `bin/`,
      `docs/`, `install.sh`, `validate.sh` into `$BALE_INSTALL`,
      finalizes via `install.sh -y --no-symlink`.
   7. The next `bale pack` from anywhere uses the freshly installed
      bale.

The reinstall step is what closes the loop — without it, every PASS
landed in bale-src but the running `bale` binary kept being the old
one. The configurables mechanism is what makes step 5 a one-line
addition instead of a hardcoded branch in `cmd_apply`.
