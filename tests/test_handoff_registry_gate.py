#!/usr/bin/env python3
"""`bale handoff` beside an open sibling session (board 73: session A's
lead 1 — the desk's leading hypothesis for "no adherence to forecast
disjointness"; session B's modernization at 0.4.28).

The contract these tests pin:

- ``cmd_handoff`` runs the same ADR-0015 forecast-disjointness gate
  ``cmd_pack`` runs — one implementation, ``run_forecast_disjointness_gate``
  in ``bale_pack``, lifted to module level for the purpose — against
  the forecast it inherits from the bailed-on session. A handoff
  forecasting hello.txt is admitted beside a read-only master (empty
  forecast) and beside a worker forecasting other.txt, and the passed
  line is journaled naming the open sids, exactly as pack's is.
- On an intersection it refuses pre-sid, naming the colliding session
  and the colliding pair, and its remedies are handoff's: narrow with
  ``--write``, apply the open session's response, or unlock it. No
  ``--supersedes`` — handoff never supersedes.
- Until 0.4.27 handoff refused while ANY session was open, before the
  bailout tarball was even opened and without reading a forecast —
  under the modern orchestration shape (a read-only master always
  open) that made the command mechanically unreachable, and the
  refusal named apply/unlock rather than the gap.

Session A's two ``@unittest.expectedFailure`` reproductions are the
acceptance tests; both decorators came off at 0.4.28 with their bodies
as written. A's diagnosis pin of the old refusal text was rewritten to
pin the collision refusal.

Run directly::

    python3 tests/test_handoff_registry_gate.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import unittest

from test_handoff_fixture import HandoffFixture

OPEN_REFUSAL_MARKER = "a session is already open"
PACK_GATE_MARKER = "forecast-disjointness gate passed"
HANDOFF_GATE_MARKER = ("forecast-disjointness gate passed (ADR-0015): "
                       "handoff write forecast")
COLLISION_MARKER = "handoff write forecast intersects"
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

    def test_handoff_admitted_beside_read_only_master(self) -> None:
        """Lead 1 (path 1, acceptance test), the modern orchestration
        shape: a bailout is applied (its session closes), a read-only
        master is open, and the handoff — forecasting hello.txt,
        disjoint from the master's empty forecast — is admitted the
        way pack is.

        Observed at 0.4.26: refused pre-tarball by the registry guard,
        naming the master sid and pointing at apply/unlock. Session B:
        decorator stripped, body as A wrote it."""
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

    def test_handoff_admitted_beside_scope_disjoint_worker(self) -> None:
        """Lead 1 (path 1, acceptance test) against a sibling with a
        non-empty forecast: the handoff's forecast (hello.txt) is
        disjoint from the worker's (other.txt); pack's gate admits
        this pair, handoff does too.

        Observed at 0.4.26: the same registry refusal, naming the
        worker sid. Session B: decorator stripped, body as A wrote it."""
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

    def test_admission_is_journaled_like_packs(self) -> None:
        """Pin: the passed gate is journaled into the new session's log
        with handoff's wording, naming the open sid it was disjoint
        from, plus the ADR-0006 several-open note — the same two lines
        pack writes."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])
        master = self.open_read_only_master()

        result = self.handoff(tarball)
        self.assert_ok(result, "handoff beside the read-only master")
        self.assertIn(HANDOFF_GATE_MARKER, result.stdout)
        self.assertIn(f"1 open session(s): {master}", result.stdout)
        new_sid = [s for s in self.open_sids() if s != master][0]
        journal = (self.repo / ".bale" / "logs" / f"{new_sid}.log").read_text()
        self.assertIn(HANDOFF_GATE_MARKER, journal)
        self.assertIn("sid disambiguation for them is deferred (ADR-0006)",
                      journal)

    def test_refusal_is_a_forecast_collision(self) -> None:
        """Pin (rewritten at 0.4.28 from the registry-guard pin): a
        handoff whose inherited forecast intersects an open session's
        refuses at the ADR-0015 gate — naming the open sid, the
        colliding pair, and handoff's own remedies (--write, apply,
        unlock; never --supersedes) — pre-sid, burning no NNN and
        opening no session. The old refusal text is gone."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])
        # A worker forecasting the very file the handoff inherits.
        r = self.pack(slug="colliding-worker",
                      goal="colliding worker session (fixture)")
        self.assert_ok(r, "colliding worker pack")
        worker = self.open_sids()[0]
        self.assertEqual(self.recorded_scope(worker), ["hello.txt"])
        peek = self.peeked_sid()

        combined = self.assert_refused(self.handoff(tarball),
                                       "handoff beside a colliding session")
        self.assertIn(COLLISION_MARKER, combined)
        self.assertIn(worker, combined)
        self.assertIn("hello.txt ~ hello.txt", combined)
        self.assertIn("ADR-0015", combined)
        self.assertIn("Narrow this handoff's forecast with --write", combined)
        self.assertIn("inherits the bailed-on session's recorded forecast",
                      combined)
        self.assertNotIn("--supersedes", combined)
        self.assertNotIn(OPEN_REFUSAL_MARKER, combined)
        # Nothing consumed: the same sid is still the next allocation
        # and only the worker is open.
        self.assertEqual(self.peeked_sid(), peek)
        self.assertEqual(self.open_sids(), [worker])

        # --write is the named remedy: a disjoint declaration is admitted.
        self.commit_file(SIBLING_FILE, "other\n")
        r = self.handoff(tarball, "--write", SIBLING_FILE)
        self.assert_ok(r, "handoff narrowed past the collision")
        self.assertEqual(len(self.open_sids()), 2)


if __name__ == "__main__":
    unittest.main()
