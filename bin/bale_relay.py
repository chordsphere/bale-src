"""bale_relay — the `bale relay` verb (the exchange thread's recording verb).

Extracted from `bin/bale`'s section 29 in v0.4.21, behavior-preserving
(ADR-0017; contract BALE.md §8.11, contract row §11.34; the verb itself
landed in v0.4.18): one exchange in, one record preserved, one paste
block out. The verb executes nothing and stages nothing — it reads a
file or stdin, gates the record (trailer, schema, sequencing, answer
resolvability), writes the thread's next NNN.json through the same
preservation apply's clarification handler uses, keeps the session
suspended, and emits the counterpart-facing paste block on stdout under
the machine-report stream discipline (every `[bale] ` line and the human
trailer on stderr), so `bale relay <sid> <file> > block.txt` captures
the block clean. Direction is read from the record's `from`, never from
a flag; the positional surface is exactly `<sid> [<file|->]` — since
v0.4.22 (board row 60, ADR-0017 Notes) the file argument is optional,
and the no-file form re-emits the paste block for the thread's latest
recorded round, byte-identical to the original emission, recording
nothing: a planner-side block otherwise exists only on the stdout that
made it. Since v0.4.48 the surface also takes `--json`: one line of JSON on
stdout on every path (`relayed`, `re-emitted`, `relay-refused`), the block
riding inside it; bale_report.format_relay_json owns the keys, and without
the flag every byte is what it was.

Public surface consumed by `bin/bale`: the single `cmd_relay(args)`
entry point — `bin/bale` does `from bale_relay import cmd_relay` and
wires it to the CLI. The paste-block sentinels and sides
(`EXCHANGE_BLOCK_BEGIN` / `EXCHANGE_BLOCK_END`,
`EXCHANGE_TRAILER_LABEL`, `EXCHANGE_SIDE_WORKER` /
`EXCHANGE_SIDE_PLANNER`) and the pure render/ingest pair
(`format_exchange_block`, `parse_exchange_input`) are module-level so
the block's one wire shape has one home.

Shared `bin/bale` helpers (`log`, `fail`, `set_log_file`,
`refuse_system_dir`, `repo_root`, `session_is_open`, `open_sessions`,
`_branch_exists`, `locate_inbound_path`, `exit_cause`) are imported lazily from
`__main__` (i.e. `bin/bale`) inside the functions that use them, the
same idiom every other sibling uses. Sibling-owned entry points are
imported lazily from their owning modules instead — `bin/bale` has
already loaded them, so the imports resolve from sys.modules:
`bale_config` (the apply search paths), `bale_validate`'s
exchange-record and question-row validators, `bale_report`'s
stream-discipline state and renderers (`enable_json_mode`,
`emit_stdout_block`, `format_summary_block`, `awaiting_side`,
`exchange_record_view`), `bale_pack.normalize_crlf` (the board-50
ingest-edge rule, one implementation for every inbound surface), and
`bale_apply`'s clarification-thread writers (`clarifications_dir`,
`next_clarification_seq`, `preserve_clarification_record` — the same
write apply's tarball ingest uses, so the thread is byte-identical
whichever path a round arrives by). Dependency direction is one-way:
`bin/bale` imports `bale_relay`; this module reaches into `bale_pack`
and `bale_apply` lazily, and neither imports it back.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Optional


def _fail(msg: str, *, reason: str) -> None:
    """Refuse through bin/bale's fail() when hosted by it — the runtime
    path, where __main__ is bin/bale — and otherwise mirror its visible
    shape (the `[bale] error:` line on stderr, exit 1). The otherwise
    matters: the crafter parity suite loads bin/bale as an ordinary
    module and drives the ingest surface in-process, so a bare
    `from __main__ import fail` here would break even happy-path calls
    under any host that isn't bale. Session-journal logging is the
    hosted path's extra; standalone refusals have no session to journal.

    `reason` (v0.4.50) is the refusal's RELAY_REFUSAL_REASONS code
    (bin/bale_report.py), passed through to fail()'s keyword; the
    standalone path attaches it the same way, as `bale_reason` on the
    exit, so both hosts' exits carry it.
    """
    import __main__
    host_fail = getattr(__main__, "fail", None)
    if host_fail is not None:
        host_fail(msg, reason=reason)
    print(f"[bale] error: {msg}", file=sys.stderr)
    exit_exc = SystemExit(1)
    exit_exc.bale_reason = reason
    raise exit_exc


# The paste block's sentinels (TARBALL.md §5.9.2, BALE.md §8.11): the
# BEGIN line carries the sid so a block pasted against the wrong session
# refuses on the sentinel before the body is even parsed. Their one home
# is bin/bale_report.py since v0.4.50 (beside the shape-prefix tuple that
# derives from the same prefix); this module reads them from there at
# import — a plain sibling import, the way bin/bale imports its siblings,
# since the names are used at module scope by every renderer below — and
# keeps them module-level so the wire surface still reads from here.
from bale_report import (  # noqa: E402 — after _fail by design
    EXCHANGE_BLOCK_BEGIN,
    EXCHANGE_BLOCK_END,
)
# The integrity trailer: the last line inside the sentinels, carrying the
# sha256 of the body bytes (the JSON text between header and trailer,
# LF line endings, one trailing newline). `# sha256 <hex>`; a colon after
# the label is tolerated on ingest.
EXCHANGE_TRAILER_LABEL = "# sha256"
_EXCHANGE_TRAILER_RE = re.compile(r"^#\s*sha256:?\s+([0-9a-fA-F]{64})\s*$")

EXCHANGE_SIDE_WORKER = "worker"
EXCHANGE_SIDE_PLANNER = "planner"


def _exchange_body_bytes(record: dict) -> bytes:
    """The paste block's body for `record`: its JSON, two-space indented,
    ASCII-escaped (the most transport-proof spelling — a chat or mail hop
    cannot mangle a non-ASCII character the body never carries), one
    trailing newline. The trailer's sha256 is computed over exactly these
    bytes, and ingest recomputes over exactly the bytes it read between
    header and trailer, so any truncation or edit in transit refuses.
    """
    return (json.dumps(record, indent=2) + "\n").encode("utf-8")


def format_exchange_block(sid: str, record: dict) -> str:
    """Render the counterpart-facing paste block for an exchange record
    (BALE.md §8.11 'The paste block'; the probe's four properties,
    TARBALL.md §4.2, applied to a record):

      BALE EXCHANGE BEGIN <sid>          sentinel (self-delimiting)
      # ... purpose header ...           direction and round, who reads it
      { ...record JSON... }              the body
      # sha256 <hex>                     integrity trailer over the body
      BALE EXCHANGE END                  sentinel

    `record` is the exchange record as ingested (for a paste-block-borne
    clarification manifest, its normalized `from: worker` reading — see
    _normalize_manifest_to_record); the preserved copy's `preserved_at`
    sidecar is never part of the body, so the block is the record and
    only the record. Pure: the tests render and re-parse it in memory.
    """
    side = record.get("from")
    rnd = record.get("round")
    to_side = (EXCHANGE_SIDE_PLANNER if side == EXCHANGE_SIDE_WORKER
               else EXCHANGE_SIDE_WORKER)
    n_q = len(record.get("questions") or [])
    n_a = len(record.get("answers") or [])
    body = _exchange_body_bytes(record)
    digest = hashlib.sha256(body).hexdigest()
    header = [
        f"{EXCHANGE_BLOCK_BEGIN} {sid}",
        f"# bale exchange record — session {sid} — round {rnd} — "
        f"from {side} to {to_side}",
    ]
    if side == EXCHANGE_SIDE_WORKER:
        header.append(
            f"# {n_q} blocking question(s)"
            + (f" and {n_a} answer(s)" if n_a else "")
            + ". Planner: answer as an exchange record (from: planner,"
            f" round {rnd + 1 if isinstance(rnd, int) else '<next>'},"
            f" answers[] keyed question_round {rnd}) and record it with"
            f" `bale relay {sid} <answer.json|->`.")
    else:
        header.append(
            f"# {n_a} answer(s)"
            + (f" and {n_q} question(s) asked back" if n_q else "")
            + f". Worker: read the record, continue under {sid}, and"
            " ship the normal response the clarification deferred"
            + (" — or answer the questions asked back as the next"
               " round." if n_q else "."))
    header.append(
        "# Body: the record (exchange-record.schema.json). Trailer: sha256 "
        "of the body bytes — a mismatch on ingest means a truncated paste; "
        "re-request the block rather than reason from it.")
    return ("\n".join(header) + "\n"
            + body.decode("utf-8")
            + f"{EXCHANGE_TRAILER_LABEL} {digest}\n"
            + f"{EXCHANGE_BLOCK_END}\n")


def reescaped_body_matches(body: str, expected_hex: str) -> bool:
    """True when `body`, parsed as JSON and re-serialized the way bale
    renders a paste block's body (_exchange_body_bytes: two-space
    indent, ASCII escaping, one trailing newline), hashes to the
    trailer's `expected_hex` (v0.4.41, the findings' section 8 item 2).

    That is the signature of one specific transit fault: a carrier (a
    chat renderer, a mail client) turned the body's `\\uXXXX` escapes
    into the characters they stand for — the record is intact, its
    bytes are not. Called only after the plain hash has disagreed, so
    the refusal can name that fault instead of "truncated or edited".
    Pure; a body that does not parse is simply not this fault (False).
    """
    try:
        parsed = json.loads(body)
    except (json.JSONDecodeError, ValueError):
        return False
    rendered = _exchange_body_bytes(parsed)
    return hashlib.sha256(rendered).hexdigest() == expected_hex.lower()


def record_relay_refusal(repo: Path, sid: str,
                         exc: BaseException) -> Optional[str]:
    """Write a `relay-refused` attempt onto `sid`'s telemetry record
    (v0.4.41; telemetry-record.schema.json outcome 'relay-refused',
    command 'relay') carrying `cause` — the refusal's first line, read
    off the SystemExit fail() raised (exit_cause in bin/bale, the same
    capture record_rejected_attempt uses).

    Called from cmd_relay's wrapper around the input's ingest and gates
    (steps 2–5), which re-raises; this must never mask the exit, and
    write_telemetry_record already never raises. A clean exit (code 0
    or None) records nothing. The session gates (not open, held
    branch) run outside the wrapper and record nothing: a sid that is
    not open should grow no record, and a held session's envelope must
    stay 'held'. A relay that records its round writes no attempt.

    Returns the record's repo-relative path when an attempt was written
    (v0.4.48: the `telemetry` key of `bale relay --json`'s refused line),
    else None — a clean exit, or a write failure write_telemetry_record
    already logged.
    """
    from __main__ import exit_cause, log, read_session_scope  # lazy
    from bale_report import (  # lazy — sibling, loaded by bin/bale
        build_telemetry_attempt,
        write_telemetry_record,
    )
    if getattr(exc, "code", None) in (None, 0):
        return None
    cause = exit_cause(exc)
    rel = write_telemetry_record(
        repo, sid, build_telemetry_attempt(
            outcome="relay-refused", command="relay",
            scope=read_session_scope(repo, sid),
            log_path=f".bale/logs/{sid}.log",
            cause=cause,
        ))
    if rel:
        log(f"relay: refusal recorded as a relay-refused attempt at {rel}")
    return rel or None


def parse_exchange_input(data: bytes) -> tuple[dict, Optional[str]]:
    """Parse relay's input — a paste block, or bare JSON — into
    (record_dict, block_sid).

    The input is CRLF-normalized first (the board-50 ingest-edge rule,
    bale_pack.normalize_crlf: a block that traveled mail, chat, or a
    Windows checkout still verifies). Then:

    - If a `BALE EXCHANGE BEGIN <sid>` sentinel line is present, the
      block path: the matching END sentinel must follow; the leading
      `#` lines are the header; the last inner line must be the sha256
      trailer; the body is everything between, and its sha256 must
      equal the trailer's — a mismatch is the truncated-or-edited paste
      the trailer exists to catch, refused with the re-request hint
      before the body is trusted (BALE.md §8.11 step 1). Returns the
      parsed body and the sentinel's sid, which the caller compares to
      the invoked sid.
    - Otherwise the bare-JSON path: the whole input is the record (an
      exchange record, or a saved clarification manifest); block_sid is
      None.

    Refusals go through _fail() naming the rule. Text outside the
    sentinels (a chat's fence lines, a greeting) is ignored by
    construction — only the sentinel-bracketed span is read.
    """
    from bale_pack import normalize_crlf  # lazy — sibling, loaded by bin/bale
    text = normalize_crlf(data).decode("utf-8", errors="replace")
    lines = text.split("\n")
    begin_idx = None
    block_sid = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith(EXCHANGE_BLOCK_BEGIN):
            rest = stripped[len(EXCHANGE_BLOCK_BEGIN):].strip()
            begin_idx = i
            block_sid = rest or None
            break
    if begin_idx is None:
        raw = text.strip()
        if not raw:
            _fail("relay input is empty — expected an exchange record, a "
                 "clarification manifest, or the paste block wrapping "
                 "either (BALE.md \u00a78.11 step 1)", reason="not-an-object")
        try:
            record = json.loads(raw)
        except json.JSONDecodeError as e:
            _fail(f"relay input is neither a BALE EXCHANGE paste block nor "
                 f"valid JSON: {e}. Expected an exchange record, a "
                 f"clarification manifest, or the paste block wrapping "
                 f"either.", reason="not-an-object")
        return record, None

    if block_sid is None:
        _fail(f"paste block's `{EXCHANGE_BLOCK_BEGIN}` sentinel carries no "
             f"session id — expected `{EXCHANGE_BLOCK_BEGIN} <sid>`",
             reason="malformed-block")
    end_idx = None
    for j in range(begin_idx + 1, len(lines)):
        if lines[j].strip() == EXCHANGE_BLOCK_END:
            end_idx = j
            break
    if end_idx is None:
        _fail(f"paste block has no `{EXCHANGE_BLOCK_END}` sentinel after "
             f"`{EXCHANGE_BLOCK_BEGIN} {block_sid}` — the paste is "
             f"truncated; re-request the block from its emitter rather "
             f"than reasoning from a partial one", reason="malformed-block")
    inner = lines[begin_idx + 1:end_idx]
    # Header: the leading comment lines. Stop at the first non-comment
    # line — the body starts there.
    k = 0
    while k < len(inner) and inner[k].lstrip().startswith("#"):
        k += 1
    if k >= len(inner):
        _fail("paste block carries a header but no body between its "
             "sentinels — the paste is truncated; re-request the block",
             reason="malformed-block")
    # Trailer: the last non-blank inner line.
    t = len(inner) - 1
    while t > k and not inner[t].strip():
        t -= 1
    m = _EXCHANGE_TRAILER_RE.match(inner[t].strip())
    if m is None:
        _fail(f"paste block's last line inside the sentinels is not the "
             f"`{EXCHANGE_TRAILER_LABEL} <hex>` integrity trailer (got "
             f"{inner[t].strip()!r}) — the paste is truncated or edited; "
             f"re-request the block from its emitter",
             reason="malformed-block")
    expected = m.group(1).lower()
    body = "\n".join(inner[k:t]) + "\n"
    actual = hashlib.sha256(body.encode("utf-8")).hexdigest()
    if actual != expected:
        if reescaped_body_matches(body, expected):
            _fail(f"paste block integrity trailer disagrees with its body "
                 f"(trailer sha256 {expected[:12]}\u2026, body sha256 "
                 f"{actual[:12]}\u2026), but the body re-serialized with "
                 f"ASCII escaping hashes to the trailer: the carrier "
                 f"unescaped the block's \\uXXXX escapes into literal "
                 f"characters in transit, so the content is intact and "
                 f"only its spelling changed; re-carry the block "
                 f"byte-for-byte (a file or an attachment rather than a "
                 f"rendered chat message), or re-request it from its "
                 f"emitter", reason="trailer-mismatch")
        _fail(f"paste block integrity trailer disagrees with its body "
             f"(trailer sha256 {expected[:12]}…, body sha256 "
             f"{actual[:12]}…) — the paste is truncated or was edited in "
             f"transit; re-request the block from its emitter rather "
             f"than reasoning from a partial one", reason="trailer-mismatch")
    try:
        record = json.loads(body)
    except json.JSONDecodeError as e:
        # Unreachable for a block bale emitted (the trailer matched a body
        # bale rendered), reachable for a hand-built block whose trailer
        # was computed over invalid JSON — still a data problem, named.
        _fail(f"paste block body is not valid JSON: {e}",
              reason="not-an-object")
    return record, block_sid


def _normalize_manifest_to_record(manifest: dict, sid: str, seq: int,
                                  created_at: str) -> dict:
    """The clarification manifest's reading as an exchange record
    (ADR-0017 clause 3; BALE.md §8.11 'The thread'): `from: worker`,
    `round` = its NNN, `created_at` = the preserved stamp, questions[]
    lifted verbatim. This is the paste-block body relay emits after a
    manifest ingest — a planner answering keys `question_round` off it —
    while the manifest itself is preserved untouched on disk, so the
    thread is byte-identical to the one apply's tarball ingest leaves.
    """
    return {
        "record_version": 1,
        "session_id": sid,
        "round": seq,
        "from": EXCHANGE_SIDE_WORKER,
        "created_at": created_at,
        "questions": list(manifest.get("questions") or []),
    }


def read_exchange_thread(repo: Path, sid: str) -> list[dict]:
    """Read the session's preserved thread as exchange_record_view rows,
    ordered by round. Unreadable records are logged and read as the
    all-None view (their round still counts — presence is the fact);
    the reader never raises on data."""
    from __main__ import log  # lazy — see module docstring
    from bale_apply import clarifications_dir  # lazy — sibling, loaded by bin/bale
    from bale_report import exchange_record_view  # lazy — sibling, loaded by bin/bale
    thread: list[dict] = []
    clar_dir = clarifications_dir(repo, sid)
    if not clar_dir.is_dir():
        return thread
    for pos, path in enumerate(sorted(clar_dir.glob("*.json")), start=1):
        try:
            n = int(path.stem)
        except ValueError:
            n = pos
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            log(f"relay: thread record {path.name} unreadable ({e}); its "
                f"questions cannot resolve an answer")
            data = None
        thread.append(exchange_record_view(data, n))
    return thread


def unresolved_answers(record: dict, thread: list[dict]) -> list[str]:
    """The referential check (the sitting's ruling, item 3): every
    answers[] row's (question_round, question_index) must resolve to a
    question in an already-preserved record of that round. Returns one
    message per unresolved pair, naming it; [] when every answer
    resolves. A shape check against the thread, not a sequencing rule:
    it catches a mis-numbered or mis-pasted answer before it is
    preserved. Pure over the view rows read_exchange_thread returns."""
    by_round = {row["round"]: row for row in thread}
    problems: list[str] = []
    for i, row in enumerate(record.get("answers") or []):
        if not isinstance(row, dict):
            continue  # validate_exchange_record already reported it
        qr, qi = row.get("question_round"), row.get("question_index")
        if not isinstance(qr, int) or not isinstance(qi, int):
            continue  # likewise
        src = by_round.get(qr)
        if src is None:
            problems.append(
                f"answers[{i}] (question_round {qr}, question_index {qi}): "
                f"no preserved record for round {qr}")
            continue
        qs = src["questions"]
        if qs is None:
            problems.append(
                f"answers[{i}] (question_round {qr}, question_index {qi}): "
                f"round {qr}'s record carries no readable questions[]")
            continue
        if not 0 <= qi < len(qs):
            problems.append(
                f"answers[{i}] (question_round {qr}, question_index {qi}): "
                f"round {qr} has {len(qs)} question(s), indices "
                f"0..{len(qs) - 1}")
    return problems


def _next_step_trailer(sid: str, awaiting: str, latest_round: int) -> list[str]:
    """The summary's next-step line after a round whose latest record
    leaves the thread awaiting `awaiting` — shared by the recording path
    and the no-file re-emit path so the two emissions of the same
    round's block always carry the same instruction."""
    if awaiting == EXCHANGE_SIDE_PLANNER:
        return [
            f"Next step — answer as an exchange record (from: planner, "
            f"round {latest_round + 1}, answers[] keyed question_round "
            f"{latest_round}), then `bale relay {sid} <answer.json|->`.",
        ]
    return [
        f"Next step — carry the block above to the worker; it continues "
        f"under {sid} and ships the normal response, then "
        f"`bale apply <response>`.",
    ]


def _cmd_reemit(repo: Path, sid: str, *, want_json: bool = False,
                report_sid: Optional[str] = None,
                log_path: Optional[str] = None) -> int:
    """The no-file form of `bale relay` (v0.4.22, board row 60; ADR-0017
    Notes): re-emit the paste block for the thread's latest recorded
    round, byte-identical to the original emission, and record nothing.

    Read-only end to end: no record is written, no thread mutation, no
    registry touch — the session gates (open, unbranched) have already
    run in cmd_relay, and everything past them here only reads. The
    block is rebuilt from the preserved record through the same
    rendering the original emission used: a preserved clarification
    manifest renders in its `from: worker` exchange-record reading
    (round = its NNN, created_at = the preserved stamp) and a preserved
    exchange record renders as itself, its `preserved_at` sidecar
    stripped — exactly what format_exchange_block was handed the first
    time, so the bytes match. A sid with no recorded rounds refuses
    loudly, naming the sid; an unreadable latest record refuses rather
    than re-emitting bytes it cannot stand behind.

    `want_json` (v0.4.48, `bale relay --json`): the block is not written
    to stdout; the "re-emitted" line carrying it is, last, after the
    clipboard notice and the summary (both stderr, unchanged).
    """
    from __main__ import fail, log  # lazy — see module docstring
    from bale_apply import clarifications_dir  # lazy — sibling, loaded by bin/bale
    from bale_report import (  # lazy — sibling, loaded by bin/bale
        CLIPBOARD_COPIED,
        PASTE_BLOCK_EXCHANGE,
        RELAY_OUTCOME_REEMITTED,
        awaiting_side,
        copy_paste_block,
        emit_json_line,
        emit_stdout_block,
        format_relay_json,
        format_summary_block,
    )
    clar_dir = clarifications_dir(repo, sid)
    records = sorted(clar_dir.glob("*.json")) if clar_dir.is_dir() else []
    if not records:
        fail(f"session {sid} has no recorded rounds — nothing to re-emit. "
             f"The no-file form re-emits the thread's latest recorded "
             f"round; record round one first (apply the clarification "
             f"tarball, or `bale relay {sid} <file|->`).", reason="no-rounds")
    path = records[-1]
    try:
        rnd = int(path.stem)
    except ValueError:
        rnd = len(records)  # read_exchange_thread's positional fallback
    try:
        preserved = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        fail(f"the thread's latest recorded round {path.name} is "
             f"unreadable ({e}) — nothing re-emitted. Fix or remove the "
             f"record at {path} and re-run.", reason="unreadable-record")
    if not isinstance(preserved, dict):
        fail(f"the thread's latest recorded round {path.name} is not a "
             f"JSON object (got {type(preserved).__name__}) — nothing "
             f"re-emitted.", reason="unreadable-record")
    preserved_at = preserved.pop("preserved_at", None)
    if preserved.get("response_kind") == "clarification":
        kind = "clarification manifest"
        body_record = _normalize_manifest_to_record(preserved, sid, rnd,
                                                    preserved_at)
    else:
        kind = "exchange record"
        body_record = preserved
    side = body_record.get("from")
    rel_path = path.relative_to(repo)
    log(f"relay: no file argument — re-emitting the thread's latest "
        f"recorded round (v0.4.22)")
    block = format_exchange_block(sid, body_record)
    if not want_json:
        emit_stdout_block(block)
    # Session clipboard-paste-blocks: the block, BEGIN through END, to
    # the clipboard when one is configured. stdout stays exactly the
    # block; the one notice rides stderr (copy_paste_block's contract).
    copied = copy_paste_block(repo, PASTE_BLOCK_EXCHANGE, block)
    awaiting = awaiting_side(side)
    log(f"relay: {kind} at {rel_path} (round {rnd}, from {side}) "
        f"re-emitted; nothing recorded — the thread, the session, and "
        f"the registry are untouched")
    print(format_summary_block(
        [
            ("session", sid),
            ("re-emitted", f"{rel_path} (round {rnd}, from {side})"),
            ("thread", f"{len(records)} round(s); awaiting {awaiting}"),
            ("block", f"emitted on stdout for the {awaiting}, "
                      f"byte-identical to the original emission"),
        ],
        status="RE-EMITTED",
        sid=sid,
        trailer=_next_step_trailer(sid, awaiting, rnd),
    ))
    if want_json:
        # `kind` and `preserved` stay null: nothing was ingested or
        # written (format_relay_json's docstring).
        emit_json_line(format_relay_json(
            outcome=RELAY_OUTCOME_REEMITTED,
            sid=report_sid if report_sid is not None else sid,
            round_no=rnd, side=side, awaiting=awaiting,
            block=block, log_path=log_path,
            clipboard=copied == CLIPBOARD_COPIED))
    return 0


def _read_relay_input(arg: str, cwd: Path, repo: Path) -> tuple[bytes, str]:
    """Read the relay input: stdin for `-`, else a file resolved like
    apply's tarball argument (cwd, then apply.search_paths; absolute
    bypasses — the one resolver every inbound surface shares). Returns
    (bytes, display name)."""
    from __main__ import (  # lazy — see module docstring
        fail,
        locate_inbound_path,
        refusal_reason,
    )
    import bale_config  # lazy — sibling module, loaded by bin/bale
    if arg == "-":
        try:
            data = sys.stdin.buffer.read()
        except OSError as e:
            fail(f"could not read the exchange from stdin: {e}",
                 reason="unreadable-input")
        return data, "<stdin>"
    with refusal_reason("config-invalid"):
        cfg = bale_config.merged_config(repo)
        search = bale_config.get_apply_search_paths(cfg)
    src = locate_inbound_path(arg, cwd, search)
    if src is None:
        lines = [f"exchange file not found: {arg}", "  searched:",
                 f"    {cwd}  (cwd)"]
        lines += [f"    {sp}" for sp in search]
        fail("\n".join(lines), reason="not-found")
    if not src.is_file():
        fail(f"exchange file not found: {src}", reason="not-found")
    try:
        return src.read_bytes(), str(src)
    except OSError as e:
        fail(f"could not read exchange file {src}: {e}",
             reason="unreadable-input")


def cmd_relay(args: argparse.Namespace) -> int:
    """`bale relay <sid> [<file|->]` — record one exchange in a suspended
    session's thread and emit the counterpart's paste block (BALE.md
    §8.11; contract row §11.34). With no file argument (v0.4.22, board
    row 60), the verb instead re-emits the paste block for the thread's
    latest recorded round, byte-identical to the original emission, and
    records nothing — the session gates below still run, then _cmd_reemit
    takes over and steps 2–7 never engage. The recording flow, each
    refusal naming its rule and preserving nothing:

    1. Session gates. `<sid>` must be open in the registry (ADR-0006),
       and no `bale/<sid>` branch may exist — a held session's
       clarification round is history (`bale status`'s precedence), and
       the thread does not reopen under a held normal response.
    2. Ingest (parse_exchange_input): the paste block's trailer is
       verified against its body before anything else is trusted, and a
       block whose sentinel names another sid refuses; bare JSON is
       accepted as-is.
    3. Classify and validate. `response_kind: "clarification"` is a
       clarification manifest — today's round-one shape — gated the way
       apply gates it (session_id, non-empty valid questions[]) and read
       as a `from: worker` record; anything else is an exchange record,
       gated by validate_exchange_record (schema, closed vocabularies,
       at-least-one-array, created_at UTC, answers key earlier rounds).
    4. Sequencing — exactly the facts D4 pins, no more: session_id equals
       `<sid>`; round equals the thread's next NNN (a stale or skipped
       round refuses loudly, naming both); and round one is worker-only
       (the planner initiates through the request, a bundle, or a HOLD
       card, never through the thread). No `from`-alternation rule: a
       worker may post twice.
    5. Answer resolvability (unresolved_answers): every
       (question_round, question_index) resolves to a preserved question.
    6. Preserve as the next NNN through preserve_clarification_record —
       the same write apply's clarification handler uses, with the same
       `preserved_at` sidecar — and retain the lock: relay never stages,
       validates, commits, or closes, and writes no telemetry record
       (the eventual normal response records; §8.10.2). A REFUSAL in
       steps 2–5 does write one (v0.4.41): a `relay-refused` attempt
       whose `cause` is the refusal's first line (record_relay_refusal)
       — the session stays open and suspended, so stats counts it
       in-flight. The session gates in step 1 record nothing.
    7. Emit the counterpart-facing block on stdout (the machine-report
       stream discipline: `[bale] ` lines and the trailer on stderr),
       copy it to the clipboard when a clipboard command is configured
       (session clipboard-paste-blocks: one stderr notice, stdout and
       the exit untouched — the no-file re-emit copies too), and end
       with the next-step hint — answer it as the planner, or carry it
       to the worker.

    `--json` (v0.4.48): stdout carries exactly one line of JSON on every
    path instead of the bare block — "relayed" and "re-emitted" with the
    block riding inside it, byte-identical to what human mode prints, and
    "relay-refused" on any refusal that exits 1, printed beside the
    unchanged `[bale] error:` line with the refusal's `cause` and the
    relay-refused record's path when one was written. stderr and the
    exit codes are unchanged. format_relay_json (bin/bale_report.py) owns
    the keys. The refused line is printed here, by the wrapper around
    _cmd_relay, so every fail() below — the session gates, the input
    read, the ingest gates — reaches it without a per-site change.
    Since v0.4.50 the line also carries `reason`: each refusal site names
    its RELAY_REFUSAL_REASONS code through fail(reason=...) (_fail's
    keyword in this module), and the wrapper reads it back off the exit
    with exit_reason — the vocabulary's fallback when none rode it —
    beside exit_cause's `cause`.
    """
    from __main__ import exit_cause, exit_reason  # lazy — module docstring
    from bale_report import (  # lazy — sibling
        REFUSAL_REASON_FALLBACK,
        RELAY_REFUSAL_REASONS,
        emit_json_line,
        enable_json_mode,
        format_relay_refusal_json,
    )

    # Stream discipline first, before any [bale] line: stdout is the
    # block and only the block — or, under --json, the one line. The
    # discipline is the verb's in both modes, not the flag's.
    enable_json_mode()
    want_json = bool(getattr(args, "json", False))
    # What the refused line reports, filled as the run wires it: the
    # session log once set_log_file ran, and the relay-refused record
    # once record_relay_refusal wrote one.
    report: dict = {"log": None, "telemetry": None}
    try:
        return _cmd_relay(args, want_json=want_json, report=report)
    except SystemExit as e:
        if want_json and getattr(e, "code", None) not in (None, 0):
            emit_json_line(format_relay_refusal_json(
                sid=args.sid,
                reason=exit_reason(e, RELAY_REFUSAL_REASONS,
                                   REFUSAL_REASON_FALLBACK),
                cause=exit_cause(e),
                log_path=report["log"], telemetry=report["telemetry"]))
        raise


def _cmd_relay(args: argparse.Namespace, *, want_json: bool,
               report: dict) -> int:
    """cmd_relay's body (its docstring is the contract), split out in
    v0.4.48 so one wrapper can print `--json`'s refused line for every
    refusal. `report` is the wrapper's: this fills `log` when the session
    log is wired and `telemetry` when a refusal is recorded."""
    from __main__ import (  # lazy — see module docstring
        _branch_exists,
        fail,
        log,
        open_sessions,
        refuse_system_dir,
        repo_root,
        session_is_open,
        set_log_file,
    )

    cwd = Path.cwd().resolve()
    refuse_system_dir(cwd)
    repo = repo_root(cwd)
    if repo is None:
        fail("not in a git repo. `bale relay` requires the project repo "
             "that holds the suspended session's `.bale/` state.",
             reason="not-a-repo")
    refuse_system_dir(repo)
    sid = args.sid.strip()
    if not sid:
        fail("`bale relay` needs a session id: `bale relay <sid> <file|->`",
             reason="no-sid")

    # Step 1: session gates.
    if not session_is_open(repo, sid):
        open_now = open_sessions(repo)
        fail(f"session {sid} is not open in the registry — `bale relay` "
             f"records rounds in a suspended (open, unbranched) session "
             f"only. Open sessions: "
             f"{', '.join(open_now) if open_now else 'none'}. "
             f"A closed session's thread is history; repack to ask again.",
             reason="not-open")
    session_log = repo / ".bale" / "logs" / f"{sid}.log"
    set_log_file(session_log)
    report["log"] = str(session_log)
    if _branch_exists(repo, f"bale/{sid}"):
        fail(f"session {sid} has a bale/{sid} branch — a normal response "
             f"was applied and is held, so its clarification round is "
             f"history, not a live thread. Finish the held response "
             f"(`bale retry` / `bale revert {sid}`) before any further "
             f"exchange.", reason="held-branch")
    log(f"relay: session {sid}")

    # The no-file form: re-emit the latest recorded round, read-only
    # (v0.4.22). The session gates above have run; nothing below does.
    if args.file is None:
        return _cmd_reemit(repo, sid, want_json=want_json,
                           report_sid=args.sid, log_path=report["log"])

    # Step 2: ingest. The input is located first, outside the refusal
    # recorder: a file that is not found never reached relay, so it is
    # an invocation error, not a refused exchange.
    data, source_name = _read_relay_input(args.file, cwd, repo)
    # Steps 2–5 refuse the INPUT; each such refusal writes a
    # relay-refused attempt with its cause (v0.4.41,
    # record_relay_refusal) and re-raises. Nothing is preserved before
    # step 6, so the wrapper's span is exactly the refusals.
    try:
        record, block_sid, source_kind, side, rnd, next_seq, thread = \
            _ingest_and_gate(repo, sid, data, source_name)
    except SystemExit as e:
        report["telemetry"] = record_relay_refusal(repo, sid, e)
        raise
    kind = source_kind
    is_manifest = kind == "clarification manifest"

    # Step 6: preserve, lock retained.
    return _preserve_and_emit(repo, sid, record, kind, is_manifest, side,
                              next_seq, thread, source_name,
                              want_json=want_json, report_sid=args.sid,
                              log_path=report["log"])


def _ingest_and_gate(repo: Path, sid: str, data: bytes, source_name: str):
    """cmd_relay's steps 2–5 (see its docstring), factored out in v0.4.41
    so one wrapper can record every input refusal. Returns (record,
    block_sid, kind, side, round, next_seq, thread); refuses through
    fail() naming the rule, preserving nothing."""
    from __main__ import fail, log  # lazy — see module docstring
    from bale_apply import (  # lazy — sibling, loaded by bin/bale
        clarifications_dir,
        next_clarification_seq,
    )
    from bale_validate import (  # lazy — sibling, loaded by bin/bale
        validate_clarification_questions,
        validate_exchange_record,
    )
    record, block_sid = parse_exchange_input(data)
    if block_sid is not None:
        log(f"relay: paste block read from {source_name} (trailer verified)")
        if block_sid != sid:
            fail(f"paste block's sentinel names session {block_sid}, but "
                 f"`bale relay` was invoked for {sid} — the block belongs "
                 f"to another session's thread; nothing preserved",
                 reason="wrong-session")
    else:
        log(f"relay: bare JSON read from {source_name}")
    if not isinstance(record, dict):
        fail(f"relay input is not a JSON object (got "
             f"{type(record).__name__}); nothing preserved",
             reason="not-an-object")

    thread = read_exchange_thread(repo, sid)
    next_seq = next_clarification_seq(repo, sid)
    if next_seq != len(thread) + 1:
        # Defensive: both derive from the same glob; a disagreement means
        # the directory changed under us mid-command.
        fail(f"thread under {clarifications_dir(repo, sid)} changed while "
             f"relay was reading it (counted {len(thread)} record(s), "
             f"next seq {next_seq}); re-run", reason="thread-changed")

    # Step 3: classify + validate.
    is_manifest = record.get("response_kind") == "clarification"
    if is_manifest:
        kind = "clarification manifest"
        if record.get("session_id") != sid:
            fail(f"clarification manifest's session_id is "
                 f"{record.get('session_id')!r}, not {sid} — the manifest "
                 f"belongs to another session; nothing preserved",
                 reason="wrong-session")
        qs = record.get("questions")
        errors = validate_clarification_questions(qs)
        if not errors and not qs:
            errors = ["questions: a clarification manifest carries at "
                      "least one blocking question"]
        if errors:
            fail("clarification manifest fails the question-row gate "
                 "(response-manifest.schema.json questions items); "
                 "nothing preserved:\n  " + "\n  ".join(errors),
                 reason="schema")
        side = EXCHANGE_SIDE_WORKER
        rnd = next_seq  # a manifest carries no round; it takes the next
    else:
        kind = "exchange record"
        errors = validate_exchange_record(record)
        if errors:
            fail("exchange record fails exchange-record.schema.json "
                 "(BALE.md \u00a711 row 34); nothing preserved:\n  "
                 + "\n  ".join(errors), reason="schema")
        side = record["from"]
        rnd = record["round"]
        # Step 4: sequencing.
        if record["session_id"] != sid:
            fail(f"exchange record's session_id is {record['session_id']!r}, "
                 f"not {sid} — the record belongs to another session's "
                 f"thread; nothing preserved", reason="wrong-session")
        if rnd != next_seq:
            which = "stale" if rnd < next_seq else "skipped"
            fail(f"exchange record's round is {rnd} but the thread's next "
                 f"round is {next_seq} ({len(thread)} record(s) preserved "
                 f"under {clarifications_dir(repo, sid).relative_to(repo)}/) "
                 f"— a {which} round; nothing preserved. The round in the "
                 f"record must be the next NNN.",
                 reason=f"{which}-round")
        if side == EXCHANGE_SIDE_PLANNER and next_seq == 1:
            fail(f"round 1 of a thread is worker-only: the planner "
                 f"initiates through the request, a bundle, or a HOLD "
                 f"card, never through the thread (ADR-0017). Session "
                 f"{sid} has no preserved record yet, so a from: planner "
                 f"record has nothing to answer; nothing preserved.",
                 reason="planner-round-one")
        # Step 5: answer resolvability.
        problems = unresolved_answers(record, thread)
        if problems:
            fail("exchange record's answers do not all resolve to preserved "
                 "questions (question_round, question_index); nothing "
                 "preserved:\n  " + "\n  ".join(problems),
                 reason="unresolved-answer")
    if next_seq > 1 and thread[-1]["from"] is None:
        log(f"relay: the previous record's side could not be read; "
            f"recording round {next_seq} from {side} regardless")
    return record, block_sid, kind, side, rnd, next_seq, thread


def _preserve_and_emit(repo: Path, sid: str, record: dict, kind: str,
                       is_manifest: bool, side: str, next_seq: int,
                       thread: list, source_name: str, *,
                       want_json: bool = False,
                       report_sid: Optional[str] = None,
                       log_path: Optional[str] = None) -> int:
    """cmd_relay's steps 6–7 (see its docstring): preserve the gated
    record as the next NNN and emit the counterpart's block. Split out
    with _ingest_and_gate (v0.4.41); behavior unchanged. Under
    `want_json` (v0.4.48) the block rides the "relayed" line instead of
    stdout, emitted last (format_relay_json)."""
    from __main__ import fail, log  # lazy — see module docstring
    from bale_apply import preserve_clarification_record  # lazy — sibling
    from bale_report import (  # lazy — sibling, loaded by bin/bale
        CLIPBOARD_COPIED,
        PASTE_BLOCK_EXCHANGE,
        RELAY_OUTCOME_RELAYED,
        awaiting_side,
        copy_paste_block,
        emit_json_line,
        emit_stdout_block,
        format_relay_json,
        format_summary_block,
    )
    record_path = preserve_clarification_record(repo, sid, record)
    preserved_at = None
    try:
        preserved_at = json.loads(
            record_path.read_text(encoding="utf-8")).get("preserved_at")
    except (OSError, json.JSONDecodeError) as e:
        fail(f"preserved {record_path} but could not read it back: {e}",
             reason="unreadable-record")
    rel_path = record_path.relative_to(repo)
    log(f"relay: {kind} preserved as round {next_seq} at {rel_path} "
        f"(from {side})")
    log(f"relay: session {sid} stays open and suspended — no staging, "
        f"no validation, no commit, no telemetry record")

    # Step 7: emit.
    body_record = (_normalize_manifest_to_record(record, sid, next_seq,
                                                 preserved_at)
                   if is_manifest else record)
    block = format_exchange_block(sid, body_record)
    if not want_json:
        emit_stdout_block(block)
    # Session clipboard-paste-blocks: as in _cmd_reemit — the block to
    # the clipboard, the notice on stderr, stdout untouched.
    copied = copy_paste_block(repo, PASTE_BLOCK_EXCHANGE, block)

    awaiting = awaiting_side(side)
    trailer = _next_step_trailer(sid, awaiting, next_seq)
    print(format_summary_block(
        [
            ("session", sid),
            ("ingested", f"{kind} from {source_name}"),
            ("preserved", f"{rel_path} (round {next_seq}, from {side})"),
            ("thread", f"{next_seq} round(s); awaiting {awaiting}"),
            ("block", f"emitted on stdout for the {awaiting}"),
        ],
        status="RELAYED",
        sid=sid,
        trailer=trailer,
    ))
    if want_json:
        emit_json_line(format_relay_json(
            outcome=RELAY_OUTCOME_RELAYED,
            sid=report_sid if report_sid is not None else sid,
            round_no=next_seq, side=side, awaiting=awaiting, kind=kind,
            preserved=str(rel_path), block=block, log_path=log_path,
            clipboard=copied == CLIPBOARD_COPIED))
    return 0
