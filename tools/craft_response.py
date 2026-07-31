#!/usr/bin/env python3
"""craft_response.py — mechanical scaffolder for a bale response directory.

A WORKER runs this against its own response-NNN/ directory while
building a response, without bale installed. It mechanizes the
computed half of TARBALL.md §5.2/§5.2.1 and the §5.1.1 scaffold, and
scaffolds all three response kinds (`--kind`, default `normal`):

- (normal) walks `files/`, computes every `size_bytes` and `sha256`,
  and emits the `changes[]` skeleton in paste-ready form — mirror
  prefix stripped, computed values filled, `action` and `reason` left
  empty for the worker (reason is judgment; the tool never generates
  it);
- (normal) emits `deleted`-entry stubs on request (`--deleted PATH`);
  the two hand-written literals of the old §5.2.1 recipe —
  `size_bytes: 0`, `sha256: null` — are this tool's to write now;
- (normal) emits the manifest skeleton (`session_id` / `responds_to`
  from `--sid`, `response_kind: "normal"`, the empty structured
  fields present) and the `apply.sh` scaffold: the §5.1.1 no-op when
  nothing needs it, otherwise `rm -f` lines for deletions and
  per-path `chmod +x` lines for files the worker names with
  `--executable`;
- (bailout, §5.6) emits the manifest skeleton with the §5.6.2 empty
  change surfaces, and under `--write` the full artifact set: the
  no-op `apply.sh` and `validation.sh`, the `handoff.md` scaffold
  carrying §5.7's section headers and nothing else (handoff CONTENT
  is judgment and stays the worker's), and the `diagnostics.json`
  skeleton carrying the schema's required keys — `session_id` filled
  (mechanical), everything else empty;
- (clarification, §5.9) emits the manifest skeleton with the same
  empty change surfaces plus `questions[]` seeded with four-field
  entry stubs (`--questions N`, default 1), and under `--write` the
  no-op `apply.sh` and `validation.sh`;
- (probe, §4.2) `--probe SLUG` emits the canonical paste-back probe
  skeleton to stdout — the shape (shebang, three-line purpose header
  with the read-only declaration verbatim, the probe() wrapper, the
  PROBE BEGIN/END sentinels carrying the slug, and the
  capture-then-count integrity trailer) final; the what/why header
  lines and the one example labeled section (its cap-and-truncation
  pattern shown) are loud TODO placeholders, in comments and strings
  only so the emission stays valid bash. A probe is chat-ephemeral
  (§4.2): no response directory is read, required, or accepted, and
  no lint runs on it — the architect audits the pasted block by eye,
  so the unfilled placeholders are the unfilled-cannot-pass analog:
  visibly not ready to paste.

For the normal kind, `validation.sh` remains un-emitted on purpose:
there it is the worker's hypothesis test (TARBALL.md §7) — judgment,
never scaffolded. The no-op validation.sh exists only for the two
kinds whose contract fixes it as a no-op.

THE CRAFTER NEVER VALIDATES ITS OWN OUTPUT. `tools/response_lint.py`
is the separately authored, separately maintained judge; this module
does not import from it, share code with it, or get imported by it.
The workflow is: craft, fill the judgment fields, then the lint
judges. An unfilled skeleton is deliberately lint-invalid (empty
`action`, `reason`, `summary`), so it cannot pass review by accident.

Usage:
    craft_response.py <response-dir> --sid SESSION_ID [options]
    craft_response.py --probe SLUG

Modes (mutually exclusive; default prints the manifest skeleton):
    (default)       print the manifest-skeleton JSON to stdout
    --changes-only  print only the changes[] array (normal kind only)
    --apply-only    print only the apply.sh scaffold
    --write         write the kind's artifact set into the response dir
                    (normal: manifest.json, apply.sh; clarification:
                    + validation.sh; bailout: + validation.sh,
                    handoff.md, diagnostics.json). Refuses to
                    overwrite; --force to allow.
    --probe SLUG    print the TARBALL.md §4.2 probe skeleton to stdout.
                    Takes no response dir and combines with none of the
                    response-directory flags — a probe is a chat
                    paste-back, not a response artifact.

Options:
    --kind KIND         normal (default) | bailout | clarification
    --questions N       clarification only: number of question-entry
                        stubs to seed (default 1)
    --deleted PATH      normal only: add a deleted-entry stub (repeatable)
    --executable PATH   normal only: add a chmod +x line for a files/
                        path (repeatable)
    --sid SESSION_ID    session id for session_id and responds_to;
                        required except under --changes-only/--apply-only

Exit codes:
    0  success
    2  the tool errored (bad usage, unreadable dir, incoherent flags)
    (1 is reserved; the crafter has no findings — findings are the
    lint's business.)

Stdlib only. Python 3.10+. No network. No bale imports. No
response_lint imports.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path, PurePosixPath

EXIT_OK = 0
EXIT_ERROR = 2

KINDS = ("normal", "bailout", "clarification")

APPLY_NOOP = """#!/usr/bin/env bash
# No additional operations for this session.
exit 0
"""

APPLY_HEADER = """#!/usr/bin/env bash
set -euo pipefail
"""

# TARBALL.md fixes validation.sh as a no-op on the two non-normal kinds
# (§5.6.1 for bailouts, §5.9.2 for clarifications): nothing changed, so
# there is nothing to test. On the normal kind validation.sh is the
# worker's hypothesis test (§7) and this tool never emits it.
VALIDATION_NOOP_BY_KIND = {
    "bailout": """#!/usr/bin/env bash
# No checks to run — a bailout response carries no change set
# (TARBALL.md 5.6.2).
exit 0
""",
    "clarification": """#!/usr/bin/env bash
# No checks to run — a clarification response carries no change set
# (TARBALL.md 5.9.2).
exit 0
""",
}

# TARBALL.md §5.7's required sections, in the required order, and
# nothing else: the scaffold is the section list; the content under
# each header is judgment and stays the worker's.
HANDOFF_SCAFFOLD = """# Handoff

## Original goal

## What I loaded

## What I explored

## What I learned

## Reading plan for the next session

## Salvageable work
"""

# The four-field questions[] entry stub of TARBALL.md §5.9.2 /
# response-manifest.schema.json. Every value is an empty string on
# purpose: an unfilled skeleton is deliberately lint-invalid.
QUESTION_STUB_KEYS = ("question", "context", "default_assumption",
                     "why_blocked")

# The TARBALL.md §4.2 canonical probe skeleton. Real and final: the
# shebang, the three-line purpose-header shape (its read-only line
# verbatim from §4.2), the probe() wrapper, the sentinels carrying the
# slug, and the capture-then-count integrity trailer. Loud TODO
# placeholders (comments and strings only, so `bash -n` stays clean):
# the what/why header lines and one example labeled section with the
# cap-and-truncation-marker pattern shown. Sections are judgment; the
# shape is not. No judge runs on a probe — it is a chat paste-back the
# architect audits by eye (§4.2), so unfilled placeholders are the
# unfilled-cannot-pass analog: visibly not ready to paste.
PROBE_SCAFFOLD = """\
#!/usr/bin/env bash
# PROBE {slug}: TODO(worker) — what this asks, in one line.
# Why: TODO(worker) — the gap this fills, in one line.
# Read-only: writes nothing anywhere; stdout is the only output.

probe() {{
  # TODO(worker): replace this placeholder with the real sections —
  # one labeled section per question, every command's output capped,
  # an explicit truncation marker when the cap bites (TARBALL.md 4.2).
  # The cap-and-truncation pattern, worked for one command:
  #   git status --porcelain=v1 2>&1 | head -n 40
  #   n=$(git status --porcelain=v1 2>/dev/null | wc -l)
  #   [ "$n" -gt 40 ] && echo "[truncated: $n lines total, showing 40]"
  echo "--- section: TODO-example ---"
  echo "TODO(worker): unfilled probe placeholder — not ready to paste"
}}

out="$(probe 2>&1)"
echo "=== PROBE BEGIN {slug} ==="
printf '%s\\n' "$out"
printf -- '--- integrity: %s lines ---\\n' "$(printf '%s\\n' "$out" | wc -l | tr -d ' ')"
echo "=== PROBE END {slug} ==="
"""


def slug_problem(slug: str) -> str | None:
    """Return a human-readable objection to a probe slug, or None.

    Session slugs are short and kebab-cased (TARBALL.md §1). The slug
    lands inside bash comments and double-quoted strings, so anything
    outside kebab-case is refused rather than escaped — hygiene, not
    quoting cleverness.
    """
    if not slug or not slug.strip():
        return "empty slug"
    kebab = set("abcdefghijklmnopqrstuvwxyz0123456789-")
    ok = all(c in kebab for c in slug) \
        and not slug.startswith("-") and not slug.endswith("-") \
        and "--" not in slug
    if not ok:
        return (f"slug {slug!r} is not kebab-case — lowercase letters, "
                "digits, and single hyphens only (TARBALL.md 1)")
    return None


def log(msg: str) -> None:
    """All operational output goes to stderr; stdout carries the payload."""
    print(f"[craft] {msg}", file=sys.stderr)


def die(msg: str) -> "int":
    log(f"error: {msg}")
    return EXIT_ERROR


# ---------------------------------------------------------------------------
# Path handling
# ---------------------------------------------------------------------------

def rel_path_problem(path_str: str) -> str | None:
    """Return a human-readable objection to a worker-supplied repo-relative
    path, or None when the path is usable. Catches the typo shapes that
    would otherwise scaffold a wrong (or dangerous) apply.sh line."""
    if not path_str or not path_str.strip():
        return "empty path"
    if path_str != path_str.strip():
        return f"leading/trailing whitespace in {path_str!r}"
    if "\\" in path_str:
        return f"backslash in {path_str!r} — manifest paths are POSIX"
    if path_str.startswith("/"):
        return f"absolute path {path_str!r} — paths are repo-relative"
    if path_str.endswith("/"):
        return f"trailing slash in {path_str!r} — entries name files"
    parts = PurePosixPath(path_str).parts
    if "." in parts or ".." in parts:
        return f"'.' or '..' segment in {path_str!r}"
    if parts and parts[0] == "files":
        return (
            f"{path_str!r} starts with 'files/' — pass the repo-relative "
            "path; the mirror prefix is the tool's to strip"
        )
    return None


def walk_mirror(files_root: Path) -> list[str]:
    """Enumerate the files/ mirror as sorted repo-relative POSIX paths.

    Directories are not entries (the mirror is enumerated by its files,
    TARBALL.md §5.1); a broken symlink is an error, never a silent skip.
    """
    found: list[str] = []
    for p in sorted(files_root.rglob("*")):
        if p.is_dir():
            continue
        if p.is_symlink() and not p.exists():
            raise ValueError(
                f"broken symlink under files/: {p.relative_to(files_root).as_posix()}"
            )
        if p.is_file():
            found.append(p.relative_to(files_root).as_posix())
            continue
        raise ValueError(
            f"unsupported entry under files/ (not a regular file): "
            f"{p.relative_to(files_root).as_posix()}"
        )
    return sorted(found)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Skeleton construction
# ---------------------------------------------------------------------------

def build_changes(files_root: Path | None, deleted: list[str]) -> list[dict]:
    """The changes[] skeleton: computed values filled, judgment left empty.

    Mirror entries first (sorted), then deleted stubs (sorted) — a stable
    order so re-runs diff cleanly.
    """
    entries: list[dict] = []
    mirror_paths: list[str] = []
    if files_root is not None and files_root.is_dir():
        mirror_paths = walk_mirror(files_root)
    for rel in mirror_paths:
        f = files_root / rel  # type: ignore[operator]
        entries.append({
            "path": rel,
            "action": "",      # worker fills: created | modified
            "reason": "",      # worker fills: judgment, never generated
            "size_bytes": f.stat().st_size,
            "sha256": sha256_of(f),
        })
    for rel in sorted(deleted):
        entries.append({
            "path": rel,
            "action": "deleted",
            "reason": "",      # worker fills: judgment, never generated
            "size_bytes": 0,
            "sha256": None,
        })
    return entries


def build_manifest(sid: str, kind: str, changes: list[dict],
                   n_questions: int = 0) -> dict:
    """The manifest skeleton per TARBALL.md §5.2 (normal), §5.6.2
    (bailout), or §5.9.2 (clarification): computed and mechanical fields
    filled, judgment fields present but empty.

    The two non-normal kinds carry the empty change surfaces their
    sections require; a clarification additionally seeds `questions[]`
    with all-empty four-field entry stubs (unfilled-cannot-pass: the
    lint rejects the empty strings).
    """
    manifest = {
        "session_id": sid,
        "responds_to": sid,
        "corrects": None,
        "response_kind": kind,
        "summary": "",              # worker fills
        "changes": changes if kind == "normal" else [],
        "deferred": [],
        "validation_will_run": [],  # worker fills (normal kind)
        "claims": {},               # worker fills (normal kind)
    }
    if kind == "clarification":
        manifest["questions"] = [
            {k: "" for k in QUESTION_STUB_KEYS}  # worker fills all four
            for _ in range(n_questions)
        ]
    return manifest


def build_diagnostics(sid: str) -> dict:
    """The diagnostics.json skeleton per TARBALL.md §5.8 /
    schemas/diagnostics.schema.json: exactly the schema's required keys.
    `session_id` is mechanical (the tool has it from --sid); every other
    value is empty and the worker's — an unfilled skeleton is
    deliberately schema-invalid (`bail_trigger` off-enum,
    `bail_narrative` empty), so it cannot pass the lint by accident.
    """
    return {
        "session_id": sid,
        "bail_trigger": "",         # worker fills: an enum value (§5.8)
        "bail_narrative": "",       # worker fills: judgment
        "context_loaded": [],       # worker fills
        "exploration_paths": [],    # worker fills
        "tool_calls_summary": {},   # worker fills
        "what_would_save_next_time": [],  # worker fills
    }


def build_apply_sh(deleted: list[str], executables: list[str]) -> str:
    """The apply.sh scaffold per TARBALL.md §5.1.1: the verbatim no-op when
    nothing needs the script, otherwise rm lines then chmod lines (chmod
    runs after the overlay applies, so it comes last)."""
    if not deleted and not executables:
        return APPLY_NOOP
    lines = [APPLY_HEADER]
    for rel in sorted(deleted):
        lines.append(f"# Remove {rel} — TODO(worker): one-line reason.")
        lines.append(f"rm -f {shell_quote(rel)}")
        lines.append("")
    if executables:
        lines.append(
            "# Restore executable bits the files/ overlay strips "
            "(TARBALL.md 5.1.1)."
        )
        for rel in sorted(executables):
            lines.append(f"chmod +x {shell_quote(rel)}")
        lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


def shell_quote(path_str: str) -> str:
    """Quote a repo-relative path for the apply.sh scaffold. Plain paths
    stay bare (readable); anything shell-significant gets single-quoted."""
    safe = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
               "0123456789._-/+")
    if path_str and all(c in safe for c in path_str):
        return path_str
    return "'" + path_str.replace("'", "'\\''") + "'"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        prog="craft_response.py",
        description=("Scaffold a bale response (--kind normal | bailout | "
                     "clarification): the manifest skeleton, apply.sh, and "
                     "the non-normal kinds' companion artifacts. The "
                     "crafter never validates its own output; run "
                     "tools/response_lint.py on the finished response."),
    )
    ap.add_argument("response_dir", nargs="?", default=None,
                    help="the response-NNN/ directory (required except "
                         "under --probe, which reads no response dir)")
    ap.add_argument("--probe", default=None, metavar="SLUG",
                    help="emit the TARBALL.md 4.2 probe skeleton for SLUG "
                         "to stdout; mutually exclusive with the "
                         "response-directory modes and flags")
    ap.add_argument("--sid", default=None,
                    help="session id (fills session_id and responds_to)")
    ap.add_argument("--kind", choices=KINDS, default=None,
                    help="response kind to scaffold (default: normal)")
    ap.add_argument("--questions", type=int, default=None, metavar="N",
                    help="with --kind clarification: number of "
                         "question-entry stubs to seed (default 1)")
    ap.add_argument("--deleted", action="append", default=[], metavar="PATH",
                    help="emit a deleted-entry stub for PATH (repeatable)")
    ap.add_argument("--executable", action="append", default=[],
                    metavar="PATH",
                    help="emit a chmod +x line in apply.sh for PATH "
                         "(repeatable; PATH must be under files/)")
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--changes-only", action="store_true",
                      help="print only the changes[] array")
    mode.add_argument("--apply-only", action="store_true",
                      help="print only the apply.sh scaffold")
    mode.add_argument("--write", action="store_true",
                      help="write manifest.json and apply.sh into the "
                           "response dir")
    ap.add_argument("--force", action="store_true",
                    help="with --write: overwrite existing manifest.json / "
                         "apply.sh")
    return ap.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    # Probe mode. A probe is a chat paste-back, not a response-directory
    # artifact (TARBALL.md §4.2): it reads no response dir and combines
    # with none of the response-directory modes or flags, so every such
    # combination is a flag error, not a silent ignore.
    if args.probe is not None:
        supplied = [flag for flag, given in (
            ("--kind", args.kind is not None),
            ("--changes-only", args.changes_only),
            ("--apply-only", args.apply_only),
            ("--write", args.write),
            ("--sid", args.sid is not None),
            ("--questions", args.questions is not None),
            ("--deleted", bool(args.deleted)),
            ("--executable", bool(args.executable)),
            ("--force", args.force),
        ) if given]
        if supplied:
            return die(f"--probe is mutually exclusive with "
                       f"{', '.join(supplied)} — a probe is a chat "
                       "paste-back, not a response-directory artifact "
                       "(TARBALL.md 4.2)")
        if args.response_dir is not None:
            return die(f"--probe takes no response dir (got "
                       f"{args.response_dir!r}) — the skeleton goes to "
                       "stdout and a probe produces no artifact directory "
                       "(TARBALL.md 4.2); drop the positional argument")
        problem = slug_problem(args.probe)
        if problem:
            return die(f"--probe: {problem}")
        sys.stdout.write(PROBE_SCAFFOLD.format(slug=args.probe))
        log("probe skeleton emitted — fill the TODO placeholders (what, "
            "why, real sections with caps), then paste into chat; no lint "
            "runs on a probe — the architect audits it by eye "
            "(TARBALL.md 4.2)")
        return EXIT_OK

    if args.response_dir is None:
        return die("response dir is required (only --probe runs without "
                   "one)")
    rdir = Path(args.response_dir)
    if not rdir.is_dir():
        return die(f"response dir not found or not a directory: {rdir}")
    if args.force and not args.write:
        return die("--force only means something with --write")

    kind = args.kind if args.kind is not None else "normal"

    # Kind/flag coherence. This is argument hygiene, not response
    # validation (the judge stays tools/response_lint.py): each of these
    # combinations would scaffold an artifact the contract forbids, so
    # the tool refuses to scaffold it rather than judging it later.
    if kind != "normal":
        if args.deleted or args.executable:
            return die(f"--deleted/--executable are meaningless with "
                       f"--kind {kind} — a {kind} response has empty "
                       "change surfaces (TARBALL.md 5.6.2 / 5.9.2)")
        if args.changes_only:
            return die(f"--changes-only is meaningless with --kind {kind} "
                       f"— a {kind} response has an empty changes[] "
                       "(TARBALL.md 5.6.2 / 5.9.2)")
    if args.questions is not None:
        if kind != "clarification":
            return die("--questions only means something with "
                       "--kind clarification")
        if args.questions < 1:
            return die("--questions must be at least 1 — questions[] is "
                       "required non-empty on a clarification "
                       "(TARBALL.md 5.9.2)")
    n_questions = args.questions if args.questions is not None else 1

    needs_sid = not (args.changes_only or args.apply_only)
    sid = (args.sid or "").strip()
    if needs_sid and not sid:
        return die("--sid is required when emitting a manifest "
                   "(only --changes-only / --apply-only run without it)")

    # Worker-supplied path sanity. This is argument hygiene, not response
    # validation: a typo'd flag scaffolding a wrong rm/chmod line is the
    # failure it prevents. Judging the finished response stays the lint's.
    for label, values in (("--deleted", args.deleted),
                          ("--executable", args.executable)):
        seen: set[str] = set()
        for v in values:
            problem = rel_path_problem(v)
            if problem:
                return die(f"{label}: {problem}")
            if v in seen:
                return die(f"{label}: duplicate path {v!r}")
            seen.add(v)

    files_root = rdir / "files"
    try:
        mirror = set(walk_mirror(files_root)) if files_root.is_dir() else set()
    except ValueError as exc:
        return die(str(exc))

    if kind != "normal" and mirror:
        return die(f"files/ holds {len(mirror)} file(s) but a {kind} "
                   "response ships no file changes (TARBALL.md 5.6.1 / "
                   "5.9.2) — clear files/ or craft in a clean response dir")

    for v in args.deleted:
        if v in mirror:
            return die(f"--deleted {v!r} also exists under files/ — a "
                       "deleted entry carries no mirror file (TARBALL.md "
                       "5.2); remove one or the other")
    for v in args.executable:
        if v not in mirror:
            return die(f"--executable {v!r} has no file under files/ — a "
                       "chmod line for an unshipped path restores nothing")

    try:
        changes = build_changes(files_root if files_root.is_dir() else None,
                                args.deleted)
    except ValueError as exc:
        return die(str(exc))
    apply_sh = (APPLY_NOOP if kind != "normal"
                else build_apply_sh(args.deleted, args.executable))

    if kind == "normal":
        log(f"files/ mirror: {len(mirror)} file(s); deleted stubs: "
            f"{len(args.deleted)}; chmod lines: {len(args.executable)}")
    else:
        log(f"scaffolding a {kind} response — empty change surfaces, "
            "no-op apply.sh and validation.sh")

    if args.changes_only:
        print(json.dumps(changes, indent=2))
        log("changes[] skeleton emitted — fill action and reason per entry, "
            "then run tools/response_lint.py on the finished response")
        return EXIT_OK

    if args.apply_only:
        sys.stdout.write(apply_sh)
        log("apply.sh scaffold emitted")
        return EXIT_OK

    manifest = build_manifest(sid, kind, changes, n_questions)

    # The kind's artifact set for --write. The normal kind never gets a
    # validation.sh from this tool (worker's hypothesis test, §7); the
    # two non-normal kinds get the contract-fixed no-op, and a bailout
    # additionally gets its two required companions (§5.6.1).
    emit: list[tuple[str, str]] = [
        ("manifest.json", json.dumps(manifest, indent=2) + "\n"),
        ("apply.sh", apply_sh),
    ]
    if kind in VALIDATION_NOOP_BY_KIND:
        emit.append(("validation.sh", VALIDATION_NOOP_BY_KIND[kind]))
    if kind == "bailout":
        emit.append(("handoff.md", HANDOFF_SCAFFOLD))
        emit.append(("diagnostics.json",
                     json.dumps(build_diagnostics(sid), indent=2) + "\n"))

    if args.write:
        for name, _ in emit:
            dst = rdir / name
            if dst.exists() and not args.force:
                return die(f"{dst} exists — re-run with --force to "
                           "overwrite")
        wrote: list[Path] = []
        for name, body in emit:
            dst = rdir / name
            dst.write_text(body, encoding="utf-8")
            wrote.append(dst)
        for dst in wrote:
            print(dst)
        names = ", ".join(name for name, _ in emit)
        fill = {
            "normal": "fill summary, action, reason, validation_will_run, "
                      "and claims",
            "bailout": "fill summary, the handoff.md sections, and the "
                       "diagnostics.json fields (bail_trigger, "
                       "bail_narrative, ...)",
            "clarification": "fill summary and all four fields of every "
                             "questions[] entry",
        }[kind]
        log(f"wrote {names} — {fill}, then run tools/response_lint.py")
        return EXIT_OK

    print(json.dumps(manifest, indent=2))
    if kind == "normal":
        log("manifest skeleton emitted (apply.sh scaffold via --apply-only "
            "or --write) — fill the judgment fields, then run "
            "tools/response_lint.py")
    else:
        rest = ", ".join(name for name, _ in emit[1:])
        log(f"manifest skeleton emitted — the {kind} kind's remaining "
            f"artifacts ({rest}) are written by --write; fill the "
            "judgment fields, then run tools/response_lint.py")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
