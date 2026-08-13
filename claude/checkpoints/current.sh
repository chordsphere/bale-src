#!/usr/bin/env bash
# claude/checkpoints/current.sh - blind checkpoint, board-10 wave 3, amended (claim_basis fixture walks attempts[].validation)
# Session gated: board-10-telemetry-extensions (S5, solo)
# Sitting: 2026-08-10-continue-plan-001 (board-10 spec-intake repack)
#
# Planner-authored from the request, before implementation. Replaces
# the wave-2 guards (both wave-2 sessions closed). Probe-surface note
# per the wave-2 finding: nothing here reads /sys/class/net.
# Runs cwd = staging. Exit: 0 pass, 1 fail, 2 error.

set -u
status=0
note() { printf '[ckpt] %s\n' "$*"; }
failck() { printf '[ckpt] FAIL: %s\n' "$*"; status=1; }

if ! grep -q "no_response" schemas/telemetry-record.schema.json 2>/dev/null; then
  note "S5 guard not armed in this tree; checkpoint passes vacuously"
  exit 0
fi
note "S5 guard armed: no_response present in telemetry schema"

for tok in malformed_response claim_basis tokens_in tokens_out model_tier; do
  if grep -q "$tok" schemas/telemetry-record.schema.json; then
    note "schema token present: $tok"
  else
    failck "pinned schema token missing: $tok"
  fi
done

# Functional probes through the pinned surface:
# validate_telemetry_record(record: dict) -> list of error strings
# (empty list = valid), importable from bin/bale_validate.py.
python3 - <<'PYEOF'
import sys, json, copy
sys.path.insert(0, "bin")
import bale_validate

fails = []

def check(name, record, expect_valid):
    errs = bale_validate.validate_telemetry_record(record)
    ok = (errs == []) if expect_valid else (errs != [])
    tag = "ok" if ok else "FAIL"
    print(f"[ckpt] {tag}: {name}" + ("" if ok else f" :: {errs[:2] if errs else 'accepted but should reject'}"))
    if not ok:
        fails.append(name)

# Base fixture: minimal-but-real shape. Built from the corpus's own
# youngest record so the fixture tracks reality, then mutated.
with open("claude/telemetry/2026-08-10-board-10-orchestration-doc-003.json") as f:
    base = json.load(f)

# 1. A legacy record (no cost block, no claim_basis) still validates.
legacy = copy.deepcopy(base)
legacy.pop("cost", None)
check("legacy record without new fields", legacy, True)

# 2. Null cost fields validate (the empty-until-harness posture).
nullcost = copy.deepcopy(base)
nullcost["cost"] = {"tokens_in": None, "tokens_out": None,
                    "usd": None, "model_tier": None}
check("cost block with all-null fields", nullcost, True)

# 3. Populated cost fields validate.
fullcost = copy.deepcopy(base)
fullcost["cost"] = {"tokens_in": 12345, "tokens_out": 678,
                    "usd": 0.42, "model_tier": "large"}
check("cost block populated", fullcost, True)

# 4. New closure reasons validate; an invented one does not.
for reason, ok in (("no_response", True), ("malformed_response", True),
                   ("definitely_not_a_reason", False)):
    r = copy.deepcopy(base)
    r["closure_reason"] = reason
    check(f"closure_reason {reason}", r, ok)

# 5. claim_basis accepts the two ratified values and rejects others.
#    Real shape (per the record contract): claim rows live at
#    attempts[].validation.claims and .claim_verdict, one level below
#    the envelope. Fixture: the youngest corpus record whose attempt
#    carries a non-null validation block with claims rows.
import glob
basis_base = None
for path in sorted(glob.glob("claude/telemetry/*.json"), reverse=True):
    try:
        with open(path) as f:
            rec = json.load(f)
    except Exception:
        continue
    for att in rec.get("attempts") or []:
        val = att.get("validation")
        if val and val.get("claims"):
            basis_base = rec
            break
    if basis_base:
        break

def set_basis(rec, value):
    rec2 = copy.deepcopy(rec)
    for att in rec2.get("attempts") or []:
        val = att.get("validation")
        if val and val.get("claims"):
            row = val["claims"][0]
            if isinstance(row, str):
                val["claims"][0] = {"value": row, "claim_basis": value}
            else:
                row["claim_basis"] = value
            return rec2
    return None

if basis_base is None:
    print("[ckpt] FAIL: no corpus record with attempts[].validation.claims found")
    fails.append("claim_basis fixture source")
else:
    for value, ok in (("predicted", True), ("observed", True), ("vibes", False)):
        r = set_basis(basis_base, value)
        if r is None:
            print("[ckpt] FAIL: claims row vanished during mutation")
            fails.append("claim_basis mutation")
            break
        check(f"claim_basis {value}", r, ok)

sys.exit(1 if fails else 0)
PYEOF
[ $? -eq 0 ] || status=1

exit "$status"
