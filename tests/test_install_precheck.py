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

Sandbox doctrine per ADR-0005 (fully hermetic):

- ``HOME`` points at a temp dir; the git identity lives in a temp
  ``.gitconfig`` there, so no read or write ever touches the
  developer's real global config.
- ``BALE_INSTALL`` points at a temp dir, so any reinstall-shaped
  operation would land in the sandbox (none is expected to fire here;
  the variable is set as insurance, not as a tested path).
- ``EDITOR``/``VISUAL`` are stubbed to ``/bin/true``. Every invocation
  in this file is piped (stdin is not a TTY), so no editor or prompt
  path should engage; the stub turns a regression there into a fast
  clean exit instead of a hang.
- Each test runs a scratch install copied from this repo and a scratch
  git repo under the temp dir. The git binary is real (a hard
  dependency; stubbing it would test a fiction) — only its config and
  state are sandboxed.
- bale is always invoked by absolute path into the scratch install,
  never resolved from ``$PATH``.

Run directly::

    python3 tests/test_install_precheck.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The install trees build_request_tarball copies from, mirrored from the
# constants in bin/bale (INSTALL_ROOT layout). Copied wholesale so the
# scratch install behaves exactly like a release-tarball install.
INSTALL_TREES = ("bin", "docs", "schemas", "tools")

# Sentinels for the refusal this file exists to pin. Kept in one place
# so a message rewording breaks one line, not six assertions.
MISSING_MARKER = "missing injected files"
REINSTALL_MARKER = "Reinstall bale."

SUBPROCESS_TIMEOUT = 120  # seconds; generous — each bale run is sub-second.


def make_sandbox_home(tmp: Path) -> Path:
    """Create the temp HOME with a sandboxed git identity (ADR-0005)."""
    home = tmp / "home"
    home.mkdir()
    (home / ".gitconfig").write_text(
        "[user]\n"
        "\tname = Bale Test Sandbox\n"
        "\temail = sandbox@example.invalid\n"
        "[init]\n"
        "\tdefaultBranch = main\n",
        encoding="utf-8",
    )
    return home


def make_install(tmp: Path) -> Path:
    """Copy this repo's install trees into a scratch install root.

    shutil.copytree preserves mode bits (copy2), so bin/bale arrives
    executable — though tests invoke it via the interpreter anyway.
    """
    install = tmp / "install"
    install.mkdir()
    for tree in INSTALL_TREES:
        src = REPO_ROOT / tree
        if not src.is_dir():
            raise AssertionError(
                f"repo is missing expected install tree {tree}/ — "
                f"the INSTALL_TREES list in this test may be stale"
            )
        shutil.copytree(src, install / tree)
    return install


def make_repo(tmp: Path, home: Path) -> Path:
    """Init a scratch git repo with one committed file, on branch main."""
    repo = tmp / "project"
    repo.mkdir()
    env = git_env(home)
    run_checked(["git", "init", "-b", "main"], cwd=repo, env=env)
    (repo / "hello.txt").write_text("hello\n", encoding="utf-8")
    run_checked(["git", "add", "hello.txt"], cwd=repo, env=env)
    run_checked(["git", "commit", "-m", "init"], cwd=repo, env=env)
    return repo


def git_env(home: Path) -> dict:
    """Minimal env: sandbox HOME/identity, real PATH for the git binary."""
    import os

    return {
        "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
        "HOME": str(home),
        "EDITOR": "/bin/true",
        "VISUAL": "/bin/true",
        "LANG": os.environ.get("LANG", "C.UTF-8"),
    }


def bale_env(home: Path, tmp: Path) -> dict:
    env = git_env(home)
    env["BALE_INSTALL"] = str(tmp / "bale-install-sandbox")
    return env


def run_checked(cmd: list, *, cwd: Path, env: dict) -> None:
    """Run a setup command; raise with full output on failure."""
    r = subprocess.run(
        cmd, cwd=cwd, env=env, capture_output=True, text=True,
        timeout=SUBPROCESS_TIMEOUT,
    )
    if r.returncode != 0:
        raise AssertionError(
            f"setup command failed: {cmd}\n"
            f"exit={r.returncode}\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}"
        )


def run_bale(install: Path, args: list, *, cwd: Path, env: dict):
    """Invoke the scratch install's bale by absolute path, piped stdin."""
    return subprocess.run(
        [sys.executable, str(install / "bin" / "bale"), *args],
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,  # not a TTY: no prompt path may engage
        capture_output=True,
        text=True,
        timeout=SUBPROCESS_TIMEOUT,
    )


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
