#!/usr/bin/env bash
# Blind checkpoint — sitting-close-deltas-3 (rev1). Authored blind at
# the 2026-08-31-continue-plan-012 sitting. Outcomes only.
# cwd = staged tree. Exit: 0 pass, 1 probe failed, 2 script errored.
set -u
T="claude/MASTER.md"; fails=0
[ -f "$T" ] || { echo "[CKPT ERROR] target missing: $T"; exit 2; }
probe() { if grep -qF -- "$2" "$T"; then echo "[CKPT PASS] $1"; else echo "[CKPT FAIL] $1"; fails=$((fails+1)); fi; }
# Fresh-authored or new-fact strings, chosen to avoid anything the
# prior closes could plausibly carry.
probe "amendment-record-kernel" "The tools-true-up oracle was amended rev1 to rev2 at the desk; the retry's stamp mismatch was accepted deliberately, and this sentence is its prose record."
probe "notes-practice-kernel" "A response carrying anything ratifiable writes notes.md, however short; the archive keeps only notes."
probe "row-44-admission-fact" "test_stats_drilldown.py"
probe "version-position-trueup" "VERSION 0.4.22"
[ "$fails" -gt 0 ] && { echo "[CKPT] $fails probe(s) failed"; exit 1; }
echo "[CKPT] all probes passed"; exit 0
