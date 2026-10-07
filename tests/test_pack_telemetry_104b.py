#!/usr/bin/env python3
"""Hermetic E2E + unit pins for board 104b's pack-side telemetry riders
(v0.4.40).

Pins, as this suite asserts them:

1. **The --json `sweep` ledger.** Pack's one JSON line always carries
   `sweep`, a list: [] when the pack closed nothing; otherwise one
   entry per bookkeeping write onto another session's record, in event
   order, each `{sid, event, status, detail, sha, files}`. A
   supersession parent appears twice (`superseded-by-split`, then
   `superseded_by`); each read-only-swept sid twice
   (`closed-read-only`, then `swept_by`). With `[apply] sweep` off the
   entries stay, their four sweep keys null / [].
2. **`swept_by`.** After a sweeping read-only pack, each swept
   session's closed-read-only attempt names the sweeping pack's sid;
   with the auto-sweep on the rewrite is committed as its own
   `[bale sweep <swept>] swept_by <pack>` event and no tracked file is
   left modified (board 107's lesson, applied to the read-only sweep).
   Several swept sessions each get the stamp.
3. **`packed_at` at open.** The `opened` attempt's provenance block
   carries the request manifest's `provenance.packed_at` verbatim, on
   the read-only (master) shape too, and the record validates against
   the schema; the registry-side provenance.json stays the pair.
4. **Pure renderers.** format_pack_sweep_entry / format_pack_json /
   format_include_group_json shapes, and stamp_swept_by's loud,
   non-fatal failure.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_pack_telemetry_104b.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import subprocess
import tempfile
import unittest
from pathlib import Path

from harness import (
    _load_module,
    bale_env,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_bale_pty,
    run_checked,
)

SWEEP_SUBJECT_PREFIX = "[bale sweep "
SWEEP_KEYS = ["sid", "event", "status", "detail", "sha", "files"]


def json_line(output: str) -> dict:
    """The pack report's JSON line out of combined (pty) output."""
    for raw in output.splitlines():
        line = raw.strip().strip("\r")
        if line.startswith('{"outcome"'):
            return json.loads(line)
    raise AssertionError(f"no JSON report line in output:\n{output}")


class _PackSandbox(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-104b-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def args(self, slug: str, *extra: str) -> list:
        return ["pack", f"board 104b fixture goal for {slug}",
                "--slug", slug, "--include", "hello.txt", "--no-readme",
                *extra]

    def pack(self, slug: str, *extra: str):
        return run_bale(self.install, self.args(slug, *extra),
                        cwd=self.repo, env=self.env)

    def pack_pty(self, slug: str, *extra: str, answers: str):
        return run_bale_pty(self.install, self.args(slug, *extra),
                            cwd=self.repo, env=self.env, answers=answers)

    def assert_ok(self, result) -> None:
        self.assertEqual(result.returncode, 0,
                         msg=f"stdout:\n{result.stdout}\n"
                             f"stderr:\n{result.stderr}")

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        entries = [d for d in root.iterdir() if (d / "open").is_file()]
        entries.sort(key=lambda d: (d.stat().st_mtime, d.name))
        return [d.name for d in entries]

    def packed_sid(self, result) -> str:
        self.assert_ok(result)
        return self.open_sids()[-1]

    def record(self, sid: str) -> dict:
        p = self.repo / "claude" / "telemetry" / f"{sid}.json"
        self.assertTrue(p.is_file(), msg=f"expected a record at {p}")
        return json.loads(p.read_text(encoding="utf-8"))

    def configure(self, *, sweep: "bool | None") -> None:
        lines = [""]
        if sweep is not None:
            lines = ["[apply]", f"sweep = {'true' if sweep else 'false'}"]
        (self.repo / "bale.toml").write_text("\n".join(lines) + "\n",
                                            encoding="utf-8")
        env = git_env(self.home)
        run_checked(["git", "add", "bale.toml"], cwd=self.repo, env=env)
        run_checked(["git", "commit", "-m", "configure"], cwd=self.repo,
                    env=env)

    def git_out(self, *args: str) -> str:
        r = subprocess.run(["git", *args], cwd=self.repo,
                           env=git_env(self.home), capture_output=True,
                           text=True)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        return r.stdout

    def sweep_subjects(self) -> list:
        return [s for s in self.git_out("log", "--format=%s").splitlines()
                if s.startswith(SWEEP_SUBJECT_PREFIX)]

    def assert_tracked_tree_clean(self, *, untracked_ok: set) -> None:
        lines = [ln for ln in
                 self.git_out("status", "--porcelain", "-uall").splitlines()
                 if ln.strip()]
        self.assertEqual([ln for ln in lines if not ln.startswith("?? ")],
                         [], msg=f"tracked files left modified: {lines}")
        untracked = {ln[3:] for ln in lines if ln.startswith("?? ")}
        self.assertLessEqual(untracked, untracked_ok, msg=str(lines))


# ---------------------------------------------------------------------------
# 2. swept_by, with the auto-sweep on / off
# ---------------------------------------------------------------------------

class SweptByStampTest(_PackSandbox):

    def test_swept_by_committed_and_tree_clean(self) -> None:
        self.configure(sweep=True)
        swept = self.packed_sid(self.pack("ro-a", "--read-only"))
        code, output = self.pack_pty("ro-b", "--read-only", "--json",
                                     answers="\n")
        self.assertEqual(code, 0, msg=output)
        sweeper = self.open_sids()[-1]
        self.assertNotEqual(sweeper, swept)
        # The closure attempt names the sweeping pack, on disk and in
        # the committed record alike.
        latest = self.record(swept)["attempts"][-1]
        self.assertEqual(latest["closure_reason"], "closed-read-only")
        self.assertEqual(latest["swept_by"], sweeper)
        committed = json.loads(self.git_out(
            "show", f"HEAD:claude/telemetry/{swept}.json"))
        self.assertEqual(committed, self.record(swept),
                         msg="HEAD and the working tree must agree")
        self.assert_tracked_tree_clean(
            untracked_ok={f"claude/telemetry/{sweeper}.json"})
        self.assertEqual(self.sweep_subjects(), [
            f"[bale sweep {swept}] swept_by {sweeper}",
            f"[bale sweep {swept}] closed-read-only",
        ])
        # The --json ledger: close then stamp, both committed.
        report = json_line(output)
        self.assertEqual(report["sid"], sweeper)
        events = [(e["sid"], e["event"], e["status"])
                  for e in report["sweep"]]
        self.assertEqual(events, [(swept, "closed-read-only", "committed"),
                                  (swept, "swept_by", "committed")])
        for entry in report["sweep"]:
            self.assertEqual(list(entry), SWEEP_KEYS)
            self.assertTrue(entry["sha"])
            self.assertEqual(entry["files"],
                             [f"claude/telemetry/{swept}.json"])

    def test_several_swept_sessions_each_stamped(self) -> None:
        self.configure(sweep=True)
        first = self.packed_sid(self.pack("ro-a", "--read-only"))
        second = self.packed_sid(self.pack("ro-b", "--read-only"))
        code, output = self.pack_pty("ro-c", "--read-only", "--json",
                                     answers="\n\n")
        self.assertEqual(code, 0, msg=output)
        sweeper = self.open_sids()[-1]
        self.assertEqual(self.open_sids(), [sweeper])
        for swept in (first, second):
            self.assertEqual(self.record(swept)["attempts"][-1]["swept_by"],
                             sweeper)
        self.assert_tracked_tree_clean(
            untracked_ok={f"claude/telemetry/{sweeper}.json"})
        report = json_line(output)
        self.assertEqual(
            sorted((e["sid"], e["event"]) for e in report["sweep"]),
            sorted([(first, "closed-read-only"), (first, "swept_by"),
                    (second, "closed-read-only"), (second, "swept_by")]))
        # Closes run pre-sid, stamps post-sid: every close precedes
        # every stamp in the ledger.
        kinds = [e["event"] for e in report["sweep"]]
        self.assertEqual(kinds, ["closed-read-only", "closed-read-only",
                                 "swept_by", "swept_by"])

    def test_sweep_off_stamps_on_disk_and_nulls_entries(self) -> None:
        self.configure(sweep=False)
        swept = self.packed_sid(self.pack("ro-a", "--read-only"))
        code, output = self.pack_pty("ro-b", "--read-only", "--json",
                                     answers="\n")
        self.assertEqual(code, 0, msg=output)
        sweeper = self.open_sids()[-1]
        self.assertEqual(self.record(swept)["attempts"][-1]["swept_by"],
                         sweeper)
        self.assertEqual(self.sweep_subjects(), [])
        self.assertNotIn("[bale] sweep:", output,
                         msg="sweep off: sweep_commit prints nothing")
        report = json_line(output)
        self.assertEqual(report["sweep"], [
            {"sid": swept, "event": "closed-read-only", "status": None,
             "detail": None, "sha": None, "files": []},
            {"sid": swept, "event": "swept_by", "status": None,
             "detail": None, "sha": None, "files": []},
        ])

    def test_declined_sweep_stamps_nothing(self) -> None:
        swept = self.packed_sid(self.pack("ro-a", "--read-only"))
        code, output = self.pack_pty("ro-b", "--read-only", "--json",
                                     answers="n\n")
        self.assertEqual(code, 0, msg=output)
        self.assertEqual(json_line(output)["sweep"], [])
        for attempt in self.record(swept)["attempts"]:
            self.assertNotIn("swept_by", attempt)

    def test_stamped_record_validates(self) -> None:
        validate = _load_module("bale_validate").validate_telemetry_record
        swept = self.packed_sid(self.pack("ro-a", "--read-only"))
        code, output = self.pack_pty("ro-b", "--read-only", answers="\n")
        self.assertEqual(code, 0, msg=output)
        self.assertEqual(validate(self.record(swept)), [])


# ---------------------------------------------------------------------------
# 1. The ledger on the other pack shapes
# ---------------------------------------------------------------------------

class SweepLedgerTest(_PackSandbox):

    def test_plain_pack_reports_empty_sweep(self) -> None:
        r = self.pack("plain", "--json")
        self.assert_ok(r)
        report = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertEqual(report["sweep"], [])
        self.assertIsNone(report["include_group"])

    def test_piped_readonly_with_open_readonly_reports_empty(self) -> None:
        """Piped stdin declines the sweep without a prompt: nothing
        closed, so the ledger is []."""
        self.packed_sid(self.pack("ro-a", "--read-only"))
        r = self.pack("ro-b", "--read-only", "--json")
        self.assert_ok(r)
        self.assertEqual(json.loads(r.stdout.strip())["sweep"], [])

    def test_supersession_parent_appears_twice(self) -> None:
        self.configure(sweep=True)
        parent = self.packed_sid(self.pack("parent"))
        code, output = self.pack_pty("child", "--supersedes", parent,
                                     "--json", answers="y\n")
        self.assertEqual(code, 0, msg=output)
        child = self.open_sids()[-1]
        report = json_line(output)
        self.assertEqual(report["sid"], child)
        self.assertEqual(
            [(e["sid"], e["event"], e["status"]) for e in report["sweep"]],
            [(parent, "superseded-by-split", "committed"),
             (parent, "superseded_by", "committed")])
        # Item 3's supersession half was already met: the closure
        # carries the child as superseded_by, and no swept_by is added.
        latest = self.record(parent)["attempts"][-1]
        self.assertEqual(latest["superseded_by"], child)
        self.assertNotIn("swept_by", latest)


# ---------------------------------------------------------------------------
# 3. packed_at at open
# ---------------------------------------------------------------------------

class PackedAtOpenTest(_PackSandbox):

    def manifest(self, sid: str) -> dict:
        return json.loads((self.repo / ".bale" / "sessions" / sid /
                           "manifest.json").read_text(encoding="utf-8"))

    def test_readonly_master_record_carries_packed_at(self) -> None:
        sid = self.packed_sid(self.pack("master", "--read-only"))
        opened = self.record(sid)["attempts"][0]
        self.assertEqual(opened["outcome"], "opened")
        self.assertEqual(opened["provenance"]["packed_at"],
                         self.manifest(sid)["provenance"]["packed_at"])
        registry = json.loads((self.repo / ".bale" / "sessions" / sid /
                               "provenance.json").read_text())
        self.assertEqual(sorted(registry), ["packer", "work_class"],
                         msg="the registry-side stamp stays the pair")
        validate = _load_module("bale_validate").validate_telemetry_record
        self.assertEqual(validate(self.record(sid)), [])

    def test_packed_at_survives_the_close(self) -> None:
        """The close wipes .bale/sessions/<sid>/ (the manifest copy with
        it); the record keeps the pack instant."""
        sid = self.packed_sid(self.pack("worker"))
        packed_at = self.manifest(sid)["provenance"]["packed_at"]
        self.assert_ok(run_bale(self.install, ["unlock", sid],
                                cwd=self.repo, env=self.env))
        self.assertFalse((self.repo / ".bale" / "sessions" / sid).exists())
        attempts = self.record(sid)["attempts"]
        self.assertEqual(len(attempts), 2)
        self.assertEqual(attempts[0]["provenance"]["packed_at"], packed_at)
        self.assertNotIn("provenance", attempts[1],
                         msg="the stamp rides the opened attempt only")


# ---------------------------------------------------------------------------
# 4. Pure renderers and the stamper's failure path
# ---------------------------------------------------------------------------

class RendererTest(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load_module("bale_report")

    def test_sweep_entry_normalizes_committed(self) -> None:
        entry = self.m.format_pack_sweep_entry(
            "2026-01-01-x-001", "closed-read-only",
            {"status": "committed", "detail": "committed 1 file(s) as ab",
             "sha": "ab", "files": ["claude/telemetry/x.json"]})
        self.assertEqual(list(entry), SWEEP_KEYS)
        self.assertEqual(entry["status"], "committed")

    def test_sweep_entry_nothing_form_normalizes_sha_files(self) -> None:
        entry = self.m.format_pack_sweep_entry(
            "s", "swept_by", {"status": "nothing",
                              "detail": "nothing to commit"})
        self.assertIsNone(entry["sha"])
        self.assertEqual(entry["files"], [])

    def test_sweep_entry_off_keeps_entry(self) -> None:
        self.assertEqual(
            self.m.format_pack_sweep_entry("s", "superseded_by", None),
            {"sid": "s", "event": "superseded_by", "status": None,
             "detail": None, "sha": None, "files": []})

    def test_sweep_entry_rejects_unknown_event(self) -> None:
        with self.assertRaises(ValueError):
            self.m.format_pack_sweep_entry("s", "unlocked", None)

    def test_event_vocabulary(self) -> None:
        self.assertEqual(set(self.m.PACK_SWEEP_EVENTS),
                         {"superseded-by-split", "closed-read-only",
                          "superseded_by", "swept_by"})

    def test_pack_json_defaults(self) -> None:
        payload = json.loads(self.m.format_pack_json(
            sid="s", tarball=Path("/t"), log_path=Path("/l"),
            session_dir=Path("/d"), context_files=1))
        self.assertEqual(payload["sweep"], [])
        self.assertIn("include_group", payload)
        self.assertIsNone(payload["include_group"])

    def test_pack_json_existing_keys_unchanged(self) -> None:
        payload = json.loads(self.m.format_pack_json(
            sid="s", tarball=Path("/t"), log_path=Path("/l"),
            session_dir=Path("/d"), context_files=1))
        self.assertEqual(list(payload)[:13], [
            "outcome", "sid", "tarball", "log", "session_dir",
            "context_files", "readme_path", "readme_heading",
            "readme_sha256", "checkpoint_file_path",
            "checkpoint_file_sha256", "branch", "applied_latest"])
        self.assertEqual(list(payload)[13:15], ["sweep", "include_group"])
        # v0.4.48: the additive `opener` key rides after them, and only
        # it (test_pack_opener pins its value).
        self.assertEqual(list(payload)[15:], ["opener"])

    def test_include_group_shape_and_state_guard(self) -> None:
        obj = self.m.format_include_group_json(
            name="g", state="engaged", triggers=["bin"], pulled=[],
            row="g engaged (already covered)")
        self.assertEqual(list(obj),
                         ["name", "state", "triggers", "pulled", "row"])
        with self.assertRaises(ValueError):
            self.m.format_include_group_json(
                name="g", state="dormant", triggers=[], pulled=[], row="")


class StampFailureTest(unittest.TestCase):
    """stamp_swept_by is best-effort: no record, or no closed-read-only
    attempt, logs and returns None, never raises."""

    def setUp(self) -> None:
        import __main__
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-104b-u-")
        self.repo = Path(self._tmpdir.name)
        self.m = _load_module("bale_report")
        self.logged: list = []
        self._main = __main__
        self._had_log = hasattr(__main__, "log")
        self._old_log = getattr(__main__, "log", None)
        __main__.log = lambda msg, **kw: self.logged.append(msg)

    def tearDown(self) -> None:
        if self._had_log:
            self._main.log = self._old_log
        else:
            del self._main.log
        self._tmpdir.cleanup()

    def test_missing_record(self) -> None:
        self.assertIsNone(self.m.stamp_swept_by(self.repo, "gone", "me"))
        self.assertTrue(any("swept_by lineage for me not stamped" in m
                            for m in self.logged), self.logged)

    def test_no_closed_read_only_attempt(self) -> None:
        p = self.repo / "claude" / "telemetry" / "s.json"
        p.parent.mkdir(parents=True)
        record = {"record_version": 1, "session_id": "s",
                  "attempts": [{"at": "x", "outcome": "opened",
                                "command": "pack"}]}
        p.write_text(json.dumps(record))
        self.assertIsNone(self.m.stamp_swept_by(self.repo, "s", "me"))
        self.assertEqual(json.loads(p.read_text()), record,
                         msg="a failed stamp leaves the record untouched")
        self.assertTrue(any("no closed-read-only closure attempt" in m
                            for m in self.logged), self.logged)


if __name__ == "__main__":
    unittest.main()
