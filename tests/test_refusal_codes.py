#!/usr/bin/env python3
"""Reason-coded refusal lines for `bale open`, `bale relay` and `bale
revert` under --json (v0.4.50, session 2026-10-07-refusal-codes-005).

The contract under test (the renderers' docstrings in
bin/bale_report.py own it; BALE.md §6.7, §5.8 and §9.1 name the owner):

- **One line per refusal.** Every refusal of the three verbs that exits
  1 prints exactly one JSON line on stdout — "open-refused",
  "relay-refused", "revert-refused" — beside its unchanged `[bale]
  error:` line on stderr, and still exits 1. `reason` is a code of the
  verb's closed vocabulary (OPEN_/RELAY_/REVERT_REFUSAL_REASONS),
  `cause` the refusal's first line (the stderr text without its
  prefix), and every other key is null (open's `bundle` / `members`
  once known; relay's `log` / `telemetry` as 0.4.48 has them; revert's
  `sid` once there is one).
- **The seam, not a text map.** The code is attached by the refusal
  site through fail(reason=...) (bin/bale) and read back by
  exit_reason; refusal_reason() attaches one on the way out of a call
  into another module. In process: fail() carries the code on the
  exit and prints nothing new; exit_reason honours the vocabulary and
  falls back; refusal_reason never overwrites a site's own code unless
  told to. A structural pin walks the three verbs' modules and
  requires a `reason=` on every fail() call in their refusal paths.
- **Human mode unchanged** for every refusal exercised: the same exit
  code, no JSON on stdout, and the same `[bale] error:` lines on stderr
  as the --json run. (The byte-for-byte comparison against the 0.4.49
  tree is the session's validation.sh's: this suite only has one tree.)
- **Coverage.** Every code of the three vocabularies has a case here,
  or a named reason it cannot be reached hermetically (COVERAGE).

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run:  python3 -m unittest tests.test_refusal_codes -v
  or: python3 -m unittest discover -s tests -p 'test_refusal_codes.py'
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:  # the dotted run form needs it
    sys.path.insert(0, _TESTS_DIR)

from harness import (  # noqa: E402
    BIN_DIR,
    _load_module,
    bale_env,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_checked,
)
from test_open_verb import CP_ERROR, CP_HOLD, _OpenVerbBase  # noqa: E402
from test_relay_verb import (  # noqa: E402
    clarification_manifest,
    planner_answer,
    worker_record,
)


ERROR_PREFIX = "[bale] error: "

# Which test exercises each code, or why none can (the coverage pin).
# A value starting "unreachable:" names the reason; anything else is a
# test method name of this module that must exist.
COVERAGE = {
    "open": {
        "not-a-repo": "test_open_not_a_repo",
        "not-found": "test_open_not_found",
        "not-a-bundle": "test_open_not_a_bundle",
        "manifest-invalid": "test_open_manifest_invalid",
        "member-mismatch": "test_open_member_mismatch",
        "no-validation-base": "test_open_no_validation_base",
        "gate-refused": "test_open_gate_refused",
        "defective-oracle": "test_open_defective_oracle",
        "sandbox-failed": (
            "unreachable: needs a host whose namespace sandbox is "
            "unavailable or whose prologue fails; the suite runs the "
            "dry-run with --no-sandbox and cannot break confinement on "
            "purpose (the code is attached at both bale_open sites, "
            "which the structural pin covers)"),
        "desk-refused": "test_open_desk_refused",
        "pack-refused": "test_open_pack_refused",
        "config-invalid": "test_open_config_invalid",
        "no-git": "test_open_no_git",
        "internal-fault": (
            "unreachable: needs the replayed cmd_pack to exit 0 without "
            "handing back exactly one report line, which no shipped pack "
            "path does — it is the defensive check behind the sink"),
        "unclassified": "test_fallback_when_no_code_rides_the_exit",
    },
    "relay": {
        "not-open": "test_relay_not_open",
        "held-branch": "test_relay_held_branch",
        "not-found": "test_relay_not_found",
        "not-an-object": "test_relay_not_an_object",
        "trailer-mismatch": "test_relay_trailer_mismatch",
        "malformed-block": "test_relay_malformed_block",
        "wrong-session": "test_relay_wrong_session",
        "schema": "test_relay_schema",
        "stale-round": "test_relay_stale_and_skipped_round",
        "skipped-round": "test_relay_stale_and_skipped_round",
        "planner-round-one": "test_relay_planner_round_one",
        "unresolved-answer": "test_relay_unresolved_answer",
        "thread-changed": (
            "unreachable: needs the clarification directory to change "
            "between two reads of one relay run — a race, not a state a "
            "fixture can hold still"),
        "no-rounds": "test_relay_no_rounds",
        "unreadable-record": "test_relay_unreadable_record",
        "unreadable-input": (
            "unreachable: needs a located file (or stdin) whose read "
            "raises OSError; the suite may run as root, where a mode-000 "
            "file still reads"),
        "no-sid": "test_relay_no_sid",
        "not-a-repo": "test_relay_not_a_repo",
        "system-dir": "test_relay_system_dir",
        "config-invalid": "test_relay_config_invalid",
        "no-git": "test_relay_no_git",
        "unclassified": "test_fallback_when_no_code_rides_the_exit",
    },
    "revert": {
        "not-a-repo": "test_revert_not_a_repo",
        "none-open": "test_revert_none_open",
        "several-open": "test_revert_several_open",
        "no-metadata": "test_revert_no_metadata",
        "no-branch": "test_revert_no_branch",
        "already-merged": "test_revert_already_merged",
        "checkout-refused": "test_revert_checkout_refused",
        "system-dir": "test_revert_system_dir",
        "no-git": "test_revert_no_git",
        "unclassified": "test_fallback_when_no_code_rides_the_exit",
    },
}

OUTCOMES = {"open": "open-refused", "relay": "relay-refused",
            "revert": "revert-refused"}


def error_lines(text: str) -> list:
    return [ln for ln in text.splitlines() if ln.startswith(ERROR_PREFIX)]


class _RefusalMixin:
    """The per-refusal assertions every case shares."""

    def run_verb(self, args: list, *, cwd: Path = None, env: dict = None):
        return run_bale(self.install, args, cwd=cwd or self.repo,
                        env=env or self.env)

    def assert_refused_line(self, verb: str, args: list, reason: str, *,
                            cwd: Path = None, env: dict = None) -> dict:
        """Run `args` in human mode, then with --json; assert the refusal
        contract on both and return the parsed --json line."""
        human = self.run_verb(args, cwd=cwd, env=env)
        result = self.run_verb(args + ["--json"], cwd=cwd, env=env)
        msg = (f"human stdout:\n{human.stdout}\nhuman stderr:\n"
               f"{human.stderr}\njson stdout:\n{result.stdout}\n"
               f"json stderr:\n{result.stderr}")
        # Exit codes: 1 in both modes.
        self.assertEqual(human.returncode, 1, msg=msg)
        self.assertEqual(result.returncode, 1, msg=msg)
        # --json: exactly one stdout line, parsed — never compared as text.
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 1, msg=msg)
        self.assertTrue(result.stdout.endswith("\n"), msg=msg)
        payload = json.loads(lines[0])
        self.assertEqual(payload["outcome"], OUTCOMES[verb], msg=msg)
        self.assertEqual(payload["reason"], reason, msg=msg)
        self.assertIsInstance(payload["cause"], str)
        self.assertTrue(payload["cause"], msg=msg)
        # The cause is the stderr error line's first line, prefix dropped.
        self.assertIn(ERROR_PREFIX + payload["cause"], error_lines(
            result.stderr), msg=msg)
        # Human mode: no JSON on stdout, the same error lines on stderr.
        self.assertFalse(any(ln.lstrip().startswith("{")
                             for ln in human.stdout.splitlines()), msg=msg)
        self.assertEqual(error_lines(human.stderr),
                         error_lines(result.stderr), msg=msg)
        self.assertNotIn('"outcome"', human.stderr, msg=msg)
        return payload

    def no_git_env(self) -> dict:
        """The sandbox env with a PATH that holds no git (python itself
        is invoked by absolute path, so nothing else needs PATH)."""
        empty = self.tmp / "empty-path"
        empty.mkdir(exist_ok=True)
        env = dict(self.env)
        env["PATH"] = str(empty)
        return env

    def non_repo_dir(self) -> Path:
        d = self.tmp / "not-a-repo"
        d.mkdir(exist_ok=True)
        return d


# ---------------------------------------------------------------------------
# bale open --json
# ---------------------------------------------------------------------------

OPEN_PACK_KEYS = [
    "sid", "tarball", "log", "session_dir", "context_files",
    "readme_path", "readme_heading", "readme_sha256",
    "checkpoint_file_path", "checkpoint_file_sha256", "branch",
    "applied_latest", "sweep", "include_group", "opener",
]


class OpenRefusalTest(_RefusalMixin, _OpenVerbBase):

    BRIEF = "# Bundle brief\n\nbody\n"

    def refuse(self, bundle_arg: str, reason: str, *extra: str,
               cwd: Path = None, env: dict = None) -> dict:
        payload = self.assert_refused_line(
            "open", ["open", bundle_arg, *extra], reason, cwd=cwd, env=env)
        for key in OPEN_PACK_KEYS + ["rehearsal", "checkpoint_dry_run",
                                     "desk"]:
            self.assertIsNone(payload[key], msg=key)
        return payload

    def assert_bundle_facts(self, payload: dict, bundle: Path) -> None:
        self.assertEqual(payload["bundle"], {
            "path": str(bundle.resolve()),
            "sha256": hashlib.sha256(bundle.read_bytes()).hexdigest(),
            "stem": bundle.name[:-len(".bale-bundle")],
        })

    def test_open_not_a_repo(self) -> None:
        bundle = self.build_bundle("w.bale-bundle",
                                   pack_argv=self.argv("nrepo"))
        payload = self.refuse(str(bundle), "not-a-repo",
                              cwd=self.non_repo_dir())
        self.assertIsNone(payload["bundle"])
        self.assertIsNone(payload["members"])

    def test_open_not_found(self) -> None:
        payload = self.refuse(str(self.tmp / "absent.bale-bundle"),
                              "not-found")
        self.assertIsNone(payload["bundle"])
        # The search-miss branch (a relative name, fail_not_found) too.
        payload = self.refuse("absent.bale-bundle", "not-found")
        self.assertIsNone(payload["bundle"])

    def test_open_not_a_bundle(self) -> None:
        stray = self.tmp / "stray.tar.gz"
        stray.write_bytes(b"whatever")
        payload = self.refuse(str(stray), "not-a-bundle")
        self.assertIsNone(payload["bundle"])
        self.assertIsNone(payload["members"])

    def test_open_manifest_invalid(self) -> None:
        cases = {
            "not a tar": None,
            "validator": {"manifest_override": {"bundle_format": 2}},
            "undeclared": {"extra_members": {"stowaway.txt": b"hi\n"}},
            "missing": {"drop_members": {"brief.md"}},
        }
        for label, knobs in cases.items():
            with self.subTest(label):
                if knobs is None:
                    bundle = self.tmp / "junk.bale-bundle"
                    bundle.write_bytes(b"not a gzip")
                else:
                    bundle = self.build_bundle(
                        f"{label.replace(' ', '-')}.bale-bundle",
                        pack_argv=self.argv("minv"), brief=self.BRIEF,
                        **knobs)
                payload = self.refuse(str(bundle), "manifest-invalid")
                # The file was read: its facts ride the line.
                self.assert_bundle_facts(payload, bundle)
                if label in ("not a tar", "validator"):
                    self.assertIsNone(payload["members"],
                                      msg="refused before the gate passed")
                else:
                    self.assertEqual(payload["members"], {
                        "brief": hashlib.sha256(
                            self.BRIEF.encode()).hexdigest(),
                        "checkpoint": None})
        self.assertFalse((self.repo / ".bale" / "sessions").exists())

    def test_open_member_mismatch(self) -> None:
        bundle = self.build_bundle(
            "mm.bale-bundle", pack_argv=self.argv("mm"), brief=self.BRIEF,
            raw_member_bytes={"brief.md": b"# Tampered\n\nbody\n"})
        payload = self.refuse(str(bundle), "member-mismatch")
        self.assert_bundle_facts(payload, bundle)
        self.assertEqual(payload["members"]["brief"],
                         hashlib.sha256(self.BRIEF.encode()).hexdigest(),
                         msg="the manifest's published hash, gated")
        self.assertIsNone(payload["members"]["checkpoint"])

    def test_open_no_validation_base(self) -> None:
        bundle = self.build_bundle("nvb.bale-bundle",
                                   pack_argv=self.argv("nvb"),
                                   checkpoint=CP_HOLD)
        payload = self.refuse(str(bundle), "no-validation-base")
        self.assert_bundle_facts(payload, bundle)
        self.assertIsNotNone(payload["members"]["checkpoint"])

    def test_open_gate_refused(self) -> None:
        bundle = self.build_bundle(
            "gate.bale-bundle",
            pack_argv=self.argv("gate", "--write", "missing.txt"))
        payload = self.refuse(str(bundle), "gate-refused")
        self.assertIn("--write path does not exist", payload["cause"])
        self.assert_bundle_facts(payload, bundle)
        # A rehearsal's refusal prints the same refused line; rehearsal
        # stays null on it.
        payload = self.refuse(str(bundle), "gate-refused", "--check")
        self.assertIsNone(payload["rehearsal"])

    def test_open_defective_oracle(self) -> None:
        self.configure_checkpoint()
        run_checked(["git", "add", "-A"], cwd=self.repo,
                    env=git_env(self.home))
        run_checked(["git", "commit", "-m", "checkpoint config"],
                    cwd=self.repo, env=git_env(self.home))
        bundle = self.build_bundle("bad.bale-bundle",
                                   pack_argv=self.argv("bad"),
                                   checkpoint=CP_ERROR)
        payload = self.refuse(str(bundle), "defective-oracle",
                              "--no-sandbox")
        self.assertIn("exited 2", payload["cause"])
        self.assertIsNone(payload["checkpoint_dry_run"])

    def read_only_bundle(self) -> Path:
        return self.build_bundle(
            "plan.bale-bundle",
            pack_argv=["Plan the next wave", "--slug", "plan",
                       "--read-only", "--include", "hello.txt"])

    def test_open_desk_refused(self) -> None:
        bundle = self.read_only_bundle()
        first = self.open_bundle(bundle)
        self.assertEqual(first.returncode, 0, msg=first.stderr)
        sessions = self.repo / ".bale" / "sessions"
        [sid] = [p.name for p in sessions.iterdir()
                 if (p / "open").is_file()]
        path = self.repo / "claude" / "telemetry" / f"{sid}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["attempts"].append(dict(record["attempts"][0],
                                       outcome="held", command="apply"))
        path.write_text(json.dumps(record), encoding="utf-8")
        payload = self.refuse(str(bundle), "desk-refused")
        self.assertIn("latest: held", payload["cause"])
        self.assertIsNone(payload["sid"])
        self.assert_bundle_facts(payload, bundle)
        # The rehearsal predicts the same refusal, with the same code.
        self.refuse(str(bundle), "desk-refused", "--check")

    def test_open_pack_refused(self) -> None:
        """A refusal only the replayed pack makes — the context walk's
        hard cap, which the argv-only gates leave to the pack."""
        (self.repo / "second.txt").write_text("two\n", encoding="utf-8")
        run_checked(["git", "add", "-A"], cwd=self.repo,
                    env=git_env(self.home))
        run_checked(["git", "commit", "-m", "second file"], cwd=self.repo,
                    env=git_env(self.home))
        bundle = self.build_bundle(
            "cap.bale-bundle",
            pack_argv=["Capped goal", "--slug", "capped", "--include",
                       "hello.txt", "--include", "second.txt",
                       "--max-files", "1", "--expects-probe", "no"])
        payload = self.refuse(str(bundle), "pack-refused")
        self.assertIn("hard threshold breach", payload["cause"])
        self.assert_bundle_facts(payload, bundle)

    def test_open_config_invalid(self) -> None:
        (self.repo / "bale.toml").write_text(
            "[apply]\nsearch_paths = 5\n", encoding="utf-8")
        bundle = self.build_bundle("cfg.bale-bundle",
                                   pack_argv=self.argv("cfg"))
        self.refuse(str(bundle), "config-invalid")

    def test_open_no_git(self) -> None:
        bundle = self.build_bundle("ng.bale-bundle",
                                   pack_argv=self.argv("ng"))
        self.refuse(str(bundle), "no-git", env=self.no_git_env())

    def test_argparse_error_prints_no_line(self) -> None:
        result = self.run_verb(["open", "--json"])
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stdout, "")


# ---------------------------------------------------------------------------
# bale relay --json
# ---------------------------------------------------------------------------

RELAY_NULL_KEYS = ("round", "from", "awaiting", "kind", "preserved",
                   "block")


def paste_block(sid: str, record: dict, *, trailer: str = None,
                begin_sid: str = None, drop_end: bool = False) -> str:
    """A hand-built exchange paste block (the shape BALE.md §8.11 pins):
    `begin_sid` "" drops the sentinel's sid, `trailer` replaces the
    computed digest, `drop_end` truncates the END line."""
    body = json.dumps(record, indent=2) + "\n"
    digest = trailer or hashlib.sha256(body.encode("utf-8")).hexdigest()
    begin_sid = sid if begin_sid is None else begin_sid
    begin = "BALE EXCHANGE BEGIN" + (f" {begin_sid}" if begin_sid else "")
    text = f"{begin}\n# header\n{body}# sha256 {digest}\n"
    return text + ("" if drop_end else "BALE EXCHANGE END\n")


class RelayRefusalTest(_RefusalMixin, unittest.TestCase):

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-relaycode-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        r = run_bale(self.install,
                     ["pack", "relay code goal", "--slug", "rcode",
                      "--include", "hello.txt", "--no-readme"],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        root = self.repo / ".bale" / "sessions"
        [self.sid] = [d.name for d in root.iterdir()
                      if (d / "open").is_file()]

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def write(self, name: str, payload) -> Path:
        p = self.tmp / name
        p.write_text(payload if isinstance(payload, str)
                     else json.dumps(payload), encoding="utf-8")
        return p

    def refuse(self, args: list, reason: str, *, sid: str = None,
               cwd: Path = None, env: dict = None) -> dict:
        payload = self.assert_refused_line(
            "relay", ["relay", self.sid if sid is None else sid, *args],
            reason, cwd=cwd, env=env)
        for key in RELAY_NULL_KEYS:
            self.assertIsNone(payload[key], msg=key)
        self.assertIs(payload["clipboard"], False)
        return payload

    def record_round_one(self) -> None:
        m = self.write("round1.json", clarification_manifest(self.sid))
        r = run_bale(self.install, ["relay", self.sid, str(m)],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, msg=r.stderr)

    def test_relay_not_open(self) -> None:
        m = self.write("m.json", clarification_manifest(self.sid))
        payload = self.refuse([str(m)], "not-open",
                              sid="2026-08-29-nothere-001")
        self.assertIsNone(payload["log"])

    def test_relay_held_branch(self) -> None:
        run_checked(["git", "branch", f"bale/{self.sid}"], cwd=self.repo,
                    env=self.genv)
        m = self.write("m.json", clarification_manifest(self.sid))
        self.refuse([str(m)], "held-branch")

    def test_relay_not_found(self) -> None:
        self.refuse(["no-such.json"], "not-found")
        self.refuse([str(self.tmp / "absent.json")], "not-found")

    def test_relay_not_an_object(self) -> None:
        for label, text in (("empty", ""), ("not json", "{nope"),
                            ("array", "[1, 2]")):
            with self.subTest(label):
                self.refuse([str(self.write(f"{label}.txt", text))],
                            "not-an-object")

    def test_relay_trailer_mismatch(self) -> None:
        block = paste_block(self.sid, clarification_manifest(self.sid),
                            trailer="0" * 64)
        payload = self.refuse([str(self.write("b.txt", block))],
                              "trailer-mismatch")
        self.assertIsNotNone(payload["telemetry"],
                             msg="an ingest refusal still records")

    def test_relay_malformed_block(self) -> None:
        record = clarification_manifest(self.sid)
        for label, block in (
                ("no END", paste_block(self.sid, record, drop_end=True)),
                ("no sid", paste_block(self.sid, record, begin_sid=""))):
            with self.subTest(label):
                self.refuse([str(self.write("mb.txt", block))],
                            "malformed-block")

    def test_relay_wrong_session(self) -> None:
        other = "2026-08-29-other-001"
        cases = {
            "sentinel": paste_block(other, clarification_manifest(other)),
            "manifest": json.dumps(clarification_manifest(other)),
        }
        for label, text in cases.items():
            with self.subTest(label):
                self.refuse([str(self.write("ws.txt", text))],
                            "wrong-session")
        self.record_round_one()
        rec = planner_answer(other)
        self.refuse([str(self.write("ws2.json", rec))], "wrong-session")

    def test_relay_schema(self) -> None:
        self.refuse([str(self.write("s.json", {"nope": 1}))], "schema")
        bad = clarification_manifest(self.sid)
        bad["questions"] = []
        self.refuse([str(self.write("q.json", bad))], "schema")

    def test_relay_stale_and_skipped_round(self) -> None:
        self.record_round_one()
        self.refuse([str(self.write("skip.json",
                                    planner_answer(self.sid, round_no=3)))],
                    "skipped-round")
        self.refuse([str(self.write("stale.json",
                                    worker_record(self.sid, 1)))],
                    "stale-round")

    def test_relay_planner_round_one(self) -> None:
        # test_relay_verb's fixture: a planner record that passes the
        # schema (asking only) and refuses on the worker-only rule.
        rec = planner_answer(self.sid, 1)
        rec["answers"] = []
        rec["questions"] = worker_record(self.sid)["questions"]
        self.refuse([str(self.write("p1.json", rec))], "planner-round-one")

    def test_relay_unresolved_answer(self) -> None:
        self.record_round_one()
        rec = planner_answer(self.sid, question_index=9)
        self.refuse([str(self.write("ua.json", rec))], "unresolved-answer")

    def test_relay_no_rounds(self) -> None:
        payload = self.refuse([], "no-rounds")
        self.assertIsNone(payload["telemetry"])

    def test_relay_unreadable_record(self) -> None:
        self.record_round_one()
        latest = (self.repo / ".bale" / "clarifications" / self.sid
                  / "001.json")
        latest.write_text("{truncated", encoding="utf-8")
        self.refuse([], "unreadable-record")

    def test_relay_no_sid(self) -> None:
        self.refuse([], "no-sid", sid=" ")

    def test_relay_not_a_repo(self) -> None:
        payload = self.refuse(["x.json"], "not-a-repo",
                              cwd=self.non_repo_dir())
        self.assertIsNone(payload["log"])

    def test_relay_system_dir(self) -> None:
        self.refuse(["x.json"], "system-dir", cwd=self.home)

    def test_relay_config_invalid(self) -> None:
        (self.repo / "bale.toml").write_text(
            "[apply]\nsearch_paths = 5\n", encoding="utf-8")
        self.refuse(["x.json"], "config-invalid")

    def test_relay_no_git(self) -> None:
        self.refuse(["x.json"], "no-git", env=self.no_git_env())


# ---------------------------------------------------------------------------
# bale revert --json
# ---------------------------------------------------------------------------

REVERT_NULL_KEYS = ("log", "closure_reason", "origin_branch",
                    "branch_deleted", "staging_state", "staging_path",
                    "telemetry", "sweep")


class RevertRefusalTest(_RefusalMixin, unittest.TestCase):

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-revcode-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def git(self, *args: str) -> None:
        run_checked(["git", *args], cwd=self.repo, env=self.genv)

    def pack(self, slug: str, include: str = "hello.txt") -> str:
        r = run_bale(self.install,
                     ["pack", f"revert code goal {slug}", "--slug", slug,
                      "--include", include, "--write", include,
                      "--no-readme"],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        return [ln for ln in r.stdout.splitlines()
                if "session id:" in ln][0].split("session id:")[1].strip()

    def held(self, slug: str = "revcode") -> str:
        """test_revert_json's make_held_session shape: a real pack, then
        a plain-git bale/<sid> branch with one session commit."""
        sid = self.pack(slug)
        self.git("checkout", "-b", f"bale/{sid}")
        (self.repo / "widget.txt").write_text("bale change\n",
                                              encoding="utf-8")
        self.git("add", "widget.txt")
        self.git("commit", "-m", f"[bale {sid}] add the widget file")
        self.git("checkout", "main")
        return sid

    def refuse(self, args: list, reason: str, *, cwd: Path = None,
               env: dict = None) -> dict:
        payload = self.assert_refused_line(
            "revert", ["revert", *args], reason, cwd=cwd, env=env)
        for key in REVERT_NULL_KEYS:
            self.assertIsNone(payload[key], msg=key)
        self.assertIs(payload["lock_cleared"], False)
        return payload

    def test_revert_not_a_repo(self) -> None:
        payload = self.refuse([], "not-a-repo", cwd=self.non_repo_dir())
        self.assertIsNone(payload["sid"])

    def test_revert_none_open(self) -> None:
        payload = self.refuse([], "none-open")
        self.assertIsNone(payload["sid"])

    def test_revert_several_open(self) -> None:
        self.pack("first")
        (self.repo / "other.txt").write_text("o\n", encoding="utf-8")
        self.git("add", "other.txt")
        self.git("commit", "-m", "other file")
        self.pack("second", include="other.txt")
        payload = self.refuse([], "several-open")
        self.assertIsNone(payload["sid"])

    def test_revert_no_metadata(self) -> None:
        sid = "2026-08-29-nothere-001"
        payload = self.refuse([sid], "no-metadata")
        self.assertEqual(payload["sid"], sid)

    def test_revert_no_branch(self) -> None:
        sid = self.pack("nobranch")
        # Implicit resolution: the line names the sid the registry gave.
        payload = self.refuse([], "no-branch")
        self.assertEqual(payload["sid"], sid)
        self.assertIn(f"no branch bale/{sid}", payload["cause"])

    def test_revert_already_merged(self) -> None:
        sid = self.held("merged")
        self.git("merge", "--no-edit", f"bale/{sid}")
        payload = self.refuse([sid], "already-merged")
        self.assertEqual(payload["sid"], sid)

    def test_revert_checkout_refused(self) -> None:
        sid = self.held("dirty")
        self.git("checkout", f"bale/{sid}")
        (self.repo / "widget.txt").write_text("local edit\n",
                                              encoding="utf-8")
        payload = self.refuse([sid], "checkout-refused")
        self.assertEqual(payload["sid"], sid)

    def test_revert_system_dir(self) -> None:
        self.refuse([], "system-dir", cwd=self.home)

    def test_revert_no_git(self) -> None:
        self.refuse([], "no-git", env=self.no_git_env())

    def test_reverted_line_carries_null_reason_and_cause(self) -> None:
        sid = self.held("ok")
        result = run_bale(self.install, ["revert", sid, "--json"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["outcome"], "reverted")
        self.assertIsNone(payload["reason"])
        self.assertIsNone(payload["cause"])

    def test_human_revert_still_logs_the_sid_on_stdout(self) -> None:
        """brief §2.3: `[bale] revert: <sid>` keeps reaching stdout in
        human mode before a refusal past the resolution."""
        sid = self.pack("humanlog")
        result = run_bale(self.install, ["revert"], cwd=self.repo,
                          env=self.env)
        self.assertEqual(result.returncode, 1)
        self.assertIn(f"[bale] revert: {sid}", result.stdout)


# ---------------------------------------------------------------------------
# The seam, in process, and the structural pins
# ---------------------------------------------------------------------------

class SeamTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        from harness import _load_cli
        cls.cli = _load_cli()
        cls.report = _load_module("bale_report")

    def test_fail_carries_the_code_beside_the_cause(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with open(os.devnull, "w") as devnull:
                old, sys.stderr = sys.stderr, devnull
                try:
                    self.cli.fail("first line\nsecond", reason="no-branch")
                finally:
                    sys.stderr = old
        exc = ctx.exception
        self.assertEqual(exc.code, 1)
        self.assertEqual(exc.bale_reason, "no-branch")
        self.assertEqual(exc.bale_cause, "first line")
        self.assertEqual(self.cli.exit_cause(exc), "first line")

    def test_fail_without_a_code_carries_none(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with open(os.devnull, "w") as devnull:
                old, sys.stderr = sys.stderr, devnull
                try:
                    self.cli.fail("why")
                finally:
                    sys.stderr = old
        self.assertIsNone(ctx.exception.bale_reason)

    def test_fallback_when_no_code_rides_the_exit(self) -> None:
        """The fallback code ("unclassified") of each vocabulary: an exit
        that carries no code, or one outside the verb's vocabulary,
        reads as the fallback — never a crash, never a bare line."""
        r = self.report
        for vocab in (r.OPEN_REFUSAL_REASONS, r.RELAY_REFUSAL_REASONS,
                      r.REVERT_REFUSAL_REASONS):
            self.assertIn(r.REFUSAL_REASON_FALLBACK, vocab)
            bare = SystemExit(1)
            self.assertEqual(self.cli.exit_reason(
                bare, vocab, r.REFUSAL_REASON_FALLBACK), "unclassified")
            stray = SystemExit(1)
            stray.bale_reason = "not-a-code-anywhere"
            with open(os.devnull, "w") as devnull:
                saved = sys.stdout, sys.stderr
                sys.stdout = sys.stderr = devnull
                try:
                    got = self.cli.exit_reason(
                        stray, vocab, r.REFUSAL_REASON_FALLBACK)
                finally:
                    sys.stdout, sys.stderr = saved
            self.assertEqual(got, "unclassified")
            known = SystemExit(1)
            known.bale_reason = vocab[0]
            self.assertEqual(self.cli.exit_reason(
                known, vocab, r.REFUSAL_REASON_FALLBACK), vocab[0])

    def test_refusal_reason_attaches_without_overwriting(self) -> None:
        with self.assertRaises(SystemExit) as ctx:
            with self.cli.refusal_reason("gate-refused"):
                raise SystemExit(1)
        self.assertEqual(ctx.exception.bale_reason, "gate-refused")
        inner = SystemExit(1)
        inner.bale_reason = "not-found"
        with self.assertRaises(SystemExit) as ctx:
            with self.cli.refusal_reason("gate-refused"):
                raise inner
        self.assertEqual(ctx.exception.bale_reason, "not-found")
        with self.assertRaises(SystemExit) as ctx:
            with self.cli.refusal_reason("gate-refused", override=True):
                raise inner
        self.assertEqual(ctx.exception.bale_reason, "gate-refused")
        with self.assertRaises(SystemExit) as ctx:
            with self.cli.refusal_reason("gate-refused"):
                raise SystemExit(0)
        self.assertFalse(hasattr(ctx.exception, "bale_reason"))

    def test_every_fail_site_names_a_code(self) -> None:
        """The structural pin: every fail()/_fail() call in the three
        verbs' refusal paths passes `reason=` — so no site falls through
        to the fallback by omission."""
        targets = {
            "bale_open.py": None,
            "bale_relay.py": None,
            "bale": {"_cmd_revert", "_discard_hold_state",
                     "resolve_open_session", "refuse_system_dir",
                     "repo_root", "fail_not_found"},
        }
        missing = []
        for name, funcs in targets.items():
            tree = ast.parse((BIN_DIR / name).read_text(encoding="utf-8"))
            for fn in ast.walk(tree):
                if not isinstance(fn, ast.FunctionDef):
                    continue
                if funcs is not None and fn.name not in funcs:
                    continue
                for call in ast.walk(fn):
                    if (isinstance(call, ast.Call)
                            and isinstance(call.func, ast.Name)
                            and call.func.id in ("fail", "_fail", "_fail_")
                            and "reason" not in [k.arg for k in
                                                 call.keywords]):
                        missing.append(f"{name}:{fn.name}:{call.lineno}")
        self.assertEqual(missing, [])

    def test_vocabularies_are_closed_and_documented(self) -> None:
        r = self.report
        for vocab, fn in ((r.OPEN_REFUSAL_REASONS, r.format_open_json),
                          (r.RELAY_REFUSAL_REASONS, r.format_relay_json),
                          (r.REVERT_REFUSAL_REASONS, r.format_revert_json)):
            self.assertEqual(len(vocab), len(set(vocab)))
            for code in vocab:
                self.assertIn(f'"{code}"', fn.__doc__,
                              msg=f"{code} has its docstring line")
        with self.assertRaises(ValueError):
            r.format_open_refusal_json(reason="nope", cause="c",
                                       bundle=None, members=None)
        with self.assertRaises(ValueError):
            r.format_open_refusal_json(reason="not-found", cause="",
                                       bundle=None, members=None)
        with self.assertRaises(ValueError):
            r.format_relay_refusal_json(sid="s", reason="nope", cause="c",
                                        log_path=None, telemetry=None)
        with self.assertRaises(ValueError):
            r.format_revert_refusal_json(reason="nope", cause="c", sid=None)
        with self.assertRaises(ValueError):
            r.format_relay_json(outcome="relayed", sid="s",
                                reason="not-open")
        with self.assertRaises(ValueError):
            r.format_revert_json(sid="s", reason="no-branch", cause="c")
        with self.assertRaises(ValueError):
            r.format_open_json(outcome="rehearsed", rehearsal="check",
                               bundle={}, members={}, reason="not-found",
                               cause="c")
        with self.assertRaises(ValueError):
            r.format_open_json(outcome="opened", bundle={}, members={},
                               tarball="/t")
        doc = r.format_pack_json.__doc__
        for word in ("open-refused", "revert-refused"):
            self.assertIn(f'"{word}"', doc)

    def test_unlock_vocabulary_unmoved(self) -> None:
        self.assertEqual(self.report.UNLOCK_REFUSAL_REASONS, (
            "hold-branch", "not-open", "several-open", "not-a-repo",
            "integration-json"))

    def test_exchange_sentinels_have_one_home(self) -> None:
        relay = _load_module("bale_relay")
        self.assertIs(relay.EXCHANGE_BLOCK_BEGIN,
                      self.report.EXCHANGE_BLOCK_BEGIN)
        self.assertIs(relay.EXCHANGE_BLOCK_END,
                      self.report.EXCHANGE_BLOCK_END)
        self.assertEqual(self.report.EXCHANGE_BLOCK_BEGIN,
                         "BALE EXCHANGE BEGIN")
        self.assertEqual(self.report.EXCHANGE_BLOCK_END, "BALE EXCHANGE END")
        src = (BIN_DIR / "bale_relay.py").read_text(encoding="utf-8")
        self.assertNotIn('EXCHANGE_BLOCK_BEGIN = "', src)
        self.assertNotIn('EXCHANGE_BLOCK_END = "', src)

    def test_help_names_the_refusal_outcome_and_the_owner(self) -> None:
        parser = self.cli.build_parser()
        sub = next(a for a in parser._actions
                   if a.__class__.__name__ == "_SubParsersAction")
        for verb, outcome, owner in (
                ("open", "open-refused", "format_open_json"),
                ("relay", "relay-refused", "format_relay_json"),
                ("revert", "revert-refused", "format_revert_json")):
            p = sub.choices[verb]
            [flag] = [a for a in p._actions if "--json" in a.option_strings]
            self.assertIn(f"'{outcome}'", flag.help, msg=verb)
            self.assertIn(owner, flag.help, msg=verb)
            self.assertIn("reason code", flag.help, msg=verb)


class CoverageTest(unittest.TestCase):

    def test_every_code_has_a_case_or_a_named_reason(self) -> None:
        r = _load_module("bale_report")
        vocabs = {"open": r.OPEN_REFUSAL_REASONS,
                  "relay": r.RELAY_REFUSAL_REASONS,
                  "revert": r.REVERT_REFUSAL_REASONS}
        classes = (OpenRefusalTest, RelayRefusalTest, RevertRefusalTest,
                   SeamTest)
        for verb, vocab in vocabs.items():
            self.assertEqual(set(COVERAGE[verb]), set(vocab), msg=verb)
            for code, how in COVERAGE[verb].items():
                if how.startswith("unreachable:"):
                    self.assertGreater(len(how), len("unreachable: "),
                                       msg=f"{verb} {code}")
                    continue
                self.assertTrue(any(hasattr(c, how) for c in classes),
                                msg=f"{verb} {code}: no test {how}")


if __name__ == "__main__":
    unittest.main()
