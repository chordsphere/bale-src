#!/usr/bin/env python3
"""`bale handoff` in a checkpoint-configured project (board 73, session
A, lead 3 — and one failure class the leads did not predict).

Two gates run on the handoff path, both shared with pack and both
sited pre-sid: the blindness pre-flight (``checkpoint_blindness_preflight``,
against the reading-plan forecast) and, for a ``{sid}``-templated base,
the resolved-existence pre-flight (``checkpoint_resolved_preflight``,
against a peeked sid). Observed against bin/ at 0.4.26:

- **{sid} base, plan cites a file (lead 3, reproduced).** The blindness
  gate passes; the resolved-existence gate refuses because HEAD has no
  checkpoint at ``claude/checkpoints/<peeked-sid>.sh``. The refusal's
  FIRST-listed remedy is ``--checkpoint-file`` — a flag handoff's
  argparse does not have, so following the remedy exits 2 with
  "unrecognized arguments". The second remedy (hand-commit at the
  named path, re-run) works; that non-break ships as a passing test.
- **Literal base, plan cites a file (lead 3's other half, NOT
  reproduced).** Handoff proceeds, stamps the checkpoint, and the
  resulting session applies with the checkpoint running. Passing test.
- **Plan-less handoff in a literal-base project (unpredicted).** The
  ``[\".\"]`` whole-tree fallback is evaluated with ``forecast_declared``
  at its True default, so it covers the checkpoint and the blindness
  gate refuses — while a bare ``bale pack`` (no --include, no --write)
  in the same project is admitted, because v0.4.9 passes
  ``forecast_declared=False`` for the include-set compatibility default
  and auto-excludes the oracle at the walk. The comment in cmd_handoff
  ("refuses without the flag, the same way a default whole-tree pack
  does") describes pre-v0.4.9 pack. The refusal's remedy ("re-bail with
  a reading plan that does not cite the checkpoint") misdiagnoses: the
  plan cited nothing.
- **Plan-less handoff in a {sid}-base project.** Both gates stack:
  blindness refuses; with ``--allow-checkpoint-in-scope`` the
  resolved-existence gate refuses next. Pinned as the two-gate
  variant of the same unpredicted class.

Breaks ship ``@unittest.expectedFailure`` asserting pack parity;
controls and non-reproductions are plain passing tests. Fix or retire
is session B's ruling, not this file's.

Run directly::

    python3 tests/test_handoff_checkpoint_gates.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import unittest

from test_handoff_fixture import (
    LITERAL_BASE,
    SID_BASE,
    HandoffFixture,
)

MISSING_RESOLVED_PHRASE = "per-session blind checkpoint missing"
FLAG_REMEDY_PHRASE = "--checkpoint-file"
BLINDNESS_PHRASE = "write forecast covers the blind checkpoint"
BLINDNESS_PASSED_PHRASE = "checkpoint blindness gate passed"
ADMITTED_PHRASE = "checkpoint blindness admitted by --allow-checkpoint-in-scope"
CHECKPOINT_STAMPED_PHRASE = "provenance: checkpoint stamped"
CHECKPOINT_VERIFIED_PHRASE = "checkpoint provenance stamp verified"


class HandoffSidBaseTest(HandoffFixture):
    """A ``{sid}``-templated [validation] base — bale-src's own shape."""

    def setUp(self) -> None:
        super().setUp()
        self.configure_checkpoint(SID_BASE)
        # The parent pack needs its own per-session oracle; pack can
        # deliver it in one run via --checkpoint-file. Handoff cannot —
        # which is the whole of this class.
        self.source = self.write_checkpoint_source()

    def resolved_for(self, sid: str) -> str:
        return SID_BASE.replace("{sid}", sid)

    def bailed_with_plan(self):
        return self.packed_and_bailed(
            reading_plan_paths=["hello.txt"],
            pack_extra=("--checkpoint-file", str(self.source)))

    def test_hand_commit_at_peeked_sid_proceeds(self) -> None:
        """The non-break half (passing): the refusal's second remedy —
        commit the planner's checkpoint at the resolved path by hand,
        re-run — converges on the same sid and the handoff proceeds,
        stamping the resolved checkpoint into provenance."""
        bailed_sid, tarball = self.bailed_with_plan()
        peek = self.peeked_sid()

        # Without the commit: refused at the resolved-existence gate,
        # naming exactly the path the peek predicts; nothing consumed.
        combined = self.assert_refused(self.handoff(tarball),
                                       "handoff with no committed checkpoint")
        self.assertIn(MISSING_RESOLVED_PHRASE, combined)
        self.assertIn(self.resolved_for(peek), combined)
        self.assertEqual(self.open_sids(), [])
        self.assertEqual(self.peeked_sid(), peek,
                         msg="a pre-sid refusal must not burn an NNN")

        self.commit_checkpoint(self.resolved_for(peek))
        result = self.handoff(tarball)
        self.assert_ok(result, "handoff after the hand-commit")
        self.assertIn(CHECKPOINT_STAMPED_PHRASE, result.stdout)

        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(new_sid, peek,
                         msg="the remedy loop converges on the peeked sid")
        prov = self.request_manifest(new_sid)["provenance"]
        self.assertEqual(prov["checkpoint"]["path"], self.resolved_for(new_sid))
        self.assertEqual(prov["checkpoint"]["sha256"],
                         self.head_sha256(self.resolved_for(new_sid)))

    @unittest.expectedFailure
    def test_refusal_named_remedy_is_accepted(self) -> None:
        """Lead 3, reproduced: the resolved-existence refusal's first
        remedy is `--checkpoint-file <file>` ("bale commits it ... and
        packs in the same run"). Pack honors it; handoff should too,
        since the refusal is emitted verbatim on both paths.

        Observed at 0.4.26: handoff's argparse rejects the flag (exit 2,
        "unrecognized arguments"). The operator following the refusal's
        own instructions hits a second, unrelated-looking failure."""
        bailed_sid, tarball = self.bailed_with_plan()
        combined = self.assert_refused(self.handoff(tarball),
                                       "handoff with no committed checkpoint")
        self.assertIn(FLAG_REMEDY_PHRASE, combined,
                      msg="precondition: the refusal names the flag remedy")

        result = self.handoff(tarball, "--checkpoint-file", str(self.source))

        self.assert_ok(result, "handoff --checkpoint-file (the named remedy)")
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(self.request_manifest(new_sid)["provenance"]
                         ["checkpoint"]["path"], self.resolved_for(new_sid))

    def test_planless_stacks_both_gates(self) -> None:
        """Diagnosis pin (passing): a plan-less handoff under a {sid}
        base meets the blindness refusal first (the whole-tree fallback
        covers the pattern), and — once admitted past it with the one
        flag handoff does carry — the resolved-existence refusal next.
        Two remedies are needed, one of them a flag the surface lacks
        (the expectedFailure above). Neither refusal burns an NNN."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=None,
            pack_extra=("--checkpoint-file", str(self.source)))
        peek = self.peeked_sid()

        combined = self.assert_refused(self.handoff(tarball),
                                       "plan-less handoff, gate 1")
        self.assertIn(BLINDNESS_PHRASE, combined)
        self.assertNotIn(MISSING_RESOLVED_PHRASE, combined)

        combined = self.assert_refused(
            self.handoff(tarball, "--allow-checkpoint-in-scope"),
            "plan-less handoff, gate 2")
        self.assertIn(ADMITTED_PHRASE, combined,
                      msg="the flag admits the forecast half (FORCE-logged)")
        self.assertIn(MISSING_RESOLVED_PHRASE, combined)

        self.assertEqual(self.open_sids(), [])
        self.assertEqual(self.peeked_sid(), peek)


class HandoffLiteralBaseTest(HandoffFixture):
    """A literal [validation] base with its oracle committed."""

    def setUp(self) -> None:
        super().setUp()
        self.configure_checkpoint(LITERAL_BASE)
        self.commit_checkpoint(LITERAL_BASE)

    def test_plan_citing_file_handoff_and_apply_succeed(self) -> None:
        """Lead 3's literal half, NOT reproduced (passing): a plan citing
        hello.txt forecasts hello.txt, which does not cover the oracle;
        handoff proceeds and stamps the literal checkpoint; the
        resulting session's normal response applies with the
        checkpoint verified and run in staging."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])

        result = self.handoff(tarball)
        self.assert_ok(result, "handoff under a literal checkpoint")
        self.assertIn(BLINDNESS_PASSED_PHRASE, result.stdout)
        self.assertIn(CHECKPOINT_STAMPED_PHRASE, result.stdout)

        new_sid = self.sole_new_open_sid(bailed_sid)
        prov = self.request_manifest(new_sid)["provenance"]
        self.assertEqual(prov["checkpoint"],
                         {"path": LITERAL_BASE,
                          "sha256": self.head_sha256(LITERAL_BASE)})
        self.assertFalse(prov["checkpoint_scope_admitted"])

        applied = self.apply_normal_response(
            new_sid, path="hello.txt", data=b"rewritten by the resumed work\n")
        self.assert_ok(applied, "apply of the handoff session's response")
        self.assertIn(CHECKPOINT_VERIFIED_PHRASE, applied.stdout)
        self.assertEqual(self.open_sids(), [])

    def test_control_bare_default_pack_is_admitted(self) -> None:
        """Control (passing): the v0.4.9 contract — a bare `bale pack`
        (no --include, no --write) in a literal-checkpoint project
        passes the blindness gate on the include-set compatibility
        default and auto-excludes the oracle from context."""
        r = self.bare_pack()
        self.assert_ok(r, "bare default pack under a literal checkpoint")
        self.assertIn(BLINDNESS_PASSED_PHRASE, r.stdout)
        self.assertIn("auto-excluded", r.stdout)
        sid = self.open_sids()[0]
        self.assertEqual(self.recorded_scope(sid), ["."],
                         msg="a bare pack still forecasts the whole tree")

    @unittest.expectedFailure
    def test_planless_handoff_is_admitted_like_a_bare_pack(self) -> None:
        """Unpredicted class: a plan-less handoff resolves to the same
        [\".\"] forecast a bare pack does, so under v0.4.9's contract it
        should pass the blindness gate the same way (the oracle
        auto-excluded, nothing in the plan named it).

        Observed at 0.4.26: refused — handoff evaluates the fallback as
        a DECLARED forecast, and the refusal's remedy tells the
        operator to re-bail with a plan that does not cite the
        checkpoint, which this plan never did."""
        bailed_sid, tarball = self.packed_and_bailed(reading_plan_paths=None)

        result = self.handoff(tarball)

        self.assert_ok(result, "plan-less handoff under a literal checkpoint")
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid), ["."])
        self.assertFalse(self.request_manifest(new_sid)["provenance"]
                         ["checkpoint_scope_admitted"])

    def test_planless_refusal_misdiagnoses_the_plan(self) -> None:
        """Diagnosis pin (passing): the plan-less refusal names the
        `.` forecast, and its first remedy blames the reading plan for
        citing the checkpoint. The plan here has no reading-plan
        section at all; the coverage came from the fallback."""
        bailed_sid, tarball = self.packed_and_bailed(reading_plan_paths=None)
        peek = self.peeked_sid()

        combined = self.assert_refused(self.handoff(tarball),
                                       "plan-less handoff")
        self.assertIn(BLINDNESS_PHRASE, combined)
        self.assertIn("(.)", combined,
                      msg="the refusal names the whole-tree fallback forecast")
        self.assertIn("re-bail with a reading plan that does not cite the "
                      "checkpoint", combined)
        self.assertEqual(self.open_sids(), [])
        self.assertEqual(self.peeked_sid(), peek)


if __name__ == "__main__":
    unittest.main()
