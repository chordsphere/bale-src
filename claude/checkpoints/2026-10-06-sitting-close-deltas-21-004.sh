#!/usr/bin/env bash
# Blind checkpoint, sitting-close-deltas-21 (v1). Authored by the
# read-only desk 2026-10-06-friction-points-close-desk-002 from the
# request, before the work exists. Outcome-only, over claude/MASTER.md:
# the header, the landed sids and the cleanup desk's close in section 3,
# the two light blocks in section 5, board rows 134 and 135, the routed
# Proposals in the ruling queue and the registry, the new watch, section
# 6 entry 224, and sections 1, 2 and 8 untouched. Pinned text is
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
 "s5_block2": [
  "Ratifyasshippedeveryflaggeddecisionoflog-hold-003(five)andsitting-close-deltas-20-001(seven),keepingclose20'sextrasection7bullet?",
  "reviewingthelog-holdandclose-20ratificationrelays",
  "yes:alltwelveasshipped,recordedatclose21",
  "ratifyingaworker'sflaggeddecisionsisyours;log-holdnarrowedthewraptopack'spre-walklines,andclose20askedaboutthesection7bullet",
  "Filelog-hold'stwowrapProposalsasaruling-queueentry(everyverb's[bale]lines)andaregistryrider(thesupersession,drift-admissionandbare-applyy/Nprompts)?",
  "routinglog-hold-003'sProposals",
  "yes:theevery-verbwrapwaitsonarulingbecauseitbreaks18ptyassertions;they/Nkeywordislayoutonlyandridesthenextsessiontouchingbale_pack.pyandbale_apply.py",
  "yourrulingcoveredonlythesweep'sprompt,andwrappingeveryverbchangesallterminaloutput",
  "Makeclose20'stwoProposalsboardrows:apack-timeincludewarningforreadsashippedsuiteneeds,andsurfacingreconciliation_parsedfalseatapplyandinstats?",
  "routingsitting-close-deltas-20-001'sProposals",
  "yes:twoboardrows,warningsonly,neverrefusals;queuedafterchoice-prompt-convergence",
  "eachaddsanewwarningsurfacetobale,whichisascopedecision"
 ],
 "s5_block4": [
  "Ratifyasshippedclipboard-key-rename-002'seightdecisionsandchoice-prompt-convergence-001'sseven,includingconvergencemovingpack'sper-pathfilterchainintopack_drop_reason?",
  "reviewingtherenameandconvergenceratificationrelays",
  "yes:allfifteenasshipped,recordedatclose21",
  "ratifyingaworker'sflaggeddecisionsisyours,andthefilter-chainrefactorrunsinsideeverypack",
  "Authoraversion-bumpmicro-session(0.4.46)besideclose21,writingthechangelogrecordforthearc'ssurfacechanges(C,D,log-hold,therename)?",
  "routingclipboard-key-rename-002'schangelogProposal(lightblock3,unanswered,foldedinhere)",
  "yes:bin/VERSIONplusclaude/changelog/0.4.46.json,authoredbythesuccessordeskbesideclose21",
  "CODE.md8.5putstheentryinthechangingsession,thearc'ssessionsskippedit,andcatchingupmintsaversion",
  "Fileconvergence'sremainingProposals:droppingtwopickerexceptionsandmovingthe.baleignoreaddpromptontoask_choiceasruling-queueentries,andPackWalkasaWalkconfigurationasaregistryrider?",
  "routingchoice-prompt-convergence-001'sProposals",
  "yes:thefirsttwochangewhatananswerorafrozenpromptsays,sotheywaitonrulings;theWalkrefactorchangesnothingvisible",
  "droppingthepickerexceptionsreversesthisdesk'spin,andtheaddprompt'stextwasfrozenbytheconvergenceconstraint"
 ],
 "row134": "aboardrowforapack-timeincludewarning:whenanincludedsuite'smoduleimportsorfixturereads(`bale.toml`,`claude/changelog/`,`claude/context/adr/`,therepo`README.md`)falloutsidetherequest'sincludes,`balepack`saysso,neverrefuses.",
 "row135": "surface`reconciliation_parsed:false`atapplyasawarninglinebesidetheworkerPASS,andin`balestats`.",
 "rq": [
  "call`set_log_display_wrap(True)`oncein`main()`,soeveryverb's`[bale]`linesfittheterminal.",
  "makethepickerreadnumberswiththelayer'sASCII`pick_number`anddropthe`number`option.",
  "moveitsnumberedpicksonto`ask_choice`(`noun=\"suggestion\"`,`typed=\"apattern\"`)."
 ],
 "reg": [
  "pass`wrap=True`atthesupersession,drift-admissionandbare-applyprompts.",
  "givebin/bale'sloggingsectiontwosmallaccessorsforitsFORCEqueue:acount,andadrop-since-mark.",
  "give`Walk`ashrinkableplan(`drop`)andplain-wordsectionheadings,thenmakePackWalkaconfigurationofit.",
  "Fromthewalk'sfirstquestionthroughitsREADMEquestion,baleholdsits`[bale]`lines(bin/bale's`hold_log`/`release_log`):eachlineisjournaledwhenloggedandprintedaftertheREADMEquestion,inorder;arefusalprintstheheldlinesbeforeitserrorline.",
  "thekeyis`[clipboard]command`atbothlayers;`[probe]clipboard_command`isreadasalegacyalias,`[clipboard]command`winninginsideonefile",
  "§7.3'sdescriptionofthesession-shapeexchangeandthecheckpointpickershouldsaythatbothdrawconfiginit'salternatives."
 ],
 "watch": "bale'sparserseesthenewkeyandrefusesitsspelling(loud,nothingcopied,`balestatus`showsUNREADABLEwiththeremedy);thecrafter'sscancannotseedottedkeysatall,soitsno-balefallbackwouldteeinto`y`."
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
    assert len(PINS["s5_block2"]) == 12 and len(PINS["s5_block4"]) == 12
    assert len(PINS["rq"]) == 3 and len(PINS["reg"]) == 6
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
        r"Last landed by: `\d{4}-\d{2}-\d{2}-sitting-close-deltas-21-\d{3}`\.",
        heads[0]) is not None,
    "the header names this close's session, once", f"reads {heads}")

# --- 2. sections 1, 2 and 8 untouched ---
s12 = "\n".join(lines[A["s1"]:A["s3"]])
s8 = "\n".join(lines[A["s8"]:])
say(hashlib.sha256(s12.encode()).hexdigest() == HASHES["s12"],
    "sections 1 and 2 unchanged", "bytes differ from the base")
say(hashlib.sha256(s8.encode()).hexdigest() == HASHES["s8"],
    "section 8 unchanged", "bytes differ from the base")

# --- 3. section 3 records the landings, the close, this desk, the bump ---
s3 = lines[A["s3"]:A["s4"]]
need3 = ["2026-10-05-clipboard-key-rename-002",
         "2026-10-06-choice-prompt-convergence-001",
         "2026-10-06-friction-points-close-desk-002",
         "19:11:36",
         "2026-10-06-bump-0-4-46"]
s3text = "\n".join(s3)
gone = [n for n in need3 if n not in s3text]
say(not gone, "section 3 names the landed sessions, the cleanup desk's close time, this desk and the bump",
    f"absent: {gone}")

# --- 4. section 5 carries blocks 2 and 4 verbatim ---
s5 = lines[A["s5"]:A["s6"]]
for key, label in (("s5_block2", "block 2"), ("s5_block4", "block 4")):
    miss = missing(s5, PINS[key])
    say(not miss, f"section 5 carries the cleanup desk's {label} verbatim",
        f"{len(miss)} of 12 field values absent, first: {miss[:1]}")

# --- 5. board rows 134 and 135 ---
s4 = lines[A["s4"]:A["s5"]]
rows = [(i, int(m.group(1))) for i, l in enumerate(s4)
        for m in [re.match(r"^(\d+)[a-z]?\. \*\*", l)] if m]


def row_span(n):
    for k, (i, num) in enumerate(rows):
        if num == n:
            end = rows[k + 1][0] if k + 1 < len(rows) else len(s4)
            return s4[i:end]
    return None


for n, key in ((134, "row134"), (135, "row135")):
    span = row_span(n)
    say(span is not None and not missing(span, [PINS[key]]),
        f"board row {n} carries close 20's Proposal verbatim",
        "no such row" if span is None else "the Proposal's text is absent from the row")

# --- 6. section 6 numbering and entry 224 ---
s6 = lines[A["s6"]:A["s7"]]
ents = [(i, int(m.group(1))) for i, l in enumerate(s6)
        for m in [re.match(r"^(\d+)\. \*\*", l)] if m]
nums = [n for _, n in ents]
contiguous = bool(nums) and nums == list(range(nums[0], nums[0] + len(nums)))
say(contiguous and nums[0] == 10 and nums[-1] >= 224,
    "section 6 entries run contiguous from 10 through at least 224",
    f"first {nums[:1]}, last {nums[-1:]}, contiguous {contiguous}")
e224 = None
for k, (i, n) in enumerate(ents):
    if n == 224:
        end = ents[k + 1][0] if k + 1 < len(ents) else len(s6)
        e224 = "\n".join(s6[i:end])
say(e224 is not None and "CODE.md" in e224 and "8.5" in e224,
    "entry 224 cites CODE.md section 8.5", "no entry 224, or no such citation in it")

# --- 7. ruling queue ---
rq = lines[A["rq"]:A["reg"]]
top = sum(1 for l in rq if l.startswith("- "))
say(top >= 5, "the ruling queue holds at least five entries", f"holds {top}")
miss = missing(rq, PINS["rq"])
say(not miss, "the ruling queue carries the three routed Proposals verbatim",
    f"{len(miss)} absent, first: {miss[:1]}")

# --- 8. fold-in registry ---
reg = lines[A["reg"]:A["landed"]]
miss = missing(reg, PINS["reg"])
say(not miss, "the registry carries the three riders and the three BALE.md sets verbatim",
    f"{len(miss)} absent, first: {miss[:1]}")

# --- 9. the new watch ---
wt = lines[A["watches"]:A["rq"]]
say(not missing(wt, [PINS["watch"]]),
    "the watches carry the rename's decision 2 split verbatim", "absent")

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
