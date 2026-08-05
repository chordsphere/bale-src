#!/usr/bin/env python3
"""Hermetic E2E for the required-check superset gate (board 6 session B).

Covers the D8 session-B assertion set against the documented contract
(BALE.md §8.1 step 15, §11 row 26, §5.4, §8.9; ADR-0002 oracle doctrine
— observable state, never golden comparisons):

- refusal on a missing required name: exit 1, the session stays open,
  the refusal is pre-staging (no bale/<sid> branch, no per-sid staging
  directory), both sets render, and `--json` emits the dispatchable
  `required-check-refused` outcome with the `required_checks` detail;
- vacuous passes: an unconfigured project's apply is unaffected; a
  clarification response under a configured required set passes the
  gate vacuously (empty `changes[]`); a read-only session's changes hit
  the step-14 drift gate first, never step 15;
- `--dry-run` predicts the refusal with no telemetry (a dry-run has no
  outcome);
- the override admits exactly the named names (a partial override still
  refuses on the rest), an unused name logs a no-effect line, every
  effective use logs a FORCE: line, and `bale retry` re-states the
  override rather than inheriting it;
- telemetry: the refusal attempt records outcome
  `required-check-refused` with `validation: null`, and the attempt
  that proceeds under an override stamps
  `attempts[].required_check_overrides`;
- stats in-flight membership (the D3 coordination rider): a session
  whose latest outcome is the new refusal counts as in-flight, never
  into the closure mix;
- the `[validation] required` config trio: the project wizard walks the
  key and preserves it across an Enter-through re-run; the global
  wizard never gains it (project-layer only, disposition 1);
- the sanctioned session-A rider: `bale apply --dry-run` predicts the
  dangling-checkpoint refusal by resolving the target base read-only,
  while a committed checkpoint and an unconfigured project dry-run
  clean.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_required_check_gate.py

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

# Sentinels for the surfaces this file pins.
REFUSED_STATUS = "[REQUIRED-CHECK-REFUSED]"
DRIFT_STATUS = "[SCOPE-DRIFT-REFUSED]"
REJECT_LINE = "required checks missing (BALE.md \u00a711 row 26)"
NO_EFFECT_LINE = ("--allow-missing-required-check named check(s) with no "
                  "matching missing required check")
FORCE_LINE = ("missing required check(s) admitted by "
              "--allow-missing-required-check")
DANGLING_PHRASE = "blind checkpoint missing at the base tree"
DRY_RUN_ROW = "a real apply would refuse the same way"

NEW_CONTENT = "hello from the required-check fixture response\n"


class RequiredCheckGateE2ETest(unittest.TestCase):
    """The board 6 session B contract, driven through real pack/apply."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-reqcheck-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def configure_required(self, names: list[str]) -> None:
        """Write bale.toml naming the required set (hand-edit is valid —
        the wizard is canonical, not exclusive; the strict accessor is
        what apply reads through)."""
        rendered = "[" + ", ".join(json.dumps(n) for n in names) + "]"
        (self.repo / "bale.toml").write_text(
            f"[validation]\nrequired = {rendered}\n", encoding="utf-8")

    def packed_sid(self, *, read_only: bool = False) -> str:
        args = ["pack", "required-check e2e goal: rewrite hello.txt",
                "--slug", "req-check", "--include", "hello.txt",
                "--no-readme"]
        if read_only:
            args.append("--read-only")
        result = run_bale(self.install, args, cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        return sids[0]

    def build_response_tarball(self, sid: str, *, name: str,
                               validation_will_run: list[str],
                               kind: str = "normal") -> Path:
        """A valid response modifying hello.txt (in scope) whose
        manifest declares `validation_will_run`; its validation.sh
        prints a PASS line per declared check and exits 0. Sizes and
        hashes computed, never transcribed. `kind="clarification"`
        builds the empty-change-surface sibling instead (BALE.md §11
        row 25's shape), for the vacuous-pass case."""
        nnn = sid[-3:]
        rdir = self.tmp / name / f"response-{nnn}"
        rdir.mkdir(parents=True)
        if kind == "clarification":
            manifest = {
                "session_id": sid,
                "responds_to": sid,
                "corrects": None,
                "response_kind": "clarification",
                "summary": "required-check fixture: blocked on a question",
                "changes": [],
                "deferred": [],
                "validation_will_run": [],
                "claims": {},
                "questions": [{
                    "question": "fixture question?",
                    "context": "fixture context",
                    "default_assumption": "fixture assumption",
                    "why_blocked": "fixture blocker",
                }],
            }
            (rdir / "validation.sh").write_text(
                "#!/usr/bin/env bash\n# no-op (clarification)\nexit 0\n",
                encoding="utf-8")
        else:
            (rdir / "files").mkdir()
            data = NEW_CONTENT.encode("utf-8")
            (rdir / "files" / "hello.txt").write_bytes(data)
            manifest = {
                "session_id": sid,
                "responds_to": sid,
                "corrects": None,
                "response_kind": "normal",
                "summary": "required-check fixture: rewrite hello.txt",
                "changes": [{
                    "path": "hello.txt",
                    "action": "modified",
                    "reason": "the goal's rewrite; the fixture's "
                              "in-scope payload change",
                    "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }],
                "deferred": [],
                "validation_will_run": validation_will_run,
                "claims": {},
            }
            check_lines = "".join(
                f"echo \"[PASS] {c}\"\n" for c in validation_will_run)
            (rdir / "validation.sh").write_text(
                "#!/usr/bin/env bash\n" + check_lines + "exit 0\n",
                encoding="utf-8")
        (rdir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        (rdir / "apply.sh").write_text(
            "#!/usr/bin/env bash\n# no-op (test fixture)\nexit 0\n",
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

    def assert_pre_staging(self, sid: str) -> None:
        """The refusal's pre-staging contract: session open, no
        bale/<sid> branch, no per-sid staging directory."""
        self.assertTrue(
            (self.repo / ".bale" / "sessions" / sid / "open").is_file(),
            msg="the session must stay open across the refusal")
        branches = subprocess.run(
            ["git", "branch", "--list", f"bale/{sid}"],
            cwd=self.repo, env=self.genv, capture_output=True, text=True,
        ).stdout.strip()
        self.assertEqual(branches, "",
                         msg="a pre-staging refusal creates no branch")
        self.assertFalse(
            (self.repo / ".bale" / "staging" / sid).exists(),
            msg="a pre-staging refusal stages nothing")

    # -- the refusal -----------------------------------------------------

    def test_refusal_names_both_sets_and_is_pre_staging(self) -> None:
        """A missing required name refuses with exit 1: both sets
        render, the reject line cites the row, the session stays open
        with no staging side effects, and the telemetry attempt records
        the distinct outcome with validation null."""
        self.configure_required(["tests", "lint"])
        sid = self.packed_sid()
        tarball = self.build_response_tarball(
            sid, name="refuse", validation_will_run=["tests"])

        refused = run_bale(self.install, ["apply", str(tarball)],
                           cwd=self.repo, env=self.env)
        self.assertEqual(
            refused.returncode, 1,
            msg=f"stdout:\n{refused.stdout}\nstderr:\n{refused.stderr}")
        self.assertIn(REFUSED_STATUS, refused.stdout)
        self.assertIn("lint", refused.stdout,
                      msg="the missing name must render")
        self.assertIn("[validation] required, project layer",
                      refused.stdout,
                      msg="the required set renders with its layer")
        self.assertIn("tests", refused.stdout,
                      msg="the declared list renders so a near-miss "
                          "is visible")
        self.assert_pre_staging(sid)
        self.assertIn(REJECT_LINE, self.session_log(sid))

        record = self.telemetry_record(sid)
        self.assertEqual(record["outcome"], "required-check-refused")
        attempt = record["attempts"][-1]
        self.assertEqual(attempt["outcome"], "required-check-refused")
        self.assertEqual(attempt["command"], "apply")
        self.assertIsNone(attempt["validation"],
                          msg="nothing ran — validation is null on the "
                              "refusal attempt")
        self.assertEqual(attempt["required_check_overrides"], [])

    def test_json_outcome_is_dispatchable(self) -> None:
        """`--json` emits the one-line report with the new outcome and
        the required_checks detail object on the exit-1 path."""
        self.configure_required(["tests"])
        sid = self.packed_sid()
        tarball = self.build_response_tarball(
            sid, name="jsonref", validation_will_run=[])

        refused = run_bale(self.install,
                           ["apply", str(tarball), "--json"],
                           cwd=self.repo, env=self.env)
        self.assertEqual(refused.returncode, 1)
        lines = [ln for ln in refused.stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1,
                         msg="json stream discipline: stdout carries "
                             "exactly the one report line\n"
                             f"stdout:\n{refused.stdout}")
        payload = json.loads(lines[0])
        self.assertEqual(payload["outcome"], "required-check-refused")
        self.assertEqual(payload["sid"], sid)
        self.assertIsNone(payload["verdict"])
        self.assertEqual(payload["required_checks"], {
            "missing": ["tests"],
            "required": ["tests"],
            "declared": [],
            "overridden": [],
        })

    # -- vacuous passes --------------------------------------------------

    def test_unconfigured_project_is_unaffected(self) -> None:
        """No [validation] required set: the gate is entirely outside
        the apply's blast radius and the fixture merges."""
        sid = self.packed_sid()
        tarball = self.build_response_tarball(
            sid, name="uncfg", validation_will_run=["fixture check"])
        merged = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            merged.returncode, 0,
            msg=f"stdout:\n{merged.stdout}\nstderr:\n{merged.stderr}")
        self.assertNotIn(REFUSED_STATUS, merged.stdout)

    def test_clarification_passes_vacuously(self) -> None:
        """A clarification's empty changes[] never trips the gate even
        under a required set the manifest does not declare."""
        self.configure_required(["tests"])
        sid = self.packed_sid()
        tarball = self.build_response_tarball(
            sid, name="clar", validation_will_run=[],
            kind="clarification")
        result = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertNotIn(REFUSED_STATUS, result.stdout)
        self.assertTrue(
            (self.repo / ".bale" / "sessions" / sid / "open").is_file(),
            msg="a clarification suspends; the session stays open")

    def test_read_only_session_hits_drift_gate_first(self) -> None:
        """A read-only session's changes are refused by step 14 before
        step 15 can engage — the documented ordering."""
        self.configure_required(["tests"])
        sid = self.packed_sid(read_only=True)
        tarball = self.build_response_tarball(
            sid, name="ro", validation_will_run=[])
        refused = run_bale(self.install, ["apply", str(tarball)],
                           cwd=self.repo, env=self.env)
        self.assertEqual(refused.returncode, 1)
        self.assertIn(DRIFT_STATUS, refused.stdout)
        self.assertNotIn(REFUSED_STATUS, refused.stdout,
                         msg="step 14 refuses first; step 15 is never "
                             "reached for a read-only session's changes")

    # -- dry-run ---------------------------------------------------------

    def test_dry_run_predicts_with_no_telemetry(self) -> None:
        """--dry-run reports the same refusal (exit 1, dry-run rows)
        and writes no telemetry record — a dry-run has no outcome."""
        self.configure_required(["tests"])
        sid = self.packed_sid()
        tarball = self.build_response_tarball(
            sid, name="dry", validation_will_run=[])
        dry = run_bale(self.install,
                       ["apply", str(tarball), "--dry-run"],
                       cwd=self.repo, env=self.env)
        self.assertEqual(dry.returncode, 1)
        self.assertIn(REFUSED_STATUS, dry.stdout)
        self.assertIn(DRY_RUN_ROW, dry.stdout)
        self.assertIn("not recorded (dry-run has no outcome)", dry.stdout)
        self.assertFalse(
            (self.repo / "claude" / "telemetry" / f"{sid}.json").exists(),
            msg="a dry-run refusal records no telemetry")
        self.assert_pre_staging(sid)

    # -- the override ----------------------------------------------------

    def test_partial_override_admits_named_and_refuses_rest(self) -> None:
        """The override's unit is the name: admitting one of two
        missing names still refuses on the other, and the refusal
        attempt stamps the partial admission."""
        self.configure_required(["tests", "lint"])
        sid = self.packed_sid()
        tarball = self.build_response_tarball(
            sid, name="partial", validation_will_run=[])
        refused = run_bale(
            self.install,
            ["apply", str(tarball),
             "--allow-missing-required-check", "tests"],
            cwd=self.repo, env=self.env)
        self.assertEqual(refused.returncode, 1)
        self.assertIn(REFUSED_STATUS, refused.stdout)
        self.assertIn("admitted by flag", refused.stdout)
        attempt = self.telemetry_record(sid)["attempts"][-1]
        self.assertEqual(attempt["outcome"], "required-check-refused")
        self.assertEqual(attempt["required_check_overrides"], ["tests"])

    def test_full_override_proceeds_forces_and_stamps(self) -> None:
        """Admitting every missing name proceeds to the merge: a FORCE:
        line lands in the session log and the applied attempt carries
        required_check_overrides; an extra unused name logs its
        no-effect line."""
        self.configure_required(["tests", "lint"])
        sid = self.packed_sid()
        tarball = self.build_response_tarball(
            sid, name="full", validation_will_run=["lint"])
        merged = run_bale(
            self.install,
            ["apply", str(tarball),
             "--allow-missing-required-check", "tests",
             "--allow-missing-required-check", "lint"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            merged.returncode, 0,
            msg=f"stdout:\n{merged.stdout}\nstderr:\n{merged.stderr}")
        log = self.session_log(sid)
        self.assertIn(FORCE_LINE, log)
        self.assertIn(NO_EFFECT_LINE, log,
                      msg="'lint' is declared, not missing — the unused "
                          "name must log its no-effect line")
        attempt = self.telemetry_record(sid)["attempts"][-1]
        self.assertEqual(attempt["outcome"], "applied")
        self.assertEqual(attempt["required_check_overrides"], ["tests"])

    def test_retry_restates_the_override(self) -> None:
        """The override is per-invocation on retry exactly as on apply:
        a retry that omits it refuses like an un-overridden apply, and
        a retry that states it proceeds."""
        self.configure_required(["tests"])
        sid = self.packed_sid()
        tarball = self.build_response_tarball(
            sid, name="retry", validation_will_run=[])
        first = run_bale(self.install, ["apply", str(tarball)],
                         cwd=self.repo, env=self.env)
        self.assertEqual(first.returncode, 1)
        self.assertIn(REFUSED_STATUS, first.stdout)

        bare_retry = run_bale(self.install, ["retry", str(tarball)],
                              cwd=self.repo, env=self.env)
        self.assertEqual(bare_retry.returncode, 1,
                         msg="the override is never carried forward")
        self.assertIn(REFUSED_STATUS, bare_retry.stdout)
        self.assertEqual(
            self.telemetry_record(sid)["attempts"][-1]["command"], "retry")

        stated = run_bale(
            self.install,
            ["retry", str(tarball),
             "--allow-missing-required-check", "tests"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            stated.returncode, 0,
            msg=f"stdout:\n{stated.stdout}\nstderr:\n{stated.stderr}")
        attempt = self.telemetry_record(sid)["attempts"][-1]
        self.assertEqual(attempt["outcome"], "applied")
        self.assertEqual(attempt["command"], "retry")
        self.assertEqual(attempt["required_check_overrides"], ["tests"])

    # -- stats membership (the D3 coordination rider) --------------------

    def test_stats_counts_the_refusal_as_in_flight(self) -> None:
        """A session whose latest outcome is required-check-refused is
        in-flight to `bale stats`, never misclassed into the closure
        mix. The record is the real one the refusal just wrote."""
        self.configure_required(["tests"])
        sid = self.packed_sid()
        tarball = self.build_response_tarball(
            sid, name="stats", validation_will_run=[])
        refused = run_bale(self.install, ["apply", str(tarball)],
                           cwd=self.repo, env=self.env)
        self.assertEqual(refused.returncode, 1)
        self.assertEqual(
            self.telemetry_record(sid)["outcome"], "required-check-refused")

        result = run_bale(self.install, ["stats", "--json"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 0,
                         msg=f"stdout:\n{result.stdout}\n"
                             f"stderr:\n{result.stderr}")
        lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1)
        stats = json.loads(lines[0])
        self.assertEqual(stats["corpus"]["sessions"], 1)
        self.assertEqual(stats["corpus"]["in_flight_sessions"], 1,
                         msg="the new refusal outcome is in-flight "
                             "membership, not a closure")
        self.assertNotIn(
            "unrecognized envelope outcome", result.stderr,
            msg="the outcome is known vocabulary, not the fallback path")

    # -- the config trio's wizard halves ---------------------------------

    def test_project_wizard_walks_and_preserves_required(self) -> None:
        """Project mode prompts for validation.required, and an
        already-set list survives an Enter-through re-run — the
        renderer-preservation precedent validation.base set."""
        self.configure_required(["tests", "lint"])
        code, output = run_bale_pty(
            self.install, ["config", "init"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("validation.required", output,
                      msg="the project wizard walks the key — the "
                          "discoverable-surface contract")
        rendered = (self.repo / "bale.toml").read_text(encoding="utf-8")
        self.assertIn("[validation]", rendered)
        self.assertIn('required = ["tests", "lint"]', rendered,
                      msg="Enter-through re-runs preserve the required "
                          "set")

    def test_global_wizard_never_walks_required(self) -> None:
        """`bale config init --global` does not gain the prompt: the
        key is project-layer only (ratified disposition 1)."""
        code, output = run_bale_pty(
            self.install, ["config", "init", "--global"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertNotIn("validation.required", output,
                         msg="the global wizard must not offer a "
                             "project-only key")

    # -- the sanctioned rider: dry-run dangling prediction ---------------

    def test_dry_run_predicts_dangling_checkpoint(self) -> None:
        """A dry-run on a project whose [validation] base names an
        uncommitted path refuses with the dangling message — the same
        refusal a real apply would raise past the dry-run exit.

        The dangling key is written AFTER the pack (v0.3.28, session C):
        pack itself now refuses a dangling checkpoint at its own
        pre-flight, so the state this rider predicts — apply-side
        dangling — arises only when the config broke between pack and
        apply, which is exactly the sequence built here."""
        sid = self.packed_sid()
        (self.repo / "bale.toml").write_text(
            "[validation]\nbase = \"scripts/validation.base.sh\"\n",
            encoding="utf-8")
        tarball = self.build_response_tarball(
            sid, name="dangdry", validation_will_run=["fixture check"])
        dry = run_bale(self.install,
                       ["apply", str(tarball), "--dry-run"],
                       cwd=self.repo, env=self.env)
        self.assertEqual(dry.returncode, 1,
                         msg=f"stdout:\n{dry.stdout}\n"
                             f"stderr:\n{dry.stderr}")
        combined = dry.stdout + dry.stderr
        self.assertIn(DANGLING_PHRASE, combined)
        self.assertIn("a real apply would refuse the same way", combined)

    def test_dry_run_clean_with_committed_checkpoint(self) -> None:
        """The prediction does not false-positive: a committed
        checkpoint's dry-run reports the plan and exits 0."""
        cp = self.repo / "scripts" / "validation.base.sh"
        cp.parent.mkdir(parents=True, exist_ok=True)
        cp.write_text("#!/usr/bin/env bash\necho \"[PASS] cp\"\nexit 0\n",
                      encoding="utf-8")
        cp.chmod(0o755)
        run_checked(["git", "add", "scripts/validation.base.sh"],
                    cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "pin checkpoint"],
                    cwd=self.repo, env=self.genv)
        (self.repo / "bale.toml").write_text(
            "[validation]\nbase = \"scripts/validation.base.sh\"\n",
            encoding="utf-8")
        sid = self.packed_sid()
        tarball = self.build_response_tarball(
            sid, name="dryok", validation_will_run=["fixture check"])
        dry = run_bale(self.install,
                       ["apply", str(tarball), "--dry-run"],
                       cwd=self.repo, env=self.env)
        self.assertEqual(
            dry.returncode, 0,
            msg=f"stdout:\n{dry.stdout}\nstderr:\n{dry.stderr}")
        self.assertNotIn(DANGLING_PHRASE, dry.stdout + dry.stderr)

    def test_dry_run_unconfigured_is_unchanged(self) -> None:
        """No checkpoint configured: the dry-run neither resolves the
        base nor refuses — today's behavior."""
        sid = self.packed_sid()
        tarball = self.build_response_tarball(
            sid, name="dryuncfg", validation_will_run=["fixture check"])
        dry = run_bale(self.install,
                       ["apply", str(tarball), "--dry-run"],
                       cwd=self.repo, env=self.env)
        self.assertEqual(dry.returncode, 0,
                         msg=f"stdout:\n{dry.stdout}\n"
                             f"stderr:\n{dry.stderr}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
