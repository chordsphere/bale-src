# bale

bale runs Claude sessions through tarballs. You pack a **request tarball**
(a goal, the files to read, the paths the session may change) and hand it
to the worker; the worker hands back a **response tarball**; `bale apply`
validates it, stages the changes against a copy of your project, runs the
**blind checkpoint** (when the project configures one) beside the
response's own `validation.sh`, and then
merges on **PASS** or holds the session's branch for inspection on
**HOLD**. The checkpoint is a planner-authored script the worker never
sees or writes — it grades the outcome, not the worker's own claims. In a
worker transcript you will see every turn end in one of four shapes: a
response tarball, a probe block (a read-only script whose output you paste
back), a light question block (at most three one-line questions you answer
inline), or a clarification response (a blocking question set that travels
through `bale relay`).

## What you get

After install, `~/bale/` (or wherever you extracted) contains:

```
bale/
  bin/
    bale               # the CLI entrypoint (Python, stdlib only)
    VERSION            # the release version
    bale_pack.py       # `bale pack`: gather, gate, and build the request tarball
    bale_open.py       # `bale open`: verify and replay a planner bundle
    bale_apply.py      # `bale apply` / `retry`: pre-flight, stage, validate, merge or hold
    bale_staging.py    # staging copies, apply.sh reconciliation, worktree helpers
    bale_sandbox.py    # namespace confinement for response scripts
    bale_validate.py   # schema and manifest shape checks
    bale_report.py     # end-of-run reports, --json output, telemetry records
    bale_relay.py      # `bale relay`: the clarification exchange thread
    bale_rollback.py   # `bale rollback`: git-revert a merged session
    bale_stats.py      # `bale stats`: aggregate the telemetry corpus
    bale_config.py     # bale.toml loading and the `bale config` wizard
    _bale_toml.py      # TOML reader with a Python 3.10 fallback
  docs/
    CLAUDE.md          # the worker's working agreement
    TARBALL.md         # the wire contract for requests, responses, probes
    PLANNER.md         # the planning desk: packs, briefs, checkpoints
    DOCS.md            # how documentation is kept
    CODE.md            # how code layout is kept
  schemas/             # JSON Schemas for manifests, records, and bundles
  tools/
    craft_response.py  # the worker's response scaffolder (and the desk's bundler)
    response_lint.py   # the worker's pre-ship response lint
  install.sh           # finalize an install (run after extracting)
  validate.sh          # sanity-check this install
  upgrade.sh           # replace this install with a newer release, keeping user/
  README.md            # this file
  user/                # YOURS — created on first `bale config init --global`
```

bale injects the five `docs/` files and the two `tools/` scripts into every
request it packs, so every project sees the same contract regardless of its
own files. `user/` is the one directory bale never owns: your install-wide
`bale.toml`, global hook scripts under `user/scripts/`, and the hook
acceptance store live there. The release tarball ships nothing under it, and
`upgrade.sh` carries it across.

## Install and upgrade

Requirements: Python 3.10+ (stdlib only — no pip), `git`, `bash`, and POSIX
`tar`/`cp`/`rm`. On Windows, run under WSL or Git Bash. Response scripts run
confined by default through `unshare` (util-linux) and unprivileged user
namespaces. On a host without them, pass `--no-sandbox` per apply, or set
`[sandbox] enabled = false` in the project's `bale.toml` — either way every
unconfined run is logged loudly.

Extract the release anywhere writable and run the installer:

```bash
tar -xzf bale-vX.Y.Z.tar.gz -C ~/
~/bale/install.sh
```

`install.sh` restores executable bits, verifies the layout, offers a
symlink at `~/.local/bin/bale`, and finishes by running `validate.sh`. Flags:
`-y`, `--no-symlink`, `--no-validate`, and `--no-termux-shebang` (on Termux
it offers to rewrite shebangs to the Termux interpreters). Run
`~/bale/validate.sh` again any time to check the install.

To upgrade, prefer `upgrade.sh` — it moves `user/` aside, replaces the
install with the new release (so files removed between versions don't linger),
moves `user/` back, and runs the new `install.sh`:

```bash
~/bale/upgrade.sh path/to/bale-vX.Y.Z.tar.gz     # -y, --no-validate, --no-symlink
```

Extracting a new release over the old one works for a quick test but leaves
stale files behind; `rm -rf ~/bale` before extracting is clean but deletes
`user/`.

### Configure a project

`cd` into a git repo and run the wizard:

```bash
bale config init            # writes <repo>/bale.toml (commit it)
bale config init --global   # writes <install>/user/bale.toml (install-wide defaults)
```

It is idempotent — re-run it to review or change anything; Enter keeps each
value. The project walk checks your git identity first and ends with the
`.baleignore` walkthrough. Project values override global ones per key, and
`x` at a prompt suppresses an inherited global value. Some sections are
project-layer only and never appear in the global walk: `[validation]` (the
blind checkpoint and required checks), `[sandbox]`, `[pack]` (the include
group), and `[probe]` (the probe scaffold's clipboard command). The wizard
rewrites the whole file, so keys it doesn't walk are dropped.

The key most people set first is `apply.search_paths` — the directories bale
searches when a command is given a relative file name, and where bare
`bale apply` looks for responses. Point it at wherever your browser saves
downloads:

```toml
[apply]
search_paths = ["~/Downloads"]
```

Cwd is always searched first; `~` and `$VARS` expand at use time.

## Daily use

`bale help <command>` (or `bale <command> --help`) is the full flag reference
for every command below. For bash, `source <(bale completion bash)` adds Tab
completion.

### Pack a request

```bash
bale pack "Add a debounced search box" --slug search-box --include src tests --write src/search tests/search
```

The goal is the ask. `--include` chooses what ships as context (default: the
whole repo, minus `.baleignore` and the built-in filters). `--write` declares
the **write forecast** — the paths the session is expected to change; open
sessions with disjoint forecasts run side by side, and work the worker ships
outside its forecast is admitted per path at apply. `--read-only` declares an
empty forecast for a discussion or audit session. `--readme-file brief.md`
ships prose context; `--checkpoint-file check.sh` commits the session's blind
checkpoint in the same step when `[validation] base` names a per-session
`{sid}` path. Run `bale pack` with no goal on a terminal to get the
interactive wizard instead.

Pack writes `.bale/outbox/request-<sid>.tar.gz`, and its report ends with a
paste-ready session opener: upload the tarball to the worker's chat and
paste the opener.

### Open a planner bundle

```bash
bale open board-12.bale-bundle
```

A planner desk can deliver a whole session as one `.bale-bundle` file (made
with `tools/craft_response.py --bundle`): the pack command, the brief, and
the blind checkpoint. `bale open` verifies the member hashes, runs the pack
command's argument-level gates, dry-runs the checkpoint (when the bundle
carries one) against a copy of your current tree — it should fail, since the
work hasn't landed yet — and then packs.

### Apply a response

```bash
bale apply                               # newest response-*.tar.gz in cwd + apply.search_paths
bale apply response-2026-09-16-search-box-001.tar.gz
```

Bare `bale apply` examines the two newest `response-*.tar.gz` files, picks the
one answering an open session, shows you its identity, and asks before
applying (decline is the default; ambiguity refuses rather than guessing).
Apply refuses malformed responses before staging anything, runs the
response's scripts in a sandbox, and then shows the verdict. On **PASS**,
Enter merges into the branch the session was packed from. On **HOLD**, the session's commit stays on
`bale/<sid>` and the staging copy is kept; the summary shows how to diff it,
where the log is, and the two ways forward — `bale retry` or `bale revert`.
`--dry-run`, `--show-validator`, and `--show-apply-script` look without
applying.

### Retry a HOLD, or amend the checkpoint

A HOLD resolves one of two ways, depending on who was wrong.

```bash
bale retry response-2026-09-16-search-box-001.tar.gz       # the work was wrong: a corrected response
bale amend-checkpoint check-v2.sh --sha256 <published-hash>  # the checkpoint was wrong
```

When the work was wrong, the worker ships a corrected response and `bale
retry` reruns the pipeline under the same session id. When the planner rules
the checkpoint itself defective, `bale amend-checkpoint` verifies the
amended script against its published hash, commits it, and prints the retry
line — the same response retried with `--accept-checkpoint-change`, the
deliberate per-invocation acceptance of the changed oracle.

### Answer a clarification

When the worker returns a clarification response, `bale apply` records its
questions and keeps the session open. Answers travel as exchange records:

```bash
bale relay 2026-09-16-search-box-001 answers.json   # record a round, print the paste block
bale relay 2026-09-16-search-box-001                # re-print the latest round's paste block
```

The session then continues to a normal response under the same id.

### Hand off a bailout

When a session can't fit its goal, the worker returns a bailout response;
`bale apply` prints the next step:

```bash
bale handoff response-2026-09-16-search-box-001.tar.gz
```

It builds a fresh request carrying the bailout's `handoff.md` and the files
its reading plan names, inheriting the original goal and write forecast.

### Undo

```bash
bale revert [sid]      # discard a held, unmerged bale/<sid> branch
bale rollback [sid]    # git-revert a merged session (--undo re-applies, --list shows status)
bale unlock [sid]      # close a packed session that was never applied
```

### Look around

```bash
bale status            # read-only: open sessions, outbox, staging, config
bale stats             # claim/verdict agreement and HOLD rates from claude/telemetry/
```

Both take `--json`.

### Hooks

`[hooks] post_pack` and `post_apply_pass` in `bale.toml` name scripts bale
runs after a pack or a PASSing apply. Bale asks before running a hook;
accepting a project-layer script once remembers its exact bytes, so that
script defaults to accept from then on (changed bytes ask again):

```bash
bale config hooks                   # list remembered acceptances
bale config hooks --forget 3fa9c1   # forget one (it asks again next time)
```

## Where to read next

- `bale help <command>` — the command reference, in this install.
- `docs/TARBALL.md` — the wire contract: request, response, probe, and the
  clarification and light-question shapes.
- `docs/CLAUDE.md` — the worker's working agreement.
- `docs/PLANNER.md` — the planning desk: authoring packs, briefs, and blind
  checkpoints.
- `docs/DOCS.md` and `docs/CODE.md` — how documentation and code are kept.
- `BALE.md` — the full tool specification. It lives in the bale-src
  repository and is not shipped in the release tarball.

If you're reading this from a bale-src checkout, you're in bale's own source:
bale is developed through bale sessions, `scripts/reinstall.sh` (wired as
`post_apply_pass`) reinstalls after each PASS, and `claude/INDEX.md` is the
contributor map.
