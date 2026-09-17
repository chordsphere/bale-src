#!/usr/bin/env bash
# Blind checkpoint — sitting close 11. Outcome anchors the brief fixes.
set -u
trap 'echo "[ERROR] checkpoint script errored at line $LINENO"; exit 2' ERR
echo "checkpoint close-11 v1: writes nothing"
fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fails=$((fails + 1)); }
M=claude/MASTER.md
chk() { if grep -qF -- "$2" "$M"; then pass "$1"; else fail "$1"; fi; }
if sed -n '1,20p' "$M" | grep -q 'Last landed by.*sitting-close-deltas-11'; then
  pass "header-last-landed-names-close-11"; else fail "header-last-landed-names-close-11"; fi
chk "sitting-record-names-continue-plan-006" "2026-09-16-continue-plan-006"
chk "sitting-record-names-stats-micro" "2026-09-17-stats-micro-001"
chk "sitting-record-names-fix-both" "2026-09-17-board-69-selfcontainment-fix-both-005"
chk "contracts-heading-2026-09-17" "New, ratified 2026-09-17"
chk "contracts-heading-2026-09-16" "New, ratified 2026-09-16"
chk "row-107-supersedes" "107."
chk "row-109-harness" "109."
chk "evidence-154" "154."
chk "contract-every-bump-has-record" "changelog"
python3 - <<'PY' || fails=$((fails + 1))
import re, sys
t = open("claude/MASTER.md", encoding="utf-8").read()
ok = all(re.search(rf"^{n}\. \*\*", t, re.M) for n in (147, 148, 149, 150, 151, 152, 153, 154))
print(("[PASS] " if ok else "[FAIL] ") + "evidence-147-to-154-are-numbered-entries")
sys.exit(0 if ok else 1)
PY
if [ "$fails" -ne 0 ]; then echo "checkpoint close-11 v1: $fails failed"; exit 1; fi
echo "checkpoint close-11 v1: all probes passed"; exit 0
