#!/usr/bin/env bash
# Blind checkpoint — the stats micro (rows 86 + 98, dossier wiring, counts).
# Authored at the desk from the request (2026-09-16 UTC), before any
# implementation existed; grades outcomes of the applied tree only.
# Runs from the staging root. Writes: a private tmpdir only.
# Exit 0 = every probe PASS/SKIP, 1 = a probe FAILed, 2 = script error.
set -u
trap 'echo "[ERROR] checkpoint script errored at line $LINENO"; exit 2' ERR
echo "checkpoint stats-micro v1: writes to nothing in the tree (tmpdir only)"
fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fails=$((fails + 1)); }
tmp="$(mktemp -d)"; export CP_TMP="$tmp"; export CP_ROOT="$PWD"

python3 - <<'PY' || fails=$((fails + $?))
import copy, json, os, subprocess, sys
from pathlib import Path
fails = 0
def verdict(label, ok, detail=""):
    global fails
    print(("[PASS] " if ok else "[FAIL] ") + label + (f" — {detail}" if detail and not ok else ""))
    if not ok: fails += 1
root = Path(os.environ["CP_ROOT"]); tmp = Path(os.environ["CP_TMP"])
bale = root / "bin" / "bale"
FIX = root / "tests/fixtures/stats_corpus/2026-06-05-fx-applied-001.json"
base = json.loads(FIX.read_text())

def corpus(name, records):
    d = tmp / name / "claude" / "telemetry"; d.mkdir(parents=True)
    for sid, rec in records.items():
        rec = copy.deepcopy(rec); rec["session_id"] = sid
        (d / f"{sid}.json").write_text(json.dumps(rec))
    return tmp / name

def stats(cwd, *args):
    r = subprocess.run([sys.executable, str(bale), "stats", "--json", *args],
                       cwd=cwd, capture_output=True, text=True)
    lines = [l for l in r.stdout.strip().splitlines() if l.startswith("{")]
    return r.returncode, (json.loads(lines[-1]) if lines else None), r.stderr[-300:]

def with_feedback(rec, **sr):
    rec = copy.deepcopy(rec)
    att = rec["attempts"][-1]
    fb = att.setdefault("feedback", {}) if isinstance(att.get("feedback"), dict) else att.setdefault("feedback", {})
    fb.setdefault("self_reported", {}).update(sr)
    return rec

try:
    # 1. dossier wiring
    c = corpus("dossier", {"2026-06-05-fx-applied-001": base})
    rc, out, err = stats(c, "--sid", "2026-06-05-fx-applied-001")
    verdict("stats-sid-renders-dossier-json",
            rc == 0 and out is not None and out.get("outcome") == "dossier"
            and out.get("found") is True
            and out.get("session_id") == "2026-06-05-fx-applied-001",
            f"rc={rc} keys={sorted(out) if out else None} {err}")
    rc, out, err = stats(c, "--sid", "2026-01-01-nope-001")
    verdict("stats-sid-unknown-is-honest-miss-exit-0",
            rc == 0 and out is not None and out.get("found") is False,
            f"rc={rc} out={out} {err}")
    r = subprocess.run([sys.executable, str(bale), "stats", "--sid",
                        "2026-06-05-fx-applied-001"], cwd=c,
                       capture_output=True, text=True)
    verdict("stats-sid-human-report-exit-0-names-sid",
            r.returncode == 0 and "2026-06-05-fx-applied-001" in r.stdout)

    # 2. row 86: handoff-origin count
    ho = copy.deepcopy(base)
    ho["attempts"].insert(0, {"at": base["attempts"][0]["at"],
                              "outcome": "opened", "command": "handoff"})
    c = corpus("handoff", {"2026-06-05-fx-applied-001": base,
                           "2026-06-09-fx-handoff-001": ho})
    rc, out, err = stats(c)
    verdict("stats-corpus-handoff-origin-sessions",
            rc == 0 and out and out["corpus"].get("handoff_origin_sessions") == 1,
            f"got {out['corpus'].get('handoff_origin_sessions') if out else out}")

    # 3. row 98: docs_read normalization + first read side
    a = with_feedback(base, docs_read=["context/docs/CLAUDE.md docs/TARBALL.md"])
    b = with_feedback(base, docs_read=["docs/CLAUDE.md"])
    c = corpus("docs", {"2026-06-05-fx-applied-001": a, "2026-06-10-fx-docs-001": b,
                        "2026-06-11-fx-plain-001": base})
    rc, out, err = stats(c)
    dr = (out or {}).get("corpus", {}).get("docs_read")
    verdict("stats-corpus-docs-read-normalized-tokens",
            rc == 0 and isinstance(dr, dict) and dr.get("sessions") == 2
            and dr.get("tokens", {}).get("docs/CLAUDE.md") == 2
            and dr.get("tokens", {}).get("docs/TARBALL.md") == 1
            and "context/docs/CLAUDE.md" not in dr.get("tokens", {}),
            f"got {dr}")

    # 4. the two counts, and paste-carried rounds counting as rounds
    p = with_feedback(base, light_blocks=2, paste_carried_rounds=1)
    c = corpus("counts", {"2026-06-05-fx-applied-001": base, "2026-06-12-fx-counts-001": p})
    rc, out, err = stats(c)
    co = (out or {}).get("corpus", {})
    verdict("stats-corpus-self-reported-count-totals",
            rc == 0 and co.get("light_blocks_total") == 2
            and co.get("paste_carried_rounds_total") == 1,
            f"got lb={co.get('light_blocks_total')} pc={co.get('paste_carried_rounds_total')}")
    c0 = corpus("counts0", {"2026-06-05-fx-applied-001": base})
    rc0, out0, _ = stats(c0)
    r0 = (out0 or {}).get("corpus", {}).get("clarification_rounds_total")
    verdict("stats-corpus-paste-carried-rounds-add-to-clarification-rounds",
            rc == 0 and isinstance(r0, int)
            and co.get("clarification_rounds_total") == r0 + 1,
            f"base={r0} with-paste={co.get('clarification_rounds_total')}")
except Exception as e:
    print(f"[FAIL] probe-errored: {type(e).__name__}: {e}"); fails += 1
sys.exit(fails)
PY

suites_ok=1
for suite in test_stats_drilldown test_stats_aggregation test_telemetry_extensions; do
  if ! python3 -m unittest discover -s tests -p "${suite}.py" >> "$tmp/suites.log" 2>&1; then
    suites_ok=0; echo "  suite failed: $suite"; fi
done
if [ "$suites_ok" -eq 1 ]; then pass "stats-suites-pass"; else
  fail "stats-suites-pass"; tail -30 "$tmp/suites.log"; fi
rm -rf "$tmp"
if [ "$fails" -ne 0 ]; then echo "checkpoint stats-micro v1: $fails probe(s) failed"; exit 1; fi
echo "checkpoint stats-micro v1: all probes passed"; exit 0
