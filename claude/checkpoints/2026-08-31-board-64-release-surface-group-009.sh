#!/usr/bin/env bash
# board-64 blind checkpoint v1 — runs from repo root in staging.
# Outcome contracts only. Exit 0 PASS, 1 HOLD, 2 defective oracle.
set -u
fail=0
python3 - <<'PYEOF'
import re, sys
try:
    text = open("BALE.md", encoding="utf-8").read()
except OSError as e:
    print(f"[P1-group-documented] ERROR reading BALE.md: {e}"); sys.exit(2)
norm = re.sub(r"\s+", " ", text)
if "release-surface" in norm:
    print("[P1-group-documented] PASS"); sys.exit(0)
print("[P1-group-documented] FAIL: BALE.md does not document release-surface"); sys.exit(1)
PYEOF
rc=$?; [ "$rc" -eq 2 ] && exit 2; [ "$rc" -ne 0 ] && fail=1
if python3 -m unittest discover -s tests >/dev/null 2>&1; then
  echo "[P2-suite] PASS"
else
  echo "[P2-suite] FAIL: full suite not green"; fail=1
fi
v="$(tr -d '[:space:]' < bin/VERSION 2>/dev/null)"
if [ "$v" = "0.4.19" ]; then
  echo "[P3-version-lane] PASS"
else
  echo "[P3-version-lane] FAIL: bin/VERSION is '$v', lane says bumpless at 0.4.19"; fail=1
fi
exit "$fail"
