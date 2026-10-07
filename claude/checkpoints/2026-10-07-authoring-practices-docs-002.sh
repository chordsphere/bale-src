#!/usr/bin/env bash
# Blind checkpoint — bale-src session `authoring-practices-docs` — v1.
# Authored blind at the read-only sitting 2026-10-06-twine-slip-sitting-006,
# from the session's brief, before the worker exists. Outcome-only: it
# grades what docs/PLANNER.md and docs/TARBALL.md carry — the seventeen
# verbatim leads in their named sections, the two carried cadence sentences,
# the rehearsal row and sentence, the untouched docs' hashes, the two docs'
# heading lists, and the doc suites green — never how the bullets were
# phrased or placed.
#
# Runs with the tree under test as the working directory. Writes nothing
# anywhere but the interpreter's scratch for the doc suites' temp files
# (TMPDIR under one fresh `mktemp -d`); no interpreter cache
# (PYTHONDONTWRITEBYTECODE, `python3 -B`). Reads no session, no manifest and
# not its own path.
#
# Exit codes (TARBALL.md §7.5): 0 all probes pass; 1 a probe failed (label
# alone on the [FAIL] line, detail on `  detail:` lines); 2 the oracle is
# defective — a control could not fire its own detector, or an unexpected
# exception.
set -u
export PYTHONDONTWRITEBYTECODE=1
echo "[oracle] authoring-practices-docs v1 — tree: $PWD"
echo "[oracle] writes: one fresh mktemp -d scratch root only (TMPDIR for the doc suites); nothing under the tree"
exec python3 -B - "$PWD" <<'ORACLE'
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
PLANNER = TREE / "docs" / "PLANNER.md"
TARBALL = TREE / "docs" / "TARBALL.md"

# The seventeen leads, byte-verbatim from the brief, each with its home:
# (doc, top-level section number or "4.3", lead).
LEADS = [
    ("PLANNER.md", "3", "Grade reconstructed text against its archived source in the tree, never against the brief's copy."),
    ("PLANNER.md", "3", "A paste through a Windows terminal mangles em dashes, section signs and ellipses."),
    ("PLANNER.md", "3", "A record format a checkpoint writes by hand is pinned in the brief to the byte, every key named."),
    ("PLANNER.md", "3", "A brief that pins \"X ships no Y\" says what \"ships\" covers."),
    ("PLANNER.md", "3", "An out-of-scope line must not fence off where a delegated decision lands."),
    ("PLANNER.md", "3", "Counts name their unit."),
    ("PLANNER.md", "3", "A pointer stays unique after the session's own insertions."),
    ("PLANNER.md", "4", "A checkpoint's control calls the probe's own detector function, not an inline copy of its expression."),
    ("PLANNER.md", "4", "Dry-run a code checkpoint against a throwaway stub landing written from the brief, discarded after."),
    ("PLANNER.md", "4", "A blind checkpoint's dry-run runs before any session exists: no sid, no manifest, no own filename."),
    ("PLANNER.md", "4", "A fixture built from \"at least these keys\" is built against a floor."),
    ("PLANNER.md", "4", "An oracle's unexpected exception exits 2."),
    ("PLANNER.md", "4", "Count from the table, not from a proposal."),
    ("PLANNER.md", "4", "An oracle that signals, kills or deletes acts only on what it started itself."),
    ("PLANNER.md", "6", "A light-block question that events answer is closed, not re-asked."),
    ("TARBALL.md", "7", "A tree walk excludes the validation base path."),
    ("TARBALL.md", "4.3", "A read-only probe cannot run a verb that writes, bale apply --dry-run included."),
]
# The carried cadence sentences (registry rider), byte-verbatim, PLANNER.md §6.
CADENCE = [
    "More project work, less master grooming: an arc's design sitting authors its own wave's bundles once the operator ratifies the decomposition; no master sits between it and its workers.",
    "Closes are per wave, not per master. A master's last job is the wave's close, after its project work is dispatched.",
]
UNTOUCHED = {
    "AGENT.md": "5124250b3d6362ae362801f89e2c0498a6e493c638a398de2f4c3d13d6c12285",
    "DOCS.md": "90cc9aad0670610b7865a54db33975103580cdd3354d000b8db07f8a6e956d0c",
    "CODE.md": "49a145323bfc472a22dd8be56565d6e7767fd1ffbd33c36cda95e7e3e149ab75",
}
HEADINGS = {
    "PLANNER.md": ['# PLANNER.md', '## META', '### What this doc is', '### Who reads this, and when', '### Conflict resolution', '## INDEX', '### Read paths', "## 1. The Planner's Surface", '## 2. Command and Request Authoring', '## 3. Brief Authoring', '## 4. Checkpoint Authoring', '## 5. Post-HOLD Authoring', '## 6. Sitting Practice', '## 20. The Sub-Master Transition', '### 20.1 The upward contract', '### 20.2 The upward report', '## 7. Hard Rules', '## 8. Orchestration Doctrine — Standing', '## 9. The Foundational Principle: Minimize Specification Friction', '## 10. The Four Controls', '## 11. Decomposition at Seams', '## 12. Blind Checkpoints', '## 13. Disjointness Enforcement', '## 14. HOLD Judgment', '## 15. Escalation and the Clarification Queue', '## 16. Worker Refresh', '## 17. Cost Governance', '## 18. Trust Phasing', '## 19. What This Half Is Not'],
    "TARBALL.md": ['# TARBALL.md', '## META', '### What this doc is', '## INDEX', '### Read paths', '## 1. Conventions', '## 2. Four Exchanges', '## 5. Response Tarball', '### 5.1 Shape', '### 5.1.1 apply.sh', '### 5.2 manifest.json', '### 5.2.1 Computing size_bytes and sha256', '### 5.2.2 The feedback block', '### 5.3 Claims vs verdict', '### 5.4 notes.md (optional)', '#### 5.4.1 The Proposals section', '### 5.5 next-prompt.md (retired)', '### 5.6 Bailout response', '#### 5.6.1 Shape', '#### 5.6.2 Manifest specifics for bailouts', '#### 5.6.3 Apply-time UX (moved)', '### 5.7 handoff.md (required in bailout responses)', '### 5.8 diagnostics.json (required in bailout responses)', '### 5.9 Clarification response', '#### 5.9.1 When it engages', '#### 5.9.2 Shape and manifest specifics', '#### 5.9.3 Apply-time UX (moved)', '#### 5.9.4 Posture and the answer path', '### 5.10 The light question block', '## 7. Validation', '### 7.1 The staging-copy approach', '### 7.2 Check sequence', '### 7.3 Claim/verdict reconciliation', '### 7.4 Logging', '### 7.5 Exit codes', '### 7.6 Runtime budget', '### 7.7 Asserting executable bits', '## 3. Request Tarball', '### 3.1 Shape', '### 3.2 manifest.json', '### 3.3 When `expects_probe: no` collides with a real gap', '### 3.4 Authoring a request with `bale pack`', '## 4. Probe', '### 4.1 When a probe engages', '### 4.2 The paste-back probe (default shape)', '### 4.3 Probe script rules', '### 4.4 The file-based fallback', '### 4.5 Provenance', '### 4.6 The probe as a tool call', '## 6. Worked Example: Smallest Plausible Response', '## 8. Hard Rules (Tarball-Specific)', '## 9. Hard Nots', '## 10. Quick Reference', '### 10.1 Building a response tarball', '### 10.2 Returning a probe instead', '### 10.3 Returning a clarification instead', '### 10.4 Returning a light question block instead'],
}
DOC_SUITES = ["tests.test_doc_crossrefs", "tests.test_global_doc_selfcontainment",
              "tests.test_sanctioned_pairs", "tests.test_global_doc_noun",
              "tests.test_schema_embeds"]

FAILS = []


def ok(label):
    print(f"[PASS] {label}")


def bad(label, detail):
    FAILS.append(label)
    print(f"[FAIL] {label}")
    for line in str(detail).splitlines() or ["(no detail)"]:
        print(f"  detail: {line}")


def verdict(label, defects):
    bad(label, "\n".join(defects)) if defects else ok(label)


def oracle_broken(why):
    print(f"[oracle] CONTROL FAILED — the oracle is defective: {why}")
    sys.stdout.flush()
    os._exit(2)


def excepthook(exc_type, exc, tb):
    import traceback
    print("[oracle] unexpected exception — exit 2, not a verdict on the work")
    traceback.print_exception(exc_type, exc, tb, file=sys.stdout)
    sys.stdout.flush()
    os._exit(2)


sys.excepthook = excepthook
SCRATCH = Path(tempfile.mkdtemp(prefix="oracle-authoring-docs-"))
print(f"[oracle] scratch root: {SCRATCH}")


# -------------------------------------------------------------- detectors
def fold(text):
    """Whitespace collapsed to single spaces, emphasis markers (*, _, `)
    stripped — the locating fold the brief names for wrapped markdown."""
    return " ".join(re.sub(r"[*_`]", "", text or "").split())


def headings(text):
    out = []
    fenced = False
    for ln in (text or "").splitlines():
        if ln.startswith("```"):
            fenced = not fenced
            continue
        if not fenced and re.match(r"^#{1,6} ", ln):
            out.append(ln.rstrip())
    return out


def section(text, number):
    """The lines of top-level section `number` (`## N.` to the next `## `),
    or of subsection `N.M` (`### N.M ` to the next `###`/`##`). Returns
    '' when the heading is absent."""
    lines = (text or "").splitlines()
    if "." in number:
        start_re = re.compile(rf"^### {re.escape(number)} ")
        end_re = re.compile(r"^#{2,3} ")
    else:
        start_re = re.compile(rf"^## {re.escape(number)}\. ")
        end_re = re.compile(r"^## ")
    start = next((i for i, ln in enumerate(lines) if start_re.match(ln)), None)
    if start is None:
        return ""
    end = next((i for i in range(start + 1, len(lines)) if end_re.match(lines[i])), len(lines))
    return "\n".join(lines[start:end])


def lead_defects(doc_text, number, lead):
    sec = section(doc_text, number)
    if not sec:
        return [f"section {number} not found"]
    if fold(lead) not in fold(sec):
        return [f"lead not found in section {number}: {lead[:60]}…"]
    return []


def hash_defects(data, expected, name):
    got = hashlib.sha256(data).hexdigest()
    return [] if got == expected else [f"{name} sha256 {got[:12]}… != {expected[:12]}… (must be byte-identical)"]


def heading_defects(text, expected, name):
    got = headings(text)
    if got == expected:
        return []
    added = [h for h in got if h not in expected]
    removed = [h for h in expected if h not in got]
    return [f"{name} headings changed: added {added!r}, removed {removed!r}"
            + ("" if added or removed else " (order changed)")]


def dry_run_row_defects(tarball_text):
    sec = section(tarball_text, "3.4")
    if not sec:
        return ["TARBALL.md 3.4 not found"]
    d = []
    if not re.search(r"^\| `--dry-run`", sec, re.M):
        d.append("TARBALL.md 3.4's flag table has no `--dry-run` row")
    if "--check" not in sec:
        d.append("TARBALL.md 3.4 does not mention the `--check` rehearsal")
    return d


def rehearsal_sentence_defects(planner_text):
    sec = section(planner_text, "4")
    if not sec:
        return ["PLANNER.md 4 not found"]
    if "bale open --dry-run" not in fold(sec):
        return ["PLANNER.md 4 does not name `bale open --dry-run` as the pre-delivery rehearsal"]
    return []


# --------------------------------------------------------------- controls
def controls():
    doc = "## 3. Brief Authoring\n\n- **Counts name\n  their unit.** text\n\n## 4. X\n\n- other\n"
    if lead_defects(doc, "3", "Counts name their unit."):
        oracle_broken("lead_defects rejected a wrapped, emphasized lead in its section: "
                      + "; ".join(lead_defects(doc, "3", "Counts name their unit.")))
    if not lead_defects(doc, "4", "Counts name their unit."):
        oracle_broken("lead_defects accepted a lead found in the wrong section")
    if not lead_defects(doc, "3", "Counts name their units."):
        oracle_broken("lead_defects accepted a lead that differs by one letter")
    sub = "## 4. Probe\n\n### 4.2 A\n\nx\n\n### 4.3 Probe script rules\n\n- **A read-only probe cannot run a verb that writes, bale apply --dry-run included.**\n\n### 4.4 B\n\nno\n"
    if lead_defects(sub, "4.3", LEADS[-1][2]):
        oracle_broken("lead_defects rejected a lead in a subsection")
    if not lead_defects(sub, "4.4", LEADS[-1][2]):
        oracle_broken("lead_defects accepted a subsection lead in the wrong subsection")
    if not hash_defects(b"changed", UNTOUCHED["AGENT.md"], "AGENT.md"):
        oracle_broken("hash_defects accepted changed bytes")
    if not heading_defects("# PLANNER.md\n## 3. Brief Authoring\n## 3b. New\n", HEADINGS["PLANNER.md"], "x"):
        oracle_broken("heading_defects accepted an added heading")
    if heading_defects("\n".join(HEADINGS["PLANNER.md"]) + "\n", HEADINGS["PLANNER.md"], "x"):
        oracle_broken("heading_defects rejected the shipped heading list")
    if not dry_run_row_defects("### 3.4 Authoring a request with `bale pack`\n\n| `--json` | x |\n"):
        oracle_broken("dry_run_row_defects accepted a 3.4 without the row")
    if dry_run_row_defects("### 3.4 Authoring a request with `bale pack`\n\n| `--dry-run` | x --check |\n"):
        oracle_broken("dry_run_row_defects rejected a 3.4 with the row")
    if not rehearsal_sentence_defects("## 4. Checkpoint Authoring\n\n- nothing\n\n## 5. Y\n"):
        oracle_broken("rehearsal_sentence_defects accepted a 4 without the rehearsal verb")
    if fold("  **a**   `b`\n c ") != "a b c":
        oracle_broken("fold does not collapse whitespace and strip emphasis")
    print("[oracle] controls: every detector fires on its known-bad input")


# ----------------------------------------------------------------- probes
def main():
    if not PLANNER.is_file() or not TARBALL.is_file():
        oracle_broken("docs/PLANNER.md or docs/TARBALL.md missing — not run from the tree root?")
    controls()
    texts = {"PLANNER.md": PLANNER.read_text(encoding="utf-8"),
             "TARBALL.md": TARBALL.read_text(encoding="utf-8")}
    for n, (doc, number, lead) in enumerate(LEADS, 1):
        verdict(f"lead {n} in {doc} {number}: {lead[:48]}", lead_defects(texts[doc], number, lead))
    for i, sentence in enumerate(CADENCE, 1):
        verdict(f"cadence sentence {i} carried verbatim into PLANNER.md 6",
                lead_defects(texts["PLANNER.md"], "6", sentence))
    verdict("PLANNER.md 4 names bale open --dry-run as the pre-delivery rehearsal",
            rehearsal_sentence_defects(texts["PLANNER.md"]))
    verdict("TARBALL.md 3.4 carries a --dry-run row and names --check",
            dry_run_row_defects(texts["TARBALL.md"]))
    for name, h in UNTOUCHED.items():
        verdict(f"docs/{name} byte-identical", hash_defects((TREE / "docs" / name).read_bytes(), h, name))
    for name in ("PLANNER.md", "TARBALL.md"):
        verdict(f"docs/{name} headings and numbering unchanged",
                heading_defects(texts[name], HEADINGS[name], name))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", TMPDIR=str(SCRATCH))
    r = subprocess.run([sys.executable, "-B", "-m", "unittest", "-q", *DOC_SUITES],
                       cwd=str(TREE), env=env, capture_output=True, text=True, timeout=600)
    tail = "\n".join(r.stderr.splitlines()[-6:])
    verdict("the doc suites are green (crossrefs, selfcontainment, sanctioned pairs, noun, schema embeds)",
            [] if r.returncode == 0 else [f"exit {r.returncode}", tail])
    shutil.rmtree(SCRATCH, ignore_errors=True)
    print(f"[oracle] {len(FAILS)} failed probe(s)")
    sys.stdout.flush()
    os._exit(1 if FAILS else 0)


main()
ORACLE
