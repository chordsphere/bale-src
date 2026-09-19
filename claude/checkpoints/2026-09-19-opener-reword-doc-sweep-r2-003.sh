#!/usr/bin/env bash
# Blind checkpoint v2 — 2026-09-19 opener reword, readme key, doc sweep (r2).
# Authored at the desk (2026-09-19-session-fix-002) from the request,
# before any implementation exists. Runs with cwd = the staging tree.
# Writes only under a mkdtemp scratch directory, removed on exit.
# Exit 0 = every probe passed; 1 = at least one [FAIL]; 2 = the
# checkpoint itself errored.
set -u
command -v python3 >/dev/null 2>&1 || { echo "checkpoint error: python3 not found"; exit 2; }
command -v git >/dev/null 2>&1 || { echo "checkpoint error: git not found"; exit 2; }
python3 - "$PWD" <<'CKPT_PY'
import hashlib, json, os, re, subprocess, sys, tarfile, tempfile, time, traceback
from pathlib import Path

ROOT = Path(sys.argv[1]).resolve()
S = json.loads(r"""{
  "OPENER_AUTHORITY": "The docs and tools in the tarball are mine, written for this workflow; CLAUDE.md and the four docs beside it are my instructions for this session.",
  "OPENER_READING_WITH_README": "Read manifest.json first, then CLAUDE.md, then README.md, my brief for this session; CLAUDE.md says when the other four docs are needed.",
  "OPENER_READING_NO_README": "Read manifest.json first, then CLAUDE.md; CLAUDE.md says when the other four docs are needed.",
  "OPENER_TOOLS": "tools/craft_response.py and tools/response_lint.py are stdlib-only formatters with no network access \u2014 conveniences over the docs, which are the contract; read them before you run them, and a response assembled by hand is just as valid.",
  "OPENER_CLOCK": "bale's dates are UTC and can run a day ahead of this chat's date (a timezone gap, not an error); date what you write from the session id.",
  "OPENER_ASK": "If you need something from me, a fact from my machine or a decision, end that turn with the matching block from TARBALL.md (a probe, a light question block, or a clarification response) rather than a question in prose, which tends to get lost.",
  "OPENER_DELIVERABLE_WORKER": "This is a worker session: what I need back is one response tarball carrying the finished work.",
  "OPENER_DELIVERABLE_PLANNER": "This is a planner session: nothing lands from it, so don't build a response tarball, even an empty one. What I need back is your answer in chat and, for each session I ask you to author, a crafter bundle with its bale open line, as PLANNER.md describes.",
  "DOC_DELIVERABLE": "What a session owes back follows from how it was packed: a worker session, any pack with a write forecast, owes one response tarball carrying the finished work; a planner session, a read-only pack, lands nothing and returns no response tarball, not even an empty one \u2014 it owes its answer in chat and, for each session it is asked to author, a crafter bundle beside its `bale open` line.",
  "DOC_ASK": "A turn that needs something from the packer, an environment fact or a decision, ends in the matching shape: a probe block, a light question block, or a clarification response; a question asked as prose is not a shape, because it gets lost. Every other turn is ordinary prose."
}""")

LINE1 = 'I\'m using "bale", a CLI that packaged the attached request tarball.'
GOAL = "checkpoint fixture: sid + goal ride the opener, verbatim"
GOAL_LINE = "Goal, verbatim from the request manifest: " + GOAL
BEGIN = "--8<-- session opener (copy everything between the scissor lines) --8<--"
END = "--8<-- end session opener --8<--"
RO_PAREN = ("(empty write forecast: an orchestration/discussion session"
            " \u2014 no changes land from it).")
PROSE = "CKPT-PROSE the packer typed this line"
failed = []


def collapse(text):
    return " ".join(text.split())


def verdict(ok, label, detail=""):
    print(("[PASS] " if ok else "[FAIL] ") + label)
    if not ok:
        failed.append(label)
        if detail:
            print("       " + detail)


class Fixture:
    """One fresh scratch repo, HOME and install-sandbox per scenario."""

    def __init__(self):
        self._t = tempfile.TemporaryDirectory(prefix="bale-ckpt-")
        self.tmp = Path(self._t.name)
        home = self.tmp / "home"
        home.mkdir()
        (home / ".gitconfig").write_text(
            "[user]\n\tname = Checkpoint Fixture\n"
            "\temail = ckpt@example.invalid\n"
            "[init]\n\tdefaultBranch = main\n", encoding="utf-8")
        self.env = {
            "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
            "HOME": str(home), "EDITOR": "/bin/true", "VISUAL": "/bin/true",
            "LANG": os.environ.get("LANG", "C.UTF-8"),
            "BALE_INSTALL": str(self.tmp / "bale-install-sandbox"),
        }
        self.repo = self.tmp / "project"
        self.repo.mkdir()
        (self.repo / "hello.txt").write_text("hello\n", encoding="utf-8")
        for cmd in (["git", "init", "-b", "main"], ["git", "add", "hello.txt"],
                    ["git", "commit", "-m", "init"]):
            r = subprocess.run(cmd, cwd=self.repo, env=self.env,
                               capture_output=True, text=True, timeout=120)
            if r.returncode != 0:
                raise RuntimeError(f"fixture setup failed: {cmd}: {r.stderr}")

    def close(self):
        self._t.cleanup()

    def pack(self, *extra):
        return subprocess.run(
            [sys.executable, str(ROOT / "bin" / "bale"), "pack", GOAL,
             "--slug", "ckpt", "--include", "hello.txt", *extra],
            cwd=self.repo, env=self.env, stdin=subprocess.DEVNULL,
            capture_output=True, text=True, timeout=120)

    def pack_pty(self, *extra):
        import pty, select
        master, slave = pty.openpty()
        proc = subprocess.Popen(
            [sys.executable, str(ROOT / "bin" / "bale"), "pack", GOAL,
             "--slug", "ckpt", "--include", "hello.txt", *extra],
            cwd=self.repo, env=self.env, stdin=slave, stdout=slave,
            stderr=slave, close_fds=True)
        os.close(slave)
        chunks, deadline = [], time.monotonic() + 90
        try:
            while time.monotonic() < deadline:
                readable, _, _ = select.select([master], [], [], 0.1)
                if master in readable:
                    try:
                        chunk = os.read(master, 4096)
                    except OSError:
                        break
                    if not chunk:
                        break
                    chunks.append(chunk)
                elif proc.poll() is not None:
                    break
            else:
                proc.kill()
                raise RuntimeError("pty-driven pack timed out")
            code = proc.wait(timeout=60)
        finally:
            os.close(master)
        return code, b"".join(chunks).decode(errors="replace")


def segment(text):
    a, b = text.find(BEGIN), text.find(END)
    if a < 0 or b < 0 or b < a:
        return None
    return text[a + len(BEGIN):b]


def report_row(text, key):
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith(key + ":"):
            return s.split(key + ":", 1)[1].strip()
    return None


def expected_block(sid, packed_at, *, read_only, readme):
    identity = ([f"This message opens read-only bale session {sid}", RO_PAREN]
                if read_only else [f"This message opens bale session {sid}."])
    return collapse(" ".join([
        LINE1, *identity, GOAL_LINE, S["OPENER_AUTHORITY"],
        S["OPENER_READING_WITH_README" if readme
          else "OPENER_READING_NO_README"],
        S["OPENER_TOOLS"], f"Packed at {packed_at} (UTC).",
        S["OPENER_CLOCK"], S["OPENER_ASK"],
        S["OPENER_DELIVERABLE_PLANNER" if read_only
          else "OPENER_DELIVERABLE_WORKER"],
    ]))


def manifest_probe(report, label, *, readme):
    tarball = report_row(report, "tarball")
    if not tarball or not Path(tarball).is_file():
        return verdict(False, label, "the report named no request tarball")
    with tarfile.open(tarball) as tf:
        names = tf.getnames()
        mname = next((n for n in names if n.count("/") == 1
                      and n.endswith("/manifest.json")), None)
        rname = next((n for n in names if n.count("/") == 1
                      and n.endswith("/README.md")), None)
        manifest = (json.loads(tf.extractfile(mname).read().decode("utf-8"))
                    if mname else None)
        shipped = tf.extractfile(rname).read() if rname else None
    if manifest is None or "readme" not in manifest:
        return verdict(False, label, "manifest.json missing, or it carries "
                       "no readme key")
    if readme:
        want = ({"path": "README.md",
                 "sha256": hashlib.sha256(shipped).hexdigest()}
                if shipped is not None else object())
        ok = (manifest["readme"] == want
              and report_row(report, "readme sha256") == want["sha256"])
    else:
        ok = manifest["readme"] is None and shipped is None
    verdict(ok, label)


def opener_probe(label, mlabel, *, read_only, readme):
    fx = Fixture()
    try:
        extra = ["--read-only"] if read_only else []
        if readme:
            brief = fx.tmp / "ckpt-brief.md"
            brief.write_text("# ckpt brief\n\nSome prose context.\n",
                             encoding="utf-8")
            extra += ["--readme-file", str(brief)]
        else:
            extra += ["--no-readme"]
        r = fx.pack(*extra)
        if r.returncode != 0:
            verdict(False, label, f"pack exited {r.returncode}")
            verdict(False, mlabel, "no pack to read a manifest from")
            return None, None
        seg = segment(r.stdout)
        sid = report_row(r.stdout, "session id")
        m = re.search(r"^Packed at (\S+) \(UTC\)\.$", seg or "", re.M)
        if seg is None or sid is None or m is None:
            verdict(False, label, "no opener block, sid row, or "
                    "own-line Packed-at line in the report")
            manifest_probe(r.stdout, mlabel, readme=readme)
            return None, None
        want = expected_block(sid, m.group(1), read_only=read_only,
                              readme=readme)
        verdict(collapse(seg) == want, label)
        manifest_probe(r.stdout, mlabel, readme=readme)
        return None, seg
    finally:
        fx.close()


def probes():
    _, seg = opener_probe(
        "opener, worker session, no README: the whole block reads as the "
        "brief's text, in the brief's order",
        "manifest, worker session, no README: the readme key is present "
        "and null", read_only=False, readme=False)
    lines = [ln.strip() for ln in (seg or "").splitlines()]
    verdict(seg is not None and GOAL_LINE in lines
            and S["OPENER_CLOCK"] in lines,
            "opener: the goal line and the clock sentence each ride one "
            "unwrapped line")
    opener_probe("opener, worker session, README shipped: the block names "
                 "README.md as the brief",
                 "manifest, worker session, README shipped: readme is the "
                 "path-and-sha256 object over the shipped bytes, equal to "
                 "the report's echo", read_only=False, readme=True)
    opener_probe("opener, planner (read-only) session, no README: the "
                 "block carries the planner deliverable",
                 "manifest, planner session, no README: the readme key is "
                 "present and null", read_only=True, readme=False)
    opener_probe("opener, planner (read-only) session, README shipped",
                 "manifest, planner session, README shipped: readme is the "
                 "path-and-sha256 object over the shipped bytes",
                 read_only=True, readme=True)

    label = ("editor scaffold: its instruction comment never reaches the "
             "shipped README; the packer's prose does")
    fx = Fixture()
    try:
        editor = fx.tmp / "ckpt-editor.sh"
        editor.write_text('#!/usr/bin/env bash\nprintf "%s\\n" "' + PROSE
                          + '" >> "$1"\n', encoding="utf-8")
        editor.chmod(0o755)
        fx.env["EDITOR"] = fx.env["VISUAL"] = str(editor)
        code, out = fx.pack_pty("--edit")
        tarball = report_row(out, "tarball")
        if code != 0 or not tarball or not Path(tarball).is_file():
            verdict(False, label, f"pack --edit exited {code} or named no "
                    "tarball")
        else:
            with tarfile.open(tarball) as tf:
                names = [n for n in tf.getnames()
                         if n.count("/") == 1 and n.endswith("/README.md")]
                body = (tf.extractfile(names[0]).read().decode("utf-8")
                        if names else None)
            verdict(body is not None and PROSE in body
                    and "README is OPTIONAL" not in body
                    and "<!--" not in body, label)
    finally:
        fx.close()

    claude = (ROOT / "docs" / "CLAUDE.md").read_text(encoding="utf-8")
    tarball_md = (ROOT / "docs" / "TARBALL.md").read_text(encoding="utf-8")
    a = claude.find("\n### Reading order\n")
    b = claude.find("\n### What this doc is\n")
    order = claude[a:b] if 0 <= a < b else ""
    row = next((ln for ln in claude.splitlines()
                if ln.startswith("| Every session |")), "")
    verdict("README.md" in order and "README.md" in row,
            "docs/CLAUDE.md: the META reading-order list and the INDEX "
            "every-session row both name README.md")
    c_claude, c_tarball = collapse(claude), collapse(tarball_md)
    verdict(S["DOC_DELIVERABLE"] in c_claude
            and S["DOC_DELIVERABLE"] in c_tarball,
            "docs: the what-a-session-owes-back sentence, VERBATIM, in "
            "CLAUDE.md and TARBALL.md")
    verdict(S["DOC_ASK"] in c_claude and S["DOC_ASK"] in c_tarball
            and "Every turn Claude ends in tarball mode takes one"
            not in c_claude
            and "Every turn the worker ends in tarball mode takes one"
            not in c_tarball,
            "docs: the re-scoped ask sentence, VERBATIM, in CLAUDE.md and "
            "TARBALL.md, with the every-turn sentences retired")
    schema = json.loads((ROOT / "schemas" / "request-manifest.schema.json")
                        .read_text(encoding="utf-8"))
    verdict("readme" in schema.get("properties", {})
            and "readme" not in schema.get("required", [])
            and schema.get("additionalProperties") is False,
            "schema: request-manifest admits a top-level readme key, does "
            "not require it, and stays a closed object")
    s32a = tarball_md.find("\n### 3.2 manifest.json\n")
    s32b = tarball_md.find("\n### 3.3 ")
    verdict(0 <= s32a < s32b and "`readme`" in tarball_md[s32a:s32b],
            "docs/TARBALL.md: section 3.2 documents the readme key")
    verdict("Most sessions skip the README" not in c_tarball,
            "docs/TARBALL.md: no longer says most sessions skip the README")

    for suite in ("test_pack_opener", "test_doc_crossrefs",
                  "test_global_doc_selfcontainment"):
        r = subprocess.run([sys.executable, str(ROOT / "tests" / f"{suite}.py")],
                           cwd=ROOT, capture_output=True, text=True,
                           timeout=900)
        verdict(r.returncode == 0, f"suite passes in staging: tests/{suite}.py")


try:
    probes()
except Exception:
    traceback.print_exc()
    print("checkpoint error: the checkpoint itself errored")
    sys.exit(2)
print(f"checkpoint: {len(failed)} probe(s) failed")
sys.exit(1 if failed else 0)
CKPT_PY
