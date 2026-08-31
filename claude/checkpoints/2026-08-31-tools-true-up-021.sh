#!/usr/bin/env bash
# Blind checkpoint — tools-true-up (rev1). Authored blind at the
# 2026-08-31-continue-plan-012 sitting. Outcomes only.
# cwd = staged tree. Exit: 0 pass, 1 probe failed, 2 script errored.
set -u
F="tools/craft_response.py"; fails=0
[ -f "$F" ] || { echo "[CKPT ERROR] $F missing"; exit 2; }
if grep -qF "bale_relay.py" "$F"; then echo "[CKPT PASS] citation-retargeted"; else echo "[CKPT FAIL] citation-retargeted"; fails=$((fails+1)); fi
if head -60 "$F" | grep -qi "index"; then echo "[CKPT PASS] index-header-present"; else echo "[CKPT FAIL] index-header-present"; fails=$((fails+1)); fi
if python3 -m py_compile "$F" 2>/dev/null; then echo "[CKPT PASS] compiles"; else echo "[CKPT FAIL] compiles"; fails=$((fails+1)); fi
[ "$fails" -gt 0 ] && { echo "[CKPT] $fails probe(s) failed"; exit 1; }
echo "[CKPT] all probes passed"; exit 0
