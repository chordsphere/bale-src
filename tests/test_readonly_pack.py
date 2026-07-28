#!/usr/bin/env python3
"""Hermetic E2E for the read-only session shape (v0.3.15).

Pins the board-24 contract: a `bale pack --read-only` (or the wizard's
read-only answer) opens a session whose recorded scope is EMPTY — a
third, distinct scope state. The pairing under test is the load-bearing
claim of the feature: the session is invisible to the ADR-0006/0007
disjointness gates *by design* (an empty scope intersects nothing, so
siblings pack and apply freely while it stays open), and that is safe
*only because* the own-scope drift gate refuses everything such a
session might land (an empty scope covers nothing). Both halves are
asserted here, plus the legacy edge the feature must not disturb: a
*missing* scope.json still reads conservative whole-tree — empty and
missing must never collapse into one state.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring. Two points
specific to this suite: the wizard tests drive bale through a real
pseudo-terminal (the wizard engages only on a TTY, and stubbing
isatty would test a fiction), and the apply tests build a minimal but
fully valid response tarball (computed sha256s, no-op scripts) so the
drift gate is reached through the same pre-flight every real response
passes.

Run directly::

    python3 tests/test_readonly_pack.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import hashlib
import json
import os
import pty
import select
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
from pathlib import Path

from harness import (
    SUBPROCESS_TIMEOUT,
    bale_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
)

# Sentinels for the surfaces this file pins. Kept in one place so a
# message rewording breaks one line, not several assertions.
SHAPE_QUESTION_MARKER = "Will this session land changes"
DRIFT_REFUSAL_MARKER = "SCOPE-DRIFT-REFUSED"
READONLY_MARKER = "read-only"
INTERSECT_MARKER = "pack scope intersects"

PTY_TIMEOUT = 60  # seconds; generous — a wizard pack run is sub-second.


def run_bale_pty(install: Path, args: list, *, cwd: Path, env: dict,
                 answers: str):
    """Invoke bale under a pseudo-terminal, feeding wizard answers.

    The wizard engages only when stdin is a TTY, so the piped
    harness.run_bale cannot reach it; this runner attaches a real pty.
    All `answers` are written up front (the kernel line-buffers them for
    the successive input() prompts) and the master side is drained
    continuously so a chatty child can never deadlock on a full pty
    buffer. Returns (exit_code, combined_output) — stdout and stderr
    share the pty, which is exactly what the wizard user sees.
    """
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


class ReadonlyPackTest(unittest.TestCase):
    """The read-only session shape: empty scope, gates, wizard, status."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-readonly-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack(self, *extra: str, slug: str = "session-a"):
        """A fully specified piped pack; extras append to the base form."""
        return run_bale(
            self.install,
            [
                "pack", "read-only shape test goal",
                "--slug", slug,
                "--include", "hello.txt",
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def assert_pack_ok(self, result) -> str:
        """Pack succeeded; return its sid (the newest registry entry)."""
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        sids = self.open_sids()
        self.assertTrue(sids, msg="pack succeeded but no session is open")
        return sids[-1]

    def open_sids(self) -> list:
        """Open sids, oldest-first by directory mtime then name."""
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        entries = [d for d in root.iterdir() if (d / "open").is_file()]
        entries.sort(key=lambda d: (d.stat().st_mtime, d.name))
        return [d.name for d in entries]

    def scope_json(self, sid: str):
        """The raw recorded scope for sid, or None when the file is absent."""
        p = self.repo / ".bale" / "sessions" / sid / "scope.json"
        if not p.is_file():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def build_response_tarball(self, sid: str, *, path: str,
                               content: str) -> Path:
        """A minimal, fully valid normal response: one created file.

        Computed size/sha256 (never transcribed), syntactically valid
        no-op apply.sh / validation.sh, and a manifest that passes the
        response schema — so the apply pipeline reaches the drift gate
        through the same pre-flight every real response passes, and a
        refusal there is attributable to the gate, not to a malformed
        fixture.
        """
        nnn = sid[-3:]
        rdir = self.tmp / f"response-{nnn}"
        (rdir / "files").mkdir(parents=True)
        target = rdir / "files" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8")
        target.write_bytes(data)
        manifest = {
            "session_id": sid,
            "responds_to": sid,
            "corrects": None,
            "response_kind": "normal",
            "summary": "drift-gate fixture: one created file, outside the "
                       "(empty) read-only scope by construction",
            "changes": [
                {
                    "path": path,
                    "action": "created",
                    "reason": "fixture change to exercise the own-scope "
                              "drift gate against an empty recorded scope",
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            ],
            "deferred": [],
            "validation_will_run": [],
            "claims": {},
        }
        (rdir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        noop = "#!/usr/bin/env bash\n# no-op (test fixture)\nexit 0\n"
        (rdir / "apply.sh").write_text(noop, encoding="utf-8")
        (rdir / "validation.sh").write_text(noop, encoding="utf-8")
        tarball = self.tmp / f"response-{nnn}.tar.gz"
        with tarfile.open(tarball, "w:gz") as tf:
            tf.add(str(rdir), arcname=f"response-{nnn}")
        return tarball

    # -- pinned behavior 1: empty scope recorded -------------------------

    def test_readonly_flag_records_empty_scope(self) -> None:
        """--read-only opens a session whose scope.json is exactly []."""
        sid = self.assert_pack_ok(self.pack("--read-only"))
        self.assertEqual(self.scope_json(sid), [])
        # And the inference: no --work-class given, so the stamp is meta.
        stamped = json.loads(
            (self.repo / ".bale" / "sessions" / sid / "manifest.json")
            .read_text(encoding="utf-8"))
        self.assertEqual(stamped["provenance"]["work_class"], "meta")

    def test_default_pack_scope_unchanged(self) -> None:
        """Without the flag, a piped pack records scope exactly as before."""
        sid = self.assert_pack_ok(self.pack())
        self.assertEqual(self.scope_json(sid), ["hello.txt"])
        stamped = json.loads(
            (self.repo / ".bale" / "sessions" / sid / "manifest.json")
            .read_text(encoding="utf-8"))
        # The un-asked piped path still stamps the pre-v0.3.15 default.
        self.assertEqual(stamped["provenance"]["work_class"], "mixed")

    # -- pinned behavior 2: siblings admitted while it stays open --------

    def test_sibling_pack_admitted_beside_readonly(self) -> None:
        """Any include set packs freely while a read-only session is open."""
        ro_sid = self.assert_pack_ok(self.pack("--read-only"))
        second = self.pack(slug="session-b")
        self.assertEqual(
            second.returncode, 0,
            msg=f"stdout:\n{second.stdout}\nstderr:\n{second.stderr}",
        )
        sids = self.open_sids()
        self.assertEqual(len(sids), 2)
        self.assertIn(ro_sid, sids)

    def test_whole_tree_sibling_admitted_beside_readonly(self) -> None:
        """Even a whole-tree pack is admitted beside a read-only session
        (and only beside it): [] intersects nothing, including '.'."""
        self.assert_pack_ok(self.pack("--read-only"))
        second = run_bale(
            self.install,
            ["pack", "whole tree beside read-only", "--slug", "session-b",
             "--no-readme", "--force"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            second.returncode, 0,
            msg=f"stdout:\n{second.stdout}\nstderr:\n{second.stderr}",
        )
        self.assertEqual(len(self.open_sids()), 2)

    # -- pinned behavior 3: legacy missing-scope path untouched ----------

    def test_missing_scope_json_stays_conservative(self) -> None:
        """A deleted scope.json reads whole-tree: empty ≠ missing."""
        ro_sid = self.assert_pack_ok(self.pack("--read-only"))
        (self.repo / ".bale" / "sessions" / ro_sid / "scope.json").unlink()
        second = self.pack(slug="session-b")
        self.assertEqual(second.returncode, 1, msg=second.stdout)
        self.assertIn(INTERSECT_MARKER, second.stderr)
        self.assertIn(ro_sid, second.stderr)

    # -- pinned behavior 4: the drift gate refuses every self-land -------

    def test_apply_refuses_drift_for_readonly_session(self) -> None:
        """Any changes[] under the read-only sid refuses at the drift gate,
        and the refusal names the session as read-only."""
        sid = self.assert_pack_ok(self.pack("--read-only"))
        tarball = self.build_response_tarball(
            sid, path="landed.txt", content="should never land\n")
        result = run_bale(
            self.install, ["apply", str(tarball)],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 1,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertIn(DRIFT_REFUSAL_MARKER, result.stdout)
        self.assertIn(READONLY_MARKER, result.stdout)
        # Refusal is pre-staging: nothing landed, session stays open.
        self.assertFalse((self.repo / "landed.txt").exists())
        self.assertIn(sid, self.open_sids())

    def test_allow_out_of_scope_admits_past_gate(self) -> None:
        """--allow-out-of-scope admits named paths past the gate for a
        read-only session too (uniform override, master's recommendation;
        exercised under --dry-run, which runs the same gate)."""
        sid = self.assert_pack_ok(self.pack("--read-only"))
        tarball = self.build_response_tarball(
            sid, path="landed.txt", content="admitted deliberately\n")
        refused = run_bale(
            self.install, ["apply", str(tarball), "--dry-run"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(refused.returncode, 1, msg=refused.stdout)
        self.assertIn(DRIFT_REFUSAL_MARKER, refused.stdout)
        admitted = run_bale(
            self.install,
            ["apply", str(tarball), "--dry-run",
             "--allow-out-of-scope", "landed.txt"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            admitted.returncode, 0,
            msg=f"stdout:\n{admitted.stdout}\nstderr:\n{admitted.stderr}",
        )
        self.assertNotIn(DRIFT_REFUSAL_MARKER, admitted.stdout)
        # Dry run: still nothing on disk.
        self.assertFalse((self.repo / "landed.txt").exists())

    # -- pinned behavior 5: wizard reaches the question; flags skip it ---

    def test_wizard_reaches_session_shape_question(self) -> None:
        """A bare cold-start wizard run asks the question; the read-only
        answer records an empty scope and infers work_class meta."""
        answers = (
            "wizard read-only goal\n"   # goal
            "wizard-ro\n"               # slug
            "r\n"                       # session shape: read-only
            "\n"                        # excludes: none
            "\n"                        # constraints: none
            "\n"                        # out-of-scope: none
            "n\n"                       # README prompt: no
        )
        code, output = run_bale_pty(
            self.install, ["pack"], cwd=self.repo, env=self.env,
            answers=answers,
        )
        self.assertEqual(code, 0, msg=output)
        self.assertIn(SHAPE_QUESTION_MARKER, output)
        sids = self.open_sids()
        self.assertEqual(len(sids), 1, msg=output)
        self.assertEqual(self.scope_json(sids[0]), [])
        stamped = json.loads(
            (self.repo / ".bale" / "sessions" / sids[0] / "manifest.json")
            .read_text(encoding="utf-8"))
        self.assertEqual(stamped["provenance"]["work_class"], "meta")

    def test_wizard_default_answer_keeps_whole_tree(self) -> None:
        """Bare Enter at the question is the pre-v0.3.15 pack: mixed
        work class, whole-tree scope — an answered default now."""
        answers = (
            "wizard default goal\n"
            "wizard-default\n"
            "\n"                        # session shape: Enter -> mixed
            "\n" "\n" "\n"              # excludes, constraints, oos
            "n\n"                       # README prompt: no
        )
        code, output = run_bale_pty(
            self.install, ["pack"], cwd=self.repo, env=self.env,
            answers=answers,
        )
        self.assertEqual(code, 0, msg=output)
        self.assertIn(SHAPE_QUESTION_MARKER, output)
        sids = self.open_sids()
        self.assertEqual(len(sids), 1, msg=output)
        self.assertEqual(self.scope_json(sids[0]), ["."])
        stamped = json.loads(
            (self.repo / ".bale" / "sessions" / sids[0] / "manifest.json")
            .read_text(encoding="utf-8"))
        self.assertEqual(stamped["provenance"]["work_class"], "mixed")

    def test_bare_flag_path_skips_question(self) -> None:
        """A fully specified command never shows the question — piped
        here, which also proves no prompt path engages at all."""
        result = self.pack("--read-only")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        combined = result.stdout + result.stderr
        self.assertNotIn(SHAPE_QUESTION_MARKER, combined)

    # -- status rendering ------------------------------------------------

    def test_status_renders_readonly_scope(self) -> None:
        """`bale status` names the empty scope instead of printing an
        empty string or a whole-tree reading."""
        self.assert_pack_ok(self.pack("--read-only"))
        result = run_bale(
            self.install, ["status"], cwd=self.repo, env=self.env,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("locks nothing, lands nothing", result.stdout)
        self.assertNotIn(". (whole tree)", result.stdout)


if __name__ == "__main__":
    unittest.main()
