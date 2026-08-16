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
FAILURES=()   # labels of failed checks, replayed in the closing summary

section() { printf '\n[validate] %s\n' "$*"; }
pass()    { printf '  [PASS] %s\n' "$1"; PASS=$((PASS + 1)); }
fail() {
  local msg="$1"
  [[ $# -gt 1 ]] && msg="$msg — $2"
  printf '  [FAIL] %s\n' "$msg"
  FAILURES+=("$msg")
  FAIL=$((FAIL + 1))
}

# Closing verdict block. Printed last — both on the early bin/bale-not-runnable
# exit and at the normal end — so the result and the list of any failures land
# at the bottom, instead of a bare count after dozens of [PASS] lines the user
# has to scroll back through to find what actually failed.
summary() {
  printf '\n[validate] ---\n'
  if [[ "$FAIL" -eq 0 ]]; then
    printf '[validate] result: OK — %s checks passed\n' "$PASS"
  else
    printf '[validate] result: FAILED — %s passed, %s failed\n' "$PASS" "$FAIL"
    printf '[validate] failed checks:\n'
    local f
    for f in "${FAILURES[@]}"; do
      printf '  - %s\n' "$f"
    done
  fi
}

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
[[ -f "$INSTALL_DIR/bin/VERSION" ]]             && pass "bin/VERSION present"    || fail "bin/VERSION present"
[[ -f "$INSTALL_DIR/bin/bale_config.py" ]]      && pass "bin/bale_config.py present" || fail "bin/bale_config.py present"
[[ -f "$INSTALL_DIR/bin/bale_validate.py" ]]    && pass "bin/bale_validate.py present" || fail "bin/bale_validate.py present"
[[ -f "$INSTALL_DIR/bin/bale_staging.py" ]]     && pass "bin/bale_staging.py present" || fail "bin/bale_staging.py present"
[[ -f "$INSTALL_DIR/bin/bale_rollback.py" ]]    && pass "bin/bale_rollback.py present" || fail "bin/bale_rollback.py present"
[[ -f "$INSTALL_DIR/bin/bale_report.py" ]]      && pass "bin/bale_report.py present" || fail "bin/bale_report.py present"
[[ -f "$INSTALL_DIR/bin/bale_pack.py" ]]        && pass "bin/bale_pack.py present" || fail "bin/bale_pack.py present"
[[ -f "$INSTALL_DIR/bin/bale_apply.py" ]]       && pass "bin/bale_apply.py present" || fail "bin/bale_apply.py present"
[[ -f "$INSTALL_DIR/bin/bale_stats.py" ]]       && pass "bin/bale_stats.py present" || fail "bin/bale_stats.py present"
[[ -f "$INSTALL_DIR/bin/_bale_toml.py" ]]       && pass "bin/_bale_toml.py present" || fail "bin/_bale_toml.py present"
[[ -f "$INSTALL_DIR/install.sh"  ]]             && pass "install.sh present"     || fail "install.sh present"
[[ -x "$INSTALL_DIR/validate.sh" ]]             && pass "validate.sh executable" || fail "validate.sh executable"
[[ -f "$INSTALL_DIR/upgrade.sh"  ]]             && pass "upgrade.sh present"     || fail "upgrade.sh present"
[[ -x "$INSTALL_DIR/upgrade.sh"  ]]             && pass "upgrade.sh executable"  || fail "upgrade.sh executable"
[[ -f "$INSTALL_DIR/README.md"   ]]             && pass "README.md present"      || fail "README.md present"
for d in CLAUDE TARBALL DOCS CODE PLANNER; do
  if [[ -f "$INSTALL_DIR/docs/$d.md" ]]; then pass "docs/$d.md present"; else fail "docs/$d.md present"; fi
done
for s in request-manifest response-manifest diagnostics; do
  schema="$INSTALL_DIR/schemas/$s.schema.json"
  if [[ -f "$schema" ]]; then
    pass "schemas/$s.schema.json present"
    # Parse-check via Python's stdlib json (always available, so free).
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

# tools/response_lint.py — the worker-side lint `bale pack` injects into
# every request beside the four globals (v0.3.8). Missing or non-executable
# means every pack hard-fails at main()'s sanity check, so catch it here.
if [[ -f "$INSTALL_DIR/tools/response_lint.py" ]]; then
  pass "tools/response_lint.py present"
  [[ -x "$INSTALL_DIR/tools/response_lint.py" ]] \
    && pass "tools/response_lint.py executable" \
    || fail "tools/response_lint.py executable"
  # Embedded-schema drift guard (v0.3.8, session B1): the lint embeds
  # verbatim copies of two schemas so it runs standalone on the worker
  # side. A session that edits a shipped schema must refresh the embedded
  # copy; this JSON-equality assertion is what makes forgetting that loud
  # instead of a silent drift where the worker lints against a stale
  # contract. Compared as parsed JSON (whitespace-insensitive), matching
  # the lint header's "JSON-equal to the source files" contract.
  for pair in "RESPONSE_MANIFEST_SCHEMA_JSON:response-manifest" \
              "DIAGNOSTICS_SCHEMA_JSON:diagnostics"; do
    const="${pair%%:*}"; s="${pair##*:}"
    if python3 -c "
import json, sys
sys.path.insert(0, '$INSTALL_DIR/tools')
import response_lint
embedded = json.loads(getattr(response_lint, '$const'))
shipped = json.load(open('$INSTALL_DIR/schemas/$s.schema.json'))
sys.exit(0 if embedded == shipped else 1)
" 2>/dev/null; then
      pass "lint embedded $s schema is JSON-equal to schemas/$s.schema.json"
    else
      fail "lint embedded $s schema is JSON-equal to schemas/$s.schema.json" \
           "refresh the embedded copy in tools/response_lint.py"
    fi
  done
else
  fail "tools/response_lint.py present" "pack injects it; every pack will refuse until it exists"
fi

# tools/craft_response.py — the worker-side crafter `bale pack` injects
# beside the lint (v1, session 007). Same present/executable rows as the
# lint; no embedded-schema drift guard, because the crafter deliberately
# embeds no schema (it scaffolds, the lint judges).
if [[ -f "$INSTALL_DIR/tools/craft_response.py" ]]; then
  pass "tools/craft_response.py present"
  [[ -x "$INSTALL_DIR/tools/craft_response.py" ]] \
    && pass "tools/craft_response.py executable" \
    || fail "tools/craft_response.py executable"
else
  fail "tools/craft_response.py present" "pack injects it into every request"
fi

section "user-owned layer (global config)"
# user/ is optional on a fresh install — absence is reported, not failed.
# Presence is reported; if a global bale.toml exists, syntax-check it.
if [[ -d "$INSTALL_DIR/user" ]]; then
  pass "user/ subtree present"
  if [[ -f "$INSTALL_DIR/user/bale.toml" ]]; then
    pass "global bale.toml present"
    # Syntax-check the global bale.toml the same way bale itself parses it:
    # through the in-tree `_bale_toml` shim (stdlib `tomllib` on 3.11+, a
    # vendored parser on 3.10), not stdlib `tomllib` directly. Using the shim
    # keeps this check working on 3.10 and exercises the exact code path
    # load_global_config uses. Treat parse failure as fatal — matches
    # load_global_config's contract.
    if python3 -c "import sys; sys.path.insert(0, '$INSTALL_DIR/bin'); import _bale_toml; _bale_toml.loads(open('$INSTALL_DIR/user/bale.toml').read())" 2>/dev/null; then
      pass "global bale.toml is valid TOML"
    else
      fail "global bale.toml is valid TOML" "_bale_toml could not parse it"
    fi
  else
    printf '  [SKIP] no global bale.toml (run "bale config init --global" to create one)\n'
  fi
else
  printf '  [SKIP] no user/ subtree (run "bale config init --global" to create one)\n'
fi

if [[ ! -x "$BALE" ]]; then
  printf '\n[validate] bin/bale not runnable; skipping remaining checks.\n'
  summary
  exit 1
fi

section "CLI surface"

# Read the canonical VERSION from bin/VERSION, the one-line version
# file bin/bale itself reads at startup (extracted from bin/bale's old
# VERSION constant in v0.4.5, board 10 S2, so version bumps stop
# colliding on bin/bale; scripts/build.sh reads the same file). Reading
# from the file (rather than from `bin/bale --version` output) keeps
# the check meaningful: if bin/bale's read of the file or argparse's
# `--version` wiring ever regresses against the declared version, the
# substring check below will catch it. `head -n 1` plus the whitespace
# trim is a defensive belt against a hand-edited trailing line or
# stray spacing; the first line is canonical.
EXPECTED_VERSION=$(head -n 1 "$INSTALL_DIR/bin/VERSION" 2>/dev/null | tr -d '[:space:]')
if [[ -n "$EXPECTED_VERSION" ]]; then
  pass "read VERSION from bin/VERSION ($EXPECTED_VERSION)"
  check_output "--version reports $EXPECTED_VERSION" "bale $EXPECTED_VERSION" "$BALE" --version
else
  fail "read VERSION from bin/VERSION" "file missing or empty — the canonical one-line version file since v0.4.5"
fi
check_output "--help mentions pack"     "pack"       "$BALE" --help
check_output "--help mentions apply"    "apply"      "$BALE" --help
check_output "--help mentions retry"    "retry"      "$BALE" --help
check_output "--help mentions revert"   "revert"     "$BALE" --help
check_output "--help mentions rollback" "rollback"   "$BALE" --help
check_output "--help mentions unlock"   "unlock"     "$BALE" --help
check_output "--help mentions handoff"  "handoff"    "$BALE" --help
check_output "--help mentions config"   "config"     "$BALE" --help

section "subcommand --help"
check_runs "pack --help"    "$BALE" pack    --help
check_runs "apply --help"   "$BALE" apply   --help
check_runs "retry --help"   "$BALE" retry   --help
check_runs "revert --help"  "$BALE" revert  --help
check_runs "rollback --help"  "$BALE" rollback --help
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

# rollback --help should surface its distinctive flags (--undo, --list,
# --stash, added in v0.2) so users discover the reverse / status / dirty-tree
# paths without reading the source. Same spirit as the handoff check above.
check_output "rollback --help mentions --undo"  "--undo"  "$BALE" rollback --help
check_output "rollback --help mentions --list"  "--list"  "$BALE" rollback --help
check_output "rollback --help mentions --stash" "--stash" "$BALE" rollback --help

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

# pack --help should surface the v0.3.8 provenance + no-readme surface:
# --no-readme (the deliberate no-prose acknowledgment the guard requires
# when piped), --packer, and --work-class (the provenance stamps). A
# missing flag string means the parser wiring regressed — the same
# contract as the --max-* checks above.
check_output "pack --help mentions --no-readme"  "--no-readme"  "$BALE" pack --help
check_output "pack --help mentions --packer"     "--packer"     "$BALE" pack --help
check_output "pack --help mentions --work-class" "--work-class" "$BALE" pack --help

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
    printf '  [SKIP] via symlink: --version (could not read VERSION from bin/VERSION)\n'
  fi
else
  printf '  [SKIP] no symlink at %s pointing at this install\n' "$SYM"
fi

summary
[[ "$FAIL" -eq 0 ]] || exit 1
