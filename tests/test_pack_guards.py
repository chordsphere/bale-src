#!/usr/bin/env python3
"""Hermetic E2E for the pack guard rails (BALE.md §7.4, §6.4).

Board-35 gap 3 — the last ranked audit item: "Pack §7.4 caps /
`--exclude` / `.baleignore` / `--force`." Four families are pinned:

- **The `--max-*` cap family** (`--max-files`, `--max-size`,
  `--max-depth`): each refuses an oversized pack with its named
  threshold, refusal happens pre-sid (no session, no tarball), and the
  at-cap boundary passes — the caps are inclusive ("N files under a
  cap of N is fine; the N+1st trips it", and the depth docstring's "a
  cap of 20 means files up to 20 directories deep are allowed").
  Flag-value validation (`--max-files 0`, a malformed `--max-size`,
  a negative `--max-depth`) refuses at input validation, before any
  walk.
- **`--force`**: the same oversized pack proceeds under the override,
  with the FORCE audit line naming every bypassed breach; it clears
  the piped soft-breach refusal the same way.
- **`--exclude` / `.baleignore`**: patterns prune paths an
  `--include` would otherwise pull in — asserted from the packed
  tarball's actual context/ members and the shipped manifest's
  context_included, never from the pack report alone. The two sources
  compose as a union (build_pack_matcher feeds file lines + session
  patterns through one matcher), `.baleignore` itself always ships in
  context/, negation patterns refuse, and excluding everything
  refuses with the widen-your-include message.
- **The soft-breach [y]/[e]/[n] prompt**: driven through a real pty
  (the prompt engages only on a TTY). [n] and bare Enter abort
  pre-sid; unrecognized input re-prompts; [e] collects session-only
  patterns and re-walks (additively — an empty collection re-prompts
  instead of re-walking); [y] proceeds at the breached scope. Piped
  mode never reaches the prompt: a soft breach without a TTY refuses
  outright (v0.2.4).

Controlled tree sizes: the soft caps are deliberately not user-tunable
(PackCaps docstring), so the soft-size breach is crossed with a sparse
file one byte past PACK_MAX_SIZE_SOFT — st_size is what the walk
projects, so the file costs no real disk or generation time. Hard-cap
tests use the tunable `--max-*` flags against tiny trees, so no test
generates more than a handful of files. The two tests where pack
*proceeds* past the soft breach ([y], and --force over the soft
refusal) do copy the sparse file into context/ (~1.5s each measured);
everything else aborts or re-walks before any copy.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring. The prompt
tests drive bale through a real pseudo-terminal via ``run_bale_pty``
(stubbing isatty would test a fiction — the piped-refusal branch under
test is exactly the isatty split).

Run directly::

    python3 tests/test_pack_guards.py

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
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_bale_pty,
)

# The soft size cap, mirrored from bin/bale_pack.py's
# PACK_MAX_SIZE_SOFT (100 MB, 1024-based). Mirrored rather than
# imported: the suite drives the shipped bale as a subprocess by
# absolute path (harness doctrine) and never imports its modules; if
# the constant moves, the sparse file stops breaching and the prompt
# assertions below fail loudly on the missing marker.
SOFT_SIZE_CAP = 100 * 1024 * 1024

# Sentinels for the surfaces this file pins. Kept in one place so a
# message rewording breaks one line, not several assertions.
HARD_BREACH_MARKER = "hard threshold breach"
SOFT_BREACH_MARKER = "Soft threshold breach"
PROJECTION_MARKER = "This pack would include:"
PIPED_SOFT_REFUSAL_MARKER = "stdin is not a TTY, so the [y]/[e]/[n] prompt"
PROMPT_ABORT_MARKER = "aborted at threshold prompt"
PROMPT_UNRECOGNIZED_MARKER = "didn't recognize"
PROMPT_EMPTY_ADDITIONS_MARKER = "no patterns added"
FORCE_BYPASS_MARKER = "bypassing threshold breach"
NO_FILES_MARKER = "no files would be included after exclusions"
INVALID_EXCLUDE_MARKER = "invalid session exclude pattern"


class PackGuardsBase(unittest.TestCase):
    """Shared sandbox plumbing for the guard-rail suites below."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-guards-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixture helpers -------------------------------------------------

    def write_payload(self, files: dict) -> None:
        """Write repo-relative files (str content or bytes). Untracked is
        enough: the walk enumerates via `git ls-files --cached --others
        --exclude-standard`, which picks up untracked-not-ignored files."""
        for rel, content in files.items():
            p = self.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                p.write_bytes(content)
            else:
                p.write_text(content, encoding="utf-8")

    def write_soft_breach_payload(self) -> None:
        """A payload/ dir whose total st_size crosses the soft size cap:
        one sparse file a single byte past it (just past the threshold,
        not orders beyond) plus one small survivor for the [e] re-walk
        assertions."""
        d = self.repo / "payload"
        d.mkdir()
        with open(d / "big.bin", "wb") as f:
            f.seek(SOFT_SIZE_CAP)  # st_size becomes SOFT_SIZE_CAP + 1
            f.write(b"\0")
        (d / "small.txt").write_text("survivor\n", encoding="utf-8")

    # -- pack invocations ------------------------------------------------

    def pack(self, *extra: str, slug: str = "guards"):
        """A fully specified piped pack over payload/; extras append."""
        return run_bale(
            self.install,
            [
                "pack", "pack guard rails test goal",
                "--slug", slug,
                "--include", "payload",
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
        )

    def pack_pty(self, answers: str, *extra: str, slug: str = "guards"):
        """The same pack driven through a pty, feeding prompt answers.
        Goal and --slug are fully specified, so the wizard never engages
        and the soft-breach [y]/[e]/[n] prompt is the only exchange."""
        return run_bale_pty(
            self.install,
            [
                "pack", "pack guard rails test goal",
                "--slug", slug,
                "--include", "payload",
                "--no-readme",
                *extra,
            ],
            cwd=self.repo,
            env=self.env,
            answers=answers,
        )

    # -- state assertions ------------------------------------------------

    def open_sids(self) -> list:
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return []
        return sorted(d.name for d in root.iterdir()
                      if (d / "open").is_file())

    def outbox_tarballs(self) -> list:
        outbox = self.repo / ".bale" / "outbox"
        if not outbox.is_dir():
            return []
        return sorted(outbox.iterdir())

    def assert_refused_pre_sid(self, combined_output: str) -> None:
        """A cap refusal (or prompt abort) happens before sid allocation:
        no session opened, no request tarball written."""
        self.assertEqual(
            self.open_sids(), [],
            msg=f"refusal opened a session anyway; output:\n{combined_output}",
        )
        self.assertEqual(
            self.outbox_tarballs(), [],
            msg=f"refusal wrote a tarball anyway; output:\n{combined_output}",
        )

    def shipped_context(self):
        """(context_included, tarball member names) from the single
        outbox request tarball — the packed artifact itself, not the
        pack report."""
        tarballs = self.outbox_tarballs()
        self.assertEqual(
            len(tarballs), 1,
            msg=f"expected exactly one request tarball, got {tarballs}",
        )
        with tarfile.open(tarballs[0]) as tf:
            names = tf.getnames()
            manifest_member = [
                n for n in names
                if n.endswith("/manifest.json") and "/context/" not in n
            ]
            self.assertEqual(len(manifest_member), 1, msg=str(names))
            manifest = json.load(tf.extractfile(manifest_member[0]))
        return manifest["context_included"], names


class HardCapTest(PackGuardsBase):
    """The --max-* family: refusal past each cap, pass at each cap,
    flag-value validation. Caps are lowered via the flags so the
    controlled trees stay tiny (the flags override only the hard caps;
    walk_for_pack short-circuits at the first hard breach)."""

    def test_max_files_refuses_past_cap(self) -> None:
        """Three files under --max-files 2: refusal names the count and
        the cap, shows the projection block, and leaves no session."""
        self.write_payload({f"payload/f{i}.txt": "x\n" for i in range(3)})
        r = self.pack("--max-files", "2")
        self.assertNotEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn(HARD_BREACH_MARKER, r.stderr)
        self.assertIn("file count 3 exceeds hard cap 2", r.stderr)
        self.assertIn(PROJECTION_MARKER, r.stderr)
        self.assert_refused_pre_sid(r.stderr)

    def test_max_files_at_cap_passes(self) -> None:
        """The cap is inclusive: exactly N files under --max-files N packs."""
        self.write_payload({f"payload/f{i}.txt": "x\n" for i in range(2)})
        r = self.pack("--max-files", "2")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        included, _ = self.shipped_context()
        self.assertEqual(
            included, ["context/payload/f0.txt", "context/payload/f1.txt"])

    def test_max_size_refuses_past_cap(self) -> None:
        """A 2049-byte file under --max-size 2K (1024-based, so 2048)
        refuses naming the size cap; the K-suffix parse is exercised on
        the way."""
        self.write_payload({"payload/blob.bin": b"\0" * 2049})
        r = self.pack("--max-size", "2K")
        self.assertNotEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn(HARD_BREACH_MARKER, r.stderr)
        self.assertIn("total size", r.stderr)
        self.assert_refused_pre_sid(r.stderr)

    def test_max_size_at_cap_passes(self) -> None:
        """total_bytes > cap is strict: exactly 2048 bytes under 2K packs."""
        self.write_payload({"payload/blob.bin": b"\0" * 2048})
        r = self.pack("--max-size", "2K")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")

    def test_max_depth_refuses_past_cap_naming_path(self) -> None:
        """Depth is directory levels above the file; the refusal names the
        offending path (walk_for_pack's depth-breach message)."""
        self.write_payload({"payload/a/b/c/f.txt": "x\n"})  # depth 4
        r = self.pack("--max-depth", "3")
        self.assertNotEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn(HARD_BREACH_MARKER, r.stderr)
        self.assertIn("path depth 4 exceeds hard cap 3", r.stderr)
        self.assertIn("payload/a/b/c/f.txt", r.stderr)
        self.assert_refused_pre_sid(r.stderr)

    def test_max_depth_at_cap_passes(self) -> None:
        """'A cap of N means files up to N directories deep are allowed'."""
        self.write_payload({"payload/a/b/f.txt": "x\n"})  # depth 3
        r = self.pack("--max-depth", "3")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")

    def test_cap_flag_values_are_validated(self) -> None:
        """Malformed cap values refuse at input validation, pre-walk:
        --max-files < 1, a size with an unknown suffix, --max-depth < 0."""
        self.write_payload({"payload/f.txt": "x\n"})
        r = self.pack("--max-files", "0")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--max-files must be >= 1", r.stderr)
        r = self.pack("--max-size", "12Q")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("invalid size value", r.stderr)
        r = self.pack("--max-depth", "-1")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("--max-depth must be >= 0", r.stderr)
        self.assert_refused_pre_sid(r.stderr)


class ForceOverrideTest(PackGuardsBase):
    """--force: the same oversized pack proceeds, with the FORCE audit
    line naming what was bypassed."""

    def test_force_bypasses_hard_cap(self) -> None:
        """The pack that test_max_files_refuses_past_cap refuses
        proceeds under --force; the audit line names the bypassed breach
        and the full file set ships."""
        self.write_payload({f"payload/f{i}.txt": "x\n" for i in range(3)})
        r = self.pack("--max-files", "2", "--force")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        combined = r.stdout + r.stderr
        self.assertIn(FORCE_BYPASS_MARKER, combined)
        self.assertIn("file count 3 exceeds hard cap 2", combined)
        self.assertEqual(len(self.open_sids()), 1)
        included, _ = self.shipped_context()
        self.assertEqual(included, [
            "context/payload/f0.txt",
            "context/payload/f1.txt",
            "context/payload/f2.txt",
        ])

    def test_force_bypasses_piped_soft_breach(self) -> None:
        """The piped soft-breach refusal names --force as the escape
        hatch; this pins that the hatch works — the breached scope packs,
        logged as a FORCE event. (Copies the sparse file: ~1.5s.)"""
        self.write_soft_breach_payload()
        r = self.pack("--force")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        combined = r.stdout + r.stderr
        self.assertIn(FORCE_BYPASS_MARKER, combined)
        self.assertIn("soft cap", combined)
        included, _ = self.shipped_context()
        self.assertIn("context/payload/big.bin", included)


class ExcludeAndBaleignoreTest(PackGuardsBase):
    """--exclude and .baleignore: pruning asserted from the packed
    tarball's context/ members and context_included, and the two
    sources' composition (a union — build_pack_matcher feeds file lines
    and session patterns through one matcher)."""

    def test_exclude_prunes_included_paths(self) -> None:
        self.write_payload({
            "payload/keep.py": "print()\n",
            "payload/drop.csv": "a,b\n",
        })
        r = self.pack("--exclude", "*.csv")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        included, members = self.shipped_context()
        self.assertEqual(included, ["context/payload/keep.py"])
        self.assertFalse(
            any(m.endswith("payload/drop.csv") for m in members),
            msg=f"excluded file shipped anyway: {members}",
        )

    def test_baleignore_prunes_and_ships_itself(self) -> None:
        """.baleignore patterns filter the walk, and the file itself is
        force-included in context/ so the worker can see what filtered
        its view."""
        self.write_payload({
            "payload/keep.py": "print()\n",
            "payload/drop.log": "log\n",
        })
        (self.repo / ".baleignore").write_text("*.log\n", encoding="utf-8")
        r = self.pack()
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        included, members = self.shipped_context()
        self.assertEqual(
            included, ["context/.baleignore", "context/payload/keep.py"])
        self.assertFalse(
            any(m.endswith("payload/drop.log") for m in members))

    def test_baleignore_composes_with_exclude_as_union(self) -> None:
        """A path matched by either source is dropped; the survivor set
        is the include set minus the union."""
        self.write_payload({
            "payload/keep.py": "print()\n",
            "payload/a.log": "x\n",     # dropped by .baleignore
            "payload/b.tmp": "x\n",     # dropped by --exclude
        })
        (self.repo / ".baleignore").write_text("*.log\n", encoding="utf-8")
        r = self.pack("--exclude", "*.tmp")
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        included, members = self.shipped_context()
        self.assertEqual(
            included, ["context/.baleignore", "context/payload/keep.py"])
        for dropped in ("payload/a.log", "payload/b.tmp"):
            self.assertFalse(any(m.endswith(dropped) for m in members),
                             msg=f"{dropped} shipped despite a filter")

    def test_exclude_negation_pattern_refuses(self) -> None:
        """Session patterns ride the .baleignore parser; leading '!' is
        the unsupported negation and refuses with the pattern named."""
        self.write_payload({"payload/f.txt": "x\n"})
        r = self.pack("--exclude", "!keep")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(INVALID_EXCLUDE_MARKER, r.stderr)
        self.assertIn("!keep", r.stderr)
        self.assert_refused_pre_sid(r.stderr)

    def test_excluding_everything_refuses(self) -> None:
        """An empty surviving set is a refusal, not an empty pack."""
        self.write_payload({"payload/f.txt": "x\n"})
        r = self.pack("--exclude", "payload/")
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(NO_FILES_MARKER, r.stderr)
        self.assert_refused_pre_sid(r.stderr)


class SoftBreachPromptTest(PackGuardsBase):
    """The §7.4 soft-cap [y]/[e]/[n] prompt, driven through a real pty,
    plus the piped-mode refusal that replaces it. Every case crosses
    the soft size cap with the sparse-file payload."""

    def setUp(self) -> None:
        super().setUp()
        self.write_soft_breach_payload()

    def test_piped_soft_breach_refuses(self) -> None:
        """No TTY, no prompt: a soft breach refuses outright (v0.2.4)
        rather than warn-and-proceed, and points at --exclude /
        .baleignore / --force."""
        r = self.pack()
        self.assertNotEqual(r.returncode, 0, msg=r.stdout)
        self.assertIn(SOFT_BREACH_MARKER, r.stderr)
        self.assertIn(PIPED_SOFT_REFUSAL_MARKER, r.stderr)
        self.assert_refused_pre_sid(r.stderr)

    def test_prompt_n_aborts(self) -> None:
        """[n] aborts pre-sid; the projection block and breach line were
        shown first so the abort is an informed one."""
        code, out = self.pack_pty("n\n")
        self.assertNotEqual(code, 0, msg=out)
        self.assertIn(PROJECTION_MARKER, out)
        self.assertIn(SOFT_BREACH_MARKER, out)
        self.assertIn(PROMPT_ABORT_MARKER, out)
        self.assert_refused_pre_sid(out)

    def test_prompt_rejects_unknown_input_and_defaults_to_abort(self) -> None:
        """Unrecognized input re-prompts rather than mis-routing; bare
        Enter then takes the safe default, abort."""
        code, out = self.pack_pty("x\n\n")
        self.assertNotEqual(code, 0, msg=out)
        self.assertIn(PROMPT_UNRECOGNIZED_MARKER, out)
        self.assertIn(PROMPT_ABORT_MARKER, out)
        self.assert_refused_pre_sid(out)

    def test_prompt_e_adds_patterns_and_rewalks(self) -> None:
        """[e] collects session-only patterns and re-walks with them
        applied: excluding the oversized file clears the breach and the
        pack proceeds without it."""
        code, out = self.pack_pty("e\n*.bin\n\n")
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(len(self.open_sids()), 1)
        included, members = self.shipped_context()
        self.assertEqual(included, ["context/payload/small.txt"])
        self.assertFalse(any(m.endswith("payload/big.bin") for m in members))

    def test_prompt_e_with_no_patterns_reprompts(self) -> None:
        """[e] with an immediately blank collection re-prompts instead of
        re-walking an identical scope; [n] then aborts."""
        code, out = self.pack_pty("e\n\nn\n")
        self.assertNotEqual(code, 0, msg=out)
        self.assertIn(PROMPT_EMPTY_ADDITIONS_MARKER, out)
        self.assertIn(PROMPT_ABORT_MARKER, out)
        self.assert_refused_pre_sid(out)

    def test_prompt_y_proceeds_at_breached_scope(self) -> None:
        """[y] continues with the pack as walked — the oversized file
        ships. (Copies the sparse file: ~1.5s.)"""
        code, out = self.pack_pty("y\n")
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(len(self.open_sids()), 1)
        included, _ = self.shipped_context()
        self.assertIn("context/payload/big.bin", included)
        self.assertIn("context/payload/small.txt", included)


if __name__ == "__main__":
    unittest.main()
