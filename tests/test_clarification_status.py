#!/usr/bin/env python3
"""Hermetic E2E for the clarification-suspended `bale status` state
(v0.3.22, board 32).

Pins BALE.md §5.5 / §8.10.2's status contract for a suspended session:
a session with preserved records under ``.bale/clarifications/<sid>/``
and no ``bale/<sid>`` branch classifies as its own lifecycle state —
``clarification`` — instead of the ``packed`` misreading (the request
tarball usually still sits in the outbox) or, with the outbox cleaned,
the ``orphan`` misreading whose hint (`bale unlock`) would discard the
suspension. The state carries a dedicated human row (rounds,
blocking-question count, latest record path) and a next-step hint
(answer, then apply the follow-up response); the json report carries
the state on the session enum and the facts under the additive
``session.clarification`` key (contract owned by format_status_json's
docstring in bin/bale_report.py).

The suite asserts:

- a packed session with a preserved clarification record reports state
  ``clarification``, the dedicated row, the answer-then-apply hint, and
  the json facts (rounds / questions / latest_record) — and stays open;
- a packed session without records is unchanged (state ``packed``,
  ``session.clarification`` null) — the additive-key regression guard;
- a ``bale/<sid>`` branch outranks the clarification state (a normal
  response later applied and hit HOLD — the round is history), while
  the json facts object still rides along;
- a record that will not parse still counts as a suspension round, with
  the question count degrading to unknown (null / "unreadable"), never
  a crash and never a silent drop;
- repeat rounds count, and the latest record wins the pointer.

The clarification state is fabricated on disk rather than driven
through a full `bale apply` of a clarification tarball — the same
fabricate-the-state precedent test_revert_json.py's make_held_session
sets — because the state under test is exactly what apply's §8.10.2
handler leaves behind: preserved record(s), lock held, no branch.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_clarification_status.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harness import (
    bale_env,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_checked,
)


def parse_single_json_line(stdout: str) -> dict:
    """The stream-discipline assertion in one place: stdout is exactly
    one non-empty line, and that line parses as a JSON object."""
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    if len(lines) != 1:
        raise AssertionError(
            f"expected exactly one stdout line under --json; got "
            f"{len(lines)}:\n{stdout}")
    payload = json.loads(lines[0])
    if not isinstance(payload, dict):
        raise AssertionError(f"stdout line is not a JSON object: {lines[0]}")
    return payload


def clarification_manifest(sid: str, n_questions: int = 2) -> dict:
    """A minimal preserved clarification manifest, shaped like the real
    thing apply preserves (TARBALL.md §5.9.2): response_kind
    clarification, empty change surfaces, four-field questions[]."""
    return {
        "session_id": sid,
        "responds_to": sid,
        "corrects": None,
        "response_kind": "clarification",
        "summary": "blocked on intent-gap questions (test fixture)",
        "changes": [],
        "deferred": [],
        "validation_will_run": [],
        "claims": {},
        "questions": [
            {
                "question": f"test question {i + 1}?",
                "context": "test context",
                "default_assumption": "test assumption",
                "why_blocked": "test blocker",
            }
            for i in range(n_questions)
        ],
    }


class ClarificationStatusTest(unittest.TestCase):
    """`bale status` on a clarification-suspended session."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-clarstatus-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.git_env = git_env(self.home)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def git(self, *args: str) -> None:
        run_checked(["git", *args], cwd=self.repo, env=self.git_env)

    def pack(self):
        return run_bale(
            self.install,
            [
                "pack", "clarification status test goal",
                "--slug", "clarstatus",
                "--include", "hello.txt",
                "--no-readme",
            ],
            cwd=self.repo,
            env=self.env,
        )

    def status(self, *extra: str):
        return run_bale(self.install, ["status", *extra],
                        cwd=self.repo, env=self.env)

    def assert_ok(self, result) -> None:
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        entries = [d for d in root.iterdir() if (d / "open").is_file()]
        entries.sort(key=lambda d: (d.stat().st_mtime, d.name))
        return [d.name for d in entries]

    def make_packed_session(self) -> str:
        result = self.pack()
        self.assert_ok(result)
        sids = self.open_sids()
        self.assertTrue(sids, msg="pack succeeded but no session is open")
        return sids[-1]

    def fabricate_record(self, sid: str, seq: int = 1,
                         n_questions: int = 2,
                         raw: str = None) -> Path:
        """Write .bale/clarifications/<sid>/<seq>.json — the state
        apply's §8.10.2 handler leaves behind. `raw` overrides the
        body for the malformed-record case."""
        clar_dir = self.repo / ".bale" / "clarifications" / sid
        clar_dir.mkdir(parents=True, exist_ok=True)
        record = clar_dir / f"{seq:03d}.json"
        if raw is not None:
            record.write_text(raw, encoding="utf-8")
        else:
            record.write_text(
                json.dumps(clarification_manifest(sid, n_questions),
                           indent=2) + "\n",
                encoding="utf-8",
            )
        return record

    # -- pinned behavior 1: the suspended state --------------------------

    def test_suspended_session_classifies_distinctly(self) -> None:
        sid = self.make_packed_session()
        record = self.fabricate_record(sid, n_questions=2)

        result = self.status("--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["sid"], sid)
        self.assertEqual(payload["session"]["state"], "clarification")
        clar = payload["session"]["clarification"]
        self.assertIsNotNone(clar, msg="clarification facts missing")
        self.assertEqual(clar["rounds"], 1)
        self.assertEqual(clar["questions"], 2)
        self.assertEqual(
            clar["latest_record"],
            str(record.relative_to(self.repo)),
        )
        # The suspension keeps the session open — status must agree.
        self.assertIn(sid, payload["sessions"])

    def test_human_row_and_hint(self) -> None:
        sid = self.make_packed_session()
        self.fabricate_record(sid, n_questions=1)

        result = self.status()
        self.assert_ok(result)
        out = result.stdout
        self.assertIn("clarification-suspended", out)
        self.assertIn("clarification:", out)
        self.assertIn("round 1", out)
        self.assertIn("1 blocking question", out)
        self.assertIn(f".bale/clarifications/{sid}", out)
        # The trailer hint carries the answer-then-apply path, and never
        # the orphan reading's discard hint.
        self.assertIn("answer the questions", out)
        self.assertIn("bale apply", out)
        self.assertNotIn("abandoned", out)

    # -- pinned behavior 2: the no-record regression guard ---------------

    def test_packed_without_records_unchanged(self) -> None:
        self.make_packed_session()
        result = self.status("--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["session"]["state"], "packed")
        self.assertIsNone(payload["session"]["clarification"])

    # -- pinned behavior 3: precedence -----------------------------------

    def test_held_outranks_clarification(self) -> None:
        sid = self.make_packed_session()
        self.fabricate_record(sid)
        # Fabricate the HOLD footprint (test_revert_json precedent): a
        # bale/<sid> branch with a session commit, checkout back on main.
        branch = f"bale/{sid}"
        self.git("checkout", "-b", branch)
        (self.repo / "widget.txt").write_text("bale change\n",
                                              encoding="utf-8")
        self.git("add", "widget.txt")
        self.git("commit", "-m", f"[bale {sid}] add the widget file")
        self.git("checkout", "main")

        result = self.status("--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["session"]["state"], "held")
        # The round is history, not the live state — but it is still a
        # fact, and the facts object rides along.
        clar = payload["session"]["clarification"]
        self.assertIsNotNone(clar)
        self.assertEqual(clar["rounds"], 1)

    # -- pinned behavior 4: degradation ----------------------------------

    def test_malformed_record_still_suspends(self) -> None:
        sid = self.make_packed_session()
        self.fabricate_record(sid, raw="{not json\n")

        result = self.status("--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        # Presence is the suspension fact; only the count degrades.
        self.assertEqual(payload["session"]["state"], "clarification")
        clar = payload["session"]["clarification"]
        self.assertEqual(clar["rounds"], 1)
        self.assertIsNone(clar["questions"])

        human = self.status()
        self.assert_ok(human)
        self.assertIn("question count unreadable", human.stdout)

    # -- pinned behavior 5: repeat rounds --------------------------------

    def test_repeat_rounds_count_and_latest_wins(self) -> None:
        sid = self.make_packed_session()
        self.fabricate_record(sid, seq=1, n_questions=2)
        latest = self.fabricate_record(sid, seq=2, n_questions=3)

        result = self.status("--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        clar = payload["session"]["clarification"]
        self.assertEqual(clar["rounds"], 2)
        self.assertEqual(clar["questions"], 3)
        self.assertEqual(
            clar["latest_record"],
            str(latest.relative_to(self.repo)),
        )


if __name__ == "__main__":
    unittest.main()
