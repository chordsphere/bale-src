#!/usr/bin/env bash
# Blind checkpoint — bare-pack-excl-waiver session (2026-08-13 sitting).
# Trimmed v2 for the A+B split: no Change C assertions.
# Planner-authored from the request per the board-6 doctrine; authored
# before any worker output existed. Commit at the resolved per-sid path
# the pack refusal names (claude/checkpoints/<sid>.sh). Runs from the
# project root against the tree with changes applied; script bytes are
# taken from HEAD by bale, so nothing here depends on staged copies.
set -euo pipefail

fail() { printf 'CHECKPOINT FAIL: %s\n' "$*" >&2; exit 1; }
note() { printf 'checkpoint: %s\n' "$*"; }

SRC="$PWD"

# --- 1. Full suite green ----------------------------------------------------
note "running unit suite"
python3 -m unittest discover -s tests >/dev/null 2>&1 \
  || fail "unit suite not green"

# --- 2. Contract anchors in BALE.md (normalized line-join grep) -------------
normalized="$(tr '\n' ' ' < BALE.md | tr -s ' ')"
a1="The configured checkpoint is auto-excluded from the shipped context of every pack; only an include that names it explicitly, or the admission flag, ships it."
a2="A read-only pack waives the per-session checkpoint: an empty forecast lands nothing, so no committed oracle is required and the waiver is stamped into provenance."
case "$normalized" in *"$a1"*) : ;; *) fail "anchor 1 (auto-exclusion) absent from BALE.md" ;; esac
case "$normalized" in *"$a2"*) : ;; *) fail "anchor 2 (read-only waiver) absent from BALE.md" ;; esac
grep -qF "$a1" BALE.md || fail "anchor 1 present but wrapped; the brief mandates one physical line"
grep -qF "$a2" BALE.md || fail "anchor 2 present but wrapped; the brief mandates one physical line"
note "both anchors present and unwrapped"

# --- 3. E2E fixture: install + repo with a {sid} base -----------------------
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
INSTALL="$TMP/install"; HOME_DIR="$TMP/home"; REPO="$TMP/repo"
mkdir -p "$INSTALL" "$HOME_DIR" "$REPO"
for tree in bin docs schemas tools; do
  cp -r "$SRC/$tree" "$INSTALL/$tree" || fail "install tree $tree missing"
done
printf '[user]\n\tname = Checkpoint Fixture\n\temail = ckpt@example.invalid\n' \
  > "$HOME_DIR/.gitconfig"
run_bale() { HOME="$HOME_DIR" python3 "$INSTALL/bin/bale" "$@"; }

git -C "$REPO" init -q
printf 'fixture\n' > "$REPO/README.md"
printf '[validation]\nbase = "claude/checkpoints/{sid}.sh"\n' > "$REPO/bale.toml"
HOME="$HOME_DIR" git -C "$REPO" add -A
HOME="$HOME_DIR" git -C "$REPO" commit -qm "fixture: sid-pattern base, no checkpoints"

# --- 3a. Read-only bare pack succeeds with NO committed checkpoint ----------
cd "$REPO"
out="$(printf '' | run_bale pack "read-only fixture session" --slug ck-ro \
        --read-only --no-readme --json 2>"$TMP/ro.err")" \
  || fail "read-only pack refused; stderr: $(cat "$TMP/ro.err")"
tarball="$(printf '%s' "$out" | python3 -c 'import sys,json;print(json.load(sys.stdin)["tarball"])')" \
  || fail "pack --json report unparseable"
python3 - "$tarball" <<'PY' || fail "read-only waiver not stamped as pinned"
import json, sys, tarfile
with tarfile.open(sys.argv[1]) as t:
    m = next(x for x in t.getnames() if x.endswith("manifest.json"))
    prov = json.load(t.extractfile(m))["provenance"]
assert prov.get("checkpoint") is None, prov.get("checkpoint")
assert prov.get("checkpoint_waived") == "read-only", prov.get("checkpoint_waived")
PY
note "read-only pack packed with checkpoint waived"

# --- 3b. Default scoped pack: refusal names the resolved path, commit,
#         identical re-run succeeds (no counter chase), checkpoint excluded --
set +e
printf '' | run_bale pack "scoped fixture session" --slug ck-scoped \
  --no-readme --json >"$TMP/s1.out" 2>"$TMP/s1.err"
rc=$?
set -e
[ "$rc" -ne 0 ] || fail "scoped pack succeeded without a committed checkpoint; waiver must stay read-only-shaped"
resolved="$(grep -o 'claude/checkpoints/[0-9A-Za-z._-]*\.sh' "$TMP/s1.err" | head -1)"
[ -n "$resolved" ] || fail "scoped-pack refusal did not name the resolved checkpoint path; stderr: $(cat "$TMP/s1.err")"
mkdir -p "$(dirname "$resolved")"
printf '#!/usr/bin/env bash\nexit 0\n' > "$resolved"
HOME="$HOME_DIR" git add "$resolved"
HOME="$HOME_DIR" git commit -qm "fixture checkpoint at $resolved"
out2="$(printf '' | run_bale pack "scoped fixture session" --slug ck-scoped \
         --no-readme --json 2>"$TMP/s2.err")" \
  || fail "identical re-run refused after committing $resolved (counter chase?); stderr: $(cat "$TMP/s2.err")"
tarball2="$(printf '%s' "$out2" | python3 -c 'import sys,json;print(json.load(sys.stdin)["tarball"])')"
python3 - "$tarball2" "$resolved" <<'PY' || fail "auto-exclusion not observed in shipped manifest"
import json, sys, tarfile
with tarfile.open(sys.argv[1]) as t:
    m = next(x for x in t.getnames() if x.endswith("manifest.json"))
    man = json.load(t.extractfile(m))
inc = man["context_included"]
assert not any("claude/checkpoints" in p for p in inc), inc
assert man["provenance"]["checkpoint"]["path"] == sys.argv[2]
PY
note "scoped pack converged on the named path and auto-excluded the checkpoint"

note "PASS"
