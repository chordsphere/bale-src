#!/bin/bash
# Blind checkpoint — board 96 (crafter third) + 85, v1. Outcome-only,
# CLI-level against the staged tools/ and schemas/. cwd = staging root.
fails=0
pass() { echo "[PASS] $1"; }
failp() { echo "[FAIL] $1"; fails=$((fails+1)); }
ROOT="$PWD"; CR="$ROOT/tools/craft_response.py"
S="$(mktemp -d /tmp/oracle-96c.XXXXXX)"; trap 'rm -rf "$S"' EXIT
mkdir -p "$S/resp"; SID="2026-09-15-oracle-001"
python3 "$CR" "$S/resp" --sid "$SID" --kind clarification --questions 3 > "$S/skel3.json" 2>/dev/null
python3 "$CR" "$S/resp" --sid "$SID" --kind clarification --questions 4 > "$S/skel4.json" 2>/dev/null
python3 - "$S/skel3.json" "$S/three.json" "$S/skel4.json" "$S/four.json" <<'PY'
import json, sys
def fill(src, dst, tag):
    m = json.load(open(src)); m["reason"] = m.get("reason") or "oracle"; m["summary"] = m.get("summary") or "oracle"
    for i, q in enumerate(m["questions"], 1):
        for k in q:
            if not q[k]: q[k] = f"{tag}-{k}-{i}"
    json.dump(m, open(dst, "w"), indent=2)
fill(sys.argv[1], sys.argv[2], "three"); fill(sys.argv[3], sys.argv[4], "four")
PY
# P1: three rows render as the §5.10 block: sentinels with the sid, the four labels, the row text, the three replies.
out="$(python3 "$CR" --light-block "$S/three.json" --sid "$SID" 2>&1)"; rc=$?
flat="$(printf '%s' "$out" | tr -s '[:space:]' ' ')"
if [ "$rc" -eq 0 ] && printf '%s' "$out" | grep -qF "=== LIGHT BEGIN $SID ===" && printf '%s' "$out" | grep -qF "=== LIGHT END $SID ===" \
   && printf '%s' "$out" | grep -q '\[3\]' && printf '%s' "$flat" | grep -q 'while doing' && printf '%s' "$flat" | grep -q 'would assume' && printf '%s' "$flat" | grep -q 'why blocked' \
   && printf '%s' "$flat" | grep -q 'three-question-2' && printf '%s' "$flat" | grep -q 'three-default_assumption-3' \
   && printf '%s' "$flat" | grep -q 'as assumed' && printf '%s' "$flat" | grep -q 'formal'; then pass "light-block renders three rows per 5.10"; else failp "light-block renders three rows per 5.10 (exit $rc)"; fi
# P2: four rows refuse.
python3 "$CR" --light-block "$S/four.json" --sid "$SID" >/dev/null 2>&1; rc=$?
if [ "$rc" -ne 0 ]; then pass "light-block refuses four rows"; else failp "light-block refuses four rows"; fi
# P3: schema admits the two counts as integers; lint embed identical to source.
if python3 - "$ROOT/schemas/response-manifest.schema.json" <<'PY'
import json, sys
sr = json.load(open(sys.argv[1]))["properties"]["feedback"]["properties"]["self_reported"]["properties"]
sys.exit(0 if all(sr.get(k, {}).get("type") == "integer" for k in ("light_blocks", "paste_carried_rounds")) else 1)
PY
then pass "self_reported admits light_blocks and paste_carried_rounds"; else failp "self_reported admits light_blocks and paste_carried_rounds"; fi
if ( cd "$ROOT" && python3 -m unittest tests.test_schema_embeds tests.test_sanctioned_pairs tests.test_doc_crossrefs tests.test_global_doc_selfcontainment >/dev/null 2>&1 ); then pass "doc-pin suites green (lint embed in parity)"; else failp "doc-pin suites green (lint embed in parity)"; fi
# P4: TARBALL.md carries the two field names, the seeded-block clause, and points at the flag.
T="$ROOT/docs/TARBALL.md"; tflat="$(tr -s '[:space:]' ' ' < "$T")"
if printf '%s' "$tflat" | grep -q 'light_blocks' && printf '%s' "$tflat" | grep -q 'paste_carried_rounds'; then pass "TARBALL.md 5.2.2 names both counts"; else failp "TARBALL.md 5.2.2 names both counts"; fi
if printf '%s' "$tflat" | grep -qF 'When the crafter seeded the block from the request (--request), fill model_identity and self_reported before running the emitter, and paste the emitter'"'"'s object over the four placeholders key for key rather than replacing the mechanical object.'; then pass "seeded-block clause verbatim"; else failp "seeded-block clause verbatim"; fi
if printf '%s' "$tflat" | grep -q -- '--light-block'; then pass "TARBALL.md points at --light-block"; else failp "TARBALL.md points at --light-block"; fi
# P5: --help carries the stem clock sentence; lint docstrings no longer say provenance is hand-added.
if python3 "$CR" --help 2>&1 | tr -s '[:space:]' ' ' | grep -qF "The stem's date is the UTC date, the same clock session ids use."; then pass "bundle stem clock sentence in --help"; else failp "bundle stem clock sentence in --help"; fi
if ! tr -s '[:space:]' ' ' < "$ROOT/tools/response_lint.py" | grep -q '(linkage, provenance) are not emitted; the worker adds them by hand'; then pass "lint docstring retires the hand-added provenance claim"; else failp "lint docstring retires the hand-added provenance claim"; fi
[ "$fails" -eq 0 ] && exit 0 || exit 1
