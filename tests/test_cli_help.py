#!/usr/bin/env python3
"""The subcommand help layout suite (board 106 / 99a; moved here whole
from tests/test_apply_preflight.py at board 110, v0.4.37 — row 109's
deferred third).

``SubcommandHelpLayoutTest`` pins that every subparser renders its
description through bin/bale's SubcommandHelpFormatter: authored
paragraph breaks and indented literal blocks survive (the `bale
completion` install examples among them), and prose still wraps at a
pinned 80-column width. A pure move: the same tests with the same
names; only the module changed. It lived in the apply pre-flight suite
by accident of which file the 106 session held, and has nothing to do
with the apply reject surface.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_cli_help.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from harness import (
    bale_env,
    make_install,
    make_sandbox_home,
    run_bale,
)


class SubcommandHelpLayoutTest(unittest.TestCase):
    """Board 106 (99a): every subparser renders its description with
    bin/bale's SubcommandHelpFormatter, a RawDescriptionHelpFormatter
    that keeps blank-line paragraph breaks and indented literal blocks
    and still wraps prose. Rendered through the real CLI at a pinned
    80-column width (argparse wraps to COLUMNS - 2)."""

    COLUMNS = 80
    COMMANDS = (
        ("pack",), ("apply",), ("retry",), ("amend-checkpoint",),
        ("relay",), ("revert",), ("rollback",), ("unlock",), ("open",),
        ("handoff",), ("config",), ("config", "init"), ("config", "hooks"),
        ("help",), ("completion",), ("status",), ("stats",),
    )

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-help-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.env = dict(bale_env(self.home, self.tmp),
                        COLUMNS=str(self.COLUMNS))

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def help_text(self, *command: str) -> str:
        result = run_bale(self.install, [*command, "--help"],
                          cwd=self.tmp, env=self.env)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return result.stdout

    @staticmethod
    def description_lines(text: str) -> list:
        """The lines between the usage block and the first argument
        section heading."""
        lines = text.splitlines()
        start = next(i for i, ln in enumerate(lines) if ln == "") + 1
        end = next((i for i, ln in enumerate(lines)
                    if i >= start and ln.endswith(":")
                    and not ln.startswith(" ")
                    and ln in ("positional arguments:", "options:",
                               "optional arguments:")), len(lines))
        return lines[start:end]

    def test_completion_examples_render_on_their_own_lines(self) -> None:
        lines = self.help_text("completion").splitlines()
        for example in (
                "    source <(bale completion bash)",
                "    bale completion bash > "
                "~/.local/share/bash-completion/completions/bale"):
            with self.subTest(example=example.strip()):
                self.assertIn(example, lines)
                at = lines.index(example)
                self.assertEqual(lines[at - 1], "",
                                 msg="blank line before the example")
                self.assertEqual(lines[at + 1], "",
                                 msg="blank line after the example")
        self.assertIn("Or install persistently:", lines)

    def test_authored_paragraph_breaks_survive(self) -> None:
        for command, opening in (
                ("apply", "The tarball argument is resolved against"),
                ("apply", "Inspection flags (--show-validator,"),
                ("retry", "A HOLD is retried on one of two rulings."),
                ("retry", "The per-attempt flags mirror")):
            with self.subTest(command=command, paragraph=opening):
                lines = self.help_text(command).splitlines()
                starts = [i for i, ln in enumerate(lines)
                          if ln.startswith(opening)]
                self.assertEqual(len(starts), 1, msg="\n".join(lines))
                self.assertEqual(lines[starts[0] - 1], "")

    def test_every_description_still_wraps(self) -> None:
        """No subparser's prose relies on a formatter that stopped
        wrapping: every non-literal description line fits the width."""
        for command in self.COMMANDS:
            with self.subTest(command=" ".join(command)):
                description = self.description_lines(
                    self.help_text(*command))
                self.assertTrue(any(ln.strip() for ln in description),
                                msg="expected a rendered description")
                for line in description:
                    if line.startswith("    "):
                        continue  # a literal block, verbatim by design
                    self.assertLessEqual(len(line), self.COLUMNS - 2,
                                         msg=line)

    def test_single_paragraph_description_renders_as_one_block(
            self) -> None:
        """A description written as one string keeps argparse's filled
        layout: one contiguous block, no blank line inside it."""
        description = self.description_lines(self.help_text("status"))
        body = [ln for ln in description if ln.strip()]
        self.assertGreater(len(body), 1)
        first = description.index(body[0])
        self.assertEqual(description[first:first + len(body)], body)


if __name__ == "__main__":
    unittest.main(verbosity=2)
