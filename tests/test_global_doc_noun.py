#!/usr/bin/env python3
"""Global-doc noun guard (session 2026-09-23-board-100-w1-doc-sweep-002,
W1 of the agent-noun arc).

The five global docs — docs/CLAUDE.md, docs/TARBALL.md, docs/DOCS.md,
docs/CODE.md, docs/PLANNER.md — and the repo README name the session
they address by the ratified role-neutral noun, "the agent", with a
hat noun ("the worker", "the planner") where a sentence means one
hat; "I"/"me" stays, because that is the operator writing to the
agent, not vendor coupling. The same sweep retired bale's own
"inject" vocabulary from those six files in favor of carry/ship
terms. Both were prose sweeps with no mechanical pin behind them: the
self-containment guard (tests/test_global_doc_selfcontainment.py)
scans denied citation tokens and never reads the noun, and the
cross-reference and sanctioned-pair suites pin sentences, not
vocabulary. This suite is the mechanical pin, on the self-containment
guard's model — a denied-token scan with line-numbered failures.

The deny table has two halves, kept as tightly anchored as the
guard's own:

- The capitalized noun as a whole word: ``\\bClaude\\b``. Word-bounded,
  so the file name ``CLAUDE.md`` (different case; the file is renamed
  by a later session, not this one), the surface name ``claude.ai``
  (lowercase; its one home is CLAUDE.md §11.7's surface table), the
  enum value ``claude-decides`` (lowercase; a code identifier until
  the sibling code session admits its successor), and the ``claude/``
  directory prefix are all untouched. The docs read the noun in
  prose only, so the whole-word form is the whole hazard.
- The inject family as lowercase words: ``inject``, ``injects``,
  ``injected``, ``injection``, ``injecting`` — matched
  case-sensitively, so the code identifier ``INJECTED_TOOLS``
  (docs/TARBALL.md §3.1's citation of ``bin/bale``'s constant) stays
  legal until the code session renames it and a doc session
  re-cites it. A lowercase hit is prose, and prose says carry/ship.

Hermetic and stdlib-only: the files are read from this repo; nothing
runs. Both directions are graded on specimens independent of the
scanned tree (``DenyShapeTest``), because a clean tree proves only
that nothing is there to catch.

Run:  python3 -m unittest tests.test_global_doc_noun -v
  or: python3 -m unittest discover -s tests -p 'test_global_doc_noun.py'
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

GLOBAL_DOCS = ("CLAUDE.md", "TARBALL.md", "DOCS.md", "CODE.md",
               "PLANNER.md")

# Every scanned file, repo-relative: the five globals plus the repo
# README, the six files the W1 sweep covered.
SCANNED_FILES = tuple(f"docs/{name}" for name in GLOBAL_DOCS) + (
    "README.md",)

# The deny table: label first, so failures read; each pattern tightly
# anchored per the module docstring.
DENIED_PATTERNS = (
    ("capitalized noun `Claude` (whole word)", re.compile(r"\bClaude\b")),
    ("lowercase inject vocabulary",
     re.compile(r"\binject(?:s|ed|ion|ing)?\b")),
)


def occurrences(text: str, pattern: re.Pattern) -> list:
    """Return (1-based line number, line) for every line the pattern
    hits — the failure message needs locations, not a count."""
    return [
        (i, line)
        for i, line in enumerate(text.splitlines(), start=1)
        if pattern.search(line) is not None
    ]


class GlobalDocNoun(unittest.TestCase):
    """No global doc, and not the README, names the session by the
    retired capitalized noun or describes bale's carry as injection."""

    DOCTRINE = (
        "the ratified noun is \"the agent\" (a hat noun where a "
        "sentence means one hat; \"I/me\" stays), and bale carries or "
        "ships the globals — it does not inject them")

    def test_all_scanned_files_present(self):
        """The guard is only meaningful if it reads the whole swept
        surface — a moved or renamed file must fail here, not
        silently drop out of the scan."""
        for rel in SCANNED_FILES:
            with self.subTest(file=rel):
                self.assertTrue(
                    (REPO / rel).is_file(),
                    f"{rel} is missing — the swept set moved or shrank; "
                    "update SCANNED_FILES here (and GLOBAL_DOCS in "
                    "test_global_doc_selfcontainment) together if that "
                    "was deliberate")

    def test_no_denied_tokens(self):
        for rel in SCANNED_FILES:
            path = REPO / rel
            if not path.is_file():
                continue  # the presence test owns this failure
            text = path.read_text(encoding="utf-8")
            for label, pattern in DENIED_PATTERNS:
                with self.subTest(file=rel, shape=label):
                    hits = occurrences(text, pattern)
                    listing = "\n".join(
                        f"  line {n}: {line.strip()}" for n, line in hits)
                    self.assertEqual(
                        hits, [],
                        f"{rel} carries {label} — {self.DOCTRINE}:\n"
                        f"{listing}")


class DenyShapeTest(unittest.TestCase):
    """Both patterns graded in both directions on specimens that do
    not depend on the scanned tree."""

    NOUN, INJECT = (p for _, p in DENIED_PATTERNS)

    NOUN_CAUGHT = (
        "Claude reads the manifest first.",
        "what Claude remembers from a prior session",
        "the next Claude session",
        "Claude-detected triggers",
        "Claude's own guidelines",
        "\"Claude\" and \"worker\" read as the same party",
    )
    NOUN_TOLERATED = (
        "the agent reads the manifest first",
        "docs/CLAUDE.md",
        "`CLAUDE.md`",
        "auto-compacts (claude.ai web/app)",
        "`claude-decides` (default)",
        "claude/checkpoints/2026-09-23-x-002.sh",
        "claude/responses/response-NNN/",
        "Claudeception",   # not the whole word; not a spelling the docs use
    )
    INJECT_CAUGHT = (
        "bale injects all five into every request",
        "# injected by bale",
        "the pack-time injection",
        "bale-injected global docs",
        "inject global doc CLAUDE.md",
        "injecting the tools pair",
        # A word boundary sits at a hyphen, so a compound is a hit too:
        # the sweep retired the word in every compound, not only standalone.
        "an injection-free design",
    )
    INJECT_TOLERATED = (
        "`INJECTED_TOOLS` in `bin/bale` is the one source",
        "bale carries all five into every request",
        "shipped by bale",
        "the carry-model question",
    )

    def test_noun_caught(self):
        for text in self.NOUN_CAUGHT:
            with self.subTest(text=text):
                self.assertIsNotNone(self.NOUN.search(text))

    def test_noun_tolerated(self):
        for text in self.NOUN_TOLERATED:
            with self.subTest(text=text):
                self.assertIsNone(self.NOUN.search(text))

    def test_inject_caught(self):
        for text in self.INJECT_CAUGHT:
            with self.subTest(text=text):
                self.assertIsNotNone(self.INJECT.search(text))

    def test_inject_tolerated(self):
        for text in self.INJECT_TOLERATED:
            with self.subTest(text=text):
                self.assertIsNone(self.INJECT.search(text))


if __name__ == "__main__":
    unittest.main()
