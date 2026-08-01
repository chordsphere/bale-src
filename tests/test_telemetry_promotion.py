#!/usr/bin/env python3
"""Hermetic E2E for the board 5 write-path promotion (v0.3.23).

Pins the D1 contract on the two promoted transient inputs:

- **Clarification stamp at close.** Every closing event stamps a
  bale-computed `clarification` summary — `{rounds, records[]}` read
  from `.bale/clarifications/<sid>/` at close time — onto its closing
  attempt, and `{rounds: 0, records: []}` when the directory is
  absent. Key presence with `rounds: 0` is *known zero*; key absence
  is *pre-epoch unknown* — the suite asserts the always-stamp rule on
  unlock closes across closure reasons (abandoned, closed-read-only,
  an explicit --reason), the per-record fields (n, at,
  blocking_questions), and the unreadable-record degradation
  (presence still counts as a round; only the question count goes
  null). The apply-close side of the stamp — and the closing-attempt-
  only rule — is pinned by the HOLD→retry E2E
  (tests/test_hold_retry_e2e.py), whose fixture drives real apply
  closes.
- **Bailout diagnostics embed.** The bailout close embeds the parsed,
  schema-validated diagnostics.json verbatim on the bailout attempt
  (symmetric with feedback), stamps the clarification summary like
  every closing event, and the bailout banner carries the same §8.9
  telemetry row every sibling terminal banner carries. The
  pre-existing failure paths — missing or invalid diagnostics.json —
  are unchanged: they exit through the rejected-attempt path (no
  bailout close, no embed, no stamp) and the session stays open.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_telemetry_promotion.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import tarfile
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
BAILOUT_HEADLINE = "[BAILOUT]"
MISSING_DIAG_MARKER = "missing diagnostics.json"
INVALID_DIAG_MARKER = "not valid JSON"

KNOWN_ZERO = {"rounds": 0, "records": []}


class TelemetryPromotionTest(unittest.TestCase):
    """Closing events stamp clarification; the bailout close embeds
    diagnostics and renders the telemetry row."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-promotion-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack(self, *extra: str, slug: str = "promo-a"):
        """A fully specified piped pack; extras append to the base form."""
        return run_bale(
            self.install,
            [
                "pack", "telemetry promotion test goal",
                "--slug", slug,
                "--include", "hello.txt",
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def assert_ok(self, result) -> None:
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

    def packed_sid(self, result) -> str:
        self.assert_ok(result)
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1, msg="expected exactly one open session")
        return sids[0]

    def seed_clarifications(self, sid: str, question_counts: list) -> None:
        """Write NNN.json clarification records, one per entry — each a
        minimal preserved manifest whose questions[] has the given
        length (only the list length is read by the stamp)."""
        clar_dir = self.repo / ".bale" / "clarifications" / sid
        clar_dir.mkdir(parents=True, exist_ok=True)
        for i, count in enumerate(question_counts, start=1):
            (clar_dir / f"{i:03d}.json").write_text(
                json.dumps({"questions": [
                    {"question": f"q{j}"} for j in range(count)
                ]}, indent=2) + "\n",
                encoding="utf-8",
            )

    def record_attempt(self, sid: str, index: int = -1) -> dict:
        p = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(p.is_file(), msg=f"expected telemetry record at {p}")
        record = json.loads(p.read_text(encoding="utf-8"))
        return record["attempts"][index]

    def build_bailout_tarball(self, sid: str, *,
                              diagnostics_body=None,
                              omit_diagnostics: bool = False) -> Path:
        """A minimal, fully valid bailout response per TARBALL.md §5.6.

        Empty change surfaces (the §5.6.2 shape validate_response_manifest
        enforces), a handoff.md with a real `## ` section, a
        schema-valid diagnostics.json — overridable to exercise the
        missing/invalid failure paths — and the no-op scripts the
        pre-flight requires of every response."""
        nnn = sid[-3:]
        rdir = self.tmp / f"response-{nnn}"
        rdir.mkdir()
        manifest = {
            "session_id": sid,
            "responds_to": sid,
            "corrects": None,
            "response_kind": "bailout",
            "summary": "bailout fixture: goal did not fit the budget",
            "changes": [],
            "deferred": [],
            "validation_will_run": [],
            "claims": {},
        }
        (rdir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (rdir / "handoff.md").write_text(
            "# Handoff\n\n## Original goal\n\ntelemetry promotion test goal\n",
            encoding="utf-8")
        if not omit_diagnostics:
            if diagnostics_body is None:
                diagnostics_body = json.dumps(self.valid_diagnostics(sid),
                                              indent=2) + "\n"
            (rdir / "diagnostics.json").write_text(diagnostics_body,
                                                   encoding="utf-8")
        noop = "#!/usr/bin/env bash\n# no-op (test fixture)\nexit 0\n"
        (rdir / "apply.sh").write_text(noop, encoding="utf-8")
        (rdir / "validation.sh").write_text(noop, encoding="utf-8")
        tarball = self.tmp / f"response-{nnn}.tar.gz"
        with tarfile.open(tarball, "w:gz") as tf:
            tf.add(str(rdir), arcname=f"response-{nnn}")
        return tarball

    @staticmethod
    def valid_diagnostics(sid: str) -> dict:
        """The universal envelope diagnostics.schema.json enforces."""
        return {
            "session_id": sid,
            "bail_trigger": "mid-build-budget-panic",
            "bail_narrative": "fixture narrative: the change set outgrew "
                              "the estimate mid-build.",
            "context_loaded": [
                {"path": "hello.txt", "verdict": "necessary", "note": ""},
            ],
            "exploration_paths": [
                {"what": "sized the change set", "verdict": "productive",
                 "note": ""},
            ],
            "tool_calls_summary": {"bash": 3},
            "what_would_save_next_time": ["split the goal at the seam"],
        }

    # -- clarification stamp on unlock closes ----------------------------

    def test_unlock_stamps_rounds_and_records(self) -> None:
        """A seeded clarification dir stamps rounds and per-record
        facts on the abandoned unlock close."""
        sid = self.packed_sid(self.pack())
        self.seed_clarifications(sid, [2, 3])
        self.assert_ok(run_bale(self.install, ["unlock", sid],
                                cwd=self.repo, env=self.env))
        attempt = self.record_attempt(sid)
        self.assertEqual(attempt["closure_reason"], "abandoned")
        clar = attempt["clarification"]
        self.assertEqual(clar["rounds"], 2)
        self.assertEqual([r["n"] for r in clar["records"]], [1, 2])
        self.assertEqual(
            [r["blocking_questions"] for r in clar["records"]], [2, 3])
        for r in clar["records"]:
            self.assertIsInstance(r["at"], str,
                                  msg="at is the record file's mtime, "
                                      "ISO 8601 UTC")

    def test_unlock_absent_dir_stamps_known_zero(self) -> None:
        """No clarification dir → the key is PRESENT with rounds 0:
        known zero, never conflated with pre-epoch absence."""
        sid = self.packed_sid(self.pack())
        self.assert_ok(run_bale(self.install, ["unlock", sid],
                                cwd=self.repo, env=self.env))
        attempt = self.record_attempt(sid)
        self.assertIn("clarification", attempt)
        self.assertEqual(attempt["clarification"], KNOWN_ZERO)

    def test_readonly_unlock_stamps(self) -> None:
        """The closed-read-only closure reason stamps like any other."""
        sid = self.packed_sid(self.pack("--read-only"))
        self.assert_ok(run_bale(self.install, ["unlock", sid],
                                cwd=self.repo, env=self.env))
        attempt = self.record_attempt(sid)
        self.assertEqual(attempt["closure_reason"], "closed-read-only")
        self.assertEqual(attempt["clarification"], KNOWN_ZERO)

    def test_explicit_reason_unlock_stamps_seeded_rounds(self) -> None:
        """An explicit --reason close carries the stamp too — the rule
        keys on the close, not on how the reason was chosen."""
        sid = self.packed_sid(self.pack())
        self.seed_clarifications(sid, [1])
        self.assert_ok(run_bale(
            self.install, ["unlock", sid, "--reason", "master-closeout"],
            cwd=self.repo, env=self.env))
        attempt = self.record_attempt(sid)
        self.assertEqual(attempt["closure_reason"], "master-closeout")
        self.assertEqual(attempt["clarification"]["rounds"], 1)

    def test_unreadable_record_counts_round_without_count(self) -> None:
        """A record that won't parse still counts as a round (the file
        is the suspension fact); only blocking_questions degrades."""
        sid = self.packed_sid(self.pack())
        clar_dir = self.repo / ".bale" / "clarifications" / sid
        clar_dir.mkdir(parents=True)
        (clar_dir / "001.json").write_text("{not json", encoding="utf-8")
        self.assert_ok(run_bale(self.install, ["unlock", sid],
                                cwd=self.repo, env=self.env))
        clar = self.record_attempt(sid)["clarification"]
        self.assertEqual(clar["rounds"], 1)
        self.assertIsNone(clar["records"][0]["blocking_questions"])

    # -- bailout: diagnostics embed, stamp, banner row -------------------

    def test_bailout_embeds_diagnostics_and_stamps(self) -> None:
        sid = self.packed_sid(self.pack(slug="promo-bail"))
        self.seed_clarifications(sid, [2])
        tarball = self.build_bailout_tarball(sid)
        result = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assert_ok(result)
        self.assertIn(BAILOUT_HEADLINE, result.stdout)
        self.assertIn(TELEMETRY_ROW_MARKER, result.stdout,
                      msg="the bailout banner carries the §8.9 telemetry "
                          "row its sibling banners carry")
        self.assertIn(RECORDED_MARKER, result.stdout)

        attempt = self.record_attempt(sid)
        self.assertEqual(attempt["outcome"], "bailout")
        self.assertEqual(attempt["diagnostics"], self.valid_diagnostics(sid),
                         msg="diagnostics.json content lands verbatim, "
                             "symmetric with feedback")
        self.assertEqual(attempt["clarification"]["rounds"], 1,
                         msg="a bailout is a closing event; it stamps")

    def test_missing_diagnostics_fails_before_close(self) -> None:
        sid = self.packed_sid(self.pack(slug="promo-miss"))
        tarball = self.build_bailout_tarball(sid, omit_diagnostics=True)
        result = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(MISSING_DIAG_MARKER, result.stdout + result.stderr)
        # Unchanged pre-existing behavior: the fail() exits through
        # cmd_apply's SystemExit wrapper, which records a REJECTED
        # attempt — never a bailout close, never an embed.
        attempt = self.record_attempt(sid)
        self.assertEqual(attempt["outcome"], "rejected")
        self.assertNotIn("diagnostics", attempt)
        self.assertNotIn("clarification", attempt,
                         msg="a rejection is not a closure; no stamp")
        self.assertTrue(
            (self.repo / ".bale" / "sessions" / sid / "open").is_file(),
            msg="the session stays open")

    def test_invalid_diagnostics_fails_before_close(self) -> None:
        sid = self.packed_sid(self.pack(slug="promo-bad"))
        tarball = self.build_bailout_tarball(sid,
                                             diagnostics_body="{not json")
        result = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(INVALID_DIAG_MARKER, result.stdout + result.stderr)
        # Same unchanged rejected-attempt path as the missing case.
        attempt = self.record_attempt(sid)
        self.assertEqual(attempt["outcome"], "rejected")
        self.assertNotIn("diagnostics", attempt)
        self.assertNotIn("clarification", attempt)
        self.assertTrue(
            (self.repo / ".bale" / "sessions" / sid / "open").is_file())

    # -- guard: the shipped schema carries the additive fields -----------

    def test_schema_gained_the_promoted_fields(self) -> None:
        schema = json.loads(
            (self.install / "schemas" / "telemetry-record.schema.json")
            .read_text(encoding="utf-8"))
        self.assertEqual(schema["properties"]["record_version"]["minimum"], 1,
                         msg="additive change; record_version stays 1")
        attempt_props = schema["properties"]["attempts"]["items"]["properties"]
        for field in ("diagnostics", "clarification", "superseded_by"):
            self.assertIn(field, attempt_props)


if __name__ == "__main__":
    unittest.main(verbosity=2)
