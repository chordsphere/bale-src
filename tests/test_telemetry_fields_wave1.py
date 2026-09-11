#!/usr/bin/env python3
"""Telemetry field additions, wave 1 (v0.4.24): the docs_read
self-report and the clarification question row's origin enum, both
additive and legacy-tolerant per the v0.4.7 pattern, plus the folded
retry/open_telemetry doc rider.

Three surfaces, one additive session:

- **origin** — an optional closed enum on the clarification question
  row (``response-manifest.schema.json``'s ``questions.items``, the
  row shape's one home), exactly ``intent-gap`` |
  ``probe-forbidden-environment``. Enforced at the named spot by the
  schema pass and row-wide at any depth by
  ``validate_clarification_questions``'s closed-vocabulary walk — the
  ``priority`` discipline applied again, with
  ``CLARIFICATION_ORIGINS`` (``bin/bale_validate.py``) as the one-home
  constant the enum spot mirrors. Because exchange records delegate
  their question-row slot to the same function, origin propagates to
  exchange rounds with no second edit — asserted here, not assumed.
- **docs_read** — an optional list of non-empty strings in
  ``feedback.self_reported``: the docs and sections the session
  actually read, weighted as self-report like everything else in that
  stream. Shape-checked only; never added to ``required``.
- **the rider** — the telemetry schema's description now enumerates
  the one non-writer beside its writer epochs: retry's registry
  re-open (``persist_pack_session`` with ``open_telemetry=False``)
  appends no 'opened' attempt.

Plus the session-level guarantee the constraints pin: every
pre-feature manifest, question row, and exchange record keeps
validating unchanged (legacy tolerance asserted per surface below).

Oracle doctrine per ADR-0002: observable-state assertions against the
documented contract (schema files, returned error lists), never
against private internals. Hermetic and stdlib-only: schemas are read
from this repo, validators imported from ``bin/``, the lint module
loaded by file path; nothing runs and nothing writes.

Run:  python3 -m unittest tests.test_telemetry_fields_wave1 -v
  or: python3 -m unittest discover -s tests -p 'test_telemetry_fields_wave1.py'
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "bin"))

import bale_validate  # noqa: E402 — sys.path insert above is load-bearing
from bale_validate import (  # noqa: E402
    CLARIFICATION_ORIGINS,
    validate_against_schema,
    validate_clarification_questions,
    validate_exchange_record,
)

RESPONSE_SCHEMA_PATH = REPO / "schemas" / "response-manifest.schema.json"
TELEMETRY_SCHEMA_PATH = REPO / "schemas" / "telemetry-record.schema.json"


def load_response_schema() -> dict:
    return json.loads(RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8"))


def legacy_question_row() -> dict:
    """The pre-v0.4.7 four-field row — the oldest shape that must
    keep validating."""
    return {
        "question": "Which config file wins?",
        "context": "Two configs disagree on the same key.",
        "default_assumption": "The repo-root one wins.",
        "why_blocked": "Guessing wrong silently flips behavior.",
    }


def exchange_record_with(rows: list) -> dict:
    """A minimal valid worker exchange record carrying `rows`."""
    return {
        "record_version": 1,
        "session_id": "2026-09-01-wave1-fixture-001",
        "round": 1,
        "from": "worker",
        "created_at": "2026-09-01T00:00:00+00:00",
        "questions": rows,
    }


def minimal_manifest() -> dict:
    """A minimal valid normal-response manifest (schema pass only —
    the cross-field Python rules are not under test here)."""
    return {
        "session_id": "2026-09-01-wave1-fixture-001",
        "responds_to": "2026-09-01-wave1-fixture-001",
        "corrects": None,
        "summary": "fixture",
        "changes": [],
        "deferred": [],
        "validation_will_run": [],
        "claims": {},
    }


def legacy_feedback() -> dict:
    """The v0.3.8 feedback block exactly as a pre-wave-1 worker wrote
    it — no docs_read key anywhere."""
    return {
        "mechanical": {
            "response_kind": "normal",
            "schema_valid": True,
            "mirror_agreement": {
                "changes_to_files": True,
                "files_to_changes": True,
            },
            "claims_subset": True,
        },
        "self_reported": {
            "assumptions": [],
            "judgment_calls": [],
            "budget_pressure": "none",
            "includes_missing": [],
            "compaction_occurred": {"occurred": False,
                                    "disclosure_ref": None},
        },
    }


class QuestionRowOrigin(unittest.TestCase):
    """The origin enum on the clarification question row: additive,
    closed, and enforced on both surfaces."""

    def test_legacy_four_field_row_keeps_validating(self) -> None:
        self.assertEqual(
            validate_clarification_questions([legacy_question_row()]), [])

    def test_v047_extended_row_without_origin_keeps_validating(self) -> None:
        row = legacy_question_row()
        row.update(options=["root", "leaf"], recommendation="root",
                   priority="batched")
        self.assertEqual(validate_clarification_questions([row]), [])

    def test_both_origin_values_validate(self) -> None:
        for value in CLARIFICATION_ORIGINS:
            with self.subTest(origin=value):
                row = legacy_question_row()
                row["origin"] = value
                self.assertEqual(
                    validate_clarification_questions([row]), [])

    def test_origin_rides_beside_the_v047_fields(self) -> None:
        row = legacy_question_row()
        row.update(options=["root", "leaf"], recommendation="root",
                   priority="blocking", origin="intent-gap")
        self.assertEqual(validate_clarification_questions([row]), [])

    def test_invented_origin_rejects_on_both_surfaces(self) -> None:
        """The schema's named enum spot and the closed-vocabulary walk
        each report — one verdict per surface, the priority pattern."""
        row = legacy_question_row()
        row["origin"] = "vibes"
        errors = validate_clarification_questions([row])
        spot = [e for e in errors
                if e.startswith("questions[0].origin:")
                and "wherever the key appears" not in e]
        walk = [e for e in errors
                if e.startswith("questions[0].origin:")
                and "wherever the key appears" in e]
        self.assertTrue(spot, f"no schema-spot verdict in {errors!r}")
        self.assertTrue(walk, f"no walk verdict in {errors!r}")

    def test_null_origin_rejects(self) -> None:
        """Omit the key on a row that predates the vocabulary — null is
        not an origin (the claim_basis asymmetry, applied again)."""
        row = legacy_question_row()
        row["origin"] = None
        self.assertTrue(validate_clarification_questions([row]))

    def test_invented_origin_rejects_at_depth(self) -> None:
        """The walk's record-wide promise: an origin key smuggled to a
        depth the schema's named spot never enumerates still gets the
        closed-vocabulary verdict (beside the schema's own
        unknown-key rejection)."""
        row = legacy_question_row()
        row["extra"] = {"origin": "vibes"}
        errors = validate_clarification_questions([row])
        self.assertTrue(
            any(e.startswith("questions[0].extra.origin:")
                and "wherever the key appears" in e
                for e in errors),
            f"no depth verdict in {errors!r}")

    def test_exchange_record_delegation_carries_origin(self) -> None:
        """One home, free propagation: an origin-tagged row validates
        inside an exchange record, and an invented origin gets the
        identical row-validator verdicts there."""
        row = legacy_question_row()
        row["origin"] = "probe-forbidden-environment"
        self.assertEqual(
            validate_exchange_record(exchange_record_with([row])), [])

        row["origin"] = "vibes"
        record_errors = validate_exchange_record(
            exchange_record_with([row]))
        direct_errors = validate_clarification_questions([row])
        self.assertTrue(direct_errors)
        for message in direct_errors:
            self.assertIn(message, record_errors)


class QuestionRowOriginSchemaParity(unittest.TestCase):
    """The schema is the one home; the constant mirrors it and the
    additive contract holds at the shape level."""

    @classmethod
    def setUpClass(cls):
        cls.schema = load_response_schema()
        cls.row = cls.schema["properties"]["questions"]["items"]

    def test_origin_constant_mirrors_schema_enum(self) -> None:
        self.assertEqual(list(CLARIFICATION_ORIGINS),
                         self.row["properties"]["origin"]["enum"])

    def test_origin_is_not_required(self) -> None:
        self.assertNotIn("origin", self.row["required"])

    def test_required_core_is_unchanged(self) -> None:
        self.assertEqual(
            self.row["required"],
            ["question", "context", "default_assumption", "why_blocked"])


class DocsReadSelfReport(unittest.TestCase):
    """docs_read in feedback.self_reported: optional, shape-checked
    only, legacy blocks untouched."""

    @classmethod
    def setUpClass(cls):
        cls.schema = load_response_schema()

    def assert_valid(self, manifest: dict) -> None:
        self.assertEqual(validate_against_schema(manifest, self.schema), [])

    def assert_invalid(self, manifest: dict) -> None:
        self.assertTrue(validate_against_schema(manifest, self.schema))

    def test_legacy_feedback_without_docs_read_keeps_validating(self) -> None:
        manifest = minimal_manifest()
        manifest["feedback"] = legacy_feedback()
        self.assert_valid(manifest)

    def test_docs_read_with_entries_validates(self) -> None:
        manifest = minimal_manifest()
        manifest["feedback"] = legacy_feedback()
        manifest["feedback"]["self_reported"]["docs_read"] = [
            "CLAUDE.md core (META through 11.2)",
            "TARBALL.md sections 1, 2, 5, 7",
        ]
        self.assert_valid(manifest)

    def test_docs_read_honest_empty_validates(self) -> None:
        manifest = minimal_manifest()
        manifest["feedback"] = legacy_feedback()
        manifest["feedback"]["self_reported"]["docs_read"] = []
        self.assert_valid(manifest)

    def test_docs_read_rejects_empty_string_entries(self) -> None:
        manifest = minimal_manifest()
        manifest["feedback"] = legacy_feedback()
        manifest["feedback"]["self_reported"]["docs_read"] = [""]
        self.assert_invalid(manifest)

    def test_docs_read_rejects_non_array(self) -> None:
        manifest = minimal_manifest()
        manifest["feedback"] = legacy_feedback()
        manifest["feedback"]["self_reported"]["docs_read"] = "TARBALL.md"
        self.assert_invalid(manifest)

    def test_docs_read_is_not_required(self) -> None:
        self_reported = (self.schema["properties"]["feedback"]
                         ["properties"]["self_reported"])
        self.assertNotIn("docs_read", self_reported["required"])
        self.assertEqual(
            self_reported["required"],
            ["assumptions", "judgment_calls", "budget_pressure",
             "includes_missing", "compaction_occurred"])

    def test_docs_read_description_carries_the_weighting_language(self) -> None:
        """The board row's weighting doctrine travels with the field:
        self-report, like everything else in the stream."""
        description = (self.schema["properties"]["feedback"]["properties"]
                       ["self_reported"]["properties"]["docs_read"]
                       ["description"])
        self.assertIn("Self-report", description)


class EmbedCarriesWave1(unittest.TestCase):
    """tools/response_lint.py's vendored schema carries both wave-1
    fields. test_schema_embeds pins full JSON-equality; this names the
    feature so a stale embed fails by name here too."""

    @classmethod
    def setUpClass(cls):
        lint_path = REPO / "tools" / "response_lint.py"
        spec = importlib.util.spec_from_file_location(
            "response_lint_wave1_under_test", lint_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        cls.embed = json.loads(module.RESPONSE_MANIFEST_SCHEMA_JSON)

    def test_embed_has_origin(self) -> None:
        row = self.embed["properties"]["questions"]["items"]
        self.assertEqual(row["properties"]["origin"]["enum"],
                         list(CLARIFICATION_ORIGINS))

    def test_embed_has_docs_read(self) -> None:
        self_reported = (self.embed["properties"]["feedback"]
                         ["properties"]["self_reported"])
        self.assertIn("docs_read", self_reported["properties"])
        self.assertNotIn("docs_read", self_reported["required"])


class RetryOpenTelemetryRider(unittest.TestCase):
    """The folded doc rider: the telemetry schema's description names
    open_telemetry and states that retry's registry re-open appends no
    'opened' attempt — the fix documented beside the writer epochs it
    completes, not only in code comments."""

    @classmethod
    def setUpClass(cls):
        cls.description = json.loads(
            TELEMETRY_SCHEMA_PATH.read_text(encoding="utf-8"))["description"]

    def test_description_names_open_telemetry(self) -> None:
        self.assertIn("open_telemetry", self.description)

    def test_description_states_no_opened_attempt(self) -> None:
        self.assertIn("appends no 'opened' attempt", self.description)


class LegacyToleranceUnchangedElsewhere(unittest.TestCase):
    """The additive contract's blast radius is zero: a pre-feature
    clarification manifest (questions block, no origin; no feedback)
    still passes the schema pass unchanged."""

    def test_pre_feature_clarification_manifest_validates(self) -> None:
        manifest = minimal_manifest()
        manifest["response_kind"] = "clarification"
        manifest["questions"] = [legacy_question_row()]
        schema = load_response_schema()
        self.assertEqual(validate_against_schema(manifest, schema), [])

    def test_deep_copies_left_fixtures_unmutated(self) -> None:
        """Guard the fixtures themselves: builders return fresh dicts,
        so cross-test mutation can't fake a pass."""
        a, b = legacy_question_row(), legacy_question_row()
        a["origin"] = "intent-gap"
        self.assertNotIn("origin", b)
        f = legacy_feedback()
        copy.deepcopy(f)["self_reported"]["docs_read"] = ["x"]
        self.assertNotIn("docs_read", f["self_reported"])


class SandboxPosturePairLegacyTolerance(unittest.TestCase):
    """The v0.4.26 (board 75) telemetry addition on this file's own
    terms — the per-surface legacy-tolerance assertion: a record from
    any earlier epoch (no posture pair) and a record from this one
    (pair present) both validate, and the schema description names
    the loud-every-run guarantee the pair records. The vocabulary's
    enforcement lives in test_telemetry_extensions; this is the
    additive-contract check only."""

    def _record(self, **attempt_extra) -> dict:
        attempt = {"at": "2026-09-10T00:00:00+00:00",
                   "outcome": "applied", "command": "apply"}
        attempt.update(attempt_extra)
        return {"record_version": 1,
                "session_id": "2026-09-10-fx-w75-001",
                "created_at": "2026-09-10T00:00:00+00:00",
                "updated_at": "2026-09-10T00:00:00+00:00",
                "outcome": "applied", "attempts": [attempt]}

    def test_pre_v0426_attempt_validates_unchanged(self) -> None:
        # The S2-epoch shape: sandbox stamps present, no posture pair.
        rec = self._record(sandbox_escaped=True,
                           network_grant_exercised=False)
        self.assertEqual(bale_validate.validate_telemetry_record(rec), [])

    def test_v0426_attempt_validates(self) -> None:
        rec = self._record(sandbox_escaped=False,
                           network_grant_exercised=False,
                           sandbox_confined=False,
                           sandbox_off_source="config")
        self.assertEqual(bale_validate.validate_telemetry_record(rec), [])

    def test_record_version_unchanged(self) -> None:
        """Additive means record_version stays 1 — a record carrying
        the pair validates at version 1, so consumers need no branch,
        and the schema's own description records no bump for it."""
        rec = self._record(sandbox_confined=True, sandbox_off_source=None)
        self.assertEqual(rec["record_version"], 1)
        self.assertEqual(bale_validate.validate_telemetry_record(rec), [])
        description = json.loads(
            TELEMETRY_SCHEMA_PATH.read_text(encoding="utf-8"))["description"]
        self.assertIn("record_version stays 1", description)

    def test_description_names_the_loudness_contract(self) -> None:
        schema = json.loads(
            TELEMETRY_SCHEMA_PATH.read_text(encoding="utf-8"))
        props = schema["properties"]["attempts"]["items"]["properties"]
        text = (props["sandbox_confined"]["description"]
                + props["sandbox_confined"].get("$comment", ""))
        self.assertIn("FORCE", text)
        self.assertIn("config", props["sandbox_off_source"]["description"])
        self.assertIn("flag", props["sandbox_off_source"]["description"])


if __name__ == "__main__":
    unittest.main()
