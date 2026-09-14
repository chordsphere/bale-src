#!/usr/bin/env bash
# Blind checkpoint — doc-lane micro: board rows 74 (emission-contract
# rules) + 76 (response-manifest echo admits base_files). Authored blind
# at the 2026-09-14 master sitting from the request, before any
# implementation exists (TARBALL.md §7; PLANNER.md §4). Outcome
# contracts only. Runs with cwd = the staged applied tree, confined.
#
# Probes:
#   echo-admits-base-files   the response-manifest schema's provenance
#                            echo declares a base_files property
#   lint-embed-parity        tests/test_schema_embeds.py passes (the
#                            schema edit and the lint embed landed together)
#   docs-self-contained      tests/test_global_doc_selfcontainment.py passes
#   checklist-names-emit-block
#                            docs/TARBALL.md's §10.1 section contains the
#                            preserved tool token `--emit-block`
#
# Exit: 0 all pass; 1 a probe failed; 2 the script itself errored.
set -u
command -v python3 >/dev/null 2>&1 || { echo "[ERROR] python3 missing"; exit 2; }
[ -f docs/TARBALL.md ] && [ -f schemas/response-manifest.schema.json ] \
  || { echo "[ERROR] docs/TARBALL.md or schemas/response-manifest.schema.json absent"; exit 2; }
failed=0

# probe 1
if python3 - <<'PY'
import json, sys
s = json.load(open("schemas/response-manifest.schema.json"))
def walk(node):
    if isinstance(node, dict):
        props = node.get("properties")
        if isinstance(props, dict) and "provenance" in props:
            prov = props["provenance"]
            if isinstance(prov, dict) and "base_files" in (prov.get("properties") or {}):
                return True
        return any(walk(v) for v in node.values())
    if isinstance(node, list):
        return any(walk(v) for v in node)
    return False
sys.exit(0 if walk(s) else 1)
PY
then echo "[PASS] echo-admits-base-files"; else echo "[FAIL] echo-admits-base-files: no provenance echo with a base_files property"; failed=1; fi

# probe 2
out=$(python3 -m unittest tests.test_schema_embeds 2>&1); rc=$?
if [ $rc -eq 0 ]; then echo "[PASS] lint-embed-parity: $(echo "$out" | grep -E '^Ran ' | head -1)"; else echo "[FAIL] lint-embed-parity: exit $rc"; echo "$out" | tail -12; failed=1; fi

# probe 3
out=$(python3 -m unittest tests.test_global_doc_selfcontainment 2>&1); rc=$?
if [ $rc -eq 0 ]; then echo "[PASS] docs-self-contained: $(echo "$out" | grep -E '^Ran ' | head -1)"; else echo "[FAIL] docs-self-contained: exit $rc"; echo "$out" | tail -12; failed=1; fi

# probe 4 — §10.1 runs from its heading to the next "### 10." heading
section=$(awk '/^### 10\.1 /{f=1} /^### 10\.[2-9]/{f=0} f' docs/TARBALL.md)
if [ -z "$section" ]; then echo "[FAIL] checklist-names-emit-block: §10.1 heading not found"; failed=1
elif printf '%s\n' "$section" | grep -q -- '--emit-block'; then echo "[PASS] checklist-names-emit-block"
else echo "[FAIL] checklist-names-emit-block: §10.1 does not name --emit-block"; failed=1; fi

exit $failed
