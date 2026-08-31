#!/usr/bin/env bash
# Blind checkpoint — board-58-exchange-constants-parity (rev1).
# Authored at the 2026-08-31-continue-plan-012 sitting, from the
# request, before implementation. Outcome contracts only.
# Runs with cwd = the staged (applied) tree. Exit: 0 pass, 1 a probe
# failed, 2 this script itself errored.
set -u
TARGET="validate.sh"
fails=0
if [ ! -f "$TARGET" ]; then echo "[CKPT ERROR] target missing: $TARGET"; exit 2; fi
probe() {
  local label="$1" needle="$2"
  if grep -qF -- "$needle" "$TARGET"; then echo "[CKPT PASS] $label";
  else echo "[CKPT FAIL] $label"; fails=$((fails + 1)); fi
}
# Outcome 1: the parity row exists and its label names its subject.
probe "parity-row-label" "exchange constants"
# Outcome 1 cont.: the row reaches the relay module (the constants' home).
probe "parity-reaches-relay-module" "bale_relay"
# Outcome 2: presence rows for the three unrowed modules.
probe "presence-row-bale-open" "bale_open.py"
probe "presence-row-bale-sandbox" "bale_sandbox.py"
probe "presence-row-bale-relay" "bale_relay.py"
if [ "$fails" -gt 0 ]; then echo "[CKPT] $fails probe(s) failed"; exit 1; fi
echo "[CKPT] all probes passed"; exit 0
