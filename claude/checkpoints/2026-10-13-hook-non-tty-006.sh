#!/usr/bin/env bash
# Blind checkpoint — session hook-non-tty (bale-src), version 1.
# Authored 2026-10-13 by sitting 2026-10-13-twine-obligations-desk-001,
# from the request, before any implementation existed.
#
# Outcome contract only: with a configured global-layer post_pack hook
# and standard input not a terminal, a pack and an open --json offer no
# prompt, decline with the fixed line, and do not invoke the hook; the
# open's stdout stays one JSON line; the release is recorded. The cwd is
# the staged tree; the scenarios copy its bin/, docs/, schemas/ and
# tools/ into a scratch install under a private mktemp directory (so the
# install's user/ layer is the oracle's, never the operator's) and drive
# that install inside fresh scratch repos, one per scenario.
# Exit 0 = every probe passed; 1 = at least one probe failed (a crash or
# refusal of the code under test is a probe failure, exit 1, never 2);
# 2 = this oracle is defective (a control failed, git or file setup
# failed, or an unplanned exception) — never a verdict on the work.
# Verdict lines carry the label alone; detail follows on "  detail:" lines.
# No network; starts only the processes it waits for; needs no sid,
# manifest or own path.
set -u
exec python3 -I -B - <<'ORACLE'
import json, os, shutil, subprocess, sys, tempfile
from pathlib import Path

TREE = Path.cwd().resolve()
TIMEOUT = 120
DECLINE_LINE = "declined (stdin is not a terminal; the prompt was not offered); not invoking."
PROMPT_LINE = "run this hook?"
MARKER = ".oracle-hook-ran"

# ----------------------------------------------------------- detectors
def run(argv, cwd, stdin_null=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith("BALE_")}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        p = subprocess.run(argv, cwd=str(cwd), env=env, capture_output=True,
                           text=True, timeout=TIMEOUT,
                           stdin=subprocess.DEVNULL if stdin_null else None)
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

def has_line(text: str, needle: str) -> bool:
    return needle in text

def fixture_fail(msg: str) -> None:
    print(f"oracle fixture failure: {msg}", file=sys.stderr)
    sys.exit(2)

def git(repo, *args):
    r = subprocess.run(["git", *args], cwd=str(repo), capture_output=True,
                       text=True, timeout=TIMEOUT)
    if r.returncode != 0:
        fixture_fail(f"git {' '.join(args)}: {r.stderr.strip()}")

def make_install(root: Path) -> Path:
    inst = root / "install"
    for d in ("bin", "docs", "schemas", "tools"):
        src = TREE / d
        if not src.is_dir():
            fixture_fail(f"{d}/ missing from the tree")
        shutil.copytree(src, inst / d, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    user = inst / "user"; user.mkdir()
    (user / "bale.toml").write_text('[hooks]\npost_pack = "hook.sh"\n', encoding="utf-8")
    hook = user / "hook.sh"
    hook.write_text('#!/bin/sh\ntouch "$BALE_REPO_ROOT/' + MARKER + '"\n', encoding="utf-8")
    hook.chmod(0o755)
    return inst

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

# ------------------------------------------------------------- controls
def control(name: str, ok: bool) -> None:
    if not ok:
        print(f"oracle control failed: {name}", file=sys.stderr)
        sys.exit(2)

def run_controls() -> None:
    control("one_json_line-positive", one_json_line('{"a": 1}\n') == {"a": 1})
    control("one_json_line-two-lines", one_json_line('{"a": 1}\n{"b": 2}\n') is None)
    control("one_json_line-garbage", one_json_line("x\n") is None)
    control("has_line-positive", has_line("a\n" + DECLINE_LINE + "\nb", DECLINE_LINE))
    control("has_line-negative", not has_line("a\nb", DECLINE_LINE))
    control("has_line-prompt", has_line("  " + PROMPT_LINE + " [Y/n] ", PROMPT_LINE))

# --------------------------------------------------------------- probes
failures = []
def probe(label: str, ok: bool, detail: str = "") -> None:
    print(f"[{'PASS' if ok else 'FAIL'}] {label}")
    if detail and not ok:
        print(f"  detail: {detail}")
    if not ok:
        failures.append(label)

def tail(err: str) -> str:
    return err.strip().splitlines()[-1] if err.strip() else "(no stderr)"

def main() -> int:
    run_controls()
    root = Path(tempfile.mkdtemp(prefix="hook-oracle-"))
    try:
        inst = make_install(root)
        bale = inst / "bin" / "bale"
        py = sys.executable

        # scenario 1: a session pack, human mode, stdin from /dev/null
        repo = scratch_repo(root, "pack")
        rc, out, err = run([py, "-B", str(bale), "pack", "hook probe", "--slug", "hook",
                            "--include", "f.txt", "--no-readme", "--expects-probe", "no"], repo)
        text = out + err
        probe("s1-pack-exit-0", rc == 0, f"exit {rc}; {tail(err)}")
        probe("s1-no-prompt-offered", not has_line(text, PROMPT_LINE),
              "the pack printed the prompt to a non-terminal stdin")
        probe("s1-decline-line", has_line(text, DECLINE_LINE),
              "the fixed non-terminal decline line is absent")
        probe("s1-hook-not-invoked", not (repo / MARKER).exists(),
              "the hook ran (its marker exists)")

        # scenario 2: bale open <bundle> --json, stdin from /dev/null — the
        # harness's exact argv; the bundle is crafted by the tree's own tool
        repo = scratch_repo(root, "open")
        crafter = inst / "tools" / "craft_response.py"
        stem = "2026-10-13-oracle-hook"
        rc, out, err = run([py, "-I", str(crafter), "--bundle", stem, "--no-brief",
                            "--pack-arg", "hook probe", "--pack-arg=--slug", "--pack-arg", "hook",
                            "--pack-arg=--include", "--pack-arg", "f.txt",
                            "--pack-arg=--expects-probe", "--pack-arg", "no",
                            "--out-dir", str(root)], repo)
        bundle = root / f"{stem}.bale-bundle"
        if rc != 0 or not bundle.is_file():
            fixture_fail(f"crafter --bundle exit {rc}: {tail(err)}")
        rc, out, err = run([py, "-B", str(bale), "open", str(bundle), "--json"], repo)
        line = one_json_line(out)
        probe("s2-open-exit-0", rc == 0, f"exit {rc}; {tail(err)}")
        probe("s2-open-one-json-line", line is not None and line.get("outcome") == "opened",
              "stdout is not exactly one JSON object line with outcome opened")
        probe("s2-no-prompt-offered", not has_line(out + err, PROMPT_LINE),
              "the open printed the prompt to a non-terminal stdin")
        probe("s2-decline-line-on-stderr", has_line(err, DECLINE_LINE),
              "the fixed non-terminal decline line is absent from stderr")
        probe("s2-hook-not-invoked", not (repo / MARKER).exists(),
              "the hook ran (its marker exists)")

        # the release is recorded
        version = (TREE / "bin" / "VERSION").read_text(encoding="utf-8").strip()
        record = TREE / "claude" / "changelog" / f"{version}.json"
        rec_ok = False; detail = f"{record.relative_to(TREE)} missing"
        if record.is_file():
            try:
                rec = json.loads(record.read_text(encoding="utf-8"))
                paths = {s.get("path") for s in rec.get("surfaces", []) if isinstance(s, dict)}
                rec_ok = rec.get("version") == version and "bin/bale" in paths
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
