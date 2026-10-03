#!/usr/bin/env bash
# Blind checkpoint, v1: session C of the friction-points split, wave 2
# (slug wizard-defaults). Authored blind at the read-only planner desk
# 2026-10-03-friction-points-wave2-004 from C's brief, before any
# implementation exists. The worker never reads, ships, or declares
# this file (TARBALL.md section 7).
#
# What it grades: outcomes of `bale config init`, never how they were
# reached. The brief pins one interaction contract this oracle reads:
# an offered alternative is a line of its own that opens with its
# number in brackets, then the value as it would be typed
# ("[2] wl-copy"), and typing that number sets the value at the layer
# being walked.
#   C1  global layer: the clipboard command is offered with
#       alternatives for macOS, Windows/WSL, Wayland, and X11, and the
#       pick is written to the install's bale.toml;
#   C2  project layer: the clipboard alternatives are offered there
#       too, and a pick is written to the project's bale.toml;
#   C3  a project's existing [probe] clipboard_command survives an
#       Enter-through, still readable by the request-carried crafter;
#   C4  identity.packer offers git's user.name;
#   C5  staging.strategy offers its values;
#   C6  apply.search_paths offers the home Downloads directory;
#   C7  apply.archive_dir offers claude/responses;
#   C8  staging.untracked_inputs offers an untracked .venv;
#   C9  validation.base offers claude/checkpoints/{sid}.sh;
#   CW  every wizard line still fits 80 columns.
# Scenarios on their own fresh fixtures: SG the global layer, SP the
# project layer, SB the back-compat Enter-through.
#
# How it drives: a real pty at 80x24 with TERM set (escape codes are
# stripped before reading). Each time the wizard waits for input, the
# driver reads the screen printed since its last answer; if that
# screen offers one of the scenario's target values as a bracketed
# alternative, it types the number, otherwise it presses Enter. The
# locators are those bracketed lines alone: no prompt wording, key
# name, or item position is read.
#
# Exit codes: 0 every probe passed; 1 a probe failed; 2 a control
# failed or a fixture could not be built (the oracle is broken, not
# the work).
set -u
exec python3 - "$PWD" <<'BALE_CHECKPOINT_PY'
import os
import pty
import re
import select
import shutil
import struct
import subprocess
import sys
import tempfile
import time
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
WIDTH = 80
ROWS = 24
INSTALL_TREES = ("bin", "docs", "schemas", "tools")
LOG_PREFIX = "[bale] "
ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)|\x1b[@-Z\\-_]")
ALT_LINE_RE = re.compile(r"^\s*\[(\d{1,2})\]\s+(\S.*?)\s*$")
# The absolute paths a scenario can make bale print all live under its
# scratch root; a line naming one of them is the width contract's one
# exemption. Set by main().
ABS_ROOTS = []

PROMPT_IDLE = 0.25
ANY_IDLE = 2.5
RUN_TIMEOUT = 150.0
MAX_ANSWERS = 150


class OracleBroken(Exception):
    """A control failed or a fixture could not be built: exit 2."""


def strip_ansi(text):
    return ANSI_RE.sub("", text)


def lines_of(segment):
    text = strip_ansi(segment).replace("\r\n", "\n").replace("\r", "\n")
    return text.split("\n")


def alternatives(segment):
    """[(number, value text)] for every bracketed alternative line."""
    out = []
    for line in lines_of(segment):
        m = ALT_LINE_RE.match(line)
        if m:
            out.append((m.group(1), m.group(2)))
    return out


def first_token(text):
    tok = text.split()[0] if text.split() else ""
    return tok.strip("\"'")


def width_offenders(segments):
    bad = []
    for k, seg in enumerate(segments):
        for line in lines_of(seg):
            if line.startswith(LOG_PREFIX):
                continue
            if len(line) > WIDTH and not any(r in line for r in ABS_ROOTS):
                bad.append((k, len(line), line))
    return bad


def looks_like_prompt(buf):
    tail = strip_ansi(buf.decode("utf-8", errors="replace"))
    return bool(tail) and not tail.endswith("\n")


def drive(argv, cwd, env, respond):
    """Run argv on a pty at 80x24. Each time it waits for input, call
    respond(screen) with the text printed since the last answer and type
    what it returns. Returns rc, segments, answers, timed_out."""
    import fcntl
    import termios
    master, slave = pty.openpty()
    fcntl.ioctl(slave, termios.TIOCSWINSZ, struct.pack("HHHH", ROWS, WIDTH, 0, 0))
    proc = subprocess.Popen(argv, cwd=str(cwd), env=env, stdin=slave,
                            stdout=slave, stderr=slave, close_fds=True,
                            start_new_session=True)
    os.close(slave)
    segments, answers = [], []
    buf = b""
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
                    buf += chunk
            except OSError:
                pass
            break
        now = time.monotonic()
        if now > deadline or len(answers) >= MAX_ANSWERS:
            timed_out = True
            proc.kill()
            break
        idle = now - last
        if (idle >= PROMPT_IDLE and looks_like_prompt(buf)) or idle >= ANY_IDLE:
            screen = buf.decode("utf-8", errors="replace")
            segments.append(screen)
            buf = b""
            answer = respond(screen)
            answers.append(answer)
            os.write(master, (answer + "\n").encode("utf-8"))
            last = time.monotonic()
    segments.append(buf.decode("utf-8", errors="replace"))
    try:
        rc = proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        rc = proc.wait()
    os.close(master)
    return {"rc": rc, "segments": segments, "answers": answers, "timed_out": timed_out}


class Picker:
    """Answers a screen with the number of the first not-yet-picked
    target it offers, else Enter. Records the screen each pick came from."""

    def __init__(self, targets):
        self.targets = dict(targets)   # name -> predicate(value text)
        self.picked = {}               # name -> (number, value, screen)

    def __call__(self, screen):
        offered = alternatives(screen)
        for name, pred in self.targets.items():
            if name in self.picked:
                continue
            for number, value in offered:
                if pred(value):
                    self.picked[name] = (number, value, screen)
                    return number
        return ""


# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

CONTROL_CHILD = r'''
import os, sys
cols, rows = os.get_terminal_size(0)
print(f"size {cols}x{rows}")
print("  \x1b[36m[1]\x1b[0m  pbcopy        (macOS)")
print("  [2] wl-copy  (Wayland)")
a = input("pick > ")
print("x" * 81)
print("see " + sys.argv[1] + "/" + "z" * 90)
print("[bale] " + "w" * 120)
b = input("next > ")
print(f"got {a}|{b}")
'''


def run_controls(scratch):
    child = scratch / "control_child.py"
    child.write_text(CONTROL_CHILD, encoding="utf-8")
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8",
           "TERM": "xterm", "HOME": str(scratch)}
    picker = Picker({"wl": lambda v: first_token(v) == "wl-copy"})
    res = drive([sys.executable, str(child), str(scratch)], scratch, env, picker)
    problems = []
    segs = res["segments"]
    if res["rc"] != 0 or res["timed_out"] or res["answers"] != ["2", ""]:
        problems.append(f"driver run: rc={res['rc']} answers={res['answers']!r}")
    if len(segs) != 3 or "size 80x24" not in segs[0] or "got 2|" not in segs[-1]:
        problems.append(f"segments: {segs!r}")
    alts = alternatives(segs[0]) if segs else []
    if [n for n, _ in alts] != ["1", "2"] or first_token(alts[0][1]) != "pbcopy":
        problems.append(f"alternative locator: {alts!r}")
    bad = width_offenders(segs)
    if [n for _, n, _ in bad] != [81]:
        problems.append(f"width detector: {bad!r}")
    try:
        toml = load_toml_module()
        if toml.loads('[a]\nb = "c"\n') != {"a": {"b": "c"}}:
            problems.append("toml reader returned the wrong value")
    except Exception as e:  # noqa: BLE001 — any failure here is the oracle's
        problems.append(f"toml reader: {e}")
    if problems:
        raise OracleBroken("control failed: " + "; ".join(problems))


def load_toml_module():
    """bale's own 3.10-safe TOML reader from the tree under test."""
    sys.path.insert(0, str(TREE / "bin"))
    try:
        import _bale_toml
    finally:
        sys.path.pop(0)
    return _bale_toml


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def checked(cmd, cwd, env):
    r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True, text=True)
    if r.returncode != 0:
        raise OracleBroken(f"fixture command failed: {cmd}: {r.stdout}{r.stderr}")
    return r


def make_fixture(root):
    home = root / "home"
    (home / "Downloads").mkdir(parents=True)
    (home / ".gitconfig").write_text(
        "[user]\n\tname = Fixture Packer\n\temail = fixture@example.invalid\n"
        "[init]\n\tdefaultBranch = main\n", encoding="utf-8")
    install = root / "install"
    install.mkdir()
    for tree in INSTALL_TREES:
        if not (TREE / tree).is_dir():
            raise OracleBroken(f"tree under test has no {tree}/")
        shutil.copytree(TREE / tree, install / tree)
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home),
           "LANG": "C.UTF-8", "TERM": "xterm", "EDITOR": "/bin/true",
           "VISUAL": "/bin/true", "BALE_INSTALL": str(root / "bale-install-sandbox")}
    return home, install, env


def make_repo(root, env, files):
    repo = root / "project"
    repo.mkdir()
    checked(["git", "init", "-q", "-b", "main"], repo, env)
    for rel, body in files.items():
        (repo / rel).parent.mkdir(parents=True, exist_ok=True)
        (repo / rel).write_text(body, encoding="utf-8")
    checked(["git", "add", "-A"], repo, env)
    checked(["git", "commit", "-q", "-m", "fixture"], repo, env)
    return repo


def read_toml(path):
    if not path.is_file():
        return None
    return load_toml_module().loads(path.read_text(encoding="utf-8"))


def string_values(node):
    if isinstance(node, dict):
        for v in node.values():
            yield from string_values(v)
    elif isinstance(node, list):
        for v in node:
            yield from string_values(v)
    elif isinstance(node, str):
        yield node


def get(cfg, dotted):
    node = cfg or {}
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


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


def run_report(res):
    return (f"rc={res['rc']} timed_out={res['timed_out']} answers={len(res['answers'])}\n"
            "--- last screen ---\n" + strip_ansi(res["segments"][-1])[-1200:])


def clipboard_preds():
    return {
        "pbcopy": lambda v: first_token(v) == "pbcopy",
        "clip.exe": lambda v: first_token(v).lower().endswith("clip.exe"),
        "wl-copy": lambda v: first_token(v) == "wl-copy",
        "xclip/xsel": lambda v: first_token(v) in ("xclip", "xsel"),
    }


def offers_all_clipboards(screen):
    offered = [v for _, v in alternatives(screen)]
    return [name for name, pred in clipboard_preds().items()
            if not any(pred(v) for v in offered)]


def scenario_global(work):
    root = work / "sg"
    home, install, env = make_fixture(root)
    elsewhere = root / "elsewhere"
    elsewhere.mkdir()
    downloads = {str(home / "Downloads"), str(home / "Downloads") + "/",
                 "~/Downloads", "~/Downloads/", "$HOME/Downloads", "${HOME}/Downloads"}
    picker = Picker({
        "clipboard": clipboard_preds()["wl-copy"],
        "packer": lambda v: v == "Fixture Packer" or v.startswith("Fixture Packer "),
        "downloads": lambda v: first_token(v) in downloads,
    })
    res = drive([sys.executable, str(install / "bin" / "bale"), "config", "init", "--global"],
                elsewhere, env, picker)
    ran = res["rc"] == 0 and not res["timed_out"]
    cfg = read_toml(install / "user" / "bale.toml") if ran else None
    report = run_report(res)

    clip = picker.picked.get("clipboard")
    missing = offers_all_clipboards(clip[2]) if clip else list(clipboard_preds())
    wrote = cfg is not None and any(s.strip().startswith("wl-copy") for s in string_values(cfg))
    verdict(ran and clip is not None and not missing and wrote,
            "C1.SG the global wizard offers the clipboard command with macOS, Windows/WSL, "
            "Wayland, and X11 alternatives, and the pick is written to the install's bale.toml",
            f"picked={clip[:2] if clip else None} missing={missing} written={wrote}\n{report}")

    packer = get(cfg, "identity.packer")
    verdict(ran and "packer" in picker.picked and packer == "Fixture Packer",
            "C4.SG identity.packer offers git's user.name, and the pick is written",
            f"picked={picker.picked.get('packer', (None, None))[:2]} written={packer!r}")

    paths = get(cfg, "apply.search_paths")
    ok_paths = False
    if isinstance(paths, list):
        saved = os.environ.get("HOME")
        os.environ["HOME"] = str(home)
        try:
            ok_paths = any(os.path.normpath(os.path.expandvars(os.path.expanduser(p)))
                           == str(home / "Downloads") for p in paths if isinstance(p, str))
        finally:
            if saved is None:
                os.environ.pop("HOME", None)
            else:
                os.environ["HOME"] = saved
    verdict(ran and "downloads" in picker.picked and ok_paths,
            "C6.SG apply.search_paths offers the home Downloads directory, and the pick "
            "is written", f"picked={picker.picked.get('downloads', (None, None))[:2]} "
                          f"written={paths!r}")
    return res


def scenario_project(work):
    root = work / "sp"
    home, install, env = make_fixture(root)
    repo = make_repo(root, env, {"hello.txt": "hello\n", ".gitignore": ".venv/\n"})
    (repo / ".venv").mkdir()
    (repo / ".venv" / "pyvenv.cfg").write_text("home = /usr/bin\n", encoding="utf-8")
    picker = Picker({
        "clipboard": clipboard_preds()["pbcopy"],
        "strategy": lambda v: first_token(v) == "target-base",
        "untracked": lambda v: first_token(v) in (".venv", ".venv/", "./.venv", "./.venv/"),
        "base": lambda v: first_token(v) == "claude/checkpoints/{sid}.sh",
        "archive": lambda v: first_token(v) in ("claude/responses", "claude/responses/"),
    })
    res = drive([sys.executable, str(install / "bin" / "bale"), "config", "init"],
                repo, env, picker)
    ran = res["rc"] == 0 and not res["timed_out"]
    cfg = read_toml(repo / "bale.toml") if ran else None
    report = run_report(res)

    clip = picker.picked.get("clipboard")
    missing = offers_all_clipboards(clip[2]) if clip else list(clipboard_preds())
    wrote = cfg is not None and any(s.strip().startswith("pbcopy") for s in string_values(cfg))
    verdict(ran and clip is not None and not missing and wrote,
            "C2.SP the project wizard offers the same clipboard alternatives, and the pick "
            "is written to the project's bale.toml",
            f"picked={clip[:2] if clip else None} missing={missing} written={wrote}\n{report}")

    def norm(v):
        return v.rstrip("/") if isinstance(v, str) else v

    checks = (
        ("C5.SP staging.strategy offers its values, and the pick is written",
         "strategy", get(cfg, "staging.strategy") == "target-base",
         get(cfg, "staging.strategy")),
        ("C7.SP apply.archive_dir offers claude/responses, and the pick is written",
         "archive", norm(get(cfg, "apply.archive_dir")) == "claude/responses",
         get(cfg, "apply.archive_dir")),
        ("C8.SP staging.untracked_inputs offers the untracked .venv, and the pick is written",
         "untracked", isinstance(get(cfg, "staging.untracked_inputs"), list)
         and any(norm(p).removeprefix("./") == ".venv"
                 for p in get(cfg, "staging.untracked_inputs") if isinstance(p, str)),
         get(cfg, "staging.untracked_inputs")),
        ("C9.SP validation.base offers claude/checkpoints/{sid}.sh, and the pick is written",
         "base", get(cfg, "validation.base") == "claude/checkpoints/{sid}.sh",
         get(cfg, "validation.base")),
    )
    for label, name, ok, written in checks:
        verdict(ran and name in picker.picked and ok, label,
                f"picked={picker.picked.get(name, (None, None))[:2]} written={written!r}")
    return res


def scenario_backcompat(work):
    root = work / "sb"
    home, install, env = make_fixture(root)
    repo = make_repo(root, env, {
        "hello.txt": "hello\n",
        "bale.toml": '[probe]\nclipboard_command = "xclip -selection clipboard"\n',
    })
    res = drive([sys.executable, str(install / "bin" / "bale"), "config", "init"],
                repo, env, lambda screen: "")
    ran = res["rc"] == 0 and not res["timed_out"]
    crafted = subprocess.run([sys.executable, str(TREE / "tools" / "craft_response.py"),
                              "--probe", "fixture-clip"], cwd=str(repo), env=env,
                             capture_output=True, text=True)
    ok = ran and crafted.returncode == 0 and "xclip -selection clipboard" in crafted.stdout
    verdict(ok, "C3.SB an existing project [probe] clipboard_command survives an "
                "Enter-through and the request-carried crafter still reads it",
            f"crafter rc={crafted.returncode} stderr={crafted.stderr[-400:]}\n{run_report(res)}")


def main():
    work = Path(tempfile.mkdtemp(prefix="cp-wizard-defaults-"))
    ABS_ROOTS[:] = sorted({str(work), str(work.resolve())})
    try:
        try:
            run_controls(work)
            print("[control] pty driver, alternative locator, width detector, toml reader: ok")
            sg = scenario_global(work)
            sp = scenario_project(work)
            scenario_backcompat(work)
        except OracleBroken as e:
            print(f"checkpoint error (oracle, not the work): {e}")
            return 2
        for tag, res in (("SG", sg), ("SP", sp)):
            bad = width_offenders(res["segments"])
            verdict(not bad, f"CW.{tag} every line the wizard prints fits 80 columns",
                    "\n".join(f"screen {k}: {n} cols: {ln[:120]}" for k, n, ln in bad))
    finally:
        shutil.rmtree(work, ignore_errors=True)
    failed = RESULTS.count(False)
    print(f"checkpoint: {len(RESULTS) - failed}/{len(RESULTS)} probes passed")
    return 1 if failed else 0


sys.exit(main())
BALE_CHECKPOINT_PY
