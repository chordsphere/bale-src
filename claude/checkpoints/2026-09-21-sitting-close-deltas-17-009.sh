#!/usr/bin/env bash
# Blind checkpoint, v1 — sitting close 17 (slug sitting-close-deltas-17).
# Authored at the 2026-09-21-continue-plan-008 desk from the request, before
# any implementation exists. Outcome-only: it reads claude/MASTER.md in the
# tree it is run in and, where HEAD still holds the authored base, that base.
# It writes nothing. Verdict lines carry the label alone; detail goes on a
# following "  detail:" line. Exit 0 all pass, 1 a probe failed, 2 the
# oracle itself is broken (a failed control, or a base anchor missing).
set -u
export PYTHONDONTWRITEBYTECODE=1
exec python3 -B - "$@" <<'PYEOF'
import hashlib
import re
import subprocess
import sys

DOC = "claude/MASTER.md"
BASE_SHA = "3cda112d02318faca00f1e8dab21c7022cf6598f0189170abaeec2b66b3151ee"
SID_RE = re.compile(
    r"(?<![A-Za-z0-9-])20\d\d-\d\d-\d\d-[a-z0-9]+(?:-[a-z0-9]+)*-\d{3}(?![A-Za-z0-9-])")
OWN_SID_RE = re.compile(r"20\d\d-\d\d-\d\d-sitting-close-deltas-17-\d{3}")
TOLERATED_SIDS = {"2026-09-21-continue-plan-008"}


def broken(why):
    print("oracle error: " + why)
    sys.exit(2)


# --- control: the sid pattern's own detectors -------------------------------
def control():
    yes = ["`2026-09-21-continue-plan-005`", "(2026-09-21-board-103-doc-lane-006)"]
    no = ["2026-09-21-board-103-doc-lane.bale-bundle",
          "2026-09-21-board-103-doc-lane",
          "2026-09-21-sitting-close-deltas-16-r2",
          "2026-09-21-continue-plan-wave-10.bale-bundle"]
    for s in yes:
        if len(SID_RE.findall(s)) != 1:
            return False
    for s in no:
        if SID_RE.findall(s):
            return False
    return True


if not control():
    broken("control failed: the session-id pattern")

try:
    with open(DOC, encoding="utf-8") as fh:
        text = fh.read()
except OSError as exc:
    broken("cannot read %s: %s" % (DOC, exc))
L = text.split("\n")


def first(pred, lo=0, hi=None):
    hi = len(L) if hi is None else hi
    for i in range(lo, hi):
        if pred(L[i]):
            return i
    return None


def anchor(prefix, lo=0, hi=None, name=None):
    i = first(lambda l: l.startswith(prefix), lo, hi)
    if i is None:
        broken("base anchor missing: " + (name or prefix))
    return i


def collapse(lines):
    return " ".join(" ".join(lines).split())


# --- base anchors (preserved text; a missing one is the oracle's problem) ---
S3 = anchor("## 3. ")
S4 = anchor("## 4. The board")
S5 = anchor("## 5. ")
S6 = anchor("## 6. ")
S7 = anchor("## 7. ")
S8 = anchor("## 8. ")
B009 = anchor("Landed 2026-09-20, the continue-plan-009 sitting (master", S3, S4)
REG_114 = anchor("- The `docs/CLAUDE.md` §11.4 pointer:", S3, S4)
REG_EX2 = anchor("- A failed oracle control exits 2, for PLANNER.md §4:", S3, S4)
REG_OLD_LAST = anchor("- Proposals of the `2026-09-20-continue-plan-006` and", S3, S4)
REG_END = anchor("Landed 2026-08-05, non-board", REG_OLD_LAST, S4)
ROW103 = anchor("103. **", S4, S5)
ROW104 = anchor("104. **", ROW103, S5)
ROW113 = anchor("113. **", ROW104, S5)
C_EX2_HOME = anchor("  script itself errored\". Home: this section, until a", S5, S6,
                    "the exit-2 contract's Home sentence")
C_SWEEP = anchor("- **A pack records what it swept", C_EX2_HOME, S6)
E191 = anchor("191. **", S6, S7)
E192 = anchor("192. **", E191, S7)
E194 = anchor("194. **", E192, S7)
ENV_LAST = anchor("- A record's `base_files` map can run past a hundred entries.", S7, S8)

# --- the authored base, when HEAD still holds it ---------------------------
base_lines = None
base_why = "HEAD does not hold the authored base"
try:
    got = subprocess.run(["git", "show", "HEAD:" + DOC], capture_output=True)
    if got.returncode == 0 and hashlib.sha256(got.stdout).hexdigest() == BASE_SHA:
        base_lines = got.stdout.decode("utf-8").split("\n")
    elif got.returncode != 0:
        base_why = "git show HEAD:%s failed" % DOC
except OSError:
    base_why = "git is not available"

results = []


def probe(label, fn, needs_base=False):
    if needs_base and base_lines is None:
        results.append(("SKIP", label, base_why))
        return
    try:
        ok, detail = fn()
    except Exception as exc:  # a probe that throws is the oracle's defect
        broken("probe raised (%s): %r" % (label, exc))
    results.append(("PASS" if ok else "FAIL", label, detail))


# inserted lines, in order, line 14 apart (None when the walk fails)
def walk_insertions():
    if L[:13] != base_lines[:13]:
        return None, "lines 1 to 13 differ from the base"
    new_rest, base_rest = L[14:], base_lines[14:]
    ins, j = [], 0
    for line in new_rest:
        if j < len(base_rest) and line == base_rest[j]:
            j += 1
        else:
            ins.append(line)
    if j != len(base_rest):
        return None, "base line %d is altered, moved or gone" % (j + 15)
    if len(ins) + len(base_rest) != len(new_rest):
        return None, "line arithmetic does not close"
    return ins, ""


# 1
def p_header():
    ok = re.fullmatch(r"Last landed by: `20\d\d-\d\d-\d\d-sitting-close-deltas-17-\d{3}`\.",
                      L[13] if len(L) > 13 else "") is not None
    return ok, "line 14 does not name a sitting-close-deltas-17 session in the base's form"


probe("header names this close", p_header)


# 2
def p_insertions():
    ins, why = walk_insertions()
    return ins is not None, why


probe("insertions only against the stamped base, line 14 apart", p_insertions, needs_base=True)

# new-block geometry
O002 = first(lambda l: l.startswith("Landed 2026-09-21, the continue-plan-002 sitting (master"), B009, S4)
O005 = first(lambda l: l.startswith("Landed 2026-09-21, the continue-plan-005 sitting (master"), B009, S4)


# 3
def p_blocks():
    if O002 is None or O005 is None:
        return False, "a block opener is missing after the 009 block"
    if not O002 < O005:
        return False, "the 005 block precedes the 002 block"
    later = [i for i in range(O005 + 1, S4) if L[i].startswith("Landed ")]
    if later:
        return False, "another Landed block follows the 005 block"
    return True, ""


probe("section 3 ends on the 002 block then the 005 block", p_blocks)


def probe_in_blocks(label, fn):
    if block_span("002") is None:
        results.append(("SKIP", label, "the block-geometry probe owns that finding"))
    else:
        probe(label, fn)


def block_span(which):
    if O002 is None or O005 is None or not O002 < O005:
        return None
    return (O002, O005) if which == "002" else (O005, S4)


# 4
def p_closing_bullets():
    want = ["- Sequencing for the next desk", "- Board deltas of this sitting's work:",
            "- Registry deltas of this sitting's work:"]
    for which in ("002", "005"):
        span = block_span(which)
        if span is None:
            return False, "blocks not found"
        tops = [L[i] for i in range(*span) if L[i].startswith("- ")]
        tail = tops[-3:]
        if len(tail) < 3 or not all(t.startswith(w) for t, w in zip(tail, want)):
            return False, "the %s block's last three top-level bullets" % which
    return True, ""


probe_in_blocks("each new block closes on sequencing, board deltas, registry deltas", p_closing_bullets)

STANDING = ("wave 10, then the 100 arc with its design sitting first, then 43, 45, S6; "
            "row 103 ongoing; row 93 stands")


# 5
def p_standing():
    for which in ("002", "005"):
        span = block_span(which)
        if span is None:
            return False, "blocks not found"
        if not any(STANDING in L[i] for i in range(*span)):
            return False, "not on one physical line in the %s block" % which
    return True, ""


probe_in_blocks("the standing line, verbatim on one physical line, in both new blocks", p_standing)

CONVENTION = ("Ratification debt carried forward, per convention: THIS close's notes.md "
              "queues to the following open.")


# 6
def p_convention():
    span = block_span("005")
    if span is None:
        return False, "blocks not found"
    return CONVENTION in collapse(L[span[0]:span[1]]), "not in the 005 block, whole"


probe_in_blocks("the 005 block's debt bullet carries the convention sentence, whole", p_convention)

SPLIT_MSG = ("applied, and I also ran into another issue while working on another project. "
             "The issue is described in the attached file. Let's tackle this now before the "
             "sitting close because it's important, unless you think it folds neatly into a "
             "queued session we'll run soon.")


# 7
def p_split_msg():
    span = block_span("005")
    if span is None:
        return False, "blocks not found"
    return any(SPLIT_MSG in L[i] for i in range(*span)), "not on one physical line in the 005 block"


probe_in_blocks("the operator's message that opened the fix, whole on one physical line, in the 005 block",
      p_split_msg)


def entry_end(start, hi):
    j = first(lambda l: l.startswith("- ") or (l and not l.startswith(" ")), start + 1, hi)
    return hi if j is None else j


# 8
def p_reg_brackets():
    a = [L[i].strip() for i in range(REG_114, entry_end(REG_114, S4))]
    b = [L[i].strip() for i in range(REG_EX2, entry_end(REG_EX2, S4))]
    if not any(s.startswith("[2026-09-21: closed at `2026-09-21-board-103-doc-lane-006`") for s in a):
        return False, "the 11.4 pointer entry"
    if not any(s.startswith("[2026-09-21: landed at `2026-09-21-split-transition-unconditional-007`")
               for s in b):
        return False, "the exit-2 rider entry"
    return True, ""


probe("registry: the 11.4 pointer entry and the exit-2 rider entry each carry their closing bracket",
      p_reg_brackets)

REG_NEW = [
    "- Close 16's Proposal 1, the bundle on an `opened` attempt:",
    "- Close 16's Proposal 2, the standing line's place in a master's brief:",
    "- The findings' §8 items 1 to 4, the two micros' sources:",
    "- The crafter seeds `forecast_departures`:",
    "- One statement of what each courier carries, for TARBALL.md §5.9:",
    "- TARBALL.md §7.5's exit codes bind the checkpoint script too:",
    "- Suite pins for the riders' two phrases:",
    "- Proposals of the `2026-09-21-continue-plan-002` and",
]


# 9
def p_reg_entries():
    tops = [L[i] for i in range(REG_OLD_LAST + 1, REG_END) if L[i].startswith("- ")]
    pos = -1
    for w in REG_NEW:
        hits = [k for k, t in enumerate(tops) if t.startswith(w)]
        if len(hits) != 1:
            return False, "opener found %d times: %s" % (len(hits), w)
        if hits[0] <= pos:
            return False, "out of order: " + w
        pos = hits[0]
    if not tops[-1].startswith(REG_NEW[-1]):
        return False, "the dispositions entry is not the last before the 2026-08-05 line"
    return True, ""


probe("registry: eight new entries in the pinned order, the dispositions entry last", p_reg_entries)

ROW103_MSG = (
    "as assumed, and I want to clarify that I want to change board 103 to an ongoing type of test "
    "instead of completing the arc with the open weight model. I don't have access to an open "
    "weight model just yet and i'm only using claude so let's drop that for now, I just want to "
    "eventually formalize this process because it was so effective. A later board for another "
    "time, just wanted to clarify all that. Reauthor close 16 if you need, I haven't packed yet")


# 10
def p_row103():
    span = range(ROW103, ROW104)
    if not any(L[i].strip().startswith("[2026-09-21:") for i in span):
        return False, "no 2026-09-21 bracket inside row 103"
    return any(ROW103_MSG in L[i] for i in span), "the message is not on one physical line in row 103"


probe("row 103 carries a 2026-09-21 bracket with the operator's message whole on one physical line",
      p_row103)


# 11
def p_rows():
    nums = [int(m.group(1)) for i in range(ROW113, S5)
            for m in [re.match(r"^(\d+)\. \*\*", L[i])] if m]
    return nums == list(range(113, 121)), "rows from 113 read %r" % (nums,)


probe("the board runs on from row 113 to row 120 and ends there", p_rows)


# 12
def p_home_bracket():
    return (any(L[i].strip().startswith("[2026-09-21: carried to PLANNER.md §4")
                for i in range(C_EX2_HOME + 1, C_SWEEP)),
            "no bracket between the Home sentence and the next contract")


probe("section 5: the exit-2 contract's home carries its 2026-09-21 bracket", p_home_bracket)


# 13
def p_s5_block():
    opens = [i for i in range(S5, S6) if L[i].startswith("New, ratified ")]
    if not opens or not L[opens[-1]].startswith("New, ratified 2026-09-21 ("):
        return False, "section 5's last New, ratified block is not dated 2026-09-21"
    return (any(L[i].startswith("- **The split is a role transition in every project.**")
                for i in range(opens[-1], S6)),
            "the contract's label is not in that block")


probe("section 5 ends on a 2026-09-21 block carrying the role-transition contract", p_s5_block)

E191_BRACKET = (
    "[2026-09-21: a negative landing per probe is the aim, not what that desk ran: at close 16 "
    "the `2026-09-21-continue-plan-002` desk ran thirteen negative runs for eighteen probes, "
    "which gave eleven probes a negative of their own and seven none.]")


# 14
def p_e191():
    return E191_BRACKET in collapse(L[E191:E192]), "not inside entry 191, whitespace-collapsed"


probe("entry 191 carries its ratified bracket, verbatim", p_e191)


# 15
def p_s6():
    nums = [int(m.group(1)) for i in range(E194, S7)
            for m in [re.match(r"^(\d+)\. \*\*", L[i])] if m]
    ok = len(nums) >= 2 and nums == list(range(194, 194 + len(nums)))
    return ok, "entries from 194 read %r" % (nums,)


probe("section 6 continues from entry 195 without gaps", p_s6)


# 16
def p_s7():
    nxt = first(lambda l: l.startswith("- "), ENV_LAST + 1, S8)
    if nxt is None:
        return False, "no bullet after the base's last"
    return L[nxt].startswith("- Version landmark: still 0.4.40"), "the first new bullet is not the landmark"


probe("section 7 ends on new bullets, the first the unchanged 0.4.40 landmark", p_s7)


# 17
def p_sids():
    import os
    ins, why = walk_insertions()
    if ins is None:
        return None
    bad = []
    for sid in sorted(set(SID_RE.findall("\n".join(ins)))):
        if sid in TOLERATED_SIDS or OWN_SID_RE.fullmatch(sid):
            continue
        if not os.path.isfile("claude/telemetry/%s.json" % sid):
            bad.append(sid)
    return not bad, "no record and no tolerance: %s" % ", ".join(bad)


def p_sids_wrapped():
    got = p_sids()
    if got is None:
        return True, ""
    return got


if base_lines is not None and walk_insertions()[0] is None:
    results.append(("SKIP", "every sid cited in the insertions has a record or a named tolerance",
                    "the insertions-only probe owns that finding"))
else:
    probe("every sid cited in the insertions has a record or a named tolerance",
          p_sids_wrapped, needs_base=True)

failed = 0
for state, label, detail in results:
    if state == "SKIP":
        print("[SKIP] %s: %s" % (label, detail))
    else:
        print("[%s] %s" % (state, label))
        if state == "FAIL":
            failed += 1
            if detail:
                print("  detail: " + detail)
sys.exit(1 if failed else 0)
PYEOF
