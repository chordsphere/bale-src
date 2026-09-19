#!/usr/bin/env python3
"""Every suite loads in the dotted run form from the repo root (board 113).

The suites import their shared helpers by bare name (``from harness
import ...``), which resolves only when ``tests/`` is on ``sys.path``.
Discovery (``-m unittest discover -s tests``) and direct execution
(``python3 tests/<suite>.py``) put it there themselves; the dotted form
(``python3 -m unittest tests.<suite>`` from the repo root) does not,
and before board 113 fifty-six of the sixty-eight suites errored on
their harness import in that form. ``tests/__init__.py`` now puts
``tests/`` on the path the way discovery does.

This suite pins that for the whole tree rather than for a list, so the
next new suite is covered the day it lands:

- **The sweep** globs ``tests/test_*.py`` — the discovery default
  pattern — and loads each as ``tests.<suite>`` the way ``python3 -m
  unittest tests.<suite>`` does, each in its own fresh interpreter
  whose cwd is the repo root and whose ``PYTHONPATH`` is cleared, so no
  suite can pass on a path entry the runner or an earlier suite left
  behind. A load error is the whole finding; nothing runs the suites'
  tests (discovery does that).
- **The pin bites**: a scratch tree with a bare-importing suite fails
  to load in the dotted form without the real ``tests/__init__.py`` and
  loads with it, through the same checker the sweep uses.

Stdlib only; it imports nothing from tests/harness.py, so it runs in
every form whatever state the harness is in.

Run:  python3 -m unittest tests.test_dotted_run_form -v
  or: python3 -m unittest discover -s tests -p 'test_dotted_run_form.py'
  or: python3 tests/test_dotted_run_form.py
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = REPO_ROOT / "tests"
PACKAGE_INIT = TESTS_DIR / "__init__.py"

SUBPROCESS_TIMEOUT = 120  # seconds; a load is well under one.

# Run in the child: load one dotted name the way `python3 -m unittest
# <name>` does and report every loader error. loadTestsFromName never
# raises on a failed import — it records the traceback in
# loader.errors and returns a stand-in failing test — so the errors
# list, not an exception, is the verdict.
_LOAD_PROBE = (
    "import sys, unittest\n"
    "loader = unittest.TestLoader()\n"
    "loader.loadTestsFromName(sys.argv[1])\n"
    "for err in loader.errors:\n"
    "    sys.stderr.write(err)\n"
    "sys.exit(1 if loader.errors else 0)\n"
)


def suite_names(tests_dir: Path) -> list[str]:
    """The discovery-default suites (``test_*.py``) in ``tests_dir``,
    as bare module names, sorted."""
    return sorted(p.stem for p in tests_dir.glob("test_*.py"))


def dotted_load_error(root: Path, suite: str) -> str | None:
    """Load ``tests.<suite>`` in a fresh interpreter from ``root`` as the
    dotted run form does. Returns None on a clean load, else the
    child's exit code and stderr (the loader's traceback)."""
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)  # only the cwd may put anything on the path
    proc = subprocess.run(
        [sys.executable, "-c", _LOAD_PROBE, f"tests.{suite}"],
        cwd=str(root), env=env, capture_output=True, text=True,
        timeout=SUBPROCESS_TIMEOUT,
    )
    if proc.returncode == 0:
        return None
    return f"exit {proc.returncode}\n{proc.stderr.strip()}"


class DottedRunFormTest(unittest.TestCase):
    """The sweep over the real tree."""

    def test_every_suite_loads_in_the_dotted_form(self) -> None:
        suites = suite_names(TESTS_DIR)
        # The glob must see the tree, this file included — an empty or
        # self-less sweep would pass while checking nothing.
        self.assertIn(Path(__file__).stem, suites)
        self.assertGreater(len(suites), 1)
        workers = min(8, os.cpu_count() or 1)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = dict(zip(
                suites,
                pool.map(lambda s: dotted_load_error(REPO_ROOT, s), suites)))
        failures = {s: err for s, err in results.items() if err is not None}
        if failures:
            # One line per suite (the traceback's last line names the
            # missing import), then the first failure in full.
            first = min(failures)
            self.fail(
                f"{len(failures)} of {len(suites)} suites fail to load as "
                f"`python3 -m unittest tests.<suite>` from {REPO_ROOT}:\n"
                + "\n".join(f"  tests.{s}: {e.splitlines()[-1]}"
                            for s, e in sorted(failures.items()))
                + f"\n\nFirst in full, tests.{first}:\n{failures[first]}")


class PinBitesTest(unittest.TestCase):
    """The checker above fails exactly when the package init is missing,
    so the sweep's green is evidence rather than a checker that always
    says yes."""

    SUITE = "test_bare_import"

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        scratch_tests = self.root / "tests"
        scratch_tests.mkdir()
        # A bare-name sibling helper and a suite importing it at module
        # scope: the shape of every harness-importing suite.
        (scratch_tests / "scratch_helper.py").write_text(
            "VALUE = 113\n", encoding="utf-8")
        (scratch_tests / f"{self.SUITE}.py").write_text(
            "import unittest\n"
            "from scratch_helper import VALUE\n"
            "class T(unittest.TestCase):\n"
            "    def test_value(self):\n"
            "        self.assertEqual(VALUE, 113)\n",
            encoding="utf-8")
        self.scratch_tests = scratch_tests

    def test_without_the_package_init_the_dotted_load_fails(self) -> None:
        err = dotted_load_error(self.root, self.SUITE)
        self.assertIsNotNone(err)
        self.assertIn("scratch_helper", err)

    def test_with_the_real_package_init_the_dotted_load_succeeds(self) -> None:
        self.assertTrue(PACKAGE_INIT.is_file(),
                        msg=f"{PACKAGE_INIT} is missing")
        shutil.copyfile(PACKAGE_INIT, self.scratch_tests / "__init__.py")
        self.assertIsNone(dotted_load_error(self.root, self.SUITE))


if __name__ == "__main__":
    unittest.main()
