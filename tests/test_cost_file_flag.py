#!/usr/bin/env python3
"""`--cost-file PATH` on apply, retry and unlock (v0.4.54, session
cost-mirror): a harness hands bale what the worker run spent, and bale
stamps it into the telemetry cost block of the attempt that invocation
writes — the block gaining ``calls`` and ``models`` beside the v0.4.6
four.

What this suite pins, against the documented contract (ADR-0002: the
record on disk, the exit code, the refusal line — never private
internals):

- **The reader** (``ReadCostFileTest``, in process): bale_report's
  ``read_cost_file`` accepts one JSON object over COST_KEYS, any subset,
  each nullable, and returns all six keys (an omitted key null); it
  refuses — CostFileError, path and key named — a missing, non-regular,
  empty, non-UTF-8, non-JSON or non-object file, a repeated key, an
  unknown key, and every wrong type the brief lists. COST_KEYS and the
  schema's ``attempts[].cost.properties`` are the same six, in order,
  under ``additionalProperties: false``.
- **unlock, end to end** (``UnlockCostFileE2ETest``): a full six-key
  file and a subset file each read back from the record's last attempt;
  an unknown key, a wrong type, a missing file and a non-object file
  each refuse with the session still open and no attempt appended; a
  closing attempt written without the flag carries the six-key all-null
  block; a relative PATH resolves through apply.search_paths; the flag
  beside ``--integration`` refuses.
- **apply and retry, end to end** (``ApplyRetryCostFileE2ETest``): one
  stub response through the staging pipeline per verb, each closing
  attempt carrying the file; a bad file refusing before the pipeline
  with no attempt appended; a clarification's landing attempt (since
  0.4.63) carrying the file, the session still open.
- **help** (``CostFileHelpTest``): ``bale help apply``, ``bale help
  retry`` and ``bale help unlock`` each name ``--cost-file``.

Each end-to-end case runs in a fresh scratch repo with the
``[sandbox] enabled = false`` config committed (tests/harness.py's
precedent, board 80 posture), so the suite runs on hosts without user
namespaces; confinement is the sandbox suite's subject, not this one's.
Sandbox doctrine per ADR-0005 (fully hermetic) via tests/harness.py.

Run directly::

    python3 tests/test_cost_file_flag.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:  # the dotted run form needs it
    sys.path.insert(0, _TESTS_DIR)

from harness import (  # noqa: E402 — sys.path tweak above
    REPO_ROOT,
    _load_module,
    bale_env,
    build_response_dir,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_checked,
    tar_response_dir,
)

SCHEMA_PATH = REPO_ROOT / "schemas" / "telemetry-record.schema.json"

SIX_KEYS = ["tokens_in", "tokens_out", "usd", "model_tier", "calls",
            "models"]
ALL_NULL = {key: None for key in SIX_KEYS}
FULL = {
    "tokens_in": 182345,
    "tokens_out": 23456,
    "usd": 4.217,
    "model_tier": "deep",
    "calls": 41,
    "models": ["claude-opus-5-5", "claude-sonnet-5-5"],
}
SUBSET = {"usd": 0.5, "calls": 3}
ERROR_PREFIX = "[bale] error: "
NEW_CONTENT = "hello from the cost-mirror fixture\n"


class ReadCostFileTest(unittest.TestCase):
    """bale_report.read_cost_file: the one reader all three verbs call."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.br = _load_module("bale_report")
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-costread-")
        self.tmp = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def write(self, text: str, name: str = "cost.json") -> Path:
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    def refuses(self, path: Path, *needles: str) -> str:
        with self.assertRaises(self.br.CostFileError) as ctx:
            self.br.read_cost_file(path)
        message = str(ctx.exception)
        self.assertIn(str(path), message, msg="the refusal names the path")
        self.assertEqual(message.count("\n"), 0,
                         msg="one line: the refusal's whole cause")
        for needle in needles:
            self.assertIn(needle, message)
        return message

    # -- the shape -------------------------------------------------------

    def test_cost_keys_are_the_schema_properties(self) -> None:
        cost = (self.schema["properties"]["attempts"]["items"]
                ["properties"]["cost"])
        self.assertEqual(list(cost["properties"]), SIX_KEYS)
        self.assertEqual(list(self.br.COST_KEYS), SIX_KEYS)
        self.assertIs(cost["additionalProperties"], False)

    def test_empty_block_is_six_nulls_and_fresh(self) -> None:
        first = self.br.empty_cost_block()
        self.assertEqual(first, ALL_NULL)
        self.assertEqual(list(first), SIX_KEYS)
        first["usd"] = 1.0
        self.assertEqual(self.br.empty_cost_block(), ALL_NULL,
                         msg="a fresh dict per call")

    # -- acceptance ------------------------------------------------------

    def test_full_file_reads_back_verbatim(self) -> None:
        block = self.br.read_cost_file(self.write(json.dumps(FULL)))
        self.assertEqual(block, FULL)
        self.assertEqual(list(block), SIX_KEYS)

    def test_subset_fills_absent_keys_null(self) -> None:
        block = self.br.read_cost_file(self.write(json.dumps(SUBSET)))
        self.assertEqual(block, dict(ALL_NULL, **SUBSET))

    def test_empty_object_and_explicit_nulls(self) -> None:
        self.assertEqual(self.br.read_cost_file(self.write("{}")), ALL_NULL)
        self.assertEqual(
            self.br.read_cost_file(self.write(json.dumps(ALL_NULL))),
            ALL_NULL)

    def test_integer_usd_and_zero_counts_accepted(self) -> None:
        block = self.br.read_cost_file(self.write(json.dumps(
            {"usd": 0, "tokens_in": 0, "calls": 0, "models": []})))
        self.assertEqual(block["usd"], 0)
        self.assertEqual(block["models"], [])

    def test_byte_order_mark_tolerated(self) -> None:
        path = self.tmp / "bom.json"
        path.write_bytes(b"\xef\xbb\xbf" + json.dumps(SUBSET).encode())
        self.assertEqual(self.br.read_cost_file(path),
                         dict(ALL_NULL, **SUBSET))

    def test_models_recorded_as_handed(self) -> None:
        """Sorted-and-unique is the harness's arithmetic; bale records
        the array as given rather than reordering it."""
        block = self.br.read_cost_file(
            self.write(json.dumps({"models": ["z-model", "a-model"]})))
        self.assertEqual(block["models"], ["z-model", "a-model"])

    # -- refusals: the file ----------------------------------------------

    def test_missing_file(self) -> None:
        self.refuses(self.tmp / "absent.json", "not found")

    def test_directory_is_not_a_file(self) -> None:
        self.refuses(self.tmp, "not a regular file")

    def test_empty_and_whitespace_files(self) -> None:
        self.refuses(self.write(""), "is empty")
        self.refuses(self.write("  \n\t\n"), "is empty")

    def test_not_utf8(self) -> None:
        path = self.tmp / "latin.json"
        path.write_bytes(b'{"model_tier": "\xe9"}')
        self.refuses(path, "not UTF-8")

    def test_invalid_json(self) -> None:
        self.refuses(self.write("{tokens_in: 3}"), "not valid JSON")

    def test_nan_and_infinity_refused(self) -> None:
        self.refuses(self.write('{"usd": NaN}'), "not valid JSON")
        self.refuses(self.write('{"usd": Infinity}'), "not valid JSON")

    def test_repeated_key_refused(self) -> None:
        self.refuses(self.write('{"usd": 1, "usd": 2}'),
                     "'usd' appears more than once")

    def test_non_object_documents(self) -> None:
        for text, kind in (("[]", "array"), ('"x"', "string"),
                           ("3", "integer"), ("null", "null")):
            with self.subTest(text=text):
                self.refuses(self.write(text), "one JSON object", kind)

    # -- refusals: the keys and types ------------------------------------

    def test_unknown_key_named(self) -> None:
        message = self.refuses(
            self.write(json.dumps({"tokenz_in": 4, "usd": 1})),
            "unknown key 'tokenz_in'", "tokens_in")
        self.assertNotIn("'usd'", message.split("(the cost keys")[0],
                         msg="a valid key is not reported")

    def test_every_problem_on_one_line(self) -> None:
        self.refuses(
            self.write(json.dumps({"bogus": 1, "calls": -1, "usd": "1"})),
            "unknown key 'bogus'", "'calls' must be a non-negative "
            "integer or null, got -1", "'usd' must be a non-negative "
            "number or null, got string")

    def test_wrong_types_each_refused(self) -> None:
        cases = [
            ({"tokens_in": "12"}, "'tokens_in'", "got string"),
            ({"tokens_in": 1.5}, "'tokens_in'", "got number"),
            ({"tokens_in": True}, "'tokens_in'", "got boolean"),
            ({"tokens_out": -3}, "'tokens_out'", "got -3"),
            ({"calls": [1]}, "'calls'", "got array"),
            ({"usd": "4.20"}, "'usd'", "got string"),
            ({"usd": -0.01}, "'usd'", "got -0.01"),
            ({"usd": False}, "'usd'", "got boolean"),
            ({"model_tier": 3}, "'model_tier'", "got integer"),
            ({"models": "claude"}, "'models'", "got string"),
            ({"models": ["ok", ""]}, "'models'[1]", "non-empty"),
            ({"models": ["ok", "  "]}, "'models'[1]", "non-empty"),
            ({"models": [3]}, "'models'[0]", "got integer"),
            ({"models": {"a": 1}}, "'models'", "got object"),
        ]
        for data, key, detail in cases:
            with self.subTest(data=data):
                self.refuses(self.write(json.dumps(data)), key, detail)

    def test_builder_stamps_a_read_block(self) -> None:
        """The read block, handed to build_telemetry_attempt, lands as
        the attempt's cost verbatim and validates against the schema."""
        bv = _load_module("bale_validate")
        block = self.br.read_cost_file(self.write(json.dumps(FULL)))
        attempt = self.br.build_telemetry_attempt(
            outcome="unlocked", command="unlock", cost=block)
        self.assertEqual(attempt["cost"], FULL)
        from harness import _minimal_record
        rec = _minimal_record()
        rec["attempts"] = [attempt]
        self.assertEqual(bv.validate_telemetry_record(rec), [])


class _ScratchRepoCase(unittest.TestCase):
    """One fresh hermetic repo per test, the sandbox-off config committed
    before any pack."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-costfile-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        self.commit_config("[sandbox]\nenabled = false\n")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture helpers -------------------------------------------------

    def commit_config(self, text: str) -> None:
        (self.repo / "bale.toml").write_text(text, encoding="utf-8")
        run_checked(["git", "add", "bale.toml"], cwd=self.repo,
                    env=self.genv)
        run_checked(["git", "commit", "-m", "fixture config"],
                    cwd=self.repo, env=self.genv)

    def bale(self, *args: str, cwd: Path = None):
        return run_bale(self.install, list(args),
                        cwd=cwd or self.repo, env=self.env)

    def assert_exit(self, result, code: int) -> None:
        self.assertEqual(
            result.returncode, code,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

    def pack(self, slug: str = "cost-mirror-fx") -> str:
        result = self.bale("pack", "cost-file fixture goal: rewrite "
                           "hello.txt", "--slug", slug, "--include",
                           "hello.txt", "--no-readme")
        self.assert_exit(result, 0)
        sids = self.open_sids()
        self.assertEqual(len(sids), 1, msg="exactly one session open")
        return sids[0]

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return sorted(d.name for d in root.iterdir()
                      if (d / "open").is_file())

    def record(self, sid: str) -> dict:
        path = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(path.is_file(), msg=f"no telemetry record at {path}")
        return json.loads(path.read_text(encoding="utf-8"))

    def attempts(self, sid: str) -> list:
        return self.record(sid)["attempts"]

    def cost_file(self, data, name: str = "cost.json",
                  where: Path = None) -> Path:
        path = (where or self.tmp) / name
        path.write_text(data if isinstance(data, str) else json.dumps(data),
                        encoding="utf-8")
        return path

    def error_line(self, stderr: str) -> str:
        lines = [ln for ln in stderr.splitlines()
                 if ln.startswith(ERROR_PREFIX)]
        self.assertEqual(len(lines), 1, msg=stderr)
        return lines[0][len(ERROR_PREFIX):]


class UnlockCostFileE2ETest(_ScratchRepoCase):
    """`bale unlock --cost-file`: the abnormal exit's spend."""

    def test_full_file_reads_back_from_the_last_attempt(self) -> None:
        sid = self.pack()
        result = self.bale("unlock", sid, "--cost-file",
                           str(self.cost_file(FULL)))
        self.assert_exit(result, 0)
        last = self.attempts(sid)[-1]
        self.assertEqual(last["outcome"], "unlocked")
        self.assertEqual(last["command"], "unlock")
        self.assertEqual(last["cost"], FULL)
        self.assertIn("stamped into the closing attempt", result.stdout)

    def test_subset_file_absent_keys_null(self) -> None:
        sid = self.pack()
        result = self.bale("unlock", sid, "--cost-file",
                           str(self.cost_file(SUBSET)))
        self.assert_exit(result, 0)
        self.assertEqual(self.attempts(sid)[-1]["cost"],
                         dict(ALL_NULL, **SUBSET))

    def test_no_flag_stamps_six_key_all_null(self) -> None:
        sid = self.pack()
        self.assert_exit(self.bale("unlock", sid), 0)
        attempts = self.attempts(sid)
        self.assertEqual(attempts[-1]["cost"], ALL_NULL)
        self.assertEqual(list(attempts[-1]["cost"]), SIX_KEYS)
        # pack's opened attempt carries the same six-key default.
        self.assertEqual(attempts[0]["outcome"], "opened")
        self.assertEqual(attempts[0]["cost"], ALL_NULL)

    def test_refusals_leave_the_session_open_and_no_attempt(self) -> None:
        sid = self.pack()
        before = self.attempts(sid)
        cases = [
            ("unknown key", self.cost_file({"tokens": 5}, "unknown.json"),
             "unknown key 'tokens'"),
            ("wrong type", self.cost_file({"calls": "41"}, "wrong.json"),
             "'calls' must be a non-negative integer or null"),
            ("missing file", self.tmp / "nowhere.json",
             "cost file not found:"),
            ("non-object", self.cost_file("[1, 2]", "array.json"),
             "must hold one JSON object"),
        ]
        for label, path, needle in cases:
            with self.subTest(case=label):
                result = self.bale("unlock", sid, "--cost-file", str(path))
                self.assert_exit(result, 1)
                self.assertIn(needle, self.error_line(result.stderr))
                self.assertEqual(self.open_sids(), [sid],
                                 msg="the session is still open")
                self.assertEqual(self.attempts(sid), before,
                                 msg="no attempt appended")
                self.assertTrue(
                    (self.repo / ".bale" / "sessions" / sid).is_dir(),
                    msg="the session dir is untouched")
        # And the session still closes normally afterwards.
        self.assert_exit(self.bale("unlock", sid), 0)
        self.assertEqual(self.open_sids(), [])

    def test_json_refusal_line_carries_cost_file(self) -> None:
        sid = self.pack()
        result = self.bale("unlock", sid, "--json", "--cost-file",
                           str(self.cost_file({"usd": "x"})))
        self.assert_exit(result, 1)
        payload = json.loads(result.stdout.strip())
        self.assertEqual(payload["outcome"], "unlock-refused")
        self.assertEqual(payload["reason"], "cost-file")
        self.assertEqual(payload["sid"], sid)
        self.assertEqual(payload["message"], self.error_line(result.stderr))

    def test_relative_path_resolves_through_search_paths(self) -> None:
        downloads = self.tmp / "downloads"
        downloads.mkdir()
        self.commit_config(
            "[sandbox]\nenabled = false\n\n"
            f"[apply]\nsearch_paths = [\"{downloads}\"]\n")
        sid = self.pack()
        self.cost_file(FULL, "harness-cost.json", where=downloads)
        result = self.bale("unlock", sid, "--cost-file", "harness-cost.json")
        self.assert_exit(result, 0)
        self.assertEqual(self.attempts(sid)[-1]["cost"], FULL)

    def test_relative_path_resolves_against_cwd(self) -> None:
        sid = self.pack()
        self.cost_file(SUBSET, "here.json", where=self.repo)
        result = self.bale("unlock", sid, "--cost-file", "here.json")
        self.assert_exit(result, 0)
        self.assertEqual(self.attempts(sid)[-1]["cost"],
                         dict(ALL_NULL, **SUBSET))

    def test_integration_beside_cost_file_refuses(self) -> None:
        result = self.bale("unlock", "--integration", "--cost-file",
                           str(self.cost_file(FULL)))
        self.assert_exit(result, 1)
        self.assertIn("nothing for --cost-file to stamp",
                      self.error_line(result.stderr))

    def test_noop_unlock_says_the_file_was_not_stamped(self) -> None:
        result = self.bale("unlock", "--cost-file",
                           str(self.cost_file(FULL)))
        self.assert_exit(result, 0)
        self.assertIn("valid, not stamped", result.stdout)


class ApplyRetryCostFileE2ETest(_ScratchRepoCase):
    """`bale apply` / `bale retry --cost-file`: the normal exits' spend,
    one stub response through the staging pipeline per verb."""

    def response(self, sid: str, name: str) -> Path:
        rdir = build_response_dir(
            self.tmp / name, sid,
            summary="cost-mirror fixture: rewrite hello.txt",
            entries=[{
                "path": "hello.txt",
                "action": "modified",
                "reason": "the fixture goal's rewrite",
                "data": NEW_CONTENT.encode("utf-8"),
            }],
        )
        return tar_response_dir(rdir)

    def clarification(self, sid: str) -> Path:
        rdir = build_response_dir(
            self.tmp / "clar", sid,
            summary="cost-mirror fixture: blocked on a question",
            entries=[], validation_will_run=[],
            validation_sh="#!/usr/bin/env bash\n# no-op\nexit 0\n",
            manifest_extra={
                "response_kind": "clarification",
                "questions": [{
                    "question": "fixture question?",
                    "context": "fixture context",
                    "default_assumption": "fixture assumption",
                    "why_blocked": "fixture blocker",
                }],
            },
        )
        return tar_response_dir(rdir)

    def test_apply_stamps_the_applied_attempt(self) -> None:
        sid = self.pack()
        result = self.bale("apply", str(self.response(sid, "one")),
                           "--no-interact", "--cost-file",
                           str(self.cost_file(FULL)))
        self.assert_exit(result, 0)
        last = self.attempts(sid)[-1]
        self.assertEqual(last["outcome"], "applied")
        self.assertEqual(last["command"], "apply")
        self.assertEqual(last["cost"], FULL)
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            NEW_CONTENT, msg="the apply really landed")

    def test_retry_stamps_its_own_attempt(self) -> None:
        """No prior HOLD: retry runs as apply would, through the same
        pipeline, and the attempt it writes carries its file."""
        sid = self.pack()
        result = self.bale("retry", str(self.response(sid, "two")),
                           "--no-interact", "--cost-file",
                           str(self.cost_file(SUBSET)))
        self.assert_exit(result, 0)
        last = self.attempts(sid)[-1]
        self.assertEqual(last["outcome"], "applied")
        self.assertEqual(last["command"], "retry")
        self.assertEqual(last["cost"], dict(ALL_NULL, **SUBSET))

    def test_bad_file_refuses_before_the_pipeline(self) -> None:
        sid = self.pack()
        tarball = self.response(sid, "three")
        before = self.attempts(sid)
        bad = self.cost_file({"models": ["ok", ""]})
        for verb in ("apply", "retry"):
            with self.subTest(verb=verb):
                result = self.bale(verb, str(tarball), "--no-interact",
                                   "--cost-file", str(bad))
                self.assert_exit(result, 1)
                self.assertIn("'models'[1] must be a non-empty string",
                              self.error_line(result.stderr))
                self.assertEqual(self.attempts(sid), before,
                                 msg="no attempt (not even rejected)")
                self.assertEqual(self.open_sids(), [sid])
                self.assertEqual(
                    (self.repo / "hello.txt").read_text(encoding="utf-8"),
                    "hello\n", msg="nothing applied")

    def test_clarification_attempt_carries_the_cost(self) -> None:
        """Since 0.4.63 a clarification landing writes a `clarification`
        attempt (session status-says-more, slip 3), so the validated
        block rides it like every other attempt's; the session stays
        open. (Before 0.4.63 the file was logged as not stamped.)"""
        sid = self.pack()
        before = self.attempts(sid)
        result = self.bale("apply", str(self.clarification(sid)),
                           "--no-interact", "--cost-file",
                           str(self.cost_file(FULL)))
        self.assert_exit(result, 0)
        self.assertNotIn("not stamped", result.stdout)
        after = self.attempts(sid)
        self.assertEqual(after[:len(before)], before)
        self.assertEqual(len(after), len(before) + 1)
        self.assertEqual(after[-1]["outcome"], "clarification")
        self.assertEqual(after[-1]["command"], "apply")
        self.assertEqual(after[-1]["cost"], FULL)
        self.assertEqual(self.open_sids(), [sid])


class CostFileHelpTest(unittest.TestCase):
    """The three verbs' help pages name the flag."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-costhelp-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_help_pages_name_cost_file(self) -> None:
        for verb in ("apply", "retry", "unlock"):
            with self.subTest(verb=verb):
                result = run_bale(self.install, ["help", verb],
                                  cwd=self.tmp, env=self.env)
                self.assertEqual(result.returncode, 0, msg=result.stderr)
                self.assertIn("--cost-file PATH", result.stdout)
                flat = " ".join(result.stdout.split())
                self.assertIn("never by hand", flat)

    def test_revert_takes_no_cost_file(self) -> None:
        result = run_bale(self.install, ["help", "revert"],
                          cwd=self.tmp, env=self.env)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn("--cost-file", result.stdout)


if __name__ == "__main__":
    unittest.main()
