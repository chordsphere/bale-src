"""Planner-bundle deny-list (v0.4.12, board 49a-i; BALE.md §6.7,
§7.1 step 4c, contract row 33).

Pins the pack-side blindness half end to end through real pack runs
in the hermetic sandbox (ADR-0005 doctrine, via tests/harness.py):

- incidental coverage: a `.bale-bundle` file under an included
  directory never ships — dropped at the walk with the loud per-file
  line naming the path and the no-ship rule, absent from the shipped
  tarball's context/
- the v0.4.10 grain: two or more dropped bundles collapse to one
  count summary line, and no per-file line renders
- explicit naming refuses, both flag families: an `--include` entry
  that is a bundle file refuses at pre-flight with no session opened;
  a `--write` entry that is a bundle file refuses the same way
- the recognizer is the exact suffix: a near-name file
  (`about.bale-bundle.md`) ships normally with no drop line

The suffix is reserved by the format (BUNDLE_SUFFIX in
bin/bale_pack.py); these tests spell it literally on purpose — a
constant rename that silently changed the wire-reserved name should
break here.
"""

from __future__ import annotations

import tarfile
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

# Sentinels for the surfaces this file pins. Kept in one place so a
# message rewording breaks one line, not several assertions.
DROP_ONE_MARKER = "auto-excluded notes/oracle.bale-bundle from shipped context"
DROP_MANY_MARKER = "auto-excluded 2 planner-bundle files"
NEVER_SHIP_MARKER = "never ship"
REFUSE_MARKER = "planner-bundle blindness"
NO_ADMISSION_MARKER = "no admission flag"


class BundleDenylistTest(unittest.TestCase):
    """`.bale-bundle` files: walk auto-exclusion + explicit-naming refusal."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-bundle-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def commit_file(self, rel: str, content: str = "payload\n") -> None:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        env = git_env(self.home)
        run_checked(["git", "add", rel], cwd=self.repo, env=env)
        run_checked(["git", "commit", "-m", f"add {rel}"],
                    cwd=self.repo, env=env)

    def pack(self, *extra: str, slug: str):
        """A fully specified piped pack; extras append to the base form."""
        return run_bale(
            self.install,
            [
                "pack", f"bundle denylist test goal for {slug}",
                "--slug", slug,
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return sorted(d.name for d in root.iterdir()
                      if (d / "open").is_file())

    def shipped_context_members(self, sid: str) -> set:
        """The context/-relative member paths inside the outbox tarball."""
        tb = self.repo / ".bale" / "outbox" / f"request-{sid}.tar.gz"
        self.assertTrue(tb.is_file(), msg=f"no outbox tarball at {tb}")
        prefix = f"request-{sid.rsplit('-', 1)[-1]}/context/"
        with tarfile.open(tb, "r:gz") as tf:
            return {
                name[len(prefix):]
                for name in tf.getnames()
                if name.startswith(prefix)
            }

    # -- pinned behavior 1: incidental coverage auto-excludes ------------

    def test_covered_bundle_drops_loudly_and_never_ships(self) -> None:
        """A bundle under an included directory drops at the walk with
        the loud per-file line; the sibling file ships; the tarball's
        context/ carries no bundle."""
        self.commit_file("notes/keep.txt")
        self.commit_file("notes/oracle.bale-bundle")
        result = self.pack("--include", "notes", slug="covered")
        self.assertEqual(result.returncode, 0,
                         msg=result.stdout + result.stderr)
        combined = result.stdout + result.stderr
        self.assertIn(DROP_ONE_MARKER, combined)
        self.assertIn(NEVER_SHIP_MARKER, combined)
        self.assertIn(NO_ADMISSION_MARKER, combined)
        sids = self.open_sids()
        self.assertEqual(len(sids), 1)
        members = self.shipped_context_members(sids[0])
        self.assertIn("notes/keep.txt", members)
        self.assertNotIn("notes/oracle.bale-bundle", members)

    # -- pinned behavior 2: the v0.4.10 summary grain --------------------

    def test_two_bundles_collapse_to_one_summary_line(self) -> None:
        """More than one dropped bundle emits the count summary, not a
        per-file wall — and still ships neither."""
        self.commit_file("notes/keep.txt")
        self.commit_file("notes/oracle.bale-bundle")
        self.commit_file("notes/older.bale-bundle")
        result = self.pack("--include", "notes", slug="grain")
        self.assertEqual(result.returncode, 0,
                         msg=result.stdout + result.stderr)
        combined = result.stdout + result.stderr
        self.assertIn(DROP_MANY_MARKER, combined)
        self.assertNotIn(DROP_ONE_MARKER, combined)
        members = self.shipped_context_members(self.open_sids()[0])
        self.assertNotIn("notes/oracle.bale-bundle", members)
        self.assertNotIn("notes/older.bale-bundle", members)

    # -- pinned behavior 3: explicit naming refuses ----------------------

    def test_include_naming_a_bundle_refuses(self) -> None:
        self.commit_file("notes/oracle.bale-bundle")
        result = self.pack("--include", "notes/oracle.bale-bundle",
                           slug="named-include")
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn(REFUSE_MARKER, result.stdout + result.stderr)
        self.assertEqual(self.open_sids(), [],
                         msg="a refused pack must open no session")

    def test_write_naming_a_bundle_refuses(self) -> None:
        self.commit_file("notes/keep.txt")
        self.commit_file("notes/oracle.bale-bundle")
        result = self.pack("--include", "notes",
                           "--write", "notes/oracle.bale-bundle",
                           slug="named-write")
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn(REFUSE_MARKER, result.stdout + result.stderr)
        self.assertEqual(self.open_sids(), [])

    # -- pinned behavior 4: the recognizer is the exact suffix -----------

    def test_near_suffix_file_ships_normally(self) -> None:
        """A file that merely contains the suffix mid-name (a note
        *about* a bundle) is not a bundle: it ships, with no drop
        line."""
        self.commit_file("notes/about.bale-bundle.md")
        result = self.pack("--include", "notes", slug="near-name")
        self.assertEqual(result.returncode, 0,
                         msg=result.stdout + result.stderr)
        combined = result.stdout + result.stderr
        self.assertNotIn("planner-bundle", combined)
        members = self.shipped_context_members(self.open_sids()[0])
        self.assertIn("notes/about.bale-bundle.md", members)


if __name__ == "__main__":
    unittest.main()
