#!/usr/bin/env bash
# Blind checkpoint for bale-src session apply-report (v1).
#
# Authored blind, from the request's brief, before any implementation
# existed, by the planner sitting 2026-11-11-bale-src-slips-plan-sitting-003.
# The worker never reads, edits or declares this file (TARBALL.md 7).
#
# It grades outcomes only, in the tree it runs in (bale's staging root, the
# landed tree), driving this tree's own bin/bale in throwaway repos under
# /tmp and reading the tree's own files:
#   - bale apply --json carries relay: the blocks to carry, in send order,
#     each with its addressee, byte for byte as printed;
#   - a checkpoint changed since pack refuses under --json with outcome
#     checkpoint-change-refused and the paste-ready accept line, and the
#     dossier records that outcome;
#   - every --json verb's help points at bale contract, and no help keeps a
#     stale key or outcome list;
#   - a newer numbered copy beside an absolute name is said;
#   - the human bale status shows each open session's state;
#   - the crafter names no office-src, PLANNER.md names no office, and the
#     stats fixture corpus holds a record with this era's keys;
#   - the release is 0.4.64.
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
import re
import shlex
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
WORK = Path(tempfile.mkdtemp(prefix="bale-oracle-apr-"))
JSON_VERBS = ("pack", "apply", "retry", "status", "stats", "open", "relay",
              "unlock", "revert")
REFUSED = "checkpoint-change-refused"


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


def relay_shape(relay):
    """[(addressee, text)] for a well-formed relay list, else None."""
    if not isinstance(relay, list):
        return None
    out = []
    for e in relay:
        if not isinstance(e, dict) or not isinstance(e.get("addressee"), str) \
                or not isinstance(e.get("text"), str):
            return None
        out.append((e["addressee"], e["text"]))
    return out


def is_relay_block(text, sid, addressee):
    """True when text is one addressed relay block: its first line the
    BEGIN sentinel and its last non-empty line the END sentinel."""
    lines = text.strip("\n").split("\n")
    return (len(lines) >= 2
            and lines[0] == f"=== RELAY BEGIN {sid} to {addressee} ==="
            and lines[-1] == f"=== RELAY END {sid} to {addressee} ===")


def printed(text, stream):
    """True when the block text appears whole in the printed stream."""
    body = text.strip("\n")
    return bool(body) and body in stream.replace("\r\n", "\n")


def has_word(text, word):
    """True when `word` occurs as a whole word in text, case-insensitively."""
    return re.search(r"(?<![A-Za-z0-9_-])" + re.escape(word) + r"(?![A-Za-z0-9_-])",
                     text or "", re.IGNORECASE) is not None


def outcome_runs(text):
    """Every run of three or more lowercase words joined by | or / in text,
    as lists of words (a help text's enumerated outcome lists)."""
    return [m.group(0).replace("/", "|").split("|") for m in
            re.finditer(r"[a-z][a-z-]*(?:[|/][a-z][a-z-]*){2,}", text or "")]


def era_keys(records):
    """Which of this era's telemetry facts a list of records carries."""
    seen = set()
    for r in records:
        for a in (r.get("attempts") or []) if isinstance(r, dict) else []:
            if not isinstance(a, dict):
                continue
            if a.get("scope_kind") == "write-forecast":
                seen.add("scope_kind")
            if isinstance(a.get("bale_version"), str):
                seen.add("bale_version")
            if isinstance((a.get("validation") or {}).get("claimed_checks"), dict):
                seen.add("claimed_checks")
            if a.get("outcome") == "clarification":
                seen.add("clarification")
    return seen


# --- controls: prove every detector on synthetic input; a miss exits 2 ---

def controls():
    if last_json('[bale] x\n{"a": 1}\n{"b": 2}\nnot json\n') != {"b": 2}:
        raise OracleError("control: last_json misread")
    if last_json("[1, 2]\nnope\n") is not None:
        raise OracleError("control: last_json took a non-object")
    good = [{"addressee": "worker", "text": "w", "first": True}, {"addressee": "planner", "text": "p"}]
    if relay_shape(good) != [("worker", "w"), ("planner", "p")] or relay_shape([]) != []:
        raise OracleError("control: relay_shape misread a good list")
    for bad in (None, {"addressee": "p"}, [{"addressee": "p"}], [{"to": "p", "text": "t"}], ["t"]):
        if relay_shape(bad) is not None:
            raise OracleError(f"control: relay_shape took {bad!r}")
    blk = "=== RELAY BEGIN s-1 to planner ===\nbody\n=== RELAY END s-1 to planner ===\n"
    if not is_relay_block(blk, "s-1", "planner"):
        raise OracleError("control: is_relay_block missed a block")
    for sid, to, text in (("s-2", "planner", blk), ("s-1", "worker", blk),
                          ("s-1", "planner", "x\n" + blk), ("s-1", "planner", blk + "tail\n")):
        if is_relay_block(text, sid, to):
            raise OracleError("control: is_relay_block took a wrong block")
    if not printed(blk, "[bale] a\r\n" + blk.replace("\n", "\r\n") + "more") or printed(blk, blk[:-5]) \
            or printed("", "anything"):
        raise OracleError("control: printed misread")
    if outcome_runs("x (a|b-c|d) and e/f/g-h; i|j") != [["a", "b-c", "d"], ["e", "f", "g-h"]]:
        raise OracleError("control: outcome_runs misread")
    if not has_word("the Office reads", "office") or has_word("an office-src note", "office") \
            or has_word("officer", "office"):
        raise OracleError("control: has_word misread")
    recs = [{"attempts": [{"scope_kind": "write-forecast", "bale_version": "1",
                           "validation": {"claimed_checks": {}}}]},
            {"attempts": [{"outcome": "clarification"}]}, "junk", {"attempts": None}]
    if era_keys(recs) != {"scope_kind", "bale_version", "claimed_checks", "clarification"} \
            or era_keys([{"attempts": [{"scope_kind": "include", "bale_version": None,
                                        "validation": {"claimed_checks": None}}]}]) != set():
        raise OracleError("control: era_keys misread")


# --- machinery ---

def run(cmd, *, cwd, env, check=False):
    try:
        r = subprocess.run(cmd, cwd=str(cwd), env=env, capture_output=True,
                           timeout=TIMEOUT, input=b"")
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


def fixture(name, *, checkpoint_rc=None):
    """A scratch install and committed repo with two files; with
    checkpoint_rc, a committed check.sh exiting it as [validation] base."""
    where = WORK / name
    where.mkdir()
    home = where / "home"
    home.mkdir()
    (home / ".gitconfig").write_text(
        "[user]\n\tname = Oracle Fixture\n\temail = oracle@example.invalid\n"
        "[init]\n\tdefaultBranch = main\n", encoding="utf-8")
    install = where / "install"
    install.mkdir()
    for tree in ("bin", "docs", "schemas", "tools"):
        src = TREE / tree
        if not src.is_dir():
            raise OracleError(f"the graded tree has no {tree}/ to copy")
        shutil.copytree(src, install / tree, ignore=shutil.ignore_patterns("__pycache__"))
    env = base_env(home)
    env["BALE_INSTALL"] = str(where / "bale-install-sandbox")
    repo = where / "project"
    repo.mkdir()
    run(["git", "init", "-q", "-b", "main"], cwd=repo, env=env, check=True)
    for fname in ("hello.txt", "alpha.txt"):
        (repo / fname).write_text(f"{fname} at start\n", encoding="utf-8")
    toml = "[sandbox]\nenabled = false\n"
    if checkpoint_rc is not None:
        (repo / "check.sh").write_text(f"#!/usr/bin/env bash\nexit {checkpoint_rc}\n",
                                       encoding="utf-8")
        toml += "\n[validation]\nbase = \"check.sh\"\n"
    (repo / "bale.toml").write_text(toml, encoding="utf-8")
    run(["git", "add", "-A"], cwd=repo, env=env, check=True)
    run(["git", "commit", "-q", "-m", "init"], cwd=repo, env=env, check=True)
    return {"where": where, "env": env, "repo": repo, "install": install,
            "bale": [sys.executable, "-B", str(install / "bin" / "bale")]}


def bale(f, *args):
    return run(f["bale"] + list(args), cwd=f["repo"], env=f["env"])


def pack(f, slug="fixture", path="hello.txt"):
    rc, out, err = bale(f, "pack", f"goal of the {slug} session", "--slug", slug,
                        "--include", "hello.txt", "--write", path, "--no-readme", "--json")
    report = last_json(out) if rc == 0 else None
    sid = report.get("sid") if report else None
    return sid, ("" if sid else f"the scratch pack exited {rc}: {(err or out)[-300:]!r}")


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


def normal_response(f, sid, dest, *, data=b"hello, oracle\n", path="hello.txt",
                    validation_rc=0, tag="r"):
    rdir = f["where"] / "build" / tag / f"response-{sid[-3:]}"
    (rdir / "files").mkdir(parents=True)
    (rdir / "files" / path).write_bytes(data)
    manifest = {
        "session_id": sid, "responds_to": sid, "corrects": None, "response_kind": "normal",
        "summary": "oracle fixture response",
        "changes": [{"path": path, "action": "modified", "reason": "fixture change",
                     "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}],
        "deferred": [], "validation_will_run": ["fixture check"],
        "claims": {"fixture check": "pass"}, "feedback": FEEDBACK,
    }
    (rdir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (rdir / "apply.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (rdir / "notes.md").write_text("# notes\n\nFixture notes for the oracle.\n", encoding="utf-8")
    (rdir / "validation.sh").write_text(
        "#!/usr/bin/env bash\necho '[PASS] fixture check'\n"
        f"exit {validation_rc}\n", encoding="utf-8")
    write_tar(rdir, dest)


def clarification_response(f, sid, dest):
    rdir = f["where"] / "build" / "clar" / f"response-{sid[-3:]}"
    rdir.mkdir(parents=True)
    crafter = f["install"] / "tools" / "craft_response.py"
    rc, out, err = run([sys.executable, "-I", "-B", str(crafter), str(rdir), "--kind",
                        "clarification", "--sid", sid, "--write"], cwd=f["where"], env=f["env"])
    if rc != 0 or not (rdir / "manifest.json").is_file():
        raise OracleError(f"the tree's crafter could not scaffold a clarification ({rc}): "
                          f"{(err or out)[-300:]!r}")
    try:
        m = json.loads((rdir / "manifest.json").read_text(encoding="utf-8"))
        m["summary"] = "Blocked on one fixture question."
        for q in m["questions"]:
            for k in list(q):
                q[k] = f"fixture text for {k}"
    except (ValueError, KeyError, TypeError) as e:
        raise OracleError(f"the crafter's clarification manifest did not read: {e}")
    (rdir / "manifest.json").write_text(json.dumps(m, indent=2) + "\n", encoding="utf-8")
    write_tar(rdir, dest)


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


def main():
    controls()
    version_file = TREE / "bin" / "VERSION"
    version = version_file.read_text(encoding="utf-8").strip() if version_file.is_file() else None

    # 1. relay on a clean apply, and on the two HOLDs.
    for name, val_rc, cp_rc, want in (("relay-applied", 0, None, ["planner"]),
                                      ("relay-held-worker", 1, None, ["worker", "planner"]),
                                      ("relay-held-checkpoint", 0, 1, ["planner", "worker"])):
        f = fixture(name, checkpoint_rc=cp_rc)
        label = {"relay-applied": "apply --json relay carries the planner block of a clean apply, as printed",
                 "relay-held-worker": "apply --json relay carries both HOLD blocks, the worker's first when only validation held",
                 "relay-held-checkpoint": "apply --json relay carries both HOLD blocks, the planner's first when the checkpoint held"}[name]
        sid, why = pack(f)
        if not sid:
            probe(label, False, why)
            continue
        tb = f["where"] / f"resp-{sid[-3:]}.tar.gz"
        normal_response(f, sid, tb, validation_rc=val_rc)
        rc, out, err = bale(f, "apply", "--json", str(tb))
        line = last_json(out)
        shape = relay_shape((line or {}).get("relay"))
        ok = (line is not None and len(out.strip().splitlines()) == 1 and shape is not None
              and [a for a, _ in shape] == want
              and all(is_relay_block(t, sid, a) and printed(t, err) for a, t in shape))
        probe(label, ok, f"apply exited {rc}; outcome {(line or {}).get('outcome')!r}; relay "
              f"{[(a, t[:60]) for a, t in shape] if shape else (line or {}).get('relay', 'absent')!r}")

    # 2. A clarification landing's relay; the human status rows per session.
    f = fixture("clarification")
    a, why_a = pack(f, "aaa", "hello.txt")
    b, why_b = pack(f, "bbb", "alpha.txt")
    labels = ("apply --json relay carries a clarification landing's exchange block for the planner",
              "the human bale status shows each open session's own state")
    if why_a or why_b:
        fail_all(labels, why_a or why_b)
    else:
        lock = sorted([a, b])[0]
        other = b if lock == a else a
        tb = f["where"] / f"clar-{other[-3:]}.tar.gz"
        clarification_response(f, other, tb)
        rc, out, err = bale(f, "apply", "--json", str(tb))
        line = last_json(out)
        shape = relay_shape((line or {}).get("relay"))
        probe(labels[0], rc == 0 and (line or {}).get("outcome") == "clarification"
              and shape is not None and len(shape) == 1 and shape[0][0] == "planner"
              and "BALE EXCHANGE BEGIN" in shape[0][1] and printed(shape[0][1], err),
              f"apply exited {rc}; outcome {(line or {}).get('outcome')!r}; relay "
              f"{[(x, t[:60]) for x, t in shape] if shape else (line or {}).get('relay', 'absent')!r}")
        rc, out, err = bale(f, "status")
        other_lines = [ln for ln in out.splitlines() if other in ln]
        lock_lines = [ln for ln in out.splitlines() if lock in ln and other not in ln]
        probe(labels[1], rc == 0 and any(has_word(ln, "clarification") for ln in other_lines)
              and any(has_word(ln, "packed") for ln in lock_lines),
              f"status exited {rc}; lines naming {other}: {other_lines!r}; naming {lock}: {lock_lines!r}")

    # 3. A checkpoint changed since pack.
    f = fixture("checkpoint-change", checkpoint_rc=0)
    sid, why = pack(f)
    labels = ("a changed checkpoint still refuses in human mode, exit 1",
              "apply --json refuses a changed checkpoint with one line, outcome checkpoint-change-refused",
              "the refusal line carries the paste-ready accept line, and running it applies",
              "the dossier records the refusal as checkpoint-change-refused",
              "bale contract lists checkpoint-change-refused among apply's outcomes")
    if not sid:
        fail_all(labels, why)
    else:
        (f["repo"] / "check.sh").write_text("#!/usr/bin/env bash\n# amended\nexit 0\n",
                                            encoding="utf-8")
        run(["git", "commit", "-q", "-am", "amend the checkpoint"], cwd=f["repo"], env=f["env"],
            check=True)
        tb = f["where"] / f"resp-{sid[-3:]}.tar.gz"
        normal_response(f, sid, tb)
        rc_h, out_h, err_h = bale(f, "apply", str(tb))
        probe(labels[0], rc_h == 1 and last_json(out_h) is None and has_word(err_h, "checkpoint"),
              f"apply exited {rc_h}; stderr {err_h[-200:]!r}")
        rc, out, err = bale(f, "apply", "--json", str(tb))
        line = last_json(out)
        probe(labels[1], rc == 1 and line is not None and len(out.strip().splitlines()) == 1
              and line.get("outcome") == REFUSED and line.get("relay") == [],
              f"apply exited {rc}; stdout {out[-300:]!r}")
        cc = (line or {}).get("checkpoint_change")
        accept = cc.get("accept") if isinstance(cc, dict) else None
        ok3, detail3 = False, f"checkpoint_change {cc!r}"
        if isinstance(accept, str) and "--accept-checkpoint-change" in accept:
            try:
                words = shlex.split(accept)
            except ValueError:
                words = []
            if words and words[0] == "bale" and str(tb) in words:
                rc2, out2, err2 = run(f["bale"] + words[1:], cwd=f["repo"], env=f["env"])
                body = (f["repo"] / "hello.txt").read_text(encoding="utf-8", errors="replace")
                ok3 = rc2 == 0 and body == "hello, oracle\n"
                detail3 = f"the accept line {accept!r} exited {rc2}: {(err2 or out2)[-200:]!r}"
            else:
                detail3 = f"the accept line {accept!r} is not a bale line naming the tarball"
        probe(labels[2], ok3, detail3)
        d = dossier(f, sid)
        outs = [x.get("outcome") for x in ((d or {}).get("attempts") or [])]
        probe(labels[3], outs.count(REFUSED) >= 2 and "rejected" not in outs,
              f"dossier outcomes {outs!r}")
        rc_k, out_k, _ = bale(f, "contract", "--json")
        ck = last_json(out_k) if rc_k == 0 else None
        voc = ((ck or {}).get("vocabularies") or {})
        probe(labels[4], REFUSED in ((voc.get("apply-outcome") or {}).get("values") or [])
              and REFUSED in ((voc.get("telemetry-outcome") or {}).get("values") or []),
              f"apply-outcome {(voc.get('apply-outcome') or {}).get('values')!r}")
        apply_outcomes = (voc.get("apply-outcome") or {}).get("values") or []

        # 4. Help: every --json verb points at bale contract; no stale list.
        stale = []
        for verb in JSON_VERBS:
            rc_v, out_v, err_v = bale(f, verb, "--help")
            text = " ".join((out_v + err_v).split())
            if rc_v != 0 or "bale contract" not in text:
                stale.append(f"{verb}: no 'bale contract' (exit {rc_v})")
            if verb in ("apply", "retry"):
                for run_ in outcome_runs(text):
                    if "base-drift-refused" in run_ and REFUSED not in run_:
                        stale.append(f"{verb}: lists outcomes {'|'.join(run_)} without {REFUSED}")
            if verb == "pack" and "session_dir, context_files" in text:
                stale.append("pack: still lists six keys")
        probe("every --json verb's help points at bale contract, and none keeps a stale list",
              not stale and bool(apply_outcomes), "; ".join(stale) or "no apply outcomes read")

    # 5. A newer numbered copy beside an absolute name.
    f = fixture("absolute-twin")
    sid, why = pack(f)
    label = "bale apply of an absolute name says a newer numbered copy sits beside it, and applies the named file"
    if not sid:
        probe(label, False, why)
    else:
        inbox = f["where"] / "inbox"
        inbox.mkdir()
        plain = inbox / f"response-{sid}.tar.gz"
        twin = inbox / f"response-{sid} (1).tar.gz"
        normal_response(f, sid, plain, data=b"the named file\n", tag="plain")
        normal_response(f, sid, twin, data=b"the numbered copy\n", tag="twin")
        set_mtime(plain, 300)
        set_mtime(twin, 100)
        rc, out, err = bale(f, "apply", str(plain))
        text = out + "\n" + err
        body = (f["repo"] / "hello.txt").read_text(encoding="utf-8", errors="replace")
        probe(label, rc == 0 and twin.name in text and has_word(text, "newer")
              and body == "the named file\n",
              f"apply exited {rc}; hello.txt {body!r}; output {text[-300:]!r}")

    # 6. The tree's own files.
    crafter = TREE / "tools" / "craft_response.py"
    planner = TREE / "docs" / "PLANNER.md"
    if not crafter.is_file() or not planner.is_file():
        raise OracleError("the graded tree has no tools/craft_response.py or docs/PLANNER.md")
    ctext = crafter.read_text(encoding="utf-8", errors="replace")
    probe("tools/craft_response.py names no office-src", "office-src" not in ctext,
          f"{ctext.count('office-src')} mention(s)")
    ptext = planner.read_text(encoding="utf-8", errors="replace")
    hits = [ln.strip()[:80] for ln in ptext.splitlines() if has_word(ln, "office")]
    probe("docs/PLANNER.md names no office", not hits, f"lines {hits[:3]!r}")
    corpus = TREE / "tests" / "fixtures" / "stats_corpus"
    records = []
    if corpus.is_dir():
        for p in sorted(corpus.glob("*.json")):
            try:
                records.append(json.loads(p.read_text(encoding="utf-8")))
            except (OSError, ValueError):
                continue
    seen = era_keys(records)
    want = {"scope_kind", "bale_version", "claimed_checks", "clarification"}
    probe("the stats fixture corpus holds this era's keys: scope_kind, bale_version, claimed_checks, a clarification attempt",
          seen == want, f"found {sorted(seen)!r} in {len(records)} record(s)")

    rec_file = TREE / "claude" / "changelog" / "0.4.64.json"
    rec_ver = None
    if rec_file.is_file():
        try:
            rec_ver = json.loads(rec_file.read_text(encoding="utf-8")).get("version")
        except (ValueError, AttributeError):
            rec_ver = "unreadable"
    probe("release 0.4.64: bin/VERSION and claude/changelog/0.4.64.json",
          version == "0.4.64" and rec_ver == "0.4.64",
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
