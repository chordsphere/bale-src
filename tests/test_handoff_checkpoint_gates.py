#!/usr/bin/env python3
"""`bale handoff` in a checkpoint-configured project (board 73: session
A's lead 3 and one unpredicted class; session B's modernization at
0.4.28).

Two gates run on the handoff path, both shared with pack and both
sited pre-sid: the blindness pre-flight (``checkpoint_blindness_preflight``,
against the inherited write forecast, with the reading-plan file set
as its read side) and, for a ``{sid}``-templated base, the
resolved-existence pre-flight (``checkpoint_resolved_preflight``,
against a peeked sid). The contract these tests pin:

- **{sid} base, plan cites a file (lead 3).** The blindness gate
  passes; the resolved-existence gate refuses because HEAD has no
  checkpoint at ``claude/checkpoints/<peeked-sid>.sh``. The refusal's
  first-listed remedy — ``--checkpoint-file`` — is accepted: handoff
  commits the planner's checkpoint at the resolved path and hands off
  in one run, exactly as pack does. The second remedy (hand-commit at
  the named path, re-run) still works. The refusal says "re-run this
  handoff" (the ``caller`` kwarg), never "re-run this pack".
- **Literal base, plan cites a file (lead 3's other half, unchanged).**
  Handoff proceeds, stamps the checkpoint, and the resulting session
  applies with the checkpoint running.
- **Plan-less handoff (the unpredicted class).** With the parent's
  record present the handoff inherits the parent's forecast and the
  plan citing nothing changes nothing: under a literal base it is
  admitted (recording the parent's forecast), under a {sid} base only
  the resolved-existence gate fires. With NO readable parent record
  the ``["."]`` fallback is an undeclared forecast and takes the
  bare-pack rule (v0.4.9): admitted, recording ``["."]``. Until
  0.4.27 the fallback was evaluated as a declared forecast and refused
  where a bare pack was admitted, and the refusal told the operator to
  re-bail with a plan that did not cite the checkpoint — which no plan
  had.
- **The blindness refusal on a handoff** names ``--write`` as the
  narrowing remedy (a handoff without ``--write`` inherits), not the
  reading plan. **The read-only waiver** (v0.4.9) reaches handoff: an
  inherited or ``--read-only`` empty forecast needs no per-session
  checkpoint, stamped ``checkpoint_waived``.

Session A's two ``@unittest.expectedFailure`` reproductions are the
acceptance tests; both decorators came off at 0.4.28. Per the desk's
ruling, ``test_planless_handoff_is_admitted_like_a_bare_pack`` keeps
its admission assertion and asserts the inherited record (the parent's
hello.txt); the ``["."]`` case has its own test behind
``drop_parent_record``. A's two diagnosis pins of the stacked-gates
and misdiagnosing refusals were rewritten to the modern outcome.

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
HANDOFF_RERUN_REMEDY = "re-run this handoff with --checkpoint-file"
WRITE_NARROWING_REMEDY = ("re-run this handoff with --write paths that "
                          "do not cover the checkpoint")
OLD_PLAN_REMEDY = "re-bail with a reading plan that does not cite the checkpoint"
WAIVER_PHRASE = "read-only checkpoint waiver"


class HandoffSidBaseTest(HandoffFixture):
    """A ``{sid}``-templated [validation] base — bale-src's own shape."""

    def setUp(self) -> None:
        super().setUp()
        self.configure_checkpoint(SID_BASE)
        # The parent pack needs its own per-session oracle; pack
        # delivers it in one run via --checkpoint-file, and since
        # 0.4.28 so does handoff.
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
        self.assertIn(HANDOFF_RERUN_REMEDY, combined,
                      msg="the remedy names the command the operator typed")
        self.assertNotIn("re-run this pack", combined)
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

    def test_refusal_named_remedy_is_accepted(self) -> None:
        """Lead 3 (path 2, acceptance test): the resolved-existence
        refusal's first remedy is `--checkpoint-file <file>` ("bale
        commits it ... and packs in the same run"). Pack honors it;
        handoff does too.

        Observed at 0.4.26: handoff's argparse rejected the flag (exit
        2, "unrecognized arguments"). Session B: decorator stripped,
        body as A wrote it."""
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

    def test_checkpoint_file_install_is_echoed_and_idempotent(self) -> None:
        """--checkpoint-file on handoff carries pack's contract: the
        installed source and its sha256 are echoed on the summary, the
        oracle is committed at the resolved path with the sid in the
        subject, and the read-only contradiction refuses pre-tarball."""
        bailed_sid, tarball = self.bailed_with_plan()
        peek = self.peeked_sid()

        combined = self.assert_refused(
            self.handoff(tarball, "--checkpoint-file", str(self.source),
                         "--read-only"),
            "handoff --checkpoint-file --read-only")
        self.assertIn("--checkpoint-file and --read-only are contradictory",
                      combined)
        self.assertEqual(self.peeked_sid(), peek)

        result = self.handoff(tarball, "--checkpoint-file", str(self.source))
        self.assert_ok(result, "handoff --checkpoint-file")
        self.assertIn(f"checkpoint: {self.source}", result.stdout)
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(new_sid, peek)
        self.assertEqual(self.head_sha256(self.resolved_for(new_sid)),
                         self.request_manifest(new_sid)["provenance"]
                         ["checkpoint"]["sha256"])

    def test_planless_handoff_inherits_and_meets_only_the_resolved_gate(self):
        """Pin (rewritten at 0.4.28 from the stacked-gates pin): a
        plan-less handoff under a {sid} base inherits the parent's
        hello.txt, so the blindness gate passes and only the
        resolved-existence refusal fires; --checkpoint-file clears it
        in one run. Neither the refusal nor the flag burns an NNN."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=None,
            pack_extra=("--checkpoint-file", str(self.source)))
        peek = self.peeked_sid()

        combined = self.assert_refused(self.handoff(tarball),
                                       "plan-less handoff, resolved gate")
        self.assertIn(BLINDNESS_PASSED_PHRASE, combined)
        self.assertNotIn(BLINDNESS_PHRASE, combined)
        self.assertIn(MISSING_RESOLVED_PHRASE, combined)
        self.assertEqual(self.open_sids(), [])
        self.assertEqual(self.peeked_sid(), peek)

        result = self.handoff(tarball, "--checkpoint-file", str(self.source))
        self.assert_ok(result, "plan-less handoff --checkpoint-file")
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(new_sid, peek)
        self.assertEqual(self.recorded_scope(new_sid), ["hello.txt"])

    def test_planless_fallback_takes_the_bare_pack_rule_under_sid_base(self):
        """The fallback under a {sid} base: no parent record, plan
        cites nothing — the ["."] forecast is undeclared, so the
        blindness gate passes as it does for a bare pack (the class A
        pinned as the stacked refusal); the resolved-existence gate
        still needs its oracle, and --checkpoint-file supplies it."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=None,
            pack_extra=("--checkpoint-file", str(self.source)))
        self.drop_parent_record(bailed_sid)

        combined = self.assert_refused(self.handoff(tarball),
                                       "fallback handoff, resolved gate")
        self.assertIn(BLINDNESS_PASSED_PHRASE, combined)
        self.assertNotIn(BLINDNESS_PHRASE, combined)
        self.assertIn(MISSING_RESOLVED_PHRASE, combined)

        result = self.handoff(tarball, "--checkpoint-file", str(self.source))
        self.assert_ok(result, "fallback handoff --checkpoint-file")
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid), ["."])
        self.assertFalse(self.request_manifest(new_sid)["provenance"]
                         ["checkpoint_scope_admitted"])

    def test_read_only_handoff_waives_the_per_session_checkpoint(self):
        """The v0.4.9 waiver reaches handoff: a --read-only handoff (or
        one inheriting a read-only parent's []) needs no committed
        per-session checkpoint, and the waiver is stamped."""
        bailed_sid, tarball = self.bailed_with_plan()

        result = self.handoff(tarball, "--read-only")
        self.assert_ok(result, "handoff --read-only under a {sid} base")
        self.assertIn(WAIVER_PHRASE, result.stdout)
        new_sid = self.sole_new_open_sid(bailed_sid)
        prov = self.request_manifest(new_sid)["provenance"]
        self.assertEqual(prov.get("checkpoint_waived"), "read-only")
        self.assertEqual(self.recorded_scope(new_sid), [])


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

    def test_planless_handoff_is_admitted_like_a_bare_pack(self) -> None:
        """Unpredicted class (path 4, acceptance test): a plan-less
        handoff is admitted the way a bare pack is. Observed at 0.4.26:
        refused — the [\".\"] fallback was evaluated as a DECLARED
        forecast, and the refusal's remedy told the operator to re-bail
        with a plan that did not cite the checkpoint, which this plan
        never did.

        Session B: decorator stripped; the recorded-scope assertion
        rewritten from [\".\"] to the parent's hello.txt per the desk's
        ruling (inheritance is the mainline; with the parent's record
        present a plan-less handoff inherits). The [\".\"] case is
        test_planless_fallback_without_parent_record below."""
        bailed_sid, tarball = self.packed_and_bailed(reading_plan_paths=None)

        result = self.handoff(tarball)

        self.assert_ok(result, "plan-less handoff under a literal checkpoint")
        self.assertIn(BLINDNESS_PASSED_PHRASE, result.stdout)
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid), ["hello.txt"],
                         msg="the plan-less handoff inherits the parent's forecast")
        self.assertFalse(self.request_manifest(new_sid)["provenance"]
                         ["checkpoint_scope_admitted"])

    def test_planless_fallback_without_parent_record(self) -> None:
        """The fallback (path 4) under a literal base: no parent record,
        plan cites nothing — the [\".\"] forecast is undeclared and takes
        the bare-pack rule: the blindness gate passes, the handoff
        records [\".\"] with no admission stamp, and the summary says
        the fallback fired."""
        bailed_sid, tarball = self.packed_and_bailed(reading_plan_paths=None)
        self.drop_parent_record(bailed_sid)

        result = self.handoff(tarball)

        self.assert_ok(result, "fallback handoff under a literal checkpoint")
        self.assertIn(BLINDNESS_PASSED_PHRASE, result.stdout)
        self.assertIn("fell back to the reading-plan file set (.), undeclared",
                      result.stdout)
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertEqual(self.recorded_scope(new_sid), ["."])
        prov = self.request_manifest(new_sid)["provenance"]
        self.assertFalse(prov["checkpoint_scope_admitted"])
        self.assertEqual(prov["checkpoint"]["path"], LITERAL_BASE)

    def test_covering_write_refuses_with_the_write_remedy(self) -> None:
        """Pin (rewritten at 0.4.28 from the misdiagnosis pin): a
        handoff whose DECLARED forecast covers the oracle refuses at
        the blindness gate, and the remedy names --write — the lever
        that moves a handoff's forecast — never the reading plan.
        --allow-checkpoint-in-scope admits it, stamped."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])
        peek = self.peeked_sid()

        combined = self.assert_refused(
            self.handoff(tarball, "--write", "claude"),
            "handoff --write covering the checkpoint")
        self.assertIn(BLINDNESS_PHRASE, combined)
        self.assertIn("(claude)", combined)
        self.assertIn(WRITE_NARROWING_REMEDY, combined)
        self.assertNotIn(OLD_PLAN_REMEDY, combined)
        self.assertEqual(self.open_sids(), [])
        self.assertEqual(self.peeked_sid(), peek)

        result = self.handoff(tarball, "--write", "claude",
                              "--allow-checkpoint-in-scope")
        self.assert_ok(result, "handoff admitted past the blindness gate")
        self.assertIn(ADMITTED_PHRASE, result.stdout)
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertTrue(self.request_manifest(new_sid)["provenance"]
                        ["checkpoint_scope_admitted"])


if __name__ == "__main__":
    unittest.main()
