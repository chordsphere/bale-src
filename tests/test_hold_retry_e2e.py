#!/usr/bin/env python3
"""Hermetic HOLD→retry multi-attempt E2E (board 5 D7.4; session 25's
deferred fixture).

Drives the full write path the ledger reads: `bale pack` → `bale apply`
of a response whose validation.sh fails (piped default: HOLD/inspect) →
`bale retry` with a corrected response (piped default: PASS/merge), and
asserts the one-file-per-sid append semantics BALE.md §8.9 promises:

- the HOLD attempt and the applied attempt accumulate in the SAME
  record, in order, each carrying its own validation state/exit;
- the envelope mirrors the latest attempt (`outcome`, `updated_at`)
  while `created_at` is preserved from the first;
- the close-time clarification stamp (v0.3.23, board 5 D1) lands on
  the CLOSING attempt only — the applied attempt carries the
  known-zero `{rounds: 0, records: []}`, the held attempt carries no
  key at all;
- the merge really landed: `applied/<sid>` tag, changed file content
  on the origin branch.

Board 35 (small pins, gap 6) added the third TARBALL.md section 7.5
exit code: a validation.sh that itself errors (exit 2, distinct from
a check failure's exit 1) rides the same HOLD path — held branch,
piped-default inspect, exit 1 — with the exit code carried faithfully
into the walkthrough row and the telemetry record, which is where the
"validation found a problem" vs "validation itself broke" distinction
survives for the planner.

The response tarballs are built via the shared harness fixture builder
(computed hashes, real validation.sh scripts; extracted to
``tests/harness.py`` at board 35) so the failure and the fix are
exactly one exit-code apart — the ADR-0002 oracle is the documented record shape,
never a golden byte comparison.

Board 71 (v0.4.25) added ``RetryArtifactResolutionTest``: `bale
retry` resolves its session from the tarball's own responds_to
however many sessions are open, --sid demoted to vetting. Pinned:
multi-open resolution with no --sid; the --sid mismatch refusal
naming both sids and the tarball; the closed-vs-unknown naming when
responds_to names no open session; and the resolve-before-wipe
ordering the desk explicitly wants — every one of those refusals
leaves the HOLD state (branch, staging stamp, open marker, and the
new HOLD-time ``held_tarball`` stamp) exactly as it was.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_hold_retry_e2e.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from harness import (
    bale_env,
    build_response_dir,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_checked,
    slow,
    tar_response_dir,
)
import subprocess

# Sentinels for the surfaces this file pins.
HOLD_HEADLINE = "[HOLD]"
PASS_HEADLINE = "[PASS]"
RECORDED_MARKER = "recorded claude/telemetry/"

KNOWN_ZERO = {"rounds": 0, "records": []}

NEW_CONTENT = "hello from the corrected response\n"


class HoldRetryE2ETest(unittest.TestCase):
    """apply HOLD → retry PASS appends attempts[] and mirrors the
    envelope; the clarification stamp sits on the closing attempt only."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-holdretry-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def packed_sid(self) -> str:
        result = run_bale(
            self.install,
            [
                "pack", "hold-retry e2e goal: rewrite hello.txt",
                "--slug", "hold-retry",
                "--include", "hello.txt",
                "--no-readme",
            ],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        return sids[0]

    def build_response_tarball(self, sid: str, *, name: str,
                               validation_exit: int) -> Path:
        """A valid normal response modifying hello.txt (in scope), whose
        validation.sh exits `validation_exit` — 1 drives the HOLD, 0
        the retry's PASS. Built via the shared harness builder (board
        35 extraction), which computes sizes and hashes from the bytes
        it writes — never transcribed."""
        verdict = "FAIL" if validation_exit else "PASS"
        rdir = build_response_dir(
            self.tmp / name, sid,
            summary="hold-retry fixture: rewrite hello.txt; the first "
                    "attempt's validation fails by construction",
            entries=[{
                "path": "hello.txt",
                "action": "modified",
                "reason": "the goal's rewrite; identical bytes on both "
                          "attempts so only the validation verdict differs",
                "data": NEW_CONTENT.encode("utf-8"),
            }],
            validation_sh=(
                "#!/usr/bin/env bash\n"
                f"echo \"[{verdict}] fixture check\"\n"
                f"exit {validation_exit}\n"),
        )
        return tar_response_dir(rdir)

    def telemetry_record(self, sid: str) -> dict:
        p = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(p.is_file(), msg=f"expected telemetry record at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    # -- the E2E ---------------------------------------------------------

    @slow
    def test_hold_then_retry_appends_and_mirrors(self) -> None:
        sid = self.packed_sid()

        # Attempt 1: validation fails → piped default is inspect → HOLD.
        holding = self.build_response_tarball(sid, name="first",
                                              validation_exit=1)
        held = run_bale(self.install, ["apply", str(holding)],
                        cwd=self.repo, env=self.env)
        self.assertEqual(held.returncode, 1,
                         msg=f"stdout:\n{held.stdout}\nstderr:\n{held.stderr}")
        self.assertIn(HOLD_HEADLINE, held.stdout)
        self.assertIn(RECORDED_MARKER, held.stdout)

        # v0.4.21: the record was CREATED at session open with an
        # `opened` attempt; the HOLD is the first close-side event and
        # APPENDS to it, so the held record carries two attempts.
        record = self.telemetry_record(sid)
        self.assertEqual(record["outcome"], "held")
        self.assertEqual(len(record["attempts"]), 2,
                         msg="open-time record + the HOLD append")
        opened_attempt = record["attempts"][0]
        self.assertEqual(opened_attempt["outcome"], "opened")
        self.assertEqual(opened_attempt["command"], "pack")
        self.assertIsNone(opened_attempt["validation"],
                          msg="nothing ran at open; nothing to record")
        created_at = record["created_at"]
        self.assertEqual(created_at, opened_attempt["at"],
                         msg="the envelope's created_at is the open "
                             "stamp, not the first close event's")

        # Attempt 2: corrected response → retry → PASS → piped merge.
        fixed = self.build_response_tarball(sid, name="second",
                                            validation_exit=0)
        merged = run_bale(self.install, ["retry", str(fixed)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            merged.returncode, 0,
            msg=f"stdout:\n{merged.stdout}\nstderr:\n{merged.stderr}")
        self.assertIn(PASS_HEADLINE, merged.stdout)

        # One file per sid; the retry APPENDED — the open-time attempt
        # plus both close-side events, in order.
        record = self.telemetry_record(sid)
        self.assertEqual(len(record["attempts"]), 3,
                         msg="opened + HOLD + retry accumulate in one "
                             "record")
        opened_attempt, held_attempt, applied_attempt = record["attempts"]
        self.assertEqual(opened_attempt["outcome"], "opened")

        self.assertEqual(held_attempt["outcome"], "held")
        self.assertEqual(held_attempt["command"], "apply")
        self.assertEqual(held_attempt["validation"]["state"], "HOLD")
        self.assertEqual(held_attempt["validation"]["exit_code"], 1)

        self.assertEqual(applied_attempt["outcome"], "applied")
        self.assertEqual(applied_attempt["command"], "retry")
        self.assertEqual(applied_attempt["validation"]["state"], "PASS")
        self.assertEqual(applied_attempt["validation"]["exit_code"], 0)

        # Envelope mirroring (§8.9): outcome/updated_at track the latest
        # attempt; created_at is preserved from the first.
        self.assertEqual(record["outcome"], "applied")
        self.assertEqual(record["updated_at"], applied_attempt["at"])
        self.assertEqual(record["created_at"], created_at)

        # The clarification stamp (board 5 D1) sits on the CLOSING
        # attempt only: known-zero on the applied close, no key at all
        # on the held attempt.
        self.assertNotIn("clarification", held_attempt,
                         msg="a HOLD is not a closure; no stamp")
        self.assertEqual(applied_attempt["clarification"], KNOWN_ZERO)

        # The merge really landed.
        env = git_env(self.home)
        run_checked(["git", "rev-parse", "--verify",
                     f"refs/tags/applied/{sid}"], cwd=self.repo, env=env)
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            NEW_CONTENT)


    # -- board 35 gap 6: validation.sh exit 2 (script errored) -----------

    def test_validation_exit2_holds_and_records_exit_code(self) -> None:
        """A validation.sh that ERRORS (exit 2, TARBALL.md section 7.5 —
        the script broke, not a check) holds exactly like a check
        failure: held branch, piped-default inspect, apply exit 1 — with
        the raw exit code carried into the walkthrough's validation row
        and the telemetry attempt, where the 1-vs-2 distinction remains
        readable after the fact."""
        sid = self.packed_sid()
        rdir = build_response_dir(
            self.tmp / "errored", sid,
            summary="exit-2 fixture: rewrite hello.txt; validation.sh "
                    "errors by construction before any check completes",
            entries=[{
                "path": "hello.txt",
                "action": "modified",
                "reason": "the goal's rewrite; never merges — the "
                          "errored validation holds it",
                "data": NEW_CONTENT.encode("utf-8"),
            }],
            validation_sh=(
                "#!/usr/bin/env bash\n"
                "echo 'validation.sh: fixture script error' >&2\n"
                "exit 2\n"),
        )
        result = run_bale(self.install,
                          ["apply", str(tar_response_dir(rdir))],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 1,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn(HOLD_HEADLINE, result.stdout)
        self.assertIn("exit=2", result.stdout,
                      msg="the walkthrough's validation row carries the "
                          "raw section 7.5 exit code")

        record = self.telemetry_record(sid)
        self.assertEqual(record["outcome"], "held")
        # v0.4.21: attempts[0] is the open-time `opened` attempt
        # (validation null — nothing ran at open); the HOLD is the
        # append that follows it.
        self.assertEqual(len(record["attempts"]), 2)
        self.assertEqual(record["attempts"][0]["outcome"], "opened")
        self.assertIsNone(record["attempts"][0]["validation"])
        attempt = record["attempts"][-1]
        self.assertEqual(attempt["outcome"], "held")
        self.assertEqual(attempt["validation"]["state"], "HOLD")
        self.assertEqual(attempt["validation"]["exit_code"], 2,
                         msg="exit 2 is recorded verbatim — the record "
                             "is where 'script errored' stays "
                             "distinguishable from 'check failed'")

        # The hold is inspectable and recoverable: session open, held
        # commit on the bale branch, origin content untouched.
        self.assertTrue(
            (self.repo / ".bale" / "sessions" / sid / "open").is_file(),
            msg="a HOLD leaves the session open for retry")
        env = git_env(self.home)
        run_checked(["git", "rev-parse", "--verify",
                     f"refs/heads/bale/{sid}"], cwd=self.repo, env=env)
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            "hello\n", msg="nothing merged")


# ---------------------------------------------------------------------------
# Board 71: artifact-borne retry resolution
# ---------------------------------------------------------------------------

# Sentinels (one place per message; the phrases live in bin/bale's
# resolve_retry_session / describe_non_open_session).
SID_MISMATCH_PHRASE = "does not match the tarball"
NOT_OPEN_PHRASE = "does not name an open session"
CLOSED_PHRASE = "closed"
UNKNOWN_PHRASE = "unknown to this repo"
HELD_STAMP = "held_tarball"


class RetryArtifactResolutionTest(unittest.TestCase):
    """`bale retry` resolves from the tarball's responds_to; --sid vets;
    every refusal names its facts and fires before the HOLD discard."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-retryres-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        # A second committed file so two scope-disjoint sessions can be
        # open at once (ADR-0007's pack gate keys on the write forecast).
        (self.repo / "other.txt").write_text("other\n", encoding="utf-8")
        run_checked(["git", "add", "other.txt"], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "second seed file"],
                    cwd=self.repo, env=self.genv)
        self._n = 0

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def packed(self, slug: str, include: str) -> str:
        r = run_bale(self.install,
                     ["pack", f"retry resolution fixture ({slug})",
                      "--slug", slug, "--include", include, "--no-readme"],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        matches = [s for s in self.open_sids() if f"-{slug}-" in s]
        self.assertEqual(len(matches), 1, msg=f"registry: {self.open_sids()}")
        return matches[0]

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return sorted(d.name for d in root.iterdir()
                      if (d / "open").is_file())

    def response(self, sid: str, path: str, *, validation_exit: int,
                 responds_to: str = None) -> Path:
        """A valid response for `sid` modifying `path`; `responds_to`
        overrides the manifest field for the stale/foreign-tarball
        cases (session_id follows it, as a real foreign tarball's
        would)."""
        self._n += 1
        verdict = "FAIL" if validation_exit else "PASS"
        rdir = build_response_dir(
            self.tmp / f"resp-{self._n}", sid,
            summary=f"retry resolution fixture: rewrite {path}",
            entries=[{
                "path": path, "action": "modified",
                "reason": "the goal's rewrite",
                "data": f"rewritten {path} #{self._n}\n".encode("utf-8"),
            }],
            validation_sh=("#!/usr/bin/env bash\n"
                           f"echo \"[{verdict}] fixture check\"\n"
                           f"exit {validation_exit}\n"),
            manifest_extra=(None if responds_to is None else
                            {"responds_to": responds_to,
                             "session_id": responds_to}),
        )
        return tar_response_dir(rdir)

    def hold(self, sid: str, path: str) -> Path:
        tarball = self.response(sid, path, validation_exit=1)
        r = run_bale(self.install, ["apply", str(tarball)],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 1,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        self.assertIn(HOLD_HEADLINE, r.stdout)
        return tarball

    def retry(self, tarball: Path, *extra: str):
        return run_bale(self.install, ["retry", str(tarball), *extra],
                        cwd=self.repo, env=self.env)

    def branch_exists(self, sid: str) -> bool:
        r = subprocess.run(["git", "rev-parse", "--verify", "--quiet",
                            f"refs/heads/bale/{sid}"],
                           cwd=self.repo, env=self.genv, capture_output=True)
        return r.returncode == 0

    def hold_snapshot(self, sid: str) -> dict:
        """The HOLD state a refused retry must leave untouched."""
        sdir = self.repo / ".bale" / "sessions" / sid
        return {
            "branch": subprocess.run(
                ["git", "rev-parse", f"refs/heads/bale/{sid}"],
                cwd=self.repo, env=self.genv, capture_output=True,
                text=True).stdout.strip(),
            "open": (sdir / "open").is_file(),
            "staging_path": ((sdir / "staging_path").read_text()
                             if (sdir / "staging_path").is_file() else None),
            "held_tarball": ((sdir / HELD_STAMP).read_text()
                             if (sdir / HELD_STAMP).is_file() else None),
        }

    def assert_hold_intact(self, sid: str, before: dict) -> None:
        after = self.hold_snapshot(sid)
        self.assertEqual(after, before,
                         msg="a refused retry must leave the HOLD state "
                             "exactly as it was (resolve-before-wipe)")
        self.assertTrue(after["open"])
        self.assertTrue(after["branch"], msg="held branch still exists")
        self.assertTrue(after["staging_path"])
        self.assertTrue(
            Path(after["staging_path"].strip()).is_dir(),
            msg="the preserved staging directory survives the refusal")

    # -- the cases -------------------------------------------------------

    def test_hold_stamps_held_tarball_resolved_path(self) -> None:
        """W2's producer: a HOLD writes .bale/sessions/<sid>/held_tarball
        holding the response tarball's resolved absolute path."""
        sid = self.packed("stamp", "hello.txt")
        tarball = self.hold(sid, "hello.txt")
        stamp = self.repo / ".bale" / "sessions" / sid / HELD_STAMP
        self.assertTrue(stamp.is_file(), msg=f"expected {stamp}")
        self.assertEqual(stamp.read_text(encoding="utf-8"),
                         str(tarball.resolve()) + "\n")

    @slow
    def test_multi_open_resolves_from_tarball_without_sid(self) -> None:
        """Two sessions open, one held: `bale retry <tarball>` with no
        --sid resolves the held session from responds_to and lands
        its PASS; the sibling stays open and untouched. A matching
        --sid is vetted and proceeds identically."""
        sid_a = self.packed("resa", "hello.txt")
        sid_b = self.packed("resb", "other.txt")
        self.hold(sid_a, "hello.txt")
        fixed = self.response(sid_a, "hello.txt", validation_exit=0)

        merged = self.retry(fixed)
        self.assertEqual(merged.returncode, 0,
                         msg=f"stdout:\n{merged.stdout}\n"
                             f"stderr:\n{merged.stderr}")
        self.assertIn(PASS_HEADLINE, merged.stdout)
        self.assertEqual(self.open_sids(), [sid_b],
                         msg="A closed at merge; B untouched and open")
        self.assertEqual(
            (self.repo / "other.txt").read_text(encoding="utf-8"),
            "other\n", msg="the sibling's file is untouched")

        # The vetting arm: --sid agreeing with the tarball proceeds.
        self.hold(sid_b, "other.txt")
        fixed_b = self.response(sid_b, "other.txt", validation_exit=0)
        vetted = self.retry(fixed_b, "--sid", sid_b)
        self.assertEqual(vetted.returncode, 0,
                         msg=f"stdout:\n{vetted.stdout}\n"
                             f"stderr:\n{vetted.stderr}")
        self.assertIn(PASS_HEADLINE, vetted.stdout)
        self.assertEqual(self.open_sids(), [])

    def test_sid_mismatch_refuses_naming_both_and_keeps_hold(self) -> None:
        """--sid naming the OTHER open session refuses, naming both sids
        and the tarball, and the HOLD is exactly as it was."""
        sid_a = self.packed("mma", "hello.txt")
        sid_b = self.packed("mmb", "other.txt")
        self.hold(sid_a, "hello.txt")
        before = self.hold_snapshot(sid_a)
        fixed = self.response(sid_a, "hello.txt", validation_exit=0)

        r = self.retry(fixed, "--sid", sid_b)
        self.assertEqual(r.returncode, 1,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        self.assertIn(SID_MISMATCH_PHRASE, r.stderr)
        for fact in (sid_a, sid_b, fixed.name):
            self.assertIn(fact, r.stderr,
                          msg=f"the refusal names {fact!r}")
        self.assert_hold_intact(sid_a, before)
        self.assertIn(sid_b, self.open_sids())

    def test_closed_and_unknown_responds_to_each_named(self) -> None:
        """responds_to naming no open session refuses; the refusal says
        which it is — closed (with the record's last outcome) or
        unknown to this repo — and leaves the HOLD untouched."""
        sid_a = self.packed("cla", "hello.txt")
        sid_b = self.packed("clb", "other.txt")
        # Close B for real: apply a passing response → merged.
        ok_b = self.response(sid_b, "other.txt", validation_exit=0)
        applied = run_bale(self.install, ["apply", str(ok_b)],
                           cwd=self.repo, env=self.env)
        self.assertEqual(applied.returncode, 0,
                         msg=f"stdout:\n{applied.stdout}\n"
                             f"stderr:\n{applied.stderr}")
        self.hold(sid_a, "hello.txt")
        before = self.hold_snapshot(sid_a)

        with self.subTest(case="closed"):
            stale = self.response(sid_b, "other.txt", validation_exit=0)
            r = self.retry(stale)
            self.assertEqual(r.returncode, 1,
                             msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
            self.assertIn(NOT_OPEN_PHRASE, r.stderr)
            self.assertIn(CLOSED_PHRASE, r.stderr)
            self.assertIn("'applied'", r.stderr,
                          msg="the refusal names the record's last outcome")
            for fact in (sid_b, sid_a, stale.name):
                self.assertIn(fact, r.stderr, msg=f"names {fact!r}")
            self.assert_hold_intact(sid_a, before)

        with self.subTest(case="unknown"):
            bogus = "2026-01-01-never-packed-999"
            foreign = self.response(sid_a, "hello.txt", validation_exit=0,
                                    responds_to=bogus)
            r = self.retry(foreign)
            self.assertEqual(r.returncode, 1,
                             msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
            self.assertIn(NOT_OPEN_PHRASE, r.stderr)
            self.assertIn(UNKNOWN_PHRASE, r.stderr)
            self.assertNotIn(CLOSED_PHRASE, r.stderr)
            for fact in (bogus, sid_a, foreign.name):
                self.assertIn(fact, r.stderr, msg=f"names {fact!r}")
            self.assert_hold_intact(sid_a, before)

    def test_unreadable_tarball_refuses_before_hold_discard(self) -> None:
        """A tarball whose manifest cannot be read refuses loudly, naming
        the file, before any HOLD state is touched."""
        sid = self.packed("unread", "hello.txt")
        self.hold(sid, "hello.txt")
        before = self.hold_snapshot(sid)

        garbage = self.tmp / "not-a-response.tar.gz"
        garbage.write_bytes(b"this is not a gzip tarball\n")
        r = self.retry(garbage)
        self.assertEqual(r.returncode, 1,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        self.assertIn(garbage.name, r.stderr)
        self.assertIn("unreadable", r.stderr)
        self.assert_hold_intact(sid, before)

        # And a well-formed archive with no manifest member.
        import tarfile
        empty = self.tmp / "response-999.tar.gz"
        with tarfile.open(empty, "w:gz") as tf:
            info = tarfile.TarInfo("response-999/README.md")
            info.size = 0
            tf.addfile(info)
        r = self.retry(empty)
        self.assertEqual(r.returncode, 1)
        self.assertIn(empty.name, r.stderr)
        self.assertIn("no response-NNN/manifest.json", r.stderr)
        self.assert_hold_intact(sid, before)


if __name__ == "__main__":
    unittest.main(verbosity=2)
