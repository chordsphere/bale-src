#!/usr/bin/env bash
# Blind checkpoint — TARBALL.md §3.4 bundle clauses micro. Authored blind
# at the 2026-09-14 master sitting from the request (TARBALL.md §7;
# PLANNER.md §4). Outcome contracts only. cwd = staged applied tree.
#
# Probes:
#   sanctioned-pairs-hold      tests/test_sanctioned_pairs.py passes — the
#                              pinned §3.4 extracts survived the edit
#   doc-crossrefs-resolve      tests/test_doc_crossrefs.py passes
#   docs-self-contained        tests/test_global_doc_selfcontainment.py passes
#   ckpt-paragraph-names-bundle
#                              docs/TARBALL.md's "Checkpoint-configured
#                              projects." paragraph contains the term bundle
#   bundle-paragraph-names-validation-key
#                              the "Planner bundles are oracle-bearing"
#                              paragraph names the [validation] config key
# Exit: 0 all pass; 1 a probe failed; 2 the script itself errored.
set -u
command -v python3 >/dev/null 2>&1 || { echo "[ERROR] python3 missing"; exit 2; }
[ -f docs/TARBALL.md ] && [ -f tests/harness.py ] || { echo "[ERROR] not the bale-src tree"; exit 2; }
failed=0
for pair in "sanctioned-pairs-hold:tests.test_sanctioned_pairs" "doc-crossrefs-resolve:tests.test_doc_crossrefs" "docs-self-contained:tests.test_global_doc_selfcontainment"; do
  label=${pair%%:*}; mod=${pair#*:}
  out=$(python3 -m unittest "$mod" 2>&1); rc=$?
  if [ $rc -eq 0 ]; then echo "[PASS] $label: $(echo "$out" | grep -E '^Ran ' | head -1)"
  else echo "[FAIL] $label: exit $rc"; echo "$out" | tail -12; failed=1; fi
done
para=$(awk '/^\*\*Checkpoint-configured projects\.\*\*/{f=1} f&&/^$/{exit} f' docs/TARBALL.md)
if [ -z "$para" ]; then echo "[FAIL] ckpt-paragraph-names-bundle: paragraph anchor not found"; failed=1
elif printf '%s\n' "$para" | grep -qi 'bundle'; then echo "[PASS] ckpt-paragraph-names-bundle"
else echo "[FAIL] ckpt-paragraph-names-bundle: the paragraph does not name the bundle"; failed=1; fi
para=$(awk '/^\*\*Planner bundles are oracle-bearing/{f=1} f&&/^$/{exit} f' docs/TARBALL.md)
if [ -z "$para" ]; then echo "[FAIL] bundle-paragraph-names-validation-key: paragraph anchor not found"; failed=1
elif printf '%s\n' "$para" | grep -q '\[validation\]'; then echo "[PASS] bundle-paragraph-names-validation-key"
else echo "[FAIL] bundle-paragraph-names-validation-key: the paragraph does not name [validation]"; failed=1; fi
exit $failed
