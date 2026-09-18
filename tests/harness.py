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
35 when the apply suites became its second and third consumers) and,
since board 80, the two in-process unit helpers ``_load_module`` /
``_minimal_record`` (extracted from test_telemetry_extensions.py when
test_admission_prompts.py became their second copy) — see the banner
sections at the bottom. Board 109 added two more there: ``_load_cli``,
the in-process loader for ``bin/bale`` itself (the script, not a
sibling), and ``normalize``, the whitespace collapse the two doc-pin
suites share.

The suites import from here (``from harness import ...``); both direct
execution (``python3 tests/<suite>.py``) and discovery
(``python3 -m unittest discover -s tests``) put ``tests/`` on
``sys.path``, so the bare module name resolves in both run modes.
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# The install trees build_request_tarball copies from, mirrored from the
# constants in bin/bale (INSTALL_ROOT layout). Copied wholesale so the
# scratch install behaves exactly like a release-tarball install.
INSTALL_TREES = ("bin", "docs", "schemas", "tools")

SUBPROCESS_TIMEOUT = 120  # seconds; generous — each bale run is sub-second.


# ---------------------------------------------------------------------------
# The slow-test gate (board-50 fold-in, landed at 0.4.16)
# ---------------------------------------------------------------------------
#
# Generation-heavy cases -- the ones whose cost is dominated by building
# sandbox installs and driving full pack/apply cycles -- gate behind an
# opt-in env var so the default ``unittest discover`` run stays under
# the two-minute validation target (TARBALL.md section 7.6). The gate is
# harness-level by design: one home, every suite imports it; a per-suite
# copy is exactly the drift this helper exists to prevent. The board-50
# session's response-side validation used a ``--slow`` spelling locally;
# that was per-response, not the convention -- this is the one home.
#
# The env var is spelled BALE_TEST_SLOW, exactly. Only the literal
# value ``"1"`` opens the gate: any other value (``yes``, ``true``, a
# typo) leaves it closed, and the skip reason names the exact spelling,
# so a half-set gate fails loud in the skip line instead of silently
# half-opening.
#
# Usage, per case or per class::
#
#     from harness import slow
#
#     @slow
#     def test_expensive_e2e(self): ...

SLOW_ENV_VAR = "BALE_TEST_SLOW"


def slow_gate():
    """Build the skip decorator from the environment as it stands now.

    Exposed as a factory (rather than only the module-level ``slow``
    baked at import) so tests/test_slow_gate.py can exercise both gate
    states without re-importing this module.
    """
    return unittest.skipUnless(
        os.environ.get(SLOW_ENV_VAR) == "1",
        f"generation-heavy; set {SLOW_ENV_VAR}=1 to run the full suite",
    )


slow = slow_gate()



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


# ---------------------------------------------------------------------------
# In-process bin/ module loader and the smallest-valid telemetry record
# ---------------------------------------------------------------------------
#
# Extracted from tests/test_telemetry_extensions.py at board 80, when
# tests/test_admission_prompts.py landed as the second copy of both —
# the same one-harness doctrine as everything above. The two copies had
# drifted slightly and this is the reconciled form:
#
# - ``_load_module`` puts bin/ on sys.path and registers the module
#   under its bare name (the admission-prompts form). The telemetry
#   copy loaded unregistered under a ``_under_test`` alias, which was
#   enough for bale_validate / bale_report / bale_stats (no sibling
#   imports at module scope) but not for bale_apply, whose sibling
#   imports need bin/ importable. The superset serves both suites; the
#   library-import property the checkpoint contract relies on — a bin/
#   sibling imports nothing from __main__ at module scope — is what
#   makes loading by path possible at all, and is unchanged.
# - ``_minimal_record`` keeps the telemetry copy's envelope (an
#   ``unlocked`` / ``unlock`` attempt): test_telemetry_extensions'
#   stats-tolerance case reads the ``unlocked`` closure-mix bucket the
#   record lands in, while nothing in test_admission_prompts depends on
#   the ``applied`` / ``apply`` envelope its copy used.
#
# tests/test_escalation_schemas.py carries its own ``_load_module`` and
# tests/test_sandbox_wrapper.py a method-form ``_minimal_record``; both
# were out of the board-80 row and stand as-is.

BIN_DIR = REPO_ROOT / "bin"


def _load_module(name: str):
    """Import bin/<name>.py by path without bin/bale's __main__.

    bin/ goes on sys.path (once) so a loaded module's own sibling
    imports resolve, and the module is registered under its bare
    name so a later sibling import finds this instance rather than
    loading a second copy.
    """
    if str(BIN_DIR) not in sys.path:
        sys.path.insert(0, str(BIN_DIR))
    spec = importlib.util.spec_from_file_location(name, BIN_DIR / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _minimal_record(**attempt_overrides) -> dict:
    """A smallest-valid telemetry record: the required envelope plus one
    minimal attempt, with per-test attempt overrides."""
    attempt = {"at": "2026-08-13T00:00:00+00:00",
               "outcome": "unlocked", "command": "unlock"}
    attempt.update(attempt_overrides)
    return {
        "record_version": 1,
        "session_id": "2026-08-13-fx-min-001",
        "created_at": "2026-08-13T00:00:00+00:00",
        "updated_at": "2026-08-13T00:00:00+00:00",
        "outcome": "unlocked",
        "attempts": [attempt],
    }


# ---------------------------------------------------------------------------
# In-process loader for bin/bale itself (board 109)
# ---------------------------------------------------------------------------
#
# From 2026-09-17-board-106-bale-dedup-003's Proposals: functions that live
# only in bin/bale (fail_not_found, SubcommandHelpFormatter._fill_text,
# compose_retry_successor, ...) had no in-process route to a unit test, so
# that session pinned them end to end instead of inventing a loader in three
# test files. _load_module above cannot serve: bin/bale has no .py suffix,
# and it is the script whose __main__ the siblings reach back into.
#
# The shape reconciles the two ad-hoc copies already in the tree
# (tests/test_thread_status.py's load_bale_module and
# tests/test_craft_response.py's ExchangeBlockParity.setUpClass): an
# explicit SourceFileLoader, the module registered under a name that is
# never "__main__" so the guarded main() does not run and dataclasses
# resolve their module by name. What it adds over both copies is
# hygiene a shared helper owes every consumer: bin/bale's own
# unconditional sys.path.insert is undone (bin/ is added only when
# absent, as _load_module does, and repeated loads never grow the
# path), a failed
# load leaves no half-built module registered, and an import-time
# sys.exit (a missing VERSION file) surfaces as a named error instead of
# a bare SystemExit. Adopting it in those two suites is left to them —
# neither is in this row.

CLI_PATH = BIN_DIR / "bale"
CLI_MODULE_NAME = "bale_cli"


def _load_cli():
    """Load bin/bale by path as an ordinary module and return it.

    The module is registered in sys.modules as ``bale_cli`` (never
    ``__main__``), so bin/bale's ``if __name__ == "__main__"`` guard
    keeps main() from running: nothing parses argv, nothing exits, and
    the returned module's functions are called directly —
    ``_load_cli().fail_not_found(...)``.

    Each call executes bin/bale afresh and returns a new module, so a
    test that mutates module state (``_log_file``, a constant) cannot
    leak it into the next load. The siblings bin/bale imports at module
    scope are *not* fresh: they resolve through sys.modules by bare
    name, so a sibling a suite already loaded with ``_load_module`` is
    the very instance bin/bale binds (no second copy), and a sibling
    first imported here is the instance a later bare import finds.
    bin/ is put on sys.path only when absent, as ``_load_module`` does;
    bin/bale's own unconditional insert is undone, so no number of
    loads grows sys.path. (Entries other suites add are theirs.)

    The limit, and it is structural: the siblings reach back into bale
    *lazily*, with ``from __main__ import fail`` (and friends) inside
    the functions that need it. ``__main__`` is the process's real main
    module — the unittest runner, or the suite file run directly —
    never this loaded CLI. So a bin/bale function is in reach only if
    its call path stays inside bin/bale and the siblings' eager
    surface; one that calls into a sibling function which reaches back
    fails with ImportError (or, worse, binds a same-named attribute of
    the runner's ``__main__``). Pure functions and bin/bale's own
    helpers — fail_not_found, the help formatter, anything that calls
    bin/bale's fail() directly — are the intended targets. Calling
    fail() (directly or through a helper) still raises SystemExit, as
    the CLI would; a test catches it.

    Raises RuntimeError, chained to the SystemExit, if bin/bale exits
    at import (its VERSION guard); any other import-time exception
    propagates as-is. Either way ``bale_cli`` is left as it was before
    the call.
    """
    if str(BIN_DIR) not in sys.path:
        sys.path.insert(0, str(BIN_DIR))
    path_before = list(sys.path)
    previous = sys.modules.get(CLI_MODULE_NAME)
    loader = importlib.machinery.SourceFileLoader(
        CLI_MODULE_NAME, str(CLI_PATH))
    spec = importlib.util.spec_from_file_location(
        CLI_MODULE_NAME, str(CLI_PATH), loader=loader)
    module = importlib.util.module_from_spec(spec)
    sys.modules[CLI_MODULE_NAME] = module  # dataclasses resolve by name
    try:
        loader.exec_module(module)
    except BaseException as exc:
        # Restore the registry first, so a failed load never leaves a
        # half-executed module behind for a later lookup to find.
        if previous is None:
            sys.modules.pop(CLI_MODULE_NAME, None)
        else:
            sys.modules[CLI_MODULE_NAME] = previous
        if isinstance(exc, SystemExit):
            raise RuntimeError(
                f"bin/bale exited while loading in-process from "
                f"{CLI_PATH} (exit payload: {exc.code!r}) — its "
                f"module-scope guards refused the install tree"
            ) from exc
        raise
    finally:
        # bin/bale inserts its own bin/ at sys.path[0] unconditionally;
        # drop that duplicate so repeated loads do not grow the path.
        sys.path[:] = path_before
    return module


# ---------------------------------------------------------------------------
# Whitespace normalization for the doc-pin suites (board 109)
# ---------------------------------------------------------------------------
#
# From 2026-09-14-board-80-tests-only-pins-008's Proposals (a fold-in
# registry rider that rode row 109 because it holds this file):
# tests/test_doc_crossrefs.py and tests/test_sanctioned_pairs.py each
# carried an identical ``" ".join(text.split())`` — docstrings differing by
# one word — and the harness's doctrine is one home per helper. Both suites
# now import it from here.


def normalize(text: str) -> str:
    """Collapse every whitespace run to a single space and strip the
    ends — the rewrapping tolerance of the doc-pin suites: a prose pin
    matches words, never line breaks or the docs' 70-column wrap."""
    return " ".join(text.split())
