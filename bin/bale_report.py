"""bale_report — end-of-command result assembly and rendering.

This module owns the result-reporting surface of the pack and apply
pipelines: the shared end-of-run summary formatter every command finishes on
(`format_summary_block`, with its private word-wrap helper
`_wrap_value_lines`), the BALE.md §8.7 apply walkthrough summary builder for
the PASS/HOLD verdicts (`format_walkthrough_summary`), the TARBALL.md §5.6.3
bailout banner (`print_bailout_banner`), the `bale apply --dry-run` plan
report (`format_dry_run_report`), the machine-readable pack report
(`format_pack_json`, added in v0.2.7 for `bale pack --json`) and its apply
twin (`format_apply_json`, added in v0.2.8 for `bale apply --json`), plus the
json-mode stream-discipline state the two machine reports share
(`enable_json_mode` / `json_mode` / `emit_json_line`, v0.2.8). The human-facing
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
status report — pack, apply (its PASS / HOLD / REVERT / BAILOUT banners and
the walkthrough summary), revert, unlock, handoff, status — ends on the same
shape: a leading blank line, an optional `[STATUS] <sid>` headline, a block
of two-space-indented, colon-aligned label/value rows, and optional verbatim
trailer lines (the actionable next step). Callers that also emit bulky
reference material (the walkthrough's notes.md body — plus legacy
next-prompt.md, tolerated per TARBALL.md §5.5 — and diffstat, the bailout's
handoff excerpt) print that material FIRST and the summary block LAST, so a
long reference body never pushes the scannable verdict off the top of the
screen. The builders here are pure string assemblers — they print nothing;
the caller prints what they return. `print_bailout_banner` is the one
deliberate exception (it prints), because its output interleaves reference
material and the summary block in a fixed §5.6.3 order that no caller
should have to re-derive.

The two json renderers (`format_pack_json`, `format_apply_json`) sit outside
that rule because for a machine consumer the verdict is the whole report:
each renders its command's outcome as ONE line of JSON whose keys are a
stable contract for downstream tooling (see their docstrings). Since v0.2.8
json mode also carries STREAM DISCIPLINE, owned here as three tiny state
functions: `enable_json_mode()` (called once by cmd_pack/cmd_apply when
--json is passed) saves the real stdout and rebinds `sys.stdout` to
`sys.stderr`, so every `[bale] ` log line, prompt, hook banner, and human
reference block the command produces lands on stderr without any print site
changing; `emit_json_line()` writes the one report line to the saved real
stdout; `json_mode()` is the accessor pass-through call sites gate on. The
consumer contract is therefore: on the reporting paths, stdout carries
exactly one JSON line (pack: exit 0; apply: exit 0, plus the held/reverted
exit-1 outcomes), and error paths exit through fail() — stderr, non-zero —
with nothing on stdout. Human (non---json) mode is untouched: the swap never
happens and every stream keeps its pre-v0.2.8 behavior byte-for-byte.

Behavior-preserving move: the functions keep the signatures, bodies, and
call sites they had in `bin/bale`. The public entry points
(`format_summary_block`, `format_walkthrough_summary`,
`print_bailout_banner`, `format_dry_run_report`, since v0.2.7
`format_pack_json`, and since v0.2.8 `format_apply_json` plus the json-mode
trio `enable_json_mode` / `json_mode` / `emit_json_line`) are pulled back into
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

See claude/context/bale-internals.md for how this module sits next to
`bin/bale` and the other siblings.
"""

from __future__ import annotations

import json
import subprocess
import sys
import textwrap
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

    # Diffstat between origin and the bale branch. On the HOLD path the bale
    # branch's HEAD is identical to origin's HEAD (no commit was made), so
    # the rev-range diff is empty; in that case run a diff against the index
    # so the user still sees what's staged. PASS path always has a commit.
    if state == "PASS":
        diff_args = ["diff", "--stat", f"{origin_branch}..{sid_branch}"]
        diff_label = f"origin..{sid_branch}"
    else:
        diff_args = ["diff", "--stat", "--cached"]
        diff_label = "staged (uncommitted)"
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
        else f"{sid_branch} (uncommitted; staged changes held)"
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


def format_dry_run_report(manifest: dict, sid: str, *, is_bailout: bool) -> str:
    """Build the `--dry-run` plan summary as a single string.

    Reports what a real `bale apply` would do with this tarball, having
    already passed every read-only pre-flight check (extract, syntax,
    manifest schema, responds_to, presence/sha256/path-safety). Pure — the
    caller prints the returned string and returns 0.
    """
    lines: list[str] = [""]
    lines.append(f"  [DRY RUN] {sid}")
    lines.append(f"  summary: {manifest.get('summary', '(no summary)')}")

    if is_bailout:
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
                     vocabulary across both json renderers is owned in this
                     module — "packed" here; "applied", "held", "reverted",
                     "bailout", "dry-run" in format_apply_json (v0.2.8) —
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
               "dry-run"   the --dry-run plan report, normal or bailout
                           shape (exit 0)
               Together with pack's "packed" these are the whole outcome
               vocabulary; extend it here, never with caller-side literals.
      sid      the session id the response was applied against.
      log      absolute path to the session log — where validation.sh's
               full output and the claim/verdict reconciliation live.
      verdict  validation.sh's result, or null when it did not run
               (bailout, dry-run). An object:
                 state      "PASS" | "HOLD"
                 exit_code  validation.sh's exit code (TARBALL.md §7.5)
                 claims     the manifest's claims map — the prediction
                            side of the TARBALL.md §5.3 claim/verdict
                            split; the verdict detail is in the log
      merge    the terminal git result, or null when no walkthrough ran
               (bailout, dry-run). An object:
                 action         "merge" | "inspect" | "revert" — the
                                walkthrough action taken
                 merged         true only when the session landed in
                                origin (merged and tagged)
                 tag            "applied/<sid>" when merged, else null
                 origin_branch  the branch a merge landed on (or, for
                                inspect/revert, would have)

    `state` None means "validation.sh did not run" and yields verdict:
    null; `action` None likewise yields merge: null. At today's call sites
    both are None together (bailout, dry-run) or set together (the three
    walkthrough outcomes). Consumer contract: on the reporting paths
    stdout is exactly this line — present on exit 0 AND on the
    held/reverted exit-1 outcomes, since a machine consumer needs the HOLD
    report as much as the PASS one; error paths exit through fail()
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
    }
    return json.dumps(payload)
