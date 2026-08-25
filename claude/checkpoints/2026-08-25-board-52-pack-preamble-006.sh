#!/usr/bin/env bash
# Blind checkpoint — board 52 (pack emits the chat-opening preamble).
# Authored blind from the request at the 2026-08-25-continue-plan-003
# sitting, before implementation exists. Outcome contracts only.
# Exit 0 = pass; 1 = a probe failed (HOLD); 2 = harness broke.
# Offline by construction: one local git fixture per scenario.
#
# The contract under test, from the ratified queued text: the pack
# report ends with the session-opening chat paragraph as a copy
# block, carrying the session's identity (sid, goal) so the opener
# names what was just packed. Probes pin identity-carriage and
# end-position as outcomes; wording, framing, and block markers are
# the worker's authored surface and are deliberately not pinned.
set -u
STAGING="$PWD"
BALE="$STAGING/bin/bale"
FAILED=0
say()  { printf '%s\n' "$*"; }
need() { command -v "$1" >/dev/null 2>&1 || { say "[CKPT-ERR] missing tool: $1"; exit 2; }; }
need git; need python3
[ -f "$BALE" ] || { say "[CKPT-ERR] bin/bale not found"; exit 2; }
verdict() {
  if [ "$2" -eq 0 ]; then say "[PASS] $1"; else say "[FAIL] $1"; FAILED=1; fi
}

MARK="quetzal-preamble-probe-7391"
R1="$(mktemp -d)" || exit 2
( cd "$R1" && git init -q && git config user.email ckpt@bale \
    && git config user.name ckpt && echo a > a.txt \
    && git add -A && git commit -qm init ) || exit 2

OUT="$(cd "$R1" && python3 "$BALE" pack "fixture goal carrying $MARK for the preamble" --slug fx-pre --write a.txt --expects-probe no --no-readme 2>&1)"
RC=$?
verdict "the fixture pack itself completes (exit 0) [got $RC]" "$RC"

# Probe 1: the pack output carries the goal text verbatim — the
# opener names what was just packed. (Today the goal appears nowhere
# in the report.)
case "$OUT" in
  *"$MARK"*) verdict "pack output carries the goal verbatim" 0 ;;
  *)         verdict "pack output carries the goal verbatim" 1 ;;
esac

# Probe 2: the pack output carries the sid. (True today via the
# session-id line — a boundary anchor, pinned so the identity pair
# stays whole.)
SID="$(cd "$R1" && ls .bale/outbox/request-*.tar.gz 2>/dev/null | head -1 | sed 's/.*request-//; s/\.tar\.gz$//')"
if [ -n "${SID:-}" ]; then
  case "$OUT" in
    *"$SID"*) verdict "pack output carries the sid" 0 ;;
    *)        verdict "pack output carries the sid" 1 ;;
  esac
else
  verdict "pack output carries the sid (no outbox tarball found)" 1
fi

# Probe 3: the goal-bearing content sits at the report's end — the
# ratified text's "ends with the chat paragraph". Generous window:
# the marker appears within the final 15 lines of output, so the
# copy block may carry its own framing without tripping this.
if printf '%s\n' "$OUT" | tail -15 | grep -Fq "$MARK"; then
  verdict "the goal-bearing block sits within the report's final 15 lines" 0
else
  verdict "the goal-bearing block sits within the report's final 15 lines" 1
fi

say "----------------------------------------------------------------"
if [ "$FAILED" -eq 0 ]; then say "[CKPT] PASS — board-52 outcome probes hold"; exit 0
else say "[CKPT] HOLD — one or more board-52 outcome probes failed"; exit 1; fi
