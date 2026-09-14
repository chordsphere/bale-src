#!/usr/bin/env python3
"""`bale handoff` and the write forecast (board 73, session A — leads 2
and 4, and the failure class that best matches row 73's own wording,
"apply trouble, no adherence to forecast disjointness").

Observed against bin/ at 0.4.26:

- **The forecast swap (unpredicted, reproduced).** Handoff never reads
  the bailed-on session's recorded forecast. It records the reading
  plan's resolved file set — the READ set the bailing worker asked the
  next session to load — as the new session's write forecast ("the
  read set and the forecast coincide by construction", cmd_handoff).
  A parent packed with ``--write other.txt`` whose bailout's reading
  plan cites ``hello.txt`` hands off to a session forecasting
  ``hello.txt``; the resumed work landing on ``other.txt`` — the very
  path the parent forecast — refuses at apply as own-forecast drift.
  That is ADR-0007's read-set-is-scope conflation, retired for pack by
  ADR-0015 at v0.4.1, still live on the handoff path. The apply-side
  refusal is the operator-visible failure; the swap is the cause.
- **The argv surface (lead 2, reproduced as a design-era mismatch).**
  ``--write`` — the ADR-0015 forecast flag pack carries — exits 2 at
  argparse; so do ``--include``, ``--read-only``, ``--constraint``,
  ``--out-of-scope``, ``--readme-file`` and ``--checkpoint-file`` (the
  last is pinned in test_handoff_checkpoint_gates.py). Handoff's only
  scope input is the bailout's prose reading plan.
- **Lead 4, NOT reproduced.** The handoff-built request manifest is
  modern: ``provenance.work_class`` stamps the "mixed" default,
  ``provenance.base_files`` carries per-file HEAD hashes across the
  forecast (the board-41 stamp), and a whole-tree session applies
  cleanly with the base-drift gate satisfied. "Old syntax" is not a
  stale manifest; it is the argv surface above.

Breaks ship ``@unittest.expectedFailure`` asserting pack parity; the
non-reproduction is a plain passing test. ``test_handoff_happy.py``
already pins the swap's current behavior from the inside (reading-plan
set IS the forecast), so no control is duplicated here. Fix or retire
is session B's ruling, not this file's.

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

    @unittest.expectedFailure
    def test_resumed_work_lands_on_the_parent_forecast(self) -> None:
        """The row-73 shape: the resumed session's response lands on
        the path the PARENT forecast. Under ADR-0015 the forecast is
        the ask; a handoff continuing the same goal under the same
        ask should carry it, so the apply should land without an
        override and the new session's record should equal the
        parent's.

        Observed at 0.4.26: the handoff records ["hello.txt"] (the
        reading plan), and the apply refuses with the own-forecast
        drift REJECT naming other.txt."""
        bailed_sid, tarball = self.bailed_parent_with_narrow_forecast()

        result = self.handoff(tarball)
        self.assert_ok(result, "handoff of the narrow-forecast parent")
        new_sid = self.sole_new_open_sid(bailed_sid)

        applied = self.apply_normal_response(
            new_sid, path=PARENT_FORECAST_FILE,
            data=b"the resumed work, landing where the parent forecast\n")
        self.assert_ok(applied, "apply of the resumed work")
        self.assertEqual(self.recorded_scope(new_sid),
                         self.recorded_scope(bailed_sid),
                         msg="the handoff carries the parent's forecast")

    def test_swap_is_visible_in_the_new_session_record(self) -> None:
        """Diagnosis pin (passing): the swap is silent at handoff time
        — exit 0, no note that the parent's forecast was dropped — and
        the new session's scope.json, manifest.resolved_scope, and
        base_files all carry the reading plan's set, not the parent's.
        The apply-side REJECT is the first the operator hears of it."""
        bailed_sid, tarball = self.bailed_parent_with_narrow_forecast()

        result = self.handoff(tarball)
        self.assert_ok(result, "handoff of the narrow-forecast parent")
        combined = result.stdout + result.stderr
        self.assertNotIn(PARENT_FORECAST_FILE, combined,
                         msg="handoff output never mentions the parent's "
                             "forecast path")
        self.assertIn("inherited:  goal from", combined,
                      msg="the summary names the goal as the one thing "
                          "inherited; the forecast is not among them")
        self.assertEqual(self.recorded_scope(bailed_sid),
                         [PARENT_FORECAST_FILE],
                         msg="the parent's record survives — it was "
                             "available to read and was not")

        new_sid = self.sole_new_open_sid(bailed_sid)
        manifest = self.request_manifest(new_sid)
        self.assertEqual(self.recorded_scope(new_sid), ["hello.txt"])
        self.assertEqual(manifest["resolved_scope"], ["hello.txt"])
        self.assertEqual(list(manifest["provenance"]["base_files"]),
                         ["hello.txt"])

        applied = self.apply_normal_response(
            new_sid, path=PARENT_FORECAST_FILE, data=b"landing\n")
        combined = self.assert_refused(applied, "apply onto the parent's path")
        self.assertIn(DRIFT_REJECT_PHRASE, combined)
        self.assertIn(PARENT_FORECAST_FILE, combined)
        self.assertEqual(self.open_sids(), [new_sid],
                         msg="the refusal leaves the session open")

    @unittest.expectedFailure
    def test_write_flag_is_accepted(self) -> None:
        """Lead 2: pack's ADR-0015 forecast flag. Handoff has no way
        to declare where the resumed work lands other than the
        bailing worker's prose; `--write` is the flag that would.

        Observed at 0.4.26: exit 2, "unrecognized arguments"."""
        bailed_sid, tarball = self.bailed_parent_with_narrow_forecast()

        result = self.handoff(tarball, "--write", PARENT_FORECAST_FILE)

        self.assert_ok(result, "handoff --write")
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid), [PARENT_FORECAST_FILE])

    def test_pack_flags_are_rejected_at_argparse(self) -> None:
        """Diagnosis pin (passing): the flag family pack grew after
        handoff's surface was frozen all exit 2 before any gate runs —
        no session state, nothing consumed. The operator's "old
        syntax" recollection is consistent with any of these."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])
        peek = self.peeked_sid()
        for flags in (["--write", "hello.txt"],
                      ["--include", "hello.txt"],
                      ["--read-only"],
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

    def test_whole_tree_handoff_stamps_modern_provenance_and_applies(self):
        """NOT reproduced (passing): a plan-less handoff stamps the
        "mixed" work_class default and a base_files map over the whole
        tree whose hashes match HEAD, and a response modifying a file
        under that forecast applies with the base-drift gate satisfied."""
        self.commit_file(PARENT_FORECAST_FILE, "other\n")
        bailed_sid, tarball = self.packed_and_bailed(reading_plan_paths=None)

        result = self.handoff(tarball)
        self.assert_ok(result, "plan-less handoff")
        self.assertIn(BASE_DRIFT_STAMP_PHRASE, result.stdout)

        new_sid = self.sole_new_open_sid(bailed_sid)
        prov = self.request_manifest(new_sid)["provenance"]
        self.assertEqual(prov["work_class"], "mixed")
        self.assertIsNone(prov["checkpoint"])
        self.assertFalse(prov["checkpoint_scope_admitted"])
        self.assertNotIn("checkpoint_waived", prov)
        base_files = prov["base_files"]
        for rel in ("hello.txt", PARENT_FORECAST_FILE):
            self.assertEqual(base_files.get(rel), self.head_sha256(rel),
                             msg=f"base_files[{rel!r}] is the HEAD hash")

        applied = self.apply_normal_response(
            new_sid, path=PARENT_FORECAST_FILE, data=b"landing\n")
        self.assert_ok(applied, "apply under the whole-tree forecast")
        self.assertEqual(self.open_sids(), [])


if __name__ == "__main__":
    unittest.main()
