#!/usr/bin/env python3
"""The crafter's probe scaffold and bundle help (session
2026-11-12-probe-scaffold-002, 0.4.60), from three slips about bale and
one proposal of the clipboard session:

- the probe scaffold's purpose header should leave a slot for the run
  line, the command a person types to run the block where it belongs,
  so one copy of the block carries how to run it;
- the scaffold's secrets note should name remote URLs and `git remote
  -v` beside secret files, and offer a masked `git remote -v` snippet:
  a probe printed a remote URL with a personal access token;
- the `--bundle` help should say that a successor's stem is new;
- the no-bale fallback copy should be `bale clipboard`'s copy: masked,
  and UTF-16LE for clip.exe.

What this suite pins, by the brief's outcomes:

1. **The run line** (``RunLineTest``): `--probe SLUG --run-line LINE`
   writes `# LINE` directly after the `# Read-only:` line and before the
   `# Bound:` line and changes nothing else; a LINE with a line break, a
   blank LINE or one starting `#` is refused with nothing on stdout, as
   is `--run-line` without `--probe`; without it the header is as in
   0.4.59.
2. **The secrets note** (``SecretsNoteTest``): the note names secret
   files, remote URLs and `git remote -v`; exactly one comment line is
   the snippet, and run as written by bash in a git checkout it masks
   each URL password and GitHub token and keeps the rest.
3. **The bundle help** (``BundleSuccessorStemHelpTest``): the sentence,
   whole, in `--bundle`'s help at any width, and in the docstring.
4. **The fallback copy is bale's** (``ClipExeTwinTest``,
   ``MaskProgramParityTest``, ``FallbackCopyTest``,
   ``FallbackMatchesBaleClipboardTest``): the scaffold's mask program
   and clip.exe rule agree with bale_report's functions on one corpus,
   a crafted probe run without bale copies exactly what those functions
   make of its printed block, and exactly what the real `bale clipboard
   --block "probe block"` copies of it; the `[clipboard]` line says
   "masked"; without python3 (or when it fails) nothing is copied and
   stderr says why.

Run directly::

    python3 tests/test_probe_scaffold.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:  # the dotted run form needs it
    sys.path.insert(0, _TESTS_DIR)

from harness import SUBPROCESS_TIMEOUT, make_sandbox_home  # noqa: E402
from test_clipboard_paste_blocks import _Fixture  # noqa: E402  (fixture)

REPO_ROOT = Path(__file__).resolve().parent.parent
CRAFT = REPO_ROOT / "tools" / "craft_response.py"
TARBALL_MD = REPO_ROOT / "docs" / "TARBALL.md"
sys.path.insert(0, str(REPO_ROOT / "bin"))
import bale_report  # noqa: E402  (path-injected sibling import)


def _load_crafter():
    """tools/craft_response.py as a module (it is a script, not a
    package member), for its constants and pure helpers."""
    spec = importlib.util.spec_from_file_location("craft_response_ps",
                                                  CRAFT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


crafter = _load_crafter()

SLUG = "fixture-probe"
PLACEHOLDER = ('  echo "TODO(worker): unfilled probe placeholder '
               '\u2014 not ready to paste"\n')
TOKEN = "ghp_" + "Q7rT" * 9          # 36 characters after the prefix
PASSWORD = "S3cretPa55"
CREDENTIAL_LINES = (
    f"origin\thttps://alice:{PASSWORD}@example.com/r.git (fetch)",
    f"gh\thttps://{TOKEN}@github.com/o/r.git (push)",
    "plain\thttps://example.org/p.git (fetch) \u2014 caf\u00e9",
)


def run_craft(*argv: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(CRAFT), *argv], cwd=cwd,
                          capture_output=True, text=True,
                          timeout=SUBPROCESS_TIMEOUT)


def path_without_bale(*prepend: Path) -> str:
    """PATH minus every directory holding an executable `bale`, with
    `prepend` in front: the scaffold sees no installed bale."""
    dirs = [d for d in os.environ.get("PATH", "/usr/bin:/bin").split(
                os.pathsep)
            if d and not os.access(os.path.join(d, "bale"), os.X_OK)]
    return os.pathsep.join([str(d) for d in prepend] + dirs)


def fill_body(script: str, lines) -> str:
    """The scaffold with its placeholder echo replaced by one printf per
    line of `lines` (printf, so a tab and any byte arrive as given)."""
    body = "".join(f"  printf '%s\\n' '{ln}'\n" for ln in lines)
    assert PLACEHOLDER in script, "the scaffold's placeholder moved"
    return script.replace(PLACEHOLDER, body)


def bale_copy(command: str, block: bytes) -> tuple:
    """(payload, aside) bale 0.4.59+ makes of `block` for `command`:
    mask_clipboard_credentials, then clipboard_payload — the order
    cmd_clipboard and copy_paste_block apply them in."""
    masked = bale_report.mask_clipboard_credentials(block)
    payload, encoding_aside = bale_report.clipboard_payload(command,
                                                            masked.data)
    return payload, bale_report.masking_aside(masked) + encoding_aside


def fake_clip_exe(directory: Path, capture: Path) -> Path:
    """An executable named clip.exe that writes its stdin to `capture`."""
    directory.mkdir(parents=True, exist_ok=True)
    prog = directory / "clip.exe"
    prog.write_text(f"#!/bin/sh\ncat >'{capture}'\n", encoding="utf-8")
    prog.chmod(0o755)
    return prog


class _TmpCase(unittest.TestCase):

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-probe-sc-")
        self.tmp = Path(self._tmp.name)
        self.addCleanup(self._tmp.cleanup)

    def craft(self, *argv: str) -> subprocess.CompletedProcess:
        return run_craft("--probe", SLUG, *argv, cwd=self.tmp)

    def set_key(self, command: str) -> None:
        (self.tmp / "bale.toml").write_text(
            f'[clipboard]\ncommand = "{command}"\n', encoding="utf-8")

    def run_script(self, text: str, *, path: str | None = None
                   ) -> subprocess.CompletedProcess:
        script = self.tmp / "probe.sh"
        script.write_text(text, encoding="utf-8")
        bash = shutil.which("bash") or "/bin/bash"
        chk = subprocess.run([bash, "-n", str(script)],
                             capture_output=True, text=True)
        self.assertEqual(chk.returncode, 0, chk.stderr)
        env = dict(os.environ)
        env["PATH"] = path if path is not None else path_without_bale()
        return subprocess.run([bash, str(script)], cwd=self.tmp, env=env,
                              capture_output=True,
                              timeout=SUBPROCESS_TIMEOUT)

    def assert_banners(self, run: subprocess.CompletedProcess) -> None:
        lines = run.stdout.decode("utf-8", "replace").splitlines()
        self.assertEqual(lines[0], f"=== PROBE BEGIN {SLUG} ===")
        self.assertEqual(lines[-1], f"=== PROBE END {SLUG} ===")


# ---------------------------------------------------------------------------
# Outcome 1: the run line
# ---------------------------------------------------------------------------

class RunLineTest(_TmpCase):

    RUN_LINE = "office: probe 43 --sid S"

    def test_the_line_sits_between_read_only_and_bound(self) -> None:
        cp = self.craft("--run-line", self.RUN_LINE)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        lines = cp.stdout.splitlines()
        self.assertTrue(lines[1].startswith(f"# PROBE {SLUG}: "))
        self.assertTrue(lines[2].startswith("# Why: "))
        self.assertEqual(lines[3], "# Read-only: writes nothing anywhere; "
                                   "stdout is the only output.")
        self.assertEqual(lines[4], "# office: probe 43 --sid S")
        self.assertTrue(lines[5].startswith("# Bound: "))

    def test_the_line_is_verbatim_and_the_only_change(self) -> None:
        plain = self.craft()
        self.assertEqual(plain.returncode, 0, plain.stderr)
        for line in (self.RUN_LINE,
                     "office probe 43 --project bale-src --sid "
                     "2026-11-12-x-001",
                     "  two  spaces, $HOME and `ticks` {braces} 'q' \"dq\"",
                     "caf\u00e9 \u2014 probe"):
            with self.subTest(line=line):
                cp = self.craft("--run-line", line)
                self.assertEqual(cp.returncode, 0, cp.stderr)
                got = cp.stdout.splitlines(keepends=True)
                self.assertEqual(got[4], f"# {line}\n")
                self.assertEqual("".join(got[:4] + got[5:]), plain.stdout)

    def test_without_the_flag_the_header_is_as_before(self) -> None:
        cp = self.craft()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        lines = cp.stdout.splitlines()
        self.assertTrue(lines[3].startswith("# Read-only: "))
        self.assertTrue(lines[4].startswith("# Bound: "))
        self.assertEqual(lines[5], "")
        self.assertEqual(lines[6], "probe() {")

    def test_refused_lines_print_nothing_on_stdout(self) -> None:
        for bad in ("a\nb", "a\rb", "trailing\n", "a\u2028b", "", "   ",
                    "# office: probe 43", "  #x"):
            with self.subTest(bad=bad):
                cp = self.craft(f"--run-line={bad}")
                self.assertNotEqual(cp.returncode, 0)
                self.assertEqual(cp.stdout, "")
                self.assertIn("--run-line", cp.stderr)

    def test_run_line_needs_probe(self) -> None:
        cp = run_craft("--run-line", self.RUN_LINE, "--sid", "s-001",
                       cwd=self.tmp)
        self.assertEqual(cp.returncode, 2, cp.stderr)
        self.assertEqual(cp.stdout, "")
        self.assertIn("--run-line goes with --probe only", cp.stderr)

    def test_the_scaffold_with_a_run_line_still_runs(self) -> None:
        cp = self.craft("--run-line", self.RUN_LINE)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        run = self.run_script(cp.stdout)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assert_banners(run)

    def test_tarball_md_names_the_flag_and_the_line(self) -> None:
        text = TARBALL_MD.read_text(encoding="utf-8")
        start = text.index("### 4.2 The paste-back probe")
        section = text[start:text.index("### 4.3 ", start)]
        self.assertIn("--run-line", section)
        self.assertIn("# Read-only:", section)
        self.assertIn("# Bound:", section)


# ---------------------------------------------------------------------------
# Outcome 2: the secrets note and its masked git remote -v line
# ---------------------------------------------------------------------------

def snippet_lines(script: str) -> list:
    """Every comment line whose text, after its `#` and any spaces, is a
    command starting `git remote -v |` — that text."""
    found = []
    for line in script.splitlines():
        stripped = line.lstrip()
        if not stripped.startswith("#"):
            continue
        text = stripped[1:].lstrip()
        if text.startswith("git remote -v |"):
            found.append(text)
    return found


class SecretsNoteTest(_TmpCase):

    def scaffold(self) -> str:
        cp = self.craft()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return cp.stdout

    def test_the_note_names_files_urls_and_git_remote(self) -> None:
        comments = "\n".join(ln for ln in self.scaffold().splitlines()
                             if ln.lstrip().startswith("#"))
        for needle in (".env*", "*.pem", "remote URL", "git remote -v",
                       "password", "token", "TARBALL.md 4.3"):
            with self.subTest(needle=needle):
                self.assertIn(needle, comments)

    def test_exactly_one_line_is_the_snippet(self) -> None:
        self.assertEqual(len(snippet_lines(self.scaffold())), 1)

    def git_env(self) -> dict:
        home = make_sandbox_home(self.tmp)
        return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": str(home), "GIT_CONFIG_NOSYSTEM": "1",
                "LANG": os.environ.get("LANG", "C.UTF-8")}

    def checkout(self, remotes: dict) -> tuple:
        repo = self.tmp / "checkout"
        repo.mkdir()
        env = self.git_env()
        subprocess.run(["git", "init", "-q", str(repo)], env=env,
                       check=True, timeout=SUBPROCESS_TIMEOUT)
        for name, url in remotes.items():
            subprocess.run(["git", "remote", "add", name, url], cwd=repo,
                           env=env, check=True, timeout=SUBPROCESS_TIMEOUT)
        return repo, env

    @unittest.skipUnless(shutil.which("git") and shutil.which("sed"),
                         "the snippet needs git and sed on PATH")
    def test_the_snippet_masks_as_written(self) -> None:
        [snippet] = snippet_lines(self.scaffold())
        repo, env = self.checkout({
            "origin": f"https://alice:{PASSWORD}@example.com/r.git",
            "gh": f"https://{TOKEN}@github.com/o/r.git",
            "bot": f"https://x-access-token:{TOKEN.replace('ghp', 'ghs')}"
                   "@github.com/o/bot.git",
            "pat": "https://github_pat_" + "Ab1_" * 6 + "@github.com/o/p.git",
            "plain": "https://example.org/p.git",
            "scp": "git@example.net:o/s.git",
        })
        bare = subprocess.run(["git", "remote", "-v"], cwd=repo, env=env,
                              capture_output=True, text=True, check=True)
        run = subprocess.run([shutil.which("bash") or "/bin/bash", "-c",
                              snippet], cwd=repo, env=env,
                             capture_output=True, text=True,
                             timeout=SUBPROCESS_TIMEOUT)
        self.assertEqual(run.returncode, 0, run.stderr)
        out = run.stdout
        self.assertNotIn(PASSWORD, out)
        self.assertNotIn(TOKEN[4:], out)
        self.assertNotIn("Ab1_" * 6, out)
        for kept in ("origin", "alice", "example.com/r.git",
                     "github.com/o/r.git", "x-access-token",
                     "github.com/o/bot.git", "github.com/o/p.git"):
            with self.subTest(kept=kept):
                self.assertIn(kept, out)
        self.assertEqual(len(out.splitlines()), len(bare.stdout.splitlines()))
        for line in bare.stdout.splitlines():
            if line.startswith(("plain\t", "scp\t")):
                with self.subTest(line=line):
                    self.assertIn(line, out.splitlines(),
                                  "a remote with no credential prints as is")

    def test_tarball_md_secrets_rule_names_remote_urls(self) -> None:
        text = TARBALL_MD.read_text(encoding="utf-8")
        start = text.index("- **Secrets-aware.**")
        rule = text[start:text.index("\n- **", start + 1)]
        self.assertIn("`.env*`", rule)
        self.assertIn("Remote URLs", rule)
        self.assertIn("`git remote -v`", rule)


# ---------------------------------------------------------------------------
# Outcome 3: the bundle help says a successor's stem is new
# ---------------------------------------------------------------------------

class BundleSuccessorStemHelpTest(unittest.TestCase):

    LINE = "A successor's bundle takes a stem no earlier bundle of its slug had."

    def test_help_carries_the_sentence_whole_at_any_width(self) -> None:
        for columns in ("40", "80", "200"):
            with self.subTest(columns=columns):
                env = {**os.environ, "COLUMNS": columns}
                cp = subprocess.run([sys.executable, str(CRAFT), "--help"],
                                    capture_output=True, text=True, env=env,
                                    timeout=SUBPROCESS_TIMEOUT)
                self.assertEqual(cp.returncode, 0, cp.stderr)
                self.assertEqual(cp.stdout.count(self.LINE), 1)
                options_at = cp.stdout.index("\noptions:\n")
                bundle_at = cp.stdout.index("--bundle STEM", options_at)
                next_flag = cp.stdout.index("--pack-arg TOKEN", bundle_at)
                self.assertTrue(
                    bundle_at < cp.stdout.index(self.LINE) < next_flag)

    def test_the_constant_and_the_docstring_carry_it(self) -> None:
        self.assertEqual(crafter.BUNDLE_SUCCESSOR_STEM_LINE, self.LINE)
        self.assertIn(self.LINE, crafter.UNWRAPPED_HELP_SENTENCES)
        self.assertIn(self.LINE, crafter.__doc__)


# ---------------------------------------------------------------------------
# Outcome 4: the fallback copy is bale clipboard's copy
# ---------------------------------------------------------------------------

CLIP_EXE_YES = ("clip.exe", "/mnt/c/windows/system32/clip.exe",
                "/mnt/c/Windows/System32/clip.exe", "CLIP.EXE", "Clip.Exe",
                "clip.exe 2>/dev/null", "  clip.exe",
                "'/mnt/c/Program Files/x/clip.exe'",
                "C:\\\\Windows\\\\System32\\\\clip.exe",
                "clip.exe 'unterminated")
CLIP_EXE_NO = ("pbcopy", "cat >capture.txt", "xclip -selection clipboard",
               "clip", "clip.exe.bak", "myclip.exe", "/tmp/clip.exe/x",
               "cmd.exe /c clip", "env A=1 clip.exe", "echo clip.exe", "",
               "   ", None)


class ClipExeTwinTest(unittest.TestCase):
    """The crafter decides the fallback's encoding at craft time by its
    twin of bale's clip.exe rule; the two agree on every command."""

    def test_the_twin_agrees_with_bale(self) -> None:
        for command in CLIP_EXE_YES + CLIP_EXE_NO:
            with self.subTest(command=command):
                self.assertEqual(
                    crafter.clip_command_is_clip_exe(command),
                    bale_report.clipboard_command_is_clip_exe(command))
        self.assertTrue(all(crafter.clip_command_is_clip_exe(c)
                            for c in CLIP_EXE_YES))
        self.assertFalse(any(crafter.clip_command_is_clip_exe(c)
                             for c in CLIP_EXE_NO))


# The parity corpus: bale's own mask edges (tests/test_clipboard_utf16_mask
# .py), the brief's two remotes, tokens, bytes that are not UTF-8, a
# byte-order mark in the input, and plain text.
PARITY_CORPUS = (
    b"",
    b"plain text, nothing to mask\n",
    "plain \u2014 caf\u00e9 \u00b7 https://example.com/a?b=c#d\n".encode(),
    b"https://alice:SECRET@example.com/x",
    b"postgres://bob:p%40ss@db.internal:5432/app",
    b"x https://u:S3cr3t-Pa55@h.example/p y\n",
    b"https://a:p@ss@host/x",
    b"https://TOKEN@host/x",
    b"ssh://git@github.com/o/r",
    b"https://host:8080/x",
    b"https://u:@host",
    b"https://u:v@h,https://c:d@h2/ y",
    b"url='https://u:pw@h'",
    b'url="https://u:pw@h" and `https://v:qq@k`',
    b"https://:pw@h/",
    b"user:pass@host and a:b@c",
    b"https://u:xxx@h",
    b"GITHUB_TOKEN=" + TOKEN.encode() + b"\n",
    b"https://" + TOKEN.encode() + b"@github.com/o/r",
    b"github_pat_" + b"Z" * 30,
    b"ghp_short",
    b"gho_" + b"a" * 40 + b" ghu_" + b"b" * 36 + b" ghs_" + b"c" * 36
    + b" ghr_" + b"d" * 255 + b"e",
    b"\xff https://u:pw@h \xfe",
    b"bad \xff byte\n",
    b"\xef\xbb\xbfa BOM first\n",
    "\n".join(CREDENTIAL_LINES).encode() + b"\n",
    b"=== PROBE BEGIN x ===\norigin https://alice:SECRET@example.com/x "
    b"(fetch)\n--- integrity: 1 lines ---\n=== PROBE END x ===\n",
    b"x" * 70 + b"://u:pw@h " + b"a+b.c-d://u:pw@h " + b"9x://u:pw@h",
)


class MaskProgramParityTest(unittest.TestCase):
    """PROBE_FALLBACK_MASK_PY, run the way the scaffold runs it, against
    mask_clipboard_credentials + clipboard_payload + masking_aside."""

    def run_program(self, mode: str, encoding: str, data: bytes) -> bytes:
        cp = subprocess.run(
            [sys.executable, "-I", "-B", "-c", crafter.PROBE_FALLBACK_MASK_PY,
             mode, encoding], input=data, capture_output=True,
            timeout=SUBPROCESS_TIMEOUT)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return cp.stdout

    def test_copy_and_aside_match_bale_on_the_corpus(self) -> None:
        for command, encoding in (
                ("clip.exe", crafter.PROBE_FALLBACK_ENCODING_CLIP_EXE),
                ("cat >capture.txt", crafter.PROBE_FALLBACK_ENCODING_OTHER)):
            for data in PARITY_CORPUS:
                with self.subTest(command=command, data=data[:60]):
                    want_payload, want_aside = bale_copy(command, data)
                    self.assertEqual(
                        self.run_program("copy", encoding, data),
                        want_payload)
                    self.assertEqual(
                        self.run_program("aside", encoding,
                                         data).decode("utf-8"),
                        want_aside)

    def test_the_corpus_exercises_every_branch(self) -> None:
        """A parity corpus that never masks proves nothing."""
        results = [bale_report.mask_clipboard_credentials(d)
                   for d in PARITY_CORPUS]
        self.assertTrue(any(r.url_passwords > 1 for r in results))
        self.assertTrue(any(r.github_tokens > 1 for r in results))
        self.assertTrue(any(r.masked == 0 for r in results))
        self.assertTrue(any(bale_report.clipboard_payload("clip.exe", d)[1]
                            for d in PARITY_CORPUS))

    def test_the_program_survives_bash_single_quotes_and_history(self) -> None:
        program = crafter.PROBE_FALLBACK_MASK_PY
        self.assertNotIn("'", program, "it rides in a single-quoted string")
        self.assertNotIn("!", program,
                         "an interactive bash would history-expand it")
        epilogue = crafter.PROBE_CLIPBOARD_FALLBACK_EPILOGUE
        self.assertNotIn("!", epilogue.replace("$!", ""))


class FallbackCopyTest(_TmpCase):
    """A crafted probe run where bale is not on PATH copies, through the
    request's command, exactly bale's copy of the block it printed."""

    def keyed_scaffold(self, command: str) -> str:
        self.set_key(command)
        cp = self.craft()
        self.assertEqual(cp.returncode, 0, cp.stderr)
        return fill_body(cp.stdout, CREDENTIAL_LINES)

    def clipboard_line(self, run: subprocess.CompletedProcess) -> str:
        lines = [ln for ln in run.stderr.decode("utf-8").splitlines()
                 if ln.startswith("[clipboard] ")
                 and "bale is not on PATH" not in ln]
        self.assertEqual(len(lines), 1, run.stderr)
        return lines[0]

    def test_utf8_command_gets_the_masked_block(self) -> None:
        capture = self.tmp / "capture.bin"
        command = f"cat >{capture}"
        run = self.run_script(self.keyed_scaffold(command))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assert_banners(run)
        self.assertIn(PASSWORD.encode(), run.stdout, "stdout is as printed")
        want, aside = bale_copy(command, run.stdout)
        self.assertEqual(capture.read_bytes(), want)
        self.assertNotIn(PASSWORD.encode(), want)
        self.assertNotIn(TOKEN[4:].encode(), want)
        self.assertIn(b"alice:xxx@example.com", want)
        line = self.clipboard_line(run)
        self.assertIn("probe output copied", line)
        self.assertIn("; masked 1 URL password and 1 GitHub token", line)
        self.assertTrue(line.endswith(aside))

    def test_clip_exe_by_name_and_by_path_gets_utf16le(self) -> None:
        capture = self.tmp / "clip-capture.bin"
        prog = fake_clip_exe(self.tmp / "winbin", capture)
        for command in ("clip.exe", str(prog)):
            with self.subTest(command=command):
                capture.unlink(missing_ok=True)
                run = self.run_script(self.keyed_scaffold(command),
                                      path=path_without_bale(prog.parent))
                self.assertEqual(run.returncode, 0, run.stderr)
                self.assert_banners(run)
                want, _ = bale_copy(command, run.stdout)
                got = capture.read_bytes()
                self.assertEqual(got, want)
                self.assertFalse(got.startswith(b"\xff\xfe"),
                                 "no byte-order mark")
                self.assertIn("\u2014 caf\u00e9", got.decode("utf-16-le"))
                line = self.clipboard_line(run)
                self.assertIn("masked", line)
                self.assertIn("UTF-16LE", line)

    def test_nothing_to_mask_is_the_printed_block(self) -> None:
        capture = self.tmp / "capture.bin"
        self.set_key(f"cat >{capture}")
        cp = self.craft()
        run = self.run_script(cp.stdout)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertEqual(capture.read_bytes(), run.stdout)
        self.assertNotIn("mask", self.clipboard_line(run))

    def tool_dir(self, *, python3: str | None) -> Path:
        """A PATH directory holding only what the scaffold runs (bash,
        env, timeout, wc, tr, cat), plus `python3` as given: None for
        none, else a shell body for a stub."""
        tools = self.tmp / "tools"
        tools.mkdir(exist_ok=True)
        for name in ("bash", "env", "timeout", "wc", "tr", "cat"):
            found = shutil.which(name)
            if found and not (tools / name).exists():
                (tools / name).symlink_to(found)
        if python3 is not None:
            stub = tools / "python3"
            stub.write_text("#!/bin/sh\n" + python3, encoding="utf-8")
            stub.chmod(0o755)
        return tools

    def test_without_python3_nothing_is_copied_and_stderr_says_so(self) -> None:
        capture = self.tmp / "capture.bin"
        script = self.keyed_scaffold(f"cat >{capture}")
        run = self.run_script(script, path=str(self.tool_dir(python3=None)))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assert_banners(run)
        self.assertFalse(capture.exists(), "never an unmasked copy")
        line = self.clipboard_line(run)
        self.assertIn("not copied", line)
        self.assertIn("python3", line)

    def test_a_failing_python3_copies_nothing(self) -> None:
        capture = self.tmp / "capture.bin"
        script = self.keyed_scaffold(f"cat >{capture}")
        run = self.run_script(script, path=str(self.tool_dir(
            python3="cat >/dev/null\necho boom >&2\nexit 3\n")))
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assert_banners(run)
        self.assertFalse(capture.exists())
        self.assertIn("could not mask", self.clipboard_line(run))

    def test_a_failing_command_is_named_not_the_mask(self) -> None:
        run = self.run_script(self.keyed_scaffold("false"))
        self.assertEqual(run.returncode, 0, run.stderr)
        line = self.clipboard_line(run)
        self.assertIn("failed or is missing", line)
        self.assertNotIn("BrokenPipe", run.stderr.decode("utf-8"))


class FallbackMatchesBaleClipboardTest(_Fixture):
    """End to end: the fallback's copy of a printed block is what this
    release's `bale clipboard --block "probe block"` copies of the same
    block through the same command, byte for byte."""

    def bale_clipboard(self, data: bytes) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, str(self.install / "bin" / "bale"),
             "clipboard", "--block", "probe block"],
            cwd=self.repo, env=self.env, input=data, capture_output=True,
            timeout=SUBPROCESS_TIMEOUT)

    def crafted_run(self, command: str, extra_path: Path | None = None
                    ) -> subprocess.CompletedProcess:
        work = self.tmp / "probe-work"
        work.mkdir(exist_ok=True)
        (work / "bale.toml").write_text(
            f'[clipboard]\ncommand = "{command}"\n', encoding="utf-8")
        cp = run_craft("--probe", SLUG, cwd=work)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        script = work / "probe.sh"
        script.write_text(fill_body(cp.stdout, CREDENTIAL_LINES),
                          encoding="utf-8")
        env = dict(os.environ)
        env["PATH"] = (path_without_bale(extra_path) if extra_path
                       else path_without_bale())
        return subprocess.run([shutil.which("bash") or "/bin/bash",
                               str(script)], cwd=work, env=env,
                              capture_output=True,
                              timeout=SUBPROCESS_TIMEOUT)

    def test_utf8_command(self) -> None:
        fallback_capture = self.tmp / "fallback.bin"
        run = self.crafted_run(f"cat >{fallback_capture}")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.capture_globally()
        r = self.bale_clipboard(run.stdout)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(b"masked", r.stderr)
        self.assertEqual(fallback_capture.read_bytes(), self.clip())

    def test_clip_exe_command(self) -> None:
        prog = fake_clip_exe(self.tmp / "winbin", self.capture)
        run = self.crafted_run("clip.exe", extra_path=prog.parent)
        self.assertEqual(run.returncode, 0, run.stderr)
        fallback = self.clip()
        self.capture.unlink()
        self.env["PATH"] = f"{prog.parent}{os.pathsep}{self.env['PATH']}"
        self.set_global('command = "clip.exe"')
        r = self.bale_clipboard(run.stdout)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(fallback, self.clip())
        self.assertFalse(fallback.startswith(b"\xff\xfe"))


if __name__ == "__main__":
    unittest.main()
