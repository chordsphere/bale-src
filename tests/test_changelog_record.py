#!/usr/bin/env python3
"""The changelog record family (v0.4.35): validator, schema, and corpus.

Three subjects, one family:

- **validate_changelog_record** (bin/bale_validate.py) — the per-record
  library entry point over schemas/changelog-record.schema.json. The
  family exists so a version's machine-readable surface changes are
  named at the time they land (CODE.md section 8.5), and the validator
  exists so omission is loud: every required key, removed one at a
  time, must produce an error naming it. The Python-side rules the
  schema subset cannot express (X.Y.Z version, UTC `at`, repo-relative
  surface paths) are pinned case by case.
- **The schema's one-home parity** — the validator's
  CHANGELOG_RECORD_VERSION mirrors the schema's record_version enum,
  and the schema stays loose (additionalProperties true at the envelope
  and in each surface row), the escalation/exchange convention.
- **The corpus** — every record under claude/changelog/ validates and
  is named <version>.json for the version it carries. The file-name
  rule is a corpus property the record-alone validator cannot see, so
  it lives here. The corpus must not be empty: 0.4.35 wrote the first
  record, and a vanished directory is a failure, not a pass on nothing.

Hermetic and stdlib-only: bale_validate is loaded in-process by path
through the shared harness (no bale process, no __main__), and the
schema and records are read from this repo; nothing is written.

Run:  python3 tests/test_changelog_record.py
  or: python3 -m unittest discover -s tests -p 'test_changelog_record.py'
"""

from __future__ import annotations

import copy
import json
import unittest
from pathlib import Path

from harness import _load_module

REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "changelog-record.schema.json"
CHANGELOG_DIR = REPO_ROOT / "claude" / "changelog"

REQUIRED_KEYS = ("record_version", "version", "session_id", "at",
                 "surfaces")


def minimal_record() -> dict:
    """A smallest-valid changelog record: the required core, one row."""
    return {
        "record_version": 1,
        "version": "0.4.35",
        "session_id": "2026-09-17-fx-changelog-001",
        "at": "2026-09-17T00:00:00+00:00",
        "surfaces": [
            {"path": "schemas/telemetry-record.schema.json",
             "change": "closure_reason enum gains 'aborted' (additive)"},
        ],
    }


class ValidateChangelogRecordTest(unittest.TestCase):
    """The validator's verdicts, one rule per case."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.validate = _load_module("bale_validate")

    def errors(self, record) -> list:
        return self.validate.validate_changelog_record(record)

    def assertRejects(self, record, needle: str) -> None:
        """At least one error, and some error mentions `needle` — so a
        failure names the rule that fired rather than any rule."""
        errors = self.errors(record)
        self.assertTrue(errors, f"expected a rejection mentioning {needle!r}")
        self.assertTrue(any(needle in e for e in errors),
                        f"no error mentions {needle!r}: {errors}")

    def test_minimal_record_is_valid(self) -> None:
        self.assertEqual(self.errors(minimal_record()), [])

    def test_each_missing_required_key_is_loud(self) -> None:
        """Omission is loud: every required key, dropped alone, is an
        error naming that key — surfaces above all."""
        for key in REQUIRED_KEYS:
            with self.subTest(key=key):
                record = minimal_record()
                del record[key]
                self.assertRejects(record, f"missing required key {key!r}")

    def test_empty_surfaces_rejects(self) -> None:
        """A record naming no surface is not a record: a version that
        changed no machine-readable surface writes none."""
        record = minimal_record()
        record["surfaces"] = []
        self.assertRejects(record, "surfaces")

    def test_surface_row_needs_path_and_change(self) -> None:
        for key in ("path", "change"):
            with self.subTest(key=key):
                record = minimal_record()
                del record["surfaces"][0][key]
                self.assertRejects(record, f"missing required key {key!r}")
                record = minimal_record()
                record["surfaces"][0][key] = ""
                self.assertRejects(record, f"surfaces[0].{key}")

    def test_record_version_is_exactly_one(self) -> None:
        for bad in (2, 0, True, "1"):
            with self.subTest(record_version=bad):
                record = minimal_record()
                record["record_version"] = bad
                self.assertRejects(record, "record_version")

    def test_version_form(self) -> None:
        for good in ("0.4.35", "1.0.0", "10.20.300"):
            with self.subTest(version=good):
                record = minimal_record()
                record["version"] = good
                self.assertEqual(self.errors(record), [])
        for bad in ("v0.4.35", "0.4", "0.4.35.1", "0.4.x", "0.4.35-rc1",
                    "", "0..35"):
            with self.subTest(version=bad):
                record = minimal_record()
                record["version"] = bad
                self.assertRejects(record, "version")

    def test_at_is_iso_utc(self) -> None:
        for good in ("2026-09-17T02:13:00+00:00", "2026-09-17T02:13:00Z"):
            with self.subTest(at=good):
                record = minimal_record()
                record["at"] = good
                self.assertEqual(self.errors(record), [])
        for bad, needle in (("2026-09-17T02:13:00", "no UTC offset"),
                            ("2026-09-17T04:13:00+02:00", "not in UTC"),
                            ("yesterday", "not an ISO 8601")):
            with self.subTest(at=bad):
                record = minimal_record()
                record["at"] = bad
                self.assertRejects(record, needle)
                # The messages name the changelog's own key, never the
                # exchange record's created_at the check was lifted from.
                self.assertFalse(
                    any("created_at" in e for e in self.errors(record)))

    def test_updated_at_checked_when_present(self) -> None:
        record = minimal_record()
        record["updated_at"] = "2026-09-18T00:00:00+00:00"
        self.assertEqual(self.errors(record), [])
        record["updated_at"] = "2026-09-18T00:00:00"
        self.assertRejects(record, "updated_at")

    def test_surface_paths_are_repo_relative(self) -> None:
        for bad in ("/etc/passwd", "../outside.json",
                    "schemas/../bin/bale", "\\\\share\\x"):
            with self.subTest(path=bad):
                record = minimal_record()
                record["surfaces"][0]["path"] = bad
                self.assertRejects(record, "surfaces[0].path")
        record = minimal_record()
        record["surfaces"][0]["path"] = "bin/bale_report.py"
        self.assertEqual(self.errors(record), [])

    def test_loose_envelope_and_rows_admit_additive_fields(self) -> None:
        """Future additive fields keep earlier-shaped records valid —
        at the envelope, in a row, and the documented optional keys."""
        record = minimal_record()
        record["notes"] = "free text"
        record["future_field"] = {"anything": [1, 2]}
        record["surfaces"][0]["session_id"] = "2026-09-18-fx-append-001"
        record["surfaces"][0]["future_row_field"] = True
        self.assertEqual(self.errors(record), [])

    def test_non_object_is_an_error_not_a_raise(self) -> None:
        for bad in (None, [], "record", 1):
            with self.subTest(record=bad):
                errors = self.errors(bad)
                self.assertEqual(len(errors), 1)
                self.assertIn("not a JSON object", errors[0])

    def test_input_is_not_mutated(self) -> None:
        record = minimal_record()
        before = copy.deepcopy(record)
        self.errors(record)
        self.assertEqual(record, before)

    def test_exchange_created_at_messages_unchanged(self) -> None:
        """The shared timestamp check kept its default wording, so the
        exchange record's messages still name created_at."""
        problem = self.validate._created_at_problem("2026-09-17T02:13:00")
        self.assertIn("created_at", problem)


class ChangelogSchemaTest(unittest.TestCase):
    """The schema file's one-home parity and loose posture."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.validate = _load_module("bale_validate")
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def test_schema_constant_names_the_file(self) -> None:
        self.assertEqual(self.validate.CHANGELOG_RECORD_SCHEMA,
                         SCHEMA_PATH.name)

    def test_required_core(self) -> None:
        self.assertEqual(sorted(self.schema["required"]),
                         sorted(REQUIRED_KEYS))

    def test_record_version_parity(self) -> None:
        self.assertEqual(self.schema["properties"]["record_version"]["enum"],
                         [self.validate.CHANGELOG_RECORD_VERSION])

    def test_loose_at_envelope_and_rows(self) -> None:
        self.assertIs(self.schema["additionalProperties"], True)
        rows = self.schema["properties"]["surfaces"]["items"]
        self.assertIs(rows["additionalProperties"], True)
        self.assertEqual(sorted(rows["required"]), ["change", "path"])


class ChangelogCorpusTest(unittest.TestCase):
    """Every landed record validates and is named for its version."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.validate = _load_module("bale_validate")

    def records(self) -> list:
        return sorted(CHANGELOG_DIR.glob("*.json"))

    def test_corpus_is_not_empty(self) -> None:
        self.assertTrue(CHANGELOG_DIR.is_dir(),
                        "claude/changelog/ is missing — 0.4.35 wrote the "
                        "family's first record")
        self.assertIn("0.4.35.json", [p.name for p in self.records()],
                      "the family's first record is gone")

    def test_every_record_validates_and_matches_its_name(self) -> None:
        for path in self.records():
            with self.subTest(record=path.name):
                record = json.loads(path.read_text(encoding="utf-8"))
                self.assertEqual(self.validate.validate_changelog_record(
                    record), [])
                self.assertEqual(path.name, f"{record['version']}.json")


if __name__ == "__main__":
    unittest.main(verbosity=2)
