#!/usr/bin/env python3
"""`bale handoff` beside an open sibling session (board 73, session A,
lead 1 — the desk's leading hypothesis for "no adherence to forecast
disjointness").

What this suite establishes, observed against bin/ at 0.4.26:

- ``cmd_handoff`` refuses while ANY session is open — it reads the
  ADR-0006 registry and fails on a non-empty list, before the bailout
  tarball is even opened. It never consults the open sessions'
  recorded forecasts. The refusal text names the open sid and points
  at ``bale apply`` / ``bale unlock``; it never mentions forecasts,
  ``--write``, or ADR-0015, so an operator has no signal that the
  refusal is a design-era gap rather than a real conflict.
- ``cmd_pack`` on the identical forecast is admitted beside the same
  open session by the ADR-0015 forecast-disjointness gate. The
  controls here pin that parity gap from pack's side.
- The consequence in the modern orchestration shape: a read-only
  master (empty forecast, conflicts with nothing) is always open, so
  handoff can never run under it.

Each break ships ``@unittest.expectedFailure`` asserting the pack-parity
expectation (handoff admitted beside a forecast-disjoint session), so
discovery stays green and the reproduction flips to an unexpected
success the day the gate is re-based. The controls are plain passing
tests. The desk's fix-or-retire ruling is session B's; nothing here
proposes one.

Run directly::

    python3 tests/test_handoff_registry_gate.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import unittest

from test_handoff_fixture import HandoffFixture

OPEN_REFUSAL_MARKER = "a session is already open"
PACK_GATE_MARKER = "forecast-disjointness gate passed"
SIBLING_FILE = "other.txt"


class HandoffRegistryGateTest(HandoffFixture):
    """The registry guard in cmd_handoff versus pack's disjointness gate."""

    # -- fixture ---------------------------------------------------------

    def open_read_only_master(self) -> str:
        """Open the modern orchestration shape's master: an empty
        forecast, disjoint from everything by construction."""
        r = self.pack("--read-only", slug="master",
                      goal="read-only master session (fixture)")
        self.assert_ok(r, "read-only master pack")
        opens = self.open_sids()
        self.assertEqual(len(opens), 1, msg=f"open sessions: {opens}")
        self.assertEqual(self.recorded_scope(opens[0]), [],
                         msg="a read-only master records the empty forecast")
        return opens[0]

    def open_disjoint_worker(self) -> str:
        """Open a worker whose forecast is one file the handoff's
        reading plan does not cite."""
        self.commit_file(SIBLING_FILE, "other\n")
        r = self.pack("--include", SIBLING_FILE, "--write", SIBLING_FILE,
                      slug="worker",
                      goal="scope-disjoint worker session (fixture)")
        self.assert_ok(r, "disjoint worker pack")
        opens = self.open_sids()
        self.assertEqual(len(opens), 1, msg=f"open sessions: {opens}")
        self.assertEqual(self.recorded_scope(opens[0]), [SIBLING_FILE])
        return opens[0]

    # -- controls: pack's gate admits the same forecast ------------------

    def test_control_pack_admitted_beside_read_only_master(self) -> None:
        """A pack forecasting hello.txt — the value handoff would
        forecast from a plan citing hello.txt — is admitted beside an
        open read-only master by the ADR-0015 gate."""
        master = self.open_read_only_master()
        r = self.pack(slug="beside-master")
        self.assert_ok(r, "pack beside the read-only master")
        self.assertIn(PACK_GATE_MARKER, r.stdout)
        self.assertIn(master, r.stdout,
                      msg="the gate journals the open sid it was disjoint from")
        self.assertEqual(len(self.open_sids()), 2)

    def test_control_pack_admitted_beside_disjoint_worker(self) -> None:
        """Same control against a sibling with a real (non-empty)
        forecast: hello.txt is disjoint from other.txt, so pack is
        admitted."""
        worker = self.open_disjoint_worker()
        r = self.pack(slug="beside-worker")
        self.assert_ok(r, "pack beside the disjoint worker")
        self.assertIn(PACK_GATE_MARKER, r.stdout)
        self.assertIn(worker, r.stdout)
        self.assertEqual(len(self.open_sids()), 2)

    # -- the reproductions -----------------------------------------------

    @unittest.expectedFailure
    def test_handoff_admitted_beside_read_only_master(self) -> None:
        """Lead 1, the modern orchestration shape: a bailout is applied
        (its session closes), a read-only master is open, and the
        handoff — forecasting hello.txt, disjoint from the master's
        empty forecast — should be admitted the way pack is.

        Observed at 0.4.26: refused pre-tarball by the registry guard,
        naming the master sid and pointing at apply/unlock. No session
        state is created."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])
        master = self.open_read_only_master()

        result = self.handoff(tarball)

        self.assert_ok(result, "handoff beside the read-only master")
        opens = self.open_sids()
        self.assertEqual(len(opens), 2, msg=f"open sessions: {opens}")
        new_sid = [s for s in opens if s != master][0]
        self.assertNotEqual(new_sid, bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid), ["hello.txt"])

    @unittest.expectedFailure
    def test_handoff_admitted_beside_scope_disjoint_worker(self) -> None:
        """Lead 1 against a sibling with a non-empty forecast: the
        handoff's forecast (hello.txt) is disjoint from the worker's
        (other.txt); pack's gate admits this pair, handoff should too.

        Observed at 0.4.26: the same registry refusal, naming the
        worker sid. The worker's recorded forecast is never read."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])
        worker = self.open_disjoint_worker()

        result = self.handoff(tarball)

        self.assert_ok(result, "handoff beside the disjoint worker")
        opens = self.open_sids()
        self.assertEqual(len(opens), 2, msg=f"open sessions: {opens}")
        new_sid = [s for s in opens if s != worker][0]
        self.assertNotEqual(new_sid, bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid), ["hello.txt"])

    def test_refusal_is_the_registry_guard_not_a_forecast_collision(self):
        """Diagnosis pin (plain, passing): when handoff refuses beside
        an open session today, the refusal is the pre-tarball registry
        guard — it names the open sid and the apply/unlock remedies,
        burns no NNN, opens no session — and says nothing about
        forecasts. This is the line the operator saw; it is what makes
        the failure read as "apply trouble" rather than a gate."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])
        master = self.open_read_only_master()
        peek = self.peeked_sid()

        combined = self.assert_refused(self.handoff(tarball),
                                       "handoff beside an open session")
        self.assertIn(OPEN_REFUSAL_MARKER, combined)
        self.assertIn(master, combined)
        self.assertIn("bale unlock", combined)
        for absent in ("forecast", "ADR-0015", "disjoint", "--write"):
            self.assertNotIn(absent, combined,
                             msg=f"the refusal must not mention {absent!r}: "
                                 f"the guard never looked at forecasts")
        # Nothing consumed: the same sid is still the next allocation
        # and only the master is open.
        self.assertEqual(self.peeked_sid(), peek)
        self.assertEqual(self.open_sids(), [master])


if __name__ == "__main__":
    unittest.main()
