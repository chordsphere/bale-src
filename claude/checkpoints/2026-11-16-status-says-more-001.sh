#!/usr/bin/env bash
# Blind checkpoint for bale-src session status-says-more (v1).
#
# Authored blind, from the request's brief, before any implementation
# existed, by the planner sitting 2026-11-11-bale-src-slips-plan-sitting-003.
# The worker never reads, edits or declares this file (TARBALL.md 7).
#
# It grades outcomes only, in the tree it runs in (bale's staging root, the
# landed tree), driving this tree's own bin/bale in throwaway repos under
# /tmp and reading bale status, bale status --json, bale stats --json,
# bale stats --sid SID --json and bale contract --json:
#   - status --json names the directories the named search consults
#     (config.search_dirs, tilde expanded) beside the old count;
#   - status --json carries open_sessions: every open session's state, goal
#     and clarification facts, and the response tarballs the named search
#     would find for it, numbered browser copies included, newest first;
#   - bale apply of a response by name says so when a newer numbered copy
#     sits beside it, and still applies the file it was named;
#   - a clarification landing writes its own attempt, which the dossier
#     shows, and the session still closes on its normal response;
#   - the clipboard row and status --json say a clip.exe command is fed
#     UTF-16LE;
#   - bale contract publishes the HOLD classes as the vocabulary hold-class,
#     and the status line's keys as status emits them;
#   - the release is 0.4.63.
#
# Exit codes (TARBALL.md 7.5): 0 every probe passed; 1 a probe failed (the
# work's failure, a crash of the code under test included); 2 the oracle's
# own machinery broke (a control, git, file setup, an unplanned exception).
# Reads nothing but the tree it grades: no session id, no manifest, no path
# of its own. Writes only under one temporary directory it makes and removes.
set -u
export PYTHONDONTWRITEBYTECODE=1
exec python3 -I -B - <<'ORACLE'
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
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
WORK = Path(tempfile.mkdtemp(prefix="bale-oracle-sta-"))
HOLD_WORDS = {"checkpoint-defect", "both", "checkpoint", "validation"}


# --- detectors (each one is exercised by a control before any probe) ---

def last_json(text):
    """The last line of text that parses as a JSON object, or None."""
    for ln in reversed(text.strip().splitlines()):
        try:
            v = json.loads(ln)
        except ValueError:
            continue
        if isinstance(v, dict):
            return v
    return None


def entry_path(entry):
    """A responses entry's path: the string itself, or an object's path."""
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict) and isinstance(entry.get("path"), str):
        return entry["path"]
    return None


def same_paths(got, want):
    """True when the list `got` names exactly the paths `want`, in order,
    each compared after resolving (a symlinked /tmp reads the same)."""
    if not isinstance(got, list) or len(got) != len(want):
        return False
    for g, w in zip(got, want):
        p = entry_path(g)
        if p is None or Path(p).resolve() != Path(w).resolve():
            return False
    return True


def mentions(text, needle):
    """True when `needle` occurs in `text`, case-insensitively."""
    return needle.lower() in (text or "").lower()


# --- controls: prove every detector on synthetic input; a miss exits 2 ---

def controls():
    if last_json('[bale] x\n{"a": 1}\n{"b": 2}\nnot json\n') != {"b": 2}:
        raise OracleError("control: last_json misread")
    if last_json("[1, 2]\nnope\n") is not None:
        raise OracleError("control: last_json took a non-object")
    if entry_path("/a") != "/a" or entry_path({"path": "/b", "x": 1}) != "/b":
        raise OracleError("control: entry_path misread a good entry")
    if entry_path({"name": "/b"}) is not None or entry_path(3) is not None:
        raise OracleError("control: entry_path took a bad entry")
    d = WORK / "control"
    d.mkdir()
    (d / "real").mkdir()
    (d / "link").symlink_to(d / "real")
    if not same_paths([str(d / "link" / "x"), {"path": str(d / "y")}],
                      [d / "real" / "x", d / "y"]):
        raise OracleError("control: same_paths missed a match")
    for got in ([str(d / "y"), str(d / "real" / "x")], [str(d / "y")], None,
                [str(d / "real" / "x"), {"name": "y"}]):
        if same_paths(got, [d / "real" / "x", d / "y"]):
            raise OracleError(f"control: same_paths took {got!r}")
    if not mentions("A Newer copy", "newer") or mentions("a fresh copy", "newer"):
        raise OracleError("control: mentions misread")


# --- machinery ---

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
            "VISUAL": "/bin/true", "PYTHONDONTWRITEBYTECODE": "1",
            "COLUMNS": "400"}


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


def fixture(name, *, toml_extra=""):
    """A scratch install and committed repo with three files, an inbound
    directory under HOME named by tilde and a second one by absolute path,
    both configured as [apply] search_paths."""
    where = WORK / name
    where.mkdir()
    home = make_home(where)
    install = make_install(where)
    env = base_env(home)
    env["BALE_INSTALL"] = str(where / "bale-install-sandbox")
    inbound = home / "inbound"
    inbound.mkdir()
    second = where / "second"
    second.mkdir()
    repo = where / "project"
    repo.mkdir()
    run(["git", "init", "-q", "-b", "main"], cwd=repo, env=env, check=True)
    for fname in ("hello.txt", "alpha.txt", "beta.txt"):
        (repo / fname).write_text(f"{fname} at start\n", encoding="utf-8")
    toml = ("[sandbox]\nenabled = false\n\n[apply]\n"
            f"search_paths = [\"~/inbound\", \"{second}\"]\n" + toml_extra)
    (repo / "bale.toml").write_text(toml, encoding="utf-8")
    run(["git", "add", "-A"], cwd=repo, env=env, check=True)
    run(["git", "commit", "-q", "-m", "init"], cwd=repo, env=env, check=True)
    return {"where": where, "env": env, "repo": repo, "home": home,
            "inbound": inbound, "second": second, "install": install,
            "bale": [sys.executable, "-B", str(install / "bin" / "bale")]}


def pack(f, goal, slug, *extra):
    rc, out, err = run(f["bale"] + ["pack", goal, "--slug", slug,
                                    "--include", "hello.txt", "--no-readme", "--json", *extra],
                       cwd=f["repo"], env=f["env"])
    report = last_json(out) if rc == 0 else None
    sid = report.get("sid") if report else None
    return sid, ("" if sid else f"the scratch pack {slug} exited {rc}: {(err or out)[-300:]!r}")


FEEDBACK = {
    "mechanical": {"response_kind": "normal", "schema_valid": True,
                   "mirror_agreement": {"changes_to_files": True, "files_to_changes": True},
                   "claims_subset": True},
    "self_reported": {"assumptions": [], "judgment_calls": [], "budget_pressure": "none",
                      "includes_missing": [], "compaction_occurred": {"occurred": False},
                      "light_blocks": 0, "paste_carried_rounds": 0},
}


def write_tar(rdir, dest):
    try:
        with tarfile.open(dest, "w:gz") as tf:
            tf.add(str(rdir), arcname=rdir.name)
    except OSError as e:
        raise OracleError(f"could not tar a fixture response: {e}")


def normal_response(f, sid, path, data, dest, *, validation_rc=0, tag="r"):
    """A one-file normal response for sid, tarred to dest."""
    rdir = f["where"] / "build" / tag / f"response-{sid[-3:]}"
    (rdir / "files").mkdir(parents=True)
    (rdir / "files" / path).write_bytes(data)
    manifest = {
        "session_id": sid, "responds_to": sid, "corrects": None, "response_kind": "normal",
        "summary": "oracle fixture response",
        "changes": [{"path": path, "action": "modified", "reason": "fixture change",
                     "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}],
        "deferred": [], "validation_will_run": ["fixture check"],
        "claims": {"fixture check": "pass"},
        "feedback": FEEDBACK,
    }
    (rdir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (rdir / "apply.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (rdir / "validation.sh").write_text(
        "#!/usr/bin/env bash\necho '[PASS] fixture check'\n"
        f"exit {validation_rc}\n", encoding="utf-8")
    write_tar(rdir, dest)


def clarification_response(f, sid, dest):
    """A clarification response for sid, scaffolded by the tree's own
    crafter, its questions filled with neutral fixture text."""
    rdir = f["where"] / "build" / "clar" / f"response-{sid[-3:]}"
    rdir.mkdir(parents=True)
    crafter = f["install"] / "tools" / "craft_response.py"
    rc, out, err = run([sys.executable, "-I", "-B", str(crafter), str(rdir), "--kind",
                        "clarification", "--sid", sid, "--write"],
                       cwd=f["where"], env=f["env"])
    if rc != 0 or not (rdir / "manifest.json").is_file():
        return f"the tree's crafter could not scaffold a clarification ({rc}): {(err or out)[-300:]!r}"
    try:
        m = json.loads((rdir / "manifest.json").read_text(encoding="utf-8"))
        m["summary"] = "Blocked on one fixture question."
        for q in m["questions"]:
            for k in list(q):
                q[k] = f"fixture text for {k}"
    except (ValueError, KeyError, TypeError) as e:
        return f"the crafter's clarification manifest did not read: {e}"
    (rdir / "manifest.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    write_tar(rdir, dest)
    return ""


def bale(f, *args):
    return run(f["bale"] + list(args), cwd=f["repo"], env=f["env"])


def status_json(f):
    rc, out, err = bale(f, "status", "--json")
    return last_json(out) if rc == 0 else None, rc, err


def dossier(f, sid):
    rc, out, err = bale(f, "stats", "--sid", sid, "--json")
    d = last_json(out) if rc == 0 else None
    return d if isinstance(d, dict) and d.get("found") else None


def set_mtime(path, seconds_ago):
    t = time.time() - seconds_ago
    os.utime(path, (t, t))


results = []


def probe(label, ok, detail=""):
    results.append((label, bool(ok), detail))


def fail_all(labels, why):
    for label in labels:
        probe(label, False, why)


def version_of_tree():
    v = TREE / "bin" / "VERSION"
    return v.read_text(encoding="utf-8").strip() if v.is_file() else None


def main():
    controls()
    version = version_of_tree()

    # 1. Four open sessions: one packed (the lock), one read-only, one
    #    suspended on a clarification, one held; and response tarballs for
    #    the first in cwd and both search directories.
    f = fixture("four-open")
    a, why_a = pack(f, "goal of the first session", "first", "--write", "hello.txt")
    b, why_b = pack(f, "goal of the second session", "second", "--read-only")
    c, why_c = pack(f, "goal of the third session", "third", "--write", "alpha.txt")
    d, why_d = pack(f, "goal of the fourth session", "fourth", "--write", "beta.txt")
    labels = (
        "status --json config.search_dirs lists the configured directories, tilde expanded",
        "status --json keeps config.search_paths as the count",
        "status --json open_sessions has one entry per open session",
        "status --json keeps sid, session and scopes for the lock session",
        "open_sessions gives each open session its own goal",
        "open_sessions reads packed, packed, clarification and held for the four sessions",
        "open_sessions carries the clarified session's clarification facts",
        "open_sessions lists the response tarballs the named search would find, numbered copies included, newest first",
        "open_sessions lists no tarball for a session with none, nor one answering a closed session",
        "a clarification landing writes its own attempt, shown on the dossier",
        "the session stays in flight after its clarification attempt",
        "the aggregate still reads a corpus holding a clarification attempt",
        "a clarified session still closes on its normal response",
        "bale contract publishes the status line's keys as status emits them",
    )
    why = why_a or why_b or why_c or why_d
    if why:
        fail_all(labels, why)
    else:
        why = clarification_response(f, c, f["inbound"] / f"response-{c}.tar.gz")
        if why:
            raise OracleError(why)
        rc_c, out_c, err_c = bale(f, "apply", f"response-{c}.tar.gz")
        held_tar = f["where"] / f"held-{d[-3:]}.tar.gz"
        normal_response(f, d, "beta.txt", b"beta, held\n", held_tar, validation_rc=1, tag="held")
        rc_d, out_d, err_d = bale(f, "apply", str(held_tar))
        plain = f["inbound"] / f"response-{a}.tar.gz"
        twin1 = f["second"] / f"response-{a} (1).tar.gz"
        twin2 = f["repo"] / f"response-{a} (2).tar.gz"
        for p, ago in ((plain, 300), (twin1, 200), (twin2, 100)):
            normal_response(f, a, "hello.txt", b"hello, " + p.name.encode() + b"\n", p,
                            tag=f"a{ago}")
            set_mtime(p, ago)
        stray = f["inbound"] / "response-2026-01-01-closed-session-001.tar.gz"
        normal_response(f, a, "hello.txt", b"stray\n", stray, tag="stray")
        st, rc, err = status_json(f)
        if st is None:
            fail_all(labels, f"status --json exited {rc}: {err[-300:]!r}")
        else:
            cfg = st.get("config") or {}
            probe(labels[0], same_paths(cfg.get("search_dirs"), [f["inbound"], f["second"]]),
                  f"config.search_dirs {cfg.get('search_dirs')!r}")
            probe(labels[1], cfg.get("search_paths") == 2 and type(cfg.get("search_paths")) is int,
                  f"config.search_paths {cfg.get('search_paths')!r}")
            op = st.get("open_sessions")
            op = op if isinstance(op, dict) else {}
            probe(labels[2], sorted(op) == sorted([a, b, c, d])
                  and sorted(st.get("sessions") or []) == sorted([a, b, c, d]),
                  f"open_sessions keys {sorted(op)!r}, sessions {st.get('sessions')!r}")
            sess = st.get("session") or {}
            goal_of = {a: "goal of the first session", b: "goal of the second session",
                       c: "goal of the third session", d: "goal of the fourth session"}
            probe(labels[3], st.get("sid") in goal_of and sess.get("goal") == goal_of[st.get("sid")]
                  and (st.get("scopes") or {}).get(b) == [],
                  f"sid {st.get('sid')!r}, session.goal {sess.get('goal')!r}, "
                  f"scopes {st.get('scopes')!r}")
            goals = [(op.get(s) or {}).get("goal") for s in (a, b, c, d)]
            probe(labels[4], goals == [f"goal of the {n} session" for n in
                                       ("first", "second", "third", "fourth")],
                  f"goals {goals!r}")
            states = [(op.get(s) or {}).get("state") for s in (a, b, c, d)]
            probe(labels[5], states == ["packed", "packed", "clarification", "held"],
                  f"states {states!r}; the clarification landing exited {rc_c}, "
                  f"the held apply exited {rc_d}")
            clar = (op.get(c) or {}).get("clarification")
            probe(labels[6], isinstance(clar, dict) and clar.get("rounds") == 1
                  and (op.get(a) or {}).get("clarification", "absent") is None,
                  f"third's clarification {clar!r}, first's "
                  f"{(op.get(a) or {}).get('clarification', 'absent')!r}")
            got = (op.get(a) or {}).get("responses")
            probe(labels[7], same_paths(got, [twin2, twin1, plain]),
                  f"first's responses {got!r}")
            got_b = (op.get(b) or {}).get("responses")
            got_c = (op.get(c) or {}).get("responses")
            probe(labels[8], got_b == [] and same_paths(got_c, [f["inbound"] / f"response-{c}.tar.gz"])
                  and not any("closed-session" in str(e) for s in (a, b, c, d)
                              for e in ((op.get(s) or {}).get("responses") or [])),
                  f"second's responses {got_b!r}, third's {got_c!r}")
            rc_k, out_k, err_k = bale(f, "contract", "--json")
            ck = last_json(out_k) if rc_k == 0 else None
            line_keys = None
            rc_s, out_s, _ = bale(f, "status", "--json")
            if rc_s == 0:
                try:
                    line_keys = list(json.loads(out_s.strip().splitlines()[-1]))
                except (ValueError, IndexError):
                    line_keys = None
            want_keys = ((ck or {}).get("json_keys") or {}).get("status")
            probe(labels[13], line_keys is not None and want_keys == line_keys
                  and "open_sessions" in line_keys,
                  f"contract {want_keys!r}, status line {line_keys!r}")
        try:
            twin2.unlink()
        except OSError as e:
            raise OracleError(f"could not remove the fixture copy in cwd: {e}")
        dc = dossier(f, c)
        atts =(dc or {}).get("attempts") or []
        clar_atts = [x for x in atts if x.get("outcome") == "clarification"]
        probe(labels[9], rc_c == 0 and len(clar_atts) == 1 and clar_atts[0].get("command") == "apply"
              and ((clar_atts[0].get("clarification") or {}).get("rounds") == 1),
              f"landing exited {rc_c}; dossier attempts "
              f"{[(x.get('command'), x.get('outcome')) for x in atts]!r}; "
              f"{(err_c or out_c)[-200:]!r}" if rc_c else
              f"dossier attempts {[(x.get('command'), x.get('outcome'), x.get('clarification')) for x in atts]!r}")
        probe(labels[10], dc is not None and (dc.get("record") or {}).get("in_flight") is True,
              f"record.in_flight {((dc or {}).get('record') or {}).get('in_flight')!r}")
        rc_g, out_g, err_g = bale(f, "stats", "--json")
        agg = last_json(out_g) if rc_g == 0 else None
        probe(labels[11], isinstance(agg, dict) and c in ((agg.get("members") or {}).get("sessions") or []),
              f"stats --json exited {rc_g}: {(err_g or '')[-200:]!r}")
        done = f["where"] / f"done-{c[-3:]}.tar.gz"
        normal_response(f, c, "alpha.txt", b"alpha, answered\n", done, tag="done")
        rc_n, out_n, err_n = bale(f, "apply", str(done))
        dn = dossier(f, c)
        seq = [x.get("outcome") for x in ((dn or {}).get("attempts") or [])]
        probe(labels[12], rc_n == 0 and seq[-2:] == ["clarification", "applied"]
              and ((dn or {}).get("record") or {}).get("in_flight") is False,
              f"apply exited {rc_n}; outcomes {seq!r}; {(err_n or out_n)[-200:]!r}")

    # 2. bale apply by name, a newer numbered copy beside it; then an older one.
    for name, plain_ago, twin_ago in (("twin-newer", 300, 100), ("twin-older", 100, 300)):
        f = fixture(name)
        a, why = pack(f, "goal of the named session", "named", "--write", "hello.txt")
        if name == "twin-newer":
            labels = ("bale apply by name says a newer numbered copy sits beside the file it names",
                      "bale apply by name still applies the file it was named")
        else:
            labels = ("bale apply by name says nothing of a numbered copy older than the file it names",)
        if why:
            fail_all(labels, why)
            continue
        plain = f["inbound"] / f"response-{a}.tar.gz"
        twin = f["second"] / f"response-{a} (1).tar.gz"
        normal_response(f, a, "hello.txt", b"the named file\n", plain, tag="plain")
        normal_response(f, a, "hello.txt", b"the numbered copy\n", twin, tag="twin")
        set_mtime(plain, plain_ago)
        set_mtime(twin, twin_ago)
        rc, out, err = bale(f, "apply", f"response-{a}.tar.gz")
        text = out + "\n" + err
        body = (f["repo"] / "hello.txt").read_text(encoding="utf-8", errors="replace")
        if name == "twin-newer":
            probe(labels[0], rc == 0 and mentions(text, twin.name) and mentions(text, "newer"),
                  f"apply exited {rc}; output {text[-400:]!r}")
            probe(labels[1], rc == 0 and body == "the named file\n",
                  f"apply exited {rc}; hello.txt {body!r}")
        else:
            probe(labels[0], rc == 0 and not mentions(text, twin.name)
                  and body == "the named file\n",
                  f"apply exited {rc}; hello.txt {body!r}; output {text[-300:]!r}")

    # 3. The clipboard row and status --json, for clip.exe, cat and unset.
    for name, toml_extra, enc in (
            ("clip-exe", "\n[clipboard]\ncommand = \"clip.exe\"\n", "utf-16le"),
            ("clip-cat", "\n[clipboard]\ncommand = \"cat\"\n", "utf-8"),
            ("clip-unset", "", None)):
        f = fixture(name, toml_extra=toml_extra)
        rc_h, out_h, err_h = bale(f, "status")
        st, rc_j, err_j = status_json(f)
        got = ((st or {}).get("clipboard") or {}).get("encoding", "absent")
        command = {"clip-exe": "clip.exe", "clip-cat": "cat", "clip-unset": "an unset command"}[name]
        probe(f"status --json clipboard.encoding reads {enc} for {command}",
              got == enc and "encoding" in ((st or {}).get("clipboard") or {}),
              f"clipboard {((st or {}).get('clipboard'))!r}; status --json exited {rc_j}")
        if name == "clip-exe":
            probe("the status clipboard row says clip.exe is fed UTF-16LE",
                  rc_h == 0 and "UTF-16LE" in out_h,
                  f"status exited {rc_h}; {out_h[-500:]!r}")
        elif name == "clip-cat":
            probe("the status clipboard row names no UTF-16 for another command",
                  rc_h == 0 and "UTF-16" not in out_h and "cat" in out_h,
                  f"status exited {rc_h}; {out_h[-500:]!r}")

    # 4. bale contract publishes the HOLD classes.
    f = fixture("contract")
    rc, out, err = bale(f, "contract", "--json")
    ck = last_json(out) if rc == 0 else None
    voc = (((ck or {}).get("vocabularies") or {}).get("hold-class") or {})
    vals = voc.get("values")
    probe("bale contract --json publishes the vocabulary hold-class with the four HOLD classes",
          isinstance(vals, list) and len(vals) == 4 and set(vals) == HOLD_WORDS
          and isinstance(voc.get("home"), str) and isinstance(voc.get("pointer"), str),
          f"contract exited {rc}; hold-class {voc!r}")

    rec_file = TREE / "claude" / "changelog" / "0.4.63.json"
    rec_ver = None
    if rec_file.is_file():
        try:
            rec_ver = json.loads(rec_file.read_text(encoding="utf-8")).get("version")
        except (ValueError, AttributeError):
            rec_ver = "unreadable"
    probe("release 0.4.63: bin/VERSION and claude/changelog/0.4.63.json",
          version == "0.4.63" and rec_ver == "0.4.63",
          f"bin/VERSION {version!r}, changelog record version {rec_ver!r}")


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
