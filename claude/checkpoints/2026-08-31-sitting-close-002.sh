#!/usr/bin/env bash
# Blind checkpoint — sitting-close (2026-08-31), v1. Outcome-only;
# read-only. Exit: 0 all pass, 1 any fail, 2 script error.
set -u
echo "checkpoint sitting-close v1: writes to no location"
fail=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fail=1; }
probe() { local l="$1"; shift; if "$@" >/dev/null 2>&1; then pass "$l"; else fail "$l"; fi; }
present() { local l="$1" n="$2" f="$3"; [[ -f "$f" ]] && grep -qF -- "$n" "$f" && pass "$l" || fail "$l"; }
# Wrap-proof fixed-phrase check: whitespace-normalize, then fixed grep.
flat() { local l="$1" n="$2" f="$3"
  if [[ ! -f "$f" ]]; then fail "$l (missing $f)"; return; fi
  if tr '\n' ' ' < "$f" | tr -s ' ' | grep -qF -- "$n"; then pass "$l"; else fail "$l"; fi; }

# --- MASTER.md rows and narrative
present "MASTER.md carries the extraction row anchor" "bin/bale_relay.py" claude/MASTER.md
present "MASTER.md carries the re-emit row anchor" "re-emit" claude/MASTER.md
present "MASTER.md carries the constants-parity row anchor" "exchange constants" claude/MASTER.md
present "MASTER.md narrative names ADR-0017" "ADR-0017" claude/MASTER.md
flat "MASTER.md records the routing reversal" "reversed for the worker" claude/MASTER.md

# --- PLANNER.md checklist line (verbatim, wrap-proof)
flat "PLANNER.md section 4 carries the verification rule" "verified against bytes or the sitting record at authoring time" docs/PLANNER.md
flat "PLANNER.md rule covers post-authoring rulings" "re-verified against every ruling made after it" docs/PLANNER.md

# --- ADR-0017 Notes append; older ADRs byte-pinned (shipped 2026-08-29 bytes)
adr=( claude/context/adr/0017-*.md )
if [[ ${#adr[@]} -eq 1 && -f "${adr[0]}" ]]; then
  pass "exactly one ADR-0017 file"
  present "ADR-0017 has a dated close append" "2026-08-31" "${adr[0]}"
  flat "ADR-0017 append records the deliberate non-widening" "re-emit surface deliberately not widened" "${adr[0]}"
else
  fail "exactly one ADR-0017 file"; fail "ADR-0017 has a dated close append"; fail "ADR-0017 append records the deliberate non-widening"
fi
pin() { local l="$1" want="$2" f="$3" got; got=$(sha256sum "$f" 2>/dev/null | cut -d' ' -f1) || got=""; [[ "$got" == "$want" ]] && pass "$l" || fail "$l"; }
pin "ADR-0010 byte-unchanged" 48d13a4f8bcba35f8bc7e766d10ca4d09a3e525180d353e37bd60b1367df3704 claude/context/adr/0010-paste-back-probes.md
pin "ADR-0011 byte-unchanged" 0d27e69dfc026cba66e943a64836840530b8ab5688991967f69e338b02b1ef2c claude/context/adr/0011-clarification-response-kind.md
pin "ADR-0012 byte-unchanged" ecc00d8739ab1b6714e0e5b4f0b529fe0fbdee25abed0e5e9e1814c3c4e6f054 claude/context/adr/0012-agent-driven-substrate.md

# --- invariants
probe "doc-contract guards pass" python3 -m unittest tests.test_doc_crossrefs tests.test_global_doc_selfcontainment
present "no bump: bin/VERSION reads 0.4.19" "0.4.19" bin/VERSION
exit $fail
