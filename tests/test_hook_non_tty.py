#!/usr/bin/env python3
"""The pack side's non-terminal hook decline (v0.4.55, session
2026-10-13-hook-non-tty-006).

The observation that started it: a hosted run opened a session with
exactly `bale open <bundle> --json` and stdin from /dev/null, and the
global `post_pack` hook printed its whole banner and `run this hook?`
to nobody, then logged "declined (stdin closed or interrupted)" — a
line naming the symptom, not the situation. Since this version
`run_hook` (bin/bale) does not offer a pack-side hook's prompt
(PACK_SIDE_HOOKS: post_pack) when stdin is not a terminal
(stdin_is_terminal): the banner still prints, the `default:` line and
the prompt do not, no configuration is consulted, nothing is recorded
in the acceptance store, and one fixed line is logged —
HOOK_DECLINE_LINE_NOT_A_TERMINAL, verbatim from the brief.

What this suite pins:

- **The constants** (``ConstantsTest``, in process): the fixed line
  byte for byte, on one physical line of bin/bale's source; the three
  board-83 HOOK_DECLINE_LINES unchanged; PACK_SIDE_HOOKS is exactly
  post_pack; stdin_is_terminal's four shapes (None, a non-terminal
  stream, a closed stream, a real pty).
- **run_hook in process** (``RunHookInProcessTest``): a non-terminal
  stdin never reaches input(); a terminal stdin still does, with the
  `default:` line and the answered-decline line as before.
- **Every pack-side path, piped** (stdin /dev/null, the harness's
  run_bale): the session pack (``SessionPackPipedTest``, human mode
  and `--json`, a global-layer and a project-layer hook), `bale
  handoff` (``HandoffPipedTest``), and the replay inside `bale open
  <bundle> --json` (``OpenReplayJsonTest``, the observed invocation:
  stdout exactly one JSON line). The context pack's piped decline is
  tests/test_context_pack.py's ContextPackHookTest, updated beside
  this suite. Each asserts the hook's marker file stays absent.
- **The terminal contract** (``TerminalStillPromptsTest``, through a
  pty as run_bale_pty drives it): a global-layer hook still shows
  `default: accept`, still prompts `[Y/n]`, and still runs on Enter;
  an `n` and an EOF at the prompt still log their own board-83 lines.
- **The apply side** (``ApplySideUnchangedTest``): `--no-interact`'s
  configured-decision line is byte-identical, and a piped apply
  without the mode still offers post_apply_pass's prompt and declines
  on EOF — post_apply_pass is not a pack-side hook.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it. The in-process cases load bin/bale
through the harness's _load_cli and write nothing outside their own
temporary directory.

Run:  python3 -m unittest tests.test_hook_non_tty -v
  or: python3 -m unittest discover -s tests -p 'test_hook_non_tty.py'
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from harness import (
    REPO_ROOT,
    _load_cli,
    run_bale,
    run_bale_pty,
)
from test_handoff_fixture import HandoffFixture
from test_hook_acceptance import _HookFixture
from test_open_verb import _OpenVerbBase

# The brief's fixed line, VERBATIM, and the prefixed form run_hook logs.
FIXED_LINE = ("declined (stdin is not a terminal; the prompt was not "
              "offered); not invoking.")
LOGGED_LINE = f"[bale] [hook post_pack] {FIXED_LINE}"

PROMPT = "run this hook?"
DEFAULT_LINE = "  default: "
EOF_PHRASE = "stdin closed or interrupted"
BANNER_LAST = "  Inspect the script before approving.\n"
MARK = "post-pack-ran.txt"
EOT = "\x04"


def hook_body() -> str:
    """A hook that leaves a marker under HOME, so "ran" and "declined"
    are told apart without parsing output."""
    return f"#!/bin/sh\necho ran > \"$HOME/{MARK}\"\n"


def write_global_post_pack(install: Path) -> Path:
    """A global-layer post_pack hook — <install>/user/bale.toml naming
    an executable under <install>/user/ (the brief's scratch shape)."""
    user = install / "user"
    (user / "scripts").mkdir(parents=True, exist_ok=True)
    script = user / "scripts" / "hook.sh"
    script.write_text(hook_body(), encoding="utf-8")
    script.chmod(0o755)
    (user / "bale.toml").write_text(
        '[hooks]\npost_pack = "scripts/hook.sh"\n', encoding="utf-8")
    return script


class _PipedAssertions:
    """The shared reading of one piped pack-side run's output."""

    def assert_declined_without_prompt(self, text: str, *,
                                       home: Path) -> None:
        self.assertIn("  hook:   post_pack (", text,
                      msg="the banner still prints")
        self.assertNotIn(PROMPT, text, msg="no prompt is offered")
        self.assertNotIn(DEFAULT_LINE, text,
                         msg="no default line: there is no prompt to "
                             "default")
        self.assertNotIn(EOF_PHRASE, text,
                         msg="nothing read stdin, so nothing hit EOF")
        self.assertEqual(text.count(LOGGED_LINE), 1, msg=text)
        # Adjacency: the banner's last line, then the fixed line —
        # nothing (no default line, no prompt) between them.
        self.assertIn(BANNER_LAST + LOGGED_LINE + "\n", text)
        self.assertNotIn("[hook post_pack] invoking", text)
        self.assertFalse((home / MARK).exists(), "the hook must not run")


# ---------------------------------------------------------------------------
# Constants and stdin_is_terminal, in process
# ---------------------------------------------------------------------------

class ConstantsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.cli = _load_cli()

    def test_fixed_line_is_verbatim(self) -> None:
        self.assertEqual(self.cli.HOOK_DECLINE_LINE_NOT_A_TERMINAL,
                         FIXED_LINE)

    def test_fixed_line_sits_on_one_physical_line_of_the_source(
            self) -> None:
        source = (REPO_ROOT / "bin" / "bale").read_text(encoding="utf-8")
        hits = [ln for ln in source.splitlines() if FIXED_LINE in ln]
        self.assertEqual(len(hits), 1,
                         msg="the fixed line appears once, unfolded")

    def test_board_83_lines_are_unchanged(self) -> None:
        cli = self.cli
        self.assertEqual(cli.HOOK_DECLINE_LINES, {
            cli.CONFIRM_BRANCH_STDIN_CLOSED:
                "declined (stdin closed or interrupted); not invoking.",
            cli.CONFIRM_BRANCH_EMPTY_AT_DECLINE_DEFAULT:
                "declined (empty answer at a decline default); not "
                "invoking.",
            cli.CONFIRM_BRANCH_ANSWERED:
                "declined (answered '{answer}'); not invoking.",
        })
        self.assertNotIn(FIXED_LINE, cli.HOOK_DECLINE_LINES.values())

    def test_pack_side_is_exactly_post_pack(self) -> None:
        import bale_config
        self.assertEqual(self.cli.PACK_SIDE_HOOKS, frozenset({"post_pack"}))
        self.assertTrue(self.cli.PACK_SIDE_HOOKS <= set(
            bale_config.HOOK_NAMES))
        self.assertNotIn("post_apply_pass", self.cli.PACK_SIDE_HOOKS)

    def test_stdin_is_terminal_shapes(self) -> None:
        cli = self.cli
        with mock.patch.object(sys, "stdin", None):
            self.assertFalse(cli.stdin_is_terminal())
        with mock.patch.object(sys, "stdin", io.StringIO("")):
            self.assertFalse(cli.stdin_is_terminal())
        closed = io.StringIO("")
        closed.close()  # isatty() raises ValueError on a closed stream
        with mock.patch.object(sys, "stdin", closed):
            self.assertFalse(cli.stdin_is_terminal())
        import pty
        master, slave = pty.openpty()
        try:
            with open(slave, "r", closefd=False) as tty_stream, \
                    mock.patch.object(sys, "stdin", tty_stream):
                self.assertTrue(cli.stdin_is_terminal())
        finally:
            os.close(slave)
            os.close(master)


# ---------------------------------------------------------------------------
# run_hook in process: input() is never reached off a terminal
# ---------------------------------------------------------------------------

class _FakeTerminal(io.StringIO):
    def isatty(self) -> bool:
        return True


class RunHookInProcessTest(unittest.TestCase):

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-nontty-")
        self.tmp = Path(self._tmpdir.name)
        self.cli = _load_cli()
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        # Outside both the install's user/ and the repo: the
        # `configured` layer, whose prompt defaults decline. Its bytes
        # carry the temp path, so no acceptance store can know them.
        self.script = self.tmp / "hook.sh"
        self.script.write_text(
            f"#!/bin/sh\n# {self.tmp}\ntouch \"{self.tmp}/ran\"\n",
            encoding="utf-8")
        self.script.chmod(self.script.stat().st_mode | stat.S_IXUSR)
        self.cfg = {"hooks": {"post_pack": str(self.script)}}

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def run_hook(self, stdin, input_fn) -> str:
        """run_hook with stdin, input() and the acceptance store
        stubbed: the store reads as "nothing accepted" and a write to it
        fails the test, so nothing outside the temp dir is touched (the
        real store sits under the install this module was loaded from)."""
        config = self.cli.bale_config

        def no_record(**_k):
            raise AssertionError("the acceptance store was written")
        out = io.StringIO()
        with mock.patch.object(sys, "stdin", stdin), \
                mock.patch("builtins.input", input_fn), \
                mock.patch.object(config, "hook_previously_accepted",
                                  return_value=False), \
                mock.patch.object(config, "record_hook_acceptance",
                                  no_record), \
                contextlib.redirect_stdout(out):
            self.cli.run_hook(self.repo, self.cfg, "post_pack", "sid-x",
                              tarball=self.tmp / "t.tar.gz")
        return out.getvalue()

    def test_non_terminal_never_calls_input(self) -> None:
        def no_input(*_a, **_k):
            raise AssertionError("input() was reached off a terminal")
        for stdin in (None, io.StringIO("y\n")):
            with self.subTest(stdin=type(stdin).__name__):
                text = self.run_hook(stdin, no_input)
                self.assertIn("  hook:   post_pack (configured)\n", text)
                self.assertIn(BANNER_LAST + LOGGED_LINE + "\n", text)
                self.assertNotIn(DEFAULT_LINE, text)
                self.assertFalse((self.tmp / "ran").exists())

    def test_terminal_still_prompts(self) -> None:
        asked: list[str] = []

        def answer_n(prompt: str = "") -> str:
            asked.append(prompt)
            return "n"
        text = self.run_hook(_FakeTerminal(""), answer_n)
        self.assertEqual(asked, ["  run this hook? [y/N] "])
        self.assertIn("  default: decline — configured-layer hook not yet "
                      "accepted at this install", text)
        self.assertIn("[bale] [hook post_pack] declined (answered 'n'); "
                      "not invoking.", text)
        self.assertNotIn(FIXED_LINE, text)
        self.assertFalse((self.tmp / "ran").exists())


# ---------------------------------------------------------------------------
# The session pack, piped
# ---------------------------------------------------------------------------

class SessionPackPipedTest(_PipedAssertions, _HookFixture):

    def pack(self, slug: str, *extra: str):
        return run_bale(self.install, [
            "pack", f"non-tty goal {slug}", "--slug", slug,
            "--include", "hello.txt", "--no-readme", *extra],
            cwd=self.repo, env=self.env)

    def test_global_hook_declines_without_prompt(self) -> None:
        write_global_post_pack(self.install)
        r = self.pack("ntglobal")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        self.assertIn("  hook:   post_pack (global)\n", r.stdout)
        self.assert_declined_without_prompt(r.stdout, home=self.home)
        self.assertFalse(self.store.exists(), "nothing is recorded")

    def test_project_hook_declines_and_records_nothing(self) -> None:
        script = self.repo / "scripts" / "pp.sh"
        script.parent.mkdir(exist_ok=True)
        script.write_text(hook_body(), encoding="utf-8")
        script.chmod(0o755)
        (self.repo / "bale.toml").write_text(
            '[sandbox]\nenabled = false\n'
            '[hooks]\npost_pack = "scripts/pp.sh"\n', encoding="utf-8")
        from harness import run_checked
        run_checked(["git", "add", "-A"], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "project post_pack"],
                    cwd=self.repo, env=self.genv)
        r = self.pack("ntproject")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        self.assertIn("  hook:   post_pack (project)\n", r.stdout)
        self.assert_declined_without_prompt(r.stdout, home=self.home)
        self.assertFalse(self.store.exists(), "nothing is recorded")

    def test_json_keeps_stdout_one_line_and_the_trail_on_stderr(
            self) -> None:
        write_global_post_pack(self.install)
        r = self.pack("ntjson", "--json")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        self.assertEqual(len(r.stdout.splitlines()), 1, msg=r.stdout)
        json.loads(r.stdout)
        self.assertNotIn("[hook ", r.stdout)
        self.assertNotIn(PROMPT, r.stdout)
        self.assert_declined_without_prompt(r.stderr, home=self.home)


# ---------------------------------------------------------------------------
# bale handoff, piped
# ---------------------------------------------------------------------------

class HandoffPipedTest(_PipedAssertions, HandoffFixture):

    def test_handoff_declines_without_prompt(self) -> None:
        _sid, tarball = self.packed_and_bailed(reading_plan_paths=None)
        # Configured only now, so the handoff is the one run that fires it.
        write_global_post_pack(self.install)
        r = self.handoff(tarball)
        self.assert_ok(r, "handoff")
        self.assertIn("  hook:   post_pack (global)\n", r.stdout)
        self.assert_declined_without_prompt(r.stdout, home=self.home)


# ---------------------------------------------------------------------------
# bale open <bundle> --json — the observed invocation
# ---------------------------------------------------------------------------

class OpenReplayJsonTest(_PipedAssertions, _OpenVerbBase):

    def test_open_json_replay_declines_and_stdout_is_one_line(self) -> None:
        write_global_post_pack(self.install)
        bundle = self.build_bundle("nt.bale-bundle",
                                   pack_argv=self.argv("ntopen"))
        r = self.open_bundle(bundle, "--json")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        lines = r.stdout.splitlines()
        self.assertEqual(len(lines), 1, msg=r.stdout)
        self.assertEqual(json.loads(lines[0])["outcome"], "opened")
        self.assertNotIn("[hook ", r.stdout)
        self.assertNotIn(PROMPT, r.stdout)
        self.assert_declined_without_prompt(r.stderr, home=self.home)

    def test_open_human_mode_replay_declines_too(self) -> None:
        write_global_post_pack(self.install)
        bundle = self.build_bundle("nth.bale-bundle",
                                   pack_argv=self.argv("ntopenh"))
        r = self.open_bundle(bundle)
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        self.assert_declined_without_prompt(r.stdout, home=self.home)


# ---------------------------------------------------------------------------
# A terminal stdin keeps the interactive contract
# ---------------------------------------------------------------------------

class TerminalStillPromptsTest(_HookFixture):

    def pty_pack(self, slug: str, answers: str):
        return run_bale_pty(self.install, [
            "pack", f"tty goal {slug}", "--slug", slug,
            "--include", "hello.txt", "--no-readme"],
            cwd=self.repo, env=self.env, answers=answers)

    def test_enter_accepts_a_global_hook(self) -> None:
        write_global_post_pack(self.install)
        code, out = self.pty_pack("ttyenter", "\n")
        self.assertEqual(code, 0, msg=out)
        self.assertIn("  default: accept — global-layer hook — your own "
                      "script", out)
        self.assertIn("  run this hook? [Y/n]", out)
        self.assertIn("[hook post_pack] invoking", out)
        self.assertNotIn(FIXED_LINE, out)
        self.assertTrue((self.home / MARK).exists(), "the hook ran")
        self.assertFalse(self.store.exists(),
                         "a global-layer default is never recorded")

    def assert_declined_at_the_prompt(self, slug: str, answers: str,
                                      phrase: str) -> None:
        write_global_post_pack(self.install)
        code, out = self.pty_pack(slug, answers)
        self.assertEqual(code, 0, msg=out)
        self.assertIn("  run this hook? [Y/n]", out)
        self.assertIn(f"[hook post_pack] {phrase}", out)
        self.assertNotIn(FIXED_LINE, out)
        self.assertFalse((self.home / MARK).exists())

    def test_n_keeps_its_board_83_line(self) -> None:
        self.assert_declined_at_the_prompt(
            "ttyn", "n\n", "declined (answered 'n'); not invoking.")

    def test_eof_on_a_terminal_keeps_its_board_83_line(self) -> None:
        self.assert_declined_at_the_prompt(
            "ttyeof", EOT,
            "declined (stdin closed or interrupted); not invoking.")


# ---------------------------------------------------------------------------
# The apply side is not the pack side
# ---------------------------------------------------------------------------

class ApplySideUnchangedTest(_HookFixture):

    def test_no_interact_line_is_byte_identical(self) -> None:
        self.write_project_hook()
        tarball = self.pack_and_response(1)
        r = run_bale(self.install, ["apply", str(tarball), "--no-interact"],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertIn(
            "[bale] [hook post_apply_pass] prompt skipped (no-interact via "
            "--no-interact flag): declined per built-in default "
            "(apply.hook_auto_accept unset); not invoking.\n", r.stdout)
        self.assertNotIn(FIXED_LINE, r.stdout + r.stderr)
        self.assertNotIn(PROMPT, r.stdout)

    def test_piped_apply_still_offers_post_apply_pass(self) -> None:
        self.write_project_hook()
        tarball = self.pack_and_response(1)
        r = run_bale(self.install, ["apply", str(tarball)],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertIn("run this hook? [y/N]", r.stdout)
        self.assertIn("[hook post_apply_pass] declined (stdin closed or "
                      "interrupted); not invoking.", r.stdout)
        self.assertNotIn(FIXED_LINE, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
