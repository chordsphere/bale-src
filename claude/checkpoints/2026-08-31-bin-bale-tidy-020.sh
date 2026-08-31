#!/usr/bin/env bash
# Blind checkpoint — bin-bale-tidy (rev1). Authored blind at the
# 2026-08-31-continue-plan-012 sitting. Outcomes only.
# cwd = staged tree. Exit: 0 pass, 1 probe failed, 2 script errored.
set -u
fails=0
[ -f bin/bale ] || { echo "[CKPT ERROR] bin/bale missing"; exit 2; }
if grep -qF 'command="handoff"' bin/bale; then echo "[CKPT PASS] handoff-honest-command"; else echo "[CKPT FAIL] handoff-honest-command"; fails=$((fails+1)); fi
if python3 bin/bale --help >/dev/null 2>&1; then echo "[CKPT PASS] cli-alive"; else echo "[CKPT FAIL] cli-alive"; fails=$((fails+1)); fi
[ "$fails" -gt 0 ] && { echo "[CKPT] $fails probe(s) failed"; exit 1; }
echo "[CKPT] all probes passed"; exit 0
