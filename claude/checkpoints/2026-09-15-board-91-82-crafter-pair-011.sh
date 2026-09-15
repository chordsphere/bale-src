#!/bin/bash
# Blind checkpoint — boards 91 + 82 (crafter pair), v1. Outcome-only,
# CLI-level against the staged tools/craft_response.py. cwd = staging root.
fails=0
pass() { echo "[PASS] $1"; }
failp() { echo "[FAIL] $1"; fails=$((fails+1)); }
ROOT="$PWD"; CR="$ROOT/tools/craft_response.py"
S="$(mktemp -d /tmp/oracle-91.XXXXXX)"; trap 'rm -rf "$S"' EXIT
mkdir -p "$S/resp"
SID="2026-09-15-oracle-001"

# Build a filled clarification manifest from the tool's own skeleton.
python3 "$CR" "$S/resp" --sid "$SID" --kind clarification --questions 1 > "$S/skel.json" 2>/dev/null
python3 - "$S/skel.json" "$S/ok.json" "$S/bad.json" <<'PY'
import json, sys
m = json.load(open(sys.argv[1]))
q = m["questions"][0]
for k in q:
    if not q[k]: q[k] = "filled " + k
m["reason"] = m.get("reason") or "oracle"; m["summary"] = m.get("summary") or "oracle"
q["origin"] = "intent-gap"; json.dump(m, open(sys.argv[2], "w"), indent=2)
q["origin"] = "not-a-real-origin"; json.dump(m, open(sys.argv[3], "w"), indent=2)
PY

# P1: a valid origin renders through --emit-block, key in the body.
out="$(python3 "$CR" --emit-block "$S/ok.json" --round 1 2>&1)"; rc=$?
if [ "$rc" -eq 0 ] && printf '%s\n' "$out" | grep -q '"origin": "intent-gap"'; then pass "emit-block renders a valid origin row"; else failp "emit-block renders a valid origin row (exit $rc)"; fi

# P2: an invalid origin value refuses (vocabulary closed).
python3 "$CR" --emit-block "$S/bad.json" --round 1 >/dev/null 2>&1; rc=$?
if [ "$rc" -ne 0 ]; then pass "emit-block refuses an invalid origin value"; else failp "emit-block refuses an invalid origin value"; fi

# P3: --request seeds feedback.mechanical.provenance = request provenance + model_identity "".
python3 - "$S/req.json" <<'PY'
import json, sys
json.dump({"session_id": "2026-09-15-oracle-001", "goal": "g", "provenance": {
  "bale_version": "0.4.33", "contract_docs": {"CLAUDE.md": "a"*64, "TARBALL.md": "b"*64, "DOCS.md": "c"*64, "CODE.md": "d"*64, "PLANNER.md": "e"*64},
  "packer": "oracle", "work_class": "code", "checkpoint": None, "checkpoint_scope_admitted": False,
  "packed_at": "2026-09-15T00:00:00+00:00", "base_files": {}}}, open(sys.argv[1], "w"))
PY
python3 "$CR" "$S/resp" --sid "$SID" --request "$S/req.json" > "$S/seeded.json" 2>"$S/seeded.err"; rc=$?
if [ "$rc" -eq 0 ] && python3 - "$S/seeded.json" "$S/req.json" <<'PY'
import json, sys
out = json.load(open(sys.argv[1])); req = json.load(open(sys.argv[2]))
p = out.get("feedback", {}).get("mechanical", {}).get("provenance")
want = dict(req["provenance"]); want["model_identity"] = ""
sys.exit(0 if p == want else 1)
PY
then pass "--request seeds the provenance echo verbatim plus empty model_identity"; else failp "--request seeds the provenance echo verbatim plus empty model_identity (exit $rc)"; fi

# P4: the four doc-pin suites stay green (a schemas/ forecast ships the guard).
if ( cd "$ROOT" && python3 -m unittest tests.test_sanctioned_pairs tests.test_doc_crossrefs tests.test_global_doc_selfcontainment tests.test_schema_embeds >/dev/null 2>&1 ); then pass "doc-pin suites green"; else failp "doc-pin suites green"; fi

[ "$fails" -eq 0 ] && exit 0 || exit 1
