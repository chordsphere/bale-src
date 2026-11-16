#!/usr/bin/env python3
"""What `bale stats` reads back, said more (v0.4.62, session dossier-says-more).

Pins the release's six outcomes, unit-first over synthetic corpora (the
``test_stats_drilldown.py`` pattern) with two E2E cases driving the real
wiring:

1. **Read-only while open** — ``is_read_only`` reads an ``opened``
   attempt's empty write forecast (``scope_kind`` "write-forecast",
   ``scope`` ``[]``) as well as the ``closed-read-only`` closure; an open
   read-only session is named in ``members.read_only``, stays in
   ``members.in_flight`` and the in-flight count, and leaves the rates.
   A ``[]`` scope without the forecast epoch key stays not-read-only.
2. **bale's version per attempt** — ``build_telemetry_attempt`` stamps
   the install's bin/VERSION as ``bale_version``; the dossier shows it
   per attempt and on ``record`` (the first stamped attempt); a record
   written before the stamp reads null even when the worker's
   provenance echo carries a version.
3. **Every session listed** — ``members.sessions``: every loaded sid,
   sorted, read-only and crash-debris included, outside both filters.
4. **Self-reported counts** — dossier ``record.self_reported``, latest
   carrier, null (never 0) when unreported.
5. **A HOLD class per held attempt** — the six exit-code shapes the
   brief's rehearsal lists, null on non-held attempts and on the
   unreachable shapes, and ``corpus.hold_classes`` / ``held_attempts``.
6. **Claimed-checks counts** — written into the attempt's validation at
   apply, projected on the dossier's validation view; the brief's
   four-claim example reads ``{"claimed": 4, "ran": 1, "disagreements":
   [the skipped one, the unrecorded one]}``.

Oracle doctrine per ADR-0002 (hand-derived expectations, never golden
bytes); sandbox doctrine per ADR-0005 via tests/harness.py.

Run directly::

    python3 tests/test_dossier_says_more.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from harness import (
    REPO_ROOT,
    bale_env,
    build_response_dir,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    tar_response_dir,
)

sys.path.insert(0, str(REPO_ROOT / "bin"))
import bale_report  # noqa: E402
import bale_stats  # noqa: E402

INSTALL_VERSION = (REPO_ROOT / "bin" / "VERSION").read_text(
    encoding="utf-8").strip()


# ---------------------------------------------------------------------------
# Synthetic-record builders
# ---------------------------------------------------------------------------

def _record(sid: str, created: str, outcome: str, attempts: list) -> dict:
    return {"record_version": 1, "session_id": sid, "created_at": created,
            "updated_at": created, "outcome": outcome, "attempts": attempts}


def _attempt(*, at: str, outcome: str = "applied", command: str = "apply",
             scope: list = None, scope_kind: object = "write-forecast",
             validation: object = None, checkpoint: object = None,
             closure_reason: object = None, feedback: object = None,
             provenance: object = None, extra: dict = None) -> dict:
    attempt = {"at": at, "outcome": outcome, "command": command,
               "closure_reason": closure_reason, "tarball": None,
               "validation": validation,
               "scope": scope if scope is not None else ["src"],
               "overridden_paths": [], "required_check_overrides": [],
               "change_paths": [], "feedback": feedback, "log": None}
    if scope_kind is not None:
        attempt["scope_kind"] = scope_kind
    if checkpoint is not None:
        attempt["checkpoint"] = checkpoint
    if provenance is not None:
        attempt["provenance"] = provenance
    if extra:
        attempt.update(extra)
    return attempt


def _opened(at: str, *, scope: list, work_class: str = "code",
            scope_kind: object = "write-forecast", extra: dict = None):
    return _attempt(at=at, outcome="opened", command="pack", scope=scope,
                    scope_kind=scope_kind,
                    provenance={"work_class": work_class, "packer": "fx"},
                    extra=extra)


def _validation(exit_code: int, state: str = None) -> dict:
    return {"state": state or ("PASS" if exit_code == 0 else "HOLD"),
            "exit_code": exit_code, "claims": {}, "claim_verdict": {},
            "reconciliation_parsed": False}


def _checkpoint(exit_code: int) -> dict:
    return {"configured": True, "state": "PASS" if exit_code == 0
            else "HOLD", "exit_code": exit_code,
            "script": {"path": "check.sh", "sha256": "0" * 64},
            "stamp_matched": True}


def _held(at: str, *, val_exit: int, ck_exit: object = None) -> dict:
    """A held apply attempt as apply writes it: validation.state is the
    combined verdict (HOLD) whatever validation.sh exited."""
    checkpoint = ({"configured": False} if ck_exit is None
                  else _checkpoint(ck_exit))
    return _attempt(at=at, outcome="held",
                    validation=_validation(val_exit, state="HOLD"),
                    checkpoint=checkpoint)


def _self_reported_feedback(**counts) -> dict:
    return {"mechanical": {"provenance": {"bale_version": "0.4.50",
                                          "work_class": "code",
                                          "packer": "fx"}},
            "self_reported": dict(counts)}


class _CorpusCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-says-more-")
        self.telemetry = Path(self._tmpdir.name) / "telemetry"
        self.telemetry.mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def seed(self, records: list) -> None:
        for record in records:
            (self.telemetry / f"{record['session_id']}.json").write_text(
                json.dumps(record, indent=2) + "\n", encoding="utf-8")

    def dossier(self, sid: str) -> dict:
        return bale_stats.compute_session_dossier(self.telemetry, sid)


T0 = "2026-11-14T10:00:00+00:00"
T1 = "2026-11-14T11:00:00+00:00"
T2 = "2026-11-14T12:00:00+00:00"


# ---------------------------------------------------------------------------
# 1. Read-only while open
# ---------------------------------------------------------------------------

class ReadOnlyWhileOpenTest(_CorpusCase):

    OPEN_RO = "2026-11-14-open-ro-001"
    OPEN_RW = "2026-11-14-open-rw-001"
    CLOSED_RO = "2026-11-14-closed-ro-001"
    PRE_EPOCH = "2026-11-14-pre-epoch-001"

    def seed_four(self) -> None:
        self.seed([
            _record(self.OPEN_RO, T0, "opened", [_opened(T0, scope=[])]),
            _record(self.OPEN_RW, T0, "opened",
                    [_opened(T0, scope=["bin"])]),
            _record(self.CLOSED_RO, T0, "unlocked", [
                _opened(T0, scope=[]),
                _attempt(at=T1, outcome="unlocked", command="unlock",
                         scope=[], closure_reason="closed-read-only")]),
            # An empty scope with no forecast epoch key: the pre-ADR
            # overload. Never read-only on scope alone.
            _record(self.PRE_EPOCH, T0, "opened",
                    [_opened(T0, scope=[], scope_kind=None)]),
        ])

    def test_is_read_only_reads_the_empty_forecast(self) -> None:
        self.seed_four()
        records, _, _ = bale_stats.load_corpus(self.telemetry)
        by_sid = {r["session_id"]: r for r in records}
        self.assertTrue(bale_stats.is_read_only(by_sid[self.OPEN_RO]))
        self.assertFalse(bale_stats.is_read_only(by_sid[self.OPEN_RW]))
        self.assertTrue(bale_stats.is_read_only(by_sid[self.CLOSED_RO]))
        self.assertFalse(bale_stats.is_read_only(by_sid[self.PRE_EPOCH]),
                         msg="a bare [] scope is not a read-only stamp")

    def test_dossier_read_only_in_flight_and_closed(self) -> None:
        self.seed_four()
        open_ro = self.dossier(self.OPEN_RO)["record"]
        self.assertTrue(open_ro["read_only"])
        self.assertTrue(open_ro["in_flight"])
        self.assertFalse(self.dossier(self.OPEN_RW)["record"]["read_only"])
        self.assertTrue(self.dossier(self.CLOSED_RO)["record"]["read_only"])

    def test_aggregate_members_and_in_flight(self) -> None:
        self.seed_four()
        stats = bale_stats.compute_stats(self.telemetry)
        members = stats["members"]
        self.assertEqual(members["read_only"],
                         sorted([self.OPEN_RO, self.CLOSED_RO]))
        self.assertNotIn(self.OPEN_RW, members["read_only"])
        # in_flight unchanged: the open read-only session is still in it.
        self.assertEqual(members["in_flight"],
                         sorted([self.OPEN_RO, self.OPEN_RW,
                                 self.PRE_EPOCH]))
        self.assertEqual(stats["corpus"]["in_flight_sessions"], 3)
        self.assertEqual(stats["corpus"]["read_only_sessions"], 2)
        # Rates exclude the open read-only session (the session's call):
        # it is out of the classed membership.
        self.assertEqual(stats["corpus"]["sessions"], 2)
        self.assertEqual(stats["classes"]["code"]["sessions"], 2)

    def test_work_class_filter_reaches_open_read_only_in_flight(self):
        self.seed([
            _record(self.OPEN_RO, T0, "opened",
                    [_opened(T0, scope=[], work_class="meta")]),
            _record(self.OPEN_RW, T0, "opened",
                    [_opened(T0, scope=["bin"], work_class="code")]),
        ])
        code = bale_stats.compute_stats(self.telemetry, work_class="code")
        self.assertEqual(code["members"]["in_flight"], [self.OPEN_RW])
        meta = bale_stats.compute_stats(self.telemetry, work_class="meta")
        self.assertEqual(meta["members"]["in_flight"], [self.OPEN_RO])
        self.assertEqual(meta["corpus"]["in_flight_sessions"], 1)
        # The read-only context count stays class-independent.
        self.assertEqual(code["corpus"]["read_only_sessions"], 1)


# ---------------------------------------------------------------------------
# 2. bale's version, per attempt and per session
# ---------------------------------------------------------------------------

class BaleVersionTest(_CorpusCase):

    def test_builder_stamps_the_install_version_on_every_attempt(self):
        self.assertEqual(bale_report.install_bale_version(), INSTALL_VERSION)
        for outcome, command in (("opened", "pack"), ("applied", "apply"),
                                 ("unlocked", "unlock"),
                                 ("rolled-back", "rollback")):
            attempt = bale_report.build_telemetry_attempt(
                outcome=outcome, command=command)
            self.assertEqual(attempt["bale_version"], INSTALL_VERSION,
                             msg=f"{outcome}/{command}")

    def test_dossier_reads_bale_stamp_and_never_the_worker_echo(self):
        old = "2026-11-14-old-001"
        new = "2026-11-14-new-001"
        self.seed([
            # Written before the stamp: the worker's echo carries a
            # version, which is not bale's stamp.
            _record(old, T0, "applied", [
                _attempt(at=T0, validation=_validation(0),
                         feedback=_self_reported_feedback())]),
            _record(new, T0, "applied", [
                _opened(T0, scope=["bin"],
                        extra={"bale_version": "0.4.62"}),
                _attempt(at=T1, validation=_validation(0),
                         extra={"bale_version": "0.4.63"})]),
        ])
        old_d = self.dossier(old)
        self.assertIn("bale_version", old_d["record"])
        self.assertIsNone(old_d["record"]["bale_version"])
        self.assertIsNone(old_d["attempts"][0]["bale_version"])
        new_d = self.dossier(new)
        self.assertEqual(new_d["record"]["bale_version"], "0.4.62",
                         msg="the first attempt carrying a stamp")
        self.assertEqual([a["bale_version"] for a in new_d["attempts"]],
                         ["0.4.62", "0.4.63"])


# ---------------------------------------------------------------------------
# 3. Every session, listed
# ---------------------------------------------------------------------------

class MembersSessionsTest(_CorpusCase):

    def test_every_sid_sorted_including_excluded_sessions(self) -> None:
        sids = ["2026-11-14-c-001", "2026-11-14-a-001", "2026-10-01-ro-001",
                "2026-11-14-debris-001"]
        self.seed([
            _record(sids[0], T0, "applied",
                    [_attempt(at=T0, validation=_validation(0))]),
            _record(sids[1], T0, "opened", [_opened(T0, scope=["x"])]),
            _record(sids[2], "2026-10-01T10:00:00+00:00", "unlocked", [
                _attempt(at=T0, outcome="unlocked", command="unlock",
                         scope=[], closure_reason="closed-read-only")]),
            _record(sids[3], T0, "unlocked", [
                _attempt(at=T0, outcome="unlocked", command="unlock",
                         scope=[], closure_reason="crash-debris")]),
        ])
        (self.telemetry / "broken.json").write_text("{nope",
                                                    encoding="utf-8")
        stats = bale_stats.compute_stats(self.telemetry)
        self.assertEqual(stats["members"]["sessions"], sorted(sids))
        # A whole-corpus fact: outside both filters.
        since = bale_stats.compute_stats(self.telemetry, since="2026-11-01",
                                         work_class="doc")
        self.assertEqual(since["members"]["sessions"], sorted(sids))


# ---------------------------------------------------------------------------
# 4. The self-reported counts, per session
# ---------------------------------------------------------------------------

class SelfReportedCountsTest(_CorpusCase):

    def test_latest_carrier_and_null_when_unreported(self) -> None:
        sid = "2026-11-14-selfrep-001"
        none_sid = "2026-11-14-silent-001"
        self.seed([
            _record(sid, T0, "applied", [
                _held(T0, val_exit=1) | {"feedback":
                    _self_reported_feedback(light_blocks=3,
                                            paste_carried_rounds=1)},
                # The retry restates light_blocks and omits the other:
                # each count reads its own latest carrier.
                _attempt(at=T1, command="retry", validation=_validation(0),
                         feedback=_self_reported_feedback(light_blocks=0)),
            ]),
            _record(none_sid, T0, "applied", [
                _attempt(at=T0, validation=_validation(0),
                         feedback=_self_reported_feedback(
                             light_blocks="two"))]),
        ])
        self.assertEqual(self.dossier(sid)["record"]["self_reported"],
                         {"light_blocks": 0, "paste_carried_rounds": 1})
        self.assertEqual(self.dossier(none_sid)["record"]["self_reported"],
                         {"light_blocks": None,
                          "paste_carried_rounds": None})
        # The aggregate sums the same figures, absence as 0.
        corpus = bale_stats.compute_stats(self.telemetry)["corpus"]
        self.assertEqual(corpus["light_blocks_total"], 0)
        self.assertEqual(corpus["paste_carried_rounds_total"], 1)


# ---------------------------------------------------------------------------
# 5. A HOLD class on every held attempt
# ---------------------------------------------------------------------------

class HoldClassTest(_CorpusCase):

    def test_the_rehearsal_shapes(self) -> None:
        # The brief's six applies (REH), validation.state HOLD on every
        # held one, read by exit code.
        cases = [
            (_attempt(at=T0, validation=_validation(0),
                      checkpoint={"configured": False}), None),
            (_held(T0, val_exit=1), "validation"),
            (_held(T0, val_exit=0, ck_exit=1), "checkpoint"),
            (_held(T0, val_exit=1, ck_exit=1), "both"),
            (_held(T0, val_exit=0, ck_exit=2), "checkpoint-defect"),
            (_held(T0, val_exit=1, ck_exit=2), "checkpoint-defect"),
            # validation non-zero, checkpoint ran and passed.
            (_held(T0, val_exit=1, ck_exit=0), "validation"),
            # validation.sh's own error exit is a non-zero exit too.
            (_held(T0, val_exit=2), "validation"),
        ]
        for attempt, expected in cases:
            self.assertEqual(bale_stats.attempt_hold_class(attempt),
                             expected, msg=json.dumps(attempt))

    def test_unreachable_shapes_read_null(self) -> None:
        no_validation = _attempt(at=T0, outcome="held")
        both_zero = _held(T0, val_exit=0, ck_exit=0)
        exit_less = _held(T0, val_exit=1)
        exit_less["checkpoint"] = {"configured": True, "state": "HOLD"}
        pre_epoch = _attempt(at=T0, outcome="held",
                             validation=_validation(1, "HOLD"))
        for attempt in (no_validation, both_zero, exit_less):
            self.assertIsNone(bale_stats.attempt_hold_class(attempt),
                              msg=json.dumps(attempt))
        # A held attempt from before the checkpoint stamp still classes.
        self.assertEqual(bale_stats.attempt_hold_class(pre_epoch),
                         "validation")
        # Not held: null, whatever its codes say.
        self.assertIsNone(bale_stats.attempt_hold_class(
            _attempt(at=T0, outcome="applied", validation=_validation(1))))

    def test_dossier_and_aggregate(self) -> None:
        sid = "2026-11-14-holds-001"
        self.seed([_record(sid, T0, "held", [
            _opened(T0, scope=["bin"]),
            _held(T1, val_exit=0, ck_exit=1),
            _held(T2, val_exit=1, ck_exit=2),
            _held(T2, val_exit=0, ck_exit=0),
        ])])
        dossier = self.dossier(sid)
        self.assertEqual([a["hold_class"] for a in dossier["attempts"]],
                         [None, "checkpoint", "checkpoint-defect", None])
        corpus = bale_stats.compute_stats(self.telemetry)["corpus"]
        self.assertEqual(corpus["held_attempts"], 3)
        self.assertEqual(corpus["hold_classes"],
                         {"checkpoint-defect": 1, "both": 0,
                          "checkpoint": 1, "validation": 0})
        # The human renderings say it beside the outcome and in the
        # summary.
        human = bale_report.format_session_dossier_report(dossier)
        self.assertIn("held (apply) at " + T1 + "; hold class checkpoint",
                      human)
        report = bale_report.format_stats_report(
            bale_stats.compute_stats(self.telemetry))
        self.assertIn("3 attempts (checkpoint-defect 1, checkpoint 1, "
                      "no class 1)", report)

    def test_cause_keeps_its_meaning(self) -> None:
        sid = "2026-11-14-cause-001"
        self.seed([_record(sid, T0, "rejected", [
            _attempt(at=T0, outcome="rejected",
                     extra={"cause": "manifest sha256 mismatch"})])])
        attempt = self.dossier(sid)["attempts"][0]
        self.assertEqual(attempt["cause"], "manifest sha256 mismatch")
        self.assertIsNone(attempt["hold_class"])


# ---------------------------------------------------------------------------
# 6. The derived claimed-checks counts
# ---------------------------------------------------------------------------

FOUR_CLAIMS = {
    "unit tests": "pass",
    "lint": "pass",
    "typecheck": "pass",
    "browser smoke": "untested",
}

# One passed, one skipped, one never recorded (no row), one claimed
# untested — the brief's example.
FOUR_CLAIMS_OUTPUT = (
    "[PASS] unit tests\n"
    "[SKIP] lint: ruff not found\n"
    "claims vs verdict:\n"
    "  unit tests: claim=pass verdict=pass [agree]\n"
    "  lint: claim=pass verdict=skip [DISAGREE]\n"
    "  browser smoke: claim=untested verdict=skip [n/a]\n"
)


class ClaimedChecksTest(_CorpusCase):

    def test_builder_records_the_brief_example(self) -> None:
        attempt = bale_report.build_telemetry_attempt(
            outcome="applied", command="apply",
            manifest={"claims": FOUR_CLAIMS, "changes": []},
            validation_state="PASS", validation_exit_code=0,
            validation_output=FOUR_CLAIMS_OUTPUT)
        self.assertEqual(attempt["validation"]["claimed_checks"],
                         {"claimed": 4, "ran": 1,
                          "disagreements": ["lint", "typecheck"]})
        # claim_verdict keeps the printed tags, unchanged.
        self.assertEqual(
            attempt["validation"]["claim_verdict"]["lint"]["agreement"],
            "disagree")
        self.assertNotIn("typecheck",
                         attempt["validation"]["claim_verdict"])

    def test_builder_no_claims_block_and_no_validation(self) -> None:
        unknown = bale_report.build_telemetry_attempt(
            outcome="applied", command="apply",
            manifest={"claims": FOUR_CLAIMS, "changes": []},
            validation_state="PASS", validation_exit_code=0,
            validation_output="[PASS] unit tests\n")
        self.assertEqual(unknown["validation"]["claimed_checks"],
                         {"claimed": 4, "ran": None, "disagreements": []})
        none_claimed = bale_report.build_telemetry_attempt(
            outcome="applied", command="apply",
            manifest={"changes": []}, validation_state="PASS",
            validation_exit_code=0, validation_output="")
        self.assertEqual(none_claimed["validation"]["claimed_checks"],
                         {"claimed": 0, "ran": 0, "disagreements": []})
        rejected = bale_report.build_telemetry_attempt(
            outcome="rejected", command="apply")
        self.assertIsNone(rejected["validation"])

    def test_dossier_view(self) -> None:
        sid = "2026-11-14-claims-001"
        written = bale_report.build_telemetry_attempt(
            outcome="applied", command="apply",
            manifest={"claims": FOUR_CLAIMS, "changes": []},
            validation_state="PASS", validation_exit_code=0,
            validation_output=FOUR_CLAIMS_OUTPUT)
        self.seed([_record(sid, T0, "applied", [
            _attempt(at=T0, outcome="rejected"),
            _attempt(at=T1, validation=_validation(0)),  # pre-release
            written,
        ])])
        attempts = self.dossier(sid)["attempts"]
        self.assertIsNone(attempts[0]["validation"])
        self.assertIn("claimed_checks", attempts[1]["validation"])
        self.assertIsNone(attempts[1]["validation"]["claimed_checks"])
        self.assertEqual(attempts[2]["validation"]["claimed_checks"],
                         {"claimed": 4, "ran": 1,
                          "disagreements": ["lint", "typecheck"]})
        human = bale_report.format_session_dossier_report(
            self.dossier(sid))
        self.assertIn("claimed checks: 1 of 4 ran; disagree: lint, "
                      "typecheck", human)


# ---------------------------------------------------------------------------
# The JSON lines carry the keys; the pinned keys stay
# ---------------------------------------------------------------------------

class JsonLinesTest(_CorpusCase):

    def test_new_keys_ride_both_lines(self) -> None:
        sid = "2026-11-14-line-001"
        self.seed([_record(sid, T0, "held",
                           [_opened(T0, scope=[]),
                            _held(T1, val_exit=1)])])
        line = json.loads(bale_report.format_session_dossier_json(
            self.dossier(sid)))
        self.assertEqual(list(line), ["outcome", "session_id", "found",
                                      "record", "attempts", "lineage"])
        for key in ("bale_version", "self_reported", "read_only"):
            self.assertIn(key, line["record"])
        for key in ("hold_class", "bale_version", "cause"):
            self.assertIn(key, line["attempts"][1])
        self.assertIn("claimed_checks", line["attempts"][1]["validation"])
        agg = json.loads(bale_report.format_stats_json(
            bale_stats.compute_stats(self.telemetry)))
        self.assertEqual(agg["members"]["sessions"], [sid])
        self.assertIn("hold_classes", agg["corpus"])
        self.assertIn("in_flight", agg["members"])


# ---------------------------------------------------------------------------
# E2E: the real wiring
# ---------------------------------------------------------------------------

class DossierSaysMoreE2ETest(unittest.TestCase):

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-says-e2e-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def bale(self, *args: str):
        result = run_bale(self.install, list(args), cwd=self.repo,
                          env=self.env)
        self.assertEqual(result.returncode, 0,
                         msg=f"bale {' '.join(args)}\nstdout:\n"
                             f"{result.stdout}\nstderr:\n{result.stderr}")
        return result

    def json_line(self, *args: str) -> dict:
        return json.loads(self.bale(*args).stdout.strip().splitlines()[-1])

    def pack(self, slug: str, *extra: str) -> str:
        return self.json_line("pack", f"{slug} goal", "--slug", slug,
                              "--include", "hello.txt", "--no-readme",
                              "--json", *extra)["sid"]

    def test_read_only_pack_reads_read_only_while_open(self) -> None:
        sid = self.pack("ro-open", "--read-only")
        dossier = self.json_line("stats", "--sid", sid, "--json")
        self.assertTrue(dossier["record"]["read_only"])
        self.assertTrue(dossier["record"]["in_flight"])
        self.assertEqual(dossier["record"]["bale_version"], INSTALL_VERSION)
        self.assertEqual(dossier["attempts"][0]["bale_version"],
                         INSTALL_VERSION)
        agg = self.json_line("stats", "--json")
        self.assertEqual(agg["members"]["read_only"], [sid])
        self.assertEqual(agg["members"]["in_flight"], [sid])
        self.assertEqual(agg["members"]["sessions"], [sid])

    def test_apply_records_claimed_checks_and_version(self) -> None:
        sid = self.pack("claims-e2e")
        validation_sh = (
            "#!/usr/bin/env bash\n"
            "echo '[PASS] unit tests'\n"
            "echo '[SKIP] lint: ruff not found'\n"
            "echo 'claims vs verdict:'\n"
            "echo '  unit tests: claim=pass verdict=pass [agree]'\n"
            "echo '  lint: claim=pass verdict=skip [DISAGREE]'\n"
            "echo '  browser smoke: claim=untested verdict=skip [n/a]'\n"
            "exit 0\n")
        rdir = build_response_dir(
            self.tmp / "resp", sid,
            summary="claimed-checks fixture: rewrite hello.txt",
            entries=[{"path": "hello.txt", "action": "modified",
                      "reason": "the fixture's change",
                      "data": b"hello, said more\n"}],
            validation_sh=validation_sh,
            validation_will_run=list(FOUR_CLAIMS),
            claims=dict(FOUR_CLAIMS))
        self.bale("apply", str(tar_response_dir(rdir)))
        dossier = self.json_line("stats", "--sid", sid, "--json")
        self.assertFalse(dossier["record"]["read_only"])
        applied = dossier["attempts"][-1]
        self.assertEqual(applied["outcome"], "applied")
        self.assertIsNone(applied["hold_class"])
        self.assertEqual(applied["bale_version"], INSTALL_VERSION)
        self.assertEqual(applied["validation"]["claimed_checks"],
                         {"claimed": 4, "ran": 1,
                          "disagreements": ["lint", "typecheck"]})


# ---------------------------------------------------------------------------
# 7. The release
# ---------------------------------------------------------------------------

class ReleaseTest(unittest.TestCase):

    def test_version_and_changelog_record(self) -> None:
        # The release's own record stays; bin/VERSION moved on at 0.4.63
        # (tests/test_status_says_more.py pins the current release), so
        # the pin is that the install is at or past this one.
        self.assertGreaterEqual(
            tuple(int(n) for n in INSTALL_VERSION.split(".")), (0, 4, 62))
        record = json.loads(
            (REPO_ROOT / "claude" / "changelog" / "0.4.62.json").read_text(
                encoding="utf-8"))
        self.assertEqual(record["version"], "0.4.62")
        self.assertEqual(record["session_id"],
                         "2026-11-14-dossier-says-more-002")


if __name__ == "__main__":
    unittest.main()
