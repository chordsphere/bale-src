#!/usr/bin/env bash
# Blind checkpoint — board 49a (planner bundle + bale open, consumption half)
# Authored at the 2026-08-18-continue-plan-008 desk, from the request,
# before implementation. v1.
#
# Contract: runs in staging (cwd = staging root) beside validation.sh;
# [PASS]/[FAIL]/[SKIP <reason>] per probe; exit 0 all-pass, 1 any-fail,
# 2 script error. Outcome-only probes by design: bundle-format internals,
# hash mechanics, dry-run leg behavior, and decline-default handling are
# deliberately unprobed — they are spec in the brief, and pinning them
# would bind mechanism. Dry-run at the desk against base: all 4 FAIL.
set -u
FAILS=0
p() { printf '%s\n' "$1"; }
fail() { p "[FAIL] $1"; FAILS=$((FAILS+1)); }
pass() { p "[PASS] $1"; }

if ! command -v python3 >/dev/null 2>&1; then
  p "[SKIP] all probes: python3 not found"
  exit 0
fi

norm() { tr -s '[:space:]' ' ' < "$1"; }

# P1 — the open verb exists: `bale help open` resolves and exits 0.
if out=$(python3 bin/bale help open 2>&1); then
  pass "P1 bale-open-verb-exists (bale help open exit 0)"
else
  fail "P1 bale-open-verb-exists: bale help open exited nonzero: $(printf '%s' "$out" | head -c 200)"
fi

# P2 — a missing bundle refuses loudly as bale's own refusal (not an
# argparse unknown-command error), and the refusal names what was not
# found. Token chosen to appear nowhere else.
tok="nonexistent-bundle-49a-probe.tar.gz"
out=$(python3 bin/bale open "/tmp/$tok" 2>&1)
rc=$?
if [ "$rc" -ne 0 ] \
   && ! printf '%s' "$out" | grep -qi "invalid choice" \
   && printf '%s' "$out" | grep -q "$tok"; then
  pass "P2 missing-bundle-refuses-loudly (rc=$rc, names the path)"
else
  fail "P2 missing-bundle-refuses-loudly: rc=$rc, output: $(printf '%s' "$out" | head -c 200)"
fi

# P3 — the pairs-pin rider landed: the suite's enumeration-count pin is
# 5 and the fifth pair's PLANNER.md side is registered. Whitespace-
# normalized; the extract's wording is the worker's — only the count and
# the doc name are pinned.
tf="tests/test_sanctioned_pairs.py"
if [ -f "$tf" ] \
   && norm "$tf" | grep -q "len(PAIRS), 5" \
   && grep -q "PLANNER.md" "$tf"; then
  pass "P3 pairs-pin-bumped-to-5-with-planner-side"
else
  fail "P3 pairs-pin-bumped-to-5-with-planner-side: pin or PLANNER.md side absent in $tf"
fi

# P4 — the verb is documented project-side: BALE.md names bale open.
# Placement and wording are the worker's; naming the verb is invariant.
if [ -f "BALE.md" ] && norm "BALE.md" | grep -q "bale open"; then
  pass "P4 bale-open-documented-in-BALE.md"
else
  fail "P4 bale-open-documented-in-BALE.md: no 'bale open' in BALE.md"
fi

if [ "$FAILS" -gt 0 ]; then
  p "checkpoint: $FAILS probe(s) failed"
  exit 1
fi
p "checkpoint: all probes passed"
exit 0
