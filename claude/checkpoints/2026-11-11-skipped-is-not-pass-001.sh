#!/usr/bin/env bash
# Blind checkpoint for bale-src session skipped-is-not-pass (v1).
#
# Authored blind, from the request's brief, before any implementation
# existed, by the planner sitting 2026-11-11-bale-src-slips-plan-sitting-003.
# The worker never reads, edits or declares this file (TARBALL.md 7).
#
# It grades outcomes only, in the tree it runs in (bale's staging root, the
# landed tree):
#   - the crafter's reconciliation epilogue tags a pass claim beside a skip,
#     or beside no recorded verdict, [DISAGREE], and leaves the other rows
#     as they were;
#   - a scratch apply, driven by this tree's own bin/bale in a throwaway repo
#     under /tmp, stays PASS on such a response, names each disagreeing check
#     in its walk and in the planner's relay, and says "1 of 4 checks ran";
#   - validation.sh finds the response's notes.md at .bale-notes.md in
#     staging, finds none when no notes.md ships, and the landing commits
#     none;
#   - docs/TARBALL.md 7.3 names .bale-notes.md, and the release is 0.4.57.
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
WORK = Path(tempfile.mkdtemp(prefix="bale-oracle-skip-"))

# The fixture's four claimed checks. Their labels and the notes text are
# chosen so that no fixture-authored text the probes read holds the word
# "disagree" or the phrase "checks ran".
ZETA = "zeta-ran check"           # claim pass, verdict pass
ETA = "eta-skipped check"         # claim pass, verdict skip
THETA = "theta-unrecorded check"  # claim pass, verdict missing
IOTA = "iota-untested check"      # claim untested, verdict skip
NOTES_BYTES = b"# notes\n\nA fixture notes page for the oracle.\n"

# The TARBALL.md 7.3 row shape, as the brief pins it unchanged.
ROW = re.compile(r"^\s+(?P<check>.+?):\s+claim=(?P<claim>\S+)"
                 r"\s+verdict=(?P<verdict>\S+)\s+\[(?P<tag>[^\]]+)\]\s*$")


# --- detectors (each one is exercised by a control before any probe) ---

def parse_rows(text):
    """The LAST 'claims vs verdict:' block's rows: {check: (claim, verdict, tag)}."""
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("claims vs verdict:"):
            start = i
    rows = {}
    if start is None:
        return rows
    for line in lines[start + 1:]:
        m = ROW.match(line)
        if not m:
            break
        rows[m.group("check").strip()] = (m.group("claim"), m.group("verdict"),
                                          "[" + m.group("tag").strip() + "]")
    return rows


def split_relay(text, sid):
    """(lines inside the planner relay block, lines outside every relay block)."""
    begin = f"=== RELAY BEGIN {sid} to planner ==="
    inside, outside = [], []
    state = None
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("=== RELAY BEGIN "):
            state = "planner" if s == begin else "other"
            continue
        if s.startswith("=== RELAY END "):
            state = None
            continue
        if state == "planner":
            inside.append(line)
        elif state is None:
            outside.append(line)
    return inside, outside


def names_disagreement(lines, label):
    """True when one line names the label and the word disagree."""
    return any(label in ln and "disagree" in ln.lower() for ln in lines)


def says_n_of_m(lines, n, m):
    pat = re.compile(rf"(?<![0-9]){n} of {m} checks ran\b")
    return any(pat.search(ln) for ln in lines)


def notes_hash_seen(log_text):
    """The value of the fixture validation.sh's last NOTES-SHA256 line, or None."""
    seen = None
    for ln in log_text.splitlines():
        if ln.startswith("NOTES-SHA256 "):
            seen = ln.split(" ", 1)[1].strip()
    return seen


def section_73(doc_text):
    """docs/TARBALL.md 7.3's text, heading line to the next ### heading, or None."""
    lines = doc_text.splitlines()
    for i, ln in enumerate(lines):
        if ln.startswith("### 7.3 "):
            body = [ln]
            for nxt in lines[i + 1:]:
                if nxt.startswith("### ") or nxt.startswith("## "):
                    break
                body.append(nxt)
            return "\n".join(body)
    return None


# --- controls: prove every detector on synthetic input; a miss exits 2 ---

def controls():
    block = ("noise\nclaims vs verdict:\n"
             "  a b: claim=pass      verdict=skip     [DISAGREE]\n"
             "  c:   claim=untested  verdict=skip     [n/a]\n\nafter\n")
    rows = parse_rows("claims vs verdict:\n  x: claim=fail verdict=fail [agree]\n\n" + block)
    want = {"a b": ("pass", "skip", "[DISAGREE]"), "c": ("untested", "skip", "[n/a]")}
    if rows != want:
        raise OracleError(f"control: parse_rows read {rows!r}")
    if parse_rows("no block here\n"):
        raise OracleError("control: parse_rows found rows where none are")
    relay = ("pre line\n=== RELAY BEGIN S to worker ===\nw1\n=== RELAY END S to worker ===\n"
             "=== RELAY BEGIN S to planner ===\np1\np2\n=== RELAY END S to planner ===\npost\n")
    inside, outside = split_relay(relay, "S")
    if inside != ["p1", "p2"] or outside != ["pre line", "post"]:
        raise OracleError(f"control: split_relay read {inside!r} / {outside!r}")
    if not names_disagreement(["x", "  eta check: Disagreement (skip)"], "eta check"):
        raise OracleError("control: names_disagreement missed a naming line")
    if names_disagreement(["eta check claim=pass", "disagreements: none"], "eta check"):
        raise OracleError("control: names_disagreement matched across lines")
    if not says_n_of_m(["validation: 1 of 4 checks ran (3 did not)"], 1, 4):
        raise OracleError("control: says_n_of_m missed the line")
    if says_n_of_m(["11 of 4 checks ran", "1 of 40 checks ran", "1 of 4 checks"], 1, 4):
        raise OracleError("control: says_n_of_m matched a wrong count")
    if notes_hash_seen("x\nNOTES-SHA256 absent\nNOTES-SHA256 abc\n") != "abc":
        raise OracleError("control: notes_hash_seen misread")
    if notes_hash_seen("nothing\n") is not None:
        raise OracleError("control: notes_hash_seen invented a value")
    doc = "## 7. V\n### 7.2 A\nnope\n### 7.3 Claim\nhas .bale-notes.md here\n### 7.4 L\nlater\n"
    s = section_73(doc)
    if s is None or ".bale-notes.md" not in s or "later" in s or "nope" in s:
        raise OracleError(f"control: section_73 read {s!r}")
    if section_73("### 7.30 X\n") is not None:
        raise OracleError("control: section_73 matched the wrong heading")


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


FIXTURE_VALIDATION = """#!/usr/bin/env bash
if [ -f .bale-notes.md ]; then
  echo "NOTES-SHA256 $(sha256sum .bale-notes.md | cut -d' ' -f1)"
else
  echo "NOTES-SHA256 absent"
fi
echo "[PASS] zeta-ran check"
echo "[SKIP] eta-skipped check: fixture tool not found"
echo "[SKIP] iota-untested check: fixture tool not found"
echo "claims vs verdict:"
echo "  zeta-ran check:         claim=pass      verdict=pass     [agree]"
echo "  eta-skipped check:      claim=pass      verdict=skip     [DISAGREE]"
echo "  theta-unrecorded check: claim=pass      verdict=missing  [DISAGREE]"
echo "  iota-untested check:    claim=untested  verdict=skip     [n/a]"
exit 0
"""


def scenario(name, *, with_notes):
    """One fresh scratch install and repo per scenario; returns what bale did."""
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
    # The scratch apply runs unconfined by the scratch repo's own config: its
    # confinement is not what is graded, and a nested-sandbox fault must never
    # read as a verdict. The checkpoint itself still runs confined by bale.
    (repo / "bale.toml").write_text("[sandbox]\nenabled = false\n", encoding="utf-8")
    run(["git", "add", "-A"], cwd=repo, env=env, check=True)
    run(["git", "commit", "-q", "-m", "init"], cwd=repo, env=env, check=True)
    bale = [sys.executable, "-B", str(install / "bin" / "bale")]
    res = {"name": name, "ok": False, "why": "", "sid": None}
    rc, out, err = run(bale + ["pack", "oracle fixture goal", "--slug", "oracle-fixture",
                               "--include", "hello.txt", "--no-readme", "--json"],
                       cwd=repo, env=env)
    if rc != 0:
        res["why"] = f"the scratch pack exited {rc}: {(err or out)[-300:]!r}"
        return res
    sid = None
    for ln in reversed(out.strip().splitlines()):
        try:
            sid = json.loads(ln).get("sid")
            break
        except (ValueError, AttributeError):
            continue
    if not sid:
        res["why"] = "the scratch pack's --json report named no sid"
        return res
    res["sid"] = sid
    rdir = where / f"response-{sid[-3:]}"
    (rdir / "files").mkdir(parents=True)
    data = b"hello, oracle\n"
    (rdir / "files" / "hello.txt").write_bytes(data)
    manifest = {
        "session_id": sid, "responds_to": sid, "corrects": None,
        "response_kind": "normal", "summary": "oracle fixture response",
        "changes": [{"path": "hello.txt", "action": "modified",
                     "reason": "fixture change", "size_bytes": len(data),
                     "sha256": hashlib.sha256(data).hexdigest()}],
        "deferred": [],
        "validation_will_run": [ZETA, ETA, THETA, IOTA],
        "claims": {ZETA: "pass", ETA: "pass", THETA: "pass", IOTA: "untested"},
    }
    (rdir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (rdir / "apply.sh").write_text("#!/usr/bin/env bash\nexit 0\n", encoding="utf-8")
    (rdir / "validation.sh").write_text(FIXTURE_VALIDATION, encoding="utf-8")
    if with_notes:
        (rdir / "notes.md").write_bytes(NOTES_BYTES)
    tarball = where / f"response-{sid[-3:]}.tar.gz"
    try:
        with tarfile.open(tarball, "w:gz") as tf:
            tf.add(str(rdir), arcname=rdir.name)
    except OSError as e:
        raise OracleError(f"could not tar the fixture response: {e}")
    rc, out, err = run(bale + ["apply", str(tarball)], cwd=repo, env=env)
    res.update(apply_rc=rc, text=out + "\n" + err)
    log = repo / ".bale" / "logs" / f"{sid}.log"
    res["log"] = log.read_text(encoding="utf-8", errors="replace") if log.is_file() else ""
    tele = repo / "claude" / "telemetry" / f"{sid}.json"
    try:
        res["telemetry"] = json.loads(tele.read_text(encoding="utf-8")) if tele.is_file() else None
    except ValueError:
        res["telemetry"] = None
    trc, tout, _ = run(["git", "rev-parse", "-q", "--verify", f"refs/tags/applied/{sid}"],
                       cwd=repo, env=env)
    res["tagged"] = trc == 0
    _, names, _ = run(["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=repo, env=env,
                      check=True)
    res["landed"] = names.split()
    res["ok"] = True
    return res


def crafter_rows():
    """Run this tree's epilogue definitions over a synthetic manifest; return its rows."""
    where = WORK / "crafter"
    rdir = where / "response-001"
    rdir.mkdir(parents=True)
    env = base_env(make_home(where))
    rc, defs, err = run([sys.executable, "-I", "-B", str(TREE / "tools" / "craft_response.py"),
                         "--validation-epilogue", "--fragment", "definitions", str(rdir)],
                        cwd=where, env=env)
    if rc != 0:
        return None, f"the crafter's epilogue exited {rc}: {err[-300:]!r}"
    claims = {"a1 check": "pass", "b1 check": "pass", "c1 check": "pass",
              "d1 check": "untested", "f1 check": "pass", "g1 check": "unknown",
              "h1 check": "fail"}
    (where / ".bale-manifest.json").write_text(json.dumps({"claims": claims}), encoding="utf-8")
    script = (defs + "\n"
              'record_verdict "a1 check" pass\n'
              'record_verdict "b1 check" skip\n'
              'record_verdict "d1 check" skip\n'
              'record_verdict "f1 check" fail\n'
              'record_verdict "g1 check" pass\n'
              'record_verdict "h1 check" fail\n'
              "reconcile_claims\n")
    (where / "run.sh").write_text(script, encoding="utf-8")
    rc, out, err = run(["bash", str(where / "run.sh")], cwd=where, env=env)
    if rc != 0:
        return None, f"the epilogue's reconcile_claims exited {rc}: {err[-300:]!r}"
    return parse_rows(out), ""


# --- probes ---

results = []


def probe(label, ok, detail=""):
    results.append((label, bool(ok), detail))


def main():
    controls()
    rows, why = crafter_rows()

    def row_is(check, verdict, tag):
        if rows is None:
            return False, why
        got = rows.get(check)
        if got is None:
            return False, f"no row for {check!r} in the epilogue's block"
        return (got[1] == verdict and got[2] == tag,
                f"{check!r} printed verdict={got[1]} {got[2]}, wanted verdict={verdict} {tag}")

    ok, d = row_is("b1 check", "skip", "[DISAGREE]")
    probe("crafter epilogue tags a pass claim beside a skip [DISAGREE]", ok, d)
    ok, d = row_is("c1 check", "missing", "[DISAGREE]")
    probe("crafter epilogue tags a pass claim with no recorded verdict [DISAGREE]", ok, d)
    others = [row_is("a1 check", "pass", "[agree]"), row_is("f1 check", "fail", "[DISAGREE]"),
              row_is("h1 check", "fail", "[agree]"), row_is("d1 check", "skip", "[n/a]"),
              row_is("g1 check", "pass", "[n/a]")]
    probe("crafter epilogue keeps the agree, cross and no-prediction rows as they were",
          all(o for o, _ in others), "; ".join(d for o, d in others if not o))

    a = scenario("with-notes", with_notes=True)
    b = scenario("without-notes", with_notes=False)

    if not a["ok"]:
        for label in ("scratch apply stays PASS when a claimed check skipped",
                      "apply walk names each disagreeing check",
                      "planner relay names each disagreeing check",
                      "planner relay says 1 of 4 checks ran",
                      "record keeps disagree for the skipped and unrecorded pass claims",
                      "validation.sh reads the response's notes.md at .bale-notes.md",
                      "the landing commits no .bale-notes.md"):
            probe(label, False, a["why"])
    else:
        tele = a["telemetry"] or {}
        attempts = tele.get("attempts") or [{}]
        val = attempts[-1].get("validation") or {}
        probe("scratch apply stays PASS when a claimed check skipped",
              a["apply_rc"] == 0 and a["tagged"] and val.get("state") == "PASS",
              f"apply exit {a['apply_rc']}, applied tag {'present' if a['tagged'] else 'absent'}, "
              f"recorded state {val.get('state')!r}")
        inside, outside = split_relay(a["text"], a["sid"])
        missing_walk = [c for c in (ETA, THETA) if not names_disagreement(outside, c)]
        probe("apply walk names each disagreeing check", not missing_walk,
              f"no walk line names {missing_walk} as a disagreement")
        if not inside:
            probe("planner relay names each disagreeing check", False,
                  "no planner relay block in the apply output")
            probe("planner relay says 1 of 4 checks ran", False,
                  "no planner relay block in the apply output")
        else:
            missing_relay = [c for c in (ETA, THETA) if not names_disagreement(inside, c)]
            probe("planner relay names each disagreeing check", not missing_relay,
                  f"no relay line names {missing_relay} as a disagreement")
            probe("planner relay says 1 of 4 checks ran", says_n_of_m(inside, 1, 4),
                  "no relay line reads '1 of 4 checks ran'")
        cv = val.get("claim_verdict") or {}
        got = {c: (cv.get(c) or {}).get("agreement") for c in (ZETA, ETA, THETA, IOTA)}
        probe("record keeps disagree for the skipped and unrecorded pass claims",
              got == {ZETA: "agree", ETA: "disagree", THETA: "disagree", IOTA: "n/a"},
              f"claim_verdict agreements {got}")
        want = hashlib.sha256(NOTES_BYTES).hexdigest()
        seen = notes_hash_seen(a["log"])
        probe("validation.sh reads the response's notes.md at .bale-notes.md",
              seen == want, f"validation.sh saw {seen!r} there, wanted the notes' sha256 {want[:12]}")
        probe("the landing commits no .bale-notes.md",
              not any(Path(n).name in (".bale-notes.md", ".bale-manifest.json") for n in a["landed"]),
              f"landed tree holds {[n for n in a['landed'] if n.startswith('.bale-')]}")

    if not b["ok"]:
        probe("no notes.md shipped: no .bale-notes.md in staging", False, b["why"])
    else:
        seen = notes_hash_seen(b["log"])
        probe("no notes.md shipped: no .bale-notes.md in staging", seen == "absent",
              f"validation.sh saw {seen!r}")

    doc = TREE / "docs" / "TARBALL.md"
    sec = section_73(doc.read_text(encoding="utf-8")) if doc.is_file() else None
    probe("docs/TARBALL.md 7.3 names .bale-notes.md",
          sec is not None and ".bale-notes.md" in sec,
          "no 7.3 section" if sec is None else "7.3 does not name .bale-notes.md")

    ver_file = TREE / "bin" / "VERSION"
    ver = ver_file.read_text(encoding="utf-8").strip() if ver_file.is_file() else None
    rec_file = TREE / "claude" / "changelog" / "0.4.57.json"
    rec_ver = None
    if rec_file.is_file():
        try:
            rec_ver = json.loads(rec_file.read_text(encoding="utf-8")).get("version")
        except (ValueError, AttributeError):
            rec_ver = "unreadable"
    probe("release 0.4.57: bin/VERSION and claude/changelog/0.4.57.json",
          ver == "0.4.57" and rec_ver == "0.4.57",
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
