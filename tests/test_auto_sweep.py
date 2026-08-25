#!/usr/bin/env python3
"""Hermetic E2E for `[apply] sweep` (v0.3.32 — the config-gated
auto-sweep commit of bale-written bookkeeping; behavior in BALE.md
§8.8).

Drives real `bale pack` → `bale apply` / `bale unlock` /
`bale rollback` runs and asserts the ratified rails:

- **enabled happy path**: the applied outcome commits exactly the
  bale-owned files this invocation wrote — the telemetry record plus
  the archive_dir copies — as `[bale sweep <sid>] applied` on top of
  the merge, the banner carries the sweep row, and an operator's
  unrelated dirty files are untouched (the deliberately dirtied
  fixture, on both the untracked and the staged face);
- **disabled/unset**: byte-identical to today — no sweep output, no
  commit beyond the merge, the record left untracked;
- **nothing to commit**: an event that wrote nothing sweeps nothing,
  loudly;
- **degenerate skip**: a detached HEAD logs the skip, leaves the
  files for a manual sweep, and never fails the parent command;
- **guard interaction**: the rollback → `--undo` toggle completes
  under sweep because each clean rollback commits its own telemetry
  append (BALE.md §9.2 step 3) — the sweep runs post-guard-window
  and the carve-out is unchanged;
- **json visibility** (v0.3.34): the additive `sweep` object on the
  apply and unlock `--json` lines mirrors sweep_commit's return —
  committed with sha and files, skipped with the reason, null when
  the key is unset — without disturbing the stream discipline;
- **wizard trio**: `bale config init` walks `apply.sweep` at both
  layers and an Enter-through re-run preserves a set value.

Response tarballs are built by hand (computed hashes, real
validation.sh) per the test_archive_dir precedent — the ADR-0002
oracle is the documented contract, never a golden byte comparison.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_auto_sweep.py

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

README_BODY = "# Response brief\n\nauto-sweep fixture readme.\n"
NOTES_BODY = "# Notes\n\nauto-sweep fixture notes.\n"
NEW_CONTENT = "hello from the auto-sweep fixture\n"


class AutoSweepBase(unittest.TestCase):
    """Shared sandbox + fixture builders for the suites below."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-sweep-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def configure(self, *, sweep: bool, archive: bool) -> None:
        """Hand-edit is a valid write path for bale.toml (the wizard is
        canonical but not exclusive); commit it so the pre-flight
        clean-tree guard on the target branch stays satisfied."""
        lines = ["[apply]"]
        if archive:
            lines.append(f'archive_dir = "{ARCHIVE_DIR}"')
        lines.append(f"sweep = {'true' if sweep else 'false'}")
        (self.repo / "bale.toml").write_text(
            "\n".join(lines) + "\n", encoding="utf-8")
        env = git_env(self.home)
        run_checked(["git", "add", "bale.toml"], cwd=self.repo, env=env)
        run_checked(["git", "commit", "-m", "configure bale.toml"],
                    cwd=self.repo, env=env)

    def packed_sid(self) -> str:
        result = run_bale(
            self.install,
            [
                "pack", "auto-sweep e2e goal: rewrite hello.txt",
                "--slug", "auto-sweep",
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

    def build_response_tarball(self, sid: str, *, name: str) -> Path:
        """A valid, PASSing normal response modifying hello.txt (in
        scope), shipping the prose artifacts the archival mechanism
        copies. Sizes and hashes computed, never transcribed."""
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
            "summary": "auto-sweep fixture: rewrite hello.txt with a "
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
        (rdir / "README.md").write_text(README_BODY, encoding="utf-8")
        (rdir / "notes.md").write_text(NOTES_BODY, encoding="utf-8")
        tarball = self.tmp / name / f"response-{nnn}.tar.gz"
        with tarfile.open(tarball, "w:gz") as tf:
            tf.add(str(rdir), arcname=f"response-{nnn}")
        return tarball

    def apply_merged(self, tarball: Path):
        """Run `bale apply` on the piped default path (PASS → merge)."""
        result = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        return result

    # -- git probes ------------------------------------------------------

    def git_out(self, *args: str) -> str:
        env = git_env(self.home)
        r = subprocess.run(["git", *args], cwd=self.repo, env=env,
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 0,
                         msg=f"git {args}: {r.stdout}\n{r.stderr}")
        return r.stdout

    def head_subject(self) -> str:
        return self.git_out("log", "-1", "--pretty=%s").strip()

    def head_files(self) -> list:
        out = self.git_out("show", "--name-only", "--pretty=format:",
                           "HEAD")
        return sorted(line for line in out.splitlines() if line.strip())

    def untracked_paths(self) -> list:
        env = git_env(self.home)
        r = subprocess.run(
            ["git", "status", "--porcelain", "-uall"],
            cwd=self.repo, env=env, capture_output=True, text=True)
        return [line[3:] for line in r.stdout.splitlines()
                if line.startswith("?? ")]


class SweepOnMergeTest(AutoSweepBase):
    """Enabled happy path: the applied outcome commits exactly the
    bale-owned files, loudly, with operator dirt untouched."""

    @slow
    def test_enabled_commits_owned_files_only(self) -> None:
        self.configure(sweep=True, archive=True)
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="resp")
        # The deliberately dirtied fixture (untracked face — a tracked
        # change on the target-branch checkout would be refused by the
        # §8.1 step-5 guard before the sweep is ever reached; the
        # staged face is exercised on the unlock trigger below, which
        # has no such pre-flight).
        scratch = self.repo / "scratch.txt"
        scratch.write_text("operator's own dirt\n", encoding="utf-8")

        result = self.apply_merged(tarball)

        # The sweep commit sits on top of the merge: HEAD is the sweep
        # commit with the conventioned message; HEAD^ is the tagged
        # merge commit.
        self.assertEqual(self.head_subject(), f"[bale sweep {sid}] applied")
        self.assertEqual(
            self.git_out("rev-parse", "HEAD^").strip(),
            self.git_out("rev-parse", f"refs/tags/applied/{sid}").strip())

        # Exactly the owned set: the telemetry record plus the two
        # archive copies this invocation wrote — nothing else.
        self.assertEqual(self.head_files(), sorted([
            f"claude/telemetry/{sid}.json",
            f"{ARCHIVE_DIR}/{sid}/README.md",
            f"{ARCHIVE_DIR}/{sid}/notes.md",
        ]))

        # Operator dirt untouched by construction.
        self.assertIn("scratch.txt", self.untracked_paths())

        # Loud: the log line and the banner row both name the commit.
        self.assertIn("sweep: committed 3 file(s) as ", result.stdout)
        self.assertIn("\n  sweep:", result.stdout)

        # The swept paths are now tracked and clean.
        self.assertIn(f"claude/telemetry/{sid}.json",
                      self.git_out("ls-files", "claude/telemetry"))
        status = self.git_out("status", "--porcelain", "--",
                              "claude/telemetry", ARCHIVE_DIR)
        self.assertEqual(status.strip(), "",
                         msg="swept paths must be committed clean")

    def test_unlock_commits_record_and_leaves_staged_dirt(self) -> None:
        """The unlock trigger (via close_session_with_record): commits
        the closure record with the closure_reason as the event, and an
        operator's STAGED unrelated change stays staged and out of the
        sweep commit — the pathspec-commit contract."""
        self.configure(sweep=True, archive=False)
        sid = self.packed_sid()
        # Staged operator dirt: modify + stage a tracked file. Unlock
        # performs no git mutation of its own and has no dirty-tree
        # pre-flight, so this face is testable here.
        (self.repo / "hello.txt").write_text("staged edit\n",
                                             encoding="utf-8")
        env = git_env(self.home)
        run_checked(["git", "add", "hello.txt"], cwd=self.repo, env=env)

        result = run_bale(self.install, ["unlock", sid],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

        self.assertEqual(self.head_subject(),
                         f"[bale sweep {sid}] abandoned")
        self.assertEqual(self.head_files(),
                         [f"claude/telemetry/{sid}.json"])
        self.assertIn("sweep: committed 1 file(s) as ", result.stdout)

        # The staged edit is still staged, untouched by the sweep.
        staged = self.git_out("diff", "--cached", "--name-only")
        self.assertIn("hello.txt", staged.splitlines())


class UnsetByteIdentityTest(AutoSweepBase):
    """Unset/false key: today's behavior — no sweep output, no commit
    beyond the merge, the record left untracked."""

    def test_unset_key_never_commits_or_speaks(self) -> None:
        self.configure(sweep=False, archive=True)
        # configure() writes `sweep = false` — the explicit-false face;
        # the absent-key face rides every other suite in this repo's
        # test corpus, which never sets the key.
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="resp")
        result = self.apply_merged(tarball)

        # HEAD is the merge commit itself — nothing on top.
        self.assertEqual(
            self.git_out("rev-parse", "HEAD").strip(),
            self.git_out("rev-parse", f"refs/tags/applied/{sid}").strip())

        # No sweep line, no sweep banner row.
        self.assertNotIn("sweep:", result.stdout)

        # The record and archives sit untracked — today's contract.
        untracked = self.untracked_paths()
        self.assertIn(f"claude/telemetry/{sid}.json", untracked)
        self.assertIn(f"{ARCHIVE_DIR}/{sid}/README.md", untracked)


class NothingToCommitTest(AutoSweepBase):
    """An event that wrote nothing sweeps nothing — loudly."""

    def test_failed_record_write_sweeps_nothing(self) -> None:
        self.configure(sweep=True, archive=False)
        sid = self.packed_sid()
        # Block the telemetry write: claude/telemetry as a FILE makes
        # write_telemetry_record's mkdir fail (logged, swallowed, None
        # returned) — the event then wrote nothing this invocation.
        claude_dir = self.repo / "claude"
        claude_dir.mkdir()
        (claude_dir / "telemetry").write_text("blocker\n",
                                              encoding="utf-8")
        head_before = self.git_out("rev-parse", "HEAD").strip()

        result = run_bale(self.install, ["unlock", sid],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("sweep: nothing to commit", result.stdout)
        self.assertEqual(self.git_out("rev-parse", "HEAD").strip(),
                         head_before,
                         msg="nothing to commit must commit nothing")


class DegenerateSkipTest(AutoSweepBase):
    """A detached HEAD skips loudly, leaves the files for a manual
    sweep, and never fails the parent command."""

    def test_detached_head_skips_loudly(self) -> None:
        self.configure(sweep=True, archive=False)
        sid = self.packed_sid()
        env = git_env(self.home)
        run_checked(["git", "checkout", "--detach", "--quiet"],
                    cwd=self.repo, env=env)
        head_before = self.git_out("rev-parse", "HEAD").strip()

        result = run_bale(self.install, ["unlock", sid],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("sweep: skipped", result.stdout)
        self.assertIn("detached HEAD", result.stdout)
        self.assertIn("manual sweep", result.stdout)
        # No commit; the record is left on disk for the manual sweep.
        self.assertEqual(self.git_out("rev-parse", "HEAD").strip(),
                         head_before)
        self.assertIn(f"claude/telemetry/{sid}.json",
                      self.untracked_paths())


class RollbackToggleTest(AutoSweepBase):
    """The guard interaction as implemented (BALE.md §9.2 step 3): the
    rollback and --undo triggers each sweep their own telemetry append,
    so the toggle completes under sweep with no --stash and no manual
    interleaved commit."""

    def test_rollback_then_undo_completes_clean(self) -> None:
        self.configure(sweep=True, archive=True)
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="resp")
        self.apply_merged(tarball)
        self.assertEqual(self.head_subject(), f"[bale sweep {sid}] applied")

        result = run_bale(self.install, ["rollback", sid],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertEqual(self.head_subject(),
                         f"[bale sweep {sid}] rolled-back")
        self.assertIn("sweep: committed 1 file(s) as ", result.stdout)

        # The toggle back: the swept append left the tree clean, so
        # --undo needs neither --stash nor --force.
        result = run_bale(self.install, ["rollback", sid, "--undo"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertEqual(self.head_subject(),
                         f"[bale sweep {sid}] re-applied")
        # Net state: re-applied content, clean tree modulo nothing —
        # the archives were committed at apply, the record at each hop.
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            NEW_CONTENT)
        self.assertEqual(
            self.git_out("status", "--porcelain", "-uall").strip(), "",
            msg="every bale-written file swept; nothing left dirty")


class SweepJsonTest(AutoSweepBase):
    """The v0.3.34 json visibility surface: the additive `sweep` object
    on the apply and unlock json lines mirrors sweep_commit's return —
    an operator dispatching on the json line sees whether bookkeeping
    landed without reading stderr. Key contract: format_apply_json's
    docstring (the sub-object's one home); null = no sweep ran."""

    def parse_single_json_line(self, stdout: str) -> dict:
        lines = [ln for ln in stdout.splitlines() if ln.strip()]
        self.assertEqual(
            len(lines), 1,
            msg=f"expected exactly one stdout line under --json; got "
                f"{len(lines)}:\n{stdout}")
        payload = json.loads(lines[0])
        self.assertIsInstance(payload, dict)
        return payload

    @slow
    def test_applied_json_carries_committed_sweep_object(self) -> None:
        """Enabled happy path under --json: outcome applied, sweep is
        the committed object — status, the loud detail line, the short
        sha, and exactly the owned file set."""
        self.configure(sweep=True, archive=True)
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="resp")

        result = run_bale(self.install,
                          ["apply", str(tarball), "--json"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        payload = self.parse_single_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "applied")
        sweep = payload["sweep"]
        self.assertEqual(sweep["status"], "committed")
        self.assertTrue(sweep["detail"].startswith("committed 3 file(s)"))
        self.assertTrue(sweep["sha"],
                        msg="the committed form carries the short sha")
        self.assertEqual(
            self.git_out("rev-parse", "--short", "HEAD").strip(),
            sweep["sha"],
            msg="the sha names the sweep commit the json line reports")
        self.assertEqual(sorted(sweep["files"]), sorted([
            f"claude/telemetry/{sid}.json",
            f"{ARCHIVE_DIR}/{sid}/README.md",
            f"{ARCHIVE_DIR}/{sid}/notes.md",
        ]))
        # The human sweep line moved to stderr with the rest of the
        # trail — the stream discipline is untouched by the new key.
        self.assertIn("sweep: committed", result.stderr)

    @slow
    def test_applied_json_sweep_null_when_unset(self) -> None:
        """The additive-null contract: [apply].sweep unset/false keeps
        the report shape with sweep: null — byte-identical semantics to
        the pre-key report modulo the additive key."""
        self.configure(sweep=False, archive=False)
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="resp")

        result = run_bale(self.install,
                          ["apply", str(tarball), "--json"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        payload = self.parse_single_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "applied")
        self.assertIsNone(payload["sweep"])

    def test_unlock_json_carries_committed_sweep_object(self) -> None:
        """The unlock surface: the closure record's sweep rides the
        top-level key — status committed, files exactly the record."""
        self.configure(sweep=True, archive=False)
        sid = self.packed_sid()

        result = run_bale(self.install, ["unlock", "--json"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        payload = self.parse_single_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "unlocked")
        sweep = payload["sweep"]
        self.assertEqual(sweep["status"], "committed")
        self.assertEqual(sweep["files"],
                         [f"claude/telemetry/{sid}.json"])
        self.assertEqual(self.head_subject(),
                         f"[bale sweep {sid}] abandoned",
                         msg="the event stamp is the closure_reason")

    def test_unlock_json_skipped_object_names_the_reason(self) -> None:
        """The degenerate-skip face on the json surface: a detached
        HEAD reports status skipped, the reason in detail, sha null,
        files empty — the loud skip, machine-readable."""
        self.configure(sweep=True, archive=False)
        sid = self.packed_sid()
        env = git_env(self.home)
        run_checked(["git", "checkout", "--detach", "--quiet"],
                    cwd=self.repo, env=env)

        result = run_bale(self.install, ["unlock", sid, "--json"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        payload = self.parse_single_json_line(result.stdout)
        sweep = payload["sweep"]
        self.assertEqual(sweep["status"], "skipped")
        self.assertIn("detached HEAD", sweep["detail"])
        self.assertIsNone(sweep["sha"])
        self.assertEqual(sweep["files"], [])


class SweepWizardTest(AutoSweepBase):
    """The wizard trio's discoverable surface: apply.sweep is walked at
    both layers and preserved on an Enter-through re-run."""

    def test_project_wizard_walks_and_preserves_the_key(self) -> None:
        (self.repo / "bale.toml").write_text(
            "[apply]\nsweep = true\n", encoding="utf-8")
        code, output = run_bale_pty(
            self.install, ["config", "init"],
            cwd=self.repo, env=self.env, answers="\n" * 48)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("apply.sweep", output,
                      msg="the project wizard walks the key — the "
                          "discoverable-surface contract")
        rendered = (self.repo / "bale.toml").read_text(encoding="utf-8")
        self.assertIn("[apply]", rendered)
        self.assertIn("sweep = true", rendered,
                      msg="Enter-through re-runs preserve the set value")

    def test_global_wizard_walks_the_key(self) -> None:
        code, output = run_bale_pty(
            self.install, ["config", "init", "--global"],
            cwd=self.repo, env=self.env, answers="\n" * 48)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("apply.sweep", output)


if __name__ == "__main__":
    unittest.main(verbosity=2)
