#!/usr/bin/env bash
# Blind checkpoint — sitting-close-deltas-2 (rev1). Authored blind at
# the 2026-08-31-continue-plan-012 sitting. Outcomes only.
# cwd = staged tree. Exit: 0 pass, 1 probe failed, 2 script errored.
set -u
T="claude/MASTER.md"; fails=0
[ -f "$T" ] || { echo "[CKPT ERROR] target missing: $T"; exit 2; }
probe() { if grep -qF -- "$2" "$T"; then echo "[CKPT PASS] $1"; else echo "[CKPT FAIL] $1"; fails=$((fails+1)); fi; }
probe "row-59-close" "2026-08-31-board-59-relay-extraction-014"
probe "row-66-close" "2026-08-31-board-66-schema-purge-015"
probe "row-58-close" "2026-08-31-board-58-exchange-constants-parity-016"
probe "row-60-close" "2026-08-31-board-60-relay-reemit-017"
probe "row-63-close" "2026-08-31-board-63-provenance-at-open-018"
probe "version-ladder-top" "0.4.22"
[ "$fails" -gt 0 ] && { echo "[CKPT] $fails probe(s) failed"; exit 1; }
echo "[CKPT] all probes passed"; exit 0
