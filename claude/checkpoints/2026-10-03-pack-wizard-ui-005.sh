#!/usr/bin/env bash
# Blind checkpoint, v1: session B of the friction-points split, wave 2
# (slug pack-wizard-ui). Authored blind at the read-only planner desk
# 2026-10-03-friction-points-wave2-004 from B's brief, before any
# implementation exists. The worker never reads, ships, or declares
# this file (TARBALL.md section 7).
#
# What it grades: outcomes of the goal-less `bale pack` wizard, never
# how they were reached.
#   B1  the wizard completes on the answer sequence a script types
#       today, with no prompt added, dropped, or reordered;
#   B2  every wizard line fits 80 columns (a line naming an absolute
#       path is exempt; bale's `[bale] ` log lines are graded by B3);
#   B3  no `[bale] ` log line appears between the wizard's first answer
#       and its last question;
#   B4  the answers land in the request exactly as they do today.
# Two scenarios, each on its own fresh fixture: S1 a project pinning a
# {sid} checkpoint base with a .baleignore and every optional answered;
# S2 a bare project answered with Enter wherever Enter is accepted.
#
# How it drives: a real pty at 80x24 with TERM set (so a colored
# layer is exercised; escape codes are stripped before measuring). One
# answer is typed each time the wizard waits for input, so the
# transcript splits into segments delimited by Enter; segment k is
# what the wizard printed after answer k. No locator keys on prompt
# wording.
#
# Exit codes: 0 every probe passed; 1 a probe failed; 2 a control
# failed or a fixture could not be built (the oracle is broken, not
# the work).
set -u
exec python3 - "$PWD" <<'BALE_CHECKPOINT_PY'
import json
import os
import pty
import re
import select
import shutil
import struct
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
WIDTH = 80
ROWS = 24
INSTALL_TREES = ("bin", "docs", "schemas", "tools")
LOG_PREFIX = "[bale] "
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]")
# The absolute paths a scenario can make bale print all live under its
# scratch root; a line naming one of them is the contract's one width
# exemption. Set per run by main(); the control sets its own.
ABS_ROOTS = []

# Waiting-for-input detection: the child is quiet and its last output
# does not end a line (a prompt), or it has been quiet long enough that
# it can only be waiting.
PROMPT_IDLE = 0.25
ANY_IDLE = 2.5
EXTRA_PROMPT_IDLE = 6.0
RUN_TIMEOUT = 120.0


class OracleBroken(Exception):
    """A control failed or a fixture could not be built: exit 2."""


def strip_ansi(text):
    return ANSI_RE.sub("", text)


def lines_of(segment):
    text = strip_ansi(segment).replace("\r\n", "\n").replace("\r", "\n")
    return text.split("\n")


def width_offenders(segments):
    bad = []
    for k, seg in enumerate(segments):
        for line in lines_of(seg):
            if line.startswith(LOG_PREFIX):
                continue
            if len(line) > WIDTH and not any(r in line for r in ABS_ROOTS):
                bad.append((k, len(line), line))
    return bad


def log_lines(segments):
    out = []
    for k, seg in enumerate(segments):
        for line in lines_of(seg):
            if line.startswith(LOG_PREFIX):
                out.append((k, line))
    return out


def looks_like_prompt(buf):
    tail = strip_ansi(buf.decode("utf-8", errors="replace"))
    return bool(tail) and not tail.endswith("\n")


def drive(argv, cwd, env, answers):
    """Run argv on a pty at 80x24, typing one answer each time it waits.

    Returns a dict: rc, segments (len(answers)+1 strings when every
    answer was consumed), unused (answers never typed), extra_prompt
    (it waited for input after the last answer), timed_out.
    """
    import fcntl
    import termios
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, WIDTH, 0, 0))
    proc = subprocess.Popen(argv, cwd=str(cwd), env=env, stdin=slave,
                            stdout=slave, stderr=slave, close_fds=True,
                            start_new_session=True)
    os.close(slave)
    pending = list(answers)
    segments = []
    buf = b""
    last = time.monotonic()
    deadline = last + RUN_TIMEOUT
    extra_prompt = False
    timed_out = False
    while True:
        readable, _, _ = select.select([master], [], [], 0.05)
        if master in readable:
            try:
                chunk = os.read(master, 65536)
            except OSError:
                chunk = b""
            if not chunk:
                break
            buf += chunk
            last = time.monotonic()
            continue
        if proc.poll() is not None:
            # Exited; drain whatever is still buffered on the master.
            try:
                while True:
                    r, _, _ = select.select([master], [], [], 0.05)
                    if master not in r:
                        break
                    chunk = os.read(master, 65536)
                    if not chunk:
                        break
                    buf += chunk
            except OSError:
                pass
            break
        now = time.monotonic()
        idle = now - last
        if now > deadline:
            timed_out = True
            proc.kill()
            break
        waiting = (idle >= PROMPT_IDLE and looks_like_prompt(buf)) or idle >= ANY_IDLE
        if pending and waiting:
            segments.append(buf.decode("utf-8", errors="replace"))
            buf = b""
            os.write(master, (pending.pop(0) + "\n").encode("utf-8"))
            last = time.monotonic()
        elif not pending and idle >= EXTRA_PROMPT_IDLE and looks_like_prompt(buf):
            extra_prompt = True
            proc.kill()
            break
    segments.append(buf.decode("utf-8", errors="replace"))
    try:
        rc = proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = proc.wait()
    os.close(master)
    return {"rc": rc, "segments": segments, "unused": pending,
            "extra_prompt": extra_prompt, "timed_out": timed_out}


# ---------------------------------------------------------------------------
# Controls: prove the driver and the detectors before trusting a verdict.
# ---------------------------------------------------------------------------

CONTROL_CHILD = r'''
import os, sys
cols, rows = os.get_terminal_size(0)
print(f"size {cols}x{rows}")
a = input("first > ")
print("x" * 81)
print("\x1b[1m" + "y" * 80 + "\x1b[0m")
print("see " + sys.argv[1] + "/" + "z" * 90)
print("[bale] " + "w" * 120)
b = input("second [y/N] ")
print(f"got {a}|{b}")
'''


def run_controls(scratch):
    child = scratch / "control_child.py"
    child.write_text(CONTROL_CHILD, encoding="utf-8")
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8",
           "TERM": "xterm", "HOME": str(scratch)}
    res = drive([sys.executable, str(child), str(scratch)], scratch, env,
                ["alpha", "beta"])
    segs = res["segments"]
    problems = []
    if res["rc"] != 0 or res["unused"] or res["extra_prompt"] or res["timed_out"]:
        problems.append(f"driver run: {res!r}")
    if len(segs) != 3:
        problems.append(f"expected 3 segments, got {len(segs)}")
    else:
        if "size 80x24" not in segs[0] or not strip_ansi(segs[0]).endswith("first > "):
            problems.append(f"segment 0 wrong: {segs[0]!r}")
        if "second [y/N] " not in segs[1] or "alpha" not in segs[1]:
            problems.append(f"segment 1 wrong: {segs[1]!r}")
        if "got alpha|beta" not in segs[2]:
            problems.append(f"segment 2 wrong: {segs[2]!r}")
        bad = width_offenders(segs)
        if [n for _, n, _ in bad] != [81]:
            problems.append(f"width detector: {bad!r}")
        logs = log_lines(segs)
        if len(logs) != 1 or logs[0][0] != 1:
            problems.append(f"log detector: {logs!r}")
    # A child that asks one question more than it is answered.
    res2 = drive([sys.executable, str(child), str(scratch)], scratch, env, ["alpha"])
    if not res2["extra_prompt"]:
        problems.append(f"extra-prompt detector did not fire: {res2!r}")
    if problems:
        raise OracleBroken("control failed: " + "; ".join(problems))


# ---------------------------------------------------------------------------
# Fixtures: one fresh home, install, and repo per scenario.
# ---------------------------------------------------------------------------

def checked(cmd, cwd, env):
    r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise OracleBroken(f"fixture command failed: {cmd}: {r.stdout}{r.stderr}")
    return r


def base_env(home):
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home),
            "LANG": "C.UTF-8", "TERM": "xterm", "EDITOR": "/bin/true",
            "VISUAL": "/bin/true", "BALE_INSTALL": str(home.parent / "bale-install-sandbox")}


def make_fixture(root):
    home = root / "home"
    home.mkdir(parents=True)
    (home / ".gitconfig").write_text(
        "[user]\n\tname = Fixture Packer\n\temail = fixture@example.invalid\n"
        "[init]\n\tdefaultBranch = main\n", encoding="utf-8")
    install = root / "install"
    install.mkdir()
    for tree in INSTALL_TREES:
        if not (TREE / tree).is_dir():
            raise OracleBroken(f"tree under test has no {tree}/")
        shutil.copytree(TREE / tree, install / tree)
    repo = root / "project"
    repo.mkdir()
    env = base_env(home)
    checked(["git", "init", "-q", "-b", "main"], repo, env)
    for rel, body in (("hello.txt", "hello\n"), ("src/a.txt", "a\n"),
                      ("docs/notes.txt", "notes\n"), ("tmp/junk.txt", "junk\n")):
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(body, encoding="utf-8")
    return home, install, repo, env


def commit_all(repo, env, msg):
    checked(["git", "add", "-A"], repo, env)
    checked(["git", "commit", "-q", "-m", msg], repo, env)


def read_request(repo):
    outbox = repo / ".bale" / "outbox"
    tarballs = sorted(outbox.glob("request-*.tar.gz")) if outbox.is_dir() else []
    if len(tarballs) != 1:
        return None, f"expected one request tarball in .bale/outbox, found {len(tarballs)}"
    with tarfile.open(tarballs[0], "r:gz") as tf:
        member = next((m for m in tf.getmembers()
                       if m.name.endswith("/manifest.json") and m.name.count("/") == 1), None)
        if member is None:
            return None, "request tarball has no top-level manifest.json"
        return json.load(tf.extractfile(member)), ""


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------

RESULTS = []


def verdict(ok, label, detail=""):
    RESULTS.append(ok)
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if detail and not ok:
        for ln in str(detail).splitlines()[:12]:
            print(f"    {ln}")


def grade_walk(tag, res, answers):
    segs = res["segments"]
    completed = (res["rc"] == 0 and not res["unused"] and not res["extra_prompt"]
                 and not res["timed_out"])
    detail = (f"rc={res['rc']} unused={res['unused']!r} extra_prompt={res['extra_prompt']} "
              f"timed_out={res['timed_out']}\n--- last segment ---\n"
              + strip_ansi(segs[-1])[-1500:])
    verdict(completed, f"B1.{tag} the wizard walk completes on today's answer sequence "
                       f"({len(answers)} answers) and the pack succeeds", detail)
    wizard = segs[:-1] if not res["unused"] else segs
    bad = width_offenders(wizard)
    verdict(not bad, f"B2.{tag} every line the wizard prints fits 80 columns",
            "\n".join(f"segment {k}: {n} cols: {ln[:120]}" for k, n, ln in bad))
    between = wizard[1:]
    logs = log_lines(between)
    verdict(not logs, f"B3.{tag} no [bale] log line appears between the first answer "
                      f"and the last question",
            "\n".join(f"segment {k + 1}: {ln[:120]}" for k, ln in logs))
    return completed


def scenario_s1(work):
    home, install, repo, env = make_fixture(work / "s1")
    downloads = work / "s1" / "inbound"
    downloads.mkdir()
    checkpoint_bytes = b"#!/usr/bin/env bash\n# fixture oracle\nexit 1\n"
    (downloads / "fxw-checkpoint-v1.sh").write_bytes(checkpoint_bytes)
    (repo / "bale.toml").write_text(
        "[apply]\n"
        f"search_paths = [{json.dumps(str(downloads))}]\n\n"
        "[identity]\npacker = \"fixture\"\n\n"
        "[validation]\nbase = \"claude/checkpoints/{sid}.sh\"\n", encoding="utf-8")
    (repo / ".baleignore").write_text("data/\n*.log\n", encoding="utf-8")
    commit_all(repo, env, "fixture s1")
    goal = "Scoped fixture goal for the pack wizard"
    answers = [goal, "fxw-scoped", "d", "src", "fxw-checkpoint-v1.sh",
               "tmp/", "", "keep the fixture small", "", "later work", "", "n"]
    res = drive([sys.executable, str(install / "bin" / "bale"), "pack"], repo, env, answers)
    completed = grade_walk("S1", res, answers)
    problems = []
    manifest, why = read_request(repo) if completed else (None, "walk did not complete")
    if manifest is None:
        problems.append(why)
    else:
        sid = manifest.get("session_id", "")
        expect = {
            "goal": goal,
            "resolved_scope": ["src"],
            "constraints": ["keep the fixture small"],
            "out_of_scope": ["later work"],
            "readme": None,
        }
        for key, want in expect.items():
            if manifest.get(key) != want:
                problems.append(f"{key}: {manifest.get(key)!r} != {want!r}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-fxw-scoped-\d{3}", sid):
            problems.append(f"session_id {sid!r} does not carry the typed slug")
        if (manifest.get("provenance") or {}).get("work_class") != "doc":
            problems.append(f"work_class {(manifest.get('provenance') or {}).get('work_class')!r} != 'doc'")
        included = manifest.get("context_included") or []
        if "context/src/a.txt" not in included:
            problems.append("context/src/a.txt not shipped")
        if any(p.startswith("context/tmp/") for p in included):
            problems.append("the session exclude tmp/ was not honored")
        shown = subprocess.run(["git", "show", f"HEAD:claude/checkpoints/{sid}.sh"],
                               cwd=str(repo), env=env, capture_output=True)
        if shown.returncode != 0 or shown.stdout != checkpoint_bytes:
            problems.append("the delivered checkpoint is not committed at the "
                            "session's checkpoint path with its bytes")
    verdict(not problems, "B4.S1 the answers land in the request unchanged (goal, slug, "
                          "work class, forecast, checkpoint, excludes, constraints, "
                          "out of scope, no README)", "\n".join(problems))


def scenario_s2(work):
    home, install, repo, env = make_fixture(work / "s2")
    commit_all(repo, env, "fixture s2")
    goal = "Bare fixture goal for the pack wizard"
    answers = [goal, "fxw-bare", "", "", "", "", "", ""]
    res = drive([sys.executable, str(install / "bin" / "bale"), "pack"], repo, env, answers)
    completed = grade_walk("S2", res, answers)
    problems = []
    manifest, why = read_request(repo) if completed else (None, "walk did not complete")
    if manifest is None:
        problems.append(why)
    else:
        sid = manifest.get("session_id", "")
        expect = {"goal": goal, "constraints": [], "out_of_scope": [], "readme": None}
        for key, want in expect.items():
            if manifest.get(key) != want:
                problems.append(f"{key}: {manifest.get(key)!r} != {want!r}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}-fxw-bare-\d{3}", sid):
            problems.append(f"session_id {sid!r} does not carry the typed slug")
        if (manifest.get("provenance") or {}).get("work_class") != "mixed":
            problems.append("Enter at the session-shape question no longer means mixed")
        scope = manifest.get("resolved_scope")
        included = manifest.get("context_included") or []
        if scope in ([], None):
            problems.append(f"Enter at the forecast question produced forecast {scope!r}")
        for rel in ("context/hello.txt", "context/src/a.txt", "context/tmp/junk.txt"):
            if rel not in included:
                problems.append(f"{rel} not shipped (Enter at excludes is no longer empty)")
    verdict(not problems, "B4.S2 Enter keeps today's defaults (mixed work, the include-set "
                          "forecast, no excludes, constraints, out of scope, or README)",
            "\n".join(problems))


def main():
    work = Path(tempfile.mkdtemp(prefix="cp-pack-wizard-ui-"))
    ABS_ROOTS[:] = sorted({str(work), str(work.resolve())})
    try:
        try:
            run_controls(work)
            print("[control] pty driver, segmenting, width and log detectors: ok")
            scenario_s1(work)
            scenario_s2(work)
        except OracleBroken as e:
            print(f"checkpoint error (oracle, not the work): {e}")
            return 2
    finally:
        shutil.rmtree(work, ignore_errors=True)
    failed = RESULTS.count(False)
    print(f"checkpoint: {len(RESULTS) - failed}/{len(RESULTS)} probes passed")
    return 1 if failed else 0


sys.exit(main())
BALE_CHECKPOINT_PY
