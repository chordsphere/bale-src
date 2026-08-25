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

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness
in ``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_pack_opener.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
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
READONLY_PHRASE = "read-only bale session"
CLOSEOUT_MARKER = "Read-only session close-out"

# A goal with spaces and punctuation, so the verbatim-carriage
# assertions exercise a realistic string, not a slug.
GOAL = "pin the opener: sid + goal ride the report's tail, verbatim"


class PackOpenerBase(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
