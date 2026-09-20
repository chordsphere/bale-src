#!/usr/bin/env bash
# Blind checkpoint v1 — sitting close 14 into claude/MASTER.md.
# Authored 2026-09-20 by the master 2026-09-20-continue-plan-001 from the
# request alone, before any implementation exists. Outcome probes only:
# what must be true of the landed claude/MASTER.md, never how it got there.
# Read-only. Runs with cwd = the staging root. Needs python3; uses git for
# one probe and SKIPs that probe by name when git cannot serve it.
# Exit 0: every probe passed. Exit 1: at least one probe failed (HOLD).
# Exit 2: the oracle itself could not run or could not locate the
# structure it grades (a defective oracle, not a verdict on the work).
set -u
command -v python3 >/dev/null 2>&1 || { echo "checkpoint: python3 not found" >&2; exit 2; }
[ -f claude/MASTER.md ] || { echo "checkpoint: claude/MASTER.md not found under $(pwd)" >&2; exit 2; }

python3 - <<'PY'
import hashlib
import re
import subprocess
import sys

PATH = "claude/MASTER.md"
# sha256 of the base this oracle was authored against (MASTER.md as landed
# by 2026-09-19-sitting-close-deltas-13-010). Used only to decide whether
# git's HEAD copy is that base; never compared against the landed file.
BASE_SHA256 = "522152dab321de897d11ed6d24a0c341f59e6649e35ea1e8f55b0e168d329688"

SID_009 = "2026-09-19-continue-plan-009"
SID_010 = "2026-09-19-sitting-close-deltas-13-010"
SID_011 = "2026-09-19-board-113-dotted-run-form-011"
CLOSE14_SID = re.compile(r"\d{4}-\d{2}-\d{2}-sitting-close-deltas-14-\d{3}")

failed = 0
broken = 0


def verdict(ok, label, detail=""):
    # The verdict line carries the label alone: labels travel to the
    # worker on a HOLD. Detail goes on its own line, for the session log.
    global failed
    print(("[PASS] " if ok else "[FAIL] ") + label)
    if not ok:
        failed += 1
        if detail:
            print("  detail: " + detail)


def anchor(ok, label, detail=""):
    # An anchor locates preserved structure. It passes on the base and on
    # any insertions-only landing; failing means the oracle cannot grade.
    global broken
    print(("[PASS] " if ok else "[FAIL] ") + "anchor: " + label)
    if not ok:
        broken += 1


def skip(label, reason):
    print("[SKIP] " + label + " — " + reason)


def norm(lines):
    # Wrap-insensitive view: every whitespace run becomes one space.
    return " ".join(" ".join(lines).split())


with open(PATH, encoding="utf-8") as fh:
    L = fh.read().split("\n")

# ---- section bounds, by the "## N. " headings ---------------------------
heads = {}
for i, ln in enumerate(L):
    m = re.match(r"^## (\d+)\. ", ln)
    if m and int(m.group(1)) not in heads:
        heads[int(m.group(1))] = i
order = [heads.get(n) for n in range(1, 9)]
anchor(all(v is not None for v in order) and order == sorted(order),
       "the eight '## N. ' headings are present, in order")
if broken:
    sys.exit(2)


def section(n):
    start = heads[n]
    end = heads[n + 1] if (n + 1) in heads else len(L)
    return start, end


def find(start, end, pred):
    return [i for i in range(start, end) if pred(L[i])]


s3, e3 = section(3)
s4, e4 = section(4)
s6, e6 = section(6)
s7, e7 = section(7)

REG_PREV = "- Proposals of the `2026-09-19-session-fix-002` and"
REG_END = "Landed 2026-08-05, non-board (`2026-08-05-auto-sweep-009`):"
HARNESS_KEY = "- The `tests/harness.py` comment above `CLI_PATH`"
BLOCK_13B = "Landed 2026-09-19, the continue-plan-006 sitting (master"

reg_prev = find(s3, e3, lambda x: x.startswith(REG_PREV))
reg_end = find(s3, e3, lambda x: x == REG_END)
harness = find(s3, e3, lambda x: x.startswith(HARNESS_KEY))
b13 = find(s3, e3, lambda x: x.startswith(BLOCK_13B))
anchor(len(reg_prev) == 1 and len(reg_end) == 1 and reg_prev[0] < reg_end[0],
       "§3 registry: close 13's dispositions entry, then the registry's end line")
anchor(len(harness) == 1 and harness[0] < reg_prev[0],
       "§3 registry: the tests/harness.py CLI_PATH entry")
anchor(len(b13) == 1, "§3: close 13's second block")


def row_span(num):
    starts = find(s4, e4, lambda x: re.match(r"^%d\. \*\*" % num, x) is not None)
    if len(starts) != 1:
        return None
    nxt = [i for i in range(starts[0] + 1, e4) if re.match(r"^\d+[a-z]?\. \*\*", L[i])]
    return starts[0], (nxt[0] if nxt else e4)


rows = {n: row_span(n) for n in (37, 104, 113)}
anchor(all(rows[n] is not None for n in rows), "§4: rows 37, 104 and 113, one of each")
e170 = find(s6, e6, lambda x: x.startswith("170. **"))
anchor(len(e170) == 1, "§6: entry 170")
if broken:
    sys.exit(2)

# ---- 1. header -----------------------------------------------------------
hdr = [x for x in L[:s3] if x.startswith("Last landed by:")]
ok = len(hdr) == 1 and re.fullmatch(r"Last landed by: `%s`\." % CLOSE14_SID.pattern, hdr[0]) is not None
verdict(ok, "header: the last-landed-by line names a sitting-close-deltas-14 session")

# ---- 2. the new §3 block ---------------------------------------------------
landed = find(s3, e3, lambda x: x.startswith("Landed 20"))
NEW_BLOCK = "Landed 2026-09-19, the continue-plan-009 sitting (master"
block_ok = bool(landed) and L[landed[-1]].startswith(NEW_BLOCK) and landed[-1] > b13[0]
verdict(block_ok, "§3: a 'Landed 2026-09-19, the continue-plan-009 sitting' block follows close 13's and ends §3")
if block_ok:
    blk = L[landed[-1]:e3]
    text = norm(blk)
    missing = [s for s in (SID_009, SID_010, SID_011) if s not in text]
    verdict(not missing and CLOSE14_SID.search(text) is not None,
            "§3 block: names the 009 master, both landed sessions and the recording close",
            "missing: " + ", ".join(missing) if missing else "no sitting-close-deltas-14 sid")
    bullets = [x for x in blk if x.startswith("- ")]
    verdict(len(bullets) >= 2
            and bullets[-2].startswith("- Board deltas of this sitting's work:")
            and bullets[-1].startswith("- Registry deltas of this sitting's work:"),
            "§3 block: closes on the board-deltas bullet, then the registry-deltas bullet")
    replies = ["what is 104? can you explain this more?",
               "documentation in bale-src but not covered in global docs",
               "whatever makes sense"]
    gone = [r for r in replies if r not in text]
    verdict(not gone, "§3 block: the operator's three light-block replies, verbatim",
            "not found: " + " | ".join(gone))
else:
    for label in ("§3 block: names the 009 master, both landed sessions and the recording close",
                  "§3 block: closes on the board-deltas bullet, then the registry-deltas bullet",
                  "§3 block: the operator's three light-block replies, verbatim"):
        verdict(False, label, "no block to read")

# ---- 3. board rows ---------------------------------------------------------
OPEN = "    [2026-09-19: "


def brackets(span):
    return [i for i in range(span[0], span[1]) if L[i].startswith(OPEN)]


def row_tail_closed(span):
    body = [x for x in L[span[0]:span[1]] if x.strip()]
    return bool(body) and body[-1].rstrip().endswith("]")


r = rows[113]
b = brackets(r)
t = norm(L[b[-1]:r[1]]) if b else ""
verdict(bool(b) and t.startswith("[2026-09-19: DONE") and SID_011 in t and "56 of 68" in t and row_tail_closed(r),
        "§4 row 113: ends on a 2026-09-19 DONE bracket naming its session and the 56-of-68 count")

r = rows[37]
b = brackets(r)
t = norm(L[b[-1]:r[1]]) if b else ""
verdict(bool(b) and "compaction_occurred" in t
        and "documentation in bale-src but not covered in global docs" in t and row_tail_closed(r),
        "§4 row 37: ends on a 2026-09-19 re-scope bracket carrying compaction_occurred and reply 2 verbatim")

r = rows[104]
b = [i for i in range(r[0], r[1]) if L[i].startswith("    [2026-09-20: ")]
t = norm(L[b[-1]:r[1]]) if b else ""
verdict(bool(b) and "narrowed, as the 009 desk recommended" in t
        and re.search(r"[Cc]lose 13|" + re.escape(SID_010), t) is not None and row_tail_closed(r),
        "§4 row 104: ends on a 2026-09-20 re-scope bracket carrying the operator's answer verbatim and naming close 13's Proposals")

# ---- 4. registry -----------------------------------------------------------
nxt = [i for i in range(harness[0] + 1, e3) if L[i].startswith("- ") or L[i] == REG_END]
hs = L[harness[0]:(nxt[0] if nxt else e3)]
cons = [x for x in hs if x.startswith("  [2026-09-19: consumed at ")]
verdict(len(cons) == 1 and SID_011 in norm(hs),
        "§3 registry: the CLI_PATH comment entry carries one 2026-09-19 consumed bracket naming 113's session")

KEYS = ["- The three redundant `tests/`-on-path guards:",
        "- `packed_at` on a pack's `opened` telemetry attempt:",
        "- The closing pack's sid on a swept or superseded attempt:",
        "- Proposals of the `2026-09-19-continue-plan-009` sitting's workers"]
tail = range(reg_prev[0] + 1, reg_end[0])
pos = []
for k in KEYS:
    hit = [i for i in tail if L[i].startswith(k)]
    pos.append(hit[0] if len(hit) == 1 else None)
entries = [i for i in tail if L[i].startswith("- ")]
verdict(all(p is not None for p in pos) and pos == sorted(pos) and entries and entries[-1] == pos[-1],
        "§3 registry: four new entries end the list, the dispositions entry last")
reg_text = norm(L[reg_prev[0]:reg_end[0]])
quotes = ["so no fixed lag recovers it",
          "stamp the closing pack's own sid on the closed attempt",
          "the package init does their job in the dotted form"]
gone = [q for q in quotes if q not in reg_text]
verdict(not gone, "§3 registry: the three carried Proposals keep their source text",
        "not found: " + " | ".join(gone))

# ---- 5. evidence -----------------------------------------------------------
nums = [int(re.match(r"^(\d+)\. \*\*", L[i]).group(1))
        for i in range(e170[0] + 1, e6) if re.match(r"^\d+\. \*\*", L[i])]
verdict(len(nums) >= 5 and nums == list(range(171, 171 + len(nums))),
        "§6: entries 171 through 175 (or more, consecutive) follow entry 170 and end §6",
        "found after 170: " + (", ".join(map(str, nums)) or "none"))

# ---- 6. standing facts -----------------------------------------------------
t7 = norm(L[s7:e7])
need = ["tests/__init__.py", "read_bundle", "compose_pack_argv"]
gone = [n for n in need if n not in t7]
lm = find(s7, e7, lambda x: x.startswith("- Version landmark: unchanged at 0.4.37"))
verdict(not gone and len(lm) == 1,
        "§7: names tests/__init__.py, read_bundle and compose_pack_argv, and the unchanged 0.4.37 landmark",
        ("missing: " + ", ".join(gone)) if gone else "landmark line count: %d" % len(lm))

# ---- 7. insertions only ----------------------------------------------------
LABEL = "insertions only but for the last-landed-by line (against git HEAD)"
try:
    out = subprocess.run(["git", "show", "HEAD:" + PATH], capture_output=True, timeout=60)
except Exception as exc:  # git missing, sandbox refusal, timeout
    out = None
    skip(LABEL, "git could not run: %s" % exc)
if out is not None:
    if out.returncode != 0:
        skip(LABEL, "git show HEAD:%s exited %d" % (PATH, out.returncode))
    elif hashlib.sha256(out.stdout).hexdigest() != BASE_SHA256:
        skip(LABEL, "HEAD's copy is not the base this oracle was authored against")
    else:
        base = [x for x in out.stdout.decode("utf-8").split("\n") if not x.startswith("Last landed by:")]
        it = iter(x for x in L if not x.startswith("Last landed by:"))
        lost = next((x for x in base if not any(x == y for y in it)), None)
        verdict(lost is None, LABEL, "first base line not carried in order: %r" % (lost,))

print("checkpoint: %d probe(s) failed" % failed)
sys.exit(1 if failed else 0)
PY
rc=$?
case "$rc" in
  0|1|2) exit "$rc" ;;
  *) echo "checkpoint: python exited $rc" >&2; exit 2 ;;
esac
