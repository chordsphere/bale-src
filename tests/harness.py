"""Shared hermetic-sandbox harness for the bale test suites.

Extracted from ``tests/test_install_precheck.py`` (the first suite)
when the second suite landed — the ratified deferred trigger from the
board-11 decision: one harness, consumed by every suite, instead of a
copy per file. The doctrine is unchanged from the original inline
form (ADR-0005, fully hermetic):

- ``HOME`` points at a temp dir; the git identity lives in a temp
  ``.gitconfig`` there, so no read or write ever touches the
  developer's real global config.
- ``BALE_INSTALL`` points at a temp dir, so any reinstall-shaped
  operation would land in the sandbox.
- ``EDITOR``/``VISUAL`` are stubbed to ``/bin/true`` so a regression
  into an editor path exits fast instead of hanging.
- Each test runs a scratch install copied from this repo and a scratch
  git repo under the temp dir. The git binary is real (a hard
  dependency; stubbing it would test a fiction) — only its config and
  state are sandboxed.
- bale is always invoked by absolute path into the scratch install,
  never resolved from ``$PATH``.

The suites import from here (``from harness import ...``); both direct
execution (``python3 tests/<suite>.py``) and discovery
(``python3 -m unittest discover -s tests``) put ``tests/`` on
``sys.path``, so the bare module name resolves in both run modes.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The install trees build_request_tarball copies from, mirrored from the
# constants in bin/bale (INSTALL_ROOT layout). Copied wholesale so the
# scratch install behaves exactly like a release-tarball install.
INSTALL_TREES = ("bin", "docs", "schemas", "tools")

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
                f"the INSTALL_TREES list in the harness may be stale"
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
