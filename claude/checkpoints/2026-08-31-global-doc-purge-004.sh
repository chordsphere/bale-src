#!/usr/bin/env bash
# Blind checkpoint — global-doc-purge
# Authored at the 2026-08-31 desk, from the request, before any
# implementation exists. Outcome contracts only: the citation shapes
# are gone, the two verbatim landings are present, and the extended
# guard actually fires on each seeded shape. No assertion touches
# mechanism — how the guard implements its deny set is not graded.
# Runs in staging with cwd at the staged repo root. Writes only to
# scratch dirs it creates under cwd and removes on exit.
set -u

fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fails=$((fails + 1)); }

GLOBALS="docs/CLAUDE.md docs/TARBALL.md docs/DOCS.md docs/CODE.md docs/PLANNER.md"
for f in $GLOBALS tools/craft_response.py tools/response_lint.py \
         tests/test_global_doc_selfcontainment.py; do
  [ -f "$f" ] || { echo "[FAIL] staged tree missing $f"; exit 1; }
done

# --- Scenario 1: citation shapes absent from the five globals -------
if grep -Eiq 'evidence [0-9]' $GLOBALS; then
  fail "evidence-N citations remain:"; grep -Ein 'evidence [0-9]' $GLOBALS | head -5
else pass "no evidence-N citations in the globals"; fi

if grep -Eiq '\bboard( row)? [0-9]' $GLOBALS; then
  fail "board-number citations remain:"; grep -Ein '\bboard( row)? [0-9]' $GLOBALS | head -5
else pass "no board-number citations in the globals"; fi

# --- Scenario 2: the two verbatim landings --------------------------
if grep -Eq 'PLANNER\.md.{0,3}§15' docs/TARBALL.md; then
  pass "TARBALL.md 5.9.2 cites PLANNER.md §15"
else fail "TARBALL.md carries no PLANNER.md §15 citation"; fi

if grep -Fq "own orchestration" docs/TARBALL.md; then
  fail "stale orchestration-documentation pointer still present in TARBALL.md"
else pass "stale orchestration-documentation pointer gone"; fi

if grep -Fq 'bale amend-checkpoint' docs/PLANNER.md; then
  pass "PLANNER.md names bale amend-checkpoint"
else fail "PLANNER.md does not name bale amend-checkpoint"; fi

# --- Scenario 3: crafter pointer fixed ------------------------------
if grep -Fq '§6.7 there' tools/craft_response.py; then
  fail "crafter still carries the dangling design-doc section pointer"
else pass "crafter design-doc section pointer gone"; fi

# --- Scenario 3b: schema purged, embed parity held ------------------
if grep -Eiq 'orchestration\.md|\bboard( row)? [0-9]' schemas/response-manifest.schema.json; then
  fail "response-manifest schema still carries project citations"
else pass "response-manifest schema descriptions purged"; fi

if python3 -m unittest discover -s tests -p 'test_schema_embeds.py' \
     >/dev/null 2>&1; then
  pass "lint embed stays JSON-equal to the purged schema"
else fail "schema/lint embed parity broken (test_schema_embeds)"; fi

# --- Scenario 4: guard passes on the purged tree --------------------
if python3 -m unittest discover -s tests \
     -p 'test_global_doc_selfcontainment.py' >/dev/null 2>&1; then
  pass "self-containment guard passes on the staged tree"
else fail "self-containment guard fails on the staged tree"; fi

# --- Scenarios 5-7: guard fires on each seeded shape ----------------
# One fresh fixture per scenario (never shared). Each copies the
# staged docs/, tools/, and the guard test into its own scratch tree,
# seeds exactly one violation, and requires the guard to FAIL there.
tripwire() {
  # tripwire <label> <target-relpath> <seed-text>
  local label="$1" target="$2" seed="$3"
  local scratch; scratch="$(mktemp -d ./.ckpt-scratch-XXXXXX)"
  mkdir -p "$scratch/tests"
  cp -r docs "$scratch/docs"
  cp -r tools "$scratch/tools"
  cp tests/test_global_doc_selfcontainment.py "$scratch/tests/"
  printf '\n%s\n' "$seed" >> "$scratch/$target"
  if ( cd "$scratch" && python3 -m unittest discover -s tests \
         -p 'test_global_doc_selfcontainment.py' >/dev/null 2>&1 ); then
    fail "tripwire not caught: $label"
  else
    pass "guard fires on seeded $label"
  fi
  rm -rf "$scratch"
}

tripwire "evidence-N citation in a global" "docs/CLAUDE.md"  "(evidence 12)"
tripwire "board-number citation in a global" "docs/CODE.md"  "per board 33"
tripwire "project-doc pointer in an injected tool" \
         "tools/craft_response.py" "# see BALE.md for the format"

# --------------------------------------------------------------------
if [ "$fails" -eq 0 ]; then
  echo "[CHECKPOINT PASS] purge landed and the guard provably covers it"
  exit 0
else
  echo "[CHECKPOINT HOLD] $fails scenario(s) failed"
  exit 1
fi
