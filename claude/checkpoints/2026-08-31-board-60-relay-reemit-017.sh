#!/usr/bin/env bash
# Blind checkpoint — board-60-relay-reemit (rev1).
# Authored at the 2026-08-31-continue-plan-012 sitting, from the
# request, before implementation. Outcome contracts only.
# Runs with cwd = the staged (applied) tree. Exit: 0 pass, 1 a probe
# failed, 2 this script itself errored.
set -u
ADR="claude/context/adr/0017-exchange-shape-independent-of-counterparty.md"
fails=0
for f in BALE.md "$ADR"; do
  if [ ! -f "$f" ]; then echo "[CKPT ERROR] expected file missing: $f"; exit 2; fi
done
probe_in() {
  local label="$1" file="$2" needle="$3"
  if grep -qF -- "$needle" "$file"; then echo "[CKPT PASS] $label";
  else echo "[CKPT FAIL] $label"; fails=$((fails + 1)); fi
}
# Outcome 1: the contract sentence landed verbatim in the relay docs.
probe_in "reemit-contract-kernel" "BALE.md" "With no file argument, bale relay re-emits the paste block for the thread's latest recorded round, byte-identical to the original emission, and records nothing."
# Outcome 2: the doctrine half landed verbatim in ADR-0017's Notes.
probe_in "adr-notes-kernel" "$ADR" "The option surface widens to sid-only: the no-file form re-emits the latest recorded round and records nothing."
# Outcome 3: the relay CLI surface is alive post-change.
if python3 bin/bale relay --help >/dev/null 2>&1; then
  echo "[CKPT PASS] relay-verb-alive"
else
  echo "[CKPT FAIL] relay-verb-alive"; fails=$((fails + 1))
fi
if [ "$fails" -gt 0 ]; then echo "[CKPT] $fails probe(s) failed"; exit 1; fi
echo "[CKPT] all probes passed"; exit 0
