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

Hermetic and stdlib-only: the lint module is loaded by file path (it
imports nothing beyond the stdlib and executes nothing at import
time), and the schema files are read from this repo.

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
SCHEMAS = REPO / "schemas"


def load_lint_module():
    """Load tools/response_lint.py by path, unregistered — the test
    needs its two embed constants, not an importable package."""
    spec = importlib.util.spec_from_file_location("response_lint_under_test",
                                                  LINT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


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


if __name__ == "__main__":
    unittest.main()
