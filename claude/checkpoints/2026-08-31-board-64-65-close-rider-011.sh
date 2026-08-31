#!/usr/bin/env bash
# board-64/65 close-rider blind checkpoint v1 — repo root, staging.
# Exit 0 PASS, 1 HOLD, 2 defective oracle.
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
probe "P3-walk-line" "A configured \`release-surface\` include group joins the wizard walk, its three keys read as one unit."
probe "P4-output-line" "When the \`release-surface\` group engages, pack output carries an include-group row naming its additions."
if python3 -m unittest discover -s tests >/dev/null 2>&1; then
  echo "[P5-suite] PASS"
else
  echo "[P5-suite] FAIL: full suite not green"; fail=1
fi
exit "$fail"
