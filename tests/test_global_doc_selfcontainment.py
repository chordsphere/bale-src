#!/usr/bin/env python3
"""Global-doc self-containment guard (session 2026-08-14-006;
PLANNER.md joined the scanned set at 2026-08-16-planner-birth-003).

The five docs bale injects into every request — docs/CLAUDE.md,
docs/TARBALL.md, docs/DOCS.md, docs/CODE.md, docs/PLANNER.md — are
self-contained:
they cite only each other (BALE.md §3.3 carries the doctrine).
BALE.md, MASTER.md, and the rest of bale-src's claude/ inventory are
project-local; a pointer at any of them inside an injected doc
dangles in every project except this repo. The rule previously lived
only in claude/INDEX.md's "Tool design" entry — drill-down-gated and
structurally invisible to the sessions editing the globals, which is
exactly how citations drifted in. This suite is the mechanical pin.

The deny list is explicit and simple — literal substrings, not a
heuristic (a false-positive-prone regex would be worse than a short
list):

- ``BALE.md`` — never legal in a global. Not a substring hazard:
  ``TARBALL.md`` ends in ``BALL.md``, not ``BALE.md``.
- ``MASTER.md`` — never legal in a global.
- ``orchestration.md`` — bale-src's claude/context/orchestration.md;
  never legal in a global. Since 2026-08-16 that file is a tombstone
  (its doctrine relocated into docs/PLANNER.md), which changes
  nothing here: the tombstone is still project-local, and the
  relocated content must stand without naming its old home.
- ``claude/INDEX.md`` — the citation-shaped reference to bale-src's
  own doc map. A bare ``INDEX.md`` stays legal everywhere: the
  globals use it as the generic project-map concept (DOCS.md §2,
  CLAUDE.md's read-paths), and that usage is deliberate.

Hermetic and stdlib-only: the docs are read from this repo; nothing
runs.

Run:  python3 -m unittest tests.test_global_doc_selfcontainment -v
  or: python3 -m unittest discover -s tests -p 'test_global_doc_selfcontainment.py'
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO / "docs"

GLOBAL_DOCS = ("CLAUDE.md", "TARBALL.md", "DOCS.md", "CODE.md",
               "PLANNER.md")

# Literal substrings that must never appear in an injected doc. Keep
# this a short deny list of exact strings; do not generalize it into
# a pattern (module docstring carries the rationale per entry).
DENIED_SUBSTRINGS = (
    "BALE.md",
    "MASTER.md",
    "orchestration.md",
    "claude/INDEX.md",
)


def occurrences(text: str, needle: str) -> list:
    """Return (1-based line number, line) for every line containing
    the needle — the failure message needs locations, not a count."""
    return [
        (i, line)
        for i, line in enumerate(text.splitlines(), start=1)
        if needle in line
    ]


class GlobalDocSelfContainment(unittest.TestCase):
    """No injected doc references a bale-src project doc."""

    def test_all_global_docs_present(self):
        """The guard is only meaningful if it actually reads all five
        docs — a moved or renamed doc must fail here, not silently
        drop out of the scan."""
        for name in GLOBAL_DOCS:
            with self.subTest(doc=name):
                self.assertTrue(
                    (DOCS_DIR / name).is_file(),
                    f"docs/{name} is missing — the injected-doc set "
                    "moved or shrank; update GLOBAL_DOCS and BALE.md "
                    "§3.3 together if that was deliberate")

    def test_no_project_local_citations(self):
        for name in GLOBAL_DOCS:
            path = DOCS_DIR / name
            if not path.is_file():
                continue  # test_all_global_docs_present owns this failure
            text = path.read_text(encoding="utf-8")
            for needle in DENIED_SUBSTRINGS:
                with self.subTest(doc=name, needle=needle):
                    hits = occurrences(text, needle)
                    listing = "\n".join(
                        f"  line {n}: {line.strip()}" for n, line in hits)
                    self.assertEqual(
                        hits, [],
                        f"docs/{name} references bale-src project doc "
                        f"{needle!r} — injected docs are self-contained "
                        "and cite only each other (BALE.md §3.3); defer "
                        "to bale-side behavior generically instead:\n"
                        f"{listing}")


if __name__ == "__main__":
    unittest.main()
