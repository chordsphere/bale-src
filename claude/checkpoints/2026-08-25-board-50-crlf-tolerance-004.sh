#!/usr/bin/env bash
# Blind checkpoint — board 50 (CRLF tolerance at text-file reads).
# Authored blind from the request at the 2026-08-25-continue-plan-003
# sitting, before implementation exists. Outcome contracts only: what
# must be true of bale as built from the applied tree, never how.
# Exit 0 = all probes pass; 1 = a probe failed (HOLD); 2 = this
# script's own harness broke (defective oracle).
# Offline by construction: local git fixtures under mktemp, no network.
set -u
STAGING="$PWD"
BALE="$STAGING/bin/bale"
FAILED=0

say()  { printf '%s\n' "$*"; }
need() { command -v "$1" >/dev/null 2>&1 || { say "[CKPT-ERR] missing tool: $1"; exit 2; }; }
need git; need python3
[ -f "$BALE" ] || { say "[CKPT-ERR] bin/bale not found at $BALE"; exit 2; }

sha_lf() {  # sha256 of the file's LF-normalized bytes
  python3 -c 'import hashlib,sys;d=open(sys.argv[1],"rb").read().replace(b"\r\n",b"\n");print(hashlib.sha256(d).hexdigest())' "$1"
}
sha_raw() {
  python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$1"
}
has_cr() {  # exit 0 when the file contains a CR byte
  python3 -c 'import sys;sys.exit(0 if b"\r" in open(sys.argv[1],"rb").read() else 1)' "$1"
}
fresh_repo() {  # fresh fixture repo per scenario; prints its path
  local d
  d="$(mktemp -d)" || exit 2
  ( cd "$d" && git init -q && git config user.email ckpt@bale \
      && git config user.name ckpt && echo hello > app.txt \
      && git add -A && git commit -qm init ) || exit 2
  printf '%s' "$d"
}
verdict() {  # verdict LABEL STATUS(0=pass)
  if [ "$2" -eq 0 ]; then say "[PASS] $1"; else say "[FAIL] $1"; FAILED=1; fi
}

# --- Probe 1+2: checkpoint delivery tolerates CRLF ---------------------
# One scenario, two outcomes. A planner checkpoint that traveled a
# line-ending-mangling transport still (a) commits as the LF bytes the
# desk authored, and (b) echoes the sha256 of those LF bytes, so the
# desk's published-LF-hash comparison holds.
R1="$(fresh_repo)"
printf '[validation]\nbase = "claude/checkpoints/{sid}.sh"\n' > "$R1/bale.toml"
( cd "$R1" && git add -A && git commit -qm cfg ) || exit 2
CK="$R1/delivered-ck.sh"
printf '#!/usr/bin/env bash\r\necho oracle-probe\r\nexit 1\r\n' > "$CK"
WANT="$(sha_lf "$CK")"
OUT1="$(cd "$R1" && python3 "$BALE" pack "ckpt fixture goal" --slug fx-ck \
  --checkpoint-file "$CK" --write app.txt --expects-probe no --no-readme 2>&1)"
RC1=$?
verdict "checkpoint-file pack accepts a CRLF-delivered oracle (exit 0)" "$RC1"
COMMITTED="$(ls "$R1"/claude/checkpoints/*.sh 2>/dev/null | head -1)"
if [ -n "${COMMITTED:-}" ] && ! has_cr "$COMMITTED" \
   && [ "$(sha_raw "$COMMITTED")" = "$WANT" ]; then
  verdict "committed oracle bytes are the LF form of the delivered file" 0
else
  verdict "committed oracle bytes are the LF form of the delivered file" 1
fi
case "$OUT1" in
  *"$WANT"*) verdict "pack echo publishes the LF-bytes sha256" 0 ;;
  *)         verdict "pack echo publishes the LF-bytes sha256" 1 ;;
esac

# --- Probe 3: same file, either line ending, re-delivers idempotent ----
# The aborted-pack re-run posture survives transport: re-delivering the
# same oracle content must not refuse as differing bytes just because
# one copy was mangled. (Fresh fixture; commit the LF form at the
# resolved path first via a first pack, then re-pack the CRLF copy of
# identical content for the same sid path — outcome: no refusal.)
R2="$(fresh_repo)"
printf '[validation]\nbase = "claude/checkpoints/{sid}.sh"\n' > "$R2/bale.toml"
( cd "$R2" && git add -A && git commit -qm cfg ) || exit 2
printf '#!/usr/bin/env bash\necho oracle-probe\nexit 1\n' > "$R2/lf-ck.sh"
printf '#!/usr/bin/env bash\r\necho oracle-probe\r\nexit 1\r\n' > "$R2/crlf-ck.sh"
( cd "$R2" && python3 "$BALE" pack "ckpt fixture goal" --slug fx-idem \
    --checkpoint-file lf-ck.sh --write app.txt --expects-probe no \
    --no-readme >/dev/null 2>&1 ) || exit 2
# The committed path is sid-resolved; an identical re-delivery is only
# exercised on the aborted-rerun shape, which needs the same sid. Probe
# the ingest identity instead: deliver the CRLF twin into a THIRD fresh
# fixture and require its committed bytes to equal R2's committed bytes.
R3="$(fresh_repo)"
printf '[validation]\nbase = "claude/checkpoints/{sid}.sh"\n' > "$R3/bale.toml"
( cd "$R3" && git add -A && git commit -qm cfg ) || exit 2
cp "$R2/crlf-ck.sh" "$R3/crlf-ck.sh"
( cd "$R3" && python3 "$BALE" pack "ckpt fixture goal" --slug fx-idem \
    --checkpoint-file crlf-ck.sh --write app.txt --expects-probe no \
    --no-readme >/dev/null 2>&1 )
RC3=$?
A="$(ls "$R2"/claude/checkpoints/*.sh 2>/dev/null | head -1)"
B="$(ls "$R3"/claude/checkpoints/*.sh 2>/dev/null | head -1)"
if [ "$RC3" -eq 0 ] && [ -n "${A:-}" ] && [ -n "${B:-}" ] \
   && [ "$(sha_raw "$A")" = "$(sha_raw "$B")" ]; then
  verdict "LF and CRLF twins of one oracle ingest to identical committed bytes" 0
else
  verdict "LF and CRLF twins of one oracle ingest to identical committed bytes" 1
fi

# --- Probe 4: brief tolerance stays contract ---------------------------
# Already-observed behavior, pinned as outcome: a CRLF --readme-file
# packs clean, ships CR-free, and echoes the LF-bytes sha256.
R4="$(fresh_repo)"
BR="$R4/crlf-brief.md"
printf '# Fixture brief\r\nOne line of intent.\r\n' > "$BR"
BWANT="$(sha_lf "$BR")"
OUT4="$(cd "$R4" && python3 "$BALE" pack "brief fixture goal" --slug fx-brief \
  --readme-file "$BR" --write app.txt --expects-probe no 2>&1)"
RC4=$?
verdict "pack accepts a CRLF brief (exit 0)" "$RC4"
TAR="$(ls "$R4"/.bale/outbox/request-*.tar.gz 2>/dev/null | head -1)"
if [ -n "${TAR:-}" ] && python3 - "$TAR" "$BWANT" <<'PY'
import hashlib, sys, tarfile
t = tarfile.open(sys.argv[1])
m = [n for n in t.getnames() if n.endswith("/README.md")]
if not m: sys.exit(1)
d = t.extractfile(m[0]).read()
sys.exit(0 if (b"\r" not in d and hashlib.sha256(d).hexdigest() == sys.argv[2]) else 1)
PY
then
  verdict "shipped README is CR-free and matches the LF-bytes sha256" 0
else
  verdict "shipped README is CR-free and matches the LF-bytes sha256" 1
fi

# --- Probe 5: config tolerance stays contract --------------------------
R5="$(fresh_repo)"
printf '[validation]\r\nbase = "claude/checkpoints/{sid}.sh"\r\n' > "$R5/bale.toml"
( cd "$R5" && git add -A && git commit -qm cfg ) || exit 2
( cd "$R5" && python3 "$BALE" status >/dev/null 2>&1 )
verdict "a CRLF bale.toml reads clean (bale status exit 0)" "$?"

say "----------------------------------------------------------------"
if [ "$FAILED" -eq 0 ]; then say "[CKPT] PASS — all board-50 outcome probes hold"; exit 0
else say "[CKPT] HOLD — one or more board-50 outcome probes failed"; exit 1; fi
