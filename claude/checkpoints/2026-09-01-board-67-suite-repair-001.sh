#!/usr/bin/env bash
# Blind checkpoint — 2026-08-31-board-67-suite-repair (v1)
# Outcome contract, nothing else: the repo's own test suite is green
# on the applied tree, under both gate positions. Exit: 0 PASS,
# 1 HOLD, 2 defective environment.
#
# Probe labels: suite-green-default, suite-green-slow-gated. Both run
# full unittest discovery against the live tree (read-only; the
# suite's own sandboxes are hermetic per ADR-0005). Pre-repair this
# checkpoint FAILs by construction — the shipped tree carries
# pre-existing failures — which is the expected-HOLD proof at open.
set -u

ROOT=""
for d in "$PWD" "$PWD/.." "$PWD/../.."; do
  if [ -f "$d/bin/bale" ] && [ -f "$d/tests/harness.py" ]; then
    ROOT="$(cd "$d" && pwd)"
    break
  fi
done
if [ -z "$ROOT" ]; then
  echo "CHECKPOINT ERROR: cannot locate tree root (bin/bale + tests/harness.py) from $PWD" >&2
  exit 2
fi

fail=0

echo "PROBE suite-green-default: running full discovery (slow gate closed)..."
if (cd "$ROOT" && python3 -m unittest discover -s tests >/tmp/ckpt67-default.log 2>&1); then
  echo "PROBE suite-green-default: PASS (discovery exit 0)"
else
  echo "PROBE suite-green-default: FAIL (nonzero discovery exit; tail follows)"
  tail -n 25 /tmp/ckpt67-default.log
  fail=1
fi

echo "PROBE suite-green-slow-gated: running full discovery (BALE_TEST_SLOW=1)..."
if (cd "$ROOT" && BALE_TEST_SLOW=1 python3 -m unittest discover -s tests >/tmp/ckpt67-slow.log 2>&1); then
  echo "PROBE suite-green-slow-gated: PASS (discovery exit 0)"
else
  echo "PROBE suite-green-slow-gated: FAIL (nonzero discovery exit; tail follows)"
  tail -n 25 /tmp/ckpt67-slow.log
  fail=1
fi

exit $fail
