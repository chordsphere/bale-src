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
  project bale.toml that sets it is still read by the crafter after an
  Enter-through re-run (the session's back-compat constraint).

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
import bale_wizard  # noqa: E402  (the wizard presentation layer)
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

    def test_global_probe_section_is_inherited(self) -> None:
        """Per-machine since session wizard-defaults (ruling 1): a
        global value applies wherever the project does not set the key."""
        self.global_toml.parent.mkdir(parents=True)
        self.global_toml.write_text(
            '[probe]\nclipboard_command = "pbcopy"\n', encoding="utf-8")
        cfg = bale_config.merged_config(self.repo)
        self.assertEqual(cfg.get("probe"), {"clipboard_command": "pbcopy"})
        self.assertEqual(bale_config.get_probe_clipboard_command(cfg),
                         "pbcopy")

    def test_project_empty_string_suppresses_the_global(self) -> None:
        self.global_toml.parent.mkdir(parents=True)
        self.global_toml.write_text(
            '[probe]\nclipboard_command = "pbcopy"\n', encoding="utf-8")
        self.write_project('[probe]\nclipboard_command = ""\n')
        self.assertIsNone(self.accessor())

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

    def test_content_problems_stay_fatal_at_either_layer(self) -> None:
        self.write_global('[probe]\nclipboard_command = "a\\\\b"\n')
        with self.assertRaises(_FailRaises.Fatal) as ctx:
            bale_config.effective_clipboard_command(self.repo)
        self.assertIn("backslash", str(ctx.exception))

    def test_triple_quoted_is_refused_at_both_layers(self) -> None:
        for line in ("clipboard_command = '''pbcopy'''",
                     'clipboard_command = """pbcopy"""',
                     'clipboard_command = """\npbcopy"""'):
            for layer in ("project", "global"):
                with self.subTest(line=line, layer=layer):
                    (self.repo / "bale.toml").unlink(missing_ok=True)
                    self.global_toml.unlink(missing_ok=True)
                    write = (self.write_project if layer == "project"
                             else self.write_global)
                    write(f"[probe]\n{line}\n")
                    with self.assertRaises(_FailRaises.Fatal) as ctx:
                        bale_config.effective_clipboard_command(self.repo)
                    message = str(ctx.exception)
                    self.assertIn("is triple-quoted", message)
                    self.assertIn("craft_response.py", message)
                    rerun = ("bale config init --global" if layer == "global"
                             else "bale config init`")
                    self.assertIn(rerun, message)

    def test_other_unseen_spellings_are_refused(self) -> None:
        for body in ('probe.clipboard_command = "pbcopy"\n',
                     'probe = { clipboard_command = "pbcopy" }\n',
                     '[probe] # mine\nclipboard_command = "pbcopy"\n'):
            with self.subTest(body=body):
                self.write_project(body)
                self.assertEqual(
                    bale_config.get_probe_clipboard_command(
                        bale_config.merged_config(self.repo)), "pbcopy",
                    msg="bale's parser reads it")
                with self.assertRaises(_FailRaises.Fatal) as ctx:
                    bale_config.effective_clipboard_command(self.repo)
                self.assertIn("[probe] header", str(ctx.exception))

    def test_readable_spellings_pass(self) -> None:
        for body in ('[probe]\nclipboard_command = "pbcopy"\n',
                     "[probe]\nclipboard_command = 'pbcopy'  # mine\n",
                     '[ probe ]\n  clipboard_command="pbcopy"\n',
                     '[hooks]\n[probe]\nclipboard_command = """"""\n'):
            with self.subTest(body=body):
                self.write_project(body)
                expected = None if '""""""' in body else "pbcopy"
                self.assertEqual(
                    bale_config.effective_clipboard_command(self.repo),
                    expected)

    def test_spelling_problem_reads_the_file(self) -> None:
        self.write_project('[probe]\nclipboard_command = "pbcopy"\n')
        self.assertIsNone(bale_config.clipboard_command_spelling_problem(
            self.repo / "bale.toml"))
        self.assertIn("could not be re-read",
                      bale_config.clipboard_command_spelling_problem(
                          self.repo / "missing.toml"))


@unittest.skipUnless(CRAFTER_PATH.is_file(),
                     "tools/craft_response.py not shipped in this sandbox")
class SpellingTwinTest(_HermeticConfigBase):
    """bin/ restates the crafter's one-line scan (it never imports
    tools/); this pins the twin against the original on one corpus."""

    LINES = (
        'clipboard_command = "pbcopy"',
        "clipboard_command = 'pbcopy'",
        'clipboard_command = "  xclip -selection clipboard  "  # c',
        "clipboard_command = '''pbcopy'''",
        'clipboard_command = """pbcopy"""',
        'clipboard_command = "a\\\\b"',
        "clipboard_command = 'sh -c \"x\"'",
        'clipboard_command = "pbcopy" trailing',
        'clipboard_command = ""',
        "clipboard_command = pbcopy",
        'clipboard_command = "unterminated',
        'clipboard_command = "tab\there"',
        'other = "pbcopy"',
    )

    def test_twin_agrees_with_the_crafter_on_every_line(self) -> None:
        crafter = load_crafter()
        for line in self.LINES:
            for header in ("[probe]", "[hooks]"):
                text = f"{header}\n{line}\n"
                with self.subTest(text=text):
                    self.write_project(text)
                    value, status, _rel = crafter.scan_bale_toml_key(
                        "probe", "clipboard_command", self.repo)
                    twin_status, twin_value, _raw = \
                        bale_config._scan_clipboard_line(text)
                    self.assertEqual((twin_status, twin_value),
                                     (status, value))


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


class WizardWalkUnitTest(unittest.TestCase):
    """walk_configurables' [probe] block, in-process."""

    def test_project_walk_sets_the_key(self) -> None:
        new, out = _walk_with_answers(
            {}, layer="project",
            answers={"probe.clipboard_command": "xclip -selection clipboard"})
        self.assertEqual(new.get("probe"),
                         {"clipboard_command": "xclip -selection clipboard"})
        self.assertRegex(out, r"(?m)^\s*\d+/\d+  probe\.clipboard_command\b",
                         msg="the item screen names its dotted key")

    def test_project_walk_enter_keeps_the_existing_value(self) -> None:
        new, _out = _walk_with_answers(
            {"probe": {"clipboard_command": "pbcopy"}}, layer="project",
            answers={})
        self.assertEqual(new.get("probe"), {"clipboard_command": "pbcopy"})

    def test_project_walk_enter_on_fresh_repo_writes_nothing(self) -> None:
        new, out = _walk_with_answers({}, layer="project", answers={})
        self.assertNotIn("probe", new)
        self.assertIn("(unset — no clipboard copy)", out)

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

    def test_help_states_the_per_machine_layering_and_the_reader(self) -> None:
        """The full description — where to set it, and which reader sees
        which file today — is one '?' away; the default view stays short."""
        _new, out = _walk_with_answers(
            {}, layer="project",
            answers={"probe.clipboard_command": ["?", ""]})
        # The help is re-wrapped to the width, so match across line breaks.
        flat = " ".join(out.split())
        for phrase in ("Per-machine: set it once with `bale config init "
                       "--global`", "never the global file",
                       "detection only suggests"):
            self.assertIn(phrase, flat)
        _new, short = _walk_with_answers({}, layer="project", answers={})
        self.assertNotIn("never the global file", " ".join(short.split()),
                         msg="the full description shows on demand only")
        heading = [ln for ln in short.splitlines() if "[probe]" in ln]
        self.assertEqual(len(heading), 1)
        self.assertNotIn("project layer only", heading[0])

    def test_global_walk_offers_sets_and_keeps_the_key(self) -> None:
        new, out = _walk_with_answers(
            {}, layer="global", answers={"probe.clipboard_command": "pbcopy"})
        self.assertRegex(out, r"(?m)^\s*11/11  probe\.clipboard_command\b")
        self.assertEqual(new.get("probe"), {"clipboard_command": "pbcopy"})
        new, _out = _walk_with_answers(
            {"probe": {"clipboard_command": "wl-copy"}}, layer="global",
            answers={})
        self.assertEqual(new.get("probe"), {"clipboard_command": "wl-copy"})

    def test_project_walk_shows_the_inherited_value_and_x_suppresses(self) -> None:
        inherited = {"probe": {"clipboard_command": "pbcopy"}}
        new, out = _walk_with_answers({}, layer="project", answers={},
                                      inherited=inherited)
        self.assertNotIn("probe", new, msg="Enter keeps inheriting")
        self.assertIn("pbcopy  (from global; x suppresses)", out)
        new, _out = _walk_with_answers(
            {}, layer="project", inherited=inherited,
            answers={"probe.clipboard_command": "x"})
        self.assertEqual(new.get("probe"), {"clipboard_command": ""})

    def test_a_number_picks_a_named_command(self) -> None:
        suggestions = bale_config.WizardSuggestions(alternatives={
            "probe.clipboard_command": bale_config.clipboard_alternatives(
                platform="darwin", environ={}, which=lambda n: "/usr/bin/x",
                wsl=False)})
        new, out = _walk_with_answers(
            {}, layer="project", answers={"probe.clipboard_command": "1"},
            suggestions=suggestions)
        self.assertEqual(new.get("probe"), {"clipboard_command": "pbcopy"})
        self.assertIn("[1] pbcopy  (macOS, detected)", out)
        self.assertIn("[2] clip.exe  (Windows and WSL)", out)
        new, _out = _walk_with_answers(
            {}, layer="project", answers={"probe.clipboard_command": "5"},
            suggestions=suggestions)
        self.assertEqual(new.get("probe"),
                         {"clipboard_command": "xsel --clipboard --input"})


class WizardSpellingWarningTest(_HermeticConfigBase):
    """A file that spells the key triple-quoted: the wizard warns on the
    key's screen, Enter keeps the value, and the rewrite is readable."""

    @unittest.skipUnless(CRAFTER_PATH.is_file(),
                         "tools/craft_response.py not shipped in this sandbox")
    def test_warns_and_the_rewrite_reads_back(self) -> None:
        self.write_project("[probe]\nclipboard_command = '''pbcopy'''\n")
        existing = bale_config.load_config(self.repo)
        suggestions = bale_config.suggest_wizard_values(
            "project", existing, config_path=self.repo / "bale.toml",
            environ={}, home=self.tmp, platform="linux",
            which=lambda n: None, wsl=False)
        new, out = _walk_with_answers(existing, layer="project", answers={},
                                      suggestions=suggestions)
        flat = " ".join(out.split())
        self.assertIn("! this file's clipboard_command is triple-quoted",
                      flat)
        self.assertEqual(new.get("probe"), {"clipboard_command": "pbcopy"})
        self.write_project(bale_config.render_bale_toml(new))
        crafter_cmd, note = load_crafter().read_clipboard_command(self.repo)
        self.assertEqual(crafter_cmd, "pbcopy", msg=note)
        self.assertEqual(bale_config.effective_clipboard_command(self.repo),
                         "pbcopy")

    def test_no_warning_for_a_readable_file(self) -> None:
        self.write_project('[probe]\nclipboard_command = "pbcopy"\n')
        suggestions = bale_config.suggest_wizard_values(
            "project", bale_config.load_config(self.repo),
            config_path=self.repo / "bale.toml", environ={}, home=self.tmp,
            platform="linux", which=lambda n: None, wsl=False)
        self.assertEqual(suggestions.warnings, {})


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

    def test_global_wizard_walks_the_key(self) -> None:
        """Per-machine since session wizard-defaults: the global wizard
        offers the key with its named alternatives, and an Enter-through
        sets nothing."""
        code, output = run_bale_pty(
            self.install, ["config", "init", "--global"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("probe.clipboard_command", output)
        self.assertIn("] xclip -selection clipboard  (X11", output)
        rendered = (self.install / "user" / "bale.toml").read_text(
            encoding="utf-8")
        self.assertNotIn("[probe]", rendered,
                         msg="an Enter-through writes nothing the "
                             "operator did not choose")

    @unittest.skipUnless(CRAFTER_PATH.is_file(),
                         "tools/craft_response.py not shipped in this sandbox")
    def test_crafter_still_reads_the_project_key_after_enter_through(self) -> None:
        """The session's back-compat constraint: a project bale.toml that
        sets [probe] clipboard_command is still read by the crafter's
        --probe reader after an Enter-through `bale config init` — with
        a different global value present, which must not leak into the
        project file."""
        user = self.install / "user"
        user.mkdir()
        (user / "bale.toml").write_text(
            "[probe]\nclipboard_command = \"xclip -selection clipboard\"\n",
            encoding="utf-8")
        (self.repo / "bale.toml").write_text(
            "[probe]\nclipboard_command = 'pbcopy'\n", encoding="utf-8")
        code, output = run_bale_pty(
            self.install, ["config", "init"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        crafter_cmd, note = load_crafter().read_clipboard_command(self.repo)
        self.assertEqual(crafter_cmd, "pbcopy", msg=note)
        self.assertIn("xclip -selection clipboard  (from global; x "
                      "suppresses)", output,
                      msg="the inherited global value is on screen")
        rendered = (self.repo / "bale.toml").read_text(encoding="utf-8")
        self.assertIn('clipboard_command = "pbcopy"', rendered)
        self.assertNotIn("xclip", rendered)


if __name__ == "__main__":
    unittest.main(verbosity=2)
