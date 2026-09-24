#!/usr/bin/env bash
# Blind checkpoint v1 — close 19, the wave-11 deltas landing, authored
# 2026-09-24 at the 2026-09-23-continue-plan-006 desk, from the request.
# Outcome contracts on claude/MASTER.md only: the record names the wave,
# the pile grows, the doc's skeleton holds. Exit 1 = a probe failed;
# exit 2 = the oracle broke.
set -u
M="claude/MASTER.md"; fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; [ -n "${2:-}" ] && echo "  detail: $2"; fails=$((fails+1)); }
[ -f "$M" ] || { echo "[ERROR] control: $M missing" >&2; exit 2; }
grep -q '^## 3\. In flight' "$M" || { echo "[ERROR] control: §3 heading not found" >&2; exit 2; }
echo "control ok: $M present, $(wc -l < "$M") lines"

# probe 1: the head names this close as the last landing
if sed -n '1,30p' "$M" | grep -q 'Last landed by: `2026-09-24-sitting-close-deltas-19-'; then pass "head-names-close-19"
else fail "head-names-close-19" "no 'Last landed by' line naming 2026-09-24-sitting-close-deltas-19-NNN in the first 30 lines"; fi

# probe 2: every session of the wave and the arc is on the record
missing=""
for sid in 2026-09-23-continue-plan-006 2026-09-23-board-121-125-code-micro-007 \
  2026-09-23-board-43-tarball-s5-compression-008 2026-09-23-board-122-rehearsal-verbs-009 \
  2026-09-23-board-45-hostile-repo-design-010 2026-09-23-seed-stemwell-001 2026-09-24-seed-stemwell-001 \
  2026-09-24-wave1-trailing-space-002 2026-09-24-wave2a-add-prune-003 2026-09-24-wave3-codec-regen-004 \
  2026-09-24-wave5-ingest-gzip-005 2026-09-24-wave2b-add-export-006 2026-09-24-wave4-report-json-007 \
  2026-09-24-board-45-close-008; do
  grep -Fq "$sid" "$M" || missing="$missing $sid"
done
[ -z "$missing" ] && pass "wave-and-arc-sids-recorded" || fail "wave-and-arc-sids-recorded" "absent:$missing"

# probe 3: the evidence pile grew past entry 212, numbering continuous
s6="$(grep -n '^## 6\. ' "$M" | cut -d: -f1)"; s7="$(grep -n '^## 7\. ' "$M" | cut -d: -f1)"
if [ -n "$s6" ] && [ -n "$s7" ] && [ "$s7" -gt "$s6" ]; then
  nums="$(sed -n "${s6},${s7}p" "$M" | grep -o '^[0-9]\+\. ' | tr -d '. ')"
  last="$(printf '%s\n' "$nums" | tail -n 1)"; gap="$(printf '%s\n' "$nums" | awk 'NR>1 && $1!=prev+1{g=1} {prev=$1} END{print g+0}')"
  if [ "${last:-0}" -ge 213 ] && [ "$gap" = "0" ]; then pass "evidence-pile-grew-continuously"
  else fail "evidence-pile-grew-continuously" "last entry ${last:-none}; numbering gap: $gap"; fi
else fail "evidence-pile-grew-continuously" "could not bound §6"; fi

# probe 4: the upward report is cited by its path
grep -Fq 'claude/context/board-45-arc/2026-09-24-board-45-close-008-upward-report.md' "$M" \
  && pass "upward-report-cited-by-path" || fail "upward-report-cited-by-path" "path not cited"

# probe 5: the doc's skeleton holds (the eight section headings, in order)
want='## 1. Ultimate goal|## 2. Milestones|## 3. In flight|## 4. The board|## 5. Contracts established|## 6. Orchestration-doctrine evidence pile|## 7. Standing environment facts|## 8. Foundation-audit findings register'
got="$(grep '^## ' "$M" | sed 's/ (.*//' | tr '\n' '|' | sed 's/|$//')"
[ "$got" = "$want" ] && pass "section-skeleton-unchanged" || fail "section-skeleton-unchanged" "headings now: $got"

echo "probes failed: $fails"; [ "$fails" -eq 0 ] && exit 0 || exit 1
