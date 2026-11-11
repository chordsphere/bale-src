#!/usr/bin/env bash
# Blind checkpoint for bale-src session exchange-words (v1).
#
# Authored blind, from the request's brief, before any implementation
# existed, by the planner sitting 2026-11-11-bale-src-slips-plan-sitting-003.
# The worker never reads, edits or declares this file (TARBALL.md 7).
#
# It grades outcomes only, in the tree it runs in (bale's staging root, the
# landed tree), driving this tree's own bin/bale and crafter in throwaway
# repos under /tmp:
#   - a clarification's landing and a dry-run of it no longer send anyone to
#     "the worker's chat", and name the answer path, bale relay <sid>;
#   - the exchange block's planner-facing header line reads as the brief
#     pins it, from bale relay and from the crafter's --emit-block alike;
#   - a crafter-rendered worker block still ingests through bale relay;
#   - the release is 0.4.58.
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
WORK = Path(tempfile.mkdtemp(prefix="bale-oracle-exch-"))

# The brief's pinned header line, verbatim, for a worker record of one
# question at round 1 (TARBALL.md 5.9.2's purpose header, second line).
PINNED_HEADER = ("# 1 blocking question(s). Planner: answer as an exchange record "
                 "(from: planner, round 2, answers[] keyed question_round 1) and "
                 "record it with the relay of the tool that carried this block "
                 "(bale's own: `bale relay {sid} <answer.json|->`).")


# --- detectors (each one is exercised by a control before any probe) ---

def mentions_worker_chat(text):
    """True when the text sends anyone to the worker's chat."""
    return re.search(r"worker(?:'|\u2019)s chat", text, re.IGNORECASE) is not None


def names_relay(text, sid):
    """True when one line names bale's relay verb with this session's id."""
    return any(f"bale relay {sid}" in ln for ln in text.splitlines())


def exchange_header(text, sid):
    """The purpose-header comment lines of the exchange block for sid, or None."""
    lines = text.splitlines()
    begin = f"BALE EXCHANGE BEGIN {sid}"
    for i, ln in enumerate(lines):
        if ln.strip() == begin:
            head = []
            for nxt in lines[i + 1:]:
                if not nxt.startswith("#"):
                    break
                head.append(nxt)
            return head
    return None


def header_reads_pinned(head, sid):
    return head is not None and len(head) >= 2 and head[1] == PINNED_HEADER.format(sid=sid)


# --- controls: prove every detector on synthetic input; a miss exits 2 ---

def controls():
    if not mentions_worker_chat("  answer the questions in the Worker's chat, then"):
        raise OracleError("control: mentions_worker_chat missed the phrase")
    if not mentions_worker_chat("in the worker\u2019s chat"):
        raise OracleError("control: mentions_worker_chat missed the typographic apostrophe")
    if mentions_worker_chat("carry it to the worker; chat later"):
        raise OracleError("control: mentions_worker_chat matched a near miss")
    if not names_relay("x\n  then `bale relay 2026-01-01-a-001 <answer.json|->`\n", "2026-01-01-a-001"):
        raise OracleError("control: names_relay missed the verb")
    if names_relay("bale relay <sid>\nbale relay 2026-01-01-a-002\n", "2026-01-01-a-001"):
        raise OracleError("control: names_relay matched another session")
    block = ("noise\nBALE EXCHANGE BEGIN S\n# one\n# two\n{\n  \"a\": 1\n}\n# sha256 x\n"
             "BALE EXCHANGE END\n")
    if exchange_header(block, "S") != ["# one", "# two"]:
        raise OracleError(f"control: exchange_header read {exchange_header(block, 'S')!r}")
    if exchange_header(block, "T") is not None:
        raise OracleError("control: exchange_header found a block for another sid")
    good = ["# first", PINNED_HEADER.format(sid="S")]
    if not header_reads_pinned(good, "S"):
        raise OracleError("control: header_reads_pinned refused the pinned line")
    if header_reads_pinned(["# first", PINNED_HEADER.format(sid="S") + " "], "S"):
        raise OracleError("control: header_reads_pinned took a line that differs by a byte")
    if header_reads_pinned(None, "S") or header_reads_pinned(["# first"], "S"):
        raise OracleError("control: header_reads_pinned took a missing line")


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



def fresh_session(name):
    """A scratch install and repo with one packed session; returns its parts."""
    where = WORK / name
    where.mkdir()
    home = make_home(where)
    install = make_install(where)
    env = base_env(home)
    env["BALE_INSTALL"] = str(where / "bale-install-sandbox")
    repo = where / "project"
    repo.mkdir()
    run(["git", "init", "-q", "-b", "main"], cwd=repo, env=env, check=True)
    (repo / "hello.txt").write_text("hello\n", encoding="utf-8")
    # Unconfined by the scratch repo's own config: its confinement is not
    # what is graded, and a nested-sandbox fault must never read as a verdict.
    (repo / "bale.toml").write_text("[sandbox]\nenabled = false\n", encoding="utf-8")
    run(["git", "add", "-A"], cwd=repo, env=env, check=True)
    run(["git", "commit", "-q", "-m", "init"], cwd=repo, env=env, check=True)
    bale = [sys.executable, "-B", str(install / "bin" / "bale")]
    crafter = [sys.executable, "-I", "-B", str(install / "tools" / "craft_response.py")]
    s = {"where": where, "env": env, "repo": repo, "bale": bale, "crafter": crafter,
         "sid": None, "why": ""}
    rc, out, err = run(bale + ["pack", "oracle fixture goal", "--slug", "oracle-fixture",
                               "--include", "hello.txt", "--no-readme", "--json"],
                       cwd=repo, env=env)
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


def clarification_dir(s):
    """A filled one-question clarification response, scaffolded by this tree's crafter."""
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
    mpath.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return rdir, ""


results = []


def probe(label, ok, detail=""):
    results.append((label, bool(ok), detail))


LANDING = ("a clarification's landing names no worker's chat",
           "a clarification's landing names bale relay with its session id",
           "a dry-run of a clarification names no worker's chat",
           "a dry-run of a clarification names bale relay with its session id",
           "bale relay's exchange header reads the brief's pinned line",
           "the crafter's --emit-block header reads the brief's pinned line")


def main():
    controls()

    a = fresh_session("landing")
    rdir, why = (None, a["why"]) if not a["sid"] else clarification_dir(a)
    if rdir is None:
        for label in LANDING:
            probe(label, False, why)
    else:
        sid = a["sid"]
        tarball = a["where"] / f"{rdir.name}.tar.gz"
        try:
            with tarfile.open(tarball, "w:gz") as tf:
                tf.add(str(rdir), arcname=rdir.name)
        except OSError as e:
            raise OracleError(f"could not tar the fixture response: {e}")
        drc, dout, derr = run(a["bale"] + ["apply", "--dry-run", str(tarball)],
                              cwd=a["repo"], env=a["env"])
        arc, aout, aerr = run(a["bale"] + ["apply", str(tarball)], cwd=a["repo"], env=a["env"])
        landing = aout + "\n" + aerr
        dry = dout + "\n" + derr
        if arc != 0:
            probe(LANDING[0], False, f"the clarification's apply exited {arc}: {landing[-300:]!r}")
            probe(LANDING[1], False, f"the clarification's apply exited {arc}")
        else:
            probe(LANDING[0], not mentions_worker_chat(landing),
                  "the landing's output still sends someone to the worker's chat")
            probe(LANDING[1], names_relay(landing, sid),
                  f"no landing line names 'bale relay {sid}'")
        if drc != 0:
            probe(LANDING[2], False, f"the dry-run exited {drc}: {dry[-300:]!r}")
            probe(LANDING[3], False, f"the dry-run exited {drc}")
        else:
            probe(LANDING[2], not mentions_worker_chat(dry),
                  "the dry-run's output still sends someone to the worker's chat")
            probe(LANDING[3], names_relay(dry, sid), f"no dry-run line names 'bale relay {sid}'")
        rrc, rout, rerr = run(a["bale"] + ["relay", sid], cwd=a["repo"], env=a["env"])
        head = exchange_header(rout, sid)
        probe(LANDING[4], rrc == 0 and header_reads_pinned(head, sid),
              f"bale relay exited {rrc}; header line 2 reads {(head or [None, None])[1:2]!r}")
        crc, cout, cerr = run(a["crafter"] + ["--emit-block", str(rdir / "manifest.json")],
                              cwd=a["where"], env=a["env"])
        chead = exchange_header(cout, sid)
        probe(LANDING[5], crc == 0 and header_reads_pinned(chead, sid),
              f"the crafter exited {crc}; header line 2 reads {(chead or [None, None])[1:2]!r}")

    b = fresh_session("ingest")
    label = "a crafter-rendered worker block still ingests through bale relay"
    rdir, why = (None, b["why"]) if not b["sid"] else clarification_dir(b)
    if rdir is None:
        probe(label, False, why)
    else:
        sid = b["sid"]
        crc, block, cerr = run(b["crafter"] + ["--emit-block", str(rdir / "manifest.json")],
                               cwd=b["where"], env=b["env"])
        if crc != 0:
            probe(label, False, f"the crafter's --emit-block exited {crc}: {cerr[-300:]!r}")
        else:
            bfile = b["where"] / "worker-block.txt"
            bfile.write_text(block, encoding="utf-8")
            rrc, rout, rerr = run(b["bale"] + ["relay", sid, str(bfile)],
                                  cwd=b["repo"], env=b["env"])
            kept = b["repo"] / ".bale" / "clarifications" / sid / "001.json"
            probe(label, rrc == 0 and kept.is_file(),
                  f"bale relay exited {rrc}; round 1 {'kept' if kept.is_file() else 'not kept'}: "
                  f"{(rerr or rout)[-300:]!r}")

    ver_file = TREE / "bin" / "VERSION"
    ver = ver_file.read_text(encoding="utf-8").strip() if ver_file.is_file() else None
    rec_file = TREE / "claude" / "changelog" / "0.4.58.json"
    rec_ver = None
    if rec_file.is_file():
        try:
            rec_ver = json.loads(rec_file.read_text(encoding="utf-8")).get("version")
        except (ValueError, AttributeError):
            rec_ver = "unreadable"
    probe("release 0.4.58: bin/VERSION and claude/changelog/0.4.58.json",
          ver == "0.4.58" and rec_ver == "0.4.58",
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
