#!/usr/bin/env bash
# Blind checkpoint for bale-src session clipboard (v1).
#
# Authored blind, from the request's brief, before any implementation
# existed, by the planner sitting 2026-11-11-bale-src-slips-plan-sitting-003.
# The worker never reads, edits or declares this file (TARBALL.md 7).
#
# It grades outcomes only, in the tree it runs in (bale's staging root, the
# landed tree), driving this tree's own bin/bale and crafter in throwaway
# repos under /tmp, with stand-in clipboard commands that keep the bytes
# they are fed:
#   - a clarification's landing prints the planner-facing exchange block,
#     the same bytes bale relay prints, and copies it last, unmasked, with a
#     notice naming it;
#   - bale clipboard masks a credential in a URL, leaves every other byte
#     alone, and says so on its notice line;
#   - a clip.exe command is fed UTF-16LE with no byte-order mark, by name or
#     by path, from bale clipboard and from bale relay alike; any other
#     command is still fed UTF-8;
#   - the release is 0.4.59.
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
import tarfile
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
WORK = Path(tempfile.mkdtemp(prefix="bale-oracle-clip-"))
NOTICE = "[bale] clipboard: "

# Fixture secrets and text. Nothing a word probe reads is authored here
# except what the probe compares byte for byte.
SECRET_A = "s3cr3t-Token"
SECRET_B = "p%40ss-W0rd"
CLARIFY_CONTEXT = ("fixture context: the mirror at https://alice:" + SECRET_A +
                   "@example.com/repo, caf\u00e9 \u2014 noted")
PROBE_TEXT = ("=== PROBE BEGIN fixture ===\n"
              "remote: https://alice:" + SECRET_A + "@example.com/x\n"
              "db: postgres://bob:" + SECRET_B + "@db.internal:5432/app\n"
              "clean: https://example.org/a?b=c\n"
              "caf\u00e9 \u2014 \u00b7 done\n"
              "=== PROBE END fixture ===\n")
CLEAN_TEXT = "=== PROBE BEGIN clean ===\ncaf\u00e9 \u2014 \u00b7 https://example.org/a\n=== PROBE END clean ===\n"


# --- detectors (each one is exercised by a control before any probe) ---

def exchange_block(text, sid):
    """The exchange block for sid, BEGIN line through END line, each line
    ending in a newline; None when there is none."""
    lines = text.splitlines()
    begin = f"BALE EXCHANGE BEGIN {sid}"
    for i, ln in enumerate(lines):
        if ln.strip() == begin:
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == "BALE EXCHANGE END":
                    return "\n".join(lines[i:j + 1]) + "\n"
            return None
    return None


def notices(text):
    """The clipboard notice lines, as printed."""
    return [ln for ln in text.splitlines() if ln.startswith(NOTICE)]


def says_masked(lines):
    """True when a notice, its backticked command left out, speaks of masking."""
    return any("mask" in re.sub(r"`[^`]*`", "", n).lower() for n in lines)


def masked_as(captured, original, secrets_by_prefix):
    """True when `captured` is `original` with each secret (found after its
    prefix and before '@') replaced by a non-empty mask holding no part of
    any secret, and every other byte unchanged."""
    expected = original
    for prefix, secret, host in secrets_by_prefix:
        m = re.search(re.escape(prefix) + r"([^@\s]*)@" + re.escape(host), captured)
        if not m:
            return False
        mask = m.group(1)
        if not mask or any(frag in mask for frag in ("s3cr3t", "Token", "W0rd", "p%40ss")):
            return False
        expected = expected.replace(prefix + secret + "@" + host, prefix + mask + "@" + host)
    return captured == expected


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
    text = ("x\nBALE EXCHANGE BEGIN S\n# h\n{}\n# sha256 a\nBALE EXCHANGE END\nafter\n"
            "BALE EXCHANGE BEGIN T\nBALE EXCHANGE END\n")
    if exchange_block(text, "S") != "BALE EXCHANGE BEGIN S\n# h\n{}\n# sha256 a\nBALE EXCHANGE END\n":
        raise OracleError(f"control: exchange_block read {exchange_block(text, 'S')!r}")
    if exchange_block("BALE EXCHANGE BEGIN S\nno end\n", "S") is not None:
        raise OracleError("control: exchange_block took an unterminated block")
    if exchange_block(text, "U") is not None:
        raise OracleError("control: exchange_block found a block for another sid")
    if notices("[bale] clipboard: copied x\n[bale] relay: y\n") != ["[bale] clipboard: copied x"]:
        raise OracleError("control: notices misread")
    if says_masked(["[bale] clipboard: copied the probe block (`sh /tmp/mask/keep.sh`, project bale.toml)"]):
        raise OracleError("control: says_masked read the command's path")
    if not says_masked(["[bale] clipboard: copied the probe block (`clip.exe`); masked 2 credentials"]):
        raise OracleError("control: says_masked missed a masking notice")
    sec = [("https://alice:", SECRET_A, "example.com/x"),
           ("postgres://bob:", SECRET_B, "db.internal:5432/app")]
    good = PROBE_TEXT.replace(SECRET_A, "***").replace(SECRET_B, "[masked]")
    if not masked_as(good, PROBE_TEXT, sec):
        raise OracleError("control: masked_as refused a correct masking")
    if masked_as(PROBE_TEXT, PROBE_TEXT, sec):
        raise OracleError("control: masked_as took an unmasked copy")
    if masked_as(good.replace("example.org", "example.net"), PROBE_TEXT, sec):
        raise OracleError("control: masked_as took a copy that changed another byte")
    if masked_as(PROBE_TEXT.replace(SECRET_A, "s3cr3t-***").replace(SECRET_B, "x"), PROBE_TEXT, sec):
        raise OracleError("control: masked_as took a mask that keeps part of the secret")
    probe_dir = WORK / "control"
    cap = Capture(probe_dir)
    (cap.dir / "copy-000").write_bytes(b"a")
    if cap.new() != [b"a"] or cap.new() != []:
        raise OracleError("control: Capture.new misread")
    (cap.dir / "copy-001").write_bytes(b"b")
    if cap.new() != [b"b"]:
        raise OracleError("control: Capture.new missed a later copy")
    shutil.rmtree(probe_dir)


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


def fresh_session(name, *, clip):
    """A scratch install and repo with one packed session, its clipboard
    command a stand-in that keeps each copy. clip: 'plain' (a command bale
    cannot take for clip.exe), 'clip.exe' (a command named clip.exe on PATH),
    or 'clip.exe-path' (the same, by absolute path)."""
    where = WORK / name
    where.mkdir()
    home = make_home(where)
    install = make_install(where)
    env = base_env(home)
    env["BALE_INSTALL"] = str(where / "bale-install-sandbox")
    cap = Capture(where)
    script = FAKE_CLIP.format(dir=cap.dir)
    if clip == "plain":
        fake = where / "keepclip.sh"
        fake.write_text(script, encoding="utf-8")
        command = f"sh {fake}"
    else:
        winbin = where / "winbin"
        winbin.mkdir()
        fake = winbin / "clip.exe"
        fake.write_text(script, encoding="utf-8")
        fake.chmod(0o755)
        env["PATH"] = f"{winbin}:{env['PATH']}"
        command = "clip.exe" if clip == "clip.exe" else str(fake)
    repo = where / "project"
    repo.mkdir()
    run(["git", "init", "-q", "-b", "main"], cwd=repo, env=env, check=True)
    (repo / "hello.txt").write_text("hello\n", encoding="utf-8")
    # Unconfined by the scratch repo's own config: its confinement is not
    # what is graded, and a nested-sandbox fault must never read as a verdict.
    (repo / "bale.toml").write_text(
        "[sandbox]\nenabled = false\n\n[clipboard]\ncommand = \"" + command + "\"\n",
        encoding="utf-8")
    run(["git", "add", "-A"], cwd=repo, env=env, check=True)
    run(["git", "commit", "-q", "-m", "init"], cwd=repo, env=env, check=True)
    bale = [sys.executable, "-B", str(install / "bin" / "bale")]
    crafter = [sys.executable, "-I", "-B", str(install / "tools" / "craft_response.py")]
    s = {"where": where, "env": env, "repo": repo, "bale": bale, "crafter": crafter,
         "cap": cap, "sid": None, "why": ""}
    rc, out, err = run(bale + ["pack", "oracle fixture goal", "--slug", "oracle-fixture",
                               "--include", "hello.txt", "--no-readme", "--json"],
                       cwd=repo, env=env)
    cap.new()  # the pack's own copies are not graded
    if rc != 0:
        s["why"] = f"the scratch pack exited {rc}: {(err or out)[-300:]!r}"
        return s
    for ln in reversed(out.strip().splitlines()):
        try:
            s["sid"] = json.loads(ln).get("sid")
            break
        except (ValueError, AttributeError):
            continue
    if not s["sid"]:
        s["why"] = "the scratch pack's --json report named no sid"
    return s


def clarification_tarball(s):
    """A filled one-question clarification response, scaffolded by this
    tree's crafter, tarred; (path, why)."""
    rdir = s["where"] / f"response-{s['sid'][-3:]}"
    rdir.mkdir()
    rc, out, err = run(s["crafter"] + [str(rdir), "--kind", "clarification",
                                       "--sid", s["sid"], "--write"],
                       cwd=s["where"], env=s["env"])
    if rc != 0:
        return None, f"the crafter's clarification scaffold exited {rc}: {err[-300:]!r}"
    mpath = rdir / "manifest.json"
    try:
        manifest = json.loads(mpath.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return None, f"the crafter's clarification manifest did not read: {e}"
    manifest["summary"] = "Asked to change a fixture file; blocked on one question."
    questions = manifest.get("questions") or []
    if len(questions) != 1:
        return None, f"the crafter seeded {len(questions)} questions, not one"
    for key in list(questions[0]):
        questions[0][key] = "fixture text for " + key
    questions[0]["context"] = CLARIFY_CONTEXT
    mpath.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tarball = s["where"] / f"{rdir.name}.tar.gz"
    try:
        with tarfile.open(tarball, "w:gz") as tf:
            tf.add(str(rdir), arcname=rdir.name)
    except OSError as e:
        raise OracleError(f"could not tar the fixture response: {e}")
    return tarball, ""


def bale_clipboard(s, text):
    """Pipe text into this tree's bale clipboard; (rc, stderr, copies)."""
    rc, out, err = run(s["bale"] + ["clipboard", "--block", "probe block"], cwd=s["repo"],
                       env=s["env"], stdin_bytes=text.encode("utf-8"))
    return rc, out + "\n" + err, s["cap"].new()


results = []


def probe(label, ok, detail=""):
    results.append((label, bool(ok), detail))


def fail_all(labels, why):
    for label in labels:
        probe(label, False, why)


def main():
    controls()

    # 1. A clarification's landing, through a plain command.
    labels = ("a clarification's landing prints the exchange block bale relay prints",
              "a clarification's landing copies that block last, as bale relay copies it",
              "the landing's clipboard notice names the exchange block",
              "exchange copies are never masked")
    a = fresh_session("landing", clip="plain")
    tarball, why = (None, a["why"]) if not a["sid"] else clarification_tarball(a)
    if tarball is None:
        fail_all(labels, why)
    else:
        sid = a["sid"]
        arc, aout, aerr = run(a["bale"] + ["apply", str(tarball)], cwd=a["repo"], env=a["env"])
        landing_copies = a["cap"].new()
        rrc, rout, rerr = run(a["bale"] + ["relay", sid], cwd=a["repo"], env=a["env"])
        relay_copies = a["cap"].new()
        relay_block = exchange_block(rout, sid)
        landing_block = exchange_block(aout, sid)
        if arc != 0 or rrc != 0 or relay_block is None:
            fail_all(labels, f"apply exited {arc}, relay re-emit exited {rrc}, "
                             f"relay block {'found' if relay_block else 'missing'}")
        else:
            probe(labels[0], landing_block == relay_block,
                  "no exchange block on the landing's stdout" if landing_block is None
                  else "the landing's block differs from bale relay's")
            want = relay_copies[-1] if relay_copies else None
            probe(labels[1], want is not None and bool(landing_copies) and landing_copies[-1] == want,
                  f"the landing made {len(landing_copies)} copies; bale relay made "
                  f"{len(relay_copies)}; the last landing copy "
                  f"{'matches' if landing_copies and want is not None and landing_copies[-1] == want else 'does not match'}")
            probe(labels[2], any("exchange block" in n and "copied" in n for n in notices(aerr)),
                  f"landing notices: {notices(aerr)!r}")
            raw = ("alice:" + SECRET_A + "@").encode("utf-8")
            probe(labels[3], bool(landing_copies) and raw in landing_copies[-1]
                  and bool(relay_copies) and raw in relay_copies[-1],
                  "a landing or relay copy lost the credential its record carries")

    # 2. bale clipboard, through a plain command.
    labels = ("bale clipboard masks a URL credential and changes nothing else",
              "bale clipboard's notice says it masked",
              "a copy through a command other than clip.exe stays UTF-8, byte for byte")
    b = fresh_session("plaincopy", clip="plain")
    if not b["sid"]:
        fail_all(labels, b["why"])
    else:
        rc, err, copies = bale_clipboard(b, PROBE_TEXT)
        got = copies[-1].decode("utf-8", "replace") if copies else None
        sec = [("https://alice:", SECRET_A, "example.com/x"),
               ("postgres://bob:", SECRET_B, "db.internal:5432/app")]
        probe(labels[0], rc == 0 and got is not None and masked_as(got, PROBE_TEXT, sec),
              f"bale clipboard exited {rc}; copy {'absent' if got is None else repr(got[:160])}")
        probe(labels[1], says_masked(notices(err)),
              f"clipboard notices: {notices(err)!r}")
        rc, err, copies = bale_clipboard(b, CLEAN_TEXT)
        probe(labels[2], rc == 0 and bool(copies) and copies[-1] == CLEAN_TEXT.encode("utf-8"),
              f"bale clipboard exited {rc}; {len(copies)} copies")

    # 3. clip.exe, by name and by path.
    for kind, label in (("clip.exe", "a clip.exe command gets UTF-16LE with no BOM"),
                        ("clip.exe-path", "clip.exe named by its path gets UTF-16LE with no BOM")):
        c = fresh_session(kind, clip=kind)
        if not c["sid"]:
            probe(label, False, c["why"])
            continue
        rc, err, copies = bale_clipboard(c, CLEAN_TEXT)
        want = CLEAN_TEXT.encode("utf-16-le")
        probe(label, rc == 0 and bool(copies) and copies[-1] == want,
              f"bale clipboard exited {rc}; copy starts {copies[-1][:12].hex() if copies else None}, "
              f"wanted {want[:12].hex()}")

    # 4. bale relay's exchange copy through clip.exe.
    label = "bale relay's exchange copy reaches clip.exe as UTF-16LE with no BOM"
    d = fresh_session("relay-clip", clip="clip.exe")
    tarball, why = (None, d["why"]) if not d["sid"] else clarification_tarball(d)
    if tarball is None:
        probe(label, False, why)
    else:
        arc, _, _ = run(d["bale"] + ["apply", str(tarball)], cwd=d["repo"], env=d["env"])
        d["cap"].new()
        rrc, rout, rerr = run(d["bale"] + ["relay", d["sid"]], cwd=d["repo"], env=d["env"])
        copies = d["cap"].new()
        block = exchange_block(rout, d["sid"])
        probe(label, arc == 0 and rrc == 0 and block is not None and bool(copies)
              and copies[-1] == block.encode("utf-16-le"),
              f"apply {arc}, relay {rrc}, {len(copies)} copies; last starts "
              f"{copies[-1][:12].hex() if copies else None}")

    ver_file = TREE / "bin" / "VERSION"
    ver = ver_file.read_text(encoding="utf-8").strip() if ver_file.is_file() else None
    rec_file = TREE / "claude" / "changelog" / "0.4.59.json"
    rec_ver = None
    if rec_file.is_file():
        try:
            rec_ver = json.loads(rec_file.read_text(encoding="utf-8")).get("version")
        except (ValueError, AttributeError):
            rec_ver = "unreadable"
    probe("release 0.4.59: bin/VERSION and claude/changelog/0.4.59.json",
          ver == "0.4.59" and rec_ver == "0.4.59",
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
