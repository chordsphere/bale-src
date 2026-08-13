#!/usr/bin/env bash
# claude/checkpoints/current.sh - blind checkpoint, board-10 wave 6
# Sessions gated: board-10-closeout-deltas, board-10-per-sid-checkpoints (S7)
# Sitting: 2026-08-10-continue-plan-001 (board-10 spec-intake repack)
#
# Planner-authored from the requests before implementation; fixture
# paths dry-run at authoring. This is the last shared-path checkpoint:
# the S7 session it gates retires the pattern. Guarded blocks as in
# every prior wave. Runs cwd = staging. Exit: 0 pass, 1 fail, 2 error.

set -u
status=0
note() { printf '[ckpt] %s\n' "$*"; }
failck() { printf '[ckpt] FAIL: %s\n' "$*"; status=1; }

ran_any=0

# ---------- Close-out deltas guard ----------
if grep -qF "arc build complete" claude/MASTER.md 2>/dev/null; then
  ran_any=1
  note "close-out guard armed: board-10 row records the arc build complete"
  for phrase in "dry-run" "stats read sides deferred" "packaging-list coupling" "per-sid checkpoint"; do
    if grep -qF "$phrase" claude/MASTER.md; then
      note "anchor present: $phrase"
    else
      failck "anchor phrase missing: $phrase"
    fi
  done
  if grep -qF "60.8" claude/MASTER.md; then
    note "operator suite-runtime figure recorded"
  else
    failck "the measured operator suite runtime is not recorded"
  fi
  if grep -qE '4 \+ 3 \+ 1 \+ 2' claude/MASTER.md; then
    failck "the stale watches-preamble enumeration survived the true-up"
  else
    note "watches preamble trued up"
  fi
fi

# ---------- S7 guard: per-sid checkpoint resolution ----------
if grep -qF '{sid}' BALE.md 2>/dev/null; then
  ran_any=1
  note "S7 guard armed: BALE.md documents the {sid} placeholder"
  python3 - <<'PYEOF'
import sys
sys.path.insert(0, "bin")
import bale_config

fails = []
def check(name, got, want):
    ok = got == want
    print(f"[ckpt] {'ok' if ok else 'FAIL'}: {name}" + ("" if ok else f" :: got {got!r}"))
    if not ok:
        fails.append(name)

r = bale_config.resolve_checkpoint_path
check("literal path unchanged (compat)",
      r("claude/checkpoints/current.sh", "2026-01-01-example-001"),
      "claude/checkpoints/current.sh")
check("placeholder substituted",
      r("claude/checkpoints/{sid}.sh", "2026-01-01-example-001"),
      "claude/checkpoints/2026-01-01-example-001.sh")

sys.exit(1 if fails else 0)
PYEOF
  [ $? -eq 0 ] || status=1
fi

if [ "$ran_any" = 0 ]; then
  note "no wave-6 guard armed in this tree; checkpoint passes vacuously"
fi

exit "$status"
