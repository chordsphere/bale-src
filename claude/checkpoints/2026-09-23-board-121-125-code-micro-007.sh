#!/usr/bin/env bash
# Blind checkpoint v1 — the four-small code micro (rows 121, 123, 124,
# 125), authored 2026-09-23 at the 2026-09-23-continue-plan-006 desk,
# from the request, before any implementation exists.
#
# Outcome contracts only: what must be true of the applied tree, never
# how the worker got there. Runs from the staging copy of the applied
# tree (its cwd); drives the staged bin/bale inside scratch repos under
# mktemp (a private tmpfs in the sandbox), with a repo-local git
# identity and [sandbox] enabled = false in each scratch bale.toml so
# inner applies nest no namespace. Every scratch repo is fresh per
# scenario.
#
# Verdict lines carry the label alone; detail goes on a following
# "  detail:" line (labels travel to the worker on a HOLD, detail never
# does). Exit 1 = at least one probe failed; exit 2 = the oracle itself
# broke (a failed control, a fixture that could not be built) — never a
# verdict on the work.

set -u
STAGING="$(pwd)"
BALE="$STAGING/bin/bale"
CRAFTER="$STAGING/tools/craft_response.py"
fails=0

pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; [ -n "${2:-}" ] && echo "  detail: $2"; fails=$((fails+1)); }
oracle_error() { echo "[ERROR] $1" >&2; exit 2; }

# ---- control: the oracle's own detectors work ------------------------
[ -x "$BALE" ] || oracle_error "control: staged bin/bale is not executable at $BALE"
[ -f "$CRAFTER" ] || oracle_error "control: staged tools/craft_response.py missing"
command -v git >/dev/null 2>&1 || oracle_error "control: git not on PATH"
command -v python3 >/dev/null 2>&1 || oracle_error "control: python3 not on PATH"
SCRATCH="$(mktemp -d)" || oracle_error "control: mktemp failed"
trap 'rm -rf "$SCRATCH"' EXIT
export HOME="$SCRATCH/home"
mkdir -p "$HOME" || oracle_error "control: could not create scratch HOME"
echo "control ok: staged bale, crafter, git, python3, scratch $SCRATCH"

# A fresh scratch repo per scenario: name, extra bale.toml lines.
new_repo() {
  local dir="$SCRATCH/$1"
  mkdir -p "$dir" || oracle_error "fixture: mkdir $dir"
  ( cd "$dir" \
    && git init -q -b main \
    && git config user.email oracle@example.invalid \
    && git config user.name oracle \
    && printf '[sandbox]\nenabled = false\n%s' "$2" > bale.toml \
    && echo seed > f.txt \
    && git add -A && git commit -qm init ) \
    || oracle_error "fixture: could not build scratch repo $1"
  echo "$dir"
}

# One-line brief for the bundles the fixtures open.
BRIEF="$SCRATCH/brief.md"; printf '# oracle fixture brief\n\nread-only.\n' > "$BRIEF"

# ---- probe 1 (row 121): argv-only gates run before the supersession
#      exchange writes another session's state --------------------------
# Fixture: a checkpoint-configured repo with a tracked file under the
# checkpoint subtree; a read-only parent session; a bundle whose argv
# names the checkpoint subtree in --include (refused by the read-side
# blindness gate) and --supersedes the parent with a pre-answered accept.
# Outcome: the open refuses, and the parent's record is still open — no
# superseded-by-split closure was written by a pack that produced no
# child.
R1="$(new_repo r121 $'[validation]\nbase = "claude/checkpoints/{sid}.sh"\n')"
( cd "$R1" && mkdir -p claude/checkpoints \
  && printf '#!/usr/bin/env bash\nexit 0\n' > claude/checkpoints/old.sh \
  && git add -A && git commit -qm ckpt ) || oracle_error "fixture r121: checkpoint dir"
( cd "$R1" && "$BALE" pack "parent" --slug parent --read-only --include f.txt \
    --no-readme --expects-probe no </dev/null >"$SCRATCH/r121-parent.out" 2>&1 ) \
  || oracle_error "fixture r121: parent pack failed: $(tail -n 3 "$SCRATCH/r121-parent.out")"
PARENT="$(ls "$R1/claude/telemetry/" 2>/dev/null | sed 's/\.json$//' | head -n 1)"
[ -n "$PARENT" ] || oracle_error "fixture r121: no parent record"
( cd "$R1" && python3 "$CRAFTER" --bundle oracle-child --brief "$BRIEF" \
    --pack-arg child --pack-arg=--slug --pack-arg child --pack-arg=--read-only \
    --pack-arg=--include --pack-arg claude/checkpoints \
    --pack-arg=--supersedes --pack-arg "$PARENT" \
    --pack-arg=--expects-probe --pack-arg no \
    --pre-answered "supersede=$PARENT" --out-dir "$R1" >"$SCRATCH/r121-bundle.out" 2>&1 ) \
  || oracle_error "fixture r121: bundle emission failed: $(tail -n 3 "$SCRATCH/r121-bundle.out")"
( cd "$R1" && "$BALE" open oracle-child.bale-bundle </dev/null >"$SCRATCH/r121-open.out" 2>&1 )
open_exit=$?
parent_state="$(python3 - "$R1/claude/telemetry/$PARENT.json" <<'PY'
import json, sys
r = json.load(open(sys.argv[1]))
closed = [a for a in r.get("attempts", []) if a.get("closure_reason") == "superseded-by-split"]
print(f"{r.get('outcome')} superseded-closures={len(closed)}")
PY
)"
if [ "$open_exit" -ne 0 ] && [ "$parent_state" = "opened superseded-closures=0" ]; then
  pass "refused-pack-leaves-supersedes-parent-open"
else
  fail "refused-pack-leaves-supersedes-parent-open" \
       "open exit $open_exit; parent record: $parent_state"
fi

# ---- probe 2 (row 123): a second open of one bundle-born session
#      records a desk suffix under the same sid, unrefused ---------------
# Fixture: a plain repo; one read-only bundle opened twice, piped stdin.
# Outcome: the second open exits 0; exactly one session is open and one
# record exists; that record carries at least two `opened` attempts and
# its last `opened` attempt carries a non-empty `desk` string.
R2="$(new_repo r123 "")"
( cd "$R2" && python3 "$CRAFTER" --bundle oracle-desk --brief "$BRIEF" \
    --pack-arg desk --pack-arg=--slug --pack-arg desk --pack-arg=--read-only \
    --pack-arg=--include --pack-arg f.txt --pack-arg=--expects-probe --pack-arg no \
    --out-dir "$R2" >"$SCRATCH/r123-bundle.out" 2>&1 ) \
  || oracle_error "fixture r123: bundle emission failed"
( cd "$R2" && "$BALE" open oracle-desk.bale-bundle </dev/null >"$SCRATCH/r123-open1.out" 2>&1 ) \
  || oracle_error "fixture r123: first open failed: $(tail -n 3 "$SCRATCH/r123-open1.out")"
( cd "$R2" && "$BALE" open oracle-desk.bale-bundle </dev/null >"$SCRATCH/r123-open2.out" 2>&1 )
second_exit=$?
desk_state="$(python3 - "$R2" <<'PY'
import glob, json, os, sys
repo = sys.argv[1]
records = sorted(glob.glob(os.path.join(repo, "claude", "telemetry", "*.json")))
sessions = sorted(os.listdir(os.path.join(repo, ".bale", "sessions"))) \
    if os.path.isdir(os.path.join(repo, ".bale", "sessions")) else []
opened = []
desk = None
if len(records) == 1:
    r = json.load(open(records[0]))
    opened = [a for a in r.get("attempts", []) if a.get("outcome") == "opened"]
    if opened:
        d = opened[-1].get("desk")
        desk = d if isinstance(d, str) and d.strip() else None
print(f"records={len(records)} sessions={len(sessions)} opened={len(opened)} "
      f"desk={'set' if desk else 'unset'}")
PY
)"
if [ "$second_exit" -eq 0 ] && [ "$desk_state" = "records=1 sessions=1 opened=2 desk=set" ]; then
  pass "second-open-same-sid-records-desk"
else
  fail "second-open-same-sid-records-desk" "second open exit $second_exit; $desk_state"
fi

# ---- probe 3 (row 124): emitted messages name the configured agent_dir
# Fixture: a repo whose [layout] agent_dir is "agent". Three emitted
# surfaces: the dossier miss, the stats verb's help text, and the
# supersession close line. Outcome: each names agent/telemetry/ (or no
# telemetry path at all) and none says claude/telemetry/.
R3="$(new_repo r124 $'[layout]\nagent_dir = "agent"\n')"
dossier="$(cd "$R3" && "$BALE" stats --sid 2026-01-01-nowhere-001 </dev/null 2>&1)"
helptext="$(cd "$R3" && "$BALE" stats --help </dev/null 2>&1)"
( cd "$R3" && "$BALE" pack "p" --slug p --read-only --include f.txt --no-readme \
    --expects-probe no </dev/null >"$SCRATCH/r124-parent.out" 2>&1 ) \
  || oracle_error "fixture r124: parent pack failed"
P3SID="$(ls "$R3/agent/telemetry/" 2>/dev/null | sed 's/\.json$//' | head -n 1)"
[ -n "$P3SID" ] || oracle_error "fixture r124: parent record not under agent/telemetry/ (the configured home)"
( cd "$R3" && python3 "$CRAFTER" --bundle oracle-sup --brief "$BRIEF" \
    --pack-arg c --pack-arg=--slug --pack-arg c --pack-arg=--read-only \
    --pack-arg=--include --pack-arg f.txt --pack-arg=--supersedes --pack-arg "$P3SID" \
    --pack-arg=--expects-probe --pack-arg no --pre-answered "supersede=$P3SID" \
    --out-dir "$R3" >"$SCRATCH/r124-bundle.out" 2>&1 ) \
  || oracle_error "fixture r124: bundle emission failed"
supersede_out="$(cd "$R3" && "$BALE" open oracle-sup.bale-bundle </dev/null 2>&1)"
p3_bad=""
case "$dossier" in *claude/telemetry*) p3_bad="$p3_bad dossier";; esac
case "$helptext" in *claude/telemetry*) p3_bad="$p3_bad stats-help";; esac
case "$supersede_out" in *claude/telemetry*) p3_bad="$p3_bad supersession-close";; esac
case "$dossier" in *agent/telemetry*) ;; *) p3_bad="$p3_bad dossier-names-no-agent-dir";; esac
if [ -z "$p3_bad" ]; then
  pass "messages-render-configured-agent-dir"
else
  fail "messages-render-configured-agent-dir" "surfaces still spelling the default:$p3_bad"
fi

# ---- probe 4 (row 125): the probe scaffold names caches as excluded --
scaffold="$(cd "$STAGING" && python3 "$CRAFTER" --probe oracle-probe 2>/dev/null)"
case "$scaffold" in
  *__pycache__*) pass "probe-scaffold-excludes-caches";;
  *) fail "probe-scaffold-excludes-caches" "the emitted skeleton never names __pycache__";;
esac

# ---- probe 5 (row 125, invariant): no cache member ships in a request
#      pack or a context pack --------------------------------------------
# Passes on the base as the desk read it (a regression pin); listed so the
# worker's fix, wherever the report's leak was, cannot reopen these two.
R5="$(new_repo r125 "")"
( cd "$R5" && mkdir -p bin/__pycache__ && echo x > bin/a.py && echo y > bin/__pycache__/a.cpython-312.pyc \
  && git add bin/a.py && git commit -qm bin ) || oracle_error "fixture r125: repo"
( cd "$R5" && "$BALE" pack "g" --slug g --include bin --no-readme --expects-probe no </dev/null \
    >"$SCRATCH/r125-pack.out" 2>&1 ) || oracle_error "fixture r125: request pack failed"
req_cache="$(tar -tzf "$R5"/.bale/outbox/request-*.tar.gz | grep -c __pycache__ || true)"
C5="$SCRATCH/ctx125"; mkdir -p "$C5/bin/__pycache__" && echo x > "$C5/bin/a.py" && echo y > "$C5/bin/__pycache__/a.pyc"
( cd "$C5" && "$BALE" pack --context </dev/null >"$SCRATCH/r125-ctx.out" 2>&1 ) \
  || oracle_error "fixture r125: context pack failed"
ctx_cache="$(tar -tzf "$C5"/.bale/outbox/context-*.tar.gz | grep -c __pycache__ || true)"
if [ "$req_cache" = "0" ] && [ "$ctx_cache" = "0" ]; then
  pass "no-cache-member-in-packs"
else
  fail "no-cache-member-in-packs" "request pack cache members=$req_cache context pack cache members=$ctx_cache"
fi

# ---- probe 6: the wave's bump carries its changelog record -----------
version="$(tr -d '[:space:]' < "$STAGING/bin/VERSION")"
bump_state="$(python3 - "$STAGING" "$version" <<'PY'
import json, os, sys
staging, version = sys.argv[1], sys.argv[2]
def key(v):
    try: return tuple(int(x) for x in v.split("."))
    except ValueError: return None
k = key(version)
if k is None or k <= (0, 4, 43):
    print(f"version {version!r} is not past 0.4.43"); sys.exit(0)
path = os.path.join(staging, "claude", "changelog", f"{version}.json")
if not os.path.isfile(path):
    print(f"no record at claude/changelog/{version}.json"); sys.exit(0)
try:
    json.load(open(path))
except Exception as e:
    print(f"record at claude/changelog/{version}.json does not parse: {e}"); sys.exit(0)
print("ok")
PY
)"
if [ "$bump_state" = "ok" ]; then
  pass "version-bump-with-changelog-record"
else
  fail "version-bump-with-changelog-record" "$bump_state"
fi

echo "probes failed: $fails"
[ "$fails" -eq 0 ] && exit 0 || exit 1
