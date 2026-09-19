#!/usr/bin/env bash
# Blind checkpoint v1 — sitting close 12 into claude/MASTER.md.
# Authored by the desk (master 2026-09-18-continue-plan-001) from the
# request, before any implementation exists. Outcome-only, read-only:
# it reads one file. Exit 0 PASS, 1 HOLD, 2 fixture error.
set -u
python3 - <<'PY'
import re, sys
from pathlib import Path

fails = 0
def verdict(ok, label):
    global fails
    print(("[PASS] " if ok else "[FAIL] ") + label, flush=True)
    if not ok:
        fails += 1

p = Path("claude/MASTER.md")
if not p.is_file():
    print("[ERROR] fixture: claude/MASTER.md is missing from the tree")
    sys.exit(2)
lines = p.read_text(encoding="utf-8").split("\n")

def section(n):
    """Lines of `## n. …` up to the next `## ` heading (strict anchors)."""
    starts = [i for i, ln in enumerate(lines) if ln.startswith(f"## {n}. ")]
    if len(starts) != 1:
        print(f"[ERROR] fixture: expected exactly one '## {n}. ' heading, "
              f"found {len(starts)}")
        sys.exit(2)
    i = starts[0]
    j = next((k for k in range(i + 1, len(lines))
              if lines[k].startswith("## ")), len(lines))
    return lines[i:j]

s3, s4, s5, s6, s7 = (section(n) for n in (3, 4, 5, 6, 7))
MASTER = "2026-09-18-continue-plan-001"
WORKERS = ("2026-09-18-board-109-harness-micro-002",
           "2026-09-18-board-47b-relay-blocks-003",
           "2026-09-18-board-107-supersedes-clean-tree-004")

header = [ln for ln in lines[:40] if ln.startswith("Last landed by:")]
verdict(len(header) == 1 and re.fullmatch(
    r"Last landed by: `\d{4}-\d{2}-\d{2}-sitting-close-deltas-12-\d{3}`\.",
    header[0]) is not None,
    "header-names-this-close-once-in-place")

verdict(any(ln.startswith("Landed 2026-09-18") for ln in s3)
        and any(MASTER in ln for ln in s3),
        "in-flight-carries-the-2026-09-18-close-block")

for sid in WORKERS:
    verdict(any(sid in ln for ln in s4),
            "board-cites-" + sid.split("-board-")[1])

def numbered(sec, n):
    return [i for i, ln in enumerate(sec) if ln.startswith(f"{n}. **")]

rows_ok = all(len(numbered(s4, n)) == 1 for n in range(1, 112))
order_ok = rows_ok and (numbered(s4, 109)[0] < numbered(s4, 110)[0]
                        < numbered(s4, 111)[0])
verdict(rows_ok and order_ok,
        "board-rows-1-to-111-each-once-with-110-and-111-appended")
verdict(not numbered(s4, 112), "board-ends-at-row-111")

ev_ok = all(len(numbered(s6, n)) == 1 for n in range(100, 164))
ev_order = ev_ok and all(numbered(s6, n)[0] < numbered(s6, n + 1)[0]
                         for n in range(154, 163))
verdict(ev_ok and ev_order,
        "evidence-100-to-163-each-once-with-155-to-163-in-order")

verdict(sum(1 for ln in s5 if ln.startswith("New, ratified 2026-09-18")) == 1,
        "contracts-carry-one-2026-09-18-heading")
verdict(any("0.4.36" in ln for ln in s7),
        "standing-facts-carry-the-0-4-36-landmark")
verdict(not any("TODO(" in ln for ln in lines),
        "no-unfilled-sentinel-anywhere")

sys.exit(1 if fails else 0)
PY
