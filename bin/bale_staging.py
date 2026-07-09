"""bale_staging — apply-pipeline staging, reconciliation, and worktree helpers.

This module owns the mechanical helpers of the apply pipeline that operate on
the staging tree and the working tree: the apply-time `bash -n` pre-flight on
the response's shell scripts (`check_response_shell_syntax`), the response-vs-
manifest presence/sha256/path-safety checks (`verify_files_against_manifest`),
building the staging tree and running the response's `apply.sh` over it
(`stage_response`), the post-`apply.sh` reconciliation of staging against the
manifest (`reconcile_staging_against_manifest`, with its private tree-snapshot
helper `_walk_tree_sha256`), running the response's `validation.sh` in staging
(`run_validation_sh`), and building the session commit from the validated
staging content via git plumbing (`build_session_commit`, which replaced the
checkout-consuming `apply_changes_to_worktree` when ADR-0008 landed in
v0.3.5). Extracted from `bin/bale`'s section 16
("Apply: helpers") in v0.1.3 to continue bringing that section back under
CODE.md §4.2's size threshold — the third extraction sibling after
`bale_config` (v0.0.4) and `bale_validate` (v0.1.2), using the same sibling-
import mechanism.

Behavior-preserving move: the functions keep the signatures and call sites they
had in `bin/bale`. The six public entry points (`check_response_shell_syntax`,
`verify_files_against_manifest`, `stage_response`,
`reconcile_staging_against_manifest`, `run_validation_sh`,
`build_session_commit`) are pulled back into `bin/bale`'s namespace via
`from bale_staging import ...`, so the apply-pipeline callers still write them
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

See claude/context/bale-internals.md for how this module sits next to `bin/bale`,
`bale_config`, and `bale_validate`.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Optional


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


def stage_response(repo: Path, response_dir: Path, staging: Path) -> None:
    """Build the staging tree: cp project, overlay files/, run apply.sh.

    BALE.md section 8.3. After cp-overlay, apply.sh runs from response_dir
    with cwd=staging — it handles deletes and any other manifest-declared
    file operations the cp mirror can't express. The post-stage
    reconciliation in reconcile_staging_against_manifest() (BALE.md §8.4,
    §11 rule 18) verifies the resulting tree matches the manifest exactly,
    so apply.sh can't quietly touch undeclared files.

    Raises RuntimeError on apply.sh non-zero exit (BALE.md §11 rule 17).
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

    # cp project state into staging, minus .bale/ (BALE.md 8.3 step 2 spec).
    # Also skip the staging directory itself if it lives inside the repo —
    # otherwise iterdir() yields it (we just created it) and we'd copy it
    # into itself.
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
    log("running apply.sh in staging...")
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
                                       manifest: dict) -> None:
    """Verify the post-apply.sh staging tree matches the manifest exactly.

    BALE.md §8.4 and §11 rule 18: every created/deleted/modified path in
    staging vs the pre-apply project state must correspond to a manifest
    entry of the matching action and sha256, with no undeclared writes,
    deletes, or modifications. Fails with a clear message naming every
    discrepancy so the user can find them.

    Pre-apply state is the project tree itself, skipping `.bale/` (per
    BALE.md 8.3 step 2 — never copied into staging) and the staging dir
    if it lives inside the repo (the user-set `--staging-dir` case;
    default `<repo>/.bale/staging/` is already covered by the `.bale/`
    skip). Both walks also skip `.git/`: the path-safety rule (§11 rule
    14) already prohibits `.git/`-prefixed paths in the manifest, so
    anything there can't be declared anyway, and the cp preserves it
    byte-for-byte — walking it just costs sha256 time on every apply
    against a mature repo. The two snapshots use the same walk function
    so the baseline is symmetric with what stage_response actually
    copied (modulo the symmetric `.git/` skip).

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
    # Build symmetric snapshots. Skip `.bale/` in the project (never copied
    # into staging) and the staging dir itself if it's inside the repo.
    # Skip `.git/` in both — see the docstring rationale (rule 14 prohibits
    # `.git/` paths in the manifest, the cp preserves it byte-for-byte).
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
                    f"declared created but existed pre-apply: {path}"
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


def run_validation_sh(repo: Path, response_dir: Path, staging: Path,
                      manifest: dict, sid: str, *, verbose: bool = False) -> int:
    """Copy validation.sh into staging, place .bale-manifest.json for claims
    access, run it, log output, return exit code.

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
    """
    from __main__ import log
    val_dst = staging / "validation.sh"
    shutil.copy2(response_dir / "validation.sh", val_dst, follow_symlinks=False)
    val_dst.chmod(0o755)

    # Per BALE.md 7.3 — validation.sh reads claims here.
    (staging / ".bale-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
    )

    log("running validation.sh in staging"
        + (" (verbose: streaming live)..." if verbose else "..."))

    log_file = repo / ".bale" / "logs" / f"{sid}.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)

    if verbose:
        # Live stream. Merge stderr into stdout so the terminal sees the same
        # interleaving the user would at a real shell, read line by line, echo
        # immediately, and collect for the log. bufsize=1 + text mode gives
        # line-buffered reads; iterating proc.stdout blocks per line until EOF.
        proc = subprocess.Popen(
            ["bash", "validation.sh"],
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
        return returncode

    # Default: capture, log only, terminal stays quiet.
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

    return result.returncode


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
