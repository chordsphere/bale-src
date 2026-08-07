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

Besides the sandbox makers and runners, the module carries the shared
response-tarball fixture builder (``build_response_dir`` /
``tar_response_dir``, extracted from test_hold_retry_e2e.py at board
35 when the apply suites became its second and third consumers) — see
the banner section at the bottom.

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


PTY_TIMEOUT = 60  # seconds; generous — a wizard pack run is sub-second.


def run_bale_pty(install: Path, args: list, *, cwd: Path, env: dict,
                 answers: str):
    """Invoke bale under a pseudo-terminal, feeding prompt answers.

    Prompt paths (the wizard, confirm_yn exchanges) engage only when
    stdin is a TTY, so the piped run_bale cannot reach them; this
    runner attaches a real pty. Extracted from test_readonly_pack.py
    when the supersession suite became its second consumer — the same
    one-harness doctrine that produced this module (board 11).
    All `answers` are written up front (the kernel line-buffers them for
    the successive input() prompts) and the master side is drained
    continuously so a chatty child can never deadlock on a full pty
    buffer. Returns (exit_code, combined_output) — stdout and stderr
    share the pty, which is exactly what the prompting user sees.
    """
    import pty
    import select
    import time

    master, slave = pty.openpty()
    try:
        proc = subprocess.Popen(
            [sys.executable, str(install / "bin" / "bale"), *args],
            cwd=cwd, env=env,
            stdin=slave, stdout=slave, stderr=slave,
            close_fds=True,
        )
        os.close(slave)
        slave = None
        os.write(master, answers.encode())
        chunks: list[bytes] = []
        deadline = time.monotonic() + PTY_TIMEOUT
        while True:
            if time.monotonic() > deadline:
                proc.kill()
                raise AssertionError(
                    "pty-driven bale run timed out; output so far:\n"
                    + b"".join(chunks).decode(errors="replace")
                )
            readable, _, _ = select.select([master], [], [], 0.1)
            if master in readable:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break  # child closed its side (Linux raises EIO)
                if not chunk:
                    break
                chunks.append(chunk)
            elif proc.poll() is not None:
                # Child exited and nothing is left to read.
                break
        exit_code = proc.wait(timeout=SUBPROCESS_TIMEOUT)
    finally:
        if slave is not None:
            os.close(slave)
        os.close(master)
    return exit_code, b"".join(chunks).decode(errors="replace")


# ---------------------------------------------------------------------------
# Response-tarball fixture builder
# ---------------------------------------------------------------------------
#
# Extracted from tests/test_hold_retry_e2e.py's build_response_tarball when
# the apply pre-flight and real-operations suites became its second and third
# consumers (board 35) — the same one-harness doctrine that produced this
# module and run_bale_pty (board 11). Sizes and hashes are computed from the
# bytes written, never transcribed (TARBALL.md section 5.2.1); the manifest
# shape mirrors TARBALL.md section 5.2. The builder produces a *valid*
# response by construction; suites that need a malformed one build valid
# first and tamper the result (see test_apply_preflight.py), so every
# rejection test is exactly one mutation away from a known-good baseline.

NO_OP_APPLY_SH = "#!/usr/bin/env bash\n# No additional operations (test fixture).\nexit 0\n"


def passing_validation_sh(check: str = "fixture check") -> str:
    """A minimal validation.sh printing one [PASS] line for `check`."""
    return (
        "#!/usr/bin/env bash\n"
        f"echo \"[PASS] {check}\"\n"
        "exit 0\n"
    )


def build_response_dir(dest: Path, sid: str, *, summary: str,
                       entries: list, apply_sh: str = NO_OP_APPLY_SH,
                       validation_sh: str = None,
                       validation_will_run: list = None,
                       claims: dict = None,
                       manifest_extra: dict = None) -> Path:
    """Write a response-NNN/ directory under `dest` and return its path.

    `entries` is a list of dicts shaped like manifest changes[] entries,
    except created/modified entries carry the file content under a `data`
    key (bytes) instead of size_bytes/sha256 — the builder writes the
    bytes under files/ and computes both fields from them. Deleted
    entries carry no `data` and get the two literals (size_bytes: 0,
    sha256: null) per TARBALL.md section 5.2.1.

    `manifest_extra` entries are merged into the manifest last, so a
    caller can add or override top-level fields (e.g. response_kind,
    questions) without the builder growing a parameter per field.
    """
    import hashlib
    import json

    nnn = sid[-3:]
    rdir = dest / f"response-{nnn}"
    (rdir / "files").mkdir(parents=True)

    changes = []
    for entry in entries:
        change = {k: v for k, v in entry.items() if k != "data"}
        if entry["action"] in ("created", "modified"):
            data = entry["data"]
            f = rdir / "files" / entry["path"]
            f.parent.mkdir(parents=True, exist_ok=True)
            f.write_bytes(data)
            change["size_bytes"] = len(data)
            change["sha256"] = hashlib.sha256(data).hexdigest()
        else:  # deleted — no file under files/, the two literals
            change["size_bytes"] = 0
            change["sha256"] = None
        changes.append(change)

    if validation_will_run is None:
        validation_will_run = ["fixture check"]
    manifest = {
        "session_id": sid,
        "responds_to": sid,
        "corrects": None,
        "response_kind": "normal",
        "summary": summary,
        "changes": changes,
        "deferred": [],
        "validation_will_run": validation_will_run,
        "claims": claims if claims is not None else {},
    }
    if manifest_extra:
        manifest.update(manifest_extra)

    (rdir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (rdir / "apply.sh").write_text(apply_sh, encoding="utf-8")
    (rdir / "validation.sh").write_text(
        validation_sh if validation_sh is not None
        else passing_validation_sh(), encoding="utf-8")
    return rdir


def tar_response_dir(rdir: Path) -> Path:
    """Tar response-NNN/ into response-NNN.tar.gz beside it; return the path."""
    import tarfile

    tarball = rdir.parent / f"{rdir.name}.tar.gz"
    with tarfile.open(tarball, "w:gz") as tf:
        tf.add(str(rdir), arcname=rdir.name)
    return tarball
