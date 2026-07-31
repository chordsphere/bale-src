#!/usr/bin/env python3
"""Hermetic tests for tools/response_lint.py's --emit-feedback-mechanical
flag (session 008, board 31).

The flag prints the paste-ready feedback.mechanical object — the
TARBALL.md 5.2.2 fill-by-running-the-lint workflow, mechanized. The
session's evidence-16 disposition under test: every emitted field is
the lint run's OWN computation (the same derivation the feedback-block
check verifies a shipped block against), the two self-reported optional
members (linkage, provenance) are never emitted, and the pre-existing
mismatch re-check still guards a stale paste.

Runs the lint as a subprocess against crafted-then-filled tempdir
response directories — no bale install, no tests/harness.py, stdlib
only (the crafter builds the fixtures the way a worker would).

Run:  python3 -m unittest tests.test_response_lint -v
  or: python3 -m unittest discover -s tests -p 'test_response_lint.py'
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CRAFT = REPO / "tools" / "craft_response.py"
LINT = REPO / "tools" / "response_lint.py"

MECHANICAL_KEYS = {"response_kind", "schema_valid", "mirror_agreement",
                   "claims_subset"}


def run_lint(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LINT), *argv],
        capture_output=True, text=True,
    )


class EmitFeedbackMechanical(unittest.TestCase):
    SID = "2026-07-31-lint-fixture-042"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.rdir = self.tmp / "response-042"
        self.body = b"fixture content\n"
        dst = self.rdir / "files" / "src" / "new.txt"
        dst.parent.mkdir(parents=True)
        dst.write_bytes(self.body)
        cp = subprocess.run(
            [sys.executable, str(CRAFT), str(self.rdir),
             "--sid", self.SID, "--write"],
            capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.fill_manifest()
        (self.rdir / "validation.sh").write_text(
            "#!/usr/bin/env bash\nexit 0\n")

    def fill_manifest(self, **overrides):
        mpath = self.rdir / "manifest.json"
        manifest = json.loads(mpath.read_text())
        manifest["summary"] = "fixture response for the emit-feedback tests"
        for c in manifest["changes"]:
            c["action"] = "created"
            c["reason"] = "fixture file"
        manifest["validation_will_run"] = ["fixture assertion"]
        manifest["claims"] = {"fixture assertion": "pass"}
        manifest.update(overrides)
        mpath.write_text(json.dumps(manifest, indent=2) + "\n")
        return manifest

    def emit(self, expect_exit: int = 0) -> tuple[dict | None, str]:
        cp = run_lint(str(self.rdir), "--emit-feedback-mechanical")
        self.assertEqual(cp.returncode, expect_exit,
                         f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        obj = json.loads(cp.stdout) if cp.stdout.strip() else None
        return obj, cp.stderr

    def test_clean_emission_shape_and_values(self):
        mech, stderr = self.emit()
        self.assertEqual(set(mech), MECHANICAL_KEYS,
                         "the emission carries exactly the four "
                         "lint-computable fields — linkage and provenance "
                         "are self-reported, never emitted")
        self.assertEqual(mech["response_kind"], "normal")
        self.assertTrue(mech["schema_valid"])
        self.assertEqual(mech["mirror_agreement"],
                         {"changes_to_files": True,
                          "files_to_changes": True})
        self.assertTrue(mech["claims_subset"])
        # Human report moved to stderr; stdout is the object alone.
        self.assertIn("result: CLEAN", stderr)

    def test_round_trip_pastes_clean(self):
        """The 5.2.2 workflow end to end: emit, paste, fill
        self_reported, re-lint clean."""
        mech, _ = self.emit()
        self.fill_manifest(feedback={
            "mechanical": mech,
            "self_reported": {
                "assumptions": [],
                "judgment_calls": [],
                "budget_pressure": "none",
                "includes_missing": [],
                "compaction_occurred": {"occurred": False,
                                        "disclosure_ref": None},
            },
        })
        cp = run_lint(str(self.rdir))
        self.assertEqual(cp.returncode, 0,
                         f"pasted emission must lint clean:\n{cp.stdout}")

    def test_emission_reflects_findings_not_hopes(self):
        """A degraded mirror degrades the emitted values: the flag
        prints what this run computed, never a transcription."""
        (self.rdir / "files" / "src" / "new.txt").write_bytes(
            b"tampered after the manifest was computed\n")
        mech, _ = self.emit(expect_exit=1)
        self.assertFalse(mech["mirror_agreement"]["changes_to_files"])
        self.assertTrue(mech["mirror_agreement"]["files_to_changes"])
        self.assertTrue(mech["schema_valid"])

    def test_stale_paste_still_flagged(self):
        """The mismatch re-check is unchanged: a block pasted before an
        edit is named FEEDBACK_MECHANICAL_MISMATCH on the next run."""
        mech, _ = self.emit()
        self.fill_manifest(feedback={
            "mechanical": mech,
            "self_reported": {
                "assumptions": [],
                "judgment_calls": [],
                "budget_pressure": "none",
                "includes_missing": [],
                "compaction_occurred": {"occurred": False,
                                        "disclosure_ref": None},
            },
        })
        # The edit after the paste: the mirror no longer matches.
        (self.rdir / "files" / "src" / "new.txt").write_bytes(
            b"edited after the block was pasted\n")
        cp = run_lint(str(self.rdir))
        self.assertEqual(cp.returncode, 1)
        self.assertIn("FEEDBACK_MECHANICAL_MISMATCH", cp.stdout)

    def test_emission_and_check_share_one_derivation(self):
        """Paste this run's emission verbatim, change nothing, and the
        feedback-block check must agree with it even while other
        findings exist — the emission and the verification come from
        the same derivation, so they cannot disagree."""
        (self.rdir / "files" / "src" / "new.txt").write_bytes(
            b"tampered after the manifest was computed\n")
        mech, _ = self.emit(expect_exit=1)
        self.fill_manifest(feedback={
            "mechanical": mech,
            "self_reported": {
                "assumptions": [],
                "judgment_calls": [],
                "budget_pressure": "none",
                "includes_missing": [],
                "compaction_occurred": {"occurred": False,
                                        "disclosure_ref": None},
            },
        })
        cp = run_lint(str(self.rdir))
        self.assertEqual(cp.returncode, 1)  # the mirror finding remains
        self.assertNotIn("FEEDBACK_MECHANICAL_MISMATCH", cp.stdout,
                         "a verbatim paste of this run's own emission "
                         "must never mismatch")

    def test_mutually_exclusive_with_json(self):
        cp = run_lint(str(self.rdir), "--emit-feedback-mechanical",
                      "--json")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("--json", cp.stderr)

    def test_unparseable_manifest_emits_nothing(self):
        (self.rdir / "manifest.json").write_text("{not json")
        cp = run_lint(str(self.rdir), "--emit-feedback-mechanical")
        self.assertEqual(cp.returncode, 1)
        self.assertEqual(cp.stdout.strip(), "",
                         "no honest object exists without a manifest")
        self.assertIn("cannot emit feedback.mechanical", cp.stderr)


if __name__ == "__main__":
    unittest.main()
