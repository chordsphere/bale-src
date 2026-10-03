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
  post-walk gates' log lines are held (WalkLogHold) and replay after the
  README question, and before the error line of a refusal.
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
    PTY_TIMEOUT,
    SUBPROCESS_TIMEOUT,
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
# WalkLogHold — the hold/replay mechanics, in-process
# ---------------------------------------------------------------------------

class WalkLogHoldTest(unittest.TestCase):
    def setUp(self) -> None:
        self._saved_main = sys.modules["__main__"]
        self.events: list = []
        fake = types.ModuleType("__main__")

        def log(msg, *, force=False):
            self.events.append(("log", msg, force))

        def fail(msg, code=1):
            self.events.append(("fail", msg, code))
            raise SystemExit(code)

        fake.log, fake.fail = log, fail
        self.real_log, self.real_fail = log, fail
        self.main = fake
        sys.modules["__main__"] = fake

    def tearDown(self) -> None:
        sys.modules["__main__"] = self._saved_main

    def test_lines_hold_then_replay_in_order_with_force(self) -> None:
        hold = bale_pack.WalkLogHold()
        hold.hold()
        self.main.log("one")
        self.main.log("two", force=True)
        self.assertEqual(self.events, [])
        with contextlib.redirect_stdout(io.StringIO()) as out:
            hold.release()
        self.assertEqual(self.events, [("log", "one", False),
                                       ("log", "two", True)])
        self.assertEqual(out.getvalue(), "\n", "one blank separator")
        self.assertIs(self.main.log, self.real_log)
        self.assertIs(self.main.fail, self.real_fail)

    def test_fail_releases_before_the_error(self) -> None:
        hold = bale_pack.WalkLogHold()
        hold.hold()
        self.main.log("context")
        with contextlib.redirect_stdout(io.StringIO()), \
                self.assertRaises(SystemExit):
            self.main.fail("refused", 3)
        self.assertEqual(self.events, [("log", "context", False),
                                       ("fail", "refused", 3)])
        self.assertFalse(hold.holding)

    def test_release_is_idempotent_and_silent_when_empty(self) -> None:
        hold = bale_pack.WalkLogHold()
        hold.hold()
        with contextlib.redirect_stdout(io.StringIO()) as out:
            hold.release()
            hold.release()
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(self.events, [])

    def test_fail_when_not_holding_reaches_the_real_fail(self) -> None:
        hold = bale_pack.WalkLogHold()
        with self.assertRaises(SystemExit):
            hold.fail("plain")
        self.assertEqual(self.events, [("fail", "plain", 1)])

    def test_no_op_without_a_cli_main(self) -> None:
        sys.modules["__main__"] = types.ModuleType("__main__")
        hold = bale_pack.WalkLogHold()
        hold.hold()
        self.assertFalse(hold.holding)


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
        """The sweep's prompt stays where it was (it is outside the walk,
        between its list questions and its README question); its log
        lines move after the walk."""
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
        span = [ln for ln in walk_span(out, last=README_PROMPT)
                if SWEEP_PROMPT_MARKER not in ln]
        self.assert_layout(span)
        closed = f"[bale] read-only sweep: closed {earlier[0]}"
        self.assertGreater(out.index(closed), out.index(README_PROMPT))
        self.assertNotIn(earlier[0], self.open_sids())


if __name__ == "__main__":
    unittest.main()
