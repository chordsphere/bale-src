#!/usr/bin/env python3
"""Schema-admission pins for the five-doc contract_docs block (v0.4.11).

PLANNER.md joined the injected global-doc set in the planner-injection
wiring session. The ratified admission posture is allowed-not-required:

- five keys validate (the post-wiring stamp),
- four keys still validate (one-apply-behind: the wiring session's own
  response echoes a four-key block, and telemetry history must stay
  parseable),
- PLANNER.md is required NOWHERE (a manifest carrying it but missing a
  required member still fails on the missing member, never on
  PLANNER.md's absence),
- additionalProperties stays false (a sixth, unknown doc key refuses —
  the set grows by schema edit, not free text).

Both schemas of record are pinned — request-manifest for the pack-time
stamp, response-manifest for the feedback.mechanical.provenance echo —
through the lint's embedded generic validator, the same instrument the
WaiverSchemaUnitTest precedent (tests/test_per_sid_checkpoint.py) uses:
the schema FILES are the instances' schemas of record here, while
tests/test_schema_embeds.py separately guards that the lint's embedded
response-manifest copy is JSON-equal to the file, so the pair of suites
together covers both the source and the shipped copy.

Run:  python3 -m unittest tests.test_planner_admission -v
  or: python3 tests/test_planner_admission.py
"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

FOUR_DOCS = ("CLAUDE.md", "TARBALL.md", "DOCS.md", "CODE.md")
FIVE_DOCS = FOUR_DOCS + ("PLANNER.md",)


def contract_docs(names) -> dict:
    """A contract_docs block with a placeholder digest per named doc."""
    return {name: "a" * 64 for name in names}


class PlannerAdmissionTest(unittest.TestCase):
    """contract_docs admits PLANNER.md everywhere and requires it nowhere."""

    @classmethod
    def setUpClass(cls) -> None:
        spec = importlib.util.spec_from_file_location(
            "response_lint_for_admission_test",
            REPO_ROOT / "tools" / "response_lint.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Hold the MODULE, not the bare function: a plain function
        # assigned as a class attribute binds as a method, silently
        # feeding `self` as the instance under validation — the
        # vacuous-pass shape the WaiverSchemaUnitTest precedent refuses.
        cls.lint = module
        cls.request_schema = json.loads(
            (REPO_ROOT / "schemas" /
             "request-manifest.schema.json").read_text(encoding="utf-8"))
        cls.response_schema = json.loads(
            (REPO_ROOT / "schemas" /
             "response-manifest.schema.json").read_text(encoding="utf-8"))

    # -- fixtures ---------------------------------------------------------

    def request_manifest(self, docs) -> dict:
        return {
            "session_id": "2026-08-16-x-001",
            "project": "p",
            "goal": "g",
            "depends_on": {"previous_response": None,
                           "previous_probe": None},
            "constraints": [],
            "out_of_scope": [],
            "expects_probe": "claude-decides",
            "context_included": ["context/hello.txt"],
            "resolved_scope": [],
            "provenance": {
                "bale_version": "0.4.11",
                "contract_docs": contract_docs(docs),
                "packer": "test",
                "work_class": "meta",
                "checkpoint": None,
                "checkpoint_scope_admitted": False,
            },
        }

    def response_manifest(self, docs) -> dict:
        return {
            "session_id": "2026-08-16-x-001",
            "responds_to": "2026-08-16-x-001",
            "corrects": None,
            "response_kind": "normal",
            "summary": "s",
            "changes": [],
            "deferred": [],
            "validation_will_run": [],
            "claims": {},
            "feedback": {
                "mechanical": {
                    "response_kind": "normal",
                    "schema_valid": True,
                    "mirror_agreement": {"changes_to_files": True,
                                         "files_to_changes": True},
                    "claims_subset": True,
                    "provenance": {
                        "bale_version": "0.4.11",
                        "contract_docs": contract_docs(docs),
                        "packer": "test",
                        "work_class": "meta",
                        "model_identity": "test",
                    },
                },
                "self_reported": {
                    "assumptions": [],
                    "judgment_calls": [],
                    "budget_pressure": "none",
                    "includes_missing": [],
                    "compaction_occurred": {"occurred": False,
                                            "disclosure_ref": None},
                },
            },
        }

    def assert_valid(self, instance, schema) -> None:
        errors = self.lint.schema_validate(instance, schema)
        self.assertEqual(errors, [], msg="; ".join(errors))

    def assert_invalid(self, instance, schema, why: str) -> None:
        errors = self.lint.schema_validate(instance, schema)
        self.assertTrue(errors, msg=why)

    # -- request-manifest: the pack-time stamp ---------------------------

    def test_request_five_key_stamp_validates(self) -> None:
        self.assert_valid(self.request_manifest(FIVE_DOCS),
                          self.request_schema)

    def test_request_four_key_stamp_still_validates(self) -> None:
        """One-apply-behind: pre-v0.4.11 stamps stay valid."""
        self.assert_valid(self.request_manifest(FOUR_DOCS),
                          self.request_schema)

    def test_request_planner_required_nowhere(self) -> None:
        """PLANNER.md present cannot stand in for a required member —
        the failure is the missing required doc, never a new
        PLANNER.md requirement."""
        docs = ("CLAUDE.md", "TARBALL.md", "DOCS.md", "PLANNER.md")
        self.assert_invalid(
            self.request_manifest(docs), self.request_schema,
            why="CODE.md is required; PLANNER.md must not satisfy it")

    def test_request_unknown_sixth_key_refuses(self) -> None:
        """additionalProperties stays false: the set grows by schema
        edit, not free text."""
        self.assert_invalid(
            self.request_manifest(FIVE_DOCS + ("MYSTERY.md",)),
            self.request_schema,
            why="an unknown sixth doc key must refuse")

    # -- response-manifest: the provenance echo ---------------------------

    def test_response_five_key_echo_validates(self) -> None:
        self.assert_valid(self.response_manifest(FIVE_DOCS),
                          self.response_schema)

    def test_response_four_key_echo_still_validates(self) -> None:
        """The wiring session's own response echoes a four-key block —
        correct, not a defect."""
        self.assert_valid(self.response_manifest(FOUR_DOCS),
                          self.response_schema)

    def test_response_unknown_sixth_key_refuses(self) -> None:
        self.assert_invalid(
            self.response_manifest(FIVE_DOCS + ("MYSTERY.md",)),
            self.response_schema,
            why="an unknown sixth doc key must refuse in the echo")


if __name__ == "__main__":
    unittest.main()
