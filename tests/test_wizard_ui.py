#!/usr/bin/env python3
"""The shared wizard presentation layer and `bale config init` on it.

Session config-wizard-ui moved `bale config init` onto a shared display
layer (bin/bale_wizard.py) without changing what it writes. This suite
pins both halves of that sentence:

- **The layer** (no subprocess): the color policy (TTY only, never under
  NO_COLOR, never with TERM unset or dumb), the 80-column wrap with its
  one exception (a line naming an absolute path is never broken), the
  item header's exported pattern, the '?' help loop, the confirm gate's
  Enter / EOF / ^C outcomes, and Walk's derived positions and section
  headings.
- **The walk order**: WIZARD_WALK_ORDER_* covers exactly the declared
  configurable tuples, and an in-process walk visits exactly that order
  at each layer — so "3/19" cannot drift from the keys walked.
- **No semantic change**: a frozen table of answers → resulting config
  (Enter keeps, '-' clears, 'x' suppresses only with an inherited value,
  bool spellings, list parsing, EOF / ^C keep, the three
  reject-with-hint checks), each also run with a '?' typed first, which
  must change nothing. (The session verified the table's expectations
  differentially against the pre-move walk over thousands of randomized
  configs and answer sets; the table is that evidence, frozen.)
- **The review**: config_changes rows, and review_and_write_config's
  gate — Enter writes, EOF writes, n or ^C leaves the file, and a file
  already matching is not rewritten (and nothing is asked).
- **.baleignore**: the review and its gate, byte-for-byte outcomes.
- **End to end under a pty**: a real `bale config init` (project and
  --global) — every key's dotted name and n/N on its screen, the grammar
  shown once, every line within 80 columns except absolute-path lines,
  the prompt count within the 40 newlines the pty suites send, color
  under a TERM and never under NO_COLOR or without a TERM, and a piped
  run that writes the file plain.

Hermetic per ADR-0005: temp repos, temp installs, temp HOME; bin/ modules
are loaded by path with the harness loader, and bale_config's lazy
`from __main__ import log` gets a recording stand-in.

Run:  python3 -m unittest tests.test_wizard_ui -v
"""

from __future__ import annotations

import builtins
import contextlib
import copy
import io
import re
import sys
import tempfile
import unittest
from pathlib import Path

from harness import (
    _load_module,
    bale_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_bale_pty,
)

bale_wizard = _load_module("bale_wizard")
bale_config = _load_module("bale_config")

ESC = "\x1b["
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
# Independent of bale_wizard.names_absolute_path on purpose: the width
# exemption is judged here, not by the code under test.
ABS_PATH_RE = re.compile(r"""(?:^|[\s(\[{'"=:])/[^\s/]""")
# Where a prompt ends. Under a pty the answers are typed ahead, so a
# prompt's line is never terminated by the user's Enter; the next output
# lands on the same captured line. Splitting here restores the lines a
# terminal shows.
PROMPT_END_RE = re.compile(r"(?<=> )|(?<=\[Y/n\] )")

PROJECT_KEYS = bale_config.wizard_walk_order("project")
GLOBAL_KEYS = bale_config.wizard_walk_order("global")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

class _Tty(io.StringIO):
    """A StringIO that claims to be a terminal."""

    def isatty(self) -> bool:
        return True


class _MainStandIns:
    """Install recording stand-ins for bin/bale's `log` on __main__.

    bale_config imports log lazily from __main__ (production: bin/bale).
    """

    def __enter__(self):
        self._main = sys.modules["__main__"]
        self._had = hasattr(self._main, "log")
        self._saved = getattr(self._main, "log", None)
        self.logged: list[str] = []
        self._main.log = lambda msg, **_kw: self.logged.append(msg)
        return self

    def __exit__(self, *exc):
        if self._had:
            self._main.log = self._saved
        else:
            delattr(self._main, "log")
        return False


EOF_ANSWER = object()
INTERRUPT = object()


def _answer(value):
    if value is EOF_ANSWER:
        raise EOFError
    if value is INTERRUPT:
        raise KeyboardInterrupt
    return value


def walk_with_answers(existing: dict, *, layer: str, answers: dict,
                      inherited=None, suggestions=None):
    """Drive walk_configurables in-process, answering by item key.

    The item an input() belongs to is the most recent line matching
    bale_wizard.ITEM_HEADER_RE. An answer may be a list (consumed one
    entry per input() call — '?' then the real answer), EOF_ANSWER, or
    INTERRUPT. Returns (new_cfg, output, prompts) where prompts are the
    (key, prompt text) pairs input() was called with. `suggestions`
    passes through (None: detect from the machine running the test).
    """
    buffer = io.StringIO()
    pending = {k: (list(v) if isinstance(v, list) else [v])
               for k, v in answers.items()}
    prompts: list[tuple[str, str]] = []

    def fake_input(prompt: str = "") -> str:
        label = None
        for line in reversed(buffer.getvalue().splitlines()):
            match = bale_wizard.ITEM_HEADER_RE.match(line)
            if match:
                label = match.group(3)
                break
        prompts.append((label, prompt))
        queue = pending.get(label) or []
        return _answer(queue.pop(0) if queue else "")

    saved = builtins.input
    builtins.input = fake_input
    try:
        with contextlib.redirect_stdout(buffer):
            new = bale_config.walk_configurables(
                copy.deepcopy(existing), layer=layer,
                inherited=copy.deepcopy(inherited),
                suggestions=suggestions)
    finally:
        builtins.input = saved
    return new, buffer.getvalue(), prompts


def run_with_inputs(func, inputs, *args, **kwargs):
    """Call func with input() answering from a sequence; return
    (result, output, prompts). An exhausted sequence answers Enter."""
    buffer = io.StringIO()
    queue = list(inputs)
    prompts: list[str] = []

    def fake_input(prompt: str = "") -> str:
        prompts.append(prompt)
        return _answer(queue.pop(0) if queue else "")

    saved = builtins.input
    builtins.input = fake_input
    try:
        with contextlib.redirect_stdout(buffer):
            result = func(*args, **kwargs)
    finally:
        builtins.input = saved
    return result, buffer.getvalue(), prompts


def terminal_lines(output: str) -> list[str]:
    """Captured pty output as the lines a terminal would show."""
    clean = ANSI_RE.sub("", output.replace("\r", ""))
    lines: list[str] = []
    for raw in clean.split("\n"):
        lines.extend(PROMPT_END_RE.split(raw))
    return lines


def overwide(output: str) -> list[str]:
    """Lines over 80 columns that do not name an absolute path."""
    return [ln for ln in terminal_lines(output)
            if len(ln) > bale_wizard.WIDTH and not ABS_PATH_RE.search(ln)]


def item_headers(output: str) -> list[tuple[int, int, str]]:
    """(position, total, key) for every item header in the output."""
    found = []
    for line in ANSI_RE.sub("", output).replace("\r", "").split("\n"):
        match = bale_wizard.ITEM_HEADER_RE.match(line)
        if match:
            found.append((int(match.group(1)), int(match.group(2)),
                          match.group(3)))
    return found


# ---------------------------------------------------------------------------
# The layer
# ---------------------------------------------------------------------------

class ColorPolicyTest(unittest.TestCase):
    """Color only on a TTY, never under NO_COLOR, never without a TERM."""

    def test_tty_with_a_terminal_type_is_colored(self) -> None:
        self.assertTrue(bale_wizard.color_enabled(
            _Tty(), {"TERM": "xterm-256color"}))

    def test_every_disqualifier_turns_color_off(self) -> None:
        cases = {
            "piped": (io.StringIO(), {"TERM": "xterm"}),
            "NO_COLOR=1": (_Tty(), {"TERM": "xterm", "NO_COLOR": "1"}),
            "NO_COLOR empty": (_Tty(), {"TERM": "xterm", "NO_COLOR": ""}),
            "TERM unset": (_Tty(), {}),
            "TERM=dumb": (_Tty(), {"TERM": "dumb"}),
            "no isatty": (object(), {"TERM": "xterm"}),
        }
        for name, (stream, env) in cases.items():
            with self.subTest(case=name):
                self.assertFalse(bale_wizard.color_enabled(stream, env))

    def test_redirected_output_is_plain(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            ui = bale_wizard.WizardUI()
            ui.heading("[apply]", "note")
            ui.item(3, 19, "apply.search_paths", "paths")
            ui.warn("nope")
        self.assertNotIn(ESC, buffer.getvalue())

    def test_forced_color_wraps_whole_fields(self) -> None:
        """Styling never splits a field, so substring checks hold."""
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            ui = bale_wizard.WizardUI(color=True)
            ui.item(14, 19, "sandbox.enabled", "true/false")
            ui.summary("NEVER silent: each such run is FORCE-logged.")
        out = buffer.getvalue()
        self.assertIn(ESC, out)
        self.assertIn("14/19  sandbox.enabled", out)
        self.assertIn("NEVER silent", out)
        self.assertEqual(
            item_headers(out), [(14, 19, "sandbox.enabled")],
            msg="the header still matches ITEM_HEADER_RE once de-styled")


class WrapTest(unittest.TestCase):

    def test_lines_fit_the_width(self) -> None:
        text = ("word " * 60).strip()
        for line in bale_wizard.wrap(text, indent=9):
            self.assertLessEqual(len(line), bale_wizard.WIDTH)

    def test_long_relative_token_is_broken_to_fit(self) -> None:
        lines = bale_wizard.wrap("x" * 200, indent=4)
        self.assertTrue(all(len(ln) <= bale_wizard.WIDTH for ln in lines))
        self.assertEqual("".join(ln.strip() for ln in lines), "x" * 200)

    def test_absolute_path_is_never_broken(self) -> None:
        path = "/opt/" + "deep/" * 30 + "inbox"
        lines = bale_wizard.wrap(f"file: {path}", indent=2)
        self.assertTrue(any(path in ln for ln in lines),
                        msg="the path survives whole on one line")

    def test_names_absolute_path(self) -> None:
        yes = ("/usr/bin", "file: /tmp/x", "(/x/y)", "C:\\Users", "a=/b")
        no = ("a / b", "<install>/user/", "~/Downloads", "src/legacy/",
              "pbcopy")
        for text in yes:
            with self.subTest(text=text):
                self.assertTrue(bale_wizard.names_absolute_path(text))
        for text in no:
            with self.subTest(text=text):
                self.assertFalse(bale_wizard.names_absolute_path(text))

    def test_clip(self) -> None:
        self.assertEqual(bale_wizard.clip("short"), "short")
        clipped = bale_wizard.clip("y" * 100, 20)
        self.assertEqual(len(clipped), 20)
        self.assertTrue(clipped.endswith("\u2026"))


class PrimitivesTest(unittest.TestCase):

    def capture(self, fn):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            fn(bale_wizard.WizardUI())
        return buffer.getvalue()

    def test_item_header_matches_the_exported_pattern(self) -> None:
        out = self.capture(lambda ui: ui.item(3, 19, "apply.search_paths",
                                              "paths, colon-separated"))
        self.assertEqual(item_headers(out), [(3, 19, "apply.search_paths")])
        self.assertTrue(all(len(ln) <= 80 for ln in out.splitlines()))

    def test_long_key_moves_its_kind_to_the_next_line(self) -> None:
        key = "section." + "k" * 70
        out = self.capture(lambda ui: ui.item(1, 2, key, "true/false"))
        self.assertEqual(item_headers(out), [(1, 2, key)])
        self.assertIn("true/false", out.splitlines()[1])

    def test_ask_item_shows_help_on_question_mark_and_asks_again(self) -> None:
        shown = []
        ui = bale_wizard.WizardUI()
        answer, _out, prompts = run_with_inputs(
            ui.ask_item, ["?", "?", "value"], "Enter keeps current",
            show_help=lambda: shown.append(1))
        self.assertEqual(answer, "value")
        self.assertEqual(len(shown), 2)
        self.assertEqual(len(prompts), 3)
        self.assertIn("Enter keeps current", prompts[0],
                      msg="the prompt states the Enter action")
        self.assertIn("? help", prompts[0])

    def test_ask_item_eof_and_interrupt_are_none(self) -> None:
        ui = bale_wizard.WizardUI()
        for gesture in (EOF_ANSWER, INTERRUPT):
            with self.subTest(gesture=gesture):
                answer, _out, _p = run_with_inputs(
                    ui.ask_item, [gesture], "Enter", show_help=lambda: None)
                self.assertIsNone(answer)

    def test_confirm_outcomes(self) -> None:
        ui = bale_wizard.WizardUI()
        cases = [
            ([""], True), (["y"], True), (["YES"], True),
            (["n"], False), (["no"], False),
            ([EOF_ANSWER], True), ([INTERRUPT], False),
            (["maybe", ""], True), (["maybe", "n"], False),
        ]
        for inputs, expected in cases:
            with self.subTest(inputs=inputs):
                result, _out, _p = run_with_inputs(
                    ui.confirm, inputs, "Write it?", default=True, eof=True,
                    interrupt=False)
                self.assertIs(result, expected)

    def test_walk_derives_positions_and_headings(self) -> None:
        def run(ui):
            walk = bale_wizard.Walk(ui, ("a.x", "a.y", "b.z"),
                                    {"a": "first", "b": "second"})
            for key in ("a.x", "a.y", "b.z"):
                walk.begin(key, kind="k", summary="s")
        out = self.capture(run)
        self.assertEqual(item_headers(out),
                         [(1, 3, "a.x"), (2, 3, "a.y"), (3, 3, "b.z")])
        self.assertEqual(out.count("[a]  first"), 1)
        self.assertEqual(out.count("[b]  second"), 1)
        self.assertLess(out.index("[a]"), out.index("1/3"))
        self.assertLess(out.index("2/3"), out.index("[b]"))

    def test_walk_refuses_unknown_and_duplicate_keys(self) -> None:
        ui = bale_wizard.WizardUI()
        with self.assertRaises(ValueError):
            bale_wizard.Walk(ui, ("a.x", "a.x"))
        walk = bale_wizard.Walk(ui, ("a.x",))
        with contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(ValueError):
                walk.begin("a.nope", kind="", summary="")

    def test_module_is_a_leaf(self) -> None:
        """Importable from any sibling (bale_pack next) without cycles:
        it imports nothing from bin/."""
        src = Path(bale_wizard.__file__).read_text(encoding="utf-8")
        imports = re.findall(r"(?m)^\s*(?:from\s+(\S+)\s+import|import\s+(\S+))",
                             src)
        names = {a or b for a, b in imports}
        for name in names:
            with self.subTest(name=name):
                self.assertNotIn(name.split(".")[0],
                                 ("__main__", "bale_config", "bale_pack",
                                  "bale_report", "bale_apply"))
                self.assertFalse(name.startswith("bale"),
                                 msg=f"{name}: the layer must stay a leaf")


# ---------------------------------------------------------------------------
# The walk order
# ---------------------------------------------------------------------------

class WalkOrderTest(unittest.TestCase):

    def test_order_covers_exactly_the_declared_configurables(self) -> None:
        declared = (
            [f"hooks.{k}" for k in bale_config.HOOK_NAMES]
            + [f"apply.{k}" for k in bale_config.APPLY_VALUES]
            + [f"staging.{k}" for k in bale_config.STAGING_VALUES]
            + [f"identity.{k}" for k in bale_config.IDENTITY_VALUES]
            # [probe] is a both-layer section since session
            # wizard-defaults (the clipboard command is per-machine), so
            # it closes the both-layer run, before the project-only ones.
            + [f"probe.{k}" for k in bale_config.PROBE_VALUES]
            + [f"validation.{k}" for k in bale_config.VALIDATION_VALUES]
            + [f"sandbox.{k}" for k in bale_config.SANDBOX_VALUES]
            + [f"pack.{k}" for k in bale_config.PACK_VALUES]
            + [f"layout.{k}" for k in bale_config.LAYOUT_VALUES]
        )
        self.assertEqual(list(PROJECT_KEYS), declared)
        self.assertEqual(len(PROJECT_KEYS), 19)
        self.assertEqual(len(GLOBAL_KEYS), 11)
        self.assertEqual(PROJECT_KEYS[:11], GLOBAL_KEYS)

    def test_unknown_layer_refuses(self) -> None:
        with self.assertRaises(ValueError):
            bale_config.wizard_walk_order("team")

    def test_walk_visits_exactly_the_order_at_each_layer(self) -> None:
        for layer, keys in (("project", PROJECT_KEYS),
                            ("global", GLOBAL_KEYS)):
            with self.subTest(layer=layer):
                _new, out, prompts = walk_with_answers(
                    {}, layer=layer, answers={})
                n = len(keys)
                self.assertEqual(
                    item_headers(out),
                    [(i + 1, n, key) for i, key in enumerate(keys)])
                self.assertEqual([k for k, _p in prompts], list(keys),
                                 msg="one prompt per key, Enter-through")

    def test_one_heading_per_section_in_walk_order(self) -> None:
        _new, out, _p = walk_with_answers({}, layer="project", answers={})
        sections = []
        for key in PROJECT_KEYS:
            section = key.split(".")[0]
            if section not in sections:
                sections.append(section)
        positions = []
        for section in sections:
            heading = re.findall(rf"(?m)^\S+ \[{section}\]  .*$", out)
            self.assertEqual(len(heading), 1, msg=section)
            positions.append(out.index(heading[0]))
            only = section in ("validation", "sandbox", "pack", "layout")
            self.assertEqual("project layer only" in heading[0], only,
                             msg=heading[0])
        self.assertEqual(positions, sorted(positions))

    def test_global_walk_draws_no_project_only_heading(self) -> None:
        _new, out, _p = walk_with_answers({}, layer="global", answers={})
        self.assertNotIn("project layer only", out)


# ---------------------------------------------------------------------------
# The screens
# ---------------------------------------------------------------------------

class ScreenTest(unittest.TestCase):

    def test_default_view_drops_the_repeated_instruction_lines(self) -> None:
        _new, out, _p = walk_with_answers({}, layer="project", answers={})
        for retired in ("Enter to keep. Type", "current at this layer",
                        "Type 'x' to suppress", "No 'x' sigil"):
            self.assertNotIn(retired, out)
        self.assertEqual(out.count("current "), len(PROJECT_KEYS))
        self.assertEqual(out.count("effective "), len(PROJECT_KEYS))

    def test_every_line_fits_80_columns_in_process(self) -> None:
        inherited = {"hooks": {"post_apply_pass": "scripts/reinstall.sh"},
                     "apply": {"search_paths": ["~/Downloads", "inbox"],
                               "no_interact": True},
                     "identity": {"packer": "alice"}}
        answers = {key: ["?", ""] for key in PROJECT_KEYS}
        _new, out, _p = walk_with_answers(
            {"probe": {"clipboard_command": "pbcopy"}}, layer="project",
            answers=answers, inherited=inherited)
        self.assertEqual(overwide(out), [])

    def test_prompt_states_the_enter_action(self) -> None:
        inherited = {"identity": {"packer": "alice"},
                     "apply": {"no_interact": True}}
        existing = {"hooks": {"post_pack": "", "post_apply_pass": "x.sh"},
                    "apply": {"search_paths": []}}
        _new, _out, prompts = walk_with_answers(
            existing, layer="project", answers={}, inherited=inherited)
        by_key = dict(prompts)
        self.assertIn("Enter keeps it suppressed", by_key["hooks.post_pack"])
        self.assertIn("Enter keeps current", by_key["hooks.post_apply_pass"])
        self.assertIn("Enter keeps it suppressed",
                      by_key["apply.search_paths"])
        self.assertIn("Enter keeps inheriting", by_key["identity.packer"])
        self.assertIn("Enter keeps inheriting", by_key["apply.no_interact"])
        self.assertIn("Enter leaves it unset", by_key["apply.archive_dir"])

    def test_loudness_guarantee_reads_whole_in_the_default_view(self) -> None:
        """sandbox.enabled's summary keeps "NEVER silent" on one line
        (test_sandbox_wrapper asserts the phrase through a real pty)."""
        _new, out, _p = walk_with_answers({}, layer="project", answers={})
        self.assertIn("NEVER silent", out)

    def test_inherited_row_only_when_inherited(self) -> None:
        _new, out, _p = walk_with_answers(
            {}, layer="project", answers={},
            inherited={"identity": {"packer": "alice"}})
        self.assertEqual(out.count("inherited "), 1)
        self.assertIn("alice  (from global; x suppresses)", out)
        _new, out, _p = walk_with_answers({}, layer="global", answers={})
        self.assertNotIn("inherited ", out)

    def test_help_is_one_question_mark_away(self) -> None:
        _new, out, _p = walk_with_answers(
            {}, layer="project", answers={"apply.sweep": ["?", ""]})
        flat = " ".join(out.split())
        self.assertIn("never a directory glob, never `git add -A`", flat,
                      msg="the full description, re-wrapped")
        self.assertIn("Answers: Enter keeps", flat)
        _new, short, _p = walk_with_answers({}, layer="project", answers={})
        self.assertNotIn("never a directory glob", " ".join(short.split()))

    def test_grammar_is_explained_once(self) -> None:
        for layer in ("project", "global"):
            with self.subTest(layer=layer):
                buffer = io.StringIO()
                with contextlib.redirect_stdout(buffer):
                    bale_config.wizard_grammar(bale_wizard.WizardUI(),
                                               layer=layer)
                out = buffer.getvalue()
                self.assertIn("How to answer", out)
                for gesture in ("Enter", "a value", "-", "?"):
                    self.assertRegex(out, rf"(?m)^\s+{re.escape(gesture)}\s")
                has_x = re.search(r"(?m)^\s+x\s", out) is not None
                self.assertEqual(has_x, layer == "project",
                                 msg="x is offered only where a value can "
                                     "be inherited")
                self.assertEqual(overwide(out), [])


# ---------------------------------------------------------------------------
# No semantic change: the frozen answer table
# ---------------------------------------------------------------------------

# (name, layer, existing, inherited, answers, expected new config). Each
# row's expectation is what the pre-move walk returned for the same input
# (checked differentially when the move landed).
SEMANTICS = [
    ("enter keeps every value", "project",
     {"hooks": {"post_pack": "a.sh"}, "apply": {"search_paths": ["d"],
      "sweep": True}, "identity": {"packer": "bob"}},
     None, {},
     {"hooks": {"post_pack": "a.sh"}, "apply": {"search_paths": ["d"],
      "sweep": True}, "identity": {"packer": "bob"}}),
    ("enter keeps the suppress forms", "project",
     {"hooks": {"post_pack": ""}, "apply": {"search_paths": []}}, None, {},
     {"hooks": {"post_pack": ""}, "apply": {"search_paths": []}}),
    ("dash clears", "project",
     {"hooks": {"post_pack": "a.sh"}, "apply": {"sweep": False}}, None,
     {"hooks.post_pack": "-", "apply.sweep": "-"}, {}),
    ("typed values set", "project", {}, None,
     {"hooks.post_pack": " b.sh ", "apply.search_paths": "a::b:",
      "apply.no_interact": "Y", "apply.sweep": "0",
      "staging.strategy": "target-base", "validation.required": "t:lint"},
     {"hooks": {"post_pack": "b.sh"},
      "apply": {"search_paths": ["a", "b"], "no_interact": True,
                "sweep": False},
      "staging": {"strategy": "target-base"},
      "validation": {"required": ["t", "lint"]}}),
    ("x suppresses an inherited value and list", "project", {},
     {"identity": {"packer": "alice"}, "apply": {"search_paths": ["~/D"]}},
     {"identity.packer": "x", "apply.search_paths": "x"},
     {"identity": {"packer": ""}, "apply": {"search_paths": []}}),
    ("x without an inherited value keeps current", "project",
     {"identity": {"packer": "bob"}}, None,
     {"identity.packer": "x", "apply.search_paths": "x"},
     {"identity": {"packer": "bob"}}),
    ("a non-boolean keeps current", "project",
     {"apply": {"sweep": True}}, None, {"apply.sweep": "maybe"},
     {"apply": {"sweep": True}}),
    ("colon-only list input clears", "project",
     {"apply": {"search_paths": ["d"]}}, None,
     {"apply.search_paths": ":"}, {}),
    ("EOF and ^C keep", "project",
     {"hooks": {"post_pack": "a.sh"}, "apply": {"sweep": True,
      "search_paths": ["d"]}}, None,
     {"hooks.post_pack": EOF_ANSWER, "apply.sweep": INTERRUPT,
      "apply.search_paths": EOF_ANSWER},
     {"hooks": {"post_pack": "a.sh"}, "apply": {"search_paths": ["d"],
      "sweep": True}}),
    ("reject-with-hint keeps current (three checks)", "project",
     {"staging": {"strategy": "working-tree"},
      "probe": {"clipboard_command": "pbcopy"},
      "layout": {"agent_dir": "agent"}}, None,
     {"staging.strategy": "fast", "probe.clipboard_command": 'sh -c "x"',
      "layout.agent_dir": "/abs"},
     {"staging": {"strategy": "working-tree"},
      "probe": {"clipboard_command": "pbcopy"},
      "layout": {"agent_dir": "agent"}}),
    ("reject-with-hint accepts the good shapes", "project", {}, None,
     {"staging.strategy": " target-base ", "probe.clipboard_command": "pbcopy",
      "layout.agent_dir": "agent"},
     {"staging": {"strategy": "target-base"},
      "probe": {"clipboard_command": "pbcopy"},
      "layout": {"agent_dir": "agent"}}),
    # Eleven since session wizard-defaults: probe.clipboard_command is
    # walked at the global layer now; validation.base still is not.
    ("global walks only its eleven keys", "global",
     {"validation": {"base": "x.sh"}, "probe": {"clipboard_command": "p"},
      "identity": {"packer": "alice"}}, None,
     {"validation.base": "y.sh", "probe.clipboard_command": "q"},
     {"identity": {"packer": "alice"}, "probe": {"clipboard_command": "q"}}),
    ("misshapen values read as unset", "project",
     {"apply": {"no_interact": "yes", "search_paths": [1]},
      "identity": {"packer": 7}}, None, {}, {}),
]


class SemanticsTest(unittest.TestCase):

    def test_frozen_answer_table(self) -> None:
        for name, layer, existing, inherited, answers, expected in SEMANTICS:
            with self.subTest(case=name):
                new, _out, _p = walk_with_answers(
                    existing, layer=layer, answers=answers,
                    inherited=inherited)
                self.assertEqual(new, expected)

    def test_question_mark_first_changes_nothing(self) -> None:
        for name, layer, existing, inherited, answers, expected in SEMANTICS:
            with self.subTest(case=name):
                keys = bale_config.wizard_walk_order(layer)
                asked = {k: ["?", answers.get(k, "")] for k in keys}
                new, _out, _p = walk_with_answers(
                    existing, layer=layer, answers=asked,
                    inherited=inherited)
                self.assertEqual(new, expected)

    def test_reject_with_hint_says_why(self) -> None:
        _new, out, _p = walk_with_answers(
            {}, layer="project",
            answers={"staging.strategy": "fast",
                     "probe.clipboard_command": "C:\\clip.exe",
                     "layout.agent_dir": "/abs"})
        flat = " ".join(out.split())
        self.assertIn("is not a staging strategy", flat)
        self.assertIn("backslash", flat)
        self.assertIn("not absolute", flat)
        self.assertEqual(flat.count("Keeping current"), 3)


# ---------------------------------------------------------------------------
# The review
# ---------------------------------------------------------------------------

class ConfigChangesTest(unittest.TestCase):

    def test_rows_in_walk_order_with_reasons(self) -> None:
        old = {"identity": {"packer": "bob"}, "apply": {"sweep": True},
               "hooks": {"post_pack": "a.sh"}, "mystery": {"k": 1}}
        new = {"identity": {"packer": "carol"},
               "apply": {"search_paths": ["~/D"]}}
        rows = bale_config.config_changes(old, new, layer="project")
        self.assertEqual(rows, [
            ("-", 'hooks.post_pack = "a.sh"  (cleared)'),
            ("+", 'apply.search_paths = ["~/D"]'),
            ("-", "apply.sweep = true  (cleared)"),
            ("~", 'identity.packer = "bob" \u2192 "carol"'),
            ("-", "mystery.k = 1  (not walked at this layer; dropped)"),
        ])

    def test_identical_configs_have_no_rows(self) -> None:
        cfg = {"apply": {"search_paths": [], "sweep": False}}
        self.assertEqual(
            bale_config.config_changes(cfg, copy.deepcopy(cfg),
                                       layer="global"), [])

    def test_a_type_change_is_a_change(self) -> None:
        rows = bale_config.config_changes({"apply": {"sweep": 1}},
                                          {"apply": {"sweep": True}},
                                          layer="project")
        self.assertEqual(rows, [("~", "apply.sweep = 1 \u2192 true")])


class ReviewGateTest(unittest.TestCase):

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-wizui-")
        self.path = Path(self._tmp.name) / "bale.toml"
        self.main = _MainStandIns().__enter__()
        self.new_cfg = {"identity": {"packer": "bob"}}
        self.rendered = bale_config.render_bale_toml(self.new_cfg)

    def tearDown(self) -> None:
        self.main.__exit__(None, None, None)
        self._tmp.cleanup()

    def review(self, inputs, existing=None):
        return run_with_inputs(
            bale_config.review_and_write_config, inputs,
            bale_wizard.WizardUI(), self.path,
            existing=existing or {}, new_cfg=self.new_cfg,
            rendered=self.rendered, layer="project")

    def test_enter_creates_the_file(self) -> None:
        outcome, out, prompts = self.review([""])
        self.assertEqual(outcome, "created")
        self.assertEqual(self.path.read_text(encoding="utf-8"),
                         self.rendered)
        self.assertIn("creates bale.toml with 1 key set", out)
        self.assertIn('+ identity.packer = "bob"', out)
        self.assertEqual(len(prompts), 1)

    def test_enter_and_eof_write_n_and_interrupt_do_not(self) -> None:
        before = '[identity]\npacker = "alice"\n'
        for inputs, outcome in (([""], "updated"), ([EOF_ANSWER], "updated"),
                                (["n"], "not written"),
                                ([INTERRUPT], "not written")):
            with self.subTest(inputs=inputs):
                self.path.write_text(before, encoding="utf-8")
                result, out, _p = self.review(
                    inputs, existing={"identity": {"packer": "alice"}})
                self.assertEqual(result, outcome)
                written = self.path.read_text(encoding="utf-8")
                if outcome == "updated":
                    self.assertEqual(written, self.rendered)
                else:
                    self.assertEqual(written, before)
                    self.assertIn("not written", out)
                self.assertIn('identity.packer = "alice" \u2192 "bob"', out)

    def test_matching_file_is_left_alone_and_nothing_is_asked(self) -> None:
        self.path.write_text(self.rendered, encoding="utf-8")
        outcome, out, prompts = self.review(
            [], existing={"identity": {"packer": "bob"}})
        self.assertEqual(outcome, "unchanged")
        self.assertEqual(prompts, [])
        self.assertIn("no changes", out)

    def test_layout_only_difference_says_no_value_changes(self) -> None:
        self.path.write_text('[identity]\npacker = "bob"\n', encoding="utf-8")
        outcome, out, _p = self.review(
            [""], existing={"identity": {"packer": "bob"}})
        self.assertEqual(outcome, "updated")
        self.assertIn("no value changes", out)


class BaleignoreStepTest(unittest.TestCase):

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-wizign-")
        self.repo = Path(self._tmp.name)
        self.path = self.repo / ".baleignore"
        self.main = _MainStandIns().__enter__()

    def tearDown(self) -> None:
        self.main.__exit__(None, None, None)
        self._tmp.cleanup()

    def walk(self, inputs):
        return run_with_inputs(bale_config.walkthrough_baleignore, inputs,
                               self.repo, bale_wizard.WizardUI())

    def test_enter_through_without_a_file_creates_nothing(self) -> None:
        _r, out, prompts = self.walk([])
        self.assertFalse(self.path.exists())
        self.assertEqual(len(prompts), 1, msg="only the additions prompt")
        self.assertIn("no changes", out)

    def test_remove_and_add_then_enter_writes(self) -> None:
        self.path.write_text("# data\ndata/\n*.parquet\n", encoding="utf-8")
        _r, out, prompts = self.walk(["n", "", "foo/", "", ""])
        self.assertEqual(self.path.read_text(encoding="utf-8"),
                         "# data\n*.parquet\n\nfoo/\n")
        self.assertIn("- data/", out)
        self.assertIn("+ foo/", out)
        self.assertIn("[Y/n]", prompts[-1])

    def test_n_at_the_gate_leaves_the_file(self) -> None:
        before = "data/\n"
        self.path.write_text(before, encoding="utf-8")
        _r, out, _p = self.walk(["", "foo/", "", "n"])
        self.assertEqual(self.path.read_text(encoding="utf-8"), before)
        self.assertIn("not written", out)

    def test_all_removed_asks_then_removes(self) -> None:
        self.path.write_text("data/\n", encoding="utf-8")
        self.walk(["n", "", "n"])
        self.assertTrue(self.path.exists(), msg="n at the gate keeps it")
        self.walk(["n", "", ""])
        self.assertFalse(self.path.exists())

    def test_no_pattern_change_rewrites_as_before_without_asking(self) -> None:
        self.path.write_text("data/\r\n*.parquet", encoding="utf-8")
        _r, out, prompts = self.walk([])
        self.assertEqual(len(prompts), 3, msg="two keeps and the additions")
        self.assertEqual(self.path.read_text(encoding="utf-8"),
                         "data/\n*.parquet\n")
        self.assertIn("no changes", out)


# ---------------------------------------------------------------------------
# Detected defaults and named alternatives (session wizard-defaults)
# ---------------------------------------------------------------------------

Alt = bale_wizard.Alternative
ALT_LINE_RE = re.compile(r"^\s+\[(\d+)\] (.+?)(?:  \((.*)\))?$")


def alt_lines(output: str) -> list[tuple[int, str, str]]:
    """(number, value, aside) for every `[n] value  (aside)` line."""
    found = []
    for line in ANSI_RE.sub("", output).splitlines():
        match = ALT_LINE_RE.match(line)
        if match:
            found.append((int(match.group(1)), match.group(2),
                          match.group(3) or ""))
    return found


def rich_suggestions(**overrides) -> "bale_config.WizardSuggestions":
    """A WizardSuggestions offering something on every key that can
    take alternatives — the walk's widest screens, machine-independent."""
    alternatives = {
        "apply.search_paths": [
            Alt("/mnt/c/Users/alice/Downloads", "Windows Downloads", True),
            Alt("~/Downloads", "home Downloads", True)],
        "apply.archive_dir": [Alt("claude/responses", "exists", True)],
        "staging.strategy": bale_config.staging_strategy_alternatives(),
        "staging.untracked_inputs": [
            Alt(".venv", "present, untracked", True),
            Alt("node_modules", "present, untracked", True)],
        "identity.packer": [Alt("Alice Example", "git user.name", True)],
        "probe.clipboard_command": bale_config.clipboard_alternatives(
            platform="linux", environ={"WAYLAND_DISPLAY": "wayland-0"},
            which=lambda name: f"/usr/bin/{name}", wsl=False),
        "validation.base": bale_config.validation_base_alternatives(
            "claude", None),
    }
    alternatives.update(overrides)
    return bale_config.WizardSuggestions(alternatives=alternatives)


class ChoiceLayerTest(unittest.TestCase):
    """bale_wizard's choice primitives, additive beside ask_item."""

    def capture(self, fn):
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            fn(bale_wizard.WizardUI())
        return buffer.getvalue()

    def test_existing_surface_is_unchanged(self) -> None:
        """Session B builds on these names concurrently: the header
        pattern and ask_item's signature are part of the contract."""
        import inspect
        self.assertEqual(bale_wizard.ITEM_HEADER_RE.pattern,
                         r"^\s*(\d+)/(\d+)  (\S+)")
        self.assertEqual(
            list(inspect.signature(
                bale_wizard.WizardUI.ask_item).parameters),
            ["self", "enter_action", "show_help"])
        self.assertEqual(bale_wizard.BODY_INDENT, 9)

    def test_aside_and_detected_first(self) -> None:
        self.assertEqual(Alt("pbcopy", "macOS", True).aside(),
                         "macOS, detected")
        self.assertEqual(Alt("x", "", True).aside(), "detected")
        self.assertEqual(Alt("x", "note").aside(), "note")
        ordered = bale_wizard.detected_first(
            [Alt("a"), Alt("b", detected=True), Alt("c"),
             Alt("d", detected=True)])
        self.assertEqual([a.value for a in ordered], ["b", "d", "a", "c"])

    def test_pick_number_reads_plain_digits_only(self) -> None:
        self.assertEqual(bale_wizard.pick_number(" 3 "), 3)
        self.assertEqual(bale_wizard.pick_number("0"), 0)
        for text in ("", "-1", "+2", "2.0", "²", "٣", "1:2", "a1"):
            with self.subTest(text=text):
                self.assertIsNone(bale_wizard.pick_number(text))

    def test_lines_take_the_pinned_shape(self) -> None:
        out = self.capture(lambda ui: ui.alternatives(
            [Alt("pbcopy", "macOS", True), Alt("wl-copy", "Wayland"),
             Alt("xclip -selection clipboard")]))
        lines = out.splitlines()
        self.assertEqual(lines[0].strip(), "alternatives")
        self.assertEqual(lines[1:], [
            "         [1] pbcopy  (macOS, detected)",
            "         [2] wl-copy  (Wayland)",
            "         [3] xclip -selection clipboard",
        ])
        self.assertEqual(item_headers(out), [],
                         msg="an alternative line never reads as an item "
                             "header to the test drivers")

    def test_nothing_to_offer_draws_nothing(self) -> None:
        self.assertEqual(self.capture(lambda ui: ui.alternatives([])), "")

    def test_long_values_keep_the_width_contract(self) -> None:
        path = "/mnt/c/Users/" + "averyverylongprofilename" * 3 + "/Downloads"
        out = self.capture(lambda ui: ui.alternatives(
            [Alt(path, "Windows Downloads", True),
             Alt("short", "an aside long enough that it cannot ride beside "
                          "its value on one eighty-column line")]))
        self.assertIn(f"[1] {path}", out, msg="an absolute path stays whole")
        self.assertEqual(overwide(out), [])
        self.assertIn("(Windows Downloads, detected)", out)

    def test_forced_color_keeps_the_value_whole(self) -> None:
        buffer = io.StringIO()
        with contextlib.redirect_stdout(buffer):
            bale_wizard.WizardUI(color=True).alternatives(
                [Alt("wl-copy", "Wayland")])
        self.assertIn("[1] wl-copy", buffer.getvalue())

    def test_ask_choice_returns_in_range_answers_raw(self) -> None:
        ui = bale_wizard.WizardUI()
        for typed in ("2", "", "value", "-", "x", " 3 "):
            with self.subTest(typed=typed):
                answer, _out, prompts = run_with_inputs(
                    ui.ask_choice, [typed], "Enter keeps current", count=3,
                    show_help=lambda: None)
                self.assertEqual(answer, typed.strip())
                self.assertEqual(len(prompts), 1)
                self.assertIn("Enter keeps current", prompts[0])
                self.assertIn("1-3 picks", prompts[0])
                self.assertIn("? help", prompts[0])

    def test_out_of_range_is_not_a_pick_and_asks_again(self) -> None:
        ui = bale_wizard.WizardUI()
        answer, out, prompts = run_with_inputs(
            ui.ask_choice, ["7", "0", "2"], "Enter keeps current", count=2,
            show_help=lambda: None)
        self.assertEqual(answer, "2")
        self.assertEqual(len(prompts), 3)
        self.assertIn("no alternative 7; pick 1-2", " ".join(out.split()))
        self.assertIn("no alternative 0", out)

    def test_separator_judges_each_entry(self) -> None:
        ui = bale_wizard.WizardUI()
        answer, out, prompts = run_with_inputs(
            ui.ask_choice, ["1:9", "1:2:inbox"], "Enter", count=2,
            show_help=lambda: None, separator=":")
        self.assertEqual(answer, "1:2:inbox")
        self.assertEqual(len(prompts), 2)
        self.assertIn("no alternative 9", out)

    def test_help_eof_and_single_alternative(self) -> None:
        ui = bale_wizard.WizardUI()
        shown = []
        answer, _out, prompts = run_with_inputs(
            ui.ask_choice, ["?", "1"], "Enter leaves it unset", count=1,
            show_help=lambda: shown.append(1))
        self.assertEqual((answer, len(shown)), ("1", 1))
        self.assertIn("1 picks it", prompts[0])
        for gesture in (EOF_ANSWER, INTERRUPT):
            with self.subTest(gesture=gesture):
                answer, _o, _p = run_with_inputs(
                    ui.ask_choice, [gesture], "Enter", count=2,
                    show_help=lambda: None)
                self.assertIsNone(answer)
        with self.assertRaises(ValueError):
            ui.ask_choice("Enter", count=0, show_help=lambda: None)


class ChoiceWalkTest(unittest.TestCase):
    """The alternatives through walk_configurables: a number sets the
    value at the layer walked; Enter keeps meaning what it meant."""

    def test_enter_through_writes_nothing_with_every_offer_shown(self) -> None:
        """The clipboard opt-in rests on this: detected values are on
        screen, and an Enter-through still returns the file unchanged."""
        cases = [({}, None), (SEMANTICS[0][2], None),
                 ({"probe": {"clipboard_command": "pbcopy"}},
                  {"probe": {"clipboard_command": "xclip"},
                   "identity": {"packer": "alice"}})]
        for layer in ("project", "global"):
            for existing, inherited in cases:
                with self.subTest(layer=layer, existing=existing):
                    plain, _o, _p = walk_with_answers(
                        existing, layer=layer, answers={},
                        inherited=inherited if layer == "project" else None,
                        suggestions=bale_config.WizardSuggestions())
                    offered, out, _p = walk_with_answers(
                        existing, layer=layer, answers={},
                        inherited=inherited if layer == "project" else None,
                        suggestions=rich_suggestions())
                    self.assertEqual(offered, plain)
                    self.assertTrue(alt_lines(out))

    def test_numbers_set_values_at_the_layer_walked(self) -> None:
        answers = {"apply.search_paths": "1:2",
                   "apply.archive_dir": "1",
                   "staging.strategy": "2",
                   "staging.untracked_inputs": "1:vendor",
                   "identity.packer": "1",
                   "probe.clipboard_command": "1",
                   "validation.base": "1"}
        new, _out, _p = walk_with_answers(
            {}, layer="project", answers=answers,
            suggestions=rich_suggestions())
        self.assertEqual(new, {
            "apply": {"search_paths": ["/mnt/c/Users/alice/Downloads",
                                       "~/Downloads"],
                      "archive_dir": "claude/responses"},
            "staging": {"strategy": "target-base",
                        "untracked_inputs": [".venv", "vendor"]},
            "identity": {"packer": "Alice Example"},
            "probe": {"clipboard_command": "wl-copy"},
            "validation": {"base": "claude/checkpoints/{sid}.sh"},
        })
        new, _out, _p = walk_with_answers(
            {}, layer="global",
            answers={"probe.clipboard_command": "4", "identity.packer": "1"},
            suggestions=rich_suggestions())
        self.assertEqual(new, {
            "identity": {"packer": "Alice Example"},
            "probe": {"clipboard_command": "xclip -selection clipboard"}})

    def test_a_pick_equals_typing_the_value(self) -> None:
        suggestions = rich_suggestions()
        for key, number in (("probe.clipboard_command", "3"),
                            ("staging.strategy", "1"),
                            ("identity.packer", "1")):
            value = suggestions.for_key(key)[int(number) - 1].value
            with self.subTest(key=key):
                picked, _o, _p = walk_with_answers(
                    {}, layer="project", answers={key: number},
                    suggestions=suggestions)
                typed, _o, _p = walk_with_answers(
                    {}, layer="project", answers={key: value},
                    suggestions=suggestions)
                self.assertEqual(picked, typed)

    def test_every_other_answer_keeps_its_meaning(self) -> None:
        inherited = {"identity": {"packer": "alice"},
                     "probe": {"clipboard_command": "xclip"}}
        existing = {"apply": {"archive_dir": "keep/me"}}
        new, out, _p = walk_with_answers(
            existing, layer="project", inherited=inherited,
            suggestions=rich_suggestions(),
            answers={"identity.packer": "x",
                     "probe.clipboard_command": ["?", "x"],
                     "apply.archive_dir": ["9", ""],
                     "staging.strategy": "fast"})
        self.assertEqual(new, {"apply": {"archive_dir": "keep/me"},
                               "identity": {"packer": ""},
                               "probe": {"clipboard_command": ""}})
        flat = " ".join(out.split())
        self.assertIn("no alternative 9; pick 1", flat)
        self.assertIn("is not a staging strategy", flat)
        self.assertIn("a number sets the alternative listed above", flat,
                      msg="the '?' help names the number gesture")

    def test_alternatives_sit_above_the_prompt_in_the_pinned_shape(self) -> None:
        _new, out, prompts = walk_with_answers(
            {}, layer="project", answers={},
            suggestions=rich_suggestions())
        rows = alt_lines(out)
        self.assertIn((1, "wl-copy", "Wayland, detected"), rows)
        self.assertIn((2, "pbcopy", "macOS"), rows)
        self.assertIn((1, "/mnt/c/Users/alice/Downloads",
                       "Windows Downloads, detected"), rows)
        by_key = dict(prompts)
        self.assertIn("1-5 picks", by_key["probe.clipboard_command"])
        self.assertIn("1 picks it", by_key["identity.packer"])
        self.assertNotIn("picks", by_key["apply.sweep"],
                         msg="a key with nothing to offer asks as before")
        self.assertEqual(overwide(out), [])

    def test_no_offer_draws_the_screen_as_it_was(self) -> None:
        _new, out, prompts = walk_with_answers(
            {}, layer="project", answers={},
            suggestions=bale_config.WizardSuggestions())
        self.assertEqual(alt_lines(out), [])
        self.assertNotIn("alternatives", out)
        self.assertTrue(all(p.endswith(" · ? help > ")
                            and "picks" not in p for _k, p in prompts))

    def test_notes_and_warnings_reach_their_screen(self) -> None:
        suggestions = bale_config.WizardSuggestions()
        suggestions.note("identity.packer", "detection skipped: git not found")
        suggestions.warn("probe.clipboard_command", "spelled oddly")
        _new, out, _p = walk_with_answers(
            {}, layer="global", answers={}, suggestions=suggestions)
        packer = out.index("identity.packer")
        self.assertLess(packer, out.index("detection skipped: git not found"))
        self.assertIn("! spelled oddly", out)


class DetectionTest(unittest.TestCase):
    """Each detector with its environment injected: suggestions only,
    and nothing found degrades to the static list or to nothing."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-wizdet-")
        self.tmp = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_clipboard_detection_matrix(self) -> None:
        def which_of(*present):
            return lambda name: f"/bin/{name}" if name in present else None
        cases = [
            ("darwin", {}, which_of("pbcopy"), False, "pbcopy"),
            ("darwin", {}, which_of(), False, None),
            ("win32", {}, which_of("clip.exe"), False, "clip.exe"),
            ("linux", {}, which_of("clip.exe"), True, "clip.exe"),
            ("linux", {"WAYLAND_DISPLAY": "w"}, which_of("wl-copy"), False,
             "wl-copy"),
            ("linux", {"WAYLAND_DISPLAY": "w", "DISPLAY": ":0"},
             which_of("xclip"), False, "xclip -selection clipboard"),
            ("linux", {"DISPLAY": ":0"}, which_of("xsel"), False,
             "xsel --clipboard --input"),
            ("linux", {}, which_of("xclip", "wl-copy"), False, None),
        ]
        for platform, env, which, wsl, expected in cases:
            with self.subTest(platform=platform, env=env, wsl=wsl):
                self.assertEqual(bale_config.detect_clipboard_command(
                    platform=platform, environ=env, which=which, wsl=wsl),
                    expected)

    def test_clipboard_alternatives_are_always_the_five(self) -> None:
        none = bale_config.clipboard_alternatives(
            platform="linux", environ={}, which=lambda n: None, wsl=False)
        self.assertEqual([a.value for a in none],
                         [v for v, _n in bale_config.CLIPBOARD_ALTERNATIVES])
        self.assertFalse(any(a.detected for a in none))
        mac = bale_config.clipboard_alternatives(
            platform="darwin", environ={}, which=lambda n: "/x", wsl=False)
        self.assertEqual(mac[0], Alt("pbcopy", "macOS", True))
        wsl = bale_config.clipboard_alternatives(
            platform="linux", environ={}, which=lambda n: "/x", wsl=True)
        self.assertEqual((wsl[0].value, wsl[0].detected), ("clip.exe", True))
        self.assertEqual(len(wsl), 5)

    def test_is_wsl(self) -> None:
        osrelease = self.tmp / "osrelease"
        self.assertTrue(bale_config.is_wsl({"WSL_DISTRO_NAME": "Ubuntu"},
                                           osrelease))
        self.assertFalse(bale_config.is_wsl({}, osrelease), msg="no file")
        osrelease.write_text("5.15.153.1-microsoft-standard-WSL2\n")
        self.assertTrue(bale_config.is_wsl({}, osrelease))
        osrelease.write_text("6.8.0-generic\n")
        self.assertFalse(bale_config.is_wsl({}, osrelease))

    def test_search_paths_offer_what_exists(self) -> None:
        users = self.tmp / "Users"
        for name in ("alice", "Public", "zed", "bob"):
            (users / name).mkdir(parents=True)
        for name in ("alice", "Public", "zed"):
            (users / name / "Downloads").mkdir()
        home = self.tmp / "home"
        home.mkdir()
        self.assertEqual(bale_config.search_path_alternatives(
            home=home, environ={"USER": "zed"}, wsl=True,
            windows_users=users), [
            Alt(str(users / "zed" / "Downloads"), "Windows Downloads", True),
            Alt(str(users / "alice" / "Downloads"), "Windows Downloads",
                True)])
        (home / "Downloads").mkdir()
        both = bale_config.search_path_alternatives(
            home=home, environ={"USER": "alice"}, wsl=True,
            windows_users=users)
        self.assertEqual([a.value for a in both],
                         [str(users / "alice" / "Downloads"),
                          str(users / "zed" / "Downloads"), "~/Downloads"])
        self.assertEqual(bale_config.search_path_alternatives(
            home=home, environ={}, wsl=False, windows_users=users),
            [Alt("~/Downloads", "home Downloads", True)])
        self.assertEqual(bale_config.search_path_alternatives(
            home=self.tmp / "nohome", environ={}, wsl=True,
            windows_users=self.tmp / "nomount"), [])

    def test_conventions_mark_what_the_repo_already_has(self) -> None:
        repo = self.tmp
        self.assertEqual(bale_config.archive_dir_alternatives("agent", repo),
                         [Alt("agent/responses", "the archive convention")])
        (repo / "agent" / "responses").mkdir(parents=True)
        self.assertEqual(bale_config.archive_dir_alternatives("agent", repo),
                         [Alt("agent/responses", "exists", True)])
        base = bale_config.validation_base_alternatives("agent", repo)
        self.assertEqual([a.value for a in base],
                         ["agent/checkpoints/{sid}.sh",
                          "scripts/validation.base.sh"])
        self.assertFalse(any(a.detected for a in base))
        (repo / "scripts").mkdir()
        (repo / "scripts" / "validation.base.sh").write_text("exit 0\n")
        base = bale_config.validation_base_alternatives("agent", repo)
        self.assertEqual((base[0].value, base[0].detected),
                         ("scripts/validation.base.sh", True),
                         msg="the detected convention moves to [1]")
        self.assertEqual(
            [a.value for a in bale_config.staging_strategy_alternatives()],
            list(bale_config.STAGING_STRATEGIES))

    def test_agent_dir_follows_the_project_layout(self) -> None:
        sugg = bale_config.suggest_wizard_values(
            "project", {"layout": {"agent_dir": "agent"}}, repo=None,
            environ={}, home=self.tmp, platform="linux",
            which=lambda n: None, wsl=False)
        self.assertEqual(sugg.for_key("apply.archive_dir")[0].value,
                         "agent/responses")
        self.assertEqual(sugg.for_key("validation.base")[0].value,
                         "agent/checkpoints/{sid}.sh")
        glob = bale_config.suggest_wizard_values(
            "global", {}, environ={}, home=self.tmp, platform="linux",
            which=lambda n: None, wsl=False)
        self.assertEqual(glob.for_key("validation.base"), [],
                         msg="no project-only offers at the global layer")
        self.assertEqual(glob.for_key("staging.untracked_inputs"), [],
                         msg="no repo, no untracked-input detection")


class GitDetectionTest(unittest.TestCase):
    """The git-backed detectors, against a real scratch repo."""

    def setUp(self) -> None:
        import os
        import subprocess
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-wizgit-")
        self.tmp = Path(self._tmp.name)
        self.home = make_sandbox_home(self.tmp)
        self.repo = make_repo(self.tmp, home=self.home)
        # Detection runs git with this process's environment: point it at
        # the sandbox identity so the machine's own gitconfig never leaks.
        self._env = {k: os.environ.get(k) for k in
                     ("HOME", "GIT_CONFIG_NOSYSTEM", "GIT_CONFIG_GLOBAL",
                      "XDG_CONFIG_HOME")}
        os.environ["HOME"] = str(self.home)
        os.environ["GIT_CONFIG_NOSYSTEM"] = "1"
        os.environ.pop("GIT_CONFIG_GLOBAL", None)
        os.environ.pop("XDG_CONFIG_HOME", None)
        self.git = lambda *a: subprocess.run(
            ["git", *a], cwd=self.repo, check=True, capture_output=True)

    def tearDown(self) -> None:
        import os
        for key, value in self._env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self._tmp.cleanup()

    def test_git_user_name(self) -> None:
        self.assertEqual(bale_config.detect_git_user_name(self.repo),
                         ("Bale Test Sandbox", None))
        self.assertEqual(bale_config.detect_git_user_name(None),
                         ("Bale Test Sandbox", None))
        self.git("config", "user.name", "Repo Local")
        self.assertEqual(bale_config.detect_git_user_name(self.repo),
                         ("Repo Local", None))
        (self.home / ".gitconfig").write_text("[init]\n")
        self.assertEqual(bale_config.detect_git_user_name(None), (None, None),
                         msg="unset is nothing found, not a failure")

    def test_untracked_inputs_need_presence_and_no_tracking(self) -> None:
        self.assertEqual(
            bale_config.untracked_input_alternatives(self.repo), ([], None))
        (self.repo / ".venv" / "bin").mkdir(parents=True)
        (self.repo / ".venv" / "bin" / "python").write_text("")
        (self.repo / ".gitignore").write_text(".venv/\n")
        (self.repo / "node_modules").mkdir()
        (self.repo / "node_modules" / "pkg.js").write_text("")
        self.git("add", "-f", "node_modules/pkg.js")
        self.assertEqual(
            bale_config.untracked_input_alternatives(self.repo),
            ([Alt(".venv", "present, untracked", True)], None))

    def test_baleignore_suggestions_follow_what_pack_would_ship(self) -> None:
        def write(rel, size):
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"x" * size)
        write("data/a.csv", 3000)
        write("data/sub/b.parquet", 1000)
        write("models/m.parquet", 5000)
        write("models/n.PARQUET", 10)
        write("big.json", 2 * 1024 * 1024)
        write("docs/notes.md", 4 * 1024 * 1024)
        write("dist/pkg.whl", 9 * 1024 * 1024)   # pack's baked-in excludes
        write("small.txt", 10)
        write("ignored/huge.zip", 8 * 1024 * 1024)
        (self.repo / ".gitignore").write_text("ignored/\n")
        found, why = bale_config.baleignore_suggestions(self.repo)
        self.assertIsNone(why)
        self.assertEqual([a.value for a in found],
                         ["docs/notes.md", "/big.json", "*.parquet",
                          "data/", "*.PARQUET"])
        self.assertEqual(found[2].note, "1 file, 4.9 KB")
        self.assertEqual(found[3].note, "2 files, 3.9 KB")
        again, _w = bale_config.baleignore_suggestions(
            self.repo, ["data/", " /big.json "])
        self.assertNotIn("data/", [a.value for a in again])
        self.assertNotIn("/big.json", [a.value for a in again])

    def test_not_a_repo_degrades_with_a_reason(self) -> None:
        found, why = bale_config.baleignore_suggestions(self.tmp / "home")
        self.assertEqual(found, [])
        self.assertIn("git ls-files exited", why)


class BaleignoreSuggestionStepTest(unittest.TestCase):
    """The .baleignore step's [n] picks, with suggestions injected."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-wizbis-")
        self.repo = Path(self._tmp.name)
        self.path = self.repo / ".baleignore"
        self.main = _MainStandIns().__enter__()
        self.offer = [Alt("*.parquet", "3 files, 40 MB"),
                      Alt("data/", "12 files, 2.0 MB")]

    def tearDown(self) -> None:
        self.main.__exit__(None, None, None)
        self._tmp.cleanup()

    def walk(self, inputs, offer=None):
        return run_with_inputs(
            bale_config.walkthrough_baleignore, inputs, self.repo,
            bale_wizard.WizardUI(),
            suggestions=self.offer if offer is None else offer)

    def test_enter_through_adds_nothing(self) -> None:
        _r, out, prompts = self.walk([])
        self.assertFalse(self.path.exists())
        self.assertEqual(alt_lines(out), [(1, "*.parquet", "3 files, 40 MB"),
                                          (2, "data/", "12 files, 2.0 MB")])
        self.assertIn("1-2 picks", prompts[0])

    def test_a_number_adds_its_pattern_once(self) -> None:
        _r, out, _p = self.walk(["2", "7", "2", "1", "", ""])
        self.assertEqual(self.path.read_text(encoding="utf-8"),
                         "data/\n*.parquet\n")
        self.assertIn("no suggestion 7; pick 1-2", " ".join(out.split()))
        self.assertIn("data/ is already added", out)

    def test_kept_patterns_are_not_offered_again(self) -> None:
        self.path.write_text("data/\n", encoding="utf-8")
        _r, out, _p = self.walk([])
        self.assertEqual(alt_lines(out), [(1, "*.parquet", "3 files, 40 MB")])

    def test_without_suggestions_a_digit_is_a_pattern(self) -> None:
        _r, out, prompts = self.walk(["2024", "", ""], offer=[])
        self.assertEqual(self.path.read_text(encoding="utf-8"), "2024\n")
        self.assertEqual(alt_lines(out), [])
        self.assertEqual(prompts[0].strip(), "add >")


# ---------------------------------------------------------------------------
# End to end under a pty
# ---------------------------------------------------------------------------

class EndToEndTest(unittest.TestCase):

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-wizpty-")
        self.tmp = Path(self._tmp.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, home=self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def init(self, *, global_layer=False, answers="\n" * 40, env=None):
        args = ["config", "init"] + (["--global"] if global_layer else [])
        code, out = run_bale_pty(self.install, args, cwd=self.repo,
                                 env=env or self.env, answers=answers)
        self.assertEqual(code, 0, msg=out)
        return out

    def test_project_enter_through(self) -> None:
        out = self.init()
        self.assertEqual(
            item_headers(out),
            [(i + 1, 19, key) for i, key in enumerate(PROJECT_KEYS)])
        self.assertEqual(out.count("How to answer"), 1)
        self.assertEqual(overwide(out), [])
        prompts = len(re.findall(r"> |\[Y/n\] ", ANSI_RE.sub("", out)))
        self.assertEqual(prompts, 21,
                         msg="19 keys, the bale.toml gate, one additions "
                             "prompt — well inside the pty suites' 40")
        rendered = (self.repo / "bale.toml").read_text(encoding="utf-8")
        self.assertEqual(rendered, bale_config.render_bale_toml({}),
                         msg="an Enter-through run lands the header-only "
                             "file, as before the review existed")

    def test_project_with_inherited_state_and_help_everywhere(self) -> None:
        user = self.install / "user"
        user.mkdir()
        (user / "bale.toml").write_text(
            '[apply]\nsearch_paths = ["~/Downloads", "/opt/' + "deep/" * 14
            + 'inbox"]\nno_interact = true\n[identity]\npacker = "alice"\n',
            encoding="utf-8")
        (self.repo / "bale.toml").write_text(
            '[hooks]\npost_pack = ""\n[apply]\nsearch_paths = []\n'
            '[probe]\nclipboard_command = "pbcopy"\n[mystery]\nk = 1\n',
            encoding="utf-8")
        (self.repo / ".baleignore").write_text("data/\n", encoding="utf-8")
        answers = "?\n\n" * 19 + "\n" + "n\n" + "foo/\n\n" + "\n"
        out = self.init(answers=answers)
        self.assertEqual(overwide(out), [])
        self.assertEqual(len(item_headers(out)), 19)
        self.assertIn("mystery.k = 1  (not walked at this layer; dropped)",
                      ANSI_RE.sub("", out))
        self.assertEqual(
            (self.repo / "bale.toml").read_text(encoding="utf-8"),
            bale_config.render_bale_toml(
                {"hooks": {"post_pack": ""}, "apply": {"search_paths": []},
                 "probe": {"clipboard_command": "pbcopy"}}))
        self.assertEqual(
            (self.repo / ".baleignore").read_text(encoding="utf-8"),
            "foo/\n")

    def test_global_enter_through(self) -> None:
        out = self.init(global_layer=True)
        self.assertEqual(
            item_headers(out),
            [(i + 1, 11, key) for i, key in enumerate(GLOBAL_KEYS)])
        self.assertEqual(overwide(out), [])
        self.assertNotIn("Git identity", out)
        self.assertNotIn(".baleignore", out)
        self.assertTrue((self.install / "user" / "bale.toml").is_file())

    def test_color_only_with_a_terminal_type_and_without_no_color(self) -> None:
        colored = dict(self.env, TERM="xterm-256color")
        self.assertIn(ESC, self.init(env=colored))
        self.assertNotIn(ESC, self.init(env=dict(colored, NO_COLOR="1")))
        self.assertNotIn(ESC, self.init(env=self.env),
                         msg="the harness env sets no TERM: plain")

    def test_piped_run_is_plain_and_still_writes(self) -> None:
        env = dict(self.env, TERM="xterm-256color")
        (self.repo / "bale.toml").write_text(
            '[identity]\npacker = "bob"\n', encoding="utf-8")
        result = run_bale(self.install, ["config", "init"], cwd=self.repo,
                          env=env)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn(ESC, result.stdout + result.stderr)
        self.assertEqual(
            (self.repo / "bale.toml").read_text(encoding="utf-8"),
            bale_config.render_bale_toml({"identity": {"packer": "bob"}}),
            msg="a closed stdin keeps every value and writes at the gate")


if __name__ == "__main__":
    unittest.main(verbosity=2)
