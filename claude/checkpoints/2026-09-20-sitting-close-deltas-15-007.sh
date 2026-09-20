#!/usr/bin/env bash
# Blind checkpoint, sitting close 15, v1. Authored by the master
# 2026-09-20-continue-plan-006 from the request, before the landing
# exists. Reads claude/MASTER.md (and claude/telemetry/ names) only;
# writes nothing.
#
# Verdict grammar: "[PASS] label" / "[FAIL] label" / "[SKIP] label", the
# label alone on the verdict line; detail on a following "  detail:"
# line. Exit 0 pass, 1 a probe failed, 2 the oracle could not run (an
# anchor it locates by is gone).
set -u
exec python3 -B - "$@" <<'PY'
import hashlib
import re
import subprocess
import sys
from pathlib import Path

DOC = Path("claude/MASTER.md")
BASE_SHA256 = "77efdd476c605bb4f87f6faa39e607222bcd9948a64830df950f2ab4e4fb8583"
if not DOC.is_file():
    print("ORACLE ERROR: claude/MASTER.md missing")
    sys.exit(2)
L = DOC.read_text(encoding="utf-8").split("\n")
results = []


def verdict(ok, label, detail=""):
    results.append(("PASS" if ok else "FAIL", label, detail))


def skip(label, detail):
    results.append(("SKIP", label, detail))


def anchor(prefix, start=0, end=None):
    """Index of the ONE line in [start, end) opening with prefix."""
    hits = [i for i in range(start, len(L) if end is None else end)
            if L[i].startswith(prefix)]
    if len(hits) != 1:
        print(f"ORACLE ERROR: anchor {prefix!r} found {len(hits)} times")
        sys.exit(2)
    return hits[0]


def first(prefix, start, end):
    for i in range(start, end):
        if L[i].startswith(prefix):
            return i
    return None


def count(prefix, start, end):
    return sum(1 for i in range(start, end) if L[i].startswith(prefix))


def collapse(start, end):
    return " ".join(" ".join(L[start:end]).split())


# --- anchors -----------------------------------------------------------
S3 = anchor("## 3. In flight")
S4 = anchor("## 4. The board")
S5 = anchor("## 5. Contracts established")
S6 = anchor("## 6. Orchestration-doctrine evidence pile")
S7 = anchor("## 7. Standing environment facts")
S8 = anchor("## 8. Foundation-audit findings register")
REG_END = anchor("Landed 2026-08-05, non-board (`2026-08-05-auto-sweep-009`):")
B009 = anchor("Landed 2026-09-19, the continue-plan-009 sitting (master", S3, S4)
LAST_DISPO = anchor("- Proposals of the `2026-09-19-continue-plan-009` "
                    "sitting's workers", S3, REG_END)
R37 = anchor("37. **Bail-mechanism recalibration**", S4, S5)
R38 = anchor("38. **", S4, S5)
R99 = anchor("99. **Outward-facing doc refresh**", S4, S5)
R100 = anchor("100. **", S4, S5)
R104 = anchor("104. **Session kinds, switchable; the context pack**", S4, S5)
R105 = anchor("105. **", S4, S5)
R113 = anchor("113. **", S4, S5)
RULING = anchor("- **Bailout-vs-compaction calibration ruling", S5, S6)
N0919 = anchor("New, ratified 2026-09-19 (", S5, S6)
E176 = anchor("176. **Close responses whose claims went unreconciled.**",
              S6, S7)
GATE = anchor("- The desk's in-process gate check:", S7, S8)

# --- 1. the header line --------------------------------------------------
verdict(len(L) > 13 and re.fullmatch(
    r"Last landed by: `20\d\d-\d\d-\d\d-sitting-close-deltas-15-\d{3}`\.",
    L[13]) is not None,
    "line 14 names this close as last landed, and nothing else",
    f"line 14: {L[13][:90]!r}" if len(L) > 13 else "short file")

# --- 2-4. the two blocks ---------------------------------------------------
b1 = first("Landed 2026-09-20, the continue-plan-001 sitting (master",
           B009 + 1, S4)
b2 = first("Landed 2026-09-20, the continue-plan-004 sitting (master",
           B009 + 1, S4)
verdict(b1 is not None and b2 is not None and b1 < b2,
        "§3 gains the continue-plan-001 block and then the "
        "continue-plan-004 block, after the 009 block and before §4",
        f"001 at {b1}, 004 at {b2}")


def block_closes(start, end):
    if start is None:
        return False
    bd = first("- Board deltas of this sitting's work:", start, end)
    rd = first("- Registry deltas of this sitting's work:", start, end)
    if bd is None or rd is None or not bd < rd:
        return False
    # nothing but the registry bullet's own continuation lines after it
    return all(L[i].startswith("  ") or L[i] == ""
               for i in range(rd + 1, end))


verdict(block_closes(b1, b2 if b2 else S4),
        "the 001 block closes on board deltas, then registry deltas")
verdict(block_closes(b2, S4),
        "the 004 block closes on board deltas, then registry deltas")

rat = first("- Ratified at the `2026-09-20-continue-plan-006` desk:",
            b2 or S4, S4)
rat_text = ""
if rat is not None:
    end = rat + 1
    while end < S4 and (L[end].startswith("  ") or L[end] == ""):
        end += 1
    rat_text = collapse(rat, end)
verdict(rat is not None and '"as assumed"' in rat_text,
        "the 004 block records the 006 desk's light block with the "
        "operator's reply verbatim")
verdict(b2 is not None
        and '"as assumed, and both applied:"' in collapse(b2, S4),
        "the 004 block carries the reply to the 004 desk's own light "
        "block verbatim")

# --- 5-6. the registry -------------------------------------------------------
BR = "  [2026-09-20: "
want = [("consumed at ", 1, None), ("ride condition reworded", 1, 1),
        ("carrier now 104b", 3, 3), ("condition not met at 37", 1, 1)]
for opening, lo, hi in want:
    n = count(BR + opening, S3, REG_END)
    ok = n >= lo and (hi is None or n <= hi)
    verdict(ok, f"the §3 registry carries its '{opening.strip()}' "
                f"bracket(s) dated 2026-09-20",
            f"found {n}, wanted {lo}" + ("" if hi is None else f" to {hi}"))

new = [first(p, LAST_DISPO + 1, REG_END) for p in (
    "- 104a's Proposals 1 to 3",
    "- A context-pack line in `bale status`",
    "- Proposals of the `2026-09-20-continue-plan-001` and")]
ordered = all(i is not None for i in new) and new == sorted(new)
tail_ok = False
if ordered:
    # the dispositions entry runs to the registry's end
    tail_ok = all(L[i].startswith("  ") or L[i] == ""
                  for i in range(new[2] + 1, REG_END))
verdict(ordered and tail_ok,
        "three new registry entries end the list in the pinned order, "
        "directly before the 2026-08-05 line",
        f"positions {new}, registry ends at {REG_END}")

# --- 7. the board -------------------------------------------------------------
last37 = [i for i in range(R37, R38) if L[i].startswith("    [20")]
verdict(bool(last37) and L[last37[-1]].startswith(
    "    [2026-09-20: DONE at "
    "`2026-09-20-board-37-compaction-read-side-003`"),
    "row 37 ends on its 2026-09-20 DONE bracket")
verdict(count("    [2026-09-20: cut in two", R104, R105) == 1
        and "--context" in collapse(R104, R105).split("cut in two")[-1],
        "row 104 gains its cut-in-two bracket, naming the --context "
        "spelling")
verdict(count("    [2026-09-20: 99b's inputs grow", R99, R100) == 1,
        "row 99 gains its 99b-inputs bracket")
verdict(not any(re.match(r"11[4-9]\. \*\*|1[2-9]\d\. \*\*", L[i])
                for i in range(R113, S5)),
        "§4 still ends at row 113")

# --- 8. contracts --------------------------------------------------------------
rul_end = RULING + 1
while rul_end < S6 and L[rul_end] != "":
    rul_end += 1
fif_at = first("  [2026-09-20: the fifteen is a hand count", RULING, rul_end)
fif_text = collapse(fif_at, rul_end) if fif_at is not None else ""
verdict(fif_at is not None
        and re.search(r"\b7\b", fif_text) is not None
        and "206" in fif_text,
        "the calibration ruling's entry ends on its hand-count bracket, "
        "with the records' 7 of 206")
n20 = first("New, ratified 2026-09-20 (", N0919 + 1, S6)
c1 = c2 = None
if n20 is not None:
    c1 = first("- **The context pack is `bale pack --context`.**", n20, S6)
    c2 = first("- **`bale stats` counts compaction disclosures.**",
               n20, S6)
verdict(None not in (n20, c1, c2) and c1 < c2
        and first("New, ratified ", n20 + 1, S6) is None,
        "§5 ends on a New, ratified 2026-09-20 block with its two "
        "contracts in order")

# --- 9. evidence ------------------------------------------------------------------
nums = [int(m.group(1)) for i in range(E176 + 1, S7)
        for m in [re.match(r"(\d+)\. \*\*", L[i])] if m]
verdict(len(nums) >= 8 and nums == list(range(177, 177 + len(nums))),
        "§6 gains entries 177 through at least 184, numbered without "
        "gaps, ending the section",
        f"entry numbers after 176: {nums}")
e177 = first("177. **", E176, S7) or S7
verdict(count("    [2026-09-20: close 14 parsed", E176, e177) == 1,
        "entry 176 gains its close-14-parsed bracket")

# --- 10. environment facts -------------------------------------------------------
vl = first("- Version landmark: 0.4.39", GATE + 1, S8)
verdict(vl is not None,
        "§7 gains a version landmark bullet for 0.4.39 after the "
        "section's present last bullet")

# --- 11-12. against the authored base ---------------------------------------------
base = None
try:
    r = subprocess.run(["git", "show", "HEAD:claude/MASTER.md"],
                       stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                       timeout=60)
    if r.returncode == 0 and \
            hashlib.sha256(r.stdout).hexdigest() == BASE_SHA256:
        base = r.stdout.decode("utf-8").split("\n")
except (OSError, subprocess.SubprocessError):
    base = None

LBL_INS = "every base line but line 14 survives, in order (insertions only)"
LBL_SID = ("every session id cited on an inserted line has a telemetry "
           "record, this close and the 006 master aside")
if base is None:
    why = "HEAD:claude/MASTER.md is not the authored base (or no git here)"
    skip(LBL_INS, why)
    skip(LBL_SID, why)
else:
    j = 0
    inserted = []
    lost = None
    for k, line in enumerate(base):
        if k == 13:
            continue
        while j < len(L) and L[j] != line:
            if j != 13:
                inserted.append(L[j])
            j += 1
        if j >= len(L):
            lost = k + 1
            break
        j += 1
    inserted += [x for n, x in enumerate(L[j:], j) if n != 13]
    verdict(lost is None, LBL_INS,
            f"base line {lost} has no match at or after its place")
    if lost is not None:
        skip(LBL_SID, "the inserted-line set is unreliable once a base "
                      "line is lost")
        base = None
if base is not None:
    sid_re = re.compile(r"20\d\d-\d\d-\d\d-[a-z0-9]+(?:-[a-z0-9]+)*-\d{3}(?![a-z0-9])")
    cited = set()
    for x in inserted:
        cited.update(sid_re.findall(x))
    tolerated = {s for s in cited
                 if re.fullmatch(r".*-sitting-close-deltas-15-\d{3}", s)}
    tolerated.add("2026-09-20-continue-plan-006")
    missing = sorted(s for s in cited - tolerated
                     if not Path("claude/telemetry", s + ".json").is_file())
    verdict(not missing, LBL_SID, f"no record for: {missing}")

failed = 0
for v, label, detail in results:
    print(f"[{v}] {label}")
    if detail and v != "PASS":
        print(f"  detail: {detail}")
    failed += v == "FAIL"
print(f"{sum(v == 'PASS' for v, _, _ in results)} of {len(results)} "
      f"probes passed")
sys.exit(1 if failed else 0)
PY
