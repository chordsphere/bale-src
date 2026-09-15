#!/usr/bin/env bash
# Blind checkpoint — board 94, clock discipline + context/ prefix.
# Authored at the desk from the request, before implementation (TARBALL.md §7).
# Outcome contracts only; how the worker gets there is the worker's.
# Exit 0 pass, 1 a check failed, 2 the oracle itself errored.
# Runs with cwd = the applied tree; network off; stdlib Python only.
set -u
fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fails=$((fails + 1)); }

need() { [ -e "$1" ] || { echo "[ERROR] oracle expects $1 in the applied tree"; exit 2; }; }
need bin/bale
need bin/bale_pack.py
need schemas/request-manifest.schema.json
need schemas/response-manifest.schema.json
need tools/response_lint.py
need docs/TARBALL.md

# --- 1. session ids are minted on the UTC date, whatever the process zone ---
# XXX-14 is UTC+14 and XXX12 is UTC-12 (POSIX TZ strings, no tzdata needed);
# their local dates never coincide, so a local-clock mint fails under at least one.
probe_sid() {
  local tz="$1"
  TZ="$tz" python3 - <<'PY'
import runpy, sys, tempfile, time
from datetime import datetime, timezone
from pathlib import Path
time.tzset()
m = runpy.run_path("bin/bale", run_name="bale_checkpoint_probe")
repo = Path(tempfile.mkdtemp())
utc_day = datetime.now(timezone.utc).date().isoformat()
peek = m["peek_session_id"](repo, "probe")
sid = m["next_session_id"](repo, "probe")
ok = sid[:10] == utc_day and peek[:10] == utc_day and sid == peek
print(f"tz-local-date={time.strftime('%Y-%m-%d')} utc={utc_day} sid={sid} peek={peek}")
sys.exit(0 if ok else 1)
PY
}
if out=$(probe_sid "XXX-14" 2>&1) && out2=$(probe_sid "XXX12" 2>&1); then
  pass "session id dated by UTC under both extreme zones ($out; $out2)"
else
  fail "session id follows the process's local date, not UTC ($out; ${out2:-second probe not reached})"
fi

# --- 2/3. the pack-time stamp is admitted, not required, on both manifest sides ---
python3 - <<'PY' && pass "provenance.packed_at admitted (optional) on the request manifest schema" || fail "provenance.packed_at missing or made required on the request manifest schema"
import json, sys
s = json.load(open("schemas/request-manifest.schema.json"))
p = s["properties"]["provenance"]
sys.exit(0 if "packed_at" in p.get("properties", {}) and "packed_at" not in p.get("required", []) else 1)
PY
python3 - <<'PY' && pass "provenance.packed_at admitted on the response echo schema" || fail "provenance.packed_at not admitted on the response echo schema (verbatim echo would drop it)"
import json, sys
s = json.load(open("schemas/response-manifest.schema.json"))
p = s["properties"]["feedback"]["properties"]["mechanical"]["properties"]["provenance"]
sys.exit(0 if "packed_at" in p.get("properties", {}) else 1)
PY

# --- 4. the request-carried lint still embeds the response schema it validates against ---
# (the echo side is the one this session widens; the embed must follow, JSON-equal)
python3 - <<'PY' && pass "response_lint's embedded response schema is JSON-equal to schemas/" || fail "response_lint's embedded response schema drifted from schemas/response-manifest.schema.json"
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("rl", "tools/response_lint.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
src = json.load(open("schemas/response-manifest.schema.json"))
cands = [v for v in vars(mod).values() if isinstance(v, dict)]
for v in vars(mod).values():
    if isinstance(v, str) and v.lstrip().startswith("{"):
        try:
            cands.append(json.loads(v))
        except ValueError:
            pass
sys.exit(0 if any(c == src for c in cands) else 1)
PY

# --- 5. the VERBATIM sentences landed where the brief places them ---
S_CLOCK='Every date bale mints — the session id, its per-day counter, a handoff re-mint — and every timestamp it writes are UTC; a session dates what it writes from the session id, never from the date its chat shows.'
S_PREFIX='A request path context/<p> is the repo path <p>: the prefix is tarball layout, and nothing in a response — no changes[] path, no self-report — carries it.'
S_OPENER='Session ids and every bale timestamp are UTC and may run a day ahead of the date this chat shows; date anything you write from the session id, never from the chat.'

grep -qF -- "$S_CLOCK" docs/TARBALL.md && pass "clock convention sentence present in docs/TARBALL.md" || fail "clock convention sentence absent from docs/TARBALL.md"
grep -qF -- "$S_PREFIX" docs/TARBALL.md && pass "context/ mapping sentence present in docs/TARBALL.md" || fail "context/ mapping sentence absent from docs/TARBALL.md"

# The opener line is graded from the pack module's string constants, which the
# parser merges across implicit concatenation — one emitted line, one constant.
S_OPENER="$S_OPENER" python3 - <<'PY' && pass "opener clock sentence rides as one emitted line in bin/bale_pack.py" || fail "opener clock sentence absent from bin/bale_pack.py's emitted lines"
import ast, os, sys
want = os.environ["S_OPENER"]
tree = ast.parse(open("bin/bale_pack.py", encoding="utf-8").read())
consts = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
sys.exit(0 if any(want in c for c in consts) else 1)
PY

echo "checkpoint: $fails failing"
[ "$fails" -eq 0 ] && exit 0 || exit 1
