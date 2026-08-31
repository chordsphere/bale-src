#!/usr/bin/env bash
# Blind checkpoint — board-66-schema-purge (rev1).
# Authored at the 2026-08-31-continue-plan-012 sitting, from the
# request, before implementation. Outcome contracts only.
# Runs with cwd = the staged (applied) tree. Exit: 0 pass, 1 a probe
# failed, 2 this script itself errored.
set -u

FILES="schemas/request-manifest.schema.json schemas/telemetry-record.schema.json schemas/escalation-record.schema.json schemas/exchange-record.schema.json schemas/bundle-manifest.schema.json"
fails=0

for f in $FILES; do
  if [ ! -f "$f" ]; then
    echo "[CKPT ERROR] expected schema missing: $f"
    exit 2
  fi
done

# Outcome 1: every file still parses as JSON.
for f in $FILES; do
  if python3 -c "import json,sys; json.load(open(sys.argv[1]))" "$f" 2>/dev/null; then
    echo "[CKPT PASS] json-parses: $f"
  else
    echo "[CKPT FAIL] json-parses: $f"
    fails=$((fails + 1))
  fi
done

# Outcome 2: citation residue is gone. Deny shapes: numbered board
# and evidence forms, the two project-local doc names, S-digit
# forms, session-letter residue. PLANNER.md citations are sanctioned
# and not denied.
for f in $FILES; do
  if grep -qE "board [0-9]|evidence [0-9]|BALE\.md|orchestration\.md|\bS[0-9]\b|session [A-D]\b" "$f"; then
    echo "[CKPT FAIL] citation-residue: $f"
    fails=$((fails + 1))
  else
    echo "[CKPT PASS] citation-residue: $f"
  fi
done

if [ "$fails" -gt 0 ]; then
  echo "[CKPT] $fails probe(s) failed"
  exit 1
fi
echo "[CKPT] all probes passed"
exit 0
