#!/usr/bin/env bash
# Blind checkpoint — board 49b (crafter-side bundle emission)
# Authored at the 2026-08-24-continue-plan-008 desk, from the request,
# before implementation. v1 (derived from the 49a v1 skeleton).
#
# Contract: runs in staging (cwd = staging root) beside validation.sh;
# [PASS]/[FAIL]/[SKIP <reason>] per probe; exit 0 all-pass, 1 any-fail,
# 2 script error. Outcome-only probes by design: bundle-format internals,
# emitter mechanics, input contract, and rider disposition are
# deliberately unprobed — they are spec in the brief, and pinning them
# would bind mechanism. Dry-run at the desk against base: all 3 FAIL.
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

# P1 — the emission surface exists and is discoverable: the crafter's
# --help resolves (exit 0) and names bundles. Derived from v1's P1
# verb-exists shape; flag surface and wording are the worker's — only
# exit 0 and the word are pinned.
if out=$(python3 tools/craft_response.py --help 2>&1) \
   && printf '%s' "$out" | tr -s '[:space:]' ' ' | grep -qi "bundle"; then
  pass "P1 crafter-emission-surface-exists (--help exit 0, names bundles)"
else
  fail "P1 crafter-emission-surface-exists: --help nonzero or no bundle mention: $(printf '%s' "$out" | head -c 200)"
fi

# P2 — the BALE.md §6.7 true-up landed: the does-not-exist-yet sentence
# about the crafter-side emission is gone. Whitespace-normalized (the
# sentence hard-wraps in the file); pinned on absence of preserved
# stale text — the replacement wording is the worker's.
if [ -f "BALE.md" ] && ! norm "BALE.md" | grep -q "is 49b and does not exist yet"; then
  pass "P2 bale-md-emission-sentence-trued-up"
else
  fail "P2 bale-md-emission-sentence-trued-up: stale does-not-exist-yet sentence still present (or BALE.md missing)"
fi

# P3 — the constant-duplication drift guard landed in validate.sh: the
# guard must name at least one of the duplicated identities. Generous
# recognizer (three spellings accepted); mechanism is the worker's.
# Base-discrimination note: validate.sh already says craft_response and
# bundle-manifest, so neither is pinned; all three tokens below are
# absent at base.
if [ -f "validate.sh" ] \
   && grep -Eq 'BUNDLE_SUFFIX|INTENT_PROMPTS|\.bale-bundle' validate.sh; then
  pass "P3 crafter-constant-drift-guard-in-validate-sh"
else
  fail "P3 crafter-constant-drift-guard-in-validate-sh: no duplicated-constant reference in validate.sh"
fi

if [ "$FAILS" -gt 0 ]; then
  p "checkpoint: $FAILS probe(s) failed"
  exit 1
fi
p "checkpoint: all probes passed"
exit 0
