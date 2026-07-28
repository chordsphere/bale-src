"""bale_report — end-of-command result assembly and rendering.

This module owns the result-reporting surface of the pack and apply
pipelines: the shared end-of-run summary formatter every command finishes on
(`format_summary_block`, with its private word-wrap helper
`_wrap_value_lines`), the BALE.md §8.7 apply walkthrough summary builder for
the PASS/HOLD verdicts (`format_walkthrough_summary`), the TARBALL.md §5.6.3
bailout banner (`print_bailout_banner`), its §5.9.3 clarification sibling
(`print_clarification_banner`), the `bale apply --dry-run` plan
report (`format_dry_run_report`), the machine-readable pack report
(`format_pack_json`, added in v0.2.7 for `bale pack --json`), its apply
twin (`format_apply_json`, added in v0.2.8 for `bale apply --json`), and its
status sibling (`format_status_json`, added in v0.2.9 for `bale status
--json`), plus the json-mode stream-discipline state the machine reports share
(`enable_json_mode` / `json_mode` / `emit_json_line`, v0.2.8), and — v0.3.0,
with the ADR-0006 session registry — the two status human-row value
formatters (`format_open_sessions_value`, `format_integration_lock_value`),
placed here because status rendering, human rows and json keys alike, is
this module's surface. v0.3.2 (the ADR-0006 command threading) adds two
more to that status family: `format_scope_value`, rendering one session's
recorded ADR-0007 scope (used for status's `scope` row, per-sid in
`format_open_sessions_value`'s listing — which grew an optional `scopes`
mapping — and reflected in `format_status_json`'s additive `scopes` key),
and `format_integration_holder`, the one holder phrase the acquire-time
refusal, the status row, and `bale unlock --integration` all share.
v0.3.11 (board 12 — display only) adds `format_staging_value` to the same
family: one session's effective staging posture (strategy plus declared
untracked inputs, BALE.md §8.3 step 2) as a row value, used for status's
`staging` row, per-sid in `format_open_sessions_value`'s listing — which
grew the optional `staging_strategy` / `staging_untracked_inputs` pair —
and reflected in `format_status_json`'s additive per-session
strategy/untracked_inputs keys. The human-facing
four were extracted from `bin/bale`'s sections 16
("Apply: helpers") and 18 ("Apply") in v0.2.6 — the fifth sibling module and
the fourth extraction, after `bale_config` (v0.0.4), `bale_validate`
(v0.1.2), and `bale_staging` (v0.1.3), using the same sibling-import
mechanism. The move also resolves the note that had sat on
`format_summary_block` since the formatter landed: "promote this into a
dedicated output-formatting home when the natural moment arrives."

One rule drives the human-facing renderers, and it is stated here so it
lives in one place: the crisp summary is the LAST thing printed, where the
terminal cursor and the reader's eye come to rest. Every command that finishes with a
status report — pack, apply (its PASS / HOLD / REVERT / BAILOUT / CLARIFICATION banners and
the walkthrough summary), revert, unlock, handoff, status — ends on the same
shape: a leading blank line, an optional `[STATUS] <sid>` headline, a block
of two-space-indented, colon-aligned label/value rows, and optional verbatim
trailer lines (the actionable next step). Callers that also emit bulky
reference material (the walkthrough's notes.md body — plus legacy
next-prompt.md, tolerated per TARBALL.md §5.5 — and diffstat, the bailout's
handoff excerpt) print that material FIRST and the summary block LAST, so a
long reference body never pushes the scannable verdict off the top of the
screen. The builders here are pure string assemblers — they print nothing;
the caller prints what they return. `print_bailout_banner` and
`print_clarification_banner` are the deliberate exceptions (they print),
because their output interleaves reference material and the summary block
in a fixed order (§5.6.3 / §5.9.3) that no caller should have to
re-derive.

The json renderers (`format_pack_json`, `format_apply_json`,
`format_status_json`) sit outside
that rule because for a machine consumer the verdict is the whole report:
each renders its command's outcome as ONE line of JSON whose keys are a
stable contract for downstream tooling (see their docstrings). Since v0.2.8
json mode also carries STREAM DISCIPLINE, owned here as three tiny state
functions: `enable_json_mode()` (called once by cmd_pack/cmd_apply/cmd_status
when --json is passed) saves the real stdout and rebinds `sys.stdout` to
`sys.stderr`, so every `[bale] ` log line, prompt, hook banner, and human
reference block the command produces lands on stderr without any print site
changing; `emit_json_line()` writes the one report line to the saved real
stdout; `json_mode()` is the accessor pass-through call sites gate on. The
consumer contract is therefore: on the reporting paths, stdout carries
exactly one JSON line (pack: exit 0; apply: exit 0, plus the held/reverted
exit-1 outcomes; status: exit 0), and error paths exit through fail() —
stderr, non-zero —
with nothing on stdout. Human (non---json) mode is untouched: the swap never
happens and every stream keeps its pre-v0.2.8 behavior byte-for-byte.

Behavior-preserving move: the functions keep the signatures, bodies, and
call sites they had in `bin/bale`. The public entry points
(`format_summary_block`, `format_walkthrough_summary`,
`print_bailout_banner`, `format_dry_run_report`, since v0.2.7
`format_pack_json`, since v0.2.8 `format_apply_json` plus the json-mode
trio `enable_json_mode` / `json_mode` / `emit_json_line`, and since v0.2.9
`format_status_json`) are pulled back into
`bin/bale`'s namespace via `from bale_report import ...`, so every caller —
the pack summary, the apply pipeline's walkthrough and terminal-action
banners, the dry-run path, revert, unlock, handoff, and status — still
writes them unqualified, the by-name convention `bale_validate` and
`bale_staging` established. `_wrap_value_lines` is private to this cluster
(its only caller is `format_summary_block`) and is not re-exported.

Imported by `bin/bale` as a sibling module: the `bin/` directory is on the
import path because `bin/bale` prepends its resolved directory to
`sys.path` (so the import works even when bale is invoked through a symlink
on `PATH`) — the same mechanism behind the other four siblings.

The shared helpers these functions need from `bin/bale` — `git` (the one
`git diff --stat` call in `format_walkthrough_summary`) and `fail` plus the
handoff-section slicer `first_section_of_handoff` (both in
`print_bailout_banner`) — are pulled from `__main__` lazily, i.e. imported
inside the functions that call them rather than at module top, exactly as
the other siblings do. The lazy form sidesteps the circular-import hazard
(`bin/bale` imports this module at load time, before its own helpers are
defined) and keeps the dependency visible at the call site.
`first_section_of_handoff` itself stays in `bin/bale` next to its twin
`reading_plan_section` — both slice handoff.md by `## ` heading, and the
pair reads as one unit there; this module consumes, not owns, that slicing.
Like `bale_staging`, this module needs no path constants from `bin/bale`;
every path these functions touch derives from their arguments.

v0.3.9 (session B2) adds the telemetry-record cluster — a third banner
section at the end of the file: `telemetry_record_path`,
`parse_claim_verdict_block` (promotes the TARBALL.md §7.3 claims-vs-verdict
reconciliation out of the transient session log), `build_telemetry_attempt`
(assembles one apply-close attempt entry from data the call site already
holds), and `write_telemetry_record` (the read-append-write persistence of
`claude/telemetry/<sid>.json`, schema `telemetry-record.schema.json`;
update semantics in BALE.md §8.9). It lives here because the module's
charter is end-of-command result assembly, and the record is exactly that —
assembled once per terminal apply outcome, persisted instead of printed.
`write_telemetry_record` is the second deliberate exception to the
pure-string-assembler rule (after the two banner printers): it writes a
file, never raises to its caller, and reports failure through the lazy
`__main__` `log` plus a `None` return the call site renders honestly.
`format_apply_json` gains the additive `telemetry` key in the same session
— path string when a record was written, null otherwise — under the
existing key-stability rules.

v0.3.10 (board item 2, the own-scope drift gate) adds
`format_scope_drift_refusal` — the human rendering of the apply
pre-flight refusal (BALE.md §8.1 step 14, §11 row 22): offending paths,
declared scope, any partially-admitted overrides, and the three remedies,
built on `format_summary_block` per the module's rules (pure string
assembler; the block is the whole output, so summary-last holds
trivially). `format_apply_json` gains the `scope-drift-refused` outcome
and the additive nullable `drift` key (the refusal's machine detail), and
`build_telemetry_attempt` gains `overridden_paths` — the bale-computed
stamp of what a per-invocation `--allow-out-of-scope` admitted, uniform
empty-list shape when none. `bin/bale` keeps wiring only, per the
standing division.

See claude/context/bale-internals.md for how this module sits next to
`bin/bale` and the other siblings.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def format_summary_block(
    rows: list[tuple[str, str]],
    *,
    status: Optional[str] = None,
    sid: Optional[str] = None,
    trailer: Optional[list[str]] = None,
    wrap_width: Optional[int] = None,
) -> str:
    """Render the canonical end-of-run summary block as a single string.

    `rows` are (label, value) pairs rendered as `  <label>: <value>` with the
    colons aligned on the longest label and a two-space indent. When both
    `status` and `sid` are given they prepend a `  [STATUS] <sid>` headline —
    the form the eye locks onto, matching the apply PASS / HOLD / REVERT /
    BAILOUT banners. Commands with no verdict (pack, handoff) pass neither and
    get rows only. `trailer` lines are emitted verbatim after a blank line, for
    the actionable next step ("Send the tarball to Claude...", "Next step:
    ...").

    `wrap_width` is opt-in long-value handling, added for `bale status` whose
    values (a wordy session goal, a long outbox listing) overflow a terminal
    line where the banner callers' values — sids, branch names, exit codes —
    never do. When it is None (every caller except status) the row-rendering
    path is byte-for-byte the original single-line form, so this stays a pure
    addition with no effect on the pack/apply/handoff/revert/unlock banners.
    When it is set, a value is split on embedded newlines and each segment is
    word-wrapped to fit `wrap_width` columns, with continuation lines indented
    to align under the value column. Long unbreakable tokens (tarball
    filenames, paths) are kept whole rather than chopped mid-token. The headline
    and the trailer are never wrapped: the trailer carries copy-pasteable
    command hints that must not break across lines.

    The returned block opens with a blank line and has NO trailing blank; the
    caller prints it (its print adds the final newline) and is responsible for
    any extra spacing before a following prompt. Pure: builds a string, prints
    nothing.
    """
    if (status is None) != (sid is None):
        # Half a headline is a caller bug — both or neither.
        raise ValueError(
            "format_summary_block: status and sid must be given together"
        )
    lines: list[str] = [""]
    if status is not None:
        lines.append(f"  [{status}] {sid}")
    width = max((len(label) for label, _ in rows), default=0)
    # Column where a value begins: two-space indent + padded "label:" + one
    # space. Continuation lines (wrap mode only) align under it.
    value_col = 2 + (width + 1) + 1
    for label, value in rows:
        prefix = f"  {(label + ':'):<{width + 1}} "
        if wrap_width is None:
            lines.append(f"{prefix}{value}")
            continue
        segments = _wrap_value_lines(value, max(wrap_width - value_col, 20))
        first = segments[0] if segments else ""
        lines.append(f"{prefix}{first}")
        cont_indent = " " * value_col
        for extra in segments[1:]:
            lines.append(f"{cont_indent}{extra}" if extra else "")
    if trailer:
        lines.append("")
        lines.extend(trailer)
    return "\n".join(lines)


def _wrap_value_lines(value: str, avail: int) -> list[str]:
    """Split `value` into physical lines that fit `avail` columns.

    Embedded newlines in `value` are honoured as hard breaks (the caller uses
    them to lay an outbox listing out one tarball per line); each resulting
    segment is then word-wrapped to `avail`. `break_long_words` and
    `break_on_hyphens` are both off so a single long token — a tarball filename
    or a repo path — is never split mid-token; it overflows its line intact,
    which is far more readable than a path chopped at an arbitrary column. Pure;
    returns the list of lines (an empty segment maps to a single empty line so a
    blank value position is preserved rather than dropped).
    """
    out: list[str] = []
    for segment in value.split("\n"):
        if not segment:
            out.append("")
            continue
        wrapped = textwrap.wrap(
            segment,
            width=avail,
            break_long_words=False,
            break_on_hyphens=False,
        )
        out.extend(wrapped or [""])
    return out


def format_walkthrough_summary(
    *,
    sid: str,
    origin_branch: str,
    sid_branch: str,
    state: str,
    exit_code: int,
    manifest: dict,
    response_dir: Path,
    staging: Path,
    repo: Path,
) -> str:
    """Build the BALE.md §8.7 walkthrough summary block as a single string.

    `state` is "PASS" or "HOLD". Pure aside from one `git diff --stat` call
    against the live repo (which is the cheapest way to get an accurate
    origin..sid_branch diffstat and matches the inspection command we tell
    the user to run). The caller prints the returned string.
    """
    from __main__ import git  # lazy — see module docstring

    # Reference material first, crisp verdict last. Everything appended to
    # `ref` below is the scrollable detail — the per-check claims table, the
    # diffstat, the notes.md body (and legacy next-prompt.md, if a
    # pre-retirement response ships one), the inspect commands. The
    # one-glance verdict block is built afterwards and returned *last*, so it
    # lands at the bottom of the output where the cursor and the eye settle.
    # (Before this change the [PASS]/[HOLD] headline printed first and a long
    # notes.md or next-prompt.md body could push it clean off the screen, so
    # the eye landed on the inspect commands instead of the verdict.)
    ref: list[str] = []

    # Claims-per-check detail per TARBALL.md §5.3. The actual claim-vs-verdict
    # reconciliation lives in validation.sh's output (already streamed to the
    # log file before this point); we surface the claims side here so the
    # walkthrough is self-contained for review. The exit code is rolled up
    # into the verdict block below — this is the per-check breakout.
    claims = manifest.get("claims", {}) or {}
    if claims:
        ref.append("")
        ref.append("  claims (verdict in .bale/logs/{}.log):".format(sid))
        width = max(len(k) for k in claims)
        for check, claim in claims.items():
            ref.append(f"    {check:<{width}}  claim={claim}")

    # Diffstat between origin and the bale branch. Both verdicts hold a
    # session commit on the bale branch since ADR-0008 (a HOLD is a
    # committed branch nothing has checked out, not staged changes in the
    # user's checkout), so one rev-range diff covers PASS and HOLD alike —
    # and it matches the inspection command the walkthrough prints.
    diff_args = ["diff", "--stat", f"{origin_branch}..{sid_branch}"]
    diff_label = f"origin..{sid_branch}"
    try:
        diffstat = git(diff_args, cwd=repo, check=False).stdout.rstrip()
    except subprocess.CalledProcessError as e:
        diffstat = f"(diffstat unavailable: {e.stderr or e})"
    ref.append("")
    ref.append(f"  diffstat ({diff_label}):")
    if diffstat:
        for ln in diffstat.splitlines():
            ref.append(f"    {ln}")
    else:
        ref.append("    (empty)")

    # notes.md from the response — surfaced inline per BALE.md §8.7. Silent
    # skip when absent; absence is the canonical signal of "nothing extra to
    # surface" (TARBALL.md §5.1, §5.4). This is the longest thing the
    # walkthrough prints, which is exactly why it sits up here in the
    # reference block rather than just above the prompt.
    #
    # next-prompt.md was retired as a response artifact (TARBALL.md §5.5):
    # nothing new ships it, and follow-up suggestions now ride in notes.md's
    # Proposals section (TARBALL.md §5.4.1). The walkthrough still reads it,
    # by design — pre-retirement response tarballs remain reviewable during
    # the transition — but labels the body deprecated rather than blending
    # it in silently. Drop it from this tuple when the archive of legacy
    # responses no longer matters.
    for fname in ("notes.md", "next-prompt.md"):
        fpath = response_dir / fname
        if not fpath.is_file():
            continue
        header = fname
        if fname == "next-prompt.md":
            header = f"{fname} (deprecated — retired per TARBALL.md §5.5)"
        try:
            body = fpath.read_text(encoding="utf-8").rstrip()
        except OSError as e:
            ref.append("")
            ref.append(f"  --- {header} (unreadable: {e}) ---")
            continue
        if not body:
            continue  # present but empty — treat as silent skip
        ref.append("")
        ref.append(f"  --- {header} ---")
        for ln in body.splitlines():
            ref.append(f"  {ln}" if ln else "")
        ref.append(f"  --- end {fname} ---")

    # Inspection commands. The user runs these manually if they want to dig
    # past the summary; we don't shell out, just print the commands.
    ref.append("")
    ref.append("  inspect:")
    ref.append(f"    git diff {origin_branch}..{sid_branch}")
    ref.append(f"    git log {sid_branch}")
    ref.append(f"    cat .bale/logs/{sid}.log")
    ref.append(f"    ls {staging}/")

    # Crisp verdict block LAST — the thing the eye lands on. Origin/branch/
    # summary plus a one-line validation roll-up; the per-check table and the
    # full diff are in the reference block above.
    if claims:
        validation_row = (
            f"exit={exit_code} ({len(claims)} claim(s); "
            f"per-check table above, verdict in log)"
        )
    else:
        validation_row = f"exit={exit_code} (no project-level claims)"
    branch_state = (
        f"{sid_branch} (committed; ready to merge)" if state == "PASS"
        else f"{sid_branch} (committed; held for inspection — "
             f"checkout untouched)"
    )
    summary_block = format_summary_block(
        [
            ("origin", origin_branch),
            ("branch", branch_state),
            ("summary", manifest.get("summary", "(no summary)")),
            ("validation", validation_row),
        ],
        status=state,
        sid=sid,
    )
    # Trailing blank separates the verdict block from the prompt the caller
    # prints next.
    return "\n".join(ref) + "\n" + summary_block + "\n"


def print_bailout_banner(manifest: dict, handoff_path: Path,
                         tarball_basename: str) -> None:
    """Per TARBALL.md §5.6.3 steps 1-3: the manifest.summary, the first
    section of handoff.md, a clear banner identifying the response as a
    bailout, and the explicit next-step instruction.

    The summary paragraph and the handoff excerpt are the bulky reference
    material, so they print FIRST, bracketed by `--- … ---` separators since
    they don't fit the label-value shape. The crisp `[BAILOUT]` banner and the
    `bale handoff` next step print LAST, via format_summary_block, so the eye
    lands on the verdict and the action even when the handoff excerpt runs
    long — the same reordering applied to the apply walkthrough summary.
    """
    from __main__ import fail, first_section_of_handoff  # lazy — see module docstring

    try:
        handoff_text = handoff_path.read_text(encoding="utf-8")
    except OSError as e:
        # handoff.md was present at the file-existence check in
        # _apply_bailout; an unreadable file here is a real surprise.
        # Surface and bail.
        fail(f"could not read handoff.md: {e}")
    first_section = first_section_of_handoff(handoff_text)

    # Reference material first: the summary paragraph and the handoff excerpt
    # (the part that can run long).
    print()
    print(f"  --- summary ---")
    for line in manifest["summary"].splitlines() or [""]:
        print(f"  {line}")
    print()
    print(f"  --- handoff (first section) ---")
    if first_section:
        for line in first_section.splitlines():
            print(f"  {line}")
    else:
        print(f"  (handoff.md has no `## ` section; check the file directly)")

    # Crisp banner + next step LAST.
    print(format_summary_block(
        [("applied", "no changes — apply.sh and validation.sh were not run")],
        status="BAILOUT",
        sid=manifest["session_id"],
        trailer=["  Next step:", f"    bale handoff {tarball_basename}"],
    ))
    print()


def print_clarification_banner(manifest: dict) -> None:
    """Per TARBALL.md §5.9.3 steps 1-2: the manifest.summary, the questions
    block rendered inline, a clear banner identifying the response as a
    clarification, and the explicit next step.

    The bailout banner's sibling, and the same layout rule applies: the
    bulky reference material (the summary paragraph and the questions, which
    can run long) prints FIRST, and the crisp `[CLARIFICATION]` banner plus
    the next step print LAST via format_summary_block, so the eye lands on
    the verdict and the action. Unlike the bailout there is no companion
    file to read — the questions ride in the manifest, already
    schema-validated and shape-checked (bale_validate) before the apply
    pipeline forks here — so this printer takes only the manifest.

    Prints (the deliberate exception to the build-a-string rule, same as
    print_bailout_banner): the output interleaves reference material and
    the summary block in a fixed §5.9.3 order no caller should re-derive.
    """
    print()
    print(f"  --- summary ---")
    for line in manifest["summary"].splitlines() or [""]:
        print(f"  {line}")

    questions = manifest.get("questions", []) or []
    print()
    print(f"  --- questions ({len(questions)}) ---")
    for i, q in enumerate(questions, start=1):
        if i > 1:
            print()
        # First line of the question carries the [n] marker; continuation
        # lines and the three follow-up fields indent under it. Values are
        # printed as-authored (no re-wrapping), matching the summary and
        # handoff excerpts above and in the bailout banner.
        q_lines = q["question"].splitlines() or [""]
        print(f"  [{i}] {q_lines[0]}")
        for ln in q_lines[1:]:
            print(f"      {ln}")
        for label, key in (("while doing", "context"),
                           ("would assume", "default_assumption"),
                           ("why blocked", "why_blocked")):
            v_lines = q[key].splitlines() or [""]
            print(f"      {label}: {v_lines[0]}")
            for ln in v_lines[1:]:
                print(f"      {' ' * (len(label) + 2)}{ln}")

    # Crisp banner + next step LAST. The load-bearing line is the session
    # row: unlike a bailout, the lock is retained — the session stays open
    # for the worker's follow-up response (TARBALL.md §5.9.3 step 4).
    print(format_summary_block(
        [
            ("applied", "no changes — apply.sh and validation.sh were not run"),
            ("session", "still open — lock retained for the follow-up response"),
        ],
        status="CLARIFICATION",
        sid=manifest["session_id"],
        trailer=[
            "  Next step:",
            "    answer the questions in the worker's chat, then apply its",
            "    follow-up response against this same session",
            "    (`bale unlock` and repack if the gap invalidates the request)",
        ],
    ))
    print()


def format_dry_run_report(manifest: dict, sid: str, *, response_kind: str) -> str:
    """Build the `--dry-run` plan summary as a single string.

    Reports what a real `bale apply` would do with this tarball, having
    already passed every read-only pre-flight check (extract, syntax,
    manifest schema, responds_to, presence/sha256/path-safety). Pure — the
    caller prints the returned string and returns 0.

    `response_kind` is the manifest's (defaulted) kind — "normal",
    "bailout", or "clarification" — passed explicitly by the caller, which
    has already resolved the `.get(..., "normal")` default at its fork
    point. (Signature changed from `is_bailout: bool` when the
    clarification kind landed; a three-way kind doesn't reduce to a bool.)
    """
    lines: list[str] = [""]
    lines.append(f"  [DRY RUN] {sid}")
    lines.append(f"  summary: {manifest.get('summary', '(no summary)')}")

    if response_kind == "bailout":
        # A bailout carries no files and isn't applied; a real apply would
        # print the §5.6.3 handoff banner and stop. Say so rather than
        # listing an empty change set as if it were applicable.
        lines.append("")
        lines.append("  response_kind: bailout")
        lines.append("  apply would: print the handoff banner and stop "
                     "(no files applied).")
        lines.append("  next step:   bale handoff <tarball>")
        lines.append("")
        lines.append("  DRY RUN — nothing applied, working tree untouched.")
        lines.append("")
        return "\n".join(lines)

    if response_kind == "clarification":
        # A clarification carries no files either; a real apply would print
        # the §5.9.3 questions banner and stop — and, unlike a bailout,
        # leave the session open (the lock is retained for the worker's
        # follow-up response).
        questions = manifest.get("questions", []) or []
        lines.append("")
        lines.append("  response_kind: clarification")
        lines.append(f"  apply would: print the questions banner "
                     f"({len(questions)} question(s)) and stop "
                     "(no files applied; the session stays open).")
        lines.append("  next step:   answer the questions in the worker's chat")
        lines.append("")
        lines.append("  DRY RUN — nothing applied, working tree untouched.")
        lines.append("")
        return "\n".join(lines)

    changes = manifest.get("changes", []) or []
    by_action = {"created": 0, "modified": 0, "deleted": 0}
    for c in changes:
        by_action[c["action"]] = by_action.get(c["action"], 0) + 1
    lines.append(
        f"  changes: {len(changes)} "
        f"({by_action['created']} created, "
        f"{by_action['modified']} modified, "
        f"{by_action['deleted']} deleted)"
    )
    lines.append("")
    lines.append("  would apply:")
    if changes:
        width = max(len(c["action"]) for c in changes)
        for c in changes:
            lines.append(f"    {c['action']:<{width}}  {c['path']}")
    else:
        lines.append("    (none)")

    will_run = manifest.get("validation_will_run", []) or []
    lines.append("")
    if will_run:
        lines.append("  validation.sh would run:")
        for item in will_run:
            lines.append(f"    - {item}")
    else:
        lines.append("  validation.sh would run: (nothing declared)")

    lines.append("")
    lines.append("  DRY RUN — validated only. No branch, no staging applied "
                 "to the worktree, no commit.")
    lines.append("")
    return "\n".join(lines)


def format_scope_drift_refusal(*, sid: str, scope: list, refused: list,
                               overridden: list,
                               telemetry: Optional[str],
                               dry_run: bool = False) -> str:
    """Render the own-scope drift refusal (BALE.md §8.1 step 14, §11 row 22).

    The human face of the v0.3.10 drift-to-contract gate: a response's
    changes[] landed on paths outside the session's own declared scope,
    and the apply refused before any staging or git work. The block names
    every offending path and the declared scope — the two facts the
    operator dispatches on — plus any paths a partial --allow-out-of-scope
    did admit, and closes with the three remedies as trailer lines. The
    session stays open, which is why every remedy is a re-run rather than
    a repack-from-scratch.

    Follows the module's summary-block-last rule trivially (the block is
    the whole output) and the pure-string-assembler rule: builds a string,
    prints nothing; the json twin is format_apply_json's `drift` key, not
    this renderer. Under `dry_run` the telemetry row reports that no
    record was written (a dry-run has no outcome — BALE.md §8.9) and the
    headline notes the prediction.

    An empty `scope` is the read-only session shape (v0.3.15): the
    declared-scope row names the session read-only rather than printing
    an empty string, and the remedies drop the regenerate-inside-scope
    line — there is no inside; the operator either overrides per path,
    knowing exactly that they are landing changes from a session packed
    to land none, or repacks a session shaped to land the work.
    """
    read_only = not scope
    rows: list[tuple[str, str]] = [
        ("out of scope", ", ".join(refused)),
        ("declared scope",
         "(read-only session — empty scope; lands nothing)"
         if read_only else ", ".join(scope)),
    ]
    if overridden:
        rows.append(("admitted by flag", ", ".join(overridden)))
    if dry_run:
        rows.append(("dry-run", "a real apply would refuse the same way"))
        rows.append(("telemetry", "not recorded (dry-run has no outcome)"))
    else:
        rows.append(("telemetry",
                     f"recorded {telemetry}" if telemetry
                     else "write failed — see log"))
    if read_only:
        trailer = [
            f"Session {sid} was packed read-only: its scope lands "
            f"nothing by design. Nothing was staged or committed, and "
            f"the session stays open. Either:",
            "  - admit specific paths deliberately, knowing they land "
            "from a read-only session: `bale apply <tarball> "
            "--allow-out-of-scope <path>` (repeat per path),",
            f"  - or land the work from a session shaped to land it: "
            f"`bale unlock {sid}` and re-pack without --read-only, with "
            f"the includes the work needs.",
        ]
    else:
        trailer = [
            "The session stays open; nothing was staged or committed. "
            "Either:",
            "  - regenerate the response inside the declared scope and "
            "re-run `bale apply`,",
            "  - admit specific paths deliberately: `bale apply <tarball> "
            "--allow-out-of-scope <path>` (repeat per path),",
            f"  - or rescope: `bale unlock {sid}` and re-pack with the "
            f"includes the work actually needs.",
        ]
    return format_summary_block(
        rows,
        status="SCOPE-DRIFT-REFUSED",
        sid=sid,
        trailer=trailer,
    )


# --- json output mode (v0.2.8) ---
#
# Shared state for `bale pack --json` and `bale apply --json`. The stream-
# discipline half of the json-mode contract lives in these three functions;
# the report-rendering half lives in format_pack_json / format_apply_json
# below. See the module docstring for the consumer contract.

_json_real_stdout = None  # saved by enable_json_mode; where emit_json_line writes


def enable_json_mode() -> None:
    """Switch this process into json output mode (the stream-discipline half).

    Json mode is a two-part contract (v0.2.8): stdout carries exactly one
    line of JSON — the machine-readable end-of-run report — and every other
    line the command produces (`[bale] ` log lines, prompts, hook banners,
    the human reference blocks) goes to stderr. This function implements the
    "every other line" half in one move: it saves the real stdout and
    rebinds `sys.stdout` to `sys.stderr`, so every existing `print()` /
    `input()`-prompt / `sys.stdout.write` in bale and its sibling modules
    lands on stderr without any print site changing — which is also what
    keeps human mode byte-identical: when the swap never happens, no code
    path differs. `emit_json_line` writes to the saved real stdout.

    Called once, by cmd_pack / cmd_apply, as soon as the --json flag is
    known and before any output. Idempotent: a second call is a no-op, so
    the saved handle can never be clobbered with the already-swapped
    stream. There is deliberately no disable — the mode is per-process,
    decided by the CLI flag, and lasts until exit.

    Two surfaces the sys-level rebinding does not reach, by design of the
    mechanism rather than oversight: session-log journaling (log() writes
    the same lines to the log file regardless of which terminal stream the
    copy went to — unchanged, and correct), and child processes that
    inherit the real file descriptors (hook scripts; run_hook in bin/bale
    routes their stdout to stderr under json mode for exactly this reason).
    """
    global _json_real_stdout
    if _json_real_stdout is not None:
        return
    _json_real_stdout = sys.stdout
    sys.stdout = sys.stderr


def json_mode() -> bool:
    """True when enable_json_mode() has switched this process into json
    output mode. The pass-through call sites in bin/bale (the apply
    pipeline's terminal reporting points, run_hook's fd routing) gate on
    this accessor instead of threading a flag through _apply_pipeline's
    signature."""
    return _json_real_stdout is not None


def emit_json_line(line: str) -> None:
    """Write `line` plus a newline to the REAL stdout and flush.

    In json mode this is the only writer that reaches the process's
    original stdout stream; everything else was rebound to stderr by
    enable_json_mode. Outside json mode (defensive — every current caller
    is gated on the --json flag or json_mode()) it degrades to a plain
    stdout write, which is still the correct stream for a report line.
    The flush matters: the JSON line is the machine consumer's entire
    signal and must not sit in a buffer while a post-report step (a hook,
    a prompt) runs or the process exits.
    """
    out = _json_real_stdout if _json_real_stdout is not None else sys.stdout
    out.write(line + "\n")
    out.flush()


def format_pack_json(
    *,
    sid: str,
    tarball: Path,
    log_path: Path,
    session_dir: Path,
    context_files: int,
) -> str:
    """Render the `bale pack --json` end-of-run report as ONE line of JSON.

    The keys are a STABLE CONTRACT for downstream tooling (request-011's
    manifest names sid, artifact paths, and outcome as the floor). Existing
    keys are never renamed or removed; new keys may be added. The set:

      outcome        "packed" — the only state that reaches pack's
                     end-of-run report today. Every failure path exits
                     through fail() (stderr + non-zero) or the interactive
                     abort (stderr + exit 1) before this renders, so a
                     consumer sees this line only on exit 0. The outcome
                     vocabulary across the json renderers is owned in this
                     module — "packed" here; "applied", "held", "reverted",
                     "bailout", "dry-run" in format_apply_json (v0.2.8);
                     "status" in format_status_json (v0.2.9) —
                     so new outcomes extend an enum in one place rather
                     than scattering literals across callers.
      sid            the session id, `YYYY-MM-DD-<slug>-NNN`.
      tarball        absolute path to the request tarball in .bale/outbox/.
      log            absolute path to the session log in .bale/logs/.
      session_dir    absolute path to .bale/sessions/<sid>/ (holds the
                     stamped request manifest.json).
      context_files  number of files packed under context/ — the same count
                     the human summary's "files" row reports.

    Emitted as a single compact line (no indent) so the consumer contract
    stays line-oriented. Since v0.2.8 json mode carries stream discipline
    (module docstring): the `[bale] ` informational lines — and every other
    human-facing line — go to stderr, and stdout carries exactly this one
    line, which the caller emits via emit_json_line so it reaches the real
    stdout that enable_json_mode saved. The v0.2.7 consumer recipe
    (`bale pack ... --json | tail -n 1 | jq -r .tarball`) keeps working:
    the last stdout line is now the only stdout line. Path values are
    stringified exactly as pack resolved them — absolute, since cmd_pack
    derives them from the resolved repo root. Pure: builds a string, prints
    nothing; the caller emits it, which supplies the trailing newline.
    """
    payload = {
        "outcome": "packed",
        "sid": sid,
        "tarball": str(tarball),
        "log": str(log_path),
        "session_dir": str(session_dir),
        "context_files": context_files,
    }
    return json.dumps(payload)


def format_apply_json(
    *,
    outcome: str,
    sid: str,
    log_path: Path,
    state: Optional[str] = None,
    exit_code: Optional[int] = None,
    claims: Optional[dict] = None,
    action: Optional[str] = None,
    merged: bool = False,
    tag: Optional[str] = None,
    origin_branch: Optional[str] = None,
    telemetry: Optional[str] = None,
    drift: Optional[dict] = None,
) -> str:
    """Render the `bale apply --json` end-of-run report as ONE line of JSON.

    The apply twin of format_pack_json (v0.2.8): same stability rules
    (existing keys are never renamed or removed; new keys may be added),
    same one-compact-line shape, same emission path (the caller emits it
    via emit_json_line so it reaches the real stdout under json mode's
    stream discipline — module docstring). Per the request-011 lineage the
    key set reuses the pack vocabulary where concepts overlap (outcome,
    sid, log) and adds the two apply-specific fields, verdict and merge:

      outcome  which terminal reporting point produced this line —
               "applied"   the PASS walkthrough ended in merge (exit 0)
               "held"      the HOLD walkthrough ended in inspect (exit 1)
               "reverted"  the walkthrough ended in revert, from either
                           verdict (exit 1)
               "bailout"   response_kind=bailout; nothing applied (exit 0)
               "clarification"
                           response_kind=clarification; nothing applied,
                           session stays open (exit 0)
               "dry-run"   the --dry-run plan report, normal, bailout,
                           or clarification shape (exit 0)
               "scope-drift-refused"
                           the own-scope drift gate refused (BALE.md §8.1
                           step 14, §11 row 22; exit 1, session open —
                           the dispatchable key an orchestrator branches
                           on instead of parsing prose). Emitted under
                           --dry-run too when the plan would refuse.
               Together with pack's "packed" these are the whole outcome
               vocabulary; extend it here, never with caller-side literals.
      sid      the session id the response was applied against.
      log      absolute path to the session log — where validation.sh's
               full output and the claim/verdict reconciliation live.
      verdict  validation.sh's result, or null when it did not run
               (bailout, clarification, dry-run). An object:
                 state      "PASS" | "HOLD"
                 exit_code  validation.sh's exit code (TARBALL.md §7.5)
                 claims     the manifest's claims map — the prediction
                            side of the TARBALL.md §5.3 claim/verdict
                            split; the verdict detail is in the log
      merge    the terminal git result, or null when no walkthrough ran
               (bailout, clarification, dry-run). An object:
                 action         "merge" | "inspect" | "revert" — the
                                walkthrough action taken
                 merged         true only when the session landed in
                                origin (merged and tagged)
                 tag            "applied/<sid>" when merged, else null
                 origin_branch  the branch a merge landed on (or, for
                                inspect/revert, would have)
      telemetry (v0.3.9, additive) repo-relative path of the telemetry
               record written for this apply-close event
               (claude/telemetry/<sid>.json, BALE.md §8.9), or null when
               none was written (dry-run, clarification, write failure).
      drift    (v0.3.10, additive) the own-scope refusal detail on the
               scope-drift-refused outcome, null on every other. An
               object:
                 out_of_scope_paths  the refused changes[] paths
                 session_scope       the session's declared scope
                 overridden_paths    paths a partial --allow-out-of-scope
                                     did admit on this invocation

    `state` None means "validation.sh did not run" and yields verdict:
    null; `action` None likewise yields merge: null. At today's call sites
    both are None together (bailout, clarification, dry-run,
    scope-drift-refused) or set
    together (the three walkthrough outcomes). Consumer contract: on the reporting paths
    stdout is exactly this line — present on exit 0 AND on the
    held/reverted/scope-drift-refused exit-1 outcomes, since a machine
    consumer needs the refusal and HOLD
    reports as much as the PASS one; error paths exit through fail()
    (stderr, non-zero) with nothing on stdout. Pure: builds a string,
    prints nothing.
    """
    verdict: Optional[dict] = None
    if state is not None:
        verdict = {
            "state": state,
            "exit_code": exit_code,
            "claims": claims or {},
        }
    merge: Optional[dict] = None
    if action is not None:
        merge = {
            "action": action,
            "merged": merged,
            "tag": tag,
            "origin_branch": origin_branch,
        }
    payload = {
        "outcome": outcome,
        "sid": sid,
        "log": str(log_path),
        "verdict": verdict,
        "merge": merge,
        # v0.3.9 (B2), additive per the stability rules above: repo-relative
        # path of the telemetry record this apply-close event wrote
        # (claude/telemetry/<sid>.json), or null when no record was written
        # (dry-run, clarification, or a write failure the log carries).
        "telemetry": telemetry,
        # v0.3.10, additive: the own-scope drift refusal detail (BALE.md
        # §8.1 step 14) — object on outcome=scope-drift-refused, null on
        # every other outcome.
        "drift": drift,
    }
    return json.dumps(payload)


def format_status_json(report) -> str:
    """Render the `bale status --json` report as ONE line of JSON.

    The status sibling of format_pack_json / format_apply_json (v0.2.9):
    same stability rules (existing keys are never renamed or removed; new
    keys may be added), same one-compact-line shape, same emission path
    (the caller emits it via emit_json_line so it reaches the real stdout
    under json mode's stream discipline — module docstring). `report` is
    bin/bale's StatusReport — the facts `bale status` gathers once and
    renders once. This function reads its attributes and performs no I/O
    of its own, preserving status's gather/render seam (all of status's
    I/O lives in _gather_status; this renderer stays the pure,
    unit-testable half ADR 0003 anticipates). It takes the report object
    rather than an unpacked kwarg per field because status reports the
    whole gathered state and the dataclass is already its one canonical
    carrier — unlike the pack/apply reports, whose handful of fields have
    no such holder at the call site.

    Keys reuse the pack/apply vocabulary where concepts overlap (outcome,
    sid) and follow format_apply_json's nullable-object pattern for facts
    that may not apply. The set:

      outcome  "status" — always. Status has no failure outcome of its
               own: a successful read exits 0 in both modes, and error
               paths exit through fail() (stderr, non-zero, nothing on
               stdout). Part of the one-place outcome vocabulary this
               module owns (see format_pack_json).
      version  the bale VERSION string.
      sid      the open session id — the lock state, in the same key
               pack and apply use — or null when no session is open.
      repo     null outside a git repository; else an object:
                 root               absolute repo root path
                 branch             current branch name
                 tree_clean         bool
                 tree_change_count  count of `git status --porcelain`
                                    lines
                 bale_initialised   whether .bale/ exists
      session  null outside a git repository; else an object, present
               even when idle — the lifecycle state is a fact either way:
                 state          "idle" | "packed" | "held" | "orphan"
                                (BALE.md §9.5; the SESSION_STATE_*
                                constants in bin/bale)
                 goal           the stamped request manifest's goal, or
                                null (no open session, or no readable
                                stamped manifest)
                 expects_probe  the stamped manifest's expects_probe
                                value, or null likewise
               The human rows' prose — the state description and the
               next-step hint — is deliberately NOT in the contract: a
               machine consumer dispatches on the state enum, and the
               prose wording must stay free to change without breaking
               anyone.
      staging  null outside a git repository; else an object. Since
               v0.3.3 the default staging layout is per-session
               (<repo>/.bale/staging/<sid>), and this object reports
               the layout: the two v0.2.9 keys survive with their
               literal values unchanged — `path` is the same
               <repo>/.bale/staging string as before, now glossed as
               the staging *root*, and `present` is the same
               directory-exists computation on it — and two additive
               keys carry the per-session state. A --staging-dir
               override on a past apply is invisible to status, so
               this reports the default layout — which is also the
               layout bale apply itself resolves absent the flag:
                 present   whether the staging root exists
                 path      the staging root, <repo>/.bale/staging
                 sessions  object mapping each open sid to
                             present  whether that session's staging
                                      directory exists (its HOLD under
                                      inspection, or an apply
                                      mid-flight)
                             path     <repo>/.bale/staging/<sid>
                             strategy          (additive, v0.3.11 —
                                      board 12) the staging strategy in
                                      effect for the session:
                                      "working-tree" | "target-base",
                                      the effective [staging].strategy
                                      the merged config resolves to
                                      (BALE.md §8.3 step 2 — the
                                      strategy is config-derived at use
                                      time, not stamped per session, so
                                      today every open sid carries the
                                      same effective value; the key is
                                      per-session because that is the
                                      fact's shape to a consumer). Null
                                      when the effective config could
                                      not be summarised (malformed
                                      bale.toml — config.summary_failed
                                      true): unknown rather than
                                      known-default.
                             untracked_inputs  (additive, v0.3.11 —
                                      board 12) the declared
                                      [staging].untracked_inputs in
                                      effect for the session, as an
                                      always-present list — empty when
                                      none (the uniform-shape
                                      convention the v0.3.10 telemetry
                                      keys set), and empty under
                                      working-tree, where the stage
                                      step ignores the declaration
                                      (untracked state rides in with
                                      the copy), so the list reports
                                      what validation will actually
                                      overlay, not raw config.
                           Keys match the `sessions` list; empty when
                           nothing is open. Consumers keep dispatching
                           on stale/sessions, never on key presence.
                 stale     sorted top-level entries under the root no
                           open session owns — closed sessions'
                           preserved-for-inspection leftovers and bare
                           pre-v0.3.3 trees; exactly what the next
                           default-path apply will remove (the
                           "inspectable staging left in place" fact
                           the v0.2.9 `present` key used to carry).
      outbox   null outside a git repository; else the full sorted list
               of request tarball names in .bale/outbox/. Unlike the
               human block it is not capped: STATUS_OUTBOX_LIST_CAP is
               presentation, not data, and a machine consumer gets
               everything.
      applied  null outside a git repository; else an object:
                 count   number of applied/<sid> tags
                 latest  most recent applied sid (by tag creation date,
                         matching `bale rollback --list`'s ordering), or
                         null when none
      sessions  (additive, v0.3.0 — ADR-0006) null outside a git
               repository; else the full list of open sids from the
               session registry, oldest-first. `sid` above remains the
               single-open pointer for existing consumers; with at most
               one session open (guaranteed until ADR-0007) this list is
               [] or [sid]. A machine consumer of the multi-session
               world reads this key.
      scopes   (additive, v0.3.2 — ADR-0007) null outside a git
               repository; else an object mapping each open sid to its
               recorded scope entries (normalized repo-relative paths,
               ["."] for whole-tree — including sessions with no
               readable scope.json, which degrade conservatively
               exactly as the disjointness gates read them). An empty
               list is a real value, not an absence (additive,
               v0.3.15): it marks a read-only session (`bale pack
               --read-only` or the wizard's read-only answer) — a
               scope that locks nothing and lands nothing, exactly as
               the gates read it. Keys match
               the `sessions` list; both are empty when nothing is
               open.
      integration_lock  (additive, v0.3.0 — ADR-0006) null when the
               repo-level integration lock is not held (the normal
               state; it is held only across apply's §8.6–§8.8 git
               window) or outside a git repository; else an object with
               sid / pid / acquired_at (each null when the lock file
               would not parse) and path (always present). A non-null
               value during no running apply is a stale lock from an
               interrupted integration.
      config   always an object (the global layer exists outside repos):
                 project         absolute path of <repo>/bale.toml, or
                                 null when absent or outside a repo
                 global          absolute path of the install-layer
                                 bale.toml, or null when absent
                 hooks_wired     hook names with a script wired in the
                                 effective (merged) config
                 search_paths    count of configured apply search paths
                 baleignore      whether <repo>/.baleignore exists
                                 (false outside a repo)
                 summary_failed  true when the effective-config summary
                                 could not be computed (malformed
                                 bale.toml). The presence facts above
                                 are still valid; hooks_wired /
                                 search_paths are then empty/zero —
                                 unknown rather than known-absent.

    Pure: builds a string, prints nothing; the caller emits it, which
    supplies the trailing newline.
    """
    repo_obj = None
    session_obj = None
    staging_obj = None
    outbox = None
    applied_obj = None
    sessions = None
    scopes = None
    integration_lock_obj = None
    if report.repo_root is not None:
        repo_obj = {
            "root": str(report.repo_root),
            "branch": report.branch,
            "tree_clean": report.tree_clean,
            "tree_change_count": report.tree_change_count,
            "bale_initialised": report.bale_initialised,
        }
        session_obj = {
            "state": report.session_state,
            "goal": report.session_goal,
            "expects_probe": report.session_expects_probe,
        }
        staging_obj = {
            "present": report.staging_present,
            "path": (str(report.staging_path)
                     if report.staging_path is not None else None),
            # Additive (v0.3.3, per-session staging): per open sid, plus
            # the root entries no open session owns. The v0.2.9 keys
            # above keep their literal values (path is now the root —
            # the same <repo>/.bale/staging string as before).
            "sessions": {
                str(sid): {
                    "present": bool(info.get("present")),
                    "path": (str(info.get("path"))
                             if info.get("path") is not None else None),
                    # Additive (v0.3.11, board 12 — display only): the
                    # effective staging posture, per session. One
                    # config-derived value fanned out per sid (see the
                    # docstring's strategy/untracked_inputs entries);
                    # strategy is null when the config summary failed,
                    # and untracked_inputs is the always-present list —
                    # empty when none, and empty under working-tree.
                    "strategy": report.staging_strategy,
                    "untracked_inputs": list(report.staging_untracked_inputs),
                }
                for sid, info in report.staging_sessions.items()
            },
            "stale": list(report.staging_stale),
        }
        outbox = list(report.outbox_tarballs)
        applied_obj = {
            "count": report.applied_count,
            "latest": report.applied_latest,
        }
        sessions = list(report.open_sids)
        scopes = {
            str(sid): list(entries)
            for sid, entries in report.session_scopes.items()
        }
        if report.integration_lock is not None:
            integration_lock_obj = {
                "sid": report.integration_lock.get("sid"),
                "pid": report.integration_lock.get("pid"),
                "acquired_at": report.integration_lock.get("acquired_at"),
                "path": report.integration_lock.get("path"),
            }
    payload = {
        "outcome": "status",
        "version": report.version,
        "sid": report.session_sid,
        "repo": repo_obj,
        "session": session_obj,
        "staging": staging_obj,
        "outbox": outbox,
        "applied": applied_obj,
        "sessions": sessions,
        "scopes": scopes,
        "integration_lock": integration_lock_obj,
        "config": {
            "project": (str(report.project_config)
                        if report.project_config is not None else None),
            "global": (str(report.global_config)
                       if report.global_config is not None else None),
            "hooks_wired": list(report.hooks_wired),
            "search_paths": report.search_path_count,
            "baleignore": report.baleignore,
            "summary_failed": report.config_summary_failed,
        },
    }
    return json.dumps(payload)


# --- status: session-registry human-value formatters (v0.3.0, ADR-0006) ---

def format_scope_value(scope: list) -> str:
    """Render one session's recorded scope (ADR-0007) as a row value.

    Scope entries are the session's resolved include set as
    read_session_scope returns them — normalized repo-relative paths,
    ["."] for a whole-tree session (a default pack, a handoff whose
    reading plan cited no files, or a session with no recorded scope at
    all), or [] for a read-only session (v0.3.15: `bale pack
    --read-only` or the wizard's read-only answer). The whole-tree case
    is spelled out rather than left as a bare dot, since "." reads as
    noise to anyone not versed in the gate's normal form; the empty
    case is spelled out rather than printed as an empty string — a
    read-only session's scope should say what it is, not vanish;
    everything else is the entries verbatim, comma-joined. Used for the
    single classified session's `scope` row and per-sid in
    format_open_sessions_value's listing.
    """
    entries = [str(s) for s in scope]
    if not entries:
        return "(read-only — locks nothing, lands nothing)"
    if entries == ["."]:
        return ". (whole tree)"
    return ", ".join(entries)


def format_staging_value(strategy: str, untracked_inputs: list = ()) -> str:
    """Render one session's effective staging posture as a row value
    (v0.3.11, board 12 — display only).

    `strategy` is the effective [staging].strategy the merged config
    resolves to — "working-tree" or "target-base" (BALE.md §8.3 step 2).
    The strategy is config-derived at use time, not stamped per session,
    so every open session renders the same effective value today; the
    caller passes it per session anyway because per-session is the shape
    the fact has to the operator (which content THIS session's apply
    will validate against). `untracked_inputs` is the effective declared
    list — non-empty only under target-base, where the declaration is
    load-bearing; under working-tree the caller passes () because the
    stage step ignores the declaration there (untracked state rides in
    with the copy). Common case — no inputs — is the bare strategy
    string, keeping the row and the per-sid listing line to one line.
    Used for the single classified session's `staging` row and per-sid
    in format_open_sessions_value's listing.
    """
    inputs = [str(p) for p in untracked_inputs] if untracked_inputs else []
    if not inputs:
        return str(strategy)
    noun = "input" if len(inputs) == 1 else "inputs"
    return f"{strategy}; untracked {noun}: {', '.join(inputs)}"


def format_open_sessions_value(open_sids: list, scopes: dict = None,
                               staging_strategy: str = None,
                               staging_untracked_inputs: list = ()) -> str:
    """Render the human `open sessions` row value for `bale status`.

    Lives here rather than in bin/bale's _render_status because status
    rendering — the key contract on the json side, the row values on the
    human side — is this module's surface. One sid per line, oldest-first
    as gathered from the registry, with a count headline; the multi-line
    value wraps under its label via format_summary_block, the same shape
    the outbox listing uses. When `scopes` (sid → recorded scope entries,
    ADR-0007 — v0.3.2) is given, each line carries the session's scope
    via format_scope_value, the fact that decides what a next concurrent
    pack may include; a sid absent from the mapping renders without one
    rather than guess. When `staging_strategy` (the effective
    [staging].strategy, v0.3.11 — board 12) is given, each line also
    carries the session's staging posture via format_staging_value —
    one effective value fanned out per sid, since the strategy is
    config-derived at use time rather than stamped per session; None
    (the merged config could not be summarised) renders without one,
    the same degradation as an absent scope. The common case stays one
    line per session. The caller only emits this row for 2+ open
    sessions (with 0 or 1 the existing single-session rows already carry
    the fact), so no singular/empty phrasing is needed — but render those
    shapes sensibly anyway rather than assume the caller.
    """
    n = len(open_sids)
    if n == 0:
        return "none"
    noun = "session" if n == 1 else "sessions"
    lines = []
    for s in open_sids:
        parts = [str(s)]
        if scopes is not None and s in scopes:
            parts.append(f"scope: {format_scope_value(scopes[s])}")
        if staging_strategy is not None:
            parts.append(
                f"staging: "
                f"{format_staging_value(staging_strategy, staging_untracked_inputs)}"
            )
        lines.append(" — ".join(parts))
    return f"{n} open {noun}:\n" + "\n".join(lines)


def format_integration_holder(info: dict) -> str:
    """Render the integration lock's holder record as one phrase.

    `info` is the read_integration_lock_info dict: "path" always, plus
    whichever of sid/pid/acquired_at the lock file yielded. Shared by
    the acquire-time refusal in bin/bale, the status row below, and
    `bale unlock --integration`'s summary, so all three name a holder
    identically.
    """
    held_by = []
    if info.get("sid"):
        held_by.append(f"session {info['sid']}")
    if info.get("pid") is not None:
        held_by.append(f"pid {info['pid']}")
    if info.get("acquired_at"):
        held_by.append(f"since {info['acquired_at']}")
    return (", ".join(held_by) if held_by
            else "holder unknown (unparseable lock file)")


def format_integration_lock_value(info: dict) -> str:
    """Render the human `integration lock` row value for `bale status`.

    `info` is StatusReport.integration_lock: always carries "path", plus
    sid/pid/acquired_at when the lock file parsed. The lock is held only
    across apply's §8.6–§8.8 git window, so a sighting outside a running
    apply is stale — the rendered value says how to clear it, matching
    the acquire-time failure message in bin/bale. Holder phrasing is
    format_integration_holder, the shared form.
    """
    holder = format_integration_holder(info)
    path = info.get("path", ".bale/integration.lock")
    return (f"HELD — {holder}. If no `bale apply` is running, the lock is "
            f"stale; clear it with `bale unlock --integration` "
            f"(or `rm {path}`).")


# --- telemetry record (v0.3.9, session B2) ---
#
# The durable per-session record written at apply close — one file per sid
# at claude/telemetry/<sid>.json, shape per schemas/telemetry-record.
# schema.json, update semantics per BALE.md §8.9. This cluster assembles
# and persists the record; the callers in bin/bale are wiring-thin: each
# terminal apply outcome builds an attempt (build_telemetry_attempt) and
# hands it to write_telemetry_record, then renders the returned path in its
# own summary row and json key. Everything here is stdlib-pure and takes
# data, not repo-inspection responsibilities: the one exception is the
# lazy __main__ `log` import inside write_telemetry_record, the siblings'
# established mechanism, used only to report a write failure — which never
# propagates to the caller, because telemetry must not be able to break an
# apply that already succeeded.

RECORD_VERSION = 1

# The §7.3 reconciliation line as validation.sh conventionally prints it:
#   <check name>: claim=<word> verdict=<word> [tag]
# The check name may contain spaces and colons; anchor on the last
# "claim=... verdict=... [...]" triple instead of splitting on ":".
_CLAIM_VERDICT_LINE = re.compile(
    r"^\s+(?P<check>.+?):\s+claim=(?P<claim>\S+)\s+verdict=(?P<verdict>\S+)"
    r"\s+\[(?P<tag>[^\]]+)\]\s*$"
)


def telemetry_record_path(repo: Path, sid: str) -> Path:
    """Absolute path of the sid's telemetry record: claude/telemetry/<sid>.json."""
    return repo / "claude" / "telemetry" / f"{sid}.json"


def parse_claim_verdict_block(output: str) -> tuple[dict, bool]:
    """Extract the TARBALL.md §7.3 claims-vs-verdict block from validation output.

    Returns (claim_verdict, parsed): `claim_verdict` maps each check name to
    {"claim", "verdict", "agreement"} — agreement is the bracketed tag
    normalized to lowercase ("agree" / "disagree" / "n/a") — and `parsed`
    is True when a "claims vs verdict:" header was found and at least one
    line under it matched the conventional shape. The block is a
    validation.sh authoring convention (TARBALL.md §7.3), not a bale-
    enforced contract, so a miss is a recorded fact (parsed=False, empty
    map), never an exception: the record's `reconciliation_parsed` field is
    how aggregation distinguishes "no disagreements" from "block absent".

    The LAST occurrence of the header wins — a validation.sh that prints
    the block more than once (a re-run inside the script, say) is summarized
    by its final reconciliation, matching how a human reads the log.
    """
    lines = output.splitlines()
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().lower().startswith("claims vs verdict:"):
            header_idx = i
    if header_idx is None:
        return {}, False
    claim_verdict: dict = {}
    for line in lines[header_idx + 1:]:
        if not line.strip():
            break  # blank line ends the block
        m = _CLAIM_VERDICT_LINE.match(line)
        if m is None:
            # First non-matching, non-blank line ends the block: the §7.3
            # shape is contiguous indented rows under the header.
            break
        claim_verdict[m.group("check").strip()] = {
            "claim": m.group("claim"),
            "verdict": m.group("verdict"),
            "agreement": m.group("tag").strip().lower(),
        }
    return claim_verdict, bool(claim_verdict)


def build_telemetry_attempt(
    *,
    outcome: str,
    command: str,
    tarball: Optional[str] = None,
    manifest: Optional[dict] = None,
    scope: Optional[list] = None,
    validation_state: Optional[str] = None,
    validation_exit_code: Optional[int] = None,
    validation_output: Optional[str] = None,
    log_path: Optional[str] = None,
    overridden_paths: Optional[list] = None,
) -> dict:
    """Assemble one attempts[] entry (telemetry-record.schema.json) from
    facts the apply-close call site already holds.

    `manifest` (the response manifest, when available) supplies the two
    promoted verbatim pieces: the feedback block and the changes[] paths.
    `scope` is the session's recorded include set (the caller reads it via
    read_session_scope). `validation_*` are present only when validation.sh
    ran this attempt; the §7.3 reconciliation is parsed here from
    `validation_output` so no caller re-implements the promotion. A rejected
    or reverted attempt passes validation_state=None and gets
    validation: null.

    `overridden_paths` (v0.3.10, board 2) stamps the out-of-scope paths a
    per-invocation `--allow-out-of-scope` admitted into the attempt's
    mechanical (bale-computed) fields — always present as a list, empty
    when no override was in play, so aggregation reads a uniform shape.
    On a `scope-drift-refused` attempt it carries any paths a PARTIAL
    override admitted while other drift still refused; the refused paths
    themselves are recoverable from scope vs change_paths, both already
    recorded raw.
    """
    validation: Optional[dict] = None
    if validation_state is not None:
        claim_verdict, parsed = parse_claim_verdict_block(
            validation_output or "")
        validation = {
            "state": validation_state,
            "exit_code": validation_exit_code,
            "claims": (manifest or {}).get("claims", {}) or {},
            "claim_verdict": claim_verdict,
            "reconciliation_parsed": parsed,
        }
    return {
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "outcome": outcome,
        "command": command,
        "tarball": tarball,
        "validation": validation,
        "scope": list(scope or []),
        "overridden_paths": list(overridden_paths or []),
        "change_paths": [c.get("path") for c in
                         (manifest or {}).get("changes", []) or []],
        "feedback": (manifest or {}).get("feedback"),
        "log": log_path,
    }


def write_telemetry_record(repo: Path, sid: str, attempt: dict) -> Optional[str]:
    """Append one apply-close attempt to claude/telemetry/<sid>.json.

    Update semantics (BALE.md §8.9): one file per sid, created on the first
    apply-close event and APPENDED to on every later one — HOLD then retry
    updates the same record rather than duplicating it, and the envelope's
    `outcome`/`updated_at` mirror the latest attempt. An existing file that
    fails to parse or has lost its attempts[] array is moved aside to
    `<sid>.json.corrupt-<utc-stamp>` (logged, never silently discarded) and
    a fresh record starts — a corrupt record must not block the apply that
    discovered it, and must not be overwritten unexamined.

    Returns the record's repo-relative path on success, None on failure.
    Never raises: a telemetry write failure is logged via the lazy
    __main__ `log` (force=True, so it reaches the terminal) and swallowed —
    the record is longitudinal signal, and losing one entry is strictly
    better than failing an apply whose git work already landed.
    """
    from __main__ import log
    path = telemetry_record_path(repo, sid)
    rel = str(path.relative_to(repo))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        record: Optional[dict] = None
        if path.is_file():
            try:
                loaded = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict) and isinstance(
                        loaded.get("attempts"), list):
                    record = loaded
            except (OSError, json.JSONDecodeError):
                record = None
            if record is None:
                stamp = now.replace(":", "").replace("+00:00", "Z")
                aside = path.with_name(f"{path.name}.corrupt-{stamp}")
                path.rename(aside)
                log(f"telemetry: existing record at {rel} was unreadable; "
                    f"moved aside to {aside.name} and starting fresh",
                    force=True)
        if record is None:
            record = {
                "record_version": RECORD_VERSION,
                "session_id": sid,
                "created_at": now,
                "attempts": [],
            }
        record["attempts"].append(attempt)
        record["updated_at"] = now
        record["outcome"] = attempt["outcome"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
        return rel
    except OSError as e:
        log(f"telemetry: could not write {rel}: {e} — the apply outcome "
            f"stands; the record entry for this event is lost", force=True)
        return None
