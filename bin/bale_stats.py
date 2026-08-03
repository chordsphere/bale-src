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
plain-dict stats payload both renderers consume; the loaders and
classifiers below it are importable for tests. The payload's *key list*
as a consumer contract is owned by the `format_stats_json` docstring in
`bin/bale_report.py` (one-home rule) — this module's docstrings describe
semantics, not the wire key set.
"""

from __future__ import annotations

import json
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
# lock-state claim.
IN_FLIGHT_OUTCOMES = frozenset({"held", "scope-drift-refused", "rejected"})

# The work_class vocabulary the pack surface stamps (BALE.md §7), plus the
# ledger's own bucket for sessions with no feedback-bearing attempt.
# Aggregation buckets by the recorded value verbatim — an unexpected value
# forms its own honest row rather than being dropped or coerced — so this
# tuple is the *known* vocabulary (it drives the --work-class choices in
# bin/bale), not a filter.
WORK_CLASSES = ("code", "doc", "contract-doc", "meta", "mixed")
UNCLASSED = "unclassed"


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


def session_work_class(record: dict) -> str:
    """Resolve the session's work class (D2).

    The value on the session's LATEST feedback-bearing attempt
    (feedback.mechanical.provenance.work_class); sessions with none —
    pure unlock closures, rejected-only — fall in the `unclassed`
    bucket, reported, never silently dropped or guessed. Attempt-level
    rates inherit this session-level resolution, which is what classes
    a rejected first attempt of a session whose later attempts carry
    the class.
    """
    for attempt in reversed(record["attempts"]):
        feedback = attempt.get("feedback")
        if not isinstance(feedback, dict):
            continue
        provenance = (feedback.get("mechanical") or {}).get("provenance")
        if isinstance(provenance, dict):
            work_class = provenance.get("work_class")
            if isinstance(work_class, str) and work_class:
                return work_class
    return UNCLASSED


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


def _self_reported_clarification(record: dict) -> bool:
    """Cross-check 1's self-reported side: any attempt whose
    feedback.mechanical.linkage.kind == "clarification"."""
    for attempt in record["attempts"]:
        feedback = attempt.get("feedback")
        if not isinstance(feedback, dict):
            continue
        linkage = (feedback.get("mechanical") or {}).get("linkage")
        if isinstance(linkage, dict) and linkage.get("kind") == "clarification":
            return True
    return False


def _rate(numerator: int, denominator: int) -> Optional[float]:
    """A rate with its honesty rule: None on a zero denominator."""
    if denominator == 0:
        return None
    return numerator / denominator


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
    bailout_sessions = 0
    sessions_with_response_attempt = 0
    closed_sessions = 0
    clarified_sessions = 0
    clarification_epoch_sessions = 0

    for record in sessions:
        had_response_attempt = False
        for attempt in record["attempts"]:
            if not is_response_attempt(attempt):
                continue
            had_response_attempt = True
            response_attempts += 1
            outcome = attempt.get("outcome")
            if outcome == "held":
                held_attempts += 1
            elif outcome == "scope-drift-refused":
                drift_refused_attempts += 1
            elif outcome == "rejected":
                rejected_attempts += 1
            if attempt.get("overridden_paths"):
                override_attempts += 1
            if not is_validated_attempt(attempt):
                continue
            validated_attempts += 1
            validation = attempt["validation"]
            if validation.get("reconciliation_parsed") is True:
                claim_verdict = validation.get("claim_verdict")
                if isinstance(claim_verdict, dict):
                    for check_name, entry in claim_verdict.items():
                        checks += 1
                        agreement = (entry or {}).get("agreement")
                        if agreement == "agree":
                            checks_agree += 1
                        elif agreement == "disagree":
                            checks_disagree += 1
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
        if had_response_attempt:
            sessions_with_response_attempt += 1
        category = closure_category(record)
        if category is not None:
            closed_sessions += 1
            if category[0] == "bailout":
                bailout_sessions += 1
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
        "bailout_sessions": bailout_sessions,
        "sessions_with_response_attempt": sessions_with_response_attempt,
        "bailout_rate": _rate(bailout_sessions,
                              sessions_with_response_attempt),
        "clarified_sessions": clarified_sessions,
        "clarification_epoch_sessions": clarification_epoch_sessions,
        "clarification_rate": _rate(clarified_sessions,
                                    clarification_epoch_sessions),
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

    Returns a plain dict; `format_stats_json` in bale_report owns its
    key list as the consumer contract, and `format_stats_report` renders
    the same payload for humans.
    """
    records, parse_failures, filtered_versions = load_corpus(telemetry_dir)

    epoch = _epoch(records)
    coverage = {
        "closure_reason": _coverage_row(records, "closure_reason"),
        "clarification": _coverage_row(records, "clarification"),
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
    pressure: dict[str, int] = {}
    bailed_with_none = 0
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
        },
    }
