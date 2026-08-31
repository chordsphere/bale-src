#!/usr/bin/env python3
"""Hermetic E2E for the named include group (board 64; BALE.md §7.2,
§11 row 35).

Pins the group's load-bearing claims at the pack surface:

- Automatic engagement: a pack whose resolved includes touch a
  configured trigger pulls the group's paths into shipped context —
  they land in the tarball's ``context/`` and in
  ``manifest.context_included`` — with a loud report line naming the
  group and the trigger.
- Read side only: engagement never widens the recorded write
  forecast — the manifest's ``resolved_scope`` (and the registry's
  ``scope.json``) stay on the user's own includes, so a sibling pack
  whose forecast is disjoint from the *user's* includes still packs
  alongside even when the group's pulls would collide.
- Non-engagement is silent: includes that touch no trigger add
  nothing and log nothing about the group.
- Already-covered pulls: a whole-tree default pack engages (``.``
  covers every trigger) but adds nothing, and says so.
- The opt-out is loud and strict: ``--no-include-group <name>``
  skips the pull with a FORCE line and a report row; a mismatched
  name refuses; the flag with no configured group refuses.
- Config coherence refuses loudly: a half-configured group (name
  without lists) fails the pack; a dangling configured pull fails
  the pack when the group engages.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness
in ``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_include_group.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import tarfile
import tempfile
import unittest
from pathlib import Path

from harness import (
    bale_env,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_checked,
)

# Sentinels for the surfaces this file pins. Kept in one place so a
# message rewording breaks one line, not several assertions.
GROUP_NAME = "release-surface"
ENGAGED_MARKER = f"include group '{GROUP_NAME}' engaged"
PULLED_MARKER = "pulled"
COVERED_MARKER = "all group paths already covered"
OPTOUT_MARKER = f"include group '{GROUP_NAME}' opt-out (--no-include-group)"
OPTOUT_MISMATCH_MARKER = "does not match the configured include group"
OPTOUT_UNCONFIGURED_MARKER = "no include group is configured"
DANGLING_PULL_MARKER = "configured pull path does not exist"
HALF_CONFIGURED_MARKER = "include group is half-configured"
REPORT_ROW_LABEL = "include group"

GROUP_TOML = (
    "[pack]\n"
    f'include_group = "{GROUP_NAME}"\n'
    'include_group_triggers = ["bin", "tests"]\n'
    'include_group_pulls = ["install.sh", "docs"]\n'
)


class IncludeGroupBase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-incgroup-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        # A tree with trigger areas (bin/, tests/), pull targets
        # (install.sh, docs/), and a bystander (lib/) that touches no
        # trigger. All tracked, so the pack walk sees them.
        for rel in ("bin/tool.py", "tests/test_tool.py",
                    "install.sh", "docs/GUIDE.md", "lib/other.txt"):
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(f"{rel}\n", encoding="utf-8")
        run_checked(["git", "add", "-A"], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "fixture tree"],
                    cwd=self.repo, env=self.genv)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def write_config(self, body: str = GROUP_TOML) -> None:
        (self.repo / "bale.toml").write_text(body, encoding="utf-8")
        run_checked(["git", "add", "bale.toml"], cwd=self.repo,
                    env=self.genv)
        run_checked(["git", "commit", "-m", "config"], cwd=self.repo,
                    env=self.genv)

    def pack(self, *extra: str, slug: str = "session-a"):
        """A fully specified piped pack; extras append to the base form."""
        return run_bale(
            self.install,
            ["pack", "pull-group surface test goal",
             "--slug", slug, "--no-readme", *extra],
            cwd=self.repo, env=self.env,
        )

    def latest_manifest_and_names(self, slug: str = "session-a"):
        """Read the packed request's manifest + tar member names."""
        outbox = self.repo / ".bale" / "outbox"
        tarballs = sorted(outbox.glob(f"request-*-{slug}-*.tar.gz"))
        self.assertTrue(tarballs, f"no request tarball for slug {slug!r} "
                                  f"in {outbox}")
        with tarfile.open(tarballs[-1], "r:gz") as tf:
            names = tf.getnames()
            manifest_member = next(
                n for n in names if n.endswith("/manifest.json"))
            manifest = json.load(tf.extractfile(manifest_member))
        return manifest, names

    def assert_pack_ok(self, r) -> None:
        self.assertEqual(
            r.returncode, 0,
            f"pack failed\nstdout:\n{r.stdout}\nstderr:\n{r.stderr}")


class TestEngagement(IncludeGroupBase):
    def test_trigger_include_pulls_group_into_context(self) -> None:
        """An include under a trigger ships the pulls, loudly."""
        self.write_config()
        r = self.pack("--include", "bin/tool.py")
        self.assert_pack_ok(r)
        self.assertIn(ENGAGED_MARKER, r.stdout)
        self.assertIn(PULLED_MARKER, r.stdout)
        # The durable report row rides the summary block.
        self.assertIn(REPORT_ROW_LABEL, r.stdout)
        manifest, names = self.latest_manifest_and_names()
        ctx = manifest["context_included"]
        for pulled in ("context/install.sh", "context/docs/GUIDE.md"):
            self.assertIn(pulled, ctx)
            self.assertTrue(
                any(n.endswith(pulled) for n in names),
                f"{pulled} not in tarball members")
        # The bystander was not swept in.
        self.assertNotIn("context/lib/other.txt", ctx)

    def test_engagement_is_read_side_only(self) -> None:
        """resolved_scope stays on the user's includes, not the pulls."""
        self.write_config()
        r = self.pack("--include", "bin/tool.py")
        self.assert_pack_ok(r)
        manifest, _ = self.latest_manifest_and_names()
        self.assertEqual(manifest["resolved_scope"], ["bin/tool.py"])
        # The registry records the same forecast (one source).
        scope_files = list(
            (self.repo / ".bale" / "sessions").glob("*/scope.json"))
        self.assertTrue(scope_files)
        recorded = json.loads(
            scope_files[0].read_text(encoding="utf-8"))
        scope_value = (recorded.get("scope")
                       if isinstance(recorded, dict) else recorded)
        self.assertEqual(scope_value, ["bin/tool.py"])

    def test_sibling_pack_alongside_pulled_paths(self) -> None:
        """The thesis: pulls never lock. A second pack forecasting a
        pulled path is admitted alongside the engaged session."""
        self.write_config()
        r = self.pack("--include", "bin/tool.py")
        self.assert_pack_ok(r)
        # Sibling forecasts docs/ — shipped by session A's group pull,
        # but never in A's forecast, so the disjointness gate admits it.
        r2 = self.pack("--include", "docs", "--write", "docs",
                       slug="session-b")
        self.assert_pack_ok(r2)

    def test_no_trigger_no_engagement(self) -> None:
        """Includes touching no trigger add nothing and say nothing."""
        self.write_config()
        r = self.pack("--include", "lib/other.txt")
        self.assert_pack_ok(r)
        self.assertNotIn(ENGAGED_MARKER, r.stdout)
        self.assertNotIn(OPTOUT_MARKER, r.stdout)
        manifest, _ = self.latest_manifest_and_names()
        self.assertNotIn("context/install.sh",
                         manifest["context_included"])

    def test_whole_tree_default_engages_already_covered(self) -> None:
        """The default include (.) covers every trigger AND every pull:
        engagement logs, adds nothing, and the walk stays whole-tree."""
        self.write_config()
        r = self.pack()
        self.assert_pack_ok(r)
        self.assertIn(ENGAGED_MARKER, r.stdout)
        self.assertIn(COVERED_MARKER, r.stdout)
        manifest, _ = self.latest_manifest_and_names()
        # Whole-tree pack ships the pulls anyway, via the default walk.
        self.assertIn("context/install.sh", manifest["context_included"])

    def test_unconfigured_group_changes_nothing(self) -> None:
        """No [pack] config — the pre-group behavior, byte-silent."""
        r = self.pack("--include", "bin/tool.py")
        self.assert_pack_ok(r)
        self.assertNotIn("include group", r.stdout)
        manifest, _ = self.latest_manifest_and_names()
        self.assertNotIn("context/install.sh",
                         manifest["context_included"])


class TestOptOut(IncludeGroupBase):
    def test_opt_out_skips_pull_loudly(self) -> None:
        self.write_config()
        r = self.pack("--include", "bin/tool.py",
                      "--no-include-group", GROUP_NAME)
        self.assert_pack_ok(r)
        self.assertIn(OPTOUT_MARKER, r.stdout)
        # FORCE-prefixed: the opt-out is an audit-trail override event.
        self.assertIn("FORCE:", r.stdout)
        self.assertIn(REPORT_ROW_LABEL, r.stdout)
        manifest, _ = self.latest_manifest_and_names()
        self.assertNotIn("context/install.sh",
                         manifest["context_included"])

    def test_opt_out_wrong_name_refuses(self) -> None:
        self.write_config()
        r = self.pack("--include", "bin/tool.py",
                      "--no-include-group", "release-surfaec")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(OPTOUT_MISMATCH_MARKER, r.stderr)
        self.assertFalse(
            list((self.repo / ".bale" / "outbox").glob("*.tar.gz"))
            if (self.repo / ".bale" / "outbox").exists() else [],
            "a refused pack must ship no tarball")

    def test_opt_out_without_configured_group_refuses(self) -> None:
        r = self.pack("--include", "bin/tool.py",
                      "--no-include-group", GROUP_NAME)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(OPTOUT_UNCONFIGURED_MARKER, r.stderr)


class TestConfigCoherence(IncludeGroupBase):
    def test_dangling_pull_refuses_on_engagement(self) -> None:
        self.write_config(
            "[pack]\n"
            f'include_group = "{GROUP_NAME}"\n'
            'include_group_triggers = ["bin"]\n'
            'include_group_pulls = ["missing-file.sh"]\n'
        )
        r = self.pack("--include", "bin/tool.py")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(DANGLING_PULL_MARKER, r.stderr)
        # And the refusal names the escape hatch by flag.
        self.assertIn("--no-include-group", r.stderr)

    def test_dangling_pull_dormant_when_not_engaged(self) -> None:
        """Config rot surfaces at engagement, not on unrelated packs —
        the same at-use posture as a configured hook script."""
        self.write_config(
            "[pack]\n"
            f'include_group = "{GROUP_NAME}"\n'
            'include_group_triggers = ["bin"]\n'
            'include_group_pulls = ["missing-file.sh"]\n'
        )
        r = self.pack("--include", "lib/other.txt")
        self.assert_pack_ok(r)

    def test_half_configured_group_refuses(self) -> None:
        self.write_config(
            "[pack]\n"
            f'include_group = "{GROUP_NAME}"\n'
        )
        r = self.pack("--include", "lib/other.txt")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(HALF_CONFIGURED_MARKER, r.stderr)


if __name__ == "__main__":
    unittest.main()
