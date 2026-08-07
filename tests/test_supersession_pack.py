"""Split supersession (`bale pack --supersedes`, v0.3.17, board 26).

Pins the flow end to end through real pack runs in the hermetic
sandbox (ADR-0005 doctrine, via tests/harness.py):

- piped decline: the exchange's decline default applies without a
  prompt; nothing closes; the disjointness gate refuses naming the
  declined supersession and the unlock remedy
- pty accept: the parent closes with a superseded-by-split closure
  record (command "pack"), the child pack clears the gate, and the
  child's stamped manifest carries depends_on.superseded_session
- a sid that is neither open nor closed superseded-by-split refuses
- idempotent re-run: a parent already closed superseded-by-split is
  accepted with a logged note and the lineage still stamps
- the gate still refuses against a second, unrelated open session
  even when the supersession was accepted — and the aborted child is
  then repairable via the idempotent re-run
- a normal pack stamps depends_on.superseded_session null (uniform
  shape), and a declined supersession refuses even when the scopes
  happen to be disjoint (the post-gate check)
- on the wizard path a decline refuses before any wizard prompt runs

The pty runner lives in the harness (extracted when this suite became
its second consumer).
"""

from __future__ import annotations

import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from harness import (
    bale_env,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_bale_pty,
    run_checked,
)

# Sentinels for the surfaces this file pins. Kept in one place so a
# message rewording breaks one line, not several assertions.
INTERSECT_MARKER = "pack write forecast intersects"
DECLINED_MARKER = "declined at the prompt"
DECLINE_DEFAULT_MARKER = "decline default applies without a prompt"
DISJOINT_DECLINE_MARKER = "does not collide with this pack"
NOTHING_TO_SUPERSEDE_MARKER = "nothing to supersede"
IDEMPOTENT_MARKER = "idempotent re-run"
PROMPT_MARKER = "Close open session"
WIZARD_GOAL_MARKER = "Goal (one sentence)"
UNLOCK_REMEDY = "bale unlock"


class SupersessionPackTest(unittest.TestCase):
    """`bale pack --supersedes`: exchange, closure record, lineage, gate."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-supersede-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack(self, *extra: str, slug: str, include: str = "hello.txt"):
        """A fully specified piped pack; extras append to the base form."""
        return run_bale(
            self.install,
            [
                "pack", f"supersession test goal for {slug}",
                "--slug", slug,
                "--include", include,
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def pack_pty(self, *extra: str, slug: str, answers: str,
                 include: str = "hello.txt"):
        """A fully specified pack under a pty, feeding prompt answers."""
        return run_bale_pty(
            self.install,
            [
                "pack", f"supersession test goal for {slug}",
                "--slug", slug,
                "--include", include,
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
            answers=answers,
        )

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
        """Pack succeeded; return its sid (the newest registry entry)."""
        self.assert_ok(result)
        sids = self.open_sids()
        self.assertTrue(sids, msg="pack succeeded but no session is open")
        return sids[-1]

    def open_parent(self, slug: str = "parent",
                    include: str = "hello.txt") -> str:
        return self.packed_sid(self.pack(slug=slug, include=include))

    def stamped_manifest(self, sid: str) -> dict:
        p = self.repo / ".bale" / "sessions" / sid / "manifest.json"
        self.assertTrue(p.is_file(), msg=f"no stamped manifest at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def telemetry_record(self, sid: str) -> dict:
        p = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(p.is_file(), msg=f"expected telemetry record at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def add_committed_file(self, name: str) -> None:
        (self.repo / name).write_text(f"{name}\n", encoding="utf-8")
        env = git_env(self.home)
        run_checked(["git", "add", name], cwd=self.repo, env=env)
        run_checked(["git", "commit", "-m", f"add {name}"],
                    cwd=self.repo, env=env)

    def request_manifest_from_tarball(self, sid: str) -> dict:
        """Read manifest.json out of the outbox tarball for `sid` —
        needed when the pack closed its own registry state's sibling
        but we want the shipped manifest, and as a cross-check that
        the stamped and shipped manifests agree."""
        tb = self.repo / ".bale" / "outbox" / f"request-{sid}.tar.gz"
        self.assertTrue(tb.is_file(), msg=f"no outbox tarball at {tb}")
        nnn = sid.rsplit("-", 1)[-1]  # archive top dir is request-NNN
        with tarfile.open(tb, "r:gz") as tf:
            member = tf.extractfile(f"request-{nnn}/manifest.json")
            assert member is not None
            return json.loads(member.read().decode("utf-8"))

    # -- pinned behavior 1: piped decline --------------------------------

    def test_piped_decline_keeps_parent_open_and_gate_refuses(self) -> None:
        """Piped stdin takes the decline default without a prompt;
        nothing closes; the gate refusal names the declined
        supersession and the unlock remedy."""
        parent = self.open_parent()
        result = self.pack("--supersedes", parent, slug="child")
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        combined = result.stdout + result.stderr
        self.assertIn(DECLINE_DEFAULT_MARKER, combined)
        self.assertIn(INTERSECT_MARKER, combined)
        self.assertIn(DECLINED_MARKER, combined)
        self.assertIn(f"{UNLOCK_REMEDY} {parent}", combined)
        self.assertEqual(self.open_sids(), [parent],
                         msg="declined supersession must close nothing")
        # No closure record was written for the parent.
        self.assertFalse(
            (self.repo / "claude" / "telemetry" / f"{parent}.json").is_file())

    # -- pinned behavior 2: pty accept -----------------------------------

    def test_pty_accept_closes_parent_and_stamps_lineage(self) -> None:
        """Accepting the exchange closes the parent superseded-by-split
        (command 'pack'), the child clears the gate, and the child's
        manifest carries depends_on.superseded_session."""
        parent = self.open_parent()
        code, output = self.pack_pty(
            "--supersedes", parent, slug="child", answers="y\n")
        self.assertEqual(code, 0, msg=output)
        self.assertIn(PROMPT_MARKER, output)
        sids = self.open_sids()
        self.assertEqual(len(sids), 1, msg=output)
        child = sids[0]
        self.assertNotEqual(child, parent)
        record = self.telemetry_record(parent)
        latest = record["attempts"][-1]
        self.assertEqual(latest["outcome"], "unlocked")
        self.assertEqual(latest["command"], "pack")
        self.assertEqual(latest["closure_reason"], "superseded-by-split")
        stamped = self.stamped_manifest(child)
        self.assertEqual(
            stamped["depends_on"]["superseded_session"], parent)
        # The shipped tarball's manifest agrees with the stamped one.
        shipped = self.request_manifest_from_tarball(child)
        self.assertEqual(
            shipped["depends_on"]["superseded_session"], parent)

    # -- pinned behavior 3: not open, no history -------------------------

    def test_unknown_sid_refuses(self) -> None:
        result = self.pack("--supersedes", "2020-01-01-bogus-001",
                           slug="child")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(NOTHING_TO_SUPERSEDE_MARKER,
                      result.stdout + result.stderr)
        self.assertEqual(self.open_sids(), [])

    def test_abandoned_closure_does_not_authorize_supersession(self) -> None:
        """A sid closed for any reason other than superseded-by-split
        (here: plain unlock -> 'abandoned') refuses — history must say
        a supersession closed it."""
        parent = self.open_parent()
        self.assert_ok(run_bale(self.install, ["unlock", parent],
                                cwd=self.repo, env=self.env))
        result = self.pack("--supersedes", parent, slug="child")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(NOTHING_TO_SUPERSEDE_MARKER,
                      result.stdout + result.stderr)

    # -- pinned behavior 4: idempotent re-run ----------------------------

    def test_idempotent_rerun_stamps_lineage_with_note(self) -> None:
        """A parent already closed superseded-by-split is accepted on a
        piped re-run (no prompt needed — nothing left to close) and the
        lineage still stamps."""
        parent = self.open_parent()
        code, output = self.pack_pty(
            "--supersedes", parent, slug="child", answers="y\n")
        self.assertEqual(code, 0, msg=output)
        first_child = self.open_sids()[0]
        # Abandon the first child so the re-run's scope is free.
        self.assert_ok(run_bale(self.install, ["unlock", first_child],
                                cwd=self.repo, env=self.env))
        rerun = self.pack("--supersedes", parent, slug="child-retry")
        child2 = self.packed_sid(rerun)
        self.assertIn(IDEMPOTENT_MARKER, rerun.stdout + rerun.stderr)
        self.assertEqual(
            self.stamped_manifest(child2)["depends_on"]["superseded_session"],
            parent)

    # -- pinned behavior 5: gate still runs against siblings -------------

    def test_gate_refuses_second_open_session_after_accept(self) -> None:
        """Supersession clears exactly one collision: an accepted
        exchange closes the parent, but the gate still refuses against
        an unrelated open session — and the aborted child is then
        repairable via the idempotent re-run."""
        self.add_committed_file("other.txt")
        parent = self.open_parent(slug="parent", include="hello.txt")
        sibling = self.packed_sid(
            self.pack(slug="sibling", include="other.txt"))
        # Child scope spans both files -> collides with the sibling.
        code, output = self.pack_pty(
            "--supersedes", parent,
            "--include", "other.txt",  # extends the base hello.txt include
            slug="child", answers="y\n")
        self.assertNotEqual(code, 0, msg=output)
        self.assertIn(INTERSECT_MARKER, output)
        self.assertIn(sibling, output)
        # The accepted close completed before the gate: the parent is
        # gone even though the pack refused — the accepted abort window.
        self.assertEqual(self.open_sids(), [sibling])
        self.assertEqual(
            self.telemetry_record(parent)["attempts"][-1]["closure_reason"],
            "superseded-by-split")
        # Repair path: the piped idempotent re-run at a disjoint scope.
        rerun = self.pack("--supersedes", parent, slug="child-repair")
        child = self.packed_sid(rerun)
        self.assertIn(IDEMPOTENT_MARKER, rerun.stdout + rerun.stderr)
        self.assertEqual(
            self.stamped_manifest(child)["depends_on"]["superseded_session"],
            parent)
        self.assertIn(sibling, self.open_sids())

    # -- stamp defaults and decline edges --------------------------------

    def test_normal_pack_stamps_null(self) -> None:
        """The lineage key is uniformly present: a non-supersession pack
        stamps depends_on.superseded_session null."""
        sid = self.open_parent(slug="plain")
        stamped = self.stamped_manifest(sid)
        self.assertIn("superseded_session", stamped["depends_on"])
        self.assertIsNone(stamped["depends_on"]["superseded_session"])

    def test_disjoint_decline_still_refuses(self) -> None:
        """A declined supersession refuses even when the parent's scope
        does not collide with the pack — a --supersedes pack that
        closes nothing and stamps nothing is not the pack asked for."""
        self.add_committed_file("other.txt")
        parent = self.open_parent(slug="parent", include="hello.txt")
        result = self.pack("--supersedes", parent, slug="child",
                           include="other.txt")
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertIn(DISJOINT_DECLINE_MARKER, combined)
        self.assertEqual(self.open_sids(), [parent])

    def test_wizard_path_decline_refuses_before_prompts(self) -> None:
        """On the wizard path (goal/slug missing) a declined exchange
        refuses immediately — the goal prompt never runs, so no wizard
        answers are collected toward a guaranteed refusal."""
        parent = self.open_parent()
        code, output = run_bale_pty(
            self.install, ["pack", "--supersedes", parent],
            cwd=self.repo, env=self.env, answers="n\n")
        self.assertNotEqual(code, 0, msg=output)
        self.assertIn(PROMPT_MARKER, output)
        self.assertNotIn(WIZARD_GOAL_MARKER, output)
        self.assertEqual(self.open_sids(), [parent])


    # -- board 5 D4 (v0.3.23): reverse lineage superseded_by -------------

    def test_accept_stamps_superseded_by_on_closure_attempt(self) -> None:
        """The accept path stamps the child sid onto the parent's
        superseded-by-split closure attempt — same single writer, no
        new attempt, envelope untouched."""
        parent = self.open_parent()
        code, output = self.pack_pty(
            "--supersedes", parent, slug="child", answers="y\n")
        self.assertEqual(code, 0, msg=output)
        child = self.open_sids()[0]
        record = self.telemetry_record(parent)
        self.assertEqual(len(record["attempts"]), 1,
                         msg="the stamp enriches the closure attempt; "
                             "it never appends")
        latest = record["attempts"][-1]
        self.assertEqual(latest["closure_reason"], "superseded-by-split")
        self.assertEqual(latest["superseded_by"], child)
        self.assertEqual(record["outcome"], "unlocked",
                         msg="the envelope still mirrors the closure — "
                             "the stamp is not a new event")

    def test_decline_stamps_nothing(self) -> None:
        """A declined exchange closes nothing and stamps nothing — no
        record exists at all for the still-open parent."""
        parent = self.open_parent()
        code, _output = self.pack_pty(
            "--supersedes", parent, slug="child", answers="n\n")
        self.assertNotEqual(code, 0)
        self.assertFalse(
            (self.repo / "claude" / "telemetry" / f"{parent}.json").exists())
        self.assertEqual(self.open_sids(), [parent])

    def test_idempotent_rerun_restamps_single_key(self) -> None:
        """The re-run of an aborted supersession pack re-stamps the same
        closure attempt in place: one attempt, one key, and the
        completing pack's child sid wins."""
        parent = self.open_parent()
        code, output = self.pack_pty(
            "--supersedes", parent, slug="child", answers="y\n")
        self.assertEqual(code, 0, msg=output)
        first_child = self.open_sids()[0]
        self.assert_ok(run_bale(self.install, ["unlock", first_child],
                                cwd=self.repo, env=self.env))
        rerun = self.pack("--supersedes", parent, slug="child-retry")
        child2 = self.packed_sid(rerun)
        record = self.telemetry_record(parent)
        split_attempts = [a for a in record["attempts"]
                          if a.get("closure_reason") == "superseded-by-split"]
        self.assertEqual(len(split_attempts), 1,
                         msg="the re-run must not append a second closure")
        self.assertEqual(split_attempts[0]["superseded_by"], child2,
                         msg="latest write wins — the completing pack's "
                             "child is the real supersessor")


if __name__ == "__main__":
    unittest.main()
