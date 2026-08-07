#!/usr/bin/env python3
"""The ledger's forecast side (ADR-0015, board 13 session B, v0.4.2).

Three suites, unit-first:

- **ContainmentMirrorTest** pins ``bale_stats``'s stdlib-pure mirrors
  of ``scope_path`` / ``scope_covers_path`` in ``bin/bale`` — the
  deliberate duplication the module's importability contract forces
  (its docstring names this file as the drift guard). Every semantic
  the gate implements is asserted against the mirror: whole-tree
  ``.``, equality, directory-ancestor coverage, the deliberate
  NON-coverage of ancestor-shaped paths, normalization, and the
  empty forecast covering nothing.
- **ForecastStatsTest** drives ``compute_stats`` directly over a
  synthetic telemetry corpus (the module is importable without
  ``bin/bale`` — exactly what makes this unit-testable) and asserts
  the forecast rows hand-derived: the drift rate over post-epoch
  response attempts, the path-granular admission rate, the precision
  counts (including the empty-change-set exclusion), the
  ``scope_kind`` coverage row, the departures-vs-admissions
  cross-check in all five counts, and — the epoch boundary itself —
  that a pre-epoch record (no ``scope_kind``) contributes to none of
  it while still aggregating under the pre-separation semantics.
- **ForecastLedgerE2ETest** drives the full pack → apply → stats
  path through the scratch install: the ``scope_kind`` epoch stamp on
  applied, drift-refused, and unlock attempts (the builder stamps
  unconditionally — one home, every command inherits); the recorded
  ``scope`` being the forecast; the drift refusal rendering forecast
  vocabulary; a ``forecast_departures``-bearing feedback block
  passing the response lint (the schema embed's live check), being
  accepted by apply, persisting verbatim into telemetry, and
  surfacing in ``bale stats``'s rows and cross-check.

Oracle doctrine per ADR-0002: observable-state assertions against the
documented contract — hand-derived expectations, never golden bytes.
Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_forecast_ledger.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness import (
    REPO_ROOT,
    bale_env,
    build_response_dir,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_checked,
    git_env,
    tar_response_dir,
)

# bale_stats is a sibling module designed to import without bin/bale
# loaded (its module docstring); the unit suites import it directly.
sys.path.insert(0, str(REPO_ROOT / "bin"))
import bale_stats  # noqa: E402

DRIFT_REFUSAL_MARKER = "SCOPE-DRIFT-REFUSED"
FORECAST_VOCAB_PHRASE = "write forecast"


# ---------------------------------------------------------------------------
# The containment mirror
# ---------------------------------------------------------------------------

class ContainmentMirrorTest(unittest.TestCase):
    """bale_stats' containment mirrors match the gate's semantics."""

    def test_scope_norm_matches_scope_path(self) -> None:
        cases = {
            "src": "src",
            "./src": "src",
            "src/": "src",
            "src/sub/../a.py": "src/a.py",
            "": ".",
            ".": ".",
            "  src  ": "src",
        }
        for raw, want in cases.items():
            self.assertEqual(bale_stats._scope_norm(raw), want,
                             msg=f"_scope_norm({raw!r})")

    def test_forecast_covers_semantics(self) -> None:
        # "." covers everything.
        self.assertTrue(bale_stats._forecast_covers(["."], "any/where.py"))
        # Equality covers.
        self.assertTrue(bale_stats._forecast_covers(["src/a.py"], "src/a.py"))
        # A directory entry covers its subtree.
        self.assertTrue(bale_stats._forecast_covers(["src"], "src/sub/a.py"))
        # The path being an ANCESTOR of an entry is deliberately NOT
        # coverage — scope_covers_path's directional rule.
        self.assertFalse(bale_stats._forecast_covers(["src/sub"], "src"))
        # Prefix similarity without a path boundary is not coverage.
        self.assertFalse(bale_stats._forecast_covers(["src"], "src2/a.py"))
        # The empty forecast (read-only shape) covers nothing.
        self.assertFalse(bale_stats._forecast_covers([], "a.py"))
        # The change path normalizes before the test.
        self.assertTrue(bale_stats._forecast_covers(["src"], "./src/a.py"))

    def test_mirror_agrees_with_bin_bale(self) -> None:
        """The drift guard itself: run bin/bale's helpers in a
        subprocess (it is a script, not an importable module) and
        assert both homes answer identically over a case matrix."""
        cases = [
            (["."], "a/b.py"),
            (["src"], "src/a.py"),
            (["src"], "src2/a.py"),
            (["src/sub"], "src"),
            (["src/a.py"], "src/a.py"),
            ([], "a.py"),
            (["docs", "src"], "./src/x/y.py"),
        ]
        probe = (
            "import runpy, json, sys\n"
            "mod = runpy.run_path(sys.argv[1])\n"
            "cases = json.loads(sys.argv[2])\n"
            "print(json.dumps([\n"
            "    mod['scope_covers_path'](\n"
            "        [mod['scope_path'](e) for e in scope], path)\n"
            "    for scope, path in cases\n"
            "]))\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", probe,
             str(REPO_ROOT / "bin" / "bale"), json.dumps(cases)],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        gate_answers = json.loads(result.stdout)
        mirror_answers = [
            bale_stats._forecast_covers(
                [bale_stats._scope_norm(e) for e in scope], path)
            for scope, path in cases
        ]
        self.assertEqual(mirror_answers, gate_answers,
                         msg="the stats mirror and the gate disagree — "
                             "one home drifted (bale_stats module "
                             "docstring names this test as the guard)")


# ---------------------------------------------------------------------------
# The forecast rows, unit-level
# ---------------------------------------------------------------------------

def _record(sid: str, created: str, outcome: str, attempts: list) -> dict:
    return {
        "record_version": 1,
        "session_id": sid,
        "created_at": created,
        "updated_at": created,
        "outcome": outcome,
        "attempts": attempts,
    }


def _feedback(work_class: str = "code", departures: list = None) -> dict:
    reported = {
        "assumptions": [],
        "judgment_calls": [],
        "budget_pressure": "none",
        "includes_missing": [],
        "compaction_occurred": {"occurred": False},
    }
    if departures is not None:
        reported["forecast_departures"] = departures
    return {
        "mechanical": {
            "response_kind": "normal",
            "schema_valid": True,
            "mirror_agreement": {"changes_to_files": True,
                                 "files_to_changes": True},
            "claims_subset": True,
            "provenance": {
                "bale_version": "0.4.2",
                "contract_docs": {"CLAUDE.md": "x", "TARBALL.md": "x",
                                  "DOCS.md": "x", "CODE.md": "x"},
                "packer": "fixture",
                "work_class": work_class,
                "model_identity": "fixture",
            },
        },
        "self_reported": reported,
    }


_UNSET = object()


def _attempt(*, at: str, outcome: str = "applied", command: str = "apply",
             scope: list, change_paths: list, overridden: list = None,
             scope_kind: str = "write-forecast",
             feedback: object = _UNSET) -> dict:
    attempt = {
        "at": at,
        "outcome": outcome,
        "command": command,
        "closure_reason": None,
        "tarball": None,
        "validation": None,
        "scope": scope,
        "overridden_paths": overridden or [],
        "required_check_overrides": [],
        "change_paths": change_paths,
        "feedback": _feedback() if feedback is _UNSET else feedback,
        "log": None,
    }
    if scope_kind is not None:
        attempt["scope_kind"] = scope_kind
    return attempt


class ForecastStatsTest(unittest.TestCase):
    """compute_stats' forecast rows over a hand-derived synthetic corpus."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-fcst-")
        self.telemetry = Path(self._tmpdir.name) / "telemetry"
        self.telemetry.mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _seed(self, records: list) -> None:
        for record in records:
            path = self.telemetry / f"{record['session_id']}.json"
            path.write_text(json.dumps(record, indent=2) + "\n",
                            encoding="utf-8")

    def test_forecast_rows_hand_derived(self) -> None:
        records = [
            # PRE-EPOCH: no scope_kind key. Drifts wildly against its
            # recorded scope — must contribute to the pre-separation
            # rows only, and to NO forecast row.
            _record("2026-08-01-pre-001", "2026-08-01T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-01T10:00:00+00:00",
                                 scope=["docs"],
                                 change_paths=["src/a.py"],
                                 scope_kind=None),
                    ]),
            # POST-EPOCH, no drift: forecast ["src", "BALE.md"],
            # changes touch src only — BALE.md is the untouched entry
            # (precision 1/2 on this attempt).
            _record("2026-08-08-clean-001", "2026-08-08T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-08T10:00:00+00:00",
                                 scope=["BALE.md", "src"],
                                 change_paths=["src/a.py", "src/b.py"]),
                    ]),
            # POST-EPOCH, drift admitted-and-declared: forecast
            # ["src"], two drift paths, one admitted; the admitted one
            # declared in forecast_departures, so both=1; the refused
            # one also declared (declared_only=1). Precision: entry
            # "src" touched -> 1/1.
            _record("2026-08-08-drift-001", "2026-08-08T11:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-08T11:00:00+00:00",
                                 scope=["src"],
                                 change_paths=["src/a.py", "tools/t.py",
                                               "schemas/s.json"],
                                 overridden=["tools/t.py"],
                                 feedback=_feedback(departures=[
                                     {"path": "tools/t.py",
                                      "why": "embed sync"},
                                     {"path": "schemas/s.json",
                                      "why": "schema edit"},
                                 ])),
                    ]),
            # POST-EPOCH, admitted with NO declaration — the audit
            # smell (admitted_only=1). Single-entry forecast touched.
            _record("2026-08-08-smell-001", "2026-08-08T12:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-08T12:00:00+00:00",
                                 scope=["src"],
                                 change_paths=["src/a.py", "lib/x.py"],
                                 overridden=["lib/x.py"]),
                    ]),
            # POST-EPOCH, empty change set (a pre-manifest rejection):
            # counts in forecast_attempts, no drift, and — the
            # documented exclusion — contributes NOTHING to precision.
            _record("2026-08-08-empty-001", "2026-08-08T13:00:00+00:00",
                    "rejected", [
                        _attempt(at="2026-08-08T13:00:00+00:00",
                                 outcome="rejected",
                                 scope=["src"],
                                 change_paths=[],
                                 feedback=None),
                    ]),
        ]
        # The rejected-only record needs a feedback-bearing attempt to
        # class as code? No — deliberately not: it resolves unclassed,
        # which is exactly what this test pins (the forecast rows are
        # per-class, so the empty-change attempt lands in unclassed's
        # row, not code's).
        self._seed(records)

        stats = bale_stats.compute_stats(self.telemetry)

        # Coverage: the sub-epoch begins at the first scope_kind
        # carrier; the one pre-epoch record lacks it.
        self.assertEqual(stats["coverage"]["scope_kind"], {
            "first_sid": "2026-08-08-clean-001",
            "records_lacking": 1,
        })

        code = stats["classes"]["code"]
        # Post-epoch response attempts in code: clean, drift, smell.
        self.assertEqual(code["forecast_attempts"], 3)
        self.assertEqual(code["forecast_drift_attempts"], 2)
        self.assertAlmostEqual(code["forecast_drift_rate"], 2 / 3)
        # Drift paths: 2 (drift-001) + 1 (smell-001) = 3; admitted:
        # tools/t.py + lib/x.py = 2.
        self.assertEqual(code["forecast_drift_paths"], 3)
        self.assertEqual(code["forecast_admitted_paths"], 2)
        self.assertAlmostEqual(code["forecast_admission_rate"], 2 / 3)
        # Precision entries: clean 2 (1 untouched) + drift 1 + smell 1
        # = 4 entries, 1 untouched, 3 touched.
        self.assertEqual(code["forecast_entries"], 4)
        self.assertEqual(code["forecast_entries_untouched"], 1)
        self.assertAlmostEqual(code["forecast_precision"], 3 / 4)
        # The pre-epoch record aggregates under pre-separation
        # semantics: its response attempt counts in the era-blind
        # denominators (4 = pre-001 + clean + drift + smell), while
        # its drift enters NO forecast row — the epoch split at work.
        self.assertEqual(code["response_attempts"], 4)

        # The empty-change post-epoch attempt landed unclassed: counts
        # as a forecast attempt with no drift and no precision
        # contribution.
        unclassed = stats["classes"]["unclassed"]
        self.assertEqual(unclassed["forecast_attempts"], 1)
        self.assertEqual(unclassed["forecast_drift_attempts"], 0)
        self.assertEqual(unclassed["forecast_entries"], 0,
                         msg="an attempt that landed nothing measures "
                             "nothing about forecast width")
        self.assertIsNone(unclassed["forecast_precision"])

        # The cross-check, all five counts hand-derived:
        # drift-001: declared {tools/t.py, schemas/s.json}, admitted
        # {tools/t.py} -> both 1, declared_only 1.
        # smell-001: admitted {lib/x.py}, declared {} -> admitted_only 1.
        self.assertEqual(stats["cross_checks"]["forecast_departures"], {
            "declared_paths": 2,
            "admitted_paths": 2,
            "both": 1,
            "admitted_only": 1,
            "declared_only": 1,
        })

    def test_pre_epoch_only_corpus_has_null_forecast_rows(self) -> None:
        """A corpus wholly pre-epoch: zero counts, null rates, and a
        null coverage row — no fabricated zeros for an epoch that
        hasn't begun."""
        self._seed([
            _record("2026-08-01-pre-001", "2026-08-01T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-01T10:00:00+00:00",
                                 scope=["docs"],
                                 change_paths=["src/a.py"],
                                 scope_kind=None),
                    ]),
        ])
        stats = bale_stats.compute_stats(self.telemetry)
        self.assertIsNone(stats["coverage"]["scope_kind"])
        code = stats["classes"]["code"]
        self.assertEqual(code["forecast_attempts"], 0)
        self.assertIsNone(code["forecast_drift_rate"])
        self.assertIsNone(code["forecast_admission_rate"])
        self.assertIsNone(code["forecast_precision"])
        self.assertEqual(stats["cross_checks"]["forecast_departures"], {
            "declared_paths": 0, "admitted_paths": 0, "both": 0,
            "admitted_only": 0, "declared_only": 0,
        })


# ---------------------------------------------------------------------------
# End to end: pack → apply → telemetry → stats
# ---------------------------------------------------------------------------

class ForecastLedgerE2ETest(unittest.TestCase):
    """The epoch stamp, the refusal vocabulary, and the departures
    field, driven through the real pack/apply/stats pipeline."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-fcst-e2e-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        # A committed src/ area so a narrow forecast has something to
        # cover while the read include stays generous (the separation
        # working as designed — the thesis this arc exists for).
        (self.repo / "src").mkdir()
        (self.repo / "src" / "a.txt").write_text("a\n", encoding="utf-8")
        run_checked(["git", "add", "src/a.txt"], cwd=self.repo,
                    env=self.genv)
        run_checked(["git", "commit", "-m", "add src"], cwd=self.repo,
                    env=self.genv)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack_narrow_forecast(self) -> str:
        """Generous read (whole tree), narrow forecast (src only)."""
        result = run_bale(
            self.install,
            ["pack", "forecast ledger e2e session",
             "--slug", "fcst-e2e",
             "--include", ".",
             "--write", "src",
             "--no-readme"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(result.returncode, 0,
                         msg=f"stdout:\n{result.stdout}\n"
                             f"stderr:\n{result.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        return sids[0]

    def telemetry_record(self, sid: str) -> dict:
        path = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(path.is_file(),
                        msg=f"telemetry record missing at {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def response(self, sid: str, *, path: str, feedback: dict = None,
                 name: str = "resp") -> Path:
        extra = {"feedback": feedback} if feedback is not None else None
        rdir = build_response_dir(
            self.tmp / name, sid,
            summary="forecast ledger e2e fixture",
            entries=[{
                "path": path,
                "action": "modified" if path == "src/a.txt" else "created",
                "reason": "forecast ledger fixture change",
                "data": b"changed by the fixture\n",
            }],
            manifest_extra=extra,
        )
        return tar_response_dir(rdir)

    # -- the pins --------------------------------------------------------

    def test_epoch_stamp_and_departures_full_path(self) -> None:
        """One session, three movements: an in-forecast apply carrying
        a departures-free feedback block stamps scope_kind and the
        forecast; then a fresh session's out-of-forecast response
        refuses in forecast vocabulary and stamps the refused attempt;
        then stats reads it all back."""
        sid = self.pack_narrow_forecast()

        # The lint accepts a departures-bearing manifest (the live
        # check on the schema embed): declare one departure even
        # though this response stays in-forecast — schema-wise the
        # field is free-standing; semantically stats will report it
        # declared_only, which the cross-check assertion pins below.
        feedback = _feedback(departures=[
            {"path": "tools/never-shipped.py",
             "why": "declared but never shipped — the declared_only "
                    "shape under test"},
        ])
        tarball = self.response(sid, path="src/a.txt", feedback=feedback)
        rdir = tarball.parent / tarball.name.replace(".tar.gz", "")
        lint = subprocess.run(
            [sys.executable,
             str(self.install / "tools" / "response_lint.py"), str(rdir)],
            capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(
            lint.returncode, 0,
            msg=f"the lint must accept forecast_departures (schema "
                f"embed in sync):\nstdout:\n{lint.stdout}\n"
                f"stderr:\n{lint.stderr}")

        result = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 0,
                         msg=f"stdout:\n{result.stdout}\n"
                             f"stderr:\n{result.stderr}")

        record = self.telemetry_record(sid)
        attempt = record["attempts"][-1]
        self.assertEqual(attempt["outcome"], "applied")
        self.assertEqual(attempt["scope_kind"], "write-forecast",
                         msg="the epoch key is stamped on every "
                             "post-epoch attempt")
        self.assertEqual(attempt["scope"], ["src"],
                         msg="post-epoch, scope IS the write forecast — "
                             "narrow despite the whole-tree include")
        self.assertEqual(
            attempt["feedback"]["self_reported"]["forecast_departures"],
            feedback["self_reported"]["forecast_departures"],
            msg="the departures field persists verbatim with the block")

        # Second movement: a fresh session, an out-of-forecast path.
        # The response carries a departures-free feedback block so the
        # session classes as code (class resolution reads the latest
        # feedback-bearing attempt) — and so its admitted path lands
        # as admitted_only, the audit smell.
        sid2 = self.pack_narrow_forecast()
        drift_tarball = self.response(sid2, path="lib/new.txt",
                                      feedback=_feedback(),
                                      name="drift")
        drift = run_bale(self.install, ["apply", str(drift_tarball)],
                         cwd=self.repo, env=self.env)
        self.assertEqual(drift.returncode, 1)
        self.assertIn(DRIFT_REFUSAL_MARKER, drift.stdout)
        self.assertIn(FORECAST_VOCAB_PHRASE, drift.stdout,
                      msg="the refusal renders forecast vocabulary "
                          "(ADR-0015 session B)")
        self.assertNotIn("declared scope", drift.stdout,
                         msg="the pre-separation vocabulary is retired "
                             "from the refusal")
        refused_attempt = self.telemetry_record(sid2)["attempts"][-1]
        self.assertEqual(refused_attempt["outcome"], "scope-drift-refused")
        self.assertEqual(refused_attempt["scope_kind"], "write-forecast")

        # Third movement: the same drift admitted per path — the
        # ADR-0014 flow generalized — lands, stamps overridden_paths,
        # and closes the session.
        admitted = run_bale(
            self.install,
            ["apply", str(drift_tarball),
             "--allow-out-of-scope", "lib/new.txt"],
            cwd=self.repo, env=self.env)
        self.assertEqual(admitted.returncode, 0,
                         msg=f"stdout:\n{admitted.stdout}\n"
                             f"stderr:\n{admitted.stderr}")
        admitted_attempt = self.telemetry_record(sid2)["attempts"][-1]
        self.assertEqual(admitted_attempt["outcome"], "applied")
        self.assertEqual(admitted_attempt["overridden_paths"],
                         ["lib/new.txt"])
        self.assertEqual(admitted_attempt["scope_kind"], "write-forecast")

        # Fourth movement: unlock a third session — the stamp rides
        # every command's attempts, not just apply's.
        sid3 = self.pack_narrow_forecast()
        unlock = run_bale(self.install, ["unlock", sid3],
                          cwd=self.repo, env=self.env)
        self.assertEqual(unlock.returncode, 0,
                         msg=f"stdout:\n{unlock.stdout}\n"
                             f"stderr:\n{unlock.stderr}")
        unlock_attempt = self.telemetry_record(sid3)["attempts"][-1]
        self.assertEqual(unlock_attempt["outcome"], "unlocked")
        self.assertEqual(unlock_attempt["scope_kind"], "write-forecast")

        # Finale: stats reads the corpus this session just wrote.
        stats_run = run_bale(self.install, ["stats", "--json"],
                             cwd=self.repo, env=self.env)
        self.assertEqual(stats_run.returncode, 0, msg=stats_run.stderr)
        lines = [ln for ln in stats_run.stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)
        stats = json.loads(lines[0])
        self.assertIsNotNone(stats["coverage"]["scope_kind"])
        code = stats["classes"]["code"]
        # sid1 applied (1 response attempt) + sid2 refused + admitted
        # (2 response attempts) = 3 post-epoch response attempts; the
        # unlock is not a response attempt. sid2's two attempts both
        # drifted (same change set).
        self.assertEqual(code["forecast_attempts"], 3)
        self.assertEqual(code["forecast_drift_attempts"], 2)
        self.assertEqual(code["forecast_drift_paths"], 2)
        self.assertEqual(code["forecast_admitted_paths"], 1)
        self.assertAlmostEqual(code["forecast_admission_rate"], 1 / 2)
        # Cross-check: sid1 declared one path never admitted
        # (declared_only 1); sid2's admitted path was never declared
        # (admitted_only 1 — the audit smell, live).
        departures = stats["cross_checks"]["forecast_departures"]
        self.assertEqual(departures["declared_only"], 1)
        self.assertEqual(departures["admitted_only"], 1)
        self.assertEqual(departures["both"], 0)

        # The human report renders the new rows.
        human = run_bale(self.install, ["stats"], cwd=self.repo,
                         env=self.env)
        self.assertEqual(human.returncode, 0)
        self.assertIn("forecast drift", human.stdout)
        self.assertIn("forecast precision", human.stdout)
        self.assertIn("cross-check forecast departures", human.stdout)
        self.assertIn("scope_kind (write-forecast epoch)", human.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
