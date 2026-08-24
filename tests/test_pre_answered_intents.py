"""Pre-answered intents through the supersession decline-default
exchange (v0.4.12, board 49a-i; BALE.md §6.7).

Two layers:

1. **The pure surface** — parse_pre_answered_intents (strict, closed
   vocabulary, ValueError posture) and consume_supersession_intent
   (exact prompt+subject match, consumed entries never re-consume).
2. **The resolver's exchange point** — _resolve_supersession called
   directly with stubbed `__main__` helpers and non-TTY stdin, pinning
   the constraint the session was scoped around: the exchange keeps
   its decline default on every existing path, and an intent routes
   THROUGH it, never around it. Matrix:

   - matching intent → accepted: the parent closes, the intent is
     consumed, and no prompt runs;
   - no intent / wrong-subject intent → the piped decline default,
     byte-identical outcome to today's, intent unconsumed;
   - the HOLD-branch guard still refuses BEFORE the intent is
     consulted — a matching intent cannot leapfrog a guard;
   - the idempotent not-open path proceeds without consuming the
     intent (no prompt was raised; the caller reports it unconsumed).

Why direct-call rather than e2e: the intents channel is deliberately
in-process only — no CLI flag exists (the design's no-typed-blanket
rule) — so a subprocess pack cannot receive intents until the `bale
open` verb (49a-ii) composes one. The existing
test_supersession_pack.py e2e suite continues to pin every typed
path's decline default unmodified; this suite pins the new path at
the function seam 49a-ii will call.

Stub discipline: bale_pack resolves shared helpers lazily via
``from __main__ import ...``, so the tests install stubs as
attributes on the real ``__main__`` module in setUp and restore or
remove every one in tearDown — novel names only (log, fail,
confirm_yn, git, session_is_open, close_session_with_record), so a
discovery run's own ``__main__`` is left exactly as found.
bale_report is the real module; the idempotent case writes a real
telemetry record under the temp repo for it to read.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "bin"))

import bale_pack  # noqa: E402  (path insertion above is the point)


class _Fail(Exception):
    """Sentinel raised by the stubbed fail() so tests can assert on it."""


class _NonTty(io.StringIO):
    def isatty(self) -> bool:  # noqa: D102 — trivial
        return False


def _intent(subject: str) -> bale_pack.PreAnsweredIntent:
    return bale_pack.PreAnsweredIntent(prompt="supersede", subject=subject)


class ParseIntentsTest(unittest.TestCase):
    """parse_pre_answered_intents: strict, closed, honest-empty."""

    def test_none_and_empty_are_no_intents(self) -> None:
        self.assertEqual(bale_pack.parse_pre_answered_intents(None), [])
        self.assertEqual(bale_pack.parse_pre_answered_intents([]), [])

    def test_valid_entry_parses_unconsumed(self) -> None:
        out = bale_pack.parse_pre_answered_intents(
            [{"prompt": "supersede", "subject": "2026-08-18-parent-001"}])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].prompt, "supersede")
        self.assertEqual(out[0].subject, "2026-08-18-parent-001")
        self.assertFalse(out[0].consumed)

    def test_additive_keys_are_tolerated(self) -> None:
        out = bale_pack.parse_pre_answered_intents(
            [{"prompt": "supersede", "subject": "s", "note": "future"}])
        self.assertEqual(len(out), 1)

    def test_defects_refuse(self) -> None:
        cases = [
            "not-a-list",
            [["not", "an", "object"]],
            [{"subject": "s"}],
            [{"prompt": "supersede"}],
            [{"prompt": " ", "subject": "s"}],
            [{"prompt": "supersede", "subject": ""}],
            [{"prompt": "yes-to-all", "subject": "s"}],
            [{"prompt": "supersede", "subject": "s"},
             {"prompt": "supersede", "subject": "s"}],
        ]
        for raw in cases:
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    bale_pack.parse_pre_answered_intents(raw)

    def test_closed_vocabulary_refusal_names_the_vocabulary(self) -> None:
        """The blanket-yes impossibility is load-bearing: an unknown
        prompt's refusal names the closed set, so the no-spelling rule
        is visible at the point of refusal."""
        with self.assertRaises(ValueError) as ctx:
            bale_pack.parse_pre_answered_intents(
                [{"prompt": "everything", "subject": "s"}])
        self.assertIn("supersede", str(ctx.exception))

    def test_vocabulary_parity_with_the_constant(self) -> None:
        """INTENT_PROMPTS is the code-side home; the wire-side enum
        parity is pinned in test_bundle_manifest.py — this asserts the
        constant itself is exactly the ratified single entry, so a
        broadening lands deliberately, not by drive-by."""
        self.assertEqual(bale_pack.INTENT_PROMPTS, ("supersede",))


class ConsumeIntentTest(unittest.TestCase):
    """consume_supersession_intent: exact match, no side effects."""

    def test_exact_match_returns_the_intent(self) -> None:
        intents = [_intent("a-001"), _intent("b-002")]
        got = bale_pack.consume_supersession_intent(intents, "b-002")
        self.assertIs(got, intents[1])
        self.assertFalse(got.consumed,
                         msg="selection is pure; the caller marks")

    def test_wrong_subject_matches_nothing(self) -> None:
        self.assertIsNone(bale_pack.consume_supersession_intent(
            [_intent("a-001")], "other-002"))

    def test_consumed_intent_never_reconsumes(self) -> None:
        one = _intent("a-001")
        one.consumed = True
        self.assertIsNone(
            bale_pack.consume_supersession_intent([one], "a-001"))


class ResolverExchangeTest(unittest.TestCase):
    """_resolve_supersession with pre_answered: through, never around."""

    STUB_NAMES = ("log", "fail", "confirm_yn", "git", "session_is_open",
                  "close_session_with_record")

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-intents-")
        self.repo = Path(self._tmpdir.name)
        self.logs: list[str] = []
        self.closed: list[str] = []
        self.prompted: list[str] = []
        self.branch_exists = False
        self.parent_open = True

        main = sys.modules["__main__"]
        self._saved = {}
        sentinel = object()
        for name in self.STUB_NAMES:
            self._saved[name] = getattr(main, name, sentinel)
        self._sentinel = sentinel

        def _log(msg, *, force=False):
            self.logs.append(msg)

        def _fail(msg, code=1):
            raise _Fail(msg)

        def _confirm_yn(prompt, *, default_no=True):
            self.prompted.append(prompt)
            return False

        def _git(argv, cwd=None, check=True):
            return SimpleNamespace(
                returncode=0 if self.branch_exists else 1,
                stdout="", stderr="")

        def _session_is_open(repo, sid):
            return self.parent_open

        def _close(repo, sid, *, closure_reason, command, log_path):
            self.closed.append(sid)
            return (f"claude/telemetry/{sid}.json", None, None)

        main.log = _log
        main.fail = _fail
        main.confirm_yn = _confirm_yn
        main.git = _git
        main.session_is_open = _session_is_open
        main.close_session_with_record = _close

    def tearDown(self) -> None:
        main = sys.modules["__main__"]
        for name in self.STUB_NAMES:
            saved = self._saved[name]
            if saved is self._sentinel:
                delattr(main, name)
            else:
                setattr(main, name, saved)
        self._tmpdir.cleanup()

    def resolve(self, sid: str, intents, *, goal="g", slug="s"):
        args = argparse.Namespace(supersedes=sid, goal=goal, slug=slug)
        with mock.patch.object(sys, "stdin", _NonTty()):
            return bale_pack._resolve_supersession(
                args, self.repo, pre_answered=intents)

    # -- the new path ----------------------------------------------------

    def test_matching_intent_accepts_and_closes(self) -> None:
        one = _intent("2026-08-18-parent-001")
        stamp, declined = self.resolve("2026-08-18-parent-001", [one])
        self.assertEqual(stamp, "2026-08-18-parent-001")
        self.assertIsNone(declined)
        self.assertEqual(self.closed, ["2026-08-18-parent-001"])
        self.assertTrue(one.consumed)
        self.assertEqual(self.prompted, [],
                         msg="the intent answers the exchange; no prompt")
        self.assertTrue(any("pre-answered intent" in m for m in self.logs))

    # -- decline defaults byte-identical ---------------------------------

    def test_no_intents_keeps_piped_decline_default(self) -> None:
        stamp, declined = self.resolve("parent-001", [])
        self.assertIsNone(stamp)
        self.assertEqual(declined, "parent-001")
        self.assertEqual(self.closed, [])
        self.assertTrue(any("decline default applies without a prompt"
                            in m for m in self.logs))

    def test_wrong_subject_intent_is_inert(self) -> None:
        """An intent for another parent changes nothing: the decline
        default governs and the intent stays unconsumed for the
        caller's loud report."""
        other = _intent("some-other-parent-009")
        stamp, declined = self.resolve("parent-001", [other])
        self.assertIsNone(stamp)
        self.assertEqual(declined, "parent-001")
        self.assertEqual(self.closed, [])
        self.assertFalse(other.consumed)

    def test_wizard_path_decline_still_refuses(self) -> None:
        """The wizard-path guaranteed-refusal decline is unchanged when
        no intent matches."""
        with self.assertRaises(_Fail):
            self.resolve("parent-001", [_intent("elsewhere-002")],
                         goal=None, slug=None)
        self.assertEqual(self.closed, [])

    # -- through, never around -------------------------------------------

    def test_hold_branch_guard_runs_before_the_intent(self) -> None:
        """A matching intent cannot leapfrog the HOLD-branch refusal:
        the guard fires first and the intent is never consumed."""
        self.branch_exists = True
        one = _intent("parent-001")
        with self.assertRaises(_Fail) as ctx:
            self.resolve("parent-001", [one])
        self.assertIn("reached HOLD", str(ctx.exception))
        self.assertFalse(one.consumed)
        self.assertEqual(self.closed, [])

    def test_idempotent_rerun_path_leaves_intent_unconsumed(self) -> None:
        """A parent already closed superseded-by-split proceeds via the
        history path — no prompt is raised, so the intent is not
        consumed (the caller reports it loudly)."""
        self.parent_open = False
        record_path = (self.repo / "claude" / "telemetry"
                       / "parent-001.json")
        record_path.parent.mkdir(parents=True)
        record_path.write_text(json.dumps({
            "attempts": [{"closure_reason": "superseded-by-split"}],
        }), encoding="utf-8")
        one = _intent("parent-001")
        stamp, declined = self.resolve("parent-001", [one])
        self.assertEqual(stamp, "parent-001")
        self.assertIsNone(declined)
        self.assertFalse(one.consumed)
        self.assertEqual(self.closed, [],
                         msg="nothing left to close on the re-run")


if __name__ == "__main__":
    unittest.main()
