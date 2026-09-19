#!/usr/bin/env bash
# Blind checkpoint v1 — board 111 (narrowed), tests smalls.
# Authored at the desk of 2026-09-19-continue-plan-006 from the request,
# before any implementation exists. Outcome contracts only.
# Writes: a mktemp directory under /tmp, nothing else.
set -uo pipefail
command -v python3 >/dev/null 2>&1 || { echo "checkpoint: python3 not found"; exit 2; }
[ -f tests/harness.py ] || { echo "checkpoint: tests/harness.py not found (cwd must be the staged tree)"; exit 2; }
WORK="$(mktemp -d /tmp/cp111.XXXXXX)" || exit 2
trap 'rm -rf "$WORK"' EXIT
echo "checkpoint writes only under: $WORK"
CP111_WORK="$WORK" python3 - <<'PY'
import ast, os, re, shutil, subprocess, sys, traceback
from pathlib import Path

STAGED = Path.cwd()
WORK = Path(os.environ["CP111_WORK"])
FAILED = []

def verdict(ok, label, detail=""):
    print(("[PASS] " if ok else "[FAIL] ") + label)
    if not ok:
        FAILED.append(label)
        if detail:
            print("       " + detail.replace("\n", "\n       "))

def run_suite(root, name):
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
           "HOME": os.environ.get("HOME", str(WORK)),
           "LANG": os.environ.get("LANG", "C.UTF-8")}
    return subprocess.run([sys.executable, str(root / "tests" / f"{name}.py")],
                          cwd=root, env=env, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=600)

def code_names(path):
    """Every identifier the module's CODE uses — comments and
    docstrings are invisible to the AST, so prose may say anything."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            names.add(node.attr)
        elif isinstance(node, ast.alias):
            names.add(node.name.split(".")[-1])
            if node.asname:
                names.add(node.asname)
    return names

def loader_probes():
    for rel in ("tests/test_thread_status.py", "tests/test_craft_response.py"):
        names = code_names(STAGED / rel)
        verdict("_load_cli" in names and "SourceFileLoader" not in names,
                f"{rel}: bin/bale is loaded through the harness's _load_cli, and no hand-rolled SourceFileLoader remains in its code",
                f"_load_cli used: {'_load_cli' in names}; SourceFileLoader used: {'SourceFileLoader' in names}")
    for name in ("test_thread_status", "test_craft_response"):
        r = run_suite(STAGED, name)
        verdict(r.returncode == 0, f"tests/{name}.py passes when run directly",
                (r.stderr or r.stdout)[-1500:])

DOC_PIN_SUITES = ("test_doc_crossrefs", "test_sanctioned_pairs",
                  "test_global_doc_selfcontainment", "test_schema_embeds")
PARA_FIRST = "A HOLD reaches the worker as one addressed block that `bale apply`"
PARA_LAST = "work, the ask is for the spec from those labels (`PLANNER.md` §5)."

def relay_pin_probe():
    green = [(n, run_suite(STAGED, n)) for n in DOC_PIN_SUITES]
    bad = [n for n, r in green if r.returncode != 0]
    verdict(not bad, "the four doc-pin suites pass on the staged docs",
            "failing: " + ", ".join(bad))
    copy = WORK / "mutated"
    shutil.copytree(STAGED, copy, symlinks=True,
                    ignore=shutil.ignore_patterns(".git", ".bale", "__pycache__", "dist"))
    doc = copy / "docs" / "TARBALL.md"
    lines = doc.read_text(encoding="utf-8").split("\n")
    firsts = [i for i, ln in enumerate(lines) if ln == PARA_FIRST]
    lasts = [i for i, ln in enumerate(lines) if ln == PARA_LAST]
    located = len(firsts) == 1 and len(lasts) == 1 and firsts[0] < lasts[0]
    verdict(located, "anchor: TARBALL.md section 7's worker relay paragraph is where the base has it",
            f"first-line matches: {len(firsts)}; last-line matches: {len(lasts)}")
    if not located:
        return
    a, b = firsts[0], lasts[0]
    para = "\n".join(lines[a:b + 1])
    mutated, count = re.subn(r"to(\s+)worker ===", r"to\1builder ===", para)
    verdict(count == 2, "anchor: the paragraph names the worker sentinel twice (BEGIN and END)",
            f"occurrences: {count}")
    if count != 2:
        return
    doc.write_text("\n".join(lines[:a] + mutated.split("\n") + lines[b + 1:]), encoding="utf-8")
    red = [n for n in DOC_PIN_SUITES if run_suite(copy, n).returncode != 0]
    verdict(bool(red),
            "a doc-pin suite goes red when the paragraph's `to worker` sentinel drifts from the wire",
            "every doc-pin suite stayed green against the drifted doc")

errored = False
for fn in (loader_probes, relay_pin_probe):
    try:
        fn()
    except Exception:
        errored = True
        print(f"checkpoint: {fn.__name__} errored before its probes could finish")
        traceback.print_exc()
if errored:
    sys.exit(2)
sys.exit(1 if FAILED else 0)
PY
exit $?
