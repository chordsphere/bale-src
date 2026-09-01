#!/usr/bin/env bash
# Blind checkpoint — 2026-09-01-board-42-telemetry-fields (v1)
# Outcome contracts for the two wave-1 field additions and the folded
# retry-rider doc line. Exit: 0 PASS, 1 HOLD, 2 defective fixture.
# Probes: docs-read-accepts, docs-read-enforced, origin-accepts,
# origin-enforced, legacy-tolerant, rider-doc-present. All validation
# probes go through the repo's own validators (bin/bale_validate.py),
# so acceptance means the enforced surface, not a schema file's text.
set -u

ROOT=""
for d in "$PWD" "$PWD/.." "$PWD/../.."; do
  if [ -f "$d/bin/bale" ] && [ -f "$d/tests/harness.py" ]; then
    ROOT="$(cd "$d" && pwd)"
    break
  fi
done
if [ -z "$ROOT" ]; then
  echo "CHECKPOINT ERROR: cannot locate tree root from $PWD" >&2
  exit 2
fi

python3 - "$ROOT" <<'PYEOF'
import json, sys, tempfile
from pathlib import Path

ROOT = Path(sys.argv[1])
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "bin"))

def fail(msg):  # satisfies bale_validate's `from __main__ import fail` contract
    raise SystemExit(msg)
try:
    from harness import build_response_dir
    import bale_validate
except Exception as e:
    print(f"CHECKPOINT ERROR: import failed: {e}", file=sys.stderr)
    sys.exit(2)

results = []
def probe(label, ok, detail):
    results.append(ok)
    print(f"PROBE {label}: {'PASS' if ok else 'FAIL'} ({detail})")

try:
    RESPONSE_SCHEMA = bale_validate.load_schema("response-manifest.schema.json")
except BaseException as e:
    print(f"CHECKPOINT ERROR: cannot load response-manifest schema: {e}", file=sys.stderr)
    sys.exit(2)

def manifest_valid(m):
    errs = bale_validate.validate_against_schema(m, RESPONSE_SCHEMA)
    return (not errs), "; ".join(errs[:2])

# Baseline fixture: a real build_response_dir manifest plus a feedback
# block valid against today's closed shapes. Baseline invalid = exit 2.
td = tempfile.TemporaryDirectory(prefix="ckpt42-")
rdir = build_response_dir(
    Path(td.name) / "resp", "2026-09-01-ckpt42-fixture-000",
    summary="board-42 checkpoint fixture",
    entries=[{"path": "f.txt", "action": "modified",
              "reason": "fixture", "data": b"x\n"}])
base = json.loads((rdir / "manifest.json").read_text(encoding="utf-8"))
base["feedback"] = {
    "mechanical": {"response_kind": "normal", "schema_valid": True,
                    "mirror_agreement": {"changes_to_files": True,
                                          "files_to_changes": True},
                    "claims_subset": True},
    "self_reported": {"assumptions": [], "judgment_calls": [],
                       "budget_pressure": "none",
                       "includes_missing": [],
                       "compaction_occurred": {"occurred": False}},
}
ok, err = manifest_valid(base)
if not ok:
    print(f"CHECKPOINT ERROR: baseline fixture manifest invalid pre-perturbation: {err}",
          file=sys.stderr)
    sys.exit(2)

QROW = {
    "question": "fixture question",
    "context": "fixture context",
    "default_assumption": "fixture default",
    "why_blocked": "fixture blocker",
}
if bale_validate.validate_clarification_questions([dict(QROW)]):
    print("CHECKPOINT ERROR: baseline question row invalid pre-perturbation",
          file=sys.stderr)
    sys.exit(2)

import copy
# --- docs-read-accepts: list-of-strings docs_read validates ---------
m = copy.deepcopy(base)
m["feedback"]["self_reported"]["docs_read"] = ["CLAUDE.md sections 6 and 11", "PLANNER.md section 4"]
ok, err = manifest_valid(m)
probe("docs-read-accepts", ok,
      "docs_read list accepted in feedback.self_reported" if ok else f"rejected: {err}")

# --- docs-read-enforced: wrong-typed docs_read rejects --------------
m = copy.deepcopy(base)
m["feedback"]["self_reported"]["docs_read"] = "CLAUDE.md"
ok, err = manifest_valid(m)
probe("docs-read-enforced", not ok,
      "wrong-typed docs_read rejected" if not ok else "string docs_read passed validation")

# --- origin-accepts: both enum values validate ----------------------
rows = [dict(QROW, origin="intent-gap"), dict(QROW, origin="probe-forbidden-environment")]
errs = bale_validate.validate_clarification_questions(rows)
probe("origin-accepts", not errs,
      "both origin values accepted on the question row" if not errs else f"rejected: {errs[:2]}")

# --- origin-enforced: out-of-vocabulary origin rejects --------------
errs = bale_validate.validate_clarification_questions([dict(QROW, origin="vibes")])
probe("origin-enforced", bool(errs),
      "out-of-vocabulary origin rejected" if errs else "bogus origin passed validation")

# --- legacy-tolerant: yesterday's shapes still validate -------------
ok, err = manifest_valid(base)
legacy_q = not bale_validate.validate_clarification_questions([dict(QROW)])
probe("legacy-tolerant", ok and legacy_q,
      "docs_read-less manifest and origin-less row both validate"
      if ok and legacy_q else f"legacy shapes broke: manifest={ok} ({err}), row={legacy_q}")

# --- rider-doc-present: the retry rider is documented ---------------
hay = (ROOT / "schemas" / "telemetry-record.schema.json").read_text(encoding="utf-8") \
      + (ROOT / "BALE.md").read_text(encoding="utf-8")
ok = "open_telemetry" in hay
probe("rider-doc-present", ok,
      "open_telemetry named in the schema description or BALE.md"
      if ok else "retry rider undocumented (open_telemetry absent from both)")

td.cleanup()
sys.exit(0 if all(results) else 1)
PYEOF
