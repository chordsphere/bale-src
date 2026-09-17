#!/usr/bin/env bash
# Blind checkpoint — board 106, the bin/bale de-dup micro.
# Authored at the desk from the request (2026-09-16/17 UTC), before any
# implementation existed; grades outcomes of the applied tree only.
# Runs from the staging root. Writes: a private tmpdir only (a scratch
# git repo with a repo-local identity, per the standing fact).
# Exit 0 = every probe PASS/SKIP, 1 = a probe FAILed, 2 = script error.
set -u
trap 'echo "[ERROR] checkpoint script errored at line $LINENO"; exit 2' ERR
echo "checkpoint 106 v1: writes to nothing in the tree (tmpdir only)"
fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fails=$((fails + 1)); }
tmp="$(mktemp -d)"; export CP_TMP="$tmp"; export CP_ROOT="$PWD"

python3 - <<'PY' || fails=$((fails + $?))
import ast, os, subprocess, sys
from pathlib import Path
fails = 0
def verdict(label, ok, detail=""):
    global fails
    print(("[PASS] " if ok else "[FAIL] ") + label + (f" — {detail}" if detail and not ok else ""))
    if not ok: fails += 1
root = Path(os.environ["CP_ROOT"]); tmp = Path(os.environ["CP_TMP"])
bale = root / "bin" / "bale"
def run(args, cwd):
    return subprocess.run([sys.executable, str(bale), *args], cwd=cwd,
                          capture_output=True, text=True)
try:
    # 1. fail_not_found: the absolute-path miss lists the near-name twin
    repo = tmp / "repo"; repo.mkdir()
    subprocess.run(["git", "init", "-q", str(repo)], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.email", "cp@example"], check=True)
    subprocess.run(["git", "-C", str(repo), "config", "user.name", "cp"], check=True)
    subprocess.run(["git", "-C", str(repo), "commit", "-q", "--allow-empty", "-m", "i"], check=True)
    dl = tmp / "dl"; dl.mkdir()
    twin = dl / "response-2026-06-05-fx-applied-001 (1).tar.gz"; twin.write_bytes(b"")
    miss = str(dl / "response-2026-06-05-fx-applied-001.tar.gz")
    for verb in ("apply", "retry", "handoff"):
        r = run([verb, miss], cwd=repo)
        verdict(f"absolute-miss-lists-near-name-twin-{verb}",
                r.returncode != 0 and "not found" in r.stderr
                and f'bale {verb} "{twin}"' in r.stderr and r.stdout.strip() == "",
                f"rc={r.returncode} stderr={r.stderr[-300:]!r}")
    # 2. one home for the forecast-existence gate
    src = bale.read_text()
    verdict("handoff-gate-text-has-one-home-in-bale-pack",
            "--write path does not exist" not in src
            and "--write path does not exist" in (root / "bin/bale_pack.py").read_text())
    # 3. compose_retry_successor delegates
    tree = ast.parse(src)
    fn = next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)
               and n.name == "compose_retry_successor"), None)
    calls = {getattr(c.func, "attr", getattr(c.func, "id", None))
             for c in ast.walk(fn) if isinstance(c, ast.Call)} if fn else set()
    verdict("compose-retry-successor-calls-compose-hold-successors",
            fn is not None and "compose_hold_successors" in calls, f"calls={sorted(x for x in calls if x)}")
    # 4. from_lines error text names no .baleignore; the loader does
    sys.path.insert(0, str(root / "bin"))
    # Both checks run in a subprocess: the file loader refuses through
    # fail() (SystemExit + stderr), so the outcome is what the process says.
    helper = tmp / "probe_baleignore.py"
    helper.write_text(
        "import runpy, sys\nfrom pathlib import Path\n"
        "g = runpy.run_path(sys.argv[1], run_name='bale_probe')\n"
        "if sys.argv[2] == 'lines':\n"
        "    try: g['BaleignoreMatcher'].from_lines(['!negated']); print('NOERR')\n"
        "    except Exception as e: print(str(e))\n"
        "else:\n"
        "    d = Path(sys.argv[3]); (d / '.baleignore').write_text('!negated\\n')\n"
        "    g['load_baleignore'](d); print('NOERR')\n")
    r = subprocess.run([sys.executable, str(helper), str(bale), "lines"],
                       capture_output=True, text=True, cwd=root / "bin")
    verdict("from-lines-error-names-no-baleignore",
            "NOERR" not in r.stdout and r.stdout.strip() != ""
            and ".baleignore" not in r.stdout, f"out={r.stdout[-200:]!r}")
    r2 = tmp / "repo2"; r2.mkdir()
    r = subprocess.run([sys.executable, str(helper), str(bale), "file", str(r2)],
                       capture_output=True, text=True, cwd=root / "bin")
    verdict("baleignore-file-loader-error-names-baleignore",
            "NOERR" not in r.stdout and ".baleignore" in (r.stderr + r.stdout),
            f"rc={r.returncode} err={r.stderr[-200:]!r}")
    # 5. completion --help keeps its example lines
    h = run(["completion", "--help"], cwd=repo).stdout
    lines = h.splitlines()
    verdict("completion-help-keeps-example-lines",
            any(l.strip() == "source <(bale completion bash)" for l in lines)
            and any(l.strip().startswith("bale completion bash >") for l in lines)
            and "\n\n" in h.split("positional arguments")[0].strip())
    # rider: 105's in-process constants test exists
    t = (root / "tests/test_pack_opener.py").read_text()
    verdict("pack-opener-in-process-constants-test",
            "session_opener_block" in t and "OPENER_AUTHORITY_SENTENCE" in t
            and "OPENER_TOOLS_SENTENCE" in t)
except Exception as e:
    print(f"[FAIL] probe-errored: {type(e).__name__}: {e}"); fails += 1
sys.exit(fails)
PY

suites_ok=1
for suite in test_apply_preflight test_amend_checkpoint test_hold_retry_e2e \
             test_handoff_forecast test_pack_opener test_pack_guards; do
  if ! python3 -m unittest discover -s tests -p "${suite}.py" >> "$tmp/suites.log" 2>&1; then
    suites_ok=0; echo "  suite failed: $suite"; fi
done
if [ "$suites_ok" -eq 1 ]; then pass "dedup-suites-pass"; else
  fail "dedup-suites-pass"; tail -30 "$tmp/suites.log"; fi
rm -rf "$tmp"
if [ "$fails" -ne 0 ]; then echo "checkpoint 106 v1: $fails probe(s) failed"; exit 1; fi
echo "checkpoint 106 v1: all probes passed"; exit 0
