#!/usr/bin/env python3
"""The `bale stats` compaction read side (board 37, v0.4.38).

Gives ``feedback.self_reported.compaction_occurred`` — the worker's own
disclosure that the runtime compacted its context mid-session
(TARBALL.md §5.2.2; CLAUDE.md §11.6 is the recovery path it points at)
— its first consumer: ``cross_checks.budget.compaction``
``{reporting_sessions, occurred_sessions}`` and
``members.compaction_occurred``, additive beside the budget pressure
pass. Before this, nothing read the field, and silence in ``bale
stats`` was indistinguishable from health.

Two suites over their own synthetic corpus, following the
``test_stats_linkage.py`` / ``test_forecast_ledger.py`` precedent (the
shared fixture corpus under ``tests/fixtures/stats_corpus/`` stays
untouched: no fixture there discloses a compaction, and adding one
would recompute every shared expectation — a rider this suite does not
carry):

- **CompactionReadSideUnitTest** drives the readers and
  ``compute_stats`` directly (``bale_stats`` imports without
  ``bin/bale`` loaded — its documented contract). It pins the
  definition hand-derived: both real shapes (the schema's object with a
  bool ``occurred``, and the bare bool the older fixtures carry), every
  malformed shape reading as no report and never crashing, the
  any-attempt session semantics (a retry's ``false`` does not erase the
  first attempt's disclosure), the membership exclusions and both
  filters reaching the counts the way they reach every cross-check,
  and agreement with the planning desk's executable definition on a
  corpus mixing all of the above.
- **CompactionReadSideE2ETest** drives ``bin/bale stats`` end to end
  and asserts both output modes: the ``--json`` line's new keys beside
  the unchanged budget keys (the additive contract), and the human
  report's ``cross-check compaction`` line plus its corpus-members sid
  line, the latter rendered only when a session discloses.

Oracle doctrine per ADR-0002: observable-state assertions against the
documented contract — hand-derived expectations, never golden bytes.
The key contract is owned by ``format_stats_json``'s docstring in
``bin/bale_report.py``.
Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_stats_compaction.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
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


# A sentinel meaning "leave the key out of self_reported entirely" —
# distinct from None, which writes an explicit JSON null.
_ABSENT = object()


# ---------------------------------------------------------------------------
# Synthetic-record builders (the test_stats_linkage.py pattern)
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


def _feedback(compaction: object = _ABSENT, *,
              work_class: str = "code") -> dict:
    """A minimal well-formed feedback block whose self_reported carries
    `compaction` verbatim under compaction_occurred (or omits the key
    for _ABSENT) — telemetry persists the block as shipped, so the
    corpus admits every shape a manifest ever carried."""
    self_reported = {
        "assumptions": [],
        "judgment_calls": [],
        "budget_pressure": "none",
        "includes_missing": [],
    }
    if compaction is not _ABSENT:
        self_reported["compaction_occurred"] = compaction
    return {
        "mechanical": {
            "response_kind": "normal",
            "schema_valid": True,
            "mirror_agreement": {"changes_to_files": True,
                                 "files_to_changes": True},
            "claims_subset": True,
            "provenance": {
                "bale_version": "0.4.37",
                "contract_docs": {"CLAUDE.md": "x", "TARBALL.md": "x",
                                  "DOCS.md": "x", "CODE.md": "x",
                                  "PLANNER.md": "x"},
                "packer": "fixture",
                "work_class": work_class,
                "model_identity": "fixture",
            },
        },
        "self_reported": self_reported,
    }


def _attempt(*, at: str, outcome: str = "applied", command: str = "apply",
             closure_reason: object = None,
             feedback: object = None) -> dict:
    return {
        "at": at,
        "outcome": outcome,
        "command": command,
        "closure_reason": closure_reason,
        "tarball": None,
        "validation": None,
        "scope": [],
        "overridden_paths": [],
        "required_check_overrides": [],
        "change_paths": [],
        "feedback": feedback,
        "log": None,
    }


def _one(sid: str, day: str, feedback: object, *,
         outcome: str = "applied") -> dict:
    """A single-attempt session dated 2026-08-<day>."""
    at = f"2026-08-{day}T10:00:00+00:00"
    return _record(sid, at, outcome,
                   [_attempt(at=at, outcome=outcome, feedback=feedback)])


def _desk_definition(membership: list) -> tuple:
    """The planning desk's measurement from the board 37 brief, verbatim
    in behavior: the definition in executable form, used here as an
    independent oracle for the shipped reader (never as its mechanism).
    Only ever fed records whose self_reported is a dict or absent — the
    desk's `(x or {}).get` would raise on a truthy non-dict, a shape the
    shipped reader tolerates and the unit tests pin separately."""
    reporting, occurred = set(), set()
    for record in membership:
        for attempt in record["attempts"]:
            feedback = attempt.get("feedback")
            if not isinstance(feedback, dict):
                continue
            value = (feedback.get("self_reported") or {}).get(
                "compaction_occurred")
            if isinstance(value, dict):
                value = value.get("occurred")
            if isinstance(value, bool):
                reporting.add(record["session_id"])
                if value:
                    occurred.add(record["session_id"])
    return reporting, occurred


# ---------------------------------------------------------------------------
# The read side, unit-level
# ---------------------------------------------------------------------------

class CompactionReadSideUnitTest(unittest.TestCase):
    """The readers and compute_stats over a hand-derived corpus."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-cmp-")
        self.telemetry = Path(self._tmpdir.name) / "telemetry"
        self.telemetry.mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _seed(self, records: list) -> None:
        for record in records:
            path = self.telemetry / f"{record['session_id']}.json"
            path.write_text(json.dumps(record, indent=2) + "\n",
                            encoding="utf-8")

    # -- the attempt reader -------------------------------------------------

    def test_attempt_reader_accepts_both_real_shapes(self) -> None:
        # The schema's object and the older corpus's bare bool, each in
        # both polarities.
        for value, expected in (({"occurred": True}, True),
                                ({"occurred": False}, False),
                                ({"occurred": True,
                                  "disclosure_ref": "notes.md"}, True),
                                (True, True),
                                (False, False)):
            attempt = _attempt(at="t", feedback=_feedback(value))
            self.assertIs(bale_stats._attempt_compaction(attempt), expected,
                          msg=f"compaction_occurred {value!r}")

    def test_attempt_reader_malformed_shapes_report_nothing(self) -> None:
        # Every shape outside the two real ones reads as no report —
        # None — never a crash and never a coerced value. 0/1 are not
        # bools (JSON numbers must not pass for false/true), and an
        # object needs a bool `occurred`.
        for value in (_ABSENT, None, "true", "yes", "", 0, 1, 1.0, [],
                      [True], {}, {"occurred": None},
                      {"occurred": "true"}, {"occurred": 1},
                      {"value": True}):
            attempt = _attempt(at="t", feedback=_feedback(value))
            self.assertIsNone(bale_stats._attempt_compaction(attempt),
                              msg=f"compaction_occurred {value!r}")
        # And the surrounding shapes: no feedback, a non-dict feedback,
        # a missing, null, or non-dict self_reported.
        for feedback in (None, "not-a-dict", [], {},
                         {"self_reported": None},
                         {"self_reported": "compacted"},
                         {"self_reported": ["compaction_occurred"]}):
            attempt = _attempt(at="t", feedback=feedback)
            self.assertIsNone(bale_stats._attempt_compaction(attempt),
                              msg=f"feedback {feedback!r}")

    # -- the session reader ---------------------------------------------------

    def test_session_reader_any_attempt(self) -> None:
        at1, at2 = "2026-08-01T10:00:00+00:00", "2026-08-01T11:00:00+00:00"

        def session(*feedbacks: object) -> dict:
            return _record("2026-08-01-s-001", at1, "applied", [
                _attempt(at=at1 if i == 0 else at2, feedback=f)
                for i, f in enumerate(feedbacks)])

        # HOLD→retry where the first attempt disclosed and the retry's
        # manifest says false: the event happened — it still discloses.
        self.assertEqual(bale_stats.session_compaction(session(
            _feedback({"occurred": True}), _feedback({"occurred": False}))),
            (True, True))
        # The reverse order discloses too.
        self.assertEqual(bale_stats.session_compaction(session(
            _feedback(False), _feedback(True))), (True, True))
        # One unreadable attempt beside one readable false: reports,
        # does not disclose.
        self.assertEqual(bale_stats.session_compaction(session(
            _feedback("garbage"), _feedback({"occurred": False}))),
            (True, False))
        # A feedback-less attempt contributes nothing either way.
        self.assertEqual(bale_stats.session_compaction(session(
            None, _feedback(True))), (True, True))
        # Nothing readable anywhere: neither.
        self.assertEqual(bale_stats.session_compaction(session(
            None, _feedback(), _feedback({"occurred": None}))),
            (False, False))
        # No attempts at all: neither, no crash.
        self.assertEqual(bale_stats.session_compaction(
            _record("2026-08-01-empty-001", at1, "opened", [])),
            (False, False))

    # -- the payload over a corpus ------------------------------------------

    def _mixed_corpus(self) -> list:
        """Hand-derived: reporting = obj-true, bool-true, obj-false,
        bool-false, retry-disclosed (5); disclosing = obj-true,
        bool-true, retry-disclosed (3). Not reporting: absent, null,
        string, int, no-feedback. Excluded from membership although
        they disclose: the read-only and crash-debris sessions."""
        retry_at1 = "2026-08-12T10:00:00+00:00"
        retry_at2 = "2026-08-12T11:00:00+00:00"
        return [
            _one("2026-08-02-obj-true-001", "02", _feedback({"occurred": True})),
            _one("2026-08-03-bool-true-001", "03", _feedback(True)),
            _one("2026-08-04-obj-false-001", "04",
                 _feedback({"occurred": False})),
            _one("2026-08-05-bool-false-001", "05", _feedback(False)),
            _one("2026-08-06-absent-001", "06", _feedback()),
            _one("2026-08-07-null-001", "07", _feedback(None)),
            _one("2026-08-08-string-001", "08", _feedback("true")),
            _one("2026-08-09-int-001", "09", _feedback(1)),
            _one("2026-08-10-nofeedback-001", "10", None,
                 outcome="unlocked"),
            _record("2026-08-12-retry-disclosed-001", retry_at1, "applied", [
                _attempt(at=retry_at1, outcome="held",
                         feedback=_feedback({"occurred": True})),
                _attempt(at=retry_at2, command="retry",
                         feedback=_feedback({"occurred": False})),
            ]),
            # Membership exclusions: disclosing, but never counted.
            _record("2026-08-13-readonly-001", "2026-08-13T10:00:00+00:00",
                    "unlocked", [
                        _attempt(at="2026-08-13T10:00:00+00:00",
                                 outcome="unlocked", command="unlock",
                                 closure_reason="closed-read-only",
                                 feedback=_feedback(True)),
                    ]),
            _record("2026-08-14-debris-001", "2026-08-14T10:00:00+00:00",
                    "unlocked", [
                        _attempt(at="2026-08-14T10:00:00+00:00",
                                 outcome="unlocked", command="unlock",
                                 closure_reason="crash-debris",
                                 feedback=_feedback(True)),
                    ]),
        ]

    def test_counts_hand_derived(self) -> None:
        self._seed(self._mixed_corpus())
        stats = bale_stats.compute_stats(self.telemetry)
        self.assertEqual(stats["cross_checks"]["budget"]["compaction"], {
            "reporting_sessions": 5,
            "occurred_sessions": 3,
        })
        self.assertEqual(stats["members"]["compaction_occurred"], [
            "2026-08-02-obj-true-001",
            "2026-08-03-bool-true-001",
            "2026-08-12-retry-disclosed-001",
        ])
        # The exclusions really were members of the loaded corpus, just
        # not of the membership — they sit in their own context counts.
        self.assertEqual(stats["corpus"]["read_only_sessions"], 1)
        self.assertEqual(stats["corpus"]["crash_debris_sessions"], 1)

    def test_agrees_with_the_desk_definition(self) -> None:
        # The brief's measurement run over the same membership the
        # shipped reader sees must give the same sets.
        records = self._mixed_corpus()
        self._seed(records)
        membership = [r for r in records
                      if not bale_stats.is_read_only(r)
                      and not bale_stats.is_crash_debris(r)]
        reporting, occurred = _desk_definition(membership)
        stats = bale_stats.compute_stats(self.telemetry)
        compaction = stats["cross_checks"]["budget"]["compaction"]
        self.assertEqual(compaction["reporting_sessions"], len(reporting))
        self.assertEqual(compaction["occurred_sessions"], len(occurred))
        self.assertEqual(stats["members"]["compaction_occurred"],
                         sorted(occurred))

    def test_existing_budget_keys_unchanged(self) -> None:
        # Additive only: the pressure pass beside the new keys computes
        # exactly what it did before (every session here self-reports
        # "none" except the feedback-less and read-only/debris ones).
        self._seed(self._mixed_corpus())
        budget = bale_stats.compute_stats(
            self.telemetry)["cross_checks"]["budget"]
        self.assertEqual(set(budget),
                         {"pressure", "bailed_with_pressure_none",
                          "compaction"})
        self.assertEqual(budget["pressure"], {"none": 9, "unreported": 1})
        self.assertEqual(budget["bailed_with_pressure_none"], 0)

    def test_filters_reach_the_counts(self) -> None:
        records = self._mixed_corpus()
        # One doc-class session that discloses, so the work_class
        # filter has something to split.
        records.append(_one("2026-08-20-doc-true-001", "20",
                            _feedback(True, work_class="doc")))
        self._seed(records)

        doc = bale_stats.compute_stats(self.telemetry, work_class="doc")
        self.assertEqual(doc["cross_checks"]["budget"]["compaction"],
                         {"reporting_sessions": 1, "occurred_sessions": 1})
        self.assertEqual(doc["members"]["compaction_occurred"],
                         ["2026-08-20-doc-true-001"])

        code = bale_stats.compute_stats(self.telemetry, work_class="code")
        self.assertEqual(code["cross_checks"]["budget"]["compaction"],
                         {"reporting_sessions": 5, "occurred_sessions": 3})

        # --since 2026-08-05: drops obj-true, bool-true, obj-false.
        since = bale_stats.compute_stats(self.telemetry,
                                         since="2026-08-05")
        self.assertEqual(since["cross_checks"]["budget"]["compaction"],
                         {"reporting_sessions": 3, "occurred_sessions": 2})
        self.assertEqual(since["members"]["compaction_occurred"], [
            "2026-08-12-retry-disclosed-001",
            "2026-08-20-doc-true-001",
        ])

    def test_empty_corpus_reads_zero(self) -> None:
        stats = bale_stats.compute_stats(self.telemetry)
        self.assertEqual(stats["cross_checks"]["budget"]["compaction"],
                         {"reporting_sessions": 0, "occurred_sessions": 0})
        self.assertEqual(stats["members"]["compaction_occurred"], [])

    def test_hostile_self_reported_never_crashes(self) -> None:
        # A truthy non-dict self_reported — the one shape the desk's
        # definition would raise on — is tolerated: no report. Before
        # board 37 the budget pressure pass beside this reader raised
        # on it too and took the whole run down; it now buckets the
        # session as "unreported", and nothing else moves.
        self._seed([
            _one("2026-08-21-hostile-001", "21",
                 {"mechanical": {}, "self_reported": "compacted"}),
            _one("2026-08-22-true-001", "22", _feedback(True)),
        ])
        stats = bale_stats.compute_stats(self.telemetry)
        self.assertEqual(stats["cross_checks"]["budget"]["compaction"],
                         {"reporting_sessions": 1, "occurred_sessions": 1})
        self.assertEqual(stats["cross_checks"]["budget"]["pressure"],
                         {"none": 1, "unreported": 1})


# ---------------------------------------------------------------------------
# The read side, end to end
# ---------------------------------------------------------------------------

class CompactionReadSideE2ETest(unittest.TestCase):
    """`bale stats` carries the compaction counts in both output modes."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-cmp-e2e-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _seed(self, *, disclose: bool) -> None:
        telemetry = self.repo / "claude" / "telemetry"
        telemetry.mkdir(parents=True, exist_ok=True)
        records = [
            _one("2026-08-02-quiet-001", "02", _feedback({"occurred": False})),
            _one("2026-08-03-bare-001", "03", _feedback(False)),
            _one("2026-08-04-silent-001", "04", _feedback()),
        ]
        if disclose:
            records.append(_one("2026-08-05-compacted-001", "05",
                                _feedback({"occurred": True,
                                           "disclosure_ref": "notes.md"})))
        for record in records:
            (telemetry / f"{record['session_id']}.json").write_text(
                json.dumps(record, indent=2) + "\n", encoding="utf-8")

    def _stats(self, *args: str):
        result = run_bale(self.install, ["stats", *args], cwd=self.repo,
                          env=self.env)
        self.assertEqual(result.returncode, 0,
                         msg=f"stderr:\n{result.stderr}")
        return result

    def test_json_mode_carries_the_keys(self) -> None:
        self._seed(disclose=True)
        lines = [ln for ln in self._stats("--json").stdout.splitlines()
                 if ln.strip()]
        self.assertEqual(len(lines), 1,
                         msg="json stream discipline: one stdout line")
        payload = json.loads(lines[0])
        budget = payload["cross_checks"]["budget"]
        self.assertEqual(budget["compaction"],
                         {"reporting_sessions": 3, "occurred_sessions": 1})
        # Additive: the pre-existing budget keys are still there, with
        # their pre-existing meaning.
        self.assertEqual(budget["pressure"], {"none": 4})
        self.assertEqual(budget["bailed_with_pressure_none"], 0)
        self.assertEqual(payload["members"]["compaction_occurred"],
                         ["2026-08-05-compacted-001"])
        self.assertIn("bailed_with_pressure_none", payload["members"])

    def test_human_mode_renders_count_and_members(self) -> None:
        self._seed(disclose=True)
        out = self._stats().stdout
        lines = out.splitlines()
        self.assertIn("  cross-check compaction: disclosed 1 of 3 "
                      "reporting sessions", lines)
        # Beside the budget line: immediately under it.
        budget_at = next(i for i, ln in enumerate(lines)
                         if ln.startswith("  cross-check budget:"))
        self.assertTrue(lines[budget_at + 1].startswith(
            "  cross-check compaction:"),
            msg="the compaction line sits directly under the budget line")
        self.assertIn("corpus members:", out)
        self.assertIn("    compaction_occurred: 2026-08-05-compacted-001",
                      lines)

    def test_human_mode_quiet_corpus(self) -> None:
        # No disclosure: the count line still renders (a computed zero,
        # not a fabricated one), and no members line is invented.
        self._seed(disclose=False)
        out = self._stats().stdout
        # quiet and bare report; silent carries no key and does not.
        self.assertIn("  cross-check compaction: disclosed 0 of 2 "
                      "reporting sessions", out.splitlines())
        self.assertNotIn("compaction_occurred:", out)


if __name__ == "__main__":
    unittest.main()
