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

Since board 109 (from 2026-09-16-board-105-operator-voice-007's
Proposals) the shape sentence's third home is pinned too. The ruling
lives in the session opener, docs/CLAUDE.md §3, and docs/TARBALL.md
§5.10, and until then the suites pinned only the first two. §5.10's
copy is its own wording, not CLAUDE.md's — "the worker" for "Claude",
an em-dash for the colon, and the §4.2 / §5.9 pointers — so it is
pinned as TARBALL_SHAPE_SENTENCE against the §5.10 section body alone
(a copy that drifted elsewhere in TARBALL.md does not satisfy it), and
a constant-level check holds the two pinned copies to one shared
second half, the half that was grown in step at board 105.

Since the opener reword's doc sweep (session
2026-09-19-opener-reword-docs-005, split from
2026-09-19-opener-reword-doc-sweep-r2-003) the shape sentence is
retired in both doc homes. Its successor is the re-scoped ask rule
(DOC_ASK_SENTENCE): a turn that *needs something* ends in a probe
block, a light question block, or a clarification response, and every
other turn is ordinary prose. The ruling's core clause, "a question
asked as prose is not a shape", survives verbatim inside it. The
session opener no longer carries a copy of the doc sentence: it has
its own chat-facing ask sentence, pinned by the opener's suite, so the
doc pins here stand on the ruling of record, not on agreement with
the opener. Beside it lands the deliverable ruling
(DOC_DELIVERABLE_SENTENCE): a worker session owes one response
tarball, a read-only planner session owes none. Both are VERBATIM in
the brief of record and pinned byte-exact (whitespace-collapsed) in
each home: DOC_ASK in docs/CLAUDE.md 3 and docs/TARBALL.md 5.10,
DOC_DELIVERABLE in docs/CLAUDE.md 3 and docs/TARBALL.md 2, each
against its section body alone. The retired sentence's fragments are
pinned absent. The same sweep names the request README as the
session's brief: docs/CLAUDE.md META's reading order lists it third
and names the manifest's `readme` key, docs/TARBALL.md 3.2 documents
the key, and 3.1's old "most sessions skip the README" claim stays
gone.

Since board 111 (from 2026-09-18-board-47b-relay-blocks-003's
Proposals) the suite also pins the worker relay paragraph of
docs/TARBALL.md 7, the one opening "A HOLD reaches the worker as one
addressed block". It states a worker-facing wire fact — the whole-line
`to worker` sentinels `bale apply` prints around a HOLD's worker
block — that the code pinned but the doc did not. The sentinels are
not pinned as a literal: they are built by bin/bale_report.py's own
relay_sentinels() with the docs' `<sid>` placeholder and asserted in
the section 7 lead (the prose before `### 7.1`), so the pin goes red
when either side moves — a doc edit that drops or re-spells them, or
a code change to what apply prints. Two narrow clauses of the same
paragraph ride beside it: the lead clause that names the sentinels as
whole-line, and the whole-of-the-failure-context sentence.

Hermetic and stdlib-only: the docs are read from this repo, and the
one code import is bin/bale_report.py for the pure relay_sentinels()
builder (stdlib-only at module scope); nothing else runs.

Run:  python3 -m unittest tests.test_doc_crossrefs -v
  or: python3 -m unittest discover -s tests -p 'test_doc_crossrefs.py'
"""

from __future__ import annotations

import re
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
from harness import _load_module, normalize  # noqa: E402 — path guard above

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


def top_level_section(text: str, number: int) -> str:
    """The body of `## N. …` up to the next `## ` heading, or '' when
    no such heading exists (the caller asserts on that)."""
    m = re.search(rf"^##\s+{number}\.\s.*$", text, re.M)
    if m is None:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^##\s", rest, re.M)
    return rest if nxt is None else rest[:nxt.start()]


def subsection(text: str, number: str) -> str:
    """The body of `### N.N …` up to the next `##` or `###` heading, or
    '' when no such heading exists (the caller asserts on that).

    A deeper `####` heading inside the subsection stays in its body;
    `number` is matched literally, so "5.1" never matches "5.10".
    """
    m = re.search(rf"^###\s+{re.escape(number)}\s.*$", text, re.M)
    if m is None:
        return ""
    rest = text[m.end():]
    nxt = re.search(r"^#{2,3}\s", rest, re.M)
    return rest if nxt is None else rest[:nxt.start()]


def section_lead(text: str, number: int) -> str:
    """The lead of `## N. …`: its body up to the first subsection
    heading (`###` or deeper) or the next `##`, whichever comes first;
    '' when no such heading exists (the caller asserts on that).

    TARBALL.md 7's worker relay paragraph sits in this lead, before
    `### 7.1`, and the relay pin reads the lead alone so a copy of the
    sentinels elsewhere in section 7 cannot satisfy it.
    """
    body = top_level_section(text, number)
    nxt = re.search(r"^#{3,6}\s", body, re.M)
    return body if nxt is None else body[:nxt.start()]


# The bundle-delivery ruling's lead phrase (PLANNER.md §2) and the
# bullet it must precede. Both pinned whitespace-normalized; the lead
# phrase is a prefix of the bold sentence, so a later clause edit
# ("in every project") does not trip it.
BUNDLE_RULING_LEAD = "**The bundle is the delivery form of every planner-authored pack"
SINGLE_LINE_BULLET = "**Commands are single-line"

# The terminal-shapes ruling's text of record for the light tier. The
# two TARBALL.md sentences are verbatim-marked in the ruling and land
# byte-exact (whitespace collapsed, since the docs wrap at 70). Keep
# these narrow — a sentence each — so unrelated edits nearby never
# trip them.
LIGHT_ADMISSION_SENTENCE = (
    "A question set is admitted to the light tier when it holds at "
    "most three questions, none multi-tiered, and each carries a "
    "default the packer can ratify with a word or an answer that fits "
    "on one line; the worker counts, never judges.")
LIGHT_REPLIES_SENTENCE = (
    "The packer replies in one of three ways: answer inline; "
    "\"as assumed\" to ratify every default at once; or \"formal\" to "
    "have the same questions returned as a clarification response.")
# The re-scoped ask rule (opener reword, 2026-09-19): VERBATIM in the
# brief of record, one wording in both homes (CLAUDE.md 3 and
# TARBALL.md 5.10). It replaced the "Every turn ... takes one
# machine-recognizable shape" sentence and that sentence's board-105
# second half, in both homes at once.
DOC_ASK_SENTENCE = (
    "A turn that needs something from the packer, an environment fact "
    "or a decision, ends in the matching shape: a probe block, a light "
    "question block, or a clarification response; a question asked as "
    "prose is not a shape, because it gets lost. Every other turn is "
    "ordinary prose.")
# The terminal-shapes ruling's core clause, which must survive inside
# the re-scoped rule word for word.
SHAPE_RULING_CORE_CLAUSE = "a question asked as prose is not a shape"
# What each session mode owes back (opener reword, 2026-09-19):
# VERBATIM in the brief of record, homed in CLAUDE.md 3 and TARBALL.md
# 2. The backticks around `bale open` are part of the pinned bytes.
DOC_DELIVERABLE_SENTENCE = (
    "What a session owes back follows from how it was packed: a worker "
    "session, any pack with a write forecast, owes one response tarball "
    "carrying the finished work; a planner session, a read-only pack, "
    "lands nothing and returns no response tarball, not even an empty "
    "one — it owes its answer in chat and, for each session it is "
    "asked to author, a crafter bundle beside its `bale open` line.")
# Fragments of the retired shape sentence, by the docs it lived in. A
# fragment coming back means a second, contradicting ask rule.
RETIRED_SHAPE_FRAGMENTS = (
    ("CLAUDE.md", "machine-recognizable shape"),
    ("TARBALL.md", "machine-recognizable shape"),
    ("CLAUDE.md", "Explanation in prose is expected and welcome"),
    ("TARBALL.md", "Explanation in prose is expected and welcome"),
)
# The README sweep: the stale claim that retired from TARBALL.md 3.1,
# and the phrase that named the brief vaguely in CLAUDE.md's reading
# order and read-paths row.
RETIRED_README_FRAGMENTS = (
    ("TARBALL.md", "Most sessions skip the README"),
    ("CLAUDE.md", "the session prompt"),
)

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


# The worker relay paragraph of TARBALL.md 7 (board 111, from
# 2026-09-18-board-47b-relay-blocks-003's Proposals). The sentinel lines
# themselves are NOT constants here: they come from bin/bale_report.py's
# relay_sentinels(), called with the docs' placeholder for the sid, so
# the doc is held to what `bale apply` actually prints. The two clauses
# are the paragraph's own words, narrow, whitespace-collapsed.
RELAY_SID_PLACEHOLDER = "<sid>"
RELAY_WORKER_LEAD_CLAUSE = (
    "A HOLD reaches the worker as one addressed block that `bale apply` "
    "prints between the whole-line sentinels")
RELAY_WORKER_CONTEXT_CLAUSE = (
    "That block is the whole of the failure context — it carries nothing "
    "else of the checkpoint's output, by construction — so the worker "
    "diagnoses from it and never asks for the session log")


def relay_worker_gaps(lead: str, begin: str, end: str) -> list[str]:
    """What the TARBALL.md 7 lead is missing of the worker relay
    paragraph, as human-readable gaps; [] when the paragraph states it
    all. `lead` is raw doc text (normalized here); `begin` and `end`
    are the sentinel lines as the code builds them. Each sentinel is
    matched as a whole backticked code span, so a longer line that
    merely contains it does not satisfy the pin, and BEGIN must come
    before END."""
    body = normalize(lead)
    gaps = []
    for label, clause in (("lead clause", RELAY_WORKER_LEAD_CLAUSE),
                          ("failure-context sentence",
                           RELAY_WORKER_CONTEXT_CLAUSE)):
        if normalize(clause) not in body:
            gaps.append(f"{label}: {clause}")
    at = {}
    for label, line in (("BEGIN sentinel", begin), ("END sentinel", end)):
        at[label] = body.find(normalize(f"`{line}`"))
        if at[label] == -1:
            gaps.append(f"{label}: `{line}`")
    if -1 not in at.values() and at["BEGIN sentinel"] > at["END sentinel"]:
        gaps.append("sentinel order: BEGIN is stated after END")
    return gaps

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
    """The terminal-shapes ruling, as re-scoped by the opener reword,
    stays stated where the docs say it is: the light question block's
    text of record in TARBALL.md 5.10, the ask rule in CLAUDE.md 3 and
    TARBALL.md 5.10, the deliverable rule in CLAUDE.md 3 and
    TARBALL.md 2, and the retired sentence and struck chat invitations
    absent."""

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

    def test_claude_3_states_ask_rule(self):
        """CLAUDE.md 3 carries the re-scoped ask rule, byte-exact
        (whitespace aside), in the section — not merely the file."""
        self.assertIn("CLAUDE.md", self.docs, "docs/CLAUDE.md is missing")
        section = normalize(top_level_section(self.docs["CLAUDE.md"], 3))
        self.assertTrue(
            section,
            "docs/CLAUDE.md has no `## 3.` heading — the modes section "
            "moved; section numbers are stable (DOCS.md 6.4)")
        self.assertTrue(
            normalize(DOC_ASK_SENTENCE) in section,
            "docs/CLAUDE.md 3 no longer states the ask rule byte-exact "
            "(whitespace aside) — it is the ruling of record, VERBATIM "
            "in the opener-reword brief, and CLAUDE.md 3 is one of its "
            "two doc homes; restore it rather than paraphrase it:\n  "
            f"{DOC_ASK_SENTENCE}")

    def test_tarball_5_10_states_ask_rule(self):
        """TARBALL.md 5.10 carries the same ask rule, same words, in
        the section body alone."""
        self.assertIn("TARBALL.md", self.docs, "docs/TARBALL.md is missing")
        section = normalize(subsection(self.docs["TARBALL.md"], "5.10"))
        self.assertTrue(
            section,
            "docs/TARBALL.md has no `### 5.10` heading — the light "
            "question block's home moved; section numbers are stable "
            "(DOCS.md 6.4)")
        self.assertTrue(
            normalize(DOC_ASK_SENTENCE) in section,
            "docs/TARBALL.md 5.10 no longer states the ask rule "
            "byte-exact (whitespace aside) — the rule has two doc homes "
            "(CLAUDE.md 3, TARBALL.md 5.10), one wording; restore it "
            f"rather than paraphrase it:\n  {DOC_ASK_SENTENCE}")

    def test_claude_3_states_deliverable_rule(self):
        self.assertIn("CLAUDE.md", self.docs, "docs/CLAUDE.md is missing")
        section = normalize(top_level_section(self.docs["CLAUDE.md"], 3))
        self.assertTrue(
            normalize(DOC_DELIVERABLE_SENTENCE) in section,
            "docs/CLAUDE.md 3 no longer states what each session mode "
            "owes back, byte-exact (whitespace aside) — the ruling of "
            "record, VERBATIM in the opener-reword brief:\n  "
            f"{DOC_DELIVERABLE_SENTENCE}")

    def test_tarball_2_states_deliverable_rule(self):
        self.assertIn("TARBALL.md", self.docs, "docs/TARBALL.md is missing")
        section = normalize(top_level_section(self.docs["TARBALL.md"], 2))
        self.assertTrue(
            section,
            "docs/TARBALL.md has no `## 2.` heading — the exchanges "
            "section moved; section numbers are stable (DOCS.md 6.4)")
        self.assertTrue(
            normalize(DOC_DELIVERABLE_SENTENCE) in section,
            "docs/TARBALL.md 2 no longer states what each session mode "
            "owes back, byte-exact (whitespace aside) — the ruling of "
            "record, VERBATIM in the opener-reword brief:\n  "
            f"{DOC_DELIVERABLE_SENTENCE}")

    def test_retired_shape_sentence_stays_absent(self):
        for doc, fragment in RETIRED_SHAPE_FRAGMENTS:
            with self.subTest(doc=doc, fragment=fragment):
                self.assertIn(doc, self.docs, f"docs/{doc} is missing")
                self.assertFalse(
                    normalize(fragment) in self.normalized[doc],
                    f"docs/{doc} carries {fragment!r} again — the "
                    "every-turn shape sentence retired in favor of the "
                    "re-scoped ask rule, and a second copy would say "
                    "every turn needs a shape when only a turn that asks "
                    "does")

    def test_subsection_reads_5_10_alone(self):
        """Self-test on the extractor, so the 5.10 pin cannot pass by
        reading past its section: the body stops before the next
        heading and does not reach back into 5.9."""
        body = subsection(self.docs["TARBALL.md"], "5.10")
        self.assertIn("=== LIGHT BEGIN", body)
        self.assertNotRegex(body, r"(?m)^#{2,3}\s",
                            "the 5.10 body ran into another heading")
        self.assertNotIn("#### 5.9.4", body)
        synthetic = ("### 5.1 One\none body\n### 5.10 Ten\nten body\n"
                     "#### 5.10.1 Deep\ndeep body\n## 6. Next\nnext\n")
        self.assertEqual(subsection(synthetic, "5.1"), "\none body\n")
        self.assertEqual(subsection(synthetic, "5.10"),
                         "\nten body\n#### 5.10.1 Deep\ndeep body\n")
        self.assertEqual(subsection(synthetic, "5.2"), "")

    def test_ask_rule_keeps_the_ruling_core_clause(self):
        """Constant-level: the re-scoped rule still carries the
        terminal-shapes ruling's core clause word for word, so a later
        edit to the constant cannot quietly drop the ruling it
        inherits. Trips before either doc is read."""
        self.assertIn(normalize(SHAPE_RULING_CORE_CLAUSE),
                      normalize(DOC_ASK_SENTENCE))

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



class ReadmeBriefPins(unittest.TestCase):
    """The request README is named as the session's brief, third in the
    reading order, and the manifest's `readme` key is documented
    (opener reword's doc sweep, 2026-09-19)."""

    def setUp(self):
        self.docs = load_docs()
        self.normalized = {name: normalize(text)
                           for name, text in self.docs.items()}

    def _reading_order(self) -> str:
        text = self.docs["CLAUDE.md"]
        m = re.search(r"^### Reading order\s*$", text, re.M)
        self.assertIsNotNone(
            m, "docs/CLAUDE.md META has no `### Reading order` heading")
        rest = text[m.end():]
        nxt = re.search(r"^#{2,3}\s", rest, re.M)
        return rest if nxt is None else rest[:nxt.start()]

    def test_reading_order_names_the_brief_third(self):
        """manifest.json, then CLAUDE.md, then README.md — the order
        the opener gives — as the list's first three items."""
        items = re.findall(r"(?m)^(\d+)\.\s+\*\*(.+?)\*\*",
                           self._reading_order())
        heads = [head for _, head in items]
        self.assertGreaterEqual(len(heads), 3, heads)
        self.assertIn("`manifest.json`", heads[0])
        self.assertIn("`CLAUDE.md`", heads[1])
        self.assertIn("`README.md`", heads[2],
                      "docs/CLAUDE.md META's reading order no longer "
                      "names the request's README.md third, after "
                      "manifest.json and CLAUDE.md")

    def test_reading_order_and_index_row_name_the_readme_key(self):
        order = normalize(self._reading_order())
        self.assertIn("`readme` key", order,
                      "docs/CLAUDE.md META's reading order no longer "
                      "says the manifest's `readme` key is how a reader "
                      "knows whether a brief ships")
        row = next((line for line in self.docs["CLAUDE.md"].splitlines()
                    if line.startswith("| Every session |")), "")
        self.assertTrue(row, "docs/CLAUDE.md INDEX lost its Every session row")
        for needle in ("`README.md`", "`readme` key"):
            with self.subTest(needle=needle):
                self.assertIn(needle, row)
        self.assertLess(row.index("`CLAUDE.md`"), row.index("`README.md`"),
                        "the Every session row names README.md before "
                        "CLAUDE.md")

    def test_tarball_3_2_documents_readme_key(self):
        section = subsection(self.docs["TARBALL.md"], "3.2")
        self.assertTrue(section, "docs/TARBALL.md has no `### 3.2` heading")
        self.assertIn('"readme": {', section,
                      "TARBALL.md 3.2's example manifest lost its readme key")
        self.assertIn("- **`readme`**", section,
                      "TARBALL.md 3.2's field semantics lost the readme bullet")
        body = normalize(section)
        for shape in ('`"path"`, always the string `README.md`',
                      '`"sha256"`, the hex sha256 of the shipped '
                      '`README.md` bytes',
                      "`null` when no `README.md` ships"):
            with self.subTest(shape=shape):
                self.assertIn(normalize(shape), body)

    def test_retired_readme_phrasing_stays_absent(self):
        for doc, fragment in RETIRED_README_FRAGMENTS:
            with self.subTest(doc=doc, fragment=fragment):
                self.assertFalse(
                    normalize(fragment) in self.normalized[doc],
                    f"docs/{doc} carries {fragment!r} again — the README "
                    "is the session's brief, named by the manifest's "
                    "`readme` key and read third")



class RelayParagraphPins(unittest.TestCase):
    """TARBALL.md 7's worker relay paragraph states the `to worker`
    sentinels exactly as `bale apply` prints them (board 111)."""

    @classmethod
    def setUpClass(cls):
        cls.docs = load_docs()
        # _load_module, not a bare import: harness's one home for loading
        # a bin/ sibling by path, bin/ added to sys.path only when absent.
        report = _load_module("bale_report")
        cls.begin, cls.end = report.relay_sentinels(
            RELAY_SID_PLACEHOLDER, report.RELAY_TO_WORKER)

    def _lead(self) -> str:
        self.assertIn("TARBALL.md", self.docs, "docs/TARBALL.md is missing")
        lead = section_lead(self.docs["TARBALL.md"], 7)
        self.assertTrue(
            lead,
            "docs/TARBALL.md has no `## 7.` heading — the validation "
            "section moved; section numbers are stable (DOCS.md 6.4)")
        return lead

    def test_tarball_7_states_worker_relay_paragraph(self):
        gaps = relay_worker_gaps(self._lead(), self.begin, self.end)
        self.assertEqual(
            gaps, [],
            "docs/TARBALL.md 7's lead no longer states the worker relay "
            "paragraph as `bale apply` prints it (whitespace aside). The "
            "sentinels are built by bin/bale_report.py's relay_sentinels(); "
            "if the code changed, the doc follows in the same response; if "
            "the doc changed, restore the paragraph rather than paraphrase "
            "it. Missing:\n  " + "\n  ".join(gaps))

    def test_builder_addresses_the_worker(self):
        """Constant-level: the builder's worker lines are the addressed
        `to worker` form, so the doc pin above cannot pass on a planner
        pair or a bare sentinel. Trips before the doc is read."""
        self.assertEqual(
            (self.begin, self.end),
            ("=== RELAY BEGIN <sid> to worker ===",
             "=== RELAY END <sid> to worker ==="))

    def test_pin_bites(self):
        """The pin fails against a lead without the fact: the paragraph
        struck, the sentinels re-addressed to the planner, BEGIN and END
        swapped, or a sentinel unbackticked into running prose. Each
        mutation starts from the real lead, so the check is not vacuous."""
        lead = self._lead()
        self.assertEqual(relay_worker_gaps(lead, self.begin, self.end), [])
        para_at = lead.index("A HOLD reaches the worker")
        para_end = lead.index("\n\n", para_at)
        begin_span = "`=== RELAY BEGIN <sid> to\nworker ===`"
        self.assertIn(begin_span, lead, "the lead's own wrap moved; "
                      "re-anchor this self-test's mutations")
        mutations = {
            "paragraph struck": lead[:para_at] + lead[para_end:],
            "addressed to planner": lead.replace(
                "to\nworker ===`", "to\nplanner ===`").replace(
                "to worker ===`", "to planner ===`"),
            "BEGIN and END swapped": lead.replace(
                "RELAY BEGIN", "RELAY @SWAP@").replace(
                "RELAY END", "RELAY BEGIN").replace(
                "RELAY @SWAP@", "RELAY END"),
            "BEGIN unbackticked": lead.replace(
                begin_span, begin_span.strip("`")),
        }
        for label, mutated in mutations.items():
            with self.subTest(mutation=label):
                self.assertNotEqual(mutated, lead, "mutation was a no-op")
                self.assertNotEqual(
                    relay_worker_gaps(mutated, self.begin, self.end), [])

    def test_section_lead_reads_7_lead_alone(self):
        """Self-test on the extractor, so the pin cannot pass by reading
        into 7.1–7.7 or past section 7."""
        lead = self._lead()
        self.assertIn("A HOLD reaches the worker", lead)
        self.assertNotRegex(lead, r"(?m)^#{2,6}\s",
                            "the 7 lead ran into a heading")
        self.assertNotIn("staging directory", lead)
        synthetic = ("## 6. Six\nsix\n## 7. Seven\nlead body\n"
                     "### 7.1 One\none body\n## 8. Eight\neight\n")
        self.assertEqual(section_lead(synthetic, 7), "\nlead body\n")
        self.assertEqual(section_lead("## 7. Seven\nonly lead\n", 7),
                         "\nonly lead\n")
        self.assertEqual(section_lead(synthetic, 9), "")

if __name__ == "__main__":
    unittest.main()
