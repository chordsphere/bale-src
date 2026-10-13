#!/usr/bin/env bash
# Blind checkpoint — session contract-verb (bale-src), version 1.
# Authored 2026-10-13 by sitting 2026-10-13-twine-obligations-desk-001,
# from the request, before any implementation existed.
#
# Outcome contract only: what `bale contract` must print from the applied
# tree, and that the release is recorded. The cwd is the staged tree.
# Exit 0 = every probe passed; 1 = at least one probe failed (a HOLD on
# the work — a crash or refusal of the verb under test is a probe failure,
# exit 1, never 2); 2 = this oracle is defective (a control failed or an
# unplanned exception) — never a verdict on the work.
# Verdict lines carry the label alone; detail follows on "  detail:" lines.
# Writes only under a private mktemp directory it removes; no network;
# starts only the processes it waits for; needs no sid, manifest or path.
set -u
exec python3 -I -B - <<'ORACLE'
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

TREE = Path.cwd().resolve()
BALE = TREE / "bin" / "bale"
SCHEMA = TREE / "schemas" / "telemetry-record.schema.json"
TIMEOUT = 60

# ---------------------------------------------------------------- pins
APPLY_OUTCOMES = {"applied", "held", "reverted", "bailout", "clarification",
                  "dry-run", "scope-drift-refused", "required-check-refused",
                  "base-drift-refused"}
OPEN_REFUSAL_REASONS = {"not-a-repo", "not-found", "not-a-bundle",
                        "manifest-invalid", "member-mismatch",
                        "no-validation-base", "gate-refused",
                        "defective-oracle", "sandbox-failed", "desk-refused",
                        "pack-refused", "config-invalid", "no-git",
                        "internal-fault", "unclassified"}
PACK_REPORT_KEYS = ["outcome", "sid", "tarball", "log", "session_dir",
                    "context_files", "readme_path", "readme_heading",
                    "readme_sha256", "checkpoint_file_path",
                    "checkpoint_file_sha256", "branch", "applied_latest",
                    "sweep", "include_group", "opener"]
OPEN_LINE_KEYS = {"outcome", "sid", "tarball", "opener", "desk", "bundle",
                  "reason", "cause"}
REQUIRED_SURFACES = {"pack", "open", "apply", "relay", "unlock", "revert",
                     "status", "stats", "open-refused", "relay-refused",
                     "unlock-refused", "revert-refused"}
REFUSAL_SETS = {"open": "OPEN_REFUSAL_REASONS", "relay": "RELAY_REFUSAL_REASONS",
                "unlock": "UNLOCK_REFUSAL_REASONS", "revert": "REVERT_REFUSAL_REASONS"}

# ----------------------------------------------------------- detectors
def run_bale(args, cwd):
    """Run the tree's bin/bale; a crash or non-zero exit is the work's."""
    env = {k: v for k, v in os.environ.items() if not k.startswith("BALE_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        p = subprocess.run([sys.executable, "-B", str(BALE), *args],
                           cwd=str(cwd), env=env, capture_output=True,
                           text=True, timeout=TIMEOUT, stdin=subprocess.DEVNULL)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired as e:
        return -1, (e.stdout or ""), f"timed out after {TIMEOUT}s"

def one_json_line(stdout: str):
    lines = [l for l in stdout.split("\n") if l.strip()]
    if len(lines) != 1:
        return None
    try:
        obj = json.loads(lines[0])
    except ValueError:
        return None
    return obj if isinstance(obj, dict) else None

def vocab_ok(entry, home: str, pointer: str, values=None) -> bool:
    if not isinstance(entry, dict):
        return False
    if entry.get("home") != home or entry.get("pointer") != pointer:
        return False
    vals = entry.get("values")
    if not (isinstance(vals, list) and vals and all(isinstance(v, str) for v in vals)):
        return False
    return True if values is None else vals == list(values)

def key_list_ok(v) -> bool:
    return (isinstance(v, list) and v and all(isinstance(k, str) and k for k in v)
            and len(set(v)) == len(v))

def schema_enum(pointer: str):
    node = json.loads(SCHEMA.read_text(encoding="utf-8"))
    for part in pointer.strip("/").split("/"):
        node = node[part]
    return node["enum"]

# ------------------------------------------------------------- controls
def control(name: str, ok: bool) -> None:
    if not ok:
        print(f"oracle control failed: {name}", file=sys.stderr)
        sys.exit(2)

def run_controls() -> None:
    control("one_json_line-positive", one_json_line('{"a": 1}\n') == {"a": 1})
    control("one_json_line-two-lines", one_json_line('{"a": 1}\n{"b": 2}\n') is None)
    control("one_json_line-not-object", one_json_line('[1]\n') is None)
    control("one_json_line-garbage", one_json_line('x\n') is None)
    good = {"home": "h", "pointer": "p", "values": ["a", "b"]}
    control("vocab_ok-positive", vocab_ok(good, "h", "p", ["a", "b"]))
    control("vocab_ok-order", not vocab_ok(good, "h", "p", ["b", "a"]))
    control("vocab_ok-home", not vocab_ok(good, "x", "p"))
    control("vocab_ok-empty", not vocab_ok({"home": "h", "pointer": "p", "values": []}, "h", "p"))
    control("key_list_ok-positive", key_list_ok(["a", "b"]))
    control("key_list_ok-dup", not key_list_ok(["a", "a"]))
    control("key_list_ok-empty", not key_list_ok([]))
    control("schema_enum", isinstance(schema_enum("/properties/outcome"), list))

# --------------------------------------------------------------- probes
failures = []
def probe(label: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if detail and not ok:
        print(f"  detail: {detail}")
    if not ok:
        failures.append(label)

def main() -> int:
    run_controls()
    scratch = Path(tempfile.mkdtemp(prefix="contract-oracle-"))
    try:
        nonrepo = scratch / "nonrepo"; nonrepo.mkdir()
        rc, out, err = run_bale(["contract", "--json"], nonrepo)
        probe("contract-json-exit-0", rc == 0,
              f"exit {rc}; stderr tail: {err.strip().splitlines()[-1] if err.strip() else '(none)'}")
        line = one_json_line(out)
        probe("contract-json-one-object", line is not None,
              "stdout is not exactly one JSON object line")
        if line is None:
            line = {}
        probe("contract-outcome", line.get("outcome") == "contract")
        version = (TREE / "bin" / "VERSION").read_text(encoding="utf-8").strip()
        probe("contract-bale-version", line.get("bale_version") == version,
              f"bale_version {line.get('bale_version')!r}; bin/VERSION {version!r}")
        vocab = line.get("vocabularies") if isinstance(line.get("vocabularies"), dict) else {}
        probe("vocab-telemetry-outcome",
              vocab_ok(vocab.get("telemetry-outcome"),
                       "schemas/telemetry-record.schema.json",
                       "/properties/outcome", schema_enum("/properties/outcome")),
              "home, pointer or values differ from the schema's enum")
        cr_ptr = "/properties/attempts/items/properties/closure_reason"
        probe("vocab-closure-reason",
              vocab_ok(vocab.get("closure-reason"),
                       "schemas/telemetry-record.schema.json", cr_ptr,
                       [v for v in schema_enum(cr_ptr) if v is not None]),
              "home, pointer or values differ from the schema's enum minus null")
        ao = vocab.get("apply-outcome")
        probe("vocab-apply-outcome",
              vocab_ok(ao, "bin/bale_report.py", "APPLY_OUTCOMES")
              and set(ao["values"]) == APPLY_OUTCOMES and len(ao["values"]) == 9,
              "apply-outcome missing, or its values are not the nine outcome words")
        refusal = line.get("refusal_reasons") if isinstance(line.get("refusal_reasons"), dict) else {}
        for surface, tuple_name in REFUSAL_SETS.items():
            entry = refusal.get(surface)
            ok = vocab_ok(entry, "bin/bale_report.py", tuple_name)
            if ok and surface == "open":
                ok = set(entry["values"]) == OPEN_REFUSAL_REASONS and len(entry["values"]) == 15
            probe(f"refusal-{surface}", ok,
                  f"refusal_reasons.{surface} missing or mis-shaped"
                  + (" (the open set is fourteen codes plus unclassified)" if surface == "open" else ""))
        keys = line.get("json_keys") if isinstance(line.get("json_keys"), dict) else {}
        missing = sorted(s for s in REQUIRED_SURFACES if not key_list_ok(keys.get(s)))
        probe("json-keys-surfaces", not missing,
              f"missing or mis-shaped surfaces: {', '.join(missing)}")
        probe("json-keys-pack", keys.get("pack") == PACK_REPORT_KEYS,
              "json_keys.pack is not PACK_REPORT_KEYS in order")
        open_keys = set(keys.get("open") or [])
        probe("json-keys-open", OPEN_LINE_KEYS <= open_keys,
              f"open line lacks: {', '.join(sorted(OPEN_LINE_KEYS - open_keys))}")
        rc2, out2, _ = run_bale(["contract", "--json"], nonrepo)
        probe("contract-deterministic", rc2 == 0 and out2 == out,
              f"second run exit {rc2}; lines {'equal' if out2 == out else 'differ'}")
        rc3, out3, err3 = run_bale(["contract"], nonrepo)
        probe("contract-human-mode", rc3 == 0 and out3.strip() != "",
              f"exit {rc3}, stdout {'empty' if not out3.strip() else 'non-empty'}")
        rc4, out4, err4 = run_bale(["help"], nonrepo)
        probe("contract-in-help", rc4 == 0 and "contract" in (out4 + err4),
              "bale help does not list the verb")
        record = TREE / "claude" / "changelog" / f"{version}.json"
        rec_ok = False; detail = f"{record.relative_to(TREE)} missing"
        if record.is_file():
            try:
                rec = json.loads(record.read_text(encoding="utf-8"))
                paths = {s.get("path") for s in rec.get("surfaces", []) if isinstance(s, dict)}
                rec_ok = rec.get("version") == version and {"bin/bale", "bin/bale_report.py"} <= paths
                detail = f"version {rec.get('version')!r}; surfaces {sorted(p for p in paths if p)}"
            except ValueError:
                detail = "record is not JSON"
        probe("release-recorded", rec_ok, detail)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    if failures:
        print(f"HOLD: {len(failures)} probe(s) failed")
        return 1
    print("PASS: every probe passed")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except BaseException as e:  # an unplanned exit is an oracle fault
        print(f"oracle fault: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(2)
ORACLE
