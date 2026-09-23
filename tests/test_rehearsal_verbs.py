"""The rehearsal verbs (v0.4.45, board row 122): `bale open --check`,
`bale open --dry-run`, `bale pack --dry-run`.

End-to-end pins through real runs in the hermetic sandbox (ADR-0005, via
tests/harness.py), against the row's brief:

- `bale open --check <bundle>` verifies the bundle and runs every
  argv-only gate against the live tree — the include-naming checkpoint
  gate among them — then stops: exit 0 when every gate passes, the gate's
  own refusal text and a nonzero exit when one refuses; no oracle runs;
- `bale open --dry-run <bundle>` is --check plus the checkpoint dry-run
  exactly as an open runs it, verdict lines echoed: exit 0 on an oracle
  exit 0 or 1, nonzero (naming the exit) on 2 or on a gate refusal; its
  log lives in a temp directory outside the repository;
- `bale pack --dry-run <argv…>` runs the same gates for a hand-typed line;
- every spelling writes nothing. `RepoSnapshot` is the one assertion: every
  file under the repo (`.bale/` and the telemetry corpus included, `.git`
  excluded) by sha256, plus HEAD, every ref, and `git status --porcelain
  --ignored` — identical before and after, on a pass and on a refusal;
- a `--supersedes` parent stays open, its record untouched, whether the
  rehearsal predicts an accept (a pre-answered intent) or refuses (piped
  stdin with no intent — where the real pack refuses too);
- a second-desk bundle is rehearsed without a desk being recorded;
- and one behavior change on a real `bale open`, which now runs the full
  gate set before the oracle: a brief still carrying `TODO(brief)`
  refuses with no dry-run spent.

Dry-run tests pass --no-sandbox, the test_open_verb convention
(deterministic in every environment; the confined tier is that suite's).
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from harness import git_env, run_bale, run_bale_pty, run_checked
from test_open_verb import (
    CP_ERROR,
    CP_HOLD,
    CP_PASS,
    DRY_RUN_MARKER,
    _OpenVerbBase,
)


class RepoSnapshot:
    """Everything a rehearsal could write, captured comparably."""

    def __init__(self, repo: Path, env: dict) -> None:
        self.files = {}
        for p in sorted(repo.rglob("*")):
            rel = p.relative_to(repo)
            if rel.parts and rel.parts[0] == ".git":
                continue
            if p.is_symlink():
                self.files[str(rel)] = "symlink:" + str(p.readlink())
            elif p.is_dir():
                self.files[str(rel)] = "dir"
            else:
                self.files[str(rel)] = hashlib.sha256(
                    p.read_bytes()).hexdigest()

        def git(*args: str) -> str:
            return subprocess.run(["git", *args], cwd=repo, env=env,
                                  capture_output=True, text=True).stdout

        self.head = git("rev-parse", "HEAD")
        self.refs = git("for-each-ref")
        self.status = git("status", "--porcelain", "--ignored")

    def diff(self, other: "RepoSnapshot") -> list:
        out = []
        for k in sorted(set(self.files) | set(other.files)):
            if self.files.get(k) != other.files.get(k):
                out.append(f"{k}: {self.files.get(k)} -> {other.files.get(k)}")
        for name in ("head", "refs", "status"):
            if getattr(self, name) != getattr(other, name):
                out.append(f"git {name} changed")
        return out


class _RehearsalBase(_OpenVerbBase):
    """Snapshot helpers and a parent-session fixture."""

    def setUp(self) -> None:
        super().setUp()
        self.genv = git_env(self.home)

    def snap(self) -> RepoSnapshot:
        return RepoSnapshot(self.repo, self.genv)

    def assert_wrote_nothing(self, before: RepoSnapshot, result) -> None:
        changes = before.diff(self.snap())
        self.assertEqual(
            changes, [],
            msg=f"the rehearsal wrote into the repo: {changes}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

    def commit_all(self, message: str) -> None:
        run_checked(["git", "add", "-A"], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", message], cwd=self.repo,
                    env=self.genv)

    def pack(self, *argv: str):
        return run_bale(self.install, ["pack", *argv], cwd=self.repo,
                        env=self.env)

    def open_parent(self, *extra: str) -> str:
        """A real pack opening a parent session; returns its sid."""
        r = self.pack("Parent", "--slug", "parent", "--include",
                      "hello.txt", "--expects-probe", "no", "--no-readme",
                      *extra)
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        return [ln for ln in r.stdout.splitlines()
                if "session id:" in ln][0].split("session id:")[1].strip()

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        return sorted(p.name for p in root.iterdir()
                      if p.is_dir()) if root.is_dir() else []

    def assert_ok(self, result) -> None:
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

    def assert_refused(self, result, *fragments: str) -> None:
        self.assertNotEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        for frag in fragments:
            self.assertIn(frag, result.stderr,
                          msg=f"stdout:\n{result.stdout}")


# ---------------------------------------------------------------------------
# bale open --check
# ---------------------------------------------------------------------------

class OpenCheckTest(_RehearsalBase):

    def test_check_passes_spends_no_oracle_and_writes_nothing(self) -> None:
        self.configure_checkpoint()
        self.commit_all("checkpoint config")
        bundle = self.build_bundle("b.bale-bundle",
                                   pack_argv=self.argv("chk"),
                                   checkpoint=CP_HOLD)
        before = self.snap()
        result = self.open_bundle(bundle, "--check")
        self.assert_ok(result)
        self.assertIn("rehearsal", result.stdout)
        self.assertIn("bale open --check", result.stdout)
        self.assertIn("wrote", result.stdout)
        self.assertIn("nothing", result.stdout)
        self.assertIn("not run (--check spends no oracle)", result.stdout)
        self.assertNotIn(DRY_RUN_MARKER, result.stdout)
        self.assertNotIn("replaying pack invocation", result.stdout)
        self.assert_wrote_nothing(before, result)

    def test_check_refuses_the_include_naming_specimen(self) -> None:
        """The paired-desk specimen (row 122's first half): a read-only
        bundle whose argv includes the checkpoint directory. --check
        refuses at the blindness gate's read half — the parent stays
        `opened`, still the one open session, and nothing is written."""
        self.configure_checkpoint()
        cp_dir = self.repo / "claude" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "old.sh").write_text("#!/usr/bin/env bash\nexit 0\n",
                                       encoding="utf-8")
        self.commit_all("checkpoint config")
        parent = self.open_parent("--read-only")
        bundle = self.build_bundle(
            "revb.bale-bundle",
            pack_argv=["Read-only child", "--slug", "child", "--read-only",
                       "--include", "claude/checkpoints",
                       "--supersedes", parent],
            pre_answered=[{"prompt": "supersede", "subject": parent}])
        before = self.snap()
        result = self.open_bundle(bundle, "--check")
        self.assert_refused(result, "--allow-checkpoint-in-scope")
        self.assertNotIn("superseded-by-split", result.stdout)
        self.assertEqual(self.open_sids(), [parent])
        self.assert_wrote_nothing(before, result)

    def test_check_refuses_a_missing_write_path(self) -> None:
        bundle = self.build_bundle(
            "b.bale-bundle",
            pack_argv=self.argv("gone", "--write", "missing.txt"))
        before = self.snap()
        result = self.open_bundle(bundle, "--check")
        self.assert_refused(result, "--write path does not exist: missing.txt")
        self.assert_wrote_nothing(before, result)

    def test_check_refuses_a_placeholder_brief(self) -> None:
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("ph"),
            brief="# Brief\n\nTODO(brief): the intent\n")
        before = self.snap()
        result = self.open_bundle(bundle, "--check")
        self.assert_refused(result, "TODO(brief)")
        self.assert_wrote_nothing(before, result)

    def test_check_predicts_the_accept_and_the_parent_stays_open(
            self) -> None:
        parent = self.open_parent()
        record_path = (self.repo / "claude" / "telemetry" /
                       f"{parent}.json")
        record_before = record_path.read_bytes()
        bundle = self.build_bundle(
            "b.bale-bundle",
            pack_argv=["Child", "--slug", "child", "--write", "hello.txt",
                       "--include", "hello.txt", "--supersedes", parent],
            pre_answered=[{"prompt": "supersede", "subject": parent}])
        before = self.snap()
        result = self.open_bundle(bundle, "--check")
        self.assert_ok(result)
        self.assertIn("a pre-answered intent would accept", result.stdout)
        self.assertIn("it stays open", result.stdout)
        self.assertEqual(self.open_sids(), [parent])
        self.assertEqual(record_path.read_bytes(), record_before)
        self.assert_wrote_nothing(before, result)

    def test_check_reports_an_unmatched_intent(self) -> None:
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("unc"),
            pre_answered=[{"prompt": "supersede",
                           "subject": "2026-01-01-ghost-001"}])
        before = self.snap()
        result = self.open_bundle(bundle, "--check")
        self.assert_ok(result)
        self.assertIn("would not be consumed", result.stdout)
        self.assert_wrote_nothing(before, result)

    def test_check_on_a_second_desk_records_no_desk(self) -> None:
        bundle = self.build_bundle(
            "plan.bale-bundle",
            pack_argv=["Plan", "--slug", "plan", "--read-only",
                       "--include", "hello.txt"])
        self.assert_ok(self.open_bundle(bundle))
        [sid] = self.open_sids()
        before = self.snap()
        result = self.open_bundle(bundle, "--check")
        self.assert_ok(result)
        self.assertIn(f"would record desk-2 on open session {sid}",
                      result.stdout)
        self.assert_wrote_nothing(before, result)
        record = json.loads((self.repo / "claude" / "telemetry" /
                             f"{sid}.json").read_text(encoding="utf-8"))
        self.assertEqual([a["outcome"] for a in record["attempts"]],
                         ["opened"])

    def test_check_and_dry_run_are_exclusive(self) -> None:
        bundle = self.build_bundle("b.bale-bundle",
                                   pack_argv=self.argv("x"))
        result = self.open_bundle(bundle, "--check", "--dry-run")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not allowed with argument", result.stderr)


# ---------------------------------------------------------------------------
# bale open --dry-run
# ---------------------------------------------------------------------------

class OpenDryRunTest(_RehearsalBase):

    def setUp(self) -> None:
        super().setUp()
        self.configure_checkpoint()
        self.commit_all("checkpoint config")

    def dry_run(self, checkpoint: str, *argv_extra: str):
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("dr", *argv_extra),
            checkpoint=checkpoint)
        return self.open_bundle(bundle, "--dry-run", "--no-sandbox")

    def test_expected_hold_echoes_verdicts_exits_zero_writes_nothing(
            self) -> None:
        before = self.snap()
        result = self.dry_run(CP_HOLD)
        self.assert_ok(result)
        self.assertIn(DRY_RUN_MARKER, result.stdout)
        self.assertIn("[FAIL] the landed marker exists", result.stdout)
        self.assertIn("exit 1 — the expected HOLD", result.stdout)
        self.assertNotIn("replaying pack invocation", result.stdout)
        self.assert_wrote_nothing(before, result)
        # The dry-run log is kept outside the repository and named.
        log_line = [ln for ln in result.stdout.splitlines()
                    if "exit 1 — the expected HOLD (log:" in ln][0]
        log_path = Path(log_line.split("(log: ")[1].rstrip(")"))
        self.assertTrue(log_path.is_file(), msg=str(log_path))
        self.assertFalse(str(log_path.resolve()).startswith(
            str(self.repo.resolve())), msg=str(log_path))
        self.assertIn("bundle checkpoint dry-run",
                      log_path.read_text(encoding="utf-8"))

    def test_vacuous_pass_exits_zero_with_the_warning(self) -> None:
        before = self.snap()
        result = self.dry_run(CP_PASS)
        self.assert_ok(result)
        self.assertIn("vacuous oracle", result.stdout)
        self.assertIn("A real open proceeds", result.stdout)
        self.assert_wrote_nothing(before, result)

    def test_defective_oracle_exits_nonzero_naming_the_exit(self) -> None:
        before = self.snap()
        result = self.dry_run(CP_ERROR)
        self.assert_refused(result, "the checkpoint dry-run exited 2")
        self.assert_wrote_nothing(before, result)

    def test_a_gate_refusal_spends_no_oracle(self) -> None:
        before = self.snap()
        result = self.dry_run(CP_HOLD, "--write", "missing.txt")
        self.assert_refused(result, "--write path does not exist")
        self.assertNotIn(DRY_RUN_MARKER, result.stdout)
        self.assert_wrote_nothing(before, result)


# ---------------------------------------------------------------------------
# bale pack --dry-run
# ---------------------------------------------------------------------------

class PackDryRunTest(_RehearsalBase):

    def line(self, *extra: str) -> list:
        return ["Typed goal", "--slug", "typed", "--include", "hello.txt",
                "--expects-probe", "no", *extra]

    def test_a_clean_line_passes_and_writes_nothing(self) -> None:
        before = self.snap()
        result = self.pack(*self.line("--no-readme"), "--dry-run")
        self.assert_ok(result)
        self.assertIn("bale pack --dry-run", result.stdout)
        self.assertIn("every argv-only gate passed", result.stdout)
        self.assertIn("write forecast", result.stdout)
        self.assert_wrote_nothing(before, result)
        self.assertFalse((self.repo / ".bale").exists())

    def test_gate_refusals_are_the_gates_own_text(self) -> None:
        cases = {
            "slug": (["Goal", "--slug", "Bad_Slug", "--no-readme"],
                     "--slug must be kebab-case"),
            "include": (["Goal", "--slug", "x", "--include", "nope",
                         "--no-readme"],
                        "--include path does not exist: nope"),
            "pair": (["Goal", "--slug", "x", "--write", "hello.txt",
                      "--read-only", "--no-readme"],
                     "--write and --read-only are contradictory"),
            "cap": (["Goal", "--slug", "x", "--max-files", "0",
                     "--no-readme"], "--max-files must be >= 1"),
            "piped wizard": (["Goal", "--no-readme"],
                             "missing required arg(s) (--slug)"),
            "no readme": (["Goal", "--slug", "x"],
                          "packing without a README and without "
                          "--no-readme"),
        }
        for name, (argv, text) in cases.items():
            with self.subTest(case=name):
                before = self.snap()
                result = self.pack(*argv, "--dry-run")
                self.assert_refused(result, text)
                self.assert_wrote_nothing(before, result)

    def test_json_and_context_pairs_refuse(self) -> None:
        before = self.snap()
        r = self.pack(*self.line("--no-readme"), "--dry-run", "--json")
        self.assert_refused(r, "--dry-run and --json are not supported "
                               "together")
        r2 = self.pack("--context", "--dry-run")
        self.assert_refused(r2, "--context writes a session-less",
                            "--dry-run")
        self.assert_wrote_nothing(before, r2)

    def test_outside_a_repository_refuses(self) -> None:
        with tempfile.TemporaryDirectory(dir=self.tmp) as bare:
            r = run_bale(self.install,
                         ["pack", *self.line("--no-readme"), "--dry-run"],
                         cwd=Path(bare), env=self.env)
            self.assert_refused(r, "git-init walkthrough")
            self.assertEqual(list(Path(bare).iterdir()), [])

    def test_piped_supersedes_refuses_and_the_parent_stays_open(
            self) -> None:
        parent = self.open_parent()
        record_path = (self.repo / "claude" / "telemetry" /
                       f"{parent}.json")
        record_before = record_path.read_bytes()
        before = self.snap()
        result = self.pack("Child", "--slug", "child", "--write",
                           "hello.txt", "--no-readme",
                           "--supersedes", parent, "--dry-run")
        self.assert_refused(result, f"{parent} is still open")
        self.assertEqual(self.open_sids(), [parent])
        self.assertEqual(record_path.read_bytes(), record_before)
        self.assert_wrote_nothing(before, result)

    def test_tty_supersedes_predicts_the_prompt_and_asks_nothing(
            self) -> None:
        parent = self.open_parent()
        before = self.snap()
        # An answer is queued, but no prompt may consume it.
        # run_bale_pty returns (exit_code, combined_output).
        code, output = run_bale_pty(
            self.install,
            ["pack", "Child", "--slug", "child", "--write", "hello.txt",
             "--no-readme", "--supersedes", parent, "--dry-run"],
            cwd=self.repo, env=self.env, answers="y\n")
        self.assertEqual(code, 0, msg=output)
        self.assertIn("the exchange would prompt", output)
        self.assertNotIn("Close open session", output)
        self.assertEqual(self.open_sids(), [parent])
        changes = before.diff(self.snap())
        self.assertEqual(changes, [], msg=f"{changes}\n{output}")

    def test_read_only_sweep_is_previewed_not_run(self) -> None:
        master = self.open_parent("--read-only")
        before = self.snap()
        result = self.pack("Another plan", "--slug", "plan2", "--read-only",
                           "--include", "hello.txt", "--no-readme",
                           "--dry-run")
        self.assert_ok(result)
        self.assertIn("read-only sweep", result.stdout)
        self.assertIn(master, result.stdout)
        self.assertEqual(self.open_sids(), [master])
        self.assert_wrote_nothing(before, result)


# ---------------------------------------------------------------------------
# A real open now gates the whole argv before the oracle
# ---------------------------------------------------------------------------

class OpenGatesBeforeOracleTest(_RehearsalBase):

    def test_placeholder_brief_refuses_before_the_dry_run(self) -> None:
        """Until v0.4.45 the `TODO(brief)` refusal fired only inside the
        replay, after the checkpoint dry-run had run; the open's gate step
        is now the rehearsal's, so it refuses first."""
        self.configure_checkpoint()
        self.commit_all("checkpoint config")
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("ph"),
            brief="# Brief\n\nTODO(brief): the intent\n",
            checkpoint=CP_HOLD)
        result = self.open_bundle(bundle, "--no-sandbox")
        self.assert_refused(result, "TODO(brief)")
        self.assertNotIn(DRY_RUN_MARKER, result.stdout)
        self.assert_no_session_state(result)


if __name__ == "__main__":
    unittest.main()
