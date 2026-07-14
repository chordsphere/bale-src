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

# Sanity: the source layout must look like a bale install root. The file
# list is DERIVED at run time from scripts/build.sh's RELEASE_FILES — the
# canonical release list — instead of hand-copied here; the hand copy this
# replaces is exactly the drift class the derivation removes. Extraction
# depends on the format contract documented above RELEASE_FILES in
# build.sh: "RELEASE_FILES=(" at column 0, one bare path per line, ")" at
# column 0. If the block is missing, unterminated, reshaped, or extracts
# empty, we die loudly rather than sanity-check against nothing.
BUILD_SH="$REPO/scripts/build.sh"
[[ -f "$BUILD_SH" ]] || die "cannot derive the release list: $BUILD_SH not found (not a bale-src checkout?)"

RELEASE_FILES=()
while IFS= read -r line; do
  case "$line" in
    ""|*[!A-Za-z0-9._/-]*)
      die "unexpected RELEASE_FILES entry '$line' extracted from $BUILD_SH — array format changed? (format contract above RELEASE_FILES in build.sh)" ;;
  esac
  RELEASE_FILES+=("$line")
done < <(
  awk '
    !inblock && $0 == "RELEASE_FILES=(" { inblock = 1; next }
    inblock && $0 == ")"                { found = 1; exit }
    inblock {
      sub(/#.*$/, "")
      gsub(/^[ \t]+|[ \t]+$/, "")
      if ($0 != "") print
    }
    END { exit found ? 0 : 1 }
  ' "$BUILD_SH"
)
# A process substitution's exit status is invisible to the loop, so a
# missing/unterminated array surfaces as zero extracted lines — the
# emptiness check below is the loud failure for that case too.
[[ ${#RELEASE_FILES[@]} -gt 0 ]] \
  || die "extracted an empty RELEASE_FILES from $BUILD_SH — array missing, empty, or format changed"

for f in "${RELEASE_FILES[@]}"; do
  [[ -f "$REPO/$f" ]] || die "source layout missing: $REPO/$f"
done
log "source layout OK (${#RELEASE_FILES[@]} files, derived from scripts/build.sh)"

# Tree coverage: every file on disk under the release-owned directories
# must appear in the derived list. Same guard (and same __pycache__ /
# *.pyc pruning) as build.sh's pre-flight; running it here makes the
# "new file, in no list" drift loud at the next apply rather than the
# next release.
RELEASE_LIST_NL="$(printf '%s\n' "${RELEASE_FILES[@]}")"
uncovered=""
while IFS= read -r f; do
  rel="${f#"$REPO"/}"
  printf '%s\n' "$RELEASE_LIST_NL" | grep -qFx -- "$rel" || uncovered="$uncovered $rel"
done < <(find "$REPO/bin" "$REPO/docs" "$REPO/schemas" "$REPO/tools" \
           -name __pycache__ -prune -o -name '*.pyc' -prune -o -type f -print | sort)
[[ -z "$uncovered" ]] \
  || die "tree coverage: file(s) on disk but in no release list:$uncovered — add to scripts/build.sh's RELEASE_FILES (and install.sh's INSTALL_LAYOUT), or remove from the tree"
log "tree coverage OK (bin/ docs/ schemas/ tools/ all covered)"

# Refuse to install over a non-bale directory. If $BALE_INSTALL exists
# but doesn't have bin/bale inside it, something else is at that path —
# bail rather than clobber.
if [[ -d "$BALE_INSTALL" && ! -e "$BALE_INSTALL/bin/bale" ]]; then
  die "$BALE_INSTALL exists but doesn't look like a bale install (no bin/bale). Resolve manually."
fi

mkdir -p "$BALE_INSTALL"

# Mirror the install-relevant pieces. Wipe bin/, docs/, schemas/, and
# tools/ first so a rename in the source doesn't leave stale files in the
# install. The top-level scripts and README are individual files so a
# plain cp suffices. user/ is intentionally left alone — it's the
# global-config subtree owned by the user, never in bale-src. This
# selective-mirror approach is what makes reinstall.sh user/-safe by
# construction (vs. the rm -rf install approach the README documents as
# an alternative).
rm -rf "$BALE_INSTALL/bin" "$BALE_INSTALL/docs" "$BALE_INSTALL/schemas" "$BALE_INSTALL/tools"
cp -R "$REPO/bin"     "$BALE_INSTALL/bin"
cp -R "$REPO/docs"    "$BALE_INSTALL/docs"
cp -R "$REPO/schemas" "$BALE_INSTALL/schemas"
cp -R "$REPO/tools"   "$BALE_INSTALL/tools"
cp    "$REPO/install.sh"  "$BALE_INSTALL/install.sh"
cp    "$REPO/validate.sh" "$BALE_INSTALL/validate.sh"
cp    "$REPO/upgrade.sh"  "$BALE_INSTALL/upgrade.sh"
cp    "$REPO/README.md"   "$BALE_INSTALL/README.md"
log "mirrored bin/, docs/, schemas/, tools/, install.sh, validate.sh, upgrade.sh, README.md (user/ left alone)"

# Finalize via install.sh in non-interactive mode.
# --no-symlink: an existing symlink (if any) was set on initial install
#               and we don't want to touch it during a reinstall.
# install.sh runs validate.sh at the end by default, which is the verifier
# that the new install is healthy.
"$BALE_INSTALL/install.sh" -y --no-symlink

# Closing summary. Runs after install.sh's own "install complete" block above,
# so this reinstall verdict — the wrapper's key facts — is the final output the
# dev loop leaves on screen. The same facts are logged as a preamble at the top
# (progress trail); restating them here puts them last, where they're wanted.
log "---"
log "reinstall complete"
log "  source:     $REPO"
log "  target:     $BALE_INSTALL"
log "  session id: ${BALE_SESSION_ID:-(unset)}"
