#!/usr/bin/env python3
"""Hermetic E2E for the `bale handoff` happy path (board-35 gap 7).

Until this suite, handoff was tested only at its refusals — the
install-precheck gate (``tests/test_install_precheck.py``) and the
checkpoint-blindness gate (``tests/test_checkpoint_provenance.py``).
The command's entire job — repackaging an applied bailout into a fresh
request — was unpinned. This file covers it:

- A valid bailout response (built with the harness's shared fixture
  builder, plus the two bailout-mandatory artifacts) is applied, then
  repackaged by ``bale handoff`` into a new request tarball in the
  outbox.
- The fresh request's manifest: new sid (same slug, new NNN),
  ``depends_on.previous_response`` pointing at the bailout, the goal
  inherited verbatim from the bailed-on request, constraints and
  out_of_scope reset to empty, ``expects_probe`` at its
  claude-decides default — all pinned against what ``cmd_handoff``
  ships today.
- Reading-plan-to-scope resolution as shipped: a plan citing files
  pre-packs them into ``context/`` and records them as the session's
  write forecast; a plan-less handoff resolves to whole-tree scope
  (``["."]``). The whole-tree fallback is pinned AS-IS — there is a
  standing watch on the refusal friction it creates in
  checkpoint-configured projects, and this suite deliberately does
  not remedy it.
- The ``--verbose`` flag (v0.4.3, the accepted 005 fold-in): default
  off leaves the build byte-quiet — no ``verbose:`` lines anywhere on
  the default run — and with the flag the ``build_request_tarball``
  build trail streams, landing in the new session's log too since
  handoff's call site runs post-``set_log_file``.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring. Every
invocation here is piped (stdin is not a TTY), so no prompt path may
engage.

Run directly::

    python3 tests/test_handoff_happy.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from harness import (
    bale_env,
    build_response_dir,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    tar_response_dir,
)

GOAL = "handoff happy-path goal: finish rewriting hello.txt"
SLUG = "handoff-happy"
VERBOSE_MARKER = "verbose:"

# The bale-injected top-level members every request tarball ships
# (TARBALL.md §3.1) — asserted on the handoff-built tarball so the
# repackaging path provably goes through the same builder as pack.
GLOBAL_DOCS = ("CLAUDE.md", "TARBALL.md", "DOCS.md", "CODE.md")
INJECTED_TOOLS = ("response_lint.py", "craft_response.py")


class HandoffHappyPathTest(unittest.TestCase):
    """`bale handoff` repackages an applied bailout into a fresh request."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-handoff-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def packed_and_bailed(self, *, reading_plan_paths) -> tuple[str, Path]:
        """Pack a session, apply a bailout against it, return
        (bailed_sid, bailout_tarball).

        The bailout is built with the harness's shared builder
        (``build_response_dir`` with the §5.6.2 empty change surfaces
        via ``manifest_extra``) plus the two bailout-mandatory
        artifacts — ``handoff.md`` carrying a reading plan citing
        ``reading_plan_paths`` (None omits the section entirely, the
        plan-less shape) and a schema-valid ``diagnostics.json``. The
        apply closes the session, which is the state handoff requires
        (it refuses while any session is open).
        """
        packed = run_bale(
            self.install,
            ["pack", GOAL, "--slug", SLUG,
             "--include", "hello.txt", "--no-readme"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            packed.returncode, 0,
            msg=f"stdout:\n{packed.stdout}\nstderr:\n{packed.stderr}")
        opens = self.open_sids()
        self.assertEqual(len(opens), 1)
        sid = opens[0]

        rdir = build_response_dir(
            self.tmp / "bailout", sid,
            summary="bailout fixture: the goal did not fit the budget; "
                    "handoff.md prescribes the next session",
            entries=[],
            validation_will_run=[],
            claims={},
            manifest_extra={"response_kind": "bailout"},
        )
        handoff_md = (f"# Handoff\n\n## Original goal\n\n{GOAL}\n")
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
        tarball = tar_response_dir(rdir)

        applied = run_bale(self.install, ["apply", str(tarball)],
                           cwd=self.repo, env=self.env)
        self.assertEqual(
            applied.returncode, 0,
            msg=f"stdout:\n{applied.stdout}\nstderr:\n{applied.stderr}")
        self.assertEqual(self.open_sids(), [],
                         msg="apply of the bailout should close its session")
        return sid, tarball

    def handoff(self, tarball: Path, *extra_args: str):
        return run_bale(self.install, ["handoff", str(tarball), *extra_args],
                        cwd=self.repo, env=self.env)

    # -- state readers ---------------------------------------------------

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return sorted(
            d.name for d in root.iterdir() if (d / "open").is_file())

    def sole_new_open_sid(self, bailed_sid: str) -> str:
        opens = self.open_sids()
        self.assertEqual(len(opens), 1,
                         msg=f"expected exactly one open session, got {opens}")
        new_sid = opens[0]
        self.assertNotEqual(new_sid, bailed_sid)
        return new_sid

    def request_manifest(self, sid: str) -> dict:
        p = self.repo / ".bale" / "sessions" / sid / "manifest.json"
        self.assertTrue(p.is_file(), msg=f"no request manifest at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def recorded_scope(self, sid: str) -> list:
        p = self.repo / ".bale" / "sessions" / sid / "scope.json"
        self.assertTrue(p.is_file(), msg=f"no scope.json at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def outbox_tarball(self, sid: str) -> Path:
        p = self.repo / ".bale" / "outbox" / f"request-{sid}.tar.gz"
        self.assertTrue(p.is_file(), msg=f"no request tarball at {p}")
        return p

    # -- the E2Es --------------------------------------------------------

    def test_happy_path_repackages_bailout(self) -> None:
        """The whole job: fresh sid on the same slug, lineage pointer,
        goal verbatim, reading-plan files pre-packed and recorded as
        the forecast, and a request tarball with the full injected
        surface. Default run — quiet (the --verbose parity pin's off
        direction rides here)."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])

        result = self.handoff(tarball)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        # Default off leaves the build byte-quiet (existing behavior
        # unchanged) — no build-trail line on either stream.
        self.assertNotIn(VERBOSE_MARKER, result.stdout)
        self.assertNotIn(VERBOSE_MARKER, result.stderr)

        new_sid = self.sole_new_open_sid(bailed_sid)
        # Same slug, new counter: sid grammar is YYYY-MM-DD-<slug>-NNN.
        self.assertEqual(new_sid[11:-4], SLUG)
        self.assertEqual(bailed_sid[11:-4], SLUG)

        manifest = self.request_manifest(new_sid)
        self.assertEqual(manifest["session_id"], new_sid)
        self.assertEqual(manifest["goal"], GOAL,
                         msg="goal is inherited verbatim from the "
                             "bailed-on request")
        self.assertEqual(
            manifest["depends_on"]["previous_response"], bailed_sid,
            msg="lineage pointer must name the bailout (the only path "
                "that populates previous_response)")
        self.assertIsNone(manifest["depends_on"]["previous_probe"])
        # cmd_handoff resets these deliberately (narrow CLI surface).
        self.assertEqual(manifest["constraints"], [])
        self.assertEqual(manifest["out_of_scope"], [])
        self.assertEqual(manifest["expects_probe"], "claude-decides")
        # handoff.md first, then the reading-plan files — the full
        # context inventory per TARBALL.md §3.2.
        self.assertEqual(manifest["context_included"],
                         ["context/handoff.md", "context/hello.txt"])
        # The reading-plan file set IS the recorded write forecast, and
        # the manifest stamp and the registry record share one value.
        self.assertEqual(manifest["resolved_scope"], ["hello.txt"])
        self.assertEqual(self.recorded_scope(new_sid), ["hello.txt"])

        # The tarball: request-NNN/ with the injected docs and tools
        # (same builder as pack), the manifest, handoff.md AND the
        # pre-packed reading-plan file under context/.
        out = self.outbox_tarball(new_sid)
        with tarfile.open(out) as tf:
            members = {m.name for m in tf.getmembers()}
            nnn = new_sid[-3:]
            prefix = f"request-{nnn}"
            for doc in GLOBAL_DOCS:
                self.assertIn(f"{prefix}/{doc}", members)
            for tool in INJECTED_TOOLS:
                self.assertIn(f"{prefix}/tools/{tool}", members)
            self.assertIn(f"{prefix}/manifest.json", members)
            self.assertIn(f"{prefix}/context/handoff.md", members)
            self.assertIn(f"{prefix}/context/hello.txt", members)
            # The shipped handoff.md is the bailout's, byte for byte.
            shipped = tf.extractfile(f"{prefix}/context/handoff.md").read()
        self.assertIn(GOAL.encode("utf-8"), shipped)

    def test_planless_handoff_resolves_whole_tree(self) -> None:
        """A reading plan citing no files degrades to handoff.md-only
        context — and the session's forecast resolves to ["."], the
        whole tree. Pinned AS-IS per the standing watch: current
        behavior, not a remedy."""
        bailed_sid, tarball = self.packed_and_bailed(reading_plan_paths=None)

        result = self.handoff(tarball)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

        new_sid = self.sole_new_open_sid(bailed_sid)
        manifest = self.request_manifest(new_sid)
        self.assertEqual(manifest["context_included"],
                         ["context/handoff.md"],
                         msg="plan-less handoff ships handoff.md only")
        self.assertEqual(manifest["resolved_scope"], ["."],
                         msg="a plan citing no files resolves to "
                             "whole-tree scope (the shipped fallback)")
        self.assertEqual(self.recorded_scope(new_sid), ["."])
        with tarfile.open(self.outbox_tarball(new_sid)) as tf:
            context_members = [
                m.name for m in tf.getmembers()
                if "/context/" in m.name and m.isfile()]
        self.assertEqual(context_members,
                         [f"request-{new_sid[-3:]}/context/handoff.md"])

    def test_verbose_streams_build_trail(self) -> None:
        """`bale handoff --verbose` streams the build trail (the
        default-off kwarg build_request_tarball already carries), and —
        because handoff's call site runs post-set_log_file — the trail
        lands in the new session's log as well as on stdout."""
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"])

        result = self.handoff(tarball, "--verbose")
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn(VERBOSE_MARKER, result.stdout)
        # A specific trail line, not just the marker: the context copy
        # of the artifact this command exists to ship.
        self.assertIn("verbose: copy context/handoff.md", result.stdout)

        new_sid = self.sole_new_open_sid(bailed_sid)
        log_path = self.repo / ".bale" / "logs" / f"{new_sid}.log"
        self.assertTrue(log_path.is_file(), msg=f"no session log at {log_path}")
        self.assertIn("verbose: copy context/handoff.md",
                      log_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
