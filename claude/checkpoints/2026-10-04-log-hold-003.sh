#!/usr/bin/env bash
# Blind checkpoint — session log-hold (friction-points cleanup, queued item 1).
# Authored at desk 2026-10-04-friction-points-cleanup-002 from the request,
# before the work exists. Outcome probes only; every probe drives the tree
# under test (the staging copy in cwd) from a fresh fixture under $TMPDIR.
#
# Exit codes (TARBALL.md §7.5): 0 every probe passed; 1 a probe failed,
# including a crash, hang, or nonzero exit of the code under test inside a
# fixture step; 2 the oracle's own machinery broke (a failed control, git
# or file setup, no pty).
#
# Probes:
#   walk-quiet       goal-less read-only pack with a sweepable session: no
#                    "[bale] " line from the first item header through the
#                    README prompt
#   walk-width       every line from the wizard title through the README
#                    prompt fits 80 columns (the sweep's y/N included)
#   walk-replay      the sweep's held close line prints after the README
#                    prompt, and the swept session is closed
#   prewalk-width    every line before the wizard title fits 80 columns
#   sweep-enter / sweep-yes / sweep-x / sweep-eof
#                    the fully specified read-only pack's sweep y/N on a
#                    pty: Enter and "yes" close the session; "x" and EOF
#                    leave it open, nothing re-asks, the pack exits 0
#   sweep-width      that prompt's lines fit 80 columns
#   clip-journal     an unreadable clipboard key: the pack still exits 0,
#                    the not-copied notice prints, and the session log
#                    carries no "[bale] error:" line
#   cli-help-verb    tests/test_cli_help.py's COMMANDS enumerates the
#                    clipboard verb
#   no-main-rebind   no module under bin/ rebinds a log or fail attribute
set -u
export PYTHONDONTWRITEBYTECODE=1
exec python3 -B - "$PWD" <<'PY'
import ast, fcntl, json, os, pty, re, select, shutil, signal, struct
import subprocess, sys, tempfile, termios, time, unicodedata
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
WIDTH = 80
TITLE = "bale pack — interactive mode"
ITEM_RE = re.compile(r"^\s*(\d+)/(\d+)  (\S+)")
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b[@-Z\\-_]")
EOF_KEY = "\x04"
RESULTS = []


class Broken(Exception):
    """The oracle's own machinery failed: exit 2."""


class UnderTest(Exception):
    """The code under test crashed, hung, or exited nonzero: a FAIL."""


def visible(line):
    line = ANSI_RE.sub("", line)
    if "\r" in line:
        line = line.rsplit("\r", 1)[1]
    return line


def width(line):
    n = 0
    for ch in visible(line):
        if unicodedata.combining(ch):
            continue
        n += 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1
    return n


def lines_of(text):
    return [visible(ln) for ln in text.replace("\r\n", "\n").split("\n")]


LABELS = {
    "walk-quiet": "walk-quiet: no [bale] line from the first walk question "
                  "through the README question",
    "walk-width": "walk-width: every walk line, the sweep's y/N included, "
                  "fits 80 columns",
    "walk-replay": "walk-replay: held lines print after the README question "
                   "and the swept session closes",
    "prewalk-width": "prewalk-width: every line before the walk's title "
                     "fits 80 columns",
    "sweep-enter": "sweep-enter: Enter at the sweep's y/N closes the session",
    "sweep-yes": "sweep-yes: 'yes' at the sweep's y/N closes the session",
    "sweep-x": "sweep-x: an unknown answer declines without re-asking",
    "sweep-eof": "sweep-eof: EOF at the sweep's y/N declines",
    "sweep-width": "sweep-width: the fully specified read-only pack's sweep "
                   "y/N fits 80 columns",
    "clip-journal": "clip-journal: an unreadable clipboard key journals no "
                    "[bale] error: line",
    "cli-help-verb": "cli-help-verb: test_cli_help.py's COMMANDS enumerates "
                     "the clipboard verb",
    "no-main-rebind": "no-main-rebind: no module under bin/ rebinds a log or "
                      "fail attribute",
}


def record(key, ok, detail=""):
    """One verdict line, label only (the HOLD relay carries labels alone);
    the detail goes on indented lines below it for the session log."""
    RESULTS.append((key, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {LABELS[key]}")
    if not ok and detail:
        for ln in str(detail).splitlines()[:12]:
            print(f"      detail: {ln}")


# --- controls: the detectors work -------------------------------------------
def controls():
    if width("x" * 81) != 81 or width("\x1b[1mab\x1b[0m") != 2 \
            or width("── é") != 4:
        raise Broken("width detector control failed")
    if [ln for ln in lines_of("a\r\n[bale] b\r\n") if ln.startswith("[bale] ")] \
            != ["[bale] b"]:
        raise Broken("[bale] detector control failed")
    if not ITEM_RE.match("    7/7  readme      y/N"):
        raise Broken("item-header detector control failed")
    if not os.path.exists("/dev/ptmx"):
        raise Broken("no /dev/ptmx: the pty driver cannot run")


# --- fixtures -----------------------------------------------------------------
def setup_run(cmd, cwd, env):
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                       timeout=60)
    if r.returncode != 0:
        raise Broken(f"setup {cmd[:3]} exited {r.returncode}: {r.stderr[-400:]}")


class Fixture:
    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="ckpt-loghold-"))
        home = self.root / "home"
        home.mkdir()
        (home / ".gitconfig").write_text(
            "[user]\n\tname = Ckpt\n\temail = ckpt@example.invalid\n"
            "[init]\n\tdefaultBranch = main\n", encoding="utf-8")
        self.install = self.root / "install"
        self.install.mkdir()
        for tree in ("bin", "docs", "schemas", "tools"):
            src = TREE / tree
            if not src.is_dir():
                raise Broken(f"tree under test has no {tree}/")
            shutil.copytree(src, self.install / tree)
        self.env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(home), "LANG": "C.UTF-8", "NO_COLOR": "1",
            "EDITOR": "/bin/true", "VISUAL": "/bin/true",
            "BALE_INSTALL": str(self.root / "bale-install-sandbox"),
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        self.repo = self.root / "project"
        self.repo.mkdir()
        setup_run(["git", "init", "-q", "-b", "main"], self.repo, self.env)
        (self.repo / "hello.txt").write_text("hello\n", encoding="utf-8")
        setup_run(["git", "add", "-A"], self.repo, self.env)
        setup_run(["git", "commit", "-qm", "init"], self.repo, self.env)

    def commit_file(self, rel, text):
        (self.repo / rel).write_text(text, encoding="utf-8")
        setup_run(["git", "add", "-A"], self.repo, self.env)
        setup_run(["git", "commit", "-qm", f"add {rel}"], self.repo, self.env)

    def argv(self, *args):
        return [sys.executable, "-B", str(self.install / "bin" / "bale"), *args]

    def bale_piped(self, *args):
        """A bale step of the code under test: a crash or refusal is a FAIL."""
        try:
            r = subprocess.run(self.argv(*args), cwd=self.repo, env=self.env,
                               stdin=subprocess.DEVNULL, capture_output=True,
                               text=True, timeout=90)
        except subprocess.TimeoutExpired:
            raise UnderTest(f"bale {' '.join(args[:2])} hung")
        return r

    def open_readonly_session(self):
        r = self.bale_piped("pack", "First desk", "--slug", "first",
                            "--read-only", "--no-readme")
        if r.returncode != 0:
            raise UnderTest(f"fixture read-only pack exited {r.returncode}: "
                            f"{r.stderr.strip()[-300:]}")
        return self.open_sessions()[-1]

    def open_sessions(self):
        r = self.bale_piped("status", "--json")
        if r.returncode != 0:
            raise UnderTest(f"bale status --json exited {r.returncode}")
        try:
            return list(json.loads(r.stdout.strip().splitlines()[-1])["sessions"])
        except (ValueError, KeyError, IndexError) as e:
            raise UnderTest(f"bale status --json unreadable: {e}")

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


def run_pty(fx, args, answers, timeout=90):
    """Run bale on an 80x24 pty, typing each answer once bale waits for one.
    Returns (exit_code, transcript, answers_left, snapshots), snapshots
    holding the transcript as it stood when each answer was typed. A
    process still alive
    and silent long after the last answer is a hang (re-ask): UnderTest."""
    try:
        master, slave = pty.openpty()
        fcntl.ioctl(slave, termios.TIOCSWINSZ,
                    struct.pack("HHHH", 24, WIDTH, 0, 0))
    except OSError as e:
        raise Broken(f"pty setup failed: {e}")
    env = dict(fx.env, COLUMNS=str(WIDTH), LINES="24")
    proc = subprocess.Popen(fx.argv(*args), cwd=fx.repo, env=env,
                            stdin=slave, stdout=slave, stderr=slave,
                            close_fds=True, start_new_session=True)
    os.close(slave)
    pending, chunks, snaps = list(answers), [], []
    start = last = time.monotonic()
    answered_at = -1
    try:
        while True:
            now = time.monotonic()
            if now - start > timeout:
                raise UnderTest("timed out")
            r, _, _ = select.select([master], [], [], 0.05)
            if master in r:
                try:
                    c = os.read(master, 4096)
                except OSError:
                    break
                if not c:
                    break
                chunks.append(c)
                last = time.monotonic()
                continue
            if proc.poll() is not None:
                break
            text = b"".join(chunks)
            quiet = time.monotonic() - last
            if pending and len(text) != answered_at and (
                    (quiet > 0.5 and not text.endswith(b"\n")) or quiet > 2.0):
                a = pending.pop(0)
                snaps.append(text.decode(errors="replace"))
                os.write(master, (a if a == EOF_KEY else a + "\n").encode())
                answered_at = len(text)
                last = time.monotonic()
            elif not pending and quiet > 8.0:
                raise UnderTest("still waiting for input after the last "
                                "answer (a re-ask, or a hang)")
        code = proc.wait(timeout=30)
    except UnderTest as e:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass
        proc.wait(timeout=10)
        tail = b"".join(chunks).decode(errors="replace")[-600:]
        raise UnderTest(f"{e}; transcript tail: {tail!r}")
    finally:
        os.close(master)
    return code, b"".join(chunks).decode(errors="replace"), pending, snaps


def wide(lines):
    return [f"{width(ln)} cols: {ln[:60]!r}" for ln in lines if width(ln) > WIDTH]


# --- probes ---------------------------------------------------------------------
def probe_walk():
    fx = Fixture()
    try:
        swept = fx.open_readonly_session()
        # goal, slug (Enter), shape r, exclude, constraint, out-of-scope,
        # the sweep y/N (Enter accepts), README (Enter = no)
        code, out, left, _ = run_pty(fx, ["pack"], [
            "Look at the walk", "", "r", "", "", "", "", ""])
        if code != 0:
            raise UnderTest(f"goal-less pack exited {code}: {out[-400:]!r}")
        lines = lines_of(out)
        try:
            title = next(i for i, ln in enumerate(lines) if ln.strip() == TITLE)
        except StopIteration:
            raise UnderTest("no wizard title line in the transcript")
        heads = [i for i, ln in enumerate(lines) if ITEM_RE.match(ln)]
        readme = [i for i in heads if ITEM_RE.match(lines[i]).group(3) == "readme"]
        if not heads or not readme:
            raise UnderTest("walk item headers not found")
        try:
            prompt = next(i for i in range(readme[-1] + 1, len(lines))
                          if "> " in lines[i])
        except StopIteration:
            raise UnderTest("no README prompt line after the readme header")
        span = lines[heads[0]:prompt + 1]
        noisy = [ln for ln in span if ln.startswith("[bale] ")]
        record("walk-quiet", not noisy, f"{len(noisy)} line(s), first {noisy[:1]!r}")
        bad = wide(lines[title:prompt + 1])
        record("walk-width", not bad, "; ".join(bad[:2]))
        after = lines[prompt + 1:]
        replayed = any(ln.startswith("[bale] ") and "read-only sweep: closed" in ln
                       and swept in ln for ln in after)
        closed = swept not in fx.open_sessions()
        record("walk-replay", replayed and closed,
               f"close line after README: {replayed}; session closed: {closed}")
        bad = wide(lines[:title])
        record("prewalk-width", not bad, "; ".join(bad[:2]))
    finally:
        fx.cleanup()


def probe_sweep(label, answer, expect_closed, check_width=False):
    fx = Fixture()
    try:
        swept = fx.open_readonly_session()
        code, out, left, snaps = run_pty(
            fx, ["pack", "Second desk", "--slug", "second", "--read-only",
                 "--no-readme"], [answer])
        if code != 0:
            record(label, False, f"pack exited {code}")
            return
        if left or not snaps:
            record(label, False, "the sweep never asked")
            return
        closed = swept not in fx.open_sessions()
        # The prompt: what bale printed after its last [bale] line before
        # the answer was typed.
        before = lines_of(snaps[0])
        marks = [i for i, ln in enumerate(before) if ln.startswith("[bale] ")]
        prompt = [ln for ln in before[(marks[-1] + 1 if marks else 0):]
                  if ln.strip()]
        prompt_seen = any(swept in ln for ln in prompt)
        record(label, closed == expect_closed and prompt_seen,
               f"closed={closed} (want {expect_closed}); "
               f"prompt naming the session shown: {prompt_seen}")
        if check_width:
            bad = wide(prompt)
            record("sweep-width", prompt_seen and not bad,
                   f"prompt shown: {prompt_seen}; {'; '.join(bad[:2])}")
    finally:
        fx.cleanup()


def probe_clip_journal():
    fx = Fixture()
    try:
        fx.commit_file("bale.toml", '[probe]\nclipboard_command = """cat"""\n')
        r = fx.bale_piped("pack", "Clip check", "--slug", "clip",
                          "--read-only", "--no-readme")
        if r.returncode != 0:
            record("clip-journal", False, f"pack exited {r.returncode}: "
                   f"{r.stderr.strip()[-200:]}")
            return
        sid_logs = sorted((fx.repo / ".bale" / "logs").glob("*clip*.log"))
        if not sid_logs:
            record("clip-journal", False, "no session log for the pack")
            return
        journal = sid_logs[-1].read_text(encoding="utf-8", errors="replace")
        errors = [ln for ln in journal.splitlines() if "[bale] error:" in ln]
        notice = any(ln.startswith("[bale] clipboard: ") and "NOT copied" in ln
                     for ln in r.stderr.splitlines())
        record("clip-journal", notice and not errors,
               f"not-copied notice on stderr: {notice}; "
               f"error lines journaled: {len(errors)}")
    finally:
        fx.cleanup()


def probe_cli_help():
    path = TREE / "tests" / "test_cli_help.py"
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as e:
        record("cli-help-verb", False, f"cannot parse {path.name}: {e}")
        return
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "COMMANDS" for t in node.targets):
            try:
                found = ("clipboard",) in ast.literal_eval(node.value)
            except ValueError:
                found = False
    record("cli-help-verb", found, "COMMANDS has no ('clipboard',) entry")


def probe_no_rebind():
    hits = []
    for path in sorted((TREE / "bin").glob("*.py")) + [TREE / "bin" / "bale"]:
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError) as e:
            hits.append(f"{path.name}: unparseable ({e})")
            continue
        for node in ast.walk(tree):
            targets = []
            if isinstance(node, ast.Assign):
                targets = node.targets
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                targets = [node.target]
            for t in targets:
                for sub in ast.walk(t):
                    if isinstance(sub, ast.Attribute) and sub.attr in ("log", "fail"):
                        hits.append(f"{path.name}:{node.lineno}")
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id == "setattr" and len(node.args) >= 2
                    and isinstance(node.args[1], ast.Constant)
                    and node.args[1].value in ("log", "fail")):
                hits.append(f"{path.name}:{node.lineno} (setattr)")
    record("no-main-rebind", not hits, ", ".join(hits[:4]))


def guarded(keys, fn, *a):
    """Run a probe; a crash, hang, or refusal of the code under test fails
    every probe key the run had not yet decided."""
    try:
        fn(*a)
    except UnderTest as e:
        decided = {k for k, _ in RESULTS}
        for key in keys:
            if key not in decided:
                record(key, False, str(e)[:900])


def main():
    try:
        controls()
        guarded(["walk-quiet", "walk-width", "walk-replay", "prewalk-width"],
                probe_walk)
        guarded(["sweep-enter", "sweep-width"], probe_sweep, "sweep-enter",
                "", True, True)
        guarded(["sweep-yes"], probe_sweep, "sweep-yes", "yes", True)
        guarded(["sweep-x"], probe_sweep, "sweep-x", "x", False)
        guarded(["sweep-eof"], probe_sweep, "sweep-eof", EOF_KEY, False)
        guarded(["clip-journal"], probe_clip_journal)
        probe_cli_help()
        probe_no_rebind()
    except Broken as e:
        print(f"[ORACLE BROKEN] {e}")
        return 2
    except Exception as e:  # an oracle bug, never a verdict on the work
        print(f"[ORACLE BROKEN] {type(e).__name__}: {e}")
        return 2
    if {k for k, _ in RESULTS} != set(LABELS):
        print("[ORACLE BROKEN] not every probe recorded a verdict")
        return 2
    failed = [key for key, ok in RESULTS if not ok]
    print(f"checkpoint: {len(RESULTS) - len(failed)}/{len(RESULTS)} probes passed")
    return 1 if failed else 0


sys.exit(main())
PY
