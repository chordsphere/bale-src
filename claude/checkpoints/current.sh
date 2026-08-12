#!/usr/bin/env bash
# claude/checkpoints/current.sh - blind checkpoint, board-10 wave 2
# Sessions gated: board-10-network-grant (S2), board-10-wave1-deltas
# Sitting: 2026-08-10-continue-plan-001 (board-10 spec-intake repack)
# rev 2 (post-S2-merge): netprobe rebuilt after the S2 apply proved the
# original's two defects on live traffic — (a) it read the inherited
# /sys/class/net, which shows the MOUNTING namespace's devices at every
# depth (netns-inaccurate in-sandbox; /proc/net/dev is accurate via the
# prologue's fresh proc), and (b) it read a DEAD probe child's exit as
# "no interfaces", turning a prologue failure into a vacuous verdict.
# Probes now report NONLO/LOONLY/DEAD distinctly, and the grant-toggle
# probe capability-gates on this checkpoint's own namespace (a granted
# child inherits it, so an ungranted outer has nothing to show it).
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
    # netprobe <network-bool> ; prints exactly one of:
    #   NONLO   - the confined child sees a non-loopback interface
    #   LOONLY  - the confined child sees only lo
    #   DEAD:.. - the probe child did not run (never read as a verdict)
    # Kernel-truth surface: /proc/net/dev inside the child (the
    # prologue mounts fresh proc, so procfs tracks the child's own
    # netns). Never /sys/class/net: the inherited sysfs instance
    # shows the mounting namespace's devices at every depth.
    python3 - "$workdir" "$1" <<'PYEOF'
import sys, os
sys.path.insert(0, "bin")
import bale_sandbox
workdir, grant = sys.argv[1], sys.argv[2] == "1"
res = bale_sandbox.run_confined(
    ["sh", "-c",
     "tail -n +3 /proc/net/dev | cut -d: -f1 | tr -d ' ' | grep -qvx lo"
     " && echo NONLO || echo LOONLY"],
    staging=os.path.join(workdir, "staging"),
    log_path=os.path.join(workdir, "ckpt.log"),
    network=grant)
lines = (res.stdout or "").strip().splitlines()
if res.returncode == 0 and lines and lines[-1] in ("NONLO", "LOONLY"):
    print(lines[-1])
else:
    err = (res.stderr or "").strip().replace("\n", " ")[:200]
    print("DEAD: rc=%d %s" % (res.returncode, err))
PYEOF
  }

  floor=$(netprobe 0)
  case "$floor" in
    LOONLY) note "default: loopback-only, floor intact" ;;
    NONLO)  failck "default confinement shows a non-loopback interface: floor widened" ;;
    *)      failck "floor probe child did not run: $floor" ;;
  esac

  # Grant-toggle probe, capability-gated on this checkpoint's OWN
  # namespace: the granted child inherits it, so when the invoking
  # bale threaded no grant out here (pre-0.4.5 install, or a project
  # on the floor) there is nothing for the child to see and the
  # assertion is vacuous - skip loudly instead. Asserts for real on
  # every granted apply.
  if tail -n +3 /proc/net/dev | cut -d: -f1 | tr -d ' ' | grep -qvx lo; then
    granted=$(netprobe 1)
    case "$granted" in
      NONLO)  note "network=True: non-loopback visible, grant toggle works" ;;
      LOONLY) failck "network=True still shows loopback-only: grant toggle inert" ;;
      *)      failck "grant probe child did not run: $granted" ;;
    esac
  else
    note "SKIP grant-toggle probe: checkpoint's own namespace is loopback-only (no grant threaded by the invoking bale); asserts on the first granted apply"
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
