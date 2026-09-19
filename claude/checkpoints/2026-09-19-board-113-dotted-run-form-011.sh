#!/usr/bin/env bash
# Blind checkpoint v1 — board 113 (slug board-113-dotted-run-form).
# Authored 2026-09-19 by the 2026-09-19-continue-plan-009 desk, from the
# request, before any implementation. Outcome-only. Runs from the staged
# tree's root. Writes: python bytecode caches are suppressed; the one
# suite it executes writes only under its own temp dirs.
# Exit 0 pass, 1 a probe failed, 2 the script itself errored.
set -u
export PYTHONDONTWRITEBYTECODE=1
fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fails=$((fails + 1)); }
echo "writes: none in the tree (PYTHONDONTWRITEBYTECODE=1); temp dirs only"
command -v python3 >/dev/null 2>&1 || { echo "checkpoint error: python3 not found"; exit 2; }

n=$(ls tests/test_*.py 2>/dev/null | wc -l)
if [ "$n" -ge 60 ] && [ -f tests/harness.py ] && [ -f tests/test_thread_status.py ]; then
  pass "anchor: the test tree is present (60 or more suites, the harness, test_thread_status)"
else
  fail "anchor: the test tree is present (60 or more suites, the harness, test_thread_status)"
fi

bad=$(python3 - <<'PY'
import glob, os, subprocess, sys
bad = []
for p in sorted(glob.glob("tests/test_*.py")):
    name = os.path.basename(p)[:-3]
    code = ("import sys, unittest\n"
            "ld = unittest.TestLoader()\n"
            "ld.loadTestsFromName('tests.%s')\n"
            "sys.exit(1 if ld.errors else 0)\n" % name)
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
    if r.returncode != 0:
        bad.append(name)
print(" ".join(bad))
PY
)
rc=$?
if [ "$rc" -ne 0 ]; then echo "checkpoint error: the loader sweep itself failed"; exit 2; fi
if [ -z "$bad" ]; then
  pass "every suite under tests/ loads in the dotted form from the repo root"
else
  echo "  do not load: $bad"
  fail "every suite under tests/ loads in the dotted form from the repo root"
fi

ok=yes
python3 -m unittest tests.test_thread_status >/dev/null 2>&1 || { ok=no; echo "  dotted form failed"; }
python3 -m unittest discover -s tests -p 'test_thread_status.py' >/dev/null 2>&1 || { ok=no; echo "  discovery failed"; }
python3 tests/test_thread_status.py >/dev/null 2>&1 || { ok=no; echo "  direct execution failed"; }
if [ "$ok" = yes ]; then
  pass "test_thread_status passes in all three run forms: dotted, discovery, direct"
else
  fail "test_thread_status passes in all three run forms: dotted, discovery, direct"
fi

if [ "$fails" -gt 0 ]; then echo "checkpoint: $fails probe(s) failed"; exit 1; fi
echo "checkpoint: all probes passed"; exit 0
