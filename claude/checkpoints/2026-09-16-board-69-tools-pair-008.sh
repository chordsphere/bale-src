#!/usr/bin/env bash
# Blind checkpoint — board 69, the tools pair.
# Authored at the desk from the request (2026-09-16 UTC), before any
# implementation existed; grades outcomes of the applied tree only.
# Runs from the staging root. Writes: a private tmpdir only.
# Exit 0 = every probe PASS/SKIP, 1 = a probe FAILed, 2 = script error.
set -u
trap 'echo "[ERROR] checkpoint script errored at line $LINENO"; exit 2' ERR

echo "checkpoint 69 v1: writes to nothing in the tree (tmpdir only)"
fails=0
pass() { echo "[PASS] $1"; }
fail() { echo "[FAIL] $1"; fails=$((fails + 1)); }
tmp="$(mktemp -d)"
export CP_TMP="$tmp"

python3 - <<'PY' || fails=$((fails + $?))
import json, os, subprocess, sys
from pathlib import Path
fails = 0
def verdict(label, ok, detail=""):
    global fails
    print(("[PASS] " if ok else "[FAIL] ") + label + (f" — {detail}" if detail and not ok else ""))
    if not ok: fails += 1

tmp = Path(os.environ["CP_TMP"])
crafter = Path("tools/craft_response.py").resolve()
lint = Path("tools/response_lint.py").resolve()
SID = "2026-09-16-checkpoint-probe-001"
req = tmp / "request.json"
req.write_text(json.dumps({
    "session_id": SID,
    "provenance": {"bale_version": "0.4.34", "packer": "chordsphere",
                   "work_class": "code", "contract_docs": {},
                   "checkpoint": None,
                   "packed_at": "2026-09-16T00:00:00+00:00"}}))

def scaffold(name):
    d = tmp / name
    (d / "files").mkdir(parents=True)
    r = subprocess.run([sys.executable, str(crafter), str(d), "--sid", SID,
                        "--request", str(req), "--write"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"crafter --write failed: {r.stderr[-400:]}")
    return d

def lint_codes(d, claim_value):
    m = json.loads((d / "manifest.json").read_text())
    m["summary"] = "checkpoint probe"
    m["validation_will_run"] = ["lint"]
    m["claims"] = {"lint": claim_value}
    (d / "manifest.json").write_text(json.dumps(m))
    r = subprocess.run([sys.executable, str(lint), "--json", str(d)],
                       capture_output=True, text=True)
    if r.returncode == 2:
        raise RuntimeError(f"lint errored: {r.stderr[-400:]}")
    report = json.loads(r.stdout.strip().splitlines()[-1])
    return [(f["code"], f["path"]) for f in report["findings"]]

try:
    # (b) the skeleton's self_reported block carries docs_read: []
    d = scaffold("skeleton")
    m = json.loads((d / "manifest.json").read_text())
    sr = m.get("feedback", {}).get("self_reported", {})
    verdict("crafter-skeleton-seeds-docs-read-empty-list",
            "docs_read" in sr and sr["docs_read"] == [],
            f"self_reported keys: {sorted(sr)}")

    # (a) a bare-string claim outside the vocabulary files CLAIMS_VALUE
    bad = lint_codes(scaffold("bad-claim"), "maybe")
    verdict("lint-files-claims-value-on-bad-bare-string",
            any(c == "CLAIMS_VALUE" and p.endswith("claims.lint")
                for c, p in bad),
            f"codes: {sorted({c for c, _ in bad})}")
    good = lint_codes(scaffold("good-claim"), "pass")
    verdict("lint-silent-on-pass-bare-string",
            not any(c == "CLAIMS_VALUE" for c, _ in good))
    # the annotated object form stays schema-caught, not double-filed
    obj = lint_codes(scaffold("obj-claim"), {"value": "maybe"})
    verdict("lint-annotated-form-not-double-filed",
            not any(c == "CLAIMS_VALUE" for c, _ in obj)
            and any(c == "SCHEMA_VIOLATION" and "claims" in p for c, p in obj))

    # (c) the single-quoted TOML literal is read, or named as unset
    sys.path.insert(0, "tools")
    import craft_response
    cfg = tmp / "sq"
    cfg.mkdir()
    (cfg / "bale.toml").write_text("[probe]\nclipboard_command = 'pbcopy'\n")
    cmd, note = craft_response.read_clipboard_command(cfg)
    verdict("clipboard-single-quoted-literal-read-or-named",
            cmd == "pbcopy" or ("single" in (note or "").lower()
                                 or "'" in (note or "")),
            f"cmd={cmd!r} note={note!r}")
except Exception as e:
    print(f"[FAIL] probe-errored: {type(e).__name__}: {e}")
    fails += 1
sys.exit(fails)
PY

# (d) a standing suite that fails on a network import in either tool.
# The brief fixes its home: tests/test_craft_response.py or a new suite
# whose filename contains "tools". Mutate a full copy of the tree and
# expect exactly those suites to fail there.
mut="$tmp/mut"
mkdir -p "$mut" && cp -r . "$mut"/
printf '\nimport socket  # checkpoint mutation\n' >> "$mut/tools/craft_response.py"
mut_ok=1
for pat in 'test_craft_response.py' 'test_*tools*.py'; do
  rc=0
  (cd "$mut" && python3 -m unittest discover -s tests -p "$pat" \
        > "$tmp/mut-$pat.log" 2>&1) || rc=$?
  # 5 = NO TESTS RAN (no file matched the pattern): nothing to grade
  if [ "$rc" -ne 0 ] && [ "$rc" -ne 5 ]; then
    mut_ok=0
  fi
done
if [ "$mut_ok" -eq 0 ]; then
  pass "standing-pin-catches-network-import-in-tools"
else
  fail "standing-pin-catches-network-import-in-tools"
fi

# the suites hold on the applied tree
suites_ok=1
for suite in test_craft_response test_response_lint \
             test_probe_clipboard_config test_schema_embeds; do
  if ! python3 -m unittest discover -s tests -p "${suite}.py" \
       >> "$tmp/suites.log" 2>&1; then
    suites_ok=0
    echo "  suite failed: $suite"
  fi
done
if [ "$suites_ok" -eq 1 ]; then pass "tools-suites-pass"; else
  fail "tools-suites-pass"; tail -30 "$tmp/suites.log"; fi
rm -rf "$tmp"

if [ "$fails" -ne 0 ]; then
  echo "checkpoint 69 v1: $fails probe(s) failed"; exit 1
fi
echo "checkpoint 69 v1: all probes passed"; exit 0
