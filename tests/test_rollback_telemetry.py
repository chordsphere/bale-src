#!/usr/bin/env python3
"""Hermetic E2E for rollback telemetry (v0.3.18, board 28).

Pins BALE.md section 9.2's telemetry paragraph: `bale rollback`'s two
clean-success paths — the same paths, and only the paths, that write the
`reverted/<sid>` / `re-applied/<sid>` tags — append an attempt to the
sid's telemetry record. Before this feature rollback was the last silent
lifecycle verb: it rewrote history and left no row, which is precisely
the "the merge was wrong" signal board 5's ledger wants.

The suite asserts:

- a clean rollback records outcome `rolled-back`, command `rollback`,
  `closure_reason` null, everything tarball- and validation-shaped null,
  scope `[]` (the session dir is long gone — never a fabricated
  whole-tree), and the summary carries the telemetry row;
- `--undo` appends a second attempt with outcome `re-applied` to the
  SAME record, and the envelope mirrors the latest attempt;
- a recorded scope that IS still recoverable (a scope.json that
  survived) records as recorded;
- the conflict path records nothing, for the same reason it tags
  nothing;
- the dirty-tree refusal records nothing (it exits before the revert);
- the shipped schema's vocabulary gained the three additive values the
  record relies on.

Board 35 (small pins, gap 4) added the two remaining rollback surfaces
without live coverage:

- `--list` — statuses per applied/<sid> tag (applied / reverted /
  re-applied), most-recent-first ordering, the empty-repo message, and
  the read-only contradiction refusal (`--list` with a sid);
- the plain-commit branch — an applied/<sid> tag on a NON-merge commit
  (BALE.md 9.2 step 2 handles it explicitly): the revert runs without
  `-m 1` (a clean revert is itself the proof — `-m 1` on a plain
  commit is a git error) and the summary is recovered from the
  commit's own subject rather than a second parent.

The applied-session fixture fabricates git state directly (branch,
`[bale <sid>] <summary>` commit, --no-ff merge, `applied/<sid>` tag) —
the durable record rollback operates on — rather than driving a full
pack/apply pipeline; rollback reads only git and never the registry, so
the fixture exercises exactly what the command sees (the ADR-0003
depth judgment, flagged in the response's notes.md).

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_rollback_telemetry.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import subprocess
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
    slow,
)

# Sentinels for the surfaces this file pins, in one place (the closure
# suite's idiom) so a message rewording breaks one line.
TELEMETRY_ROW_MARKER = "telemetry:"
RECORDED_MARKER = "recorded claude/telemetry/"
ROLLED_BACK_HEADLINE = "[ROLLED BACK]"
REAPPLIED_HEADLINE = "[RE-APPLIED]"
CONFLICT_HEADLINE = "[CONFLICT]"

SID = "2026-07-20-rollback-fixture-001"


class RollbackTelemetryTest(unittest.TestCase):
    """Rollback's clean-success paths append attempts; nothing else does."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-rollback-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.git_env = git_env(self.home)
        # Any real bale repo gitignores .bale/ (pack's own .gitignore
        # handling runs long before an applied/<sid> tag can exist, and
        # rollback itself journals into .bale/logs/ before the dirty-tree
        # guard runs). This fixture never runs pack, so it mirrors that
        # state by hand — without it, rollback's own log file dirties the
        # tree and the guard refuses (the exact first-apply HOLD of this
        # suite's own session).
        (self.repo / ".gitignore").write_text(".bale/\n", encoding="utf-8")
        self.git("add", ".gitignore")
        self.git("commit", "-m", "ignore .bale (as pack would)")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def git(self, *args: str) -> None:
        run_checked(["git", *args], cwd=self.repo, env=self.git_env)

    def make_applied_session(self, sid: str = SID,
                             summary: str = "add the widget file",
                             filename: str = "widget.txt") -> None:
        """Fabricate the durable record apply's merge path leaves behind:
        a --no-ff merge on main whose second parent's subject is
        `[bale <sid>] <summary>`, tagged applied/<sid>. The bale branch
        is deleted afterwards, as a completed apply leaves it.

        `filename` lets the --list test fabricate several sessions in
        one repo without their file changes colliding on revert."""
        branch = f"bale/{sid}"
        self.git("checkout", "-b", branch)
        (self.repo / filename).write_text("line1\nline2-bale\nline3\n",
                                          encoding="utf-8")
        self.git("add", filename)
        self.git("commit", "-m", f"[bale {sid}] {summary}")
        self.git("checkout", "main")
        self.git("merge", "--no-ff", branch, "-m", f"merge [bale {sid}]")
        self.git("tag", f"applied/{sid}")
        self.git("branch", "-D", branch)

    def make_applied_plain_commit(self, sid: str,
                                  summary: str = "add the plain file",
                                  filename: str = "plain.txt") -> None:
        """Fabricate the applied tag's OTHER shape: a plain (non-merge)
        commit on main with the `[bale <sid>] <summary>` subject, tagged
        applied/<sid>. Apply's merge path never writes this — it always
        tags a --no-ff merge — but BALE.md 9.2 step 2 handles it
        explicitly (a hand-tagged apply, a squashed history), so the
        detection branch stays live behavior worth pinning."""
        (self.repo / filename).write_text("plain-bale content\n",
                                          encoding="utf-8")
        self.git("add", filename)
        self.git("commit", "-m", f"[bale {sid}] {summary}")
        self.git("tag", f"applied/{sid}")

    def rollback(self, *extra: str):
        return run_bale(self.install, ["rollback", *extra],
                        cwd=self.repo, env=self.env)

    def assert_ok(self, result) -> None:
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

    def record_path(self, sid: str = SID) -> Path:
        return self.repo / "claude" / "telemetry" / f"{sid}.json"

    def telemetry_record(self, sid: str = SID) -> dict:
        p = self.record_path(sid)
        self.assertTrue(p.is_file(),
                        msg=f"expected telemetry record at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    # -- pinned behavior 1: clean rollback records rolled-back -----------

    def test_clean_rollback_records_rolled_back(self) -> None:
        self.make_applied_session()
        result = self.rollback(SID)
        self.assert_ok(result)
        self.assertIn(ROLLED_BACK_HEADLINE, result.stdout)
        self.assertIn(TELEMETRY_ROW_MARKER, result.stdout,
                      msg="the summary carries the same telemetry row "
                          "unlock and revert carry")
        self.assertIn(RECORDED_MARKER, result.stdout)

        record = self.telemetry_record()
        self.assertEqual(record["session_id"], SID)
        self.assertEqual(record["outcome"], "rolled-back",
                         msg="envelope outcome mirrors the latest attempt")
        self.assertEqual(len(record["attempts"]), 1)
        attempt = record["attempts"][0]
        self.assertEqual(attempt["outcome"], "rolled-back")
        self.assertEqual(attempt["command"], "rollback")
        self.assertIsNone(attempt["closure_reason"],
                          msg="rollback closes no session — the outcome "
                              "names the event")
        self.assertIsNone(attempt["tarball"])
        self.assertIsNone(attempt["validation"])
        self.assertEqual(attempt["change_paths"], [])
        self.assertEqual(attempt["scope"], [],
                         msg="the session dir is long gone at rollback "
                             "time; [] means 'not recoverable', never a "
                             "fabricated whole-tree")
        self.assertEqual(attempt["log"], f".bale/logs/{SID}.log")

    # -- pinned behavior 2: --undo appends re-applied to the same record -

    def test_undo_appends_re_applied(self) -> None:
        self.make_applied_session()
        self.assert_ok(self.rollback(SID))
        # Since the board 5 D5 guard change (v0.3.23) the dirty-tree
        # guard disregards untracked claude/telemetry/ paths, so this
        # interleaved commit is no longer REQUIRED for the toggle —
        # test_toggle_completes_without_interleaved_commit below pins
        # that path. This test keeps the commit deliberately: it is the
        # committed-variant coverage (the durable-record discipline an
        # operator follows anyway), asserting the guard change did not
        # disturb the ordinary tracked-record flow.
        self.git("add", "claude/telemetry")
        self.git("commit", "-m", "record rollback telemetry")
        result = self.rollback(SID, "--undo")
        self.assert_ok(result)
        self.assertIn(REAPPLIED_HEADLINE, result.stdout)
        self.assertIn(RECORDED_MARKER, result.stdout)

        record = self.telemetry_record()
        self.assertEqual(len(record["attempts"]), 2,
                         msg="one file per sid; the undo APPENDS")
        self.assertEqual(record["attempts"][0]["outcome"], "rolled-back")
        self.assertEqual(record["attempts"][1]["outcome"], "re-applied")
        self.assertEqual(record["attempts"][1]["command"], "rollback")
        self.assertIsNone(record["attempts"][1]["closure_reason"])
        self.assertEqual(record["outcome"], "re-applied",
                         msg="envelope mirrors the latest attempt")

    # -- pinned behavior 3: a surviving scope.json records as recorded ---

    def test_surviving_scope_records_as_recorded(self) -> None:
        """The [] fallback is for the normal long-gone case; a scope.json
        that still exists (unusual, but read_session_scope's contract)
        records exactly as recorded."""
        self.make_applied_session()
        scope_dir = self.repo / ".bale" / "sessions" / SID
        scope_dir.mkdir(parents=True)
        (scope_dir / "scope.json").write_text('["widget.txt"]\n',
                                              encoding="utf-8")
        self.assert_ok(self.rollback(SID))
        attempt = self.telemetry_record()["attempts"][0]
        self.assertEqual(attempt["scope"], ["widget.txt"])

    # -- pinned behavior 4: the conflict path records nothing ------------

    def test_conflict_path_records_nothing(self) -> None:
        """A post-merge commit touching the same line the bale commit
        changed forces the revert into conflict: left in progress, exit
        non-zero, no tag — and no record, for the same reason."""
        self.make_applied_session()
        # Rewrite the line the bale commit introduced so the revert's
        # reverse hunk no longer applies cleanly.
        (self.repo / "widget.txt").write_text("line1\nline2-user\nline3\n",
                                              encoding="utf-8")
        self.git("add", "widget.txt")
        self.git("commit", "-m", "user edit on the same line")

        result = self.rollback(SID)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(CONFLICT_HEADLINE, result.stdout)
        self.assertFalse(self.record_path().exists(),
                         msg="a record would claim a rollback that "
                             "hasn't happened")

    # -- pinned behavior 5: the dirty-tree refusal records nothing -------

    def test_dirty_refusal_records_nothing(self) -> None:
        self.make_applied_session()
        (self.repo / "widget.txt").write_text("uncommitted\n",
                                              encoding="utf-8")
        result = self.rollback(SID)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dirty", result.stderr.lower())
        self.assertFalse(self.record_path().exists())

    # -- guard: the shipped schema carries the additive vocabulary -------

    def test_schema_vocabulary_gained_rollback_values(self) -> None:
        schema = json.loads(
            (self.install / "schemas" / "telemetry-record.schema.json")
            .read_text(encoding="utf-8"))
        envelope = schema["properties"]["outcome"]["enum"]
        attempt_props = schema["properties"]["attempts"]["items"]["properties"]
        for value in ("rolled-back", "re-applied"):
            self.assertIn(value, envelope)
            self.assertIn(value, attempt_props["outcome"]["enum"])
        self.assertIn("rollback", attempt_props["command"]["enum"],
                      msg="the record honestly names the producing command")


    # -- board 35 gap 4a: rollback --list ---------------------------------

    @slow
    def test_list_reports_status_per_session(self) -> None:
        """`--list` is read-only reporting: per-tag status, most-recent-
        first ordering, the empty message, and the contradiction refusal.
        Subtests run in sequence against one repo — each fabrication
        builds on the previous state, the way a real history would."""
        sid_a = "2026-07-20-list-fixture-001"
        sid_b = "2026-07-21-list-fixture-002"

        with self.subTest(variant="no applied tags"):
            result = self.rollback("--list")
            self.assert_ok(result)
            self.assertIn("no applied/<sid> tags reachable from HEAD.",
                          result.stdout)

        # Two applied sessions, A then B — B sits nearer HEAD, so the
        # topological most-recent-first ordering must list B before A.
        self.make_applied_session(sid_a, summary="session A",
                                  filename="widget-a.txt")
        self.make_applied_session(sid_b, summary="session B",
                                  filename="widget-b.txt")

        def status_lines(stdout: str) -> dict:
            """Map sid -> its status word from the listing rows."""
            out = {}
            for line in stdout.splitlines():
                parts = line.split()
                if len(parts) == 2 and parts[1] in (sid_a, sid_b):
                    out[parts[1]] = parts[0]
            return out

        with self.subTest(variant="both applied, most recent first"):
            result = self.rollback("--list")
            self.assert_ok(result)
            self.assertEqual(status_lines(result.stdout),
                             {sid_a: "applied", sid_b: "applied"})
            self.assertLess(result.stdout.index(sid_b),
                            result.stdout.index(sid_a),
                            msg="most-recent-first: B is nearer HEAD")
            self.assertIn("2 applied session(s)", result.stdout)

        with self.subTest(variant="reverted status after rollback"):
            self.assert_ok(self.rollback(sid_a))
            result = self.rollback("--list")
            self.assert_ok(result)
            self.assertEqual(status_lines(result.stdout),
                             {sid_a: "reverted", sid_b: "applied"})

        with self.subTest(variant="re-applied status after --undo"):
            self.assert_ok(self.rollback(sid_a, "--undo"))
            result = self.rollback("--list")
            self.assert_ok(result)
            self.assertEqual(status_lines(result.stdout),
                             {sid_a: "re-applied", sid_b: "applied"})

        with self.subTest(variant="--list with a sid is a contradiction"):
            result = self.rollback("--list", sid_a)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("read-only", result.stderr)
            # The refusal named the condition instead of silently
            # ignoring one flag (CLAUDE.md 6: silent skips are bugs).
            self.assertIn("does not take a sid or --undo", result.stderr)

    # -- board 35 gap 4b: the plain-commit branch -------------------------

    def test_plain_commit_rollback(self) -> None:
        """An applied/<sid> tag on a NON-merge commit rolls back cleanly:
        detection takes the plain branch (the log names it), the revert
        runs without `-m 1` — which would be a git error on a plain
        commit, so the clean exit is itself the proof — and the summary
        for the amended message comes from the commit's own subject,
        there being no second parent to read."""
        sid = "2026-07-22-plain-fixture-001"
        summary = "add the plain file"
        self.make_applied_plain_commit(sid, summary=summary)

        result = self.rollback(sid)
        self.assert_ok(result)
        self.assertIn(ROLLED_BACK_HEADLINE, result.stdout)
        self.assertIn("plain commit", result.stdout,
                      msg="detection took the non-merge branch")

        # The revert really landed: the file the plain commit added is
        # gone, the tag exists, and the amended subject carries the
        # summary recovered from the plain commit's own subject.
        self.assertFalse((self.repo / "plain.txt").exists(),
                         msg="reverting the plain commit removes its file")
        run_checked(["git", "rev-parse", "--verify",
                     f"refs/tags/reverted/{sid}"],
                    cwd=self.repo, env=self.git_env)
        head = subprocess.run(
            ["git", "log", "-1", "--format=%s"],
            cwd=self.repo, env=self.git_env, capture_output=True, text=True)
        self.assertEqual(head.stdout.strip(),
                         f"[bale rollback {sid}] {summary}")

        record = self.telemetry_record(sid)
        self.assertEqual(record["outcome"], "rolled-back")
        self.assertEqual(record["attempts"][0]["command"], "rollback")

    # -- board 5 D5 (v0.3.23): the guard disregards untracked telemetry -

    def test_toggle_completes_without_interleaved_commit(self) -> None:
        """rollback leaves its own record untracked; --undo immediately
        after proceeds anyway, disregarding exactly that path — the
        friction the guard change exists to remove — with the log line
        naming what was disregarded."""
        self.make_applied_session()
        self.assert_ok(self.rollback(SID))
        result = self.rollback(SID, "--undo")
        self.assert_ok(result)
        # The log-line phrasing generalized in v0.3.30 when the guard
        # gained the archive_dir carve-out (BALE.md §9.2 step 3) — the
        # pinned sentinel is the disregard announcement plus the exact
        # telemetry path it names.
        self.assertIn("disregarding untracked bale-written", result.stdout)
        self.assertIn(f"claude/telemetry/{SID}.json", result.stdout)
        record = self.telemetry_record()
        self.assertEqual([a["outcome"] for a in record["attempts"]],
                         ["rolled-back", "re-applied"])

    def test_modified_tracked_telemetry_still_refuses(self) -> None:
        """A tracked telemetry file with uncommitted modifications is a
        real conflict surface for git revert; the guard still refuses."""
        self.make_applied_session()
        self.assert_ok(self.rollback(SID))
        self.git("add", "claude/telemetry")
        self.git("commit", "-m", "record rollback telemetry")
        p = self.record_path()
        p.write_text(p.read_text(encoding="utf-8") + "\n", encoding="utf-8")
        result = self.rollback(SID, "--undo")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dirty", result.stderr.lower())

    def test_untracked_non_telemetry_still_refuses(self) -> None:
        """The disregard is a prefix, not a policy on untracked files:
        stray untracked paths elsewhere refuse exactly as before."""
        self.make_applied_session()
        (self.repo / "stray.txt").write_text("stray\n", encoding="utf-8")
        result = self.rollback(SID)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("dirty", result.stderr.lower())
        self.assertFalse(self.record_path().exists())

    def test_stash_path_unchanged_with_tracked_dirt(self) -> None:
        """--stash on tracked dirt still stashes, reverts, and pops —
        the guard change touches only the clean/dirty judgment."""
        self.make_applied_session()
        (self.repo / "hello.txt").write_text("hello edited\n",
                                             encoding="utf-8")
        result = self.rollback(SID, "--stash")
        self.assert_ok(result)
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            "hello edited\n",
            msg="the stashed edit pops back after the revert lands")
        self.assertEqual(self.telemetry_record()["outcome"], "rolled-back")


if __name__ == "__main__":
    unittest.main(verbosity=2)
