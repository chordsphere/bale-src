#!/usr/bin/env python3
"""Hermetic tests for scripts/build.sh's packaging pre-flights.

Covers the two packaging deliverables of the stats closeout session:

- **Release-list coverage of ``bin/bale_stats.py``** — the eighth
  sibling was the first new top-level ``bin/`` file since the packaging
  lists were introduced, and the reinstall hook's tree-coverage guard
  refused on it. Pure list checks here read the REAL checkout's
  ``scripts/build.sh`` and ``install.sh`` (extraction per the format
  contract documented above ``RELEASE_FILES``) and pin that the file is
  in both lists and that the two lists are set-equal.

- **The version-tag drift guard** — the release-time check that refuses
  when the highest v-prefixed version tag referenced across the release
  surface exceeds the canonical version in ``bin/VERSION`` (the
  session-005 drift class; the constant moved out of ``bin/bale`` in
  v0.4.5, board 10 S2). Exercised E2E by driving the REAL
  ``scripts/build.sh`` over a SYNTHETIC minimal tree: every
  ``RELEASE_FILES`` entry is synthesized with just enough content to
  clear the earlier pre-flights (the version line in the dummy
  ``bin/VERSION``, a generated ``INSTALL_LAYOUT`` in the dummy
  ``install.sh``, parseable dummies for ``.py``/``.json``/``.sh``), so
  each test controls exactly which version tags the scrape sees. The
  build under test is the real script; only the tree it packages is
  synthetic.

- **Release-list coverage of ``bin/VERSION``** — the extracted version
  file (v0.4.5) is release-critical the same way the eighth sibling
  was: ``bin/bale`` reads it at startup, so a release without it is
  dead on arrival. Pinned in both lists beside the ``bale_stats``
  rows.

Sandbox doctrine per ADR-0005: every write lands under a per-test
``TemporaryDirectory`` — ``TMPDIR`` is pointed into it so build.sh's
``mktemp`` staging does too — and nothing reads or writes the real
install. The harness's bale-invoking helpers don't apply here (no bale
run, no git repo); the temp-everything discipline is the same.

Run directly::

    python3 tests/test_release_packaging.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import os
import subprocess
import tarfile
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BUILD_SH = REPO_ROOT / "scripts" / "build.sh"
INSTALL_SH = REPO_ROOT / "install.sh"

SUBPROCESS_TIMEOUT = 120  # seconds; generous — each build run is seconds.

# The synthetic trees' VERSION constant. High enough that any stray tag
# in the real files copied nowhere (none are) can't interfere, and with
# headroom below the drift tags the tests inject.
SANDBOX_VERSION = "9.8.0"
BENIGN_TAG = "v9.8.0"   # equal to the constant — the boundary that passes
DRIFT_TAG = "v9.9.9"    # above the constant — the boundary that dies


def extract_bash_array(path: Path, name: str) -> list[str]:
    """Extract a bash array per build.sh's documented format contract.

    ``<NAME>=(`` at column 0, one bare path per line (trailing comments
    tolerated), ``)`` at column 0. Mirrors the awk extraction build.sh
    and reinstall.sh use, so a format change breaks this test the same
    way it breaks them — loudly.
    """
    out: list[str] = []
    inblock = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not inblock and line == f"{name}=(":
            inblock = True
            continue
        if inblock and line == ")":
            return out
        if inblock:
            bare = line.split("#", 1)[0].strip()
            if bare:
                out.append(bare)
    raise AssertionError(
        f"array {name} missing or unterminated in {path} — format "
        f"contract changed?"
    )


def make_release_tree(tmp: Path, *, version: str = SANDBOX_VERSION) -> Path:
    """Synthesize a minimal tree that clears every pre-flight before the
    drift guard, driven by the REAL build.sh's own RELEASE_FILES.

    The real ``scripts/build.sh`` is copied in as the script under test;
    every file it expects is written with the least content that passes
    the source-layout, list-agreement, subset, tree-coverage, and syntax
    pre-flights. No version tags are injected here — callers add the
    tags each test needs, so the scrape's input is fully controlled
    (including the empty-scrape case).
    """
    repo = tmp / "repo"
    (repo / "scripts").mkdir(parents=True)
    build_copy = repo / "scripts" / "build.sh"
    build_copy.write_bytes(BUILD_SH.read_bytes())
    build_copy.chmod(0o755)

    release_files = extract_bash_array(build_copy, "RELEASE_FILES")
    layout_block = "\n".join(f"  {f}" for f in release_files)

    for rel in release_files:
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        if rel == "bin/VERSION":
            # The canonical one-line version file the guard reads
            # (v0.4.5 — extracted from bin/bale's old constant).
            p.write_text(f"{version}\n", encoding="utf-8")
        elif rel == "bin/bale":
            # Python-parseable stub; the real bin/bale reads
            # bin/VERSION at startup, and the guard no longer scrapes
            # this file — only the syntax pre-flight touches it here.
            p.write_text("# synthetic bin/bale (packaging tests)\n",
                         encoding="utf-8")
        elif rel == "install.sh":
            # bash -n clean, INSTALL_LAYOUT generated to match exactly.
            p.write_text(
                "#!/usr/bin/env bash\n"
                "INSTALL_LAYOUT=(\n"
                f"{layout_block}\n"
                ")\n",
                encoding="utf-8",
            )
        elif rel == "upgrade.sh":
            # A deliberate one-member subset, per the real contract.
            p.write_text(
                "#!/usr/bin/env bash\n"
                "REQUIRED_RELEASE_MEMBERS=(\n"
                "  bin/bale\n"
                ")\n",
                encoding="utf-8",
            )
        elif rel.endswith(".json"):
            p.write_text("{}\n", encoding="utf-8")
        elif rel.endswith(".py"):
            p.write_text("", encoding="utf-8")
        elif rel.endswith(".sh"):
            p.write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
        else:
            p.write_text("stub\n", encoding="utf-8")
    return repo


def run_build(tmp: Path, repo: Path, *args: str) -> subprocess.CompletedProcess:
    """Run the sandbox tree's build.sh with all writes confined to tmp."""
    out = tmp / "dist"
    scratch = tmp / "tmp"
    scratch.mkdir(exist_ok=True)
    env = dict(os.environ, TMPDIR=str(scratch))
    return subprocess.run(
        ["bash", str(repo / "scripts" / "build.sh"), "-o", str(out), *args],
        capture_output=True,
        text=True,
        env=env,
        timeout=SUBPROCESS_TIMEOUT,
    )


class ReleaseListCoverageTest(unittest.TestCase):
    """The real checkout's lists cover the eighth sibling and agree."""

    def test_release_files_covers_bale_stats(self) -> None:
        self.assertIn("bin/bale_stats.py", extract_bash_array(BUILD_SH, "RELEASE_FILES"))

    def test_install_layout_covers_bale_stats(self) -> None:
        self.assertIn("bin/bale_stats.py", extract_bash_array(INSTALL_SH, "INSTALL_LAYOUT"))

    def test_release_files_covers_bin_version(self) -> None:
        """The extracted version file (v0.4.5) ships: bin/bale reads it
        at startup, so a release without it is dead on arrival."""
        self.assertIn("bin/VERSION", extract_bash_array(BUILD_SH, "RELEASE_FILES"))

    def test_install_layout_covers_bin_version(self) -> None:
        self.assertIn("bin/VERSION", extract_bash_array(INSTALL_SH, "INSTALL_LAYOUT"))

    def test_release_files_covers_planner_doc(self) -> None:
        """docs/PLANNER.md joined the injected set in v0.4.11: a release
        without it fails main()'s missing-docs pre-check on every pack
        and handoff, and the tree-coverage guard dies at build time —
        so its row in the list is load-bearing, not decorative."""
        self.assertIn("docs/PLANNER.md",
                      extract_bash_array(BUILD_SH, "RELEASE_FILES"))

    def test_install_layout_covers_planner_doc(self) -> None:
        self.assertIn("docs/PLANNER.md",
                      extract_bash_array(INSTALL_SH, "INSTALL_LAYOUT"))

    def test_lists_are_set_equal(self) -> None:
        release = extract_bash_array(BUILD_SH, "RELEASE_FILES")
        layout = extract_bash_array(INSTALL_SH, "INSTALL_LAYOUT")
        self.assertEqual(sorted(release), sorted(layout))
        # Duplicate entries would make set-equality lie; pin both clean.
        self.assertEqual(len(release), len(set(release)))
        self.assertEqual(len(layout), len(set(layout)))


class VersionTagDriftGuardTest(unittest.TestCase):
    """E2E drives of the real build.sh over synthetic trees."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-relpkg-")
        self.tmp = Path(self._tmpdir.name)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_build_passes_when_highest_tag_equals_constant(self) -> None:
        """The equal boundary passes, and the release ships bale_stats."""
        repo = make_release_tree(self.tmp)
        docs = repo / "docs" / "CLAUDE.md"
        docs.write_text(f"stub\n<!-- landed in {BENIGN_TAG} -->\n", encoding="utf-8")
        result = run_build(self.tmp, repo)
        self.assertEqual(
            result.returncode, 0,
            f"clean tree should build\nstdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}",
        )
        self.assertIn(f"highest referenced tag {BENIGN_TAG}", result.stdout)
        tarball = self.tmp / "dist" / f"bale-v{SANDBOX_VERSION}.tar.gz"
        self.assertTrue(tarball.is_file(), "expected release tarball")
        with tarfile.open(tarball) as tf:
            self.assertIn("bale/bin/bale_stats.py", tf.getnames())

    def test_build_dies_on_tag_above_constant(self) -> None:
        """The session-005 drift class is a failed build, loudly named."""
        repo = make_release_tree(self.tmp)
        offender = repo / "docs" / "DOCS.md"
        offender.write_text(f"stub\nratified in {DRIFT_TAG}\n", encoding="utf-8")
        result = run_build(self.tmp, repo)
        self.assertNotEqual(result.returncode, 0, "drifted tree must not build")
        self.assertIn("version-tag drift", result.stderr)
        self.assertIn(DRIFT_TAG, result.stderr)
        self.assertIn("docs/DOCS.md", result.stderr)

    def test_guard_keys_on_constant_not_on_override(self) -> None:
        """--version must neither mask nor trip the guard: the drift is
        tree-vs-constant, so a drifted tree dies under any override."""
        repo = make_release_tree(self.tmp)
        (repo / "docs" / "DOCS.md").write_text(
            f"stub\n{DRIFT_TAG}\n", encoding="utf-8"
        )
        result = run_build(self.tmp, repo, "--version", "1.2.3")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("version-tag drift", result.stderr)
        self.assertIn(f"bin/VERSION ({SANDBOX_VERSION})", result.stderr)

    def test_empty_scrape_is_fatal(self) -> None:
        """Zero scraped tags is a broken scrape, not a clean tree."""
        repo = make_release_tree(self.tmp)  # no tags injected anywhere
        result = run_build(self.tmp, repo)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("scraped zero", result.stderr)


if __name__ == "__main__":
    unittest.main()
