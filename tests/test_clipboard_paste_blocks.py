#!/usr/bin/env python3
"""Every operator-side paste block, copied to the configured clipboard
command (session clipboard-paste-blocks, the friction-points arc's
session D).

Driven end to end against a scratch install and a scratch repo
(ADR-0005). The clipboard command is a capture — `cat >capture.txt`
in the install's global bale.toml, the per-machine layer — so what
"landed on the clipboard" is a file the test reads byte for byte.

Pinned, outcome by outcome (the brief's section 4):

- **Every paste point copies exactly what the operator pastes.** pack's
  session opener (human and --json: the lines between the scissor
  lines), `bale open`'s second-desk opener, `bale relay`'s exchange
  block on ingest and on the no-file re-emit (BEGIN through END),
  `bale apply`'s APPLIED relay block, and `bale retry`'s on a PASS.
- **A HOLD copies the block the card names under `send first:`** — the
  worker block when only the worker held, the planner block when the
  checkpoint held — and the notice names the block left printed.
- **A copy never changes what a command does.** pack --json keeps
  stdout to its one JSON line; relay keeps stdout to the block, byte-
  identical to an unconfigured run; a failing clipboard command leaves
  pack's, relay's, and apply's exit codes and a HOLD's exit alone and
  says the copy did not happen.
- **An unreadable key never takes a command down.** A triple-quoted
  key skips the copy with a notice naming the problem and the remedy;
  pack, relay, and apply still succeed.
- **Unset means no copy, and nothing is detected.** With pbcopy,
  xclip, xsel, wl-copy, and clip.exe all on PATH and no key, nothing
  runs and nothing is said; a project's `clipboard_command = ""`
  suppresses the global value.
- **`bale status` gains the clipboard row**: command and layer,
  suppressed, unset, and UNREADABLE with the reason — exit 0 always.
- **The probe copies through the installed bale.** A scaffold crafted
  with no bale.toml anywhere, run with a `bale` on PATH, lands its
  PROBE BEGIN/END block on the global command; a project value
  overrides it.
- **`bale clipboard`**, the verb the probe pipes into: 0 copied, 1 not
  copied (with the reason), 2 on a terminal stdin; nothing on stdout.
- **In-process units**: the runner returns while a forked selection
  owner (xclip, wl-copy) still holds its stderr, stops a hung command
  at the timeout, cannot deadlock on a command that never reads, and
  names the exit plus the first stderr line; plus the pure helpers
  (opener_paste_text, the status row's values, the refusal reason).

Run:  python3 -m unittest tests.test_clipboard_paste_blocks -v
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from harness import (
    SUBPROCESS_TIMEOUT,
    build_response_dir,
    run_bale,
    run_bale_pty,
    run_checked,
    tar_response_dir,
)
from test_open_verb import _OpenVerbBase  # noqa: E402  (fixture base; no tests)
from test_per_sid_checkpoint import CP_PATTERN, PerSidFixture  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
CRAFTER = REPO_ROOT / "tools" / "craft_response.py"
sys.path.insert(0, str(REPO_ROOT / "bin"))
import bale_report  # noqa: E402  (path-injected sibling import)
from bale_pack import (  # noqa: E402
    OPENER_BEGIN,
    OPENER_END,
    opener_paste_text,
    session_opener_block,
)

NOTICE = "[bale] clipboard: "
DETECTABLE = ("pbcopy", "xclip", "xsel", "wl-copy", "clip.exe")


def path_without_bale(*prepend: Path) -> str:
    """PATH minus every directory holding an executable `bale`, with
    `prepend` in front: a scaffold run sees exactly the bale a test
    provides, never the developer's real install."""
    dirs = [d for d in os.environ.get("PATH", "/usr/bin:/bin").split(
                os.pathsep)
            if d and not os.access(os.path.join(d, "bale"), os.X_OK)]
    return os.pathsep.join([str(d) for d in prepend] + dirs)


def notices(stderr: str) -> list:
    return [ln for ln in stderr.splitlines() if ln.startswith(NOTICE)]


def between_scissors(text: str) -> bytes:
    """The opener's paste text as printed: the lines strictly between
    the scissor lines, LF-joined, one trailing LF."""
    lines = text.splitlines()
    i = lines.index(OPENER_BEGIN)
    j = lines.index(OPENER_END, i + 1)
    return ("\n".join(lines[i + 1:j]) + "\n").encode("utf-8")


def sentinel_block(text: str, begin: str, end: str) -> bytes:
    """BEGIN line through END line, inclusive, LF-joined, trailing LF."""
    lines = text.splitlines()
    i = lines.index(begin)
    j = lines.index(end, i + 1)
    return ("\n".join(lines[i:j + 1]) + "\n").encode("utf-8")


class _ClipboardMixin:
    """Clipboard knobs over a fixture that has self.tmp, self.install,
    self.repo, self.env (PerSidFixture or _OpenVerbBase). No tests."""

    @property
    def capture(self) -> Path:
        return self.tmp / "clipboard-capture.txt"

    def global_toml(self) -> Path:
        return self.install / "user" / "bale.toml"

    def set_global(self, line: str) -> None:
        self.global_toml().parent.mkdir(parents=True, exist_ok=True)
        self.global_toml().write_text(f"[probe]\n{line}\n", encoding="utf-8")

    def capture_globally(self) -> None:
        self.set_global(f'clipboard_command = "cat >{self.capture}"')

    def clip(self) -> bytes:
        self.assertTrue(self.capture.is_file(),
                        msg="nothing reached the clipboard command")
        return self.capture.read_bytes()

    def assert_ok(self, r, code: int = 0) -> None:
        self.assertEqual(r.returncode, code,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")


class _Fixture(_ClipboardMixin, PerSidFixture):
    """PerSidFixture plus the clipboard knobs. Holds no tests."""

    def packed(self, slug: str, *extra: str) -> str:
        r = self.pack(slug, "--include", "hello.txt", *extra)
        self.assert_ok(r)
        matches = [s for s in self.open_sids() if f"-{slug}-" in s]
        self.assertEqual(len(matches), 1, msg=f"{self.open_sids()}")
        return matches[0]


# ---------------------------------------------------------------------------
# The session opener (pack)
# ---------------------------------------------------------------------------

class PackOpenerCopyTest(_Fixture):

    def test_human_pack_copies_the_lines_between_the_scissors(self) -> None:
        self.capture_globally()
        r = self.pack("opener", "--include", "hello.txt")
        self.assert_ok(r)
        self.assertEqual(self.clip(), between_scissors(r.stdout))
        self.assertNotIn(OPENER_BEGIN.encode(), self.clip())
        [line] = notices(r.stderr)
        self.assertIn("copied the session opener", line)
        self.assertIn("global bale.toml", line)
        self.assertNotIn(NOTICE, r.stdout, msg="notices ride stderr")
        self.assertEqual(r.stdout.splitlines()[-1], OPENER_END,
                         msg="the printed report still ends on the opener")

    def test_json_pack_keeps_one_stdout_line_and_copies(self) -> None:
        self.capture_globally()
        r = self.pack("openjson", "--include", "hello.txt", "--json")
        self.assert_ok(r)
        self.assertEqual(len(r.stdout.splitlines()), 1, msg=r.stdout)
        self.assertEqual(json.loads(r.stdout)["outcome"], "packed")
        self.assertEqual(self.clip(), between_scissors(r.stderr))
        self.assertEqual(len(notices(r.stderr)), 1)

    def test_failing_command_changes_nothing_but_the_notice(self) -> None:
        self.set_global('clipboard_command = "echo boom >&2; exit 3"')
        r = self.pack("openfail", "--include", "hello.txt")
        self.assert_ok(r)
        [line] = notices(r.stderr)
        self.assertIn("the session opener was NOT copied", line)
        self.assertIn("exited 3 (boom)", line)
        self.assertEqual(r.stdout.splitlines()[-1], OPENER_END)
        self.assertEqual(len(self.open_sids()), 1, msg="the pack landed")

    def test_unreadable_global_key_skips_with_reason_and_remedy(self) -> None:
        self.global_toml().parent.mkdir(parents=True, exist_ok=True)
        self.global_toml().write_text(
            "[probe]\nclipboard_command = '''cat >/dev/null'''\n",
            encoding="utf-8")
        r = self.pack("openbad", "--include", "hello.txt")
        self.assert_ok(r)
        [line] = notices(r.stderr)
        self.assertIn("NOT copied", line)
        self.assertIn("is triple-quoted", line)
        self.assertIn("bale config init --global", line)
        self.assertNotIn("[bale] error:", r.stderr,
                         msg="the refusal is a notice, not an error")
        self.assertEqual(len(self.open_sids()), 1)

    def test_unreadable_key_journals_the_notice_not_an_error(self) -> None:
        """Session log-hold's rider: the copy reads the key through the
        non-exiting clipboard_command_reading, so the session log holds
        the "NOT copied" notice and no `[bale] error:` entry above it
        (session D's fail()-routed read journaled one)."""
        self.global_toml().parent.mkdir(parents=True, exist_ok=True)
        self.global_toml().write_text(
            "[probe]\nclipboard_command = '''cat >/dev/null'''\n",
            encoding="utf-8")
        sid = self.packed("journal")
        journal = (self.repo / ".bale" / "logs" / f"{sid}.log").read_text(
            encoding="utf-8")
        self.assertNotIn("[bale] error:", journal)
        noticed = [ln for ln in journal.splitlines()
                   if "[bale] clipboard: the session opener was NOT copied"
                   in ln]
        self.assertEqual(len(noticed), 1, msg=journal)
        self.assertIn("is triple-quoted", noticed[0])

    def test_unset_copies_nothing_with_clipboard_programs_on_path(self) -> None:
        fakebin = self.tmp / "fakebin"
        fakebin.mkdir()
        for name in DETECTABLE:
            prog = fakebin / name
            prog.write_text(f"#!/bin/sh\ntouch {self.tmp}/ran-{name}\n",
                            encoding="utf-8")
            prog.chmod(0o755)
        self.env["PATH"] = f"{fakebin}{os.pathsep}{self.env['PATH']}"
        r = self.pack("unset", "--include", "hello.txt")
        self.assert_ok(r)
        self.assertEqual(notices(r.stderr), [],
                         msg="no opt-in, nothing said")
        self.assertEqual(sorted(p.name for p in self.tmp.glob("ran-*")), [],
                         msg="nothing is detected at run time")

    def test_project_suppress_beats_the_global(self) -> None:
        self.capture_globally()
        self.commit_files({"bale.toml": '[probe]\nclipboard_command = ""\n'},
                          "suppress the clipboard here")
        r = self.pack("suppressed", "--include", "hello.txt")
        self.assert_ok(r)
        self.assertFalse(self.capture.exists())
        self.assertEqual(notices(r.stderr), [])

    def test_project_value_overrides_the_global(self) -> None:
        self.capture_globally()
        project_capture = self.tmp / "project-capture.txt"
        self.commit_files(
            {"bale.toml": f'[probe]\nclipboard_command = '
                          f'"cat >{project_capture}"\n'},
            "a project clipboard command")
        r = self.pack("override", "--include", "hello.txt")
        self.assert_ok(r)
        self.assertFalse(self.capture.exists())
        self.assertEqual(project_capture.read_bytes(),
                         between_scissors(r.stdout))
        self.assertIn("project bale.toml", notices(r.stderr)[0])


# ---------------------------------------------------------------------------
# The exchange block (relay)
# ---------------------------------------------------------------------------

def clarification_manifest(sid: str) -> dict:
    return {
        "session_id": sid, "responds_to": sid, "corrects": None,
        "response_kind": "clarification",
        "summary": "blocked on one question (fixture)",
        "changes": [], "deferred": [], "validation_will_run": [],
        "claims": {},
        "questions": [{
            "question": "fixture question?", "context": "fixture context",
            "default_assumption": "fixture assumption",
            "why_blocked": "fixture blocker",
            "options": ["yes", "no"], "recommendation": "yes",
        }],
    }


class RelayCopyTest(_Fixture):

    def setUp(self) -> None:
        super().setUp()
        self.sid = self.packed("relay")
        self.manifest = self.tmp / "m.json"
        self.manifest.write_text(
            json.dumps(clarification_manifest(self.sid)), encoding="utf-8")

    def relay(self, *args: str):
        return subprocess.run(
            [sys.executable, str(self.install / "bin" / "bale"), "relay",
             self.sid, *args],
            cwd=self.repo, env=self.env, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=SUBPROCESS_TIMEOUT)

    def test_ingest_copies_the_block_and_stdout_is_exactly_it(self) -> None:
        self.capture_globally()
        r = self.relay(str(self.manifest))
        self.assert_ok(r)
        self.assertTrue(r.stdout.startswith(f"BALE EXCHANGE BEGIN {self.sid}"))
        self.assertTrue(r.stdout.endswith("BALE EXCHANGE END\n"))
        self.assertEqual(self.clip(), r.stdout.encode("utf-8"),
                         msg="the clipboard holds BEGIN through END")
        [line] = notices(r.stderr)
        self.assertIn("copied the exchange block", line)

    def test_reemit_copies_and_stdout_is_byte_identical_to_unset(self) -> None:
        self.assert_ok(self.relay(str(self.manifest)))
        unset = self.relay()
        self.assert_ok(unset)
        self.assertEqual(notices(unset.stderr), [])
        self.capture_globally()
        configured = self.relay()
        self.assert_ok(configured)
        self.assertEqual(configured.stdout, unset.stdout,
                         msg="copying never changes the printed block")
        self.assertEqual(self.clip(), configured.stdout.encode("utf-8"))

    def test_failing_or_unreadable_command_keeps_exit_and_stdout(self) -> None:
        self.assert_ok(self.relay(str(self.manifest)))
        baseline = self.relay()
        for line, needle in (('clipboard_command = "false"', "exited 1"),
                             ("clipboard_command = '''x'''",
                              "is triple-quoted")):
            with self.subTest(line=line):
                self.set_global(line)
                r = self.relay()
                self.assert_ok(r)
                self.assertEqual(r.stdout, baseline.stdout)
                [notice] = notices(r.stderr)
                self.assertIn("NOT copied", notice)
                self.assertIn(needle, notice)


# ---------------------------------------------------------------------------
# The HOLD and APPLIED relay blocks (apply, retry)
# ---------------------------------------------------------------------------

def probe_checkpoint(verdicts: list, exit_code: int) -> str:
    body = "".join(f'echo "[{v}] {label}"\n' for v, label in verdicts)
    return f"#!/usr/bin/env bash\n{body}exit {exit_code}\n"


class ApplyRelayCopyTest(_Fixture):

    def response(self, sid: str, *, worker_exit: int, name: str,
                 extra: dict = None) -> Path:
        verdict = "FAIL" if worker_exit else "PASS"
        rdir = build_response_dir(
            self.tmp / name, sid, summary="clipboard fixture",
            entries=[{"path": "hello.txt", "action": "modified",
                      "reason": "the fixture's rewrite",
                      "data": f"rewrite {name}\n".encode("utf-8")}],
            validation_sh=("#!/usr/bin/env bash\n"
                           f"echo \"[{verdict}] fixture check\"\n"
                           f"exit {worker_exit}\n"),
            manifest_extra=extra)
        return tar_response_dir(rdir)

    def apply(self, tarball: Path, verb: str = "apply"):
        return run_bale(self.install, [verb, str(tarball)],
                        cwd=self.repo, env=self.env)

    @staticmethod
    def relay_block(stdout: str, sid: str, addressee: str) -> bytes:
        return sentinel_block(stdout,
                              f"=== RELAY BEGIN {sid} to {addressee} ===",
                              f"=== RELAY END {sid} to {addressee} ===")

    def test_worker_held_copies_the_worker_block(self) -> None:
        self.capture_globally()
        sid = self.packed("whold")
        r = self.apply(self.response(sid, worker_exit=1, name="held"))
        self.assert_ok(r, code=1)
        self.assertIn("send first: worker", r.stdout)
        self.assertEqual(self.clip(), self.relay_block(r.stdout, sid,
                                                       "worker"))
        [line] = notices(r.stderr)
        self.assertIn("copied the HOLD relay block to the worker "
                      "(send first)", line)
        self.assertIn("HOLD relay block to the planner stays printed above, "
                      "not copied", line)

    def test_checkpoint_held_copies_the_planner_block(self) -> None:
        self.capture_globally()
        self.configure_base(CP_PATTERN)
        source = self.tmp / "cp.sh"
        source.write_text(probe_checkpoint([("FAIL", "probe-alpha")], 1),
                          encoding="utf-8")
        r = self.pack("cphold", "--include", "hello.txt",
                      "--checkpoint-file", str(source))
        self.assert_ok(r)
        [sid] = [s for s in self.open_sids() if "-cphold-" in s]
        r = self.apply(self.response(sid, worker_exit=0, name="held"))
        self.assert_ok(r, code=1)
        self.assertIn("send first: planner", r.stdout)
        self.assertEqual(self.clip(), self.relay_block(r.stdout, sid,
                                                       "planner"))
        [line] = notices(r.stderr)
        self.assertIn("HOLD relay block to the planner (send first)", line)
        self.assertIn("HOLD relay block to the worker stays printed above",
                      line)
        self.assertIn("only after the planner rules", line)

    def test_clean_apply_copies_the_applied_relay(self) -> None:
        self.capture_globally()
        sid = self.packed("pass")
        r = self.apply(self.response(sid, worker_exit=0, name="pass"))
        self.assert_ok(r)
        self.assertEqual(self.clip(), self.relay_block(r.stdout, sid,
                                                       "planner"))
        self.assertIn(b"APPLIED", self.clip())
        [line] = notices(r.stderr)
        self.assertIn("copied the APPLIED relay block", line)

    def test_retry_to_pass_copies_the_applied_relay(self) -> None:
        self.capture_globally()
        sid = self.packed("retry")
        self.assert_ok(self.apply(
            self.response(sid, worker_exit=1, name="first")), code=1)
        self.capture.unlink()
        r = self.apply(self.response(sid, worker_exit=0, name="second",
                                     extra={"corrects": sid}),
                       verb="retry")
        self.assert_ok(r)
        self.assertIn(f"APPLIED — session {sid}", r.stdout)
        self.assertEqual(self.clip(), self.relay_block(r.stdout, sid,
                                                       "planner"))

    def test_failing_or_unreadable_command_keeps_the_exit_codes(self) -> None:
        for line, needle in (('clipboard_command = "false"', "exited 1"),
                             ("clipboard_command = '''x'''",
                              "is triple-quoted")):
            with self.subTest(line=line):
                self.set_global(line)
                slug = "kf" if "false" in line else "ku"
                sid = self.packed(slug + "hold")
                held = self.apply(self.response(sid, worker_exit=1,
                                                name=f"{slug}-held"))
                self.assert_ok(held, code=1)
                self.assertIn("NOT copied", notices(held.stderr)[0])
                self.assertIn(needle, notices(held.stderr)[0])
                run_checked(["git", "branch", "-D", f"bale/{sid}"],
                            cwd=self.repo, env=self.genv)
                self.assert_ok(run_bale(self.install, ["unlock", sid],
                                        cwd=self.repo, env=self.env))
                sid = self.packed(slug + "pass")
                applied = self.apply(self.response(sid, worker_exit=0,
                                                   name=f"{slug}-pass"))
                self.assert_ok(applied)
                self.assertIn("NOT copied", notices(applied.stderr)[0])


# ---------------------------------------------------------------------------
# The second-desk opener (bale open)
# ---------------------------------------------------------------------------

class SecondDeskCopyTest(_ClipboardMixin, _OpenVerbBase):

    def test_both_desks_copy_their_own_opener(self) -> None:
        self.capture_globally()
        bundle = self.build_bundle(
            "plan.bale-bundle",
            pack_argv=["Plan the next wave", "--slug", "plan",
                       "--read-only", "--include", "hello.txt"])
        first = self.open_bundle(bundle)
        self.assert_ok(first)
        self.assertEqual(self.clip(), between_scissors(first.stdout),
                         msg="desk one: the replayed pack copies")
        second = self.open_bundle(bundle)
        self.assert_ok(second)
        self.assertIn(b"@desk-2", self.clip())
        self.assertEqual(self.clip(), between_scissors(second.stdout))
        self.assertEqual(len(notices(second.stderr)), 1)


# ---------------------------------------------------------------------------
# `bale clipboard` and the status row
# ---------------------------------------------------------------------------

class ClipboardVerbTest(_Fixture):

    def clipboard(self, data: bytes, *args: str, cwd: Path = None):
        return subprocess.run(
            [sys.executable, str(self.install / "bin" / "bale"),
             "clipboard", *args],
            cwd=cwd or self.repo, env=self.env, input=data,
            capture_output=True, timeout=SUBPROCESS_TIMEOUT)

    def test_copies_stdin_unchanged_and_writes_no_stdout(self) -> None:
        self.capture_globally()
        data = "=== PROBE BEGIN x ===\nnon-ASCII é\n=== PROBE END x ===\n"
        for cwd in (self.repo, self.tmp):  # in a repo, and outside one
            with self.subTest(cwd=cwd):
                r = self.clipboard(data.encode("utf-8"), "--block",
                                   "probe block", cwd=cwd)
                self.assertEqual(r.returncode, 0, msg=r.stderr)
                self.assertEqual(r.stdout, b"")
                self.assertEqual(self.clip(), data.encode("utf-8"))
                self.assertIn(b"copied the probe block", r.stderr)

    def test_not_copied_exits_one_and_says_why(self) -> None:
        r = self.clipboard(b"x\n")
        self.assertEqual(r.returncode, 1)
        self.assertIn(b"no clipboard command is configured", r.stderr)
        self.assertIn(b"bale config init --global", r.stderr)
        for line, needle in (('clipboard_command = "false"', b"exited 1"),
                             ("clipboard_command = '''x'''",
                              b"is triple-quoted")):
            with self.subTest(line=line):
                self.set_global(line)
                r = self.clipboard(b"x\n")
                self.assertEqual(r.returncode, 1)
                self.assertEqual(r.stdout, b"")
                self.assertIn(needle, r.stderr)
        self.capture_globally()
        self.assertEqual(self.clipboard(b"").returncode, 1,
                         msg="an empty stdin copies nothing")

    def test_terminal_stdin_is_refused_with_exit_two(self) -> None:
        code, output = run_bale_pty(self.install, ["clipboard"],
                                    cwd=self.repo, env=self.env, answers="")
        self.assertEqual(code, 2, msg=output)
        self.assertIn("pipe the block into it", output)

    def test_help_names_the_key_the_layers_and_the_exit_codes(self) -> None:
        r = run_bale(self.install, ["help", "clipboard"], cwd=self.repo,
                     env=dict(self.env, COLUMNS="80"))
        self.assert_ok(r)
        flat = " ".join(r.stdout.split())
        for phrase in ("[probe] clipboard_command",
                       "`bale config init --global`",
                       "Nothing is detected at run time",
                       "Exit 0 when the block was copied, 1 when it was not",
                       "--block NAME"):
            self.assertIn(phrase, flat)


class StatusClipboardRowTest(_Fixture):

    def row(self) -> str:
        r = run_bale(self.install, ["status"], cwd=self.repo,
                     env=dict(self.env, COLUMNS="400"))
        self.assert_ok(r)
        hits = [ln.strip() for ln in r.stdout.splitlines()
                if ln.strip().startswith("probe clipboard:")]
        self.assertEqual(len(hits), 1, msg=r.stdout)
        return hits[0][len("probe clipboard:"):].strip()

    def test_each_state_reads_as_a_row(self) -> None:
        self.assertIn("unset", self.row())
        self.assertIn("bale config init --global", self.row())
        self.set_global('clipboard_command = "pbcopy"')
        self.assertTrue(self.row().startswith("pbcopy (global layer)"))
        (self.repo / "bale.toml").write_text(
            '[probe]\nclipboard_command = "wl-copy"\n', encoding="utf-8")
        self.assertTrue(self.row().startswith("wl-copy (project layer)"))
        (self.repo / "bale.toml").write_text(
            '[probe]\nclipboard_command = ""\n', encoding="utf-8")
        self.assertTrue(self.row().startswith("suppressed here"))
        (self.repo / "bale.toml").write_text(
            "[probe]\nclipboard_command = '''pbcopy'''\n", encoding="utf-8")
        row = self.row()
        self.assertTrue(row.startswith("UNREADABLE"), msg=row)
        self.assertIn("is triple-quoted", row)

    def test_row_outside_a_repo(self) -> None:
        self.set_global('clipboard_command = "pbcopy"')
        r = run_bale(self.install, ["status"], cwd=self.tmp,
                     env=dict(self.env, COLUMNS="400"))
        self.assert_ok(r)
        self.assertIn("probe clipboard: pbcopy (global layer)", r.stdout)


# ---------------------------------------------------------------------------
# The probe, through the installed bale
# ---------------------------------------------------------------------------

@unittest.skipUnless(CRAFTER.is_file(), "tools/ not shipped in this sandbox")
class ProbeThroughInstalledBaleTest(_Fixture):
    """A probe crafted with no bale.toml anywhere still copies: the
    scaffold asks the installed bale, which reads the per-machine key."""

    SLUG = "fixture-probe"

    def scaffold(self) -> Path:
        crafting_dir = self.tmp / "desk"
        crafting_dir.mkdir()
        cp = subprocess.run([sys.executable, str(CRAFTER), "--probe",
                             self.SLUG], cwd=crafting_dir,
                            capture_output=True, text=True,
                            timeout=SUBPROCESS_TIMEOUT)
        self.assertEqual(cp.returncode, 0, cp.stderr)
        self.assertIn("no bale.toml found", cp.stderr)
        script = self.tmp / "probe.sh"
        script.write_text(cp.stdout, encoding="utf-8")
        return script

    def bale_on_path(self) -> Path:
        bindir = self.tmp / "onpath"
        bindir.mkdir()
        shim = bindir / "bale"
        shim.write_text(f'#!/bin/sh\nexec "{sys.executable}" '
                        f'"{self.install / "bin" / "bale"}" "$@"\n',
                        encoding="utf-8")
        shim.chmod(0o755)
        return bindir

    def run_probe(self, script: Path):
        env = dict(self.env, PATH=path_without_bale(self.bale_on_path()))
        return subprocess.run(["bash", str(script)], cwd=self.repo, env=env,
                              capture_output=True, text=True,
                              timeout=SUBPROCESS_TIMEOUT)

    def test_global_key_copies_the_sentinel_block(self) -> None:
        self.capture_globally()
        r = self.run_probe(self.scaffold())
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        lines = r.stdout.splitlines()
        self.assertEqual(lines[0], f"=== PROBE BEGIN {self.SLUG} ===")
        self.assertEqual(lines[-1], f"=== PROBE END {self.SLUG} ===")
        self.assertEqual(self.clip(), r.stdout.encode("utf-8"))
        self.assertIn("copied the probe block", r.stderr)
        self.assertEqual(list(self.install.rglob("__pycache__")), [],
                         msg="the probe stays read-only: no bytecode caches")

    def test_project_value_overrides_the_global_for_the_probe(self) -> None:
        self.capture_globally()
        project_capture = self.tmp / "project-capture.txt"
        (self.repo / "bale.toml").write_text(
            f'[probe]\nclipboard_command = "cat >{project_capture}"\n',
            encoding="utf-8")
        r = self.run_probe(self.scaffold())
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertFalse(self.capture.exists())
        self.assertEqual(project_capture.read_bytes(),
                         r.stdout.encode("utf-8"))

    def test_unset_never_fails_the_probe_and_names_the_remedy(self) -> None:
        r = self.run_probe(self.scaffold())
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertIn("PROBE BEGIN", r.stdout)
        self.assertIn("bale config init --global", r.stderr)


# ---------------------------------------------------------------------------
# In-process units: the runner's edges and the pure helpers
# ---------------------------------------------------------------------------

class RunClipboardCommandUnitTest(unittest.TestCase):
    """run_clipboard_command never hangs bale and always says why."""

    def test_success_delivers_the_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / "c"
            ok, detail = bale_report.run_clipboard_command(
                f"cat >{out}", "é\n".encode("utf-8"))
            self.assertEqual((ok, detail), (True, ""))
            self.assertEqual(out.read_bytes(), "é\n".encode("utf-8"))

    def test_failure_names_the_exit_and_first_stderr_line(self) -> None:
        ok, detail = bale_report.run_clipboard_command(
            "echo first >&2; echo second >&2; exit 4", b"x")
        self.assertFalse(ok)
        self.assertEqual(detail, "exited 4 (first)")

    def test_a_forked_owner_holding_stderr_does_not_block(self) -> None:
        """xclip and wl-copy fork a selection owner that keeps the pipe
        open; bale returns when the command itself exits."""
        start = time.monotonic()
        ok, _ = bale_report.run_clipboard_command(
            "cat >/dev/null; (sleep 5 >&2 &); exit 0", b"x", timeout=4)
        self.assertTrue(ok)
        self.assertLess(time.monotonic() - start, 3)

    def test_a_hung_command_is_stopped_at_the_timeout(self) -> None:
        start = time.monotonic()
        ok, detail = bale_report.run_clipboard_command("sleep 30", b"x",
                                                       timeout=0.5)
        self.assertFalse(ok)
        self.assertIn("did not finish within 0.5s", detail)
        self.assertLess(time.monotonic() - start, 5)

    def test_exit_zero_with_the_block_half_read_is_not_a_copy(self) -> None:
        """A background child holding stdin without reading it: the
        command exits 0, but the clipboard did not get the block."""
        start = time.monotonic()
        ok, detail = bale_report.run_clipboard_command(
            "exec 3<&0; (sleep 20 <&3 &); exit 0", b"a" * 4_000_000,
            timeout=5)
        self.assertFalse(ok)
        self.assertIn("before reading the whole block", detail)
        self.assertLess(time.monotonic() - start, 8)

    def test_a_timeout_stops_the_whole_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as d:
            marker = Path(d) / "survived"
            ok, _ = bale_report.run_clipboard_command(
                f"cat >/dev/null; sleep 2 | (sleep 1; touch {marker})",
                b"x", timeout=0.3)
            self.assertFalse(ok)
            time.sleep(1.5)
            self.assertFalse(marker.exists(),
                             msg="the pipeline's children were stopped too")

    def test_a_command_that_never_reads_cannot_deadlock(self) -> None:
        ok, _ = bale_report.run_clipboard_command("true", b"a" * 4_000_000,
                                                  timeout=5)
        self.assertTrue(ok)


class PureHelperUnitTest(unittest.TestCase):

    def test_opener_paste_text_is_strictly_between_the_scissors(self) -> None:
        block = session_opener_block(
            "2026-10-04-fx-001", "a goal", read_only=False,
            packed_at="2026-10-04T00:00:00+00:00", has_readme=True)
        text = opener_paste_text(block)
        i, j = block.index(OPENER_BEGIN), block.index(OPENER_END)
        self.assertEqual(text, "\n".join(block[i + 1:j]) + "\n")
        self.assertTrue(text.startswith("I'm using \"bale\""))
        self.assertNotIn("--8<--", text)
        with self.assertRaises(ValueError):
            opener_paste_text(["no", "scissors"])

    def test_status_row_values(self) -> None:
        d = bale_report.describe_clipboard_state
        self.assertTrue(d("pbcopy", "global", None).startswith(
            "pbcopy (global layer)"))
        self.assertTrue(d(None, "project", None).startswith(
            "suppressed here"))
        self.assertIn("bale config init --global", d(None, None, None))
        self.assertTrue(d(None, "global", "x is triple-quoted").startswith(
            "UNREADABLE"))

    def test_refusal_reason_strips_the_error_prefix(self) -> None:
        exc = SystemExit(1)
        self.assertEqual(bale_report._refusal_reason(
            "[bale] error: f: probe.clipboard_command is triple-quoted.\n",
            exc), "f: probe.clipboard_command is triple-quoted.")
        exc.bale_cause = "the cause"
        self.assertEqual(bale_report._refusal_reason("", exc), "the cause")


if __name__ == "__main__":
    unittest.main(verbosity=2)
