#!/usr/bin/env bash
# Blind checkpoint — session planner-practices (bale-src), version 1.
# Authored 2026-10-13 by sitting 2026-10-13-twine-obligations-desk-001,
# from the request, before any implementation existed.
#
# Outcome contract only: what must be true of the applied tree. The
# cwd is the staged tree. Exit 0 = every probe passed; 1 = at least one
# probe failed (a HOLD on the work); 2 = this oracle is defective (a
# control failed or an unplanned exception) — never a verdict on the work.
# Verdict lines carry the label alone; detail follows on "  detail:" lines.
# Reads only; writes nothing; needs no sid, no manifest, no own path.
set -u
exec python3 -I -B - <<'ORACLE'
import hashlib, sys
from pathlib import Path

# ---------------------------------------------------------------- pins
PLANNER = Path("docs/PLANNER.md")
UNTOUCHED = {
    "docs/DOCS.md": "90cc9aad0670610b7865a54db33975103580cdd3354d000b8db07f8a6e956d0c",
    "docs/CODE.md": "49a145323bfc472a22dd8be56565d6e7767fd1ffbd33c36cda95e7e3e149ab75",
}
# sha256 over the LF-joined heading lines of PLANNER.md as the request
# carried it — no heading added, renamed or removed.
PLANNER_HEADINGS = "caffafca83b39e129863c2fd73e788cf687c5ffca980ea4cc1dd482c923ebb12"

# Heading text locates each section; PLANNER.md is core-first (§20 sits
# between §6 and §7), so every section is bounded by heading text, not by
# number order.
H2, H3, H4, H5, H6, H20 = ("## 2. Command and Request Authoring",
                           "## 3. Brief Authoring",
                           "## 4. Checkpoint Authoring",
                           "## 5. Post-HOLD Authoring",
                           "## 6. Sitting Practice",
                           "## 20. The Sub-Master Transition")

BLOCKS = {
    # label: (section start heading, section end heading, pinned text)
    "s2-named-unknown": (H2, H3,
        "label pre-flight guesses about unread code as guesses. A named unknown is not coverage for the unnamed check."),
    "s2-forecast-width": (H2, H3,
        "- **A directory forecast's width is not licence.** A forecast names existing paths, and a new file is covered by the directory it lands under; what may change under a directory entry is what the brief says may change, and validation proves the rest of the directory untouched."),
    "s3-unpinned-key": (H3, H4,
        "- **A brief never names a key it does not pin.** A line like \"the capabilities it implements\" with no key named is a HOLD waiting to happen: pin the key, or say that any key is accepted."),
    "s3-suite-runner": (H3, H4,
        "- **Name the suite's runner in every brief that asks for the suite.** A worker told to run the suite and not how guesses the runner, and a guessed runner finds a different suite."),
    "s3-verbatim-fences": (H3, H4,
        "- **Text the worker must carry verbatim rides as fences in the brief.** An archived file shipped with an instruction to extract from it is a paraphrase risk, and on some chat surfaces trips a safeguard outright; the blocks ride in the brief byte-exact, and the archive stays the checkpoint's to compare against."),
    "s3-quote-carries-text": (H3, H4,
        "- **A brief that asks for a verbatim quote carries the text**, or the request ships the file it is quoted from: a quotation the worker cannot see is a quotation it cannot make."),
    "s3-plain-words": (H3, H4,
        "- **A brief says what a fixture is and why the operator is blind, in plain words.** The reader may be the operator, who carries the artifact without reading the oracle; a brief that explains its fixtures only by their mechanics explains nothing to the one who pastes it."),
    "s3-ledger-verifier": (H3, H4,
        "- **Ledger lines carry their verifier.** Each line of a ledger a brief carries names the desk or session id that verified it and a `file:line`, and is re-tagged on re-verification; an untagged line is a claim, not a verified fact."),
    "s4-brief-is-contract": (H4, H5,
        "- **The brief is the contract the oracle grades.** When the two disagree the brief wins and the oracle is amended; write the twin table once, in the brief, and derive the oracle's expectations from it, never beside it."),
    "s4-pid-namespace": (H4, H5,
        "- **Rehearse under the sandbox's PID namespace.** The apply sandbox is a PID namespace — the runner can be pid 1, and an inherited process-group id reads as 0 — so an oracle that registers *itself* by process group becomes a session leader first (`os.setsid()`), or registers a child spawned for the purpose; `unshare -rpf --mount-proc` reproduces the fault at the desk."),
    "s4-specimen-off-forecast": (H4, H5,
        "- **A gate's fixture builds its specimen off the forecast.** A fixture that exercises a gate never builds its specimen through a surface in the session's own forecast."),
    "s4-crash-is-work-failure": (H4, H5,
        "- **A crash in the code under test is the work's failure.** An oracle grades it exit 1, inside its own fixture steps included; only failures of the oracle's own machinery — its controls, git, file setup — exit 2. And no probe that matches a word may see text the fixture itself authored."),
    "s5-hold-from-bytes": (H5, H6,
        "A HOLD is ruled from bytes, and the relay block often carries them: the failed probes' labels beside the worker's own validation output settle many HOLDs — a pure oracle defect, a brief gap, a brief/oracle contradiction — without more, and a read-only probe over the staging tree settles the rest. Ruling from memory of what the oracle was meant to check is the fixture defect's second life."),
    "s6-context-included": (H6, H20,
        "- **A sitting's `context_included` is its reads.** A read-only pack names what the desk will read and nothing it will not; a design sitting's include set is the record of what its rulings were made from."),
}

# ----------------------------------------------------------- detectors
def fold(s: str) -> str:
    return " ".join(s.split())

def section(text: str, start: str, end: str):
    """The folded text between two heading lines, or None when either
    heading is missing or out of order."""
    lines = text.split("\n")
    try:
        i = lines.index(start); j = lines.index(end)
    except ValueError:
        return None
    if j <= i:
        return None
    return fold("\n".join(lines[i:j]))

def contains(folded_section, phrase: str) -> bool:
    return folded_section is not None and fold(phrase) in folded_section

def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def heading_hash(text: str) -> str:
    hs = [l for l in text.split("\n")
          if l.startswith("#") and l.lstrip("#").startswith(" ")]
    return hashlib.sha256("\n".join(hs).encode("utf-8")).hexdigest()

# ------------------------------------------------------------- controls
def control(name: str, ok: bool) -> None:
    if not ok:
        print(f"oracle control failed: {name}", file=sys.stderr)
        sys.exit(2)

def run_controls() -> None:
    control("fold", fold("a \n\t b  c") == "a b c")
    sample = "## A\nx\n  y\n## B\nz\n## C\n"
    control("section-positive", section(sample, "## A", "## B") == "## A x y")
    control("section-missing", section(sample, "## A", "## Z") is None)
    control("section-order", section(sample, "## B", "## A") is None)
    control("contains-positive", contains(section(sample, "## A", "## B"), "x  y"))
    control("contains-negative", not contains(section(sample, "## A", "## B"), "z"))
    control("contains-none", not contains(None, "x"))
    control("sha256", hashlib.sha256(b"").hexdigest().startswith("e3b0c442"))
    control("heading_hash-sensitive",
            heading_hash("# a\n## b\n") != heading_hash("# a\n## c\n"))
    control("heading_hash-fence-blind",
            heading_hash("# a\n#!/bin/sh\n") == heading_hash("# a\n"))

# --------------------------------------------------------------- probes
failures = []
def probe(label: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if detail and not ok:
        print(f"  detail: {detail}")
    if not ok:
        failures.append(label)

def main() -> int:
    run_controls()
    planner = PLANNER.read_text(encoding="utf-8")
    for label, (start, end, text) in BLOCKS.items():
        sec = section(planner, start, end)
        probe(label, contains(sec, text),
              "section not located by its headings" if sec is None
              else "pinned block absent from its section (whitespace folded)")
    for rel, want in UNTOUCHED.items():
        got = sha256_of(Path(rel))
        probe(f"untouched-{Path(rel).name}", got == want,
              f"sha256 {got[:12]}… differs from the request's {want[:12]}…")
    got = heading_hash(planner)
    probe("headings-stable-PLANNER.md", got == PLANNER_HEADINGS,
          "the heading list changed (added, renamed or removed)")
    if failures:
        print(f"HOLD: {len(failures)} probe(s) failed")
        return 1
    print("PASS: every probe passed")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as e:  # an unplanned exit is an oracle fault
        print(f"oracle fault: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
ORACLE
