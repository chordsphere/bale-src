#!/usr/bin/env bash
# blind checkpoint — board-53-amend-checkpoint, v1
# Contract: TARBALL.md 7.5 — exit 0 all pass, exit 1 any fail.
# Outcome-only probes, run from the tree root. Authored blind from the
# request at the 2026-08-26 continue-plan sitting, before implementation.
set -u
fails=0

# P1 verb-surface: the amend-checkpoint verb is registered on bale's CLI.
out=$(python3 bin/bale --help 2>&1)
if [ $? -eq 0 ] && printf '%s' "$out" | grep -qF 'amend-checkpoint'; then
  echo "[PASS] P1 verb-surface: bale --help lists amend-checkpoint"
else
  echo "[FAIL] P1 verb-surface: bale --help does not list amend-checkpoint"
  fails=$((fails+1))
fi

# P2 docs: BALE.md documents the verb.
if [ -f BALE.md ] && grep -qF 'amend-checkpoint' BALE.md; then
  echo "[PASS] P2 docs: BALE.md mentions amend-checkpoint"
else
  echo "[FAIL] P2 docs: BALE.md carries no amend-checkpoint documentation"
  fails=$((fails+1))
fi

# P3 version: a new user-facing verb owes a bump — VERSION off the 0.4.16 base.
v=$(tr -d '[:space:]' < bin/VERSION 2>/dev/null || echo "")
if [ -n "$v" ] && [ "$v" != "0.4.16" ]; then
  echo "[PASS] P3 version: bin/VERSION ($v) moved off the 0.4.16 base"
else
  echo "[FAIL] P3 version: bin/VERSION still 0.4.16 (or unreadable)"
  fails=$((fails+1))
fi

[ "$fails" -gt 0 ] && exit 1
exit 0
