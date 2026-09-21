#!/usr/bin/env bash
# Blind checkpoint, sitting close 16 (claude/MASTER.md only). v1.
# Authored 2026-09-21 at the master 2026-09-21-continue-plan-002, from the
# request, before any landing existed. Runs from the repo root (staging).
# Reads claude/MASTER.md, claude/telemetry/ and `git show HEAD:`; writes
# nothing. Exit 0 every probe passed or skipped by name, 1 a probe failed,
# 2 the control block failed (a defective oracle or an unexpected tree).
# A verdict line carries the label alone; detail sits on the line after it.
set -u
exec python3 -B - "$@" <<'PY'
import hashlib
import re
import subprocess
import sys
from pathlib import Path

TARGET = Path("claude/MASTER.md")
TELEMETRY = Path("claude/telemetry")
BASE_SHA256 = "e5b80f830785c8718a01e98cd4107280992591bb13f99fabb672431ba363dcfc"
AUTHORING_DESK = "2026-09-21-continue-plan-002"
SID_104B = "2026-09-20-board-104b-pack-telemetry-008"

results = []  # (state, label, detail)


def verdict(state, label, detail=""):
    results.append(state)
    print(f"[{state}] {label}")
    if detail:
        print(f"  detail: {detail}")


def control_fail(why):
    print("[FAIL] control")
    print(f"  detail: {why}; the oracle's own footing is missing and no probe ran")
    sys.exit(2)


# ---------------------------------------------------------------- control
if not TARGET.is_file():
    control_fail("claude/MASTER.md is not a file here")
try:
    text = TARGET.read_text(encoding="utf-8")
except (OSError, UnicodeDecodeError) as exc:
    control_fail(f"claude/MASTER.md unreadable ({exc.__class__.__name__})")
lines = text.split("\n")

# Anchors: lines of the authored base the probes locate by. Each must open
# exactly one physical line of the file under test.
ANCHORS = {
    "s3": "## 3. In flight",
    "registry": "**Fold-in registry** (one home, this list",
    "reg_sweep_key": "- Pack-json `sweep`/`include_group` key: named and deferred at 47a",
    "reg_pin_105": "- A suite-level pin that `tools/craft_response.py` and",
    "reg_packed_at": "- `packed_at` on a pack's `opened` telemetry attempt: accepted at the",
    "reg_closing_sid": "- The closing pack's sid on a swept or superseded attempt: accepted at",
    "reg_104a_props": "- 104a's Proposals 1 to 3: accepted at the",
    "reg_last_base": "- Proposals of the `2026-09-20-continue-plan-001` and",
    "reg_end": "Landed 2026-08-05, non-board (",
    "block_004": "Landed 2026-09-20, the continue-plan-004 sitting (master",
    "s4": "## 4. The board",
    "row_103": "103. **Cross-model capability probe**",
    "row_104": "104. **Session kinds, switchable; the context pack**",
    "row_105": "105. **Operator-voice authority framing**",
    "row_113": "113. **Every suite's dotted run form**",
    "s5": "## 5. Contracts established (do not re-litigate casually)",
    "s5_block_15": "New, ratified 2026-09-20 (the `2026-09-20-continue-plan-004` and",
    "s6": "## 6. Orchestration-doctrine evidence pile",
    "entry_187": "187. **An attempt no desk's account mentions.**",
    "s7": "## 7. Standing environment facts",
    "s7_last_base": "- A range in a core-first doc is bounded by line numbers from a heading",
    "s8": "## 8. Foundation-audit findings register",
}
ORDER = list(ANCHORS)  # the base's own order, top to bottom
at = {}
for key, opener in ANCHORS.items():
    hits = [i for i, ln in enumerate(lines) if ln.startswith(opener)]
    if len(hits) != 1:
        control_fail(f"anchor '{opener[:48]}' opens {len(hits)} lines, wanted 1")
    at[key] = hits[0]
for a, b in zip(ORDER, ORDER[1:]):
    if not at[a] < at[b]:
        control_fail(f"anchors out of order: '{a}' is not above '{b}'")

SID_RE = re.compile(r"(?<![\w-])\d{4}-\d\d-\d\d-[a-z0-9-]+-\d{3}(?![\w-])")
_sid_selftest = {
    "`2026-09-20-board-103-probe-design-010`": ["2026-09-20-board-103-probe-design-010"],
    "2026-09-20-board-103-probe-design-r2.bale-bundle": [],
    "2026-09-20-board-104b-pack-telemetry beside": [],
    "response-2026-09-20-x-003 (1).tar.gz": [],
    "`applied/2026-09-20-x-003` at 2026-09-21T01:18:25Z": ["2026-09-20-x-003"],
}
for sample, want in _sid_selftest.items():
    if SID_RE.findall(sample) != want:
        control_fail("the session-id pattern failed its own self-test")

# The base, for the two base-relative probes. Absent or different, they
# SKIP by name: the oracle was authored against one base only.
base_lines = None
base_why = ""
try:
    shown = subprocess.run(["git", "show", "HEAD:claude/MASTER.md"],
                           capture_output=True, timeout=60)
    if shown.returncode != 0:
        base_why = "git show HEAD:claude/MASTER.md did not succeed"
    elif hashlib.sha256(shown.stdout).hexdigest() != BASE_SHA256:
        base_why = "HEAD:claude/MASTER.md is not the base this oracle was authored against"
    else:
        base_lines = shown.stdout.decode("utf-8").split("\n")
except (OSError, subprocess.SubprocessError) as exc:
    base_why = f"git unavailable ({exc.__class__.__name__})"

print("[PASS] control: anchors, order, and the session-id pattern")


def region(start_key, end_key):
    """(index, line) pairs strictly between two anchors."""
    return [(i, lines[i]) for i in range(at[start_key] + 1, at[end_key])]


def opens(ln, opener):
    return ln.startswith(opener)


# ----------------------------------------------------------------- probes
# 1. header
label = "line 14 names a close-16 session"
m = re.fullmatch(r"Last landed by: `(\d{4}-\d\d-\d\d-sitting-close-deltas-16-\d{3})`\.",
                 lines[13] if len(lines) > 13 else "")
own_sid = m.group(1) if m else None
verdict("PASS" if m else "FAIL", label,
        "" if m else "line 14 is not the whole pinned line with a sitting-close-deltas-16 sid")

# 2. insertions only
label = "insertions only against the authored base, but for line 14"
if base_lines is None:
    verdict("SKIP", label, base_why)
else:
    have = list(lines)
    want = list(base_lines)
    if len(have) > 13 and len(want) > 13:
        have[13] = want[13] = "<line 14>"
    ptr = 0
    for ln in have:
        if ptr < len(want) and ln == want[ptr]:
            ptr += 1
    if ptr == len(want):
        verdict("PASS", label)
    else:
        verdict("FAIL", label,
                f"base line {ptr + 1} does not survive in order, byte for byte")

# 3. two blocks end section 3
label = "two blocks end section 3, 006 then 009"
PIN_006 = "Landed 2026-09-20, the continue-plan-006 sitting (master"
PIN_009 = "Landed 2026-09-20, the continue-plan-009 sitting (master"
tail3 = region("block_004", "s4")
block_opens = [(i, ln) for i, ln in tail3 if ln.startswith("Landed ")]
ok3 = (len(block_opens) == 2 and opens(block_opens[0][1], PIN_006)
       and opens(block_opens[1][1], PIN_009))
verdict("PASS" if ok3 else "FAIL", label,
        "" if ok3 else f"{len(block_opens)} block opening(s) after the 004 block, "
                       "wanted the two pinned ones in order")


def block_region(pin):
    """A block's lines, found by its own pinned opener, so a fault in one
    block (or in the order) does not fail the other block's probes."""
    starts = [i for i, ln in tail3 if opens(ln, pin)]
    if len(starts) != 1:
        return None
    later = [i for i, ln in block_opens if i > starts[0]]
    end = later[0] if later else at["s4"]
    return [(i, lines[i]) for i in range(starts[0], end)]


r006 = block_region(PIN_006)
r009 = block_region(PIN_009)
NEEDS_BLOCK = "this block's pinned opening line was not found after the 004 block"

# 4. block closings
label = "each new block closes on sequencing, board deltas, registry deltas"
CLOSERS = ["- Sequencing for the next desk",
           "- Board deltas of this sitting's work:",
           "- Registry deltas of this sitting's work:"]
if r006 is None and r009 is None:
    verdict("FAIL", label, "neither block's pinned opening line was found after the 004 block")
else:
    bad = []
    for name, reg in (("006", r006), ("009", r009)):
        if reg is None:
            bad.append(name)
            continue
        bullets = [ln for _, ln in reg if ln.startswith("- ")]
        last3 = bullets[-3:]
        if len(last3) != 3 or not all(opens(b, c) for b, c in zip(last3, CLOSERS)):
            bad.append(name)
    verdict("FAIL" if bad else "PASS", label,
            f"block(s) {', '.join(bad)}: the last three bullets are not the pinned three in order"
            if bad else "")

# 5. 006 block's ratified-at bullet
label = "the 006 block carries its ratified-at-the-009-desk bullet"
if r006 is None:
    verdict("FAIL", label, NEEDS_BLOCK)
else:
    ok = any(opens(ln, "- Ratified at the `2026-09-20-continue-plan-009` desk:") for _, ln in r006)
    verdict("PASS" if ok else "FAIL", label, "" if ok else "no line of the block opens with the pinned bullet")

# 6. operator's three messages
label = "the 009 block carries the operator's three messages, each on one line"
MESSAGES = [
    '"ratify the outstanding questions"',
    '"as assumed, still waiting on 104b and close 15 to finish"',
    "\"i haven't opened the 103 bundle so reauthor, and closing is fine, i'll append my 103 "
    "notes to the opening of the next master. Otherwise, as assumed\"",
]
if r009 is None:
    verdict("FAIL", label, NEEDS_BLOCK)
else:
    missing = [n + 1 for n, msg in enumerate(MESSAGES) if not any(msg in ln for _, ln in r009)]
    verdict("FAIL" if missing else "PASS", label,
            f"message(s) {missing} of three not found whole on one physical line" if missing else "")

# 7. convention sentence
label = "the 009 block's debt bullet closes on the convention sentence"
CONVENTION = ("  Ratification debt carried forward, per convention: THIS close's "
              "notes.md queues to the following open.")
if r009 is None:
    verdict("FAIL", label, NEEDS_BLOCK)
else:
    ok = any(ln == CONVENTION for _, ln in r009)
    verdict("PASS" if ok else "FAIL", label, "" if ok else "the whole pinned line is not in the block")

# 8. registry brackets
label = "five registry entries carry a consumed-at-104b bracket"
BRACKET = f"  [2026-09-20: consumed at `{SID_104B}`"
missing = []
for key in ("reg_sweep_key", "reg_pin_105", "reg_packed_at", "reg_closing_sid", "reg_104a_props"):
    i = at[key] + 1
    found = False
    while i < len(lines) and lines[i].startswith("  "):
        if opens(lines[i], BRACKET):
            found = True
        i += 1
    if not found:
        missing.append(ANCHORS[key][2:34])
verdict("FAIL" if missing else "PASS", label,
        "no pinned bracket inside: " + " | ".join(missing) if missing else "")

# 9. six new registry entries
label = "the registry ends on the six pinned entries, in order"
NEW_ENTRIES = [
    "- A cause on a `rejected` attempt:",
    "- A `swept_by` line in the `bale stats` dossier:",
    "- The cap/breach loop in `bin/bale_pack.py`:",
    "- The `docs/CLAUDE.md` §11.4 pointer:",
    "- A failed oracle control exits 2, for PLANNER.md §4:",
    "- Proposals of the `2026-09-20-continue-plan-006` and",
]
reg_tail = region("reg_last_base", "reg_end")
tail_bullets = [ln for _, ln in reg_tail if ln.startswith("- ")]
stray = [i + 1 for i, ln in reg_tail if not (ln.startswith("- ") or ln.startswith("  "))]
ok9 = (len(tail_bullets) >= 6
       and all(opens(b, p) for b, p in zip(tail_bullets[-6:], NEW_ENTRIES)) and not stray)
detail9 = ""
if not ok9:
    detail9 = (f"{len(tail_bullets)} entries follow the base's last one; wanted the list to end on "
               "the six pinned openers in order, with only entry lines before the 2026-08-05 line")
verdict("PASS" if ok9 else "FAIL", label, detail9)

# 10. row 104
label = "row 104 ends on its 104b DONE bracket"
row104 = region("row_104", "row_105")
brackets = [ln for _, ln in row104 if ln.startswith("    [")]
nonblank = [ln for _, ln in row104 if ln.strip()]
ok = (bool(brackets) and opens(brackets[-1], f"    [2026-09-20: 104b DONE at `{SID_104B}`")
      and bool(nonblank) and nonblank[-1].rstrip().endswith("]"))
verdict("PASS" if ok else "FAIL", label,
        "" if ok else "the row's last bracket is not the pinned one, or the row does not end on it")

# 11. row 103
label = "row 103 carries the design-sitting bracket"
ok = any(opens(ln, "    [2026-09-20: the design sitting's bundle was authored at the")
         for _, ln in region("row_103", "row_104"))
verdict("PASS" if ok else "FAIL", label, "" if ok else "no line of the row opens with the pinned bracket")

# 12. board end
label = "the board still ends at row 113"
rows = [int(m.group(1)) for _, ln in region("s4", "s5")
        for m in [re.match(r"(\d+)\. \*\*", ln)] if m]
ok = bool(rows) and rows[-1] == 113 and max(rows) == 113
verdict("PASS" if ok else "FAIL", label, "" if ok else "a row numbered past 113, or 113 is not last")

# 13, 14. section 5
label13 = "section 5 ends on the 009 desk's block"
label14 = "the new section 5 block opens on its two contracts, in order"
s5_tail = region("s5_block_15", "s6")
news = [(i, ln) for i, ln in s5_tail if ln.startswith("New, ratified ")]
ok13 = bool(news) and opens(news[-1][1], "New, ratified 2026-09-20 (the `2026-09-20-continue-plan-009` desk")
verdict("PASS" if ok13 else "FAIL", label13,
        "" if ok13 else "the last 'New, ratified' block of the section is not the pinned one")
if not ok13:
    verdict("FAIL", label14, "the block was not found (see the probe above)")
else:
    bolds = [lines[i] for i in range(news[-1][0], at["s6"]) if lines[i].startswith("- **")]
    ok14 = (len(bolds) >= 2 and opens(bolds[0], "- **A failed oracle control exits 2.**")
            and opens(bolds[1], "- **A pack records what it swept, and when it was packed.**"))
    verdict("PASS" if ok14 else "FAIL", label14,
            "" if ok14 else "the block's first two bullets are not the pinned two in order")

# 15, 16. section 6
entries = [(i, int(m.group(1))) for i, ln in region("s6", "s7")
           for m in [re.match(r"(\d+)\. \*\*", ln)] if m]
label = "entry 187 carries the 009 desk's bracket"
after187 = [i for i, n in entries if i > at["entry_187"]]
end187 = after187[0] if after187 else at["s7"]
ok = any(opens(lines[i], "    [2026-09-20: the 009 desk's read of 37's record:")
         for i in range(at["entry_187"] + 1, end187))
verdict("PASS" if ok else "FAIL", label, "" if ok else "no line inside entry 187 opens with the pinned bracket")

label = "entries 188 onward end section 6 without gaps, through at least 193"
new_numbers = [n for i, n in entries if i > at["entry_187"]]
ok = (len(new_numbers) >= 6 and new_numbers == list(range(188, 188 + len(new_numbers))))
verdict("PASS" if ok else "FAIL", label,
        "" if ok else f"after entry 187 the section numbers {new_numbers[:12]}")

# 17. section 7
label = "section 7 ends past its 0.4.40 landmark"
landmarks = [(i, ln) for i, ln in region("s7", "s8") if ln.startswith("- Version landmark:")]
ok = (bool(landmarks) and landmarks[-1][0] > at["s7_last_base"]
      and opens(landmarks[-1][1], f"- Version landmark: 0.4.40 (`{SID_104B}`)"))
verdict("PASS" if ok else "FAIL", label,
        "" if ok else "the section's last version landmark is not the pinned one, after the base's last bullet")

# 18. cited session ids
label = "every session id on an inserted line has a telemetry record"
if base_lines is None:
    verdict("SKIP", label, base_why)
else:
    known = {p.stem for p in TELEMETRY.glob("*.json")} if TELEMETRY.is_dir() else set()
    known.add(AUTHORING_DESK)
    OWN_RE = re.compile(r"\d{4}-\d\d-\d\d-sitting-close-deltas-16-\d{3}")
    base_set = set(base_lines)
    unknown = []
    for n, ln in enumerate(lines, 1):
        if n == 14 or ln in base_set:
            continue
        for sid in SID_RE.findall(ln):
            if sid not in known and not OWN_RE.fullmatch(sid) and sid not in unknown:
                unknown.append(sid)
    verdict("FAIL" if unknown else "PASS", label,
            "no record for: " + ", ".join(unknown[:6]) if unknown else "")

# ---------------------------------------------------------------- summary
failed = results.count("FAIL")
print(f"summary: {results.count('PASS')} passed, {failed} failed, {results.count('SKIP')} skipped")
sys.exit(1 if failed else 0)
PY
