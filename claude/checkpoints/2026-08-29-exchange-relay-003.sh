#!/usr/bin/env bash
# Blind checkpoint — exchange-relay (2026-08-29), v1.
# Authored at the read-only sitting 2026-08-29-formalize-convo-001
# from the request, before implementation. Outcome-only. Read-only:
# writes nowhere.
# Exit: 0 all probes pass, 1 any probe fails, 2 script error.
set -u
echo "checkpoint exchange-relay v1: writes to no location"
fail=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fail=1; }
probe() { local l="$1"; shift; if "$@" >/dev/null 2>&1; then pass "$l"; else fail "$l"; fi; }
present() { local l="$1" n="$2" f="$3"; [[ -f "$f" ]] && grep -qF -- "$n" "$f" && pass "$l" || fail "$l"; }
absent()  { local l="$1" n="$2" f="$3"; if [[ ! -f "$f" ]]; then fail "$l (missing $f)"; elif grep -qF -- "$n" "$f"; then fail "$l"; else pass "$l"; fi; }

# --- 1. The schema exists and pins D3's enums (searched anywhere in the
#        document, so the nesting is the worker's call).
S=schemas/exchange-record.schema.json
probe "exchange-record schema exists and parses" python3 -c "import json;json.load(open('$S'))"
probe "schema requires the five D3 envelope keys" python3 - "$S" <<'EOF'
import json,sys
d=json.load(open(sys.argv[1]))
req=set(d.get("required",[]))
sys.exit(0 if {"record_version","session_id","round","from","created_at"}<=req else 1)
EOF
probe "schema pins from = worker|planner and disposition = as-recommended|option|free-text" python3 - "$S" <<'EOF'
import json,sys
d=json.load(open(sys.argv[1])); enums=[]
def walk(x):
    if isinstance(x,dict):
        if isinstance(x.get("enum"),list): enums.append(sorted(x["enum"]))
        for v in x.values(): walk(v)
    elif isinstance(x,list):
        for v in x: walk(v)
walk(d)
ok=(["planner","worker"] in enums) and (["as-recommended","free-text","option"] in enums)
sys.exit(0 if ok else 1)
EOF

# --- 2. The library validator: [] on a D3 record, errors otherwise.
VAL='import sys,json; sys.path.insert(0,"bin"); from bale_validate import validate_exchange_record as v'
GOOD='{"record_version":1,"session_id":"2026-08-29-x-001","round":2,"from":"planner","created_at":"2026-08-29T00:00:00+00:00","answers":[{"question_round":1,"question_index":0,"answer":"the second","disposition":"option"}]}'
probe "validator accepts a D3-shaped planner answer" python3 -c "$VAL; sys.exit(0 if v(json.loads('$GOOD'))==[] else 1)"
probe "validator rejects from=architect" python3 -c "$VAL; r=json.loads('$GOOD'); r['from']='architect'; sys.exit(0 if v(r) else 1)"
probe "validator rejects an empty exchange (no questions, no answers)" python3 -c "$VAL; r=json.loads('$GOOD'); r['answers']=[]; sys.exit(0 if v(r) else 1)"
probe "validator rejects a bad disposition" python3 -c "$VAL; r=json.loads('$GOOD'); r['answers'][0]['disposition']='maybe'; sys.exit(0 if v(r) else 1)"

# --- 3. The verb is wired.
probe "bale --help lists relay" bash -c "python3 bin/bale --help 2>&1 | grep -q relay"
probe "bale relay --help exits 0" python3 bin/bale relay --help

# --- 4. Bump and docs.
present "bin/VERSION reads 0.4.18" "0.4.18" bin/VERSION
probe "BALE.md section 5 relay table row is no longer pending" bash -c "grep -E '^\\| \`bale relay' BALE.md | grep -v -q pending"
present "INDEX.md lists the exchange-record schema" "exchange-record.schema.json" claude/INDEX.md
absent  "BALE.md section 6.5 role-only (user-pastes phrase retired)" "the user runs it, the user" BALE.md

# --- 5. Invariants.
probe "full unit suite passes" python3 -m unittest discover -s tests
probe "tools/ untouched: crafter still has no exchange kind" bash -c "! grep -q 'exchange' tools/craft_response.py"

exit $fail
