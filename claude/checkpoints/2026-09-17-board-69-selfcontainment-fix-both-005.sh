#!/usr/bin/env bash
# Blind checkpoint — board 69 follow-up: injected-surface self-containment.
# Authored at the desk (2026-09-17 UTC) before any implementation existed.
# Runs from the staging root. Writes: a private tmpdir only.
set -u
trap 'echo "[ERROR] checkpoint script errored at line $LINENO"; exit 2' ERR
echo "checkpoint 69-fix-both v1: writes to nothing in the tree (tmpdir only)"
fails=0; tmp="$(mktemp -d)"
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fails=$((fails + 1)); }
# The guard suite is the outcome; the desk's own citation grep was wider
# than the guard's pattern and would refuse a passing tree, so it is gone.
for suite in test_global_doc_selfcontainment test_response_lint test_craft_response test_schema_embeds; do
  if python3 -m unittest discover -s tests -p "${suite}.py" > "$tmp/$suite.log" 2>&1; then
    pass "suite-$suite"
  else
    fail "suite-$suite"; tail -25 "$tmp/$suite.log"
  fi
done
rm -rf "$tmp"
if [ "$fails" -ne 0 ]; then echo "checkpoint 69-fix-both v1: $fails probe(s) failed"; exit 1; fi
echo "checkpoint 69-fix-both v1: all probes passed"; exit 0
