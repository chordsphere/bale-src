#!/usr/bin/env python3
"""Global-doc self-containment guard (session 2026-08-14-006;
PLANNER.md joined the scanned set at 2026-08-16-planner-birth-003;
the injected tools and the citation shapes joined at
2026-08-31-global-doc-purge-004; the install-shipped schemas and
their own deny table joined at 2026-08-31-guard-deny-shapes-022;
the changelog-record schema and the hyphenated board shape joined at
2026-09-17-guard-maintenance-006).

The injected surface bale ships into every request is self-contained:
it cites only the five global docs — docs/CLAUDE.md, docs/TARBALL.md,
docs/DOCS.md, docs/CODE.md, docs/PLANNER.md — and never a project
doc (BALE.md §3.3 carries the doctrine). BALE.md, MASTER.md, and the
rest of bale-src's claude/ inventory are project-local; a pointer at
any of them inside an injected surface dangles in every project
except this repo. The scanned set is the five docs plus the two
injected tools — tools/craft_response.py and tools/response_lint.py,
the INJECTED_TOOLS pair (bin/bale is the list's one source; this
suite mirrors it) — because the tools ride beside the docs in every
request and carried dangling pointers of their own until the
2026-08-31 purge. The rule previously lived only in
claude/INDEX.md's "Tool design" entry — drill-down-gated and
structurally invisible to the sessions editing the globals, which is
exactly how citations drifted in. This suite is the mechanical pin.

The deny list has two halves. The first is literal substrings —
exact strings, one rationale each:

- ``BALE.md`` — never legal in an injected surface. Not a substring
  hazard: ``TARBALL.md`` ends in ``BALL.md``, not ``BALE.md``.
- ``MASTER.md`` — never legal in an injected surface.
- ``orchestration.md`` — bale-src's claude/context/orchestration.md;
  never legal in an injected surface. Since 2026-08-16 that file is
  a tombstone (its doctrine relocated into docs/PLANNER.md), which
  changes nothing here: the tombstone is still project-local, and
  the relocated content must stand without naming its old home.
- ``claude/INDEX.md`` — the citation-shaped reference to bale-src's
  own doc map. A bare ``INDEX.md`` stays legal everywhere: the
  globals use it as the generic project-map concept (DOCS.md §2,
  CLAUDE.md's read-paths), and that usage is deliberate.

The second half is citation *shapes* — the 2026-08-31 sitting
ratified that injected surfaces carry no evidence-ledger or board
citations, and those are numbered forms, not fixed strings, so this
half is necessarily patterns. The original "literal substrings, not
a heuristic" framing is amended honestly rather than quietly
outgrown: the substring half stays literal, and the pattern half is
kept to tightly anchored shapes (word-boundary + digits, no
fuzzier) so the false-positive surface stays near zero. It was two
shapes until 2026-09-17; the third, hyphenated board form carries one
extra anchor, the sid awareness, and is amended in here in the same
honest spirit rather than slipped in:

- ``evidence <digits>`` — the "(evidence N)" ledger citations. The
  bare word "evidence" stays legal; only the numbered form is a
  citation.
- ``board <digits>`` / ``board row <digits>`` — the board citations
  ("board 33", "board row 54", "board 49b"). The word-boundary
  anchor keeps "keyboard"/"dashboard" out; version strings
  ("v0.3.21") never match.
- ``board-<digits>`` / ``board-row-<digits>`` — the hyphenated board
  citation ("board-13c"), one hyphen away from the form above and
  the same citation (desk ruling, 2026-09-17). It needs one more
  anchor than its spaced twin, because session ids are kebab tokens
  that legitimately carry ``board-<digits>``
  (``2026-09-16-board-96-crafter-85-light-block-002``) and sids are
  lineage, not citations. The anchor is sid-aware by token, not by
  a fixed prefix: the match must begin a kebab token (no word
  character or hyphen before it), and no hyphen-separated segment
  between that start and ``board`` may open a ``YYYY-MM-DD-`` date.
  So a sid is tolerated wherever ``board-`` sits in its slug
  (``2026-09-17-fx-board-12-cleanup-003``) and however it is
  prefixed (``response-<sid>.tar.gz``, a checkpoint path), while a
  bare ``board-13c``, a parenthesized one, or an undated kebab
  fragment (``fx-board-12``) still fails. ``keyboard-1``/``onboard-3``
  stay out on the token-start anchor. The one known blind spot is a
  sid hard-wrapped at the hyphen before ``board`` — the line scan
  sees a bare ``board-<digits>`` there and fails it, which errs
  loud; re-wrap the sid. ``BoardHyphenAnchorTest`` pins both
  directions on specimens independent of the scanned tree.

A third half rides beside the substrings and the citation shapes:
the pointer class (the 2026-09-01 reachability cleanup). "the
(bale) tool's (own) (design) documentation" — every spelling, the
optional words optional — points at bale's repo-local operator
manual, which ships with no install and dangles from every other
project. Unlike the two halves above, this deny is matched over the
raw text with whitespace runs tolerated inside the phrase, because
its live specimen wrapped across two physical lines in a tool
docstring and was invisible to a line scan; the wrapped matcher
reports the line the match starts on. One sanction bounds the whole
guard: bin/, schemas/, and tools/ paths are sanctioned in the
request-carried docs and tools because they ship with the install
and resolve wherever it exists; repo-local doc names do not and are
denied.

The third scan group is the install-shipped schemas — the five
non-embedded schemas the 2026-08-31 schema purge (board row 66,
session ...-board-66-schema-purge-015) made self-contained:
request-manifest, telemetry-record, escalation-record,
exchange-record, bundle-manifest — plus changelog-record, which
landed self-contained at v0.4.35 and joined the group at
2026-09-17-guard-maintenance-006 (the docstring's own instruction:
the group is updated alongside the schemas tree, and the schema
ships with every install). They are not injected into
requests, but they ship with every bale install and are reachable
from any project the same way the tools pair is, so a project-local
citation in a schema description dangles everywhere except this
repo. diagnostics and response-manifest are embedded-family and
deliberately outside this group: response-manifest still carries
pre-purge citations (and tools/response_lint.py vendors one of its
descriptions), so it joins only after its own purge lands — and
that purge must land on the vendored copy in the same change, or
this group's shapes can never converge with the tools group's.

The schema group's deny table is the purge's ratified seven,
reconstructed from the purge brief plus its session notes and
ratified by the planner in this session's exchange thread (round 2,
preserved under .bale/clarifications/): the board and evidence
numbered forms, the literals ``BALE.md`` and ``orchestration.md``,
the S-digit sitting form, session-letter residue (``session A`` …
``session D``), and the standalone letter-digit token — the purge's
own broadening, which subsumes the S-digit form and is kept beside
it so a failure names the ratified shape it violated. One
mechanism note: the ratified text reads "board followed by digits";
this table reuses the docs group's row-tolerant anchor (``board
row 66`` is the purge's own citation form), which is strictly
wider. A second mechanism note, from 2026-09-17: the hyphenated
board row (``board-<digits>``, sid-aware, half two above) rides in
this table too, as the same shared compiled pattern. That is the
ratified board form widened by one hyphen per the desk ruling that
the guard catch it — the board row this table already carries, not
a step toward convergence; every other row stays per-surface. There is deliberately NO dated-citation shape: the purge's
one dated rewrite was editorial judgment beyond the literal deny
set, and any date anchor collides with created_at and session-id
examples in the scanned files. ADR-number and PLANNER.md-section
citations are house style, ratified exempt — no shape here matches
them, and that is by design, not oversight.

The two deny tables are per-surface and stay that way until a
sitting ratifies convergence. The collision inventory that keeps
them apart, as of this session: schema-side, the docs group's board
form correctly fails post-purge drift (board 63/44 citations
reintroduced into telemetry-record the same day the purge applied —
specimen one for this guard's existence, purged again by the
session that added this group); docs-and-tools-side, PLANNER.md
carries S6 provisional-doctrine markers, tools/response_lint.py
carries B1/B2 session letters, and TARBALL.md's session-id examples
sit adjacent to any loosely anchored date shape. A merged table
fails the tree in both directions.

Hermetic and stdlib-only: the files are read from this repo; nothing
runs.

Run:  python3 -m unittest tests.test_global_doc_selfcontainment -v
  or: python3 -m unittest discover -s tests -p 'test_global_doc_selfcontainment.py'
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

GLOBAL_DOCS = ("CLAUDE.md", "TARBALL.md", "DOCS.md", "CODE.md",
               "PLANNER.md")

# Mirror of bin/bale's INJECTED_TOOLS — the pair injected beside the
# docs into every request (TARBALL.md §3.1). Update both together if
# the injected set changes.
INJECTED_TOOLS = ("craft_response.py", "response_lint.py")

# Every scanned file, repo-relative. The guard covers the whole
# injected surface: the five docs and the two tools.
SCANNED_FILES = tuple(f"docs/{name}" for name in GLOBAL_DOCS) + tuple(
    f"tools/{name}" for name in INJECTED_TOOLS)

# Half one: literal substrings that must never appear in an injected
# surface. Keep this half exact strings; the module docstring carries
# the rationale per entry.
DENIED_SUBSTRINGS = (
    "BALE.md",
    "MASTER.md",
    "orchestration.md",
    "claude/INDEX.md",
)

# The hyphenated board citation, sid-aware (docstring, half two, carries
# the design): a match must open a kebab token — nothing word-like or a
# hyphen before it — and no hyphen-separated segment between that token
# start and "board" may open a YYYY-MM-DD- date, so a session id carrying
# board-<digits> anywhere in its slug, however prefixed, never matches.
# One compiled object shared by both deny tables, so they cannot drift.
BOARD_HYPHEN_LABEL = "board-<digits> / board-row-<digits> (sid-aware)"
BOARD_HYPHEN_PATTERN = re.compile(
    r"(?<![\w-])"                          # opens a kebab token
    r"(?:(?!\d{4}-\d{2}-\d{2}-)\w+-)*"     # undated leading segments only
    r"board(?:-row)?-\d")

# Half two: citation shapes — numbered forms with no literal spelling.
# Keep each pattern tightly anchored (docstring carries the honesty
# note on why this half is patterns); label first, so failures read.
DENIED_PATTERNS = (
    ("evidence <digits>", re.compile(r"\bevidence \d")),
    ("board <digits> / board row <digits>",
     re.compile(r"\bboard(?: row)? \d")),
    (BOARD_HYPHEN_LABEL, BOARD_HYPHEN_PATTERN),
)

# Half three: the pointer class — matched over the whole text, with
# whitespace runs (including line wraps) tolerated between words, so
# a wrapped instance cannot hide from a line scan (docstring carries
# the rationale and the live wrapped specimen's story). Both
# apostrophes are tolerated; "bale", "own", and "design" are each
# optional so every observed spelling of the phrase is one shape.
DENIED_WRAPPED_PATTERNS = (
    ("(bale) tool's (own) (design) documentation",
     re.compile(r"(?:bale\s+)?tool['\u2019]s\s+(?:own\s+)?"
                r"(?:design\s+)?documentation")),
)

# The third scan group: the five non-embedded install-shipped schemas
# the 2026-08-31 schema purge made self-contained, plus changelog-record
# (landed self-contained at v0.4.35) (docstring carries
# the group's rationale and why diagnostics/response-manifest stay
# out). Update alongside the schemas tree if the install set changes.
INSTALL_SCHEMAS = ("request-manifest", "telemetry-record",
                   "escalation-record", "exchange-record",
                   "bundle-manifest", "changelog-record")

SCANNED_SCHEMAS = tuple(
    f"schemas/{name}.schema.json" for name in INSTALL_SCHEMAS)

# The schema group's deny table: the purge's ratified seven, kept
# per-surface from the docs-and-tools tables above (docstring carries
# the collision inventory that keeps them apart). Literal substrings
# first, patterns second, same split discipline as the first group.
SCHEMA_DENIED_SUBSTRINGS = (
    "BALE.md",
    "orchestration.md",
)

SCHEMA_DENIED_PATTERNS = (
    ("board <digits> / board row <digits>",
     re.compile(r"\bboard(?: row)? \d")),
    (BOARD_HYPHEN_LABEL, BOARD_HYPHEN_PATTERN),
    ("evidence <digits>", re.compile(r"\bevidence \d")),
    ("S<digit> sitting form", re.compile(r"\bS[0-9]\b")),
    ("session <letter> residue", re.compile(r"\bsession [A-D]\b")),
    ("standalone letter-digit token", re.compile(r"\b[A-Z][0-9]\b")),
)


def occurrences(text: str, matcher) -> list:
    """Return (1-based line number, line) for every line the matcher
    hits — the failure message needs locations, not a count. The
    matcher is a callable line -> bool, so substrings and patterns
    share one scan."""
    return [
        (i, line)
        for i, line in enumerate(text.splitlines(), start=1)
        if matcher(line)
    ]


def wrapped_occurrences(text: str, pattern) -> list:
    """Return (1-based line number of the match start, matched text
    with whitespace runs collapsed to single spaces) for every hit of
    a full-text pattern — the wrap-tolerant twin of `occurrences`,
    for the deny shapes a line scan cannot see."""
    return [
        (text.count("\n", 0, m.start()) + 1, " ".join(m.group(0).split()))
        for m in pattern.finditer(text)
    ]


class GlobalDocSelfContainment(unittest.TestCase):
    """No injected surface references a bale-src project doc or
    carries a project citation shape."""

    def test_all_global_docs_present(self):
        """The guard is only meaningful if it actually reads the whole
        injected surface — a moved or renamed file must fail here, not
        silently drop out of the scan."""
        for rel in SCANNED_FILES:
            with self.subTest(file=rel):
                self.assertTrue(
                    (REPO / rel).is_file(),
                    f"{rel} is missing — the injected set moved or "
                    "shrank; update SCANNED_FILES (and BALE.md §3.3 / "
                    "bin/bale's INJECTED_TOOLS) together if that was "
                    "deliberate")

    INJECTED_DOCTRINE = (
        "injected surfaces are self-contained and cite only the "
        "five global docs (BALE.md §3.3); state the lesson "
        "self-standingly and keep provenance project-side")

    SCHEMA_DOCTRINE = (
        "install-shipped schemas are self-contained — they travel "
        "with every bale install, so a project citation in a "
        "description dangles from every other project's vantage; "
        "anchor epochs to versions and keep provenance project-side "
        "(the 2026-08-31 purge's idiom)")

    def _assert_clean(self, rel: str, label: str, matcher,
                      doctrine: str = INJECTED_DOCTRINE):
        path = REPO / rel
        if not path.is_file():
            return  # the presence tests own this failure
        text = path.read_text(encoding="utf-8")
        hits = occurrences(text, matcher)
        listing = "\n".join(
            f"  line {n}: {line.strip()}" for n, line in hits)
        self.assertEqual(
            hits, [],
            f"{rel} carries project-local citation {label!r} — "
            f"{doctrine}:\n{listing}")

    def test_no_project_local_citations(self):
        for rel in SCANNED_FILES:
            for needle in DENIED_SUBSTRINGS:
                with self.subTest(file=rel, needle=needle):
                    self._assert_clean(
                        rel, needle, lambda line, n=needle: n in line)

    def test_no_citation_shapes(self):
        for rel in SCANNED_FILES:
            for label, pattern in DENIED_PATTERNS:
                with self.subTest(file=rel, shape=label):
                    self._assert_clean(
                        rel, label,
                        lambda line, p=pattern: p.search(line) is not None)

    def test_no_wrapped_pointer_shapes(self):
        """The pointer class, matched wrap-tolerantly over the whole
        text (module docstring, half three) — an instance split
        across physical lines fails here with the line its match
        starts on."""
        for rel in SCANNED_FILES:
            for label, pattern in DENIED_WRAPPED_PATTERNS:
                with self.subTest(file=rel, shape=label):
                    path = REPO / rel
                    if not path.is_file():
                        continue  # the presence tests own this failure
                    text = path.read_text(encoding="utf-8")
                    hits = wrapped_occurrences(text, pattern)
                    listing = "\n".join(
                        f"  line {n}: {snippet}" for n, snippet in hits)
                    self.assertEqual(
                        hits, [],
                        f"{rel} carries the unreachable-doc pointer "
                        f"{label!r} — {self.INJECTED_DOCTRINE}; re-point "
                        "at an install-shipped surface (bin/, schemas/, "
                        f"tools/) or a bale verb instead:\n{listing}")

    def test_all_scanned_schemas_present(self):
        """Same meaningfulness rule as the injected surface: a moved
        or renamed schema must fail here, not silently drop out."""
        for rel in SCANNED_SCHEMAS:
            with self.subTest(file=rel):
                self.assertTrue(
                    (REPO / rel).is_file(),
                    f"{rel} is missing — the install-shipped schema "
                    "set moved or shrank; update INSTALL_SCHEMAS "
                    "(and the install/build/upgrade layout lists) "
                    "together if that was deliberate")

    def test_no_schema_project_local_citations(self):
        for rel in SCANNED_SCHEMAS:
            for needle in SCHEMA_DENIED_SUBSTRINGS:
                with self.subTest(file=rel, needle=needle):
                    self._assert_clean(
                        rel, needle, lambda line, n=needle: n in line,
                        doctrine=self.SCHEMA_DOCTRINE)

    def test_no_schema_citation_shapes(self):
        for rel in SCANNED_SCHEMAS:
            for label, pattern in SCHEMA_DENIED_PATTERNS:
                with self.subTest(file=rel, shape=label):
                    self._assert_clean(
                        rel, label,
                        lambda line, p=pattern: p.search(line)
                        is not None,
                        doctrine=self.SCHEMA_DOCTRINE)


class BoardHyphenAnchorTest(unittest.TestCase):
    """The sid-aware hyphenated board anchor, graded both directions on
    specimens that do not depend on the scanned tree — a clean tree
    proves only that nothing is there to catch, never that the shape
    would catch it (module docstring, half two, carries the design)."""

    # Citations: every one must match.
    CITATIONS = (
        # The live leftover this shape was ruled in to catch, verbatim
        # from tools/craft_response.py before its rewrite.
        "    Separable (fold-in: board-13c via the registry): `--fragment`",
        "board-13c",
        "(board-13c)",
        "see board-row-54 for the ruling",
        "claude/board-7 notes",
        "the board-50 fold-in",
        "an undated kebab fragment fx-board-12 is not a sid",
        "a date apart from it is no sid: 2026-09-16 board-13c",
        "board-13c beside a sid 2026-09-16-board-96-x-002",
    )

    # Session ids and look-alikes: none may match.
    TOLERATED = (
        # The live sid in tools/craft_response.py, verbatim.
        "# session (2026-09-16-board-96-crafter-85-light-block-002).",
        "2026-09-16-board-96-crafter-85-light-block-002",
        "2026-09-17-fx-board-12-cleanup-003",
        "2026-09-16-board-row-54-fold-001",
        "response-2026-09-16-board-96-crafter-85-light-block-002.tar.gz",
        "claude/checkpoints/2026-09-16-board-96-x-002.sh",
        "keyboard-1",
        "dashboard-2 widget",
        "onboard-3",
        "billboard-9",
        "board-level decision",
        "v0.3.21",
    )

    def test_citations_match(self):
        for text in self.CITATIONS:
            with self.subTest(text=text):
                self.assertIsNotNone(
                    BOARD_HYPHEN_PATTERN.search(text),
                    f"hyphenated board citation not caught: {text!r}")

    def test_session_ids_and_lookalikes_tolerated(self):
        for text in self.TOLERATED:
            with self.subTest(text=text):
                match = BOARD_HYPHEN_PATTERN.search(text)
                self.assertIsNone(
                    match,
                    f"sid or look-alike flagged as a citation: {text!r} "
                    f"(matched {match.group(0) if match else ''!r})")

    def test_both_deny_tables_carry_the_shared_row(self):
        """One compiled object in both tables, so the docs-and-tools
        and schema groups cannot drift on this row."""
        for name, table in (("DENIED_PATTERNS", DENIED_PATTERNS),
                            ("SCHEMA_DENIED_PATTERNS",
                             SCHEMA_DENIED_PATTERNS)):
            with self.subTest(table=name):
                rows = [p for label, p in table
                        if label == BOARD_HYPHEN_LABEL]
                self.assertEqual(len(rows), 1)
                self.assertIs(rows[0], BOARD_HYPHEN_PATTERN)

    def test_changelog_schema_is_scanned(self):
        """changelog-record ships with every install (v0.4.35), so it
        rides in the schema group — and the presence test then fails
        loud if it moves."""
        self.assertIn("schemas/changelog-record.schema.json",
                      SCANNED_SCHEMAS)


if __name__ == "__main__":
    unittest.main()
