#!/usr/bin/env python3
"""What `bale status` and the dossier say of open sessions (0.4.63,
session 2026-11-16-status-says-more-001: slips 1, 3, 5 and 7 from the
office's suggestion box, and two fold-ins).

What this suite pins:

- **Where bale looks** (``SearchDirsTest``): `bale status --json`'s
  ``config.search_dirs`` is the configured ``[apply] search_paths`` list
  in order, tilde and variables expanded, and ``config.search_paths``
  stays its count.
- **Every open session** (``OpenSessionsTest``): the top-level
  ``open_sessions`` object has exactly the ``sessions`` keys, each entry
  classified on its own facts — a clarification-suspended session that
  does not hold the lock reads "clarification" with its rounds, a
  packed one "packed" — while ``sid`` and ``session`` still describe the
  lock session; null outside a repo; ``bale contract --json`` lists the
  line's keys as it emits them.
- **The responses the named search would find** (same class): each
  entry's ``responses`` lists ``response-<sid>.tar.gz`` and its
  ``(N)`` copies in cwd and each search directory, newest first, by
  absolute path, never a file named for another session or a
  ``-variant``.
- **A newer copy is said** (``NewerCopyTest``): `bale apply` and `bale
  retry` given a relative name that resolves, with a newer
  ``<name> (1).tar.gz`` in another searched directory, name the copy,
  the word "newer" and the paste-ready line, and still apply the bytes
  of the file named; an older copy is not mentioned; under ``--json``
  the note rides stderr and stdout stays one line.
- **A clarification landing writes an attempt**
  (``ClarificationAttemptTest``): outcome "clarification", command
  "apply", the clarification summary with rounds 1; the dossier shows
  it and reads the session in flight; the later normal response closes
  it ("clarification", "applied"); the record validates and `bale stats
  --json` reads the corpus.
- **The clipboard row says UTF-16LE** (``ClipboardEncodingTest``): for
  clip.exe the human row says so and ``clipboard.encoding`` reads
  "utf-16le"; another command reads "utf-8" and its row names no
  UTF-16; null when nothing is copied.
- **HOLD classes in the contract** (``HoldClassVocabularyTest``): the
  ``hold-class`` vocabulary is bin/bale_stats.py's HOLD_CLASSES, read
  from there, in both renderings.
- **The release** (``ReleaseTest``): bin/VERSION is 0.4.63 and
  claude/changelog/0.4.63.json is its record.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it.

Run directly::

    python3 tests/test_status_says_more.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:  # the dotted run form needs it
    sys.path.insert(0, _TESTS_DIR)

from harness import (  # noqa: E402 — sys.path tweak above
    _load_module,
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

FIRST_STATUS_KEYS = [
    "outcome", "version", "sid", "repo", "session", "staging", "outbox",
    "applied", "sessions", "scopes", "integration_lock", "config",
    "clipboard",
]
QUESTION = {
    "question": "fixture question?",
    "context": "fixture context",
    "default_assumption": "fixture assumption",
    "why_blocked": "fixture blocker",
}


def _one_json_line(stdout: str) -> dict:
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    if len(lines) != 1:
        raise AssertionError(f"expected one stdout line, got {len(lines)}:"
                             f"\n{stdout}")
    return json.loads(lines[0])


class _Scratch(unittest.TestCase):
    """A fresh hermetic repo per test with the sandbox off and two
    search directories configured (a tilde spelling for the first)."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-saysmore-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        self.dl1 = self.home / "dl1"
        self.dl2 = self.tmp / "dl2"
        self.dl1.mkdir()
        self.dl2.mkdir()
        for name in ("a.txt", "b.txt"):
            (self.repo / name).write_text(f"{name}\n", encoding="utf-8")
        self.commit_config(
            "[sandbox]\nenabled = false\n\n"
            f"[apply]\nsearch_paths = [\"~/dl1\", \"{self.dl2}\"]\n",
            "a.txt", "b.txt")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def commit_config(self, text: str, *extra: str) -> None:
        (self.repo / "bale.toml").write_text(text, encoding="utf-8")
        run_checked(["git", "add", "bale.toml", *extra], cwd=self.repo,
                    env=self.genv)
        run_checked(["git", "commit", "-m", "fixture config"],
                    cwd=self.repo, env=self.genv)

    def bale(self, *args: str, cwd: Path = None):
        return run_bale(self.install, list(args), cwd=cwd or self.repo,
                        env=self.env)

    def ok(self, result, code: int = 0):
        self.assertEqual(result.returncode, code,
                         msg=f"stdout:\n{result.stdout}\n"
                             f"stderr:\n{result.stderr}")
        return result

    def pack(self, slug: str, include: str) -> str:
        before = set(self.open_sids())
        self.ok(self.bale("pack", f"says-more fixture goal for {slug}",
                          "--slug", slug, "--include", include,
                          "--no-readme"))
        new = sorted(set(self.open_sids()) - before)
        self.assertEqual(len(new), 1)
        return new[0]

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return sorted(d.name for d in root.iterdir()
                      if (d / "open").is_file())

    def status_json(self, cwd: Path = None) -> dict:
        return _one_json_line(self.ok(self.bale("status", "--json",
                                                cwd=cwd)).stdout)

    def response(self, sid: str, where: Path, name: str,
                 content: str, path: str = "a.txt") -> Path:
        rdir = build_response_dir(
            self.tmp / f"build-{name}-{len(list(self.tmp.iterdir()))}",
            sid, summary="says-more fixture",
            entries=[{"path": path, "action": "modified",
                      "reason": "the fixture goal's rewrite",
                      "data": content.encode("utf-8")}])
        built = tar_response_dir(rdir)
        target = where / name
        built.rename(target)
        return target

    def clarification(self, sid: str, where: Path) -> Path:
        rdir = build_response_dir(
            self.tmp / f"clar-{sid}", sid,
            summary="says-more fixture: blocked on a question",
            entries=[], validation_will_run=[],
            validation_sh="#!/usr/bin/env bash\n# no-op\nexit 0\n",
            manifest_extra={"response_kind": "clarification",
                            "questions": [dict(QUESTION)]})
        built = tar_response_dir(rdir)
        target = where / f"clarification-{sid}.tar.gz"
        built.rename(target)
        return target

    @staticmethod
    def touch(path: Path, mtime: int) -> None:
        os.utime(path, (mtime, mtime))

    def record(self, sid: str) -> dict:
        return json.loads((self.repo / "claude" / "telemetry"
                           / f"{sid}.json").read_text(encoding="utf-8"))


class SearchDirsTest(_Scratch):

    def test_search_dirs_is_the_expanded_list_beside_the_count(self) -> None:
        config = self.status_json()["config"]
        self.assertEqual(config["search_dirs"],
                         [str(self.dl1), str(self.dl2)])
        self.assertEqual(config["search_paths"], 2,
                         msg="search_paths stays the count")
        self.assertEqual(list(config)[:6],
                         ["project", "global", "hooks_wired", "search_paths",
                          "baleignore", "summary_failed"],
                         msg="every existing config key keeps its place")

    def test_no_search_paths_is_an_empty_list(self) -> None:
        self.commit_config("[sandbox]\nenabled = false\n")
        config = self.status_json()["config"]
        self.assertEqual(config["search_dirs"], [])
        self.assertEqual(config["search_paths"], 0)


class OpenSessionsTest(_Scratch):

    def test_keys_and_null_outside_a_repo(self) -> None:
        payload = self.status_json()
        self.assertEqual(list(payload), FIRST_STATUS_KEYS + ["open_sessions"])
        self.assertEqual(payload["open_sessions"], {})
        outside = self.tmp / "outside"
        outside.mkdir()
        payload = self.status_json(cwd=outside)
        self.assertIsNone(payload["open_sessions"])
        self.assertIsNone(payload["sessions"])

    def test_every_session_classified_and_its_responses(self) -> None:
        first = self.pack("first", "a.txt")
        second = self.pack("second", "b.txt")
        lock = self.open_sids()[0]
        other = second if lock == first else first
        # The session that does NOT hold the lock lands a clarification.
        self.ok(self.bale("apply", str(self.clarification(other, self.tmp)),
                          "--no-interact"))

        # Response tarballs for the lock session: the plain name in cwd,
        # a newer (1) copy in the second search dir, an older (2) in the
        # first; and files that must not be listed — another session's,
        # a -variant, a sid-prefixed name of another session.
        plain = self.response(lock, self.repo, f"response-{lock}.tar.gz",
                              "x\n")
        newer = self.response(lock, self.dl2, f"response-{lock} (1).tar.gz",
                              "y\n")
        older = self.response(lock, self.dl1, f"response-{lock} (2).tar.gz",
                              "z\n")
        self.touch(plain, 1_700_000_100)
        self.touch(newer, 1_700_000_200)
        self.touch(older, 1_700_000_000)
        for stray in (f"response-{lock}-variant.tar.gz",
                      f"response-{lock}-002.tar.gz",
                      f"response-{other}.tar.gz", "response-x.tar.gz"):
            (self.dl1 / stray).write_bytes(b"not read")

        payload = self.status_json()
        self.assertEqual(payload["sid"], lock)
        self.assertEqual(payload["session"]["state"], "packed",
                         msg="`session` still describes the lock session")
        entries = payload["open_sessions"]
        self.assertEqual(list(entries), payload["sessions"])
        self.assertEqual(list(entries[lock]),
                         ["state", "goal", "expects_probe", "clarification",
                          "responses"])
        self.assertEqual(entries[lock]["state"], "packed")
        self.assertEqual(entries[lock]["goal"], payload["session"]["goal"])
        self.assertEqual(entries[lock]["expects_probe"],
                         payload["session"]["expects_probe"])
        self.assertIsNone(entries[lock]["clarification"])
        self.assertEqual(entries[other]["state"], "clarification")
        self.assertIn(other.split("-")[3], entries[other]["goal"])
        clar = entries[other]["clarification"]
        self.assertEqual(clar["rounds"], 1)
        self.assertEqual(clar["questions"], 1)
        self.assertEqual(clar["from"], "worker")
        self.assertEqual(clar["awaiting"], "planner")
        self.assertEqual(clar["latest_record"],
                         f".bale/clarifications/{other}/001.json")

        responses = entries[lock]["responses"]
        self.assertEqual([r["path"] for r in responses],
                         [str(newer.resolve()), str(plain.resolve()),
                          str(older.resolve())],
                         msg="newest first, absolute, nothing stray")
        self.assertEqual([r["copy"] for r in responses], [1, None, 2])
        self.assertTrue(all(Path(r["path"]).is_absolute()
                            for r in responses))
        self.assertEqual([r["name"] for r in entries[other]["responses"]],
                         [f"response-{other}.tar.gz"],
                         msg="each session lists its own names only")

    def test_held_session_reads_held(self) -> None:
        sid = self.pack("held", "a.txt")
        failing = ("#!/usr/bin/env bash\necho \"[FAIL] fixture check\"\n"
                   "exit 1\n")
        rdir = build_response_dir(
            self.tmp / "heldbuild", sid, summary="hold fixture",
            entries=[{"path": "a.txt", "action": "modified",
                      "reason": "fixture", "data": b"held\n"}],
            validation_sh=failing)
        self.ok(self.bale("apply", str(tar_response_dir(rdir)),
                          "--no-interact"), 1)
        entry = self.status_json()["open_sessions"][sid]
        self.assertEqual(entry["state"], "held")

    def test_contract_lists_the_status_keys_as_emitted(self) -> None:
        contract = _one_json_line(self.ok(self.bale("contract",
                                                    "--json")).stdout)
        self.assertEqual(contract["json_keys"]["status"],
                         list(self.status_json()))


class NewerCopyTest(_Scratch):

    def setUp(self) -> None:
        super().setUp()
        self.sid = self.pack("copy", "a.txt")
        self.name = f"response-{self.sid}.tar.gz"
        self.plain = self.response(self.sid, self.dl1, self.name,
                                   "from the named file\n")
        self.copy = self.response(self.sid, self.dl2,
                                  f"response-{self.sid} (1).tar.gz",
                                  "from the newer copy\n")

    def test_apply_says_newer_and_applies_the_named_file(self) -> None:
        self.touch(self.plain, 1_700_000_000)
        self.touch(self.copy, 1_700_000_500)
        result = self.ok(self.bale("apply", self.name, "--no-interact"))
        out = result.stdout
        self.assertIn(self.copy.name, out)
        self.assertIn("newer", out)
        self.assertIn(f"    bale apply '{self.copy.resolve()}'\n", out)
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"),
                         "from the named file\n",
                         msg="the file named is the one applied")

    def test_json_keeps_stdout_one_line(self) -> None:
        self.touch(self.plain, 1_700_000_000)
        self.touch(self.copy, 1_700_000_500)
        result = self.ok(self.bale("apply", self.name, "--no-interact",
                                   "--json"))
        payload = _one_json_line(result.stdout)
        self.assertEqual(payload["outcome"], "applied")
        self.assertIn("newer", result.stderr)
        self.assertIn(self.copy.name, result.stderr)

    def test_retry_says_it_too(self) -> None:
        self.touch(self.plain, 1_700_000_000)
        self.touch(self.copy, 1_700_000_500)
        result = self.ok(self.bale("retry", self.name, "--no-interact"))
        self.assertIn(f"    bale retry '{self.copy.resolve()}'\n",
                      result.stdout)
        self.assertEqual((self.repo / "a.txt").read_text(encoding="utf-8"),
                         "from the named file\n")

    def test_an_older_copy_is_not_mentioned(self) -> None:
        self.touch(self.plain, 1_700_000_500)
        self.touch(self.copy, 1_700_000_000)
        result = self.ok(self.bale("apply", self.name, "--no-interact"))
        self.assertNotIn("newer", result.stdout)
        self.assertNotIn(self.copy.name, result.stdout)


class NewerCopyNoteUnitTest(unittest.TestCase):
    """bin/bale's newer_numbered_copy_note, in process."""

    @classmethod
    def setUpClass(cls) -> None:
        from harness import _load_cli
        cls.cli = _load_cli()

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-newernote-")
        self.tmp = Path(self._tmpdir.name)
        self.cwd = self.tmp / "cwd"
        self.sp = self.tmp / "sp"
        self.cwd.mkdir()
        self.sp.mkdir()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def put(self, where: Path, name: str, mtime: int) -> Path:
        path = where / name
        path.write_bytes(name.encode())
        os.utime(path, (mtime, mtime))
        return path

    def note(self, arg: str, resolved: Path):
        return self.cli.newer_numbered_copy_note(
            arg, resolved, self.cwd, [str(self.sp)], "apply")

    def test_none_without_a_newer_copy(self) -> None:
        named = self.put(self.cwd, "response-s-001.tar.gz", 200)
        self.assertIsNone(self.note(named.name, named))
        self.put(self.sp, "response-s-001 (1).tar.gz", 100)
        self.assertIsNone(self.note(named.name, named), msg="older copy")
        self.put(self.sp, "response-s-001-variant.tar.gz", 300)
        self.assertIsNone(self.note(named.name, named), msg="not a copy")

    def test_names_every_newer_copy_newest_first(self) -> None:
        named = self.put(self.cwd, "response-s-001.tar.gz", 100)
        two = self.put(self.cwd, "response-s-001 (2).tar.gz", 300)
        one = self.put(self.sp, "response-s-001 (1).tar.gz", 200)
        note = self.note(named.name, named)
        lines = note.split("\n")
        self.assertIn("newer", lines[0])
        self.assertIn(f"{two.name}, {one.name}", lines[0])
        self.assertEqual(lines[1:], [f"    bale apply '{two.resolve()}'",
                                     f"    bale apply '{one.resolve()}'"])

    def test_absolute_names_and_other_suffixes_are_left_alone(self) -> None:
        named = self.put(self.cwd, "response-s-001.tar.gz", 100)
        self.put(self.cwd, "response-s-001 (1).tar.gz", 200)
        self.assertIsNone(self.note(str(named), named))
        notes = self.put(self.cwd, "notes.md", 100)
        self.put(self.cwd, "notes (1).md", 200)
        self.assertIsNone(self.note(notes.name, notes))


class ClarificationAttemptTest(_Scratch):

    def test_landing_writes_an_attempt_the_dossier_shows(self) -> None:
        sid = self.pack("clar", "a.txt")
        result = self.ok(self.bale("apply",
                                   str(self.clarification(sid, self.tmp)),
                                   "--no-interact", "--json"))
        line = _one_json_line(result.stdout)
        self.assertEqual(line["outcome"], "clarification")
        self.assertEqual(line["telemetry"], f"claude/telemetry/{sid}.json")

        record = self.record(sid)
        bv = _load_module("bale_validate")
        self.assertEqual(bv.validate_telemetry_record(record), [])
        self.assertEqual([a["outcome"] for a in record["attempts"]],
                         ["opened", "clarification"])
        attempt = record["attempts"][-1]
        self.assertEqual(attempt["command"], "apply")
        self.assertEqual(attempt["clarification"]["rounds"], 1)
        self.assertEqual(len(attempt["clarification"]["records"]), 1)
        self.assertIsNone(attempt["validation"])
        self.assertEqual(self.open_sids(), [sid], msg="still open")

        dossier = _one_json_line(self.ok(self.bale(
            "stats", "--sid", sid, "--json")).stdout)
        self.assertEqual([a["outcome"] for a in dossier["attempts"]],
                         ["opened", "clarification"])
        self.assertEqual(dossier["attempts"][-1]["clarification"]["rounds"],
                         1)
        self.assertTrue(dossier["record"]["in_flight"])
        human = self.ok(self.bale("stats", "--sid", sid)).stdout
        self.assertIn("clarification", human)

        # The later normal response applies and closes the session.
        self.ok(self.bale("apply",
                          str(self.response(sid, self.tmp, "normal.tar.gz",
                                            "answered\n")),
                          "--no-interact"))
        record = self.record(sid)
        self.assertEqual([a["outcome"] for a in record["attempts"]][-2:],
                         ["clarification", "applied"])
        self.assertEqual(bv.validate_telemetry_record(record), [])
        self.assertEqual(self.open_sids(), [])
        stats = _one_json_line(self.ok(self.bale("stats", "--json")).stdout)
        self.assertEqual(stats["outcome"], "stats")


class ClipboardEncodingTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.br = _load_module("bale_report")

    def test_encoding_words(self) -> None:
        enc = self.br.clipboard_encoding
        for command in ("clip.exe", "CLIP.EXE", "/mnt/c/Windows/System32/"
                        "clip.exe", "'C:\\Windows\\clip.exe'"):
            with self.subTest(command=command):
                self.assertEqual(enc(command), "utf-16le")
        for command in ("pbcopy", "xclip -selection clipboard",
                        "cmd.exe /c clip"):
            with self.subTest(command=command):
                self.assertEqual(enc(command), "utf-8")
        self.assertIsNone(enc(None))

    def test_row_says_utf16le_for_clip_exe_only(self) -> None:
        d = self.br.describe_clipboard_state
        row = d("clip.exe", "project", None, key="clipboard.command")
        self.assertIn("UTF-16LE", row)
        self.assertTrue(row.startswith("clip.exe (project layer) — every "
                                       "paste block is copied"))
        other = d("pbcopy", "project", None, key="clipboard.command")
        self.assertNotIn("UTF-16", other)
        self.assertEqual(other, "pbcopy (project layer) — every paste "
                                "block is copied")


class ClipboardStatusE2ETest(unittest.TestCase):
    """`bale status` with clip.exe configured: nothing is copied by
    status itself, so the command need not exist."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-clipenc-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def status(self, *args: str):
        r = run_bale(self.install, ["status", *args], cwd=self.repo,
                     env=self.env)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        return r

    def test_clip_exe_and_another_command(self) -> None:
        self.assertIsNone(_one_json_line(self.status("--json").stdout)
                          ["clipboard"]["encoding"])
        (self.repo / "bale.toml").write_text(
            '[clipboard]\ncommand = "clip.exe"\n', encoding="utf-8")
        self.assertIn("UTF-16LE", " ".join(self.status().stdout.split()))
        self.assertEqual(_one_json_line(self.status("--json").stdout)
                         ["clipboard"]["encoding"], "utf-16le")
        (self.repo / "bale.toml").write_text(
            '[clipboard]\ncommand = "pbcopy"\n', encoding="utf-8")
        self.assertNotIn("UTF-16", self.status().stdout)
        self.assertEqual(_one_json_line(self.status("--json").stdout)
                         ["clipboard"]["encoding"], "utf-8")


class HoldClassVocabularyTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.br = _load_module("bale_report")
        cls.stats = _load_module("bale_stats")

    def schemas(self) -> dict:
        root = Path(self.br.__file__).resolve().parent.parent
        return {home: json.loads((root / home).read_text(encoding="utf-8"))
                for home in self.br.contract_schema_homes()}

    def test_json_entry_reads_the_stats_tuple(self) -> None:
        line = json.loads(self.br.format_contract_json(
            version="9.9.9", schemas=self.schemas()))
        entry = line["vocabularies"]["hold-class"]
        self.assertEqual(entry, {
            "home": "bin/bale_stats.py", "pointer": "HOLD_CLASSES",
            "values": ["checkpoint-defect", "both", "checkpoint",
                       "validation"]})
        self.assertEqual(entry["values"], list(self.stats.HOLD_CLASSES))
        self.assertFalse(hasattr(self.br, "HOLD_CLASSES"),
                         msg="one home for the words, never a second list")

    def test_human_listing_names_it(self) -> None:
        text = self.br.format_contract_report(version="9.9.9",
                                              schemas=self.schemas())
        self.assertIn("  hold-class  bin/bale_stats.py HOLD_CLASSES", text)
        self.assertIn("checkpoint-defect, both, checkpoint, validation",
                      text)



class ReleaseTest(unittest.TestCase):

    def test_version_and_changelog_record(self) -> None:
        root = Path(_TESTS_DIR).parent
        self.assertEqual((root / "bin" / "VERSION").read_text(
            encoding="utf-8"), "0.4.63\n")
        record = json.loads((root / "claude" / "changelog"
                             / "0.4.63.json").read_text(encoding="utf-8"))
        self.assertEqual(record["version"], "0.4.63")
        self.assertEqual(record["session_id"],
                         "2026-11-16-status-says-more-001")


if __name__ == "__main__":
    unittest.main()
