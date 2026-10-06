#!/usr/bin/env bash
# Blind checkpoint — session choice-prompt-convergence (friction-points
# cleanup, queued item 3). Authored at desk
# 2026-10-04-friction-points-cleanup-002 from the request, before the work
# exists. Outcome probes only; every probe drives the tree under test (the
# staging copy in cwd) on an 80x24 pty from a fresh fixture under $TMPDIR.
#
# Exit codes (TARBALL.md §7.5): 0 every probe passed; 1 a probe failed,
# including a crash, hang, or nonzero exit of the code under test inside a
# fixture step; 2 the oracle's own machinery broke (a failed control, git
# or file setup, no pty).
#
# Probes (goal-less `bale pack` unless named otherwise):
#   shape-code / shape-enter / shape-read-only / shape-unknown
#                       the shape question's answers keep their meaning:
#                       c -> code, Enter -> mixed, r -> read-only, an unknown
#                       answer re-asks (read off the request manifest)
#   shape-help-gesture  the shape question's prompt ends in the layer's
#                       "· ? help > "
#   ckpt-pick / ckpt-out-of-range / ckpt-number-file
#                       the checkpoint picker (two .sh candidates in cwd):
#                       1 commits the newest; 9 re-asks, then 2 commits the
#                       older; 7, out of range but a file in cwd, is that path
#   baleignore-filters  `bale config init` (Enter through): the .baleignore
#                       step suggests *.parquet but not a file under a kept
#                       .baleignore pattern, a secret-pattern file, or a file
#                       under the checkpoint base's directory
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



# --- fixtures -----------------------------------------------------------------
def setup_run(cmd, cwd, env):
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                       timeout=60)
    if r.returncode != 0:
        raise Broken(f"setup {cmd[:3]} exited {r.returncode}: {r.stderr[-400:]}")


class Fixture:
    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="ckpt-choice-"))
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



LABELS = {
    "shape-code": "shape-code: c at the shape question stamps work class code",
    "shape-enter": "shape-enter: Enter at the shape question stamps mixed",
    "shape-read-only": "shape-read-only: r at the shape question packs a "
                       "read-only session",
    "shape-unknown": "shape-unknown: an unknown shape answer re-asks, and the "
                     "next answer counts",
    "shape-help-gesture": "shape-help-gesture: the shape question's prompt "
                          "offers the layer's ? help",
    "ckpt-pick": "ckpt-pick: a candidate's number commits that candidate as "
                 "the session's checkpoint",
    "ckpt-out-of-range": "ckpt-out-of-range: an out-of-range number re-asks, "
                         "and the next pick counts",
    "ckpt-number-file": "ckpt-number-file: an out-of-range number naming a "
                        "file in cwd is taken as that path",
    "baleignore-filters": "baleignore-filters: .baleignore suggestions leave "
                          "out what pack's filters already drop",
}


def record(key, ok, detail=""):
    """One verdict line, label only (the HOLD relay carries labels alone);
    the detail goes on indented lines below it for the session log."""
    RESULTS.append((key, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {LABELS[key]}")
    if not ok and detail:
        for ln in str(detail).splitlines()[:12]:
            print(f"      detail: {ln}")


def controls():
    if width("x" * 81) != 81 or width("\x1b[1mab\x1b[0m") != 2:
        raise Broken("width detector control failed")
    if not os.path.exists("/dev/ptmx"):
        raise Broken("no /dev/ptmx: the pty driver cannot run")
    if not shutil.which("git"):
        raise Broken("git is not on PATH")
    if region_between("a\n── .baleignore  x ──\nb\n── Review: .baleignore ──\nc",
                      ) != ["b"]:
        raise Broken(".baleignore region locator control failed")


def region_between(text, start="── .baleignore ", end="── Review: .baleignore"):
    """Lines strictly between the .baleignore step's heading and its review
    heading (both drawn by the layer's heading/rule grammar)."""
    lines = lines_of(text)
    try:
        a = max(i for i, ln in enumerate(lines) if ln.startswith(start))
        b = next(i for i in range(a + 1, len(lines)) if lines[i].startswith(end))
    except (ValueError, StopIteration):
        return None
    return lines[a + 1:b]


def request_manifest(fx):
    """The manifest of the one request this fixture's pack wrote."""
    outbox = sorted((fx.repo / ".bale" / "outbox").glob("request-*.tar.gz"))
    if len(outbox) != 1:
        raise UnderTest(f"expected one request tarball, found {len(outbox)}")
    import tarfile
    try:
        with tarfile.open(outbox[0]) as tf:
            member = next(m for m in tf.getmembers()
                          if m.name.endswith("/manifest.json")
                          and m.name.count("/") == 1)
            return json.loads(tf.extractfile(member).read().decode("utf-8"))
    except (OSError, StopIteration, ValueError, tarfile.TarError) as e:
        raise UnderTest(f"request tarball unreadable: {e}")


def pack_walk(fx, answers):
    code, out, left, snaps = run_pty(fx, ["pack"], answers + [""] * 8)
    return code, out, snaps


def p_shape(key, answers, check):
    fx = Fixture()
    try:
        code, out, snaps = pack_walk(fx, answers)
        if code != 0:
            raise UnderTest(f"goal-less pack exited {code}: {out[-300:]!r}")
        m = request_manifest(fx)
        ok, detail = check(m)
        record(key, ok, detail)
        if key == "shape-code":
            shape_prompt = None
            for s in snaps:
                last = lines_of(s)[-1] if s else ""
                if "mixed" in last and last.rstrip().endswith(">"):
                    shape_prompt = last
                    break
            record("shape-help-gesture",
                   shape_prompt is not None
                   and shape_prompt.endswith("· ? help > "),
                   f"shape prompt line: {shape_prompt!r}")
    finally:
        fx.cleanup()


def work_class_is(want):
    def check(m):
        got = (m.get("provenance") or {}).get("work_class")
        return got == want, f"work_class {got!r}, want {want!r}"
    return check


def read_only(m):
    return m.get("resolved_scope") == [], f"resolved_scope {m.get('resolved_scope')!r}"


CKPT_BASE = '[validation]\nbase = "claude/checkpoints/{sid}.sh"\n'


def checkpoint_fixture():
    fx = Fixture()
    fx.commit_file("bale.toml", CKPT_BASE)
    (fx.repo / ".gitignore").write_text("/*.sh\n/7\n.bale/\n", encoding="utf-8")
    setup_run(["git", "add", "-A"], fx.repo, fx.env)
    setup_run(["git", "commit", "-qm", "ignore"], fx.repo, fx.env)
    older = fx.repo / "older-ckpt.sh"
    newer = fx.repo / "newer-ckpt.sh"
    older.write_text("#!/usr/bin/env bash\necho older\nexit 1\n", encoding="utf-8")
    newer.write_text("#!/usr/bin/env bash\necho newer\nexit 1\n", encoding="utf-8")
    now = time.time()
    os.utime(older, (now - 3600, now - 3600))
    os.utime(newer, (now - 60, now - 60))
    return fx, older, newer


def committed_checkpoint(fx):
    m = request_manifest(fx)
    sid = m.get("session_id")
    r = subprocess.run(["git", "show", f"HEAD:claude/checkpoints/{sid}.sh"],
                       cwd=fx.repo, env=fx.env, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def p_ckpt(key, ckpt_answers, want_file):
    fx, older, newer = checkpoint_fixture()
    try:
        if want_file == "seven":
            seven = fx.repo / "7"
            seven.write_text("#!/usr/bin/env bash\necho seven\nexit 1\n",
                             encoding="utf-8")
        answers = ["Checkpoint probe goal", "", "c", ""] + ckpt_answers
        code, out, snaps = pack_walk(fx, answers)
        if code != 0:
            raise UnderTest(f"goal-less pack exited {code}: {out[-300:]!r}")
        got = committed_checkpoint(fx)
        want = {"newer": newer, "older": older,
                "seven": fx.repo / "7"}[want_file].read_text(encoding="utf-8")
        record(key, got == want, f"committed {got!r}, want {want!r}")
    finally:
        fx.cleanup()


def p_baleignore():
    fx = Fixture()
    try:
        for rel, size in (("assets/big.bin", 2_200_000),
                          ("data.parquet", 2_100_000),
                          ("keys.pem", 2_300_000),
                          ("claude/checkpoints/old.sh", 2_400_000)):
            p = fx.repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            with open(p, "wb") as f:
                f.write(os.urandom(size))
        (fx.repo / ".baleignore").write_text("assets/\n", encoding="utf-8")
        fx.commit_file("bale.toml", CKPT_BASE)
        code, out, left, snaps = run_pty(fx, ["config", "init"], [""] * 80)
        if code != 0:
            raise UnderTest(f"bale config init exited {code}: {out[-300:]!r}")
        region = region_between(out)
        if region is None:
            raise UnderTest("no .baleignore step in the config init transcript")
        text = "\n".join(region)
        kept = "*.parquet" in text
        leaked = [n for n in ("big.bin", "keys.pem", "old.sh") if n in text]
        record("baleignore-filters", kept and not leaked,
               f"*.parquet suggested: {kept}; suggested though pack drops "
               f"them: {leaked}")
    finally:
        fx.cleanup()


def guarded(keys, fn, *a):
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
        guarded(["shape-code", "shape-help-gesture"], p_shape, "shape-code",
                ["Shape probe goal", "", "c"], work_class_is("code"))
        guarded(["shape-enter"], p_shape, "shape-enter",
                ["Shape probe goal", "", ""], work_class_is("mixed"))
        guarded(["shape-read-only"], p_shape, "shape-read-only",
                ["Shape probe goal", "", "r"], read_only)
        guarded(["shape-unknown"], p_shape, "shape-unknown",
                ["Shape probe goal", "", "q", "d"], work_class_is("doc"))
        guarded(["ckpt-pick"], p_ckpt, "ckpt-pick", ["1"], "newer")
        guarded(["ckpt-out-of-range"], p_ckpt, "ckpt-out-of-range",
                ["9", "2"], "older")
        guarded(["ckpt-number-file"], p_ckpt, "ckpt-number-file",
                ["7"], "seven")
        guarded(["baleignore-filters"], p_baleignore)
    except Broken as e:
        print(f"[ORACLE BROKEN] {e}")
        return 2
    except Exception as e:  # an oracle bug, never a verdict on the work
        print(f"[ORACLE BROKEN] {type(e).__name__}: {e}")
        return 2
    if {k for k, _ in RESULTS} != set(LABELS):
        print("[ORACLE BROKEN] not every probe recorded a verdict")
        return 2
    failed = [k for k, ok in RESULTS if not ok]
    print(f"checkpoint: {len(RESULTS) - len(failed)}/{len(RESULTS)} probes passed")
    return 1 if failed else 0


sys.exit(main())
PY
