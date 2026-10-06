#!/usr/bin/env python3
"""The clipboard command's config trio (board 99a's `[probe]
clipboard_command`; `[clipboard] command` since session
clipboard-key-rename, the legacy spelling still read as an alias).

The probe scaffold's opt-in clipboard epilogue landed crafter-side
first: `tools/craft_response.py --probe` reads the key from the project
bale.toml with its own minimal single-key scan. This suite pins the
config-side carrier in `bin/bale_config.py` — the typed accessor, the
renderer branch, and the wizard walk — and, above all, that bale and
the crafter agree about every value the wizard can write, under either
spelling of the key. The suite keeps its pre-rename file name; the
rename's own outcomes (the two-key precedence, the wizard's carry-over,
the status row and its JSON object) have their own suite in
tests/test_clipboard_key_rename.py.

Three tiers, cheapest first:

- **Unit** (no subprocess): `get_probe_clipboard_command` semantics —
  absent/empty read as unset, set values come back stripped, non-string
  and crafter-unreadable shapes are fatal — plus the both-layer merge
  (session wizard-defaults: a global [probe] is inherited, a project
  value wins, "" at the project suppresses), the accessors bale code
  calls (`effective_clipboard_command`, `clipboard_command_source`),
  the bale-side refusal of spellings the crafter cannot see
  (triple-quoted above all — the 005/69 rider), and the renderer's
  `[probe]` branch, including literal non-ASCII.
- **Agreement** (the crafter's own reader, imported from tools/): every
  value the accessor accepts, rendered by `render_bale_toml`, reads back
  identically through `read_clipboard_command`; every value the shape
  check refuses would have read back as unset — so the refusal is
  load-bearing, not taste.
- **Wizard**: `walk_configurables` driven with a label-aware input
  stand-in (set, reject-and-keep, set and suppress at both layers, a
  numbered pick, the spelling warning, the full description reachable
  through the '?' gesture), and the PTY discoverable-surface pair
  through a real `bale config init`: both wizards walk the key, and a
  project bale.toml that sets it — in either spelling — is still read
  by the crafter after an Enter-through re-run (the session's
  back-compat constraint, kept across the rename).

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
import json
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
import bale_wizard  # noqa: E402  (the wizard presentation layer)
import _bale_toml as tomllib  # noqa: E402  (the module's own TOML shim)

CRAFTER_PATH = REPO_ROOT / "tools" / "craft_response.py"


def json_quote(value: str) -> str:
    """`value` as a one-line TOML basic string, the way the renderer
    writes it (non-ASCII literal)."""
    return json.dumps(value, ensure_ascii=False)


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


# The two spellings of the one key, as a file writes each: (section
# header, key name, dotted form). Every accessor-level case below runs
# under both — the rename's constraint that a legacy file reads the same.
SPELLINGS = (
    ("[clipboard]", "command", "clipboard.command"),
    ("[probe]", "clipboard_command", "probe.clipboard_command"),
)


class AccessorUnitTest(_HermeticConfigBase):
    """get_clipboard_command (get_probe_clipboard_command, its pre-rename
    name) + the both-layer merge, under either spelling of the key."""

    def test_key_is_declared_in_the_value_tuples(self) -> None:
        """The trio's anchor: the renderer writes CLIPBOARD_VALUES and
        the readers walk CLIPBOARD_SPELLINGS, new spelling first."""
        self.assertEqual(bale_config.CLIPBOARD_VALUES, ("command",))
        self.assertEqual(bale_config.PROBE_VALUES, ("clipboard_command",))
        self.assertEqual(bale_config.CLIPBOARD_SPELLINGS,
                         (("clipboard", "command"),
                          ("probe", "clipboard_command")))
        self.assertEqual(bale_config.CLIPBOARD_DOTTED, "clipboard.command")
        self.assertEqual(bale_config.LEGACY_CLIPBOARD_DOTTED,
                         "probe.clipboard_command")
        self.assertIs(bale_config.get_probe_clipboard_command,
                      bale_config.get_clipboard_command)
        self.assertIs(bale_config.probe_clipboard_command_problem,
                      bale_config.clipboard_command_problem)

    def test_absent_file_section_and_key_are_unset(self) -> None:
        self.assertIsNone(self.accessor())
        self.write_project("[hooks]\npost_pack = \"x.sh\"\n")
        self.assertIsNone(self.accessor())
        for header, _key, _dotted in SPELLINGS:
            self.write_project(f"{header}\n")
            self.assertIsNone(self.accessor())

    def test_set_value_comes_back_stripped(self) -> None:
        for header, key, _dotted in SPELLINGS:
            with self.subTest(header=header):
                self.write_project(f'{header}\n{key} = "  pbcopy  "\n')
                self.assertEqual(self.accessor(), "pbcopy")

    def test_empty_and_blank_values_are_unset(self) -> None:
        for header, key, _dotted in SPELLINGS:
            for value in ('""', '"   "'):
                with self.subTest(header=header, value=value):
                    self.write_project(f"{header}\n{key} = {value}\n")
                    self.assertIsNone(self.accessor())

    def test_global_section_is_inherited_in_either_spelling(self) -> None:
        """Per-machine since session wizard-defaults (ruling 1): a
        global value applies wherever the project does not set the key.
        The merge lays the deciding file's own spelling in."""
        self.global_toml.parent.mkdir(parents=True)
        for header, key, _dotted in SPELLINGS:
            with self.subTest(header=header):
                self.global_toml.write_text(
                    f'{header}\n{key} = "pbcopy"\n', encoding="utf-8")
                cfg = bale_config.merged_config(self.repo)
                self.assertEqual(cfg.get(header[1:-1]), {key: "pbcopy"})
                self.assertEqual(bale_config.get_clipboard_command(cfg),
                                 "pbcopy")

    def test_project_empty_string_suppresses_the_global(self) -> None:
        self.global_toml.parent.mkdir(parents=True)
        for g_header, g_key, _d in SPELLINGS:
            for p_header, p_key, _d2 in SPELLINGS:
                with self.subTest(glob=g_header, project=p_header):
                    self.global_toml.write_text(
                        f'{g_header}\n{g_key} = "pbcopy"\n', encoding="utf-8")
                    self.write_project(f'{p_header}\n{p_key} = ""\n')
                    self.assertIsNone(self.accessor())

    def test_project_value_wins_with_a_global_present(self) -> None:
        """Across files the layer rule is spelling-blind: the project
        decides when it sets either spelling."""
        self.global_toml.parent.mkdir(parents=True)
        for g_header, g_key, _d in SPELLINGS:
            for p_header, p_key, _d2 in SPELLINGS:
                with self.subTest(glob=g_header, project=p_header):
                    self.global_toml.write_text(
                        f'{g_header}\n{g_key} = "xclip"\n', encoding="utf-8")
                    self.write_project(f'{p_header}\n{p_key} = "pbcopy"\n')
                    self.assertEqual(self.accessor(), "pbcopy")
                    merged = bale_config.merged_config(self.repo)
                    self.assertEqual(
                        merged.get(p_header[1:-1]), {p_key: "pbcopy"})
                    if g_header != p_header:
                        self.assertNotIn(g_header[1:-1], merged,
                                         msg="nothing of the global "
                                             "file's spelling is mixed in")

    def test_new_spelling_wins_inside_one_file(self) -> None:
        """The desk's precedence pin, in-file half: [clipboard] command
        wins when both spellings are set — including the suppress form."""
        self.write_project('[clipboard]\ncommand = "pbcopy"\n'
                           '[probe]\nclipboard_command = "xclip"\n')
        self.assertEqual(self.accessor(), "pbcopy")
        self.write_project('[probe]\nclipboard_command = "xclip"\n'
                           '[clipboard]\ncommand = "pbcopy"\n')
        self.assertEqual(self.accessor(), "pbcopy",
                         msg="section order in the file does not matter")
        self.write_project('[clipboard]\ncommand = ""\n'
                           '[probe]\nclipboard_command = "xclip"\n')
        self.assertIsNone(self.accessor(),
                          msg="an empty [clipboard] command suppresses "
                              "the same file's legacy value too")
        self.write_project('[clipboard]\nother = 1\n'
                           '[probe]\nclipboard_command = "xclip"\n')
        self.assertEqual(self.accessor(), "xclip",
                         msg="a [clipboard] table without the key falls "
                             "through to the legacy spelling")

    def test_non_string_value_is_fatal(self) -> None:
        for header, key, dotted in SPELLINGS:
            for value in ("123", "true", '["pbcopy"]'):
                with self.subTest(header=header, value=value):
                    self.write_project(f"{header}\n{key} = {value}\n")
                    with self.assertRaises(_FailRaises.Fatal) as ctx:
                        self.accessor()
                    self.assertIn(f"{dotted} must be a string",
                                  str(ctx.exception))

    def test_non_table_section_is_fatal(self) -> None:
        for section in ("clipboard", "probe"):
            with self.subTest(section=section):
                with self.assertRaises(_FailRaises.Fatal) as ctx:
                    bale_config.get_clipboard_command({section: "pbcopy"})
                self.assertIn(f"[{section}] must be a table",
                              str(ctx.exception))
        self.write_project('clipboard = "pbcopy"\n'
                           '[probe]\nclipboard_command = "xclip"\n')
        with self.assertRaises(_FailRaises.Fatal) as ctx:
            self.accessor()
        self.assertIn("[clipboard] must be a table", str(ctx.exception),
                      msg="a misshapen new section is refused, never "
                          "skipped in favour of the legacy key")

    def test_crafter_unreadable_shapes_are_fatal(self) -> None:
        for section, key in bale_config.CLIPBOARD_SPELLINGS:
            for value, reason in UNREADABLE_COMMANDS:
                with self.subTest(section=section, value=value):
                    cfg = {section: {key: value}}
                    with self.assertRaises(_FailRaises.Fatal) as ctx:
                        bale_config.get_clipboard_command(cfg)
                    self.assertIn(reason, str(ctx.exception))
                    self.assertIn(f"{section}.{key} ", str(ctx.exception))
                    self.assertIn("craft_response.py", str(ctx.exception),
                                  msg="the refusal names the reader it "
                                      "protects")


class ShapeCheckUnitTest(unittest.TestCase):
    """clipboard_command_problem: None for readable, a reason
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
    """render_bale_toml's [clipboard] branch — which never writes the
    legacy spelling."""

    def test_renderer_emits_the_section_and_key(self) -> None:
        rendered = bale_config.render_bale_toml(
            {"clipboard": {"command": "pbcopy"}})
        self.assertIn('[clipboard]\ncommand = "pbcopy"\n', rendered)
        self.assertNotIn("[probe]", rendered)

    def test_renderer_omits_an_unset_section(self) -> None:
        rendered = bale_config.render_bale_toml({})
        self.assertNotIn("[clipboard]", rendered)
        self.assertNotIn("[probe]", rendered)

    def test_legacy_dict_is_carried_into_the_new_spelling(self) -> None:
        """A parsed pre-rename file handed straight to the renderer
        writes [clipboard] command with the same value; a dict carrying
        both writes the [clipboard] one (the in-file precedence)."""
        rendered = bale_config.render_bale_toml(
            {"probe": {"clipboard_command": "pbcopy"}})
        self.assertIn('[clipboard]\ncommand = "pbcopy"\n', rendered)
        self.assertNotIn("[probe]", rendered)
        self.assertNotIn("clipboard_command", rendered)
        rendered = bale_config.render_bale_toml(
            {"probe": {"clipboard_command": "xclip"},
             "clipboard": {"command": "pbcopy"}})
        self.assertIn('[clipboard]\ncommand = "pbcopy"\n', rendered)
        self.assertNotIn("xclip", rendered)
        rendered = bale_config.render_bale_toml(
            {"probe": {"clipboard_command": ""}})
        self.assertIn('[clipboard]\ncommand = ""\n', rendered,
                      msg="the suppress form moves too")

    def test_non_ascii_is_written_literally(self) -> None:
        """json.dumps' default would write \\u00e9, a backslash the
        crafter's reader treats as unset."""
        rendered = bale_config.render_bale_toml(
            {"clipboard": {"command": "tee /tmp/probé.txt"}})
        self.assertIn('command = "tee /tmp/probé.txt"', rendered)
        self.assertNotIn("\\u00e9", rendered)

    def test_rendered_file_parses_back_to_the_same_value(self) -> None:
        for value in READABLE_COMMANDS:
            with self.subTest(value=value):
                rendered = bale_config.render_bale_toml(
                    {"clipboard": {"command": value}})
                parsed = tomllib.loads(rendered)
                self.assertEqual(parsed["clipboard"]["command"], value)
                self.assertNotIn("probe", parsed)


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
                {"clipboard": {"command": value}}),
            encoding="utf-8")

    def test_spelling_matches_the_crafter_constants(self) -> None:
        self.assertEqual(self.crafter.CLIPBOARD_SECTION, "clipboard")
        self.assertEqual(self.crafter.CLIPBOARD_KEY,
                         bale_config.CLIPBOARD_VALUES[0])
        self.assertEqual(self.crafter.LEGACY_CLIPBOARD_SECTION, "probe")
        self.assertEqual(self.crafter.LEGACY_CLIPBOARD_KEY,
                         bale_config.PROBE_VALUES[0])
        self.assertEqual(self.crafter.CLIPBOARD_SPELLINGS,
                         bale_config.CLIPBOARD_SPELLINGS,
                         msg="one precedence order on both sides")

    def test_legacy_spelling_reads_back_on_both_sides(self) -> None:
        """A pre-rename file is read the same by bale and the crafter:
        the legacy alias is the whole of the back-compat promise."""
        for value in READABLE_COMMANDS:
            with self.subTest(value=value):
                self.write_project(
                    f'[probe]\nclipboard_command = {json_quote(value)}\n')
                crafter_cmd, note = self.crafter.read_clipboard_command(
                    self.repo)
                self.assertEqual(crafter_cmd, value, msg=note)
                self.assertIn("legacy spelling", note)
                self.assertEqual(self.accessor(), crafter_cmd)

    def test_both_spellings_in_one_file_agree_on_the_new_one(self) -> None:
        """The in-file precedence is shared: both readers take
        [clipboard] command, wherever it sits in the file, and both
        read a new-key suppress as no command."""
        for body in ('[clipboard]\ncommand = "pbcopy"\n'
                     '[probe]\nclipboard_command = "xclip"\n',
                     '[probe]\nclipboard_command = "xclip"\n'
                     '[clipboard]\ncommand = "pbcopy"\n'):
            with self.subTest(body=body):
                self.write_project(body)
                crafter_cmd, note = self.crafter.read_clipboard_command(
                    self.repo)
                self.assertEqual(crafter_cmd, "pbcopy", msg=note)
                self.assertNotIn("legacy", note)
                self.assertEqual(self.accessor(), "pbcopy")
        self.write_project('[clipboard]\ncommand = ""\n'
                           '[probe]\nclipboard_command = "xclip"\n')
        self.assertIsNone(self.crafter.read_clipboard_command(self.repo)[0])
        self.assertIsNone(self.accessor())

    def test_unreadable_new_key_never_falls_through_to_the_legacy(self) -> None:
        """A triple-quoted [clipboard] command bale refuses: the crafter
        treats the file as unset rather than teeing into a legacy line
        bale ignores — right or loud, never split."""
        self.write_project("[clipboard]\ncommand = '''pbcopy'''\n"
                           '[probe]\nclipboard_command = "xclip"\n')
        crafter_cmd, note = self.crafter.read_clipboard_command(self.repo)
        self.assertIsNone(crafter_cmd)
        self.assertIn("[clipboard] command", note)
        self.assertIn("treated as unset", note)
        with self.assertRaises(_FailRaises.Fatal) as ctx:
            bale_config.effective_clipboard_command(self.repo)
        self.assertIn("clipboard.command is triple-quoted",
                      str(ctx.exception))

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


class EffectiveAccessorTest(_HermeticConfigBase):
    """effective_clipboard_command and clipboard_command_source — the
    readers session D's bale-side copying builds on — and the bale-side
    refusal of spellings the crafter's scan cannot see (the 005/69
    rider routed to this session)."""

    def write_global(self, body: str) -> None:
        self.global_toml.parent.mkdir(parents=True, exist_ok=True)
        self.global_toml.write_text(body, encoding="utf-8")

    def test_layering_and_source(self) -> None:
        eff = bale_config.effective_clipboard_command
        src = bale_config.clipboard_command_source
        self.assertEqual((eff(self.repo), src(self.repo)), (None, None))
        self.write_global('[probe]\nclipboard_command = "wl-copy"\n')
        self.assertEqual((eff(self.repo), src(self.repo)),
                         ("wl-copy", "global"))
        self.assertEqual((eff(None), src(None)), ("wl-copy", "global"),
                         msg="outside a repo the global file decides")
        self.write_project('[probe]\nclipboard_command = " pbcopy "\n')
        self.assertEqual((eff(self.repo), src(self.repo)),
                         ("pbcopy", "project"))
        self.write_project('[probe]\nclipboard_command = ""\n')
        self.assertEqual((eff(self.repo), src(self.repo)),
                         (None, "project"),
                         msg="the project decided: none here")

    def test_layering_and_source_in_the_new_spelling(self) -> None:
        eff = bale_config.effective_clipboard_command
        src = bale_config.clipboard_command_source
        self.write_global('[clipboard]\ncommand = "wl-copy"\n')
        self.assertEqual((eff(self.repo), src(self.repo)),
                         ("wl-copy", "global"))
        self.assertEqual((eff(None), src(None)), ("wl-copy", "global"))
        self.write_project('[clipboard]\ncommand = " pbcopy "\n')
        self.assertEqual((eff(self.repo), src(self.repo)),
                         ("pbcopy", "project"))
        self.write_project('[clipboard]\ncommand = ""\n')
        self.assertEqual((eff(self.repo), src(self.repo)),
                         (None, "project"))

    def test_two_key_precedence_across_files(self) -> None:
        """The desk's pin, cross-file half: the project file decides when
        it sets either spelling; "" in either spelling suppresses; a
        global file is read in either spelling."""
        eff = bale_config.effective_clipboard_command
        src = bale_config.clipboard_command_source
        self.write_global('[clipboard]\ncommand = "wl-copy"\n')
        self.write_project('[probe]\nclipboard_command = "pbcopy"\n')
        self.assertEqual((eff(self.repo), src(self.repo)),
                         ("pbcopy", "project"),
                         msg="a legacy project key beats a new global key")
        self.write_project('[probe]\nclipboard_command = ""\n')
        self.assertEqual((eff(self.repo), src(self.repo)), (None, "project"))
        self.write_global('[probe]\nclipboard_command = "wl-copy"\n')
        self.write_project('[clipboard]\ncommand = "pbcopy"\n')
        self.assertEqual((eff(self.repo), src(self.repo)),
                         ("pbcopy", "project"))
        self.write_project('[clipboard]\ncommand = ""\n')
        self.assertEqual((eff(self.repo), src(self.repo)), (None, "project"))
        self.write_project("[hooks]\n")
        self.assertEqual((eff(self.repo), src(self.repo)),
                         ("wl-copy", "global"),
                         msg="a legacy global key is inherited")

    def test_two_key_precedence_inside_one_file(self) -> None:
        self.write_project('[probe]\nclipboard_command = "xclip"\n'
                           '[clipboard]\ncommand = "pbcopy"\n')
        self.assertEqual(bale_config.effective_clipboard_command(self.repo),
                         "pbcopy")
        self.write_global('[probe]\nclipboard_command = "xclip"\n'
                          '[clipboard]\ncommand = ""\n')
        (self.repo / "bale.toml").unlink()
        self.assertIsNone(bale_config.effective_clipboard_command(self.repo),
                          msg="an empty new key suppresses the legacy "
                              "value in the same global file")

    def test_content_problems_stay_fatal_at_either_layer(self) -> None:
        for header, key, _dotted in SPELLINGS:
            with self.subTest(header=header):
                self.write_global(f'{header}\n{key} = "a\\\\b"\n')
                with self.assertRaises(_FailRaises.Fatal) as ctx:
                    bale_config.effective_clipboard_command(self.repo)
                self.assertIn("backslash", str(ctx.exception))

    def test_triple_quoted_is_refused_at_both_layers(self) -> None:
        for header, key, dotted in SPELLINGS:
            for value in ("'''pbcopy'''", '"""pbcopy"""', '"""\npbcopy"""'):
                for layer in ("project", "global"):
                    with self.subTest(header=header, value=value, layer=layer):
                        (self.repo / "bale.toml").unlink(missing_ok=True)
                        self.global_toml.unlink(missing_ok=True)
                        write = (self.write_project if layer == "project"
                                 else self.write_global)
                        write(f"{header}\n{key} = {value}\n")
                        with self.assertRaises(_FailRaises.Fatal) as ctx:
                            bale_config.effective_clipboard_command(self.repo)
                        message = str(ctx.exception)
                        self.assertIn(f"{dotted} is triple-quoted", message)
                        self.assertIn("craft_response.py", message)
                        self.assertIn(f'{key} = "<command>" under a '
                                      f'{header} header', message)
                        rerun = ("bale config init --global"
                                 if layer == "global" else "bale config init`")
                        self.assertIn(rerun, message)
                        if dotted == "probe.clipboard_command":
                            self.assertIn("as [clipboard] command", message,
                                          msg="the remedy says the re-run "
                                              "re-spells a legacy key")
                        else:
                            self.assertNotIn("as [clipboard] command",
                                             message)

    def test_other_unseen_spellings_are_refused(self) -> None:
        cases = (
            ('probe.clipboard_command = "pbcopy"\n', "[probe] header"),
            ('probe = { clipboard_command = "pbcopy" }\n', "[probe] header"),
            ('[probe] # mine\nclipboard_command = "pbcopy"\n',
             "[probe] header"),
            ('clipboard.command = "pbcopy"\n', "[clipboard] header"),
            ('clipboard = { command = "pbcopy" }\n', "[clipboard] header"),
            ('[clipboard] # mine\ncommand = "pbcopy"\n', "[clipboard] header"),
            # A dotted new key beside a readable legacy line: the parser
            # decides by the new key, whose spelling the scan cannot see.
            ('clipboard.command = "pbcopy"\n'
             '[probe]\nclipboard_command = "xclip"\n', "[clipboard] header"),
        )
        for body, phrase in cases:
            with self.subTest(body=body):
                self.write_project(body)
                self.assertEqual(
                    bale_config.get_clipboard_command(
                        bale_config.merged_config(self.repo)), "pbcopy",
                    msg="bale's parser reads it")
                with self.assertRaises(_FailRaises.Fatal) as ctx:
                    bale_config.effective_clipboard_command(self.repo)
                self.assertIn(phrase, str(ctx.exception))

    def test_readable_spellings_pass(self) -> None:
        for body in ('[probe]\nclipboard_command = "pbcopy"\n',
                     "[probe]\nclipboard_command = 'pbcopy'  # mine\n",
                     '[ probe ]\n  clipboard_command="pbcopy"\n',
                     '[hooks]\n[probe]\nclipboard_command = """"""\n',
                     '[clipboard]\ncommand = "pbcopy"\n',
                     "[clipboard]\ncommand = 'pbcopy'  # mine\n",
                     '[ clipboard ]\n  command="pbcopy"\n',
                     '[hooks]\n[clipboard]\ncommand = """"""\n'):
            with self.subTest(body=body):
                self.write_project(body)
                expected = None if '""""""' in body else "pbcopy"
                self.assertEqual(
                    bale_config.effective_clipboard_command(self.repo),
                    expected)

    def test_spelling_problem_reads_the_file(self) -> None:
        for header, key, dotted in SPELLINGS:
            with self.subTest(header=header):
                self.write_project(f'{header}\n{key} = "pbcopy"\n')
                self.assertIsNone(bale_config.clipboard_command_spelling_problem(
                    self.repo / "bale.toml"))
                self.assertIsNone(bale_config.clipboard_command_spelling_problem(
                    self.repo / "bale.toml", dotted))
        self.assertIn("could not be re-read",
                      bale_config.clipboard_command_spelling_problem(
                          self.repo / "missing.toml"))
        self.write_project("[hooks]\n")
        self.assertIsNone(bale_config.clipboard_command_spelling_problem(
            self.repo / "bale.toml"), msg="nothing set, nothing to judge")
        self.write_project("[probe\n")
        self.assertIn("could not be re-parsed",
                      bale_config.clipboard_command_spelling_problem(
                          self.repo / "bale.toml"))


@unittest.skipUnless(CRAFTER_PATH.is_file(),
                     "tools/craft_response.py not shipped in this sandbox")
class NonExitingReadingTest(_HermeticConfigBase):
    """clipboard_command_reading — the non-exiting form of
    effective_clipboard_command (session log-hold, session D's first
    rider): the same answer for every readable file, and for every file
    the fatal accessor refuses, the same refusal text returned as a
    value — with fail() never called (the stand-in raises, so a call
    would surface here as _FailRaises.Fatal)."""

    def write_global(self, body: str) -> None:
        self.global_toml.parent.mkdir(parents=True, exist_ok=True)
        self.global_toml.write_text(body, encoding="utf-8")

    def reset(self) -> None:
        (self.repo / "bale.toml").unlink(missing_ok=True)
        self.global_toml.unlink(missing_ok=True)

    def test_readable_states_match_the_fatal_accessor_and_source(self) -> None:
        cases = (
            (None, None),
            (None, '[probe]\nclipboard_command = "wl-copy"\n'),
            ('[probe]\nclipboard_command = " pbcopy "\n',
             '[probe]\nclipboard_command = "wl-copy"\n'),
            ('[probe]\nclipboard_command = ""\n',
             '[probe]\nclipboard_command = "wl-copy"\n'),
            ('[hooks]\n', None),
        )
        for project, glob in cases:
            with self.subTest(project=project, glob=glob):
                self.reset()
                if project is not None:
                    self.write_project(project)
                if glob is not None:
                    self.write_global(glob)
                for repo in (self.repo, None):
                    reading = bale_config.clipboard_command_reading(repo)
                    self.assertIsNone(reading.refusal)
                    self.assertEqual(
                        (reading.command, reading.source),
                        (bale_config.effective_clipboard_command(repo),
                         bale_config.clipboard_command_source(repo)))

    def test_every_refusal_is_the_fatal_message_and_never_fails(self) -> None:
        refusals = (
            # (layer, file body, a phrase the refusal carries)
            ("project", "[probe\n", "is malformed TOML"),
            ("global", "[probe\n", "is malformed TOML"),
            ("global", '[probe]\nclipboard_command = "a\\\\b"\n',
             "backslash"),
            ("project", "[probe]\nclipboard_command = 3\n",
             "must be a string"),
            ("project", "[probe]\nclipboard_command = '''pbcopy'''\n",
             "is triple-quoted"),
            ("global", "[probe]\nclipboard_command = '''pbcopy'''\n",
             "is triple-quoted"),
            ("project", 'probe.clipboard_command = "pbcopy"\n',
             "[probe] header"),
        )
        for layer, body, phrase in refusals:
            with self.subTest(layer=layer, body=body):
                self.reset()
                (self.write_project if layer == "project"
                 else self.write_global)(body)
                reading = bale_config.clipboard_command_reading(self.repo)
                self.assertIsNone(reading.command)
                self.assertIn(phrase, reading.refusal or "")
                with self.assertRaises(_FailRaises.Fatal) as ctx:
                    bale_config.effective_clipboard_command(self.repo)
                self.assertEqual(str(ctx.exception), reading.refusal,
                                 msg="one refusal text, two forms")

    def test_refusal_keeps_the_deciding_layer_as_source(self) -> None:
        self.write_global("[probe]\nclipboard_command = '''x'''\n")
        self.assertEqual(
            bale_config.clipboard_command_reading(self.repo).source,
            "global")
        self.write_project("[probe\n")
        self.assertIsNone(
            bale_config.clipboard_command_reading(self.repo).source,
            msg="an unparsable file decides nothing")

    def test_key_and_shadowed_name_the_spellings(self) -> None:
        """The reading's two rename fields (session clipboard-key-rename):
        the dotted spelling the deciding file was read by, and the other
        spelling that file also sets and bale ignored."""
        R = bale_config.ClipboardCommandReading
        self.assertEqual(bale_config.clipboard_command_reading(self.repo),
                         R(None, None, None, None, None))
        self.write_global('[probe]\nclipboard_command = "wl-copy"\n')
        self.assertEqual(bale_config.clipboard_command_reading(self.repo),
                         R("wl-copy", "global", None,
                           "probe.clipboard_command", None))
        self.write_project('[clipboard]\ncommand = "pbcopy"\n')
        self.assertEqual(bale_config.clipboard_command_reading(self.repo),
                         R("pbcopy", "project", None,
                           "clipboard.command", None))
        self.write_project('[probe]\nclipboard_command = "xclip"\n'
                           '[clipboard]\ncommand = "pbcopy"\n')
        self.assertEqual(bale_config.clipboard_command_reading(self.repo),
                         R("pbcopy", "project", None, "clipboard.command",
                           "probe.clipboard_command"))
        self.write_project('[probe]\nclipboard_command = "xclip"\n'
                           '[clipboard]\ncommand = ""\n')
        self.assertEqual(bale_config.clipboard_command_reading(self.repo),
                         R(None, "project", None, "clipboard.command",
                           "probe.clipboard_command"),
                         msg="a suppressing new key still names the "
                             "legacy one it shadows")
        self.write_project("[probe]\nclipboard_command = 'xclip'\n"
                           "[clipboard]\ncommand = '''pbcopy'''\n")
        reading = bale_config.clipboard_command_reading(self.repo)
        self.assertEqual((reading.command, reading.source, reading.key,
                          reading.shadowed),
                         (None, "project", "clipboard.command",
                          "probe.clipboard_command"))
        self.assertIn("clipboard.command is triple-quoted", reading.refusal)
        self.assertEqual(R("c", "s", None), R("c", "s", None, None, None),
                         msg="the pre-rename triple still constructs")

    def test_loaders_share_the_reader_and_stay_fatal(self) -> None:
        self.write_project("[probe\n")
        cfg, refusal = bale_config.read_config_file(self.repo / "bale.toml")
        self.assertEqual(cfg, {})
        self.assertIn("is malformed TOML", refusal)
        with self.assertRaises(_FailRaises.Fatal) as ctx:
            bale_config.load_config(self.repo)
        self.assertEqual(str(ctx.exception), refusal)
        self.assertEqual(
            bale_config.read_config_file(self.tmp / "absent.toml"),
            ({}, None))


class SpellingTwinTest(_HermeticConfigBase):
    """bin/ restates the crafter's one-line scan (it never imports
    tools/); this pins the twin against the original on one corpus —
    both spellings, and files that carry the two together, since
    session clipboard-key-rename."""

    VALUES = (
        '"pbcopy"',
        "'pbcopy'",
        '"  xclip -selection clipboard  "  # c',
        "'''pbcopy'''",
        '"""pbcopy"""',
        '"a\\\\b"',
        "'sh -c \"x\"'",
        '"pbcopy" trailing',
        '""',
        "pbcopy",
        '"unterminated',
        '"tab\there"',
    )

    @staticmethod
    def crafter_scan(crafter, repo):
        """The crafter's answer as (status, value, dotted key) — the
        twin's shape — from scan_clipboard_command."""
        value, status, _rel, spelling = crafter.scan_clipboard_command(repo)
        dotted = f"{spelling[0]}.{spelling[1]}" if spelling else None
        return status, value, dotted

    def test_twin_agrees_with_the_crafter_on_every_line(self) -> None:
        crafter = load_crafter()
        texts = []
        for value in self.VALUES:
            for header, key in (("[clipboard]", "command"),
                                ("[probe]", "clipboard_command"),
                                ("[hooks]", "command"),
                                ("[hooks]", "clipboard_command"),
                                ("[clipboard]", "clipboard_command"),
                                ("[probe]", "command")):
                texts.append(f"{header}\n{key} = {value}\n")
        for value in self.VALUES:
            for other in ('"xclip"', "'''xclip'''", '""'):
                texts.append(f"[clipboard]\ncommand = {value}\n"
                             f"[probe]\nclipboard_command = {other}\n")
                texts.append(f"[probe]\nclipboard_command = {other}\n"
                             f"[clipboard]\ncommand = {value}\n")
        texts.append('[clipboard]\nother = "pbcopy"\n[probe]\n'
                     'clipboard_command = "pbcopy"\n')
        texts.append("")
        for text in texts:
            with self.subTest(text=text):
                self.write_project(text)
                twin_status, twin_value, _raw, twin_key = \
                    bale_config._scan_clipboard_line(text)
                self.assertEqual((twin_status, twin_value, twin_key),
                                 self.crafter_scan(crafter, self.repo))

    def test_the_new_spelling_decides_when_its_line_is_there(self) -> None:
        """The precedence is the scan's too, on both sides: a
        [clipboard] command line that is there — readable or not —
        decides, and the legacy line is read only when there is none."""
        crafter = load_crafter()
        cases = (
            ('[clipboard]\ncommand = "pbcopy"\n'
             '[probe]\nclipboard_command = "xclip"\n',
             ("set", "pbcopy", "clipboard.command")),
            ("[clipboard]\ncommand = '''pbcopy'''\n"
             '[probe]\nclipboard_command = "xclip"\n',
             ("bad-shape", None, "clipboard.command")),
            ('[clipboard]\ncommand = ""\n'
             '[probe]\nclipboard_command = "xclip"\n',
             ("bad-shape", None, "clipboard.command")),
            ('[clipboard]\nother = 1\n'
             '[probe]\nclipboard_command = "xclip"\n',
             ("set", "xclip", "probe.clipboard_command")),
            ('[probe]\nclipboard_command = "xclip"\n',
             ("set", "xclip", "probe.clipboard_command")),
            ("[hooks]\n", ("unset", None, None)),
        )
        for text, expected in cases:
            with self.subTest(text=text):
                self.write_project(text)
                status, value, _raw, key = bale_config._scan_clipboard_line(
                    text)
                self.assertEqual((status, value, key), expected)
                self.assertEqual(self.crafter_scan(crafter, self.repo),
                                 expected)


def _walk_with_answers(existing: dict, *, layer: str, answers: dict,
                       inherited=None, suggestions=None) -> tuple[dict, str]:
    """Run walk_configurables with input() answering by prompt label.

    Every item screen opens with a header line matching
    bale_wizard.ITEM_HEADER_RE (`  11/19  probe.clipboard_command ...`)
    before its input() call; the stand-in finds the most recent header in
    the captured output and answers from `answers` (Enter otherwise). An
    answer may be a list, consumed one entry per input() call for that
    item — how a test types '?' and then its real answer. Order-
    independent, so adding a configurable elsewhere in the walk cannot
    shift these answers.
    """
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
                existing, layer=layer, inherited=inherited,
                suggestions=suggestions)
    finally:
        builtins.input = saved_input
    return new, buffer.getvalue()


KEY = "clipboard.command"


class WizardWalkUnitTest(unittest.TestCase):
    """walk_configurables' [clipboard] block, in-process."""

    def test_project_walk_sets_the_key(self) -> None:
        new, out = _walk_with_answers(
            {}, layer="project",
            answers={KEY: "xclip -selection clipboard"})
        self.assertEqual(new.get("clipboard"),
                         {"command": "xclip -selection clipboard"})
        self.assertNotIn("probe", new)
        self.assertRegex(out, r"(?m)^\s*\d+/\d+  clipboard\.command\b",
                         msg="the item screen names its dotted key")
        self.assertNotIn("probe.clipboard_command", out,
                         msg="the legacy spelling is not a screen")

    def test_project_walk_enter_keeps_the_existing_value(self) -> None:
        new, _out = _walk_with_answers(
            {"clipboard": {"command": "pbcopy"}}, layer="project",
            answers={})
        self.assertEqual(new.get("clipboard"), {"command": "pbcopy"})

    def test_legacy_value_is_current_and_enter_carries_it_over(self) -> None:
        """Outcome 5: a file that carries only the legacy spelling has
        its value carried into the new spelling on the wizard's next
        write — the value unchanged, only the spelling moves — and the
        screen says where the current value came from."""
        new, out = _walk_with_answers(
            {"probe": {"clipboard_command": "pbcopy"}}, layer="project",
            answers={})
        self.assertEqual(new, {"clipboard": {"command": "pbcopy"}})
        flat = " ".join(out.split())
        self.assertIn("current pbcopy (read from this file's legacy "
                      "[probe] clipboard_command; the write moves it to "
                      "[clipboard] command)", flat)
        new, out = _walk_with_answers(
            {"probe": {"clipboard_command": ""}}, layer="project",
            answers={}, inherited={"clipboard": {"command": "wl-copy"}})
        self.assertEqual(new, {"clipboard": {"command": ""}},
                         msg="a legacy suppress moves as a suppress")
        self.assertIn("(unset — no clipboard copy)", out)
        self.assertIn("wl-copy  (from global; x suppresses)", out)
        new, out = _walk_with_answers(
            {"clipboard": {"command": "pbcopy"}}, layer="project", answers={})
        self.assertNotIn("legacy", out,
                         msg="a new-spelling file gets no aside")

    def test_both_spellings_show_the_new_one_and_drop_the_legacy(self) -> None:
        new, out = _walk_with_answers(
            {"probe": {"clipboard_command": "xclip"},
             "clipboard": {"command": "pbcopy"}}, layer="project",
            answers={})
        self.assertEqual(new, {"clipboard": {"command": "pbcopy"}})
        self.assertIn("current    pbcopy", out)
        self.assertNotIn("current    xclip", out)
        self.assertNotIn("read from this file's legacy", out,
                         msg="the current value is the new key's, so no "
                             "carry-over aside")
        flat = " ".join(out.split())
        self.assertIn("! this file sets both [clipboard] command (shown "
                      "here, and what bale uses) and the legacy [probe] "
                      "clipboard_command (ignored)", flat,
                      msg="a file that sets both is never silent about it")

    def test_project_walk_enter_on_fresh_repo_writes_nothing(self) -> None:
        new, out = _walk_with_answers({}, layer="project", answers={})
        self.assertNotIn("clipboard", new)
        self.assertNotIn("probe", new)
        self.assertIn("(unset — no clipboard copy)", out)

    def test_project_walk_dash_clears_the_key(self) -> None:
        for existing in ({"clipboard": {"command": "pbcopy"}},
                         {"probe": {"clipboard_command": "pbcopy"}}):
            with self.subTest(existing=existing):
                new, _out = _walk_with_answers(
                    existing, layer="project", answers={KEY: "-"})
                self.assertNotIn("clipboard", new)
                self.assertNotIn("probe", new)

    def test_unreadable_entry_is_refused_and_current_kept(self) -> None:
        for value, reason in UNREADABLE_COMMANDS[:2]:
            for existing in ({"clipboard": {"command": "pbcopy"}},
                             {"probe": {"clipboard_command": "pbcopy"}}):
                with self.subTest(value=value, existing=existing):
                    new, out = _walk_with_answers(
                        existing, layer="project", answers={KEY: value})
                    self.assertEqual(new.get("clipboard"),
                                     {"command": "pbcopy"},
                                     msg="current is kept — in the new "
                                         "spelling")
                    self.assertIn(reason, out)
                    self.assertIn("Keeping current", out)

    def test_help_states_the_per_machine_layering_and_the_reader(self) -> None:
        """The full description — where to set it, and what bale copies
        with it now that it does (session clipboard-paste-blocks: C's two
        future-tense phrases are present tense) — is one '?' away; the
        default view stays short."""
        _new, out = _walk_with_answers(
            {}, layer="project",
            answers={KEY: ["?", ""]})
        # The help is re-wrapped to the width, so match across line breaks.
        flat = " ".join(out.split())
        for phrase in ("Per-machine: set it once with `bale config init "
                       "--global`",
                       "bale copies every paste block it prints",
                       "through the installed bale (`bale clipboard`)",
                       "whether or not the request shipped a bale.toml",
                       "detection only suggests",
                       "Written as `command` under a `[clipboard]` header",
                       "`clipboard_command` under `[probe]`, is still read "
                       "as a legacy alias at both layers",
                       "When one file sets both spellings, [clipboard] "
                       "command wins"):
            self.assertIn(phrase, flat)
        for gone in ("until bale copies paste blocks itself",
                     "once it lands", "never the global file"):
            self.assertNotIn(gone, flat,
                             msg="the pre-session-D future tense is gone")
        _new, short = _walk_with_answers({}, layer="project", answers={})
        self.assertNotIn("bale copies every paste block",
                         " ".join(short.split()),
                         msg="the full description shows on demand only")
        heading = [ln for ln in short.splitlines() if "[clipboard]" in ln]
        self.assertEqual(len(heading), 1)
        self.assertNotIn("project layer only", heading[0])
        self.assertEqual([ln for ln in short.splitlines() if "[probe]" in ln],
                         [], msg="no [probe] heading is drawn any more")

    def test_global_walk_offers_sets_and_keeps_the_key(self) -> None:
        new, out = _walk_with_answers(
            {}, layer="global", answers={KEY: "pbcopy"})
        self.assertRegex(out, r"(?m)^\s*11/11  clipboard\.command\b")
        self.assertEqual(new.get("clipboard"), {"command": "pbcopy"})
        for existing in ({"clipboard": {"command": "wl-copy"}},
                         {"probe": {"clipboard_command": "wl-copy"}}):
            new, _out = _walk_with_answers(existing, layer="global",
                                           answers={})
            self.assertEqual(new, {"clipboard": {"command": "wl-copy"}})

    def test_project_walk_shows_the_inherited_value_and_x_suppresses(self) -> None:
        for inherited in ({"clipboard": {"command": "pbcopy"}},
                          {"probe": {"clipboard_command": "pbcopy"}},
                          {"probe": {"clipboard_command": "xclip"},
                           "clipboard": {"command": "pbcopy"}}):
            with self.subTest(inherited=inherited):
                new, out = _walk_with_answers({}, layer="project", answers={},
                                              inherited=inherited)
                self.assertEqual(new, {}, msg="Enter keeps inheriting")
                self.assertIn("pbcopy  (from global; x suppresses)", out)
                self.assertNotIn("xclip  (from global", out,
                                 msg="the global file's shadowed legacy "
                                     "value is not the inherited one")
                new, _out = _walk_with_answers(
                    {}, layer="project", inherited=inherited,
                    answers={KEY: "x"})
                self.assertEqual(new, {"clipboard": {"command": ""}})

    def test_a_number_picks_a_named_command(self) -> None:
        suggestions = bale_config.WizardSuggestions(alternatives={
            KEY: bale_config.clipboard_alternatives(
                platform="darwin", environ={}, which=lambda n: "/usr/bin/x",
                wsl=False)})
        new, out = _walk_with_answers(
            {}, layer="project", answers={KEY: "1"},
            suggestions=suggestions)
        self.assertEqual(new.get("clipboard"), {"command": "pbcopy"})
        self.assertIn("[1] pbcopy  (macOS, detected)", out)
        self.assertIn("[2] clip.exe  (Windows and WSL)", out)
        new, _out = _walk_with_answers(
            {}, layer="project", answers={KEY: "5"},
            suggestions=suggestions)
        self.assertEqual(new.get("clipboard"),
                         {"command": "xsel --clipboard --input"})


class WizardSpellingWarningTest(_HermeticConfigBase):
    """A file that spells the key triple-quoted: the wizard warns on the
    key's screen, Enter keeps the value, and the rewrite is readable."""

    @unittest.skipUnless(CRAFTER_PATH.is_file(),
                         "tools/craft_response.py not shipped in this sandbox")
    def suggest(self) -> "bale_config.WizardSuggestions":
        return bale_config.suggest_wizard_values(
            "project", bale_config.load_config(self.repo),
            config_path=self.repo / "bale.toml", environ={}, home=self.tmp,
            platform="linux", which=lambda n: None, wsl=False)

    def test_warns_and_the_rewrite_reads_back(self) -> None:
        for header, key, _dotted in SPELLINGS:
            with self.subTest(header=header):
                self.write_project(f"{header}\n{key} = '''pbcopy'''\n")
                existing = bale_config.load_config(self.repo)
                new, out = _walk_with_answers(existing, layer="project",
                                              answers={},
                                              suggestions=self.suggest())
                flat = " ".join(out.split())
                self.assertIn(f"! this file's {header} {key} is "
                              f"triple-quoted", flat)
                self.assertIn("rewrites it as a one-line [clipboard] "
                              "command string", flat)
                self.assertEqual(new, {"clipboard": {"command": "pbcopy"}})
                self.write_project(bale_config.render_bale_toml(new))
                crafter_cmd, note = load_crafter().read_clipboard_command(
                    self.repo)
                self.assertEqual(crafter_cmd, "pbcopy", msg=note)
                self.assertEqual(
                    bale_config.effective_clipboard_command(self.repo),
                    "pbcopy")

    def test_both_spellings_warn_and_name_the_winner(self) -> None:
        self.write_project('[probe]\nclipboard_command = "xclip"\n'
                           '[clipboard]\ncommand = "pbcopy"\n')
        warnings = self.suggest().warnings
        self.assertEqual(list(warnings), ["clipboard.command"])
        [text] = warnings["clipboard.command"]
        self.assertIn("sets both [clipboard] command (shown here, and what "
                      "bale uses) and the legacy [probe] clipboard_command "
                      "(ignored)", text)
        self.assertIn("keeps only [clipboard] command", text)

    def test_no_warning_for_a_readable_file(self) -> None:
        for header, key, _dotted in SPELLINGS:
            with self.subTest(header=header):
                self.write_project(f'{header}\n{key} = "pbcopy"\n')
                self.assertEqual(self.suggest().warnings, {})


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
        for body in ('[clipboard]\ncommand = "pbcopy"\n',
                     '[probe]\nclipboard_command = "pbcopy"\n'):
            with self.subTest(body=body):
                (self.repo / "bale.toml").write_text(body, encoding="utf-8")
                code, output = run_bale_pty(
                    self.install, ["config", "init"],
                    cwd=self.repo, env=self.env, answers="\n" * 40)
                self.assertEqual(code, 0, msg=output)
                self.assertRegex(output, r"\d+/\d+\s+clipboard\.command\b",
                                 msg="the project wizard walks the key — "
                                     "the discoverable-surface contract")
                self.assertNotRegex(output,
                                    r"\d+/\d+\s+probe\.clipboard_command",
                                    msg="the legacy spelling is not a screen")
                rendered = (self.repo / "bale.toml").read_text(
                    encoding="utf-8")
                self.assertIn("[clipboard]", rendered)
                self.assertIn('command = "pbcopy"', rendered,
                              msg="Enter-through re-runs preserve the set "
                                  "value — the renderer-preservation "
                                  "precedent, now in the new spelling")
                self.assertNotIn("[probe]", rendered)
                self.assertNotIn("clipboard_command", rendered)

    def test_global_wizard_walks_the_key(self) -> None:
        """Per-machine since session wizard-defaults: the global wizard
        offers the key with its named alternatives, and an Enter-through
        sets nothing."""
        code, output = run_bale_pty(
            self.install, ["config", "init", "--global"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("clipboard.command", output)
        self.assertIn("] xclip -selection clipboard  (X11", output)
        rendered = (self.install / "user" / "bale.toml").read_text(
            encoding="utf-8")
        self.assertNotIn("[clipboard]", rendered,
                         msg="an Enter-through writes nothing the "
                             "operator did not choose")
        self.assertNotIn("[probe]", rendered)

    @unittest.skipUnless(CRAFTER_PATH.is_file(),
                         "tools/craft_response.py not shipped in this sandbox")
    def test_crafter_still_reads_the_project_key_after_enter_through(self) -> None:
        """The session's back-compat constraint, kept across the rename:
        a project bale.toml that sets the key — in the legacy spelling
        here, as bale-src's own file does — is still read by the
        crafter's --probe reader after an Enter-through `bale config
        init` (which moves it to [clipboard] command) — with a different
        global value present, which must not leak into the project
        file."""
        user = self.install / "user"
        user.mkdir()
        (user / "bale.toml").write_text(
            "[probe]\nclipboard_command = \"xclip -selection clipboard\"\n",
            encoding="utf-8")
        (self.repo / "bale.toml").write_text(
            "[probe]\nclipboard_command = 'pbcopy'\n", encoding="utf-8")
        before, note = load_crafter().read_clipboard_command(self.repo)
        self.assertEqual(before, "pbcopy", msg=note)
        code, output = run_bale_pty(
            self.install, ["config", "init"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        crafter_cmd, note = load_crafter().read_clipboard_command(self.repo)
        self.assertEqual(crafter_cmd, "pbcopy", msg=note)
        self.assertIn("xclip -selection clipboard  (from global; x "
                      "suppresses)", output,
                      msg="the inherited global value is on screen")
        flat = " ".join(output.split())
        self.assertIn("~ probe.clipboard_command → clipboard.command = "
                      "\"pbcopy\" (the legacy spelling moves; same value)",
                      flat, msg="the review names the move, not a drop")
        self.assertNotIn("dropped", flat)
        self.assertIn("read from this file's legacy [probe] "
                      "clipboard_command; the write moves it to [clipboard] "
                      "command", flat)
        rendered = (self.repo / "bale.toml").read_text(encoding="utf-8")
        self.assertIn('[clipboard]\ncommand = "pbcopy"', rendered)
        self.assertNotIn("xclip", rendered)
        self.assertNotIn("[probe]", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
