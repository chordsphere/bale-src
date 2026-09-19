#!/usr/bin/env bash
# Blind checkpoint v1 — child session slug opener-reword-docs (the doc-sweep
# half; its sid is whatever pack allocates).
# Authored at the sub-master split of 2026-09-19-opener-reword-doc-sweep-r2-003,
# from the child's request and the r2 brief's VERBATIM blocks (extracted
# mechanically from the brief's bytes), before any implementation exists.
# Outcome-only over the landed global docs: fixed strings for the rulings
# of record (the brief marks them VERBATIM, whitespace collapsed),
# invariant-shaped probes for authored prose, and the global docs'
# self-containment suite. Connective wording is the worker's and is not
# graded; the sweep's judgment calls are not graded.
# Exit: 0 every probe passed; 1 at least one [FAIL] (HOLD); 2 the oracle
# itself could not run.
set -u
for f in docs/CLAUDE.md docs/TARBALL.md; do
  [ -f "$f" ] || { echo "checkpoint: $f missing — not a bale-src tree root (cwd=$(pwd))" >&2; exit 2; }
done
command -v python3 >/dev/null 2>&1 || { echo "checkpoint: python3 not found" >&2; exit 2; }
python3 - <<'PYEOF'
import re, subprocess, sys
from pathlib import Path

V = {'DOC_DELIVERABLE': 'What a session owes back follows from how it was packed: a worker session, any pack with a write forecast, owes one response tarball carrying the finished work; a planner session, a read-only pack, lands nothing and returns no response tarball, not even an empty one — it owes its answer in chat and, for each session it is asked to author, a crafter bundle beside its `bale open` line.', 'DOC_ASK': 'A turn that needs something from the packer, an environment fact or a decision, ends in the matching shape: a probe block, a light question block, or a clarification response; a question asked as prose is not a shape, because it gets lost. Every other turn is ordinary prose.'}
ROOT = Path.cwd()
failed = []
def verdict(ok, label, detail=""):
    print(("[PASS] " if ok else "[FAIL] ") + label)
    if not ok:
        failed.append(label)
        if detail:
            print("       " + detail[:600].replace("\n", "\n       "))

def collapse(s):
    return " ".join(s.split())

def section(text, heading_re, level):
    """Body from the first heading matching heading_re up to the next
    heading of the same or a higher level (strict line anchors)."""
    lines = text.splitlines()
    start = next((i for i, ln in enumerate(lines) if re.match(heading_re, ln)), None)
    if start is None:
        return None
    stop = re.compile(r"^#{1,%d}\s" % level)
    end = next((j for j in range(start + 1, len(lines)) if stop.match(lines[j])), len(lines))
    return "\n".join(lines[start:end])

claude = (ROOT / "docs/CLAUDE.md").read_text(encoding="utf-8")
tarball = (ROOT / "docs/TARBALL.md").read_text(encoding="utf-8")
KEY = re.compile(r"(?<![A-Za-z_])readme(?![A-Za-z_.])")   # the manifest key, not README.md
OLD_SHAPE = "takes one machine-recognizable shape"
OLD_SECOND_HALF = "Explanation in prose is expected and welcome"

# --- CLAUDE.md section 3: what each session owes back; the ask rule -----
s3 = section(claude, r"^## 3\. ", 2)
verdict(s3 is not None, "CLAUDE.md: section 3 heading present")
if s3 is not None:
    c3 = collapse(s3)
    verdict(collapse(V["DOC_DELIVERABLE"]) in c3, "CLAUDE.md 3: deliverable sentence verbatim")
    verdict(collapse(V["DOC_ASK"]) in c3, "CLAUDE.md 3: ask sentence verbatim")
    verdict(OLD_SHAPE not in c3, "CLAUDE.md 3: the every-turn shape sentence is retired")
    verdict(OLD_SECOND_HALF not in c3, "CLAUDE.md 3: the shape sentence's second half is retired")

# --- CLAUDE.md META reading order: the brief is named third -------------
ro = section(claude, r"^### Reading order", 3)
verdict(ro is not None, "CLAUDE.md: META Reading order heading present")
if ro is not None:
    items = {}
    cur = None
    for ln in ro.splitlines():
        m = re.match(r"^(\d+)\.\s", ln)
        if m:
            cur = int(m.group(1)); items[cur] = ln
        elif cur is not None and ln.startswith("   "):
            items[cur] += " " + ln.strip()
        elif not ln.strip():
            cur = None
    verdict("manifest.json" in items.get(1, ""), "CLAUDE.md reading order: item 1 is manifest.json")
    verdict("CLAUDE.md" in items.get(2, ""), "CLAUDE.md reading order: item 2 is CLAUDE.md")
    verdict("README.md" in items.get(3, ""), "CLAUDE.md reading order: item 3 names README.md",
            items.get(3, "(no item 3)"))
    verdict(bool(KEY.search(ro)), "CLAUDE.md reading order: names the manifest's readme key")
    verdict("session prompt" not in collapse(ro).lower(), "CLAUDE.md reading order: 'the session prompt' retired")

# --- CLAUDE.md INDEX 'Every session' row --------------------------------
row = next((ln for ln in claude.splitlines() if ln.startswith("| Every session |")), None)
verdict(row is not None, "CLAUDE.md INDEX: the Every session row is present")
if row is not None:
    verdict("README.md" in row, "CLAUDE.md INDEX Every session: names README.md")
    verdict(bool(KEY.search(row)), "CLAUDE.md INDEX Every session: names the manifest's readme key")
    verdict("session prompt" not in row.lower(), "CLAUDE.md INDEX Every session: 'the session prompt' retired")

# --- TARBALL.md ---------------------------------------------------------
ct = collapse(tarball)
verdict(collapse(V["DOC_DELIVERABLE"]) in ct, "TARBALL.md: deliverable sentence verbatim (home is the worker's)")
s510 = section(tarball, r"^### 5\.10 ", 3)
verdict(s510 is not None, "TARBALL.md: section 5.10 heading present")
if s510 is not None:
    c510 = collapse(s510)
    verdict(collapse(V["DOC_ASK"]) in c510, "TARBALL.md 5.10: ask sentence verbatim")
    verdict(OLD_SHAPE not in c510, "TARBALL.md 5.10: the every-turn shape sentence is retired")
    verdict(OLD_SECOND_HALF not in c510, "TARBALL.md 5.10: the shape sentence's second half is retired")
    verdict("Admission is a count, not a judgment." in c510,
            "TARBALL.md 5.10: the admission sentence is untouched")
    verdict("The block ends with the packer's three replies, every time." in c510,
            "TARBALL.md 5.10: the three-replies sentence is untouched")
s31 = section(tarball, r"^### 3\.1 ", 3)
verdict(s31 is not None, "TARBALL.md: section 3.1 heading present")
if s31 is not None:
    verdict("Most sessions skip the README" not in collapse(s31),
            "TARBALL.md 3.1: the stale most-sessions-skip claim is gone")
s32 = section(tarball, r"^### 3\.2 ", 3)
verdict(s32 is not None, "TARBALL.md: section 3.2 heading present")
if s32 is not None:
    verdict(re.search(r'"readme"\s*:', s32) is not None,
            "TARBALL.md 3.2: the example manifest carries the readme key")
    prose = re.sub(r"```.*?```", "", s32, flags=re.S)
    verdict(bool(KEY.search(prose)), "TARBALL.md 3.2: the field semantics name the readme key")

# --- the global docs stay self-contained --------------------------------
t = ROOT / "tests" / "test_global_doc_selfcontainment.py"
if not t.is_file():
    verdict(False, "self-containment suite present")
else:
    r = subprocess.run([sys.executable, str(t)], cwd=ROOT / "tests",
                       capture_output=True, text=True, timeout=300)
    verdict(r.returncode == 0, "global docs stay self-contained", (r.stdout + r.stderr)[-1200:])

print(f"checkpoint: {len(failed)} probe(s) failed")
sys.exit(1 if failed else 0)
PYEOF
