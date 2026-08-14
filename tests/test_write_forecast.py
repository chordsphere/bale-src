#!/usr/bin/env python3
"""Hermetic E2E for the write-forecast pack surface (ADR-0015, board 13
Session A).

Pins the separation's load-bearing claims at the pack surface:

- `--write` records the forecast — `sessions/<sid>/scope.json` and the
  manifest's `resolved_scope` stamp hold the resolved --write set, not
  the include set, from one source.
- The compatibility default: a pack without `--write` records exactly
  what it recorded before the separation (the resolved include set),
  so separation is opt-in per pack.
- Arg-parse rules: `--write` contradicts `--read-only` (refused before
  any prompt), and entries must name existing paths (ADR-0014's rule
  held on the forecast surface).
- The thesis itself: two packs whose *includes* overlap but whose
  *forecasts* are disjoint run concurrently — broad reading stops
  costing locks — while intersecting forecasts still refuse, in
  forecast vocabulary.
- The consumers read the forecast: the apply-side own-scope drift gate
  refuses a changes[] path the session was *shown* (in includes) but
  did not *forecast*, and admits a forecast path.
- The wizard's where-will-changes-land follow-up: Enter keeps the
  includes default; typed paths become the forecast; a typed --write
  skips the read-only half of the session-shape exchange.
- Checkpoint blindness under separation (board 13 E3 as ratified):
  the covering refusal keys on the forecast, and the new read-side
  refusal fires when the includes would ship the oracle's bytes while
  the forecast excludes it — same override flag, same provenance
  stamp for both halves.
- `bale status` labels the recorded set as the write forecast (Q4's
  minimal rendering).

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring. The wizard
tests drive bale through a real pseudo-terminal (the wizard engages
only on a TTY), and the drift-gate tests build a minimal but fully
valid response through the harness's shared fixture builder so the
gate is reached through the same pre-flight every real response
passes.

Run directly::

    python3 tests/test_write_forecast.py

or via ``python3 -m unittest discover -s tests``.
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
    run_bale_pty,
    run_checked,
    tar_response_dir,
)

# Sentinels for the surfaces this file pins. Kept in one place so a
# message rewording breaks one line, not several assertions.
CONTRADICTION_MARKER = "--write and --read-only are contradictory"
MISSING_WRITE_MARKER = "--write path does not exist"
INTERSECT_MARKER = "pack write forecast intersects"
DRIFT_REFUSAL_MARKER = "SCOPE-DRIFT-REFUSED"
FORECAST_QUESTION_MARKER = "Where will changes land?"
SHAPE_QUESTION_MARKER = "Will this session land changes"
FORECAST_COVER_PHRASE = "write forecast covers the blind checkpoint"
READ_NAME_PHRASE = "pack includes name the blind checkpoint explicitly"
AUTO_EXCLUDE_PHRASE = "never ships incidentally"
STATUS_ROW_LABEL = "write forecast"

CHECKPOINT_PATH = "scripts/check.sh"


class WriteForecastBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-forecast-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        # A second committed tree area so forecasts and includes can be
        # narrowed independently of the harness's hello.txt: src/a.txt
        # and lib/b.txt, both tracked.
        for rel in ("src/a.txt", "lib/b.txt"):
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"{rel}\n", encoding="utf-8")
        run_checked(["git", "add", "src/a.txt", "lib/b.txt"],
                    cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "fixture tree"],
                    cwd=self.repo, env=self.genv)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack(self, *extra: str, slug: str = "session-a"):
        """A fully specified piped pack; extras append to the base form.
        Includes the whole src/ + lib/ pair by default so forecast
        narrowing has something to be narrower than."""
        return run_bale(
            self.install,
            [
                "pack", "write forecast surface test goal",
                "--slug", slug,
                "--include", "src", "lib",
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

    def scope_json(self, sid: str):
        p = self.repo / ".bale" / "sessions" / sid / "scope.json"
        if not p.is_file():
            return None
        return json.loads(p.read_text(encoding="utf-8"))

    def stamped_manifest(self, sid: str) -> dict:
        p = self.repo / ".bale" / "sessions" / sid / "manifest.json"
        self.assertTrue(p.is_file(), msg=f"no stamped manifest at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def response_tarball(self, sid: str, *, path: str) -> Path:
        """A minimal valid response modifying one existing file, built
        through the harness's shared fixture builder."""
        data = f"rewritten by {sid}\n".encode("utf-8")
        rdir = build_response_dir(
            self.tmp / f"resp-{path.replace('/', '-')}", sid,
            summary="write-forecast fixture: modify one file",
            entries=[{
                "path": path,
                "action": "modified",
                "reason": "fixture change exercising the own-forecast "
                          "drift gate against a narrowed forecast",
                "data": data,
            }],
        )
        return tar_response_dir(rdir)


class ForecastRecordTest(WriteForecastBase):
    """--write records the forecast; absence keeps the include default."""

    def test_write_flag_records_forecast_not_includes(self) -> None:
        """scope.json and the resolved_scope stamp hold the --write set."""
        sid = self.assert_pack_ok(self.pack("--write", "src"))
        self.assertEqual(self.scope_json(sid), ["src"])
        self.assertEqual(self.stamped_manifest(sid)["resolved_scope"],
                         ["src"])

    def test_absent_write_defaults_to_includes(self) -> None:
        """The compatibility default: no --write records the resolved
        include set, byte-for-byte the pre-separation record."""
        sid = self.assert_pack_ok(self.pack())
        self.assertEqual(self.scope_json(sid), ["lib", "src"])
        self.assertEqual(self.stamped_manifest(sid)["resolved_scope"],
                         ["lib", "src"])

    def test_write_need_not_be_subset_of_includes(self) -> None:
        """A session can be shown one thing and forecast landing
        another (design brief I.1) — no subset rule couples the two
        surfaces."""
        sid = self.assert_pack_ok(
            self.pack("--write", "hello.txt"))  # not under src/ or lib/
        self.assertEqual(self.scope_json(sid), ["hello.txt"])

    def test_write_contradicts_read_only(self) -> None:
        """Refused at arg-parse, before any prompt or session state."""
        result = self.pack("--write", "src", "--read-only")
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn(CONTRADICTION_MARKER, result.stderr)
        self.assertEqual(self.open_sids(), [])

    def test_write_entries_must_exist(self) -> None:
        """ADR-0014's rule held on the forecast surface: entries name
        existing paths; new files are forecast via their directory."""
        result = self.pack("--write", "src/not-yet-written.txt")
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn(MISSING_WRITE_MARKER, result.stderr)
        self.assertEqual(self.open_sids(), [])


class ForecastGateTest(WriteForecastBase):
    """The disjointness gate reads forecasts, not includes."""

    def test_overlapping_includes_disjoint_forecasts_run_concurrently(
            self) -> None:
        """The thesis: both packs read src/ AND lib/; one forecasts
        src, the other lib — admitted side by side. Under the conflated
        model the second pack refused; the separation makes this the
        structural point of the feature."""
        first = self.assert_pack_ok(self.pack("--write", "src"))
        second = self.pack("--write", "lib", slug="session-b")
        self.assertEqual(
            second.returncode, 0,
            msg=f"stdout:\n{second.stdout}\nstderr:\n{second.stderr}",
        )
        sids = self.open_sids()
        self.assertEqual(len(sids), 2)
        self.assertIn(first, sids)

    def test_intersecting_forecasts_refuse_in_forecast_vocabulary(
            self) -> None:
        self.assert_pack_ok(self.pack("--write", "src"))
        second = self.pack("--write", "src/a.txt", slug="session-b")
        self.assertEqual(second.returncode, 1, msg=second.stdout)
        self.assertIn(INTERSECT_MARKER, second.stderr)
        self.assertIn("--write", second.stderr,
                      msg="the refusal's remedy names the forecast's "
                          "own lever")

    def test_default_forecast_still_conflicts_like_before(self) -> None:
        """No --write on either side: the include-set default keeps the
        pre-separation collision — nothing changes under anyone who
        never types the flag."""
        self.assert_pack_ok(self.pack())
        second = self.pack(slug="session-b")
        self.assertEqual(second.returncode, 1, msg=second.stdout)
        self.assertIn(INTERSECT_MARKER, second.stderr)


class ForecastConsumersTest(WriteForecastBase):
    """Downstream gates read the recorded forecast."""

    def test_drift_gate_refuses_shown_but_unforecast_path(self) -> None:
        """A path inside the includes but outside the forecast is
        drift: shown-and-landable are no longer the same set, and the
        own-scope drift gate proves it reads the forecast."""
        sid = self.assert_pack_ok(self.pack("--write", "src"))
        tarball = self.response_tarball(sid, path="lib/b.txt")
        result = run_bale(
            self.install, ["apply", str(tarball), "--dry-run"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        self.assertIn(DRIFT_REFUSAL_MARKER, result.stdout)
        self.assertIn(sid, self.open_sids())

    def test_forecast_path_passes_drift_gate(self) -> None:
        sid = self.assert_pack_ok(self.pack("--write", "src"))
        tarball = self.response_tarball(sid, path="src/a.txt")
        result = run_bale(
            self.install, ["apply", str(tarball), "--dry-run"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        self.assertNotIn(DRIFT_REFUSAL_MARKER, result.stdout)

    def test_status_labels_the_forecast(self) -> None:
        """Q4's minimal rendering: the session row names the recorded
        set as the write forecast."""
        self.assert_pack_ok(self.pack("--write", "src"))
        result = run_bale(
            self.install, ["status"], cwd=self.repo, env=self.env,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn(STATUS_ROW_LABEL, result.stdout)
        self.assertIn("src", result.stdout)


class ForecastWizardTest(WriteForecastBase):
    """The where-will-changes-land follow-up (evidence 37)."""

    def test_enter_default_keeps_includes_forecast(self) -> None:
        """The cold-start user presses Enter and gets exactly the
        pre-separation pack: forecast = resolved includes."""
        answers = (
            "wizard forecast default goal\n"  # goal
            "wiz-default\n"                   # slug
            "c\n"                             # session shape: code
            "\n"                              # forecast: Enter -> includes
            "\n" "\n" "\n"                    # excludes, constraints, oos
            "n\n"                             # README prompt: no
        )
        code, output = run_bale_pty(
            self.install, ["pack"], cwd=self.repo, env=self.env,
            answers=answers,
        )
        self.assertEqual(code, 0, msg=output)
        self.assertIn(FORECAST_QUESTION_MARKER, output)
        sids = self.open_sids()
        self.assertEqual(len(sids), 1, msg=output)
        # No --include either, so the include default is the whole tree.
        self.assertEqual(self.scope_json(sids[0]), ["."])

    def test_typed_paths_become_the_forecast(self) -> None:
        answers = (
            "wizard forecast typed goal\n"
            "wiz-typed\n"
            "c\n"                             # session shape: code
            "src lib/b.txt\n"                 # forecast: two entries
            "\n" "\n" "\n"
            "n\n"
        )
        code, output = run_bale_pty(
            self.install, ["pack"], cwd=self.repo, env=self.env,
            answers=answers,
        )
        self.assertEqual(code, 0, msg=output)
        sids = self.open_sids()
        self.assertEqual(len(sids), 1, msg=output)
        self.assertEqual(self.scope_json(sids[0]), ["lib/b.txt", "src"])

    def test_nonexistent_entry_reprompts(self) -> None:
        """A miss re-prompts interactively rather than failing the pack
        after the answers are in."""
        answers = (
            "wizard forecast reprompt goal\n"
            "wiz-reprompt\n"
            "c\n"
            "no/such/path\n"                  # forecast: rejected, re-ask
            "src\n"                           # forecast: accepted
            "\n" "\n" "\n"
            "n\n"
        )
        code, output = run_bale_pty(
            self.install, ["pack"], cwd=self.repo, env=self.env,
            answers=answers,
        )
        self.assertEqual(code, 0, msg=output)
        self.assertIn("do not exist", output)
        sids = self.open_sids()
        self.assertEqual(self.scope_json(sids[0]), ["src"])

    def test_read_only_answer_skips_follow_up(self) -> None:
        """The follow-up rides the lands-changes branch only: [r]
        records [] and never asks where changes land."""
        answers = (
            "wizard read-only goal\n"
            "wiz-ro\n"
            "r\n"                             # session shape: read-only
            "\n" "\n" "\n"
            "n\n"
        )
        code, output = run_bale_pty(
            self.install, ["pack"], cwd=self.repo, env=self.env,
            answers=answers,
        )
        self.assertEqual(code, 0, msg=output)
        self.assertNotIn(FORECAST_QUESTION_MARKER, output)
        sids = self.open_sids()
        self.assertEqual(self.scope_json(sids[0]), [])

    def test_typed_write_skips_read_only_half_and_follow_up(self) -> None:
        """--write on the wizard path declares lands-changes: the
        exchange asks only the work-class half (no [r] on offer) and
        the follow-up is already answered."""
        answers = (
            "wizard typed-write goal\n"
            "wiz-flag\n"
            "c\n"                             # work class only
            "\n" "\n" "\n"
            "n\n"
        )
        code, output = run_bale_pty(
            self.install, ["pack", "--write", "src"],
            cwd=self.repo, env=self.env, answers=answers,
        )
        self.assertEqual(code, 0, msg=output)
        self.assertNotIn(SHAPE_QUESTION_MARKER, output)
        self.assertNotIn(FORECAST_QUESTION_MARKER, output)
        self.assertIn("--write given", output)
        sids = self.open_sids()
        self.assertEqual(self.scope_json(sids[0]), ["src"])
        stamped = self.stamped_manifest(sids[0])
        self.assertEqual(stamped["provenance"]["work_class"], "code")


class ForecastBlindnessTest(WriteForecastBase):
    """Checkpoint blindness under separation (board 13 E3 as ratified;
    read side re-keyed at v0.4.9): forecast-keyed covering refusal on a
    TYPED --write + the read-side explicit-naming refusal, with
    incidental include coverage auto-excluding at the walk instead of
    refusing — one override flag, one stamp."""

    def configure_checkpoint(self) -> None:
        (self.repo / "bale.toml").write_text(
            f'[validation]\nbase = "{CHECKPOINT_PATH}"\n', encoding="utf-8")
        p = self.repo / CHECKPOINT_PATH
        p.parent.mkdir(parents=True, exist_ok=True)
        body = "#!/usr/bin/env bash\necho \"[PASS] cp\"\nexit 0\n"
        p.write_bytes(body.encode("utf-8"))
        p.chmod(0o755)
        run_checked(["git", "add", CHECKPOINT_PATH, "bale.toml"],
                    cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "pin blind checkpoint"],
                    cwd=self.repo, env=self.genv)

    def test_forecast_covering_checkpoint_refuses(self) -> None:
        self.configure_checkpoint()
        result = self.pack("--include", "scripts", "--write", "scripts")
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        combined = result.stdout + result.stderr
        self.assertIn(FORECAST_COVER_PHRASE, combined)
        self.assertIn("--write", combined,
                      msg="the forecast-side remedy names --write")

    def test_reads_naming_checkpoint_refuses(self) -> None:
        """The E3 read side, re-keyed at v0.4.9: forecast excludes the
        oracle, and an include entry NAMES it explicitly — an explicit
        ask to ship the oracle's bytes, refused pre-sid."""
        self.configure_checkpoint()
        result = self.pack("--include", CHECKPOINT_PATH, "--write", "src")
        self.assertEqual(result.returncode, 1, msg=result.stdout)
        combined = result.stdout + result.stderr
        self.assertIn(READ_NAME_PHRASE, combined)
        self.assertIn("drop the --include entry", combined,
                      msg="the read-side remedy names the include "
                          "entry as the lever")
        self.assertEqual(self.open_sids(), [],
                         msg="refusal is pre-sid: no session state")

    def test_broad_include_auto_excludes_instead_of_refusing(self) -> None:
        """The v0.4.9 restoration: forecast excludes the oracle, a
        BROAD include merely covers it — the pack succeeds, the walk
        drops the checkpoint loudly, and the shipped read set carries
        no checkpoint path."""
        self.configure_checkpoint()
        result = self.pack("--include", "scripts", "--write", "src")
        sid = self.assert_pack_ok(result)
        combined = result.stdout + result.stderr
        self.assertIn(AUTO_EXCLUDE_PHRASE, combined,
                      msg="the walk logs the drop loudly, naming the "
                          "checkpoint exclusion")
        self.assertIn(CHECKPOINT_PATH, combined,
                      msg="the drop line names the dropped file")
        stamped = self.stamped_manifest(sid)
        self.assertNotIn(
            f"context/{CHECKPOINT_PATH}", stamped["context_included"],
            msg="the shipped read set carries no checkpoint path")
        self.assertFalse(
            stamped["provenance"]["checkpoint_scope_admitted"],
            msg="nothing was admitted — the bytes were withheld, not "
                "delegated")

    def test_one_flag_admits_read_side_and_stamps(self) -> None:
        self.configure_checkpoint()
        result = self.pack("--include", "scripts", "--write", "src",
                           "--allow-checkpoint-in-scope")
        sid = self.assert_pack_ok(result)
        combined = result.stdout + result.stderr
        self.assertIn("FORCE", combined)
        stamped = self.stamped_manifest(sid)
        self.assertTrue(
            stamped["provenance"]["checkpoint_scope_admitted"],
            msg="the admission stamp covers the read-side half too — "
                "one flag, one stamp")
        # The forecast still recorded --write's set, not the includes.
        self.assertEqual(self.scope_json(sid), ["src"])

    def test_noncovering_pack_passes_and_stamps_false(self) -> None:
        self.configure_checkpoint()
        result = self.pack("--write", "src")  # includes: src, lib only
        sid = self.assert_pack_ok(result)
        stamped = self.stamped_manifest(sid)
        self.assertFalse(
            stamped["provenance"]["checkpoint_scope_admitted"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
