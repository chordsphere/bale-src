#!/bin/bash
# Blind checkpoint — board 99a (outward docs), v1. Invariant-shaped:
# README facts derived from the tree; wizard transcript. cwd = staging root.
fails=0
pass() { echo "[PASS] $1"; }
failp() { echo "[FAIL] $1"; fails=$((fails+1)); }
ROOT="$PWD"; BALE="$ROOT/bin/bale"; RM="$ROOT/README.md"
S="$(mktemp -d /tmp/oracle-99a.XXXXXX)"; trap 'rm -rf "$S"' EXIT
export HOME="$S" GIT_CONFIG_NOSYSTEM=1
# P1: README names every verb bale --help lists.
missing=""
for v in $(python3 "$BALE" --help 2>/dev/null | awk '/^positional arguments:/{on=1;next} /^options:/{on=0} on && /^    [a-z]/{print $1}'); do grep -q -- "$v" "$RM" || missing="$missing $v"; done
if [ -z "$missing" ]; then pass "README names every verb"; else failp "README names every verb (missing:$missing)"; fi
# P2: README names every bin/*.py module and all five docs.
missing=""
for f in "$ROOT"/bin/bale_*.py; do b="$(basename "$f")"; grep -q "$b" "$RM" || missing="$missing $b"; done
for d in CLAUDE.md TARBALL.md DOCS.md CODE.md PLANNER.md; do grep -q "$d" "$RM" || missing="$missing $d"; done
if [ -z "$missing" ]; then pass "README names every bin module and doc"; else failp "README names every bin module and doc (missing:$missing)"; fi
# P3: stale facts gone.
if ! grep -q '2026-06-03' "$RM" && ! grep -qi 'four docs' "$RM"; then pass "README stale date and four-docs claim gone"; else failp "README stale date and four-docs claim gone"; fi
# P4: README names the light question block and bundles.
if grep -qi 'light question block' "$RM" && grep -qi 'bundle' "$RM"; then pass "README names the light block and bundles"; else failp "README names the light block and bundles"; fi
# P5: the wizard walks [probe] clipboard_command.
mkdir -p "$S/repo" && ( cd "$S/repo" && git init -q && git config user.name o && git config user.email o@o && git commit -q --allow-empty -m i && python3 "$BALE" config init </dev/null >"$S/wiz.out" 2>&1 )
if grep -q '\[probe\.clipboard_command\]' "$S/wiz.out"; then pass "wizard walks probe.clipboard_command"; else failp "wizard walks probe.clipboard_command"; fi
[ "$fails" -eq 0 ] && exit 0 || exit 1
