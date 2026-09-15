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

Since v0.4.29 (board 83) two more facts live here:

- A decline names its cause. The hook's log line carries one of three
  fixed phrases — `stdin closed or interrupted`, `empty answer at a
  decline default`, `answered 'x'` — and the bare `declined; not
  invoking.` line is gone. One case per cause below, each pinning its
  phrase and the bare line's absence.
- `bale config hooks` is the store's operable face: bare, it lists
  every entry; `--forget <sha256-or-unique-prefix>` removes one and
  says so; `--json` is one line on stdout. ConfigHooksVerbTest drives
  it end-to-end through the scratch install (no git repo needed), and
  AcceptanceStoreUnitTest covers the resolver/forget helpers beside
  the store trio it already covered. The `--json` renderer
  (`format_config_hooks_json`) lives in bale_report since v0.4.31
  (board 89), beside its siblings; the unit case loads it from there.

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
    _load_module,
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

# The three decline lines, verbatim from the board-83 brief. The third is
# a template over the operator's stripped, lowercased answer.
BARE_DECLINE = "[hook post_apply_pass] declined; not invoking"
DECLINE_STDIN_CLOSED = ("[hook post_apply_pass] declined (stdin closed or "
                        "interrupted); not invoking.")
DECLINE_EMPTY_AT_DECLINE_DEFAULT = (
    "[hook post_apply_pass] declined (empty answer at a decline default); "
    "not invoking.")


def decline_answered(answer: str) -> str:
    return f"[hook post_apply_pass] declined (answered '{answer}'); not invoking."


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
        # Cause 2 of 3: Enter at a decline default names itself.
        self.assertIn(DECLINE_EMPTY_AT_DECLINE_DEFAULT, out)
        self.assertNotIn(BARE_DECLINE, out)
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
        self.assertIn(DECLINE_EMPTY_AT_DECLINE_DEFAULT, out)
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
        # Cause 1 of 3: EOF at an accept default names itself — this is
        # the line the operator's unexplained "Enter did not accept"
        # report could not be told apart from before board 83.
        self.assertIn("run this hook? [Y/n]", r.stdout)
        self.assertIn(DECLINE_STDIN_CLOSED, r.stdout)
        self.assertNotIn(BARE_DECLINE, r.stdout)
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
        # Cause 3 of 3: a typed answer at an accept default is quoted
        # back verbatim (stripped, lowercased).
        self.assertIn("run this hook? [Y/n]", out)
        self.assertIn(decline_answered("n"), out)
        self.assertNotIn(BARE_DECLINE, out)
        self.assertFalse(self.marker.exists())

    def test_stray_answer_is_quoted_back_stripped_and_lowercased(self) -> None:
        """The third phrase carries the operator's actual answer, so a
        stray keystroke is legible in the log: `  NO ` declines as
        `answered 'no'`."""
        self.write_global_hook()
        tarball = self.pack_and_response(1)
        code, out = self.apply_pty(tarball, "\n  NO \n")
        self.assertEqual(code, 0, msg=out)
        self.assertIn(decline_answered("no"), out)
        self.assertNotIn(BARE_DECLINE, out)
        self.assertFalse(self.marker.exists())


class ConfigHooksVerbTest(_HookFixture):
    """`bale config hooks` end-to-end through the scratch install: the
    listing, --forget by full sha256 and by unique prefix, the two loud
    refusals, --json's stream discipline, and the round trip back to the
    prompt (a forgotten script asks again with the decline default)."""

    def config_hooks(self, *extra: str, cwd: Path = None):
        # Default cwd is the scratch tmp dir — NOT a git repo — pinning
        # that the verb needs none (the store is install-level).
        return run_bale(self.install, ["config", "hooks", *extra],
                        cwd=cwd or self.tmp, env=self.env)

    def seed_store(self, entries: dict) -> None:
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text(json.dumps(entries), encoding="utf-8")

    @staticmethod
    def entry(script: str, hook: str = "post_apply_pass",
              layer: str = "project",
              accepted_at: str = "2026-09-14T00:00:00+00:00") -> dict:
        return {"script": script, "hook": hook, "layer": layer,
                "accepted_at": accepted_at}

    def test_empty_store_lists_nothing_and_exits_zero(self) -> None:
        r = self.config_hooks()
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertIn("no hook acceptances remembered at", r.stdout)
        self.assertIn(str(self.store), r.stdout)
        self.assertIn("nothing accepted yet", r.stdout)
        self.assertFalse(self.store.exists(),
                         msg="listing never creates the file")

    def test_lists_what_the_prompt_remembered(self) -> None:
        script = self.write_project_hook()
        tarball = self.pack_and_response(1)
        code, out = self.apply_pty(tarball, "\ny\n")
        self.assertEqual(code, 0, msg=out)
        digest = self.sha(script)
        r = self.config_hooks()
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertIn("1 hook acceptance remembered at", r.stdout)
        self.assertIn(digest[:12], r.stdout)
        self.assertIn("post_apply_pass", r.stdout)
        self.assertIn("project", r.stdout)
        self.assertIn(str(script.resolve()), r.stdout)
        self.assertIn(self.store_json()[digest]["accepted_at"], r.stdout)

    def test_listing_is_oldest_first(self) -> None:
        self.seed_store({
            "b" * 64: self.entry("/x/newer.sh",
                                 accepted_at="2026-09-14T12:00:00+00:00"),
            "a" * 64: self.entry("/x/older.sh",
                                 accepted_at="2026-09-13T12:00:00+00:00"),
        })
        r = self.config_hooks()
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertLess(r.stdout.index("/x/older.sh"),
                        r.stdout.index("/x/newer.sh"))

    def test_forget_by_unique_prefix_says_what_it_removed(self) -> None:
        keep = "a1" + "0" * 62
        gone = "b2" + "0" * 62
        self.seed_store({keep: self.entry("/x/keep.sh"),
                         gone: self.entry("/x/gone.sh", hook="post_pack",
                                          layer="configured")})
        r = self.config_hooks("--forget", "b2")
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertIn(f"forgot sha256 {gone[:12]}", r.stdout)
        self.assertIn("forgot:  " + gone, r.stdout)
        self.assertIn("hook post_pack, layer configured", r.stdout)
        self.assertIn("/x/gone.sh", r.stdout)
        self.assertIn("remaining:", r.stdout)
        self.assertEqual(list(self.store_json()), [keep])
        self.assertFalse(self.store.with_name(self.store.name + ".tmp")
                         .exists(), msg="atomic rewrite leaves no temp")

    def test_forget_by_full_sha256_and_uppercase_input(self) -> None:
        key = "c3" + "0" * 62
        self.seed_store({key: self.entry("/x/one.sh")})
        r = self.config_hooks("--forget", key.upper())
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertEqual(self.store_json(), {},
                         msg="the file stays, empty, after the last forget")
        self.assertIn("the file exists but holds no entries", r.stdout)

    def test_forget_ambiguous_prefix_refuses_and_names_both(self) -> None:
        one = "ab1" + "0" * 61
        two = "ab2" + "0" * 61
        self.seed_store({one: self.entry("/x/one.sh"),
                         two: self.entry("/x/two.sh")})
        r = self.config_hooks("--forget", "ab")
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertIn("ambiguous", r.stderr)
        self.assertIn(one, r.stderr)
        self.assertIn(two, r.stderr)
        self.assertIn("/x/one.sh", r.stderr)
        self.assertIn("/x/two.sh", r.stderr)
        self.assertEqual("", r.stdout, msg="a refusal prints nothing to stdout")
        self.assertEqual(set(self.store_json()), {one, two},
                         msg="nothing removed on refusal")

    def test_forget_missing_key_refuses_and_points_at_the_listing(self) -> None:
        self.seed_store({"d4" + "0" * 62: self.entry("/x/one.sh")})
        r = self.config_hooks("--forget", "e5")
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertIn("no remembered hook acceptance starts with 'e5'",
                      r.stderr)
        self.assertIn("`bale config hooks` lists", r.stderr)
        self.assertEqual(len(self.store_json()), 1)

    def test_forget_non_hex_refuses_as_a_typo(self) -> None:
        r = self.config_hooks("--forget", "not-a-hash")
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertIn("is not a sha256 or a prefix of one", r.stderr)

    def test_forget_empty_store_refuses_as_missing(self) -> None:
        r = self.config_hooks("--forget", "ab")
        self.assertEqual(r.returncode, 1, msg=r.stdout + r.stderr)
        self.assertIn("no remembered hook acceptance starts with", r.stderr)
        self.assertFalse(self.store.exists())

    def test_no_forget_all_flag(self) -> None:
        r = self.config_hooks("--forget-all")
        self.assertNotEqual(r.returncode, 0)
        self.assertNotIn("--forget-all", run_bale(
            self.install, ["help", "config", "hooks"],
            cwd=self.tmp, env=self.env).stdout)

    def test_malformed_store_lists_empty_with_the_warning(self) -> None:
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text("{not json", encoding="utf-8")
        r = self.config_hooks()
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertIn("unreadable or malformed", r.stdout)
        self.assertIn("the file exists but holds no entries", r.stdout)
        r = self.config_hooks("--forget", "ab")
        self.assertEqual(r.returncode, 1)
        self.assertIn("unreadable or malformed", r.stdout)
        self.assertIn("no remembered hook acceptance", r.stderr)
        self.assertEqual(self.store.read_text(encoding="utf-8"), "{not json",
                         msg="a refused forget never rewrites the file")

    def test_non_object_entry_is_shown_not_dropped(self) -> None:
        key = "f6" + "0" * 62
        self.seed_store({key: "junk"})
        r = self.config_hooks()
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertIn(key[:12], r.stdout)
        self.assertIn("malformed entry", r.stdout)
        r = self.config_hooks("--forget", "f6")
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertEqual(self.store_json(), {})

    def test_json_is_one_line_on_stdout_and_the_trail_on_stderr(self) -> None:
        key = "a7" + "0" * 62
        self.seed_store({key: self.entry("/x/one.sh")})
        r = self.config_hooks("--json")
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(len(lines), 1, msg=r.stdout)
        report = json.loads(lines[0])
        self.assertEqual(report["outcome"], "listed")
        self.assertEqual(report["store"], str(self.store))
        self.assertTrue(report["exists"])
        self.assertIsNone(report["forgotten"])
        self.assertEqual(report["entries"], [{
            "sha256": key, "script": "/x/one.sh", "hook": "post_apply_pass",
            "layer": "project", "accepted_at": "2026-09-14T00:00:00+00:00",
            "malformed": False}])
        self.assertIn("version", report)
        self.assertIn("bale config hooks", r.stderr,
                      msg="the human block rides stderr under --json")

    def test_json_forget_reports_the_removed_entry_and_survivors(self) -> None:
        keep = "b8" + "0" * 62
        gone = "c9" + "0" * 62
        self.seed_store({keep: self.entry("/x/keep.sh"),
                         gone: self.entry("/x/gone.sh")})
        r = self.config_hooks("--forget", gone, "--json")
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        report = json.loads(r.stdout.strip())
        self.assertEqual(report["outcome"], "forgotten")
        self.assertEqual(report["forgotten"]["sha256"], gone)
        self.assertEqual([e["sha256"] for e in report["entries"]], [keep])
        self.assertIn("[bale] config hooks: forgot", r.stderr)

    def test_json_refusal_leaves_stdout_empty(self) -> None:
        r = self.config_hooks("--forget", "ab", "--json")
        self.assertEqual(r.returncode, 1)
        self.assertEqual("", r.stdout)
        self.assertIn("[bale] error:", r.stderr)

    def test_forgotten_script_asks_again_with_the_decline_default(self) -> None:
        """The round trip: accept once, forget it, and the next apply is
        back to [y/N] with Enter declining — the same state as before
        the acceptance, by the same prompt."""
        script = self.write_project_hook()
        tarball = self.pack_and_response(1)
        code, out = self.apply_pty(tarball, "\ny\n")
        self.assertEqual(code, 0, msg=out)
        self.assertEqual(self.marker.read_text(), "hook-v1\n")
        self.marker.unlink()
        digest = self.sha(script)

        r = self.config_hooks("--forget", digest[:10], cwd=self.repo)
        self.assertEqual(r.returncode, 0, msg=r.stdout + r.stderr)
        self.assertEqual(self.store_json(), {})

        tarball = self.pack_and_response(2)
        code, out = self.apply_pty(tarball, "\n\n")
        self.assertEqual(code, 0, msg=out)
        self.assertIn("default: decline — project-layer hook not yet accepted",
                      out)
        self.assertIn("run this hook? [y/N]", out)
        self.assertIn(DECLINE_EMPTY_AT_DECLINE_DEFAULT, out)
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

    # --- v0.4.29 (board 83): the resolver, forget, and the shared writer

    def test_resolve_exact_prefix_and_case(self) -> None:
        data = {"ab" + "1" * 62: {}, "ac" + "2" * 62: {}}
        self.assertEqual(self.bc.resolve_hook_acceptance_key("ab", data),
                         "ab" + "1" * 62)
        self.assertEqual(self.bc.resolve_hook_acceptance_key("AB", data),
                         "ab" + "1" * 62)
        self.assertEqual(self.bc.resolve_hook_acceptance_key(
            "ab" + "1" * 62, data), "ab" + "1" * 62)
        self.assertEqual(self.bc.resolve_hook_acceptance_key(
            "  ac2 ", data), "ac" + "2" * 62)

    def test_resolve_refusals_are_typed(self) -> None:
        data = {"ab" + "1" * 62: {}, "ab" + "2" * 62: {}}
        with self.assertRaises(self.bc.HookAcceptanceLookupError) as cm:
            self.bc.resolve_hook_acceptance_key("ab", data)
        self.assertEqual(cm.exception.kind, "ambiguous")
        self.assertEqual(cm.exception.matches, sorted(data))
        with self.assertRaises(self.bc.HookAcceptanceLookupError) as cm:
            self.bc.resolve_hook_acceptance_key("ff", data)
        self.assertEqual(cm.exception.kind, "missing")
        self.assertEqual(cm.exception.matches, [])
        for bad in ("", "xyz", "ab-1", "a" * 65):
            with self.assertRaises(ValueError):
                self.bc.resolve_hook_acceptance_key(bad, data)
        self.assertTrue(issubclass(self.bc.HookAcceptanceLookupError,
                                   LookupError))

    def test_forget_removes_one_and_rewrites_atomically(self) -> None:
        keep = "11" + "0" * 62
        gone = "22" + "0" * 62
        self.store.parent.mkdir(parents=True)
        self.store.write_text(json.dumps({
            keep: {"script": "/k", "hook": "post_pack", "layer": "project",
                   "accepted_at": "2026-09-14T00:00:00+00:00"},
            gone: {"script": "/g", "hook": "post_apply_pass",
                   "layer": "configured",
                   "accepted_at": "2026-09-14T00:00:01+00:00"}}),
            encoding="utf-8")
        key, removed = self.bc.forget_hook_acceptance("22", self.store)
        self.assertEqual(key, gone)
        self.assertEqual(removed["script"], "/g")
        self.assertEqual(list(self.bc.load_hook_acceptances(self.store)),
                         [keep])
        self.assertFalse(self.store.with_name(self.store.name + ".tmp")
                         .exists())
        self.assertTrue(self.store.read_text(encoding="utf-8").endswith("\n"))

    def test_forget_on_absent_or_malformed_store_is_missing(self) -> None:
        with self.assertRaises(self.bc.HookAcceptanceLookupError) as cm:
            self.bc.forget_hook_acceptance("ab", self.store)
        self.assertEqual(cm.exception.kind, "missing")
        self.assertFalse(self.store.exists(), msg="a refusal never writes")
        self.store.parent.mkdir(parents=True)
        self.store.write_text("{not json", encoding="utf-8")
        with self.assertRaises(self.bc.HookAcceptanceLookupError):
            self.bc.forget_hook_acceptance("ab", self.store)
        self.assertTrue(any("malformed" in ln for ln in self.lines))
        self.assertEqual(self.store.read_text(encoding="utf-8"), "{not json")

    def test_write_is_the_one_writer_the_record_path_uses(self) -> None:
        out = self.bc.write_hook_acceptances({"z": 1}, self.store)
        self.assertEqual(out, self.store)
        self.assertEqual(json.loads(self.store.read_text()), {"z": 1})
        script = self.tmp / "h.sh"
        script.write_bytes(b"#!/bin/sh\n")
        digest = self.bc.hook_script_sha256(script)
        self.bc.record_hook_acceptance(
            script_sha256=digest, script_path=script, hook="post_apply_pass",
            layer="project", path=self.store)
        self.assertEqual(set(json.loads(self.store.read_text())), {"z", digest})

    def test_json_report_shape(self) -> None:
        """The renderer lives beside its json siblings in bale_report
        since v0.4.31 (board 89), one function moved; the emitted line
        is unchanged."""
        br = _load_module("bale_report")
        self.assertFalse(hasattr(self.bc, "format_config_hooks_json"),
                         msg="the renderer moved out of bale_config")
        line = br.format_config_hooks_json(
            outcome="listed", version="0.0.0", store=self.store, entries=[],
            forgotten=None)
        self.assertNotIn("\n", line)
        report = json.loads(line)
        self.assertEqual(list(report), ["outcome", "version", "store",
                                        "exists", "entries", "forgotten"])
        self.assertFalse(report["exists"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
