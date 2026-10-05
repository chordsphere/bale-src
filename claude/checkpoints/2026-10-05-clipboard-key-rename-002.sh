#!/usr/bin/env bash
# Blind checkpoint — session clipboard-key-rename (friction-points cleanup,
# queued item 2). Authored at desk 2026-10-04-friction-points-cleanup-002
# from the request, before the work exists. Outcome probes only; every
# probe drives the tree under test (the staging copy in cwd) from a fresh
# fixture under $TMPDIR. The clipboard command each fixture configures is
# `cat > <file>`, so a copy is observable as that file's bytes.
#
# Exit codes (TARBALL.md §7.5): 0 every probe passed; 1 a probe failed,
# including a crash, hang, or unexpected exit of the code under test inside
# a fixture step; 2 the oracle's own machinery broke (a failed control, git
# or file setup).
#
# Probes:
#   new-key-copies        [clipboard] command in the project file copies
#   legacy-key-copies     [probe] clipboard_command alone still copies
#   new-wins-in-file      a file setting both copies with [clipboard] command
#   project-suppresses    the project's legacy "" suppresses a global new key
#   project-beats-global  the project's legacy value beats a global new key
#   global-new-key        a global [clipboard] command copies in a repo whose
#                         project file sets neither spelling
#   status-row            `bale status` labels the row "clipboard", not
#                         "probe clipboard", and names the command
#   status-json           `bale status --json` carries a clipboard object
#                         (command, source, problem) beside its old keys
#   status-json-problem   a triple-quoted [clipboard] command reads as a
#                         problem there, with no command
#   crafter-new-key       the probe scaffold's no-bale fallback tees into a
#                         [clipboard] command read at craft time
#   crafter-new-wins      ... and into the new spelling when both are set
set -u
export PYTHONDONTWRITEBYTECODE=1
exec python3 -B - "$PWD" <<'PY'
import json, os, re, shutil, subprocess, sys, tempfile
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
RESULTS = []
BLOCK = "clipboard probe block\n"
LABELS = {
    "new-key-copies": "new-key-copies: [clipboard] command in the project "
                      "file copies",
    "legacy-key-copies": "legacy-key-copies: [probe] clipboard_command alone "
                         "still copies",
    "new-wins-in-file": "new-wins-in-file: a file setting both spellings "
                        "copies with [clipboard] command",
    "project-suppresses": "project-suppresses: the project's legacy \"\" "
                          "suppresses a global [clipboard] command",
    "project-beats-global": "project-beats-global: the project's legacy value "
                            "beats a global [clipboard] command",
    "global-new-key": "global-new-key: a global [clipboard] command copies "
                      "when the project sets neither spelling",
    "status-row": "status-row: bale status labels the row clipboard and "
                  "names the command",
    "status-json": "status-json: bale status --json carries a clipboard "
                   "object (command, source, problem)",
    "status-json-problem": "status-json-problem: a triple-quoted [clipboard] "
                           "command reads as a problem with no command",
    "crafter-new-key": "crafter-new-key: the probe scaffold's fallback tees "
                       "into a [clipboard] command read at craft time",
    "crafter-new-wins": "crafter-new-wins: the probe scaffold's fallback "
                        "prefers [clipboard] command over the legacy key",
}
OLD_STATUS_KEYS = {"applied", "config", "integration_lock", "outbox",
                   "outcome", "repo", "scopes", "session", "sessions", "sid",
                   "staging", "version"}


class Broken(Exception):
    """The oracle's own machinery failed: exit 2."""


class UnderTest(Exception):
    """The code under test crashed, hung, or exited unexpectedly: a FAIL."""


def record(key, ok, detail=""):
    RESULTS.append((key, ok))
    print(f"[{'PASS' if ok else 'FAIL'}] {LABELS[key]}")
    if not ok and detail:
        for ln in str(detail).splitlines()[:12]:
            print(f"      detail: {ln}")


def setup_run(cmd, cwd, env, stdin=None):
    r = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True,
                       timeout=60, input=stdin)
    if r.returncode != 0:
        raise Broken(f"setup {cmd[:3]} exited {r.returncode}: {r.stderr[-400:]}")
    return r


class Fixture:
    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="ckpt-clipkey-"))
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

    def out(self, name):
        return self.root / f"{name}.out"

    def cmd(self, name):
        return f"cat > {self.out(name)}"

    def project_toml(self, text):
        (self.repo / "bale.toml").write_text(text, encoding="utf-8")
        setup_run(["git", "add", "-A"], self.repo, self.env)
        setup_run(["git", "commit", "-qm", "config"], self.repo, self.env)

    def global_toml(self, text):
        user = self.install / "user"
        user.mkdir(exist_ok=True)
        (user / "bale.toml").write_text(text, encoding="utf-8")

    def bale(self, *args, stdin=None):
        try:
            return subprocess.run(
                [sys.executable, "-B", str(self.install / "bin" / "bale"), *args],
                cwd=self.repo, env=self.env, capture_output=True, text=True,
                input=stdin if stdin is not None else "", timeout=90)
        except subprocess.TimeoutExpired:
            raise UnderTest(f"bale {' '.join(args)} hung")

    def clipboard(self):
        r = self.bale("clipboard", stdin=BLOCK)
        if r.returncode not in (0, 1):
            raise UnderTest(f"bale clipboard exited {r.returncode}: "
                            f"{r.stderr.strip()[-300:]}")
        return r

    def copied(self, name):
        p = self.out(name)
        return p.read_text(encoding="utf-8") if p.exists() else None

    def status_json(self):
        r = self.bale("status", "--json")
        if r.returncode != 0:
            raise UnderTest(f"bale status --json exited {r.returncode}: "
                            f"{r.stderr.strip()[-300:]}")
        try:
            return json.loads(r.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError) as e:
            raise UnderTest(f"bale status --json is not one JSON line: {e}")

    def craft_probe(self):
        r = subprocess.run(
            [sys.executable, "-B", str(TREE / "tools" / "craft_response.py"),
             "--probe", "ckpt"], cwd=self.repo, env=self.env,
            capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise UnderTest(f"craft_response.py --probe exited {r.returncode}: "
                            f"{r.stderr.strip()[-300:]}")
        return r.stdout

    def cleanup(self):
        shutil.rmtree(self.root, ignore_errors=True)


def scenario(fn):
    fx = Fixture()
    try:
        fn(fx)
    finally:
        fx.cleanup()


def p_new_key(fx):
    fx.project_toml(f'[clipboard]\ncommand = "{fx.cmd("new")}"\n')
    r = fx.clipboard()
    got = fx.copied("new")
    record("new-key-copies", r.returncode == 0 and got == BLOCK,
           f"exit {r.returncode}; copied {got!r}; stderr {r.stderr.strip()[-200:]!r}")


def p_legacy_key(fx):
    fx.project_toml(f'[probe]\nclipboard_command = "{fx.cmd("old")}"\n')
    r = fx.clipboard()
    got = fx.copied("old")
    record("legacy-key-copies", r.returncode == 0 and got == BLOCK,
           f"exit {r.returncode}; copied {got!r}")


def p_both_in_file(fx):
    fx.project_toml(f'[clipboard]\ncommand = "{fx.cmd("new")}"\n\n'
                    f'[probe]\nclipboard_command = "{fx.cmd("old")}"\n')
    r = fx.clipboard()
    new, old = fx.copied("new"), fx.copied("old")
    record("new-wins-in-file", r.returncode == 0 and new == BLOCK and old is None,
           f"exit {r.returncode}; new {new!r}; legacy {old!r}")


def p_project_suppresses(fx):
    fx.global_toml(f'[clipboard]\ncommand = "{fx.cmd("global")}"\n')
    fx.project_toml('[probe]\nclipboard_command = ""\n')
    r = fx.clipboard()
    got = fx.copied("global")
    record("project-suppresses", r.returncode == 1 and got is None,
           f"exit {r.returncode}; global copied {got!r}")


def p_project_beats_global(fx):
    fx.global_toml(f'[clipboard]\ncommand = "{fx.cmd("global")}"\n')
    fx.project_toml(f'[probe]\nclipboard_command = "{fx.cmd("project")}"\n')
    r = fx.clipboard()
    g, p = fx.copied("global"), fx.copied("project")
    record("project-beats-global", r.returncode == 0 and p == BLOCK and g is None,
           f"exit {r.returncode}; project {p!r}; global {g!r}")


def p_global_new(fx):
    fx.global_toml(f'[clipboard]\ncommand = "{fx.cmd("global")}"\n')
    r = fx.clipboard()
    g = fx.copied("global")
    record("global-new-key", r.returncode == 0 and g == BLOCK,
           f"exit {r.returncode}; copied {g!r}; stderr {r.stderr.strip()[-200:]!r}")


def p_status(fx):
    command = fx.cmd("new")
    fx.project_toml(f'[clipboard]\ncommand = "{command}"\n')
    r = fx.bale("status")
    if r.returncode != 0:
        raise UnderTest(f"bale status exited {r.returncode}")
    lines = r.stdout.splitlines()
    row = [i for i, ln in enumerate(lines) if re.match(r"^\s*clipboard:\s", ln)]
    old = [ln for ln in lines if re.match(r"^\s*probe clipboard:", ln)]
    named = bool(row) and str(fx.out("new")) in " ".join(
        ln.strip() for ln in lines[row[0]:row[0] + 3])
    record("status-row", bool(row) and not old and named,
           f"clipboard row: {bool(row)}; probe clipboard row: {bool(old)}; "
           f"names the command: {named}")
    data = fx.status_json()
    clip = data.get("clipboard")
    ok = (isinstance(clip, dict) and clip.get("command") == command
          and clip.get("source") == "project" and clip.get("problem") is None
          and OLD_STATUS_KEYS <= set(data))
    record("status-json", ok, f"clipboard: {clip!r}; "
           f"missing old keys: {sorted(OLD_STATUS_KEYS - set(data))}")


def p_status_problem(fx):
    fx.project_toml('[clipboard]\ncommand = """cat"""\n')
    data = fx.status_json()
    clip = data.get("clipboard")
    ok = (isinstance(clip, dict) and clip.get("command") is None
          and isinstance(clip.get("problem"), str) and clip["problem"].strip())
    record("status-json-problem", ok, f"clipboard: {clip!r}")


def scaffold_fallback(text):
    """The body of clip_fallback() in an emitted probe scaffold."""
    m = re.search(r"^clip_fallback\(\) \{\n(.*?)^\}", text, re.S | re.M)
    if not m:
        raise UnderTest("the emitted probe scaffold has no clip_fallback()")
    return m.group(1)


def p_crafter_new(fx):
    fx.project_toml(f'[clipboard]\ncommand = "{fx.cmd("new")}"\n')
    body = scaffold_fallback(fx.craft_probe())
    record("crafter-new-key", str(fx.out("new")) in body,
           f"clip_fallback body: {body.strip()[:160]!r}")


def p_crafter_both(fx):
    fx.project_toml(f'[clipboard]\ncommand = "{fx.cmd("new")}"\n\n'
                    f'[probe]\nclipboard_command = "{fx.cmd("old")}"\n')
    body = scaffold_fallback(fx.craft_probe())
    record("crafter-new-wins",
           str(fx.out("new")) in body and str(fx.out("old")) not in body,
           f"clip_fallback body: {body.strip()[:160]!r}")


def controls():
    if not shutil.which("git"):
        raise Broken("git is not on PATH")
    probe = Path(tempfile.mkdtemp(prefix="ckpt-clipkey-ctl-"))
    try:
        target = probe / "c.out"
        subprocess.run(["sh", "-c", f"cat > {target}"], input=BLOCK, text=True,
                       timeout=10, check=True)
        if target.read_text(encoding="utf-8") != BLOCK:
            raise Broken("the cat > file copy detector does not round-trip")
    except (OSError, subprocess.SubprocessError) as e:
        raise Broken(f"control failed: {e}")
    finally:
        shutil.rmtree(probe, ignore_errors=True)
    sample = "x\nclip_fallback() {\n  tee a\n}\nmore\n"
    if scaffold_fallback(sample).strip() != "tee a":
        raise Broken("clip_fallback locator control failed")


def main():
    plan = [
        (["new-key-copies"], p_new_key),
        (["legacy-key-copies"], p_legacy_key),
        (["new-wins-in-file"], p_both_in_file),
        (["project-suppresses"], p_project_suppresses),
        (["project-beats-global"], p_project_beats_global),
        (["global-new-key"], p_global_new),
        (["status-row", "status-json"], p_status),
        (["status-json-problem"], p_status_problem),
        (["crafter-new-key"], p_crafter_new),
        (["crafter-new-wins"], p_crafter_both),
    ]
    try:
        controls()
        for keys, fn in plan:
            try:
                scenario(fn)
            except UnderTest as e:
                decided = {k for k, _ in RESULTS}
                for key in keys:
                    if key not in decided:
                        record(key, False, str(e)[:900])
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
