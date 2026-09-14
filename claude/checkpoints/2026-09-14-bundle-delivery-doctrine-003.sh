#!/usr/bin/env bash
# Blind checkpoint — bundle-delivery doctrine micro (docs/CLAUDE.md +
# docs/PLANNER.md). Authored blind at the 2026-09-14 master sitting
# from the request, before any implementation exists (TARBALL.md §7;
# PLANNER.md §4). Outcome contracts only. Runs with cwd = the staged
# applied tree, confined.
#
# Probes:
#   docs-self-contained      tests/test_global_doc_selfcontainment.py passes
#   doc-crossrefs-resolve    tests/test_doc_crossrefs.py passes (every
#                            section pointer between the five docs resolves)
#   planner-s2-names-bundle  docs/PLANNER.md §2 (Command and Request
#                            Authoring) contains the preserved crafter token
#                            `--bundle`
#   core-names-open-verb     docs/CLAUDE.md contains the preserved verb
#                            `bale open` — the every-read core now names the
#                            operator's verb for a planner-delivered pack
#
# Exit: 0 all pass; 1 a probe failed; 2 the script itself errored.
set -u
command -v python3 >/dev/null 2>&1 || { echo "[ERROR] python3 missing"; exit 2; }
[ -f docs/CLAUDE.md ] && [ -f docs/PLANNER.md ] && [ -f tests/harness.py ] \
  || { echo "[ERROR] docs/ or tests/ absent — not the bale-src tree"; exit 2; }
failed=0

out=$(python3 -m unittest tests.test_global_doc_selfcontainment 2>&1); rc=$?
if [ $rc -eq 0 ]; then echo "[PASS] docs-self-contained: $(echo "$out" | grep -E '^Ran ' | head -1)"
else echo "[FAIL] docs-self-contained: exit $rc"; echo "$out" | tail -12; failed=1; fi

out=$(python3 -m unittest tests.test_doc_crossrefs 2>&1); rc=$?
if [ $rc -eq 0 ]; then echo "[PASS] doc-crossrefs-resolve: $(echo "$out" | grep -E '^Ran ' | head -1)"
else echo "[FAIL] doc-crossrefs-resolve: exit $rc"; echo "$out" | tail -12; failed=1; fi

# PLANNER.md §2 runs from its "## 2." heading to the next "## " heading
section=$(awk '/^## 2\. /{f=1; print; next} /^## /{f=0} f' docs/PLANNER.md)
if [ -z "$section" ]; then echo "[FAIL] planner-s2-names-bundle: §2 heading not found"; failed=1
elif printf '%s\n' "$section" | grep -q -- '--bundle'; then echo "[PASS] planner-s2-names-bundle"
else echo "[FAIL] planner-s2-names-bundle: docs/PLANNER.md §2 does not name --bundle"; failed=1; fi

if grep -q 'bale open' docs/CLAUDE.md; then echo "[PASS] core-names-open-verb"
else echo "[FAIL] core-names-open-verb: docs/CLAUDE.md never names bale open"; failed=1; fi

exit $failed
