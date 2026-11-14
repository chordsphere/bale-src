#!/usr/bin/env bash
# Blind checkpoint for bale-src session planner-practice (v1).
#
# Authored blind, from the request's brief, before any implementation
# existed, by the planner sitting 2026-11-11-bale-src-slips-plan-sitting-003.
# The worker never reads, edits or declares this file (TARBALL.md 7).
#
# It grades outcomes only, in the tree it runs in (bale's staging root, the
# landed tree): docs/PLANNER.md carries each phrase the brief marks
# VERBATIM (whitespace folded, so wrapping never matters), still names no
# office, and the release is 0.4.61.
#
# Exit codes (TARBALL.md 7.5): 0 every probe passed; 1 a probe failed (the
# work's failure); 2 the oracle's own machinery broke (a control, an
# unplanned exception). Reads nothing but the tree it grades. Writes
# nothing.
set -u
export PYTHONDONTWRITEBYTECODE=1
exec python3 -I -B - <<'ORACLE'
import json
import os
import re
import shutil
import sys
import traceback
from pathlib import Path


class OracleError(Exception):
    """The oracle's own machinery failed: exit 2, never a verdict."""


def _excepthook(kind, value, tb):
    print("[oracle] unexpected exception; this is the oracle's fault, "
          "not the work's (exit 2):")
    traceback.print_exception(kind, value, tb, file=sys.stdout)
    sys.stdout.flush()
    work = globals().get("WORK")
    if work is not None:
        shutil.rmtree(work, ignore_errors=True)
    os._exit(2)


sys.excepthook = _excepthook

TREE = Path.cwd()

# The brief's VERBATIM phrases, one per practice line, with the slip each
# answers. Matched in docs/PLANNER.md with whitespace folded and the
# phrase's own case.
PHRASES = (
    ("27", "the wrapping tool's line, never bale's"),
    ("28", "no backtick and no dollar sign inside its double quotes"),
    ("29", "when, for whom, what must be live and what may be not yet"),
    ("29", "LC_ALL=C"),
    ("30", "A successor's bundle takes a stem no earlier bundle of its slug had."),
    ("31", "A paste block never sits inside a list item"),
    ("31", "probed, not assumed"),
    ("31", "shows the plan and its place in it"),
)


# --- detectors (each one is exercised by a control before any probe) ---

def fold(text):
    """Every run of whitespace, line breaks included, as one space."""
    return " ".join(text.split())


def carries(doc, phrase):
    return fold(phrase) in fold(doc)


def names_office(doc):
    """True when the word office (any case, as a whole word) appears."""
    return re.search(r"\boffice\b", doc, re.IGNORECASE) is not None


# --- controls: prove every detector on synthetic input; a miss exits 2 ---

def controls():
    if fold("a  b\n\n c\t") != "a b c":
        raise OracleError("control: fold misread")
    if not carries("x when, for\n  whom, what must\nbe live and what may be not yet y",
                   "when, for whom, what must be live and what may be not yet"):
        raise OracleError("control: carries missed a wrapped phrase")
    if carries("A paste block never sits in a list item", "A paste block never sits inside a list item"):
        raise OracleError("control: carries took a near miss")
    if carries("a successor's bundle takes a stem no earlier bundle of its slug had.",
               "A successor's bundle takes a stem no earlier bundle of its slug had."):
        raise OracleError("control: carries ignored case")
    if not names_office("the Office's line") or not names_office("an office.") :
        raise OracleError("control: names_office missed the word")
    if names_office("officer, officially, home-offices"):
        raise OracleError("control: names_office matched inside another word")


def main():
    controls()
    results = []
    path = TREE / "docs" / "PLANNER.md"
    doc = path.read_text(encoding="utf-8") if path.is_file() else None
    for slip, phrase in PHRASES:
        label = f"docs/PLANNER.md carries slip {slip}'s phrase: {phrase}"
        results.append((label, doc is not None and carries(doc, phrase),
                        "no docs/PLANNER.md" if doc is None else "the phrase is absent"))
    results.append(("docs/PLANNER.md still names no office",
                    doc is not None and not names_office(doc),
                    "no docs/PLANNER.md" if doc is None else "the word office appears"))
    ver_file = TREE / "bin" / "VERSION"
    ver = ver_file.read_text(encoding="utf-8").strip() if ver_file.is_file() else None
    rec_file = TREE / "claude" / "changelog" / "0.4.61.json"
    rec_ver = None
    if rec_file.is_file():
        try:
            rec_ver = json.loads(rec_file.read_text(encoding="utf-8")).get("version")
        except (ValueError, AttributeError):
            rec_ver = "unreadable"
    results.append(("release 0.4.61: bin/VERSION and claude/changelog/0.4.61.json",
                    ver == "0.4.61" and rec_ver == "0.4.61",
                    f"bin/VERSION {ver!r}, changelog record version {rec_ver!r}"))
    return results


try:
    results = main()
except OracleError as e:
    print(f"[oracle] the oracle's own machinery failed (exit 2): {e}")
    sys.stdout.flush()
    os._exit(2)

failed = 0
for label, ok, detail in results:
    if ok:
        print(f"[PASS] {label}")
    else:
        failed += 1
        print(f"[FAIL] {label}: {detail}")
print(f"[oracle] {len(results) - failed} of {len(results)} probes passed")
sys.exit(1 if failed else 0)
ORACLE
