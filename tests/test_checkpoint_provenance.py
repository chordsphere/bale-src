#!/usr/bin/env python3
"""Hermetic E2E for blindness enforcement (board 6 session C, v0.3.28).

Covers the D8 session-C assertion set against the documented contract
(BALE.md §7.1 step 4b, §7.2, §8.5, §11 rows 27–28; ADR-0002 oracle
doctrine — observable state, never golden comparisons):

- pack refuses a resolved include set that covers the configured
  checkpoint's path — by direct file include and by directory include
  (the same containment semantics as the drift gate) — before any sid
  or session state exists;
- --allow-checkpoint-in-scope admits the covering scope: the pack
  succeeds, the FORCE: line lands in the output, and the request
  manifest's provenance stamps checkpoint_scope_admitted: true;
- the provenance stamp is present and correct when a checkpoint is
  configured ({path, sha256} equal to the committed bytes' hash) and
  explicit null when none is — key presence being what separates a
  v0.3.28 pack from a hand-rolled or pre-stamp request;
- pack refuses a configured-but-dangling checkpoint at its own
  pre-flight (the D1 rule caught at request-build time);
- apply refuses when the base-tree bytes about to run diverge from the
  request's pack-time stamp (the oracle changed between pack and
  apply): remedy text present, session stays open, no bale/<sid>
  branch — the refusal is pre-staging, pre-branch;
- `bale apply --dry-run` predicts the same divergence refusal;
- --accept-checkpoint-change executes the CURRENT base-tree bytes —
  asserted on EXECUTED output (the new marker ran; the stale stamped
  version's marker did not) — and records stamp_matched: false in the
  attempt's telemetry stamp;
- a stampless request (the provenance.checkpoint key stripped from the
  persisted session manifest, simulating a hand-rolled or pre-v0.3.28
  request) verifies nothing and stamps stamp_matched: null;
- the retry path re-states the flag (v0.3.29, board 6 session D — the
  session-C notes' proposed rider): after a HOLD, a diverged oracle
  refuses `bale retry` without `--accept-checkpoint-change` exactly as
  apply would, and re-stating the flag on the retry invocation admits
  it — current base-tree bytes run, stamp_matched: false on the retry
  attempt beside the HOLD attempt's verified true;
- a read-only pack passes the blindness gate vacuously (empty scope
  covers nothing) while still stamping checkpoint provenance;
- the handoff path runs the same gate (v0.3.33, §11 row 30): a
  handoff whose reading-plan scope covers the configured checkpoint
  refuses pre-sid without `--allow-checkpoint-in-scope` (no new
  session state), the mirroring flag admits it — FORCE-logged,
  `checkpoint_scope_admitted: true` stamped through the shared
  provenance builder — a non-covering reading plan passes with the
  stamp false, and a reading plan citing no files resolves to the
  whole tree, which covers the checkpoint and refuses the same way a
  default whole-tree pack does.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_checkpoint_provenance.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
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
    run_checked,
)

CHECKPOINT_PATH = "scripts/validation.base.sh"

# Sentinels for the surfaces this file pins.
SCOPE_REFUSAL_PHRASE = "write forecast covers the blind checkpoint"
PACK_DANGLING_PHRASE = "blind checkpoint missing at the pack-time tip"
DIVERGENCE_PHRASE = "blind checkpoint changed since pack"
STAMPLESS_PHRASE = "request carries no checkpoint provenance stamp"
V1_MARKER = "PROV-MARKER-V1"
V2_MARKER = "PROV-MARKER-V2"

NEW_CONTENT = "hello from the provenance fixture response\n"


def checkpoint_script(marker: str, exit_code: int = 0) -> str:
    """A committed-checkpoint fixture honoring TARBALL.md §7.2/§7.5."""
    verdict = "PASS" if exit_code == 0 else "FAIL"
    return (
        "#!/usr/bin/env bash\n"
        f"echo \"[{verdict}] {marker}\"\n"
        f"exit {exit_code}\n"
    )


class CheckpointProvenanceE2ETest(unittest.TestCase):
    """The board 6 session C contract, driven through real pack/apply."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-cpprov-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def configure_checkpoint(self, path: str = CHECKPOINT_PATH) -> None:
        """Write bale.toml naming the checkpoint (hand-edit is valid —
        the wizard is canonical, not exclusive; the strict accessor is
        what pack and apply read through)."""
        (self.repo / "bale.toml").write_text(
            f"[validation]\nbase = \"{path}\"\n", encoding="utf-8")

    def commit_checkpoint(self, body: str,
                          message: str = "pin blind checkpoint") -> str:
        """Commit the checkpoint script; return the committed bytes'
        sha256 — the tip identity both the pack stamp and apply's
        verification must agree on."""
        p = self.repo / CHECKPOINT_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        data = body.encode("utf-8")
        p.write_bytes(data)
        p.chmod(0o755)
        run_checked(["git", "add", CHECKPOINT_PATH],
                    cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", message],
                    cwd=self.repo, env=self.genv)
        return hashlib.sha256(data).hexdigest()

    def pack(self, *extra_args: str, slug: str = "cp-prov"):
        """Run a minimal in-scope pack; return the CompletedProcess."""
        return run_bale(
            self.install,
            ["pack", "checkpoint provenance e2e goal: rewrite hello.txt",
             "--slug", slug, "--include", "hello.txt", *extra_args,
             "--no-readme"],
            cwd=self.repo, env=self.env,
        )

    def only_open_sid(self) -> str:
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        return sids[0]

    def session_request_manifest(self, sid: str) -> dict:
        p = self.repo / ".bale" / "sessions" / sid / "manifest.json"
        return json.loads(p.read_text(encoding="utf-8"))

    def build_response_tarball(self, sid: str, *, name: str,
                               validation_exit: int = 0) -> Path:
        """A valid normal response modifying hello.txt (in scope).
        Sizes and hashes computed, never transcribed. `validation_exit`
        drives the worker verdict — 1 for the retry rider's HOLD leg,
        the default 0 everywhere else (the pre-rider behavior,
        unchanged)."""
        nnn = sid[-3:]
        rdir = self.tmp / name / f"response-{nnn}"
        (rdir / "files").mkdir(parents=True)
        data = NEW_CONTENT.encode("utf-8")
        (rdir / "files" / "hello.txt").write_bytes(data)
        manifest = {
            "session_id": sid,
            "responds_to": sid,
            "corrects": None,
            "response_kind": "normal",
            "summary": "checkpoint provenance fixture: rewrite hello.txt",
            "changes": [
                {
                    "path": "hello.txt",
                    "action": "modified",
                    "reason": "the goal's rewrite; the fixture's "
                              "in-scope payload change",
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            ],
            "deferred": [],
            "validation_will_run": ["fixture check"],
            "claims": {},
        }
        (rdir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (rdir / "apply.sh").write_text(
            "#!/usr/bin/env bash\n# no-op (test fixture)\nexit 0\n",
            encoding="utf-8")
        verdict = "FAIL" if validation_exit else "PASS"
        (rdir / "validation.sh").write_text(
            "#!/usr/bin/env bash\n"
            f"echo \"[{verdict}] fixture check\"\n"
            f"exit {validation_exit}\n",
            encoding="utf-8")
        tarball = self.tmp / name / f"response-{nnn}.tar.gz"
        with tarfile.open(tarball, "w:gz") as tf:
            tf.add(str(rdir), arcname=f"response-{nnn}")
        return tarball

    def session_log(self, sid: str) -> str:
        p = self.repo / ".bale" / "logs" / f"{sid}.log"
        self.assertTrue(p.is_file(), msg=f"expected session log at {p}")
        return p.read_text(encoding="utf-8")

    def telemetry_record(self, sid: str) -> dict:
        p = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(p.is_file(), msg=f"expected telemetry record at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def assert_no_bale_branch(self, sid: str, why: str) -> None:
        rp = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/heads/bale/{sid}"],
            cwd=self.repo, env=self.genv, capture_output=True, text=True)
        self.assertNotEqual(rp.returncode, 0, msg=why)

    # -- pack side: the blindness gate (D5 layer 1) ----------------------

    def test_pack_refuses_direct_include_of_checkpoint(self) -> None:
        """A resolved include set naming the checkpoint path directly is
        refused, pre-sid: remedy text present, no session opened, no
        session directory created."""
        self.commit_checkpoint(checkpoint_script(V1_MARKER))
        self.configure_checkpoint()
        refused = self.pack("--include", CHECKPOINT_PATH)
        self.assertNotEqual(refused.returncode, 0)
        combined = refused.stdout + refused.stderr
        self.assertIn(SCOPE_REFUSAL_PHRASE, combined)
        self.assertIn("--allow-checkpoint-in-scope", combined,
                      msg="the refusal names its override successor")
        # The caller-aware remedy sentence (v0.3.34; re-based to the
        # forecast's own lever by ADR-0015): pack's refusal carries the
        # pack-flavored narrowing remedy — --write, since the forecast
        # is what covered the oracle here — never handoff's; only the
        # one sentence differs between callers.
        self.assertIn("narrow this pack's write forecast with --write "
                      "paths", combined)
        self.assertNotIn("re-bail with a reading plan", combined)
        self.assertFalse(
            (self.repo / ".bale" / "sessions").exists(),
            msg="the refusal is pre-sid — no session state may exist")

    def test_pack_refuses_directory_include_covering_checkpoint(self) -> None:
        """Coverage uses the drift gate's containment semantics: a
        directory include covering the checkpoint's parent refuses the
        same way a direct include does."""
        self.commit_checkpoint(checkpoint_script(V1_MARKER))
        self.configure_checkpoint()
        refused = self.pack("--include", "scripts")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn(SCOPE_REFUSAL_PHRASE,
                      refused.stdout + refused.stderr)

    def test_override_admits_and_stamps_the_admission(self) -> None:
        """--allow-checkpoint-in-scope admits the covering scope: the
        pack succeeds, the FORCE: line is in the output, and provenance
        stamps checkpoint_scope_admitted: true beside the checkpoint
        stamp itself."""
        sha = self.commit_checkpoint(checkpoint_script(V1_MARKER))
        self.configure_checkpoint()
        admitted = self.pack("--include", "scripts",
                             "--allow-checkpoint-in-scope")
        self.assertEqual(
            admitted.returncode, 0,
            msg=f"stdout:\n{admitted.stdout}\nstderr:\n{admitted.stderr}")
        combined = admitted.stdout + admitted.stderr
        self.assertIn("FORCE:", combined)
        self.assertIn("--allow-checkpoint-in-scope", combined)
        provenance = self.session_request_manifest(
            self.only_open_sid())["provenance"]
        self.assertIs(provenance["checkpoint_scope_admitted"], True)
        self.assertEqual(provenance["checkpoint"],
                         {"path": CHECKPOINT_PATH, "sha256": sha})

    def test_pack_refuses_dangling_checkpoint(self) -> None:
        """Config naming a checkpoint absent at the pack-time tip is a
        loud pack refusal — the D1 rule caught at request-build time,
        before a session doomed to refuse at apply can exist."""
        self.configure_checkpoint("scripts/never-committed.sh")
        refused = self.pack()
        self.assertNotEqual(refused.returncode, 0)
        combined = refused.stdout + refused.stderr
        self.assertIn(PACK_DANGLING_PHRASE, combined)
        self.assertIn("committed-is-ratified", combined)

    def test_read_only_pack_passes_gate_and_still_stamps(self) -> None:
        """A read-only pack's empty scope covers nothing, so the
        blindness gate passes vacuously — and the provenance stamp is
        still written (a master session's request records the oracle it
        was packed under too)."""
        sha = self.commit_checkpoint(checkpoint_script(V1_MARKER))
        self.configure_checkpoint()
        packed = run_bale(
            self.install,
            ["pack", "read-only alongside a pinned checkpoint",
             "--slug", "cp-ro", "--read-only", "--include", "hello.txt",
             "--no-readme"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            packed.returncode, 0,
            msg=f"stdout:\n{packed.stdout}\nstderr:\n{packed.stderr}")
        provenance = self.session_request_manifest(
            self.only_open_sid())["provenance"]
        self.assertEqual(provenance["checkpoint"],
                         {"path": CHECKPOINT_PATH, "sha256": sha})
        self.assertIs(provenance["checkpoint_scope_admitted"], False)

    # -- pack side: the stamp itself (D5 layer 2, write half) ------------

    def test_stamp_present_and_correct_when_configured(self) -> None:
        """provenance.checkpoint carries the configured path and the
        sha256 of the COMMITTED tip bytes — asserted against a hash
        computed from the bytes handed to git, with a diverging
        working-tree edit in place to prove the stamp never reads the
        working tree (committed-is-ratified)."""
        sha = self.commit_checkpoint(checkpoint_script(V1_MARKER))
        # A working-tree-only edit the stamp must NOT honor.
        (self.repo / CHECKPOINT_PATH).write_text(
            checkpoint_script("working-tree-only-edit"), encoding="utf-8")
        self.configure_checkpoint()
        packed = self.pack()
        self.assertEqual(
            packed.returncode, 0,
            msg=f"stdout:\n{packed.stdout}\nstderr:\n{packed.stderr}")
        provenance = self.session_request_manifest(
            self.only_open_sid())["provenance"]
        self.assertEqual(
            provenance["checkpoint"],
            {"path": CHECKPOINT_PATH, "sha256": sha},
            msg="the stamp hashes the committed tip bytes, never a "
                "working-tree copy")

    def test_stamp_explicit_null_when_unconfigured(self) -> None:
        """No [validation] config: the key is PRESENT with value null —
        the known-zero form that keeps key ABSENCE meaning a
        hand-rolled or pre-v0.3.28 request."""
        packed = self.pack()
        self.assertEqual(packed.returncode, 0)
        provenance = self.session_request_manifest(
            self.only_open_sid())["provenance"]
        self.assertIn("checkpoint", provenance)
        self.assertIsNone(provenance["checkpoint"])
        self.assertIs(provenance["checkpoint_scope_admitted"], False)

    # -- apply side: stamp verification (D5 layer 2, read half) ----------

    def _packed_sid_with_committed_checkpoint(self) -> str:
        self.commit_checkpoint(checkpoint_script(V1_MARKER))
        self.configure_checkpoint()
        packed = self.pack()
        self.assertEqual(
            packed.returncode, 0,
            msg=f"stdout:\n{packed.stdout}\nstderr:\n{packed.stderr}")
        return self.only_open_sid()

    def test_divergence_refuses_before_staging(self) -> None:
        """The planner edits and commits the checkpoint after pack: the
        base-tree bytes about to run no longer match the stamp, and
        apply refuses — remedy text present, session open, no bale
        branch (pre-staging, pre-branch)."""
        sid = self._packed_sid_with_committed_checkpoint()
        self.commit_checkpoint(checkpoint_script(V2_MARKER),
                               message="planner edits the oracle post-pack")
        tarball = self.build_response_tarball(sid, name="diverge")
        refused = run_bale(self.install, ["apply", str(tarball)],
                           cwd=self.repo, env=self.env)
        self.assertNotEqual(refused.returncode, 0)
        combined = refused.stdout + refused.stderr
        self.assertIn(DIVERGENCE_PHRASE, combined)
        self.assertIn("--accept-checkpoint-change", combined,
                      msg="the refusal names its override successor")
        self.assertIn("re-pack", combined,
                      msg="the refusal names the honest-path successor")
        self.assertTrue(
            (self.repo / ".bale" / "sessions" / sid / "open").is_file(),
            msg="the refusal leaves the session open")
        self.assert_no_bale_branch(
            sid, "no bale/<sid> branch may exist after the refusal — it "
                 "must fire before branch creation")

    def test_dry_run_predicts_divergence(self) -> None:
        """`bale apply --dry-run` refuses a diverged checkpoint with the
        same message plus the prediction trailer — the session-B rider's
        pattern extended to the stamp verification."""
        sid = self._packed_sid_with_committed_checkpoint()
        self.commit_checkpoint(checkpoint_script(V2_MARKER),
                               message="planner edits the oracle post-pack")
        tarball = self.build_response_tarball(sid, name="divergedry")
        dry = run_bale(self.install,
                       ["apply", str(tarball), "--dry-run"],
                       cwd=self.repo, env=self.env)
        self.assertEqual(dry.returncode, 1,
                         msg=f"stdout:\n{dry.stdout}\n"
                             f"stderr:\n{dry.stderr}")
        combined = dry.stdout + dry.stderr
        self.assertIn(DIVERGENCE_PHRASE, combined)
        self.assertIn("a real apply would refuse the same way", combined)

    def test_accept_change_runs_current_bytes_and_records_false(self) -> None:
        """--accept-checkpoint-change executes the CURRENT base-tree
        version — asserted on EXECUTED output: the post-pack oracle's
        marker ran, the stale stamped version's did not — logs FORCE:,
        and records stamp_matched: false in the telemetry stamp."""
        sid = self._packed_sid_with_committed_checkpoint()
        self.commit_checkpoint(checkpoint_script(V2_MARKER),
                               message="planner edits the oracle post-pack")
        tarball = self.build_response_tarball(sid, name="accept")
        merged = run_bale(
            self.install,
            ["apply", str(tarball), "--accept-checkpoint-change"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            merged.returncode, 0,
            msg=f"stdout:\n{merged.stdout}\nstderr:\n{merged.stderr}")

        log = self.session_log(sid)
        self.assertIn("FORCE:", log)
        self.assertIn(V2_MARKER, log,
                      msg="the CURRENT (post-edit) base-tree oracle ran")
        self.assertNotIn(V1_MARKER, log,
                         msg="the stale stamped bytes must never execute")

        stamp = self.telemetry_record(sid)["attempts"][-1]["checkpoint"]
        self.assertIs(stamp["stamp_matched"], False)
        self.assertEqual(
            stamp["script"]["sha256"],
            hashlib.sha256(
                checkpoint_script(V2_MARKER).encode("utf-8")).hexdigest(),
            msg="the telemetry stamp hashes the executed current bytes")

    def test_retry_refuses_divergence_and_restates_the_flag(self) -> None:
        """The lifecycle-wide re-state contract, pinned on the retry
        wiring (v0.3.29, board 6 session D — the session-C notes'
        proposed rider): a HOLD leaves the session open, the planner
        diverges the oracle, and `bale retry` without the flag refuses
        exactly as apply would; re-stating `--accept-checkpoint-change`
        on the retry invocation admits it — the CURRENT base-tree
        bytes run and the retry attempt records stamp_matched: false
        beside the first attempt's verified true."""
        sid = self._packed_sid_with_committed_checkpoint()

        # Attempt 1: worker validation fails while the oracle still
        # matches its stamp — a plain HOLD (piped default: inspect),
        # session open, stamp verified on that attempt.
        holding = self.build_response_tarball(sid, name="retryhold",
                                              validation_exit=1)
        held = run_bale(self.install, ["apply", str(holding)],
                        cwd=self.repo, env=self.env)
        self.assertEqual(held.returncode, 1,
                         msg=f"stdout:\n{held.stdout}\n"
                             f"stderr:\n{held.stderr}")
        record = self.telemetry_record(sid)
        self.assertEqual(record["outcome"], "held")
        first_stamp = record["attempts"][0]["checkpoint"]
        self.assertIs(first_stamp["stamp_matched"], True)
        self.assertEqual(
            first_stamp["script"]["sha256"],
            hashlib.sha256(
                checkpoint_script(V1_MARKER).encode("utf-8")).hexdigest())

        # The planner edits and commits the oracle post-HOLD.
        self.commit_checkpoint(checkpoint_script(V2_MARKER),
                               message="planner edits the oracle mid-hold")

        # Retry WITHOUT the flag: the same divergence refusal apply
        # gives — nothing carried from any earlier invocation, the
        # session stays open, and no second attempt is recorded (the
        # refusal is pre-staging, pre-telemetry).
        fixed = self.build_response_tarball(sid, name="retryfix")
        refused = run_bale(self.install, ["retry", str(fixed)],
                           cwd=self.repo, env=self.env)
        self.assertNotEqual(refused.returncode, 0)
        combined = refused.stdout + refused.stderr
        self.assertIn(DIVERGENCE_PHRASE, combined)
        self.assertIn("--accept-checkpoint-change", combined,
                      msg="the retry refusal names its override "
                          "successor too")
        self.assertTrue(
            (self.repo / ".bale" / "sessions" / sid / "open").is_file(),
            msg="the refused retry leaves the session open")
        # The refusal lands in telemetry through the shared
        # rejected-path wrapper (BALE.md §8.9) — a `rejected` attempt
        # with validation null and, by the always-stamp rule's other
        # half, no checkpoint key: nothing executed, so there is
        # nothing to stamp.
        record = self.telemetry_record(sid)
        self.assertEqual(len(record["attempts"]), 2)
        rejected_attempt = record["attempts"][1]
        self.assertEqual(rejected_attempt["outcome"], "rejected")
        self.assertEqual(rejected_attempt["command"], "retry")
        self.assertIsNone(rejected_attempt["validation"])
        self.assertNotIn("checkpoint", rejected_attempt)

        # Retry WITH the flag re-stated on this invocation: admitted —
        # the CURRENT base-tree oracle runs and the retry merges.
        merged = run_bale(
            self.install,
            ["retry", str(fixed), "--accept-checkpoint-change"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            merged.returncode, 0,
            msg=f"stdout:\n{merged.stdout}\nstderr:\n{merged.stderr}")

        log = self.session_log(sid)
        self.assertIn("FORCE:", log)
        self.assertIn(V2_MARKER, log,
                      msg="the CURRENT (post-edit) base-tree oracle ran "
                          "on the retry")

        # All three attempts accumulated (the §8.9 append semantics):
        # the HOLD, the rejected divergence refusal, and the admitted
        # retry — the validated pair each carrying its own verification
        # result: verified true on the HOLD, admitted false on the
        # retry. The per-attempt stamp is what makes the mid-session
        # divergence auditable later.
        record = self.telemetry_record(sid)
        self.assertEqual(record["outcome"], "applied")
        self.assertEqual(len(record["attempts"]), 3)
        held_attempt, _rejected, applied_attempt = record["attempts"]
        self.assertEqual(applied_attempt["command"], "retry")
        self.assertIs(held_attempt["checkpoint"]["stamp_matched"], True)
        retry_stamp = applied_attempt["checkpoint"]
        self.assertIs(retry_stamp["stamp_matched"], False)
        self.assertEqual(
            retry_stamp["script"]["sha256"],
            hashlib.sha256(
                checkpoint_script(V2_MARKER).encode("utf-8")).hexdigest(),
            msg="the retry's telemetry stamp hashes the executed "
                "current bytes")

    def test_stampless_request_verifies_nothing(self) -> None:
        """A request without the provenance.checkpoint key — a
        hand-rolled request, or one packed pre-v0.3.28, simulated by
        stripping the key from the persisted session manifest — verifies
        nothing (logged, never silent) and stamps stamp_matched: null,
        even when the oracle changed post-pack."""
        sid = self._packed_sid_with_committed_checkpoint()
        manifest_path = (self.repo / ".bale" / "sessions" / sid
                         / "manifest.json")
        request_manifest = json.loads(
            manifest_path.read_text(encoding="utf-8"))
        del request_manifest["provenance"]["checkpoint"]
        del request_manifest["provenance"]["checkpoint_scope_admitted"]
        manifest_path.write_text(
            json.dumps(request_manifest, indent=2) + "\n", encoding="utf-8")
        # A post-pack oracle edit a stamped request would refuse on.
        self.commit_checkpoint(checkpoint_script(V2_MARKER),
                               message="planner edits the oracle post-pack")

        tarball = self.build_response_tarball(sid, name="stampless")
        merged = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            merged.returncode, 0,
            msg=f"stdout:\n{merged.stdout}\nstderr:\n{merged.stderr}")

        log = self.session_log(sid)
        self.assertIn(STAMPLESS_PHRASE, log,
                      msg="the skipped verification is logged, never silent")
        stamp = self.telemetry_record(sid)["attempts"][-1]["checkpoint"]
        self.assertIsNone(stamp["stamp_matched"])
        self.assertIs(stamp["configured"], True,
                      msg="the checkpoint still RAN — only the "
                          "verification was skipped")


class HandoffBlindnessGateTest(unittest.TestCase):
    """The handoff-side covering refusal (v0.3.33, BALE.md §11 row 30):
    the same gate implementation as pack's, run pre-sid against the
    handoff's reading-plan scope, with the mirroring per-invocation
    admission flag stamping through the shared provenance builder.

    Fixture flow per test: pack an ordinary in-scope session, apply a
    bailout response whose handoff.md reading plan cites a chosen file
    set (closing the session — handoff refuses while any is open), then
    run `bale handoff` against the bailout tarball."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-cpho-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def configure_checkpoint(self) -> None:
        (self.repo / "bale.toml").write_text(
            f"[validation]\nbase = \"{CHECKPOINT_PATH}\"\n",
            encoding="utf-8")

    def commit_checkpoint(self) -> str:
        """Commit the checkpoint script; return the committed bytes'
        sha256 (the tip identity the provenance stamp must carry)."""
        p = self.repo / CHECKPOINT_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        data = checkpoint_script(V1_MARKER).encode("utf-8")
        p.write_bytes(data)
        p.chmod(0o755)
        run_checked(["git", "add", CHECKPOINT_PATH],
                    cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "pin blind checkpoint"],
                    cwd=self.repo, env=self.genv)
        return hashlib.sha256(data).hexdigest()

    def packed_and_bailed_sid(self, *, reading_plan_paths) -> tuple[str, Path]:
        """Pack an ordinary session, apply a bailout whose reading plan
        cites `reading_plan_paths` (backtick-inline, the §5.7 shape the
        extractor parses; None omits the section entirely), and return
        (bailed_sid, bailout_tarball). The apply closes the session, so
        `bale handoff` can open the successor."""
        packed = run_bale(
            self.install,
            ["pack", "handoff blindness e2e goal: rewrite hello.txt",
             "--slug", "cp-ho", "--include", "hello.txt", "--no-readme"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            packed.returncode, 0,
            msg=f"stdout:\n{packed.stdout}\nstderr:\n{packed.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        sid = sids[0]

        nnn = sid[-3:]
        rdir = self.tmp / "bailout" / f"response-{nnn}"
        rdir.mkdir(parents=True)
        manifest = {
            "session_id": sid,
            "responds_to": sid,
            "corrects": None,
            "response_kind": "bailout",
            "summary": "bailout fixture: goal did not fit the budget",
            "changes": [],
            "deferred": [],
            "validation_will_run": [],
            "claims": {},
        }
        (rdir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        handoff_md = ("# Handoff\n\n## Original goal\n\n"
                      "handoff blindness e2e goal: rewrite hello.txt\n")
        if reading_plan_paths is not None:
            cites = "\n".join(
                f"- read `{p}` before building" for p in reading_plan_paths)
            handoff_md += ("\n## Reading plan for the next session\n\n"
                           f"{cites}\n")
        (rdir / "handoff.md").write_text(handoff_md, encoding="utf-8")
        diagnostics = {
            "session_id": sid,
            "bail_trigger": "mid-build-budget-panic",
            "bail_narrative": "fixture narrative: the change set outgrew "
                              "the estimate mid-build.",
            "context_loaded": [
                {"path": "hello.txt", "verdict": "necessary", "note": ""},
            ],
            "exploration_paths": [
                {"what": "sized the change set", "verdict": "productive",
                 "note": ""},
            ],
            "tool_calls_summary": {"bash": 3},
            "what_would_save_next_time": ["split the goal at the seam"],
        }
        (rdir / "diagnostics.json").write_text(
            json.dumps(diagnostics, indent=2) + "\n", encoding="utf-8")
        noop = "#!/usr/bin/env bash\n# no-op (test fixture)\nexit 0\n"
        (rdir / "apply.sh").write_text(noop, encoding="utf-8")
        (rdir / "validation.sh").write_text(noop, encoding="utf-8")
        tarball = self.tmp / "bailout" / f"response-{nnn}.tar.gz"
        with tarfile.open(tarball, "w:gz") as tf:
            tf.add(str(rdir), arcname=f"response-{nnn}")

        applied = run_bale(self.install, ["apply", str(tarball)],
                           cwd=self.repo, env=self.env)
        self.assertEqual(
            applied.returncode, 0,
            msg=f"stdout:\n{applied.stdout}\nstderr:\n{applied.stderr}")
        return sid, tarball

    def handoff(self, tarball: Path, *extra_args: str):
        return run_bale(self.install, ["handoff", str(tarball), *extra_args],
                        cwd=self.repo, env=self.env)

    def open_sids(self) -> list[str]:
        root = self.repo / ".bale" / "sessions"
        return [d.name for d in root.iterdir() if (d / "open").is_file()]

    def session_dirs(self) -> set[str]:
        root = self.repo / ".bale" / "sessions"
        return {d.name for d in root.iterdir() if d.is_dir()}

    def new_session_request_manifest(self, bailed_sid: str) -> dict:
        opens = self.open_sids()
        self.assertEqual(len(opens), 1)
        new_sid = opens[0]
        self.assertNotEqual(new_sid, bailed_sid)
        p = self.repo / ".bale" / "sessions" / new_sid / "manifest.json"
        return json.loads(p.read_text(encoding="utf-8"))

    # -- the E2Es --------------------------------------------------------

    def test_handoff_refuses_covering_reading_plan(self) -> None:
        """A reading plan citing the checkpoint path resolves to a
        covering scope: handoff refuses pre-sid — remedy text present,
        the flag named as successor, no new session state of any
        kind."""
        self.commit_checkpoint()
        self.configure_checkpoint()
        bailed_sid, tarball = self.packed_and_bailed_sid(
            reading_plan_paths=["hello.txt", CHECKPOINT_PATH])

        refused = self.handoff(tarball)
        self.assertNotEqual(refused.returncode, 0)
        combined = refused.stdout + refused.stderr
        self.assertIn(SCOPE_REFUSAL_PHRASE, combined)
        self.assertIn("--allow-checkpoint-in-scope", combined,
                      msg="the refusal names its override successor")
        # The caller-aware remedy sentence (v0.3.34): the handoff
        # refusal swaps only the narrowing remedy — a handoff's scope
        # is the reading plan's resolved cite set, so --include is not
        # its lever; the diagnosis and flag lines above stay byte-shared
        # with pack's.
        self.assertIn("re-bail with a reading plan that does not cite "
                      "the checkpoint", combined)
        self.assertNotIn("narrow this pack with --include paths",
                         combined)
        self.assertEqual(self.open_sids(), [],
                         msg="the refusal is pre-sid — no session opened")
        self.assertEqual(
            self.session_dirs(), {bailed_sid},
            msg="no new session directory may exist after the refusal")

    def test_handoff_flag_admits_and_stamps(self) -> None:
        """--allow-checkpoint-in-scope on handoff admits the covering
        reading-plan scope: the handoff succeeds, the FORCE: line lands,
        and the NEW request's provenance stamps
        checkpoint_scope_admitted: true beside the checkpoint stamp —
        through the same builder pack stamps through."""
        sha = self.commit_checkpoint()
        self.configure_checkpoint()
        bailed_sid, tarball = self.packed_and_bailed_sid(
            reading_plan_paths=["hello.txt", CHECKPOINT_PATH])

        admitted = self.handoff(tarball, "--allow-checkpoint-in-scope")
        self.assertEqual(
            admitted.returncode, 0,
            msg=f"stdout:\n{admitted.stdout}\nstderr:\n{admitted.stderr}")
        combined = admitted.stdout + admitted.stderr
        self.assertIn("FORCE:", combined)
        self.assertIn("--allow-checkpoint-in-scope", combined)
        provenance = self.new_session_request_manifest(bailed_sid)[
            "provenance"]
        self.assertIs(provenance["checkpoint_scope_admitted"], True)
        self.assertEqual(provenance["checkpoint"],
                         {"path": CHECKPOINT_PATH, "sha256": sha})

    def test_handoff_noncovering_plan_passes_and_stamps_false(self) -> None:
        """A reading plan that does not cover the checkpoint passes the
        gate without the flag — the pack-baseline mirror — and the new
        request stamps checkpoint_scope_admitted: false beside the
        checkpoint stamp."""
        sha = self.commit_checkpoint()
        self.configure_checkpoint()
        bailed_sid, tarball = self.packed_and_bailed_sid(
            reading_plan_paths=["hello.txt"])

        passed = self.handoff(tarball)
        self.assertEqual(
            passed.returncode, 0,
            msg=f"stdout:\n{passed.stdout}\nstderr:\n{passed.stderr}")
        provenance = self.new_session_request_manifest(bailed_sid)[
            "provenance"]
        self.assertIs(provenance["checkpoint_scope_admitted"], False)
        self.assertEqual(provenance["checkpoint"],
                         {"path": CHECKPOINT_PATH, "sha256": sha})

    def test_handoff_empty_plan_whole_tree_refuses(self) -> None:
        """A reading plan citing no files resolves to ["."] — the
        conservative whole-tree fallback — which covers any configured
        checkpoint: the handoff refuses the same way a default
        whole-tree pack does, and the flag remains the admission
        path."""
        self.commit_checkpoint()
        self.configure_checkpoint()
        bailed_sid, tarball = self.packed_and_bailed_sid(
            reading_plan_paths=None)

        refused = self.handoff(tarball)
        self.assertNotEqual(refused.returncode, 0)
        combined = refused.stdout + refused.stderr
        self.assertIn(SCOPE_REFUSAL_PHRASE, combined)
        self.assertEqual(self.open_sids(), [],
                         msg="the refusal is pre-sid — no session opened")
        self.assertEqual(self.session_dirs(), {bailed_sid})


if __name__ == "__main__":
    unittest.main(verbosity=2)
