#!/usr/bin/env bash
# Blind checkpoint v3 — row 43, the TARBALL.md §5 compression pilot,
# authored 2026-09-23 at the 2026-09-23-continue-plan-006 desk, from the
# request, before any implementation exists. Outcome contracts only.
# Runs from the staging copy of the applied tree (its cwd). Spans are
# bounded by heading-line greps, never by section number: TARBALL.md is
# core-first and §7 follows §5 in the file.
#
# Verdict lines carry the label alone; detail goes on a following
# "  detail:" line. Exit 1 = a probe failed; exit 2 = the oracle itself
# broke (a control failed, a span could not be bounded).

set -u
DOC="docs/TARBALL.md"
fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; [ -n "${2:-}" ] && echo "  detail: $2"; fails=$((fails+1)); }
oracle_error() { echo "[ERROR] $1" >&2; exit 2; }

# ---- control ---------------------------------------------------------
[ -f "$DOC" ] || oracle_error "control: $DOC missing from the staging tree"
command -v python3 >/dev/null 2>&1 || oracle_error "control: python3 not on PATH"
line_of() { grep -n -m1 "$1" "$DOC" | cut -d: -f1; }
S5="$(line_of '^## 5\. ')"; S7="$(line_of '^## 7\. ')"
S3_4="$(line_of '^### 3\.4 ')"; S4="$(line_of '^## 4\. ')"
[ -n "$S5" ] && [ -n "$S7" ] && [ "$S7" -gt "$S5" ] || oracle_error "control: could not bound §5 (## 5. … ## 7.)"
[ -n "$S3_4" ] && [ -n "$S4" ] && [ "$S4" -gt "$S3_4" ] || oracle_error "control: could not bound §3.4 (### 3.4 … ## 4.)"
span() { sed -n "${1},$(( $2 - 1 ))p" "$DOC"; }
sub_span() {  # $1 = heading regex; prints that subsection's lines up to the next heading of any depth
  local start; start="$(line_of "$1")"
  [ -n "$start" ] || { echo ""; return; }
  awk -v s="$start" 'NR>s && /^#+ /{exit} NR>=s{print}' "$DOC"
}
echo "control ok: §5 spans lines $S5-$((S7-1)), §3.4 spans $S3_4-$((S4-1))"

s5_lines=$(( S7 - S5 ))
S5TXT="$(span "$S5" "$S7")"

# ---- probe 1: §5 is compressed (≤ 85% of the base's 988 lines) --------
if [ "$s5_lines" -le 839 ]; then pass "section-5-compressed"
else fail "section-5-compressed" "§5 spans $s5_lines lines; the base spanned 988 and the pilot's floor is 839"; fi

# ---- probe 2: every §5 heading number survives (DOCS.md §6.4) ---------
missing=""
for h in 5.1 5.1.1 5.2 5.2.1 5.2.2 5.3 5.4 5.4.1 5.5 5.6 5.6.1 5.6.2 5.6.3 5.7 5.8 5.9 5.9.1 5.9.2 5.9.3 5.9.4 5.10; do
  printf '%s\n' "$S5TXT" | grep -Eq "^#{3,4} $(printf '%s' "$h" | sed 's/\./\\./g') " || missing="$missing $h"
done
if [ -z "$missing" ]; then pass "section-5-headings-stable"
else fail "section-5-headings-stable" "headings gone:$missing"; fi

# ---- probe 3: the four claim values and the subset rule stay ----------
cv_missing=""
for v in pass fail untested unknown; do
  printf '%s\n' "$S5TXT" | grep -Fq "| \`$v\` |" || cv_missing="$cv_missing $v"
done
printf '%s\n' "$S5TXT" | grep -Fq '⊆' || cv_missing="$cv_missing subset-relation"
if [ -z "$cv_missing" ]; then pass "claim-values-and-subset-rule-kept"
else fail "claim-values-and-subset-rule-kept" "missing:$cv_missing"; fi

# ---- probe 4: no version tokens inside §5 ------------------------------
vcount="$(printf '%s\n' "$S5TXT" | grep -c 'v0\.[0-9]' || true)"
if [ "$vcount" = "0" ]; then pass "no-version-tokens-in-section-5"
else fail "no-version-tokens-in-section-5" "$vcount lines in §5 still carry a v0.x token"; fi

# ---- probe 5: every ADR-0013 citation in §5 carries a section key -----
unkeyed="$(printf '%s\n' "$S5TXT" | grep -o 'ADR-0013[^ ]*\( [^ ]*\)\?' | grep -vc 'ADR-0013 §' || true)"
if [ "$unkeyed" = "0" ]; then pass "adr-0013-cites-keyed"
else fail "adr-0013-cites-keyed" "$unkeyed ADR-0013 citations in §5 without a § key"; fi

# ---- probe 6: the expects_probe collision has one home (§3.3) ----------
s591="$(sub_span '^#### 5\.9\.1 ')"
s591_lines="$(printf '%s\n' "$s591" | sed '/^[[:space:]]*$/d' | wc -l | tr -d ' ')"
ep_count="$(printf '%s\n' "$S5TXT" | grep -c 'expects_probe: no' || true)"
# v2 (amended 2026-09-23 after the 008 HOLD, a fixture defect): v1 pinned a
# 12-line floor on the whole subsection, a size the brief never gave; the
# brief's outcome is that the collision has one home, §3.3, and §5.9.1
# keeps a pointer. v2 asserts exactly that: no `expects_probe: no` inside
# §5, §5.9.1 citing §3.3, and §5.9.1 shorter than the base's 47 non-blank
# lines. Every other probe is byte-identical to v1.
# v3 (amended 2026-09-23 after the worker's corrected response): v2 pinned
# zero mentions, calibrated to the held landing; a pointer that names the
# flag and its home is the better outcome. v3 asserts the shape: §5.9.1
# shorter than the base's 47 non-blank lines and citing §3.3, and every
# §5 line that names expects_probe also names §3.3 (a pointer, never a
# restatement). Every other probe is byte-identical to v1.
unpointed="$(printf '%s\n' "$S5TXT" | grep 'expects_probe' | grep -vc '3\.3' || true)"
if [ -n "$s591" ] && [ "$s591_lines" -lt 47 ] && [ "$unpointed" = "0" ] && printf '%s\n' "$s591" | grep -q '3\.3'; then
  pass "expects-probe-collision-one-home"
else
  fail "expects-probe-collision-one-home" "§5.9.1 has $s591_lines non-blank lines (base 47); $unpointed §5 line(s) name expects_probe without citing §3.3; §5.9.1 cites §3.3: $(printf '%s\n' "$s591" | grep -q '3\.3' && echo yes || echo no)"
fi

# ---- probes 7-9: the three VERBATIM riders, byte-exact, in place -------
V1='An `--include` may not name the subtree the `[validation] base` pattern lives under; a broader ancestor is fine, and the checkpoint auto-excludes from it at the walk.'
V2='Two couriers, one record: the tarball carries the manifest, the empty change surfaces and an optional `notes.md`; the paste block carries the manifest JSON alone; a question row'"'"'s `context` rides both.'
V3='The emitter exits 0 once it has written the block and 1 when there was nothing to paste, so a worker chaining it with `&&` never skips the paste; `--request` lets the lint read `resolved_scope` and warn on an undeclared forecast departure, and lets the crafter seed the departure stubs §5.4 names.'
if span "$S3_4" "$S4" | grep -Fxq -- "$V1"; then pass "verbatim-1-include-rule-in-3-4"
else fail "verbatim-1-include-rule-in-3-4" "VERBATIM-1 not found as one whole line inside §3.4"; fi
if sub_span '^#### 5\.9\.2 ' | grep -Fxq -- "$V2"; then pass "verbatim-2-couriers-in-5-9-2"
else fail "verbatim-2-couriers-in-5-9-2" "VERBATIM-2 not found as one whole line inside §5.9.2"; fi
if sub_span '^### 5\.2\.2 ' | grep -Fxq -- "$V3"; then pass "verbatim-3-emitter-in-5-2-2"
else fail "verbatim-3-emitter-in-5-2-2" "VERBATIM-3 not found as one whole line inside §5.2.2"; fi

# ---- probe 10: the four doc-pin suites pass on the applied tree --------
suite_out="$(python3 -m unittest tests.test_sanctioned_pairs tests.test_doc_crossrefs tests.test_global_doc_selfcontainment tests.test_schema_embeds 2>&1)"
if [ $? -eq 0 ]; then pass "doc-pin-suites-pass"
else fail "doc-pin-suites-pass" "$(printf '%s\n' "$suite_out" | grep -E '^(FAIL|ERROR):' | head -n 5 | tr '\n' ';')"; fi

echo "probes failed: $fails"
[ "$fails" -eq 0 ] && exit 0 || exit 1
