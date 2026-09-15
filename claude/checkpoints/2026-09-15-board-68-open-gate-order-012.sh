#!/bin/bash
# Blind checkpoint — board 68 (open gate ordering + riders), v1.
# Outcome-only, CLI-level against the staged bin/ in a scratch repo.
# cwd = staging root. The nested opens run --no-sandbox (the outer
# confinement is this checkpoint's own).
fails=0
pass() { echo "[PASS] $1"; }
failp() { echo "[FAIL] $1"; fails=$((fails+1)); }
ROOT="$PWD"; BALE="$ROOT/bin/bale"; CR="$ROOT/tools/craft_response.py"
S="$(mktemp -d /tmp/oracle-68.XXXXXX)"; trap 'rm -rf "$S"' EXIT
export HOME="$S" GIT_CONFIG_NOSYSTEM=1
R="$S/repo"; DL="$S/dl"; mkdir -p "$R/src" "$R/claude/checkpoints" "$DL"
echo x > "$R/src/a.py"; echo "# brief" > "$S/brief.md"
printf '#!/bin/bash\necho "[FAIL] pre-work"\nexit 1\n' > "$S/ck.sh"
git_() { git -C "$R" -c user.name=o -c user.email=o@o "$@"; }
( git -C "$R" init -q && git -C "$R" config user.name o && git -C "$R" config user.email o@o && git_ add -A && git_ commit -qm init ) || { failp "scratch repo"; exit 1; }
cfg() { printf '[staging]\nstrategy = "target-base"\n[apply]\nsearch_paths = ["%s"]\n%s' "$DL" "$1" > "$R/bale.toml"; git_ add -A; git_ commit -qm cfg; }
mk() { # mk STEM WRITE_PATH -> bundle in $DL
  python3 "$CR" --bundle "$1" --pack-arg "goal $1" --pack-arg=--slug --pack-arg "$1" --pack-arg=--include --pack-arg src --pack-arg=--write --pack-arg "$2" --brief "$S/brief.md" --checkpoint "$S/ck.sh" --out-dir "$DL" >/dev/null 2>&1; }
run_open() { ( cd "$R" && python3 "$BALE" open "$1" --no-sandbox </dev/null >"$S/out" 2>&1 ); }

cfg "" 
# P1: no [validation] base — the refusal names the resolved repo root.
mk o1 src/a.py; run_open o1.bale-bundle
if grep -q "no \[validation\] base" "$S/out" && grep -qF "$R" "$S/out"; then pass "no-validation-base refusal names the resolved project root"; else failp "no-validation-base refusal names the resolved project root"; fi

cfg $'[validation]\nbase = "claude/checkpoints/{sid}.sh"\n'
# P2: forecast-existence refusal fires with no dry-run.
mk o2 src/nope.py; run_open o2.bale-bundle
if grep -q "does not exist" "$S/out" && ! grep -q "dry-running bundle checkpoint" "$S/out"; then pass "forecast-existence refusal precedes the dry-run"; else failp "forecast-existence refusal precedes the dry-run"; fi

# P3: disjointness refusal fires with no dry-run (an open session holds src).
( cd "$R" && python3 "$BALE" pack "occupy" --slug occ --include src --write src --no-readme --checkpoint-file "$S/ck.sh" </dev/null >/dev/null 2>&1 )
mk o3 src/a.py; run_open o3.bale-bundle
if grep -q "forecast intersects" "$S/out" && ! grep -q "dry-running bundle checkpoint" "$S/out"; then pass "disjointness refusal precedes the dry-run"; else failp "disjointness refusal precedes the dry-run"; fi

unlock_all() { for sid in $(ls "$R/.bale/sessions" 2>/dev/null); do ( cd "$R" && python3 "$BALE" unlock "$sid" </dev/null >/dev/null 2>&1 ); done; }
# P4: the happy path still dry-runs and replays (fresh session state).
unlock_all
mk o4 src/a.py; run_open o4.bale-bundle
if grep -q "dry-running bundle checkpoint" "$S/out" && grep -q "expected-HOLD proof" "$S/out"; then pass "clean bundle still dry-runs with the expected-HOLD proof"; else failp "clean bundle still dry-runs with the expected-HOLD proof"; fi

# P5: single FORCE prefix on the --no-sandbox line (any transcript above suffices).
if grep -q "FORCE:" "$S/out" && ! grep -q "FORCE: FORCE:" "$S/out"; then pass "one FORCE prefix per line"; else failp "one FORCE prefix per line"; fi

# P6: whole-tree conflict remedy — a default-forecast open session; the refusal must not lead with narrowing this pack.
unlock_all
( cd "$R" && python3 "$BALE" pack "whole" --slug whole --no-readme --checkpoint-file "$S/ck.sh" </dev/null >/dev/null 2>&1 )
( cd "$R" && python3 "$BALE" pack "beside" --slug beside --include src --write src/a.py --no-readme --checkpoint-file "$S/ck.sh" </dev/null >"$S/out6" 2>&1 )
if grep -q "forecast intersects" "$S/out6" && ! grep -q "Narrow this pack" "$S/out6"; then pass "whole-tree conflict refusal does not say narrow this pack"; else failp "whole-tree conflict refusal does not say narrow this pack"; fi

# P7: bale.toml pulls tools.
if python3 - "$ROOT/bale.toml" <<'PY'
import sys,tomllib
c=tomllib.load(open(sys.argv[1],'rb')); sys.exit(0 if 'tools' in c.get('pack',{}).get('include_group_pulls',[]) else 1)
PY
then pass "release-surface group pulls tools"; else failp "release-surface group pulls tools"; fi

# P8: the emitted opener closes with the shape-rule sentence (whitespace collapsed).
( cd "$R" && python3 "$BALE" pack "opener" --slug opener --include src --read-only --no-readme </dev/null >"$S/out8" 2>&1 )
if tr -s '[:space:]' ' ' < "$S/out8" | grep -qF "Every turn you end in this session takes one machine-recognizable shape: a response tarball, a probe block, a light question block, or a clarification response; a question asked as prose is not a shape."; then pass "opener closes with the shape rule"; else failp "opener closes with the shape rule"; fi

[ "$fails" -eq 0 ] && exit 0 || exit 1
