#!/usr/bin/env bash
# install.sh — finalize a bale install (bundled with the release tarball).
#
# Run this after extracting bale's release tarball. It does:
#   - chmod +x the shipped executables (extract can lose the bit)
#   - On Termux, offer to rewrite shebangs to the Termux interpreter
#   - Verify the install layout is intact
#   - Offer a symlink at ~/.local/bin/bale, with caution if one exists
#   - Run validate.sh
#
# Usage:
#   ~/bale/install.sh                      # interactive
#   ~/bale/install.sh -y                   # auto-yes all prompts
#   ~/bale/install.sh --no-symlink         # skip the symlink offer
#   ~/bale/install.sh --no-validate        # skip the trailing validate
#   ~/bale/install.sh --no-termux-shebang  # skip the Termux shebang rewrite
#   ~/bale/install.sh -h | --help          # this help
#
# For a clean upgrade over an existing install, the recommended path is
# upgrade.sh, which preserves the user-owned <install>/user/ subtree
# (global config + global hook scripts) across the swap:
#   ~/bale/upgrade.sh path/to/new-bale-release.tar.gz
# Alternatives (drift- or data-loss-prone — see README for tradeoffs):
#   rm -rf ~/bale && tar -xzf bale-vX.Y.Z.tar.gz -C ~/ && ~/bale/install.sh
#   tar -xzf bale-vX.Y.Z.tar.gz -C ~/ && ~/bale/install.sh   # may leave stale files

set -euo pipefail

# ---------------------------------------------------------------------------
# Functions first, install flow second. Everything above the source guard
# below is side-effect-free: defining these functions runs no install steps,
# so the file can be `source`d to reach a single helper in isolation (this is
# how the response's validation.sh exercises the shebang rewrite hermetically,
# without driving a real install). Direct execution falls through the guard
# into the install flow at the bottom.
# ---------------------------------------------------------------------------

log() { printf '[install] %s\n' "$*"; }
die() { printf '[install] error: %s\n' "$*" >&2; exit 1; }
confirm() {
  # ${YES:-0}: tolerate being defined-but-uncalled when the file is sourced
  # (YES is only assigned in the install flow below the guard).
  [[ "${YES:-0}" == "1" ]] && return 0
  read -r -p "[install] $* [y/N] " ans
  [[ "$ans" =~ ^[Yy]$ ]]
}

# --- Termux shebang handling -----------------------------------------------
# On Termux (Android) there is no /usr/bin/env, so the stock
# `#!/usr/bin/env <interp>` shebangs the release ships fail to exec unless the
# termux-exec LD_PRELOAD shim is installed and active. Rewriting them to
# absolute Termux interpreter paths lets the install run with no dependency on
# termux-exec. Detection and the per-file rewrite are split into small
# functions so the rewrite transform can be tested in isolation.

# Termux's $PREFIX (…/files/usr) is the root every interpreter lives under;
# fall back to the canonical path if $PREFIX is somehow unset.
termux_prefix() {
  printf '%s' "${PREFIX:-/data/data/com.termux/files/usr}"
}

# True when we appear to be running under Termux. TERMUX_VERSION is set by the
# Termux app itself and is the strongest signal; a $PREFIX under com.termux and
# the canonical bin dir are corroborating fallbacks.
is_termux() {
  [[ -n "${TERMUX_VERSION:-}" ]] && return 0
  [[ "${PREFIX:-}" == *"/com.termux/"* ]] && return 0
  [[ -d "/data/data/com.termux/files/usr/bin" ]] && return 0
  return 1
}

# Resolve an interpreter name (bash, python3, …) to an absolute path under the
# Termux prefix. Prefer the real on-PATH location (handles a non-default
# prefix); fall back to $prefix/bin/<name>. Returns 1 (and prints nothing) if
# neither resolves, so the caller can report a skip rather than write a shebang
# pointing at a binary that isn't there. This is path resolution intrinsic to
# the rewrite, not a prerequisite-package check (that is out of scope).
termux_interp_path() {
  local name="$1" prefix resolved
  prefix="$(termux_prefix)"
  if resolved="$(command -v "$name" 2>/dev/null)" && [[ -n "$resolved" ]]; then
    printf '%s' "$resolved"
    return 0
  fi
  if [[ -x "$prefix/bin/$name" ]]; then
    printf '%s' "$prefix/bin/$name"
    return 0
  fi
  return 1
}

# Rewrite one file's shebang to an absolute Termux interpreter path, in place.
#
# Prints exactly one outcome token to stdout (and nothing else, so callers and
# the validation test can capture it cleanly):
#   rewritten:<old> -> <new>   the shebang was rewritten
#   current                    already points under the Termux prefix (no-op)
#   not-shebang                line 1 is not a `#!` line (left untouched)
#   no-interp                  shebang named no interpreter (left untouched)
#   unresolved:<name>          interpreter did not resolve (left untouched)
#   error-*                    an fs operation failed (returns non-zero)
#
# The replacement is an atomic rename (mktemp beside the target, then mv). A
# rename leaves any process already executing this file reading the original,
# now-unlinked inode — so install.sh rewriting its OWN shebang mid-run is safe:
# the current run finishes on the old content, the new shebang takes effect on
# the next invocation. The executable bit is preserved across the rename.
rewrite_shebang() {
  local file="$1"
  local first body f0 f1 rest interp prefix newpath new

  first="$(head -n 1 "$file")"
  case "$first" in
    '#!'*) ;;
    *) printf 'not-shebang'; return 0 ;;
  esac

  body="${first#\#!}"
  # `read` splits on IFS (space/tab) without globbing — safer than an array.
  read -r f0 f1 rest <<< "$body"
  if [[ -z "$f0" ]]; then
    printf 'no-interp'; return 0
  fi

  # `#!/usr/bin/env bash` -> interpreter is the 2nd field (bash);
  # `#!/usr/bin/python3` -> interpreter is the basename of the 1st field.
  if [[ "$(basename "$f0")" == "env" && -n "$f1" ]]; then
    interp="$f1"
  else
    interp="$(basename "$f0")"
  fi
  if [[ -z "$interp" ]]; then
    printf 'no-interp'; return 0
  fi

  prefix="$(termux_prefix)"
  # Already Termux-pointed (e.g. a re-run, or an already-fixed install)?
  if [[ "$f0" == "$prefix/"* ]]; then
    printf 'current'; return 0
  fi

  if ! newpath="$(termux_interp_path "$interp")"; then
    printf 'unresolved:%s' "$interp"; return 0
  fi
  new="#!$newpath"
  if [[ "$first" == "$new" ]]; then
    printf 'current'; return 0
  fi

  local dir tmp was_x=0
  dir="$(dirname "$file")"
  if ! tmp="$(mktemp "$dir/.bale-shebang.XXXXXX")"; then
    printf 'error-mktemp'; return 1
  fi
  if ! { printf '%s\n' "$new"; tail -n +2 "$file"; } > "$tmp"; then
    rm -f "$tmp"; printf 'error-write'; return 1
  fi
  if [[ -x "$file" ]]; then was_x=1; fi
  if ! mv "$tmp" "$file"; then
    rm -f "$tmp"; printf 'error-mv'; return 1
  fi
  if [[ "$was_x" == "1" ]]; then chmod +x "$file"; fi

  printf 'rewritten:%s -> %s' "$first" "$new"
  return 0
}

# --- Source guard ----------------------------------------------------------
# When sourced (BASH_SOURCE differs from $0), stop here: the caller wants the
# functions above, not a live install. When executed directly, fall through.
if [[ "${BASH_SOURCE[0]}" != "${0}" ]]; then
  return 0 2>/dev/null || true
fi

# ===========================================================================
# Install flow (runs only on direct execution)
# ===========================================================================

# This script's directory IS the bale install root.
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
BALE="$INSTALL_DIR/bin/bale"
SYMLINK_TARGET="$HOME/.local/bin/bale"

YES=0
DO_SYMLINK=1
DO_VALIDATE=1
DO_TERMUX_SHEBANG=1

# Outcomes captured as the script runs, reported in the closing summary so the
# key facts land last (rather than scattered through the step log above).
SYMLINK_STATUS="(unknown)"
VALIDATE_STATUS="(unknown)"
SHEBANG_STATUS="(unknown)"

for arg in "$@"; do
  case "$arg" in
    -y|--yes)             YES=1 ;;
    --no-symlink)         DO_SYMLINK=0 ;;
    --no-validate)        DO_VALIDATE=0 ;;
    --no-termux-shebang)  DO_TERMUX_SHEBANG=0 ;;
    -h|--help)            sed -n '2,21p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) printf '[install] error: unknown flag: %s\n' "$arg" >&2; exit 1 ;;
  esac
done

log "install dir: $INSTALL_DIR"

# Verify expected layout. Catches a partial/corrupt extract before we do
# anything. user/ is intentionally NOT in this list — it's user-owned and
# absent on a fresh install; we report its state below but don't fail.
#
# INSTALL_LAYOUT is a LITERAL copy of scripts/build.sh's RELEASE_FILES —
# literal because build.sh is not a release file and does not exist at
# install time. build.sh's list-agreement pre-flight asserts the two are
# exactly equal on every release build, so drift here is a failed build,
# not a broken install. Format contract (build.sh extracts this block
# mechanically): "INSTALL_LAYOUT=(" at column 0, one bare path per line,
# ")" at column 0.
INSTALL_LAYOUT=(
  bin/bale
  bin/bale_config.py
  bin/bale_validate.py
  bin/bale_staging.py
  bin/bale_sandbox.py
  bin/bale_rollback.py
  bin/bale_report.py
  bin/bale_pack.py
  bin/bale_apply.py
  bin/bale_stats.py
  bin/_bale_toml.py
  docs/CLAUDE.md
  docs/TARBALL.md
  docs/DOCS.md
  docs/CODE.md
  schemas/request-manifest.schema.json
  schemas/response-manifest.schema.json
  schemas/diagnostics.schema.json
  schemas/telemetry-record.schema.json
  tools/response_lint.py
  tools/craft_response.py
  install.sh
  validate.sh
  upgrade.sh
  README.md
)
for f in "${INSTALL_LAYOUT[@]}"; do
  [[ -e "$INSTALL_DIR/$f" ]] || die "missing expected file: $INSTALL_DIR/$f"
done
log "layout OK (${#INSTALL_LAYOUT[@]} files)"

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

# Restore executable bits. Some filesystems (NTFS, FAT) drop them on
# extract. tools/response_lint.py and tools/craft_response.py are
# executable by contract — validate.sh asserts the bits, and pack refuses
# without a working lint.
chmod +x "$BALE" "$INSTALL_DIR/validate.sh" "$INSTALL_DIR/upgrade.sh" "$INSTALL_DIR/tools/response_lint.py" "$INSTALL_DIR/tools/craft_response.py"
log "ensured executable bits"

# Termux shebang rewrite (optional; only meaningful on Termux). Runs before the
# symlink and validate steps below so that validate.sh — which execs bin/bale —
# sees the rewritten interpreter and therefore passes without termux-exec.
if [[ "$DO_TERMUX_SHEBANG" == "1" ]] && is_termux; then
  log "Termux detected (prefix: $(termux_prefix))"
  if confirm "rewrite shebangs to the Termux interpreter so bale runs without termux-exec?"; then
    rewrote=0
    skipped=0
    # bin/bale and the two tools/ executables are the installed
    # executables; the three .sh are the shipped scripts. install.sh
    # rewrites its own shebang too — safe via the atomic rename in
    # rewrite_shebang (see that function's header).
    for f in "$BALE" "$INSTALL_DIR/install.sh" "$INSTALL_DIR/validate.sh" "$INSTALL_DIR/upgrade.sh" "$INSTALL_DIR/tools/response_lint.py" "$INSTALL_DIR/tools/craft_response.py"; do
      rel="${f#"$INSTALL_DIR"/}"
      # `|| true`: rewrite_shebang prints an error-* token AND returns non-zero
      # on a filesystem failure. Whether `set -e` aborts on a failed command
      # substitution in an assignment is bash-version-dependent, so guard it
      # explicitly — the token is still captured, and the error-* case below
      # turns it into a clean die() rather than a bare contextless exit.
      outcome="$(rewrite_shebang "$f")" || true
      case "$outcome" in
        rewritten:*)    log "  $rel: ${outcome#rewritten:}"; rewrote=$((rewrote + 1)) ;;
        current)        log "  $rel: already Termux-pointed; left as-is" ;;
        unresolved:*)   log "  $rel: interpreter '${outcome#unresolved:}' not found; left unchanged"; skipped=$((skipped + 1)) ;;
        not-shebang|no-interp)
                        log "  $rel: no rewritable shebang; left unchanged" ;;
        error-*)        die "shebang rewrite failed for $rel ($outcome)" ;;
        *)              die "shebang rewrite returned unexpected outcome for $rel: $outcome" ;;
      esac
    done
    if [[ "$skipped" -gt 0 ]]; then
      SHEBANG_STATUS="rewrote $rewrote, skipped $skipped (interpreter unresolved) -> $(termux_prefix)"
    else
      SHEBANG_STATUS="rewrote $rewrote file(s) -> $(termux_prefix)"
    fi
  else
    log "skipped Termux shebang rewrite (declined; re-run install.sh to apply, or use termux-exec)"
    SHEBANG_STATUS="skipped (declined)"
  fi
elif [[ "$DO_TERMUX_SHEBANG" == "0" ]]; then
  log "skipping Termux shebang step (--no-termux-shebang)"
  SHEBANG_STATUS="skipped (--no-termux-shebang)"
else
  # Not Termux — nothing to do, and no flag was needed to get here.
  SHEBANG_STATUS="not applicable (not Termux)"
fi

# Symlink onto PATH (optional).
if [[ "$DO_SYMLINK" == "1" ]]; then
  mkdir -p "$(dirname "$SYMLINK_TARGET")"
  if [[ -L "$SYMLINK_TARGET" ]]; then
    existing="$(readlink "$SYMLINK_TARGET")"
    if [[ "$existing" == "$BALE" ]]; then
      log "symlink already points to this install ($SYMLINK_TARGET); no change"
      SYMLINK_STATUS="already current ($SYMLINK_TARGET)"
    else
      log "symlink at $SYMLINK_TARGET currently points elsewhere: $existing"
      if confirm "repoint $SYMLINK_TARGET -> $BALE?"; then
        ln -sf "$BALE" "$SYMLINK_TARGET"
        log "repointed symlink"
        SYMLINK_STATUS="repointed to this install ($SYMLINK_TARGET)"
      else
        log "left existing symlink alone"
        SYMLINK_STATUS="left pointing elsewhere: $existing"
      fi
    fi
  elif [[ -e "$SYMLINK_TARGET" ]]; then
    # Not a symlink — a regular file or directory at that path. Don't clobber.
    die "$SYMLINK_TARGET exists and is not a symlink. Resolve manually before re-running."
  else
    if confirm "create symlink $SYMLINK_TARGET -> $BALE?"; then
      ln -s "$BALE" "$SYMLINK_TARGET"
      log "created symlink $SYMLINK_TARGET"
      SYMLINK_STATUS="created ($SYMLINK_TARGET)"
      case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *) log "note: $HOME/.local/bin is not on PATH. Add to your shell rc or invoke by full path." ;;
      esac
    else
      log "skipped symlink (re-run install.sh to add it later, or 'ln -s' by hand)"
      SYMLINK_STATUS="skipped (declined; re-run install.sh to add)"
    fi
  fi
else
  log "skipping symlink step (--no-symlink)"
  SYMLINK_STATUS="skipped (--no-symlink)"
fi

# Validate at the end. Under `set -e`, a non-zero validate.sh aborts the
# install here (before the summary) — so reaching the summary below means
# validation passed. We capture that outcome rather than re-deriving it.
if [[ "$DO_VALIDATE" == "1" ]]; then
  log "---"
  "$INSTALL_DIR/validate.sh"
  VALIDATE_STATUS="passed"
else
  log "skipping validate (--no-validate); run $INSTALL_DIR/validate.sh manually any time"
  VALIDATE_STATUS="skipped (--no-validate)"
fi

# Closing summary. The key facts land here, last, after the step log and
# validate.sh's own output above — so a user reading from the bottom sees
# what happened and what to do next without scrolling back through the steps.
# We don't try to run `bale config init` from here — it requires a git repo
# (the project the user wants to use bale on), and the install dir is not that.
log "---"
log "install complete"
log "  install dir: $INSTALL_DIR"
log "  layout:      verified"
log "  exec bits:   restored (bin/bale, validate.sh, upgrade.sh, tools/response_lint.py, tools/craft_response.py)"
log "  shebangs:    $SHEBANG_STATUS"
log "  symlink:     $SYMLINK_STATUS"
log "  validate:    $VALIDATE_STATUS"
log ""
log "next steps:"
log "  - cd to a project (git repo) you want to use bale with, then"
log "    run 'bale config init' to walk through per-repo setup."
log "  - optionally run 'bale config init --global' (from anywhere) to set"
log "    install-wide defaults that every project inherits per-key."
log "  (both walkthroughs are idempotent; re-run any time.)"
