#!/usr/bin/env bash
# Blind checkpoint — board row 89: decline cause on every prompt, one
# composed-line rule, and the JSON renderer's home.
# Authored blind at the 2026-09-15-continue-plan-004 sitting, from the
# request, before implementation. Runs in staging (cwd = staging root).
# Outcome contracts only: what must be true of the applied tree, never
# how the worker got there. Exit 0 PASS / 1 HOLD / 2 errored.
set -u
fails=0
check() {  # check <label> <0|1>
  if [ "$2" -eq 0 ]; then echo "[PASS] $1"; else echo "[FAIL] $1"; fails=$((fails+1)); fi
}
if ! command -v python3 >/dev/null 2>&1; then
  echo "[SKIP] python3 not found"; exit 2
fi
[ -f tests/harness.py ] || { echo "[FAIL] tests/harness.py absent in staging"; exit 2; }

python3 - <<'PY'
import json, sys, tempfile
from pathlib import Path
sys.path.insert(0, "tests")
from harness import (bale_env, build_response_dir, git_env, make_install,
                     make_repo, make_sandbox_home, run_bale, run_bale_pty,
                     run_checked, tar_response_dir)

results = []
def check(label, ok, detail=""):
    results.append((label, bool(ok), detail))

class Fx:
    """One fresh fixture per scenario (per-scenario isolation)."""
    def __init__(self):
        self.td = tempfile.TemporaryDirectory(prefix="ckpt89-")
        self.tmp = Path(self.td.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        genv = git_env(self.home)
        for rel in ("src/a.txt", "lib/b.txt"):
            p = self.repo / rel; p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(rel + "\n", encoding="utf-8")
        (self.repo / "bale.toml").write_text("[sandbox]\nenabled = false\n",
                                             encoding="utf-8")
        run_checked(["git", "add", "-A"], cwd=self.repo, env=genv)
        run_checked(["git", "commit", "-m", "fixture"], cwd=self.repo, env=genv)
    def pack(self, write):
        r = run_bale(self.install, ["pack", "row 89 oracle fixture", "--slug",
                                    "ck", "--include", "src", "lib", "--write",
                                    write, "--no-readme"],
                     cwd=self.repo, env=self.env)
        assert r.returncode == 0, r.stdout + r.stderr
        root = self.repo / ".bale" / "sessions"
        return sorted(d.name for d in root.iterdir() if (d / "open").is_file())[-1]
    def response(self, sid, *paths):
        entries = [{"path": p, "action": "modified", "reason": "fixture",
                    "data": f"rewritten {p}\n".encode()} for p in paths]
        rdir = build_response_dir(self.tmp / "resp", sid, summary="fixture",
                                  entries=entries)
        return tar_response_dir(rdir)
    def is_open(self, sid):
        return (self.repo / ".bale" / "sessions" / sid / "open").is_file()
    def close(self):
        self.td.cleanup()

# 1. Composed drift line carries a typed --allow-out-of-scope value that
#    had no effect (one rule for all three composed lines).
fx = Fx()
try:
    sid = fx.pack("src")
    tb = fx.response(sid, "lib/b.txt")
    r = run_bale(fx.install, ["apply", str(tb), "--allow-out-of-scope",
                              "src/a.txt", "--json"], cwd=fx.repo, env=fx.env)
    lines = [ln for ln in r.stdout.splitlines()
             if ln.startswith("{") and '"scope-drift-refused"' in ln]
    remedy = json.loads(lines[0])["drift"]["remedy"] if len(lines) == 1 else ""
    check("drift remedy carries the typed no-effect path beside the refused one",
          "--allow-out-of-scope 'src/a.txt'" in remedy
          and "--allow-out-of-scope 'lib/b.txt'" in remedy, remedy)
    check("drift refusal still refuses (exit 1, session open)",
          r.returncode == 1 and fx.is_open(sid))
finally:
    fx.close()

# 2. The bare-apply confirmation: Enter at the decline default and an
#    explicit 'n' both decline, apply nothing, and render DIFFERENT
#    decline text — the cause is distinguishable from the line alone.
def bare_decline(answer):
    fx = Fx()
    try:
        sid = fx.pack("src")
        tb = fx.response(sid, "src/a.txt")
        dl = fx.repo / "inbox"; dl.mkdir()
        (dl / tb.name).write_bytes(tb.read_bytes())
        code, out = run_bale_pty(fx.install, ["apply"], cwd=dl, env=fx.env,
                                 answers=answer)
        return code, out, fx.is_open(sid), (fx.repo / "src" / "a.txt").read_text()
    finally:
        fx.close()
c1, o1, open1, a1 = bare_decline("\n")
c2, o2, open2, a2 = bare_decline("n\n")
def after_prompt(out, marker, answer):
    """Text after the last prompt marker, with the pty's echo of the
    typed answer removed, so only the program's own decline text is
    compared."""
    i = out.rfind(marker)
    seg = out[i + len(marker):] if i >= 0 else out
    seg = seg.lstrip()
    a = answer.strip()
    if a and seg.startswith(a):
        seg = seg[len(a):]
    return seg.strip()
def tail(out, answer):
    return after_prompt(out, "[y/N]", answer)
check("bare-apply: Enter at [y/N] declines, nothing applied, session open",
      c1 != 0 and open1 and a1 == "src/a.txt\n", o1[-400:])
check("bare-apply: 'n' declines, nothing applied, session open",
      c2 != 0 and open2 and a2 == "src/a.txt\n", o2[-400:])
check("bare-apply: the two decline renderings differ (cause is visible)",
      tail(o1, "\n") != tail(o2, "n\n"), tail(o1, "\n")[:200] + " || " + tail(o2, "n\n")[:200])

# 3. The drift admission prompt: same distinguishability contract.
def drift_decline(answer):
    fx = Fx()
    try:
        sid = fx.pack("src")
        tb = fx.response(sid, "lib/b.txt")
        code, out = run_bale_pty(fx.install, ["apply", str(tb)], cwd=fx.repo,
                                 env=fx.env, answers=answer)
        return code, out, fx.is_open(sid)
    finally:
        fx.close()
d1, p1, dopen1 = drift_decline("\n")
d2, p2, dopen2 = drift_decline("n\n")
def dtail(out, answer):
    return after_prompt(out, "admit lib/b.txt?", answer)
check("drift prompt: Enter declines, session open", d1 == 1 and dopen1, p1[-300:])
check("drift prompt: 'n' declines, session open", d2 == 1 and dopen2, p2[-300:])
check("drift prompt: the two decline renderings differ",
      dtail(p1, "\n") != dtail(p2, "n\n"), dtail(p1, "\n")[:200] + " || " + dtail(p2, "n\n")[:200])

# 4. The hooks JSON renderer is defined in bale_report, and the verb it
#    serves still emits its JSON line.
sys.path.insert(0, "bin")
import bale_report, bale_config
fn = getattr(bale_report, "format_config_hooks_json", None)
check("format_config_hooks_json is defined in bin/bale_report.py",
      fn is not None and getattr(fn, "__module__", "") == "bale_report")
own = getattr(bale_config, "format_config_hooks_json", None)
check("bin/bale_config.py no longer defines format_config_hooks_json",
      own is None or getattr(own, "__module__", "") != "bale_config")
fx = Fx()
try:
    r = run_bale(fx.install, ["config", "hooks", "--json"], cwd=fx.repo, env=fx.env)
    jl = [ln for ln in r.stdout.splitlines() if ln.startswith("{")]
    ok = r.returncode == 0 and len(jl) == 1
    if ok:
        try: json.loads(jl[0])
        except ValueError: ok = False
    check("`bale config hooks --json` still emits one JSON line", ok, r.stdout[-300:] + r.stderr[-300:])
finally:
    fx.close()

fails = 0
for label, ok, detail in results:
    print(("[PASS] " if ok else "[FAIL] ") + label)
    if not ok and detail:
        for ln in str(detail).splitlines()[-6:]:
            print("       " + ln)
    fails += 0 if ok else 1
print(f"checkpoint: {len(results) - fails}/{len(results)} outcomes hold")
sys.exit(1 if fails else 0)
PY
