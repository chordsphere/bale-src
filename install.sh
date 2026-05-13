#!/usr/bin/env bash
# install.sh — finalize a bale install (bundled with the release tarball).
#
# Run this after extracting bale's release tarball. It does:
#   - chmod +x bin/bale and validate.sh (extract can lose the bit)
#   - Verify the install layout is intact
#   - Offer a symlink at ~/.local/bin/bale, with caution if one exists
#   - Run validate.sh
#
# Usage:
#   ~/bale/install.sh                  # interactive
#   ~/bale/install.sh -y               # auto-yes all prompts
#   ~/bale/install.sh --no-symlink     # skip the symlink offer
#   ~/bale/install.sh --no-validate    # skip the trailing validate
#   ~/bale/install.sh -h | --help      # this help
#
# For a clean upgrade over an existing install:
#   rm -rf ~/bale && tar -xzf bale-vX.Y.Z.tar.gz -C ~/ && ~/bale/install.sh

set -euo pipefail

# This script's directory IS the bale install root.
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
BALE="$INSTALL_DIR/bin/bale"
SYMLINK_TARGET="$HOME/.local/bin/bale"

YES=0
DO_SYMLINK=1
DO_VALIDATE=1

for arg in "$@"; do
  case "$arg" in
    -y|--yes)       YES=1 ;;
    --no-symlink)   DO_SYMLINK=0 ;;
    --no-validate)  DO_VALIDATE=0 ;;
    -h|--help)      sed -n '2,19p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) printf '[install] error: unknown flag: %s\n' "$arg" >&2; exit 1 ;;
  esac
done

log() { printf '[install] %s\n' "$*"; }
die() { printf '[install] error: %s\n' "$*" >&2; exit 1; }
confirm() {
  [[ "$YES" == "1" ]] && return 0
  read -r -p "[install] $* [y/N] " ans
  [[ "$ans" =~ ^[Yy]$ ]]
}

log "install dir: $INSTALL_DIR"

# Verify expected layout. Catches a partial/corrupt extract before we do anything.
for f in bin/bale docs/CLAUDE.md docs/TARBALL.md docs/DOCS.md validate.sh; do
  [[ -e "$INSTALL_DIR/$f" ]] || die "missing expected file: $INSTALL_DIR/$f"
done
log "layout OK"

# Restore executable bits. Some filesystems (NTFS, FAT) drop them on extract.
chmod +x "$BALE" "$INSTALL_DIR/validate.sh"
log "ensured executable bits"

# Symlink onto PATH (optional).
if [[ "$DO_SYMLINK" == "1" ]]; then
  mkdir -p "$(dirname "$SYMLINK_TARGET")"
  if [[ -L "$SYMLINK_TARGET" ]]; then
    existing="$(readlink "$SYMLINK_TARGET")"
    if [[ "$existing" == "$BALE" ]]; then
      log "symlink already points to this install ($SYMLINK_TARGET); no change"
    else
      log "symlink at $SYMLINK_TARGET currently points elsewhere: $existing"
      if confirm "repoint $SYMLINK_TARGET -> $BALE?"; then
        ln -sf "$BALE" "$SYMLINK_TARGET"
        log "repointed symlink"
      else
        log "left existing symlink alone"
      fi
    fi
  elif [[ -e "$SYMLINK_TARGET" ]]; then
    # Not a symlink — a regular file or directory at that path. Don't clobber.
    die "$SYMLINK_TARGET exists and is not a symlink. Resolve manually before re-running."
  else
    if confirm "create symlink $SYMLINK_TARGET -> $BALE?"; then
      ln -s "$BALE" "$SYMLINK_TARGET"
      log "created symlink $SYMLINK_TARGET"
      case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *) log "note: $HOME/.local/bin is not on PATH. Add to your shell rc or invoke by full path." ;;
      esac
    else
      log "skipped symlink (re-run install.sh to add it later, or 'ln -s' by hand)"
    fi
  fi
else
  log "skipping symlink step (--no-symlink)"
fi

# Validate at the end.
if [[ "$DO_VALIDATE" == "1" ]]; then
  log "---"
  "$INSTALL_DIR/validate.sh"
else
  log "skipping validate (--no-validate); run $INSTALL_DIR/validate.sh manually any time"
fi
