#!/usr/bin/env bash
# Blind checkpoint — 2026-08-31-board-41-base-drift (v1)
# Authored at the desk from the request, before implementation exists.
# Outcome contracts only; no mechanism is asserted. Exit: 0 PASS,
# 1 HOLD, 2 defective fixture/environment.
#
# Probe labels: stamp-at-pack, refuse-moved-base, override-lands,
# clean-base-applies. Each probe builds its own fresh fixture
# (per-scenario isolation); fixtures reuse the repo's own test harness
# so every bale invocation travels the same hermetic path the suite
# uses (ADR-0005).
set -u

ROOT=""
for d in "$PWD" "$PWD/.." "$PWD/../.."; do
  if [ -f "$d/bin/bale" ] && [ -f "$d/tests/harness.py" ]; then
    ROOT="$(cd "$d" && pwd)"
    break
  fi
done
if [ -z "$ROOT" ]; then
  echo "CHECKPOINT ERROR: cannot locate tree root (bin/bale + tests/harness.py) from $PWD" >&2
  exit 2
fi

python3 - "$ROOT" <<'PYEOF'
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(sys.argv[1])
sys.path.insert(0, str(ROOT / "tests"))
try:
    from harness import (
        bale_env, build_response_dir, git_env, make_install, make_repo,
        make_sandbox_home, run_bale, run_checked, tar_response_dir,
    )
except Exception as e:  # fixture defect, not a work verdict
    print(f"CHECKPOINT ERROR: harness import failed: {e}", file=sys.stderr)
    sys.exit(2)

PINNED_FLAG = "--accept-base-drift"   # pinned in the brief (constraint 1)
results = []


class Fixture:
    """One fresh hermetic project per scenario."""

    def __init__(self, tag: str):
        self._td = tempfile.TemporaryDirectory(prefix=f"ckpt41-{tag}-")
        self.tmp = Path(self._td.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)
        self.genv = git_env(self.home)
        target = self.repo / "src" / "a.txt"
        target.parent.mkdir(parents=True)
        target.write_text("base bytes v1\n", encoding="utf-8")
        run_checked(["git", "add", "src/a.txt"], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "fixture target"],
                    cwd=self.repo, env=self.genv)

    def pack(self):
        return run_bale(
            self.install,
            ["pack", "base drift checkpoint fixture goal",
             "--slug", "ckpt-fixture",
             "--include", "src",
             "--write", "src/a.txt",
             "--no-readme"],
            cwd=self.repo, env=self.env)

    def open_sid(self):
        root = self.repo / ".bale" / "sessions"
        if not root.is_dir():
            return None
        opens = [d.name for d in root.iterdir() if (d / "open").is_file()]
        return opens[-1] if opens else None

    def stamped_manifest(self, sid: str):
        p = self.repo / ".bale" / "sessions" / sid / "manifest.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None

    def move_base(self):
        target = self.repo / "src" / "a.txt"
        target.write_text("base bytes v2 -- moved after pack\n",
                          encoding="utf-8")
        run_checked(["git", "add", "src/a.txt"], cwd=self.repo, env=self.genv)
        run_checked(["git", "commit", "-m", "base moves after pack"],
                    cwd=self.repo, env=self.genv)

    def response(self, sid: str) -> Path:
        data = b"response bytes from the session\n"
        rdir = build_response_dir(
            self.tmp / "resp", sid,
            summary="base-drift checkpoint fixture: modify the forecast file",
            entries=[{
                "path": "src/a.txt",
                "action": "modified",
                "reason": "fixture change exercising the base-drift gate",
                "data": data,
            }])
        return tar_response_dir(rdir)

    def target_bytes(self) -> bytes:
        return (self.repo / "src" / "a.txt").read_bytes()

    def cleanup(self):
        self._td.cleanup()


def probe(label: str, ok: bool, detail: str):
    results.append(ok)
    print(f"PROBE {label}: {'PASS' if ok else 'FAIL'} ({detail})")


def fixture_error(label: str, detail: str):
    print(f"CHECKPOINT ERROR in fixture for {label}: {detail}",
          file=sys.stderr)
    sys.exit(2)


# --- Probe 1: stamp-at-pack -------------------------------------------
# Outcome: after a pack whose forecast names src/a.txt, the stamped
# request manifest's provenance block carries the file's base sha256.
# Field-name-agnostic by design: the worker owns the key names; the
# probe asserts the real digest of the real base bytes appears inside
# the serialized provenance block, alongside the path it stamps.
fx = Fixture("stamp")
try:
    r = fx.pack()
    if r.returncode != 0:
        fixture_error("stamp-at-pack", f"fixture pack failed:\n{r.stdout}\n{r.stderr}")
    sid = fx.open_sid()
    if not sid:
        fixture_error("stamp-at-pack", "pack succeeded but no open session")
    manifest = fx.stamped_manifest(sid)
    if manifest is None:
        fixture_error("stamp-at-pack", "no stamped manifest for the open sid")
    digest = hashlib.sha256(fx.target_bytes()).hexdigest()
    prov = json.dumps(manifest.get("provenance") or {})
    ok = digest in prov and "src/a.txt" in prov
    probe("stamp-at-pack", ok,
          "base sha256 of src/a.txt present in request provenance"
          if ok else "base sha256 (or the path) absent from request provenance")
finally:
    fx.cleanup()

# --- Probe 2: refuse-moved-base ---------------------------------------
# Outcome: base moves after pack; a response modifying the same file
# refuses at apply (nonzero exit) and lands nothing — the moved base
# bytes survive untouched. Mechanism-agnostic: any refusal stage
# satisfies it; a silent lost-update fails it.
fx = Fixture("refuse")
try:
    r = fx.pack()
    if r.returncode != 0:
        fixture_error("refuse-moved-base", f"fixture pack failed:\n{r.stdout}\n{r.stderr}")
    sid = fx.open_sid()
    if not sid:
        fixture_error("refuse-moved-base", "pack succeeded but no open session")
    fx.move_base()
    moved = fx.target_bytes()
    tarball = fx.response(sid)
    r = run_bale(fx.install, ["apply", str(tarball)],
                 cwd=fx.repo, env=fx.env)
    refused = r.returncode != 0
    untouched = fx.target_bytes() == moved
    probe("refuse-moved-base", refused and untouched,
          "apply refused and the moved base survived"
          if refused and untouched else
          f"refused={refused}, base untouched={untouched} — a pass-through here is the lost-update hazard")
finally:
    fx.cleanup()

# --- Probe 3: override-lands ------------------------------------------
# Outcome: the same moved-base setup, applied with the pinned per-path
# override flag, proceeds — exit 0 and the response bytes land. The
# flag spelling is preserved text (pinned in the brief), so a fixed
# string is a legitimate probe of it.
fx = Fixture("override")
try:
    r = fx.pack()
    if r.returncode != 0:
        fixture_error("override-lands", f"fixture pack failed:\n{r.stdout}\n{r.stderr}")
    sid = fx.open_sid()
    if not sid:
        fixture_error("override-lands", "pack succeeded but no open session")
    fx.move_base()
    tarball = fx.response(sid)
    r = run_bale(fx.install,
                 ["apply", str(tarball), PINNED_FLAG, "src/a.txt"],
                 cwd=fx.repo, env=fx.env)
    landed = fx.target_bytes() == b"response bytes from the session\n"
    probe("override-lands", r.returncode == 0 and landed,
          "per-path override admitted the drifted base and the change landed"
          if r.returncode == 0 and landed else
          f"exit={r.returncode}, landed={landed}")
finally:
    fx.cleanup()

# --- Probe 4: clean-base-applies --------------------------------------
# Outcome: with an unmoved base, the same shape applies cleanly with no
# flags — the gate must not over-fire. (Refuse-not-warn cuts both
# ways: refusal on real drift, silence on none.)
fx = Fixture("clean")
try:
    r = fx.pack()
    if r.returncode != 0:
        fixture_error("clean-base-applies", f"fixture pack failed:\n{r.stdout}\n{r.stderr}")
    sid = fx.open_sid()
    if not sid:
        fixture_error("clean-base-applies", "pack succeeded but no open session")
    tarball = fx.response(sid)
    r = run_bale(fx.install, ["apply", str(tarball)],
                 cwd=fx.repo, env=fx.env)
    landed = fx.target_bytes() == b"response bytes from the session\n"
    probe("clean-base-applies", r.returncode == 0 and landed,
          "clean-base apply proceeded unrefused"
          if r.returncode == 0 and landed else
          f"exit={r.returncode}, landed={landed} — the gate over-fires on an unmoved base")
finally:
    fx.cleanup()

sys.exit(0 if all(results) else 1)
PYEOF
