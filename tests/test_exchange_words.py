"""The words bale prints for whoever answers a clarification.

Session 2026-11-11-exchange-words-002 (0.4.58), from two slips:

- bale's own next step at a clarification's landing told the reader to
  answer "in the worker's chat", which TARBALL.md 5.9.1 calls the breach
  case; the answer path is the exchange thread, and its verb is
  `bale relay <sid> <answer.json|->` (TARBALL.md 5.9.4, BALE.md 8.10.2
  step 4);
- the exchange block's planner-facing header named `bale relay` bare,
  which is the wrong verb for a planner reading a block some tool that
  wraps bale carried; the header now says to record the answer with the
  relay of the tool that carried the block, and still names bale's.

What this suite pins:

1. The header line, verbatim, from both renderers (bin/bale_relay.py's
   format_exchange_block and the crafter's re-declaration), with and
   without answers, and the worker-facing line unchanged.
2. The landing's trailer (bale_report.clarification_next_step_trailer,
   printed by print_clarification_banner) and the dry-run's next step:
   no "worker's chat", and the relay line with the real sid standing on
   a line of its own.
3. End to end: a real pack, a dry-run and a real apply of a clarification
   tarball; `bale relay <sid>` alone afterwards re-emits the landed round
   with the pinned header; and a block the crafter renders from a
   clarification manifest still ingests through `bale relay <sid> FILE`
   and is kept as round 1.

Sandbox doctrine per ADR-0005 (fully hermetic): the shared harness in
tests/harness.py carries it.

Run directly::

    python3 tests/test_exchange_words.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness import (
    REPO_ROOT,
    _load_module,
    bale_env,
    build_response_dir,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    tar_response_dir,
)

CRAFT = REPO_ROOT / "tools" / "craft_response.py"
SID = "2026-11-11-x-001"

# The brief's pinned line (outcome 3) with SID, N and the rounds filled
# in. The bytes are the brief's; only the placeholders vary.
PINNED = ("# {n} blocking question(s){a}. Planner: answer as an exchange "
          "record (from: planner, round {nxt}, answers[] keyed "
          "question_round {rnd}) and record it with the relay of the tool "
          "that carried this block (bale's own: `bale relay {sid} "
          "<answer.json|->`).")

# The worker-facing line as it read before this session, unchanged.
WORKER_FACING = ("# 1 answer(s). Worker: read the record, continue under "
                 "{sid}, and ship the normal response the clarification "
                 "deferred.")

RELAY_LINE = "bale relay {sid} <answer.json|->"

QUESTION = {
    "question": "Which config governs?",
    "context": "wiring the lint step",
    "default_assumption": "the repo-root config",
    "why_blocked": "the brief names both",
}


def pinned(sid: str, rnd: int, n_q: int = 1, n_a: int = 0) -> str:
    return PINNED.format(n=n_q, a=f" and {n_a} answer(s)" if n_a else "",
                         nxt=rnd + 1, rnd=rnd, sid=sid)


def worker_record(sid: str, rnd: int, *, answers=None) -> dict:
    record = {
        "record_version": 1, "session_id": sid, "round": rnd,
        "from": "worker", "created_at": "2026-11-11T19:40:00+00:00",
        "questions": [dict(QUESTION)],
    }
    if answers:
        record["answers"] = answers
    return record


def planner_record(sid: str) -> dict:
    return {
        "record_version": 1, "session_id": sid, "round": 2,
        "from": "planner", "created_at": "2026-11-11T19:45:00+00:00",
        "answers": [{"question_round": 1, "question_index": 0,
                     "answer": "Yes.", "disposition": "free-text"}],
    }


def clarification_manifest(sid: str) -> dict:
    return {
        "session_id": sid, "responds_to": sid, "corrects": None,
        "response_kind": "clarification",
        "summary": "blocked on one question (fixture)",
        "changes": [], "deferred": [], "validation_will_run": [],
        "claims": {}, "questions": [dict(QUESTION)],
    }


def load_crafter():
    spec = importlib.util.spec_from_file_location(
        "craft_response_exchange_words", CRAFT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def header_lines(block: str) -> list[str]:
    """The block's header: every leading '#' line after BEGIN."""
    lines = block.split("\n")
    out = []
    for ln in lines[1:]:
        if not ln.startswith("#"):
            break
        out.append(ln)
    return out


class HeaderLineTest(unittest.TestCase):
    """Outcome 3: the planner-facing header line, both renderers."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.relay = _load_module("bale_relay")
        cls.craft = load_crafter()

    def renderers(self):
        return (("bale_relay", self.relay.format_exchange_block),
                ("craft_response", self.craft.format_exchange_block))

    def test_one_question_round_one_is_the_pinned_bytes(self) -> None:
        for name, render in self.renderers():
            with self.subTest(renderer=name):
                header = header_lines(render(SID, worker_record(SID, 1)))
                self.assertEqual(header[1], pinned(SID, 1))
                # The line starts at its '#', with no leading space.
                self.assertTrue(header[1].startswith("# 1 blocking"))

    def test_answers_clause_stays_where_it_is(self) -> None:
        answers = [{"question_round": 2, "question_index": 0,
                    "answer": "Root.", "disposition": "free-text"}]
        record = worker_record(SID, 3, answers=answers)
        for name, render in self.renderers():
            with self.subTest(renderer=name):
                header = header_lines(render(SID, record))
                self.assertEqual(header[1], pinned(SID, 3, n_a=1))

    def test_first_and_last_header_lines_unchanged(self) -> None:
        for name, render in self.renderers():
            with self.subTest(renderer=name):
                header = header_lines(render(SID, worker_record(SID, 1)))
                self.assertEqual(len(header), 3)
                self.assertEqual(
                    header[0],
                    f"# bale exchange record — session {SID} — "
                    f"round 1 — from worker to planner")
                self.assertTrue(header[2].startswith(
                    "# Body: the record (exchange-record.schema.json)."))

    def test_worker_facing_line_unchanged(self) -> None:
        for name, render in self.renderers():
            with self.subTest(renderer=name):
                header = header_lines(render(SID, planner_record(SID)))
                self.assertEqual(header[1], WORKER_FACING.format(sid=SID))
                self.assertNotIn("carried this block", header[1])

    def test_both_renderers_byte_identical(self) -> None:
        for record in (worker_record(SID, 1), planner_record(SID)):
            with self.subTest(side=record["from"]):
                self.assertEqual(
                    self.relay.format_exchange_block(SID, record),
                    self.craft.format_exchange_block(SID, record))

    def test_trailer_hashes_the_body_only(self) -> None:
        """Outcome 4: the header's words move no hash."""
        record = worker_record(SID, 1)
        block = self.relay.format_exchange_block(SID, record)
        body = self.relay._exchange_body_bytes(record)
        self.assertIn(f"# sha256 {hashlib.sha256(body).hexdigest()}\n",
                      block)

    def test_crafter_emit_block_from_a_manifest(self) -> None:
        with tempfile.TemporaryDirectory(prefix="bale-xwords-") as d:
            path = Path(d) / "clar.json"
            path.write_text(json.dumps(clarification_manifest(SID)),
                            encoding="utf-8")
            cp = subprocess.run(
                [sys.executable, "-I", str(CRAFT), "--emit-block",
                 str(path)], capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(header_lines(cp.stdout)[1], pinned(SID, 1))


class NextStepWordsTest(unittest.TestCase):
    """Outcomes 1 and 2, unit-shaped: the landing's trailer and the
    dry-run's next step."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = _load_module("bale_report")

    def assert_answer_path(self, text: str) -> None:
        self.assertNotIn("worker's chat", text)
        stripped = [ln.strip() for ln in text.splitlines()]
        self.assertIn(RELAY_LINE.format(sid=SID), stripped,
                      msg="the relay line, with the real sid, on its own "
                          "line:\n" + text)
        self.assertNotIn("<sid>", text)

    def test_trailer(self) -> None:
        trailer = self.report.clarification_next_step_trailer(SID)
        self.assertEqual(trailer[0], "  Next step:")
        text = "\n".join(trailer)
        self.assert_answer_path(text)
        self.assertIn(f"`bale relay {SID}` alone", text)
        self.assertIn("`bale unlock` and repack", text)
        self.assertIn("exchange record", text)

    def test_landing_banner_prints_the_trailer(self) -> None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            self.report.print_clarification_banner(
                clarification_manifest(SID))
        out = buf.getvalue()
        self.assertIn(f"[CLARIFICATION] {SID}", out)
        self.assert_answer_path(out)

    def test_dry_run_next_step(self) -> None:
        out = self.report.format_dry_run_report(
            clarification_manifest(SID), SID, response_kind="clarification")
        self.assert_answer_path(out)
        self.assertIn("  next step:   answer the questions as an exchange "
                      "record", out)

    def test_bailout_dry_run_unchanged(self) -> None:
        out = self.report.format_dry_run_report(
            clarification_manifest(SID), SID, response_kind="bailout")
        self.assertIn("  next step:   bale handoff <tarball>", out)


class ExchangeWordsE2ETest(unittest.TestCase):
    """One real pack per case, then apply and relay through bin/bale."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-xwords-e2e-")
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def bale(self, *args: str):
        return run_bale(self.install, list(args), cwd=self.repo,
                        env=self.env)

    def pack(self, slug: str) -> str:
        r = self.bale("pack", f"{slug} goal: rewrite hello.txt",
                      "--slug", slug, "--include", "hello.txt",
                      "--no-readme")
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        return sids[0]

    def clarification_tarball(self, sid: str) -> Path:
        rdir = build_response_dir(
            self.tmp / "clar", sid,
            summary="exchange-words fixture: blocked on a question",
            entries=[], validation_will_run=[],
            validation_sh="#!/usr/bin/env bash\n# No checks.\nexit 0\n",
            manifest_extra={"response_kind": "clarification",
                            "questions": [dict(QUESTION)]})
        return tar_response_dir(rdir)

    def thread(self, sid: str) -> list[str]:
        d = self.repo / ".bale" / "clarifications" / sid
        return sorted(p.name for p in d.glob("*.json")) if d.is_dir() else []

    def assert_answer_path(self, out: str, sid: str) -> None:
        self.assertNotIn("worker's chat", out)
        self.assertIn(RELAY_LINE.format(sid=sid),
                      [ln.strip() for ln in out.splitlines()], msg=out)

    def test_dry_run_then_landing_then_reemit(self) -> None:
        sid = self.pack("xwords")
        tarball = self.clarification_tarball(sid)

        dry = self.bale("apply", str(tarball), "--dry-run", "--no-interact")
        self.assertEqual(dry.returncode, 0, msg=dry.stdout + dry.stderr)
        self.assertIn("response_kind: clarification", dry.stdout)
        self.assert_answer_path(dry.stdout, sid)
        self.assertEqual(self.thread(sid), [], msg="a dry-run preserves "
                         "nothing")

        land = self.bale("apply", str(tarball), "--no-interact")
        self.assertEqual(land.returncode, 0, msg=land.stdout + land.stderr)
        self.assertIn(f"[CLARIFICATION] {sid}", land.stdout)
        self.assert_answer_path(land.stdout, sid)
        self.assertNotIn("worker's chat", land.stderr)
        self.assertEqual(self.thread(sid), ["001.json"])

        # The trailer's no-file form prints the landed round's block,
        # with the pinned planner-facing line.
        again = self.bale("relay", sid)
        self.assertEqual(again.returncode, 0, msg=again.stdout + again.stderr)
        self.assertEqual(header_lines(again.stdout)[1], pinned(sid, 1))
        self.assertEqual(self.thread(sid), ["001.json"])

    def test_crafter_block_ingests_as_round_one(self) -> None:
        """Outcome 4: a block the crafter renders from a clarification
        manifest still ingests through `bale relay <sid> FILE`."""
        sid = self.pack("xwordsingest")
        manifest = clarification_manifest(sid)
        mpath = self.tmp / "clar.json"
        mpath.write_text(json.dumps(manifest), encoding="utf-8")
        cp = subprocess.run(
            [sys.executable, "-I", str(CRAFT), "--emit-block", str(mpath)],
            capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(header_lines(cp.stdout)[1], pinned(sid, 1))
        bpath = self.tmp / "block.txt"
        bpath.write_text(cp.stdout, encoding="utf-8")

        r = self.bale("relay", sid, str(bpath))
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertEqual(self.thread(sid), ["001.json"])
        kept = json.loads((self.repo / ".bale" / "clarifications" / sid
                           / "001.json").read_text(encoding="utf-8"))
        kept.pop("preserved_at", None)
        # The crafter's block body is the manifest's `from: worker`
        # reading at round 1; relay keeps it as the thread's round 1.
        self.assertEqual(kept["from"], "worker")
        self.assertEqual(kept["round"], 1)
        self.assertEqual(kept["questions"], manifest["questions"])
        # Relay's own planner-facing block carries the same line.
        self.assertEqual(header_lines(r.stdout)[1], pinned(sid, 1))


if __name__ == "__main__":
    unittest.main()
