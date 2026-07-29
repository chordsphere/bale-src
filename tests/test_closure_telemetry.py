#!/usr/bin/env python3
"""Hermetic E2E for closure telemetry (v0.3.16).

Pins the board-25 contract: every registry close is a recorded event
(BALE.md section 8.9 / section 9.3). Before this feature the telemetry
corpus was structurally apply-only — only apply and revert wrote
records — so sessions that ended in `bale unlock` (abandonments,
master close-outs, crash-debris cleanup, and every read-only session,
whose only exit is unlock by construction) left no durable trace.
The suite asserts the four unlock-side behaviors and revert's
`--reason` threading:

- a plain unlock records outcome `unlocked`, command `unlock`,
  closure_reason `abandoned`, with the session's scope captured
  before the wipe destroyed it;
- a read-only session's unlock infers `closed-read-only`, keyed on
  the recorded scope being exactly `[]`;
- an explicit `--reason` beats the read-only inference;
- the no-sid crash-debris sweep best-effort appends a `crash-debris`
  entry for the sid the stale pointer named, without disturbing the
  benign no-op contract;
- revert's `closure_reason` threads through `build_telemetry_attempt`
  (unit-shaped — see the class docstring for the depth rationale)
  and the `--reason` flag is wired with the shared choices.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_closure_telemetry.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import importlib.util
import json
import sys
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

# Sentinels for the surfaces this file pins. Kept in one place so a
# message rewording breaks one line, not several assertions.
TELEMETRY_ROW_MARKER = "telemetry"
RECORDED_MARKER = "recorded claude/telemetry/"
NO_OPEN_SESSION_MARKER = "no open session; nothing to unlock"


def load_bale_report(install: Path):
    """Import the scratch install's bale_report module by path.

    The unit-shaped revert assertions call build_telemetry_attempt
    directly; loading it from the scratch install (not the repo)
    keeps the suite exercising exactly the bytes an installed bale
    would run, per the harness's absolute-path doctrine.
    """
    path = install / "bin" / "bale_report.py"
    spec = importlib.util.spec_from_file_location("bale_report_under_test",
                                                  str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ClosureTelemetryTest(unittest.TestCase):
    """Unlock and revert write durable closure records with a reason.

    Depth choice for revert (ADR-0003 dogfood-depth judgment, flagged
    in the response's notes.md): the reason threading is asserted
    unit-shaped — a direct build_telemetry_attempt call plus CLI
    wiring smoke (the flag exists; bogus values are rejected with the
    choices listed) — rather than through a full HOLD fixture. A real
    HOLD requires driving the apply pipeline to a validation failure
    and through its walkthrough prompt; that fixture would cost far
    more than it proves here, because revert's record write itself is
    pre-existing, already exercised behavior — this session's delta
    is one threaded argument.
    """

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-closure-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack(self, *extra: str, slug: str = "closure-a"):
        """A fully specified piped pack; extras append to the base form."""
        return run_bale(
            self.install,
            [
                "pack", "closure telemetry test goal",
                "--slug", slug,
                "--include", "hello.txt",
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def unlock(self, *extra: str):
        return run_bale(self.install, ["unlock", *extra],
                        cwd=self.repo, env=self.env)

    def assert_ok(self, result) -> None:
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        entries = [d for d in root.iterdir() if (d / "open").is_file()]
        entries.sort(key=lambda d: (d.stat().st_mtime, d.name))
        return [d.name for d in entries]

    def packed_sid(self, result) -> str:
        """Pack succeeded; return its sid (the newest registry entry)."""
        self.assert_ok(result)
        sids = self.open_sids()
        self.assertTrue(sids, msg="pack succeeded but no session is open")
        return sids[-1]

    def telemetry_record(self, sid: str) -> dict:
        p = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(
            p.is_file(),
            msg=f"expected telemetry record at {p}; "
                f"claude/ tree: {sorted((self.repo / 'claude').rglob('*')) if (self.repo / 'claude').is_dir() else 'absent'}",
        )
        return json.loads(p.read_text(encoding="utf-8"))

    # -- pinned behavior 1: plain unlock records `abandoned` -------------

    def test_unlock_records_abandoned_with_scope(self) -> None:
        """pack then unlock: outcome unlocked, reason abandoned, command
        unlock, and the scope captured before the wipe (non-empty)."""
        sid = self.packed_sid(self.pack())
        result = self.unlock()
        self.assert_ok(result)

        record = self.telemetry_record(sid)
        self.assertEqual(record["session_id"], sid)
        self.assertEqual(record["outcome"], "unlocked",
                         msg="envelope outcome mirrors the latest attempt")
        self.assertEqual(len(record["attempts"]), 1)
        attempt = record["attempts"][0]
        self.assertEqual(attempt["outcome"], "unlocked")
        self.assertEqual(attempt["command"], "unlock")
        self.assertEqual(attempt["closure_reason"], "abandoned")
        self.assertTrue(attempt["scope"],
                        msg="scope must be captured before the session-dir "
                            "wipe destroys scope.json")
        self.assertIsNone(attempt["tarball"])
        self.assertIsNone(attempt["validation"])
        self.assertEqual(attempt["change_paths"], [])
        # The wipe happened — the record is now the only trace.
        self.assertFalse(
            (self.repo / ".bale" / "sessions" / sid).exists())
        # And the summary told the operator where the record landed.
        self.assertIn(TELEMETRY_ROW_MARKER, result.stdout)
        self.assertIn(RECORDED_MARKER, result.stdout)

    # -- pinned behavior 2: read-only inference --------------------------

    def test_readonly_unlock_infers_closed_read_only(self) -> None:
        """pack --read-only then unlock: reason closed-read-only, keyed
        on the recorded scope being exactly []."""
        sid = self.packed_sid(self.pack("--read-only"))
        self.assert_ok(self.unlock())

        attempt = self.telemetry_record(sid)["attempts"][0]
        self.assertEqual(attempt["closure_reason"], "closed-read-only")
        self.assertEqual(attempt["scope"], [],
                         msg="the recorded empty scope is what the "
                             "inference keys on, and it records raw")

    # -- pinned behavior 3: explicit --reason beats the inference --------

    def test_explicit_reason_beats_readonly_inference(self) -> None:
        """The operator knows more than the heuristic: a read-only
        session unlocked with --reason abandoned records abandoned."""
        sid = self.packed_sid(self.pack("--read-only"))
        self.assert_ok(self.unlock("--reason", "abandoned"))

        attempt = self.telemetry_record(sid)["attempts"][0]
        self.assertEqual(attempt["closure_reason"], "abandoned")
        self.assertEqual(attempt["scope"], [])

    # -- pinned behavior 4: the crash-debris pointer path ----------------

    def test_crash_debris_sweep_records_for_named_sid(self) -> None:
        """A stale pointer naming a sid, no open marker (the half-state
        section 7.6's write ordering confines interruptions to): the
        no-sid unlock clears it, stays a benign no-op, and best-effort
        records a crash-debris closure for that sid."""
        debris_sid = "2026-07-01-crashed-pack-001"
        bale_dir = self.repo / ".bale"
        bale_dir.mkdir()
        (bale_dir / "current_session").write_text(f"{debris_sid}\n")

        result = self.unlock()
        self.assert_ok(result)
        self.assertIn(NO_OPEN_SESSION_MARKER, result.stdout,
                      msg="the benign no-op contract is untouchable")
        self.assertEqual(
            (bale_dir / "current_session").read_text(), "",
            msg="the stale pointer must be cleared")

        record = self.telemetry_record(debris_sid)
        attempt = record["attempts"][0]
        self.assertEqual(attempt["outcome"], "unlocked")
        self.assertEqual(attempt["command"], "unlock")
        self.assertEqual(attempt["closure_reason"], "crash-debris")
        self.assertEqual(attempt["scope"], [],
                         msg="no scope was ever recorded for the debris "
                             "sid; [] means 'no scope recorded', never "
                             "the fabricated whole-tree widening")
        self.assertIsNone(attempt["tarball"])
        self.assertIsNone(attempt["validation"])

    def test_empty_pointer_writes_nothing(self) -> None:
        """An empty pointer names no session, so nothing records."""
        bale_dir = self.repo / ".bale"
        bale_dir.mkdir()
        (bale_dir / "current_session").write_text("")

        result = self.unlock()
        self.assert_ok(result)
        self.assertIn(NO_OPEN_SESSION_MARKER, result.stdout)
        self.assertFalse((self.repo / "claude" / "telemetry").exists(),
                         msg="no session to record — no record")

    # -- pinned behavior 5: revert's reason threading (unit-shaped) ------

    def test_revert_reason_threads_through_builder(self) -> None:
        """build_telemetry_attempt stamps closure_reason verbatim; the
        default is null. This is the revert delta — the call site
        passes args.reason straight through."""
        report = load_bale_report(self.install)
        with_reason = report.build_telemetry_attempt(
            outcome="reverted", command="revert",
            closure_reason="superseded-by-split",
        )
        self.assertEqual(with_reason["closure_reason"],
                         "superseded-by-split")
        without = report.build_telemetry_attempt(
            outcome="reverted", command="revert",
        )
        self.assertIsNone(without["closure_reason"],
                          msg="omitted --reason records an honest null")
        self.assertIn("superseded-by-split", report.CLOSURE_REASONS,
                      msg="board 26 consumes this value; it must survive")

    def test_reason_flag_wired_with_shared_choices(self) -> None:
        """Both commands reject a bogus --reason at the parser, listing
        the shared vocabulary — proof the flag is wired to
        CLOSURE_REASONS, without a full HOLD fixture."""
        for command in ("unlock", "revert"):
            result = run_bale(
                self.install, [command, "--reason", "not-a-reason"],
                cwd=self.repo, env=self.env)
            self.assertNotEqual(result.returncode, 0,
                                msg=f"{command} accepted a bogus reason")
            self.assertIn("closed-read-only", result.stderr,
                          msg=f"{command}'s rejection should list the "
                              f"valid choices")

    # -- guard: --integration takes no --reason --------------------------

    def test_integration_unlock_rejects_reason(self) -> None:
        """The integration lock is repo-level state, not a session;
        there is no closure to give a reason for."""
        result = self.unlock("--integration", "--reason", "abandoned")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("no closure", result.stderr.lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)
