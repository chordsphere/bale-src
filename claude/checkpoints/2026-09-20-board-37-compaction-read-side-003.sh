#!/usr/bin/env bash
# Blind checkpoint v1 — board 37 re-scoped: the compaction read side in
# bale stats, the PLANNER.md single-window paragraph, the step 5 clause.
# Authored 2026-09-20 by the master 2026-09-20-continue-plan-001 from the
# request alone, before any implementation exists. Outcome probes only.
# Runs with cwd = the staging root. Reads the tree; its only writes are
# one scratch directory under cwd, removed on exit. No network, no bale
# invocation, no bytecode left behind.
# Exit 0 pass, 1 at least one probe failed (HOLD), 2 the oracle could not
# run or could not find the structure it grades.
set -u
command -v python3 >/dev/null 2>&1 || { echo "checkpoint: python3 not found" >&2; exit 2; }
SCRATCH="$(pwd)/.checkpoint-scratch-37-$$"
trap 'rm -rf "$SCRATCH"' EXIT
mkdir -p "$SCRATCH" || { echo "checkpoint: cannot create scratch under cwd" >&2; exit 2; }
export SCRATCH PYTHONDONTWRITEBYTECODE=1

python3 - <<'PY'
import copy, inspect, json, os, pathlib, re, shutil, sys

sys.dont_write_bytecode = True
ROOT = pathlib.Path.cwd()
SCRATCH = pathlib.Path(os.environ["SCRATCH"])
FIXTURES = ROOT / "tests" / "fixtures" / "stats_corpus"
VICTIM = "2026-06-05-fx-applied-001"   # an applied, classed fixture session
failed = 0


def verdict(ok, label, detail=""):
    # Labels travel to the worker on a HOLD; detail stays in the log.
    global failed
    print(("[PASS] " if ok else "[FAIL] ") + label)
    if not ok:
        failed += 1
        if detail:
            print("  detail: " + detail)


def broken(why):
    print("[FAIL] anchor: " + why)
    sys.exit(2)


# ---- anchors: the surfaces this oracle drives exist as they did -----------
sys.path.insert(0, str(ROOT / "bin"))
try:
    import bale_stats
    import bale_report
except Exception as exc:
    broken("bin/bale_stats.py and bin/bale_report.py import in-process (%s)" % exc)
if not (FIXTURES / (VICTIM + ".json")).is_file():
    broken("the shared stats fixture corpus carries %s" % VICTIM)
planner = (ROOT / "docs" / "PLANNER.md").read_text(encoding="utf-8")
banner = planner.find("> **PAST THE CORE.**")
step5 = re.search(r"^5\. The operator commits.*?(?=^6\. )", planner, flags=re.S | re.M)
if banner < 0 or step5 is None:
    broken("docs/PLANNER.md keeps its core banner and §5's numbered step 5")
print("[PASS] anchor: stats modules import, the fixture corpus and PLANNER.md's landmarks are present")


def corpus(name, mutate=None):
    dest = SCRATCH / name
    shutil.copytree(FIXTURES, dest)
    if mutate is not None:
        path = dest / (VICTIM + ".json")
        record = json.loads(path.read_text(encoding="utf-8"))
        carriers = [a for a in record["attempts"] if isinstance(a.get("feedback"), dict)]
        if not carriers:
            broken("%s carries a feedback block" % VICTIM)
        for attempt in carriers:
            attempt["feedback"].setdefault("self_reported", {})["compaction_occurred"] = copy.deepcopy(mutate[0])
        path.write_text(json.dumps(record), encoding="utf-8")
    return dest


def stats(name, mutate=None):
    # stderr carries the module's own named-skip diagnostics; they are
    # expected on this corpus and are not this oracle's business.
    return bale_stats.compute_stats(corpus(name, mutate))


def block(payload):
    comp = payload.get("cross_checks", {}).get("budget", {}).get("compaction")
    sids = payload.get("members", {}).get("compaction_occurred")
    ok = (isinstance(comp, dict)
          and all(isinstance(comp.get(k), int) and not isinstance(comp.get(k), bool)
                  for k in ("reporting_sessions", "occurred_sessions"))
          and isinstance(sids, list) and all(isinstance(s, str) for s in sids))
    return (comp, sids) if ok else None


try:
    base = stats("base")
except Exception as exc:
    broken("compute_stats runs over the shared fixture corpus (%s)" % exc)

b = block(base)
verdict(b is not None,
        "stats payload: cross_checks.budget.compaction carries integer reporting_sessions and occurred_sessions, and members.compaction_occurred is a sid list")
if b is None:
    for label in ("stats payload: the sid list is sorted and its length equals occurred_sessions",
                  "read side: a bare-bool true disclosure adds exactly that session",
                  "read side: an object-shaped true disclosure adds exactly that session",
                  "read side: a non-bool value neither reports nor discloses, and does not crash"):
        verdict(False, label, "no compaction block to read")
else:
    comp, sids = b
    verdict(sids == sorted(sids) and len(sids) == comp["occurred_sessions"]
            and comp["occurred_sessions"] <= comp["reporting_sessions"],
            "stats payload: the sid list is sorted and its length equals occurred_sessions")
    base_sids = set(sids)
    if VICTIM in base_sids:
        broken("%s does not disclose on the shared corpus (the oracle flips it)" % VICTIM)
    # First make sure the victim reports-but-does-not-disclose, in a known shape.
    ref = block(stats("ref", (False,)))
    for name, value, label in (
            ("bare", True, "read side: a bare-bool true disclosure adds exactly that session"),
            ("obj", {"occurred": True, "disclosure_ref": "notes.md"},
             "read side: an object-shaped true disclosure adds exactly that session")):
        try:
            got = block(stats(name, (value,)))
        except Exception as exc:
            got = None
            verdict(False, label, "compute_stats raised: %s" % exc)
            continue
        ok = (ref is not None and got is not None
              and set(got[1]) == set(ref[1]) | {VICTIM}
              and got[0]["occurred_sessions"] == ref[0]["occurred_sessions"] + 1
              and got[0]["reporting_sessions"] == ref[0]["reporting_sessions"])
        verdict(ok, label, "ref=%r got=%r" % (ref, got))
    label = "read side: a non-bool value neither reports nor discloses, and does not crash"
    try:
        got = block(stats("junk", ("yes",)))
        ok = (ref is not None and got is not None
              and VICTIM not in got[1]
              and got[0]["reporting_sessions"] == ref[0]["reporting_sessions"] - 1
              and got[0]["occurred_sessions"] == ref[0]["occurred_sessions"])
        verdict(ok, label, "ref=%r got=%r" % (ref, got))
    except Exception as exc:
        verdict(False, label, "compute_stats raised: %s" % exc)

# ---- rendering ---------------------------------------------------------------
doc = inspect.getdoc(bale_report.format_stats_json) or ""
verdict("compaction" in doc and "compaction_occurred" in doc,
        "key contract: format_stats_json's docstring documents the compaction keys")
try:
    shown = bale_report.format_stats_report(stats("render", (True,)))
    verdict(isinstance(shown, str) and "compaction" in shown.lower() and VICTIM in
            "".join(l for l in shown.splitlines(True) if "compaction" in l.lower()),
            "human report: shows the compaction count and names a disclosing session on a compaction line")
except Exception as exc:
    verdict(False, "human report: shows the compaction count and names a disclosing session on a compaction line",
            "format_stats_report raised: %s" % exc)

# ---- docs/PLANNER.md ---------------------------------------------------------
planner_norm_tail = " ".join(planner[banner:].split())
paras = [" ".join(p.split()) for p in re.split(r"\n\s*\n", planner[banner:])]
wanted = ("window growth", "caching economics", "session persistence")
verdict(any(all(w in p for w in wanted) for p in paras),
        "PLANNER.md: one paragraph past the core banner names window growth, caching economics and session persistence")
verdict("admissions" in " ".join(step5.group(0).split()),
        "PLANNER.md §5 step 5: the retry clause mentions the held apply's admissions")

# ---- version -----------------------------------------------------------------
try:
    version = (ROOT / "bin" / "VERSION").read_text(encoding="utf-8").strip()
    rec_path = ROOT / "claude" / "changelog" / (version + ".json")
    rec = json.loads(rec_path.read_text(encoding="utf-8")) if rec_path.is_file() else None
    def key(v):
        return tuple(int(x) for x in v.split("."))
    verdict(rec is not None and rec.get("version") == version and key(version) > key("0.4.37"),
            "version: bin/VERSION is past 0.4.37 and names a changelog record of its own")
except Exception as exc:
    verdict(False, "version: bin/VERSION is past 0.4.37 and names a changelog record of its own", str(exc))

print("checkpoint: %d probe(s) failed" % failed)
sys.exit(1 if failed else 0)
PY
rc=$?
case "$rc" in
  0|1|2) exit "$rc" ;;
  *) echo "checkpoint: python exited $rc" >&2; exit 2 ;;
esac
