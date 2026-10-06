#!/usr/bin/env python3
"""The clipboard key's move to `[clipboard] command` (session
clipboard-key-rename, friction-points cleanup item 2), end to end.

What the session delivers, pinned outcome by outcome against a scratch
install and a scratch repo (ADR-0005), with in-process units beside:

- **Every file that configured a clipboard command before reads the
  same after.** A global or project `[probe] clipboard_command` still
  copies pack's session opener; `""` at the project layer in the legacy
  spelling still suppresses a global value written in the new one, and
  the other way round (the layer rule is spelling-blind).
- **The two-key precedence (the desk's pin).** Inside one file
  `[clipboard] command` wins when both spellings are set; the copy uses
  it, and the status row says which spelling bale used and which it
  ignored — a file that sets both is never silent about it.
- **The status row is labelled `clipboard`**, names a value read from
  the legacy spelling as such, and `bale status --json` gains the
  additive `clipboard` object (`command`, `source`, `key`, `shadowed`,
  `problem`), in and out of a repo; the existing keys are untouched.
- **`bale clipboard`'s suppress notice names the spelling** the project
  file used.
- **The review names the move.** `config_changes` renders a legacy line
  the walk writes back as `clipboard.command` as one "~" row (the value
  beside it), a cleared legacy line as "(cleared)", and a legacy line
  shadowed by a `clipboard.command` the file already had as dropped for
  that reason — never as a hand-edited stranger.
- **The words follow the key**: `bale help clipboard` and `bale help
  config init` name `[clipboard] command` and the legacy alias, and the
  three docs in the session's forecast do too.

The config trio itself — accessors, renderer, wizard walk, the crafter
twin — stays pinned in tests/test_probe_clipboard_config.py (its
pre-rename file name kept), extended there for both spellings.

Run:  python3 -m unittest tests.test_clipboard_key_rename -v
"""

from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

from harness import REPO_ROOT, SUBPROCESS_TIMEOUT, run_bale
from test_clipboard_paste_blocks import _Fixture, between_scissors, notices

sys.path.insert(0, str(REPO_ROOT / "bin"))
import bale_config  # noqa: E402  (path-injected sibling import)
import bale_report  # noqa: E402

NEW = "clipboard.command"
LEGACY = "probe.clipboard_command"


class _RenameFixture(_Fixture):
    """The paste-blocks fixture plus writers for either spelling."""

    def write_global(self, body: str) -> None:
        self.global_toml().parent.mkdir(parents=True, exist_ok=True)
        self.global_toml().write_text(body, encoding="utf-8")

    def write_project(self, body: str) -> None:
        (self.repo / "bale.toml").write_text(body, encoding="utf-8")

    def status(self, *args: str, cwd: Path | None = None):
        r = run_bale(self.install, ["status", *args], cwd=cwd or self.repo,
                     env=dict(self.env, COLUMNS="400"))
        self.assert_ok(r)
        return r

    def row(self, cwd: Path | None = None) -> str:
        r = self.status(cwd=cwd)
        hits = [ln.strip() for ln in r.stdout.splitlines()
                if ln.strip().startswith("clipboard:")]
        self.assertEqual(len(hits), 1, msg=r.stdout)
        return " ".join(hits[0][len("clipboard:"):].split())

    def clipboard_json(self, cwd: Path | None = None) -> dict:
        r = self.status("--json", cwd=cwd)
        self.assertEqual(len(r.stdout.splitlines()), 1, msg=r.stdout)
        payload = json.loads(r.stdout)
        self.assertEqual(payload["outcome"], "status")
        return payload["clipboard"]


# ---------------------------------------------------------------------------
# The legacy alias keeps every existing file working
# ---------------------------------------------------------------------------

class LegacyAliasCopyTest(_RenameFixture):

    def test_legacy_global_key_still_copies_the_opener(self) -> None:
        self.write_global(f'[probe]\nclipboard_command = "cat >{self.capture}"\n')
        r = self.pack("legacyglobal", "--include", "hello.txt")
        self.assert_ok(r)
        self.assertEqual(self.clip(), between_scissors(r.stdout))
        [line] = notices(r.stderr)
        self.assertIn("copied the session opener", line)
        self.assertIn("global bale.toml", line)

    def test_legacy_project_key_still_overrides_a_new_global_one(self) -> None:
        self.capture_globally()  # [clipboard] command, the new spelling
        project_capture = self.tmp / "project-capture.txt"
        self.commit_files(
            {"bale.toml": f'[probe]\nclipboard_command = '
                          f'"cat >{project_capture}"\n'},
            "a legacy project clipboard command")
        r = self.pack("legacyproject", "--include", "hello.txt")
        self.assert_ok(r)
        self.assertFalse(self.capture.exists())
        self.assertEqual(project_capture.read_bytes(),
                         between_scissors(r.stdout))
        self.assertIn("project bale.toml", notices(r.stderr)[0])

    def suppress_beats_the_other_layer(self, glob: str, project: str) -> None:
        self.write_global(glob)
        self.commit_files({"bale.toml": project}, "suppress here")
        r = self.pack("suppress", "--include", "hello.txt")
        self.assert_ok(r)
        self.assertFalse(self.capture.exists())
        self.assertEqual(notices(r.stderr), [],
                         msg="pack says nothing when the project opted out")

    def test_legacy_suppress_beats_a_new_global_value(self) -> None:
        self.suppress_beats_the_other_layer(
            f'[clipboard]\ncommand = "cat >{self.capture}"\n',
            '[probe]\nclipboard_command = ""\n')

    def test_new_suppress_beats_a_legacy_global_value(self) -> None:
        self.suppress_beats_the_other_layer(
            f'[probe]\nclipboard_command = "cat >{self.capture}"\n',
            '[clipboard]\ncommand = ""\n')

    def test_bale_clipboard_suppress_notice_names_the_spelling(self) -> None:
        self.capture_globally()
        for body, spelled in (('[probe]\nclipboard_command = ""\n',
                               '[probe] clipboard_command = ""'),
                              ('[clipboard]\ncommand = ""\n',
                               '[clipboard] command = ""')):
            with self.subTest(body=body):
                self.write_project(body)
                r = subprocess.run(
                    [sys.executable, str(self.install / "bin" / "bale"),
                     "clipboard"], cwd=self.repo, env=self.env, input=b"x\n",
                    capture_output=True, timeout=SUBPROCESS_TIMEOUT)
                self.assertEqual(r.returncode, 1, msg=r.stderr)
                err = r.stderr.decode("utf-8")
                self.assertIn("this project suppresses the clipboard "
                              "command", err)
                self.assertIn(f"its bale.toml sets {spelled}", err)
                self.assertFalse(self.capture.exists())


# ---------------------------------------------------------------------------
# The precedence inside one file, and the row that says so
# ---------------------------------------------------------------------------

class InFilePrecedenceTest(_RenameFixture):

    def test_new_spelling_wins_and_the_copy_uses_it(self) -> None:
        old = self.tmp / "old-capture.txt"
        self.write_global(f'[probe]\nclipboard_command = "cat >{old}"\n'
                          f'[clipboard]\ncommand = "cat >{self.capture}"\n')
        r = self.pack("bothset", "--include", "hello.txt")
        self.assert_ok(r)
        self.assertEqual(self.clip(), between_scissors(r.stdout))
        self.assertFalse(old.exists(), msg="the legacy value is ignored")

    def test_row_names_the_spelling_used_and_the_one_ignored(self) -> None:
        self.write_global('[probe]\nclipboard_command = "xclip"\n'
                          '[clipboard]\ncommand = "pbcopy"\n')
        row = self.row()
        self.assertTrue(row.startswith("pbcopy (global layer; [clipboard] "
                                       "command, which wins over the same "
                                       "file's [probe] clipboard_command "
                                       "— ignored)"), msg=row)
        self.assertTrue(row.endswith("— every paste block is copied"))
        self.write_project('[probe]\nclipboard_command = "xclip"\n'
                           '[clipboard]\ncommand = ""\n')
        row = self.row()
        self.assertTrue(row.startswith('suppressed here (this project\'s '
                                       'bale.toml sets [clipboard] command '
                                       '= ""; [clipboard] command, which '
                                       'wins over the same file\'s [probe] '
                                       'clipboard_command — ignored)'),
                        msg=row)

    def test_row_names_a_legacy_value_as_legacy(self) -> None:
        self.write_global('[probe]\nclipboard_command = "wl-copy"\n')
        self.assertEqual(self.row(), "wl-copy (global layer; via the legacy "
                                     "[probe] clipboard_command) — every "
                                     "paste block is copied")
        self.write_project('[probe]\nclipboard_command = ""\n')
        self.assertEqual(self.row(), 'suppressed here (this project\'s '
                                     'bale.toml sets [probe] '
                                     'clipboard_command = ""; via the '
                                     'legacy [probe] clipboard_command) — '
                                     'nothing is copied')
        self.write_project('[clipboard]\ncommand = "pbcopy"\n')
        self.assertEqual(self.row(), "pbcopy (project layer) — every paste "
                                     "block is copied",
                         msg="the new spelling, alone, needs no aside")


# ---------------------------------------------------------------------------
# bale status --json: the additive clipboard object
# ---------------------------------------------------------------------------

class StatusJsonClipboardTest(_RenameFixture):

    KEYS = ("command", "source", "key", "shadowed", "problem")

    def test_every_state_in_and_out_of_a_repo(self) -> None:
        def expect(**kw):
            want = {k: None for k in self.KEYS}
            want.update(kw)
            return want

        self.assertEqual(self.clipboard_json(), expect())
        self.assertEqual(self.clipboard_json(cwd=self.tmp), expect())

        self.write_global('[clipboard]\ncommand = " pbcopy "\n')
        self.assertEqual(self.clipboard_json(),
                         expect(command="pbcopy", source="global", key=NEW))
        self.assertEqual(self.clipboard_json(cwd=self.tmp),
                         expect(command="pbcopy", source="global", key=NEW),
                         msg="outside a repo the global file decides")

        self.write_project('[probe]\nclipboard_command = "wl-copy"\n')
        self.assertEqual(self.clipboard_json(),
                         expect(command="wl-copy", source="project",
                                key=LEGACY))

        self.write_project('[probe]\nclipboard_command = "wl-copy"\n'
                           '[clipboard]\ncommand = "xclip"\n')
        self.assertEqual(self.clipboard_json(),
                         expect(command="xclip", source="project", key=NEW,
                                shadowed=LEGACY))

        self.write_project('[clipboard]\ncommand = ""\n')
        self.assertEqual(self.clipboard_json(),
                         expect(source="project", key=NEW))

        self.write_project("[clipboard]\ncommand = '''pbcopy'''\n")
        got = self.clipboard_json()
        self.assertIsNone(got["command"])
        self.assertEqual((got["source"], got["key"], got["shadowed"]),
                         ("project", NEW, None))
        self.assertIn("clipboard.command is triple-quoted", got["problem"])
        self.assertIn("bale config init", got["problem"])

    def test_existing_keys_are_untouched(self) -> None:
        r = self.status("--json")
        payload = json.loads(r.stdout)
        for key in ("outcome", "version", "sid", "repo", "session",
                    "staging", "outbox", "applied", "sessions", "scopes",
                    "integration_lock", "config"):
            self.assertIn(key, payload)
        self.assertNotIn("clipboard", payload["config"],
                         msg="the object is top-level, beside config")
        self.assertEqual(sorted(payload["clipboard"]), sorted(self.KEYS))

    def test_json_object_matches_the_human_row(self) -> None:
        """One read, two renderings: the object's facts are the row's."""
        self.write_global('[probe]\nclipboard_command = "pbcopy"\n'
                          '[clipboard]\ncommand = "wl-copy"\n')
        obj = self.clipboard_json()
        rendered = bale_report.describe_clipboard_state(
            obj["command"], obj["source"], obj["problem"],
            key=obj["key"], shadowed=obj["shadowed"])
        self.assertEqual(" ".join(rendered.split()), self.row())


# ---------------------------------------------------------------------------
# The words follow the key
# ---------------------------------------------------------------------------

class WordsFollowTheKeyTest(_RenameFixture):

    def help_text(self, *verb: str) -> str:
        r = run_bale(self.install, ["help", *verb], cwd=self.repo,
                     env=dict(self.env, COLUMNS="80"))
        self.assert_ok(r)
        return " ".join(r.stdout.split())

    def test_bale_help_clipboard_names_both_spellings(self) -> None:
        flat = self.help_text("clipboard")
        self.assertIn("[clipboard] command in bale.toml", flat)
        self.assertIn("[probe] clipboard_command, is still read as a legacy "
                      "alias", flat)
        self.assertIn("when a file sets both, [clipboard] command wins", flat)

    def test_config_init_help_names_the_key_and_the_alias(self) -> None:
        flat = self.help_text("config", "init")
        self.assertIn("([clipboard] command;", flat)
        self.assertIn("[probe] clipboard_command is read as a legacy alias "
                      "and re-spelled on the wizard's next write", flat)

    def test_the_docs_name_the_key_and_the_alias(self) -> None:
        """The three docs in the forecast: docs/TARBALL.md §4.3's
        clipboard paragraph, README.md's config paragraph, and
        claude/context/bale-internals.md."""
        for rel, phrases in (
                ("docs/TARBALL.md",
                 ("`command` under `[clipboard]` in `bale.toml`",
                  "`[probe] clipboard_command`", "legacy")),
                ("README.md",
                 ("`[clipboard]` (this machine's clipboard command,",
                  "`[probe] clipboard_command`")),
                ("claude/context/bale-internals.md",
                 ("`[clipboard] command` names the machine's clipboard "
                  "command",
                  "`[probe] clipboard_command`",
                  "`clipboard.command`"))):
            text = (REPO_ROOT / rel).read_text(encoding="utf-8")
            flat = " ".join(text.split())
            for phrase in phrases:
                with self.subTest(doc=rel, phrase=phrase):
                    self.assertIn(phrase, flat)
        tarball = (REPO_ROOT / "docs" / "TARBALL.md").read_text(
            encoding="utf-8")
        self.assertNotIn("`clipboard_command` under `[probe]`", tarball,
                         msg="the old wording is gone, not duplicated")
        readme = " ".join(
            (REPO_ROOT / "README.md").read_text(encoding="utf-8").split())
        self.assertNotIn("and `[probe]` (the probe scaffold's clipboard "
                         "command)", readme,
                         msg="README no longer lists the clipboard key as "
                             "project-layer only")


# ---------------------------------------------------------------------------
# In-process units: the review rows and the row renderer
# ---------------------------------------------------------------------------

class ConfigChangesMoveTest(unittest.TestCase):
    """config_changes treats the legacy spelling as the key it aliases."""

    def rows(self, old: dict, new: dict, layer: str = "project") -> list:
        return bale_config.config_changes(old, new, layer=layer)

    def test_a_move_with_the_same_value_is_one_row(self) -> None:
        self.assertEqual(
            self.rows({"probe": {"clipboard_command": "pbcopy"}},
                      {"clipboard": {"command": "pbcopy"}}),
            [("~", 'probe.clipboard_command → clipboard.command = "pbcopy"  '
                   "(the legacy spelling moves; same value)")])

    def test_a_move_with_a_new_value_shows_both(self) -> None:
        self.assertEqual(
            self.rows({"probe": {"clipboard_command": "pbcopy"}},
                      {"clipboard": {"command": "wl-copy"}}, layer="global"),
            [("~", 'probe.clipboard_command = "pbcopy" → clipboard.command '
                   '= "wl-copy"  (the legacy spelling moves)')])

    def test_a_cleared_legacy_line_is_cleared_not_dropped(self) -> None:
        self.assertEqual(
            self.rows({"probe": {"clipboard_command": "pbcopy"}}, {}),
            [("-", 'probe.clipboard_command = "pbcopy"  (cleared)')])

    def test_a_shadowed_legacy_line_says_why_it_goes(self) -> None:
        self.assertEqual(
            self.rows({"probe": {"clipboard_command": "xclip"},
                       "clipboard": {"command": "pbcopy"}},
                      {"clipboard": {"command": "pbcopy"}}),
            [("-", 'probe.clipboard_command = "xclip"  (legacy spelling '
                   "beside clipboard.command, which wins; ignored by bale, "
                   "dropped by the write)")])

    def test_the_move_row_sits_where_the_clipboard_screen_sat(self) -> None:
        rows = self.rows(
            {"identity": {"packer": "bob"},
             "probe": {"clipboard_command": "pbcopy"},
             "validation": {"base": "x.sh"}},
            {"identity": {"packer": "carol"},
             "clipboard": {"command": "pbcopy"},
             "validation": {"base": "y.sh"}})
        self.assertEqual([r[1].split(" ")[0] for r in rows],
                         ["identity.packer", "probe.clipboard_command",
                          "validation.base"])

    def test_unrelated_reviews_are_unchanged(self) -> None:
        old = {"identity": {"packer": "bob"}, "mystery": {"k": 1}}
        new = {"identity": {"packer": "carol"},
               "clipboard": {"command": "pbcopy"}}
        self.assertEqual(self.rows(old, new), [
            ("~", 'identity.packer = "bob" → "carol"'),
            ("+", 'clipboard.command = "pbcopy"'),
            ("-", "mystery.k = 1  (not walked at this layer; dropped)"),
        ])


class DescribeClipboardStateUnitTest(unittest.TestCase):

    def test_every_wording(self) -> None:
        d = bale_report.describe_clipboard_state
        self.assertEqual(d("pbcopy", "project", None, key=NEW),
                         "pbcopy (project layer) — every paste block is "
                         "copied")
        self.assertEqual(d("pbcopy", "project", None, key=LEGACY),
                         "pbcopy (project layer; via the legacy [probe] "
                         "clipboard_command) — every paste block is copied")
        self.assertEqual(d("pbcopy", "global", None, key=NEW,
                           shadowed=LEGACY),
                         "pbcopy (global layer; [clipboard] command, which "
                         "wins over the same file's [probe] "
                         "clipboard_command — ignored) — every paste block "
                         "is copied")
        self.assertEqual(d(None, "project", None, key=LEGACY),
                         'suppressed here (this project\'s bale.toml sets '
                         '[probe] clipboard_command = ""; via the legacy '
                         '[probe] clipboard_command) — nothing is copied')
        self.assertEqual(d(None, "global", None, key=NEW),
                         "unset (the global bale.toml sets [clipboard] "
                         "command empty) — nothing is copied; `bale config "
                         "init --global` sets one")
        self.assertEqual(d(None, None, None),
                         "unset — nothing is copied; `bale config init "
                         "--global` sets one for this machine")
        self.assertEqual(d(None, "project", "f: x is triple-quoted.",
                           key=NEW, shadowed=LEGACY),
                         "UNREADABLE — nothing is copied until it is fixed: "
                         "f: x is triple-quoted.",
                         msg="a refusal carries its own text, nothing else")

    def test_resolution_and_triple_agree(self) -> None:
        """resolve_clipboard_command is the first three facts of
        resolve_clipboard, never a second read."""
        resolution = bale_report.resolve_clipboard(None)
        self.assertEqual(bale_report.resolve_clipboard_command(None),
                         tuple(resolution)[:3])
        self.assertEqual(resolution._fields,
                         ("command", "source", "problem", "key", "shadowed"))
        self.assertEqual(bale_report.clipboard_key_display(NEW),
                         "[clipboard] command")
        self.assertEqual(bale_report.clipboard_key_display(LEGACY),
                         bale_config.clipboard_key_display(LEGACY))
        self.assertEqual(bale_report.clipboard_key_display(None),
                         "the clipboard command")


if __name__ == "__main__":
    unittest.main(verbosity=2)
