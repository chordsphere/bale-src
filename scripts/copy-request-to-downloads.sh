#!/usr/bin/env bash
# scripts/copy-request-to-downloads.sh — drop the request tarball into
# this user's Windows Downloads folder (WSL-specific destination path).
#
# Wired via bale.toml [hooks].post_pack. Invoked by `bale pack` after the
# request tarball is on disk and the session lock is held. Bale prompts
# before running this script, so confirmation lives upstream — once we
# reach here the user has already opted in for this invocation.
#
# This is a user-supplied hook script in the bale contract; bale does
# not embed copy logic. It happens to live in the bale-src repo because
# bale-src is the canonical first consumer of post_pack, but a different
# project could wire any script of its own choosing.
#
# Environment (set by bale):
#   BALE_REPO_ROOT  — absolute path to the repo. Used to locate the
#                     outbox.
#   BALE_SESSION_ID — full session id. Used to name the source tarball.
#   BALE_HOOK       — "post_pack". Unused here but present for hooks
#                     that share a script across types.
#
# Failure modes (intentionally noisy via `set -euo pipefail`):
#   - `$dst` not present (e.g. running on a non-WSL host) → cp errors,
#     pack still succeeded — the hook is post-pack and advisory.
#   - source tarball missing → cp errors. Should not happen since bale
#     just wrote it, but the shell will surface anything weird.

set -euo pipefail

src="$BALE_REPO_ROOT/.bale/outbox/request-$BALE_SESSION_ID.tar.gz"
dst="/mnt/c/Users/chord/Downloads/"

cp "$src" "$dst"
printf '[post_pack] copied %s -> %s\n' "$src" "$dst"
