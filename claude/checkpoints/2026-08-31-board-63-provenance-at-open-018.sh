#!/usr/bin/env bash
# Blind checkpoint — board-63-provenance-at-open (rev1).
# Authored at the 2026-08-31-continue-plan-012 sitting, from the
# request, before implementation. Outcome contracts only.
# Runs with cwd = the staged (applied) tree; the E2E probe exercises
# the STAGED tool in a scratch repo created inside staging (writes
# stay confined; no network needed). Exit: 0 pass, 1 a probe failed,
# 2 this script itself errored.
set -u
fails=0
# Outcome (schema half): the record shape's one home documents the
# two fields.
for field in work_class packer; do
  if grep -qF "$field" schemas/telemetry-record.schema.json; then
    echo "[CKPT PASS] schema-documents-$field"
  else
    echo "[CKPT FAIL] schema-documents-$field"; fails=$((fails + 1))
  fi
done
# Outcome (behavior half): a fresh open leaves a telemetry record
# carrying both fields, before any close.
SCRATCH=".ckpt-63-scratch"
rm -rf "$SCRATCH"; mkdir -p "$SCRATCH"
( cd "$SCRATCH" \
  && git init -q . \
  && git config user.email ckpt@bale \
  && git config user.name ckpt \
  && echo x > f && git add f && git commit -qm init ) \
  || { echo "[CKPT ERROR] scratch repo setup failed"; exit 2; }
PACK_JSON="$SCRATCH/.pack-report.json"
( cd "$SCRATCH" && python3 ../bin/bale pack "checkpoint open-stamp probe" --slug ckpt63-probe --read-only --no-readme --work-class meta --packer ckpt-oracle --json </dev/null >".pack-report.json" 2>".pack-stderr" )
if [ $? -ne 0 ]; then
  echo "[CKPT FAIL] scratch-pack-succeeds"
  fails=$((fails + 1))
else
  echo "[CKPT PASS] scratch-pack-succeeds"
  SID=$(python3 -c "import json,sys; d=json.load(open(sys.argv[1])); print(d.get('sid') or d.get('session_id') or '')" "$PACK_JSON" 2>/dev/null)
  REC="$SCRATCH/claude/telemetry/$SID.json"
  if [ -n "$SID" ] && [ -f "$REC" ]; then
    echo "[CKPT PASS] open-writes-telemetry-record"
    for field in work_class packer; do
      if grep -qF "\"$field\"" "$REC"; then
        echo "[CKPT PASS] open-record-carries-$field"
      else
        echo "[CKPT FAIL] open-record-carries-$field"; fails=$((fails + 1))
      fi
    done
  else
    echo "[CKPT FAIL] open-writes-telemetry-record"
    fails=$((fails + 3))
  fi
fi
rm -rf "$SCRATCH"
if [ "$fails" -gt 0 ]; then echo "[CKPT] $fails probe(s) failed"; exit 1; fi
echo "[CKPT] all probes passed"; exit 0
