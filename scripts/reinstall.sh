#!/usr/bin/env bash
# scripts/reinstall.sh — reinstall bale from this bale-src checkout.
#
# Wired via bale.toml [hooks].post_apply_pass. Invoked by `bale apply` on
# the PASS path after the session's commit has been merged. Bale prompts
# before running this script, so confirmation lives upstream — once we
# reach here the user has already opted in for this invocation.
#
# This is a user-supplied script in the bale contract; bale does not
# embed install or copy logic. It happens to live in the bale-src repo
# because bale-src is the canonical first consumer of post_apply_pass,
# but a different project could wire any script of its own choosing.
#
# Environment:
#   BALE_INSTALL    — install root to write to. Default: ~/bale.
#                     A symlink at ~/.local/bin/bale -> $BALE_INSTALL/bin/bale
#                     is left alone (install.sh's --no-symlink path).
#   BALE_REPO_ROOT  — set by bale to the repo root. Falls back to
#                     `git rev-parse --show-toplevel` when run by hand.
#   BALE_HOOK       — set by bale to "post_apply_pass". Unused here but
#                     present for hooks that share a script across types.
#   BALE_SESSION_ID — set by bale to the session id. Logged for traceability.

set -euo pipefail

BALE_INSTALL="${BALE_INSTALL:-$HOME/bale}"
REPO="${BALE_REPO_ROOT:-}"
if [[ -z "$REPO" ]]; then
  REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || {
    echo "[reinstall] error: BALE_REPO_ROOT unset and not in a git repo" >&2
    exit 1
  }
fi

log() { printf '[reinstall] %s\n' "$*"; }
die() { printf '[reinstall] error: %s\n' "$*" >&2; exit 1; }

log "source:     $REPO"
log "target:     $BALE_INSTALL"
log "session id: ${BALE_SESSION_ID:-(unset)}"

# Sanity: the source layout must look like a bale install root.
for f in bin/bale bin/bale_config.py bin/bale_validate.py bin/bale_staging.py bin/bale_rollback.py docs/CLAUDE.md docs/TARBALL.md docs/DOCS.md docs/CODE.md schemas/request-manifest.schema.json schemas/response-manifest.schema.json schemas/diagnostics.schema.json install.sh validate.sh upgrade.sh README.md; do
  [[ -f "$REPO/$f" ]] || die "source layout missing: $REPO/$f"
done

# Refuse to install over a non-bale directory. If $BALE_INSTALL exists
# but doesn't have bin/bale inside it, something else is at that path —
# bail rather than clobber.
if [[ -d "$BALE_INSTALL" && ! -e "$BALE_INSTALL/bin/bale" ]]; then
  die "$BALE_INSTALL exists but doesn't look like a bale install (no bin/bale). Resolve manually."
fi

mkdir -p "$BALE_INSTALL"

# Mirror the install-relevant pieces. Wipe bin/, docs/, and schemas/ first so
# a rename in the source doesn't leave stale files in the install. The
# top-level scripts and README are individual files so a plain cp suffices.
# user/ is intentionally left alone — it's the global-config subtree owned
# by the user, never in bale-src. This selective-mirror approach is what
# makes reinstall.sh user/-safe by construction (vs. the rm -rf install
# approach the README documents as an alternative).
rm -rf "$BALE_INSTALL/bin" "$BALE_INSTALL/docs" "$BALE_INSTALL/schemas"
cp -R "$REPO/bin"     "$BALE_INSTALL/bin"
cp -R "$REPO/docs"    "$BALE_INSTALL/docs"
cp -R "$REPO/schemas" "$BALE_INSTALL/schemas"
cp    "$REPO/install.sh"  "$BALE_INSTALL/install.sh"
cp    "$REPO/validate.sh" "$BALE_INSTALL/validate.sh"
cp    "$REPO/upgrade.sh"  "$BALE_INSTALL/upgrade.sh"
cp    "$REPO/README.md"   "$BALE_INSTALL/README.md"
log "mirrored bin/, docs/, schemas/, install.sh, validate.sh, upgrade.sh, README.md (user/ left alone)"

# Finalize via install.sh in non-interactive mode.
# --no-symlink: an existing symlink (if any) was set on initial install
#               and we don't want to touch it during a reinstall.
# install.sh runs validate.sh at the end by default, which is the verifier
# that the new install is healthy.
"$BALE_INSTALL/install.sh" -y --no-symlink

log "reinstall complete"
