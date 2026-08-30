#!/usr/bin/env python3
"""The exchange record's library validator and schema parity (v0.4.18,
ADR-0017; contract BALE.md §8.11, row §11.34).

Pins, at the library layer (no bale process, the validate_bundle_manifest
posture):

- **validate_exchange_record(record) -> list** — ``[]`` for a valid
  worker record, planner record, and a both-arrays record; error
  strings otherwise, never a raise on data (a non-dict is reported).
- **The closed vocabularies are record-wide.** An invented ``from`` or
  ``disposition`` rejects at the schema-named spot AND at any depth the
  schema never enumerated (the _walk_closed_vocabularies discipline).
- **The rules the schema subset cannot express** — at least one of
  questions[] / answers[] non-empty; ``created_at`` ISO 8601 with a
  zero UTC offset (``Z`` accepted; naive and non-UTC refused); every
  answer's ``question_round`` earlier than the record's own round.
- **The question rows by reference.** questions[] delegates to
  validate_clarification_questions, so a row that fails inside a
  clarification manifest fails here with the same questions[i] path.
- **The envelope is loose.** The preserved copy's ``preserved_at``
  sidecar, and any future additive top-level key, keeps validating;
  the answer row is closed (an unknown key there rejects).
- **Parity.** The Python constants (EXCHANGE_SIDES,
  ANSWER_DISPOSITIONS, EXCHANGE_RECORD_VERSION) equal the schema's enum
  spots — the INTENT_PROMPTS precedent: constants the tests pin, never
  a second copy of the field set — and the schema's questions.items is
  a $ref into response-manifest.schema.json's questions.items (one
  home), with the schema listed by validate.sh's well-formedness walk.

Hermetic and stdlib-only (ADR-0005): bin/bale_validate.py is imported
from this repo with bin/ on sys.path; nothing touches the developer's
environment. One fixture per scenario, built inline from the shared
minimal records below.

Run:  python3 -m unittest tests.test_exchange_record -v
  or: python3 -m unittest discover -s tests -p 'test_exchange_record.py'
"""

from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "bin"))

import bale_validate  # noqa: E402 — sys.path insert above is load-bearing
from bale_validate import validate_exchange_record  # noqa: E402

SID = "2026-08-29-fixture-001"

QUESTION_ROW = {
    "question": "Which base?",
    "context": "choosing the validation base",
    "default_assumption": "the {sid} form",
    "why_blocked": "a literal base is project-wide",
    "options": ["{sid} form", "literal"],
    "recommendation": "{sid} form",
    "priority": "blocking",
}


def worker_record() -> dict:
    return {
        "record_version": 1,
        "session_id": SID,
        "round": 1,
        "from": "worker",
        "created_at": "2026-08-29T14:03:00+00:00",
        "questions": [copy.deepcopy(QUESTION_ROW)],
    }


def planner_record() -> dict:
    return {
        "record_version": 1,
        "session_id": SID,
        "round": 2,
        "from": "planner",
        "created_at": "2026-08-29T15:00:00Z",
        "answers": [
            {
                "question_round": 1,
                "question_index": 0,
                "answer": "the {sid} form",
                "disposition": "as-recommended",
                "amendment_target": "claude/context/adr/0018-bases.md",
            }
        ],
    }


class ValidExchangeRecords(unittest.TestCase):
    """The three shapes the doctrine names validate clean."""

    def test_worker_record_is_valid(self) -> None:
        self.assertEqual(validate_exchange_record(worker_record()), [])

    def test_planner_record_is_valid(self) -> None:
        self.assertEqual(validate_exchange_record(planner_record()), [])

    def test_answering_and_asking_back_in_one_record(self) -> None:
        rec = planner_record()
        rec["questions"] = [copy.deepcopy(QUESTION_ROW)]
        self.assertEqual(validate_exchange_record(rec), [])

    def test_preserved_sidecar_and_additive_keys_tolerated(self) -> None:
        """The envelope is loose: the preserved copy (preserved_at) and a
        future additive key both validate — a preserved record must
        re-validate as-is."""
        rec = worker_record()
        rec["preserved_at"] = "2026-08-29T14:04:00+00:00"
        rec["future_key"] = {"anything": True}
        self.assertEqual(validate_exchange_record(rec), [])


class RefusedExchangeRecords(unittest.TestCase):
    """Each rule refuses by name, on its own fixture."""

    def assert_error_mentions(self, errors: list, *needles: str) -> None:
        joined = "\n".join(errors)
        for needle in needles:
            self.assertIn(needle, joined, msg=f"errors:\n{joined}")

    def test_non_dict_is_reported_not_raised(self) -> None:
        errors = validate_exchange_record(["not", "a", "record"])
        self.assertEqual(len(errors), 1)
        self.assert_error_mentions(errors, "not a JSON object")

    def test_missing_required_core(self) -> None:
        rec = worker_record()
        del rec["created_at"]
        del rec["round"]
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "missing required key 'created_at'",
                                   "missing required key 'round'")

    def test_record_version_pinned_to_one(self) -> None:
        rec = worker_record()
        rec["record_version"] = 2
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "record_version: 2 is not one of [1]")

    def test_round_below_one(self) -> None:
        rec = worker_record()
        rec["round"] = 0
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "round: 0 is below minimum 1")

    def test_from_vocabulary_closed_at_named_spot(self) -> None:
        rec = worker_record()
        rec["from"] = "master"
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "from: 'master' is not one of")

    def test_from_vocabulary_closed_at_any_depth(self) -> None:
        """The record-wide walk: an invented side nested where the schema
        never named the key still rejects."""
        rec = worker_record()
        rec["extra"] = {"from": "harness"}
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "extra.from: 'harness' is not one of")

    def test_disposition_vocabulary_closed_at_named_spot(self) -> None:
        rec = planner_record()
        rec["answers"][0]["disposition"] = "maybe"
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "answers[0].disposition: 'maybe'")

    def test_disposition_vocabulary_closed_at_any_depth(self) -> None:
        rec = planner_record()
        rec["note"] = {"disposition": "shrug"}
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "note.disposition: 'shrug'")

    def test_answer_row_is_closed(self) -> None:
        rec = planner_record()
        rec["answers"][0]["confidence"] = "high"
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "answers[0]: unknown key 'confidence'")

    def test_answer_row_required_fields(self) -> None:
        rec = planner_record()
        del rec["answers"][0]["answer"]
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "answers[0]: missing required key 'answer'")

    def test_empty_answer_text(self) -> None:
        rec = planner_record()
        rec["answers"][0]["answer"] = ""
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "answers[0].answer: string is shorter")

    def test_both_arrays_empty_refuses(self) -> None:
        rec = worker_record()
        rec["questions"] = []
        rec["answers"] = []
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "at least one of questions[] / answers[]")

    def test_both_arrays_absent_refuses(self) -> None:
        rec = worker_record()
        del rec["questions"]
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "at least one of questions[] / answers[]")

    def test_created_at_naive_refuses(self) -> None:
        rec = worker_record()
        rec["created_at"] = "2026-08-29T14:03:00"
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "created_at:", "no UTC offset")

    def test_created_at_non_utc_refuses(self) -> None:
        rec = worker_record()
        rec["created_at"] = "2026-08-29T14:03:00+02:00"
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "created_at:", "not in UTC")

    def test_created_at_garbage_refuses(self) -> None:
        rec = worker_record()
        rec["created_at"] = "yesterday"
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "created_at:", "not an ISO 8601")

    def test_answer_cannot_key_own_or_later_round(self) -> None:
        rec = planner_record()
        rec["answers"][0]["question_round"] = 2
        self.assert_error_mentions(validate_exchange_record(rec),
                                   "answers[0].question_round: 2 is not an "
                                   "earlier round than this record's round 2")

    def test_question_rows_validated_by_reference(self) -> None:
        """A row that fails the response manifest's questions.items
        fails here with the same questions[i] path — one home."""
        rec = worker_record()
        rec["questions"][0]["priority"] = "urgent"
        del rec["questions"][0]["why_blocked"]
        errors = validate_exchange_record(rec)
        self.assert_error_mentions(errors,
                                   "questions[0]: missing required key "
                                   "'why_blocked'",
                                   "questions[0].priority: 'urgent'")
        # And the same verdict from the row validator directly.
        direct = bale_validate.validate_clarification_questions(
            rec["questions"])
        self.assertTrue(direct)
        for message in direct:
            self.assertIn(message, errors)


class ExchangeSchemaParity(unittest.TestCase):
    """The schema is the one home; the constants and $ref mirror it."""

    @classmethod
    def setUpClass(cls):
        cls.schema = json.loads(
            (REPO / "schemas" / "exchange-record.schema.json")
            .read_text(encoding="utf-8"))
        cls.props = cls.schema["properties"]

    def test_id_follows_sibling_convention(self) -> None:
        self.assertEqual(
            self.schema["$id"],
            "https://github.com/anthropics/bale/schemas/"
            "exchange-record.schema.json")

    def test_sides_constant_mirrors_schema(self) -> None:
        self.assertEqual(list(bale_validate.EXCHANGE_SIDES),
                         self.props["from"]["enum"])

    def test_dispositions_constant_mirrors_schema(self) -> None:
        self.assertEqual(
            list(bale_validate.ANSWER_DISPOSITIONS),
            self.props["answers"]["items"]["properties"]["disposition"]
            ["enum"])

    def test_record_version_constant_mirrors_schema(self) -> None:
        self.assertEqual([bale_validate.EXCHANGE_RECORD_VERSION],
                         self.props["record_version"]["enum"])

    def test_questions_items_reference_the_response_manifest_row(self) -> None:
        """One home for the question row: the schema points at the
        response manifest's questions.items, and the pointer resolves
        to the row validate_clarification_questions derives from."""
        ref = self.props["questions"]["items"]["$ref"]
        rm = json.loads((REPO / "schemas" / "response-manifest.schema.json")
                        .read_text(encoding="utf-8"))
        base, _, pointer = ref.partition("#")
        self.assertEqual(base, rm["$id"])
        self.assertEqual(pointer, "/properties/questions/items")
        self.assertIn("why_blocked",
                      rm["properties"]["questions"]["items"]["required"])

    def test_envelope_loose_answer_row_closed(self) -> None:
        self.assertIs(self.schema["additionalProperties"], True)
        self.assertIs(self.props["answers"]["items"]["additionalProperties"],
                      False)

    def test_validate_sh_walks_the_schema(self) -> None:
        """validate.sh names each shipped schema explicitly (its own
        comment: a session adding a schema extends the list) — a
        schema the walk does not know is a silent skip."""
        text = (REPO / "validate.sh").read_text(encoding="utf-8")
        self.assertRegex(text, r"for s in [^\n]*\bexchange-record\b")

    def test_library_import_posture(self) -> None:
        """Importable without a bale process: the module-level names
        the verb and the crafter build against exist by name."""
        for name in ("validate_exchange_record", "EXCHANGE_SIDES",
                     "ANSWER_DISPOSITIONS", "EXCHANGE_RECORD_VERSION",
                     "EXCHANGE_RECORD_SCHEMA"):
            self.assertTrue(hasattr(bale_validate, name), name)


if __name__ == "__main__":
    unittest.main()
