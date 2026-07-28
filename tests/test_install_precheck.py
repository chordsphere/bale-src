#!/usr/bin/env python3
"""Hermetic E2E for the request-command install sanity check.

Covers the ``main()`` pre-flight in ``bin/bale`` that verifies the
installation ships its injected files (GLOBAL_DOCS under ``docs/``,
INJECTED_TOOLS under ``tools/``) before either request-building
command — ``bale pack`` or ``bale handoff`` — does any work. On a
broken install both commands must refuse up front with the identical
"Reinstall bale." message: before any prompt, before any tarball
resolution, before any session state exists. The handoff side is the
gap this test pins closed — previously a broken install died mid-build
as a copy failure after sid allocation.

Sandbox doctrine per ADR-0005 (fully hermetic) — the harness lives
in ``tests/harness.py`` since the second suite landed (the board-11
extraction trigger) and this file consumes it; see the harness module
docstring for the doctrine in full. One point specific to this suite:
every invocation here is piped (stdin is not a TTY), so no editor or
prompt path should engage — the harness's ``/bin/true`` editor stub
turns a regression there into a fast clean exit instead of a hang.

Run directly::

    python3 tests/test_install_precheck.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

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

# Sentinels for the refusal this file exists to pin. Kept in one place
# so a message rewording breaks one line, not six assertions.
MISSING_MARKER = "missing injected files"
REINSTALL_MARKER = "Reinstall bale."


def error_line(stderr: str) -> str:
    """Extract the single '[bale] error:' line for message-parity checks."""
    lines = [ln for ln in stderr.splitlines() if ln.startswith("[bale] error:")]
    if len(lines) != 1:
        raise AssertionError(
            f"expected exactly one '[bale] error:' line, got "
            f"{len(lines)}:\n{stderr}"
        )
    return lines[0]


class InstallPrecheckTest(unittest.TestCase):
    """Both request-building commands refuse a broken install up front."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-precheck-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def assert_refused_up_front(self, result, missing_name: str) -> None:
        """The refusal fired, named the missing file, and left no state."""
        self.assertEqual(result.returncode, 1, msg=result.stderr)
        self.assertIn(MISSING_MARKER, result.stderr)
        self.assertIn(missing_name, result.stderr)
        self.assertIn(REINSTALL_MARKER, result.stderr)
        # Before any session state: the gate sits ahead of args.func, so
        # not even .bale/ may exist yet.
        self.assertFalse(
            (self.repo / ".bale").exists(),
            msg=".bale/ was created despite the up-front refusal",
        )

    def run_pack(self, install: Path):
        return run_bale(
            install,
            [
                "pack", "sanity-gate probe goal",
                "--slug", "precheck-e2e",
                "--include", "hello.txt",
                "--no-readme",
            ],
            cwd=self.repo,
            env=self.env,
        )

    def run_handoff(self, install: Path):
        # The positional only needs to parse; on a broken install the
        # gate must fire before resolution ever looks at it.
        return run_bale(
            install,
            ["handoff", "no-such-response.tar.gz"],
            cwd=self.repo,
            env=self.env,
        )

    # -- broken install: both commands refuse, identically ---------------

    def test_missing_global_doc_refuses_pack_and_handoff(self) -> None:
        (self.install / "docs" / "CODE.md").unlink()

        pack = self.run_pack(self.install)
        self.assert_refused_up_front(pack, "CODE.md")

        handoff = self.run_handoff(self.install)
        self.assert_refused_up_front(handoff, "CODE.md")
        # Fired before tarball resolution: the bogus path never surfaced.
        self.assertNotIn("no-such-response", handoff.stderr)

        # Message parity with pack's refusal, byte for byte.
        self.assertEqual(error_line(pack.stderr), error_line(handoff.stderr))

    def test_missing_injected_tool_refuses_pack_and_handoff(self) -> None:
        (self.install / "tools" / "response_lint.py").unlink()

        pack = self.run_pack(self.install)
        self.assert_refused_up_front(pack, "tools/response_lint.py")

        handoff = self.run_handoff(self.install)
        self.assert_refused_up_front(handoff, "tools/response_lint.py")
        self.assertNotIn("no-such-response", handoff.stderr)

        self.assertEqual(error_line(pack.stderr), error_line(handoff.stderr))

    # -- intact install: the gate is pass-through ------------------------

    def test_intact_install_handoff_passes_gate(self) -> None:
        """Handoff proceeds past the gate and fails later, on resolution."""
        result = self.run_handoff(self.install)
        self.assertEqual(result.returncode, 1, msg=result.stderr)
        self.assertNotIn(MISSING_MARKER, result.stderr)
        self.assertIn("not found", result.stderr)

    def test_intact_install_pack_end_to_end(self) -> None:
        """A full piped pack succeeds — the widened gate broke nothing."""
        result = self.run_pack(self.install)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        outbox = self.repo / ".bale" / "outbox"
        tarballs = list(outbox.glob("request-*.tar.gz"))
        self.assertEqual(
            len(tarballs), 1,
            msg=f"expected one request tarball in {outbox}, "
                f"found {[t.name for t in tarballs]}",
        )


if __name__ == "__main__":
    unittest.main()
