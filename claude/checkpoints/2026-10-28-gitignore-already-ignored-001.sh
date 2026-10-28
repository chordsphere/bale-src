#!/usr/bin/env bash
# Blind checkpoint - session gitignore-already-ignored (bale-src), version 1.
# Authored 2026-10-28 by sitting 2026-10-28-bale-on-its-first-pack-in-a-clone-bale-sitting-001,
# from the request, before any implementation existed.
#
# Outcome contract only: what must be true of the applied tree. The cwd
# is the staged tree. Exit 0 = every probe passed; 1 = at least one probe
# failed (a HOLD on the work); 2 = this oracle is defective (a control
# failed, a fixture could not be built, or an unplanned exception) -
# never a verdict on the work. Verdict lines carry the label alone;
# detail follows on "  detail:" lines.
# Reads the staged tree only; writes only under a temporary directory of
# its own that it removes; needs no sid, no manifest, no own path.
#
# What it does, in plain words: it builds three throwaway git repos, runs
# the staged bin/bale pack in each with stdin closed, and reads the
# repos back. Two repos already ignore .bale/ through .git/info/exclude
# and must come out with no new commit and their .gitignore untouched
# (or still absent); the third ignores nothing and must come out with
# .bale/ in .gitignore and the commit "bale: ignore .bale/" at HEAD, as
# today. HOME is pointed at an empty directory for every git and bale
# call, so the operator's own global excludes cannot leak into a repo.
set -u
exec python3 -I -B - <<'ORACLE'
import os, shutil, subprocess, sys, tempfile, traceback
from pathlib import Path

SUBJECT = "bale: ignore .bale/"
STAGE = Path.cwd()
BALE = STAGE / "bin" / "bale"
PACK_TIMEOUT = 240  # seconds per pack run

status = 0


def note(msg):
    print(f"[ckpt] {msg}")


def passed(label):
    print(f"[ckpt] pass: {label}")


def failed(label, detail):
    global status
    status = 1
    print(f"[ckpt] FAIL: {label}")
    for line in str(detail).rstrip().splitlines() or ["(no detail)"]:
        print(f"  detail: {line}")


def defective(msg):
    print(f"[ckpt] ORACLE DEFECT: {msg}")
    sys.stdout.flush()
    sys.exit(2)


# ------------------------------------------------------------ environment
ROOT = None
HOME = None


def base_env():
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("GIT_") and k not in ("HOME", "XDG_CONFIG_HOME")}
    env.update({
        "HOME": str(HOME),
        "XDG_CONFIG_HOME": str(HOME / ".config"),
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_PAGER": "cat",
        "PAGER": "cat",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
    return env


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, env=base_env(),
                          stdin=subprocess.DEVNULL, capture_output=True,
                          text=True, timeout=60)


def tail(text, n=12):
    lines = text.rstrip().splitlines()
    return "\n".join(lines[-n:]) if lines else "(empty)"


# --------------------------------------------------------------- fixtures
def make_repo(name, gitignore=None, exclude_bale=False):
    """One fresh repo per scenario (isolation): one commit holding
    README.md and, when given, a .gitignore; optionally .bale/ appended
    to .git/info/exclude after the commit."""
    repo = ROOT / name
    repo.mkdir()
    for args in (("init", "-q"),
                 ("config", "user.name", "ckpt"),
                 ("config", "user.email", "ckpt@example.invalid"),
                 ("config", "commit.gpgsign", "false")):
        r = git(repo, *args)
        if r.returncode != 0:
            defective(f"git {' '.join(args)} failed building {name}: {tail(r.stderr)}")
    (repo / "README.md").write_text("fixture\n", encoding="utf-8")
    if gitignore is not None:
        (repo / ".gitignore").write_bytes(gitignore)
    for args in (("add", "-A"), ("commit", "-q", "-m", "fixture")):
        r = git(repo, *args)
        if r.returncode != 0:
            defective(f"git {' '.join(args)} failed building {name}: {tail(r.stderr)}")
    if exclude_bale:
        info = repo / ".git" / "info"
        info.mkdir(exist_ok=True)
        with (info / "exclude").open("a", encoding="utf-8") as fh:
            fh.write(".bale/\n")
    return repo


# -------------------------------------------------------------- detectors
def commit_subjects(repo):
    r = git(repo, "log", "--format=%s")
    if r.returncode != 0:
        defective(f"git log failed in {repo.name}: {tail(r.stderr)}")
    return r.stdout.splitlines()


def gitignore_bytes(repo):
    p = repo / ".gitignore"
    return p.read_bytes() if p.exists() else None


def git_ignores_bale(repo):
    # Asked with the trailing slash: a directory-only pattern such as
    # ".bale/" does not match a bare ".bale" that does not exist yet
    # (git 2.43, verified at authoring), and before a first pack the
    # directory does not exist.
    r = git(repo, "check-ignore", "-q", ".bale/")
    if r.returncode not in (0, 1):
        defective(f"git check-ignore errored in {repo.name}: {tail(r.stderr)}")
    return r.returncode == 0


def porcelain(repo):
    r = git(repo, "status", "--porcelain")
    if r.returncode != 0:
        defective(f"git status failed in {repo.name}: {tail(r.stderr)}")
    return r.stdout


def run_pack(repo):
    argv = [sys.executable, str(BALE), "pack", "fixture goal for the oracle",
            "--slug", "ckpt-fixture", "--include", "README.md",
            "--no-readme", "--json", "--packer", "ckpt", "--work-class", "code"]
    try:
        return subprocess.run(argv, cwd=repo, env=base_env(),
                              stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, timeout=PACK_TIMEOUT)
    except subprocess.TimeoutExpired:
        failed(f"{repo.name}: bale pack did not finish within {PACK_TIMEOUT}s",
               "a pack that waits on a terminal, or hangs, is the work's failure")
        return None


# ---------------------------------------------------------------- controls
def controls():
    """Each control calls the detector it certifies; a failed control is
    the oracle's defect (exit 2), never a verdict on the work."""
    if not BALE.is_file():
        defective(f"{BALE} is not a file: the oracle must run with cwd = the staged tree")
    c = make_repo("control-ignored", exclude_bale=True)
    if not git_ignores_bale(c):
        defective("control: a repo with .bale/ in .git/info/exclude does not read as ignored")
    c = make_repo("control-not-ignored")
    if git_ignores_bale(c):
        defective("control: a repo with nothing ignoring .bale/ reads as ignored (a global exclude leaked in?)")
    (c / "x.txt").write_text("x\n", encoding="utf-8")
    git(c, "add", "-A")
    r = git(c, "commit", "-q", "-m", SUBJECT)
    if r.returncode != 0 or commit_subjects(c)[0] != SUBJECT:
        defective("control: commit_subjects does not see a hand-made commit with the guard's subject")
    if gitignore_bytes(c) is not None:
        defective("control: gitignore_bytes reports a .gitignore that does not exist")
    (c / ".gitignore").write_bytes(b"*.log\n")
    if gitignore_bytes(c) != b"*.log\n":
        defective("control: gitignore_bytes does not read the bytes written")
    note("controls passed: fixture ignores read back, both detectors fire")


# ------------------------------------------------------------------ probes
def expect_untouched(label, repo, before_gitignore):
    """Scenarios where .bale/ is already ignored: pack succeeds, writes
    no .gitignore byte, makes no commit, leaves the tree clean."""
    r = run_pack(repo)
    if r is None:
        return
    if r.returncode != 0:
        failed(f"{label}: bale pack exited {r.returncode} in a repo that already ignores .bale/",
               tail(r.stderr) + "\n" + tail(r.stdout, 3))
        return
    after = gitignore_bytes(repo)
    if after != before_gitignore:
        failed(f"{label}: .gitignore was changed although git already ignored .bale/",
               f"before: {before_gitignore!r}\nafter:  {after!r}")
    else:
        passed(f"{label}: .gitignore untouched")
    subjects = commit_subjects(repo)
    if SUBJECT in subjects or len(subjects) != 1:
        failed(f"{label}: a commit was made although git already ignored .bale/",
               "subjects, newest first: " + " | ".join(subjects))
    else:
        passed(f"{label}: no commit made")
    dirty = porcelain(repo)
    if dirty.strip():
        failed(f"{label}: the tree is not clean after pack", dirty)
    else:
        passed(f"{label}: tree clean")


def expect_guard_fires(label, repo):
    """The unchanged path: nothing ignores .bale/, so pack appends it to
    .gitignore and auto-commits with the known subject on a clean tree."""
    r = run_pack(repo)
    if r is None:
        return
    if r.returncode != 0:
        failed(f"{label}: bale pack exited {r.returncode} in a repo where nothing ignores .bale/",
               tail(r.stderr) + "\n" + tail(r.stdout, 3))
        return
    after = gitignore_bytes(repo)
    lines = [] if after is None else [ln.strip() for ln in after.decode("utf-8", "replace").splitlines()]
    if ".bale/" not in lines and ".bale" not in lines:
        failed(f"{label}: .gitignore does not hold a .bale/ line after pack", f"after: {after!r}")
    else:
        passed(f"{label}: .bale/ appended to .gitignore")
    subjects = commit_subjects(repo)
    if not subjects or subjects[0] != SUBJECT:
        failed(f"{label}: HEAD is not the auto-commit {SUBJECT!r}",
               "subjects, newest first: " + " | ".join(subjects))
    else:
        passed(f"{label}: auto-commit at HEAD")
    dirty = porcelain(repo)
    if dirty.strip():
        failed(f"{label}: the tree is not clean after pack", dirty)
    else:
        passed(f"{label}: tree clean")


def main():
    global ROOT, HOME
    try:
        ROOT = Path(tempfile.mkdtemp(prefix="ckpt-gitignore-already-ignored-"))
    except OSError as e:
        defective(f"cannot make a temporary directory: {e}")
    HOME = ROOT / "home"
    (HOME / ".config").mkdir(parents=True)
    note(f"fixtures under {ROOT} (removed at exit); HOME for every call is {HOME}")
    try:
        controls()
        a1 = make_repo("tracked-gitignore-and-exclude", gitignore=b"*.log\n", exclude_bale=True)
        expect_untouched("A1 tracked .gitignore, .bale/ in info/exclude", a1, b"*.log\n")
        a2 = make_repo("no-gitignore-and-exclude", exclude_bale=True)
        expect_untouched("A2 no .gitignore, .bale/ in info/exclude", a2, None)
        b = make_repo("nothing-ignores-bale")
        expect_guard_fires("B nothing ignores .bale/ (unchanged path)", b)
    finally:
        shutil.rmtree(ROOT, ignore_errors=True)
    note("verdict: " + ("pass" if status == 0 else "HOLD"))
    return status


try:
    sys.exit(main())
except SystemExit:
    raise
except BaseException:
    traceback.print_exc()
    print("[ckpt] ORACLE DEFECT: unplanned exception")
    sys.stdout.flush()
    os._exit(2)
ORACLE
