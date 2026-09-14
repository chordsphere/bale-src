#!/usr/bin/env bash
# Blind checkpoint — sitting-close-deltas-6 (the claude/MASTER.md landing
# for the 2026-09-10..14 sitting). Authored blind from the request
# (TARBALL.md §7; PLANNER.md §4). Outcome contracts on preserved tokens
# only — sids, row anchors, the header's fixed form; never on authored
# prose. cwd = staged applied tree.
#
# Probes:
#   header-last-landed-by   the "Last landed by:" line names a
#                           sitting-close-deltas-6 sid
#   header-version-unbumped the title line still reads "v5 — 2026-08-16"
#                           (v-numbers mark regenerations, not closes)
#   row-75-done             row 75's heading line no longer reads IN FLIGHT
#                           and carries DONE
#   rows-78-79-exist        rows 78 and 79 exist as numbered board rows
#   close-block-names-sitting
#                           §3 contains this sitting's master sid
#   only-master-changed     no file other than claude/MASTER.md differs
#                           from the base tree (git status on staging)
# Exit: 0 all pass; 1 a probe failed; 2 the script itself errored.
set -u
[ -f claude/MASTER.md ] || { echo "[ERROR] claude/MASTER.md absent"; exit 2; }
failed=0
M=claude/MASTER.md
if grep -qE '^Last landed by: `2026-09-1[0-9]-sitting-close-deltas-6-[0-9]{3}`\.' "$M"; then echo "[PASS] header-last-landed-by"
else echo "[FAIL] header-last-landed-by: $(grep -m1 '^Last landed by:' "$M")"; failed=1; fi
if head -1 "$M" | grep -q '^# bale master-session state — v5 — 2026-08-16$'; then echo "[PASS] header-version-unbumped"
else echo "[FAIL] header-version-unbumped: $(head -1 "$M")"; failed=1; fi
row75=$(grep -m1 -E '^75\. \*\*' "$M")
if [ -n "$row75" ] && ! printf '%s' "$row75" | grep -q 'IN FLIGHT' && printf '%s' "$row75" | grep -q 'DONE'; then echo "[PASS] row-75-done"
else echo "[FAIL] row-75-done: ${row75:-row 75 heading not found}"; failed=1; fi
s4=$(awk '/^## 4\. The board/{f=1} /^## 5\. Contracts/{f=0} f' "$M")
if printf '%s\n' "$s4" | grep -qE '^78\. \*\*' && printf '%s\n' "$s4" | grep -qE '^79\. \*\*'; then echo "[PASS] rows-78-79-exist"
else echo "[FAIL] rows-78-79-exist (in §4): 78=$(printf '%s\n' "$s4" | grep -cE '^78\. \*\*') 79=$(printf '%s\n' "$s4" | grep -cE '^79\. \*\*')"; failed=1; fi
s3=$(awk '/^## 3\. In flight/{f=1} /^## 4\. The board/{f=0} f' "$M")
if printf '%s\n' "$s3" | grep -q '2026-09-11-continue-plan-001'; then echo "[PASS] close-block-names-sitting"
else echo "[FAIL] close-block-names-sitting: §3 never names 2026-09-11-continue-plan-001"; failed=1; fi
if command -v git >/dev/null 2>&1 && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  changed=$(git status --porcelain --untracked-files=all 2>/dev/null | awk '{print $2}' | grep -v '^claude/MASTER.md$' | grep -v '^\.bale' || true)
  if [ -z "$changed" ]; then echo "[PASS] only-master-changed"
  else echo "[FAIL] only-master-changed: $(echo "$changed" | tr '\n' ' ')"; failed=1; fi
else echo "[PASS] only-master-changed: (no git context in staging — not judged)"; fi
exit $failed
