#!/usr/bin/env bash
# Blind checkpoint — tarball-reemit-mention (rev1). Authored blind at
# the 2026-08-31-continue-plan-012 sitting. Outcomes only.
# cwd = staged tree. Exit: 0 pass, 1 probe failed, 2 script errored.
set -u
F="docs/TARBALL.md"; fails=0
[ -f "$F" ] || { echo "[CKPT ERROR] $F missing"; exit 2; }
n=$(grep -o "re-emit" "$F" | wc -l)
if [ "$n" -ge 2 ]; then
  echo "[CKPT PASS] reemit-documented-both-sections ($n occurrences)"
else
  echo "[CKPT FAIL] reemit-documented-both-sections ($n occurrences)"
  fails=$((fails+1))
fi
[ "$fails" -gt 0 ] && { echo "[CKPT] $fails probe(s) failed"; exit 1; }
echo "[CKPT] all probes passed"; exit 0
