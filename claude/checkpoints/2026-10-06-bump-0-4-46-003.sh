#!/usr/bin/env bash
# Blind checkpoint, bump-0-4-46 (v1). Authored by the read-only desk
# 2026-10-06-friction-points-close-desk-002 from the request, before the
# work exists. Outcome-only: bin/VERSION, the 0.4.46 record, the four
# ratified sessions' attribution, the bin/VERSION row, and the earlier
# records untouched. Runs from the tree root; writes nothing.
# Exit 0: every probe passed. Exit 1: a probe failed (the work).
# Exit 2: the control failed or the oracle's own machinery broke.
set -u
export PYTHONDONTWRITEBYTECODE=1

python3 -B -I - "$PWD" <<'PYEOF'
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

root = Path(sys.argv[1])
failed = []


def say(ok, label, why=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {label}" + ("" if ok else f": {why}"))
    if not ok:
        failed.append(label)


# --- control: the validator this oracle leans on judges known records ---
try:
    spec = importlib.util.spec_from_file_location(
        "bale_validate_ckpt", root / "bin" / "bale_validate.py")
    bv = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(root / "bin"))
    spec.loader.exec_module(bv)
    good = {"record_version": 1, "version": "0.4.35",
            "session_id": "2026-09-17-fx-changelog-001",
            "at": "2026-09-17T00:00:00+00:00",
            "surfaces": [{"path": "bin/VERSION", "change": "x -> y"}]}
    bad = dict(good)
    bad["version"] = "v0.4.35"
    assert bv.validate_changelog_record(good) == [], "good record rejected"
    assert bv.validate_changelog_record(bad), "bad record accepted"
except Exception as e:  # the oracle's own machinery, not the work
    print(f"[CONTROL] validator control failed: {e!r}")
    sys.exit(20)
print("[CONTROL] validate_changelog_record judges a known good and a known bad record")

# --- probe 1: bin/VERSION ---
vpath = root / "bin" / "VERSION"
try:
    first = vpath.read_text(encoding="utf-8").splitlines()[0].strip()
except Exception as e:
    first = None
    say(False, "bin/VERSION reads 0.4.46", f"unreadable: {e!r}")
if first is not None:
    say(first == "0.4.46", "bin/VERSION reads 0.4.46", f"reads {first!r}")

# --- probe 2: the record exists, parses, validates, names 0.4.46 ---
rpath = root / "claude" / "changelog" / "0.4.46.json"
record = None
try:
    record = json.loads(rpath.read_text(encoding="utf-8"))
except Exception as e:
    say(False, "claude/changelog/0.4.46.json validates as 0.4.46",
        f"missing or not JSON: {e!r}")
if record is not None:
    try:
        errs = bv.validate_changelog_record(record)
    except Exception as e:  # a crash on the work's record is the work's
        errs = [f"validator raised {e!r}"]
    ok = (errs == [] and isinstance(record, dict)
          and record.get("version") == "0.4.46")
    say(ok, "claude/changelog/0.4.46.json validates as 0.4.46",
        f"errors {errs}, version {record.get('version') if isinstance(record, dict) else None!r}")

rows = []
if isinstance(record, dict) and isinstance(record.get("surfaces"), list):
    rows = [r for r in record["surfaces"] if isinstance(r, dict)]

# --- probe 3: the record is this session's ---
sid = record.get("session_id") if isinstance(record, dict) else None
say(isinstance(sid, str) and re.fullmatch(
        r"\d{4}-\d{2}-\d{2}-bump-0-4-46-\d{3}", sid) is not None,
    "the record's session_id is this session's", f"reads {sid!r}")

# --- probe 4: the bin/VERSION row ---
vrows = [r for r in rows if r.get("path") == "bin/VERSION"
         and "0.4.45" in str(r.get("change", ""))
         and "0.4.46" in str(r.get("change", ""))]
say(len(vrows) >= 1, "a bin/VERSION row names 0.4.45 and 0.4.46",
    "no such row")

# --- probe 5: the four ratified sessions each attributed on a row ---
for label, s in (("C", "2026-10-03-wizard-defaults-006"),
                 ("D", "2026-10-04-clipboard-paste-blocks-001"),
                 ("log-hold", "2026-10-04-log-hold-003"),
                 ("the rename", "2026-10-05-clipboard-key-rename-002")):
    n = sum(1 for r in rows if r.get("session_id") == s)
    say(n >= 1, f"{label}'s change is attributed on a row ({s})",
        "no row carries that session_id")

# --- probe 6: the earlier records are untouched ---
pinned = {
    "0.4.35.json": "14422ebc4977997fe159cbf3ff3d1735c70642481ae445b952748eb9abcec13b",
    "0.4.36.json": "edbbb5c7eef40d9a5102a59f94e4a734dc203ed63fab2ebe8875d72bd0753be0",
    "0.4.37.json": "5ef59d140d133f4e0fc0ebb5ee9c15ea73a7fcb7644ae7a90900bc0d9f5d05ea",
    "0.4.38.json": "dbee836b0341c4c154910cca6dc149366b5f5f149dbc64804952c5a44b504e61",
    "0.4.39.json": "c977531f87e44471fb9d7cfa2294468780ef2a831b1437873fd506928a1fad57",
    "0.4.40.json": "aa787750fc30c9621263c1dc6b825441ab9976b4aea19ce172651f94a9f9e4ed",
    "0.4.41.json": "c6a2dea436e6ecc3215c637a934cef4f76140c4409035ca215374022f4586065",
    "0.4.42.json": "c0d26fe4b30cefa33612a497d8390c6e3eeec67df79434ac61ddbe46df660e46",
    "0.4.43.json": "90b4854fd11251bf9a6d02cc2516142d88c1dfa7d33f8d20c62bba5467576f36",
    "0.4.44.json": "62e71e58abf649a076c606c0c06097819980862e728824d48eeaaa14f553c570",
    "0.4.45.json": "2088ed72407753211e2ca185e5e5b9f91e206ef7a4db35a1934e7a98fa3aad20",
}
cdir = root / "claude" / "changelog"
moved = []
for name, digest in pinned.items():
    p = cdir / name
    got = hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else None
    if got != digest:
        moved.append(name)
extra = sorted(p.name for p in cdir.glob("*.json")
               if p.name not in pinned and p.name != "0.4.46.json")
say(not moved and not extra,
    "claude/changelog holds the eleven earlier records unchanged plus 0.4.46.json",
    f"changed or missing {moved}, unexpected {extra}")

sys.exit(10 if failed else 0)
PYEOF
rc=$?
# The interpreter's own exits are 0 (pass), 10 (a probe failed) and 20
# (the control failed); anything else, a traceback's 1 included, is the
# oracle breaking, never a verdict on the work.
case "$rc" in
  0) exit 0 ;;
  10) exit 1 ;;
  20) exit 2 ;;
  *) echo "[CONTROL] the oracle's interpreter exited $rc unexpectedly"; exit 2 ;;
esac
