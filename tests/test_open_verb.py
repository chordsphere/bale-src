"""The `bale open` verb (board 49a-ii, v0.4.13; BALE.md §6.7, §5 row).

End-to-end pins for planner-bundle consumption, through real `bale
open` runs in the hermetic sandbox (ADR-0005 doctrine, via
tests/harness.py):

- the reserved suffix is the recognizer: a non-`.bale-bundle` file
  refuses before any archive read;
- the manifest gate runs before anything else is trusted: a missing
  `bundle.json`, an invalid manifest (`bundle_format` 2), and a
  stored delivery flag all refuse with the validator's own errors;
- the archive is sealed: an undeclared member refuses, a declared
  member missing from the archive refuses;
- both member hashes verify against LF-normalized bytes (boards
  36/40): a mismatch refuses; a CRLF-mangled transport copy still
  verifies and packs;
- the delivery flags follow member presence: a shipped brief
  becomes the request README byte-for-byte; a null brief packs with
  `--no-readme`; a shipped checkpoint is committed at the resolved
  per-session path by the replayed pack;
- the dry-run leg (board 48, subsumed): exit 1 echoes the FAIL
  probes as the expected-HOLD proof and proceeds; exit 2 refuses the
  whole open as a defective oracle with no session state created;
  exit 0 proceeds under a loud vacuous-oracle warning; the scratch
  copy makes the run read-only against the live base even
  UNCONFINED (a write-attempting checkpoint leaves the real tree
  untouched); a checkpoint member against a project pinning no
  [validation] base refuses before the dry-run, naming the resolved
  project root and the config files judged (board 68);
- gate order (board 68): the arg-inspectable pack gates — forecast
  existence, forecast disjointness — and the argv parse itself run
  before the dry-run, so a bundle they refuse spends no oracle
  execution (no announcement line, no open-*.log band); a bundle
  that clears them dry-runs and replays exactly as before;
- the FORCE prefix rides once per line on both unconfined escapes
  (--no-sandbox, [sandbox] enabled = false) — board 68 rider;
- the pre-answered-intents channel: a `supersede` intent accepts the
  decline-default exchange under piped stdin (where the bare replay
  would decline), closing the parent as superseded-by-split and
  stamping lineage; an intent no prompt consumed is reported loudly
  and changes nothing.

Non-sandbox-dependent dry-run tests pass --no-sandbox (deterministic
in every environment; the FORCE line is itself asserted once); the
confined tier is one happy-path run gated on userns availability, the
test_sandbox_wrapper pattern.

Bundles here are built at test runtime inside the scratch sandbox —
runtime artifacts, not shipped fixtures, so the worker-blindness rule
(BALE.md §6.7: sessions never *ship* bundle files) is untouched.
"""

from __future__ import annotations

import hashlib
import importlib.util
import io
import json
import subprocess
import sys
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

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))
import bale_sandbox  # noqa: E402 — userns probe only


def _userns_available() -> bool:
    try:
        r = subprocess.run(
            [bale_sandbox.UNSHARE, *bale_sandbox.UNSHARE_ARGS, "true"],
            capture_output=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return r.returncode == 0


USERNS_AVAILABLE = _userns_available()
USERNS_SKIP = ("unprivileged user namespaces unavailable in this "
               "environment; the confined dry-run tier runs on the "
               "operator's machine (the --no-sandbox tier covers the "
               "verb's logic here)")

CP_PATTERN = "claude/checkpoints/{sid}.sh"

# The dry-run's announcement line (bale_open.dry_run_checkpoint). Its
# absence from a refused open's stdout is the board-68 gate-order pin:
# an arg-inspectable refusal costs no oracle execution.
DRY_RUN_MARKER = "dry-running bundle checkpoint"

# Checkpoint bodies per dry-run verdict. Each prints probe-grammar
# lines so the proof echo has something to carry.
CP_HOLD = ("#!/usr/bin/env bash\n"
           "echo '[FAIL] the landed marker exists'\n"
           "exit 1\n")
CP_PASS = ("#!/usr/bin/env bash\n"
           "echo '[PASS] invariant holds'\n"
           "exit 0\n")
CP_ERROR = ("#!/usr/bin/env bash\n"
            "echo 'oracle blew up' >&2\n"
            "exit 2\n")
CP_WRITES = ("#!/usr/bin/env bash\n"
             "touch attempted-write.txt\n"
             "echo '[FAIL] wrote a scratch file'\n"
             "exit 1\n")


def sha_lf(text: str) -> str:
    """sha256 of the LF-normalized UTF-8 bytes — the published form."""
    return hashlib.sha256(
        text.encode("utf-8").replace(b"\r\n", b"\n")).hexdigest()


class _OpenVerbBase(unittest.TestCase):
    """Shared sandbox fixtures and helpers for the open-verb suites.
    No test methods live here (an underscore-prefixed base holds no
    tests to inherit-and-re-run); OpenVerbTest carries the consumer's
    refusal/replay pins and CrafterEmissionRoundTrip the 49b
    producer→consumer round trip."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-open-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixtures ----------------------------------------------------

    def configure_checkpoint(self) -> None:
        (self.repo / "bale.toml").write_text(
            f"[validation]\nbase = \"{CP_PATTERN}\"\n", encoding="utf-8")

    def build_bundle(self, name: str, *, pack_argv: list,
                     brief: str | None = "# Bundle brief\n\nbody\n",
                     checkpoint: str | None = None,
                     pre_answered: list | None = None,
                     manifest_override: dict | None = None,
                     extra_members: dict | None = None,
                     drop_members: set | None = None,
                     raw_member_bytes: dict | None = None) -> Path:
        """Assemble a `.bale-bundle` in the scratch tmp and return it.

        Hashes are computed over each member's LF-normalized bytes
        (the format's rule); `raw_member_bytes` substitutes what the
        archive actually carries for a member without touching the
        published hash, so transport-mangling and mismatch cases are
        one knob. `manifest_override` merges over the assembled
        manifest; `drop_members` removes archive members after the
        manifest is sealed (the declared-but-missing case);
        `extra_members` adds undeclared ones.
        """
        members: dict = {}
        payload: dict[str, bytes] = {}
        if brief is not None:
            members["brief"] = {"path": "brief.md",
                                "sha256": sha_lf(brief)}
            payload["brief.md"] = brief.encode("utf-8")
        else:
            members["brief"] = None
        if checkpoint is not None:
            members["checkpoint"] = {"path": "checkpoint.sh",
                                     "sha256": sha_lf(checkpoint)}
            payload["checkpoint.sh"] = checkpoint.encode("utf-8")
        else:
            members["checkpoint"] = None
        manifest = {
            "bundle_format": 1,
            "pack_argv": pack_argv,
            "members": members,
            "pre_answered": pre_answered if pre_answered is not None
            else [],
        }
        if manifest_override:
            manifest.update(manifest_override)
        payload["bundle.json"] = json.dumps(manifest).encode("utf-8")
        for mname, data in (raw_member_bytes or {}).items():
            payload[mname] = data
        for mname, data in (extra_members or {}).items():
            payload[mname] = data
        for mname in (drop_members or set()):
            payload.pop(mname, None)

        bundle = self.tmp / name
        with tarfile.open(bundle, "w:gz") as tf:
            for mname, data in payload.items():
                info = tarfile.TarInfo(mname)
                info.size = len(data)
                tf.addfile(info, io.BytesIO(data))
        return bundle

    def open_bundle(self, bundle: Path, *extra: str):
        return run_bale(self.install, ["open", str(bundle), *extra],
                        cwd=self.repo, env=self.env)

    def argv(self, slug: str, *extra: str) -> list:
        return [f"Goal for {slug}", "--slug", slug,
                "--include", "hello.txt", "--expects-probe", "no",
                *extra]

    def assert_no_session_state(self, result) -> None:
        """The refusal left nothing behind: no outbox, no open session."""
        outbox = self.repo / ".bale" / "outbox"
        tarballs = list(outbox.glob("*.tar.gz")) if outbox.exists() else []
        self.assertEqual(
            tarballs, [],
            msg=f"a refused open left a request tarball behind: "
                f"{tarballs}\nstdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}")
        sessions = self.repo / ".bale" / "sessions"
        open_dirs = ([p for p in sessions.iterdir() if p.is_dir()]
                     if sessions.exists() else [])
        self.assertEqual(
            open_dirs, [],
            msg=f"a refused open left session state behind: {open_dirs}")

    def request_readme(self, result) -> str | None:
        """Extract README.md from the packed request tarball, or None."""
        outbox = self.repo / ".bale" / "outbox"
        tarballs = sorted(outbox.glob("request-*.tar.gz"))
        self.assertEqual(
            len(tarballs), 1,
            msg=f"expected exactly one packed request, got {tarballs}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        with tarfile.open(tarballs[0], "r:gz") as tf:
            for member in tf.getmembers():
                if Path(member.name).name == "README.md" and \
                        len(Path(member.name).parts) == 2:
                    raw = tf.extractfile(member)
                    assert raw is not None
                    return raw.read().decode("utf-8")
        return None

class OpenVerbTest(_OpenVerbBase):
    """`bale open <bundle>`: gate, verify, dry-run, replay."""

    # -- recognizer + gate -------------------------------------------

    def test_non_bundle_suffix_refuses(self) -> None:
        stray = self.tmp / "notabundle.tar.gz"
        stray.write_bytes(b"whatever")
        result = run_bale(self.install, ["open", str(stray)],
                          cwd=self.repo, env=self.env)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(".bale-bundle", result.stderr)
        self.assertIn("recognizer", result.stderr)

    def test_missing_bundle_json_refuses(self) -> None:
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("x"),
            drop_members={"bundle.json"})
        result = self.open_bundle(bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("bundle.json", result.stderr)
        self.assert_no_session_state(result)

    def test_invalid_manifest_refuses_with_validator_errors(self) -> None:
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("x"),
            manifest_override={"bundle_format": 2})
        result = self.open_bundle(bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("failed validation", result.stderr)
        self.assertIn("bundle_format", result.stderr)
        self.assert_no_session_state(result)

    def test_stored_delivery_flag_refuses_at_the_gate(self) -> None:
        bundle = self.build_bundle(
            "b.bale-bundle",
            pack_argv=self.argv("x", "--readme-file", "sneaky.md"))
        result = self.open_bundle(bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--readme-file", result.stderr)
        self.assertIn("single source", result.stderr)
        self.assert_no_session_state(result)

    # -- sealed archive + hashes -------------------------------------

    def test_undeclared_member_refuses(self) -> None:
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("x"),
            extra_members={"stowaway.txt": b"hi\n"})
        result = self.open_bundle(bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stowaway.txt", result.stderr)
        self.assertIn("sealed", result.stderr)
        self.assert_no_session_state(result)

    def test_declared_member_missing_refuses(self) -> None:
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("x"),
            drop_members={"brief.md"})
        result = self.open_bundle(bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("brief.md", result.stderr)
        self.assertIn("does not carry", result.stderr)
        self.assert_no_session_state(result)

    def test_hash_mismatch_refuses(self) -> None:
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("x"),
            raw_member_bytes={"brief.md": b"# Tampered\n\nbody\n"})
        result = self.open_bundle(bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("hash", result.stderr)
        self.assertIn("brief.md", result.stderr)
        self.assert_no_session_state(result)

    def test_crlf_transport_still_verifies_and_packs(self) -> None:
        """A CRLF-mangled member verifies against the LF-computed hash
        — the format's own normalization rule, end to end."""
        brief = "# CRLF brief\n\nbody\n"
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("crlf"),
            brief=brief,
            raw_member_bytes={
                "brief.md": brief.replace("\n", "\r\n").encode("utf-8")})
        result = self.open_bundle(bundle)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        shipped = self.request_readme(result)
        self.assertEqual(shipped, brief,
                         msg="the request README should carry the "
                             "LF-normalized brief bytes")

    # -- delivery flags from member presence -------------------------------------

    def test_brief_ships_as_request_readme(self) -> None:
        brief = "# Carried brief\n\nprose context\n"
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("brf"), brief=brief)
        result = self.open_bundle(bundle)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("--readme-file", result.stdout)
        self.assertEqual(self.request_readme(result), brief)

    def test_null_brief_supplies_no_readme(self) -> None:
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("nul"), brief=None)
        result = self.open_bundle(bundle)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("--no-readme", result.stdout)
        self.assertIsNone(self.request_readme(result),
                          msg="a null-brief bundle must pack without "
                              "a README")

    # -- v0.4.41: the bundle on the opened attempt ---------------------

    def opened_attempts(self) -> list:
        """Every opened attempt in the repo's telemetry corpus."""
        out = []
        for path in sorted((self.repo / "claude" / "telemetry")
                           .glob("*.json")):
            record = json.loads(path.read_text(encoding="utf-8"))
            out += [a for a in record["attempts"]
                    if a.get("outcome") == "opened"]
        return out

    def bundle_json_sha(self, bundle: Path) -> str:
        with tarfile.open(bundle, "r:gz") as tf:
            data = tf.extractfile("bundle.json").read()
        return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()

    def test_opened_attempt_carries_the_bundle(self) -> None:
        brief = "# Stamped brief\n\nbody\n"
        bundle = self.build_bundle(
            "rev-b.bale-bundle", pack_argv=self.argv("bnd"), brief=brief)
        result = self.open_bundle(bundle)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        opened = self.opened_attempts()
        self.assertEqual(len(opened), 1)
        self.assertEqual(opened[0]["bundle"], {
            "stem": "rev-b",
            "brief_sha256": sha_lf(brief),
            "checkpoint_sha256": None,
            "manifest_sha256": self.bundle_json_sha(bundle),
        })
        self.assertIn("provenance", opened[0],
                      msg="the bundle rides beside provenance, not in it")

    def test_null_brief_bundle_stamps_a_null_brief_sha(self) -> None:
        bundle = self.build_bundle(
            "nb.bale-bundle", pack_argv=self.argv("nbs"), brief=None)
        result = self.open_bundle(bundle)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        stamp = self.opened_attempts()[0]["bundle"]
        self.assertEqual(stamp["stem"], "nb")
        self.assertIsNone(stamp["brief_sha256"])

    # -- the dry-run leg ---------------------------------------------

    def test_expected_hold_echoes_proof_and_packs(self) -> None:
        self.configure_checkpoint()
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("hold"),
            checkpoint=CP_HOLD)
        result = self.open_bundle(bundle, "--no-sandbox")
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("[FAIL] the landed marker exists", result.stdout)
        self.assertIn("expected-HOLD proof", result.stdout)
        # The FORCE line for the unconfined escape, asserted once here.
        self.assertIn("--no-sandbox", result.stdout)
        self.assertIn("FORCE", result.stdout)
        # The replayed pack committed the checkpoint at the resolved
        # per-session path, on the branch.
        committed = subprocess.run(
            ["git", "show",
             "HEAD:claude/checkpoints/2026-08-24-hold-001.sh"],
            cwd=self.repo, env=git_env(self.home),
            capture_output=True, text=True)
        # sid date is the run date, not a literal — resolve via ls-tree.
        if committed.returncode != 0:
            ls = subprocess.run(
                ["git", "ls-tree", "-r", "--name-only", "HEAD",
                 "claude/checkpoints/"],
                cwd=self.repo, env=git_env(self.home),
                capture_output=True, text=True)
            paths = [p for p in ls.stdout.splitlines()
                     if p.endswith("-hold-001.sh")]
            self.assertEqual(
                len(paths), 1,
                msg=f"expected one committed checkpoint, tree has: "
                    f"{ls.stdout}")
            committed = subprocess.run(
                ["git", "show", f"HEAD:{paths[0]}"],
                cwd=self.repo, env=git_env(self.home),
                capture_output=True, text=True)
        self.assertEqual(committed.stdout, CP_HOLD)

    def test_exit_two_refuses_as_defective_oracle(self) -> None:
        self.configure_checkpoint()
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("bad"),
            checkpoint=CP_ERROR)
        result = self.open_bundle(bundle, "--no-sandbox")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("defective", result.stderr)
        self.assert_no_session_state(result)

    def test_exit_zero_warns_vacuous_and_proceeds(self) -> None:
        self.configure_checkpoint()
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("vac"),
            checkpoint=CP_PASS)
        result = self.open_bundle(bundle, "--no-sandbox")
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("WARNING", result.stdout)
        self.assertIn("vacuous", result.stdout)

    def test_dry_run_is_read_only_against_the_live_base(self) -> None:
        """Even UNCONFINED, the scratch copy keeps the real tree
        untouched — the read-only guarantee is structural."""
        self.configure_checkpoint()
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("ro"),
            checkpoint=CP_WRITES)
        result = self.open_bundle(bundle, "--no-sandbox")
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertFalse(
            (self.repo / "attempted-write.txt").exists(),
            msg="the dry-run wrote into the live base — the scratch "
                "copy failed its one job")

    def test_checkpoint_member_without_config_refuses_pre_dry_run(
            self) -> None:
        # No bale.toml: the project pins no [validation] base.
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("cfg"),
            checkpoint=CP_HOLD)
        result = self.open_bundle(bundle, "--no-sandbox")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("[validation] base", result.stderr)
        self.assertNotIn(DRY_RUN_MARKER, result.stdout)
        self.assert_no_session_state(result)
        # Board 68: the refusal names the resolved project root and
        # the config files it judged, each marked read or absent —
        # "this project" alone cost a live probe round.
        self.assert_names_root_and_config(
            result.stderr, project_read=False, global_read=False)

    # -- gate order (board 68): cheap gates before the oracle --------

    def assert_no_dry_run(self, result) -> None:
        """No dry-run ran: no announcement line, no proof, and no
        open-*.log band under .bale/logs (the dry-run's only durable
        trace)."""
        self.assertNotIn(DRY_RUN_MARKER, result.stdout)
        self.assertNotIn("expected-HOLD proof", result.stdout)
        logs = self.repo / ".bale" / "logs"
        dry_logs = (sorted(logs.glob("open-*.log")) if logs.exists()
                    else [])
        self.assertEqual(
            dry_logs, [],
            msg=f"a refused open still ran the dry-run: {dry_logs}\n"
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

    def assert_names_root_and_config(self, text: str, *,
                                     project_read: bool,
                                     global_read: bool) -> None:
        """The config-judgment tail: absolute root, both config paths,
        each with its read/absent mark."""
        root = self.repo.resolve()
        self.assertIn(f"Project root: {root};", text)
        self.assertIn(
            f"{root / 'bale.toml'} "
            f"({'read' if project_read else 'absent'})", text)
        global_cfg = self.install / "user" / "bale.toml"
        self.assertIn(
            f"{global_cfg} ({'read' if global_read else 'absent'})", text)

    def test_missing_write_path_refuses_before_the_dry_run(self) -> None:
        """A stored --write naming a path that does not exist refuses
        with the existence gate's own text, and the checkpoint never
        runs — the specimen where a ~9-minute confined dry-run preceded
        an arg-inspectable refusal."""
        self.configure_checkpoint()
        bundle = self.build_bundle(
            "b.bale-bundle",
            pack_argv=self.argv("gone", "--write", "missing.txt"),
            checkpoint=CP_HOLD)
        result = self.open_bundle(bundle, "--no-sandbox")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--write path does not exist: missing.txt",
                      result.stderr)
        self.assert_no_dry_run(result)
        self.assert_no_session_state(result)

    def test_forecast_intersection_refuses_before_the_dry_run(
            self) -> None:
        """A stored forecast intersecting an open session's refuses
        with the disjointness gate's own text, before the dry-run."""
        # The parent packs before the project pins a [validation]
        # base (a {sid} base would demand a committed checkpoint the
        # fixture has no reason to author); its recorded forecast is
        # its include set, hello.txt.
        parent = run_bale(
            self.install,
            ["pack", "Parent holding hello.txt", "--slug", "parent",
             "--include", "hello.txt", "--expects-probe", "no",
             "--no-readme"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            parent.returncode, 0,
            msg=f"stdout:\n{parent.stdout}\nstderr:\n{parent.stderr}")
        parent_sid = [ln for ln in parent.stdout.splitlines()
                      if "session id:" in ln][0].split("session id:")[1].strip()
        self.configure_checkpoint()
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("kid"),
            checkpoint=CP_HOLD)
        result = self.open_bundle(bundle, "--no-sandbox")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pack write forecast intersects", result.stderr)
        self.assertIn(parent_sid, result.stderr)
        self.assertIn("hello.txt ~ hello.txt", result.stderr)
        self.assert_no_dry_run(result)
        # Only the parent's state exists: no second tarball, no child.
        outbox = self.repo / ".bale" / "outbox"
        self.assertEqual(len(list(outbox.glob("request-*.tar.gz"))), 1)
        sessions = self.repo / ".bale" / "sessions"
        self.assertEqual(
            sorted(p.name for p in sessions.iterdir() if p.is_dir()),
            [parent_sid])

    def test_gates_clear_then_dry_run_then_replay_in_that_order(
            self) -> None:
        """The happy path is unchanged in outcome, and the transcript
        proves the order: the dry-run announcement precedes the replay
        line, and the replayed pack re-runs its own gates and packs."""
        self.configure_checkpoint()
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("ord"),
            checkpoint=CP_HOLD)
        result = self.open_bundle(bundle, "--no-sandbox")
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        out = result.stdout
        self.assertIn(DRY_RUN_MARKER, out)
        self.assertLess(out.index(DRY_RUN_MARKER),
                        out.index("replaying pack invocation"))
        self.assertIn("expected-HOLD proof", out)
        self.request_readme(result)  # exactly one packed request

    def test_unparseable_stored_argv_refuses_before_the_dry_run(
            self) -> None:
        """The argv is parsed before the oracle runs: a stored flag the
        CLI does not know refuses at argparse, with no dry-run spent."""
        self.configure_checkpoint()
        bundle = self.build_bundle(
            "b.bale-bundle",
            pack_argv=self.argv("bad", "--no-such-flag"),
            checkpoint=CP_HOLD)
        result = self.open_bundle(bundle, "--no-sandbox")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--no-such-flag", result.stderr)
        self.assert_no_dry_run(result)
        self.assert_no_session_state(result)

    # -- FORCE prefix (board 68 rider) -------------------------------

    def _force_lines(self, text: str) -> list:
        return [ln for ln in text.splitlines() if "FORCE" in ln]

    def test_no_sandbox_force_line_carries_one_prefix(self) -> None:
        """log(force=True) prefixes `[bale] FORCE: ` itself; the message
        must not add a second one (the observed `FORCE: FORCE:`)."""
        self.configure_checkpoint()
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("one"),
            checkpoint=CP_HOLD)
        result = self.open_bundle(bundle, "--no-sandbox")
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertNotIn("FORCE: FORCE:", result.stdout)
        escape = [ln for ln in self._force_lines(result.stdout)
                  if "--no-sandbox" in ln]
        self.assertEqual(len(escape), 1, msg=str(escape))
        self.assertTrue(escape[0].startswith("[bale] FORCE: --no-sandbox"),
                        msg=escape[0])

    def test_sandbox_off_by_config_force_line_carries_one_prefix(
            self) -> None:
        (self.repo / "bale.toml").write_text(
            f"[validation]\nbase = \"{CP_PATTERN}\"\n"
            f"[sandbox]\nenabled = false\n", encoding="utf-8")
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("cfgoff"),
            checkpoint=CP_HOLD)
        result = self.open_bundle(bundle)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertNotIn("FORCE: FORCE:", result.stdout)
        by_config = [ln for ln in self._force_lines(result.stdout)
                     if "[sandbox] enabled = false" in ln]
        self.assertEqual(len(by_config), 1, msg=str(by_config))
        self.assertTrue(
            by_config[0].startswith("[bale] FORCE: bale.toml [sandbox]"),
            msg=by_config[0])

    @unittest.skipUnless(USERNS_AVAILABLE, USERNS_SKIP)
    def test_confined_dry_run_happy_path(self) -> None:
        """The default (sandboxed) tier, where userns allows it."""
        self.configure_checkpoint()
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("cfd"),
            checkpoint=CP_HOLD)
        result = self.open_bundle(bundle)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("confined", result.stdout)
        self.assertIn("expected-HOLD proof", result.stdout)

    # -- pre-answered intents ----------------------------------------

    def test_supersede_intent_accepts_under_piped_stdin(self) -> None:
        """The channel's whole point: piped stdin takes the decline
        default on the typed path; the bundle's intent supplies the
        accept, routed through the exchange."""
        parent = run_bale(
            self.install,
            ["pack", "Parent to supersede", "--slug", "parent",
             "--include", "hello.txt", "--expects-probe", "no",
             "--no-readme"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            parent.returncode, 0,
            msg=f"stdout:\n{parent.stdout}\nstderr:\n{parent.stderr}")
        sid_lines = [ln for ln in parent.stdout.splitlines()
                     if "session id:" in ln]
        parent_sid = sid_lines[0].split("session id:")[1].strip()

        bundle = self.build_bundle(
            "b.bale-bundle",
            pack_argv=self.argv("child", "--supersedes", parent_sid),
            pre_answered=[{"prompt": "supersede",
                           "subject": parent_sid}])
        result = self.open_bundle(bundle)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("pre-answered intent", result.stdout)
        self.assertIn("superseded-by-split", result.stdout)
        # The parent's open-session state is gone; the child is the
        # one open session.
        sessions = self.repo / ".bale" / "sessions"
        open_sids = sorted(p.name for p in sessions.iterdir()
                           if p.is_dir())
        self.assertEqual(len(open_sids), 1, msg=str(open_sids))
        self.assertNotIn(parent_sid, open_sids)

    def test_unconsumed_intent_reports_loudly_and_packs(self) -> None:
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("unc"),
            pre_answered=[{"prompt": "supersede",
                           "subject": "2026-01-01-ghost-001"}])
        result = self.open_bundle(bundle)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("was not consumed", result.stdout)

    # -- v0.4.44, board row 121: argv-only gates before the exchange ---

    def test_include_naming_checkpoint_refuses_before_supersession(
            self) -> None:
        """The paired-desk specimen, reproduced as the planner desk did:
        a checkpoint-configured repo with a tracked checkpoint file, a
        read-only parent, and a bundle whose argv is `--read-only
        --include claude/checkpoints --supersedes <parent>` with a
        pre-answered `supersede`. pack_argv_preflight passes (the include
        exists; [] is disjoint from []), so the refusal is the replay's —
        and it must land before the exchange: the open refuses, the
        parent's record still reads `opened` with no superseded-by-split
        closure, and the parent is still the one open session."""
        self.configure_checkpoint()
        cp_dir = self.repo / "claude" / "checkpoints"
        cp_dir.mkdir(parents=True)
        (cp_dir / "old.sh").write_text("#!/usr/bin/env bash\nexit 0\n",
                                       encoding="utf-8")
        genv = git_env(self.home)
        run_checked(["git", "add", "bale.toml", "claude/checkpoints"],
                    cwd=self.repo, env=genv)
        run_checked(["git", "commit", "-m", "checkpoint config"],
                    cwd=self.repo, env=genv)
        parent = run_bale(
            self.install,
            ["pack", "Read-only parent", "--slug", "parent", "--read-only",
             "--include", "hello.txt", "--no-readme"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            parent.returncode, 0,
            msg=f"stdout:\n{parent.stdout}\nstderr:\n{parent.stderr}")
        parent_sid = [ln for ln in parent.stdout.splitlines()
                      if "session id:" in ln][0].split("session id:")[1].strip()

        bundle = self.build_bundle(
            "revb.bale-bundle",
            pack_argv=["Read-only child", "--slug", "child", "--read-only",
                       "--include", "claude/checkpoints",
                       "--supersedes", parent_sid],
            pre_answered=[{"prompt": "supersede", "subject": parent_sid}])
        result = self.open_bundle(bundle)
        combined = result.stdout + result.stderr
        self.assertNotEqual(result.returncode, 0, msg=combined)
        self.assertNotIn("superseded-by-split", result.stdout, msg=combined)
        record = json.loads(
            (self.repo / "claude" / "telemetry" / f"{parent_sid}.json")
            .read_text(encoding="utf-8"))
        self.assertEqual([a["outcome"] for a in record["attempts"]],
                         ["opened"], msg=combined)
        self.assertNotIn("superseded-by-split", json.dumps(record))
        sessions = self.repo / ".bale" / "sessions"
        self.assertEqual(
            sorted(p.name for p in sessions.iterdir() if p.is_dir()),
            [parent_sid], msg=combined)


class SecondDeskTest(_OpenVerbBase):
    """v0.4.44, board row 123: a second `bale open` of a bundle whose
    session is still open records a further desk on the SAME sid — a
    second `opened` attempt carrying `desk`, command 'open' — exits 0
    with one session open, and re-emits the opener with the
    desk-qualified name. Recognition precedes the read-only sweep, so
    desk two never closes desk one's session. A closed session's bundle
    opens a new session as before."""

    def sessions(self) -> list:
        root = self.repo / ".bale" / "sessions"
        return sorted(p.name for p in root.iterdir()
                      if (p / "open").is_file()) if root.is_dir() else []

    def record(self, sid: str) -> dict:
        return json.loads((self.repo / "claude" / "telemetry" /
                           f"{sid}.json").read_text(encoding="utf-8"))

    def open_ok(self, bundle: Path):
        result = self.open_bundle(bundle)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        return result

    def read_only_bundle(self, name: str = "plan.bale-bundle") -> Path:
        return self.build_bundle(
            name, pack_argv=["Plan the next wave", "--slug", "plan",
                             "--read-only", "--include", "hello.txt"])

    def test_second_open_of_a_read_only_bundle_records_a_desk(self) -> None:
        bundle = self.read_only_bundle()
        self.open_ok(bundle)
        [sid] = self.sessions()
        second = self.open_ok(bundle)
        self.assertEqual(self.sessions(), [sid],
                         msg="one session open; no second sid minted")
        opened = [a for a in self.record(sid)["attempts"]
                  if a["outcome"] == "opened"]
        self.assertEqual(len(opened), 2)
        self.assertNotIn("desk", opened[0])
        self.assertEqual(opened[1]["desk"], "desk-2")
        self.assertEqual(opened[1]["command"], "open")
        self.assertEqual(opened[1]["bundle"], opened[0]["bundle"])
        self.assertEqual(opened[1]["provenance"]["packed_at"],
                         opened[0]["provenance"]["packed_at"])
        self.assertEqual(self.record(sid)["outcome"], "opened")
        # The re-emitted opener names the desk-qualified sid, and the
        # sweep never ran (nothing closed desk one's session).
        self.assertIn(f"This message opens read-only bale session {sid}",
                      second.stdout)
        self.assertIn(f"{sid}@desk-2", second.stdout)
        self.assertNotIn("read-only sweep", second.stdout)
        self.assertNotIn("replaying pack invocation", second.stdout)
        # A third open is desk-3.
        self.open_ok(bundle)
        desks = [a.get("desk") for a in self.record(sid)["attempts"]]
        self.assertEqual(desks, [None, "desk-2", "desk-3"])
        # The additive proof: the three-desk record validates against
        # the updated schema (desk, and command 'open').
        spec = importlib.util.spec_from_file_location(
            "bale_validate_under_test",
            str(self.install / "bin" / "bale_validate.py"))
        bv = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(bv)
        self.assertEqual(bv.validate_telemetry_record(self.record(sid)), [])

    def test_renamed_copy_is_the_same_bundle(self) -> None:
        bundle = self.read_only_bundle()
        self.open_ok(bundle)
        [sid] = self.sessions()
        copy = self.tmp / "plan (1).bale-bundle"
        copy.write_bytes(bundle.read_bytes())
        self.open_ok(copy)
        self.assertEqual(self.sessions(), [sid])
        last = self.record(sid)["attempts"][-1]
        self.assertEqual(last["desk"], "desk-2")
        self.assertEqual(last["bundle"]["stem"], "plan (1)")

    def test_scoped_bundle_second_desk_skips_its_own_gate(self) -> None:
        """A worker bundle's second open would collide with its own
        session's forecast at the pre-flight; recognition precedes it."""
        bundle = self.build_bundle("w.bale-bundle",
                                   pack_argv=self.argv("work"))
        self.open_ok(bundle)
        [sid] = self.sessions()
        second = self.open_ok(bundle)
        self.assertEqual(self.sessions(), [sid])
        self.assertIn(f"This message opens bale session {sid}.",
                      second.stdout)
        self.assertIn(f"{sid}@desk-2", second.stdout)

    def test_a_different_bundle_still_opens_its_own_session(self) -> None:
        self.open_ok(self.read_only_bundle())
        other = self.build_bundle(
            "other.bale-bundle",
            pack_argv=["Another plan", "--slug", "other", "--read-only",
                       "--include", "hello.txt"])
        self.open_ok(other)
        self.assertTrue(any("other" in sid for sid in self.sessions()))

    def test_closed_session_bundle_opens_a_new_session(self) -> None:
        bundle = self.read_only_bundle()
        self.open_ok(bundle)
        [sid] = self.sessions()
        unlock = run_bale(self.install, ["unlock", sid], cwd=self.repo,
                          env=self.env)
        self.assertEqual(unlock.returncode, 0, msg=unlock.stderr)
        self.open_ok(bundle)
        [new_sid] = self.sessions()
        self.assertNotEqual(new_sid, sid)
        self.assertNotIn("desk", json.dumps(self.record(new_sid)))

    def test_event_past_the_opens_refuses_a_desk(self) -> None:
        """An 'opened' attempt after an apply-side event would contradict
        the record; the open refuses, naming the event, and writes
        nothing."""
        bundle = self.read_only_bundle()
        self.open_ok(bundle)
        [sid] = self.sessions()
        path = self.repo / "claude" / "telemetry" / f"{sid}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record["attempts"].append(dict(record["attempts"][0],
                                       outcome="held", command="apply"))
        record["outcome"] = "held"
        path.write_text(json.dumps(record), encoding="utf-8")
        before = path.read_bytes()
        result = self.open_bundle(bundle)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("latest: held", result.stderr)
        self.assertEqual(path.read_bytes(), before)
        self.assertEqual(self.sessions(), [sid])


class CrafterEmissionRoundTrip(_OpenVerbBase):
    """Board 49b meets 49a-ii: a bundle EMITTED by the crafter
    (`tools/craft_response.py --bundle`) consumed by a real `bale
    open` — the producer against the consumer, end to end, in the
    hermetic sandbox. The hand-assembled build_bundle covers the
    consumer's refusal surface above; this class pins that the
    emitter's happy path is inside it: the archive is accepted, the
    hashes verify, the delivery flags come from member presence,
    the dry-run leg runs the shipped checkpoint, and the crafter's
    printed paste line — the bundle filename only — resolves through
    the configured search path exactly as the desk ships it.

    Bundles here are runtime artifacts inside the scratch tmp, never
    shipped fixtures (the worker-blindness rule)."""

    CRAFT = Path(__file__).resolve().parent.parent / "tools" / \
        "craft_response.py"

    def craft_bundle(self, stem: str, *argv: str):
        return subprocess.run(
            [sys.executable, str(self.CRAFT), "--bundle", stem, *argv,
             "--out-dir", str(self.tmp)],
            capture_output=True, text=True, cwd=self.tmp)

    def test_emitted_bundle_opens_via_the_printed_line(self) -> None:
        # [validation] base for the checkpoint leg, plus a search path
        # covering the bundle's directory so the crafter's
        # filename-only paste line resolves from the repo cwd — the
        # downloads-dir save, reproduced.
        (self.repo / "bale.toml").write_text(
            f"[validation]\nbase = \"{CP_PATTERN}\"\n"
            f"[apply]\nsearch_paths = [\"{self.tmp}\"]\n",
            encoding="utf-8")
        brief = "# Crafted brief\n\nCRLF in transit\r\nis fine\r\n"
        brief_file = self.tmp / "the-brief.md"
        brief_file.write_text(brief, encoding="utf-8")
        cp_file = self.tmp / "the-checkpoint.sh"
        cp_file.write_text(CP_HOLD, encoding="utf-8")

        crafted = self.craft_bundle(
            "2026-07-29-crafted-rt",
            "--brief", str(brief_file), "--checkpoint", str(cp_file),
            "--pack-arg", "Goal for crafted-rt",
            "--pack-arg=--slug", "--pack-arg", "crafted-rt",
            "--pack-arg=--include", "--pack-arg", "hello.txt",
            "--pack-arg=--expects-probe", "--pack-arg", "no")
        self.assertEqual(crafted.returncode, 0, crafted.stderr)
        # The paste line carries the bundle FILENAME only.
        paste_line = crafted.stdout.strip()
        self.assertEqual(paste_line,
                         "bale open 2026-07-29-crafted-rt.bale-bundle")
        filename = paste_line.split()[-1]
        self.assertNotIn("/", filename)

        result = run_bale(self.install,
                          ["open", filename, "--no-sandbox"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        # Both member hashes verified; the dry-run leg ran the shipped
        # checkpoint and echoed the expected-HOLD proof.
        self.assertIn("member brief verified", result.stdout)
        self.assertIn("member checkpoint verified", result.stdout)
        self.assertIn("expected-HOLD proof", result.stdout)
        # Delivery flags from member presence: the packed request
        # carries the LF-normalized brief byte-for-byte.
        self.assertEqual(self.request_readme(result),
                         brief.replace("\r\n", "\n"))

    def test_emitted_null_slots_open_clean(self) -> None:
        crafted = self.craft_bundle(
            "2026-07-29-crafted-nul", "--no-brief",
            "--pack-arg", "Goal for crafted-nul",
            "--pack-arg=--slug", "--pack-arg", "crafted-nul",
            "--pack-arg=--include", "--pack-arg", "hello.txt",
            "--pack-arg=--expects-probe", "--pack-arg", "no")
        self.assertEqual(crafted.returncode, 0, crafted.stderr)
        bundle = self.tmp / "2026-07-29-crafted-nul.bale-bundle"
        result = self.open_bundle(bundle)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("--no-readme", result.stdout)
        self.assertIn("no checkpoint member", result.stdout)
        self.assertIsNone(self.request_readme(result))


if __name__ == "__main__":
    unittest.main()
