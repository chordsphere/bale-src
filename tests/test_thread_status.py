#!/usr/bin/env python3
"""The exchange thread's direction on `bale status` and in the close-time
`clarification` summary (v0.4.18; BALE.md §5.5, §8.10.2, §8.11).

Extends test_clarification_status (v0.3.22's suspension row) with what
the thread adds, each on its own fixture:

- **After a worker record** (a preserved clarification manifest, the
  apply-side shape) the row reads `from worker … awaiting planner`, the
  state description and next-step hint name the planner and `bale
  relay`, and the json `session.clarification` object carries
  `from: worker`, `answers: null`, `awaiting: planner` — additively,
  beside the v0.3.22 keys.
- **After a planner record** the same surfaces flip: `from planner`,
  the answer count, `awaiting worker`, the hint says carry the block
  then `bale apply`; json `from: planner`, `answers: N`,
  `awaiting: worker`.
- **An unreadable latest record** degrades to a null side and a hint
  that still names relay and apply — never the orphan reading.
- **The close-time summary** (read_clarification_summary through a
  real `bale unlock` close) stamps `from` and `answers` on every
  records[] entry, `rounds` counting both sides, and the record still
  validates under telemetry-record.schema.json's loose envelope.
- **The pure classifier** (_session_state_and_hint) maps `awaiting` to
  the three hint shapes without touching disk — the ADR-0003 unit
  target.

Hermetic (ADR-0005): scratch install, scratch repo, records fabricated
directly under .bale/clarifications/<sid>/ in the shapes apply and
relay leave.

Run:  python3 -m unittest tests.test_thread_status -v
  or: python3 -m unittest discover -s tests -p 'test_thread_status.py'
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import re
import sys
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
)

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "bin"))
from bale_validate import validate_telemetry_record  # noqa: E402


def parse_single_json_line(stdout: str) -> dict:
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    if len(lines) != 1:
        raise AssertionError(f"expected one stdout line; got:\n{stdout}")
    return json.loads(lines[0])


def clarification_manifest(sid: str, n_questions: int = 2) -> dict:
    return {
        "session_id": sid,
        "responds_to": sid,
        "corrects": None,
        "response_kind": "clarification",
        "summary": "blocked (fixture)",
        "changes": [],
        "deferred": [],
        "validation_will_run": [],
        "claims": {},
        "questions": [
            {
                "question": f"q{i + 1}?",
                "context": "c",
                "default_assumption": "d",
                "why_blocked": "w",
            }
            for i in range(n_questions)
        ],
        "preserved_at": "2026-08-29T14:00:00+00:00",
    }


def planner_record(sid: str, round_no: int = 2, n_answers: int = 2) -> dict:
    return {
        "record_version": 1,
        "session_id": sid,
        "round": round_no,
        "from": "planner",
        "created_at": "2026-08-29T15:00:00+00:00",
        "answers": [
            {"question_round": 1, "question_index": i,
             "answer": "yes", "disposition": "as-recommended"}
            for i in range(n_answers)
        ],
        "preserved_at": "2026-08-29T15:00:01+00:00",
    }


def load_bale_module():
    """Load bin/bale by path as a module (not __main__) for the pure
    classifier. The file has no .py suffix, so the source loader is
    named explicitly; bin/ is on sys.path (above) for its sibling
    imports, and nothing runs at import — main() is guarded."""
    path = str(REPO_ROOT / "bin" / "bale")
    loader = importlib.machinery.SourceFileLoader("bale_under_test", path)
    spec = importlib.util.spec_from_file_location(
        "bale_under_test", path, loader=loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules["bale_under_test"] = module  # dataclasses resolve by name
    loader.exec_module(module)
    return module


def flat(text: str) -> str:
    """Collapse the summary block's wrapping so row values assert as
    one line."""
    return re.sub(r"\s+", " ", text)


class ThreadStatusTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-thread-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.git_env = git_env(self.home)
        result = run_bale(
            self.install,
            ["pack", "thread status goal", "--slug", "thread",
             "--include", "hello.txt", "--no-readme"],
            cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        root = self.repo / ".bale" / "sessions"
        self.sid = sorted(d.name for d in root.iterdir()
                          if (d / "open").is_file())[0]

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def fabricate(self, seq: int, record, raw: str = None) -> None:
        d = self.repo / ".bale" / "clarifications" / self.sid
        d.mkdir(parents=True, exist_ok=True)
        p = d / f"{seq:03d}.json"
        p.write_text(raw if raw is not None
                     else json.dumps(record, indent=2) + "\n",
                     encoding="utf-8")

    def status(self, *extra: str):
        r = run_bale(self.install, ["status", *extra],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r

    # -- after a worker record -------------------------------------------

    def test_awaiting_planner_after_worker_record(self) -> None:
        self.fabricate(1, clarification_manifest(self.sid, 2))
        out = flat(self.status().stdout)
        self.assertIn("clarification-suspended", out)
        self.assertIn("awaiting the planner", out)
        self.assertIn("from worker", out)
        self.assertIn("2 blocking questions", out)
        self.assertIn("awaiting planner", out)
        self.assertIn(f"bale relay {self.sid}", out)
        self.assertIn("bale apply", out)
        self.assertNotIn("abandoned", out)
        clar = parse_single_json_line(
            self.status("--json").stdout)["session"]["clarification"]
        self.assertEqual(clar["rounds"], 1)
        self.assertEqual(clar["questions"], 2)
        self.assertEqual(clar["from"], "worker")
        self.assertIsNone(clar["answers"])
        self.assertEqual(clar["awaiting"], "planner")

    # -- after a planner record ------------------------------------------

    def test_awaiting_worker_after_planner_record(self) -> None:
        self.fabricate(1, clarification_manifest(self.sid, 2))
        self.fabricate(2, planner_record(self.sid, 2, 2))
        out = flat(self.status().stdout)
        self.assertIn("clarification-suspended", out)
        self.assertIn("awaiting the worker", out)
        self.assertIn("round 2", out)
        self.assertIn("from planner", out)
        self.assertIn("2 answers", out)
        self.assertIn("awaiting worker", out)
        self.assertIn("carry round 2's paste block", out)
        self.assertIn("bale apply", out)
        payload = parse_single_json_line(self.status("--json").stdout)
        self.assertEqual(payload["session"]["state"], "clarification")
        clar = payload["session"]["clarification"]
        self.assertEqual(clar["rounds"], 2)
        self.assertEqual(clar["from"], "planner")
        self.assertEqual(clar["answers"], 2)
        self.assertEqual(clar["awaiting"], "worker")
        self.assertEqual(clar["latest_record"],
                         f".bale/clarifications/{self.sid}/002.json")

    # -- unreadable latest record ----------------------------------------

    def test_unreadable_latest_degrades_to_null_side(self) -> None:
        self.fabricate(1, clarification_manifest(self.sid, 1))
        self.fabricate(2, None, raw="{not json")
        out = flat(self.status().stdout)
        self.assertIn("clarification-suspended", out)
        self.assertIn("could not be read", out)
        self.assertIn("bale relay", out)
        self.assertIn("bale apply", out)
        self.assertNotIn("abandoned", out)
        clar = parse_single_json_line(
            self.status("--json").stdout)["session"]["clarification"]
        self.assertEqual(clar["rounds"], 2)
        self.assertIsNone(clar["from"])
        self.assertIsNone(clar["awaiting"])
        self.assertIsNone(clar["questions"])

    # -- the close-time summary ------------------------------------------

    def test_close_summary_stamps_side_and_answers(self) -> None:
        self.fabricate(1, clarification_manifest(self.sid, 2))
        self.fabricate(2, planner_record(self.sid, 2, 2))
        r = run_bale(self.install, ["unlock", self.sid],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        record = json.loads(
            (self.repo / "claude" / "telemetry" / f"{self.sid}.json")
            .read_text(encoding="utf-8"))
        self.assertEqual(validate_telemetry_record(record), [])
        clar = record["attempts"][-1]["clarification"]
        self.assertEqual(clar["rounds"], 2, "both sides count")
        by_n = {row["n"]: row for row in clar["records"]}
        self.assertEqual(by_n[1]["from"], "worker")
        self.assertEqual(by_n[1]["blocking_questions"], 2)
        self.assertIsNone(by_n[1]["answers"])
        self.assertEqual(by_n[1]["at"], "2026-08-29T14:00:00+00:00")
        self.assertEqual(by_n[2]["from"], "planner")
        self.assertIsNone(by_n[2]["blocking_questions"])
        self.assertEqual(by_n[2]["answers"], 2)


class PureClassifierTest(unittest.TestCase):
    """_session_state_and_hint with the v0.4.18 `awaiting` input."""

    @classmethod
    def setUpClass(cls):
        cls.bale = load_bale_module()

    def classify(self, awaiting, rounds=1):
        return self.bale._session_state_and_hint(
            "2026-08-29-x-001", False, True, True,
            awaiting=awaiting, rounds=rounds)

    def test_planner_side(self) -> None:
        state, desc, hint = self.classify("planner", 1)
        self.assertEqual(state, "clarification")
        self.assertIn("awaiting the planner", desc)
        self.assertIn("bale relay 2026-08-29-x-001", hint)
        self.assertIn("bale apply", hint)

    def test_worker_side(self) -> None:
        state, desc, hint = self.classify("worker", 2)
        self.assertEqual(state, "clarification")
        self.assertIn("awaiting the worker", desc)
        self.assertIn("carry round 2's paste block", hint)

    def test_unknown_side(self) -> None:
        state, desc, hint = self.classify(None, 2)
        self.assertEqual(state, "clarification")
        self.assertIn("could not be read", desc)
        self.assertIn("bale relay", hint)

    def test_branch_still_beats_clarification(self) -> None:
        state, _, _ = self.bale._session_state_and_hint(
            "2026-08-29-x-001", True, False, True, awaiting="planner")
        self.assertEqual(state, "held")

    def test_format_clarification_value_shapes(self) -> None:
        f = self.bale.format_clarification_value
        self.assertEqual(f(0), "none")
        self.assertEqual(
            f(1, 1, "p", latest_from="worker"),
            "round 1 — from worker: 1 blocking question; latest record p; "
            "awaiting planner")
        self.assertEqual(
            f(2, None, "p", latest_from="planner", answers=3),
            "round 2 — from planner: 3 answers; latest record p; "
            "awaiting worker")
        self.assertEqual(
            f(3, 1, None, latest_from="planner", answers=2),
            "round 3 — from planner: 1 blocking question, 2 answers; "
            "awaiting worker")
        self.assertEqual(f(1, None, "p"),
                         "round 1 — question count unreadable (see the "
                         "record); latest record p")


if __name__ == "__main__":
    unittest.main()
