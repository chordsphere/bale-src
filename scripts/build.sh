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

# The files the release tarball contains (BALE.md §3.1) — the CANONICAL
# release list. The other places that need this layout no longer keep
# free-floating copies:
#   - scripts/reinstall.sh derives its source-layout sanity list from
#     this array at run time (awk extraction; it dies loudly if the
#     format contract below is broken or extraction comes back empty).
#   - install.sh's INSTALL_LAYOUT stays a literal copy — build.sh does
#     not exist at install time — and the list-agreement pre-flight
#     below asserts it is exactly equal to this array on every build.
#   - upgrade.sh's REQUIRED_RELEASE_MEMBERS is a deliberate subset (a
#     pre-wipe spot check, not a full layout check); the pre-flight
#     below asserts the subset relation holds.
#   - validate.sh's filesystem-layout rows remain hand-maintained for
#     now (deliberately deferred: drift there yields a missing check,
#     never a broken install).
# The tree-coverage pre-flight below closes the gap none of those
# list-vs-list checks can see: a file on disk under bin/ docs/ schemas/
# tools/ that never made it into ANY list.
#
# History: omissions here are fatal, not cosmetic. This list has drifted
# twice — once missing three bin/ helper modules and all of schemas/
# (bin/bale hard-imports the helpers at module load and resolves
# schemas/ at runtime), and once missing bin/bale_report.py,
# tools/response_lint.py, and schemas/telemetry-record.schema.json
# (load-time import, pack's hard requirement, and apply's telemetry
# schema respectively). The derivations and assertions above exist so a
# third drift is a failed build, not a dead-on-arrival release.
#
# Format contract (extraction depends on it): the array opens with
# "RELEASE_FILES=(" at column 0, holds one bare path per line (no
# quoting, no globs, no inline elements), and closes with ")" at
# column 0. Trailing comments on element lines are tolerated.
#
# No file count is hardcoded in this comment on purpose: a literal count
# is just one more thing to drift. The verifier below derives it from the
# array (${#RELEASE_FILES[@]}), so the array is the single source.
RELEASE_FILES=(
  bin/bale
  bin/bale_config.py
  bin/bale_validate.py
  bin/bale_staging.py
  bin/bale_rollback.py
  bin/bale_report.py
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
  tools/response_lint.py
)

# Extract a bash array's elements from a file, one per line, per the
# format contract documented above RELEASE_FILES: '<NAME>=(' at column 0,
# one bare path per line, ')' at column 0. Trailing comments and blank
# lines inside the block are tolerated. Exits non-zero when the block is
# missing or unterminated; callers die on that and on empty output.
#   usage: extract_bash_array FILE NAME
extract_bash_array() {
  awk -v name="$2" '
    !inblock && $0 == name "=(" { inblock = 1; next }
    inblock && $0 == ")"        { found = 1; exit }
    inblock {
      sub(/#.*$/, "")
      gsub(/^[ \t]+|[ \t]+$/, "")
      if ($0 != "") print
    }
    END { exit found ? 0 : 1 }
  ' "$1"
}

# Die if stdin (one path per line) contains anything but plain relative
# paths — the tell of a changed array format leaking through extraction.
#   usage: printf '%s\n' "$list" | require_plain_paths LABEL
require_plain_paths() {
  local label="$1" line
  while IFS= read -r line; do
    case "$line" in
      ""|*[!A-Za-z0-9._/-]*)
        die "$label: unexpected entry '$line' — array format changed? (format contract above RELEASE_FILES)" ;;
    esac
  done
}

log "source: $REPO_ROOT"

# Pre-flight: every release file exists in the source. Catches a broken
# checkout before we waste time staging.
for f in "${RELEASE_FILES[@]}"; do
  [[ -f "$REPO_ROOT/$f" ]] || die "missing source file: $f"
done
log "source layout OK (${#RELEASE_FILES[@]} files)"

# Pre-flight: list agreement. RELEASE_FILES is canonical; the literal
# copies elsewhere are asserted against it here so drift is a failed
# build, not a broken release. (Rationale in the comment above
# RELEASE_FILES; reinstall.sh needs no assertion — it derives.)
log "pre-flight: list agreement"
RELEASE_SORTED="$(printf '%s\n' "${RELEASE_FILES[@]}" | sort)"

# install.sh's INSTALL_LAYOUT must be EXACTLY equal (as a set).
INSTALL_LIST="$(extract_bash_array "$REPO_ROOT/install.sh" INSTALL_LAYOUT)" \
  || die "could not extract INSTALL_LAYOUT from install.sh — array missing or format changed"
[[ -n "$INSTALL_LIST" ]] || die "INSTALL_LAYOUT extracted empty from install.sh — format changed?"
printf '%s\n' "$INSTALL_LIST" | require_plain_paths "install.sh INSTALL_LAYOUT"
INSTALL_SORTED="$(printf '%s\n' "$INSTALL_LIST" | sort)"
if [[ "$INSTALL_SORTED" != "$RELEASE_SORTED" ]]; then
  only_release="$(comm -23 <(printf '%s\n' "$RELEASE_SORTED") <(printf '%s\n' "$INSTALL_SORTED") | tr '\n' ' ')"
  only_install="$(comm -13 <(printf '%s\n' "$RELEASE_SORTED") <(printf '%s\n' "$INSTALL_SORTED") | tr '\n' ' ')"
  die "install.sh INSTALL_LAYOUT disagrees with RELEASE_FILES — missing from install.sh: [${only_release% }] | extra in install.sh: [${only_install% }]"
fi
log "  install.sh INSTALL_LAYOUT matches RELEASE_FILES"

# upgrade.sh's REQUIRED_RELEASE_MEMBERS is a deliberate subset.
UPGRADE_LIST="$(extract_bash_array "$REPO_ROOT/upgrade.sh" REQUIRED_RELEASE_MEMBERS)" \
  || die "could not extract REQUIRED_RELEASE_MEMBERS from upgrade.sh — array missing or format changed"
[[ -n "$UPGRADE_LIST" ]] || die "REQUIRED_RELEASE_MEMBERS extracted empty from upgrade.sh — format changed?"
printf '%s\n' "$UPGRADE_LIST" | require_plain_paths "upgrade.sh REQUIRED_RELEASE_MEMBERS"
not_in_release=""
while IFS= read -r m; do
  printf '%s\n' "$RELEASE_SORTED" | grep -qFx -- "$m" || not_in_release="$not_in_release $m"
done <<< "$UPGRADE_LIST"
[[ -z "$not_in_release" ]] \
  || die "upgrade.sh REQUIRED_RELEASE_MEMBERS is not a subset of RELEASE_FILES — not in RELEASE_FILES:$not_in_release"
log "  upgrade.sh REQUIRED_RELEASE_MEMBERS is a subset of RELEASE_FILES"

# Pre-flight: tree coverage. Every file on disk under the release-owned
# directories must appear in RELEASE_FILES. This is the check that
# catches "new file, in no list" — the drift class the list-vs-list
# assertions above cannot see. __pycache__/ and *.pyc are generated
# artifacts, pruned. reinstall.sh runs the same guard at apply time.
log "pre-flight: tree coverage (bin/ docs/ schemas/ tools/)"
uncovered=""
while IFS= read -r f; do
  rel="${f#"$REPO_ROOT"/}"
  printf '%s\n' "$RELEASE_SORTED" | grep -qFx -- "$rel" || uncovered="$uncovered $rel"
done < <(find "$REPO_ROOT/bin" "$REPO_ROOT/docs" "$REPO_ROOT/schemas" "$REPO_ROOT/tools" \
           -name __pycache__ -prune -o -name '*.pyc' -prune -o -type f -print | sort)
[[ -z "$uncovered" ]] \
  || die "tree coverage: file(s) on disk but in no release list:$uncovered — add to RELEASE_FILES (and install.sh's INSTALL_LAYOUT), or remove from the tree"
log "  every file under bin/ docs/ schemas/ tools/ is in RELEASE_FILES"

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
# Syntax-check every Python source the release ships: the bin/bale entry
# point (named explicitly — it has no .py extension) plus the helper
# modules it imports at load time, plus the tools/ Python the release
# carries (the worker lint: pack hard-fails without a working copy). The
# list is derived from RELEASE_FILES rather than re-typed, so a module
# added to the release above is checked here automatically — the exact
# drift the file list itself has suffered. bin/bale hard-imports every
# helper, so a syntax error in any one of them is a crash on first run;
# better to fail here than at a user's install.sh.
log "syntax check: python files"
PY_SOURCES=(bin/bale)
for f in "${RELEASE_FILES[@]}"; do
  [[ "$f" == bin/*.py || "$f" == tools/*.py ]] && PY_SOURCES+=("$f")
done
for py in "${PY_SOURCES[@]}"; do
  python3 -c "import ast,sys; ast.parse(open(sys.argv[1]).read())" "$REPO_ROOT/$py" \
    || die "$py failed Python syntax check"
done
log "syntax check: shell scripts"
bash -n "$REPO_ROOT/install.sh"  || die "install.sh failed bash syntax check"
bash -n "$REPO_ROOT/validate.sh" || die "validate.sh failed bash syntax check"
bash -n "$REPO_ROOT/upgrade.sh"  || die "upgrade.sh failed bash syntax check"
# Parse-check the JSON schemas the release ships, derived from RELEASE_FILES
# for the same anti-drift reason as the Python sources above. validate.sh
# runs this same stdlib json.load check at install time; doing it here too
# catches a malformed schema before tarring rather than at a user's
# validate.sh. A schema bale can't load turns every pack/apply into a hard
# fail, so the one extra parse per file is worth it.
log "syntax check: json schemas"
for f in "${RELEASE_FILES[@]}"; do
  [[ "$f" == schemas/*.json ]] || continue
  python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$REPO_ROOT/$f" \
    || die "$f failed JSON parse check"
done

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
log "build complete"
log "  release: bale-v$VERSION"
log "  path:    $TARBALL"
log "  size:    $SIZE bytes"
log "  sha256:  ${SHA256:-(unavailable: install sha256sum or shasum)}"
log "  install: tar -xzf $(basename "$TARBALL") -C ~/  &&  ~/bale/install.sh"
