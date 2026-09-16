#!/usr/bin/env python3
"""The durable schema-embed drift guard (session 22d rider).

tools/response_lint.py embeds verbatim copies of the two schemas under
schemas/ so it runs standalone in a request tarball. validate.sh
asserts JSON-equality between each source schema and its embed on
every install validation run; this suite is the same guard in durable,
per-commit form, so an edit to either side that forgets the refresh
fails the test run by name — not only the next validate.sh pass.

Equality is JSON-level (parsed values), not byte-level: formatting is
free to differ, content is not. The comparison direction is
symmetric — the test names the pair, not a winner; whichever side
drifted is the fix.

A second guard rides here since board 80 (proposed by the doc-lane
session 2026-09-14-002): request/response provenance key parity.
The request manifest's ``provenance`` block is echoed verbatim into
the response manifest's ``feedback.mechanical.provenance`` (TARBALL.md
§5.2.2), so every key the request side can carry must be admissible
on the echo side — otherwise the next request-side stamp lands
without its echo and the verbatim copy starts dropping fields. The
echo may carry *more* (``model_identity`` is echo-only); the request
side may never carry a key the echo lacks.

A third guard rides here since board 91: the crafter's question-row
key set and vocabularies against the response schema's
``questions.items`` — the same one-home rule, applied to the second
tool that re-declares the row. tools/craft_response.py cannot read
the schema (a worker session has no install), so QUESTION_STUB_KEYS
+ QUESTION_OPTIONAL_KEYS re-declare the row's permitted key set and
QUESTION_PRIORITIES / QUESTION_ORIGINS its two closed vocabularies;
this guard is what keeps the next additive row key (the ``origin``
precedent: admitted by bale in v0.4.24, refused by the crafter until
board 91) from landing on one side only.

A fourth guard rides here since session
2026-09-16-board-96-crafter-85-light-block-002: the two self-reported
counts (``light_blocks``, row 96; ``paste_carried_rounds``, row 85)
keep their contracted shape in the schema — optional (never in
``required``, so pre-wave manifests validate), integer, minimum 0 —
inside a ``self_reported`` that stays a closed object. The embed
equality above carries the shape into the lint's copy; this names the
shape itself, so a later edit that made a count required or signed
fails by name rather than only as an unexplained embed diff.

Hermetic and stdlib-only: the lint and crafter modules are loaded by
file path (both import nothing beyond the stdlib and execute nothing
at import time), and the schema files are read from this repo.

Run:  python3 -m unittest tests.test_schema_embeds -v
  or: python3 -m unittest discover -s tests -p 'test_schema_embeds.py'
"""

from __future__ import annotations

import importlib.util
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
LINT = REPO / "tools" / "response_lint.py"
CRAFT = REPO / "tools" / "craft_response.py"
SCHEMAS = REPO / "schemas"


def load_module_by_path(name: str, path: Path):
    """Load a tools/ module by path, unregistered — the tests need a
    few constants, not an importable package."""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_lint_module():
    return load_module_by_path("response_lint_under_test", LINT)


class SchemaEmbedEquality(unittest.TestCase):
    """Each embedded schema JSON-equals its schemas/ source file."""

    @classmethod
    def setUpClass(cls):
        cls.lint = load_lint_module()

    def assert_embed_equals_source(self, embed_text: str, filename: str):
        embed = json.loads(embed_text)
        source = json.loads(
            (SCHEMAS / filename).read_text(encoding="utf-8"))
        self.assertEqual(
            embed, source,
            f"tools/response_lint.py's embedded copy of {filename} is not "
            "JSON-equal to the schemas/ source — a schema edit and its "
            "embed refresh land together (fix whichever side drifted)")

    def test_diagnostics_embed_equals_source(self):
        self.assert_embed_equals_source(
            self.lint.DIAGNOSTICS_SCHEMA_JSON,
            "diagnostics.schema.json")

    def test_response_manifest_embed_equals_source(self):
        self.assert_embed_equals_source(
            self.lint.RESPONSE_MANIFEST_SCHEMA_JSON,
            "response-manifest.schema.json")


def load_schema(filename: str) -> dict:
    return json.loads((SCHEMAS / filename).read_text(encoding="utf-8"))


class ProvenanceKeyParity(unittest.TestCase):
    """The request manifest's provenance keys are a subset of the
    response echo's (board 80, item 1)."""

    @classmethod
    def setUpClass(cls):
        request = load_schema("request-manifest.schema.json")
        response = load_schema("response-manifest.schema.json")
        cls.request_provenance = request["properties"]["provenance"]
        cls.echo_provenance = (
            response["properties"]["feedback"]["properties"]["mechanical"]
            ["properties"]["provenance"])

    def test_both_provenance_blocks_are_closed_objects(self):
        """Parity is only meaningful between two closed key sets: if
        either side opened up (``additionalProperties`` no longer
        false) the subset check below would pass vacuously while the
        real contract went unpinned, so the closedness is asserted
        first, by name."""
        for side, block in (("request provenance", self.request_provenance),
                            ("response echo", self.echo_provenance)):
            with self.subTest(side=side):
                self.assertIs(
                    block.get("additionalProperties"), False,
                    f"the {side} block is no longer a closed object "
                    "(additionalProperties: false) — key parity can't be "
                    "pinned against an open key set")

    def test_request_provenance_keys_subset_of_echo(self):
        request_keys = set(self.request_provenance["properties"])
        echo_keys = set(self.echo_provenance["properties"])
        self.assertTrue(
            request_keys <= echo_keys,
            "request-manifest.schema.json's provenance carries keys the "
            "response echo (feedback.mechanical.provenance in "
            "response-manifest.schema.json) cannot admit: "
            f"{sorted(request_keys - echo_keys)} — a request-side "
            "provenance stamp lands with its echo in the same session "
            "(TARBALL.md 5.2.2: the echo is verbatim)")


class QuestionRowKeyParity(unittest.TestCase):
    """The crafter's question-row key set and vocabularies equal the
    response schema's ``questions.items`` (board 91).

    The row has one home — response-manifest.schema.json's
    questions.items, which bale's validate_clarification_questions
    derives from and exchange-record.schema.json reaches by $ref. The
    crafter re-declares the row (QUESTION_STUB_KEYS is the required
    half, QUESTION_OPTIONAL_KEYS the additive half, the two vocabulary
    tuples the closed enums) because a worker session has no schema to
    read; this class is what holds the re-declaration to the home.
    """

    @classmethod
    def setUpClass(cls):
        cls.craft = load_module_by_path("craft_response_under_test", CRAFT)
        response = load_schema("response-manifest.schema.json")
        cls.row = response["properties"]["questions"]["items"]

    def test_row_is_a_closed_object(self):
        """Parity between key sets is only meaningful when the schema's
        side is closed; asserted first, by name, like the provenance
        guard above."""
        self.assertIs(self.row.get("additionalProperties"), False,
                      "questions.items is no longer a closed object — "
                      "the crafter's unknown-key refusal would have "
                      "nothing to be in parity with")

    def test_stub_keys_are_the_schema_required_set(self):
        self.assertEqual(
            set(self.craft.QUESTION_STUB_KEYS), set(self.row["required"]),
            "tools/craft_response.py's QUESTION_STUB_KEYS is not the "
            "schema's required question-row set — fix whichever side "
            "drifted (the seeded stub and the required half share a "
            "home)")

    def test_permitted_keys_are_the_schema_property_set(self):
        permitted = (set(self.craft.QUESTION_STUB_KEYS)
                     | set(self.craft.QUESTION_OPTIONAL_KEYS))
        self.assertEqual(
            permitted, set(self.row["properties"]),
            "tools/craft_response.py's permitted question-row keys "
            "(QUESTION_STUB_KEYS + QUESTION_OPTIONAL_KEYS) are not the "
            "schema's questions.items properties: "
            f"crafter-only {sorted(permitted - set(self.row['properties']))}, "
            f"schema-only {sorted(set(self.row['properties']) - permitted)} "
            "— an additive row key lands on both sides in one session "
            "(the board-91 origin precedent)")
        self.assertFalse(
            set(self.craft.QUESTION_STUB_KEYS)
            & set(self.craft.QUESTION_OPTIONAL_KEYS),
            "a key is required or optional, never both")

    def test_vocabularies_are_the_schema_enums(self):
        for constant, key in (("QUESTION_PRIORITIES", "priority"),
                              ("QUESTION_ORIGINS", "origin")):
            with self.subTest(key=key):
                self.assertEqual(
                    tuple(getattr(self.craft, constant)),
                    tuple(self.row["properties"][key]["enum"]),
                    f"tools/craft_response.py's {constant} is not the "
                    f"schema's questions.items.{key} enum — the "
                    "vocabulary is closed and has one home")


class SelfReportedCountShape(unittest.TestCase):
    """light_blocks and paste_carried_rounds: optional integers >= 0 in a
    closed self_reported, in the source schema and the lint's embed."""

    COUNTS = ("light_blocks", "paste_carried_rounds")

    @staticmethod
    def self_reported_of(schema: dict) -> dict:
        return (schema["properties"]["feedback"]["properties"]
                ["self_reported"])

    def test_counts_are_optional_nonnegative_integers(self):
        lint = load_lint_module()
        for label, schema in (
                ("schemas/response-manifest.schema.json",
                 load_schema("response-manifest.schema.json")),
                ("tools/response_lint.py embed",
                 json.loads(lint.RESPONSE_MANIFEST_SCHEMA_JSON))):
            block = self.self_reported_of(schema)
            with self.subTest(side=label):
                self.assertIs(block.get("additionalProperties"), False,
                              "self_reported stays a closed object")
                for key in self.COUNTS:
                    self.assertIn(key, block["properties"])
                    self.assertNotIn(key, block["required"],
                                     f"{key} is optional — pre-wave "
                                     "manifests must keep validating")
                    prop = block["properties"][key]
                    self.assertEqual(prop.get("type"), "integer")
                    self.assertEqual(prop.get("minimum"), 0)
                    self.assertTrue(prop.get("description"))


if __name__ == "__main__":
    unittest.main()
