#!/usr/bin/env python3
"""Hermetic E2E for pack's tree-position echo (v0.3.31; BALE.md §7.7).

The board-6 upward report's tooling corrective: a stale pack command
was re-pasted after its session had already applied, because pack said
nothing about where the tree was at the moment of paste. The echo
names the two facts that make that staleness visible — the current
branch and the latest applied sid (the same fact the status applied
row renders, from the same source) — on both of pack's surfaces.

Pinned behaviors:

- **The pre-flight banner line**: ``tree position: branch <branch>;
  latest applied <sid-or-none-yet>``, printed before the end-of-run
  summary (paste-time visibility, ahead of any wizard investment).
- **The report rows**: ``branch`` and ``latest applied`` in the human
  summary block, same rendering rule as the banner.
- **--json parity**: additive keys ``branch`` / ``applied_latest``
  (null when nothing applied yet), stdout still exactly one line —
  the banner line rides stderr under json-mode stream discipline.
- **Latest means latest**: with two applied/<sid> tags the echo names
  the most recent by creation date, matching the status applied row.
- **Reject-early intact**: a pre-flight refusal that precedes the
  echo's site (the detached-HEAD refusal) shows no echo at all.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness
in ``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_tree_position_echo.py

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

# Sentinels for the surfaces this file pins (one place per message).
BANNER_MARKER = "tree position: branch "
BRANCH_ROW_MARKER = "branch:"
APPLIED_ROW_MARKER = "latest applied:"
NONE_YET = "none yet"

SID_OLDER = "2026-08-01-fx-echo-001"
SID_NEWER = "2026-08-02-fx-echo-002"


class TreePositionEchoTest(unittest.TestCase):
    """Pack's tree-position echo: banner line, report rows, json keys."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-treepos-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack(self, *extra: str, slug: str = "echo-a"):
        return run_bale(
            self.install,
            [
                "pack", "tree position echo test goal",
                "--slug", slug,
                "--include", "hello.txt",
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def commit_and_tag_applied(self, sid: str, *, date: str,
                               filename: str) -> None:
        """One commit with a pinned committer date, tagged applied/<sid>.

        applied/<sid> tags are lightweight (bale_apply tags the merge
        commit without -a), and a lightweight tag's creatordate is its
        commit's committer date — so pinning GIT_COMMITTER_DATE per
        commit is what makes the "most recent by creation date"
        ordering deterministic across the two tags below.
        """
        env = dict(git_env(self.home))
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
        (self.repo / filename).write_text(f"{sid}\n", encoding="utf-8")
        run_checked(["git", "add", filename], cwd=self.repo, env=env)
        run_checked(["git", "commit", "-m", f"apply {sid}"],
                    cwd=self.repo, env=env)
        run_checked(["git", "tag", f"applied/{sid}"],
                    cwd=self.repo, env=env)

    # -- pinned behavior 1: banner + rows, nothing applied yet -----------

    def test_fresh_repo_echoes_branch_and_none_yet(self) -> None:
        """A fresh repo's pack echoes the branch and an honest
        'none yet' on both surfaces — banner line and summary rows."""
        result = self.pack()
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertIn(f"{BANNER_MARKER}main; latest applied {NONE_YET}",
                      result.stdout)
        self.assertIn(BRANCH_ROW_MARKER, result.stdout)
        self.assertIn(APPLIED_ROW_MARKER, result.stdout)

    def test_banner_prints_before_the_summary(self) -> None:
        """The banner line is paste-time visibility: it precedes the
        end-of-run summary (whose first row is the session id)."""
        result = self.pack()
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        banner_at = result.stdout.find(BANNER_MARKER)
        summary_at = result.stdout.find("session id:")
        self.assertGreaterEqual(banner_at, 0, msg=result.stdout)
        self.assertGreaterEqual(summary_at, 0, msg=result.stdout)
        self.assertLess(banner_at, summary_at,
                        msg="the tree-position banner must precede the "
                            "end-of-run summary")

    # -- pinned behavior 2: latest applied sid, deterministic ------------

    def test_echo_names_the_latest_applied_sid(self) -> None:
        """With two applied/<sid> tags, the echo names the most recent
        by creation date — the status applied row's own ordering."""
        self.commit_and_tag_applied(
            SID_OLDER, date="2026-08-01T10:00:00 +0000", filename="a.txt")
        self.commit_and_tag_applied(
            SID_NEWER, date="2026-08-02T10:00:00 +0000", filename="b.txt")
        result = self.pack()
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn(f"{BANNER_MARKER}main; latest applied {SID_NEWER}",
                      result.stdout)
        # The row surface carries the same sid; the older one appears
        # nowhere (the echo is the latest fact, not a listing).
        self.assertIn(SID_NEWER, result.stdout)
        self.assertNotIn(SID_OLDER, result.stdout)

    # -- pinned behavior 3: --json parity --------------------------------

    def test_json_keys_null_on_fresh_repo(self) -> None:
        """--json carries branch and a null applied_latest on a repo
        with nothing applied — a value, not the human 'none yet'."""
        result = self.pack("--json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        stdout_lines = [ln for ln in result.stdout.splitlines() if ln]
        self.assertEqual(
            len(stdout_lines), 1,
            msg="json-mode stdout must stay exactly one line; the "
                f"banner rides stderr. stdout:\n{result.stdout}")
        payload = json.loads(stdout_lines[0])
        self.assertEqual(payload["branch"], "main")
        self.assertIsNone(payload["applied_latest"])
        # The banner still printed — on stderr, per stream discipline.
        self.assertIn(BANNER_MARKER, result.stderr)
        self.assertNotIn(BANNER_MARKER, result.stdout)

    def test_json_carries_latest_applied_sid(self) -> None:
        """--json's applied_latest agrees with the human echo."""
        self.commit_and_tag_applied(
            SID_NEWER, date="2026-08-02T10:00:00 +0000", filename="b.txt")
        result = self.pack("--json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(payload["branch"], "main")
        self.assertEqual(payload["applied_latest"], SID_NEWER)

    # -- pinned behavior 4: reject-early precedes the echo ---------------

    def test_detached_head_refusal_shows_no_echo(self) -> None:
        """A pre-flight refusal sited before the echo (detached HEAD)
        rejects with no tree-position line on either stream — a doomed
        command sees no echo, per the reject-early contract."""
        env = git_env(self.home)
        run_checked(["git", "checkout", "--detach"],
                    cwd=self.repo, env=env)
        result = self.pack()
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn("HEAD is detached", result.stderr)
        self.assertNotIn(BANNER_MARKER, result.stdout)
        self.assertNotIn(BANNER_MARKER, result.stderr)


if __name__ == "__main__":
    unittest.main()
