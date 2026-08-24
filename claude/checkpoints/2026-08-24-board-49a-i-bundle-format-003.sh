#!/usr/bin/env bash
# Blind checkpoint — board 49a-i (planner bundle format, pack-side half)
# Re-derived at the 2026-08-24 master sitting from the 49a checkpoint v1
# (sha256 56d578…) for the ratified three-way seam's narrowed scope,
# per the scope-change re-derivation rule. v1 for this session.
#
# Contract: runs in staging (cwd = staging root) beside validation.sh;
# [PASS]/[FAIL]/[SKIP <reason>] per probe; exit 0 all-pass, 1 any-fail,
# 2 script error. Outcome-only probes by design: bundle manifest keys,
# the deny-list recognizer, and the pre-answered-intents API shape are
# deliberately unprobed — they are the worker's mechanism authority,
# and the decline-default invariant is already pinned by the existing
# supersession suite in the worker's own validation stream. The parent
# oracle's open-verb probes (P1, P2) and its consumed pairs-pin probe
# (P3) do not carry: the verb is 49a-ii's scope, and the rider was
# consumed before this session existed. Probes are date-agnostic; no
# sid patterns. Dry-run at the desk against base: all 3 FAIL.
set -u
FAILS=0
p() { printf '%s\n' "$1"; }
fail() { p "[FAIL] $1"; FAILS=$((FAILS+1)); }
pass() { p "[PASS] $1"; }

norm() { tr -s '[:space:]' ' ' < "$1"; }

# P1 — the format has a durable project-side spec: the term "planner
# bundle" (preserved spec vocabulary from the ratified row; the
# compound term, since BALE.md already uses bare "bundle" as an
# ordinary verb) appears, whitespace-normalized and case-insensitive,
# in one of the two expected doc homes. Placement between them and
# all surrounding wording are the worker's.
found=""
for f in BALE.md docs/TARBALL.md; do
  if [ -f "$f" ] && norm "$f" | grep -qi "planner bundle"; then
    found="$f"
    break
  fi
done
if [ -n "$found" ]; then
  pass "P1 planner-bundle-spec-documented (in $found)"
else
  fail "P1 planner-bundle-spec-documented: 'planner bundle' absent from BALE.md and docs/TARBALL.md"
fi

# P2 — the work landed pack-side, per the ratified seam: the bundle
# surface is visible in the pack module. Token-presence only; naming,
# structure, and the recognizer mechanism are unprobed.
if [ -f "bin/bale_pack.py" ] && grep -qi "bundle" bin/bale_pack.py; then
  pass "P2 bundle-surface-in-pack-module"
else
  fail "P2 bundle-surface-in-pack-module: no bundle surface in bin/bale_pack.py"
fi

# P3 — tests ship with the surface: the bundle work is exercised
# somewhere under tests/. File naming and suite shape are the
# worker's.
if [ -d "tests" ] && grep -rqi "bundle" tests/; then
  pass "P3 bundle-tests-ship"
else
  fail "P3 bundle-tests-ship: no bundle reference under tests/"
fi

if [ "$FAILS" -gt 0 ]; then
  p "checkpoint: $FAILS probe(s) failed"
  exit 1
fi
p "checkpoint: all probes passed"
exit 0
