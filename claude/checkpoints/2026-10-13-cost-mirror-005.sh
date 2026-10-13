#!/usr/bin/env bash
# Blind checkpoint — session cost-mirror (bale-src), version 1.
# Authored 2026-10-13 by sitting 2026-10-13-twine-obligations-desk-001,
# from the request, before any implementation existed.
#
# Outcome contract only: a closing attempt written through --cost-file
# carries the file's values; a bad file refuses before any state change;
# an attempt written without the flag carries the six-key all-null block;
# the schema and the release record say so. The cwd is the staged tree,
# whose bin/bale the scenarios drive inside scratch repos under a private
# mktemp directory (one fresh repo per scenario, removed at the end).
# Exit 0 = every probe passed; 1 = at least one probe failed (a crash or
# refusal of the code under test is a probe failure, exit 1, never 2);
# 2 = this oracle is defective (a control failed, git or file setup
# failed, or an unplanned exception) — never a verdict on the work.
# Verdict lines carry the label alone; detail follows on "  detail:" lines.
# No network; starts only the processes it waits for; needs no sid,
# manifest or own path.
set -u
exec python3 -I -B - <<'ORACLE'
import glob, json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

TREE = Path.cwd().resolve()
BALE = TREE / "bin" / "bale"
SCHEMA = TREE / "schemas" / "telemetry-record.schema.json"
TIMEOUT = 120
COST_KEYS = {"tokens_in", "tokens_out", "usd", "model_tier", "calls", "models"}
FULL = {"tokens_in": 12345, "tokens_out": 678, "usd": 0.4321,
        "model_tier": None, "calls": 14, "models": ["model-a-1", "model-b-2"]}
SUBSET = {"usd": 1.5, "calls": 3}
ALL_NULL = {k: None for k in COST_KEYS}

# ----------------------------------------------------------- detectors
def run_bale(args, cwd):
    env = {k: v for k, v in os.environ.items() if not k.startswith("BALE_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
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

def git(repo, *args):
    r = subprocess.run(["git", *args], cwd=str(repo), capture_output=True,
                       text=True, timeout=TIMEOUT)
    if r.returncode != 0:  # the oracle's own fixture failed: exit 2
        print(f"oracle fixture failure: git {' '.join(args)}: {r.stderr.strip()}",
              file=sys.stderr)
        sys.exit(2)

def scratch_repo(root: Path, name: str) -> Path:
    repo = root / name; repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.email", "oracle@example.invalid")
    git(repo, "config", "user.name", "oracle")
    (repo / "f.txt").write_text("fixture\n", encoding="utf-8")
    (repo / "bale.toml").write_text("[sandbox]\nenabled = false\n", encoding="utf-8")
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", "fixture")
    return repo

def pack(repo: Path):
    """Open a session; return (sid, detail)."""
    rc, out, err = run_bale(["pack", "cost probe", "--slug", "cost",
                             "--include", "f.txt", "--write", "f.txt",
                             "--no-readme", "--expects-probe", "no", "--json"], repo)
    line = one_json_line(out)
    if rc != 0 or not line or not isinstance(line.get("sid"), str):
        tail = err.strip().splitlines()[-1] if err.strip() else "(no stderr)"
        return None, f"pack exit {rc}; {tail}"
    return line["sid"], ""

def record_of(repo: Path, sid: str):
    hits = glob.glob(str(repo / "*" / "telemetry" / f"{sid}.json"))
    if len(hits) != 1:
        return None
    try:
        return json.loads(Path(hits[0]).read_text(encoding="utf-8"))
    except ValueError:
        return None

def last_cost(record):
    if not record or not isinstance(record.get("attempts"), list) or not record["attempts"]:
        return None
    last = record["attempts"][-1]
    return (last.get("outcome"), last.get("cost"))

def cost_equal(a, b) -> bool:
    return isinstance(a, dict) and isinstance(b, dict) and a == b

def schema_cost_shape():
    s = json.loads(SCHEMA.read_text(encoding="utf-8"))
    cost = s["properties"]["attempts"]["items"]["properties"]["cost"]
    return set(cost.get("properties", {})), cost.get("additionalProperties")

# ------------------------------------------------------------- controls
def control(name: str, ok: bool) -> None:
    if not ok:
        print(f"oracle control failed: {name}", file=sys.stderr)
        sys.exit(2)

def run_controls(root: Path) -> None:
    control("one_json_line-positive", one_json_line('{"a": 1}\n') == {"a": 1})
    control("one_json_line-two-lines", one_json_line('{"a": 1}\n{"b": 2}\n') is None)
    control("cost_equal-positive", cost_equal({"a": 1}, {"a": 1}))
    control("cost_equal-negative", not cost_equal({"a": 1}, {"a": 2}))
    control("cost_equal-none", not cost_equal(None, {"a": 1}))
    control("last_cost-none", last_cost({"attempts": []}) is None)
    control("last_cost-positive",
            last_cost({"attempts": [{"outcome": "x", "cost": {"k": 1}}]}) == ("x", {"k": 1}))
    fake = root / "fake"; (fake / "claude" / "telemetry").mkdir(parents=True)
    (fake / "claude" / "telemetry" / "s.json").write_text('{"attempts": []}')
    control("record_of-positive", record_of(fake, "s") == {"attempts": []})
    control("record_of-missing", record_of(fake, "t") is None)
    keys, ap = schema_cost_shape()
    control("schema_cost_shape", isinstance(keys, set) and keys)

# --------------------------------------------------------------- probes
failures = []
def probe(label: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if detail and not ok:
        print(f"  detail: {detail}")
    if not ok:
        failures.append(label)

def main() -> int:
    root = Path(tempfile.mkdtemp(prefix="cost-oracle-"))
    try:
        run_controls(root)

        # schema
        keys, ap = schema_cost_shape()
        probe("schema-cost-six-keys", keys == COST_KEYS,
              f"cost properties: {sorted(keys)}")
        probe("schema-cost-closed", ap is False,
              f"additionalProperties is {ap!r}, not false")

        # help names the flag on the three verbs
        for verb in ("apply", "retry", "unlock"):
            rc, out, err = run_bale(["help", verb], root)
            probe(f"help-{verb}-cost-file", rc == 0 and "--cost-file" in (out + err),
                  f"exit {rc}; --cost-file absent from the help text")

        # scenario 1: full file round-trips through unlock
        repo = scratch_repo(root, "full")
        sid, detail = pack(repo)
        probe("s1-pack", sid is not None, detail)
        if sid:
            cost_path = root / "full-cost.json"
            cost_path.write_text(json.dumps(FULL), encoding="utf-8")
            rc, out, err = run_bale(["unlock", sid, "--reason", "abandoned",
                                     "--cost-file", str(cost_path), "--json"], repo)
            line = one_json_line(out)
            probe("s1-unlock-exit-0", rc == 0 and line is not None and line.get("outcome") == "unlocked",
                  f"exit {rc}; {err.strip().splitlines()[-1] if err.strip() else '(no stderr)'}")
            lc = last_cost(record_of(repo, sid))
            probe("s1-record-cost-mirrored",
                  lc is not None and lc[0] == "unlocked" and cost_equal(lc[1], FULL),
                  f"last attempt: {lc!r}")

        # scenario 2: subset file — absent keys null
        repo = scratch_repo(root, "subset")
        sid, detail = pack(repo)
        probe("s2-pack", sid is not None, detail)
        if sid:
            cost_path = root / "subset-cost.json"
            cost_path.write_text(json.dumps(SUBSET), encoding="utf-8")
            rc, out, err = run_bale(["unlock", sid, "--reason", "abandoned",
                                     "--cost-file", str(cost_path), "--json"], repo)
            expected = dict(ALL_NULL, **SUBSET)
            lc = last_cost(record_of(repo, sid))
            probe("s2-subset-nulls",
                  rc == 0 and lc is not None and lc[0] == "unlocked" and cost_equal(lc[1], expected),
                  f"exit {rc}; last attempt: {lc!r}")

        # scenario 3: a bad file refuses before any state change; then a
        # flagless unlock writes the six-key all-null block
        repo = scratch_repo(root, "bad")
        sid, detail = pack(repo)
        probe("s3-pack", sid is not None, detail)
        if sid:
            before = record_of(repo, sid)
            n_before = len(before["attempts"]) if before and isinstance(before.get("attempts"), list) else None
            bad_path = root / "bad-cost.json"
            bad_path.write_text(json.dumps({"usd": 1.0, "tokens_total": 5}), encoding="utf-8")
            rc, out, err = run_bale(["unlock", sid, "--reason", "abandoned",
                                     "--cost-file", str(bad_path), "--json"], repo)
            after = record_of(repo, sid)
            n_after = len(after["attempts"]) if after and isinstance(after.get("attempts"), list) else None
            probe("s3-unknown-key-refused", rc != 0,
                  "unlock accepted a cost file with an unknown key")
            probe("s3-refusal-wrote-nothing",
                  n_before is not None and n_after == n_before,
                  f"attempts before {n_before}, after {n_after}")
            missing = root / "missing-cost.json"
            rc, out, err = run_bale(["unlock", sid, "--reason", "abandoned",
                                     "--cost-file", str(missing), "--json"], repo)
            probe("s3-missing-file-refused", rc != 0,
                  "unlock accepted a missing cost file")
            rc, out, err = run_bale(["unlock", sid, "--reason", "abandoned", "--json"], repo)
            lc = last_cost(record_of(repo, sid))
            probe("s3-flagless-all-null",
                  rc == 0 and lc is not None and lc[0] == "unlocked" and cost_equal(lc[1], ALL_NULL),
                  f"exit {rc}; last attempt: {lc!r}")

        # the release is recorded
        version = (TREE / "bin" / "VERSION").read_text(encoding="utf-8").strip()
        record = TREE / "claude" / "changelog" / f"{version}.json"
        rec_ok = False; detail = f"{record.relative_to(TREE)} missing"
        if record.is_file():
            try:
                rec = json.loads(record.read_text(encoding="utf-8"))
                paths = {s.get("path") for s in rec.get("surfaces", []) if isinstance(s, dict)}
                want = {"bin/bale", "bin/bale_report.py", "schemas/telemetry-record.schema.json"}
                rec_ok = rec.get("version") == version and want <= paths
                detail = f"version {rec.get('version')!r}; surfaces {sorted(p for p in paths if p)}"
            except ValueError:
                detail = "record is not JSON"
        probe("release-recorded", rec_ok, detail)
    finally:
        shutil.rmtree(root, ignore_errors=True)
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
