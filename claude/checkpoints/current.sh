#!/usr/bin/env bash
# claude/checkpoints/current.sh - blind checkpoint, board-10 wave 2
# Sessions gated: board-10-network-grant (S2), board-10-wave1-deltas
# Sitting: 2026-08-10-continue-plan-001 (board-10 spec-intake repack)
#
# Planner-authored from the requests, before implementation. Replaces
# the wave-1 guards (both wave-1 sessions are closed). Same single-path
# mechanism note as wave 1: guarded blocks, each arming only when its
# session's work is present, so either apply passes vacuously on the
# other's guard. Runs cwd = staging. Exit: 0 pass, 1 fail, 2 error.

set -u
status=0
note() { printf '[ckpt] %s\n' "$*"; }
failck() { printf '[ckpt] FAIL: %s\n' "$*"; status=1; }

ran_any=0

# ---------- S2 guard: network grant + sandbox telemetry ----------
# Arms on the pinned schema field. The brief pins: telemetry fields
# named exactly sandbox_escaped and network_grant_exercised; a
# network=True keyword on run_confined. Default-off is re-asserted so
# the grant work cannot have widened the floor.
if grep -q "sandbox_escaped" schemas/telemetry-record.schema.json 2>/dev/null; then
  ran_any=1
  note "S2 guard armed: sandbox_escaped present in telemetry schema"

  if grep -q "network_grant_exercised" schemas/telemetry-record.schema.json; then
    note "schema field present: network_grant_exercised"
  else
    failck "pinned schema field missing: network_grant_exercised"
  fi

  workdir=$(mktemp -d) || { note "ERROR: mktemp failed"; exit 2; }
  trap 'rm -rf "$workdir"' EXIT
  mkdir -p "$workdir/staging"

  netprobe() {
    # netprobe <network-bool> ; exit 0 iff a non-loopback interface is
    # visible to the confined child (offline-safe visibility test)
    python3 - "$workdir" "$1" <<'PYEOF'
import sys, os
sys.path.insert(0, "bin")
import bale_sandbox
workdir, grant = sys.argv[1], sys.argv[2] == "1"
staging = os.path.join(workdir, "staging")
log = os.path.join(workdir, "ckpt.log")
res = bale_sandbox.run_confined(
    ["bash", "-c", "ls /sys/class/net | grep -qv '^lo$'"],
    staging=staging, log_path=log, network=grant)
sys.exit(res.returncode)
PYEOF
  }

  if netprobe 0; then
    failck "default confinement shows a non-loopback interface: floor widened"
  else
    note "default: loopback-only, floor intact"
  fi

  if netprobe 1; then
    note "network=True: host interfaces visible, grant toggle works"
  else
    failck "network=True still shows loopback-only: grant toggle inert"
  fi

  # VERSION rider: the tree still reports its version after extraction.
  v=$(python3 bin/bale --version 2>/dev/null || true)
  case "$v" in
    *0.4.5*) note "version reports 0.4.5 post-rider" ;;
    *) failck "bin/bale --version did not report 0.4.5 (got: ${v:-empty})" ;;
  esac
fi

# ---------- Deltas guard: MASTER.md wave-1 record ----------
if grep -qF "wave 1 landed" claude/MASTER.md 2>/dev/null; then
  ran_any=1
  note "deltas guard armed: board-10 row records wave 1"
  if grep -qF "forecast/include mismatch" claude/MASTER.md; then
    note "fold-in present: forecast/include mismatch warning"
  else
    failck "fold-in registry missing the forecast/include mismatch entry"
  fi
  if grep -qF "probe-salvage" claude/MASTER.md; then
    note "evidence present: probe-salvage pattern"
  else
    failck "evidence pile missing the probe-salvage entry"
  fi
fi

if [ "$ran_any" = 0 ]; then
  note "no wave-2 guard armed in this tree; checkpoint passes vacuously"
fi

exit "$status"
