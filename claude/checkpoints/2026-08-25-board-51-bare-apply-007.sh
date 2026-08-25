#!/usr/bin/env bash
# Blind checkpoint — board 51 (bare `bale apply` resolution).
# Authored blind from the request at the 2026-08-25-continue-plan-003
# sitting, before implementation exists. Outcome contracts only.
# Exit 0 = pass; 1 = a probe failed (HOLD); 2 = harness broke.
# Offline by construction: local git fixtures under mktemp.
#
# The contract under test, from the ratified queued text: apply with
# no argument resolves the newest response tarball matching an open
# session across the search paths, echoes its identity, and takes a
# y/N; ambiguity — two candidates, or two open sessions — refuses
# loudly, never guesses. These probes pin the refusal half as
# outcomes: a bare `bale apply` is a real command whose refusals are
# bale refusals (the tool's exit-1 convention), never an argparse
# usage error (exit 2) — i.e. the bare spelling exists. The
# resolution happy path is the worker's own test surface; this
# oracle stays thin on purpose.
set -u
STAGING="$PWD"
BALE="$STAGING/bin/bale"
FAILED=0
say()  { printf '%s\n' "$*"; }
need() { command -v "$1" >/dev/null 2>&1 || { say "[CKPT-ERR] missing tool: $1"; exit 2; }; }
need git; need python3
[ -f "$BALE" ] || { say "[CKPT-ERR] bin/bale not found"; exit 2; }
fresh_repo() {
  local d
  d="$(mktemp -d)" || exit 2
  ( cd "$d" && git init -q && git config user.email ckpt@bale \
      && git config user.name ckpt && echo a > a.txt && echo b > b.txt \
      && git add -A && git commit -qm init ) || exit 2
  printf '%s' "$d"
}
verdict() {
  if [ "$2" -eq 0 ]; then say "[PASS] $1"; else say "[FAIL] $1"; FAILED=1; fi
}
open_session() {  # open_session REPO SLUG WRITEPATH
  ( cd "$1" && python3 "$BALE" pack "fixture goal for $2" --slug "$2" \
      --write "$3" --expects-probe no --no-readme >/dev/null 2>&1 ) || exit 2
}

# Probe 1: bare apply, zero open sessions -> a bale refusal, not an
# argparse usage error. (Today the positional is required: exit 2.)
R1="$(fresh_repo)"
( cd "$R1" && python3 "$BALE" apply </dev/null >/dev/null 2>&1 )
RC=$?
[ "$RC" -eq 1 ]; verdict "bare apply with no open session refuses as a bale refusal (exit 1, not argparse's 2) [got $RC]" $?

# Probe 2: bare apply, one open session, no response tarball anywhere
# on the search paths -> a bale refusal, never a guess.
R2="$(fresh_repo)"
open_session "$R2" fx-one a.txt
( cd "$R2" && python3 "$BALE" apply </dev/null >/dev/null 2>&1 )
RC=$?
[ "$RC" -eq 1 ]; verdict "bare apply with one open session and no candidate refuses (exit 1) [got $RC]" $?

# Probe 3: bare apply, two open sessions -> the ambiguity refusal,
# loud, never a guess. (Disjoint forecasts so both sessions open.)
R3="$(fresh_repo)"
open_session "$R3" fx-two-a a.txt
open_session "$R3" fx-two-b b.txt
( cd "$R3" && python3 "$BALE" apply </dev/null >/dev/null 2>&1 )
RC=$?
[ "$RC" -eq 1 ]; verdict "bare apply with two open sessions refuses on ambiguity (exit 1) [got $RC]" $?

# Probe 4 (boundary pin, expected true on both sides): the explicit
# spelling still works — apply with an argument that resolves nowhere
# fails as the existing not-found refusal, exit 1. Pins that adding
# the bare form does not disturb the argumented form's posture.
R4="$(fresh_repo)"
( cd "$R4" && python3 "$BALE" apply no-such-response.tar.gz </dev/null >/dev/null 2>&1 )
RC=$?
[ "$RC" -eq 1 ]; verdict "argumented apply keeps its not-found refusal (exit 1) [got $RC]" $?

say "----------------------------------------------------------------"
if [ "$FAILED" -eq 0 ]; then say "[CKPT] PASS — board-51 outcome probes hold"; exit 0
else say "[CKPT] HOLD — one or more board-51 outcome probes failed"; exit 1; fi
