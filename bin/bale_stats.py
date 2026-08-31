"""bale_stats — the `bale stats` aggregation core (BALE.md §5.6, board 5 D6).

The eighth sibling module. Like `bale_rollback` (the fourth), this is not
an extraction of code that previously lived in `bin/bale` — it is the
net-new v0.3.24 trust-ledger read side, placed in its own module from the
start (extraction-by-need, CODE.md §3.1): neither `bale_report`
(rendering) nor `bin/bale` (wiring) is the home for corpus loading, unit
classification, and rate computation. The division per the ratified board
5 brief (D6): this module computes, `bale_report.format_stats_json` /
`format_stats_report` render, `bin/bale` wires the subcommand.

The corpus is `claude/telemetry/*.json` — the tracked per-session records
`schemas/telemetry-record.schema.json` describes — and NOTHING ELSE. In
particular `bale stats` never reads `.bale/` (D1): the transient side
varies by checkout, and an input that varies by checkout would poison
every rate computed over it. Everything this module consumes is under the
tracked substrate, so a fresh clone computes the same rates as the
original machine, minus only records not yet committed there (D5 — the
reader is the filesystem, matching §8.9's write-to-working-tree posture).

The unit model and every rate definition here follow brief D2 verbatim;
each function's docstring restates the definition it implements so a
future session can audit the code against the contract without the brief
in hand. Two membership rules deserve their one-home statement up front:

- **Read-only detection keys on `closure_reason == "closed-read-only"`,
  never on scope** (ratified constraint). A recorded scope of `[]` is
  overloaded in the real corpus: pre-ADR-0007 records also read `[]`, so
  scope-keyed detection would misclassify them.
- **Every rate reports its denominator, and a rate with a zero
  denominator is `None`** — honest "no data", never a fabricated 0 or a
  crash.

Diagnostics discipline: a record that fails to parse is skipped, counted
in the `parse_failures` row, and named on **stderr** (hard rule: silent
skips are bugs); a `record_version > 1` record is filtered, counted under
`filtered_record_versions`, and likewise named. This module writes those
lines to `sys.stderr` directly rather than through `bin/bale`'s `log()`:
in human (non---json) mode `log()` prints to stdout, and the stats
report's stdout is content — under `--json` it is exactly one line — so
the diagnostic channel is stderr in both modes. That is a deliberate,
documented deviation from the siblings' lazy `__main__` `log` idiom; the
module stays stdlib-pure and importable without `bin/bale` loaded, which
is also what makes it directly unit-testable.

Stateless and read-only: no writes, no locks, no git. Public surface is
`compute_stats(telemetry_dir, work_class=None, since=None)` returning the
plain-dict stats payload both renderers consume, and — board 44's level
2 — `compute_session_dossier(telemetry_dir, sid)`, one sid rendered
whole over the same one substrate; the loaders and
classifiers below them are importable for tests. The payload's *key
list* as a consumer contract is owned by the `format_stats_json`
docstring in `bin/bale_report.py` (one-home rule; the dossier line's
keys are owned by `format_session_dossier_json`'s, per the same
per-surface rule) — this module's docstrings describe semantics, not
the wire key set.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Optional


# The record shape this reader understands (telemetry-record.schema.json).
# A record_version above this is filtered and counted, per the schema's own
# instruction that consumers branch on the version.
SUPPORTED_RECORD_VERSION = 1

# Attempt commands that constitute a RESPONSE ATTEMPT (D2): a response was
# processed. unlock, pack, and rollback events are session-lifecycle facts,
# not response processing.
RESPONSE_COMMANDS = frozenset({"apply", "retry"})

# Envelope outcomes that mean the session is CLOSED (D2). rolled-back and
# re-applied are post-close history on an applied close: the session's
# closure category is "applied" and the rollback lands in the churn row.
CLOSED_OUTCOMES = frozenset({
    "applied", "reverted", "bailout", "unlocked", "rolled-back", "re-applied",
})

# Envelope outcomes that mean the session is IN-FLIGHT (D2): reported as a
# count, excluded from the closure mix. Stats reads only the corpus, never
# the .bale/ registry — in-flight is the corpus's honest view, not a
# lock-state claim. required-check-refused (board 6 session B — the D3
# coordination rider that lands WITH the gate, not after it): the step-15
# refusal keeps its session open exactly as the drift refusal does, so a
# session whose latest outcome is the new refusal is in-flight, never
# misclassed into the closure mix. The fuller stats rows for the outcome
# — the per-class refusal and override counts — landed in session D
# (v0.3.29, _class_row); this membership line preceded them by contract.
IN_FLIGHT_OUTCOMES = frozenset({
    "held", "scope-drift-refused", "rejected", "required-check-refused",
    # opened (board 63 write side, v0.4.21; this membership is the board
    # 44 read half): the record was created at session open and no close
    # or apply event has landed yet. In-flight by the schema's own
    # instruction ("readers treat the session as in-flight — never a
    # closure category"), which also retires the per-open-session
    # unrecognized-outcome warning closure_category used to emit.
    "opened",
})

# The work_class vocabulary the pack surface stamps (BALE.md §7), plus the
# ledger's own bucket for sessions with no feedback-bearing attempt.
# Aggregation buckets by the recorded value verbatim — an unexpected value
# forms its own honest row rather than being dropped or coerced — so this
# tuple is the *known* vocabulary (it drives the --work-class choices in
# bin/bale), not a filter.
WORK_CLASSES = ("code", "doc", "contract-doc", "meta", "mixed")
UNCLASSED = "unclassed"

# The packer-resolution sibling of UNCLASSED (board 44): sessions whose
# record carries no usable packer identity anywhere — no open-time
# provenance stamp, no feedback echo — bucket here, reported, never
# dropped or guessed. (The write side's own no-identity fallback is the
# literal "unconfigured", which is a *recorded* value and buckets
# verbatim like any other.)
UNATTRIBUTED = "unattributed"


def _warn(msg: str) -> None:
    """Stats diagnostic line, always on stderr (module docstring: the
    stats report's stdout is content in both output modes)."""
    sys.stderr.write(f"[bale] stats: {msg}\n")


# ---------------------------------------------------------------------------
# Corpus loading and parsing tolerances
# ---------------------------------------------------------------------------

def _record_shape_ok(loaded: object) -> bool:
    """Minimal shape check: the envelope fields aggregation stands on.

    Deliberately looser than the schema (additionalProperties is the
    schema's own posture) but strict on what the rates read: a dict with
    string session_id / created_at / outcome, an integer record_version,
    and a non-empty attempts[] of dicts each carrying at / outcome /
    command. A record failing this is a parse failure — counted and
    named, never a crash and never a silent skip.
    """
    if not isinstance(loaded, dict):
        return False
    if not isinstance(loaded.get("record_version"), int):
        return False
    for key in ("session_id", "created_at", "outcome"):
        if not isinstance(loaded.get(key), str) or not loaded[key]:
            return False
    attempts = loaded.get("attempts")
    if not isinstance(attempts, list) or not attempts:
        return False
    for a in attempts:
        if not isinstance(a, dict):
            return False
        for key in ("at", "outcome", "command"):
            if not isinstance(a.get(key), str) or not a[key]:
                return False
    return True


def load_corpus(telemetry_dir: Path) -> tuple[list[dict], list[str], list[str]]:
    """Load every claude/telemetry/*.json record, tolerantly.

    Returns (records, parse_failures, filtered_record_versions):
    filenames land in the second list when the file is unreadable, not
    JSON, or fails the minimal shape check (skipped, counted, named on
    stderr — D2's corrupt-record rule), and in the third when
    record_version > SUPPORTED_RECORD_VERSION (filtered and counted —
    consumers branch on the version, as the schema instructs). An absent
    or empty directory is the honest empty corpus: three empty lists, no
    error.
    """
    records: list[dict] = []
    parse_failures: list[str] = []
    filtered: list[str] = []
    if not telemetry_dir.is_dir():
        return records, parse_failures, filtered
    for path in sorted(telemetry_dir.glob("*.json")):
        try:
            loaded = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as e:
            parse_failures.append(path.name)
            _warn(f"skipped unparseable record {path.name}: {e}")
            continue
        if not _record_shape_ok(loaded):
            parse_failures.append(path.name)
            _warn(f"skipped malformed record {path.name}: missing or "
                  f"invalid envelope fields")
            continue
        if loaded["record_version"] > SUPPORTED_RECORD_VERSION:
            filtered.append(path.name)
            _warn(f"filtered {path.name}: record_version "
                  f"{loaded['record_version']} > supported "
                  f"{SUPPORTED_RECORD_VERSION}")
            continue
        records.append(loaded)
    return records, parse_failures, filtered


# ---------------------------------------------------------------------------
# Unit classification (D2)
# ---------------------------------------------------------------------------

def is_response_attempt(attempt: dict) -> bool:
    """D2: an attempts[] entry with command in {apply, retry}."""
    return attempt.get("command") in RESPONSE_COMMANDS


def is_validated_attempt(attempt: dict) -> bool:
    """D2: a response attempt with validation non-null."""
    return is_response_attempt(attempt) and isinstance(
        attempt.get("validation"), dict)


def _attempt_provenance_stamp(attempt: dict) -> Optional[dict]:
    """The attempt-level open-time provenance stamp (v0.4.21, board 63),
    or None. The one home for the read: per the schema the stamp rides
    on 'opened' attempts only, but the reader keys on the stamp itself —
    a dict under the `provenance` key — so a record whose stamp survived
    at another depth still resolves. Tolerant like every stamp read."""
    stamp = attempt.get("provenance")
    return stamp if isinstance(stamp, dict) else None


def _resolve_provenance_value(record: dict, key: str,
                              fallback: str) -> str:
    """Resolve one provenance identity (work_class or packer) for a
    session: the open-time stamp first, the feedback echo second (board
    63 fold-in, landed with board 44's read sides).

    Pass 1 reads the attempt-level `provenance` stamp — the open-time
    pair bale writes verbatim from the request manifest at pack, which
    exists precisely so sessions that close without a feedback-bearing
    attempt (unlock closures, open sessions) still resolve. Pass 2 is
    the pre-stamp behavior unchanged: the latest feedback-bearing
    attempt's mechanical.provenance echo. Both passes scan latest-first
    for symmetry; sessions carrying neither fall to `fallback`
    (UNCLASSED / UNATTRIBUTED), reported, never dropped or guessed.
    """
    for attempt in reversed(record["attempts"]):
        stamp = _attempt_provenance_stamp(attempt)
        if stamp is not None:
            value = stamp.get(key)
            if isinstance(value, str) and value:
                return value
    for attempt in reversed(record["attempts"]):
        feedback = attempt.get("feedback")
        if not isinstance(feedback, dict):
            continue
        provenance = (feedback.get("mechanical") or {}).get("provenance")
        if isinstance(provenance, dict):
            value = provenance.get(key)
            if isinstance(value, str) and value:
                return value
    return fallback


def session_work_class(record: dict) -> str:
    """Resolve the session's work class (D2; stamp-first since board 44).

    The open-time provenance stamp resolves first — the board 63 write
    side's pair, present on post-v0.4.21 'opened' attempts — falling
    back to the value on the session's LATEST feedback-bearing attempt
    (feedback.mechanical.provenance.work_class); sessions with neither —
    pre-stamp pure unlock closures, rejected-only — fall in the
    `unclassed` bucket, reported, never silently dropped or guessed.
    The stamp-first order is what closes the unlocked-session blind
    spot: the class now resolves for sessions that never carried a
    feedback echo. Attempt-level rates inherit this session-level
    resolution, which is what classes a rejected first attempt of a
    session whose later attempts carry the class.
    """
    return _resolve_provenance_value(record, "work_class", UNCLASSED)


def session_packer(record: dict) -> str:
    """Resolve the session's packer identity (board 44), the
    session_work_class sibling: the open-time provenance stamp first,
    the feedback echo's provenance.packer second, `unattributed` when
    the record carries neither. Buckets are the recorded value verbatim
    (the honest-row doctrine) — including the write side's own
    "unconfigured" fallback, which is a recorded identity, not this
    reader's absence bucket.
    """
    return _resolve_provenance_value(record, "packer", UNATTRIBUTED)


def is_read_only(record: dict) -> bool:
    """D2: any attempt with closure_reason == "closed-read-only".

    Keyed on closure_reason, NEVER on scope: the `[]` scope overload is
    real in the corpus (pre-ADR-0007 records also read `[]`).
    """
    return any(a.get("closure_reason") == "closed-read-only"
               for a in record["attempts"])


def is_crash_debris(record: dict) -> bool:
    """D2: any attempt with closure_reason == "crash-debris" — hygiene
    row, excluded from rates."""
    return any(a.get("closure_reason") == "crash-debris"
               for a in record["attempts"])


def closure_category(record: dict) -> Optional[tuple[str, Optional[str]]]:
    """Classify the session for the closure mix (D2).

    Returns (category, unlock_reason) for a closed session, None for an
    in-flight one. Categories: applied / reverted / bailout / unlocked —
    with rolled-back and re-applied envelope outcomes mapping to
    "applied" (they are post-close history on an applied close; the
    rollback itself is the churn row's fact, and v1 deliberately does
    not reinterpret it as a defect signal). For "unlocked" the second
    member is the closing attempt's closure_reason ("unspecified" when
    the record carries none — an honest bucket, not a guess).
    """
    outcome = record["outcome"]
    if outcome in IN_FLIGHT_OUTCOMES:
        return None
    if outcome in ("applied", "rolled-back", "re-applied"):
        return ("applied", None)
    if outcome in ("reverted", "bailout"):
        return (outcome, None)
    if outcome == "unlocked":
        reason: Optional[str] = None
        for attempt in reversed(record["attempts"]):
            if attempt.get("outcome") == "unlocked":
                reason = attempt.get("closure_reason")
                break
        return ("unlocked", reason if reason else "unspecified")
    # An outcome outside both sets is a vocabulary this reader doesn't
    # know; treat it as in-flight (reported in that count) rather than
    # inventing a closure category for it.
    _warn(f"record {record['session_id']}: unrecognized envelope outcome "
          f"{outcome!r}; counting the session as in-flight")
    return None


def _closing_attempt(record: dict) -> Optional[dict]:
    """The latest attempt whose outcome is a closing one (applied,
    reverted, bailout, unlocked) — where the D1 clarification stamp
    lives. Rollback attempts are post-close history, not closures."""
    closing = {"applied", "reverted", "bailout", "unlocked"}
    for attempt in reversed(record["attempts"]):
        if attempt.get("outcome") in closing:
            return attempt
    return None


def _clarification_stamp(record: dict) -> Optional[dict]:
    """The promoted clarification summary on the closing attempt, or
    None when the key is absent (pre-epoch unknown — never conflated
    with a known zero, which is key presence with rounds: 0)."""
    attempt = _closing_attempt(record)
    if attempt is None:
        return None
    stamp = attempt.get("clarification")
    return stamp if isinstance(stamp, dict) else None


def _latest_feedback(record: dict) -> Optional[dict]:
    """The latest feedback-bearing attempt's feedback block, or None."""
    for attempt in reversed(record["attempts"]):
        feedback = attempt.get("feedback")
        if isinstance(feedback, dict):
            return feedback
    return None


def _attempt_linkage(attempt: dict) -> Optional[dict]:
    """The attempt's feedback.mechanical.linkage stamp, or None.

    The one home for the read (board 65): the linkage rollup and the
    clarification cross-check both go through here. Tolerant like every
    feedback read — a missing block or a non-dict linkage reads as no
    stamp, never a crash.
    """
    feedback = attempt.get("feedback")
    if not isinstance(feedback, dict):
        return None
    linkage = (feedback.get("mechanical") or {}).get("linkage")
    return linkage if isinstance(linkage, dict) else None


def _linkage_point(linkage: dict) -> Optional[str]:
    """The linkage stamp's placement value, or None when unreported.

    The current response-manifest schema spells the key `point`
    (enum pre-read / pre-build / mid-build); records persisted from
    older manifests spell it `surfaced` — the corpus carries both, and
    telemetry persists feedback verbatim, so the reader accepts the
    legacy key rather than reporting real placements as missing.
    `point` wins when both are present. Values pass through verbatim
    (the honest-row doctrine); only the key is normalized here.
    """
    for key in ("point", "surfaced"):
        value = linkage.get(key)
        if isinstance(value, str) and value:
            return value
    return None


def _self_reported_clarification(record: dict) -> bool:
    """Cross-check 1's self-reported side: any attempt whose
    feedback.mechanical.linkage.kind == "clarification"."""
    for attempt in record["attempts"]:
        linkage = _attempt_linkage(attempt)
        if linkage is not None and linkage.get("kind") == "clarification":
            return True
    return False


def _rate(numerator: int, denominator: int) -> Optional[float]:
    """A rate with its honesty rule: None on a zero denominator."""
    if denominator == 0:
        return None
    return numerator / denominator


# The absence bucket every self-reported grouping shares (linkage kinds
# and points, claim bases): the stamp exists but omits the field.
UNSPECIFIED = "unspecified"


def _claim_basis(validation: dict, check_name: str,
                 verdict_entry: dict) -> str:
    """Resolve one check's claim basis (board 10 queue, landed with
    board 44): the claim_verdict row's own `claim_basis` when present,
    else the claims map's annotated object form for the same check, else
    UNSPECIFIED — the honest bucket for every bare-string claim and
    every pre-v0.4.6 record, which carry no basis at all. Values pass
    through verbatim (the honest-row doctrine): the schema's enum is
    closed, but an out-of-vocabulary basis forms its own row here
    rather than being dropped or coerced.
    """
    basis = (verdict_entry or {}).get("claim_basis")
    if isinstance(basis, str) and basis:
        return basis
    claim = (validation.get("claims") or {}).get(check_name) \
        if isinstance(validation.get("claims"), dict) else None
    if isinstance(claim, dict):
        basis = claim.get("claim_basis")
        if isinstance(basis, str) and basis:
            return basis
    return UNSPECIFIED


def _session_contract_docs(record: dict) -> Optional[dict]:
    """The session's contract-doc hash set, or None when unstamped.

    Read from the latest feedback-bearing attempt's
    mechanical.provenance.contract_docs — the request provenance block
    apply persists verbatim — mirroring session resolution's
    latest-first scan. (The open-time attempt stamp carries only
    work_class and packer, so feedback is this read's one carrier
    today.) None means the record predates provenance echoes or the
    request carried none — pre-epoch unknown, bucketed as "unstamped",
    never conflated with a recorded hash set.
    """
    for attempt in reversed(record["attempts"]):
        feedback = attempt.get("feedback")
        if not isinstance(feedback, dict):
            continue
        provenance = (feedback.get("mechanical") or {}).get("provenance")
        if not isinstance(provenance, dict):
            continue
        docs = provenance.get("contract_docs")
        if isinstance(docs, dict) and docs and all(
                isinstance(k, str) and isinstance(v, str)
                for k, v in docs.items()):
            return dict(docs)
    return None


DOC_EPOCH_UNSTAMPED = "unstamped"


def _doc_epoch_key(docs: Optional[dict]) -> str:
    """A stable, jq-derivable bucket key for one contract-doc hash set:
    the first 12 hex of sha256 over the sorted "name=hash" lines. The
    full hash set is reported beside the key in the epoch row, so the
    digest is an identifier, never the only record of what it names.
    None (unstamped) keys the DOC_EPOCH_UNSTAMPED bucket.
    """
    if docs is None:
        return DOC_EPOCH_UNSTAMPED
    joined = "\n".join(f"{name}={docs[name]}" for name in sorted(docs))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:12]


# ---------------------------------------------------------------------------
# Forecast epoch and containment (ADR-0015, board 13 session B)
# ---------------------------------------------------------------------------

# The write-forecast epoch marker (ADR-0015, design brief I.5): the
# attempt-level key bale stamps on every post-epoch attempt, absent
# before. Key presence is epoch membership — post-epoch, attempts[].scope
# holds the session's write forecast, and drift computed against it is
# judgment past the ask; pre-epoch, scope was the conflated include set
# and drift against it was structurally near zero. The forecast rows
# below read post-epoch attempts ONLY, so the two eras never aggregate
# into one lying trend line. record_version stays 1 (additive).
FORECAST_SCOPE_KIND = "write-forecast"


def _scope_norm(p: str) -> str:
    """Normalize one path for forecast containment.

    A deliberate stdlib-pure mirror of `scope_path` in bin/bale (same
    normal form: repo-relative, forward-slash, no trailing slash, no
    leading `./`; empty and `.` both mean the whole tree). Duplicated
    rather than imported because this module's contract is
    importability without bin/bale loaded (module docstring); the
    mirror is pinned by tests/test_forecast_ledger.py so the two homes
    cannot drift silently.
    """
    s = os.path.normpath(p.strip()).replace(os.sep, "/")
    return "." if s in ("", ".") else s


def _forecast_covers(entries: list, path: str) -> bool:
    """True when a normalized change path lies inside the forecast.

    The stdlib-pure mirror of `scope_covers_path` in bin/bale — the
    drift gate's own containment test, so the drift the ledger counts
    is exactly the drift the gate saw: an entry covers the path when
    the entry is "." (the whole tree), equals the path, or is a
    directory ancestor of it; an empty forecast covers nothing (the
    read-only shape). `entries` must already be _scope_norm'd; the
    path is normalized here.
    """
    p = _scope_norm(path)
    return any(
        entry == "." or p == entry or p.startswith(entry + "/")
        for entry in entries
    )


def _departure_paths(attempt: dict) -> set:
    """The worker's self-declared forecast departures on one attempt,
    as a normalized path set.

    Reads feedback.self_reported.forecast_departures — the additive
    optional [{path, why}] field (ADR-0015 E2, ratified;
    response-manifest.schema.json) apply persists verbatim into the
    record. Tolerant like every feedback read: a missing block, a
    non-list field, or a malformed entry reads as no declaration —
    the cross-check reports what was declared, never crashes on what
    wasn't.
    """
    feedback = attempt.get("feedback")
    if not isinstance(feedback, dict):
        return set()
    reported = feedback.get("self_reported")
    if not isinstance(reported, dict):
        return set()
    departures = reported.get("forecast_departures")
    if not isinstance(departures, list):
        return set()
    return {
        _scope_norm(d["path"]) for d in departures
        if isinstance(d, dict) and isinstance(d.get("path"), str)
        and d["path"].strip()
    }


# ---------------------------------------------------------------------------
# Epoch and coverage (D2)
# ---------------------------------------------------------------------------

def _epoch(records: list[dict]) -> Optional[dict]:
    """The corpus epoch: first sid and created_at by minimum created_at.

    ISO 8601 UTC strings order lexicographically, so the minimum is the
    string minimum — no datetime parsing, no timezone arithmetic (the
    schema fixes UTC). None on an empty corpus. Pre-epoch sessions exist
    only in git and are not counted (D2: no git mining at v1 — a second,
    differently-shaped input would undermine the one-substrate property).
    """
    if not records:
        return None
    first = min(records, key=lambda r: r["created_at"])
    return {"first_sid": first["session_id"],
            "first_created_at": first["created_at"]}


def _coverage_row(records: list[dict], key: str) -> Optional[dict]:
    """A sub-epoch coverage row by attempt-key presence (D2).

    First record (by created_at) with any attempt carrying `key`, plus
    the count of records lacking it everywhere. Key-presence detection
    needs no version table and stays correct as the corpus grows. None
    when no record carries the key at all (the sub-epoch has not begun).
    """
    carrying = [r for r in records
                if any(key in a for a in r["attempts"])]
    if not carrying:
        return None
    first = min(carrying, key=lambda r: r["created_at"])
    return {"first_sid": first["session_id"],
            "records_lacking": len(records) - len(carrying)}


# ---------------------------------------------------------------------------
# The aggregation
# ---------------------------------------------------------------------------

def _class_row(sessions: list[dict]) -> dict:
    """Compute one work class's D2 rate row over its member sessions.

    Every numerator and denominator is reported beside its rate so the
    consumer (board 10's grant harness, a human reading the table) can
    re-derive or re-weight; a zero denominator renders the rate None.

    Checks are counted per agreement value under the schema's own
    vocabulary — agree / disagree / n/a
    (telemetry-record.schema.json, claim_verdict.agreement) — one
    named count per value, no catch-all bucket. Over a well-formed
    corpus the three sum to `checks`; an out-of-vocabulary agreement
    value counts in `checks` only and is named on stderr.
    `agreement_rate` keeps its D2 definition untouched: agree over ALL
    checks, n/a included.

    Blind-checkpoint rows (v0.3.29, board 6 session D, brief D4.2):
    a CHECKPOINTED attempt is a validated attempt whose
    `attempts[].checkpoint` stamp carries `configured: true` — the
    key-presence epoch doctrine means pre-epoch attempts (no key) and
    known-zero attempts (`configured: false`) are both outside the
    denominator, for different, never-conflated reasons. The
    checkpoint-HOLD count is the checkpointed attempts whose stamp's
    own `state` is "HOLD" (the per-source attribution field — the
    checkpoint script objected or errored, regardless of the worker's
    verdict), and the rate is that count over checkpointed attempts,
    None on a zero denominator. Blind outcomes never touch the
    claim/verdict counts above: the checkpoint has no claims by
    construction.

    Required-check rows (same session, brief D3/D4.2): the refusal
    count is the response attempts whose outcome is
    `required-check-refused` (the step-15 gate, board 6 session B),
    and the override count is the attempts carrying a non-empty
    `required_check_overrides` list — both counts beside the drift
    rows, mirroring drift's refusal/override pair; override incidence
    is a count, not a rate, per the drift precedent.

    Linkage rollup (board 65): the `linkage` sub-dict counts the
    class's attempts carrying a `feedback.mechanical.linkage` stamp —
    the self-reported record that the session went through a probe or
    clarification round on the way to the response
    (response-manifest.schema.json). Counts and groupings only,
    nominated beside the rates, never blended into them: `attempts`
    is the stamped-attempt count, `kinds` buckets by the stamp's
    `kind` verbatim (an unexpected value forms its own honest row;
    a stamp with no usable kind lands under "unspecified"), and
    `points` buckets by the placement value `_linkage_point` resolves
    (the current `point` key or the legacy `surfaced` spelling; a
    stamp reporting neither lands under "unspecified"). Every attempt
    is scanned, response or not, mirroring the clarification
    cross-check's read — the stamp is self-reported data and the
    rollup reports what was recorded, wherever it was recorded. The
    per-work-class split is the classes table itself.

    Forecast rows (ADR-0015, board 13 session B — design brief I.5).
    All three read POST-EPOCH response attempts only: attempts whose
    `scope_kind` reads FORECAST_SCOPE_KIND, where `scope` is the
    session's recorded write forecast. Pre-epoch attempts (no key)
    aggregate under the pre-separation semantics above and never
    enter these denominators — key absence is the epoch boundary.
    Both scoping signals below are about the packer's forecasts, not
    the worker's discipline (ADR-0014's doctrine generalized):

    - **Forecast drift rate** — a post-epoch response attempt DRIFTS
      when at least one of its change_paths lies outside the forecast
      (`_forecast_covers`, the drift gate's own containment, so the
      ledger's drift is the gate's drift). The rate is drifting
      attempts over post-epoch response attempts — the drift the
      constraint says the ledger grades: judgment past the ask.
      Drift clustering reads as forecasts drawn too NARROW.
    - **Admission rate** — path-granular, the unit the operator
      decides in: admitted drift paths (the attempt's drift set ∩ its
      `overridden_paths`) over all drift paths, both summed as
      per-attempt unique-path counts across post-epoch response
      attempts. The refused complement is derivable
      (`forecast_drift_paths - forecast_admitted_paths`).
    - **Forecast precision** — touched forecast entries over forecast
      entries, where an entry is TOUCHED when any change path lies
      under it (same containment, per-entry). Counted per attempt
      across post-epoch response attempts that recorded at least one
      change path — an attempt that landed nothing (a pre-manifest
      rejection) measures nothing about forecast width and stays
      outside both counts; a retried session's forecast is counted
      once per attempt, symmetric with the drift denominators.
      `forecast_entries_untouched` is reported beside the rate — the
      imprecision count itself. Imprecision clustering reads as
      forecasts drawn too WIDE, the mirror signal.

    Claim-coverage rows (board 44, the queued no-new-fields cut):
    `claims_declared` sums the promoted claims-map entries over
    validated attempts, `claims_per_validated_attempt` is that sum
    over validated attempts (a ratio, not a 0..1 rate — it can exceed
    1; None on a zero denominator), and
    `empty_claims_validated_attempts` counts validated attempts whose
    promoted claims map is empty. The last is the computable form of
    the queued "empty claims beside a non-empty validation_will_run"
    count: the record does not persist `validation_will_run` (only the
    claims map is promoted), but validation RAN on every validated
    attempt, so an empty claims map here is the §5.3 wasted-signal
    shape the cut hunts — with the one honest residual that a session
    whose checks were all mechanical (the typo-session shape) counts
    too. Gaming shows in aggregate trends, which is where the ledger
    already looks; the per-packer cut of the same three values is
    compute_stats' `packers` table.

    Checkpoint CATCH rows (board 44, beside the D4.2 hold rows): a
    CATCH is a checkpointed attempt where the blind oracle objected —
    the stamp's own `state` is "HOLD" with the stamp's own
    `exit_code` 1 — while the worker's own script passed
    (`validation.exit_code` 0, the worker-script code per the schema;
    the attempt's overall state needs both). A both-HOLD attempt is
    not a catch (the worker also saw it), and a checkpoint that
    ERRORED (stamp exit 2) is not a catch either — that is a tooling
    fact, the unparsed-share analogy, still visible in the hold count.
    `checkpoint_catch_rate` is catches over checkpointed attempts,
    None on zero.

    Claim-basis split (board 44, from the board 10 queue): the
    `claim_basis` sub-dict buckets claim_verdict checks by the
    worker's declared basis — `observed` (a real run before shipping)
    vs `predicted` (structural grounds) vs UNSPECIFIED (every
    bare-string claim and every pre-v0.4.6 record) — resolved per
    check by `_claim_basis` (verdict row first, annotated claims-map
    form second). Each bucket reports {checks, agree, agreement_rate}
    so the observed-vs-predicted calibration split reads directly;
    buckets are the recorded value verbatim (honest rows), and the
    per-basis counts partition `checks` the same way the
    per-agreement counts do.

    Bucket membership (board 44 level 1): the `members` sub-dict names
    the session ids composing each anomaly count, sid-granular and
    sorted — the sets were computed on the way to the counts already
    and are now emitted, so an anomalous rate drills to its sids with
    one jq. Keys mirror their counts: held, checks_disagree, unparsed,
    drift_refused, rejected, required_check_refused, checkpoint_hold,
    checkpoint_catch, forecast_drift, bailout, empty_claims. A sid
    appears once per bucket however many attempts put it there;
    non-anomalous counts (applied closures, agreeing checks) carry no
    membership — nominate, never curate, and the dossier is the level
    2 read for any named sid.
    """
    response_attempts = 0
    validated_attempts = 0
    checks = 0
    checks_agree = 0
    checks_disagree = 0
    checks_na = 0
    unparsed_validated = 0
    held_attempts = 0
    drift_refused_attempts = 0
    override_attempts = 0
    rejected_attempts = 0
    checkpointed_attempts = 0
    checkpoint_hold_attempts = 0
    required_check_refused_attempts = 0
    required_check_override_attempts = 0
    forecast_attempts = 0
    forecast_drift_attempts = 0
    forecast_drift_paths = 0
    forecast_admitted_paths = 0
    forecast_entries = 0
    forecast_entries_touched = 0
    forecast_entries_untouched = 0
    bailout_sessions = 0
    sessions_with_response_attempt = 0
    closed_sessions = 0
    clarified_sessions = 0
    clarification_epoch_sessions = 0
    linkage_attempts = 0
    linkage_kinds: dict[str, int] = {}
    linkage_points: dict[str, int] = {}
    claims_declared = 0
    empty_claims_validated = 0
    checkpoint_catch_attempts = 0
    basis_checks: dict[str, int] = {}
    basis_agree: dict[str, int] = {}
    members: dict[str, set] = {key: set() for key in (
        "held", "checks_disagree", "unparsed", "drift_refused",
        "rejected", "required_check_refused", "checkpoint_hold",
        "checkpoint_catch", "forecast_drift", "bailout", "empty_claims",
    )}

    for record in sessions:
        sid = record["session_id"]
        had_response_attempt = False
        for attempt in record["attempts"]:
            linkage = _attempt_linkage(attempt)
            if linkage is not None:
                # The board 65 rollup (docstring above): every stamped
                # attempt counts, by kind and by placement, values
                # verbatim, "unspecified" the honest bucket for a
                # stamp that omits the field.
                linkage_attempts += 1
                kind = linkage.get("kind")
                kind_key = (kind if isinstance(kind, str) and kind
                            else "unspecified")
                linkage_kinds[kind_key] = linkage_kinds.get(kind_key, 0) + 1
                point = _linkage_point(linkage)
                point_key = point if point is not None else "unspecified"
                linkage_points[point_key] = (
                    linkage_points.get(point_key, 0) + 1)
            if not is_response_attempt(attempt):
                continue
            had_response_attempt = True
            response_attempts += 1
            outcome = attempt.get("outcome")
            if outcome == "held":
                held_attempts += 1
                members["held"].add(sid)
            elif outcome == "scope-drift-refused":
                drift_refused_attempts += 1
                members["drift_refused"].add(sid)
            elif outcome == "rejected":
                rejected_attempts += 1
                members["rejected"].add(sid)
            elif outcome == "required-check-refused":
                # The step-15 superset gate's refusal (board 6 session
                # B; counted here since session D) — a count beside the
                # drift refusals, same species, different gate.
                required_check_refused_attempts += 1
                members["required_check_refused"].add(sid)
            if attempt.get("overridden_paths"):
                override_attempts += 1
            if attempt.get("required_check_overrides"):
                # Effective --allow-missing-required-check use — the
                # overridden_paths mirror in the gate's own unit (check
                # names). Absent on pre-session-B records; a truthy
                # check reads absence and [] the same honest way.
                required_check_override_attempts += 1
            if attempt.get("scope_kind") == FORECAST_SCOPE_KIND:
                # The write-forecast epoch (ADR-0015; docstring above
                # carries every definition). Post-epoch only: key
                # presence is epoch membership.
                forecast_attempts += 1
                forecast = [_scope_norm(e) for e in
                            (attempt.get("scope") or [])
                            if isinstance(e, str) and e.strip()]
                change_paths = {
                    _scope_norm(p) for p in
                    (attempt.get("change_paths") or [])
                    if isinstance(p, str) and p.strip()
                }
                drift = {p for p in change_paths
                         if not _forecast_covers(forecast, p)}
                if drift:
                    forecast_drift_attempts += 1
                    members["forecast_drift"].add(sid)
                forecast_drift_paths += len(drift)
                admitted = {_scope_norm(p) for p in
                            (attempt.get("overridden_paths") or [])
                            if isinstance(p, str) and p.strip()}
                forecast_admitted_paths += len(drift & admitted)
                if change_paths:
                    # Precision only over attempts that landed
                    # something: an empty change set measures nothing
                    # about forecast width (docstring).
                    entries = sorted(set(forecast))
                    touched = [e for e in entries
                               if any(e == "." or p == e
                                      or p.startswith(e + "/")
                                      for p in change_paths)]
                    forecast_entries += len(entries)
                    forecast_entries_touched += len(touched)
                    forecast_entries_untouched += (len(entries)
                                                   - len(touched))
            if not is_validated_attempt(attempt):
                continue
            validated_attempts += 1
            validation = attempt["validation"]
            # Claim coverage (board 44; docstring above): the promoted
            # claims map's size, and the empty-map count — validation
            # ran on this attempt, so an empty map is the §5.3
            # wasted-signal shape.
            claims_map = validation.get("claims")
            declared = len(claims_map) if isinstance(claims_map, dict) \
                else 0
            claims_declared += declared
            if declared == 0:
                empty_claims_validated += 1
                members["empty_claims"].add(sid)
            checkpoint = attempt.get("checkpoint")
            if isinstance(checkpoint, dict) \
                    and checkpoint.get("configured") is True:
                # The D4.2 denominator: validated attempts where a
                # blind checkpoint actually executed. Pre-epoch
                # attempts (no key) and known-zero stamps
                # (configured: false) both stay outside it.
                checkpointed_attempts += 1
                if checkpoint.get("state") == "HOLD":
                    # The stamp's own per-source state: the checkpoint
                    # objected (exit 1) or errored (exit 2), whatever
                    # the worker's verdict was.
                    checkpoint_hold_attempts += 1
                    members["checkpoint_hold"].add(sid)
                    if checkpoint.get("exit_code") == 1 \
                            and validation.get("exit_code") == 0:
                        # The CATCH (board 44; docstring above): the
                        # blind oracle objected (its own exit 1) while
                        # the worker's own script passed — the
                        # checkpoint saw what the worker missed. An
                        # errored checkpoint (exit 2) is a tooling
                        # fact, not a catch.
                        checkpoint_catch_attempts += 1
                        members["checkpoint_catch"].add(sid)
            if validation.get("reconciliation_parsed") is True:
                claim_verdict = validation.get("claim_verdict")
                if isinstance(claim_verdict, dict):
                    for check_name, entry in claim_verdict.items():
                        checks += 1
                        # The claim-basis split (board 44; docstring
                        # above): every check lands in exactly one
                        # basis bucket, agreement counted beside it.
                        agreement = (entry or {}).get("agreement")
                        basis = _claim_basis(validation, check_name,
                                             entry or {})
                        basis_checks[basis] = basis_checks.get(basis,
                                                               0) + 1
                        if agreement == "agree":
                            basis_agree[basis] = basis_agree.get(basis,
                                                                 0) + 1
                            checks_agree += 1
                        elif agreement == "disagree":
                            checks_disagree += 1
                            members["checks_disagree"].add(sid)
                        elif agreement == "n/a":
                            # The named residual: the §7.3 [n/a] tag —
                            # the claim made no prediction (untested,
                            # unknown) or the verdict was a skip or
                            # never recorded. Counted by its schema
                            # name; it stays inside agreement_rate's
                            # all-checks denominator (D2 — naming the
                            # bucket does not redefine the rate).
                            checks_na += 1
                        else:
                            # The schema's agreement vocabulary is
                            # exactly agree / disagree / n/a
                            # (telemetry-record.schema.json,
                            # claim_verdict.agreement); a value
                            # outside it gets no catch-all bucket —
                            # it counts in `checks` only, and is
                            # named here rather than silently left
                            # out of every per-value row.
                            _warn(f"record {record['session_id']}: "
                                  f"check {check_name!r} carries "
                                  f"unrecognized agreement "
                                  f"{agreement!r}; counted in checks "
                                  f"only")
            else:
                # A parse miss is a tooling fact, not worker
                # disagreement — its own share, NEVER folded into
                # agreement (D2).
                unparsed_validated += 1
                members["unparsed"].add(sid)
        if had_response_attempt:
            sessions_with_response_attempt += 1
        category = closure_category(record)
        if category is not None:
            closed_sessions += 1
            if category[0] == "bailout":
                bailout_sessions += 1
                members["bailout"].add(sid)
            stamp = _clarification_stamp(record)
            if stamp is not None:
                clarification_epoch_sessions += 1
                if isinstance(stamp.get("rounds"), int) and stamp["rounds"] >= 1:
                    clarified_sessions += 1

    return {
        "sessions": len(sessions),
        "closed_sessions": closed_sessions,
        "response_attempts": response_attempts,
        "validated_attempts": validated_attempts,
        "checks": checks,
        "checks_agree": checks_agree,
        "checks_disagree": checks_disagree,
        "checks_na": checks_na,
        # Denominator is ALL checks (D2) — n/a included, now visibly so
        # via the named count above.
        "agreement_rate": _rate(checks_agree, checks),
        "unparsed_validated_attempts": unparsed_validated,
        "unparsed_share": _rate(unparsed_validated, validated_attempts),
        "held_attempts": held_attempts,
        "hold_rate": _rate(held_attempts, validated_attempts),
        "drift_refused_attempts": drift_refused_attempts,
        "drift_refusal_rate": _rate(drift_refused_attempts, response_attempts),
        "override_attempts": override_attempts,
        "rejected_attempts": rejected_attempts,
        "claims_declared": claims_declared,
        "claims_per_validated_attempt": _rate(claims_declared,
                                              validated_attempts),
        "empty_claims_validated_attempts": empty_claims_validated,
        "checkpointed_attempts": checkpointed_attempts,
        "checkpoint_hold_attempts": checkpoint_hold_attempts,
        "checkpoint_hold_rate": _rate(checkpoint_hold_attempts,
                                      checkpointed_attempts),
        "checkpoint_catch_attempts": checkpoint_catch_attempts,
        "checkpoint_catch_rate": _rate(checkpoint_catch_attempts,
                                       checkpointed_attempts),
        "required_check_refused_attempts": required_check_refused_attempts,
        "required_check_override_attempts": required_check_override_attempts,
        "forecast_attempts": forecast_attempts,
        "forecast_drift_attempts": forecast_drift_attempts,
        "forecast_drift_rate": _rate(forecast_drift_attempts,
                                     forecast_attempts),
        "forecast_drift_paths": forecast_drift_paths,
        "forecast_admitted_paths": forecast_admitted_paths,
        "forecast_admission_rate": _rate(forecast_admitted_paths,
                                         forecast_drift_paths),
        "forecast_entries": forecast_entries,
        "forecast_entries_untouched": forecast_entries_untouched,
        "forecast_precision": _rate(forecast_entries_touched,
                                    forecast_entries),
        "bailout_sessions": bailout_sessions,
        "sessions_with_response_attempt": sessions_with_response_attempt,
        "bailout_rate": _rate(bailout_sessions,
                              sessions_with_response_attempt),
        "clarified_sessions": clarified_sessions,
        "clarification_epoch_sessions": clarification_epoch_sessions,
        "clarification_rate": _rate(clarified_sessions,
                                    clarification_epoch_sessions),
        "linkage": {
            "attempts": linkage_attempts,
            "kinds": dict(sorted(linkage_kinds.items())),
            "points": dict(sorted(linkage_points.items())),
        },
        "claim_basis": {
            basis: {
                "checks": count,
                "agree": basis_agree.get(basis, 0),
                "agreement_rate": _rate(basis_agree.get(basis, 0),
                                        count),
            }
            for basis, count in sorted(basis_checks.items())
        },
        "members": {bucket: sorted(sids)
                    for bucket, sids in members.items()},
    }


def compute_stats(telemetry_dir: Path, *, work_class: Optional[str] = None,
                  since: Optional[str] = None) -> dict:
    """Compute the full `bale stats` payload over claude/telemetry/.

    Filter semantics (D6):
    - `since` (ISO date string, inclusive) restricts membership to
      records whose created_at is on or after the date — compared
      lexicographically, exact for the schema's ISO 8601 UTC stamps.
    - `work_class` restricts the classed membership (the rate table,
      closure mix, churn, cross-checks, and the classed corpus totals)
      to sessions resolving to that class.

    Two row families deliberately sit outside the filters' reach, and
    the renderers say so:
    - **Corpus facts** — `records`, `parse_failures`,
      `filtered_record_versions`, the epoch row, and the coverage rows —
      describe the whole loaded corpus. A filtered view's "epoch" is the
      filter, which the filters echo already states; restating the
      corpus's true start under a filter keeps the row meaningful.
    - **Context counts** — read-only and crash-debris sessions — honor
      `since` (they are counts of sessions in the reported window) but
      not `work_class`, because excluded sessions are never classed.

    The membership pipeline, in order: load → since-window → exclude
    read-only and crash-debris (context/hygiene counts; D2's membership
    exclusions) → resolve work class → work_class filter. Everything
    classed is computed over what survives.

    Three board 44 surfaces ride the same filtered membership as the
    classes table (so both filters reach them the way they reach every
    rate):
    - **`packers`** — the per-packer cut of the claim-coverage
      aggregates (_class_row's docstring carries the definitions), one
      row per resolved packer identity (session_packer: the open-time
      stamp first, the feedback echo second, UNATTRIBUTED for neither):
      sessions, validated_attempts, claims_declared,
      claims_per_validated_attempt, empty_claims_validated_attempts.
      Packer identities bucket verbatim (honest rows).
    - **`doc_epochs`** — outcome counts per contract-doc-hash epoch,
      the read side that makes doc changes A/B-able (BALE.md §5.6
      names it as an intended use). Sessions bucket by the digest of
      their echoed provenance.contract_docs set (_doc_epoch_key; the
      full name→hash map is reported beside the digest so the key is
      an identifier, never the only record), with DOC_EPOCH_UNSTAMPED
      the honest bucket for records carrying no echo. Each row:
      first_created_at (so epochs order chronologically), sessions,
      closed_sessions, in_flight, the closure counts (applied /
      reverted / bailout / unlocked), applied_rate (applied over
      closed, None on zero), and contract_docs (the map, or None for
      the unstamped row). Counts only beyond the one rate — every
      other rate is derivable, and the renderer never owns the
      numbers.
    - **`members`** — the corpus-level half of the level 1 drill
      (per-class membership lives in each class row): sid lists for
      in_flight, read_only, crash_debris, the clarification
      cross-check's self_only / promoted_only disagreement sets, the
      forecast-departures smells (admitted_only / declared_only —
      sids of sessions with at least one such path), and
      bailed_with_pressure_none. Sorted, sid-granular, emitted beside
      the counts they compose — the existing cross_checks counts are
      unchanged.

    Returns a plain dict; `format_stats_json` in bale_report owns its
    key list as the consumer contract, and `format_stats_report` renders
    the same payload for humans.
    """
    records, parse_failures, filtered_versions = load_corpus(telemetry_dir)

    epoch = _epoch(records)
    coverage = {
        "closure_reason": _coverage_row(records, "closure_reason"),
        "clarification": _coverage_row(records, "clarification"),
        # The board 6 sub-epoch (v0.3.29, session D): the checkpoint
        # stamp's always-on-validated-attempts key, detected by
        # presence exactly like its two siblings — a record whose
        # validated attempts all predate session A lacks the key
        # everywhere and lands in records_lacking.
        "checkpoint": _coverage_row(records, "checkpoint"),
        # The write-forecast sub-epoch (ADR-0015, board 13 session B):
        # the scope_kind key bale stamps on every post-epoch attempt.
        # Detected by presence like its three siblings; the forecast
        # rows in _class_row read only inside this sub-epoch.
        "scope_kind": _coverage_row(records, "scope_kind"),
    }

    windowed = [r for r in records
                if since is None or r["created_at"] >= since]

    read_only = [r for r in windowed if is_read_only(r)]
    crash_debris = [r for r in windowed
                    if is_crash_debris(r) and not is_read_only(r)]
    membership = [r for r in windowed
                  if not is_read_only(r) and not is_crash_debris(r)]

    by_class: dict[str, list[dict]] = {}
    for record in membership:
        by_class.setdefault(session_work_class(record), []).append(record)
    if work_class is not None:
        by_class = {cls: sessions for cls, sessions in by_class.items()
                    if cls == work_class}
        membership = [r for sessions in by_class.values() for r in sessions]

    classes = {cls: _class_row(sessions)
               for cls, sessions in sorted(by_class.items())}

    # Closure mix over the classed membership: read-only and crash-debris
    # never appear here (their homes are the context and hygiene counts);
    # superseded-by-split parents DO, under their reason — that mix is
    # exactly where the split economics show (D2).
    closure_mix: dict = {"applied": 0, "reverted": 0, "bailout": 0,
                         "unlocked": {}}
    in_flight = 0
    in_flight_sids: set = set()
    rolled_back = 0
    re_applied = 0
    for record in membership:
        for attempt in record["attempts"]:
            if attempt.get("outcome") == "rolled-back":
                rolled_back += 1
            elif attempt.get("outcome") == "re-applied":
                re_applied += 1
        category = closure_category(record)
        if category is None:
            in_flight += 1
            in_flight_sids.add(record["session_id"])
            continue
        kind, reason = category
        if kind == "unlocked":
            closure_mix["unlocked"][reason] = (
                closure_mix["unlocked"].get(reason, 0) + 1)
        else:
            closure_mix[kind] += 1

    # Dual-stream cross-checks (D2, deliberately minimal at v1): the
    # self-reported stream is a calibration target, reported BESIDE the
    # mechanical rates, never blended into them.
    self_clar = {r["session_id"] for r in membership
                 if _self_reported_clarification(r)}
    promoted_clar = set()
    for record in membership:
        stamp = _clarification_stamp(record)
        if stamp is not None and isinstance(stamp.get("rounds"), int) \
                and stamp["rounds"] >= 1:
            promoted_clar.add(record["session_id"])
    # The departures-vs-admissions cross-check (ADR-0015 / design brief
    # I.5): the worker's self-declared forecast_departures against the
    # mechanically admitted overridden_paths, path-granular per
    # post-epoch response attempt, per-attempt set counts summed. An
    # admitted path with NO declared departure ("admitted_only") is the
    # ADR-0014 audit smell, now computed instead of eyeballed; a
    # declared path never admitted ("declared_only") is either refused
    # drift or a worker misjudging its own forecast — both worth eyes.
    # Self-reported beside mechanical, never blended (D2's posture).
    fd_declared = 0
    fd_admitted = 0
    fd_both = 0
    fd_admitted_only = 0
    fd_declared_only = 0
    fd_admitted_only_sids: set = set()
    fd_declared_only_sids: set = set()
    for record in membership:
        for attempt in record["attempts"]:
            if not is_response_attempt(attempt):
                continue
            if attempt.get("scope_kind") != FORECAST_SCOPE_KIND:
                continue
            declared = _departure_paths(attempt)
            admitted = {_scope_norm(p) for p in
                        (attempt.get("overridden_paths") or [])
                        if isinstance(p, str) and p.strip()}
            fd_declared += len(declared)
            fd_admitted += len(admitted)
            fd_both += len(declared & admitted)
            fd_admitted_only += len(admitted - declared)
            fd_declared_only += len(declared - admitted)
            # The corpus-level membership half (board 44): a session
            # with at least one smell path is named so the count
            # drills to its sids; the counts above stay path-granular
            # and unchanged.
            if admitted - declared:
                fd_admitted_only_sids.add(record["session_id"])
            if declared - admitted:
                fd_declared_only_sids.add(record["session_id"])

    pressure: dict[str, int] = {}
    bailed_with_none = 0
    bailed_with_none_sids: set = set()
    for record in membership:
        feedback = _latest_feedback(record)
        value = None
        if feedback is not None:
            reported = (feedback.get("self_reported") or {})
            candidate = reported.get("budget_pressure")
            if isinstance(candidate, str) and candidate:
                value = candidate
        bucket = value if value is not None else "unreported"
        pressure[bucket] = pressure.get(bucket, 0) + 1
        category = closure_category(record)
        if category is not None and category[0] == "bailout" \
                and value == "none":
            bailed_with_none += 1
            bailed_with_none_sids.add(record["session_id"])

    # The per-packer claim-coverage cut (board 44; the compute_stats
    # docstring carries the surface, _class_row's docstring the
    # definitions). Same filtered membership as the classes table.
    packers: dict[str, dict] = {}
    for record in membership:
        row = packers.setdefault(session_packer(record), {
            "sessions": 0,
            "validated_attempts": 0,
            "claims_declared": 0,
            "empty_claims_validated_attempts": 0,
        })
        row["sessions"] += 1
        for attempt in record["attempts"]:
            if not is_validated_attempt(attempt):
                continue
            row["validated_attempts"] += 1
            claims_map = attempt["validation"].get("claims")
            declared_n = len(claims_map) \
                if isinstance(claims_map, dict) else 0
            row["claims_declared"] += declared_n
            if declared_n == 0:
                row["empty_claims_validated_attempts"] += 1
    for row in packers.values():
        row["claims_per_validated_attempt"] = _rate(
            row["claims_declared"], row["validated_attempts"])
    packers = dict(sorted(packers.items()))

    # Outcome counts per contract-doc-hash epoch (board 44; the
    # compute_stats docstring carries the surface). Same filtered
    # membership; sessions bucket by their echoed doc-hash set.
    doc_epochs: dict[str, dict] = {}
    for record in membership:
        docs = _session_contract_docs(record)
        key = _doc_epoch_key(docs)
        row = doc_epochs.setdefault(key, {
            "first_created_at": record["created_at"],
            "sessions": 0,
            "closed_sessions": 0,
            "in_flight": 0,
            "applied": 0,
            "reverted": 0,
            "bailout": 0,
            "unlocked": 0,
            "contract_docs": docs,
        })
        row["first_created_at"] = min(row["first_created_at"],
                                      record["created_at"])
        row["sessions"] += 1
        category = closure_category(record)
        if category is None:
            row["in_flight"] += 1
        else:
            row["closed_sessions"] += 1
            row[category[0]] += 1
    for row in doc_epochs.values():
        row["applied_rate"] = _rate(row["applied"],
                                    row["closed_sessions"])
    doc_epochs = dict(sorted(
        doc_epochs.items(),
        key=lambda item: (item[1]["first_created_at"], item[0])))

    total_response = sum(row["response_attempts"] for row in classes.values())
    total_validated = sum(row["validated_attempts"]
                          for row in classes.values())
    total_checks = sum(row["checks"] for row in classes.values())

    return {
        "epoch": epoch,
        "coverage": coverage,
        "filters": {"work_class": work_class, "since": since},
        "corpus": {
            "records": len(records),
            "parse_failures": len(parse_failures),
            "filtered_record_versions": len(filtered_versions),
            "read_only_sessions": len(read_only),
            "crash_debris_sessions": len(crash_debris),
            "sessions": len(membership),
            "in_flight_sessions": in_flight,
            "response_attempts": total_response,
            "validated_attempts": total_validated,
            "checks": total_checks,
        },
        "classes": classes,
        "closure_mix": closure_mix,
        "churn": {"rolled_back": rolled_back, "re_applied": re_applied},
        "cross_checks": {
            "clarification": {
                "self_reported_sessions": len(self_clar),
                "promoted_sessions": len(promoted_clar),
                "both": len(self_clar & promoted_clar),
                "self_only": len(self_clar - promoted_clar),
                "promoted_only": len(promoted_clar - self_clar),
            },
            "budget": {
                "pressure": dict(sorted(pressure.items())),
                "bailed_with_pressure_none": bailed_with_none,
            },
            "forecast_departures": {
                "declared_paths": fd_declared,
                "admitted_paths": fd_admitted,
                "both": fd_both,
                "admitted_only": fd_admitted_only,
                "declared_only": fd_declared_only,
            },
        },
        "packers": packers,
        "doc_epochs": doc_epochs,
        "members": {
            "in_flight": sorted(in_flight_sids),
            "read_only": sorted(r["session_id"] for r in read_only),
            "crash_debris": sorted(r["session_id"]
                                   for r in crash_debris),
            "clarification_self_only": sorted(self_clar - promoted_clar),
            "clarification_promoted_only": sorted(
                promoted_clar - self_clar),
            "forecast_admitted_only": sorted(fd_admitted_only_sids),
            "forecast_declared_only": sorted(fd_declared_only_sids),
            "bailed_with_pressure_none": sorted(bailed_with_none_sids),
        },
    }


# ---------------------------------------------------------------------------
# The session dossier (board 44, level 2)
# ---------------------------------------------------------------------------

def _dossier_attempt(attempt: dict) -> dict:
    """One attempt's dossier view: the record's own facts projected
    with light, definition-reusing annotation — nothing here is
    invented, and every value is re-derivable from the raw record with
    jq (PLANNER.md §17: the read side never owns the numbers).

    Key-presence semantics survive the projection: `checkpoint`,
    `clarification`, `diagnostics`, `provenance`, `superseded_by`, and
    `linkage` are None when the record carries none — pre-epoch
    unknown or not-a-carrier, per each field's own doctrine — and the
    claim/verdict `checks` rows carry the resolved `claim_basis`
    (UNSPECIFIED for bare-string claims). `forecast_drift_paths` is
    computed for post-epoch response attempts (the drift gate's own
    containment, the same read the class rows use) and None
    otherwise — pre-epoch scope is the conflated include set and
    drift against it would lie.
    """
    validation = attempt.get("validation")
    validation_view = None
    if isinstance(validation, dict):
        checks = []
        claim_verdict = validation.get("claim_verdict")
        if isinstance(claim_verdict, dict):
            for check_name in sorted(claim_verdict):
                entry = claim_verdict[check_name] or {}
                checks.append({
                    "check": check_name,
                    "claim": entry.get("claim"),
                    "verdict": entry.get("verdict"),
                    "agreement": entry.get("agreement"),
                    "claim_basis": _claim_basis(validation, check_name,
                                                entry),
                })
        claims_map = validation.get("claims")
        validation_view = {
            "state": validation.get("state"),
            "exit_code": validation.get("exit_code"),
            "reconciliation_parsed":
                validation.get("reconciliation_parsed"),
            "claims_declared": (len(claims_map)
                                if isinstance(claims_map, dict) else 0),
            "checks": checks,
        }

    drift_paths = None
    if is_response_attempt(attempt) \
            and attempt.get("scope_kind") == FORECAST_SCOPE_KIND:
        forecast = [_scope_norm(e) for e in (attempt.get("scope") or [])
                    if isinstance(e, str) and e.strip()]
        change_paths = {_scope_norm(p) for p in
                        (attempt.get("change_paths") or [])
                        if isinstance(p, str) and p.strip()}
        drift_paths = sorted(p for p in change_paths
                             if not _forecast_covers(forecast, p))

    checkpoint = attempt.get("checkpoint")
    clarification = attempt.get("clarification")
    diagnostics = attempt.get("diagnostics")
    superseded_by = attempt.get("superseded_by")
    return {
        "at": attempt.get("at"),
        "command": attempt.get("command"),
        "outcome": attempt.get("outcome"),
        "closure_reason": attempt.get("closure_reason"),
        "tarball": attempt.get("tarball"),
        "scope_kind": attempt.get("scope_kind"),
        "scope": list(attempt.get("scope") or []),
        "change_paths": list(attempt.get("change_paths") or []),
        "overridden_paths": list(attempt.get("overridden_paths") or []),
        "required_check_overrides":
            list(attempt.get("required_check_overrides") or []),
        "forecast_drift_paths": drift_paths,
        "validation": validation_view,
        "checkpoint": (checkpoint if isinstance(checkpoint, dict)
                       else None),
        "linkage": _attempt_linkage(attempt),
        "clarification": (clarification
                          if isinstance(clarification, dict) else None),
        "diagnostics": (diagnostics
                        if isinstance(diagnostics, dict) else None),
        "provenance": _attempt_provenance_stamp(attempt),
        "superseded_by": (superseded_by
                          if isinstance(superseded_by, str) else None),
        "log": attempt.get("log"),
    }


def compute_session_dossier(telemetry_dir: Path, sid: str) -> dict:
    """Compute the board 44 level 2 read: one sid rendered whole.

    The dossier replaces the hand-jq walk across the record's surfaces
    with one computed view over `claude/telemetry/` — the same one
    substrate, and nothing else (D1: never `.bale/`): the record's
    envelope and status, every attempt with its claim/verdict pairs,
    checkpoint stamp, clarification stamp (rounds and preserved-record
    summaries — the promoted image of `.bale/clarifications/<sid>/`,
    which is how those records reach a fresh clone), bailout
    diagnostics, and the lineage edges the corpus records — so a
    HOLD-to-retry arc reads end to end. Read-only, stateless; the
    renderers in bale_report project it and never own the numbers
    (PLANNER.md §17).

    Returns a plain dict, always: `found` False when no record under
    the sid parses (with `parse_failure` True when a file exists but
    was skipped by the loader — named on stderr as ever), so the
    caller renders an honest miss instead of crashing. On a hit:

    - `record` — envelope facts (record_version, created_at,
      updated_at, outcome) plus the resolved `work_class` and `packer`
      (stamp-first, the session_* resolvers) and status flags:
      `in_flight`, `closure` ({category, unlock_reason} or None),
      `read_only`, `crash_debris`.
    - `attempts` — one _dossier_attempt view per attempt, in order.
    - `lineage` — the cross-record edges recoverable from the corpus:
      `superseded_by` (this record's own closure stamp),
      `superseded_from` (sids whose stamp names this one), and the
      corrects pair — `corrects` (read tolerantly from the record or
      any attempt; the response manifest's field is NOT promoted into
      telemetry today, so this is None on every bale-written record —
      an honest unrecorded, not a known "no correction"; the write-side
      promotion is proposed, and this reader lights up the day it
      lands) and `corrected_by` (the tolerant converse scan).

    The full-corpus load is deliberate: lineage edges live on OTHER
    records, so the dossier reads the corpus the aggregation reads.
    """
    records, parse_failures, filtered = load_corpus(telemetry_dir)
    record = next((r for r in records if r["session_id"] == sid), None)
    if record is None:
        return {
            "session_id": sid,
            "found": False,
            "parse_failure": f"{sid}.json" in parse_failures,
            "filtered_record_version": f"{sid}.json" in filtered,
        }

    def _record_corrects(r: dict) -> Optional[str]:
        # Tolerant read at both depths (docstring): the field is not
        # promoted today; a record carrying it anyway resolves.
        value = r.get("corrects")
        if isinstance(value, str) and value:
            return value
        for a in r["attempts"]:
            value = a.get("corrects")
            if isinstance(value, str) and value:
                return value
        return None

    superseded_by = None
    for attempt in reversed(record["attempts"]):
        candidate = attempt.get("superseded_by")
        if isinstance(candidate, str) and candidate:
            superseded_by = candidate
            break
    superseded_from = sorted(
        r["session_id"] for r in records if r["session_id"] != sid
        and any(a.get("superseded_by") == sid for a in r["attempts"]))
    corrected_by = sorted(
        r["session_id"] for r in records if r["session_id"] != sid
        and _record_corrects(r) == sid)

    closure = closure_category(record)
    return {
        "session_id": sid,
        "found": True,
        "record": {
            "record_version": record["record_version"],
            "created_at": record["created_at"],
            "updated_at": record.get("updated_at"),
            "outcome": record["outcome"],
            "work_class": session_work_class(record),
            "packer": session_packer(record),
            "in_flight": closure is None,
            "closure": (None if closure is None
                        else {"category": closure[0],
                              "unlock_reason": closure[1]}),
            "read_only": is_read_only(record),
            "crash_debris": is_crash_debris(record),
        },
        "attempts": [_dossier_attempt(a) for a in record["attempts"]],
        "lineage": {
            "superseded_by": superseded_by,
            "superseded_from": superseded_from,
            "corrects": _record_corrects(record),
            "corrected_by": corrected_by,
        },
    }
