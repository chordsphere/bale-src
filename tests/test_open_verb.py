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
- delivery-flag injection follows member presence: a shipped brief
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
  [validation] base refuses before the dry-run;
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

    # -- delivery-flag injection -------------------------------------

    def test_brief_ships_as_request_readme(self) -> None:
        brief = "# Injected brief\n\nprose context\n"
        bundle = self.build_bundle(
            "b.bale-bundle", pack_argv=self.argv("brf"), brief=brief)
        result = self.open_bundle(bundle)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn("--readme-file", result.stdout)
        self.assertEqual(self.request_readme(result), brief)

    def test_null_brief_injects_no_readme(self) -> None:
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
        self.assert_no_session_state(result)

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


class CrafterEmissionRoundTrip(_OpenVerbBase):
    """Board 49b meets 49a-ii: a bundle EMITTED by the crafter
    (`tools/craft_response.py --bundle`) consumed by a real `bale
    open` — the producer against the consumer, end to end, in the
    hermetic sandbox. The hand-assembled build_bundle covers the
    consumer's refusal surface above; this class pins that the
    emitter's happy path is inside it: the archive is accepted, the
    hashes verify, the delivery flags inject from member presence,
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
        # Delivery injection from member presence: the packed request
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
