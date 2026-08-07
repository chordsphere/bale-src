#!/usr/bin/env python3
"""Real-operations apply.sh suite (board 35 gap 2).

Drives the operations the ``files/`` cp-mirror cannot express — the
TARBALL.md §5.1.1 surface — through a full ``bale pack`` → ``bale
apply`` → merge, and asserts each one really landed on the target
branch:

- **delete** — a ``deleted`` manifest entry whose removal apply.sh
  performs with ``rm``;
- **the removal half of a rename** — a ``created`` entry for the new
  path under ``files/`` plus an ``rm`` of the old path (apply.sh never
  runs ``mv``; the commit step is driven per-manifest-entry);
- **exec-bit restore** — the overlay strips mode, so apply.sh's
  per-path ``chmod +x`` is what makes a shipped script executable, and
  the TARBALL.md §7.7 assertion in validation.sh is what turns a
  forgotten chmod into a ``[FAIL]``. Both halves are pinned: the
  restore landing (git mode 100755 on the merged tree) and the
  assertion catching the forgotten-chmod case with a HOLD.

Fixtures extend the shared harness response builder past the no-op —
custom ``apply.sh`` and ``validation.sh`` bodies over computed-hash
manifests (TARBALL.md §5.2.1). The ADR-0002 posture holds: the oracle
is the documented apply contract (merged tree state, git file mode,
walkthrough headline), never a golden byte comparison.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_apply_operations.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

from harness import (
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

PASS_HEADLINE = "[PASS]"
HOLD_HEADLINE = "[HOLD]"

RUN_SH_BODY = b"#!/usr/bin/env bash\necho ran\n"
EXEC_CHECK = "exec bit: data/run.sh"

# The §7.7 assertion pattern: test the repo-relative path in staging
# (never the files/ copy, whose mode was already stripped), one labeled
# [PASS]/[FAIL] line, exit reflecting the verdict.
EXEC_ASSERT_VALIDATION_SH = (
    "#!/usr/bin/env bash\n"
    "# TARBALL.md section 7.7: assert the exec bit apply.sh restored.\n"
    "if [ -x data/run.sh ]; then\n"
    f"  echo \"[PASS] {EXEC_CHECK}\"\n"
    "else\n"
    f"  echo \"[FAIL] {EXEC_CHECK}\"\n"
    "  exit 1\n"
    "fi\n"
    "exit 0\n"
)


class ApplyRealOperationsTest(unittest.TestCase):
    """Deletes, rename removal halves, and exec-bit restores land through
    a real apply; the §7.7 assertion catches the forgotten chmod."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-applyops-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        # Committed fixtures for the removal-shaped operations: a file to
        # delete outright and a rename source.
        data = self.repo / "data"
        data.mkdir()
        (data / "old.txt").write_text("obsolete body\n", encoding="utf-8")
        (data / "src.txt").write_text("rename me\n", encoding="utf-8")
        run_checked(["git", "add", "data"], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "data fixtures"],
                    cwd=self.repo, env=self.genv)
        # A directory-shaped scope: new files created under data/ (the
        # rename target, the shipped executable) land in scope by design
        # (TARBALL.md section 3.2).
        result = run_bale(
            self.install,
            ["pack", "real-operations fixture session",
             "--slug", "applyops",
             "--include", "data",
             "--no-readme"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        self.sid = sids[0]

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def apply_and_expect_merge(self, tarball: Path):
        """Run apply, assert the piped default merged (PASS headline,
        applied tag, session closed), and return the result."""
        result = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn(PASS_HEADLINE, result.stdout)
        run_checked(["git", "rev-parse", "--verify",
                     f"refs/tags/applied/{self.sid}"],
                    cwd=self.repo, env=self.genv)
        open_flag = self.repo / ".bale" / "sessions" / self.sid / "open"
        self.assertFalse(open_flag.is_file(),
                         msg="a merged apply closes the session")
        return result

    def git_mode(self, path: str) -> str:
        """The committed file mode on the merged tree ('' when untracked)."""
        out = subprocess.run(
            ["git", "ls-files", "-s", path],
            cwd=self.repo, env=self.genv, capture_output=True, text=True,
        ).stdout.strip()
        return out.split()[0] if out else ""

    # -- the operations --------------------------------------------------

    def test_delete_lands(self) -> None:
        """A deleted entry (rm in apply.sh) is gone from both the working
        tree and the merged commit's index."""
        rdir = build_response_dir(
            self.tmp / "delete", self.sid,
            summary="real-ops fixture: delete data/old.txt",
            entries=[{
                "path": "data/old.txt", "action": "deleted",
                "reason": "the delete operation under test",
            }],
            apply_sh=(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "# Remove data/old.txt — the delete operation under test.\n"
                "rm -f data/old.txt\n"),
        )
        self.apply_and_expect_merge(tar_response_dir(rdir))
        self.assertFalse((self.repo / "data" / "old.txt").exists(),
                         msg="the delete must land on the working tree")
        self.assertEqual(self.git_mode("data/old.txt"), "",
                         msg="the delete must land in the merged index")
        # The neighboring fixture survived: the delete was surgical.
        self.assertEqual(
            (self.repo / "data" / "src.txt").read_text(encoding="utf-8"),
            "rename me\n")

    def test_rename_removal_half_lands(self) -> None:
        """A rename decomposed per §5.1.1 — created new path under files/
        plus rm of the old path — lands as exactly that transition: old
        gone, new present with the shipped bytes."""
        body = b"rename me\n"
        rdir = build_response_dir(
            self.tmp / "rename", self.sid,
            summary="real-ops fixture: rename data/src.txt to data/dst.txt",
            entries=[
                {"path": "data/dst.txt", "action": "created",
                 "reason": "the rename's created half (full content)",
                 "data": body},
                {"path": "data/src.txt", "action": "deleted",
                 "reason": "the rename's removal half"},
            ],
            apply_sh=(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "# Removal half of the src.txt -> dst.txt rename;\n"
                "# apply.sh never performs mv (TARBALL.md section 5.1.1).\n"
                "rm -f data/src.txt\n"),
        )
        self.apply_and_expect_merge(tar_response_dir(rdir))
        self.assertFalse((self.repo / "data" / "src.txt").exists(),
                         msg="the removal half must land")
        self.assertEqual(self.git_mode("data/src.txt"), "")
        self.assertEqual(
            (self.repo / "data" / "dst.txt").read_bytes(), body,
            msg="the created half must carry the full content")

    def test_exec_bit_restore_lands_with_assertion(self) -> None:
        """The overlay strips mode; apply.sh's chmod +x restores it, the
        §7.7 assertion passes, and the merged tree records 100755."""
        rdir = build_response_dir(
            self.tmp / "execbit", self.sid,
            summary="real-ops fixture: ship an executable with the "
                    "chmod restore and its section 7.7 assertion",
            entries=[{
                "path": "data/run.sh", "action": "created",
                "reason": "the shipped executable under test",
                "data": RUN_SH_BODY,
            }],
            apply_sh=(
                "#!/usr/bin/env bash\n"
                "set -euo pipefail\n"
                "# Exec-bit restore: the files/ overlay strips mode\n"
                "# (TARBALL.md section 5.1.1).\n"
                "chmod +x data/run.sh\n"),
            validation_sh=EXEC_ASSERT_VALIDATION_SH,
            validation_will_run=[EXEC_CHECK],
            claims={EXEC_CHECK: "pass"},
        )
        result = self.apply_and_expect_merge(tar_response_dir(rdir))
        # The assertion ran and passed inside staging.
        self.assertNotIn("[FAIL]", result.stdout)
        merged = self.repo / "data" / "run.sh"
        self.assertTrue(os.access(merged, os.X_OK),
                        msg="the exec bit must land on the working tree")
        self.assertEqual(self.git_mode("data/run.sh"), "100755",
                         msg="the exec bit must land in the merged index")
        self.assertEqual(merged.read_bytes(), RUN_SH_BODY)

    def test_forgotten_chmod_is_caught_by_assertion(self) -> None:
        """The §7.7 assertion's whole point: with the chmod line missing
        from apply.sh, the shipped script arrives mode-stripped, the
        assertion FAILs, and the piped default holds instead of merging
        — nothing lands."""
        rdir = build_response_dir(
            self.tmp / "forgot", self.sid,
            summary="real-ops fixture: the forgotten-chmod failure the "
                    "section 7.7 assertion exists to catch",
            entries=[{
                "path": "data/run.sh", "action": "created",
                "reason": "shipped executable whose chmod was forgotten",
                "data": RUN_SH_BODY,
            }],
            # apply.sh defaults to the no-op: the forgotten chmod.
            validation_sh=EXEC_ASSERT_VALIDATION_SH,
            validation_will_run=[EXEC_CHECK],
            claims={EXEC_CHECK: "pass"},
        )
        result = run_bale(self.install,
                          ["apply", str(tar_response_dir(rdir))],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 1,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn(HOLD_HEADLINE, result.stdout)
        # The per-check verdict streams to the session log (the
        # walkthrough points at it); the [FAIL] line is the assertion
        # firing.
        session_log = (self.repo / ".bale" / "logs" / f"{self.sid}.log")
        self.assertIn(f"[FAIL] {EXEC_CHECK}",
                      session_log.read_text(encoding="utf-8"))
        # Nothing landed: no script on the tree, session still open for
        # the corrective retry.
        self.assertFalse((self.repo / "data" / "run.sh").exists())
        open_flag = self.repo / ".bale" / "sessions" / self.sid / "open"
        self.assertTrue(open_flag.is_file())


if __name__ == "__main__":
    unittest.main(verbosity=2)
