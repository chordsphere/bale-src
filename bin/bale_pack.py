"""bale_pack — the `bale pack` path (request-tarball construction).

The sixth sibling module after `bale_config` (v0.0.4), `bale_validate`
(v0.1.2), `bale_staging` (v0.1.3), `bale_rollback` (v0.2.0), and
`bale_report` (v0.2.6). Extracted from `bin/bale`'s sections 10–15 in
v0.3.12, behavior-preserving: file enumeration and filtering, scope
projection + threshold caps (BALE.md §7.4), manifest and tarball
construction, the §7.3 wizard, and `cmd_pack` itself (which hosts the
git-init walkthrough per BALE.md §10). `bin/bale` keeps the CLI entry
point and dispatch, plus the helpers the pack and apply paths share —
the `.baleignore` matcher cluster (`BaleignoreMatcher`,
`load_baleignore`, `is_baleignore_match`), `is_valid_slug`, and the
logging / git / registry / editor machinery.

Public surface consumed by `bin/bale`: `cmd_pack` (CLI dispatch);
`gather_files_for_pack`, `build_request_manifest`,
`build_provenance_block`, `build_request_tarball`,
`persist_pack_session` (the second request-building path, `bale
handoff`, plus `bale retry`'s record re-persist); and `format_bytes` +
the `PACK_MAX_*` cap constants (the `--max-*` flag help text). Shared
`bin/bale` helpers are imported lazily from `__main__` inside the
functions that use them, the same idiom every other sibling uses.
Sibling-owned entry points (`bale_config`, `bale_report`'s pack-report
renderers and json-mode state, `bale_validate`'s request validator) are
imported lazily from their owning modules instead — bin/bale has already
loaded them, so the imports resolve from sys.modules, and pack does not
depend on `__main__` re-exporting names bin/bale itself never calls.
This module imports nothing from
the apply path — the dependency direction is `bin/bale` → `bale_pack`,
never the reverse.

Sections:
  1. Pack constants                                      (~line   55)
  2. File enumeration and filtering                      (~line  105)
  3. Scope projection + threshold caps (BALE.md §7.4)    (~line  245)
  4. Manifest and tarball construction                   (~line  525)
  5. Wizard (BALE.md §7.3)                               (~line  755)
  6. Pack: git-init walkthrough + cmd_pack               (~line 1050)
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    # Annotation-only: the matcher class lives in bin/bale (shared with
    # the apply side); runtime access goes through the lazy __main__
    # imports inside the functions that construct one.
    from __main__ import BaleignoreMatcher


# ---------------------------------------------------------------------------
# 1. Pack constants
# ---------------------------------------------------------------------------

# Baked-in exclusions for pack. From BALE.md section 6.4.
# Directory names (matched by basename at any depth).
BAKED_IN_EXCLUDE_DIRS = {
    # Bale and git internals
    ".git", ".bale",
    # Common big-build dirs
    "node_modules", "__pycache__", ".venv", "target", "dist",
    "build", ".next", ".nuxt", "out", ".cache",
}

# Filename glob patterns (matched by basename).
SECRET_PATTERNS = (
    ".env", ".env.*",
    "*.pem", "*.key",
    "*_rsa", "*_dsa",
    "*.p12", "*.pfx",
    "id_rsa", "id_dsa",
    ".pypirc",
)

# Full relative paths from repo root that are always excluded.
SECRET_PATH_EXCLUDES = (
    ".aws/credentials",
)

# Pack threshold caps. From BALE.md section 7.4.
# Soft caps drive the interactive [y]/[e]/[n] prompt; in piped mode (stdin
# not a TTY) a soft breach refuses instead — no prompt is possible and a
# warning nobody reads is not a check (v0.2.4; --force proceeds
# deliberately). Hard caps drive refusal in both modes. Depth is hard-only — there's
# no realistic case where "uh, 19 directories deep is fine but 20 is iffy"
# is the right product gesture; deep paths are either fine or pathological.
# Sizes are 1024-based (a "GB" here means 2^30 bytes), matching how every
# OS-shaped tool quotes them.
PACK_MAX_FILES_SOFT = 10_000
PACK_MAX_FILES_HARD = 100_000
PACK_MAX_SIZE_SOFT = 100 * 1024 * 1024            # 100 MB
PACK_MAX_SIZE_HARD = 1 * 1024 * 1024 * 1024       # 1 GB
PACK_MAX_DEPTH = 20

# How many entries to show in the "largest directories" report on a soft
# breach. Keep this small — the prompt is meant to point at obvious
# offenders, not survey the whole tree.
PACK_LARGEST_DIRS_TOPN = 5

# The worker-side crafter's interim CRAFT_TOOL constant (v1, session 007)
# was deleted in v0.3.19: bin/bale's INJECTED_TOOLS names the crafter
# directly, and that tuple is the single source for the injected-tool
# list — see its comment for the consolidation history.


# ---------------------------------------------------------------------------
# 2. File enumeration and filtering
# ---------------------------------------------------------------------------

def list_git_files(repo: Path) -> list[str]:
    """All tracked + untracked-not-ignored files in the repo, repo-relative.

    Uses `git ls-files --cached --others --exclude-standard`, which honors
    .gitignore at every level plus .git/info/exclude. This is bale's default
    way of respecting .gitignore (BALE.md section 6.4). There is no
    `--no-gitignore` escape hatch yet; that's a later enhancement.
    """
    from __main__ import run  # lazy — see module docstring
    r = run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=repo, check=True,
    )
    return [line for line in r.stdout.splitlines() if line]


def is_under_excluded_dir(rel: str) -> bool:
    """Any path component matches a baked-in excluded directory name."""
    for part in Path(rel).parts:
        if part in BAKED_IN_EXCLUDE_DIRS:
            return True
    return False


def matches_secret_pattern(rel: str) -> bool:
    """Basename matches a secret glob, or full path matches a secret-path entry."""
    base = Path(rel).name
    for pat in SECRET_PATTERNS:
        if fnmatch.fnmatchcase(base, pat):
            return True
    for full in SECRET_PATH_EXCLUDES:
        if rel == full or rel.endswith("/" + full):
            return True
    return False


def npmrc_has_authtoken(file_path: Path) -> bool:
    """`.npmrc` is excluded only when it contains _authToken (BALE.md 6.4)."""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return "_authToken" in content


def is_secret_excluded(rel: str, repo: Path) -> bool:
    if matches_secret_pattern(rel):
        return True
    if Path(rel).name == ".npmrc":
        return npmrc_has_authtoken(repo / rel)
    return False


def is_under_include(rel: str, includes: list[str]) -> bool:
    """No includes = include everything. Otherwise must be under one of them."""
    if not includes:
        return True
    rel_p = Path(rel)
    for inc in includes:
        inc_p = Path(inc)
        if rel_p == inc_p:
            return True
        try:
            rel_p.relative_to(inc_p)
            return True
        except ValueError:
            continue
    return False




def build_pack_matcher(
    repo: Path, session_excludes: list[str],
) -> Optional[BaleignoreMatcher]:
    """Compose `.baleignore` lines with this session's extra exclude
    patterns into a single matcher. Returns None when there's neither a
    file nor any session patterns, so the pack walk can skip the per-path
    check entirely in the common case.

    The session-excludes pass through the same parser as the file
    contents — same syntax, same semantics, same negation rejection.
    `walk_for_pack` accepts the combined matcher; it does not need to
    know which patterns came from which source. The wizard previews the
    file contents separately so the user still understands what's
    persistent vs session-scoped, but at walk time they're the same set.
    """
    from __main__ import (  # lazy — see module docstring
        BALEIGNORE_FILE,
        BaleignoreMatcher,
        fail,
    )
    file_lines: list[str] = []
    f = repo / BALEIGNORE_FILE
    if f.is_file():
        try:
            file_lines = f.read_text(encoding="utf-8").splitlines()
        except OSError as e:
            fail(f"could not read {f}: {e}")
    combined = file_lines + list(session_excludes)
    if not any(ln.strip() and not ln.strip().startswith("#")
               for ln in combined):
        return None
    try:
        return BaleignoreMatcher.from_lines(combined)
    except ValueError as e:
        # `.baleignore` was already validated by load_baleignore in any
        # surface that called it; this branch fires when a session-extra
        # pattern triggered the negation guard. Include the offending
        # pattern in the message — the user typed it.
        fail(f"invalid session exclude pattern: {e}")



def gather_files_for_pack(repo: Path, includes: list[str]) -> list[str]:
    """Return repo-relative paths that should land in the request's context/,
    with no threshold caps engaged. Thin wrapper over walk_for_pack — kept
    as a named entry point because the filter chain (BALE.md sections 6.4
    and 7.5 step 5) is conceptually distinct from the threshold projection
    and a future caller (e.g. a `bale debug filter` introspection command)
    will want just the list, not the projection. cmd_pack itself uses
    walk_for_pack directly so it gets the projection in the same pass.

    Honors `.baleignore` at the repo root (build_pack_matcher loads it) but
    has no surface for session-scoped excludes — those are wizard/CLI-driven
    and `cmd_pack` plumbs them through directly. A debug caller that wants
    to test session excludes can use walk_for_pack with a pre-built matcher
    rather than going through this convenience entry point."""
    matcher = build_pack_matcher(repo, [])
    return walk_for_pack(
        repo, includes, caps=PackCaps(), force=True, matcher=matcher,
    ).files


# ---------------------------------------------------------------------------
# 3. Scope projection + threshold caps (BALE.md section 7.4)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PackCaps:
    """Threshold caps for a pack walk. The hard caps are the only knobs
    --max-* exposes; the soft caps are deliberately not user-tunable, since
    their job is to nudge the user toward thinking about scope before pack
    proceeds, not to be a second tuning surface."""
    max_files_soft: int = PACK_MAX_FILES_SOFT
    max_files_hard: int = PACK_MAX_FILES_HARD
    max_size_soft: int = PACK_MAX_SIZE_SOFT
    max_size_hard: int = PACK_MAX_SIZE_HARD
    max_depth: int = PACK_MAX_DEPTH


@dataclass
class PackProjection:
    """Result of walk_for_pack: the surviving file list plus the numbers the
    threshold-breach prompt and the refusal message both want to display.

    `files` is sorted on return — matches the old gather_files_for_pack
    contract. On a hard breach `files` holds the *partial* list collected
    up to the short-circuit; the caller should treat it as diagnostic, not
    as the set to pack. `largest_dirs` is sorted descending by bytes, capped
    at PACK_LARGEST_DIRS_TOPN — designed for the prompt's brief overview,
    not for surveying the whole tree. `hard_breach` is the cap that
    triggered short-circuit (only set when force=False); it's the field
    cmd_pack reads to decide refusal. `hard_breaches_seen` is the full set
    of hard caps the final totals exceed — populated only under --force,
    where the walk doesn't short-circuit, so the FORCE audit log can name
    every cap that was bypassed instead of just the first."""
    files: list[str]
    total_bytes: int
    max_depth_seen: int
    # (top-level-dir-name, total_bytes_in_dir, file_count_in_dir), descending by bytes.
    largest_dirs: list[tuple[str, int, int]]
    # Human-readable description of the cap that tripped short-circuit, or None.
    hard_breach: Optional[str] = None
    # Hard caps the final totals exceed (populated only under --force).
    hard_breaches_seen: list[str] = field(default_factory=list)
    # Soft caps exceeded by final totals (only when no hard breach was seen).
    soft_breaches: list[str] = field(default_factory=list)


def walk_for_pack(
    repo: Path,
    includes: list[str],
    *,
    caps: PackCaps,
    force: bool,
    matcher: Optional[BaleignoreMatcher] = None,
) -> PackProjection:
    """Enumerate files for pack, applying the filter chain, while accumulating
    file count, total size, max depth, and per-top-level-dir totals.

    Filter chain (BALE.md sections 6.4, 7.5 step 5): git ls-files → drop
    non-files → drop baked-in excluded dirs → drop secrets → drop paths
    matched by the .baleignore-plus-session matcher (if any) → keep only
    paths under --include. Order matches the v0.0.9 function's filter chain
    with the matcher slotted before --include — same reasoning as the
    other exclude filters: cheaper to drop matched paths early than to
    run them through the --include pruner.

    `matcher` is the combined `.baleignore`-plus-session-excludes matcher
    built by `build_pack_matcher`. None (the common case for repos without
    a `.baleignore` and a no-CLI-exclude session) skips the per-path
    matcher check entirely.

    Short-circuit (BALE.md §7.4): when `force` is False, the walk stops the
    moment a hard cap is exceeded, reporting which cap triggered in
    `hard_breach`. When `force` is True, the walk runs to completion with
    no breach detection — --force callers want the full set, not a count
    of what they're bypassing. Soft breaches are computed only when no
    hard breach tripped, since a hard breach already obviates the prompt.

    Depth semantics: `depth` is the number of directory components above
    the file ('foo.txt' is depth 0, 'a/b/foo.txt' is depth 2). A cap of
    20 means files up to 20 directories deep are allowed; the 21st-level
    file trips the cap. Files at depth 0 are bucketed under '(root)' in
    largest_dirs so root-level files don't disappear from the report."""
    files: list[str] = []
    total_bytes = 0
    max_depth_seen = 0
    dir_bytes: dict[str, int] = {}
    dir_counts: dict[str, int] = {}
    hard_breach: Optional[str] = None

    for rel in list_git_files(repo):
        # Filter chain — matches gather_files_for_pack's body so the
        # surviving set on a no-cap run is consistent across entry points.
        if not (repo / rel).is_file():
            continue
        if is_under_excluded_dir(rel):
            continue
        if is_secret_excluded(rel, repo):
            continue
        if matcher is not None and matcher.matches(rel):
            continue
        if not is_under_include(rel, includes):
            continue

        # File survives. Account for it before the cap check, so the
        # breach message can name the file count and size that *include*
        # the offending entry — clearer than "you were at 99,999 and the
        # next file would have been #100,000".
        try:
            size = (repo / rel).stat().st_size
        except OSError:
            # Secrets-and-perms gaps shouldn't crash the walk. Treat
            # unreadable as 0 bytes; the file's still in the surviving
            # set per the filter chain.
            size = 0

        parts = Path(rel).parts
        depth = len(parts) - 1
        top = parts[0] if depth > 0 else "(root)"

        files.append(rel)
        total_bytes += size
        if depth > max_depth_seen:
            max_depth_seen = depth
        dir_bytes[top] = dir_bytes.get(top, 0) + size
        dir_counts[top] = dir_counts.get(top, 0) + 1

        # Hard-cap short-circuit — only when not --force. The order
        # (files → size → depth) is the order the messages will read
        # most naturally if multiple caps would have tripped, since
        # only the first one is reported.
        if not force:
            if len(files) >= caps.max_files_hard + 1:
                hard_breach = (
                    f"file count {len(files):,} exceeds hard cap "
                    f"{caps.max_files_hard:,}"
                )
                break
            if total_bytes > caps.max_size_hard:
                hard_breach = (
                    f"total size {format_bytes(total_bytes)} exceeds hard cap "
                    f"{format_bytes(caps.max_size_hard)}"
                )
                break
            if depth > caps.max_depth:
                hard_breach = (
                    f"path depth {depth} exceeds hard cap {caps.max_depth} "
                    f"(at {rel})"
                )
                break

    # Largest-directories report. Only meaningful when there's something to
    # report — root-only walks just have ('(root)', ...) which is still useful.
    largest = sorted(
        ((d, dir_bytes[d], dir_counts[d]) for d in dir_bytes),
        key=lambda t: t[1],
        reverse=True,
    )[:PACK_LARGEST_DIRS_TOPN]

    # Post-walk breach detection.
    #
    # `hard_breach` is set inside the loop only when the loop short-circuited,
    # which only happens when force=False. So:
    #   - force=False, no breach: hard_breach=None, hard_breaches_seen=[],
    #                             may set soft_breaches
    #   - force=False, breach:    hard_breach="…", hard_breaches_seen=[],
    #                             soft_breaches=[] (we never get past the break)
    #   - force=True, breach:     hard_breach=None, walk ran to completion;
    #                             compute hard_breaches_seen + soft_breaches
    #                             against final totals so the FORCE audit log
    #                             can name every cap that was bypassed.
    #
    # The soft/hard separation in the audit case: list soft breaches only when
    # no hard breach is seen, otherwise the soft list is redundant noise —
    # exceeding the hard cap necessarily exceeds the soft cap of the same kind.
    hard_breaches_seen: list[str] = []
    soft_breaches: list[str] = []
    if hard_breach is None:
        if len(files) > caps.max_files_hard:
            hard_breaches_seen.append(
                f"file count {len(files):,} exceeds hard cap "
                f"{caps.max_files_hard:,}"
            )
        if total_bytes > caps.max_size_hard:
            hard_breaches_seen.append(
                f"total size {format_bytes(total_bytes)} exceeds hard cap "
                f"{format_bytes(caps.max_size_hard)}"
            )
        if max_depth_seen > caps.max_depth:
            hard_breaches_seen.append(
                f"path depth {max_depth_seen} exceeds hard cap "
                f"{caps.max_depth}"
            )
        if not hard_breaches_seen:
            if len(files) > caps.max_files_soft:
                soft_breaches.append(
                    f"file count {len(files):,} exceeds soft cap "
                    f"{caps.max_files_soft:,}"
                )
            if total_bytes > caps.max_size_soft:
                soft_breaches.append(
                    f"total size {format_bytes(total_bytes)} exceeds soft cap "
                    f"{format_bytes(caps.max_size_soft)}"
                )

    return PackProjection(
        files=sorted(files),
        total_bytes=total_bytes,
        max_depth_seen=max_depth_seen,
        largest_dirs=largest,
        hard_breach=hard_breach,
        hard_breaches_seen=hard_breaches_seen,
        soft_breaches=soft_breaches,
    )


def parse_size_arg(s: str) -> int:
    """Parse a --max-size value. Accepts a bare byte count ('5000000'), or
    an integer suffixed with K/M/G (case-insensitive; KB/MB/GB also accepted).
    Multiplier is 1024-based, matching the OS-style 'M' = 2^20 convention
    bale uses throughout (see PACK_MAX_SIZE_* and format_bytes). Raises
    ValueError with a user-facing message on a malformed input — callers
    surface that via fail()."""
    s = (s or "").strip()
    if not s:
        raise ValueError("empty size value")
    # Try the two-char suffixes first ('KB', 'MB', 'GB') so '100MB' doesn't
    # get tail-stripped as '100M' + leftover 'B' on the int parse.
    mults = {"K": 1024, "M": 1024**2, "G": 1024**3}
    upper = s.upper()
    if len(upper) >= 2 and upper[-2:] in ("KB", "MB", "GB"):
        try:
            return int(upper[:-2]) * mults[upper[-2]]
        except ValueError:
            raise ValueError(f"invalid size value: {s!r}")
    if upper[-1] in mults:
        try:
            return int(upper[:-1]) * mults[upper[-1]]
        except ValueError:
            raise ValueError(f"invalid size value: {s!r}")
    try:
        return int(s)
    except ValueError:
        raise ValueError(
            f"invalid size value: {s!r} (expected bytes, or a number with "
            f"K/M/G suffix, e.g. '500M', '1G')"
        )


def format_bytes(n: int) -> str:
    """Pretty-print a byte count using 1024-based units (KB = 2^10, etc.).
    Mirrors the convention used in BALE.md's example projection block and
    in the soft-breach prompt — sticking to one unit family across all
    bale output."""
    if n < 1024:
        return f"{n} B"
    if n < 1024**2:
        return f"{n / 1024:.1f} KB"
    if n < 1024**3:
        return f"{n / (1024**2):.1f} MB"
    return f"{n / (1024**3):.2f} GB"


def format_projection_block(projection: PackProjection) -> str:
    """Render the human-readable projection block per BALE.md §7.4. Shown to
    the user before the y/N prompt on a soft breach, on stderr as the
    'warn and proceed' message in piped mode, and inside the hard-breach
    refusal message — same content in all three places, single source of
    truth."""
    lines = [
        "This pack would include:",
        f"  Files:      {len(projection.files):,}",
        f"  Size:       {format_bytes(projection.total_bytes)}",
        f"  Max depth:  {projection.max_depth_seen} levels",
    ]
    if projection.largest_dirs:
        lines.append("")
        lines.append("Largest directories:")
        for d, b, c in projection.largest_dirs:
            label = d if d == "(root)" else f"{d}/"
            lines.append(f"  {label:<14} {format_bytes(b):>10}   {c:>6,} files")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# 4. Manifest and tarball construction
# ---------------------------------------------------------------------------

def build_request_manifest(
    sid: str,
    project_name: str,
    goal: str,
    constraints: list[str],
    out_of_scope: list[str],
    expects_probe: str,
    context_paths: list[str],
    depends_on: Optional[dict] = None,
    provenance: Optional[dict] = None,
    *,
    resolved_scope: list[str],
) -> dict:
    """Per TARBALL.md section 3.2. `depends_on` defaults to the v0.0.1 shape
    ({previous_response: None, previous_probe: None}); `bale handoff` passes
    a populated dict pointing at the bailout it's continuing from, which is
    the only path that sets `previous_response` non-null in v0.0.6.

    `resolved_scope` (v0.3.21, board 33) is the session's declared scope
    stamped into the manifest — the same value the caller records in the
    registry (persist_pack_session's `scope`), serialized here so the
    worker can read from inside the tarball what the ADR-0007 gates will
    enforce repo-side: `[]` for a read-only pack, the resolved include
    set otherwise. One source, never a re-derivation: callers pass the
    exact list they persist. Required keyword-only — both request-building
    paths (pack, handoff) always stamp it — while the schema addition is
    additive per the `superseded_session` precedent (the property is not
    required, so previously stamped manifests stay valid).

    `depends_on.superseded_session` (v0.3.17, board 26) is normalized in
    here — setdefault(None) on whatever dict arrives — so every manifest
    bale builds carries the key with a uniform shape: the sid of the
    session this pack closed as superseded-by-split (cmd_pack passes it
    on a supersession pack), or null everywhere else, including the
    handoff path, which never supersedes. The schema addition is
    additive (the key is a nullable property, never required), so
    previously stamped manifests stay valid.

    `provenance` (v0.3.8, session B1) is the pack-time stamp from
    build_provenance_block; both request-building paths pass one, so the
    key is present on every request bale builds. Optional here (and in
    request-manifest.schema.json) so hand-rolled requests and pre-0.3.8
    manifests remain valid — the schema change is additive."""
    if depends_on is None:
        depends_on = {
            "previous_response": None,
            "previous_probe": None,
        }
    depends_on.setdefault("superseded_session", None)
    manifest = {
        "session_id": sid,
        "project": project_name,
        "goal": goal,
        "depends_on": depends_on,
        "constraints": constraints,
        "out_of_scope": out_of_scope,
        "expects_probe": expects_probe,
        "context_included": [f"context/{p}" for p in context_paths],
        "resolved_scope": list(resolved_scope),
    }
    if provenance is not None:
        manifest["provenance"] = provenance
    return manifest


def build_provenance_block(
    repo: Path,
    *,
    packer_flag: Optional[str] = None,
    work_class: str = "mixed",
    checkpoint_scope_admitted: bool = False,
) -> dict:
    """Assemble the request manifest's provenance block (v0.3.8, B1).

    Stamps six facts about the pack, per request-manifest.schema.json:

    - `bale_version` — this install's VERSION constant.
    - `contract_docs` — sha256 of each injected global doc, hashed from
      the install at pack time. Pins exactly which contract text the
      session ran under; a doc edit between two packs shows up as a
      hash change in the longitudinal record.
    - `packer` — flag > [identity].packer (project > global via the
      merged config) > the literal "unconfigured", which is stamped
      rather than omitted so the block's shape is uniform, with a
      logged hint pointing at `bale config init`. A misconfigured
      identity is loud at read time (get_identity_packer's fatal shape
      check), never silently mis-attributed.
    - `work_class` — the --work-class enum value; callers with no flag
      surface (handoff) pass the "mixed" default.
    - `checkpoint` (v0.3.28, board 6 session C) — the contract_docs
      precedent extended to the blind checkpoint: `{path, sha256}` of
      the configured `[validation] base` script's bytes at the
      pack-time target tip (HEAD — pack refuses a detached HEAD
      upstream, so HEAD is the target branch's tip), or explicit null
      when no checkpoint is configured. Absence of the KEY therefore
      remains the pre-v0.3.28 / hand-rolled-request signal, which is
      what keeps apply's stamp verification (BALE.md §8.5) additive.
      Configured-but-dangling at the tip is a loud refusal — the D1
      dangling rule caught at request-build time, before apply ever
      sees the broken oracle reference — though both request-building
      paths (pack, and handoff since v0.3.33) run
      checkpoint_blindness_preflight pre-sid and already refused it;
      the re-check here is defense in depth for any future caller.
    - `checkpoint_scope_admitted` (v0.3.28, session C) — true when the
      caller admitted a checkpoint-covering scope past the blindness
      refusal via --allow-checkpoint-in-scope; false otherwise. Both
      request-building paths carry the flag and pass their own gate's
      admission through this parameter — pack against its resolved
      include set (v0.3.28), handoff against its reading-plan scope
      (the mirroring flag, v0.3.33).
      Stamped unconditionally so bale-built blocks keep a uniform
      shape (the superseded_session precedent), and echoed into
      telemetry via the response's feedback.mechanical.provenance —
      which is how the session's record carries the admission.

    Reads the merged config itself so both request-building call sites
    stay wiring-thin. Doc hashing reads the same DOCS_DIR files
    build_request_tarball injects, so the hashes describe the bytes the
    worker actually receives.
    """
    from __main__ import (  # lazy — see module docstring
        DOCS_DIR,
        GLOBAL_DOCS,
        VERSION,
        fail,
        log,
    )
    import bale_config  # lazy — see module docstring
    contract_docs: dict[str, str] = {}
    for doc in GLOBAL_DOCS:
        h = hashlib.sha256()
        h.update((DOCS_DIR / doc).read_bytes())
        contract_docs[doc] = h.hexdigest()

    merged = bale_config.merged_config(repo)

    packer = packer_flag.strip() if isinstance(packer_flag, str) else None
    if not packer:
        packer = bale_config.get_identity_packer(merged)
    if not packer:
        packer = "unconfigured"
        log("provenance: no packer identity set — stamping "
            "packer=\"unconfigured\". Set one with `bale config init` "
            "([identity].packer) or pass --packer.")

    # The checkpoint stamp (v0.3.28, session C). Bytes come from the
    # committed tip, never the working tree — committed-is-ratified,
    # the same rule apply's execution side holds (BALE.md §8.5) — so
    # the stamped hash is exactly what apply's base-tree extraction
    # will hash when nothing changed in between. Binary-exact via a
    # direct subprocess call (text=False), mirroring
    # run_blind_checkpoint's extraction, so stamp and execution hash
    # the same bytes.
    checkpoint_path = bale_config.get_validation_base(merged)
    checkpoint_stamp: Optional[dict] = None
    if checkpoint_path is not None:
        blob = subprocess.run(
            ["git", "show", f"HEAD:{checkpoint_path}"],
            cwd=str(repo), capture_output=True,
        )
        if blob.returncode != 0:
            fail(f"blind checkpoint missing at the pack-time tip: "
                 f"bale.toml [validation] base names "
                 f"{checkpoint_path!r}, but HEAD has no committed file "
                 f"at that path. A working-tree-only checkpoint is not "
                 f"yet the project's oracle (committed-is-ratified). "
                 f"Remedies: commit the checkpoint at the named path, "
                 f"or clear the key via `bale config init`.")
        checkpoint_stamp = {
            "path": checkpoint_path,
            "sha256": hashlib.sha256(blob.stdout).hexdigest(),
        }
        log(f"provenance: checkpoint stamped {checkpoint_path} "
            f"(sha256 {checkpoint_stamp['sha256'][:12]}, HEAD bytes)")

    return {
        "bale_version": VERSION,
        "contract_docs": contract_docs,
        "packer": packer,
        "work_class": work_class,
        "checkpoint": checkpoint_stamp,
        "checkpoint_scope_admitted": bool(checkpoint_scope_admitted),
    }


def checkpoint_blindness_preflight(repo: Path, pack_scope: list,
                                   *, allow: bool,
                                   caller: str = "pack") -> bool:
    """The pack-time blindness gate (v0.3.28, board 6 session C; BALE.md
    §7.1 step 4b): refuse a resolved include set that covers the
    configured blind checkpoint's path, and refuse a configured
    checkpoint that dangles at the pack-time tip.

    Returns True when a covering scope was admitted past the refusal by
    --allow-checkpoint-in-scope (the caller stamps the admission into
    the manifest's provenance), False otherwise — including the vacuous
    cases: no checkpoint configured, or a scope that does not cover it
    (a read-only pack's empty scope covers nothing by construction).

    The two refusals, in check order:

    - **Dangling at the tip** (the D1 rule, caught at request-build
      time): bale.toml names a checkpoint HEAD has no committed file
      for. Caught here, pre-sid, so the broken oracle reference never
      produces a session doomed to refuse at apply; the provenance
      stamp builder re-checks as defense in depth for any future
      caller.
    - **Scope covers the checkpoint** (D5 layer 1, the contract layer):
      the checkpoint is the planner's oracle, and any path by which the
      worker under evaluation authors or selects its own oracle is the
      self-oracle shape this refusal closes. Coverage uses the same
      containment test as the apply-side drift gate (scope_covers_path
      — directory entries cover subtrees, "." covers everything), so
      the two gates agree on what "in scope" means; keeping the path
      out of scope here is what lets the existing step-14 drift gate do
      the rest at apply time. The sanctioned ordinary update path needs
      no session at all: the checkpoint is planner-authored by the §1
      floor's own wording, so the planner edits and commits it
      directly, exactly as they edit bale.toml. The override exists for
      the deliberate exception (a checkpoint-maintenance session the
      planner chooses to delegate); its use is loud (FORCE: line) and
      recorded (the provenance stamp the caller writes).

    Sited before the ADR-0007 disjointness gate on both of cmd_pack's
    gate paths, so a blindness refusal precedes any scope-collision
    conversation. cmd_handoff (v0.3.33; BALE.md §11 row 30) is the
    second caller: same gate, run pre-sid against the handoff's
    reading-plan scope, with the mirroring --allow-checkpoint-in-scope
    flag feeding `allow` — one implementation, so the two
    request-building paths cannot drift on what "in scope" means.
    `caller` (v0.3.34) names which command is refusing — "pack"
    (default) or "handoff" — and is passed through verbatim to
    format_checkpoint_scope_refusal, which swaps only the
    narrowing-remedy sentence on it (the diagnosis and flag-successor
    text stay byte-shared; the swap's rationale lives on the
    formatter). Pack's call sites ride the default unedited. bale.toml itself is deliberately NOT added to this
    refusal at v1: it is legitimately session-editable (hooks,
    staging), in-flight retargeting is already inert (apply reads the
    merged config from the repo working tree, never the staged
    overlay), and a merged bale.toml edit is a one-line, review-visible
    diff — the accepted residue, re-trigger: the first observed worker
    edit to [validation] keys in a merged session.
    """
    from __main__ import fail, log, scope_covers_path  # lazy — see module docstring
    import bale_config  # lazy — see module docstring
    from bale_report import format_checkpoint_scope_refusal  # lazy — see module docstring

    checkpoint_path = bale_config.get_validation_base(
        bale_config.merged_config(repo))
    if checkpoint_path is None:
        return False

    probe = subprocess.run(
        ["git", "cat-file", "-e", f"HEAD:{checkpoint_path}"],
        cwd=str(repo), capture_output=True,
    )
    if probe.returncode != 0:
        fail(f"blind checkpoint missing at the pack-time tip: bale.toml "
             f"[validation] base names {checkpoint_path!r}, but HEAD "
             f"has no committed file at that path. A working-tree-only "
             f"checkpoint is not yet the project's oracle "
             f"(committed-is-ratified). Remedies: commit the checkpoint "
             f"at the named path, or clear the key via "
             f"`bale config init`.")

    if not scope_covers_path(pack_scope, checkpoint_path):
        log(f"checkpoint blindness gate passed: pack scope does not "
            f"cover {checkpoint_path}")
        return False

    if not allow:
        fail(format_checkpoint_scope_refusal(
            checkpoint_path=checkpoint_path, scope=pack_scope,
            caller=caller))

    # force=True: an admitted checkpoint-covering scope is an override
    # event of the same species as --allow-out-of-scope — the FORCE:
    # line is the audit trail; the provenance stamp
    # (checkpoint_scope_admitted, echoed into telemetry via the
    # response's provenance echo) is the durable copy.
    log(f"checkpoint-covering scope admitted by "
        f"--allow-checkpoint-in-scope: pack scope covers "
        f"{checkpoint_path} (the planner delegated oracle maintenance "
        f"deliberately; admission stamped into provenance)", force=True)
    return True


def build_request_tarball(
    sid: str,
    context_entries: list[tuple[str, Path]],
    manifest: dict,
    out_path: Path,
    *,
    readme_body: Optional[str] = None,
) -> None:
    """Write the request tarball to out_path. Layout per TARBALL.md section 3.1.

    `context_entries` is a list of (context_relative_path, source_absolute_path)
    tuples. For `bale pack` the tuples are (rel, repo / rel) for each repo-
    relative file the scope selected. For `bale handoff` there's exactly one
    tuple — ("handoff.md", <extracted bailout dir>/handoff.md) — because the
    source lives outside the project's repo. Decoupling the context-relative
    path from the source path is what makes both call sites work without one
    pretending to be the other.

    `readme_body` is the §7.3 wizard's optional prose: written as `README.md`
    at the top of the request tarball when set, omitted entirely when None.
    Per TARBALL.md §3.1 (and the wizard's "empty buffer = skip" contract in
    BALE.md §7.3), absence is the canonical signal that the manifest's
    structured fields are the whole story.

    The caller is responsible for path safety on each entry's
    context_relative_path (no traversal, no absolute, no .bale/.git prefix);
    both current callers feed already-filtered inputs.
    """
    from __main__ import (  # lazy — see module docstring
        DOCS_DIR,
        GLOBAL_DOCS,
        INJECTED_TOOLS,
        TOOLS_DIR,
    )
    nnn = sid[-3:]
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        request_dir = Path(tmp) / f"request-{nnn}"
        request_dir.mkdir()

        # Inject the global docs from the bale installation. copy2 +
        # follow_symlinks=False preserves mode bits — see the context-files
        # copy below for why that matters for the rest of the tarball.
        for doc in GLOBAL_DOCS:
            shutil.copy2(DOCS_DIR / doc, request_dir / doc, follow_symlinks=False)

        # Inject the worker-side tools beside the four globals, per
        # TARBALL.md §3.1: request-NNN/tools/<each INJECTED_TOOLS member>
        # — the lint (v0.3.8, session B1) and the crafter (session 007;
        # consolidated into the list in v0.3.19, retiring the guarded
        # interim copy that lived here while bin/bale was held by a
        # concurrent session). Same copy2 treatment as the docs so each
        # tool arrives executable. main()'s request-command sanity check
        # (gating both callers: pack and handoff) verified presence, so
        # a missing file here means the install broke mid-run — let the
        # copy raise and the caller's failed-to-build handler surface it.
        tools_dir = request_dir / "tools"
        tools_dir.mkdir()
        for tool in INJECTED_TOOLS:
            shutil.copy2(TOOLS_DIR / tool, tools_dir / tool,
                         follow_symlinks=False)

        # manifest.json.
        (request_dir / "manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
        )

        # Optional README.md. Written when the wizard collected non-empty
        # prose; omitted otherwise. Trailing newline is normalized so the
        # tarball doesn't ship the rare buffer that ends mid-line.
        if readme_body is not None:
            text = readme_body if readme_body.endswith("\n") else readme_body + "\n"
            (request_dir / "README.md").write_text(text, encoding="utf-8")

        # context/<files>. copy2 + follow_symlinks=False preserves mode bits
        # so an executable script in the project arrives in context/ still
        # executable, matching what stage_response does for files/ in
        # response tarballs.
        context_dir = request_dir / "context"
        context_dir.mkdir()
        for rel, src in context_entries:
            dst = context_dir / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst, follow_symlinks=False)

        # Tar with arcname so the archive's top-level entry is `request-NNN/`,
        # independent of the temp directory's filesystem path.
        with tarfile.open(out_path, "w:gz") as tf:
            tf.add(str(request_dir), arcname=f"request-{nnn}")


def persist_pack_session(repo: Path, sid: str, manifest: dict,
                         scope: Optional[list[str]] = None,
                         origin_branch: Optional[str] = None) -> None:
    """Write per-session metadata. Called AFTER tarball is built but BEFORE
    the lock — see BALE.md section 7.6.

    `scope` is the session's resolved include set (ADR-0007), recorded
    via persist_session_scope so the disjointness gates can read it.
    Both request-building call sites pass one since v0.3.2 — pack its
    resolved --include set, handoff its resolved reading-plan file set.
    None writes no scope.json, in which case read_session_scope reads
    the session as whole-tree, the conservative default. An empty list
    ([], v0.3.15) is distinct from None: it records the read-only
    session shape, which reads back as [] — locks nothing, may land
    nothing — never falling through to the conservative whole-tree
    read.

    `origin_branch` is the session's integration target (ADR-0008,
    v0.3.5): the branch checked out when the request was packed, which is
    the branch its content was gathered from and the branch its response
    merges into — fixed at pack time so a later apply run from an
    unrelated (even dirty) checkout still knows where it lands. Both
    request-building call sites pass current_branch(repo). The stamp is
    required at apply: resolve_target_branch hard-refuses a session with
    a missing or empty stamp. None or the detached-HEAD sentinel "HEAD"
    writes no stamp and therefore produces a session apply will refuse —
    cmd_pack's and cmd_handoff's pre-flights each refuse a detached HEAD
    before reaching here (BALE.md §7.1 step 4a; §11 rows 23–24), so on
    both request-building paths the sentinel is unreachable; the guard
    stays as defense in depth for any other caller.
    """
    from __main__ import persist_session_scope  # lazy — see module docstring
    sessions_dir = repo / ".bale" / "sessions" / sid
    sessions_dir.mkdir(parents=True, exist_ok=True)
    (sessions_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
    )
    if scope is not None:
        persist_session_scope(repo, sid, scope)
    if origin_branch and origin_branch != "HEAD":
        (sessions_dir / "origin_branch").write_text(origin_branch + "\n")


# ---------------------------------------------------------------------------
# 5. Wizard (BALE.md section 7.3)
# ---------------------------------------------------------------------------
#
# Interactive prompts for the BALE.md §7.3 wizard. Wizard mode engages
# when `bale pack` is invoked without enough on the command line to skip
# it — specifically when either the goal positional or --slug is missing.
# Once engaged, the wizard walks the optionals (excludes, constraints,
# out_of_scope) too, prompting only for fields the CLI didn't already
# provide. The README step is no longer wizard-internal: since v0.2.4 it
# lives in _resolve_readme_body (this section), called by cmd_pack on
# both the wizard and fully-specified paths, because --readme-file and
# --edit give the README CLI surfaces that exist independently of the
# wizard. The wizard's y/N-then-$EDITOR flow survives inside the
# resolver as the lowest-precedence branch.
#
# Pattern visibility: the wizard previews any `.baleignore` patterns
# already at the repo root before prompting for session-scoped additions.
# Session excludes do NOT persist — they shape this pack only and vanish
# afterward. Persistence lives in `bale config init`'s .baleignore step
# (bale_config.walkthrough_baleignore), so the two surfaces stay
# separable: ad-hoc filtering at pack, durable filtering at config init.
#
# These helpers are pack-specific (single caller — cmd_pack). They live
# in their own section because the wizard is a coherent enough subject
# that grouping the prompts under a banner is cheaper than letting them
# sprawl across cmd_pack's prologue, and parallel to the other "Pack:
# <aspect>" sections already in the file.

# README scaffold template (BALE.md §7.3). Saved as a constant so the
# wizard test can read it back and compare. The braces are replaced by
# the wizard's collected answers; the comment text instructs the user
# how to skip the file (empty buffer omits per BALE.md §7.3).
_PACK_README_SCAFFOLD = """\
# {goal}

<!--
This README is OPTIONAL — extra prose context beyond what the manifest's
structured fields carry. The manifest will already include:

  goal:         {goal}
  constraints:  {constraints}
  out_of_scope: {out_of_scope}

Add prose below this comment that doesn't fit those fields (e.g. a
short story of why the session exists, links to context the architect
wants Claude to read first, a list of files-of-interest with reasons).
Save an empty buffer to omit this README entirely; the structured
fields above will still ship in the manifest either way.
-->

"""


def _wizard_input_required(prompt: str, *, validator=None,
                           validator_hint: str = "") -> str:
    """Single-line prompt, loops until the user gives a non-empty value
    that passes `validator` (if supplied). EOF/^C aborts the whole pack.
    Used for the required wizard fields (goal, slug)."""
    from __main__ import fail  # lazy — see module docstring
    while True:
        try:
            raw = input(prompt).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            fail("aborted at wizard prompt")
        if not raw:
            print("  (cannot be empty)")
            continue
        if validator is not None and not validator(raw):
            print(f"  ({validator_hint})")
            continue
        return raw


def _wizard_input_list(label: str) -> list[str]:
    """Multi-line prompt; one item per line, blank line ends collection.
    Used for the optional list fields (constraints, out_of_scope). EOF/^C
    aborts the whole pack (consistent with the required prompts — a user
    bailing out partway through has signalled they don't want this
    session, not "ship what's collected so far")."""
    from __main__ import fail  # lazy — see module docstring
    print(label)
    items: list[str] = []
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            fail("aborted at wizard prompt")
        if not raw:
            return items
        items.append(raw)


def _wizard_input_session_shape(args: argparse.Namespace) -> None:
    """The v0.3.15 session-shape prompt (BALE.md §7.3): will this session
    land changes, or is it read-only — and, in the same exchange, what
    work class is it? Mutates args.read_only / args.work_class in place.

    One added question, not an interrogation (BALE.md §5.2): the two
    facts share one prompt, and every path with a CLI answer skips the
    part it already has:

    - `--read-only` given → nothing to ask; the shape is declared and
      work_class rides the flag-or-inference path at the provenance
      stamp in cmd_pack.
    - `--work-class` given (without `--read-only`) → only the binary
      lands-changes/read-only half remains; ask that alone.
    - Neither given → the combined prompt below. Bare Enter takes
      'mixed', today's default, so a user who doesn't care presses
      Enter once and gets exactly the pre-v0.3.15 stamp — the delta is
      that the whole-tree scope is now an *answered* default, never a
      silent omission.

    The read-only answer sets args.read_only and leaves args.work_class
    for cmd_pack's provenance-time inference (meta, logged there), so
    the inference has one home whichever surface — flag or wizard —
    declared the shape. EOF/^C aborts the whole pack, consistent with
    the other wizard prompts."""
    from __main__ import fail  # lazy — see module docstring
    if args.read_only:
        return

    if args.work_class is not None:
        # Work class already declared on the CLI; only the shape half of
        # the exchange remains.
        prompt = ("Will this session land changes? [Y/n] "
                  "(n = read-only: discussion, orchestration, audit) > ")
        while True:
            try:
                raw = input(prompt).strip().lower()
            except (EOFError, KeyboardInterrupt):
                print()
                fail("aborted at wizard prompt")
            if raw in ("", "y", "yes"):
                return
            if raw in ("n", "no", "r", "read-only", "readonly"):
                args.read_only = True
                return
            print("  (type y or n)")

    print("Will this session land changes, and of what kind?")
    print("  [c] code   [d] doc   [t] contract-doc   [m] meta   "
          "[x] mixed (default)")
    print("  [r] read-only — nothing lands (discussion, orchestration, "
          "audit)")
    choices = {
        "c": "code", "code": "code",
        "d": "doc", "doc": "doc",
        "t": "contract-doc", "contract-doc": "contract-doc",
        "m": "meta", "meta": "meta",
        "x": "mixed", "mixed": "mixed", "": "mixed",
    }
    while True:
        try:
            raw = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            fail("aborted at wizard prompt")
        if raw in ("r", "read-only", "readonly"):
            args.read_only = True
            return
        if raw in choices:
            args.work_class = choices[raw]
            return
        print("  (type c, d, t, m, x, or r — or Enter for mixed)")


def _resolve_supersession(args: argparse.Namespace,
                          repo: Path) -> tuple[Optional[str], Optional[str]]:
    """Resolve `--supersedes` and run the exchange (v0.3.17, board 26).

    Returns (stamp_sid, declined_sid) — at most one is non-None:

    - `stamp_sid` — the supersession happened (the parent was closed
      here, or was already closed superseded-by-split on a prior
      aborted run); the caller stamps it into
      depends_on.superseded_session.
    - `declined_sid` — the parent is open and the exchange declined the
      close; nothing closed. The caller threads it into the
      disjointness gate's refusal so the message names the declined
      supersession, and refuses the pack even when the gate would
      admit it (a --supersedes pack that neither closes its parent nor
      records lineage does something materially different from what
      the flag declared; silent-proceed would be the silent skip the
      hard rules ban).

    The exchange is the §5.2 wizard idiom (BALE.md §7.2): on a TTY, a
    y/N prompt with a decline default, naming the cost; piped stdin
    takes the decline default without a prompt — the piped path IS the
    non-interactive form (pack has no --no-interact), matching the
    no-readme guard's posture that automation never gets a destructive
    default silently. On the wizard path a decline refuses immediately
    rather than walking the user through prompts toward a guaranteed
    refusal (with the parent still open, either the gate refuses or
    the declined-supersession check does).

    Resolution of the named sid:

    - **Open** → refuse first if its bale/<sid> branch exists (the
      session reached HOLD; superseding it here would strand the
      branch — `bale revert <sid>` is the command that knows how to
      discard that state); otherwise run the exchange, and on accept
      close it through close_session_with_record — closure_reason
      superseded-by-split, command "pack", one implementation shared
      with cmd_unlock.
    - **Not open, latest telemetry closure is superseded-by-split** →
      proceed with a logged note and stamp the lineage anyway: the
      idempotent re-run of a supersession pack that aborted after the
      close (a cap refusal, an editor abort, a gate refusal against a
      second open session) must be re-runnable without manual repair.
    - **Anything else** → refuse: nothing open to supersede, and the
      sid's history doesn't say a supersession already closed it.

    The close events print to stdout here (no session log is open yet
    — the child sid doesn't exist); the durable record is the parent's
    telemetry entry, and cmd_pack journals the outcome into the child's
    session log once it opens, beside the gate journal line.
    """
    from __main__ import (  # lazy — see module docstring
        close_session_with_record,
        confirm_yn,
        fail,
        git,
        log,
        session_is_open,
    )
    from bale_report import read_telemetry_record  # lazy — see module docstring

    if args.supersedes is None:
        return None, None
    sid = args.supersedes.strip()
    if not sid:
        fail("--supersedes requires a session id.")

    if not session_is_open(repo, sid):
        record = read_telemetry_record(repo, sid)
        attempts = (record or {}).get("attempts") or []
        latest = attempts[-1] if attempts else {}
        if latest.get("closure_reason") == "superseded-by-split":
            log(f"--supersedes {sid}: not open, but its latest closure "
                f"is superseded-by-split — treating this as the "
                f"idempotent re-run of a supersession pack that aborted "
                f"after the close; lineage will be stamped")
            return sid, None
        fail(
            f"--supersedes {sid}: no open session with that id, and its "
            f"telemetry history does not show a superseded-by-split "
            f"closure — nothing to supersede. Check the sid against "
            f"`bale status`, or drop --supersedes."
        )

    # Open parent. A HOLD-reached session owns a bale/<sid> branch;
    # closing it here would strand the branch the same way cmd_unlock
    # refuses to. Same remedy: revert first.
    sid_branch = f"bale/{sid}"
    branch_check = git(["rev-parse", "--verify", "--quiet", sid_branch],
                       cwd=repo, check=False)
    if branch_check.returncode == 0:
        fail(
            f"--supersedes {sid}: branch {sid_branch} exists — that "
            f"session reached HOLD. Run `bale revert {sid}` to discard "
            f"the held branch and close the session, then re-run this "
            f"pack (the re-run proceeds via the supersession history "
            f"only if the revert stamped superseded-by-split; otherwise "
            f"re-state --supersedes is unnecessary — the parent is "
            f"closed and the gate no longer collides)."
        )

    # The exchange (§5.2 wizard idiom): decline default, cost named.
    if sys.stdin.isatty():
        accepted = confirm_yn(
            f"Close open session {sid} as superseded-by-split? Its "
            f"registry entry and .bale/sessions/ state are removed and "
            f"a closure record is written; a response for it could no "
            f"longer be applied."
        )
    else:
        accepted = False
        log(f"--supersedes {sid}: stdin is not a TTY; the exchange's "
            f"decline default applies without a prompt (nothing closed)")

    if accepted:
        telemetry_rel, _, _ = close_session_with_record(
            repo, sid,
            closure_reason="superseded-by-split",
            command="pack",
            log_path=f".bale/logs/{sid}.log",
        )
        log(f"superseded {sid} (closure record: "
            f"{telemetry_rel if telemetry_rel else 'write failed — see log'})")
        return sid, None

    log(f"supersession of {sid} declined; nothing closed")
    if args.goal is None or args.slug is None:
        # Wizard path: the refusal is guaranteed (the parent stays open
        # and a declined --supersedes pack refuses even past the gate),
        # so refuse before walking the user through prompts whose
        # answers would be thrown away.
        fail(
            f"supersession of {sid} was declined; the session stays "
            f"open. Re-run and accept the prompt, `bale unlock {sid}` "
            f"to close it by hand, or drop --supersedes."
        )
    return None, sid


def _run_readonly_sweep(repo: Path) -> list[str]:
    """The read-only sweep (v0.3.21, board 33): a read-only pack offers
    to close each open session whose recorded scope is exactly [].

    Only the read-only pack sweeps — cmd_pack calls this after the
    session shape is final on every path (post-wizard, since the
    wizard's session-shape answer can turn the pack read-only) and only
    when it is. Worker (scoped) packs and apply never trigger it; the
    board-33 out-of-scope line ("no auto-close on worker packs or on
    apply") is enforced by this call-site placement, and `bale unlock`
    remains the no-successor escape hatch.

    Per open []-scope session, on a TTY, a y/N prompt with an **accept
    default** — deliberately inverting `--supersedes`' decline default,
    because a read-only session structurally cannot lose work (its
    empty scope means the drift gate refuses everything a response
    under it could ship, so nothing appliable is abandoned by the
    close). Piped stdin declines without a prompt — automation never
    silently closes a session, the same posture as the supersession
    exchange and the no-readme guard, just with the interactive default
    flipped.

    On accept the session closes through the shared
    close_session_with_record sequencing — closure_reason
    "closed-read-only", command "pack" (the record honestly names the
    producing command; both values were already in the telemetry
    schema's enums) — the same machinery cmd_unlock and the
    supersession close use. The scope was read here to select the
    session, so it is passed through rather than re-read.

    Two deliberate skips, both logged, neither fatal to the pack (the
    sweep is a courtesy close-out, not the pack's purpose):

    - a session whose `bale/<sid>` branch exists reached HOLD (an
      operator admitted paths past the drift gate); closing it here
      would strand the branch — `bale revert <sid>` is the command
      that knows how to discard that state;
    - a declined prompt leaves the session open for the next sweep or
      `bale unlock`.

    Runs pre-sid (no session log is open yet), so these lines reach
    stdout/stderr only; cmd_pack journals the outcome into the child's
    session log once it opens, beside the gate and supersession journal
    lines. Returns the closed sids for that journal entry.
    """
    from __main__ import (  # lazy — see module docstring
        close_session_with_record,
        confirm_yn,
        git,
        log,
        open_sessions,
        read_session_scope,
    )

    closed: list[str] = []
    for sid in open_sessions(repo):
        if read_session_scope(repo, sid) != []:
            continue
        sid_branch = f"bale/{sid}"
        branch_check = git(["rev-parse", "--verify", "--quiet", sid_branch],
                           cwd=repo, check=False)
        if branch_check.returncode == 0:
            log(f"read-only sweep: {sid} has branch {sid_branch} — it "
                f"reached HOLD (paths were admitted past the drift gate), "
                f"and closing it here would strand the branch. Skipping; "
                f"run `bale revert {sid}` to discard the held state.")
            continue
        if sys.stdin.isatty():
            accepted = confirm_yn(
                f"Close open read-only session {sid} as closed-read-only? "
                f"A read-only session lands nothing, so no work is lost; "
                f"its registry entry and .bale/sessions/ state are removed "
                f"and a closure record is written.",
                default_no=False,
            )
        else:
            accepted = False
            log(f"read-only sweep: open read-only session {sid} found; "
                f"stdin is not a TTY, so the prompt's accept default does "
                f"NOT apply — declining without a prompt (automation "
                f"never silently closes a session). Close it with `bale "
                f"unlock {sid}`, or re-run this pack on a TTY.")
        if not accepted:
            if sys.stdin.isatty():
                log(f"read-only sweep: close of {sid} declined; it stays "
                    f"open for the next read-only pack or `bale unlock "
                    f"{sid}`")
            continue
        telemetry_rel, _, _ = close_session_with_record(
            repo, sid,
            closure_reason="closed-read-only",
            command="pack",
            scope=[],
            log_path=f".bale/logs/{sid}.log",
        )
        log(f"read-only sweep: closed {sid} (closure record: "
            f"{telemetry_rel if telemetry_rel else 'write failed — see log'})")
        closed.append(sid)
    return closed


def _wizard_input_excludes(repo: Path) -> list[str]:
    """The §7.3 'anything to exclude' prompt. Previews any persisted
    `.baleignore` patterns so the user knows what's already filtered before
    adding session-only ones. Returns the session-scoped additions; the
    caller composes them with `.baleignore` via `build_pack_matcher`.

    The preview uses the matcher's own normalized form, not raw file
    bytes — comment lines and blanks are already stripped, so what the
    user sees is what the walk applies. A present-but-empty file shows
    `(no patterns)` rather than nothing, to distinguish 'file exists,
    has no effect' from 'no file'.

    Each pattern goes through BaleignoreMatcher's validator (negation
    rejected, etc.) at compose time in `build_pack_matcher`, so the
    wizard doesn't second-guess syntax here — bad patterns surface as
    fail() inside the pack pipeline a few steps later, with the same
    error wording the file-load path uses."""
    from __main__ import load_baleignore  # lazy — see module docstring
    matcher = load_baleignore(repo)
    if matcher is None:
        print(
            "No .baleignore at the repo root. (Set durable patterns via "
            "`bale config init` later if you want them; for now, list "
            "anything to skip just for this pack — gitignore-style "
            "patterns, e.g. data/, *.parquet, /build/.)"
        )
    else:
        persisted = matcher.patterns
        if persisted:
            print("Current .baleignore (already filtered out):")
            for p in persisted:
                print(f"  {p}")
        else:
            print(".baleignore is present but contains no patterns.")
        print(
            "Anything else to exclude just for this pack? "
            "(one per line, blank to finish)"
        )
    return _wizard_input_list("> ")


def _prompt_soft_breach_action() -> str:
    """The §7.4 soft-cap [y]/[e]/[n] prompt. Returns 'y', 'e', or 'n'.

    Re-prompts on unrecognized input rather than picking a default for a
    typo — the choice between 'continue with this scope', 'add filters
    and re-walk', and 'abort the whole pack' is large enough that a
    silent default would surprise the user. EOF/^C is treated as 'n'
    (abort) — consistent with how the rest of the wizard treats those
    signals (a bail-out, not a confirm)."""
    print()
    print("[y] continue with this pack")
    print("[e] edit excludes (add session-only patterns and re-walk)")
    print("[n] abort")
    while True:
        try:
            raw = input("> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            return "n"
        if raw in ("y", "yes"):
            return "y"
        if raw in ("e", "edit"):
            return "e"
        if raw in ("n", "no", ""):
            # Empty input falls through to 'n' — the prompt's whole job
            # is making the user pick, and bare Enter on a scope-breach
            # prompt should be the safe choice.
            return "n"
        print(f"  (didn't recognize {raw!r}; type y, e, or n)")


def _resolve_readme_body(args: argparse.Namespace, *,
                         wizard_engaged: bool) -> Optional[str]:
    """Resolve the request README's body (BALE.md §7.3). Returns non-empty
    content, or None to omit the file. Called by cmd_pack on both the
    wizard path and the fully-specified path — one resolver so the two
    paths can't drift.

    Precedence, first match wins:

    1. `--edit` — open $EDITOR unconditionally (the flag is the "y").
       Seeded with --readme-file's content when both flags are given
       (review-then-pack), with the standard scaffold otherwise. An empty
       buffer after editing yields None (per §7.3: "Saving an empty
       buffer omits the file") — in the editor, deliberate deletion is
       the omit gesture, unlike the --readme-file-alone path below where
       an empty file is an upstream failure. cmd_pack has already
       verified --edit's preconditions (TTY stdin, no --no-edit) before
       any prompt or editor could run.
    2. `--readme-file` alone — the file's contents verbatim, no editor.
       cmd_pack resolved the path (through the inbound search paths,
       resolve_inbound_path over apply.search_paths — v0.3.6) and read
       and validated the file up front (missing or empty fails loudly
       there), so args._readme_file_body is non-empty whenever it is
       not None.
    3. Wizard engaged and not --no-edit — the §7.3 y/N prompt; on y,
       $EDITOR opens with a scaffold pre-populated from the wizard
       answers. Empty buffer omits, same as branch 1.
    4. Otherwise None — the fully-specified path with no README flags
       has no README, exactly as before v0.2.4; `--no-edit` forces skip
       of the wizard's step regardless (per §7.3).
    """
    from __main__ import (  # lazy — see module docstring
        confirm_yn,
        open_in_editor,
    )
    scaffold = _PACK_README_SCAFFOLD.format(
        goal=args.goal,
        constraints=", ".join(args.constraint) if args.constraint else "(none)",
        out_of_scope=(
            ", ".join(args.out_of_scope) if args.out_of_scope else "(none)"
        ),
    )

    # --no-readme (v0.3.8): the explicit no-prose acknowledgment. Skips
    # the wizard's y/N prompt too — the flag IS the answer — and
    # cmd_pack's no-readme guard treats it as the deliberate case.
    # Contradictory combinations (--readme-file, --edit) already failed
    # in cmd_pack's flag validation.
    if args.no_readme:
        return None

    if args.edit:
        seed = (
            args._readme_file_body
            if args._readme_file_body is not None
            else scaffold
        )
        body = open_in_editor(
            seed,
            abort_hint="drop --edit to pack without the editor step",
        )
        return body if body else None

    if args._readme_file_body is not None:
        return args._readme_file_body

    if wizard_engaged and not args.no_edit:
        if not confirm_yn("Add a README with prose context?", default_no=True):
            return None
        body = open_in_editor(
            scaffold,
            abort_hint="answer 'n' at the README prompt to skip it",
        )
        return body if body else None

    return None


def _wizard_fill_args(args: argparse.Namespace, repo: Path) -> None:
    """Run the §7.3 wizard, populating any args.* fields the CLI left
    unset. Mutates args in place; does not return. Caller has already
    verified stdin is a TTY.

    Prompt order matches the §7.3 example: goal → slug → session shape
    (v0.3.15: lands-changes-or-read-only + work class, one exchange) →
    exclude → constraints → out_of_scope. Each prompt is skipped if its CLI
    counterpart was already supplied — a user who ran `bale pack
    "my goal" --constraint foo` only sees the slug/exclude/out_of_scope
    prompts. The exclude prompt previews any persisted `.baleignore` so
    the user sees what's already filtered before adding session-only
    patterns; persistence happens via `bale config init`, not here.

    The README step — historically the wizard's last prompt — moved to
    _resolve_readme_body in v0.2.4, which cmd_pack calls right after
    this function returns, so the user-visible prompt order is
    unchanged. The move exists because --readme-file and --edit make
    README resolution reachable outside the wizard."""
    from __main__ import is_valid_slug  # lazy — see module docstring
    print("[bale pack] interactive mode — fill missing fields. ^C to abort.")
    print()

    if args.goal is None:
        args.goal = _wizard_input_required("Goal (one sentence)? > ")

    if args.slug is None:
        args.slug = _wizard_input_required(
            "Short slug (kebab-case)? > ",
            validator=is_valid_slug,
            validator_hint=(
                "must be kebab-case: lowercase letters, digits, hyphens; "
                "no leading/trailing/double hyphens"
            ),
        )

    # Session shape (v0.3.15) — the lands-changes-or-read-only question,
    # asked in the same exchange as (or instead of) work class. Sits
    # between slug and excludes per §7.3's updated prompt order; the
    # helper itself skips whatever the CLI already answered. A bare
    # cold-start pack therefore no longer resolves to whole-tree scope
    # by silent omission — the whole-tree default is now an answered
    # default (bare Enter).
    _wizard_input_session_shape(args)

    # Session excludes — skipped when --exclude was already provided on
    # the CLI (parallel to --constraint / --out-of-scope). The §7.3 prompt
    # order puts this between slug and constraints; if the CLI pre-filled
    # it, we silently skip and proceed.
    if not args.exclude:
        args.exclude = _wizard_input_excludes(repo)

    if not args.constraint:
        args.constraint = _wizard_input_list(
            "Any constraints? (one per line, blank to finish)"
        )

    if not args.out_of_scope:
        args.out_of_scope = _wizard_input_list(
            "Any out-of-scope concerns? (one per line, blank to finish)"
        )


# ---------------------------------------------------------------------------
# 6. Pack: git-init walkthrough + cmd_pack
# ---------------------------------------------------------------------------

# --- Git-init walkthrough (BALE.md §10) --------------------------------------

# The .gitignore body the walkthrough drops on a fresh init. Sourced from
# BALE.md §6.4's baked-in exclusion set — kept in parallel with the
# pack-side constants above (BAKED_IN_EXCLUDE_DIRS / SECRET_PATTERNS /
# SECRET_PATH_EXCLUDES) rather than reconstructed from them. Two reasons
# the duplication is the right call here: pack consumes those tuples
# programmatically (basename matching, plus npmrc_has_authtoken content
# inspection), and .gitignore needs a verbatim text body with grouping
# comments — reconstructing one from the other would either drop the
# comments or re-introduce the conditional-npmrc logic git can't express.
# validation.sh asserts the literal patterns are present so the two
# surfaces don't silently diverge.
_INITIAL_GITIGNORE_BODY = """\
# bale: default exclusion set (BALE.md §6.4)
# Created by the git-init walkthrough. Edit freely; bale won't rewrite this.

# Bale and git internals
.bale/
.git/

# Common big-build dirs
node_modules/
__pycache__/
.venv/
target/
dist/
build/
.next/
.nuxt/
out/
.cache/

# Common secret patterns.
# Pack's filter only excludes .npmrc when its content matches `_authToken`
# (see npmrc_has_authtoken). .gitignore can't express a content-conditional,
# so this list ignores .npmrc unconditionally — un-ignore with `!.npmrc`
# if your project's .npmrc is genuinely public (registry config only).
.env
.env.*
*.pem
*.key
*_rsa
*_dsa
*.p12
*.pfx
id_rsa
id_dsa
.aws/credentials
.npmrc
.pypirc
"""


def _write_initial_gitignore(cwd: Path) -> None:
    """Create or append the §6.4 baked-in exclusion set to .gitignore.

    On a fresh init the file is usually absent — write _INITIAL_GITIGNORE_BODY
    directly. If a .gitignore already exists (e.g., the user ran a project
    scaffolder like `npx create-foo` before `bale pack`), append the block
    while skipping any pattern lines already present so re-runs and partial
    overlaps don't accumulate duplicates. Comment and blank lines are always
    re-emitted: their job is grouping the appended block, not preserving
    uniqueness.
    """
    gi = cwd / ".gitignore"
    if not gi.exists():
        gi.write_text(_INITIAL_GITIGNORE_BODY, encoding="utf-8")
        return

    existing = gi.read_text(encoding="utf-8")
    existing_patterns = {
        ln.strip()
        for ln in existing.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    }

    block_lines: list[str] = []
    for raw in _INITIAL_GITIGNORE_BODY.splitlines():
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            block_lines.append(raw)
            continue
        if stripped in existing_patterns:
            continue
        block_lines.append(raw)

    # Ensure a blank line separates pre-existing content from the appended
    # block. If the file already ended in a blank, no extra separator is
    # needed; if it ended with content (with or without a trailing newline),
    # add enough newlines to land the block at column 0 after one blank.
    if existing.endswith("\n\n") or existing == "":
        sep = ""
    elif existing.endswith("\n"):
        sep = "\n"
    else:
        sep = "\n\n"
    with gi.open("a", encoding="utf-8") as f:
        f.write(sep + "\n".join(block_lines) + "\n")


def git_init_walkthrough(cwd: Path, *, force: bool) -> Path:
    """Per BALE.md §10. Offer to initialize a git repo at cwd.

    On accept: run `git init`, prompt for any missing git identity via
    bale_config.walkthrough_git_identity (per the manifest constraint to
    reuse that helper rather than reimplement), write a .gitignore with
    the §6.4 baked-in exclusion set, and record the initial commit. Returns
    the new repo root (== cwd) on success.

    On decline: print the spec'd "bale requires a git repo" one-liner and
    sys.exit(0). Per §10 the decline path is exit 0 — declining isn't an
    error, it's a user choice.

    Defense-in-depth: re-applies the §7.1 step 1-2 refusals before
    initializing even though cmd_pack already called refuse_system_dir on
    cwd. The inner re-check protects future callers (or future direct
    entry points to the walkthrough) from accidentally `git init`-ing at
    `/` or `$HOME`. The home-directory refusal is `--force`-overridable
    per the spec; the system-dir refusal has no override at all.

    Flow ordering note: BALE.md §10 documents the step order as
    init → identity → gitignore → commit. `git init` runs first so the
    identity prompt has a repo to write into; walkthrough_git_identity
    writes the prompted values to repo-local git config (per its own
    constraint — "never --global"), which requires an existing repo.
    The display matches that order.
    """
    from __main__ import (  # lazy — see module docstring
        confirm_yn,
        fail,
        git,
        log,
        refuse_system_dir,
    )
    import bale_config  # lazy — see module docstring
    print()
    print("This directory isn't a git repository. Bale needs git for branch")
    print("staging and the rollback story.")
    print()

    # Piped / non-interactive mode: there's no way to confirm intent and no
    # way to prompt for identity. Fail loudly rather than auto-initializing
    # a repo somewhere unexpected.
    if not sys.stdin.isatty():
        fail(
            "not in a git repo; the walkthrough needs a TTY (it prompts for "
            "confirmation and git identity). Re-run from an interactive "
            "shell, or run `git init && git add -A && git commit -m initial` "
            "yourself, then retry."
        )

    if not confirm_yn("Would you like me to set it up?", default_no=False):
        print()
        print(
            "bale requires a git repo. Re-run after `git init` or accept "
            "the walkthrough."
        )
        sys.exit(0)

    # Defense in depth — see docstring. cmd_pack already refused at this
    # cwd before calling us; the inner re-check exists in case a future
    # caller forgets that step.
    refuse_system_dir(cwd, force=force)

    print()
    print("Initializing repository...")
    try:
        git(["init"], cwd=cwd)
    except subprocess.CalledProcessError as e:
        fail(
            f"git init at {cwd} failed (exit {e.returncode}). Check "
            f"directory permissions and retry."
        )
    log(f"git init at {cwd}")
    print("  ✓ git init")

    # Identity prompts via the shared helper. It checks repo-local + global
    # scope, reports any already-set values, and prompts only for the
    # unset ones — writing to repo-local (never --global). Prints its own
    # header block, so no preamble line is needed here.
    bale_config.walkthrough_git_identity(cwd)

    _write_initial_gitignore(cwd)
    log("wrote initial .gitignore with §6.4 baked-in exclusion set")
    print("  ✓ Created .gitignore with bale's default exclusion set")

    try:
        git(["add", "-A"], cwd=cwd)
    except subprocess.CalledProcessError as e:
        fail(
            f"git add -A failed (exit {e.returncode}). Inspect the repo "
            f"and re-run `bale pack` after recovering."
        )
    print("  ✓ Staging all files in this directory")

    try:
        git(["commit", "-m", "Initial commit (bale)"], cwd=cwd)
    except subprocess.CalledProcessError as e:
        # Most likely cause: every file in cwd was matched by the new
        # .gitignore (e.g. a directory of nothing but .env files). The
        # spec asks for a real baseline commit, not --allow-empty; fail
        # explicitly so the user understands the directory needs at
        # least one trackable file. The repo is left in the "init'd but
        # uncommitted" state — `bale pack` retried after adding a file
        # will pick up via repo_root and not re-run the walkthrough.
        fail(
            f"initial commit failed (exit {e.returncode}). If the "
            f"directory contains only files matched by the new "
            f".gitignore, add a tracked file (e.g. README.md) and retry. "
            f"The repo is initialized but has no baseline commit yet."
        )
    log("recorded initial commit: 'Initial commit (bale)'")
    print('  ✓ Initial commit: "Initial commit (bale)"')

    print()
    print("Done. Continuing with bale pack...")
    print()
    return cwd


# --- cmd_pack ----------------------------------------------------------------

def cmd_pack(args: argparse.Namespace) -> int:
    from __main__ import (  # lazy — see module docstring
        BALEIGNORE_FILE,
        applied_tags,
        current_branch,
        ensure_bale_gitignored,
        fail,
        git,
        is_valid_slug,
        log,
        next_session_id,
        open_sessions,
        read_session_scope,
        refuse_system_dir,
        register_session,
        repo_root,
        resolve_inbound_path,
        resolved_scope,
        run_hook,
        scope_intersection,
        set_log_file,
    )
    # Sibling-owned entry points come from their owning modules directly
    # (already imported by bin/bale, so these resolve from sys.modules) —
    # __main__ re-exports would make bin/bale keep imports it doesn't
    # itself call, an invitation for a future cleanup to break pack.
    import bale_config  # lazy — see module docstring
    from bale_report import (  # lazy — see module docstring
        emit_json_line,
        enable_json_mode,
        format_pack_json,
        format_summary_block,
        format_tree_position,
        tree_position_rows,
    )
    from bale_validate import validate_request_manifest  # lazy — see module docstring
    # json output mode (v0.2.8): stream discipline engages first, before
    # any line can print — from here on the [bale] logs, prompts, and
    # banners this command produces go to stderr, and stdout is reserved
    # for the one-line report emitted at the summary site below. The mode
    # state and the rendering live in bale_report.
    if args.json:
        enable_json_mode()
    cwd = Path.cwd().resolve()
    refuse_system_dir(cwd, force=args.force)

    # README-flag validation, before anything can prompt (the git-init
    # walkthrough below is interactive) and before the wizard could
    # collect answers a doomed command line would then throw away.
    # Fail-fast: a contradictory or unusable flag combination should
    # cost the user zero keystrokes.
    if args.edit and args.no_edit:
        fail(
            "--edit and --no-edit are contradictory: one forces the "
            "README $EDITOR step, the other suppresses it. Drop one."
        )
    if args.no_readme and (args.readme_file is not None or args.edit):
        fail(
            "--no-readme is contradictory with --readme-file/--edit: one "
            "declares the pack deliberately ships no prose, the others "
            "supply or edit prose. Drop one side."
        )
    if args.edit and not sys.stdin.isatty():
        fail(
            "--edit needs a TTY (it opens $EDITOR); stdin is not one. "
            "For non-interactive packs, supply prose via --readme-file "
            "instead."
        )
    # Resolve the repo root before the README-flag read below: the flag's
    # path resolution consults the merged config, and the project layer of
    # that config lives at the root. This is only the walk-up — the
    # interactive git-init walkthrough stays where it was, after the flag
    # validation, preserving fail-fast (a doomed --readme-file still costs
    # zero keystrokes).
    repo = repo_root(cwd)

    # Read --readme-file up front so a bad path or empty file fails here,
    # not after the wizard/editor. Empty is a hard failure rather than a
    # silent omit: the flag is an explicit request to ship prose, so an
    # empty file means something upstream (a generator, a redirect) went
    # wrong — per the no-silent-skips rule. Deliberate omission is
    # spelled "don't pass the flag". The body is stashed on args for
    # _resolve_readme_body, the same private-attr idiom as _readme_body.
    #
    # Since v0.3.6 the path resolves through the same inbound search paths
    # apply/retry/handoff use for their tarball argument
    # (resolve_inbound_path over apply.search_paths): absolute paths
    # bypass, cwd is tried first, then each configured directory in order,
    # and a bare filename that matches nowhere fails naming every
    # directory consulted. This lets a worker author `--readme-file
    # request-brief.md` without knowing where the architect's downloads
    # land. With no search paths configured, resolution is against cwd —
    # the pre-v0.3.6 behavior, minus one deliberate alignment: the flag
    # argument is no longer expanduser()'d here, matching the resolver's
    # contract that the shell already expanded an unquoted `~` and a
    # quoted one was deliberate. Outside a git repo (the git-init
    # walkthrough case) only the global config layer can exist, so that
    # is what's consulted.
    args._readme_file_body = None
    args._readme_file_path = None
    if args.readme_file is not None:
        if repo is not None:
            pack_cfg = bale_config.merged_config(repo)
        else:
            pack_cfg = bale_config.load_global_config()
        readme_search_paths = bale_config.get_apply_search_paths(pack_cfg)
        readme_path = resolve_inbound_path(
            args.readme_file, cwd, readme_search_paths, kind="readme file"
        )
        try:
            file_body = readme_path.read_text(encoding="utf-8")
        except OSError as e:
            fail(f"could not read --readme-file {args.readme_file!r}: {e}")
        except UnicodeDecodeError as e:
            fail(
                f"--readme-file {args.readme_file!r} is not UTF-8 text: {e}. "
                f"The request README is prose; point the flag at a text file."
            )
        if not file_body.strip():
            fail(
                f"--readme-file {args.readme_file!r} is empty. The flag "
                f"asks bale to ship prose context; omit the flag to pack "
                f"without a README."
            )
        # Placeholder refusal (v0.3.21, board 33 rider): a worker-
        # authored brief scaffolds unfilled slots as lines containing
        # the sentinel `TODO(brief)` (TARBALL.md §3.4, the --readme-file
        # row). A brief that still carries one is a generation or
        # editing step that didn't finish, and shipping it would hand
        # the worker a hole where intent should be — the same
        # no-silent-skips posture as the empty-file refusal above, at
        # the same fail-fast position (read time, before any prompt;
        # fix or regenerate the file, then re-pack — this fires even
        # with --edit, matching the empty-file refusal's timing).
        placeholder_lines = [
            str(i) for i, ln in enumerate(file_body.splitlines(), 1)
            if "TODO(brief)" in ln
        ]
        if placeholder_lines:
            fail(
                f"--readme-file {args.readme_file!r} (resolved to "
                f"{readme_path}) still contains an unfilled placeholder: "
                f"line(s) {', '.join(placeholder_lines)} contain the "
                f"sentinel 'TODO(brief)'. Fill the brief (or regenerate "
                f"it), then re-pack; a brief with unfilled slots must "
                f"not ship."
            )
        args._readme_file_body = file_body
        # Stashed for the pack report's README identity echo (v0.3.21,
        # board 33 rider): the resolved path is the identity the
        # search-path resolution made ambiguous — echoing it (plus the
        # shipped body's first heading and sha256, computed at the
        # report site) is how the operator confirms which brief shipped.
        args._readme_file_path = readme_path

    if repo is None:
        # BALE.md §7.1 step 4 / §10: not in a repo → run the walkthrough.
        # The walkthrough re-applies refuse_system_dir as defense in depth
        # (the constraint that motivated separating it from cmd_pack), then
        # `git init`s here, prompts for any missing git identity, writes a
        # .gitignore with the §6.4 baked-in exclusion set, and records the
        # initial commit. On user decline it prints the spec'd one-liner
        # and exits 0; on accept it returns the new repo root (== cwd).
        repo = git_init_walkthrough(cwd, force=args.force)
    refuse_system_dir(repo, force=args.force)

    # Detached-HEAD refusal (BALE.md §7.1 step 4a). The session's
    # integration target is stamped from current_branch(repo) at the
    # persist step (ADR-0008), and apply hard-refuses a session without
    # the stamp (resolve_target_branch, BALE.md §8.1 step 5). A
    # detached-HEAD pack would therefore create a session doomed to
    # refuse at apply — discovered only after the tarball shipped and a
    # response came back. Fail here instead: in pre-flight, before the
    # wizard can collect answers and before any tarball or session state
    # exists. The git-init walkthrough path above always lands on a
    # branch, so this fires only for a pre-existing detached checkout.
    # No override flag: there is no session state a detached pack could
    # produce that apply would accept.
    pack_branch = current_branch(repo)
    if pack_branch == "HEAD":
        fail(
            "HEAD is detached — bale pack stamps the currently checked-out "
            "branch as the session's integration target (ADR-0008), and a "
            "session packed without that stamp can never be applied. Check "
            "out the branch this session should integrate into, then "
            "re-pack."
        )

    # Tree-position echo (v0.3.31; BALE.md §7.7). Pack says where the
    # tree is at the moment of paste — the current branch and the most
    # recent applied sid (the same fact the status applied row renders,
    # read from the same source, applied_tags) — because a stale
    # re-pasted pack command does its damage exactly when the operator's
    # picture of the tree has fallen one session behind the tree itself.
    # Sited here deliberately: after every earlier pre-flight refusal
    # (reject-early intact — a doomed command still costs zero
    # keystrokes and sees no echo), and before the supersession exchange
    # and the wizard, so the operator sees the position before investing
    # any answers. Pre-sid, so log() reaches the terminal but no session
    # journal exists yet; the end-of-run report (human rows + --json
    # keys, the summary site below) carries the same facts durably.
    # bale_report owns the rendering; this site only gathers and wires.
    # applied_count is deliberately unrendered (the ratified lean: the
    # echo is the latest sid + branch; `bale status` stays the
    # ground-truth consultation surface for the fuller applied row).
    _applied_count, applied_latest = applied_tags(repo)
    log(format_tree_position(branch=pack_branch, applied_latest=applied_latest))

    # Split supersession (v0.3.17, board 26): resolve --supersedes and
    # run its exchange BEFORE the disjointness gate on both paths — the
    # fully-specified path fires the gate in pre-flight just below, and
    # the wizard path defers it to post-wizard, so the one placement
    # that precedes both is here. An accepted exchange closes the named
    # parent (closure_reason superseded-by-split, command "pack",
    # through the shared close_session_with_record sequencing), which
    # clears exactly that one collision; the gate still evaluates
    # against every other open session. The close preceding the §7.4
    # caps means an abort after acceptance leaves the parent closed —
    # accepted (the parent was being abandoned by declared intent), and
    # the idempotent re-run in _resolve_supersession is its repair
    # path.
    superseded_sid, declined_supersession = _resolve_supersession(args, repo)

    # Scope-disjointness gate (BALE.md 7.1 step 5, ADR-0007), read from
    # the ADR-0006 session registry. This replaces the unconditional
    # refusal that stood here: a pack is now admitted alongside open
    # sessions exactly when its declared scope — resolved_scope of its
    # --include set, or [] for a read-only pack (v0.3.15) — is disjoint
    # from every open session's recorded scope. Includes are a
    # deliberately conservative proxy for change scope (a session rarely
    # changes everything it was shown), so the gate can false-positive;
    # the cheap remedy is a narrower --include set or waiting for the
    # intersecting session to close. A default include-everything pack
    # resolves to ["."] and therefore intersects every open session —
    # broad scope and concurrency are mutually exclusive by design; an
    # empty (read-only) scope intersects nothing and is admitted beside
    # anything. With no session open, behavior is unchanged.
    def _run_scope_gate(pack_scope: list) -> Optional[tuple]:
        """Refuse on intersection with any open session's scope; return
        the (scope, open_sids) journal tuple when admitted alongside
        open sessions, None when nothing was open."""
        open_sids = open_sessions(repo)
        if not open_sids:
            return None
        conflicts: list[tuple[str, list[tuple[str, str]]]] = []
        for open_sid in open_sids:
            pairs = scope_intersection(
                pack_scope, read_session_scope(repo, open_sid))
            if pairs:
                conflicts.append((open_sid, pairs))
        if conflicts:
            detail = "; ".join(
                f"{osid} ({', '.join(sorted({f'{a} ~ {b}' for a, b in pairs}))})"
                for osid, pairs in conflicts
            )
            declined_note = ""
            if declined_supersession is not None:
                declined_note = (
                    f" The supersession of {declined_supersession} was "
                    f"declined at the prompt, so it stays open; re-run "
                    f"and accept the prompt to close it as "
                    f"superseded-by-split, or `bale unlock "
                    f"{declined_supersession}` to close it by hand."
                )
            fail(
                f"pack scope intersects {len(conflicts)} open "
                f"session(s): {detail}. Concurrent sessions require "
                f"disjoint scope (ADR-0007). Narrow this pack with "
                f"--include paths disjoint from the open scope(s), apply "
                f"the open session's response first, run `bale unlock` "
                f"if it was abandoned, or re-run with `--supersedes "
                f"<sid>` if this pack splits and supersedes an open "
                f"session (BALE.md §7.2). Note: a pack without "
                f"--include scopes the whole tree and conflicts with "
                f"every open session; a read-only pack (--read-only, "
                f"empty scope) conflicts with none." + declined_note
            )
        # Journaled below, once the session log is open (sid allocation
        # happens further down; an informational line logged here would
        # reach stdout but never the session journal).
        return (pack_scope, list(open_sids))

    # Wizard engagement is decided before the gate runs (v0.3.15): the
    # wizard's session-shape question can turn the pack read-only, which
    # empties its scope, so on the wizard path (without --read-only
    # already deciding the answer) the gate defers to just after the
    # wizard — otherwise a whole-tree provisional scope would refuse a
    # pack the user was about to declare read-only, before the question
    # could be asked. On every path where the scope is already final —
    # fully specified CLI, or --read-only given — the gate fires here,
    # in pre-flight before any prompt, exactly as before.
    wizard_engaged = args.goal is None or args.slug is None
    gate_deferred = wizard_engaged and not args.read_only
    admitted_alongside: Optional[tuple] = None
    checkpoint_scope_admitted = False
    if not gate_deferred:
        _early_scope = [] if args.read_only else resolved_scope(
            list(args.include))
        # Checkpoint blindness gate (v0.3.28, board 6 session C; BALE.md
        # §7.1 step 4b) — before the disjointness gate, so a self-oracle
        # scope is refused ahead of any scope-collision conversation.
        checkpoint_scope_admitted = checkpoint_blindness_preflight(
            repo, _early_scope, allow=args.allow_checkpoint_in_scope)
        admitted_alongside = _run_scope_gate(_early_scope)

    # Wizard entry (BALE.md §7.3). Engaged when either of the required
    # fields (goal positional, --slug) is missing AND stdin is a TTY.
    # The wizard fills in the missing fields plus walks the optionals
    # (session shape, excludes, constraints, out_of_scope), skipping any
    # field already supplied on the command line. README resolution
    # happens just below via _resolve_readme_body on both paths —
    # wizard_engaged tells the resolver whether its lowest-precedence
    # branch (the §7.3 y/N + $EDITOR flow) is on the table.
    if wizard_engaged:
        if not sys.stdin.isatty():
            missing = []
            if args.goal is None:
                missing.append("goal")
            if args.slug is None:
                missing.append("--slug")
            fail(
                f"missing required arg(s) ({', '.join(missing)}) and stdin "
                f"is not a TTY; cannot prompt interactively. Provide them "
                f"on the command line and re-run."
            )
        _wizard_fill_args(args, repo)

    # The pack's ADR-0007 scope, final now on every path: the wizard has
    # run (its session-shape answer may have set args.read_only; it
    # never collects includes), so nothing below changes the inputs. []
    # is the read-only shape — recorded via persist_pack_session further
    # down, read back by the gates as "locks nothing, may land nothing".
    pack_scope = [] if args.read_only else resolved_scope(list(args.include))
    if gate_deferred:
        # Same order as the pre-flight path: blindness gate (v0.3.28,
        # session C) before the disjointness gate, now that the wizard's
        # session-shape answer has finalized the scope.
        checkpoint_scope_admitted = checkpoint_blindness_preflight(
            repo, pack_scope, allow=args.allow_checkpoint_in_scope)
        admitted_alongside = _run_scope_gate(pack_scope)

    # A declined supersession that survives the gate (the parent's scope
    # happened to be disjoint from this pack's) still refuses: the pack
    # was invoked to supersede, nothing closed, and no lineage would be
    # stamped — proceeding would silently do something materially
    # different from what --supersedes declared. On the wizard path
    # _resolve_supersession already refused at the decline, before any
    # prompt could collect throwaway answers.
    if declined_supersession is not None:
        fail(
            f"supersession of {declined_supersession} was declined and "
            f"its scope does not collide with this pack, but a "
            f"--supersedes pack that closes nothing and stamps no "
            f"lineage would not be the pack you asked for. Re-run and "
            f"accept the prompt, `bale unlock {declined_supersession}` "
            f"to close it by hand, or drop --supersedes."
        )

    # The read-only sweep (v0.3.21, board 33). Placed here because the
    # session shape is final on every path only now (the wizard's
    # session-shape answer can turn the pack read-only), and pre-sid
    # like the supersession exchange — its close events reach stdout
    # only, and the outcome is journaled into the child's session log
    # once it opens. Only a read-only pack sweeps: worker (scoped)
    # packs and apply never trigger it, and `bale unlock` remains the
    # no-successor escape hatch. Semantics — accept-default prompt,
    # piped decline, HOLD skip — live in _run_readonly_sweep.
    swept_sids: list[str] = []
    if args.read_only:
        swept_sids = _run_readonly_sweep(repo)

    # README resolution (BALE.md §7.3; precedence lives in the resolver's
    # docstring). Runs after the wizard so a wizard-collected goal /
    # constraints / out_of_scope can seed the $EDITOR scaffold, and so
    # the user-visible prompt order matches the pre-v0.2.4 wizard, where
    # README was the last step. _readme_body rides on args to the build
    # step downstream, exactly as before.
    args._readme_body = _resolve_readme_body(args, wizard_engaged=wizard_engaged)

    # No-readme guard (v0.3.8, board 3): a pack shipping no prose is
    # either deliberate or an oversight, and the two must not look the
    # same. --no-readme is the deliberate spelling; a wizard-path user
    # who answered 'n' at the README prompt (or saved an empty buffer)
    # made the choice interactively. What remains is the un-asked case:
    # on a TTY, warn — the user is watching and can Ctrl-C to repack;
    # piped, refuse — nobody reads a stderr warning in automation, the
    # same posture as the piped soft-breach refusal above. The wizard
    # exemption is scoped to paths where a prompt actually ran:
    # wizard_engaged with --no-edit suppresses the prompt, so that
    # combination is NOT exempt.
    if args._readme_body is None:
        if args.no_readme:
            log("packing without a README (--no-readme)")
        elif wizard_engaged and not args.no_edit:
            log("packing without a README (declined at the wizard prompt)")
        elif sys.stdin.isatty():
            print(
                "[bale] warning: packing without a README — the request "
                "ships only the manifest's structured fields. Supply prose "
                "via --readme-file or --edit, or pass --no-readme to "
                "acknowledge and silence this.",
                file=sys.stderr,
            )
        else:
            fail(
                "packing without a README and without --no-readme: stdin "
                "is not a TTY, so the warning would be read by nobody. "
                "Supply prose via --readme-file, or pass --no-readme to "
                "declare the omission deliberate."
            )

    # README identity echo (v0.3.21, board 33 rider; evidence 45/47):
    # when a README ships, the pack report echoes its identity — the
    # resolved path, the first heading line, and the sha256 — because
    # path + heading alone proved insufficient (two revisions of a
    # brief share both; the hash is the identity). The hash is computed
    # over the exact bytes build_request_tarball ships (its trailing-
    # newline normalization mirrored here), so the echoed value matches
    # `sha256sum` of the README.md inside the tarball. The path is the
    # --readme-file resolution when that flag sourced the prose (the
    # search-path ambiguity the echo exists to close), and an honest
    # "(authored in $EDITOR)" when the wizard/--edit path authored it
    # with no file involved.
    readme_echo_path: Optional[str] = None
    readme_echo_heading: Optional[str] = None
    readme_echo_sha256: Optional[str] = None
    if args._readme_body is not None:
        shipped_text = (args._readme_body
                        if args._readme_body.endswith("\n")
                        else args._readme_body + "\n")
        readme_echo_sha256 = hashlib.sha256(
            shipped_text.encode("utf-8")).hexdigest()
        readme_echo_heading = next(
            (ln.strip() for ln in shipped_text.splitlines()
             if ln.lstrip().startswith("#")),
            "(no heading)",
        )
        readme_echo_path = (str(args._readme_file_path)
                            if args._readme_file_path is not None
                            else "(authored in $EDITOR)")

    # Input validation.
    if not is_valid_slug(args.slug):
        fail(
            f"--slug must be kebab-case (lowercase letters, digits, "
            f"hyphens; no leading/trailing/double hyphens): got {args.slug!r}"
        )
    goal = args.goal.strip()
    if not goal:
        fail("goal must be non-empty.")
    for inc in args.include:
        if not (repo / inc).exists():
            fail(f"--include path does not exist: {inc}")

    # Pack threshold caps (BALE.md §7.4). The --max-* flags override only
    # the hard caps; the soft caps stay at PACK_MAX_*_SOFT so the prompt
    # still fires at the same scope-sanity threshold regardless of how the
    # user tuned the hard refusal point.
    caps_kwargs: dict = {}
    if args.max_files is not None:
        if args.max_files < 1:
            fail(f"--max-files must be >= 1; got {args.max_files}")
        caps_kwargs["max_files_hard"] = args.max_files
    if args.max_size is not None:
        try:
            caps_kwargs["max_size_hard"] = parse_size_arg(args.max_size)
        except ValueError as e:
            fail(str(e))
    if args.max_depth is not None:
        if args.max_depth < 0:
            fail(f"--max-depth must be >= 0; got {args.max_depth}")
        caps_kwargs["max_depth"] = args.max_depth
    caps = PackCaps(**caps_kwargs)

    # Ensure .bale/ is in .gitignore before we start writing under it. If we
    # had to modify .gitignore and the tree is otherwise clean, auto-commit
    # the change so `bale apply` doesn't trip on the dirty tree later. If
    # the tree is dirty for other reasons, just warn — the user is mid-WIP
    # and we shouldn't entangle our setup commit with their work.
    gitignore_changed = ensure_bale_gitignored(repo)
    if gitignore_changed:
        r = git(["status", "--porcelain"], cwd=repo)
        other_dirty = [
            ln for ln in r.stdout.splitlines()
            if ln and not ln.endswith(" .gitignore")
        ]
        if other_dirty:
            log("note: working tree has other uncommitted changes; "
                ".gitignore was modified but not auto-committed. "
                "Commit it before `bale apply` or apply will refuse.")
        else:
            git(["add", ".gitignore"], cwd=repo)
            git(["commit", "-m", "bale: ignore .bale/"], cwd=repo)
            log("auto-committed the .gitignore change")

    # Build the .baleignore + session-excludes matcher (BALE.md §6.4).
    # None when the repo has no .baleignore AND the session has no extra
    # excludes — walk_for_pack skips the per-path matcher check in that
    # case. The matcher is rebuilt on each iteration of the soft-cap
    # [e] loop below, since adding patterns mid-prompt has to take
    # effect on the re-walk.
    session_excludes: list[str] = list(args.exclude)
    matcher = build_pack_matcher(repo, session_excludes)

    # Walk + project, with the soft-breach edit-excludes loop wrapped
    # around it. The loop's body is:
    #   1. walk_for_pack with the current matcher.
    #   2. Hard breach → refuse (or --force-log-and-proceed).
    #   3. Soft breach → prompt y/e/n.
    #      - y: break out of loop, proceed.
    #      - e: collect more session-exclude patterns, rebuild matcher,
    #           re-walk (this iteration).
    #      - n: abort.
    #   4. No breach → break out of loop, proceed.
    # The loop terminates either via `break` (continue/abort decision
    # made) or via `fail()` (hard breach without --force, piped-mode soft
    # breach, or user abort). Piped mode never enters [e] — a soft breach
    # without a TTY fails outright (v0.2.4), since no prompt can run and
    # warn-and-proceed defeats the cap exactly where nobody is watching.
    # --force bypasses the prompt and the piped refusal entirely.
    while True:
        projection = walk_for_pack(
            repo, args.include, caps=caps, force=args.force, matcher=matcher,
        )
        files = projection.files
        if not files:
            fail(
                "no files would be included after exclusions; widen "
                "--include or relax .baleignore / --exclude patterns."
            )

        # Breach handling (BALE.md §7.4).
        # Order: hard breach refuses (or --force bypasses with a FORCE log);
        # then soft breach prompts (TTY) or warns (piped) — unless --force,
        # which logs the bypass and proceeds.
        if projection.hard_breach is not None:
            # walk_for_pack only sets hard_breach when force=False; this
            # branch is unreachable under --force by construction.
            sys.stderr.write(format_projection_block(projection) + "\n\n")
            fail(
                f"hard threshold breach: {projection.hard_breach}. "
                f"Walk stopped at the breach (BALE.md §7.4). Re-run with the "
                f"appropriate --max-* flag to raise the cap, or with --force "
                f"to bypass all caps."
            )
        elif args.force:
            # --force is active. Name every cap that would have tripped so the
            # audit log records exactly what was bypassed. hard_breaches_seen
            # is populated even though walk_for_pack didn't short-circuit, and
            # soft_breaches is populated only when no hard breach is seen. An
            # empty union means the user passed --force but nothing tripped —
            # still log the event so the audit trail records the user's intent.
            # The home-dir override (if it fired) was already logged inside
            # refuse_system_dir; this line covers the threshold-cap side.
            all_bypassed = projection.hard_breaches_seen + projection.soft_breaches
            if all_bypassed:
                log(
                    "bypassing threshold breach(es): "
                    + "; ".join(all_bypassed)
                    + f". Final scope: {len(files):,} files, "
                    + f"{format_bytes(projection.total_bytes)}, "
                    + f"max depth {projection.max_depth_seen}.",
                    force=True,
                )
            else:
                log(
                    f"--force active; no thresholds tripped. Final scope: "
                    f"{len(files):,} files, "
                    f"{format_bytes(projection.total_bytes)}, "
                    f"max depth {projection.max_depth_seen}.",
                    force=True,
                )
            break
        elif projection.soft_breaches:
            # Soft breach without --force. Print the projection block to stderr
            # in both modes — it's diagnostic context, not the pack's output —
            # then either prompt (TTY, y/e/n) or warn-and-proceed (piped).
            sys.stderr.write(format_projection_block(projection) + "\n\n")
            sys.stderr.write(
                "Soft threshold breach: "
                + "; ".join(projection.soft_breaches)
                + ".\n"
            )
            if sys.stdin.isatty():
                # [y] continue, [e] edit excludes, [n] abort. Default is
                # abort on bare Enter so an accidental keystroke doesn't
                # pack a 200MB tarball. The prompt repeats on unrecognized
                # input rather than picking a default — better to ask
                # again than to mis-route on a typo.
                action = _prompt_soft_breach_action()
                if action == "n":
                    # No sid allocated yet, no log file open — clean abort.
                    print("[bale] aborted at threshold prompt",
                          file=sys.stderr)
                    return 1
                if action == "e":
                    # Collect more session-only patterns, rebuild matcher,
                    # re-walk. The new patterns stack on top of whatever
                    # was already in session_excludes — pressing `e`
                    # repeatedly is additive, not replace-all.
                    print()
                    print("Adding session-only exclusions. These do NOT")
                    print("modify .baleignore (use `bale config init`")
                    print("for that). Patterns are gitignore-style; one")
                    print("per line, blank to finish:")
                    additions = _wizard_input_list("> ")
                    if not additions:
                        # User pressed Enter immediately — no new patterns
                        # to apply. Re-walk would be identical; just
                        # re-prompt for the breach decision.
                        sys.stderr.write(
                            "[bale] no patterns added; re-prompting.\n"
                        )
                        continue
                    session_excludes.extend(additions)
                    matcher = build_pack_matcher(repo, session_excludes)
                    print()
                    print(f"Added {len(additions)} pattern(s); re-walking...")
                    print()
                    continue
                # action == "y" — proceed past the breach.
                break
            else:
                # Piped mode (v0.2.4): refuse rather than warn-and-proceed.
                # A soft cap exists to make a human look at the scope before
                # packing; in automation there is no human at the prompt and
                # a stderr warning is read by nobody, so proceeding silently
                # ships exactly the oversized pack the cap exists to catch.
                # The projection block is already on stderr above. Escape
                # hatches: narrow with --exclude / .baleignore, or pass
                # --force to proceed at this scope deliberately (which is
                # logged as a FORCE event and never reaches this branch).
                fail(
                    "soft threshold breach: "
                    + "; ".join(projection.soft_breaches)
                    + ". stdin is not a TTY, so the [y]/[e]/[n] prompt "
                    "cannot run and bale will not proceed past a scope "
                    "warning unattended. Narrow the pack with --exclude "
                    "or .baleignore, or re-run with --force to proceed "
                    "at this scope deliberately."
                )
        else:
            # No breach. Proceed.
            break

    # `.baleignore` is force-included in context/ when it exists. The
    # filter chain above would have skipped it only if a baked-in or
    # secret pattern matched (none do — `.baleignore` isn't a secret and
    # isn't under a baked-in excluded dir), but the file may not be
    # tracked yet on a fresh repo, in which case `git ls-files
    # --exclude-standard` already picks it up via the --others branch.
    # The append-if-missing here is defense in depth for the case where
    # a user adds `.baleignore` to their `.gitignore` (which would be
    # odd, but is permitted and Claude shouldn't be blind to the file
    # just because its owning user chose to gitignore it). Inserted as
    # a relative path so it lines up with the other entries the walker
    # produced, and only when it actually exists on disk.
    if (repo / BALEIGNORE_FILE).is_file() and BALEIGNORE_FILE not in files:
        files = sorted(files + [BALEIGNORE_FILE])
        log(f"force-included {BALEIGNORE_FILE} in context (was not in "
            f"git-tracked set)")

    log(f"selected {len(files)} files for context/ "
        f"({format_bytes(projection.total_bytes)}, "
        f"max depth {projection.max_depth_seen})"
        + (f" [session excludes: {len(session_excludes)}]"
           if session_excludes else ""))

    # Allocate session ID and switch logging to the per-session file. The
    # set_log_file() call drains any buffered --force lines from
    # refuse_system_dir / the threshold check above into the new log file,
    # so the session journal has the override events even though they
    # preceded sid allocation.
    sid = next_session_id(repo, args.slug)
    log_path = repo / ".bale" / "logs" / f"{sid}.log"
    set_log_file(log_path)
    log(f"session id: {sid}")
    if admitted_alongside is not None:
        gate_scope, gate_open_sids = admitted_alongside
        log(f"scope-disjointness gate passed (ADR-0007): pack scope "
            f"({', '.join(gate_scope)}) is disjoint from "
            f"{len(gate_open_sids)} open session(s): "
            f"{', '.join(gate_open_sids)}")
        log("note: revert/retry/unlock/handoff resolve the session the "
            "compatibility pointer names (the most recently opened) "
            "while several are open; sid disambiguation for them is "
            "deferred (ADR-0006)")
    if superseded_sid is not None:
        # Journal the supersession into the child's session log — the
        # exchange ran pre-sid (its lines reached stdout only); the
        # child's journal is where a later reader traces this pack, and
        # the parent's telemetry record carries the durable closure.
        log(f"supersedes {superseded_sid}: closed as superseded-by-split "
            f"(closure record at claude/telemetry/{superseded_sid}.json); "
            f"lineage stamped in depends_on.superseded_session")
        # Reverse lineage (v0.3.23, board 5 D4): stamp superseded_by on
        # the parent's closure attempt, now that the child sid exists.
        # The exchange wrote that attempt pre-sid, so this is the same
        # single writer (pack) enriching the closure it already
        # recorded; the idempotent re-run of an aborted supersession
        # pack re-stamps the same attempt in place — the completing
        # pack's child sid wins, and the attempt count never grows.
        # Best-effort like every telemetry write.
        from bale_report import stamp_superseded_by  # lazy — see module docstring
        stamp_rel = stamp_superseded_by(repo, superseded_sid, sid)
        if stamp_rel:
            log(f"supersedes {superseded_sid}: reverse lineage "
                f"superseded_by={sid} stamped on the closure attempt "
                f"({stamp_rel})")
    if swept_sids:
        # Same journaling rationale for the read-only sweep (v0.3.21):
        # the close events ran pre-sid; the durable closure lives in
        # each swept sid's telemetry record.
        log(f"read-only sweep: closed {', '.join(swept_sids)} as "
            f"closed-read-only (closure record(s) under claude/telemetry/)")

    # Manifest, with the pack-time provenance stamp (v0.3.8, B1):
    # bale_version + contract-doc hashes + packer (--packer > [identity].
    # packer > "unconfigured") + work_class from --work-class. Since
    # v0.3.15 the flag's parser default is None so the wizard can tell
    # "unspecified" from an explicit choice; resolution here is: the
    # flag or wizard answer > 'meta' for a read-only session (inferred —
    # a session that lands nothing is doing orchestration/discussion/
    # audit work; logged so the inference is auditable, overridable via
    # --work-class) > 'mixed', the pre-v0.3.15 default, unchanged for
    # every non-read-only path that never answered.
    work_class = args.work_class
    if work_class is None:
        if args.read_only:
            work_class = "meta"
            log("work_class inferred 'meta' for the read-only session "
                "shape (no --work-class given; pass the flag to override)")
        else:
            work_class = "mixed"
    if args.read_only:
        log("read-only session shape (v0.3.15): recorded scope is empty — "
            "locks nothing (siblings pack freely), may land nothing (the "
            "own-scope drift gate refuses every changes[] path this "
            "session ships). Close-out (board 33): the next read-only "
            "pack offers to close this session, or run `bale unlock` now")
    provenance = build_provenance_block(
        repo, packer_flag=args.packer, work_class=work_class,
        checkpoint_scope_admitted=checkpoint_scope_admitted,
    )
    log(f"provenance: packer={provenance['packer']!r} "
        f"work_class={provenance['work_class']!r} "
        f"bale_version={provenance['bale_version']}")
    manifest = build_request_manifest(
        sid=sid,
        project_name=repo.name,
        goal=goal,
        constraints=list(args.constraint),
        out_of_scope=list(args.out_of_scope),
        expects_probe=args.expects_probe,
        context_paths=files,
        depends_on={
            "previous_response": None,
            "previous_probe": None,
            # The child→parent lineage stamp (v0.3.17, board 26): the
            # sid this pack closed as superseded-by-split (or accepted
            # as already so closed on the idempotent re-run), null on
            # every non-supersession pack. One-directional by design:
            # the child sid did not exist when the parent closed, so
            # the parent's closure record carries no successor pointer
            # — the manifest field here is the lineage's single home.
            "superseded_session": superseded_sid,
        },
        provenance=provenance,
        # The board-33 scope stamp (v0.3.21): the same pack_scope value
        # persist_pack_session records below — one source, never a
        # re-derivation. [] for a read-only pack.
        resolved_scope=pack_scope,
    )

    # Pack pre-flight schema check (BALE.md §11 row 6, request side). bale
    # builds this manifest itself, so a failure here means a construction bug
    # in build_request_manifest — defense in depth (CODE.md §8.2) catching it
    # before the tarball ships rather than letting Claude's session be the
    # first to notice. Cheap, and it keeps request and response manifests on
    # the same enforced-shape footing.
    validate_request_manifest(manifest)
    log("request manifest schema validation passed")

    # Build tarball. Pack's context is just repo-relative paths picked by
    # the filter chain; bale handoff builds (rel, source) tuples differently
    # since handoff.md doesn't live in the repo. The wizard's optional
    # README, when the user opted in via the §7.3 prompt, rides along here.
    tarball_path = repo / ".bale" / "outbox" / f"request-{sid}.tar.gz"
    context_entries = [(rel, repo / rel) for rel in files]
    try:
        build_request_tarball(
            sid, context_entries, manifest, tarball_path,
            readme_body=args._readme_body,
        )
    except Exception as e:
        if tarball_path.exists():
            tarball_path.unlink()
        fail(f"failed to build request tarball: {e}")
    log(f"wrote {tarball_path}")

    # Persist session, then open it in the registry LAST (BALE.md 7.6 —
    # same ordering rationale as the old lock: a pack that fails earlier
    # leaves no open session and the user just retries). register_session
    # writes the ADR-0006 open marker plus the current_session
    # compatibility pointer in one step.
    persist_pack_session(repo, sid, manifest, scope=pack_scope,
                         origin_branch=current_branch(repo))
    register_session(repo, sid)
    log(f"opened session {sid} in the registry (lock pointer written)")

    # post_pack hook. Silent no-op when not configured. Fires after the
    # tarball is on disk AND the session is locked — i.e. after every
    # state change pack performs has succeeded, mirroring the
    # post_apply_pass placement (after merge + tag + lock-clear). A
    # hook-side failure logs but does not unwind pack; the tarball is
    # already where the user needs it.
    #
    # merged_config layers global under project so a single config call covers
    # both `<install>/user/bale.toml` and `<repo>/bale.toml`.
    run_hook(repo, bale_config.merged_config(repo), "post_pack", sid)

    # User-facing summary. --json swaps the format of this one report
    # (everything above ran identically): pass-through to
    # bale_report.format_pack_json, which owns the rendering and the stable
    # key contract (outcome, sid, tarball, log, session_dir, context_files),
    # emitted via emit_json_line so it reaches the real stdout — under json
    # mode's stream discipline (v0.2.8) every other line this command
    # printed went to stderr, making the report the only stdout line.
    # Otherwise the shared formatter, so pack ends on the same shape as
    # apply/handoff; the actionable next step is the trailer, so it is the
    # last thing printed.
    if args.json:
        emit_json_line(format_pack_json(
            sid=sid,
            tarball=tarball_path,
            log_path=log_path,
            session_dir=repo / ".bale" / "sessions" / sid,
            context_files=len(files),
            readme_path=readme_echo_path,
            readme_heading=readme_echo_heading,
            readme_sha256=readme_echo_sha256,
            branch=pack_branch,
            applied_latest=applied_latest,
        ))
    else:
        rows = [
            ("session id", sid),
            ("tarball", str(tarball_path)),
            ("files", f"{len(files)} in context/"),
        ]
        if readme_echo_sha256 is not None:
            # The board-33 identity echo: path, first heading, sha256
            # of the shipped README.md (see the computation above).
            rows += [
                ("readme", readme_echo_path),
                ("readme heading", readme_echo_heading),
                ("readme sha256", readme_echo_sha256),
            ]
        # The tree-position echo's report half (v0.3.31; BALE.md §7.7):
        # the same facts the pre-flight banner line named, restated in
        # the block the operator reads last — the banner is visibility
        # at paste time, these rows are the durable record beside the
        # sid. bale_report owns the rendering (tree_position_rows).
        rows += tree_position_rows(
            branch=pack_branch, applied_latest=applied_latest)
        trailer = [
            "Send the tarball to Claude. When the response tarball comes back,",
            "run: bale apply <response-tarball>",
        ]
        if args.read_only:
            # The open banner names its own close-out (board 33,
            # v0.3.21) — the every-command-names-its-successor
            # contract. Both paths: the sweep on the next read-only
            # pack, or unlock now.
            trailer += [
                "",
                f"Read-only session close-out: the next read-only pack "
                f"offers to close {sid},",
                f"or run: bale unlock {sid}",
            ]
        print(format_summary_block(
            rows,
            trailer=trailer,
        ))
    return 0
