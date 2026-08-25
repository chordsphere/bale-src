#!/usr/bin/env bash
# Blind checkpoint — pair-close rider (VERSION bump + doc cargo +
# harness-level --slow convention). Authored blind from the request at
# the 2026-08-25-continue-plan-003 sitting. Outcome contracts only.
# Exit 0 = pass; 1 = a probe failed (HOLD); 2 = harness broke.
# Offline, read-only over the staged tree: pure content probes, no
# fixtures, no subprocesses beyond grep/cat.
#
# Provenance note per the split-probes rule: every string pinned below
# is either tool-fixed content (the version number) or text the brief
# marks verbatim-required as a desk decision (the BALE.md sentence,
# the BALE_TEST_SLOW spelling, the bale-emitted term). Nothing here
# pins wording the worker was free to choose.
set -u
FAILED=0
say() { printf '%s\n' "$*"; }
verdict() {
  if [ "$2" -eq 0 ]; then say "[PASS] $1"; else say "[FAIL] $1"; FAILED=1; fi
}
for f in bin/VERSION BALE.md docs/CLAUDE.md tests/harness.py validate.sh; do
  [ -f "$f" ] || { say "[CKPT-ERR] missing expected file: $f"; exit 2; }
done

# P1: the pair's shared bump landed, exactly.
[ "$(head -1 bin/VERSION | tr -d '[:space:]')" = "0.4.16" ]
verdict "bin/VERSION is exactly 0.4.16 (the pair's shared bump)" $?

# P2: board 51's apply documentation landed in BALE.md — the brief's
# one verbatim-required sentence, byte-fixed by desk decision.
grep -Fq "A bare \`bale apply\` resolves the newest response tarball answering the single open session" BALE.md
verdict "BALE.md carries the verbatim-required bare-apply sentence" $?

# P3: board 52's version tag landed — the literal version string
# appears in BALE.md (position-free; robust to section rewrites).
grep -Fq "0.4.16" BALE.md
verdict "BALE.md carries the 0.4.16 version tag" $?

# P4: the --slow convention exists harness-level — the desk-pinned
# env-var spelling appears in both the harness and validate.sh.
grep -Fq "BALE_TEST_SLOW" tests/harness.py
verdict "tests/harness.py carries the BALE_TEST_SLOW gate" $?
grep -Fq "BALE_TEST_SLOW" validate.sh
verdict "validate.sh knows the BALE_TEST_SLOW gate" $?

# P5: the convention's docs line landed in BALE.md (desk-ruled home).
grep -Fq "BALE_TEST_SLOW" BALE.md
verdict "BALE.md documents BALE_TEST_SLOW" $?

# P6: the docs/CLAUDE.md pointer landed — the brief's verbatim-marked
# term in the preamble-vs-manifest doctrine's file.
grep -Fq "bale-emitted" docs/CLAUDE.md
verdict "docs/CLAUDE.md carries the bale-emitted pointer term" $?

say "----------------------------------------------------------------"
if [ "$FAILED" -eq 0 ]; then say "[CKPT] PASS — pair-close rider probes hold"; exit 0
else say "[CKPT] HOLD — one or more rider probes failed"; exit 1; fi
