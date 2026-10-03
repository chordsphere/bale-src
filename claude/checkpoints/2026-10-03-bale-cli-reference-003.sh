#!/usr/bin/env bash
# Blind checkpoint — session bale-cli-reference (2026-10-03-friction-points-001 desk).
# Authored blind from the request, before implementation. Outcome-only:
# it packs fixture requests with this tree as the install and judges what
# a worker in another project receives. Exit 0 = every probe passes;
# 1 = a probe failed; 2 = the oracle itself broke (a failed control).
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1
ROOT="$(pwd)"
exec python3 - "$ROOT" <<'PY'
import os, re, shutil, subprocess, sys, tarfile, tempfile

ROOT = sys.argv[1]
FAILED = []

def verdict(ok, label, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(label)

def control_fail(msg):
    print(f"control failed: {msg}")
    sys.exit(2)

VERBS = [("pack",), ("apply",), ("retry",), ("amend-checkpoint",), ("relay",),
         ("revert",), ("rollback",), ("unlock",), ("open",), ("handoff",),
         ("config",), ("config", "init"), ("config", "hooks"), ("help",),
         ("completion",), ("status",), ("stats",)]
GLOBAL_DOCS = ["AGENT.md", "TARBALL.md", "DOCS.md", "CODE.md", "PLANNER.md"]
TOOLS = ["tools/craft_response.py", "tools/response_lint.py"]

T = tempfile.mkdtemp(prefix="ck-")
HOME = os.path.join(T, "home")
INST = os.path.join(T, "inst")
os.makedirs(HOME)
with open(os.path.join(HOME, ".gitconfig"), "w") as f:
    f.write("[user]\n\tname = Desk Fixture\n\temail = desk@example.invalid\n"
            "[init]\n\tdefaultBranch = main\n")

def ignore(d, entries):
    if os.path.abspath(d) == os.path.abspath(ROOT):
        return [e for e in entries if e in (".git", ".bale", "user")]
    return [e for e in entries if e == "__pycache__"]

try:
    shutil.copytree(ROOT, INST, symlinks=True, ignore=ignore)
except Exception as e:
    control_fail(f"could not copy the tree as an install: {e}")
BALE = os.path.join(INST, "bin", "bale")

ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": HOME,
       "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "PYTHONDONTWRITEBYTECODE": "1",
       "EDITOR": "true", "VISUAL": "true"}

def bale(args, cwd, columns="80"):
    env = dict(ENV, COLUMNS=columns)
    return subprocess.run([sys.executable, BALE, *args], cwd=cwd, env=env,
                          stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=180)

def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, env=ENV, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def make_repo(name):
    repo = os.path.join(T, name)
    os.makedirs(os.path.join(repo, "src"))
    with open(os.path.join(repo, "src", "app.py"), "w") as f:
        f.write("print('hi')\n")
    git(repo, "init", "-q")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo

def collapse(text):
    return " ".join(text.split())

def request_files(tarball):
    """{path relative to request-NNN/: bytes} for every regular file."""
    out = {}
    with tarfile.open(tarball) as tf:
        for m in tf.getmembers():
            if not m.isfile():
                continue
            parts = m.name.split("/", 1)
            if len(parts) == 2:
                out[parts[1]] = tf.extractfile(m).read()
    return out

def pack(repo, slug, columns):
    p = bale(["pack", "Fixture goal for the reference probe", "--slug", slug,
              "--include", "src", "--no-readme"], repo, columns)
    if p.returncode != 0:
        return None, p
    outbox = os.path.join(repo, ".bale", "outbox")
    tars = sorted(f for f in os.listdir(outbox) if f.startswith("request-") and slug in f)
    return (os.path.join(outbox, tars[-1]) if tars else None), p

# ---- control: the tree runs as an install and its help renders -----------
helps = {}
for v in VERBS:
    p = bale(["help", *v], T)
    if p.returncode != 0 or "usage:" not in p.stdout:
        control_fail(f"`bale help {' '.join(v)}` did not render from the tree (exit {p.returncode})")
    helps[v] = p.stdout

# ---- 1. a project request carries the reference --------------------------
repo = make_repo("proj")
tb, p = pack(repo, "ref-a", "80")
if tb is None:
    control_fail(f"fixture pack failed (exit {p.returncode}): {p.stderr[-600:]}")
files = request_files(tb)
outside = {k: v for k, v in files.items() if not k.startswith("context/")}
verdict(all(d in files for d in GLOBAL_DOCS + TOOLS) and "manifest.json" in files,
        "request still carries manifest.json, the five docs, and the two tools")
cands = [k for k, v in outside.items()
         if k not in GLOBAL_DOCS + TOOLS + ["manifest.json", "README.md"]
         and b"usage: bale pack" in v]
verdict(len(cands) == 1, "request carries exactly one bale reference file outside context/",
        f"candidates: {cands}")
ref_name = cands[0] if len(cands) == 1 else None
ref = outside[ref_name].decode("utf-8", "replace") if ref_name else ""
flat = collapse(ref)
missing = [" ".join(v) for v in VERBS if collapse(helps[v]) not in flat]
verdict(ref_name is not None and not missing,
        "the reference holds every verb's `bale help` output verbatim (whitespace-insensitive)",
        "missing or altered: " + ", ".join(missing[:8]))

# ---- 2. deterministic: same install, any terminal width, same bytes ------
repo2 = make_repo("proj2")
tb2, p2 = pack(repo2, "ref-b", "200")
if tb2 is None:
    control_fail(f"second fixture pack failed (exit {p2.returncode})")
files2 = request_files(tb2)
verdict(ref_name is not None and files2.get(ref_name) == files.get(ref_name),
        "the reference is byte-identical across packs at different terminal widths")

# ---- 3. the shipped docs route a worker to it ----------------------------
base = os.path.basename(ref_name) if ref_name else "\x00no-reference\x00"
agent = files.get("AGENT.md", b"").decode("utf-8", "replace")
tarball_doc = files.get("TARBALL.md", b"").decode("utf-8", "replace")
rows = [ln for ln in agent.splitlines() if ln.lstrip().startswith("|") and base in ln]
verdict(bool(rows), "AGENT.md's INDEX read-paths table has a row naming the reference file")
shape = tarball_doc.split("### 3.1 Shape", 1)[-1].split("### 3.2", 1)[0]
verdict(base in shape, "TARBALL.md §3.1's request shape lists the reference file")

# ---- 4. a context tarball carries no reference ---------------------------
ctxdir = os.path.join(T, "ctxsrc")
os.makedirs(ctxdir)
with open(os.path.join(ctxdir, "notes.txt"), "w") as f:
    f.write("reading material\n")
pc = bale(["pack", "--context"], ctxdir)
ctx_out = os.path.join(ctxdir, ".bale", "outbox")
ctx_tars = (sorted(f for f in os.listdir(ctx_out) if f.startswith("context-") and f.endswith(".tar.gz"))
            if os.path.isdir(ctx_out) else [])
if pc.returncode != 0 or not ctx_tars:
    control_fail(f"fixture context pack failed (exit {pc.returncode}): {pc.stderr[-400:]}")
with tarfile.open(os.path.join(ctx_out, ctx_tars[-1])) as tf:
    carried = any(m.isfile() and b"usage: bale pack" in tf.extractfile(m).read()
                  for m in tf.getmembers())
verdict(not carried, "a context tarball (bale pack --context) carries no bale reference")

shutil.rmtree(T, ignore_errors=True)
print(f"checkpoint: {len(FAILED)} probe(s) failed")
sys.exit(1 if FAILED else 0)
PY
