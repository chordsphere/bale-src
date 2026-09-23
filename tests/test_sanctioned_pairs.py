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

Since session 2026-09-21-split-transition-unconditional-007 the
CLAUDE.md 11.2 / TARBALL.md 3.4 pair states the split's role transition
and its bundled delivery for every project, with the checkpoint
condition attached to the children's checkpoints alone. Both CLAUDE.md
extracts are VERBATIM in that session's brief of record and pinned
whole; TARBALL.md's twins are its own wording, pinned by their
load-bearing clauses. The pair had been pinned in its conditional form
(the bundled-delivery group's CLAUDE.md extract opened "In a
checkpoint-configured project"), so the suite held in place the very
reading the bundle-delivery ruling was written to retire. A positive
pin cannot see a condition coming back beside it, so
RetiredSplitConditions pins the absence: the conditional openings stay
gone from the three docs that carried them, and TARBALL.md 3.4's
"**Checkpoint-configured projects.**" paragraph stays about
checkpoints, with no bundle sentence filed under it.

Since the W1 doc sweep (session 2026-09-23-board-100-w1-doc-sweep-002)
the two hard-rules closings are pinned with the ratified agent noun:
the sweep changed the subject of both sentences in the same motion,
and the pins moved with them.

Hermetic and stdlib-only: the docs are read from this repo; nothing
runs.

Run:  python3 -m unittest tests.test_sanctioned_pairs -v
  or: python3 -m unittest discover -s tests -p 'test_sanctioned_pairs.py'
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

# normalize() lives in tests/harness.py (board 109: one home per helper).
# The dotted run form in the docstring (`python3 -m unittest
# tests.<suite>`) does not put tests/ on sys.path the way direct execution
# and `discover -s tests` do, so put it there before the bare import —
# this suite ran in all three forms before the helper moved, and still
# does.
_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)
from harness import normalize  # noqa: E402 — path guard above

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
        # The noun in both closings is the ratified agent noun since
        # 2026-09-23-board-100-w1-doc-sweep-002 (the W1 doc sweep);
        # the pins moved with the text.
        ("DOCS.md", "The agent should surface policy concerns in "
                    "`notes.md` precisely because mechanical checks "
                    "won't catch them."),
        ("CODE.md", "The agent surfaces policy concerns in `notes.md` "
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
        # stated from both ends of the same command. Unconditional
        # since 2026-09-21-split-transition-unconditional-007: the
        # transition is owed in every project, and the checkpoint
        # condition attaches to the children's checkpoints alone. The
        # CLAUDE.md sentence is VERBATIM in that session's brief and
        # pinned whole; TARBALL.md states the same rule in its own
        # words, pinned by the clause that makes it general and
        # carries the `PLANNER.md` §20 pointer.
        ("CLAUDE.md", "The split is always a role transition "
                      "(`PLANNER.md` §20): the offering session, as "
                      "sub-master for its subtree, authors the split "
                      "sessions' materials — commands, briefs, and, "
                      "in a checkpoint-configured project, re-derived "
                      "checkpoints for children it will not build "
                      "against — and holds its decomposition for the "
                      "parent's ratification before anything spawns "
                      "(`PLANNER.md` §20.1); the operator carries "
                      "artifacts, never authors them."),
        ("TARBALL.md", "A pre-flight split (`CLAUDE.md` §11.2) is a "
                       "role transition in every project "
                       "(`PLANNER.md` §20): the offering session, as "
                       "sub-master for its subtree, authors the split "
                       "sessions' materials"),
        # The children's-checkpoints half of the same rider: TARBALL.md
        # 3.4's checkpoint paragraph, where "them" is the children's
        # checkpoints. Unchanged since 2026-08-18-010.
        ("TARBALL.md", "the offering session authors them as "
                       "sub-master (PLANNER.md carries the "
                       "doctrine), and the operator delivers, never "
                       "authors."),
    ],
    # The bundle-delivery rider on the same CLAUDE.md §11.2 /
    # TARBALL.md §3.4 pair (board 80, from session
    # 2026-09-14-tarball-s34-bundle-clauses-004): the offered command
    # travels as a crafter bundle beside its `bale open` line, stated
    # from both ends. A second pin group over an already-enumerated
    # pair, not a sixth pair — see test_pairs_match_the_docs_enumeration.
    "bundled delivery (CLAUDE.md 11.2 / TARBALL.md 3.4)": [
        # Unconditional since
        # 2026-09-21-split-transition-unconditional-007. The CLAUDE.md
        # sentence is VERBATIM in that session's brief and pinned
        # whole. TARBALL.md's first extract is byte-for-byte the one
        # pinned before: the sentence moved out from under 3.4's
        # "**Checkpoint-configured projects.**" lead unchanged (its
        # position is RetiredSplitConditions' to hold). The second is
        # the sentence under 3.4's rescope worked example, so the
        # example and the rule stop disagreeing by omission.
        ("CLAUDE.md", "The offering session delivers that command "
                      "bundled, in every project — as the stored pack "
                      "argv of a crafter bundle emitted beside its "
                      "`bale open` line — per `PLANNER.md` §20 and §2; "
                      "the bare line stays the offer's content, which "
                      "the planner re-derives from (`TARBALL.md` "
                      "§3.4)."),
        ("TARBALL.md", "Each child's command is delivered as one "
                       "crafter bundle emitted beside its `bale open` "
                       "line (`PLANNER.md` §2)."),
        ("TARBALL.md", "in every project it is delivered as the stored "
                       "pack argv of a crafter bundle emitted beside "
                       "its `bale open` line (`PLANNER.md` §2)."),
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

# The conditional openings session
# 2026-09-21-split-transition-unconditional-007 retired, by the doc
# each lived in. Each sentence was true and none said "only", but a
# worker in a project with no checkpoint read the condition as
# excluding it and skipped the transition. An opening coming back is
# that misreading coming back, whatever the positive pins above say.
RETIRED_SPLIT_CONDITIONS = (
    ("CLAUDE.md", "In a checkpoint-configured project the offering "
                  "session delivers that command bundled"),
    ("CLAUDE.md", "In a checkpoint-configured project the split is "
                  "also a role transition"),
    ("PLANNER.md", "in a checkpoint-configured project does not emit "
                   "an offer"),
)

# TARBALL.md 3.4's checkpoint paragraph, by its bold lead, and the
# general facts that must not be filed under it: the bundle sentence
# (the bundled-delivery group's unchanged TARBALL.md extract) and the
# transition itself.
CHECKPOINT_PARAGRAPH_LEAD = "**Checkpoint-configured projects.**"
NOT_UNDER_THE_CHECKPOINT_LEAD = (
    "Each child's command is delivered as one crafter bundle",
    "role transition",
)


def paragraph_led_by(text: str, lead: str) -> str:
    """The one blank-line-delimited paragraph of `text` that opens with
    `lead`, whitespace-normalized; '' when none or several do (the
    caller asserts on that, so a duplicated lead fails loudly instead
    of being judged by its first copy)."""
    hits = [p for p in text.split("\n\n") if p.lstrip().startswith(lead)]
    return normalize(hits[0]) if len(hits) == 1 else ""


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
        pin.

        What is counted is doc pairs, not table keys: a key's trailing
        parenthetical names its pair, and one pair may carry several
        pin groups (the rescope offer and its bundled-delivery rider
        both pin CLAUDE.md 11.2 / TARBALL.md 3.4, since board 80). Two
        keys over the same pair are two groups, one pair."""
        doc_pairs = {key[key.rindex("("):] for key in PAIRS}
        self.assertEqual(
            len(doc_pairs), 5,
            f"the PAIRS table covers {len(doc_pairs)} doc pairs "
            f"({sorted(doc_pairs)}), not DOCS.md 9's five sanctioned "
            "pairs — re-read the enumeration there and bring the table "
            "back in step with it")

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


class RetiredSplitConditions(unittest.TestCase):
    """The split's role transition and its bundled delivery stay
    stated for every project: the retired conditional openings stay
    absent, and TARBALL.md 3.4's checkpoint paragraph stays about
    checkpoints."""

    def test_conditional_openings_stay_retired(self):
        for doc, fragment in RETIRED_SPLIT_CONDITIONS:
            with self.subTest(doc=doc, fragment=fragment[:50] + "…"):
                body = normalize(
                    (DOCS_DIR / doc).read_text(encoding="utf-8"))
                self.assertFalse(
                    normalize(fragment) in body,
                    f"docs/{doc} again opens a split rule with a "
                    f"checkpoint condition:\n  {fragment}\nThe "
                    "transition and the bundled delivery are owed in "
                    "every project; only the children's checkpoints "
                    "are conditional on the project pinning one. "
                    "Attach the condition to the checkpoints, not to "
                    "the sentence.")

    def test_checkpoint_paragraph_is_about_checkpoints_only(self):
        text = (DOCS_DIR / "TARBALL.md").read_text(encoding="utf-8")
        paragraph = paragraph_led_by(text, CHECKPOINT_PARAGRAPH_LEAD)
        self.assertTrue(
            paragraph,
            "docs/TARBALL.md should carry exactly one paragraph led "
            f"{CHECKPOINT_PARAGRAPH_LEAD} — it moved, was renamed, or "
            "was duplicated; update this pin if that was deliberate")
        for general_fact in NOT_UNDER_THE_CHECKPOINT_LEAD:
            with self.subTest(general_fact=general_fact):
                self.assertFalse(
                    normalize(general_fact) in paragraph,
                    "docs/TARBALL.md 3.4 files a general fact under "
                    f"{CHECKPOINT_PARAGRAPH_LEAD}:\n  {general_fact}\n"
                    "A reader in a project with no checkpoint skips "
                    "that paragraph, and the fact with it. State it "
                    "in 3.4's role-transition paragraph instead.")


if __name__ == "__main__":
    unittest.main()
