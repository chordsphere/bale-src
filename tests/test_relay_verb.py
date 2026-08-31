#!/usr/bin/env python3
"""`bale relay <sid> <file|->` end to end (v0.4.18, ADR-0017; contract
BALE.md §8.11, row §11.34).

Pins, against a scratch install and a scratch git repo (ADR-0005; the
test_amend_checkpoint shape — one fixture per scenario):

- **The two ingest paths agree.** A clarification manifest relayed as
  bare JSON is preserved as `001.json` in exactly the shape apply's
  handler leaves (the manifest plus a `preserved_at` sidecar), and the
  planner-facing block relay emits carries the manifest's exchange-
  record reading (`from: worker`, `round` 1, `created_at` = the
  preserved stamp, questions verbatim) which itself validates.
- **The block is the probe's four properties.** Sentinels with the sid,
  a purpose header naming direction and round, the record as the body,
  and a sha256 trailer that ingest verifies — a truncated block, an
  edited body, or a sentinel naming another sid refuses with the
  re-request wording and preserves nothing.
- **Stream discipline.** stdout is the block and only the block; every
  `[bale] ` line and the `[RELAYED]` summary go to stderr.
- **Sequencing — exactly D4's facts.** session_id must equal the sid;
  round must be the thread's next NNN (stale and skipped both refuse
  naming both numbers); round one is worker-only; no alternation rule
  (a worker may post twice).
- **Answer resolvability.** An answers[] row whose (question_round,
  question_index) names no preserved question refuses naming the pair.
- **Session gates.** A sid not open, or one with a bale/<sid> branch,
  refuses before reading the input.
- **What relay never does.** The lock is retained, no telemetry record
  is written, no git ref moves, and a refusal leaves the thread
  directory exactly as it was.
- **Round trips.** relay's own emitted block (with a chat's fence lines
  and CRLF endings around it) is accepted on ingest — it is the wire
  form the courier carries.
- **The no-file re-emit form (v0.4.22, board row 60).** `bale relay
  <sid>` with no file re-emits the latest recorded round's block
  byte-identical to the original emission — for a manifest round and
  for an exchange-record round alike — records nothing (the thread,
  session, and registry are untouched), reports `[RE-EMITTED]` rather
  than `[RELAYED]`, refuses loudly on a sid with no recorded rounds
  naming the sid, and still runs the session gates first.

Run:  python3 -m unittest tests.test_relay_verb -v
  or: python3 -m unittest discover -s tests -p 'test_relay_verb.py'
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
    bale_env,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_checked,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "bin"))
from bale_validate import validate_exchange_record  # noqa: E402

BEGIN = "BALE EXCHANGE BEGIN"
END = "BALE EXCHANGE END"


def clarification_manifest(sid: str, n_questions: int = 2) -> dict:
    """A clarification manifest as the crafter emits it (TARBALL.md
    §5.9.2): empty change surfaces, extended question rows."""
    return {
        "session_id": sid,
        "responds_to": sid,
        "corrects": None,
        "response_kind": "clarification",
        "summary": "blocked on intent-gap questions (fixture)",
        "changes": [],
        "deferred": [],
        "validation_will_run": [],
        "claims": {},
        "questions": [
            {
                "question": f"fixture question {i + 1}?",
                "context": "fixture context",
                "default_assumption": "fixture assumption",
                "why_blocked": "fixture blocker",
                "options": ["yes", "no"],
                "recommendation": "yes",
            }
            for i in range(n_questions)
        ],
    }


def planner_answer(sid: str, round_no: int = 2,
                   question_round: int = 1, question_index: int = 0) -> dict:
    return {
        "record_version": 1,
        "session_id": sid,
        "round": round_no,
        "from": "planner",
        "created_at": "2026-08-29T15:00:00+00:00",
        "answers": [
            {
                "question_round": question_round,
                "question_index": question_index,
                "answer": "yes — the recommendation stands",
                "disposition": "as-recommended",
            }
        ],
    }


def worker_record(sid: str, round_no: int = 1) -> dict:
    return {
        "record_version": 1,
        "session_id": sid,
        "round": round_no,
        "from": "worker",
        "created_at": "2026-08-29T14:00:00+00:00",
        "questions": clarification_manifest(sid, 1)["questions"],
    }


def split_block(stdout: str) -> tuple[str, list, str, str]:
    """Parse relay's stdout as the block: (sid, header lines, body text,
    trailer hex). Asserts the four properties structurally."""
    lines = stdout.split("\n")
    assert lines[0].startswith(BEGIN + " "), lines[:2]
    sid = lines[0][len(BEGIN) + 1:]
    assert END in lines, "no END sentinel"
    end = lines.index(END)
    inner = lines[1:end]
    k = 0
    while inner[k].startswith("#"):
        k += 1
    header = inner[:k]
    trailer = inner[-1]
    assert trailer.startswith("# sha256 "), trailer
    body = "\n".join(inner[k:-1]) + "\n"
    return sid, header, body, trailer.split()[-1]


class RelayVerbTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-relay-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.git_env = git_env(self.home)
        self.sid = self.make_packed_session()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return sorted(d.name for d in root.iterdir()
                      if (d / "open").is_file())

    def make_packed_session(self) -> str:
        result = run_bale(
            self.install,
            ["pack", "relay verb test goal", "--slug", "relay",
             "--include", "hello.txt", "--no-readme"],
            cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 0,
                         msg=f"pack failed:\n{result.stderr}")
        sids = self.open_sids()
        self.assertEqual(len(sids), 1)
        return sids[0]

    def write(self, name: str, payload) -> Path:
        p = self.tmp / name
        text = payload if isinstance(payload, str) else json.dumps(payload)
        p.write_text(text, encoding="utf-8")
        return p

    def relay(self, arg: str = None, *, stdin: str = None, sid: str = None):
        """Run `bale relay <sid> <arg>`; `stdin` feeds `-`. `arg=None`
        runs the no-file re-emit form (v0.4.22)."""
        cmd = [sys.executable, str(self.install / "bin" / "bale"),
               "relay", sid or self.sid]
        if arg is not None:
            cmd.append(arg)
        return subprocess.run(
            cmd, cwd=self.repo, env=self.env,
            input=stdin if stdin is not None else None,
            stdin=subprocess.DEVNULL if stdin is None else None,
            capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT)

    def assert_ok(self, result) -> None:
        self.assertEqual(result.returncode, 0,
                         msg=f"stdout:\n{result.stdout}\nstderr:\n"
                             f"{result.stderr}")

    def assert_refused(self, result, *needles: str) -> None:
        self.assertEqual(result.returncode, 1,
                         msg=f"expected a refusal; stdout:\n{result.stdout}"
                             f"\nstderr:\n{result.stderr}")
        self.assertEqual(result.stdout, "", msg="a refusal emits no block")
        for needle in needles:
            self.assertIn(needle, result.stderr)

    def clar_dir(self) -> Path:
        return self.repo / ".bale" / "clarifications" / self.sid

    def thread_files(self) -> list:
        d = self.clar_dir()
        return sorted(p.name for p in d.glob("*.json")) if d.is_dir() else []

    def relay_round_one(self) -> None:
        """The shared precondition for planner-side scenarios: round one
        (a manifest) already in the thread."""
        self.assert_ok(self.relay(
            str(self.write("m.json", clarification_manifest(self.sid)))))
        self.assertEqual(self.thread_files(), ["001.json"])

    def assert_untouched(self) -> None:
        """A refusal's invariants: session open, no telemetry, no
        bale/<sid> ref."""
        self.assertIn(self.sid, self.open_sids())
        self.assertFalse(
            (self.repo / "claude" / "telemetry" / f"{self.sid}.json").exists())
        r = subprocess.run(["git", "rev-parse", "--verify", "--quiet",
                            f"refs/heads/bale/{self.sid}"],
                           cwd=self.repo, env=self.git_env,
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0, "no bale/<sid> branch")

    # -- pinned behavior 1: the manifest ingest path ---------------------

    def test_manifest_preserved_like_apply_and_block_normalized(self) -> None:
        manifest = clarification_manifest(self.sid)
        result = self.relay(str(self.write("m.json", manifest)))
        self.assert_ok(result)
        self.assertEqual(self.thread_files(), ["001.json"])
        preserved = json.loads(
            (self.clar_dir() / "001.json").read_text(encoding="utf-8"))
        stamp = preserved.pop("preserved_at")
        self.assertTrue(stamp)
        self.assertEqual(preserved, manifest,
                         "the manifest is preserved untouched + the sidecar")
        sid, header, body, digest = split_block(result.stdout)
        self.assertEqual(sid, self.sid)
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), digest)
        self.assertIn("round 1", header[0])
        self.assertIn("from worker to planner", header[0])
        record = json.loads(body)
        self.assertEqual(validate_exchange_record(record), [])
        self.assertEqual(record["from"], "worker")
        self.assertEqual(record["round"], 1)
        self.assertEqual(record["created_at"], stamp)
        self.assertEqual(record["questions"], manifest["questions"])
        self.assertNotIn("preserved_at", record)
        self.assert_untouched()

    def test_stdout_is_only_the_block(self) -> None:
        result = self.relay(
            str(self.write("m.json", clarification_manifest(self.sid))))
        self.assert_ok(result)
        self.assertTrue(result.stdout.startswith(BEGIN + " "))
        self.assertTrue(result.stdout.rstrip("\n").endswith(END))
        self.assertNotIn("[bale]", result.stdout)
        self.assertIn("[bale] relay:", result.stderr)
        self.assertIn("[RELAYED]", result.stderr)
        self.assertIn("Next step", result.stderr)
        self.assertIn("bale relay", result.stderr)

    def test_manifest_with_wrong_sid_refuses(self) -> None:
        other = clarification_manifest("2026-08-29-other-009")
        result = self.relay(str(self.write("m.json", other)))
        self.assert_refused(result, "session_id", "2026-08-29-other-009",
                            "nothing preserved")
        self.assertEqual(self.thread_files(), [])

    def test_manifest_with_bad_question_row_refuses(self) -> None:
        m = clarification_manifest(self.sid)
        m["questions"][0]["priority"] = "urgent"
        result = self.relay(str(self.write("m.json", m)))
        self.assert_refused(result, "question-row gate",
                            "questions[0].priority")
        self.assertEqual(self.thread_files(), [])

    # -- pinned behavior 2: the planner answer path ----------------------

    def test_planner_answer_via_stdin_emits_worker_block(self) -> None:
        self.relay_round_one()
        result = self.relay("-", stdin=json.dumps(planner_answer(self.sid)))
        self.assert_ok(result)
        self.assertEqual(self.thread_files(), ["001.json", "002.json"])
        preserved = json.loads(
            (self.clar_dir() / "002.json").read_text(encoding="utf-8"))
        self.assertIn("preserved_at", preserved)
        self.assertEqual(preserved["from"], "planner")
        _, header, body, digest = split_block(result.stdout)
        self.assertIn("round 2", header[0])
        self.assertIn("from planner to worker", header[0])
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), digest)
        self.assertEqual(json.loads(body), planner_answer(self.sid))
        self.assertIn("carry the block", result.stderr)
        self.assertIn("bale apply", result.stderr)
        self.assert_untouched()

    def test_emitted_block_round_trips_through_ingest(self) -> None:
        """relay's own block, as a courier pastes it (fenced, CRLF), is
        the accepted wire form — here a worker record's block ingested
        as round 1, then the planner's answer built from it."""
        rec = worker_record(self.sid)
        # Relay the bare record to obtain relay's own block, reset the
        # thread, then re-ingest the block as a courier would paste it.
        first = self.relay(str(self.write("w.json", rec)))
        self.assert_ok(first)
        block = first.stdout
        (self.clar_dir() / "001.json").unlink()
        pasted = "Here is the block:\r\n```\r\n" + block.replace("\n", "\r\n") \
            + "```\r\nthanks\r\n"
        second = self.relay(str(self.write("paste.txt", pasted)))
        self.assert_ok(second)
        self.assertIn("paste block read", second.stderr)
        self.assertEqual(self.thread_files(), ["001.json"])
        preserved = json.loads(
            (self.clar_dir() / "001.json").read_text(encoding="utf-8"))
        preserved.pop("preserved_at")
        self.assertEqual(preserved, rec)

    def test_worker_may_post_twice(self) -> None:
        """No from-alternation rule: a worker re-asking before any
        answer is round 2 from worker."""
        self.relay_round_one()
        result = self.relay(str(self.write("w2.json",
                                           worker_record(self.sid, 2))))
        self.assert_ok(result)
        self.assertEqual(self.thread_files(), ["001.json", "002.json"])
        self.assertIn("from worker to planner", result.stdout)

    # -- pinned behavior 3: the paste block's integrity gate --------------

    def test_trailer_mismatch_refuses_with_re_request(self) -> None:
        self.relay_round_one()
        block = self.relay(
            str(self.write("a.json", planner_answer(self.sid)))).stdout
        (self.clar_dir() / "002.json").unlink()
        edited = block.replace('"as-recommended"', '"free-text"')
        result = self.relay(str(self.write("edited.txt", edited)))
        self.assert_refused(result, "integrity trailer disagrees",
                            "re-request")
        self.assertEqual(self.thread_files(), ["001.json"])

    def test_truncated_block_refuses(self) -> None:
        self.relay_round_one()
        block = self.relay(
            str(self.write("a.json", planner_answer(self.sid)))).stdout
        (self.clar_dir() / "002.json").unlink()
        result = self.relay(str(self.write("trunc.txt", block[:200])))
        self.assert_refused(result, "no `BALE EXCHANGE END` sentinel",
                            "truncated")
        self.assertEqual(self.thread_files(), ["001.json"])

    def test_sentinel_naming_another_sid_refuses(self) -> None:
        self.relay_round_one()
        block = self.relay(
            str(self.write("a.json", planner_answer(self.sid)))).stdout
        (self.clar_dir() / "002.json").unlink()
        wrong = block.replace(f"{BEGIN} {self.sid}",
                              f"{BEGIN} 2026-08-29-other-009", 1)
        result = self.relay(str(self.write("wrong.txt", wrong)))
        self.assert_refused(result, "sentinel names session "
                                    "2026-08-29-other-009")
        self.assertEqual(self.thread_files(), ["001.json"])

    def test_non_json_non_block_refuses(self) -> None:
        result = self.relay(str(self.write("junk.txt", "hello there\n")))
        self.assert_refused(result, "neither a BALE EXCHANGE paste block "
                                    "nor valid JSON")
        self.assertEqual(self.thread_files(), [])

    # -- pinned behavior 4: sequencing, exactly D4's facts ----------------

    def test_planner_round_one_refuses(self) -> None:
        # A planner record that passes the library validator (asking
        # only, so no answer keys a round that cannot precede round 1)
        # and still refuses on the worker-only rule.
        rec = planner_answer(self.sid, 1)
        rec["answers"] = []
        rec["questions"] = worker_record(self.sid)["questions"]
        result = self.relay(str(self.write("p1.json", rec)))
        self.assert_refused(result, "round 1 of a thread is worker-only",
                            "nothing preserved")
        self.assertEqual(self.thread_files(), [])

    def test_stale_round_refuses(self) -> None:
        self.relay_round_one()
        rec = worker_record(self.sid, 1)
        result = self.relay(str(self.write("stale.json", rec)))
        self.assert_refused(result, "round is 1 but the thread's next "
                                    "round is 2", "stale")
        self.assertEqual(self.thread_files(), ["001.json"])

    def test_skipped_round_refuses(self) -> None:
        self.relay_round_one()
        result = self.relay(str(self.write("skip.json",
                                           planner_answer(self.sid, 3))))
        self.assert_refused(result, "round is 3 but the thread's next "
                                    "round is 2", "skipped")
        self.assertEqual(self.thread_files(), ["001.json"])

    def test_record_with_wrong_session_id_refuses(self) -> None:
        self.relay_round_one()
        rec = planner_answer("2026-08-29-other-009")
        result = self.relay(str(self.write("other.json", rec)))
        self.assert_refused(result, "session_id is "
                                    "'2026-08-29-other-009', not")
        self.assertEqual(self.thread_files(), ["001.json"])

    def test_invalid_record_refuses_naming_schema_rule(self) -> None:
        self.relay_round_one()
        rec = planner_answer(self.sid)
        rec["answers"][0]["disposition"] = "maybe"
        result = self.relay(str(self.write("bad.json", rec)))
        self.assert_refused(result, "exchange-record.schema.json",
                            "answers[0].disposition: 'maybe'")
        self.assertEqual(self.thread_files(), ["001.json"])

    # -- pinned behavior 5: answer resolvability -------------------------

    def test_unresolved_answer_index_refuses_naming_pair(self) -> None:
        self.relay_round_one()  # two questions: indices 0..1
        rec = planner_answer(self.sid, question_index=5)
        result = self.relay(str(self.write("bad.json", rec)))
        self.assert_refused(result, "do not all resolve",
                            "(question_round 1, question_index 5)",
                            "indices 0..1")
        self.assertEqual(self.thread_files(), ["001.json"])

    def test_unresolved_answer_round_refuses(self) -> None:
        """A round that exists numerically but is not a preserved
        record yet cannot be answered: three rounds in (worker, planner
        asking back nothing, worker) answering round 2 — which carried
        no questions — is unresolved."""
        self.relay_round_one()
        self.assert_ok(self.relay(str(self.write("a.json",
                                                 planner_answer(self.sid)))))
        self.assert_ok(self.relay(str(self.write("w3.json",
                                                 worker_record(self.sid, 3)))))
        rec = planner_answer(self.sid, round_no=4, question_round=2)
        result = self.relay(str(self.write("bad.json", rec)))
        self.assert_refused(result, "question_round 2",
                            "carries no readable questions[]")
        self.assertEqual(self.thread_files(),
                         ["001.json", "002.json", "003.json"])

    # -- pinned behavior 6: session gates --------------------------------

    def test_sid_not_open_refuses(self) -> None:
        result = self.relay(
            str(self.write("m.json", clarification_manifest(self.sid))),
            sid="2026-08-29-nothere-001")
        self.assert_refused(result, "is not open in the registry",
                            f"Open sessions: {self.sid}")

    def test_held_branch_refuses(self) -> None:
        run_checked(["git", "branch", f"bale/{self.sid}"],
                    cwd=self.repo, env=self.git_env)
        result = self.relay(
            str(self.write("m.json", clarification_manifest(self.sid))))
        self.assert_refused(result, f"has a bale/{self.sid} branch",
                            "history, not a live thread")
        self.assertEqual(self.thread_files(), [])

    def test_missing_file_refuses_naming_search(self) -> None:
        result = self.relay("no-such-file.json")
        self.assert_refused(result, "exchange file not found",
                            "no-such-file.json")

    # -- pinned behavior 7: the no-file re-emit form (v0.4.22) -----------

    def test_reemit_manifest_round_is_byte_identical(self) -> None:
        """`bale relay <sid>` re-emits the latest round's block
        byte-identical to the original emission — here round one, a
        preserved clarification manifest, whose block carries the
        manifest's exchange-record reading."""
        original = self.relay(
            str(self.write("m.json", clarification_manifest(self.sid))))
        self.assert_ok(original)
        reemit = self.relay()
        self.assert_ok(reemit)
        self.assertEqual(reemit.stdout, original.stdout,
                         "re-emit is byte-identical to the original "
                         "emission")
        self.assertNotIn("[bale]", reemit.stdout)
        self.assertIn("[RE-EMITTED]", reemit.stderr)
        self.assertNotIn("[RELAYED]", reemit.stderr)
        self.assertIn("Next step", reemit.stderr)
        self.assertEqual(self.thread_files(), ["001.json"],
                         "re-emit records nothing")
        self.assert_untouched()

    def test_reemit_record_round_is_byte_identical(self) -> None:
        """The latest round an exchange record: the planner's answer is
        recorded, its block captured, and the no-file form re-emits the
        same bytes — the preserved_at sidecar never leaks into the
        body."""
        self.relay_round_one()
        original = self.relay(
            str(self.write("a.json", planner_answer(self.sid))))
        self.assert_ok(original)
        reemit = self.relay()
        self.assert_ok(reemit)
        self.assertEqual(reemit.stdout, original.stdout)
        self.assertNotIn("preserved_at", reemit.stdout)
        _, header, body, digest = split_block(reemit.stdout)
        self.assertIn("round 2", header[0])
        self.assertIn("from planner to worker", header[0])
        self.assertEqual(hashlib.sha256(body.encode()).hexdigest(), digest)
        self.assertEqual(json.loads(body), planner_answer(self.sid))
        self.assertEqual(self.thread_files(), ["001.json", "002.json"])
        self.assert_untouched()

    def test_reemit_reemitted_block_round_trips_through_ingest(self) -> None:
        """The re-emitted block is the same wire form the original was:
        a courier can paste it and relay ingests it (here into a fresh
        thread after resetting, as the round-trip test does)."""
        rec = worker_record(self.sid)
        self.assert_ok(self.relay(str(self.write("w.json", rec))))
        block = self.relay().stdout
        (self.clar_dir() / "001.json").unlink()
        second = self.relay(str(self.write("paste.txt", block)))
        self.assert_ok(second)
        preserved = json.loads(
            (self.clar_dir() / "001.json").read_text(encoding="utf-8"))
        preserved.pop("preserved_at")
        self.assertEqual(preserved, rec)

    def test_reemit_empty_thread_refuses_naming_sid(self) -> None:
        result = self.relay()
        self.assert_refused(result, "no recorded rounds", self.sid,
                            "nothing to re-emit")
        self.assertEqual(self.thread_files(), [])
        self.assert_untouched()

    def test_reemit_runs_session_gates(self) -> None:
        """The no-file form is still the relay verb: a sid that is not
        open, or one with a held bale/<sid> branch, refuses before any
        re-emit."""
        result = self.relay(sid="2026-08-29-nothere-001")
        self.assert_refused(result, "is not open in the registry")
        self.relay_round_one()
        run_checked(["git", "branch", f"bale/{self.sid}"],
                    cwd=self.repo, env=self.git_env)
        held = self.relay()
        self.assert_refused(held, f"has a bale/{self.sid} branch")

    # -- pinned behavior 8: the verb is in the CLI surface ---------------

    def test_help_lists_relay(self) -> None:
        result = run_bale(self.install, ["help", "relay"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("<sid>", result.stdout + result.stderr)
        self.assertIn("paste block", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
