#!/usr/bin/env python3
"""Cross-doc section-reference integrity (session 2026-08-15-002;
PLANNER.md joined the parsed set at 2026-08-16-planner-birth-003).

The five injected docs — docs/CLAUDE.md, docs/TARBALL.md,
docs/DOCS.md, docs/CODE.md, docs/PLANNER.md — cite one another by
section number
constantly, and DOCS.md §6.4 pins those numbers as stable: once
cross-referenced, a number is permanent, and content that relocates
leaves a pointer tombstone under the same heading. This suite is the
mechanical half of that rule: every `<DOC>.md §N(.N…)` pointer (and
the equivalent singular `<DOC>.md section N` prose form) found in any
of the five docs must resolve to a numbered heading in the named doc.
The tombstone form is tolerated by construction — a tombstoned
section keeps its heading (`TARBALL.md` §5.5 is the precedent), so
the pointer resolves to it like any live section.

Deliberately NOT parsed, to keep false positives at zero:
- bare internal references ("§11.2" with no doc name) — the doc-name
  prefix is what makes a pointer unambiguous across five files;
- plural prose lists ("sections 1, 2, 5, and 7") — enumerable only
  with grammar heuristics that would misfire; the §-form carries the
  load-bearing cross-doc references.

Hermetic and stdlib-only: the docs are read from this repo; nothing
runs.

Run:  python3 -m unittest tests.test_doc_crossrefs -v
  or: python3 -m unittest discover -s tests -p 'test_doc_crossrefs.py'
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO / "docs"

GLOBAL_DOCS = ("CLAUDE.md", "TARBALL.md", "DOCS.md", "CODE.md",
               "PLANNER.md")

# A cross-doc pointer: the doc name, optionally backticked and
# possessive, then a section number in either the `§N(.N…)` form or
# the singular `section N(.N…)` prose form.
POINTER = re.compile(
    r"`?(?P<doc>CLAUDE|TARBALL|DOCS|CODE|PLANNER)\.md`?(?:'s)?\s+"
    r"(?:§|section\s+)(?P<num>\d+(?:\.\d+)*)")

# A numbered heading: `## N. Title`, `### N.N Title`, `#### N.N.N …`.
# The top-level form carries a trailing dot (`## 5. Response Tarball`);
# subsection forms don't (`### 5.2 manifest.json`).
HEADING = re.compile(r"^#{2,6}\s+(\d+(?:\.\d+)*)[.\s]", re.M)


def load_docs() -> dict[str, str]:
    return {
        name: (DOCS_DIR / name).read_text(encoding="utf-8")
        for name in GLOBAL_DOCS
        if (DOCS_DIR / name).is_file()
    }


class DocCrossReferences(unittest.TestCase):
    """Every doc-named section pointer resolves to a heading."""

    def setUp(self):
        self.docs = load_docs()
        self.headings = {
            name: set(HEADING.findall(text))
            for name, text in self.docs.items()
        }

    def test_all_global_docs_present(self):
        """The guard reads all five docs — a moved or renamed doc must
        fail here, not silently drop out of the scan (the same posture
        as test_global_doc_selfcontainment)."""
        for name in GLOBAL_DOCS:
            with self.subTest(doc=name):
                self.assertIn(
                    name, self.docs,
                    f"docs/{name} is missing — the injected-doc set "
                    "moved or shrank; update GLOBAL_DOCS here and in "
                    "test_global_doc_selfcontainment together if that "
                    "was deliberate")

    def test_pointers_are_found_at_all(self):
        """Self-test on the parser: the five docs are known to be
        thick with cross-references, so a scan finding almost none
        means the POINTER regex rotted, not that the docs went
        quiet."""
        total = sum(
            len(POINTER.findall(text)) for text in self.docs.values())
        self.assertGreater(
            total, 50,
            f"only {total} cross-doc pointers parsed across the five "
            "docs — the POINTER regex no longer matches the docs' "
            "citation style")

    def test_every_pointer_resolves(self):
        for name, text in self.docs.items():
            for lineno, line in enumerate(text.splitlines(), start=1):
                for m in POINTER.finditer(line):
                    target_doc = m.group("doc") + ".md"
                    num = m.group("num")
                    with self.subTest(doc=name, line=lineno,
                                      ref=f"{target_doc} §{num}"):
                        self.assertIn(
                            target_doc, self.docs,
                            f"docs/{name}:{lineno} points at "
                            f"{target_doc}, which is not on disk")
                        self.assertIn(
                            num, self.headings[target_doc],
                            f"docs/{name}:{lineno} points at "
                            f"{target_doc} §{num}, but no heading "
                            f"numbered {num} exists there — section "
                            "numbers are stable and relocations leave "
                            "a tombstone heading (DOCS.md 6.4):\n"
                            f"  {line.strip()}")


if __name__ == "__main__":
    unittest.main()
