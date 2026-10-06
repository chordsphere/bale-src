#!/usr/bin/env bash
# Blind checkpoint, sitting-close-deltas-22 (v1). Authored by the
# read-only desk 2026-10-06-friction-points-close-desk-002 from the
# request, before the work exists. Outcome-only, over claude/MASTER.md:
# the header, the bump's landing, the "seven keys" brackets and this
# close's stem in section 3, the desk's light block and the operator's
# reply in section 5, the routed Proposals in the ruling queue and the
# registry, the specimen on the WSL watch, section 6 entry 225, and
# sections 1, 2 and 8 as close 21's PASSed oracle left them. Pinned text is
# compared with all whitespace removed (and a line-leading '>' quote
# marker dropped): the brief allows re-wrapping, never rewording.
# Runs from the tree root; writes nothing.
# Exit 0: every probe passed. Exit 1: a probe failed (the work).
# Exit 2: the control failed or the oracle's own machinery broke.
set -u
export PYTHONDONTWRITEBYTECODE=1

python3 -B -I - "$PWD" <<'PYEOF'
import hashlib
import json
import re
import sys
from pathlib import Path

PINS = json.loads(r'''{
 "s5_block": [
  "Ratifyclose21-004'ssevenflaggeddecisionsasshipped,keepingitsrow-99bracketand§7bullet,withnobracketon§5's\"recordedbythenextclose\"line?",
  "reviewingclose21'sratificationrelay",
  "yes:allsevenasshipped,bothoptionalblockskept,no§5bracket;recordedatclose22",
  "ratifyingaworker'sflaggeddecisionsisyours,andtwoofitsblockswentpastthebrief'soutcomes",
  "Ratifybump-0-4-46-003asshipped:rowsforalleightsessionsdescribing0.4.46endstate,testrowskept,norowsforREADME.mdorbale-internals.md?",
  "reviewingthebump'sratificationrelay",
  "yes:allasshipped;C's\"eightkeys\"(seveninthebytes)getsadatedbracketatclose22,neveranedit",
  "thefourextrasessionswerethedesk'sread,notyourruling,andtheend-stateruleistheworker'sown",
  "Routethebump'stwoProposals:theCODE.md8.5bumpnudgetotherulingqueue,andtherecord-as-99b-checklistintothe99broutingentry?",
  "routingbump-0-4-46-003'sProposals",
  "yes:thenudgewaitsonarulingbecauseitchangeshowforecastsareauthored;thechecklistrides99b",
  "thenudgeaddsanapply-timesurfaceorapackingrule,whichisascopedecision"
 ],
 "reply": "asassumed,butdon'tweneedanupwardreport?",
 "rq": "acheckin`tests/test_changelog_record.py`thataversion'srecordexistswhenevercodeunder`bin/`or`tools/`changes",
 "reg": "theBALE.md99btrue-upcouldcitethisrecordasitschecklist.",
 "watch": "ΓÇö"
}''')
HASHES = json.loads(r'''{
 "s12": "a7e4b36c85a7facfb097ba75b0cb40ee990db2735cfc994b776634889c26fc3e",
 "s8": "516494622b09fa5def73dbc5ea6d124cbc7def18f7f3674f6698a23e89d5871f"
}''')

root = Path(sys.argv[1])
failed = []


def say(ok, label, why=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + ("" if ok else f": {why}"))
    if not ok:
        failed.append(label)


def flat(lines):
    """Whitespace-free text of `lines`, a leading '>' quote marker dropped
    from each line first."""
    return re.sub(r"\s+", "", "\n".join(re.sub(r"^\s*>", "", l) for l in lines))


def missing(haystack_lines, needles):
    hay = flat(haystack_lines)
    return [n for n in needles if n not in hay]


# --- control: the comparison and the hash this oracle leans on work ---
try:
    probe_lines = ["> alpha `beta`", "  gamma: delta,", "epsilon."]
    assert missing(probe_lines, ["alpha`beta`gamma:delta,epsilon."]) == []
    assert missing(probe_lines, ["alpha`beta`gamma:delta;epsilon."]) != []
    assert len(PINS["s5_block"]) == 12
except Exception as e:
    print(f"[CONTROL] comparison control failed: {e!r}")
    sys.exit(20)
print("[CONTROL] the whitespace-free comparison finds a planted string and misses an altered one")

path = root / "claude" / "MASTER.md"
try:
    text = path.read_text(encoding="utf-8")
except Exception as e:
    say(False, "claude/MASTER.md is readable UTF-8", repr(e))
    sys.exit(10)
lines = text.split("\n")


def find(prefix):
    hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
    return hits[0] if len(hits) == 1 else None


anchors = {k: find(v) for k, v in {
    "s1": "## 1. ", "s3": "## 3. ", "s4": "## 4. ", "s5": "## 5. ",
    "s6": "## 6. ", "s7": "## 7. ", "s8": "## 8. ",
    "watches": "**Watches** (named re-triggers, no work;",
    "rq": "**Ruling queue** (desk rulings awaiting a future sitting",
    "reg": "**Fold-in registry** (one home, this list",
    "landed": "Landed 2026-08-05, non-board (`2026-08-05-auto-sweep-009`):",
}.items()}
bad = [k for k, v in anchors.items() if v is None]
order = ["s1", "s3", "watches", "rq", "reg", "landed", "s4", "s5", "s6", "s7", "s8"]
in_order = not bad and all(anchors[a] < anchors[b] for a, b in zip(order, order[1:]))
say(in_order, "section anchors present once each, in order",
    f"missing or repeated {bad}" if bad else "out of order")
if not in_order:
    sys.exit(10)
A = anchors

# --- 1. header ---
heads = [l for l in lines if l.startswith("Last landed by:")]
say(len(heads) == 1 and re.fullmatch(
        r"Last landed by: `\d{4}-\d{2}-\d{2}-sitting-close-deltas-22-\d{3}`\.",
        heads[0]) is not None,
    "the header names this close's session, once", f"reads {heads}")

# --- 2. sections 1, 2 and 8 untouched ---
s12 = "\n".join(lines[A["s1"]:A["s3"]])
s8 = "\n".join(lines[A["s8"]:])
say(hashlib.sha256(s12.encode()).hexdigest() == HASHES["s12"],
    "sections 1 and 2 unchanged", "bytes differ from close 21's tree")
say(hashlib.sha256(s8.encode()).hexdigest() == HASHES["s8"],
    "section 8 unchanged", "bytes differ from close 21's tree")

# --- 3. section 3: the bump's landing, the seven-keys brackets, this close's stem ---
s3text = "\n".join(lines[A["s3"]:A["s4"]])
need3 = ["2026-10-06-bump-0-4-46-003", "suggest_wizard_values",
         "2026-10-06-sitting-close-deltas-22"]
gone = [n for n in need3 if n not in s3text]
say(not gone, "section 3 names the bump's session, suggest_wizard_values and this close's stem",
    f"absent: {gone}")

# --- 4. section 5: the light block and the operator's reply, verbatim ---
s5 = lines[A["s5"]:A["s6"]]
miss = missing(s5, PINS["s5_block"])
say(not miss, "section 5 carries the desk's light block verbatim",
    f"{len(miss)} of 12 field values absent, first: {miss[:1]}")
say(not missing(s5, [PINS["reply"]]), "section 5 carries the operator's reply verbatim",
    "absent")

# --- 5. section 6 numbering and entry 225 ---
s6 = lines[A["s6"]:A["s7"]]
ents = [(i, int(m.group(1))) for i, l in enumerate(s6)
        for m in [re.match(r"^(\d+)\. \*\*", l)] if m]
nums = [n for _, n in ents]
contiguous = bool(nums) and nums == list(range(nums[0], nums[0] + len(nums)))
say(contiguous and nums[0] == 10 and nums[-1] >= 225,
    "section 6 entries run contiguous from 10 through at least 225",
    f"first {nums[:1]}, last {nums[-1:]}, contiguous {contiguous}")
e225 = None
for k, (i, n) in enumerate(ents):
    if n == 225:
        end = ents[k + 1][0] if k + 1 < len(ents) else len(s6)
        e225 = "\n".join(s6[i:end])
say(e225 is not None and "bin/bale_report.py" in e225,
    "entry 225 names bin/bale_report.py", "no entry 225, or it does not name the file")

# --- 6. ruling queue ---
rq = lines[A["rq"]:A["reg"]]
top = sum(1 for l in rq if l.startswith("- "))
say(top >= 6, "the ruling queue holds at least six entries", f"holds {top}")
say(not missing(rq, [PINS["rq"]]),
    "the ruling queue carries the bump's first Proposal verbatim", "absent")

# --- 7. registry ---
reg = lines[A["reg"]:A["landed"]]
say(not missing(reg, [PINS["reg"]]),
    "the registry carries the bump's second Proposal verbatim", "absent")

# --- 8. the WSL watch's specimen ---
wt = "\n".join(lines[A["watches"]:A["rq"]])
say(PINS["watch"] in wt, "the watches quote the mangled-paste specimen", "absent")

sys.exit(10 if failed else 0)
PYEOF
rc=$?
# The interpreter's own exits are 0 (pass), 10 (a probe failed) and 20
# (the control failed); anything else, a traceback's 1 included, is the
# oracle breaking, never a verdict on the work.
case "$rc" in
  0) exit 0 ;;
  10) exit 1 ;;
  20) exit 2 ;;
  *) echo "[CONTROL] the oracle's interpreter exited $rc unexpectedly"; exit 2 ;;
esac
