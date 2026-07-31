#!/usr/bin/env python3
"""Hermetic E2E for `bale revert --json` (v0.3.19, board 30).

Pins BALE.md section 9.1's --json sentence: revert ends on the same
format_summary_block shape unlock does and already carries the
telemetry row, so an orchestrator discarding HOLDs had the same
machine-readability gap unlock had before v0.3.18. The contract under
test is the ratified json-mode split: stdout carries exactly one line
of JSON (the key contract owned by format_revert_json's docstring in
bin/bale_report.py), every human line — `[bale] ` logs and the summary
block — goes to stderr, and human mode is byte-untouched (no code path
differs when the stream swap never happens).

The suite asserts:

- the discard path emits outcome `reverted` with sid, closure_reason
  null, the branch facts (origin_branch, branch_deleted), lock_cleared,
  the staging machine keys, and the telemetry record path;
- an explicit `--reason` rides through the closure_reason key;
- a recorded staging directory rides the machine keys as
  `staging_state: "wiped"` with its path — derived from the
  filesystem, never parsed from the human row;
- reverting an already-closed session's leftovers reports
  `lock_cleared: false`;
- refusal paths stay fail()-shaped: non-zero, stderr, nothing on
  stdout;
- human mode emits no JSON.

The HOLD fixture fabricates git state directly (a real `bale pack` for
the registry/metadata half, then a plain-git `bale/<sid>` branch with a
session commit) rather than driving a full apply pipeline — the same
sanctioned shape 006's rollback fixture used for its applied merge:
revert reads only the session metadata and the branch, so the fixture
exercises exactly what the command sees (the ADR-0003 depth judgment,
flagged in the response's notes.md).

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_revert_json.py

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


class RevertJsonTest(unittest.TestCase):
    """`bale revert --json`: one stdout JSON line, human trail on stderr."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-revertjson-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.git_env = git_env(self.home)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def git(self, *args: str) -> None:
        run_checked(["git", *args], cwd=self.repo, env=self.git_env)

    def pack(self):
        return run_bale(
            self.install,
            [
                "pack", "revert json test goal",
                "--slug", "revertjson",
                "--include", "hello.txt",
                "--no-readme",
            ],
            cwd=self.repo,
            env=self.env,
        )

    def revert(self, *extra: str):
        return run_bale(self.install, ["revert", *extra],
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

    def make_held_session(self) -> str:
        """Fabricate the state revert acts on: a real pack (registry
        entry, origin_branch stamp, session dir), then a plain-git
        `bale/<sid>` branch with a session commit — what an apply HOLD
        leaves behind (ADR-0008), without driving the apply pipeline."""
        result = self.pack()
        self.assert_ok(result)
        sids = self.open_sids()
        self.assertTrue(sids, msg="pack succeeded but no session is open")
        sid = sids[-1]
        branch = f"bale/{sid}"
        self.git("checkout", "-b", branch)
        (self.repo / "widget.txt").write_text("bale change\n",
                                              encoding="utf-8")
        self.git("add", "widget.txt")
        self.git("commit", "-m", f"[bale {sid}] add the widget file")
        self.git("checkout", "main")
        return sid

    def branch_exists(self, branch: str) -> bool:
        import subprocess
        r = subprocess.run(
            ["git", "rev-parse", "--verify", "--quiet", branch],
            cwd=self.repo, env=self.git_env, capture_output=True, text=True)
        return r.returncode == 0

    # -- pinned behavior 1: the discard path -----------------------------

    def test_discard_path_emits_reverted_contract(self) -> None:
        sid = self.make_held_session()
        result = self.revert("--json")
        self.assert_ok(result)

        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "reverted")
        self.assertEqual(payload["sid"], sid)
        self.assertIsNone(payload["closure_reason"],
                          msg="no --reason records null — the outcome "
                              "already names the event")
        self.assertEqual(payload["origin_branch"], "main")
        self.assertEqual(payload["branch_deleted"], f"bale/{sid}")
        self.assertTrue(payload["lock_cleared"])
        self.assertEqual(payload["staging_state"], "not-recorded",
                         msg="no apply attempt ever stamped a staging "
                             "path for this fixture")
        self.assertIsNone(payload["staging_path"])
        self.assertTrue(
            payload["telemetry"].startswith("claude/telemetry/"),
            msg="the machine-readable telemetry path is the point of "
                "the feature")
        self.assertTrue(payload["log"].endswith(f".bale/logs/{sid}.log"))
        # The facts the keys report really happened.
        self.assertFalse(self.branch_exists(f"bale/{sid}"))
        self.assertTrue((self.repo / payload["telemetry"]).is_file())
        self.assertEqual(self.open_sids(), [])
        # Stream discipline: the human trail moved to stderr, whole.
        self.assertIn("[bale]", result.stderr)
        self.assertIn("[REVERT]", result.stderr,
                      msg="the human summary block is the stderr "
                          "reference trail under json mode")

    # -- pinned behavior 2: --reason rides the key -----------------------

    def test_reason_rides_closure_reason_key(self) -> None:
        self.make_held_session()
        result = self.revert("--reason", "superseded-by-split", "--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["closure_reason"], "superseded-by-split")

    # -- pinned behavior 3: staging facts as machine keys ----------------

    def test_staging_facts_ride_machine_keys(self) -> None:
        sid = self.make_held_session()
        # Stamp a recorded staging directory the way apply would, and
        # create it so the wipe path (not already-gone) is exercised.
        staging = self.repo / ".bale" / "staging" / sid
        staging.mkdir(parents=True)
        (staging / "scratch.txt").write_text("staged\n", encoding="utf-8")
        (self.repo / ".bale" / "sessions" / sid / "staging_path").write_text(
            f"{staging}\n", encoding="utf-8")

        result = self.revert("--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["staging_state"], "wiped")
        self.assertEqual(payload["staging_path"], str(staging))
        self.assertFalse(staging.exists(),
                         msg="the key claims a wipe that must have "
                             "actually happened")

    # -- pinned behavior 4: already-closed session reports honestly ------

    def test_closed_session_reports_lock_cleared_false(self) -> None:
        """revert's explicit-sid path can clean up a session the
        registry no longer shows open; lock_cleared must say so rather
        than claim a close that didn't happen. The closed-but-branch-
        and-metadata-intact state is fabricated by removing the registry
        marker directly — the crash-adjacent shape revert's
        require_open=False threading exists for."""
        sid = self.make_held_session()
        (self.repo / ".bale" / "sessions" / sid / "open").unlink()
        (self.repo / ".bale" / "current_session").write_text("")

        result = self.revert(sid, "--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "reverted")
        self.assertFalse(payload["lock_cleared"])
        self.assertFalse(self.branch_exists(f"bale/{sid}"))

    # -- pinned behavior 5: refusal paths stay fail()-shaped -------------

    def test_refusal_emits_nothing_on_stdout(self) -> None:
        """No session open, no sid: the refusal exits through fail() —
        stderr, non-zero, nothing on stdout, like every other json
        surface's error paths."""
        result = self.revert("--json")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertIn("no session is open", result.stderr)

    # -- pinned behavior 6: human mode emits no JSON ---------------------

    def test_human_mode_emits_no_json(self) -> None:
        self.make_held_session()
        result = self.revert()
        self.assert_ok(result)
        self.assertNotIn('{"outcome"', result.stdout)
        self.assertIn("[REVERT]", result.stdout,
                      msg="the human block stays on stdout when the "
                          "stream swap never happens")


if __name__ == "__main__":
    unittest.main(verbosity=2)
