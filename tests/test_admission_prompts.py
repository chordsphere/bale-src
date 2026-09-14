"""Unit tier for the v0.4.27 (board 78) admission prompts: the composed
remedy line, the scope-admission vocabulary's three homes, the
overridden_path_sources telemetry stamp, the two refusal renderers, and
the one prompt-eligibility gate both prompts share.

The end-to-end tier (a real apply under a pty, the non-TTY faces, the
namespace-less sandbox refusal) lives in
tests/test_admission_prompts_e2e.py; the hook default and acceptance
store are tests/test_hook_acceptance.py. This file needs no scratch
install: bin/ is importable directly (the checkpoint-import posture
test_telemetry_extensions.py pins), through the ``_load_module`` /
``_minimal_record`` helpers both suites share from tests/harness.py
(moved there at board 80).
"""

from __future__ import annotations

import json
import shlex
import unittest

from harness import REPO_ROOT, _load_module, _minimal_record

SCHEMA_PATH = REPO_ROOT / "schemas" / "telemetry-record.schema.json"


class ComposedCommandTest(unittest.TestCase):
    """compose_admission_command: one physical line, real filename
    quoted, every admission flag carried verbatim, zero placeholders."""

    @classmethod
    def setUpClass(cls):
        cls.br = _load_module("bale_report")

    def test_minimal_drift_line(self) -> None:
        line = self.br.compose_admission_command(
            verb="apply", tarball_name="response-003.tar.gz",
            allow_out_of_scope=["lib/b.txt"])
        self.assertEqual(
            line,
            "bale apply 'response-003.tar.gz' --allow-out-of-scope 'lib/b.txt'")
        self.assertNotIn("\n", line, msg="one physical line")
        self.assertNotIn("<", line, msg="zero placeholders")

    def test_every_admission_flag_is_carried_and_nothing_else(self) -> None:
        line = self.br.compose_admission_command(
            verb="retry", tarball_name="r.tar.gz",
            allow_out_of_scope=["a", "b"],
            accept_base_drift=["c"],
            allow_missing_required_check=["lint"],
            accept_checkpoint_change=True,
            no_sandbox=True)
        argv = shlex.split(line)
        self.assertEqual(argv[:3], ["bale", "retry", "r.tar.gz"])
        self.assertEqual(argv.count("--allow-out-of-scope"), 2)
        self.assertIn("--accept-base-drift", argv)
        self.assertIn("--allow-missing-required-check", argv)
        self.assertIn("--accept-checkpoint-change", argv)
        self.assertIn("--no-sandbox", argv)
        for absent in ("--verbose", "--json", "--no-interact", "--sid"):
            self.assertNotIn(absent, argv)

    def test_repeatable_flags_deduplicate_in_order(self) -> None:
        line = self.br.compose_admission_command(
            verb="apply", tarball_name="r.tar.gz",
            allow_out_of_scope=["b", "a", "b"])
        argv = shlex.split(line)
        self.assertEqual(
            [argv[i + 1] for i, tok in enumerate(argv)
             if tok == "--allow-out-of-scope"], ["b", "a"])

    def test_quoting_survives_spaces_and_quotes(self) -> None:
        line = self.br.compose_admission_command(
            verb="apply", tarball_name="my resp'onse.tar.gz",
            allow_out_of_scope=["dir with space/f.py"])
        self.assertEqual(
            shlex.split(line),
            ["bale", "apply", "my resp'onse.tar.gz",
             "--allow-out-of-scope", "dir with space/f.py"])

    def test_verb_is_closed(self) -> None:
        with self.assertRaises(ValueError):
            self.br.compose_admission_command(
                verb="revert", tarball_name="r.tar.gz")


class ScopeAdmissionVocabularyTest(unittest.TestCase):
    """overridden_path_sources rides the sandbox_off_source rails: the
    schema's per-value enum is the one home, SCOPE_ADMISSION_SOURCES
    mirrors it, the record-wide walk enforces it at any depth, and
    records without the key keep validating."""

    @classmethod
    def setUpClass(cls):
        cls.bv = _load_module("bale_validate")
        cls.br = _load_module("bale_report")
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def _spot(self) -> dict:
        return (self.schema["properties"]["attempts"]["items"]
                ["properties"]["overridden_path_sources"])

    def test_schema_enum_is_exactly_flag_and_prompt(self) -> None:
        self.assertEqual(self._spot()["type"], "object")
        self.assertEqual(sorted(self._spot()["additionalProperties"]["enum"]),
                         ["flag", "prompt"])

    def test_tuple_and_schema_enum_agree(self) -> None:
        self.assertEqual(list(self._spot()["additionalProperties"]["enum"]),
                         list(self.br.SCOPE_ADMISSION_SOURCES))

    def test_additive_not_required(self) -> None:
        items = self.schema["properties"]["attempts"]["items"]
        self.assertNotIn("overridden_path_sources", items.get("required", []))
        self.assertEqual(self.bv.validate_telemetry_record(_minimal_record()),
                         [], msg="a pre-epoch record keeps validating")

    def test_known_values_validate_at_the_named_spot(self) -> None:
        rec = _minimal_record(overridden_paths=["a", "b"],
                              overridden_path_sources={"a": "flag",
                                                       "b": "prompt"})
        self.assertEqual(self.bv.validate_telemetry_record(rec), [])
        self.assertEqual(self.bv.validate_telemetry_record(
            _minimal_record(overridden_path_sources={})), [])

    def test_unknown_value_rejects_at_the_named_spot(self) -> None:
        rec = _minimal_record(overridden_path_sources={"a": "config"})
        errors = self.bv.validate_telemetry_record(rec)
        self.assertTrue(errors)
        self.assertTrue(any("overridden_path_sources" in e for e in errors))

    def test_unknown_value_rejects_at_any_depth(self) -> None:
        rec = _minimal_record()
        rec["attempts"][0]["feedback"] = {
            "nested": {"overridden_path_sources": {"x": "wish"}}}
        errors = self.bv.validate_telemetry_record(rec)
        self.assertTrue(any("nested.overridden_path_sources" in e
                            for e in errors), msg=errors)

    def test_null_and_non_object_reject(self) -> None:
        for bad in (None, ["flag"], "flag"):
            errors = self.bv.validate_telemetry_record(
                _minimal_record(overridden_path_sources=bad))
            self.assertTrue(errors, msg=f"{bad!r} should reject")

    def test_sandbox_off_source_prompt_is_in_the_vocabulary(self) -> None:
        rec = _minimal_record(sandbox_confined=False,
                              sandbox_off_source="prompt")
        self.assertEqual(self.bv.validate_telemetry_record(rec), [])
        self.assertIn("prompt", self.br.SANDBOX_OFF_SOURCES)


class TelemetryStampTest(unittest.TestCase):
    """build_telemetry_attempt stamps the map unconditionally, keyed by
    overridden_paths, gap-filling with "flag"."""

    @classmethod
    def setUpClass(cls):
        cls.br = _load_module("bale_report")

    def test_empty_when_nothing_admitted(self) -> None:
        a = self.br.build_telemetry_attempt(outcome="applied", command="apply")
        self.assertEqual(a["overridden_path_sources"], {})

    def test_keys_follow_overridden_paths_and_gaps_read_flag(self) -> None:
        a = self.br.build_telemetry_attempt(
            outcome="applied", command="apply",
            overridden_paths=["a", "b", "c"],
            overridden_path_sources={"b": "prompt", "zzz": "prompt"})
        self.assertEqual(a["overridden_path_sources"],
                         {"a": "flag", "b": "prompt", "c": "flag"})

    def test_prompt_sandbox_source_keeps_escaped_false(self) -> None:
        a = self.br.build_telemetry_attempt(
            outcome="applied", command="apply",
            sandbox_confined=False, sandbox_off_source="prompt")
        self.assertIs(a["sandbox_escaped"], False)
        self.assertEqual(a["sandbox_off_source"], "prompt")


class RefusalRendererTest(unittest.TestCase):
    """The two renderers print the composed line verbatim and never a
    placeholder when a remedy is supplied."""

    @classmethod
    def setUpClass(cls):
        cls.br = _load_module("bale_report")

    def test_drift_refusal_carries_the_composed_line(self) -> None:
        remedy = "bale apply 'r.tar.gz' --allow-out-of-scope 'lib/b.txt'"
        out = self.br.format_scope_drift_refusal(
            sid="s", scope=["src"], refused=["lib/b.txt"], overridden=[],
            telemetry="claude/telemetry/s.json", remedy=remedy,
            declined_at_prompt=True)
        self.assertIn(remedy, out)
        self.assertNotIn("<tarball>", out)
        self.assertNotIn("<path>", out)
        self.assertIn("admission prompt", out)
        self.assertIn("declined", out)
        self.assertTrue(any(line.strip() == remedy
                            for line in out.splitlines()),
                        msg="the composed line is its own physical line")

    def test_drift_refusal_read_only_shape_carries_it_too(self) -> None:
        remedy = "bale retry 'r.tar.gz' --allow-out-of-scope 'x'"
        out = self.br.format_scope_drift_refusal(
            sid="s", scope=[], refused=["x"], overridden=[],
            telemetry=None, dry_run=True, remedy=remedy)
        self.assertIn(remedy, out)
        self.assertIn("read-only", out)
        self.assertNotIn("<tarball>", out)

    def test_drift_refusal_without_remedy_keeps_the_template(self) -> None:
        out = self.br.format_scope_drift_refusal(
            sid="s", scope=["src"], refused=["x"], overridden=[],
            telemetry=None)
        self.assertIn("<tarball>", out)

    def test_sandbox_refusal_carries_the_composed_line(self) -> None:
        remedy = "bale apply 'r.tar.gz' --no-sandbox"
        out = self.br.format_sandbox_unavailable_refusal(
            sid="s", detail="sandbox self-probe failed (exit 1)",
            remedy=remedy, declined_at_prompt=False)
        self.assertIn("[SANDBOX-UNAVAILABLE] s", out)
        self.assertIn(remedy, out)
        self.assertIn("[sandbox] enabled = false", out)
        self.assertIn("self-probe failed", out)
        self.assertNotIn("admission prompt", out)
        out2 = self.br.format_sandbox_unavailable_refusal(
            sid="s", detail="d", remedy=remedy, declined_at_prompt=True)
        self.assertIn("admission prompt", out2)


class PromptGateTest(unittest.TestCase):
    """admission_prompt_allowed: every non-TTY door declines, in the
    documented order, and names itself."""

    @classmethod
    def setUpClass(cls):
        # bale_apply imports nothing from __main__ at module level, so
        # the pure predicate is reachable without bin/bale.
        cls.ba = _load_module("bale_apply")

    def _gate(self, **kw):
        base = dict(dry_run=False, no_interact=False, json_output=False,
                    stdin_isatty=True)
        base.update(kw)
        return self.ba.admission_prompt_allowed(**base)

    def test_tty_allows(self) -> None:
        self.assertEqual(self._gate(), (True, ""))

    def test_each_door_declines_and_names_itself(self) -> None:
        ok, why = self._gate(dry_run=True)
        self.assertFalse(ok); self.assertIn("--dry-run", why)
        ok, why = self._gate(no_interact=True, no_interact_source="--no-interact")
        self.assertFalse(ok); self.assertIn("--no-interact", why)
        ok, why = self._gate(json_output=True)
        self.assertFalse(ok); self.assertIn("--json", why)
        ok, why = self._gate(stdin_isatty=False)
        self.assertFalse(ok); self.assertIn("TTY", why)

    def test_order_dry_run_first(self) -> None:
        ok, why = self._gate(dry_run=True, no_interact=True, json_output=True,
                             stdin_isatty=False)
        self.assertFalse(ok)
        self.assertIn("--dry-run", why)


if __name__ == "__main__":
    unittest.main(verbosity=2)
