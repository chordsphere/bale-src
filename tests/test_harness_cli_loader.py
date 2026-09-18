#!/usr/bin/env python3
"""The harness's in-process bin/bale loader and shared normalizer
(session 2026-09-18-board-109-harness-micro-002).

``harness._load_cli()`` loads bin/bale — the script, not a sibling — as
an ordinary module, so functions that live only there can be unit
tested without running the CLI. This suite is the loader's own test,
and the first consumer: it drives two real bin/bale-only functions
in-process (``fail_not_found`` and ``SubcommandHelpFormatter._fill_text``,
both named in board 106's proposal), then pins what "does not disturb a
suite that also uses ``_load_module``" means in practice:

- main() does not run, and ``sys.modules["__main__"]`` is untouched;
- bin/ is on sys.path after a load, and no number of loads grows
  sys.path (bin/bale's own unconditional insert is undone);
- a sibling already loaded with ``_load_module`` is the instance
  bin/bale binds, and stays registered — no second copy;
- each call returns a fresh module, so module state cannot leak;
- a failed load leaves no half-built ``bale_cli`` registered.

It also pins the documented limit (the siblings' lazy ``from __main__
import`` never reaches the loaded CLI), so a change that lifts or moves
that limit has to update the docstring that states it.

``harness.normalize`` gets its unit test here too: the two doc-pin
suites (test_doc_crossrefs, test_sanctioned_pairs) consume it, and
neither pins the helper's own behavior.

Hermetic: nothing runs as a subprocess; bin/bale is loaded from this
repo and every filesystem touch is under a temp dir.

Run:  python3 tests/test_harness_cli_loader.py -v
  or: python3 -m unittest discover -s tests -p 'test_harness_cli_loader.py'
"""

from __future__ import annotations

import argparse
import contextlib
import io
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

import harness
from harness import BIN_DIR, CLI_MODULE_NAME, _load_cli, _load_module, normalize


def _bin_entries() -> int:
    """How many sys.path entries name the repo's bin/."""
    return sum(1 for entry in sys.path if entry == str(BIN_DIR))


class LoadCliBasics(unittest.TestCase):
    """The loader returns bin/bale as a module without running it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cli = _load_cli()

    def test_module_identity(self):
        self.assertEqual(self.cli.__name__, CLI_MODULE_NAME)
        self.assertNotEqual(self.cli.__name__, "__main__")
        self.assertEqual(Path(self.cli.__file__), BIN_DIR / "bale")

    def test_bin_bale_only_functions_are_reachable(self):
        """The three functions board 106's proposal named all resolve
        on the loaded module — the point of the loader."""
        for name in ("fail_not_found", "SubcommandHelpFormatter",
                     "compose_retry_successor", "main", "build_parser"):
            with self.subTest(name=name):
                self.assertTrue(callable(getattr(self.cli, name, None)),
                                f"bin/bale's {name} is not reachable")

    def test_main_module_untouched(self):
        """Loading does not replace the process's __main__ (the guard
        that keeps main() from running is exactly this)."""
        main_before = sys.modules["__main__"]
        cli = _load_cli()
        self.assertIs(sys.modules["__main__"], main_before)
        self.assertIsNot(sys.modules["__main__"], cli)

    def test_version_constant_matches_file(self):
        """Module scope ran to completion: the VERSION guard read the
        real file."""
        self.assertEqual(
            self.cli.VERSION,
            (BIN_DIR / "VERSION").read_text(encoding="utf-8").strip())


class LoadCliFailNotFound(unittest.TestCase):
    """bin/bale's fail_not_found, unit tested in-process (board 106
    pinned it end to end only)."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cli = _load_cli()

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name).resolve()
        self.addCleanup(self._tmp.cleanup)

    def _refusal(self, *args, **kwargs) -> tuple[int, str]:
        """Call fail_not_found; return (exit code, stderr text)."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err), \
                self.assertRaises(SystemExit) as ctx:
            self.cli.fail_not_found(*args, **kwargs)
        return ctx.exception.code, err.getvalue()

    def test_bare_refusal(self):
        code, err = self._refusal("readme file", "notes/README.md")
        self.assertEqual(code, 1)
        self.assertEqual(err, "[bale] error: readme file not found: "
                              "notes/README.md\n")

    def test_search_miss_lists_cwd_first(self):
        sp = self.tmp / "downloads"
        code, err = self._refusal("response tarball", "response-x.tar.gz",
                                  cwd=self.tmp, search_paths=[str(sp)])
        self.assertEqual(code, 1)
        self.assertEqual(
            err,
            "[bale] error: response tarball not found: response-x.tar.gz\n"
            "  searched:\n"
            f"    {self.tmp}  (cwd)\n"
            f"    {sp}\n")

    def test_verb_with_no_candidates_is_byte_identical(self):
        """The docstring's promise: zero near-name candidates adds
        nothing, so the refusal equals the no-verb form."""
        _, without = self._refusal("response tarball", "response-x.tar.gz",
                                   cwd=self.tmp, search_paths=[])
        _, with_verb = self._refusal("response tarball", "response-x.tar.gz",
                                     "apply", cwd=self.tmp, search_paths=[])
        self.assertEqual(with_verb, without)

    def test_verb_lists_near_name_candidates_newest_first(self):
        older = self.tmp / "response-x (1).tar.gz"
        newer = self.tmp / "response-x-retry.tar.gz"
        unrelated = self.tmp / "request-x.tar.gz"
        for f in (older, newer, unrelated):
            f.write_bytes(b"")
        now = time.time()
        os.utime(older, (now - 100, now - 100))
        os.utime(newer, (now, now))
        # search_paths=None: the no-search-path branch, so no
        # `searched:` block precedes the listing; cwd is still scanned.
        _, err = self._refusal("response tarball", "response-x.tar.gz",
                               "apply", cwd=self.tmp, search_paths=None)
        lines = err.splitlines()
        self.assertEqual(lines[1], "  near-name candidates (newest first):")
        self.assertEqual(lines[2:], [
            f"    bale apply {newer}",
            f"    bale apply '{older}'",  # shlex-quoted: space and parens
        ])


class LoadCliHelpFormatter(unittest.TestCase):
    """bin/bale's SubcommandHelpFormatter._fill_text, in-process."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.cli = _load_cli()

    def _fill(self, text: str, width: int = 40, indent: str = "") -> str:
        fmt = self.cli.SubcommandHelpFormatter(prog="bale")
        return fmt._fill_text(text, width, indent)

    def test_paragraphs_kept_and_literal_block_verbatim(self):
        text = ("alpha beta\ngamma\n\n"
                "  bale apply response.tar.gz\n"
                "  bale retry  \"a b\"\n\n"
                "delta")
        self.assertEqual(
            self._fill(text, indent="  "),
            "  alpha beta gamma\n\n"
            "    bale apply response.tar.gz\n"
            "    bale retry  \"a b\"\n\n"
            "  delta")

    def test_prose_block_wraps_to_width(self):
        out = self._fill("word " * 30, width=30)
        self.assertGreater(len(out.splitlines()), 1)
        self.assertTrue(all(len(line) <= 30 for line in out.splitlines()))

    def test_unstructured_description_matches_default_formatter(self):
        """No blank lines means byte-for-byte the default formatter's
        fill, at any width — the class docstring's compatibility
        claim."""
        text = "one long description " * 12
        default = argparse.HelpFormatter(prog="bale")
        for width in (20, 57, 200):
            with self.subTest(width=width):
                self.assertEqual(
                    self._fill(text, width=width, indent=" "),
                    default._fill_text(text, width, " "))


class LoadCliDoesNotDisturb(unittest.TestCase):
    """What a _load_module suite can rely on after _load_cli runs."""

    def test_repeated_loads_never_grow_sys_path(self):
        """Relative, not absolute: in a full discover run other suites
        insert bin/ themselves, so the count before is whatever they
        left; the loader's promise is only that it adds nothing past
        ensuring bin/ is present."""
        _load_cli()  # first load may add bin/ if absent — allowed
        path_before = list(sys.path)
        for _ in range(3):
            _load_cli()
        self.assertEqual(sys.path, path_before,
                         "bin/bale's own sys.path.insert leaked a "
                         "duplicate bin/ entry")
        self.assertGreaterEqual(_bin_entries(), 1)

    def test_existing_sibling_instance_is_reused(self):
        """A sibling the suite loaded first stays the registered
        instance, and it is the one bin/bale bound — no second copy."""
        validate = _load_module("bale_validate")
        cli = _load_cli()
        self.assertIs(sys.modules["bale_validate"], validate)
        self.assertIs(cli.validate_request_manifest,
                      validate.validate_request_manifest)

    def test_each_call_is_a_fresh_module(self):
        first = _load_cli()
        first.VERSION = "mutated-by-test"
        second = _load_cli()
        self.assertIsNot(first, second)
        self.assertNotEqual(second.VERSION, "mutated-by-test")
        self.assertIs(sys.modules[CLI_MODULE_NAME], second)

    def test_failed_load_leaves_registry_as_it_was(self):
        """An import-time sys.exit (the VERSION guard) surfaces as a
        named RuntimeError, and the prior bale_cli stays registered.
        Driven against a scratch copy of bin/ with an empty VERSION, by
        pointing the loader's path constant at it for this test only."""
        good = _load_cli()
        path_before = list(sys.path)
        with tempfile.TemporaryDirectory() as tmp:
            scratch_bin = Path(tmp) / "bin"
            scratch_bin.mkdir()
            (scratch_bin / "bale").write_bytes(
                (BIN_DIR / "bale").read_bytes())
            (scratch_bin / "VERSION").write_text("\n", encoding="utf-8")
            original = harness.CLI_PATH
            harness.CLI_PATH = scratch_bin / "bale"
            try:
                with contextlib.redirect_stderr(io.StringIO()), \
                        self.assertRaises(RuntimeError) as ctx:
                    _load_cli()
            finally:
                harness.CLI_PATH = original
        self.assertIsInstance(ctx.exception.__cause__, SystemExit)
        self.assertIn("exited while loading", str(ctx.exception))
        self.assertIs(sys.modules[CLI_MODULE_NAME], good)
        self.assertEqual(sys.path, path_before,
                         "a failed load left its sys.path insert behind")


class LoadCliDocumentedLimit(unittest.TestCase):
    """The limit _load_cli's docstring states: the siblings' lazy
    ``from __main__ import`` resolves against the process's real
    __main__, never the loaded CLI."""

    def test_lazy_main_reach_back_does_not_find_the_cli(self):
        _load_cli()
        with self.assertRaises(ImportError):
            exec("from __main__ import fail_not_found", {})


class NormalizeTest(unittest.TestCase):
    """harness.normalize, the doc-pin suites' shared rewrap tolerance."""

    def test_collapses_every_whitespace_run(self):
        self.assertEqual(normalize("a  b\n\tc\r\n d"), "a b c d")

    def test_strips_the_ends(self):
        self.assertEqual(normalize("\n  lead and trail \n"),
                         "lead and trail")

    def test_empty_and_blank(self):
        self.assertEqual(normalize(""), "")
        self.assertEqual(normalize(" \n\t "), "")

    def test_rewrapped_prose_matches(self):
        """The use the suites make of it: a 70-column rewrap of a pinned
        sentence still contains it."""
        pinned = "the rule is that a turn that asks ends in a block"
        wrapped = "the rule is that a turn\nthat asks ends in a\n  block"
        self.assertIn(normalize(pinned), normalize(wrapped))


if __name__ == "__main__":
    unittest.main()
