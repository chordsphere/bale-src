#!/usr/bin/env bash
# Blind checkpoint — wave 10 tools micro (slug tools-micro).
# Authored 2026-09-22 by the 2026-09-22-continue-plan-001 desk from the
# request, before any implementation existed (TARBALL.md §7). Outcome
# contracts only: what must be true of the applied tree, never how.
#
# Exit codes (TARBALL.md §7.5, read for this script as PLANNER.md §4
# says): 0 every probe passed or skipped by name; 1 at least one probe
# failed; 2 the script itself errored, including a failed control.
#
# Writes: a mktemp directory under ${TMPDIR:-/tmp} (fixture response
# dirs and request manifests), removed on exit. Nothing else. Python is
# run with -B and PYTHONDONTWRITEBYTECODE=1, so no __pycache__.
set -u
export PYTHONDONTWRITEBYTECODE=1
export LC_ALL=C.UTF-8 2>/dev/null || export LC_ALL=C

FAILED=0
pass() { printf '[PASS] %s\n' "$1"; }
fail() { printf '[FAIL] %s — %s\n' "$1" "$2"; FAILED=1; }
skip() { printf '[SKIP] %s — %s\n' "$1" "$2"; }
die()  { printf '[ERROR] %s\n' "$1"; exit 2; }

ROOT="$(pwd)"
echo "checkpoint tools-micro v1: cwd $ROOT"
echo "writes: a temporary directory under ${TMPDIR:-/tmp} only"

command -v python3 >/dev/null 2>&1 || die "python3 not found"
[ -f tools/response_lint.py ]   || die "tools/response_lint.py missing from the tree"
[ -f tools/craft_response.py ]  || die "tools/craft_response.py missing from the tree"
[ -f docs/TARBALL.md ]          || die "docs/TARBALL.md missing from the tree"
[ -f tests/test_craft_response.py ] || die "tests/test_craft_response.py missing from the tree"

WORK="$(mktemp -d "${TMPDIR:-/tmp}/tools-micro-ckpt.XXXXXX")" || die "mktemp failed"
trap 'rm -rf "$WORK"' EXIT

# ---------------------------------------------------------------------
# Fixture: a crafter-seeded response directory whose ONLY lint finding
# on the 0.4.40 base is the seeded feedback block (the four
# lint-computable placeholders). Built mechanically here so the probe
# grades the tool, never a hand-written manifest.
# ---------------------------------------------------------------------
SID="2026-09-22-fixture-001"
ZERO="0000000000000000000000000000000000000000000000000000000000000000"

write_request() {  # $1 path, $2 resolved_scope JSON array, $3 readme JSON
  cat > "$1" <<EOF
{"session_id":"$SID","project":"fx","goal":"fixture","depends_on":{"previous_response":null,"previous_probe":null,"superseded_session":null},"constraints":[],"out_of_scope":[],"expects_probe":"claude-decides","context_included":["context/tools/a.py"],"resolved_scope":$2,"readme":$3,"provenance":{"bale_version":"0.4.40","contract_docs":{"CLAUDE.md":"$ZERO","TARBALL.md":"$ZERO","DOCS.md":"$ZERO","CODE.md":"$ZERO","PLANNER.md":"$ZERO"},"packer":"chordsphere","work_class":"code","checkpoint":null,"checkpoint_scope_admitted":false,"packed_at":"2026-09-22T00:00:00+00:00","base_files":{}}}
EOF
}

FILL="$WORK/fill.py"
cat > "$FILL" <<'EOF'
import json, sys
p = sys.argv[1]; m = json.load(open(p))
m["summary"] = "fixture"
for c in m["changes"]:
    c["action"] = "created"; c["reason"] = "fixture"
m["validation_will_run"] = ["syntax"]; m["claims"] = {"syntax": "pass"}
m["feedback"]["mechanical"]["provenance"]["model_identity"] = "fixture"
sr = m["feedback"]["self_reported"]
sr["budget_pressure"] = "none"
sr["compaction_occurred"] = {"occurred": False, "disclosure_ref": None}
sr["docs_read"] = sys.argv[2:]
sr.pop("forecast_departures", None)   # the fixture declares no departure; probe 6 grades seeding
json.dump(m, open(p, "w"), indent=2)
EOF

# build_fixture DIR REQUEST DOCS_READ... — a response dir seeded from
# REQUEST with one files/ path, tools/a.py, every judgment field
# filled and no forecast_departures declared, so only the seeded
# feedback block can fail the lint.
build_fixture() {
  local dir="$1" req="$2"; shift 2
  rm -rf "$dir"; mkdir -p "$dir/files/tools"
  printf 'x\n' > "$dir/files/tools/a.py"
  python3 -B tools/craft_response.py "$dir" --sid "$SID" --request "$req" --write >/dev/null 2>&1 \
    || die "the crafter could not build the fixture (its --request/--write path errored)"
  python3 -B "$FILL" "$dir/manifest.json" "$@" || die "fixture fill failed"
  printf '#!/usr/bin/env bash\necho "[PASS] syntax"\n' > "$dir/validation.sh"
}

REQ_OUT="$WORK/req-out.json";  write_request "$REQ_OUT" '["bin"]'   '{"path":"README.md","sha256":"'"$ZERO"'"}'
REQ_IN="$WORK/req-in.json";    write_request "$REQ_IN"  '["tools"]' '{"path":"README.md","sha256":"'"$ZERO"'"}'
REQ_NOREADME="$WORK/req-noreadme.json"; write_request "$REQ_NOREADME" '["tools"]' 'null'

# ---------------------------------------------------------------------
# CONTROL (exit 2 on failure, never a probe): the fixture must show the
# seeded-block finding to the lint, and the lint's plain run must
# report it — otherwise the emit-exit probe below grades nothing.
# ---------------------------------------------------------------------
build_fixture "$WORK/ctl" "$REQ_IN" "CLAUDE.md" "README.md"
python3 -B tools/response_lint.py "$WORK/ctl" > "$WORK/ctl.out" 2>&1
grep -q '^\[FAIL\] feedback-block' "$WORK/ctl.out" \
  || die "control: the fixture's seeded feedback block is not a lint finding; the fixture no longer exercises the emit path"
python3 -B tools/response_lint.py "$WORK/ctl" --emit-feedback-mechanical > "$WORK/ctl.mech" 2>/dev/null
python3 -B - "$WORK/ctl/manifest.json" "$WORK/ctl.mech" <<'EOF' || die "control: pasting the emitted object over the seeded block did not lint clean"
import json, subprocess, sys
m = json.load(open(sys.argv[1])); mech = json.load(open(sys.argv[2]))
m["feedback"]["mechanical"].update(mech)
json.dump(m, open(sys.argv[1], "w"), indent=2)
rc = subprocess.run([sys.executable, "-B", "tools/response_lint.py", sys.argv[1].rsplit("/", 1)[0]],
                    capture_output=True).returncode
sys.exit(0 if rc == 0 else 1)
EOF
echo "control: fixture exercises the seeded block, and the pasted emission lints clean"

# ---------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------

# 1. Item 1: emit mode exits 0 when the object was emitted, even though
#    the seeded block it exists to refresh is the run's finding.
build_fixture "$WORK/p1" "$REQ_IN" "CLAUDE.md" "README.md"
python3 -B tools/response_lint.py "$WORK/p1" --emit-feedback-mechanical > "$WORK/p1.out" 2> "$WORK/p1.err"
rc=$?
if [ "$rc" -eq 0 ] && python3 -B - "$WORK/p1.out" <<'EOF'
import json, sys
o = json.load(open(sys.argv[1]))
sys.exit(0 if set(o) >= {"response_kind", "schema_valid", "mirror_agreement", "claims_subset"} else 1)
EOF
then pass "lint-emit-exit-zero-on-seeded-block"
else fail "lint-emit-exit-zero-on-seeded-block" "exit $rc; stdout must carry the four-key object and the exit must be 0"
fi

# 2. Item 3: --request lets the lint see the forecast; a changes[] path
#    outside resolved_scope with no forecast_departures entry is named.
build_fixture "$WORK/p2" "$REQ_OUT" "CLAUDE.md" "README.md"
python3 -B tools/response_lint.py "$WORK/p2" --request "$REQ_OUT" > "$WORK/p2.out" 2>&1
rc=$?
if [ "$rc" -ne 2 ] && grep -q 'tools/a.py' "$WORK/p2.out" && grep -q 'forecast_departures' "$WORK/p2.out"
then pass "lint-request-flag-names-undeclared-forecast-departure"
else fail "lint-request-flag-names-undeclared-forecast-departure" "exit $rc; with --request the lint must accept the flag and name tools/a.py beside forecast_departures"
fi

# 3. The same run must be silent about a path INSIDE the forecast.
build_fixture "$WORK/p3" "$REQ_IN" "CLAUDE.md" "README.md"
python3 -B tools/response_lint.py "$WORK/p3" --request "$REQ_IN" > "$WORK/p3.out" 2>&1
rc=$?
if [ "$rc" -ne 2 ] && ! grep -q 'forecast_departures' "$WORK/p3.out"
then pass "lint-request-flag-silent-inside-forecast"
else fail "lint-request-flag-silent-inside-forecast" "exit $rc; an in-forecast path must raise no forecast_departures line"
fi

# 4. The docs_read rider: readme key non-null and docs_read without
#    README.md warns, naming README.md; never a finding, never exit 2.
build_fixture "$WORK/p4" "$REQ_IN" "CLAUDE.md"
python3 -B tools/response_lint.py "$WORK/p4" --request "$REQ_IN" > "$WORK/p4.out" 2>&1
rc=$?
if [ "$rc" -ne 2 ] && grep '^\[WARN\]' "$WORK/p4.out" | grep -q 'README' \
   && grep -qi 'README.md' "$WORK/p4.out"
then pass "lint-warns-readme-shipped-but-not-read"
else fail "lint-warns-readme-shipped-but-not-read" "exit $rc; a non-null readme key with README.md absent from docs_read must print a [WARN] line naming README.md"
fi

# 5. …and stays silent when README.md is listed, or no brief shipped.
build_fixture "$WORK/p5a" "$REQ_IN" "CLAUDE.md" "README.md"
build_fixture "$WORK/p5b" "$REQ_NOREADME" "CLAUDE.md"
python3 -B tools/response_lint.py "$WORK/p5a" --request "$REQ_IN" > "$WORK/p5a.out" 2>&1; rca=$?
python3 -B tools/response_lint.py "$WORK/p5b" --request "$REQ_NOREADME" > "$WORK/p5b.out" 2>&1; rcb=$?
if [ "$rca" -ne 2 ] && [ "$rcb" -ne 2 ] \
   && ! grep '^\[WARN\]' "$WORK/p5a.out" | grep -qi 'README' \
   && ! grep '^\[WARN\]' "$WORK/p5b.out" | grep -qi 'README'
then pass "lint-readme-warning-silent-when-read-or-absent"
else fail "lint-readme-warning-silent-when-read-or-absent" "exit $rca/$rcb; README.md listed, or readme null, must not warn"
fi

# 6. Doc lane Proposal 1: the crafter seeds forecast_departures from
#    --request for a files/ path outside resolved_scope, as {path, why}
#    with why empty (unfilled), and seeds nothing for an in-forecast path.
python3 -B tools/craft_response.py "$WORK/p6" --sid "$SID" --request "$REQ_OUT" > "$WORK/p6.json" 2>/dev/null
rm -rf "$WORK/p6"; mkdir -p "$WORK/p6/files/tools"; printf 'x\n' > "$WORK/p6/files/tools/a.py"
python3 -B tools/craft_response.py "$WORK/p6" --sid "$SID" --request "$REQ_OUT" > "$WORK/p6.json" 2>/dev/null
python3 -B tools/craft_response.py "$WORK/p6" --sid "$SID" --request "$REQ_IN"  > "$WORK/p6in.json" 2>/dev/null
if python3 -B - "$WORK/p6.json" "$WORK/p6in.json" <<'EOF'
import json, sys
out = json.load(open(sys.argv[1]))["feedback"]["self_reported"]
inn = json.load(open(sys.argv[2]))["feedback"]["self_reported"]
dep = out.get("forecast_departures")
ok = isinstance(dep, list) and any(
    isinstance(e, dict) and e.get("path") == "tools/a.py" and e.get("why") == "" for e in dep)
ok = ok and not [e for e in (inn.get("forecast_departures") or []) if e.get("path") == "tools/a.py"]
sys.exit(0 if ok else 1)
EOF
then pass "crafter-seeds-forecast-departures-from-request"
else fail "crafter-seeds-forecast-departures-from-request" "with --request, an out-of-forecast files/ path must appear as {path, why: \"\"} and an in-forecast path must not"
fi

# 7. TARBALL.md §5.4's sentence about the crafter not seeding the field
#    is gone (the one-line edit the proposal named).
if ! grep -q "does not seed the field, so it is the worker's to add" docs/TARBALL.md
then pass "tarball-5.4-crafter-does-not-seed-sentence-gone"
else fail "tarball-5.4-crafter-does-not-seed-sentence-gone" "docs/TARBALL.md §5.4 still says the crafter does not seed the field"
fi

# 8. The §7.5 rider: the brief's VERBATIM sentence, present in §7.5
#    (between its heading and §7.6's), whitespace-normalized so the
#    worker's line wrapping is free.
S75_SENTENCE='The blind checkpoint (§7) is read against the same three codes: bale takes its `0`, `1`, and `2` to mean exactly what they mean for `validation.sh`, so a checkpoint that exits `2` is a defective oracle, never a verdict on the work.'
if python3 -B - docs/TARBALL.md "$S75_SENTENCE" <<'EOF'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
start = text.find("### 7.5 Exit codes"); end = text.find("### 7.6", start)
sect = text[start:end] if start >= 0 and end > start else ""
norm = lambda s: re.sub(r"\s+", " ", s)
sys.exit(0 if start >= 0 and norm(sys.argv[2]) in norm(sect) else 1)
EOF
then pass "tarball-7.5-checkpoint-exit-codes-sentence-verbatim"
else fail "tarball-7.5-checkpoint-exit-codes-sentence-verbatim" "docs/TARBALL.md §7.5 lacks the brief's VERBATIM sentence (wrapping is free; wording is not)"
fi

# 9. The craft path guard rider: ExchangeBlockParity.setUpClass no
#    longer carries the redundant tests/-on-path guard.
if ! grep -q 'tests_dir = str(Path(__file__).resolve().parent)' tests/test_craft_response.py
then pass "tests-craft-path-guard-dropped"
else fail "tests-craft-path-guard-dropped" "tests/test_craft_response.py still carries the tests/-on-path guard line"
fi

# 10. The tools and doc suites are green on the landed tree (dotted
#     form, from the repo root; the self-containment guard rides here).
if python3 -B -m unittest tests.test_craft_response tests.test_response_lint \
     tests.test_global_doc_selfcontainment tests.test_doc_crossrefs \
     tests.test_sanctioned_pairs tests.test_schema_embeds > "$WORK/suites.out" 2>&1
then pass "tools-and-doc-suites-green"
else fail "tools-and-doc-suites-green" "$(grep -E '^(FAIL|ERROR):' "$WORK/suites.out" | head -5 | tr '\n' ';')"
fi

# 11. Disjointness: nothing landed on the rider micro's forecast or the
#     other four docs. HEAD is the base at apply; SKIP by name without git.
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  if git diff --quiet HEAD -- bin schemas BALE.md claude/changelog docs/CLAUDE.md docs/DOCS.md docs/CODE.md docs/PLANNER.md 2>/dev/null
  then pass "sibling-forecast-and-other-docs-untouched"
  else fail "sibling-forecast-and-other-docs-untouched" "$(git diff --name-only HEAD -- bin schemas BALE.md claude/changelog docs/CLAUDE.md docs/DOCS.md docs/CODE.md docs/PLANNER.md | tr '\n' ' ')"
  fi
else
  skip "sibling-forecast-and-other-docs-untouched" "no git HEAD in this tree; the apply-side run has one"
fi

echo "checkpoint tools-micro v1: done"
exit "$FAILED"
