"""bale_staging — apply-pipeline staging, reconciliation, and worktree helpers.

This module owns the mechanical helpers of the apply pipeline that operate on
the staging tree and the working tree: the apply-time `bash -n` pre-flight on
the response's shell scripts (`check_response_shell_syntax`), the response-vs-
manifest presence/sha256/path-safety checks (`verify_files_against_manifest`),
its base-tree sibling for the planner's blind checkpoint
(`check_checkpoint_shell_syntax`, the ratified board-10 fail-fast rider),
building the staging tree and running the response's `apply.sh` over it
(`stage_response`, which since v0.3.7 also owns the opt-in `target-base`
staging strategy — BALE.md §8.3 step 2 — via the private helpers
`_materialize_target_tree`, `_copy_git_dir`, and
`_overlay_declared_untracked`), the post-`apply.sh` reconciliation of staging
against the manifest (`reconcile_staging_against_manifest`, with its private
tree-snapshot helper `_walk_tree_sha256`), running the planner's blind
checkpoint from base-tree bytes (`run_blind_checkpoint`, board 6 session A —
BALE.md §8.5), running the response's `validation.sh` in staging
(`run_validation_sh`), and building the session commit from the validated
staging content via git plumbing (`build_session_commit`, which replaced the
checkout-consuming `apply_changes_to_worktree` when ADR-0008 landed in
v0.3.5). Extracted from `bin/bale`'s section 16
("Apply: helpers") in v0.1.3 to continue bringing that section back under
CODE.md §4.2's size threshold — the third extraction sibling after
`bale_config` (v0.0.4) and `bale_validate` (v0.1.2), using the same sibling-
import mechanism.

Behavior-preserving move: the functions keep the signatures and call sites they
had in `bin/bale`. The public entry points (`check_response_shell_syntax`,
`verify_files_against_manifest`, `stage_response`,
`reconcile_staging_against_manifest`, `run_blind_checkpoint`,
`run_validation_sh`,
`build_session_commit`) are pulled into the apply path's namespace via
`from bale_staging import ...` (in `bale_apply` since v0.3.13), so the
apply-pipeline callers still write them
unqualified — the by-name convention `bale_validate` established, chosen here
over `bale_config`'s qualified style precisely because it leaves the call sites
untouched. `_walk_tree_sha256` is private to this cluster (its only caller is
`reconcile_staging_against_manifest`) and is therefore not re-exported.

Imported by `bin/bale` as a sibling module: the `bin/` directory is on the
import path because `bin/bale` prepends its resolved directory to `sys.path`
(so the import works even when bale is invoked through a symlink on `PATH`) —
the same mechanism that lets `bin/bale` import `bale_config` and `bale_validate`.

The shared helpers these functions need from `bin/bale` — `fail`, `log`, `git`,
`sha256_file`, `is_path_safe`, `load_baleignore`, `is_baleignore_match` — are
pulled from `__main__` lazily, i.e. imported inside each function that calls
them rather than at module top, exactly as `bale_config` and `bale_validate` do.
The lazy form sidesteps the circular-import hazard (`bin/bale` imports this
module at load time, before its own helpers are defined) and keeps the
dependency visible at the call site. Unlike `bale_validate`, this module needs
no path constants from `bin/bale`: every path these functions touch derives from
their arguments (`repo`, `response_dir`, `staging`), so nothing but the
functions themselves moved.

`check_response_shell_syntax` lived in section 16 through v0.1.2 — the
`bale_validate` extraction deliberately left it behind because it is an apply-
time pre-flight, not a manifest/schema validator. It moves here because
`bale_staging` is the apply-helpers home, and a `bash -n` pre-flight on the
response's `apply.sh`/`validation.sh` belongs with the staging cluster it gates.

Since board 10 S1 (ADR-0016) the three response-script executions this
module owns — the `apply.sh` run in `stage_response`, the checkpoint run
in `run_blind_checkpoint`, and the worker run in `run_validation_sh` —
are confined by default through the sibling module `bale_sandbox`
(namespace confinement: network off, writes limited to staging plus the
session log, environment scrubbed), with a per-invocation `sandbox=False`
escape the apply pipeline threads from `--no-sandbox` and FORCE-logs.
The sandbox module is deliberately standalone (no `__main__`
back-references) so the blind checkpoint and the tests can exercise it
as a library.

See claude/context/bale-internals.md for how this module sits next to `bin/bale`,
`bale_config`, and `bale_validate`.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from typing import Optional, Sequence


def check_response_shell_syntax(response_dir: Path) -> None:
    """Pre-flight `bash -n` on the response's apply.sh and validation.sh.

    Both are required deliverables in every response tarball (TARBALL.md
    section 5.1) and both get staged and invoked by bale — apply.sh as
    part of building the staging tree (BALE.md 8.3 step 4), validation.sh
    after the post-apply reconciliation passes (8.5). Without this pre-
    flight a syntax error in either would surface mid-pipeline after
    expensive cp work. This closes that gap and fails fast for both files.

    Runs against the extracted response tree, not the staging tree, so
    it sees exactly what the tarball shipped.

    The required-files check upstream guarantees both files exist by
    the time this runs.
    """
    from __main__ import fail
    for name in ("apply.sh", "validation.sh"):
        path = response_dir / name
        r = subprocess.run(
            ["bash", "-n", str(path)],
            capture_output=True, text=True, check=False,
        )
        if r.returncode != 0:
            msg = (r.stderr or r.stdout or "").strip() or "syntax error"
            fail(f"{name} has bash syntax errors: {msg}")


def check_checkpoint_shell_syntax(repo: Path, base_sha: str,
                                  checkpoint_path: str) -> None:
    """Pre-flight `bash -n` on the blind checkpoint's base-tree bytes.

    The fail-fast sibling of check_response_shell_syntax, closing the
    gap that function's docstring left open: the worker's two scripts
    were syntax-gated before any staging work, but a syntax-errored
    checkpoint surfaced only mid-pipeline, after the expensive stage
    and reconciliation, as a confusing exit-2 "checkpoint itself
    errored" HOLD. This runs at the same pre-staging point as the
    checkpoint's dangling and provenance checks (both already have
    base_sha in hand), against the exact bytes run_blind_checkpoint
    will execute — `git show <base_sha>:<path>`, never a working-tree
    or staged copy (the board-6 blindness rule, BALE.md §8.5).

    (Ratified rider from the 2026-08-07-sandbox-adr-009 sitting's
    fold-in registry, landed with board 10 S1.)
    """
    from __main__ import fail
    shown = subprocess.run(
        ["git", "show", f"{base_sha}:{checkpoint_path}"],
        cwd=str(repo), capture_output=True,
    )
    if shown.returncode != 0:
        # The dangling pre-check upstream already passed; a show failure
        # here means the base tree changed mid-apply or git errored.
        fail(f"could not read the blind checkpoint {checkpoint_path!r} "
             f"from the base tree {base_sha[:7]} for the syntax "
             f"pre-flight: "
             f"{shown.stderr.decode(errors='replace').strip()}")
    with tempfile.NamedTemporaryFile(prefix="bale-ckpt-syntax-",
                                     suffix=".sh") as tf:
        tf.write(shown.stdout)
        tf.flush()
        r = subprocess.run(
            ["bash", "-n", tf.name],
            capture_output=True, text=True, check=False,
        )
    if r.returncode != 0:
        msg = (r.stderr or r.stdout or "").strip() or "syntax error"
        fail(f"the blind checkpoint {checkpoint_path!r} (base-tree "
             f"bytes at {base_sha[:7]}) has bash syntax errors: {msg}. "
             f"The checkpoint is planner-authored — fix and commit it "
             f"at the named path, then re-run apply.")


def verify_files_against_manifest(
    repo: Path, response_dir: Path, manifest: dict,
) -> None:
    """BALE.md 8.1 steps 7, 8, 9. All path-safety + presence + sha256 checks.

    `repo` is the apply target — required since v0.0.10 because step 9's
    path-safety now includes the `.baleignore` match per BALE.md §11
    rule 14: a response cannot declare a path the project's user-managed
    exclusion file says shouldn't ride through bale. The matcher is
    loaded once and reused across all change entries; load failure
    propagates as `fail()` so the apply rejects with the same error
    wording pack uses for the same file.
    """
    from __main__ import (
        fail,
        is_baleignore_match,
        is_path_safe,
        load_baleignore,
        sha256_file,
    )
    files_dir = response_dir / "files"
    baleignore = load_baleignore(repo)

    # 9: path safety on every changes[].path. Two independent gates —
    # is_path_safe rejects path-traversal and reserved prefixes; the
    # .baleignore check (rule 14) rejects paths the user said shouldn't
    # flow through bale. Distinct messages so the user knows which gate
    # tripped and how to recover (fix the manifest vs edit .baleignore).
    for change in manifest["changes"]:
        if not is_path_safe(change["path"]):
            fail(f"unsafe path in manifest: {change['path']}")
        if is_baleignore_match(change["path"], baleignore):
            # baleignore is non-None here (is_baleignore_match returns
            # False on None) so first_match is safe.
            pat = baleignore.first_match(change["path"])
            fail(
                f"manifest declares {change['path']!r} but it matches "
                f".baleignore pattern {pat!r}. The response is rejected "
                f"per BALE.md §11 rule 14. Either edit `.baleignore` to "
                f"allow this path (then re-run apply) or use `bale retry` "
                f"with a corrected response."
            )

    # 7: presence per action.
    for change in manifest["changes"]:
        path = change["path"]
        action = change["action"]
        f = files_dir / path
        if action in ("created", "modified"):
            if not f.is_file():
                fail(f"manifest declares {action} {path} but files/{path} "
                     f"is missing in the tarball")
        else:  # deleted
            if f.exists():
                fail(f"manifest declares deleted {path} but files/{path} "
                     f"is present in the tarball (deletes must not ship a file)")

    # 7 (other direction): every file in files/ is declared.
    declared = {c["path"] for c in manifest["changes"]
                if c["action"] in ("created", "modified")}
    if files_dir.exists():
        for f in files_dir.rglob("*"):
            if f.is_file():
                rel = f.relative_to(files_dir).as_posix()
                if rel not in declared:
                    fail(f"file in tarball not declared in manifest: files/{rel}")

    # 8: sha256 matches for created/modified.
    for change in manifest["changes"]:
        if change["action"] in ("created", "modified"):
            actual = sha256_file(files_dir / change["path"])
            if actual != change["sha256"]:
                fail(f"sha256 mismatch for {change['path']}: "
                     f"manifest={change['sha256'][:12]}..., "
                     f"actual={actual[:12]}...")


def _materialize_target_tree(repo: Path, base_sha: str, staging: Path) -> None:
    """Extract the target tip's tree (`git archive <base_sha>`) into staging.

    The target-base half of BALE.md §8.3 step 2: instead of copying the
    working tree, materialize exactly the tree the session commit will be
    built against (§8.2's `git_head_at_apply`). `git archive --format=tar`
    is core plumbing (as old as rev-parse) and preserves file modes and
    symlinks; extraction goes through stdlib `tarfile` reading the
    subprocess pipe directly — no shell pipeline, no external `tar`
    dependency.

    Member names are validated defensively before extraction (no absolute
    paths, no `..` components) even though the archive comes from the
    project's own object database; where the running Python supports
    extraction filters (3.12+, and backported 3.10.12+/3.11.4+), the
    stdlib `tar` filter is applied as a second belt.

    Raises RuntimeError on any git or extraction failure; the caller
    wipes staging and rejects the tarball, matching the apply.sh failure
    contract.
    """
    extract_kwargs = {}
    if hasattr(tarfile, "tar_filter"):
        # The stdlib extraction-filter API exists on this Python; the
        # "tar" filter blocks absolute names and .. escapes (and silences
        # the 3.12/3.13 no-filter DeprecationWarning) while preserving
        # modes and symlinks, which the commit-side mode derivation in
        # build_session_commit depends on.
        extract_kwargs["filter"] = "tar"
    proc = subprocess.Popen(
        ["git", "archive", "--format=tar", base_sha],
        cwd=str(repo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdout is not None  # stdout=PIPE above; guard for mypy
    try:
        with tarfile.open(fileobj=proc.stdout, mode="r|") as tf:
            for member in tf:
                name = member.name
                if name.startswith("/") or ".." in Path(name).parts:
                    raise RuntimeError(
                        f"git archive emitted an unsafe member path "
                        f"{name!r}; refusing to extract"
                    )
                tf.extract(member, path=str(staging), **extract_kwargs)
    except tarfile.TarError as e:
        proc.kill()
        proc.wait()
        raise RuntimeError(
            f"could not extract git archive of {base_sha[:12]}: {e}"
        )
    stderr = proc.stderr.read() if proc.stderr is not None else b""
    returncode = proc.wait()
    if returncode != 0:
        detail = stderr.decode("utf-8", "replace").strip() or "(no output)"
        raise RuntimeError(
            f"git archive {base_sha[:12]} exited {returncode}: {detail}"
        )


def _copy_git_dir(repo: Path, staging: Path) -> None:
    """Copy the repo's `.git` (directory, or gitfile in a linked worktree)
    into staging.

    Target-base staging only. The working-tree strategy copies `.git`
    incidentally (it copies everything but `.bale/`), and its presence is
    load-bearing in a way that is easy to miss: the default staging
    directory lives *inside* the repo (`.bale/staging/<sid>`), and a git
    invocation from a `validation.sh` running in a staging tree with no
    `.git` of its own would discover *upward* to the real repo — exactly
    the surface validation must never operate on (TARBALL.md §9). Copying
    `.git` keeps git-in-staging resolving to staging under both
    strategies. `git status` inside a target-base staging will report the
    base-vs-index divergence; that is cosmetic, and the same class of
    noise the working-tree copy shows mid-edit.
    """
    src = repo / ".git"
    if src.is_dir() and not src.is_symlink():
        shutil.copytree(src, staging / ".git", symlinks=True)
    elif src.exists() or src.is_symlink():
        # Linked-worktree checkouts have .git as a file pointing at the
        # main repository's git dir; copy it as-is.
        shutil.copy2(src, staging / ".git", follow_symlinks=False)


def _overlay_declared_untracked(repo: Path, staging: Path,
                                untracked_inputs: Sequence[str],
                                base_sha: str) -> None:
    """Overlay each declared untracked input from the working tree onto the
    materialized target-base staging (BALE.md §8.3 step 2, target-base).

    The declaration mechanism is load-bearing, not polish: a pure
    git-archive tree carries no untracked build or dependency state, and
    without that state validation cannot run at all for most projects.
    Every declared entry is validated before copying, and every violation
    is loud (the silent-skip rule, CLAUDE.md §6):

      - the path must be safe and repo-relative (`is_path_safe`: no
        absolute paths, no `..`, not under `.git/` or `.bale/`);
      - it must exist in the working tree — a missing declared input is
        a hard stage failure, never a skip;
      - it must be untracked at the target tip (`git ls-tree` of
        `base_sha` finds nothing at or under it) — overlaying a tracked
        path would replace committed content with working-tree content,
        re-opening exactly the fidelity gap this strategy closes;
      - it must not be the staging directory itself or contain it —
        the copy-into-itself hazard the working-tree strategy guards
        with its own resolve() check.

    Entries are copied verbatim (dirs recursively, symlinks preserved).
    Declared paths are expected to be disjoint; a nested pair (e.g.
    `.venv` and `.venv/lib`) fails on the second copy's FileExistsError,
    which propagates as a stage failure naming the collision.

    Raises RuntimeError on any violation; the caller wipes staging and
    rejects the tarball.
    """
    from __main__ import is_path_safe, log
    staging_resolved = staging.resolve()
    for raw in untracked_inputs:
        rel = raw.strip().strip("/")
        if not rel or not is_path_safe(rel):
            raise RuntimeError(
                f"staging.untracked_inputs entry {raw!r} is not a safe "
                f"repo-relative path (no absolute paths, no '..', not "
                f"under .git/ or .bale/)"
            )
        src = repo / rel
        if not src.exists() and not src.is_symlink():
            raise RuntimeError(
                f"declared untracked input {rel!r} is missing from the "
                f"working tree. Declared inputs are required at stage "
                f"time — build it, or remove it from "
                f"staging.untracked_inputs in bale.toml"
            )
        src_resolved = src.resolve()
        if (src_resolved == staging_resolved
                or staging_resolved in src_resolved.parents
                or src_resolved in staging_resolved.parents):
            raise RuntimeError(
                f"declared untracked input {rel!r} overlaps the staging "
                f"directory {staging}; refusing the copy-into-itself"
            )
        r = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", base_sha, "--", rel],
            cwd=str(repo), capture_output=True, text=True,
        )
        if r.returncode != 0:
            detail = (r.stderr or r.stdout or "").strip() or "(no output)"
            raise RuntimeError(
                f"git ls-tree {base_sha[:12]} -- {rel!r} exited "
                f"{r.returncode}: {detail}"
            )
        if r.stdout.strip():
            raise RuntimeError(
                f"declared untracked input {rel!r} is tracked at the "
                f"target tip ({base_sha[:12]}); overlaying it would "
                f"replace committed content with working-tree content. "
                f"Remove it from staging.untracked_inputs in bale.toml — "
                f"tracked content already rides in via the materialized "
                f"tree"
            )
        dst = staging / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            if src.is_dir() and not src.is_symlink():
                shutil.copytree(src, dst, symlinks=True)
            else:
                shutil.copy2(src, dst, follow_symlinks=False)
        except FileExistsError as e:
            raise RuntimeError(
                f"declared untracked input {rel!r} collides with content "
                f"already staged (nested or duplicate declaration?): {e}"
            )
        log(f"overlaid declared untracked input: {rel}")


def stage_response(repo: Path, response_dir: Path, staging: Path, *,
                   strategy: str = "working-tree",
                   untracked_inputs: Sequence[str] = (),
                   base_sha: Optional[str] = None,
                   sandbox: bool = True,
                   log_path: Optional[Path] = None,
                   ) -> Optional[dict[str, str]]:
    """Build the staging tree, overlay files/, run apply.sh.

    `sandbox` (default on, ADR-0016) confines the apply.sh run via
    bale_sandbox.run_confined — writes land only in staging and the
    handed `log_path`, network off, environment scrubbed — with the
    response extraction dir passed through read-only (apply.sh is read
    from it, and it lives under /tmp, which the sandbox replaces with
    a private tmpfs). `log_path` is required when sandbox is on; the
    caller passes the session log. `sandbox=False` is the escape
    path — the caller (apply_pipeline) FORCE-logs the bypass.

    BALE.md section 8.3. The staging *base* is built per `strategy`:

      - "working-tree" (default): cp the project's working tree, minus
        `.bale/` — byte-identical to the historical behavior, and the
        documented fallback and ground truth. `untracked_inputs` is
        redundant here (the copy already carries all untracked state)
        and is logged as such rather than silently ignored.
      - "target-base" (opt-in, bale.toml [staging]): materialize the
        target tip's tree (`base_sha`, required — §8.2's
        git_head_at_apply) via git archive, copy `.git` alongside it,
        then overlay the declared `untracked_inputs` from the working
        tree. Validation then exercises exactly the content the session
        commit lands, closing the §8.3 validation-fidelity gap.

    Returns the reconciliation baseline for the target-base strategy — a
    {path: sha256} snapshot of the staging base taken *before* the
    files/ overlay, which reconcile_staging_against_manifest() must use
    in place of its working-tree walk (the manifest's changes are
    authored against the target tip, and diffing a target-base staging
    against a diverged working tree would report the divergence as
    undeclared changes). Returns None for the working-tree strategy,
    whose baseline remains the working-tree walk, unchanged.

    After the base is built, apply.sh runs from response_dir with
    cwd=staging — it handles deletes and any other manifest-declared
    file operations the cp mirror can't express. The post-stage
    reconciliation in reconcile_staging_against_manifest() (BALE.md §8.4,
    §11 rule 18) verifies the resulting tree matches the manifest exactly,
    so apply.sh can't quietly touch undeclared files.

    Raises RuntimeError on apply.sh non-zero exit (BALE.md §11 rule 17)
    and on any target-base materialization or declared-input failure.
    The caller wipes staging and rejects the tarball — no git side
    effects, no reconciliation attempted.

    Precondition: `staging` must not exist. `_apply_pipeline` checks
    and removes a stale default-path staging before calling this; the
    explicit --staging-dir path errors out upstream when staging exists.
    The bare `staging.mkdir(parents=True)` below (no `exist_ok=True`) is
    intentional — a violation of the precondition should surface as a
    FileExistsError, not a silent overlay onto someone else's directory.
    """
    from __main__ import log
    staging.mkdir(parents=True)
    staging_resolved = staging.resolve()

    baseline: Optional[dict[str, str]] = None
    if strategy == "target-base":
        if not base_sha:
            raise RuntimeError(
                "target-base staging requires the resolved target tip "
                "(base_sha); caller must pass §8.2's git_head_at_apply"
            )
        _materialize_target_tree(repo, base_sha, staging)
        _copy_git_dir(repo, staging)
        _overlay_declared_untracked(repo, staging, untracked_inputs,
                                    base_sha)
        # The reconciliation baseline is this pre-overlay base — the
        # same walk (and the same .git skip) the post-apply.sh snapshot
        # uses, so the comparison is symmetric.
        baseline = _walk_tree_sha256(staging, {staging / ".git"})
        log(f"staged from target base {base_sha[:7]} "
            f"({len(untracked_inputs)} declared untracked input(s); "
            f"baseline snapshot: {len(baseline)} files)")
    elif strategy == "working-tree":
        if untracked_inputs:
            log("staging.untracked_inputs is configured but "
                "staging.strategy is working-tree; the declaration is "
                "redundant (the working-tree copy already carries all "
                "untracked state) and is ignored")
        # cp project state into staging, minus .bale/ (BALE.md 8.3 step 2
        # spec). Also skip the staging directory itself if it lives inside
        # the repo — otherwise iterdir() yields it (we just created it)
        # and we'd copy it into itself.
        for item in repo.iterdir():
            if item.name == ".bale":
                continue
            if item.resolve() == staging_resolved:
                continue
            dst = staging / item.name
            if item.is_dir():
                shutil.copytree(item, dst, symlinks=True)
            else:
                shutil.copy2(item, dst, follow_symlinks=False)
    else:
        raise RuntimeError(
            f"unknown staging strategy {strategy!r}; expected "
            f"'working-tree' or 'target-base'"
        )

    # Overlay files/ from the response (BALE.md 8.3 step 3).
    files_dir = response_dir / "files"
    if files_dir.exists():
        for src in files_dir.rglob("*"):
            if src.is_file():
                rel = src.relative_to(files_dir)
                dst = staging / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst, follow_symlinks=False)

    # Run apply.sh from the extracted response dir with cwd=staging
    # (BALE.md 8.3 step 4). Running from response_dir rather than copying
    # apply.sh into staging keeps the staging tree clean for the
    # post-apply reconciliation — reconciliation compares staging against
    # the pre-apply project state and anything extra at the staging root
    # would surface as undeclared. Output is logged in full; on non-zero
    # exit we raise so the caller wipes staging and rejects the tarball.
    apply_sh = response_dir / "apply.sh"
    if sandbox:
        import bale_sandbox  # lazy — sibling module, standalone by design
        if log_path is None:
            raise RuntimeError(
                "stage_response(sandbox=True) requires log_path — the "
                "session log the confinement contract binds writable")
        try:
            bale_sandbox.ensure_verified(log_path)
        except bale_sandbox.SandboxUnavailableError as e:
            raise RuntimeError(str(e))
        log("running apply.sh in staging (confined: network off, "
            "writes limited to staging + session log)...")
        result = bale_sandbox.run_confined(
            ["bash", str(apply_sh)],
            staging=staging, log_path=log_path,
            tmp_passthrough=[response_dir],
        )
    else:
        log("running apply.sh in staging (UNCONFINED — --no-sandbox)...")
        result = subprocess.run(
            ["bash", str(apply_sh)],
            cwd=str(staging),
            capture_output=True,
            text=True,
        )
    if result.stdout:
        log(f"apply.sh stdout:\n{result.stdout.rstrip()}")
    if result.stderr:
        log(f"apply.sh stderr:\n{result.stderr.rstrip()}")
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip() or "(no output)"
        raise RuntimeError(
            f"apply.sh exited {result.returncode} in staging: {detail}"
        )
    log(f"apply.sh exited 0")
    return baseline


def _walk_tree_sha256(root: Path, skip_paths: set[Path]) -> dict[str, str]:
    """Compute {posix_relative_path: sha256_hex} for every regular file under
    `root`, pruning any directory whose resolved path appears in `skip_paths`.

    Used by reconcile_staging_against_manifest to take symmetric snapshots
    of the pre-apply project tree and the post-apply staging tree. `os.walk`
    with in-place mutation of `dirnames` prevents descending into pruned
    subtrees (e.g. `.bale/` or a staging dir nested inside the repo) so
    large pruned paths aren't even iterated.

    `Path.is_file()` returns False for broken symlinks, which is what we
    want — a dangling symlink shouldn't count toward the diff either way,
    and the cp-overlay path in stage_response wouldn't materialize one as
    a regular file anyway.
    """
    from __main__ import sha256_file
    skip_resolved: set[Path] = set()
    for p in skip_paths:
        try:
            skip_resolved.add(p.resolve())
        except OSError:
            # A skip target that doesn't resolve (e.g. --staging-dir under a
            # broken parent) can't match anything we'd walk; drop it.
            continue
    out: dict[str, str] = {}
    for dirpath, dirnames, filenames in os.walk(root):
        d = Path(dirpath)
        # Prune subdirs whose resolved path is in skip_resolved. Mutating
        # dirnames in place is the os.walk-supported way to prevent descent.
        dirnames[:] = [
            name for name in dirnames
            if (d / name).resolve() not in skip_resolved
        ]
        for fn in filenames:
            fp = d / fn
            if fp.is_file():
                rel = fp.relative_to(root).as_posix()
                out[rel] = sha256_file(fp)
    return out


def reconcile_staging_against_manifest(repo: Path, staging: Path,
                                       manifest: dict, *,
                                       baseline: Optional[dict[str, str]]
                                       = None) -> None:
    """Verify the post-apply.sh staging tree matches the manifest exactly.

    BALE.md §8.4 and §11 rule 18: every created/deleted/modified path in
    staging vs the staging base must correspond to a manifest entry of
    the matching action and sha256, with no undeclared writes, deletes,
    or modifications. Fails with a clear message naming every
    discrepancy so the user can find them.

    The comparison base depends on how staging was built (BALE.md §8.3
    step 2). With `baseline=None` — the working-tree strategy — the base
    is the project tree itself, skipping `.bale/` (per BALE.md 8.3 step 2
    — never copied into staging) and the staging dir if it lives inside
    the repo (the user-set `--staging-dir` case; default
    `<repo>/.bale/staging/` is already covered by the `.bale/` skip),
    exactly the historical behavior. With a `baseline` dict — the
    target-base strategy — the base is stage_response's pre-overlay
    snapshot of the materialized staging (target tree plus declared
    untracked inputs): the manifest was authored against the target tip,
    and walking a diverged working tree here would misreport the
    divergence itself as undeclared changes. Both walks skip `.git/`:
    the path-safety rule (§11 rule 14) already prohibits `.git/`-prefixed
    paths in the manifest, so anything there can't be declared anyway,
    and the cp preserves it byte-for-byte — walking it just costs sha256
    time on every apply against a mature repo. The two snapshots use the
    same walk function so the baseline is symmetric with what
    stage_response actually built (modulo the symmetric `.git/` skip).

    Reasoning per action:
      - created: must be absent from project, present in staging, with
        sha256 matching the manifest (which already matched files/ at
        pre-flight).
      - deleted: must be present in project, absent from staging after
        apply.sh ran.
      - modified: must be present in both, with staging's sha256 matching
        the manifest and differing from project (otherwise the manifest's
        action is wrong — modified-with-no-actual-change is a contract
        violation worth surfacing).

    Anything that changed in staging but isn't declared in the manifest
    is an apply.sh violation — the script touched a file it wasn't
    authorized to touch.
    """
    from __main__ import log
    # Build symmetric snapshots. The working-tree base walks the project,
    # skipping `.bale/` (never copied into staging) and the staging dir
    # itself if it's inside the repo; the target-base base is the
    # pre-overlay snapshot stage_response handed us. Skip `.git/` in all
    # walks — see the docstring rationale (rule 14 prohibits `.git/`
    # paths in the manifest, the cp preserves it byte-for-byte).
    if baseline is not None:
        project_state = baseline
    else:
        project_state = _walk_tree_sha256(
            repo, {repo / ".bale", repo / ".git", staging}
        )
    staging_state = _walk_tree_sha256(staging, {staging / ".git"})

    project_paths = set(project_state)
    staging_paths = set(staging_state)
    actual_created = staging_paths - project_paths
    actual_deleted = project_paths - staging_paths
    actual_modified = {
        p for p in (project_paths & staging_paths)
        if project_state[p] != staging_state[p]
    }

    problems: list[str] = []

    # For each manifest entry, verify the actual transition matches.
    declared_paths: set[str] = set()
    for change in manifest["changes"]:
        path = change["path"]
        action = change["action"]
        declared_paths.add(path)
        in_project = path in project_state
        in_staging = path in staging_state

        if action == "created":
            if in_project:
                problems.append(
                    f"declared created but existed pre-apply: {path} — "
                    f"likely a concurrent session already landed this file, "
                    f"so the response was authored against a snapshot that "
                    f"predates it; inspect what landed with "
                    f"`git log --oneline -- {path}` on the target branch "
                    f"(or diff the sibling's held branch: "
                    f"`git diff <origin>..bale/<sibling-sid>`), then "
                    f"regenerate the response against the current tree"
                )
            elif not in_staging:
                problems.append(
                    f"declared created but absent from staging: {path}"
                )
            elif staging_state[path] != change["sha256"]:
                problems.append(
                    f"created {path}: staging sha256={staging_state[path][:12]}..."
                    f" manifest={change['sha256'][:12]}..."
                )
        elif action == "deleted":
            if not in_project:
                problems.append(
                    f"declared deleted but absent pre-apply: {path}"
                )
            elif in_staging:
                problems.append(
                    f"declared deleted but still in staging after apply.sh: {path}"
                )
        elif action == "modified":
            if not in_project:
                problems.append(
                    f"declared modified but absent pre-apply: {path}"
                )
            elif not in_staging:
                problems.append(
                    f"declared modified but absent from staging: {path}"
                )
            elif staging_state[path] != change["sha256"]:
                problems.append(
                    f"modified {path}: staging sha256={staging_state[path][:12]}..."
                    f" manifest={change['sha256'][:12]}..."
                )
            elif project_state[path] == staging_state[path]:
                problems.append(
                    f"declared modified but staging matches project (no change): {path}"
                )

    # Catch undeclared changes — apply.sh touched something the manifest
    # didn't authorize. The .bale-manifest.json that run_validation_sh
    # writes is placed AFTER reconciliation (in step 8.5), so it doesn't
    # appear here as a false positive.
    for path in sorted(actual_created - declared_paths):
        problems.append(f"undeclared created in staging: {path}")
    for path in sorted(actual_deleted - declared_paths):
        problems.append(f"undeclared deleted from staging: {path}")
    for path in sorted(actual_modified - declared_paths):
        problems.append(f"undeclared modified in staging: {path}")

    if problems:
        detail = "\n  ".join(problems)
        raise RuntimeError(
            "post-apply.sh staging does not match manifest "
            f"(BALE.md §11 rule 18):\n  {detail}"
        )

    log(
        f"reconciled staging against manifest: "
        f"{len(actual_created)} created, "
        f"{len(actual_deleted)} deleted, "
        f"{len(actual_modified)} modified"
    )


def run_blind_checkpoint(repo: Path, staging: Path, base_sha: str,
                         checkpoint_path: str, sid: str, *,
                         verbose: bool = False,
                         sandbox: bool = True) -> dict:
    """Materialize and run the planner's blind checkpoint from BASE-TREE
    bytes; log a banded section; return
    {"path", "sha256", "exit_code", "output"}.

    The board-6 misunderstanding control (BALE.md §8.5): the executed
    script is `git show <base_sha>:<checkpoint_path>` — the committed
    version at the target tip the session commit is built against —
    NEVER the staging copy, which is the current project state plus the
    response overlay and therefore the worker's post-overlay version
    whenever the response touched it. Consequences, each deliberate:

    - A response that modifies the checkpoint is checked against the
      old one — in-flight self-grading is structurally impossible, not
      policy-refused.
    - An uncommitted working-tree edit to the checkpoint is not honored:
      committed-is-ratified, matching the dangling-config refusal.
    - The rule is staging-strategy-independent: working-tree and
      target-base staging both stage from states that could already
      contain drift; base-tree extraction bypasses both.

    Materialization rule (ratified disposition 5): `git show` emits blob
    bytes only — the exec bit lives in tree metadata and does not
    survive materialization — so this runner BOTH restores the mode
    explicitly (from the tree entry's mode via `git ls-tree`, falling
    back to 0o755) AND invokes via the interpreter (`bash <script>`,
    exactly as run_validation_sh invokes the worker script). Either
    alone satisfies the decision; doing both makes silent non-execution
    impossible by construction. The temp copy lives OUTSIDE staging
    (tempfile.mkdtemp) so it can never collide with the staged tree or
    the §8.4 reconciliation walk, and is removed on the way out.

    Capture and logging mirror run_validation_sh's two paths: verbose
    streams live (stderr merged into stdout) while collecting; default
    captures quietly. Both write to `.bale/logs/<sid>.log` inside a
    banded section — `=== blind checkpoint (<path>, <sha256[:12]>) ===`
    — and close by writing the `=== worker validation.sh ===` band, so
    the two invocations' output is attributed in the log even though
    each is captured on its own and the §7.3 reconciliation parse of the
    WORKER's output never sees checkpoint lines. The bands appear only
    when a checkpoint is configured: an unconfigured project's log stays
    byte-identical to today's.

    Exit-code semantics per script (TARBALL.md §7.5, unchanged): 0 pass,
    1 check failed, 2 the script itself errored. The PASS/HOLD
    derivation that combines this exit code with the worker's is the
    caller's (BALE.md §8.6), outside either script. The returned sha256
    is the hash of the executed base-tree bytes — the value the D4
    telemetry stamp records and the value session C's provenance
    verification will audit after the fact.

    `sandbox` (default on, ADR-0016 position 1: uniform confinement —
    the checkpoint's planner provenance is one merge deep, and
    confinement costs it nothing by contract) wraps the invocation in
    bale_sandbox: writes land only in staging and the session log,
    network off, environment scrubbed. The materialization tempdir is
    passed through read-only — confinement is on writes and network;
    bale-materialized read inputs stay readable — and the deliberate
    absence of the --verbose argv pass-through is untouched (the flag
    below controls streaming around the script, never its argv).

    Raises via fail() when materialization itself breaks (a `git show`
    failure after the dangling pre-check passed means the base tree
    changed mid-apply or git itself errored — both worth stopping for),
    and when the sandbox self-probe refuses (ADR-0016: loud refusal
    naming --no-sandbox, never silent unconfined execution).
    """
    from __main__ import fail, log
    if sandbox:
        import bale_sandbox  # lazy — sibling module, standalone by design

    # Base-tree bytes, binary-exact: hashed and executed as-is, so the
    # subprocess call is direct (text=False) rather than through the
    # __main__ text-mode git helper.
    shown = subprocess.run(
        ["git", "show", f"{base_sha}:{checkpoint_path}"],
        cwd=str(repo), capture_output=True,
    )
    if shown.returncode != 0:
        fail(f"could not materialize the blind checkpoint "
             f"{checkpoint_path!r} from the base tree {base_sha[:7]}: "
             f"{shown.stderr.decode(errors='replace').strip()}")
    script_bytes = shown.stdout
    script_sha = hashlib.sha256(script_bytes).hexdigest()

    # Tree-entry mode for the explicit restore half of disposition 5.
    # ls-tree output: "<mode> blob <sha>\t<path>"; a parse miss falls
    # back to 0o755 — restoring executability is the safe direction, and
    # the interpreter invocation below runs the script regardless.
    mode = 0o755
    ls = subprocess.run(
        ["git", "ls-tree", base_sha, "--", checkpoint_path],
        cwd=str(repo), capture_output=True, text=True,
    )
    if ls.returncode == 0 and ls.stdout.strip():
        tree_mode = ls.stdout.split()[0]
        if tree_mode == "100644":
            mode = 0o644

    tmpdir = tempfile.mkdtemp(prefix="bale-checkpoint-")
    try:
        script = Path(tmpdir) / Path(checkpoint_path).name
        script.write_bytes(script_bytes)
        script.chmod(mode | 0o500)  # owner read+exec at minimum

        log(f"running blind checkpoint {checkpoint_path} "
            f"(base-tree bytes {script_sha[:12]}, {base_sha[:7]}"
            + (", confined" if sandbox else ", UNCONFINED — --no-sandbox")
            + ")"
            + (" (verbose: streaming live)..." if verbose else "..."))

        log_file = repo / ".bale" / "logs" / f"{sid}.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        band = (f"=== blind checkpoint ({checkpoint_path}, "
                f"{script_sha[:12]}) ===")

        if sandbox:
            try:
                bale_sandbox.ensure_verified(log_file)
            except bale_sandbox.SandboxUnavailableError as e:
                fail(str(e))

        if verbose:
            if sandbox:
                proc = bale_sandbox.popen_confined(
                    ["bash", str(script)],
                    staging=staging, log_path=log_file,
                    tmp_passthrough=[Path(tmpdir)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
            else:
                proc = subprocess.Popen(
                    ["bash", str(script)],
                    cwd=str(staging),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                )
            collected: list[str] = []
            assert proc.stdout is not None
            for line in proc.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                collected.append(line)
            returncode = proc.wait()
            merged = "".join(collected)
            with log_file.open("a", encoding="utf-8") as f:
                f.write(f"\n{band}\n")
                f.write(merged)
                f.write(f"\n--- blind checkpoint exit code: {returncode} "
                        f"---\n")
                f.write("\n=== worker validation.sh ===\n")
            return {"path": checkpoint_path, "sha256": script_sha,
                    "exit_code": returncode, "output": merged}

        if sandbox:
            result = bale_sandbox.run_confined(
                ["bash", str(script)],
                staging=staging, log_path=log_file,
                tmp_passthrough=[Path(tmpdir)],
            )
        else:
            result = subprocess.run(
                ["bash", str(script)],
                cwd=str(staging),
                capture_output=True,
                text=True,
            )
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"\n{band}\n")
            f.write(result.stdout)
            if result.stderr:
                f.write("\n--- blind checkpoint stderr ---\n")
                f.write(result.stderr)
            f.write(f"\n--- blind checkpoint exit code: "
                    f"{result.returncode} ---\n")
            f.write("\n=== worker validation.sh ===\n")
        combined = result.stdout + (("\n" + result.stderr)
                                    if result.stderr else "")
        return {"path": checkpoint_path, "sha256": script_sha,
                "exit_code": result.returncode, "output": combined}
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def run_validation_sh(repo: Path, response_dir: Path, staging: Path,
                      manifest: dict, sid: str, *,
                      verbose: bool = False,
                      sandbox: bool = True) -> tuple[int, str]:
    """Copy validation.sh into staging, place .bale-manifest.json for claims
    access, run it, log output, return (exit code, captured output).

    The output element (v0.3.9, B2) is the same text the session log
    receives — stdout+stderr interleaved on the verbose path, stdout plus
    any stderr on the default path — returned so the caller can promote the
    TARBALL.md §7.3 claims-vs-verdict block into the telemetry record
    (bale_report.parse_claim_verdict_block) without re-parsing the
    append-mode session log, whose earlier attempts would make "which
    block?" ambiguous. Both paths already collected the text; this returns
    what was previously dropped.

    Output routing follows BALE.md §8.5 step 4: validation.sh's stdout/stderr
    always land in the session log (`.bale/logs/<sid>.log`); the terminal
    sees them only when `verbose` is set (cmd_apply --verbose). In the
    default (non-verbose) path the run is captured and dumped to the log
    after completion — the walkthrough summary the caller prints carries the
    verdict, and the HOLD banner points at the log for detail. The verbose
    path streams live instead: stderr is merged into stdout (live output is
    interleaved on one stream anyway) and each line is echoed to the terminal
    as it arrives while being collected for the log. Exit-code semantics
    (0 pass / 1 check-failed / 2 script-errored, TARBALL.md §7.5) are
    identical on both paths.

    The §7.4 pass-through (v0.3.35): when `verbose` is set, the script is
    invoked as `bash validation.sh --verbose`, so TARBALL.md §7.4's own
    verbose mode ("prints command output live") engages inside the script,
    not just around it. Forwarded unconditionally on the verbose path —
    the contract doc has specified the flag since the section was written,
    a script that ignores its argv (most of them) is unaffected, and a
    strict script that rejects unknown arguments fails loudly in verbose
    mode only, with the streamed output showing why; re-running without
    --verbose restores the bare invocation. The default (non-verbose)
    invocation stays exactly `bash validation.sh` — byte-identical to
    every prior release. Retry inherits the pass-through for free: it
    reruns this same path with its own --verbose flag. The blind
    checkpoint (run_blind_checkpoint) deliberately does NOT receive the
    flag: it is planner-authored with no §7.4 contract on its argv, and
    its invocation stays stable.

    `sandbox` (default on, ADR-0016) confines the run via
    bale_sandbox: writes land only in staging and the session log,
    network off, environment scrubbed. validation.sh was copied into
    staging above, so no pass-through is needed; the --verbose argv
    pass-through rides inside the confined argv unchanged. On a
    sandbox self-probe refusal this raises via fail() naming
    --no-sandbox — never silent unconfined execution.
    """
    from __main__ import fail, log
    if sandbox:
        import bale_sandbox  # lazy — sibling module, standalone by design
    val_dst = staging / "validation.sh"
    shutil.copy2(response_dir / "validation.sh", val_dst, follow_symlinks=False)
    val_dst.chmod(0o755)

    # Per BALE.md 7.3 — validation.sh reads claims here.
    (staging / ".bale-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
    )

    log("running validation.sh in staging"
        + (" (confined: network off, writes limited to staging + "
           "session log)" if sandbox else " (UNCONFINED — --no-sandbox)")
        + (" (verbose: streaming live)..." if verbose else "..."))

    log_file = repo / ".bale" / "logs" / f"{sid}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    if sandbox:
        try:
            bale_sandbox.ensure_verified(log_file)
        except bale_sandbox.SandboxUnavailableError as e:
            fail(str(e))

    if verbose:
        # Live stream. Merge stderr into stdout so the terminal sees the same
        # interleaving the user would at a real shell, read line by line, echo
        # immediately, and collect for the log. bufsize=1 + text mode gives
        # line-buffered reads; iterating proc.stdout blocks per line until EOF.
        # §7.4 pass-through: the operator's --verbose rides onto the
        # script's own argv (docstring above owns the rationale).
        if sandbox:
            proc = bale_sandbox.popen_confined(
                ["bash", "validation.sh", "--verbose"],
                staging=staging, log_path=log_file,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        else:
            proc = subprocess.Popen(
                ["bash", "validation.sh", "--verbose"],
                cwd=str(staging),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
        collected: list[str] = []
        # proc.stdout is non-None because stdout=PIPE; guard anyway for mypy.
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            collected.append(line)
        returncode = proc.wait()
        merged = "".join(collected)
        with log_file.open("a", encoding="utf-8") as f:
            f.write(f"\n--- validation.sh output ({sid}, verbose: "
                    f"stdout+stderr interleaved) ---\n")
            f.write(merged)
            f.write(f"\n--- validation.sh exit code: {returncode} ---\n")
        return returncode, merged

    # Default: capture, log only, terminal stays quiet.
    if sandbox:
        result = bale_sandbox.run_confined(
            ["bash", "validation.sh"],
            staging=staging, log_path=log_file,
        )
    else:
        result = subprocess.run(
            ["bash", "validation.sh"],
            cwd=str(staging),
            capture_output=True,
            text=True,
        )

    with log_file.open("a", encoding="utf-8") as f:
        f.write(f"\n--- validation.sh stdout ({sid}) ---\n")
        f.write(result.stdout)
        if result.stderr:
            f.write(f"\n--- validation.sh stderr ---\n")
            f.write(result.stderr)
        f.write(f"\n--- validation.sh exit code: {result.returncode} ---\n")

    # stdout carries the check lines and the §7.3 reconciliation block;
    # stderr rides along so a script-error trail (exit 2) is visible to the
    # same consumer. Matches what the log received, minus the framing.
    combined = result.stdout + (("\n" + result.stderr) if result.stderr else "")
    return result.returncode, combined


def build_session_commit(repo: Path, staging: Path, manifest: dict,
                         base_sha: str, message: str) -> str:
    """Build the session commit via git plumbing — never through a checkout.

    ADR-0008: the commit is constructed in a temporary index seeded from the
    integration target's tree (`base_sha`), updated per-manifest-entry with
    content taken from the validated staging copy, written out with
    `write-tree`, and committed with `commit-tree -p base_sha`. Neither the
    user's checkout nor the real index is touched; the only durable side
    effects are loose objects. Used by both PASS and HOLD (BALE.md §8.6) —
    the caller moves the `bale/<sid>` ref to the returned commit and decides
    whether to merge.

    Per-manifest-entry, not tree-level: the manifest is the contract, and the
    commit shape follows its `changes[]` directly (BALE.md §8.6). Files the
    manifest doesn't name keep their `base_sha` content even when the staging
    copy (built from the working tree, §8.3) diverges from the target branch.

    Mode bits: the entry mode is derived from the staging copy's own mode —
    `100755` when any execute bit is set, `100644` otherwise, `120000` for a
    symlink — so an executable restored by the response's `apply.sh`
    (TARBALL.md §5.1.1) lands executable in the commit. stage_response
    preserves mode bits going into staging; this is the matching half on the
    way into the object database. Blob content for regular files is hashed
    with `--path=<repo path>` so the attribute-driven conversions `git add`
    would apply at that path apply here too.

    A delete whose path isn't in the base tree is a no-op
    (`--force-remove` tolerates it), mirroring the old `git rm
    --ignore-unmatch` tolerance for an already-absent file.

    Raises subprocess.CalledProcessError on any git failure; the caller owns
    the integration-lock release/hold decision for that case. Returns the new
    commit sha.
    """
    from __main__ import log
    fd, index_path = tempfile.mkstemp(prefix="bale-index-")
    os.close(fd)
    os.unlink(index_path)  # git creates the index file itself
    env = {**os.environ, "GIT_INDEX_FILE": index_path}

    def pgit(args: list[str], *, input_text: Optional[str] = None) -> str:
        r = subprocess.run(
            ["git", *args], cwd=str(repo), env=env,
            capture_output=True, text=True, input=input_text,
        )
        if r.returncode != 0:
            raise subprocess.CalledProcessError(
                r.returncode, ["git", *args], r.stdout, r.stderr)
        return r.stdout

    try:
        pgit(["read-tree", base_sha])
        for change in manifest["changes"]:
            path = change["path"]
            action = change["action"]
            if action in ("created", "modified"):
                src = staging / path
                if src.is_symlink():
                    mode = "120000"
                    blob = pgit(["hash-object", "-w", "--stdin"],
                                input_text=os.readlink(src)).strip()
                else:
                    mode = "100755" if (src.stat().st_mode & 0o111) else "100644"
                    blob = pgit(["hash-object", "-w", f"--path={path}",
                                 "--", str(src)]).strip()
                # Three-argument --cacheinfo form: the comma-joined
                # single-argument form can't carry a path containing a comma.
                pgit(["update-index", "--add", "--cacheinfo",
                      mode, blob, path])
            elif action == "deleted":
                pgit(["update-index", "--force-remove", "--", path])
        tree = pgit(["write-tree"]).strip()
        commit = pgit(["commit-tree", tree, "-p", base_sha,
                       "-m", message]).strip()
        log(f"built session commit {commit[:7]} (tree {tree[:7]}, "
            f"parent {base_sha[:7]}) via temporary index")
        return commit
    finally:
        try:
            os.unlink(index_path)
        except FileNotFoundError:
            pass
