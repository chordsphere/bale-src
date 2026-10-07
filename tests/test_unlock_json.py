#!/usr/bin/env python3
"""Hermetic E2E for `bale unlock --json` (v0.3.18, board 29).

Pins BALE.md section 9.3's --json row: unlock was the one
summary-emitting lifecycle command without --json, and an orchestrator
closing (for instance) read-only sessions wants the telemetry path
machine-readable. The contract under test is the ratified json-mode
split: stdout carries exactly one line of JSON (the key contract owned
by format_unlock_json's docstring in bin/bale_report.py), every human
line — `[bale] ` logs and the summary block — goes to stderr, and human
mode is byte-untouched (no code path differs when the stream swap never
happens).

The suite asserts:

- the session-close path emits outcome `unlocked` with sid,
  closure_reason, session/lock facts, and the telemetry record path;
- the read-only inference (`closed-read-only`) rides through the json
  key;
- the benign no-op emits outcome `no-op` (sid null, debris null);
- the crash-debris sweep's no-op carries the debris object (the swept
  sid and its record path) without disturbing the no-op contract;
- `--integration --json` is refused (the report is session-shaped);
- human mode emits no JSON.

v0.4.47 (session unlock-json-refusals; twine's `[[wanted]]` for
`bale unlock`) replaced the 0.4.45 pin that a refusal prints nothing
on stdout under --json: every session-shaped refusal now prints one
line, outcome `unlock-refused`, with a `reason` code from the closed
vocabulary bin/bale_report.py declares (UNLOCK_REFUSAL_REASONS), the
refusal's first line as `message`, the sid it is about and the open
sids — and still exits 1 with its `[bale] error:` line on stderr. The
two old refusal pins were rewritten into assertions on that line
(test_several_open_refusal_line, test_integration_json_refusal_line),
and the suite grew one case per code, the human-mode refusal (no JSON,
same stderr), the argparse exit 2, and the three new keys as null on
the `unlocked` and `no-op` lines. ``UnlockRefusalVocabularyTest`` pins
the vocabulary and the renderer's guard rails without a subprocess.

Board 35 (small pins, gap 5) added the `--integration` CLEAR path
itself (v0.3.2), previously covered only through its --json refusal:
a held lock is removed with the holder named and the live-apply
caveat printed; the not-held case is a benign exit-0 no-op; and an
unparseable lock file still clears, degrading to rows-only (no
[UNLOCK] headline, since a headline needs a sid the file couldn't
yield). The class fabricates `.bale/integration.lock` directly — the
lock is repo-level state apply holds only across its git window, so
the file is exactly what the command sees.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_unlock_json.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harness import (
    _load_module,
    bale_env,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_checked,
)

# The full key set of every unlock line since v0.4.47, in emission
# order: the nine v0.3.18/v0.3.34 keys, then the three refusal keys.
UNLOCK_LINE_KEYS = [
    "outcome", "sid", "log", "closure_reason", "session_dir_wiped",
    "branch_preserved", "telemetry", "debris", "sweep",
    "reason", "message", "open_sessions",
]

# The closed refusal vocabulary, spelled here independently of the
# module so a silent widening or reorder in bin/bale_report.py fails.
REFUSAL_REASONS = (
    "hold-branch", "not-open", "several-open", "not-a-repo",
    "integration-json",
)

ERROR_PREFIX = "[bale] error: "


def parse_single_json_line(stdout: str) -> dict:
    """The stream-discipline assertion in one place: stdout is exactly
    one non-empty line, and that line parses as a JSON object."""
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    if len(lines) != 1:
        raise AssertionError(
            f"expected exactly one stdout line under --json; got "
            f"{len(lines)}:\n{stdout}")
    payload = json.loads(lines[0])
    if not isinstance(payload, dict):
        raise AssertionError(f"stdout line is not a JSON object: {lines[0]}")
    return payload


class UnlockJsonTest(unittest.TestCase):
    """`bale unlock --json`: one stdout JSON line, human trail on stderr."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-unlockjson-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack(self, *extra: str, slug: str = "unlockjson-a",
             include: str = "hello.txt"):
        return run_bale(
            self.install,
            [
                "pack", "unlock json test goal",
                "--slug", slug,
                "--include", include,
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def unlock(self, *extra: str):
        return run_bale(self.install, ["unlock", *extra],
                        cwd=self.repo, env=self.env)

    def assert_ok(self, result) -> None:
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        entries = [d for d in root.iterdir() if (d / "open").is_file()]
        entries.sort(key=lambda d: (d.stat().st_mtime, d.name))
        return [d.name for d in entries]

    def packed_sid(self, result) -> str:
        self.assert_ok(result)
        sids = self.open_sids()
        self.assertTrue(sids, msg="pack succeeded but no session is open")
        return sids[-1]

    def registry_order(self) -> list:
        """Open sids in registry order (sorted: sids are date-prefixed),
        the order the refusal line's open_sessions promises."""
        return sorted(self.open_sids())

    def open_two_sessions(self) -> list:
        """Two open sessions: the second pack needs a scope-disjoint
        include (ADR-0007's pack-time gate refuses intersecting
        scopes), so a second committed file carries it; piped stdin
        means no sweep prompt can close the first."""
        env = git_env(self.home)
        (self.repo / "world.txt").write_text("world\n", encoding="utf-8")
        run_checked(["git", "add", "world.txt"], cwd=self.repo, env=env)
        run_checked(["git", "commit", "-m", "second file"],
                    cwd=self.repo, env=env)
        self.packed_sid(self.pack(slug="unlockjson-a"))
        self.packed_sid(self.pack(slug="unlockjson-b",
                                  include="world.txt"))
        sids = self.registry_order()
        self.assertEqual(len(sids), 2, msg="both sessions must stay open")
        return sids

    def error_line(self, stderr: str) -> str:
        """The refusal's `[bale] error:` line, prefix stripped — the
        human contract the refusal line's `message` must echo."""
        lines = [ln for ln in stderr.splitlines()
                 if ln.startswith(ERROR_PREFIX)]
        self.assertEqual(len(lines), 1,
                         msg=f"expected one error line on stderr:\n{stderr}")
        return lines[0][len(ERROR_PREFIX):]

    def assert_refusal_line(self, result, *, reason: str, sid,
                            open_sessions, error_starts: str) -> dict:
        """Everything one `unlock-refused` line must hold: exit 1, exactly
        one JSON line on stdout with the full key set in order, the code,
        the sid, the open sids, every closure key null (branch_preserved
        false), `message` equal to the stderr error line's text, and that
        error line still on stderr with its unchanged wording."""
        self.assertEqual(
            result.returncode, 1,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(list(payload), UNLOCK_LINE_KEYS)
        self.assertEqual(payload["outcome"], "unlock-refused")
        self.assertEqual(payload["reason"], reason)
        self.assertIn(payload["reason"], REFUSAL_REASONS)
        self.assertEqual(payload["sid"], sid)
        self.assertEqual(payload["open_sessions"], open_sessions)
        for key in ("log", "closure_reason", "session_dir_wiped",
                    "telemetry", "debris", "sweep"):
            self.assertIsNone(payload[key], msg=key)
        self.assertIs(payload["branch_preserved"], False)
        error = self.error_line(result.stderr)
        self.assertTrue(error.startswith(error_starts),
                        msg=f"stderr wording moved: {error!r}")
        # message is failure_cause's string: the error's first line.
        self.assertEqual(payload["message"], error.splitlines()[0].strip())
        return payload

    def unlock_attempts(self, sid: str) -> list:
        """The unlock attempts in sid's telemetry record (none expected
        after a refusal — a refusal is not a closure)."""
        path = self.repo / "claude" / "telemetry" / f"{sid}.json"
        if not path.is_file():
            return []
        record = json.loads(path.read_text(encoding="utf-8"))
        return [a for a in record.get("attempts", [])
                if a.get("command") == "unlock"]

    # -- pinned behavior 1: the session-close path -----------------------

    def test_close_path_emits_unlocked_contract(self) -> None:
        sid = self.packed_sid(self.pack())
        result = self.unlock("--json")
        self.assert_ok(result)

        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "unlocked")
        self.assertEqual(payload["sid"], sid)
        self.assertEqual(payload["closure_reason"], "abandoned")
        self.assertTrue(payload["session_dir_wiped"])
        self.assertFalse(payload["branch_preserved"])
        self.assertTrue(
            payload["telemetry"].startswith("claude/telemetry/"),
            msg="the machine-readable telemetry path is the point of "
                "the feature")
        self.assertTrue(payload["log"].endswith(f".bale/logs/{sid}.log"))
        # The v0.3.34 additive sweep key: null when [apply].sweep is
        # unset (this sandbox never sets it) — the additive-null
        # contract, same posture as apply's archive key.
        self.assertIsNone(payload["sweep"])
        # Stream discipline: the human trail moved to stderr, whole.
        self.assertIn("[bale]", result.stderr)
        self.assertIn("[UNLOCK]", result.stderr,
                      msg="the human summary block is the stderr "
                          "reference trail under json mode")
        # And the record it points at really exists.
        self.assertTrue((self.repo / payload["telemetry"]).is_file())

    # -- pinned behavior 2: the read-only inference rides the key --------

    def test_readonly_inference_in_json(self) -> None:
        self.packed_sid(self.pack("--read-only"))
        result = self.unlock("--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["closure_reason"], "closed-read-only")

    # -- pinned behavior 3: the benign no-op -----------------------------

    def test_noop_emits_no_op_outcome(self) -> None:
        result = self.unlock("--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "no-op")
        self.assertIsNone(payload["sid"])
        self.assertIsNone(payload["closure_reason"])
        self.assertIsNone(payload["debris"])
        self.assertIn("no open session", result.stderr,
                      msg="the human no-op line moved to stderr")

    # -- pinned behavior 4: the crash-debris sweep's no-op ---------------

    def test_noop_carries_debris_object(self) -> None:
        debris_sid = "2026-07-01-crashed-pack-001"
        bale_dir = self.repo / ".bale"
        bale_dir.mkdir()
        (bale_dir / "current_session").write_text(f"{debris_sid}\n")

        result = self.unlock("--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "no-op")
        self.assertIsNone(payload["sid"],
                          msg="the debris sid is not 'the' closed "
                              "session; it rides under debris")
        debris = payload["debris"]
        self.assertEqual(debris["sid"], debris_sid)
        self.assertTrue(debris["telemetry"].startswith("claude/telemetry/"))
        self.assertTrue((self.repo / debris["telemetry"]).is_file())
        # The debris record's own sweep rides under debris (v0.3.34),
        # not the top-level key; null here since [apply].sweep is unset.
        self.assertIsNone(debris["sweep"])
        self.assertIsNone(payload["sweep"],
                          msg="the no-op's only sweep is the debris "
                              "record's — the top-level key stays null")

    # -- pinned behavior 5: a refusal prints its line (v0.4.47) ---------

    def test_several_open_refusal_line(self) -> None:
        """Two sessions open, no sid. Until v0.4.45 this pinned an empty
        stdout (test_refusal_emits_nothing_on_stdout); since v0.4.47 the
        refusal prints the unlock-refused line, reason several-open, no
        sid, both open sids — and still exits 1 with the same stderr."""
        sids = self.open_two_sessions()
        result = self.unlock("--json")
        self.assert_refusal_line(
            result, reason="several-open", sid=None, open_sessions=sids,
            error_starts="2 sessions are open; `bale unlock` needs an "
                         "explicit session id when more than one is "
                         "open. Open sessions (oldest first): ")
        self.assertEqual(self.registry_order(), sids,
                         msg="a refusal closes nothing")

    # -- pinned behavior 6: --integration --json is refused, with a line -

    def test_integration_json_refusal_line(self) -> None:
        """`--integration --json` (until v0.4.45 pinned as an empty
        stdout, test_integration_json_refused) prints reason
        integration-json; under --json the code covers the other two
        --integration contradictions too, each keeping its own stderr
        text, and the sid key echoes a sid only when one was given."""
        with self.subTest(variant="--integration --json"):
            result = self.unlock("--integration", "--json")
            self.assert_refusal_line(
                result, reason="integration-json", sid=None,
                open_sessions=[],
                error_starts="`bale unlock --integration --json` is not "
                             "supported: the json report is "
                             "session-shaped")
        with self.subTest(variant="--integration <sid> --json"):
            result = self.unlock("--integration", "2026-01-01-x-001",
                                 "--json")
            self.assert_refusal_line(
                result, reason="integration-json", sid="2026-01-01-x-001",
                open_sessions=[],
                error_starts="`bale unlock --integration` clears the "
                             "repo-level integration lock and takes no "
                             "session id.")
        with self.subTest(variant="--integration --reason --json"):
            result = self.unlock("--integration", "--reason", "aborted",
                                 "--json")
            self.assert_refusal_line(
                result, reason="integration-json", sid=None,
                open_sessions=[],
                error_starts="`bale unlock --integration` clears the "
                             "repo-level integration lock; it closes no "
                             "session")
        with self.subTest(variant="open sessions are listed"):
            sid = self.packed_sid(self.pack())
            result = self.unlock("--integration", "--json")
            self.assert_refusal_line(
                result, reason="integration-json", sid=None,
                open_sessions=[sid],
                error_starts="`bale unlock --integration --json`")

    # -- pinned behavior 7: human mode emits no JSON ---------------------

    def test_human_mode_emits_no_json(self) -> None:
        self.packed_sid(self.pack())
        result = self.unlock()
        self.assert_ok(result)
        self.assertNotIn('{"outcome"', result.stdout)
        self.assertIn("[UNLOCK]", result.stdout,
                      msg="the human block stays on stdout when the "
                          "stream swap never happens")

    # -- v0.4.47: one case per refusal code ------------------------------

    def test_hold_branch_refusal_line(self) -> None:
        """The refusal twine's kill-switch dispatches on: a bale/<sid>
        branch exists, no --force. Exactly twine's command line
        (`unlock <sid> --reason aborted --json`). The session stays open,
        the branch stays, and no closure record is written."""
        sid = self.packed_sid(self.pack())
        run_checked(["git", "branch", f"bale/{sid}"], cwd=self.repo,
                    env=git_env(self.home))
        result = self.unlock(sid, "--reason", "aborted", "--json")
        self.assert_refusal_line(
            result, reason="hold-branch", sid=sid, open_sessions=[sid],
            error_starts=f"branch bale/{sid} exists — this session "
                         f"reached HOLD. Use `bale revert {sid}`")
        self.assertEqual(self.registry_order(), [sid])
        self.assertEqual(self.unlock_attempts(sid), [],
                         msg="a refusal is not a closure: no record")

    def test_hold_branch_force_still_unlocks(self) -> None:
        """--force never refuses: the unlocked line, branch_preserved
        true, the refusal keys null."""
        sid = self.packed_sid(self.pack())
        run_checked(["git", "branch", f"bale/{sid}"], cwd=self.repo,
                    env=git_env(self.home))
        result = self.unlock(sid, "--force", "--json")
        self.assert_ok(result)
        payload = parse_single_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "unlocked")
        self.assertIs(payload["branch_preserved"], True)
        self.assertIsNone(payload["reason"])

    def test_not_open_refusal_line(self) -> None:
        """An explicit sid the registry does not show open: the sid asked
        for rides the line; open_sessions lists what is open, [] when
        nothing is."""
        with self.subTest(variant="nothing open"):
            result = self.unlock("2026-01-01-ghost-001", "--json")
            self.assert_refusal_line(
                result, reason="not-open", sid="2026-01-01-ghost-001",
                open_sessions=[],
                error_starts="session 2026-01-01-ghost-001 is not open; "
                             "nothing to unlock. No sessions are open.")
        with self.subTest(variant="another session open"):
            sid = self.packed_sid(self.pack())
            result = self.unlock("2026-01-01-ghost-001", "--json")
            self.assert_refusal_line(
                result, reason="not-open", sid="2026-01-01-ghost-001",
                open_sessions=[sid],
                error_starts=f"session 2026-01-01-ghost-001 is not open; "
                             f"nothing to unlock. Open session(s): {sid}.")
            self.assertEqual(self.registry_order(), [sid])

    def test_not_a_repo_refusal_line(self) -> None:
        """Outside any git repository: no registry, so open_sessions is
        null; sid is null, or the sid asked for. GIT_CEILING_DIRECTORIES
        keeps git from walking out of the sandbox (ADR-0005)."""
        outside = self.tmp / "not-a-repo"
        outside.mkdir()
        env = dict(self.env, GIT_CEILING_DIRECTORIES=str(self.tmp))
        for args, sid in ((["--json"], None),
                          (["2026-01-01-ghost-001", "--json"],
                           "2026-01-01-ghost-001")):
            with self.subTest(args=args):
                result = run_bale(self.install, ["unlock", *args],
                                  cwd=outside, env=env)
                self.assert_refusal_line(
                    result, reason="not-a-repo", sid=sid,
                    open_sessions=None,
                    error_starts="not in a git repo. `bale unlock` "
                                 "requires the project repo.")

    def test_every_reason_code_is_reached(self) -> None:
        """The vocabulary has no dead code: the cases above reach each
        of the five through the CLI. Pinned as a list so adding a code
        without its case fails here."""
        covered = {
            "hold-branch": "test_hold_branch_refusal_line",
            "not-open": "test_not_open_refusal_line",
            "several-open": "test_several_open_refusal_line",
            "not-a-repo": "test_not_a_repo_refusal_line",
            "integration-json": "test_integration_json_refusal_line",
        }
        br = _load_module("bale_report")
        self.assertEqual(tuple(covered), br.UNLOCK_REFUSAL_REASONS)
        for name in covered.values():
            self.assertTrue(callable(getattr(self, name, None)), msg=name)

    # -- v0.4.47: what does not change -----------------------------------

    def test_human_mode_refusals_print_no_json(self) -> None:
        """Without --json a refusal prints no JSON and nothing new: the
        resolution refusals print nothing on stdout at all, the hold
        refusal only the `[bale] unlock: <sid>` log line it always
        printed there (log() writes stdout in human mode), and each
        stderr is exactly its one error line. Exit 1 throughout."""
        sids = self.open_two_sessions()
        cases = [
            ((), ""),
            (("2026-01-01-ghost-001",), ""),
            (("--integration", "2026-01-01-ghost-001"), ""),
        ]
        for args, stdout in cases:
            with self.subTest(args=args):
                result = self.unlock(*args)
                self.assertEqual(result.returncode, 1)
                self.assertEqual(result.stdout, stdout)
                self.assertEqual(result.stderr.count("\n"), 1,
                                 msg=result.stderr)
                self.assertTrue(result.stderr.startswith(ERROR_PREFIX))
        with self.subTest(args="hold"):
            sid = sids[0]
            run_checked(["git", "branch", f"bale/{sid}"], cwd=self.repo,
                        env=git_env(self.home))
            result = self.unlock(sid)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, f"[bale] unlock: {sid}\n")
            self.assertNotIn('{"outcome"', result.stdout)
            self.assertTrue(result.stderr.startswith(
                f"{ERROR_PREFIX}branch bale/{sid} exists"))

    def test_argparse_error_exits_two_with_empty_stdout(self) -> None:
        """An argparse error never reaches cmd_unlock: exit 2, nothing on
        stdout, under --json too."""
        result = self.unlock("--reason", "not-a-reason", "--json")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")
        self.assertIn("invalid choice", result.stderr)

    def test_unlocked_and_noop_lines_carry_null_refusal_keys(self) -> None:
        """The three v0.4.47 keys are on every line, null off the refused
        outcome, after the nine earlier keys (their order unchanged)."""
        with self.subTest(outcome="no-op"):
            result = self.unlock("--json")
            self.assert_ok(result)
            payload = parse_single_json_line(result.stdout)
            self.assertEqual(list(payload), UNLOCK_LINE_KEYS)
            self.assertEqual(payload["outcome"], "no-op")
            for key in ("reason", "message", "open_sessions"):
                self.assertIn(key, payload)
                self.assertIsNone(payload[key], msg=key)
        with self.subTest(outcome="unlocked"):
            sid = self.packed_sid(self.pack())
            result = self.unlock(sid, "--json")
            self.assert_ok(result)
            payload = parse_single_json_line(result.stdout)
            self.assertEqual(list(payload), UNLOCK_LINE_KEYS)
            self.assertEqual(payload["outcome"], "unlocked")
            for key in ("reason", "message", "open_sessions"):
                self.assertIn(key, payload)
                self.assertIsNone(payload[key], msg=key)

    def test_help_names_the_refusal_outcome(self) -> None:
        """`bale help unlock` names the refused line by its outcome and
        keeps pointing at the key contract's owner."""
        result = run_bale(self.install, ["help", "unlock"],
                          cwd=self.repo, env=self.env)
        self.assert_ok(result)
        flat = " ".join(result.stdout.split())
        self.assertIn("'unlock-refused'", flat)
        self.assertIn("format_unlock_json's docstring", flat)


class UnlockRefusalVocabularyTest(unittest.TestCase):
    """The reason vocabulary and the renderer's guard rails (v0.4.47),
    in process — format_unlock_json is pure."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.br = _load_module("bale_report")

    def test_vocabulary_is_the_closed_five(self) -> None:
        self.assertEqual(self.br.UNLOCK_REFUSAL_REASONS, REFUSAL_REASONS)

    def test_docstring_lists_every_code(self) -> None:
        doc = self.br.format_unlock_json.__doc__
        self.assertIn('"unlock-refused"', doc)
        for code in self.br.UNLOCK_REFUSAL_REASONS:
            self.assertRegex(doc, rf"\n\s+{code}\s", msg=code)

    def test_refusal_renderer_key_set(self) -> None:
        payload = json.loads(self.br.format_unlock_refusal_json(
            reason="not-open", message="session x is not open",
            sid="x", open_sessions=("a", "b")))
        self.assertEqual(list(payload), UNLOCK_LINE_KEYS)
        self.assertEqual(payload["outcome"], "unlock-refused")
        self.assertEqual(payload["open_sessions"], ["a", "b"])
        self.assertIs(payload["branch_preserved"], False)

    def test_unknown_reason_raises(self) -> None:
        with self.assertRaises(ValueError):
            self.br.format_unlock_refusal_json(
                reason="system-dir", message="m", sid=None,
                open_sessions=None)
        with self.assertRaises(ValueError):
            self.br.format_unlock_json(outcome="unlock-refused")

    def test_refusal_keys_off_the_refused_outcome_raise(self) -> None:
        for kwargs in ({"reason": "not-open"}, {"message": "m"},
                       {"open_sessions": []}):
            with self.subTest(**{k: repr(v) for k, v in kwargs.items()}):
                with self.assertRaises(ValueError):
                    self.br.format_unlock_json(outcome="unlocked", **kwargs)

    def test_earlier_keys_render_unchanged(self) -> None:
        """The nine pre-0.4.47 keys keep their values and order: the
        no-op line is the old line plus three trailing nulls."""
        line = self.br.format_unlock_json(outcome="no-op")
        self.assertTrue(line.startswith(
            '{"outcome": "no-op", "sid": null, "log": null, '
            '"closure_reason": null, "session_dir_wiped": null, '
            '"branch_preserved": false, "telemetry": null, '
            '"debris": null, "sweep": null, '))
        self.assertTrue(line.endswith(
            '"reason": null, "message": null, "open_sessions": null}'))


class UnlockIntegrationTest(unittest.TestCase):
    """`bale unlock --integration`: the clear path (board 35 gap 5)."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-unlockint-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.lock = self.repo / ".bale" / "integration.lock"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def unlock_integration(self):
        return run_bale(self.install, ["unlock", "--integration"],
                        cwd=self.repo, env=self.env)

    def test_integration_clear_path(self) -> None:
        """Subtests run in sequence against one repo: the not-held no-op
        first (nothing exists yet), then a well-formed lock cleared with
        the holder named, then an unparseable lock cleared rows-only."""
        holder_sid = "2026-07-30-integration-fixture-001"

        with self.subTest(variant="not held is a benign no-op"):
            result = self.unlock_integration()
            self.assertEqual(
                result.returncode, 0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            self.assertIn("integration lock is not held; nothing to unlock.",
                          result.stdout)

        with self.subTest(variant="held lock clears, holder named"):
            self.lock.parent.mkdir(parents=True, exist_ok=True)
            self.lock.write_text(json.dumps({
                "sid": holder_sid,
                "pid": 12345,
                "acquired_at": "2026-07-30T12:00:00+00:00",
            }) + "\n", encoding="utf-8")
            result = self.unlock_integration()
            self.assertEqual(
                result.returncode, 0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            self.assertFalse(self.lock.exists(),
                             msg="the clear path's one job")
            self.assertIn(f"cleared (was held by session {holder_sid}, "
                          f"pid 12345", result.stdout)
            self.assertIn("[UNLOCK]", result.stdout)
            self.assertIn(holder_sid, result.stdout)
            # The one caveat the summary insists on: only safe while no
            # apply is mid-integration.
            self.assertIn("Only clear this while no `bale apply` is "
                          "running", result.stdout)

        with self.subTest(variant="unparseable lock clears rows-only"):
            self.lock.write_text("not json{", encoding="utf-8")
            result = self.unlock_integration()
            self.assertEqual(
                result.returncode, 0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            self.assertFalse(self.lock.exists(),
                             msg="an unreadable lock is exactly the "
                                 "debris the command exists to clear")
            self.assertIn("holder unknown (unparseable lock file)",
                          result.stdout)
            self.assertNotIn("[UNLOCK]", result.stdout,
                             msg="no sid, no headline — rows-only degrade")


if __name__ == "__main__":
    unittest.main(verbosity=2)
