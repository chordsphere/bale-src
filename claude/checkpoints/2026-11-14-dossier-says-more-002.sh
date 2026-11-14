#!/usr/bin/env bash
# Blind checkpoint for bale-src session dossier-says-more (v1).
#
# Authored blind, from the request's brief, before any implementation
# existed, by the planner sitting 2026-11-11-bale-src-slips-plan-sitting-003.
# The worker never reads, edits or declares this file (TARBALL.md 7).
#
# It grades outcomes only, in the tree it runs in (bale's staging root, the
# landed tree), driving this tree's own bin/bale in throwaway repos under
# /tmp and reading bale stats --json and bale stats --sid SID --json:
#   - a session packed --read-only reads read_only true while in flight,
#     on its dossier and in members.read_only;
#   - every attempt this bale writes carries its version, and the dossier
#     shows it per attempt and per session; a record from before carries
#     null;
#   - members.sessions lists every session in the corpus;
#   - the dossier carries the session's self-reported light_blocks and
#     paste_carried_rounds, null when none reports;
#   - every held attempt carries hold_class from its own exit codes
#     (checkpoint, validation, both, checkpoint-defect), records from
#     before included, and corpus.hold_classes counts them;
#   - an apply's derived claimed-checks counts ride on the dossier;
#   - the release is 0.4.62.
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
WORK = Path(tempfile.mkdtemp(prefix="bale-oracle-dos-"))

ZETA, ETA, THETA, IOTA = ("zeta-ran check", "eta-skipped check",
                          "theta-unrecorded check", "iota-untested check")

# The keys a telemetry record carried before this release, at each level
# the dossier reads (bale-src 0.4.59's records). Stripping a record written
# by this tree to these keys gives a record as an earlier release wrote it.
PRE_ENVELOPE = {"record_version", "session_id", "created_at", "updated_at",
                "outcome", "attempts"}
PRE_ATTEMPT = {"at", "base_drift_overrides", "bundle", "cause", "change_paths",
               "checkpoint", "clarification", "closure_reason", "command",
               "corrects", "cost", "diagnostics", "feedback", "log",
               "network_grant_exercised", "outcome", "overridden_path_sources",
               "overridden_paths", "provenance", "required_check_overrides",
               "sandbox_confined", "sandbox_escaped", "sandbox_off_source",
               "scope", "scope_kind", "superseded_by", "swept_by", "tarball",
               "validation"}
PRE_VALIDATION = {"claim_verdict", "claims", "exit_code", "reconciliation_parsed",
                  "state", "validation_will_run"}
PRE_CHECKPOINT = {"configured", "state", "exit_code", "script", "stamp_matched",
                  "failed_probes"}
PRE_PROVENANCE = {"work_class", "packer", "packed_at"}


# --- detectors (each one is exercised by a control before any probe) ---

def as_pre_release(record, new_sid):
    """The record stripped to the keys an earlier release wrote, renamed."""
    out = {k: v for k, v in record.items() if k in PRE_ENVELOPE}
    out["session_id"] = new_sid
    attempts = []
    for a in record.get("attempts") or []:
        b = {k: v for k, v in a.items() if k in PRE_ATTEMPT}
        if isinstance(b.get("validation"), dict):
            b["validation"] = {k: v for k, v in b["validation"].items() if k in PRE_VALIDATION}
        if isinstance(b.get("checkpoint"), dict):
            b["checkpoint"] = {k: v for k, v in b["checkpoint"].items() if k in PRE_CHECKPOINT}
        if isinstance(b.get("provenance"), dict):
            b["provenance"] = {k: v for k, v in b["provenance"].items() if k in PRE_PROVENANCE}
        attempts.append(b)
    out["attempts"] = attempts
    return out


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


def nonzero(counts):
    """A class-count mapping with its zero entries dropped; None if not a mapping."""
    if not isinstance(counts, dict):
        return None
    return {k: v for k, v in counts.items() if v}


# --- controls: prove every detector on synthetic input; a miss exits 2 ---

def controls():
    rec = {"record_version": 1, "session_id": "a", "new_top": 1, "attempts": [
        {"outcome": "held", "bale_version": "9", "hold_class": "x",
         "validation": {"state": "HOLD", "exit_code": 1, "claimed_checks": {}},
         "checkpoint": {"state": "PASS", "exit_code": 0, "extra": 1},
         "provenance": {"work_class": "w", "packer": "p", "packed_at": "t", "bale_version": "9"}}]}
    got = as_pre_release(rec, "b")
    want = {"record_version": 1, "session_id": "b", "attempts": [
        {"outcome": "held", "validation": {"state": "HOLD", "exit_code": 1},
         "checkpoint": {"state": "PASS", "exit_code": 0},
         "provenance": {"work_class": "w", "packer": "p", "packed_at": "t"}}]}
    if got != want:
        raise OracleError(f"control: as_pre_release made {got!r}")
    if rec["session_id"] != "a" or "bale_version" not in rec["attempts"][0]:
        raise OracleError("control: as_pre_release changed its input")
    if last_json('[bale] x\n{"a": 1}\n{"b": 2}\nnot json\n') != {"b": 2}:
        raise OracleError("control: last_json misread")
    if last_json("[1, 2]\nnope\n") is not None:
        raise OracleError("control: last_json took a non-object")
    if nonzero({"a": 0, "b": 2}) != {"b": 2} or nonzero(None) is not None:
        raise OracleError("control: nonzero misread")


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




def fixture(name, *, checkpoint_rc=None):
    """A scratch install and committed repo; with checkpoint_rc, a committed
    check.sh exiting it, named as the repo's [validation] base."""
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
    toml = "[sandbox]\nenabled = false\n"
    if checkpoint_rc is not None:
        (repo / "check.sh").write_text(f"#!/usr/bin/env bash\nexit {checkpoint_rc}\n",
                                       encoding="utf-8")
        toml += "\n[validation]\nbase = \"check.sh\"\n"
    (repo / "bale.toml").write_text(toml, encoding="utf-8")
    run(["git", "add", "-A"], cwd=repo, env=env, check=True)
    run(["git", "commit", "-q", "-m", "init"], cwd=repo, env=env, check=True)
    return {"where": where, "env": env, "repo": repo,
            "bale": [sys.executable, "-B", str(install / "bin" / "bale")]}


def pack(f, *extra):
    rc, out, err = run(f["bale"] + ["pack", "oracle fixture goal", "--slug", "oracle-fixture",
                                    "--include", "hello.txt", "--no-readme", "--json", *extra],
                       cwd=f["repo"], env=f["env"])
    report = last_json(out) if rc == 0 else None
    sid = report.get("sid") if report else None
    return sid, ("" if sid else f"the scratch pack exited {rc}: {(err or out)[-300:]!r}")


FEEDBACK = {
    "mechanical": {"response_kind": "normal", "schema_valid": True,
                   "mirror_agreement": {"changes_to_files": True, "files_to_changes": True},
                   "claims_subset": True},
    "self_reported": {"assumptions": [], "judgment_calls": [], "budget_pressure": "none",
                      "includes_missing": [], "compaction_occurred": {"occurred": False},
                      "light_blocks": 2, "paste_carried_rounds": 1},
}

BLOCK_FOUR = ("echo 'claims vs verdict:'\n"
              "echo '  zeta-ran check:         claim=pass      verdict=pass     [agree]'\n"
              "echo '  eta-skipped check:      claim=pass      verdict=skip     [DISAGREE]'\n"
              "echo '  theta-unrecorded check: claim=pass      verdict=missing  [DISAGREE]'\n"
              "echo '  iota-untested check:    claim=untested  verdict=skip     [n/a]'\n")


def respond(f, sid, *, validation_rc):
    """Apply a one-file response with four claimed checks; (rc, text)."""
    rdir = f["where"] / f"response-{sid[-3:]}"
    (rdir / "files").mkdir(parents=True)
    data = b"hello, oracle\n"
    (rdir / "files" / "hello.txt").write_bytes(data)
    manifest = {
        "session_id": sid, "responds_to": sid, "corrects": None, "response_kind": "normal",
        "summary": "oracle fixture response",
        "changes": [{"path": "hello.txt", "action": "modified", "reason": "fixture change",
                     "size_bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}],
        "deferred": [], "validation_will_run": [ZETA, ETA, THETA, IOTA],
        "claims": {ZETA: "pass", ETA: "pass", THETA: "pass", IOTA: "untested"},
        "feedback": FEEDBACK,
    }
    (rdir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (rdir / "apply.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (rdir / "validation.sh").write_text(
        "#!/usr/bin/env bash\necho '[PASS] zeta-ran check'\n" + BLOCK_FOUR +
        f"exit {validation_rc}\n", encoding="utf-8")
    tarball = f["where"] / f"{rdir.name}.tar.gz"
    try:
        with tarfile.open(tarball, "w:gz") as tf:
            tf.add(str(rdir), arcname=rdir.name)
    except OSError as e:
        raise OracleError(f"could not tar the fixture response: {e}")
    rc, out, err = run(f["bale"] + ["apply", str(tarball)], cwd=f["repo"], env=f["env"])
    return rc, out + "\n" + err


def dossier(f, sid):
    rc, out, err = run(f["bale"] + ["stats", "--sid", sid, "--json"], cwd=f["repo"], env=f["env"])
    d = last_json(out) if rc == 0 else None
    return d if isinstance(d, dict) and d.get("found") else None


def aggregate(f):
    rc, out, err = run(f["bale"] + ["stats", "--json"], cwd=f["repo"], env=f["env"])
    return last_json(out) if rc == 0 else None


results = []


def probe(label, ok, detail=""):
    results.append((label, bool(ok), detail))


def version_of_tree():
    v = TREE / "bin" / "VERSION"
    return v.read_text(encoding="utf-8").strip() if v.is_file() else None


def main():
    controls()
    version = version_of_tree()

    # 1. A read-only session in flight, and a plain one beside it.
    f = fixture("read-only")
    ro, why_ro = pack(f, "--read-only")
    plain, why_plain = pack(f)
    labels = ("a session packed --read-only reads read_only true on its dossier while in flight",
              "members.read_only names the in-flight read-only session, and not a plain one",
              "members.sessions lists every session in the corpus",
              "a session with no self-report reads null light_blocks and paste_carried_rounds")
    if not ro or not plain:
        for label in labels:
            probe(label, False, why_ro or why_plain)
    else:
        d_ro, d_plain, agg = dossier(f, ro), dossier(f, plain), aggregate(f)
        probe(labels[0], d_ro is not None and d_ro["record"].get("read_only") is True
              and d_plain is not None and d_plain["record"].get("read_only") is False,
              f"read-only {None if d_ro is None else d_ro['record'].get('read_only')!r}, "
              f"plain {None if d_plain is None else d_plain['record'].get('read_only')!r}")
        members = (agg or {}).get("members") or {}
        probe(labels[1], ro in (members.get("read_only") or [])
              and plain not in (members.get("read_only") or []),
              f"members.read_only {members.get('read_only')!r}")
        probe(labels[2], members.get("sessions") == sorted([ro, plain]),
              f"members.sessions {members.get('sessions')!r}")
        sr = (d_plain or {}).get("record", {}).get("self_reported")
        probe(labels[3], sr == {"light_blocks": None, "paste_carried_rounds": None},
              f"record.self_reported {sr!r}")

    # 2. An applied session: version, self-report, claimed checks.
    f = fixture("applied")
    sid, why = pack(f)
    labels = ("every attempt this bale writes carries its version on the dossier",
              "the dossier's record carries the packing bale's version",
              "the dossier carries the session's self-reported counts",
              "the applied attempt's dossier carries its derived claimed-checks counts",
              "an applied attempt carries hold_class null")
    if not sid:
        for label in labels:
            probe(label, False, why)
    else:
        rc, text = respond(f, sid, validation_rc=0)
        d = dossier(f, sid)
        if rc != 0 or d is None:
            for label in labels:
                probe(label, False, f"apply exited {rc}; dossier {'found' if d else 'missing'}: {text[-300:]!r}")
        else:
            vs = [a.get("bale_version") for a in d["attempts"]]
            probe(labels[0], bool(vs) and all(v == version for v in vs),
                  f"attempt versions {vs!r}, tree {version!r}")
            probe(labels[1], d["record"].get("bale_version") == version,
                  f"record.bale_version {d['record'].get('bale_version')!r}")
            sr = d["record"].get("self_reported")
            probe(labels[2], sr == {"light_blocks": 2, "paste_carried_rounds": 1},
                  f"record.self_reported {sr!r}")
            last = d["attempts"][-1]
            cc = (last.get("validation") or {}).get("claimed_checks")
            probe(labels[3], cc == {"claimed": 4, "ran": 1, "disagreements": sorted([ETA, THETA])},
                  f"validation.claimed_checks {cc!r}")
            probe(labels[4], "hold_class" in last and last["hold_class"] is None,
                  f"hold_class {'absent' if 'hold_class' not in last else repr(last['hold_class'])}")

    # 3. The four HOLD classes, each in its own repo.
    for name, validation_rc, checkpoint_rc, want in (
            ("hold-validation", 1, None, "validation"),
            ("hold-checkpoint", 0, 1, "checkpoint"),
            ("hold-both", 1, 1, "both"),
            ("hold-defect", 0, 2, "checkpoint-defect")):
        f = fixture(name, checkpoint_rc=checkpoint_rc)
        sid, why = pack(f)
        label = f"a HOLD from {name[5:]} reads hold_class {want} on the dossier"
        agg_label = f"corpus.hold_classes counts the {want} HOLD"
        if not sid:
            probe(label, False, why)
            probe(agg_label, False, why)
            continue
        rc, text = respond(f, sid, validation_rc=validation_rc)
        d = dossier(f, sid)
        last = d["attempts"][-1] if d else {}
        probe(label, rc == 1 and last.get("outcome") == "held" and last.get("hold_class") == want,
              f"apply exited {rc}; outcome {last.get('outcome')!r}, hold_class {last.get('hold_class')!r}")
        counts = nonzero(((aggregate(f) or {}).get("corpus") or {}).get("hold_classes"))
        probe(agg_label, counts == {want: 1}, f"corpus.hold_classes {counts!r}")
        if name == "hold-validation" and d is not None:
            # A record as an earlier release wrote it, beside the real one.
            tele = f["repo"] / "claude" / "telemetry" / f"{sid}.json"
            try:
                record = json.loads(tele.read_text(encoding="utf-8"))
            except (OSError, ValueError) as e:
                raise OracleError(f"could not read the scratch telemetry record: {e}")
            old_sid = sid[:-3] + "900"
            (tele.parent / f"{old_sid}.json").write_text(
                json.dumps(as_pre_release(record, old_sid), indent=2) + "\n", encoding="utf-8")
            old = dossier(f, old_sid)
            labels_old = ("a record from before this release reads bale_version null",
                          "a held attempt from before this release still reads its hold_class",
                          "a record from before this release reads claimed_checks null")
            if old is None:
                for lab in labels_old:
                    probe(lab, False, "the dossier did not find the stripped record")
            else:
                probe(labels_old[0], old["record"].get("bale_version", "absent") is None
                      and all(a.get("bale_version", "absent") is None for a in old["attempts"]),
                      f"record {old['record'].get('bale_version', 'absent')!r}, attempts "
                      f"{[a.get('bale_version', 'absent') for a in old['attempts']]!r}")
                probe(labels_old[1], old["attempts"][-1].get("hold_class") == "validation",
                      f"hold_class {old['attempts'][-1].get('hold_class')!r}")
                occ = (old["attempts"][-1].get("validation") or {}).get("claimed_checks", "absent")
                probe(labels_old[2], occ is None, f"claimed_checks {occ!r}")

    rec_file = TREE / "claude" / "changelog" / "0.4.62.json"
    rec_ver = None
    if rec_file.is_file():
        try:
            rec_ver = json.loads(rec_file.read_text(encoding="utf-8")).get("version")
        except (ValueError, AttributeError):
            rec_ver = "unreadable"
    probe("release 0.4.62: bin/VERSION and claude/changelog/0.4.62.json",
          version == "0.4.62" and rec_ver == "0.4.62",
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
