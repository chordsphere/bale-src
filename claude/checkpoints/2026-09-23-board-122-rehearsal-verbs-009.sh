#!/usr/bin/env bash
# Blind checkpoint v1 — row 122, the rehearsal verbs, authored
# 2026-09-23 at the 2026-09-23-continue-plan-006 desk, from the request,
# before any implementation exists. Outcome contracts only, over fresh
# scratch repos under mktemp, driving the staged bin/bale. Fixture
# bundles are hand-rolled from the wire format (never emitted by a
# surface in the session's forecast — this wave's lesson). Verdict
# lines carry the label alone; detail on a following "  detail:" line.
# Exit 1 = a probe failed; exit 2 = the oracle itself broke.

set -u
STAGING="$(pwd)"
BALE="$STAGING/bin/bale"
fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; [ -n "${2:-}" ] && echo "  detail: $2"; fails=$((fails+1)); }
oracle_error() { echo "[ERROR] $1" >&2; exit 2; }

[ -x "$BALE" ] || oracle_error "control: staged bin/bale is not executable"
command -v git >/dev/null 2>&1 || oracle_error "control: git not on PATH"
command -v python3 >/dev/null 2>&1 || oracle_error "control: python3 not on PATH"
SCRATCH="$(mktemp -d)" || oracle_error "control: mktemp failed"
trap 'rm -rf "$SCRATCH"' EXIT
export HOME="$SCRATCH/home"; mkdir -p "$HOME" || oracle_error "control: scratch HOME"
echo "control ok: staged bale, git, python3, scratch $SCRATCH"

new_repo() {
  local dir="$SCRATCH/$1"
  mkdir -p "$dir" || oracle_error "fixture: mkdir $dir"
  ( cd "$dir" && git init -q -b main && git config user.email o@example.invalid \
    && git config user.name oracle \
    && printf '[sandbox]\nenabled = false\n%s' "$2" > bale.toml \
    && echo seed > f.txt && git add -A && git commit -qm init ) \
    || oracle_error "fixture: scratch repo $1"
  echo "$dir"
}
BRIEF="$SCRATCH/brief.md"; printf '# oracle fixture brief\n\nfixture.\n' > "$BRIEF"

# Hand-roll a bundle: hand_bundle OUT BRIEF CHECKPOINT|- PARENT|- ARGV...
hand_bundle() {
  python3 - "$@" <<'PY' || oracle_error "fixture: hand-rolled bundle failed"
import gzip, hashlib, io, json, sys, tarfile
out, brief_path, ckpt_path, parent = sys.argv[1:5]
argv = sys.argv[5:]
def lf(p): return open(p, "rb").read().replace(b"\r\n", b"\n")
brief = lf(brief_path)
members = {"brief": {"path": "brief.md", "sha256": hashlib.sha256(brief).hexdigest()},
           "checkpoint": None}
payload = [("brief.md", brief)]
if ckpt_path != "-":
    ck = lf(ckpt_path)
    members["checkpoint"] = {"path": "checkpoint.sh", "sha256": hashlib.sha256(ck).hexdigest()}
    payload.append(("checkpoint.sh", ck))
manifest = {"bundle_format": 1, "pack_argv": argv, "members": members,
            "pre_answered": ([] if parent == "-" else [{"prompt": "supersede", "subject": parent}])}
payload.insert(0, ("bundle.json", json.dumps(manifest, indent=2).encode() + b"\n"))
buf = io.BytesIO()
with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
    with tarfile.open(fileobj=gz, mode="w") as tf:
        for name, data in payload:
            info = tarfile.TarInfo(name); info.size = len(data); info.mode = 0o644
            tf.addfile(info, io.BytesIO(data))
open(out, "wb").write(buf.getvalue())
PY
}
# A snapshot of everything a verb could write: tracked/untracked state,
# sessions, records, outbox members.
snapshot() {
  ( cd "$1" && git status --porcelain=v1 2>/dev/null; echo "--"; \
    ls .bale/sessions 2>/dev/null; echo "--"; ls claude/telemetry 2>/dev/null; \
    echo "--"; ls .bale/outbox 2>/dev/null; echo "--"; ls claude/checkpoints 2>/dev/null )
}
argparse_unknown() { grep -q "unrecognized arguments\|invalid choice\|no such option" "$1"; }

# ---- probe 1: `bale open --check` refuses on the include-naming gate,
#      writes nothing, and leaves a --supersedes parent open --------------
R1="$(new_repo r1 $'[validation]\nbase = "claude/checkpoints/{sid}.sh"\n')"
( cd "$R1" && mkdir -p claude/checkpoints && printf '#!/usr/bin/env bash\nexit 0\n' > claude/checkpoints/old.sh \
  && git add -A && git commit -qm ckpt ) || oracle_error "fixture r1: checkpoint dir"
( cd "$R1" && "$BALE" pack "parent" --slug parent --read-only --include f.txt --no-readme \
    --expects-probe no </dev/null >"$SCRATCH/r1-parent.out" 2>&1 ) || oracle_error "fixture r1: parent pack"
PARENT="$(ls "$R1/claude/telemetry/" | sed 's/\.json$//' | head -n 1)"
[ -n "$PARENT" ] || oracle_error "fixture r1: no parent record"
hand_bundle "$R1/child.bale-bundle" "$BRIEF" - "$PARENT" child --slug child --read-only \
  --include claude/checkpoints --supersedes "$PARENT" --expects-probe no
before="$(snapshot "$R1")"
( cd "$R1" && "$BALE" open --check child.bale-bundle </dev/null >"$SCRATCH/r1-check.out" 2>&1 ); rc=$?
after="$(snapshot "$R1")"
pstate="$(python3 -c "import json,sys; r=json.load(open(sys.argv[1])); print(r['outcome'])" "$R1/claude/telemetry/$PARENT.json")"
if [ "$rc" -ne 0 ] && ! argparse_unknown "$SCRATCH/r1-check.out" && [ "$before" = "$after" ] && [ "$pstate" = "opened" ]; then
  pass "open-check-refuses-writes-nothing-parent-open"
else
  fail "open-check-refuses-writes-nothing-parent-open" "exit $rc; flag known: $(argparse_unknown "$SCRATCH/r1-check.out" && echo no || echo yes); tree unchanged: $([ "$before" = "$after" ] && echo yes || echo no); parent: $pstate"
fi

# ---- probe 2: `bale open --check` on a clean bundle exits 0 and opens
#      nothing ------------------------------------------------------------
R2="$(new_repo r2 "")"
hand_bundle "$R2/clean.bale-bundle" "$BRIEF" - - clean --slug clean --read-only --include f.txt --expects-probe no
before="$(snapshot "$R2")"
( cd "$R2" && "$BALE" open --check clean.bale-bundle </dev/null >"$SCRATCH/r2-check.out" 2>&1 ); rc=$?
after="$(snapshot "$R2")"
if [ "$rc" -eq 0 ] && [ "$before" = "$after" ]; then pass "open-check-clean-exits-0-opens-nothing"
else fail "open-check-clean-exits-0-opens-nothing" "exit $rc; tree unchanged: $([ "$before" = "$after" ] && echo yes || echo no)"; fi

# ---- probe 3: `bale pack --dry-run` gates a typed line and writes nothing
R3="$(new_repo r3 "")"
before="$(snapshot "$R3")"
( cd "$R3" && "$BALE" pack "dry" --slug dry --read-only --include f.txt --no-readme --expects-probe no --dry-run \
    </dev/null >"$SCRATCH/r3-ok.out" 2>&1 ); rc_ok=$?
( cd "$R3" && "$BALE" pack "dry" --slug dry --read-only --include nope.txt --no-readme --expects-probe no --dry-run \
    </dev/null >"$SCRATCH/r3-bad.out" 2>&1 ); rc_bad=$?
after="$(snapshot "$R3")"
if [ "$rc_ok" -eq 0 ] && [ "$rc_bad" -ne 0 ] && ! argparse_unknown "$SCRATCH/r3-ok.out" && [ "$before" = "$after" ]; then
  pass "pack-dry-run-gates-and-writes-nothing"
else
  fail "pack-dry-run-gates-and-writes-nothing" "clean exit $rc_ok; missing-path exit $rc_bad; tree unchanged: $([ "$before" = "$after" ] && echo yes || echo no)"
fi

# ---- probe 4: `bale open --dry-run` runs the bundle's checkpoint against
#      the base, echoes its verdicts, commits nothing, opens nothing ------
R4="$(new_repo r4 $'[validation]\nbase = "claude/checkpoints/{sid}.sh"\n')"
CK1="$SCRATCH/ck-hold.sh"; printf '#!/usr/bin/env bash\necho "[FAIL] fixture-probe"\nexit 1\n' > "$CK1"
CK2="$SCRATCH/ck-broken.sh"; printf '#!/usr/bin/env bash\necho "oracle broke" >&2\nexit 2\n' > "$CK2"
hand_bundle "$R4/hold.bale-bundle" "$BRIEF" "$CK1" - scoped --slug scoped --include f.txt --write f.txt --expects-probe no
hand_bundle "$R4/broken.bale-bundle" "$BRIEF" "$CK2" - scoped --slug scoped --include f.txt --write f.txt --expects-probe no
before="$(snapshot "$R4")"
( cd "$R4" && "$BALE" open --dry-run hold.bale-bundle </dev/null >"$SCRATCH/r4-hold.out" 2>&1 ); rc_hold=$?
( cd "$R4" && "$BALE" open --dry-run broken.bale-bundle </dev/null >"$SCRATCH/r4-broken.out" 2>&1 ); rc_broken=$?
after="$(snapshot "$R4")"
echoed=$(grep -c "\[FAIL\] fixture-probe" "$SCRATCH/r4-hold.out" || true)
if [ "$rc_hold" -eq 0 ] && [ "$echoed" -ge 1 ] && [ "$rc_broken" -ne 0 ] && [ "$before" = "$after" ]; then
  pass "open-dry-run-runs-checkpoint-writes-nothing"
else
  fail "open-dry-run-runs-checkpoint-writes-nothing" "expected-HOLD dry-run exit $rc_hold (verdict echoed: $echoed); exit-2 oracle dry-run exit $rc_broken; tree unchanged: $([ "$before" = "$after" ] && echo yes || echo no)"
fi

# ---- probe 5: the bump carries its changelog record -------------------
version="$(tr -d '[:space:]' < "$STAGING/bin/VERSION")"
bump="$(python3 - "$STAGING" "$version" <<'PY'
import json, os, sys
st, v = sys.argv[1], sys.argv[2]
try: k = tuple(int(x) for x in v.split("."))
except ValueError: k = None
if k is None or k <= (0, 4, 44): print(f"version {v!r} is not past 0.4.44"); sys.exit()
p = os.path.join(st, "claude", "changelog", f"{v}.json")
if not os.path.isfile(p): print(f"no record at claude/changelog/{v}.json"); sys.exit()
try: json.load(open(p))
except Exception as e: print(f"record does not parse: {e}"); sys.exit()
print("ok")
PY
)"
[ "$bump" = "ok" ] && pass "version-bump-with-changelog-record" || fail "version-bump-with-changelog-record" "$bump"

echo "probes failed: $fails"
[ "$fails" -eq 0 ] && exit 0 || exit 1
