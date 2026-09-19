#!/usr/bin/env bash
# Blind checkpoint v1 — sitting close 13 (slug sitting-close-deltas-13).
# Authored 2026-09-19 by the 2026-09-19-continue-plan-009 desk, from the
# request, before any implementation. Outcome-only: it reads
# claude/MASTER.md in the staged tree and writes nothing anywhere.
# Exit 0 pass, 1 a probe failed, 2 the script itself errored.
set -u
F="claude/MASTER.md"
fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fails=$((fails + 1)); }
check() { if [ "$2" = "yes" ]; then pass "$1"; else fail "$1"; fi; }

echo "writes: none (read-only probes of $F)"
if [ ! -f "$F" ]; then echo "[FAIL] $F present in the staged tree"; exit 1; fi

# Section bounds, by the doc's own level-two headings (strict anchors).
line_of() { grep -n -m1 "^## $1\\. " "$F" | cut -d: -f1; }
S3=$(line_of 3); S4=$(line_of 4); S5=$(line_of 5)
S6=$(line_of 6); S7=$(line_of 7); S8=$(line_of 8)
for v in "$S3" "$S4" "$S5" "$S6" "$S7" "$S8"; do
  case "$v" in ''|*[!0-9]*) echo "[FAIL] sections 3-8 located by heading"; exit 1;; esac
done
pass "sections 3-8 located by heading"
sec() { sed -n "$1,$(( $2 - 1 ))p" "$F"; }          # [start, end)
squash() { tr -d ' \n\t'; }                           # wrap-insensitive
# Span of a board row inside section 4: from "N. **" to the next row.
row() { sec "$S4" "$S5" | awk -v n="$1" '
  /^[0-9]+[a-z]?\. \*\*/ { on = ($1 == n".") } on { print }'; }
# Span of a registry entry inside section 3: from a line starting with
# the given fixed text to the next column-one "- " entry or blank+non-list.
entry() { sec "$S3" "$S4" | awk -v k="$1" '
  index($0, k) == 1 { on = 1; print; next }
  on && /^- / { exit } on && /^[^ \[]/ && !/^$/ { exit } on { print }'; }

# --- anchors: base text that must survive (pass on the base tree) -----
a1=$(grep -c '^Landed 2026-09-18, the continue-plan-001 sitting (master$' "$F")
a2=$(sec "$S4" "$S5" | grep -c '^111\. \*\*Tests smalls\*\* — queued 2026-09-18 (tests only):$')
a3=$(sec "$S6" "$S7" | grep -c '^163\. \*\*A tool-use pause at the open\.\*\*')
a4=$(grep -c '^New, ratified 2026-09-18 (the `2026-09-18-continue-plan-001` sitting;$' "$F")
check "anchor: close 12's block, row 111, entry 163 and the 09-18 contracts heading survive" \
  "$([ "$a1" = 1 ] && [ "$a2" = 1 ] && [ "$a3" = 1 ] && [ "$a4" = 1 ] && echo yes || echo no)"
n_landed=$(grep -c '^Landed ' "$F"); n_rat=$(grep -c '^New, ratified' "$F")
n_rows=$(sec "$S4" "$S5" | grep -c '^[0-9]\+[a-z]\?\. \*\*')
n_ev=$(sec "$S6" "$S7" | grep -c '^[0-9]\+\. \*\*')
check "anchor: no close block, contracts heading, board row or evidence entry was removed" \
  "$([ "$n_landed" -ge 25 ] && [ "$n_rat" -ge 29 ] && [ "$n_rows" -ge 111 ] && [ "$n_ev" -ge 154 ] && echo yes || echo no)"

# --- the close's outcomes ---------------------------------------------
h=$(grep -c '^Last landed by: `20[0-9][0-9]-[0-9][0-9]-[0-9][0-9]-sitting-close-deltas-13-[0-9][0-9][0-9]`\.$' "$F")
hl=$(grep -c '^Last landed by: ' "$F")
check "header: the one last-landed-by line names a sitting-close-deltas-13 session" \
  "$([ "$h" = 1 ] && [ "$hl" = 1 ] && echo yes || echo no)"

b=$(sec "$S3" "$S4" | grep -c '^Landed 2026-09-19')
last=$(sec "$S3" "$S4" | grep '^Landed ' | tail -1 | cut -c1-17)
check "section 3: two blocks open 'Landed 2026-09-19', and the last block of the section is one of them" \
  "$([ "$b" = 2 ] && [ "$last" = "Landed 2026-09-19" ] && echo yes || echo no)"

s3=$(sec "$S3" "$S4" | squash); ok=yes
for sid in 2026-09-19-session-fix-002 2026-09-19-opener-reword-doc-sweep-r2-003 \
  2026-09-19-opener-reword-code-004 2026-09-19-opener-reword-docs-005 \
  2026-09-19-continue-plan-006 2026-09-19-board-110-held-admissions-007 \
  2026-09-19-board-111-tests-smalls-008; do
  case "$s3" in *"$sid"*) ;; *) ok=no; echo "  missing in section 3: $sid";; esac
done
check "section 3: cites all seven session ids of the two sittings" "$ok"

r112=$(sec "$S4" "$S5" | grep -c '^112\. \*\*'); r113=$(sec "$S4" "$S5" | grep -c '^113\. \*\*')
rl=$(sec "$S4" "$S5" | grep '^[0-9]\+[a-z]\?\. \*\*' | tail -1 | cut -c1-7)
check "section 4: rows 112 and 113 exist once each, and 113 is the board's last row" \
  "$([ "$r112" = 1 ] && [ "$r113" = 1 ] && [ "$rl" = "113. **" ] && echo yes || echo no)"

ok=yes
for n in 104 109 110 111; do
  case "$(row "$n" | squash)" in *"[2026-09-19:"*) ;; *) ok=no; echo "  row $n: no [2026-09-19: bracket";; esac
done
check "section 4: rows 104, 109, 110 and 111 each carry a [2026-09-19: bracket" "$ok"
ok=yes
case "$(row 110 | squash)" in *"2026-09-19-board-110-held-admissions-007"*) ;; *) ok=no;; esac
case "$(row 111 | squash)" in *"2026-09-19-board-111-tests-smalls-008"*) ;; *) ok=no;; esac
check "section 4: row 110 names its landing session, and row 111 names its own" "$ok"

c=$(sec "$S5" "$S6" | grep -c '^New, ratified 2026-09-19')
cl=$(sec "$S5" "$S6" | grep '^New, ratified' | tail -1 | cut -c1-24)
check "section 5: one 'New, ratified 2026-09-19' heading, and it is the section's last" \
  "$([ "$c" = 1 ] && [ "$cl" = "New, ratified 2026-09-19" ] && echo yes || echo no)"

ok=yes
for n in 164 165 166 167 168 169 170; do
  k=$(sec "$S6" "$S7" | grep -c "^$n\\. \\*\\*")
  [ "$k" = 1 ] || { ok=no; echo "  entry $n: found $k"; }
done
check "section 6: entries 164 through 170 exist once each" "$ok"

v=$(sec "$S7" "$S8" | grep -c '^- Version landmark: 0\.4\.37 (')
check "section 7: the 0.4.37 version landmark bullet" "$([ "$v" = 1 ] && echo yes || echo no)"

ok=yes
while IFS= read -r key; do
  case "$(entry "$key" | squash)" in *"[2026-09-19:"*) ;; *) ok=no; echo "  registry entry without a [2026-09-19: bracket: $key";; esac
done <<'KEYS'
- run_hook's three placeholder-less f-strings
- test_apply_preflight.py module-docstring history true-up
- The two `_section_29` test-id renames
- `from_lines`' stale "at v0.1" marker
- Whether the shape sentence's three homes converge on one wording
KEYS
check "section 3 registry: the five consumed or closed entries each carry a [2026-09-19: bracket" "$ok"

if [ "$fails" -gt 0 ]; then echo "checkpoint: $fails probe(s) failed"; exit 1; fi
echo "checkpoint: all probes passed"; exit 0
