#!/usr/bin/env python3
"""The board 10 S4 escalation-contract schemas (v0.4.7): the escalation
record, the clarification questions[] extension, and the claim_basis
manifest carrier.

Three additive surfaces, doctrine home orchestration.md section 8 (the
schemas point at it; nothing here restates it):

- **validate_escalation_record** (``bin/bale_validate.py``) — the
  per-record entry point over ``schemas/escalation-record.schema.json``,
  pinned by name: ``validate_escalation_record(record: dict) -> list``,
  empty list = valid, strings = errors. Six-field required core
  (question, options, recommendation, priority, subsumes,
  amendment_target), loose envelope (additive fields tolerated), and
  the CLOSED priority vocabulary (``blocking`` | ``batched``) enforced
  record-wide by the vocabulary walk — an invented class rejects at any
  depth, not only at the schema-named spot (the S5 single-spot-enum
  lesson).
- **validate_clarification_questions** (``bin/bale_validate.py``) —
  pinned by name: ``validate_clarification_questions(rows: list) ->
  list``, over the response manifest schema's own questions items (one
  home; the sub-schema is derived, never duplicated). Legacy four-field
  rows keep validating; extended rows add any of ``options`` (non-empty
  when present), ``recommendation``, and ``priority`` (same closed
  enum, same row-wide walk).
- **the claim_basis manifest carrier** — a response manifest ``claims``
  value is the legacy bare string or the annotated
  ``{"value": ..., "claim_basis": ...}`` object (the exact record-side
  shape S5's telemetry schema already accepts), with the bare-string
  vocabulary moved to ``validate_response_manifest``'s Python layer
  (the schema-validator subset has no oneOf). One e2e apply pins the
  pipeline: the annotated map validates at pre-flight, reconciles in
  validation.sh (the crafted epilogue compares the unwrapped value),
  and promotes verbatim into ``attempts[].validation.claims``, where
  ``validate_telemetry_record`` accepts it; a second e2e pins the moved
  bare-string check rejecting an invented claim word.

Oracle doctrine per ADR-0002: observable-state assertions against the
documented contract (schema files, returned error lists, the written
telemetry record, apply's stdout), never against private internals.

Hermetic: the library classes are in-process module work over this
repo's own files plus one bare ``python3 -c`` import-posture check;
the two e2e tests run through the shared sandboxed harness.

Run directly::

    python3 tests/test_escalation_schemas.py

or via ``python3 -m unittest discover -s tests``.
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

from harness import (
    bale_env,
    build_response_dir,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_checked,
    slow,
    tar_response_dir,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
BIN = REPO_ROOT / "bin"
ESCALATION_SCHEMA_PATH = REPO_ROOT / "schemas" / "escalation-record.schema.json"
RESPONSE_SCHEMA_PATH = REPO_ROOT / "schemas" / "response-manifest.schema.json"


def _load_module(name: str):
    """Load a bin/ sibling by path, unregistered — the modules import
    nothing from __main__ at module scope, which is exactly the
    library-import property the checkpoint contract relies on."""
    spec = importlib.util.spec_from_file_location(
        f"{name}_under_test", BIN / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def minimal_escalation_record() -> dict:
    """The smallest-valid record: exactly the six-field required core."""
    return {
        "question": "Which auth flow does the seed doc intend?",
        "options": ["session cookie", "stateless JWT"],
        "recommendation": "session cookie",
        "priority": "blocking",
        "subsumes": [],
        "amendment_target": "claude/context/decisions.md",
    }


def legacy_question_row() -> dict:
    """A pre-v0.4.7 four-field clarification question row."""
    return {
        "question": "Which auth flow?",
        "context": "wiring the login endpoint",
        "default_assumption": "session cookie, matching the existing app",
        "why_blocked": "the two flows imply different session storage",
    }


def extended_question_row() -> dict:
    """A v0.4.7 row carrying all three optional fields."""
    row = legacy_question_row()
    row.update({
        "options": ["session cookie", "stateless JWT"],
        "recommendation": "session cookie",
        "priority": "batched",
    })
    return row


class EscalationRecordValidationTest(unittest.TestCase):
    """validate_escalation_record: the pinned core, rejections, and the
    record-wide priority vocabulary."""

    @classmethod
    def setUpClass(cls):
        cls.bv = _load_module("bale_validate")

    def test_minimal_six_field_record_validates(self) -> None:
        self.assertEqual(
            self.bv.validate_escalation_record(minimal_escalation_record()),
            [])

    def test_each_missing_core_field_rejects(self) -> None:
        """Every one of the six core fields is required — its absence is
        named in the error (the pinned missing-recommendation case is
        one instance of the loop)."""
        for field in ("question", "options", "recommendation", "priority",
                      "subsumes", "amendment_target"):
            with self.subTest(missing=field):
                record = minimal_escalation_record()
                del record[field]
                errors = self.bv.validate_escalation_record(record)
                self.assertTrue(any(field in e for e in errors),
                                msg=f"errors: {errors}")

    def test_priority_outside_enum_rejects(self) -> None:
        record = minimal_escalation_record()
        record["priority"] = "urgent"
        errors = self.bv.validate_escalation_record(record)
        self.assertTrue(any("priority" in e for e in errors))

    def test_priority_rejects_at_any_depth(self) -> None:
        """The vocabulary walk's point: an invented class inside a field
        the schema never enumerated gets the same verdict as the named
        spot — a blind consumer's placement choice cannot smuggle one."""
        record = minimal_escalation_record()
        record["producer_extra"] = {
            "batch": [{"priority": "whenever"}]}
        errors = self.bv.validate_escalation_record(record)
        self.assertTrue(
            any("producer_extra.batch[0].priority" in e for e in errors),
            msg=f"errors: {errors}")

    def test_subsumes_bare_string_rejects(self) -> None:
        record = minimal_escalation_record()
        record["subsumes"] = "2026-08-12-worker-a-001"
        errors = self.bv.validate_escalation_record(record)
        self.assertTrue(any("subsumes" in e and "array" in e
                            for e in errors))

    def test_empty_options_rejects(self) -> None:
        record = minimal_escalation_record()
        record["options"] = []
        errors = self.bv.validate_escalation_record(record)
        self.assertTrue(any("options" in e for e in errors))

    def test_loose_envelope_tolerates_additive_fields(self) -> None:
        """additionalProperties true at the envelope: a future producer's
        extra field never rejects an otherwise-valid record."""
        record = minimal_escalation_record()
        record.update({
            "record_version": 1,
            "escalation_id": "esc-0001",
            "session_id": "2026-08-13-master-distill-001",
            "created_at": "2026-08-13T00:00:00+00:00",
            "status": "open",
            "some_future_field": {"anything": True},
        })
        self.assertEqual(self.bv.validate_escalation_record(record), [])

    def test_status_enum_is_closed_at_its_spot(self) -> None:
        record = minimal_escalation_record()
        record["status"] = "parked"
        errors = self.bv.validate_escalation_record(record)
        self.assertTrue(any("status" in e for e in errors))

    def test_non_dict_is_an_error_not_an_exception(self) -> None:
        errors = self.bv.validate_escalation_record(["not", "a", "record"])
        self.assertEqual(len(errors), 1)
        self.assertIn("not a JSON object", errors[0])

    def test_schema_file_pins_the_contract(self) -> None:
        """The shipped schema itself carries the pinned surface: the six
        required, the closed priority enum, options minItems 1."""
        schema = json.loads(
            ESCALATION_SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(schema["required"]),
            sorted(["question", "options", "recommendation", "priority",
                    "subsumes", "amendment_target"]))
        self.assertEqual(schema["properties"]["priority"]["enum"],
                         ["blocking", "batched"])
        self.assertEqual(schema["properties"]["options"]["minItems"], 1)
        self.assertIs(schema["additionalProperties"], True,
                      msg="the envelope is deliberately loose")


class ClarificationQuestionRowsTest(unittest.TestCase):
    """validate_clarification_questions: legacy rows survive, extended
    rows validate, the enum holds on both the schema spot and the walk."""

    @classmethod
    def setUpClass(cls):
        cls.bv = _load_module("bale_validate")

    def test_legacy_four_field_row_validates(self) -> None:
        self.assertEqual(
            self.bv.validate_clarification_questions([legacy_question_row()]),
            [])

    def test_extended_row_validates(self) -> None:
        self.assertEqual(
            self.bv.validate_clarification_questions(
                [extended_question_row()]),
            [])

    def test_partial_extensions_validate(self) -> None:
        """The three fields are independently optional."""
        for extra in ({"priority": "blocking"},
                      {"options": ["a"]},
                      {"recommendation": "a"},
                      {"options": ["a", "b"], "recommendation": "b"}):
            with self.subTest(extra=extra):
                row = legacy_question_row()
                row.update(extra)
                self.assertEqual(
                    self.bv.validate_clarification_questions([row]), [])

    def test_priority_outside_enum_rejects_with_row_path(self) -> None:
        row = extended_question_row()
        row["priority"] = "soon"
        errors = self.bv.validate_clarification_questions(
            [legacy_question_row(), row])
        self.assertTrue(any("questions[1].priority" in e for e in errors),
                        msg=f"errors: {errors}")

    def test_empty_options_rejects(self) -> None:
        row = legacy_question_row()
        row["options"] = []
        errors = self.bv.validate_clarification_questions([row])
        self.assertTrue(any("options" in e for e in errors))

    def test_unknown_row_key_rejects(self) -> None:
        """The item schema stays additionalProperties:false — the row
        vocabulary grows by schema amendment, never by drift."""
        row = legacy_question_row()
        row["severity"] = "high"
        errors = self.bv.validate_clarification_questions([row])
        self.assertTrue(any("severity" in e for e in errors))

    def test_non_list_is_an_error_not_an_exception(self) -> None:
        errors = self.bv.validate_clarification_questions(
            {"question": "not rows"})
        self.assertEqual(len(errors), 1)
        self.assertIn("not a JSON array", errors[0])

    def test_sub_schema_is_derived_not_duplicated(self) -> None:
        """One home: the rows validate against the response manifest
        schema's own questions items — the file pins the three optional
        fields and the closed enum where the validator reads them."""
        schema = json.loads(
            RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8"))
        item = schema["properties"]["questions"]["items"]
        self.assertEqual(
            sorted(item["required"]),
            sorted(["question", "context", "default_assumption",
                    "why_blocked"]),
            msg="the four legacy fields stay the only required ones")
        self.assertEqual(item["properties"]["priority"]["enum"],
                         ["blocking", "batched"])
        self.assertEqual(item["properties"]["options"]["minItems"], 1)


class LibraryImportPostureTest(unittest.TestCase):
    """Both entry points hold the checkpoint contract's import posture:
    a bare interpreter imports bale_validate and calls them with no bale
    process and no __main__.fail in sight."""

    def test_bare_python_import_and_calls(self) -> None:
        code = (
            "import json, sys\n"
            f"sys.path.insert(0, {str(BIN)!r})\n"
            "import bale_validate as bv\n"
            "rec = {'question': 'q', 'options': ['a'],\n"
            "       'recommendation': 'a', 'priority': 'blocking',\n"
            "       'subsumes': [], 'amendment_target': 'seed.md'}\n"
            "assert bv.validate_escalation_record(rec) == []\n"
            "assert bv.validate_escalation_record({'priority': 'x'})\n"
            "row = {'question': 'q', 'context': 'c',\n"
            "       'default_assumption': 'd', 'why_blocked': 'w'}\n"
            "assert bv.validate_clarification_questions([row]) == []\n"
            "print('LIBRARY-OK')\n"
        )
        result = subprocess.run(
            [sys.executable, "-c", code],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("LIBRARY-OK", result.stdout)


class ClaimsCarrierSchemaTest(unittest.TestCase):
    """The annotated claims form at the schema layer, via the same
    validate_against_schema pass bale's pre-flight runs."""

    @classmethod
    def setUpClass(cls):
        cls.bv = _load_module("bale_validate")
        cls.schema = json.loads(
            RESPONSE_SCHEMA_PATH.read_text(encoding="utf-8"))

    def base_manifest(self, claims: dict) -> dict:
        return {
            "session_id": "2026-08-13-fx-claims-001",
            "responds_to": "2026-08-13-fx-claims-001",
            "corrects": None,
            "response_kind": "normal",
            "summary": "claims carrier schema fixture",
            "changes": [],
            "deferred": [],
            "validation_will_run": ["suite"],
            "claims": claims,
        }

    def assert_schema_ok(self, claims: dict) -> None:
        errors = self.bv.validate_against_schema(
            self.base_manifest(claims), self.schema)
        self.assertEqual(errors, [])

    def assert_schema_rejects(self, claims: dict, fragment: str) -> None:
        errors = self.bv.validate_against_schema(
            self.base_manifest(claims), self.schema)
        self.assertTrue(any(fragment in e for e in errors),
                        msg=f"errors: {errors}")

    def test_bare_string_still_validates(self) -> None:
        self.assert_schema_ok({"suite": "pass"})

    def test_annotated_form_validates(self) -> None:
        for basis in ("predicted", "observed"):
            with self.subTest(basis=basis):
                self.assert_schema_ok(
                    {"suite": {"value": "pass", "claim_basis": basis}})

    def test_annotated_form_without_basis_validates(self) -> None:
        """claim_basis stays optional on the object form — the exact
        record-side looseness (omit the key when the basis is unknown)."""
        self.assert_schema_ok({"suite": {"value": "unknown"}})

    def test_invented_basis_rejects(self) -> None:
        self.assert_schema_rejects(
            {"suite": {"value": "pass", "claim_basis": "vibes"}},
            "claim_basis")

    def test_null_basis_rejects(self) -> None:
        self.assert_schema_rejects(
            {"suite": {"value": "pass", "claim_basis": None}},
            "claim_basis")

    def test_missing_value_rejects(self) -> None:
        self.assert_schema_rejects(
            {"suite": {"claim_basis": "predicted"}}, "value")

    def test_invented_value_in_object_rejects(self) -> None:
        self.assert_schema_rejects(
            {"suite": {"value": "probably"}}, "value")

    def test_unknown_object_key_rejects(self) -> None:
        self.assert_schema_rejects(
            {"suite": {"value": "pass", "basis": "predicted"}}, "basis")


class AnnotatedClaimsApplyE2ETest(unittest.TestCase):
    """The carrier through the real pipeline: pre-flight accepts, the
    crafted epilogue reconciles the unwrapped value, promotion into the
    telemetry record is verbatim, and the moved bare-string vocabulary
    check rejects an invented claim word."""

    CHECK = "fixture check"

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-claims-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        result = run_bale(
            self.install,
            ["pack", "claims carrier fixture session",
             "--slug", "claimscarrier",
             "--include", "hello.txt",
             "--no-readme"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        self.sid = sids[0]

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def build_tarball(self, claims: dict) -> Path:
        rdir = build_response_dir(
            self.tmp / "resp", self.sid,
            summary="claims carrier fixture: modify hello.txt",
            entries=[{
                "path": "hello.txt", "action": "modified",
                "reason": "carrier fixture body",
                "data": b"hello from the carrier fixture\n",
            }],
            validation_sh=(
                "#!/usr/bin/env bash\n"
                f"echo \"[PASS] {self.CHECK}\"\n"
                "echo \"claims vs verdict:\"\n"
                f"echo \"  {self.CHECK}: claim=pass verdict=pass "
                "[agree]\"\n"
                "exit 0\n"),
            validation_will_run=[self.CHECK],
            claims=claims,
        )
        return tar_response_dir(rdir)

    @slow
    def test_annotated_claims_apply_and_promote_verbatim(self) -> None:
        annotated = {self.CHECK: {"value": "pass",
                                  "claim_basis": "observed"}}
        tarball = self.build_tarball(annotated)
        result = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("[PASS]", result.stdout)
        record_path = (self.repo / "claude" / "telemetry"
                       / f"{self.sid}.json")
        record = json.loads(record_path.read_text(encoding="utf-8"))
        promoted = record["attempts"][-1]["validation"]["claims"]
        self.assertEqual(promoted, annotated,
                         msg="promotion is verbatim — the annotated "
                             "object arrives unchanged")
        bv = _load_module("bale_validate")
        self.assertEqual(bv.validate_telemetry_record(record), [],
                         msg="the written record validates, annotated "
                             "claims included")

    def test_invented_bare_string_claim_rejects_at_preflight(self) -> None:
        """The vocabulary check that moved from the schema's enum into
        validate_response_manifest still holds on the installed path."""
        tarball = self.build_tarball({self.CHECK: "maybe"})
        result = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn("'maybe'", combined)
        self.assertIn("is not one of", combined)


if __name__ == "__main__":
    unittest.main()
