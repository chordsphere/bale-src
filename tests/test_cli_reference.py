#!/usr/bin/env python3
"""The request-carried CLI reference (session
2026-10-03-bale-cli-reference-003).

Every request bale builds carries ``BALE_HELP.md`` (bin/bale's
CLI_REFERENCE_NAME) at its top level: the installed bale's top-level
``bale help`` and every verb's ``bale help <verb>``, nested verbs
included, generated from ``build_parser()`` at request-build time by
``render_cli_reference()``. The carried docs route a worker in any
project to it (docs/AGENT.md's INDEX row and META reachability
paragraph, docs/TARBALL.md's INDEX row and §3.1), so a verb's syntax
is a read, never a probe for ``bale --help``. What this suite pins:

- **Verbatim** (``VerbatimTest``): every fenced section equals the
  real CLI's ``bale help <path>`` stdout at COLUMNS=80, byte for byte,
  and the contents list names exactly the sections that follow.
- **Coverage** (``CoverageTest``): one section per help page — the top
  level plus every command path a structural walk of the parser
  finds, nested ``config init`` / ``config hooks`` among them — in
  ``bale help``'s listing order.
- **Deterministic** (``DeterminismTest``): the rendered bytes do not
  move with COLUMNS (narrow, wide, unset) or FORCE_COLOR, and carry no
  escape sequence; the code fence outgrows any backtick run in a body.
- **Carried** (``CarriageTest``, end to end): a piped ``bale pack`` run
  at a narrow terminal ships the reference at ``request-NNN/``'s top
  level, outside ``context/``, equal to the CLI's own help in the same
  repo; ``bale handoff`` (the other build_request_tarball caller)
  ships it too; ``bale pack --context`` ships none.
- **Handoff filter** (``ReadingPlanFilterTest``): a reading plan citing
  the reference does not pull it into ``context/``.

The reference's framing prose is held to the global-doc
self-containment deny table by tests/test_global_doc_selfcontainment.py
(its rendered scan group), not here: one home per rule.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_cli_reference.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import os
import re
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:  # the dotted run form needs it
    sys.path.insert(0, _TESTS_DIR)

from harness import (  # noqa: E402 — path guard above
    _load_cli,
    bale_env,
    make_install,
    make_repo,
    make_sandbox_home,
    normalize,
    run_bale,
)
import test_handoff_happy  # noqa: E402 — reused fixture, see HandoffCarriageTest

REFERENCE_NAME = "BALE_HELP.md"
COLUMNS = 80

# A section: its heading, then a fence carrying an info string, the
# verbatim body, and a closing fence of the same backtick run.
SECTION_RE = re.compile(
    r"^## `(?P<heading>bale help[^`]*)`\n\n"
    r"(?P<fence>`{3,})text\n(?P<body>.*?)(?P=fence)$",
    re.MULTILINE | re.DOTALL)
CONTENTS_ENTRY_RE = re.compile(r"^- `(bale help[^`]*)`$", re.MULTILINE)


def sections(reference: str) -> list:
    """[(heading, body)] for every fenced help section, in order."""
    return [(m.group("heading"), m.group("body"))
            for m in SECTION_RE.finditer(reference)]


def help_args(heading: str) -> list:
    """`bale help config init` -> ["help", "config", "init"]."""
    return heading.split()[1:]


class _CliTestCase(unittest.TestCase):
    """bin/bale loaded in-process (harness._load_cli), plus a hermetic
    scratch install and HOME for the CLI comparisons."""

    def setUp(self) -> None:
        self.cli = _load_cli()
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-cliref-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def cli_help(self, heading: str, *, cwd: Path) -> str:
        """The real CLI's stdout for `heading` at COLUMNS=80."""
        result = run_bale(self.install, help_args(heading), cwd=cwd,
                          env=dict(self.env, COLUMNS=str(COLUMNS)))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return result.stdout

    def assert_matches_cli(self, reference: str, *, cwd: Path) -> None:
        found = sections(reference)
        self.assertTrue(found, "the reference has no fenced help sections")
        for heading, body in found:
            with self.subTest(page=heading):
                self.assertEqual(body, self.cli_help(heading, cwd=cwd))


class VerbatimTest(_CliTestCase):

    def test_every_section_is_the_clis_own_help(self) -> None:
        """Rendered outside any git repo (the stats section's telemetry
        home then renders the default, as the CLI does there)."""
        with mock.patch.dict(os.environ, {"COLUMNS": "200"}):
            cwd = Path.cwd()
            try:
                os.chdir(self.tmp)
                reference = self.cli.render_cli_reference()
            finally:
                os.chdir(cwd)
        self.assert_matches_cli(reference, cwd=self.tmp)

    def test_contents_lists_the_sections_in_order(self) -> None:
        reference = self.cli.render_cli_reference()
        self.assertEqual(CONTENTS_ENTRY_RE.findall(reference),
                         [h for h, _ in sections(reference)])

    def test_header_names_the_file_and_version(self) -> None:
        reference = self.cli.render_cli_reference()
        self.assertTrue(reference.startswith(f"# {REFERENCE_NAME}\n"))
        # The header (everything before the contents list), with its
        # blockquote markers dropped and its 70-column wrap collapsed.
        header = reference.split("\n## Contents\n", 1)[0]
        header = normalize(header.replace("\n> ", "\n"))
        self.assertIn(f"generated by bale v{self.cli.VERSION} when it "
                      f"built this request", header)
        self.assertEqual(self.cli.CLI_REFERENCE_NAME, REFERENCE_NAME)


class CoverageTest(unittest.TestCase):

    @staticmethod
    def structural_walk(parser, prefix=()) -> list:
        """Every command path, found through argparse's own structures
        rather than bin/bale's iter_command_paths — an independent
        oracle for the walk the renderer uses."""
        import argparse
        out = []
        for action in parser._actions:
            if isinstance(action, argparse._SubParsersAction):
                seen = set()
                for name, child in action.choices.items():
                    if id(child) in seen:
                        continue
                    seen.add(id(child))
                    out.append(prefix + (name,))
                    out += CoverageTest.structural_walk(child,
                                                        prefix + (name,))
        return out

    def test_one_section_per_help_page(self) -> None:
        cli = _load_cli()
        expected = ["bale help"] + [
            "bale help " + " ".join(path)
            for path in self.structural_walk(cli.build_parser())]
        got = [h for h, _ in sections(cli.render_cli_reference())]
        self.assertEqual(got, expected)

    def test_nested_and_documented_verbs_present(self) -> None:
        """The verbs the carried docs name without spelling out, and the
        nested config verbs the brief names, each have a section."""
        got = {h for h, _ in sections(_load_cli().render_cli_reference())}
        for verb in ("open", "relay", "retry", "handoff", "unlock",
                     "amend-checkpoint", "pack", "apply", "config init",
                     "config hooks"):
            with self.subTest(verb=verb):
                self.assertIn(f"bale help {verb}", got)


class DeterminismTest(unittest.TestCase):

    def render_with(self, env: dict) -> str:
        with mock.patch.dict(os.environ, env):
            return _load_cli().render_cli_reference()

    def test_bytes_do_not_move_with_the_terminal(self) -> None:
        with mock.patch.dict(os.environ):
            os.environ.pop("COLUMNS", None)
            os.environ.pop("FORCE_COLOR", None)
            baseline = _load_cli().render_cli_reference()
        for env in ({"COLUMNS": "30"}, {"COLUMNS": "80"},
                    {"COLUMNS": "250"},
                    {"COLUMNS": "120", "FORCE_COLOR": "1"}):
            with self.subTest(env=env):
                self.assertEqual(self.render_with(env), baseline)

    def test_no_escape_sequences(self) -> None:
        reference = self.render_with({"FORCE_COLOR": "1"})
        self.assertNotIn("\x1b", reference)

    def test_fixed_width_render_matches_argparse_at_that_width(self) -> None:
        """The pin on the mechanism: rendering at N columns is what
        argparse itself prints with COLUMNS=N."""
        cli = _load_cli()
        for columns in (60, 80, 100):
            with self.subTest(columns=columns):
                fixed = cli.render_fixed_width_help(
                    cli.build_parser(), columns)
                with mock.patch.dict(os.environ, {"COLUMNS": str(columns)}):
                    live = cli.build_parser().format_help()
                self.assertEqual(fixed, live)

    def test_fence_outgrows_any_backtick_run(self) -> None:
        cli = _load_cli()
        self.assertEqual(cli._code_fence("no ticks"), "```")
        self.assertEqual(cli._code_fence("`one` here"), "```")
        self.assertEqual(cli._code_fence("a ``` b"), "````")
        self.assertEqual(cli._code_fence("x ````` y"), "``````")


class CarriageTest(_CliTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.repo = make_repo(self.tmp, self.home)

    def test_pack_ships_the_reference_at_top_level(self) -> None:
        """Packed at a 37-column terminal; compared to the CLI at 80 in
        the same repo — so this one case pins carriage, placement, and
        width independence end to end."""
        packed = run_bale(
            self.install,
            ["pack", "carry the cli reference", "--slug", "cliref",
             "--include", "hello.txt", "--no-readme"],
            cwd=self.repo, env=dict(self.env, COLUMNS="37"))
        self.assertEqual(packed.returncode, 0,
                         msg=f"stdout:\n{packed.stdout}\n"
                             f"stderr:\n{packed.stderr}")
        tarballs = sorted((self.repo / ".bale" / "outbox").glob(
            "request-*-cliref-*.tar.gz"))
        self.assertEqual(len(tarballs), 1)
        with tarfile.open(tarballs[0]) as tf:
            names = tf.getnames()
            tops = [n for n in names
                    if Path(n).name == REFERENCE_NAME]
            self.assertEqual(len(tops), 1, msg=str(names))
            self.assertEqual(len(Path(tops[0]).parts), 2,
                             msg=f"{tops[0]} is not at request-NNN/'s "
                                 f"top level")
            raw = tf.extractfile(tops[0]).read()
        self.assertNotIn(b"\r\n", raw)
        self.assert_matches_cli(raw.decode("utf-8"), cwd=self.repo)

    def test_context_tarball_carries_no_reference(self) -> None:
        tree = self.tmp / "notes"
        tree.mkdir()
        (tree / "a.txt").write_text("a\n", encoding="utf-8")
        result = run_bale(self.install, ["pack", "--context"], cwd=tree,
                          env=self.env)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        tarballs = list(tree.glob("context-*.tar.gz")) or list(
            Path(self.tmp).rglob("context-*.tar.gz"))
        self.assertEqual(len(tarballs), 1, msg=result.stdout)
        with tarfile.open(tarballs[0]) as tf:
            names = tf.getnames()
        self.assertFalse(
            [n for n in names if Path(n).name == REFERENCE_NAME],
            msg=f"a context tarball carries no reference: {names}")


class HandoffCarriageTest(unittest.TestCase):
    """`bale handoff` builds through the same build_request_tarball, and
    its tarball carries the reference. The pack-then-bail fixture is
    tests/test_handoff_happy.py's, borrowed method by method rather than
    inherited — inheriting would re-run that suite's own tests here."""

    setUp = test_handoff_happy.HandoffHappyPathTest.setUp
    tearDown = test_handoff_happy.HandoffHappyPathTest.tearDown
    packed_and_bailed = \
        test_handoff_happy.HandoffHappyPathTest.packed_and_bailed
    handoff = test_handoff_happy.HandoffHappyPathTest.handoff
    open_sids = test_handoff_happy.HandoffHappyPathTest.open_sids
    sole_new_open_sid = \
        test_handoff_happy.HandoffHappyPathTest.sole_new_open_sid
    outbox_tarball = test_handoff_happy.HandoffHappyPathTest.outbox_tarball

    def test_handoff_request_carries_the_reference(self) -> None:
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt", REFERENCE_NAME])
        result = self.handoff(tarball)
        self.assertEqual(result.returncode, 0,
                         msg=f"stdout:\n{result.stdout}\n"
                             f"stderr:\n{result.stderr}")
        new_sid = self.sole_new_open_sid(bailed_sid)
        prefix = f"request-{new_sid[-3:]}"
        with tarfile.open(self.outbox_tarball(new_sid)) as tf:
            names = tf.getnames()
            raw = tf.extractfile(f"{prefix}/{REFERENCE_NAME}").read()
        # The plan cited the reference; the filter kept it out of
        # context/, so it ships once, at the top level.
        self.assertNotIn(f"{prefix}/context/{REFERENCE_NAME}", names)
        self.assertEqual(raw.decode("utf-8"),
                         _render_in(self.repo))


def _render_in(cwd: Path) -> str:
    """render_cli_reference() as it renders with `cwd` as the working
    directory (the stats section reads that repo's [layout])."""
    previous = Path.cwd()
    try:
        os.chdir(cwd)
        return _load_cli().render_cli_reference()
    finally:
        os.chdir(previous)


class ReadingPlanFilterTest(unittest.TestCase):

    def test_reference_is_filtered_like_the_global_docs(self) -> None:
        cli = _load_cli()
        plan = (f"- read `{REFERENCE_NAME}` for `bale relay`\n"
                "- read `AGENT.md` again\n"
                "- read `src/app.py` before building\n")
        self.assertEqual(cli.extract_paths_from_reading_plan(plan),
                         ["src/app.py"])


if __name__ == "__main__":
    unittest.main()
