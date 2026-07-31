#!/usr/bin/env python3
"""Hermetic E2E for the read-only session shape (v0.3.15).

Pins the board-24 contract: a `bale pack --read-only` (or the wizard's
read-only answer) opens a session whose recorded scope is EMPTY — a
third, distinct scope state. The pairing under test is the load-bearing
claim of the feature: the session is invisible to the ADR-0006/0007
disjointness gates *by design* (an empty scope intersects nothing, so
siblings pack and apply freely while it stays open), and that is safe
*only because* the own-scope drift gate refuses everything such a
session might land (an empty scope covers nothing). Both halves are
asserted here, plus the legacy edge the feature must not disturb: a
*missing* scope.json still reads conservative whole-tree — empty and
missing must never collapse into one state.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring. Two points
specific to this suite: the wizard tests drive bale through a real
pseudo-terminal (the wizard engages only on a TTY, and stubbing
isatty would test a fiction), and the apply tests build a minimal but
fully valid response tarball (computed sha256s, no-op scripts) so the
drift gate is reached through the same pre-flight every real response
passes.

Run directly::

    python3 tests/test_readonly_pack.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import hashlib
import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from harness import (
    bale_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_bale_pty,
)

# Sentinels for the surfaces this file pins. Kept in one place so a
# message rewording breaks one line, not several assertions.
SHAPE_QUESTION_MARKER = "Will this session land changes"
DRIFT_REFUSAL_MARKER = "SCOPE-DRIFT-REFUSED"
READONLY_MARKER = "read-only"
INTERSECT_MARKER = "pack scope intersects"
SWEEP_PROMPT_MARKER = "Close open read-only session"
SWEEP_DECLINE_MARKER = "declining without a prompt"
CLOSEOUT_MARKER = "Read-only session close-out"

# run_bale_pty and PTY_TIMEOUT moved to tests/harness.py when the
# supersession suite became their second consumer (one harness,
# consumed by every suite — the board-11 doctrine).


class ReadonlyPackTest(unittest.TestCase):
    """The read-only session shape: empty scope, gates, wizard, status."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-readonly-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack(self, *extra: str, slug: str = "session-a"):
        """A fully specified piped pack; extras append to the base form."""
        return run_bale(
            self.install,
            [
                "pack", "read-only shape test goal",
                "--slug", slug,
                "--include", "hello.txt",
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def assert_pack_ok(self, result) -> str:
        """Pack succeeded; return its sid (the newest registry entry)."""
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        sids = self.open_sids()
        self.assertTrue(sids, msg="pack succeeded but no session is open")
        return sids[-1]

    def open_sids(self) -> list:
        """Open sids, oldest-first by directory mtime then name."""
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        entries = [d for d in root.iterdir() if (d / "open").is_file()]
        entries.sort(key=lambda d: (d.stat().st_mtime, d.name))
        return [d.name for d in entries]

    def scope_json(self, sid: str):
        """The raw recorded scope for sid, or None when the file is absent."""
        p = self.repo / ".bale" / "sessions" / sid / "scope.json"
        if not p.is_file():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def build_response_tarball(self, sid: str, *, path: str,
                               content: str) -> Path:
        """A minimal, fully valid normal response: one created file.

        Computed size/sha256 (never transcribed), syntactically valid
        no-op apply.sh / validation.sh, and a manifest that passes the
        response schema — so the apply pipeline reaches the drift gate
        through the same pre-flight every real response passes, and a
        refusal there is attributable to the gate, not to a malformed
        fixture.
        """
        nnn = sid[-3:]
        rdir = self.tmp / f"response-{nnn}"
        (rdir / "files").mkdir(parents=True)
        target = rdir / "files" / path
        target.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode("utf-8")
        target.write_bytes(data)
        manifest = {
            "session_id": sid,
            "responds_to": sid,
            "corrects": None,
            "response_kind": "normal",
            "summary": "drift-gate fixture: one created file, outside the "
                       "(empty) read-only scope by construction",
            "changes": [
                {
                    "path": path,
                    "action": "created",
                    "reason": "fixture change to exercise the own-scope "
                              "drift gate against an empty recorded scope",
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            ],
            "deferred": [],
            "validation_will_run": [],
            "claims": {},
        }
        (rdir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        noop = "#!/usr/bin/env bash\n# no-op (test fixture)\nexit 0\n"
        (rdir / "apply.sh").write_text(noop, encoding="utf-8")
        (rdir / "validation.sh").write_text(noop, encoding="utf-8")
        tarball = self.tmp / f"response-{nnn}.tar.gz"
        with tarfile.open(tarball, "w:gz") as tf:
            tf.add(str(rdir), arcname=f"response-{nnn}")
        return tarball

    # -- pinned behavior 1: empty scope recorded -------------------------

    def test_readonly_flag_records_empty_scope(self) -> None:
        """--read-only opens a session whose scope.json is exactly []."""
        sid = self.assert_pack_ok(self.pack("--read-only"))
        self.assertEqual(self.scope_json(sid), [])
        # And the inference: no --work-class given, so the stamp is meta.
        stamped = json.loads(
            (self.repo / ".bale" / "sessions" / sid / "manifest.json")
            .read_text(encoding="utf-8"))
        self.assertEqual(stamped["provenance"]["work_class"], "meta")

    def test_default_pack_scope_unchanged(self) -> None:
        """Without the flag, a piped pack records scope exactly as before."""
        sid = self.assert_pack_ok(self.pack())
        self.assertEqual(self.scope_json(sid), ["hello.txt"])
        stamped = json.loads(
            (self.repo / ".bale" / "sessions" / sid / "manifest.json")
            .read_text(encoding="utf-8"))
        # The un-asked piped path still stamps the pre-v0.3.15 default.
        self.assertEqual(stamped["provenance"]["work_class"], "mixed")

    # -- pinned behavior 2: siblings admitted while it stays open --------

    def test_sibling_pack_admitted_beside_readonly(self) -> None:
        """Any include set packs freely while a read-only session is open."""
        ro_sid = self.assert_pack_ok(self.pack("--read-only"))
        second = self.pack(slug="session-b")
        self.assertEqual(
            second.returncode, 0,
            msg=f"stdout:\n{second.stdout}\nstderr:\n{second.stderr}",
        )
        sids = self.open_sids()
        self.assertEqual(len(sids), 2)
        self.assertIn(ro_sid, sids)

    def test_whole_tree_sibling_admitted_beside_readonly(self) -> None:
        """Even a whole-tree pack is admitted beside a read-only session
        (and only beside it): [] intersects nothing, including '.'."""
        self.assert_pack_ok(self.pack("--read-only"))
        second = run_bale(
            self.install,
            ["pack", "whole tree beside read-only", "--slug", "session-b",
             "--no-readme", "--force"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            second.returncode, 0,
            msg=f"stdout:\n{second.stdout}\nstderr:\n{second.stderr}",
        )
        self.assertEqual(len(self.open_sids()), 2)

    # -- pinned behavior 3: legacy missing-scope path untouched ----------

    def test_missing_scope_json_stays_conservative(self) -> None:
        """A deleted scope.json reads whole-tree: empty ≠ missing."""
        ro_sid = self.assert_pack_ok(self.pack("--read-only"))
        (self.repo / ".bale" / "sessions" / ro_sid / "scope.json").unlink()
        second = self.pack(slug="session-b")
        self.assertEqual(second.returncode, 1, msg=second.stdout)
        self.assertIn(INTERSECT_MARKER, second.stderr)
        self.assertIn(ro_sid, second.stderr)

    # -- pinned behavior 4: the drift gate refuses every self-land -------

    def test_apply_refuses_drift_for_readonly_session(self) -> None:
        """Any changes[] under the read-only sid refuses at the drift gate,
        and the refusal names the session as read-only."""
        sid = self.assert_pack_ok(self.pack("--read-only"))
        tarball = self.build_response_tarball(
            sid, path="landed.txt", content="should never land\n")
        result = run_bale(
            self.install, ["apply", str(tarball)],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 1,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertIn(DRIFT_REFUSAL_MARKER, result.stdout)
        self.assertIn(READONLY_MARKER, result.stdout)
        # Refusal is pre-staging: nothing landed, session stays open.
        self.assertFalse((self.repo / "landed.txt").exists())
        self.assertIn(sid, self.open_sids())

    def test_allow_out_of_scope_admits_past_gate(self) -> None:
        """--allow-out-of-scope admits named paths past the gate for a
        read-only session too (uniform override, master's recommendation;
        exercised under --dry-run, which runs the same gate)."""
        sid = self.assert_pack_ok(self.pack("--read-only"))
        tarball = self.build_response_tarball(
            sid, path="landed.txt", content="admitted deliberately\n")
        refused = run_bale(
            self.install, ["apply", str(tarball), "--dry-run"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(refused.returncode, 1, msg=refused.stdout)
        self.assertIn(DRIFT_REFUSAL_MARKER, refused.stdout)
        admitted = run_bale(
            self.install,
            ["apply", str(tarball), "--dry-run",
             "--allow-out-of-scope", "landed.txt"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            admitted.returncode, 0,
            msg=f"stdout:\n{admitted.stdout}\nstderr:\n{admitted.stderr}",
        )
        self.assertNotIn(DRIFT_REFUSAL_MARKER, admitted.stdout)
        # Dry run: still nothing on disk.
        self.assertFalse((self.repo / "landed.txt").exists())

    # -- pinned behavior 5: wizard reaches the question; flags skip it ---

    def test_wizard_reaches_session_shape_question(self) -> None:
        """A bare cold-start wizard run asks the question; the read-only
        answer records an empty scope and infers work_class meta."""
        answers = (
            "wizard read-only goal\n"   # goal
            "wizard-ro\n"               # slug
            "r\n"                       # session shape: read-only
            "\n"                        # excludes: none
            "\n"                        # constraints: none
            "\n"                        # out-of-scope: none
            "n\n"                       # README prompt: no
        )
        code, output = run_bale_pty(
            self.install, ["pack"], cwd=self.repo, env=self.env,
            answers=answers,
        )
        self.assertEqual(code, 0, msg=output)
        self.assertIn(SHAPE_QUESTION_MARKER, output)
        sids = self.open_sids()
        self.assertEqual(len(sids), 1, msg=output)
        self.assertEqual(self.scope_json(sids[0]), [])
        stamped = json.loads(
            (self.repo / ".bale" / "sessions" / sids[0] / "manifest.json")
            .read_text(encoding="utf-8"))
        self.assertEqual(stamped["provenance"]["work_class"], "meta")

    def test_wizard_default_answer_keeps_whole_tree(self) -> None:
        """Bare Enter at the question is the pre-v0.3.15 pack: mixed
        work class, whole-tree scope — an answered default now."""
        answers = (
            "wizard default goal\n"
            "wizard-default\n"
            "\n"                        # session shape: Enter -> mixed
            "\n" "\n" "\n"              # excludes, constraints, oos
            "n\n"                       # README prompt: no
        )
        code, output = run_bale_pty(
            self.install, ["pack"], cwd=self.repo, env=self.env,
            answers=answers,
        )
        self.assertEqual(code, 0, msg=output)
        self.assertIn(SHAPE_QUESTION_MARKER, output)
        sids = self.open_sids()
        self.assertEqual(len(sids), 1, msg=output)
        self.assertEqual(self.scope_json(sids[0]), ["."])
        stamped = json.loads(
            (self.repo / ".bale" / "sessions" / sids[0] / "manifest.json")
            .read_text(encoding="utf-8"))
        self.assertEqual(stamped["provenance"]["work_class"], "mixed")

    def test_bare_flag_path_skips_question(self) -> None:
        """A fully specified command never shows the question — piped
        here, which also proves no prompt path engages at all."""
        result = self.pack("--read-only")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        combined = result.stdout + result.stderr
        self.assertNotIn(SHAPE_QUESTION_MARKER, combined)

    # -- status rendering ------------------------------------------------

    def test_status_renders_readonly_scope(self) -> None:
        """`bale status` names the empty scope instead of printing an
        empty string or a whole-tree reading."""
        self.assert_pack_ok(self.pack("--read-only"))
        result = run_bale(
            self.install, ["status"], cwd=self.repo, env=self.env,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("locks nothing, lands nothing", result.stdout)
        self.assertNotIn(". (whole tree)", result.stdout)

    # -- board 33 (v0.3.21): the resolved_scope manifest stamp -----------

    def stamped_manifest(self, sid: str) -> dict:
        p = self.repo / ".bale" / "sessions" / sid / "manifest.json"
        self.assertTrue(p.is_file(), msg=f"no stamped manifest at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def shipped_manifest(self, sid: str) -> dict:
        """manifest.json out of the outbox tarball — the copy the worker
        reads, cross-checked against the registry-side stamp."""
        tb = self.repo / ".bale" / "outbox" / f"request-{sid}.tar.gz"
        self.assertTrue(tb.is_file(), msg=f"no outbox tarball at {tb}")
        nnn = sid.rsplit("-", 1)[-1]
        with tarfile.open(tb, "r:gz") as tf:
            member = tf.extractfile(f"request-{nnn}/manifest.json")
            assert member is not None
            return json.loads(member.read().decode("utf-8"))

    def test_manifest_stamps_empty_scope_for_readonly(self) -> None:
        """A read-only pack stamps resolved_scope: [] — the manifest
        carries the registry-recorded scope, [] for the read-only
        shape, in both the stamped and the shipped copies."""
        sid = self.assert_pack_ok(self.pack("--read-only"))
        self.assertEqual(self.stamped_manifest(sid)["resolved_scope"], [])
        self.assertEqual(self.shipped_manifest(sid)["resolved_scope"], [])

    def test_manifest_stamp_equals_recorded_scope(self) -> None:
        """A scoped pack's resolved_scope equals scope.json exactly —
        one source, never a re-derivation."""
        sid = self.assert_pack_ok(self.pack())
        recorded = self.scope_json(sid)
        self.assertEqual(recorded, ["hello.txt"])
        self.assertEqual(self.stamped_manifest(sid)["resolved_scope"],
                         recorded)
        self.assertEqual(self.shipped_manifest(sid)["resolved_scope"],
                         recorded)

    # -- board 33 (v0.3.21): the read-only sweep -------------------------

    def telemetry_record(self, sid: str) -> dict:
        p = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(p.is_file(), msg=f"expected telemetry record at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def readonly_pack_pty(self, *, slug: str, answers: str):
        """A fully specified read-only pack under a pty, so the sweep
        prompt (the only prompt on this path) can engage."""
        return run_bale_pty(
            self.install,
            [
                "pack", "read-only sweep test goal",
                "--slug", slug,
                "--include", "hello.txt",
                "--no-readme",
                "--read-only",
            ],
            cwd=self.repo, env=self.env, answers=answers,
        )

    def test_sweep_accept_default_closes_open_readonly(self) -> None:
        """Bare Enter at the sweep prompt takes the ACCEPT default
        (the deliberate inversion of --supersedes' decline default):
        the open read-only session closes as closed-read-only with
        command 'pack' through the closure machinery, durably."""
        first = self.assert_pack_ok(self.pack("--read-only"))
        code, output = self.readonly_pack_pty(slug="session-b",
                                              answers="\n")
        self.assertEqual(code, 0, msg=output)
        self.assertIn(SWEEP_PROMPT_MARKER, output)
        self.assertIn("[Y/n]", output,
                      msg="the sweep prompt must show the accept default")
        sids = self.open_sids()
        self.assertEqual(len(sids), 1, msg=output)
        self.assertNotIn(first, sids)
        latest = self.telemetry_record(first)["attempts"][-1]
        self.assertEqual(latest["outcome"], "unlocked")
        self.assertEqual(latest["command"], "pack")
        self.assertEqual(latest["closure_reason"], "closed-read-only")
        self.assertEqual(latest["scope"], [])

    def test_sweep_explicit_decline_keeps_session_open(self) -> None:
        """'n' at the sweep prompt declines: nothing closes, both
        read-only sessions stay open, no closure record is written."""
        first = self.assert_pack_ok(self.pack("--read-only"))
        code, output = self.readonly_pack_pty(slug="session-b",
                                              answers="n\n")
        self.assertEqual(code, 0, msg=output)
        self.assertIn(SWEEP_PROMPT_MARKER, output)
        sids = self.open_sids()
        self.assertEqual(len(sids), 2, msg=output)
        self.assertIn(first, sids)
        self.assertFalse(
            (self.repo / "claude" / "telemetry" / f"{first}.json").is_file())

    def test_sweep_piped_declines_without_prompt(self) -> None:
        """Piped stdin declines without a prompt — automation never
        silently closes a session. Both sessions stay open and the
        decline is logged, naming the unlock remedy."""
        first = self.assert_pack_ok(self.pack("--read-only"))
        second = self.pack("--read-only", slug="session-b")
        self.assertEqual(
            second.returncode, 0,
            msg=f"stdout:\n{second.stdout}\nstderr:\n{second.stderr}",
        )
        combined = second.stdout + second.stderr
        self.assertIn(SWEEP_DECLINE_MARKER, combined)
        self.assertNotIn(SWEEP_PROMPT_MARKER, combined)
        sids = self.open_sids()
        self.assertEqual(len(sids), 2)
        self.assertIn(first, sids)
        self.assertFalse(
            (self.repo / "claude" / "telemetry" / f"{first}.json").is_file())

    def test_scoped_pack_never_sweeps(self) -> None:
        """A worker (scoped) pack beside an open read-only session
        neither prompts nor closes — the sweep is the read-only
        pack's alone."""
        first = self.assert_pack_ok(self.pack("--read-only"))
        second = self.pack(slug="session-b")
        self.assertEqual(second.returncode, 0, msg=second.stderr)
        combined = second.stdout + second.stderr
        self.assertNotIn("read-only sweep", combined)
        self.assertIn(first, self.open_sids())

    def test_apply_never_sweeps(self) -> None:
        """An apply beside an open read-only session leaves it
        untouched — here a sibling scoped session's response is run
        through apply --dry-run; the apply's own verdict on the
        fixture is irrelevant to this pin, which is only that the
        apply pipeline neither prompts for nor closes the read-only
        sibling."""
        ro_sid = self.assert_pack_ok(self.pack("--read-only"))
        scoped_sid = self.assert_pack_ok(self.pack(slug="session-b"))
        tarball = self.build_response_tarball(
            scoped_sid, path="hello.txt", content="hello edited\n")
        result = run_bale(
            self.install, ["apply", str(tarball), "--dry-run"],
            cwd=self.repo, env=self.env,
        )
        combined = result.stdout + result.stderr
        self.assertNotIn("read-only sweep", combined)
        self.assertIn(ro_sid, self.open_sids())
        self.assertFalse(
            (self.repo / "claude" / "telemetry" / f"{ro_sid}.json").is_file())

    # -- board 33 (v0.3.21): the open banner names its close-out ---------

    def test_readonly_banner_names_both_closeouts(self) -> None:
        """The read-only pack's end-of-run banner names both exits:
        the next read-only pack's sweep, and `bale unlock <sid>`."""
        result = self.pack("--read-only")
        sid = self.assert_pack_ok(result)
        self.assertIn(CLOSEOUT_MARKER, result.stdout)
        self.assertIn("next read-only pack", result.stdout)
        self.assertIn(f"bale unlock {sid}", result.stdout)

    def test_scoped_banner_has_no_closeout(self) -> None:
        """A scoped pack's banner is unchanged — no close-out lines."""
        result = self.pack()
        self.assert_pack_ok(result)
        self.assertNotIn(CLOSEOUT_MARKER, result.stdout)


if __name__ == "__main__":
    unittest.main()
