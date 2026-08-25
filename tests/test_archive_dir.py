#!/usr/bin/env python3
"""Hermetic E2E for `[apply] archive_dir` (v0.3.30 — BALE.md §13's v0.5
response-archive candidate, landed; behavior in §8.8).

Drives real `bale pack` → `bale apply` runs through the piped PASS/merge
path and asserts the archival contract on its three faces:

- **configured**: whichever of the response's prose artifacts the
  tarball actually included (README.md, notes.md) lands under
  `<archive_dir>/<sid>/` as UNTRACKED working-tree copies after the
  merge, the closing banner names them, and the `--json` report carries
  the additive `archive` object;
- **unconfigured**: byte-for-byte today's behavior — no archive
  directory materializes, no banner row, `archive: null` in the json
  report;
- **copy failure**: a blocked destination after a successful merge is
  LOUD (banner + log) and never fatal — exit 0, tag present, merged
  content on the branch, the un-blocked sibling artifact still copied.

Plus the two adjacent surfaces this session touched:

- the rollback dirty-tree guard's shape-matched carve-out — untracked
  `<archive_dir>/<sid>/<artifact>` paths bale itself wrote do not block
  `bale rollback`, while unrelated untracked files under the same
  configured directory still refuse (BALE.md §9.2 step 3);
- the wizard trio's discoverable surface — `bale config init` walks
  `apply.archive_dir` at both layers and an Enter-through re-run
  preserves a set value (the renderer-preservation precedent).

Response tarballs are built by hand (computed hashes, real
validation.sh) per the test_hold_retry_e2e precedent — the ADR-0002
oracle is the documented contract, never a golden byte comparison.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_archive_dir.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
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
    run_bale_pty,
    run_checked,
    slow,
)

ARCHIVE_DIR = "claude/responses"

README_BODY = "# Response brief\n\narchive-dir fixture readme.\n"
NOTES_BODY = "# Notes\n\narchive-dir fixture notes.\n"
NEW_CONTENT = "hello from the archive-dir fixture\n"


class ArchiveDirBase(unittest.TestCase):
    """Shared sandbox + fixture builders for the suites below."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-archive-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def configure_archive_dir(self, value: str = ARCHIVE_DIR) -> None:
        """Hand-edit is a valid write path for bale.toml (the wizard is
        canonical but not exclusive); commit it so the pre-flight
        clean-tree guard on the target branch stays satisfied."""
        (self.repo / "bale.toml").write_text(
            f'[apply]\narchive_dir = "{value}"\n', encoding="utf-8")
        env = git_env(self.home)
        run_checked(["git", "add", "bale.toml"], cwd=self.repo, env=env)
        run_checked(["git", "commit", "-m", "configure archive_dir"],
                    cwd=self.repo, env=env)

    def packed_sid(self) -> str:
        result = run_bale(
            self.install,
            [
                "pack", "archive-dir e2e goal: rewrite hello.txt",
                "--slug", "archive-dir",
                "--include", "hello.txt",
                "--no-readme",
            ],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        return sids[0]

    def build_response_tarball(self, sid: str, *, name: str,
                               with_readme: bool = True,
                               with_notes: bool = True) -> Path:
        """A valid, PASSing normal response modifying hello.txt (in
        scope), optionally shipping the prose artifacts the archival
        mechanism copies. Sizes and hashes computed, never transcribed."""
        nnn = sid[-3:]
        rdir = self.tmp / name / f"response-{nnn}"
        (rdir / "files").mkdir(parents=True)
        data = NEW_CONTENT.encode("utf-8")
        (rdir / "files" / "hello.txt").write_bytes(data)
        manifest = {
            "session_id": sid,
            "responds_to": sid,
            "corrects": None,
            "response_kind": "normal",
            "summary": "archive-dir fixture: rewrite hello.txt with a "
                       "passing validation so the merge path runs",
            "changes": [
                {
                    "path": "hello.txt",
                    "action": "modified",
                    "reason": "the goal's rewrite; the change itself is "
                              "incidental — the fixture exists to drive "
                              "the applied outcome",
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            ],
            "deferred": [],
            "validation_will_run": ["fixture check"],
            "claims": {},
        }
        (rdir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (rdir / "apply.sh").write_text(
            "#!/usr/bin/env bash\n# no-op (test fixture)\nexit 0\n",
            encoding="utf-8")
        (rdir / "validation.sh").write_text(
            "#!/usr/bin/env bash\n"
            "echo \"[PASS] fixture check\"\n"
            "exit 0\n",
            encoding="utf-8")
        if with_readme:
            (rdir / "README.md").write_text(README_BODY, encoding="utf-8")
        if with_notes:
            (rdir / "notes.md").write_text(NOTES_BODY, encoding="utf-8")
        tarball = self.tmp / name / f"response-{nnn}.tar.gz"
        with tarfile.open(tarball, "w:gz") as tf:
            tf.add(str(rdir), arcname=f"response-{nnn}")
        return tarball

    def apply_merged(self, tarball: Path, *, json_mode: bool = False):
        """Run `bale apply` on the piped default path (PASS → merge)."""
        args = ["apply", str(tarball)]
        if json_mode:
            args.append("--json")
        result = run_bale(self.install, args, cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        return result

    def assert_merged(self, sid: str) -> None:
        env = git_env(self.home)
        run_checked(["git", "rev-parse", "--verify",
                     f"refs/tags/applied/{sid}"], cwd=self.repo, env=env)
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            NEW_CONTENT)

    def untracked_paths(self) -> list[str]:
        env = git_env(self.home)
        r = subprocess.run(
            ["git", "status", "--porcelain", "-uall"],
            cwd=self.repo, env=env, capture_output=True, text=True)
        return [line[3:] for line in r.stdout.splitlines()
                if line.startswith("?? ")]


class ArchiveOnMergeTest(ArchiveDirBase):
    """Configured path: the applied outcome copies the shipped prose
    artifacts to <archive_dir>/<sid>/, untracked, and says so."""

    @slow
    def test_configured_archives_shipped_artifacts(self) -> None:
        self.configure_archive_dir()
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="resp")
        result = self.apply_merged(tarball)
        self.assert_merged(sid)

        dest = self.repo / ARCHIVE_DIR / sid
        self.assertEqual(
            (dest / "README.md").read_text(encoding="utf-8"), README_BODY)
        self.assertEqual(
            (dest / "notes.md").read_text(encoding="utf-8"), NOTES_BODY)
        self.assertFalse(
            (dest / "next-prompt.md").exists(),
            msg="only artifacts the response actually shipped are copied")

        # The copies are untracked working-tree writes — never committed.
        untracked = self.untracked_paths()
        self.assertIn(f"{ARCHIVE_DIR}/{sid}/README.md", untracked)
        self.assertIn(f"{ARCHIVE_DIR}/{sid}/notes.md", untracked)

        # The closing banner carries the archive row naming the
        # destination (the row form, not the bare substring — this
        # fixture's slug itself contains "archive").
        self.assertIn("\n  archive:", result.stdout)
        self.assertIn(f"{ARCHIVE_DIR}/{sid}/", result.stdout)

    def test_configured_but_response_shipped_nothing(self) -> None:
        """A prose-less response archives nothing, and the banner says
        so explicitly rather than skipping silently."""
        self.configure_archive_dir()
        sid = self.packed_sid()
        tarball = self.build_response_tarball(
            sid, name="resp", with_readme=False, with_notes=False)
        result = self.apply_merged(tarball)
        self.assert_merged(sid)
        self.assertFalse((self.repo / ARCHIVE_DIR / sid).exists(),
                         msg="no artifacts shipped → no directory created")
        self.assertIn("nothing to archive", result.stdout)

    @slow
    def test_json_report_carries_archive_object(self) -> None:
        self.configure_archive_dir()
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="resp")
        result = self.apply_merged(tarball, json_mode=True)
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(payload["outcome"], "applied")
        self.assertEqual(payload["archive"], {
            "dir": f"{ARCHIVE_DIR}/{sid}",
            "copied": [f"{ARCHIVE_DIR}/{sid}/README.md",
                       f"{ARCHIVE_DIR}/{sid}/notes.md"],
            "failed": [],
        })


class UnconfiguredTest(ArchiveDirBase):
    """Unset key: today's behavior — no archival, no banner row, null in
    the json report."""

    def test_unset_key_archives_nothing(self) -> None:
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="resp")
        result = self.apply_merged(tarball, json_mode=True)
        self.assert_merged(sid)
        self.assertFalse((self.repo / ARCHIVE_DIR).exists())
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertIsNone(payload["archive"])
        # The human banner (stderr under --json) has no archive ROW — the
        # substring alone would false-positive on this fixture's own
        # "archive-dir" slug, so the assertion targets the summary-row
        # form format_summary_block renders.
        self.assertNotIn("\n  archive:", result.stderr,
                         msg="unset key must not surface an archive "
                             "banner row")


class CopyFailureTest(ArchiveDirBase):
    """A blocked copy after a successful merge is loud, partial where
    possible, and never fatal."""

    def test_blocked_destination_is_loud_never_fatal(self) -> None:
        self.configure_archive_dir()
        sid = self.packed_sid()
        # Block README.md's destination with a DIRECTORY so its
        # copyfile raises; notes.md's destination stays writable. The
        # blocker is untracked, which the merge path never touches.
        blocker = self.repo / ARCHIVE_DIR / sid / "README.md"
        blocker.mkdir(parents=True)
        tarball = self.build_response_tarball(sid, name="resp")
        result = self.apply_merged(tarball)

        # The merge itself landed and the exit code is the PASS 0 —
        # the archival failure did not un-apply or HOLD anything.
        self.assert_merged(sid)

        # Partial result: the un-blocked artifact still copied.
        self.assertEqual(
            (self.repo / ARCHIVE_DIR / sid / "notes.md")
            .read_text(encoding="utf-8"),
            NOTES_BODY)

        # Loud in the banner, naming the failed artifact.
        self.assertIn("copy FAILED", result.stdout)
        self.assertIn("README.md", result.stdout)

        # Loud in the session log too (the banner points at it).
        log_text = (self.repo / ".bale" / "logs" / f"{sid}.log").read_text(
            encoding="utf-8")
        self.assertIn("ARCHIVE FAILED", log_text)


class RollbackGuardCarveOutTest(ArchiveDirBase):
    """BALE.md §9.2 step 3: untracked archive artifacts bale itself
    wrote do not block rollback; unrelated untracked files under the
    same configured directory still refuse."""

    def merged_sid_with_archive(self) -> str:
        self.configure_archive_dir()
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="resp")
        self.apply_merged(tarball)
        self.assert_merged(sid)
        # Precondition for both tests: the archive copies sit untracked.
        untracked = self.untracked_paths()
        self.assertIn(f"{ARCHIVE_DIR}/{sid}/README.md", untracked)
        return sid

    def test_rollback_proceeds_past_bale_written_archives(self) -> None:
        sid = self.merged_sid_with_archive()
        result = run_bale(self.install, ["rollback", sid],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        env = git_env(self.home)
        run_checked(["git", "rev-parse", "--verify",
                     f"refs/tags/reverted/{sid}"], cwd=self.repo, env=env)
        # The archives survive the revert, still untracked.
        self.assertIn(f"{ARCHIVE_DIR}/{sid}/README.md",
                      self.untracked_paths())

    @slow
    def test_unrelated_untracked_file_still_refuses(self) -> None:
        """The carve-out is shape-matched: a stray untracked file under
        the configured directory that bale did not write keeps the
        guard's refusal."""
        sid = self.merged_sid_with_archive()
        stray = self.repo / ARCHIVE_DIR / "scratch.txt"
        stray.write_text("not bale's\n", encoding="utf-8")
        result = run_bale(self.install, ["rollback", sid],
                          cwd=self.repo, env=self.env)
        self.assertNotEqual(result.returncode, 0,
                            msg="a non-bale untracked file must refuse")
        self.assertIn("dirty", (result.stdout + result.stderr).lower())


class ArchiveDirWizardTest(ArchiveDirBase):
    """The wizard trio's discoverable surface: apply.archive_dir is
    walked at both layers and preserved on an Enter-through re-run."""

    def test_project_wizard_walks_and_preserves_the_key(self) -> None:
        (self.repo / "bale.toml").write_text(
            f'[apply]\narchive_dir = "{ARCHIVE_DIR}"\n', encoding="utf-8")
        code, output = run_bale_pty(
            self.install, ["config", "init"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("apply.archive_dir", output,
                      msg="the project wizard walks the key — the "
                          "discoverable-surface contract")
        rendered = (self.repo / "bale.toml").read_text(encoding="utf-8")
        self.assertIn("[apply]", rendered)
        self.assertIn(f'archive_dir = "{ARCHIVE_DIR}"', rendered,
                      msg="Enter-through re-runs preserve the set value")

    def test_global_wizard_walks_the_key(self) -> None:
        """Unlike [validation], archive_dir is valid at both layers —
        the global wizard offers it too."""
        code, output = run_bale_pty(
            self.install, ["config", "init", "--global"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("apply.archive_dir", output)

    def test_malformed_key_refuses_at_preflight_not_post_merge(self) -> None:
        """An absolute archive_dir is fatal — and fatal BEFORE staging:
        the session stays open, nothing merged, no tag. The strict
        accessor resolves at apply pre-flight precisely so a typo can
        never fail() after a merge has landed."""
        self.configure_archive_dir("/absolute/escape")
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="resp")
        result = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("archive_dir", result.stdout + result.stderr)
        env = git_env(self.home)
        r = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/tags/applied/{sid}"],
            cwd=self.repo, env=env, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0,
                            msg="the refusal must precede any merge")
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            "hello\n", msg="working tree untouched by the refusal")


if __name__ == "__main__":
    unittest.main(verbosity=2)
