#!/usr/bin/env bash
# validate.sh — sanity-check the bale install this script ships with.
#
# Usage:
#   ~/bale/validate.sh
#
# Exits 0 if every check passes, 1 if any fails.

set -uo pipefail   # NOT -e: we record failures and keep going.

# This script's directory IS the bale install root.
INSTALL_DIR="$(cd "$(dirname "$0")" && pwd)"
BALE="$INSTALL_DIR/bin/bale"

PASS=0
FAIL=0

section() { printf '\n[validate] %s\n' "$*"; }
pass()    { printf '  [PASS] %s\n' "$1"; PASS=$((PASS + 1)); }
fail()    { printf '  [FAIL] %s'  "$1"; [[ $# -gt 1 ]] && printf ' — %s' "$2"; printf '\n'; FAIL=$((FAIL + 1)); }

check_runs() {
  local name="$1"; shift
  if "$@" >/dev/null 2>&1; then pass "$name"; else fail "$name" "exited non-zero"; fi
}

check_output() {
  local name="$1" expected="$2"; shift 2
  local got
  got=$("$@" 2>&1 || true)
  if [[ "$got" == *"$expected"* ]]; then
    pass "$name"
  else
    fail "$name" "expected substring '$expected' not in output"
  fi
}

check_exit() {
  local name="$1" expected="$2"; shift 2
  local got=0
  "$@" >/dev/null 2>&1 || got=$?
  if [[ "$got" == "$expected" ]]; then
    pass "$name"
  else
    fail "$name" "expected exit $expected, got $got"
  fi
}

section "install dir: $INSTALL_DIR"

section "filesystem layout"
[[ -f "$BALE" ]]                                && pass "bin/bale exists"        || fail "bin/bale exists"
[[ -x "$BALE" ]]                                && pass "bin/bale executable"    || fail "bin/bale executable"
[[ -f "$INSTALL_DIR/bin/bale_config.py" ]]      && pass "bin/bale_config.py present" || fail "bin/bale_config.py present"
[[ -f "$INSTALL_DIR/bin/bale_validate.py" ]]    && pass "bin/bale_validate.py present" || fail "bin/bale_validate.py present"
[[ -f "$INSTALL_DIR/install.sh"  ]]             && pass "install.sh present"     || fail "install.sh present"
[[ -x "$INSTALL_DIR/validate.sh" ]]             && pass "validate.sh executable" || fail "validate.sh executable"
[[ -f "$INSTALL_DIR/upgrade.sh"  ]]             && pass "upgrade.sh present"     || fail "upgrade.sh present"
[[ -x "$INSTALL_DIR/upgrade.sh"  ]]             && pass "upgrade.sh executable"  || fail "upgrade.sh executable"
[[ -f "$INSTALL_DIR/README.md"   ]]             && pass "README.md present"      || fail "README.md present"
for d in CLAUDE TARBALL DOCS CODE; do
  if [[ -f "$INSTALL_DIR/docs/$d.md" ]]; then pass "docs/$d.md present"; else fail "docs/$d.md present"; fi
done
for s in request-manifest response-manifest diagnostics; do
  schema="$INSTALL_DIR/schemas/$s.schema.json"
  if [[ -f "$schema" ]]; then
    pass "schemas/$s.schema.json present"
    # Parse-check via Python's stdlib json (bale requires 3.11+, so free).
    # A schema that doesn't parse is one bale can't load at pre-flight, which
    # would turn every pack/apply into a hard fail — catch it here instead.
    if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$schema" 2>/dev/null; then
      pass "schemas/$s.schema.json is valid JSON"
    else
      fail "schemas/$s.schema.json is valid JSON" "json could not parse it"
    fi
  else
    fail "schemas/$s.schema.json present"
  fi
done

section "user-owned layer (global config)"
# user/ is optional on a fresh install — absence is reported, not failed.
# Presence is reported; if a global bale.toml exists, syntax-check it.
if [[ -d "$INSTALL_DIR/user" ]]; then
  pass "user/ subtree present"
  if [[ -f "$INSTALL_DIR/user/bale.toml" ]]; then
    pass "global bale.toml present"
    # Syntax-check via Python's tomllib (stdlib in 3.11+; bale already
    # requires that, so this is a free dependency). Treat parse failure
    # as fatal — matches load_global_config's contract.
    if python3 -c "import tomllib, sys; tomllib.loads(open('$INSTALL_DIR/user/bale.toml').read())" 2>/dev/null; then
      pass "global bale.toml is valid TOML"
    else
      fail "global bale.toml is valid TOML" "tomllib could not parse it"
    fi
  else
    printf '  [SKIP] no global bale.toml (run "bale config init --global" to create one)\n'
  fi
else
  printf '  [SKIP] no user/ subtree (run "bale config init --global" to create one)\n'
fi

if [[ ! -x "$BALE" ]]; then
  printf '\n[validate] bin/bale not runnable; skipping remaining checks.\n'
  printf '[validate] summary: %s passed, %s failed\n' "$PASS" "$FAIL"
  exit 1
fi

section "CLI surface"

# Read the canonical VERSION from bin/bale so this script doesn't
# duplicate the version string. Matches the module-level
#   VERSION = "X.Y.Z"
# assignment near the top of bin/bale. Reading from the declaration
# (rather than from `bin/bale --version` output) keeps the check
# meaningful: if argparse's `--version` wiring ever regresses against
# the declared constant, the substring check below will catch it.
# `head -1` is a defensive belt in case future edits introduce a
# second matching line; the first top-level assignment is canonical.
EXPECTED_VERSION=$(sed -n 's/^VERSION = "\([^"]*\)".*/\1/p' "$BALE" | head -1)
if [[ -n "$EXPECTED_VERSION" ]]; then
  pass "read VERSION from bin/bale ($EXPECTED_VERSION)"
  check_output "--version reports $EXPECTED_VERSION" "bale $EXPECTED_VERSION" "$BALE" --version
else
  fail "read VERSION from bin/bale" "no top-level VERSION = \"...\" assignment found"
fi
check_output "--help mentions pack"     "pack"       "$BALE" --help
check_output "--help mentions apply"    "apply"      "$BALE" --help
check_output "--help mentions retry"    "retry"      "$BALE" --help
check_output "--help mentions revert"   "revert"     "$BALE" --help
check_output "--help mentions unlock"   "unlock"     "$BALE" --help
check_output "--help mentions handoff"  "handoff"    "$BALE" --help
check_output "--help mentions config"   "config"     "$BALE" --help

section "subcommand --help"
check_runs "pack --help"    "$BALE" pack    --help
check_runs "apply --help"   "$BALE" apply   --help
check_runs "retry --help"   "$BALE" retry   --help
check_runs "revert --help"  "$BALE" revert  --help
check_runs "unlock --help"  "$BALE" unlock  --help
check_runs "handoff --help" "$BALE" handoff --help
check_runs "config --help"  "$BALE" config  --help
check_runs "config init --help" "$BALE" config init --help

# apply --help should surface the new default so users see where staging
# lands without having to read the source.
check_output "apply --help mentions .bale/staging" ".bale/staging" "$BALE" apply --help

# retry --help should surface the same default for the same reason —
# retry takes --staging-dir with the identical default, and a user
# discovering retry shouldn't have to read the source to know that.
check_output "retry --help mentions .bale/staging" ".bale/staging" "$BALE" retry --help

# apply and retry --help should mention apply.search_paths so users see
# how relative tarball names get resolved before reading the source.
check_output "apply --help mentions search_paths"  "search_paths" "$BALE" apply --help
check_output "retry --help mentions search_paths"  "search_paths" "$BALE" retry --help

# handoff --help should mention --edit-goal (its distinctive flag, added in
# v0.0.7) so users discover the inherited-goal edit path without reading the
# source. Parallels the per-subcommand spot-checks for apply/retry above.
check_output "handoff --help mentions --edit-goal" "--edit-goal" "$BALE" handoff --help

# config init's help should mention idempotency since that's the
# user-facing contract — re-running is safe.
check_output "config init --help mentions Idempotent" "Idempotent" "$BALE" config init --help

# config init --help should also surface the --global option so users
# discover the install-wide layer without reading the source. Mention
# "<install>/user" path so the location is concrete in the help text.
check_output "config init --help mentions --global" "--global" "$BALE" config init --help
check_output "config init --help mentions install/user path" "<install>/user" "$BALE" config init --help

# pack --help should surface the threshold-cap flags and --force introduced
# in 0.0.3. The check is that the literal flag string appears — argparse
# generates the usage line and the long-option entry, so a missing flag
# means the parser wiring regressed.
check_output "pack --help mentions --max-files" "--max-files" "$BALE" pack --help
check_output "pack --help mentions --max-size"  "--max-size"  "$BALE" pack --help
check_output "pack --help mentions --max-depth" "--max-depth" "$BALE" pack --help
check_output "pack --help mentions --force"     "--force"     "$BALE" pack --help

# pack --help should also surface --no-edit (added in 0.0.9 alongside the
# §7.3 wizard) so users discover the README-step opt-out without reading
# the source. Parallels the per-subcommand spot-check for handoff
# --edit-goal above.
check_output "pack --help mentions --no-edit"   "--no-edit"   "$BALE" pack --help

# unlock --help should mention --force (the only flag it takes; if the
# parser wiring regressed and --force went missing, callers stuck in the
# held-with-branch state would have no documented way out).
check_output "unlock --help mentions --force"   "--force"     "$BALE" unlock --help

# upgrade.sh must be runnable and self-document via --help.
check_runs "upgrade.sh --help" "$INSTALL_DIR/upgrade.sh" --help
check_output "upgrade.sh --help mentions user/" "user/" "$INSTALL_DIR/upgrade.sh" --help

# If a symlink at ~/.local/bin/bale points at this install, verify it works.
section "symlink resolution (if applicable)"
SYM="$HOME/.local/bin/bale"
if [[ -L "$SYM" && "$(readlink "$SYM")" == "$BALE" ]]; then
  if [[ -n "$EXPECTED_VERSION" ]]; then
    check_output "via symlink: --version" "bale $EXPECTED_VERSION" "$SYM" --version
  else
    printf '  [SKIP] via symlink: --version (could not read VERSION from bin/bale)\n'
  fi
else
  printf '  [SKIP] no symlink at %s pointing at this install\n' "$SYM"
fi

printf '\n[validate] summary: %s passed, %s failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]] || exit 1
