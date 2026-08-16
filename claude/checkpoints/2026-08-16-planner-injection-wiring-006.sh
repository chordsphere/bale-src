#!/usr/bin/env bash
# checkpoint-planner-wiring-v2.sh
# Blind checkpoint for the planner-injection-wiring supersession
# repack. Authored at the planner desk, 2026-08-16, from the request
# and the superseded session's probe findings. Outcome-only.
#
# Writes to: nothing. Read-only assertions against the staging copy.

set -u
fails=0

check() {
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then
    printf '[PASS] %s\n' "$label"
  else
    printf '[FAIL] %s\n' "$label"
    fails=$((fails + 1))
  fi
}

# --- The tool knows the fifth doc -----------------------------------
check "bin/ names PLANNER.md"                 grep -rq "PLANNER.md" bin/

# --- The release surfaces cover it ----------------------------------
check "build.sh release list has the row"     grep -q "docs/PLANNER.md" scripts/build.sh
check "install.sh layout has the row"         grep -q "docs/PLANNER.md" install.sh

# --- The two deferred BALE.md sites are trued up --------------------
check "BALE.md: inject-all-four gone"         bash -c '! grep -q "Inject all four" BALE.md'
check "BALE.md: four-real-files note gone"    bash -c '! grep -q "four global docs are real files" BALE.md'

# --- Schemas admit the fifth key without requiring it ---------------
check "response schema names PLANNER.md"      grep -q "PLANNER.md" schemas/response-manifest.schema.json
check "request schema names PLANNER.md"       grep -q "PLANNER.md" schemas/request-manifest.schema.json

# --- The suites hold, on the runner this repo actually uses ---------
check "schema-embed sync passes"      python3 -m unittest tests.test_schema_embeds
check "release packaging passes"      python3 -m unittest tests.test_release_packaging
check "self-containment guard passes" python3 -m unittest tests.test_global_doc_selfcontainment
check "crossref guard passes"         python3 -m unittest tests.test_doc_crossrefs

# (Deliberately unasserted: the required-vs-allowed shape of the
# schema admission — that is mechanism, reviewed at the desk, and a
# grep cannot see additionalProperties semantics honestly. Also the
# version bump, per the v1 rationale.)

# --- Verdict ----------------------------------------------------------
if [ "$fails" -eq 0 ]; then
  printf 'checkpoint: PASS\n'
  exit 0
else
  printf 'checkpoint: FAIL (%d)\n' "$fails"
  exit 1
fi
