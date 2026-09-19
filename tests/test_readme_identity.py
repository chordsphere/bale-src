#!/usr/bin/env python3
"""Hermetic E2E for the request README's identity surfaces.

The board-33 riders (v0.3.21) pinned two behaviors around
`--readme-file`; the opener-reword session added the manifest's
`readme` key and the editor-scaffold strip, pinned in the classes after
ReadmeIdentityTest.

- **The identity echo** (evidence 45, strengthened per evidence 47):
  the pack report — human summary rows and `--json` keys alike —
  echoes the resolved README's path, its first heading line, and the
  sha256 of the shipped bytes. Path + heading alone proved
  insufficient identity (two revisions of a brief share both); the
  hash is the identity, and it is computed over the bytes inside the
  tarball, so `sha256sum` of the shipped README.md reproduces it.

- **The placeholder refusal**: a resolved brief still containing an
  unfilled placeholder — any line containing the sentinel
  `TODO(brief)` (TARBALL.md §3.4, the --readme-file row) — refuses
  loudly at read time, naming the sentinel and the file, before any
  prompt and before any session state exists.

- **The manifest's `readme` key** (ManifestReadmeKeyTest): every request
  bale builds stamps a top-level `readme` — null when no README ships,
  else exactly `{"path": "README.md", "sha256": <hex>}` with the sha256
  equal to the shipped bytes and to the report's echo (human row and
  --json key); null on the handoff path, which ships no README. The
  schema admits the key without requiring it and keeps both the key's
  object and the top level closed (ReadmeKeySchemaTest, in process).

- **The editor scaffold never ships** (ScaffoldStripTest in process,
  ScaffoldStripE2ETest under a pty with a scripted $EDITOR): the
  scaffold's instruction comment is stripped from the editor's buffer
  on both editor paths (--edit and the wizard's y), the packer's prose
  ships as typed, and a buffer holding only the untouched scaffold
  counts as no README — the manifest stamps null and no README.md
  ships.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness
in ``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_readme_identity.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import hashlib
import json
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from harness import (
    _load_module,
    bale_env,
    build_response_dir,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_bale_pty,
    tar_response_dir,
)

# Sentinels for the surfaces this file pins (one place per message).
SENTINEL = "TODO(brief)"
REFUSAL_MARKER = "unfilled placeholder"
HEADING_ROW_MARKER = "readme heading:"
SHA_ROW_MARKER = "readme sha256:"

# The scaffold's instruction-comment marker, restated (the module's
# _PACK_README_SCAFFOLD_MARKER must equal it).
SCAFFOLD_MARKER = "This README is OPTIONAL"
README_KEYS = {"path", "sha256"}
SCHEMA_PATH = (Path(__file__).resolve().parent.parent / "schemas"
               / "request-manifest.schema.json")

BRIEF_BODY = (
    "# Brief — identity echo fixture — rev A\n"
    "\n"
    "Some prose the worker authored.\n"
)


class ReadmeIdentityTest(unittest.TestCase):
    """The README identity echo and the placeholder refusal."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-readme-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def write_brief(self, body: str, name: str = "brief.md") -> Path:
        p = self.tmp / name
        p.write_text(body, encoding="utf-8")
        return p

    def pack(self, *extra: str, slug: str = "session-a"):
        return run_bale(
            self.install,
            [
                "pack", "readme identity test goal",
                "--slug", slug,
                "--include", "hello.txt",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return [d.name for d in root.iterdir() if (d / "open").is_file()]

    def shipped_readme_sha256(self, sid: str) -> str:
        """sha256 of the README.md bytes inside the outbox tarball —
        the ground truth the echo must reproduce."""
        tb = self.repo / ".bale" / "outbox" / f"request-{sid}.tar.gz"
        self.assertTrue(tb.is_file(), msg=f"no outbox tarball at {tb}")
        nnn = sid.rsplit("-", 1)[-1]
        with tarfile.open(tb, "r:gz") as tf:
            member = tf.extractfile(f"request-{nnn}/README.md")
            self.assertIsNotNone(member, msg="tarball ships no README.md")
            return hashlib.sha256(member.read()).hexdigest()

    # -- pinned behavior 1: the identity echo, human summary -------------

    def test_summary_echoes_path_heading_and_sha256(self) -> None:
        """The human report carries the resolved path, the first
        heading line, and a sha256 that matches the shipped file."""
        brief = self.write_brief(BRIEF_BODY)
        result = self.pack("--readme-file", str(brief))
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )
        sids = self.open_sids()
        self.assertEqual(len(sids), 1)
        self.assertIn(str(brief), result.stdout)
        self.assertIn("# Brief — identity echo fixture — rev A",
                      result.stdout)
        shipped_sha = self.shipped_readme_sha256(sids[0])
        self.assertIn(shipped_sha, result.stdout,
                      msg="echoed sha256 must match the shipped README.md")
        # The source file's own bytes agree too (the body ends with a
        # newline, so no normalization difference exists here).
        self.assertEqual(
            shipped_sha,
            hashlib.sha256(brief.read_bytes()).hexdigest())

    def test_no_readme_pack_has_no_echo_rows(self) -> None:
        """A --no-readme pack's summary carries no identity rows."""
        result = self.pack("--no-readme")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertNotIn(HEADING_ROW_MARKER, result.stdout)
        self.assertNotIn(SHA_ROW_MARKER, result.stdout)

    def test_headingless_brief_echoes_honest_marker(self) -> None:
        """A brief with no heading line echoes '(no heading)' rather
        than a silent blank or an invented one."""
        brief = self.write_brief("just prose, no markdown heading\n")
        result = self.pack("--readme-file", str(brief))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn("(no heading)", result.stdout)

    # -- pinned behavior 2: the identity echo, --json keys ---------------

    def test_json_report_carries_identity_keys(self) -> None:
        """--json emits readme_path / readme_heading / readme_sha256,
        agreeing with the shipped bytes."""
        brief = self.write_brief(BRIEF_BODY)
        result = self.pack("--readme-file", str(brief), "--json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(payload["readme_path"], str(brief))
        self.assertEqual(payload["readme_heading"],
                         "# Brief — identity echo fixture — rev A")
        self.assertEqual(payload["readme_sha256"],
                         self.shipped_readme_sha256(payload["sid"]))

    def test_json_keys_null_without_readme(self) -> None:
        """The three keys are present and null together on a
        no-README pack — additive keys, uniform shape."""
        result = self.pack("--no-readme", "--json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertIsNone(payload["readme_path"])
        self.assertIsNone(payload["readme_heading"])
        self.assertIsNone(payload["readme_sha256"])

    # -- pinned behavior 3: the placeholder refusal ----------------------

    def test_placeholder_brief_refuses_loudly(self) -> None:
        """A brief containing a TODO(brief) line refuses at read time,
        naming the sentinel and the file; no session state exists."""
        brief = self.write_brief(
            "# Brief — half generated\n"
            "\n"
            "TODO(brief): fill the goal restatement here\n",
            name="bad-brief.md",
        )
        result = self.pack("--readme-file", str(brief))
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn(REFUSAL_MARKER, result.stderr)
        self.assertIn(SENTINEL, result.stderr)
        self.assertIn(str(brief), result.stderr)
        self.assertEqual(self.open_sids(), [],
                         msg="a refused pack must open no session")
        self.assertFalse((self.repo / ".bale" / "outbox").exists()
                         and any((self.repo / ".bale" / "outbox").iterdir()),
                         msg="a refused pack must ship no tarball")

    def test_filled_brief_with_plain_todo_is_not_refused(self) -> None:
        """The sentinel is the exact form 'TODO(brief)' — an ordinary
        TODO in prose does not trip the refusal."""
        brief = self.write_brief(
            "# Brief — rev B\n"
            "\n"
            "TODO: the worker should consider edge cases.\n",
            name="ok-brief.md",
        )
        result = self.pack("--readme-file", str(brief))
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}",
        )


class _ReadmeSandbox(unittest.TestCase):
    """Sandbox plumbing and tarball readers shared by the classes
    below; holds no tests."""

    GOAL = "readme key test goal"

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-readme-key-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def pack(self, *extra: str, slug: str = "readme-key"):
        return run_bale(
            self.install,
            ["pack", self.GOAL, "--slug", slug, "--include", "hello.txt",
             *extra],
            cwd=self.repo, env=self.env)

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return sorted(d.name for d in root.iterdir()
                      if (d / "open").is_file())

    def request_members(self, sid: str) -> tuple:
        """(manifest dict, README.md bytes or None) from the outbox
        tarball — what the worker actually receives."""
        tb = self.repo / ".bale" / "outbox" / f"request-{sid}.tar.gz"
        self.assertTrue(tb.is_file(), msg=f"no outbox tarball at {tb}")
        nnn = sid.rsplit("-", 1)[-1]
        with tarfile.open(tb, "r:gz") as tf:
            names = tf.getnames()
            manifest = json.load(
                tf.extractfile(f"request-{nnn}/manifest.json"))
            readme_name = f"request-{nnn}/README.md"
            readme = (tf.extractfile(readme_name).read()
                      if readme_name in names else None)
        return manifest, readme

    def assert_readme_stamp(self, manifest: dict, readme) -> None:
        """The stamp describes the shipped bytes exactly."""
        self.assertIn("readme", manifest)
        if readme is None:
            self.assertIsNone(manifest["readme"])
            return
        stamp = manifest["readme"]
        self.assertIsInstance(stamp, dict)
        self.assertEqual(set(stamp), README_KEYS)
        self.assertEqual(stamp["path"], "README.md")
        self.assertEqual(stamp["sha256"], hashlib.sha256(readme).hexdigest())


class ManifestReadmeKeyTest(_ReadmeSandbox):
    """The request manifest's top-level `readme` key, on both
    request-building paths."""

    def test_no_readme_pack_stamps_null(self) -> None:
        result = self.pack("--no-readme")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        sid = self.open_sids()[0]
        manifest, readme = self.request_members(sid)
        self.assertIsNone(readme)
        self.assertIn("readme", manifest,
                      msg="the key is present on every bale-built request")
        self.assertIsNone(manifest["readme"])
        # The registry's copy of the manifest carries the same stamp.
        recorded = json.loads(
            (self.repo / ".bale" / "sessions" / sid / "manifest.json")
            .read_text(encoding="utf-8"))
        self.assertIsNone(recorded["readme"])

    def test_readme_pack_stamps_path_and_shipped_sha(self) -> None:
        brief = self.tmp / "brief.md"
        # No trailing newline: the shipped bytes gain one, and the stamp
        # must follow the shipped bytes, not the source file's.
        brief.write_text("# Brief\n\nprose with no final newline",
                         encoding="utf-8")
        result = self.pack("--readme-file", str(brief))
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        sid = self.open_sids()[0]
        manifest, readme = self.request_members(sid)
        self.assertIsNotNone(readme)
        self.assertTrue(readme.endswith(b"\n"))
        self.assert_readme_stamp(manifest, readme)
        # ...and equals the human report's echo row.
        self.assertIn(f"{SHA_ROW_MARKER} {manifest['readme']['sha256']}",
                      " ".join(result.stdout.split()))

    def test_json_echo_equals_the_stamp(self) -> None:
        brief = self.tmp / "brief.md"
        brief.write_text(BRIEF_BODY, encoding="utf-8")
        result = self.pack("--readme-file", str(brief), "--json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        manifest, readme = self.request_members(payload["sid"])
        self.assert_readme_stamp(manifest, readme)
        self.assertEqual(payload["readme_sha256"],
                         manifest["readme"]["sha256"])

    def test_handoff_stamps_null(self) -> None:
        """bale handoff builds through the shared builder and ships no
        README, so its request carries `readme: null`."""
        packed = self.pack("--no-readme", slug="readme-handoff")
        self.assertEqual(packed.returncode, 0, msg=packed.stderr)
        sid = self.open_sids()[0]
        rdir = build_response_dir(
            self.tmp / "bailout", sid,
            summary="bailout fixture for the readme-key handoff pin",
            entries=[], validation_will_run=[], claims={},
            manifest_extra={"response_kind": "bailout"})
        (rdir / "handoff.md").write_text(
            f"# Handoff\n\n## Original goal\n\n{self.GOAL}\n",
            encoding="utf-8")
        (rdir / "diagnostics.json").write_text(json.dumps({
            "session_id": sid,
            "bail_trigger": "mid-build-budget-panic",
            "bail_narrative": "fixture narrative.",
            "context_loaded": [
                {"path": "hello.txt", "verdict": "necessary", "note": ""}],
            "exploration_paths": [
                {"what": "sized it", "verdict": "productive", "note": ""}],
            "tool_calls_summary": {"bash": 1},
            "what_would_save_next_time": ["split earlier"],
        }, indent=2) + "\n", encoding="utf-8")
        tarball = tar_response_dir(rdir)
        applied = run_bale(self.install, ["apply", str(tarball)],
                           cwd=self.repo, env=self.env)
        self.assertEqual(applied.returncode, 0,
                         msg=f"{applied.stdout}\n{applied.stderr}")
        handed = run_bale(self.install, ["handoff", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(handed.returncode, 0,
                         msg=f"{handed.stdout}\n{handed.stderr}")
        new_sid = self.open_sids()[0]
        self.assertNotEqual(new_sid, sid)
        manifest, readme = self.request_members(new_sid)
        self.assertIsNone(readme)
        self.assertIn("readme", manifest)
        self.assertIsNone(manifest["readme"])


class ReadmeKeySchemaTest(unittest.TestCase):
    """request-manifest.schema.json admits `readme` (null or the
    two-key object), does not require it, and stays closed — checked
    with bale's own validator, in process."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.validate = staticmethod(
            _load_module("bale_validate").validate_against_schema)
        cls.schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))

    def base(self) -> dict:
        return {
            "session_id": "2026-09-19-schema-fixture-001",
            "project": "p", "goal": "g",
            "depends_on": {"previous_response": None,
                           "previous_probe": None},
            "constraints": [], "out_of_scope": [],
            "expects_probe": "claude-decides", "context_included": [],
        }

    def errors(self, readme=..., **extra) -> list:
        m = self.base()
        if readme is not ...:
            m["readme"] = readme
        m.update(extra)
        return self.validate(m, self.schema)

    def test_admitted_not_required(self) -> None:
        self.assertNotIn("readme", self.schema["required"])
        self.assertIs(self.schema["additionalProperties"], False)
        self.assertEqual(self.errors(), [], msg="absent key is valid")
        self.assertEqual(self.errors(None), [])
        self.assertEqual(
            self.errors({"path": "README.md", "sha256": "a" * 64}), [])

    def test_shape_is_closed_and_pinned(self) -> None:
        for label, bad in (
                ("extra key", {"path": "README.md", "sha256": "a" * 64,
                               "heading": "# x"}),
                ("missing sha256", {"path": "README.md"}),
                ("missing path", {"sha256": "a" * 64}),
                ("other path", {"path": "brief.md", "sha256": "a" * 64}),
                ("short sha256", {"path": "README.md", "sha256": "abc"}),
                ("wrong type", "README.md")):
            with self.subTest(case=label):
                self.assertNotEqual(self.errors(bad), [])

    def test_description_is_self_contained(self) -> None:
        """Request-carried surface: no repo-local doc names (the
        self-containment guard scans this too; this pin keeps the new
        key's own text honest at its source)."""
        text = json.dumps(self.schema["properties"]["readme"])
        for denied in ("BALE.md", "MASTER.md", "board ", "evidence "):
            self.assertNotIn(denied, text)


class ScaffoldStripTest(unittest.TestCase):
    """_readme_from_editor, in process: the scaffold's instruction
    comment never ships; a scaffold-only buffer is no README."""

    GOAL = "ship the widget"

    @classmethod
    def setUpClass(cls) -> None:
        cls.bp = _load_module("bale_pack")

    def scaffold(self) -> str:
        return self.bp._PACK_README_SCAFFOLD.format(
            goal=self.GOAL, constraints="(none)", out_of_scope="(none)")

    def strip(self, body: str):
        # open_in_editor returns the buffer rstripped; mirror that.
        return self.bp._readme_from_editor(
            body.rstrip(), scaffold_heading=f"# {self.GOAL}")

    def test_marker_opens_the_scaffold_comment(self) -> None:
        self.assertEqual(self.bp._PACK_README_SCAFFOLD_MARKER,
                         SCAFFOLD_MARKER)
        self.assertIn("<!--\n" + SCAFFOLD_MARKER,
                      self.bp._PACK_README_SCAFFOLD)

    def test_untouched_scaffold_is_no_readme(self) -> None:
        self.assertIsNone(self.strip(self.scaffold()))
        self.assertIsNone(self.strip(""))
        self.assertIsNone(self.strip("\n\n  \n"))

    def test_prose_ships_without_the_comment(self) -> None:
        body = self.scaffold() + "Why this session exists.\n\n- a list\n"
        out = self.strip(body)
        self.assertEqual(
            out, f"# {self.GOAL}\n\nWhy this session exists.\n\n- a list")
        self.assertNotIn(SCAFFOLD_MARKER, out)
        self.assertNotIn("<!--", out)

    def test_comment_edited_inside_is_still_stripped(self) -> None:
        body = self.scaffold().replace("(e.g. a", "(e.g. an edited") \
            + "prose\n"
        out = self.strip(body)
        self.assertNotIn("<!--", out)
        self.assertTrue(out.endswith("prose"))

    def test_packers_own_comment_ships(self) -> None:
        body = (self.scaffold()
                + "prose\n\n<!-- my own note for the worker -->\n")
        out = self.strip(body)
        self.assertIn("<!-- my own note for the worker -->", out)
        self.assertNotIn(SCAFFOLD_MARKER, out)

    def test_edited_heading_is_prose(self) -> None:
        body = self.scaffold().replace(f"# {self.GOAL}",
                                       f"# {self.GOAL}, carefully")
        self.assertEqual(self.strip(body), f"# {self.GOAL}, carefully")

    def test_seeded_file_without_scaffold_is_untouched(self) -> None:
        """--edit seeded from --readme-file: no scaffold comment, so the
        planner's text comes through as typed."""
        seed = "# Brief\n\nPlanner prose.\n\n<!-- keep -->"
        self.assertEqual(self.strip(seed), seed)


class ScaffoldStripE2ETest(_ReadmeSandbox):
    """Both editor paths under a pty with a scripted $EDITOR: the
    shipped README.md carries the packer's prose and no scaffold
    comment, and the stamp and echo still match the shipped bytes; an
    untouched scaffold ships no README and stamps null."""

    PROSE = "Prose the packer typed in the editor."

    def editor_env(self, *, append: bool) -> dict:
        env = dict(self.env)
        if append:
            script = self.tmp / "append_editor.py"
            script.write_text(
                "import sys\n"
                "with open(sys.argv[1], 'a', encoding='utf-8') as f:\n"
                f"    f.write({self.PROSE!r} + '\\n')\n",
                encoding="utf-8")
            env["EDITOR"] = f"{sys.executable} {script}"
        else:
            env["EDITOR"] = "/bin/true"  # saves the scaffold untouched
        return env

    def run_pty(self, args: list, *, env: dict, answers: str = ""):
        code, output = run_bale_pty(self.install, args, cwd=self.repo,
                                    env=env, answers=answers)
        self.assertEqual(code, 0, msg=output)
        sids = self.open_sids()
        self.assertEqual(len(sids), 1, msg=output)
        return sids[0], output

    def assert_prose_shipped(self, sid: str, output: str) -> None:
        manifest, readme = self.request_members(sid)
        self.assertIsNotNone(readme, msg=output)
        text = readme.decode("utf-8")
        self.assertIn(self.PROSE, text)
        self.assertNotIn(SCAFFOLD_MARKER, text)
        self.assertNotIn("<!--", text)
        self.assert_readme_stamp(manifest, readme)
        self.assertIn(manifest["readme"]["sha256"], output,
                      msg="the report's echo is the shipped sha256")

    def test_edit_flag_strips_the_comment(self) -> None:
        sid, output = self.run_pty(
            ["pack", self.GOAL, "--slug", "scaffold-edit",
             "--include", "hello.txt", "--edit"],
            env=self.editor_env(append=True))
        self.assert_prose_shipped(sid, output)

    def test_wizard_y_strips_the_comment(self) -> None:
        answers = (
            f"{self.GOAL}\n"   # goal
            "scaffold-wiz\n"   # slug
            "c\n"              # session shape: code
            "\n"               # forecast: Enter -> includes
            "\n" "\n" "\n"     # excludes, constraints, out-of-scope
            "y\n"              # README prompt: yes
        )
        sid, output = self.run_pty(["pack"],
                                   env=self.editor_env(append=True),
                                   answers=answers)
        self.assert_prose_shipped(sid, output)

    def test_untouched_scaffold_ships_no_readme(self) -> None:
        sid, output = self.run_pty(
            ["pack", self.GOAL, "--slug", "scaffold-bare",
             "--include", "hello.txt", "--edit"],
            env=self.editor_env(append=False))
        manifest, readme = self.request_members(sid)
        self.assertIsNone(readme, msg=output)
        self.assertIsNone(manifest["readme"])
        self.assertNotIn(SHA_ROW_MARKER, output)


if __name__ == "__main__":
    unittest.main()
