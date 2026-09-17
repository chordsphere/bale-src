#!/usr/bin/env python3
"""The `[probe] clipboard_command` config trio (board 99a).

The probe scaffold's opt-in clipboard epilogue landed crafter-side
first: `tools/craft_response.py --probe` reads `[probe]
clipboard_command` from the project bale.toml with its own minimal
single-key scan. This suite pins the config-side carrier in
`bin/bale_config.py` — the typed accessor, the renderer branch, and the
wizard walk — and, above all, that bale and the crafter agree about
every value the wizard can write.

Three tiers, cheapest first:

- **Unit** (no subprocess): `get_probe_clipboard_command` semantics —
  absent/empty read as unset, set values come back stripped, non-string
  and crafter-unreadable shapes are fatal — plus the project-only merge
  ruling (a global [probe] is never inherited) and the renderer's
  `[probe]` branch, including literal non-ASCII.
- **Agreement** (the crafter's own reader, imported from tools/): every
  value the accessor accepts, rendered by `render_bale_toml`, reads back
  identically through `read_clipboard_command`; every value the shape
  check refuses would have read back as unset — so the refusal is
  load-bearing, not taste.
- **Wizard**: `walk_configurables` driven with a label-aware input
  stand-in (set, reject-and-keep, global never walks), and the PTY
  discoverable-surface pair through a real `bale config init` (the
  test_sandbox_wrapper / test_blind_checkpoint precedent): the project
  wizard walks and preserves the key and states why it is project-only;
  the global wizard never offers it.

Board 69's registry rider (session 2026-09-16-board-69-tools-pair-008)
extends the agreement tier to the hand-edited TOML literal string: for
`clipboard_command = 'pbcopy'` the crafter's reader returns `pbcopy`,
the value bale's accessor returns; every readable command a literal can
carry agrees on both sides; a refused content (backslash, double quote,
raw tab) is unset crafter-side in either quote form and fatal
bale-side; and the one remaining split — triple-quoted strings, which
bale's parser reads and the crafter's one-line scan does not — is named
in the crafter's treated-as-unset note, pinned here.
"""

from __future__ import annotations

import builtins
import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path

from harness import (
    REPO_ROOT,
    bale_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale_pty,
)

sys.path.insert(0, str(REPO_ROOT / "bin"))
import bale_config  # noqa: E402  (path-injected sibling import)
import _bale_toml as tomllib  # noqa: E402  (the module's own TOML shim)

CRAFTER_PATH = REPO_ROOT / "tools" / "craft_response.py"


def load_crafter():
    """Import tools/craft_response.py as a module (it is a script)."""
    spec = importlib.util.spec_from_file_location(
        "craft_response_under_test", CRAFTER_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# Values a real operator configures; every one must survive the round
# trip bale-render → crafter-read unchanged.
READABLE_COMMANDS = (
    "pbcopy",
    "xclip -selection clipboard",
    "clip.exe",
    "wl-copy --type text/plain",
    "cat >clipboard-capture.txt",
    "tee /tmp/probé-output.txt",  # non-ASCII rides literally
    "sh -c 'pbcopy'",             # single quotes are fine
)

# Values the shape check refuses, each with the substring its reason
# names. Rendered anyway, each would read back as unset crafter-side.
UNREADABLE_COMMANDS = (
    ("C:\\Windows\\clip.exe", "backslash"),
    ('sh -c "pbcopy"', "double quote"),
    ("xclip\t-selection clipboard", "control character"),
    ("pbcopy\nrm -rf /", "control character"),
)


class _FailRaises:
    """Stand in for bin/bale's fail() on direct-import unit runs.

    bale_config imports fail lazily from __main__; production supplies
    bin/bale's. The stand-in raises so a fatal shape is observable
    (the test_sandbox_wrapper __main__-injection precedent).
    """

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


class _HermeticConfigBase(unittest.TestCase):
    """Temp repo + a temp global config path, fail() stand-in active."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-probecfg-")
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

    def accessor(self):
        return bale_config.get_probe_clipboard_command(
            bale_config.merged_config(self.repo))


class AccessorUnitTest(_HermeticConfigBase):
    """get_probe_clipboard_command + the project-only merge ruling."""

    def test_key_is_declared_in_probe_values(self) -> None:
        """The trio's anchor: the renderer iterates PROBE_VALUES."""
        self.assertEqual(bale_config.PROBE_VALUES, ("clipboard_command",))

    def test_absent_file_section_and_key_are_unset(self) -> None:
        self.assertIsNone(self.accessor())
        self.write_project("[hooks]\npost_pack = \"x.sh\"\n")
        self.assertIsNone(self.accessor())
        self.write_project("[probe]\n")
        self.assertIsNone(self.accessor())

    def test_set_value_comes_back_stripped(self) -> None:
        self.write_project('[probe]\nclipboard_command = "  pbcopy  "\n')
        self.assertEqual(self.accessor(), "pbcopy")

    def test_empty_and_blank_values_are_unset(self) -> None:
        for body in ('clipboard_command = ""', 'clipboard_command = "   "'):
            with self.subTest(body=body):
                self.write_project(f"[probe]\n{body}\n")
                self.assertIsNone(self.accessor())

    def test_global_probe_section_is_never_inherited(self) -> None:
        """A global value would never reach the crafter, which reads the
        project bale.toml as shipped in the request — so the merge drops
        it rather than reporting a configuration nothing consults."""
        self.global_toml.parent.mkdir(parents=True)
        self.global_toml.write_text(
            '[probe]\nclipboard_command = "pbcopy"\n', encoding="utf-8")
        cfg = bale_config.merged_config(self.repo)
        self.assertNotIn("probe", cfg,
                         msg="a global [probe] leaked into the merge")
        self.assertIsNone(bale_config.get_probe_clipboard_command(cfg))

    def test_project_value_wins_with_a_global_present(self) -> None:
        self.global_toml.parent.mkdir(parents=True)
        self.global_toml.write_text(
            '[probe]\nclipboard_command = "xclip"\n', encoding="utf-8")
        self.write_project('[probe]\nclipboard_command = "pbcopy"\n')
        self.assertEqual(self.accessor(), "pbcopy")

    def test_non_string_value_is_fatal(self) -> None:
        for body in ("clipboard_command = 123",
                     "clipboard_command = true",
                     'clipboard_command = ["pbcopy"]'):
            with self.subTest(body=body):
                self.write_project(f"[probe]\n{body}\n")
                with self.assertRaises(_FailRaises.Fatal) as ctx:
                    self.accessor()
                self.assertIn("must be a string", str(ctx.exception))

    def test_non_table_section_is_fatal(self) -> None:
        cfg = {"probe": "pbcopy"}
        with self.assertRaises(_FailRaises.Fatal) as ctx:
            bale_config.get_probe_clipboard_command(cfg)
        self.assertIn("[probe] must be a table", str(ctx.exception))

    def test_crafter_unreadable_shapes_are_fatal(self) -> None:
        for value, reason in UNREADABLE_COMMANDS:
            with self.subTest(value=value):
                cfg = {"probe": {"clipboard_command": value}}
                with self.assertRaises(_FailRaises.Fatal) as ctx:
                    bale_config.get_probe_clipboard_command(cfg)
                self.assertIn(reason, str(ctx.exception))
                self.assertIn("craft_response.py", str(ctx.exception),
                              msg="the refusal names the reader it "
                                  "protects")


class ShapeCheckUnitTest(unittest.TestCase):
    """probe_clipboard_command_problem: None for readable, a reason
    otherwise."""

    def test_readable_commands_have_no_problem(self) -> None:
        for value in READABLE_COMMANDS:
            with self.subTest(value=value):
                self.assertIsNone(
                    bale_config.probe_clipboard_command_problem(value))

    def test_unreadable_commands_name_their_problem(self) -> None:
        for value, reason in UNREADABLE_COMMANDS:
            with self.subTest(value=value):
                problem = bale_config.probe_clipboard_command_problem(value)
                self.assertIsNotNone(problem)
                self.assertIn(reason, problem)

    def test_delete_character_is_a_control_character(self) -> None:
        self.assertIn("control character",
                      bale_config.probe_clipboard_command_problem("a\x7fb"))


class RendererUnitTest(unittest.TestCase):
    """render_bale_toml's [probe] branch."""

    def test_renderer_emits_the_section_and_key(self) -> None:
        rendered = bale_config.render_bale_toml(
            {"probe": {"clipboard_command": "pbcopy"}})
        self.assertIn('[probe]\nclipboard_command = "pbcopy"\n', rendered)

    def test_renderer_omits_an_unset_section(self) -> None:
        rendered = bale_config.render_bale_toml({})
        self.assertNotIn("[probe]", rendered)

    def test_non_ascii_is_written_literally(self) -> None:
        """json.dumps' default would write \\u00e9, a backslash the
        crafter's reader treats as unset."""
        rendered = bale_config.render_bale_toml(
            {"probe": {"clipboard_command": "tee /tmp/probé.txt"}})
        self.assertIn('clipboard_command = "tee /tmp/probé.txt"', rendered)
        self.assertNotIn("\\u00e9", rendered)

    def test_rendered_file_parses_back_to_the_same_value(self) -> None:
        for value in READABLE_COMMANDS:
            with self.subTest(value=value):
                rendered = bale_config.render_bale_toml(
                    {"probe": {"clipboard_command": value}})
                parsed = tomllib.loads(rendered)
                self.assertEqual(parsed["probe"]["clipboard_command"], value)


@unittest.skipUnless(CRAFTER_PATH.is_file(),
                     "tools/craft_response.py not shipped in this sandbox")
class CrafterAgreementTest(_HermeticConfigBase):
    """bale's accessor and the crafter's scan agree on the written file.

    The crafter is the key's only consumer; this is the test that makes
    "the config-side carrier lands the same spelling" mechanical rather
    than a comment in two files.
    """

    def setUp(self) -> None:
        super().setUp()
        self.crafter = load_crafter()

    def render_to_repo(self, value: str) -> None:
        (self.repo / "bale.toml").write_text(
            bale_config.render_bale_toml(
                {"probe": {"clipboard_command": value}}),
            encoding="utf-8")

    def test_spelling_matches_the_crafter_constants(self) -> None:
        self.assertEqual(self.crafter.CLIPBOARD_SECTION, "probe")
        self.assertEqual(self.crafter.CLIPBOARD_KEY,
                         bale_config.PROBE_VALUES[0])

    def test_every_accepted_value_reads_back_identically(self) -> None:
        for value in READABLE_COMMANDS + ("  pbcopy  ",):
            with self.subTest(value=value):
                self.render_to_repo(value)
                crafter_cmd, note = self.crafter.read_clipboard_command(
                    self.repo)
                self.assertEqual(crafter_cmd, value.strip(), msg=note)
                self.assertEqual(self.accessor(), crafter_cmd)

    def test_every_refused_value_would_read_as_unset(self) -> None:
        """The refusal is load-bearing: rendered anyway, the crafter
        would silently fall back to remedy text."""
        for value, _reason in UNREADABLE_COMMANDS:
            with self.subTest(value=value):
                self.render_to_repo(value)
                crafter_cmd, _note = self.crafter.read_clipboard_command(
                    self.repo)
                self.assertIsNone(crafter_cmd)

    def test_empty_value_is_unset_on_both_sides(self) -> None:
        self.render_to_repo("")
        crafter_cmd, _note = self.crafter.read_clipboard_command(self.repo)
        self.assertIsNone(crafter_cmd)
        self.assertIsNone(self.accessor())

    # -- board 69's registry rider: the hand-edited literal string -----

    def test_single_quoted_literal_reads_back_on_both_sides(self) -> None:
        """The rider's graded outcome: for clipboard_command = 'pbcopy'
        the crafter's reader returns pbcopy — the value bale's own TOML
        parser and accessor return for the same bytes."""
        self.write_project("[probe]\nclipboard_command = 'pbcopy'\n")
        crafter_cmd, note = self.crafter.read_clipboard_command(self.repo)
        self.assertEqual(crafter_cmd, "pbcopy", msg=note)
        self.assertEqual(self.accessor(), "pbcopy")

    def test_hand_written_literals_agree_with_the_accessor(self) -> None:
        """Every readable command that a literal string can carry (no
        single quote inside), padded and with a trailing comment, reads
        identically on both sides."""
        for value in READABLE_COMMANDS:
            if "'" in value:
                continue  # a TOML literal string cannot contain its quote
            for line in (f"clipboard_command = '{value}'",
                         f"clipboard_command = '  {value}  '  # hand edit"):
                with self.subTest(line=line):
                    self.write_project(f"[probe]\n{line}\n")
                    crafter_cmd, note = self.crafter.read_clipboard_command(
                        self.repo)
                    self.assertEqual(crafter_cmd, value, msg=note)
                    self.assertEqual(self.accessor(), crafter_cmd)

    def test_refused_contents_in_either_quote_read_as_unset(self) -> None:
        """A one-line value bale's accessor refuses is unset crafter-side
        in both quote forms — including a raw tab, legal TOML in either
        form, which the basic-string scan used to return."""
        cases = (
            ("clipboard_command = 'C:\\Windows\\clip.exe'", "backslash"),
            ("clipboard_command = 'sh -c \"pbcopy\"'", "double quote"),
            ("clipboard_command = 'xclip\t-selection clipboard'",
             "control character"),
            ('clipboard_command = "xclip\t-selection clipboard"',
             "control character"),
        )
        for line, reason in cases:
            with self.subTest(line=line):
                self.write_project(f"[probe]\n{line}\n")
                crafter_cmd, _note = self.crafter.read_clipboard_command(
                    self.repo)
                self.assertIsNone(crafter_cmd)
                with self.assertRaises(_FailRaises.Fatal) as ctx:
                    self.accessor()
                self.assertIn(reason, str(ctx.exception))

    def test_unread_triple_quoted_forms_are_named_in_the_note(self) -> None:
        """The known remaining split, disclosed rather than silent: bale
        parses a one-line triple-quoted string; the crafter's scan does
        not read it, and its treated-as-unset note says so."""
        for line in ("clipboard_command = '''pbcopy'''",
                     'clipboard_command = """pbcopy"""'):
            with self.subTest(line=line):
                self.write_project(f"[probe]\n{line}\n")
                crafter_cmd, note = self.crafter.read_clipboard_command(
                    self.repo)
                self.assertIsNone(crafter_cmd)
                self.assertIn("treated as unset", note)
                self.assertIn("triple-quoted", note)
                self.assertIn("'single-quoted'", note)


def _walk_with_answers(existing: dict, *, layer: str,
                       answers: dict[str, str]) -> tuple[dict, str]:
    """Run walk_configurables with input() answering by prompt label.

    Every prompt prints `[<label>]` before its input() call; the stand-in
    finds the most recent label in the captured output and answers from
    `answers` (Enter otherwise). Order-independent, so adding a
    configurable elsewhere in the walk cannot shift these answers.
    """
    buffer = io.StringIO()

    def fake_input(_prompt: str = "") -> str:
        label = None
        for line in reversed(buffer.getvalue().splitlines()):
            if line.startswith("[") and line.endswith("]"):
                label = line[1:-1]
                break
        return answers.get(label, "")

    saved_input = builtins.input
    builtins.input = fake_input
    try:
        with contextlib.redirect_stdout(buffer):
            new = bale_config.walk_configurables(
                existing, layer=layer, inherited=None)
    finally:
        builtins.input = saved_input
    return new, buffer.getvalue()


class WizardWalkUnitTest(unittest.TestCase):
    """walk_configurables' [probe] block, in-process."""

    def test_project_walk_sets_the_key(self) -> None:
        new, out = _walk_with_answers(
            {}, layer="project",
            answers={"probe.clipboard_command": "xclip -selection clipboard"})
        self.assertEqual(new.get("probe"),
                         {"clipboard_command": "xclip -selection clipboard"})
        self.assertIn("[probe.clipboard_command]", out)

    def test_project_walk_enter_keeps_the_existing_value(self) -> None:
        new, _out = _walk_with_answers(
            {"probe": {"clipboard_command": "pbcopy"}}, layer="project",
            answers={})
        self.assertEqual(new.get("probe"), {"clipboard_command": "pbcopy"})

    def test_project_walk_enter_on_fresh_repo_writes_nothing(self) -> None:
        new, out = _walk_with_answers({}, layer="project", answers={})
        self.assertNotIn("probe", new)
        self.assertIn("(unset — no clipboard epilogue)", out)

    def test_project_walk_dash_clears_the_key(self) -> None:
        new, _out = _walk_with_answers(
            {"probe": {"clipboard_command": "pbcopy"}}, layer="project",
            answers={"probe.clipboard_command": "-"})
        self.assertNotIn("probe", new)

    def test_unreadable_entry_is_refused_and_current_kept(self) -> None:
        for value, reason in UNREADABLE_COMMANDS[:2]:
            with self.subTest(value=value):
                new, out = _walk_with_answers(
                    {"probe": {"clipboard_command": "pbcopy"}},
                    layer="project",
                    answers={"probe.clipboard_command": value})
                self.assertEqual(new.get("probe"),
                                 {"clipboard_command": "pbcopy"})
                self.assertIn(reason, out)
                self.assertIn("Keeping current", out)

    def test_prompt_states_the_project_only_reason(self) -> None:
        _new, out = _walk_with_answers({}, layer="project", answers={})
        self.assertIn("would never reach the probe epilogue", out)

    def test_global_walk_never_offers_the_key(self) -> None:
        new, out = _walk_with_answers({}, layer="global", answers={})
        self.assertNotIn("probe.clipboard_command", out)
        self.assertNotIn("probe", new)


class WizardSurfaceTest(unittest.TestCase):
    """The discoverable-surface pair through a real `bale config init`
    under a pty (the test_sandbox_wrapper precedent)."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-probewiz-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, home=self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_project_wizard_walks_and_preserves_the_key(self) -> None:
        (self.repo / "bale.toml").write_text(
            '[probe]\nclipboard_command = "pbcopy"\n', encoding="utf-8")
        code, output = run_bale_pty(
            self.install, ["config", "init"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("probe.clipboard_command", output,
                      msg="the project wizard walks the key — the "
                          "discoverable-surface contract")
        rendered = (self.repo / "bale.toml").read_text(encoding="utf-8")
        self.assertIn("[probe]", rendered)
        self.assertIn('clipboard_command = "pbcopy"', rendered,
                      msg="Enter-through re-runs preserve the set value — "
                          "the renderer-preservation precedent")

    def test_global_wizard_never_walks_the_key(self) -> None:
        code, output = run_bale_pty(
            self.install, ["config", "init", "--global"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertNotIn("probe.clipboard_command", output,
                         msg="the global wizard must not offer a key no "
                             "global-layer reader consults")


if __name__ == "__main__":
    unittest.main(verbosity=2)
