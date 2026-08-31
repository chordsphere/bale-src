#!/usr/bin/env python3
"""The `bale stats` drill-down read sides (board 44).

Covers the four pieces the board row names, plus the board 63 fold-in
that landed with them:

- the **opened vocabulary** — ``"opened"`` joins ``IN_FLIGHT_OUTCOMES``
  (retiring the per-open-session unrecognized-outcome warning) and
  session class/packer resolution reads the open-time provenance stamp
  before falling back to the feedback echo;
- **level 1, bucket membership** — anomalous counts name the sids
  composing them, per class row and at the corpus level;
- **level 2, the session dossier** — one sid rendered whole
  (``compute_session_dossier`` plus its rendering pair), including the
  lineage edges the corpus records;
- the **no-new-fields aggregate cuts** — claim coverage per class and
  per packer, checkpoint catch rates, the claim-basis
  observed-vs-predicted split, and outcome rates per contract-doc-hash
  epoch.

Suites are unit-first over synthetic corpora, following the
``test_stats_linkage.py`` precedent (the shared fixture corpus and
``test_stats_aggregation.py``'s whole-corpus expectations stay
untouched; the queued post-epoch fixture fold-ins ride a session that
must perturb those expectations anyway). ``bale_stats`` and
``bale_report`` both import without ``bin/bale`` loaded — their
documented contracts — so the unit suites drive the compute and render
halves directly; one small E2E class drives ``bin/bale stats`` end to
end to pin that the additive keys survive the real wiring in both
output modes.

Oracle doctrine per ADR-0002: observable-state assertions against the
documented contract — hand-derived expectations, never golden bytes.
Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_stats_drilldown.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import contextlib
import io
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

# Both siblings are designed to import without bin/bale loaded (their
# module docstrings); the unit suites import them directly.
sys.path.insert(0, str(REPO_ROOT / "bin"))
import bale_report  # noqa: E402
import bale_stats  # noqa: E402


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


def _feedback(work_class: str = "code", packer: str = "fixture",
              contract_docs: object = None,
              budget_pressure: str = "none") -> dict:
    """A minimal well-formed feedback block. `contract_docs` defaults
    to None (echo carries no doc hashes — the unstamped doc-epoch
    shape); pass a dict for a stamped epoch."""
    provenance = {
        "bale_version": "0.4.22",
        "packer": packer,
        "work_class": work_class,
        "model_identity": "fixture",
    }
    if contract_docs is not None:
        provenance["contract_docs"] = contract_docs
    return {
        "mechanical": {
            "response_kind": "normal",
            "schema_valid": True,
            "mirror_agreement": {"changes_to_files": True,
                                 "files_to_changes": True},
            "claims_subset": True,
            "linkage": None,
            "provenance": provenance,
        },
        "self_reported": {
            "assumptions": [],
            "judgment_calls": [],
            "budget_pressure": budget_pressure,
            "includes_missing": [],
            "compaction_occurred": {"occurred": False},
        },
    }


def _validation(*, state: str = "PASS", exit_code: int = 0,
                claims: dict = None, claim_verdict: dict = None,
                parsed: bool = True) -> dict:
    return {
        "state": state,
        "exit_code": exit_code,
        "claims": claims if claims is not None else {},
        "claim_verdict": claim_verdict if claim_verdict is not None
        else {},
        "reconciliation_parsed": parsed,
    }


def _check(claim: str, verdict: str, agreement: str,
           claim_basis: str = None) -> dict:
    entry = {"claim": claim, "verdict": verdict, "agreement": agreement}
    if claim_basis is not None:
        entry["claim_basis"] = claim_basis
    return entry


def _attempt(*, at: str, outcome: str = "applied", command: str = "apply",
             feedback: object = None, validation: object = None,
             checkpoint: object = None, provenance: object = None,
             closure_reason: object = None, clarification: object = None,
             scope: list = None, change_paths: list = None,
             overridden_paths: list = None,
             scope_kind: str = None, superseded_by: str = None,
             extra: dict = None) -> dict:
    attempt = {
        "at": at,
        "outcome": outcome,
        "command": command,
        "closure_reason": closure_reason,
        "tarball": None,
        "validation": validation,
        "scope": scope if scope is not None else [],
        "overridden_paths": (overridden_paths
                             if overridden_paths is not None else []),
        "required_check_overrides": [],
        "change_paths": change_paths if change_paths is not None else [],
        "feedback": feedback,
        "log": None,
    }
    if checkpoint is not None:
        attempt["checkpoint"] = checkpoint
    if provenance is not None:
        attempt["provenance"] = provenance
    if clarification is not None:
        attempt["clarification"] = clarification
    if scope_kind is not None:
        attempt["scope_kind"] = scope_kind
    if superseded_by is not None:
        attempt["superseded_by"] = superseded_by
    if extra:
        attempt.update(extra)
    return attempt


def _opened_attempt(at: str, work_class: str = "code",
                    packer: str = "chordsphere") -> dict:
    """The board 63 open-time attempt: outcome 'opened', command
    'pack', the verbatim provenance pair, no promoted surfaces."""
    return _attempt(at=at, outcome="opened", command="pack",
                    provenance={"work_class": work_class,
                                "packer": packer})


class _CorpusCase(unittest.TestCase):
    """Shared temp-corpus plumbing for the unit suites."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-drill-")
        self.telemetry = Path(self._tmpdir.name) / "telemetry"
        self.telemetry.mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def seed(self, records: list) -> None:
        for record in records:
            path = self.telemetry / f"{record['session_id']}.json"
            path.write_text(json.dumps(record, indent=2) + "\n",
                            encoding="utf-8")

    def stats(self, **kwargs):
        """compute_stats with stderr captured; returns (stats, stderr)."""
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            stats = bale_stats.compute_stats(self.telemetry, **kwargs)
        return stats, err.getvalue()

    def dossier(self, sid: str):
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            dossier = bale_stats.compute_session_dossier(
                self.telemetry, sid)
        return dossier, err.getvalue()


# ---------------------------------------------------------------------------
# The opened vocabulary (board 63 fold-in)
# ---------------------------------------------------------------------------

class OpenedVocabularyTest(_CorpusCase):
    """'opened' is in-flight, warning-free, and class/packer resolution
    reads the open-time stamp before the feedback echo."""

    def test_opened_record_is_in_flight_without_warning(self) -> None:
        self.seed([
            _record("2026-08-20-open-001", "2026-08-20T10:00:00+00:00",
                    "opened", [
                        _opened_attempt("2026-08-20T10:00:00+00:00",
                                        work_class="doc"),
                    ]),
        ])
        stats, stderr = self.stats()
        # In-flight, never a closure — and no unrecognized-outcome
        # warning, the fold-in's stated point.
        self.assertEqual(stats["corpus"]["in_flight_sessions"], 1)
        self.assertEqual(stats["closure_mix"]["applied"], 0)
        self.assertNotIn("unrecognized envelope outcome", stderr)
        self.assertEqual(stats["members"]["in_flight"],
                         ["2026-08-20-open-001"])
        # The open-time stamp resolves the class for a session with no
        # feedback anywhere — the blind spot the write side closed and
        # this read half consumes.
        self.assertEqual(sorted(stats["classes"]), ["doc"])
        self.assertEqual(stats["classes"]["doc"]["sessions"], 1)

    def test_stamp_resolves_before_feedback_echo(self) -> None:
        # The fold-in's ordering, verbatim: the opened attempt's
        # provenance stamp first, the feedback echo the fallback.
        self.seed([
            _record("2026-08-20-both-001", "2026-08-20T10:00:00+00:00",
                    "applied", [
                        _opened_attempt("2026-08-20T09:00:00+00:00",
                                        work_class="doc",
                                        packer="stamped-packer"),
                        _attempt(at="2026-08-20T10:00:00+00:00",
                                 feedback=_feedback(
                                     work_class="code",
                                     packer="echoed-packer")),
                    ]),
        ])
        stats, _ = self.stats()
        self.assertEqual(sorted(stats["classes"]), ["doc"],
                         msg="the open-time stamp wins over the echo")
        self.assertEqual(sorted(stats["packers"]), ["stamped-packer"])

    def test_echo_fallback_and_absence_buckets(self) -> None:
        self.seed([
            # No stamp: the pre-fold-in behavior, unchanged — the
            # latest feedback echo resolves both identities.
            _record("2026-08-21-echo-001", "2026-08-21T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-21T10:00:00+00:00",
                                 feedback=_feedback(
                                     work_class="mixed",
                                     packer="unconfigured")),
                    ]),
            # Neither: the honest absence buckets.
            _record("2026-08-22-none-001", "2026-08-22T10:00:00+00:00",
                    "unlocked", [
                        _attempt(at="2026-08-22T10:00:00+00:00",
                                 outcome="unlocked", command="unlock",
                                 closure_reason="abandoned",
                                 clarification={"rounds": 0,
                                                "records": []}),
                    ]),
        ])
        stats, _ = self.stats()
        self.assertEqual(sorted(stats["classes"]),
                         ["mixed", "unclassed"])
        # The write side's literal "unconfigured" is a RECORDED
        # identity and buckets verbatim; "unattributed" is this
        # reader's absence bucket — the two are never conflated.
        self.assertEqual(sorted(stats["packers"]),
                         ["unattributed", "unconfigured"])
        self.assertEqual(stats["packers"]["unattributed"]["sessions"], 1)


# ---------------------------------------------------------------------------
# Claim coverage (per class and per packer)
# ---------------------------------------------------------------------------

class ClaimCoverageTest(_CorpusCase):
    """claims_declared, the per-attempt ratio, and the empty-claims
    count — cut per work class and per packer."""

    def _corpus(self) -> None:
        self.seed([
            # Two validated attempts: 3 claims, then 0 claims — the
            # empty map while validation ran is the counted shape.
            _record("2026-08-10-cov-001", "2026-08-10T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-10T10:00:00+00:00",
                                 outcome="held",
                                 feedback=_feedback(packer="alice"),
                                 validation=_validation(
                                     state="HOLD", exit_code=1,
                                     claims={"lint": "pass",
                                             "tests": "pass",
                                             "build": "pass"})),
                        _attempt(at="2026-08-10T11:00:00+00:00",
                                 command="retry",
                                 feedback=_feedback(packer="alice"),
                                 validation=_validation(claims={})),
                    ]),
            # A doc session from another packer: 1 claim.
            _record("2026-08-11-cov-002", "2026-08-11T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-11T10:00:00+00:00",
                                 feedback=_feedback(work_class="doc",
                                                    packer="bob"),
                                 validation=_validation(
                                     claims={"file syntax": "pass"})),
                    ]),
        ])

    def test_class_rows(self) -> None:
        self._corpus()
        stats, _ = self.stats()
        code = stats["classes"]["code"]
        self.assertEqual(code["claims_declared"], 3)
        self.assertEqual(code["validated_attempts"], 2)
        self.assertAlmostEqual(code["claims_per_validated_attempt"],
                               3 / 2)
        self.assertEqual(code["empty_claims_validated_attempts"], 1)
        self.assertEqual(code["members"]["empty_claims"],
                         ["2026-08-10-cov-001"])
        doc = stats["classes"]["doc"]
        self.assertEqual(doc["claims_declared"], 1)
        self.assertEqual(doc["empty_claims_validated_attempts"], 0)
        self.assertEqual(doc["members"]["empty_claims"], [])

    def test_packer_cut(self) -> None:
        self._corpus()
        stats, _ = self.stats()
        self.assertEqual(stats["packers"]["alice"], {
            "sessions": 1,
            "validated_attempts": 2,
            "claims_declared": 3,
            "empty_claims_validated_attempts": 1,
            "claims_per_validated_attempt": 1.5,
        })
        self.assertEqual(stats["packers"]["bob"]["claims_declared"], 1)
        self.assertIsNone(
            bale_stats._rate(0, 0),
            msg="the honesty rule the ratio inherits: None on zero")

    def test_zero_denominator_ratio_is_none(self) -> None:
        # A session with no validated attempt: honest null ratio, no
        # fabricated 0.0 — in the class row and the packer row alike.
        self.seed([
            _record("2026-08-12-cov-003", "2026-08-12T10:00:00+00:00",
                    "rejected", [
                        _attempt(at="2026-08-12T10:00:00+00:00",
                                 outcome="rejected",
                                 feedback=_feedback(packer="carol")),
                    ]),
        ])
        stats, _ = self.stats()
        self.assertIsNone(
            stats["classes"]["code"]["claims_per_validated_attempt"])
        self.assertIsNone(
            stats["packers"]["carol"]["claims_per_validated_attempt"])


# ---------------------------------------------------------------------------
# Checkpoint catch
# ---------------------------------------------------------------------------

class CheckpointCatchTest(_CorpusCase):
    """A catch is the blind oracle objecting (its own exit 1) while
    the worker's own script passed — attribution shapes hand-derived."""

    def test_catch_attribution(self) -> None:
        def ckpt(state: str, exit_code: int) -> dict:
            return {"configured": True, "state": state,
                    "exit_code": exit_code, "stamp_matched": True}

        self.seed([
            # Checkpoint alone objected: worker exit 0 — THE catch.
            _record("2026-08-10-catch-001", "2026-08-10T10:00:00+00:00",
                    "held", [
                        _attempt(at="2026-08-10T10:00:00+00:00",
                                 outcome="held",
                                 feedback=_feedback(),
                                 validation=_validation(
                                     state="HOLD", exit_code=0,
                                     claims={"tests": "pass"}),
                                 checkpoint=ckpt("HOLD", 1)),
                    ]),
            # Both held: the worker also saw it — not a catch.
            _record("2026-08-11-both-001", "2026-08-11T10:00:00+00:00",
                    "held", [
                        _attempt(at="2026-08-11T10:00:00+00:00",
                                 outcome="held",
                                 feedback=_feedback(),
                                 validation=_validation(
                                     state="HOLD", exit_code=1,
                                     claims={"tests": "pass"}),
                                 checkpoint=ckpt("HOLD", 1)),
                    ]),
            # The checkpoint itself errored (exit 2): a tooling fact —
            # in the HOLD count, outside the catches.
            _record("2026-08-12-err-001", "2026-08-12T10:00:00+00:00",
                    "held", [
                        _attempt(at="2026-08-12T10:00:00+00:00",
                                 outcome="held",
                                 feedback=_feedback(),
                                 validation=_validation(
                                     state="HOLD", exit_code=0,
                                     claims={"tests": "pass"}),
                                 checkpoint=ckpt("HOLD", 2)),
                    ]),
            # Worker alone held: checkpoint PASS — neither count.
            _record("2026-08-13-wrk-001", "2026-08-13T10:00:00+00:00",
                    "held", [
                        _attempt(at="2026-08-13T10:00:00+00:00",
                                 outcome="held",
                                 feedback=_feedback(),
                                 validation=_validation(
                                     state="HOLD", exit_code=1,
                                     claims={"tests": "pass"}),
                                 checkpoint=ckpt("PASS", 0)),
                    ]),
        ])
        stats, _ = self.stats()
        code = stats["classes"]["code"]
        self.assertEqual(code["checkpointed_attempts"], 4)
        self.assertEqual(code["checkpoint_hold_attempts"], 3)
        self.assertEqual(code["checkpoint_catch_attempts"], 1)
        self.assertAlmostEqual(code["checkpoint_catch_rate"], 1 / 4)
        self.assertEqual(code["members"]["checkpoint_catch"],
                         ["2026-08-10-catch-001"])
        self.assertEqual(code["members"]["checkpoint_hold"],
                         ["2026-08-10-catch-001", "2026-08-11-both-001",
                          "2026-08-12-err-001"])

    def test_pre_epoch_is_null_not_zero_rate(self) -> None:
        self.seed([
            _record("2026-08-14-pre-001", "2026-08-14T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-14T10:00:00+00:00",
                                 feedback=_feedback(),
                                 validation=_validation(
                                     claims={"tests": "pass"})),
                    ]),
        ])
        stats, _ = self.stats()
        code = stats["classes"]["code"]
        self.assertEqual(code["checkpoint_catch_attempts"], 0)
        self.assertIsNone(code["checkpoint_catch_rate"])


# ---------------------------------------------------------------------------
# The claim-basis split
# ---------------------------------------------------------------------------

class ClaimBasisTest(_CorpusCase):
    """Observed vs predicted vs unspecified, resolved per check from
    the verdict row first and the annotated claims form second."""

    def test_split_hand_derived(self) -> None:
        self.seed([
            _record("2026-08-10-basis-001", "2026-08-10T10:00:00+00:00",
                    "applied", [
                        _attempt(
                            at="2026-08-10T10:00:00+00:00",
                            feedback=_feedback(),
                            validation=_validation(
                                claims={
                                    # Annotated form carries the basis
                                    # the verdict row omits — the
                                    # fallback read.
                                    "lint": {"value": "pass",
                                             "claim_basis": "observed"},
                                    "tests": "pass",
                                    "build": "pass",
                                },
                                claim_verdict={
                                    "lint": _check("pass", "pass",
                                                   "agree"),
                                    # Verdict-row basis wins outright.
                                    "tests": _check(
                                        "pass", "fail", "disagree",
                                        claim_basis="predicted"),
                                    # Bare string, no basis anywhere.
                                    "build": _check("pass", "pass",
                                                    "agree"),
                                })),
                    ]),
        ])
        stats, _ = self.stats()
        code = stats["classes"]["code"]
        self.assertEqual(code["claim_basis"], {
            "observed": {"checks": 1, "agree": 1,
                         "agreement_rate": 1.0},
            "predicted": {"checks": 1, "agree": 0,
                          "agreement_rate": 0.0},
            "unspecified": {"checks": 1, "agree": 1,
                            "agreement_rate": 1.0},
        })
        # The bases partition checks, the per-agreement counts' rule
        # applied to the new grouping.
        self.assertEqual(
            sum(cell["checks"] for cell in code["claim_basis"].values()),
            code["checks"])

    def test_out_of_vocabulary_basis_is_an_honest_row(self) -> None:
        self.seed([
            _record("2026-08-11-odd-001", "2026-08-11T10:00:00+00:00",
                    "applied", [
                        _attempt(
                            at="2026-08-11T10:00:00+00:00",
                            feedback=_feedback(),
                            validation=_validation(
                                claims={"tests": "pass"},
                                claim_verdict={
                                    "tests": _check(
                                        "pass", "pass", "agree",
                                        claim_basis="vibes"),
                                })),
                    ]),
        ])
        stats, _ = self.stats()
        self.assertEqual(
            list(stats["classes"]["code"]["claim_basis"]), ["vibes"],
            msg="a value outside the closed enum forms its own row "
                "verbatim — the honest-row doctrine, never a coercion")


# ---------------------------------------------------------------------------
# Doc epochs
# ---------------------------------------------------------------------------

DOCS_A = {"CLAUDE.md": "aaa", "TARBALL.md": "bbb"}
DOCS_B = {"CLAUDE.md": "aaa", "TARBALL.md": "ccc"}


class DocEpochTest(_CorpusCase):
    """Outcome counts per contract-doc-hash epoch — the A/B read."""

    def _corpus(self) -> None:
        self.seed([
            _record("2026-08-10-ea-001", "2026-08-10T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-10T10:00:00+00:00",
                                 feedback=_feedback(
                                     contract_docs=DOCS_A)),
                    ]),
            _record("2026-08-11-ea-002", "2026-08-11T10:00:00+00:00",
                    "held", [
                        _attempt(at="2026-08-11T10:00:00+00:00",
                                 outcome="held",
                                 feedback=_feedback(
                                     contract_docs=DOCS_A)),
                    ]),
            _record("2026-08-12-eb-001", "2026-08-12T10:00:00+00:00",
                    "bailout", [
                        _attempt(at="2026-08-12T10:00:00+00:00",
                                 outcome="bailout",
                                 feedback=_feedback(
                                     contract_docs=DOCS_B)),
                    ]),
            # No echo anywhere: the unstamped honest bucket.
            _record("2026-08-13-un-001", "2026-08-13T10:00:00+00:00",
                    "unlocked", [
                        _attempt(at="2026-08-13T10:00:00+00:00",
                                 outcome="unlocked", command="unlock",
                                 closure_reason="abandoned"),
                    ]),
        ])

    def test_epoch_rows_hand_derived(self) -> None:
        self._corpus()
        stats, _ = self.stats()
        key_a = bale_stats._doc_epoch_key(DOCS_A)
        key_b = bale_stats._doc_epoch_key(DOCS_B)
        self.assertNotEqual(key_a, key_b)
        self.assertEqual(sorted(stats["doc_epochs"]),
                         sorted([key_a, key_b, "unstamped"]))
        row_a = stats["doc_epochs"][key_a]
        self.assertEqual(row_a["sessions"], 2)
        self.assertEqual(row_a["closed_sessions"], 1)
        self.assertEqual(row_a["in_flight"], 1)
        self.assertEqual(row_a["applied"], 1)
        self.assertEqual(row_a["applied_rate"], 1.0)
        self.assertEqual(row_a["first_created_at"],
                         "2026-08-10T10:00:00+00:00")
        self.assertEqual(row_a["contract_docs"], DOCS_A,
                         msg="the full hash set rides beside the "
                             "digest — the key is an identifier, "
                             "never the only record")
        row_b = stats["doc_epochs"][key_b]
        self.assertEqual(row_b["bailout"], 1)
        self.assertIsNone(row_b["applied_rate"] if
                          row_b["closed_sessions"] == 0 else None)
        un = stats["doc_epochs"]["unstamped"]
        self.assertEqual(un["unlocked"], 1)
        self.assertIsNone(un["contract_docs"])
        # Rows order chronologically by first_created_at.
        self.assertEqual(list(stats["doc_epochs"]),
                         [key_a, key_b, "unstamped"])

    def test_filters_reach_the_epochs(self) -> None:
        self._corpus()
        stats, _ = self.stats(since="2026-08-12")
        self.assertNotIn(bale_stats._doc_epoch_key(DOCS_A),
                         stats["doc_epochs"])
        self.assertIn(bale_stats._doc_epoch_key(DOCS_B),
                      stats["doc_epochs"])


# ---------------------------------------------------------------------------
# Membership (level 1) — the corpus-level half and the emission rules
# ---------------------------------------------------------------------------

class MembershipTest(_CorpusCase):
    """The sids composing the counts, per class row and corpus-wide."""

    def test_class_and_corpus_members(self) -> None:
        self.seed([
            _record("2026-08-10-mem-001", "2026-08-10T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-10T10:00:00+00:00",
                                 outcome="held",
                                 feedback=_feedback(),
                                 validation=_validation(
                                     state="HOLD", exit_code=1,
                                     claims={"tests": "pass"},
                                     claim_verdict={
                                         "tests": _check(
                                             "pass", "fail",
                                             "disagree")})),
                        _attempt(at="2026-08-10T11:00:00+00:00",
                                 command="retry",
                                 feedback=_feedback(),
                                 validation=_validation(
                                     claims={"tests": "pass"},
                                     claim_verdict={
                                         "tests": _check(
                                             "pass", "pass",
                                             "agree")})),
                    ]),
            _record("2026-08-11-mem-002", "2026-08-11T10:00:00+00:00",
                    "scope-drift-refused", [
                        _attempt(at="2026-08-11T10:00:00+00:00",
                                 outcome="scope-drift-refused",
                                 feedback=_feedback()),
                    ]),
            # A read-only closure: context count, corpus members only.
            _record("2026-08-12-mem-003", "2026-08-12T10:00:00+00:00",
                    "unlocked", [
                        _attempt(at="2026-08-12T10:00:00+00:00",
                                 outcome="unlocked", command="unlock",
                                 closure_reason="closed-read-only"),
                    ]),
        ])
        stats, _ = self.stats()
        code = stats["classes"]["code"]
        self.assertEqual(code["members"]["held"],
                         ["2026-08-10-mem-001"])
        self.assertEqual(code["members"]["checks_disagree"],
                         ["2026-08-10-mem-001"])
        self.assertEqual(code["members"]["drift_refused"],
                         ["2026-08-11-mem-002"])
        # A sid appears once per bucket however many attempts put it
        # there, and non-anomalous buckets are honest empties.
        self.assertEqual(code["members"]["rejected"], [])
        self.assertEqual(stats["members"]["in_flight"],
                         ["2026-08-11-mem-002"])
        self.assertEqual(stats["members"]["read_only"],
                         ["2026-08-12-mem-003"])

    def test_counts_unchanged_beside_membership(self) -> None:
        # The emission rule: members ride BESIDE the counts — the
        # pre-existing cross-check counters must not move.
        self.seed([
            _record("2026-08-13-mem-004", "2026-08-13T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-13T10:00:00+00:00",
                                 outcome="applied",
                                 feedback=_feedback(),
                                 clarification={
                                     "rounds": 1,
                                     "records": [
                                         {"n": 1, "at": None,
                                          "blocking_questions": 1}]}),
                    ]),
        ])
        stats, _ = self.stats()
        clar = stats["cross_checks"]["clarification"]
        self.assertEqual(clar["promoted_only"], 1)
        self.assertEqual(stats["members"]["clarification_promoted_only"],
                         ["2026-08-13-mem-004"])


# ---------------------------------------------------------------------------
# The session dossier (level 2)
# ---------------------------------------------------------------------------

class SessionDossierTest(_CorpusCase):
    """One sid rendered whole: attempts, claim/verdict pairs,
    checkpoint outcome, clarification records, lineage."""

    def _hold_retry_record(self) -> dict:
        return _record(
            "2026-08-10-dossier-001", "2026-08-10T10:00:00+00:00",
            "applied", [
                _opened_attempt("2026-08-10T09:00:00+00:00",
                                work_class="code"),
                _attempt(at="2026-08-10T10:00:00+00:00",
                         outcome="held",
                         feedback=_feedback(),
                         validation=_validation(
                             state="HOLD", exit_code=0,
                             claims={"tests": {
                                 "value": "pass",
                                 "claim_basis": "observed"}},
                             claim_verdict={
                                 "tests": _check("pass", "pass",
                                                 "agree")}),
                         checkpoint={"configured": True,
                                     "state": "HOLD", "exit_code": 1,
                                     "stamp_matched": True},
                         scope_kind="write-forecast",
                         scope=["src"],
                         change_paths=["src/a.py", "docs/x.md"],
                         overridden_paths=[]),
                _attempt(at="2026-08-10T11:00:00+00:00",
                         command="retry",
                         feedback=_feedback(),
                         validation=_validation(
                             claims={"tests": "pass"},
                             claim_verdict={
                                 "tests": _check("pass", "pass",
                                                 "agree")}),
                         checkpoint={"configured": True,
                                     "state": "PASS", "exit_code": 0,
                                     "stamp_matched": True},
                         scope_kind="write-forecast",
                         scope=["src"],
                         change_paths=["src/a.py", "docs/x.md"],
                         overridden_paths=["docs/x.md"],
                         clarification={
                             "rounds": 2,
                             "records": [
                                 {"n": 1,
                                  "at": "2026-08-10T10:30:00+00:00",
                                  "blocking_questions": 2,
                                  "from": "worker", "answers": 0},
                                 {"n": 2,
                                  "at": "2026-08-10T10:40:00+00:00",
                                  "blocking_questions": 0,
                                  "from": "planner", "answers": 2},
                             ]}),
            ])

    def test_hold_to_retry_arc_reads_end_to_end(self) -> None:
        self.seed([self._hold_retry_record()])
        dossier, _ = self.dossier("2026-08-10-dossier-001")
        self.assertTrue(dossier["found"])
        record = dossier["record"]
        self.assertEqual(record["work_class"], "code")
        self.assertEqual(record["packer"], "chordsphere",
                         msg="the open-time stamp resolves the packer")
        self.assertFalse(record["in_flight"])
        self.assertEqual(record["closure"],
                         {"category": "applied", "unlock_reason": None})
        self.assertEqual(len(dossier["attempts"]), 3)

        opened, held, retry = dossier["attempts"]
        self.assertEqual(opened["outcome"], "opened")
        self.assertEqual(opened["provenance"]["packer"], "chordsphere")
        self.assertIsNone(opened["validation"])

        self.assertEqual(held["validation"]["state"], "HOLD")
        self.assertEqual(held["validation"]["checks"], [
            {"check": "tests", "claim": "pass", "verdict": "pass",
             "agreement": "agree", "claim_basis": "observed"},
        ])
        self.assertEqual(held["checkpoint"]["state"], "HOLD")
        # The post-epoch drift annotation reuses the gate's own
        # containment: docs/x.md sits outside the src forecast.
        self.assertEqual(held["forecast_drift_paths"], ["docs/x.md"])

        self.assertEqual(retry["outcome"], "applied")
        self.assertEqual(retry["overridden_paths"], ["docs/x.md"])
        self.assertEqual(retry["clarification"]["rounds"], 2)
        self.assertEqual(
            retry["clarification"]["records"][1]["from"], "planner")

    def test_lineage_edges_both_directions(self) -> None:
        parent = _record(
            "2026-08-11-parent-001", "2026-08-11T10:00:00+00:00",
            "unlocked", [
                _attempt(at="2026-08-11T10:00:00+00:00",
                         outcome="unlocked", command="pack",
                         closure_reason="superseded-by-split",
                         superseded_by="2026-08-11-child-001"),
            ])
        child = _record(
            "2026-08-11-child-001", "2026-08-11T11:00:00+00:00",
            "applied", [
                _attempt(at="2026-08-11T11:00:00+00:00",
                         feedback=_feedback()),
            ])
        # A record hand-carrying `corrects` (the field is not promoted
        # by bale today; the tolerant read resolves it wherever a
        # record carries it, and lights up the day the write side
        # lands).
        corrector = _record(
            "2026-08-12-fix-001", "2026-08-12T10:00:00+00:00",
            "applied", [
                _attempt(at="2026-08-12T10:00:00+00:00",
                         feedback=_feedback(),
                         extra={"corrects": "2026-08-11-child-001"}),
            ])
        self.seed([parent, child, corrector])

        d_parent, _ = self.dossier("2026-08-11-parent-001")
        self.assertEqual(d_parent["lineage"]["superseded_by"],
                         "2026-08-11-child-001")
        d_child, _ = self.dossier("2026-08-11-child-001")
        self.assertEqual(d_child["lineage"]["superseded_from"],
                         ["2026-08-11-parent-001"])
        self.assertEqual(d_child["lineage"]["corrected_by"],
                         ["2026-08-12-fix-001"])
        self.assertIsNone(d_child["lineage"]["corrects"],
                          msg="unrecorded is an honest null, never a "
                              "known 'no correction'")
        d_fix, _ = self.dossier("2026-08-12-fix-001")
        self.assertEqual(d_fix["lineage"]["corrects"],
                         "2026-08-11-child-001")

    def test_honest_misses(self) -> None:
        (self.telemetry / "2026-08-13-broken-001.json").write_text(
            "{not json", encoding="utf-8")
        missing, _ = self.dossier("2026-08-14-nowhere-001")
        self.assertEqual(missing, {
            "session_id": "2026-08-14-nowhere-001",
            "found": False,
            "parse_failure": False,
            "filtered_record_version": False,
        })
        broken, stderr = self.dossier("2026-08-13-broken-001")
        self.assertFalse(broken["found"])
        self.assertTrue(broken["parse_failure"])
        self.assertIn("2026-08-13-broken-001.json", stderr,
                      msg="the loader names the skip on stderr as ever")


# ---------------------------------------------------------------------------
# Rendering — both surfaces, both modes' string halves
# ---------------------------------------------------------------------------

class RenderingTest(_CorpusCase):
    """The renderers project the computed payloads: new extras append
    after the pre-existing entries, membership renders only non-empty
    buckets, and the summary block stays last."""

    def test_stats_report_carries_the_drill_surfaces(self) -> None:
        self.seed([
            _record("2026-08-10-r-001", "2026-08-10T10:00:00+00:00",
                    "held", [
                        _attempt(at="2026-08-10T10:00:00+00:00",
                                 outcome="held",
                                 feedback=_feedback(
                                     packer="alice",
                                     contract_docs=DOCS_A),
                                 validation=_validation(
                                     state="HOLD", exit_code=1,
                                     claims={"tests": {
                                         "value": "pass",
                                         "claim_basis": "predicted"}},
                                     claim_verdict={
                                         "tests": _check(
                                             "pass", "fail",
                                             "disagree",
                                             claim_basis="predicted"),
                                     })),
                    ]),
        ])
        stats, _ = self.stats()
        out = bale_report.format_stats_report(stats)
        self.assertIn("claims 1 (1.0/validated attempt)", out)
        self.assertIn("claim basis [predicted 0/1 agree (0%)]", out)
        self.assertIn("code members:", out)
        self.assertIn("held: 2026-08-10-r-001", out)
        self.assertIn("checks_disagree: 2026-08-10-r-001", out)
        self.assertIn("packer alice: 1 sessions, 1 validated, "
                      "claims 1 (1.0/validated attempt), "
                      "empty-claims 0", out)
        key_a = bale_stats._doc_epoch_key(DOCS_A)
        self.assertIn(f"doc epoch {key_a} since "
                      f"2026-08-10T10:00:00+00:00", out)
        self.assertIn("corpus members:", out)
        self.assertIn("in_flight: 2026-08-10-r-001", out)
        # The module rule survives: summary block last, no next-step
        # hint after it.
        last = [ln for ln in out.splitlines() if ln.strip()][-1]
        self.assertIn("filters:", last)

    def test_stats_report_renders_no_fabricated_membership(self) -> None:
        self.seed([
            _record("2026-08-11-r-002", "2026-08-11T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-11T10:00:00+00:00",
                                 feedback=_feedback(),
                                 validation=_validation(
                                     claims={"tests": "pass"},
                                     claim_verdict={
                                         "tests": _check(
                                             "pass", "pass",
                                             "agree")})),
                    ]),
        ])
        stats, _ = self.stats()
        out = bale_report.format_stats_report(stats)
        self.assertNotIn("members:", out,
                         msg="an anomaly-free corpus renders no "
                             "membership lines at all")
        self.assertNotIn("claim basis", out,
                         msg="an all-unspecified corpus renders no "
                             "basis split — it would restate the "
                             "agree column")

    def test_dossier_renderers(self) -> None:
        self.seed([
            _record("2026-08-12-r-003", "2026-08-12T10:00:00+00:00",
                    "applied", [
                        _attempt(at="2026-08-12T10:00:00+00:00",
                                 feedback=_feedback(),
                                 validation=_validation(
                                     claims={"tests": "pass"},
                                     claim_verdict={
                                         "tests": _check(
                                             "pass", "pass",
                                             "agree")})),
                    ]),
        ])
        dossier, _ = self.dossier("2026-08-12-r-003")
        line = bale_report.format_session_dossier_json(dossier)
        self.assertEqual(len(line.splitlines()), 1,
                         msg="one compact line, the stats json rule")
        payload = json.loads(line)
        self.assertEqual(payload["outcome"], "dossier")
        self.assertEqual(payload["session_id"], "2026-08-12-r-003")
        out = bale_report.format_session_dossier_report(dossier)
        self.assertIn("attempt 1: applied (apply)", out)
        self.assertIn("tests: claim pass / verdict pass [agree]", out)
        self.assertIn("lineage: none recorded", out)
        last = [ln for ln in out.splitlines() if ln.strip()][-1]
        self.assertIn("updated:", last)

        miss, _ = self.dossier("2026-08-13-none-001")
        miss_out = bale_report.format_session_dossier_report(miss)
        self.assertIn("no dossier", miss_out)
        self.assertIn("found", miss_out)


# ---------------------------------------------------------------------------
# End to end: the additive keys survive the real wiring, both modes
# ---------------------------------------------------------------------------

class DrilldownE2ETest(unittest.TestCase):
    """`bale stats` carries the board 44 surfaces without any wiring
    change: the payload flows through the existing subcommand."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-drill-e2e-")
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
            _record("2026-08-10-e2e-001", "2026-08-10T10:00:00+00:00",
                    "held", [
                        _attempt(at="2026-08-10T10:00:00+00:00",
                                 outcome="held",
                                 feedback=_feedback(packer="alice"),
                                 validation=_validation(
                                     state="HOLD", exit_code=1,
                                     claims={"tests": "pass"},
                                     claim_verdict={
                                         "tests": _check(
                                             "pass", "fail",
                                             "disagree")})),
                    ]),
            _record("2026-08-11-e2e-002", "2026-08-11T10:00:00+00:00",
                    "opened", [
                        _opened_attempt("2026-08-11T10:00:00+00:00",
                                        work_class="doc",
                                        packer="bob"),
                    ]),
        ]
        for record in records:
            (telemetry / f"{record['session_id']}.json").write_text(
                json.dumps(record, indent=2) + "\n", encoding="utf-8")

    def test_json_mode_carries_the_surfaces(self) -> None:
        self._seed()
        result = run_bale(self.install, ["stats", "--json"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 0,
                         msg=f"stderr:\n{result.stderr}")
        lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1,
                         msg="json stream discipline: one stdout line")
        payload = json.loads(lines[0])
        # The opened session resolves from its stamp with no warning
        # and reads as in-flight.
        self.assertIn("doc", payload["classes"])
        self.assertNotIn("unrecognized envelope outcome", result.stderr)
        self.assertEqual(payload["corpus"]["in_flight_sessions"], 2)
        self.assertEqual(sorted(payload["packers"]), ["alice", "bob"])
        self.assertIn("unstamped", payload["doc_epochs"])
        self.assertEqual(payload["members"]["in_flight"],
                         ["2026-08-10-e2e-001", "2026-08-11-e2e-002"])
        self.assertEqual(payload["classes"]["code"]["members"]["held"],
                         ["2026-08-10-e2e-001"])

    def test_human_mode_carries_the_surfaces(self) -> None:
        self._seed()
        result = run_bale(self.install, ["stats"], cwd=self.repo,
                          env=self.env)
        self.assertEqual(result.returncode, 0,
                         msg=f"stderr:\n{result.stderr}")
        out = result.stdout
        self.assertIn("code members:", out)
        self.assertIn("held: 2026-08-10-e2e-001", out)
        self.assertIn("packer alice:", out)
        self.assertIn("doc epoch unstamped", out)
        last = [ln for ln in out.splitlines() if ln.strip()][-1]
        self.assertIn("filters:", last)


if __name__ == "__main__":
    unittest.main()
