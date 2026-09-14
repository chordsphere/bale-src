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
- **E2E** (full ``bale pack`` → ``bale apply`` runs): the
  default-on sandbox confines a validation.sh that attempts an
  escape write (the write does not land, the apply still PASSes on
  the script's own verdict), and ``--no-sandbox`` bypasses (the same
  write lands, the session log carries the FORCE line).

Board 10 S2 additions (v0.4.5 — the ADR-0016 position-3 network
grant and the sandbox telemetry stamps) ride the same tiers:

- **Unit**: `[sandbox] network` config semantics (absent = the
  network-off floor; project-layer only — a global `[sandbox]` is
  never inherited), the wizard's discoverable-surface contract for
  the key (project walks it, global never does), the telemetry
  builder's unconditional `sandbox_escaped` /
  `network_grant_exercised` stamps, and the schema carrying both
  field names as additive non-required booleans (old records keep
  validating).
- **Behavioral**: `run_confined(network=True)` sees the parent
  namespace's interfaces while filesystem confinement holds
  (capability-gated on the invoking environment having a
  non-loopback interface — nested inside an ungranted outer sandbox
  there is nothing beyond ``lo`` to see); the default keeps the
  child's network namespace loopback-only. Interface visibility is
  probed via ``/proc/net/dev`` — netns-accurate because the prologue
  mounts a fresh proc — never ``/sys/class/net``, whose inherited
  sysfs instance keeps showing the MOUNTING namespace's devices
  inside ``unshare --net`` (verified empirically; a sysfs-based
  probe would misread the floor as breached).
- **E2E**: a committed ``bale.toml`` ``[sandbox] network = true``
  grant makes the confined scripts run with network (the session log
  says GRANTED, the applied attempt stamps
  ``network_grant_exercised: true``); the default apply stays
  loopback-only inside validation.sh and stamps both fields false;
  ``--no-sandbox`` beside a configured grant stamps
  ``sandbox_escaped: true`` with ``network_grant_exercised: false``
  — nothing confined ran, so no grant was exercised.

Board 75 additions (v0.4.26 — sandbox-off by config, ``[sandbox]
enabled``) ride the same tiers:

- **Unit**: ``[sandbox] enabled`` config semantics (absent = confined,
  the default; ``false`` disables; a global ``[sandbox] enabled``
  is never inherited, exactly like ``network``; a non-bool is fatal),
  the wizard's discoverable-surface contract for the key (project
  walks it, global never does, an Enter-through re-run preserves a
  set ``false``), the telemetry builder's unconditional
  ``sandbox_confined`` / ``sandbox_off_source`` posture pair, the
  schema carrying both as additive non-required fields with a closed
  ``sandbox_off_source`` enum, and ``validate_telemetry_record``
  enforcing that enum record-wide (null-tolerant) while legacy
  records without the pair keep validating.
- **E2E, deliberately NOT gated on user namespaces**: a committed
  ``[sandbox] enabled = false`` makes the apply run ``validation.sh``
  unconfined (the escape write lands), the session log carries a
  FORCE line naming ``bale.toml [sandbox] enabled = false`` as the
  source, and the applied attempt stamps ``sandbox_confined: false``
  / ``sandbox_off_source: "config"`` with ``sandbox_escaped: false``;
  the same beside a typed ``--no-sandbox`` prints both FORCE lines
  and records ``"config"`` with ``sandbox_escaped: true``; and a
  configured network grant beside config-off is not exercised. This
  tier runs on the motivating host (no namespaces) by construction —
  nothing confined runs — which is exactly the point: the
  namespace-gated E2E class above pins the confined default and the
  flag path, and gains one case pinning that a default apply stamps
  the posture pair's known-negative form (``true`` / ``null``) and
  that ``--no-sandbox`` alone records ``"flag"``.

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

import importlib.util
import json
import os
import shlex
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Optional

from harness import (
    REPO_ROOT,
    bale_env,
    build_response_dir,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_bale_pty,
    run_checked,
    slow,
    tar_response_dir,
)

sys.path.insert(0, str(REPO_ROOT / "bin"))
import bale_sandbox  # noqa: E402  (path-injected sibling import)
import bale_config  # noqa: E402  (path-injected sibling import)


def _proc_net_ifaces(dev_text: str) -> list[str]:
    """Interface names from /proc/net/dev content (the netns-accurate
    probe surface — see the module docstring's behavioral note)."""
    names = []
    for line in dev_text.splitlines()[2:]:
        if ":" in line:
            names.append(line.split(":", 1)[0].strip())
    return names


def _current_netns_ifaces() -> list[str]:
    """The invoking environment's own interfaces, for capability gates."""
    try:
        return _proc_net_ifaces(
            Path("/proc/net/dev").read_text(encoding="utf-8"))
    except OSError:
        return []


HAS_NON_LOOPBACK = any(n != "lo" for n in _current_netns_ifaces())
NON_LOOPBACK_SKIP = (
    "the invoking environment's network namespace has no non-loopback "
    "interface (e.g. this suite is itself running inside an ungranted "
    "sandbox), so a granted child would inherit nothing beyond lo — "
    "the visibility assertion is vacuous here and runs where the "
    "namespace carries real interfaces")


def load_bale_report():
    """Import bin/bale_report.py by path for the unit-shaped stamp
    assertions (the test_closure_telemetry precedent — its top-level
    imports are stdlib-only, so it loads standalone)."""
    path = REPO_ROOT / "bin" / "bale_report.py"
    spec = importlib.util.spec_from_file_location(
        "bale_report_under_sandbox_test", str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _probe_writable_non_tmp_base() -> tuple:
    """Capability probe: a writable directory OUTSIDE /tmp.

    Returns (base_or_None, findings) where findings is one line per
    candidate — what was probed and what was found — so the caller's
    run/skip decision is self-diagnosing wherever the suite ran.
    Probes the capability itself (an mkdir in each candidate), never
    the environment's name.
    """
    findings = []
    for label, candidate in (("HOME", Path.home()), ("cwd", Path.cwd())):
        if str(candidate).startswith("/tmp"):
            findings.append(
                f"{label}={candidate}: /tmp-resident (rides the private "
                f"tmpfs, cannot exercise the non-/tmp branch)")
            continue
        probe = None
        try:
            probe = tempfile.mkdtemp(prefix="bale-sbx-wprobe-",
                                     dir=str(candidate))
            findings.append(f"{label}={candidate}: writable")
            return str(candidate), findings
        except OSError as e:
            findings.append(
                f"{label}={candidate}: mkdir denied "
                f"({e.__class__.__name__}: {e})")
            continue
        finally:
            if probe:
                os.rmdir(probe)
    return None, findings


# One probe per process, its result printed once (run or skip alike) so
# every run is self-diagnosing — the exchange-answered compensating
# instruction alongside constraint 3: guards print what they probed,
# what they found, and the decision.
_NON_TMP_BASE_PROBE: Optional[tuple] = None


def writable_non_tmp_base() -> str:
    """A writable directory OUTSIDE /tmp for the fixtures that
    exercise build_prologue's non-/tmp branch.

    HOME is the S1 choice and stays the first preference. But when
    this suite itself runs CONFINED — a validation.sh under the
    ADR-0016 sandbox, live since the first sandboxed apply (v0.4.5,
    board 10 S2) — HOME is swept read-only, and the S1 fixtures
    errored in setUp. Inside a confined validation the working
    directory is staging: writable by construction and outside /tmp
    (<repo>/.bale/staging/<sid>), so it exercises exactly the same
    prologue branch. Probe HOME first, fall back to cwd.

    When NEITHER candidate holds — HOME swept read-only AND the cwd
    /tmp-resident, the confined open-time grading topology (dry-run
    staging under /tmp; observed at the board-67 grading dry-run) —
    the capability is legitimately absent: no fixture for the
    non-/tmp prologue branch can be staged anywhere. That is a
    counted, loud unittest skip (capability-probed, never
    environment-name-matched), not a failure: the wrapper itself is
    sound, and the branch's tests run wherever a non-/tmp writable
    base exists (every unconfined run, and confined runs whose cwd
    is a writable non-/tmp staging).
    """
    global _NON_TMP_BASE_PROBE
    if _NON_TMP_BASE_PROBE is None:
        _NON_TMP_BASE_PROBE = _probe_writable_non_tmp_base()
        base, findings = _NON_TMP_BASE_PROBE
        decision = "run" if base else "skip"
        print(f"[capability-probe] writable-non-tmp-base: "
              f"{'; '.join(findings)}; decision: {decision}")
    base, findings = _NON_TMP_BASE_PROBE
    if base is None:
        raise unittest.SkipTest(
            "capability absent: no writable non-/tmp directory "
            f"({'; '.join(findings)}) — the prologue's non-/tmp fixture "
            "branch cannot be staged here; these cases run where the "
            "capability holds")
    return base


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
        # writable_non_tmp_base (v0.4.5): HOME when writable, else
        # cwd — HOME is read-only when this suite itself runs inside
        # a confined validation.sh.
        self._tmpdir = tempfile.TemporaryDirectory(
            prefix="bale-sbxu-", dir=writable_non_tmp_base())
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
            "mnt_id",                             # 2. the kernel-truth
            # reachability annotator (fdinfo mnt_id, never the mount
            # table — the v0.4.5 WSL2 fix), defined as a quoted
            # heredoc before its capture
            "findmnt -rn -o TARGET",              # 2. the sweep source,
            # piped through the annotator and CAPTURED (fail-closed)
            # before the loop consumes it — since v0.4.5 the source
            # precedes the loop body, unlike the old `done < <(...)`
            # form where the redirect trailed it
            'remount,bind,ro "$target"',          # 2. per-mount ro
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
        sweep = p[p.index("while IFS= read -r entry"):p.index('done <<< "$entries"')]
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
        # targets, and targets the kernel says no path resolves INTO
        # (the v0.4.5 fdinfo-mnt_id reachability fix — the mount
        # table's own answer is shadowing-blind, per the WSL2
        # shadowed-submount HOLD). Recorded, and unreachable by the
        # confined child for the same reason.
        self.assertIn('case ",$swept,"', sweep)
        self.assertIn('if [ "$mark" != "R" ]; then '
                      'skipped="$skipped $target"', sweep)
        self.assertIn("mnt_id", p)
        self.assertIn("O_PATH", p)
        # Fail-closed plumbing: a broken annotator must refuse, never
        # yield an unswept (writable) tree.
        self.assertIn("refusing an unswept tree", p)
        self.assertIn('[ -n "$entries" ]', p)
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


class NetworkGrantConfigUnitTest(unittest.TestCase):
    """[sandbox] network config semantics + the telemetry stamps + the
    schema's additive fields (v0.4.5, board 10 S2). Pure unit tier —
    no namespace, no subprocess."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-sbxgrant-")
        self.tmp = Path(self._tmpdir.name)
        # Hermeticity (ADR-0005): merged_config resolves the global
        # layer through the module-level GLOBAL_CONFIG_PATH; point it
        # at a temp location so the test neither reads nor depends on
        # any real user/ subtree.
        self._saved_global = bale_config.GLOBAL_CONFIG_PATH
        self.global_toml = self.tmp / "user" / "bale.toml"
        bale_config.GLOBAL_CONFIG_PATH = self.global_toml
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        # bale_config's loaders/accessors lazily import fail from
        # __main__ (bin/bale provides it in production). Inject a
        # raising stand-in for direct-import unit runs — the
        # test_craft_response __main__-injection precedent. On the
        # happy paths under test it is never called.
        self._main = sys.modules["__main__"]
        self._had_fail = hasattr(self._main, "fail")
        self._saved_fail = getattr(self._main, "fail", None)

        def _fail(msg):
            raise AssertionError(f"bale fail(): {msg}")
        self._main.fail = _fail

    def tearDown(self) -> None:
        if self._had_fail:
            self._main.fail = self._saved_fail
        else:
            delattr(self._main, "fail")
        bale_config.GLOBAL_CONFIG_PATH = self._saved_global
        self._tmpdir.cleanup()

    def test_absent_key_is_the_network_off_floor(self) -> None:
        cfg = bale_config.merged_config(self.repo)
        self.assertFalse(bale_config.get_sandbox_network(cfg))

    def test_project_true_grants(self) -> None:
        (self.repo / "bale.toml").write_text(
            "[sandbox]\nnetwork = true\n", encoding="utf-8")
        cfg = bale_config.merged_config(self.repo)
        self.assertTrue(bale_config.get_sandbox_network(cfg))

    def test_project_false_is_explicit_floor(self) -> None:
        (self.repo / "bale.toml").write_text(
            "[sandbox]\nnetwork = false\n", encoding="utf-8")
        cfg = bale_config.merged_config(self.repo)
        self.assertFalse(bale_config.get_sandbox_network(cfg))

    def test_global_sandbox_section_is_never_inherited(self) -> None:
        """The project-only ruling (SANDBOX_VALUES): a hand-edited
        global [sandbox] must not grant network to every repo the
        install touches — merged_config drops it entirely."""
        self.global_toml.parent.mkdir(parents=True)
        self.global_toml.write_text(
            "[sandbox]\nnetwork = true\n", encoding="utf-8")
        cfg = bale_config.merged_config(self.repo)
        self.assertNotIn("sandbox", cfg,
                         msg="a global [sandbox] leaked into the merge")
        self.assertFalse(bale_config.get_sandbox_network(cfg))

    def test_builder_stamps_are_unconditional_booleans(self) -> None:
        """build_telemetry_attempt writes both stamps on every attempt
        (the overridden_paths posture): defaults false, passed values
        recorded verbatim — key presence is S2 epoch membership."""
        bale_report = load_bale_report()
        default = bale_report.build_telemetry_attempt(
            outcome="unlocked", command="unlock",
            tarball=None, manifest=None, scope=[],
            log_path=".bale/logs/x.log")
        self.assertIs(default.get("sandbox_escaped"), False)
        self.assertIs(default.get("network_grant_exercised"), False)
        stamped = bale_report.build_telemetry_attempt(
            outcome="applied", command="apply",
            tarball="t.tar.gz", manifest={"summary": "s"}, scope=[],
            log_path=".bale/logs/x.log",
            sandbox_escaped=True, network_grant_exercised=True)
        self.assertIs(stamped.get("sandbox_escaped"), True)
        self.assertIs(stamped.get("network_grant_exercised"), True)

    def test_schema_carries_both_fields_as_additive_booleans(self) -> None:
        """The exact pinned names live in the telemetry schema as
        attempts[] booleans, and neither joins required — pre-S2
        records keep validating."""
        schema = json.loads(
            (REPO_ROOT / "schemas" / "telemetry-record.schema.json")
            .read_text(encoding="utf-8"))
        items = schema["properties"]["attempts"]["items"]
        props = items["properties"]
        for name in ("sandbox_escaped", "network_grant_exercised"):
            self.assertIn(name, props)
            self.assertEqual(props[name]["type"], "boolean")
            self.assertNotIn(name, items.get("required", []),
                             msg=f"{name} must stay additive — old "
                                 f"records without it must validate")


class SandboxEnabledConfigUnitTest(NetworkGrantConfigUnitTest):
    """[sandbox] enabled config semantics + the posture-pair stamps +
    the schema's additive fields + the validator's closed vocabulary
    (v0.4.26, board 75). Inherits the hermetic setUp/tearDown (and,
    harmlessly, the network cases) from the S2 class above — same
    section, same project-only ruling, same __main__ fail stand-in."""

    def test_absent_key_is_confined_by_default(self) -> None:
        cfg = bale_config.merged_config(self.repo)
        self.assertTrue(bale_config.get_sandbox_enabled(cfg))

    def test_absent_section_is_confined_by_default(self) -> None:
        (self.repo / "bale.toml").write_text(
            "[apply]\nauto_open = false\n", encoding="utf-8")
        cfg = bale_config.merged_config(self.repo)
        self.assertTrue(bale_config.get_sandbox_enabled(cfg))

    def test_project_false_disables(self) -> None:
        (self.repo / "bale.toml").write_text(
            "[sandbox]\nenabled = false\n", encoding="utf-8")
        cfg = bale_config.merged_config(self.repo)
        self.assertFalse(bale_config.get_sandbox_enabled(cfg))

    def test_project_true_is_the_explicit_default(self) -> None:
        (self.repo / "bale.toml").write_text(
            "[sandbox]\nenabled = true\n", encoding="utf-8")
        cfg = bale_config.merged_config(self.repo)
        self.assertTrue(bale_config.get_sandbox_enabled(cfg))

    def test_enabled_and_network_coexist(self) -> None:
        (self.repo / "bale.toml").write_text(
            "[sandbox]\nnetwork = true\nenabled = false\n",
            encoding="utf-8")
        cfg = bale_config.merged_config(self.repo)
        self.assertFalse(bale_config.get_sandbox_enabled(cfg))
        self.assertTrue(bale_config.get_sandbox_network(cfg))

    def test_non_bool_is_fatal_not_a_silent_default(self) -> None:
        (self.repo / "bale.toml").write_text(
            '[sandbox]\nenabled = "false"\n', encoding="utf-8")
        cfg = bale_config.merged_config(self.repo)
        with self.assertRaises(AssertionError) as ctx:
            bale_config.get_sandbox_enabled(cfg)
        self.assertIn("sandbox.enabled", str(ctx.exception))

    def test_global_enabled_false_is_never_inherited(self) -> None:
        """The project-only ruling applied to the new key: a global
        `enabled = false` must not silently unconfine every repo the
        install touches — merged_config drops the section, and the
        accessor reads confined."""
        self.global_toml.parent.mkdir(parents=True)
        self.global_toml.write_text(
            "[sandbox]\nenabled = false\n", encoding="utf-8")
        cfg = bale_config.merged_config(self.repo)
        self.assertNotIn("sandbox", cfg,
                         msg="a global [sandbox] leaked into the merge")
        self.assertTrue(bale_config.get_sandbox_enabled(cfg))

    def test_enabled_is_in_sandbox_values(self) -> None:
        """The trio contract's anchor: the renderer and the wizard both
        iterate SANDBOX_VALUES, so membership is what makes the key
        round-trip through `bale config init`."""
        self.assertIn("enabled", bale_config.SANDBOX_VALUES)

    def test_renderer_emits_the_key(self) -> None:
        rendered = bale_config.render_bale_toml(
            {"sandbox": {"network": False, "enabled": False}})
        self.assertIn("[sandbox]", rendered)
        self.assertIn("enabled = false", rendered)

    def test_builder_posture_pair_is_unconditional(self) -> None:
        """build_telemetry_attempt stamps the pair on every attempt: the
        known-negative form is confined=True / source=None (an unlock
        attempt, nothing ran); passed values are recorded verbatim."""
        bale_report = load_bale_report()
        default = bale_report.build_telemetry_attempt(
            outcome="unlocked", command="unlock",
            tarball=None, manifest=None, scope=[],
            log_path=".bale/logs/x.log")
        self.assertIs(default.get("sandbox_confined"), True)
        self.assertIn("sandbox_off_source", default,
                      msg="the key is present even when null — uniform "
                          "shape, key presence is epoch membership")
        self.assertIsNone(default["sandbox_off_source"])
        for source in ("config", "flag"):
            stamped = bale_report.build_telemetry_attempt(
                outcome="applied", command="apply",
                tarball="t.tar.gz", manifest={"summary": "s"}, scope=[],
                log_path=".bale/logs/x.log",
                sandbox_confined=False, sandbox_off_source=source)
            self.assertIs(stamped["sandbox_confined"], False)
            self.assertEqual(stamped["sandbox_off_source"], source)

    def test_schema_carries_the_pair_additively(self) -> None:
        schema = json.loads(
            (REPO_ROOT / "schemas" / "telemetry-record.schema.json")
            .read_text(encoding="utf-8"))
        items = schema["properties"]["attempts"]["items"]
        props = items["properties"]
        self.assertEqual(props["sandbox_confined"]["type"], "boolean")
        # Three writers since v0.4.27 (board 78): the sandbox-
        # unavailable y/N joined the config key and the flag.
        self.assertEqual(sorted(x for x in props["sandbox_off_source"]["enum"]
                                if x is not None),
                         ["config", "flag", "prompt"])
        self.assertIn(None, props["sandbox_off_source"]["enum"])
        for name in ("sandbox_confined", "sandbox_off_source"):
            self.assertNotIn(name, items.get("required", []),
                             msg=f"{name} must stay additive")

    def test_writer_tuple_mirrors_the_schema_enum(self) -> None:
        bale_report = load_bale_report()
        schema = json.loads(
            (REPO_ROOT / "schemas" / "telemetry-record.schema.json")
            .read_text(encoding="utf-8"))
        enum = (schema["properties"]["attempts"]["items"]["properties"]
                ["sandbox_off_source"]["enum"])
        self.assertEqual([v for v in enum if v is not None],
                         list(bale_report.SANDBOX_OFF_SOURCES))

    def _minimal_record(self, **attempt_extra) -> dict:
        """A smallest-valid record (the test_telemetry_extensions
        shape): the required envelope plus one minimal attempt."""
        attempt = {"at": "2026-09-10T00:00:00+00:00",
                   "outcome": "applied", "command": "apply"}
        attempt.update(attempt_extra)
        return {"record_version": 1,
                "session_id": "2026-09-10-fx-sbx-001",
                "created_at": "2026-09-10T00:00:00+00:00",
                "updated_at": "2026-09-10T00:00:00+00:00",
                "outcome": "applied",
                "attempts": [attempt]}

    def test_validator_accepts_the_pair_and_legacy_records(self) -> None:
        import bale_validate
        legacy = self._minimal_record()
        self.assertEqual(bale_validate.validate_telemetry_record(legacy),
                         [], msg="a pre-v0.4.26 record keeps validating")
        for confined, source in ((True, None), (False, "config"),
                                 (False, "flag")):
            rec = self._minimal_record(sandbox_confined=confined,
                                       sandbox_off_source=source)
            self.assertEqual(
                bale_validate.validate_telemetry_record(rec), [],
                msg=f"confined={confined} source={source!r} must validate")

    def test_validator_rejects_invented_source_at_any_depth(self) -> None:
        """The closed-vocabulary walk (the S5 discipline): an invented
        sandbox_off_source rejects at the named spot AND at a spot the
        schema never enumerated, so a consumer's placement choice
        cannot route around the enum."""
        import bale_validate
        rec = self._minimal_record(sandbox_confined=False,
                                   sandbox_off_source="vibes")
        errors = bale_validate.validate_telemetry_record(rec)
        self.assertTrue(any("sandbox_off_source" in e for e in errors),
                        msg=f"named spot must reject: {errors}")
        rec = self._minimal_record()
        rec["attempts"][0]["future_sibling"] = {
            "sandbox_off_source": "operator-said-so"}
        errors = bale_validate.validate_telemetry_record(rec)
        self.assertTrue(any("sandbox_off_source" in e for e in errors),
                        msg="nested invented source must reject")
        rec = self._minimal_record()
        rec["sandbox_off_source"] = None  # envelope-level null: tolerated
        self.assertEqual(bale_validate.validate_telemetry_record(rec), [])


class NetworkGrantWizardSurfaceTest(unittest.TestCase):
    """The discoverable-surface contract for sandbox.network (BALE.md
    §3.6): the project wizard walks it and preserves a set key on an
    Enter-through re-run; the global wizard never offers it (the
    project-only ruling). The test_blind_checkpoint PTY precedent."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-sbxwiz-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, home=self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_project_wizard_walks_and_preserves_the_key(self) -> None:
        (self.repo / "bale.toml").write_text(
            "[sandbox]\nnetwork = true\n", encoding="utf-8")
        code, output = run_bale_pty(
            self.install, ["config", "init"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("sandbox.network", output,
                      msg="the project wizard walks the key — the "
                          "discoverable-surface contract")
        rendered = (self.repo / "bale.toml").read_text(encoding="utf-8")
        self.assertIn("[sandbox]", rendered)
        self.assertIn("network = true", rendered,
                      msg="Enter-through re-runs preserve the granted "
                          "value — the renderer-preservation precedent")

    def test_global_wizard_never_walks_the_key(self) -> None:
        code, output = run_bale_pty(
            self.install, ["config", "init", "--global"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertNotIn("sandbox.network", output,
                         msg="the global wizard must not offer a "
                             "project-only key")
        self.assertNotIn("sandbox.enabled", output,
                         msg="the global wizard must not offer the "
                             "project-only enabled key either (v0.4.26)")

    def test_project_wizard_walks_and_preserves_enabled(self) -> None:
        """The v0.4.26 key rides the same contract: walked in project
        mode (BALE.md §3.6 — an un-walked configurable is a contract
        violation), an Enter-through re-run preserves a set `false`,
        and the effective line never tells the operator an absent key
        means the sandbox is off."""
        (self.repo / "bale.toml").write_text(
            "[sandbox]\nenabled = false\n", encoding="utf-8")
        code, output = run_bale_pty(
            self.install, ["config", "init"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("sandbox.enabled", output)
        self.assertIn("NEVER silent", output,
                      msg="the prompt states the loudness guarantee")
        rendered = (self.repo / "bale.toml").read_text(encoding="utf-8")
        self.assertIn("enabled = false", rendered,
                      msg="Enter-through re-runs preserve the disabling "
                          "value — the renderer-preservation precedent")

    def test_project_wizard_enter_leaves_sandbox_on(self) -> None:
        """A fresh project pressing Enter through the walk ends with no
        `enabled` key at all — confined stays the default and the
        effective line reads ON, not the generic 'off'."""
        code, output = run_bale_pty(
            self.install, ["config", "init"],
            cwd=self.repo, env=self.env, answers="\n" * 40)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("(unset — sandbox ON)", output)
        rendered = (self.repo / "bale.toml").read_text(encoding="utf-8") \
            if (self.repo / "bale.toml").is_file() else ""
        self.assertNotIn("enabled", rendered)


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
                                     dir=writable_non_tmp_base()))
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

    def test_shadowed_submount_is_skipped_not_fatal(self) -> None:
        """Regression for the second target-machine HOLD (first
        sandboxed apply, WSL2): a submount shadowed by a later mount
        over an ANCESTOR path stays listed in the inherited mount
        table while its mountpoint directory still exists in the
        shadowing filesystem — the sweep's old existence check passed
        it and the remount died EINVAL ("not mounted"). Canonically:
        the level-1 prologue's own fresh /proc shadows an inherited
        /proc/sys/fs/binfmt_misc submount, so every level-2 spin
        (nested sandboxes — the E2E suites inside a confined
        validation) failed. The topology is erected here explicitly
        (the bind's source carries the same relative path, so the
        phantom's path EXISTS post-shadowing); reachability must now
        come from the kernel (fdinfo mnt_id), the phantom must be
        skipped and named in the log, and the spin must succeed."""
        script = f"""
mount --make-rprivate /
mkdir -p /tmp/shadow-src/sub /tmp/shadow-base /tmp/sh-stag /tmp/sh-logs
mount -t tmpfs tmpfs /tmp/shadow-base
mkdir /tmp/shadow-base/sub
mount -t tmpfs tmpfs /tmp/shadow-base/sub
mount --bind /tmp/shadow-src /tmp/shadow-base
cd {shlex.quote(str(REPO_ROOT / "bin"))}
exec python3 - <<'PYEOF'
from pathlib import Path
import bale_sandbox
r = bale_sandbox.run_confined(
    ["bash", "-c", "echo shadow-ok"],
    staging=Path("/tmp/sh-stag"), log_path=Path("/tmp/sh-logs/s.log"))
print("rc:", r.returncode)
print("out:", r.stdout.strip())
print("err:", (r.stderr or "").strip()[:300])
log = Path("/tmp/sh-logs/s.log").read_text(encoding="utf-8")
skips = [l for l in log.splitlines() if "skipped" in l]
print("skips:", skips)
PYEOF
"""
        outer = subprocess.run(
            [bale_sandbox.UNSHARE, "--user", "--map-root-user",
             "--mount", "bash", "-c", script],
            capture_output=True, text=True, timeout=60)
        self.assertEqual(outer.returncode, 0, msg=outer.stderr)
        self.assertIn("rc: 0", outer.stdout,
                      msg=f"confined spin failed under the shadowed-"
                          f"submount topology:\n{outer.stdout}\n"
                          f"{outer.stderr}")
        self.assertIn("out: shadow-ok", outer.stdout)
        self.assertIn("/tmp/shadow-base/sub", outer.stdout,
                      msg="the phantom must be skipped BY NAME in the "
                          "session log — silent skipping hides "
                          "environment drift")

    def test_self_probe_passes_where_the_mechanism_holds(self) -> None:
        real_flag = bale_sandbox._verified
        bale_sandbox._verified = False
        try:
            bale_sandbox.ensure_verified(self.tmp / "logs" / "s.log")
            self.assertTrue(bale_sandbox._verified)
        finally:
            bale_sandbox._verified = real_flag

    def _iface_probe(self, *, network: bool):
        """Spin run_confined listing /proc/net/dev (netns-accurate:
        the prologue mounts fresh proc; inherited /sys/class/net is
        NOT — it keeps showing the mounting namespace's devices, per
        the module-docstring note) and return the interface list."""
        staging = self.tmp / f"stag-net-{int(network)}"
        staging.mkdir()
        result = bale_sandbox.run_confined(
            ["bash", "-c", "cat /proc/net/dev"],
            staging=staging,
            log_path=self.tmp / "logs" / "s.log",
            network=network,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        return _proc_net_ifaces(result.stdout)

    def test_network_floor_is_loopback_only(self) -> None:
        """The default child netns carries lo and nothing else — the
        confinement floor the grant must never move (offline-safe: an
        interface listing needs no egress)."""
        ifaces = self._iface_probe(network=False)
        self.assertIn("lo", ifaces)
        self.assertEqual(
            [n for n in ifaces if n != "lo"], [],
            msg=f"non-loopback interface visible on the floor: {ifaces}")

    @unittest.skipUnless(HAS_NON_LOOPBACK, NON_LOOPBACK_SKIP)
    def test_network_grant_keeps_fs_confinement(self) -> None:
        """network=True inherits the parent namespace's interfaces
        (visibility, not egress — the offline-safe assertable property)
        while the filesystem legs hold: an outside write is still
        denied under the grant. Capability-gated per the S1 tier
        pattern: inside an ungranted outer sandbox the parent netns
        has only lo, so there is nothing beyond lo to inherit."""
        ifaces = self._iface_probe(network=True)
        self.assertTrue(
            any(n != "lo" for n in ifaces),
            msg=f"granted child saw no non-loopback interface: {ifaces}")
        # The grant relaxes the network leg ONLY. The escape target
        # sits under /tmp, which the sandbox replaces with a private
        # tmpfs — so the child's write may "succeed" into the decoy;
        # the confinement property is that the HOST path stays
        # untouched, and that is the assertion (the S1 behavioral
        # test's own posture for /tmp-resident targets).
        staging = self.tmp / "stag-net-fs"
        staging.mkdir()
        outside = self.tmp / "net-grant-escape.txt"
        result = bale_sandbox.run_confined(
            ["bash", "-c",
             f"echo w > {shlex.quote(str(outside))} 2>/dev/null; true"],
            staging=staging,
            log_path=self.tmp / "logs" / "s.log",
            network=True,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertFalse(outside.exists(),
                         msg="the network grant loosened the "
                             "filesystem confinement: the outside "
                             "write landed on the host")


class _SandboxApplyFixture(unittest.TestCase):
    """The shared E2E fixture: a hermetic install + packed repo, the
    escape-write validation.sh, the grant helper, log and telemetry
    readers. No tests of its own. Split out of SandboxApplyE2ETest at
    v0.4.26 so the config-off tier below can reuse it WITHOUT
    inheriting the namespace gate — a class-level skipUnless is
    inherited by subclasses, and the config-off cases must run
    precisely where namespaces are absent."""

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

    def _latest_attempt(self) -> dict:
        record = json.loads(
            (self.repo / "claude" / "telemetry" / f"{self.sid}.json")
            .read_text(encoding="utf-8"))
        self.assertTrue(record["attempts"])
        return record["attempts"][-1]

    def _grant_network(self) -> None:
        """Commit bale.toml's [sandbox] network grant. Hand-edit is a
        valid write path (the wizard is canonical, not exclusive);
        committed so the pre-flight clean-tree guard stays satisfied,
        and committed-after-pack is fine — apply resolves its base at
        apply time."""
        (self.repo / "bale.toml").write_text(
            "[sandbox]\nnetwork = true\n", encoding="utf-8")
        env = git_env(self.home)
        run_checked(["git", "add", "bale.toml"], cwd=self.repo, env=env)
        run_checked(["git", "commit", "-m", "grant sandbox network"],
                    cwd=self.repo, env=env)

    IFACE_CHECK = "interface listing"

    def _iface_validation_sh(self) -> str:
        """A validation.sh printing one `iface:<name>` line per
        interface from /proc/net/dev — netns-accurate through the
        sandbox's fresh proc mount (never /sys/class/net; the module
        docstring owns the sysfs caveat) — then PASSing. Offline-safe:
        visibility, not egress."""
        return (
            "#!/usr/bin/env bash\n"
            "awk -F: 'NR>2 {gsub(/ /, \"\", $1); print \"iface:\" $1}'"
            " /proc/net/dev\n"
            f"echo \"[PASS] {self.IFACE_CHECK}\"\n"
            "exit 0\n"
        )

    def _iface_tarball(self) -> Path:
        rdir = build_response_dir(
            self.tmp / "out", self.sid,
            summary="sandbox network-grant e2e fixture",
            entries=[{
                "path": "hello.txt", "action": "modified",
                "reason": "fixture edit",
                "data": b"hello granted\n",
            }],
            validation_sh=self._iface_validation_sh(),
            validation_will_run=[self.IFACE_CHECK],
            claims={self.IFACE_CHECK: "pass"},
        )
        return tar_response_dir(rdir)



@unittest.skipUnless(USERNS_AVAILABLE, SKIP_REASON)
class SandboxApplyE2ETest(_SandboxApplyFixture):
    """The default-on sandbox and its escape, through a real apply."""

    @slow
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
        # The S2 stamps (v0.4.5): a plain confined apply is the
        # double-known-negative — present, both false.
        attempt = self._latest_attempt()
        self.assertIs(attempt["sandbox_escaped"], False)
        self.assertIs(attempt["network_grant_exercised"], False)
        # The v0.4.26 posture pair on a plain confined apply: the
        # known-negative form, key present.
        self.assertIs(attempt["sandbox_confined"], True)
        self.assertIn("sandbox_off_source", attempt)
        self.assertIsNone(attempt["sandbox_off_source"])

    def test_no_sandbox_bypasses_and_force_logs(self) -> None:
        # A configured grant beside the escape pins the interaction:
        # an escaped run exercises NO grant — nothing confined ran.
        self._grant_network()
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
        attempt = self._latest_attempt()
        self.assertIs(attempt["sandbox_escaped"], True,
                      msg="the escape must be stamped durably (§8.9)")
        self.assertIs(attempt["network_grant_exercised"], False,
                      msg="an escaped run exercises no grant — "
                          "nothing confined ran")
        # The v0.4.26 posture pair: only the flag disabled, so "flag".
        self.assertIs(attempt["sandbox_confined"], False)
        self.assertEqual(attempt["sandbox_off_source"], "flag")
        self.assertNotIn("[sandbox] enabled", log,
                         msg="no config-off line when config is on")

    @slow
    def test_grant_runs_confined_scripts_with_network(self) -> None:
        """The full grant path: committed [sandbox] network = true →
        the confined validation.sh runs with the parent namespace's
        network, the session log says GRANTED, and the applied attempt
        stamps network_grant_exercised: true beside sandbox_escaped:
        false. The non-loopback visibility assertion is capability-
        gated (module docstring): inside an ungranted outer sandbox
        the parent netns carries only lo, and the grant/stamp
        assertions still run — they are namespace-independent."""
        self._grant_network()
        result = run_bale(
            self.install,
            ["apply", str(self._iface_tarball()), "--no-interact"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        log = self._session_log()
        self.assertIn("network GRANTED", log)
        self.assertIn("bale.toml [sandbox] network", log)
        self.assertNotIn("FORCE", log,
                         msg="a config-granted apply is not an "
                             "override — no FORCE line")
        self.assertIn("iface:lo", log)
        if HAS_NON_LOOPBACK:
            granted_ifaces = [
                line.split("iface:", 1)[1].strip()
                for line in log.splitlines() if "iface:" in line]
            self.assertTrue(
                any(n != "lo" for n in granted_ifaces),
                msg=f"granted validation.sh saw only {granted_ifaces} "
                    f"though the invoking netns has non-loopback "
                    f"interfaces")
        attempt = self._latest_attempt()
        self.assertIs(attempt["sandbox_escaped"], False)
        self.assertIs(attempt["network_grant_exercised"], True,
                      msg="an exercised grant must be recorded (§8.9)")


class SandboxOffByConfigE2ETest(_SandboxApplyFixture):
    """Sandbox-off by config (v0.4.26, board 75) through a real apply.

    Deliberately NOT gated on user namespaces: with `[sandbox] enabled
    = false` committed nothing confined runs, so this tier exercises
    on the motivating host — the one without namespaces — exactly as
    it does here. Verified both ways at authoring time: with
    namespaces present, and with `unshare` removed from PATH.
    """

    CONFIG_OFF_LINE = "bale.toml [sandbox] enabled = false"

    def _disable_sandbox(self, *, network: bool = False) -> None:
        """Commit bale.toml's [sandbox] enabled = false (optionally
        beside a network grant). Same hand-edit-then-commit path as
        _grant_network: the wizard is canonical, not exclusive."""
        body = "[sandbox]\nenabled = false\n"
        if network:
            body += "network = true\n"
        (self.repo / "bale.toml").write_text(body, encoding="utf-8")
        env = git_env(self.home)
        run_checked(["git", "add", "bale.toml"], cwd=self.repo, env=env)
        run_checked(["git", "commit", "-m", "disable sandbox by config"],
                    cwd=self.repo, env=env)

    def test_config_off_runs_unconfined_and_force_logs_the_source(
            self) -> None:
        """The core contract: committed enabled = false → the escape
        write lands (unconfined), the session log carries a FORCE line
        naming the config key as the source (never silent), and the
        applied attempt stamps sandbox_confined: false /
        sandbox_off_source: "config" with sandbox_escaped: false — the
        flag was never typed."""
        self._disable_sandbox()
        result = run_bale(
            self.install, ["apply", str(self._tarball()), "--no-interact"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertTrue(
            self.escape.exists(),
            msg="config-off did not unconfine: the outside write "
                "should land exactly as under --no-sandbox")
        log = self._session_log()
        self.assertIn("FORCE", log)
        self.assertIn(self.CONFIG_OFF_LINE, log,
                      msg="every config-off run names its source")
        self.assertIn("UNCONFINED", log)
        self.assertNotIn("(--no-sandbox)", log,
                         msg="the flag line must not print when the "
                             "flag was not typed")
        attempt = self._latest_attempt()
        self.assertIs(attempt["sandbox_confined"], False)
        self.assertEqual(attempt["sandbox_off_source"], "config")
        self.assertIs(attempt["sandbox_escaped"], False,
                      msg="sandbox_escaped keeps its flag-only meaning")
        self.assertIs(attempt["network_grant_exercised"], False)

    def test_config_off_beside_flag_logs_both_and_records_config(
            self) -> None:
        """Both escapes present: both FORCE lines print (neither is
        silenced by the other), the source records "config" — the run
        was unconfined regardless — and sandbox_escaped: true carries
        the flag fact, so the four states stay readable."""
        self._disable_sandbox()
        result = run_bale(
            self.install,
            ["apply", str(self._tarball()), "--no-interact",
             "--no-sandbox"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertTrue(self.escape.exists())
        log = self._session_log()
        self.assertIn("(--no-sandbox)", log)
        self.assertIn(self.CONFIG_OFF_LINE, log)
        self.assertIn("redundant", log,
                      msg="the config-off line says the flag is redundant")
        attempt = self._latest_attempt()
        self.assertIs(attempt["sandbox_confined"], False)
        self.assertEqual(attempt["sandbox_off_source"], "config")
        self.assertIs(attempt["sandbox_escaped"], True)

    def test_config_off_does_not_exercise_a_configured_grant(self) -> None:
        """A network grant beside config-off is not exercised: nothing
        confined ran, and the note names the config key (not the flag)
        as what bypassed confinement."""
        self._disable_sandbox(network=True)
        result = run_bale(
            self.install, ["apply", str(self._tarball()), "--no-interact"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        log = self._session_log()
        self.assertIn(self.CONFIG_OFF_LINE, log)
        self.assertIn("grant is not exercised", log)
        self.assertIn("[sandbox] enabled = false bypassed", log)
        attempt = self._latest_attempt()
        self.assertIs(attempt["network_grant_exercised"], False)
        self.assertEqual(attempt["sandbox_off_source"], "config")

    def test_dry_run_under_config_off_is_silent_because_nothing_runs(
            self) -> None:
        """--dry-run executes no scripts, so no unconfined run happens
        and no FORCE line is owed — the same exemption the flag has."""
        self._disable_sandbox()
        result = run_bale(
            self.install, ["apply", str(self._tarball()), "--dry-run"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertFalse(self.escape.exists())
        self.assertNotIn(self.CONFIG_OFF_LINE, self._session_log())

    def test_global_enabled_false_does_not_unconfine_an_apply(self) -> None:
        """The project-only ruling end to end: a global bale.toml with
        enabled = false is ignored — the apply either confines (where
        namespaces exist) or refuses loudly naming both bypasses (where
        they do not). It never runs unconfined by a global key."""
        global_toml = self.install / "user" / "bale.toml"
        global_toml.parent.mkdir(parents=True, exist_ok=True)
        global_toml.write_text("[sandbox]\nenabled = false\n",
                               encoding="utf-8")
        result = run_bale(
            self.install, ["apply", str(self._tarball()), "--no-interact"],
            cwd=self.repo, env=self.env)
        log = self._session_log()
        self.assertNotIn("sandbox DISABLED by config", log,
                         msg="a global enabled = false must never be "
                             "the named source of an unconfined run")
        if USERNS_AVAILABLE:
            self.assertEqual(
                result.returncode, 0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            self.assertFalse(self.escape.exists())
            self.assertIs(self._latest_attempt()["sandbox_confined"], True)
        else:
            self.assertNotEqual(result.returncode, 0,
                                msg="without namespaces and without a "
                                    "project key, the apply refuses")
            self.assertFalse(self.escape.exists())
            self.assertIn("[sandbox] enabled = false", result.stderr,
                          msg="the refusal names the config bypass")


if __name__ == "__main__":
    unittest.main(verbosity=2)
