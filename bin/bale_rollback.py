"""bale_rollback — the `bale rollback` command (BALE.md §9.2).

The fourth sibling module after `bale_config` (v0.0.4), `bale_validate`
(v0.1.2), and `bale_staging` (v0.1.3). Unlike those three, this module is
not an extraction of code that previously lived in `bin/bale` — it is the
net-new v0.2 rollback feature, placed in its own module from the start so
`bin/bale` (already ~4200 lines) gains only the CLI wiring rather than a
fresh command cluster. See the response notes for the layout rationale and
the alternative (a Rollback section inside `bin/bale`, next to Revert).

`bale rollback` is the third "undo" verb. The other two live in `bin/bale`
and operate on different git states (BALE.md §9.4):
  - `bale revert <sid>`   — discards a *staged, not-yet-merged* bale branch.
  - `bale unlock`         — clears an abandoned lock, no git side effect.
  - `bale rollback [sid]` — undoes an *applied (merged)* bale via
                            `git revert`, history-preserving and itself
                            reversible with `--undo`.

The durable record rollback operates on is the `applied/<sid>` tag that the
apply walkthrough's merge path writes (bin/bale §18): a `--no-ff` merge
commit on the origin branch, tagged `applied/<sid>`. Its second parent
(`<merge>^2`) is the bale branch tip whose subject is `[bale <sid>]
<summary>` — that's where the original summary is recovered for the amended
rollback commit message.

Tag lifecycle for one applied session:
    applied/<sid>      written by apply's merge path
      → rollback       git revert -m 1 <merge>, amend msg, tag reverted/<sid>
      → rollback --undo  git revert <revert-commit>, amend, tag re-applied/<sid>

Each clean-success path also appends an attempt to the sid's telemetry
record (v0.3.18, BALE.md §9.2/§8.9): outcome `rolled-back` / `re-applied`,
command `rollback` — the same paths that write the tags, and only those.
The conflict and empty-revert paths record nothing for the same reason
they tag nothing: a record would claim a rollback that hasn't happened.

Public surface is the single `cmd_rollback(args)` entry point; `bin/bale`
does `from bale_rollback import cmd_rollback` and wires it to the CLI. Shared
helpers (`log`, `fail`, `git`, `repo_root`, `refuse_system_dir`,
`current_branch`, `working_tree_clean`, `set_log_file`) are imported lazily
from `__main__` (i.e. `bin/bale`) inside the functions that use them, the
same idiom `bale_config` / `bale_validate` / `bale_staging` use. No path
constants are recomputed here — everything derives from the repo argument.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Tag naming. The three tags that track one applied session through rollback.
# Kept as constants so the prefixes are defined once and the summary-prefix
# stripper below stays in sync with what apply and rollback actually write.
# ---------------------------------------------------------------------------

TAG_APPLIED = "applied"
TAG_REVERTED = "reverted"
TAG_REAPPLIED = "re-applied"

# Commit-subject prefixes, in the order the summary stripper tries them.
# Longest/most-specific first so `[bale rollback <sid> --undo] ` is matched
# before `[bale rollback <sid>] ` and that before `[bale <sid>] `.
# `[bale <sid>] <summary>`            — apply's change commit (bin/bale §17).
# `[bale rollback <sid>] <summary>`   — what a rollback amends its revert to.
# `[bale rollback <sid> --undo] ...`  — what an --undo amends its revert to.
def _subject_prefixes(sid: str) -> tuple[str, ...]:
    return (
        f"[bale rollback {sid} --undo] ",
        f"[bale rollback {sid}] ",
        f"[bale {sid}] ",
    )


# ---------------------------------------------------------------------------
# git query helpers (read-only). Each lazily imports the shared `git` wrapper.
# ---------------------------------------------------------------------------

def _tag_exists(repo: Path, tag: str) -> bool:
    """True if a tag ref named `tag` exists in the repo."""
    from __main__ import git
    r = git(["rev-parse", "--verify", "--quiet", f"refs/tags/{tag}"],
            cwd=repo, check=False)
    return r.returncode == 0


def _tag_commit(repo: Path, tag: str) -> str:
    """Resolve a tag to the commit SHA it points at (peeling annotated tags)."""
    from __main__ import git
    r = git(["rev-parse", f"refs/tags/{tag}^{{commit}}"], cwd=repo)
    return r.stdout.strip()


def _is_merge_commit(repo: Path, commit: str) -> bool:
    """True if `commit` has a second parent (i.e. it is a merge commit).

    apply writes `applied/<sid>` on a `--no-ff` merge, so this is normally
    True for rollback targets; BALE.md §9.2 step 2 nonetheless handles a
    plain commit, so detection stays explicit rather than assumed.
    """
    from __main__ import git
    r = git(["rev-parse", "--verify", "--quiet", f"{commit}^2"],
            cwd=repo, check=False)
    return r.returncode == 0


def _commit_subject(repo: Path, commit: str) -> str:
    """Return the one-line subject of `commit`."""
    from __main__ import git
    r = git(["log", "-1", "--format=%s", commit], cwd=repo)
    return r.stdout.strip()


def _reachable_tags(repo: Path, prefix: str) -> list[tuple[str, str]]:
    """`(sid, tag)` pairs for `<prefix>/*` tags reachable from HEAD, **most
    recent first by history position**. BALE.md §9.2 step 1: rollback only
    considers tags merged into the current history, so a tag from an unrelated
    branch can't be rolled back from here.

    Ordering is by the tagged commit's position walking back from HEAD (the
    commit nearest HEAD is "most recent"), not by tagger/commit *date*. Dates
    tie on same-second commits and can lie under rebase, and picking the wrong
    session to roll back is a silent, high-cost error (CODE.md §8.2), so the
    unambiguous topological position is the key. The spec's "by commit date"
    is the normal-case equivalent of this; this is the same answer made robust
    to ties.
    """
    from __main__ import git
    r = git(["tag", "--list", f"{prefix}/*", "--merged", "HEAD"], cwd=repo)
    names = [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]
    if not names:
        return []
    # commit SHA -> distance from HEAD (0 = HEAD, larger = older).
    rl = git(["rev-list", "HEAD"], cwd=repo)
    order = {sha.strip(): i for i, sha in enumerate(rl.stdout.splitlines())}
    unreachable = len(order)  # sort any non-resolving tag last, deterministically
    decorated: list[tuple[int, str, str]] = []
    for name in names:
        commit = _tag_commit(repo, name)
        decorated.append((order.get(commit, unreachable), name[len(prefix) + 1:], name))
    decorated.sort(key=lambda t: t[0])
    return [(sid, name) for _idx, sid, name in decorated]


def _revert_in_progress(repo: Path) -> bool:
    """True if a `git revert` is paused mid-flight (REVERT_HEAD present).

    Distinguishes a real merge conflict (revert in progress) from an empty
    revert that git declines outright (e.g. re-reverting an already-reverted
    commit), which exits non-zero but leaves nothing in progress.
    """
    from __main__ import git
    r = git(["rev-parse", "-q", "--verify", "REVERT_HEAD"], cwd=repo, check=False)
    return r.returncode == 0


def _extract_summary(subject: str, sid: str) -> str:
    """Recover the original session summary from a commit subject.

    Strips whichever known `[bale ...]` prefix the subject carries for this
    sid. Falls back to the subject verbatim if none match — never returns an
    empty string, because a silent-empty commit message would be a bug
    (CLAUDE.md §6: silent skips are bugs), not a tidy default.
    """
    for prefix in _subject_prefixes(sid):
        if subject.startswith(prefix):
            remainder = subject[len(prefix):].strip()
            return remainder or subject
    return subject


def _conflicted_paths(repo: Path) -> list[str]:
    """Unmerged paths left by an in-progress revert (diff-filter=U)."""
    from __main__ import git
    r = git(["diff", "--name-only", "--diff-filter=U"], cwd=repo, check=False)
    return [ln.strip() for ln in r.stdout.splitlines() if ln.strip()]


# ---------------------------------------------------------------------------
# Dirty-tree guard. BALE.md §9.2 step 3: refuse on a dirty tree; `--stash`
# stashes before and pops after; the global `--force` also bypasses (§5.4).
# Returns a "stash token" the caller pops after a successful revert, or None.
# ---------------------------------------------------------------------------

# The one directory whose *untracked* entries the guard disregards
# wholesale (v0.3.23, board 5 D5). A prefix, not a pattern: exactly the
# tracked-side telemetry home BALE.md §8.9 writes to.
_TELEMETRY_PREFIX = "claude/telemetry/"


def _is_bale_archive_artifact(path: str, archive_dir: Optional[str]) -> bool:
    """True when `path` has exactly the shape the [apply].archive_dir
    mechanism writes (v0.3.30; BALE.md §8.8): `<archive_dir>/<sid>/<name>`
    where <sid> parses as a real session id and <name> is one of the
    archivable response artifacts.

    Deliberately shape-matched rather than a whole-prefix disregard like
    `_TELEMETRY_PREFIX` above: the telemetry home is a fixed path bale
    owns outright, while archive_dir is user-configured and may sit in a
    directory the user also works in — disregarding only what bale
    itself demonstrably wrote keeps the guard's conservatism. `None`
    archive_dir (the key unset) matches nothing.
    """
    if not archive_dir:
        return False
    prefix = archive_dir.rstrip("/") + "/"
    if not path.startswith(prefix):
        return False
    rest = path[len(prefix):]
    parts = rest.split("/")
    if len(parts) != 2:
        return False
    sid, name = parts
    # Lazy sibling imports (module docstring idiom): the artifact tuple's
    # one home is the apply module that writes the copies, and the sid
    # grammar's one home is bin/bale's parser.
    import bale_apply
    if name not in bale_apply.ARCHIVABLE_RESPONSE_ARTIFACTS:
        return False
    from __main__ import parse_session_id
    try:
        parse_session_id(sid)
    except ValueError:
        return False
    return True


def _split_untracked_disregarded(
        status: str, archive_dir: Optional[str]) -> tuple[list[str], list[str]]:
    """Split `git status --porcelain` output for the guard's judgment.

    Takes `git status --porcelain -uall` output — `-uall` so an
    entirely-untracked directory is enumerated file by file instead of
    collapsing to one `?? claude/` entry the tests below could
    not judge (the first record bale ever writes creates exactly that
    state). Returns (disregarded_paths, remainder_lines):
    `disregarded_paths` are the paths of `?? ` (untracked) entries that
    bale itself left behind — under `claude/telemetry/` (v0.3.23), or
    matching the [apply].archive_dir artifact shape
    (`_is_bale_archive_artifact`, v0.3.30) — and `remainder_lines` is
    every other non-blank status line verbatim.
    Only the untracked marker qualifies; a modified/added/deleted tracked
    file under the same locations stays in the remainder (a real conflict
    surface for `git revert`). Porcelain quotes paths containing special
    characters; the surrounding quotes are stripped before the tests
    so such a path is still judged by its real location.
    """
    disregarded: list[str] = []
    remainder: list[str] = []
    for line in status.splitlines():
        if not line.strip():
            continue
        if line.startswith("?? "):
            path = line[3:].strip()
            if path.startswith('"') and path.endswith('"') and len(path) >= 2:
                path = path[1:-1]
            if (path.startswith(_TELEMETRY_PREFIX)
                    or path == _TELEMETRY_PREFIX.rstrip("/")
                    or path == _TELEMETRY_PREFIX):
                disregarded.append(path)
                continue
            if _is_bale_archive_artifact(path, archive_dir):
                disregarded.append(path)
                continue
        remainder.append(line)
    return disregarded, remainder

def _guard_dirty_tree(repo: Path, *, stash: bool, force: bool) -> Optional[str]:
    """Ensure the tree is clean enough to run `git revert`.

    Clean tree → returns None (nothing stashed). Untracked paths that
    bale itself left behind are disregarded when judging cleanliness
    (BALE.md §9.2 step 3): the telemetry record under
    `claude/telemetry/` (v0.3.23, board 5 D5), and — when the project
    configures [apply].archive_dir — response-artifact copies matching
    exactly the `<archive_dir>/<sid>/<artifact>` shape apply writes at
    merge (v0.3.30; shape test in `_is_bale_archive_artifact`, which
    keeps the carve-out narrower than the telemetry prefix because
    archive_dir is user-configured ground). The rationale is the same
    for both: bale wrote them and leaves them uncommitted by design, so
    refusing on them is friction with no protective value — `git
    revert` rewrites tracked content only, and the one collision case
    (a revert that would materialize a file at an untracked path) is
    refused loudly by git itself. When those entries were the only
    dirt, the guard proceeds with a log line naming them. A *modified
    tracked* file at the same locations still refuses — that is a real
    conflict surface — and so does any other dirt, unchanged:
      - `--stash` → stash (including untracked — the disregarded
        paths ride along, unchanged behavior) and return the
        stash ref so the caller can pop it after the revert lands.
      - `--force` → log the bypass prominently and proceed without stashing
        (the user owns the consequences of reverting onto dirty state).
      - neither  → fail() with a message pointing at `--stash`.
    """
    from __main__ import log, fail, git, working_tree_clean
    import bale_config  # lazy — sibling module, loaded by bin/bale
    clean, status = working_tree_clean(repo)
    if clean:
        return None
    # Judge on the -uall enumeration (see _split_untracked_disregarded);
    # the refusal message below keeps the familiar collapsed `status`.
    # The archive_dir read goes through the strict typed accessor: a
    # malformed key is fatal here exactly as it is at apply — a typo
    # must not silently change which paths the guard disregards.
    archive_dir = bale_config.get_apply_archive_dir(
        bale_config.merged_config(repo))
    r = git(["status", "--porcelain", "-uall"], cwd=repo)
    disregarded, remainder = _split_untracked_disregarded(r.stdout, archive_dir)
    if disregarded and not remainder:
        log("dirty-tree guard: disregarding untracked bale-written "
            f"path(s) — {', '.join(disregarded)} — telemetry and/or "
            "archived response artifacts, untouched by git revert; tree "
            "is otherwise clean")
        return None
    if stash:
        # -u includes untracked files so the revert sees a truly clean tree;
        # a labeled message makes the stash findable if a later step aborts.
        git(["stash", "push", "-u", "-m", "bale rollback autostash"], cwd=repo)
        # Resolve the ref now so the caller pops exactly this stash even if
        # the user has other stashes; stash@{0} is the one we just pushed.
        log("stashed dirty working tree (`--stash`); will pop after revert")
        return "stash@{0}"
    if force:
        log("FORCE: proceeding with rollback on a dirty working tree "
            "(--force); changes were NOT stashed", force=True)
        return None
    fail("working tree is dirty; rollback would revert onto uncommitted "
         "changes. Commit or stash first, or re-run with --stash to stash "
         "automatically (or --force to proceed anyway).\n"
         f"git status --porcelain:\n{status.rstrip()}")
    return None  # unreachable (fail exits); satisfies the type checker


def _pop_stash(repo: Path, stash_ref: Optional[str]) -> None:
    """Pop a stash created by _guard_dirty_tree, if any.

    A pop conflict does not fail the rollback — the revert already landed and
    is the primary work; the user is told the stash is preserved to resolve
    by hand. Surfacing this rather than swallowing it honors CLAUDE.md §6.
    """
    if stash_ref is None:
        return
    from __main__ import log, git
    r = git(["stash", "pop"], cwd=repo, check=False)
    if r.returncode != 0:
        log(f"warning: `git stash pop` did not apply cleanly "
            f"(exit {r.returncode}); the stashed changes are preserved — "
            f"resolve and `git stash pop` by hand. stderr:\n{r.stderr.rstrip()}")
    else:
        log("popped autostash back onto the working tree")


# ---------------------------------------------------------------------------
# The revert core, shared by rollback and --undo. Runs `git revert`, handles
# the conflict path, and on success amends the message and tags the result.
# ---------------------------------------------------------------------------

def _run_revert(
    repo: Path,
    *,
    target_commit: str,
    is_merge: bool,
    new_message: str,
    result_tag: str,
    stash_ref: Optional[str],
    force: bool,
) -> int:
    """Run `git revert` on `target_commit`, then amend + tag on success.

    `is_merge` selects `-m 1` (mainline = the origin-branch parent). Three
    outcomes after the revert:

      - clean → amend the auto "Revert ..." message to bale's form and tag.
      - conflict (revert left in progress, BALE.md §9.2 step 5) → print the
        affected files, tell the user to resolve and `git revert --continue`,
        exit non-zero WITHOUT tagging (a tag would claim a clean rollback that
        hasn't happened).
      - empty (git declines a no-op revert — e.g. re-reverting an
        already-reverted commit; exits non-zero but nothing in progress) →
        report it as a no-op, point at `--undo`, exit non-zero without tagging.

    `force` selects `git tag -f` so a guard-bypassing re-run doesn't crash on
    a pre-existing tag; the non-force path is guaranteed tag-free by the
    caller's existence guard. Returns the operation's exit code.
    """
    from __main__ import log, git
    revert_cmd = ["revert", "--no-edit"]
    if is_merge:
        revert_cmd += ["-m", "1"]
    revert_cmd.append(target_commit)
    log(f"git {' '.join(revert_cmd)}")
    r = git(revert_cmd, cwd=repo, check=False)

    if r.returncode != 0:
        if not _revert_in_progress(repo):
            # Empty / no-op revert: git refused because there's nothing to
            # apply (the target is already reverted). Working tree is
            # unchanged, so a stash (if any) pops cleanly back.
            print()
            print(f"  nothing to revert — {target_commit[:9]} appears already "
                  f"reverted (the revert would be empty).")
            print("  to reverse a prior rollback, use `bale rollback <sid> --undo`.")
            log("revert produced no changes (already reverted); not tagged")
            _pop_stash(repo, stash_ref)
            return 1
        conflicts = _conflicted_paths(repo)
        print()
        if conflicts:
            print("  conflicted files:")
            for p in conflicts:
                print(f"    {p}")
        print("  the revert is left in progress. Resolve the conflicts, then:")
        print("    git revert --continue   (or: git revert --abort)")
        print(f"  bale did NOT tag {result_tag} — `git revert --continue` "
              f"completes the revert without bale's bookkeeping; tag by hand "
              f"if you want it tracked.")
        if stash_ref is not None:
            print(f"  your --stash changes are still stashed ({stash_ref}); "
                  f"`git stash pop` after the revert is resolved.")
        # Status headline last, after the resolution steps the user needs to
        # act on (the main-CLI output idiom: takeaway nearest the prompt).
        print()
        print(f"  [CONFLICT] revert of {target_commit[:9]} left in progress")
        log(f"revert conflict (exit {r.returncode}); left in progress, "
            f"not tagged")
        return 1

    # Clean revert: rewrite the auto-generated "Revert ..." subject to bale's
    # form so the history reads as a bale rollback, and tag the new commit.
    git(["commit", "--amend", "-m", new_message], cwd=repo)
    git(["tag", "-f", result_tag] if force else ["tag", result_tag], cwd=repo)
    new_head = git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()
    log(f"reverted cleanly; amended message, tagged {result_tag} "
        f"at {new_head[:9]}")

    _pop_stash(repo, stash_ref)
    return 0


# ---------------------------------------------------------------------------
# Telemetry. The clean-success paths append an attempt to the sid's record.
# ---------------------------------------------------------------------------

def _record_rollback_attempt(repo: Path, sid: str, outcome: str) -> Optional[str]:
    """Append this operation's attempt to the sid's telemetry record.

    Called from the clean-success paths of _do_rollback / _do_undo only —
    the same paths that write the reverted/<sid> / re-applied/<sid> tags
    (v0.3.18, BALE.md §9.2/§8.9). `outcome` is "rolled-back" or
    "re-applied"; command is always "rollback" (the schema's command enum
    honestly names the producing command). closure_reason is null:
    rollback closes no session — the outcome names the event, matching
    revert's null-when-no---reason posture. Everything tarball- and
    validation-shaped is null via the builder's defaults.

    Scope: the session directory (and its scope.json) is normally long
    gone at rollback time — apply's close wiped it. Read the recorded
    scope only when scope.json still exists; otherwise record [] ("no
    scope recorded"), per the crash-debris honesty refinement — never the
    conservative whole-tree widening read_session_scope applies to a
    MISSING scope, which here would fabricate a scope this record never
    observed.

    Best-effort like every telemetry write: a failure is logged inside
    write_telemetry_record and never raises — the revert that already
    landed stands. Returns the record's repo-relative path, or None on a
    write failure (the caller's summary row reports which).
    """
    from __main__ import (build_telemetry_attempt, read_session_scope,
                          scope_file_path, write_telemetry_record)
    scope = (read_session_scope(repo, sid)
             if scope_file_path(repo, sid).exists() else [])
    return write_telemetry_record(
        repo, sid, build_telemetry_attempt(
            outcome=outcome, command="rollback",
            scope=scope,
            closure_reason=None,
            log_path=f".bale/logs/{sid}.log",
        ))


# ---------------------------------------------------------------------------
# Operations: list, rollback (default), undo.
# ---------------------------------------------------------------------------

def _do_list(repo: Path) -> int:
    """`--list`: applied sessions reachable from HEAD with rollback status.

    Read-only — no git state changes. Status per `applied/<sid>`:
      re-applied  rolled back, then undone (net: applied)
      reverted    rolled back, not undone (net: reverted)
      applied     untouched by rollback
    """
    from __main__ import log
    log("rollback --list")
    applied = _reachable_tags(repo, TAG_APPLIED)
    if not applied:
        print()
        print("  no applied/<sid> tags reachable from HEAD.")
        return 0

    print()
    print("  applied sessions reachable from HEAD:")
    print()
    for sid, _tag in applied:
        if _tag_exists(repo, f"{TAG_REAPPLIED}/{sid}"):
            status = "re-applied"
        elif _tag_exists(repo, f"{TAG_REVERTED}/{sid}"):
            status = "reverted"
        else:
            status = "applied"
        print(f"    {status:<11} {sid}")
    # Summary + the actionable hint land last, after the rows (the readable
    # idiom the main CLI uses: detail first, the takeaway nearest the prompt).
    print()
    print(f"  {len(applied)} applied session(s); "
          f"rollback <sid> to revert, rollback <sid> --undo to re-apply.")
    return 0


def _resolve_sid(repo: Path, explicit_sid: Optional[str], prefix: str,
                 what: str) -> str:
    """Resolve the target sid for an operation against `<prefix>/*` tags.

    Explicit sid: require `<prefix>/<sid>` to exist. No sid: pick the most
    recent reachable `<prefix>/*` tag (BALE.md §9.2 default behavior).
    fail()s with an actionable message when nothing matches.
    """
    from __main__ import fail
    if explicit_sid is not None:
        if not _tag_exists(repo, f"{prefix}/{explicit_sid}"):
            fail(f"no {prefix}/{explicit_sid} tag. "
                 f"`bale rollback --list` shows applied sessions; "
                 f"`git tag --list '{prefix}/*'` shows all {prefix} tags.")
        return explicit_sid
    reachable = _reachable_tags(repo, prefix)
    if not reachable:
        fail(f"no {prefix}/<sid> tags reachable from HEAD — nothing to "
             f"{what}. (`bale rollback --list` shows applied sessions.)")
    return reachable[0][0]


def _do_rollback(repo: Path, args) -> int:
    """Default `rollback [sid]`: git revert an applied (merged) session."""
    from __main__ import log, fail, set_log_file
    sid = _resolve_sid(repo, args.sid, TAG_APPLIED, "roll back")
    set_log_file(repo / ".bale" / "logs" / f"{sid}.log")
    log(f"rollback: {sid}")

    # BALE.md §9.2 step 4: refuse if reverted/<sid> already exists. The intent
    # guards against double-reverting; --force overrides (and --undo is the
    # normal way back).
    reverted_tag = f"{TAG_REVERTED}/{sid}"
    if _tag_exists(repo, reverted_tag) and not args.force:
        fail(f"{reverted_tag} already exists — this session was already "
             f"rolled back. Use `bale rollback {sid} --undo` to re-apply it. "
             f"(--force bypasses this guard, but re-reverting an "
             f"already-reverted commit is a no-op.)")

    commit = _tag_commit(repo, f"{TAG_APPLIED}/{sid}")
    is_merge = _is_merge_commit(repo, commit)
    # Recover the original summary: on a merge commit it lives on the second
    # parent (the bale branch tip, `[bale <sid>] <summary>`); on a plain
    # commit it is the commit's own subject.
    summary_src = _commit_subject(repo, f"{commit}^2") if is_merge \
        else _commit_subject(repo, commit)
    summary = _extract_summary(summary_src, sid)
    log(f"target {commit[:9]} ({'merge' if is_merge else 'plain'} commit); "
        f"summary: {summary!r}")

    stash_ref = _guard_dirty_tree(repo, stash=args.stash, force=args.force)

    rc = _run_revert(
        repo,
        target_commit=commit,
        is_merge=is_merge,
        new_message=f"[bale rollback {sid}] {summary}",
        result_tag=reverted_tag,
        stash_ref=stash_ref,
        force=args.force,
    )
    if rc == 0:
        # Telemetry (v0.3.18, BALE.md §9.2): the clean-success path — and
        # only it — appends the attempt, same as it alone writes the tag.
        telemetry_rel = _record_rollback_attempt(repo, sid, "rolled-back")
        # Detail first, the status headline last — the takeaway sits nearest
        # the user's next prompt (the main-CLI output idiom). The telemetry
        # row is the same row unlock and revert carry.
        print()
        print(f"  reverted:  applied/{sid} ({commit[:9]})")
        print(f"  tag:       {reverted_tag}")
        print(f"  undo with: bale rollback {sid} --undo")
        print(f"  telemetry: "
              + (f"recorded {telemetry_rel}" if telemetry_rel
                 else "write failed — see log"))
        print()
        print(f"  [ROLLED BACK] {sid}")
    return rc


def _do_undo(repo: Path, args) -> int:
    """`rollback [sid] --undo`: revert a prior rollback's revert commit.

    Symmetric with _do_rollback. Finds reverted/<sid>, reverts that (always a
    plain commit — `git revert` never produces a merge), and tags
    re-applied/<sid>. The net effect re-applies the original change.
    """
    from __main__ import log, fail, set_log_file
    sid = _resolve_sid(repo, args.sid, TAG_REVERTED, "undo")
    set_log_file(repo / ".bale" / "logs" / f"{sid}.log")
    log(f"rollback --undo: {sid}")

    reapplied_tag = f"{TAG_REAPPLIED}/{sid}"
    if _tag_exists(repo, reapplied_tag) and not args.force:
        fail(f"{reapplied_tag} already exists — this rollback was already "
             f"undone. Use --force to undo again.")

    revert_commit = _tag_commit(repo, f"{TAG_REVERTED}/{sid}")
    # The reverted/<sid> commit's subject is `[bale rollback <sid>] <summary>`;
    # strip that to recover the summary for the re-apply message.
    summary = _extract_summary(_commit_subject(repo, revert_commit), sid)
    log(f"undoing revert {revert_commit[:9]}; summary: {summary!r}")

    stash_ref = _guard_dirty_tree(repo, stash=args.stash, force=args.force)

    rc = _run_revert(
        repo,
        target_commit=revert_commit,
        is_merge=False,  # a revert commit is never a merge
        new_message=f"[bale rollback {sid} --undo] {summary}",
        result_tag=reapplied_tag,
        stash_ref=stash_ref,
        force=args.force,
    )
    if rc == 0:
        # Telemetry (v0.3.18, BALE.md §9.2): success-path-only, as above.
        telemetry_rel = _record_rollback_attempt(repo, sid, "re-applied")
        # Detail first, status headline last (same idiom as _do_rollback).
        # Labels realigned to the 10-char field so the telemetry row fits.
        print()
        print(f"  undid:     reverted/{sid} ({revert_commit[:9]})")
        print(f"  tag:       {reapplied_tag}")
        print(f"  telemetry: "
              + (f"recorded {telemetry_rel}" if telemetry_rel
                 else "write failed — see log"))
        print()
        print(f"  [RE-APPLIED] {sid}")
    return rc


# ---------------------------------------------------------------------------
# Public entry point.
# ---------------------------------------------------------------------------

def cmd_rollback(args) -> int:
    """Dispatch `bale rollback` to list / undo / default-rollback.

    `--list` is read-only and mutually the "just show me" path. Otherwise the
    operation is a rollback (default) or its inverse (`--undo`); both mutate
    git history and share the dirty-tree guard, the revert core, and the
    tag-bookkeeping. `--list` with `--undo`/sid is rejected as contradictory
    rather than silently ignoring one (CLAUDE.md §6: silent skips are bugs).
    """
    from __main__ import fail, repo_root, refuse_system_dir, set_log_file

    cwd = Path.cwd().resolve()
    refuse_system_dir(cwd)
    repo = repo_root(cwd)
    if repo is None:
        fail("not in a git repo. `bale rollback` requires the project repo.")
    refuse_system_dir(repo)

    if args.list:
        if args.undo or args.sid:
            fail("--list is read-only; it does not take a sid or --undo. "
                 "Run `bale rollback --list` alone to see applied sessions.")
        # --list resolves no single sid; journal it under a shared log.
        set_log_file(repo / ".bale" / "logs" / "rollback.log")
        return _do_list(repo)

    if args.undo:
        return _do_undo(repo, args)
    return _do_rollback(repo, args)
