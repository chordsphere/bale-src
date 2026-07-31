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


if __name__ == "__main__":
    unittest.main()
