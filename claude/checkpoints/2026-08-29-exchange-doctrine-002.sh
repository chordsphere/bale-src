#!/usr/bin/env bash
# Blind checkpoint — exchange-doctrine (2026-08-29), v1.
# Authored at the read-only sitting 2026-08-29-formalize-convo-001,
# from the request, before any implementation exists. Outcome-only:
# asserts what must be true of the applied tree, never how it got
# there. Read-only: this script writes nowhere.
#
# Exit contract (TARBALL.md §7.5 / board-6 D2): 0 every probe passed,
# 1 at least one probe failed, 2 the script itself errored.
set -u
echo "checkpoint exchange-doctrine v1: writes to no location"

fail=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fail=1; }
probe() {  # probe <label> <command...>
  local label="$1"; shift
  if "$@" >/dev/null 2>&1; then pass "$label"; else fail "$label"; fi
}
absent() {  # absent <label> <fixed-string> <file>
  local label="$1" needle="$2" file="$3"
  if [[ ! -f "$file" ]]; then fail "$label (missing $file)"; return; fi
  if grep -qF -- "$needle" "$file"; then fail "$label"; else pass "$label"; fi
}
present() {  # present <label> <fixed-string> <file>
  local label="$1" needle="$2" file="$3"
  if [[ ! -f "$file" ]]; then fail "$label (missing $file)"; return; fi
  if grep -qF -- "$needle" "$file"; then pass "$label"; else fail "$label"; fi
}

# --- 1. The ADR exists, is Accepted, and has the DOCS.md §5 sections
adr_matches=( claude/context/adr/0017-*.md )
if [[ ${#adr_matches[@]} -eq 1 && -f "${adr_matches[0]}" ]]; then
  adr="${adr_matches[0]}"
  pass "exactly one ADR-0017 file exists ($adr)"
  present "ADR-0017 status is Accepted" "- **Status:** Accepted" "$adr"
  present "ADR-0017 has a Context section" "## Context" "$adr"
  present "ADR-0017 has a Decision section" "## Decision" "$adr"
  present "ADR-0017 has a Consequences section" "## Consequences" "$adr"
else
  fail "exactly one ADR-0017 file exists"
  fail "ADR-0017 status is Accepted"
  fail "ADR-0017 has a Context section"
  fail "ADR-0017 has a Decision section"
  fail "ADR-0017 has a Consequences section"
fi
present "INDEX.md lists ADR-0017" "context/adr/0017-" claude/INDEX.md

# --- 2. Prior ADRs untouched (append-only): sha256 pinned from the
#        bytes shipped in the authoring request, 2026-08-29.
pin() {  # pin <label> <sha256> <file>
  local label="$1" want="$2" file="$3" got
  got=$(sha256sum "$file" 2>/dev/null | cut -d' ' -f1) || got=""
  if [[ "$got" == "$want" ]]; then pass "$label"; else fail "$label"; fi
}
pin "ADR-0010 byte-unchanged" 48d13a4f8bcba35f8bc7e766d10ca4d09a3e525180d353e37bd60b1367df3704 claude/context/adr/0010-paste-back-probes.md
pin "ADR-0011 byte-unchanged" 0d27e69dfc026cba66e943a64836840530b8ab5688991967f69e338b02b1ef2c claude/context/adr/0011-clarification-response-kind.md
pin "ADR-0012 byte-unchanged" ecc00d8739ab1b6714e0e5b4f0b529fe0fbdee25abed0e5e9e1814c3c4e6f054 claude/context/adr/0012-agent-driven-substrate.md

# --- 3. The counterparty forks are retired (preserved text, pinned as
#        fixed strings: each is a phrase the docs carry today).
absent "TARBALL.md §5.9.1 human-attended fork retired" "human-attended session, chat is the default" docs/TARBALL.md
absent "TARBALL.md §5.9.4 manual-today fork retired" "manual today (the architect reads the questions" docs/TARBALL.md
absent "TARBALL.md §1 planner-is-the-human retired" "the human architect; the **worker** builds responses — Claude" docs/TARBALL.md
absent "TARBALL.md §4.6 harness-executes framing retired" "harness executes and feeds back automatically" docs/TARBALL.md
absent "PLANNER.md §15 transport-to-overseer future tense retired" "harness era moves the architect from transport to overseer" docs/PLANNER.md
absent "PLANNER.md §15 architect-as-transport present tense retired" "with the architect as transport" docs/PLANNER.md
absent "PLANNER.md §18 manual rung no longer 'every step human-operated'" "human-operated, the present tense)" docs/PLANNER.md
absent "BALE.md §8.10.2 answer-in-chat next step retired" "answering the questions in the worker's chat" BALE.md

# --- 4. The pinned vocabulary landed (verbatim-required in the brief).
present "TARBALL.md names the relay verb" "bale relay" docs/TARBALL.md
present "TARBALL.md names the exchange record schema" "exchange-record.schema.json" docs/TARBALL.md
present "BALE.md names the relay verb" "bale relay" BALE.md
present "PLANNER.md names the relay verb" "bale relay" docs/PLANNER.md

# --- 5. Invariants: the global docs stay self-contained and cross-refs resolve.
probe "global-doc self-containment suite passes" python3 -m unittest discover -s tests -p 'test_global_doc_selfcontainment.py'
probe "doc cross-reference suite passes" python3 -m unittest discover -s tests -p 'test_doc_crossrefs.py'

# --- 6. Out-of-forecast surfaces untouched: no bump, no schema change.
present "bin/VERSION still reads 0.4.17" "0.4.17" bin/VERSION
probe "no exchange-record schema landed by this session" test ! -e schemas/exchange-record.schema.json

exit $fail
