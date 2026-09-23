#!/usr/bin/env bash
# Blind checkpoint — W2 of the 100 arc, code surfaces (v1).
# Sitting: 2026-09-23-board-100-design-001 (sub-master desk). Authored from
# the W2 request before any worker output existed; rehearsed against the
# 0.4.41 tree (expected HOLD). Runs cwd = staging. Exit: 0 pass, 1 fail,
# 2 the oracle itself is broken (a failed control, TARBALL.md §7.5).
set -u
status=0
note()   { printf '[ckpt] %s\n' "$*"; }
failck() { printf '[ckpt] FAIL: %s\n' "$*"; status=1; }
broken() { printf '[ckpt] ERROR (oracle): %s\n' "$*"; exit 2; }

for f in bin/bale bin/VERSION schemas/request-manifest.schema.json schemas/response-manifest.schema.json BALE.md; do
  [ -f "$f" ] || broken "missing $f in staging"; done
command -v python3 >/dev/null || broken "python3 missing"
[ -d tests ] || broken "no tests/ in staging"
printf 'the Claude reads\n' | grep -qw 'Claude' || broken "noun detector cannot see the token"
note "controls passed"

# ---------- 1. Version and changelog ----------
v="$(tr -d '[:space:]' < bin/VERSION)"
[ "$v" = "0.4.42" ] && note "bin/VERSION 0.4.42" || failck "bin/VERSION reads '$v', expected 0.4.42"
if [ -f claude/changelog/0.4.42.json ]; then
  python3 -c 'import json,sys; d=json.load(open("claude/changelog/0.4.42.json")); sys.exit(0 if d.get("version")=="0.4.42" and d.get("surfaces") else 1)' \
    && note "changelog record 0.4.42 parses" || failck "claude/changelog/0.4.42.json parses wrong or names no surfaces"
else failck "claude/changelog/0.4.42.json absent"; fi

# ---------- 2. Schemas: enum alias, contract_docs oneOf, model_identity pattern ----------
python3 - <<'PYEOF' || status=1
import json, re, sys
fails = []
def ok(name, cond, extra=""):
    print(f"[ckpt] {'ok' if cond else 'FAIL'}: {name}" + ("" if cond else f" :: {extra}"))
    if not cond: fails.append(name)

req = json.load(open("schemas/request-manifest.schema.json"))
res = json.load(open("schemas/response-manifest.schema.json"))
text_req = json.dumps(req); text_res = json.dumps(res)

def find(node, key):
    if isinstance(node, dict):
        if key in node: yield node[key]
        for v in node.values(): yield from find(v, key)
    elif isinstance(node, list):
        for v in node: yield from find(v, key)

enums = [e for e in find(req, "enum") if isinstance(e, list) and "claude-decides" in e]
ok("request schema: expects_probe enum admits agent-decides", any("agent-decides" in e for e in enums), str(enums))
ok("request schema: expects_probe enum keeps claude-decides", any("claude-decides" in e for e in enums))

def required_sets(schema):
    return [set(r) for r in find(schema, "required") if isinstance(r, list) and ("CLAUDE.md" in r or "AGENT.md" in r)]
for label, s in (("request", req), ("response", res)):
    sets = required_sets(s)
    ok(f"{label} schema: contract_docs admits the AGENT.md key set", any("AGENT.md" in r for r in sets), str(sets))
    ok(f"{label} schema: contract_docs keeps the CLAUDE.md key set", any("CLAUDE.md" in r for r in sets))

props = list(find(res, "model_identity"))
pat = None
for p in props:
    if isinstance(p, dict) and "pattern" in p: pat = p["pattern"]
ok("response schema: model_identity carries a pattern", pat is not None)
if pat:
    rx = re.compile(pat)
    live = ["Claude Fable 5.1, self-reported", "Claude Fable 5.1 (self-reported)",
            "Claude (Anthropic); exact model string not visible to the session"]
    good = ["anthropic:claude-fable-5.1", "anthropic:unknown"]
    ok("pattern rejects the three live spellings", not any(rx.fullmatch(s) for s in live))
    ok("pattern accepts the canonical spellings", all(rx.fullmatch(s) for s in good), pat)
desc = [p.get("description", "") for p in props if isinstance(p, dict)]
ok("model_identity description names <vendor>:<model>", any("<vendor>:<model>" in d for d in desc))
inc = [p.get("description", "") for p in find(res, "includes_missing") if isinstance(p, dict)]
ok("includes_missing description names decision:", any("decision:" in d for d in inc))
sys.exit(1 if fails else 0)
PYEOF

# ---------- 3. CLI: the alias is admitted, the default not yet flipped ----------
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
INSTALL="$TMP/install"; HOME_DIR="$TMP/home"; REPO="$TMP/repo"
mkdir -p "$INSTALL" "$HOME_DIR" "$REPO"
for tree in bin docs schemas tools; do cp -r "$PWD/$tree" "$INSTALL/$tree" || broken "install tree $tree missing"; done
printf '[user]\n\tname = Checkpoint Fixture\n\temail = ckpt@example.invalid\n' > "$HOME_DIR/.gitconfig"
run_bale() { HOME="$HOME_DIR" python3 "$INSTALL/bin/bale" "$@"; }
git -C "$REPO" init -q && printf 'fixture\n' > "$REPO/README.md" \
  && HOME="$HOME_DIR" git -C "$REPO" add -A && HOME="$HOME_DIR" git -C "$REPO" commit -qm fixture \
  || broken "fixture repo could not be built"
python3 "$INSTALL/bin/bale" pack --help 2>/dev/null | grep -q 'agent-decides' \
  && note "pack --help names agent-decides" || failck "pack --help does not name agent-decides"
stamp() {  # $1 = slug, rest = extra flags; prints the stamped expects_probe
  ( cd "$REPO" && printf '' | run_bale pack "fixture $1" --slug "$1" --read-only --no-readme --json "${@:2}" 2>"$TMP/$1.err" ) \
    | python3 -c '
import sys, json, tarfile
rep = json.load(sys.stdin)
with tarfile.open(rep["tarball"]) as t:
    m = [n for n in t.getnames() if n.endswith("/manifest.json")][0]
    print(json.load(t.extractfile(m))["expects_probe"])' 2>/dev/null
}
got="$(stamp ck-alias --expects-probe agent-decides)"
[ "$got" = "agent-decides" ] && note "a pack typed --expects-probe agent-decides stamps it" \
  || failck "typed agent-decides, manifest stamped '$got' (stderr: $(head -c 200 "$TMP/ck-alias.err" 2>/dev/null))"
got="$(stamp ck-default)"
[ "$got" = "claude-decides" ] && note "an untyped pack still stamps claude-decides (W3 flips it)" \
  || failck "untyped pack stamped '$got'; the default flip is W3's (stderr: $(head -c 200 "$TMP/ck-default.err" 2>/dev/null))"

# ---------- 4. Layer 4 hardcodes gone; constant renamed; noun gone ----------
grep -q '"claude" */ *"telemetry"' bin/bale && failck "bin/bale still hardcodes claude/telemetry" || note "bin/bale telemetry path keyed"
grep -q '"claude" */ *"telemetry"' bin/bale_report.py && failck "bale_report.py still hardcodes claude/telemetry" || note "bale_report.py telemetry path keyed"
grep -qE '_TELEMETRY_PREFIX *= *"claude/telemetry/"' bin/bale_rollback.py && failck "bale_rollback.py still hardcodes the prefix" || note "bale_rollback.py prefix keyed"
grep -q 'agent_dir' BALE.md && note "BALE.md documents agent_dir" || failck "BALE.md does not document agent_dir"
grep -rq 'INJECTED_TOOLS' bin/ && failck "INJECTED_TOOLS survives in bin/" || note "INJECTED_TOOLS gone from bin/"
hits="$(grep -rnw --exclude-dir=__pycache__ 'Claude' bin tools schemas 2>/dev/null)"
[ -z "$hits" ] && note "noun gone from bin/, tools/, schemas/" \
  || failck "capitalized Claude remains in code: $(printf '%s\n' "$hits" | wc -l | tr -d ' ') line(s), first: $(printf '%s\n' "$hits" | head -n 1)"

# ---------- 5. What W2 must not have done ----------
[ -f docs/CLAUDE.md ] && [ ! -f docs/AGENT.md ] && note "file name untouched (W3's)" || failck "the file rename is W3's"

# ---------- 6. Suite green ----------
if python3 -m unittest discover -s tests >/dev/null 2>&1; then note "unit suite green"; else failck "unit suite not green"; fi

exit "$status"
