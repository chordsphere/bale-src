#!/usr/bin/env python3
"""The board 10 S5 telemetry extensions (v0.4.6): nullable cost block,
no_response / malformed_response closure reasons, claim_basis rows, and
the validate_telemetry_record library entry point.

Four surfaces, one additive session (BALE.md §8.9):

- **validate_telemetry_record** (`bin/bale_validate.py`) — the
  per-record entry point the blind-checkpoint contract pins by name:
  ``validate_telemetry_record(record: dict) -> list``, empty list =
  valid, non-empty = human-readable error strings. Library-importable
  with NO bale process and no ``__main__`` dependency — asserted here
  by driving it through a bare ``python3 -c`` subprocess, the exact
  import posture a planner-authored checkpoint uses.
- **cost** — ``attempts[].cost`` (tokens_in / tokens_out / usd /
  model_tier, every field nullable), stamped unconditionally by
  ``build_telemetry_attempt`` as the all-null block (the
  sandbox-stamps epoch posture: key presence is epoch membership,
  all-null is the pre-harness steady state, a caller's real block is
  recorded verbatim). Not in ``required`` — legacy records validate.
- **closure reasons** — ``no_response`` and ``malformed_response`` as
  additive enum values, in the schema and in the one-home
  ``CLOSURE_REASONS`` tuple both ``--reason`` flags import; unknown
  reasons keep rejecting (the enum is deliberately closed).
- **claim_basis** — optional on claim-bearing rows (``claim_verdict``
  rows and the annotated object form a ``claims`` value may take),
  enum exactly ``predicted`` | ``observed``, enforced RECORD-WIDE by
  the validator's walk so an invented basis rejects at any depth the
  loose schema didn't enumerate.

Plus the two session-level guarantees the brief names as explicit
claims: the legacy corpus keeps validating (zero regressions, run over
both the checked-in ``claude/telemetry/`` corpus and the synthetic
``tests/fixtures/stats_corpus/`` fixtures), and ``bale stats``
tolerates the new fields' mere presence (no read side — tolerance
only), asserted by aggregating a corpus containing new-shape records.

Oracle doctrine per ADR-0002: observable-state assertions against the
documented contract (schema files, returned error lists, the stats
dict), never against private internals.

Hermetic and schema-cheap: everything here is in-process module work
over this repo's own files — no sandbox spin-up, no git, no
subprocess-driven bale runs beyond the one bare-python import check.

Run:  python3 -m unittest tests.test_telemetry_extensions -v
  or: python3 -m unittest discover -s tests -p 'test_telemetry_extensions.py'
"""

from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BIN = REPO_ROOT / "bin"
SCHEMA_PATH = REPO_ROOT / "schemas" / "telemetry-record.schema.json"
TELEMETRY_DIR = REPO_ROOT / "claude" / "telemetry"
STATS_CORPUS = REPO_ROOT / "tests" / "fixtures" / "stats_corpus"


def _load_module(name: str):
    """Load a bin/ sibling by path, unregistered — the modules import
    nothing from __main__ at module scope, which is exactly the
    library-import property S5 relies on."""
    spec = importlib.util.spec_from_file_location(
        f"{name}_under_test", BIN / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _minimal_record(**attempt_overrides) -> dict:
    """A smallest-valid record: the required envelope plus one minimal
    attempt, with per-test attempt overrides."""
    attempt = {"at": "2026-08-13T00:00:00+00:00",
               "outcome": "unlocked", "command": "unlock"}
    attempt.update(attempt_overrides)
    return {
        "record_version": 1,
        "session_id": "2026-08-13-fx-min-001",
        "created_at": "2026-08-13T00:00:00+00:00",
        "updated_at": "2026-08-13T00:00:00+00:00",
        "outcome": "unlocked",
        "attempts": [attempt],
    }


class ValidatorEntryPointTest(unittest.TestCase):
    """The pinned function: name, signature shape, and the
    no-bale-process import posture."""

    @classmethod
    def setUpClass(cls):
        cls.bv = _load_module("bale_validate")

    def test_importable_as_library_without_bale(self) -> None:
        """The checkpoint contract: a bare python3 process imports
        bin/bale_validate and calls validate_telemetry_record — no
        bale __main__, no fail() available. A valid minimal record
        returns [] and an invented closure reason returns errors."""
        script = (
            "import sys, json; sys.path.insert(0, sys.argv[1]); "
            "import bale_validate as bv; "
            "rec = json.loads(sys.argv[2]); "
            "print(json.dumps(bv.validate_telemetry_record(rec)))"
        )
        good = _minimal_record()
        result = subprocess.run(
            [sys.executable, "-c", script, str(BIN), json.dumps(good)],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertEqual(json.loads(result.stdout), [])

        bad = _minimal_record(closure_reason="ghosted")
        result = subprocess.run(
            [sys.executable, "-c", script, str(BIN), json.dumps(bad)],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        errors = json.loads(result.stdout)
        self.assertTrue(errors, msg="invented closure reason must reject")
        self.assertTrue(all(isinstance(e, str) for e in errors),
                        msg="errors are human-readable strings")

    def test_non_dict_is_an_error_not_an_exception(self) -> None:
        errors = self.bv.validate_telemetry_record(["not", "a", "record"])
        self.assertEqual(len(errors), 1)
        self.assertIn("not a JSON object", errors[0])

    def test_missing_required_envelope_reports_by_name(self) -> None:
        rec = _minimal_record()
        del rec["outcome"]
        errors = self.bv.validate_telemetry_record(rec)
        self.assertTrue(any("outcome" in e for e in errors))


class ClosureReasonVocabularyTest(unittest.TestCase):
    """The two additive values, everywhere the vocabulary lives."""

    @classmethod
    def setUpClass(cls):
        cls.bv = _load_module("bale_validate")
        cls.br = _load_module("bale_report")
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_schema_enum_gained_exactly_the_two_values(self) -> None:
        enum = (self.schema["properties"]["attempts"]["items"]
                ["properties"]["closure_reason"]["enum"])
        for value in ("no_response", "malformed_response"):
            self.assertIn(value, enum)
        self.assertIn(None, enum, msg="nullability is unchanged")

    def test_tuple_and_schema_enum_agree(self) -> None:
        """CLOSURE_REASONS is the one home both --reason flags import;
        the schema's enum is the tuple plus null. Drift in either
        direction fails here by name."""
        enum = (self.schema["properties"]["attempts"]["items"]
                ["properties"]["closure_reason"]["enum"])
        self.assertEqual([v for v in enum if v is not None],
                         list(self.br.CLOSURE_REASONS))

    def test_new_reasons_validate_and_invented_rejects(self) -> None:
        for value in ("no_response", "malformed_response"):
            rec = _minimal_record(closure_reason=value)
            self.assertEqual(self.bv.validate_telemetry_record(rec), [],
                             msg=f"{value} must validate")
        rec = _minimal_record(closure_reason="worker-exploded")
        errors = self.bv.validate_telemetry_record(rec)
        self.assertTrue(errors, msg="the enum is deliberately closed")
        self.assertIn("closure_reason", errors[0])

    def test_vocabulary_enforced_record_wide(self) -> None:
        """The correction the first HOLD demanded (checkpoint finding 1):
        a closure_reason key at a depth the schema never named — the
        envelope, a nested sibling — gets the same verdict as the named
        spot. Known reasons and null pass; an invented value rejects
        wherever it rides, so a blind consumer's placement choice cannot
        route around the closed vocabulary."""
        for value in ("no_response", "malformed_response",
                      "abandoned", None):
            rec = _minimal_record()
            rec["closure_reason"] = value  # envelope-level, un-named spot
            self.assertEqual(self.bv.validate_telemetry_record(rec), [],
                             msg=f"envelope closure_reason={value!r} "
                                 f"must validate")
        rec = _minimal_record()
        rec["closure_reason"] = "definitely_not_a_reason"
        errors = self.bv.validate_telemetry_record(rec)
        self.assertTrue(any("closure_reason" in e for e in errors),
                        msg="envelope-level invented reason must reject")
        rec = _minimal_record()
        rec["attempts"][0]["future_sibling"] = {
            "closure_reason": "ghosted"}
        errors = self.bv.validate_telemetry_record(rec)
        self.assertTrue(any("closure_reason" in e for e in errors),
                        msg="nested invented reason must reject")

    def test_record_wide_walk_tracks_the_schema_enum(self) -> None:
        """The walk derives its allowed set from the schema's own enum
        (the vocabulary's one home) — a value in the schema enum is a
        value the walk accepts, by construction, at every depth."""
        schema_enum = (self.schema["properties"]["attempts"]["items"]
                       ["properties"]["closure_reason"]["enum"])
        for value in schema_enum:
            rec = _minimal_record()
            rec["closure_reason"] = value
            self.assertEqual(self.bv.validate_telemetry_record(rec), [],
                             msg=f"schema-enum value {value!r} must pass "
                                 f"the record-wide walk")


class CostBlockTest(unittest.TestCase):
    """The nullable cost block: schema shape, additive posture, and the
    builder's unconditional all-null stamp."""

    @classmethod
    def setUpClass(cls):
        cls.bv = _load_module("bale_validate")
        cls.br = _load_module("bale_report")
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    ALL_NULL = {"tokens_in": None, "tokens_out": None,
                "usd": None, "model_tier": None}

    def test_schema_carries_the_pinned_names_additively(self) -> None:
        items = self.schema["properties"]["attempts"]["items"]
        cost = items["properties"]["cost"]
        for name in ("tokens_in", "tokens_out", "usd", "model_tier"):
            self.assertIn(name, cost["properties"])
            self.assertIn("null", cost["properties"][name]["type"],
                          msg=f"{name} must be nullable")
        self.assertNotIn("cost", items.get("required", []),
                         msg="cost must stay additive — legacy records "
                             "without it must validate")
        self.assertIn("null", cost["type"],
                      msg="the block itself is nullable")

    def test_all_null_and_populated_blocks_validate(self) -> None:
        rec = _minimal_record(cost=dict(self.ALL_NULL))
        self.assertEqual(self.bv.validate_telemetry_record(rec), [])
        rec = _minimal_record(cost={"tokens_in": 12000, "tokens_out": 3400,
                                    "usd": 0.87, "model_tier": "sonnet"})
        self.assertEqual(self.bv.validate_telemetry_record(rec), [])

    def test_builder_stamps_all_null_unconditionally(self) -> None:
        """The epoch stamp: every post-S5 attempt of every command
        carries the block; the pre-harness steady state is all-null."""
        for outcome, command in (("unlocked", "unlock"),
                                 ("applied", "apply"),
                                 ("rolled-back", "rollback")):
            attempt = self.br.build_telemetry_attempt(
                outcome=outcome, command=command)
            self.assertEqual(attempt["cost"], self.ALL_NULL,
                             msg=f"{command}: all-null stamp expected")

    def test_builder_records_a_real_block_verbatim(self) -> None:
        real = {"tokens_in": 10, "tokens_out": 5,
                "usd": 0.01, "model_tier": "opus"}
        attempt = self.br.build_telemetry_attempt(
            outcome="applied", command="apply", cost=dict(real))
        self.assertEqual(attempt["cost"], real)

    def test_stamped_attempt_validates(self) -> None:
        attempt = self.br.build_telemetry_attempt(
            outcome="unlocked", command="unlock")
        rec = _minimal_record()
        rec["attempts"] = [attempt]
        self.assertEqual(self.bv.validate_telemetry_record(rec), [])


class ClaimBasisTest(unittest.TestCase):
    """predicted | observed, optional everywhere, closed everywhere."""

    @classmethod
    def setUpClass(cls):
        cls.bv = _load_module("bale_validate")
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    @staticmethod
    def _validated_record(claims_value, verdict_row_extra=None) -> dict:
        row = {"claim": "pass", "verdict": "pass", "agreement": "agree"}
        if verdict_row_extra:
            row.update(verdict_row_extra)
        return _minimal_record(
            outcome="applied", command="apply",
            validation={
                "state": "PASS", "exit_code": 0,
                "claims": {"suite": claims_value},
                "claim_verdict": {"suite": row},
                "reconciliation_parsed": True,
            })

    def test_vocabulary_constant_is_the_pinned_pair(self) -> None:
        self.assertEqual(tuple(self.bv.CLAIM_BASES),
                         ("predicted", "observed"))

    def test_schema_enum_at_both_claim_bearing_spots(self) -> None:
        validation = (self.schema["properties"]["attempts"]["items"]
                      ["properties"]["validation"])
        row = validation["properties"]["claim_verdict"]["additionalProperties"]
        self.assertEqual(row["properties"]["claim_basis"]["enum"],
                         ["predicted", "observed"])
        self.assertNotIn("claim_basis", row.get("required", []),
                         msg="claim_basis is optional — no backfill")
        annotated = validation["properties"]["claims"]["additionalProperties"]
        self.assertEqual(annotated["properties"]["claim_basis"]["enum"],
                         ["predicted", "observed"])
        self.assertIn("string", annotated["type"],
                      msg="the bare-string claim value must keep validating")

    def test_both_values_pass_on_claim_verdict_rows(self) -> None:
        for basis in ("predicted", "observed"):
            rec = self._validated_record(
                "pass", verdict_row_extra={"claim_basis": basis})
            self.assertEqual(self.bv.validate_telemetry_record(rec), [],
                             msg=f"claim_verdict claim_basis={basis}")

    def test_both_values_pass_on_annotated_claims_values(self) -> None:
        for basis in ("predicted", "observed"):
            rec = self._validated_record(
                {"value": "pass", "claim_basis": basis})
            self.assertEqual(self.bv.validate_telemetry_record(rec), [],
                             msg=f"claims annotated claim_basis={basis}")

    def test_invented_value_rejects_at_every_placement(self) -> None:
        """The record-wide walk: an invented basis rejects on a
        claim_verdict row, on an annotated claims value, and at a depth
        the schema never enumerated (additionalProperties true)."""
        rec = self._validated_record(
            "pass", verdict_row_extra={"claim_basis": "vibes"})
        errors = self.bv.validate_telemetry_record(rec)
        self.assertTrue(any("claim_basis" in e for e in errors))

        rec = self._validated_record({"value": "pass",
                                      "claim_basis": "guessed"})
        errors = self.bv.validate_telemetry_record(rec)
        self.assertTrue(any("claim_basis" in e for e in errors))

        rec = _minimal_record()
        rec["attempts"][0]["future_sibling"] = {
            "rows": [{"claim": "pass", "claim_basis": "hunch"}]}
        errors = self.bv.validate_telemetry_record(rec)
        self.assertTrue(any("claim_basis" in e for e in errors),
                        msg="the walk must catch an invented basis at "
                            "any depth, not only the schema's two spots")

    def test_null_is_not_a_basis(self) -> None:
        """Unknown basis is spelled by omitting the key; null is an
        invented value like any other."""
        rec = self._validated_record(
            "pass", verdict_row_extra={"claim_basis": None})
        errors = self.bv.validate_telemetry_record(rec)
        self.assertTrue(any("claim_basis" in e for e in errors))

    def test_legacy_bare_string_claims_still_validate(self) -> None:
        rec = self._validated_record("pass")
        self.assertEqual(self.bv.validate_telemetry_record(rec), [])


class CorpusZeroRegressionTest(unittest.TestCase):
    """The brief's explicit claim: every legacy record keeps validating.

    Runs over the repo's own checked-in corpus (claude/telemetry/) and
    the synthetic stats fixtures — every parseable record validates with
    zero errors. corrupt-record.json is excluded by design (it does not
    parse; that is its job)."""

    @classmethod
    def setUpClass(cls):
        cls.bv = _load_module("bale_validate")

    def _validate_dir(self, directory: Path, exclude: set[str]) -> int:
        count = 0
        for path in sorted(directory.glob("*.json")):
            if path.name in exclude:
                continue
            record = json.loads(path.read_text(encoding="utf-8"))
            errors = self.bv.validate_telemetry_record(record)
            self.assertEqual(errors, [],
                             msg=f"{path.name} regressed: {errors[:3]}")
            count += 1
        return count

    def test_checked_in_corpus_validates_clean(self) -> None:
        if not TELEMETRY_DIR.is_dir():
            self.skipTest("claude/telemetry/ absent in this checkout")
        count = self._validate_dir(TELEMETRY_DIR, exclude=set())
        self.assertGreater(count, 0, msg="corpus present but empty — "
                                         "the zero-regression claim "
                                         "needs records to run over")

    def test_stats_fixture_corpus_validates_clean(self) -> None:
        count = self._validate_dir(STATS_CORPUS,
                                   exclude={"corrupt-record.json"})
        self.assertGreater(count, 0)


class StatsToleranceTest(unittest.TestCase):
    """The brief's caution: `bale stats` must not choke on the new
    fields' mere presence. No read side — tolerance only: the
    aggregation runs clean over new-shape records and the new unlock
    reasons land in the closure mix as ordinary buckets."""

    @classmethod
    def setUpClass(cls):
        cls.stats = _load_module("bale_stats")

    def test_aggregation_tolerates_new_shape_records(self) -> None:
        def new_shape(sid: str, reason: str) -> dict:
            rec = _minimal_record(closure_reason=reason)
            rec["session_id"] = sid
            att = rec["attempts"][0]
            att["cost"] = {"tokens_in": None, "tokens_out": None,
                           "usd": None, "model_tier": None}
            att["validation"] = {
                "state": "PASS", "exit_code": 0,
                "claims": {"suite": {"value": "pass",
                                     "claim_basis": "predicted"}},
                "claim_verdict": {"suite": {
                    "claim": "pass", "verdict": "pass",
                    "agreement": "agree", "claim_basis": "observed"}},
                "reconciliation_parsed": True,
            }
            return rec

        with tempfile.TemporaryDirectory() as td:
            tel = Path(td)
            for src in STATS_CORPUS.glob("*.json"):
                (tel / src.name).write_bytes(src.read_bytes())
            for sid, reason in (
                    ("2026-08-13-fx-noresp-001", "no_response"),
                    ("2026-08-13-fx-malformed-001", "malformed_response")):
                (tel / f"{sid}.json").write_text(
                    json.dumps(new_shape(sid, reason)), encoding="utf-8")
            result = self.stats.compute_stats(tel)
        mix = result["closure_mix"]["unlocked"]
        self.assertEqual(mix.get("no_response"), 1)
        self.assertEqual(mix.get("malformed_response"), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
