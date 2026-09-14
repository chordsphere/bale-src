#!/usr/bin/env python3
"""Shared fixture for the `bale handoff` suites (board 73: session A
wrote the reproductions against 0.4.26; session B modernized the
command at 0.4.28 and re-pointed the suites at the ADR-0015 contract).

``tests/test_handoff_happy.py`` pins the paths handoff walks cleanly.
The three suites that import from here — ``test_handoff_registry_gate``,
``test_handoff_checkpoint_gates``, ``test_handoff_forecast`` — walk the
paths it does not: an open sibling session, a checkpoint-configured
project, a parent session with its own write forecast, and the
forecast flag family. This module carries the fixture they share so
the pack → bailout → apply setup lives once.

Since 0.4.28 a handoff inherits the bailed-on session's recorded
forecast exactly, and the ``["."]`` reading-plan fallback fires only
when that record is missing or unreadable. Every parent this fixture
packs goes through bale, so its record always exists; ``drop_parent_record``
is the knob that removes it, so the fallback branch can be exercised
deliberately rather than by accident.

The happy test's inline fixture is deliberately left untouched (its
three cases are a pinned baseline, and a refactor is not this
session's job); this module re-implements the same shape with the
extra knobs the reproductions need — ``pack_extra`` for the parent
pack's flags, ``slug``, checkpoint configuration, a normal-response
builder for the apply leg — rather than subclassing it.

Discovery note: this file matches the ``test_handoff_`` prefix so a
direct run of any consumer (``python3 tests/test_handoff_forecast.py``)
resolves the bare import the same way discovery does. ``HandoffFixture``
defines no ``test_*`` methods, so discovery collects nothing from it.
It also carries NO class-level ``skipUnless``/``expectedFailure``
decorator — the board-75 notes record a class-level ``@skipUnless``
being inherited by every subclass and silently skipping a whole suite.
Every gate in these suites is per-method.

Sandbox doctrine per ADR-0005 (fully hermetic) — ``tests/harness.py``
carries it. Every invocation is piped (stdin is not a TTY).
"""

from __future__ import annotations

import datetime
import json
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
    run_checked,
    tar_response_dir,
)

GOAL = "handoff reproduction goal: finish rewriting hello.txt"
SLUG = "handoff-repro"

# A {sid}-templated [validation] base, the shape bale-src itself uses,
# and a literal one. Both are hand-written into bale.toml (the wizard is
# canonical, not exclusive — test_blind_checkpoint.py's precedent).
SID_BASE = "claude/checkpoints/{sid}.sh"
LITERAL_BASE = "claude/checkpoint.sh"

PASSING_CHECKPOINT = (
    "#!/usr/bin/env bash\n"
    "echo \"[PASS] blind checkpoint (fixture)\"\n"
    "exit 0\n"
)


class HandoffFixture(unittest.TestCase):
    """Scratch install + scratch repo, plus the handoff-shaped helpers.

    No test methods here. Consumers subclass and add their own.
    """

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-handoff-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- repo shaping ----------------------------------------------------

    def commit_file(self, rel: str, body: str, *, executable: bool = False,
                    message: str = None) -> None:
        """Write and commit one file at `rel` (parents created)."""
        p = self.repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(body, encoding="utf-8")
        if executable:
            p.chmod(0o755)
        run_checked(["git", "add", rel], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", message or f"add {rel}"],
                    cwd=self.repo, env=self.genv)

    def configure_checkpoint(self, base: str) -> None:
        """Commit a bale.toml naming `base` as the blind checkpoint."""
        self.commit_file(
            "bale.toml", f"[validation]\nbase = \"{base}\"\n",
            message="configure blind checkpoint")

    def commit_checkpoint(self, rel: str,
                          body: str = PASSING_CHECKPOINT) -> None:
        """Commit a checkpoint script at `rel` (committed-is-ratified)."""
        self.commit_file(rel, body, executable=True,
                         message=f"pin blind checkpoint {rel}")

    def write_checkpoint_source(self, name: str = "cp.sh",
                                body: str = PASSING_CHECKPOINT) -> Path:
        """A planner's checkpoint file OUTSIDE the repo — the shape
        pack's --checkpoint-file ingests."""
        p = self.tmp / name
        p.write_text(body, encoding="utf-8")
        return p

    def head_sha256(self, rel: str) -> str:
        """sha256 of `rel`'s committed bytes at HEAD."""
        import hashlib
        import subprocess
        r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=self.repo,
                           capture_output=True)
        self.assertEqual(r.returncode, 0, msg=f"expected {rel} at HEAD")
        return hashlib.sha256(r.stdout).hexdigest()

    # -- the pack → bailout → apply setup ----------------------------------

    def pack(self, *extra: str, slug: str = SLUG, goal: str = GOAL):
        """A fully specified piped pack; `extra` appends to the base
        form (which includes hello.txt and forecasts it, absent
        --write/--read-only in `extra`)."""
        return run_bale(
            self.install,
            ["pack", goal, "--slug", slug, "--include", "hello.txt",
             "--no-readme", *extra],
            cwd=self.repo, env=self.env)

    def bare_pack(self, *extra: str, slug: str = "bare"):
        """A bare pack: no --include, no --write — the whole-tree
        include-set default that v0.4.9 made admissible in a
        checkpoint-configured project."""
        return run_bale(
            self.install,
            ["pack", "bare default pack (fixture)", "--slug", slug,
             "--no-readme", *extra],
            cwd=self.repo, env=self.env)

    def assert_ok(self, result, what: str = "bale run") -> None:
        self.assertEqual(
            result.returncode, 0,
            msg=f"{what} failed (exit {result.returncode})\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

    def assert_refused(self, result, what: str = "bale run") -> str:
        """Non-zero exit; returns stdout+stderr for phrase assertions."""
        self.assertNotEqual(
            result.returncode, 0,
            msg=f"{what} unexpectedly succeeded\nstdout:\n{result.stdout}")
        return result.stdout + result.stderr

    def packed_and_bailed(self, *, reading_plan_paths,
                          pack_extra: tuple = (),
                          slug: str = SLUG) -> tuple[str, Path]:
        """Pack a session (with `pack_extra` flags), apply a bailout
        against it, return (bailed_sid, bailout_tarball).

        Mirrors the happy test's fixture: the bailout is built with the
        harness's shared builder plus the two bailout-mandatory
        artifacts; ``handoff.md`` carries a reading plan citing
        `reading_plan_paths` (None omits the section — the plan-less
        shape that resolves to the whole-tree forecast). The apply
        closes the session, which is the state handoff requires.
        """
        packed = self.pack(*pack_extra, slug=slug)
        self.assert_ok(packed, "parent pack")
        opens = self.open_sids()
        self.assertEqual(len(opens), 1, msg=f"open sessions: {opens}")
        sid = opens[0]

        rdir = build_response_dir(
            self.tmp / f"bailout-{slug}", sid,
            summary="bailout fixture: the goal did not fit the budget; "
                    "handoff.md prescribes the next session",
            entries=[],
            validation_will_run=[],
            claims={},
            manifest_extra={"response_kind": "bailout"},
        )
        handoff_md = f"# Handoff\n\n## Original goal\n\n{GOAL}\n"
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
        self.assert_ok(applied, "apply of the bailout")
        self.assertEqual(self.open_sids(), [],
                         msg="apply of the bailout should close its session")
        return sid, tarball

    def handoff(self, tarball: Path, *extra_args: str):
        return run_bale(self.install, ["handoff", str(tarball), *extra_args],
                        cwd=self.repo, env=self.env)

    def drop_parent_record(self, sid: str) -> None:
        """Delete `sid`'s recorded forecast (``scope.json``) so a handoff
        against its bailout takes the no-readable-record fallback:
        the reading-plan file set, or ["."] when the plan cites
        nothing, as an UNDECLARED forecast (v0.4.28). The shape a
        pre-v0.3.2 parent or a cleaned-up record presents."""
        p = self.repo / ".bale" / "sessions" / sid / "scope.json"
        self.assertTrue(p.is_file(), msg=f"no scope.json to drop at {p}")
        p.unlink()

    def apply_normal_response(self, sid: str, *, path: str, data: bytes,
                              tag: str = "resp", extra_args: tuple = ()):
        """Build a normal response for `sid` modifying one file and
        apply it. Returns the apply result (caller asserts)."""
        rdir = build_response_dir(
            self.tmp / f"{tag}-{sid}", sid,
            summary=f"fixture response: rewrites {path}",
            entries=[{"path": path, "action": "modified",
                      "reason": "the resumed work landing", "data": data}])
        return run_bale(
            self.install, ["apply", str(tar_response_dir(rdir)), *extra_args],
            cwd=self.repo, env=self.env)

    # -- state readers ---------------------------------------------------

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return sorted(
            d.name for d in root.iterdir() if (d / "open").is_file())

    def request_manifest(self, sid: str) -> dict:
        p = self.repo / ".bale" / "sessions" / sid / "manifest.json"
        self.assertTrue(p.is_file(), msg=f"no request manifest at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def recorded_scope(self, sid: str) -> list:
        p = self.repo / ".bale" / "sessions" / sid / "scope.json"
        self.assertTrue(p.is_file(), msg=f"no scope.json at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def peeked_sid(self, slug: str = SLUG) -> str:
        """The sid the next allocation WOULD take: today's date, `slug`,
        the per-day counter plus one. Mirrors bin/bale's
        peek_session_id (read from the counter file rather than
        imported, so the test never loads the repo's bin/ into the
        test process — the install under test is the scratch copy).
        """
        day = datetime.date.today().isoformat()
        counter = self.repo / ".bale" / f"counter-{day}"
        n = 1
        if counter.exists():
            n = int(counter.read_text().strip()) + 1
        return f"{day}-{slug}-{n:03d}"

    def sole_new_open_sid(self, bailed_sid: str) -> str:
        opens = self.open_sids()
        self.assertEqual(len(opens), 1,
                         msg=f"expected exactly one open session, got {opens}")
        self.assertNotEqual(opens[0], bailed_sid)
        return opens[0]
