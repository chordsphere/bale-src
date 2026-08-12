#!/usr/bin/env python3
"""Sandbox wrapper suite (board 10 S1 — ADR-0016).

Three tiers, cheapest first:

- **Unit** (no namespace spun): the generated prologue carries every
  step of the pinned choreography — private propagation, the strict
  read-only sweep with per-mount loud failure and VFS-flag
  preservation, the fresh proc mount, the tmpfs stage-and-move onto
  ``/tmp`` with pass-through binds, ``-n`` on every mount call — plus
  the environment allowlist, path quoting, the ``network`` keyword's
  ``--net`` toggle, and the self-probe refusal path (a broken
  mechanism refuses loudly, naming ``--no-sandbox``; never silent
  unconfined execution).
- **Behavioral** (one confined spin, mirroring the blind checkpoint's
  probes through ``run_confined`` as a library): an in-staging write
  lands on the host, an outside write does not, ``/dev/tcp`` fails,
  an exported operator variable is invisible, a ``/tmp`` pass-through
  is readable but not writable, and the private ``/tmp`` tmpfs is
  writable.
- **E2E** (two full ``bale pack`` → ``bale apply`` runs): the
  default-on sandbox confines a validation.sh that attempts an
  escape write (the write does not land, the apply still PASSes on
  the script's own verdict), and ``--no-sandbox`` bypasses (the same
  write lands, the session log carries the FORCE line).

Behavioral and E2E tiers skip loudly (unittest.skipUnless with a
named reason) where unprivileged user namespaces are unavailable —
the mechanism's own refusal contract covers real applies there, and
the operator's environment (WSL2, verified) runs the full tier.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring. This
suite's namespace confinement is a different sandbox from ADR-0005's:
0005 isolates the test run from the developer's machine; ADR-0016
isolates response scripts from the operator's. Both apply here.

Run directly::

    python3 tests/test_sandbox_wrapper.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harness import (
    REPO_ROOT,
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

sys.path.insert(0, str(REPO_ROOT / "bin"))
import bale_sandbox  # noqa: E402  (path-injected sibling import)


def _userns_available() -> bool:
    """Can this environment spin the sandbox's namespace set at all?

    A capability probe, not a confinement probe — the real self-probe
    (ensure_verified) asserts the properties; this only decides
    whether the behavioral tiers can run here.
    """
    try:
        r = subprocess.run(
            [bale_sandbox.UNSHARE, *bale_sandbox.UNSHARE_ARGS,
             "true"],
            capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


USERNS_AVAILABLE = _userns_available()
SKIP_REASON = ("unprivileged user namespaces unavailable in this "
               "environment; behavioral confinement assertions run on "
               "the operator's machine (the mechanism's own self-probe "
               "refusal covers real applies here)")


class PrologueUnitTest(unittest.TestCase):
    """The generated prologue carries the pinned choreography."""

    def setUp(self) -> None:
        # The base deliberately sits OUTSIDE /tmp: build_prologue
        # branches on /tmp residence, and the non-/tmp branch is the
        # baseline the operator's real staging (<repo>/.bale/staging)
        # takes. The under-/tmp branch gets its own fixture below.
        self._tmpdir = tempfile.TemporaryDirectory(
            prefix="bale-sbxu-", dir=str(Path.home()))
        self.tmp = Path(self._tmpdir.name)
        self.staging = self.tmp / "staging"
        self.staging.mkdir()
        self.log = self.tmp / "logs" / "s.log"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _prologue(self, **kwargs) -> str:
        return bale_sandbox.build_prologue(
            staging=self.staging, log_path=self.log, **kwargs)

    def test_choreography_steps_present_in_order(self) -> None:
        p = self._prologue()
        steps = [
            "mount --make-rprivate /",           # 1. private propagation
            'remount,bind,ro "$target"',          # 2. per-mount ro
            "findmnt -rn -o TARGET",              # 2. the sweep source
            # (the redirect trails the loop body in bash's
            # `done < <(...)` form, hence this order)
            "mount -n -t proc proc /proc",        # 3. fresh rw proc
            "mount -n -t tmpfs",                  # 4. tmpfs stage
            "mount -n --move",                    # 4. move onto /tmp
            'exec "$@"',                          # 6. the wrapped argv
        ]
        pos = -1
        for step in steps:
            found = p.find(step)
            self.assertGreater(found, pos,
                               msg=f"step missing or out of order: {step}")
            pos = found

    def test_every_mount_call_carries_dash_n(self) -> None:
        # The utab update fails once /run goes read-only, so every
        # mount call after make-rprivate must be -n. make-rprivate
        # itself precedes the sweep and needs no exception made for it.
        p = self._prologue()
        for line in p.splitlines():
            if "mount " in line and "--make-rprivate" not in line:
                self.assertIn("mount -n ", line,
                              msg=f"mount call without -n: {line}")

    def test_sweep_fails_loud_per_mount_with_no_allowlist(self) -> None:
        p = self._prologue()
        sweep = p[p.index("while IFS= read -r target"):p.index("done <")]
        # Loud: the failure names the mount, the error, and the full
        # findmnt record (the post-HOLD diagnostics enrichment).
        self.assertIn('fail "read-only remount failed for $target: $err', p)
        self.assertIn("TARGET,FSTYPE,VFS-OPTIONS,FS-OPTIONS,PROPAGATION", p)
        # Plain remount only: no flag restating rides the call — flag
        # preservation is libmount's merge, and restating flags read
        # from findmnt EPERMs at overmounted paths (the /run/user
        # HOLD). The mount call carries exactly remount,bind,ro.
        self.assertIn('remount,bind,ro "$target"', sweep)
        self.assertNotIn("noatime", sweep)
        self.assertNotIn("$keep", sweep)
        # The only skips are capability-based: duplicate stacked
        # targets, and targets no path resolves to (recorded, and
        # unreachable by the confined child for the same reason).
        self.assertIn('case ",$swept,"', sweep)
        self.assertIn('if ! [ -e "$target" ]; then '
                      'skipped="$skipped $target"', sweep)
        # The skip note lands in the session log, never stdout.
        self.assertIn("sweep skipped shadowed unreachable", p)

    def test_prologue_failure_is_sentinel_prefixed(self) -> None:
        p = self._prologue()
        self.assertIn(bale_sandbox.PROLOGUE_FAILURE_SENTINEL, p)
        self.assertIn(f"exit {bale_sandbox.PROLOGUE_EXIT_CODE}", p)

    def test_tmp_passthrough_binds_are_read_only(self) -> None:
        ckpt = Path(tempfile.mkdtemp(prefix="bale-checkpoint-"))
        try:
            p = self._prologue(tmp_passthrough=[ckpt])
            self.assertIn(f"--bind {ckpt}", p)
            # The bind is remounted ro at its tmpfs-staged location.
            rel = ckpt.relative_to("/tmp")
            self.assertIn(f"remount,bind,ro /mnt/{rel}", p)
        finally:
            ckpt.rmdir()

    def test_writable_paths_split_by_tmp_residence(self) -> None:
        # A writable outside /tmp is bind-remounted rw at its own path;
        # one under /tmp rides the staged tmpfs before the move.
        under = Path(tempfile.mkdtemp(prefix="bale-sbx-under-"))
        try:
            p = self._prologue(extra_writable=[under])
            self.assertIn(f"remount,bind,rw {self.staging}", p)
            rel = under.relative_to("/tmp")
            self.assertIn(f"remount,bind,rw /mnt/{rel}", p)
        finally:
            under.rmdir()

    def test_paths_with_spaces_are_quoted(self) -> None:
        spaced = self.tmp / "stag ing"
        spaced.mkdir()
        p = bale_sandbox.build_prologue(staging=spaced, log_path=self.log)
        self.assertIn(f"cd '{spaced}'", p)

    def test_network_keyword_toggles_dash_dash_net(self) -> None:
        confined = bale_sandbox.confined_command(
            ["true"], staging=self.staging, log_path=self.log)
        self.assertIn("--net", confined)
        granted = bale_sandbox.confined_command(
            ["true"], staging=self.staging, log_path=self.log,
            network=True)
        self.assertNotIn("--net", granted)
        # The filesystem confinement flags survive the grant.
        for flag in ("--user", "--map-root-user", "--mount", "--pid"):
            self.assertIn(flag, granted)

    def test_env_allowlist_scrubs_everything_else(self) -> None:
        os.environ["BALE_SBX_TEST_SECRET"] = "leak"
        try:
            env = bale_sandbox.sandbox_env({"BALE_EXTRA": "yes"})
        finally:
            del os.environ["BALE_SBX_TEST_SECRET"]
        self.assertNotIn("BALE_SBX_TEST_SECRET", env)
        self.assertEqual(env.get("BALE_EXTRA"), "yes")
        for key in env:
            self.assertTrue(
                key in bale_sandbox.ENV_ALLOWLIST or key == "BALE_EXTRA",
                msg=f"unexpected env key passed through: {key}")

    def test_self_probe_refusal_names_the_escape_flag(self) -> None:
        # A broken mechanism (unshare unreachable) must refuse loudly,
        # naming --no-sandbox — never fall through to unconfined runs.
        real, real_flag = bale_sandbox.UNSHARE, bale_sandbox._verified
        bale_sandbox.UNSHARE = str(self.tmp / "no-such-unshare")
        bale_sandbox._verified = False
        try:
            with self.assertRaises(
                    bale_sandbox.SandboxUnavailableError) as ctx:
                bale_sandbox.ensure_verified(self.log)
            self.assertIn("--no-sandbox", str(ctx.exception))
            self.assertFalse(bale_sandbox._verified)
        finally:
            bale_sandbox.UNSHARE = real
            bale_sandbox._verified = real_flag


@unittest.skipUnless(USERNS_AVAILABLE, SKIP_REASON)
class ConfinementBehavioralTest(unittest.TestCase):
    """run_confined as a library: the checkpoint's own probe set."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-sbxb-")
        self.tmp = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_confinement_properties_hold(self) -> None:
        # Staging outside /tmp and an escape target beside it; a
        # checkpoint-shaped ro pass-through under /tmp. One spin covers
        # the property set the blind checkpoint probes.
        base = Path(tempfile.mkdtemp(prefix="bale-sbx-behav-",
                                     dir=str(Path.home())))
        self.addCleanup(lambda: subprocess.run(
            ["rm", "-rf", str(base)], check=False))
        staging = base / "staging"
        staging.mkdir()
        log = base / "logs" / "s.log"
        escape = base / "escape.txt"
        ckpt = Path(tempfile.mkdtemp(prefix="bale-checkpoint-"))
        self.addCleanup(lambda: subprocess.run(
            ["rm", "-rf", str(ckpt)], check=False))
        (ckpt / "current.sh").write_text("echo ckpt-bytes\n",
                                         encoding="utf-8")

        os.environ["BALE_SBX_OPERATOR_SECRET"] = "sekrit"
        try:
            result = bale_sandbox.run_confined(
                ["bash", "-c", f'''
set -u
echo w > in.txt                        && echo "in-write: ok"
echo x > "{escape}" 2>/dev/null        || echo "out-write: denied"
cat "{ckpt}/current.sh" > /dev/null    && echo "passthrough-read: ok"
echo y > "{ckpt}/w" 2>/dev/null        || echo "passthrough-write: denied"
echo t > /tmp/scratch                  && echo "tmpfs-write: ok"
(exec 3<>/dev/tcp/127.0.0.1/9) 2>/dev/null || echo "net: off"
[ -z "${{BALE_SBX_OPERATOR_SECRET:-}}" ]   && echo "env: scrubbed"
'''],
                staging=staging, log_path=log, tmp_passthrough=[ckpt])
        finally:
            del os.environ["BALE_SBX_OPERATOR_SECRET"]

        self.assertEqual(result.returncode, 0, msg=result.stderr)
        for marker in ("in-write: ok", "out-write: denied",
                       "passthrough-read: ok", "passthrough-write: denied",
                       "tmpfs-write: ok", "net: off", "env: scrubbed"):
            self.assertIn(marker, result.stdout)
        # The in-staging write landed on the HOST — confinement is on
        # writes outside staging, not on staging itself.
        self.assertEqual((staging / "in.txt").read_text(), "w\n")
        self.assertFalse(escape.exists(),
                         msg="escape write leaked to the host")

    def test_overmounted_path_with_mismatched_locked_flags(self) -> None:
        """Regression for the first target-machine HOLD: /run/user
        there is an overmount pair — a shadowed noatime mount under a
        topmost relatime mount. The old sweep restated the shadowed
        mount's flags onto the topmost mount and hit the locked-flag
        EPERM; the plain-remount sweep must confine cleanly through
        the same topology (erected here in an outer namespace, so its
        flags are locked for the sandbox exactly as on a real host)."""
        script = f"""
mount --make-rprivate /
mkdir -p /tmp/ru-om /tmp/ru-om-staging /tmp/ru-om-logs
mount -t tmpfs -o nosuid,nodev,noexec,noatime tmpfs /tmp/ru-om
mount -t tmpfs -o relatime tmpfs /tmp/ru-om
cd {shlex.quote(str(REPO_ROOT / "bin"))}
exec python3 - <<'PYEOF'
from pathlib import Path
import bale_sandbox
r = bale_sandbox.run_confined(
    ["bash", "-c", "echo om-ok > probe.txt && cat probe.txt"],
    staging=Path("/tmp/ru-om-staging"),
    log_path=Path("/tmp/ru-om-logs/s.log"))
print("rc:", r.returncode)
print("out:", r.stdout.strip())
print("err:", r.stderr.strip())
PYEOF
"""
        outer = subprocess.run(
            [bale_sandbox.UNSHARE, "--user", "--map-root-user",
             "--mount", "bash", "-c", script],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(outer.returncode, 0, msg=outer.stderr)
        self.assertIn("rc: 0", outer.stdout,
                      msg=f"confined spin failed inside the overmount "
                          f"topology:\n{outer.stdout}\n{outer.stderr}")
        self.assertIn("out: om-ok", outer.stdout)

    def test_self_probe_passes_where_the_mechanism_holds(self) -> None:
        real_flag = bale_sandbox._verified
        bale_sandbox._verified = False
        try:
            bale_sandbox.ensure_verified(self.tmp / "logs" / "s.log")
            self.assertTrue(bale_sandbox._verified)
        finally:
            bale_sandbox._verified = real_flag


@unittest.skipUnless(USERNS_AVAILABLE, SKIP_REASON)
class SandboxApplyE2ETest(unittest.TestCase):
    """The default-on sandbox and its escape, through a real apply."""

    ESCAPE_CHECK = "escape write attempt"

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-sbxe2e-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        result = run_bale(
            self.install,
            ["pack", "sandbox wrapper fixture session",
             "--slug", "sbx",
             "--include", "hello.txt",
             "--no-readme"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        self.sid = sids[0]
        # The escape target lives OUTSIDE the repo (and outside any
        # staging), in the sandboxed HOME — a landed write there is a
        # confinement breach, full stop.
        self.escape = self.home / "escaped.txt"

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _escape_validation_sh(self) -> str:
        # The script itself PASSes either way: the assertion under test
        # is where the write LANDS, not the script's verdict — a
        # confined run must still validate normally (ADR-0016: no
        # legitimate victim).
        return (
            "#!/usr/bin/env bash\n"
            f"echo attempted > \"{self.escape}\" 2>/dev/null || true\n"
            f"echo \"[PASS] {self.ESCAPE_CHECK}\"\n"
            "exit 0\n"
        )

    def _tarball(self) -> Path:
        rdir = build_response_dir(
            self.tmp / "out", self.sid,
            summary="sandbox e2e fixture",
            entries=[{
                "path": "hello.txt", "action": "modified",
                "reason": "fixture edit",
                "data": b"hello sandboxed\n",
            }],
            validation_sh=self._escape_validation_sh(),
            validation_will_run=[self.ESCAPE_CHECK],
            claims={self.ESCAPE_CHECK: "pass"},
        )
        return tar_response_dir(rdir)

    def _session_log(self) -> str:
        return (self.repo / ".bale" / "logs" / f"{self.sid}.log"
                ).read_text(encoding="utf-8")

    def test_default_apply_confines_the_escape_write(self) -> None:
        result = run_bale(
            self.install, ["apply", str(self._tarball()), "--no-interact"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertFalse(
            self.escape.exists(),
            msg="validation.sh escaped the sandbox: the outside write "
                "landed on the host")
        log = self._session_log()
        self.assertIn("confined", log)
        self.assertNotIn("FORCE", log)

    def test_no_sandbox_bypasses_and_force_logs(self) -> None:
        result = run_bale(
            self.install,
            ["apply", str(self._tarball()), "--no-interact",
             "--no-sandbox"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertTrue(
            self.escape.exists(),
            msg="--no-sandbox did not bypass: the unconfined write "
                "should land")
        log = self._session_log()
        self.assertIn("FORCE", log)
        self.assertIn("--no-sandbox", log)
        self.assertIn("UNCONFINED", log)


if __name__ == "__main__":
    unittest.main(verbosity=2)
