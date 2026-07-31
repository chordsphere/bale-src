#!/usr/bin/env python3
"""Hermetic E2E for the board-33 README riders (v0.3.21).

Two pinned behaviors around `--readme-file`:

- **The identity echo** (evidence 45, strengthened per evidence 47):
  the pack report — human summary rows and `--json` keys alike —
  echoes the resolved README's path, its first heading line, and the
  sha256 of the shipped bytes. Path + heading alone proved
  insufficient identity (two revisions of a brief share both); the
  hash is the identity, and it is computed over the bytes inside the
  tarball, so `sha256sum` of the shipped README.md reproduces it.

- **The placeholder refusal**: a resolved brief still containing an
  unfilled placeholder — any line containing the sentinel
  `TODO(brief)` (TARBALL.md §3.4, the --readme-file row) — refuses
  loudly at read time, naming the sentinel and the file, before any
  prompt and before any session state exists.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness
in ``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_readme_identity.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import hashlib
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
)

# Sentinels for the surfaces this file pins (one place per message).
SENTINEL = "TODO(brief)"
REFUSAL_MARKER = "unfilled placeholder"
HEADING_ROW_MARKER = "readme heading:"
SHA_ROW_MARKER = "readme sha256:"

BRIEF_BODY = (
    "# Brief — identity echo fixture — rev A\n"
    "\n"
    "Some prose the worker authored.\n"
)


class ReadmeIdentityTest(unittest.TestCase):
    """The README identity echo and the placeholder refusal."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-readme-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def write_brief(self, body: str, name: str = "brief.md") -> Path:
        p = self.tmp / name
        p.write_text(body, encoding="utf-8")
        return p

    def pack(self, *extra: str, slug: str = "session-a"):
        return run_bale(
            self.install,
            [
                "pack", "readme identity test goal",
                "--slug", slug,
                "--include", "hello.txt",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return [d.name for d in root.iterdir() if (d / "open").is_file()]

    def shipped_readme_sha256(self, sid: str) -> str:
        """sha256 of the README.md bytes inside the outbox tarball —
        the ground truth the echo must reproduce."""
        tb = self.repo / ".bale" / "outbox" / f"request-{sid}.tar.gz"
        self.assertTrue(tb.is_file(), msg=f"no outbox tarball at {tb}")
        nnn = sid.rsplit("-", 1)[-1]
        with tarfile.open(tb, "r:gz") as tf:
            member = tf.extractfile(f"request-{nnn}/README.md")
            self.assertIsNotNone(member, msg="tarball ships no README.md")
            return hashlib.sha256(member.read()).hexdigest()

    # -- pinned behavior 1: the identity echo, human summary -------------

    def test_summary_echoes_path_heading_and_sha256(self) -> None:
        """The human report carries the resolved path, the first
        heading line, and a sha256 that matches the shipped file."""
        brief = self.write_brief(BRIEF_BODY)
        result = self.pack("--readme-file", str(brief))
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        sids = self.open_sids()
        self.assertEqual(len(sids), 1)
        self.assertIn(str(brief), result.stdout)
        self.assertIn("# Brief — identity echo fixture — rev A",
                      result.stdout)
        shipped_sha = self.shipped_readme_sha256(sids[0])
        self.assertIn(shipped_sha, result.stdout,
                      msg="echoed sha256 must match the shipped README.md")
        # The source file's own bytes agree too (the body ends with a
        # newline, so no normalization difference exists here).
        self.assertEqual(
            shipped_sha,
            hashlib.sha256(brief.read_bytes()).hexdigest())

    def test_no_readme_pack_has_no_echo_rows(self) -> None:
        """A --no-readme pack's summary carries no identity rows."""
        result = self.pack("--no-readme")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn(HEADING_ROW_MARKER, result.stdout)
        self.assertNotIn(SHA_ROW_MARKER, result.stdout)

    def test_headingless_brief_echoes_honest_marker(self) -> None:
        """A brief with no heading line echoes '(no heading)' rather
        than a silent blank or an invented one."""
        brief = self.write_brief("just prose, no markdown heading\n")
        result = self.pack("--readme-file", str(brief))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("(no heading)", result.stdout)

    # -- pinned behavior 2: the identity echo, --json keys ---------------

    def test_json_report_carries_identity_keys(self) -> None:
        """--json emits readme_path / readme_heading / readme_sha256,
        agreeing with the shipped bytes."""
        brief = self.write_brief(BRIEF_BODY)
        result = self.pack("--readme-file", str(brief), "--json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(payload["readme_path"], str(brief))
        self.assertEqual(payload["readme_heading"],
                         "# Brief — identity echo fixture — rev A")
        self.assertEqual(payload["readme_sha256"],
                         self.shipped_readme_sha256(payload["sid"]))

    def test_json_keys_null_without_readme(self) -> None:
        """The three keys are present and null together on a
        no-README pack — additive keys, uniform shape."""
        result = self.pack("--no-readme", "--json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertIsNone(payload["readme_path"])
        self.assertIsNone(payload["readme_heading"])
        self.assertIsNone(payload["readme_sha256"])

    # -- pinned behavior 3: the placeholder refusal ----------------------

    def test_placeholder_brief_refuses_loudly(self) -> None:
        """A brief containing a TODO(brief) line refuses at read time,
        naming the sentinel and the file; no session state exists."""
        brief = self.write_brief(
            "# Brief — half generated\n"
            "\n"
            "TODO(brief): fill the goal restatement here\n",
            name="bad-brief.md",
        )
        result = self.pack("--readme-file", str(brief))
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn(REFUSAL_MARKER, result.stderr)
        self.assertIn(SENTINEL, result.stderr)
        self.assertIn(str(brief), result.stderr)
        self.assertEqual(self.open_sids(), [],
                         msg="a refused pack must open no session")
        self.assertFalse((self.repo / ".bale" / "outbox").exists()
                         and any((self.repo / ".bale" / "outbox").iterdir()),
                         msg="a refused pack must ship no tarball")

    def test_filled_brief_with_plain_todo_is_not_refused(self) -> None:
        """The sentinel is the exact form 'TODO(brief)' — an ordinary
        TODO in prose does not trip the refusal."""
        brief = self.write_brief(
            "# Brief — rev B\n"
            "\n"
            "TODO: the worker should consider edge cases.\n",
            name="ok-brief.md",
        )
        result = self.pack("--readme-file", str(brief))
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
