#!/usr/bin/env python3
"""`bale handoff` and the write forecast (board 73: session A's leads 2
and 4 and the failure class that best matched row 73's own wording —
"apply trouble, no adherence to forecast disjointness"; session B's
modernization at 0.4.28, ADR-0015).

The contract these tests pin:

- **Forecast inheritance (path 5).** A handoff inherits the bailed-on
  session's recorded forecast exactly — a parent packed with
  ``--write other.txt`` hands off a session forecasting ``other.txt``
  whatever its bailout's reading plan cites, and the resumed work
  landing there applies without an override. The reading plan is the
  READ set only: it still ships in ``context/`` and gates nothing. A
  read-only parent (recorded ``[]``) resumes read-only. Until 0.4.27
  handoff recorded the reading plan's file set as the forecast —
  ADR-0007's read-set-is-scope conflation, retired for pack at v0.4.1
  and never re-based on this path — and the resumed work refused at
  apply as own-forecast drift.
- **The fallback (path 4).** Only a missing or unreadable parent record
  falls back to the reading-plan file set — ``["."]`` when the plan
  cites nothing — and that fallback is an undeclared forecast: it
  takes the bare-pack rule, and the summary says which branch fired.
- **The flag family (path 6).** ``--write`` overrides the inheritance
  with pack's grammar; ``--read-only`` spells the empty forecast;
  ``--checkpoint-file`` is pinned in test_handoff_checkpoint_gates.py.
  ``--include``, ``--constraint``, ``--out-of-scope`` and
  ``--readme-file`` still exit 2 at argparse — deliberately, until a
  use case argues for them — and the sweep here pins that.
- **Lead 4, NOT reproduced (unchanged).** The handoff-built request
  manifest is modern: ``provenance.work_class`` stamps the "mixed"
  default and ``provenance.base_files`` carries per-file HEAD hashes
  across the forecast.

Session A shipped the path-5 and path-6 cases as
``@unittest.expectedFailure``; both decorators came off at 0.4.28.
The diagnosis pin that asserted the swap's exact artifacts was
rewritten to assert the inherited outcome, and the lead-4 pin moved
from the whole-tree fallback to the inherited forecast (the fallback
has its own case behind ``drop_parent_record``).

Run directly::

    python3 tests/test_handoff_forecast.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import unittest

from test_handoff_fixture import HandoffFixture

PARENT_FORECAST_FILE = "other.txt"
DRIFT_REJECT_PHRASE = "own-forecast drift"
UNRECOGNIZED_PHRASE = "unrecognized arguments"
BASE_DRIFT_STAMP_PHRASE = "provenance: base-drift stamp covers"
INHERITED_FORECAST_PHRASE = "forecast from"
FALLBACK_PHRASE = "fell back to the reading-plan file set"
UNDECLARED_PHRASE = "undeclared"
CONTRADICTION_PHRASE = "--write and --read-only are contradictory"


class HandoffForecastTest(HandoffFixture):
    """The forecast handoff records, versus the one the parent declared."""

    def bailed_parent_with_narrow_forecast(self):
        """Parent forecasts other.txt (read set hello.txt + other.txt);
        the bailout's reading plan cites hello.txt only — the shape a
        bailing worker produces when it names what to READ next, not
        where the work lands."""
        self.commit_file(PARENT_FORECAST_FILE, "other\n")
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"],
            pack_extra=("--include", PARENT_FORECAST_FILE,
                        "--write", PARENT_FORECAST_FILE))
        self.assertEqual(self.recorded_scope(bailed_sid),
                         [PARENT_FORECAST_FILE],
                         msg="precondition: the parent recorded its --write")
        return bailed_sid, tarball

    def test_resumed_work_lands_on_the_parent_forecast(self) -> None:
        """The row-73 shape (path 5, the acceptance test): the resumed
        session's response lands on the path the PARENT forecast.
        Under ADR-0015 the forecast is the ask; a handoff continuing
        the same goal under the same ask carries it, so the apply
        lands without an override and the new session's record equals
        the parent's.

        Observed at 0.4.26: the handoff recorded ["hello.txt"] (the
        reading plan), and the apply refused with the own-forecast
        drift REJECT naming other.txt. Session B: decorator stripped;
        the record-equality assertion moved ahead of the apply, since
        a PASS merge wipes the session directory it reads."""
        bailed_sid, tarball = self.bailed_parent_with_narrow_forecast()

        result = self.handoff(tarball)
        self.assert_ok(result, "handoff of the narrow-forecast parent")
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid),
                         self.recorded_scope(bailed_sid),
                         msg="the handoff carries the parent's forecast")

        applied = self.apply_normal_response(
            new_sid, path=PARENT_FORECAST_FILE,
            data=b"the resumed work, landing where the parent forecast\n")
        self.assert_ok(applied, "apply of the resumed work")
        self.assertEqual(self.open_sids(), [])

    def test_inheritance_is_visible_in_the_new_session_record(self) -> None:
        """Pin (rewritten at 0.4.28 from the swap's diagnosis pin): the
        inheritance is loud at handoff time — the `inherited:` row
        names the forecast beside the goal and the session log names
        the branch — and the new session's scope.json,
        manifest.resolved_scope, and base_files all carry the parent's
        forecast, while context_included still carries the reading
        plan's file: read set and forecast are two values."""
        bailed_sid, tarball = self.bailed_parent_with_narrow_forecast()

        result = self.handoff(tarball)
        self.assert_ok(result, "handoff of the narrow-forecast parent")
        combined = result.stdout + result.stderr
        self.assertIn(f"inherited:  goal from {bailed_sid} (verbatim); "
                      f"{INHERITED_FORECAST_PHRASE} {bailed_sid} "
                      f"({PARENT_FORECAST_FILE})", combined,
                      msg="the summary names the goal AND the forecast")
        self.assertIn("write forecast (inherited):", combined,
                      msg="the log names the branch taken")
        self.assertNotIn(FALLBACK_PHRASE, combined)

        new_sid = self.sole_new_open_sid(bailed_sid)
        manifest = self.request_manifest(new_sid)
        self.assertEqual(self.recorded_scope(new_sid), [PARENT_FORECAST_FILE])
        self.assertEqual(manifest["resolved_scope"], [PARENT_FORECAST_FILE])
        self.assertEqual(list(manifest["provenance"]["base_files"]),
                         [PARENT_FORECAST_FILE])
        self.assertEqual(manifest["context_included"],
                         ["context/handoff.md", "context/hello.txt"],
                         msg="the reading plan still ships as the read set")

        applied = self.apply_normal_response(
            new_sid, path=PARENT_FORECAST_FILE, data=b"landing\n")
        self.assert_ok(applied, "apply onto the parent's path")
        self.assertEqual(self.open_sids(), [])

    def test_read_only_parent_hands_off_read_only(self) -> None:
        """A parent packed --read-only records []; its bailout hands off
        a session that records [] too — it could not have landed work,
        so its child cannot either (the desk's ruling, board 73). The
        summary spells the inherited empty forecast out."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"], pack_extra=("--read-only",))
        self.assertEqual(self.recorded_scope(bailed_sid), [],
                         msg="precondition: the parent recorded the empty forecast")

        result = self.handoff(tarball)
        self.assert_ok(result, "handoff of the read-only parent")
        self.assertIn(f"{INHERITED_FORECAST_PHRASE} {bailed_sid} "
                      f"(empty: read-only)", result.stdout)

        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid), [])
        manifest = self.request_manifest(new_sid)
        self.assertEqual(manifest["resolved_scope"], [])
        self.assertEqual(manifest["provenance"]["base_files"], {})

        applied = self.apply_normal_response(
            new_sid, path="hello.txt", data=b"landing\n")
        combined = self.assert_refused(applied, "apply under the empty forecast")
        self.assertIn(DRIFT_REJECT_PHRASE, combined)

    def test_write_flag_is_accepted(self) -> None:
        """Lead 2 (path 6, acceptance test): pack's ADR-0015 forecast
        flag on handoff. Observed at 0.4.26: exit 2, "unrecognized
        arguments". Session B: decorator stripped, body as A wrote it."""
        bailed_sid, tarball = self.bailed_parent_with_narrow_forecast()

        result = self.handoff(tarball, "--write", PARENT_FORECAST_FILE)

        self.assert_ok(result, "handoff --write")
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid), [PARENT_FORECAST_FILE])

    def test_write_overrides_the_inheritance(self) -> None:
        """--write is the override for the case where the bailing
        worker's handoff.md argues the ask changed: the parent
        forecast other.txt, the handoff declares hello.txt, and the
        child records the declaration — visibly."""
        bailed_sid, tarball = self.bailed_parent_with_narrow_forecast()

        result = self.handoff(tarball, "--write", "hello.txt")
        self.assert_ok(result, "handoff --write hello.txt")
        self.assertIn("forecast overridden by --write (hello.txt)",
                      result.stdout)
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid), ["hello.txt"])
        self.assertEqual(list(self.request_manifest(new_sid)
                              ["provenance"]["base_files"]), ["hello.txt"])

    def test_write_grammar_matches_pack(self) -> None:
        """--write carries pack's refusals: a non-existent path refuses
        with ADR-0014's rule, and --write beside --read-only refuses as
        contradictory — both pre-tarball, nothing consumed."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])
        peek = self.peeked_sid()

        combined = self.assert_refused(
            self.handoff(tarball, "--write", "missing.txt"),
            "handoff --write on a missing path")
        self.assertIn("--write path does not exist: missing.txt", combined)

        combined = self.assert_refused(
            self.handoff(tarball, "--write", "hello.txt", "--read-only"),
            "handoff --write --read-only")
        self.assertIn(CONTRADICTION_PHRASE, combined)

        self.assertEqual(self.open_sids(), [])
        self.assertEqual(self.peeked_sid(), peek)

    def test_read_only_flag_overrides_the_inheritance(self) -> None:
        """--read-only spells the empty forecast on handoff as on pack:
        the child records [] whatever the parent recorded."""
        bailed_sid, tarball = self.bailed_parent_with_narrow_forecast()

        result = self.handoff(tarball, "--read-only")
        self.assert_ok(result, "handoff --read-only")
        self.assertIn("forecast declared empty by --read-only", result.stdout)
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid), [])

    def test_remaining_pack_flags_are_rejected_at_argparse(self) -> None:
        """Pin (sweep narrowed at 0.4.28): the four pack flags handoff
        deliberately still lacks exit 2 before any gate runs — no
        session state, nothing consumed. --write, --read-only and
        --checkpoint-file left this sweep when they landed."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])
        peek = self.peeked_sid()
        for flags in (["--include", "hello.txt"],
                      ["--constraint", "c"],
                      ["--out-of-scope", "o"],
                      ["--readme-file", "README.md"]):
            with self.subTest(flags=flags):
                result = self.handoff(tarball, *flags)
                self.assertEqual(result.returncode, 2,
                                 msg=f"{flags}: {result.stdout}{result.stderr}")
                self.assertIn(UNRECOGNIZED_PHRASE, result.stderr)
        self.assertEqual(self.open_sids(), [])
        self.assertEqual(self.peeked_sid(), peek)


class HandoffManifestIsModernTest(HandoffFixture):
    """Lead 4: is the handoff-built request "old syntax"? No."""

    def test_planless_handoff_stamps_modern_provenance_and_applies(self):
        """NOT reproduced (passing; re-pointed at 0.4.28 from the
        whole-tree fallback to the inherited forecast): a plan-less
        handoff whose parent recorded hello.txt stamps the "mixed"
        work_class default and a base_files map over that forecast
        whose hash matches HEAD, ships handoff.md only, and a response
        modifying hello.txt applies with the base-drift gate satisfied."""
        self.commit_file(PARENT_FORECAST_FILE, "other\n")
        bailed_sid, tarball = self.packed_and_bailed(reading_plan_paths=None)

        result = self.handoff(tarball)
        self.assert_ok(result, "plan-less handoff")
        self.assertIn(BASE_DRIFT_STAMP_PHRASE, result.stdout)

        new_sid = self.sole_new_open_sid(bailed_sid)
        manifest = self.request_manifest(new_sid)
        self.assertEqual(manifest["context_included"], ["context/handoff.md"])
        self.assertEqual(self.recorded_scope(new_sid), ["hello.txt"])
        prov = manifest["provenance"]
        self.assertEqual(prov["work_class"], "mixed")
        self.assertIsNone(prov["checkpoint"])
        self.assertFalse(prov["checkpoint_scope_admitted"])
        self.assertNotIn("checkpoint_waived", prov)
        self.assertEqual(prov["base_files"],
                         {"hello.txt": self.head_sha256("hello.txt")},
                         msg="base_files covers the inherited forecast only")

        applied = self.apply_normal_response(
            new_sid, path="hello.txt", data=b"landing\n")
        self.assert_ok(applied, "apply under the inherited forecast")
        self.assertEqual(self.open_sids(), [])

    def test_planless_handoff_without_parent_record_forecasts_whole_tree(self):
        """The fallback (path 4): with the parent's record dropped, a
        plan-less handoff forecasts ["."] — undeclared, and said so —
        stamps base_files across the whole tree, and a response
        modifying any file applies."""
        self.commit_file(PARENT_FORECAST_FILE, "other\n")
        bailed_sid, tarball = self.packed_and_bailed(reading_plan_paths=None)
        self.drop_parent_record(bailed_sid)

        result = self.handoff(tarball)
        self.assert_ok(result, "plan-less handoff with no parent record")
        self.assertIn(f"session {bailed_sid} has no recorded scope",
                      result.stdout)
        self.assertIn(FALLBACK_PHRASE, result.stdout)
        self.assertIn(UNDECLARED_PHRASE, result.stdout)
        self.assertIn("write forecast (fallback):", result.stdout)

        new_sid = self.sole_new_open_sid(bailed_sid)
        manifest = self.request_manifest(new_sid)
        self.assertEqual(self.recorded_scope(new_sid), ["."])
        self.assertEqual(manifest["resolved_scope"], ["."])
        base_files = manifest["provenance"]["base_files"]
        for rel in ("hello.txt", PARENT_FORECAST_FILE):
            self.assertEqual(base_files.get(rel), self.head_sha256(rel),
                             msg=f"base_files[{rel!r}] is the HEAD hash")

        applied = self.apply_normal_response(
            new_sid, path=PARENT_FORECAST_FILE, data=b"landing\n")
        self.assert_ok(applied, "apply under the whole-tree fallback")
        self.assertEqual(self.open_sids(), [])

    def test_plan_citing_file_without_parent_record_forecasts_the_plan(self):
        """The fallback's other shape: no parent record, plan cites
        hello.txt — the child forecasts hello.txt as today's behavior
        did, marked undeclared."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])
        self.drop_parent_record(bailed_sid)

        result = self.handoff(tarball)
        self.assert_ok(result, "handoff with no parent record")
        self.assertIn(f"{FALLBACK_PHRASE} (hello.txt), {UNDECLARED_PHRASE}",
                      result.stdout)
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid), ["hello.txt"])


if __name__ == "__main__":
    unittest.main()
