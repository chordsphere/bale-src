#!/usr/bin/env python3
"""Malformed-tarball apply pre-flight suite (board 35 gap 1).

Pins the reject surface of the apply contract — the rows BALE.md §11
enumerates that a malformed or mismatched *response tarball itself* can
trip, none of which had live coverage before this suite (the
2026-08-06 selftest audit's gap 1). One test per row; each asserts
three things per the session brief:

- the refusal fires (exit 1),
- the refusal is loud (the message names the row's condition),
- nothing was applied (the tree and the session state survive the
  rejected apply: content unchanged, session still open, no
  ``bale/<sid>`` branch, no ``applied/<sid>`` tag).

Rows covered, enumerated from BALE.md §11 itself (the brief's summary
list was verified against the doc per its own instruction):

- 5   tar archive integrity (unreadable / unsafe member / top-level shape)
- 6   manifest schema validity
- 7   an open session exists
- 9   ``responds_to`` names the open session
- 10  every changes[] path in files/ per its action
- 11  every files/ entry declared in changes[]
- 12  sha256 match against files/
- 13  non-empty (stripped) reason
- 14  path safety (traversal, ``.git/``, ``.bale/``, ``.baleignore``)
- 15  claims ⊆ validation_will_run
- 16  required artifacts present (manifest.json / apply.sh / validation.sh)
- 17  apply.sh exits 0 (stage)
- 18  post-apply.sh reconciliation (post-stage)
- 20  generated-artifact denial
- 25  non-normal response-kind shape
- 32  duplicate changes[] paths (v0.4.2 — the board-35 rider ratified
      2026-08-07: TARBALL.md §5.2's prose converted to apply-side
      contract; this suite's earlier behavior pin, which documented
      the identical-duplicate acceptance the rider closed, is
      superseded by the row's own test)

Rows deliberately excluded: 8 (dirty-on-target — an environment-state
refusal, not tarball malformation), 19/21/22 (sibling-scope, declared
untracked inputs, own-scope drift — session-topology and config
machinery; row 22's refusal and override are pinned in
test_readonly_pack.py), 26–29 (required checks and checkpoints — their
own suites), and the pack/handoff-side rows.

Fixture doctrine: every rejection test is exactly one mutation away
from a known-good baseline — the shared harness builder
(``build_response_dir``) produces a valid response, and the local
tamper helper applies a single named mutation before tarring. The
fixture session is packed with ``--include .`` on purpose: a
whole-tree scope makes the own-scope drift gate (row 22) vacuous, so
each test's tampered path reaches *its* row's check instead of being
intercepted by the drift refusal.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_apply_preflight.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import subprocess
import tarfile
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

ORIGINAL_HELLO = "hello\n"
ORIGINAL_OTHER = "other\n"


class ApplyPreflightRejectTest(unittest.TestCase):
    """Each §11 malformed-tarball row refuses loudly and applies nothing."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-preflight-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        # A second committed file: the row-18 reconciliation subtests need a
        # path that exists pre-apply but is NOT declared in the baseline
        # manifest (hello.txt is declared modified there).
        genv = git_env(self.home)
        (self.repo / "other.txt").write_text(ORIGINAL_OTHER, encoding="utf-8")
        run_checked(["git", "add", "other.txt"], cwd=self.repo, env=genv)
        run_checked(["git", "commit", "-m", "add other.txt"],
                    cwd=self.repo, env=genv)
        self.env = bale_env(self.home, self.tmp)
        self.sid = self._packed_sid()
        self.nnn = self.sid[-3:]
        self._fixture_counter = 0

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- fixtures --------------------------------------------------------

    def _packed_sid(self) -> str:
        """Pack the fixture session with a whole-tree scope (see module
        docstring: keeps the row-22 drift gate vacuous so each row's own
        refusal is the one that fires)."""
        result = run_bale(
            self.install,
            ["pack", "apply pre-flight fixture session",
             "--slug", "preflight",
             "--include", ".",
             "--no-readme"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        return sids[0]

    def baseline_dir(self) -> Path:
        """A valid normal response modifying hello.txt — the known-good
        baseline every tamper starts from. A fresh directory per call so
        subtests never share a mutated fixture."""
        self._fixture_counter += 1
        return build_response_dir(
            self.tmp / f"fixture-{self._fixture_counter}", self.sid,
            summary="pre-flight fixture: rewrite hello.txt",
            entries=[{
                "path": "hello.txt",
                "action": "modified",
                "reason": "baseline rewrite the tamper mutates around",
                "data": b"tampered-fixture content\n",
            }],
        )

    def tampered_tarball(self, mutate) -> Path:
        """Build the valid baseline, apply one mutation, tar the result.

        `mutate(manifest, rdir)` edits the parsed manifest dict and/or the
        response directory in place; the (possibly mutated) manifest is
        written back before tarring, so a manifest-only tamper needs no
        file I/O of its own. Because of that write-back, this helper is
        the wrong tool for a tamper that removes manifest.json itself —
        the rewrite would resurrect it (test_row16 builds directly).
        """
        rdir = self.baseline_dir()
        manifest = json.loads(
            (rdir / "manifest.json").read_text(encoding="utf-8"))
        mutate(manifest, rdir)
        (rdir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
        return tar_response_dir(rdir)

    # -- assertions ------------------------------------------------------

    def assert_rejected(self, result, *needles: str) -> None:
        """Refusal fired (exit 1) and its message names the condition."""
        self.assertEqual(
            result.returncode, 1,
            msg=f"expected a rejection; stdout:\n{result.stdout}\n"
                f"stderr:\n{result.stderr}")
        for needle in needles:
            self.assertIn(
                needle, result.stderr,
                msg=f"refusal is not loud: {needle!r} missing from "
                    f"stderr:\n{result.stderr}")
        self.assert_nothing_applied()

    def assert_nothing_applied(self) -> None:
        """The tree and the session state survive the rejected apply."""
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            ORIGINAL_HELLO, msg="rejected apply must not touch the tree")
        self.assertEqual(
            (self.repo / "other.txt").read_text(encoding="utf-8"),
            ORIGINAL_OTHER, msg="rejected apply must not touch the tree")
        open_flag = self.repo / ".bale" / "sessions" / self.sid / "open"
        self.assertTrue(open_flag.is_file(),
                        msg="rejected apply must leave the session open")
        genv = git_env(self.home)
        for ref in (f"refs/heads/bale/{self.sid}",
                    f"refs/tags/applied/{self.sid}"):
            probe = subprocess.run(
                ["git", "rev-parse", "--verify", "--quiet", ref],
                cwd=self.repo, env=genv, capture_output=True, text=True)
            self.assertNotEqual(
                probe.returncode, 0,
                msg=f"rejected apply must leave no git side effects; "
                    f"{ref} exists")

    def apply(self, tarball: Path):
        return run_bale(self.install, ["apply", str(tarball)],
                        cwd=self.repo, env=self.env)

    # -- the rows --------------------------------------------------------

    def test_row5_tar_archive_integrity(self) -> None:
        """Row 5: unreadable archives, unsafe member paths, and a broken
        top-level shape are all refused before anything else runs."""
        with self.subTest(variant="unreadable bytes"):
            bad = self.tmp / "corrupt.tar.gz"
            bad.write_bytes(b"this is not a gzip stream")
            self.assert_rejected(self.apply(bad), "tarball is unreadable")

        with self.subTest(variant="path-traversal member"):
            rdir = self.baseline_dir()
            tarball = self.tmp / "traversal-member.tar.gz"
            with tarfile.open(tarball, "w:gz") as tf:
                tf.add(str(rdir), arcname=rdir.name)
                tf.add(str(rdir / "manifest.json"),
                       arcname=f"{rdir.name}/../evil.json")
            self.assert_rejected(
                self.apply(tarball),
                "tarball contains unsafe path", "../evil.json")

        with self.subTest(variant="second top-level entry"):
            rdir = self.baseline_dir()
            tarball = self.tmp / "two-top-level.tar.gz"
            with tarfile.open(tarball, "w:gz") as tf:
                tf.add(str(rdir), arcname=rdir.name)
                tf.add(str(rdir / "manifest.json"), arcname="stray.json")
            self.assert_rejected(
                self.apply(tarball),
                "exactly one top-level directory")

        with self.subTest(variant="top-level dir not response-NNN"):
            rdir = self.baseline_dir()
            tarball = self.tmp / "bad-prefix.tar.gz"
            with tarfile.open(tarball, "w:gz") as tf:
                tf.add(str(rdir), arcname="reply-001")
            self.assert_rejected(
                self.apply(tarball),
                "top-level directory must be named response-NNN/")

    def test_row6_manifest_schema(self) -> None:
        """Row 6: a manifest missing a required key, or carrying an
        unknown key, fails schema validation with the field named."""
        with self.subTest(variant="missing required key"):
            tarball = self.tampered_tarball(
                lambda m, rdir: m.pop("summary"))
            self.assert_rejected(
                self.apply(tarball),
                "failed schema validation", "missing required key 'summary'")

        with self.subTest(variant="unknown key"):
            tarball = self.tampered_tarball(
                lambda m, rdir: m.__setitem__("surprise", True))
            self.assert_rejected(
                self.apply(tarball),
                "failed schema validation", "unknown key 'surprise'")

    def test_row7_no_open_session(self) -> None:
        """Row 7: with no session open in the registry, apply refuses
        before reading anything from the tarball's contents."""
        # Close the fixture session first: unlock is the sanctioned
        # no-successor close (TARBALL.md §3.4); the piped run needs no
        # confirmation.
        result = run_bale(self.install, ["unlock", self.sid],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        tarball = tar_response_dir(self.baseline_dir())
        result = self.apply(tarball)
        self.assertEqual(result.returncode, 1)
        self.assertIn("no session is open", result.stderr)
        # The session was closed by unlock, not by the rejected apply, so
        # assert only the tree half of nothing-applied here.
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            ORIGINAL_HELLO)

    def test_row9_responds_to_mismatch(self) -> None:
        """Row 9: a response naming a sid that is not the open session is
        refused with both sids in the message."""
        ghost = "2026-01-01-ghost-001"

        def wrong_sid(m, rdir):
            m["session_id"] = ghost
            m["responds_to"] = ghost

        tarball = self.tampered_tarball(wrong_sid)
        self.assert_rejected(
            self.apply(tarball),
            "does not match the open session", ghost, self.sid)

    def test_row10_changes_vs_files_presence(self) -> None:
        """Row 10: a created/modified entry must have its file under
        files/, and a deleted entry must not ship one."""
        with self.subTest(variant="modified entry with no file"):
            def drop_file(m, rdir):
                (rdir / "files" / "hello.txt").unlink()
            self.assert_rejected(
                self.apply(self.tampered_tarball(drop_file)),
                "manifest declares modified hello.txt",
                "files/hello.txt is missing")

        with self.subTest(variant="deleted entry shipping a file"):
            def delete_ships(m, rdir):
                m["changes"][0].update(
                    action="deleted", size_bytes=0, sha256=None)
            self.assert_rejected(
                self.apply(self.tampered_tarball(delete_ships)),
                "manifest declares deleted hello.txt",
                "deletes must not ship a file")

    def test_row11_undeclared_file(self) -> None:
        """Row 11: a file under files/ with no changes[] entry is refused
        by name."""
        def stow_extra(m, rdir):
            (rdir / "files" / "extra.txt").write_bytes(b"stowaway\n")
        self.assert_rejected(
            self.apply(self.tampered_tarball(stow_extra)),
            "file in tarball not declared in manifest", "files/extra.txt")

    def test_row12_sha256_mismatch(self) -> None:
        """Row 12: a manifest sha256 disagreeing with the shipped bytes is
        refused with both hashes' prefixes shown."""
        tarball = self.tampered_tarball(
            lambda m, rdir: m["changes"][0].__setitem__("sha256", "0" * 64))
        self.assert_rejected(
            self.apply(tarball),
            "sha256 mismatch for hello.txt", "manifest=000000000000")

    def test_row13_empty_reason(self) -> None:
        """Row 13: a whitespace-only reason is refused by the
        stripped-non-empty rule (the schema's minLength:1 already rejects
        the empty string; the stripped check is this row's stronger
        Python-side half)."""
        tarball = self.tampered_tarball(
            lambda m, rdir: m["changes"][0].__setitem__("reason", "   "))
        self.assert_rejected(
            self.apply(tarball),
            "reason must be non-empty after stripping")

    def test_row14_path_safety(self) -> None:
        """Row 14: traversal, reserved prefixes, and .baleignore matches
        are all refused. The fixture scope is the whole tree, so these
        reach the path-safety gate rather than the row-22 drift gate."""
        def declare(m, rdir, path: str) -> None:
            data = b"unsafe\n"
            m["changes"].append({
                "path": path, "action": "created",
                "reason": "path-safety tamper", "size_bytes": len(data),
                "sha256": "0" * 64,
            })

        for path in ("../escape.txt", ".git/hooks/hook", ".bale/smuggled"):
            with self.subTest(variant=path):
                tarball = self.tampered_tarball(
                    lambda m, rdir, p=path: declare(m, rdir, p))
                self.assert_rejected(
                    self.apply(tarball), "unsafe path in manifest", path)

        with self.subTest(variant=".baleignore match"):
            # The .baleignore file is user-managed project state; writing
            # it after pack is fine (untracked files never block apply —
            # row 8 is deliberately narrow).
            (self.repo / ".baleignore").write_text(
                "secret.txt\n", encoding="utf-8")
            def declare_secret(m, rdir):
                data = b"contraband\n"
                f = rdir / "files" / "secret.txt"
                f.write_bytes(data)
                import hashlib
                m["changes"].append({
                    "path": "secret.txt", "action": "created",
                    "reason": "baleignore tamper", "size_bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                })
            self.assert_rejected(
                self.apply(self.tampered_tarball(declare_secret)),
                "matches .baleignore pattern", "secret.txt")

    def test_row15_claims_subset(self) -> None:
        """Row 15: a claims key with no verbatim validation_will_run match
        is refused with the stray key named."""
        tarball = self.tampered_tarball(
            lambda m, rdir: m.__setitem__("claims", {"phantom check": "pass"}))
        self.assert_rejected(
            self.apply(tarball),
            "claims has keys not in validation_will_run", "phantom check")

    def test_row16_required_artifacts(self) -> None:
        """Row 16: each of the three required artifacts is refused by name
        when absent. Built without the tamper helper on purpose — the
        helper writes manifest.json back after the mutation, which would
        resurrect the very file this row deletes."""
        for artifact in ("manifest.json", "apply.sh", "validation.sh"):
            with self.subTest(variant=artifact):
                rdir = self.baseline_dir()
                (rdir / artifact).unlink()
                self.assert_rejected(
                    self.apply(tar_response_dir(rdir)),
                    "missing required file in tarball", artifact)

    def test_row17_apply_sh_nonzero_exit(self) -> None:
        """Row 17: an apply.sh that exits non-zero fails the stage loudly,
        with the script's own output carried into the message."""
        rdir = build_response_dir(
            self.tmp / "row17", self.sid,
            summary="row 17 fixture: apply.sh fails by construction",
            entries=[{
                "path": "hello.txt", "action": "modified",
                "reason": "never lands; apply.sh fails first",
                "data": b"unreachable\n",
            }],
            apply_sh="#!/usr/bin/env bash\necho boom >&2\nexit 3\n",
        )
        self.assert_rejected(
            self.apply(tar_response_dir(rdir)),
            "failed to stage response", "apply.sh exited 3", "boom")

    def test_row18_reconciliation_mismatch(self) -> None:
        """Row 18: the post-apply.sh staging tree must match the manifest
        exactly — undeclared writes, undeclared deletes, and a declared
        delete apply.sh never performed all refuse, each named."""
        cases = [
            ("undeclared write",
             "#!/usr/bin/env bash\necho rogue > rogue.txt\nexit 0\n",
             None,
             ["undeclared created in staging: rogue.txt"]),
            ("undeclared delete",
             "#!/usr/bin/env bash\nrm -f other.txt\nexit 0\n",
             None,
             ["undeclared deleted from staging: other.txt"]),
            ("declared delete not performed",
             None,  # no-op apply.sh: the declared rm never happens
             lambda m: m["changes"].append({
                 "path": "other.txt", "action": "deleted",
                 "reason": "declared but never performed",
                 "size_bytes": 0, "sha256": None,
             }),
             ["declared deleted but still in staging", "other.txt"]),
        ]
        for label, apply_sh, manifest_mut, needles in cases:
            with self.subTest(variant=label):
                def mutate(m, rdir):
                    if manifest_mut:
                        manifest_mut(m)
                    if apply_sh:
                        (rdir / "apply.sh").write_text(
                            apply_sh, encoding="utf-8")
                self.assert_rejected(
                    self.apply(self.tampered_tarball(mutate)),
                    "BALE.md §11 rule 18", *needles)

    def test_row20_generated_artifact_denial(self) -> None:
        """Row 20: a changes[] path naming a generated artifact is refused
        with the offending path listed."""
        def declare_pyc(m, rdir):
            m["changes"].append({
                "path": "__pycache__/module.pyc", "action": "created",
                "reason": "generated-artifact tamper", "size_bytes": 2,
                "sha256": "0" * 64,
            })
        self.assert_rejected(
            self.apply(self.tampered_tarball(declare_pyc)),
            "generated artifacts in changes[]", "__pycache__/module.pyc")

    def test_row25_response_kind_shape(self) -> None:
        """Row 25: the non-normal kinds' cross-field rules — a
        clarification with a non-empty change surface, and a normal
        response carrying questions[], both refuse."""
        with self.subTest(variant="clarification with changes"):
            def clar_with_changes(m, rdir):
                m["response_kind"] = "clarification"
                m["questions"] = [{
                    "question": "q", "context": "c",
                    "default_assumption": "d", "why_blocked": "w",
                }]
            self.assert_rejected(
                self.apply(self.tampered_tarball(clar_with_changes)),
                "response_kind=clarification requires changes[] to be empty")

        with self.subTest(variant="normal with questions"):
            def normal_with_questions(m, rdir):
                m["questions"] = [{
                    "question": "q", "context": "c",
                    "default_assumption": "d", "why_blocked": "w",
                }]
            self.assert_rejected(
                self.apply(self.tampered_tarball(normal_with_questions)),
                "questions is only valid when response_kind=clarification")

    def test_row32_duplicate_changes_path(self) -> None:
        """Row 32 (v0.4.2, the board-35 rider ratified 2026-08-07): a
        duplicated changes[] path refuses at the manifest checks —
        prose and enforcement now agree that TARBALL.md §5.2's
        "a duplicated path is invalid" is contract, not lint-only.

        Both variants land on the same gate: the *identical* duplicate
        (which previously applied cleanly — the disagreement the rider
        was ratified to close) and the *conflicting* one (which
        previously limped to the row-12 sha mismatch; the duplicate
        gate now fires first, at the manifest checks where the
        ambiguity actually lives).
        """
        with self.subTest(variant="identical duplicate"):
            def duplicate_identical(m, rdir):
                m["changes"].append(dict(m["changes"][0]))

            self.assert_rejected(
                self.apply(self.tampered_tarball(duplicate_identical)),
                "duplicate changes[] path", "hello.txt")

        with self.subTest(variant="conflicting duplicate"):
            def duplicate_conflicting(m, rdir):
                twin = dict(m["changes"][0])
                twin["sha256"] = "f" * 64
                twin["reason"] = "conflicting duplicate of the same path"
                m["changes"].append(twin)

            self.assert_rejected(
                self.apply(self.tampered_tarball(duplicate_conflicting)),
                "duplicate changes[] path", "hello.txt")


if __name__ == "__main__":
    unittest.main(verbosity=2)
