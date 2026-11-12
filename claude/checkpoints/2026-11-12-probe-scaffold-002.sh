#!/usr/bin/env bash
# Blind checkpoint for bale-src session probe-scaffold (v1).
#
# Authored blind, from the request's brief, before any implementation
# existed, by the planner sitting 2026-11-11-bale-src-slips-plan-sitting-003.
# The worker never reads, edits or declares this file (TARBALL.md 7).
#
# It grades outcomes only, in the tree it runs in (bale's staging root, the
# landed tree), driving this tree's own crafter and bin/bale in throwaway
# directories under /tmp:
#   - craft_response.py --probe SLUG --run-line LINE puts "# LINE" in the
#     header after the Read-only line; without it the header is as before;
#     a LINE holding a newline is refused; TARBALL.md 4.2 names the option;
#   - the scaffold's secrets note names remote URLs and git remote -v, and
#     its git remote -v snippet, run as written, prints remotes masked;
#     TARBALL.md 4.3 names git remote -v;
#   - craft_response.py --help says a successor's bundle needs a new stem;
#   - with no bale on PATH, a crafted probe's closing copy is byte for byte
#     what bale clipboard copies of the same block, through clip.exe and
#     through any other command, and its notice says it masked;
#   - the release is 0.4.60.
#
# Exit codes (TARBALL.md 7.5): 0 every probe passed; 1 a probe failed (the
# work's failure, a crash of the code under test included); 2 the oracle's
# own machinery broke (a control, git, file setup, an unplanned exception).
# Reads nothing but the tree it grades: no session id, no manifest, no path
# of its own. Writes only under one temporary directory it makes and removes.
set -u
export PYTHONDONTWRITEBYTECODE=1
exec python3 -I -B - <<'ORACLE'
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path


class OracleError(Exception):
    """The oracle's own machinery failed: exit 2, never a verdict."""


def _excepthook(kind, value, tb):
    print("[oracle] unexpected exception; this is the oracle's fault, "
          "not the work's (exit 2):")
    traceback.print_exception(kind, value, tb, file=sys.stdout)
    sys.stdout.flush()
    work = globals().get("WORK")
    if work is not None:
        shutil.rmtree(work, ignore_errors=True)
    os._exit(2)


sys.excepthook = _excepthook

TREE = Path.cwd()
TIMEOUT = 300
WORK = Path(tempfile.mkdtemp(prefix="bale-oracle-scaf-"))

RUN_LINE = "office: probe 43 --sid 2026-01-01-oracle-fixture-001"
SUCCESSOR_SENTENCE = "A successor's bundle takes a stem no earlier bundle of its slug had."
PW = "S3cretPw-77"
TOKEN = "ghp_A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8"
REMOTES = (("origin", "https://alice:" + PW + "@example.com/r.git"),
           ("tok", "https://" + TOKEN + "@github.com/o/r.git"),
           ("plain", "https://example.org/plain.git"))
PROBE_BODY = ("probe() {\n"
              "  echo \"--- section: 1 fixture ---\"\n"
              "  echo \"remote https://alice:" + PW + "@example.com/r.git\"\n"
              "  echo \"token " + TOKEN + "\"\n"
              "  echo \"clean https://example.org/plain.git caf\\u00e9 \\u2014 done\"\n"
              "}\n")


# --- detectors (each one is exercised by a control before any probe) ---

def after_read_only(text):
    """(the line after the header's '# Read-only:' line, the one after that),
    or None when there is no Read-only line."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("# Read-only:"):
            nxt = lines[i + 1] if i + 1 < len(lines) else ""
            nxt2 = lines[i + 2] if i + 2 < len(lines) else ""
            return nxt, nxt2
    return None


def snippet(text):
    """The first comment line that, its '#' and spaces stripped, starts
    'git remote -v |'; the command, or None."""
    for ln in text.splitlines():
        m = re.match(r"^\s*#+\s*(git remote -v \|.*\S)\s*$", ln)
        if m:
            return m.group(1)
    return None


def fold(text):
    return " ".join(text.split())


def section(doc, number):
    """The '### <number> ' section's text, heading to the next ## or ### heading."""
    lines = doc.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith(f"### {number} "):
            out = [ln]
            for nxt in lines[i + 1:]:
                if nxt.startswith("### ") or nxt.startswith("## "):
                    break
                out.append(nxt)
            return "\n".join(out)
    return None


def says_masked(text):
    """True when a '[clipboard]' or '[bale] clipboard:' line, its backticked
    command left out, speaks of masking."""
    for ln in text.splitlines():
        if ln.startswith("[clipboard]") or ln.startswith("[bale] clipboard:"):
            if "mask" in re.sub(r"`[^`]*`", "", ln).lower():
                return True
    return False


def swap_probe_body(scaffold, body):
    """The scaffold with its probe() function (the line 'probe() {' through
    the first line that is exactly '}') replaced by body; None if absent."""
    lines = scaffold.splitlines(keepends=True)
    try:
        start = next(i for i, ln in enumerate(lines) if ln.rstrip("\n") == "probe() {")
        end = next(j for j in range(start + 1, len(lines)) if lines[j].rstrip("\n") == "}")
    except StopIteration:
        return None
    return "".join(lines[:start]) + body + "".join(lines[end + 1:])


class Capture:
    """A directory the stand-in clipboard writes one file per copy into."""

    def __init__(self, where):
        self.dir = where / "clipboard-copies"
        self.dir.mkdir(parents=True)
        self.seen = 0

    def new(self):
        files = sorted(self.dir.iterdir())
        fresh = [f.read_bytes() for f in files[self.seen:]]
        self.seen = len(files)
        return fresh


# --- controls: prove every detector on synthetic input; a miss exits 2 ---

def controls():
    hdr = "#!/usr/bin/env bash\n# PROBE x: a\n# Why: b\n# Read-only: c\n# office: d\n# Bound: e\n"
    if after_read_only(hdr) != ("# office: d", "# Bound: e"):
        raise OracleError(f"control: after_read_only read {after_read_only(hdr)!r}")
    if after_read_only("# PROBE x\n# Bound: e\n") is not None:
        raise OracleError("control: after_read_only invented a Read-only line")
    sn = "x\n#   remote URLs can carry a token:\n#   git remote -v | sed -E 's/a/b/'\n"
    if snippet(sn) != "git remote -v | sed -E 's/a/b/'":
        raise OracleError(f"control: snippet read {snippet(sn)!r}")
    if snippet("  git remote -v | cat\n# git remote -v\n") is not None:
        raise OracleError("control: snippet took an uncommented or pipeless line")
    if fold("a  b\n c") != "a b c":
        raise OracleError("control: fold misread")
    doc = "## 4\n### 4.2 A\nhas --run-line\n### 4.3 B\nhas git remote -v\n## 5\nlater\n"
    if section(doc, "4.2") != "### 4.2 A\nhas --run-line" or "later" in (section(doc, "4.3") or "later"):
        raise OracleError("control: section misread")
    if section(doc, "4.4") is not None:
        raise OracleError("control: section found a missing heading")
    if not says_masked("[clipboard] probe output copied; masked 1 URL password\n"):
        raise OracleError("control: says_masked missed a masking line")
    if says_masked("[clipboard] copied with `sh /tmp/mask/keep.sh`\nmasked elsewhere\n"):
        raise OracleError("control: says_masked read a command path or a non-notice line")
    sc = "head\nprobe() {\n  old\n  inner() {\n  }\n}\ntail\n"
    if swap_probe_body(sc, "probe() {\n  new\n}\n") != "head\nprobe() {\n  new\n}\ntail\n":
        raise OracleError(f"control: swap_probe_body read {swap_probe_body(sc, 'X')!r}")
    if swap_probe_body("no function\n", "x") is not None:
        raise OracleError("control: swap_probe_body found a missing function")
    where = WORK / "control"
    cap = Capture(where)
    (cap.dir / "copy-000").write_bytes(b"a")
    if cap.new() != [b"a"] or cap.new() != []:
        raise OracleError("control: Capture.new misread")
    shutil.rmtree(where)


# --- machinery (shared with the session's sibling oracles) ---

def run(cmd, *, cwd, env, check=False, stdin_bytes=None):
    try:
        r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True,
                           timeout=TIMEOUT,
                           input=stdin_bytes if stdin_bytes is not None else b"")
    except (OSError, subprocess.SubprocessError) as e:
        if check:
            raise OracleError(f"could not run {cmd[:3]}: {e}")
        return 125, "", f"could not run: {e}"
    out = r.stdout.decode("utf-8", "replace")
    err = r.stderr.decode("utf-8", "replace")
    if check and r.returncode != 0:
        raise OracleError(f"setup command {cmd} exited {r.returncode}: {err[-400:]}")
    return r.returncode, out, err


def base_env(home):
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home),
            "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "EDITOR": "/bin/true",
            "VISUAL": "/bin/true", "PYTHONDONTWRITEBYTECODE": "1"}


def make_home(where):
    home = where / "home"
    home.mkdir(parents=True)
    (home / ".gitconfig").write_text(
        "[user]\n\tname = Oracle Fixture\n\temail = oracle@example.invalid\n"
        "[init]\n\tdefaultBranch = main\n", encoding="utf-8")
    return home


def make_install(where):
    install = where / "install"
    install.mkdir()
    for tree in ("bin", "docs", "schemas", "tools"):
        src = TREE / tree
        if not src.is_dir():
            raise OracleError(f"the graded tree has no {tree}/ to copy")
        shutil.copytree(src, install / tree, ignore=shutil.ignore_patterns("__pycache__"))
    return install



FAKE_CLIP = """#!/bin/sh
d='{dir}'
n=$(ls "$d" | wc -l)
cat > "$d/copy-$(printf %03d "$n")"
"""

NO_BALE_TOOLS = ("bash", "sh", "env", "timeout", "wc", "tr", "cat", "ls", "head",
                 "sed", "grep", "cut", "iconv", "sleep", "mkdir", "rm", "mktemp")


def no_bale_path(where, winbin):
    """A PATH of symlinks to the tools a probe uses, with python3 as this
    interpreter, and never a bale."""
    tools = where / "no-bale-bin"
    tools.mkdir()
    for name in NO_BALE_TOOLS:
        found = shutil.which(name)
        if found:
            (tools / name).symlink_to(found)
    (tools / "python3").symlink_to(sys.executable)
    path = f"{winbin}:{tools}"
    if shutil.which("bale", path=path) is not None:
        raise OracleError("control: the no-bale PATH still finds a bale")
    if shutil.which("bash", path=path) is None:
        raise OracleError("control: the no-bale PATH finds no bash")
    return path


def setup(name, *, clip):
    """A scratch install, home, and a git repo whose bale.toml names a
    stand-in clipboard command; clip is 'plain' or 'clip.exe'."""
    where = WORK / name
    where.mkdir()
    home = make_home(where)
    install = make_install(where)
    env = base_env(home)
    env["BALE_INSTALL"] = str(where / "bale-install-sandbox")
    cap = Capture(where)
    script = FAKE_CLIP.format(dir=cap.dir)
    winbin = where / "winbin"
    winbin.mkdir()
    if clip == "plain":
        fake = where / "keepclip.sh"
        fake.write_text(script, encoding="utf-8")
        command = f"sh {fake}"
    else:
        fake = winbin / "clip.exe"
        fake.write_text(script, encoding="utf-8")
        fake.chmod(0o755)
        command = "clip.exe"
    env["PATH"] = f"{winbin}:{env['PATH']}"
    repo = where / "project"
    repo.mkdir()
    run(["git", "init", "-q", "-b", "main"], cwd=repo, env=env, check=True)
    (repo / "bale.toml").write_text(
        "[sandbox]\nenabled = false\n\n[clipboard]\ncommand = \"" + command + "\"\n",
        encoding="utf-8")
    run(["git", "add", "-A"], cwd=repo, env=env, check=True)
    run(["git", "commit", "-q", "-m", "init"], cwd=repo, env=env, check=True)
    return {"where": where, "env": env, "repo": repo, "cap": cap, "winbin": winbin,
            "bale": [sys.executable, "-B", str(install / "bin" / "bale")],
            "crafter": [sys.executable, "-I", "-B", str(install / "tools" / "craft_response.py")]}


def craft(s, *extra):
    return run(s["crafter"] + ["--probe", "oracle-fixture", *extra], cwd=s["repo"], env=s["env"])


results = []


def probe(label, ok, detail=""):
    results.append((label, bool(ok), detail))


def fallback_matches(s, label_copy, label_notice=None):
    """Craft a probe in s's repo, run it with no bale on PATH, and compare its
    closing copy with bale clipboard's copy of the same printed block."""
    rc, scaffold, err = craft(s)
    if rc != 0:
        probe(label_copy, False, f"the crafter's --probe exited {rc}: {err[-300:]!r}")
        if label_notice:
            probe(label_notice, False, "no scaffold")
        return
    filled = swap_probe_body(scaffold, PROBE_BODY)
    if filled is None:
        probe(label_copy, False, "the scaffold has no 'probe() {' ... '}' function to fill")
        if label_notice:
            probe(label_notice, False, "no probe() function")
        return
    pfile = s["where"] / "probe.sh"
    pfile.write_text(filled, encoding="utf-8")
    env = dict(s["env"])
    env["PATH"] = no_bale_path(s["where"], s["winbin"])
    s["cap"].new()
    prc, block, perr = run(["bash", str(pfile)], cwd=s["repo"], env=env)
    copies = s["cap"].new()
    if prc != 0 or "=== PROBE BEGIN oracle-fixture ===" not in block:
        probe(label_copy, False, f"the crafted probe exited {prc}: {(perr or block)[-300:]!r}")
        if label_notice:
            probe(label_notice, False, "the crafted probe did not run")
        return
    rrc, rout, rerr = run(s["bale"] + ["clipboard", "--block", "probe block"], cwd=s["repo"],
                          env=s["env"], stdin_bytes=block.encode("utf-8"))
    ref = s["cap"].new()
    if rrc != 0 or not ref:
        probe(label_copy, False, f"bale clipboard's reference copy failed (exit {rrc}): {rerr[-300:]!r}")
    else:
        probe(label_copy, bool(copies) and copies[-1] == ref[-1],
              f"the fallback made {len(copies)} copies; the last "
              f"{'starts ' + copies[-1][:16].hex() if copies else 'is absent'}, "
              f"bale clipboard's starts {ref[-1][:16].hex()}")
    if label_notice:
        probe(label_notice, says_masked(perr), f"the fallback's lines: {[l for l in perr.splitlines() if 'clipboard' in l][:3]!r}")


def main():
    controls()

    s = setup("craft", clip="plain")
    # 1. The run line.
    rc, out, err = craft(s, "--run-line", RUN_LINE)
    got = after_read_only(out) if rc == 0 else None
    run_line_works = got is not None and got[0] == "# " + RUN_LINE and got[1].startswith("# Bound:")
    probe("--run-line puts its line in the header after the Read-only line",
          run_line_works, f"crafter exited {rc}; the two lines after Read-only: {got!r}")
    rc, out, err = craft(s)
    got = after_read_only(out) if rc == 0 else None
    probe("without --run-line the Bound line follows the Read-only line",
          got is not None and got[0].startswith("# Bound:"),
          f"crafter exited {rc}; the line after Read-only: {got!r}")
    scaffold = out if rc == 0 else ""
    rc2, out2, err2 = craft(s, "--run-line", "office: probe 43\n# injected")
    probe("a --run-line holding a newline is refused",
          run_line_works and rc2 != 0 and out2 == "",
          "--run-line itself does not work" if not run_line_works
          else f"crafter exited {rc2} with {len(out2)} bytes on stdout")

    # 2. The secrets note and its snippet.
    low = scaffold.lower()
    probe("the scaffold's secrets note names remote URLs and git remote -v",
          "remote url" in low and "git remote -v" in scaffold,
          "the scaffold does not name both 'remote URL' and 'git remote -v'")
    cmd = snippet(scaffold)
    label = "the scaffold's git remote -v snippet prints remotes with their credentials masked"
    if cmd is None:
        probe(label, False, "no comment line in the scaffold starts 'git remote -v |'")
    else:
        repo = s["where"] / "remotes"
        repo.mkdir()
        run(["git", "init", "-q", "-b", "main"], cwd=repo, env=s["env"], check=True)
        for name, url in REMOTES:
            run(["git", "remote", "add", name, url], cwd=repo, env=s["env"], check=True)
        src, sout, serr = run(["bash", "-c", cmd], cwd=repo, env=s["env"])
        leaked = [x for x in (PW, TOKEN[4:]) if x in sout]
        kept = all(k in sout for k in ("origin", "alice", "example.com/r.git",
                                       "github.com/o/r.git", "example.org/plain.git"))
        probe(label, src == 0 and not leaked and kept,
              f"the snippet exited {src}; leaked {leaked!r}; output {sout[:240]!r}")

    # 3. The docs.
    doc_path = TREE / "docs" / "TARBALL.md"
    doc = doc_path.read_text(encoding="utf-8") if doc_path.is_file() else ""
    s42, s43 = section(doc, "4.2"), section(doc, "4.3")
    probe("docs/TARBALL.md 4.2 names --run-line", s42 is not None and "--run-line" in s42,
          "no 4.2 section" if s42 is None else "4.2 does not name --run-line")
    probe("docs/TARBALL.md 4.3 names git remote -v", s43 is not None and "git remote -v" in s43,
          "no 4.3 section" if s43 is None else "4.3 does not name git remote -v")

    # 4. The bundle help.
    hrc, hout, herr = run(s["crafter"] + ["--help"], cwd=s["repo"], env=s["env"])
    probe("craft_response.py --help says a successor's bundle needs a new stem",
          hrc == 0 and SUCCESSOR_SENTENCE in fold(hout),
          f"--help exited {hrc}; the sentence is {'present' if SUCCESSOR_SENTENCE in fold(hout) else 'absent'}")

    # 5. The fallback copy, with no bale on PATH.
    fallback_matches(setup("fallback-clip", clip="clip.exe"),
                     "with no bale on PATH, a probe's copy to clip.exe is bale clipboard's, byte for byte",
                     "the fallback's clipboard line says it masked")
    fallback_matches(setup("fallback-plain", clip="plain"),
                     "with no bale on PATH, a probe's copy to another command is bale clipboard's, byte for byte")

    ver_file = TREE / "bin" / "VERSION"
    ver = ver_file.read_text(encoding="utf-8").strip() if ver_file.is_file() else None
    rec_file = TREE / "claude" / "changelog" / "0.4.60.json"
    rec_ver = None
    if rec_file.is_file():
        try:
            rec_ver = json.loads(rec_file.read_text(encoding="utf-8")).get("version")
        except (ValueError, AttributeError):
            rec_ver = "unreadable"
    probe("release 0.4.60: bin/VERSION and claude/changelog/0.4.60.json",
          ver == "0.4.60" and rec_ver == "0.4.60",
          f"bin/VERSION {ver!r}, changelog record version {rec_ver!r}")


try:
    main()
except OracleError as e:
    shutil.rmtree(WORK, ignore_errors=True)
    print(f"[oracle] the oracle's own machinery failed (exit 2): {e}")
    sys.stdout.flush()
    os._exit(2)
shutil.rmtree(WORK, ignore_errors=True)

failed = 0
for label, ok, detail in results:
    if ok:
        print(f"[PASS] {label}")
    else:
        failed += 1
        print(f"[FAIL] {label}" + (f": {detail}" if detail else ""))
print(f"[oracle] {len(results) - failed} of {len(results)} probes passed")
sys.exit(1 if failed else 0)
ORACLE
