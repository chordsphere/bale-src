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
13. **`cmd_revert`.**
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

## 2. `bale.toml` — the per-repo configurables file

### 2.1 Location and lifecycle

- **Path:** `<repo>/bale.toml`, repo root.
- **Source of truth:** committed, team-shared. Not per-developer —
  every clone of the repo gets the same hook wiring.
- **Lifecycle:** written by `bale config init`. Hand-edits work, but
  re-running the wizard rewrites the file from its walked surface, so
  unrecognized keys you hand-edit in are dropped on re-run. At v0.0.x
  there is no escape hatch for this — `set/get/edit` subcommands will
  land in a later session if the need is real.

### 2.2 Absence is silent

The whole mechanism is opt-in:

- File absent → bale behaves exactly as it did pre-configurables. No
  warning, no prompt to run `bale config init`.
- File present but a key absent → that configurable is silently
  skipped.
- Key present but the value is `""` (empty string) → also silently
  skipped. This lets the wizard write `key = ""` for "I considered this
  and chose to skip" without a separate delete path. In practice the
  wizard's render omits unset keys, but `get_hook()` honors the empty
  case if the file is hand-edited.

The contract is uniform: anywhere a configurable could be read, "not
configured" is a silent no-op. Bale never nags about a configurable
that hasn't been opted in to.

### 2.3 Malformed files are fatal

A typo in `bale.toml` is fatal — `load_config()` raises through
`fail()` with the parser's line/column. We never want a typo to
silently disable a hook the user thought was wired up.

### 2.4 Schema at v0.0.1

```toml
[hooks]
post_apply_pass = "scripts/reinstall.sh"
```

Only one section, one key. Future sessions add:

- More keys under `[hooks]` (e.g. `post_pack`).
- A new top-level section for path resolution (working name `[apply]`
  with a `search_paths` array, but the exact shape is the next
  session's call).

The wizard owns the discoverable surface. If you add a key without
extending `walk_configurables()`, there is no canonical way for a user
to set it.

---

## 3. The hook contract

### 3.1 What a hook is

A hook is a path to a user-supplied executable script, repo-relative.
Bale invokes it at a specific moment in its lifecycle. Bale never
embeds install or copy logic; the script is the consumer's
responsibility.

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

### 3.7 Hooks coming in follow-up sessions

These are listed here to make the design rationale visible — they are
not implemented yet.

- **`post_pack`** (next session) — invoked after `bale pack` writes the
  request tarball. Use case: opening Claude in the browser with the
  tarball ready to drag in, or copying the tarball to a shared folder.
  Same contract as `post_apply_pass`: opt-in, prompted, exit code is
  advisory.
- **Apply search paths** (session after next) — not a hook but a
  configurable under the same mechanism. A `[apply]` table (working
  name) with a list of directories `bale apply` should look in when
  given a bare session id rather than a path. Lets `bale apply
  2026-05-13-foo-003` find the tarball wherever it landed without
  retyping the path.

Both extensions slot into the existing mechanism: a new entry in
`HOOK_NAMES`, a new branch in `walk_configurables()`, and (for the
apply paths) a new branch in `render_bale_toml()`. No new wire-format,
no new bale command.

---

## 4. `bale config init` — the wizard

### 4.1 Canonical interface

The wizard is the single way to opt in to the configurables mechanism.
A user who only ever runs `bale config init` should be able to discover
every configurable that exists; conversely, a configurable bale knows
about but the wizard doesn't walk through is a contract violation.

### 4.2 Walkthrough

1. Resolve repo root; refuse system dirs and non-git-repos.
2. Load existing `bale.toml` (if present).
3. Walk git identity:
   - For each of `user.name`, `user.email`, check `git config --get`.
     If already set (anywhere — repo-local or global), report and
     leave alone.
   - If unset everywhere, prompt. Non-empty input is written to the
     **repo-local** git config (`git config <key> <value>`, no
     `--global`). Empty input is treated as a skip.
4. Walk every configurable in `walk_configurables()`. For each:
   - Show its description and current value (or `(unset)`).
   - Prompt for new value.
   - Empty input → keep current.
   - Non-empty input → set.
   - Literal `-` → clear.
5. Render the result via `render_bale_toml()` and write to
   `<repo>/bale.toml`.

### 4.3 Idempotency

Re-running on a configured repo shows the current value for each
configurable and accepts Enter to keep. The output file after a
re-run-with-all-Enters equals the input file modulo trailing whitespace
— the wizard is safe to run on a whim.

### 4.4 Header in the generated file

`render_bale_toml()` prepends a fixed header comment that points back
at the wizard. The header explicitly warns that hand-edited unknown
keys are dropped on re-run.

---

## 5. End-to-end: a bale-on-bale PASS

The full loop with everything wired up:

1. User runs `bale pack ... --slug X` in `bale-src/`. Request tarball
   lands in `.bale/outbox/`, lock acquired, session sid issued.
2. User ships the tarball to Claude.
3. Claude returns a response tarball.
4. User runs `bale apply <response.tar.gz>`:
   1. Tarball validated, manifest schema-checked, sha256s verified.
   2. Project state copied into `.bale/staging/`, response files
      overlaid, deletes applied.
   3. `validation.sh` runs in staging. PASS or HOLD.
   4. PASS path: changes applied to working tree on `bale/<sid>`
      branch, committed, merged into origin with `--no-ff`, tagged
      `applied/<sid>`, lock cleared, session dir wiped.
   5. **`run_hook(repo, load_config(repo), "post_apply_pass", sid)`**
      — loads `bale.toml`, looks up `[hooks].post_apply_pass`, finds
      `scripts/reinstall.sh`, prompts the user.
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
