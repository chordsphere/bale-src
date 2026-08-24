#!/usr/bin/env python3
"""Sanctioned-pair drift pins (session 2026-08-15-002).

DOCS.md §9's one-home rule has exactly one sanctioned exception:
deliberate cross-doc parallelism, where two docs state the same shape
for their own subjects so each stands alone. The contract on the
exception is that parallel copies agree — a change to one propagates
to its twin in the same session, or the parallelism has become drift.
DOCS.md §9 enumerates the pairs; this suite is the mechanical pin.

How the pin works: each side of each pair contributes one or more
narrow, whitespace-normalized extracts, asserted present in its doc.
The twins are parallel, not byte-identical (DOCS.md speaks of docs,
CODE.md of code), so the pin is per-side rather than an equality
check between the docs. Editing either twin passage breaks its pin,
and the failure message says what the fix is: propagate the change to
the twin, then update BOTH sides' extracts here in the same response
— never just the side that broke. A pin update without its twin's is
exactly the drift the pair contract forbids.

Whitespace is normalized (all runs collapse to single spaces) before
matching, so innocent markdown rewrapping never trips a pin — the
extracts pin words, not line breaks.

Hermetic and stdlib-only: the docs are read from this repo; nothing
runs.

Run:  python3 -m unittest tests.test_sanctioned_pairs -v
  or: python3 -m unittest discover -s tests -p 'test_sanctioned_pairs.py'
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO / "docs"

# The sanctioned pairs, exactly as DOCS.md §9 enumerates them. Every
# extract below is written whitespace-normalized (single spaces) and
# must match its doc after the same normalization. Keep extracts
# narrow — a sentence or two — so unrelated edits nearby never trip
# them.
PAIRS: dict[str, list[tuple[str, str]]] = {
    # DOCS.md §9's preamble and closing with CODE.md §10's.
    "hard-rules preamble and closing (DOCS.md 9 / CODE.md 10)": [
        ("DOCS.md", "Bale is project-agnostic and does not enforce "
                    "doc-inventory rules itself."),
        ("CODE.md", "Bale is project-agnostic and does not enforce "
                    "code-layout rules itself."),
        ("DOCS.md", "The universal bale-enforced rules live in "
                    "`TARBALL.md` section 8, which owns their "
                    "enumeration."),
        ("CODE.md", "The universal bale-enforced rules live in "
                    "`TARBALL.md` section 8, which owns their "
                    "enumeration."),
        ("DOCS.md", "and the enforcement recipe lives in the emission, "
                    "where it cannot drift from what runs."),
        ("CODE.md", "and the enforcement recipe lives in the emission, "
                    "where it cannot drift from what runs."),
        ("DOCS.md", "Claude should surface policy concerns in "
                    "`notes.md` precisely because mechanical checks "
                    "won't catch them."),
        ("CODE.md", "Claude surfaces policy concerns in `notes.md` "
                    "precisely because mechanical checks won't catch "
                    "them."),
    ],
    # DOCS.md §8's framing with CODE.md §9's.
    "naming-conventions framing (DOCS.md 8 / CODE.md 9)": [
        ("DOCS.md", "Strict enough to be predictable; loose enough not "
                    "to be a tax."),
        ("CODE.md", "Strict enough to be predictable; loose enough not "
                    "to be a tax."),
        ("DOCS.md", "Use the closest existing pattern and note the "
                    "awkwardness in `notes.md`."),
        ("CODE.md", "Use the closest existing pattern and note the "
                    "awkwardness in `notes.md`."),
    ],
    # DOCS.md §7's pruning sentences with CODE.md §6's.
    "pruning sentences (DOCS.md 7 / CODE.md 6)": [
        ("DOCS.md", "Lack of recent reference is **not** sufficient on "
                    "its own. Some docs are infrequently needed but "
                    "critical when they are."),
        ("CODE.md", "Lack of recent use is **not** sufficient. Some "
                    "code is infrequently exercised but load-bearing "
                    "when it is."),
        ("DOCS.md", "**Not during active feature work** — pruning "
                    "while building risks removing something needed "
                    "twenty minutes later."),
        ("CODE.md", "**Not during active feature work** — pruning "
                    "while building risks removing something needed "
                    "twenty minutes later."),
    ],
    # CLAUDE.md §11.2's rescope-offer prose with TARBALL.md §3.4's
    # pack-flag surface — the same `bale pack` command described from
    # both ends.
    "rescope offer (CLAUDE.md 11.2 / TARBALL.md 3.4)": [
        ("CLAUDE.md", "a real, copy-pasteable `bale pack` command the "
                      "architect can paste to create the narrower "
                      "request."),
        ("CLAUDE.md", "Form, flags, and their mapping to manifest "
                      "fields live in `TARBALL.md` §3.4;"),
        ("CLAUDE.md", "the command carries `--supersedes <parent-sid>` "
                      "per `TARBALL.md` §3.4's split-supersession "
                      "flow."),
        ("TARBALL.md", "Unsolicited, the worker emits a runnable "
                       "command in exactly one place: the rescope "
                       "offer, when the pre-flight scope check "
                       "(`CLAUDE.md` §11.2) decides a goal needs "
                       "splitting."),
        ("TARBALL.md", "the rescope command carries `--supersedes "
                       "<parent-sid>`, and that is the documented "
                       "path: not packing around the gate, and not "
                       "closing the parent by hand first."),
        # The sub-master rider on the same pair (session
        # 2026-08-18-010): the split-as-role-transition sentence,
        # stated from both ends of the same command.
        ("CLAUDE.md", "the offering session, as sub-master for its "
                      "subtree, authors the split sessions' "
                      "materials — commands, briefs, and re-derived "
                      "checkpoints for children it will not build "
                      "against"),
        ("TARBALL.md", "the offering session authors them as "
                       "sub-master (PLANNER.md carries the "
                       "doctrine), and the operator delivers, never "
                       "authors."),
    ],
    # DOCS.md §9's fifth pair: PLANNER.md §10's four-controls floor
    # with the project-side planning record that ratified it. The pin
    # is one-sided by construction: this suite reads docs/ only, so
    # the project-side twin cannot be pinned here — its half is
    # pinned project-side. Only the global-doc half is asserted.
    "four-controls floor (PLANNER.md 10 / project-side record)": [
        ("PLANNER.md", "The ratified floor, restated here so this "
                       "half stands alone for its citers"),
    ],
}


def normalize(text: str) -> str:
    """Collapse all whitespace runs to single spaces — the rewrapping
    tolerance: pins match words, never line breaks."""
    return " ".join(text.split())


class SanctionedPairPins(unittest.TestCase):
    """Each side of each sanctioned pair still carries its pinned
    passage."""

    def setUp(self):
        names = {doc for extracts in PAIRS.values()
                 for doc, _ in extracts}
        self.docs = {}
        for name in sorted(names):
            path = DOCS_DIR / name
            self.assertTrue(
                path.is_file(),
                f"docs/{name} is missing — a pinned doc moved; update "
                "the PAIRS table if that was deliberate")
            self.docs[name] = normalize(
                path.read_text(encoding="utf-8"))

    def test_pairs_match_the_docs_enumeration(self):
        """DOCS.md §9's enumeration is the source of which pairs
        exist; this table must not silently cover fewer. The count is
        pinned rather than parsed — the enumeration is one prose
        sentence, and a parser for it would be more fragile than the
        pin."""
        self.assertEqual(
            len(PAIRS), 5,
            "the PAIRS table no longer covers DOCS.md 9's five "
            "sanctioned pairs — re-read the enumeration there and "
            "bring the table back in step with it")

    def test_every_pin_holds(self):
        for pair, extracts in PAIRS.items():
            for doc, extract in extracts:
                with self.subTest(pair=pair, doc=doc,
                                  extract=extract[:50] + "…"):
                    # assertTrue, not assertIn: the haystack is a whole
                    # normalized doc and would drown the message.
                    self.assertTrue(
                        normalize(extract) in self.docs[doc],
                        f"sanctioned-pair pin broke: docs/{doc} no "
                        f"longer contains the pinned passage for "
                        f"[{pair}]:\n  {extract}\nA sanctioned pair "
                        "changes both twins in the same session "
                        "(DOCS.md 9) — propagate the edit to the "
                        "twin doc, then update BOTH sides' extracts "
                        "in this table in the same response.")


if __name__ == "__main__":
    unittest.main()
