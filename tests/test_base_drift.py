#!/usr/bin/env python3
"""Hermetic E2E for the base-drift stamp and apply gate (board 41).

Pins the feature's load-bearing claims end to end:

- **The stamp**: `bale pack` writes `provenance.base_files` into the
  request manifest — per-file sha256s of the resolved write forecast's
  committed bytes at the pack-time tip, with directory forecast
  entries enumerated to the committed files under them (per-file
  granularity, the ratified default) and `{}` for the read-only
  empty forecast.
- **The gate, refusing**: an intervening commit to a stamped file
  between pack and apply refuses at apply pre-flight with the
  BASE-DRIFT-REFUSED report, outcome `base-drift-refused` in
  telemetry, the session open — and, the hazard the gate exists for,
  the moved base bytes SURVIVE (nothing staged, nothing merged: the
  lost-update is prevented, not merely reported).
- **The override**: `--accept-base-drift <path>` admits exactly the
  named path — the response's bytes land over the moved base, the
  admission is stamped as `base_drift_overrides` in the applied
  attempt's telemetry.
- **The clean path**: an unmoved base applies with no refusal and no
  base-drift output.
- **Legacy tolerance**: a request whose manifest carries no
  `provenance.base_files` key (pre-feature / hand-rolled) applies
  exactly as today — the same intervening edit that refuses a stamped
  request passes a stampless one.
- **New-in-response files**: a created path has no base bytes, is
  absent from the stamp, and never refuses.
- **Retry-side flag parity**: `bale retry --accept-base-drift` exists
  with the same per-path, repeatable shape (pinned constraint).

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring. Responses
are built through the harness's shared fixture builder so the gate is
reached through the same pre-flight every real response passes.
Generation-heavy cases (full pack + apply/merge cycles) sit behind the
harness's slow gate per the 0.7s criterion (TARBALL.md §7.6); the
stamp-shape and flag-parity cases stay in the default run.

Run directly::

    python3 tests/test_base_drift.py

or via ``python3 -m unittest discover -s tests`` (set BALE_TEST_SLOW=1
for the full suite).
"""

from __future__ import annotations

import hashlib
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
    slow,
    tar_response_dir,
)

# Sentinels for the surfaces this file pins. Kept in one place so a
# message rewording breaks one line, not several assertions.
REFUSAL_MARKER = "BASE-DRIFT-REFUSED"
STAMP_LOG_MARKER = "base-drift stamp covers"
STAMPLESS_LOG_MARKER = "no base-drift provenance stamp"
FORCE_ADMIT_PHRASE = "base drift admitted by --accept-base-drift"
NO_EFFECT_PHRASE = "--accept-base-drift named path(s) with no matching"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class BaseDriftBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-basedrift-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        # A committed tree the forecast can cover: src/a.txt (the file
        # the drift scenarios move) and src/b.txt (a stamped bystander
        # that never moves), both tracked at the pack-time tip.
        self.base_a = b"original a\n"
        self.base_b = b"original b\n"
        for rel, data in (("src/a.txt", self.base_a),
                          ("src/b.txt", self.base_b)):
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(data)
        run_checked(["git", "add", "src/a.txt", "src/b.txt"],
                    cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "fixture tree"],
                    cwd=self.repo, env=self.genv)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack(self, *extra: str, slug: str = "base-drift"):
        """A fully specified piped pack forecasting src/ (a directory
        entry, so the stamp's per-file enumeration is exercised on
        every path through here)."""
        return run_bale(
            self.install,
            [
                "pack", "base drift surface test goal",
                "--slug", slug,
                "--include", "src",
                "--write", "src",
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def assert_pack_ok(self, result) -> str:
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        sids = self.open_sids()
        self.assertTrue(sids, msg="pack succeeded but no session is open")
        return sids[-1]

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        entries = [d for d in root.iterdir() if (d / "open").is_file()]
        entries.sort(key=lambda d: (d.stat().st_mtime, d.name))
        return [d.name for d in entries]

    def stamped_manifest(self, sid: str) -> dict:
        p = self.repo / ".bale" / "sessions" / sid / "manifest.json"
        self.assertTrue(p.is_file(), msg=f"no stamped manifest at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def telemetry_record(self, sid: str) -> dict:
        p = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(p.is_file(), msg=f"no telemetry record at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def move_base(self, rel: str = "src/a.txt",
                  data: bytes = b"moved by an intervening commit\n"
                  ) -> bytes:
        """Commit an intervening edit on main — the base moves under
        the open session, exactly the lost-update setup."""
        (self.repo / rel).write_bytes(data)
        run_checked(["git", "add", rel], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", f"intervening edit to {rel}"],
                    cwd=self.repo, env=self.genv)
        return data

    def response_tarball(self, sid: str, *, path: str = "src/a.txt",
                         action: str = "modified",
                         data: bytes = None) -> Path:
        """A minimal valid response touching one path, built through
        the harness's shared fixture builder (stale-based by
        construction: its bytes derive from the pack-time originals,
        never from any intervening edit)."""
        if data is None:
            data = f"rewritten by {sid}\n".encode("utf-8")
        rdir = build_response_dir(
            self.tmp / f"resp-{path.replace('/', '-')}-{action}", sid,
            summary="base-drift fixture: one change exercising the gate",
            entries=[{
                "path": path,
                "action": action,
                "reason": "fixture change exercising the base-drift gate "
                          "against a stamped forecast",
                "data": data,
            }],
        )
        return tar_response_dir(rdir)


class BaseStampTest(BaseDriftBase):
    """Pack writes the stamp; its content is the committed base."""

    def test_stamp_present_and_correct_after_pack(self) -> None:
        """provenance.base_files holds per-file sha256s of the
        committed HEAD bytes for every file the directory forecast
        entry covers — the per-file enumeration of a directory entry,
        the ratified default."""
        result = self.pack()
        sid = self.assert_pack_ok(result)
        self.assertIn(STAMP_LOG_MARKER, result.stderr + result.stdout)
        provenance = self.stamped_manifest(sid).get("provenance") or {}
        self.assertIn("base_files", provenance,
                      msg="pack stamped no provenance.base_files")
        self.assertEqual(
            provenance["base_files"],
            {
                "src/a.txt": sha256_hex(self.base_a),
                "src/b.txt": sha256_hex(self.base_b),
            },
        )

    def test_uncommitted_forecast_file_absent_from_stamp(self) -> None:
        """A forecast-covered file with no committed base bytes (an
        untracked working-tree file) enumerates nothing — absent from
        the map, never a hash of working-tree bytes."""
        (self.repo / "src" / "untracked.txt").write_bytes(b"wip\n")
        sid = self.assert_pack_ok(self.pack())
        base_files = (self.stamped_manifest(sid).get("provenance")
                      or {}).get("base_files") or {}
        self.assertNotIn("src/untracked.txt", base_files)
        self.assertIn("src/a.txt", base_files)

    def test_read_only_pack_stamps_empty_map(self) -> None:
        """The empty forecast stamps base_files: {} — key present
        (uniform bale-built shape), covering nothing."""
        result = run_bale(
            self.install,
            ["pack", "read-only base drift shape", "--slug", "ro-shape",
             "--include", "src", "--read-only", "--no-readme"],
            cwd=self.repo, env=self.env,
        )
        sid = self.assert_pack_ok(result)
        provenance = self.stamped_manifest(sid).get("provenance") or {}
        self.assertIn("base_files", provenance)
        self.assertEqual(provenance["base_files"], {})


class BaseDriftGateTest(BaseDriftBase):
    """Apply compares the intersection and refuses drift."""

    def test_moved_base_refuses_and_moved_bytes_survive(self) -> None:
        """The lost-update case: an intervening commit to a stamped
        file refuses the apply pre-staging — and the moved bytes are
        still on disk and at the branch tip afterwards, which is the
        entire point of refusing."""
        sid = self.assert_pack_ok(self.pack())
        moved = self.move_base()
        tarball = self.response_tarball(sid)
        result = run_bale(
            self.install, ["apply", str(tarball), "--no-interact"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn(REFUSAL_MARKER, result.stdout)
        # The hazard did not fire: the intervening edit survives in the
        # working tree and at the target tip.
        self.assertEqual((self.repo / "src" / "a.txt").read_bytes(), moved)
        # Session stays open (a later attempt supersedes the refusal).
        self.assertIn(sid, self.open_sids())
        # Telemetry records the distinct, dispatchable outcome.
        record = self.telemetry_record(sid)
        outcomes = [a.get("outcome") for a in record.get("attempts", [])]
        self.assertIn("base-drift-refused", outcomes)
        refused = [a for a in record["attempts"]
                   if a.get("outcome") == "base-drift-refused"][-1]
        self.assertEqual(refused.get("base_drift_overrides"), [])

    def test_dry_run_predicts_refusal_without_telemetry(self) -> None:
        """--dry-run reports the same refusal (exit 1, dry-run rows)
        and records no telemetry attempt for it — a dry-run has no
        outcome."""
        sid = self.assert_pack_ok(self.pack())
        self.move_base()
        tarball = self.response_tarball(sid)
        result = run_bale(
            self.install, ["apply", str(tarball), "--dry-run"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn(REFUSAL_MARKER, result.stdout)
        record = self.telemetry_record(sid)
        outcomes = [a.get("outcome") for a in record.get("attempts", [])]
        self.assertNotIn("base-drift-refused", outcomes,
                         msg="a dry-run refusal must record no attempt")

    def test_clean_base_passes_unrefused(self) -> None:
        """No intervening edit: the stamped hashes still match and the
        gate adds no output on the pass path."""
        sid = self.assert_pack_ok(self.pack())
        tarball = self.response_tarball(sid)
        result = run_bale(
            self.install, ["apply", str(tarball), "--dry-run"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertNotIn(REFUSAL_MARKER, result.stdout)

    def test_created_path_absent_from_stamp_never_refuses(self) -> None:
        """A file the response creates has no base bytes and no stamp
        entry — the changes[]∩stamp intersection excludes it, so the
        gate compares nothing for it (the brief's null/absent-must-
        not-refuse determination)."""
        sid = self.assert_pack_ok(self.pack())
        tarball = self.response_tarball(
            sid, path="src/new.txt", action="created",
            data=b"created by the response\n")
        result = run_bale(
            self.install, ["apply", str(tarball), "--dry-run"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertNotIn(REFUSAL_MARKER, result.stdout)

    def test_stampless_legacy_manifest_applies_as_today(self) -> None:
        """Additive/legacy tolerance: strip provenance.base_files from
        the persisted request manifest (simulating a pre-feature or
        hand-rolled request), move the base the same way that refuses
        a stamped request — and the apply proceeds, with the skip
        logged rather than silent."""
        sid = self.assert_pack_ok(self.pack())
        manifest_path = (self.repo / ".bale" / "sessions" / sid
                         / "manifest.json")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        del manifest["provenance"]["base_files"]
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n",
                                 encoding="utf-8")
        self.move_base()
        tarball = self.response_tarball(sid)
        result = run_bale(
            self.install, ["apply", str(tarball), "--dry-run"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertNotIn(REFUSAL_MARKER, result.stdout)
        self.assertIn(STAMPLESS_LOG_MARKER,
                      result.stdout + result.stderr,
                      msg="the stampless skip must be logged, not silent")


class BaseDriftOverrideTest(BaseDriftBase):
    """--accept-base-drift admits exactly the named path."""

    def test_unnamed_drift_still_refuses_beside_an_admission(self) -> None:
        """Two stamped files move; the override names one. The other
        still refuses — per-path admission, never a blanket accept —
        and the partial admission is visible in the refusal."""
        sid = self.assert_pack_ok(self.pack())
        self.move_base("src/a.txt")
        self.move_base("src/b.txt", b"b moved too\n")
        rdir = build_response_dir(
            self.tmp / "resp-two", sid,
            summary="base-drift fixture: two changes, one admitted",
            entries=[
                {"path": "src/a.txt", "action": "modified",
                 "reason": "fixture change on the admitted path",
                 "data": b"response a\n"},
                {"path": "src/b.txt", "action": "modified",
                 "reason": "fixture change on the refused path",
                 "data": b"response b\n"},
            ],
        )
        tarball = tar_response_dir(rdir)
        result = run_bale(
            self.install,
            ["apply", str(tarball), "--accept-base-drift", "src/a.txt"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn(REFUSAL_MARKER, result.stdout)
        self.assertIn("src/b.txt", result.stdout)
        self.assertIn("src/a.txt", result.stdout,
                      msg="the partial admission is reported")
        # The refused attempt records what the partial override admitted.
        record = self.telemetry_record(sid)
        refused = [a for a in record["attempts"]
                   if a.get("outcome") == "base-drift-refused"][-1]
        self.assertEqual(refused.get("base_drift_overrides"),
                         ["src/a.txt"])

    def test_unused_flag_logs_no_effect(self) -> None:
        """A named path with no matching drift is harmless but loud —
        a silently ignored override flag is the surprise the logging
        rules exist to prevent."""
        sid = self.assert_pack_ok(self.pack())
        tarball = self.response_tarball(sid)
        result = run_bale(
            self.install,
            ["apply", str(tarball), "--dry-run",
             "--accept-base-drift", "src/a.txt"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn(NO_EFFECT_PHRASE, result.stdout + result.stderr)

    @slow
    def test_override_lands_response_bytes_over_moved_base(self) -> None:
        """The full admitted path: the response's bytes land (merged
        into main), the intervening edit is deliberately superseded,
        and the applied attempt's telemetry stamps the admission."""
        sid = self.assert_pack_ok(self.pack())
        self.move_base()
        response_bytes = f"rewritten by {sid}\n".encode("utf-8")
        tarball = self.response_tarball(sid, data=response_bytes)
        result = run_bale(
            self.install,
            ["apply", str(tarball), "--no-interact",
             "--accept-base-drift", "src/a.txt"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertIn(FORCE_ADMIT_PHRASE, result.stdout + result.stderr)
        self.assertEqual((self.repo / "src" / "a.txt").read_bytes(),
                         response_bytes)
        record = self.telemetry_record(sid)
        applied = [a for a in record["attempts"]
                   if a.get("outcome") == "applied"]
        self.assertTrue(applied, msg="no applied attempt recorded")
        self.assertEqual(applied[-1].get("base_drift_overrides"),
                         ["src/a.txt"])


class RetryFlagParityTest(BaseDriftBase):
    """The pinned constraint: --accept-base-drift exists on retry with
    the apply flag's grammar."""

    def test_retry_parser_carries_the_flag(self) -> None:
        result = run_bale(self.install, ["retry", "--help"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--accept-base-drift", result.stdout)
        self.assertIn("PATH", result.stdout)

    def test_apply_parser_carries_the_flag(self) -> None:
        result = run_bale(self.install, ["apply", "--help"],
                          cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("--accept-base-drift", result.stdout)

    @slow
    def test_retry_reruns_the_gate_and_admits_per_invocation(self) -> None:
        """A HOLDed session retried against a moved base refuses at
        retry (the override is never carried forward), then admits
        when THIS retry invocation re-states the flag."""
        sid = self.assert_pack_ok(self.pack())
        # First attempt HOLDs (validation fails), leaving the session
        # retryable.
        failing_validation = (
            "#!/usr/bin/env bash\n"
            "echo \"[FAIL] fixture check\"\n"
            "exit 1\n"
        )
        rdir = build_response_dir(
            self.tmp / "resp-hold", sid,
            summary="base-drift fixture: HOLD then retry",
            entries=[{
                "path": "src/a.txt", "action": "modified",
                "reason": "fixture change that HOLDs first",
                "data": b"first attempt\n",
            }],
            validation_sh=failing_validation,
        )
        first = run_bale(
            self.install,
            ["apply", str(tar_response_dir(rdir)), "--no-interact"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(first.returncode, 1, msg=first.stdout)
        # Base moves after the HOLD; the retry's gate must see it.
        self.move_base()
        retry_bytes = b"retry attempt\n"
        retry_tarball = self.response_tarball(sid, data=retry_bytes)
        refused = run_bale(
            self.install,
            ["retry", str(retry_tarball), "--no-interact"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(refused.returncode, 1, msg=refused.stdout)
        self.assertIn(REFUSAL_MARKER, refused.stdout)
        admitted = run_bale(
            self.install,
            ["retry", str(retry_tarball), "--no-interact",
             "--accept-base-drift", "src/a.txt"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            admitted.returncode, 0,
            msg=f"stdout:\n{admitted.stdout}\nstderr:\n{admitted.stderr}",
        )
        self.assertEqual((self.repo / "src" / "a.txt").read_bytes(),
                         retry_bytes)


if __name__ == "__main__":
    unittest.main()
