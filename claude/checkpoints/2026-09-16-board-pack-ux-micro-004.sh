#!/bin/bash
# Blind checkpoint — pack-UX micro, v1. Outcome-only, CLI-level in a
# scratch repo (piped stdin; read-only packs where a forecast is not
# the point, so packs never collide). cwd = staging root.
fails=0
pass() { echo "[PASS] $1"; }
failp() { echo "[FAIL] $1"; fails=$((fails+1)); }
ROOT="$PWD"; BALE="$ROOT/bin/bale"
S="$(mktemp -d /tmp/oracle-pux.XXXXXX)"; trap 'rm -rf "$S"' EXIT
export HOME="$S" GIT_CONFIG_NOSYSTEM=1
R="$S/repo"; mkdir -p "$R/src" "$R/docs" "$R/tests"
echo x > "$R/src/a.py"; echo d > "$R/docs/x.md"; printf 'from tests.helper_b import X\nimport os\n' > "$R/tests/test_a.py"; echo 'X=1' > "$R/tests/helper_b.py"
( cd "$R" && git init -q && git config user.name o && git config user.email o@o && printf '[staging]\nstrategy = "target-base"\n' > bale.toml && git add -A && git commit -qm i ) || { failp "scratch repo"; exit 1; }
echo y > "$R/src/untracked.py"
pk() { ( cd "$R" && python3 "$BALE" pack "g" "$@" --no-readme </dev/null >"$S/out" 2>&1 ); }
# P1: a .baleignore negation is attributed to .baleignore, not the session.
printf '!keep.py\n' > "$R/.baleignore"
pk --slug n1 --include src --read-only
if grep -q '\.baleignore' "$S/out" && ! grep -q 'invalid session exclude pattern' "$S/out"; then pass "baleignore negation attributed to .baleignore"; else failp "baleignore negation attributed to .baleignore"; fi
rm -f "$R/.baleignore"
pk --slug n2 --include src --read-only --exclude '!keep.py'
if grep -q 'invalid session exclude pattern' "$S/out"; then pass "--exclude negation still attributed to the session"; else failp "--exclude negation still attributed to the session"; fi
# P2: forecast/include mismatch warns, naming the path, and still packs.
pk --slug m --include src --write docs/x.md
if grep -q 'docs/x.md' "$S/out" && grep -qi 'warn' "$S/out" && ! grep -q '\[bale\] error' "$S/out"; then pass "forecast-not-included warning names the path"; else failp "forecast-not-included warning names the path"; fi
# P3: verbose names the untracked drop.
pk --slug v --include src --read-only --verbose
if grep -q 'verbose: drop src/untracked.py (not tracked)' "$S/out"; then pass "verbose names the untracked drop"; else failp "verbose names the untracked drop"; fi
# P4: included test importing an excluded tests module warns, naming both; stdlib import does not.
pk --slug t --include tests/test_a.py --read-only
if grep -q 'tests/test_a.py' "$S/out" && grep -q 'helper_b' "$S/out" && grep -qi 'warn' "$S/out" && ! grep -q '\[bale\] error' "$S/out"; then pass "test-import-outside-includes warning"; else failp "test-import-outside-includes warning"; fi
if ! grep -qi 'warn.*\bos\b' "$S/out"; then pass "no warning for a stdlib import"; else failp "no warning for a stdlib import"; fi
# P5: opener pin relocated.
if grep -q 'OpenerShapeSentenceTest' "$ROOT/tests/test_pack_opener.py" && ! grep -q 'OpenerShapeSentenceTest' "$ROOT/tests/test_pack_guards.py"; then pass "opener shape pin lives in test_pack_opener"; else failp "opener shape pin lives in test_pack_opener"; fi
[ "$fails" -eq 0 ] && exit 0 || exit 1
