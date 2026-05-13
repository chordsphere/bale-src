#!/usr/bin/env bash
# upgrade.sh — clean-replace this bale install with a new release tarball,
# preserving the user/ subtree (the only user-owned location inside the
# install: global config and global hook scripts).
#
# Usage:
#   ~/bale/upgrade.sh path/to/new-bale-release.tar.gz
#
# What it does:
#   1. Validates the new tarball looks like a bale install (bin/bale exists).
#   2. Moves <install>/user/ aside to <install>.user-backup/.
#   3. rm -rf <install>/ and extracts the new tarball in its place.
#   4. Moves user/ back into the new install.
#   5. Runs the new install.sh (which restores exec bits, manages the
#      symlink, and runs validate.sh).
#
# What it preserves: <install>/user/ (in its entirety — bale.toml plus any
# scripts/ tree the user has built up).
#
# What it does NOT preserve: anything you hand-edited outside user/. The
# release tarball's contents are authoritative; that's the contract for
# every release file (bin/bale, docs/*, install.sh, validate.sh, README.md,
# upgrade.sh itself). Hand-edits inside user/ ARE preserved.
#
# Why this script ships in the release: making upgrades clean-replace by
# default is the only mechanism that prevents stale-file drift (a renamed
# file in v0.0.N leaving its old copy behind from v0.0.N-1). Two other paths
# exist and are documented in README.md (tar-over-top; rm -rf + extract),
# but they're discouraged because they either leave drift (tar-over-top) or
# nuke user/ (rm -rf without preservation).
#
# Flags:
#   -y, --yes              non-interactive (no prompts).
#   --no-validate          skip the final validate.sh run (install.sh's flag,
#                          passed through). Useful for scripted upgrades.

set -euo pipefail

INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
NEW_TARBALL=""
YES="0"
PASS_TO_INSTALL=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -y|--yes)         YES="1"; PASS_TO_INSTALL+=("-y");           shift ;;
    --no-validate)    PASS_TO_INSTALL+=("--no-validate");          shift ;;
    --no-symlink)     PASS_TO_INSTALL+=("--no-symlink");           shift ;;
    -h|--help)
      sed -n '2,/^$/p' "$0" | sed 's/^# \?//'
      exit 0
      ;;
    -*)
      echo "[upgrade] error: unknown flag: $1" >&2
      echo "[upgrade] usage: $0 [-y] [--no-validate] [--no-symlink] <new-bale-release.tar.gz>" >&2
      exit 2
      ;;
    *)
      if [[ -n "$NEW_TARBALL" ]]; then
        echo "[upgrade] error: unexpected extra argument: $1 (already have tarball $NEW_TARBALL)" >&2
        exit 2
      fi
      NEW_TARBALL="$1"
      shift
      ;;
  esac
done

if [[ -z "$NEW_TARBALL" ]]; then
  echo "[upgrade] error: no tarball given" >&2
  echo "[upgrade] usage: $0 [-y] [--no-validate] [--no-symlink] <new-bale-release.tar.gz>" >&2
  exit 2
fi

log() { printf '[upgrade] %s\n' "$*"; }
die() { printf '[upgrade] error: %s\n' "$*" >&2; exit 1; }

confirm() {
  if [[ "$YES" == "1" ]]; then return 0; fi
  local prompt="$1"
  read -r -p "$prompt [y/N] " ans </dev/tty
  [[ "$ans" == "y" || "$ans" == "Y" ]]
}

# Resolve and verify the new tarball.
if [[ ! -f "$NEW_TARBALL" ]]; then die "tarball not found: $NEW_TARBALL"; fi
NEW_TARBALL="$(cd "$(dirname "$NEW_TARBALL")" && pwd)/$(basename "$NEW_TARBALL")"

log "install:    $INSTALL_DIR"
log "tarball:    $NEW_TARBALL"

# Sanity: this script must be inside a bale install.
if [[ ! -x "$INSTALL_DIR/bin/bale" ]]; then
  die "$INSTALL_DIR does not look like a bale install (no executable bin/bale). Refusing to upgrade."
fi

# Sanity: peek at the tarball; require it contains bin/bale.
if ! tar -tzf "$NEW_TARBALL" 2>/dev/null | grep -q '\(^\|/\)bin/bale$'; then
  die "tarball $NEW_TARBALL does not contain bin/bale — does not look like a bale release."
fi

# Detect the tarball's top-level prefix (it's usually a single directory like
# bale-vX.Y.Z/). We need to extract into a temp dir and then mirror its
# contents into $INSTALL_DIR, because we don't know the prefix in advance.
TMP_EXTRACT="$(mktemp -d "${TMPDIR:-/tmp}/bale-upgrade.XXXXXX")"
USER_BACKUP="$INSTALL_DIR.user-backup-$$"

cleanup_on_error() {
  local rc=$?
  if [[ -d "$USER_BACKUP" && ! -d "$INSTALL_DIR/$(basename "${USER_BACKUP%-*}")" ]]; then
    log "error path: user/ backup remains at $USER_BACKUP — restore manually if needed."
  fi
  rm -rf "$TMP_EXTRACT"
  exit "$rc"
}
trap cleanup_on_error EXIT

log "extracting tarball to staging: $TMP_EXTRACT"
tar -xzf "$NEW_TARBALL" -C "$TMP_EXTRACT"

# Find the install root inside the extracted tarball: the dir containing bin/bale.
EXTRACTED_ROOT=""
while IFS= read -r -d '' candidate; do
  if [[ -x "$candidate/bin/bale" || -f "$candidate/bin/bale" ]]; then
    EXTRACTED_ROOT="$candidate"
    break
  fi
done < <(find "$TMP_EXTRACT" -mindepth 1 -maxdepth 2 -type d -print0)

if [[ -z "$EXTRACTED_ROOT" ]]; then
  die "could not locate bin/bale inside extracted tarball at $TMP_EXTRACT"
fi
log "extracted root: $EXTRACTED_ROOT"

# Confirm before destructive step.
log ""
log "about to:"
log "  1. move $INSTALL_DIR/user/  →  $USER_BACKUP   (if user/ exists)"
log "  2. rm -rf $INSTALL_DIR/* (everything except user/, which is moved aside)"
log "  3. copy new install contents in place"
log "  4. move user/ back"
log "  5. run install.sh on the new install"
log ""
if ! confirm "proceed?"; then
  log "aborted by user; nothing changed."
  trap - EXIT
  rm -rf "$TMP_EXTRACT"
  exit 0
fi

# Preserve user/.
if [[ -d "$INSTALL_DIR/user" ]]; then
  mv "$INSTALL_DIR/user" "$USER_BACKUP"
  log "moved user/ aside: $USER_BACKUP"
else
  log "no user/ subdir to preserve (this install hasn't been configured globally yet)"
fi

# Wipe everything else in the install dir. Use find rather than rm -rf $INSTALL_DIR
# itself, because we want to keep the directory (a symlink at ~/.local/bin/bale
# might point to a file inside it; recreating the dir invalidates the inode-
# based references potential mounts/aliases might hold).
find "$INSTALL_DIR" -mindepth 1 -maxdepth 1 ! -name "$(basename "$USER_BACKUP")" -exec rm -rf {} +
log "wiped install dir (preserved user/ backup)"

# Copy the new install in place. Use cp -R so symlinks and exec bits are
# preserved (install.sh will re-chmod the canonical executables anyway).
cp -R "$EXTRACTED_ROOT"/. "$INSTALL_DIR"/
log "copied new install contents into $INSTALL_DIR"

# Restore user/.
if [[ -d "$USER_BACKUP" ]]; then
  if [[ -e "$INSTALL_DIR/user" ]]; then
    die "unexpected: $INSTALL_DIR/user exists in the new install. The release tarball should not ship user/. Aborting before clobbering preserved data; backup remains at $USER_BACKUP."
  fi
  mv "$USER_BACKUP" "$INSTALL_DIR/user"
  log "restored user/ from backup"
fi

# Hand off to install.sh.
log "---"
log "running install.sh on the upgraded install"
trap - EXIT
rm -rf "$TMP_EXTRACT"
exec "$INSTALL_DIR/install.sh" "${PASS_TO_INSTALL[@]}"
