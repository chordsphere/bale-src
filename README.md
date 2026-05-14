# bale

A CLI that orchestrates Claude sessions via request/response tarballs.

You author a request describing what you want, hand the tarball to Claude,
get a response tarball back, and bale validates it, stages the changes
against a copy of your project, runs your session's validation script, and
either commits-and-merges (PASS) or holds the branch for inspection (HOLD).

## What you get

After install, `~/bale/` (or wherever you extracted) contains:

```
bale/
  bin/bale          # the CLI entrypoint (Python, stdlib only)
  bin/bale_config.py  # configurables loader/merger + `bale config init` wizard
  docs/
    CLAUDE.md       # the working agreement bale injects into every request
    TARBALL.md      # the wire-format contract for request/response tarballs
    DOCS.md         # doc-management philosophy
    CODE.md         # code-layout philosophy (extraction, splitting, indexing)
  install.sh        # finalize an install (run after extracting)
  validate.sh       # sanity-check this install
  upgrade.sh        # in-place upgrade to a newer release, preserving user/
  README.md         # this file
  user/             # USER-OWNED. Optional; created by `bale config init --global`.
                    # Holds global bale.toml + global hook scripts. Never in
                    # the release tarball; survives upgrade.sh.
```

The four docs in `docs/` are the global workflow docs — bale ships them and
injects them into every request, so any project using bale sees the same
contract regardless of the project's own files.

`user/` is the only directory inside the install that bale doesn't own. It's
where your install-wide (global) `bale.toml` and global hook scripts live.
A fresh install has no `user/` subtree; `bale config init --global` creates
it on first write. Everything inside is preserved across upgrades when you
use `upgrade.sh`.

## Install

Extract the release tarball anywhere writable (default: `~/`), then run
`install.sh`:

```bash
tar -xzf bale-vX.Y.Z.tar.gz -C ~/
~/bale/install.sh
```

`install.sh`:
  - verifies the layout is intact,
  - restores executable bits (some filesystems strip them on extract),
  - offers a symlink at `~/.local/bin/bale → ~/bale/bin/bale` so `bale`
    works as a bare command (you can decline; invoke by full path otherwise),
  - runs `validate.sh` to confirm the install is healthy.

`install.sh --help` covers the flags (`-y`, `--no-symlink`, `--no-validate`).

## Upgrading

Three paths, in order of preference:

**1. `upgrade.sh` (recommended).** Preserves `user/` across the swap.

```bash
~/bale/upgrade.sh path/to/new-bale-release.tar.gz
```

It moves `user/` aside, wipes the install dir, extracts the new release,
moves `user/` back, and runs the new `install.sh`. This is the only path
that's both drift-free (stale files from prior versions are gone) and
user-data-safe (your `user/bale.toml` and `user/scripts/` survive).

**2. `rm -rf && extract` (manual, drift-free but nukes user/).** Use only
when you don't have a `user/` subtree (or you've backed it up):

```bash
rm -rf ~/bale && tar -xzf bale-vX.Y.Z.tar.gz -C ~/ && ~/bale/install.sh
```

**3. `tar -xzf` over the existing install (untracked drift risk).** The new
release's files overwrite the old, but anything *removed* between versions
stays behind:

```bash
tar -xzf bale-vX.Y.Z.tar.gz -C ~/ && ~/bale/install.sh
```

Use only for quick local tests, never for the install you rely on.

## Requirements

- Python 3.11+ (stdlib only — no pip, no virtualenv).
- `git`, `bash`, and POSIX `tar`/`cp`/`rm` on `PATH`.

On Windows, run under WSL or Git Bash — bale assumes a POSIX shell.

## First-time setup, per project

`cd` into a project (any git repo) you want to use bale with, then run:

```bash
bale config init
```

This is the canonical setup walkthrough. It is idempotent — re-run any time
to review or change values, pressing Enter to keep each one. It walks:

  - **Git identity** — your `user.name` and `user.email`, used for the
    commits bale makes on the apply path. If either is already set
    (anywhere — repo-local or global), bale leaves it alone. Otherwise
    bale prompts and writes to the repo-local git config.

  - **Hooks** (optional) — `post_pack` and `post_apply_pass` scripts.
    Hooks let you wire custom behavior into bale's lifecycle (e.g., copy
    the request tarball into a shared folder after `pack`, or run a
    deploy/reinstall step after a PASSing `apply`). Press Enter to skip;
    you can revisit later.

  - **Tarball search paths** (optional) — directories `bale apply` and
    `bale retry` should look in when given a bare tarball name. Useful
    if a `post_pack` hook drops the request somewhere predictable.

The result is `bale.toml` at the repo root, committed alongside the rest
of the project. Absent file or absent key means "silently skip" — the
mechanism is opt-in by design.

### Optional: global (install-wide) defaults

Two layers share the same schema:

  - **Project layer**: `<repo>/bale.toml`, what `bale config init` writes.
    Committed and team-shared.
  - **Global layer**: `<install>/user/bale.toml`, what `bale config init
    --global` writes. Lives inside the install and follows it as a unit —
    user-owned, preserved across `upgrade.sh`, never in the release tarball.

When both layers set a key, the project wins. When only the global sets it,
the project inherits. To suppress an inherited global at a particular project
without setting your own, set the key to `""` (empty string for scalars,
`[]` for lists) — the wizard offers this as an explicit `x` option when it
sees you're walking over an inherited value.

Global hook scripts live under `<install>/user/scripts/`. Project hook scripts
live under `<repo>/`. Hook paths resolve relative to whichever layer owns them.

You can also skip `bale config init` entirely and just use bale; the first
`bale pack` in a non-git directory offers a git-init walkthrough, and
hooks/search-paths default to off at both layers when nothing is configured.

## Daily use

```bash
bale pack "<one-sentence goal>" --slug <short-kebab-slug>
#   builds .bale/outbox/request-<sid>.tar.gz; you hand it to Claude.

bale apply <response-tarball>
#   validates, stages, runs validation.sh in staging, commits or holds.

bale retry <new-response>
#   for a HOLDed session: re-attempt with a corrected response, same sid.

bale revert <sid>
#   discard a held bale branch when inspection is done.
```

Run `bale --help` for the full command surface and `bale <command> --help`
for any specific command. The workflow these commands enforce is described
in `docs/CLAUDE.md` and `docs/TARBALL.md`; read those when you want the why.

## bale-src — this is also bale's own source

If you're reading this from a git checkout (rather than the extracted
release tarball), you're in **bale-src**, the source repo for the bale
tool. bale-src evolves through bale-on-bale sessions: bale is used to
modify bale itself, and `scripts/reinstall.sh` (wired as `post_apply_pass`
in `bale.toml`) reinstalls the just-merged version into your bale install
dir after each PASS.

For the contributor map, see `claude/INDEX.md`.
