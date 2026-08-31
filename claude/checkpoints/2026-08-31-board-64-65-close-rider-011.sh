#!/usr/bin/env bash
# board-64/65 close-rider blind checkpoint v2 — repo root, staging.
# Amends v1 per the 2026-08-31 desk ruling: former P3 (wizard-walk
# line) dropped — flag ratified; former P4's needle replaced with the
# corrected engagement sentence. Exit 0 PASS, 1 HOLD, 2 defective.
set -u
fail=0
v="$(tr -d '[:space:]' < bin/VERSION 2>/dev/null)"
if [ "$v" = "0.4.20" ]; then echo "[P1-version] PASS"; else echo "[P1-version] FAIL: bin/VERSION is '$v', expected 0.4.20"; fail=1; fi
probe() {
  local label="$1" needle="$2"
  python3 - "$label" "$needle" <<'PYEOF'
import re, sys
label, needle = sys.argv[1], sys.argv[2]
try:
    text = open("BALE.md", encoding="utf-8").read()
except OSError as e:
    print(f"[{label}] ERROR reading BALE.md: {e}"); sys.exit(2)
norm = re.sub(r"\s+", " ", text)
want = re.sub(r"\s+", " ", needle).strip()
if want in norm:
    print(f"[{label}] PASS"); sys.exit(0)
print(f"[{label}] FAIL: sentence absent"); sys.exit(1)
PYEOF
  local rc=$?
  [ "$rc" -eq 2 ] && exit 2
  [ "$rc" -ne 0 ] && fail=1
}
probe "P2-stats-line" "Each stats class row carries a \`linkage\` aggregation over the records' \`feedback.mechanical.linkage\` stamps; unstamped classes render no fabricated zeros."
probe "P3-engagement-line" "When the \`release-surface\` group engages, pack output carries an include-group row."
if python3 -m unittest discover -s tests >/dev/null 2>&1; then
  echo "[P4-suite] PASS"
else
  echo "[P4-suite] FAIL: full suite not green"; fail=1
fi
exit "$fail"
