#!/bin/bash
# Blind checkpoint — sitting-close-deltas-10, v1. Presence pins on
# claude/MASTER.md, whitespace collapsed. cwd = staging root.
fails=0
pass() { echo "[PASS] $1"; }
failp() { echo "[FAIL] $1"; fails=$((fails+1)); }
M="claude/MASTER.md"; FLAT="$(tr -s '[:space:]' ' ' < "$M")"
has() { if printf '%s' "$FLAT" | grep -qF "$1"; then pass "$2"; else failp "$2"; fi; }
has "Landed 2026-09-16, the continue-plan-009 sitting" "§3 close block present"
n="$(printf '%s' "$FLAT" | grep -oF "continue-plan-009 sitting (master" | wc -l)"; if [ "$n" -eq 1 ]; then pass "close block landed once"; else failp "close block landed once (found $n)"; fi
has "Sequencing for the next desk: wave 3 — 47b, 56+57, 69" "sequencing line for wave 3"
for pair in "102|DONE at \`2026-09-15-board-102-explicit-name-010\`" "91|DONE at \`2026-09-15-board-91-82-crafter-pair-011\`, bumpless" "82|DONE at \`2026-09-15-board-91-82-crafter-pair-011\`. \`--request\`" "68|DONE at \`2026-09-15-board-68-open-gate-order-012\`" "96|Doc third DONE at \`2026-09-15-board-96-doc-97-terminal-shapes-013\`" "97|DONE at \`2026-09-15-board-96-doc-97-terminal-shapes-013\`. DOCS.md" "47|47a DONE at \`2026-09-16-board-47a-hold-card-triage-001\`" "85|DONE at \`2026-09-16-board-96-crafter-85-light-block-002\`. \`feedback" "99|99a DONE at \`2026-09-16-board-99a-outward-docs-003\`" "92|DONE at \`2026-09-16-board-pack-ux-micro-004\`. One rule" "84|DONE at \`2026-09-16-board-pack-ux-micro-004\`. Warns"; do has "${pair#*|}" "row ${pair%%|*} growth present"; done
has "the stats micro also reads the two new self-reported counts" "row 98 growth present"
has "the crafter's size — bundle, probe, emit-block, light-block modes" "row 69 growth present"
for r in "104. **Session kinds, switchable; the context pack**" "105. **Operator-voice authority framing**" "106. **\`bin/bale\` de-dup micro**"; do has "$r" "row ${r:0:3} opened"; done
has "**A session kind is a declared start, switchable.**" "§5 kinds contract"
has "**The operator's voice carries the authority.**" "§5 authority contract"
for e in "141. **Four beside the desk, twice.**" "142. **Absence is not a drop.**" "143. **A validation invariant under target-base staging" "144. **The card paid for itself the same hour.**" "145. **An outside review.**" "146. **The shape rule wins by silence.**"; do has "$e" "§6 entry ${e:0:3}"; done
has "Version landmark: 0.4.34" "§7 version landmark"
has "Tests-forecast rule, concurrency clause (2026-09-16)" "§7 concurrency clause"
has "sets a repo-local git identity" "§7 scratch-repo checkpoint rule"
has "Install-shipped schemas are self-contained" "§7 schema self-containment rule"
c="$(printf '%s' "$FLAT" | grep -oF "[2026-09-16: consumed at" | wc -l)"; if [ "$c" -ge 11 ]; then pass "registry consumptions ($c)"; else failp "registry consumptions ($c of 11)"; fi
has "BALE.md riders for 99b's true-up, one entry" "registry: 99b riders entry"
has "Whether the release tarball ships BALE.md" "ruling queue: BALE.md in the release"
[ "$fails" -eq 0 ] && exit 0 || exit 1
