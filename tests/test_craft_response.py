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


def run_craft(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CRAFT), *argv],
        capture_output=True, text=True,
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
