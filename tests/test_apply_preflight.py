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
- 37  apply-side bundle backstop (v0.4.25 — the board-71 rider, accepted
      2026-08-24 from the 49a-i session's Proposals: no changes[] path
      ends in ``.bale-bundle``; the landing-direction twin of pack's
      row 33)

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
import sys
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
    slow,
    tar_response_dir,
)

ORIGINAL_HELLO = "hello\n"
ORIGINAL_OTHER = "other\n"

# The bare-apply confirmation's decline lines (v0.4.31, board 89;
# bale_apply.BARE_APPLY_DECLINE_LINES), verbatim: the cause parenthetical
# is the only addition to the fail() line the prompt always exited
# through, and the cause-less form must not survive. ^D at the start of
# a line under the pty makes input() raise EOFError — the "stdin
# closed" branch at a TTY prompt.
EOT = "\x04"
BARE_DECLINE_CAUSELESS = "bare apply declined at the confirmation; nothing"
BARE_DECLINE_STDIN_CLOSED = (
    "bare apply declined at the confirmation (stdin closed or interrupted); "
    "nothing applied.")
BARE_DECLINE_EMPTY = (
    "bare apply declined at the confirmation (empty answer at a decline "
    "default); nothing applied.")


def bare_decline_answered(answer: str) -> str:
    return (f"bare apply declined at the confirmation (answered '{answer}'); "
            f"nothing applied.")

# bin/ on sys.path for the pure-helper unit test below (the same
# sys.path tweak the harness's consumers of bin/ modules use).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "bin"))


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

    @slow
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

    @slow
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

    @slow
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

    def test_row37_bundle_backstop(self) -> None:
        """Row 37: a changes[] path ending in .bale-bundle is refused with
        the offending path named — the self-oracle shape from the
        landing direction."""
        def declare_bundle(m, rdir):
            m["changes"].append({
                "path": "claude/bundles/board-71.bale-bundle",
                "action": "created",
                "reason": "bundle-landing tamper", "size_bytes": 2,
                "sha256": "0" * 64,
            })
        self.assert_rejected(
            self.apply(self.tampered_tarball(declare_bundle)),
            "planner bundle in changes[]",
            "claude/bundles/board-71.bale-bundle", "row 37")

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


class BundleChangePathsUnitTest(unittest.TestCase):
    """The row-37 recognizer is pure and keys on the reserved suffix
    exactly as pack's row 33 does (bale_pack.is_bundle_file)."""

    def test_suffix_boundary(self) -> None:
        import bale_apply
        paths = [
            "x.bale-bundle",                 # bare, repo root
            "claude/bundles/y.bale-bundle",  # nested
            "notes/y.bale-bundle.md",        # a note ABOUT a bundle: fine
            "src/bale-bundle.py",            # no dot-suffix: fine
            "X.BALE-BUNDLE",                 # case-sensitive: fine
        ]
        self.assertEqual(bale_apply.bundle_change_paths(paths),
                         ["claude/bundles/y.bale-bundle", "x.bale-bundle"])
        self.assertEqual(bale_apply.bundle_change_paths([]), [],
                         msg="empty change surfaces pass vacuously")


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
    """Bare `bale apply` (board 51; widened at board 87; bounded at
    board 101): argument-less resolution.

    The ratified contract: apply with no argument resolves the newest
    response tarball answering *any* open session across the search
    paths, echoes its identity — the resolved session included — and
    takes a y/N naming that session; ambiguity — a candidate mtime tie
    — refuses loudly, never guesses. Board 51's multi-open refusal is
    retired at board 87: a response's responds_to is one string, so one
    file answers one session, and the open set is the match surface
    rather than a precondition (the master's read-only session is
    always open beside the worker at a sitting, which is exactly where
    the old refusal fired). Board 101 (v0.4.32) bounds the scan: only
    files named `response-*.tar.gz` are ever opened, only the two
    newest by st_mtime_ns (plus any file sharing the second's exact
    mtime) are examined, resolution is among the examined files only,
    and the no-candidate refusal names each examined file with why it
    was rejected. Refusals exit through the bale refusal convention
    (exit 1, remedy-naming stderr), never an argparse usage error.
    Piped stdin takes the confirmation's decline default without a
    prompt (the --supersedes precedent), so the piped runner exercises
    the refusal surface and the pty runner exercises the resolution
    happy path and the interactive decline.
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
        # can be open at once (the multi-open resolution cases).
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
                         mtime_ns: int = None, *,
                         raw_name: bool = False) -> Path:
        """Build a valid response tarball answering `sid`, drop it into
        the downloads dir, and optionally pin its mtime. The filename is
        `response-<name>.tar.gz` by default — since board 101 the name
        is the pre-filter, so only response-named files are ever opened
        (the rest of the name is arbitrary: a browser's `(1)` suffix
        passes). `raw_name=True` drops the prefix, for the pins that
        prove an un-named file is never a candidate however new it is
        and whatever it contains."""
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
        filename = f"{name}.tar.gz" if raw_name else f"response-{name}.tar.gz"
        dest = self.downloads / filename
        shutil.move(str(tarball), str(dest))
        if mtime_ns is not None:
            os.utime(dest, ns=(mtime_ns, mtime_ns))
        return dest

    def deliver_request_shaped(self, name: str, mtime_ns: int = None) -> Path:
        """A request-shaped tarball (top-level request-NNN/) in downloads
        under exactly the name given: must never be a candidate, however
        new it is — un-named, it is never opened (board 101); named
        `response-*`, its content rejects it at the peek (board 51)."""
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

    @slow
    def test_bare_resolves_newest_echoes_and_applies(self) -> None:
        sid = self.pack_session("bare")
        base = 1_700_000_000_000_000_000  # arbitrary fixed epoch ns
        self.deliver_response(sid, "older-delivery", b"older content\n",
                              mtime_ns=base)
        newest = self.deliver_response(sid, "newer-delivery",
                                       b"newer content\n",
                                       mtime_ns=base + 10 * 10**9)
        # A request-shaped tarball newer than both: never a candidate
        # (and, un-named, never opened).
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

    # -- the decline names its cause (v0.4.31, board 89) ------------------

    def _bare_declined(self, answers: str) -> str:
        """Drive the confirmation to a decline and assert the posture
        that predates the cause: exit 1 through fail(), the explicit-
        form remedy, nothing applied, the session open, and the
        pre-board-89 cause-less line gone."""
        sid = self.pack_session("bare-cause")
        self.deliver_response(sid, "sole-delivery", b"declined content\n")
        exit_code, output = run_bale_pty(
            self.install, ["apply"], cwd=self.repo, env=self.env,
            answers=answers)
        self.assertEqual(exit_code, 1,
                         msg=f"decline must refuse; output:\n{output}")
        self.assertIn(f"Apply this tarball against session {sid}? [y/N]",
                      output)
        self.assertIn("[bale] error: bare apply declined at the "
                      "confirmation (", output)
        self.assertIn("nothing applied. Name the tarball explicitly if the "
                      "resolution picked the wrong file: bale apply <path>.",
                      output)
        self.assertNotIn(BARE_DECLINE_CAUSELESS, output)
        # One delivery: nothing else was examined, so no alternative is
        # named beneath the placeholder remedy (board 101).
        self.assertNotIn("The other examined file", output)
        self.assert_nothing_applied(sid)
        return output

    def test_bare_enter_at_the_decline_default_names_itself(self) -> None:
        output = self._bare_declined("\n")
        self.assertIn(BARE_DECLINE_EMPTY, output)

    def test_bare_n_is_quoted_back(self) -> None:
        output = self._bare_declined("n\n")
        self.assertIn(bare_decline_answered("n"), output)

    def test_bare_stray_answer_is_quoted_back_stripped_and_lowercased(self) -> None:
        output = self._bare_declined("  NO \n")
        self.assertIn(bare_decline_answered("no"), output)

    def test_bare_stdin_closed_at_the_prompt_names_itself(self) -> None:
        output = self._bare_declined(EOT)
        self.assertIn(BARE_DECLINE_STDIN_CLOSED, output)

    # -- the refusal surface (piped: decline default, no prompt) ---------

    def test_bare_no_open_session(self) -> None:
        result = self.bare_apply_piped()
        self.assert_refused(result, "no session is open", "bale pack",
                            "name the tarball explicitly")

    # -- multi-open resolution (board 87) ---------------------------------

    @slow
    def test_bare_resolves_across_open_sessions_at_a_sitting(self) -> None:
        """The desk's own shape: the master's read-only session and a
        scoped worker session both open, one response answering the
        scoped one. Bare apply resolves it, names the session in the
        echo and the y/N, and a `y` applies — the sitting where board
        51's multi-open refusal used to fire on every run."""
        master = self.pack_session("bare-master", ["--read-only"])
        worker = self.pack_session("bare-worker",
                                   ["--write", "hello.txt"])
        delivered = self.deliver_response(worker, "for-worker",
                                          b"worker content\n")
        exit_code, output = run_bale_pty(
            self.install, ["apply"], cwd=self.repo, env=self.env,
            answers="y\n\n")
        self.assertEqual(exit_code, 0,
                         msg=f"bare apply should resolve across the open "
                             f"set and merge; output:\n{output}")
        self.assertNotIn("more than one session open", output)
        # The echo names the path and the resolved session, and says
        # which open sessions were on the match surface.
        self.assertIn(str(delivered), output)
        self.assertIn(f"responds_to: {worker}", output)
        self.assertIn("2 open sessions", output)
        self.assertIn(master, output)
        # The y/N asks about the resolved session by name.
        self.assertIn(f"against session {worker}?", output)
        self.assertEqual(
            (self.repo / "hello.txt").read_text(encoding="utf-8"),
            "worker content\n")
        run_checked(["git", "rev-parse", "--verify",
                     f"refs/tags/applied/{worker}"],
                    cwd=self.repo, env=self.genv)
        # The master session it did not answer stays open, untouched.
        self.assertTrue(
            (self.repo / ".bale" / "sessions" / master / "open").is_file())

    def test_bare_multi_open_newest_wins_whichever_session(self) -> None:
        """Two scoped sessions open, a response for each: newest by
        st_mtime_ns wins regardless of which session it answers, and
        the echo names that session. Piped, so the decline default
        refuses after the echo — the resolution itself is what this
        pins."""
        sid_a = self.pack_session("bare-multi-a",
                                  ["--write", "hello.txt"])
        sid_b = self.pack_session("bare-multi-b",
                                  ["--write", "other.txt"])
        base = 1_700_000_000_000_000_000
        self.deliver_response(sid_a, "for-a-older", b"for session a\n",
                              mtime_ns=base)
        newest = self.deliver_response(sid_b, "for-b-newer",
                                       b"for session b\n",
                                       mtime_ns=base + 10 * 10**9)
        result = self.bare_apply_piped()
        self.assert_refused(result, "not a TTY", str(newest))
        self.assertNotIn("more than one session open",
                         result.stdout + result.stderr)
        self.assertIn(str(newest), result.stdout)
        self.assertIn(f"responds_to: {sid_b}", result.stdout)
        self.assertIn("2 candidates answered an open session",
                      result.stdout)
        self.assert_nothing_applied(sid_a)
        self.assertTrue(
            (self.repo / ".bale" / "sessions" / sid_b / "open").is_file())

    def test_bare_multi_open_tie_names_each_session(self) -> None:
        """An exact mtime tie across sessions still refuses (board 51's
        never-guess rule stands), and the tie listing names the session
        each tied path answers so the operator can pick by intent."""
        sid_a = self.pack_session("bare-tie-a",
                                  ["--write", "hello.txt"])
        sid_b = self.pack_session("bare-tie-b",
                                  ["--write", "other.txt"])
        base = 1_700_000_000_000_000_000
        first = self.deliver_response(sid_a, "tie-a", b"tie a\n",
                                      mtime_ns=base)
        second = self.deliver_response(sid_b, "tie-b", b"tie b\n",
                                       mtime_ns=base)
        result = self.bare_apply_piped()
        self.assert_refused(result, "share the newest modification time",
                            "never guesses", str(first), str(second),
                            f"(answers {sid_a})", f"(answers {sid_b})")
        self.assert_nothing_applied(sid_a)

    def test_bare_multi_open_no_candidates_names_every_session(self) -> None:
        """With several sessions open and nothing answering any of
        them, the refusal names the whole match surface."""
        sid_a = self.pack_session("bare-nocand-a",
                                  ["--write", "hello.txt"])
        sid_b = self.pack_session("bare-nocand-b",
                                  ["--write", "other.txt"])
        self.deliver_response("2020-01-01-stale-001", "stale-response",
                              b"stale\n")
        result = self.bare_apply_piped()
        self.assert_refused(
            result,
            "no response tarball answering any open session",
            "2 open", sid_a, sid_b,
            "name the path explicitly")
        self.assert_nothing_applied(sid_a)

    def test_bare_no_candidates_and_request_never_a_candidate(self) -> None:
        sid = self.pack_session("bare-nocand")
        # Everything present is a non-candidate: a request-shaped tarball
        # and raw junk (both un-named, so never opened — board 101) and
        # a response-named tarball answering a session that is not open
        # (opened, rejected by content, named in the refusal).
        self.deliver_request_shaped("request-only")
        stale = self.deliver_response("2020-01-01-stale-001",
                                      "stale-response", b"stale\n")
        junk = self.downloads / "junk.tar.gz"
        junk.write_bytes(b"not a gzip stream")
        result = self.bare_apply_piped()
        self.assert_refused(
            result,
            f"no response tarball answering open session {sid}",
            "searched (response-*.tar.gz, non-recursive",
            str(self.downloads),
            "(cwd)",
            "examined and rejected:",
            f"{stale}  — answers 2020-01-01-stale-001, which is not an "
            f"open session",
            "name the path explicitly")
        # The un-named files are not part of the scan at all: not
        # examined, not counted, not mentioned.
        self.assertNotIn("request-only", result.stdout + result.stderr)
        self.assertNotIn("junk.tar.gz", result.stdout + result.stderr)
        self.assertNotIn("not examined", result.stderr)
        self.assert_nothing_applied(sid)

    def test_bare_no_named_files_says_so(self) -> None:
        """Nothing named response-*.tar.gz anywhere: the refusal says the
        examined set was empty rather than listing nothing."""
        sid = self.pack_session("bare-nonamed")
        self.deliver_request_shaped("request-only")
        result = self.bare_apply_piped()
        self.assert_refused(
            result,
            f"no response tarball answering open session {sid}",
            "examined: nothing — no response-*.tar.gz file",
            "name the path explicitly")
        self.assertNotIn("examined and rejected", result.stderr)
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

    # -- the bounded scan (board 101, v0.4.32) ----------------------------

    def test_bare_name_prefilter_never_opens_unnamed_files(self) -> None:
        """Rule 1: only response-*.tar.gz files are opened. The proof is
        behavioral, in both directions: a `junk.tar.gz` and a
        `request-*.tar.gz` newer than the real delivery each carry VALID
        response content answering the open session — if either were
        opened it would be a candidate and, being newest, would win and
        be echoed. A third un-named file is unreadable — if it were
        opened, --verbose would print a skip line naming it. None of the
        three appears anywhere in the output; the response-named file
        resolves; the --verbose count says one named file was found."""
        sid = self.pack_session("bare-prefilter")
        base = 1_700_000_000_000_000_000
        real = self.deliver_response(sid, "real", b"real content\n",
                                     mtime_ns=base)
        junk = self.deliver_response(sid, "junk", b"junk content\n",
                                     mtime_ns=base + 10 * 10**9,
                                     raw_name=True)
        misnamed = self.deliver_response(
            sid, "request-2026-01-01-misnamed-001", b"misnamed content\n",
            mtime_ns=base + 20 * 10**9, raw_name=True)
        unreadable = self.downloads / "unreadable.tar.gz"
        unreadable.write_bytes(b"not a gzip stream")
        os.utime(unreadable, ns=(base + 30 * 10**9, base + 30 * 10**9))
        unreadable.chmod(0)
        try:
            result = self.bare_apply_piped("--verbose")
        finally:
            unreadable.chmod(0o644)
        self.assert_refused(result, "not a TTY", str(real))
        combined = result.stdout + result.stderr
        self.assertIn(str(real), result.stdout)
        self.assertIn(f"responds_to: {sid}", result.stdout)
        self.assertIn("1 response-*.tar.gz file(s) found; examined the 1 "
                      "newest", result.stdout)
        for never_opened in (junk, misnamed, unreadable):
            self.assertNotIn(never_opened.name, combined,
                             msg=f"{never_opened.name} is not named "
                                 f"response-*.tar.gz and must never be "
                                 f"opened, listed, or counted")
        self.assert_nothing_applied(sid)

    def test_bare_cap_examines_two_newest_and_names_both(self) -> None:
        """Rule 2 and rule 3 together: three response-named files, the
        two newest non-candidates (one answers a closed session, one is
        request content under a response name) and the oldest a real
        candidate. The oldest is never opened — resolution refuses —
        and the refusal names both examined files with the reason each
        was rejected, plus the count of older named files it left
        unopened, so the stale download does not go silent."""
        sid = self.pack_session("bare-cap")
        base = 1_700_000_000_000_000_000
        oldest = self.deliver_response(sid, "oldest-real", b"real\n",
                                       mtime_ns=base)
        stale = self.deliver_response("2020-01-01-stale-001", "stale",
                                      b"stale\n",
                                      mtime_ns=base + 10 * 10**9)
        misnamed = self.deliver_request_shaped(
            "response-2026-01-01-actually-a-request-001",
            mtime_ns=base + 20 * 10**9)
        result = self.bare_apply_piped()
        self.assert_refused(
            result,
            f"no response tarball answering open session {sid}",
            "examined and rejected:",
            f"{misnamed}  — not a candidate: no response-NNN/manifest.json "
            f"member (not a response tarball)",
            f"{stale}  — answers 2020-01-01-stale-001, which is not an "
            f"open session",
            "1 older response-*.tar.gz file(s) not examined: bare apply "
            "opens only the two newest",
            "name the path explicitly")
        self.assertNotIn(str(oldest), result.stdout + result.stderr,
                         msg="the third-newest file is never opened, so "
                             "it is never named as examined")
        self.assert_nothing_applied(sid)

    def test_bare_second_newest_wins_when_newest_is_not_a_candidate(self) -> None:
        """Rule 2's resolution order: the newest examined file answers a
        closed session, the second answers the open one — the second
        wins, and the echo names it. Piped, so the decline default
        refuses after the echo; the resolution is what this pins."""
        sid = self.pack_session("bare-second")
        base = 1_700_000_000_000_000_000
        second = self.deliver_response(sid, "second", b"second\n",
                                       mtime_ns=base)
        newest = self.deliver_response("2020-01-01-stale-001", "newest",
                                       b"stale\n",
                                       mtime_ns=base + 10 * 10**9)
        result = self.bare_apply_piped()
        self.assert_refused(result, "not a TTY", str(second))
        self.assertIn(str(second), result.stdout)
        self.assertIn(f"responds_to: {sid}", result.stdout)
        self.assertIn("1 examined tarball(s) not candidates", result.stdout)
        self.assertNotIn("newest modification time won", result.stdout,
                         msg="one candidate: nothing competed")
        self.assertNotIn(str(newest), result.stdout)
        self.assert_nothing_applied(sid)

    def test_bare_tie_at_second_rank_still_refuses(self) -> None:
        """The tie rule survives the cap: the newest examined file is a
        non-candidate and the next two share an exact mtime and both
        answer the open session — both are examined (a file sharing the
        second's mtime is in the examined set) and the tie refuses,
        naming each."""
        sid = self.pack_session("bare-tie2")
        base = 1_700_000_000_000_000_000
        tie_a = self.deliver_response(sid, "tie-a", b"tie a\n",
                                      mtime_ns=base)
        tie_b = self.deliver_response(sid, "tie-b", b"tie b\n",
                                      mtime_ns=base)
        self.deliver_response("2020-01-01-stale-001", "newest-stale",
                              b"stale\n", mtime_ns=base + 10 * 10**9)
        result = self.bare_apply_piped()
        self.assert_refused(result, "share the newest modification time",
                            "never guesses", str(tie_a), str(tie_b))
        self.assert_nothing_applied(sid)

    def test_bare_verbose_lists_each_examined_skip(self) -> None:
        """--verbose keeps its per-file skip lines for the examined
        files, and says how many named files were found, examined, and
        left unopened."""
        sid = self.pack_session("bare-verbose")
        base = 1_700_000_000_000_000_000
        self.deliver_response(sid, "oldest-real", b"real\n", mtime_ns=base)
        stale = self.deliver_response("2020-01-01-stale-001", "stale",
                                      b"stale\n",
                                      mtime_ns=base + 10 * 10**9)
        misnamed = self.deliver_request_shaped(
            "response-2026-01-01-actually-a-request-001",
            mtime_ns=base + 20 * 10**9)
        result = self.bare_apply_piped("--verbose")
        self.assert_refused(result, "examined and rejected:")
        self.assertIn("3 response-*.tar.gz file(s) found; examined the 2 "
                      "newest by modification time (1 older not opened)",
                      result.stdout)
        self.assertIn(f"bare apply: skipped {stale} — answers "
                      f"2020-01-01-stale-001, which is not an open session",
                      result.stdout)
        self.assertIn(f"bare apply: skipped {misnamed} — not a candidate: "
                      f"no response-NNN/manifest.json member",
                      result.stdout)
        self.assertNotIn("--verbose lists each", result.stderr)

    def test_bare_decline_names_the_other_candidate(self) -> None:
        """The row-89 decline remedy's `<path>` placeholder gains a
        concrete alternative when the other examined file also answered
        an open session: one `bale apply <second>` line beneath the
        byte-exact table line, naming the session it answers."""
        sid = self.pack_session("bare-alt")
        base = 1_700_000_000_000_000_000
        second = self.deliver_response(sid, "second", b"second\n",
                                       mtime_ns=base)
        newest = self.deliver_response(sid, "newest", b"newest\n",
                                       mtime_ns=base + 10 * 10**9)
        exit_code, output = run_bale_pty(
            self.install, ["apply"], cwd=self.repo, env=self.env,
            answers="n\n")
        self.assertEqual(exit_code, 1,
                         msg=f"decline must refuse; output:\n{output}")
        self.assertIn(str(newest), output)
        self.assertIn(bare_decline_answered("n"), output)
        self.assertIn("bale apply <path>.", output)
        self.assertIn("The other examined file also answers an open "
                      "session:", output)
        self.assertIn(f"bale apply {second}  (answers {sid})", output)
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

    def test_bare_piped_remedy_line_is_quoted(self) -> None:
        """Board 102 (the board-101 rider): the non-TTY refusal's
        `bale apply <path>` remedy is shlex-quoted, matching the decline
        line's alternative a few lines below it in the source. A
        browser's `(1)` twin carries a space and parens, so the unquoted
        line was a paste that never worked; the quoted one is."""
        sid = self.pack_session("bare-piped-quoted")
        twin = self.deliver_response(sid, "twin (1)", b"twin content\n")
        self.assertIn(" ", twin.name)
        result = self.bare_apply_piped()
        self.assert_refused(result, "not a TTY", "decline default",
                            f"bale apply '{twin}'")
        self.assertNotIn(f"prompt: bale apply {twin}", result.stderr)
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

    @slow
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


class ExplicitNameMissTest(unittest.TestCase):
    """The explicit-name miss surface (board 102, v0.4.33).

    `bale apply <name>`, `bale retry <name>` and `bale handoff <name>`
    resolve a relative name through cwd and then each configured
    `apply.search_paths` directory (bin/bale's resolve_inbound_path);
    a miss refuses naming every directory consulted. Board 102 adds the
    near-name listing to that refusal: every `*.tar.gz` file in the
    consulted directories whose name starts with the typed name minus
    its `.tar.gz` suffix, rendered as a complete `bale <verb> <path>`
    command line for the verb the user typed — absolute, shlex-quoted
    (a path with a space or parens gets single quotes: the
    load-bearing part, since a browser's second download of the same
    name is `<name> (1).tar.gz`), newest first by mtime. With zero
    candidates the refusal is byte-identical to the pre-listing form.

    The resolver never opens a candidate — the listing is a directory
    scan and a stat — so the fixtures are empty files with pinned
    mtimes; nothing here needs an open session, and every verb refuses
    at resolution before any session state is touched.
    """

    PREFIX = "response-2026-09-15-near-001"

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-nearname-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.downloads = self.tmp / "downloads"
        self.downloads.mkdir()
        (self.repo / "bale.toml").write_text(
            "[apply]\n"
            f"search_paths = [\"{self.downloads}\"]\n",
            encoding="utf-8")

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def drop(self, name: str, *, where: Path = None,
             mtime_ns: int = None) -> Path:
        """An empty file under `where` (downloads by default) with a
        pinned mtime — content is irrelevant, the resolver only lists."""
        dest = (where or self.downloads) / name
        dest.write_bytes(b"")
        if mtime_ns is not None:
            os.utime(dest, ns=(mtime_ns, mtime_ns))
        return dest

    def miss(self, verb: str, typed: str):
        result = run_bale(self.install, [verb, typed],
                          cwd=self.repo, env=self.env)
        self.assertEqual(
            result.returncode, 1,
            msg=f"expected the not-found refusal (exit 1); "
                f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn(f"tarball not found: {typed}", result.stderr)
        self.assertIn("  searched:", result.stderr)
        self.assertIn(f"    {self.downloads}", result.stderr)
        return result

    @staticmethod
    def listing_lines(stderr: str) -> list:
        """The `bale <verb> <path>` lines under the near-name header,
        in emitted order; empty when the header is absent."""
        lines = stderr.splitlines()
        for i, line in enumerate(lines):
            if line.strip() == "near-name candidates (newest first):":
                return [l.strip() for l in lines[i + 1:]
                        if l.startswith("    bale ")]
        return []

    # -- the listing -----------------------------------------------------

    def test_apply_miss_lists_near_names_newest_first(self) -> None:
        base = 1_700_000_000_000_000_000
        older = self.drop(f"{self.PREFIX}-older.tar.gz", mtime_ns=base)
        newest = self.drop(f"{self.PREFIX}-newest.tar.gz",
                           mtime_ns=base + 20 * 10**9)
        middle = self.drop(f"{self.PREFIX}-middle.tar.gz",
                           mtime_ns=base + 10 * 10**9)
        result = self.miss("apply", f"{self.PREFIX}.tar.gz")
        self.assertEqual(
            self.listing_lines(result.stderr),
            [f"bale apply {newest}", f"bale apply {middle}",
             f"bale apply {older}"])

    def test_retry_miss_renders_the_retry_verb(self) -> None:
        twin = self.drop(f"{self.PREFIX}-v2.tar.gz")
        result = self.miss("retry", f"{self.PREFIX}.tar.gz")
        self.assertEqual(self.listing_lines(result.stderr),
                         [f"bale retry {twin}"])
        self.assertNotIn("bale apply ", result.stderr)

    def test_handoff_miss_renders_the_handoff_verb(self) -> None:
        twin = self.drop(f"{self.PREFIX}-v2.tar.gz")
        result = self.miss("handoff", f"{self.PREFIX}.tar.gz")
        self.assertEqual(self.listing_lines(result.stderr),
                         [f"bale handoff {twin}"])

    def test_space_and_parens_are_single_quoted(self) -> None:
        """The load-bearing case: the browser's `(1)` twin pastes back
        as one argument. A candidate without shell metacharacters stays
        bare, so the two lines differ only where quoting is needed."""
        twin = self.drop(f"{self.PREFIX} (1).tar.gz")
        plain = self.drop(f"{self.PREFIX}-plain.tar.gz")
        for verb in ("apply", "retry"):
            with self.subTest(verb=verb):
                result = self.miss(verb, f"{self.PREFIX}.tar.gz")
                lines = self.listing_lines(result.stderr)
                self.assertIn(f"bale {verb} '{twin}'", lines)
                self.assertIn(f"bale {verb} {plain}", lines)
                self.assertNotIn(f"bale {verb} {twin}", lines)

    def test_prefix_is_the_typed_name_minus_suffix(self) -> None:
        """Only names starting with the typed name's stem are near: a
        different sid, a name that merely contains the stem, and a
        non-.tar.gz file sharing the stem are all silent."""
        near = self.drop(f"{self.PREFIX}-near.tar.gz")
        self.drop("response-2026-09-15-other-001.tar.gz")
        self.drop(f"prefix-{self.PREFIX}.tar.gz")
        self.drop(f"{self.PREFIX}.tar.gz.part")
        self.drop(f"{self.PREFIX}.md")
        result = self.miss("apply", f"{self.PREFIX}.tar.gz")
        self.assertEqual(self.listing_lines(result.stderr),
                         [f"bale apply {near}"])

    def test_typed_name_without_suffix_is_its_own_prefix(self) -> None:
        exact = self.drop(f"{self.PREFIX}.tar.gz")
        result = self.miss("apply", self.PREFIX)
        self.assertEqual(self.listing_lines(result.stderr),
                         [f"bale apply {exact}"])

    def test_cwd_candidates_are_listed_too(self) -> None:
        """cwd is consulted before the configured directories for the
        exact match, so its near-names are candidates as well; a file
        reachable from both cwd and a search path lists once."""
        base = 1_700_000_000_000_000_000
        in_cwd = self.drop(f"{self.PREFIX}-here.tar.gz", where=self.repo,
                           mtime_ns=base + 10 * 10**9)
        in_dl = self.drop(f"{self.PREFIX}-there.tar.gz", mtime_ns=base)
        result = self.miss("apply", f"{self.PREFIX}.tar.gz")
        self.assertEqual(self.listing_lines(result.stderr),
                         [f"bale apply {in_cwd.resolve()}",
                          f"bale apply {in_dl}"])
        # Dedupe: cwd doubling as a configured search path.
        (self.repo / "bale.toml").write_text(
            "[apply]\n"
            f"search_paths = [\"{self.repo}\", \"{self.downloads}\"]\n",
            encoding="utf-8")
        result = self.miss("apply", f"{self.PREFIX}.tar.gz")
        lines = self.listing_lines(result.stderr)
        self.assertEqual(lines.count(f"bale apply {in_cwd.resolve()}"), 1)

    def test_zero_candidates_leaves_the_refusal_unchanged(self) -> None:
        self.drop("response-2026-09-15-other-001.tar.gz")
        for verb in ("apply", "retry", "handoff"):
            with self.subTest(verb=verb):
                result = self.miss(verb, f"{self.PREFIX}.tar.gz")
                self.assertNotIn("near-name", result.stderr)
                self.assertNotIn(f"bale {verb} ", result.stderr)
                # The refusal ends at the searched list: nothing after
                # the last consulted directory.
                self.assertTrue(
                    result.stderr.rstrip().endswith(str(self.downloads)),
                    msg=f"unexpected trailer after the searched list:"
                        f"\n{result.stderr}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
