#!/usr/bin/env bash
# Blind checkpoint v1 — board row 109, narrowed (harness loaders; the
# class move is deferred). Authored by the desk (master
# 2026-09-18-continue-plan-001) from the request, before any
# implementation exists. Outcome-only; writes nothing outside
# Python's own caches. Exit 0 PASS, 1 HOLD, 2 fixture error.
set -u
ROOT="$(pwd)"
export PYTHONDONTWRITEBYTECODE=1
python3 - "$ROOT" <<'PY'
import ast, subprocess, sys
from pathlib import Path

root = Path(sys.argv[1])
tests = root / "tests"
fails = 0

def verdict(ok, label):
    global fails
    print(("[PASS] " if ok else "[FAIL] ") + label, flush=True)
    if not ok:
        fails += 1

for needed in ("harness.py", "test_doc_crossrefs.py", "test_sanctioned_pairs.py"):
    if not (tests / needed).is_file():
        print(f"[ERROR] fixture: tests/{needed} is missing from the tree")
        sys.exit(2)

sys.path.insert(0, str(tests))
try:
    import harness as H
except Exception as e:
    print(f"[ERROR] fixture: tests/harness.py does not import: {e!r}")
    sys.exit(2)

# 1. normalize() has its home in the harness, and behaves.
norm = getattr(H, "normalize", None)
verdict(callable(norm) and norm("  a \n\t b  c\n") == "a b c",
        "harness-normalize-collapses-whitespace")

# 2. One home: neither doc-pin suite still defines its own copy.
def defines_normalize(path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return any(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name == "normalize" for n in tree.body)

verdict(not defines_normalize(tests / "test_doc_crossrefs.py")
        and not defines_normalize(tests / "test_sanctioned_pairs.py"),
        "doc-pin-suites-define-no-normalize-of-their-own")

# 3. _load_cli() reaches names that live only in bin/bale, in-process,
#    without running the CLI. Attribute or mapping access both count.
def reach(obj, name):
    if isinstance(obj, dict):
        return obj.get(name)
    return getattr(obj, name, None)

cli_ok = False
loader = getattr(H, "_load_cli", None)
if callable(loader):
    try:
        cli = loader()
        cli_ok = all(callable(reach(cli, n)) for n in
                     ("fail_not_found", "compose_retry_successor"))
    except BaseException as e:  # SystemExit included: the CLI must not run
        print(f"       _load_cli() raised {e!r}")
verdict(cli_ok, "load-cli-reaches-bin-bale-only-functions")

# 4. The loader has at least one test that uses it.
users = [p.name for p in sorted(tests.glob("test_*.py"))
         if "_load_cli" in p.read_text(encoding="utf-8")]
verdict(bool(users), "some-test-file-exercises-load-cli")

# 5. The two doc-pin suites still pass on the new import.
for suite in ("test_doc_crossrefs.py", "test_sanctioned_pairs.py"):
    r = subprocess.run([sys.executable, "-m", "unittest", "discover",
                        "-s", "tests", "-p", suite],
                       cwd=root, capture_output=True, text=True)
    ran_some = "Ran 0 tests" not in r.stderr
    verdict(r.returncode == 0 and ran_some, f"suite-passes-{suite[:-3]}")
    if r.returncode != 0:
        print("       " + " | ".join(r.stderr.strip().splitlines()[-4:]))

# 6. The shape sentence's third home is pinned: with TARBALL.md 5.10's
#    copy struck in a scratch copy of the tree, test_doc_crossrefs fails.
import shutil, tempfile
scratch = Path(tempfile.mkdtemp(prefix="cp109-")) / "tree"
scratch.mkdir()
for part in ("bin", "docs", "schemas", "tools", "tests", "scripts"):
    if (root / part).is_dir():
        shutil.copytree(root / part, scratch / part)
for part in ("install.sh", "validate.sh", "upgrade.sh", "BALE.md", "README.md"):
    if (root / part).is_file():
        shutil.copy2(root / part, scratch / part)
doc = scratch / "docs" / "TARBALL.md"
text = doc.read_text(encoding="utf-8")
start = text.find("### 5.10")
stop = text.find("\n## ", start + 1)
needle = "nothing is lost"
section = text[start:stop] if start >= 0 and stop > start else ""
if needle not in " ".join(section.split()):
    print("[ERROR] fixture: TARBALL.md 5.10 no longer carries the shape "
          "sentence's second half; this probe's premise is gone")
    sys.exit(2)
import re
struck = re.sub(r"nothing\s+is\s+lost", "nothing is mislaid", section)
doc.write_text(text[:start] + struck + text[stop:], encoding="utf-8")
def crossrefs(tree):
    return subprocess.run([sys.executable, "-m", "unittest", "discover",
                           "-s", "tests", "-p", "test_doc_crossrefs.py"],
                          cwd=tree, capture_output=True, text=True)
mutated = crossrefs(scratch)
verdict(mutated.returncode != 0 and "Ran 0 tests" not in mutated.stderr,
        "crossrefs-suite-fails-when-5-10-shape-sentence-is-struck")

sys.exit(1 if fails else 0)
PY
