#!/usr/bin/env python3
"""Hermetic E2E for pack's session opener (board 52; BALE.md §7.7).

Pack's successor is a chat message — the operator pastes an opening
paragraph into a fresh Claude chat with the request tarball attached.
Board 52 makes bale own, version, and emit that paragraph: the
end-of-run report ENDS with it as a paste-ready copy block framed by
scissor lines, carrying the session's identity (sid and goal,
verbatim) so the opener names what was just packed.

Pinned behaviors:

- **End-position**: the copy block is the last thing the human report
  prints — the final non-empty stdout line is the closing scissor
  line, on every pack shape.
- **Identity carriage**: the sid and the goal appear verbatim between
  the scissor lines, the goal riding a single unwrapped line.
- **Every shape**: the fully-specified path, the wizard path, and the
  read-only shape all emit the block; the read-only opener names the
  session read-only and still lands after the close-out trailer.
- **--json interplay**: stdout keeps its one-JSON-line contract; the
  opener rides stderr (json-mode stream discipline) and still ends
  the run there.
- **Clock carriage** (board 94, 0.4.30; reworded with the opener): the
  block carries the pack instant on its own line — the same string the
  request manifest's provenance.packed_at stamps — and the VERBATIM
  clock sentence on its own line, both after the goal line, whose
  single-line carriage is untouched.
- **The reworded opener** (the README-and-deliverable reword, which
  retired the examine and shape sentences): after the goal line, a
  paragraph of the authority sentence, the reading sentence, and the
  tools sentence; then the pack-time and clock lines; then a paragraph
  of the ask sentence and the deliverable sentence(s). The reading
  sentence names README.md as the brief exactly when a README ships;
  the deliverable is the planner form on a --read-only pack and the
  worker form otherwise. All four variants (worker/planner x
  README/no README) are pinned byte-exact under whitespace collapse,
  whole block, against the literals restated here — and the human
  report and the --json stream carry the same block per variant.
- **One copy of each sentence** (board 106): an in-process unit test
  calls ``session_opener_block`` directly on all four variants, asserts
  the module's sentence constants equal the literals restated here and
  that bin/bale_pack.py holds each sentence once — the emitted lines
  are cut from the constants, not restated beside them — and that the
  wrap breaks on whitespace only (``stdlib-only`` is never split).

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness
in ``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_pack_opener.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from harness import (
    _load_module,
    bale_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_bale_pty,
)

# Sentinels for the surfaces this file pins (one place per message).
# The scissor lines are the copy block's stable frame — these literals
# mirror OPENER_BEGIN / OPENER_END in bin/bale_pack.py, restated here
# so a silent rewording of the emitted frame breaks a test.
OPENER_BEGIN = (
    "--8<-- session opener (copy everything between the scissor lines)"
    " --8<--"
)
OPENER_END = "--8<-- end session opener --8<--"
GOAL_LINE_PREFIX = "Goal, verbatim from the request manifest: "
PACKED_LINE_PREFIX = "Packed at "
PACKED_LINE_SUFFIX = " (UTC)."
# VERBATIM: the opener's sentences, restated from the brief so a
# silent rewording of any emitted sentence breaks a test. They mirror
# the OPENER_*_SENTENCE constants in bin/bale_pack.py. The clock
# sentence rides one emitted line and is pinned as a line; the others
# ride wrapped paragraphs and are pinned whitespace-collapsed. The em
# dash in the tools sentence is U+2014.
CLOCK_SENTENCE = (
    "bale's dates are UTC and can run a day ahead of this chat's date "
    "(a timezone gap, not an error); date what you write from the "
    "session id."
)
OPENER_AUTHORITY_SENTENCE = (
    "The docs and tools in the tarball are mine, written for this "
    "workflow; CLAUDE.md and the four docs beside it are my instructions "
    "for this session."
)
OPENER_READING_WITH_README_SENTENCE = (
    "Read manifest.json first, then CLAUDE.md, then README.md, my brief "
    "for this session; CLAUDE.md says when the other four docs are "
    "needed."
)
OPENER_READING_NO_README_SENTENCE = (
    "Read manifest.json first, then CLAUDE.md; CLAUDE.md says when the "
    "other four docs are needed."
)
OPENER_TOOLS_SENTENCE = (
    "tools/craft_response.py and tools/response_lint.py are stdlib-only "
    "formatters with no network access — conveniences over the "
    "docs, which are the contract; read them before you run them, and a "
    "response assembled by hand is just as valid."
)
OPENER_ASK_SENTENCE = (
    "If you need something from me, a fact from my machine or a "
    "decision, end that turn with the matching block from TARBALL.md (a "
    "probe, a light question block, or a clarification response) rather "
    "than a question in prose, which tends to get lost."
)
OPENER_DELIVERABLE_WORKER_SENTENCE = (
    "This is a worker session: what I need back is one response tarball "
    "carrying the finished work."
)
OPENER_DELIVERABLE_PLANNER_SENTENCE = (
    "This is a planner session: nothing lands from it, so don't build a "
    "response tarball, even an empty one. What I need back is your "
    "answer in chat and, for each session I ask you to author, a crafter "
    "bundle with its bale open line, as PLANNER.md describes."
)
# The sentences the reword retired, by a fragment of each — none may
# come back. The old authority and clock wordings are retired too.
RETIRED_FRAGMENTS = (
    "Ask me if anything is unclear",
    "Please examine the tarball contents",
    "machine-recognizable shape",
    "read CLAUDE.md and the four docs beside it as my instructions",
    "Session ids and every bale timestamp are UTC",
)
USING_LINE = (
    "I'm using \"bale\", a CLI that packaged the attached request tarball.")
READONLY_PHRASE = "read-only bale session"
CLOSEOUT_MARKER = "Read-only session close-out"

# A goal with spaces and punctuation, so the verbatim-carriage
# assertions exercise a realistic string, not a slug.
GOAL = "pin the opener: sid + goal ride the report's tail, verbatim"
# A brief for the README variants — its content is irrelevant here; the
# opener keys only on whether one ships.
BRIEF_BODY = "# Brief — opener fixture\n\nProse the worker reads.\n"


def _collapse(text: str) -> str:
    """Whitespace-collapse, so a wrapped sentence compares verbatim."""
    return " ".join(text.split())


class PackOpenerFixture(unittest.TestCase):
    """Sandbox plumbing and opener helpers, holding no tests — so a
    second suite class (OpenerShapeSentenceTest) inherits the helpers
    without re-running PackOpenerBase's methods."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-opener-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack(self, *extra: str, slug: str = "opener-a",
             readme: bool = False):
        """Pack GOAL non-interactively. `readme` ships a brief through
        --readme-file; otherwise --no-readme declares none."""
        if readme:
            brief = self.tmp / f"brief-{slug}.md"
            brief.write_text(BRIEF_BODY, encoding="utf-8")
            readme_args = ["--readme-file", str(brief)]
        else:
            readme_args = ["--no-readme"]
        return run_bale(
            self.install,
            [
                "pack", GOAL,
                "--slug", slug,
                "--include", "hello.txt",
                *readme_args,
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def opener_segment(self, text: str) -> str:
        """The copy block: everything between the scissor lines.

        Asserts both lines are present and correctly ordered before
        slicing, so a failure names the missing frame rather than a
        cryptic -1 slice.
        """
        begin_at = text.find(OPENER_BEGIN)
        end_at = text.find(OPENER_END)
        self.assertGreaterEqual(
            begin_at, 0, msg=f"opening scissor line missing:\n{text}")
        self.assertGreaterEqual(
            end_at, 0, msg=f"closing scissor line missing:\n{text}")
        self.assertLess(
            begin_at, end_at,
            msg="scissor lines out of order — the frame is broken")
        return text[begin_at + len(OPENER_BEGIN):end_at]

    def assert_ends_with_opener(self, text: str, *, label: str) -> None:
        """The closing scissor line is the last non-empty line."""
        lines = [ln for ln in text.splitlines() if ln.strip()]
        self.assertTrue(lines, msg=f"{label} is empty:\n{text}")
        self.assertEqual(
            lines[-1], OPENER_END,
            msg=f"the opener must END the report on {label}; "
                f"last line was: {lines[-1]!r}")

    def newest_sid(self, text: str) -> str:
        """The packed sid, read from the report's own session id row."""
        for ln in text.splitlines():
            stripped = ln.strip()
            if stripped.startswith("session id:"):
                return stripped.split("session id:", 1)[1].strip()
        self.fail(f"no session id row in report:\n{text}")


class PackOpenerBase(PackOpenerFixture):
    """The opener's pinned behaviors 1-5 (the class name predates the
    fixture split and is kept so existing test ids do not move)."""

    # -- pinned behavior 1 + 2: end-position and identity carriage -------

    def test_report_ends_with_the_opener_block(self) -> None:
        """Fully-specified path: the human report's last non-empty
        line is the closing scissor line."""
        result = self.pack()
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assert_ends_with_opener(result.stdout, label="stdout")

    def test_opener_carries_sid_and_goal_verbatim(self) -> None:
        """The sid and the goal both appear inside the copy block —
        the goal verbatim on a single line."""
        result = self.pack()
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        sid = self.newest_sid(result.stdout)
        segment = self.opener_segment(result.stdout)
        self.assertIn(sid, segment,
                      msg="the opener must carry the sid")
        self.assertIn(GOAL, segment,
                      msg="the opener must carry the goal verbatim")
        goal_lines = [ln for ln in segment.splitlines()
                      if ln.startswith(GOAL_LINE_PREFIX)]
        self.assertEqual(
            len(goal_lines), 1,
            msg=f"exactly one goal line expected:\n{segment}")
        # Single-line carriage: the whole goal rides that one line,
        # unwrapped — a hard wrap would break verbatim substring match.
        self.assertEqual(goal_lines[0], GOAL_LINE_PREFIX + GOAL)

    # -- pinned behavior 5: clock carriage (board 94) --------------------

    def packed_at_of(self, tarball: Path) -> str:
        """provenance.packed_at as the packed request manifest stamps it."""
        with tarfile.open(tarball) as tf:
            member = next(m for m in tf.getmembers()
                          if m.name.endswith("/manifest.json"))
            manifest = json.load(tf.extractfile(member))
        return manifest["provenance"]["packed_at"]

    def test_opener_carries_pack_time_and_clock_sentence(self) -> None:
        """Two lines ride after the goal line: the pack instant
        (verbatim the manifest's packed_at) and the clock sentence, each
        one emitted line; the goal line is untouched."""
        result = self.pack("--json", slug="opener-clock")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout.strip().splitlines()[0])
        packed_at = self.packed_at_of(Path(payload["tarball"]))
        segment = self.opener_segment(result.stderr)
        lines = segment.splitlines()
        packed_lines = [ln for ln in lines
                        if ln.startswith(PACKED_LINE_PREFIX)]
        self.assertEqual(len(packed_lines), 1,
                         msg=f"exactly one pack-time line expected:\n{segment}")
        self.assertEqual(
            packed_lines[0],
            f"{PACKED_LINE_PREFIX}{packed_at}{PACKED_LINE_SUFFIX}",
            msg="the opener names the very instant provenance stamps")
        self.assertEqual(
            lines.count(CLOCK_SENTENCE), 1,
            msg=f"the clock sentence must ride as one verbatim line:\n{segment}")
        goal_lines = [ln for ln in lines if ln.startswith(GOAL_LINE_PREFIX)]
        self.assertEqual(goal_lines, [GOAL_LINE_PREFIX + GOAL],
                         msg="the goal line's single-line carriage is untouched")
        # Order: identity, goal, pack time, clock sentence — and the
        # clock line immediately follows the pack-time line.
        sid_at = next(i for i, ln in enumerate(lines)
                      if payload["sid"] in ln)
        self.assertLess(sid_at, lines.index(goal_lines[0]))
        self.assertLess(lines.index(goal_lines[0]),
                        lines.index(packed_lines[0]))
        self.assertEqual(lines.index(packed_lines[0]) + 1,
                         lines.index(CLOCK_SENTENCE))

    def test_read_only_opener_carries_the_clock_too(self) -> None:
        """The read-only shape emits the same two lines."""
        result = self.pack("--read-only", slug="opener-ro-clock")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        segment = self.opener_segment(result.stdout)
        self.assertIn(CLOCK_SENTENCE, segment.splitlines())
        self.assertTrue(any(ln.startswith(PACKED_LINE_PREFIX)
                            for ln in segment.splitlines()))

    # -- pinned behavior 3: every shape ----------------------------------

    def test_read_only_opener_names_the_shape_and_still_ends(self) -> None:
        """The read-only pack's opener names the session read-only and
        lands after the close-out trailer — the block still ends the
        report."""
        result = self.pack("--read-only", slug="opener-ro")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        segment = self.opener_segment(result.stdout)
        self.assertIn(READONLY_PHRASE, segment,
                      msg="the read-only opener must name the shape")
        self.assertIn(GOAL, segment)
        self.assert_ends_with_opener(result.stdout, label="stdout")
        # End-position beats the close-out: the read-only trailer's
        # close-out lines precede the opener, never follow it.
        closeout_at = result.stdout.find(CLOSEOUT_MARKER)
        opener_at = result.stdout.find(OPENER_BEGIN)
        self.assertGreaterEqual(closeout_at, 0, msg=result.stdout)
        self.assertLess(closeout_at, opener_at,
                        msg="the opener must come after the read-only "
                            "close-out, ending the report")

    def test_wizard_path_emits_the_opener(self) -> None:
        """The wizard path converges on the same report: sid + goal
        in the copy block, block at the end."""
        answers = (
            f"{GOAL}\n"       # goal
            "opener-wiz\n"    # slug
            "c\n"             # session shape: code
            "\n"              # forecast: Enter -> includes
            "\n" "\n" "\n"    # excludes, constraints, out-of-scope
            "n\n"             # README prompt: no
        )
        code, output = run_bale_pty(
            self.install, ["pack"], cwd=self.repo, env=self.env,
            answers=answers,
        )
        self.assertEqual(code, 0, msg=output)
        segment = self.opener_segment(output)
        self.assertIn(GOAL, segment)
        self.assertIn(self.newest_sid(output), segment)
        self.assert_ends_with_opener(output, label="the wizard pty run")

    # -- pinned behavior 4: --json interplay -----------------------------

    def test_json_stdout_stays_one_line_opener_rides_stderr(self) -> None:
        """--json keeps stdout at exactly one JSON line; the opener
        prints after it, on stderr, and ends that stream."""
        result = self.pack("--json", slug="opener-json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        stdout_lines = [ln for ln in result.stdout.splitlines() if ln]
        self.assertEqual(
            len(stdout_lines), 1,
            msg="json-mode stdout must stay exactly one line; the "
                f"opener rides stderr. stdout:\n{result.stdout}")
        payload = json.loads(stdout_lines[0])
        self.assertEqual(payload["outcome"], "packed")
        self.assertNotIn(OPENER_BEGIN, result.stdout)
        segment = self.opener_segment(result.stderr)
        self.assertIn(payload["sid"], segment)
        self.assertIn(GOAL, segment)
        self.assert_ends_with_opener(result.stderr, label="stderr")


def expected_collapsed_block(sid: str, packed_at: str, *,
                             read_only: bool, has_readme: bool) -> str:
    """The whole opener, between the scissor lines, whitespace-
    collapsed — built from this file's literals alone, never from the
    module, so it is the independent statement of each variant."""
    if read_only:
        identity = (f"This message opens read-only bale session {sid} "
                    "(empty write forecast: an orchestration/discussion "
                    "session — no changes land from it).")
    else:
        identity = f"This message opens bale session {sid}."
    reading = (OPENER_READING_WITH_README_SENTENCE if has_readme
               else OPENER_READING_NO_README_SENTENCE)
    deliverable = (OPENER_DELIVERABLE_PLANNER_SENTENCE if read_only
                   else OPENER_DELIVERABLE_WORKER_SENTENCE)
    return _collapse(" ".join((
        USING_LINE,
        identity,
        GOAL_LINE_PREFIX + GOAL,
        OPENER_AUTHORITY_SENTENCE,
        reading,
        OPENER_TOOLS_SENTENCE,
        f"{PACKED_LINE_PREFIX}{packed_at}{PACKED_LINE_SUFFIX}",
        CLOCK_SENTENCE,
        OPENER_ASK_SENTENCE,
        deliverable,
    )))


# The four variants: (label, read_only, has_readme).
VARIANTS = (
    ("worker, no README", False, False),
    ("worker, README", False, True),
    ("planner, no README", True, False),
    ("planner, README", True, True),
)


class OpenerVariantsTest(PackOpenerFixture):
    """The four opener variants, end to end: each pack's rendered block
    equals, whitespace-collapsed and whole, the block built from this
    file's literals; the human report and the --json stream carry the
    same block; and the retired sentences are gone."""

    def packed_at_of(self, sid: str) -> str:
        p = self.repo / ".bale" / "sessions" / sid / "manifest.json"
        return json.loads(p.read_text(encoding="utf-8"))[
            "provenance"]["packed_at"]

    def run_variant(self, *, read_only: bool, has_readme: bool,
                    json_mode: bool, slug: str):
        """Pack one variant; return (sid, packed_at, opener segment)."""
        extra = ["--read-only"] if read_only else []
        if json_mode:
            extra.append("--json")
        result = self.pack(*extra, slug=slug, readme=has_readme)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        if json_mode:
            sid = json.loads(result.stdout.strip().splitlines()[0])["sid"]
            text = result.stderr
        else:
            sid = self.newest_sid(result.stdout)
            text = result.stdout
        self.assert_ends_with_opener(
            text, label="stderr" if json_mode else "stdout")
        packed_at = self.packed_at_of(sid)
        # Close the session so the next variant's pack is not refused by
        # the forecast-disjointness gate (every variant forecasts
        # hello.txt).
        unlocked = run_bale(self.install, ["unlock", sid],
                            cwd=self.repo, env=self.env)
        self.assertEqual(unlocked.returncode, 0,
                         msg=f"unlock failed:\n{unlocked.stderr}")
        return sid, packed_at, self.opener_segment(text)

    def test_each_variant_is_the_pinned_block(self) -> None:
        for n, (label, read_only, has_readme) in enumerate(VARIANTS):
            with self.subTest(variant=label):
                sid, packed_at, segment = self.run_variant(
                    read_only=read_only, has_readme=has_readme,
                    json_mode=False, slug=f"opener-v{n}")
                self.assertEqual(
                    _collapse(segment),
                    expected_collapsed_block(sid, packed_at,
                                             read_only=read_only,
                                             has_readme=has_readme))
                collapsed = _collapse(segment)
                for fragment in RETIRED_FRAGMENTS:
                    self.assertNotIn(fragment, collapsed)
                # Line structure the collapse cannot see: the goal and
                # the clock sentence ride one emitted line each.
                lines = segment.splitlines()
                self.assertIn(GOAL_LINE_PREFIX + GOAL, lines)
                self.assertIn(CLOCK_SENTENCE, lines)

    def test_human_and_json_surfaces_agree(self) -> None:
        """Same variant, both surfaces: once the sid and pack instant
        (which differ per pack) are normalized, the blocks are
        byte-identical — the two call sites cannot drift."""
        for n, (label, read_only, has_readme) in enumerate(VARIANTS):
            with self.subTest(variant=label):
                blocks = []
                for json_mode in (False, True):
                    sid, packed_at, segment = self.run_variant(
                        read_only=read_only, has_readme=has_readme,
                        json_mode=json_mode,
                        slug=f"opener-s{n}{'j' if json_mode else 'h'}")
                    blocks.append(segment.replace(sid, "<sid>")
                                  .replace(packed_at, "<packed_at>"))
                self.assertEqual(blocks[0], blocks[1])

    def test_readme_sentence_keys_on_the_shipped_readme(self) -> None:
        """With a README the reading sentence names README.md as the
        brief; without one, the block never mentions README.md."""
        _, _, with_readme = self.run_variant(
            read_only=False, has_readme=True, json_mode=False,
            slug="opener-rd1")
        _, _, without = self.run_variant(
            read_only=False, has_readme=False, json_mode=False,
            slug="opener-rd0")
        self.assertIn(OPENER_READING_WITH_README_SENTENCE,
                      _collapse(with_readme))
        self.assertNotIn("README.md", without)


class OpenerConstantsInProcessTest(unittest.TestCase):
    """Board 106's one-copy rule, carried onto the reworded opener: the
    block is built from bin/bale_pack.py's sentence constants, pinned in
    process — no sandbox, no pack run. The E2E classes above pin the
    rendered text against this file's restated literals; this class pins
    the module's constants themselves, so the two cannot drift apart
    unnoticed."""

    SID = "2026-09-19-opener-constants-001"
    PACKED_AT = "2026-09-19T01:36:19+00:00"

    @classmethod
    def setUpClass(cls) -> None:
        cls.bp = _load_module("bale_pack")

    def block(self, *, read_only: bool, has_readme: bool) -> list:
        return self.bp.session_opener_block(
            self.SID, GOAL, read_only=read_only, packed_at=self.PACKED_AT,
            has_readme=has_readme)

    def segment(self, lines: list) -> list:
        begin = lines.index(self.bp.OPENER_BEGIN)
        end = lines.index(self.bp.OPENER_END)
        self.assertLess(begin, end)
        return lines[begin + 1:end]

    def test_module_constants_equal_the_pinned_literals(self) -> None:
        """The restated literals at the top of this file are the
        rewording guard; the module constants must be those bytes."""
        for name, pinned in (
                ("OPENER_BEGIN", OPENER_BEGIN),
                ("OPENER_END", OPENER_END),
                ("OPENER_CLOCK_SENTENCE", CLOCK_SENTENCE),
                ("OPENER_AUTHORITY_SENTENCE", OPENER_AUTHORITY_SENTENCE),
                ("OPENER_READING_WITH_README_SENTENCE",
                 OPENER_READING_WITH_README_SENTENCE),
                ("OPENER_READING_NO_README_SENTENCE",
                 OPENER_READING_NO_README_SENTENCE),
                ("OPENER_TOOLS_SENTENCE", OPENER_TOOLS_SENTENCE),
                ("OPENER_ASK_SENTENCE", OPENER_ASK_SENTENCE),
                ("OPENER_DELIVERABLE_WORKER_SENTENCE",
                 OPENER_DELIVERABLE_WORKER_SENTENCE),
                ("OPENER_DELIVERABLE_PLANNER_SENTENCE",
                 OPENER_DELIVERABLE_PLANNER_SENTENCE)):
            with self.subTest(constant=name):
                self.assertEqual(getattr(self.bp, name), pinned)

    def test_retired_constants_are_gone(self) -> None:
        for name in ("OPENER_EXAMINE_SENTENCE", "OPENER_SHAPE_SENTENCE",
                     "OPENER_VOICE_WORDS_PER_LINE",
                     "OPENER_CLOSING_WORDS_PER_LINE"):
            with self.subTest(constant=name):
                self.assertFalse(hasattr(self.bp, name))

    def test_each_variant_is_the_pinned_block(self) -> None:
        for label, read_only, has_readme in VARIANTS:
            with self.subTest(variant=label):
                collapsed = _collapse("\n".join(self.segment(
                    self.block(read_only=read_only,
                               has_readme=has_readme))))
                self.assertEqual(
                    collapsed,
                    expected_collapsed_block(self.SID, self.PACKED_AT,
                                             read_only=read_only,
                                             has_readme=has_readme))

    def test_each_sentence_has_one_copy_in_the_module_source(self) -> None:
        """The emitted lines are cut from the constants, never restated
        beside them: a fragment that sits inside one string literal of
        each constant occurs once in the file."""
        source = Path(self.bp.__file__).read_text(encoding="utf-8")
        for fragment in (
                "The docs and tools in the tarball are mine",
                "then README.md, my brief",
                "Read manifest.json first, then CLAUDE.md; CLAUDE.md",
                "response assembled by hand is just as valid.",
                "(a timezone gap, not an error)",
                "which tends to get lost.",
                "This is a worker session:",
                "This is a planner session:",
                "as PLANNER.md describes."):
            with self.subTest(fragment=fragment):
                self.assertEqual(source.count(fragment), 1)

    def test_wrap_width_and_whitespace_only_breaks(self) -> None:
        """Every wrapped line stays within the 70 columns (the goal and
        clock lines are single lines and exempt), and no line ends or
        begins mid-word — `stdlib-only`, the hyphenated word a
        hyphen-breaking wrap would split, rides whole on one line."""
        for label, read_only, has_readme in VARIANTS:
            with self.subTest(variant=label):
                segment = self.segment(self.block(
                    read_only=read_only, has_readme=has_readme))
                # The wrapped paragraphs follow the goal line; the
                # identity lines above it are fixed text (the read-only
                # two-liner predates the wrap and runs past 70 with a
                # full sid), so only the lines after the goal are
                # checked, as board 106's pin did.
                goal_at = next(i for i, ln in enumerate(segment)
                               if ln.startswith(GOAL_LINE_PREFIX))
                for line in segment[goal_at + 1:]:
                    if line == CLOCK_SENTENCE:
                        continue
                    self.assertLessEqual(len(line), 70, msg=line)
                self.assertTrue(
                    any("stdlib-only" in line.split() for line in segment),
                    msg="\n".join(segment))

    def test_opener_lines_breaks_on_whitespace_only(self) -> None:
        """The wrapper itself: a hyphenated word straddling the width
        moves whole to the next line, and a word longer than the width
        is never broken."""
        wrap = self.bp._opener_lines
        text = ("x" * 60) + " stdlib-only formatters"
        self.assertEqual(wrap(text),
                         ["x" * 60, "stdlib-only formatters"])
        long_word = "tools/" + ("y" * 80)
        self.assertEqual(wrap(f"a {long_word} b"), ["a", long_word, "b"])
        words = f"{OPENER_ASK_SENTENCE} {OPENER_DELIVERABLE_PLANNER_SENTENCE}"
        self.assertEqual(" ".join(wrap(words)).split(), words.split())


if __name__ == "__main__":
    unittest.main()
