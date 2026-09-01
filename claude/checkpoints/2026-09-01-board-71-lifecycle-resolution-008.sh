#!/usr/bin/env bash
# board-71 blind checkpoint v1 — lifecycle resolution from the
# artifact in hand. Outcome contracts only; runs at the applied
# tree's root. Exit 0 all pass; 1 HOLD; 2 checkpoint-error.
set -u

fail_count=0

probe() {
  local label="$1" rc="$2"
  if [ "$rc" -eq 0 ]; then echo "[PASS] $label"
  else echo "[FAIL] $label"; fail_count=$((fail_count + 1)); fi
}

for f in bin/bale bin/bale_apply.py BALE.md \
         claude/context/adr/0006-session-registry.md; do
  [ -f "$f" ] || { echo "[CHECKPOINT-ERROR] missing file: $f"; exit 2; }
done

# P1 — retry's help no longer states the retired several-open
# --sid requirement (scoped to retry's own help output; the four
# other verbs keep the phrase by contract).
help_out=$(python3 bin/bale retry --help 2>&1) \
  || { echo "[CHECKPOINT-ERROR] retry --help failed to run"; exit 2; }
printf '%s' "$help_out" | tr -s ' \n' '  ' \
  | grep -qi "required when several are"
rc=$?
probe "P1-retry-sid-requirement-retired" \
      "$([ "$rc" -ne 0 ]; echo $?)"

# P2 — the amend successor's placeholder is retired from bin/bale.
tr -s ' \n' '  ' < bin/bale | grep -q "retry <response-tarball>"
rc=$?
probe "P2-successor-placeholder-retired" \
      "$([ "$rc" -ne 0 ]; echo $?)"

# P3 — ADR-0006 grew by a dated append and only by an append:
# the base bytes remain a byte-identical prefix.
BASE_SIZE=5645
BASE_SHA=1117b3f483ac39269ab342824466b769d18b9d2e1a7207ccac41eaafb2f88f05
adr=claude/context/adr/0006-session-registry.md
size=$(wc -c < "$adr")
prefix_sha=$(head -c "$BASE_SIZE" "$adr" | sha256sum | cut -d' ' -f1)
tail_txt=$(tail -c +"$((BASE_SIZE + 1))" "$adr")
[ "$size" -gt "$BASE_SIZE" ] \
  && [ "$prefix_sha" = "$BASE_SHA" ] \
  && printf '%s' "$tail_txt" | grep -q "2026-09"
rc=$?
if [ "$prefix_sha" = "$BASE_SHA" ]; then pfx=ok; else pfx=CHANGED; fi
probe "P3-adr0006-dated-append-only (size=$size prefix=$pfx)" "$rc"

# P4 — BALE.md's retry row names artifact-borne resolution.
grep -E '^\| `bale retry ' BALE.md | grep -q "responds_to"
probe "P4-balemd-retry-row-names-responds_to" "$?"

if [ "$fail_count" -gt 0 ]; then
  echo "checkpoint: HOLD ($fail_count probe(s) failed)"
  exit 1
fi
echo "checkpoint: PASS (4/4)"
exit 0
