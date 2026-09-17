#!/usr/bin/env bash
# Blind checkpoint — rows 56 + 57: changelog record family, `aborted`.
# Authored at the desk from the request (2026-09-16 UTC), before any
# implementation existed; grades outcomes of the applied tree only.
# Runs from the staging root. Writes: a private tmpdir only.
# Exit 0 = every probe PASS/SKIP, 1 = a probe FAILed, 2 = script error.
set -u
trap 'echo "[ERROR] checkpoint script errored at line $LINENO"; exit 2' ERR
echo "checkpoint 56+57 v1: writes to nothing in the tree (tmpdir only)"
fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fails=$((fails + 1)); }
tmp="$(mktemp -d)"

python3 - <<'PY' || fails=$((fails + $?))
import copy, json, re, sys
from pathlib import Path
sys.path.insert(0, "bin")
fails = 0
def verdict(label, ok, detail=""):
    global fails
    print(("[PASS] " if ok else "[FAIL] ") + label + (f" — {detail}" if detail and not ok else ""))
    if not ok: fails += 1
try:
    import bale_validate, bale_report
    # --- row 57 ------------------------------------------------------
    schema = json.loads(Path("schemas/telemetry-record.schema.json").read_text())
    enum = schema["properties"]["attempts"]["items"]["properties"]["closure_reason"]["enum"]
    verdict("telemetry-schema-closure-enum-has-aborted", "aborted" in enum)
    verdict("closure-reasons-constant-has-aborted",
            "aborted" in bale_report.CLOSURE_REASONS)
    rec = json.loads(Path("tests/fixtures/stats_corpus/2026-06-16-fx-pack-close-001.json").read_text())
    ok_rec = copy.deepcopy(rec); ok_rec["attempts"][-1]["closure_reason"] = "aborted"
    bad_rec = copy.deepcopy(rec); bad_rec["attempts"][-1]["closure_reason"] = "vaporized"
    verdict("validate-telemetry-record-accepts-aborted-refuses-unknown",
            bale_validate.validate_telemetry_record(ok_rec) == []
            and bale_validate.validate_telemetry_record(bad_rec) != [],
            f"ok={bale_validate.validate_telemetry_record(ok_rec)}")
    # --- row 56 ------------------------------------------------------
    sp = Path("schemas/changelog-record.schema.json")
    verdict("changelog-schema-present-and-json", sp.is_file() and isinstance(json.loads(sp.read_text()), dict))
    fn = getattr(bale_validate, "validate_changelog_record", None)
    verdict("validate-changelog-record-exists", callable(fn))
    recs = sorted(Path("claude/changelog").glob("*.json")) if Path("claude/changelog").is_dir() else []
    first = json.loads(recs[0].read_text()) if recs else None
    verdict("changelog-first-record-is-this-bump-and-validates",
            bool(recs) and callable(fn) and fn(first) == []
            and first.get("version") == "0.4.35"
            and isinstance(first.get("surfaces"), list) and len(first["surfaces"]) >= 1
            and any("telemetry-record.schema.json" in json.dumps(s) for s in first["surfaces"]),
            f"records={[r.name for r in recs]} problems={fn(first) if (recs and callable(fn)) else None}")
    if callable(fn) and first:
        missing = copy.deepcopy(first); missing.pop("surfaces", None)
        verdict("validate-changelog-record-omitted-surfaces-is-loud", fn(missing) != [])
    else:
        verdict("validate-changelog-record-omitted-surfaces-is-loud", False, "no validator or record")
    # --- inventories -------------------------------------------------
    verdict("validate-sh-inventory-names-changelog-record",
            "changelog-record" in Path("validate.sh").read_text())
    verdict("release-lists-name-changelog-schema",
            "schemas/changelog-record.schema.json" in Path("scripts/build.sh").read_text()
            and "schemas/changelog-record.schema.json" in Path("install.sh").read_text())
    verdict("version-is-0-4-35", Path("bin/VERSION").read_text().strip() == "0.4.35")
    docs = Path("docs/CODE.md").read_text() + Path("docs/TARBALL.md").read_text()
    verdict("discipline-sentence-mentions-changelog-and-same-response",
            re.search(r"changelog.{0,300}same response|same response.{0,300}changelog",
                      docs, re.I | re.S) is not None)
except Exception as e:
    print(f"[FAIL] probe-errored: {type(e).__name__}: {e}"); fails += 1
sys.exit(fails)
PY

suites_ok=1
for pat in test_release_packaging.py test_closure_telemetry.py test_schema_embeds.py \
           test_global_doc_selfcontainment.py test_doc_crossrefs.py 'test_*changelog*.py'; do
  rc=0
  python3 -m unittest discover -s tests -p "$pat" >> "$tmp/suites.log" 2>&1 || rc=$?
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 5 ]; then suites_ok=0; echo "  suite failed: $pat"; fi
done
if [ "$suites_ok" -eq 1 ]; then pass "release-schema-and-doc-suites-pass"; else
  fail "release-schema-and-doc-suites-pass"; tail -30 "$tmp/suites.log"; fi
rm -rf "$tmp"
if [ "$fails" -ne 0 ]; then echo "checkpoint 56+57 v1: $fails probe(s) failed"; exit 1; fi
echo "checkpoint 56+57 v1: all probes passed"; exit 0
