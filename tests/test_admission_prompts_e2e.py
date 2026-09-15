"""End-to-end tier for the v0.4.27 (board 78) admission prompts: real
`bale apply` runs against a scratch install, piped (every non-TTY face
declines without prompting and prints the composed remedy) and under a
pty (the per-path drift y/N and the sandbox-unavailable y/N).

The sandbox-unavailable cases do not depend on the host: a shim
`unshare` that exits 1 is put first on PATH, so the self-probe refuses
the same way on a namespace-less work server and on a host that has
namespaces. That is the row-75 "second run" made unconditional. The
happy confined path itself is tests/test_sandbox_wrapper.py's business.

Not covered here: the `bale retry` verb on the composed line (the
suite that builds a HOLD state, test_hold_retry_e2e.py, is not shipped
with this request; compose_admission_command's verb handling is pinned
at the unit tier in test_admission_prompts.py).

Since v0.4.31 (board 89) two more facts are pinned here:

- The composed drift line carries every typed --allow-out-of-scope
  value (normalized, first), then every drifted path — a typed path
  that matched no drift used to be dropped. The json face's
  `drift.remedy` is the same line.
- Each of the two apply-time admission prompts names its decline
  cause: `stdin closed or interrupted` (^D at the prompt under the
  pty), `empty answer at a decline default` (Enter), `answered 'x'`
  (a typed answer, stripped and lowercased). One case per cause per
  prompt, the model being test_hook_acceptance.py's three.
"""

from __future__ import annotations

import json
import os
import stat
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
    run_bale_pty,
    run_checked,
    tar_response_dir,
)

DRIFT_MARKER = "[SCOPE-DRIFT-REFUSED]"
SANDBOX_MARKER = "[SANDBOX-UNAVAILABLE]"
NOT_OFFERED = "admission prompt not offered"
SANDBOX_NOT_OFFERED = "sandbox admission prompt not offered"

# ^D at the start of a line under the pty: the line discipline makes
# input() raise EOFError — the "stdin closed" branch at a TTY prompt.
EOT = "\x04"

# The drift prompt's three decline lines (bale_apply.DRIFT_ADMISSION_
# DECLINE_LINES), verbatim; the bare pre-board-89 line must not survive.
DRIFT_DECLINE_BARE = "admission prompt declined at lib/b.txt; nothing"
DRIFT_DECLINE_TAIL = "; nothing admitted at the prompt, nothing lands partially"
DRIFT_DECLINE_STDIN_CLOSED = (
    "admission prompt declined at lib/b.txt (stdin closed or interrupted)"
    + DRIFT_DECLINE_TAIL)
DRIFT_DECLINE_EMPTY = (
    "admission prompt declined at lib/b.txt (empty answer at a decline "
    "default)" + DRIFT_DECLINE_TAIL)


def drift_decline_answered(answer: str) -> str:
    return (f"admission prompt declined at lib/b.txt (answered '{answer}')"
            + DRIFT_DECLINE_TAIL)


# The sandbox prompt's three (bale_apply.SANDBOX_ADMISSION_DECLINE_LINES).
SANDBOX_DECLINE_BARE = "sandbox admission prompt declined; nothing"
SANDBOX_DECLINE_TAIL = "; nothing staged, nothing ran"
SANDBOX_DECLINE_STDIN_CLOSED = (
    "sandbox admission prompt declined (stdin closed or interrupted)"
    + SANDBOX_DECLINE_TAIL)
SANDBOX_DECLINE_EMPTY = (
    "sandbox admission prompt declined (empty answer at a decline default)"
    + SANDBOX_DECLINE_TAIL)


def sandbox_decline_answered(answer: str) -> str:
    return (f"sandbox admission prompt declined (answered '{answer}')"
            + SANDBOX_DECLINE_TAIL)


class _AdmissionFixture(unittest.TestCase):
    """A repo with src/a.txt and lib/b.txt committed, a session whose
    write forecast is `src` only, and response builders that drift onto
    lib/ (one or two paths).

    CONFINE=False (the default) commits `[sandbox] enabled = false` so
    the apply that follows an admission runs nothing confined: the
    drift and hook prompts are host-independent and the suite passes on
    a namespace-less host too (verified with `unshare` off PATH). The
    sandbox-unavailable class sets CONFINE=True — it needs the probe.
    """

    CONFINE = False

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-admit-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        for rel in ("src/a.txt", "lib/b.txt", "lib/c.txt"):
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"{rel}\n", encoding="utf-8")
        if not self.CONFINE:
            (self.repo / "bale.toml").write_text(
                "[sandbox]\nenabled = false\n", encoding="utf-8")
            run_checked(["git", "add", "bale.toml"],
                        cwd=self.repo, env=self.genv)
        run_checked(["git", "add", "src", "lib"], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "fixture tree"],
                    cwd=self.repo, env=self.genv)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- session ---------------------------------------------------------

    def pack_src_forecast(self) -> str:
        r = run_bale(self.install, [
            "pack", "admission prompt fixture goal",
            "--slug", "admit", "--include", "src", "lib",
            "--write", "src", "--no-readme",
        ], cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        sids = self.open_sids()
        self.assertTrue(sids)
        return sids[-1]

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return sorted(d.name for d in root.iterdir()
                      if (d / "open").is_file())

    def response(self, sid: str, *paths: str) -> Path:
        entries = [{
            "path": p, "action": "modified",
            "reason": f"fixture reason for {p}",
            "data": f"rewritten {p} by {sid}\n".encode("utf-8"),
        } for p in paths]
        rdir = build_response_dir(
            self.tmp / ("resp-" + "-".join(p.replace("/", "_") for p in paths)),
            sid, summary="admission fixture", entries=entries)
        return tar_response_dir(rdir)

    # -- readers ---------------------------------------------------------

    def record(self, sid: str) -> dict:
        return json.loads((self.repo / "claude" / "telemetry" / f"{sid}.json")
                          .read_text(encoding="utf-8"))

    def latest_attempt(self, sid: str) -> dict:
        return self.record(sid)["attempts"][-1]

    def session_log(self, sid: str) -> str:
        return (self.repo / ".bale" / "logs" / f"{sid}.log").read_text(
            encoding="utf-8")

    def composed(self, tarball: Path, *paths: str, verb: str = "apply",
                 tail: str = "") -> str:
        flags = " ".join(f"--allow-out-of-scope '{p}'" for p in paths)
        return f"bale {verb} '{tarball.name}'" + (f" {flags}" if flags else "") + tail

    # -- the namespace-less host, unconditionally ------------------------

    def break_sandbox(self) -> None:
        """Put a failing `unshare` first on PATH so the self-probe refuses."""
        shim_dir = self.tmp / "shim"
        shim_dir.mkdir(exist_ok=True)
        shim = shim_dir / "unshare"
        shim.write_text("#!/bin/sh\necho 'shim: namespaces unavailable' >&2\nexit 1\n",
                        encoding="utf-8")
        shim.chmod(shim.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP
                   | stat.S_IXOTH)
        self.env["PATH"] = str(shim_dir) + os.pathsep + self.env["PATH"]


class DriftNonTTYFacesTest(_AdmissionFixture):
    """Every non-TTY path declines without prompting and prints the
    same composed line."""

    def test_piped_stdin_declines_with_composed_line(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt", "lib/c.txt")
        r = run_bale(self.install, ["apply", str(tarball)],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 1, msg=r.stdout)
        self.assertIn(DRIFT_MARKER, r.stdout)
        self.assertIn(f"{NOT_OFFERED} (stdin is not a TTY)", r.stdout)
        line = self.composed(tarball, "lib/b.txt", "lib/c.txt")
        self.assertIn(line, r.stdout)
        self.assertTrue(any(ln.strip() == line for ln in r.stdout.splitlines()),
                        msg="the composed remedy is one physical line")
        self.assertNotIn("<tarball>", r.stdout)
        self.assertNotIn("<path>", r.stdout)
        self.assertIn(sid, self.open_sids())
        a = self.latest_attempt(sid)
        self.assertEqual(a["outcome"], "scope-drift-refused")
        self.assertEqual(a["overridden_paths"], [])
        self.assertEqual(a["overridden_path_sources"], {})

    def test_composed_line_carries_typed_flags_and_admitted_paths(self) -> None:
        """A partial typed admission: the refused re-run carries the
        typed path AND the refused one, plus the other admission flags
        the invocation had, and the record stamps the typed one as
        flag-sourced."""
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt", "lib/c.txt")
        r = run_bale(self.install, [
            "apply", str(tarball), "--allow-out-of-scope", "lib/b.txt",
            "--no-sandbox", "--accept-checkpoint-change",
        ], cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 1, msg=r.stdout)
        self.assertIn(self.composed(tarball, "lib/b.txt", "lib/c.txt",
                                    tail=" --accept-checkpoint-change "
                                         "--no-sandbox"),
                      r.stdout)
        a = self.latest_attempt(sid)
        self.assertEqual(a["overridden_paths"], ["lib/b.txt"])
        self.assertEqual(a["overridden_path_sources"], {"lib/b.txt": "flag"})

    def test_composed_line_carries_a_typed_path_that_matched_no_drift(self) -> None:
        """The one composed-line rule (board 89): every typed
        --allow-out-of-scope value rides the re-run line verbatim —
        normalized as the gate compared it, typed values first, then
        the drifted paths, deduplicated — so a no-effect typed path is
        never dropped and re-asked. Here `./lib/zzz.txt` is in the
        forecast's complement but not in the change set (no effect,
        logged as such), `lib/b.txt` is typed AND drifting (once on the
        line), and `lib/c.txt` is the refused drift."""
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt", "lib/c.txt")
        r = run_bale(self.install, [
            "apply", str(tarball),
            "--allow-out-of-scope", "./lib/zzz.txt",
            "--allow-out-of-scope", "lib/b.txt",
        ], cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 1, msg=r.stdout)
        self.assertIn("no matching out-of-forecast change: lib/zzz.txt "
                      "(no effect)", r.stdout)
        line = self.composed(tarball, "lib/b.txt", "lib/zzz.txt", "lib/c.txt")
        self.assertIn(line, r.stdout)
        self.assertTrue(any(ln.strip() == line for ln in r.stdout.splitlines()),
                        msg="typed values first, drift appended, one line")
        self.assertEqual(r.stdout.count("--allow-out-of-scope 'lib/b.txt'"),
                         r.stdout.count(line),
                         msg="a typed-and-drifting path rides once")
        a = self.latest_attempt(sid)
        self.assertEqual(a["overridden_paths"], ["lib/b.txt"])

    def test_json_remedy_follows_the_typed_value_carry(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt")
        r = run_bale(self.install, [
            "apply", str(tarball), "--json",
            "--allow-out-of-scope", "lib/zzz.txt",
        ], cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 1, msg=r.stderr)
        report = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(report["outcome"], "scope-drift-refused")
        self.assertEqual(report["drift"]["remedy"],
                         self.composed(tarball, "lib/zzz.txt", "lib/b.txt"))

    def test_json_mode_declines_even_on_a_tty(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt")
        code, out = run_bale_pty(self.install, ["apply", str(tarball), "--json"],
                                 cwd=self.repo, env=self.env, answers="y\n")
        self.assertEqual(code, 1, msg=out)
        self.assertNotIn("admit lib/b.txt?", out)
        self.assertIn(f"{NOT_OFFERED} (--json output mode)", out)
        json_lines = [ln for ln in out.splitlines()
                      if ln.startswith("{") and '"scope-drift-refused"' in ln]
        self.assertEqual(len(json_lines), 1, msg=out)
        report = json.loads(json_lines[0])
        self.assertEqual(report["drift"]["remedy"],
                         self.composed(tarball, "lib/b.txt"))
        self.assertEqual(report["drift"]["overridden_path_sources"], {})

    def test_dry_run_declines_on_a_tty_with_no_telemetry(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt")
        code, out = run_bale_pty(self.install,
                                 ["apply", str(tarball), "--dry-run"],
                                 cwd=self.repo, env=self.env, answers="y\n")
        self.assertEqual(code, 1, msg=out)
        self.assertNotIn("admit lib/b.txt?", out)
        self.assertIn("--dry-run predicts, never admits", out)
        self.assertIn(self.composed(tarball, "lib/b.txt"), out)
        outcomes = [a["outcome"] for a in self.record(sid)["attempts"]]
        self.assertNotIn("scope-drift-refused", outcomes,
                         msg="a dry-run has no outcome")

    def test_no_interact_declines_on_a_tty(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt")
        code, out = run_bale_pty(self.install,
                                 ["apply", str(tarball), "--no-interact"],
                                 cwd=self.repo, env=self.env, answers="y\n")
        self.assertEqual(code, 1, msg=out)
        self.assertNotIn("admit lib/b.txt?", out)
        self.assertIn("non-interactive mode (no-interact via --no-interact flag)", out)
        self.assertEqual(self.latest_attempt(sid)["outcome"],
                         "scope-drift-refused")


class DriftPromptTest(_AdmissionFixture):
    """The per-path y/N on a TTY."""

    def test_accept_every_path_proceeds_with_prompt_sources(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt", "lib/c.txt")
        code, out = run_bale_pty(self.install, ["apply", str(tarball)],
                                 cwd=self.repo, env=self.env,
                                 answers="y\ny\n\n")
        self.assertEqual(code, 0, msg=out)
        self.assertIn("admit lib/b.txt? [y/N]", out)
        self.assertIn("admit lib/c.txt? [y/N]", out)
        self.assertIn("reason:   fixture reason for lib/b.txt", out)
        self.assertIn("write forecast: src", out)
        log = self.session_log(sid)
        for p in ("lib/b.txt", "lib/c.txt"):
            self.assertIn(f"FORCE: own-forecast drift admitted at the "
                          f"admission prompt: {p}", log)
        self.assertNotIn("admitted by --allow-out-of-scope", log)
        a = self.latest_attempt(sid)
        self.assertEqual(a["outcome"], "applied")
        self.assertEqual(a["overridden_paths"], ["lib/b.txt", "lib/c.txt"])
        self.assertEqual(a["overridden_path_sources"],
                         {"lib/b.txt": "prompt", "lib/c.txt": "prompt"})
        self.assertNotIn(sid, self.open_sids())

    def test_enter_declines_and_nothing_lands_partially(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt", "lib/c.txt")
        code, out = run_bale_pty(self.install, ["apply", str(tarball)],
                                 cwd=self.repo, env=self.env,
                                 answers="y\n\n")
        self.assertEqual(code, 1, msg=out)
        self.assertIn(DRIFT_MARKER, out)
        self.assertIn("admission prompt declined at lib/c.txt", out)
        self.assertRegex(out, r"admission prompt:\s+declined")
        self.assertIn(self.composed(tarball, "lib/b.txt", "lib/c.txt"), out)
        self.assertIn(sid, self.open_sids())
        a = self.latest_attempt(sid)
        self.assertEqual(a["outcome"], "scope-drift-refused")
        self.assertEqual(a["overridden_paths"], [],
                         msg="a y answered before the decline admits nothing")
        self.assertEqual(a["overridden_path_sources"], {})
        self.assertFalse((self.repo / ".bale" / "staging").exists(),
                         msg="the refusal is pre-staging")

    def test_mixed_typed_flag_and_prompt_stamp_both_sources(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt", "lib/c.txt")
        code, out = run_bale_pty(
            self.install,
            ["apply", str(tarball), "--allow-out-of-scope", "lib/b.txt"],
            cwd=self.repo, env=self.env, answers="y\n\n")
        self.assertEqual(code, 0, msg=out)
        self.assertNotIn("admit lib/b.txt?", out,
                         msg="a typed path is not asked again")
        self.assertIn("admit lib/c.txt? [y/N]", out)
        log = self.session_log(sid)
        self.assertIn("admitted by --allow-out-of-scope: lib/b.txt", log)
        self.assertIn("admission prompt: lib/c.txt", log)
        a = self.latest_attempt(sid)
        self.assertEqual(a["overridden_path_sources"],
                         {"lib/b.txt": "flag", "lib/c.txt": "prompt"})


class DriftDeclineCauseTest(_AdmissionFixture):
    """The per-path drift y/N names why it declined (board 89): one
    case per branch, each refusing pre-staging with the session open
    and the composed line printed."""

    def _declined(self, answers: str):
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt")
        code, out = run_bale_pty(self.install, ["apply", str(tarball)],
                                 cwd=self.repo, env=self.env,
                                 answers=answers)
        self.assertEqual(code, 1, msg=out)
        self.assertIn("admit lib/b.txt? [y/N]", out)
        self.assertIn(DRIFT_MARKER, out)
        self.assertRegex(out, r"admission prompt:\s+declined")
        self.assertIn(self.composed(tarball, "lib/b.txt"), out)
        self.assertNotIn(DRIFT_DECLINE_BARE, out,
                         msg="the cause-less line must not survive")
        self.assertIn(sid, self.open_sids())
        self.assertEqual(self.latest_attempt(sid)["outcome"],
                         "scope-drift-refused")
        self.assertFalse((self.repo / ".bale" / "staging").exists())
        return out

    def test_enter_names_the_empty_answer(self) -> None:
        out = self._declined("\n")
        self.assertIn(DRIFT_DECLINE_EMPTY, out)

    def test_n_is_quoted_back(self) -> None:
        out = self._declined("n\n")
        self.assertIn(drift_decline_answered("n"), out)

    def test_stray_answer_is_quoted_back_stripped_and_lowercased(self) -> None:
        out = self._declined("  NO \n")
        self.assertIn(drift_decline_answered("no"), out)

    def test_stdin_closed_at_the_prompt_names_itself(self) -> None:
        out = self._declined(EOT)
        self.assertIn(DRIFT_DECLINE_STDIN_CLOSED, out)


class SandboxUnavailableTest(_AdmissionFixture):
    """The sandbox-unavailable refusal and its y/N, on a host made
    namespace-less by the shim."""

    CONFINE = True

    def _in_forecast_response(self, sid: str) -> Path:
        return self.response(sid, "src/a.txt")

    def test_piped_stdin_refuses_with_composed_no_sandbox_line(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self._in_forecast_response(sid)
        self.break_sandbox()
        r = run_bale(self.install, ["apply", str(tarball)],
                     cwd=self.repo, env=self.env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(SANDBOX_MARKER, r.stdout)
        self.assertIn(f"{SANDBOX_NOT_OFFERED} (stdin is not a TTY)", r.stdout)
        line = self.composed(tarball, tail=" --no-sandbox")
        self.assertIn(line, r.stdout)
        self.assertIn(line, r.stderr, msg="fail() names the remedy too")
        self.assertIn("[sandbox] enabled = false", r.stderr)
        self.assertNotIn("staged into", r.stdout, msg="pre-staging")
        self.assertIn(sid, self.open_sids())
        a = self.latest_attempt(sid)
        self.assertEqual(a["outcome"], "rejected")
        self.assertIs(a["sandbox_confined"], True)
        self.assertIsNone(a["sandbox_off_source"])
        self.assertIs(a["sandbox_escaped"], False)

    def test_prompt_accept_runs_unconfined_force_logged_as_prompt(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self._in_forecast_response(sid)
        self.break_sandbox()
        code, out = run_bale_pty(self.install, ["apply", str(tarball)],
                                 cwd=self.repo, env=self.env,
                                 answers="y\n\n")
        self.assertEqual(code, 0, msg=out)
        self.assertIn("run this attempt unconfined? [y/N]", out)
        log = self.session_log(sid)
        self.assertIn("FORCE: sandbox DISABLED for this invocation (admitted "
                      "at the sandbox-unavailable prompt)", log)
        self.assertIn("UNCONFINED", log)
        self.assertNotIn("(--no-sandbox)", log)
        self.assertNotIn("DISABLED by config", log)
        a = self.latest_attempt(sid)
        self.assertEqual(a["outcome"], "applied")
        self.assertIs(a["sandbox_confined"], False)
        self.assertEqual(a["sandbox_off_source"], "prompt")
        self.assertIs(a["sandbox_escaped"], False,
                      msg="sandbox_escaped keeps its flag-only meaning")

    def test_prompt_decline_refuses_pre_staging(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self._in_forecast_response(sid)
        self.break_sandbox()
        code, out = run_bale_pty(self.install, ["apply", str(tarball)],
                                 cwd=self.repo, env=self.env, answers="\n")
        self.assertNotEqual(code, 0)
        self.assertIn(SANDBOX_MARKER, out)
        self.assertRegex(out, r"admission prompt:\s+declined")
        self.assertIn(self.composed(tarball, tail=" --no-sandbox"), out)
        self.assertIn(sid, self.open_sids())
        self.assertEqual(self.latest_attempt(sid)["outcome"], "rejected")

    def test_dry_run_neither_probes_nor_prompts(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self._in_forecast_response(sid)
        self.break_sandbox()
        code, out = run_bale_pty(self.install,
                                 ["apply", str(tarball), "--dry-run"],
                                 cwd=self.repo, env=self.env, answers="y\n")
        self.assertEqual(code, 0, msg=out)
        self.assertNotIn(SANDBOX_MARKER, out)
        self.assertNotIn("self-probe", out)

    def test_typed_flag_and_config_off_bypass_the_probe(self) -> None:
        sid = self.pack_src_forecast()
        tarball = self._in_forecast_response(sid)
        self.break_sandbox()
        r = run_bale(self.install,
                     ["apply", str(tarball), "--no-sandbox", "--no-interact"],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        a = self.latest_attempt(sid)
        self.assertEqual(a["sandbox_off_source"], "flag")
        self.assertIs(a["sandbox_escaped"], True)

    def test_drift_refuses_before_the_sandbox_prompt(self) -> None:
        """Board 68's ordering: the cheap manifest-only refusal comes
        first, so a namespace-less operator with drift is never asked
        the sandbox y/N only to be refused on drift afterwards."""
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt")
        self.break_sandbox()
        code, out = run_bale_pty(self.install, ["apply", str(tarball)],
                                 cwd=self.repo, env=self.env,
                                 answers="\n")
        self.assertEqual(code, 1, msg=out)
        self.assertIn(DRIFT_MARKER, out)
        self.assertNotIn("run this attempt unconfined?", out)
        self.assertNotIn(SANDBOX_MARKER, out)

    def test_prompt_admitted_drift_rides_the_sandbox_remedy(self) -> None:
        """Drift admitted at its prompt, then the sandbox declined: the
        composed --no-sandbox line carries the admitted path, so the
        paste is one re-run rather than a re-prompt."""
        sid = self.pack_src_forecast()
        tarball = self.response(sid, "lib/b.txt")
        self.break_sandbox()
        code, out = run_bale_pty(self.install, ["apply", str(tarball)],
                                 cwd=self.repo, env=self.env,
                                 answers="y\n\n")
        self.assertNotEqual(code, 0)
        self.assertIn(SANDBOX_MARKER, out)
        self.assertIn(self.composed(tarball, "lib/b.txt", tail=" --no-sandbox"),
                      out)

    # -- the decline names its cause (board 89) ---------------------------

    def _declined(self, answers: str):
        sid = self.pack_src_forecast()
        tarball = self._in_forecast_response(sid)
        self.break_sandbox()
        code, out = run_bale_pty(self.install, ["apply", str(tarball)],
                                 cwd=self.repo, env=self.env,
                                 answers=answers)
        self.assertNotEqual(code, 0, msg=out)
        self.assertIn("run this attempt unconfined? [y/N]", out)
        self.assertIn(SANDBOX_MARKER, out)
        self.assertRegex(out, r"admission prompt:\s+declined")
        line = self.composed(tarball, tail=" --no-sandbox")
        self.assertIn(line, out)
        self.assertIn("[bale] error: sandbox unavailable on this host", out,
                      msg="the fail() posture and remedy are unchanged")
        self.assertNotIn(SANDBOX_DECLINE_BARE, out,
                         msg="the cause-less line must not survive")
        self.assertIn(sid, self.open_sids())
        self.assertEqual(self.latest_attempt(sid)["outcome"], "rejected")
        return out

    def test_enter_names_the_empty_answer(self) -> None:
        out = self._declined("\n")
        self.assertIn(SANDBOX_DECLINE_EMPTY, out)

    def test_n_is_quoted_back(self) -> None:
        out = self._declined("n\n")
        self.assertIn(sandbox_decline_answered("n"), out)

    def test_stdin_closed_at_the_prompt_names_itself(self) -> None:
        out = self._declined(EOT)
        self.assertIn(SANDBOX_DECLINE_STDIN_CLOSED, out)


if __name__ == "__main__":
    unittest.main(verbosity=2)
