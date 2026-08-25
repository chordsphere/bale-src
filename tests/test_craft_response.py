#!/usr/bin/env python3
"""Hermetic tests for tools/craft_response.py (session 007).

Runs the crafter as a subprocess against programmatically built tempdir
response directories — no bale install, no tests/harness.py, stdlib
only. Also asserts, unit-shaped, that bale_pack's injected-file surface
ships the craft tool (the request deliberately runs no bin/bale E2E;
build.sh's tree-coverage guard and validate.sh's install rows backstop
the rest).

Two design-contract guards ride along:
- the crafter shares no code with the judge (no response_lint import in
  either direction), per the request's load-bearing constraint;
- an unfilled skeleton is invalid to the judge — crafted, completed
  output passes response_lint; crafted, *unfilled* output does not.

Session 22c extends the surface to all three response kinds (--kind
bailout / clarification). The new classes prove: back-compat on the
normal path (--kind normal is byte-identical to the default), the two
new kinds' unfilled-cannot-pass / filled-passes round trips against an
actual response_lint run, the schema key-set drift bridges (the emitted
skeletons match the repo schemas' required sets — the crafter embeds
neither schema, per the one-home rule), and refuse-overwrite across the
enlarged artifact sets.

Session 22d adds --probe SLUG (the TARBALL.md 4.2 paste-back probe
skeleton, emitted to stdout). CraftProbeMode proves: the emission's
fixed shape (purpose header with the read-only line verbatim, probe()
wrapper, slug-carrying sentinels, capture-then-count integrity
trailer) plus loud TODO placeholders; that the emission is valid bash
(`bash -n`) AND runs read-only with a self-consistent integrity count;
mutual exclusion against every response-directory mode and flag; and
slug hygiene. Deliberately no lint round trip: no judge exists for
probes — they are chat paste-backs the architect audits by eye (4.2).

Session 008 (board 31) adds --validation-epilogue, the paste-ready
TARBALL.md 7.3 reconciliation epilogue plus 7.7 exec-bit assertions.
CraftValidationEpilogue proves the emission's semantics against 7.3's
contract by executing it, that it suggests no checks (worker judgment
stays worker judgment), and that the assertions come from the same
--executable list as apply.sh's chmod lines. PackInjectionSurface
gains a skipUnless(bin/) rider so tools-only sandboxes run
clean-green; this repo ships bin/, so the class still runs here.

Session 2026-08-15-002 adds two surfaces. CraftEpilogueFragments
covers the fold-in riders: --fragment {definitions,assertions,call}
emits each epilogue part separably (pasting the definitions can never
fire reconcile_claims early; the parts concatenate byte-identically
to the combined emission), and the reconciliation label column is
capped so one pathological label can't drag every row's alignment.
CraftDocAssertions covers --doc-assertions, the parameterized
emissions for the DOCS.md 9 / CODE.md 10 contract rows (INDEX
coherence, ADR append-only + sanctioned flips by reverse transform +
sequential numbering, prune declarations, index-header coherence) —
each proven by executing the emitted block against synthetic staging
trees, pass and fail sides both.

Session board-49b adds --bundle STEM (the planner-bundle emission
half — the desk stops hand-composing argv and hash blocks) plus the
opt-in probe clipboard epilogue (registry fold-in). CraftBundleEmission
proves the container against the consumer's own contract: flat archive
= exactly {bundle.json} ∪ declared members, hashes over LF-normalized
bytes (a CRLF input still verifies), the null slots' uniform shape,
deterministic bytes, the idempotent re-run, and the stdout paste line
carrying the bundle FILENAME only. CraftBundleHygiene proves the
refusals (delivery flags bare and =-glued, a leading 'pack' verb,
--no-readme, stem shapes, intent vocabulary and duplicates, the
TODO(brief) sentinel, hollow member files) and the mode's mutual
exclusion, both directions against --probe and the response-directory
surface. CraftProbeClipboard proves the epilogue's contract per the
fold-in text: emitted only when [probe] clipboard_command is readable
(./bale.toml then ./context/bale.toml), sentinel banners always,
runtime tee loud on success and failure and never failing the probe,
remedy text on the unset and misconfigured paths. BundlePackParity
(skipUnless bin/, the PackInjectionSurface rider pattern) pins the
re-declared constants equal to bale_pack's, the TODO(brief) literal
still present in the pack source, and the emitted bundle.json passing
validate_bundle_manifest — the producer against the consumer's gate.
The full producer→consumer E2E (a crafter-emitted bundle through a
real `bale open`) lives in tests/test_open_verb.py.

Run:  python3 -m unittest tests.test_craft_response -v
  or: python3 -m unittest discover -s tests -p 'test_craft_response.py'
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CRAFT = REPO / "tools" / "craft_response.py"
LINT = REPO / "tools" / "response_lint.py"
PACK_MODULE = REPO / "bin" / "bale_pack.py"


def run_craft(*argv: str, cwd: Path | None = None
              ) -> subprocess.CompletedProcess:
    """cwd is None = inherit (the historical shape); the bundle and
    clipboard tests pass an explicit tempdir because those surfaces
    read the current directory (output landing, bale.toml lookup)."""
    return subprocess.run(
        [sys.executable, str(CRAFT), *argv],
        capture_output=True, text=True, cwd=cwd,
    )


def make_response_dir(tmp: Path, files: dict[str, bytes]) -> Path:
    """Build response-XXX/files/<rel> with the given contents."""
    rdir = tmp / "response-042"
    for rel, body in files.items():
        dst = rdir / "files" / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(body)
    rdir.mkdir(parents=True, exist_ok=True)
    return rdir


class CraftManifestSkeleton(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_mirror_walk_computes_and_strips(self):
        body_a = b"alpha\n"
        body_b = b"x" * 1024
        rdir = make_response_dir(self.tmp, {
            "src/deep/nested/b.bin": body_b,
            "a.txt": body_a,
        })
        cp = run_craft(str(rdir), "--sid", "2026-07-29-fixture-042")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        manifest = json.loads(cp.stdout)

        self.assertEqual(manifest["session_id"], "2026-07-29-fixture-042")
        self.assertEqual(manifest["responds_to"], "2026-07-29-fixture-042")
        self.assertIsNone(manifest["corrects"])
        self.assertEqual(manifest["response_kind"], "normal")
        self.assertEqual(manifest["summary"], "")
        self.assertEqual(manifest["deferred"], [])
        self.assertEqual(manifest["validation_will_run"], [])
        self.assertEqual(manifest["claims"], {})

        changes = manifest["changes"]
        self.assertEqual([c["path"] for c in changes],
                         ["a.txt", "src/deep/nested/b.bin"])  # sorted, stripped
        by_path = {c["path"]: c for c in changes}
        self.assertEqual(by_path["a.txt"]["size_bytes"], len(body_a))
        self.assertEqual(by_path["a.txt"]["sha256"],
                         hashlib.sha256(body_a).hexdigest())
        self.assertEqual(by_path["src/deep/nested/b.bin"]["size_bytes"],
                         len(body_b))
        self.assertEqual(by_path["src/deep/nested/b.bin"]["sha256"],
                         hashlib.sha256(body_b).hexdigest())
        for c in changes:
            self.assertEqual(c["action"], "")  # worker's, never generated
            self.assertEqual(c["reason"], "")  # worker's, never generated

    def test_deleted_stub_literals(self):
        rdir = make_response_dir(self.tmp, {"kept.txt": b"k\n"})
        cp = run_craft(str(rdir), "--sid", "s-042",
                       "--deleted", "old/gone.py",
                       "--deleted", "also/gone.md")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        changes = json.loads(cp.stdout)["changes"]
        stubs = [c for c in changes if c["action"] == "deleted"]
        self.assertEqual([c["path"] for c in stubs],
                         ["also/gone.md", "old/gone.py"])  # sorted after mirror
        for c in stubs:
            self.assertEqual(c["size_bytes"], 0)
            self.assertIsNone(c["sha256"])
            self.assertEqual(c["reason"], "")
        # Mirror entries precede stubs.
        self.assertEqual(changes[0]["path"], "kept.txt")

    def test_empty_mirror_deleted_only(self):
        rdir = self.tmp / "response-042"
        rdir.mkdir()
        cp = run_craft(str(rdir), "--sid", "s-042", "--deleted", "gone.txt")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        changes = json.loads(cp.stdout)["changes"]
        self.assertEqual(len(changes), 1)
        self.assertEqual(changes[0]["action"], "deleted")

    def test_changes_only_needs_no_sid(self):
        rdir = make_response_dir(self.tmp, {"f.txt": b"f\n"})
        cp = run_craft(str(rdir), "--changes-only")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        arr = json.loads(cp.stdout)
        self.assertIsInstance(arr, list)
        self.assertEqual(arr[0]["path"], "f.txt")


class CraftApplyScaffold(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_noop_verbatim(self):
        rdir = make_response_dir(self.tmp, {"f.txt": b"f\n"})
        cp = run_craft(str(rdir), "--apply-only")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertEqual(cp.stdout, textwrap.dedent("""\
            #!/usr/bin/env bash
            # No additional operations for this session.
            exit 0
        """))

    def test_rm_then_chmod_order(self):
        rdir = make_response_dir(self.tmp, {"scripts/run.sh": b"#!/bin/sh\n"})
        cp = run_craft(str(rdir), "--apply-only",
                       "--deleted", "legacy/dead.sh",
                       "--executable", "scripts/run.sh")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        out = cp.stdout
        self.assertIn("set -euo pipefail", out)
        self.assertIn("rm -f legacy/dead.sh", out)
        self.assertIn("chmod +x scripts/run.sh", out)
        self.assertLess(out.index("rm -f legacy/dead.sh"),
                        out.index("chmod +x scripts/run.sh"))
        # The scaffold must be syntactically valid bash.
        script = self.tmp / "apply.sh"
        script.write_text(out)
        chk = subprocess.run(["bash", "-n", str(script)],
                             capture_output=True, text=True)
        self.assertEqual(chk.returncode, 0, chk.stderr)

    def test_shell_significant_path_is_quoted(self):
        rdir = make_response_dir(self.tmp, {"has space/f.sh": b"#!/bin/sh\n"})
        cp = run_craft(str(rdir), "--apply-only",
                       "--executable", "has space/f.sh")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("chmod +x 'has space/f.sh'", cp.stdout)


class CraftWriteMode(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def test_write_refuse_force_cycle(self):
        rdir = make_response_dir(self.tmp, {"f.txt": b"f\n"})
        cp = run_craft(str(rdir), "--sid", "s-042", "--write")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertTrue((rdir / "manifest.json").is_file())
        self.assertTrue((rdir / "apply.sh").is_file())
        json.loads((rdir / "manifest.json").read_text())  # parses

        cp2 = run_craft(str(rdir), "--sid", "s-042", "--write")
        self.assertEqual(cp2.returncode, 2)
        self.assertIn("--force", cp2.stderr)

        cp3 = run_craft(str(rdir), "--sid", "s-042", "--write", "--force")
        self.assertEqual(cp3.returncode, 0, cp3.stderr)


class CraftArgumentHygiene(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.rdir = make_response_dir(self.tmp, {"f.txt": b"f\n"})

    def check_error(self, *argv: str, needle: str):
        cp = run_craft(*argv)
        self.assertEqual(cp.returncode, 2, cp.stderr)
        self.assertIn(needle, cp.stderr)

    def test_missing_dir(self):
        self.check_error(str(self.tmp / "nope"), "--sid", "s",
                         needle="not found")

    def test_missing_sid(self):
        self.check_error(str(self.rdir), needle="--sid is required")

    def test_deleted_collides_with_mirror(self):
        self.check_error(str(self.rdir), "--sid", "s",
                         "--deleted", "f.txt", needle="also exists under")

    def test_executable_not_in_mirror(self):
        self.check_error(str(self.rdir), "--sid", "s",
                         "--executable", "ghost.sh",
                         needle="no file under files/")

    def test_unsafe_paths_rejected(self):
        for bad, needle in (("/etc/passwd", "absolute"),
                            ("../escape.txt", "'..'"),
                            ("files/f.txt", "mirror prefix"),
                            ("dir/", "trailing slash")):
            with self.subTest(bad=bad):
                self.check_error(str(self.rdir), "--sid", "s",
                                 "--deleted", bad, needle=needle)

    def test_duplicate_flag_values_rejected(self):
        self.check_error(str(self.rdir), "--sid", "s",
                         "--deleted", "x.txt", "--deleted", "x.txt",
                         needle="duplicate")

    def test_force_without_write(self):
        self.check_error(str(self.rdir), "--sid", "s", "--force",
                         needle="--force")


class CraftJudgeSeparation(unittest.TestCase):
    """The load-bearing constraint: crafter and judge share nothing."""

    def test_no_cross_imports(self):
        # Prose mentions are fine (the crafter points workers at the
        # judge); imports are the violation. Parse, don't grep.
        import ast
        for src_path, forbidden in ((CRAFT, "response_lint"),
                                    (LINT, "craft_response")):
            tree = ast.parse(src_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    names = [a.name for a in node.names]
                elif isinstance(node, ast.ImportFrom):
                    names = [node.module or ""]
                else:
                    continue
                for name in names:
                    self.assertNotIn(
                        forbidden, name,
                        f"{src_path.name} imports {name!r} — the crafter "
                        "and the judge share no code")

    def test_crafted_and_completed_passes_the_judge(self):
        """Craft → worker fills → lint judges clean. The self-check that
        stays on the right side of the self-oracle line: the judge judging
        crafted output, never the crafter checking itself."""
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            rdir = make_response_dir(tmp, {"src/new.txt": b"content\n"})
            sid = "2026-07-29-fixture-042"
            cp = run_craft(str(rdir), "--sid", sid, "--write")
            self.assertEqual(cp.returncode, 0, cp.stderr)

            # The worker's half: fill the judgment fields.
            mpath = rdir / "manifest.json"
            manifest = json.loads(mpath.read_text())
            manifest["summary"] = "fixture response for the craft->lint test"
            for c in manifest["changes"]:
                c["action"] = "created"
                c["reason"] = "fixture file for the end-to-end test"
            mpath.write_text(json.dumps(manifest, indent=2) + "\n")
            # response_lint requires validation.sh; the crafter deliberately
            # does not scaffold it (it is the worker's hypothesis test).
            (rdir / "validation.sh").write_text(
                "#!/usr/bin/env bash\nexit 0\n")

            lint = subprocess.run(
                [sys.executable, str(LINT), str(rdir)],
                capture_output=True, text=True)
            self.assertEqual(lint.returncode, 0,
                             f"judge found findings:\n{lint.stdout}\n{lint.stderr}")

    def test_unfilled_skeleton_fails_the_judge(self):
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            rdir = make_response_dir(tmp, {"src/new.txt": b"content\n"})
            cp = run_craft(str(rdir), "--sid", "s-042", "--write")
            self.assertEqual(cp.returncode, 0, cp.stderr)
            (rdir / "validation.sh").write_text(
                "#!/usr/bin/env bash\nexit 0\n")
            lint = subprocess.run(
                [sys.executable, str(LINT), str(rdir)],
                capture_output=True, text=True)
            self.assertEqual(lint.returncode, 1,
                             "an unfilled skeleton must be lint-invalid")


def run_lint(rdir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(LINT), str(rdir)],
        capture_output=True, text=True,
    )


def load_schema(name: str) -> dict:
    return json.loads(
        (REPO / "schemas" / name).read_text(encoding="utf-8"))


HANDOFF_HEADERS = [
    "# Handoff",
    "## Original goal",
    "## What I loaded",
    "## What I explored",
    "## What I learned",
    "## Reading plan for the next session",
    "## Salvageable work",
]


class CraftKindBackCompat(unittest.TestCase):
    """--kind normal is the default: byte-identical output, both modes."""

    def test_kind_normal_equals_default(self):
        with tempfile.TemporaryDirectory() as td:
            rdir = make_response_dir(Path(td), {"src/f.txt": b"f\n"})
            for extra in ([], ["--changes-only"]):
                with self.subTest(mode=extra or ["default"]):
                    args = [str(rdir), "--sid", "s-042", *extra]
                    plain = run_craft(*args)
                    kinded = run_craft(*args, "--kind", "normal")
                    self.assertEqual(plain.returncode, 0, plain.stderr)
                    self.assertEqual(kinded.returncode, 0, kinded.stderr)
                    self.assertEqual(plain.stdout, kinded.stdout)

    def test_normal_write_still_emits_no_validation_sh(self):
        """validation.sh stays the worker's hypothesis test on the normal
        kind — the no-op is emitted only where the contract fixes it."""
        with tempfile.TemporaryDirectory() as td:
            rdir = make_response_dir(Path(td), {"src/f.txt": b"f\n"})
            cp = run_craft(str(rdir), "--sid", "s-042", "--write")
            self.assertEqual(cp.returncode, 0, cp.stderr)
            self.assertFalse((rdir / "validation.sh").exists())


class CraftBailoutKind(unittest.TestCase):
    SID = "2026-07-30-bail-fixture-042"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.rdir = self.tmp / "response-042"
        self.rdir.mkdir()

    def write_bailout(self) -> subprocess.CompletedProcess:
        return run_craft(str(self.rdir), "--sid", self.SID,
                         "--kind", "bailout", "--write")

    def fill_bailout(self):
        """The worker's half: judgment fields, minimally but honestly."""
        mpath = self.rdir / "manifest.json"
        manifest = json.loads(mpath.read_text())
        manifest["summary"] = ("attempted the fixture goal; "
                               "architect-requested bail for the test")
        mpath.write_text(json.dumps(manifest, indent=2) + "\n")
        dpath = self.rdir / "diagnostics.json"
        diag = json.loads(dpath.read_text())
        diag["bail_trigger"] = "other"
        diag["bail_narrative"] = "fixture bailout for the craft->lint test"
        dpath.write_text(json.dumps(diag, indent=2) + "\n")

    def test_manifest_skeleton_shape(self):
        cp = run_craft(str(self.rdir), "--sid", self.SID, "--kind", "bailout")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        m = json.loads(cp.stdout)
        self.assertEqual(m["response_kind"], "bailout")
        self.assertEqual(m["session_id"], self.SID)
        self.assertEqual(m["responds_to"], self.SID)
        self.assertEqual(m["summary"], "")           # worker's
        self.assertEqual(m["changes"], [])           # 5.6.2 empty surfaces
        self.assertEqual(m["deferred"], [])
        self.assertEqual(m["validation_will_run"], [])
        self.assertEqual(m["claims"], {})
        self.assertNotIn("questions", m)             # bailouts carry none

    def test_write_emits_the_full_artifact_set(self):
        cp = self.write_bailout()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        for name in ("manifest.json", "apply.sh", "validation.sh",
                     "handoff.md", "diagnostics.json"):
            self.assertTrue((self.rdir / name).is_file(), name)
        # apply.sh is the verbatim 5.1.1 no-op; validation.sh a no-op too.
        self.assertIn("No additional operations",
                      (self.rdir / "apply.sh").read_text())
        self.assertIn("No checks to run",
                      (self.rdir / "validation.sh").read_text())
        for script in ("apply.sh", "validation.sh"):
            chk = subprocess.run(["bash", "-n", str(self.rdir / script)],
                                 capture_output=True, text=True)
            self.assertEqual(chk.returncode, 0, chk.stderr)

    def test_handoff_scaffold_is_headers_only(self):
        """5.7's section list, in order, and nothing else — handoff
        content is judgment and stays the worker's."""
        cp = self.write_bailout()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        body = (self.rdir / "handoff.md").read_text()
        lines = [ln for ln in body.splitlines() if ln.strip()]
        self.assertEqual(lines, HANDOFF_HEADERS)

    def test_diagnostics_skeleton_fields(self):
        cp = self.write_bailout()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        diag = json.loads((self.rdir / "diagnostics.json").read_text())
        self.assertEqual(diag["session_id"], self.SID)  # mechanical: filled
        self.assertEqual(diag["bail_trigger"], "")      # judgment: empty
        self.assertEqual(diag["bail_narrative"], "")
        self.assertEqual(diag["context_loaded"], [])
        self.assertEqual(diag["exploration_paths"], [])
        self.assertEqual(diag["tool_calls_summary"], {})
        self.assertEqual(diag["what_would_save_next_time"], [])

    def test_unfilled_skeleton_fails_the_judge(self):
        cp = self.write_bailout()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        lint = run_lint(self.rdir)
        self.assertEqual(lint.returncode, 1,
                         "an unfilled bailout skeleton must be lint-invalid")

    def test_filled_skeleton_passes_the_judge(self):
        cp = self.write_bailout()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.fill_bailout()
        lint = run_lint(self.rdir)
        self.assertEqual(
            lint.returncode, 0,
            f"judge found findings:\n{lint.stdout}\n{lint.stderr}")

    def test_write_refuses_partial_presence_and_writes_nothing(self):
        """Refuse-overwrite covers the whole enlarged set, checked before
        anything is written: a stray companion must not leave a
        half-scaffolded response behind."""
        (self.rdir / "handoff.md").write_text("stale\n")
        cp = self.write_bailout()
        self.assertEqual(cp.returncode, 2)
        self.assertIn("--force", cp.stderr)
        self.assertFalse((self.rdir / "manifest.json").exists(),
                         "refusal must precede all writes")
        cp2 = run_craft(str(self.rdir), "--sid", self.SID,
                        "--kind", "bailout", "--write", "--force")
        self.assertEqual(cp2.returncode, 0, cp2.stderr)
        self.assertNotIn("stale", (self.rdir / "handoff.md").read_text())

    def test_incoherent_flags_rejected(self):
        for argv, needle in (
            (["--deleted", "x.txt"], "--deleted/--executable"),
            (["--executable", "x.sh"], "--deleted/--executable"),
            (["--changes-only"], "--changes-only"),
            (["--questions", "1"], "--questions"),
        ):
            with self.subTest(argv=argv):
                cp = run_craft(str(self.rdir), "--sid", self.SID,
                               "--kind", "bailout", *argv)
                self.assertEqual(cp.returncode, 2, cp.stderr)
                self.assertIn(needle, cp.stderr)

    def test_populated_files_rejected(self):
        (self.rdir / "files").mkdir()
        (self.rdir / "files" / "left.txt").write_bytes(b"leftover\n")
        cp = run_craft(str(self.rdir), "--sid", self.SID, "--kind", "bailout")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("no file changes", cp.stderr)


class CraftClarificationKind(unittest.TestCase):
    SID = "2026-07-30-clar-fixture-042"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.rdir = self.tmp / "response-042"
        self.rdir.mkdir()

    def test_manifest_skeleton_default_one_stub(self):
        cp = run_craft(str(self.rdir), "--sid", self.SID,
                       "--kind", "clarification")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        m = json.loads(cp.stdout)
        self.assertEqual(m["response_kind"], "clarification")
        self.assertEqual(m["changes"], [])           # 5.9.2 empty surfaces
        self.assertEqual(m["deferred"], [])
        self.assertEqual(m["validation_will_run"], [])
        self.assertEqual(m["claims"], {})
        self.assertEqual(len(m["questions"]), 1)
        self.assertEqual(m["questions"][0], {
            "question": "", "context": "",
            "default_assumption": "", "why_blocked": "",
        })

    def test_questions_n_seeds_n_stubs(self):
        cp = run_craft(str(self.rdir), "--sid", self.SID,
                       "--kind", "clarification", "--questions", "3")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        qs = json.loads(cp.stdout)["questions"]
        self.assertEqual(len(qs), 3)
        for q in qs:
            self.assertEqual(set(q), {"question", "context",
                                      "default_assumption", "why_blocked"})
            self.assertTrue(all(v == "" for v in q.values()))

    def test_questions_bounds_and_placement(self):
        cp = run_craft(str(self.rdir), "--sid", self.SID,
                       "--kind", "clarification", "--questions", "0")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("at least 1", cp.stderr)
        cp2 = run_craft(str(self.rdir), "--sid", self.SID,
                        "--questions", "2")  # default kind: normal
        self.assertEqual(cp2.returncode, 2)
        self.assertIn("--kind clarification", cp2.stderr)

    def test_write_artifact_set_no_bailout_companions(self):
        cp = run_craft(str(self.rdir), "--sid", self.SID,
                       "--kind", "clarification", "--write")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        for name in ("manifest.json", "apply.sh", "validation.sh"):
            self.assertTrue((self.rdir / name).is_file(), name)
        self.assertFalse((self.rdir / "handoff.md").exists())
        self.assertFalse((self.rdir / "diagnostics.json").exists())
        for script in ("apply.sh", "validation.sh"):
            chk = subprocess.run(["bash", "-n", str(self.rdir / script)],
                                 capture_output=True, text=True)
            self.assertEqual(chk.returncode, 0, chk.stderr)
        # Refuse/force across the set.
        cp2 = run_craft(str(self.rdir), "--sid", self.SID,
                        "--kind", "clarification", "--write")
        self.assertEqual(cp2.returncode, 2)
        self.assertIn("--force", cp2.stderr)
        cp3 = run_craft(str(self.rdir), "--sid", self.SID,
                        "--kind", "clarification", "--write", "--force")
        self.assertEqual(cp3.returncode, 0, cp3.stderr)

    def test_unfilled_fails_filled_passes_the_judge(self):
        cp = run_craft(str(self.rdir), "--sid", self.SID,
                       "--kind", "clarification", "--questions", "2",
                       "--write")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        lint = run_lint(self.rdir)
        self.assertEqual(lint.returncode, 1,
                         "an unfilled clarification skeleton must be "
                         "lint-invalid")

        mpath = self.rdir / "manifest.json"
        manifest = json.loads(mpath.read_text())
        manifest["summary"] = "blocked on two fixture questions"
        for q in manifest["questions"]:
            q.update(question="which of A or B?",
                     context="building the fixture",
                     default_assumption="A",
                     why_blocked="the two produce incompatible manifests")
        mpath.write_text(json.dumps(manifest, indent=2) + "\n")
        lint2 = run_lint(self.rdir)
        self.assertEqual(
            lint2.returncode, 0,
            f"judge found findings:\n{lint2.stdout}\n{lint2.stderr}")


class CraftProbeMode(unittest.TestCase):
    """--probe SLUG: the TARBALL.md 4.2 skeleton to stdout, no response
    dir, no judge (probes are chat paste-backs audited by eye)."""

    SLUG = "fixture-probe"

    def emit(self) -> str:
        cp = run_craft("--probe", self.SLUG)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return cp.stdout

    def test_fixed_shape_and_loud_placeholders(self):
        out = self.emit()
        lines = out.splitlines()
        # The three-line purpose header, read-only declaration verbatim.
        self.assertEqual(lines[0], "#!/usr/bin/env bash")
        self.assertTrue(lines[1].startswith(f"# PROBE {self.SLUG}: "))
        self.assertTrue(lines[2].startswith("# Why: "))
        self.assertEqual(
            lines[3],
            "# Read-only: writes nothing anywhere; stdout is the only "
            "output.")
        # Function wrapper and slug-carrying sentinels.
        self.assertIn("probe() {", out)
        self.assertIn(f'echo "=== PROBE BEGIN {self.SLUG} ==="', out)
        self.assertIn(f'echo "=== PROBE END {self.SLUG} ==="', out)
        # Capture-then-count integrity machinery, 4.2's form.
        self.assertIn('out="$(probe 2>&1)"', out)
        self.assertIn("--- integrity: %s lines ---", out)
        self.assertIn("wc -l", out)
        # Loud placeholders: what/why lines and the example section,
        # its cap-and-truncation pattern shown.
        self.assertGreaterEqual(out.count("TODO(worker)"), 3)
        self.assertIn("head -n 40", out)
        self.assertIn("[truncated:", out)

    def test_emission_is_valid_bash_and_runs_read_only(self):
        out = self.emit()
        with tempfile.TemporaryDirectory() as td:
            script = Path(td) / "probe.sh"
            script.write_text(out)
            chk = subprocess.run(["bash", "-n", str(script)],
                                 capture_output=True, text=True)
            self.assertEqual(chk.returncode, 0, chk.stderr)
            # The unfilled skeleton still executes (placeholders are
            # comments and strings only), writes nothing, and its
            # integrity trailer counts the real sentinel-bracketed body.
            before = sorted(p.name for p in Path(td).iterdir())
            run = subprocess.run(["bash", str(script)], cwd=td,
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(sorted(p.name for p in Path(td).iterdir()),
                             before, "probe run must write nothing")
            body = run.stdout.splitlines()
            self.assertEqual(body[0], f"=== PROBE BEGIN {self.SLUG} ===")
            self.assertEqual(body[-1], f"=== PROBE END {self.SLUG} ===")
            counted = body[1:-2]  # between BEGIN and the integrity line
            self.assertEqual(
                body[-2], f"--- integrity: {len(counted)} lines ---")

    def test_mutually_exclusive_with_response_dir_surface(self):
        for argv, needle in (
            (["--kind", "bailout"], "--kind"),
            (["--kind", "normal"], "--kind"),
            (["--changes-only"], "--changes-only"),
            (["--apply-only"], "--apply-only"),
            (["--write"], "--write"),
            (["--validation-epilogue"], "--validation-epilogue"),
            (["--sid", "s-042"], "--sid"),
            (["--questions", "2"], "--questions"),
            (["--deleted", "x.txt"], "--deleted"),
            (["--executable", "x.sh"], "--executable"),
            (["--force"], "--force"),
        ):
            with self.subTest(argv=argv):
                cp = run_craft("--probe", self.SLUG, *argv)
                self.assertEqual(cp.returncode, 2, cp.stderr)
                self.assertIn(needle, cp.stderr)
                self.assertIn("mutually exclusive", cp.stderr)

    def test_supplied_response_dir_refused_not_ignored(self):
        with tempfile.TemporaryDirectory() as td:
            cp = run_craft("--probe", self.SLUG, td)
            self.assertEqual(cp.returncode, 2, cp.stderr)
            self.assertIn("no response dir", cp.stderr)

    def test_slug_hygiene(self):
        for bad in ("", "  ", "Has-Caps", "under_score", "spa ce",
                    "tick`tick", "-lead", "trail-", "dou--ble", "a/b"):
            with self.subTest(bad=bad):
                # --probe=X keeps hyphen-leading values out of argparse's
                # option parsing so the tool's own hygiene answers.
                cp = run_craft(f"--probe={bad}")
                self.assertEqual(cp.returncode, 2, cp.stderr)

    def test_missing_response_dir_still_an_error_without_probe(self):
        cp = run_craft("--sid", "s-042")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("response dir is required", cp.stderr)


class SchemaDriftBridge(unittest.TestCase):
    """The test-side drift bridge (no third home for the schemas): the
    crafter embeds neither schema and never validates its output, so the
    suite is where skeleton key sets and the repo schemas are held
    together. If a schema gains or loses a required key, these fail and
    name the drift."""

    def test_diagnostics_skeleton_matches_schema_required_set(self):
        schema = load_schema("diagnostics.schema.json")
        with tempfile.TemporaryDirectory() as td:
            rdir = Path(td) / "response-042"
            rdir.mkdir()
            cp = run_craft(str(rdir), "--sid", "s-042",
                           "--kind", "bailout", "--write")
            self.assertEqual(cp.returncode, 0, cp.stderr)
            diag = json.loads((rdir / "diagnostics.json").read_text())
        self.assertEqual(set(diag), set(schema["required"]),
                         "diagnostics.json skeleton keys must equal the "
                         "schema's required set — fix whichever side "
                         "drifted")

    def test_question_stub_matches_schema_entry_required_set(self):
        schema = load_schema("response-manifest.schema.json")
        entry_required = schema["properties"]["questions"]["items"]["required"]
        with tempfile.TemporaryDirectory() as td:
            rdir = Path(td) / "response-042"
            rdir.mkdir()
            cp = run_craft(str(rdir), "--sid", "s-042",
                           "--kind", "clarification")
            self.assertEqual(cp.returncode, 0, cp.stderr)
            stub = json.loads(cp.stdout)["questions"][0]
        self.assertEqual(set(stub), set(entry_required),
                         "questions[] stub keys must equal the schema's "
                         "required entry set — fix whichever side drifted")


class CraftValidationEpilogue(unittest.TestCase):
    """--validation-epilogue: the TARBALL.md 7.3 reconciliation epilogue
    and 7.7 exec-bit assertions, emitted paste-ready to stdout. The
    session-31 constraints under test: which checks run stays worker
    judgment (the emission names no checks), reconciliation semantics
    equal 7.3's contract (agree / DISAGREE only on a pass-fail cross /
    n/a for skip, missing, untested, unknown; diagnostic — never the
    exit code), and the exec-bit assertions come from the same
    --executable list as apply.sh's chmod lines."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def emit(self, *argv: str) -> str:
        rdir = make_response_dir(self.tmp, {"scripts/run.sh": b"#!/bin/sh\n"})
        cp = run_craft(str(rdir), "--validation-epilogue", *argv)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return cp.stdout

    def test_emission_shape_and_bash_validity(self):
        out = self.emit()
        self.assertIn("record_verdict() {", out)
        self.assertIn("reconcile_claims() {", out)
        self.assertIn(".bale-manifest.json", out)
        # Placement instructions ride each part.
        self.assertIn("BEFORE your checks", out)
        self.assertIn("AFTER every check", out)
        # No sid, no manifest emission: stdout is bash only.
        script = self.tmp / "epilogue.sh"
        script.write_text(out)
        chk = subprocess.run(["bash", "-n", str(script)],
                             capture_output=True, text=True)
        self.assertEqual(chk.returncode, 0, chk.stderr)

    def test_emission_suggests_no_checks(self):
        """Worker judgment stays worker judgment: the epilogue must not
        pin or suggest a check list. The doc's canonical example names
        (7.2's typical list) are the canary set."""
        out = self.emit()
        for canary in ("eslint", "typecheck", "tsc", "vite", "pytest",
                       "unittest", "build"):
            self.assertNotIn(canary, out.lower())

    def test_reconciliation_semantics_match_7_3(self):
        out = self.emit()
        stage = self.tmp / "staging"
        stage.mkdir()
        (stage / ".bale-manifest.json").write_text(json.dumps({
            "claims": {
                "alpha check": "pass",
                "beta check": "pass",
                "gamma check": "pass",
                "delta=check": "untested",
                "epsilon check": "fail",
            }
        }))
        driver = (
            "#!/usr/bin/env bash\nset -euo pipefail\nexit_code=0\n"
            + out
            + '\nrecord_verdict "alpha check" pass\n'
            'record_verdict "beta check" fail\n'
            'record_verdict "gamma check" skip\n'
            'record_verdict "delta=check" pass\n'
            "reconcile_claims\n"
            'exit "$exit_code"\n'
        )
        # The pasted emission ends in a bare reconcile_claims call; the
        # driver's second call after recording mirrors real placement.
        script = stage / "validation.sh"
        script.write_text(driver)
        run = subprocess.run(["bash", str(script)], cwd=stage,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        body = run.stdout
        self.assertIn("claims vs verdict:", body)
        self.assertRegex(body, r"alpha check:\s+claim=pass\s+verdict=pass\s+\[agree\]")
        self.assertRegex(body, r"beta check:\s+claim=pass\s+verdict=fail\s+\[DISAGREE\]")
        self.assertRegex(body, r"gamma check:\s+claim=pass\s+verdict=skip\s+\[n/a\]")
        # A label containing '=' still pairs (rsplit from the right),
        # and a no-prediction claim is n/a even against a verdict.
        self.assertRegex(body, r"delta=check:\s+claim=untested\s+verdict=pass\s+\[n/a\]")
        # A claimed check whose verdict was never recorded surfaces
        # loudly as missing rather than silently vanishing.
        self.assertRegex(body, r"epsilon check:\s+claim=fail\s+verdict=missing\s+\[n/a\]")
        # Diagnostic, never gatekeeping: the DISAGREE left exit 0.

    def test_missing_manifest_skips_loudly(self):
        out = self.emit()
        empty = self.tmp / "no-staging"
        empty.mkdir()
        script = empty / "validation.sh"
        script.write_text("#!/usr/bin/env bash\nset -euo pipefail\n"
                          + out)
        run = subprocess.run(["bash", str(script)], cwd=empty,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("[SKIP] claims reconciliation", run.stdout)

    def test_exec_assertions_share_the_chmod_source(self):
        """One source, two emissions: the same --executable list yields
        chmod lines in --apply-only and per-path assertions in
        --validation-epilogue, same paths, same order."""
        rdir = make_response_dir(self.tmp, {
            "scripts/b.sh": b"#!/bin/sh\n",
            "scripts/a.sh": b"#!/bin/sh\n",
        })
        argv = ["--executable", "scripts/b.sh", "--executable", "scripts/a.sh"]
        apply_cp = run_craft(str(rdir), "--apply-only", *argv)
        self.assertEqual(apply_cp.returncode, 0, apply_cp.stderr)
        epi_cp = run_craft(str(rdir), "--validation-epilogue", *argv)
        self.assertEqual(epi_cp.returncode, 0, epi_cp.stderr)
        chmod_paths = [ln.split()[-1] for ln in apply_cp.stdout.splitlines()
                       if ln.startswith("chmod +x ")]
        assert_paths = [ln.split()[3] for ln in epi_cp.stdout.splitlines()
                        if ln.startswith("if [ -x ")]
        self.assertEqual(chmod_paths, ["scripts/a.sh", "scripts/b.sh"])
        self.assertEqual(assert_paths, chmod_paths)

    def test_exec_assertion_fails_then_passes(self):
        """The assertion's behavior is 7.7's: a stripped exec bit is a
        [FAIL] that flips exit_code; a restored one is a [PASS]."""
        out = self.emit("--executable", "scripts/run.sh")
        stage = self.tmp / "exec-stage"
        (stage / "scripts").mkdir(parents=True)
        target = stage / "scripts" / "run.sh"
        target.write_text("#!/bin/sh\n")
        script = stage / "validation.sh"
        script.write_text("#!/usr/bin/env bash\nset -euo pipefail\n"
                          "exit_code=0\n" + out + '\nexit "$exit_code"\n')
        run1 = subprocess.run(["bash", str(script)], cwd=stage,
                              capture_output=True, text=True)
        self.assertEqual(run1.returncode, 1, run1.stdout)
        self.assertIn("[FAIL] scripts/run.sh not executable", run1.stdout)
        target.chmod(0o755)
        run2 = subprocess.run(["bash", str(script)], cwd=stage,
                              capture_output=True, text=True)
        self.assertEqual(run2.returncode, 0, run2.stdout)
        self.assertIn("[PASS] scripts/run.sh is executable", run2.stdout)

    def test_no_assertions_without_executables(self):
        out = self.emit()
        self.assertNotIn("exec-bit assertions", out)
        self.assertNotIn("[ -x", out)

    def test_flag_hygiene(self):
        rdir = make_response_dir(self.tmp, {"f.txt": b"f\n"})
        # Normal kind only: the two non-normal kinds fix validation.sh
        # as the no-op.
        cp = run_craft(str(rdir), "--validation-epilogue",
                       "--kind", "bailout")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("--validation-epilogue", cp.stderr)
        # --executable hygiene still applies: no phantom assertions.
        cp2 = run_craft(str(rdir), "--validation-epilogue",
                        "--executable", "ghost.sh")
        self.assertEqual(cp2.returncode, 2)
        self.assertIn("no file under files/", cp2.stderr)
        # No --sid needed (stdout fragment, no manifest).
        cp3 = run_craft(str(rdir), "--validation-epilogue")
        self.assertEqual(cp3.returncode, 0, cp3.stderr)


class CraftEpilogueFragments(unittest.TestCase):
    """--fragment: the separable epilogue parts (fold-in riders). The
    contract: `definitions` never fires reconcile_claims when pasted
    alone (the hazard the rider retires), the three parts concatenate
    byte-identically to the combined emission, and the combined shape
    is unchanged for callers that never type the flag. The label cap
    rider rides here too: one long claims key must not widen every
    reconciliation row."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.rdir = make_response_dir(self.tmp,
                                      {"scripts/run.sh": b"#!/bin/sh\n"})

    def emit(self, *argv: str) -> str:
        cp = run_craft(str(self.rdir), "--validation-epilogue", *argv)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return cp.stdout

    def test_parts_concatenate_to_the_combined_emission(self):
        for argv in ([], ["--executable", "scripts/run.sh"]):
            with self.subTest(argv=argv or ["no-executables"]):
                combined = self.emit(*argv)
                parts = [self.emit(*argv, "--fragment", "definitions")]
                if argv:
                    parts.append(self.emit(*argv, "--fragment",
                                           "assertions"))
                parts.append(self.emit(*argv, "--fragment", "call"))
                self.assertEqual(combined, "\n".join(parts))

    def test_definitions_alone_fires_nothing(self):
        """The rider's exact hazard: paste the definitions block at
        the top of a strict-mode script and nothing runs — no early
        reconciliation, no output, exit 0."""
        out = self.emit("--fragment", "definitions")
        self.assertIn("record_verdict() {", out)
        self.assertIn("reconcile_claims() {", out)
        script = self.tmp / "defs.sh"
        script.write_text("#!/usr/bin/env bash\nset -euo pipefail\n"
                          + out)
        run = subprocess.run(["bash", str(script)], cwd=self.tmp,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(run.stdout, "",
                         "sourcing the definitions fragment must not "
                         "fire reconcile_claims")

    def test_call_fragment_is_the_call_site(self):
        out = self.emit("--fragment", "call")
        lines = [ln for ln in out.splitlines()
                 if ln.strip() and not ln.startswith("#")]
        self.assertEqual(lines, ["reconcile_claims"])

    def test_assertions_fragment_is_the_exec_block(self):
        out = self.emit("--executable", "scripts/run.sh",
                        "--fragment", "assertions")
        self.assertIn("if [ -x scripts/run.sh ]; then", out)
        self.assertNotIn("record_verdict() {", out)
        self.assertNotIn("reconcile_claims", out)

    def test_fragment_hygiene(self):
        cp = run_craft(str(self.rdir), "--fragment", "call")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("--validation-epilogue", cp.stderr)
        cp2 = run_craft(str(self.rdir), "--validation-epilogue",
                        "--fragment", "assertions")
        self.assertEqual(cp2.returncode, 2)
        self.assertIn("--executable", cp2.stderr)

    def test_label_column_is_capped(self):
        """Fold-in (008's accepted proposal): the label column tops
        out, so one pathological label can't drag every row; the long
        label itself still prints in full — identifiers are verbatim,
        never truncated."""
        out = self.emit()
        long_label = "an implausibly long project-level check label " \
                     "that would widen every row"
        stage = self.tmp / "cap-stage"
        stage.mkdir()
        (stage / ".bale-manifest.json").write_text(json.dumps({
            "claims": {"short check": "pass", long_label: "pass"}
        }))
        script = stage / "validation.sh"
        script.write_text(
            "#!/usr/bin/env bash\nset -euo pipefail\nexit_code=0\n"
            + out
            + '\nrecord_verdict "short check" pass\n'
            + f'record_verdict "{long_label}" pass\n'
            "reconcile_claims\n"
            'exit "$exit_code"\n')
        run = subprocess.run(["bash", str(script)], cwd=stage,
                             capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        short_line = next(ln for ln in run.stdout.splitlines()
                          if ln.strip().startswith("short check:"))
        self.assertLess(
            short_line.index("claim="), 45,
            "the short row's claim column moved past the cap — the "
            "long label widened every row instead of only its own")
        self.assertIn(long_label + ":", run.stdout,
                      "long labels print in full, never truncated")


class CraftDocAssertions(unittest.TestCase):
    """--doc-assertions: the parameterized emissions for the DOCS.md 9
    / CODE.md 10 contract rows. Each block is proven by executing the
    emission against a synthetic staging tree — the pass side and the
    fail side — mirroring how CraftValidationEpilogue proves 7.3
    semantics by running them."""

    SID_DIR = "response-042"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.rdir = self.tmp / self.SID_DIR
        self.rdir.mkdir()
        self.stage = self.tmp / "stage"
        self.stage.mkdir()

    def emit(self, *argv: str) -> str:
        cp = run_craft(str(self.rdir), "--doc-assertions", *argv)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return cp.stdout

    def run_blocks(self, emission: str) -> subprocess.CompletedProcess:
        """Execute the emitted blocks the way validation.sh would:
        strict mode, exit_code tracked by the enclosing script."""
        script = self.stage / "validation.sh"
        script.write_text("#!/usr/bin/env bash\nset -euo pipefail\n"
                          "exit_code=0\n" + emission
                          + '\nexit "$exit_code"\n')
        return subprocess.run(["bash", str(script)], cwd=self.stage,
                              capture_output=True, text=True)

    def write_manifest(self, changes: list) -> None:
        (self.stage / ".bale-manifest.json").write_text(
            json.dumps({"claims": {}, "changes": changes}))

    def stage_file(self, rel: str, body: str) -> None:
        dst = self.stage / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(body, encoding="utf-8")

    # -- shape -------------------------------------------------------

    def test_emission_is_valid_bash_and_opt_in(self):
        out = self.emit("--index", "claude/INDEX.md",
                        "--adr-dir", "claude/context/adr",
                        "--prune-reasons",
                        "--index-header", "bin/tool.py")
        script = self.tmp / "blocks.sh"
        script.write_text(out)
        chk = subprocess.run(["bash", "-n", str(script)],
                             capture_output=True, text=True)
        self.assertEqual(chk.returncode, 0, chk.stderr)
        # Only the selected blocks emit.
        only_prune = self.emit("--prune-reasons")
        self.assertIn("prune declarations", only_prune)
        self.assertNotIn("INDEX coherence", only_prune)
        self.assertNotIn("ADR guards", only_prune)
        self.assertNotIn("index-header coherence", only_prune)

    def test_flag_hygiene(self):
        cp = run_craft(str(self.rdir), "--doc-assertions")
        self.assertEqual(cp.returncode, 2)
        self.assertIn("at least one block", cp.stderr)
        cp2 = run_craft(str(self.rdir), "--index", "claude/INDEX.md")
        self.assertEqual(cp2.returncode, 2)
        self.assertIn("--doc-assertions", cp2.stderr)
        cp3 = run_craft(str(self.rdir), "--sid", "s", "--kind", "bailout",
                        "--doc-assertions", "--prune-reasons")
        self.assertEqual(cp3.returncode, 2)
        self.assertIn("--doc-assertions", cp3.stderr)
        cp4 = run_craft(str(self.rdir), "--doc-assertions",
                        "--prune-reasons", "--deleted", "x.md")
        self.assertEqual(cp4.returncode, 2)
        self.assertIn("--deleted/--executable", cp4.stderr)
        cp5 = run_craft(str(self.rdir), "--doc-assertions",
                        "--adr-baseline", str(self.tmp))
        self.assertEqual(cp5.returncode, 2)
        self.assertIn("--adr-dir", cp5.stderr)

    # -- INDEX coherence ---------------------------------------------

    def index_fixture(self):
        self.stage_file("claude/INDEX.md",
                        "# INDEX.md\n\n"
                        "- `context/new-doc.md` — a new explainer.\n")
        self.stage_file("claude/context/new-doc.md", "hello\n")
        self.write_manifest([
            {"path": "claude/context/new-doc.md", "action": "created",
             "reason": "explainer"},
            {"path": "claude/INDEX.md", "action": "modified",
             "reason": "index update"},
        ])

    def test_index_coherence_passes_both_directions(self):
        self.index_fixture()
        run = self.run_blocks(self.emit("--index", "claude/INDEX.md"))
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertIn("[PASS] INDEX entries resolve", run.stdout)
        self.assertIn("[PASS] shipped docs indexed", run.stdout)

    def test_index_coherence_fails_on_dangling_entry(self):
        self.index_fixture()
        with (self.stage / "claude/INDEX.md").open("a") as fh:
            fh.write("- `context/ghost.md` — gone.\n")
        run = self.run_blocks(self.emit("--index", "claude/INDEX.md"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn("not resolving to a file: context/ghost.md",
                      run.stdout)

    def test_index_coherence_fails_on_unindexed_shipped_doc(self):
        self.index_fixture()
        self.stage_file("claude/context/stray.md", "stray\n")
        manifest = json.loads(
            (self.stage / ".bale-manifest.json").read_text())
        manifest["changes"].append(
            {"path": "claude/context/stray.md", "action": "created",
             "reason": "stray"})
        self.write_manifest(manifest["changes"])
        run = self.run_blocks(self.emit("--index", "claude/INDEX.md"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn("no INDEX entry: claude/context/stray.md",
                      run.stdout)

    def test_index_coverage_skips_loudly_without_manifest(self):
        self.index_fixture()
        (self.stage / ".bale-manifest.json").unlink()
        run = self.run_blocks(self.emit("--index", "claude/INDEX.md"))
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertIn("[SKIP] INDEX coverage", run.stdout)
        self.assertIn("[PASS] INDEX entries resolve", run.stdout)

    # -- ADR guards --------------------------------------------------

    ADR_PRE = ("# ADR-0003: Example\n\n"
               "- **Status:** Proposed\n"
               "- **Date:** 2026-08-01\n"
               "- **Supersedes:** —\n"
               "- **Superseded by:** —\n\n"
               "## Context\n\nWords.\n\n## Notes\n\nNone.\n")

    def adr_fixture(self, post: str, action: str = "modified",
                    baseline: bool = True) -> list[str]:
        """Ship ADR 0003 in the mirror and staging; return the argv
        for an --adr-dir emission (with the pre-change baseline dir
        wired in when `baseline`)."""
        mirror = self.rdir / "files" / "claude/context/adr"
        mirror.mkdir(parents=True, exist_ok=True)
        (mirror / "0003-example.md").write_text(post, encoding="utf-8")
        self.stage_file("claude/context/adr/0003-example.md", post)
        self.write_manifest([
            {"path": "claude/context/adr/0003-example.md",
             "action": action, "reason": "adr change"},
        ])
        argv = ["--adr-dir", "claude/context/adr"]
        if baseline:
            bdir = self.tmp / "baseline"
            bdir.mkdir(exist_ok=True)
            (bdir / "0003-example.md").write_text(self.ADR_PRE,
                                                  encoding="utf-8")
            argv += ["--adr-baseline", str(bdir)]
        return argv

    def test_ratification_flip_passes(self):
        post = self.ADR_PRE.replace("- **Status:** Proposed",
                                    "- **Status:** Accepted")
        run = self.run_blocks(self.emit(*self.adr_fixture(post)))
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertIn("confined to a sanctioned flip", run.stdout)

    def test_ratification_flip_with_landing_note_passes(self):
        post = self.ADR_PRE.replace(
            "- **Status:** Proposed", "- **Status:** Accepted"
        ) + "- 2026-08-15: landed in session 002.\n"
        run = self.run_blocks(self.emit(*self.adr_fixture(post)))
        self.assertEqual(run.returncode, 0, run.stdout)

    def test_supersession_flip_passes(self):
        pre = self.ADR_PRE.replace("- **Status:** Proposed",
                                   "- **Status:** Accepted")
        post = pre.replace(
            "- **Status:** Accepted", "- **Status:** Superseded"
        ).replace("- **Superseded by:** —",
                  "- **Superseded by:** ADR-0007")
        argv = self.adr_fixture(post)
        # The baseline for this case is the Accepted pre-image.
        (self.tmp / "baseline" / "0003-example.md").write_text(
            pre, encoding="utf-8")
        run = self.run_blocks(self.emit(*argv))
        self.assertEqual(run.returncode, 0, run.stdout)

    def test_unsanctioned_edit_fails(self):
        post = self.ADR_PRE.replace(
            "- **Status:** Proposed", "- **Status:** Accepted"
        ).replace("Words.", "Rewritten context.")
        run = self.run_blocks(self.emit(*self.adr_fixture(post)))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn("not a sanctioned flip", run.stdout)

    def test_modified_without_baseline_fails_at_validation(self):
        post = self.ADR_PRE.replace("- **Status:** Proposed",
                                    "- **Status:** Accepted")
        argv = self.adr_fixture(post, baseline=False)
        run = self.run_blocks(self.emit(*argv))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn("no embedded baseline hash", run.stdout)

    def test_deleted_adr_fails(self):
        self.write_manifest([
            {"path": "claude/context/adr/0002-old.md",
             "action": "deleted", "reason": "delete: obsolete"},
        ])
        run = self.run_blocks(
            self.emit("--adr-dir", "claude/context/adr"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn("append-only", run.stdout)

    def test_new_adr_numbering(self):
        for name, ok in (("0004-next.md", True),
                         ("0006-gap.md", False)):
            with self.subTest(name=name):
                self.stage_file("claude/context/adr/0003-example.md",
                                self.ADR_PRE)
                self.stage_file(f"claude/context/adr/{name}", "# ADR\n")
                self.write_manifest([
                    {"path": f"claude/context/adr/{name}",
                     "action": "created", "reason": "new decision"},
                ])
                run = self.run_blocks(
                    self.emit("--adr-dir", "claude/context/adr"))
                if ok:
                    self.assertEqual(run.returncode, 0, run.stdout)
                    self.assertIn("numbering sequential", run.stdout)
                else:
                    self.assertEqual(run.returncode, 1, run.stdout)
                    self.assertIn("!= expected", run.stdout)
                (self.stage / "claude/context/adr" / name).unlink()

    def test_adr_baseline_must_be_a_directory(self):
        cp = run_craft(str(self.rdir), "--doc-assertions",
                       "--adr-dir", "claude/context/adr",
                       "--adr-baseline", str(self.tmp / "nope"))
        self.assertEqual(cp.returncode, 2)
        self.assertIn("not a directory", cp.stderr)

    # -- prune declarations ------------------------------------------

    def test_prune_declarations(self):
        cases = (
            ([], 0, "no deleted entries"),
            ([{"path": "old/a.md", "action": "deleted",
               "reason": "archived to claude/archive/ — stale"}],
             0, "distinguish archive from delete"),
            ([{"path": "old/b.md", "action": "deleted",
               "reason": "no longer needed"}],
             1, "naming neither archive nor delete: old/b.md"),
        )
        for changes, want_exit, needle in cases:
            with self.subTest(needle=needle):
                self.write_manifest(changes)
                run = self.run_blocks(self.emit("--prune-reasons"))
                self.assertEqual(run.returncode, want_exit, run.stdout)
                self.assertIn(needle, run.stdout)

    # -- index-header coherence --------------------------------------

    HEADED = ('"""tool.py — demo.\n\nSections:\n'
              "  1. Imports          (~line 10)\n"
              "  2. Helpers          (~line 20)\n"
              '"""\n'
              "# " + "-" * 75 + "\n"
              "# 1. Imports\n"
              "# " + "-" * 75 + "\n"
              "import os\n"
              "# " + "-" * 75 + "\n"
              "# 2. Helpers\n"
              "# " + "-" * 75 + "\n"
              "def f(): pass\n")

    def test_index_header_coherent_passes(self):
        self.stage_file("bin/tool.py", self.HEADED)
        run = self.run_blocks(self.emit("--index-header", "bin/tool.py"))
        self.assertEqual(run.returncode, 0, run.stdout)
        self.assertIn("[PASS] index header coherent: bin/tool.py "
                      "(2 section(s))", run.stdout)

    def test_index_header_drift_fails_both_directions(self):
        # A header entry with no banner…
        self.stage_file("bin/extra-entry.py", self.HEADED.replace(
            "  2. Helpers          (~line 20)\n",
            "  2. Helpers          (~line 20)\n"
            "  3. Missing          (~line 99)\n"))
        # …and a banner missing from the header.
        self.stage_file("bin/extra-banner.py", self.HEADED.replace(
            "def f(): pass\n",
            "def f(): pass\n"
            "# " + "-" * 75 + "\n"
            "# 3. Unlisted\n"
            "# " + "-" * 75 + "\n"))
        run = self.run_blocks(self.emit(
            "--index-header", "bin/extra-entry.py",
            "--index-header", "bin/extra-banner.py"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn("header entry '3. Missing' has no banner",
                      run.stdout)
        self.assertIn("banner '3. Unlisted' missing from the header",
                      run.stdout)

    def test_index_header_absent_fails(self):
        self.stage_file("bin/bare.py", "print('no header here')\n")
        run = self.run_blocks(self.emit("--index-header", "bin/bare.py"))
        self.assertEqual(run.returncode, 1, run.stdout)
        self.assertIn("no numbered banners and no index-header listing",
                      run.stdout)


@unittest.skipUnless((REPO / "bin").is_dir(),
                     "bin/ not present — a tools-only sandbox has no "
                     "bale_pack.py to drive; the injection surface is "
                     "covered where bin/ ships")
def norm_sha(data: bytes) -> str:
    """sha256 of the LF-normalized bytes — the bundle format's
    published-hash rule, restated locally so the tests assert the
    contract rather than echo the implementation."""
    return hashlib.sha256(data.replace(b"\r\n", b"\n")).hexdigest()


class CraftBundleEmission(unittest.TestCase):
    """--bundle STEM: the planner-bundle emission half (board 49b).

    Every test runs in its own tempdir cwd — the bundle lands there
    and no bale.toml is in reach, so nothing environmental leaks in.
    Bundles are runtime artifacts under temp dirs only; nothing with
    the reserved suffix is ever a committed fixture (worker-blindness
    rule)."""

    STEM = "2026-07-29-fixture-bundle"
    SUFFIX = ".bale-bundle"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def inputs(self, brief: bytes = b"# Brief\n\nbody\n",
               checkpoint: bytes = b"#!/usr/bin/env bash\nexit 1\n"
               ) -> tuple[Path, Path]:
        b = self.tmp / "the-brief.md"
        b.write_bytes(brief)
        c = self.tmp / "the-checkpoint.sh"
        c.write_bytes(checkpoint)
        return b, c

    def emit(self, *argv: str) -> subprocess.CompletedProcess:
        return run_craft("--bundle", self.STEM, *argv, cwd=self.tmp)

    def read_archive(self, path: Path) -> tuple[dict, dict[str, bytes]]:
        members: dict[str, bytes] = {}
        with tarfile.open(path, "r:gz") as tf:
            for m in tf.getmembers():
                self.assertTrue(m.isreg(),
                                f"non-regular member {m.name!r}")
                self.assertNotIn("/", m.name,
                                 f"nested member {m.name!r} — members "
                                 "sit flat at the archive root")
                raw = tf.extractfile(m)
                assert raw is not None
                members[m.name] = raw.read()
        manifest = json.loads(members["bundle.json"])
        return manifest, members

    def test_full_bundle_matches_the_consumer_contract(self):
        brief, checkpoint = self.inputs(
            brief=b"# Brief\n\nCRLF travels\r\nfine\r\n")
        cp = self.emit(
            "--brief", str(brief), "--checkpoint", str(checkpoint),
            "--pack-arg", "Goal text", "--pack-arg=--slug",
            "--pack-arg", "fixture",
            "--pre-answered", "supersede=2026-07-01-parent-001")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        # The paste line: bundle FILENAME only (the 49a-ii consumer
        # fact — search-path resolution makes a downloads save
        # paste-ready), nothing else on stdout.
        filename = self.STEM + self.SUFFIX
        self.assertEqual(cp.stdout, f"bale open {filename}\n")
        out = self.tmp / filename
        self.assertTrue(out.is_file())

        manifest, members = self.read_archive(out)
        # Archive = exactly {bundle.json} ∪ declared members, flat.
        self.assertEqual(set(members),
                         {"bundle.json", "brief.md", "checkpoint.sh"})
        # The four required keys, format 1, argv verbatim, intents.
        self.assertEqual(manifest["bundle_format"], 1)
        self.assertEqual(manifest["pack_argv"],
                         ["Goal text", "--slug", "fixture"])
        self.assertEqual(manifest["pre_answered"],
                         [{"prompt": "supersede",
                           "subject": "2026-07-01-parent-001"}])
        # Member slots publish the LF-normalized hash; the archived
        # bytes are already normalized (CRLF written out as LF), so
        # the stored bytes hash straight to the published digest.
        for slot, name, src in ((("brief"), "brief.md", brief),
                                (("checkpoint"), "checkpoint.sh",
                                 checkpoint)):
            entry = manifest["members"][slot]
            self.assertEqual(entry["path"], name)
            self.assertEqual(entry["sha256"], norm_sha(src.read_bytes()))
            self.assertNotIn(b"\r\n", members[name])
            self.assertEqual(hashlib.sha256(members[name]).hexdigest(),
                             entry["sha256"])

    def test_null_slots_uniform_shape(self):
        cp = self.emit("--no-brief", "--pack-arg", "Goal")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        manifest, members = self.read_archive(
            self.tmp / (self.STEM + self.SUFFIX))
        # Both slots present, both explicit null; the archive carries
        # exactly bundle.json and nothing else.
        self.assertIsNone(manifest["members"]["brief"])
        self.assertIsNone(manifest["members"]["checkpoint"])
        self.assertEqual(set(members), {"bundle.json"})
        self.assertEqual(manifest["pre_answered"], [])
        self.assertIn("oracle-less", cp.stderr)

    def test_deterministic_and_idempotent(self):
        brief, checkpoint = self.inputs()
        argv = ("--brief", str(brief), "--checkpoint", str(checkpoint),
                "--pack-arg", "Goal")
        other = self.tmp / "elsewhere"
        other.mkdir()
        first = self.emit(*argv)
        self.assertEqual(first.returncode, 0, first.stderr)
        elsewhere = self.emit(*argv, "--out-dir", str(other))
        self.assertEqual(elsewhere.returncode, 0, elsewhere.stderr)
        name = self.STEM + self.SUFFIX
        blob = (self.tmp / name).read_bytes()
        self.assertEqual(blob, (other / name).read_bytes(),
                         "identical inputs must produce identical bytes")
        # Idempotent re-run onto the identical file: exit 0, bytes
        # untouched, the paste line still printed, no --force needed.
        again = self.emit(*argv)
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertIn("idempotent re-run", again.stderr)
        self.assertEqual(again.stdout, f"bale open {name}\n")
        self.assertEqual((self.tmp / name).read_bytes(), blob)

    def test_differing_bytes_need_force(self):
        brief, checkpoint = self.inputs()
        cp = self.emit("--brief", str(brief), "--pack-arg", "Goal")
        self.assertEqual(cp.returncode, 0, cp.stderr)
        clash = self.emit("--brief", str(brief), "--pack-arg", "Other")
        self.assertEqual(clash.returncode, 2)
        self.assertIn("--force", clash.stderr)
        forced = self.emit("--brief", str(brief), "--pack-arg", "Other",
                           "--force")
        self.assertEqual(forced.returncode, 0, forced.stderr)
        manifest, _ = self.read_archive(
            self.tmp / (self.STEM + self.SUFFIX))
        self.assertEqual(manifest["pack_argv"], ["Other"])


class CraftBundleHygiene(unittest.TestCase):
    """--bundle's argument hygiene and mode exclusivity: a defective
    bundle fails at the desk, where the fix is immediate, not at the
    operator's `bale open`."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)
        self.brief = self.tmp / "brief.md"
        self.brief.write_text("# Brief\n\nbody\n")

    def emit(self, *argv: str) -> subprocess.CompletedProcess:
        return run_craft(*argv, cwd=self.tmp)

    def test_brief_slot_is_a_deliberate_choice(self):
        neither = self.emit("--bundle", "s-001", "--pack-arg", "g")
        self.assertEqual(neither.returncode, 2)
        self.assertIn("--no-brief", neither.stderr)
        both = self.emit("--bundle", "s-001", "--pack-arg", "g",
                         "--brief", str(self.brief), "--no-brief")
        self.assertEqual(both.returncode, 2)
        self.assertIn("contradict", both.stderr)

    def test_pack_argv_hygiene(self):
        for tokens, needle in (
            ((), "at least one --pack-arg"),
            (("--pack-arg=--readme-file",), "--readme-file"),
            (("--pack-arg", "g",
              "--pack-arg=--readme-file=x.md"), "--readme-file"),
            (("--pack-arg=--checkpoint-file",), "--checkpoint-file"),
            (("--pack-arg", "pack", "--pack-arg", "g"), "AFTER"),
            (("--pack-arg", "g", "--pack-arg=--no-readme"),
             "--no-readme"),
            (("--pack-arg", ""), "empty"),
        ):
            with self.subTest(tokens=tokens):
                cp = self.emit("--bundle", "s-001", "--no-brief",
                               *tokens)
                self.assertEqual(cp.returncode, 2, cp.stderr)
                self.assertIn(needle, cp.stderr)
        # 'pack' is only the verb in position 0; elsewhere it is an
        # ordinary token (a goal word, a path segment).
        ok = self.emit("--bundle", "s-001", "--no-brief",
                       "--pack-arg", "Repack the pack goal",
                       "--pack-arg", "pack")
        self.assertEqual(ok.returncode, 0, ok.stderr)

    def test_stem_hygiene(self):
        for bad in ("", "Has-Caps", "under_score", "a/b", "x.bale-bundle",
                    "-lead", "trail-", "dou--ble"):
            with self.subTest(bad=bad):
                cp = self.emit(f"--bundle={bad}", "--no-brief",
                               "--pack-arg", "g")
                self.assertEqual(cp.returncode, 2, cp.stderr)

    def test_intent_hygiene(self):
        for spec, needle in (
            ("everything=yes", "closed"),
            ("supersede=", "empty subject"),
            ("supersede", "PROMPT=SUBJECT"),
        ):
            with self.subTest(spec=spec):
                cp = self.emit("--bundle", "s-001", "--no-brief",
                               "--pack-arg", "g", "--pre-answered", spec)
                self.assertEqual(cp.returncode, 2, cp.stderr)
                self.assertIn(needle, cp.stderr)
        dup = self.emit("--bundle", "s-001", "--no-brief",
                        "--pack-arg", "g",
                        "--pre-answered", "supersede=p-001",
                        "--pre-answered", "supersede=p-001")
        self.assertEqual(dup.returncode, 2)
        self.assertIn("duplicates", dup.stderr)

    def test_member_input_hygiene(self):
        missing = self.emit("--bundle", "s-001", "--pack-arg", "g",
                            "--brief", "no-such-file.md")
        self.assertEqual(missing.returncode, 2)
        self.assertIn("not a file", missing.stderr)
        hollow = self.tmp / "hollow.md"
        hollow.write_text("   \n")
        empty = self.emit("--bundle", "s-001", "--pack-arg", "g",
                          "--brief", str(hollow))
        self.assertEqual(empty.returncode, 2)
        self.assertIn("empty", empty.stderr)
        half = self.tmp / "half.md"
        half.write_text("# Brief\n\nTODO(brief): fill the goal here\n")
        sentinel = self.emit("--bundle", "s-001", "--pack-arg", "g",
                             "--brief", str(half))
        self.assertEqual(sentinel.returncode, 2)
        self.assertIn("TODO(brief)", sentinel.stderr)

    def test_mutually_exclusive_with_response_dir_surface(self):
        for argv, needle in (
            (["--kind", "normal"], "--kind"),
            (["--changes-only"], "--changes-only"),
            (["--write"], "--write"),
            (["--validation-epilogue"], "--validation-epilogue"),
            (["--doc-assertions"], "--doc-assertions"),
            (["--sid", "s-042"], "--sid"),
            (["--deleted", "x.txt"], "--deleted"),
            (["--executable", "x.sh"], "--executable"),
        ):
            with self.subTest(argv=argv):
                cp = self.emit("--bundle", "s-001", "--no-brief",
                               "--pack-arg", "g", *argv)
                self.assertEqual(cp.returncode, 2, cp.stderr)
                self.assertIn(needle, cp.stderr)
                self.assertIn("mutually exclusive", cp.stderr)

    def test_mutually_exclusive_with_probe_both_directions(self):
        a = self.emit("--probe", "slug-a", "--bundle", "s-001")
        self.assertEqual(a.returncode, 2)
        self.assertIn("--bundle", a.stderr)
        b = self.emit("--probe", "slug-a", "--pack-arg", "g")
        self.assertEqual(b.returncode, 2)
        self.assertIn("--pack-arg", b.stderr)

    def test_supplied_response_dir_refused_not_ignored(self):
        cp = self.emit("--bundle", "s-001", "--no-brief",
                       "--pack-arg", "g", str(self.tmp))
        self.assertEqual(cp.returncode, 2)
        self.assertIn("no response dir", cp.stderr)

    def test_bundle_flags_stray_on_the_response_path(self):
        rdir = self.tmp / "response-042"
        rdir.mkdir()
        for argv, needle in (
            (["--pack-arg", "g"], "--pack-arg"),
            (["--no-brief"], "--no-brief"),
            (["--brief", str(self.brief)], "--brief"),
            (["--checkpoint", str(self.brief)], "--checkpoint"),
            (["--pre-answered", "supersede=x"], "--pre-answered"),
            (["--out-dir", str(self.tmp)], "--out-dir"),
        ):
            with self.subTest(argv=argv):
                cp = self.emit(str(rdir), "--sid",
                               "2026-07-29-fixture-042", *argv)
                self.assertEqual(cp.returncode, 2, cp.stderr)
                self.assertIn(needle, cp.stderr)
                self.assertIn("--bundle", cp.stderr)


class CraftProbeClipboard(unittest.TestCase):
    """The probe scaffold's opt-in clipboard epilogue (registry
    fold-in, configurable-never-core): emitted only when [probe]
    clipboard_command is readable at craft time, sentinel banners
    always, runtime loud either way and never failing the probe,
    remedy text on every unset or misconfigured path."""

    SLUG = "fixture-probe"

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def emit(self) -> subprocess.CompletedProcess:
        return run_craft("--probe", self.SLUG, cwd=self.tmp)

    def set_key(self, value_line: str, where: str = "bale.toml"):
        path = self.tmp / where
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"[probe]\n{value_line}\n", encoding="utf-8")

    def run_scaffold(self, script_text: str) -> subprocess.CompletedProcess:
        script = self.tmp / "probe.sh"
        script.write_text(script_text)
        chk = subprocess.run(["bash", "-n", str(script)],
                             capture_output=True, text=True)
        self.assertEqual(chk.returncode, 0, chk.stderr)
        return subprocess.run(["bash", str(script)], cwd=self.tmp,
                              capture_output=True, text=True)

    def test_keyless_emits_remedy_and_no_epilogue(self):
        cp = self.emit()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("Clipboard epilogue not emitted", cp.stdout)
        self.assertIn("clipboard_command", cp.stdout)
        self.assertIn("[probe]", cp.stdout)
        self.assertNotIn("emit_probe_block |", cp.stdout)
        self.assertIn("clipboard epilogue not emitted", cp.stderr)
        run = self.run_scaffold(cp.stdout)
        self.assertEqual(run.returncode, 0, run.stderr)
        body = run.stdout.splitlines()
        self.assertEqual(body[0], f"=== PROBE BEGIN {self.SLUG} ===")
        self.assertEqual(body[-1], f"=== PROBE END {self.SLUG} ===")

    def test_key_set_tees_the_sentinel_block(self):
        self.set_key('clipboard_command = "cat >clipboard-capture.txt"')
        cp = self.emit()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("emit_probe_block | cat >clipboard-capture.txt",
                      cp.stdout)
        self.assertIn("clipboard epilogue emitted", cp.stderr)
        run = self.run_scaffold(cp.stdout)
        self.assertEqual(run.returncode, 0, run.stderr)
        # stdout is exactly the sentinel-bracketed block (status lines
        # ride stderr); the capture is the same block, byte for byte —
        # what lands on the operator's clipboard is what they paste.
        body = run.stdout.splitlines()
        self.assertEqual(body[0], f"=== PROBE BEGIN {self.SLUG} ===")
        self.assertEqual(body[-1], f"=== PROBE END {self.SLUG} ===")
        self.assertIn("probe output copied", run.stderr)
        capture = (self.tmp / "clipboard-capture.txt").read_bytes()
        self.assertEqual(capture, run.stdout.encode("utf-8"))

    def test_failing_command_is_loud_and_never_fails_the_probe(self):
        self.set_key('clipboard_command = "false"')
        cp = self.emit()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        run = self.run_scaffold(cp.stdout)
        self.assertEqual(run.returncode, 0,
                         "the epilogue must never fail the probe")
        self.assertIn("failed or is missing", run.stderr)
        self.assertIn("PROBE BEGIN", run.stdout)

    def test_context_bale_toml_is_the_request_root_lookup(self):
        self.set_key('clipboard_command = "cat >/dev/null"',
                     where="context/bale.toml")
        cp = self.emit()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("emit_probe_block | cat >/dev/null", cp.stdout)
        self.assertIn("context/bale.toml", cp.stderr)

    def test_misconfigured_shapes_fall_back_to_remedy(self):
        for bad in ("clipboard_command = 123",
                    'clipboard_command = ""',
                    'clipboard_command = "with \\" escape"'):
            with self.subTest(bad=bad):
                self.set_key(bad)
                cp = self.emit()
                self.assertEqual(cp.returncode, 0, cp.stderr)
                self.assertIn("Clipboard epilogue not emitted",
                              cp.stdout)
                self.assertIn("treated as unset", cp.stderr)

    def test_key_outside_the_probe_section_is_unset(self):
        (self.tmp / "bale.toml").write_text(
            '[hooks]\nclipboard_command = "pbcopy"\n', encoding="utf-8")
        cp = self.emit()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("Clipboard epilogue not emitted", cp.stdout)
        self.assertIn("unset", cp.stderr)


@unittest.skipUnless(PACK_MODULE.is_file(),
                     "bin/ not shipped in this sandbox")
class BundlePackParity(unittest.TestCase):
    """The 49b constant-duplication drift guard, unit-shaped — the CI
    twin of validate.sh's install-side assertion: the crafter's
    re-declared constants equal bale_pack's, the TODO(brief) sentinel
    literal is still what the pack guard scans for, and the emitted
    bundle.json passes the consumer's own manifest gate."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(REPO / "tools"))
        sys.path.insert(0, str(REPO / "bin"))
        import craft_response  # noqa: F401
        import bale_pack  # noqa: F401
        cls.craft = sys.modules["craft_response"]
        cls.pack = sys.modules["bale_pack"]

    def test_bundle_suffix_parity(self):
        self.assertEqual(self.craft.BUNDLE_SUFFIX,
                         self.pack.BUNDLE_SUFFIX)

    def test_intent_vocabulary_parity(self):
        self.assertEqual(tuple(self.craft.INTENT_PROMPTS),
                         tuple(self.pack.INTENT_PROMPTS))

    def test_brief_placeholder_literal_still_in_pack_source(self):
        # bale_pack carries the sentinel as a literal (no named
        # constant), so the pin is source containment: if pack renames
        # its sentinel, this goes loud and the crafter follows.
        self.assertIn(self.craft.BRIEF_PLACEHOLDER,
                      PACK_MODULE.read_text(encoding="utf-8"))

    def test_emitted_manifest_passes_the_consumer_gate(self):
        import bale_validate
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            brief = tmp / "b.md"
            brief.write_text("# Brief\n\nbody\r\nwith CRLF\r\n")
            checkpoint = tmp / "c.sh"
            checkpoint.write_text("#!/usr/bin/env bash\nexit 1\n")
            cp = run_craft(
                "--bundle", "2026-07-29-fixture-rt",
                "--brief", str(brief), "--checkpoint", str(checkpoint),
                "--pack-arg", "Goal", "--pack-arg=--slug",
                "--pack-arg", "rt",
                "--pre-answered", "supersede=2026-07-01-parent-001",
                cwd=tmp)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            with tarfile.open(
                    tmp / "2026-07-29-fixture-rt.bale-bundle") as tf:
                raw = tf.extractfile("bundle.json")
                assert raw is not None
                manifest = json.loads(raw.read())
            self.assertEqual(
                bale_validate.validate_bundle_manifest(manifest), [])


class PackInjectionSurface(unittest.TestCase):
    """Unit-shaped injection assertion: build_request_tarball ships
    exactly bin/bale's INJECTED_TOOLS members — the single source since
    the v0.3.19 consolidation retired the guarded interim copy that
    shipped the crafter while bin/bale was held (session 007). The
    real-bale end-to-end pin (a piped pack ships both tools with exec
    bits) lives in tests/test_install_precheck.py."""

    def _run_injection(self, injected_tools: list[str]) -> list[str]:
        """Drive build_request_tarball in a subprocess whose __main__ we
        control (the function lazily imports DOCS_DIR/GLOBAL_DOCS/
        INJECTED_TOOLS/TOOLS_DIR from __main__, which in bale is bin/bale).
        Returns the tar member names."""
        driver = textwrap.dedent("""
            import importlib.util, json, sys, tarfile
            from pathlib import Path

            repo = Path(sys.argv[1])
            tmp = Path(sys.argv[2])
            injected = json.loads(sys.argv[3])

            docs = tmp / "docs"; docs.mkdir()
            for d in ("CLAUDE.md", "TARBALL.md", "DOCS.md", "CODE.md"):
                (docs / d).write_text(f"# {d}\\n")

            main = sys.modules["__main__"]
            main.DOCS_DIR = docs
            main.GLOBAL_DOCS = ["CLAUDE.md", "TARBALL.md", "DOCS.md",
                                "CODE.md"]
            main.INJECTED_TOOLS = injected
            main.TOOLS_DIR = repo / "tools"

            spec = importlib.util.spec_from_file_location(
                "bale_pack", repo / "bin" / "bale_pack.py")
            bale_pack = importlib.util.module_from_spec(spec)
            sys.modules["bale_pack"] = bale_pack
            spec.loader.exec_module(bale_pack)

            out = tmp / "request-042.tar.gz"
            manifest = {"session_id": "2026-07-29-fixture-042"}
            bale_pack.build_request_tarball(
                "2026-07-29-fixture-042", [], manifest, out)
            with tarfile.open(out) as tf:
                print(json.dumps(tf.getnames()))
        """)
        with tempfile.TemporaryDirectory() as td:
            cp = subprocess.run(
                [sys.executable, "-c", driver, str(REPO), td,
                 json.dumps(injected_tools)],
                capture_output=True, text=True)
            self.assertEqual(cp.returncode, 0, cp.stderr)
            return json.loads(cp.stdout.strip().splitlines()[-1])

    def test_injects_exactly_the_list_once_each(self):
        names = self._run_injection(["response_lint.py",
                                     "craft_response.py"])
        self.assertEqual(
            names.count("request-042/tools/response_lint.py"), 1)
        self.assertEqual(
            names.count("request-042/tools/craft_response.py"), 1)

    def test_list_is_the_sole_source(self):
        """With the guard block gone, nothing beside INJECTED_TOOLS
        ships a tool: a list without the crafter yields a tarball
        without it. (bin/bale's real list names both — this drives the
        function with a narrowed list to prove no second copy site
        survived the consolidation.)"""
        names = self._run_injection(["response_lint.py"])
        self.assertIn("request-042/tools/response_lint.py", names)
        self.assertNotIn("request-042/tools/craft_response.py", names)


if __name__ == "__main__":
    unittest.main()
