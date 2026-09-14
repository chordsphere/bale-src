"""The hook confirmation default (v0.4.27, board 78): trust by layer,
then by bytes.

- A global-layer hook (under <install>/user/) defaults accept ([Y/n]).
- A project-layer hook defaults decline ([y/N]) until the operator has
  accepted that exact script's bytes once; the acceptance is remembered
  in <install>/user/hook-acceptances.json keyed by sha256 (with the
  script path, hook name, layer, and timestamp beside it); thereafter
  it defaults accept; changed bytes ask again with the decline default.
- --no-interact / apply.hook_auto_accept are unchanged and never write
  the store; a global-layer default-accept is never recorded either.

The first suite to mention post_apply_pass and hook_auto_accept: the
hook path had no coverage before this session. Driven through real
`bale apply` runs under a pty (the hook prompt engages only on a TTY),
against a scratch install whose user/ dir starts empty — "nothing
accepted yet".
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
import sys
import tempfile
import unittest
from pathlib import Path

from harness import (
    REPO_ROOT,
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

MARK = "hook-ran.txt"


class _HookFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-hook-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        self.store = self.install / "user" / "hook-acceptances.json"
        # The hook writes a marker under HOME (outside the repo) so the
        # test can tell "ran" from "declined" without parsing output.
        self.marker = self.home / MARK
        # Nothing confined runs in this suite: the hook prompt is what is
        # under test, and config-off keeps it host-independent (a
        # namespace-less host would otherwise hit the sandbox prompt).
        (self.repo / "bale.toml").write_text(
            "[sandbox]\nenabled = false\n", encoding="utf-8")
        run_checked(["git", "add", "bale.toml"], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "sandbox off for fixture"],
                    cwd=self.repo, env=self.genv)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def _script_body(self, tag: str = "v1") -> str:
        return (f"#!/bin/sh\n# {tag}\necho hook-{tag} > \"$HOME/{MARK}\"\n")

    def write_project_hook(self, tag: str = "v1") -> Path:
        script = self.repo / "scripts" / "after.sh"
        script.parent.mkdir(exist_ok=True)
        script.write_text(self._script_body(tag), encoding="utf-8")
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        (self.repo / "bale.toml").write_text(
            '[sandbox]\nenabled = false\n'
            '[hooks]\npost_apply_pass = "scripts/after.sh"\n',
            encoding="utf-8")
        run_checked(["git", "add", "bale.toml", "scripts/after.sh"],
                    cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", f"project hook {tag}"],
                    cwd=self.repo, env=self.genv)
        return script

    def write_global_hook(self) -> Path:
        user = self.install / "user"
        (user / "scripts").mkdir(parents=True, exist_ok=True)
        script = user / "scripts" / "after.sh"
        script.write_text(self._script_body("global"), encoding="utf-8")
        script.chmod(script.stat().st_mode | stat.S_IXUSR)
        (user / "bale.toml").write_text(
            '[hooks]\npost_apply_pass = "scripts/after.sh"\n',
            encoding="utf-8")
        return script

    def set_project_apply(self, body: str) -> None:
        toml = self.repo / "bale.toml"
        toml.write_text(toml.read_text(encoding="utf-8") + body,
                        encoding="utf-8")
        run_checked(["git", "add", "bale.toml"], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "apply config"],
                    cwd=self.repo, env=self.genv)

    def pack_and_response(self, n: int) -> Path:
        r = run_bale(self.install, [
            "pack", f"hook fixture goal {n}", "--slug", f"hook{n}",
            "--include", "hello.txt", "--no-readme",
        ], cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        sids = sorted(d.name for d in (self.repo / ".bale" / "sessions").iterdir()
                      if (d / "open").is_file())
        sid = sids[-1]
        rdir = build_response_dir(
            self.tmp / f"resp{n}", sid, summary="hook fixture",
            entries=[{"path": "hello.txt", "action": "modified",
                      "reason": "fixture", "data": f"hello {n}\n".encode()}])
        return tar_response_dir(rdir)

    def apply_pty(self, tarball: Path, answers: str):
        # First answer is the walkthrough's merge prompt (Enter), then the
        # hook confirmation.
        return run_bale_pty(self.install, ["apply", str(tarball)],
                            cwd=self.repo, env=self.env, answers=answers)

    def store_json(self) -> dict:
        return json.loads(self.store.read_text(encoding="utf-8"))

    @staticmethod
    def sha(path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()


class ProjectHookDefaultTest(_HookFixture):

    def test_first_time_declines_by_default_and_records_nothing(self) -> None:
        self.write_project_hook()
        tarball = self.pack_and_response(1)
        code, out = self.apply_pty(tarball, "\n\n")
        self.assertEqual(code, 0, msg=out)
        self.assertIn("hook:   post_apply_pass (project)", out)
        self.assertIn("default: decline — project-layer hook not yet accepted",
                      out)
        self.assertIn("run this hook? [y/N]", out)
        self.assertIn("[hook post_apply_pass] declined; not invoking", out)
        self.assertFalse(self.marker.exists())
        self.assertFalse(self.store.exists(),
                         msg="a decline earns no memory")

    def test_accept_once_then_default_accept_until_bytes_change(self) -> None:
        script = self.write_project_hook()
        first_sha = self.sha(script)

        # Run 1: y at the decline default → runs, remembered.
        tarball = self.pack_and_response(1)
        code, out = self.apply_pty(tarball, "\ny\n")
        self.assertEqual(code, 0, msg=out)
        self.assertIn("run this hook? [y/N]", out)
        self.assertIn("remembered sha256", out)
        self.assertEqual(self.marker.read_text(), "hook-v1\n")
        store = self.store_json()
        self.assertEqual(list(store), [first_sha])
        entry = store[first_sha]
        self.assertEqual(entry["script"], str(script.resolve()))
        self.assertEqual(entry["hook"], "post_apply_pass")
        self.assertEqual(entry["layer"], "project")
        self.assertIn("accepted_at", entry)
        self.marker.unlink()

        # Run 2: same bytes → accept default; Enter runs it; store unchanged.
        tarball = self.pack_and_response(2)
        code, out = self.apply_pty(tarball, "\n\n")
        self.assertEqual(code, 0, msg=out)
        self.assertIn("default: accept — these exact bytes were accepted "
                      "before", out)
        self.assertIn("run this hook? [Y/n]", out)
        self.assertEqual(self.marker.read_text(), "hook-v1\n")
        self.assertEqual(list(self.store_json()), [first_sha])
        self.marker.unlink()

        # Run 3: changed bytes → decline default again; Enter declines.
        script = self.write_project_hook("v2")
        self.assertNotEqual(self.sha(script), first_sha)
        tarball = self.pack_and_response(3)
        code, out = self.apply_pty(tarball, "\n\n")
        self.assertEqual(code, 0, msg=out)
        self.assertIn("run this hook? [y/N]", out)
        self.assertFalse(self.marker.exists())
        self.assertEqual(list(self.store_json()), [first_sha],
                         msg="changed bytes are a new key; nothing recorded "
                             "until accepted")

    def test_no_interact_auto_accept_runs_but_records_nothing(self) -> None:
        self.write_project_hook()
        self.set_project_apply("\n[apply]\nhook_auto_accept = true\n")
        tarball = self.pack_and_response(1)
        r = run_bale(self.install, ["apply", str(tarball), "--no-interact"],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        self.assertIn("auto-accepted per apply.hook_auto_accept=true", r.stdout)
        self.assertEqual(self.marker.read_text(), "hook-v1\n")
        self.assertFalse(self.store.exists(),
                         msg="a bypass is not an operator reading the bytes")

    def test_no_interact_without_auto_accept_still_declines(self) -> None:
        """Unchanged semantics: even a remembered script does not ride
        --no-interact — the store is a prompt default, never a bypass."""
        script = self.write_project_hook()
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text(json.dumps({self.sha(script): {
            "script": str(script), "hook": "post_apply_pass",
            "layer": "project", "accepted_at": "2026-09-14T00:00:00+00:00"}}),
            encoding="utf-8")
        tarball = self.pack_and_response(1)
        r = run_bale(self.install, ["apply", str(tarball), "--no-interact"],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertIn("declined per built-in default (apply.hook_auto_accept "
                      "unset)", r.stdout)
        self.assertFalse(self.marker.exists())

    def test_piped_stdin_declines_regardless_of_memory(self) -> None:
        script = self.write_project_hook()
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text(json.dumps({self.sha(script): {
            "script": str(script), "hook": "post_apply_pass",
            "layer": "project", "accepted_at": "2026-09-14T00:00:00+00:00"}}),
            encoding="utf-8")
        tarball = self.pack_and_response(1)
        r = run_bale(self.install, ["apply", str(tarball)],
                     cwd=self.repo, env=self.env)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertIn("[hook post_apply_pass] declined; not invoking", r.stdout)
        self.assertFalse(self.marker.exists(),
                         msg="EOF declines even at an accept default")


class GlobalHookDefaultTest(_HookFixture):

    def test_global_layer_defaults_accept_and_is_not_recorded(self) -> None:
        self.write_global_hook()
        tarball = self.pack_and_response(1)
        code, out = self.apply_pty(tarball, "\n\n")
        self.assertEqual(code, 0, msg=out)
        self.assertIn("hook:   post_apply_pass (global)", out)
        self.assertIn("default: accept — global-layer hook — your own script",
                      out)
        self.assertIn("run this hook? [Y/n]", out)
        self.assertEqual(self.marker.read_text(), "hook-global\n")
        self.assertFalse(self.store.exists())

    def test_global_layer_n_declines(self) -> None:
        self.write_global_hook()
        tarball = self.pack_and_response(1)
        code, out = self.apply_pty(tarball, "\nn\n")
        self.assertEqual(code, 0, msg=out)
        self.assertIn("[hook post_apply_pass] declined; not invoking", out)
        self.assertFalse(self.marker.exists())


class AcceptanceStoreUnitTest(unittest.TestCase):
    """The store helpers in bin/bale_config.py, without a bale process."""

    @classmethod
    def setUpClass(cls):
        import importlib.util
        import types
        bin_dir = REPO_ROOT / "bin"
        if str(bin_dir) not in sys.path:
            sys.path.insert(0, str(bin_dir))
        # The helpers pull log() from __main__ lazily; give the test
        # process a stub that collects lines.
        cls.lines: list = []
        main = sys.modules["__main__"]
        cls._saved_log = getattr(main, "log", None)
        main.log = lambda msg, *, force=False: cls.lines.append(msg)
        spec = importlib.util.spec_from_file_location(
            "bale_config", bin_dir / "bale_config.py")
        cls.bc = importlib.util.module_from_spec(spec)
        sys.modules["bale_config"] = cls.bc
        spec.loader.exec_module(cls.bc)

    @classmethod
    def tearDownClass(cls):
        main = sys.modules["__main__"]
        if cls._saved_log is None:
            delattr(main, "log")
        else:
            main.log = cls._saved_log

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-store-")
        self.tmp = Path(self._tmpdir.name)
        self.store = self.tmp / "user" / "hook-acceptances.json"
        self.lines.clear()

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def test_store_lives_under_the_install_user_dir(self) -> None:
        self.assertEqual(self.bc.HOOK_ACCEPTANCES_PATH,
                         self.bc.GLOBAL_USER_DIR / "hook-acceptances.json")

    def test_absent_reads_as_nothing_accepted_silently(self) -> None:
        self.assertEqual(self.bc.load_hook_acceptances(self.store), {})
        self.assertFalse(self.bc.hook_previously_accepted("abc", self.store))
        self.assertEqual(self.lines, [])

    def test_record_then_lookup_and_the_fields_beside_the_hash(self) -> None:
        script = self.tmp / "h.sh"
        script.write_bytes(b"#!/bin/sh\n")
        digest = self.bc.hook_script_sha256(script)
        self.assertEqual(digest, hashlib.sha256(b"#!/bin/sh\n").hexdigest())
        out = self.bc.record_hook_acceptance(
            script_sha256=digest, script_path=script, hook="post_apply_pass",
            layer="project", path=self.store)
        self.assertEqual(out, self.store)
        self.assertTrue(self.bc.hook_previously_accepted(digest, self.store))
        entry = self.bc.load_hook_acceptances(self.store)[digest]
        self.assertEqual(set(entry), {"script", "hook", "layer", "accepted_at"})
        self.assertEqual(entry["script"], str(script))
        self.assertFalse(self.store.with_name(self.store.name + ".tmp").exists(),
                         msg="atomic rename leaves no temp file")

    def test_malformed_store_reads_empty_with_a_logged_warning(self) -> None:
        self.store.parent.mkdir(parents=True)
        self.store.write_text("{not json", encoding="utf-8")
        self.assertEqual(self.bc.load_hook_acceptances(self.store), {})
        self.assertTrue(any("malformed" in ln for ln in self.lines))
        self.store.write_text("[]", encoding="utf-8")
        self.lines.clear()
        self.assertEqual(self.bc.load_hook_acceptances(self.store), {})
        self.assertTrue(any("not a JSON object" in ln for ln in self.lines))


if __name__ == "__main__":
    unittest.main(verbosity=2)
