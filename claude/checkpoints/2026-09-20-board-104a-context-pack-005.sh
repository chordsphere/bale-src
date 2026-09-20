#!/usr/bin/env bash
# Blind checkpoint v1 — board 104a, the context pack (bale pack --context).
# Authored 2026-09-20 by the master 2026-09-20-continue-plan-004, from the
# request, before any implementation existed. Outcome-only.
#
# Runs from the root of the tree under judgment. Writes ONE scratch
# directory under the current directory, removed on exit; python runs
# with -B, so no bytecode is left. No network.
#
# Verdict lines carry the label alone; any detail is on a following
# "  detail:" line (labels travel to the worker on a HOLD, detail must not).
# Exit 0: every probe passed. Exit 1: a probe failed. Exit 2: the oracle
# itself could not run (an anchor failed).
set -u
ROOT="$(pwd)"
SCR="$ROOT/.ckpt-104a-scratch.$$"
fails=0
cleanup() { rm -rf "$SCR"; }
trap cleanup EXIT

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; [ -n "${2:-}" ] && echo "  detail: $2"; fails=$((fails+1)); }
anchor_fail() { echo "[ERROR] anchor: $1"; [ -n "${2:-}" ] && echo "  detail: $2"; exit 2; }

# ---- anchors -------------------------------------------------------------
[ -f "$ROOT/bin/bale" ] || anchor_fail "bin/bale exists"
[ -f "$ROOT/docs/TARBALL.md" ] || anchor_fail "docs/TARBALL.md exists"
command -v python3 >/dev/null || anchor_fail "python3 is on PATH"
command -v git >/dev/null || anchor_fail "git is on PATH"
for h in '### 3.1 Shape' '### 3.2 manifest.json' '### 3.4 Authoring a request with `bale pack`' '## 4. Probe' '### 5.8 diagnostics.json (required in bailout responses)' '### 5.9 Clarification response'; do
  grep -qxF -- "$h" "$ROOT/docs/TARBALL.md" || anchor_fail "TARBALL.md heading anchors are present" "$h"
done
python3 -B "$ROOT/bin/bale" --version >/dev/null 2>&1 || anchor_fail "bin/bale runs"
mkdir -p "$SCR/home" || anchor_fail "scratch directory is writable"
echo "[PASS] anchors"

export HOME="$SCR/home"
export GIT_AUTHOR_NAME=oracle GIT_AUTHOR_EMAIL=oracle@example.invalid
export GIT_COMMITTER_NAME=oracle GIT_COMMITTER_EMAIL=oracle@example.invalid
export GIT_CONFIG_NOSYSTEM=1
unset BALE_INSTALL 2>/dev/null || true

make_fixture() {  # one fresh committed repo per scenario
  local d="$1"
  mkdir -p "$d/sub" || return 1
  printf 'alpha-104a\n' > "$d/a.txt"
  printf '# bravo-104a\n' > "$d/sub/b.md"
  ( cd "$d" && git init -q -b main . && git add -A && git commit -qm init ) >/dev/null 2>&1
}

# ---- scenario C: the context pack ----------------------------------------
CTX="$SCR/ctxfixture-tree"
make_fixture "$CTX" || anchor_fail "fixture repo builds"
( cd "$CTX" && python3 -B "$ROOT/bin/bale" pack --context </dev/null >"$SCR/ctx.out" 2>&1 )
ctx_rc=$?

L="context pack: exits 0 with piped stdin"
if [ "$ctx_rc" -eq 0 ]; then pass "$L"; else fail "$L" "exit $ctx_rc"; fi

TB="$(find "$CTX" -type f -name '*ctxfixture-tree*.tar.gz' 2>/dev/null | head -1)"
L="context pack: one tarball named for the directory lands under it"
if [ -n "$TB" ]; then pass "$L"; else fail "$L" "no *ctxfixture-tree*.tar.gz under the fixture"; fi

L="context pack: the tarball carries the tree's files byte for byte"
L2="context pack: the tarball is not a request (no session stamp, no injected docs or tools)"
if [ -n "$TB" ]; then
  out="$(python3 -B - "$TB" <<'PY'
import sys, tarfile, json
want = {"a.txt": b"alpha-104a\n", "sub/b.md": b"# bravo-104a\n"}
injected = {"CLAUDE.md", "TARBALL.md", "DOCS.md", "CODE.md", "PLANNER.md",
            "craft_response.py", "response_lint.py"}
found, bad_inj, stamped = set(), [], []
with tarfile.open(sys.argv[1], "r:gz") as tf:
    for m in tf.getmembers():
        if not m.isfile():
            continue
        name = m.name.lstrip("./")
        base = name.rsplit("/", 1)[-1]
        data = tf.extractfile(m).read()
        for w, b in want.items():
            if (name == w or name.endswith("/" + w)) and data == b:
                found.add(w)
        if base in injected:
            bad_inj.append(name)
        if base == "manifest.json":
            try:
                if "session_id" in json.loads(data.decode("utf-8")):
                    stamped.append(name)
            except Exception:
                pass
print("FILES", "ok" if found == set(want) else "missing:" + ",".join(sorted(set(want) - found)))
print("REQ", "ok" if not bad_inj and not stamped else "present:" + ",".join(bad_inj + stamped))
PY
)" || out="FILES error
REQ error"
  f="$(printf '%s\n' "$out" | sed -n 's/^FILES //p')"; r="$(printf '%s\n' "$out" | sed -n 's/^REQ //p')"
  if [ "$f" = ok ]; then pass "$L"; else fail "$L" "$f"; fi
  if [ "$r" = ok ]; then pass "$L2"; else fail "$L2" "$r"; fi
else
  fail "$L" "no tarball to read"; fail "$L2" "no tarball to read"
fi

# ---- scenario N: the control, a normal pack in its own fixture -------------
CTL="$SCR/ctlfixture-tree"
make_fixture "$CTL" || anchor_fail "control fixture repo builds"
( cd "$CTL" && python3 -B "$ROOT/bin/bale" pack "control goal" --slug ctl --read-only --no-readme </dev/null >"$SCR/ctl.out" 2>&1 )
ctl_rc=$?
ctl_ok=1
[ "$ctl_rc" -eq 0 ] || ctl_ok=0
[ -n "$(find "$CTL/.bale/sessions" -mindepth 1 -maxdepth 1 2>/dev/null | head -1)" ] || ctl_ok=0
[ -n "$(find "$CTL" -path '*/telemetry/*.json' 2>/dev/null | head -1)" ] || ctl_ok=0
[ -n "$(find "$CTL/.bale" -maxdepth 1 -name 'counter-*' 2>/dev/null | head -1)" ] || ctl_ok=0
grep -qF 'end session opener' "$SCR/ctl.out" || ctl_ok=0
L="control: a normal pack still opens a session, writes telemetry, and prints its opener"
if [ "$ctl_ok" -eq 1 ]; then pass "$L"; else fail "$L" "exit $ctl_rc; see the detectors"; fi

L="context pack: no sid — nothing under .bale/sessions, no day counter, no telemetry record"
if [ "$ctl_ok" -ne 1 ]; then fail "$L" "control failed, detectors unproven"
elif [ "$ctx_rc" -ne 0 ]; then fail "$L" "context pack did not run"
else
  s="$(find "$CTX/.bale/sessions" -mindepth 1 -maxdepth 1 2>/dev/null | head -1)"
  t="$(find "$CTX" -path '*/telemetry/*.json' 2>/dev/null | head -1)"
  c="$(find "$CTX/.bale" -maxdepth 1 -name 'counter-*' 2>/dev/null | head -1)"
  if [ -z "$s$t$c" ]; then pass "$L"; else fail "$L" "found: ${s:+session }${t:+telemetry }${c:+counter}"; fi
fi

L="context pack: no opener is printed"
if [ "$ctl_ok" -ne 1 ]; then fail "$L" "control failed, detector unproven"
elif [ "$ctx_rc" -ne 0 ]; then fail "$L" "context pack did not run"
elif grep -qF 'end session opener' "$SCR/ctx.out"; then fail "$L" "opener sentinel present"
else pass "$L"; fi

# ---- help ------------------------------------------------------------------
L="pack --help lists --context"
if python3 -B "$ROOT/bin/bale" pack --help 2>&1 | grep -qF -- '--context'; then pass "$L"; else fail "$L"; fi

# ---- the global doc ----------------------------------------------------------
docout="$(python3 -B - "$ROOT/docs/TARBALL.md" "$ROOT/bin/bale_pack.py" <<'PY'
import sys, re
text = open(sys.argv[1], encoding="utf-8").read()
lines = text.split("\n")
def span(start, end):
    i = lines.index(start); j = lines.index(end)
    return lines[i:j] if i < j else []
norm = lambda s: re.sub(r"\s+", " ", s)
VERB = ("A context tarball is reading material, not a request: it carries "
        "no session id and no opener, and it owes nothing back.")
s31 = span("### 3.1 Shape", "### 3.2 manifest.json")
s34 = span("### 3.4 Authoring a request with `bale pack`", "## 4. Probe")
s58 = span("### 5.8 diagnostics.json (required in bailout responses)", "### 5.9 Clarification response")
print("V31", "ok" if VERB in norm(" ".join(s31)) else "absent")
print("F31", "ok" if "--context" in "\n".join(s31) else "absent")
print("ROW", "ok" if any(l.startswith("| `--context`") for l in s34) else "absent")
j58 = norm(" ".join(s58))
print("S58", "ok" if ("eventual `bale stats`" not in norm(text) and "bale stats" in j58) else "stale-or-unnamed")
pk = open(sys.argv[2], encoding="utf-8").read()
print("CMT", "ok" if "carries no successor pointer" not in pk else "present")
PY
)" || docout=""
dv() { printf '%s\n' "$docout" | sed -n "s/^$1 //p"; }
L="TARBALL.md 3.1 carries the verbatim context-tarball sentence"
[ "$(dv V31)" = ok ] && pass "$L" || fail "$L" "$(dv V31)"
L="TARBALL.md 3.1 names the --context flag"
[ "$(dv F31)" = ok ] && pass "$L" || fail "$L" "$(dv F31)"
L="TARBALL.md 3.4 flag table has a --context row"
[ "$(dv ROW)" = ok ] && pass "$L" || fail "$L" "$(dv ROW)"
L="TARBALL.md 5.8 names bale stats and no longer calls it eventual"
[ "$(dv S58)" = ok ] && pass "$L" || fail "$L" "$(dv S58)"
L="rider: cmd_pack's stale successor-pointer comment is gone"
[ "$(dv CMT)" = ok ] && pass "$L" || fail "$L" "$(dv CMT)"

if [ "$fails" -eq 0 ]; then echo "checkpoint: PASS"; exit 0; fi
echo "checkpoint: $fails probe(s) failed"; exit 1
