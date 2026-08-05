#!/usr/bin/env python3
"""Hermetic E2E for the blind checkpoint (board 6 session A).

Covers the D8 session-A assertion set against the documented contract
(BALE.md §8.5/§8.6/§8.9; ADR-0002 oracle doctrine — observable state,
never golden comparisons):

- the executed checkpoint is the BASE TREE's bytes: a response that
  modifies the checkpoint is graded against the pre-edit version, and
  the assertion is on *executed output* in the session log, not on the
  materialized file's presence or content — so a mode-stripped,
  never-run checkpoint fails the test (ratified disposition 5);
- both scripts always run: a checkpoint FAIL still runs the worker and
  a worker FAIL still ran the checkpoint (both banded sections in the
  log);
- PASS requires both exit codes 0; any other combination is HOLD, with
  per-source attribution in the walkthrough — including the distinct
  "the planner's checkpoint itself errored" phrasing on checkpoint
  exit 2;
- configured-but-dangling refuses loudly before staging (session stays
  open, no bale/<sid> branch);
- absent config is today's behavior: no checkpoint bands in the log,
  and the telemetry stamp is the known-zero {"configured": false};
- the telemetry stamp records the executed base-tree bytes' sha256 —
  asserted equal to a hash computed from the committed blob, never
  from a working-tree or staged copy.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_blind_checkpoint.py

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
    run_bale_pty,
    run_checked,
)

CHECKPOINT_PATH = "scripts/validation.base.sh"

# Sentinels for the surfaces this file pins.
CP_BAND_PREFIX = "=== blind checkpoint ("
WORKER_BAND = "=== worker validation.sh ==="
V1_MARKER = "CHECKPOINT-MARKER-V1"
V2_MARKER = "CHECKPOINT-MARKER-V2"
ERRORED_PHRASE = "the planner's checkpoint itself errored"
DANGLING_PHRASE = "blind checkpoint missing at the base tree"

NEW_CONTENT = "hello from the checkpoint fixture response\n"


def checkpoint_script(marker: str, exit_code: int) -> str:
    """A committed-checkpoint fixture honoring TARBALL.md §7.2/§7.5."""
    verdict = "PASS" if exit_code == 0 else "FAIL"
    return (
        "#!/usr/bin/env bash\n"
        f"echo \"[{verdict}] {marker}\"\n"
        f"exit {exit_code}\n"
    )


class BlindCheckpointE2ETest(unittest.TestCase):
    """The board 6 session A contract, driven through real pack/apply."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-blindcp-")
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
        what apply reads through)."""
        (self.repo / "bale.toml").write_text(
            f"[validation]\nbase = \"{path}\"\n", encoding="utf-8")

    def commit_checkpoint(self, body: str) -> str:
        """Commit the checkpoint script; return the committed blob's
        sha256 (computed from the bytes handed to git — the base-tree
        identity the stamp must match)."""
        p = self.repo / CHECKPOINT_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        data = body.encode("utf-8")
        p.write_bytes(data)
        p.chmod(0o755)
        run_checked(["git", "add", CHECKPOINT_PATH],
                    cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "pin blind checkpoint"],
                    cwd=self.repo, env=self.genv)
        return hashlib.sha256(data).hexdigest()

    def packed_sid(self, *, include_checkpoint: bool = False) -> str:
        includes = ["--include", "hello.txt"]
        if include_checkpoint:
            # A checkpoint-covering scope needs the session-C admission
            # flag (v0.3.28): pack's blindness gate refuses it otherwise.
            # This fixture is exactly the deliberate delegation case the
            # override exists for — the in-flight-tampering test needs
            # the checkpoint edit to be IN scope so the drift gate does
            # not refuse it first.
            includes += ["--include", CHECKPOINT_PATH,
                         "--allow-checkpoint-in-scope"]
        result = run_bale(
            self.install,
            ["pack", "blind checkpoint e2e goal: rewrite hello.txt",
             "--slug", "blind-cp", *includes, "--no-readme"],
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
                               validation_exit: int,
                               modify_checkpoint_to: str = None) -> Path:
        """A valid normal response modifying hello.txt (in scope), whose
        validation.sh exits `validation_exit`. When
        `modify_checkpoint_to` is given, the response ALSO ships a new
        checkpoint body at the configured path — the in-flight-tampering
        fixture the base-tree rule must render inert. Sizes and hashes
        computed, never transcribed."""
        nnn = sid[-3:]
        rdir = self.tmp / name / f"response-{nnn}"
        (rdir / "files").mkdir(parents=True)
        data = NEW_CONTENT.encode("utf-8")
        (rdir / "files" / "hello.txt").write_bytes(data)
        changes = [
            {
                "path": "hello.txt",
                "action": "modified",
                "reason": "the goal's rewrite; the fixture's in-scope "
                          "payload change",
                "size_bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(),
            }
        ]
        if modify_checkpoint_to is not None:
            cp_data = modify_checkpoint_to.encode("utf-8")
            cp_dst = rdir / "files" / CHECKPOINT_PATH
            cp_dst.parent.mkdir(parents=True, exist_ok=True)
            cp_dst.write_bytes(cp_data)
            changes.append({
                "path": CHECKPOINT_PATH,
                "action": "modified",
                "reason": "in-flight checkpoint edit — the base-tree "
                          "execution rule must grade this response "
                          "against the pre-edit oracle",
                "size_bytes": len(cp_data),
                "sha256": hashlib.sha256(cp_data).hexdigest(),
            })
        manifest = {
            "session_id": sid,
            "responds_to": sid,
            "corrects": None,
            "response_kind": "normal",
            "summary": "blind checkpoint fixture: rewrite hello.txt",
            "changes": changes,
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

    # -- the E2Es --------------------------------------------------------

    def test_base_tree_bytes_run_and_stamp_records_their_hash(self) -> None:
        """A response that edits the checkpoint is graded against the
        committed (pre-edit) oracle — the assertion is on EXECUTED
        output, so a mode-stripped or never-run checkpoint fails here —
        and the telemetry stamp records the base-tree bytes' hash."""
        v1_body = checkpoint_script(V1_MARKER, 0)
        v1_sha = self.commit_checkpoint(v1_body)
        self.configure_checkpoint()
        sid = self.packed_sid(include_checkpoint=True)

        tarball = self.build_response_tarball(
            sid, name="tamper", validation_exit=0,
            modify_checkpoint_to=checkpoint_script(V2_MARKER, 1))
        merged = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            merged.returncode, 0,
            msg=f"stdout:\n{merged.stdout}\nstderr:\n{merged.stderr}")
        self.assertIn("[PASS]", merged.stdout)

        log = self.session_log(sid)
        self.assertIn(V1_MARKER, log,
                      msg="the committed (base-tree) checkpoint's output "
                          "must be what ran")
        self.assertNotIn(V2_MARKER, log,
                         msg="the response's staged checkpoint edit must "
                             "be inert — its marker never executes")
        self.assertIn(CP_BAND_PREFIX, log)
        self.assertIn(WORKER_BAND, log)

        record = self.telemetry_record(sid)
        stamp = record["attempts"][-1]["checkpoint"]
        self.assertEqual(stamp["configured"], True)
        self.assertEqual(stamp["state"], "PASS")
        self.assertEqual(stamp["exit_code"], 0)
        self.assertEqual(stamp["script"]["path"], CHECKPOINT_PATH)
        self.assertEqual(
            stamp["script"]["sha256"], v1_sha,
            msg="the stamp hashes the EXECUTED base-tree bytes")
        self.assertIs(stamp["stamp_matched"], True,
                      msg="the pack-time provenance stamp exists since "
                          "v0.3.28 (session C) and the oracle did not "
                          "change between pack and apply — the in-flight "
                          "edit is staged, never committed, so the "
                          "base-tree bytes still match the stamp")

    def test_checkpoint_fail_holds_and_worker_still_runs(self) -> None:
        """PASS requires both: checkpoint FAIL beside worker PASS is a
        HOLD, attributed per source, and the worker's run is not
        suppressed (both banded sections, worker check line present)."""
        self.commit_checkpoint(checkpoint_script("cp-fails", 1))
        self.configure_checkpoint()
        sid = self.packed_sid()

        tarball = self.build_response_tarball(sid, name="cpfail",
                                              validation_exit=0)
        held = run_bale(self.install, ["apply", str(tarball)],
                        cwd=self.repo, env=self.env)
        self.assertEqual(
            held.returncode, 1,
            msg=f"stdout:\n{held.stdout}\nstderr:\n{held.stderr}")
        self.assertIn("[HOLD]", held.stdout)
        self.assertIn("checkpoint: HOLD (exit 1)", held.stdout)
        self.assertIn("worker validation: PASS", held.stdout)

        log = self.session_log(sid)
        self.assertIn(CP_BAND_PREFIX, log)
        self.assertIn(WORKER_BAND, log)
        self.assertIn("[PASS] fixture check", log,
                      msg="the worker's script must have run despite the "
                          "checkpoint failure")

        record = self.telemetry_record(sid)
        attempt = record["attempts"][-1]
        self.assertEqual(attempt["outcome"], "held")
        self.assertEqual(attempt["validation"]["state"], "HOLD")
        self.assertEqual(attempt["validation"]["exit_code"], 0,
                         msg="the worker's own exit code stays 0 — the "
                             "HOLD is the checkpoint's")
        self.assertEqual(attempt["checkpoint"]["state"], "HOLD")
        self.assertEqual(attempt["checkpoint"]["exit_code"], 1)

    def test_worker_fail_still_ran_checkpoint(self) -> None:
        """The converse suppression is also forbidden: a worker FAIL's
        log still carries the checkpoint's banded run, and the
        walkthrough attributes both states."""
        self.commit_checkpoint(checkpoint_script("cp-passes", 0))
        self.configure_checkpoint()
        sid = self.packed_sid()

        tarball = self.build_response_tarball(sid, name="wkfail",
                                              validation_exit=1)
        held = run_bale(self.install, ["apply", str(tarball)],
                        cwd=self.repo, env=self.env)
        self.assertEqual(held.returncode, 1)
        self.assertIn("checkpoint: PASS", held.stdout)
        self.assertIn("worker validation: HOLD (exit 1)", held.stdout)

        log = self.session_log(sid)
        self.assertIn(CP_BAND_PREFIX, log)
        self.assertIn("cp-passes", log,
                      msg="the checkpoint ran before the worker failed")

    def test_checkpoint_error_gets_distinct_phrasing(self) -> None:
        """Checkpoint exit 2 is 'the planner's checkpoint itself
        errored' — the remedy differs from a worker failure."""
        self.commit_checkpoint(checkpoint_script("cp-errors", 2))
        self.configure_checkpoint()
        sid = self.packed_sid()

        tarball = self.build_response_tarball(sid, name="cperr",
                                              validation_exit=0)
        held = run_bale(self.install, ["apply", str(tarball)],
                        cwd=self.repo, env=self.env)
        self.assertEqual(held.returncode, 1)
        self.assertIn(ERRORED_PHRASE, held.stdout)

        record = self.telemetry_record(sid)
        attempt = record["attempts"][-1]
        self.assertEqual(attempt["checkpoint"]["exit_code"], 2)
        self.assertEqual(attempt["checkpoint"]["state"], "HOLD")

    def test_dangling_config_refuses_before_staging(self) -> None:
        """Config naming a checkpoint absent at the base tree is a loud
        refusal: non-zero exit, remedy text, session open, no bale
        branch (the refusal is pre-staging, pre-branch).

        The dangling key is written AFTER the pack (v0.3.28, session C):
        pack itself now refuses a dangling checkpoint at its own
        pre-flight — the D1 rule caught at request-build time — so the
        apply-side refusal this test pins arises only when the config
        broke between pack and apply, which is the sequence built
        here."""
        sid = self.packed_sid()
        self.configure_checkpoint("scripts/never-committed.sh")

        tarball = self.build_response_tarball(sid, name="dangling",
                                              validation_exit=0)
        refused = run_bale(self.install, ["apply", str(tarball)],
                           cwd=self.repo, env=self.env)
        self.assertNotEqual(refused.returncode, 0)
        combined = refused.stdout + refused.stderr
        self.assertIn(DANGLING_PHRASE, combined)
        self.assertIn("committed-is-ratified", combined)

        self.assertTrue(
            (self.repo / ".bale" / "sessions" / sid / "open").is_file(),
            msg="the refusal leaves the session open")
        rp = subprocess.run(
            ["git", "rev-parse", "--verify", f"refs/heads/bale/{sid}"],
            cwd=self.repo, env=self.genv, capture_output=True, text=True)
        self.assertNotEqual(
            rp.returncode, 0,
            msg="no bale/<sid> branch may exist after the refusal — it "
                "must fire before branch creation")

    def test_absent_config_is_known_zero(self) -> None:
        """No [validation] config: no checkpoint bands in the log
        (today's behavior), and the validated attempt's stamp is the
        known-zero {"configured": false} — post-epoch key presence
        distinguishes it from pre-epoch records."""
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="absent",
                                              validation_exit=0)
        merged = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            merged.returncode, 0,
            msg=f"stdout:\n{merged.stdout}\nstderr:\n{merged.stderr}")

        log = self.session_log(sid)
        self.assertNotIn(CP_BAND_PREFIX, log)
        self.assertNotIn(WORKER_BAND, log,
                         msg="the worker band frames the checkpoint's "
                             "section; unconfigured logs stay "
                             "band-free (byte-compatible)")

        record = self.telemetry_record(sid)
        attempt = record["attempts"][-1]
        self.assertEqual(attempt["checkpoint"], {"configured": False})




class ValidationBaseWizardTest(unittest.TestCase):
    """The [validation] base trio's wizard half (disposition 1):
    project-only walk, and renderer preservation on re-run."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-cpwiz-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_project_wizard_walks_and_preserves_the_key(self) -> None:
        """Project mode prompts for validation.base, and an
        already-set key survives an Enter-through re-run — the
        [staging]/[identity] renderer-preservation precedent, without
        which a wizard re-run would drop the pinned oracle."""
        (self.repo / "bale.toml").write_text(
            "[validation]\nbase = \"scripts/validation.base.sh\"\n",
            encoding="utf-8")
        code, output = run_bale_pty(
            self.install, ["config", "init"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("validation.base", output,
                      msg="the project wizard walks the key — the "
                          "discoverable-surface contract")
        rendered = (self.repo / "bale.toml").read_text(encoding="utf-8")
        self.assertIn("[validation]", rendered)
        self.assertIn('base = "scripts/validation.base.sh"', rendered,
                      msg="Enter-through re-runs preserve the pinned "
                          "checkpoint path")

    def test_global_wizard_never_walks_the_key(self) -> None:
        """`bale config init --global` does not gain the prompt: the
        key is project-layer only (ratified disposition 1)."""
        code, output = run_bale_pty(
            self.install, ["config", "init", "--global"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertNotIn("validation.base", output,
                         msg="the global wizard must not offer a "
                             "project-only key")

if __name__ == "__main__":
    unittest.main(verbosity=2)
