#!/usr/bin/env bash
# Blind checkpoint — board row 90: doc residue of rows 83 and 87.
# Authored blind at the 2026-09-15-continue-plan-004 sitting, from the
# request, before implementation. Runs in staging (cwd = staging root).
# Outcome contracts only. Exit 0 PASS / 1 HOLD / 2 errored.
set -u
if ! command -v python3 >/dev/null 2>&1; then
  echo "[SKIP] python3 not found"; exit 2
fi
for f in BALE.md docs/TARBALL.md bin/bale tests/harness.py; do
  [ -f "$f" ] || { echo "[FAIL] $f absent in staging"; exit 2; }
done

python3 - <<'PY'
import re, subprocess, sys, tempfile
from pathlib import Path
sys.path.insert(0, "tests")
from harness import bale_env, make_install, make_repo, make_sandbox_home, run_bale

results = []
def check(label, ok, detail=""):
    results.append((label, bool(ok), detail))
def collapse(s):
    return re.sub(r"\s+", " ", s).strip()

bale_md = Path("BALE.md").read_text(encoding="utf-8")
bale_c = collapse(bale_md)
tarball_md = Path("docs/TARBALL.md").read_text(encoding="utf-8")

# 1. BALE.md's bare-apply description: the superseded board-51 wording
#    is gone (preserved stale strings, pinned absent) ...
check("BALE.md no longer says bare apply answers 'the single open session'",
      "answering the single open session" not in bale_c)
check("BALE.md no longer lists 'multiple open sessions' as a bare-apply refusal",
      "multiple open sessions" not in bale_c)
# ... and the 2026-09-14 ruling lands verbatim (transported decision,
#    whitespace-collapsed for the doc's own wrapping).
ruling = ("Candidates answer any open session; newest by `st_mtime_ns` "
          "wins; an exact tie refuses; the echo names the resolved "
          "session and the open set.")
check("BALE.md carries the bare-apply ruling sentence verbatim",
      collapse(ruling) in bale_c)

# 2. BALE.md's hook-acceptance passage names the operable surface.
check("BALE.md names `bale config hooks`", "bale config hooks" in bale_md)
check("BALE.md names `--forget`", "--forget" in bale_md)

# 3. `bale apply --help` no longer describes the single-open bare form.
td = tempfile.TemporaryDirectory(prefix="ckpt90-")
try:
    tmp = Path(td.name)
    home = make_sandbox_home(tmp)
    install = make_install(tmp)
    repo = make_repo(tmp, home)
    r = run_bale(install, ["apply", "--help"], cwd=repo, env=bale_env(home, tmp))
    helptext = collapse(r.stdout + r.stderr)
    check("`bale apply --help` exits 0", r.returncode == 0, r.stderr[-300:])
    check("`bale apply --help` no longer says 'with exactly one session open'",
          "with exactly one session open" not in helptext)
    check("`bale apply --help` no longer lists 'more than one open session' as a refusal",
          "more than one open session" not in helptext)
finally:
    td.cleanup()

# 4. TARBALL.md §1's "Artifact directories" bullet states the tarball
#    filename convention beside the directory one.
m = re.search(r"- \*\*Artifact directories\.\*\*(.*?)(?=\n- \*\*|\n## |\Z)",
              tarball_md, re.S)
bullet = m.group(1) if m else ""
check("TARBALL.md §1 'Artifact directories' bullet still exists", bool(m))
check("that bullet names `response-<sid>.tar.gz`", "response-<sid>.tar.gz" in bullet)

# 5. The four doc-pin suites hold on the applied tree.
r = subprocess.run([sys.executable, "-m", "unittest",
                    "tests.test_sanctioned_pairs", "tests.test_doc_crossrefs",
                    "tests.test_global_doc_selfcontainment", "tests.test_schema_embeds"],
                   capture_output=True, text=True, timeout=600)
check("doc-pin suites pass", r.returncode == 0, r.stderr[-800:])

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
