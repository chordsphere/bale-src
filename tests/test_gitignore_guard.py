#!/usr/bin/env python3
"""The .bale/ gitignore guard asks git, and writes only when nothing ignores.

Pins ``ensure_bale_gitignored`` (bin/bale section 7) on its two callers,
``bale pack`` and ``bale handoff``, after the 0.4.56 change: the guard
asks git (``git check-ignore -v -- .bale/``) whether ``.bale/`` is
already ignored from any source and leaves ``.gitignore`` alone when it
is. Before 0.4.56 it decided from the ``.gitignore`` text alone, so a
clone whose owner had put ``.bale/`` in ``.git/info/exclude`` (the
office's ``projects add --prepare`` does exactly that) got a tracked
``.gitignore`` written and committed on its first pack — the report
that opened this work.

What is pinned, per row of the session's outcome contract:

- **Already ignored, from each source** (a tracked ``.gitignore``,
  ``.git/info/exclude`` — the shape the report hit — and a
  ``core.excludesFile``): a first ``bale pack`` creates no
  ``.gitignore``, changes no byte of an existing one, makes no commit,
  leaves the tree as clean as it found it, and says in one log line
  that ``.bale/`` is already ignored, naming the source.
- **Nothing ignores**: unchanged behavior. ``.bale/`` is appended to
  ``.gitignore`` (created when absent, with the blank-line courtesy
  when the file lacks a trailing newline); a clean tree gets the
  auto-commit ``bale: ignore .bale/`` as HEAD, a dirty tree keeps the
  change uncommitted with the standing warning.
- **``bale handoff``** behaves the same on both rows — the fix lives
  in the one helper both callers share.
- **Git cannot answer** (exit 128, no git on PATH): logged, then the
  pre-0.4.56 text rule decides — never a silent skip, never a silent
  "treat as ignored". Pinned in-process through the harness's
  ``_load_cli`` loader, with ``run`` patched to stand in for the
  failure; the E2E path cannot provoke a 128 in a healthy repo.

Every fixture repo is fresh and its ``HOME`` is the harness's sandbox
home — a ``.gitconfig`` with the test identity and nothing else — so
the machine's own global excludes cannot leak into a verdict. The
in-process cases patch ``HOME`` and ``XDG_CONFIG_HOME`` to the same
sandbox for the same reason. The query carries the trailing slash on
purpose (``BALE_DIR_IGNORE_QUERY``): a directory-only pattern does not
match a bare ``.bale`` that does not exist yet, and on a first pack it
does not.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring. Every bale
invocation here is piped (stdin is not a TTY), so no prompt path may
engage.

Run directly::

    python3 tests/test_gitignore_guard.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from harness import (
    SUBPROCESS_TIMEOUT,
    _load_cli,
    bale_env,
    build_response_dir,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    tar_response_dir,
)

GOAL = "gitignore guard test goal: nothing about hello.txt"
SLUG = "gitignore-guard"

# Sentinels for the surfaces this file pins, kept in one place so a
# rewording breaks one line, not several assertions.
AUTO_COMMIT_SUBJECT = "bale: ignore .bale/"
ALREADY_IGNORED_MARKER = ".bale/ is already ignored ("
LEAVING_ALONE_MARKER = "leaving .gitignore alone"
NOT_COMMITTED_MARKER = ".gitignore was modified but not auto-committed"
CANNOT_ASK_MARKER = "could not ask git whether .bale/ is ignored ("
EXCLUDE_FILE = Path(".git") / "info" / "exclude"


class GitignoreGuardBase(unittest.TestCase):
    """Shared sandbox plumbing: a fresh repo per test, sandbox HOME."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-gitignore-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- git readers and fixture writers ----------------------------------

    def git(self, *args: str) -> str:
        """Run git in the fixture repo under the sandbox env; return stdout."""
        r = subprocess.run(
            ["git", *args], cwd=self.repo, env=git_env(self.home),
            capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT,
        )
        if r.returncode != 0:
            raise AssertionError(
                f"git {' '.join(args)} failed: exit={r.returncode}\n"
                f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        return r.stdout

    def head(self) -> str:
        return self.git("rev-parse", "HEAD").strip()

    def subjects(self) -> list:
        return self.git("log", "--format=%s").splitlines()

    def status(self) -> str:
        return self.git("status", "--porcelain")

    def exclude_bale(self) -> None:
        """Put `.bale/` in .git/info/exclude — the shape the report hit."""
        exclude = self.repo / EXCLUDE_FILE
        exclude.parent.mkdir(parents=True, exist_ok=True)
        with exclude.open("a", encoding="utf-8") as f:
            f.write(".bale/\n")

    def commit_gitignore(self, text: str) -> bytes:
        """Write and commit a .gitignore with `text`; return its bytes."""
        gi = self.repo / ".gitignore"
        gi.write_text(text, encoding="utf-8")
        self.git("add", ".gitignore")
        self.git("commit", "-q", "-m", "project .gitignore")
        return gi.read_bytes()

    def set_core_excludes_file(self, text: str) -> Path:
        """A core.excludesFile under the sandbox HOME holding `text`,
        configured through the sandbox's own global .gitconfig."""
        p = self.home / "global-excludes"
        p.write_text(text, encoding="utf-8")
        self.git("config", "--global", "core.excludesFile", str(p))
        return p

    # -- bale invocations ---------------------------------------------------

    def pack(self):
        """A fully specified piped first pack over hello.txt."""
        return run_bale(
            self.install,
            ["pack", GOAL, "--slug", SLUG,
             "--include", "hello.txt", "--no-readme"],
            cwd=self.repo, env=self.env,
        )

    def assert_ok(self, r) -> None:
        self.assertEqual(
            r.returncode, 0,
            msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")

    # -- shared assertions -------------------------------------------------

    def assert_left_alone(self, r, head_before: str, *, source: str) -> None:
        """Row 1: no auto-commit, tree clean, one log line naming `source`."""
        self.assertEqual(self.head(), head_before, msg="a commit was made")
        self.assertNotIn(AUTO_COMMIT_SUBJECT, self.subjects())
        # Not an empty porcelain: a session open writes its telemetry
        # record on the tracked side (claude/telemetry/<sid>.json, BALE.md
        # section 8.9), untracked until the user's next commit. What the
        # row forbids is any trace of .gitignore in the status.
        self.assertNotIn(".gitignore", self.status(),
                         msg=f".gitignore shows in the status:\n{self.status()}")
        lines = [ln for ln in r.stdout.splitlines()
                 if ALREADY_IGNORED_MARKER in ln]
        self.assertEqual(len(lines), 1,
                         msg=f"expected one already-ignored line:\n{r.stdout}")
        self.assertIn(source, lines[0])
        self.assertIn(LEAVING_ALONE_MARKER, lines[0])


# ---------------------------------------------------------------------------
# bale pack: already ignored, from each source
# ---------------------------------------------------------------------------
#
class PackAlreadyIgnoredTest(GitignoreGuardBase):
    """Row 1 on the pack path: git already ignores .bale/, from any
    source, and the first pack writes nothing and commits nothing."""

    def test_info_exclude_pack_creates_no_gitignore_and_no_commit(
            self) -> None:
        """The report's shape: .git/info/exclude holds .bale/, no
        .gitignore exists. After the pack there is still none."""
        self.exclude_bale()
        head_before = self.head()
        r = self.pack()
        self.assert_ok(r)
        self.assertFalse((self.repo / ".gitignore").exists(),
                         msg=".gitignore was created")
        self.assert_left_alone(r, head_before, source=".git/info/exclude:")
        # The pack itself happened: its outbox landed under .bale/.
        self.assertTrue((self.repo / ".bale" / "outbox").is_dir())

    def test_info_exclude_leaves_existing_gitignore_byte_identical(
            self) -> None:
        """A tracked .gitignore that does not mention .bale/ keeps every
        byte when the exclude file already ignores the directory."""
        before = self.commit_gitignore("*.log\nbuild/\n")
        self.exclude_bale()
        head_before = self.head()
        r = self.pack()
        self.assert_ok(r)
        self.assertEqual((self.repo / ".gitignore").read_bytes(), before,
                         msg=".gitignore bytes changed")
        self.assert_left_alone(r, head_before, source=".git/info/exclude:")

    def test_tracked_gitignore_already_lists_bale(self) -> None:
        """The pre-0.4.56 happy case still holds, now with git as the
        judge: the log names .gitignore as the source."""
        before = self.commit_gitignore("*.log\n.bale/\n")
        head_before = self.head()
        r = self.pack()
        self.assert_ok(r)
        self.assertEqual((self.repo / ".gitignore").read_bytes(), before)
        self.assert_left_alone(r, head_before, source=".gitignore:2:.bale/")

    def test_core_excludes_file_already_ignores(self) -> None:
        """A core.excludesFile under the sandbox HOME is a source too;
        the log names that file by path."""
        excludes = self.set_core_excludes_file(".bale/\n")
        head_before = self.head()
        r = self.pack()
        self.assert_ok(r)
        self.assertFalse((self.repo / ".gitignore").exists())
        self.assert_left_alone(r, head_before, source=str(excludes))


# ---------------------------------------------------------------------------
# bale pack: nothing ignores — the unchanged behavior
# ---------------------------------------------------------------------------
#
class PackNothingIgnoresTest(GitignoreGuardBase):
    """Row 2 on the pack path: nothing ignores .bale/, so .gitignore
    gets the line and a clean tree gets the auto-commit."""

    def test_no_gitignore_is_created_and_committed(self) -> None:
        head_before = self.head()
        r = self.pack()
        self.assert_ok(r)
        self.assertEqual((self.repo / ".gitignore").read_text(
            encoding="utf-8"), ".bale/\n")
        self.assertNotEqual(self.head(), head_before)
        self.assertEqual(self.subjects()[0], AUTO_COMMIT_SUBJECT)
        self.assertNotIn(".gitignore", self.status())
        self.assertNotIn(ALREADY_IGNORED_MARKER, r.stdout)

    def test_existing_gitignore_gets_the_line_appended_and_committed(
            self) -> None:
        """A tracked .gitignore without .bale/ (and without a trailing
        newline) gains the line on its own line; the commit follows."""
        self.commit_gitignore("*.log")
        r = self.pack()
        self.assert_ok(r)
        self.assertEqual((self.repo / ".gitignore").read_text(
            encoding="utf-8"), "*.log\n.bale/\n")
        self.assertEqual(self.subjects()[0], AUTO_COMMIT_SUBJECT)
        self.assertNotIn(".gitignore", self.status())

    def test_dirty_tree_appends_without_committing(self) -> None:
        """Other uncommitted work: the line is written, the commit is
        not, and the standing warning says so."""
        (self.repo / "wip.txt").write_text("mid-work\n", encoding="utf-8")
        head_before = self.head()
        r = self.pack()
        self.assert_ok(r)
        self.assertEqual((self.repo / ".gitignore").read_text(
            encoding="utf-8"), ".bale/\n")
        self.assertEqual(self.head(), head_before)
        self.assertNotIn(AUTO_COMMIT_SUBJECT, self.subjects())
        self.assertIn(NOT_COMMITTED_MARKER, r.stdout)
        self.assertIn("?? .gitignore", self.status())
        self.assertIn("?? wip.txt", self.status())


# ---------------------------------------------------------------------------
# bale handoff: the same guard, the same two rows
# ---------------------------------------------------------------------------
#
class HandoffGitignoreGuardTest(GitignoreGuardBase):
    """`bale handoff` runs the same helper before its own gates, so the
    two rows hold there too. The fixture is tests/test_handoff_happy.py's
    in miniature: pack, apply a bailout (which closes the session, the
    state handoff requires), then hand off."""

    def pack_and_apply_bailout(self) -> Path:
        """Pack over hello.txt, apply a schema-valid bailout against it,
        return the bailout tarball handoff takes."""
        self.assert_ok(self.pack())
        sessions = self.repo / ".bale" / "sessions"
        opens = sorted(d.name for d in sessions.iterdir()
                       if (d / "open").is_file())
        self.assertEqual(len(opens), 1, msg=f"open sessions: {opens}")
        sid = opens[0]
        rdir = build_response_dir(
            self.tmp / "bailout", sid,
            summary="bailout fixture: the goal did not fit the budget; "
                    "handoff.md prescribes the next session",
            entries=[], validation_will_run=[], claims={},
            manifest_extra={"response_kind": "bailout"},
        )
        (rdir / "handoff.md").write_text(
            f"# Handoff\n\n## Original goal\n\n{GOAL}\n", encoding="utf-8")
        diagnostics = {
            "session_id": sid,
            "bail_trigger": "mid-build-budget-panic",
            "bail_narrative": "fixture narrative: the change set outgrew "
                              "the estimate mid-build.",
            "context_loaded": [
                {"path": "hello.txt", "verdict": "necessary", "note": ""},
            ],
            "exploration_paths": [
                {"what": "sized the change set", "verdict": "productive",
                 "note": ""},
            ],
            "tool_calls_summary": {"bash": 3},
            "what_would_save_next_time": ["split the goal at the seam"],
        }
        (rdir / "diagnostics.json").write_text(
            json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
        tarball = tar_response_dir(rdir)
        self.assert_ok(run_bale(self.install, ["apply", str(tarball)],
                                cwd=self.repo, env=self.env))
        return tarball

    def commit_everything(self, subject: str) -> None:
        """Commit whatever apply left in the tree (the telemetry record
        lands untracked at apply close, BALE.md section 8.9), so the
        handoff below starts from a clean tree."""
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "-m", subject)

    def handoff(self, tarball: Path):
        return run_bale(self.install, ["handoff", str(tarball)],
                        cwd=self.repo, env=self.env)

    def test_handoff_leaves_gitignore_alone_when_exclude_ignores(
            self) -> None:
        """Row 1 on the handoff path: .git/info/exclude ignores .bale/
        from the start, so neither the pack nor the handoff writes a
        .gitignore or commits."""
        self.exclude_bale()
        tarball = self.pack_and_apply_bailout()
        self.assertFalse((self.repo / ".gitignore").exists(),
                         msg="the pack wrote a .gitignore")
        self.commit_everything("record the applied bailout")
        head_before = self.head()
        r = self.handoff(tarball)
        self.assert_ok(r)
        self.assertFalse((self.repo / ".gitignore").exists(),
                         msg="the handoff wrote a .gitignore")
        self.assert_left_alone(r, head_before, source=".git/info/exclude:")

    def test_handoff_appends_and_commits_when_nothing_ignores(self) -> None:
        """Row 2 on the handoff path: with the pack's .gitignore removed
        and nothing else ignoring .bale/, the handoff writes the line and
        auto-commits it as HEAD."""
        tarball = self.pack_and_apply_bailout()
        self.assertEqual((self.repo / ".gitignore").read_text(
            encoding="utf-8"), ".bale/\n", msg="the pack's own write")
        # Stage apply's leftovers while .bale/ is still ignored, then drop
        # the .gitignore in the same commit: afterwards nothing ignores
        # .bale/ and the tree is otherwise clean.
        self.git("add", "-A")
        self.git("rm", "-q", ".gitignore")
        self.git("commit", "-q", "-m", "drop the .gitignore")
        self.assertIn("?? .bale/", self.status())
        r = self.handoff(tarball)
        self.assert_ok(r)
        self.assertEqual((self.repo / ".gitignore").read_text(
            encoding="utf-8"), ".bale/\n")
        self.assertEqual(self.subjects()[0], AUTO_COMMIT_SUBJECT)
        self.assertNotIn(".gitignore", self.status())


# ---------------------------------------------------------------------------
# In-process: git_check_ignore's verdicts, and the guard when git is mute
# ---------------------------------------------------------------------------
#
class GitCheckIgnoreUnitTest(unittest.TestCase):
    """bin/bale's `git_check_ignore` and `ensure_bale_gitignored` called
    directly through the harness loader. Both stay inside bin/bale (they
    call its own `run` and `log`), so the loader's structural limit does
    not bite. `run` is patched to stand in for the failures a healthy
    repo cannot produce; the real-git cases run under the sandbox HOME."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-ci-unit-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.cli = _load_cli()
        self.logged: list = []
        self._log_patch = mock.patch.object(
            self.cli, "log",
            side_effect=lambda msg, **kw: self.logged.append(msg))
        self._log_patch.start()
        # git reads HOME (and $XDG_CONFIG_HOME/git/ignore) for its global
        # excludes; point both at the sandbox so the machine's cannot leak.
        self._env_patch = mock.patch.dict(os.environ, {
            "HOME": str(self.home),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
        })
        self._env_patch.start()

    def tearDown(self) -> None:
        self._env_patch.stop()
        self._log_patch.stop()
        self._tmpdir.cleanup()

    def completed(self, code: int, *, stdout: str = "", stderr: str = ""):
        return subprocess.CompletedProcess(
            args=["git"], returncode=code, stdout=stdout, stderr=stderr)

    def test_query_carries_the_trailing_slash(self) -> None:
        self.assertEqual(self.cli.BALE_DIR_IGNORE_QUERY, ".bale/")

    def test_ignored_verdict_names_the_source(self) -> None:
        with (self.repo / EXCLUDE_FILE).open("a", encoding="utf-8") as f:
            f.write(".bale/\n")
        verdict, detail = self.cli.git_check_ignore(
            self.repo, self.cli.BALE_DIR_IGNORE_QUERY)
        self.assertIs(verdict, True)
        self.assertTrue(detail.startswith(".git/info/exclude:"), msg=detail)
        self.assertTrue(detail.endswith(":.bale/"), msg=detail)

    def test_not_ignored_verdict_is_false(self) -> None:
        verdict, detail = self.cli.git_check_ignore(
            self.repo, self.cli.BALE_DIR_IGNORE_QUERY)
        self.assertIs(verdict, False)
        self.assertEqual(detail, "")

    def test_bare_bale_does_not_match_a_directory_pattern_before_it_exists(
            self) -> None:
        """The git fact the trailing slash exists for, pinned so a future
        git that changes it is noticed here rather than in the field."""
        with (self.repo / EXCLUDE_FILE).open("a", encoding="utf-8") as f:
            f.write(".bale/\n")
        self.assertFalse((self.repo / ".bale").exists())
        bare, _ = self.cli.git_check_ignore(self.repo, ".bale")
        slashed, _ = self.cli.git_check_ignore(self.repo, ".bale/")
        self.assertIs(bare, False)
        self.assertIs(slashed, True)

    def test_exit_128_is_no_verdict_with_the_message(self) -> None:
        with mock.patch.object(self.cli, "run",
                               return_value=self.completed(
                                   128, stderr="fatal: boom\n")):
            verdict, detail = self.cli.git_check_ignore(self.repo, ".bale/")
        self.assertIsNone(verdict)
        self.assertIn("128", detail)
        self.assertIn("fatal: boom", detail)

    def test_missing_git_is_no_verdict(self) -> None:
        with mock.patch.object(self.cli, "run",
                               side_effect=FileNotFoundError("git")):
            verdict, detail = self.cli.git_check_ignore(self.repo, ".bale/")
        self.assertIsNone(verdict)
        self.assertEqual(detail, "git not found on PATH")

    def test_mute_git_falls_back_to_the_text_rule_and_says_so(self) -> None:
        """Git cannot answer: the guard logs that, then decides from the
        .gitignore text — appends when the line is absent, leaves the
        file alone when present — and never pretends to a verdict."""
        gi = self.repo / ".gitignore"
        with mock.patch.object(self.cli, "run",
                               return_value=self.completed(
                                   128, stderr="fatal: boom\n")):
            self.assertTrue(self.cli.ensure_bale_gitignored(self.repo))
            self.assertEqual(gi.read_text(encoding="utf-8"), ".bale/\n")
            self.assertTrue(any(CANNOT_ASK_MARKER in m for m in self.logged),
                            msg=self.logged)
            self.logged.clear()
            self.assertFalse(self.cli.ensure_bale_gitignored(self.repo))
            self.assertEqual(gi.read_text(encoding="utf-8"), ".bale/\n")
        self.assertTrue(any(CANNOT_ASK_MARKER in m for m in self.logged),
                        msg=self.logged)
        self.assertTrue(any("already lists .bale/" in m for m in self.logged),
                        msg=self.logged)

    def test_listed_but_negated_is_left_alone_with_a_note(self) -> None:
        """git says not ignored although .gitignore lists .bale/ (a later
        negation): no duplicate line, one note, no change reported."""
        gi = self.repo / ".gitignore"
        gi.write_text(".bale/\n!.bale/\n", encoding="utf-8")
        self.assertFalse(self.cli.ensure_bale_gitignored(self.repo))
        self.assertEqual(gi.read_text(encoding="utf-8"), ".bale/\n!.bale/\n")
        self.assertTrue(any("does not ignore it" in m for m in self.logged),
                        msg=self.logged)


if __name__ == "__main__":
    unittest.main()
