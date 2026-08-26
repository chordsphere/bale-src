#!/usr/bin/env python3
"""Hermetic E2E for `bale amend-checkpoint` (board 53, v0.4.17).

The operator half of the bad-oracle correction flow (PLANNER.md §5
steps 4–5) as a first-class verb, driven through real pack and amend
runs (ADR-0002 oracle doctrine: observable state, never golden
comparisons). Coverage, per the board-53 ruling ((b)-as-adjusted):

- **Happy path**: pack installs oracle v0 via `--checkpoint-file`;
  amend with v1 and its published hash commits v1's LF bytes at the
  per-sid path as a pathspec-limited `bale: amend ...` commit, and the
  report's LAST line is the paste-ready
  `bale retry ... --accept-checkpoint-change --sid <sid>` successor.
- **CRLF ingest**: a CRLF-mangled amendment commits as its LF twin —
  the published hash is over LF bytes, and the committed oracle is LF.
- **Idempotent re-run**: amending with already-committed bytes makes
  no new commit and still ends with the successor line.
- **The accounting rung**: committed bytes matching neither the
  pack-time stamp nor the amendment refuse loudly naming all three
  hashes; `--accept-unaccounted-oracle` admits the replacement with a
  FORCE line naming the same three.
- **The stamp-less degrade**: a session whose persisted request
  manifest carries no `provenance.checkpoint` proceeds loudly on the
  published-hash deliberateness alone (the §8.5 "verify nothing"
  precedent).
- **Published-hash gates**: a mismatching hash refuses naming both
  hashes and the resolved source path (evidence 45's stale-duplicate
  class); a malformed (short) hash refuses before anything runs.
- **Resolution**: read-only sessions are structurally invisible (bare
  amend refuses naming the waiver; an explicit --sid at one refuses
  too); two scoped sessions refuse naming both and --sid picks.
- **Read + tree refusals**: missing file, empty file, uncommitted
  working-tree edits at the oracle path, and a config with no
  [validation] base or a literal base.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py``; the per-sid fixture base comes from
``tests/test_per_sid_checkpoint.py`` (its stated purpose).

Run directly::

    python3 tests/test_amend_checkpoint.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import unittest
from pathlib import Path

from harness import run_bale, run_checked
from test_per_sid_checkpoint import (
    CP_PATTERN,
    PerSidFixture,
    checkpoint_script,
)

# Sentinels for the surfaces this file pins (one place per message).
REFUSE_UNACCOUNTED_PHRASE = "cannot account for"
ACCEPT_FLAG = "--accept-unaccounted-oracle"
FORCE_UNACCOUNTED_MARKER = f"FORCE: {ACCEPT_FLAG}"
IDEMPOTENT_PHRASE = "idempotent re-run"
DEGRADE_PHRASE = "no pack-time stamp to account"
MISMATCH_PHRASE = "amendment hash mismatch"
MALFORMED_HASH_PHRASE = "64 hex characters"
READONLY_PHRASE = "read-only"
NO_SCOPED_PHRASE = "no scoped session is open"
CLOBBER_PHRASE = "uncommitted working-tree edits"
EMPTY_PHRASE = "is empty"
NO_ORACLE_PHRASE = "no committed blind checkpoint"
UNCONFIGURED_PHRASE = "pins no [validation] base"
LITERAL_BASE_PHRASE = "per-session ({sid} bases) only"
AMEND_SUBJECT_PREFIX = "bale: amend per-session checkpoint for "


def sha256_text_lf(body: str) -> str:
    """The desk's published hash: sha256 over the LF form of `body`."""
    return hashlib.sha256(
        body.replace("\r\n", "\n").encode("utf-8")).hexdigest()


class AmendFixture(PerSidFixture):
    """PerSidFixture plus the amend-specific helpers: an
    outside-the-repo amendment writer, a checkpointed-pack opener, and
    the amend runner."""

    def write_amendment(self, body: str, name: str = "amend-v1.sh") -> Path:
        """Write the desk's amendment OUTSIDE the repo (the
        downloads-directory shape the search-path resolution serves)."""
        p = self.tmp / name
        p.write_bytes(body.encode("utf-8"))
        return p

    def packed_session(self, slug: str, *, marker: str = "v0",
                       include: str = "hello.txt") -> str:
        """Open a checkpoint-configured scoped session via a real pack
        with `--checkpoint-file`, returning its sid. The pack-time
        stamp this records is what the accounting rung reads."""
        self.configure_base(CP_PATTERN)
        source = self.tmp / f"cp-{slug}.sh"
        source.write_text(checkpoint_script(marker), encoding="utf-8")
        r = self.pack(slug, "--include", include,
                      "--checkpoint-file", str(source))
        self.assertEqual(r.returncode, 0,
                         msg=f"fixture pack failed:\nstdout:\n{r.stdout}\n"
                             f"stderr:\n{r.stderr}")
        # Derive the sid from the registry rather than predicting it:
        # the per-day counter is global, so a second same-day pack in
        # the same fixture would break an nnn=1 prediction.
        matches = [s for s in self.open_sids() if f"-{slug}-" in s]
        self.assertEqual(len(matches), 1,
                         msg=f"expected exactly one open session for "
                             f"slug {slug!r}; registry: {self.open_sids()}")
        return matches[0]

    def amend(self, *args: str):
        return run_bale(self.install, ["amend-checkpoint", *args],
                        cwd=self.repo, env=self.env)

    def resolved_for(self, sid: str) -> str:
        return f"claude/checkpoints/{sid}.sh"

    def head_bytes(self, rel: str) -> bytes:
        r = subprocess.run(["git", "show", f"HEAD:{rel}"],
                           cwd=self.repo, capture_output=True)
        self.assertEqual(r.returncode, 0,
                         msg=f"expected {rel} committed at HEAD")
        return r.stdout

    def commit_subjects(self, rel: str) -> list:
        r = subprocess.run(["git", "log", "--format=%s", "--", rel],
                           cwd=self.repo, capture_output=True, text=True)
        return [ln for ln in r.stdout.splitlines() if ln]

    def files_in_head_commit(self) -> list:
        r = subprocess.run(
            ["git", "show", "--name-only", "--format=", "HEAD"],
            cwd=self.repo, capture_output=True, text=True)
        return [ln for ln in r.stdout.splitlines() if ln.strip()]

    def assert_successor_is_last_line(self, stdout: str, sid: str) -> None:
        """The board-53 constraint: the report ENDS with the paste-ready
        retry line — the verb's named successor."""
        lines = [ln.strip() for ln in stdout.splitlines() if ln.strip()]
        self.assertTrue(lines, msg="expected report output")
        last = lines[-1]
        self.assertTrue(last.startswith("bale retry "),
                        msg=f"report must end with the retry successor; "
                            f"last line was: {last!r}")
        self.assertIn("--accept-checkpoint-change", last)
        self.assertIn(f"--sid {sid}", last)


class AmendCheckpointHappyPathTest(AmendFixture):
    """The amendment proper, its idempotent re-run, and CRLF ingest."""

    def test_happy_path_commits_amendment_and_names_successor(self) -> None:
        """v0 committed by pack (stamped); amend with v1 + published
        hash commits v1 at the per-sid path as a pathspec-limited
        `bale: amend ...` commit, and the report's last line is the
        paste-ready retry successor carrying the accept flag."""
        sid = self.packed_session("happy")
        resolved = self.resolved_for(sid)
        v1 = checkpoint_script("v1-amended")
        amendment = self.write_amendment(v1)

        r = self.amend(str(amendment), "--sha256", sha256_text_lf(v1))
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        self.assertEqual(self.head_bytes(resolved),
                         v1.encode("utf-8"),
                         msg="the amendment's LF bytes are the "
                             "committed oracle")
        subjects = self.commit_subjects(resolved)
        self.assertEqual(subjects[0], AMEND_SUBJECT_PREFIX + sid,
                         msg=f"amend commit subject; got {subjects!r}")
        self.assertEqual(self.files_in_head_commit(), [resolved],
                         msg="the amend commit is pathspec-limited to "
                             "the oracle path")
        self.assertIn(sid, self.open_sids(),
                      msg="the session stays open across an amendment")
        self.assert_successor_is_last_line(r.stdout, sid)

    def test_crlf_amendment_commits_as_lf_twin(self) -> None:
        """A CRLF-mangled amendment normalizes at the ingest edge: the
        published LF hash verifies, and the committed oracle is LF."""
        sid = self.packed_session("crlf")
        resolved = self.resolved_for(sid)
        v1_lf = checkpoint_script("v1-crlf")
        v1_crlf = v1_lf.replace("\n", "\r\n")
        amendment = self.write_amendment(v1_crlf, name="amend-crlf.sh")

        r = self.amend(str(amendment), "--sha256", sha256_text_lf(v1_lf))
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        committed = self.head_bytes(resolved)
        self.assertEqual(committed, v1_lf.encode("utf-8"))
        self.assertNotIn(b"\r\n", committed)

    def test_idempotent_rerun_makes_no_new_commit(self) -> None:
        """Amending with already-committed bytes is the idempotent
        re-run: no new commit, exit 0, successor still emitted."""
        sid = self.packed_session("idem")
        resolved = self.resolved_for(sid)
        v1 = checkpoint_script("v1-idem")
        amendment = self.write_amendment(v1)
        published = sha256_text_lf(v1)

        first = self.amend(str(amendment), "--sha256", published)
        self.assertEqual(first.returncode, 0,
                         msg=f"stdout:\n{first.stdout}\n"
                             f"stderr:\n{first.stderr}")
        subjects_after_first = self.commit_subjects(resolved)

        second = self.amend(str(amendment), "--sha256", published)
        self.assertEqual(second.returncode, 0,
                         msg=f"stdout:\n{second.stdout}\n"
                             f"stderr:\n{second.stderr}")
        self.assertIn(IDEMPOTENT_PHRASE, second.stdout + second.stderr)
        self.assertEqual(self.commit_subjects(resolved),
                         subjects_after_first,
                         msg="the idempotent re-run makes no new commit")
        self.assert_successor_is_last_line(second.stdout, sid)


class AmendCheckpointAccountingTest(AmendFixture):
    """The accounting rung: the unaccounted refusal, its per-invocation
    accept, and the stamp-less degrade."""

    def test_unaccounted_committed_bytes_refuse_naming_three_hashes(
            self) -> None:
        """Committed bytes matching neither the pack-time stamp nor the
        amendment refuse loudly, naming all three hashes and the accept
        flag — never a silent replace."""
        sid = self.packed_session("unacct")
        resolved = self.resolved_for(sid)
        # An edit outside the flow: hand-commit different bytes at the
        # oracle path (the prior-amendment / interference shape).
        interposed = checkpoint_script("hand-edit")
        self.commit_files({resolved: interposed}, "hand edit the oracle")
        interposed_sha = sha256_text_lf(interposed)

        v2 = checkpoint_script("v2")
        amendment = self.write_amendment(v2, name="amend-v2.sh")
        v2_sha = sha256_text_lf(v2)

        r = self.amend(str(amendment), "--sha256", v2_sha)
        self.assertNotEqual(r.returncode, 0,
                            msg=f"stdout:\n{r.stdout}\n"
                                f"stderr:\n{r.stderr}")
        combined = r.stdout + r.stderr
        self.assertIn(REFUSE_UNACCOUNTED_PHRASE, combined)
        self.assertIn(ACCEPT_FLAG, combined,
                      msg="the refusal names its per-invocation "
                          "successor flag")
        for sha in (interposed_sha[:12], v2_sha[:12]):
            self.assertIn(sha, combined,
                          msg=f"the refusal names hash {sha}")
        self.assertEqual(self.head_bytes(resolved),
                         interposed.encode("utf-8"),
                         msg="a refusal commits nothing")

    def test_accept_unaccounted_oracle_admits_with_force_line(self) -> None:
        """--accept-unaccounted-oracle admits the replacement: FORCE
        line naming committed, stamped, and delivered hashes; the
        amendment lands; the successor is emitted."""
        sid = self.packed_session("acct2")
        resolved = self.resolved_for(sid)
        stamped_sha = sha256_text_lf(
            (self.repo / resolved).read_text(encoding="utf-8"))
        interposed = checkpoint_script("prior-amendment")
        self.commit_files({resolved: interposed}, "prior amendment")

        v2 = checkpoint_script("v2-accepted")
        amendment = self.write_amendment(v2, name="amend-v2b.sh")
        v2_sha = sha256_text_lf(v2)

        r = self.amend(str(amendment), "--sha256", v2_sha,
                       ACCEPT_FLAG)
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        combined = r.stdout + r.stderr
        self.assertIn(FORCE_UNACCOUNTED_MARKER, combined)
        for sha in (sha256_text_lf(interposed)[:12], stamped_sha[:12],
                    v2_sha[:12]):
            self.assertIn(sha, combined,
                          msg=f"the FORCE line names hash {sha}")
        self.assertEqual(self.head_bytes(resolved), v2.encode("utf-8"))
        self.assert_successor_is_last_line(r.stdout, sid)

    def test_stampless_session_degrades_loudly_and_commits(self) -> None:
        """No provenance.checkpoint in the persisted request manifest
        (hand-rolled / pre-0.3.28 shape): the accounting rung degrades
        loudly and the amendment proceeds on the published-hash
        deliberateness alone."""
        sid = self.packed_session("nostamp")
        resolved = self.resolved_for(sid)
        mpath = self.repo / ".bale" / "sessions" / sid / "manifest.json"
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
        manifest.get("provenance", {}).pop("checkpoint", None)
        mpath.write_text(json.dumps(manifest), encoding="utf-8")

        v1 = checkpoint_script("v1-nostamp")
        amendment = self.write_amendment(v1, name="amend-ns.sh")
        r = self.amend(str(amendment), "--sha256", sha256_text_lf(v1))
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        self.assertIn(DEGRADE_PHRASE, r.stdout + r.stderr,
                      msg="the degrade is loud, never silent")
        self.assertEqual(self.head_bytes(resolved), v1.encode("utf-8"))


class AmendCheckpointHashGateTest(AmendFixture):
    """The mandatory published-hash comparison and its shape gate."""

    def test_hash_mismatch_refuses_naming_both_and_source(self) -> None:
        sid = self.packed_session("mismatch")
        resolved = self.resolved_for(sid)
        before = self.head_bytes(resolved)
        v1 = checkpoint_script("v1-mm")
        amendment = self.write_amendment(v1, name="amend-mm.sh")
        wrong = sha256_text_lf("something else entirely\n")

        r = self.amend(str(amendment), "--sha256", wrong)
        self.assertNotEqual(r.returncode, 0)
        combined = r.stdout + r.stderr
        self.assertIn(MISMATCH_PHRASE, combined)
        self.assertIn(sha256_text_lf(v1), combined,
                      msg="the refusal names the delivered hash")
        self.assertIn(wrong, combined,
                      msg="the refusal names the published hash")
        self.assertIn(str(amendment), combined,
                      msg="the refusal names the resolved source path "
                          "(the stale-duplicate catch)")
        self.assertEqual(self.head_bytes(resolved), before,
                         msg="a refusal commits nothing")

    def test_malformed_hash_refuses_before_anything_runs(self) -> None:
        sid = self.packed_session("shorthash")
        amendment = self.write_amendment(checkpoint_script("x"),
                                         name="amend-sh.sh")
        r = self.amend(str(amendment), "--sha256", "abc123")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(MALFORMED_HASH_PHRASE, r.stdout + r.stderr)
        # sid remains untouched-open; the shape gate is pure.
        self.assertIn(sid, self.open_sids())


class AmendCheckpointResolutionTest(AmendFixture):
    """Session resolution: read-only invisibility and the two-scoped
    refusal, per the board-51 posture."""

    def test_readonly_sessions_are_structurally_invisible(self) -> None:
        """With only a read-only session open, a bare amend refuses
        naming the waiver; an explicit --sid at it refuses too."""
        self.configure_base(CP_PATTERN)
        r = self.pack("romaster", "--read-only", "--include", "hello.txt")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        ro_sid = self.open_sids()[0]
        amendment = self.write_amendment(checkpoint_script("ro"),
                                         name="amend-ro.sh")
        good_hash = sha256_text_lf(checkpoint_script("ro"))

        bare = self.amend(str(amendment), "--sha256", good_hash)
        self.assertNotEqual(bare.returncode, 0)
        self.assertIn(NO_SCOPED_PHRASE, bare.stdout + bare.stderr)
        self.assertIn(READONLY_PHRASE, bare.stdout + bare.stderr)

        explicit = self.amend(str(amendment), "--sha256", good_hash,
                              "--sid", ro_sid)
        self.assertNotEqual(explicit.returncode, 0)
        self.assertIn(READONLY_PHRASE, explicit.stdout + explicit.stderr)

    def test_two_scoped_sessions_refuse_named_and_sid_picks(self) -> None:
        """Two scoped opens: bare amend refuses naming both candidates
        (never guesses); --sid picks one and amends only its oracle."""
        (self.repo / "other.txt").write_text("other\n", encoding="utf-8")
        run_checked(["git", "add", "other.txt"],
                    cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "second seed file"],
                    cwd=self.repo, env=self.genv)
        sid_a = self.packed_session("twoa", include="hello.txt")
        sid_b = self.packed_session("twob", include="other.txt")
        resolved_b = self.resolved_for(sid_b)
        untouched_a = self.head_bytes(self.resolved_for(sid_a))

        v1 = checkpoint_script("v1-two")
        amendment = self.write_amendment(v1, name="amend-two.sh")
        published = sha256_text_lf(v1)

        bare = self.amend(str(amendment), "--sha256", published)
        self.assertNotEqual(bare.returncode, 0)
        combined = bare.stdout + bare.stderr
        for sid in (sid_a, sid_b):
            self.assertIn(sid, combined,
                          msg=f"the refusal names candidate {sid}")

        picked = self.amend(str(amendment), "--sha256", published,
                            "--sid", sid_b)
        self.assertEqual(picked.returncode, 0,
                         msg=f"stdout:\n{picked.stdout}\n"
                             f"stderr:\n{picked.stderr}")
        self.assertEqual(self.head_bytes(resolved_b), v1.encode("utf-8"))
        self.assertEqual(self.head_bytes(self.resolved_for(sid_a)),
                         untouched_a,
                         msg="--sid amends exactly the named session's "
                             "oracle")
        self.assert_successor_is_last_line(picked.stdout, sid_b)


class AmendCheckpointReadAndTreeTest(AmendFixture):
    """Read refusals, the working-tree rung, and the config gate."""

    def test_missing_and_empty_files_refuse(self) -> None:
        sid = self.packed_session("readgate")
        resolved = self.resolved_for(sid)
        before = self.head_bytes(resolved)
        some_hash = "0" * 64

        missing = self.amend("no-such-amendment.sh",
                             "--sha256", some_hash)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn("not found", missing.stdout + missing.stderr)

        empty = self.write_amendment("", name="amend-empty.sh")
        r = self.amend(str(empty), "--sha256", some_hash)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(EMPTY_PHRASE, r.stdout + r.stderr)
        self.assertEqual(self.head_bytes(resolved), before)

    def test_uncommitted_working_tree_edits_refuse(self) -> None:
        """Uncommitted bytes at the oracle path matching neither HEAD
        nor the amendment refuse — never clobbered."""
        sid = self.packed_session("clobber")
        resolved = self.resolved_for(sid)
        local = "# local uncommitted work\nexit 3\n"
        (self.repo / resolved).write_text(local, encoding="utf-8")

        v1 = checkpoint_script("v1-clobber")
        amendment = self.write_amendment(v1, name="amend-cl.sh")
        r = self.amend(str(amendment), "--sha256", sha256_text_lf(v1))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(CLOBBER_PHRASE, r.stdout + r.stderr)
        self.assertEqual((self.repo / resolved).read_text(encoding="utf-8"),
                         local, msg="the local edits are preserved")

    def test_dangling_oracle_refuses(self) -> None:
        """A session whose committed oracle was removed has nothing to
        amend; the refusal names the state."""
        sid = self.packed_session("dangling")
        resolved = self.resolved_for(sid)
        run_checked(["git", "rm", "-q", resolved],
                    cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "remove the oracle"],
                    cwd=self.repo, env=self.genv)
        v1 = checkpoint_script("v1-d")
        amendment = self.write_amendment(v1, name="amend-d.sh")
        r = self.amend(str(amendment), "--sha256", sha256_text_lf(v1))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(NO_ORACLE_PHRASE, r.stdout + r.stderr)

    def test_unconfigured_and_literal_bases_refuse(self) -> None:
        """No [validation] base refuses (no oracle to revise); a
        literal base refuses naming the direct-commit remedy. Both fire
        before session resolution, so no session state is needed."""
        amendment = self.write_amendment(checkpoint_script("cfg"),
                                         name="amend-cfg.sh")
        some_hash = "0" * 64

        unconfigured = self.amend(str(amendment), "--sha256", some_hash)
        self.assertNotEqual(unconfigured.returncode, 0)
        self.assertIn(UNCONFIGURED_PHRASE,
                      unconfigured.stdout + unconfigured.stderr)

        self.configure_base("claude/checkpoint.sh")
        literal = self.amend(str(amendment), "--sha256", some_hash)
        self.assertNotEqual(literal.returncode, 0)
        self.assertIn(LITERAL_BASE_PHRASE,
                      literal.stdout + literal.stderr)


if __name__ == "__main__":
    unittest.main()
