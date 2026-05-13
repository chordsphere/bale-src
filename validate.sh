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
[[ -f "$INSTALL_DIR/install.sh"  ]]             && pass "install.sh present"     || fail "install.sh present"
[[ -x "$INSTALL_DIR/validate.sh" ]]             && pass "validate.sh executable" || fail "validate.sh executable"
for d in CLAUDE TARBALL DOCS; do
  if [[ -f "$INSTALL_DIR/docs/$d.md" ]]; then pass "docs/$d.md present"; else fail "docs/$d.md present"; fi
done

if [[ ! -x "$BALE" ]]; then
  printf '\n[validate] bin/bale not runnable; skipping remaining checks.\n'
  printf '[validate] summary: %s passed, %s failed\n' "$PASS" "$FAIL"
  exit 1
fi

section "CLI surface"
check_output "--version reports 0.0.1"  "bale 0.0.1" "$BALE" --version
check_output "--help mentions pack"     "pack"       "$BALE" --help
check_output "--help mentions apply"    "apply"      "$BALE" --help
check_output "--help mentions retry"    "retry"      "$BALE" --help
check_output "--help mentions revert"   "revert"     "$BALE" --help
check_output "--help mentions config"   "config"     "$BALE" --help

section "subcommand --help"
check_runs "pack --help"   "$BALE" pack   --help
check_runs "apply --help"  "$BALE" apply  --help
check_runs "retry --help"  "$BALE" retry  --help
check_runs "revert --help" "$BALE" revert --help
check_runs "config --help" "$BALE" config --help
check_runs "config init --help" "$BALE" config init --help

# apply --help should surface the new default so users see where staging
# lands without having to read the source.
check_output "apply --help mentions .bale/staging" ".bale/staging" "$BALE" apply --help

# retry --help should surface the same default for the same reason —
# retry takes --staging-dir with the identical default, and a user
# discovering retry shouldn't have to read the source to know that.
check_output "retry --help mentions .bale/staging" ".bale/staging" "$BALE" retry --help

# config init's help should mention idempotency since that's the
# user-facing contract — re-running is safe.
check_output "config init --help mentions Idempotent" "Idempotent" "$BALE" config init --help

# If a symlink at ~/.local/bin/bale points at this install, verify it works.
section "symlink resolution (if applicable)"
SYM="$HOME/.local/bin/bale"
if [[ -L "$SYM" && "$(readlink "$SYM")" == "$BALE" ]]; then
  check_output "via symlink: --version" "bale 0.0.1" "$SYM" --version
else
  printf '  [SKIP] no symlink at %s pointing at this install\n' "$SYM"
fi

printf '\n[validate] summary: %s passed, %s failed\n' "$PASS" "$FAIL"
[[ "$FAIL" -eq 0 ]] || exit 1
