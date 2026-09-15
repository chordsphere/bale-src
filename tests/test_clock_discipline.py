#!/usr/bin/env python3
"""Hermetic E2E for the one-clock rule (board 94, 0.4.30; TARBALL.md
section 1).

Bale ran three clocks and named none: session ids were minted by
``date.today()`` (the packing machine's local date), every ISO
timestamp by ``datetime.now(timezone.utc)``, and the worker's chat
showed the operator's wall clock. Since 0.4.30 the mint clock is UTC,
the request manifest stamps ``provenance.packed_at`` from the same
instant the sid was allocated from, and the emitted opener names it
(``tests/test_pack_opener.py`` pins the opener half).

Pinned behaviors:

- **UTC mint, not local.** Two packs under wall clocks 26 hours apart
  (``TZ=Etc/GMT-14`` is UTC+14, ``TZ=Etc/GMT+12`` is UTC-12) mint the
  same sid date. Under a local-date mint those two zones never agree
  on the calendar day, so the pin is deterministic at any time of day
  — no midnight-window flake in either direction.
- **The stamp.** ``provenance.packed_at`` is present on every
  bale-built request, ISO 8601 with a zero UTC offset at seconds
  precision (the ``created_at`` shape ``bin/bale_validate.py``
  accepts), and its date equals the sid's date — pack and handoff
  alike, since both paths read one instant.
- **The counter follows the mint.** The per-day counter file is keyed
  by the sid's (UTC) date, not the local date.
- **Additive schema.** ``packed_at`` is admitted and never required on
  the request schema, admitted on the response echo, and a pre-stamp
  provenance block still validates — the lint's embedded echo schema
  is JSON-equal to the source (``tests/test_schema_embeds.py`` pins
  that pair); here the request side is pinned against the file.

Sandbox doctrine per ADR-0005 (fully hermetic) — ``tests/harness.py``
carries it. The handoff leg reuses ``tests/test_handoff_fixture.py``.

Run directly::

    python3 tests/test_clock_discipline.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import re
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from harness import (
    bale_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
)
from test_handoff_fixture import HandoffFixture

REPO = Path(__file__).resolve().parent.parent
REQUEST_SCHEMA = REPO / "schemas" / "request-manifest.schema.json"
RESPONSE_SCHEMA = REPO / "schemas" / "response-manifest.schema.json"

# ISO 8601, seconds precision, explicit zero offset — the created_at
# shape (bin/bale_validate.py's _created_at_problem accepts +00:00).
PACKED_AT_SHAPE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+00:00$")

GOAL = "clock discipline fixture goal"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class PackClockTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-clock-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def pack(self, slug: str, *, tz: str | None = None,
             read_only: bool = False) -> tuple[dict, str]:
        """A --json pack under wall clock `tz`; returns (report, stderr).
        The opener rides stderr under --json (board 52). `read_only`
        packs forecast nothing, so several can be open at once (the
        two-zone test packs twice into one repo)."""
        env = dict(self.env)
        if tz is not None:
            env["TZ"] = tz
        shape = ["--read-only"] if read_only else ["--include", "hello.txt"]
        result = run_bale(
            self.install,
            ["pack", GOAL, "--slug", slug, *shape, "--no-readme", "--json"],
            cwd=self.repo, env=env)
        self.assertEqual(result.returncode, 0,
                         msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        return json.loads(result.stdout.strip().splitlines()[0]), result.stderr

    def request_manifest(self, sid: str) -> dict:
        p = self.repo / ".bale" / "sessions" / sid / "manifest.json"
        self.assertTrue(p.is_file(), msg=f"no request manifest at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    # -- pinned behavior 1: UTC mint, not local ---------------------------

    def test_sid_date_is_the_utc_date_under_any_wall_clock(self) -> None:
        """Two packs 26 wall-clock hours apart mint the same date, and
        it is the UTC date bracketing the run."""
        before = utc_now().date()
        east, _ = self.pack("clock-east", tz="Etc/GMT-14",
                            read_only=True)   # UTC+14
        west, _ = self.pack("clock-west", tz="Etc/GMT+12",
                            read_only=True)   # UTC-12
        after = utc_now().date()
        east_day, west_day = east["sid"][:10], west["sid"][:10]
        self.assertEqual(
            east_day, west_day,
            msg="a local-date mint would put these two zones on "
                "different calendar days at every moment of the day")
        self.assertIn(east_day, {before.isoformat(), after.isoformat()},
                      msg="the minted date is the UTC date")

    # -- pinned behavior 2 + 3: the stamp and the counter -----------------

    def test_packed_at_stamped_utc_and_agrees_with_the_sid(self) -> None:
        before = utc_now()
        payload, stderr = self.pack("clock-stamp", tz="Etc/GMT-14")
        after = utc_now()
        sid = payload["sid"]
        prov = self.request_manifest(sid)["provenance"]
        self.assertIn("packed_at", prov,
                      msg="every bale-built provenance block stamps packed_at")
        packed_at = prov["packed_at"]
        self.assertRegex(packed_at, PACKED_AT_SHAPE)
        stamped = datetime.fromisoformat(packed_at)
        self.assertEqual(stamped.utcoffset().total_seconds(), 0)
        # Bracketed by the run (seconds precision truncates, so the
        # lower bound is the floor of `before`).
        self.assertLessEqual(before.replace(microsecond=0), stamped)
        self.assertLessEqual(stamped, after)
        # The one-instant rule: sid date == stamp date, by construction.
        self.assertEqual(sid[:10], packed_at[:10],
                         msg="the sid's date and packed_at come from one "
                             "UTC instant")
        counter = self.repo / ".bale" / f"counter-{sid[:10]}"
        self.assertTrue(counter.is_file(),
                        msg="the per-day counter is keyed by the sid's "
                            "UTC date")
        # The opener names the same string (the opener suite pins
        # placement; here only identity with the stamp).
        self.assertIn(f"Packed at {packed_at} (UTC).", stderr)

    # -- pinned behavior 4: additive schema ------------------------------

    def test_request_schema_admits_and_never_requires_packed_at(self) -> None:
        schema = json.loads(REQUEST_SCHEMA.read_text(encoding="utf-8"))
        prov = schema["properties"]["provenance"]
        self.assertIn("packed_at", prov["properties"])
        self.assertNotIn("packed_at", prov["required"])
        self.assertFalse(prov.get("additionalProperties", True),
                         msg="the block is closed, which is why the key "
                             "must be admitted explicitly")
        self.assertEqual(prov["properties"]["packed_at"]["type"], "string")
        # A pre-stamp block (the four required keys only) still validates
        # against the closed shape — additive means no retroactive edit.
        pre_stamp = {"bale_version": "0.4.29", "contract_docs": {
            "CLAUDE.md": "a", "TARBALL.md": "b", "DOCS.md": "c",
            "CODE.md": "d"}, "packer": "x", "work_class": "code"}
        missing = [k for k in prov["required"] if k not in pre_stamp]
        self.assertEqual(missing, [])
        self.assertTrue(set(pre_stamp) <= set(prov["properties"]))

    def test_response_echo_admits_packed_at(self) -> None:
        schema = json.loads(RESPONSE_SCHEMA.read_text(encoding="utf-8"))
        echo = (schema["properties"]["feedback"]["properties"]["mechanical"]
                ["properties"]["provenance"])
        self.assertIn("packed_at", echo["properties"])
        self.assertNotIn("packed_at", echo["required"])
        self.assertFalse(echo.get("additionalProperties", True))


class HandoffClockTest(HandoffFixture):
    """The second request-building path stamps and mints the same way."""

    def test_handoff_re_mint_is_utc_and_stamped(self) -> None:
        bailed_sid, tarball = self.packed_and_bailed(
            reading_plan_paths=["hello.txt"], slug="clock-parent")
        env = dict(self.env)
        env["TZ"] = "Etc/GMT-14"  # UTC+14: a local mint would run a day ahead
        before = utc_now()
        result = run_bale(self.install, ["handoff", str(tarball)],
                          cwd=self.repo, env=env)
        after = utc_now()
        self.assert_ok(result, "handoff")
        new_sid = self.sole_new_open_sid(bailed_sid)
        self.assertIn(new_sid[:10],
                      {before.date().isoformat(), after.date().isoformat()},
                      msg="the re-mint is on the UTC clock, not TZ's")
        prov = self.request_manifest(new_sid)["provenance"]
        self.assertIn("packed_at", prov)
        self.assertRegex(prov["packed_at"], PACKED_AT_SHAPE)
        self.assertEqual(new_sid[:10], prov["packed_at"][:10],
                         msg="handoff reads one instant for the sid and "
                             "the stamp, exactly as pack does")


if __name__ == "__main__":
    unittest.main()
