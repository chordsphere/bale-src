"""The goal-less `bale pack` wizard on the shared wizard layer.

Session pack-wizard-ui (wave 2 of the friction-points arc) moved the
wizard bale_pack runs when `bale pack` is missing its goal or --slug onto
bin/bale_wizard.py, the display layer `bale config init` already uses.
This suite pins what that move promised:

- **Answers keep their meaning.** In-process cases feed the prompt
  helpers fixed answer streams through a patched input() and check what
  lands on args: the session-shape letters and spelled-out forms, Enter's
  defaults, the README y/N's decline-on-anything-else. The pty suites in
  the session's forecast (test_readonly_pack, test_write_forecast, ...)
  pin the same property end to end with their unchanged answer streams.
- **The one new default**: Enter at the slug question takes a slug
  derived from the goal (suggest_slug), where it used to re-prompt.
- **Width**: every line from the title screen through the last question
  fits 80 columns, a line naming an absolute path excepted.
- **No `[bale] ` line between the first question and the last**: the
  post-walk gates' log lines are held and print after the README
  question, and before the error line of a refusal. Since session
  log-hold the hold is bin/bale's own (hold_log / release_log in its
  logging section); bale_pack's WalkLogHold, which rebound
  `__main__.log` / `__main__.fail`, is retired.
- **80 columns before and inside the walk** (session log-hold): from
  its start until the walk's first question, cmd_pack turns on
  bin/bale's display wrapping, so on a terminal the pre-walk [bale]
  lines are word-wrapped to its width; the read-only sweep's y/N is laid
  out the same way — layout only, its answers mean what they meant.
  Piped output, the session journal, and every line outside that span
  are byte-identical to before.
- **One visual grammar**: item headers match bale_wizard.ITEM_HEADER_RE,
  and the n/N count re-derives when a read-only answer drops items.

The end-to-end cases drive bale on a pseudo-terminal one answer at a time
(run_walk_pty below) rather than writing every answer up front as
harness.run_bale_pty does: with the answers typed as each prompt appears,
the echo lands after its prompt, so the transcript reads as a user sees it
and its lines can be measured. run_bale_pty is left as it is; its suites
pin answer streams, not layout.
"""

from __future__ import annotations

import builtins
import contextlib
import io
import os
import re
import select
import subprocess
import sys
import tempfile
import time
import types
import unittest
from argparse import Namespace
from pathlib import Path

from harness import (
    BIN_DIR,
    PTY_TIMEOUT,
    SUBPROCESS_TIMEOUT,
    _load_cli,
    _load_module,
    bale_env,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_checked,
)

bale_wizard = _load_module("bale_wizard")
bale_pack = _load_module("bale_pack")
_load_module("bale_config")  # registered for the picker tests' patches

TITLE_MARKER = "bale pack — interactive mode"
README_PROMPT = "y, or Enter = no > "
OUT_OF_SCOPE_KEY = "--out-of-scope"
SWEEP_PROMPT_MARKER = "Close open read-only session"
BLINDNESS_LOG_MARKER = "[bale] checkpoint blindness gate passed"
SID_BASE = "claude/checkpoints/{sid}.sh"

# EOF typed at a prompt (^D at the start of a line, canonical mode).
EOF = "\x04"


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------

def run_walk_pty(install: Path, args: list, *, cwd: Path, env: dict,
                 answers: list) -> tuple:
    """Run bale on a pty, typing each answer once a prompt is waiting.

    A prompt is waiting when the child has been quiet for a moment and
    its output ends the way every bale prompt ends ("> " for the walk,
    "] " for a [Y/n] / [y/N] exchange). Answers are typed one at a time
    (EOF is the bare ^D), so the terminal echo follows its prompt and
    the transcript is the one a user sees. Returns (exit_code, output),
    output with CRLF folded to LF.
    """
    import pty

    master, slave = pty.openpty()
    pending = list(answers)
    chunks: list[bytes] = []
    try:
        proc = subprocess.Popen(
            [sys.executable, str(install / "bin" / "bale"), *args],
            cwd=cwd, env=env, stdin=slave, stdout=slave, stderr=slave,
            close_fds=True,
        )
        os.close(slave)
        slave = None
        deadline = time.monotonic() + PTY_TIMEOUT
        last_output = time.monotonic()
        answered_at_len = -1
        while True:
            if time.monotonic() > deadline:
                proc.kill()
                raise AssertionError(
                    "pty-driven bale run timed out; output so far:\n"
                    + b"".join(chunks).decode(errors="replace"))
            readable, _, _ = select.select([master], [], [], 0.05)
            if master in readable:
                try:
                    chunk = os.read(master, 4096)
                except OSError:
                    break  # child closed its side (Linux raises EIO)
                if not chunk:
                    break
                chunks.append(chunk)
                last_output = time.monotonic()
                continue
            if proc.poll() is not None:
                break
            text = b"".join(chunks)
            quiet = time.monotonic() - last_output > 0.15
            waiting = text.endswith(b"> ") or text.endswith(b"] ")
            if pending and quiet and waiting and len(text) != answered_at_len:
                answer = pending.pop(0)
                os.write(master, (answer if answer == EOF
                                  else answer + "\n").encode())
                answered_at_len = len(text)
        exit_code = proc.wait(timeout=SUBPROCESS_TIMEOUT)
    finally:
        if slave is not None:
            os.close(slave)
        os.close(master)
    output = b"".join(chunks).decode(errors="replace")
    return exit_code, output.replace("\r\n", "\n")


def walk_span(output: str, *, last: str) -> list:
    """The transcript's lines from the wizard's title through the last
    line containing `last` (the walk's final prompt)."""
    lines = output.split("\n")
    start = next(i for i, ln in enumerate(lines) if TITLE_MARKER in ln)
    end = max(i for i, ln in enumerate(lines) if last in ln)
    return lines[start:end + 1]


def item_headers(lines: list) -> list:
    """(position, total, key) for each item header line, in order."""
    found = []
    for ln in lines:
        m = bale_wizard.ITEM_HEADER_RE.match(ln)
        if m:
            found.append((int(m.group(1)), int(m.group(2)), m.group(3)))
    return found


@contextlib.contextmanager
def fed_input(answers: list):
    """Patch builtins.input to return `answers` in order (EOFError past
    the end); yields the list of prompts input() was called with."""
    prompts: list = []
    stream = iter(answers)

    def fake_input(prompt=""):
        prompts.append(prompt)
        try:
            return next(stream)
        except StopIteration:
            raise EOFError from None

    saved = builtins.input
    builtins.input = fake_input
    try:
        yield prompts
    finally:
        builtins.input = saved


def quiet_walk(plan: list):
    """A PackWalk on a plain (uncolored) UI, for in-process cases."""
    return bale_pack.PackWalk(bale_wizard.WizardUI(color=False), plan)


# ---------------------------------------------------------------------------
# suggest_slug — the slug question's Enter default
# ---------------------------------------------------------------------------

def is_valid_slug(s: str) -> bool:
    """bin/bale's rule, restated: lowercase letters, digits, single
    hyphens between them (the CLI's own copy is pinned elsewhere)."""
    return bool(s) and not s.startswith("-") and not s.endswith("-") \
        and "--" not in s and all(c.islower() or c.isdigit() or c == "-"
                                  for c in s)


class SuggestSlugTest(unittest.TestCase):
    def test_first_four_words_without_stopwords(self) -> None:
        self.assertEqual(
            bale_pack.suggest_slug(
                "Move the goal-less bale pack wizard onto the shared layer"),
            "move-goal-less-bale-pack")

    def test_punctuation_and_case_fold_away(self) -> None:
        self.assertEqual(bale_pack.suggest_slug("Fix: README typo!"),
                         "fix-readme-typo")

    def test_all_stopwords_keeps_the_words(self) -> None:
        self.assertEqual(bale_pack.suggest_slug("To be or"), "to-be-or")

    def test_no_ascii_alnum_gives_none(self) -> None:
        self.assertIsNone(bale_pack.suggest_slug("¿¡ — …"))
        self.assertIsNone(bale_pack.suggest_slug(""))

    def test_length_cap_stops_at_a_word(self) -> None:
        slug = bale_pack.suggest_slug(
            "internationalization localization accessibility performance")
        self.assertLessEqual(len(slug), bale_pack.SLUG_SUGGESTION_MAX_CHARS)
        self.assertEqual(slug, "internationalization-localization")

    def test_one_overlong_word_is_cut_not_dropped(self) -> None:
        slug = bale_pack.suggest_slug("x" * 60)
        self.assertEqual(slug, "x" * bale_pack.SLUG_SUGGESTION_MAX_CHARS)

    def test_every_suggestion_is_a_valid_slug(self) -> None:
        goals = ["Ship v2.0 -- now!", "a-b--c", "Q3 report: 50% done",
                 "-leading and trailing-", "naïve café résumé",
                 "x" * 39 + "-yy more words"]
        for goal in goals:
            slug = bale_pack.suggest_slug(goal)
            if slug is not None:
                self.assertTrue(is_valid_slug(slug), (goal, slug))


# ---------------------------------------------------------------------------
# PackWalk — numbering, headings, the plan
# ---------------------------------------------------------------------------

class PackWalkTest(unittest.TestCase):
    def draw(self, walk, keys) -> str:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            for key in keys:
                walk.begin(key, kind="k", summary="s")
        return buf.getvalue()

    def test_headers_count_the_plan_and_match_the_layer_pattern(self) -> None:
        plan = [bale_pack.WALK_GOAL, bale_pack.WALK_SLUG,
                bale_pack.WALK_EXCLUDE]
        out = self.draw(quiet_walk(plan), plan)
        self.assertEqual(item_headers(out.splitlines()),
                         [(1, 3, "goal"), (2, 3, "--slug"),
                          (3, 3, "--exclude")])

    def test_drop_renumbers_the_items_still_to_come(self) -> None:
        plan = list(bale_pack.WALK_ORDER)
        walk = quiet_walk(plan)
        first = self.draw(walk, [bale_pack.WALK_GOAL, bale_pack.WALK_SLUG,
                                 bale_pack.WALK_SHAPE])
        walk.drop(bale_pack.WALK_WRITE, bale_pack.WALK_CHECKPOINT)
        rest = self.draw(walk, [bale_pack.WALK_EXCLUDE,
                                bale_pack.WALK_README])
        self.assertEqual(item_headers(first.splitlines())[-1],
                         (3, 9, "shape"))
        self.assertEqual(item_headers(rest.splitlines()),
                         [(4, 7, "--exclude"), (7, 7, "readme")])

    def test_drop_refuses_an_item_already_asked(self) -> None:
        walk = quiet_walk([bale_pack.WALK_GOAL])
        self.draw(walk, [bale_pack.WALK_GOAL])
        with self.assertRaises(ValueError):
            walk.drop(bale_pack.WALK_GOAL)

    def test_begin_refuses_an_unplanned_item(self) -> None:
        walk = quiet_walk([bale_pack.WALK_GOAL])
        with self.assertRaises(ValueError):
            self.draw(walk, [bale_pack.WALK_SLUG])

    def test_plan_refuses_duplicates_and_unknown_items(self) -> None:
        with self.assertRaises(ValueError):
            quiet_walk([bale_pack.WALK_GOAL, bale_pack.WALK_GOAL])
        with self.assertRaises(ValueError):
            quiet_walk(["walk.goal"])

    def test_a_heading_per_section_not_per_item(self) -> None:
        plan = list(bale_pack.WALK_ORDER)
        out = self.draw(quiet_walk(plan), plan)
        headings = [ln for ln in out.splitlines() if ln.startswith("── ")]
        self.assertEqual([h.split()[1] for h in headings],
                         ["Session", "Scope", "Brief"])
        self.assertNotIn("[session]", out)

    def test_every_order_item_has_a_section(self) -> None:
        self.assertEqual(set(bale_pack.WALK_ORDER),
                         set(bale_pack.WALK_SECTION_OF))
        self.assertEqual(set(bale_pack.WALK_SECTION_OF.values()),
                         set(bale_pack.WALK_SECTION_HEADINGS))

    def test_ask_list_states_none_then_done(self) -> None:
        walk = quiet_walk([bale_pack.WALK_CONSTRAINT])
        with fed_input(["one", "two", ""]) as prompts, \
                contextlib.redirect_stdout(io.StringIO()):
            items = walk.ask_list(empty="none")
        self.assertEqual(items, ["one", "two"])
        self.assertTrue(prompts[0].endswith("Enter = none > "))
        self.assertTrue(prompts[1].endswith("Enter = done > "))


# ---------------------------------------------------------------------------
# Answers keep their meaning (in-process, fixed answer streams)
# ---------------------------------------------------------------------------

def shape_args(**overrides) -> Namespace:
    base = dict(read_only=False, work_class=None, write=[])
    base.update(overrides)
    return Namespace(**base)


SHAPE_PLAN = [bale_pack.WALK_SHAPE, bale_pack.WALK_WRITE,
              bale_pack.WALK_CHECKPOINT, bale_pack.WALK_EXCLUDE]


class SessionShapeAnswersTest(unittest.TestCase):
    def answer(self, answers: list, **overrides):
        args = shape_args(**overrides)
        walk = quiet_walk(SHAPE_PLAN)
        with fed_input(answers) as prompts, \
                contextlib.redirect_stdout(io.StringIO()) as out:
            bale_pack._wizard_input_session_shape(args, walk)
        return args, walk, prompts, out.getvalue()

    def test_combined_letters_and_spellings(self) -> None:
        cases = {"c": "code", "code": "code", "d": "doc", "doc": "doc",
                 "t": "contract-doc", "contract-doc": "contract-doc",
                 "m": "meta", "META": "meta", "x": "mixed",
                 "mixed": "mixed", "": "mixed"}
        for typed, work_class in cases.items():
            args, _, _, _ = self.answer([typed])
            self.assertEqual(args.work_class, work_class, typed)
            self.assertFalse(args.read_only, typed)

    def test_combined_read_only_drops_forecast_and_checkpoint(self) -> None:
        for typed in ("r", "read-only", "readonly", "R"):
            args, walk, _, _ = self.answer([typed])
            self.assertTrue(args.read_only, typed)
            self.assertIsNone(args.work_class)
            self.assertEqual(walk.plan,
                             [bale_pack.WALK_SHAPE, bale_pack.WALK_EXCLUDE])

    def test_combined_unknown_answer_reprompts_with_a_hint(self) -> None:
        args, _, prompts, out = self.answer(["?", "y", "t"])
        self.assertEqual(args.work_class, "contract-doc")
        self.assertEqual(len(prompts), 3)
        self.assertIn("! Type c, d, t, m, x, or r", out)

    def test_write_given_asks_work_class_only(self) -> None:
        args, _, _, out = self.answer(["r", ""], write=["src"])
        # 'r' is not an answer here (the flag declared lands-changes).
        self.assertEqual(args.work_class, "mixed")
        self.assertFalse(args.read_only)
        self.assertIn("--write given", out)

    def test_work_class_given_asks_shape_only(self) -> None:
        lands = {"": False, "y": False, "yes": False, "n": True,
                 "no": True, "r": True, "read-only": True,
                 "readonly": True}
        for typed, read_only in lands.items():
            args, _, _, _ = self.answer([typed], work_class="doc")
            self.assertEqual(args.read_only, read_only, typed)
            self.assertEqual(args.work_class, "doc")

    def test_both_flags_ask_nothing(self) -> None:
        _, _, prompts, out = self.answer([], work_class="doc",
                                         write=["src"])
        self.assertEqual(prompts, [])
        self.assertEqual(out, "")


class ShapeChoiceTest(unittest.TestCase):
    """Session choice-prompt-convergence: the shape question asks through
    bale_wizard's choice primitive — lettered rows, Enter's row marked,
    '? help' offered — and '?' is the only answer whose meaning moved
    (it re-asked with a warning; it now shows help and asks again)."""

    FORMS = {
        # name: (overrides, every answer the form takes, a non-answer)
        "combined": ({}, ["c", "code", "d", "doc", "t", "contract-doc",
                          "m", "META", "x", "mixed", "", "r", "read-only",
                          "readonly", "R"], "y"),
        "write given": ({"write": ["src"]},
                        ["c", "code", "d", "doc", "t", "contract-doc", "m",
                         "meta", "x", "mixed", ""], "r"),
        "work-class given": ({"work_class": "doc"},
                             ["", "y", "yes", "n", "no", "r", "read-only",
                              "readonly", "YES"], "x"),
    }

    def run_shape(self, answers: list, **overrides):
        args = shape_args(**overrides)
        walk = quiet_walk(SHAPE_PLAN)
        with fed_input(answers) as prompts, \
                contextlib.redirect_stdout(io.StringIO()) as out:
            bale_pack._wizard_input_session_shape(args, walk)
        return (args.read_only, args.work_class, walk.plan), prompts, \
            out.getvalue()

    def test_a_question_mark_first_changes_no_answer(self) -> None:
        for form, (overrides, answers, _bad) in self.FORMS.items():
            for typed in answers:
                with self.subTest(form=form, typed=typed):
                    plain, _p, _o = self.run_shape([typed], **overrides)
                    helped, prompts, out = self.run_shape(["?", typed],
                                                          **overrides)
                    self.assertEqual(helped, plain)
                    self.assertEqual(len(prompts), 2)
                    self.assertIn("── shape ", out, msg="the help block")
                    self.assertNotIn("! Type", out)

    def test_a_non_answer_still_reasks_with_the_hint(self) -> None:
        hints = {"combined": "! Type c, d, t, m, x, or r",
                 "write given": "! Type c, d, t, m, or x",
                 "work-class given": "! Type y or n"}
        for form, (overrides, _answers, bad) in self.FORMS.items():
            with self.subTest(form=form):
                _r, prompts, out = self.run_shape([bad, ""], **overrides)
                self.assertEqual(len(prompts), 2)
                self.assertIn(hints[form], out)

    def test_digits_are_not_picks_here(self) -> None:
        """Lettered rows offer no numbers: '1' re-asks with the hint, as
        it always did, rather than picking the first row."""
        result, prompts, out = self.run_shape(["1", "d"])
        self.assertEqual(result[1], "doc")
        self.assertEqual(len(prompts), 2)
        self.assertIn("! Type c, d, t, m, x, or r", out)
        self.assertNotIn("no alternative", out)

    def test_the_screen_reads_like_config_inits_alternatives(self) -> None:
        _r, prompts, out = self.run_shape([""])
        rows = [ln.strip() for ln in out.splitlines()
                if ln.strip().startswith("[")]
        self.assertEqual(rows, [
            "[c] code", "[d] doc", "[t] contract-doc", "[m] meta",
            "[x] mixed  (Enter)",
            "[r] read-only  (nothing lands: discussion, orchestration, "
            "audit)"])
        self.assertTrue(prompts[0].endswith(
            "Enter = mixed · c/d/t/m/x/r picks · ? help > "))
        _r, prompts, out = self.run_shape([""], work_class="doc")
        rows = [ln.strip() for ln in out.splitlines()
                if ln.strip().startswith("[")]
        self.assertEqual(rows[0], "[y] yes  (it lands changes, Enter)")
        self.assertTrue(rows[1].startswith("[n] no  (read-only"))
        self.assertTrue(prompts[0].endswith(
            "Enter = yes · y/n picks · ? help > "))
        for line in out.splitlines():
            self.assertLessEqual(len(line), bale_wizard.WIDTH, line)

    def test_eof_still_aborts_the_pack(self) -> None:
        saved = sys.modules["__main__"]
        fake = types.ModuleType("__main__")

        def fail(msg):
            raise SystemExit(msg)
        fake.fail = fail
        sys.modules["__main__"] = fake
        try:
            with self.assertRaises(SystemExit) as caught:
                self.run_shape([])
        finally:
            sys.modules["__main__"] = saved
        self.assertIn("aborted at wizard prompt", str(caught.exception))


class CheckpointPickerAnswersTest(unittest.TestCase):
    """Every picker answer keeps its meaning on the choice primitive
    (session choice-prompt-convergence; brief outcome 2): a number in
    range picks; Enter packs without one; any other answer — '?'
    included — is a path; an out-of-range number re-asks unless a file of
    that name is in cwd, which is then the path. The pty suites
    (test_checkpoint_file_flag) pin the same end to end; this pins the
    whole answer table in-process, with the config, the Enter outcome,
    and the path resolution stood in."""

    def setUp(self) -> None:
        from unittest import mock
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-picker-")
        self.cwd = Path(self._tmp.name).resolve()
        self._saved_cwd = os.getcwd()
        os.chdir(self.cwd)
        for i, name in enumerate(("older.sh", "newer.sh")):
            path = self.cwd / name
            path.write_text(f"#!/bin/sh\nexit {i}\n", encoding="utf-8")
            os.utime(path, (1_780_000_000 + i, 1_780_000_000 + i))
        self.resolved: list = []

        def locate(raw, repo, cwd):
            self.resolved.append(raw)
            if raw.startswith("/") or (cwd / raw).is_file():
                return Path(raw), b"#!/bin/sh\n", None
            return None, None, f"could not read --checkpoint-file {raw!r}"

        # The live module bale_pack's lazy `import bale_config` will get:
        # another suite in the same run may have re-registered it.
        bale_config = sys.modules["bale_config"]
        self._patches = [
            mock.patch.object(bale_config, "merged_config",
                              lambda repo: {}),
            mock.patch.object(bale_config, "get_validation_base",
                              lambda cfg: SID_BASE),
            mock.patch.object(bale_config, "get_apply_search_paths",
                              lambda cfg: []),
            mock.patch.object(bale_pack, "_checkpoint_enter_outcome",
                              lambda repo, base, slug: None),
            mock.patch.object(bale_pack, "locate_and_read_checkpoint_file",
                              locate),
        ]
        for patch in self._patches:
            patch.start()

    def tearDown(self) -> None:
        for patch in self._patches:
            patch.stop()
        os.chdir(self._saved_cwd)
        self._tmp.cleanup()

    def pick(self, answers: list):
        self.resolved.clear()
        args = Namespace(read_only=False, checkpoint_file=None, slug="s")
        walk = quiet_walk([bale_pack.WALK_CHECKPOINT])
        with fed_input(answers) as prompts, \
                contextlib.redirect_stdout(io.StringIO()) as out:
            bale_pack._wizard_input_checkpoint_file(args, self.cwd, walk)
        return args.checkpoint_file, prompts, out.getvalue()

    def test_numbers_in_range_pick_newest_first(self) -> None:
        newer, older = str(self.cwd / "newer.sh"), str(self.cwd / "older.sh")
        for typed, expected in (("1", newer), ("2", older), ("02", older),
                                ("١", newer)):
            with self.subTest(typed=typed):
                picked, prompts, _o = self.pick([typed])
                self.assertEqual(picked, expected)
                self.assertEqual(len(prompts), 1)

    def test_enter_packs_without_one(self) -> None:
        picked, prompts, _o = self.pick([""])
        self.assertIsNone(picked)
        self.assertEqual(self.resolved, [])

    def test_out_of_range_reasks_naming_the_range(self) -> None:
        picked, prompts, out = self.pick(["7", "0", "1"])
        self.assertEqual(picked, str(self.cwd / "newer.sh"))
        self.assertEqual(len(prompts), 3)
        self.assertIn("no candidate 7; pick 1-2", " ".join(out.split()))
        self.assertIn("no candidate 0", out)
        self.assertEqual(self.resolved, [str(self.cwd / "newer.sh")],
                         msg="a re-asked number is never resolved")

    def test_out_of_range_names_a_cwd_file_literally(self) -> None:
        (self.cwd / "7").write_text("#!/bin/sh\n", encoding="utf-8")
        picked, prompts, out = self.pick(["7"])
        self.assertEqual((picked, len(prompts)), ("7", 1))
        self.assertNotIn("no candidate", out)

    def test_a_question_mark_is_a_path(self) -> None:
        picked, prompts, out = self.pick(["?", "1"])
        self.assertEqual(self.resolved[0], "?")
        self.assertIn("could not read --checkpoint-file '?'", out)
        self.assertNotIn("? help", prompts[0])
        (self.cwd / "?").write_text("#!/bin/sh\n", encoding="utf-8")
        picked, _p, _o = self.pick(["?"])
        self.assertEqual(picked, "?")

    def test_other_answers_are_paths(self) -> None:
        for typed in ("newer.sh", "²", "1:2", "-1"):
            with self.subTest(typed=typed):
                _picked, _p, _o = self.pick([typed, ""])
                self.assertEqual(self.resolved[0], typed)

    def test_the_screen_and_prompt(self) -> None:
        _picked, prompts, out = self.pick([""])
        self.assertIn(f"[1] {self.cwd / 'newer.sh'}", out)
        self.assertIn(f"[2] {self.cwd / 'older.sh'}", out)
        self.assertIn("sha256 ", out)
        self.assertIn("Checkpoint file to commit for this session?", out)
        self.assertTrue(prompts[0].endswith("Enter = none · 1-2 picks > "))

    def test_no_candidates_asks_a_plain_path(self) -> None:
        for name in ("older.sh", "newer.sh"):
            (self.cwd / name).unlink()
        (self.cwd / "3").write_text("#!/bin/sh\n", encoding="utf-8")
        picked, prompts, out = self.pick(["3"])
        self.assertEqual(picked, "3", msg="a digit is a path with no list")
        self.assertTrue(prompts[0].endswith("a path, or Enter = none > "))
        self.assertNotIn("[1]", out)


class PackDropReasonTest(unittest.TestCase):
    """pack_drop_reason is walk_for_pack's filter chain, short of
    --include — one implementation, which config init's .baleignore
    suggestions count through too (session choice-prompt-convergence)."""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-dropreason-")
        self.repo = Path(self._tmp.name)
        self.files = {
            "src/app.py": "ok", "node_modules/x.js": "", "keys.pem": "",
            ".aws/credentials": "", "web/.npmrc": "_authToken=1\n",
            "web/plain/.npmrc": "registry=x\n",
            "claude/checkpoints/old.sh": "", "plan.bale-bundle": "",
            "data/a.csv": "", "notes.md": "",
        }
        for rel, body in self.files.items():
            path = self.repo / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(body, encoding="utf-8")
        cli = _load_cli()
        self.matcher = cli.BaleignoreMatcher.from_lines(["data/"])

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_each_reason_in_chain_order(self) -> None:
        reason = lambda rel: bale_pack.pack_drop_reason(  # noqa: E731
            rel, self.repo, matcher=self.matcher,
            checkpoint_exclude="claude/checkpoints")
        self.assertEqual(
            {rel: reason(rel) for rel in self.files} | {"gone.txt":
                                                        reason("gone.txt")},
            {"src/app.py": None, "notes.md": None,
             "web/plain/.npmrc": None,
             "node_modules/x.js": bale_pack.DROP_BAKED_IN_DIR,
             "keys.pem": bale_pack.DROP_SECRET,
             ".aws/credentials": bale_pack.DROP_SECRET,
             "web/.npmrc": bale_pack.DROP_SECRET,
             "claude/checkpoints/old.sh": bale_pack.DROP_CHECKPOINT,
             "plan.bale-bundle": bale_pack.DROP_BUNDLE,
             "data/a.csv": bale_pack.DROP_BALEIGNORE,
             "gone.txt": bale_pack.DROP_NOT_A_FILE})
        self.assertIsNone(bale_pack.pack_drop_reason(
            "claude/checkpoints/old.sh", self.repo),
            msg="no basis configured, no checkpoint drop")

    def test_the_walk_ships_exactly_what_it_lets_through(self) -> None:
        from unittest import mock
        logged: list = []
        main = sys.modules["__main__"]
        with mock.patch.object(main, "log", logged.append, create=True):
            projection = bale_pack.walk_for_pack(
                self.repo, [], caps=bale_pack.PackCaps(), force=True,
                matcher=self.matcher, verbose=True,
                checkpoint_exclude="claude/checkpoints",
                listed=sorted(self.files) + ["gone.txt"])
        self.assertEqual(projection.files,
                         ["notes.md", "src/app.py", "web/plain/.npmrc"])
        self.assertIn("verbose: skip keys.pem (secret pattern)", logged)
        self.assertIn("verbose: skip data/a.csv (.baleignore / session "
                      "exclude)", logged)
        self.assertTrue(any(line.startswith("auto-excluded") and
                            "claude/checkpoints/old.sh" in line
                            for line in logged),
                        msg="the checkpoint drop is still logged loudly")


class ReadmeAnswersTest(unittest.TestCase):
    """The README y/N keeps confirm_yn(default_no=True)'s answer set:
    y/yes accept, anything else declines without re-asking, and EOF
    declines rather than aborting the pack."""

    def answer(self, answers: list):
        walk = quiet_walk([bale_pack.WALK_README])
        with fed_input(answers) as prompts, \
                contextlib.redirect_stdout(io.StringIO()):
            accepted = bale_pack._walk_input_readme(walk)
        return accepted, prompts

    def test_accepts(self) -> None:
        for typed in ("y", "Y", "yes", "YES", " y "):
            self.assertTrue(self.answer([typed])[0], typed)

    def test_declines_without_reasking(self) -> None:
        for typed in ("", "n", "no", "x", "maybe"):
            accepted, prompts = self.answer([typed, "y"])
            self.assertFalse(accepted, typed)
            self.assertEqual(len(prompts), 1, typed)

    def test_eof_declines(self) -> None:
        self.assertFalse(self.answer([])[0])


class SlugAnswersTest(unittest.TestCase):
    def setUp(self) -> None:
        # _walk_input_slug imports is_valid_slug and peek_session_id from
        # __main__; give it a stand-in __main__ for the in-process run.
        self._saved_main = sys.modules["__main__"]
        fake = types.ModuleType("__main__")
        fake.is_valid_slug = is_valid_slug
        fake.peek_session_id = lambda repo, slug: f"2026-10-03-{slug}-001"
        sys.modules["__main__"] = fake

    def tearDown(self) -> None:
        sys.modules["__main__"] = self._saved_main

    def answer(self, goal: str, answers: list):
        args = Namespace(goal=goal, slug=None)
        walk = quiet_walk([bale_pack.WALK_SLUG])
        with fed_input(answers) as prompts, \
                contextlib.redirect_stdout(io.StringIO()) as out:
            bale_pack._walk_input_slug(args, walk, Path("."))
        return args.slug, prompts, out.getvalue()

    def test_enter_takes_the_suggestion(self) -> None:
        slug, prompts, out = self.answer("Fix the README typo", [""])
        self.assertEqual(slug, "fix-readme-typo")
        self.assertTrue(prompts[0].endswith("Enter = fix-readme-typo > "))
        self.assertIn("Session id: 2026-10-03-fix-readme-typo-001", out)

    def test_a_typed_slug_wins(self) -> None:
        slug, _, _ = self.answer("Fix the README typo", ["typo"])
        self.assertEqual(slug, "typo")

    def test_invalid_slug_reprompts(self) -> None:
        slug, prompts, out = self.answer("Fix it", ["Bad_Slug", "ok"])
        self.assertEqual(slug, "ok")
        self.assertEqual(len(prompts), 2)
        self.assertIn("must be kebab-case", out)

    def test_enter_without_a_suggestion_reprompts_as_before(self) -> None:
        slug, prompts, out = self.answer("¿¡", ["", "named"])
        self.assertEqual(slug, "named")
        self.assertEqual(len(prompts), 2)
        self.assertTrue(prompts[0].endswith("slug > "))
        self.assertIn("A slug is required", out)


# ---------------------------------------------------------------------------
# The native log hold — bin/bale's logging section, in-process
# ---------------------------------------------------------------------------

class _TTY(io.StringIO):
    """A captured stream that says it is a terminal (no fileno, so the
    width comes from $COLUMNS or the 80-column fallback)."""

    def isatty(self) -> bool:
        return True


@contextlib.contextmanager
def columns(value):
    """Set (or, with None, unset) $COLUMNS for the block."""
    saved = os.environ.get("COLUMNS")
    if value is None:
        os.environ.pop("COLUMNS", None)
    else:
        os.environ["COLUMNS"] = str(value)
    try:
        yield
    finally:
        if saved is None:
            os.environ.pop("COLUMNS", None)
        else:
            os.environ["COLUMNS"] = saved


class NativeLogHoldTest(unittest.TestCase):
    """hold_log / release_log / log_held and fail()'s release, driven on
    a freshly loaded bin/bale (harness._load_cli) — no __main__ rebinding
    anywhere."""

    def setUp(self) -> None:
        self.cli = _load_cli()
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-loghold-")
        self.journal = Path(self._tmpdir.name) / "s.log"

    def tearDown(self) -> None:
        self.cli.release_log()
        self.cli.set_log_file(None)
        self._tmpdir.cleanup()

    def journal_lines(self) -> list:
        if not self.journal.is_file():
            return []
        # Each entry is "<timestamp> <line>"; keep the line.
        return [ln.split(" ", 1)[1] for ln in
                self.journal.read_text(encoding="utf-8").splitlines()]

    def test_held_lines_journal_now_and_print_at_release_in_order(self) -> None:
        self.cli.set_log_file(self.journal)
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.cli.hold_log()
            self.assertTrue(self.cli.log_holding())
            self.cli.log("one")
            self.cli.log("two", force=True)
            self.assertEqual(out.getvalue(), "", "nothing prints while held")
            self.assertEqual(self.journal_lines(),
                             ["[bale] one", "[bale] FORCE: two"],
                             "journaled at the moment of logging")
            self.cli.release_log()
        self.assertEqual(out.getvalue(),
                         "\n[bale] one\n[bale] FORCE: two\n",
                         "one blank separator, then the lines in order")
        self.assertFalse(self.cli.log_holding())
        self.assertEqual(len(self.journal_lines()), 2,
                         "release prints; it does not journal again")

    def test_force_line_queues_for_the_session_log_while_held(self) -> None:
        self.cli._pending_log_lines.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            self.cli.hold_log()
            self.cli.log("override", force=True)
            self.cli.log("ordinary")
            self.assertEqual(self.cli._pending_log_lines,
                             ["[bale] FORCE: override"])
            self.cli.release_log()
        self.cli.set_log_file(self.journal)
        self.assertEqual(self.journal_lines(), ["[bale] FORCE: override"])

    def test_fail_releases_before_its_error_line(self) -> None:
        both = io.StringIO()
        with contextlib.redirect_stdout(both), \
                contextlib.redirect_stderr(both), \
                self.assertRaises(SystemExit) as ctx:
            self.cli.hold_log()
            self.cli.log("context")
            self.cli.fail("refused", 3)
        self.assertEqual(ctx.exception.code, 3)
        self.assertEqual(both.getvalue(),
                         "\n[bale] context\n[bale] error: refused\n")
        self.assertFalse(self.cli.log_holding())

    def test_release_is_idempotent_and_silent_when_empty(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()) as out:
            self.cli.release_log()
            self.cli.hold_log()
            self.cli.hold_log()  # one level: a second hold is a no-op
            self.cli.release_log()
            self.cli.release_log()
            self.cli.log("after")
        self.assertEqual(out.getvalue(), "[bale] after\n")

    def test_log_held_releases_on_the_way_out_of_an_exception(self) -> None:
        with contextlib.redirect_stdout(io.StringIO()) as out, \
                self.assertRaises(RuntimeError):
            with self.cli.log_held():
                self.cli.log("waited")
                raise RuntimeError("boom")
        self.assertEqual(out.getvalue(), "\n[bale] waited\n")
        self.assertFalse(self.cli.log_holding())

    def test_no_module_under_bin_rebinds_log_or_fail(self) -> None:
        """Outcome 1: the rebinding is retired — nothing under bin/
        assigns a `log` or `fail` attribute, and WalkLogHold is gone."""
        assign = re.compile(r"\.\s*(log|fail)\s*=(?!=)")
        for path in sorted(BIN_DIR.iterdir()):
            if path.suffix not in ("", ".py") or not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            for n, line in enumerate(text.splitlines(), 1):
                code = line.split("#", 1)[0]
                self.assertIsNone(assign.search(code),
                                  f"{path.name}:{n}: {line.strip()}")
        self.assertFalse(hasattr(bale_pack, "WalkLogHold"))


class LogDisplayWrapTest(unittest.TestCase):
    """log()'s terminal layout: wrap_log_line (pure) and log() on a
    terminal vs a pipe, wrapping on vs off, with the journal untouched
    either way."""

    def setUp(self) -> None:
        self.cli = _load_cli()

    def tearDown(self) -> None:
        self.cli.set_log_display_wrap(False)

    def test_short_lines_and_no_terminal_are_untouched(self) -> None:
        long = "[bale] " + "word " * 40
        self.assertEqual(self.cli.wrap_log_line(long, None), long)
        self.assertEqual(self.cli.wrap_log_line("[bale] short", 80),
                         "[bale] short")

    def test_wraps_under_the_text_after_the_prefix(self) -> None:
        line = ("[bale] argv-only pack gates passed before any exchange "
                "(slug/goal, forecast existence, bundle-file naming, cap "
                "values, checkpoint blindness read half — the forecast "
                "half runs post-wizard)")
        out = self.cli.wrap_log_line(line, 80).split("\n")
        self.assertGreater(len(out), 1)
        self.assertTrue(all(len(ln) <= 80 for ln in out), out)
        self.assertTrue(out[0].startswith("[bale] argv-only pack gates"))
        self.assertTrue(all(ln.startswith(" " * 7) and ln[7] != " "
                            for ln in out[1:]), out)
        self.assertEqual(" ".join(" ".join(out).split()),
                         " ".join(line.split()), "words kept, in order")

    def test_never_breaks_a_token(self) -> None:
        token = "a" * 120
        out = self.cli.wrap_log_line(f"[bale] see {token} now", 80)
        self.assertIn(" " * 7 + token, out.split("\n"),
                      "the token runs long on its own line, whole")
        self.assertIn("2026-10-04-very-long-session-slug-for-width-001",
                      self.cli.wrap_log_line(
                          "[bale] " + "x " * 30 + "closed "
                          "2026-10-04-very-long-session-slug-for-width-001",
                          60))

    def test_later_physical_lines_keep_their_indent(self) -> None:
        line = "[bale] head\n    " + "detail " * 20
        out = self.cli.wrap_log_line(line, 60).split("\n")
        self.assertEqual(out[0], "[bale] head")
        self.assertTrue(all(ln.startswith("    ") for ln in out[1:]))
        self.assertTrue(all(len(ln) <= 60 for ln in out))

    def test_width_follows_columns_then_falls_back_to_80(self) -> None:
        tty = _TTY()
        with columns(None):
            self.assertEqual(self.cli.log_display_width(tty), 80)
        with columns(132):
            self.assertEqual(self.cli.log_display_width(tty), 132)
        with columns(10):
            self.assertEqual(self.cli.log_display_width(tty),
                             self.cli.LOG_WRAP_MIN_WIDTH)
        with columns(80):
            self.assertIsNone(self.cli.log_display_width(io.StringIO()))

    def test_log_wraps_on_a_terminal_and_journals_one_entry(self) -> None:
        msg = "read-only sweep: " + "something long " * 10
        with tempfile.TemporaryDirectory() as tmp:
            journal = Path(tmp) / "s.log"
            self.cli.set_log_file(journal)
            try:
                with columns(80):
                    tty, pipe, off = _TTY(), io.StringIO(), _TTY()
                    self.assertFalse(self.cli.set_log_display_wrap(True),
                                     "off by default")
                    with contextlib.redirect_stdout(tty):
                        self.cli.log(msg)
                    with contextlib.redirect_stdout(pipe):
                        self.cli.log(msg)
                    self.assertTrue(self.cli.set_log_display_wrap(False))
                    with contextlib.redirect_stdout(off):
                        self.cli.log(msg)
            finally:
                self.cli.set_log_file(None)
            entries = journal.read_text(encoding="utf-8").splitlines()
        self.assertEqual(pipe.getvalue(), f"[bale] {msg}\n",
                         "piped output is byte-identical to before")
        self.assertEqual(off.getvalue(), f"[bale] {msg}\n",
                         "with wrapping off a terminal gets the line whole")
        shown = tty.getvalue().splitlines()
        self.assertGreater(len(shown), 1)
        self.assertTrue(all(len(ln) <= 80 for ln in shown))
        self.assertEqual(len(entries), 3, "one journal entry per log()")
        self.assertTrue(all(e.endswith(f"[bale] {msg}") for e in entries))


class SweepPromptLayoutTest(unittest.TestCase):
    """The read-only sweep's y/N (confirm_yn_decision(..., wrap=True)):
    width only. Every answer decides exactly what the one-line prompt
    decides, nothing re-asks, and the prompt fits 80 columns with the
    typed answer."""

    SID = "2026-10-04-a-twenty-char-001"
    ANSWERS = ["", "y", "Y", "yes", "YES", " yes ", "n", "no", "nope",
               "maybe", "yess", EOF, "^C"]

    def setUp(self) -> None:
        self.cli = _load_cli()
        self.prompt = (
            f"Close open read-only session {self.SID} as closed-read-only? "
            f"A read-only session lands nothing, so no work is lost; its "
            f"registry entry and .bale/sessions/ state are removed and a "
            f"closure record is written.")

    def decide(self, answer: str, *, wrap: bool):
        prompts: list = []

        def fake_input(prompt=""):
            prompts.append(prompt)
            if answer == EOF:
                raise EOFError
            if answer == "^C":
                raise KeyboardInterrupt
            return answer

        saved = builtins.input
        builtins.input = fake_input
        try:
            with columns(80), contextlib.redirect_stdout(_TTY()) as out:
                decision = self.cli.confirm_yn_decision(
                    self.prompt, default_no=False, wrap=wrap)
        finally:
            builtins.input = saved
        return decision, prompts, out.getvalue()

    def test_every_answer_means_what_it_meant(self) -> None:
        for answer in self.ANSWERS:
            with self.subTest(answer=answer):
                wrapped, prompts, _ = self.decide(answer, wrap=True)
                plain, _, _ = self.decide(answer, wrap=False)
                self.assertEqual(wrapped, plain)
                self.assertEqual(len(prompts), 1, "nothing re-asks")
        accepts = [a for a in self.ANSWERS
                   if self.decide(a, wrap=True)[0].accepted]
        self.assertEqual(accepts, ["", "y", "Y", "yes", "YES", " yes "])

    def test_the_prompt_fits_80_columns_with_its_answer(self) -> None:
        _, prompts, printed = self.decide("yes", wrap=True)
        lines = printed.splitlines() + [prompts[0] + "yes"]
        self.assertGreater(len(lines), 1)
        self.assertTrue(all(len(ln) <= 80 for ln in lines), lines)
        self.assertTrue(lines[0].startswith(
            f"Close open read-only session {self.SID}"))
        self.assertTrue(prompts[0].endswith("[Y/n] "))
        self.assertEqual(" ".join(" ".join(lines[:-1] + [prompts[0]]).split()),
                         " ".join((self.prompt + " [Y/n]").split()))

    def test_unwrapped_and_piped_prompts_are_one_line(self) -> None:
        _, prompts, printed = self.decide("", wrap=False)
        self.assertEqual((printed, prompts),
                         ("", [self.prompt + " [Y/n] "]))
        self.assertEqual(
            self.cli.layout_yn_prompt(self.prompt + " [Y/n]", None),
            [self.prompt + " [Y/n]"])


# ---------------------------------------------------------------------------
# End to end on a pty
# ---------------------------------------------------------------------------

class _PtyFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-packwalk-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def commit(self, files: dict, message: str) -> None:
        for rel, body in files.items():
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(body, encoding="utf-8")
        run_checked(["git", "add", *files], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", message], cwd=self.repo,
                    env=self.genv)

    def configure_sid_base(self) -> None:
        self.commit({"bale.toml": f'[validation]\nbase = "{SID_BASE}"\n'},
                    "configure a per-session checkpoint base")

    def walk(self, answers: list, *extra: str):
        return run_walk_pty(self.install, ["pack", *extra], cwd=self.repo,
                            env=self.env, answers=answers)

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return sorted(d.name for d in root.iterdir()
                      if (d / "open").is_file())

    def assert_layout(self, span: list) -> None:
        """Outcome 2 and outcome 3 over one walk span."""
        for line in span:
            if len(line) > bale_wizard.WIDTH:
                self.assertTrue(bale_wizard.names_absolute_path(line),
                                f"{len(line)} columns: {line!r}")
            self.assertFalse(line.startswith("[bale] "),
                             f"[bale] line inside the walk: {line!r}")


class FullWalkTest(_PtyFixture):
    def test_plain_walk_fits_and_lands_the_answers(self) -> None:
        code, out = self.walk(
            ["Tidy the hello file for the demo", "", "c", "hello.txt", "",
             "keep it tiny", "", "docs/", "", ""])
        self.assertEqual(code, 0, out)
        span = walk_span(out, last=README_PROMPT)
        self.assert_layout(span)
        self.assertEqual(
            [k for _, _, k in item_headers(span)],
            ["goal", "--slug", "shape", "--write", "--exclude",
             "--constraint", "--out-of-scope", "readme"])
        self.assertTrue(all(t == 8 for _, t, _ in item_headers(span)))
        sids = self.open_sids()
        self.assertEqual(len(sids), 1)
        self.assertIn("-tidy-hello-file-demo-", sids[0],
                      "Enter at the slug took the goal-derived slug")
        manifest = self.request_manifest(sids[0])
        self.assertEqual(manifest["goal"], "Tidy the hello file for the demo")
        self.assertEqual(manifest["constraints"], ["keep it tiny"])
        self.assertEqual(manifest["out_of_scope"], ["docs/"])
        self.assertEqual(manifest["resolved_scope"], ["hello.txt"])
        self.assertEqual(manifest["provenance"]["work_class"], "code")

    def request_manifest(self, sid: str) -> dict:
        import json
        import tarfile
        tarball = (self.repo / ".bale" / "outbox"
                   / f"request-{sid}.tar.gz")
        with tarfile.open(tarball) as tf:
            member = next(m for m in tf.getmembers()
                          if m.name.endswith("/manifest.json")
                          and m.name.count("/") == 1)
            return json.load(tf.extractfile(member))

    def test_read_only_answer_renumbers_the_rest(self) -> None:
        self.configure_sid_base()
        code, out = self.walk(["Audit the tree", "audit", "r", "", "",
                               "", ""])
        self.assertEqual(code, 0, out)
        span = walk_span(out, last=README_PROMPT)
        self.assert_layout(span)
        headers = item_headers(span)
        # Nine planned in a {sid} project (forecast and checkpoint
        # included); the read-only answer drops those two, and the items
        # still to come count against the seven that remain.
        self.assertEqual(headers[:3], [(1, 9, "goal"), (2, 9, "--slug"),
                                       (3, 9, "shape")])
        self.assertEqual(headers[3:],
                         [(4, 7, "--exclude"), (5, 7, "--constraint"),
                          (6, 7, "--out-of-scope"), (7, 7, "readme")])
        self.assertNotIn("Where will changes land?", out)
        self.assertNotIn("Checkpoint file to commit", out)

    def test_eof_at_the_goal_aborts_the_pack(self) -> None:
        code, out = self.walk([EOF])
        self.assertNotEqual(code, 0)
        self.assertIn("aborted at wizard prompt", out)
        self.assertEqual(self.open_sids(), [])

    def test_eof_at_the_readme_question_declines_and_packs(self) -> None:
        code, out = self.walk(["Tidy hello", "", "", "", "", "", "", EOF])
        self.assertEqual(code, 0, out)
        self.assertIn("packing without a README", out)
        self.assertEqual(len(self.open_sids()), 1)


class HeldLogLinesTest(_PtyFixture):
    def test_gate_lines_wait_for_the_readme_question(self) -> None:
        """In a {sid} project the post-walk blindness gate logs; those
        lines now print after the README question, not above it."""
        self.configure_sid_base()
        (self.repo / "cp.sh").write_text("#!/bin/sh\nexit 0\n",
                                         encoding="utf-8")
        code, out = self.walk(["Grade with a checkpoint", "graded", "", "",
                               "1", "", "", "", ""])
        self.assertEqual(code, 0, out)
        span = walk_span(out, last=README_PROMPT)
        self.assert_layout(span)
        readme_at = out.index(README_PROMPT)
        self.assertGreater(out.rindex(BLINDNESS_LOG_MARKER), readme_at,
                           "the post-walk gate line replays after the walk")
        self.assertIn("[1] " + str((self.repo / "cp.sh").resolve()), out)
        self.assertIn("not committed yet", out)

    def test_refusal_prints_held_lines_before_its_error(self) -> None:
        """A post-walk refusal still reads its context lines first."""
        self.configure_sid_base()
        (self.repo / "cp.sh").write_text("#!/bin/sh\nexit 0\n",
                                         encoding="utf-8")
        first = run_bale(self.install,
                         ["pack", "whole-tree sibling", "--slug", "sib",
                          "--no-readme", "--checkpoint-file", "cp.sh"],
                         cwd=self.repo, env=self.env)
        self.assertEqual(first.returncode, 0, first.stderr)
        code, out = self.walk(["Collide with the sibling", "collide", "",
                               "", "", "", "", ""])
        self.assertNotEqual(code, 0, out)
        span = walk_span(out, last="Enter = none > ")
        self.assert_layout(span)
        error_at = out.index("[bale] error:")
        self.assertLess(out.rindex(BLINDNESS_LOG_MARKER), error_at)
        self.assertGreater(out.rindex(BLINDNESS_LOG_MARKER),
                           out.index(TITLE_MARKER))

    def test_read_only_sweep_lines_wait_for_the_readme_question(self) -> None:
        """The sweep's prompt stays where it was (between the walk's list
        questions and its README question) and, since session log-hold,
        fits the width with the rest of the span; its log lines move
        after the walk."""
        ro = run_bale(self.install,
                      ["pack", "an earlier desk", "--slug", "desk",
                       "--read-only", "--no-readme"],
                      cwd=self.repo, env=self.env)
        self.assertEqual(ro.returncode, 0, ro.stderr)
        earlier = self.open_sids()
        self.assertEqual(len(earlier), 1)
        code, out = self.walk(["A later desk", "desk-two", "r", "", "", "",
                               "", ""])
        self.assertEqual(code, 0, out)
        self.assertIn(SWEEP_PROMPT_MARKER, out)
        span = walk_span(out, last=README_PROMPT)
        self.assertTrue(any(SWEEP_PROMPT_MARKER in ln for ln in span))
        self.assert_layout(span)
        closed = f"[bale] read-only sweep: closed {earlier[0]}"
        self.assertGreater(out.index(closed), out.index(README_PROMPT))
        self.assertTrue(any(ln.startswith(closed) and ln.endswith(".json)")
                            for ln in out.split("\n")),
                        "a held line prints whole, as it always did")
        self.assertNotIn(earlier[0], self.open_sids())



class PreWalkWidthTest(_PtyFixture):
    """Outcome 4 (session log-hold): on an 80-column terminal the
    [bale] lines pack prints before the walk's first question fit —
    bin/bale's log() wraps them for display — while piped output keeps
    each logged line whole."""

    LONG_SID = "2026-10-04-clipboard-paste-blocks-and-a-long-tail-001"
    GATES = "[bale] argv-only pack gates passed before any exchange"

    def pre_title(self, out: str) -> list:
        lines = out.split("\n")
        return lines[:next(i for i, ln in enumerate(lines)
                           if TITLE_MARKER in ln)]

    def assert_fits(self, lines: list) -> None:
        for line in lines:
            if len(line) > bale_wizard.WIDTH:
                self.assertTrue(bale_wizard.names_absolute_path(line),
                                f"{len(line)} columns: {line!r}")

    def test_pre_walk_lines_fit_and_keep_their_words(self) -> None:
        run_checked(["git", "tag", f"applied/{self.LONG_SID}"],
                    cwd=self.repo, env=self.genv)
        code, out = self.walk(["Tidy hello", "", "", "", "", "", "", ""])
        self.assertEqual(code, 0, out)
        before = self.pre_title(out)
        self.assert_fits(before)
        joined = " ".join(" ".join(before).split())
        self.assertIn(f"[bale] tree position: branch ", joined)
        self.assertIn(f"latest applied {self.LONG_SID}", joined)
        self.assertIn(self.GATES + " (slug/goal, forecast existence, "
                      "bundle-file naming, cap values, checkpoint "
                      "blindness read half — the forecast half runs "
                      "post-wizard)", joined)
        self.assertTrue(any(ln.startswith(" " * 7) and ln.strip()
                            for ln in before),
                        "a wrapped line hangs under its text")

    def test_fully_specified_read_only_sweep_prompt_fits(self) -> None:
        ro = run_bale(self.install,
                      ["pack", "an earlier desk", "--slug", "desk",
                       "--read-only", "--no-readme"],
                      cwd=self.repo, env=self.env)
        self.assertEqual(ro.returncode, 0, ro.stderr)
        earlier = self.open_sids()
        code, out = run_walk_pty(
            self.install,
            ["pack", "a later desk", "--slug", "desk-two",
             "--include", "hello.txt", "--no-readme", "--read-only"],
            cwd=self.repo, env=self.env, answers=["n"])
        self.assertEqual(code, 0, out)
        lines = out.split("\n")
        prompt_end = next(i for i, ln in enumerate(lines)
                          if "[Y/n]" in ln)
        self.assertTrue(any(SWEEP_PROMPT_MARKER in ln
                            for ln in lines[:prompt_end + 1]))
        self.assert_fits(lines[:prompt_end + 1])
        self.assertTrue(lines[prompt_end].endswith("[Y/n] n"),
                        "the typed answer follows the suffix")
        self.assertIn(earlier[0], self.open_sids(),
                      "'n' declined: the earlier desk stays open")

    def test_piped_pack_keeps_each_logged_line_whole(self) -> None:
        r = run_bale(self.install,
                     ["pack", "a piped pack", "--slug", "piped",
                      "--include", "hello.txt", "--no-readme"],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, r.stderr)
        gates = [ln for ln in r.stdout.splitlines()
                 if ln.startswith(self.GATES)]
        self.assertEqual(len(gates), 1, r.stdout)
        self.assertTrue(gates[0].endswith("checkpoint blindness)"),
                        gates[0])
        self.assertGreater(len(gates[0]), bale_wizard.WIDTH,
                           "unwrapped when stdout is not a terminal")

if __name__ == "__main__":
    unittest.main()
