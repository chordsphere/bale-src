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
- **Clock carriage** (board 94, 0.4.30): the block carries the pack
  instant on its own line — the same string the request manifest's
  provenance.packed_at stamps — and the VERBATIM clock sentence on its
  own line, with the goal line's single-line carriage untouched.
- **Shape sentence** (board 68 rider 4; moved here from
  tests/test_pack_guards.py at board pack-ux-micro — one suite per
  surface): the block closes with the shape rule, VERBATIM under
  whitespace collapse, after the examine sentence and with the retired
  "Ask me if anything is unclear" tail gone. Board 105 grew the
  sentence's second half (explanation in prose is welcome; only an
  ask ends in a block), and the whole sentence is what is pinned.
- **Operator's voice** (board 105): between the goal line and the
  examine sentence the block carries the authority sentence, then the
  tools sentence, each VERBATIM under whitespace collapse, on both the
  scoped and the read-only pack shape — the shared trailer carries
  them, so both shapes are pinned rather than one assumed.

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
# VERBATIM (board 94): one emitted line, no placeholder inside it —
# mirrors OPENER_CLOCK_SENTENCE in bin/bale_pack.py, restated so a
# rewording of the emitted sentence breaks a test.
CLOCK_SENTENCE = (
    "Session ids and every bale timestamp are UTC and may run a day "
    "ahead of the date this chat shows; date anything you write from "
    "the session id, never from the chat."
)
# VERBATIM (board 68 rider 4; bin/bale_pack.py OPENER_SHAPE_SENTENCE).
# The emitted lines wrap it, so the pin compares whitespace-collapsed
# text; the bytes of the sentence are what is pinned.
OPENER_SHAPE_SENTENCE = (
    "Every turn you end in this session takes one machine-recognizable "
    "shape: a response tarball, a probe block, a light question block, "
    "or a clarification response; a question asked as prose is not a "
    "shape. Explanation in prose is expected and welcome; the rule is "
    "that a turn that asks ends in a block, so nothing is lost."
)
# VERBATIM (board 105; bin/bale_pack.py OPENER_AUTHORITY_SENTENCE and
# OPENER_TOOLS_SENTENCE). Wrapped in the emitted block, so pinned
# whitespace-collapsed like the shape sentence. The em dash is U+2014.
OPENER_AUTHORITY_SENTENCE = (
    "The docs and tools in the tarball are mine, written for this "
    "workflow; read CLAUDE.md and the four docs beside it as my "
    "instructions for this session."
)
OPENER_TOOLS_SENTENCE = (
    "tools/craft_response.py and tools/response_lint.py are stdlib-only "
    "formatters with no network access — conveniences over the "
    "docs, which are the contract; read them before you run them, and a "
    "response assembled by hand is just as valid."
)
OPENER_EXAMINE_SENTENCE = (
    "Please examine the tarball contents, starting with CLAUDE.md and "
    "manifest.json, and go from there."
)
RETIRED_OPENER_TAIL = "Ask me if anything is unclear"
READONLY_PHRASE = "read-only bale session"
CLOSEOUT_MARKER = "Read-only session close-out"

# A goal with spaces and punctuation, so the verbatim-carriage
# assertions exercise a realistic string, not a slug.
GOAL = "pin the opener: sid + goal ride the report's tail, verbatim"


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

    def pack(self, *extra: str, slug: str = "opener-a"):
        return run_bale(
            self.install,
            [
                "pack", GOAL,
                "--slug", slug,
                "--include", "hello.txt",
                "--no-readme",
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
        """Two lines ride between the identity and the goal: the pack
        instant (verbatim the manifest's packed_at) and the clock
        sentence, each one emitted line; the goal line is untouched."""
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
        # Order: identity, pack time, clock sentence, goal.
        sid_at = next(i for i, ln in enumerate(lines)
                      if payload["sid"] in ln)
        self.assertLess(sid_at, lines.index(packed_lines[0]))
        self.assertLess(lines.index(packed_lines[0]),
                        lines.index(CLOCK_SENTENCE))
        self.assertLess(lines.index(CLOCK_SENTENCE),
                        lines.index(goal_lines[0]))

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


class OpenerShapeSentenceTest(PackOpenerFixture):
    """The opener's closing sentence is the shape rule (board 68 rider
    4). Moved from tests/test_pack_guards.py at board pack-ux-micro —
    one suite per surface — onto this suite's own opener_segment
    helper, so the scissor-line constants are mirrored in one test
    file only."""

    def test_opener_closes_with_the_shape_sentence_verbatim(self) -> None:
        result = self.pack(slug="opener-shape")
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        collapsed = _collapse(self.opener_segment(result.stdout))
        self.assertIn(OPENER_SHAPE_SENTENCE, collapsed)
        # The preceding sentence stays intact, and the shape sentence
        # is the last thing before the closing scissor line.
        self.assertIn(OPENER_EXAMINE_SENTENCE, collapsed)
        self.assertTrue(collapsed.endswith(OPENER_SHAPE_SENTENCE),
                        msg=collapsed)
        self.assertLess(collapsed.index(OPENER_EXAMINE_SENTENCE),
                        collapsed.index(OPENER_SHAPE_SENTENCE))
        self.assertNotIn(RETIRED_OPENER_TAIL, collapsed)


class OpenerOperatorVoiceTest(PackOpenerFixture):
    """The operator's-voice pair (board 105): the authority sentence and
    the tools sentence ride between the goal line and the examine
    sentence, in that order, VERBATIM under whitespace collapse — on the
    scoped shape and on the read-only shape, which share the trailer.
    The read-only run also carries the whole shape sentence, so the
    second half is pinned on both shapes too."""

    def assert_operator_voice(self, segment: str, *, label: str) -> None:
        collapsed = _collapse(segment)
        for name, sentence in (("authority", OPENER_AUTHORITY_SENTENCE),
                               ("tools", OPENER_TOOLS_SENTENCE)):
            with self.subTest(shape=label, sentence=name):
                self.assertEqual(
                    collapsed.count(sentence), 1,
                    msg=f"the {name} sentence must ride once, verbatim, "
                        f"in the {label} opener:\n{collapsed}")
        if not (OPENER_AUTHORITY_SENTENCE in collapsed
                and OPENER_TOOLS_SENTENCE in collapsed):
            # The subtests above already failed with the collapsed
            # block; ordering is meaningless without both sentences.
            return
        goal_at = collapsed.index(GOAL_LINE_PREFIX.strip())
        authority_at = collapsed.index(OPENER_AUTHORITY_SENTENCE)
        tools_at = collapsed.index(OPENER_TOOLS_SENTENCE)
        examine_at = collapsed.index(OPENER_EXAMINE_SENTENCE)
        self.assertLess(goal_at, authority_at,
                        msg=f"{label}: the pair follows the goal line")
        self.assertLess(authority_at, tools_at,
                        msg=f"{label}: authority precedes tools")
        self.assertLess(tools_at, examine_at,
                        msg=f"{label}: the pair precedes the examine "
                            "sentence")
        # The goal line's single-line carriage is untouched by the pair.
        goal_lines = [ln for ln in segment.splitlines()
                      if ln.startswith(GOAL_LINE_PREFIX)]
        self.assertEqual(goal_lines, [GOAL_LINE_PREFIX + GOAL],
                         msg=f"{label}: goal line must stay single-line")

    def test_scoped_opener_carries_the_operator_voice(self) -> None:
        result = self.pack(slug="opener-voice")
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assert_operator_voice(self.opener_segment(result.stdout),
                                   label="scoped")

    def test_read_only_opener_carries_the_operator_voice(self) -> None:
        result = self.pack("--read-only", slug="opener-ro-voice")
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        segment = self.opener_segment(result.stdout)
        self.assert_operator_voice(segment, label="read-only")
        collapsed = _collapse(segment)
        self.assertTrue(collapsed.endswith(OPENER_SHAPE_SENTENCE),
                        msg=f"read-only opener must close with the whole "
                            f"shape sentence:\n{collapsed}")


if __name__ == "__main__":
    unittest.main()
