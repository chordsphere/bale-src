#!/usr/bin/env bash
# Blind checkpoint — exchange-crafter (2026-08-30), v1. Outcome-only.
# Writes only under a mktemp -d scratch, removed on exit.
# Exit: 0 all pass, 1 any fail, 2 script error.
set -u
scratch="$(mktemp -d)" || { echo "[FAIL] scratch dir"; exit 2; }
trap 'rm -rf "$scratch"' EXIT
echo "checkpoint exchange-crafter v1: writes only under $scratch (removed on exit)"
fail=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fail=1; }
probe() { local l="$1"; shift; if "$@" >/dev/null 2>&1; then pass "$l"; else fail "$l"; fi; }
present() { local l="$1" n="$2" f="$3"; [[ -f "$f" ]] && grep -qF -- "$n" "$f" && pass "$l" || fail "$l"; }

# Fixture: a filled clarification manifest (row shape per
# response-manifest.schema.json: question, context, default_assumption,
# why_blocked are required).
cat > "$scratch/manifest.json" <<'JSON'
{
  "session_id": "2026-08-30-fixture-001",
  "response_kind": "clarification",
  "responds_to": "2026-08-30-fixture-001",
  "corrects": null,
  "summary": "clarification: one blocking intent gap",
  "changes": [],
  "deferred": [],
  "validation_will_run": false,
  "claims": [],
  "questions": [
    {
      "question": "Which of the two targets is authoritative?",
      "context": "The brief names both files as the home.",
      "default_assumption": "The first named is authoritative.",
      "why_blocked": "The edit lands in one of them and they disagree."
    }
  ]
}
JSON

# --- 1. The flag exists and stdout is exactly the block.
probe "crafter --help names --emit-block" bash -c "python3 tools/craft_response.py --help 2>&1 | grep -q -- --emit-block"
if python3 tools/craft_response.py --kind clarification --emit-block "$scratch/manifest.json" > "$scratch/block.txt" 2>"$scratch/err.txt"; then
  pass "emit-block over a filled manifest exits 0"
else
  fail "emit-block over a filled manifest exits 0"
fi
probe "stdout first line is the BEGIN sentinel with the sid" bash -c "head -1 '$scratch/block.txt' | grep -qE '^BALE EXCHANGE BEGIN 2026-08-30-fixture-001$'"
probe "stdout last line is the END sentinel" bash -c "tail -1 '$scratch/block.txt' | grep -qE '^BALE EXCHANGE END$'"

# --- 2. The block's body: trailer sha256 matches; the record is the
#        normalized worker round-1 reading and the library accepts it.
probe "body sha256 matches the trailer and the record is a valid worker round-1" python3 - "$scratch/block.txt" <<'PYEOF'
import sys, json, hashlib
lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
body_lines = [l for l in lines[1:-1] if not l.startswith("#")]
body = "\n".join(body_lines)
trailer = [l for l in lines if l.startswith("# sha256 ")]
assert len(trailer) == 1, "exactly one sha256 trailer line"
digest = trailer[0].split()[-1]
for candidate in (body, body + "\n"):
    if hashlib.sha256(candidate.encode("utf-8")).hexdigest() == digest:
        break
else:
    sys.exit(1)
rec = json.loads(body)
assert rec["from"] == "worker" and rec["round"] == 1
assert rec["session_id"] == "2026-08-30-fixture-001"
assert rec["questions"][0]["question"].startswith("Which of the two")
sys.path.insert(0, "bin")
from bale_validate import validate_exchange_record
sys.exit(0 if validate_exchange_record({k: v for k, v in rec.items()}) == [] else 1)
PYEOF

# --- 3. Round selection and refusals.
probe "emit-block honors --round 3" bash -c "python3 tools/craft_response.py --kind clarification --emit-block '$scratch/manifest.json' --round 3 2>/dev/null | grep -q '\"round\": 3'"
probe "a from-planner record is refused" bash -c "printf '{\"record_version\":1,\"session_id\":\"s\",\"round\":2,\"from\":\"planner\",\"created_at\":\"2026-08-30T00:00:00+00:00\",\"answers\":[{\"question_round\":1,\"question_index\":0,\"answer\":\"x\",\"disposition\":\"free-text\"}]}' > '$scratch/p.json'; ! python3 tools/craft_response.py --emit-block '$scratch/p.json' >/dev/null 2>&1"

# --- 4. Parity is pinned in the suite and the suite passes.
probe "a parity test imports format_exchange_block" bash -c "grep -rl format_exchange_block tests/ | grep -q ."
probe "full unit suite passes" python3 -m unittest discover -s tests

# --- 5. Docs and bump.
present "TARBALL.md 5.9.2 names --emit-block" "--emit-block" docs/TARBALL.md
present "bin/VERSION reads 0.4.19" "0.4.19" bin/VERSION
exit $fail
