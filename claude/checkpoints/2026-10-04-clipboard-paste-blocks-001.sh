#!/usr/bin/env bash
# Blind checkpoint, v1: session D of the friction-points split, wave 3
# (slug clipboard-paste-blocks). Authored blind at the read-only planner
# desk 2026-10-03-friction-points-wave2-004 from D's brief, against the
# tree as landed after B (2026-10-03-pack-wizard-ui-005) and C
# (2026-10-03-wizard-defaults-006), before any implementation exists. The
# worker never reads, ships, or declares this file (TARBALL.md section 7).
#
# What it grades: outcomes, never how they were reached. Each scenario
# runs on its own fresh fixture (home, install, repo), with a stand-in
# clipboard command that writes what it receives to a file.
#   D1  bale pack (on a terminal) puts the session opener, the lines
#       between its scissor lines, on the clipboard;
#   D2  bale relay puts the exchange block it emits on the clipboard;
#   D3  a passing bale apply puts its APPLIED relay block on the clipboard;
#   D4  a held bale apply puts the block its card says to send first on
#       the clipboard (a worker-only HOLD: the worker block);
#   D5  a crafter-emitted probe, from a request that ships no bale.toml,
#       copies its PROBE block through the installed bale on PATH;
#   D6  bale status names the effective clipboard command and its layer,
#       and says so when a project suppresses it;
#   D7  a clipboard command that fails never fails the command, and a
#       line says the copy failed;
#   guards (pass today, must keep passing): with no command configured
#   nothing is copied even when common clipboard programs are on PATH;
#   an unreadable clipboard_command spelling never fails a pack; pack
#   --json and bale relay keep stdout to exactly their payload; a probe
#   with no bale on PATH still exits 0 with its block on stdout; and the
#   printed blocks themselves are unchanged in shape.
#
# Exit codes: 0 every probe passed; 1 a probe failed; 2 a control failed
# or a fixture could not be built (the oracle is broken, not the work).
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
import hashlib
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
WIDTH = 80
ROWS = 24
INSTALL_TREES = ("bin", "docs", "schemas", "tools")
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]")
OPENER_BEGIN = "--8<-- session opener (copy everything between the scissor lines) --8<--"
OPENER_END = "--8<-- end session opener --8<--"
EXCHANGE_BEGIN = "BALE EXCHANGE BEGIN"
EXCHANGE_END = "BALE EXCHANGE END"

PROMPT_IDLE = 0.25
ANY_IDLE = 2.5
RUN_TIMEOUT = 180.0
MAX_ANSWERS = 20


WORK_ROOTS = []


def mentions(line, word):
    """`word` in `line`, case-insensitively, outside any scratch path."""
    for root in WORK_ROOTS:
        line = re.sub(re.escape(root) + r"\S*", "", line)
    return word in line.lower()


class OracleBroken(Exception):
    """A control failed or a fixture could not be built: exit 2."""


class WorkFailed(Exception):
    """A fixture step that runs the tree under test (bale, the crafter)
    failed: that is the work's failure, graded as FAIL, never exit 2."""


def strip_ansi(text):
    return ANSI_RE.sub("", text)


def norm_lines(text):
    lines = [ln.rstrip() for ln in strip_ansi(text).replace("\r\n", "\n")
             .replace("\r", "\n").split("\n")]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return lines


def looks_like_prompt(buf):
    tail = strip_ansi(buf.decode("utf-8", errors="replace"))
    return bool(tail) and not tail.endswith("\n")


def drive(argv, cwd, env, answer=""):
    """Run argv on a pty at 80x24, typing `answer` (Enter by default) each
    time it waits for input. Returns rc, text, answers, timed_out."""
    import fcntl
    import termios
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, WIDTH, 0, 0))
    proc = subprocess.Popen(argv, cwd=str(cwd), env=env, stdin=slave,
                            stdout=slave, stderr=slave, close_fds=True,
                            start_new_session=True)
    os.close(slave)
    buf, seen = b"", b""
    answers = 0
    last = time.monotonic()
    deadline = last + RUN_TIMEOUT
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
            seen += chunk
            last = time.monotonic()
            continue
        if proc.poll() is not None:
            try:
                while True:
                    r, _, _ = select.select([master], [], [], 0.05)
                    if master not in r:
                        break
                    chunk = os.read(master, 65536)
                    if not chunk:
                        break
                    seen += chunk
            except OSError:
                pass
            break
        now = time.monotonic()
        if now > deadline or answers >= MAX_ANSWERS:
            timed_out = True
            proc.kill()
            break
        idle = now - last
        if (idle >= PROMPT_IDLE and looks_like_prompt(buf)) or idle >= ANY_IDLE:
            buf = b""
            answers += 1
            os.write(master, (answer + "\n").encode("utf-8"))
            last = time.monotonic()
    try:
        rc = proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = proc.wait()
    os.close(master)
    return {"rc": rc, "text": seen.decode("utf-8", errors="replace"),
            "answers": answers, "timed_out": timed_out}


def between(lines, begin_pred, end_pred, inclusive):
    """The first span of `lines` from a line matching begin_pred to the
    next matching end_pred; None when either is missing."""
    for i, ln in enumerate(lines):
        if begin_pred(ln):
            for j in range(i + 1, len(lines)):
                if end_pred(lines[j]):
                    return lines[i:j + 1] if inclusive else lines[i + 1:j]
            return None
    return None


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

CONTROL_CHILD = r'''
import os
cols, rows = os.get_terminal_size(0)
print(f"size {cols}x{rows}")
print("--8<-- session opener (copy everything between the scissor lines) --8<--")
print("line one  ")
print("line two")
print("--8<-- end session opener --8<--")
a = input("  > ")
print(f"got [{a}]")
'''


def run_controls(scratch):
    child = scratch / "control_child.py"
    child.write_text(CONTROL_CHILD, encoding="utf-8")
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8",
           "TERM": "xterm", "HOME": str(scratch)}
    res = drive([sys.executable, str(child)], scratch, env)
    problems = []
    if res["rc"] != 0 or res["timed_out"] or res["answers"] != 1:
        problems.append(f"driver: {res!r}")
    lines = norm_lines(res["text"])
    span = between(lines, lambda l: l == OPENER_BEGIN, lambda l: l == OPENER_END, False)
    if span != ["line one", "line two"] or "size 80x24" not in lines or "got []" not in lines:
        problems.append(f"span/locator: {span!r} {lines!r}")
    if mentions(f"path {scratch}/clipboard/x", "clipboard") or not mentions(
            f"copied to the clipboard ({scratch}/a)", "clipboard"):
        problems.append("mentions() does not ignore scratch paths")
    clip = make_clip(scratch / "ctl", "ok")
    r = subprocess.run([str(clip["cmd"])], input="a\nb\n", text=True)
    if r.returncode != 0 or clip["file"].read_text() != "a\nb\n":
        problems.append("stand-in clipboard command does not capture its input")
    if problems:
        raise OracleBroken("control failed: " + "; ".join(problems))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def checked(cmd, cwd, env, **kw):
    r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise OracleBroken(f"fixture command failed: {cmd}: {r.stdout}{r.stderr}")
    return r


def make_clip(root, kind):
    """A stand-in clipboard command: 'ok' writes stdin to a file, 'fail'
    exits 1. The command is an absolute path with no quotes or
    backslashes, so every reader of the key can see it."""
    root.mkdir(parents=True, exist_ok=True)
    out = root / "clipboard.txt"
    cmd = root / ("fxclip" if kind == "ok" else "fxclip-broken")
    body = (f"#!/bin/sh\ncat > '{out}'\n" if kind == "ok"
            else "#!/bin/sh\ncat > /dev/null\nexit 1\n")
    cmd.write_text(body, encoding="utf-8")
    cmd.chmod(0o755)
    return {"cmd": cmd, "file": out}


def make_fixture(root, *, global_clip=None, project_toml="", extra_files=None):
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
    if global_clip is not None:
        (install / "user").mkdir()
        (install / "user" / "bale.toml").write_text(
            f'[probe]\nclipboard_command = "{global_clip}"\n', encoding="utf-8")
    pathbin = root / "pathbin"
    pathbin.mkdir()
    (pathbin / "bale").symlink_to(install / "bin" / "bale")
    env = {"PATH": f"{pathbin}:{os.environ.get('PATH', '/usr/bin:/bin')}",
           "HOME": str(home), "LANG": "C.UTF-8", "TERM": "xterm",
           "EDITOR": "/bin/true", "VISUAL": "/bin/true",
           "BALE_INSTALL": str(root / "bale-install-sandbox")}
    repo = root / "project"
    repo.mkdir()
    checked(["git", "init", "-q", "-b", "main"], repo, env)
    files = {"hello.txt": "hello\n", "src/a.txt": "a\n",
             "bale.toml": "[sandbox]\nenabled = false\n" + project_toml}
    files.update(extra_files or {})
    for rel, body in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(body, encoding="utf-8")
    checked(["git", "add", "-A"], repo, env)
    checked(["git", "commit", "-q", "-m", "fixture"], repo, env)
    return {"home": home, "install": install, "repo": repo, "env": env,
            "bale": [sys.executable, str(install / "bin" / "bale")]}


def open_sids(repo):
    root = repo / ".bale" / "sessions"
    if not root.is_dir():
        return []
    return sorted(d.name for d in root.iterdir() if (d / "open").is_file())


def pack_piped(fx, slug, *extra):
    r = subprocess.run(fx["bale"] + ["pack", f"Fixture goal for {slug}", "--slug", slug,
                                     "--include", "hello.txt", "src", "--write",
                                     "hello.txt", "--no-readme", *extra],
                       cwd=str(fx["repo"]), env=fx["env"], stdin=subprocess.DEVNULL,
                       capture_output=True, text=True)
    sids = open_sids(fx["repo"])
    if r.returncode != 0 or len(sids) != 1:
        raise WorkFailed(f"bale pack (fixture step) failed: rc={r.returncode} "
                         f"sids={sids}\n{r.stderr[-1500:]}")
    return sids[0], r


def response_tarball(fx, sid, *, passing):
    rdir = fx["repo"].parent / "resp" / f"response-{sid[-3:]}"
    (rdir / "files").mkdir(parents=True)
    data = b"hello from the fixture response\n"
    (rdir / "files" / "hello.txt").write_bytes(data)
    manifest = {
        "session_id": sid, "responds_to": sid, "corrects": None,
        "response_kind": "normal", "summary": "fixture change to hello.txt",
        "changes": [{"path": "hello.txt", "action": "modified",
                     "reason": "fixture", "size_bytes": len(data),
                     "sha256": hashlib.sha256(data).hexdigest()}],
        "deferred": [], "validation_will_run": ["fixture check"], "claims": {},
    }
    (rdir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                        encoding="utf-8")
    (rdir / "apply.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (rdir / "validation.sh").write_text(
        "#!/usr/bin/env bash\n"
        + ('echo "[PASS] fixture check"\nexit 0\n' if passing
           else 'echo "[FAIL] fixture check"\nexit 1\n'), encoding="utf-8")
    tarball = rdir.parent / f"{rdir.name}.tar.gz"
    with tarfile.open(tarball, "w:gz") as tf:
        tf.add(str(rdir), arcname=rdir.name)
    return tarball


def clarification_manifest(sid):
    return {
        "session_id": sid, "responds_to": sid, "corrects": None,
        "response_kind": "clarification",
        "summary": "blocked on an intent question (fixture)",
        "changes": [], "deferred": [], "validation_will_run": [], "claims": {},
        "questions": [{"question": "fixture question?", "context": "fixture context",
                       "default_assumption": "fixture assumption",
                       "why_blocked": "fixture blocker", "options": ["yes", "no"],
                       "recommendation": "yes"}],
    }


def clipboard(clip):
    return norm_lines(clip["file"].read_text(encoding="utf-8")) if clip["file"].is_file() else None


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------

RESULTS = []


def verdict(ok, label, detail=""):
    RESULTS.append(bool(ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if detail and not ok:
        for ln in str(detail).splitlines()[:14]:
            print(f"    {ln}")


def tail(text, n=1200):
    return strip_ansi(text)[-n:]


def scenario_pack(work):
    root = work / "d1"
    clip = make_clip(root / "clip", "ok")
    fx = make_fixture(root, global_clip=clip["cmd"])
    res = drive(fx["bale"] + ["pack", "Fixture goal for the opener", "--slug", "fx-opener",
                              "--include", "hello.txt", "src", "--write", "hello.txt",
                              "--no-readme"], fx["repo"], fx["env"])
    lines = norm_lines(res["text"])
    opener = between(lines, lambda l: l == OPENER_BEGIN, lambda l: l == OPENER_END, False)
    got = clipboard(clip)
    ok = res["rc"] == 0 and opener is not None and got == opener
    verdict(ok, "D1 bale pack puts the session opener (the lines between its scissor "
                "lines) on the clipboard",
            f"rc={res['rc']} opener_found={opener is not None} clipboard={got!r:.300}\n"
            + tail(res["text"]))


def scenario_pack_json(work):
    root = work / "g-json"
    clip = make_clip(root / "clip", "ok")
    fx = make_fixture(root, global_clip=clip["cmd"])
    _sid, r = pack_piped(fx, "fx-json", "--json")
    out = r.stdout.splitlines()
    ok = False
    try:
        ok = len(out) == 1 and isinstance(json.loads(out[0]), dict)
    except ValueError:
        ok = False
    verdict(ok, "G1 bale pack --json keeps stdout to exactly its one JSON line",
            f"stdout={r.stdout[:600]!r}")


def scenario_relay(work):
    root = work / "d2"
    clip = make_clip(root / "clip", "ok")
    fx = make_fixture(root, global_clip=clip["cmd"])
    sid, _ = pack_piped(fx, "fx-relay")
    clip["file"].unlink(missing_ok=True)   # the pack may copy its opener; start clean
    mpath = root / "clar.json"
    mpath.write_text(json.dumps(clarification_manifest(sid)), encoding="utf-8")
    res = drive(fx["bale"] + ["relay", sid, str(mpath)], fx["repo"], fx["env"])
    lines = norm_lines(res["text"])
    block = between(lines, lambda l: l == f"{EXCHANGE_BEGIN} {sid}",
                    lambda l: l == EXCHANGE_END, True)
    got = clipboard(clip)
    verdict(res["rc"] == 0 and block is not None and got == block,
            "D2 bale relay puts the exchange block it emits on the clipboard",
            f"rc={res['rc']} block_found={block is not None} clipboard={got!r:.300}\n"
            + tail(res["text"]))
    # Guard: the re-emit form, piped, keeps stdout to exactly the block.
    r = subprocess.run(fx["bale"] + ["relay", sid], cwd=str(fx["repo"]), env=fx["env"],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True)
    out = norm_lines(r.stdout)
    ok = (r.returncode == 0 and out[:1] == [f"{EXCHANGE_BEGIN} {sid}"]
          and out[-1:] == [EXCHANGE_END] and (block is None or out == block))
    verdict(ok, "G2 bale relay keeps stdout to exactly the exchange block",
            f"rc={r.returncode} stdout={r.stdout[:400]!r}")


def relay_span(lines, sid, to):
    b = f"=== RELAY BEGIN {sid} to {to} ==="
    e = f"=== RELAY END {sid} to {to} ==="
    return between(lines, lambda l: l == b, lambda l: l == e, True)


def scenario_apply(work, passing):
    tag = "d3" if passing else "d4"
    root = work / tag
    clip = make_clip(root / "clip", "ok")
    fx = make_fixture(root, global_clip=clip["cmd"])
    sid, _ = pack_piped(fx, f"fx-{tag}")
    tarball = response_tarball(fx, sid, passing=passing)
    clip["file"].unlink(missing_ok=True)
    res = drive(fx["bale"] + ["apply", str(tarball)], fx["repo"], fx["env"])
    lines = norm_lines(res["text"])
    got = clipboard(clip)
    if passing:
        block = relay_span(lines, sid, "planner")
        applied = block is not None and any("APPLIED" in l for l in block)
        verdict(res["rc"] == 0 and applied and got == block,
                "D3 a passing bale apply puts its APPLIED relay block on the clipboard",
                f"rc={res['rc']} block_found={block is not None} clipboard={got!r:.300}\n"
                + tail(res["text"]))
    else:
        block = relay_span(lines, sid, "worker")
        send_first = any(re.search(r"send first:\s*worker", l) for l in lines)
        verdict(res["rc"] != 0 and block is not None and send_first and got == block,
                "D4 a held bale apply puts the block its card says to send first on the "
                "clipboard (worker-only HOLD: the worker block)",
                f"rc={res['rc']} block_found={block is not None} send_first_worker="
                f"{send_first} clipboard={got!r:.300}\n" + tail(res["text"]))


def emit_probe_script(work):
    """The crafter's probe scaffold, emitted from a directory with no
    bale.toml (a request that ships none)."""
    bare = work / "bare-request"
    bare.mkdir(exist_ok=True)
    r = subprocess.run([sys.executable, str(TREE / "tools" / "craft_response.py"),
                        "--probe", "fx-probe"], cwd=str(bare), capture_output=True,
                       text=True, env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                                       "HOME": str(bare), "LANG": "C.UTF-8"})
    if r.returncode != 0 or "PROBE BEGIN" not in r.stdout:
        raise WorkFailed(f"crafter --probe did not emit a scaffold: {r.stderr[-600:]}")
    script = bare / "probe.sh"
    script.write_text(r.stdout, encoding="utf-8")
    return script


def scenario_probe(work):
    script = emit_probe_script(work)
    root = work / "d5"
    clip = make_clip(root / "clip", "ok")
    fx = make_fixture(root, global_clip=clip["cmd"])
    r = subprocess.run(["bash", str(script)], cwd=str(fx["repo"]), env=fx["env"],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
    out = norm_lines(r.stdout)
    block = between(out, lambda l: l == "=== PROBE BEGIN fx-probe ===",
                    lambda l: l == "=== PROBE END fx-probe ===", True)
    got = clipboard(clip)
    verdict(r.returncode == 0 and block is not None and got == block,
            "D5 a probe from a request with no bale.toml copies its PROBE block through "
            "the installed bale on PATH, using the machine's configured command",
            f"rc={r.returncode} block_found={block is not None} clipboard={got!r:.300}\n"
            f"stderr={r.stderr[-600:]}")
    # Guard: no bale on PATH -> exit 0, the block still on stdout.
    env = dict(fx["env"])
    env["PATH"] = os.environ.get("PATH", "/usr/bin:/bin")
    if shutil.which("bale", path=env["PATH"]):
        env["PATH"] = "/usr/bin:/bin"
    r2 = subprocess.run(["bash", str(script)], cwd=str(fx["repo"]), env=env,
                        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=120)
    out2 = norm_lines(r2.stdout)
    ok2 = (r2.returncode == 0 and "=== PROBE BEGIN fx-probe ===" in out2
           and "=== PROBE END fx-probe ===" in out2)
    verdict(ok2, "G3 a probe with no bale on PATH still exits 0 with its block on stdout",
            f"rc={r2.returncode} stderr={r2.stderr[-400:]}")


def status_lines(fx):
    r = subprocess.run(fx["bale"] + ["status"], cwd=str(fx["repo"]), env=fx["env"],
                       stdin=subprocess.DEVNULL, capture_output=True, text=True)
    return r.returncode, norm_lines(r.stdout + "\n" + r.stderr)


def scenario_status(work):
    root = work / "d6"
    clip = make_clip(root / "clip", "ok")
    fx = make_fixture(root, global_clip=clip["cmd"])
    rc, lines = status_lines(fx)
    cmd = str(clip["cmd"])
    hit = [l for l in lines if cmd in l and mentions(l, "clipboard")]
    named = rc == 0 and hit and any(mentions(l, "global") for l in hit)
    root2 = work / "d6s"
    clip2 = make_clip(root2 / "clip", "ok")
    fx2 = make_fixture(root2, global_clip=clip2["cmd"],
                       project_toml='\n[probe]\nclipboard_command = ""\n')
    rc2, lines2 = status_lines(fx2)
    supp = rc2 == 0 and any(mentions(l, "clipboard") and mentions(l, "suppress")
                            for l in lines2)
    verdict(named and supp,
            "D6 bale status names the effective clipboard command and its layer, and "
            "says when the project suppresses it",
            f"global case rc={rc} lines={[l for l in lines if mentions(l, 'clipboard')]!r}\n"
            f"suppressed case rc={rc2} lines="
            f"{[l for l in lines2 if mentions(l, 'clipboard')]!r}")


def scenario_failing_command(work):
    root = work / "d7"
    bad = make_clip(root / "clip", "fail")
    fx = make_fixture(root, global_clip=bad["cmd"])
    res = drive(fx["bale"] + ["pack", "Fixture goal for a failing copy command",
                              "--slug", "fx-failclip", "--include", "hello.txt", "src",
                              "--write", "hello.txt", "--no-readme"], fx["repo"], fx["env"])
    outbox = sorted((fx["repo"] / ".bale" / "outbox").glob("request-*.tar.gz")) \
        if (fx["repo"] / ".bale" / "outbox").is_dir() else []
    lines = norm_lines(res["text"])
    opener_end = max((i for i, l in enumerate(lines) if l == OPENER_END), default=-1)
    said = any(mentions(l, "clipboard") for l in lines)
    verdict(res["rc"] == 0 and len(outbox) == 1 and said,
            "D7 a failing clipboard command never fails bale pack, and a line says the "
            "copy did not happen",
            f"rc={res['rc']} tarballs={len(outbox)} clipboard_line={said} "
            f"opener_end_at={opener_end}\n" + tail(res["text"]))


def scenario_unset(work):
    root = work / "g-unset"
    fx = make_fixture(root)
    sentinel = root / "detected-clipboard-used.txt"
    lure = root / "lure"
    lure.mkdir()
    for name in ("pbcopy", "wl-copy", "xclip", "xsel", "clip.exe"):
        p = lure / name
        p.write_text(f"#!/bin/sh\ncat > '{sentinel}'\n", encoding="utf-8")
        p.chmod(0o755)
    env = dict(fx["env"])
    env["PATH"] = f"{lure}:{env['PATH']}"
    env["WAYLAND_DISPLAY"] = "wayland-0"
    env["DISPLAY"] = ":0"
    res = drive(fx["bale"] + ["pack", "Fixture goal with no copy command configured",
                              "--slug", "fx-unset", "--include", "hello.txt", "src",
                              "--write", "hello.txt", "--no-readme"], fx["repo"], env)
    verdict(res["rc"] == 0 and not sentinel.exists(),
            "G4 with no clipboard command configured, nothing is copied, even with "
            "common clipboard programs on PATH",
            f"rc={res['rc']} sentinel_written={sentinel.exists()}\n" + tail(res["text"]))


def scenario_unreadable(work):
    root = work / "g-unreadable"
    clip = make_clip(root / "clip", "ok")
    fx = make_fixture(root, project_toml=f"\n[probe]\nclipboard_command = \"\"\"{clip['cmd']}\"\"\"\n")
    res = drive(fx["bale"] + ["pack", "Fixture goal with an unreadable copy key",
                              "--slug", "fx-unreadable", "--include", "hello.txt", "src",
                              "--write", "hello.txt", "--no-readme"], fx["repo"], fx["env"])
    outbox = sorted((fx["repo"] / ".bale" / "outbox").glob("request-*.tar.gz")) \
        if (fx["repo"] / ".bale" / "outbox").is_dir() else []
    verdict(res["rc"] == 0 and len(outbox) == 1,
            "G5 a clipboard_command bale cannot read (triple-quoted) never fails bale pack",
            f"rc={res['rc']} tarballs={len(outbox)}\n" + tail(res["text"]))


def main():
    # The scratch root's name must not contain "clipboard": D6 and D7
    # read lines by that word, and a path must never satisfy them.
    work = Path(tempfile.mkdtemp(prefix="cp-wave3-d-"))
    WORK_ROOTS[:] = sorted({str(work), str(work.resolve())})
    try:
        try:
            run_controls(work)
            print("[control] pty driver, block locator, stand-in clipboard: ok")
            for labels, run in (
                (["D1 bale pack puts the session opener on the clipboard"],
                 lambda: scenario_pack(work)),
                (["G1 bale pack --json keeps stdout to exactly its one JSON line"],
                 lambda: scenario_pack_json(work)),
                (["D2 bale relay puts the exchange block it emits on the clipboard",
                  "G2 bale relay keeps stdout to exactly the exchange block"],
                 lambda: scenario_relay(work)),
                (["D3 a passing bale apply puts its APPLIED relay block on the clipboard"],
                 lambda: scenario_apply(work, passing=True)),
                (["D4 a held bale apply puts its send-first block on the clipboard"],
                 lambda: scenario_apply(work, passing=False)),
                (["D5 a probe copies its PROBE block through the installed bale",
                  "G3 a probe with no bale on PATH still exits 0 with its block"],
                 lambda: scenario_probe(work)),
                (["D6 bale status names the clipboard command and its layer"],
                 lambda: scenario_status(work)),
                (["D7 a failing clipboard command never fails bale pack"],
                 lambda: scenario_failing_command(work)),
                (["G4 with no clipboard command configured, nothing is copied"],
                 lambda: scenario_unset(work)),
                (["G5 an unreadable clipboard_command never fails bale pack"],
                 lambda: scenario_unreadable(work)),
            ):
                try:
                    run()
                except WorkFailed as e:
                    for label in labels:
                        verdict(False, label + " (a fixture step that runs the tree "
                                       "under test failed)", str(e))
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
