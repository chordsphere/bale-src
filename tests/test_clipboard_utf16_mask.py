#!/usr/bin/env python3
"""What bale puts on the clipboard (session 2026-11-12-clipboard-001,
0.4.59), from three slips about bale's copies:

- bale's own copy of a block arrives mangled on WSL: clip.exe fed UTF-8
  reads the console's code page (an em dash as U+0393 U+00C7 U+00F6),
  and only UTF-16LE with no byte-order mark arrives whole (the
  occupant's probe clipexe-encoding);
- the planner-facing exchange block was printed and copied only by
  `bale relay <sid>`, a second command, never at the clarification's
  landing where it is first needed;
- `bale clipboard`'s copy of a probe's output is the one copy the office
  cannot mask, and piped it is the only one: it should mask a URL's
  password and say so.

What this suite pins, by the brief's outcomes:

1. **clip.exe gets UTF-16LE, no BOM** (``ClipExeUnitTest``,
   ``ClipExeCopyTest``): a command whose first word has the base name
   clip.exe (bare or a path; any case) is fed every copy as UTF-16LE
   with no mark; any other command the UTF-8 bytes, unchanged. End to
   end through a fake clip.exe: pack's opener, relay's exchange block,
   apply's HOLD and APPLIED relays, the landing's block, `bale
   clipboard` (including input that is not UTF-8), and `bale open`'s
   opener.
2. **A clarification's landing prints and copies the exchange block**
   (``LandingBlockTest``): stdout carries the block byte for byte as
   `bale relay <sid>` re-emits it afterwards, the clipboard holds it
   when the landing ends, the notice is relay's, and the exit, the
   suspension and the trailer are unchanged; under --json stdout stays
   one line and the block rides stderr.
3. **bale clipboard masks a URL credential and says so**
   (``MaskUnitTest``, ``ClipboardMaskTest``): the password goes, the user
   and host stay, nothing else moves; the notice says "masked"; with
   nothing to mask the copy is the input byte for byte.
4. **Nothing else is masked** (``NothingElseMaskedTest``): an exchange
   record carrying a credential URL is copied with it, from relay and
   from the landing.

Sandbox doctrine per ADR-0005 (fully hermetic): the shared harness in
tests/harness.py carries it, and the clipboard is a capture file.

Run directly::

    python3 tests/test_clipboard_utf16_mask.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:  # the dotted run form needs it
    sys.path.insert(0, _TESTS_DIR)

from harness import (  # noqa: E402
    SUBPROCESS_TIMEOUT,
    build_response_dir,
    run_bale,
    tar_response_dir,
)
from test_clipboard_paste_blocks import (  # noqa: E402  (fixtures; no tests)
    _ClipboardMixin,
    _Fixture,
    between_scissors,
    notices,
    sentinel_block,
)
from test_open_verb import _OpenVerbBase  # noqa: E402  (fixture base)

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "bin"))
import bale_report  # noqa: E402  (path-injected sibling import)

# The probe's line, A U+2014 B U+00B7 C U+00E9 and a line feed.
PROBE_LINE = "A\u2014B\u00b7C\u00e9\n"
BOM = b"\xff\xfe"

# A question whose text carries a credential URL (outcome 4).
CREDENTIAL_URL = "https://alice:SECRET@example.com/x"
QUESTION = {
    "question": "Keep the mirror at " + CREDENTIAL_URL + " \u2014 or drop it?",
    "context": "fixture context \u2014 with an em dash",
    "default_assumption": "keep it",
    "why_blocked": "fixture blocker",
    "options": ["keep", "drop"],
    "recommendation": "keep",
}


def utf16(text_or_bytes) -> bytes:
    """The UTF-16LE, no-BOM bytes of a str or of UTF-8 bytes."""
    text = (text_or_bytes.decode("utf-8")
            if isinstance(text_or_bytes, bytes) else text_or_bytes)
    return text.encode("utf-16-le")


# ---------------------------------------------------------------------------
# Outcome 1, in process: which commands are clip.exe, and what they get
# ---------------------------------------------------------------------------

class ClipExeUnitTest(unittest.TestCase):

    def test_which_commands_are_clip_exe(self) -> None:
        yes = ("clip.exe", "/mnt/c/windows/system32/clip.exe",
               "/mnt/c/Windows/System32/clip.exe", "CLIP.EXE", "Clip.Exe",
               "clip.exe 2>/dev/null", "  clip.exe",
               "'/mnt/c/Program Files/x/clip.exe'",
               "C:\\\\Windows\\\\System32\\\\clip.exe")
        no = ("pbcopy", "cat >capture.txt", "xclip -selection clipboard",
              "clip", "clip.exe.bak", "myclip.exe", "/tmp/clip.exe/x",
              "cmd.exe /c clip", "env A=1 clip.exe", "echo clip.exe", "",
              "   ", None)
        for command in yes:
            with self.subTest(command=command):
                self.assertTrue(
                    bale_report.clipboard_command_is_clip_exe(command))
        for command in no:
            with self.subTest(command=command):
                self.assertFalse(
                    bale_report.clipboard_command_is_clip_exe(command))

    def test_unparseable_line_falls_back_to_a_whitespace_split(self) -> None:
        self.assertTrue(bale_report.clipboard_command_is_clip_exe(
            "clip.exe 'unterminated"))

    def test_clip_exe_payload_is_utf16le_without_a_mark(self) -> None:
        data = PROBE_LINE.encode("utf-8")
        payload, aside = bale_report.clipboard_payload("clip.exe", data)
        self.assertEqual(payload, bytes.fromhex(
            "4100 1420 4200 b700 4300 e900 0a00"))
        self.assertFalse(payload.startswith(BOM))
        self.assertEqual(aside, "")

    def test_ascii_is_utf16le_too(self) -> None:
        payload, _ = bale_report.clipboard_payload("clip.exe", b"ABC\n")
        self.assertEqual(payload, b"A\x00B\x00C\x00\n\x00")

    def test_other_commands_get_the_bytes_unchanged(self) -> None:
        data = PROBE_LINE.encode("utf-8")
        for command in ("pbcopy", "cat >x", "xclip", "clip"):
            with self.subTest(command=command):
                payload, aside = bale_report.clipboard_payload(command, data)
                self.assertIs(payload, data)
                self.assertEqual(aside, "")

    def test_bytes_not_utf8_are_replaced_and_said(self) -> None:
        payload, aside = bale_report.clipboard_payload(
            "clip.exe", b"ok \xff\xfe end\n")
        self.assertEqual(payload.decode("utf-16-le"),
                         "ok \ufffd\ufffd end\n")
        self.assertIn("not valid UTF-8", aside)
        self.assertIn("U+FFFD", aside)
        # Bound for any other command, they pass through as they came.
        payload, aside = bale_report.clipboard_payload("cat", b"\xff")
        self.assertEqual((payload, aside), (b"\xff", ""))


def _fake_clip_exe(directory: Path, capture: Path) -> Path:
    """An executable named clip.exe that writes its stdin to `capture`."""
    directory.mkdir(parents=True, exist_ok=True)
    prog = directory / "clip.exe"
    prog.write_text(f"#!/bin/sh\ncat >'{capture}'\n", encoding="utf-8")
    prog.chmod(0o755)
    return prog


class _ClipExeMixin:
    """A fake clip.exe on PATH and the global command naming it, bare
    (`clip.exe`, the occupant's spelling) or by its full path."""

    def use_clip_exe(self, *, full_path: bool = False) -> Path:
        prog = _fake_clip_exe(self.tmp / "winbin", self.capture)
        self.env["PATH"] = f"{prog.parent}{os.pathsep}{self.env['PATH']}"
        self.set_global(f'command = "{prog if full_path else "clip.exe"}"')
        return prog

    def assert_clip_holds(self, expected_utf8: bytes) -> None:
        got = self.clip()
        self.assertFalse(got.startswith(BOM), msg="no byte-order mark")
        self.assertEqual(got, utf16(expected_utf8))
        self.assertEqual(got.decode("utf-16-le").encode("utf-8"),
                         expected_utf8, msg="every character arrives whole")


def clarification_tarball(fixture, sid: str, name: str = "clar",
                          question: dict = None) -> Path:
    rdir = build_response_dir(
        fixture.tmp / name, sid,
        summary="clipboard fixture \u2014 blocked on one question",
        entries=[], validation_will_run=[],
        validation_sh="#!/usr/bin/env bash\n# No checks.\nexit 0\n",
        manifest_extra={"response_kind": "clarification",
                        "questions": [dict(question or QUESTION)]})
    return tar_response_dir(rdir)


def exchange_block_of(text: str, sid: str) -> bytes:
    return sentinel_block(text, f"BALE EXCHANGE BEGIN {sid}",
                          "BALE EXCHANGE END")


# ---------------------------------------------------------------------------
# Outcome 1, end to end: every copy bale makes reaches clip.exe whole
# ---------------------------------------------------------------------------

class ClipExeCopyTest(_ClipExeMixin, _Fixture):

    def bale(self, *args: str, verb_stdin: bytes = None):
        return run_bale(self.install, list(args), cwd=self.repo,
                        env=self.env)

    def test_pack_opener_bare_name(self) -> None:
        self.use_clip_exe()
        r = self.pack("clipopen", "--include", "hello.txt")
        self.assert_ok(r)
        self.assert_clip_holds(between_scissors(r.stdout))
        [line] = notices(r.stderr)
        self.assertIn("copied the session opener to the clipboard "
                      "(`clip.exe`, global bale.toml)", line)

    def test_pack_opener_full_path(self) -> None:
        self.use_clip_exe(full_path=True)
        r = self.pack("clippath", "--include", "hello.txt")
        self.assert_ok(r)
        self.assert_clip_holds(between_scissors(r.stdout))

    def test_relay_exchange_block_ingest_and_reemit(self) -> None:
        self.use_clip_exe()
        sid = self.packed("cliprelay")
        manifest = self.tmp / "m.json"
        manifest.write_text(json.dumps({
            "session_id": sid, "responds_to": sid, "corrects": None,
            "response_kind": "clarification", "summary": "s",
            "changes": [], "deferred": [], "validation_will_run": [],
            "claims": {}, "questions": [dict(QUESTION)]}), encoding="utf-8")
        ingest = self.bale("relay", sid, str(manifest))
        self.assert_ok(ingest)
        self.assertIn("\u2014", ingest.stdout, msg="the header's em dash")
        self.assert_clip_holds(ingest.stdout.encode("utf-8"))
        again = self.bale("relay", sid)
        self.assert_ok(again)
        self.assert_clip_holds(again.stdout.encode("utf-8"))

    def test_apply_hold_and_applied_relays(self) -> None:
        self.use_clip_exe(full_path=True)
        sid = self.packed("cliphold")
        rdir = build_response_dir(
            self.tmp / "held", sid, summary="clipboard fixture",
            entries=[{"path": "hello.txt", "action": "modified",
                      "reason": "the fixture's rewrite",
                      "data": b"rewrite held\n"}],
            validation_sh=("#!/usr/bin/env bash\n"
                           "echo \"[FAIL] fixture check\"\nexit 1\n"))
        held = self.bale("apply", str(tar_response_dir(rdir)))
        self.assert_ok(held, code=1)
        self.assert_clip_holds(sentinel_block(
            held.stdout, f"=== RELAY BEGIN {sid} to worker ===",
            f"=== RELAY END {sid} to worker ==="))
        self.capture.unlink()
        rdir = build_response_dir(
            self.tmp / "pass", sid, summary="clipboard fixture",
            entries=[{"path": "hello.txt", "action": "modified",
                      "reason": "the fixture's rewrite",
                      "data": b"rewrite pass\n"}],
            validation_sh=("#!/usr/bin/env bash\n"
                           "echo \"[PASS] fixture check\"\nexit 0\n"),
            manifest_extra={"corrects": sid})
        applied = self.bale("retry", str(tar_response_dir(rdir)))
        self.assert_ok(applied)
        block = sentinel_block(
            applied.stdout, f"=== RELAY BEGIN {sid} to planner ===",
            f"=== RELAY END {sid} to planner ===")
        self.assertIn("\u2014".encode("utf-8"), block)
        self.assert_clip_holds(block)

    def test_landing_block(self) -> None:
        self.use_clip_exe()
        sid = self.packed("clipland")
        land = self.bale("apply", str(clarification_tarball(self, sid)),
                         "--no-interact")
        self.assert_ok(land)
        self.assert_clip_holds(exchange_block_of(land.stdout, sid))

    def clipboard(self, data: bytes, *args: str):
        return subprocess.run(
            [sys.executable, str(self.install / "bin" / "bale"),
             "clipboard", *args],
            cwd=self.repo, env=self.env, input=data,
            capture_output=True, timeout=SUBPROCESS_TIMEOUT)

    def test_bale_clipboard_utf8_input(self) -> None:
        self.use_clip_exe()
        data = ("=== PROBE BEGIN x ===\n" + PROBE_LINE
                + "=== PROBE END x ===\n").encode("utf-8")
        r = self.clipboard(data, "--block", "probe block")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertEqual(r.stdout, b"")
        self.assert_clip_holds(data)
        [line] = notices(r.stderr.decode("utf-8"))
        self.assertNotIn("U+FFFD", line)

    def test_bale_clipboard_input_not_utf8_is_replaced_and_said(self) -> None:
        self.use_clip_exe()
        r = self.clipboard(b"bad \xff byte\n", "--block", "probe block")
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertEqual(self.clip(), utf16("bad \ufffd byte\n"))
        [line] = notices(r.stderr.decode("utf-8"))
        self.assertIn("copied the probe block", line)
        self.assertIn("not valid UTF-8", line)

    def test_any_other_command_is_fed_utf8_unchanged(self) -> None:
        self.capture_globally()
        data = PROBE_LINE.encode("utf-8") + b"\xff\n"
        r = self.clipboard(data)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertEqual(self.clip(), data)


class ClipExeOpenTest(_ClipExeMixin, _ClipboardMixin, _OpenVerbBase):

    def test_open_opener_reaches_clip_exe_whole(self) -> None:
        self.use_clip_exe()
        bundle = self.build_bundle(
            "plan.bale-bundle",
            pack_argv=["Plan the next wave", "--slug", "plan",
                       "--read-only", "--include", "hello.txt"])
        r = self.open_bundle(bundle)
        self.assert_ok(r)
        self.assert_clip_holds(between_scissors(r.stdout))


# ---------------------------------------------------------------------------
# Outcome 2: the landing prints and copies the exchange block
# ---------------------------------------------------------------------------

class LandingBlockTest(_Fixture):

    def bale(self, *args: str):
        return run_bale(self.install, list(args), cwd=self.repo,
                        env=self.env)

    def land(self, slug: str, *extra: str):
        sid = self.packed(slug)
        r = self.bale("apply", str(clarification_tarball(self, sid)),
                      "--no-interact", *extra)
        self.assert_ok(r)
        return sid, r

    def test_block_is_relays_byte_for_byte_and_on_the_clipboard(self) -> None:
        self.capture_globally()
        sid, land = self.land("landblock")
        block = exchange_block_of(land.stdout, sid)
        self.assertIn(b"from worker to planner", block)
        self.assertEqual(self.clip(), block,
                         msg="the clipboard holds BEGIN through END")
        [line] = notices(land.stderr)
        self.assertIn("copied the exchange block to the clipboard", line)
        self.capture.unlink()
        relay = self.bale("relay", sid)
        self.assert_ok(relay)
        self.assertEqual(relay.stdout.encode("utf-8"), block,
                         msg="byte for byte the block relay re-emits")
        self.assertEqual(self.clip(), block)
        [relay_line] = notices(relay.stderr)
        self.assertEqual(line, relay_line, msg="the notice is relay's")

    def test_landing_still_suspends_with_the_same_trailer(self) -> None:
        self.capture_globally()
        sid, land = self.land("landtrailer")
        self.assertIn(f"[CLARIFICATION] {sid}", land.stdout)
        self.assertIn(sid, self.open_sids(), msg="the session stays open")
        lines = [ln.strip() for ln in land.stdout.splitlines()]
        self.assertIn(f"bale relay {sid} <answer.json|->", lines)
        self.assertIn(f"(`bale relay {sid}` alone prints the exchange "
                      f"block to carry;", lines)
        # The banner prints after the block: the verdict stays last.
        self.assertLess(land.stdout.index("BALE EXCHANGE END"),
                        land.stdout.index(f"[CLARIFICATION] {sid}"))

    def test_the_landing_block_is_the_last_copy(self) -> None:
        log = self.tmp / "copies.log"
        self.set_global(f'command = "cat >>{log}; echo ---- >>{log}"')
        sid, land = self.land("landlast")
        copies = log.read_bytes().split(b"----\n")
        self.assertEqual(copies[-1], b"")
        self.assertEqual(copies[-2], exchange_block_of(land.stdout, sid))
        self.assertEqual(len(notices(land.stderr)), 1)

    def test_unset_clipboard_still_prints_the_block(self) -> None:
        sid, land = self.land("landunset")
        self.assertIn(f"BALE EXCHANGE BEGIN {sid}", land.stdout)
        self.assertEqual(notices(land.stderr), [])

    def test_failing_clipboard_keeps_the_exit(self) -> None:
        self.set_global('command = "exit 4"')
        sid, land = self.land("landfail")
        [line] = notices(land.stderr)
        self.assertIn("the exchange block was NOT copied", line)
        self.assertIn(f"BALE EXCHANGE BEGIN {sid}", land.stdout)

    def test_json_keeps_stdout_one_line_and_copies(self) -> None:
        self.capture_globally()
        sid, land = self.land("landjson", "--json")
        self.assertEqual(len(land.stdout.splitlines()), 1, msg=land.stdout)
        self.assertEqual(json.loads(land.stdout)["outcome"], "clarification")
        block = exchange_block_of(land.stderr, sid)
        self.assertEqual(self.clip(), block)
        relay = self.bale("relay", sid)
        self.assertEqual(relay.stdout.encode("utf-8"), block)

    def test_dry_run_prints_and_copies_nothing(self) -> None:
        self.capture_globally()
        sid = self.packed("landdry")
        self.capture.unlink()  # the pack's opener copy
        r = self.bale("apply", str(clarification_tarball(self, sid)),
                      "--dry-run", "--no-interact")
        self.assert_ok(r)
        self.assertNotIn("BALE EXCHANGE BEGIN", r.stdout + r.stderr)
        self.assertFalse(self.capture.exists())


class RenderRecordedRoundTest(unittest.TestCase):
    """bale_relay.render_recorded_round, the one rendering the landing
    and relay's re-emit share, in process."""

    def setUp(self) -> None:
        import tempfile
        import bale_relay
        self.relay = bale_relay
        self._tmp = tempfile.TemporaryDirectory(prefix="bale-render-")
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)

    def test_a_preserved_manifest_renders_as_its_worker_record(self) -> None:
        sid = "2026-11-12-x-001"
        path = self.dir / "001.json"
        manifest = {"session_id": sid, "response_kind": "clarification",
                    "questions": [dict(QUESTION)],
                    "preserved_at": "2026-11-12T01:00:00+00:00"}
        path.write_text(json.dumps(manifest), encoding="utf-8")
        got = self.relay.render_recorded_round(path, sid, 9)
        self.assertEqual((got.round, got.kind, got.side),
                         (1, "clarification manifest", "worker"))
        self.assertEqual(got.block, self.relay.format_exchange_block(sid, {
            "record_version": 1, "session_id": sid, "round": 1,
            "from": "worker", "created_at": "2026-11-12T01:00:00+00:00",
            "questions": [dict(QUESTION)]}))

    def test_unreadable_rounds_raise(self) -> None:
        bad = self.dir / "001.json"
        bad.write_text("{not json", encoding="utf-8")
        with self.assertRaises(self.relay.UnreadableRound) as cm:
            self.relay.render_recorded_round(bad, "s", 1)
        self.assertFalse(cm.exception.not_object)
        bad.write_text("[1]", encoding="utf-8")
        with self.assertRaises(self.relay.UnreadableRound) as cm:
            self.relay.render_recorded_round(bad, "s", 1)
        self.assertTrue(cm.exception.not_object)
        self.assertEqual(cm.exception.detail, "list")


# ---------------------------------------------------------------------------
# Outcome 3: `bale clipboard` masks a URL credential, and says so
# ---------------------------------------------------------------------------

class MaskUnitTest(unittest.TestCase):

    def mask(self, data: bytes) -> bale_report.MaskedCopy:
        return bale_report.mask_clipboard_credentials(data)

    def test_the_briefs_two_urls(self) -> None:
        for given, want in (
                (b"https://alice:SECRET@example.com/x",
                 b"https://alice:xxx@example.com/x"),
                (b"postgres://bob:p%40ss@db.internal:5432/app",
                 b"postgres://bob:xxx@db.internal:5432/app")):
            with self.subTest(given=given):
                got = self.mask(given)
                self.assertEqual(got.data, want)
                self.assertEqual((got.url_passwords, got.masked), (1, 1))

    def test_the_mask_holds_nothing_of_the_password(self) -> None:
        got = self.mask(b"x https://u:S3cr3t-Pa55@h.example/p y\n")
        self.assertNotIn(b"S3cr3t", got.data)
        self.assertNotIn(b"Pa55", got.data)
        self.assertEqual(got.data, b"x https://u:xxx@h.example/p y\n")

    def test_edges(self) -> None:
        for given, want, n in (
                # a raw '@' in the password: the host is after the last '@'
                (b"https://a:p@ss@host/x", b"https://a:xxx@host/x", 1),
                # no colon: a user name (or a bare token), left alone
                (b"https://TOKEN@host/x", b"https://TOKEN@host/x", 0),
                (b"ssh://git@github.com/o/r", b"ssh://git@github.com/o/r", 0),
                # a port, not a password
                (b"https://host:8080/x", b"https://host:8080/x", 0),
                (b"https://u:@host", b"https://u:@host", 0),
                # two URLs on a line, each its own authority
                (b"https://u:v@h,https://c:d@h2/ y",
                 b"https://u:xxx@h,https://c:xxx@h2/ y", 2),
                # quoted, and with no path
                (b"url='https://u:pw@h'", b"url='https://u:xxx@h'", 1),
                # an empty user name with a password
                (b"https://:pw@h/", b"https://:xxx@h/", 1),
                # not a URL
                (b"user:pass@host and a:b@c", b"user:pass@host and a:b@c", 0),
                # already the mask: unchanged and not counted
                (b"https://u:xxx@h", b"https://u:xxx@h", 0)):
            with self.subTest(given=given):
                got = self.mask(given)
                self.assertEqual(got.data, want)
                self.assertEqual(got.url_passwords, n)

    def test_github_tokens(self) -> None:
        token = b"ghp_" + b"A1b2" * 9
        got = self.mask(b"GITHUB_TOKEN=" + token + b"\n")
        self.assertEqual(got.data, b"GITHUB_TOKEN=ghp_xxx\n")
        self.assertEqual((got.github_tokens, got.url_passwords), (1, 0))
        got = self.mask(b"https://" + token + b"@github.com/o/r")
        self.assertEqual(got.data, b"https://ghp_xxx@github.com/o/r")
        pat = b"github_pat_" + b"Z" * 30
        self.assertEqual(self.mask(pat).data, b"github_pat_xxx")
        # Too short to be a token: left alone.
        self.assertEqual(self.mask(b"ghp_short").data, b"ghp_short")

    def test_nothing_to_mask_is_the_input_itself(self) -> None:
        data = ("plain text \u2014 https://example.com/a?b=c#d\n"
                ).encode("utf-8") + b"\xff\n"
        got = self.mask(data)
        self.assertEqual(got.data, data)
        self.assertEqual(got.masked, 0)

    def test_bytes_not_utf8_are_kept_around_the_mask(self) -> None:
        got = self.mask(b"\xff https://u:pw@h \xfe")
        self.assertEqual(got.data, b"\xff https://u:xxx@h \xfe")

    def test_aside(self) -> None:
        cases = ((0, 0, ""),
                 (1, 0, "; masked 1 URL password before copying"),
                 (2, 1, "; masked 2 URL passwords and 1 GitHub token "
                        "before copying"),
                 (0, 3, "; masked 3 GitHub tokens before copying"))
        for pw, tok, want in cases:
            with self.subTest(pw=pw, tok=tok):
                self.assertEqual(bale_report.masking_aside(
                    bale_report.MaskedCopy(b"", pw, tok)), want)


class ClipboardMaskTest(_Fixture):

    def clipboard(self, data: bytes):
        return subprocess.run(
            [sys.executable, str(self.install / "bin" / "bale"),
             "clipboard", "--block", "probe block"],
            cwd=self.repo, env=self.env, input=data,
            capture_output=True, timeout=SUBPROCESS_TIMEOUT)

    def test_masks_and_says_so(self) -> None:
        self.capture_globally()
        data = (b"=== PROBE BEGIN x ===\n"
                b"origin https://alice:SECRET@example.com/x (fetch)\n"
                b"DATABASE_URL=postgres://bob:p%40ss@db.internal:5432/app\n"
                b"=== PROBE END x ===\n")
        r = self.clipboard(data)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertEqual(r.stdout, b"")
        self.assertEqual(self.clip(), data
                         .replace(b"SECRET", b"xxx")
                         .replace(b"p%40ss", b"xxx"))
        [line] = notices(r.stderr.decode("utf-8"))
        self.assertIn("copied the probe block", line)
        self.assertIn("masked 2 URL passwords", line)

    def test_nothing_to_mask_copies_the_input_byte_for_byte(self) -> None:
        self.capture_globally()
        data = ("=== PROBE BEGIN x ===\nhttps://example.com/x \u2014 "
                "git@github.com:o/r\n=== PROBE END x ===\n").encode("utf-8")
        r = self.clipboard(data)
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertEqual(self.clip(), data)
        [line] = notices(r.stderr.decode("utf-8"))
        self.assertNotIn("mask", line)

    def test_masked_then_utf16le_for_clip_exe(self) -> None:
        prog = _fake_clip_exe(self.tmp / "winbin", self.capture)
        self.env["PATH"] = f"{prog.parent}{os.pathsep}{self.env['PATH']}"
        self.set_global('command = "clip.exe"')
        r = self.clipboard("https://u:pw@h \u2014\n".encode("utf-8"))
        self.assertEqual(r.returncode, 0, msg=r.stderr)
        self.assertEqual(self.clip(), utf16("https://u:xxx@h \u2014\n"))
        self.assertIn("masked 1 URL password",
                      notices(r.stderr.decode("utf-8"))[0])


# ---------------------------------------------------------------------------
# Outcome 4: nothing else is masked
# ---------------------------------------------------------------------------

class NothingElseMaskedTest(_Fixture):

    def bale(self, *args: str):
        return run_bale(self.install, list(args), cwd=self.repo,
                        env=self.env)

    def test_landing_and_relay_copy_the_credential_url_as_printed(self) -> None:
        self.capture_globally()
        sid = self.packed("nomask")
        land = self.bale("apply", str(clarification_tarball(self, sid)),
                         "--no-interact")
        self.assert_ok(land)
        block = exchange_block_of(land.stdout, sid)
        self.assertIn(CREDENTIAL_URL.encode("utf-8"), block)
        self.assertEqual(self.clip(), block)
        self.assertNotIn("mask", notices(land.stderr)[0])
        relay = self.bale("relay", sid)
        self.assert_ok(relay)
        self.assertEqual(self.clip(), relay.stdout.encode("utf-8"))
        self.assertIn(CREDENTIAL_URL.encode("utf-8"), self.clip())
        self.assertNotIn("mask", notices(relay.stderr)[0])

    def test_the_paste_points_never_call_the_mask(self) -> None:
        """Only bin/bale's cmd_clipboard calls the mask: every other
        paste point hands copy_paste_block its block as printed."""
        hits = []
        for path in sorted((REPO_ROOT / "bin").iterdir()):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for n, line in enumerate(text.splitlines(), 1):
                if ("mask_clipboard_credentials(" in line
                        and "def mask_clipboard_credentials" not in line):
                    hits.append((path.name, n))
        self.assertEqual([name for name, _ in hits], ["bale"], msg=hits)


if __name__ == "__main__":
    unittest.main()
