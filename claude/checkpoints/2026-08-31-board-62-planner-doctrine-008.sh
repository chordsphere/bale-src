#!/usr/bin/env bash
# board-62 blind checkpoint v1 — runs from repo root in staging.
# Outcome contracts only: two VERBATIM sentences present in
# docs/PLANNER.md before the core banner (wrap-tolerant), guard
# suites green. Exit 0 PASS, 1 HOLD, 2 defective oracle.
set -u
fail=0

probe_sentence() {
  local label="$1" needle="$2"
  python3 - "$label" "$needle" <<'PYEOF'
import re, sys
label, needle = sys.argv[1], sys.argv[2]
try:
    text = open("docs/PLANNER.md", encoding="utf-8").read()
except OSError as e:
    print(f"[{label}] ERROR reading docs/PLANNER.md: {e}")
    sys.exit(2)
norm = re.sub(r"\s+", " ", text)
want = re.sub(r"\s+", " ", needle).strip()
banner = norm.find("PAST THE CORE.")
if banner < 0:
    print(f"[{label}] ERROR: core banner not found")
    sys.exit(2)
pos = norm.find(want)
if pos < 0:
    print(f"[{label}] FAIL: sentence absent")
    sys.exit(1)
if pos >= banner:
    print(f"[{label}] FAIL: sentence present but past the core banner")
    sys.exit(1)
print(f"[{label}] PASS")
sys.exit(0)
PYEOF
  local rc=$?
  if [ "$rc" -eq 2 ]; then exit 2; fi
  if [ "$rc" -ne 0 ]; then fail=1; fi
}

probe_sentence "P1-narrow-forecast" "When split sessions are meant to run concurrently, each pack carries a narrow \`--write\` forecast — the declared forecasts are the decomposition's disjointness proof, and a default forecast intersects everything."

probe_sentence "P2-bundle-delivery" "In a checkpoint-pinning project, spawn materials are delivered as one crafter-emitted bundle — brief, blind checkpoint, and pack argv with published hashes — beside its emitted \`bale open\` line, so the desk hand-composes neither; the bundle format itself lives in the bale tool's documentation, not here."

if python3 -m unittest tests.test_global_doc_selfcontainment >/dev/null 2>&1; then
  echo "[P3-selfcontainment] PASS"
else
  echo "[P3-selfcontainment] FAIL: guard suite not green"
  fail=1
fi

if python3 -m unittest tests.test_doc_crossrefs >/dev/null 2>&1; then
  echo "[P4-crossrefs] PASS"
else
  echo "[P4-crossrefs] FAIL: crossref suite not green"
  fail=1
fi

exit "$fail"
