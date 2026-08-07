#!/usr/bin/env python3
"""Hermetic HOLD→retry multi-attempt E2E (board 5 D7.4; session 25's
deferred fixture).

Drives the full write path the ledger reads: `bale pack` → `bale apply`
of a response whose validation.sh fails (piped default: HOLD/inspect) →
`bale retry` with a corrected response (piped default: PASS/merge), and
asserts the one-file-per-sid append semantics BALE.md §8.9 promises:

- the HOLD attempt and the applied attempt accumulate in the SAME
  record, in order, each carrying its own validation state/exit;
- the envelope mirrors the latest attempt (`outcome`, `updated_at`)
  while `created_at` is preserved from the first;
- the close-time clarification stamp (v0.3.23, board 5 D1) lands on
  the CLOSING attempt only — the applied attempt carries the
  known-zero `{rounds: 0, records: []}`, the held attempt carries no
  key at all;
- the merge really landed: `applied/<sid>` tag, changed file content
  on the origin branch.

The response tarballs are built via the shared harness fixture builder
(computed hashes, real validation.sh scripts; extracted to
``tests/harness.py`` at board 35) so the failure and the fix are
exactly one exit-code apart — the ADR-0002 oracle is the documented record shape,
never a golden byte comparison.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_hold_retry_e2e.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harness import (
    bale_env,
    build_response_dir,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_checked,
    tar_response_dir,
)

# Sentinels for the surfaces this file pins.
HOLD_HEADLINE = "[HOLD]"
PASS_HEADLINE = "[PASS]"
RECORDED_MARKER = "recorded claude/telemetry/"

KNOWN_ZERO = {"rounds": 0, "records": []}

NEW_CONTENT = "hello from the corrected response\n"


class HoldRetryE2ETest(unittest.TestCase):
    """apply HOLD → retry PASS appends attempts[] and mirrors the
    envelope; the clarification stamp sits on the closing attempt only."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-holdretry-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def packed_sid(self) -> str:
        result = run_bale(
            self.install,
            [
                "pack", "hold-retry e2e goal: rewrite hello.txt",
                "--slug", "hold-retry",
                "--include", "hello.txt",
                "--no-readme",
            ],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        return sids[0]

    def build_response_tarball(self, sid: str, *, name: str,
                               validation_exit: int) -> Path:
        """A valid normal response modifying hello.txt (in scope), whose
        validation.sh exits `validation_exit` — 1 drives the HOLD, 0
        the retry's PASS. Built via the shared harness builder (board
        35 extraction), which computes sizes and hashes from the bytes
        it writes — never transcribed."""
        verdict = "FAIL" if validation_exit else "PASS"
        rdir = build_response_dir(
            self.tmp / name, sid,
            summary="hold-retry fixture: rewrite hello.txt; the first "
                    "attempt's validation fails by construction",
            entries=[{
                "path": "hello.txt",
                "action": "modified",
                "reason": "the goal's rewrite; identical bytes on both "
                          "attempts so only the validation verdict differs",
                "data": NEW_CONTENT.encode("utf-8"),
            }],
            validation_sh=(
                "#!/usr/bin/env bash\n"
                f"echo \"[{verdict}] fixture check\"\n"
                f"exit {validation_exit}\n"),
        )
        return tar_response_dir(rdir)

    def telemetry_record(self, sid: str) -> dict:
        p = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(p.is_file(), msg=f"expected telemetry record at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    # -- the E2E ---------------------------------------------------------

    def test_hold_then_retry_appends_and_mirrors(self) -> None:
        sid = self.packed_sid()

        # Attempt 1: validation fails → piped default is inspect → HOLD.
        holding = self.build_response_tarball(sid, name="first",
                                              validation_exit=1)
        held = run_bale(self.install, ["apply", str(holding)],
                        cwd=self.repo, env=self.env)
        self.assertEqual(held.returncode, 1,
                         msg=f"stdout:\n{held.stdout}\nstderr:\n{held.stderr}")
        self.assertIn(HOLD_HEADLINE, held.stdout)
        self.assertIn(RECORDED_MARKER, held.stdout)

        record = self.telemetry_record(sid)
        self.assertEqual(record["outcome"], "held")
        self.assertEqual(len(record["attempts"]), 1)
        created_at = record["created_at"]

        # Attempt 2: corrected response → retry → PASS → piped merge.
        fixed = self.build_response_tarball(sid, name="second",
                                            validation_exit=0)
        merged = run_bale(self.install, ["retry", str(fixed)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            merged.returncode, 0,
            msg=f"stdout:\n{merged.stdout}\nstderr:\n{merged.stderr}")
        self.assertIn(PASS_HEADLINE, merged.stdout)

        # One file per sid; the retry APPENDED.
        record = self.telemetry_record(sid)
        self.assertEqual(len(record["attempts"]), 2,
                         msg="HOLD then retry accumulates both attempts")
        held_attempt, applied_attempt = record["attempts"]

        self.assertEqual(held_attempt["outcome"], "held")
        self.assertEqual(held_attempt["command"], "apply")
        self.assertEqual(held_attempt["validation"]["state"], "HOLD")
        self.assertEqual(held_attempt["validation"]["exit_code"], 1)

        self.assertEqual(applied_attempt["outcome"], "applied")
        self.assertEqual(applied_attempt["command"], "retry")
        self.assertEqual(applied_attempt["validation"]["state"], "PASS")
        self.assertEqual(applied_attempt["validation"]["exit_code"], 0)

        # Envelope mirroring (§8.9): outcome/updated_at track the latest
        # attempt; created_at is preserved from the first.
        self.assertEqual(record["outcome"], "applied")
        self.assertEqual(record["updated_at"], applied_attempt["at"])
        self.assertEqual(record["created_at"], created_at)

        # The clarification stamp (board 5 D1) sits on the CLOSING
        # attempt only: known-zero on the applied close, no key at all
        # on the held attempt.
        self.assertNotIn("clarification", held_attempt,
                         msg="a HOLD is not a closure; no stamp")
        self.assertEqual(applied_attempt["clarification"], KNOWN_ZERO)

        # The merge really landed.
        env = git_env(self.home)
        run_checked(["git", "rev-parse", "--verify",
                     f"refs/tags/applied/{sid}"], cwd=self.repo, env=env)
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            NEW_CONTENT)


if __name__ == "__main__":
    unittest.main(verbosity=2)
