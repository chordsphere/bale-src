#!/usr/bin/env bash
# Blind checkpoint — sitting-close-deltas (2026-08-31)
# Authored at the desk, from the request, before implementation.
# Outcome contracts only: pins are exactly the strings the brief
# marks VERBATIM (each required contiguous on one line by the
# brief, so fixed-string grep is the honest probe). Placement,
# numbering, and all other phrasing are the worker's and are not
# graded. Read-only; runs in staging, cwd at the staged repo root.
set -u

DOC="claude/MASTER.md"
fails=0

check() {
  if grep -qF -- "$2" "$DOC"; then
    echo "[PASS] $1"
  else
    echo "[FAIL] $1 — pinned string absent: $2"
    fails=$((fails + 1))
  fi
}

if [ ! -f "$DOC" ]; then
  echo "[FAIL] $DOC missing from staged tree"
  exit 1
fi

# Scenario 1 — the two section-5 kernels, verbatim.
check "six-row ratification kernel" \
  "The fold-in's six-row superset reading is ratified; the brief's five-row header was the defect."
check "bin/-path sanction kernel" \
  "bin/ paths are sanctioned in injected surfaces — they resolve wherever the install exists."

# Scenario 2 — row 66's sweep-extension phrase.
check "row 66 sweep extension" "sitting-label shapes"

# Scenario 3 — the three ledger-specimen phrases.
check "specimen: stale count"    "stale-count brief defect"
check "specimen: citation count" "citation-count correction"
check "specimen: dual spelling"  "dual-spelling resolution"

if [ "$fails" -eq 0 ]; then
  echo "[CHECKPOINT PASS] all pinned landings present in $DOC"
  exit 0
else
  echo "[CHECKPOINT HOLD] $fails pinned landing(s) absent"
  exit 1
fi
