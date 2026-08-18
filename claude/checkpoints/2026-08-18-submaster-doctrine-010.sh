#!/usr/bin/env bash
# Blind checkpoint — sub-master doctrine landing (contract-doc session)
# Authored at the 2026-08-18-continue-plan-008 desk, from the request,
# before implementation. v1.
#
# Probes pin only desk-authored verbatim-required lines (preserved
# class) and the rider's specified count — never the worker's own
# prose. Whitespace-normalized throughout. Dry-run at the desk against
# base: all probes FAIL, exit 1.
set -u
FAILS=0
fail() { printf '[FAIL] %s\n' "$1"; FAILS=$((FAILS+1)); }
pass() { printf '[PASS] %s\n' "$1"; }
norm() { tr -s '[:space:]' ' ' < "$1"; }

has() { # has <file> <normalized phrase>
  norm "$1" | grep -qF "$2"
}

P=docs/PLANNER.md; C=docs/CLAUDE.md; T=docs/TARBALL.md
TF=tests/test_sanctioned_pairs.py
for f in "$P" "$C" "$T" "$TF"; do
  [ -f "$f" ] || { printf '[FAIL] missing file %s\n' "$f"; exit 1; }
done

# C1 — the flat authorship clause is gone from PLANNER.md.
if has "$P" "never oracle authorship"; then
  fail "C1 flat-clause-removed: 'never oracle authorship' still in $P"
else
  pass "C1 flat-clause-removed"
fi

# C2 — K2's builds-against form present in PLANNER.md.
if has "$P" "what it never grants is authorship of an oracle the authoring session builds against"; then
  pass "C2 builds-against-form-present"
else
  fail "C2 builds-against-form-present"
fi

# C3 — K1 transition statement present in PLANNER.md.
if has "$P" "A split is a role transition: the session that proposes it becomes a master for its own subtree"; then
  pass "C3 role-transition-statement-present"
else
  fail "C3 role-transition-statement-present"
fi

# C4 — K3 arc dual-stream present in PLANNER.md.
if has "$P" "grading the summed outcome of the subtree; the sub-master ships its own validation of the sum"; then
  pass "C4 arc-dual-stream-present"
else
  fail "C4 arc-dual-stream-present"
fi

# C5 — K4 one-remove control present in PLANNER.md.
if has "$P" "the self-oracle shape at one remove"; then
  pass "C5 one-remove-control-present"
else
  fail "C5 one-remove-control-present"
fi

# C6 — K5 rehearsal rule present in PLANNER.md.
if has "$P" "derives its rehearsal landing from the brief's extracted block bytes"; then
  pass "C6 rehearsal-rule-present"
else
  fail "C6 rehearsal-rule-present"
fi

# C7 — K7 present in CLAUDE.md (the doc had zero 'sub-master' at base).
if has "$C" "the offering session, as sub-master for its subtree, authors the split sessions' materials"; then
  pass "C7 claude-split-transition-present"
else
  fail "C7 claude-split-transition-present"
fi

# C8 — K8 present in TARBALL.md.
if has "$T" "re-derived for the narrowed scope; the offering session authors them as sub-master"; then
  pass "C8 tarball-checkpoint-handback-present"
else
  fail "C8 tarball-checkpoint-handback-present"
fi

# C9 — the rider landed: count pin 5 and a PLANNER.md side in the suite.
if norm "$TF" | grep -qF "len(PAIRS), 5" && grep -q "PLANNER.md" "$TF"; then
  pass "C9 pairs-pin-bumped-to-5-with-planner-side"
else
  fail "C9 pairs-pin-bumped-to-5-with-planner-side"
fi

if [ "$FAILS" -gt 0 ]; then
  printf 'checkpoint: %d probe(s) failed\n' "$FAILS"
  exit 1
fi
printf 'checkpoint: all probes passed\n'
exit 0
