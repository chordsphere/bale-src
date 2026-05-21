#!/usr/bin/env bash
# scripts/build.sh — package this bale-src checkout into a release tarball.
#
# Produces dist/bale-vX.Y.Z.tar.gz with the install layout described in
# BALE.md §3.1 (and documented for users in README.md). After build:
#
#   tar -xzf dist/bale-vX.Y.Z.tar.gz -C ~/   # extracts to ~/bale/
#   ~/bale/install.sh                        # finalize the install
#
# The release tarball contains only the install layout. bale-src's
# source-only extras (BALE.md, bale.toml, scripts/, claude/) are
# excluded — see BALE.md §13 v0.0.1 for why.
#
# Usage:
#   scripts/build.sh                       # build with version from bin/bale
#   scripts/build.sh -o, --output OUTDIR   # output directory (default: dist/)
#   scripts/build.sh --version X.Y.Z       # override version (snapshots, tests)
#   scripts/build.sh --skip-verify         # skip the post-build verification
#   scripts/build.sh -h, --help            # this help

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

OUTPUT_DIR="$REPO_ROOT/dist"
VERSION_OVERRIDE=""
DO_VERIFY=1

while [[ $# -gt 0 ]]; do
  case "$1" in
    -o|--output)
      [[ $# -ge 2 ]] || { printf '[build] error: %s needs a value\n' "$1" >&2; exit 2; }
      OUTPUT_DIR="$2"; shift 2 ;;
    --version)
      [[ $# -ge 2 ]] || { printf '[build] error: --version needs a value\n' >&2; exit 2; }
      VERSION_OVERRIDE="$2"; shift 2 ;;
    --skip-verify)
      DO_VERIFY=0; shift ;;
    -h|--help)
      sed -n '2,/^$/p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *)
      printf '[build] error: unknown argument: %s\n' "$1" >&2
      printf '[build] usage: scripts/build.sh [-o OUTDIR] [--version X.Y.Z] [--skip-verify]\n' >&2
      exit 2 ;;
  esac
done

log() { printf '[build] %s\n' "$*"; }
die() { printf '[build] error: %s\n' "$*" >&2; exit 1; }

# The 10 files the release tarball contains (BALE.md §3.1, mirrored in
# scripts/reinstall.sh's source-layout sanity check and in install.sh's
# layout verifier). When these three lists drift apart it's always a
# bug — one of them is wrong about what the release actually contains.
RELEASE_FILES=(
  bin/bale
  bin/bale_config.py
  docs/CLAUDE.md
  docs/TARBALL.md
  docs/DOCS.md
  docs/CODE.md
  install.sh
  validate.sh
  upgrade.sh
  README.md
)

# Files that should be executable in the extracted release. install.sh
# re-chmods on extract, but arriving-already-executable is friendlier to
# users who skip install.sh (inspecting a release, running in place).
EXECUTABLES=(
  bin/bale
  install.sh
  validate.sh
  upgrade.sh
)

log "source: $REPO_ROOT"

# Pre-flight: every release file exists in the source. Catches a broken
# checkout before we waste time staging.
for f in "${RELEASE_FILES[@]}"; do
  [[ -f "$REPO_ROOT/$f" ]] || die "missing source file: $f"
done
log "source layout OK (${#RELEASE_FILES[@]} files)"

# Resolve version. The canonical source is bin/bale's top-level
# VERSION = "X.Y.Z" assignment. The sed pattern matches the one in
# validate.sh's "CLI surface" section so the two read the same line —
# a regression in either is caught by the other on the next install.
if [[ -n "$VERSION_OVERRIDE" ]]; then
  VERSION="$VERSION_OVERRIDE"
  log "version: $VERSION (override)"
else
  VERSION=$(sed -n 's/^VERSION = "\([^"]*\)".*/\1/p' "$REPO_ROOT/bin/bale" | head -1)
  [[ -n "$VERSION" ]] || die "could not read VERSION from bin/bale (no top-level VERSION = \"...\" assignment)"
  log "version: $VERSION (from bin/bale)"
fi

# Cheap pre-flight syntax checks. We'd rather fail before tarring than
# ship a release whose first sign of trouble is a user's install.sh.
log "syntax check: python files"
python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$REPO_ROOT/bin/bale" \
  || die "bin/bale failed Python syntax check"
python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$REPO_ROOT/bin/bale_config.py" \
  || die "bin/bale_config.py failed Python syntax check"
log "syntax check: shell scripts"
bash -n "$REPO_ROOT/install.sh"  || die "install.sh failed bash syntax check"
bash -n "$REPO_ROOT/validate.sh" || die "validate.sh failed bash syntax check"
bash -n "$REPO_ROOT/upgrade.sh"  || die "upgrade.sh failed bash syntax check"

# Stage to a tmpdir. The tarball's top-level directory is `bale/`:
# README.md's install command is `tar -xzf bale-vX.Y.Z.tar.gz -C ~/`
# followed by `~/bale/install.sh`, so the top-level MUST be `bale/` for
# the documented flow to work. Versioning the directory (bale-vX.Y.Z/)
# would break that command without a separate rename step.
STAGING="$(mktemp -d "${TMPDIR:-/tmp}/bale-build.XXXXXX")"
trap 'rm -rf "$STAGING"' EXIT
STAGE_ROOT="$STAGING/bale"
mkdir -p "$STAGE_ROOT"

for f in "${RELEASE_FILES[@]}"; do
  mkdir -p "$STAGE_ROOT/$(dirname "$f")"
  cp "$REPO_ROOT/$f" "$STAGE_ROOT/$f"
done

for f in "${EXECUTABLES[@]}"; do
  chmod +x "$STAGE_ROOT/$f"
done
log "staged: $STAGE_ROOT"

mkdir -p "$OUTPUT_DIR"
TARBALL="$OUTPUT_DIR/bale-v$VERSION.tar.gz"
[[ -e "$TARBALL" ]] && log "overwriting existing tarball at $TARBALL"

tar -czf "$TARBALL" -C "$STAGING" bale
log "wrote: $TARBALL"

# Verification. Inspect the just-built tarball end-to-end: every release
# file is present, no extras snuck in. Skip with --skip-verify when the
# caller wants a faster build (e.g., scripted snapshot loops).
if [[ "$DO_VERIFY" == "1" ]]; then
  log "verifying tarball contents"
  CONTENTS=$(tar -tzf "$TARBALL")

  for f in "${RELEASE_FILES[@]}"; do
    if ! grep -qE "^bale/${f}\$" <<< "$CONTENTS"; then
      die "verify failed: bale/$f not found in tarball"
    fi
  done

  # File-entry count (tar -tzf prints directory entries with trailing
  # slashes; file entries don't). Strict equality catches stray includes.
  ACTUAL_FILES=$(grep -cE '[^/]$' <<< "$CONTENTS" || true)
  if [[ "$ACTUAL_FILES" != "${#RELEASE_FILES[@]}" ]]; then
    die "verify failed: expected ${#RELEASE_FILES[@]} file entries, found $ACTUAL_FILES"
  fi
  log "verify OK: ${#RELEASE_FILES[@]} files match the release layout"
fi

# Summary. Portable sha256: prefer GNU sha256sum (Linux), fall back to
# BSD shasum -a 256 (macOS). If neither is on PATH the rest of the build
# still succeeded — the hash is informational, not gating.
if   command -v sha256sum >/dev/null 2>&1; then
  SHA256=$(sha256sum "$TARBALL" | awk '{print $1}')
elif command -v shasum    >/dev/null 2>&1; then
  SHA256=$(shasum -a 256 "$TARBALL" | awk '{print $1}')
else
  SHA256=""
fi
SIZE=$(wc -c < "$TARBALL" | tr -d ' ')

log "---"
log "release: bale-v$VERSION"
log "path:    $TARBALL"
log "size:    $SIZE bytes"
log "sha256:  ${SHA256:-(unavailable: install sha256sum or shasum)}"
log "install: tar -xzf $(basename "$TARBALL") -C ~/  &&  ~/bale/install.sh"
