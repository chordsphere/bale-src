#!/usr/bin/env bash
# Blind checkpoint — wave 10 rider micro (slug rider-micro).
# Authored 2026-09-22 by the 2026-09-22-continue-plan-001 desk from the
# request, before any implementation existed (TARBALL.md §7). Outcome
# contracts only: what must be true of the applied tree, never how.
#
# Exit codes (TARBALL.md §7.5, read for this script as PLANNER.md §4
# says): 0 every probe passed or skipped by name; 1 at least one probe
# failed; 2 the script itself errored, including a failed control.
#
# Writes: a mktemp directory under ${TMPDIR:-/tmp} (captured output),
# removed on exit. Nothing else. Python runs with -B and
# PYTHONDONTWRITEBYTECODE=1, so no __pycache__.
set -u
export PYTHONDONTWRITEBYTECODE=1
export LC_ALL=C.UTF-8 2>/dev/null || export LC_ALL=C

FAILED=0
pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s — %s\n' "$1" "$2"; FAILED=1; }
skip() { printf '[SKIP] %s — %s\n' "$1" "$2"; }
die()  { printf '[ERROR] %s\n' "$1"; exit 2; }

ROOT="$(pwd)"
echo "checkpoint rider-micro v1: cwd $ROOT"
echo "writes: a temporary directory under ${TMPDIR:-/tmp} only"

command -v python3 >/dev/null 2>&1 || die "python3 not found"
[ -f bin/bale ]                              || die "bin/bale missing from the tree"
[ -f bin/VERSION ]                           || die "bin/VERSION missing from the tree"
[ -f schemas/telemetry-record.schema.json ]  || die "schemas/telemetry-record.schema.json missing from the tree"

WORK="$(mktemp -d "${TMPDIR:-/tmp}/rider-micro-ckpt.XXXXXX")" || die "mktemp failed"
trap 'rm -rf "$WORK"' EXIT

SCHEMA=schemas/telemetry-record.schema.json
SWEPT_SID="2026-09-21-continue-plan-005"
SWEEPER_SID="2026-09-21-continue-plan-008"
SWEPT_RECORD="claude/telemetry/$SWEPT_SID.json"
NEW_VERSION="0.4.41"

# ---------------------------------------------------------------------
# CONTROL (exit 2 on failure, never a probe): the inputs the probes
# read must exist and carry what the probes key on, or a probe below
# would grade nothing. The schema parses; the swept session's record
# is on the tree with swept_by stamped by the sweeper; the JSON
# helper below detects a missing key (a known-absent key must read as
# absent).
# ---------------------------------------------------------------------
python3 -B - "$SCHEMA" "$SWEPT_RECORD" "$SWEPT_SID" "$SWEEPER_SID" <<'EOF' || die "control failed: schema or swept record not as the desk read them"
import json, sys
s = json.load(open(sys.argv[1]))
a = s["properties"]["attempts"]["items"]["properties"]
assert "outcome" in a and isinstance(a["outcome"].get("enum"), list)
assert "no-such-key-xyz" not in a
r = json.load(open(sys.argv[2]))
assert r["session_id"] == sys.argv[3]
assert any(t.get("swept_by") == sys.argv[4] for t in r["attempts"]), "swept_by not on the record"
EOF
echo "control: schema parses; $SWEPT_SID carries swept_by $SWEEPER_SID; absent keys read absent"

# ---------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------

# 1. The bump.
if [ "$(tr -d '[:space:]' < bin/VERSION)" = "$NEW_VERSION" ]
then pass "bin-version-is-$NEW_VERSION"
else fail "bin-version-is-$NEW_VERSION" "bin/VERSION reads '$(tr -d '[:space:]' < bin/VERSION)'"
fi

# 2. The bump's changelog record, naming the schema among its surfaces.
if python3 -B - "claude/changelog/$NEW_VERSION.json" "$NEW_VERSION" <<'EOF'
import json, os, sys
if not os.path.isfile(sys.argv[1]):
    sys.exit(1)
r = json.load(open(sys.argv[1]))
ok = r.get("version") == sys.argv[2] and isinstance(r.get("surfaces"), list) and r["surfaces"]
ok = ok and any(e.get("path") == "schemas/telemetry-record.schema.json" for e in r["surfaces"])
sys.exit(0 if ok else 1)
EOF
then pass "changelog-$NEW_VERSION-record-names-the-schema"
else fail "changelog-$NEW_VERSION-record-names-the-schema" "claude/changelog/$NEW_VERSION.json must exist, carry version $NEW_VERSION, and list schemas/telemetry-record.schema.json among its surfaces"
fi

# 3–5. The schema's additive contract: two new attempt keys, one new
#      outcome value, record_version still 1, every existing value kept.
schema_probe() {  # label, python expression over `a` (attempt props) and `s` (schema)
  if python3 -B - "$SCHEMA" "$2" <<'EOF'
import json, sys
s = json.load(open(sys.argv[1]))
a = s["properties"]["attempts"]["items"]["properties"]
sys.exit(0 if eval(sys.argv[2]) else 1)
EOF
  then pass "$1"; else fail "$1" "$3"; fi
}
schema_probe "schema-attempt-declares-cause" \
  '"cause" in a' \
  "attempts[].properties lacks cause (the refusal stamped on a rejected attempt)"
schema_probe "schema-attempt-declares-bundle" \
  '"bundle" in a' \
  "attempts[].properties lacks bundle (the bundle an opened attempt came from)"
schema_probe "schema-outcome-enum-gains-relay-refused" \
  '"relay-refused" in a["outcome"]["enum"] and "relay-refused" in s["properties"]["outcome"]["enum"]' \
  "relay-refused must be in both outcome enums (attempt and envelope)"
schema_probe "schema-stays-additive" \
  's["properties"]["record_version"].get("type") == "integer" and s["properties"]["record_version"].get("minimum") == 1 and "enum" not in s["properties"]["record_version"] and set(["opened","applied","held","reverted","rejected","bailout","scope-drift-refused","required-check-refused","base-drift-refused","unlocked","rolled-back","re-applied"]) <= set(a["outcome"]["enum"]) and set(["apply","retry","revert","unlock","pack","rollback","handoff"]) <= set(a["command"]["enum"]) and "swept_by" in a and "superseded_by" in a and set(a["provenance"]["properties"]) >= {"work_class","packer","packed_at"}' \
  "record_version must stay the integer >= 1 it is (additive change, no shape bump) and every 0.4.40 outcome, command, attempt key and provenance key must remain"

# 6. The whole telemetry corpus still reads under the new schema.
if python3 -B bin/bale stats --json > "$WORK/stats.json" 2> "$WORK/stats.err"
then pass "stats-reads-the-whole-corpus"
else fail "stats-reads-the-whole-corpus" "$(tail -3 "$WORK/stats.err" | tr '\n' ';')"
fi

# 7. 104b's Proposal 1: the dossier says who swept a swept session,
#    in the human report and in the attempt view.
python3 -B bin/bale stats --sid "$SWEPT_SID" > "$WORK/dossier.txt" 2>&1; rc1=$?
python3 -B bin/bale stats --sid "$SWEPT_SID" --json > "$WORK/dossier.json" 2>/dev/null; rc2=$?
if [ "$rc1" -eq 0 ] && [ "$rc2" -eq 0 ] && grep -q "swept by $SWEEPER_SID" "$WORK/dossier.txt" \
   && python3 -B - "$WORK/dossier.json" "$SWEEPER_SID" <<'EOF'
import json, sys
d = json.load(open(sys.argv[1]))
sys.exit(0 if any(t.get("swept_by") == sys.argv[2] for t in d.get("attempts", [])) else 1)
EOF
then pass "stats-dossier-names-the-sweeper"
else fail "stats-dossier-names-the-sweeper" "exit $rc1/$rc2; the human dossier must carry 'swept by $SWEEPER_SID' and the --json attempt view a swept_by key with that value"
fi

# 8. The apply-, stats-, relay-, open- and telemetry-side suites are
#    green on the landed tree (dotted form, from the repo root).
if python3 -B -m unittest tests.test_rollback_telemetry tests.test_stats_drilldown \
     tests.test_stats_aggregation tests.test_schema_embeds tests.test_provenance_at_open \
     tests.test_open_verb tests.test_relay_verb tests.test_apply_preflight \
     tests.test_telemetry_promotion tests.test_telemetry_extensions \
     tests.test_changelog_record tests.test_release_packaging > "$WORK/suites.out" 2>&1
then pass "bin-side-suites-green"
else fail "bin-side-suites-green" "$(grep -E '^(FAIL|ERROR):' "$WORK/suites.out" | head -5 | tr '\n' ';')"
fi

# 9. Disjointness: nothing landed on the tools micro's forecast or on
#    the four docs it does not hold either. HEAD is the base at apply;
#    SKIP by name without git.
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  if git diff --quiet HEAD -- tools docs tests/test_craft_response.py tests/test_response_lint.py 2>/dev/null
  then pass "sibling-forecast-and-docs-untouched"
  else fail "sibling-forecast-and-docs-untouched" "$(git diff --name-only HEAD -- tools docs tests/test_craft_response.py tests/test_response_lint.py | tr '\n' ' ')"
  fi
else
  skip "sibling-forecast-and-docs-untouched" "no git HEAD in this tree; the apply-side run has one"
fi

echo "checkpoint rider-micro v1: done"
exit "$FAILED"
