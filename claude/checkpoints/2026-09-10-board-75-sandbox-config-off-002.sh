#!/usr/bin/env bash
# board-75 blind checkpoint v1 — sandbox-off by config. Outcome
# contracts; contradiction-pass done against the brief (no probe
# asserts bale.toml gains the key — the brief forbids that; no
# probe asserts the --no-sandbox flag's removal — it stays).
set -u
fail_count=0
probe() {
  local label="$1" rc="$2"
  if [ "$rc" -eq 0 ]; then echo "[PASS] $label"
  else echo "[FAIL] $label"; fail_count=$((fail_count + 1)); fi
}
for f in bin/bale_config.py schemas/telemetry-record.schema.json BALE.md; do
  [ -f "$f" ] || { echo "[CHECKPOINT-ERROR] missing $f"; exit 2; }
done

# P1 — the config surface exposes the key (runtime, not source-grep:
# whatever SANDBOX_VALUES' entry shape, its rendering names enabled).
py_out=$(python3 -c "
import sys; sys.path.insert(0,'bin')
import bale_config
print(bale_config.SANDBOX_VALUES)
" 2>&1) || { echo "[CHECKPOINT-ERROR] SANDBOX_VALUES import failed: $py_out"; exit 2; }
printf '%s' "$py_out" | grep -q "enabled"
probe "P1-config-surface-has-enabled" "$?"

# P2 — telemetry schema carries the required posture keys.
tr -s ' \n' '  ' < schemas/telemetry-record.schema.json \
  | grep -q "sandbox_confined"
rc=$?
tr -s ' \n' '  ' < schemas/telemetry-record.schema.json \
  | grep -q "sandbox_off_source"
rc2=$?
probe "P2-telemetry-posture-keys" "$([ "$rc" -eq 0 ] && [ "$rc2" -eq 0 ]; echo $?)"

# P3 — BALE.md documents the literal example.
tr -s ' \n' ' ' < BALE.md | grep -q "enabled = false"
probe "P3-balemd-enabled-false-example" "$?"

if [ "$fail_count" -gt 0 ]; then
  echo "checkpoint: HOLD ($fail_count probe(s) failed)"; exit 1
fi
echo "checkpoint: PASS (3/3)"; exit 0
