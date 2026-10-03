#!/usr/bin/env bash
# Blind checkpoint — session config-wizard-ui (2026-10-03-friction-points-001 desk).
# Authored blind from the request, before implementation. Outcome-only:
# it drives `bale config init` (project and --global layers) from this
# tree as an install and judges what the operator sees and what lands
# in bale.toml. Exit 0 = every probe passes; 1 = a probe failed;
# 2 = the oracle itself broke (a failed control).
set -uo pipefail
export PYTHONDONTWRITEBYTECODE=1
ROOT="$(pwd)"
exec python3 - "$ROOT" <<'PY'
import os, pty, re, select, shutil, struct, subprocess, sys, tempfile, time
import fcntl, termios

ROOT = sys.argv[1]
FAILED = []

def verdict(ok, label, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + (f" — {detail}" if detail and not ok else ""))
    if not ok:
        FAILED.append(label)

def control_fail(msg):
    print(f"control failed: {msg}")
    sys.exit(2)

PROJECT_KEYS = [
    "hooks.post_pack", "hooks.post_apply_pass", "apply.search_paths",
    "apply.no_interact", "apply.hook_auto_accept", "apply.archive_dir",
    "apply.sweep", "staging.strategy", "staging.untracked_inputs",
    "identity.packer", "validation.base", "validation.required",
    "sandbox.network", "sandbox.enabled", "pack.include_group",
    "pack.include_group_triggers", "pack.include_group_pulls",
    "probe.clipboard_command", "layout.agent_dir",
]
GLOBAL_KEYS = [
    "hooks.post_pack", "hooks.post_apply_pass", "apply.search_paths",
    "apply.no_interact", "apply.hook_auto_accept", "apply.archive_dir",
    "apply.sweep", "staging.strategy", "staging.untracked_inputs",
    "identity.packer",
]
PROJECT_ONLY = [k for k in PROJECT_KEYS if k not in GLOBAL_KEYS]

ANSI = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]|\x1b\][^\x07]*\x07|\x1b[@-Z\\-_]")
RULE_ONLY = re.compile(r"^[\s\-─━═=_~·•.*+|]+$")
MAX_COLS = 80
MAX_ITEM_LINES = 14

T = tempfile.mkdtemp(prefix="ck-")
HOME = os.path.join(T, "home")
INST = os.path.join(T, "inst")
os.makedirs(HOME)
with open(os.path.join(HOME, ".gitconfig"), "w") as f:
    f.write("[user]\n\tname = Desk Fixture\n\temail = desk@example.invalid\n"
            "[init]\n\tdefaultBranch = main\n")

def ignore(d, entries):
    if os.path.abspath(d) == os.path.abspath(ROOT):
        return [e for e in entries if e in (".git", ".bale", "user")]
    return [e for e in entries if e == "__pycache__"]

try:
    shutil.copytree(ROOT, INST, symlinks=True, ignore=ignore)
except Exception as e:
    control_fail(f"could not copy the tree as an install: {e}")
BALE = os.path.join(INST, "bin", "bale")
if not os.path.isfile(BALE):
    control_fail("bin/bale missing from the tree")

ENV = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": HOME,
       "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "TERM": "xterm-256color",
       "COLUMNS": "80", "LINES": "24", "PYTHONDONTWRITEBYTECODE": "1",
       "EDITOR": "true", "VISUAL": "true"}

def git(repo, *args):
    subprocess.run(["git", *args], cwd=repo, env=ENV, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def make_repo(name):
    repo = os.path.join(T, name)
    os.makedirs(repo)
    git(repo, "init", "-q")
    with open(os.path.join(repo, "README"), "w") as f:
        f.write("fixture\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "init")
    return repo

def run_pty(args, cwd, extra_env=None, quiet=0.8, limit=240):
    """Run bale under an 80x24 pty, pressing Enter whenever output goes
    quiet. Returns (exit_code, segments): segments[i] is the output
    printed between Enter i-1 and Enter i (CR stripped)."""
    env = dict(ENV, **(extra_env or {}))
    try:
        pid, fd = pty.fork()
    except OSError as e:
        control_fail(f"no pty available: {e}")
    if pid == 0:
        os.chdir(cwd)
        os.execve(sys.executable, [sys.executable, BALE, *args], env)
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))
    segs, cur, last, start = [], b"", time.time(), time.time()
    while True:
        if time.time() - start > limit:
            os.kill(pid, 9)
            break
        r, _, _ = select.select([fd], [], [], 0.2)
        if r:
            try:
                d = os.read(fd, 65536)
            except OSError:
                break
            if not d:
                break
            cur += d
            last = time.time()
        elif time.time() - last > quiet:
            segs.append(cur)
            cur = b""
            try:
                os.write(fd, b"\n")
            except OSError:
                break
            last = time.time()
    segs.append(cur)
    _, status = os.waitpid(pid, 0)
    code = os.waitstatus_to_exitcode(status)
    return code, [s.decode("utf-8", "replace").replace("\r", "") for s in segs]

def plain(text):
    return ANSI.sub("", text)

def width(line):
    try:
        import unicodedata
        return sum(2 if unicodedata.east_asian_width(c) in "WF" else 1
                   for c in line)
    except Exception:
        return len(line)

sys.path.insert(0, os.path.join(INST, "bin"))
try:
    import _bale_toml
except Exception as e:
    control_fail(f"bale's own TOML parser did not import: {e}")

def parsed(path):
    if not os.path.isfile(path):
        return {}
    with open(path, encoding="utf-8") as f:
        return _bale_toml.loads(f.read())

def has_key(text, key):
    return re.search(r"(?<![\w.])" + re.escape(key) + r"(?![\w])", text) is not None

def item_segments(segs, keys):
    """For each walked key, the first Enter-delimited segment whose
    first-mentioned walked key is that key — the item's own screen."""
    out = {}
    for s in segs:
        p = plain(s)
        firsts = [(m.start(), k) for k in keys
                  for m in [re.search(r"(?<![\w.])" + re.escape(k) + r"(?![\w])", p)] if m]
        if not firsts:
            continue
        k = min(firsts)[1]
        out.setdefault(k, p)
    return out

def judge_layout(tag, segs, keys):
    text = plain("".join(segs))
    long = [ln for ln in text.split("\n") if width(ln) > MAX_COLS and T not in ln]
    verdict(not long, f"{tag}: every line fits {MAX_COLS} columns (lines naming the fixture path exempt)",
            f"{len(long)} line(s) too wide, e.g. {long[0][:100]!r}" if long else "")
    items = item_segments(segs, keys)
    missing = [k for k in keys if k not in items]
    verdict(not missing, f"{tag}: each configurable gets its own prompt screen",
            f"no screen leads with: {', '.join(missing)}")
    tall, unseparated = [], []
    for k, seg in items.items():
        # Line 0 is the tail of the previous prompt line (the echoed Enter).
        body = seg.split("\n")[1:]
        idx = next((i for i, ln in enumerate(body) if has_key(ln, k)), None)
        if idx is None:
            continue
        seps = [i for i, ln in enumerate(body[:idx])
                if (not ln.strip()) or RULE_ONLY.match(ln)]
        if not seps:
            unseparated.append(k)
        screen = body[(seps[-1] + 1) if seps else 0:]
        nonblank = [ln for ln in screen if ln.strip()]
        if len(nonblank) > MAX_ITEM_LINES:
            tall.append(f"{k} ({len(nonblank)})")
    verdict(not tall, f"{tag}: an item's default screen is at most {MAX_ITEM_LINES} non-blank lines",
            "too tall: " + ", ".join(tall))
    verdict(not unseparated, f"{tag}: consecutive items are visibly separated (blank or rule line before each)",
            "unseparated: " + ", ".join(unseparated))

# ---- control: the driver sees a prompt and the tree runs as an install --
code, segs = run_pty(["--version"], T)
if code != 0 or "bale" not in plain("".join(segs)).lower():
    control_fail(f"`bale --version` from the tree did not run (exit {code})")

# ---- 1. project layer, fresh repo, Enter through everything --------------
repo1 = make_repo("fresh")
code, segs = run_pty(["config", "init"], repo1)
text = plain("".join(segs))
verdict(code == 0, "project wizard: Enter-through exits 0", f"exit {code}")
missing = [k for k in PROJECT_KEYS if not has_key(text, k)]
verdict(not missing, "project wizard: walks every project-layer configurable by its dotted key",
        "absent: " + ", ".join(missing))
got = parsed(os.path.join(repo1, "bale.toml"))
verdict(got == {}, "project wizard: Enter-through on a fresh repo sets no configurable",
        f"bale.toml parsed to {got!r}")
verdict(not os.path.exists(os.path.join(repo1, ".baleignore")),
        "project wizard: Enter-through creates no .baleignore")
judge_layout("project wizard", segs, PROJECT_KEYS)

# ---- 2. project layer, existing values preserved through Enter ----------
SEED_GLOBAL = '[hooks]\npost_pack = "scripts/g.sh"\n[identity]\npacker = "global-desk"\n'
SEED_PROJECT = """[hooks]
post_pack = ""
post_apply_pass = "scripts/reinstall.sh"
[apply]
search_paths = ["~/Downloads", "$HOME/inbox"]
no_interact = false
hook_auto_accept = true
archive_dir = "claude/responses"
sweep = true
[staging]
strategy = "target-base"
untracked_inputs = [".venv"]
[identity]
packer = "desk"
[validation]
base = "claude/checkpoints/{sid}.sh"
required = ["tests", "lint"]
[sandbox]
network = true
enabled = true
[pack]
include_group = "release-surface"
include_group_triggers = ["bin", "tests"]
include_group_pulls = ["docs"]
[probe]
clipboard_command = "pbcopy"
[layout]
agent_dir = "claude"
"""
os.makedirs(os.path.join(INST, "user"), exist_ok=True)
with open(os.path.join(INST, "user", "bale.toml"), "w") as f:
    f.write(SEED_GLOBAL)
repo2 = make_repo("seeded")
with open(os.path.join(repo2, "bale.toml"), "w") as f:
    f.write(SEED_PROJECT)
with open(os.path.join(repo2, ".baleignore"), "w") as f:
    f.write("# keep me\ndata/\n")
want = _bale_toml.loads(SEED_PROJECT)
code, segs = run_pty(["config", "init"], repo2)
verdict(code == 0, "project wizard (seeded): Enter-through exits 0", f"exit {code}")
got = parsed(os.path.join(repo2, "bale.toml"))
verdict(got == want, "project wizard (seeded): Enter-through preserves every value, including the empty-string suppression",
        f"diff keys: {sorted(set(map(str, got.items())) ^ set(map(str, want.items())))[:3]}")
with open(os.path.join(repo2, ".baleignore")) as f:
    bi = f.read()
verdict("data/" in bi.split("\n"), "project wizard (seeded): Enter-through keeps existing .baleignore patterns")
judge_layout("project wizard (seeded)", segs, PROJECT_KEYS)

# ---- 3. global layer ------------------------------------------------------
code, segs = run_pty(["config", "init", "--global"], repo1)
text = plain("".join(segs))
verdict(code == 0, "global wizard: Enter-through exits 0", f"exit {code}")
missing = [k for k in GLOBAL_KEYS if not has_key(text, k)]
verdict(not missing, "global wizard: walks every global-layer configurable", "absent: " + ", ".join(missing))
leaked = [k for k in PROJECT_ONLY if has_key(text, k)]
verdict(not leaked, "global wizard: offers no project-only configurable", "offered: " + ", ".join(leaked))
got = parsed(os.path.join(INST, "user", "bale.toml"))
verdict(got == _bale_toml.loads(SEED_GLOBAL), "global wizard: Enter-through preserves the global file's values",
        f"parsed {got!r}")
judge_layout("global wizard", segs, GLOBAL_KEYS)

# ---- 4. plain output where color cannot render ---------------------------
repo3 = make_repo("plain")
p = subprocess.run([sys.executable, BALE, "config", "init"], cwd=repo3, env=ENV,
                   input="\n" * 80, capture_output=True, text=True, timeout=120)
verdict(p.returncode == 0 and "\x1b" not in p.stdout + p.stderr,
        "piped (non-TTY) run: exits 0 and emits no ANSI escape sequences",
        f"exit {p.returncode}, escapes={chr(27) in p.stdout + p.stderr}")
repo4 = make_repo("nocolor")
code, segs = run_pty(["config", "init"], repo4, extra_env={"NO_COLOR": "1"})
raw = "".join(segs)
verdict(code == 0 and "\x1b[" not in raw.replace("\x1b[?2004h", "").replace("\x1b[?2004l", ""),
        "NO_COLOR=1 under a TTY: no color escape sequences", f"exit {code}")

shutil.rmtree(T, ignore_errors=True)
print(f"checkpoint: {len(FAILED)} probe(s) failed")
sys.exit(1 if FAILED else 0)
PY
