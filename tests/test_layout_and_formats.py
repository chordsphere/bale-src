#!/usr/bin/env python3
"""The 100 arc's W2 code surfaces (v0.4.42), pinned in-process.

Five things landed together and this suite holds each by name:

- **The enum alias.** request-manifest.schema.json's ``expects_probe``
  admits ``agent-decides`` beside ``claude-decides``; both validate,
  and nothing else does. (The default and the emitted value stay
  ``claude-decides`` until the flip — the pack-side suites pin that.)
- **The contract_docs key sets.** Both manifest schemas take the
  block as a oneOf over two closed key sets — the four keys headed by
  ``CLAUDE.md`` and the same four headed by ``AGENT.md``, PLANNER.md
  admitted on both. Either alone validates; both together, neither,
  or a stray key refuses. Pinned through bin/bale_validate.py and the
  lint's own validator, since the lint runs where bale is not
  installed.
- **The model_identity format.** ``<vendor>:<model>`` — the two
  canonical forms validate, the three free-text spellings the corpus
  carried before v0.4.42 (claude/telemetry/, history, never rewritten)
  are refused, and so are the near-misses (trailing space, capital,
  empty model token).
- **The subset validators' new keywords.** ``pattern`` (unanchored, as
  in JSON Schema) and ``oneOf`` (exactly one) in bin/bale_validate.py
  and tools/response_lint.py alike, so the two stay in step.
- **``[layout] agent_dir``.** The accessor (default, configured, every
  refusal), the project-only merge, the renderer, the wizard walk at
  both layers, and the three consumers: bale_report.telemetry_dir,
  telemetry_record_path, and bale_rollback's dirty-tree prefix.

Hermetic and stdlib-only: bin/ modules are loaded by path with the
harness loader (bale_config's lazy ``from __main__ import fail`` gets
the raising stand-in, the test_probe_clipboard_config precedent), the
lint by file path, and the schemas from this repo.

Run:  python3 -m unittest tests.test_layout_and_formats -v
  or: python3 -m unittest discover -s tests -p 'test_layout_and_formats.py'
"""

from __future__ import annotations

import builtins
import contextlib
import importlib.util
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

from harness import REPO_ROOT, _load_module

bale_config = _load_module("bale_config")
bale_wizard = _load_module("bale_wizard")
bale_validate = _load_module("bale_validate")
bale_report = _load_module("bale_report")
bale_rollback = _load_module("bale_rollback")

SCHEMAS = REPO_ROOT / "schemas"
LINT = REPO_ROOT / "tools" / "response_lint.py"
TELEMETRY_HISTORY = REPO_ROOT / "claude" / "telemetry"


def load_schema(name: str) -> dict:
    return json.loads((SCHEMAS / name).read_text(encoding="utf-8"))


def load_lint():
    spec = importlib.util.spec_from_file_location("response_lint_w2", LINT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class _FailRaises:
    """bin/bale's fail() stand-in for direct-import unit runs: raises so
    a fatal shape is observable instead of exiting the runner."""

    class Fatal(Exception):
        pass

    def __enter__(self):
        self._main = sys.modules["__main__"]
        self._had = hasattr(self._main, "fail")
        self._saved = getattr(self._main, "fail", None)

        def _fail(msg):
            raise _FailRaises.Fatal(msg)
        self._main.fail = _fail
        return self

    def __exit__(self, *exc):
        if self._had:
            self._main.fail = self._saved
        else:
            delattr(self._main, "fail")
        return False


FOUR_CLAUDE = {"CLAUDE.md": "a", "TARBALL.md": "b", "DOCS.md": "c",
               "CODE.md": "d"}
FOUR_AGENT = {"AGENT.md": "a", "TARBALL.md": "b", "DOCS.md": "c",
              "CODE.md": "d"}

# The three spellings the corpus carried before the format was pinned.
# Read from the shipped history where it is present, so the pin tracks
# the real specimens; the literals are the fallback when a checkout
# does not carry those records (a release install, say).
LEGACY_SPELLINGS = (
    "Claude Fable 5.1 (self-reported)",
    "Claude Fable 5.1, self-reported",
    "Claude (Anthropic); exact model string not visible to the session",
)


def corpus_model_identities() -> list[str]:
    found: list[str] = []
    if TELEMETRY_HISTORY.is_dir():
        for record in sorted(TELEMETRY_HISTORY.glob("*.json")):
            try:
                data = json.loads(record.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            for attempt in data.get("attempts", []) if isinstance(data, dict) else []:
                prov = ((attempt.get("feedback") or {}).get("mechanical") or {}
                        ).get("provenance") if isinstance(attempt, dict) else None
                if isinstance(prov, dict) and isinstance(
                        prov.get("model_identity"), str):
                    found.append(prov["model_identity"])
    return found


# ---------------------------------------------------------------------------
# The enum alias
# ---------------------------------------------------------------------------

class ExpectsProbeAlias(unittest.TestCase):
    def setUp(self) -> None:
        self.field = load_schema("request-manifest.schema.json")[
            "properties"]["expects_probe"]

    def test_both_spellings_validate_and_nothing_else(self) -> None:
        for ok in ("yes", "no", "claude-decides", "agent-decides"):
            with self.subTest(value=ok):
                self.assertEqual(
                    bale_validate.validate_against_schema(ok, self.field), [])
        for bad in ("Claude-decides", "agent decides", "maybe", ""):
            with self.subTest(value=bad):
                self.assertTrue(
                    bale_validate.validate_against_schema(bad, self.field))

    def test_enum_order_keeps_the_old_spelling_first(self) -> None:
        """The old spelling stays; the alias is appended (additive)."""
        self.assertEqual(self.field["enum"],
                         ["yes", "no", "claude-decides", "agent-decides"])


# ---------------------------------------------------------------------------
# The contract_docs key sets, both schemas, both validators
# ---------------------------------------------------------------------------

class ContractDocsKeySets(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        request = load_schema("request-manifest.schema.json")
        response = load_schema("response-manifest.schema.json")
        cls.blocks = {
            "request": request["properties"]["provenance"]["properties"][
                "contract_docs"],
            "response echo": response["properties"]["feedback"]["properties"][
                "mechanical"]["properties"]["provenance"]["properties"][
                "contract_docs"],
        }
        lint = load_lint()
        cls.validators = {
            "bin/bale_validate.py": bale_validate.validate_against_schema,
            "tools/response_lint.py": lint.schema_validate,
        }

    def _errors(self, validator_name, block_name, instance):
        return self.validators[validator_name](instance,
                                               self.blocks[block_name])

    def test_shape_is_a_two_branch_oneof_of_closed_objects(self) -> None:
        for name, block in self.blocks.items():
            with self.subTest(block=name):
                self.assertEqual(block["type"], "object")
                self.assertEqual(len(block["oneOf"]), 2)
                heads = []
                for branch in block["oneOf"]:
                    self.assertIs(branch["additionalProperties"], False)
                    self.assertEqual(set(branch["properties"]) - {"PLANNER.md"},
                                     set(branch["required"]))
                    self.assertIn("PLANNER.md", branch["properties"])
                    self.assertNotIn("PLANNER.md", branch["required"])
                    heads.append(sorted(branch["required"])[0])
                self.assertEqual(sorted(heads), ["AGENT.md", "CLAUDE.md"])

    def test_either_key_set_validates_with_or_without_planner(self) -> None:
        for v, b in ((v, b) for v in self.validators for b in self.blocks):
            for inst in (FOUR_CLAUDE, FOUR_AGENT,
                         {**FOUR_CLAUDE, "PLANNER.md": "e"},
                         {**FOUR_AGENT, "PLANNER.md": "e"}):
                with self.subTest(validator=v, block=b, keys=sorted(inst)):
                    self.assertEqual(self._errors(v, b, inst), [])

    def test_both_neither_and_stray_keys_refuse(self) -> None:
        for v, b in ((v, b) for v in self.validators for b in self.blocks):
            for inst in ({**FOUR_CLAUDE, "AGENT.md": "z"},
                         {k: v_ for k, v_ in FOUR_CLAUDE.items()
                          if k != "CLAUDE.md"},
                         {**FOUR_CLAUDE, "EXTRA.md": "q"},
                         {**FOUR_AGENT, "CLAUDE.md": ""}):
                with self.subTest(validator=v, block=b, keys=sorted(inst)):
                    errors = self._errors(v, b, inst)
                    self.assertTrue(errors)
                    self.assertIn("oneOf", errors[0])


# ---------------------------------------------------------------------------
# The model_identity format
# ---------------------------------------------------------------------------

class ModelIdentityFormat(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        response = load_schema("response-manifest.schema.json")
        cls.field = response["properties"]["feedback"]["properties"][
            "mechanical"]["properties"]["provenance"]["properties"][
            "model_identity"]
        lint = load_lint()
        cls.validators = {
            "bin/bale_validate.py": bale_validate.validate_against_schema,
            "tools/response_lint.py": lint.schema_validate,
        }

    def test_stays_a_string_with_a_pattern_and_names_the_format(self) -> None:
        self.assertEqual(self.field["type"], "string")
        self.assertIn("pattern", self.field)
        self.assertIn("<vendor>:<model>", self.field["description"])
        self.assertIn("anthropic:unknown", self.field["description"])

    def test_canonical_forms_validate(self) -> None:
        for v in self.validators:
            for ok in ("anthropic:claude-fable-5.1", "anthropic:unknown",
                       "openai:gpt-5", "fixture:model", "x:y"):
                with self.subTest(validator=v, value=ok):
                    self.assertEqual(self.validators[v](ok, self.field), [])

    def test_the_legacy_spellings_are_refused(self) -> None:
        specimens = set(LEGACY_SPELLINGS) | set(corpus_model_identities())
        # The corpus may already carry canonical values once this
        # version has run; only the free-text ones are the refusal set.
        pattern = re.compile(self.field["pattern"])
        legacy = [s for s in specimens if not pattern.search(s)]
        self.assertTrue(set(LEGACY_SPELLINGS) <= set(legacy),
                        "the three pre-0.4.42 spellings must be refused")
        for v in self.validators:
            for bad in legacy:
                with self.subTest(validator=v, value=bad):
                    errors = self.validators[v](bad, self.field)
                    self.assertTrue(errors)
                    self.assertIn("pattern", errors[0])

    def test_near_misses_are_refused(self) -> None:
        for bad in ("anthropic:claude-fable-5.1 ", " anthropic:unknown",
                    "Anthropic:unknown", "anthropic:", ":unknown",
                    "anthropic:Claude", "anthropic:claude fable",
                    "anthropic:claude-fable-5.1-(self-reported)",
                    "anthropic::unknown", "anthropic:unknown:x"):
            with self.subTest(value=bad):
                self.assertTrue(
                    bale_validate.validate_against_schema(bad, self.field))


# ---------------------------------------------------------------------------
# The subset validators' keywords
# ---------------------------------------------------------------------------

class SubsetValidatorKeywords(unittest.TestCase):
    """pattern and oneOf behave the same in both validators."""

    @classmethod
    def setUpClass(cls) -> None:
        lint = load_lint()
        cls.validators = (bale_validate.validate_against_schema,
                          lint.schema_validate)

    def test_pattern_is_an_unanchored_search(self) -> None:
        schema = {"type": "string", "pattern": "b+"}
        for validate in self.validators:
            self.assertEqual(validate("abbc", schema), [])
            self.assertTrue(validate("ac", schema))
            self.assertEqual(validate("ac", {"type": "string",
                                             "pattern": "^ac$"}), [])

    def test_pattern_ignores_non_strings_after_type(self) -> None:
        """A type failure short-circuits; pattern never runs on a
        non-string, so the one error is the type's."""
        schema = {"type": "string", "pattern": "^x$"}
        for validate in self.validators:
            errors = validate(7, schema)
            self.assertEqual(len(errors), 1)
            self.assertNotIn("pattern", errors[0])

    def test_oneof_exactly_one(self) -> None:
        schema = {"oneOf": [{"type": "string", "minLength": 3},
                            {"type": "string", "enum": ["ok", "no"]}]}
        for validate in self.validators:
            self.assertEqual(validate("hello", schema), [])   # branch 0 only
            self.assertEqual(validate("ok", schema), [])      # branch 1 only
            zero = validate("x", schema)
            self.assertEqual(len(zero), 1)
            self.assertIn("none of the oneOf branches", zero[0])
            self.assertIn("branch 0", zero[0])
            self.assertIn("branch 1", zero[0])
            both = validate("yes", {"oneOf": [{"type": "string"},
                                              {"minLength": 1}]})
            self.assertEqual(len(both), 1)
            self.assertIn("2 oneOf branches", both[0])

    def test_oneof_reports_with_the_enclosing_path(self) -> None:
        schema = {"type": "object", "properties": {
            "k": {"oneOf": [{"type": "string"}, {"type": "integer"}]}}}
        for validate in self.validators:
            errors = validate({"k": None}, schema)
            self.assertEqual(len(errors), 1)
            self.assertIn("k", errors[0])


# ---------------------------------------------------------------------------
# [layout] agent_dir
# ---------------------------------------------------------------------------

class _LayoutBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-layout-")
        self.tmp = Path(self._tmpdir.name)
        self._saved_global = bale_config.GLOBAL_CONFIG_PATH
        self.global_toml = self.tmp / "user" / "bale.toml"
        bale_config.GLOBAL_CONFIG_PATH = self.global_toml
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        self._fail = _FailRaises()
        self._fail.__enter__()

    def tearDown(self) -> None:
        self._fail.__exit__(None, None, None)
        bale_config.GLOBAL_CONFIG_PATH = self._saved_global
        self._tmpdir.cleanup()

    def write_project(self, body: str) -> None:
        (self.repo / "bale.toml").write_text(body, encoding="utf-8")

    def write_global(self, body: str) -> None:
        self.global_toml.parent.mkdir(parents=True, exist_ok=True)
        self.global_toml.write_text(body, encoding="utf-8")

    def accessor(self) -> str:
        return bale_config.get_layout_agent_dir(
            bale_config.merged_config(self.repo))


class LayoutAccessorTest(_LayoutBase):
    def test_key_is_declared_and_the_default_is_history(self) -> None:
        self.assertEqual(bale_config.LAYOUT_VALUES, ("agent_dir",))
        self.assertEqual(bale_config.DEFAULT_AGENT_DIR, "claude")

    def test_absent_file_section_key_and_empty_read_as_the_default(self) -> None:
        self.assertEqual(self.accessor(), "claude")
        self.write_project('[hooks]\npost_pack = "x.sh"\n')
        self.assertEqual(self.accessor(), "claude")
        self.write_project("[layout]\n")
        self.assertEqual(self.accessor(), "claude")
        for body in ('agent_dir = ""', 'agent_dir = "   "'):
            with self.subTest(body=body):
                self.write_project(f"[layout]\n{body}\n")
                self.assertEqual(self.accessor(), "claude")

    def test_set_value_comes_back_stripped(self) -> None:
        self.write_project('[layout]\nagent_dir = "  agent  "\n')
        self.assertEqual(self.accessor(), "agent")
        self.write_project('[layout]\nagent_dir = "meta/agent"\n')
        self.assertEqual(self.accessor(), "meta/agent")

    def test_non_table_and_non_string_are_fatal(self) -> None:
        # merged_config drops a non-table section before the accessor
        # sees it, so the table-shape refusal is exercised on the
        # accessor directly (a caller handing it raw config).
        with self.assertRaises(_FailRaises.Fatal) as cm:
            bale_config.get_layout_agent_dir({"layout": "agent"})
        self.assertIn("[layout] must be a table", str(cm.exception))
        self.write_project("[layout]\nagent_dir = 3\n")
        with self.assertRaises(_FailRaises.Fatal) as cm:
            self.accessor()
        self.assertIn("layout.agent_dir must be a string", str(cm.exception))

    def test_escaping_and_malformed_paths_are_fatal(self) -> None:
        for value, reason in (("/abs/agent", "not absolute"),
                              ("../agent", "'..' component"),
                              ("agent/../x", "'..' component"),
                              ("agent/", "end in a slash"),
                              ("my agent", "whitespace")):
            with self.subTest(value=value):
                self.write_project(f'[layout]\nagent_dir = "{value}"\n')
                with self.assertRaises(_FailRaises.Fatal) as cm:
                    self.accessor()
                self.assertIn(reason, str(cm.exception))
                self.assertEqual(
                    bale_config.layout_agent_dir_problem(value) is not None,
                    True)

    def test_problem_helper_accepts_the_good_shapes(self) -> None:
        for value in ("claude", "agent", "meta/agent", ".agent", "a-b_c"):
            with self.subTest(value=value):
                self.assertIsNone(bale_config.layout_agent_dir_problem(value))

    def test_global_layer_is_never_inherited(self) -> None:
        self.write_global('[layout]\nagent_dir = "global-agent"\n')
        self.assertEqual(self.accessor(), "claude")
        self.assertNotIn("layout", bale_config.merged_config(self.repo))
        self.write_project('[layout]\nagent_dir = "agent"\n')
        self.assertEqual(self.accessor(), "agent")
        self.assertEqual(bale_config.merged_config(self.repo)["layout"],
                         {"agent_dir": "agent"})

    def test_repo_convenience_short_circuits_without_a_config_file(self) -> None:
        """layout_agent_dir(repo) reads the project file only and needs
        no fail() on __main__ when there is none — the shape the
        in-process report and stats suites rely on."""
        self._fail.__exit__(None, None, None)
        try:
            self.assertEqual(bale_config.layout_agent_dir(self.repo), "claude")
        finally:
            self._fail.__enter__()
        self.write_project('[layout]\nagent_dir = "agent"\n')
        self.assertEqual(bale_config.layout_agent_dir(self.repo), "agent")

    def test_renderer_emits_the_section_after_probe(self) -> None:
        rendered = bale_config.render_bale_toml(
            {"probe": {"clipboard_command": "pbcopy"},
             "layout": {"agent_dir": "agent"}}, layer="project")
        self.assertIn('[layout]\nagent_dir = "agent"\n', rendered)
        self.assertLess(rendered.index("[probe]"), rendered.index("[layout]"))
        self.assertNotIn("[layout]", bale_config.render_bale_toml(
            {"probe": {"clipboard_command": "pbcopy"}}, layer="project"))

    def test_render_then_load_round_trips(self) -> None:
        rendered = bale_config.render_bale_toml(
            {"layout": {"agent_dir": "agent"}}, layer="project")
        self.write_project(rendered)
        self.assertEqual(self.accessor(), "agent")


def _walk_with_answers(existing: dict, *, layer: str,
                       answers: dict) -> tuple[dict, str]:
    """Drive walk_configurables with input() answering by prompt label
    (the test_probe_clipboard_config driver, order-independent): the item
    an input() belongs to is the most recent line matching
    bale_wizard.ITEM_HEADER_RE, and a list answer is consumed one entry
    per input() call for that item ('?' then the real answer)."""
    buffer = io.StringIO()
    pending = {key: (list(value) if isinstance(value, list) else [value])
               for key, value in answers.items()}

    def fake_input(_prompt: str = "") -> str:
        label = None
        for line in reversed(buffer.getvalue().splitlines()):
            match = bale_wizard.ITEM_HEADER_RE.match(line)
            if match:
                label = match.group(3)
                break
        queue = pending.get(label) or []
        return queue.pop(0) if queue else ""

    saved_input = builtins.input
    builtins.input = fake_input
    try:
        with contextlib.redirect_stdout(buffer):
            new = bale_config.walk_configurables(
                existing, layer=layer, inherited=None)
    finally:
        builtins.input = saved_input
    return new, buffer.getvalue()


class LayoutWizardWalkTest(unittest.TestCase):
    def test_project_walk_sets_the_key(self) -> None:
        new, out = _walk_with_answers(
            {}, layer="project", answers={"layout.agent_dir": "agent"})
        self.assertEqual(new.get("layout"), {"agent_dir": "agent"})
        self.assertRegex(out, r"(?m)^\s*\d+/\d+  layout\.agent_dir\b",
                         msg="the item screen names its dotted key")

    def test_project_walk_enter_keeps_and_names_the_default(self) -> None:
        new, out = _walk_with_answers({}, layer="project", answers={})
        self.assertNotIn("layout", new)
        self.assertIn('(unset — "claude")', out)
        new, _ = _walk_with_answers(
            {"layout": {"agent_dir": "agent"}}, layer="project", answers={})
        self.assertEqual(new.get("layout"), {"agent_dir": "agent"})

    def test_project_walk_dash_clears_the_key(self) -> None:
        new, _ = _walk_with_answers(
            {"layout": {"agent_dir": "agent"}}, layer="project",
            answers={"layout.agent_dir": "-"})
        self.assertNotIn("layout", new)

    def test_unusable_value_is_refused_and_current_kept(self) -> None:
        new, out = _walk_with_answers(
            {"layout": {"agent_dir": "agent"}}, layer="project",
            answers={"layout.agent_dir": "/abs"})
        self.assertEqual(new.get("layout"), {"agent_dir": "agent"})
        self.assertIn("Keeping current", out)
        self.assertIn("not absolute", out)

    def test_prompt_says_it_moves_nothing_and_is_project_only(self) -> None:
        """The full description is one '?' away; the [layout] heading
        carries the project-only note in the default view."""
        _new, out = _walk_with_answers(
            {}, layer="project", answers={"layout.agent_dir": ["?", ""]})
        self.assertIn("rename", out)
        self.assertIn("Project-layer only", " ".join(out.split()))
        _new, short = _walk_with_answers({}, layer="project", answers={})
        self.assertRegex(short, r"\[layout\].*project layer only")

    def test_global_walk_never_offers_the_key(self) -> None:
        new, out = _walk_with_answers({}, layer="global", answers={})
        self.assertNotIn("layout.agent_dir", out)
        self.assertNotIn("layout", new)


class LayoutConsumersTest(_LayoutBase):
    """The three sites that used to spell the directory."""

    def test_telemetry_dir_and_record_path_follow_the_key(self) -> None:
        self.assertEqual(bale_report.telemetry_dir(self.repo),
                         self.repo / "claude" / "telemetry")
        self.assertEqual(
            bale_report.telemetry_record_path(self.repo, "2026-09-23-x-001"),
            self.repo / "claude" / "telemetry" / "2026-09-23-x-001.json")
        self.write_project('[layout]\nagent_dir = "agent"\n')
        self.assertEqual(bale_report.telemetry_dir(self.repo),
                         self.repo / "agent" / "telemetry")
        self.assertEqual(
            bale_report.telemetry_record_path(self.repo, "2026-09-23-x-001"),
            self.repo / "agent" / "telemetry" / "2026-09-23-x-001.json")

    def test_no_spelled_telemetry_segment_remains_in_code(self) -> None:
        """The path is built in one place; a re-spelled segment anywhere
        in bin/ is the regression this guards."""
        for name in ("bale", "bale_report.py", "bale_rollback.py"):
            src = (REPO_ROOT / "bin" / name).read_text(encoding="utf-8")
            self.assertNotIn('/ "claude" / "telemetry"', src, name)
            self.assertNotIn('_TELEMETRY_PREFIX = "claude/telemetry/"', src,
                             name)
        self.assertFalse(hasattr(bale_rollback, "_TELEMETRY_PREFIX"))

    def test_rollback_prefix_follows_the_key(self) -> None:
        self.assertEqual(bale_rollback._telemetry_prefix("claude"),
                         "claude/telemetry/")
        self.assertEqual(bale_rollback._telemetry_prefix("agent/"),
                         "agent/telemetry/")
        status = ("?? claude/telemetry/2026-09-23-x-001.json\n"
                  "?? agent/telemetry/2026-09-23-y-001.json\n"
                  " M src/thing.py\n")
        disregarded, remainder = bale_rollback._split_untracked_disregarded(
            status, None)
        self.assertEqual(disregarded,
                         ["claude/telemetry/2026-09-23-x-001.json"])
        self.assertEqual(remainder, ["?? agent/telemetry/2026-09-23-y-001.json",
                                     " M src/thing.py"])
        disregarded, remainder = bale_rollback._split_untracked_disregarded(
            status, None, "agent")
        self.assertEqual(disregarded,
                         ["agent/telemetry/2026-09-23-y-001.json"])
        self.assertEqual(remainder, ["?? claude/telemetry/2026-09-23-x-001.json",
                                     " M src/thing.py"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
