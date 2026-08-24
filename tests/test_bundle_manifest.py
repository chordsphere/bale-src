"""Bundle-manifest schema and validator (v0.4.12, board 49a-i;
BALE.md §6.7).

Pins the wire side of the planner-bundle format, schema-first per
the §6.6 precedent (no producer or consumer exists yet — the crafter
emission is 49b, the open verb 49a-ii; the contract lands ahead of
both):

- schemas/bundle-manifest.schema.json parses and pins the four-key
  required envelope;
- validate_bundle_manifest (bin/bale_validate.py, the library entry
  point in the validate_telemetry_record posture) accepts a
  canonical bundle manifest, including null member slots;
- it rejects the shape and invariant defects the format cares
  about: an unknown bundle_format, a stored delivery flag (bare or
  =-glued), the pack verb stored in argv, a non-flat or duplicated
  member path, a malformed sha256, an unknown intent prompt, and a
  missing member slot;
- the intent-prompt vocabulary has two homes by design —
  INTENT_PROMPTS (bin/bale_pack.py, the consumption site) and the
  schema's enum (the wire) — and this suite pins their parity so
  the two cannot drift (the CLOSURE_REASONS-parity precedent).

Hermetic and stdlib-only: the schema is read from this repo; no
bale process runs.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "bin"))

import bale_pack  # noqa: E402
import bale_validate  # noqa: E402

SCHEMA_PATH = REPO_ROOT / "schemas" / "bundle-manifest.schema.json"


def canonical() -> dict:
    """A fresh, fully valid bundle manifest — mutate per test."""
    return {
        "bundle_format": 1,
        "pack_argv": [
            "define the widget seam",
            "--slug", "widget-seam",
            "--include", "src",
            "--supersedes", "2026-08-18-parent-001",
            "--no-readme",
        ],
        "members": {
            "brief": {"path": "brief.md", "sha256": "a" * 64},
            "checkpoint": {"path": "checkpoint.sh", "sha256": "b" * 64},
        },
        "pre_answered": [
            {"prompt": "supersede", "subject": "2026-08-18-parent-001"},
        ],
    }


class SchemaFileTest(unittest.TestCase):
    """The shipped schema file itself."""

    def test_schema_parses_and_pins_the_envelope(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual(
            sorted(schema["required"]),
            ["bundle_format", "members", "pack_argv", "pre_answered"])
        self.assertEqual(schema["properties"]["bundle_format"]["enum"], [1])
        self.assertEqual(
            sorted(schema["properties"]["members"]["required"]),
            ["brief", "checkpoint"])

    def test_intent_vocabulary_parity(self) -> None:
        """The wire enum and the code constant are one vocabulary."""
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        wire = schema["properties"]["pre_answered"]["items"][
            "properties"]["prompt"]["enum"]
        self.assertEqual(tuple(wire), bale_pack.INTENT_PROMPTS)


class ValidateBundleManifestTest(unittest.TestCase):
    """validate_bundle_manifest: accepts canon, rejects each defect."""

    def assert_valid(self, record: dict) -> None:
        errors = bale_validate.validate_bundle_manifest(record)
        self.assertEqual(errors, [], msg=errors)

    def assert_invalid(self, record, needle: str) -> None:
        errors = bale_validate.validate_bundle_manifest(record)
        self.assertTrue(errors, msg=f"expected errors mentioning {needle!r}")
        self.assertTrue(any(needle in e for e in errors),
                        msg=f"{needle!r} not in {errors}")

    def test_canonical_manifest_validates(self) -> None:
        self.assert_valid(canonical())

    def test_null_member_slots_validate(self) -> None:
        record = canonical()
        record["members"] = {"brief": None, "checkpoint": None}
        self.assert_valid(record)

    def test_empty_intents_validate(self) -> None:
        record = canonical()
        record["pre_answered"] = []
        self.assert_valid(record)

    def test_additive_keys_validate(self) -> None:
        record = canonical()
        record["emitted_by"] = "future-crafter/0.1"
        record["members"]["brief"]["size_bytes"] = 1234
        self.assert_valid(record)

    def test_non_object_reports_not_raises(self) -> None:
        errors = bale_validate.validate_bundle_manifest(
            ["not", "an", "object"])
        self.assertTrue(errors)

    def test_unknown_format_version_rejects(self) -> None:
        record = canonical()
        record["bundle_format"] = 2
        self.assert_invalid(record, "bundle_format")

    def test_missing_envelope_key_rejects(self) -> None:
        record = canonical()
        del record["pre_answered"]
        self.assert_invalid(record, "pre_answered")

    def test_missing_member_slot_rejects(self) -> None:
        record = canonical()
        record["members"] = {"brief": None}
        self.assert_invalid(record, "checkpoint")

    def test_stored_delivery_flags_reject(self) -> None:
        for arg in ("--readme-file", "--readme-file=x",
                    "--checkpoint-file", "--checkpoint-file=x"):
            with self.subTest(arg=arg):
                record = canonical()
                record["pack_argv"] = ["goal", arg]
                self.assert_invalid(record, "injected by the consumer")

    def test_stored_pack_verb_rejects(self) -> None:
        record = canonical()
        record["pack_argv"] = ["pack", "goal", "--slug", "x"]
        self.assert_invalid(record, "AFTER")

    def test_nonflat_member_path_rejects(self) -> None:
        record = canonical()
        record["members"]["brief"]["path"] = "sub/brief.md"
        self.assert_invalid(record, "flat archive-member name")

    def test_duplicate_member_paths_reject(self) -> None:
        record = canonical()
        record["members"]["checkpoint"]["path"] = "brief.md"
        self.assert_invalid(record, "distinct")

    def test_malformed_sha256_rejects(self) -> None:
        for sha in ("A" * 64, "a" * 63, "a" * 65, "g" * 64):
            with self.subTest(sha=sha):
                record = canonical()
                record["members"]["checkpoint"]["sha256"] = sha
                self.assert_invalid(record, "64 lowercase hex")

    def test_unknown_intent_prompt_rejects(self) -> None:
        record = canonical()
        record["pre_answered"] = [{"prompt": "yes-to-all", "subject": "s"}]
        self.assert_invalid(record, "prompt")


if __name__ == "__main__":
    unittest.main()
