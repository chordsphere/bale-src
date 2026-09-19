#!/usr/bin/env bash
# Blind checkpoint v1 — board 110, held admissions stamped at HOLD.
# Authored at the desk of 2026-09-19-continue-plan-006 from the request,
# before any implementation exists. Outcome contracts only: every probe
# drives the real CLI in a fresh scratch repo (one per scenario) through
# tests/harness.py's sandbox makers and reads what an operator would read.
# Writes: a mktemp directory under /tmp, nothing else.
set -uo pipefail
command -v python3 >/dev/null 2>&1 || { echo "checkpoint: python3 not found"; exit 2; }
[ -f tests/harness.py ] || { echo "checkpoint: tests/harness.py not found (cwd must be the staged tree)"; exit 2; }
WORK="$(mktemp -d /tmp/cp110.XXXXXX)" || exit 2
trap 'rm -rf "$WORK"' EXIT
echo "checkpoint writes only under: $WORK"
CP110_WORK="$WORK" python3 - <<'PY'
import hashlib, json, os, re, shlex, subprocess, sys, traceback
from pathlib import Path

STAGED = Path.cwd()
sys.path.insert(0, str(STAGED / "tests"))
try:
    import harness as H
except Exception:
    traceback.print_exc()
    print("checkpoint: tests/harness.py did not import")
    sys.exit(2)

WORK = Path(os.environ["CP110_WORK"])
FAILED = []

def verdict(ok, label, detail=""):
    print(("[PASS] " if ok else "[FAIL] ") + label)
    if not ok:
        FAILED.append(label)
        if detail:
            print("       " + detail.replace("\n", "\n       "))

FAILING_ORACLE = '#!/usr/bin/env bash\necho "[FAIL] fixture-oracle-probe"\nexit 1\n'
PASSING_ORACLE = '#!/usr/bin/env bash\necho "[PASS] fixture-oracle-probe"\nexit 0\n'
PASSING_VALIDATION = '#!/usr/bin/env bash\necho "[PASS] fixture check"\nexit 0\n'
ADMITTED = "extra dir/new file.txt"   # out of forecast, and needs quoting

class Scenario:
    """One fresh install + repo + HOME per scenario; nothing is shared."""
    def __init__(self, name):
        self.tmp = WORK / name
        self.tmp.mkdir()
        self.home = H.make_sandbox_home(self.tmp)
        self.install = H.make_install(self.tmp)
        self.repo = H.make_repo(self.tmp, self.home)
        self.env = H.bale_env(self.home, self.tmp)
        genv = H.git_env(self.home)
        H.run_checked(["git", "config", "user.name", "Checkpoint"], cwd=self.repo, env=genv)
        H.run_checked(["git", "config", "user.email", "checkpoint@example.invalid"], cwd=self.repo, env=genv)
        # The checkpoint already runs confined; the scratch repo's own
        # applies run unconfined rather than nesting namespaces.
        (self.repo / "bale.toml").write_text(
            '[validation]\nbase = "claude/checkpoints/{sid}.sh"\n\n'
            '[sandbox]\nenabled = false\n', encoding="utf-8")
        self.genv = genv

    def bale(self, *args):
        return H.run_bale(self.install, list(args), cwd=self.repo, env=self.env)

    def pack_with_failing_oracle(self, slug):
        src = self.tmp / f"oracle-{slug}-v0.sh"
        src.write_text(FAILING_ORACLE, encoding="utf-8")
        r = self.bale("pack", f"checkpoint fixture goal {slug}", "--slug", slug,
                      "--no-readme", "--include", "hello.txt",
                      "--checkpoint-file", str(src))
        if r.returncode != 0:
            raise RuntimeError(f"fixture pack failed:\n{r.stdout}\n{r.stderr}")
        root = self.repo / ".bale" / "sessions"
        sids = [d.name for d in root.iterdir() if (d / "open").is_file() and f"-{slug}-" in d.name]
        if len(sids) != 1:
            raise RuntimeError(f"expected one open session for {slug}: {sids}")
        return sids[0]

    def response(self, sid, entries):
        rdir = H.build_response_dir(self.tmp / "delivery dir", sid,
                                    summary="checkpoint fixture response",
                                    entries=entries,
                                    validation_sh=PASSING_VALIDATION)
        return H.tar_response_dir(rdir)

def card_of(stdout):
    at = stdout.rfind("[HOLD]")
    return stdout[at:] if at >= 0 else ""

def fixture_rungs(text):
    """The retry lines that carry --accept-checkpoint-change: the
    fixture-defect rung, on the card or ending the amend report."""
    out = []
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("bale retry ") and "--accept-checkpoint-change" in s:
            out.append(s)
    return out

def restates(line, path):
    try:
        toks = shlex.split(line)
    except ValueError:
        return False
    return any(a == "--allow-out-of-scope" and b == path
               for a, b in zip(toks, toks[1:]))

def amend(sc, sid, name):
    body = PASSING_ORACLE
    f = sc.tmp / name
    f.write_text(body, encoding="utf-8")
    sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
    return sc.bale("amend-checkpoint", str(f), "--sha256", sha, "--sid", sid)

def scenario_admitted():
    sc = Scenario("admitted")
    sid = sc.pack_with_failing_oracle("cp110a")
    tarball = sc.response(sid, [
        {"path": "hello.txt", "action": "modified", "reason": "fixture", "data": b"landed by the fixture rung\n"},
        {"path": ADMITTED, "action": "created", "reason": "fixture, out of forecast", "data": b"admitted\n"},
    ])
    held = sc.bale("apply", str(tarball), "--allow-out-of-scope", ADMITTED)
    card = card_of(held.stdout)
    if held.returncode != 1 or not card:
        raise RuntimeError(f"fixture did not reach HOLD (exit {held.returncode}):\n{held.stdout}\n{held.stderr}")
    rungs = fixture_rungs(card)
    verdict(len(rungs) >= 1 and all(restates(r, ADMITTED) for r in rungs) and
            True,
            "HOLD card: the fixture-defect retry rung re-states the held apply's out-of-forecast admission",
            "rungs seen: " + repr(rungs))
    am = amend(sc, sid, "amendment-cp110a-v1.sh")
    if am.returncode != 0:
        raise RuntimeError(f"fixture amend failed:\n{am.stdout}\n{am.stderr}")
    lines = [ln.strip() for ln in am.stdout.splitlines() if ln.strip()]
    successor = lines[-1] if lines else ""
    verdict(successor.startswith("bale retry ") and restates(successor, ADMITTED),
            "amend-checkpoint report: its closing retry line re-states the same admission",
            "closing line: " + repr(successor))
    verdict(bool(rungs) and successor in rungs,
            "the card's fixture-defect rung and amend-checkpoint's closing line are the same line",
            f"card: {rungs!r}\namend: {successor!r}")
    try:
        argv = shlex.split(successor)
    except ValueError:
        argv = []
    landed = None
    if argv[:2] == ["bale", "retry"]:
        landed = sc.bale(*argv[1:])
    show = subprocess.run(["git", "show", f"main:{ADMITTED}"], cwd=sc.repo,
                          env=sc.genv, capture_output=True, text=True)
    verdict(landed is not None and landed.returncode == 0 and show.returncode == 0
            and show.stdout == "admitted\n",
            "pasting amend-checkpoint's closing line as printed lands the held tarball on main",
            "" if landed is None else f"exit {landed.returncode}\n{landed.stdout[-1200:]}\n{landed.stderr[-600:]}")

def scenario_plain():
    sc = Scenario("plain")
    sid = sc.pack_with_failing_oracle("cp110b")
    tarball = sc.response(sid, [
        {"path": "hello.txt", "action": "modified", "reason": "fixture", "data": b"no admissions needed\n"},
    ])
    held = sc.bale("apply", str(tarball))
    card = card_of(held.stdout)
    if held.returncode != 1 or not card:
        raise RuntimeError(f"fixture did not reach HOLD (exit {held.returncode}):\n{held.stdout}\n{held.stderr}")
    rungs = fixture_rungs(card)
    want = ["bale", "retry", str(tarball.resolve()), "--accept-checkpoint-change", "--sid", sid]
    got = [shlex.split(r) for r in rungs]
    verdict(got == [want],
            "a HOLD that exercised no admission composes the fixture-defect rung with no admission flags",
            f"want {want!r}\ngot  {got!r}")

def version_probe():
    ver = (STAGED / "bin" / "VERSION").read_text(encoding="utf-8").strip()
    m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", ver)
    newer = bool(m) and tuple(map(int, m.groups())) > (0, 4, 36)
    rec = STAGED / "claude" / "changelog" / f"{ver}.json"
    ok = False
    if newer and rec.is_file():
        try:
            ok = json.loads(rec.read_text(encoding="utf-8")).get("version") == ver
        except ValueError:
            ok = False
    verdict(ok, "bin/VERSION moved past 0.4.36 and claude/changelog carries a record naming that version",
            f"bin/VERSION={ver!r}; record present: {rec.is_file()}")

errored = False
for fn in (scenario_admitted, scenario_plain, version_probe):
    try:
        fn()
    except Exception:
        errored = True
        print(f"checkpoint: scenario {fn.__name__} errored before its probes could run")
        traceback.print_exc()
if errored:
    sys.exit(2)
sys.exit(1 if FAILED else 0)
PY
rc=$?
exit $rc
