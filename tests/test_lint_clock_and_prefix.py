#!/usr/bin/env python3
"""Hermetic tests for tools/response_lint.py's two board-94 checks
(0.4.30): `context-prefix` and `dated-artifacts`, and the warning tier
they introduced.

TARBALL.md section 3.1: a request path context/<p> is the repo path
<p>; nothing in a response carries the prefix. Section 1: a session
dates what it writes from the session id, never from the date its
chat shows. The lint is the worker's pre-pack self-check, so both
traps are caught there:

- a `changes[]` path carrying `context/` is a finding (exit 1) — bale
  would land it at the wrong place;
- a `feedback.self_reported.docs_read` entry carrying it is a
  warning: reported, own `warnings[]` in the JSON report, never
  counted against `ok` or the exit code;
- a created .md carrying DOCS.md section 5's `- **Date:** YYYY-MM-DD`
  header must carry the sid's date (finding otherwise);
- a modified one is judged only for a dated line LATER than the sid's
  date (the planner's ruling: the header is byte-stable under the two
  sanctioned diff shapes, so an older date is original and an
  earlier-but-re-dated line is the doc-assertion's catch, not the
  lint's);
- the recognizer is content-keyed and path-agnostic.

Runs the lint as a subprocess against crafted-then-filled tempdir
response directories — no bale install, no tests/harness.py, stdlib
only, the pattern tests/test_response_lint.py set.

Run:  python3 -m unittest tests.test_lint_clock_and_prefix -v
  or: python3 -m unittest discover -s tests -p 'test_lint_clock_and_prefix.py'
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

SID = "2026-09-15-lint-clock-007"
SID_DATE = "2026-09-15"
YESTERDAY = "2026-09-14"   # the chat's date, one day behind UTC
TOMORROW = "2026-09-16"


def adr_text(date: str, extra_lines: tuple[str, ...] = ()) -> str:
    body = [
        "# ADR-0009: fixture decision",
        "",
        "- **Status:** Accepted",
        f"- **Date:** {date}",
        "- **Supersedes:** —",
        "- **Superseded by:** —",
        "",
        "## Context",
        "",
        "Fixture.",
        *extra_lines,
    ]
    return "\n".join(body) + "\n"


def run_lint(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(LINT), *argv],
                          capture_output=True, text=True)


class LintFixture(unittest.TestCase):
    """A crafted response dir whose files/ the test populates first."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.rdir = self.tmp / "response-007"
        (self.rdir / "files").mkdir(parents=True)

    def write(self, rel: str, text: str) -> None:
        dst = self.rdir / "files" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")

    def craft(self, actions: dict[str, str], *, sid: str = SID,
              path_rewrite: dict[str, str] | None = None,
              docs_read: list[str] | None = None) -> dict:
        """Scaffold with the crafter, then fill the judgment fields.
        `actions` maps repo path -> created|modified. `path_rewrite`
        lets a test ship a path spelled wrong on purpose (the crafter
        strips the mirror prefix correctly; the trap under test is a
        worker re-adding context/ by hand)."""
        cp = subprocess.run(
            [sys.executable, str(CRAFT), str(self.rdir), "--sid", sid,
             "--write"], capture_output=True, text=True)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        mpath = self.rdir / "manifest.json"
        manifest = json.loads(mpath.read_text())
        manifest["summary"] = "fixture response for the clock/prefix lint tests"
        for c in manifest["changes"]:
            c["action"] = actions.get(c["path"], "created")
            c["reason"] = "fixture file"
        if path_rewrite:
            for c in manifest["changes"]:
                if c["path"] in path_rewrite:
                    new = path_rewrite[c["path"]]
                    src = self.rdir / "files" / c["path"]
                    dst = self.rdir / "files" / new
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    src.rename(dst)
                    c["path"] = new
        manifest["validation_will_run"] = ["fixture assertion"]
        manifest["claims"] = {"fixture assertion": "pass"}
        if docs_read is not None:
            manifest["feedback"] = {
                "mechanical": {
                    "response_kind": "normal", "schema_valid": True,
                    "mirror_agreement": {"changes_to_files": True,
                                         "files_to_changes": True},
                    "claims_subset": True,
                },
                "self_reported": {
                    "assumptions": [], "judgment_calls": [],
                    "budget_pressure": "none", "includes_missing": [],
                    "docs_read": docs_read,
                    "compaction_occurred": {"occurred": False,
                                            "disclosure_ref": None},
                },
            }
        mpath.write_text(json.dumps(manifest, indent=2) + "\n")
        (self.rdir / "validation.sh").write_text(
            "#!/usr/bin/env bash\nexit 0\n")
        return manifest

    def lint_json(self, expect_exit: int) -> dict:
        cp = run_lint(str(self.rdir), "--json")
        self.assertEqual(cp.returncode, expect_exit,
                         f"stdout:\n{cp.stdout}\nstderr:\n{cp.stderr}")
        return json.loads(cp.stdout.strip().splitlines()[0])

    def codes(self, report: dict, tier: str = "findings") -> list[str]:
        return sorted(f["code"] for f in report[tier])

    def check_status(self, report: dict, check_id: str) -> str:
        return next(c["status"] for c in report["checks"]
                    if c["id"] == check_id)


class ContextPrefixCheck(LintFixture):
    def test_context_prefixed_changes_path_is_a_finding(self):
        self.write("src/new.txt", "hello\n")
        self.craft({}, path_rewrite={"src/new.txt": "context/src/new.txt"})
        report = self.lint_json(1)
        self.assertIn("CONTEXT_PREFIXED_PATH", self.codes(report))
        self.assertFalse(report["ok"])
        self.assertEqual(self.check_status(report, "context-prefix"), "fail")
        f = next(x for x in report["findings"]
                 if x["code"] == "CONTEXT_PREFIXED_PATH")
        self.assertEqual(f["path"], "context/src/new.txt")
        self.assertIn("'src/new.txt'", f["message"],
                      "the finding names the repo path the worker meant")

    def test_repo_relative_path_is_clean(self):
        self.write("src/new.txt", "hello\n")
        self.craft({})
        report = self.lint_json(0)
        self.assertTrue(report["ok"])
        self.assertEqual(self.check_status(report, "context-prefix"), "pass")
        self.assertEqual(report["warnings"], [])

    def test_context_prefixed_docs_read_is_a_warning_not_a_finding(self):
        self.write("src/new.txt", "hello\n")
        self.craft({}, docs_read=[
            "TARBALL.md sections 1, 2, 5, 7",
            "context/bin/bale (section 5), context/docs/CODE.md",
        ])
        report = self.lint_json(0)
        self.assertTrue(report["ok"], "a warning never flips ok")
        self.assertEqual(report["findings"], [])
        self.assertEqual(self.codes(report, "warnings"),
                         ["CONTEXT_PREFIXED_DOCS_READ"])
        self.assertEqual(report["warning_count"], 1)
        self.assertEqual(self.check_status(report, "context-prefix"), "warn")
        w = report["warnings"][0]
        self.assertEqual(w["severity"], "warning")
        self.assertTrue(w["path"].endswith("docs_read[1]"))
        self.assertIn("'context/bin/bale'", w["message"])
        self.assertIn("'context/docs/CODE.md'", w["message"])
        # feedback.mechanical still verifies: the warning does not
        # perturb the recomputed values.
        self.assertEqual(self.check_status(report, "feedback-block"), "pass")

    def test_human_report_renders_the_warn_tier(self):
        self.write("src/new.txt", "hello\n")
        self.craft({}, docs_read=["context/docs/TARBALL.md"])
        cp = run_lint(str(self.rdir))
        self.assertEqual(cp.returncode, 0, cp.stdout)
        self.assertIn("[WARN] context-prefix", cp.stdout)
        self.assertIn("~ CONTEXT_PREFIXED_DOCS_READ", cp.stdout)
        self.assertIn("result: CLEAN (1 warning(s), non-gating)", cp.stdout)


class DatedArtifactsCheck(LintFixture):
    def test_created_adr_dated_from_the_sid_is_clean(self):
        self.write("claude/context/adr/0009-fixture.md", adr_text(SID_DATE))
        self.craft({})
        report = self.lint_json(0)
        self.assertEqual(self.check_status(report, "dated-artifacts"), "pass")

    def test_created_adr_dated_from_the_chat_is_a_finding(self):
        self.write("claude/context/adr/0009-fixture.md", adr_text(YESTERDAY))
        self.craft({})
        report = self.lint_json(1)
        self.assertEqual(self.codes(report), ["WRONG_CLOCK_DATE"])
        f = report["findings"][0]
        self.assertEqual(f["path"], "claude/context/adr/0009-fixture.md")
        self.assertIn(SID_DATE, f["expected"])
        self.assertIn(YESTERDAY, f["got"])

    def test_recognizer_is_content_keyed_not_path_keyed(self):
        """A dated note anywhere in the tree is a dated artifact; an
        undated .md under adr/ is not."""
        self.write("docs/notes/landing.md", adr_text(YESTERDAY))
        self.write("claude/context/adr/0010-undated.md",
                   "# ADR-0010: no header\n\nProse only.\n")
        self.craft({})
        report = self.lint_json(1)
        self.assertEqual([f["path"] for f in report["findings"]],
                         ["docs/notes/landing.md"])

    def test_modified_adr_keeps_its_original_older_date(self):
        """A supersession stamp on an old ADR: header Date untouched
        and earlier than the sid — original by construction, clean."""
        old = adr_text("2026-05-12").replace(
            "- **Superseded by:** —", "- **Superseded by:** ADR-0011")
        self.write("claude/context/adr/0009-fixture.md", old)
        self.craft({"claude/context/adr/0009-fixture.md": "modified"})
        report = self.lint_json(0)
        self.assertEqual(self.check_status(report, "dated-artifacts"), "pass")

    def test_modified_adr_landing_note_from_the_future_is_a_finding(self):
        text = adr_text("2026-05-12", extra_lines=(
            "", f"- {TOMORROW}: landed in session {SID}"))
        self.write("claude/context/adr/0009-fixture.md", text)
        self.craft({"claude/context/adr/0009-fixture.md": "modified"})
        report = self.lint_json(1)
        self.assertEqual(self.codes(report), ["WRONG_CLOCK_DATE"])
        f = report["findings"][0]
        self.assertTrue(f["path"].startswith(
            "claude/context/adr/0009-fixture.md:"),
            "the finding names the line")
        self.assertIn(TOMORROW, f["got"])

    def test_modified_adr_landing_note_dated_from_the_sid_is_clean(self):
        text = adr_text("2026-05-12", extra_lines=(
            "", f"- {SID_DATE}: landed in session {SID}"))
        self.write("claude/context/adr/0009-fixture.md", text)
        self.craft({"claude/context/adr/0009-fixture.md": "modified"})
        report = self.lint_json(0)
        self.assertEqual(self.check_status(report, "dated-artifacts"), "pass")

    def test_modified_adr_earlier_landing_note_is_outside_reach(self):
        """Deliberately not the lint's catch: an earlier date on a
        modified artifact reads as original (no base bytes here); the
        crafter's ADR doc-assertion is the gate for a re-dated line."""
        text = adr_text("2026-05-12", extra_lines=(
            "", f"- {YESTERDAY}: landed in session {SID}"))
        self.write("claude/context/adr/0009-fixture.md", text)
        self.craft({"claude/context/adr/0009-fixture.md": "modified"})
        report = self.lint_json(0)
        self.assertEqual(self.check_status(report, "dated-artifacts"), "pass")

    def test_unparseable_sid_date_warns_and_does_not_run(self):
        self.write("claude/context/adr/0009-fixture.md", adr_text(YESTERDAY))
        self.craft({}, sid="not-a-dated-session-id-001")
        report = self.lint_json(0)
        self.assertEqual(self.codes(report, "warnings"),
                         ["SID_DATE_UNPARSEABLE"])
        self.assertEqual(self.check_status(report, "dated-artifacts"), "warn")
        self.assertEqual(report["findings"], [],
                         "the check did not run, and said so")


if __name__ == "__main__":
    unittest.main()
