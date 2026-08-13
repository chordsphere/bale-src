#!/usr/bin/env bash
# claude/checkpoints/current.sh - blind checkpoint, board-10 wave 4
# Session gated: board-10-escalation-schemas (S4, solo)
# Sitting: 2026-08-10-continue-plan-001 (board-10 spec-intake repack)
#
# Planner-authored from the request before implementation; fixture
# construction dry-run against stubs at authoring per the wave-3
# standing practice. Runs cwd = staging. Exit: 0 pass, 1 fail, 2 error.

set -u
status=0
note() { printf '[ckpt] %s\n' "$*"; }
failck() { printf '[ckpt] FAIL: %s\n' "$*"; status=1; }

if [ ! -f schemas/escalation-record.schema.json ]; then
  note "S4 guard not armed in this tree; checkpoint passes vacuously"
  exit 0
fi
note "S4 guard armed: schemas/escalation-record.schema.json present"

for tok in subsumes amendment_target recommendation priority; do
  if grep -q "$tok" schemas/escalation-record.schema.json; then
    note "escalation schema token present: $tok"
  else
    failck "pinned escalation schema token missing: $tok"
  fi
done
for tok in options recommendation priority; do
  if grep -q "$tok" schemas/response-manifest.schema.json; then
    note "manifest schema token present: $tok"
  else
    failck "pinned manifest schema token missing: $tok"
  fi
done
if grep -q "claim_basis" schemas/response-manifest.schema.json; then
  note "manifest schema admits the annotated claim form"
else
  failck "manifest schema missing the claim_basis carrier"
fi

python3 - <<'PYEOF'
import sys, copy
sys.path.insert(0, "bin")
import bale_validate

fails = []

def check(fn, name, fixture, expect_valid):
    errs = fn(fixture)
    ok = (errs == []) if expect_valid else (errs != [])
    print(f"[ckpt] {'ok' if ok else 'FAIL'}: {name}"
          + ("" if ok else f" :: {errs[:2] if errs else 'accepted but should reject'}"))
    if not ok:
        fails.append(name)

# --- escalation records (new schema; fixtures authored from the pin) ---
er = bale_validate.validate_escalation_record
base = {
    "question": "Should the retry counter live in the registry or the record?",
    "options": ["registry", "record"],
    "recommendation": "record",
    "priority": "batched",
    "subsumes": [],
    "amendment_target": "claude/MASTER.md",
}
check(er, "minimal escalation record", base, True)

full = copy.deepcopy(base)
full["priority"] = "blocking"
full["subsumes"] = ["sid-a:q1", "sid-b:q3"]
check(er, "blocking record with lineage", full, True)

for name, mut, ok in (
    ("priority outside the enum", {"priority": "urgent"}, False),
    ("missing recommendation", {"recommendation": None}, False),
    ("subsumes not an array", {"subsumes": "sid-a:q1"}, False),
    ("empty options", {"options": []}, False),
):
    r = copy.deepcopy(base)
    for k, v in mut.items():
        if v is None:
            r.pop(k, None)
        else:
            r[k] = v
    check(er, name, r, ok)

# --- clarification question rows (extended surface) ---
cq = bale_validate.validate_clarification_questions
row = {
    "question": "Which config layer owns the cap?",
    "context": "The cap could be global or project.",
    "default_assumption": "project layer",
    "why_blocked": "the key's home decides the merge branch",
    "options": ["global", "project"],
    "recommendation": "project",
    "priority": "batched",
}
check(cq, "extended question row", [row], True)

legacy = {k: row[k] for k in ("question", "context", "default_assumption", "why_blocked")}
check(cq, "legacy row without the extension", [legacy], True)

bad = copy.deepcopy(row)
bad["priority"] = "whenever"
check(cq, "question priority outside the enum", [bad], False)

sys.exit(1 if fails else 0)
PYEOF
[ $? -eq 0 ] || status=1

exit "$status"
