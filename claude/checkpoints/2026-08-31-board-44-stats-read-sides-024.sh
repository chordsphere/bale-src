#!/usr/bin/env bash
# Blind checkpoint — board-44-stats-read-sides (rev1). Authored blind
# at the 2026-08-31-continue-plan-012 sitting. Outcomes only.
# cwd = staged tree. Exit: 0 pass, 1 probe failed, 2 script errored.
set -u
fails=0
for f in bin/bale_stats.py BALE.md; do
  [ -f "$f" ] || { echo "[CKPT ERROR] $f missing"; exit 2; }
done
if grep -qF '"opened"' bin/bale_stats.py; then echo "[CKPT PASS] opened-vocabulary"; else echo "[CKPT FAIL] opened-vocabulary"; fails=$((fails+1)); fi
if grep -qF "Outcome rates cut per contract-doc-hash epoch make doc changes A/B-able; the epoch read is an intended use, not a side effect." BALE.md; then echo "[CKPT PASS] epoch-docs-kernel"; else echo "[CKPT FAIL] epoch-docs-kernel"; fails=$((fails+1)); fi
if python3 bin/bale stats --help >/dev/null 2>&1; then echo "[CKPT PASS] stats-cli-alive"; else echo "[CKPT FAIL] stats-cli-alive"; fails=$((fails+1)); fi
[ "$fails" -gt 0 ] && { echo "[CKPT] $fails probe(s) failed"; exit 1; }
echo "[CKPT] all probes passed"; exit 0
