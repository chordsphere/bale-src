#!/usr/bin/env bash
# Blind checkpoint — row 80 (tests-only pin micro), v1.
# Authored at the 2026-09-14-continue-plan-006 sitting from the
# request, before implementation. Outcome contracts only:
#   1. the affected suites run green under discover;
#   2. the four brief-named pins exist (names are preserved text the
#      brief hands the worker, so fixed-string probes are legitimate);
#   3. the helper move landed: harness.py defines both helpers, the
#      two named suites define neither;
# Writes: nothing outside the suites' own temp dirs.
set -u
status=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; status=1; }

if [ ! -f bin/VERSION ] || [ ! -d tests ]; then
  echo "[FAIL] checkpoint must run at the repo root (bin/VERSION, tests/ missing)"
  exit 2
fi

# 1. Suites green.
out="$(python3 -m unittest discover -s tests \
  -p 'test_schema_embeds.py' 2>&1; \
  python3 -m unittest discover -s tests -p 'test_doc_crossrefs.py' 2>&1; \
  python3 -m unittest discover -s tests -p 'test_sanctioned_pairs.py' 2>&1; \
  python3 -m unittest discover -s tests -p 'test_telemetry_extensions.py' 2>&1; \
  python3 -m unittest discover -s tests -p 'test_admission_prompts.py' 2>&1; \
  python3 -m unittest discover -s tests -p 'test_apply_operations.py' 2>&1; \
  python3 -m unittest discover -s tests -p 'test_slow_gate.py' 2>&1)"
echo "$out" | grep -E '^(Ran |OK|FAILED)' 
bad="$(echo "$out" | grep -Ec '^FAILED')"
runs="$(echo "$out" | grep -Ec '^Ran ')"
if [ "$bad" -eq 0 ] && [ "$runs" -eq 7 ]; then
  pass "seven suites ran, none FAILED"
else
  fail "suites: $runs run lines, $bad FAILED lines (expected 7 and 0)"
fi

# 2. Named pins present (preserved text from the brief).
probe_fixed() {  # file, fixed string, label
  if [ -f "$1" ] && grep -Fq -- "$2" "$1"; then
    pass "$3"
  else
    fail "$3 (missing in $1)"
  fi
}
probe_fixed tests/test_schema_embeds.py \
  "def test_request_provenance_keys_subset_of_echo" \
  "schema key-parity pin present"
probe_fixed tests/test_doc_crossrefs.py \
  "def test_planner_bundle_ruling_bullet_precedes_single_line" \
  "PLANNER.md ruling-bullet pin present"
probe_fixed tests/test_doc_crossrefs.py \
  "def test_claude_mentions_bale_open" \
  "CLAUDE.md bale-open pin present"
probe_fixed tests/test_sanctioned_pairs.py \
  "bundled delivery (CLAUDE.md 11.2 / TARBALL.md 3.4)" \
  "sanctioned-pair key for the bundled-delivery sentence present"

# 3. Helper move.
for h in _minimal_record _load_module; do
  if grep -Eq "^def $h\(" tests/harness.py; then
    pass "tests/harness.py defines $h"
  else
    fail "tests/harness.py does not define $h"
  fi
  for f in tests/test_telemetry_extensions.py tests/test_admission_prompts.py; do
    if grep -Eq "^def $h\(" "$f"; then
      fail "$f still defines $h"
    else
      pass "$f no longer defines $h"
    fi
  done
done

exit "$status"
