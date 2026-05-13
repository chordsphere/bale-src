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
  docs/
    CLAUDE.md       # the working agreement bale injects into every request
    TARBALL.md      # the wire-format contract for request/response tarballs
    DOCS.md         # doc-management philosophy
  install.sh        # finalize an install (run after extracting)
  validate.sh       # sanity-check this install
  README.md         # this file
```

The three docs in `docs/` are the global workflow docs — bale ships them and
injects them into every request, so any project using bale sees the same
contract regardless of the project's own files.

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

For a clean upgrade over an existing install:

```bash
rm -rf ~/bale && tar -xzf bale-vX.Y.Z.tar.gz -C ~/ && ~/bale/install.sh
```

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

You can also skip `bale config init` entirely and just use bale; the first
`bale pack` in a non-git directory offers a git-init walkthrough, and
hooks/search-paths default to off if `bale.toml` doesn't exist.

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
