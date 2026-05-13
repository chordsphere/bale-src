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
# For a clean upgrade over an existing install, the recommended path is
# upgrade.sh, which preserves the user-owned <install>/user/ subtree
# (global config + global hook scripts) across the swap:
#   ~/bale/upgrade.sh path/to/new-bale-release.tar.gz
# Alternatives (drift- or data-loss-prone — see README for tradeoffs):
#   rm -rf ~/bale && tar -xzf bale-vX.Y.Z.tar.gz -C ~/ && ~/bale/install.sh
#   tar -xzf bale-vX.Y.Z.tar.gz -C ~/ && ~/bale/install.sh   # may leave stale files

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

# Verify expected layout. Catches a partial/corrupt extract before we do
# anything. user/ is intentionally NOT in this list — it's user-owned and
# absent on a fresh install; we report its state below but don't fail.
for f in bin/bale docs/CLAUDE.md docs/TARBALL.md docs/DOCS.md install.sh validate.sh upgrade.sh README.md; do
  [[ -e "$INSTALL_DIR/$f" ]] || die "missing expected file: $INSTALL_DIR/$f"
done
log "layout OK"

# Report user/ state. Present after an upgrade (upgrade.sh restored it).
# Absent on a fresh install — `bale config init --global` creates it on
# first write. install.sh never creates user/ itself, because doing so
# implicitly claims that subtree on a clean install; we'd rather it stay
# absent until the user opts into global config.
if [[ -d "$INSTALL_DIR/user" ]]; then
  if [[ -f "$INSTALL_DIR/user/bale.toml" ]]; then
    log "global config present: $INSTALL_DIR/user/bale.toml"
  else
    log "user/ subtree present (no global bale.toml inside)"
  fi
else
  log "no global config (no user/ subtree); run 'bale config init --global' to set one up"
fi

# Restore executable bits. Some filesystems (NTFS, FAT) drop them on extract.
chmod +x "$BALE" "$INSTALL_DIR/validate.sh" "$INSTALL_DIR/upgrade.sh"
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

# Point the user at the canonical first-project setup. Printed after validate
# so it's the last thing the user sees on a clean install. We don't try to
# run `bale config init` from here — it requires a git repo (the project the
# user wants to use bale on), and the install dir is not that.
log "---"
log "next steps:"
log "  - cd to a project (git repo) you want to use bale with, then"
log "    run 'bale config init' to walk through per-repo setup."
log "  - optionally run 'bale config init --global' (from anywhere) to set"
log "    install-wide defaults that every project inherits per-key."
log "  (both walkthroughs are idempotent; re-run any time.)"
