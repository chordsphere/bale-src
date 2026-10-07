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

Board 47a (v0.4.34) added ``HoldCardE2ETest``: the closing [HOLD]
card driven through real checkpoint-configured applies — the judge
line in each of its three cases, the failed probe labels (none / one /
several, log order) on the card and in the telemetry stamp's
``failed_probes``, both successor forks composed from the HOLD-time
stamp with a path that needs shell quoting, the failed-stamp
degradation, the literal-base note, and the unconfigured HOLD's
absent row and field. The renderer's pure pieces are pinned
unit-shaped in tests/test_apply_preflight.py (``HoldCardUnitTest``).

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
    numbered_sibling,
    run_bale,
    run_checked,
    slow,
    tar_response_dir,
)
import os
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

    # -- v0.4.51: a missing numbered name resolves to the newest sibling ----

    RESOLVED_PHRASE = "is not there; resolved"

    def junk(self, directory: Path, name: str, mtime_ns: int) -> Path:
        """A sibling-named file that is not a tarball: the resolution
        reads names and stats only, and the later gate (the manifest
        peek) refuses it naming the file — which is how a test sees
        which file the resolution handed on."""
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        path.write_bytes(b"not a gzip tarball\n")
        os.utime(path, ns=(mtime_ns, mtime_ns))
        return path

    def test_missing_numbered_name_resolves_newest_sibling(self) -> None:
        sid = self.packed("sibnewest", "hello.txt")
        downloads = self.tmp / "Down loads"
        t = 1_700_000_000_000_000_000
        older = self.junk(downloads, f"response-{sid}.tar.gz", t)
        newer = self.junk(downloads, f"response-{sid} (1).tar.gz",
                          t + 1_000)
        asked = downloads / f"response-{sid} (2).tar.gz"
        r = self.retry(asked)
        self.assertEqual(r.returncode, 1,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        self.assertIn(f"[bale] retry: {asked} is not there; resolved "
                      f"{newer} (newest sibling by mtime in {downloads})",
                      r.stdout)
        self.assertIn(newer.name, r.stderr,
                      msg="the later gate names the resolved file")
        self.assertIn("unreadable", r.stderr)
        self.assertNotIn(f"{older}", r.stderr)
        self.assertNotIn("tarball not found", r.stderr)

    def test_missing_plain_name_resolves_too(self) -> None:
        """The plain `response-<sid>.tar.gz` is a numbered name with
        counter zero: missing, it resolves the same way."""
        sid = self.packed("sibplain", "hello.txt")
        downloads = self.tmp / "dl"
        only = self.junk(downloads, f"response-{sid} (3).tar.gz", 10**18)
        r = self.retry(downloads / f"response-{sid}.tar.gz")
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertIn(self.RESOLVED_PHRASE, r.stdout)
        self.assertIn(only.name, r.stderr)

    def test_mtime_tie_refuses_naming_both(self) -> None:
        sid = self.packed("sibtie", "hello.txt")
        downloads = self.tmp / "tie dir"
        t = 1_700_000_000_000_000_000
        a = self.junk(downloads, f"response-{sid}.tar.gz", t)
        b = self.junk(downloads, f"response-{sid} (1).tar.gz", t)
        self.junk(downloads, f"response-{sid} (2).tar.gz", t - 5)
        r = self.retry(downloads / f"response-{sid} (3).tar.gz")
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertIn("share one modification time", r.stderr)
        for tied in (a, b):
            self.assertIn(f"bale retry {shlex.quote(str(tied))}", r.stderr)
        self.assertNotIn("(2).tar.gz", r.stderr,
                         msg="only the tied newest are named")
        self.assertNotIn(self.RESOLVED_PHRASE, r.stdout)
        self.assertNotIn("unreadable", r.stderr,
                         msg="a tie refuses before any later gate")

    def test_no_sibling_keeps_the_not_found_refusal(self) -> None:
        sid = self.packed("sibnone", "hello.txt")
        downloads = self.tmp / "empty dl"
        downloads.mkdir()
        asked = downloads / f"response-{sid} (1).tar.gz"
        r = self.retry(asked)
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertIn(f"[bale] error: tarball not found: {asked}", r.stderr)
        self.assertNotIn(self.RESOLVED_PHRASE, r.stdout)

    def test_existing_path_is_used_as_given(self) -> None:
        """Resolution never replaces a file the operator named and has,
        even when a newer sibling sits beside it."""
        sid = self.packed("sibexists", "hello.txt")
        downloads = self.tmp / "given"
        t = 1_700_000_000_000_000_000
        given = self.junk(downloads, f"response-{sid}.tar.gz", t)
        self.junk(downloads, f"response-{sid} (1).tar.gz", t + 10**9)
        r = self.retry(given)
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertNotIn(self.RESOLVED_PHRASE, r.stdout)
        self.assertIn(given.name, r.stderr)
        self.assertNotIn("(1).tar.gz", r.stderr)

    def test_other_names_and_other_directories_are_not_resolved(
            self) -> None:
        """Only `response-<sid>[ (N)].tar.gz` engages, and only in the
        named directory: a sibling elsewhere — cwd included — is never
        found."""
        sid = self.packed("sibscope", "hello.txt")
        here = self.tmp / "here"
        self.junk(here, "notes (1).tar.gz", 10**18)
        r = self.retry(here / "notes (2).tar.gz")
        self.assertIn("tarball not found", r.stderr, msg=r.stdout)
        self.assertNotIn(self.RESOLVED_PHRASE, r.stdout)
        self.junk(self.repo, f"response-{sid}.tar.gz", 10**18)
        try:
            r = self.retry(here / f"response-{sid} (1).tar.gz")
            self.assertIn("tarball not found", r.stderr, msg=r.stdout)
            self.assertNotIn(self.RESOLVED_PHRASE, r.stdout)
        finally:
            (self.repo / f"response-{sid}.tar.gz").unlink()

    def test_json_mode_routes_the_resolution_line_to_stderr(self) -> None:
        sid = self.packed("sibjson", "hello.txt")
        downloads = self.tmp / "json dl"
        self.junk(downloads, f"response-{sid}.tar.gz", 10**18)
        r = run_bale(self.install,
                     ["retry", str(downloads / f"response-{sid} (1).tar.gz"),
                      "--json"], cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertNotIn(self.RESOLVED_PHRASE, r.stdout)
        self.assertIn(self.RESOLVED_PHRASE, r.stderr)

    def test_held_work_line_lands_the_twin_the_browser_saved(self) -> None:
        """The loop the feature exists for: the HOLD card's work-fork
        line names `(1)`; the corrected tarball arrives there (the
        browser's twin of the held name); pasting the line exactly as
        the card printed it lands the retry."""
        sid = self.packed("sibloop", "hello.txt")
        held = self.response(sid, "hello.txt", validation_exit=1)
        r = run_bale(self.install, ["apply", str(held)],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        card = r.stdout[r.stdout.rindex("  [HOLD] "):]
        (work,) = [ln.strip() for ln in card.splitlines()
                   if ln.strip().startswith("bale retry ")
                   and " --" not in ln]
        twin = numbered_sibling(held.resolve())
        self.assertEqual(work, f"bale retry {shlex.quote(str(twin))}")
        self.response(sid, "hello.txt", validation_exit=0).rename(twin)
        landed = run_bale(self.install, shlex.split(work)[1:],
                          cwd=self.repo, env=self.env)
        self.assertEqual(landed.returncode, 0,
                         msg=f"stdout:\n{landed.stdout}\n"
                             f"stderr:\n{landed.stderr}")
        self.assertIn(PASS_HEADLINE, landed.stdout)
        self.assertNotIn(self.RESOLVED_PHRASE, landed.stdout,
                         msg="the twin exists: used as given")


# ---------------------------------------------------------------------------
# Board 47a (v0.4.34): the HOLD card — judge line, failed probe labels,
# ruling-forked composed successors — and the labels on telemetry
# ---------------------------------------------------------------------------

from test_per_sid_checkpoint import CP_PATTERN, PerSidFixture  # noqa: E402
import shlex  # noqa: E402

LITERAL_BASE = "claude/checkpoint.sh"


def probe_checkpoint(verdicts: list, exit_code: int) -> str:
    """A blind checkpoint printing `verdicts` ([(VERDICT, label), ...])
    in order and exiting `exit_code` (TARBALL.md §7.2/§7.5)."""
    body = "".join(f'echo "[{v}] {label}"\n' for v, label in verdicts)
    return f"#!/usr/bin/env bash\n{body}exit {exit_code}\n"


class HoldCardE2ETest(PerSidFixture):
    """The desk's specimen, driven for real: a checkpoint-configured
    session HOLDs through a real apply, and the closing card and the
    telemetry attempt are asserted as observable output (ADR-0002).

    The response tarball lands in a directory whose name holds a space,
    so every composed successor exercises shlex quoting and is proven
    pasteable by round-tripping through shlex.split. The three judge
    cases each get a real HOLD; the unconfigured HOLD, the no-stamp
    degradation, and the literal-base note ride the same fixture.
    """

    def open_checkpointed(self, slug: str, script: str, *,
                          base: str = CP_PATTERN) -> str:
        self.configure_base(base)
        if base == CP_PATTERN:
            source = self.tmp / f"cp-{slug}.sh"
            source.write_text(script, encoding="utf-8")
            r = self.pack(slug, "--include", "hello.txt",
                          "--checkpoint-file", str(source))
        else:
            self.commit_files({base: script, "bale.toml":
                               (self.repo / "bale.toml").read_text()},
                              "commit the literal-base checkpoint")
            r = self.pack(slug, "--include", "hello.txt")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        matches = [s for s in self.open_sids() if f"-{slug}-" in s]
        self.assertEqual(len(matches), 1, msg=f"{self.open_sids()}")
        return matches[0]

    def hold(self, sid: str, *, worker_exit: int, extra: dict = None):
        verdict = "FAIL" if worker_exit else "PASS"
        rdir = build_response_dir(
            self.tmp / "held dir", sid,
            summary="oracle",
            entries=[{"path": "hello.txt", "action": "modified",
                      "reason": "the specimen's rewrite",
                      "data": b"specimen rewrite\n"}],
            validation_sh=("#!/usr/bin/env bash\n"
                           f"echo \"[{verdict}] fixture check\"\n"
                           f"exit {worker_exit}\n"),
            manifest_extra=extra)
        tarball = tar_response_dir(rdir)
        r = run_bale(self.install, ["apply", str(tarball)],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 1,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        return tarball, r

    def card(self, stdout: str) -> list:
        """The closing card's lines: everything after its [HOLD] headline
        (the LAST headline — the walkthrough summary prints one too)."""
        lines = stdout.splitlines()
        starts = [i for i, ln in enumerate(lines)
                  if ln.startswith("  [HOLD] ")]
        self.assertTrue(starts, msg=stdout)
        return [ln.strip() for ln in lines[starts[-1]:]]

    def row(self, card: list, label: str) -> str:
        hits = [ln for ln in card if ln.startswith(f"{label}:")]
        self.assertEqual(len(hits), 1, msg=f"row {label!r} in {card}")
        return hits[0][len(label) + 1:].strip()

    def attempt(self, sid: str) -> dict:
        p = self.repo / "claude" / "telemetry" / f"{sid}.json"
        return json.loads(p.read_text(encoding="utf-8"))["attempts"][-1]

    def commands(self, card: list, verb: str) -> list:
        return [ln for ln in card if ln.startswith(f"bale {verb} ")]

    # -- the three judge cases ------------------------------------------

    def test_checkpoint_held_specimen(self) -> None:
        sid = self.open_checkpointed("specimen", probe_checkpoint(
            [("FAIL", "oracle-probe-alpha"), ("PASS", "oracle-probe-beta")],
            1))
        tarball, r = self.hold(sid, worker_exit=0,
                               extra={"corrects": "2026-09-01-prior-001",
                                      "validation_will_run":
                                          ["fixture check"]})
        card = self.card(r.stdout)
        self.assertEqual(self.row(card, "judge"),
                         "blind checkpoint — checkpoint: HOLD (exit 1) · "
                         "worker validation: PASS")
        self.assertEqual(self.row(card, "failed probes"),
                         "oracle-probe-alpha")
        self.assertNotIn("validation: exited 0", r.stdout)
        self.assertNotIn("<new-tarball>", r.stdout)

        # v0.4.51: every fork names the held tarball's next numbered
        # sibling — `(1)`, the held directory holding no twin yet.
        named = str(numbered_sibling(tarball.resolve()))
        amend = self.commands(card, "amend-checkpoint")
        self.assertEqual(len(amend), 1, msg=card)
        self.assertIn(f"--sid {sid}", amend[0])
        retries = self.commands(card, "retry")
        self.assertEqual(retries, [
            f"bale retry {shlex.quote(named)} --accept-checkpoint-change "
            f"--sid {sid}",
            f"bale retry {shlex.quote(named)}",
            f"bale retry {shlex.quote(named)} --sid {sid}",
        ])
        for line in retries:
            self.assertEqual(shlex.split(line)[2], named,
                             msg="pasteable: the quoted path round-trips")

        attempt = self.attempt(sid)
        self.assertEqual(attempt["checkpoint"]["failed_probes"],
                         ["oracle-probe-alpha"])
        self.assertEqual(attempt["validation"]["validation_will_run"],
                         ["fixture check"])
        self.assertEqual(attempt["corrects"], "2026-09-01-prior-001")

    def test_worker_held_renders_work_fork_only(self) -> None:
        sid = self.open_checkpointed("workerheld", probe_checkpoint(
            [("PASS", "oracle-probe-beta")], 0))
        tarball, r = self.hold(sid, worker_exit=1)
        card = self.card(r.stdout)
        self.assertEqual(self.row(card, "judge"),
                         "worker validation — worker validation: HOLD "
                         "(exit 1) · checkpoint: PASS")
        self.assertEqual(self.row(card, "failed probes"), "none")
        self.assertEqual(self.commands(card, "amend-checkpoint"), [])
        quoted = shlex.quote(str(numbered_sibling(tarball.resolve())))
        self.assertEqual(self.commands(card, "retry"),
                         [f"bale retry {quoted}",
                          f"bale retry {quoted} --sid {sid}"])
        self.assertEqual(self.attempt(sid)["checkpoint"]["failed_probes"],
                         [])

    def test_both_held_renders_both_forks_labels_in_log_order(self) -> None:
        sid = self.open_checkpointed("bothheld", probe_checkpoint(
            [("FAIL", "zeta-probe"), ("PASS", "beta-probe"),
             ("FAIL", "alpha-probe")], 1))
        _, r = self.hold(sid, worker_exit=1)
        card = self.card(r.stdout)
        self.assertEqual(self.row(card, "judge"),
                         "both — checkpoint: HOLD (exit 1) · worker "
                         "validation: HOLD (exit 1)")
        self.assertEqual(self.row(card, "failed probes"),
                         "zeta-probe · alpha-probe")
        self.assertEqual(len(self.commands(card, "amend-checkpoint")), 1)
        self.assertEqual(len(self.commands(card, "retry")), 3)
        self.assertEqual(self.attempt(sid)["checkpoint"]["failed_probes"],
                         ["zeta-probe", "alpha-probe"],
                         msg="log order, never sorted")

    # -- no checkpoint, no stamp, literal base ---------------------------

    def test_unconfigured_hold_has_no_probe_row_or_field(self) -> None:
        r = self.pack("nocp", "--include", "hello.txt")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        sid = self.open_sids()[0]
        _, held = self.hold(sid, worker_exit=1)
        card = self.card(held.stdout)
        self.assertEqual(self.row(card, "judge"),
                         "worker validation — worker validation: HOLD "
                         "(exit 1) · no blind checkpoint configured")
        self.assertFalse([ln for ln in card
                          if ln.startswith("failed probes:")])
        self.assertEqual(self.attempt(sid)["checkpoint"],
                         {"configured": False},
                         msg="failed_probes absent when no checkpoint ran")

    def test_failed_stamp_write_degrades_the_card_loudly(self) -> None:
        sid = self.open_checkpointed("nostamp", probe_checkpoint(
            [("FAIL", "oracle-probe-alpha")], 1))
        # A directory where the stamp file goes makes the write fail —
        # the loud-never-fatal branch, reached without mocking.
        (self.repo / ".bale" / "sessions" / sid / "held_tarball").mkdir()
        _, r = self.hold(sid, worker_exit=0)
        card = self.card(r.stdout)
        notes = [ln for ln in card if "could not be filled in" in ln]
        self.assertEqual(len(notes), 3, msg=card)
        self.assertIn("could not be written", notes[0])
        self.assertEqual(self.commands(card, "retry"), [
            f"bale retry <response-tarball> --accept-checkpoint-change "
            f"--sid {sid}",
            "bale retry <response-tarball>",
            f"bale retry <response-tarball> --sid {sid}",
        ])
        self.assertIn("FORCE: could not write the HOLD-time tarball stamp",
                      r.stdout + r.stderr)

    def test_literal_base_notes_the_direct_commit(self) -> None:
        sid = self.open_checkpointed("literal", probe_checkpoint(
            [("FAIL", "oracle-probe-alpha")], 1), base=LITERAL_BASE)
        tarball, r = self.hold(sid, worker_exit=0)
        card = self.card(r.stdout)
        self.assertEqual(self.commands(card, "amend-checkpoint"), [])
        notes = [ln for ln in card if "literal [validation] base" in ln]
        self.assertEqual(len(notes), 1, msg=card)
        self.assertIn(LITERAL_BASE, notes[0])
        self.assertIn(
            f"bale retry {shlex.quote(str(numbered_sibling(tarball.resolve())))} "
            f"--accept-checkpoint-change --sid {sid}",
            self.commands(card, "retry"))


class RelayBlocksE2ETest(HoldCardE2ETest):
    """Board 47b, driven for real: a HOLD prints the addressed relay
    blocks before the card, the worker block carries the failed labels
    and nothing else of the checkpoint's output, the planner block
    inlines exactly this attempt's log bands (a retry's block does not
    re-carry the first attempt's), and a clean apply prints the
    ratification relay with notes.md verbatim and no worker block.
    """

    # The checkpoint's passing probe label: in the log, in the planner
    # block, never in the worker block.
    PASSING_LABEL = "oracle-mechanics-beta"

    def block(self, stdout: str, sid: str, addressee: str) -> str:
        begin = f"=== RELAY BEGIN {sid} to {addressee} ==="
        end = f"=== RELAY END {sid} to {addressee} ==="
        lines = stdout.splitlines()
        self.assertEqual(lines.count(begin), 1, msg=stdout)
        self.assertEqual(lines.count(end), 1, msg=stdout)
        i, j = lines.index(begin), lines.index(end)
        self.assertLess(i, j)
        return "\n".join(lines[i:j + 1])

    def checkpoint_held(self, slug: str):
        sid = self.open_checkpointed(slug, probe_checkpoint(
            [("FAIL", "oracle-probe-alpha"), ("PASS", self.PASSING_LABEL)],
            1))
        return sid

    def test_hold_blocks_addressed_and_spec_safe(self) -> None:
        sid = self.checkpoint_held("relayhold")
        tarball, r = self.hold(sid, worker_exit=1)
        planner = self.block(r.stdout, sid, "planner")
        worker = self.block(r.stdout, sid, "worker")

        self.assertIn("failed probes: oracle-probe-alpha", worker)
        self.assertIn("[FAIL] fixture check", worker,
                      msg="the worker's own output rides")
        self.assertNotIn(self.PASSING_LABEL, worker)
        self.assertNotIn("=== blind checkpoint", worker)
        self.assertNotIn("blind checkpoint exit code", worker)
        self.assertNotIn(".bale/logs", worker)
        self.assertIn(
            f"bale retry '{numbered_sibling(tarball.resolve())}'", worker,
            msg="v0.4.51: the worker's closing line names the (1) twin")

        self.assertIn(self.PASSING_LABEL, planner,
                      msg="the checkpoint band is inlined for the desk")
        self.assertIn("=== worker validation.sh ===", planner)
        self.assertIn("exit codes: checkpoint 1 · worker validation.sh 1",
                      planner)
        self.assertIn(f"held tarball: {tarball.resolve()}", planner)

        out = r.stdout
        self.assertLess(out.index(f"=== RELAY BEGIN {sid} to planner ==="),
                        out.index(f"=== RELAY BEGIN {sid} to worker ==="),
                        msg="send order: planner first on a checkpoint hold")
        card = self.card(out)
        self.assertLess(out.rindex("=== RELAY END"),
                        out.rindex(f"  [HOLD] {sid}"),
                        msg="the blocks print before the card")
        self.assertIn("send first: planner — the checkpoint held; the "
                      "worker block waits for the planner's ruling", card)
        heads = [ln for ln in card if ln.startswith("base defect")]
        self.assertEqual(len(heads), 1, msg=card)

    def test_worker_only_hold_sends_worker_first(self) -> None:
        sid = self.open_checkpointed("relayworker", probe_checkpoint(
            [("PASS", self.PASSING_LABEL)], 0))
        _, r = self.hold(sid, worker_exit=1)
        worker = self.block(r.stdout, sid, "worker")
        self.assertNotIn(self.PASSING_LABEL, worker,
                         msg="a passing checkpoint's output stays out too")
        self.assertIn("failed probes: none", worker)
        self.assertLess(r.stdout.index(f"=== RELAY BEGIN {sid} to worker"),
                        r.stdout.index(f"=== RELAY BEGIN {sid} to planner"))
        self.assertTrue([ln for ln in self.card(r.stdout)
                         if ln.startswith("send first: worker — ")],
                        msg=r.stdout)

    def test_retry_block_carries_only_this_attempts_bands(self) -> None:
        sid = self.checkpoint_held("relayretry")
        self.hold(sid, worker_exit=0)
        rdir = build_response_dir(
            self.tmp / "second", sid, summary="second",
            entries=[{"path": "hello.txt", "action": "modified",
                      "reason": "the second attempt",
                      "data": b"second attempt\n"}],
            validation_sh=("#!/usr/bin/env bash\n"
                           "echo \"[PASS] second attempt check\"\nexit 0\n"))
        r = run_bale(self.install, ["retry", str(tar_response_dir(rdir))],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        planner = self.block(r.stdout, sid, "planner")
        self.assertEqual(planner.count("=== blind checkpoint ("), 1)
        self.assertIn("second attempt check", planner)
        self.assertNotIn("[PASS] fixture check", planner,
                         msg="the first attempt's worker band is not "
                             "re-carried")
        log = (self.repo / ".bale" / "logs" / f"{sid}.log").read_text()
        self.assertEqual(log.count("=== blind checkpoint ("), 2,
                         msg="the log itself holds both attempts")

    def test_clean_apply_prints_the_ratification_relay(self) -> None:
        sid = self.open_checkpointed("relaypass", probe_checkpoint(
            [("PASS", self.PASSING_LABEL)], 0))
        rdir = build_response_dir(
            self.tmp / "pass dir", sid, summary="clean",
            entries=[{"path": "hello.txt", "action": "modified",
                      "reason": "a clean rewrite", "data": b"clean\n"}],
            validation_sh=("#!/usr/bin/env bash\n"
                           "echo \"[PASS] fixture check\"\nexit 0\n"))
        (rdir / "notes.md").write_text("# Notes\n\nRatify the thing.\n",
                                       encoding="utf-8")
        r = run_bale(self.install, ["apply", str(tar_response_dir(rdir)),
                                    "--no-interact"],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        planner = self.block(r.stdout, sid, "planner")
        self.assertNotIn(f"to worker ===", r.stdout)
        self.assertIn("--- notes.md ---\n# Notes\n\nRatify the thing.\n"
                      "--- end notes.md ---", planner)
        self.assertIn("verdict: checkpoint: PASS · worker validation: PASS",
                      planner)
        self.assertIn("admissions: none", planner)
        self.assertNotIn(self.PASSING_LABEL, planner,
                         msg="a clean apply relays notes and verdict, "
                             "not log bands")
        self.assertLess(r.stdout.index(f"=== RELAY END {sid} to planner"),
                        r.stdout.rindex(f"[PASS] {sid}"))

    def test_json_mode_keeps_stdout_one_line(self) -> None:
        sid = self.checkpoint_held("relayjson")
        rdir = build_response_dir(
            self.tmp / "json dir", sid, summary="json",
            entries=[{"path": "hello.txt", "action": "modified",
                      "reason": "json", "data": b"json\n"}],
            validation_sh="#!/usr/bin/env bash\necho \"[PASS] x\"\nexit 0\n")
        r = run_bale(self.install, ["apply", str(tar_response_dir(rdir)),
                                    "--json"],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertEqual(len(r.stdout.splitlines()), 1, msg=r.stdout)
        json.loads(r.stdout)
        self.assertIn(f"=== RELAY BEGIN {sid} to worker ===", r.stderr)


if __name__ == "__main__":
    unittest.main(verbosity=2)
