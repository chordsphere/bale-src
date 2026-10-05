#!/usr/bin/env bash
# Blind checkpoint — session sitting-close-deltas-20 (the friction-points
# arc's close). Authored at desk 2026-10-04-friction-points-cleanup-002
# from the request, before the work exists. Reads claude/MASTER.md in the
# tree under test (cwd) and nothing else; writes nothing.
#
# Exit codes (TARBALL.md §7.5): 0 every probe passed; 1 a probe failed;
# 2 the oracle's own machinery broke (a failed control, an unreadable or
# missing MASTER.md is a FAIL, not a 2).
#
# Probes:
#   last-landed        the header's last-landed-by line names a
#                      sitting-close-deltas-20 sid, edited in place
#   rider-status-row   the "bale status row" rider stays, bracketed
#                      consumed at 2026-10-04-clipboard-paste-blocks-001
#   rider-triple-quote the triple-quoted refusal rider stays, bracketed
#                      consumed at 2026-10-03-wizard-defaults-006
#   bale-md-open       the ruling queue's BALE.md entry stays, undisposed
#   arc-sids           every session of the arc is named: five workers and
#                      three desks
#   evidence-appended  §6's numbered entries continue past 219, in order
#   sections-intact    the eight top-level sections, in order; §2 unchanged
set -u
exec python3 -B - "$PWD" <<'PY'
import hashlib, re, sys
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
MASTER = TREE / "claude" / "MASTER.md"
RESULTS = []
LABELS = {
    "last-landed": "last-landed: the last-landed-by line names this close's "
                   "sitting-close-deltas-20 sid",
    "rider-status-row": "rider-status-row: the bale status row rider is "
                        "marked consumed by session D",
    "rider-triple-quote": "rider-triple-quote: the triple-quoted refusal "
                          "rider is marked consumed by session C",
    "bale-md-open": "bale-md-open: the BALE.md ruling-queue entry stays "
                    "open and unaltered",
    "arc-sids": "arc-sids: every session of the arc is named in MASTER.md",
    "evidence-appended": "evidence-appended: new evidence entries continue "
                         "section 6's numbering past 219",
    "sections-intact": "sections-intact: the eight sections stand in order "
                       "and section 2 is unchanged",
}
SECTION_2_SHA256 = ("77378669c7e15f90d6bd54f5f93e6e4b"
                    "387bec8c7bd48b7184753e2a6f7e0cf7")
HEADINGS = ["## 1. ", "## 2. ", "## 3. ", "## 4. ", "## 5. ", "## 6. ",
            "## 7. ", "## 8. "]
ARC_SIDS = ["2026-10-03-friction-points-001",
            "2026-10-03-config-wizard-ui-002",
            "2026-10-03-bale-cli-reference-003",
            "2026-10-03-friction-points-wave2-004",
            "2026-10-03-pack-wizard-ui-005",
            "2026-10-03-wizard-defaults-006",
            "2026-10-04-clipboard-paste-blocks-001",
            "2026-10-04-friction-points-cleanup-002"]
RIDER_STATUS = [
    "- A bale-side consumer for `get_probe_clipboard_command`: a `bale",
    "  status` row (\"probe clipboard: <cmd> / unset\") so a",
    "  crafter-unreadable hand edit surfaces before a probe falls back to",
    "  remedy text. Rides the next `bale status` touch.",
]
RIDER_TRIPLE = [
    "- Bale-side refusal of a triple-quoted `clipboard_command` — rides the",
    "  next `bin/bale_config.py` touch; 005/69's disclosure stands",
    "  meanwhile.",
]
RULING_BALE_MD = [
    "- Whether the release tarball ships BALE.md — today `scripts/build.sh`",
    "  excludes it, the README now points install readers at `bale help",
    "  <command>`, and several `--help` strings still cite `BALE.md §N` an",
    "  install reader cannot open (99a's Proposal 1). Ship it, or keep it",
    "  source-only and qualify the citations in a `bin/bale` string pass.",
]


class Broken(Exception):
    pass


def record(key, ok, detail=""):
    RESULTS.append((key, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {LABELS[key]}")
    if not ok and detail:
        for ln in str(detail).splitlines()[:8]:
            print(f"      detail: {ln}")


def find_block(lines, block):
    """Index of the first line of `block` matched line for line, or None."""
    n = len(block)
    for i in range(len(lines) - n + 1):
        if lines[i:i + n] == block:
            return i
    return None


def entry_span(lines, start):
    """A top-level "- " entry from `start` to the line before the next
    top-level entry, blank line, or bold header."""
    end = start + 1
    while end < len(lines):
        ln = lines[end]
        if ln.startswith("- ") or ln.strip() == "" or ln.startswith("**"):
            break
        end += 1
    return lines[start:end]


def controls():
    sample = ["x", "- a", "  b", "  [c]", "- d"]
    if find_block(sample, ["- a", "  b"]) != 1:
        raise Broken("block locator control failed")
    if entry_span(sample, 1) != ["- a", "  b", "  [c]"]:
        raise Broken("entry span control failed")


def rider(lines, key, block, sid):
    at = find_block(lines, block)
    if at is None:
        record(key, False, "the entry's original lines are not all present, "
               "unchanged and in order")
        return
    span = "\n".join(entry_span(lines, at)[len(block):])
    ok = "consumed" in span and sid in span
    record(key, ok, f"bracket text after the entry: {span[:200]!r}")


def main():
    try:
        controls()
    except Broken as e:
        print(f"[ORACLE BROKEN] {e}")
        return 2
    try:
        text = MASTER.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        for key in LABELS:
            record(key, False, f"claude/MASTER.md unreadable: {e}")
        return 1
    lines = text.split("\n")
    try:
        header = lines[:40]
        landed = [i for i, ln in enumerate(header)
                  if ln.startswith("Last landed by:")]
        ok = (len(landed) == 1 and re.fullmatch(
            r"Last landed by: `\d{4}-\d{2}-\d{2}-sitting-close-deltas-20-\d{3}`\.",
            header[landed[0]]) is not None
              and header[landed[0] + 1] ==
              "(This line is edited in place at each landing, never appended to.)")
        record("last-landed", ok,
               f"{[header[i] for i in landed]!r}")

        rider(lines, "rider-status-row", RIDER_STATUS,
              "2026-10-04-clipboard-paste-blocks-001")
        rider(lines, "rider-triple-quote", RIDER_TRIPLE,
              "2026-10-03-wizard-defaults-006")

        at = find_block(lines, RULING_BALE_MD)
        if at is None:
            record("bale-md-open", False, "the entry's original lines are not "
                   "all present, unchanged and in order")
        else:
            span = "\n".join(entry_span(lines, at))
            record("bale-md-open", "DISPOSED" not in span,
                   "the entry is marked DISPOSED")

        missing = [s for s in ARC_SIDS if s not in text]
        record("arc-sids", not missing, f"not named: {missing}")

        try:
            s6 = next(i for i, ln in enumerate(lines) if ln.startswith("## 6. "))
            s7 = next(i for i, ln in enumerate(lines) if ln.startswith("## 7. "))
        except StopIteration:
            s6 = s7 = None
        if s6 is None:
            record("evidence-appended", False, "section 6 or 7 heading missing")
        else:
            # Entries 10 and up only: a short numbered sub-list inside an
            # entry ("1. **…") is not an entry.
            nums = [int(m.group(1)) for ln in lines[s6:s7]
                    for m in [re.match(r"^(\d+)\. \*\*", ln)] if m
                    and int(m.group(1)) >= 10]
            ok = (bool(nums) and max(nums) >= 220
                  and nums == list(range(nums[0], nums[0] + len(nums))))
            record("evidence-appended", ok,
                   f"entries {nums[0] if nums else None}..{nums[-1] if nums else None}, "
                   f"{len(nums)} found, sequential: "
                   f"{nums == list(range(nums[0], nums[0] + len(nums))) if nums else False}")

        heads = [ln for ln in lines if ln.startswith("## ")]
        order_ok = [h[:6] for h in heads] == HEADINGS
        try:
            a = next(i for i, ln in enumerate(lines) if ln.startswith("## 2. "))
            b = next(i for i, ln in enumerate(lines) if ln.startswith("## 3. "))
            s2 = hashlib.sha256(("\n".join(lines[a:b]) + "\n").encode("utf-8")
                                ).hexdigest()
        except StopIteration:
            s2 = None
        record("sections-intact", order_ok and s2 == SECTION_2_SHA256,
               f"headings in order: {order_ok}; section 2 unchanged: "
               f"{s2 == SECTION_2_SHA256}")
    except Exception as e:  # an oracle bug, never a verdict on the work
        print(f"[ORACLE BROKEN] {type(e).__name__}: {e}")
        return 2
    if {k for k, _ in RESULTS} != set(LABELS):
        print("[ORACLE BROKEN] not every probe recorded a verdict")
        return 2
    failed = [k for k, ok in RESULTS if not ok]
    print(f"checkpoint: {len(RESULTS) - len(failed)}/{len(RESULTS)} probes passed")
    return 1 if failed else 0


sys.exit(main())
PY
