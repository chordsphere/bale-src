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

Since board 80 the suite also carries two prose-content pins for the
bundle-delivery ruling (session 2026-09-14-bundle-delivery-doctrine-003
proposed them): docs/PLANNER.md §2 leads its bundle bullet with the
bold phrase "The bundle is the delivery form of every planner-authored
pack" and states it before the "Commands are single-line" bullet, and
docs/CLAUDE.md mentions `bale open` at least once. Neither the
cross-reference scan above nor test_sanctioned_pairs reads that
content, so a doc session that rewrapped §2 or pruned the bullet would
pass both — and the operator's original report ("no project other than
bale-src has ever emitted a planner bundle") was exactly a
docs-as-written outcome. Matching is whitespace-normalized, the same
rewrapping tolerance the sanctioned-pair pins use.

Since the terminal-shapes ruling (session
2026-09-15-board-96-doc-97-terminal-shapes-013) the suite also pins
that ruling's text of record: every tarball-mode turn ends in a
machine-recognizable shape, and the light question block is one of
them. Two sentences land byte-exact in docs/TARBALL.md §5.10 (the
count-not-judgment admission test and the packer's three replies),
docs/CLAUDE.md §3 states the every-turn-ends-in-a-shape rule beside
its shapes paragraph, and four chat-invitation phrases the ruling
struck stay absent from the docs they lived in. The cross-reference
scan resolves `TARBALL.md` §5.10 as a pointer but cannot see whether
the section still says what the ruling said, and the struck phrases
are exactly the kind of prose a rewrap-tolerant scan never reads;
these pins are that content check. Matching is whitespace-normalized
like every other prose pin here.

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


def normalize(text: str) -> str:
    """Collapse all whitespace runs to single spaces — the rewrapping
    tolerance: prose pins match words, never line breaks."""
    return " ".join(text.split())


def top_level_section(text: str, number: int) -> str:
    """The body of `## N. …` up to the next `## ` heading, or '' when
    no such heading exists (the caller asserts on that)."""
    m = re.search(rf"^##\s+{number}\.\s.*$", text, re.M)
    if m is None:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    return rest if nxt is None else rest[:nxt.start()]


# The bundle-delivery ruling's lead phrase (PLANNER.md §2) and the
# bullet it must precede. Both pinned whitespace-normalized; the lead
# phrase is a prefix of the bold sentence, so a later clause edit
# ("in every project") does not trip it.
BUNDLE_RULING_LEAD = "**The bundle is the delivery form of every planner-authored pack"
SINGLE_LINE_BULLET = "**Commands are single-line"

# The terminal-shapes ruling's text of record. The two TARBALL.md
# sentences are verbatim-marked in the ruling and land byte-exact
# (whitespace collapsed, since the docs wrap at 70); the CLAUDE.md
# sentence agrees with the session opener's closing sentence that
# bale emits. Keep these narrow — a sentence each — so unrelated
# edits nearby never trip them.
LIGHT_ADMISSION_SENTENCE = (
    "A question set is admitted to the light tier when it holds at "
    "most three questions, none multi-tiered, and each carries a "
    "default the packer can ratify with a word or an answer that fits "
    "on one line; the worker counts, never judges.")
LIGHT_REPLIES_SENTENCE = (
    "The packer replies in one of three ways: answer inline; "
    "\"as assumed\" to ratify every default at once; or \"formal\" to "
    "have the same questions returned as a clarification response.")
EVERY_TURN_SENTENCE = (
    "Every turn Claude ends in tarball mode takes one "
    "machine-recognizable shape: a response tarball, a probe block, a "
    "light question block, or a clarification response; a question "
    "asked as prose is not a shape.")

# The chat-invitation phrases the ruling struck, by the doc each lived
# in. A phrase reappearing is the drift this pin exists to catch: a
# worker choosing between a doc that says "not size" and a doc that
# says "ask in chat" picks the invitation.
STRUCK_PHRASES = (
    ("TARBALL.md", "small enough to resolve"),
    ("TARBALL.md", "a question in chat as conversation"),
    ("CLAUDE.md", "Claude asks, in one sentence"),
    ("CLAUDE.md", "brief paused question in chat"),
)


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


class BundleRulingPins(unittest.TestCase):
    """The bundle-delivery ruling stays stated where the docs say it
    is (board 80, item 2)."""

    def setUp(self):
        self.docs = load_docs()

    def test_planner_bundle_ruling_bullet_precedes_single_line(self):
        self.assertIn("PLANNER.md", self.docs, "docs/PLANNER.md is missing")
        section = normalize(top_level_section(self.docs["PLANNER.md"], 2))
        self.assertTrue(
            section,
            "docs/PLANNER.md has no `## 2.` heading — the ruling's home "
            "section moved; section numbers are stable (DOCS.md 6.4)")
        lead_at = section.find(normalize(BUNDLE_RULING_LEAD))
        self.assertNotEqual(
            lead_at, -1,
            "docs/PLANNER.md 2 no longer opens a bullet with the bold "
            f"phrase {BUNDLE_RULING_LEAD!r} — the bundle-delivery ruling "
            "was pruned or reworded (session 2026-09-14-003's doctrine)")
        single_at = section.find(normalize(SINGLE_LINE_BULLET))
        self.assertNotEqual(
            single_at, -1,
            "docs/PLANNER.md 2 no longer carries the "
            f"{SINGLE_LINE_BULLET!r} bullet the ruling is ordered before")
        self.assertLess(
            lead_at, single_at,
            "docs/PLANNER.md 2 states the bundle-delivery ruling after "
            "the single-line-commands bullet — the ruling leads; the "
            "command form follows it")

    def test_claude_mentions_bale_open(self):
        self.assertIn("CLAUDE.md", self.docs, "docs/CLAUDE.md is missing")
        # assertTrue, not assertIn: the haystack is the whole doc and
        # would drown the message.
        self.assertTrue(
            "`bale open`" in self.docs["CLAUDE.md"],
            "docs/CLAUDE.md no longer mentions `bale open` — the bundle "
            "is delivered beside its `bale open` line (PLANNER.md 2), "
            "and CLAUDE.md is where the worker learns that verb exists")


class TerminalShapePins(unittest.TestCase):
    """The terminal-shapes ruling stays stated where the docs say it
    is: the light question block's text of record in TARBALL.md
    5.10, the every-turn rule in CLAUDE.md 3, and the struck chat
    invitations absent."""

    def setUp(self):
        self.docs = load_docs()
        self.normalized = {name: normalize(text)
                           for name, text in self.docs.items()}

    def test_tarball_has_light_question_block_section(self):
        self.assertIn("TARBALL.md", self.docs, "docs/TARBALL.md is missing")
        self.assertIsNotNone(
            re.search(r"^### 5\.10\s", self.docs["TARBALL.md"], re.M),
            "docs/TARBALL.md has no `### 5.10` heading — the light "
            "question block's home moved; section numbers are stable "
            "(DOCS.md 6.4)")

    def test_light_tier_sentences_verbatim(self):
        self.assertIn("TARBALL.md", self.docs, "docs/TARBALL.md is missing")
        for label, sentence in (("admission", LIGHT_ADMISSION_SENTENCE),
                                ("three replies", LIGHT_REPLIES_SENTENCE)):
            with self.subTest(sentence=label):
                # assertTrue, not assertIn: the haystack is the whole
                # doc and would drown the message.
                self.assertTrue(
                    normalize(sentence) in self.normalized["TARBALL.md"],
                    f"docs/TARBALL.md no longer carries the light tier's "
                    f"{label} sentence byte-exact (whitespace aside) — "
                    "the ruling marked it verbatim; restore it rather "
                    f"than paraphrase it:\n  {sentence}")

    def test_claude_states_every_turn_rule(self):
        self.assertIn("CLAUDE.md", self.docs, "docs/CLAUDE.md is missing")
        self.assertTrue(
            normalize(EVERY_TURN_SENTENCE) in self.normalized["CLAUDE.md"],
            "docs/CLAUDE.md no longer states the every-turn-ends-in-a-"
            "shape rule beside its tarball-mode shapes — the sentence "
            "must agree with the session opener bale emits:\n  "
            f"{EVERY_TURN_SENTENCE}")

    def test_struck_chat_invitations_stay_absent(self):
        for doc, phrase in STRUCK_PHRASES:
            with self.subTest(doc=doc, phrase=phrase):
                self.assertIn(doc, self.docs, f"docs/{doc} is missing")
                self.assertFalse(
                    normalize(phrase) in self.normalized[doc],
                    f"docs/{doc} carries the struck chat invitation "
                    f"{phrase!r} again — the terminal-shapes ruling "
                    "removed it: a non-blocking ask is a light question "
                    "block (TARBALL.md 5.10), a blocking one a "
                    "clarification (TARBALL.md 5.9), and a question "
                    "asked as prose is not a shape")


if __name__ == "__main__":
    unittest.main()
