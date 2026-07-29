#!/usr/bin/env python3
"""craft_response.py — mechanical scaffolder for a bale response directory.

A WORKER runs this against its own response-NNN/ directory while
building a normal response, without bale installed. It mechanizes the
computed half of TARBALL.md §5.2/§5.2.1 and the §5.1.1 scaffold:

- walks `files/`, computes every `size_bytes` and `sha256`, and emits
  the `changes[]` skeleton in paste-ready form — mirror prefix
  stripped, computed values filled, `action` and `reason` left empty
  for the worker (reason is judgment; the tool never generates it);
- emits `deleted`-entry stubs on request (`--deleted PATH`); the two
  hand-written literals of the old §5.2.1 recipe — `size_bytes: 0`,
  `sha256: null` — are this tool's to write now;
- emits the manifest skeleton for a normal response (`session_id` /
  `responds_to` from `--sid`, `response_kind: "normal"`, the empty
  structured fields present) and the `apply.sh` scaffold: the §5.1.1
  no-op when nothing needs it, otherwise `rm -f` lines for deletions
  and per-path `chmod +x` lines for files the worker names with
  `--executable`.

THE CRAFTER NEVER VALIDATES ITS OWN OUTPUT. `tools/response_lint.py`
is the separately authored, separately maintained judge; this module
does not import from it, share code with it, or get imported by it.
The workflow is: craft, fill the judgment fields, then the lint
judges. An unfilled skeleton is deliberately lint-invalid (empty
`action`, `reason`, `summary`), so it cannot pass review by accident.

Usage:
    craft_response.py <response-dir> --sid SESSION_ID [options]

Modes (mutually exclusive; default prints the manifest skeleton):
    (default)       print the manifest-skeleton JSON to stdout
    --changes-only  print only the changes[] array (paste-ready)
    --apply-only    print only the apply.sh scaffold
    --write         write manifest.json and apply.sh into the response
                    dir (refuses to overwrite; --force to allow)

Options:
    --deleted PATH      add a deleted-entry stub (repeatable)
    --executable PATH   add a chmod +x line for a files/ path (repeatable)
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

APPLY_NOOP = """#!/usr/bin/env bash
# No additional operations for this session.
exit 0
"""

APPLY_HEADER = """#!/usr/bin/env bash
set -euo pipefail
"""


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


def build_manifest(sid: str, changes: list[dict]) -> dict:
    """The normal-response manifest skeleton per TARBALL.md §5.2: computed
    and mechanical fields filled, judgment fields present but empty."""
    return {
        "session_id": sid,
        "responds_to": sid,
        "corrects": None,
        "response_kind": "normal",
        "summary": "",              # worker fills
        "changes": changes,
        "deferred": [],
        "validation_will_run": [],  # worker fills
        "claims": {},               # worker fills
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
        description=("Scaffold a bale normal-response manifest and apply.sh "
                     "from the files/ mirror. The crafter never validates "
                     "its own output; run tools/response_lint.py on the "
                     "finished response."),
    )
    ap.add_argument("response_dir", help="the response-NNN/ directory")
    ap.add_argument("--sid", default=None,
                    help="session id (fills session_id and responds_to)")
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

    rdir = Path(args.response_dir)
    if not rdir.is_dir():
        return die(f"response dir not found or not a directory: {rdir}")
    if args.force and not args.write:
        return die("--force only means something with --write")

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
    apply_sh = build_apply_sh(args.deleted, args.executable)

    n_mirror = len(mirror)
    log(f"files/ mirror: {n_mirror} file(s); deleted stubs: "
        f"{len(args.deleted)}; chmod lines: {len(args.executable)}")

    if args.changes_only:
        print(json.dumps(changes, indent=2))
        log("changes[] skeleton emitted — fill action and reason per entry, "
            "then run tools/response_lint.py on the finished response")
        return EXIT_OK

    if args.apply_only:
        sys.stdout.write(apply_sh)
        log("apply.sh scaffold emitted")
        return EXIT_OK

    manifest = build_manifest(sid, changes)

    if args.write:
        wrote: list[Path] = []
        for name, body in (("manifest.json",
                            json.dumps(manifest, indent=2) + "\n"),
                           ("apply.sh", apply_sh)):
            dst = rdir / name
            if dst.exists() and not args.force:
                return die(f"{dst} exists — re-run with --force to "
                           "overwrite")
            dst.write_text(body, encoding="utf-8")
            wrote.append(dst)
        for dst in wrote:
            print(dst)
        log("wrote manifest.json and apply.sh — fill summary, action, "
            "reason, validation_will_run, and claims, then run "
            "tools/response_lint.py")
        return EXIT_OK

    print(json.dumps(manifest, indent=2))
    log("manifest skeleton emitted (apply.sh scaffold via --apply-only or "
        "--write) — fill the judgment fields, then run "
        "tools/response_lint.py")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
