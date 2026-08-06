#!/usr/bin/env python3
"""Hermetic E2E for the board-34 --verbose thread close (v0.3.35).

Pins the three closes BALE.md §13's v0.3 --verbose entry named as the
residue, plus the riding staging-row fold-in:

- `bale pack --verbose` streams the filter-chain drop decisions (which
  filter dropped each path) and the tarball build trail (injected
  docs/tools, manifest, context copies, the tar step); the default pack
  emits none of those lines — byte-parity with the pre-flag surface.
- `bale revert --verbose` streams the discard's captured git output
  (the `branch -D` result at minimum); default emits no verbose lines;
  and under `--json --verbose` the v0.3.19 stream discipline holds —
  stdout carries exactly the one JSON line, verbose lines ride stderr.
- The TARBALL.md §7.4 pass-through: `bale apply --verbose` forwards
  `--verbose` onto validation.sh's own argv, and the default apply
  invokes the script with no arguments — asserted by a validation.sh
  that echoes its argv, read back from the session log both runs write.
- The fold-in: `_discard_hold_state` returns machine facts only and
  bale_report.format_staging_row projects the human row from them,
  byte-identical to the old inline strings (all four states unit-
  checked against the shipped renderer), and revert's human summary
  still carries the projected row.
- The v0.4.0 rider (the accepted 005 proposal): the other two
  `_discard_hold_state` callers thread the already-present verbose
  flag — `bale retry --verbose` and the apply walkthrough's revert
  action stream the discard's captured git output; both default
  surfaces emit no verbose lines, same parity pin as pack/revert.

The response tarball fixture mirrors test_hold_retry_e2e's shape
(computed hashes, real scripts); the HOLD fixture for revert mirrors
test_revert_json's sanctioned plain-git branch fabrication.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_verbose_thread.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from harness import (
    REPO_ROOT,
    bale_env,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_bale_pty,
    run_checked,
)

VERBOSE_MARKER = "verbose:"
ARGV_SENTINEL = "VALIDATION-ARGV:["


class VerboseThreadTest(unittest.TestCase):
    """pack/revert --verbose stream their quiet phases; apply --verbose
    forwards the flag onto validation.sh's argv; defaults are unchanged."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-verbose-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.git_env = git_env(self.home)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def git(self, *args: str) -> None:
        run_checked(["git", *args], cwd=self.repo, env=self.git_env)

    def commit_extra_file(self) -> None:
        """A second tracked file, outside the pack's --include, so the
        filter chain has a drop to narrate."""
        (self.repo / "extra.txt").write_text("outside the include\n",
                                             encoding="utf-8")
        self.git("add", "extra.txt")
        self.git("commit", "-m", "add extra.txt")

    def pack(self, *extra: str):
        return run_bale(
            self.install,
            [
                "pack", "verbose thread test goal",
                "--slug", "verbose",
                "--include", "hello.txt",
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
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

    def packed_sid(self, *extra: str) -> str:
        result = self.pack(*extra)
        self.assert_ok(result)
        sids = self.open_sids()
        self.assertTrue(sids, msg="pack succeeded but no session is open")
        return sids[-1]

    def make_held_session(self) -> str:
        """The sanctioned revert fixture (test_revert_json's shape): a
        real pack for the registry/metadata half, then a plain-git
        `bale/<sid>` branch with a session commit."""
        sid = self.packed_sid()
        branch = f"bale/{sid}"
        self.git("checkout", "-b", branch)
        (self.repo / "widget.txt").write_text("bale change\n",
                                              encoding="utf-8")
        self.git("add", "widget.txt")
        self.git("commit", "-m", f"[bale {sid}] add the widget file")
        self.git("checkout", "main")
        return sid

    def build_response_tarball(self, sid: str, *, name: str) -> Path:
        """A valid normal response modifying hello.txt whose
        validation.sh echoes its own argv (the §7.4 probe) and passes.
        Sizes and hashes computed, never transcribed."""
        nnn = sid[-3:]
        rdir = self.tmp / name / f"response-{nnn}"
        (rdir / "files").mkdir(parents=True)
        data = f"rewritten by {name}\n".encode("utf-8")
        (rdir / "files" / "hello.txt").write_bytes(data)
        manifest = {
            "session_id": sid,
            "responds_to": sid,
            "corrects": None,
            "response_kind": "normal",
            "summary": "verbose-thread fixture: rewrite hello.txt; "
                       "validation.sh echoes its argv so the §7.4 "
                       "pass-through is observable in the session log",
            "changes": [
                {
                    "path": "hello.txt",
                    "action": "modified",
                    "reason": "the goal's rewrite; the validation script's "
                              "argv echo is the surface under test",
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
        (rdir / "validation.sh").write_text(
            "#!/usr/bin/env bash\n"
            "# Echo the argv bale invoked us with — the §7.4 probe.\n"
            f"echo \"{ARGV_SENTINEL}$*]\"\n"
            "echo \"[PASS] fixture check\"\n"
            "exit 0\n",
            encoding="utf-8")
        tarball = self.tmp / name / f"response-{nnn}.tar.gz"
        with tarfile.open(tarball, "w:gz") as tf:
            tf.add(str(rdir), arcname=f"response-{nnn}")
        return tarball

    def session_log_text(self, sid: str) -> str:
        p = self.repo / ".bale" / "logs" / f"{sid}.log"
        self.assertTrue(p.is_file(), msg=f"no session log at {p}")
        return p.read_text(encoding="utf-8")

    # -- pinned behavior 1: pack --verbose streams its quiet phases ------

    def test_pack_verbose_streams_drops_and_build_trail(self) -> None:
        self.commit_extra_file()
        result = self.pack("--verbose")
        self.assert_ok(result)
        combined = result.stdout + result.stderr
        # The filter-chain drop trail names the path AND the filter.
        self.assertIn("verbose: skip extra.txt (outside --include)",
                      combined)
        # The build trail: an injected global doc, the manifest write,
        # and the surviving context copy.
        self.assertIn("verbose: inject global doc CLAUDE.md", combined)
        self.assertIn("verbose: write manifest.json", combined)
        self.assertIn("verbose: copy context/hello.txt", combined)
        # Build-trail lines run post-sid: they land in the session log
        # too (the §5.4 in-addition-to-the-log contract).
        sid = self.open_sids()[-1]
        log_text = self.session_log_text(sid)
        self.assertIn("verbose: copy context/hello.txt", log_text)

    def test_pack_default_emits_no_verbose_lines(self) -> None:
        self.commit_extra_file()
        result = self.pack()
        self.assert_ok(result)
        combined = result.stdout + result.stderr
        self.assertNotIn(VERBOSE_MARKER, combined,
                         msg="the default pack surface must stay "
                             "byte-parity with the pre-flag behavior")

    # -- pinned behavior 2: revert --verbose streams captured git --------

    def test_revert_verbose_streams_git_output(self) -> None:
        sid = self.make_held_session()
        result = run_bale(self.install, ["revert", "--verbose"],
                          cwd=self.repo, env=self.env)
        self.assert_ok(result)
        combined = result.stdout + result.stderr
        # git's own "Deleted branch bale/<sid>" line, surfaced through
        # the verbose echo of the captured branch -D result.
        self.assertIn(f"verbose: git branch -D bale/{sid}", combined)
        self.assertIn("Deleted branch", combined)

    def test_revert_default_emits_no_verbose_lines(self) -> None:
        self.make_held_session()
        result = run_bale(self.install, ["revert"],
                          cwd=self.repo, env=self.env)
        self.assert_ok(result)
        combined = result.stdout + result.stderr
        self.assertNotIn(VERBOSE_MARKER, combined)
        # The fold-in's projected human row still renders (this fixture
        # never staged, so the row reads "not recorded").
        self.assertIn("not recorded", combined)

    def test_revert_json_verbose_keeps_stream_discipline(self) -> None:
        sid = self.make_held_session()
        result = run_bale(self.install, ["revert", "--json", "--verbose"],
                          cwd=self.repo, env=self.env)
        self.assert_ok(result)
        stdout_lines = [ln for ln in result.stdout.splitlines()
                        if ln.strip()]
        self.assertEqual(
            len(stdout_lines), 1,
            msg=f"--json stdout must stay exactly one line under "
                f"--verbose; got:\n{result.stdout}")
        payload = json.loads(stdout_lines[0])
        self.assertEqual(payload["outcome"], "reverted")
        self.assertEqual(payload["sid"], sid)
        # Machine staging keys unchanged by the fold-in.
        self.assertEqual(payload["staging_state"], "not-recorded")
        self.assertIsNone(payload["staging_path"])
        # The verbose trail rides stderr with the rest of the human
        # reference trail.
        self.assertIn(f"verbose: git branch -D bale/{sid}", result.stderr)

    # -- pinned behavior 3: the §7.4 argv pass-through -------------------

    def test_apply_verbose_forwards_flag_onto_validation_argv(self) -> None:
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="verbose-run")
        result = run_bale(self.install,
                          ["apply", str(tarball), "--verbose"],
                          cwd=self.repo, env=self.env)
        self.assert_ok(result)
        log_text = self.session_log_text(sid)
        self.assertIn(f"{ARGV_SENTINEL}--verbose]", log_text,
                      msg="apply --verbose must forward --verbose onto "
                          "validation.sh's own argv (TARBALL.md §7.4)")
        # The verbose path also streamed the script's output live.
        self.assertIn(f"{ARGV_SENTINEL}--verbose]",
                      result.stdout + result.stderr)

    def test_apply_default_invokes_validation_with_no_args(self) -> None:
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="default-run")
        result = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assert_ok(result)
        log_text = self.session_log_text(sid)
        self.assertIn(f"{ARGV_SENTINEL}]", log_text,
                      msg="the default invocation must stay exactly "
                          "`bash validation.sh` — no arguments")
        self.assertNotIn(f"{ARGV_SENTINEL}--verbose]", log_text)

    # -- pinned behavior 5: the discard-path threading (v0.4.0 rider) ----

    def test_retry_verbose_streams_discard_git_output(self) -> None:
        """`bale retry --verbose` threads the flag into
        _discard_hold_state: the prior attempt's branch -D result
        streams live before the pipeline re-runs."""
        sid = self.make_held_session()
        tarball = self.build_response_tarball(sid, name="retry-verbose")
        result = run_bale(self.install,
                          ["retry", str(tarball), "--verbose"],
                          cwd=self.repo, env=self.env)
        self.assert_ok(result)
        combined = result.stdout + result.stderr
        self.assertIn(f"verbose: git branch -D bale/{sid}", combined)
        self.assertIn("Deleted branch", combined)

    def test_retry_default_emits_no_verbose_lines(self) -> None:
        sid = self.make_held_session()
        tarball = self.build_response_tarball(sid, name="retry-default")
        result = run_bale(self.install, ["retry", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assert_ok(result)
        combined = result.stdout + result.stderr
        self.assertNotIn(VERBOSE_MARKER, combined,
                         msg="the default retry surface must stay "
                             "byte-parity with the pre-rider behavior")

    def test_walkthrough_revert_verbose_streams_discard_git_output(
            self) -> None:
        """The apply walkthrough's revert action threads the pipeline's
        verbose flag into _discard_hold_state: choosing [r] under
        `apply --verbose` streams the branch -D result."""
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="walkrevert-verbose")
        exit_code, output = run_bale_pty(
            self.install, ["apply", str(tarball), "--verbose"],
            cwd=self.repo, env=self.env, answers="r\n")
        self.assertEqual(
            exit_code, 1,
            msg=f"walkthrough revert exits 1 (work did not land); "
                f"output:\n{output}")
        self.assertIn(f"verbose: git branch -D bale/{sid}", output)
        self.assertIn("Deleted branch", output)

    def test_walkthrough_revert_default_emits_no_verbose_lines(self) -> None:
        sid = self.packed_sid()
        tarball = self.build_response_tarball(sid, name="walkrevert-default")
        exit_code, output = run_bale_pty(
            self.install, ["apply", str(tarball)],
            cwd=self.repo, env=self.env, answers="r\n")
        self.assertEqual(
            exit_code, 1,
            msg=f"walkthrough revert exits 1 (work did not land); "
                f"output:\n{output}")
        self.assertIn(f"bale/{sid} deleted", output,
                      msg="the revert action must still have run")
        self.assertNotIn(VERBOSE_MARKER, output,
                         msg="the default walkthrough-revert surface must "
                             "stay byte-parity with the pre-rider behavior")

    # -- pinned behavior 4: the staging-row projection -------------------

    def test_format_staging_row_projects_all_four_states(self) -> None:
        """The renderer's output is byte-identical to the strings
        _discard_hold_state used to build inline (the fold-in's
        no-drift guarantee), checked against the shipped module."""
        sys.path.insert(0, str(REPO_ROOT / "bin"))
        try:
            import bale_report
            row = bale_report.format_staging_row
            self.assertEqual(row(state="wiped", path="/tmp/s"),
                             "wiped (/tmp/s)")
            self.assertEqual(row(state="already-gone", path="/tmp/s"),
                             "already gone")
            self.assertEqual(row(state="not-recorded", path=None),
                             "not recorded")
            self.assertEqual(
                row(state="unremovable", path="/tmp/s",
                    error="[Errno 13] Permission denied: '/tmp/s'"),
                "left in place (/tmp/s: [Errno 13] Permission denied: "
                "'/tmp/s')")
        finally:
            sys.path.remove(str(REPO_ROOT / "bin"))


if __name__ == "__main__":
    unittest.main()
