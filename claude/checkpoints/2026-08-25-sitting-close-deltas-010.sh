#!/usr/bin/env bash
# Blind checkpoint — sitting-close deltas (master-003 desk).
# Content probes on claude/MASTER.md only: sid recordings, the
# version position, the sed-ritual retirement, and the two
# verbatim-required phrases the brief marks. Wording elsewhere is
# the close worker's, in the document's voice, and is not pinned.
# Exit 0 = pass; 1 = HOLD; 2 = harness broke.
set -u
M="claude/MASTER.md"
[ -f "$M" ] || { echo "[CKPT-ERR] $M missing"; exit 2; }
FAILED=0
verdict() { if [ "$2" -eq 0 ]; then echo "[PASS] $1"; else echo "[FAIL] $1"; FAILED=1; fi; }

for sid in 2026-08-25-board-50-crlf-tolerance-004 \
           2026-08-25-board-52-pack-preamble-006 \
           2026-08-25-board-51-bare-apply-007 \
           2026-08-25-pair-close-rider-008; do
  grep -Fq "$sid" "$M"
  verdict "MASTER.md records $sid" $?
done

grep -Fq "0.4.16" "$M"
verdict "MASTER.md carries the 0.4.16 position" $?

if grep -Fq "sed -i" "$M"; then
  verdict "the sed-ritual remedy is retired (no 'sed -i' remains)" 1
else
  verdict "the sed-ritual remedy is retired (no 'sed -i' remains)" 0
fi

grep -Fq "cannot separate" "$M"
verdict "the board-51 ambiguity bracket carries its verbatim phrase" $?

grep -Fq "un-decorating is the" "$M"
verdict "the recency watch carries its verbatim remedy phrase" $?

grep -Fq "desk-unique bundle stems" "$M"
verdict "the collision specimen carries its verbatim remedy phrase" $?

echo "----------------------------------------------------------------"
if [ "$FAILED" -eq 0 ]; then echo "[CKPT] PASS — close-delta probes hold"; exit 0
else echo "[CKPT] HOLD — one or more close-delta probes failed"; exit 1; fi
