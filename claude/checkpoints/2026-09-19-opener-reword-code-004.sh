#!/usr/bin/env bash
# Blind checkpoint v1 — child session slug opener-reword-code (the code half;
# its sid is whatever pack allocates, 2026-09-19-opener-reword-code-004 expected).
# Authored at the sub-master split of 2026-09-19-opener-reword-doc-sweep-r2-003,
# from the child's request and the r2 brief's VERBATIM blocks (extracted
# mechanically from the brief's bytes), before any implementation exists.
# Outcome-only: it drives the staged tree's own bin/bale through hermetic
# packs in fresh per-scenario fixtures under /tmp and grades what pack
# emits and ships — never how the worker got there.
# Exit: 0 every probe passed; 1 at least one [FAIL] (HOLD); 2 the oracle
# itself could not run (fixture setup broke, not the work).
set -u
if [ ! -f bin/bale ] || [ ! -d schemas ]; then
  echo "checkpoint: not at a bale-src tree root (cwd=$(pwd))" >&2
  exit 2
fi
command -v python3 >/dev/null 2>&1 || { echo "checkpoint: python3 not found" >&2; exit 2; }
command -v git >/dev/null 2>&1 || { echo "checkpoint: git not found" >&2; exit 2; }
python3 - <<'PYEOF'
import hashlib, json, os, pty, re, select, shutil, subprocess, sys, tarfile, tempfile, time
from pathlib import Path

ROOT = Path.cwd()
V = {'OPENER_AUTHORITY': 'The docs and tools in the tarball are mine, written for this workflow; CLAUDE.md and the four docs beside it are my instructions for this session.', 'OPENER_READING_WITH_README': 'Read manifest.json first, then CLAUDE.md, then README.md, my brief for this session; CLAUDE.md says when the other four docs are needed.', 'OPENER_READING_NO_README': 'Read manifest.json first, then CLAUDE.md; CLAUDE.md says when the other four docs are needed.', 'OPENER_TOOLS': 'tools/craft_response.py and tools/response_lint.py are stdlib-only formatters with no network access — conveniences over the docs, which are the contract; read them before you run them, and a response assembled by hand is just as valid.', 'OPENER_CLOCK': "bale's dates are UTC and can run a day ahead of this chat's date (a timezone gap, not an error); date what you write from the session id.", 'OPENER_ASK': 'If you need something from me, a fact from my machine or a decision, end that turn with the matching block from TARBALL.md (a probe, a light question block, or a clarification response) rather than a question in prose, which tends to get lost.', 'OPENER_DELIVERABLE_WORKER': 'This is a worker session: what I need back is one response tarball carrying the finished work.', 'OPENER_DELIVERABLE_PLANNER': "This is a planner session: nothing lands from it, so don't build a response tarball, even an empty one. What I need back is your answer in chat and, for each session I ask you to author, a crafter bundle with its bale open line, as PLANNER.md describes."}
RETIRED = [
    "Please examine the tarball contents",
    "Every turn you end in this session takes one machine-recognizable shape",
    "Session ids and every bale timestamp are UTC",
    "read CLAUDE.md and the four docs beside it as my instructions",
]
BEGIN = "--8<-- session opener (copy everything between the scissor lines) --8<--"
END = "--8<-- end session opener --8<--"
GOAL_PREFIX = "Goal, verbatim from the request manifest: "
GOAL = "Checkpoint fixture goal for the opener"
PROSE = "Brief prose typed by the checkpoint editor stub, with an apostrophe: it's here."

failed = []
SAMPLE = {}
def verdict(ok, label, detail=""):
    print(("[PASS] " if ok else "[FAIL] ") + label)
    if not ok:
        failed.append(label)
        if detail:
            print("       " + detail.replace("\n", "\n       ")[:1500])

class SetupError(Exception):
    pass

def collapse(s):
    return " ".join(s.split())

def fixture(tag):
    tmp = Path(tempfile.mkdtemp(prefix=f"cp-a-{tag}-"))
    home = tmp / "home"; home.mkdir()
    (home / ".gitconfig").write_text(
        "[user]\n\tname = Checkpoint Sandbox\n\temail = cp@example.invalid\n"
        "[init]\n\tdefaultBranch = main\n", encoding="utf-8")
    install = tmp / "install"; install.mkdir()
    for tree in ("bin", "docs", "schemas", "tools"):
        if not (ROOT / tree).is_dir():
            raise SetupError(f"tree root has no {tree}/")
        shutil.copytree(ROOT / tree, install / tree)
    repo = tmp / "project"; repo.mkdir()
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home),
           "EDITOR": "/bin/true", "VISUAL": "/bin/true",
           "LANG": os.environ.get("LANG", "C.UTF-8"),
           "BALE_INSTALL": str(tmp / "bale-install-sandbox")}
    for cmd in (["git", "init", "-b", "main"], None, ["git", "add", "hello.txt"],
                ["git", "commit", "-m", "init"]):
        if cmd is None:
            (repo / "hello.txt").write_text("hello\n", encoding="utf-8"); continue
        r = subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise SetupError(f"{cmd} failed: {r.stderr}")
    return tmp, install, repo, env

def run(install, repo, env, args):
    return subprocess.run([sys.executable, str(install / "bin" / "bale"), *args],
                          cwd=repo, env=env, stdin=subprocess.DEVNULL,
                          capture_output=True, text=True, timeout=180)

def run_pty(install, repo, env, args):
    master, slave = pty.openpty()
    try:
        proc = subprocess.Popen([sys.executable, str(install / "bin" / "bale"), *args],
                                cwd=repo, env=env, stdin=slave, stdout=slave,
                                stderr=slave, close_fds=True)
        os.close(slave); slave = None
        chunks, deadline = [], time.monotonic() + 120
        while True:
            if time.monotonic() > deadline:
                proc.kill(); return -9, b"".join(chunks).decode(errors="replace")
            r, _, _ = select.select([master], [], [], 0.1)
            if master in r:
                try:
                    c = os.read(master, 4096)
                except OSError:
                    break
                if not c:
                    break
                chunks.append(c)
            elif proc.poll() is not None:
                break
        code = proc.wait(timeout=60)
    finally:
        if slave is not None:
            os.close(slave)
        os.close(master)
    return code, b"".join(chunks).decode(errors="replace").replace("\r\n", "\n")

def segment(text):
    b, e = text.find(BEGIN), text.find(END)
    if b < 0 or e < 0 or e < b:
        return None
    return text[b + len(BEGIN):e]

def row(text, marker):
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith(marker):
            return s[len(marker):].strip()
    return None

def request_of(repo, sid):
    tb = repo / ".bale" / "outbox" / f"request-{sid}.tar.gz"
    if not tb.is_file():
        return None, None
    nnn = sid.rsplit("-", 1)[-1]
    with tarfile.open(tb, "r:gz") as tf:
        names = tf.getnames()
        man = json.load(tf.extractfile(f"request-{nnn}/manifest.json"))
        rm = f"request-{nnn}/README.md"
        readme = tf.extractfile(rm).read() if rm in names else None
    return man, readme

def check_opener(tag, text, *, read_only, with_readme, manifest):
    seg = segment(text)
    verdict(seg is not None, f"{tag}: opener block framed by both scissor lines")
    if seg is None:
        return
    lines = [ln for ln in text.splitlines() if ln.strip()]
    verdict(bool(lines) and lines[-1] == END, f"{tag}: opener ends the report stream")
    c = collapse(seg)
    reading = V["OPENER_READING_WITH_README"] if with_readme else V["OPENER_READING_NO_README"]
    other_reading = V["OPENER_READING_NO_README"] if with_readme else V["OPENER_READING_WITH_README"]
    deliver = V["OPENER_DELIVERABLE_PLANNER"] if read_only else V["OPENER_DELIVERABLE_WORKER"]
    other_deliver = V["OPENER_DELIVERABLE_WORKER"] if read_only else V["OPENER_DELIVERABLE_PLANNER"]
    for key, s in (("authority", V["OPENER_AUTHORITY"]), ("reading", reading),
                   ("tools", V["OPENER_TOOLS"]), ("clock", V["OPENER_CLOCK"]),
                   ("ask", V["OPENER_ASK"]), ("deliverable", deliver)):
        verdict(collapse(s) in c, f"{tag}: {key} sentence verbatim (whitespace collapsed)",
                f"missing: {s}")
    verdict(collapse(other_reading) not in c, f"{tag}: the other reading form is absent")
    verdict(collapse(other_deliver) not in c, f"{tag}: the other session mode's deliverable is absent")
    for old in RETIRED:
        verdict(collapse(old) not in c, f"{tag}: retired wording absent: {old[:40]}")
    verdict(any(ln.strip() == V["OPENER_CLOCK"] for ln in seg.splitlines()),
            f"{tag}: clock sentence is its own single line")
    goal_lines = [ln.strip() for ln in seg.splitlines() if ln.strip().startswith(GOAL_PREFIX)]
    verdict(goal_lines == [GOAL_PREFIX + GOAL], f"{tag}: goal rides one unwrapped line")
    packed = (manifest or {}).get("provenance", {}).get("packed_at")
    verdict(packed is not None and any(ln.strip() == f"Packed at {packed} (UTC)." for ln in seg.splitlines()),
            f"{tag}: Packed at line carries provenance.packed_at on its own line")
    order = [GOAL_PREFIX, V["OPENER_AUTHORITY"], reading, V["OPENER_TOOLS"], "Packed at ",
             V["OPENER_CLOCK"], V["OPENER_ASK"], deliver]
    idx = [c.find(collapse(s)) for s in order]
    verdict(all(i >= 0 for i in idx) and idx == sorted(idx),
            f"{tag}: order goal, authority, reading, tools, packed-at, clock, ask, deliverable",
            f"positions: {idx}")
    verdict(c.endswith(collapse(deliver)), f"{tag}: the deliverable closes the block")

def check_readme_key(tag, manifest, readme_bytes, echo_sha):
    if manifest is None:
        verdict(False, f"{tag}: request tarball found in the outbox"); return
    verdict("readme" in manifest, f"{tag}: manifest stamps a top-level readme key")
    val = manifest.get("readme", "ABSENT")
    if readme_bytes is None:
        verdict(val is None, f"{tag}: readme is null when no README ships", f"got {val!r}")
    else:
        sha = hashlib.sha256(readme_bytes).hexdigest()
        ok = isinstance(val, dict) and set(val) == {"path", "sha256"} and \
            val.get("path") == "README.md" and val.get("sha256") == sha
        verdict(ok, f"{tag}: readme is exactly {{path: README.md, sha256: shipped bytes}}",
                f"got {val!r}, shipped sha {sha}")
        verdict(echo_sha == sha, f"{tag}: report's readme sha256 echo equals the shipped bytes",
                f"echo {echo_sha!r} vs {sha}")
    verdict("readme" not in manifest.get("provenance", {}), f"{tag}: readme is not under provenance")

def scenario(tag, *, read_only, with_readme, json_mode=False):
    tmp, install, repo, env = fixture(tag)
    try:
        args = ["pack", GOAL, "--slug", f"cp-{tag}", "--include", "hello.txt"]
        if read_only:
            args.append("--read-only")
        if with_readme:
            brief = tmp / f"brief-{tag}.md"
            brief.write_text(f"# Checkpoint brief {tag}\n\n{PROSE}\n", encoding="utf-8")
            args += ["--readme-file", str(brief)]
        else:
            args.append("--no-readme")
        if json_mode:
            args.append("--json")
        r = run(install, repo, env, args)
        verdict(r.returncode == 0, f"{tag}: pack exits 0", r.stderr[-800:])
        if r.returncode != 0:
            return
        if json_mode:
            out_lines = [ln for ln in r.stdout.splitlines() if ln.strip()]
            verdict(len(out_lines) == 1, f"{tag}: --json stdout stays one line")
            try:
                payload = json.loads(out_lines[0])
            except Exception:
                verdict(False, f"{tag}: --json stdout parses"); return
            sid, echo, text = payload.get("sid"), payload.get("readme_sha256"), r.stderr
            verdict(segment(r.stdout) is None, f"{tag}: opener stays off json stdout")
        else:
            text = r.stdout
            sid, echo = row(text, "session id:"), row(text, "readme sha256:")
        man, readme = request_of(repo, sid or "none")
        check_opener(tag, text, read_only=read_only, with_readme=with_readme, manifest=man)
        check_readme_key(tag, man, readme, echo)
        if tag == "worker-readme" and man is not None:
            SAMPLE["manifest"] = man
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def scaffold_scenario():
    tag = "edit-scaffold"
    tmp, install, repo, env = fixture(tag)
    try:
        seed_copy = tmp / "seed-seen-by-editor.md"
        stub = tmp / "editor-stub.sh"
        prose_file = tmp / "prose-to-type.txt"
        prose_file.write_text("\n" + PROSE + "\n", encoding="utf-8")
        stub.write_text("#!/bin/sh\n"
                        f"cp \"$1\" '{seed_copy}'\n"
                        f"cat '{prose_file}' >> \"$1\"\n", encoding="utf-8")
        stub.chmod(0o755)
        env = dict(env, EDITOR=str(stub), VISUAL=str(stub))
        code, out = run_pty(install, repo, env,
                            ["pack", GOAL, "--slug", "cp-edit", "--include", "hello.txt", "--edit"])
        verdict(code == 0, f"{tag}: --edit pack exits 0", out[-800:])
        if code != 0:
            return
        if not seed_copy.is_file():
            raise SetupError("editor stub never ran — the --edit path did not open $EDITOR")
        seed = seed_copy.read_text(encoding="utf-8")
        comment_lines = []
        for m in re.finditer(r"<!--(.*?)-->", seed, re.S):
            comment_lines += [ln.strip() for ln in m.group(1).splitlines() if ln.strip()]
        sid = row(out, "session id:")
        man, readme = request_of(repo, sid or "none")
        verdict(readme is not None, f"{tag}: the typed prose ships a README")
        if readme is None:
            return
        shipped = readme.decode("utf-8", errors="replace")
        verdict(PROSE in shipped, f"{tag}: the packer's prose ships as typed")
        leaked = [ln for ln in comment_lines if ln in shipped]
        verdict(not leaked and "<!--" not in shipped,
                f"{tag}: no line of the scaffold's instruction comment ships",
                f"leaked: {leaked[:3]}")
        check_readme_key(tag, man, readme, row(out, "readme sha256:"))
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

def schema_probe():
    p = ROOT / "schemas" / "request-manifest.schema.json"
    try:
        s = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        raise SetupError(f"request-manifest schema unreadable: {e}")
    props = s.get("properties", {})
    verdict("readme" in props, "schema: request manifest admits a top-level readme key")
    verdict("readme" not in s.get("required", []), "schema: readme is admitted, not required")
    verdict(s.get("additionalProperties") is False, "schema: the top level stays a closed object")
    try:
        import jsonschema
    except ImportError:
        print("[SKIP] schema: jsonschema not installed — instance validation not run")
        return
    if SAMPLE.get("manifest") is None:
        print("[SKIP] schema: no packed manifest to validate (the worker-readme pack failed above)")
        return
    for label, val, want in (("null", None, True),
                             ("two-key object", {"path": "README.md", "sha256": "0" * 64}, True),
                             ("three-key object", {"path": "README.md", "sha256": "0" * 64, "x": 1}, False),
                             ("absent", "ABSENT", True)):
        inst = dict(SAMPLE["manifest"])
        if val == "ABSENT":
            inst.pop("readme", None)
        else:
            inst["readme"] = val
        try:
            jsonschema.validate(inst, s)
            ok = True
        except jsonschema.ValidationError:
            ok = False
        verdict(ok == want, f"schema: a packed manifest with readme {label} is {'valid' if want else 'invalid'}")

def selfcontainment_probe():
    t = ROOT / "tests" / "test_global_doc_selfcontainment.py"
    if not t.is_file():
        verdict(False, "self-containment suite present"); return
    r = subprocess.run([sys.executable, str(t)], cwd=ROOT / "tests", capture_output=True,
                       text=True, timeout=300)
    verdict(r.returncode == 0, "global docs and schema descriptions stay self-contained",
            (r.stdout + r.stderr)[-1200:])

try:
    for tag, ro, rd, js in (("worker-noreadme", False, False, False),
                            ("worker-readme", False, True, False),
                            ("planner-noreadme", True, False, False),
                            ("planner-readme", True, True, False),
                            ("worker-readme-json", False, True, True),
                            ("planner-noreadme-json", True, False, True)):
        scenario(tag, read_only=ro, with_readme=rd, json_mode=js)
    scaffold_scenario()
    schema_probe()
    selfcontainment_probe()
except SetupError as e:
    print(f"checkpoint errored: {e}", file=sys.stderr)
    sys.exit(2)
print(f"checkpoint: {len(failed)} probe(s) failed")
sys.exit(1 if failed else 0)
PYEOF
