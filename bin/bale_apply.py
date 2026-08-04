"""bale_apply — the `bale apply` path (response-tarball validation + integration).

The seventh sibling module after `bale_config` (v0.0.4), `bale_validate`
(v0.1.2), `bale_staging` (v0.1.3), `bale_rollback` (v0.2.0), `bale_report`
(v0.2.6), and `bale_pack` (v0.3.12). Extracted from `bin/bale`'s sections
16-18 in v0.3.13, behavior-preserving: the apply pre-flight helpers (the
ADR-0008 narrow dirty-on-target trio, the walkthrough prompt, the
responds_to peek, non-interactive-mode resolution, the bailout and
clarification handlers, the per-session staging-path layout, and the
generated-artifact denial), the apply pipeline proper, and `cmd_apply`
with its inspection surface. Revert, retry, unlock, and handoff are their
own commands and stay in `bin/bale`; retry re-enters the pipeline through
this module's public surface.

Public surface consumed by `bin/bale`: `cmd_apply` (CLI dispatch);
`apply_pipeline`, `record_rejected_attempt`, `resolve_no_interact`,
`refuse_dirty_on_target`, and `resolve_target_branch` (cmd_retry — the
pipeline's second front door; the first two dropped their leading
underscore at extraction, since what `bin/bale` imports by name is this
module's public surface); and `default_staging_root` +
`default_staging_dir` (`bale status`'s gather, so the path status reports
is by construction the path apply uses). Shared `bin/bale` helpers are
imported lazily from `__main__` inside the functions that use them, the
same idiom every other sibling uses. Sibling-owned entry points
(`bale_config`, `bale_staging`'s staging/commit machinery,
`bale_validate`'s response/diagnostics validators, `bale_report`'s
apply-side renderers, telemetry, and json-mode state) are imported lazily
from their owning modules instead — `bin/bale` has already loaded them,
so the imports resolve from sys.modules. Dependency direction is one-way:
`bin/bale` imports this module; `bale_pack` never imports the apply path,
and this module never imports `bale_pack` (the per-response
`validation.sh` asserts the pack-side direction).

Sections:
  1. Apply: helpers                                      (~line    55)
  2. Apply: pipeline                                     (~line   630)
  3. Apply                                               (~line  1540)
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


# ---------------------------------------------------------------------------
# 1. Apply: helpers
# ---------------------------------------------------------------------------

def tracked_dirty_paths(repo: Path) -> list[str]:
    """Paths with tracked modifications — staged or unstaged — i.e. every
    `git status --porcelain` line whose XY status is not `??` (untracked).

    ADR-0008's narrow pre-flight cares only about tracked dirt: untracked
    files are invisible to a branch ref, so moving the ref under a checkout
    that merely has untracked files cannot desynchronize the checkout from
    its own branch. (An untracked file that would collide with merged
    content is caught later, by `git merge --ff-only`'s own safety checks
    on the fast-forward path.)
    """
    from __main__ import git  # lazy — see module docstring
    r = git(["status", "--porcelain"], cwd=repo)
    paths: list[str] = []
    for line in r.stdout.splitlines():
        if not line.strip() or line.startswith("??"):
            continue
        paths.append(line[3:].strip())
    return paths


def resolve_target_branch(repo: Path, sid: str) -> str:
    """The branch this session's integration merges into (ADR-0008).

    Reads the session's recorded origin branch —
    `.bale/sessions/<sid>/origin_branch`, stamped at pack time since v0.3.5
    (persist_pack_session) and re-stamped by apply's §8.2 — so the target is
    fixed by the session, independent of whatever branch the user's checkout
    happens to be on. That independence is what makes the §8.1 step 5 narrow
    rule's cases meaningful: "switch branches" is a valid remedy, and an
    apply run from an unrelated dirty branch proceeds without touching the
    checkout.

    The stamp is required — stamped at pack since v0.3.5 and re-stamped
    by apply's §8.2. A missing or empty stamp is a hard refusal naming
    the remedy; sessions predating the stamp (and detached-checkout
    packs, which write none) are no longer applyable. A stamp naming a
    branch that no longer exists is likewise refused, with its own
    remedies.
    """
    from __main__ import fail, git  # lazy — see module docstring
    stamp = repo / ".bale" / "sessions" / sid / "origin_branch"
    b = stamp.read_text().strip() if stamp.is_file() else ""
    if not b:
        fail(f"session {sid} has no recorded origin branch (missing or "
             f"empty stamp at {stamp}). The stamp is required — written "
             f"at pack since v0.3.5 — and sessions predating it are no "
             f"longer applyable. `bale unlock {sid}` and re-pack against "
             f"the branch this session should merge into.")
    exists = git(["rev-parse", "--verify", "--quiet",
                  f"refs/heads/{b}"], cwd=repo, check=False)
    if exists.returncode != 0:
        fail(f"the session's recorded target branch {b!r} no longer "
             f"exists. Recreate it, or `bale unlock {sid}` and "
             f"re-pack against the branch you mean to target.")
    return b


def refuse_dirty_on_target(repo: Path, target_branch: str) -> None:
    """The ADR-0008 narrow pre-flight (BALE.md §8.1 step 5, §11 row 8),
    replacing the blanket clean-tree requirement.

    Refuses only the one genuinely entangled case: the checkout is on the
    target branch AND has tracked changes — moving the ref under a dirty
    checkout of that same branch would desynchronize the user's tree from
    its own branch (git would report the inverse diff as local changes).
    Every other state proceeds: another branch or detached (integration
    never touches the checkout), or on-target but tracked-clean (the
    checkout is fast-forwarded to the new ref at merge, §8.8).
    """
    from __main__ import current_branch, fail  # lazy — see module docstring
    if current_branch(repo) != target_branch:
        return
    dirty = tracked_dirty_paths(repo)
    if dirty:
        fail(
            f"working tree has tracked changes while checked out on the "
            f"integration target {target_branch!r} — merging would move "
            f"the branch ref under a dirty checkout of that same branch "
            f"and desynchronize it. Stash or commit the changes, or "
            f"switch to another branch, then re-run:\n  "
            + "\n  ".join(dirty)
        )


# --- Apply walkthrough (BALE.md §8.7) ----------------------------------------
#
# The walkthrough is the interactive step that resolves a freshly-applied bale
# branch into a terminal git state. Both validation outcomes (PASS, HOLD) print
# the same summary block and then prompt for an action; the action set differs
# per state. Factored into helpers so the summary can be re-built/inspected
# without re-running the apply pipeline (a v0.3 polish item) and so the
# prompt's TTY/EOF handling stays out of apply_pipeline's already-long body.
# The summary builder itself (format_walkthrough_summary) lives in the sibling
# bale_report module since v0.2.6, with the rest of the end-of-command
# reporting surface; what stays here is the prompt.

def prompt_walkthrough_action(state: str, *, no_interact: bool = False,
                              no_interact_source: str = "") -> str:
    """Prompt the user for the terminal walkthrough action.

    Returns one of "merge" (PASS only), "inspect" (HOLD only), or "revert"
    (both states). The default selected on Enter / EOF / non-TTY matches
    BALE.md §8.7's piped-mode contract:

      - PASS path → default "merge" (auto-merge into origin).
      - HOLD path → default "inspect" (exit non-zero with branch held).

    `no_interact` (BALE.md §5.4 / §8.7) skips the prompt and takes the same
    default, but *logs* the bypassed prompt's decision and its source
    (`no_interact_source`, e.g. "--no-interact flag" or the bale.toml key
    and layer) — the audit trail the interactive prompt would otherwise be.
    The plain non-TTY branch below stays a silent default on purpose: it is
    the unchanged legacy path for runs that did not opt in.

    `state` is "PASS" or "HOLD"; any other value is a caller bug.
    """
    from __main__ import log  # lazy — see module docstring
    if state not in ("PASS", "HOLD"):
        raise ValueError(f"prompt_walkthrough_action: bad state {state!r}")
    default = "merge" if state == "PASS" else "inspect"

    if no_interact:
        log(f"walkthrough prompt skipped ({no_interact_source}): taking "
            f"default action {default!r} ({state} default)")
        return default

    if not sys.stdin.isatty():
        # Piped/non-interactive: take the default silently. The summary
        # already printed above carries the context the user needs to
        # interpret the exit code.
        return default

    if state == "PASS":
        print(
            "  [Enter/m] merge into origin (default)   "
            "[r] revert — discard branch"
        )
    else:
        print(
            "  [Enter/i] inspect — hold for review (default)   "
            "[r] revert — discard branch"
        )
    try:
        ans = input("  > ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        # ^C or stdin closed mid-prompt: treat as default. Don't fail the
        # whole apply for an interrupted prompt; the user can re-run.
        print()
        return default

    if ans == "":
        return default
    if ans in ("r", "revert"):
        return "revert"
    if state == "PASS" and ans in ("m", "merge"):
        return "merge"
    if state == "HOLD" and ans in ("i", "inspect"):
        return "inspect"
    # Unrecognized inputs fall back to the default rather than re-prompting.
    # The user can ^C and re-run apply if they typo'd; re-prompt loops in a
    # 2-option surface add code without much benefit.
    print(f"  (unrecognized {ans!r}; defaulting to {default})")
    return default


def _peek_responds_to(tarball_path: Path) -> str:
    """Read `responds_to` from a response tarball's manifest, pre-pipeline.

    The multi-open resolution path (ADR-0007): when the registry holds
    more than one open session, cmd_apply needs the response's own
    `responds_to` to know which session log to wire and which sid the
    pipeline runs against — before apply_pipeline extracts anything.
    This reads exactly one member (response-NNN/manifest.json) from the
    archive in memory; nothing is extracted to disk, and every check
    here is re-run in full by the pipeline's own pre-flight. Failures
    are fatal with the same voice the pipeline would use — a tarball
    this helper can't read was never going to survive pre-flight.
    """
    from __main__ import fail  # lazy — see module docstring
    try:
        with tarfile.open(tarball_path, "r:gz") as tf:
            member = None
            for m in tf.getmembers():
                parts = Path(m.name).parts
                if (m.isfile() and len(parts) == 2
                        and parts[0].startswith("response-")
                        and parts[1] == "manifest.json"):
                    member = m
                    break
            if member is None:
                fail("tarball has no response-NNN/manifest.json; cannot "
                     "resolve which open session it responds to")
            extracted = tf.extractfile(member)
            if extracted is None:
                fail(f"could not read {member.name} from the tarball")
            raw = extracted.read()
    except (tarfile.TarError, OSError) as e:
        fail(f"tarball is unreadable: {e}")
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        fail(f"manifest.json in the tarball is not valid JSON: {e}")
    responds_to = manifest.get("responds_to")
    if not isinstance(responds_to, str) or not responds_to.strip():
        fail("manifest.responds_to is missing or empty; cannot resolve "
             "which open session this response answers")
    return responds_to


def resolve_no_interact(repo: Path, cfg: dict, flag: bool) -> tuple[bool, str]:
    """Resolve whether non-interactive apply mode is active, and its source.

    Shared by cmd_apply and cmd_retry (BALE.md §5.4 / §8.7). Returns
    (active, source): `active` says whether the mode is on; `source` is the
    human-readable provenance string the pipeline logs beside every bypassed
    prompt ("" when the mode is off). Precedence: the per-invocation
    --no-interact flag wins by being checked first; otherwise the merged
    config's apply.no_interact enables the mode for every invocation, with
    the supplying layer named via apply_bool_source. There is deliberately
    no per-invocation "force interactive" negation over a config true — if
    that need is real it earns a flag later (see the v0.2.5 session notes).
    """
    import bale_config  # lazy — see module docstring
    if flag:
        return True, "no-interact via --no-interact flag"
    if bale_config.get_apply_no_interact(cfg):
        layer = bale_config.apply_bool_source(repo, "no_interact") or "config"
        return True, f"no-interact via apply.no_interact=true ({layer} bale.toml)"
    return False, ""


def _apply_bailout(repo: Path, response_dir: Path, manifest: dict, sid: str,
                   tarball_basename: str, *,
                   invoked_by: str = "apply") -> int:
    """Apply-time handler for `response_kind: "bailout"` per TARBALL.md §5.6.3.

    This is the branch apply_pipeline takes when the manifest declares a
    bailout. We:

      1. Verify the bailout's mandatory artifacts (handoff.md and
         diagnostics.json) — §5.6.1.
      2. Preserve manifest + handoff.md + diagnostics.json under
         `.bale/sessions/<sid>/` so `bale handoff`'s lineage chase can
         find them later. (Normal-PASS sessions wipe their session dir;
         bailouts keep theirs, since the next handoff session may chase
         this one for repeat-bailout warning.)
      3. Close the session in the ADR-0006 registry — the session is
         consumed. The user's explicit next action is `bale handoff
         <tarball>`, which opens a fresh session against a new sid.
      4. Write the telemetry record (with the diagnostics embed and the
         clarification stamp, v0.3.23), then print the §5.6.3 banner
         (`print_bailout_banner` does the layout) — record before
         banner so the banner's §8.9 telemetry row reports the write.
      5. Under json output mode (v0.2.8), emit the one-line machine
         report — outcome "bailout", verdict and merge null since no
         validation ran and no walkthrough decided anything.
      6. Return 0. No `apply.sh`, no staging, no validation, no branch.

    No `git_head_at_apply` / `origin_branch` / `staging_path` metadata is
    written — no branch is created so there's nothing for `bale revert`
    to chase. (`bale revert` against a bailout sid will fall through the
    `no branch` guard, which is correct: a bailout has nothing to
    revert.)
    """
    from __main__ import (  # lazy — see module docstring
        close_session,
        fail,
        log,
        read_session_scope,
    )
    from bale_validate import validate_diagnostics  # lazy — see module docstring
    from bale_report import (  # lazy — see module docstring
        build_telemetry_attempt,
        emit_json_line,
        format_apply_json,
        json_mode,
        print_bailout_banner,
        read_clarification_summary,
        write_telemetry_record,
    )
    handoff_path = response_dir / "handoff.md"
    diagnostics_path = response_dir / "diagnostics.json"
    if not handoff_path.is_file():
        fail("bailout response is missing handoff.md (TARBALL.md §5.6.1 — "
             "required when response_kind=bailout)")
    if not diagnostics_path.is_file():
        fail("bailout response is missing diagnostics.json (TARBALL.md §5.6.1 — "
             "required when response_kind=bailout)")

    # Parse + schema-validate diagnostics. The schema is intentionally loose
    # (TARBALL.md §5.8: additionalProperties:true at the top level, so future
    # additive fields don't reject historical aggregation) — but the universal
    # envelope (session_id, bail_trigger enum, the verdict-bearing arrays,
    # tool_calls_summary, what_would_save_next_time) is now enforced rather
    # than only checked for parseability. An unparseable or off-shape file is
    # the kind of thing aggregation tooling later would silently skip, which
    # is worse than failing here.
    try:
        diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"diagnostics.json is not valid JSON: {e}")
    validate_diagnostics(diagnostics)
    log("diagnostics.json schema validation passed")

    # Preserve artifacts for the lineage chase + later inspection.
    sessions_dir = repo / ".bale" / "sessions" / sid
    sessions_dir.mkdir(parents=True, exist_ok=True)
    (sessions_dir / "response-manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
    )
    shutil.copy2(handoff_path, sessions_dir / "handoff.md", follow_symlinks=False)
    shutil.copy2(diagnostics_path, sessions_dir / "diagnostics.json",
                 follow_symlinks=False)
    log(f"bailout artifacts preserved under {sessions_dir}")

    # Close the session in the registry. The bailed session is consumed;
    # the next user action is `bale handoff <tarball>` (which itself opens
    # the follow-up session via the pack-style acquisition). The bailout's
    # session dir stays in place — small, valuable for the chase, easy to
    # remove by hand if the user decides the lineage is done — which is
    # exactly why the registry keys openness on the `open` marker
    # (removed here) rather than on the directory's existence.
    close_session(repo, sid)
    log(f"bailout {sid}: session closed")

    # Telemetry record (v0.3.9, B2 — BALE.md §8.9). A bailout consumes its
    # session, so it is an apply close and it records: validation null
    # (nothing ran), changes[] empty by §5.6.2, and — the pieces that make
    # this branch worth recording — the feedback block verbatim, whose
    # self_reported.budget_pressure="bailed" is exactly the longitudinal
    # signal board 5 aggregates, plus (v0.3.23, board 5 D1) the parsed,
    # already-schema-validated diagnostics embedded verbatim and the
    # close-time clarification stamp every closing event carries. Written
    # after close_session so a telemetry failure (already non-fatal)
    # cannot even reorder the session's real state changes, and BEFORE
    # the banner (v0.3.23, D7.1) so the banner can carry the §8.9
    # telemetry row its siblings carry.
    telemetry_rel = write_telemetry_record(
        repo, sid, build_telemetry_attempt(
            outcome="bailout", command=invoked_by,
            tarball=tarball_basename, manifest=manifest,
            scope=read_session_scope(repo, sid),
            log_path=f".bale/logs/{sid}.log",
            diagnostics=diagnostics,
            clarification=read_clarification_summary(repo, sid),
        ))
    if telemetry_rel:
        log(f"telemetry: recorded {telemetry_rel}")

    print_bailout_banner(manifest, handoff_path, tarball_basename,
                         telemetry=telemetry_rel)

    if json_mode():
        # Terminal json report (v0.2.8), emitted after the §5.6.3 banner
        # (which json mode routed to stderr) so the stdout line a consumer
        # waits on is the last thing this command does.
        emit_json_line(format_apply_json(
            outcome="bailout", sid=sid,
            log_path=repo / ".bale" / "logs" / f"{sid}.log",
            telemetry=telemetry_rel,
        ))
    return 0


def _apply_clarification(repo: Path, manifest: dict, sid: str) -> int:
    """Apply-time handler for `response_kind: "clarification"` per TARBALL.md
    §5.9.3 — the branch apply_pipeline takes when the manifest declares a
    clarification: blocking intent-gap questions, nothing to apply.

    Structurally _apply_bailout's sibling, with two deliberate differences:

    - **No artifact checks here.** The clarification's payload is the
      manifest's own questions[] block, which validate_response_manifest
      already schema-validated and shape-checked (non-empty, four fields per
      entry) before the pipeline forked — there is no handoff.md /
      diagnostics.json analog to verify.
    - **The lock is NOT cleared — the session stays open.** A bailout
      consumes its session (the next step is `bale handoff` against a fresh
      sid); a clarification suspends it. The architect answers the questions
      in the worker's chat and the session continues to a normal response
      applied against this same sid. If the gap invalidates the request's
      framing, the user runs `bale unlock` and repacks — their call, not
      ours.

    What this handler does:

      1. Preserve the manifest under `.bale/clarifications/<sid>/NNN.json`
         (NOT under `.bale/sessions/<sid>/`, which the eventual normal-PASS
         merge wipes — the clarification record must outlive the session it
         suspended, since its whole longitudinal value is aggregation across
         *completed* sessions, TARBALL.md §5.9.4). NNN increments so a
         session that clarifies more than once keeps every round. The
         preserved copy carries a `preserved_at` sidecar key stamped at
         write time (v0.3.27): mtime survives normal use but not every
         copy/restore path, so the record holds its own timestamp, which
         read_clarification_summary prefers over mtime. Pre-v0.3.27
         records have no stamp and read via the mtime fallback — no
         backfill.
      2. Print the §5.9.3 banner (`print_clarification_banner`).
      3. Under json output mode, emit the one-line machine report — outcome
         "clarification", verdict and merge null since no validation ran and
         no walkthrough decided anything.
      4. Return 0. No `apply.sh`, no staging, no validation, no branch, no
         lock change.

    No `git_head_at_apply` / `origin_branch` / `staging_path` metadata is
    written — same as the bailout, nothing was applied so there is nothing
    for `bale revert` to chase.
    """
    from __main__ import log  # lazy — see module docstring
    from bale_report import (  # lazy — see module docstring
        emit_json_line,
        format_apply_json,
        json_mode,
        print_clarification_banner,
    )
    # Preserve the manifest for the aggregation surface. Sequence numbering
    # keeps repeat clarifications within one session distinct; the count of
    # existing entries + 1 is race-free enough for a single-user CLI.
    clar_dir = repo / ".bale" / "clarifications" / sid
    clar_dir.mkdir(parents=True, exist_ok=True)
    seq = len(list(clar_dir.glob("*.json"))) + 1
    record_path = clar_dir / f"{seq:03d}.json"
    # Sidecar key, not a wrapper (v0.3.27): the record stays a preserved
    # manifest — every reader of questions[] keeps its shape, and
    # read_clarification_summary's fallback chain (preserved_at, then
    # mtime, then null) covers stampless pre-v0.3.27 records unchanged.
    # A shallow copy keeps the in-memory manifest pristine for the
    # banner below.
    record = dict(manifest)
    record["preserved_at"] = datetime.now(timezone.utc).isoformat(
        timespec="seconds")
    record_path.write_text(
        json.dumps(record, indent=2) + "\n", encoding="utf-8",
    )
    log(f"clarification manifest preserved at {record_path}")

    print_clarification_banner(manifest)

    # Deliberately no close_session(repo, sid): the session stays open in
    # the ADR-0006 registry (§5.9.3 step 4). `bale status` will keep
    # reporting the sid as an open session, which is correct — it *is*
    # still awaiting its applicable response.
    log(f"clarification {sid}: session stays open in the registry")

    if json_mode():
        # Terminal json report, emitted after the §5.9.3 banner (which json
        # mode routed to stderr) so the stdout line a consumer waits on is
        # the last thing this command does.
        emit_json_line(format_apply_json(
            outcome="clarification", sid=sid,
            log_path=repo / ".bale" / "logs" / f"{sid}.log",
        ))
    return 0


# --- Per-session default staging (v0.3.3) ------------------------------------
#
# The default apply staging path is per-session: <repo>/.bale/staging/<sid>,
# with .bale/staging itself demoted to a parent ("the staging root"). The
# shared default was the last surface concurrent open sessions (ADR-0006 /
# ADR-0007) collided on: with sessions A and B both open, B's apply removed
# A's live HOLD staging as "stale". These three helpers are the single
# source for the layout — the apply pipeline (BALE.md §8.3) and the status
# gather both resolve through them, so the path status reports is by
# construction the path apply uses.

def default_staging_root(repo: Path) -> Path:
    """The parent directory per-session staging lives under (BALE.md §8.3).

    Pre-v0.3.3 this exact path WAS the staging directory; a bare project
    tree found here now is a leftover of that layout, and
    clean_staging_root removes it (no session under the per-sid layout
    can own it).
    """
    return repo / ".bale" / "staging"


def default_staging_dir(repo: Path, sid: str) -> Path:
    """The default staging directory for one session (BALE.md §8.3).

    Only the default: a --staging-dir override bypasses the root layout
    entirely and keeps its own refuse-if-exists contract.
    """
    return default_staging_root(repo) / sid


def clean_staging_root(repo: Path, root: Path, sid: str) -> None:
    """Remove the staging-root entries the apply for `sid` may clear.

    Called by the apply pipeline at the 8.3 stage step, default path
    only, before stage_response builds `root/<sid>` fresh. The rule is
    ownership by *open* sessions (the ADR-0006 registry):

      - an entry that is a directory named for an open session OTHER
        than `sid` is a live sibling's staging (its HOLD under
        inspection, or its apply mid-flight) — never touched. This is
        the clobber window the per-session layout closes.
      - `sid`'s own directory is removed: rebuilding this session's
        staging is correct on a retry of an errored stage and on a HOLD
        the user is moving past (re-invoking apply is the signal) —
        the surviving two thirds of the old shared-path trichotomy.
      - everything else is stale and removed with a log line: closed
        sessions' preserved-for-inspection leftovers (exactly what the
        next apply removed under the shared path — merge/revert keep
        the durable record in git), and any bare pre-v0.3.3 tree at the
        root itself, whose top-level entries are project files and
        directories no open session's name matches.

    Failure to remove is fatal (fail()), matching the old stale-staging
    removal: proceeding would hand stage_response a dirty tree its
    exists()-precondition rejects anyway. A missing root is a no-op; a
    root that exists as a non-directory is itself stale junk and is
    removed.
    """
    from __main__ import fail, log, open_sessions  # lazy — see module docstring
    if not root.exists():
        return
    if not root.is_dir():
        log(f"removing non-directory at staging root {root}")
        try:
            root.unlink()
        except OSError as e:
            fail(f"could not remove stale staging entry {root}: {e}")
        return
    keep = set(open_sessions(repo)) - {sid}
    removed: list[str] = []
    for entry in sorted(root.iterdir(), key=lambda p: p.name):
        if entry.is_dir() and not entry.is_symlink() and entry.name in keep:
            continue  # a sibling open session's staging — never touched
        try:
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)
            else:
                entry.unlink()
        except OSError as e:
            fail(f"could not remove stale staging entry {entry}: {e}")
        removed.append(entry.name)
    if removed:
        shown = ", ".join(removed[:5])
        if len(removed) > 5:
            shown += f", ... ({len(removed)} entries total)"
        log(f"cleaned staging root {root}: removed stale {shown}")


# --- Generated-artifact denial (v0.3.4) ---------------------------------------
#
# Response tarballs ship source, never generated artifacts — bytecode,
# dependency trees, build output (TARBALL.md §5.1 carries the builder-side
# rule; BALE.md §8.1 step 13 / §11 row 20 is the enforcement). The deny
# list is deliberately conservative — short, obvious names, not a
# heuristic — because the two failure costs are asymmetric: a false
# refusal costs the worker a repack, while a false pass costs nothing new
# (the architect's review still exists). `.bale/` paths are an obvious
# offender too but are NOT duplicated here: path safety (BALE.md §11
# row 14) already rejects them, and one rejection per cause keeps the
# refusal messages unambiguous.

# Directory names denied as any non-final path component (a file INSIDE
# one of these is generated; a file merely NAMED like one — `scripts/build`,
# say — is not, which is the conservative side of the line).
GENERATED_ARTIFACT_DIRS = frozenset({
    "__pycache__", "node_modules", "dist", "build",
})

# Basename globs denied on the final path component.
GENERATED_ARTIFACT_FILE_GLOBS = ("*.pyc", "*.pyo")


def generated_artifact_paths(paths: Iterable[str]) -> list[str]:
    """Return the sorted subset of `paths` that name generated artifacts.

    A path offends when any non-final component is in
    GENERATED_ARTIFACT_DIRS, or its basename matches a
    GENERATED_ARTIFACT_FILE_GLOBS pattern. Pure — no filesystem access;
    the inputs are manifest `changes[].path` strings, which path safety
    (is_path_safe) has already normalized expectations for. Empty input
    (bailout/clarification manifests) returns empty.
    """
    offending: set[str] = set()
    for p in paths:
        parts = Path(p).parts
        if any(part in GENERATED_ARTIFACT_DIRS for part in parts[:-1]):
            offending.add(p)
            continue
        if parts and any(fnmatch.fnmatch(parts[-1], pat)
                         for pat in GENERATED_ARTIFACT_FILE_GLOBS):
            offending.add(p)
    return sorted(offending)


# ---------------------------------------------------------------------------
# 2. Apply: pipeline
# ---------------------------------------------------------------------------

def apply_pipeline(repo: Path, tarball_path: Path, locked_sid: str,
                    staging_override: Optional[str], *,
                    dry_run: bool = False, verbose: bool = False,
                    no_interact: bool = False,
                    no_interact_source: str = "",
                    invoked_by: str = "apply",
                    allow_out_of_scope: Optional[list[str]] = None) -> int:
    """The apply pipeline proper: extract, validate, stage, run
    validation.sh, commit-or-hold. Shared between cmd_apply (after lock
    + clean-tree guards) and cmd_retry (after _discard_hold_state has
    cleaned up a HOLDed attempt).

    Expects, on entry:
      - lock held on `locked_sid`
      - the ADR-0008 narrow pre-flight already passed: no tracked changes
        while checked out on the session's target branch
        (refuse_dirty_on_target; not required when dry_run — a dry-run
        touches neither the worktree nor .bale/). Any other checkout
        state, dirty or not, is fine: integration never consumes the
        checkout.
      - no bale/<sid> branch (revert/retry deleted it if needed)
      - logging already wired to the session log file

    `dry_run` (cmd_apply --dry-run) runs only the read-only front half —
    extract, syntax pre-flight, manifest schema, responds_to, the
    generated-artifact denial, and the presence/sha256/path-safety
    verification — then prints the plan and
    returns 0 before the session stamp, staging, branch, validation run, or
    commit. No git or filesystem side effects. `verbose` (cmd_apply
    --verbose) is forwarded to run_validation_sh, which streams
    validation.sh output live to the terminal in addition to the session log
    (BALE.md §8.5 step 4); it has no effect under dry_run, which never runs
    validation.sh.

    `no_interact` / `no_interact_source` (BALE.md §5.4 / §8.7; --no-interact
    or apply.no_interact in bale.toml, resolved by the caller) thread to the
    pipeline's two prompt points — prompt_walkthrough_action and the
    post_apply_pass run_hook — which skip their prompts and log the decision
    taken plus `no_interact_source`. No effect under dry_run, which returns
    before either prompt. All keywords default off, so callers that pass
    nothing (and older call shapes) keep the interactive behavior unchanged.

    Under json output mode (cmd_apply --json; bale_report.enable_json_mode
    already rebound the human streams to stderr by the time this runs) each
    terminal reporting point below — dry-run, bailout, merge, inspect,
    revert — additionally emits the one-line machine report via
    emit_json_line(format_apply_json(...)). The human banners still render
    (landing on stderr); the emission is a pass-through addition gated on
    bale_report.json_mode(), so nothing threads through this signature —
    cmd_retry enables the mode the same way since v0.3.14 (`bale retry
    --json`, flag parity) and rides the same gated emission points.

    `allow_out_of_scope` (v0.3.10, board 2; cmd_apply --allow-out-of-scope,
    repeatable) names changes[] paths the own-scope drift gate below should
    admit despite lying outside the session's declared scope. Per
    invocation only — there is deliberately no config key — and any drift
    path NOT named still refuses. None/empty means no override. cmd_retry
    accepts and threads the same flag since v0.3.14 (flag parity), passing
    whatever THIS retry invocation named — never state carried from a
    prior attempt — so a retry that needs the override re-states it, and
    one that omits it hits the drift gate like an un-overridden apply.

    `invoked_by` (v0.3.9, B2) names the command for the telemetry record's
    attempts[].command field — "apply" (default) or "retry" from cmd_retry.
    Each terminal outcome below (merge, inspect, revert; plus the bailout
    fork) also appends an attempt to claude/telemetry/<sid>.json via
    build_telemetry_attempt + write_telemetry_record (BALE.md §8.9),
    renders the returned path as one summary row, and passes it to
    format_apply_json's additive `telemetry` key. Dry-run and clarification
    write no record: a dry-run has no outcome, and a clarification suspends
    rather than closes its session — the eventual normal response records.

    Returns the apply exit code: 0 on PASS (or a clean dry-run), 1 on HOLD.
    """
    from __main__ import (  # lazy — see module docstring
        _discard_hold_state,
        acquire_integration_lock,
        close_session,
        current_branch,
        fail,
        git,
        log,
        open_sessions,
        read_session_scope,
        release_integration_lock,
        run_hook,
        scope_covers_path,
        scope_path,
        scope_paths_intersect,
    )
    import bale_config  # lazy — see module docstring
    from bale_staging import (  # lazy — see module docstring
        build_session_commit,
        check_response_shell_syntax,
        reconcile_staging_against_manifest,
        run_blind_checkpoint,
        run_validation_sh,
        stage_response,
        verify_files_against_manifest,
    )
    from bale_validate import validate_response_manifest  # lazy — see module docstring
    from bale_report import (  # lazy — see module docstring
        build_telemetry_attempt,
        emit_json_line,
        format_apply_json,
        format_dry_run_report,
        format_scope_drift_refusal,
        format_summary_block,
        format_walkthrough_summary,
        json_mode,
        read_clarification_summary,
        write_telemetry_record,
    )
    # The session log path as the json reports cite it (absolute) — the
    # same file cmd_apply/cmd_retry already wired set_log_file to.
    session_log = repo / ".bale" / "logs" / f"{locked_sid}.log"

    # Extract and validate the tarball into a temp dir.
    with tempfile.TemporaryDirectory() as tmpdir:
        # 8.1 step 1: tar integrity.
        try:
            tf = tarfile.open(tarball_path, "r:gz")
        except (tarfile.TarError, OSError) as e:
            fail(f"tarball is unreadable: {e}")

        try:
            # Defensive scan for unsafe paths inside the archive itself.
            for member in tf.getmembers():
                name = member.name
                if name.startswith("/") or ".." in Path(name).parts:
                    fail(f"tarball contains unsafe path: {name}")
            # 8.1 step 2: extract.
            tf.extractall(tmpdir)
        finally:
            tf.close()

        # The archive must have exactly one top-level response-NNN/ directory.
        entries = [p for p in Path(tmpdir).iterdir()]
        if len(entries) != 1 or not entries[0].is_dir():
            fail(f"tarball must contain exactly one top-level directory; "
                 f"found {[e.name for e in entries]}")
        response_dir = entries[0]
        if not response_dir.name.startswith("response-"):
            fail(f"top-level directory must be named response-NNN/, "
                 f"got {response_dir.name}/")

        # 8.1 step 12: required files present.
        for required in ("manifest.json", "apply.sh", "validation.sh"):
            if not (response_dir / required).is_file():
                fail(f"missing required file in tarball: {required}")

        # Pre-flight syntax check on the response's shell deliverables.
        # The required-files check above guarantees they exist.
        check_response_shell_syntax(response_dir)
        log("apply.sh and validation.sh syntax checks passed")

        # 8.1 step 3: read and schema-validate the manifest.
        try:
            manifest = json.loads((response_dir / "manifest.json").read_text())
        except (OSError, json.JSONDecodeError) as e:
            fail(f"manifest.json is not valid JSON: {e}")
        validate_response_manifest(manifest)
        log("manifest schema validation passed")

        # 8.1 step 6 / §11 row 9, read against the ADR-0006 registry: the
        # sid the response names must be an open session. With several
        # sessions open (ADR-0007), cmd_apply already resolved
        # `locked_sid` from the manifest's own responds_to via
        # _peek_responds_to, so this equality re-checks the full pipeline
        # extraction against the peek — defense in depth; with one open
        # session it is the same check it always was.
        if manifest["responds_to"] != locked_sid:
            fail(f"manifest.responds_to={manifest['responds_to']!r} does not "
                 f"match the open session {locked_sid!r}")

        # 8.1 step 7 / §11 row 19 (ADR-0007): cross-session scope
        # collision. Whatever this response's worker did, its changes may
        # not land on files ANOTHER open session has in scope — bale's
        # overlay is whole-file replacement, so a later apply authored
        # against a stale snapshot would silently clobber the sibling's
        # work and the --no-ff merge would land clean. This is the real
        # guard; the pack-time gate is only the conservative early one.
        # Own-scope drift (changes outside this session's own scope with
        # no sibling claiming the path) remains policy, caught at review
        # (BALE.md §2.2, TARBALL.md §8) — unchanged by ADR-0007. With at
        # most one session open there are no siblings and this is a
        # no-op; bailout and clarification manifests carry empty
        # changes[], so they pass vacuously. Runs under --dry-run too —
        # read-only, and a dry-run should predict the rejection.
        sibling_sids = [s for s in open_sessions(repo) if s != locked_sid]
        if sibling_sids and manifest.get("changes"):
            collisions: list[tuple[str, list[str]]] = []
            for sib_sid in sibling_sids:
                sib_scope = read_session_scope(repo, sib_sid)
                hit_paths = sorted({
                    change["path"] for change in manifest["changes"]
                    if any(scope_paths_intersect(scope_path(change["path"]),
                                                 entry)
                           for entry in sib_scope)
                })
                if hit_paths:
                    collisions.append((sib_sid, hit_paths))
            if collisions:
                detail = "; ".join(
                    f"{sib_sid} claims {', '.join(paths)}"
                    for sib_sid, paths in collisions
                )
                fail(
                    f"[REJECT] cross-session scope collision (ADR-0007): "
                    f"changes[] lands on paths in another open session's "
                    f"scope — {detail}. Apply or close the sibling "
                    f"session(s) first (`bale apply <its tarball>`, `bale "
                    f"revert <sid>`, or `bale unlock`), then re-run this "
                    f"apply."
                )
            log(f"cross-session scope collision check passed against "
                f"{len(sibling_sids)} sibling session(s): "
                f"{', '.join(sibling_sids)}")

        # 8.1 step 14 / §11 row 22 (v0.3.10, board 2): own-scope drift
        # gate — the drift-to-contract conversion of the stay-in-the-lane
        # rule, sited beside its step-7 sibling above. The 008 audit's
        # finding 2: two sessions can each drift into the same UNCLAIMED
        # file, pass every ADR-0007 declared-vs-declared gate, and the
        # second whole-file overlay clobbers the first under a clean
        # --no-ff merge. So: every changes[] path must lie inside THIS
        # session's own declared scope (the pack-time include set,
        # sessions/<sid>/scope.json — read conservatively as whole-tree
        # when missing/unreadable, which also keeps default whole-tree
        # packs entirely outside this gate's blast radius). Created paths
        # are rejected the same as modified — the clobber scenario is
        # precisely two sessions creating the same unclaimed file.
        # --allow-out-of-scope (per-invocation, repeatable; no config
        # key) admits exactly the named paths; any other drift still
        # refuses. The refusal is pre-staging: no git side effects, the
        # session stays open, and the remedies are a regenerated
        # response, a deliberate per-path override, or an unlock+repack.
        # Manifest-only, so it runs under --dry-run (same report, no
        # telemetry — no outcome occurred) and passes vacuously for
        # bailout and clarification manifests, whose changes[] is empty.
        # session_scope read here doubles as the telemetry input the
        # terminal actions promote (BALE.md §8.9) — read once, before
        # any terminal action's cleanup can wipe it.
        session_scope = read_session_scope(repo, locked_sid)
        allow_norm = sorted({scope_path(p)
                             for p in (allow_out_of_scope or [])})
        drift_paths = sorted({
            scope_path(change["path"])
            for change in manifest.get("changes", []) or []
            if not scope_covers_path(session_scope, change["path"])
        })
        overridden_paths = [p for p in drift_paths if p in allow_norm]
        refused_paths = [p for p in drift_paths if p not in allow_norm]
        unused_allow = [p for p in allow_norm if p not in drift_paths]
        if unused_allow:
            # Named but not drifting: harmless (in-scope or not in the
            # change set at all), but say so — a silently ignored
            # override flag is exactly the surprise the logging rules
            # exist to prevent.
            log(f"--allow-out-of-scope named path(s) with no matching "
                f"out-of-scope change: {', '.join(unused_allow)} "
                f"(no effect)")
        if refused_paths:
            scope_rendered = (", ".join(session_scope) if session_scope
                              else "(read-only session — empty scope; "
                                   "lands nothing)")
            log(f"[REJECT] own-scope drift (BALE.md §11 row 22): "
                f"{len(refused_paths)} changes[] path(s) outside session "
                f"{locked_sid}'s declared scope — "
                f"{', '.join(refused_paths)}; declared scope: "
                f"{scope_rendered}")
            # A drift refusal is a distinct, dispatchable outcome — it
            # does NOT ride the generic fail() path: the human rendering
            # and the json line come from bale_report (wiring only here),
            # telemetry records the attempt (except under --dry-run,
            # which has no outcome), and the return keeps the session
            # open with the committed state untouched. The cmd_apply
            # SystemExit wrapper never fires (no SystemExit), so the
            # attempt is not double-recorded as "rejected".
            telemetry_rel: Optional[str] = None
            if not dry_run:
                telemetry_rel = write_telemetry_record(
                    repo, locked_sid, build_telemetry_attempt(
                        outcome="scope-drift-refused", command=invoked_by,
                        tarball=tarball_path.name, manifest=manifest,
                        scope=session_scope,
                        overridden_paths=overridden_paths,
                        log_path=f".bale/logs/{locked_sid}.log",
                    ))
            print(format_scope_drift_refusal(
                sid=locked_sid,
                scope=session_scope,
                refused=refused_paths,
                overridden=overridden_paths,
                telemetry=telemetry_rel,
                dry_run=dry_run,
            ))
            if json_mode():
                # Emitted on this exit-1 path deliberately, like held/
                # reverted: an orchestrating operator dispatches on the
                # outcome key instead of parsing prose.
                emit_json_line(format_apply_json(
                    outcome="scope-drift-refused", sid=locked_sid,
                    log_path=session_log,
                    telemetry=telemetry_rel,
                    drift={
                        "out_of_scope_paths": refused_paths,
                        "session_scope": session_scope,
                        "overridden_paths": overridden_paths,
                    },
                ))
            return 1
        if overridden_paths:
            # force=True: an admitted out-of-scope path is an override
            # event of the same species as the --force bypasses — the
            # FORCE: journal line is the audit trail the session log
            # keeps of it (the telemetry stamp at the terminal action is
            # the durable copy). For a read-only session (empty scope,
            # v0.3.15) the line says so: the operator is landing changes
            # from a session packed to land none, and the audit trail
            # should record that that is exactly what they overrode.
            scope_note = (", ".join(session_scope) if session_scope
                          else "read-only session — empty scope; the "
                               "override lands changes from a session "
                               "packed to land none")
            log(f"own-scope drift admitted by --allow-out-of-scope: "
                f"{', '.join(overridden_paths)} (declared scope: "
                f"{scope_note})", force=True)
        # No pass-path log line beyond the reads above: like the
        # generated-artifact denial below, a clean pass adds no output,
        # keeping accepted-tarball output byte-identical to v0.3.9.

        # 8.1 step 13 / §11 row 20: generated-artifact denial. Response
        # tarballs ship source, never generated artifacts (TARBALL.md
        # §5.1); a manifest-only check like the scope gate above, so it
        # sits with the other manifest checks before the response_kind
        # forks (bailout/clarification carry empty changes[] and pass
        # vacuously) and runs under --dry-run, which should predict the
        # rejection. Rejection here is pre-staging by construction —
        # nothing below 8.2 has run — and adds no output on the pass
        # path, keeping accepted-tarball output byte-identical.
        offending = generated_artifact_paths(
            change["path"] for change in manifest.get("changes", []))
        if offending:
            fail(
                f"[REJECT] generated artifacts in changes[]: "
                f"{', '.join(offending)}. Response tarballs ship source, "
                f"not generated artifacts (TARBALL.md §5.1) — bytecode, "
                f"dependency trees, and build output are rebuilt by the "
                f"project's toolchain. Remove them and repack the response."
            )

        # Bailout fork — TARBALL.md §5.6.3. response_kind="bailout" means no
        # files, no apply.sh effect, no validation.sh run; the response is a
        # signal to package a fresh session via `bale handoff <tarball>`.
        # _apply_bailout owns the artifact checks, the session-dir
        # preservation, the §5.6.3 banner, and the lock release. The early
        # branch is what keeps the bailout path free of staging side
        # effects — by the time the normal path's verify_files / stage /
        # reconcile runs, response_kind=="normal" is guaranteed.
        #
        # The `.get(..., "normal")` default keeps v0.0.5-shaped manifests
        # (the ones without a response_kind key — including this very CLI
        # session's own response) on the normal path. Validation upstream
        # guarantees the value is in the response_kind enum when present
        # (response-manifest.schema.json).
        if manifest.get("response_kind", "normal") == "bailout":
            if dry_run:
                # Don't run _apply_bailout under dry-run — it preserves the
                # session dir, prints the live §5.6.3 banner, and releases
                # the lock, all of which are side effects. Report the plan
                # instead.
                print(format_dry_run_report(manifest, locked_sid,
                                            response_kind="bailout"))
                log("dry-run: bailout response; no side effects performed")
                if json_mode():
                    # No validation ran and no walkthrough decided anything,
                    # so verdict and merge are null (format_apply_json).
                    emit_json_line(format_apply_json(
                        outcome="dry-run", sid=locked_sid,
                        log_path=session_log,
                    ))
                return 0
            return _apply_bailout(
                repo, response_dir, manifest, locked_sid, tarball_path.name,
                invoked_by=invoked_by,
            )

        # Clarification fork — TARBALL.md §5.9.3, the bailout fork's sibling.
        # response_kind="clarification" means blocking intent-gap questions
        # ride in the manifest (already schema-validated and shape-checked
        # above); nothing is applied, and — the one deliberate divergence
        # from the bailout — the session stays OPEN: _apply_clarification
        # does not clear the lock, because the architect answers in the
        # worker's chat and this same sid receives the follow-up response.
        # The early branch keeps the clarification path free of staging side
        # effects, exactly as the bailout branch above does.
        if manifest.get("response_kind", "normal") == "clarification":
            if dry_run:
                # Don't run _apply_clarification under dry-run — it preserves
                # the manifest under .bale/clarifications/ and prints the
                # live §5.9.3 banner, both side effects. Report the plan
                # instead.
                print(format_dry_run_report(manifest, locked_sid,
                                            response_kind="clarification"))
                log("dry-run: clarification response; no side effects performed")
                if json_mode():
                    # No validation ran and no walkthrough decided anything,
                    # so verdict and merge are null (format_apply_json).
                    emit_json_line(format_apply_json(
                        outcome="dry-run", sid=locked_sid,
                        log_path=session_log,
                    ))
                return 0
            return _apply_clarification(repo, manifest, locked_sid)

        # 8.1 steps 8, 9, 10: file presence, sha256, path safety (incl.
        # .baleignore match per BALE.md §11 rule 14).
        verify_files_against_manifest(repo, response_dir, manifest)
        log("file presence, sha256, and path safety verified")

        # --dry-run stops here: every check that doesn't touch the worktree
        # or .bale/ has now run and passed. Report the plan and return before
        # the session stamp, staging, branch creation, validation run, and
        # commit. A passing dry-run means the tarball would be accepted for a
        # real apply.
        if dry_run:
            print(format_dry_run_report(manifest, locked_sid,
                                        response_kind="normal"))
            log("dry-run: validated; no git side effects performed")
            if json_mode():
                # Plan only: validation.sh never ran and no walkthrough
                # decided anything, so verdict and merge are null.
                emit_json_line(format_apply_json(
                    outcome="dry-run", sid=locked_sid, log_path=session_log,
                ))
            return 0

        # 8.2 stamp session. The integration target is the session's own
        # (ADR-0008): resolve_target_branch reads the required pack-time
        # origin_branch stamp — a missing or empty stamp was already a
        # hard refusal at the §8.1 step 5 pre-flight. The recorded base is
        # the TARGET branch's tip, not the checkout's HEAD; they coincide
        # only when the user happens to be on the target. The session
        # branch, the session commit, and the merge are all built against
        # this base.
        sessions_dir = repo / ".bale" / "sessions" / locked_sid
        sessions_dir.mkdir(parents=True, exist_ok=True)
        origin_branch = resolve_target_branch(repo, locked_sid)
        base_sha = git(["rev-parse", f"refs/heads/{origin_branch}"],
                       cwd=repo).stdout.strip()
        (sessions_dir / "git_head_at_apply").write_text(base_sha + "\n")
        (sessions_dir / "origin_branch").write_text(origin_branch + "\n")
        (sessions_dir / "response-manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8",
        )
        head_now = git(["rev-parse", "HEAD"], cwd=repo).stdout.strip()
        # Resolve the staging strategy (BALE.md §8.3 step 2) from the
        # merged config here, ahead of the divergence note below, since
        # the note's claim about what validation will exercise depends on
        # it. Re-resolved per invocation rather than threaded from
        # cmd_apply/cmd_retry — both callers already run merged_config for
        # search paths, the re-read is two small files, and resolving at
        # stage time is what makes retry inherit the strategy structurally
        # (same config, same strategy, identical staged content).
        staging_cfg = bale_config.merged_config(repo)
        staging_strategy = bale_config.get_staging_strategy(staging_cfg)
        staging_untracked = bale_config.get_staging_untracked_inputs(staging_cfg)
        # Blind checkpoint (board 6 session A, BALE.md §8.5): resolve the
        # [validation] base key from the same merged config — project
        # layer only by construction (disposition 1; merged_config never
        # inherits the section from global). Resolved here, beside the
        # staging strategy, because the dangling check below needs
        # base_sha in hand — and refusing HERE is still pre-staging: no
        # staging tree exists, no branch exists, and the session stays
        # open with no git side effects beyond the session-dir stamps
        # every apply writes.
        checkpoint_path = bale_config.get_validation_base(staging_cfg)
        if checkpoint_path is not None:
            probe = git(["cat-file", "-e", f"{base_sha}:{checkpoint_path}"],
                        cwd=repo, check=False)
            if probe.returncode != 0:
                # Configured-but-dangling = loud refusal (never a silent
                # skip — a broken oracle reference is a bug by hard rule).
                # Committed-is-ratified is deliberate: a working-tree-only
                # checkpoint the planner has not committed is not yet the
                # project's oracle.
                fail(f"[REJECT] blind checkpoint missing at the base tree: "
                     f"bale.toml [validation] base names "
                     f"{checkpoint_path!r}, but {origin_branch}'s tip "
                     f"({base_sha[:7]}) has no committed file at that "
                     f"path. A working-tree-only checkpoint is not yet "
                     f"the project's oracle (committed-is-ratified). "
                     f"Remedies: commit the checkpoint at the named path, "
                     f"or clear the key via `bale config init`.")
            log(f"blind checkpoint configured: {checkpoint_path} "
                f"(bale.toml [validation] base, project layer; "
                f"base-tree bytes will run)")
        if staging_strategy != "working-tree":
            log(f"staging strategy: {staging_strategy} "
                f"(bale.toml [staging]; default is working-tree)")
        if head_now != base_sha:
            if staging_strategy == "target-base":
                log(f"note: checkout HEAD ({head_now[:7]}) differs from "
                    f"the target branch tip ({base_sha[:7]}); "
                    f"staging.strategy=target-base materializes the "
                    f"target tip's tree, so validation exercises the "
                    f"same content the commit lands")
            else:
                # Default-strategy semantics are deliberately unchanged
                # (§8.3 copies the working tree — untracked
                # build/dependency state has to ride into staging for
                # validation to run). When the checkout has diverged from
                # the target branch, that means validation.sh exercises
                # the checkout's content while the commit itself is built
                # per-manifest-entry against the target base. Say so
                # rather than let the mismatch pass silently.
                log(f"note: checkout HEAD ({head_now[:7]}) differs from the "
                    f"target branch tip ({base_sha[:7]}); staging copies the "
                    f"working tree, so validation runs against the checkout's "
                    f"content while the commit is built against "
                    f"{origin_branch}'s tip")

        # 8.3 stage. Default is <repo>/.bale/staging/<sid> — per-session
        # since v0.3.3 — so the tree lives inside the already-gitignored
        # .bale/ directory and concurrent open sessions (ADR-0006/0007)
        # cannot collide on it. The old shared default's "pre-existing
        # staging is unambiguously stale" trichotomy was sound under
        # single-session semantics and false under multi-open: with A and
        # B both open, A can sit in HOLD (staging present, awaiting
        # inspection) while B's apply runs, and B would have removed A's
        # live staging. clean_staging_root keeps the two per-sid legs of
        # that reasoning (retry of an errored stage; a HOLD this session
        # is moving past) and scopes them to `locked_sid`'s own directory,
        # removes root entries no open session owns (closed sessions'
        # preserved-for-inspection leftovers, bare pre-v0.3.3 trees), and
        # never touches a sibling open session's directory. The `bale
        # revert` path has its own cleanup, driven by the staging_path
        # stamped below. A user-specified --staging-dir, by contrast, is
        # the user's directory, taken verbatim (no <sid> suffix), resolved
        # relative to cwd, and refused rather than removed if it exists —
        # unchanged semantics; two open sessions both overriding to the
        # same directory is the user's collision to own (BALE.md §8.3).
        if staging_override is None:
            staging = default_staging_dir(repo, locked_sid)
            clean_staging_root(repo, default_staging_root(repo), locked_sid)
        else:
            staging = Path(staging_override).resolve()
            if staging.exists():
                fail(f"staging directory already exists: {staging}. "
                     f"Remove it or pass a different --staging-dir.")
        # Record staging path under the session dir so `bale revert` can
        # clean it up later. Written before stage_response so a partial
        # stage that errors out still leaves a trail for revert to follow.
        (sessions_dir / "staging_path").write_text(str(staging) + "\n")
        try:
            staging_baseline = stage_response(
                repo, response_dir, staging,
                strategy=staging_strategy,
                untracked_inputs=staging_untracked,
                base_sha=base_sha,
            )
        except Exception as e:
            shutil.rmtree(staging, ignore_errors=True)
            fail(f"failed to stage response: {e}")
        log(f"staged into {staging}")

        # 8.4 reconcile the post-apply.sh staging tree against the manifest
        # (BALE.md §11 rule 18). Runs before branch creation so a failure
        # leaves no git side effects — wipe staging, exit non-zero. The
        # baseline is stage_response's pre-overlay snapshot under
        # target-base staging, and None (working-tree walk, historical
        # behavior) under the default.
        try:
            reconcile_staging_against_manifest(repo, staging, manifest,
                                               baseline=staging_baseline)
        except Exception as e:
            shutil.rmtree(staging, ignore_errors=True)
            fail(str(e))

        # 8.5: create bale/<sid> branch at the target base (never checked
        # out — ADR-0008; the ref is moved onto the plumbing-built session
        # commit after validation).
        sid_branch = f"bale/{locked_sid}"
        try:
            git(["branch", sid_branch, base_sha], cwd=repo)
        except subprocess.CalledProcessError as e:
            fail(f"could not create branch {sid_branch}: "
                 f"{e.stderr or e.stdout or e}")
        log(f"created branch {sid_branch} at {origin_branch} tip "
            f"({base_sha[:7]})")

        # Blind checkpoint first (BALE.md §8.5, board 6): the planner's
        # misunderstanding control frames what follows in the log, its
        # separately-captured invocation keeps the §7.3 reconciliation
        # parse of the WORKER's output untouched, and a checkpoint that
        # errors (exit 2) is surfaced before the worker's longer run
        # spends its budget. Both scripts ALWAYS run — a checkpoint FAIL
        # does not skip the worker (a checkpoint FAIL beside a worker
        # PASS is precisely the misunderstanding-with-calibrated-worker
        # signal the dual stream exists to surface), and the worker's
        # run below is unconditional.
        checkpoint_result = None
        if checkpoint_path is not None:
            checkpoint_result = run_blind_checkpoint(
                repo, staging, base_sha, checkpoint_path,
                locked_sid, verbose=verbose)
            log(f"blind checkpoint exit code: "
                f"{checkpoint_result['exit_code']} ({checkpoint_path})")

        # Run validation.sh in staging. The captured output feeds the
        # telemetry record's §7.3 claim/verdict promotion (v0.3.9, B2).
        exit_code, val_output = run_validation_sh(
            repo, response_dir, staging, manifest,
            locked_sid, verbose=verbose)
        log(f"validation.sh exit code: {exit_code}")

        # The D4 telemetry stamp for every validated attempt this apply
        # records (BALE.md §8.9): key presence = post-epoch; configured
        # false = the known-zero form; when the checkpoint ran, the
        # per-source state/exit plus the executed base-tree bytes' hash.
        # stamp_matched is null until session C's provenance stamp
        # exists to verify against (requests carry no stamp yet).
        if checkpoint_result is None:
            checkpoint_stamp: dict = {"configured": False}
        else:
            checkpoint_stamp = {
                "configured": True,
                "state": ("PASS" if checkpoint_result["exit_code"] == 0
                          else "HOLD"),
                "exit_code": checkpoint_result["exit_code"],
                "script": {"path": checkpoint_path,
                           "sha256": checkpoint_result["sha256"]},
                "stamp_matched": None,
            }

        # Telemetry inputs (v0.3.9, B2): session_scope was read at the
        # own-scope drift gate above — once, before any terminal action's
        # cleanup can wipe .bale/sessions/<sid>/ — and is reused by the
        # terminal actions' telemetry calls below, alongside the
        # overridden_paths the gate computed (v0.3.10).

        # 8.6 commit-or-hold + 8.7 walkthrough — checkout-free (ADR-0008).
        # Both validation outcomes build the session commit via plumbing
        # (build_session_commit: temporary index seeded from the base tree,
        # per-manifest-entry updates from staging, write-tree/commit-tree)
        # and move bale/<sid> onto it. PASS proceeds to the merge decision;
        # HOLD stops there — the committed branch, inert because nothing
        # has it checked out, IS the inspection surface, alongside the
        # preserved per-sid staging directory. The user's checkout is never
        # switched, applied to, or committed through.
        #
        # The ADR-0006 integration lock guards this window (§8.6–§8.8): from
        # the commit build below through the terminal action's git work,
        # bale is mutating refs (bale/<sid>, and on merge the target branch
        # — plus, in the clean-on-target case, a fast-forward of the user's
        # checkout), and concurrent integrations (reachable since ADR-0007's
        # pack gate landed) serialize here. Released explicitly at each
        # terminal action once its git work is done — and deliberately NOT
        # from a finally: an abnormal exit inside the window (a git
        # failure, a crash) leaves the ref work possibly half-done, and a
        # held lock naming the holder is the honest signal of that state.
        # The acquire-time failure message is the recovery path (stale-lock
        # story, ADR-0006). The one exception is the commit build itself:
        # if it raises, no ref has moved and the checkout was never
        # touched, so the lock releases before the fail — nothing is
        # mid-mutation.
        acquire_integration_lock(repo, locked_sid)
        commit_msg = f"[bale {locked_sid}] {manifest['summary']}"
        try:
            session_commit = build_session_commit(
                repo, staging, manifest, base_sha, commit_msg)
            # Guarded ref move: bale/<sid> was created at base_sha in 8.5;
            # anything else there means outside interference — refuse
            # atomically rather than clobber.
            git(["update-ref", f"refs/heads/{sid_branch}",
                 session_commit, base_sha], cwd=repo)
        except subprocess.CalledProcessError as e:
            release_integration_lock(repo)
            fail(f"could not build the session commit for {sid_branch}: "
                 f"{e.stderr or e.stdout or e}")
        state = "PASS" if exit_code == 0 else "HOLD"
        if checkpoint_result is not None:
            # PASS requires BOTH exit codes 0 (BALE.md §8.6); the
            # envelope vocabulary stays PASS/HOLD — additive posture —
            # with attribution carried everywhere the outcome renders.
            if checkpoint_result["exit_code"] != 0:
                state = "HOLD"
        if state == "PASS":
            log(f"committed changes to {sid_branch} "
                f"({session_commit[:7]}; checkout untouched)")
        elif checkpoint_result is None:
            log(f"validation FAILED (exit={exit_code}); held as commit "
                f"{session_commit[:7]} on {sid_branch} — inspect with "
                f"`git diff {origin_branch}..{sid_branch}`; checkout "
                f"untouched")
        else:
            # Attribute the HOLD per source (board 6 D2): the remedy
            # differs by which script objected — and a checkpoint exit 2
            # means the PLANNER's artifact broke, not the worker's.
            cp_exit = checkpoint_result["exit_code"]
            cp_desc = ("PASS" if cp_exit == 0 else
                       "errored (exit 2) — the planner's checkpoint "
                       "itself errored; inspect the checkpoint script"
                       if cp_exit == 2 else f"HOLD (exit {cp_exit})")
            wk_desc = ("PASS" if exit_code == 0
                       else f"HOLD (exit {exit_code})")
            log(f"HOLD — blind checkpoint: {cp_desc} · worker "
                f"validation: {wk_desc}; held as commit "
                f"{session_commit[:7]} on {sid_branch} — inspect with "
                f"`git diff {origin_branch}..{sid_branch}`; checkout "
                f"untouched")

        # 8.7 walkthrough — print summary, prompt for terminal action.
        # Both PASS and HOLD go through the same summary path so the user
        # sees the same shape regardless of outcome (only the prompt
        # action set and the default differ).
        print(format_walkthrough_summary(
            sid=locked_sid,
            origin_branch=origin_branch,
            sid_branch=sid_branch,
            state=state,
            exit_code=exit_code,
            manifest=manifest,
            response_dir=response_dir,
            staging=staging,
            repo=repo,
            checkpoint=checkpoint_stamp if checkpoint_result is not None
            else None,
        ))
        action = prompt_walkthrough_action(
            state, no_interact=no_interact,
            no_interact_source=no_interact_source,
        )
        log(f"walkthrough action: {action}")

        # 8.8 terminal actions. Merge (PASS only), inspect (HOLD only),
        # revert (both states; currently stubbed — see below).
        if action == "merge":
            # PASS → merge into origin, tag the applied sid, delete the
            # bale branch, clean up session dir + lock, fire the hook.
            # Checkout-free (ADR-0008): the merge commit is built with
            # plumbing — a two-parent commit-tree whose first parent is the
            # old target tip and whose tree is the session commit's tree,
            # exactly the topology `git merge --no-ff` produces — and the
            # target ref is advanced without going through any checkout of
            # the target branch (git refuses to check one out in a second
            # worktree anyway, when the user is sitting on it).
            #
            # Two guards, both refuse-and-preserve: if the target moved
            # during this apply, the session commit's parent is stale and
            # merging would silently drop the new tip's content from the
            # merge tree — refuse. And the ref advance itself is
            # compare-and-swap (update-ref with the expected old value /
            # --ff-only), so a race inside the window refuses rather than
            # clobbers. Either refusal leaves the session commit on
            # bale/<sid> and the session open — recoverable with
            # `bale retry <tarball>` or `bale revert <sid>` — and since no
            # ref moved and the checkout was never touched, the lock
            # releases before the fail.
            cur_target_sha = git(["rev-parse", f"refs/heads/{origin_branch}"],
                                 cwd=repo).stdout.strip()
            if cur_target_sha != base_sha:
                release_integration_lock(repo)
                fail(f"target branch {origin_branch!r} moved during this "
                     f"apply ({base_sha[:7]} → {cur_target_sha[:7]}); "
                     f"refusing to merge a commit built against the old "
                     f"tip. The session commit is held on {sid_branch} and "
                     f"the session is open — `bale revert {locked_sid}` to "
                     f"discard, then re-pack against the new tip.")
            tree_sha = git(["rev-parse", f"{session_commit}^{{tree}}"],
                           cwd=repo).stdout.strip()
            merge_commit = git(
                ["commit-tree", tree_sha, "-p", base_sha,
                 "-p", session_commit, "-m", f"Merge bale {locked_sid}"],
                cwd=repo).stdout.strip()
            if current_branch(repo) == origin_branch:
                # The checked-out-target case, clean by pre-flight: advance
                # the ref THROUGH the checkout with a fast-forward merge, so
                # ref, index, and working tree move together under git's own
                # safety checks (a mid-pipeline tracked edit or a colliding
                # untracked file refuses here instead of desynchronizing).
                try:
                    git(["merge", "--ff-only", merge_commit], cwd=repo)
                except subprocess.CalledProcessError as e:
                    release_integration_lock(repo)
                    fail(f"could not fast-forward the checkout on "
                         f"{origin_branch} to the merge commit: "
                         f"{e.stderr or e.stdout or e}\nThe session commit "
                         f"is held on {sid_branch} and the session is open "
                         f"— resolve what git reports above (an untracked "
                         f"file colliding with the merge is the common "
                         f"case: move it aside), then `bale retry "
                         f"<tarball>`, or `bale revert {locked_sid}`.")
                log(f"fast-forwarded checkout on {origin_branch} to merge "
                    f"commit {merge_commit[:7]}")
                merged_note = "checkout fast-forwarded"
            else:
                try:
                    git(["update-ref", f"refs/heads/{origin_branch}",
                         merge_commit, cur_target_sha], cwd=repo)
                except subprocess.CalledProcessError as e:
                    release_integration_lock(repo)
                    fail(f"could not advance {origin_branch!r} to the merge "
                         f"commit: {e.stderr or e.stdout or e}\nThe session "
                         f"commit is held on {sid_branch} and the session "
                         f"is open — `bale retry <tarball>` or `bale revert "
                         f"{locked_sid}`.")
                log(f"advanced {origin_branch} to merge commit "
                    f"{merge_commit[:7]} without touching the checkout "
                    f"(currently on {current_branch(repo)})")
                cur_after = current_branch(repo)
                merged_note = ("detached checkout untouched"
                               if cur_after == "HEAD"
                               else f"checkout on {cur_after!r} untouched")
            git(["tag", f"applied/{locked_sid}", merge_commit], cwd=repo)
            # -D, not -d: branch -d checks merged-into-HEAD, and HEAD may be
            # an unrelated checkout now. The merge commit and the tag above
            # already anchor the session's history.
            git(["branch", "-D", sid_branch], cwd=repo)
            close_session(repo, locked_sid)
            shutil.rmtree(sessions_dir, ignore_errors=True)
            release_integration_lock(repo)
            log(f"tagged applied/{locked_sid}, closed session, "
                f"deleted {sid_branch}")

            # post_apply_pass hook. Silent no-op when not configured. Prompts
            # the user before invoking; a decline is logged and silent. The
            # hook runs after the merge so a hook-side failure can't unwind
            # bale's primary work — at this point the session is durably
            # applied and tagged.
            #
            # merged_config layers global under project so a single config
            # call covers both `<install>/user/bale.toml` and `<repo>/bale.toml`.
            run_hook(repo, bale_config.merged_config(repo), "post_apply_pass",
                     locked_sid, no_interact=no_interact,
                     no_interact_source=no_interact_source)

            # Telemetry record (v0.3.9, B2 — BALE.md §8.9). The merge is a
            # closing event, so the attempt carries the close-time
            # clarification stamp (v0.3.23, board 5 D1) — the HOLD/refusal
            # attempts above deliberately do not: the stamp lives on the
            # closing attempt only.
            telemetry_rel = write_telemetry_record(
                repo, locked_sid, build_telemetry_attempt(
                    outcome="applied", command=invoked_by,
                    tarball=tarball_path.name, manifest=manifest,
                    scope=session_scope,
                    overridden_paths=overridden_paths,
                    validation_state=state,
                    validation_exit_code=exit_code,
                    validation_output=val_output,
                    checkpoint=checkpoint_stamp,
                    log_path=f".bale/logs/{locked_sid}.log",
                    clarification=read_clarification_summary(
                        repo, locked_sid),
                ))
            print(format_summary_block(
                [
                    ("tag", f"applied/{locked_sid}"),
                    ("branch", f"{origin_branch} (merged — {merged_note})"),
                    ("files", f"{len(manifest['changes'])} changed"),
                    ("staging", f"{staging} (preserved for inspection)"),
                    ("telemetry",
                     f"recorded {telemetry_rel}" if telemetry_rel
                     else "write failed — see log"),
                ],
                status="PASS",
                sid=locked_sid,
                trailer=[
                    f"To roll back this bale: `bale rollback {locked_sid}`, "
                    f"or `bale rollback` for the most recent.",
                ],
            ))
            if json_mode():
                # Terminal json report (v0.2.8), emitted after the human
                # banner (now on stderr) so the stdout line a consumer
                # waits on is the last thing this command does.
                emit_json_line(format_apply_json(
                    outcome="applied", sid=locked_sid, log_path=session_log,
                    state=state, exit_code=exit_code,
                    checkpoint=checkpoint_stamp,
                    claims=manifest.get("claims", {}) or {},
                    action="merge", merged=True,
                    tag=f"applied/{locked_sid}", origin_branch=origin_branch,
                    telemetry=telemetry_rel,
                ))
            return 0

        if action == "inspect":
            # HOLD → leave the session commit on bale/<sid> for the user to
            # investigate (branch diff plus the preserved staging dir — the
            # checkout was never switched, ADR-0008). Exit non-zero per
            # BALE.md §8.7 piped-mode contract; the session stays open and
            # the branch persists until the user retries with a corrected
            # response or reverts. This invocation's git mutation is
            # complete, so the integration lock releases here — the held
            # state is guarded by the session's registry entry plus the
            # branch itself, not by the lock.
            release_integration_lock(repo)
            # Telemetry record (v0.3.9, B2 — BALE.md §8.9). The HOLD attempt
            # is appended now; a later retry appends its own attempt to the
            # same record rather than duplicating the file.
            telemetry_rel = write_telemetry_record(
                repo, locked_sid, build_telemetry_attempt(
                    outcome="held", command=invoked_by,
                    tarball=tarball_path.name, manifest=manifest,
                    scope=session_scope,
                    overridden_paths=overridden_paths,
                    validation_state=state,
                    validation_exit_code=exit_code,
                    validation_output=val_output,
                    checkpoint=checkpoint_stamp,
                    log_path=f".bale/logs/{locked_sid}.log",
                ))
            print(format_summary_block(
                [
                    ("validation", f"exited {exit_code}"),
                    ("branch", f"{sid_branch} (committed; `git diff "
                               f"{origin_branch}..{sid_branch}` to inspect "
                               f"— checkout untouched)"),
                    ("log", f".bale/logs/{locked_sid}.log"),
                    ("staging", f"{staging} (preserved)"),
                    ("telemetry",
                     f"recorded {telemetry_rel}" if telemetry_rel
                     else "write failed — see log"),
                    ("retry", "bale retry <new-tarball>"),
                    ("discard", f"bale revert {locked_sid}"),
                ],
                status="HOLD",
                sid=locked_sid,
            ))
            if json_mode():
                # Emitted on the exit-1 path deliberately: a machine
                # consumer needs the HOLD report as much as the PASS one
                # (format_apply_json's consumer contract).
                emit_json_line(format_apply_json(
                    outcome="held", sid=locked_sid, log_path=session_log,
                    state=state, exit_code=exit_code,
                    checkpoint=checkpoint_stamp,
                    claims=manifest.get("claims", {}) or {},
                    action="inspect", merged=False,
                    origin_branch=origin_branch,
                    telemetry=telemetry_rel,
                ))
            return 1

        # action == "revert" — BALE.md §8.8: "Delete the branch (forcefully),
        # wipe .bale/sessions/<sid>/, clear the lock. Same operation
        # regardless of whether validation passed or held." Wired through
        # to _discard_hold_state (section 19) which already does the heavy
        # lifting for `bale revert <sid>` — branch-aware reset/checkout,
        # branch -D, session-dir wipe, recorded-staging wipe. clear_lock
        # is the caller's responsibility per _discard_hold_state's
        # docstring contract.
        #
        # Why this is safe on both paths: PASS and HOLD alike hold a
        # session commit on bale/<sid> (ADR-0008), so sid_sha !=
        # origin_sha and _discard_hold_state's ancestor guard recognises
        # an unmerged branch (the guard's purpose is to refuse
        # already-merged sessions, which this isn't — origin still points
        # at the pre-apply base). Either way the cleanup runs, and since
        # the checkout was never switched there is nothing to reset or
        # check back out on the common path.
        #
        # Exit code: 1, matching the stub this replaces. The work did
        # not land in origin; a scripted `bale apply $TARBALL && deploy`
        # caller should short-circuit. The distinction between
        # [HOLD]+inspect (work staged for human review) and
        # [REVERT]+revert (work backed out cleanly) lives in the
        # printed banner, not the exit code — exit code carries the
        # binary "work landed or not" signal only.
        status = _discard_hold_state(repo, locked_sid)
        close_session(repo, locked_sid)
        release_integration_lock(repo)
        log(f"walkthrough revert: {locked_sid}; session closed")

        # Telemetry record (v0.3.9, B2 — BALE.md §8.9). Validation DID run
        # on this attempt (revert is reachable from both verdicts), so the
        # attempt carries its state/exit/reconciliation alongside the
        # reverted outcome — exactly the pairing the longitudinal signal
        # wants ("validation said X and the human backed it out anyway").
        telemetry_rel = write_telemetry_record(
            repo, locked_sid, build_telemetry_attempt(
                outcome="reverted", command=invoked_by,
                tarball=tarball_path.name, manifest=manifest,
                scope=session_scope,
                overridden_paths=overridden_paths,
                validation_state=state,
                validation_exit_code=exit_code,
                validation_output=val_output,
                checkpoint=checkpoint_stamp,
                log_path=f".bale/logs/{locked_sid}.log",
                clarification=read_clarification_summary(repo, locked_sid),
            ))
        print(format_summary_block(
            [
                ("branch", f"{status['origin_branch']} ({sid_branch} deleted)"),
                ("lock", "cleared"),
                ("staging", status['staging_status']),
                ("telemetry",
                 f"recorded {telemetry_rel}" if telemetry_rel
                 else "write failed — see log"),
            ],
            status="REVERT",
            sid=locked_sid,
        ))
        if json_mode():
            # Revert is reachable from both verdicts, so state/exit_code
            # still report what validation.sh found before the user (or
            # the non-interactive default) backed the work out.
            emit_json_line(format_apply_json(
                outcome="reverted", sid=locked_sid, log_path=session_log,
                state=state, exit_code=exit_code,
                checkpoint=checkpoint_stamp,
                claims=manifest.get("claims", {}) or {},
                action="revert", merged=False,
                origin_branch=origin_branch,
                telemetry=telemetry_rel,
            ))
        return 1


# ---------------------------------------------------------------------------
# 3. Apply
# ---------------------------------------------------------------------------

def record_rejected_attempt(repo: Path, sid: str, command: str,
                             tarball_basename: str, exc: SystemExit) -> None:
    """Record a rejected apply/retry in the telemetry record (BALE.md §8.9).

    Called from cmd_apply/cmd_retry's SystemExit wrapper around
    apply_pipeline; the caller re-raises, so this must never mask the exit
    — and write_telemetry_record already never raises. A SystemExit with
    code 0 or None is a clean exit, not a rejection, and records nothing.
    The attempt is minimal (validation null, feedback null): a rejected
    tarball's manifest is unvalidated, and the rejection detail lives in
    the session log fail() already wrote.
    """
    from __main__ import read_session_scope  # lazy — see module docstring
    from bale_report import (  # lazy — see module docstring
        build_telemetry_attempt,
        write_telemetry_record,
    )
    if exc.code in (None, 0):
        return
    write_telemetry_record(
        repo, sid, build_telemetry_attempt(
            outcome="rejected", command=command,
            tarball=tarball_basename,
            scope=read_session_scope(repo, sid),
            log_path=f".bale/logs/{sid}.log",
        ))


def _extract_response_dir(tmpdir: str, tarball_path: Path) -> Path:
    """Open `tarball_path`, scan for unsafe member paths, extract into
    `tmpdir`, and return the single top-level `response-NNN/` directory.

    The same tar-integrity / single-top-level-dir / response- prefix checks
    the apply pipeline (section 2) does, factored out so the inspection
    flags (`--show-validator`, `--show-apply-script`) can reuse them without
    duplicating the safety scan. `fail()`s on any structural problem, so the
    caller can assume a well-formed response dir on return.
    """
    from __main__ import fail  # lazy — see module docstring
    try:
        tf = tarfile.open(tarball_path, "r:gz")
    except (tarfile.TarError, OSError) as e:
        fail(f"tarball is unreadable: {e}")
    try:
        for member in tf.getmembers():
            name = member.name
            if name.startswith("/") or ".." in Path(name).parts:
                fail(f"tarball contains unsafe path: {name}")
        tf.extractall(tmpdir)
    finally:
        tf.close()

    entries = [p for p in Path(tmpdir).iterdir()]
    if len(entries) != 1 or not entries[0].is_dir():
        fail(f"tarball must contain exactly one top-level directory; "
             f"found {[e.name for e in entries]}")
    response_dir = entries[0]
    if not response_dir.name.startswith("response-"):
        fail(f"top-level directory must be named response-NNN/, "
             f"got {response_dir.name}/")
    return response_dir


def inspect_response_scripts(tarball_path: Path, *, show_apply: bool,
                             show_validator: bool) -> int:
    """`bale apply --show-apply-script` / `--show-validator`: print the
    requested shell deliverable(s) from a response tarball, then exit.

    Pure inspection — no session lock, no clean-tree requirement, no git or
    staging side effects. The point is to read what a tarball *would* run
    before deciding to apply it, so it deliberately works whether or not a
    session is open. The tarball is still resolved through
    `apply.search_paths` by the caller and validated for structure here via
    `_extract_response_dir`, so a malformed tarball is reported the same way
    `bale apply` would report it.

    When both flags are set, apply.sh is printed before validation.sh, each
    under a banner naming the file so piping the combined output stays
    legible. Returns 0 on success; structural problems `fail()` (exit 1)
    inside `_extract_response_dir`.
    """
    from __main__ import fail  # lazy — see module docstring
    with tempfile.TemporaryDirectory() as tmpdir:
        response_dir = _extract_response_dir(tmpdir, tarball_path)
        # Both scripts are required deliverables (TARBALL.md §5.1 / BALE.md
        # §11 row 16); a missing one is a malformed tarball, not a silent
        # skip. Check only the file(s) actually requested so showing one
        # script still works against a tarball whose other script is absent
        # for some reason — the failure is then specific to what was asked.
        wanted: list[str] = []
        if show_apply:
            wanted.append("apply.sh")
        if show_validator:
            wanted.append("validation.sh")
        for name in wanted:
            if not (response_dir / name).is_file():
                fail(f"{name} is missing from {tarball_path.name} "
                     f"(required deliverable per TARBALL.md §5.1)")
        for i, name in enumerate(wanted):
            if i > 0:
                print()
            print(f"# ===== {response_dir.name}/{name} "
                  f"({tarball_path.name}) =====")
            try:
                sys.stdout.write((response_dir / name).read_text())
            except OSError as e:
                fail(f"could not read {name} from tarball: {e}")
    return 0


def cmd_apply(args: argparse.Namespace) -> int:
    from __main__ import (  # lazy — see module docstring
        fail,
        log,
        open_sessions,
        refuse_system_dir,
        repo_root,
        resolve_inbound_path,
        set_log_file,
    )
    import bale_config  # lazy — see module docstring
    from bale_report import enable_json_mode  # lazy — see module docstring
    cwd = Path.cwd().resolve()
    refuse_system_dir(cwd)

    repo = repo_root(cwd)
    if repo is None:
        fail("not in a git repo. `bale apply` requires the project repo.")
    refuse_system_dir(repo)

    # Resolve the tarball argument through apply.search_paths. When no
    # search paths are configured at either layer, this is equivalent to
    # Path(arg).resolve() against cwd — preserving the pre-feature behavior
    # verbatim. The config-malformed-path is fatal up front (merged_config
    # delegates to load_config/load_global_config which both validate parsing,
    # and get_apply_search_paths validates the shape) so the user finds out
    # before any session work.
    cfg = bale_config.merged_config(repo)
    search_paths = bale_config.get_apply_search_paths(cfg)
    tarball_path = resolve_inbound_path(args.tarball, cwd, search_paths)
    if not tarball_path.is_file():
        # Only reachable for the absolute-path branch (relative + search
        # paths configured already fails inside the helper); the empty-
        # search-paths relative branch reaches here only if (cwd/arg)
        # doesn't exist. Either way, the existing message is right.
        fail(f"tarball not found: {tarball_path}")

    # `--show-apply-script` / `--show-validator`: pure inspection. Print the
    # requested deliverable(s) from the tarball and exit. Deliberately ahead
    # of the lock and clean-tree guards — inspecting what a tarball would run
    # shouldn't require an open session or a pristine worktree.
    if args.show_apply_script or args.show_validator:
        return inspect_response_scripts(
            tarball_path,
            show_apply=args.show_apply_script,
            show_validator=args.show_validator,
        )

    # json output mode (v0.2.8): enabled after the inspection branch above
    # on purpose — --show-validator / --show-apply-script print a script
    # body as their whole output, which is its own stdout contract, so
    # --json is documented as having no effect there. From here down the
    # stream discipline holds: [bale] logs, prompts, and the human banners
    # go to stderr; stdout is reserved for the one-line report the apply
    # pipeline emits at its terminal reporting point.
    if args.json:
        enable_json_mode()

    # 8.1 step 4: an open session must exist (opened with `bale pack`),
    # resolved from the ADR-0006 session registry — §11 row 7 re-read as
    # "the sid this response names is open". Required for a real apply, a
    # retry, and a dry-run alike — the responds_to check a dry-run performs
    # needs the open sid to compare against. With exactly one session open
    # the resolution is exactly what it always was: the registry's sole
    # entry. With several open (reachable since ADR-0007's pack gate
    # landed), the response itself says which session it answers:
    # _peek_responds_to reads responds_to from the tarball's manifest, and
    # membership in the open set is the §11 row 9 registry lookup, made
    # here so the session log wires to the right sid before the pipeline
    # runs. The pipeline re-checks responds_to against the resolved sid
    # after its own full extraction (defense in depth).
    open_sids = open_sessions(repo)
    if not open_sids:
        fail("no session is open. Run `bale pack` first to open one.")
    if len(open_sids) == 1:
        locked_sid = open_sids[0]
    else:
        responds_to = _peek_responds_to(tarball_path)
        if responds_to not in open_sids:
            fail(
                f"manifest.responds_to={responds_to!r} does not name an "
                f"open session. Open sessions: {', '.join(open_sids)}. "
                f"The response answers a session that is not open here — "
                f"wrong repo, already-applied session, or a stale tarball."
            )
        locked_sid = responds_to

    # Wire logging to the session log from here on.
    set_log_file(repo / ".bale" / "logs" / f"{locked_sid}.log")
    log(f"{'dry-run validating' if args.dry_run else 'applying'} "
        f"{tarball_path.name} against session {locked_sid}")

    # Non-interactive mode (BALE.md §5.4 / §8.7): per-invocation flag or
    # per-config opt-in, resolved once so every bypassed prompt logs the
    # same source string. Logged at activation (after set_log_file, so the
    # session log carries it) — the mode changes what the rest of this
    # command will do at its prompt points, and that should be on the
    # record before any of them is reached.
    no_interact, no_interact_source = resolve_no_interact(
        repo, cfg, args.no_interact)
    if no_interact:
        log(f"non-interactive apply mode active ({no_interact_source})")

    # `--dry-run`: run the read-only front half of the pipeline (validate,
    # report the plan) and stop before any git or worktree side effect. It
    # touches neither the working tree nor `.bale/`, so the clean-tree guard
    # a real apply needs is skipped here. (Non-interactive mode has no
    # effect on this path — a dry-run reaches no prompt point.)
    if args.dry_run:
        return apply_pipeline(
            repo, tarball_path, locked_sid, args.staging_dir,
            dry_run=True, verbose=args.verbose,
            allow_out_of_scope=args.allow_out_of_scope,
        )

    # 8.1 step 5 — the ADR-0008 narrow rule, replacing the blanket
    # clean-tree requirement: refuse only tracked changes on the target
    # branch itself. Untracked files never block; a dirty checkout on any
    # OTHER branch never blocks (integration no longer touches the
    # checkout). cmd_retry runs the same guard.
    refuse_dirty_on_target(repo, resolve_target_branch(repo, locked_sid))

    # Telemetry on the rejected path (v0.3.9, B2 — BALE.md §8.9): every
    # rejection or pipeline error exits through fail() → SystemExit, from
    # many sites (pre-flight, reconciliation, merge guards) — too many to
    # wire individually, and several sit inside module code. One wrapper at
    # the invocation records outcome="rejected" uniformly and re-raises;
    # detail stays in the session log, which fail() already writes to. The
    # record is minimal by design: a rejected tarball's own manifest is
    # unvalidated (possibly the reason for the rejection), so nothing from
    # it is promoted. record_rejected_attempt never raises.
    try:
        return apply_pipeline(
            repo, tarball_path, locked_sid, args.staging_dir,
            verbose=args.verbose, no_interact=no_interact,
            no_interact_source=no_interact_source,
            allow_out_of_scope=args.allow_out_of_scope,
        )
    except SystemExit as e:
        record_rejected_attempt(repo, locked_sid, "apply",
                                 tarball_path.name, e)
        raise
