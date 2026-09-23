#!/usr/bin/env python3
"""Hermetic E2E and unit tests for the context pack (`bale pack --context`,
v0.4.39; BALE.md §7.8; the receiving side is TARBALL.md §3.1).

A context pack is a session-less tarball of the current directory's
tree, made to travel beside another project's request as reading
material. The contract under test, outcome by outcome:

- It writes exactly one gzipped tarball, at
  ``<dir>/.bale/outbox/context-<dir>.tar.gz``, exits 0 with piped stdin,
  and carries the tree's files byte for byte under one ``<dir>/``
  folder — and nothing a request carries: no manifest.json, none of the
  five carried docs, neither carried tool.
- It is session-less: no sid (no day counter), nothing under
  ``.bale/sessions/``, no lock, no telemetry record, no session log, no
  opener, no .gitignore edit, no commit; outside a git work tree no
  git-init walkthrough (no ``.git`` appears).
- The pack filters apply: the built-in directory and secret-pattern
  filters, .gitignore (inside a work tree), .baleignore, --exclude, the
  planner-bundle deny, the configured blind checkpoint, and the caps.
- Session-only flags refuse beside it, fail-fast, writing nothing; the
  two classification tables in bin/bale_pack.py partition the parser's
  pack flags, so a future flag must be classified.
- Normal packs are untouched: goal-less piped pack still refuses, a TTY
  goal-less pack still enters the wizard, a full pack still ends with
  the opener, and a context pack never sweeps an open read-only
  session. `bale open`'s pre-flight refuses a stored argv carrying
  --context before any oracle runs.

Sandbox doctrine per ADR-0005 via tests/harness.py.

Run:  python3 tests/test_context_pack.py
  or: python3 -m unittest discover -s tests -p 'test_context_pack.py'
"""

from __future__ import annotations

import hashlib
import io
import json
import os
import subprocess
import sys
import tarfile
import tempfile
import unittest
from pathlib import Path

from harness import (
    REPO_ROOT,
    SUBPROCESS_TIMEOUT,
    _load_cli,
    _load_module,
    bale_env,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
    run_bale_pty,
    run_checked,
)

GLOBAL_DOCS = ("AGENT.md", "TARBALL.md", "DOCS.md", "CODE.md", "PLANNER.md")
CARRIED_TOOLS = ("craft_response.py", "response_lint.py")
OPENER_MARKERS = ("--8<-- session opener", "--8<-- end session opener")


def tar_members(path: Path) -> dict:
    """{arcname: bytes-or-None} for every member (None for non-files)."""
    out: dict = {}
    with tarfile.open(path, "r:gz") as tf:
        for m in tf.getmembers():
            if m.isfile():
                f = tf.extractfile(m)
                out[m.name] = f.read() if f is not None else None
            else:
                out[m.name] = None
    return out


class _Sandbox(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-context-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def context(self, cwd: Path, *extra: str):
        return run_bale(self.install, ["pack", "--context", *extra],
                        cwd=cwd, env=self.env)

    def assertOk(self, r) -> None:
        self.assertEqual(r.returncode, 0,
                         f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")

    def assertRefused(self, r, *needles: str) -> None:
        self.assertNotEqual(r.returncode, 0,
                            f"expected refusal; stdout:\n{r.stdout}")
        for n in needles:
            self.assertIn(n, r.stderr)


# ---------------------------------------------------------------------------
# Outside a git work tree
# ---------------------------------------------------------------------------

class NonGitDirectoryTest(_Sandbox):
    def setUp(self) -> None:
        super().setUp()
        self.dir = self.tmp / "notes-tree"
        (self.dir / "sub").mkdir(parents=True)
        (self.dir / "readme.txt").write_bytes(b"hello\r\nworld\n")
        (self.dir / "sub" / "data.bin").write_bytes(bytes(range(256)))
        (self.dir / "run.sh").write_text("#!/bin/sh\necho hi\n")
        os.chmod(self.dir / "run.sh", 0o755)
        # Junk and secrets the filters must keep out.
        (self.dir / ".env").write_text("TOKEN=x\n")
        (self.dir / "id_rsa").write_text("key\n")
        (self.dir / "node_modules").mkdir()
        (self.dir / "node_modules" / "m.js").write_text("m\n")
        (self.dir / "sub" / "__pycache__").mkdir()
        (self.dir / "sub" / "__pycache__" / "x.pyc").write_bytes(b"\0")
        (self.dir / "plan.bale-bundle").write_text("oracle\n")

    def test_writes_one_tarball_named_for_the_directory(self) -> None:
        r = self.context(self.dir)
        self.assertOk(r)
        out = self.dir / ".bale" / "outbox" / "context-notes-tree.tar.gz"
        self.assertTrue(out.is_file())
        self.assertEqual(sorted((self.dir / ".bale" / "outbox").iterdir()),
                         [out])
        self.assertIn("notes-tree", out.name)

    def test_contents_byte_for_byte_under_one_folder(self) -> None:
        self.assertOk(self.context(self.dir))
        members = tar_members(
            self.dir / ".bale" / "outbox" / "context-notes-tree.tar.gz")
        files = {k: v for k, v in members.items() if v is not None}
        self.assertEqual(sorted(files), [
            "notes-tree/readme.txt", "notes-tree/run.sh",
            "notes-tree/sub/data.bin",
        ])
        for arc, data in files.items():
            src = self.dir / arc.split("/", 1)[1]
            self.assertEqual(hashlib.sha256(data).hexdigest(),
                             hashlib.sha256(src.read_bytes()).hexdigest(),
                             arc)
        with tarfile.open(self.dir / ".bale" / "outbox"
                          / "context-notes-tree.tar.gz") as tf:
            self.assertTrue(tf.getmember("notes-tree/run.sh").mode & 0o100,
                            "exec bit must travel")

    def test_carries_nothing_a_request_carries(self) -> None:
        self.assertOk(self.context(self.dir))
        names = tar_members(self.dir / ".bale" / "outbox"
                            / "context-notes-tree.tar.gz")
        basenames = {n.rsplit("/", 1)[-1] for n in names}
        self.assertNotIn("manifest.json", basenames)
        for doc in GLOBAL_DOCS + CARRIED_TOOLS:
            self.assertNotIn(doc, basenames)

    def test_filters_keep_secrets_junk_and_bundles_out(self) -> None:
        r = self.context(self.dir)
        self.assertOk(r)
        names = " ".join(tar_members(self.dir / ".bale" / "outbox"
                                     / "context-notes-tree.tar.gz"))
        for leaked in (".env", "id_rsa", "node_modules", "__pycache__",
                       "bale-bundle", ".bale/"):
            self.assertNotIn(leaked, names)
        self.assertIn("plan.bale-bundle", r.stdout,
                      "the bundle drop must be logged, not silent")

    def test_no_git_init_and_no_session_state(self) -> None:
        r = self.context(self.dir)
        self.assertOk(r)
        self.assertFalse((self.dir / ".git").exists(),
                         "a context pack must not run the git-init walkthrough")
        self.assertEqual(sorted(p.name for p in (self.dir / ".bale").iterdir()),
                         ["outbox"])
        self.assertFalse((self.dir / "claude").exists())
        self.assertFalse((self.dir / ".gitignore").exists())
        for marker in OPENER_MARKERS:
            self.assertNotIn(marker, r.stdout + r.stderr)

    def test_baleignore_and_exclude_apply(self) -> None:
        (self.dir / ".baleignore").write_text("sub/\n")
        r = self.context(self.dir, "--exclude", "*.sh")
        self.assertOk(r)
        files = [n for n, v in tar_members(
            self.dir / ".bale" / "outbox" / "context-notes-tree.tar.gz"
        ).items() if v is not None]
        self.assertEqual(sorted(files), ["notes-tree/.baleignore",
                                         "notes-tree/readme.txt"])

    def test_rerun_replaces_and_never_ships_the_previous_tarball(self) -> None:
        self.assertOk(self.context(self.dir))
        r = self.context(self.dir)
        self.assertOk(r)
        self.assertIn("replaced context tarball", r.stdout)
        names = tar_members(self.dir / ".bale" / "outbox"
                            / "context-notes-tree.tar.gz")
        self.assertFalse(any(".bale" in n for n in names))
        leftovers = [p.name for p in (self.dir / ".bale" / "outbox").iterdir()]
        self.assertEqual(leftovers, ["context-notes-tree.tar.gz"])

    def test_json_report_is_one_line(self) -> None:
        r = self.context(self.dir, "--json")
        self.assertOk(r)
        lines = r.stdout.splitlines()
        self.assertEqual(len(lines), 1, r.stdout)
        payload = json.loads(lines[0])
        self.assertEqual(payload["outcome"], "context-packed")
        self.assertEqual(payload["context_files"], 3)
        self.assertEqual(payload["tree_name"], "notes-tree")
        self.assertFalse(payload["git"])
        self.assertTrue(Path(payload["tarball"]).is_file())
        self.assertEqual(payload["directory"], str(self.dir.resolve()))

    def test_include_restricts_and_is_directory_relative(self) -> None:
        r = self.context(self.dir, "--include", "sub")
        self.assertOk(r)
        files = [n for n, v in tar_members(
            self.dir / ".bale" / "outbox" / "context-notes-tree.tar.gz"
        ).items() if v is not None]
        self.assertEqual(files, ["notes-tree/sub/data.bin"])

    def test_include_refusals(self) -> None:
        self.assertRefused(self.context(self.dir, "--include", "nope"),
                           "--include path does not exist: nope")
        self.assertRefused(self.context(self.dir, "--include", "../x"),
                           "outside")
        self.assertRefused(self.context(self.dir, "--include",
                                        "plan.bale-bundle"),
                           "planner-bundle blindness")
        self.assertFalse((self.dir / ".bale").exists())

    def test_hard_cap_refuses_and_writes_nothing(self) -> None:
        r = self.context(self.dir, "--max-files", "1")
        self.assertRefused(r, "hard threshold breach")
        self.assertFalse((self.dir / ".bale").exists())
        r = self.context(self.dir, "--max-files", "1", "--force")
        self.assertOk(r)
        self.assertIn("FORCE:", r.stdout)

    def test_empty_tree_refuses(self) -> None:
        empty = self.tmp / "empty"
        empty.mkdir()
        (empty / ".env").write_text("x\n")
        self.assertRefused(self.context(empty), "no files would be included")
        self.assertFalse((empty / ".bale").exists())


# ---------------------------------------------------------------------------
# Inside a git work tree
# ---------------------------------------------------------------------------

class GitRepoTest(_Sandbox):
    def setUp(self) -> None:
        super().setUp()
        self.repo = make_repo(self.tmp, self.home)
        genv = git_env(self.home)
        (self.repo / "docs" / "private").mkdir(parents=True)
        (self.repo / "docs" / "guide.md").write_text("guide\n")
        (self.repo / "docs" / "private" / "p.md").write_text("private\n")
        (self.repo / "docs" / "trace.log").write_text("noise\n")
        (self.repo / ".gitignore").write_text("*.log\n")
        (self.repo / ".baleignore").write_text("docs/private/\n")
        (self.repo / "claude" / "checkpoints").mkdir(parents=True)
        (self.repo / "claude" / "checkpoints" / "old-001.sh").write_text(
            "#!/bin/sh\nexit 1\n")
        (self.repo / "bale.toml").write_text(
            "[validation]\nbase = \"claude/checkpoints/{sid}.sh\"\n")
        run_checked(["git", "add", "-A"], cwd=self.repo, env=genv)
        run_checked(["git", "commit", "-m", "tree"], cwd=self.repo, env=genv)
        (self.repo / "untracked.txt").write_text("untracked but not ignored\n")
        self.genv = genv

    def head(self) -> str:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=self.repo,
                              env=self.genv, capture_output=True, text=True,
                              timeout=SUBPROCESS_TIMEOUT).stdout.strip()

    def test_session_less_at_the_repo_root(self) -> None:
        before_head = self.head()
        before_gitignore = (self.repo / ".gitignore").read_bytes()
        r = self.context(self.repo)
        self.assertOk(r)
        bale = self.repo / ".bale"
        self.assertEqual(sorted(p.name for p in bale.iterdir()), ["outbox"])
        self.assertEqual([p.name for p in (bale / "outbox").iterdir()],
                         ["context-project.tar.gz"])
        self.assertEqual(list(bale.glob("counter-*")), [])
        self.assertFalse((self.repo / "claude" / "telemetry").exists())
        self.assertEqual(self.head(), before_head, "no commit")
        self.assertEqual((self.repo / ".gitignore").read_bytes(),
                         before_gitignore, ".gitignore untouched")
        for marker in OPENER_MARKERS:
            self.assertNotIn(marker, r.stdout + r.stderr)
        self.assertIn("not gitignored", r.stdout)

    def test_filters_inside_git(self) -> None:
        r = self.context(self.repo)
        self.assertOk(r)
        files = sorted(n for n, v in tar_members(
            self.repo / ".bale" / "outbox" / "context-project.tar.gz"
        ).items() if v is not None)
        self.assertIn("project/untracked.txt", files)
        self.assertIn("project/docs/guide.md", files)
        self.assertIn("project/hello.txt", files)
        joined = " ".join(files)
        self.assertNotIn("trace.log", joined, ".gitignore honored")
        self.assertNotIn("private", joined, ".baleignore honored")
        self.assertNotIn("checkpoints", joined, "checkpoint auto-excluded")
        self.assertIn("auto-excluded claude/checkpoints/old-001.sh", r.stdout)

    def test_subdirectory_honors_the_enclosing_repo_filters(self) -> None:
        docs = self.repo / "docs"
        r = self.context(docs, "--json")
        self.assertOk(r)
        payload = json.loads(r.stdout.strip())
        self.assertTrue(payload["git"])
        out = docs / ".bale" / "outbox" / "context-docs.tar.gz"
        self.assertEqual(payload["tarball"], str(out))
        files = sorted(n for n, v in tar_members(out).items()
                       if v is not None)
        self.assertEqual(files, ["docs/guide.md"])
        self.assertFalse((self.repo / ".bale").exists())

    def test_context_pack_never_sweeps_an_open_read_only_session(self) -> None:
        ro = run_bale(self.install, ["pack", "a read-only desk", "--slug",
                                     "desk", "--read-only", "--no-readme",
                                     "--include", "hello.txt"],
                      cwd=self.repo, env=self.env)
        self.assertOk(ro)
        sessions = self.repo / ".bale" / "sessions"
        before = sorted(p.name for p in sessions.iterdir())
        self.assertEqual(len(before), 1)
        counters = sorted((self.repo / ".bale").glob("counter-*"))
        counter_bytes = [c.read_bytes() for c in counters]
        # On a TTY the sweep's accept default would close the session;
        # feed an Enter to prove no prompt exists to take it.
        code, out = run_bale_pty(self.install, ["pack", "--context"],
                                 cwd=self.repo, env=self.env, answers="\n")
        self.assertEqual(code, 0, out)
        self.assertNotIn("sweep", out.lower())
        self.assertEqual(sorted(p.name for p in sessions.iterdir()), before)
        self.assertEqual([c.read_bytes() for c in counters], counter_bytes,
                         "the day counter must not advance")
        telemetry = self.repo / "claude" / "telemetry"
        self.assertEqual(len(list(telemetry.glob("*.json"))), 1,
                         "only the read-only session's own record")


# ---------------------------------------------------------------------------
# Refusals and the flag classification
# ---------------------------------------------------------------------------

# One typed example per session-only flag (dest -> argv fragment).
SESSION_ONLY_EXAMPLES = {
    "goal": ["a goal"],
    "slug": ["--slug", "x"],
    "write": ["--write", "hello.txt"],
    "read_only": ["--read-only"],
    "supersedes": ["--supersedes", "2026-01-01-x-001"],
    "checkpoint_file": ["--checkpoint-file", "c.sh"],
    "readme_file": ["--readme-file", "r.md"],
    "edit": ["--edit"],
    "no_edit": ["--no-edit"],
    "no_readme": ["--no-readme"],
    "constraint": ["--constraint", "c"],
    "out_of_scope": ["--out-of-scope", "o"],
    "expects_probe": ["--expects-probe", "no"],
    "packer": ["--packer", "me"],
    "work_class": ["--work-class", "doc"],
    "allow_checkpoint_in_scope": ["--allow-checkpoint-in-scope"],
    "no_include_group": ["--no-include-group", "g"],
    "dry_run": ["--dry-run"],  # v0.4.45, board row 122
}


class RefusalTest(_Sandbox):
    def setUp(self) -> None:
        super().setUp()
        self.repo = make_repo(self.tmp, self.home)

    def test_every_session_only_flag_refuses_and_writes_nothing(self) -> None:
        for dest, frag in SESSION_ONLY_EXAMPLES.items():
            with self.subTest(dest=dest):
                r = self.context(self.repo, *frag)
                self.assertRefused(r, "--context writes a session-less "
                                      "context tarball")
                self.assertFalse((self.repo / ".bale").exists())

    def test_refusal_names_every_offending_flag(self) -> None:
        r = self.context(self.repo, "--slug", "x", "--read-only")
        self.assertRefused(r, "--slug, --read-only", "Drop them")

    def test_expects_probe_at_its_default_is_a_no_op(self) -> None:
        self.assertOk(self.context(self.repo, "--expects-probe",
                                   "agent-decides"))

    def test_expects_probe_alias_differs_from_the_default(self) -> None:
        """`claude-decides` is the pre-0.4.43 spelling, accepted for good
        as a value — but it is not the parser default any more, so typed
        beside --context it reads as a session-only flag like any other."""
        r = self.context(self.repo, "--expects-probe", "claude-decides")
        self.assertRefused(r, "--expects-probe", "Drop it")

    def test_help_lists_the_flag(self) -> None:
        r = run_bale(self.install, ["pack", "--help"], cwd=self.repo,
                     env=self.env)
        self.assertOk(r)
        self.assertIn("--context", r.stdout)


class ClassificationTest(unittest.TestCase):
    """The two tables partition the pack parser's flags."""

    def test_tables_partition_the_pack_parser(self) -> None:
        cli = _load_cli()
        pack_mod = _load_module("bale_pack")
        parser = cli.build_parser()
        sub = next(a for a in parser._actions
                   if a.__class__.__name__ == "_SubParsersAction")
        p_pack = sub.choices["pack"]
        dests = {a.dest for a in p_pack._actions if a.dest != "help"}
        session_only = {d for d, _s, _dflt in
                        pack_mod.CONTEXT_SESSION_ONLY_FLAGS}
        composing = set(pack_mod.CONTEXT_COMPOSING_FLAGS)
        self.assertEqual(session_only & composing, set())
        self.assertEqual(session_only | composing, dests,
                         "classify every pack flag as session-only or "
                         "composing in bin/bale_pack.py")
        # The tables' defaults must be the parser's defaults, or a flag
        # left at its default would refuse (or a typed one pass).
        defaults = {a.dest: a.default for a in p_pack._actions}
        for dest, _spelling, dflt in pack_mod.CONTEXT_SESSION_ONLY_FLAGS:
            self.assertEqual(defaults[dest], dflt, dest)
        self.assertEqual(set(SESSION_ONLY_EXAMPLES), session_only)


class PureHelpersTest(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load_module("bale_pack")

    def test_tree_name(self) -> None:
        name = self.m.context_tree_name
        self.assertEqual(name(Path("/x/bale-src")), "bale-src")
        self.assertEqual(name(Path("/x/My Notes (v2)")), "My-Notes-v2")
        self.assertEqual(name(Path("/x/.dotted")), "dotted")
        self.assertEqual(name(Path("/x/???")), "tree")
        self.assertEqual(self.m.context_tarball_filename(Path("/x/a b")),
                         "context-a-b.tar.gz")

    def test_session_only_detection(self) -> None:
        import argparse
        ns = argparse.Namespace(**{d: dflt for d, _s, dflt in
                                   self.m.CONTEXT_SESSION_ONLY_FLAGS})
        self.assertEqual(self.m.context_session_only_flags(ns), [])
        ns.slug = "x"
        ns.constraint = ["c"]
        self.assertEqual(self.m.context_session_only_flags(ns),
                         ["--slug", "--constraint"])

    def test_json_renderer(self) -> None:
        # Homed in bin/bale_report.py since v0.4.40 (board 104b rider):
        # the outcome vocabulary's one home. Same keys, same compact
        # separators as when it lived in bale_pack.
        report = _load_module("bale_report")
        line = report.format_context_pack_json(
            tarball=Path("/d/.bale/outbox/context-d.tar.gz"),
            directory=Path("/d"), tree_name="d", context_files=2,
            total_bytes=10, in_git=True)
        self.assertNotIn("\n", line)
        self.assertEqual(
            line,
            '{"outcome":"context-packed",'
            '"tarball":"/d/.bale/outbox/context-d.tar.gz",'
            '"directory":"/d","tree_name":"d","context_files":2,'
            '"total_bytes":10,"git":true}')

    def test_json_renderer_has_one_home(self) -> None:
        # The pack module no longer defines the renderer: two homes for
        # one outcome word is the drift the move exists to prevent.
        self.assertFalse(hasattr(self.m, "format_context_pack_json"))


# ---------------------------------------------------------------------------
# Normal packs untouched; bale open's pre-flight
# ---------------------------------------------------------------------------

class NormalPackUntouchedTest(_Sandbox):
    def setUp(self) -> None:
        super().setUp()
        self.repo = make_repo(self.tmp, self.home)

    def test_goal_less_piped_pack_still_refuses(self) -> None:
        r = run_bale(self.install, ["pack"], cwd=self.repo, env=self.env)
        self.assertRefused(r, "missing required arg(s) (goal, --slug)")

    def test_goal_less_tty_pack_still_enters_the_wizard(self) -> None:
        code, out = run_bale_pty(self.install, ["pack"], cwd=self.repo,
                                 env=self.env, answers="\x04")
        self.assertIn("interactive mode", out)
        self.assertFalse((self.repo / ".bale" / "outbox").exists()
                         and any((self.repo / ".bale" / "outbox")
                                 .glob("context-*")))

    def test_full_pack_still_ends_with_the_opener(self) -> None:
        r = run_bale(self.install, ["pack", "a normal goal", "--slug", "n",
                                    "--no-readme", "--include", "hello.txt"],
                     cwd=self.repo, env=self.env)
        self.assertOk(r)
        self.assertIn(OPENER_MARKERS[1], r.stdout)
        self.assertEqual(len(list((self.repo / ".bale" / "sessions")
                                  .iterdir())), 1)

    def test_open_preflight_refuses_a_context_argv(self) -> None:
        """pack_argv_preflight is bale open's gate before the checkpoint
        dry-run; driven in a child process whose __main__ carries bin/bale's
        fail(), the lazy-import surface the sibling expects."""
        script = (
            "import sys, importlib.machinery, importlib.util\n"
            "from pathlib import Path\n"
            f"bin_dir = Path({str(REPO_ROOT / 'bin')!r})\n"
            "sys.path.insert(0, str(bin_dir))\n"
            "loader = importlib.machinery.SourceFileLoader("
            "'bale_cli', str(bin_dir / 'bale'))\n"
            "spec = importlib.util.spec_from_loader('bale_cli', loader)\n"
            "cli = importlib.util.module_from_spec(spec)\n"
            "sys.modules['bale_cli'] = cli\n"
            "loader.exec_module(cli)\n"
            "import __main__\n"
            "__main__.fail = cli.fail\n"
            "import bale_pack\n"
            "args = cli.build_parser().parse_args("
            "['pack', '--context', '--no-readme'])\n"
            f"bale_pack.pack_argv_preflight(Path({str(self.repo)!r}), args)\n"
            "print('NOT REFUSED')\n"
        )
        # -B (v0.4.44, board row 125): this child imports the SOURCE
        # repo's own bin/ modules (not a scratch install's), under the
        # harness's scrubbed env, which carries no PYTHONDONTWRITEBYTECODE
        # — so without -B every run left an untracked bin/__pycache__ in
        # the repo under test. That is the one cache writer this session
        # found behind the report's "bin/__pycache__ ships in packs".
        r = subprocess.run([sys.executable, "-B", "-c", script],
                           cwd=self.repo, env=self.env, capture_output=True,
                           text=True, timeout=SUBPROCESS_TIMEOUT)
        self.assertNotEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertNotIn("NOT REFUSED", r.stdout)
        self.assertIn("carries --context", r.stderr)


# ---------------------------------------------------------------------------
# Cache hygiene (v0.4.44, board row 125)
# ---------------------------------------------------------------------------

class CacheHygieneTest(_Sandbox):
    """The report's claim — "bin/__pycache__ ships in packs" — pinned in
    the shape it was reported: a repo with a bin/__pycache__ and NO
    .gitignore, packed both as a request and as a context pack. Two
    caches per tree: one untracked (git lists it as --others) and one
    committed (git lists it as --cached — the harder case, since no
    ignore rule can hide it). Neither may ship; the walk's baked-in
    exclusion drops `__pycache__` by path component. The session that
    added this found no leak site in the pack walk; it did find a test
    child process writing the repo's own bin/__pycache__ (fixed with -B
    in test_open_preflight_refuses_a_context_argv above)."""

    def setUp(self) -> None:
        super().setUp()
        self.repo = make_repo(self.tmp, self.home)
        genv = git_env(self.home)
        (self.repo / "bin" / "__pycache__").mkdir(parents=True)
        (self.repo / "bin" / "tool.py").write_text("x = 1\n")
        (self.repo / "bin" / "__pycache__" / "committed.cpython-312.pyc") \
            .write_bytes(b"\0")
        run_checked(["git", "add", "-A"], cwd=self.repo, env=genv)
        run_checked(["git", "commit", "-m", "tree with a committed cache"],
                    cwd=self.repo, env=genv)
        (self.repo / "bin" / "__pycache__" / "untracked.cpython-312.pyc") \
            .write_bytes(b"\0")
        self.assertFalse((self.repo / ".gitignore").exists())

    def assertNoCacheMember(self, tarball: Path) -> dict:
        names = tar_members(tarball)
        self.assertFalse([n for n in names if "__pycache__" in n],
                         sorted(names))
        return names

    def test_request_pack_ships_no_cache_member(self) -> None:
        r = run_bale(self.install,
                     ["pack", "Cache hygiene goal", "--slug", "cache",
                      "--include", "bin", "--no-readme"],
                     cwd=self.repo, env=self.env)
        self.assertOk(r)
        [tarball] = sorted((self.repo / ".bale" / "outbox")
                           .glob("request-*.tar.gz"))
        names = self.assertNoCacheMember(tarball)
        self.assertTrue([n for n in names if n.endswith("bin/tool.py")],
                        "the source beside the cache still ships")

    def test_context_pack_ships_no_cache_member(self) -> None:
        self.assertOk(self.context(self.repo))
        names = self.assertNoCacheMember(
            self.repo / ".bale" / "outbox" / "context-project.tar.gz")
        self.assertIn("project/bin/tool.py", names)


if __name__ == "__main__":
    unittest.main()
