#!/usr/bin/env python3
"""Hermetic E2E for `bale unlock --json` (v0.3.18, board 29).

Pins BALE.md section 9.3's --json row: unlock was the one
summary-emitting lifecycle command without --json, and an orchestrator
closing (for instance) read-only sessions wants the telemetry path
machine-readable. The contract under test is the ratified json-mode
split: stdout carries exactly one line of JSON (the key contract owned
by format_unlock_json's docstring in bin/bale_report.py), every human
line — `[bale] ` logs and the summary block — goes to stderr, and human
mode is byte-untouched (no code path differs when the stream swap never
happens).

The suite asserts:

- the session-close path emits outcome `unlocked` with sid,
  closure_reason, session/lock facts, and the telemetry record path;
- the read-only inference (`closed-read-only`) rides through the json
  key;
- the benign no-op emits outcome `no-op` (sid null, debris null);
- the crash-debris sweep's no-op carries the debris object (the swept
  sid and its record path) without disturbing the no-op contract;
- refusal paths stay fail()-shaped: non-zero, stderr, nothing on
  stdout;
- `--integration --json` is refused (the report is session-shaped);
- human mode emits no JSON.

Board 35 (small pins, gap 5) added the `--integration` CLEAR path
itself (v0.3.2), previously covered only through its --json refusal:
a held lock is removed with the holder named and the live-apply
caveat printed; the not-held case is a benign exit-0 no-op; and an
unparseable lock file still clears, degrading to rows-only (no
[UNLOCK] headline, since a headline needs a sid the file couldn't
yield). The class fabricates `.bale/integration.lock` directly — the
lock is repo-level state apply holds only across its git window, so
the file is exactly what the command sees.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_unlock_json.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harness import (
    bale_env,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_checked,
)


def parse_single_json_line(stdout: str) -> dict:
    """The stream-discipline assertion in one place: stdout is exactly
    one non-empty line, and that line parses as a JSON object."""
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    if len(lines) != 1:
        raise AssertionError(
            f"expected exactly one stdout line under --json; got "
            f"{len(lines)}:\n{stdout}")
    payload = json.loads(lines[0])
    if not isinstance(payload, dict):
        raise AssertionError(f"stdout line is not a JSON object: {lines[0]}")
    return payload


class UnlockJsonTest(unittest.TestCase):
    """`bale unlock --json`: one stdout JSON line, human trail on stderr."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-unlockjson-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack(self, *extra: str, slug: str = "unlockjson-a",
             include: str = "hello.txt"):
        return run_bale(
            self.install,
            [
                "pack", "unlock json test goal",
                "--slug", slug,
                "--include", include,
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
        self.assert_ok(result)
        sids = self.open_sids()
        self.assertTrue(sids, msg="pack succeeded but no session is open")
        return sids[-1]

    # -- pinned behavior 1: the session-close path -----------------------

    def test_close_path_emits_unlocked_contract(self) -> None:
        sid = self.packed_sid(self.pack())
        result = self.unlock("--json")
        self.assert_ok(result)

        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "unlocked")
        self.assertEqual(payload["sid"], sid)
        self.assertEqual(payload["closure_reason"], "abandoned")
        self.assertTrue(payload["session_dir_wiped"])
        self.assertFalse(payload["branch_preserved"])
        self.assertTrue(
            payload["telemetry"].startswith("claude/telemetry/"),
            msg="the machine-readable telemetry path is the point of "
                "the feature")
        self.assertTrue(payload["log"].endswith(f".bale/logs/{sid}.log"))
        # The v0.3.34 additive sweep key: null when [apply].sweep is
        # unset (this sandbox never sets it) — the additive-null
        # contract, same posture as apply's archive key.
        self.assertIsNone(payload["sweep"])
        # Stream discipline: the human trail moved to stderr, whole.
        self.assertIn("[bale]", result.stderr)
        self.assertIn("[UNLOCK]", result.stderr,
                      msg="the human summary block is the stderr "
                          "reference trail under json mode")
        # And the record it points at really exists.
        self.assertTrue((self.repo / payload["telemetry"]).is_file())

    # -- pinned behavior 2: the read-only inference rides the key --------

    def test_readonly_inference_in_json(self) -> None:
        self.packed_sid(self.pack("--read-only"))
        result = self.unlock("--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["closure_reason"], "closed-read-only")

    # -- pinned behavior 3: the benign no-op -----------------------------

    def test_noop_emits_no_op_outcome(self) -> None:
        result = self.unlock("--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "no-op")
        self.assertIsNone(payload["sid"])
        self.assertIsNone(payload["closure_reason"])
        self.assertIsNone(payload["debris"])
        self.assertIn("no open session", result.stderr,
                      msg="the human no-op line moved to stderr")

    # -- pinned behavior 4: the crash-debris sweep's no-op ---------------

    def test_noop_carries_debris_object(self) -> None:
        debris_sid = "2026-07-01-crashed-pack-001"
        bale_dir = self.repo / ".bale"
        bale_dir.mkdir()
        (bale_dir / "current_session").write_text(f"{debris_sid}\n")

        result = self.unlock("--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "no-op")
        self.assertIsNone(payload["sid"],
                          msg="the debris sid is not 'the' closed "
                              "session; it rides under debris")
        debris = payload["debris"]
        self.assertEqual(debris["sid"], debris_sid)
        self.assertTrue(debris["telemetry"].startswith("claude/telemetry/"))
        self.assertTrue((self.repo / debris["telemetry"]).is_file())
        # The debris record's own sweep rides under debris (v0.3.34),
        # not the top-level key; null here since [apply].sweep is unset.
        self.assertIsNone(debris["sweep"])
        self.assertIsNone(payload["sweep"],
                          msg="the no-op's only sweep is the debris "
                              "record's — the top-level key stays null")

    # -- pinned behavior 5: refusal paths stay fail()-shaped -------------

    def test_refusal_emits_nothing_on_stdout(self) -> None:
        """Two sessions open, no sid: the refusal exits through fail() —
        stderr, non-zero, nothing on stdout, like every other json
        surface's error paths. The second pack needs a scope-disjoint
        include (ADR-0007's pack-time gate refuses intersecting scopes),
        so a second committed file carries it."""
        env = git_env(self.home)
        (self.repo / "world.txt").write_text("world\n", encoding="utf-8")
        run_checked(["git", "add", "world.txt"], cwd=self.repo, env=env)
        run_checked(["git", "commit", "-m", "second file"],
                    cwd=self.repo, env=env)
        self.packed_sid(self.pack(slug="unlockjson-a"))
        self.packed_sid(self.pack(slug="unlockjson-b",
                                  include="world.txt"))
        result = self.unlock("--json")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertIn("sessions are open", result.stderr)

    # -- pinned behavior 6: --integration --json is refused --------------

    def test_integration_json_refused(self) -> None:
        result = self.unlock("--integration", "--json")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "")
        self.assertIn("session-shaped", result.stderr)

    # -- pinned behavior 7: human mode emits no JSON ---------------------

    def test_human_mode_emits_no_json(self) -> None:
        self.packed_sid(self.pack())
        result = self.unlock()
        self.assert_ok(result)
        self.assertNotIn('{"outcome"', result.stdout)
        self.assertIn("[UNLOCK]", result.stdout,
                      msg="the human block stays on stdout when the "
                          "stream swap never happens")


class UnlockIntegrationTest(unittest.TestCase):
    """`bale unlock --integration`: the clear path (board 35 gap 5)."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-unlockint-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.lock = self.repo / ".bale" / "integration.lock"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def unlock_integration(self):
        return run_bale(self.install, ["unlock", "--integration"],
                        cwd=self.repo, env=self.env)

    def test_integration_clear_path(self) -> None:
        """Subtests run in sequence against one repo: the not-held no-op
        first (nothing exists yet), then a well-formed lock cleared with
        the holder named, then an unparseable lock cleared rows-only."""
        holder_sid = "2026-07-30-integration-fixture-001"

        with self.subTest(variant="not held is a benign no-op"):
            result = self.unlock_integration()
            self.assertEqual(
                result.returncode, 0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            self.assertIn("integration lock is not held; nothing to unlock.",
                          result.stdout)

        with self.subTest(variant="held lock clears, holder named"):
            self.lock.parent.mkdir(parents=True, exist_ok=True)
            self.lock.write_text(json.dumps({
                "sid": holder_sid,
                "pid": 12345,
                "acquired_at": "2026-07-30T12:00:00+00:00",
            }) + "\n", encoding="utf-8")
            result = self.unlock_integration()
            self.assertEqual(
                result.returncode, 0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            self.assertFalse(self.lock.exists(),
                             msg="the clear path's one job")
            self.assertIn(f"cleared (was held by session {holder_sid}, "
                          f"pid 12345", result.stdout)
            self.assertIn("[UNLOCK]", result.stdout)
            self.assertIn(holder_sid, result.stdout)
            # The one caveat the summary insists on: only safe while no
            # apply is mid-integration.
            self.assertIn("Only clear this while no `bale apply` is "
                          "running", result.stdout)

        with self.subTest(variant="unparseable lock clears rows-only"):
            self.lock.write_text("not json{", encoding="utf-8")
            result = self.unlock_integration()
            self.assertEqual(
                result.returncode, 0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            self.assertFalse(self.lock.exists(),
                             msg="an unreadable lock is exactly the "
                                 "debris the command exists to clear")
            self.assertIn("holder unknown (unparseable lock file)",
                          result.stdout)
            self.assertNotIn("[UNLOCK]", result.stdout,
                             msg="no sid, no headline — rows-only degrade")


if __name__ == "__main__":
    unittest.main(verbosity=2)
