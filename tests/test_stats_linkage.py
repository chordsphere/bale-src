#!/usr/bin/env python3
"""The `bale stats` linkage rollup (board 65).

Gives ``feedback.mechanical.linkage`` — the self-reported record that a
session went through a probe or clarification round — its first
consumer: per-class counts by ``kind`` and by placement, nominated
beside the rates, never blended into them. Two suites, unit-first,
following the ``test_forecast_ledger.py`` precedent of a separate
suite over its own synthetic corpus (the shared fixture corpus stays
untouched; the queued fold-in for post-epoch fixtures rides a session
that must perturb ``test_stats_aggregation.py``'s whole-corpus
expectations anyway):

- **LinkageRollupUnitTest** drives ``compute_stats`` directly over a
  synthetic telemetry corpus (``bale_stats`` imports without
  ``bin/bale`` loaded — its documented contract) and asserts the
  rollup hand-derived: counts per kind, verbatim honest rows for an
  out-of-vocabulary kind, the "unspecified" bucket for a stamp with
  no usable kind or placement, the legacy ``surfaced`` key read
  beside the current ``point`` key (both spellings exist in the real
  corpus — telemetry persists feedback verbatim), the per-work-class
  split falling out of the classes keying, tolerance of malformed
  stamps (non-dict linkage counts nothing, crashes nothing), the
  scan-every-attempt semantics mirroring the clarification
  cross-check's read, and the untouched behavior of that cross-check
  after its read moved into the shared ``_attempt_linkage`` home.
- **LinkageRollupE2ETest** drives ``bin/bale stats`` end to end over
  a scratch repo seeded with the same synthetic shapes and asserts
  both output modes carry the aggregation under the ``linkage``
  label: the ``--json`` line's per-class ``linkage`` key, and the
  human report's extras line — rendered only for classes with
  stamped attempts, absent otherwise (no fabricated zeros).

Oracle doctrine per ADR-0002: observable-state assertions against the
documented contract — hand-derived expectations, never golden bytes.
Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_stats_linkage.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

from harness import (
    REPO_ROOT,
    bale_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
)

# bale_stats is a sibling module designed to import without bin/bale
# loaded (its module docstring); the unit suite imports it directly.
sys.path.insert(0, str(REPO_ROOT / "bin"))
import bale_stats  # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic-record builders (the test_forecast_ledger.py pattern)
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


def _feedback(work_class: str = "code", linkage: object = None) -> dict:
    """A minimal well-formed feedback block carrying the given linkage
    stamp verbatim (telemetry persists the block as-shipped, so the
    corpus admits every shape a manifest ever carried)."""
    return {
        "mechanical": {
            "response_kind": "normal",
            "schema_valid": True,
            "mirror_agreement": {"changes_to_files": True,
                                 "files_to_changes": True},
            "claims_subset": True,
            "linkage": linkage,
            "provenance": {
                "bale_version": "0.4.19",
                "contract_docs": {"CLAUDE.md": "x", "TARBALL.md": "x",
                                  "DOCS.md": "x", "CODE.md": "x",
                                  "PLANNER.md": "x"},
                "packer": "fixture",
                "work_class": work_class,
                "model_identity": "fixture",
            },
        },
        "self_reported": {
            "assumptions": [],
            "judgment_calls": [],
            "budget_pressure": "none",
            "includes_missing": [],
            "compaction_occurred": {"occurred": False},
        },
    }


def _attempt(*, at: str, outcome: str = "applied", command: str = "apply",
             feedback: object = None) -> dict:
    return {
        "at": at,
        "outcome": outcome,
        "command": command,
        "closure_reason": None,
        "tarball": None,
        "validation": None,
        "scope": [],
        "overridden_paths": [],
        "required_check_overrides": [],
        "change_paths": [],
        "feedback": feedback,
        "log": None,
    }


# ---------------------------------------------------------------------------
# The rollup, unit-level
# ---------------------------------------------------------------------------

class LinkageRollupUnitTest(unittest.TestCase):
    """compute_stats' linkage rollup over a hand-derived corpus."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-lkg-")
        self.telemetry = Path(self._tmpdir.name) / "telemetry"
        self.telemetry.mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _seed(self, records: list) -> None:
        for record in records:
            path = self.telemetry / f"{record['session_id']}.json"
            path.write_text(json.dumps(record, indent=2) + "\n",
                            encoding="utf-8")

    # -- the stamp readers, directly --------------------------------------

    def test_attempt_linkage_reader_tolerance(self) -> None:
        # The one-home read: a dict stamp comes back verbatim; every
        # malformed surrounding shape reads as no stamp, never a crash.
        stamp = {"kind": "probe", "point": "pre-build"}
        self.assertEqual(
            bale_stats._attempt_linkage(
                _attempt(at="t", feedback=_feedback(linkage=stamp))),
            stamp)
        for feedback in (None, "not-a-dict",
                         {"mechanical": None},
                         {"mechanical": {"linkage": None}},
                         {"mechanical": {"linkage": "clarification"}},
                         {"mechanical": {"linkage": ["probe"]}}):
            self.assertIsNone(
                bale_stats._attempt_linkage(
                    _attempt(at="t", feedback=feedback)),
                msg=f"feedback shape {feedback!r} must read as no stamp")

    def test_linkage_point_key_spellings(self) -> None:
        # The current schema key, the legacy spelling, precedence when
        # both are present, and None for an unreported placement.
        self.assertEqual(
            bale_stats._linkage_point({"point": "pre-read"}), "pre-read")
        self.assertEqual(
            bale_stats._linkage_point({"surfaced": "mid-build"}),
            "mid-build")
        self.assertEqual(
            bale_stats._linkage_point(
                {"point": "pre-build", "surfaced": "mid-build"}),
            "pre-build",
            msg="the current key wins over the legacy spelling")
        for stamp in ({}, {"point": ""}, {"point": None},
                      {"surfaced": 3}, {"point": "", "surfaced": ""}):
            self.assertIsNone(bale_stats._linkage_point(stamp),
                              msg=f"stamp {stamp!r} reports no placement")

    # -- the rollup over a corpus ------------------------------------------

    def test_rollup_hand_derived(self) -> None:
        records = [
            # Two clarification stamps in one code session — one under
            # the current `point` key, one under the legacy `surfaced`
            # spelling (a retried session whose rounds persisted from
            # manifests of different eras).
            _record("2026-08-10-clar-001", "2026-08-10T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-10T10:00:00+00:00",
                                 outcome="held",
                                 feedback=_feedback(linkage={
                                     "kind": "clarification",
                                     "point": "pre-build",
                                 })),
                        _attempt(at="2026-08-10T11:00:00+00:00",
                                 command="retry",
                                 feedback=_feedback(linkage={
                                     "kind": "clarification",
                                     "surfaced": "mid-build",
                                 })),
                    ]),
            # A probe stamp carrying depends_on (the file-based-probe
            # shape) — the extra key is schema-legal and ignored here.
            _record("2026-08-11-probe-001", "2026-08-11T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-11T10:00:00+00:00",
                                 feedback=_feedback(linkage={
                                     "kind": "probe",
                                     "point": "pre-read",
                                     "depends_on": None,
                                 })),
                    ]),
            # An out-of-vocabulary kind and no placement at all: the
            # kind forms its own honest verbatim row; the placement
            # lands under "unspecified".
            _record("2026-08-12-odd-001", "2026-08-12T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-12T10:00:00+00:00",
                                 feedback=_feedback(linkage={
                                     "kind": "escalation",
                                 })),
                    ]),
            # A stamp with no usable kind: "unspecified" kind bucket.
            _record("2026-08-13-nokind-001", "2026-08-13T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-13T10:00:00+00:00",
                                 feedback=_feedback(linkage={
                                     "point": "mid-build",
                                 })),
                    ]),
            # A doc-class probe: the per-work-class split falls out of
            # the classes keying — this one must land in doc's row.
            _record("2026-08-14-doc-001", "2026-08-14T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-14T10:00:00+00:00",
                                 feedback=_feedback(
                                     work_class="doc",
                                     linkage={"kind": "probe",
                                              "point": "mid-build"})),
                    ]),
            # No stamp anywhere (linkage null, the schema's own
            # absent-marker): honest empty rollup for this session.
            _record("2026-08-15-none-001", "2026-08-15T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-15T10:00:00+00:00",
                                 feedback=_feedback()),
                    ]),
            # A malformed stamp (string, not dict): counts nothing,
            # crashes nothing.
            _record("2026-08-16-bad-001", "2026-08-16T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-16T10:00:00+00:00",
                                 feedback={
                                     "mechanical": {
                                         "linkage": "clarification"}}),
                    ]),
        ]
        self._seed(records)

        stats = bale_stats.compute_stats(self.telemetry)

        code = stats["classes"]["code"]
        # code stamps: 2 clarification + 1 probe + 1 escalation +
        # 1 kindless = 5. (The malformed-stamp session classes as
        # unclassed — its feedback carries no provenance — and counts
        # nothing anywhere; the stampless session is code with an
        # honest zero contribution.)
        self.assertEqual(code["linkage"], {
            "attempts": 5,
            "kinds": {"clarification": 2, "escalation": 1, "probe": 1,
                      "unspecified": 1},
            "points": {"mid-build": 2, "pre-build": 1, "pre-read": 1,
                       "unspecified": 1},
        })

        doc = stats["classes"]["doc"]
        self.assertEqual(doc["linkage"], {
            "attempts": 1,
            "kinds": {"probe": 1},
            "points": {"mid-build": 1},
        })

        # The malformed-stamp session: unclassed, empty rollup — the
        # non-dict stamp reads as no stamp, and empties are honest
        # (counts, not rates: no null-on-zero rule applies).
        unclassed = stats["classes"]["unclassed"]
        self.assertEqual(unclassed["linkage"],
                         {"attempts": 0, "kinds": {}, "points": {}})

        # The rollup nominates beside the existing cross-check and
        # redefines nothing: the two clarification-stamped sessions
        # are exactly the self-reported set the cross-check counts
        # (the "escalation" and kindless stamps are not clarification
        # self-reports).
        self.assertEqual(
            stats["cross_checks"]["clarification"]
            ["self_reported_sessions"], 1,
            msg="one session self-reports clarification linkage; the "
                "rollup's finer counts must not widen the cross-check")

    def test_scan_covers_every_attempt(self) -> None:
        # The documented scan-every-attempt semantics (mirroring the
        # clarification cross-check's read): a stamp on a non-response
        # attempt still counts — the rollup reports what was recorded,
        # wherever it was recorded.
        self._seed([
            _record("2026-08-17-unlock-001", "2026-08-17T10:00:00+00:00",
                    "unlocked", [
                        _attempt(at="2026-08-17T10:00:00+00:00",
                                 outcome="unlocked", command="unlock",
                                 feedback=_feedback(linkage={
                                     "kind": "clarification",
                                     "point": "pre-build",
                                 })),
                    ]),
        ])
        stats = bale_stats.compute_stats(self.telemetry)
        self.assertEqual(stats["classes"]["code"]["linkage"]["attempts"], 1)

    def test_filters_reach_the_rollup(self) -> None:
        # The rollup is a class-row member, so both filters reach it
        # the same way they reach every rate: membership first.
        self._seed([
            _record("2026-08-10-old-001", "2026-08-10T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-10T10:00:00+00:00",
                                 feedback=_feedback(linkage={
                                     "kind": "probe",
                                     "point": "pre-read"})),
                    ]),
            _record("2026-09-01-new-001", "2026-09-01T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-09-01T10:00:00+00:00",
                                 feedback=_feedback(
                                     work_class="doc",
                                     linkage={"kind": "clarification",
                                              "point": "mid-build"})),
                    ]),
        ])
        since = bale_stats.compute_stats(self.telemetry,
                                         since="2026-09-01")
        self.assertEqual(sorted(since["classes"]), ["doc"])
        self.assertEqual(since["classes"]["doc"]["linkage"]["kinds"],
                         {"clarification": 1})
        classed = bale_stats.compute_stats(self.telemetry,
                                           work_class="code")
        self.assertEqual(sorted(classed["classes"]), ["code"])
        self.assertEqual(classed["classes"]["code"]["linkage"]["kinds"],
                         {"probe": 1})

    def test_empty_corpus_no_rollup_rows(self) -> None:
        # An empty corpus has no class rows at all — the rollup adds
        # no top-level surface and degrades exactly as the rest of the
        # classes table does.
        stats = bale_stats.compute_stats(self.telemetry)
        self.assertEqual(stats["classes"], {})


# ---------------------------------------------------------------------------
# Both output modes, end to end
# ---------------------------------------------------------------------------

class LinkageRollupE2ETest(unittest.TestCase):
    """`bale stats` surfaces the rollup under the `linkage` label in
    both output modes (the brief's outcome contract 1)."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-lkg-e2e-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _seed(self) -> None:
        telemetry = self.repo / "claude" / "telemetry"
        telemetry.mkdir(parents=True, exist_ok=True)
        records = [
            _record("2026-08-10-clar-001", "2026-08-10T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-10T10:00:00+00:00",
                                 feedback=_feedback(linkage={
                                     "kind": "clarification",
                                     "surfaced": "mid-build"})),
                    ]),
            _record("2026-08-11-probe-001", "2026-08-11T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-11T10:00:00+00:00",
                                 feedback=_feedback(linkage={
                                     "kind": "probe",
                                     "point": "pre-build"})),
                    ]),
            # A doc-class session with NO stamp: its extras must carry
            # no linkage entry (no fabricated zeros).
            _record("2026-08-12-doc-001", "2026-08-12T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-12T10:00:00+00:00",
                                 feedback=_feedback(work_class="doc")),
                    ]),
        ]
        for record in records:
            (telemetry / f"{record['session_id']}.json").write_text(
                json.dumps(record, indent=2) + "\n", encoding="utf-8")

    def test_json_mode_carries_linkage(self) -> None:
        self._seed()
        result = run_bale(self.install, ["stats", "--json"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 0,
                         msg=f"stderr:\n{result.stderr}")
        lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1,
                         msg="json stream discipline: one stdout line")
        payload = json.loads(lines[0])
        self.assertEqual(payload["classes"]["code"]["linkage"], {
            "attempts": 2,
            "kinds": {"clarification": 1, "probe": 1},
            "points": {"mid-build": 1, "pre-build": 1},
        })
        self.assertEqual(payload["classes"]["doc"]["linkage"],
                         {"attempts": 0, "kinds": {}, "points": {}})

    def test_human_mode_carries_linkage(self) -> None:
        self._seed()
        result = run_bale(self.install, ["stats"], cwd=self.repo,
                          env=self.env)
        self.assertEqual(result.returncode, 0,
                         msg=f"stderr:\n{result.stderr}")
        out = result.stdout
        # The label, the kind counts, and the placement counts — the
        # renderer's thin projection of the computed dicts, in the
        # class extras (the legacy `surfaced` spelling normalizes into
        # the same placement bucket as `point`, so the line reads one
        # vocabulary).
        self.assertIn(
            "code: linkage 2 [clarification 1, probe 1] "
            "surfaced [mid-build 1, pre-build 1]", out)
        # The stampless class renders no linkage entry at all.
        self.assertNotIn("doc: linkage", out)

    def test_empty_corpus_still_exits_zero(self) -> None:
        # Outcome contract 1's exit-0 half must survive a repo with no
        # telemetry at all: the rollup adds nothing that crashes the
        # honest empty report in either mode.
        for args in (["stats"], ["stats", "--json"]):
            result = run_bale(self.install, args, cwd=self.repo,
                              env=self.env)
            self.assertEqual(result.returncode, 0,
                             msg=f"{args}: stderr:\n{result.stderr}")


if __name__ == "__main__":
    unittest.main()
