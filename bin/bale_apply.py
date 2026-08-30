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
module's public surface); `default_staging_root` +
`default_staging_dir` (`bale status`'s gather, so the path status reports
is by construction the path apply uses); and
`read_request_checkpoint_stamp` (`bale amend-checkpoint`'s accounting
rung, v0.4.17 — the amendment verb and the provenance gate read the
session's pack-time stamp through one implementation). Shared `bin/bale` helpers are
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
import hashlib
import json
import shutil
import subprocess
import sys
import tarfile
import tempfile
from collections import Counter
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


def _peek_bare_candidate(tarball_path: Path) -> tuple[Optional[str], str]:
    """Non-fatal candidacy peek for bare-apply resolution (board 51).

    Returns (responds_to, "") when `tarball_path` is a readable response
    tarball — a gzip tar whose members include a response-NNN/manifest.json
    carrying a non-empty string `responds_to` — and (None, reason)
    otherwise. The sibling of `_peek_responds_to`, split rather than
    parameterized because the two callers want opposite failure postures:
    the argumented multi-open path holds exactly the tarball the user
    named, so an unreadable one is fatal there; the bare scan walks every
    *.tar.gz in the search directories, where a stray request tarball or
    a corrupt download is a skip with a reason, never an exit — dying on
    the first non-candidate in ~/Downloads would make the feature unusable
    beside ordinary clutter. This is also the response/request
    discriminator: a request tarball's single top-level directory is
    request-NNN/, so it has no response-*/manifest.json member and returns
    (None, ...) here — request tarballs are structurally never candidates.
    Every check this peek performs is re-run in full by the pipeline's own
    pre-flight; candidacy is a scan filter, not a validation.
    """
    try:
        with tarfile.open(tarball_path, "r:gz") as tf:
            raw = None
            for m in tf.getmembers():
                parts = Path(m.name).parts
                if (m.isfile() and len(parts) == 2
                        and parts[0].startswith("response-")
                        and parts[1] == "manifest.json"):
                    extracted = tf.extractfile(m)
                    if extracted is None:
                        return None, f"could not read {m.name}"
                    raw = extracted.read()
                    break
            if raw is None:
                return None, ("no response-NNN/manifest.json member "
                              "(not a response tarball)")
    except (tarfile.TarError, OSError) as e:
        return None, f"unreadable archive ({e})"
    try:
        manifest = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        return None, f"manifest.json is not valid JSON ({e})"
    responds_to = manifest.get("responds_to")
    if not isinstance(responds_to, str) or not responds_to.strip():
        return None, "manifest.responds_to is missing or empty"
    return responds_to.strip(), ""


def resolve_bare_apply_tarball(repo: Path, cwd: Path, cfg: dict,
                               args: argparse.Namespace,
                               search_paths: list[str]) -> Path:
    """Resolve bare `bale apply` (no tarball argument) to a tarball path.

    Board 51's contract: resolve the newest response tarball matching an
    open session across cwd plus apply.search_paths, echo its identity,
    and take a y/N; ambiguity refuses loudly, never guesses. Every
    refusal exits through fail() with a remedy-naming message — the bare
    spelling is a real command path, never an argparse usage error.

    Semantics, in refusal order:

    - Non-interactive mode (--no-interact or apply.no_interact) refuses:
      the echoed-identity y/N is the guard that makes bare resolution
      safe, so a mode whose whole point is skipping prompts contradicts
      the bare form. The explicit form is the non-interactive spelling.
    - Zero open sessions refuses (nothing to match); two or more refuse
      (which session's response is wanted is a guess — the argumented
      form disambiguates via the manifest's own responds_to).
    - Candidates are the *.tar.gz files directly in cwd and each
      configured search directory (non-recursive, the same surface the
      argumented form's relative-name resolution searches) whose peeked
      responds_to equals the open sid. Non-candidates are skipped with a
      reason — logged per file under --verbose, always summarized in
      aggregate — never fatal (see _peek_bare_candidate).
    - "Newest" is file modification time at nanosecond stat granularity
      (st_mtime_ns): the download that arrived last wins, which is the
      re-delivery case the feature exists for. An exact tie refuses and
      names every tied path — the contract's never-guess rule; there is
      deliberately no secondary tie-break.
    - The winner's identity — path, matched sid, content sha256 of the
      tarball bytes, mtime — is echoed *before* the y/N, so the operator
      confirms what resolution picked before anything applies. The
      prompt follows the decline-default precedent (--supersedes, v0.3.17):
      on a TTY, y/N with decline as the default; piped stdin takes the
      decline without a prompt and refuses with the explicit-form remedy,
      so automation never applies a guessed tarball silently.

    On confirmation, returns the resolved path; cmd_apply proceeds
    exactly as if the user had typed it — the argumented form's behavior
    downstream is untouched.
    """
    from __main__ import confirm_yn, fail, log, open_sessions

    no_interact, no_interact_source = resolve_no_interact(
        repo, cfg, args.no_interact)
    if no_interact:
        fail(
            f"bare `bale apply` and non-interactive mode are contradictory "
            f"({no_interact_source}): the resolved tarball's identity echo "
            f"and y/N confirmation are what make argument-less resolution "
            f"safe, and non-interactive mode exists to skip prompts. Name "
            f"the tarball explicitly instead: "
            f"bale apply <response-NNN.tar.gz>."
        )

    open_sids = open_sessions(repo)
    if not open_sids:
        fail(
            "bare `bale apply` resolves the newest response tarball "
            "answering an open session, and no session is open. Run "
            "`bale pack` to open one, or name the tarball explicitly: "
            "bale apply <response-NNN.tar.gz>."
        )
    if len(open_sids) > 1:
        fail(
            f"bare `bale apply` is ambiguous with more than one session "
            f"open — resolution never guesses which session's response "
            f"you meant. Open sessions: {', '.join(open_sids)}. Name the "
            f"tarball explicitly (its manifest's responds_to selects the "
            f"session): bale apply <response-NNN.tar.gz>."
        )
    sid = open_sids[0]

    # The scan surface: cwd first, then each configured directory, the
    # same order resolve_inbound_path searches. Directories deduped by
    # resolved path (cwd may itself be configured); candidate files
    # deduped the same way (a symlinked twin is one delivery, not two).
    directories: list[Path] = []
    seen_dirs: set = set()
    for d in [cwd] + [Path(sp) for sp in search_paths]:
        try:
            key = d.resolve()
        except OSError:
            key = d
        if key in seen_dirs:
            continue
        seen_dirs.add(key)
        directories.append(d)

    candidates: list[tuple[Path, int]] = []
    skipped: list[tuple[Path, str]] = []
    seen_files: set = set()
    for d in directories:
        if not d.is_dir():
            continue
        for p in sorted(d.glob("*.tar.gz")):
            if not p.is_file():
                continue
            try:
                resolved = p.resolve()
                mtime_ns = p.stat().st_mtime_ns
            except OSError as e:
                skipped.append((p, f"unreadable path ({e})"))
                continue
            if resolved in seen_files:
                continue
            seen_files.add(resolved)
            responds_to, reason = _peek_bare_candidate(p)
            if responds_to is None:
                skipped.append((p, reason))
                continue
            if responds_to != sid:
                skipped.append(
                    (p, f"responds_to={responds_to} is not the open "
                        f"session"))
                continue
            candidates.append((resolved, mtime_ns))

    # Skips are reported, never silent: per-file under --verbose (a
    # Downloads directory full of old request tarballs would otherwise
    # drown the terminal on every bare run), in aggregate always — as a
    # log line when resolution proceeds, and folded into the refusal
    # itself when nothing was a candidate, so the stderr message alone
    # says both what was searched and what was seen-but-rejected.
    if skipped and args.verbose:
        for p, reason in skipped:
            log(f"bare apply: skipped {p} — {reason}")

    if not candidates:
        lines = [
            f"bare `bale apply` found no response tarball answering open "
            f"session {sid}.",
            "  searched (*.tar.gz, non-recursive):",
            f"    {cwd}  (cwd)",
        ]
        for sp in search_paths:
            lines.append(f"    {sp}")
        if skipped:
            lines.append(
                f"  {len(skipped)} tarball(s) were scanned and are not "
                f"candidates"
                + ("." if args.verbose
                   else " (--verbose lists each with its reason)."))
        lines.append(
            "  Download the response tarball into one of these "
            "directories, add its directory to apply.search_paths "
            "(`bale config init`), or name the path explicitly: "
            "bale apply <response-NNN.tar.gz>."
        )
        fail("\n".join(lines))

    if skipped:
        log(f"bare apply: {len(skipped)} tarball(s) scanned and not "
            f"candidates"
            + ("" if args.verbose else " (--verbose lists each with its "
                                      "reason)"))

    newest_ns = max(m for _, m in candidates)
    newest = sorted(p for p, m in candidates if m == newest_ns)
    if len(newest) > 1:
        listing = "\n".join(f"    {p}" for p in newest)
        fail(
            f"bare `bale apply` is ambiguous: {len(newest)} candidates "
            f"share the newest modification time, and resolution never "
            f"guesses between them. Tied candidates:\n{listing}\n"
            f"  Name the one you meant explicitly: bale apply <path>."
        )
    tarball_path = newest[0]

    # The identity echo, before the prompt: path, the sid it matched, a
    # content identity (sha256 of the tarball bytes), and the mtime that
    # won the resolution. The operator confirms this, not a guess.
    digest = hashlib.sha256()
    try:
        with tarball_path.open("rb") as f:
            for chunk in iter(lambda: f.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as e:
        fail(f"could not read resolved tarball {tarball_path}: {e}")
    mtime_iso = datetime.fromtimestamp(
        newest_ns / 1_000_000_000, tz=timezone.utc
    ).isoformat(timespec="seconds")
    log("bare apply resolved a response tarball:")
    log(f"  path:        {tarball_path}")
    log(f"  responds_to: {sid} (the open session)")
    log(f"  sha256:      {digest.hexdigest()}")
    log(f"  modified:    {mtime_iso}")
    if len(candidates) > 1:
        log(f"  ({len(candidates)} candidates matched the session; "
            f"newest modification time won)")

    if not sys.stdin.isatty():
        fail(
            f"stdin is not a TTY; the bare-apply confirmation's decline "
            f"default applies without a prompt (nothing applied) — the "
            f"--supersedes precedent: automation never accepts a "
            f"resolution guess silently. Name the tarball explicitly to "
            f"apply without the prompt: bale apply {tarball_path}"
        )
    if not confirm_yn(f"Apply this tarball against session {sid}?"):
        fail(
            "bare apply declined at the confirmation; nothing applied. "
            "Name the tarball explicitly if the resolution picked the "
            "wrong file: bale apply <path>."
        )
    return tarball_path


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
        sweep_commit,
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

    # Auto-sweep (v0.3.32; BALE.md §8.8): a bailout consumes its session
    # — a closing event — and performs no git mutation of its own, so
    # the sweep commit interleaves with nothing. Config-gated (resolved
    # here, not at the normal pipeline's pre-flight, since the bailout
    # branch forks before it); silent when unset, loud and never fatal
    # when enabled.
    sweep_result = sweep_commit(repo, sid, "bailout",
                                [telemetry_rel] if telemetry_rel else [])

    print_bailout_banner(manifest, handoff_path, tarball_basename,
                         telemetry=telemetry_rel)

    if json_mode():
        # Terminal json report (v0.2.8), emitted after the §5.6.3 banner
        # (which json mode routed to stderr) so the stdout line a consumer
        # waits on is the last thing this command does. The sweep object
        # (v0.3.34, additive) is the sweep_commit return above — null
        # when [apply].sweep is unset/false.
        emit_json_line(format_apply_json(
            outcome="bailout", sid=sid,
            log_path=repo / ".bale" / "logs" / f"{sid}.log",
            telemetry=telemetry_rel,
            sweep=sweep_result,
        ))
    return 0


def clarifications_dir(repo: Path, sid: str) -> Path:
    """The session's exchange-thread directory, `.bale/clarifications/<sid>/`
    (BALE.md §8.10.2 step 3, §8.11). One home for the path: the apply-side
    preservation, `bale relay`, `bale status`'s gather, and the close-time
    summary all resolve through it. Deliberately NOT under
    `.bale/sessions/<sid>/`, which the eventual normal-PASS merge wipes —
    the thread must outlive the session it suspended."""
    return repo / ".bale" / "clarifications" / sid


def next_clarification_seq(repo: Path, sid: str) -> int:
    """The next NNN in the session's thread: count of preserved `*.json`
    records + 1. Race-free enough for a single-user CLI (BALE.md §3.5);
    `bale relay` refuses a record whose `round` is not this value, so a
    stale or skipped round is caught before anything is written."""
    clar_dir = clarifications_dir(repo, sid)
    if not clar_dir.is_dir():
        return 1
    return len(list(clar_dir.glob("*.json"))) + 1


def preserve_clarification_record(repo: Path, sid: str, record: dict) -> Path:
    """Write `record` as the thread's next `NNN.json` under
    `.bale/clarifications/<sid>/` and return the path.

    The one write both ingest paths share (v0.4.18, BALE.md §8.11): apply's
    clarification handler preserves the manifest through it, and `bale
    relay` preserves an exchange record or a paste-block-borne manifest
    through it, so the thread is identical after either. Sequence
    numbering keeps rounds distinct (next_clarification_seq). The
    preserved copy carries a `preserved_at` sidecar key stamped here at
    write time (v0.3.27) — a sidecar key, not a wrapper, so the record
    keeps its own shape for every reader of questions[] / answers[], and
    read_clarification_summary's fallback chain (preserved_at, then
    mtime, then null) covers stampless pre-v0.3.27 records unchanged. A
    shallow copy keeps the caller's in-memory record pristine.
    """
    clar_dir = clarifications_dir(repo, sid)
    clar_dir.mkdir(parents=True, exist_ok=True)
    seq = next_clarification_seq(repo, sid)
    record_path = clar_dir / f"{seq:03d}.json"
    preserved = dict(record)
    preserved["preserved_at"] = datetime.now(timezone.utc).isoformat(
        timespec="seconds")
    record_path.write_text(
        json.dumps(preserved, indent=2) + "\n", encoding="utf-8",
    )
    return record_path


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
         via preserve_clarification_record — the write `bale relay` shares
         (v0.4.18; BALE.md §8.11 — apply's tarball ingest is one of two
         ingest paths for the same round-one record)
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
    # Preserve the manifest for the aggregation surface — the shared
    # thread write (preserve_clarification_record), which `bale relay`
    # also uses, so the two ingest paths for a round-one record (BALE.md
    # §8.10.2 step 4) leave a byte-for-byte identical thread behind.
    record_path = preserve_clarification_record(repo, sid, manifest)
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


# --- Checkpoint provenance stamp (v0.3.28, board 6 session C) -----------------
#
# The request-side half of the §8.5 stamp verification: pack stamped
# `provenance.checkpoint` ({path, sha256} of the oracle's tip bytes, or
# explicit null when none was configured) into the request manifest,
# which persist_pack_session copied to .bale/sessions/<sid>/manifest.json.
# Apply reads it back from there — the registry copy is the one the
# operator's own pack wrote, so a doctored response tarball cannot carry
# a forged stamp past it.

# The response prose artifacts the [apply].archive_dir mechanism copies
# (BALE.md §8.8): the two optional artifacts TARBALL.md §5.1 defines,
# plus the retired-but-tolerated next-prompt.md (TARBALL.md §5.5 /
# BALE.md §6.2) so pre-retirement archives round-trip too. One source:
# the archival copy loop and the rollback guard's carve-out
# (bale_rollback) both read this tuple.
ARCHIVABLE_RESPONSE_ARTIFACTS = ("README.md", "notes.md", "next-prompt.md")


def archive_response_artifacts(repo: Path, response_dir: Path, sid: str,
                               archive_dir: str) -> tuple[list[str], list[str]]:
    """Copy the response's prose artifacts into <archive_dir>/<sid>/.

    The [apply].archive_dir mechanism (BALE.md §8.8, the landed v0.5
    candidate): called on the applied outcome only, AFTER the merge has
    succeeded. Copies whichever of ARCHIVABLE_RESPONSE_ARTIFACTS the
    response actually included — absence of an artifact is meaningful
    (TARBALL.md §5.1) and archives nothing for that name.

    The copies are untracked working-tree writes; committing them is the
    operator's job, by design — bale writes files, never commits them.
    Destination files are overwritten if present (idempotent re-copy).

    Returns (copied, failed): repo-relative destination paths that landed,
    and artifact names whose copy failed. **Never raises, never fatal**:
    by the time this runs the merge has landed and the session is closed,
    so a copy failure must not un-apply or HOLD anything — each failure
    is logged loudly (force-level) and surfaced to the caller for the
    closing banner, honoring the no-silent-skip rule (CLAUDE.md §6).
    """
    from __main__ import log  # lazy — see module docstring

    copied: list[str] = []
    failed: list[str] = []
    present = [name for name in ARCHIVABLE_RESPONSE_ARTIFACTS
               if (response_dir / name).is_file()]
    if not present:
        log(f"archive_dir: response shipped none of "
            f"{', '.join(ARCHIVABLE_RESPONSE_ARTIFACTS)} — nothing to archive")
        return copied, failed

    dest_dir = repo / archive_dir / sid
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        # The whole batch fails; name every artifact so the banner and the
        # log agree on what did NOT land. Loud, never fatal (docstring).
        log(f"ARCHIVE FAILED: could not create {dest_dir}: {e} — "
            f"{', '.join(present)} were NOT archived; the merge itself "
            f"landed and is unaffected. Copy them by hand from the "
            f"response tarball if needed.", force=True)
        return copied, list(present)

    for name in present:
        dest = dest_dir / name
        try:
            shutil.copyfile(response_dir / name, dest)
        except OSError as e:
            log(f"ARCHIVE FAILED: could not copy {name} to {dest}: {e} — "
                f"the merge itself landed and is unaffected. Copy it by "
                f"hand from the response tarball if needed.", force=True)
            failed.append(name)
            continue
        rel = f"{archive_dir}/{sid}/{name}"
        copied.append(rel)
        log(f"archived {name} → {rel}")
    return copied, failed


def read_request_checkpoint_stamp(
        repo: Path, sid: str) -> tuple[bool, Optional[dict]]:
    """Return (key_present, stamp) from the session's persisted request
    manifest's provenance block.

    `key_present` False means the request carried no
    `provenance.checkpoint` key at all — a hand-rolled request, a
    pre-v0.3.28 pack, or (defensively) a missing/unreadable session
    manifest, each logged so the skip is never silent. That is the
    "verify nothing, stamp_matched: null" case (BALE.md §8.5). When
    True, `stamp` is the key's value: a {path, sha256} object, or None
    for the explicit-null stamp (packed with no checkpoint configured).
    """
    from __main__ import log  # lazy — see module docstring
    manifest_path = repo / ".bale" / "sessions" / sid / "manifest.json"
    try:
        request_manifest = json.loads(
            manifest_path.read_text(encoding="utf-8"))
    except OSError as e:
        log(f"note: session request manifest unreadable at "
            f"{manifest_path} ({e}); checkpoint provenance verification "
            f"skipped (treated as a stampless request)")
        return (False, None)
    except json.JSONDecodeError as e:
        log(f"note: session request manifest at {manifest_path} is not "
            f"valid JSON ({e}); checkpoint provenance verification "
            f"skipped (treated as a stampless request)")
        return (False, None)
    provenance = request_manifest.get("provenance")
    if not isinstance(provenance, dict) or "checkpoint" not in provenance:
        return (False, None)
    stamp = provenance.get("checkpoint")
    return (True, stamp if isinstance(stamp, dict) else None)


def base_tree_sha256(repo: Path, base_sha: str, path: str) -> Optional[str]:
    """sha256 of the committed blob at `base_sha:path`, or None when no
    blob exists there. Binary-exact via a direct subprocess call
    (text=False), the same extraction run_blind_checkpoint performs, so
    verification and execution hash the same bytes.
    """
    shown = subprocess.run(
        ["git", "show", f"{base_sha}:{path}"],
        cwd=str(repo), capture_output=True,
    )
    if shown.returncode != 0:
        return None
    return hashlib.sha256(shown.stdout).hexdigest()


# ---------------------------------------------------------------------------
# 2. Apply: pipeline
# ---------------------------------------------------------------------------

def apply_pipeline(repo: Path, tarball_path: Path, locked_sid: str,
                    staging_override: Optional[str], *,
                    dry_run: bool = False, verbose: bool = False,
                    no_interact: bool = False,
                    no_interact_source: str = "",
                    invoked_by: str = "apply",
                    allow_out_of_scope: Optional[list[str]] = None,
                    allow_missing_required_check: Optional[list[str]] = None,
                    accept_checkpoint_change: bool = False,
                    no_sandbox: bool = False,
                    ) -> int:
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
    repeatable) names changes[] paths the own-forecast drift gate below
    should admit despite lying outside the session's write forecast
    (ADR-0015: worker judgment past the ask, admitted per path). Per
    invocation only — there is deliberately no config key — and any drift
    path NOT named still refuses. None/empty means no override. cmd_retry
    accepts and threads the same flag since v0.3.14 (flag parity), passing
    whatever THIS retry invocation named — never state carried from a
    prior attempt — so a retry that needs the override re-states it, and
    one that omits it hits the drift gate like an un-overridden apply.

    `allow_missing_required_check` (board 6 session B; cmd_apply/cmd_retry
    --allow-missing-required-check, repeatable) names required-check NAMES
    the step-15 superset gate below should admit despite being absent from
    the manifest's validation_will_run. The override's unit is the check
    name — the gate's own unit — and its contract is the ratified §5
    override shape: per-invocation only (deliberately no config key),
    re-stated on retry exactly like `allow_out_of_scope` above, never
    carried from a prior attempt. Any missing name NOT admitted still
    refuses. None/empty means no override.

    `accept_checkpoint_change` (v0.3.28, board 6 session C; cmd_apply/
    cmd_retry --accept-checkpoint-change) admits a blind checkpoint whose
    base-tree bytes no longer match the request manifest's pack-time
    `provenance.checkpoint` stamp — the §8.5 stamp verification below,
    which otherwise refuses pre-staging (the oracle changed between pack
    and apply). On admission the CURRENT base-tree version runs — the
    planner's latest committed oracle, never the stale stamped bytes —
    the use is FORCE-logged, and the attempt's telemetry stamp records
    stamp_matched: false. Same ratified override contract as the two
    flags above: per-invocation only, no config key, re-stated on retry,
    never carried from a prior attempt. Verification runs only when the
    request carries the provenance.checkpoint key AND a checkpoint is
    configured now; a stampless request (hand-rolled, or packed
    pre-0.3.28) verifies nothing and stamps stamp_matched: null.

    `no_sandbox` (v0.4.4, board 10 S1 — ADR-0016; cmd_apply/cmd_retry
    --no-sandbox) disables the default-on namespace confinement of the
    three response-script executions (apply.sh, the blind checkpoint,
    validation.sh) for this invocation only. The bypass is FORCE-logged
    at pipeline start; the same ratified override contract as the flags
    above applies: per-invocation only, deliberately no config key,
    re-stated on retry, never carried from a prior attempt. It exists
    for debugging the sandbox itself, not for routine convenience
    (ADR-0016 position 2). No effect under dry_run, which runs no
    scripts. Every validated attempt's telemetry entry stamps the
    bypass as `sandbox_escaped` (v0.4.5, board 10 S2; BALE.md §8.9),
    beside the FORCE line the session log has carried since S1.

    The network grant (v0.4.5, board 10 S2 — ADR-0016 position 3) has
    no parameter here on purpose: it is per-project committed config,
    never per-invocation, so the pipeline resolves bale.toml's
    [sandbox] network from the merged config at the same pre-flight
    point as the staging strategy and threads it to the three script
    runs itself. When the grant is active and the sandbox is on, the
    confined scripts run with network enabled (the sandbox's --net leg
    only; filesystem confinement unchanged) and the validated
    attempt's telemetry entry stamps `network_grant_exercised: true`.

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
        sweep_commit,
    )
    import bale_config  # lazy — see module docstring
    from bale_staging import (  # lazy — see module docstring
        build_session_commit,
        check_checkpoint_shell_syntax,
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
        format_checkpoint_stamp_refusal,
        format_dry_run_report,
        format_required_check_refusal,
        format_scope_drift_refusal,
        format_staging_row,
        format_summary_block,
        format_walkthrough_summary,
        json_mode,
        read_clarification_summary,
        write_telemetry_record,
    )
    # The session log path as the json reports cite it (absolute) — the
    # same file cmd_apply/cmd_retry already wired set_log_file to.
    session_log = repo / ".bale" / "logs" / f"{locked_sid}.log"

    # ADR-0016 position 2: the sandbox escape is per-invocation and
    # loud. Logged here, once, before any script could run under it —
    # the FORCE: line is the audit trail, and since v0.4.5 (board 10
    # S2) the validated attempt's telemetry entry stamps the same fact
    # durably as sandbox_escaped (BALE.md §8.9).
    if no_sandbox and not dry_run:
        log("sandbox DISABLED for this invocation (--no-sandbox): "
            "apply.sh, the blind checkpoint, and validation.sh will run "
            "unconfined — operator privileges, inherited environment, "
            "network on; sandbox_escaped: true will be recorded",
            force=True)

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

        # 8.1 step 16 / §11 row 32 (v0.4.2, the board-35 rider ratified
        # at the master desk 2026-08-07): duplicate changes[] paths.
        # TARBALL.md §5.2 has called a duplicated path invalid all along
        # — it makes the files/ ↔ changes[] mirror correspondence
        # ambiguous — and the worker-side lint's DUPLICATE_PATH row
        # already says so; this converts the prose to apply-side
        # contract, closing the prose-vs-enforcement disagreement the
        # board-35 session verified (an identical duplicate applied
        # cleanly). Identical path STRINGS, the lint's own basis, so the
        # two surfaces agree on what a duplicate is; a conflicting
        # duplicate that would previously have limped to the sha
        # mismatch now refuses here, at the manifest checks where the
        # disease actually lives. Manifest-only, so it runs under
        # --dry-run and passes vacuously for bailout and clarification
        # manifests, whose changes[] is empty.
        duplicate_paths = sorted(p for p, n in Counter(
            c.get("path") for c in manifest.get("changes", []) or []
            if isinstance(c.get("path"), str)
        ).items() if n > 1)
        if duplicate_paths:
            fail(f"[REJECT] duplicate changes[] path(s) (BALE.md §11 "
                 f"row 32): {', '.join(duplicate_paths)} — a duplicated "
                 f"path makes the files/ <-> changes[] correspondence "
                 f"ambiguous (TARBALL.md §5.2)")

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

        # 8.1 step 7 / §11 row 19 (ADR-0007, re-based onto forecasts by
        # ADR-0015): cross-session forecast collision. Whatever this
        # response's worker did, its changes may not land on paths
        # ANOTHER open session's write forecast claims — bale's overlay
        # is whole-file replacement, so a later apply authored against a
        # stale snapshot would silently clobber the sibling's work and
        # the --no-ff merge would land clean. This is the one mechanical
        # refusal the ADR-0015 model reserves (no override flag,
        # deliberately: admission never crosses a sibling's forecast);
        # the pack-time gate is only the conservative early one. Read
        # includes participate in nothing — a sibling may land inside
        # this session's read set, the accepted read-staleness residue.
        # With at most one session open there are no siblings and this
        # is a no-op; bailout and clarification manifests carry empty
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
                    f"[REJECT] cross-session forecast collision "
                    f"(ADR-0015, re-basing ADR-0007): changes[] lands on "
                    f"paths inside another open session's write forecast "
                    f"— {detail}. This refusal takes no override "
                    f"(admission never crosses a sibling's forecast); "
                    f"apply or close the sibling session(s) first "
                    f"(`bale apply <its tarball>`, `bale revert <sid>`, "
                    f"or `bale unlock`), then re-run this apply."
                )
            log(f"cross-session forecast collision check passed against "
                f"{len(sibling_sids)} sibling session(s): "
                f"{', '.join(sibling_sids)}")

        # 8.1 step 14 / §11 row 22 (v0.3.10, board 2; forecast
        # vocabulary and doctrine per ADR-0015, board 13): own-forecast
        # drift gate — sited beside its step-7 sibling above. The 008
        # audit's finding 2: two sessions can each drift into the same
        # UNCLAIMED file, pass every declared-vs-declared gate, and the
        # second whole-file overlay clobbers the first under a clean
        # --no-ff merge. So: every changes[] path must lie inside THIS
        # session's own recorded write forecast
        # (sessions/<sid>/scope.json — post-separation the forecast,
        # with pre-separation sessions' recorded include sets reading
        # as over-forecasts; read conservatively as whole-tree when
        # missing/unreadable, which also keeps default whole-tree
        # packs entirely outside this gate's blast radius). Created
        # paths are refused the same as modified — the clobber scenario
        # is precisely two sessions creating the same unclaimed file.
        # Under ADR-0015 the forecast is a forecast, not a wall: an
        # out-of-forecast edit is worker judgment past the ask —
        # shipped, enumerated in notes.md, admitted per path, graded by
        # the ledger — never a silent landing, and never a landing on a
        # path a sibling's forecast claims (step 7 above, which an
        # admission here cannot cross).
        # --allow-out-of-scope (per-invocation, repeatable; no config
        # key) admits exactly the named paths; any other drift still
        # refuses. The refusal is pre-staging: no git side effects, the
        # session stays open, and the remedies are a per-path admission,
        # a regenerated response, or an unlock+repack.
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
            # Named but not drifting: harmless (inside the forecast or
            # not in the change set at all), but say so — a silently
            # ignored override flag is exactly the surprise the logging
            # rules exist to prevent.
            log(f"--allow-out-of-scope named path(s) with no matching "
                f"out-of-forecast change: {', '.join(unused_allow)} "
                f"(no effect)")
        if refused_paths:
            scope_rendered = (", ".join(session_scope) if session_scope
                              else "(read-only session — empty forecast; "
                                   "lands nothing)")
            log(f"[REJECT] own-forecast drift (BALE.md §11 row 22): "
                f"{len(refused_paths)} changes[] path(s) outside session "
                f"{locked_sid}'s write forecast — "
                f"{', '.join(refused_paths)}; write forecast: "
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
                          else "read-only session — empty forecast; the "
                               "override lands changes from a session "
                               "packed to land none")
            log(f"own-forecast drift admitted by --allow-out-of-scope: "
                f"{', '.join(overridden_paths)} (write forecast: "
                f"{scope_note})", force=True)
        # No pass-path log line beyond the reads above: like the
        # generated-artifact denial below, a clean pass adds no output,
        # keeping accepted-tarball output byte-identical to v0.3.9.

        # 8.1 step 15 / §11 row 26 (board 6 session B): required-check
        # superset gate — the drift gate's declaration-side sibling,
        # sited beside it (appended as step 15 so steps 1–14 stay
        # stable). The worker's validation_will_run is the declaration
        # claims hang off (row 15: claims ⊆ validation_will_run); an
        # under-declared set starves the calibration stream on exactly
        # the checks that matter and is invisible to every gate above.
        # When the project pins `[validation] required` (bale.toml,
        # project layer only — get_validation_required), every required
        # name must appear VERBATIM in validation_will_run whenever
        # changes[] is non-empty. Name membership only — content stays
        # review policy — and a declared check may still [SKIP] with a
        # reason at runtime (TARBALL.md §7.2), grading n/a (§7.3):
        # honest and visible rather than forced work. Fires only when
        # the required set resolves non-empty AND changes[] is non-empty,
        # so bailout and clarification manifests pass vacuously,
        # read-only sessions never reach it (step 14 refuses their
        # changes first), and unconfigured projects are entirely outside
        # its blast radius. Manifest-and-config-only, so it runs under
        # --dry-run (same report, no telemetry — no outcome occurred),
        # mirroring step 14. --allow-missing-required-check <name>
        # (per-invocation, repeatable, per-NAME, flag-only — the
        # ratified override shape; a standing config opt-out is the
        # rejected self-oracle-adjacent silent bypass) admits exactly
        # the named names; any other missing name still refuses. The
        # merged config is re-read here rather than threaded from
        # cmd_apply/cmd_retry — both callers already run merged_config,
        # the re-read is two small files, and resolving at the gate is
        # what makes retry structurally inherit the project's current
        # required set (same config, same gate). The same resolved
        # config feeds the dry-run dangling-checkpoint prediction below
        # (the sanctioned session-A rider), one read for both.
        preflight_cfg = bale_config.merged_config(repo)
        required_checks = bale_config.get_validation_required(preflight_cfg)
        # [apply].archive_dir is CONSUMED post-merge (§8.8), but its
        # strict accessor is fatal on a malformed shape — so it is
        # resolved HERE, at pre-flight, where a typo refuses before any
        # staging exists. Post-merge code only uses this validated value
        # and can never fail() after the merge has landed (the archival
        # contract: loud, never fatal, never un-applies).
        archive_dir_cfg = bale_config.get_apply_archive_dir(preflight_cfg)
        # [apply].sweep follows the same pattern (v0.3.32): consumed
        # only after a terminal outcome's git mutation is complete, but
        # resolved HERE through the strict accessor so a non-bool typo
        # refuses before staging — post-outcome code passes the
        # validated value into sweep_commit and can never fail() after
        # the merge (the sweep contract: loud, never fatal).
        sweep_cfg = bale_config.get_apply_sweep(preflight_cfg)
        required_check_overridden: list[str] = []
        if required_checks and (manifest.get("changes") or []):
            declared = manifest.get("validation_will_run", []) or []
            declared_set = set(declared)
            # Dedupe preserving config order; exact string match per
            # TARBALL.md §5.3's canonical-identifier rule.
            missing = [n for n in dict.fromkeys(required_checks)
                       if n not in declared_set]
            allow_names = list(dict.fromkeys(
                allow_missing_required_check or []))
            required_check_overridden = [n for n in missing
                                         if n in allow_names]
            refused_names = [n for n in missing if n not in allow_names]
            unused_names = [n for n in allow_names if n not in missing]
            if unused_names:
                # Named but not missing: harmless (declared, or not in
                # the required set at all), but say so — the step-14
                # unused_allow mirror; a silently ignored override flag
                # is exactly the surprise the logging rules exist to
                # prevent.
                log(f"--allow-missing-required-check named check(s) "
                    f"with no matching missing required check: "
                    f"{', '.join(unused_names)} (no effect)")
            if refused_names:
                log(f"[REJECT] required checks missing (BALE.md §11 "
                    f"row 26): validation_will_run omits required "
                    f"check(s): {', '.join(refused_names)}. Required "
                    f"set ([validation] required, project layer): "
                    f"{', '.join(required_checks)}. Declared: "
                    f"{', '.join(declared) if declared else '(empty)'}")
                # A distinct, dispatchable outcome — the step-14
                # refusal's structure exactly: rendering and the json
                # line come from bale_report (wiring only here),
                # telemetry records the attempt (except under
                # --dry-run, which has no outcome), and the return
                # keeps the session open, pre-staging, with no git
                # side effects. The cmd_apply/cmd_retry SystemExit
                # wrapper never fires (no SystemExit), so the attempt
                # is not double-recorded as "rejected".
                telemetry_rel = None
                if not dry_run:
                    telemetry_rel = write_telemetry_record(
                        repo, locked_sid, build_telemetry_attempt(
                            outcome="required-check-refused",
                            command=invoked_by,
                            tarball=tarball_path.name, manifest=manifest,
                            scope=session_scope,
                            overridden_paths=overridden_paths,
                            required_check_overrides=(
                                required_check_overridden),
                            log_path=f".bale/logs/{locked_sid}.log",
                        ))
                print(format_required_check_refusal(
                    sid=locked_sid,
                    required=required_checks,
                    declared=declared,
                    missing=refused_names,
                    overridden=required_check_overridden,
                    telemetry=telemetry_rel,
                    dry_run=dry_run,
                ))
                if json_mode():
                    # Emitted on this exit-1 path deliberately, like
                    # held/scope-drift-refused: an orchestrating
                    # operator dispatches on the outcome key instead
                    # of parsing prose.
                    emit_json_line(format_apply_json(
                        outcome="required-check-refused", sid=locked_sid,
                        log_path=session_log,
                        telemetry=telemetry_rel,
                        required_checks={
                            "missing": refused_names,
                            "required": required_checks,
                            "declared": declared,
                            "overridden": required_check_overridden,
                        },
                    ))
                return 1
            if required_check_overridden:
                # force=True: an admitted missing required check is an
                # override event of the same species as
                # --allow-out-of-scope — the FORCE: journal line is the
                # session log's audit trail; the telemetry stamp at the
                # terminal action is the durable copy.
                log(f"missing required check(s) admitted by "
                    f"--allow-missing-required-check: "
                    f"{', '.join(required_check_overridden)} (required "
                    f"set: {', '.join(required_checks)})", force=True)
        # As with steps 13 and 14, a clean pass adds no output.

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
            # Dry-run dangling-checkpoint prediction (board 6 session B —
            # the sanctioned session-A rider): the real dangling refusal
            # sits past this exit (§8.2 resolves base_sha first), so a
            # dry-run on a checkpoint-configured project would report a
            # clean plan for an apply that refuses. Resolve the target
            # base READ-ONLY here — rev-parse and cat-file only, no
            # session-dir stamps — and predict the same refusal. Gated on
            # a configured checkpoint so unconfigured projects' dry-run
            # behavior stays byte-identical. preflight_cfg is the step-15
            # gate's merged-config read, reused.
            dry_checkpoint = bale_config.get_validation_base(preflight_cfg)
            if dry_checkpoint is not None:
                # Per-sid resolution (v0.4.8, board 10 S7): the dry-run
                # predicts the real apply, so it resolves the same way —
                # against the locked sid — before probing and verifying.
                dry_resolved = bale_config.resolve_checkpoint_path(
                    dry_checkpoint, locked_sid)
                if dry_resolved != dry_checkpoint:
                    log(f"dry-run: per-session checkpoint resolved: "
                        f"{dry_checkpoint} -> {dry_resolved} "
                        f"(sid {locked_sid})")
                dry_checkpoint = dry_resolved
                dry_origin = resolve_target_branch(repo, locked_sid)
                dry_base = git(["rev-parse", f"refs/heads/{dry_origin}"],
                               cwd=repo).stdout.strip()
                dry_probe = git(
                    ["cat-file", "-e", f"{dry_base}:{dry_checkpoint}"],
                    cwd=repo, check=False)
                if dry_probe.returncode != 0:
                    fail(f"[REJECT] blind checkpoint missing at the base "
                         f"tree: bale.toml [validation] base names "
                         f"{dry_checkpoint!r}, but {dry_origin}'s tip "
                         f"({dry_base[:7]}) has no committed file at that "
                         f"path — a real apply would refuse the same way. "
                         f"A working-tree-only checkpoint is not yet "
                         f"the project's oracle (committed-is-ratified). "
                         f"Remedies: commit the checkpoint at the named "
                         f"path, or clear the key via `bale config init`.")
                # Stamp-divergence prediction (v0.3.28, session C — the
                # same rider extended): the real verification sits past
                # this exit too, and it is manifest-and-git-read-only, so
                # a dry-run predicts it. With --accept-checkpoint-change
                # given, predict the admission instead, exactly as a real
                # apply would take it.
                dry_stamp_present, dry_stamp = read_request_checkpoint_stamp(
                    repo, locked_sid)
                if dry_stamp_present:
                    dry_sha = base_tree_sha256(
                        repo, dry_base, dry_checkpoint)
                    dry_matched = (dry_sha is not None
                                   and isinstance(dry_stamp, dict)
                                   and dry_stamp.get("path") == dry_checkpoint
                                   and dry_stamp.get("sha256") == dry_sha)
                    if dry_matched:
                        log(f"dry-run: checkpoint provenance stamp "
                            f"verified ({dry_checkpoint} sha256 "
                            f"{dry_sha[:12]})")
                    elif not accept_checkpoint_change:
                        fail(format_checkpoint_stamp_refusal(
                            checkpoint_path=dry_checkpoint,
                            stamped=dry_stamp,
                            current_sha256=dry_sha or "",
                            base_sha=dry_base,
                            origin_branch=dry_origin,
                            dry_run=True,
                        ))
                    else:
                        log("dry-run: checkpoint changed since pack; a "
                            "real apply with --accept-checkpoint-change "
                            "would execute the current base-tree bytes "
                            "and record stamp_matched: false")
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
            # Per-sid resolution (v0.4.8, board 10 S7): a {sid}-bearing
            # base resolves against the LOCKED session id — the same
            # value pack's stamp resolved against — so everything
            # downstream (dangling refusal, stamp verification, syntax
            # check, execution, the telemetry stamp) reads and records
            # the resolved path. Sibling sessions with different sids
            # resolve to different files, so concurrent waves stop
            # sharing an oracle and an amendment to one session's
            # checkpoint no longer trips another's stamp. A literal
            # base resolves to itself, byte-for-byte; a config
            # retargeted between pack and apply (literal -> pattern or
            # vice versa) surfaces as a stamp-path mismatch below,
            # exactly the retargeted-path refusal the §8.5
            # verification already holds.
            resolved_cp = bale_config.resolve_checkpoint_path(
                checkpoint_path, locked_sid)
            if resolved_cp != checkpoint_path:
                log(f"per-session checkpoint resolved: {checkpoint_path} "
                    f"-> {resolved_cp} (sid {locked_sid})")
            checkpoint_path = resolved_cp
        # The ADR-0016 position-3 network grant (v0.4.5, board 10 S2):
        # bale.toml [sandbox] network, project layer only by
        # construction (merged_config never inherits the section from
        # global — SANDBOX_VALUES owns the ruling). Resolved here,
        # beside the staging strategy and the checkpoint key, because
        # the three script runs below all thread it. The two S2
        # telemetry stamps are computed beside it so every validated
        # attempt this apply records carries the same pair (BALE.md
        # §8.9): sandbox_escaped is the --no-sandbox fact (scripts ran
        # unconfined), and network_grant_exercised is true exactly when
        # confined scripts run with the grant active — an escaped run
        # exercises no grant, since nothing confined ran.
        sandbox_network = bale_config.get_sandbox_network(staging_cfg)
        sandbox_escaped = bool(no_sandbox)
        network_grant_exercised = bool(sandbox_network and not no_sandbox)
        if sandbox_network and not no_sandbox:
            log("network grant active (bale.toml [sandbox] network, "
                "project layer): apply.sh, the blind checkpoint, and "
                "validation.sh run confined WITH network — filesystem "
                "confinement and environment scrub unchanged; "
                "network_grant_exercised: true will be recorded")
        elif sandbox_network:
            log("note: bale.toml [sandbox] network is set, but "
                "--no-sandbox bypassed confinement for this invocation "
                "— nothing confined ran, so the grant is not exercised "
                "(unconfined scripts have network regardless)")
        # The §8.5 stamp verification's result, threaded into the D4
        # telemetry stamp below (v0.3.28, session C): True on a verified
        # match, False on a divergence admitted by
        # --accept-checkpoint-change, None when no checkpoint runs or
        # the request carried no provenance.checkpoint key.
        checkpoint_stamp_matched: Optional[bool] = None
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
            # Provenance stamp verification (v0.3.28, board 6 session C;
            # BALE.md §8.5) — the D5 provenance layer, sited beside its
            # dangling-refusal sibling because both need base_sha in hand
            # and both are pre-staging: hash the base-tree bytes about to
            # run and compare to the request's pack-time stamp. Divergence
            # means the oracle changed between pack and apply — a
            # legitimate planner edit or interference, and either is worth
            # stopping for. Verification runs only when the request
            # carries the provenance.checkpoint key, keeping hand-rolled
            # and pre-v0.3.28 requests on today's behavior with
            # stamp_matched: null.
            stamp_present, stamp = read_request_checkpoint_stamp(
                repo, locked_sid)
            if stamp_present:
                current_sha = base_tree_sha256(
                    repo, base_sha, checkpoint_path)
                if current_sha is None:
                    # The cat-file probe just passed; a show failure here
                    # means the base tree changed mid-apply or git itself
                    # errored — both worth stopping for.
                    fail(f"could not read the blind checkpoint "
                         f"{checkpoint_path!r} from the base tree "
                         f"{base_sha[:7]} for provenance verification")
                matched = (isinstance(stamp, dict)
                           and stamp.get("path") == checkpoint_path
                           and stamp.get("sha256") == current_sha)
                if matched:
                    checkpoint_stamp_matched = True
                    log(f"checkpoint provenance stamp verified: "
                        f"{checkpoint_path} sha256 {current_sha[:12]} "
                        f"matches the pack-time stamp")
                elif not accept_checkpoint_change:
                    fail(format_checkpoint_stamp_refusal(
                        checkpoint_path=checkpoint_path,
                        stamped=stamp,
                        current_sha256=current_sha,
                        base_sha=base_sha,
                        origin_branch=origin_branch,
                    ))
                else:
                    # force=True: an admitted oracle change is an override
                    # event of the same species as --allow-out-of-scope —
                    # the FORCE: line is the audit trail; the telemetry
                    # stamp's stamp_matched: false is the durable copy.
                    checkpoint_stamp_matched = False
                    stamped_desc = ("null (packed with no checkpoint "
                                    "configured)" if stamp is None else
                                    f"{stamp.get('path')} sha256 "
                                    f"{str(stamp.get('sha256'))[:12]}")
                    log(f"checkpoint change accepted by "
                        f"--accept-checkpoint-change: executing the "
                        f"CURRENT base-tree bytes ({checkpoint_path} "
                        f"sha256 {current_sha[:12]}) over the pack-time "
                        f"stamp ({stamped_desc}); stamp_matched: false "
                        f"will be recorded", force=True)
            else:
                log("request carries no checkpoint provenance stamp "
                    "(hand-rolled, or packed pre-0.3.28); verification "
                    "skipped — stamp_matched: null")
            # The ratified board-10 fail-fast rider: `bash -n` the
            # checkpoint's base-tree bytes here, at the same pre-staging
            # point as the dangling and provenance checks, so a
            # syntax-errored checkpoint refuses before the expensive
            # stage instead of surfacing mid-pipeline as an exit-2
            # "checkpoint itself errored" HOLD. check_response_shell_
            # syntax gates the worker's two scripts above; this is the
            # planner-script sibling.
            check_checkpoint_shell_syntax(repo, base_sha, checkpoint_path)
            log(f"blind checkpoint syntax check passed (base-tree bytes)")
            log(f"blind checkpoint configured: {checkpoint_path} "
                f"(bale.toml [validation] base, project layer; "
                f"base-tree bytes will run)")
        else:
            # The removed-oracle residue (v0.3.28, session C): the
            # request stamped a checkpoint but the merged config names
            # none now, so nothing will run and there are no
            # about-to-run bytes to verify. Logged loudly rather than
            # refused: in-flight removal is impossible (apply reads the
            # config from the repo working tree, never the staged
            # overlay), so this is a planner config edit — the same
            # accepted bale.toml residue D5 records, re-trigger: the
            # first observed worker edit to [validation] keys in a
            # merged session.
            _sp, _stamp = read_request_checkpoint_stamp(repo, locked_sid)
            if _sp and isinstance(_stamp, dict):
                log(f"note: the request stamped a blind checkpoint "
                    f"({_stamp.get('path')}, sha256 "
                    f"{str(_stamp.get('sha256'))[:12]}) but bale.toml "
                    f"names none now — the oracle was removed between "
                    f"pack and apply (a planner config edit); this "
                    f"attempt validates with the worker's script only")
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
                sandbox=not no_sandbox,
                log_path=session_log,
                network=sandbox_network,
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
                locked_sid, verbose=verbose, sandbox=not no_sandbox,
                network=sandbox_network)
            log(f"blind checkpoint exit code: "
                f"{checkpoint_result['exit_code']} ({checkpoint_path})")

        # Run validation.sh in staging. The captured output feeds the
        # telemetry record's §7.3 claim/verdict promotion (v0.3.9, B2).
        exit_code, val_output = run_validation_sh(
            repo, response_dir, staging, manifest,
            locked_sid, verbose=verbose, sandbox=not no_sandbox,
            network=sandbox_network)
        log(f"validation.sh exit code: {exit_code}")

        # The D4 telemetry stamp for every validated attempt this apply
        # records (BALE.md §8.9): key presence = post-epoch; configured
        # false = the known-zero form; when the checkpoint ran, the
        # per-source state/exit plus the executed base-tree bytes' hash.
        # stamp_matched carries the §8.5 provenance verification's
        # result (v0.3.28, session C): true on a verified match, false
        # on a divergence admitted by --accept-checkpoint-change, null
        # when the request carried no provenance.checkpoint key
        # (hand-rolled, or packed pre-0.3.28).
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
                "stamp_matched": checkpoint_stamp_matched,
            }

        # Telemetry inputs (v0.3.9, B2): session_scope was read at the
        # own-forecast drift gate above — once, before any terminal action's
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

            # Response-artifact archival ([apply].archive_dir — BALE.md
            # §8.8, the landed v0.5 candidate). Applied outcome only, and
            # sited after the merge has durably landed: a copy failure
            # logs loudly and reports in the closing banner below, but can
            # never un-apply or HOLD the merged session
            # (archive_response_artifacts' contract). Unset key = no
            # archival, no banner row — today's behavior. `archive_dir_cfg`
            # was resolved at pre-flight through the strict accessor, so a
            # malformed key refused before staging — nothing here can
            # fail() after the merge.
            archived_paths: list[str] = []
            archive_failed: list[str] = []
            if archive_dir_cfg:
                archived_paths, archive_failed = archive_response_artifacts(
                    repo, response_dir, locked_sid, archive_dir_cfg)

            # post_apply_pass hook. Silent no-op when not configured. Prompts
            # the user before invoking; a decline is logged and silent. The
            # hook runs after the merge so a hook-side failure can't unwind
            # bale's primary work — at this point the session is durably
            # applied and tagged (and any configured archival has already
            # run, so a hook that consumes the archive sees it on disk).
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
                    required_check_overrides=required_check_overridden,
                    validation_state=state,
                    validation_exit_code=exit_code,
                    validation_output=val_output,
                    checkpoint=checkpoint_stamp,
                    sandbox_escaped=sandbox_escaped,
                    network_grant_exercised=network_grant_exercised,
                    log_path=f".bale/logs/{locked_sid}.log",
                    clarification=read_clarification_summary(
                        repo, locked_sid),
                ))
            # Auto-sweep (v0.3.32; BALE.md §8.8): config-gated commit
            # of exactly what this invocation wrote — the telemetry
            # record above plus the archive copies. Sited after the
            # merge completed, the branch advanced, and the record
            # exists on disk, so the sweep commit never interleaves
            # with the merge — it is its own commit on top. `enabled`
            # was resolved at pre-flight (sweep_cfg), so nothing here
            # can fail() post-merge; sweep_commit itself is loud and
            # never fatal.
            sweep_result = sweep_commit(
                repo, locked_sid, "applied",
                ([telemetry_rel] if telemetry_rel else [])
                + list(archived_paths),
                enabled=sweep_cfg)
            summary_rows = [
                ("tag", f"applied/{locked_sid}"),
                ("branch", f"{origin_branch} (merged — {merged_note})"),
                ("files", f"{len(manifest['changes'])} changed"),
                ("staging", f"{staging} (preserved for inspection)"),
            ]
            # Archive row only when [apply].archive_dir is configured —
            # unset stays byte-identical to the pre-archival banner. The
            # failure form is loud in the banner as well as the log
            # (no-silent-skip, CLAUDE.md §6); the shipped-nothing form is
            # named too, since "configured but empty" is a fact the
            # operator should see rather than infer.
            if archive_dir_cfg:
                if archive_failed:
                    detail = (f"copy FAILED for {', '.join(archive_failed)} "
                              f"— see log; merge unaffected")
                    if archived_paths:
                        detail = (f"{len(archived_paths)} file(s) → "
                                  f"{archive_dir_cfg}/{locked_sid}/; {detail}")
                    summary_rows.append(("archive", detail))
                elif archived_paths:
                    # "(uncommitted)" is the standing contract — except
                    # when this invocation's sweep just committed the
                    # copies, where it would be false on its face.
                    archived_state = (
                        "committed by sweep"
                        if sweep_result is not None
                        and sweep_result.get("status") == "committed"
                        else "uncommitted")
                    summary_rows.append(
                        ("archive",
                         f"{len(archived_paths)} file(s) → "
                         f"{archive_dir_cfg}/{locked_sid}/ "
                         f"({archived_state})"))
                else:
                    summary_rows.append(
                        ("archive", "nothing to archive — response shipped "
                                    "no README.md or notes.md"))
            summary_rows.append(
                ("telemetry",
                 f"recorded {telemetry_rel}" if telemetry_rel
                 else "write failed — see log"))
            # Sweep row only when [apply].sweep is enabled (sweep_result
            # is None otherwise) — unset stays byte-identical to the
            # pre-sweep banner, the archive-row precedent. The detail is
            # the same loud line the log carries: committed-as,
            # nothing-to-commit, or the skip with its reason.
            if sweep_result is not None:
                summary_rows.append(("sweep", sweep_result["detail"]))
            print(format_summary_block(
                summary_rows,
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
                    # v0.3.34, additive: the sweep_commit return from
                    # above — null when [apply].sweep is unset/false.
                    sweep=sweep_result,
                    # Additive archival result ([apply].archive_dir): an
                    # object only when the key is configured — unset keeps
                    # the pre-archival report (modulo the additive null).
                    archive=(None if not archive_dir_cfg else {
                        "dir": f"{archive_dir_cfg}/{locked_sid}",
                        "copied": archived_paths,
                        "failed": archive_failed,
                    }),
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
                    required_check_overrides=required_check_overridden,
                    validation_state=state,
                    validation_exit_code=exit_code,
                    validation_output=val_output,
                    checkpoint=checkpoint_stamp,
                    sandbox_escaped=sandbox_escaped,
                    network_grant_exercised=network_grant_exercised,
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
        # --verbose (v0.4.0, the accepted 005 rider) rides into the
        # helper the same way cmd_revert's call does: the discard's
        # captured git output streams live; the default path is
        # byte-identical.
        status = _discard_hold_state(repo, locked_sid, verbose=verbose)
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
                required_check_overrides=required_check_overridden,
                validation_state=state,
                validation_exit_code=exit_code,
                validation_output=val_output,
                checkpoint=checkpoint_stamp,
                sandbox_escaped=sandbox_escaped,
                network_grant_exercised=network_grant_exercised,
                log_path=f".bale/logs/{locked_sid}.log",
                clarification=read_clarification_summary(repo, locked_sid),
            ))
        # Auto-sweep (v0.3.32; BALE.md §8.8): the walkthrough revert is
        # a closing event and _discard_hold_state's git mutation is
        # complete. `enabled` resolved at pre-flight (sweep_cfg) — the
        # no-post-outcome-fail() contract, same as the applied path.
        sweep_result = sweep_commit(repo, locked_sid, "reverted",
                                    [telemetry_rel] if telemetry_rel else [],
                                    enabled=sweep_cfg)
        print(format_summary_block(
            [
                ("branch", f"{status['origin_branch']} ({sid_branch} deleted)"),
                ("lock", "cleared"),
                # v0.3.35: rendered from the machine facts by
                # bale_report.format_staging_row (the accepted
                # session-008 fold-in) — same projection cmd_revert's
                # summary block uses, since both paths run the same
                # _discard_hold_state cleanup.
                ("staging", format_staging_row(
                    state=status["staging_state"],
                    path=status["staging_path"],
                    error=status["staging_error"])),
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
                # v0.3.34, additive: the sweep_commit return from above
                # — null when [apply].sweep is unset/false.
                sweep=sweep_result,
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
    if args.tarball is not None:
        tarball_path = resolve_inbound_path(args.tarball, cwd, search_paths)
        if not tarball_path.is_file():
            # Only reachable for the absolute-path branch (relative + search
            # paths configured already fails inside the helper); the empty-
            # search-paths relative branch reaches here only if (cwd/arg)
            # doesn't exist. Either way, the existing message is right.
            fail(f"tarball not found: {tarball_path}")
    else:
        # Bare form (board 51): resolved below, after the inspection and
        # json branches — the inspection flags refuse the bare form (they
        # are deliberately session-independent, and bare resolution is
        # keyed on the open session), and json mode must be enabled before
        # the bare path's identity echo and prompt so those land on stderr
        # per the stream discipline.
        tarball_path = None

    # `--show-apply-script` / `--show-validator`: pure inspection. Print the
    # requested deliverable(s) from the tarball and exit. Deliberately ahead
    # of the lock and clean-tree guards — inspecting what a tarball would run
    # shouldn't require an open session or a pristine worktree.
    if args.show_apply_script or args.show_validator:
        if tarball_path is None:
            fail(
                "--show-validator / --show-apply-script need the tarball "
                "named: inspection works without an open session, and "
                "bare resolution is keyed on the open session, so the "
                "two don't compose. Name the tarball explicitly: "
                "bale apply <response-NNN.tar.gz> --show-validator."
            )
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

    # Bare form: resolve the newest matching response tarball against the
    # single open session, echo its identity, take the y/N. Every refusal
    # inside is a fail() with a remedy; on return, the resolved path flows
    # into exactly the code the argumented form runs.
    if tarball_path is None:
        tarball_path = resolve_bare_apply_tarball(
            repo, cwd, cfg, args, search_paths)

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
            allow_missing_required_check=args.allow_missing_required_check,
            accept_checkpoint_change=args.accept_checkpoint_change,
            no_sandbox=args.no_sandbox,
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
            allow_missing_required_check=args.allow_missing_required_check,
            accept_checkpoint_change=args.accept_checkpoint_change,
            no_sandbox=args.no_sandbox,
        )
    except SystemExit as e:
        record_rejected_attempt(repo, locked_sid, "apply",
                                 tarball_path.name, e)
        raise
