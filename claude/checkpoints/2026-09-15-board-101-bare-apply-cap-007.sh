#!/usr/bin/env bash
# Blind checkpoint — board row 101: bare `bale apply` bounded resolution.
# Authored blind at the 2026-09-15-continue-plan-004 sitting, from the
# request, before implementation. Runs in staging (cwd = staging root).
# Outcome contracts only. Exit 0 PASS / 1 HOLD / 2 errored.
set -u
if ! command -v python3 >/dev/null 2>&1; then echo "[SKIP] python3 not found"; exit 2; fi
[ -f tests/harness.py ] || { echo "[FAIL] tests/harness.py absent in staging"; exit 2; }

python3 - <<'PY'
import os, shutil, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, "tests")
from harness import (bale_env, build_response_dir, git_env, make_install,
                     make_repo, make_sandbox_home, run_bale, run_checked,
                     tar_response_dir)

results = []
def check(label, ok, detail=""):
    results.append((label, bool(ok), detail))

class Fx:
    """One fresh fixture per scenario. One open worker session plus an
    open read-only master beside it (the sitting shape)."""
    def __init__(self):
        self.td = tempfile.TemporaryDirectory(prefix="ckpt101-")
        self.tmp = Path(self.td.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        genv = git_env(self.home)
        (self.repo / "src").mkdir(); (self.repo / "src" / "a.txt").write_text("a\n")
        self.inbox = self.tmp / "inbox"; self.inbox.mkdir()
        (self.repo / "bale.toml").write_text(
            "[sandbox]\nenabled = false\n[apply]\nsearch_paths = [\"%s\"]\n"
            % str(self.inbox).replace("\\", "\\\\"))
        run_checked(["git", "add", "-A"], cwd=self.repo, env=genv)
        run_checked(["git", "commit", "-m", "fixture"], cwd=self.repo, env=genv)
        self.n = 0
    def pack(self, *extra):
        r = run_bale(self.install, ["pack", "row 101 oracle fixture", "--slug",
                                    "w", "--include", "src", "--no-readme", *extra],
                     cwd=self.repo, env=self.env)
        assert r.returncode == 0, r.stdout + r.stderr
        root = self.repo / ".bale" / "sessions"
        return sorted(d.name for d in root.iterdir() if (d / "open").is_file())[-1]
    def tarball(self, sid, name, mtime):
        """A valid response for `sid`, saved into the inbox under `name`
        with the given mtime (seconds)."""
        self.n += 1
        rdir = build_response_dir(self.tmp / f"r{self.n}", sid, summary="fx",
                                  entries=[{"path": "src/a.txt", "action": "modified",
                                            "reason": "fx", "data": f"{self.n}\n".encode()}])
        tb = tar_response_dir(rdir)
        dest = self.inbox / name
        shutil.copyfile(tb, dest)
        os.utime(dest, (mtime, mtime))
        return dest
    def bare(self):
        # Piped stdin: the resolver declines without a prompt and its
        # refusal names the resolved tarball; a non-resolution refuses
        # with its own text. Either way, nothing applies.
        return run_bale(self.install, ["apply"], cwd=self.repo, env=self.env)
    def close(self):
        self.td.cleanup()

T = 1_700_000_000
UNKNOWN = "2026-01-01-nobody-001"

# A. Non-conventional names never count, whatever they contain: the
#    newest file named response-*.tar.gz wins over newer junk.
fx = Fx()
try:
    sid = fx.pack("--write", "src")
    win = fx.tarball(sid, f"response-{sid}.tar.gz", T)
    for i, name in enumerate(["request-x.tar.gz", "junk.tar.gz", "request-y.tar.gz",
                              "notes.tar.gz", "request-z.tar.gz"]):
        fx.tarball(sid, name, T + 10 + i)
    r = fx.bare()
    out = r.stdout + r.stderr
    check("A: newest response-*.tar.gz resolves despite five newer non-conventional files",
          r.returncode == 1 and win.name in out and "junk.tar.gz" not in out.split("bale apply")[-1],
          out[-600:])
finally:
    fx.close()

# B. Fixed cap of two: when the two newest conventional files answer no
#    open session, bare apply refuses — even though an older one would.
fx = Fx()
try:
    sid = fx.pack("--write", "src")
    older = fx.tarball(sid, f"response-{sid}.tar.gz", T)
    ex1 = fx.tarball(UNKNOWN, f"response-{UNKNOWN}.tar.gz", T + 10)
    ex2 = fx.tarball(UNKNOWN, "response-002.tar.gz", T + 20)
    r = fx.bare()
    out = r.stdout + r.stderr
    check("B: two newer non-candidates exhaust the cap; the older candidate is not resolved",
          r.returncode == 1 and older.name not in out, out[-600:])
    check("B: the refusal names both examined files",
          ex1.name in out and ex2.name in out, out[-600:])
finally:
    fx.close()

# C. Second-newest wins when the newest conventional file is not a candidate.
fx = Fx()
try:
    sid = fx.pack("--write", "src")
    second = fx.tarball(sid, f"response-{sid}.tar.gz", T)
    fx.tarball(UNKNOWN, f"response-{UNKNOWN}.tar.gz", T + 10)
    r = fx.bare()
    out = r.stdout + r.stderr
    check("C: the second-newest conventional file resolves when the newest is not a candidate",
          r.returncode == 1 and second.name in out, out[-600:])
finally:
    fx.close()

# D. An exact mtime tie between two candidates still refuses.
fx = Fx()
try:
    sid = fx.pack("--write", "src")
    a = fx.tarball(sid, f"response-{sid}.tar.gz", T)
    b = fx.tarball(sid, "response-001.tar.gz", T)
    r = fx.bare()
    out = r.stdout + r.stderr
    check("D: an exact mtime tie refuses and names both",
          r.returncode == 1 and a.name in out and b.name in out
          and "bale apply " + a.name not in out, out[-600:])
finally:
    fx.close()

# E. `bale apply --help` exits 0 (its description is in the forecast).
fx = Fx()
try:
    r = run_bale(fx.install, ["apply", "--help"], cwd=fx.repo, env=fx.env)
    check("E: `bale apply --help` exits 0", r.returncode == 0, r.stderr[-300:])
finally:
    fx.close()

# F. The tests rider: the two handoff blindness-gate cases pass.
r = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests",
                    "-p", "test_checkpoint_provenance.py", "-k", "HandoffBlindnessGateTest"],
                   capture_output=True, text=True, timeout=600)
check("F: HandoffBlindnessGateTest passes", r.returncode == 0, r.stderr[-600:])

fails = 0
for label, ok, detail in results:
    print(("[PASS] " if ok else "[FAIL] ") + label)
    if not ok and detail:
        for ln in str(detail).splitlines()[-8:]:
            print("       " + ln)
    fails += 0 if ok else 1
print(f"checkpoint: {len(results) - fails}/{len(results)} outcomes hold")
sys.exit(1 if fails else 0)
PY
