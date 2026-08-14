#!/usr/bin/env python3
"""Hermetic E2E for per-sid blind checkpoints (board 10 S7, v0.4.8).

Covers the S7 contract against the documented behavior (BALE.md §8.5's
per-session-checkpoints paragraph; ADR-0002 oracle doctrine —
observable state, never golden comparisons):

- resolve_checkpoint_path is pure string resolution: a literal path
  returns unchanged byte-for-byte, and every occurrence of the literal
  token {sid} substitutes the session id — pinning the surface the
  brief names (bin/bale_config.py, exact signature);
- an unrecognized brace token (the {date} case the brief leaves to
  craft) refuses loudly at pack — the config-read validation, so the
  refusal names the token and no session state exists after it; a
  half-substituted path is impossible by construction and asserted
  never to appear;
- a {sid}-bearing base whose resolved file is absent from HEAD refuses
  loudly at pack, naming the resolved path and the author-and-commit
  remedy, pre-allocation: the per-day counter is NOT consumed, so
  committing the checkpoint the refusal named and re-running the same
  pack allocates the same sid and the same resolved path (the
  no-counter-chase property the pre-allocation peek exists for);
- the happy path threads the resolved path honestly through the
  lifecycle: pack stamps provenance.checkpoint with the RESOLVED path
  and the committed bytes' sha256; apply executes the per-sid script
  (asserted on EXECUTED output — the session's own marker in the log,
  never a sibling's) and the telemetry stamp records the resolved
  path, the executed bytes' hash, and stamp_matched true;
- sibling isolation, the goal sentence: two concurrently open sessions
  resolve to different files, so an amendment committed to one
  session's checkpoint neither trips the OTHER session's stamp
  verification (its apply merges with stamp_matched true and its own
  pre-amendment marker executing) nor slips past its own (the amended
  session's apply refuses with the stamp-divergence message until
  --accept-checkpoint-change admits it).

Sid prediction note: the pack-refusal and happy-path fixtures commit a
checkpoint at the path the NEXT pack will resolve — date.today() +
slug + the fresh repo's counter — which is exactly the planner's own
workflow under {sid}. A midnight rollover between the prediction and
the pack would desync them; the suites already embed same-day
assumptions and the window is sub-second.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_per_sid_checkpoint.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from datetime import date
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

REPO_ROOT = Path(__file__).resolve().parent.parent

CP_PATTERN = "claude/checkpoints/{sid}.sh"

# Sentinels for the surfaces this file pins.
UNKNOWN_TOKEN_PHRASE = "unrecognized placeholder token"
MISSING_RESOLVED_PHRASE = "per-session blind checkpoint missing"
REMEDY_PHRASE = "author and commit the session's checkpoint"
STAMP_DIVERGED_PHRASE = "blind checkpoint changed since pack"
AUTO_EXCLUDE_PHRASE = "never ships incidentally"
READ_NAME_PHRASE = "pack includes name the blind checkpoint explicitly"
FORECAST_COVER_PHRASE = "write forecast covers the blind checkpoint"
WAIVER_PHRASE = "read-only checkpoint waiver"


def checkpoint_script(marker: str) -> str:
    """A committed per-sid checkpoint fixture honoring TARBALL.md
    §7.2/§7.5 — passes, printing its session-distinct marker."""
    return (
        "#!/usr/bin/env bash\n"
        f"echo \"[PASS] {marker}\"\n"
        "exit 0\n"
    )


class ResolveCheckpointPathUnitTest(unittest.TestCase):
    """The pinned pure-resolution surface, imported directly."""

    @classmethod
    def setUpClass(cls) -> None:
        sys.path.insert(0, str(REPO_ROOT / "bin"))
        import bale_config  # noqa: F401 — the import under test
        cls.bale_config = bale_config

    @classmethod
    def tearDownClass(cls) -> None:
        sys.path.remove(str(REPO_ROOT / "bin"))

    def test_literal_path_returns_unchanged(self) -> None:
        self.assertEqual(
            self.bale_config.resolve_checkpoint_path(
                "scripts/validation.base.sh", "2026-08-13-x-001"),
            "scripts/validation.base.sh",
            msg="a value without the token behaves byte-for-byte as "
                "before — resolution must be the identity on literals")

    def test_sid_token_substitutes(self) -> None:
        self.assertEqual(
            self.bale_config.resolve_checkpoint_path(
                CP_PATTERN, "2026-08-13-x-001"),
            "claude/checkpoints/2026-08-13-x-001.sh")

    def test_every_occurrence_substitutes(self) -> None:
        """No half-substitution: resolution is total over the token."""
        self.assertEqual(
            self.bale_config.resolve_checkpoint_path(
                "claude/{sid}/{sid}.sh", "s-001"),
            "claude/s-001/s-001.sh")

    def test_non_token_braces_pass_through(self) -> None:
        """Braces that do not form a {token} are literal characters."""
        self.assertEqual(
            self.bale_config.resolve_checkpoint_path(
                "claude/weird{name/{sid}.sh", "s-001"),
            "claude/weird{name/s-001.sh")


class PerSidFixture(unittest.TestCase):
    """Shared per-sid sandbox fixture: a scratch repo + install with
    helpers for configuring a base, predicting sids, committing
    checkpoint files, and packing. Holds no tests itself, so suites
    can inherit the fixture without re-running each other's methods."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-persid-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture ---------------------------------------------------------

    def configure_base(self, value: str) -> None:
        (self.repo / "bale.toml").write_text(
            f"[validation]\nbase = \"{value}\"\n", encoding="utf-8")

    def predicted_sid(self, slug: str, nnn: int = 1) -> str:
        """The sid the next pack will mint: today + slug + the counter.
        Mirrors the planner's own prediction workflow under {sid}."""
        return f"{date.today().isoformat()}-{slug}-{nnn:03d}"

    def commit_files(self, files: dict, message: str) -> dict:
        """Write and commit `files` ({relpath: text}); return
        {relpath: sha256 of the committed bytes}."""
        shas = {}
        for rel, body in files.items():
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            data = body.encode("utf-8")
            p.write_bytes(data)
            shas[rel] = hashlib.sha256(data).hexdigest()
        run_checked(["git", "add", *files.keys()],
                    cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", message],
                    cwd=self.repo, env=self.genv)
        return shas

    def pack(self, slug: str, *extra: str):
        return run_bale(
            self.install,
            ["pack", f"per-sid checkpoint e2e goal ({slug})",
             "--slug", slug, "--no-readme", *extra],
            cwd=self.repo, env=self.env,
        )

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return sorted(d.name for d in root.iterdir()
                      if (d / "open").is_file())

    def persisted_manifest(self, sid: str) -> dict:
        p = self.repo / ".bale" / "sessions" / sid / "manifest.json"
        self.assertTrue(p.is_file(), msg=f"expected persisted manifest {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def session_log(self, sid: str) -> str:
        p = self.repo / ".bale" / "logs" / f"{sid}.log"
        self.assertTrue(p.is_file(), msg=f"expected session log at {p}")
        return p.read_text(encoding="utf-8")

    def telemetry_record(self, sid: str) -> dict:
        p = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(p.is_file(), msg=f"expected telemetry record at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def apply_response(self, sid: str, *, name: str, path: str,
                       body: str, extra_flags: list = None):
        """Build a minimal valid response modifying `path` and apply it."""
        rdir = build_response_dir(
            self.tmp / name, sid,
            summary=f"per-sid fixture: rewrite {path}",
            entries=[{
                "path": path,
                "action": "modified",
                "reason": "the goal's rewrite; the fixture's in-scope "
                          "payload change",
                "data": body.encode("utf-8"),
            }],
        )
        tarball = tar_response_dir(rdir)
        return run_bale(
            self.install, ["apply", str(tarball), *(extra_flags or [])],
            cwd=self.repo, env=self.env)


class PerSidCheckpointE2ETest(PerSidFixture):
    """The S7 lifecycle, driven through real pack/apply."""

    def test_unknown_token_refuses_at_pack_with_no_session_state(self) -> None:
        """{date} is not a recognized token: pack refuses loudly at
        config read, names the token, and leaves no open session — and
        no half-substituted path ever appears in the output."""
        self.configure_base("claude/checkpoints/{date}.sh")
        result = self.pack("badtoken", "--include", "hello.txt")
        self.assertNotEqual(result.returncode, 0,
                            msg=f"stdout:\n{result.stdout}\n"
                                f"stderr:\n{result.stderr}")
        combined = result.stdout + result.stderr
        self.assertIn(UNKNOWN_TOKEN_PHRASE, combined)
        self.assertIn("{date}", combined,
                      msg="the refusal names the offending token")
        self.assertIn("{sid}", combined,
                      msg="the refusal names the one recognized token")
        self.assertEqual(self.open_sids(), [],
                         msg="a config-read refusal opens no session")

    def test_missing_resolved_refuses_preallocation_no_counter_chase(
            self) -> None:
        """A {sid} base with no committed per-sid file refuses at pack,
        naming the resolved path and the remedy, WITHOUT consuming the
        counter: committing the named checkpoint and re-running the
        same pack allocates the same sid — the resolved path the
        refusal named is the one the successful pack runs under."""
        self.configure_base(CP_PATTERN)
        sid = self.predicted_sid("chase")
        resolved = f"claude/checkpoints/{sid}.sh"

        refused = self.pack("chase", "--include", "hello.txt")
        self.assertNotEqual(refused.returncode, 0,
                            msg=f"stdout:\n{refused.stdout}\n"
                                f"stderr:\n{refused.stderr}")
        combined = refused.stdout + refused.stderr
        self.assertIn(MISSING_RESOLVED_PHRASE, combined)
        self.assertIn(resolved, combined,
                      msg="the refusal names the resolved path the "
                          "planner must commit")
        self.assertIn(REMEDY_PHRASE, combined)
        self.assertEqual(self.open_sids(), [],
                         msg="the refusal is pre-allocation: no session")
        self.assertFalse(
            (self.repo / ".bale" /
             f"counter-{date.today().isoformat()}").exists(),
            msg="the per-day counter was not consumed by the refusal")

        # The remedy loop converges: commit exactly what was named,
        # re-run the same pack, get the SAME sid.
        self.commit_files({resolved: checkpoint_script("chase-cp")},
                          "pin per-sid checkpoint")
        ok = self.pack("chase", "--include", "hello.txt")
        self.assertEqual(ok.returncode, 0,
                         msg=f"stdout:\n{ok.stdout}\nstderr:\n{ok.stderr}")
        self.assertEqual(self.open_sids(), [sid],
                         msg="the re-run pack allocates the sid the "
                             "refusal's resolved path embedded — no "
                             "counter chase")

    def test_resolved_path_threads_pack_apply_and_telemetry(self) -> None:
        """The happy path: pack stamps the RESOLVED path and committed
        bytes' hash; apply executes the per-sid script (asserted on
        executed output) and telemetry records the resolved identity
        with stamp_matched true."""
        self.configure_base(CP_PATTERN)
        sid = self.predicted_sid("percp")
        resolved = f"claude/checkpoints/{sid}.sh"
        shas = self.commit_files(
            {resolved: checkpoint_script("percp-marker")},
            "pin per-sid checkpoint")

        packed = self.pack("percp", "--include", "hello.txt")
        self.assertEqual(packed.returncode, 0,
                         msg=f"stdout:\n{packed.stdout}\n"
                             f"stderr:\n{packed.stderr}")
        self.assertEqual(self.open_sids(), [sid])

        stamp = self.persisted_manifest(sid)["provenance"]["checkpoint"]
        self.assertEqual(stamp["path"], resolved,
                         msg="the provenance stamp records the RESOLVED "
                             "path, exactly as the literal model "
                             "recorded the literal one")
        self.assertEqual(stamp["sha256"], shas[resolved])

        merged = self.apply_response(sid, name="happy", path="hello.txt",
                                     body="rewritten by the fixture\n")
        self.assertEqual(merged.returncode, 0,
                         msg=f"stdout:\n{merged.stdout}\n"
                             f"stderr:\n{merged.stderr}")

        log = self.session_log(sid)
        self.assertIn("percp-marker", log,
                      msg="the per-sid script's EXECUTED output is the "
                          "assertion — a resolved-but-never-run "
                          "checkpoint fails here")
        self.assertIn(resolved, log,
                      msg="the checkpoint band names the resolved path")

        record = self.telemetry_record(sid)
        cp = record["attempts"][-1]["checkpoint"]
        self.assertEqual(cp["configured"], True)
        self.assertEqual(cp["state"], "PASS")
        self.assertEqual(cp["script"]["path"], resolved)
        self.assertEqual(cp["script"]["sha256"], shas[resolved],
                         msg="the stamp hashes the executed base-tree "
                             "bytes of the per-sid file")
        self.assertIs(cp["stamp_matched"], True)

    def test_sibling_amendment_does_not_trip_other_sessions_stamp(
            self) -> None:
        """The goal sentence: two open sessions resolve to different
        files. An amendment to S2's checkpoint leaves S1's stamp
        verification untouched (S1 merges, stamp_matched true, S1's own
        pre-amendment marker runs), while S2's own apply refuses on the
        divergence until --accept-checkpoint-change admits it."""
        self.commit_files({"a.txt": "alpha\n", "b.txt": "beta\n"},
                          "add the two sessions' payload files")
        self.configure_base(CP_PATTERN)
        sid1 = self.predicted_sid("sib", 1)
        sid2 = self.predicted_sid("sib", 2)
        cp1 = f"claude/checkpoints/{sid1}.sh"
        cp2 = f"claude/checkpoints/{sid2}.sh"
        shas = self.commit_files(
            {cp1: checkpoint_script("sib1-marker"),
             cp2: checkpoint_script("sib2-v1")},
            "pin both sessions' checkpoints")

        p1 = self.pack("sib", "--include", "a.txt", "--write", "a.txt")
        self.assertEqual(p1.returncode, 0,
                         msg=f"stdout:\n{p1.stdout}\nstderr:\n{p1.stderr}")
        p2 = self.pack("sib", "--include", "b.txt", "--write", "b.txt")
        self.assertEqual(p2.returncode, 0,
                         msg=f"stdout:\n{p2.stdout}\nstderr:\n{p2.stderr}")
        self.assertEqual(self.open_sids(), sorted([sid1, sid2]))

        # The amendment: S2's oracle changes after both packs. Under
        # the shared-oracle model this is exactly the edit that tripped
        # every sibling's stamp.
        self.commit_files({cp2: checkpoint_script("sib2-v2")},
                          "amend S2's checkpoint mid-flight")

        merged = self.apply_response(sid1, name="sib1", path="a.txt",
                                     body="alpha rewritten\n")
        self.assertEqual(
            merged.returncode, 0,
            msg=f"S1 must be untouched by S2's amendment.\n"
                f"stdout:\n{merged.stdout}\nstderr:\n{merged.stderr}")
        log1 = self.session_log(sid1)
        self.assertIn("sib1-marker", log1,
                      msg="S1 executed its OWN per-sid checkpoint")
        self.assertNotIn("sib2", log1,
                         msg="no sibling checkpoint output in S1's log")
        rec1 = self.telemetry_record(sid1)
        cp1_stamp = rec1["attempts"][-1]["checkpoint"]
        self.assertEqual(cp1_stamp["script"]["path"], cp1)
        self.assertEqual(cp1_stamp["script"]["sha256"], shas[cp1])
        self.assertIs(cp1_stamp["stamp_matched"], True,
                      msg="the sibling amendment no longer trips this "
                          "session's stamp — the per-sid point")

        # S2's own stamp DID diverge: refusal without the flag...
        refused = self.apply_response(sid2, name="sib2a", path="b.txt",
                                      body="beta rewritten\n")
        self.assertNotEqual(refused.returncode, 0,
                            msg=f"stdout:\n{refused.stdout}\n"
                                f"stderr:\n{refused.stderr}")
        self.assertIn(STAMP_DIVERGED_PHRASE,
                      refused.stdout + refused.stderr)

        # ...and the deliberate admission runs the CURRENT bytes.
        admitted = self.apply_response(
            sid2, name="sib2b", path="b.txt", body="beta rewritten\n",
            extra_flags=["--accept-checkpoint-change"])
        self.assertEqual(admitted.returncode, 0,
                         msg=f"stdout:\n{admitted.stdout}\n"
                             f"stderr:\n{admitted.stderr}")
        log2 = self.session_log(sid2)
        self.assertIn("sib2-v2", log2,
                      msg="the admitted apply executes the CURRENT "
                          "(amended) base-tree bytes")
        rec2 = self.telemetry_record(sid2)
        cp2_stamp = rec2["attempts"][-1]["checkpoint"]
        self.assertEqual(cp2_stamp["script"]["path"], cp2)
        self.assertIs(cp2_stamp["stamp_matched"], False)


class BarePackRestorationTest(PerSidFixture):
    """The v0.4.9 bare-pack restoration under a {sid} base (Change A):
    the configured checkpoint is a structural exclusion at the walk —
    a default or broad include auto-excludes the checkpoints subtree,
    logged loudly per file — and the blindness refusal re-keys to
    explicit naming. Inherits the E2E fixture helpers; adds no new
    sandbox doctrine."""

    def bare_pack(self, slug: str, *extra: str):
        """A pack with NO --include and NO --write — the bare
        cold-start shape the §5 typed-surface contract protects."""
        return run_bale(
            self.install,
            ["pack", f"bare-shaped pack goal ({slug})",
             "--slug", slug, "--no-readme", *extra],
            cwd=self.repo, env=self.env,
        )

    def test_bare_default_pack_auto_excludes_and_passes(self) -> None:
        """The ratified goal sentence: a bare default pack in a
        checkpoint-configured project works again. The blindness gate
        passes, the walk drops the checkpoints subtree (the session's
        own file AND a past session's — dead weight to a worker) with
        a loud per-file log naming the remedy, and the shipped
        manifest's context_included carries no checkpoint path."""
        self.configure_base(CP_PATTERN)
        sid = self.predicted_sid("bare")
        own = f"claude/checkpoints/{sid}.sh"
        past = "claude/checkpoints/2026-06-01-past-001.sh"
        self.commit_files(
            {own: checkpoint_script("bare-own"),
             past: checkpoint_script("bare-past")},
            "pin per-sid checkpoint plus a past session's")

        packed = self.bare_pack("bare")
        self.assertEqual(
            packed.returncode, 0,
            msg=f"stdout:\n{packed.stdout}\nstderr:\n{packed.stderr}")
        combined = packed.stdout + packed.stderr
        self.assertIn("checkpoint blindness gate passed", combined)
        for dropped in (own, past):
            self.assertIn(dropped, combined,
                          msg="the walk logs each drop, naming the file")
        self.assertIn(AUTO_EXCLUDE_PHRASE, combined)
        self.assertIn("--allow-checkpoint-in-scope", combined,
                      msg="the drop line names its successor")
        manifest = self.persisted_manifest(sid)
        self.assertEqual(
            [p for p in manifest["context_included"]
             if "claude/checkpoints" in p], [],
            msg="the shipped read set carries no checkpoint path")
        # The stamp still records the session's own resolved oracle.
        self.assertEqual(manifest["provenance"]["checkpoint"]["path"], own)
        self.assertIs(
            manifest["provenance"]["checkpoint_scope_admitted"], False)
        self.assertNotIn("checkpoint_waived", manifest["provenance"],
                         msg="a scoped (non-empty-forecast) pack never "
                             "stamps the waiver key")

    def test_explicit_naming_refuses_file_and_prefix_forms(self) -> None:
        """Explicit naming is the read-side key: an include entry equal
        to a file strictly under the static prefix, or equal to the
        prefix itself, refuses pre-sid without the flag."""
        self.configure_base(CP_PATTERN)
        past = "claude/checkpoints/2026-06-01-past-001.sh"
        self.commit_files({past: checkpoint_script("past")}, "pin past")

        for form, include in (("file", past),
                              ("prefix", "claude/checkpoints")):
            refused = self.pack(f"exn-{form}", "--include", include)
            self.assertNotEqual(
                refused.returncode, 0,
                msg=f"{form} form should refuse:\n{refused.stdout}\n"
                    f"{refused.stderr}")
            combined = refused.stdout + refused.stderr
            self.assertIn(READ_NAME_PHRASE, combined)
            self.assertEqual(self.open_sids(), [],
                             msg="refusal is pre-sid: no session state")

    def test_flag_ships_bytes_and_stamps_admission(self) -> None:
        """--allow-checkpoint-in-scope disables auto-exclusion: the
        delegated maintenance session receives the bytes, and the
        admission stamps exactly as before — one flag, one stamp."""
        self.configure_base(CP_PATTERN)
        sid = self.predicted_sid("maint")
        own = f"claude/checkpoints/{sid}.sh"
        past = "claude/checkpoints/2026-06-01-past-001.sh"
        self.commit_files(
            {own: checkpoint_script("own"),
             past: checkpoint_script("past")},
            "pin checkpoints")
        packed = self.pack("maint", "--include", "claude/checkpoints",
                           "--allow-checkpoint-in-scope")
        self.assertEqual(
            packed.returncode, 0,
            msg=f"stdout:\n{packed.stdout}\nstderr:\n{packed.stderr}")
        self.assertIn("FORCE:", packed.stdout + packed.stderr)
        manifest = self.persisted_manifest(sid)
        self.assertIs(
            manifest["provenance"]["checkpoint_scope_admitted"], True)
        shipped = [p for p in manifest["context_included"]
                   if "claude/checkpoints" in p]
        self.assertEqual(sorted(shipped),
                         [f"context/{past}", f"context/{own}"],
                         msg="the admitted pack ships the subtree")

    def test_forecast_covering_write_still_refuses(self) -> None:
        """The forecast half is untouched for a TYPED --write: a
        forecast covering the checkpoints subtree remains the graver
        self-oracle shape and refuses without the flag."""
        self.configure_base(CP_PATTERN)
        past = "claude/checkpoints/2026-06-01-past-001.sh"
        self.commit_files({past: checkpoint_script("past")}, "pin past")
        refused = self.pack("wfc", "--include", "hello.txt",
                            "--write", "claude/checkpoints")
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn(FORECAST_COVER_PHRASE,
                      refused.stdout + refused.stderr)
        self.assertEqual(self.open_sids(), [])


class ReadOnlyWaiverTest(PerSidFixture):
    """The v0.4.9 read-only checkpoint waiver (Change B): an empty
    resolved write forecast waives the per-session checkpoint — the
    checkpoint is the misunderstanding control for landed work, and a
    []-forecast session mechanically cannot land — with the waiver
    stamped into provenance so the ledger distinguishes waived from
    unconfigured."""

    def test_readonly_pack_waives_missing_checkpoint(self) -> None:
        """A read-only pack under a {sid} base with NO committed
        checkpoint succeeds; provenance stamps checkpoint: null plus
        checkpoint_waived: "read-only"; the waiver is logged."""
        self.configure_base(CP_PATTERN)
        sid = self.predicted_sid("ro")
        packed = run_bale(
            self.install,
            ["pack", "read-only master pack under a {sid} base",
             "--slug", "ro", "--read-only", "--include", "hello.txt",
             "--no-readme"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            packed.returncode, 0,
            msg=f"stdout:\n{packed.stdout}\nstderr:\n{packed.stderr}")
        self.assertIn(WAIVER_PHRASE, packed.stdout + packed.stderr)
        manifest = self.persisted_manifest(sid)
        self.assertEqual(manifest["resolved_scope"], [])
        self.assertIsNone(manifest["provenance"]["checkpoint"])
        self.assertEqual(manifest["provenance"]["checkpoint_waived"],
                         "read-only")

    def test_scoped_pack_still_requires_checkpoint(self) -> None:
        """The waiver is read-only-shaped only: the sibling refusal
        test (test_missing_resolved_refuses_preallocation_no_counter_
        chase) pins the scoped-pack requirement and the
        no-counter-chase property in full; this test pins the boundary
        directly beside the waiver — same repo state, scoped shape,
        refusal — so a future waiver widening trips a named test."""
        self.configure_base(CP_PATTERN)
        refused = self.pack("scoped", "--include", "hello.txt")
        self.assertNotEqual(refused.returncode, 0)
        combined = refused.stdout + refused.stderr
        self.assertIn(MISSING_RESOLVED_PHRASE, combined)
        self.assertNotIn(WAIVER_PHRASE, combined)


class WaiverSchemaUnitTest(unittest.TestCase):
    """The additive checkpoint_waived key, validated at the schema
    level through the lint's embedded generic validator — the request
    schema file is the instance's schema of record, and the closed
    enum refuses any spelling but "read-only"."""

    @classmethod
    def setUpClass(cls) -> None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "response_lint_for_schema_test",
            REPO_ROOT / "tools" / "response_lint.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        # Hold the MODULE, not the bare function: a plain function
        # assigned as a class attribute binds as a method, silently
        # feeding `self` as the instance under validation — the
        # vacuous-pass shape this suite exists to refuse.
        cls.lint = module
        cls.request_schema = json.loads(
            (REPO_ROOT / "schemas" /
             "request-manifest.schema.json").read_text(encoding="utf-8"))

    def minimal_manifest(self, provenance_extra: dict) -> dict:
        provenance = {
            "bale_version": "0.4.9",
            "contract_docs": {"CLAUDE.md": "a", "TARBALL.md": "b",
                              "DOCS.md": "c", "CODE.md": "d"},
            "packer": "test",
            "work_class": "meta",
            "checkpoint": None,
            "checkpoint_scope_admitted": False,
        }
        provenance.update(provenance_extra)
        return {
            "session_id": "2026-08-14-x-001",
            "project": "p",
            "goal": "g",
            "depends_on": {"previous_response": None,
                           "previous_probe": None},
            "constraints": [],
            "out_of_scope": [],
            "expects_probe": "claude-decides",
            "context_included": ["context/hello.txt"],
            "resolved_scope": [],
            "provenance": provenance,
        }

    def test_waived_manifest_validates(self) -> None:
        errors = self.lint.schema_validate(
            self.minimal_manifest({"checkpoint_waived": "read-only"}),
            self.request_schema)
        self.assertEqual(errors, [], msg="; ".join(errors))

    def test_unwaived_manifest_validates_without_the_key(self) -> None:
        errors = self.lint.schema_validate(
            self.minimal_manifest({}), self.request_schema)
        self.assertEqual(errors, [], msg="; ".join(errors))

    def test_unknown_waiver_value_refuses(self) -> None:
        errors = self.lint.schema_validate(
            self.minimal_manifest({"checkpoint_waived": "always"}),
            self.request_schema)
        self.assertTrue(errors,
                        msg="the enum is closed — extend by schema "
                            "edit, not free text")


if __name__ == "__main__":
    unittest.main()
