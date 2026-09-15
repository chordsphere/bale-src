#!/bin/bash
# Blind checkpoint — board 102 (explicit-name tarball resolution), v1.
# Outcome-only: runs the staged CLI against a scratch repo. cwd is the
# staging root. Exit 0 = all probes pass, 1 = a probe failed.
fails=0
pass() { echo "[PASS] $1"; }
failp() { echo "[FAIL] $1"; fails=$((fails+1)); }
ROOT="$PWD"
BALE="$ROOT/bin/bale"
S="$(mktemp -d /tmp/oracle-102.XXXXXX)"
trap 'rm -rf "$S"' EXIT
export HOME="$S" GIT_CONFIG_NOSYSTEM=1
mkdir -p "$S/repo" "$S/dl"
( cd "$S/repo" && git init -q && git -c user.name=o -c user.email=o@o commit -q --allow-empty -m init ) || { failp "scratch repo init"; echo "[SKIP] remaining probes: scratch unavailable"; exit 1; }
printf '[staging]\nstrategy = "target-base"\n[apply]\nsearch_paths = ["%s"]\n' "$S/dl" > "$S/repo/bale.toml"
TYPED="response-2026-09-15-oracle-001.tar.gz"
TWIN="$S/dl/response-2026-09-15-oracle-001 (1).tar.gz"
: > "$TWIN"
QUOTED="'$TWIN'"

# P1: apply miss lists the (1) twin as a complete quoted apply line.
out="$(cd "$S/repo" && python3 "$BALE" apply "$TYPED" </dev/null 2>&1)"
if printf '%s\n' "$out" | grep -qF "bale apply $QUOTED"; then pass "apply miss lists near-name as quoted apply line"; else failp "apply miss lists near-name as quoted apply line"; fi

# P2: retry miss lists the same twin as a complete quoted retry line.
out="$(cd "$S/repo" && python3 "$BALE" retry "$TYPED" </dev/null 2>&1)"
if printf '%s\n' "$out" | grep -qF "bale retry $QUOTED"; then pass "retry miss lists near-name as quoted retry line"; else failp "retry miss lists near-name as quoted retry line"; fi

# P3: a miss with no candidates still names the searched directories and exits non-zero.
rm -f "$TWIN"
( cd "$S/repo" && python3 "$BALE" apply "$TYPED" </dev/null >"$S/o3" 2>&1 ); rc=$?
if [ "$rc" -ne 0 ] && grep -q "$S/dl" "$S/o3"; then pass "zero-candidate miss still refuses naming the searched dirs"; else failp "zero-candidate miss still refuses naming the searched dirs"; fi

# P4: BALE.md carries the desk's sentence byte-exact.
if grep -qF 'On a miss, apply and retry list every near-name candidate in the searched directories — the typed name minus its .tar.gz suffix as a prefix — as complete quoted command lines, newest first.' "$ROOT/BALE.md"; then pass "BALE.md near-name sentence present verbatim"; else failp "BALE.md near-name sentence present verbatim"; fi

# P5: version bumped.
if [ "$(tr -d '[:space:]' < "$ROOT/bin/VERSION")" = "0.4.33" ]; then pass "bin/VERSION is 0.4.33"; else failp "bin/VERSION is 0.4.33"; fi

[ "$fails" -eq 0 ] && exit 0 || exit 1
