#!/usr/bin/env python3
"""`bale open --json` and `bale relay --json` (v0.4.48; twine's two
`[[wanted]]` entries), end to end against a scratch install and a
scratch git repo (ADR-0005, via tests/harness.py), plus the two
renderers in process.

Pins, per the session brief's outcome contract:

- **open --json, every path that exits 0, prints exactly one stdout
  line**: "opened" (the replayed pack's keys verbatim, folded in — the
  pack's own line is not printed twice), "second-desk" (sid, desk,
  that desk's opener text), "rehearsed" (`--check`, `--dry-run`; every
  pack key null; nothing written — the rehearsal suite's RepoSnapshot).
  Every line carries `bundle` (path, the file's sha256, stem),
  `members` (the published member hashes), `rehearsal`,
  `checkpoint_dry_run` and `desk`; the human-facing lines all ride
  stderr. A refusal stays fail()-shaped: exit 1, nothing on stdout.
- **relay --json prints exactly one stdout line on every path**:
  "relayed" and "re-emitted" carry the block byte-identical to what
  human mode prints (compared against the human no-file re-emit, which
  is itself byte-identical to the original emission), and
  "relay-refused" carries `cause` — the string the relay-refused
  telemetry attempt records — and `telemetry`, the record's path when
  one was written (an ingest refusal) or null (a session gate, a
  missing file). Exit codes unchanged.
- **The renderers' contracts** (format_open_json, format_relay_json in
  bin/bale_report.py): key order, the folded pack keys equal to
  PACK_REPORT_KEYS, and the ValueError guards.

Human mode of both verbs is pinned by their own suites
(test_open_verb, test_rehearsal_verbs, test_relay_verb), which run
unchanged; this suite adds the cross-check that the human block and
the --json block are the same bytes.

Run:  python3 -m unittest tests.test_open_relay_json -v
  or: python3 -m unittest discover -s tests -p 'test_open_relay_json.py'
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness import (
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
from test_open_verb import CP_ERROR, CP_HOLD, sha_lf
from test_rehearsal_verbs import _RehearsalBase
from test_relay_verb import clarification_manifest, planner_answer

OPENER_MARK = "--8<--"  # both scissor lines open with it (bale_pack)

# The pack report line's keys after `outcome`, in order — the
# format_pack_json contract this session extends by `opener`.
PACK_KEYS = [
    "sid", "tarball", "log", "session_dir", "context_files",
    "readme_path", "readme_heading", "readme_sha256",
    "checkpoint_file_path", "checkpoint_file_sha256", "branch",
    "applied_latest", "sweep", "include_group", "opener",
]
OPEN_KEYS = (["outcome"] + PACK_KEYS
             + ["bundle", "members", "rehearsal", "checkpoint_dry_run",
                "desk"])
RELAY_KEYS = ["outcome", "sid", "round", "from", "awaiting", "kind",
              "preserved", "block", "log", "clipboard", "cause",
              "telemetry"]


def one_json_line(testcase: unittest.TestCase, result) -> dict:
    """stdout is exactly one line of JSON; return it parsed."""
    lines = result.stdout.splitlines()
    testcase.assertEqual(
        len(lines), 1,
        msg=f"--json stdout must be exactly one line; got {len(lines)}:\n"
            f"{result.stdout}\nstderr:\n{result.stderr}")
    testcase.assertTrue(result.stdout.endswith("\n"))
    return json.loads(lines[0])


def scissor_paste_text(testcase: unittest.TestCase, text: str) -> str:
    """The lines strictly between the opener's two scissor lines, LF
    joined, one trailing LF — opener_paste_text's definition, recomputed
    here from the printed stream rather than imported."""
    lines = text.split("\n")
    marks = [i for i, ln in enumerate(lines)
             if ln.startswith(OPENER_MARK)]
    testcase.assertEqual(len(marks), 2,
                         msg=f"expected one scissor pair:\n{text}")
    return "\n".join(lines[marks[0] + 1:marks[1]]) + "\n"


# ---------------------------------------------------------------------------
# bale open --json
# ---------------------------------------------------------------------------

class OpenJsonTest(_RehearsalBase):

    BRIEF = "# Bundle brief\n\nbody\n"

    def assert_bundle_keys(self, payload: dict, bundle: Path, *,
                           checkpoint: str | None = None) -> None:
        self.assertEqual(list(payload), OPEN_KEYS)
        self.assertEqual(payload["bundle"], {
            "path": str(bundle.resolve()),
            "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
            "stem": bundle.name[:-len(".bale-bundle")],
        })
        self.assertEqual(payload["members"], {
            "brief": sha_lf(self.BRIEF),
            "checkpoint": sha_lf(checkpoint) if checkpoint else None,
        })

    def test_opened_line_folds_the_pack_report(self) -> None:
        bundle = self.build_bundle("work.bale-bundle",
                                   pack_argv=self.argv("jopen"),
                                   brief=self.BRIEF)
        result = self.open_bundle(bundle, "--json")
        self.assert_ok(result)
        payload = one_json_line(self, result)
        self.assertEqual(payload["outcome"], "opened")
        self.assert_bundle_keys(payload, bundle)
        [sid] = self.open_sids()
        self.assertEqual(payload["sid"], sid)
        self.assertTrue(Path(payload["tarball"]).is_file())
        self.assertEqual(payload["tarball"],
                         str(self.repo.resolve() / ".bale" / "outbox"
                             / f"request-{sid}.tar.gz"))
        self.assertEqual(payload["session_dir"],
                         str(self.repo.resolve() / ".bale" / "sessions"
                             / sid))
        self.assertEqual(payload["readme_sha256"], sha_lf(self.BRIEF))
        self.assertIsNone(payload["checkpoint_file_sha256"])
        self.assertIsInstance(payload["sweep"], list)
        self.assertIsNone(payload["rehearsal"])
        self.assertIsNone(payload["checkpoint_dry_run"])
        self.assertIsNone(payload["desk"])
        # The opener key is the scissor block's paste text, which rides
        # stderr; the pack's own line ("packed") never reaches stdout.
        self.assertEqual(payload["opener"],
                         scissor_paste_text(self, result.stderr))
        self.assertIn(f"This message opens bale session {sid}.",
                      payload["opener"])
        self.assertNotIn('"packed"', result.stdout)
        self.assertNotIn("[bale]", result.stdout)
        self.assertIn("replaying pack invocation", result.stderr)

    def test_opened_with_checkpoint_reports_the_dry_run(self) -> None:
        self.configure_checkpoint()
        self.commit_all("checkpoint config")
        bundle = self.build_bundle("cp.bale-bundle",
                                   pack_argv=self.argv("jcp"),
                                   brief=self.BRIEF, checkpoint=CP_HOLD)
        result = self.open_bundle(bundle, "--json", "--no-sandbox")
        self.assert_ok(result)
        payload = one_json_line(self, result)
        self.assertEqual(payload["outcome"], "opened")
        self.assert_bundle_keys(payload, bundle, checkpoint=CP_HOLD)
        dry = payload["checkpoint_dry_run"]
        self.assertEqual(dry["exit_code"], 1)
        self.assertEqual(dry["log"], str(self.repo.resolve() / ".bale"
                                         / "logs" / "open-cp.log"))
        self.assertTrue(Path(dry["log"]).is_file())
        self.assertEqual(payload["checkpoint_file_sha256"], sha_lf(CP_HOLD))
        # The echoed verdict line is human output: stderr only.
        self.assertIn("[FAIL] the landed marker exists", result.stderr)
        self.assertNotIn("[FAIL]", result.stdout)

    def test_check_json_is_rehearsed_and_writes_nothing(self) -> None:
        bundle = self.build_bundle("chk.bale-bundle",
                                   pack_argv=self.argv("jchk"),
                                   brief=self.BRIEF)
        before = self.snap()
        result = self.open_bundle(bundle, "--check", "--json")
        self.assert_ok(result)
        self.assert_wrote_nothing(before, result)
        payload = one_json_line(self, result)
        self.assertEqual(payload["outcome"], "rehearsed")
        self.assertEqual(payload["rehearsal"], "check")
        self.assert_bundle_keys(payload, bundle)
        for key in PACK_KEYS:
            self.assertIsNone(payload[key], msg=key)
        self.assertIsNone(payload["checkpoint_dry_run"])
        self.assertIsNone(payload["desk"])
        self.assertIn("bale open --check", result.stderr,
                      msg="the rehearsal report rides stderr")

    def test_dry_run_json_reports_the_verdict_and_writes_nothing(
            self) -> None:
        self.configure_checkpoint()
        self.commit_all("checkpoint config")
        bundle = self.build_bundle("dr.bale-bundle",
                                   pack_argv=self.argv("jdr"),
                                   brief=self.BRIEF, checkpoint=CP_HOLD)
        before = self.snap()
        result = self.open_bundle(bundle, "--dry-run", "--no-sandbox",
                                  "--json")
        self.assert_ok(result)
        self.assert_wrote_nothing(before, result)
        payload = one_json_line(self, result)
        self.assertEqual(payload["outcome"], "rehearsed")
        self.assertEqual(payload["rehearsal"], "dry-run")
        self.assert_bundle_keys(payload, bundle, checkpoint=CP_HOLD)
        for key in PACK_KEYS:
            self.assertIsNone(payload[key], msg=key)
        dry = payload["checkpoint_dry_run"]
        self.assertEqual(dry["exit_code"], 1)
        self.assertTrue(Path(dry["log"]).is_file(), msg=dry["log"])
        self.assertFalse(str(Path(dry["log"]).resolve()).startswith(
            str(self.repo.resolve())), msg="a rehearsal's log lives outside")

    def test_dry_run_json_without_a_checkpoint_member(self) -> None:
        bundle = self.build_bundle("nocp.bale-bundle",
                                   pack_argv=self.argv("jnocp"),
                                   brief=self.BRIEF)
        result = self.open_bundle(bundle, "--dry-run", "--json")
        self.assert_ok(result)
        payload = one_json_line(self, result)
        self.assertEqual(payload["rehearsal"], "dry-run")
        self.assertIsNone(payload["checkpoint_dry_run"])

    def read_only_bundle(self) -> Path:
        return self.build_bundle(
            "plan.bale-bundle", brief=self.BRIEF,
            pack_argv=["Plan the next wave", "--slug", "plan",
                       "--read-only", "--include", "hello.txt"])

    def test_second_desk_json(self) -> None:
        bundle = self.read_only_bundle()
        self.assert_ok(self.open_bundle(bundle))
        [sid] = self.open_sids()
        result = self.open_bundle(bundle, "--json")
        self.assert_ok(result)
        payload = one_json_line(self, result)
        self.assertEqual(payload["outcome"], "second-desk")
        self.assert_bundle_keys(payload, bundle)
        self.assertEqual(payload["sid"], sid)
        self.assertEqual(payload["desk"], "desk-2")
        self.assertEqual(payload["opener"],
                         scissor_paste_text(self, result.stderr))
        self.assertIn(f"{sid}@desk-2", payload["opener"])
        # Brief §2.2: every pack-report key but sid and opener is null on
        # a second desk — log included (the HOLD of the first attempt).
        self.assertIsNone(payload["log"])
        self.assertEqual(
            {k: payload[k] for k in PACK_KEYS if k not in ("sid", "opener")},
            {k: None for k in PACK_KEYS if k not in ("sid", "opener")})
        self.assertIsNone(payload["rehearsal"])
        self.assertIsNone(payload["checkpoint_dry_run"])
        self.assertEqual(self.open_sids(), [sid], msg="no sid minted")
        self.assertIn("desk-2", result.stderr,
                      msg="the second-desk summary rides stderr")

    def test_second_desk_rehearsal_json_records_no_desk(self) -> None:
        bundle = self.read_only_bundle()
        self.assert_ok(self.open_bundle(bundle))
        before = self.snap()
        result = self.open_bundle(bundle, "--check", "--json")
        self.assert_ok(result)
        self.assert_wrote_nothing(before, result)
        payload = one_json_line(self, result)
        self.assertEqual(payload["outcome"], "rehearsed")
        self.assertEqual(payload["rehearsal"], "check")
        self.assertIsNone(payload["desk"])
        self.assertIsNone(payload["sid"])
        self.assertIn("would record desk-2", result.stderr)

    def test_refusals_stay_fail_shaped(self) -> None:
        stray = self.tmp / "notabundle.tar.gz"
        stray.write_bytes(b"whatever")
        result = run_bale(self.install, ["open", str(stray), "--json"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("[bale] error:", result.stderr)
        # A defective oracle refuses the whole open the same way.
        self.configure_checkpoint()
        self.commit_all("checkpoint config")
        bundle = self.build_bundle("bad.bale-bundle",
                                   pack_argv=self.argv("jbad"),
                                   checkpoint=CP_ERROR)
        result = self.open_bundle(bundle, "--json", "--no-sandbox")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(result.stdout, "")
        self.assertIn("the checkpoint dry-run exited 2", result.stderr)
        self.assert_no_session_state(result)

    def test_human_open_prints_no_json(self) -> None:
        bundle = self.build_bundle("h.bale-bundle",
                                   pack_argv=self.argv("jhuman"),
                                   brief=self.BRIEF)
        result = self.open_bundle(bundle)
        self.assert_ok(result)
        self.assertFalse(result.stdout.lstrip().startswith("{"))
        self.assertIn("session id:", result.stdout)
        self.assertEqual(scissor_paste_text(self, result.stdout).count(
            "This message opens bale session"), 1)


# ---------------------------------------------------------------------------
# bale relay --json
# ---------------------------------------------------------------------------

class RelayJsonTest(unittest.TestCase):

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-relayjson-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.git_env = git_env(self.home)
        r = run_bale(self.install,
                     ["pack", "relay json goal", "--slug", "rjson",
                      "--include", "hello.txt", "--no-readme"],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        root = self.repo / ".bale" / "sessions"
        [self.sid] = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.session_log = str(self.repo.resolve() / ".bale" / "logs"
                               / f"{self.sid}.log")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def write(self, name: str, payload) -> Path:
        p = self.tmp / name
        p.write_text(payload if isinstance(payload, str)
                     else json.dumps(payload), encoding="utf-8")
        return p

    def relay(self, *args: str, sid: str = None):
        return subprocess.run(
            [sys.executable, str(self.install / "bin" / "bale"), "relay",
             sid or self.sid, *args],
            cwd=self.repo, env=self.env, stdin=subprocess.DEVNULL,
            capture_output=True, timeout=SUBPROCESS_TIMEOUT)

    @staticmethod
    def text(result) -> "subprocess.CompletedProcess":
        """Decode a bytes run's streams in place (UTF-8)."""
        result.stdout = result.stdout.decode("utf-8")
        result.stderr = result.stderr.decode("utf-8")
        return result

    def human_reemit_bytes(self) -> bytes:
        r = self.relay()
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        return r.stdout

    def telemetry_attempts(self) -> list:
        p = self.repo / "claude" / "telemetry" / f"{self.sid}.json"
        return json.loads(p.read_text(encoding="utf-8"))["attempts"]

    def test_relayed_line_carries_the_human_block(self) -> None:
        m = self.write("m.json", clarification_manifest(self.sid))
        result = self.text(self.relay(str(m), "--json"))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = one_json_line(self, result)
        self.assertEqual(list(payload), RELAY_KEYS)
        self.assertEqual(payload["outcome"], "relayed")
        self.assertEqual(payload["sid"], self.sid)
        self.assertEqual(payload["round"], 1)
        self.assertEqual(payload["from"], "worker")
        self.assertEqual(payload["awaiting"], "planner")
        self.assertEqual(payload["kind"], "clarification manifest")
        self.assertEqual(payload["preserved"],
                         f".bale/clarifications/{self.sid}/001.json")
        self.assertTrue((self.repo / payload["preserved"]).is_file())
        self.assertEqual(payload["log"], self.session_log)
        self.assertIs(payload["clipboard"], False)
        self.assertIsNone(payload["cause"])
        self.assertIsNone(payload["telemetry"])
        # stderr is unchanged in kind: the summary and the [bale] lines.
        self.assertIn("[RELAYED]", result.stderr)
        self.assertIn("[bale] relay:", result.stderr)
        # The block is byte-identical to human mode's stdout: the human
        # no-file re-emit is byte-identical to the original emission.
        a, b = self.tmp / "json-block.txt", self.tmp / "human-block.txt"
        a.write_bytes(payload["block"].encode("utf-8"))
        b.write_bytes(self.human_reemit_bytes())
        self.assertEqual(a.read_bytes(), b.read_bytes())
        self.assertTrue(payload["block"].endswith("BALE EXCHANGE END\n"))

    def test_reemitted_line(self) -> None:
        m = self.write("m.json", clarification_manifest(self.sid))
        self.assertEqual(self.relay(str(m)).returncode, 0)
        human = self.human_reemit_bytes()
        result = self.text(self.relay("--json"))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = one_json_line(self, result)
        self.assertEqual(list(payload), RELAY_KEYS)
        self.assertEqual(payload["outcome"], "re-emitted")
        self.assertEqual(payload["round"], 1)
        self.assertEqual(payload["from"], "worker")
        self.assertEqual(payload["awaiting"], "planner")
        self.assertIsNone(payload["kind"])
        self.assertIsNone(payload["preserved"])
        self.assertEqual(payload["block"].encode("utf-8"), human)
        self.assertEqual(payload["log"], self.session_log)
        self.assertIn("[RE-EMITTED]", result.stderr)
        self.assertEqual(
            sorted(p.name for p in (self.repo / ".bale" / "clarifications"
                                    / self.sid).glob("*.json")),
            ["001.json"], msg="re-emit records nothing")

    def test_planner_round_relayed(self) -> None:
        m = self.write("m.json", clarification_manifest(self.sid))
        self.assertEqual(self.relay(str(m)).returncode, 0)
        a = self.write("a.json", planner_answer(self.sid))
        result = self.text(self.relay(str(a), "--json"))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = one_json_line(self, result)
        self.assertEqual(payload["outcome"], "relayed")
        self.assertEqual(payload["round"], 2)
        self.assertEqual(payload["from"], "planner")
        self.assertEqual(payload["awaiting"], "worker")
        self.assertEqual(payload["kind"], "exchange record")
        self.assertEqual(payload["block"].encode("utf-8"),
                         self.human_reemit_bytes())

    def test_ingest_refusal_line_names_cause_and_record(self) -> None:
        bad = self.write("bad.json", {"nope": 1})
        result = self.text(self.relay(str(bad), "--json"))
        self.assertEqual(result.returncode, 1)
        payload = one_json_line(self, result)
        self.assertEqual(list(payload), RELAY_KEYS)
        self.assertEqual(payload["outcome"], "relay-refused")
        self.assertEqual(payload["sid"], self.sid)
        for key in ("round", "from", "awaiting", "kind", "preserved",
                    "block"):
            self.assertIsNone(payload[key], msg=key)
        self.assertIs(payload["clipboard"], False)
        self.assertEqual(payload["log"], self.session_log)
        attempt = self.telemetry_attempts()[-1]
        self.assertEqual(attempt["outcome"], "relay-refused")
        self.assertEqual(payload["cause"], attempt["cause"])
        self.assertIn(f"[bale] error: {payload['cause']}", result.stderr)
        self.assertEqual(payload["telemetry"],
                         f"claude/telemetry/{self.sid}.json")
        self.assertTrue((self.repo / payload["telemetry"]).is_file())

    def test_session_gate_refusals_record_nothing(self) -> None:
        m = self.write("m.json", clarification_manifest(self.sid))
        result = self.text(self.relay(str(m), "--json",
                                      sid="2026-08-29-nothere-001"))
        self.assertEqual(result.returncode, 1)
        payload = one_json_line(self, result)
        self.assertEqual(payload["outcome"], "relay-refused")
        self.assertEqual(payload["sid"], "2026-08-29-nothere-001")
        self.assertIn("is not open in the registry", payload["cause"])
        self.assertIsNone(payload["telemetry"])
        self.assertIsNone(payload["log"],
                          msg="refused before the session log was wired")
        # A held branch refuses after the log is wired, still recording
        # nothing.
        run_checked(["git", "branch", f"bale/{self.sid}"],
                    cwd=self.repo, env=self.git_env)
        result = self.text(self.relay(str(m), "--json"))
        self.assertEqual(result.returncode, 1)
        payload = one_json_line(self, result)
        self.assertEqual(payload["outcome"], "relay-refused")
        self.assertIn("history, not a live thread", payload["cause"])
        self.assertIsNone(payload["telemetry"])
        self.assertEqual(payload["log"], self.session_log)
        self.assertEqual([a["outcome"] for a in self.telemetry_attempts()],
                         ["opened"])

    def test_missing_file_and_empty_thread_refusals(self) -> None:
        result = self.text(self.relay("no-such.json", "--json"))
        self.assertEqual(result.returncode, 1)
        payload = one_json_line(self, result)
        self.assertEqual(payload["outcome"], "relay-refused")
        self.assertIn("exchange file not found", payload["cause"])
        self.assertIsNone(payload["telemetry"])
        result = self.text(self.relay("--json"))
        self.assertEqual(result.returncode, 1)
        payload = one_json_line(self, result)
        self.assertIn("has no recorded rounds", payload["cause"])
        self.assertIsNone(payload["telemetry"])

    def test_clipboard_true_when_copied(self) -> None:
        capture = self.tmp / "clip.txt"
        toml = self.install / "user" / "bale.toml"
        toml.parent.mkdir(parents=True, exist_ok=True)
        toml.write_text(f'[clipboard]\ncommand = "cat >{capture}"\n',
                        encoding="utf-8")
        m = self.write("m.json", clarification_manifest(self.sid))
        result = self.text(self.relay(str(m), "--json"))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = one_json_line(self, result)
        self.assertIs(payload["clipboard"], True)
        self.assertEqual(capture.read_bytes(),
                         payload["block"].encode("utf-8"))

    def test_human_relay_stdout_is_still_the_bare_block(self) -> None:
        m = self.write("m.json", clarification_manifest(self.sid))
        result = self.text(self.relay(str(m)))
        self.assertEqual(result.returncode, 0)
        self.assertTrue(result.stdout.startswith(
            f"BALE EXCHANGE BEGIN {self.sid}\n"))
        self.assertTrue(result.stdout.endswith("BALE EXCHANGE END\n"))

    def test_argparse_error_prints_no_line(self) -> None:
        result = self.text(self.relay("a", "b", "--json"))
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")


# ---------------------------------------------------------------------------
# The renderers, in process
# ---------------------------------------------------------------------------

class RendererContractTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.m = _load_module("bale_report")

    BUNDLE = {"path": "/b/x.bale-bundle", "sha256": "a" * 64, "stem": "x"}
    MEMBERS = {"brief": "b" * 64, "checkpoint": None}

    def pack_line(self) -> dict:
        return json.loads(self.m.format_pack_json(
            sid="s", tarball=Path("/t"), log_path=Path("/l"),
            session_dir=Path("/d"), context_files=1, opener="o\n"))

    def test_pack_report_keys_are_format_pack_jsons(self) -> None:
        self.assertEqual(list(self.pack_line()),
                         list(self.m.PACK_REPORT_KEYS))
        self.assertEqual(list(self.m.PACK_REPORT_KEYS), ["outcome"]
                         + PACK_KEYS)
        self.assertIsNone(json.loads(self.m.format_pack_json(
            sid="s", tarball=Path("/t"), log_path=Path("/l"),
            session_dir=Path("/d"), context_files=1))["opener"])

    def test_opened_folds_the_pack_line_verbatim(self) -> None:
        pack = self.pack_line()
        line = json.loads(self.m.format_open_json(
            outcome="opened", bundle=self.BUNDLE, members=self.MEMBERS,
            pack_report=pack))
        self.assertEqual(list(line), OPEN_KEYS)
        self.assertEqual({k: line[k] for k in PACK_KEYS},
                         {k: pack[k] for k in PACK_KEYS})
        self.assertEqual(line["outcome"], "opened")

    def test_second_desk_nulls_every_pack_key_but_sid_and_opener(
            self) -> None:
        line = json.loads(self.m.format_open_json(
            outcome="second-desk", bundle=self.BUNDLE, members=self.MEMBERS,
            sid="2026-10-07-x-001", opener="o\n", desk="desk-2"))
        self.assertEqual(list(line), OPEN_KEYS)
        self.assertEqual(line["sid"], "2026-10-07-x-001")
        self.assertEqual(line["opener"], "o\n")
        self.assertEqual(line["desk"], "desk-2")
        for key in PACK_KEYS:
            if key not in ("sid", "opener"):
                self.assertIsNone(line[key], msg=key)

    def test_open_guards(self) -> None:
        with self.assertRaises(ValueError):
            self.m.format_open_json(outcome="packed", bundle=self.BUNDLE,
                                    members=self.MEMBERS)
        with self.assertRaises(ValueError):
            self.m.format_open_json(outcome="opened", bundle=self.BUNDLE,
                                    members=self.MEMBERS,
                                    pack_report={"outcome": "packed"})
        with self.assertRaises(ValueError):
            self.m.format_open_json(outcome="rehearsed", bundle=self.BUNDLE,
                                    members=self.MEMBERS)
        with self.assertRaises(ValueError):
            self.m.format_open_json(outcome="rehearsed", bundle=self.BUNDLE,
                                    members=self.MEMBERS, rehearsal="full")
        with self.assertRaises(ValueError):
            self.m.format_open_json(outcome="second-desk",
                                    bundle=self.BUNDLE, members=self.MEMBERS,
                                    rehearsal="check")
        with self.assertRaises(ValueError):
            self.m.format_open_json(outcome="rehearsed", bundle=self.BUNDLE,
                                    members=self.MEMBERS, rehearsal="check",
                                    desk="desk-2")

    def test_open_and_relay_vocabularies(self) -> None:
        self.assertEqual(self.m.OPEN_OUTCOMES,
                         ("opened", "second-desk", "rehearsed"))
        self.assertEqual(self.m.RELAY_OUTCOMES,
                         ("relayed", "re-emitted", "relay-refused"))
        doc = self.m.format_pack_json.__doc__
        for word in self.m.OPEN_OUTCOMES + self.m.RELAY_OUTCOMES:
            self.assertIn(f'"{word}"', doc,
                          msg="the outcome vocabulary is named in "
                              "format_pack_json's docstring")

    def test_relay_line_shapes(self) -> None:
        line = json.loads(self.m.format_relay_refusal_json(
            sid="s", cause="why", log_path=None, telemetry=None))
        self.assertEqual(list(line), RELAY_KEYS)
        self.assertEqual(line["outcome"], "relay-refused")
        self.assertIs(line["clipboard"], False)
        with self.assertRaises(ValueError):
            self.m.format_relay_json(outcome="relay", sid="s")


if __name__ == "__main__":
    unittest.main()
