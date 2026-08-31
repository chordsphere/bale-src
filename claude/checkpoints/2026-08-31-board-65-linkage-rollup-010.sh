#!/usr/bin/env bash
# board-65 blind checkpoint v1 — runs from repo root in staging.
# Outcome contracts only. Exit 0 PASS, 1 HOLD, 2 defective oracle.
set -u
fail=0
out="$(./bin/bale stats 2>/dev/null)"; rc=$?
if [ "$rc" -ne 0 ]; then
  echo "[P1-linkage-surfaced] FAIL: bale stats exited $rc"; fail=1
else
  if printf '%s' "$out" | tr -s '[:space:]' ' ' | grep -qi "linkage"; then
    echo "[P1-linkage-surfaced] PASS"
  else
    echo "[P1-linkage-surfaced] FAIL: stats output carries no linkage aggregation"; fail=1
  fi
fi
if python3 -m unittest discover -s tests >/dev/null 2>&1; then
  echo "[P2-suite] PASS"
else
  echo "[P2-suite] FAIL: full suite not green"; fail=1
fi
v="$(tr -d '[:space:]' < bin/VERSION 2>/dev/null)"
if [ "$v" = "0.4.19" ]; then
  echo "[P3-version-lane] PASS"
else
  echo "[P3-version-lane] FAIL: bin/VERSION is '$v', lane says bumpless at 0.4.19"; fail=1
fi
exit "$fail"
