#!/usr/bin/env python3
"""Hermetic E2E for the open-time provenance stamps (v0.4.21, board 63).

Pins the board-63 contract: pack writes work_class and packer
provenance into the registry and the telemetry record at session OPEN,
so every exit path carries the pair — closing the blind spot where
sessions that closed without an apply (unlock, closed-read-only) were
invisible to per-class and per-packer rates.

The four outcome contracts, as this suite asserts them:

1. After a pack, `claude/telemetry/<sid>.json` exists with envelope
   outcome `opened` and one `opened` attempt (command `pack`) carrying
   `provenance: {work_class, packer}` — verbatim, unnormalized — plus
   the uniform epoch stamps every attempt gets from the one builder
   (scope_kind, sandbox_escaped, network_grant_exercised, cost).
2. `.bale/sessions/<sid>/provenance.json` carries exactly the same
   two fields — the registry-side home, readable without parsing the
   manifest copy.
3. A later unlock APPENDS to the open-time record: two attempts, the
   opened one intact, created_at preserved, envelope mirroring the
   closure. (The closure suite pins the same fact from the unlock
   side; this suite pins it from the open side.)
4. The record validates clean against the updated schema via
   validate_telemetry_record — the additive-change proof, alongside
   test_telemetry_extensions.py's checked-in-corpus regression run,
   which proves pre-epoch records keep validating.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_provenance_at_open.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

from harness import (
    bale_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
)


def load_install_module(install: Path, name: str):
    """Import a scratch-install bin/ module by path (the harness's
    absolute-path doctrine: the suite exercises exactly the bytes an
    installed bale would run)."""
    path = install / "bin" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"{name}_under_test",
                                                 str(path))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class ProvenanceAtOpenTest(unittest.TestCase):
    """Pack stamps the pair at open; close appends rather than clobbers."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-provopen-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack(self, *extra: str, slug: str = "provopen-a"):
        """A fully specified piped pack; extras append to the base form."""
        return run_bale(
            self.install,
            [
                "pack", "provenance at open test goal",
                "--slug", slug,
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

    def packed_sid(self, result) -> str:
        """Pack succeeded; return its sid (the newest registry entry)."""
        self.assert_ok(result)
        root = self.repo / ".bale" / "sessions"
        entries = [d for d in root.iterdir() if (d / "open").is_file()]
        self.assertTrue(entries, msg="pack succeeded but no session open")
        entries.sort(key=lambda d: (d.stat().st_mtime, d.name))
        return entries[-1].name

    def telemetry_record(self, sid: str) -> dict:
        p = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(p.is_file(),
                        msg=f"expected the open-time record at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def registry_provenance(self, sid: str) -> dict:
        p = self.repo / ".bale" / "sessions" / sid / "provenance.json"
        self.assertTrue(p.is_file(),
                        msg=f"expected the registry-side stamp at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    # -- contract 1: the open-time telemetry record ----------------------

    def test_pack_opens_record_with_provenance(self) -> None:
        """pack --work-class code --packer alice: the record exists at
        open, outcome `opened`, and the attempt carries the pair
        verbatim plus the uniform builder epoch stamps."""
        sid = self.packed_sid(
            self.pack("--work-class", "code", "--packer", "alice"))

        record = self.telemetry_record(sid)
        self.assertEqual(record["session_id"], sid)
        self.assertEqual(record["outcome"], "opened",
                         msg="no close event yet — the envelope mirrors "
                             "the open stamp")
        self.assertEqual(len(record["attempts"]), 1)
        attempt = record["attempts"][0]
        self.assertEqual(attempt["outcome"], "opened")
        self.assertEqual(attempt["command"], "pack")
        self.assertEqual(attempt["provenance"],
                         {"work_class": "code", "packer": "alice"},
                         msg="verbatim from the request manifest — no "
                             "normalization")
        self.assertEqual(attempt["scope"], ["hello.txt"],
                         msg="the recorded write forecast (defaulted from "
                             "the include set) stamps onto the open event")
        self.assertEqual(attempt["scope_kind"], "write-forecast",
                         msg="the opened attempt goes through the one "
                             "builder, so the epoch key is uniform")
        self.assertIn("cost", attempt,
                      msg="uniform builder stamps: the all-null cost "
                          "block rides on every post-epoch attempt")
        self.assertIs(attempt["sandbox_escaped"], False,
                      msg="known-negative: nothing executed at open")
        self.assertIsNone(attempt.get("closure_reason"),
                          msg="an open is not a closure")

    def test_unconfigured_packer_stamps_literal(self) -> None:
        """No --packer and no [identity].packer in the sandbox: the
        literal 'unconfigured' is stamped rather than omitted — the
        uniform-shape posture of build_provenance_block."""
        sid = self.packed_sid(self.pack("--work-class", "doc"))
        attempt = self.telemetry_record(sid)["attempts"][0]
        self.assertEqual(attempt["provenance"]["packer"], "unconfigured")
        self.assertEqual(attempt["provenance"]["work_class"], "doc")

    def test_read_only_pack_stamps_inferred_meta(self) -> None:
        """pack --read-only with no --work-class: the inferred 'meta'
        class reaches both stamps, and the opened attempt's scope is
        the empty forecast."""
        sid = self.packed_sid(self.pack("--read-only"))
        attempt = self.telemetry_record(sid)["attempts"][0]
        self.assertEqual(attempt["provenance"]["work_class"], "meta")
        self.assertEqual(attempt["scope"], [],
                         msg="the read-only shape's empty forecast, raw")
        self.assertEqual(self.registry_provenance(sid)["work_class"],
                         "meta")

    # -- contract 2: the registry-side stamp -----------------------------

    def test_registry_provenance_json_carries_the_pair(self) -> None:
        """.bale/sessions/<sid>/provenance.json is exactly the two
        fields — beside scope.json, no manifest parsing required."""
        sid = self.packed_sid(
            self.pack("--work-class", "code", "--packer", "alice"))
        stamp = self.registry_provenance(sid)
        self.assertEqual(stamp, {"work_class": "code", "packer": "alice"})
        # The pre-existing session-dir census still holds around it.
        sdir = self.repo / ".bale" / "sessions" / sid
        for name in ("manifest.json", "open", "origin_branch",
                     "scope.json"):
            self.assertTrue((sdir / name).is_file(),
                            msg=f"{name} must still be written")

    # -- contract 3: close-time writes append ----------------------------

    def test_unlock_appends_to_open_time_record(self) -> None:
        """pack then unlock: one file, two attempts — the opened stamp
        intact, created_at preserved, the envelope mirroring the
        closure. The HOLD-then-retry accumulation contract, proven on
        the unlock path the blind spot was about."""
        sid = self.packed_sid(
            self.pack("--work-class", "code", "--packer", "alice"))
        opened = self.telemetry_record(sid)
        self.assert_ok(run_bale(self.install, ["unlock"],
                                cwd=self.repo, env=self.env))

        record = self.telemetry_record(sid)
        self.assertEqual(record["created_at"], opened["created_at"],
                         msg="created_at is the OPEN time, preserved "
                             "across the close append")
        self.assertEqual(record["outcome"], "unlocked")
        self.assertEqual(len(record["attempts"]), 2,
                         msg="append, never duplicate or clobber")
        self.assertEqual(record["attempts"][0], opened["attempts"][0],
                         msg="the opened attempt survives byte-identical")
        closing = record["attempts"][-1]
        self.assertEqual(closing["outcome"], "unlocked")
        self.assertEqual(closing["closure_reason"], "abandoned")
        self.assertNotIn("provenance", closing,
                         msg="key presence is epoch-and-event membership: "
                             "the pair rides the opened attempt only")

    # -- contract 4: the updated schema agrees ---------------------------

    def test_open_time_record_validates_against_schema(self) -> None:
        """validate_telemetry_record returns [] on both the freshly
        opened record and the opened-then-unlocked one — the additive
        proof from the new-shape side (the extensions suite's corpus
        run proves the pre-epoch side)."""
        bv = load_install_module(self.install, "bale_validate")
        sid = self.packed_sid(
            self.pack("--work-class", "code", "--packer", "alice"))
        self.assertEqual(
            bv.validate_telemetry_record(self.telemetry_record(sid)), [])
        self.assert_ok(run_bale(self.install, ["unlock"],
                                cwd=self.repo, env=self.env))
        self.assertEqual(
            bv.validate_telemetry_record(self.telemetry_record(sid)), [])

    # -- read-side tolerance: the corpus keeps aggregating ---------------

    def test_stats_counts_open_record_as_in_flight(self) -> None:
        """bale_stats over a corpus containing an open-time record:
        the `opened` envelope outcome lands in the in-flight count
        (closure_category's unknown-vocabulary path — reported, never
        dropped), and the aggregation runs clean. The known-vocabulary
        row for `opened` is board 44's read side."""
        stats = load_install_module(self.install, "bale_stats")
        sid = self.packed_sid(
            self.pack("--work-class", "code", "--packer", "alice"))
        record = self.telemetry_record(sid)
        with tempfile.TemporaryDirectory() as td:
            tel = Path(td)
            (tel / f"{sid}.json").write_text(json.dumps(record),
                                             encoding="utf-8")
            result = stats.compute_stats(tel)
        self.assertEqual(result["corpus"]["in_flight_sessions"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
