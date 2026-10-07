#!/usr/bin/env bash
# Blind checkpoint — bale-src session `open-relay-json` — v1.
# Authored blind at the read-only sitting 2026-10-06-twine-slip-sitting-006,
# from the session's brief, before the worker exists. Outcome-only: it
# grades what `bale pack --json`, `bale open --json` and `bale relay --json`
# print and exit, never how.
#
# Runs with the tree under test as the working directory. Writes ONLY under
# one fresh `mktemp -d` scratch root (a scratch HOME, scratch repositories,
# a scratch bundle directory); nothing under the tree; no interpreter cache
# (PYTHONDONTWRITEBYTECODE, `python3 -B`). Reads no session, no manifest and
# not its own path. Every process it starts is its own.
#
# Exit codes (TARBALL.md §7.5): 0 all probes pass; 1 a probe failed (label
# alone on the [FAIL] line, detail on `  detail:` lines); 2 the oracle is
# defective — a control could not fire its own detector, or an unexpected
# exception.
set -u
export PYTHONDONTWRITEBYTECODE=1
echo "[oracle] open-relay-json v1 — tree: $PWD"
echo "[oracle] writes: one fresh mktemp -d scratch root only (scratch HOME, scratch repos, scratch bundles); nothing under the tree"
exec python3 -B - "$PWD" <<'ORACLE'
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

TREE = Path(sys.argv[1]).resolve()
BALE = TREE / "bin" / "bale"
CRAFT = TREE / "tools" / "craft_response.py"
EXPECTED_VERSION = "0.4.48"
PACK_KEYS = ("outcome", "sid", "tarball", "log", "session_dir",
             "context_files", "readme_path", "readme_heading",
             "readme_sha256", "checkpoint_file_path",
             "checkpoint_file_sha256", "branch", "applied_latest", "sweep",
             "include_group")
OPEN_ONLY_KEYS = ("bundle", "members", "rehearsal", "checkpoint_dry_run",
                  "desk")
RELAY_KEYS = ("outcome", "sid", "round", "from", "awaiting", "kind",
              "preserved", "block", "log", "clipboard", "cause", "telemetry")
RELAY_KINDS = ("clarification manifest", "exchange record")
OPENER_BEGIN = "--8<-- session opener (copy everything between the scissor lines) --8<--"
OPENER_END = "--8<-- end session opener --8<--"
SID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-[a-z0-9-]+-\d{3}$")

FAILS = []


def ok(label):
    print(f"[PASS] {label}")


def bad(label, detail):
    FAILS.append(label)
    print(f"[FAIL] {label}")
    for line in str(detail).splitlines() or ["(no detail)"]:
        print(f"  detail: {line}")


def verdict(label, defects):
    bad(label, "\n".join(defects)) if defects else ok(label)


def oracle_broken(why):
    print(f"[oracle] CONTROL FAILED — the oracle is defective: {why}")
    sys.stdout.flush()
    os._exit(2)


def excepthook(exc_type, exc, tb):
    import traceback
    print("[oracle] unexpected exception — exit 2, not a verdict on the work")
    traceback.print_exception(exc_type, exc, tb, file=sys.stdout)
    sys.stdout.flush()
    os._exit(2)


sys.excepthook = excepthook

SCRATCH = Path(tempfile.mkdtemp(prefix="oracle-open-relay-json-"))
HOME = SCRATCH / "home"
HOME.mkdir()
(HOME / ".gitconfig").write_text(
    "[user]\n\tname = Bale Oracle\n\temail = oracle@example.invalid\n"
    "[init]\n\tdefaultBranch = main\n", encoding="utf-8")
(SCRATCH / "tmp").mkdir()
BUNDLES = SCRATCH / "bundles"
BUNDLES.mkdir()
ENV = {
    "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
    "HOME": str(HOME),
    "EDITOR": "/bin/true", "VISUAL": "/bin/true",
    "LANG": os.environ.get("LANG", "C.UTF-8"),
    "PYTHONDONTWRITEBYTECODE": "1",
    "BALE_INSTALL": str(SCRATCH / "install-sandbox"),
    "TMPDIR": str(SCRATCH / "tmp"),
}
print(f"[oracle] scratch root: {SCRATCH}")
COUNTER = [0]


def sh(cmd, cwd):
    r = subprocess.run(cmd, cwd=str(cwd), env=ENV, capture_output=True,
                       text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"setup command failed: {cmd}\n{r.stderr}")
    return r


def fresh_repo():
    COUNTER[0] += 1
    repo = SCRATCH / f"repo{COUNTER[0]}"
    repo.mkdir()
    sh(["git", "init", "-q", "-b", "main"], repo)
    sh(["git", "config", "user.name", "Bale Oracle"], repo)
    sh(["git", "config", "user.email", "oracle@example.invalid"], repo)
    (repo / "hello.txt").write_text("hello\n", encoding="utf-8")
    (repo / "bale.toml").write_text("[sandbox]\nenabled = false\n",
                                    encoding="utf-8")
    (repo / ".gitignore").write_text(".bale/\n", encoding="utf-8")
    sh(["git", "add", "-A"], repo)
    sh(["git", "commit", "-q", "-m", "init"], repo)
    return repo


def bale(args, cwd):
    return subprocess.run([sys.executable, "-B", str(BALE), *args],
                          cwd=str(cwd), env=ENV, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=120)


def one_line(stdout):
    lines = [ln for ln in stdout.splitlines() if ln.strip()]
    return json.loads(lines[0])


def pack_read_only(repo, slug):
    r = bale(["pack", f"fixture {slug}", "--slug", slug, "--read-only",
              "--no-readme", "--json"], repo)
    if r.returncode != 0:
        raise RuntimeError(f"fixture pack failed:\n{r.stderr}")
    return one_line(r.stdout)["sid"], r


def craft_bundle(slug):
    """A brief-only read-only bundle, built by the tree's own crafter."""
    COUNTER[0] += 1
    stem = f"2026-10-06-oracle-{slug}-{COUNTER[0]}"
    brief = BUNDLES / f"brief-{stem}.md"
    brief_bytes = f"# Brief — oracle fixture {stem}\n\nA fixture brief.\n".encode()
    brief.write_bytes(brief_bytes)
    r = subprocess.run(
        [sys.executable, "-B", "-I", str(CRAFT), "--bundle", stem,
         "--brief", str(brief), "--out-dir", str(BUNDLES),
         "--pack-arg", f"oracle fixture {slug}", "--pack-arg=--slug",
         "--pack-arg", f"oracle-{slug}", "--pack-arg=--read-only",
         "--pack-arg=--include", "--pack-arg", "hello.txt"],
        cwd=str(BUNDLES), env=ENV, capture_output=True, text=True, timeout=120)
    if r.returncode != 0:
        raise RuntimeError(f"crafter failed to build the fixture bundle:\n{r.stderr}")
    path = BUNDLES / f"{stem}.bale-bundle"
    if not path.is_file():
        raise RuntimeError("crafter wrote no bundle file")
    return path, stem, brief_bytes


def clarification_manifest(repo, sid):
    p = repo / "m.json"
    p.write_text(json.dumps({
        "response_kind": "clarification", "session_id": sid,
        "questions": [{"question": "Which?", "context": "wiring",
                       "default_assumption": "the first",
                       "why_blocked": "ambiguous"}]}) + "\n", encoding="utf-8")
    return p


def sha256(data):
    return hashlib.sha256(data).hexdigest()


# -------------------------------------------------------------- detectors
def parse_one_json_line(stdout):
    lines = [ln for ln in (stdout or "").splitlines() if ln.strip()]
    if len(lines) != 1:
        return None, [f"stdout holds {len(lines)} non-empty line(s), "
                      f"expected exactly one JSON line: {stdout[:300]!r}"]
    try:
        payload = json.loads(lines[0])
    except json.JSONDecodeError as e:
        return None, [f"stdout line is not JSON ({e}): {lines[0][:200]!r}"]
    if not isinstance(payload, dict):
        return None, [f"stdout line is not a JSON object: {lines[0][:200]!r}"]
    return payload, []


def scissor_text(stderr):
    """The opener as pasted: lines strictly between the scissor lines,
    LF-joined, one trailing LF; None when the pair is absent."""
    lines = (stderr or "").splitlines()
    try:
        b = lines.index(OPENER_BEGIN)
        e = lines.index(OPENER_END, b + 1)
    except ValueError:
        return None
    return "\n".join(lines[b + 1:e]) + "\n"


def pack_line_defects(payload, stderr):
    d = []
    if payload is None:
        return ["no JSON payload to grade"]
    for k in PACK_KEYS:
        if k not in payload:
            d.append(f"pack key {k!r} missing")
    if "opener" not in payload:
        d.append("pack line lacks the `opener` key")
    else:
        expected = scissor_text(stderr)
        if expected is None:
            d.append("stderr carries no scissor-bracketed opener to compare")
        elif payload["opener"] != expected:
            d.append(f"opener differs from the scissor-paste text: "
                     f"{payload['opener'][:80]!r} vs {expected[:80]!r}")
    if payload.get("outcome") != "packed":
        d.append(f"outcome {payload.get('outcome')!r} != 'packed'")
    return d


def open_line_defects(payload, *, outcome, bundle_path, bundle_bytes,
                      brief_bytes, stem, stderr, rehearsal=None, sid=None):
    d = []
    if payload is None:
        return ["no JSON payload to grade"]
    if payload.get("outcome") != outcome:
        d.append(f"outcome {payload.get('outcome')!r} != {outcome!r}")
    for k in PACK_KEYS + ("opener",) + OPEN_ONLY_KEYS:
        if k not in payload:
            d.append(f"key {k!r} missing from the open line")
    b = payload.get("bundle")
    if not isinstance(b, dict):
        d.append(f"bundle is not an object: {b!r}")
    else:
        if b.get("path") != str(Path(bundle_path).resolve()):
            d.append(f"bundle.path {b.get('path')!r} != {str(Path(bundle_path).resolve())!r}")
        if b.get("sha256") != sha256(bundle_bytes):
            d.append("bundle.sha256 is not the file's sha256")
        if b.get("stem") != stem:
            d.append(f"bundle.stem {b.get('stem')!r} != {stem!r}")
    m = payload.get("members")
    if not isinstance(m, dict):
        d.append(f"members is not an object: {m!r}")
    else:
        if m.get("brief") != sha256(brief_bytes):
            d.append("members.brief is not the brief's sha256")
        if m.get("checkpoint", "missing") is not None:
            d.append(f"members.checkpoint should be null: {m.get('checkpoint')!r}")
    if payload.get("rehearsal") != rehearsal:
        d.append(f"rehearsal {payload.get('rehearsal')!r} != {rehearsal!r}")
    if payload.get("checkpoint_dry_run") is not None:
        d.append("checkpoint_dry_run should be null with no checkpoint member")
    if outcome == "opened":
        if not (isinstance(payload.get("sid"), str) and SID_RE.match(payload["sid"])):
            d.append(f"sid {payload.get('sid')!r} is not a session id")
        if not (isinstance(payload.get("tarball"), str) and Path(payload["tarball"]).is_file()):
            d.append(f"tarball {payload.get('tarball')!r} is not an existing file")
        if payload.get("readme_sha256") != sha256(brief_bytes):
            d.append("readme_sha256 is not the brief member's sha256")
        if payload.get("desk") is not None:
            d.append(f"desk should be null on 'opened': {payload.get('desk')!r}")
        expected = scissor_text(stderr)
        if expected is None:
            d.append("stderr carries no scissor-bracketed opener to compare")
        elif payload.get("opener") != expected:
            d.append("opener differs from the scissor-paste text on stderr")
    elif outcome == "rehearsed":
        for k in PACK_KEYS + ("opener",):
            if k != "outcome" and payload.get(k) is not None:
                d.append(f"{k} should be null on 'rehearsed', got {payload.get(k)!r}")
        if payload.get("desk") is not None:
            d.append("desk should be null on 'rehearsed'")
    elif outcome == "second-desk":
        if payload.get("sid") != sid:
            d.append(f"sid {payload.get('sid')!r} != the joined session {sid!r}")
        for k in PACK_KEYS:
            if k not in ("outcome", "sid") and payload.get(k) is not None:
                d.append(f"{k} should be null on 'second-desk', got {payload.get(k)!r}")
        desk = payload.get("desk")
        if not (isinstance(desk, str) and desk and desk in (stderr or "")):
            d.append(f"desk {desk!r} is not the desk name the human summary prints")
        expected = scissor_text(stderr)
        if expected is None:
            d.append("stderr carries no scissor-bracketed opener to compare")
        elif payload.get("opener") != expected:
            d.append("opener differs from the second desk's scissor-paste text")
    return d


def relay_line_defects(payload, *, outcome, sid, round_, from_, awaiting,
                       kind, preserved, block, log_suffix, telemetry):
    """`kind` and `telemetry` take a value, None, or a tuple of accepted
    values; `preserved`/`block`/`log_suffix` None means 'must be null'."""
    d = []
    if payload is None:
        return ["no JSON payload to grade"]
    for k in RELAY_KEYS:
        if k not in payload:
            d.append(f"relay key {k!r} missing")
    if payload.get("outcome") != outcome:
        d.append(f"outcome {payload.get('outcome')!r} != {outcome!r}")
    if payload.get("sid") != sid:
        d.append(f"sid {payload.get('sid')!r} != {sid!r}")
    if payload.get("round") != round_:
        d.append(f"round {payload.get('round')!r} != {round_!r}")
    if payload.get("from") != from_:
        d.append(f"from {payload.get('from')!r} != {from_!r}")
    if payload.get("awaiting") != awaiting:
        d.append(f"awaiting {payload.get('awaiting')!r} != {awaiting!r}")
    accepted_kind = kind if isinstance(kind, tuple) else (kind,)
    if payload.get("kind") not in accepted_kind:
        d.append(f"kind {payload.get('kind')!r} not in {accepted_kind!r}")
    if payload.get("preserved") != preserved:
        d.append(f"preserved {payload.get('preserved')!r} != {preserved!r}")
    if block is None:
        if payload.get("block") is not None:
            d.append("block should be null")
    elif payload.get("block") != block:
        d.append("block is not byte-identical to the human-mode stdout")
    log = payload.get("log")
    if log_suffix is None:
        if log is not None:
            d.append(f"log should be null, got {log!r}")
    elif not (isinstance(log, str) and os.path.isabs(log) and log.endswith(log_suffix)):
        d.append(f"log {log!r} is not an absolute path ending {log_suffix!r}")
    if not isinstance(payload.get("clipboard"), bool):
        d.append(f"clipboard is not a boolean: {payload.get('clipboard')!r}")
    cause = payload.get("cause")
    if outcome == "relay-refused":
        if not (isinstance(cause, str) and cause.strip()):
            d.append(f"cause is not a non-empty string on a refusal: {cause!r}")
    elif cause is not None:
        d.append(f"cause should be null on {outcome!r}: {cause!r}")
    accepted_tel = telemetry if isinstance(telemetry, tuple) else (telemetry,)
    if "exists" in accepted_tel:
        t = payload.get("telemetry")
        if not (isinstance(t, str) and t):
            d.append(f"telemetry should name the relay-refused record: {t!r}")
    elif payload.get("telemetry") not in accepted_tel:
        d.append(f"telemetry {payload.get('telemetry')!r} not in {accepted_tel!r}")
    return d


def version_defects(text, expected):
    if (text or "").strip() != expected:
        return [f"bin/VERSION reads {text.strip()!r}, expected {expected!r}"]
    return []


def record_defects(record, version, required_paths, validator):
    d = []
    if not isinstance(record, dict):
        return ["changelog record is not a JSON object"]
    errors = validator(record)
    if errors:
        d.append("record fails validate_changelog_record: " + "; ".join(map(str, errors)))
    if record.get("version") != version:
        d.append(f"record version {record.get('version')!r} != {version!r}")
    paths = {row.get("path") for row in record.get("surfaces", []) if isinstance(row, dict)}
    for p in required_paths:
        if p not in paths:
            d.append(f"no surfaces row for {p}")
    return d


def tokens_defects(text, tokens, where):
    return [f"{where} does not mention {t!r}" for t in tokens if t not in (text or "")]


def absent_defects(text, phrase, where):
    return [f"{where} still carries {phrase!r}"] if phrase in (text or "") else []


# --------------------------------------------------------------- controls
def controls():
    old_pack = {k: None for k in PACK_KEYS}
    old_pack["outcome"] = "packed"
    stderr = f"x\n{OPENER_BEGIN}\nline one\nline two\n{OPENER_END}\n"
    if not pack_line_defects(old_pack, stderr):
        oracle_broken("pack_line_defects accepted a 0.4.46 pack line without `opener`")
    if pack_line_defects(dict(old_pack, opener="line one\nline two\n"), stderr):
        oracle_broken("pack_line_defects rejected a conforming pack line: "
                      + "; ".join(pack_line_defects(dict(old_pack, opener="line one\nline two\n"), stderr)))
    if not pack_line_defects(dict(old_pack, opener="wrong\n"), stderr):
        oracle_broken("pack_line_defects accepted an opener that is not the scissor text")
    p, d = parse_one_json_line("")
    if p is not None or not d:
        oracle_broken("parse_one_json_line accepted empty stdout")
    p, d = parse_one_json_line('{"a":1}\n{"b":2}\n')
    if not d:
        oracle_broken("parse_one_json_line accepted two lines")
    bb = b"bundle"; br = b"brief"
    good = {k: None for k in PACK_KEYS + ("opener",) + OPEN_ONLY_KEYS}
    good.update(outcome="rehearsed", rehearsal="check",
                bundle={"path": str(Path("/x/y.bale-bundle").resolve()),
                        "sha256": sha256(bb), "stem": "y"},
                members={"brief": sha256(br), "checkpoint": None})
    if open_line_defects(good, outcome="rehearsed", bundle_path="/x/y.bale-bundle",
                         bundle_bytes=bb, brief_bytes=br, stem="y", stderr="",
                         rehearsal="check"):
        oracle_broken("open_line_defects rejected a conforming rehearsed line: "
                      + "; ".join(open_line_defects(good, outcome="rehearsed", bundle_path="/x/y.bale-bundle", bundle_bytes=bb, brief_bytes=br, stem="y", stderr="", rehearsal="check")))
    if not open_line_defects(dict(good, bundle=dict(good["bundle"], sha256="00")),
                             outcome="rehearsed", bundle_path="/x/y.bale-bundle",
                             bundle_bytes=bb, brief_bytes=br, stem="y", stderr="",
                             rehearsal="check"):
        oracle_broken("open_line_defects accepted a wrong bundle.sha256")
    if not open_line_defects({"outcome": "opened"}, outcome="opened",
                             bundle_path="/x/y.bale-bundle", bundle_bytes=bb,
                             brief_bytes=br, stem="y", stderr=""):
        oracle_broken("open_line_defects accepted a bare {outcome: opened}")
    rl = {k: None for k in RELAY_KEYS}
    rl.update(outcome="relayed", sid="s", round=1, **{"from": "worker"},
              awaiting="planner", kind="clarification manifest",
              preserved=".bale/clarifications/s/001.json", block="B\n",
              log="/abs/.bale/logs/s.log", clipboard=False)
    if relay_line_defects(rl, outcome="relayed", sid="s", round_=1, from_="worker",
                          awaiting="planner", kind="clarification manifest",
                          preserved=".bale/clarifications/s/001.json", block="B\n",
                          log_suffix=".bale/logs/s.log", telemetry=None):
        oracle_broken("relay_line_defects rejected a conforming relayed line: "
                      + "; ".join(relay_line_defects(rl, outcome="relayed", sid="s", round_=1, from_="worker", awaiting="planner", kind="clarification manifest", preserved=".bale/clarifications/s/001.json", block="B\n", log_suffix=".bale/logs/s.log", telemetry=None)))
    if not relay_line_defects(dict(rl, block="other\n"), outcome="relayed", sid="s",
                              round_=1, from_="worker", awaiting="planner",
                              kind="clarification manifest",
                              preserved=".bale/clarifications/s/001.json", block="B\n",
                              log_suffix=".bale/logs/s.log", telemetry=None):
        oracle_broken("relay_line_defects accepted a block that differs from the human stdout")
    if not relay_line_defects(dict(rl, outcome="relay-refused", cause=""),
                              outcome="relay-refused", sid="s", round_=None,
                              from_=None, awaiting=None, kind=None, preserved=None,
                              block=None, log_suffix=None, telemetry=None):
        oracle_broken("relay_line_defects accepted a refusal with an empty cause")
    if not version_defects("0.4.47\n", EXPECTED_VERSION):
        oracle_broken("version_defects accepted 0.4.47")
    if not record_defects({"version": EXPECTED_VERSION}, EXPECTED_VERSION,
                          ["bin/bale"], lambda r: ["missing surfaces"]):
        oracle_broken("record_defects accepted a record the validator rejects")
    if not tokens_defects("abc", ["format_open_json"], "x"):
        oracle_broken("tokens_defects accepted text lacking the token")
    if not absent_defects("still deliberately not part of this contract yet",
                          "deliberately not part of this contract yet", "x"):
        oracle_broken("absent_defects accepted text carrying the retired sentence")
    if scissor_text(f"{OPENER_BEGIN}\na\nb\n{OPENER_END}\n") != "a\nb\n":
        oracle_broken("scissor_text does not cut the paste text")
    print("[oracle] controls: every detector fires on its known-bad input")


# ----------------------------------------------------------------- probes
def probe_pack_opener():
    repo = fresh_repo()
    sid, r = pack_read_only(repo, "pack")
    payload, d = parse_one_json_line(r.stdout)
    d += pack_line_defects(payload, r.stderr)
    verdict("pack --json line carries `opener`, the scissor-paste text; keys unchanged", d)


def probe_open_json():
    repo = fresh_repo()
    bundle, stem, brief = craft_bundle("open")
    bb = bundle.read_bytes()
    r = bale(["open", str(bundle), "--json"], repo)
    payload, d = parse_one_json_line(r.stdout)
    d += open_line_defects(payload, outcome="opened", bundle_path=bundle,
                           bundle_bytes=bb, brief_bytes=brief, stem=stem,
                           stderr=r.stderr)
    if r.returncode != 0:
        d.append(f"exit {r.returncode} != 0")
    verdict("open --json: one line, outcome opened, pack keys, bundle, members", d)
    sid = payload.get("sid") if payload else None
    r2 = bale(["open", str(bundle), "--json"], repo)
    payload2, d = parse_one_json_line(r2.stdout)
    d += open_line_defects(payload2, outcome="second-desk", bundle_path=bundle,
                           bundle_bytes=bb, brief_bytes=brief, stem=stem,
                           stderr=r2.stderr, sid=sid)
    if r2.returncode != 0:
        d.append(f"exit {r2.returncode} != 0")
    verdict("open --json on a still-open bundle: outcome second-desk, desk named", d)


def probe_open_rehearsals():
    for flag, name in (("--check", "check"), ("--dry-run", "dry-run")):
        repo = fresh_repo()
        bundle, stem, brief = craft_bundle(name)
        bb = bundle.read_bytes()
        r = bale(["open", str(bundle), flag, "--json"], repo)
        payload, d = parse_one_json_line(r.stdout)
        d += open_line_defects(payload, outcome="rehearsed", bundle_path=bundle,
                               bundle_bytes=bb, brief_bytes=brief, stem=stem,
                               stderr=r.stderr, rehearsal=name)
        if r.returncode != 0:
            d.append(f"exit {r.returncode} != 0")
        if (repo / ".bale" / "sessions").exists():
            d.append("the rehearsal wrote .bale/sessions/ into the repo")
        verdict(f"open {flag} --json: outcome rehearsed/{name}, nothing written", d)


def probe_open_human_and_refusal():
    repo = fresh_repo()
    bundle, stem, brief = craft_bundle("human")
    r = bale(["open", str(bundle)], repo)
    d = []
    if r.returncode != 0:
        d.append(f"exit {r.returncode} != 0")
    if OPENER_BEGIN not in r.stdout.splitlines():
        d.append("human-mode stdout no longer carries the opener block")
    if any(ln.startswith('{"outcome"') for ln in r.stdout.splitlines()):
        d.append("human-mode stdout carries a JSON report line")
    verdict("open without --json: human mode unchanged (opener on stdout, no JSON)", d)
    missing = BUNDLES / "no-such.bale-bundle"
    r = bale(["open", str(missing), "--json"], repo)
    d = [] if r.returncode == 1 and r.stdout == "" else [
        f"exit {r.returncode}, stdout {r.stdout!r}"]
    verdict("open refusal under --json: exit 1, nothing on stdout (unchanged)", d)


def probe_relay_json():
    repo = fresh_repo()
    sid, _ = pack_read_only(repo, "relay")
    m = clarification_manifest(repo, sid)
    r = bale(["relay", sid, str(m), "--json"], repo)
    payload, d = parse_one_json_line(r.stdout)
    human = bale(["relay", sid], repo)   # the no-file re-emit, human mode
    if human.returncode != 0 or not human.stdout.startswith(f"BALE EXCHANGE BEGIN {sid}"):
        d.append("the human-mode re-emit did not print the block on stdout")
    d += relay_line_defects(payload, outcome="relayed", sid=sid, round_=1,
                            from_="worker", awaiting="planner",
                            kind="clarification manifest",
                            preserved=f".bale/clarifications/{sid}/001.json",
                            block=human.stdout, log_suffix=f".bale/logs/{sid}.log",
                            telemetry=None)
    if r.returncode != 0:
        d.append(f"exit {r.returncode} != 0")
    verdict("relay --json of a clarification manifest: outcome relayed, block == human stdout", d)
    r2 = bale(["relay", sid, "--json"], repo)
    payload2, d = parse_one_json_line(r2.stdout)
    d += relay_line_defects(payload2, outcome="re-emitted", sid=sid, round_=1,
                            from_="worker", awaiting="planner",
                            kind=(None,) + RELAY_KINDS, preserved=None,
                            block=human.stdout, log_suffix=f".bale/logs/{sid}.log",
                            telemetry=None)
    if r2.returncode != 0:
        d.append(f"exit {r2.returncode} != 0")
    verdict("relay --json with no file: outcome re-emitted, same block, nothing preserved", d)


def probe_relay_human_unchanged():
    repo = fresh_repo()
    sid, _ = pack_read_only(repo, "relayh")
    m = clarification_manifest(repo, sid)
    r = bale(["relay", sid, str(m)], repo)
    d = []
    if r.returncode != 0:
        d.append(f"exit {r.returncode} != 0")
    if not r.stdout.startswith(f"BALE EXCHANGE BEGIN {sid}\n"):
        d.append("human-mode stdout does not start with the exchange block")
    if not r.stdout.rstrip("\n").endswith("BALE EXCHANGE END"):
        d.append("human-mode stdout does not end with the exchange block")
    if "[RELAYED]" not in r.stderr:
        d.append("stderr lacks the [RELAYED] summary")
    verdict("relay without --json: stdout is the block alone, summary on stderr", d)


def probe_relay_refusals():
    repo = fresh_repo()
    sid, _ = pack_read_only(repo, "relayr")
    bad_file = repo / "bad.json"
    bad_file.write_text('{"nope": 1}\n', encoding="utf-8")
    r = bale(["relay", sid, str(bad_file), "--json"], repo)
    payload, d = parse_one_json_line(r.stdout)
    d += relay_line_defects(payload, outcome="relay-refused", sid=sid, round_=None,
                            from_=None, awaiting=None, kind=None, preserved=None,
                            block=None, log_suffix=f".bale/logs/{sid}.log",
                            telemetry="exists")
    if payload and isinstance(payload.get("telemetry"), str) and \
            not (repo / payload["telemetry"]).is_file():
        d.append(f"telemetry names {payload['telemetry']!r}, which does not exist")
    if r.returncode != 1:
        d.append(f"exit {r.returncode} != 1")
    verdict("relay --json ingest refusal: outcome relay-refused, cause, telemetry record", d)
    m = clarification_manifest(repo, sid)
    r2 = bale(["relay", "no-such-sid", str(m), "--json"], repo)
    payload2, d = parse_one_json_line(r2.stdout)
    d += relay_line_defects(payload2, outcome="relay-refused", sid="no-such-sid",
                            round_=None, from_=None, awaiting=None, kind=None,
                            preserved=None, block=None, log_suffix=None,
                            telemetry=None)
    if r2.returncode != 1:
        d.append(f"exit {r2.returncode} != 1")
    verdict("relay --json session-gate refusal: relay-refused, no telemetry, no log", d)
    h = bale(["relay", sid, str(bad_file)], repo)
    d = [] if h.returncode == 1 and h.stdout == "" else [
        f"human refusal: exit {h.returncode}, stdout {h.stdout!r}"]
    verdict("relay refusal without --json: nothing on stdout, exit 1 (unchanged)", d)


def probe_version_and_record():
    label = f"bin/VERSION minted {EXPECTED_VERSION}"
    d = version_defects((TREE / "bin" / "VERSION").read_text(encoding="utf-8"),
                        EXPECTED_VERSION)
    v = bale(["--version"], SCRATCH)
    if v.stdout.strip() != f"bale {EXPECTED_VERSION}":
        d.append(f"`bale --version` printed {v.stdout.strip()!r}")
    verdict(label, d)
    label = f"claude/changelog/{EXPECTED_VERSION}.json exists, validates, names the surfaces"
    rec_path = TREE / "claude" / "changelog" / f"{EXPECTED_VERSION}.json"
    if not rec_path.is_file():
        bad(label, f"{rec_path.relative_to(TREE)} is missing")
        return
    spec = importlib.util.spec_from_file_location(
        "bale_validate", TREE / "bin" / "bale_validate.py")
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(TREE / "bin"))
    spec.loader.exec_module(mod)
    try:
        record = json.loads(rec_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        bad(label, f"record is not JSON: {e}")
        return
    verdict(label, record_defects(
        record, EXPECTED_VERSION,
        ["bin/bale", "bin/bale_open.py", "bin/bale_relay.py", "bin/bale_pack.py",
         "bin/bale_report.py"], mod.validate_changelog_record))


def probe_docs_and_help():
    h = bale(["open", "--help"], SCRATCH)
    verdict("`bale open --help` names --json and its owner format_open_json",
            tokens_defects(h.stdout, ["--json", "format_open_json"], "bale open --help"))
    h = bale(["relay", "--help"], SCRATCH)
    verdict("`bale relay --help` names --json and its owner format_relay_json",
            tokens_defects(h.stdout, ["--json", "format_relay_json"], "bale relay --help"))
    bale_md = (TREE / "BALE.md").read_text(encoding="utf-8")
    d = tokens_defects(bale_md, ["format_open_json", "format_relay_json"], "BALE.md")
    d += absent_defects(bale_md, "deliberately not part of this contract yet", "BALE.md")
    verdict("BALE.md names the two owners and retires the 'opener not yet' sentence", d)
    report = (TREE / "bin" / "bale_report.py").read_text(encoding="utf-8")
    verdict("bin/bale_report.py owns the six new outcome values",
            tokens_defects(report, ["opened", "second-desk", "rehearsed", "relayed",
                                    "re-emitted", "relay-refused"], "bin/bale_report.py"))


def main():
    if not BALE.is_file() or not CRAFT.is_file():
        oracle_broken(f"{BALE} or {CRAFT} is not a file — not run from the tree root?")
    controls()
    for probe in (probe_pack_opener, probe_open_json, probe_open_rehearsals,
                  probe_open_human_and_refusal, probe_relay_json,
                  probe_relay_human_unchanged, probe_relay_refusals,
                  probe_version_and_record, probe_docs_and_help):
        probe()
    shutil.rmtree(SCRATCH, ignore_errors=True)
    print(f"[oracle] {len(FAILS)} failed probe(s)")
    sys.stdout.flush()
    os._exit(1 if FAILS else 0)


main()
ORACLE
