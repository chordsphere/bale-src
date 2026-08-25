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

Row 8 (dirty-on-target) is an environment-state refusal, not tarball
malformation, so it lives in its own class below
(``ApplyDirtyOnTargetTest``, board 35 small pins) rather than in the
malformed-tarball class: its narrow contract has proceed-cases as well
as the refusal, which the reject class's charter can't carry.

Rows deliberately excluded: 19/21/22 (sibling-scope, declared
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
import os
import shutil
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
    run_bale_pty,
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


class ApplyDirtyOnTargetTest(unittest.TestCase):
    """BALE.md §11 row 8 — the ADR-0008 narrow dirty-on-target rule.

    The last apply pre-flight refusal with no live coverage (board 35,
    from session 1's proposals), pinned as the three-case narrow
    contract a regression would silently widen:

    - the ONE entangled case refuses: checkout on the integration
      target with tracked changes (moving the ref would desynchronize
      the checkout from its own branch);
    - untracked files NEVER block — invisible to a branch ref;
    - a dirty checkout on any OTHER branch never blocks — integration
      is checkout-free (ADR-0008) and only moves the target ref.

    Pure git choreography in the standard sandbox; no new fixtures.
    Subtests run in sequence: the refusal leaves its session open for
    the untracked case, whose merge then closes it; the off-target case
    packs its own session before switching branches.
    """

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-dirtytgt-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack_session(self, slug: str) -> str:
        """Pack a whole-tree session on the CURRENT branch (the
        origin_branch stamp fixes the integration target at pack time)
        and return its sid."""
        result = run_bale(
            self.install,
            ["pack", "dirty-on-target fixture session",
             "--slug", slug, "--include", ".", "--no-readme"],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file()]
        self.assertEqual(len(sids), 1)
        return sids[0]

    def response_tarball(self, sid: str, name: str, data: bytes) -> Path:
        rdir = build_response_dir(
            self.tmp / name, sid,
            summary="dirty-on-target fixture: rewrite hello.txt",
            entries=[{
                "path": "hello.txt", "action": "modified",
                "reason": "the fixture rewrite the three cases apply",
                "data": data,
            }])
        return tar_response_dir(rdir)

    def apply(self, tarball: Path):
        return run_bale(self.install, ["apply", str(tarball)],
                        cwd=self.repo, env=self.env)

    # -- the three cases -------------------------------------------------

    def test_row8_narrow_dirty_on_target(self) -> None:
        with self.subTest(variant="tracked dirt on the target refuses"):
            sid = self.pack_session("dirtytgt")
            dirty_content = "uncommitted user edit\n"
            (self.repo / "hello.txt").write_text(dirty_content,
                                                 encoding="utf-8")
            result = self.apply(self.response_tarball(
                sid, "refused", b"on-target content\n"))
            self.assertEqual(
                result.returncode, 1,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            self.assertIn("tracked changes while checked out on the "
                          "integration target", result.stderr)
            self.assertIn("'main'", result.stderr)
            self.assertIn("hello.txt", result.stderr,
                          msg="the refusal lists the dirty paths")
            # Nothing happened: dirt untouched, session open, no refs.
            self.assertEqual(
                (self.repo / "hello.txt").read_text(encoding="utf-8"),
                dirty_content)
            self.assertTrue(
                (self.repo / ".bale" / "sessions" / sid / "open").is_file())
            for ref in (f"refs/heads/bale/{sid}",
                        f"refs/tags/applied/{sid}"):
                probe = subprocess.run(
                    ["git", "rev-parse", "--verify", "--quiet", ref],
                    cwd=self.repo, env=self.genv,
                    capture_output=True, text=True)
                self.assertNotEqual(probe.returncode, 0,
                                    msg=f"{ref} must not exist")
            # Drop the dirt; the session is still open for the next case.
            run_checked(["git", "checkout", "--", "hello.txt"],
                        cwd=self.repo, env=self.genv)

        with self.subTest(variant="untracked files never block"):
            (self.repo / "stray.txt").write_text("untracked stray\n",
                                                 encoding="utf-8")
            merged_content = b"untracked-case content\n"
            result = self.apply(self.response_tarball(
                sid, "untracked-ok", merged_content))
            self.assertEqual(
                result.returncode, 0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            run_checked(["git", "rev-parse", "--verify",
                         f"refs/tags/applied/{sid}"],
                        cwd=self.repo, env=self.genv)
            # On-target and tracked-clean: the checkout fast-forwards.
            self.assertEqual(
                (self.repo / "hello.txt").read_text(encoding="utf-8"),
                merged_content.decode("utf-8"))
            self.assertEqual(
                (self.repo / "stray.txt").read_text(encoding="utf-8"),
                "untracked stray\n",
                msg="the untracked file rides through untouched")

        with self.subTest(variant="a dirty OTHER branch never blocks"):
            # Pack on main (fixing main as the target), then switch to a
            # side branch and dirty it: integration is checkout-free, so
            # the apply proceeds and only the main ref moves.
            sid2 = self.pack_session("dirtytgt-side")
            run_checked(["git", "checkout", "-b", "side"],
                        cwd=self.repo, env=self.genv)
            side_dirty = "side-branch uncommitted edit\n"
            (self.repo / "hello.txt").write_text(side_dirty,
                                                 encoding="utf-8")
            merged_content = b"off-target-case content\n"
            result = self.apply(self.response_tarball(
                sid2, "offtarget-ok", merged_content))
            self.assertEqual(
                result.returncode, 0,
                msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
            run_checked(["git", "rev-parse", "--verify",
                         f"refs/tags/applied/{sid2}"],
                        cwd=self.repo, env=self.genv)
            # The merge landed on main's ref...
            show = subprocess.run(
                ["git", "show", "main:hello.txt"],
                cwd=self.repo, env=self.genv,
                capture_output=True, text=True)
            self.assertEqual(show.returncode, 0)
            self.assertEqual(show.stdout, merged_content.decode("utf-8"))
            # ...while the checkout stayed on side, dirt intact.
            branch = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo, env=self.genv,
                capture_output=True, text=True)
            self.assertEqual(branch.stdout.strip(), "side")
            self.assertEqual(
                (self.repo / "hello.txt").read_text(encoding="utf-8"),
                side_dirty,
                msg="integration never touches the checkout")


class BareApplyResolutionTest(unittest.TestCase):
    """Bare `bale apply` (board 51): argument-less resolution.

    The ratified contract: apply with no argument resolves the newest
    response tarball matching an open session across the search paths,
    echoes its identity, and takes a y/N; ambiguity — a candidate tie, or
    two open sessions — refuses loudly, never guesses. Refusals exit
    through the bale refusal convention (exit 1, remedy-naming stderr),
    never an argparse usage error. Piped stdin takes the confirmation's
    decline default without a prompt (the --supersedes precedent), so the
    piped runner exercises the refusal surface and the pty runner
    exercises the resolution happy path and the interactive decline.
    """

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-bareapply-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        # A second committed file so a disjoint --write pair of sessions
        # can be open at once (the two-open-sessions ambiguity case).
        (self.repo / "other.txt").write_text("other\n", encoding="utf-8")
        run_checked(["git", "add", "other.txt"], cwd=self.repo,
                    env=self.genv)
        run_checked(["git", "commit", "-m", "add other.txt"],
                    cwd=self.repo, env=self.genv)
        # The inbound directory bare resolution scans, configured as an
        # apply search path in the repo's bale.toml (untracked; untracked
        # files never block per the ADR-0008 narrow rule).
        self.downloads = self.tmp / "downloads"
        self.downloads.mkdir()
        (self.repo / "bale.toml").write_text(
            "[apply]\n"
            f"search_paths = [\"{self.downloads}\"]\n",
            encoding="utf-8")
        self._fixture_counter = 0

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def pack_session(self, slug: str, extra: list = ()) -> str:
        result = run_bale(
            self.install,
            ["pack", "bare-apply fixture session", "--slug", slug,
             "--include", ".", "--no-readme", *extra],
            cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = sorted(d.name for d in root.iterdir()
                      if (d / "open").is_file())
        return sids[-1]

    def deliver_response(self, sid: str, name: str, data: bytes,
                         mtime_ns: int = None) -> Path:
        """Build a valid response tarball answering `sid`, drop it into
        the downloads dir under an arbitrary filename (discrimination is
        content-based, so browser-mangled names must not matter), and
        optionally pin its mtime."""
        self._fixture_counter += 1
        rdir = build_response_dir(
            self.tmp / f"bare-fixture-{self._fixture_counter}", sid,
            summary=f"bare-apply fixture: {name}",
            entries=[{
                "path": "hello.txt", "action": "modified",
                "reason": "the fixture rewrite the bare form applies",
                "data": data,
            }])
        tarball = tar_response_dir(rdir)
        dest = self.downloads / f"{name}.tar.gz"
        shutil.move(str(tarball), str(dest))
        if mtime_ns is not None:
            os.utime(dest, ns=(mtime_ns, mtime_ns))
        return dest

    def deliver_request_shaped(self, name: str, mtime_ns: int = None) -> Path:
        """A request-shaped tarball (top-level request-NNN/) in downloads:
        must never be a candidate, however new it is."""
        rdir = self.tmp / f"reqshape-{name}" / "request-999"
        rdir.mkdir(parents=True)
        (rdir / "manifest.json").write_text(
            json.dumps({"session_id": "2026-01-01-reqshape-999",
                        "goal": "not a response"}) + "\n",
            encoding="utf-8")
        dest = self.downloads / f"{name}.tar.gz"
        with tarfile.open(dest, "w:gz") as tf:
            tf.add(str(rdir), arcname=rdir.name)
        if mtime_ns is not None:
            os.utime(dest, ns=(mtime_ns, mtime_ns))
        return dest

    def bare_apply_piped(self, *flags: str):
        return run_bale(self.install, ["apply", *flags],
                        cwd=self.repo, env=self.env)

    def assert_refused(self, result, *needles: str) -> None:
        """Exit 1 (the bale refusal convention — never argparse's 2) and
        a stderr message naming the condition and its remedy."""
        self.assertEqual(
            result.returncode, 1,
            msg=f"expected a bale refusal (exit 1); "
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        for needle in needles:
            self.assertIn(
                needle, result.stderr,
                msg=f"refusal is not loud: {needle!r} missing from "
                    f"stderr:\n{result.stderr}")

    def assert_nothing_applied(self, sid: str) -> None:
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            "hello\n", msg="a refused/declined bare apply must not "
                           "touch the tree")
        self.assertTrue(
            (self.repo / ".bale" / "sessions" / sid / "open").is_file(),
            msg="a refused/declined bare apply must leave the session open")

    # -- the happy path (pty: the y/N must actually be answered) ---------

    def test_bare_resolves_newest_echoes_and_applies(self) -> None:
        sid = self.pack_session("bare")
        base = 1_700_000_000_000_000_000  # arbitrary fixed epoch ns
        self.deliver_response(sid, "older-delivery", b"older content\n",
                              mtime_ns=base)
        newest = self.deliver_response(sid, "newer-delivery",
                                       b"newer content\n",
                                       mtime_ns=base + 10 * 10**9)
        # A request-shaped tarball newer than both: never a candidate.
        self.deliver_request_shaped("request-newest",
                                    mtime_ns=base + 20 * 10**9)
        exit_code, output = run_bale_pty(
            self.install, ["apply"], cwd=self.repo, env=self.env,
            answers="y\n\n")
        self.assertEqual(exit_code, 0,
                         msg=f"bare apply should resolve and merge; "
                             f"output:\n{output}")
        # The identity echo precedes the prompt: path, sid, a content
        # identity, and the newest-won note.
        self.assertIn(str(newest), output)
        self.assertIn(sid, output)
        self.assertIn("sha256", output)
        self.assertIn("newest modification time won", output)
        # The newer delivery is what landed.
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            "newer content\n")
        run_checked(["git", "rev-parse", "--verify",
                     f"refs/tags/applied/{sid}"],
                    cwd=self.repo, env=self.genv)

    def test_bare_interactive_decline_applies_nothing(self) -> None:
        sid = self.pack_session("bare-decline")
        self.deliver_response(sid, "sole-delivery", b"declined content\n")
        exit_code, output = run_bale_pty(
            self.install, ["apply"], cwd=self.repo, env=self.env,
            answers="n\n")
        self.assertEqual(exit_code, 1,
                         msg=f"decline must refuse; output:\n{output}")
        self.assertIn("declined", output)
        self.assert_nothing_applied(sid)

    # -- the refusal surface (piped: decline default, no prompt) ---------

    def test_bare_no_open_session(self) -> None:
        result = self.bare_apply_piped()
        self.assert_refused(result, "no session is open", "bale pack",
                            "name the tarball explicitly")

    def test_bare_two_open_sessions(self) -> None:
        sid_a = self.pack_session("bare-two-a",
                                  ["--write", "hello.txt"])
        sid_b = self.pack_session("bare-two-b",
                                  ["--write", "other.txt"])
        self.deliver_response(sid_a, "for-a", b"for session a\n")
        result = self.bare_apply_piped()
        self.assert_refused(result, "more than one session open",
                            "never guesses", sid_a, sid_b,
                            "responds_to")
        self.assert_nothing_applied(sid_a)

    def test_bare_no_candidates_and_request_never_a_candidate(self) -> None:
        sid = self.pack_session("bare-nocand")
        # Everything present is a non-candidate: a request-shaped tarball,
        # a response answering a session that is not open, and raw junk.
        self.deliver_request_shaped("request-only")
        self.deliver_response("2020-01-01-stale-001", "stale-response",
                              b"stale\n")
        junk = self.downloads / "junk.tar.gz"
        junk.write_bytes(b"not a gzip stream")
        result = self.bare_apply_piped()
        self.assert_refused(
            result,
            f"no response tarball answering open session {sid}",
            str(self.downloads),
            "(cwd)",
            "name the path explicitly")
        # The skips were reported in aggregate, inside the refusal.
        self.assertIn("3 tarball(s) were scanned and are not candidates",
                      result.stderr)
        self.assert_nothing_applied(sid)

    def test_bare_mtime_tie_refuses(self) -> None:
        sid = self.pack_session("bare-tie")
        base = 1_700_000_000_000_000_000
        first = self.deliver_response(sid, "tie-one", b"tie one\n",
                                      mtime_ns=base)
        second = self.deliver_response(sid, "tie-two", b"tie two\n",
                                       mtime_ns=base)
        result = self.bare_apply_piped()
        self.assert_refused(result, "share the newest modification time",
                            "never guesses", str(first), str(second))
        self.assert_nothing_applied(sid)

    def test_bare_piped_stdin_declines_without_prompt(self) -> None:
        sid = self.pack_session("bare-piped")
        sole = self.deliver_response(sid, "sole", b"piped content\n")
        result = self.bare_apply_piped()
        self.assert_refused(result, "not a TTY", "decline default",
                            str(sole))
        # The identity echo still ran before the decline (stdout is where
        # log() writes in human mode; run_bale captures it separately).
        self.assertIn(str(sole), result.stdout)
        self.assertIn("sha256", result.stdout)
        self.assert_nothing_applied(sid)

    def test_bare_with_inspection_flag_refuses(self) -> None:
        sid = self.pack_session("bare-inspect")
        self.deliver_response(sid, "inspectable", b"inspect\n")
        for flag in ("--show-validator", "--show-apply-script"):
            with self.subTest(flag=flag):
                result = self.bare_apply_piped(flag)
                self.assert_refused(result, "need the tarball named",
                                    "Name the tarball explicitly")
                self.assert_nothing_applied(sid)

    def test_bare_with_no_interact_refuses(self) -> None:
        sid = self.pack_session("bare-nointeract")
        self.deliver_response(sid, "auto", b"auto\n")
        result = self.bare_apply_piped("--no-interact")
        self.assert_refused(result, "contradictory",
                            "Name the tarball explicitly")
        self.assert_nothing_applied(sid)

    def test_argumented_form_untouched_by_bare_landing(self) -> None:
        """The boundary pin: naming the tarball still applies with no
        echo-prompt round and no bare-resolution scan."""
        sid = self.pack_session("bare-argform")
        tarball = self.deliver_response(sid, "named", b"named content\n")
        result = run_bale(self.install, ["apply", str(tarball)],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertNotIn("bare apply", result.stdout + result.stderr)
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            "named content\n")


if __name__ == "__main__":
    unittest.main(verbosity=2)
