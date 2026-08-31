#!/usr/bin/env bash
# Blind checkpoint — sitting-decisions-foldin
# Authored at the 2026-08-31 desk, from the request, before any
# implementation exists. Outcome contracts only: asserts that the
# sitting's decision inventory landed in claude/MASTER.md. Pins are
# exactly the strings the brief marks VERBATIM; all other phrasing
# is the worker's and is not graded. Read-only; writes nothing.
# Runs in staging with cwd at the staged repo root.
set -u

DOC="claude/MASTER.md"
fails=0

check() {
  # check <label> <fixed-string>
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

# Scenario 1 — the section-5 ratification kernel, verbatim.
check "ratification kernel present" \
  "Global docs reference no project-specific material — including bale-src's own."

# Scenario 2 — the five board-row titles, verbatim.
check "board row: purge"        "Global-doc purge"
check "board row: doctrine"     "PLANNER.md doctrine additions"
check "board row: provenance"   "Provenance stamped at open"
check "board row: release grp"  "Release-surface include group"
check "board row: linkage"      "Linkage rollup"
check "board row: schema purge" "Install-surface schema purge"

# Scenario 3 — the ruling-queue item title, verbatim.
check "ruling-queue item"       "Bailout-vs-compaction calibration"

# Scenario 4 — the two watch-entry phrase pins, verbatim.
check "watch: predicted basis"  "predicted-basis claims"
check "watch: hold rate"        "contract-doc HOLD rate"

if [ "$fails" -eq 0 ]; then
  echo "[CHECKPOINT PASS] all pinned landings present in $DOC"
  exit 0
else
  echo "[CHECKPOINT HOLD] $fails pinned landing(s) absent"
  exit 1
fi
