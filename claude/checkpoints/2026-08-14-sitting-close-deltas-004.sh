#!/usr/bin/env bash
# Blind checkpoint — sitting-close-deltas (2026-08-13/14 sitting).
# Planner-authored from the brief before the worker exists. Docs
# session: the oracle checks that the sitting's record actually
# reached MASTER.md, anchored on outcome-level greps only.
set -euo pipefail
fail() { printf 'CHECKPOINT FAIL: %s\n' "$*" >&2; exit 1; }
note() { printf 'checkpoint: %s\n' "$*"; }

M=claude/MASTER.md
C=docs/CLAUDE.md
[ -f "$M" ] || fail "MASTER.md missing"
[ -f "$C" ] || fail "docs/CLAUDE.md missing"

anchor="Mechanism authority sits with the session that has the code in context: the planner pins intent, constraints, and outcomes; the worker owns the how, and a reasoned, flagged deviation from the brief is the system working, not failing."
grep -qF "$anchor" "$C" || fail "engraved principle absent from docs/CLAUDE.md or rewrapped (must be one physical line)"
grep -qiE "mechanism authority" "$M" || fail "MASTER.md carries no ratification pointer to the principle"
note "principle engraved globally in docs/CLAUDE.md; MASTER.md points to it"

for needle in \
  "2026-08-14-bare-pack-excl-waiver-002" \
  "2026-08-14-bare-pack-oneshot-003" \
  "0.4.10" \
  "checkpoint_waived" \
  "--accept-checkpoint-change" \
  "--checkpoint-file"; do
  grep -qF -- "$needle" "$M" || fail "expected recording absent from MASTER.md: $needle"
done
note "landings, trail, waiver, amendment valve, and flag all recorded"

# Supersession-sweep rider and fixture-isolation evidence, keyword level.
grep -qi "sweep" "$M" || fail "supersession sweep-order rider not found"
grep -qiE "per[- ]scenario|fresh repo per scenario" "$M" || fail "fixture-isolation rule not found"
grep -qiE "PLANNER|doctrine extraction" "$M" || fail "planner-doctrine extraction queue entry not found"
note "riders and evidence entries present"

note "PASS"
