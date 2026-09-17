#!/usr/bin/env bash
# Blind checkpoint — guard maintenance (deny table, INSTALL_SCHEMAS, missing-record pin).
# Authored at the desk (2026-09-17 UTC) before any implementation existed.
# Runs from the staging root. Writes: a private tmpdir only.
set -u
trap 'echo "[ERROR] checkpoint script errored at line $LINENO"; exit 2' ERR
echo "checkpoint guard-maintenance v1: writes to nothing in the tree (tmpdir only)"
fails=0; tmp="$(mktemp -d)"
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fails=$((fails + 1)); }
guard() { (cd "$1" && python3 -m unittest discover -s tests -p test_global_doc_selfcontainment.py > "$2" 2>&1); }

# 1. INSTALL_SCHEMAS names the changelog schema
if grep -q 'changelog-record' tests/test_global_doc_selfcontainment.py; then
  pass "install-schemas-names-changelog-record"; else fail "install-schemas-names-changelog-record"; fi

# 2. the guard passes on the applied tree (leftovers rewritten, table sane)
if guard . "$tmp/g0.log"; then pass "guard-passes-on-applied-tree"; else
  fail "guard-passes-on-applied-tree"; tail -20 "$tmp/g0.log"; fi

# 3. hyphenated board citation is caught; a sid string is tolerated
mkdir -p "$tmp/m1" "$tmp/m2"
cp -r . "$tmp/m1"/ && cp -r . "$tmp/m2"/
printf '\n# fold-in: board-13c via the registry\n' >> "$tmp/m1/tools/response_lint.py"
printf '\n# lineage: 2026-09-16-board-96-crafter-85-light-block-002\n' >> "$tmp/m2/tools/response_lint.py"
if guard "$tmp/m1" "$tmp/g1.log"; then fail "guard-catches-hyphenated-board-citation"; else
  pass "guard-catches-hyphenated-board-citation"; fi
if guard "$tmp/m2" "$tmp/g2.log"; then pass "guard-tolerates-sid-string"; else
  fail "guard-tolerates-sid-string"; tail -15 "$tmp/g2.log"; fi

# 4. a missing changelog record for bin/VERSION is loud
ver="$(tr -d '[:space:]' < bin/VERSION)"
rc=0
python3 -m unittest discover -s tests -p test_changelog_record.py > "$tmp/c0.log" 2>&1 || rc=$?
if [ "$rc" -ne 0 ]; then fail "changelog-suite-passes-on-applied-tree"; tail -15 "$tmp/c0.log"; else
  pass "changelog-suite-passes-on-applied-tree"; fi
mkdir -p "$tmp/m3" && cp -r . "$tmp/m3"/ && rm -f "$tmp/m3/claude/changelog/$ver.json"
rc=0
(cd "$tmp/m3" && python3 -m unittest discover -s tests -p test_changelog_record.py > "$tmp/c1.log" 2>&1) || rc=$?
if [ "$rc" -eq 0 ] || [ "$rc" -eq 5 ]; then fail "missing-changelog-record-is-loud"; else
  pass "missing-changelog-record-is-loud"; fi

# tools unchanged in effect
for suite in test_response_lint test_craft_response test_schema_embeds; do
  if python3 -m unittest discover -s tests -p "${suite}.py" > "$tmp/$suite.log" 2>&1; then
    pass "suite-$suite"; else fail "suite-$suite"; tail -15 "$tmp/$suite.log"; fi
done
rm -rf "$tmp"
if [ "$fails" -ne 0 ]; then echo "checkpoint guard-maintenance v1: $fails probe(s) failed"; exit 1; fi
echo "checkpoint guard-maintenance v1: all probes passed"; exit 0
