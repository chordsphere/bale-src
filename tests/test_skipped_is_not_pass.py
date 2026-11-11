"""A pass claim beside a skipped or unrecorded verdict is a disagreement.

Session 2026-11-11-skipped-is-not-pass-001 (0.4.57), from two slips:

- a validation.sh whose every check skipped landed as PASS with claims of
  pass beside verdicts of skip, and nothing said so; a declared pass beside
  a skip is a disagreement, named at the walk and carried in the relay,
  with a line `N of M checks ran`;
- bale staged validation.sh without the session's notes.md, so a session
  could not check its own notes sections at apply.

What this suite pins:

1. The twin table. TARBALL.md 7.3's claim/verdict table, held twice on
   purpose: the crafter's epilogue (tools/craft_response.py, run inside a
   response's validation.sh) and bale's reading at apply
   (bale_report.claim_agreement). Both are driven over every row of one
   table, ``TABLE`` below, so neither can drift from the doc or from the
   other.
2. The summary bale builds from the manifest's claims and validation's
   output (bale_report.summarize_claimed_checks), its `N of M checks ran`
   line and its `disagree:` lines, in the planner relay blocks (applied and
   HOLD) and nowhere in the worker's block.
3. The notes placement (bale_staging.place_response_notes): byte for byte,
   absent when the response ships none, a stale copy removed, a symlink
   never followed.
4. End to end, one real pack and apply: a validation.sh made with this
   release's crafter, four claims (one ran, two skipped, one never
   recorded), and a check on `.bale-notes.md` from inside validation.sh.
   The apply still lands PASS (a disagreement is diagnostic, never a HOLD);
   the walk and the relay name each disagreeing check; the relay says
   `1 of 4 checks ran`; the telemetry record keeps the printed tag; and
   neither staged file reaches the session's commit.

Sandbox doctrine per ADR-0005 (fully hermetic): the shared harness in
tests/harness.py carries it.

Run directly::

    python3 tests/test_skipped_is_not_pass.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness import (
    REPO_ROOT,
    _load_module,
    bale_env,
    build_response_dir,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    tar_response_dir,
)

CRAFT = REPO_ROOT / "tools" / "craft_response.py"

# TARBALL.md 7.3's table, one row per (claim, verdict) pair, with the tag
# both twins must print. "missing" is the epilogue's word for a verdict
# never recorded. The fail-beside-skip and fail-beside-missing rows are the
# session's ruling (a deliberate failure that did not run is not the false
# PASS the slip names), flagged in its notes.md.
TABLE = [
    ("pass", "pass", "agree"),
    ("pass", "fail", "disagree"),
    ("pass", "skip", "disagree"),
    ("pass", "missing", "disagree"),
    ("fail", "fail", "agree"),
    ("fail", "pass", "disagree"),
    ("fail", "skip", "n/a"),
    ("fail", "missing", "n/a"),
    ("untested", "pass", "n/a"),
    ("untested", "fail", "n/a"),
    ("untested", "skip", "n/a"),
    ("untested", "missing", "n/a"),
    ("unknown", "pass", "n/a"),
    ("unknown", "fail", "n/a"),
    ("unknown", "skip", "n/a"),
    ("unknown", "missing", "n/a"),
]

PRINTED = {"agree": "[agree]", "disagree": "[DISAGREE]", "n/a": "[n/a]"}


def load_crafter():
    """tools/craft_response.py in-process (its main() is guarded)."""
    spec = importlib.util.spec_from_file_location(
        "craft_response_skipped_is_not_pass", CRAFT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def epilogue_definitions() -> str:
    """The definitions fragment exactly as a worker pastes it."""
    return load_crafter().build_validation_epilogue([], "definitions")


def run_epilogue(tmp: Path, claims: dict, verdicts: dict) -> str:
    """Run the crafter's epilogue in a scratch staging dir holding a
    .bale-manifest.json with `claims`, recording `verdicts`; return
    stdout. The exit code must stay 0: reconciliation never gates."""
    stage = Path(tempfile.mkdtemp(dir=tmp))
    (stage / ".bale-manifest.json").write_text(
        json.dumps({"claims": claims}), encoding="utf-8")
    body = ["#!/usr/bin/env bash", "set -euo pipefail", "exit_code=0",
            epilogue_definitions()]
    for label, verdict in verdicts.items():
        body.append(f'record_verdict "{label}" {verdict}')
    body += ["reconcile_claims", 'exit "$exit_code"', ""]
    script = stage / "validation.sh"
    script.write_text("\n".join(body), encoding="utf-8")
    run = subprocess.run(["bash", str(script)], cwd=stage,
                         capture_output=True, text=True, timeout=60)
    if run.returncode != 0:
        raise AssertionError(f"epilogue exited {run.returncode}:\n"
                             f"{run.stdout}\n{run.stderr}")
    return run.stdout


class TwinTableTest(unittest.TestCase):
    """The crafter and bale read TARBALL.md 7.3's table the same way."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.br = _load_module("bale_report")

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-skipnotpass-")
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_bale_reads_every_row(self) -> None:
        for claim, verdict, want in TABLE:
            with self.subTest(claim=claim, verdict=verdict):
                self.assertEqual(self.br.claim_agreement(claim, verdict),
                                 want)

    def test_crafter_prints_every_row(self) -> None:
        claims, verdicts = {}, {}
        for i, (claim, verdict, _) in enumerate(TABLE):
            label = f"row {i} {claim}-{verdict} check"
            claims[label] = claim
            if verdict != "missing":
                verdicts[label] = verdict
        out = run_epilogue(self.tmp, claims, verdicts)
        rows, parsed = self.br.parse_claim_verdict_block(out)
        self.assertTrue(parsed, msg=out)
        for i, (claim, verdict, want) in enumerate(TABLE):
            label = f"row {i} {claim}-{verdict} check"
            with self.subTest(label=label):
                self.assertEqual(rows[label],
                                 {"claim": claim, "verdict": verdict,
                                  "agreement": want}, msg=out)

    def test_brief_rows_print_in_the_pinned_shape(self) -> None:
        """The brief's two example rows, as the parser's regex and a
        reader both see them: two-space indent, name, colon, claim=,
        verdict=, bracketed tag, under the header."""
        out = run_epilogue(self.tmp,
                           {"eta-skipped check": "pass",
                            "theta-unrecorded check": "pass"},
                           {"eta-skipped check": "skip"})
        self.assertIn("claims vs verdict:\n", out)
        self.assertRegex(out, r"(?m)^  eta-skipped check:\s+claim=pass\s+"
                              r"verdict=skip\s+\[DISAGREE\]$")
        self.assertRegex(out, r"(?m)^  theta-unrecorded check:\s+claim=pass"
                              r"\s+verdict=missing\s+\[DISAGREE\]$")

    def test_annotated_claim_reads_its_value(self) -> None:
        out = run_epilogue(
            self.tmp,
            {"kappa check": {"value": "pass", "claim_basis": "predicted"}},
            {"kappa check": "skip"})
        self.assertRegex(out, r"kappa check:\s+claim=pass\s+verdict=skip"
                              r"\s+\[DISAGREE\]")
        self.assertEqual(self.br.claim_value(
            {"value": "pass", "claim_basis": "observed"}), "pass")
        self.assertEqual(self.br.claim_value("fail"), "fail")

    def test_the_tag_vocabulary_is_unchanged(self) -> None:
        """No new tag: only [agree], [DISAGREE] and [n/a] appear in the
        epilogue's rule."""
        defs = epilogue_definitions()
        rule = defs[defs.index("verdict = verdicts.get"):
                    defs.index("name = check")]
        import re
        self.assertEqual(set(re.findall(r'"\[[^\]]+\]"', rule)),
                         {'"[agree]"', '"[DISAGREE]"', '"[n/a]"'})


class ClaimsSummaryTest(unittest.TestCase):
    """summarize_claimed_checks and the lines built from it."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.br = _load_module("bale_report")

    BLOCK = (
        "[PASS] alpha\n"
        "[SKIP] eta: tool not found\n"
        "claims vs verdict:\n"
        "  alpha check:            claim=pass      verdict=pass     [agree]\n"
        "  eta-skipped check:      claim=pass      verdict=skip     "
        "[DISAGREE]\n"
        "  iota-skipped check:     claim=pass      verdict=skip     "
        "[DISAGREE]\n"
        "  theta-unrecorded check: claim=pass      verdict=missing  "
        "[DISAGREE]\n")
    CLAIMS = {"alpha check": "pass", "eta-skipped check": "pass",
              "iota-skipped check": "pass", "theta-unrecorded check": "pass"}

    def summary(self, claims=None, output=None):
        return self.br.summarize_claimed_checks(
            self.CLAIMS if claims is None else claims,
            self.BLOCK if output is None else output)

    def test_the_brief_example_reads_1_of_4(self) -> None:
        s = self.summary()
        self.assertEqual((s["claimed"], s["ran"], s["parsed"]), (4, 1, True))
        line = self.br.format_claims_ran_line(s)
        self.assertIn("1 of 4 checks ran", line)
        self.assertEqual([c["check"] for c in s["disagreements"]],
                         ["eta-skipped check", "iota-skipped check",
                          "theta-unrecorded check"])

    def test_each_disagreement_line_names_the_key_verbatim(self) -> None:
        lines = self.br.format_disagreement_lines(self.summary())
        self.assertEqual(len(lines), 3)
        for key, line in zip(["eta-skipped check", "iota-skipped check",
                              "theta-unrecorded check"], lines):
            self.assertTrue(line.startswith(f"disagree: {key} ("), line)
        self.assertIn("verdict=missing", lines[2])

    def test_a_fail_counts_as_ran(self) -> None:
        out = ("claims vs verdict:\n"
               "  a: claim=pass verdict=fail [DISAGREE]\n"
               "  b: claim=fail verdict=fail [agree]\n"
               "  c: claim=fail verdict=skip [n/a]\n")
        s = self.summary({"a": "pass", "b": "fail", "c": "fail"}, out)
        self.assertEqual(s["ran"], 2)
        self.assertIn("2 of 3 checks ran",
                      self.br.format_claims_ran_line(s))
        self.assertEqual([c["check"] for c in s["disagreements"]], ["a"])

    def test_a_claimed_check_with_no_row_is_never_recorded(self) -> None:
        out = "claims vs verdict:\n  a: claim=pass verdict=pass [agree]\n"
        s = self.summary({"a": "pass", "b": "pass"}, out)
        self.assertEqual(s["ran"], 1)
        (b,) = s["disagreements"]
        self.assertEqual((b["check"], b["verdict"], b["has_row"]),
                         ("b", "missing", False))
        self.assertIn("no row in the claims block",
                      self.br.format_disagreement_lines(s)[0])

    def test_an_older_crafters_na_still_reads_as_a_disagreement(self) -> None:
        """A validation.sh pasted from a pre-0.4.57 crafter prints [n/a]
        beside a pass and a skip; bale derives the disagreement anyway and
        says what the script printed."""
        out = "claims vs verdict:\n  a: claim=pass verdict=skip [n/a]\n"
        s = self.summary({"a": "pass"}, out)
        (a,) = s["disagreements"]
        self.assertEqual(a["printed"], "n/a")
        self.assertIn("validation.sh tagged it [n/a]",
                      self.br.format_disagreement_lines(s)[0])

    def test_a_printed_disagree_is_never_downgraded(self) -> None:
        out = "claims vs verdict:\n  a: claim=fail verdict=skip [DISAGREE]\n"
        s = self.summary({"a": "fail"}, out)
        self.assertEqual([c["check"] for c in s["disagreements"]], ["a"])

    def test_no_block_names_nothing_and_says_unknown(self) -> None:
        s = self.summary(output="[PASS] alpha\n")
        self.assertIsNone(s["ran"])
        self.assertEqual(s["disagreements"], [])
        line = self.br.format_claims_ran_line(s)
        self.assertIn("printed no claims vs verdict block", line)
        self.assertIn("4 claimed checks", line)
        self.assertIn("unknown", line)

    def test_no_claims_reads_0_of_0(self) -> None:
        s = self.summary(claims={}, output="")
        self.assertEqual(self.br.format_claims_ran_line(s),
                         "claimed checks: 0 of 0 checks ran (the manifest "
                         "claims no checks)")

    def test_the_record_keeps_the_printed_tag(self) -> None:
        """parse_claim_verdict_block, the telemetry promotion's reader, is
        unchanged: agreement is what validation.sh printed."""
        out = "claims vs verdict:\n  a: claim=pass verdict=skip [n/a]\n"
        rows, parsed = self.br.parse_claim_verdict_block(out)
        self.assertTrue(parsed)
        self.assertEqual(rows["a"]["agreement"], "n/a")


class RelayRowsTest(unittest.TestCase):
    """The planner blocks carry the rows; the worker block never does."""

    SID = "2026-11-11-relayrows-001"

    @classmethod
    def setUpClass(cls) -> None:
        cls.br = _load_module("bale_report")

    def summary(self):
        return self.br.summarize_claimed_checks(
            ClaimsSummaryTest.CLAIMS, ClaimsSummaryTest.BLOCK)

    def cp(self, exit_code: int = 0) -> dict:
        return {"configured": True, "state": "PASS" if exit_code == 0
                else "HOLD", "exit_code": exit_code,
                "script": {"path": "claude/checkpoints/x.sh",
                           "sha256": "0" * 64},
                "stamp_matched": True, "failed_probes": []}

    def assert_rows(self, block: str) -> None:
        lines = block.splitlines()
        ran = [ln for ln in lines if "1 of 4 checks ran" in ln]
        self.assertEqual(len(ran), 1, msg=block)
        for key in ("eta-skipped check", "iota-skipped check",
                    "theta-unrecorded check"):
            hits = [ln for ln in lines
                    if key in ln and "disagree" in ln.lower()]
            self.assertEqual(len(hits), 1, msg=f"{key} in\n{block}")
        self.assertFalse([ln for ln in lines if "alpha check" in ln
                          and "disagree" in ln.lower()], msg=block)

    def test_applied_relay(self) -> None:
        block = self.br.format_apply_relay_planner(
            sid=self.SID, origin_branch="main", exit_code=0,
            checkpoint=self.cp(), notes="# notes\n", admissions={},
            claims_summary=self.summary())
        self.assert_rows(block)
        self.assertIn(f"APPLIED — session {self.SID}", block)
        # The rows sit after the admissions and before notes.md.
        self.assertLess(block.index("admissions: none"),
                        block.index("1 of 4 checks ran"))
        self.assertLess(block.index("1 of 4 checks ran"),
                        block.index("--- notes.md ---"))

    def test_hold_relay_planner_and_worker(self) -> None:
        blocks = self.br.format_hold_relay_blocks(
            sid=self.SID, exit_code=1, checkpoint=None,
            worker_output="[FAIL] x\n", held_tarball="/t/r.tar.gz",
            bands={"worker": "[FAIL] x\n"}, admissions={},
            claims_summary=self.summary())
        by = {("planner" if "to planner ===" in b.splitlines()[0]
               else "worker"): b for b in blocks}
        self.assert_rows(by["planner"])
        self.assertNotIn("checks ran", by["worker"])
        lines = by["planner"].splitlines()
        held = lines.index("held tarball: /t/r.tar.gz")
        self.assertEqual(lines[held + 1], "admissions: none",
                         msg="the admissions line still follows held "
                             "tarball directly")

    def test_walk_fallback_prints_an_annotated_claims_word(self) -> None:
        """With claims but no block, the walk keeps the claim-only table;
        an annotated claim prints its word there, not the object."""
        import inspect
        src = inspect.getsource(self.br.format_walkthrough_summary)
        self.assertIn("claim={claim_value(claim)}", src)
        self.assertNotIn('claim={claim}")', src)

    def test_none_renders_nothing(self) -> None:
        kw = dict(sid=self.SID, origin_branch="main", exit_code=0,
                  checkpoint=None, notes=None, admissions={})
        self.assertEqual(
            self.br.format_apply_relay_planner(**kw),
            self.br.format_apply_relay_planner(**kw, claims_summary=None))
        self.assertNotIn("checks ran",
                         self.br.format_apply_relay_planner(**kw))
        self.assertEqual(self.br.claims_relay_rows(None), [])


class NotesPlacementTest(unittest.TestCase):
    """bale_staging.place_response_notes."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.bs = _load_module("bale_staging")

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-notesplace-")
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.rdir = self.tmp / "response-001"
        self.rdir.mkdir()
        self.stage = self.tmp / "staging"
        self.stage.mkdir()

    def test_the_name(self) -> None:
        self.assertEqual(self.bs.STAGED_NOTES_NAME, ".bale-notes.md")

    def test_byte_for_byte(self) -> None:
        data = "# Notes\r\n\nno trailing newline, a tab\t, ü".encode("utf-8")
        (self.rdir / "notes.md").write_bytes(data)
        path, msg = self.bs.place_response_notes(self.rdir, self.stage)
        self.assertEqual(path, self.stage / ".bale-notes.md")
        self.assertEqual(path.read_bytes(), data)
        self.assertIn("placed", msg)

    def test_absent_when_none_ships_and_stale_copy_removed(self) -> None:
        (self.stage / ".bale-notes.md").write_text("an earlier attempt's\n")
        path, msg = self.bs.place_response_notes(self.rdir, self.stage)
        self.assertIsNone(path)
        self.assertFalse(os.path.lexists(self.stage / ".bale-notes.md"))
        self.assertIn("ships no notes.md", msg)

    def test_a_symlinked_notes_is_not_followed(self) -> None:
        secret = self.tmp / "outside.txt"
        secret.write_text("not the response's\n")
        (self.rdir / "notes.md").symlink_to(secret)
        path, msg = self.bs.place_response_notes(self.rdir, self.stage)
        self.assertIsNone(path)
        self.assertFalse(os.path.lexists(self.stage / ".bale-notes.md"))
        self.assertIn("not a regular file", msg)


class SkippedIsNotPassE2ETest(unittest.TestCase):
    """One real pack and apply, the brief's example made concrete."""

    NOTES = ("# Notes\n\nA pass claim beside a skip.\n\n"
             "## Structure\n\n- title: t\n- size: small\n- goal: g\n")

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-skipnotpass-")
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def pack(self, slug: str) -> str:
        r = run_bale(self.install,
                     ["pack", f"{slug} goal: rewrite hello.txt",
                      "--slug", slug, "--include", "hello.txt",
                      "--no-readme"], cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        return sids[0]

    def validation_sh(self, notes_sha: str) -> str:
        """Four claimed checks: the notes check runs (and checks
        .bale-notes.md against the shipped notes' hash), two skip, and
        one never records a verdict."""
        expect = ("[ ! -e .bale-notes.md ]" if not notes_sha else
                  f'[ "$(sha256sum .bale-notes.md | cut -d" " -f1)" = '
                  f'"{notes_sha}" ] && [ -f .bale-manifest.json ]')
        return "\n".join([
            "#!/usr/bin/env bash",
            "set -uo pipefail",
            "exit_code=0",
            epilogue_definitions(),
            f"if {expect}; then",
            '  echo "[PASS] notes beside manifest"',
            '  record_verdict "notes beside manifest" pass',
            "else",
            '  echo "[FAIL] notes beside manifest"',
            '  record_verdict "notes beside manifest" fail',
            "  exit_code=1",
            "fi",
            'echo "[SKIP] eta-skipped check: no node_modules"',
            'record_verdict "eta-skipped check" skip',
            'echo "[SKIP] iota-skipped check: no node_modules"',
            'record_verdict "iota-skipped check" skip',
            "reconcile_claims",
            'exit "$exit_code"',
            ""])

    def response(self, sid: str, *, notes: str | None) -> Path:
        notes_sha = (hashlib.sha256(notes.encode("utf-8")).hexdigest()
                     if notes is not None else "")
        checks = ["notes beside manifest", "eta-skipped check",
                  "iota-skipped check", "theta-unrecorded check"]
        rdir = build_response_dir(
            self.tmp / "resp", sid, summary="skipped-is-not-pass fixture",
            entries=[{"path": "hello.txt", "action": "modified",
                      "reason": "the fixture's rewrite",
                      "data": b"rewritten\n"}],
            validation_sh=self.validation_sh(notes_sha),
            validation_will_run=checks,
            claims={c: "pass" for c in checks})
        if notes is not None:
            (rdir / "notes.md").write_text(notes, encoding="utf-8")
        return tar_response_dir(rdir)

    def relay(self, stdout: str, sid: str) -> str:
        begin = f"=== RELAY BEGIN {sid} to planner ==="
        end = f"=== RELAY END {sid} to planner ==="
        lines = stdout.splitlines()
        self.assertEqual(lines.count(begin), 1, msg=stdout)
        return "\n".join(lines[lines.index(begin):lines.index(end) + 1])

    def test_lands_pass_names_disagreements_and_counts(self) -> None:
        sid = self.pack("skipnotpass")
        r = run_bale(self.install,
                     ["apply", str(self.response(sid, notes=self.NOTES)),
                      "--no-interact"], cwd=self.repo, env=self.env)
        out = r.stdout
        # Diagnostic, not a HOLD: validation exited 0, so it lands PASS.
        self.assertEqual(r.returncode, 0, msg=out + r.stderr)
        self.assertIn(f"[PASS] {sid}", out)

        relay = self.relay(out, sid)
        self.assertIn("1 of 4 checks ran", relay)
        walk = out[:out.index(f"=== RELAY BEGIN {sid} to planner ===")]
        for key in ("eta-skipped check", "iota-skipped check",
                    "theta-unrecorded check"):
            for where, text in (("walk", walk), ("relay", relay)):
                with self.subTest(key=key, where=where):
                    self.assertTrue(
                        [ln for ln in text.splitlines()
                         if key in ln and "disagree" in ln.lower()],
                        msg=text)
        self.assertFalse([ln for ln in relay.splitlines()
                          if "notes beside manifest" in ln
                          and "disagree" in ln.lower()], msg=relay)
        self.assertIn("1 of 4 checks ran", walk)
        self.assertIn("3 claim/verdict disagreement(s)", walk)

        # The record keeps the printed tag, the new crafter's [DISAGREE].
        rec = json.loads((self.repo / "claude" / "telemetry"
                          / f"{sid}.json").read_text(encoding="utf-8"))
        cv = rec["attempts"][-1]["validation"]["claim_verdict"]
        self.assertEqual(cv["eta-skipped check"],
                         {"claim": "pass", "verdict": "skip",
                          "agreement": "disagree"})
        self.assertEqual(cv["theta-unrecorded check"]["verdict"], "missing")
        self.assertEqual(cv["notes beside manifest"]["agreement"], "agree")

        # Neither staged file reaches the session's commit or main.
        tree = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", f"applied/{sid}"],
            cwd=self.repo, env=git_env(self.home), capture_output=True,
            text=True, check=True).stdout.split()
        self.assertNotIn(".bale-notes.md", tree)
        self.assertNotIn(".bale-manifest.json", tree)
        log = (self.repo / ".bale" / "logs" / f"{sid}.log").read_text(
            encoding="utf-8")
        self.assertIn("[PASS] notes beside manifest", log)

    def test_no_notes_means_no_staged_notes(self) -> None:
        sid = self.pack("skipnonotes")
        r = run_bale(self.install,
                     ["apply", str(self.response(sid, notes=None)),
                      "--no-interact"], cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        log = (self.repo / ".bale" / "logs" / f"{sid}.log").read_text(
            encoding="utf-8")
        self.assertIn("[PASS] notes beside manifest", log)
        self.assertIn("ships no notes.md", log)


if __name__ == "__main__":
    unittest.main(verbosity=2)
