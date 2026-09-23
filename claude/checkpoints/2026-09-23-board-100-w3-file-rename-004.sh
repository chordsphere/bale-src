#!/usr/bin/env bash
# Blind checkpoint — W3 of the 100 arc, the file rename (v1).
# Sitting: 2026-09-23-board-100-design-001 (sub-master desk). Authored from
# the W3 request before any worker output existed; rehearsed against the
# 0.4.41 tree (expected HOLD). Runs cwd = staging. Exit: 0 pass, 1 fail,
# 2 the oracle itself is broken (a failed control, TARBALL.md §7.5).
set -u
status=0
note()   { printf '[ckpt] %s\n' "$*"; }
failck() { printf '[ckpt] FAIL: %s\n' "$*"; status=1; }
broken() { printf '[ckpt] ERROR (oracle): %s\n' "$*"; exit 2; }

for f in bin/bale bin/VERSION validate.sh docs/TARBALL.md docs/DOCS.md docs/CODE.md docs/PLANNER.md; do
  [ -f "$f" ] || broken "missing $f in staging"; done
command -v python3 >/dev/null || broken "python3 missing"
[ -d tests ] || broken "no tests/ in staging"
note "controls passed"

# ---------- 1. The file ----------
if [ -f docs/AGENT.md ]; then
  note "docs/AGENT.md present"
  [ "$(head -n 1 docs/AGENT.md)" = "# AGENT.md" ] && note "first line verbatim" || failck "docs/AGENT.md first line is not '# AGENT.md'"
else failck "docs/AGENT.md absent"; fi
[ -f docs/CLAUDE.md ] && failck "docs/CLAUDE.md survives beside the rename" || note "docs/CLAUDE.md gone"

# ---------- 2. Version and changelog ----------
v="$(tr -d '[:space:]' < bin/VERSION)"
[ "$v" = "0.4.43" ] && note "bin/VERSION 0.4.43" || failck "bin/VERSION reads '$v', expected 0.4.43"
if [ -f claude/changelog/0.4.43.json ]; then
  python3 -c 'import json,sys; d=json.load(open("claude/changelog/0.4.43.json")); sys.exit(0 if d.get("version")=="0.4.43" and d.get("surfaces") else 1)' \
    && note "changelog record 0.4.43 parses" || failck "claude/changelog/0.4.43.json parses wrong or names no surfaces"
else failck "claude/changelog/0.4.43.json absent"; fi

# ---------- 3. A real pack against the applied install ----------
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
INSTALL="$TMP/install"; HOME_DIR="$TMP/home"; REPO="$TMP/repo"
mkdir -p "$INSTALL" "$HOME_DIR" "$REPO"
for tree in bin docs schemas tools; do cp -r "$PWD/$tree" "$INSTALL/$tree" || broken "install tree $tree missing"; done
printf '[user]\n\tname = Checkpoint Fixture\n\temail = ckpt@example.invalid\n' > "$HOME_DIR/.gitconfig"
run_bale() { HOME="$HOME_DIR" python3 "$INSTALL/bin/bale" "$@"; }
git -C "$REPO" init -q && printf 'fixture\n' > "$REPO/README.md" \
  && HOME="$HOME_DIR" git -C "$REPO" add -A && HOME="$HOME_DIR" git -C "$REPO" commit -qm fixture \
  || broken "fixture repo could not be built"
rep="$( cd "$REPO" && printf '' | run_bale pack "fixture rename" --slug ck-rename --read-only --no-readme --json 2>"$TMP/pack.err" )"
if [ -z "$rep" ]; then failck "fixture pack refused on the applied install (stderr: $(head -c 300 "$TMP/pack.err"))"
else
  printf '%s' "$rep" | python3 - <<'PYEOF' || status=1
import sys, json, tarfile
rep = json.load(sys.stdin)
fails = []
def ok(name, cond, extra=""):
    print(f"[ckpt] {'ok' if cond else 'FAIL'}: {name}" + ("" if cond else f" :: {extra}"))
    if not cond: fails.append(name)
with tarfile.open(rep["tarball"]) as t:
    names = t.getnames()
    root = [n for n in names if n.endswith("/manifest.json")][0].rsplit("/", 1)[0]
    ok("request root ships AGENT.md", f"{root}/AGENT.md" in names, str([n for n in names if n.endswith(".md")][:8]))
    ok("request root ships no CLAUDE.md", f"{root}/CLAUDE.md" not in names)
    m = json.load(t.extractfile(f"{root}/manifest.json"))
    ok("untyped pack stamps agent-decides", m.get("expects_probe") == "agent-decides", str(m.get("expects_probe")))
    cd = (m.get("provenance") or {}).get("contract_docs") or {}
    ok("contract_docs keyed by AGENT.md", "AGENT.md" in cd and "CLAUDE.md" not in cd, str(sorted(cd)))
sys.exit(1 if fails else 0)
PYEOF
fi
grep -q 'AGENT.md' "$TMP/pack.err" && note "pack report names AGENT.md" || note "(pack report on stderr does not mention AGENT.md; opener may be on stdout in --json mode — informational)"

# ---------- 4. validate.sh: passes on the applied tree, refuses a leftover ----------
COPY="$TMP/copy"; mkdir -p "$COPY"
for p in bin docs schemas tools tests install.sh validate.sh upgrade.sh README.md; do
  [ -e "$PWD/$p" ] && cp -r "$PWD/$p" "$COPY/$p"; done
chmod +x "$COPY/validate.sh" "$COPY/upgrade.sh" 2>/dev/null
if ( cd "$COPY" && bash validate.sh >"$TMP/v1.out" 2>&1 ); then note "validate.sh passes on the applied tree"
else failck "validate.sh fails on the applied tree: $(grep '\[FAIL\]' "$TMP/v1.out" | head -n 3 | tr '\n' ';')"; fi
printf '# stale\n' > "$COPY/docs/CLAUDE.md"
if ( cd "$COPY" && bash validate.sh >"$TMP/v2.out" 2>&1 ); then failck "validate.sh passes with a leftover docs/CLAUDE.md beside docs/AGENT.md"
else note "validate.sh refuses the leftover docs/CLAUDE.md"; fi

# ---------- 5. Cross-refs and enum sites in the docs ----------
for f in docs/AGENT.md docs/DOCS.md docs/CODE.md docs/PLANNER.md; do
  [ -f "$f" ] || continue
  n=$(grep -c 'CLAUDE\.md' "$f"); [ "$n" -eq 0 ] && note "$f names CLAUDE.md nowhere" || failck "$f still names CLAUDE.md on $n line(s)"
done
n=$(grep -c 'AGENT\.md' docs/TARBALL.md); [ "$n" -ge 20 ] && note "TARBALL.md cross-refs AGENT.md ($n lines)" || failck "TARBALL.md names AGENT.md on only $n line(s)"
n=$(grep -c 'agent-decides' docs/TARBALL.md); [ "$n" -ge 3 ] && note "TARBALL.md enum sites read agent-decides ($n lines)" || failck "agent-decides on $n line(s) of TARBALL.md; three sites expected"
grep -rq 'INJECTED_TOOLS' docs tests && failck "INJECTED_TOOLS still cited in docs/ or tests/" || note "identifier re-cited everywhere"

# ---------- 6. Suite green ----------
if python3 -m unittest discover -s tests >/dev/null 2>&1; then note "unit suite green"; else failck "unit suite not green"; fi

exit "$status"
