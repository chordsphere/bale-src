# notes.md — 2026-08-07-board-13-read-write-design-003

Read-only design session; nothing lands. Four artifacts delivered as
files: design brief revA, implementation decomposition revA, ADR
draft, upward report. This file relays to the master desk per
standing style.

## What I actually did

Read the manifest, CLAUDE.md, the brief; then ADRs 0006/0007/0014,
the request-manifest and telemetry schemas, BALE.md §5, §7.1–§7.6,
§8.1, §8.9, §8.10, §11, TARBALL.md §3.2/§3.4/§5.2, DOCS.md §5/§7,
and targeted code: `persist_pack_session`, `persist_session_scope`,
`read_session_scope`, the pack wizard's session-shape exchange, and
apply's step-7/step-14 gate sites. Did not read: bale_config,
bale_report, bale_stats, bale_rollback, bale_staging, bale_validate,
_bale_toml, or most of bin/bale — the brief licensed selective
drilling and nothing in the design turned on them beyond what BALE.md
already specifies.

## The finding that shaped the design

The conflation has exactly one write site: `persist_pack_session`
hands the resolved include set to `persist_session_scope`, and every
consumer — both ADR-0007 gates, the drift gate, the `resolved_scope`
stamp, the sweep, the `closed-read-only` inference, telemetry's
`scope` field — reads that one record through shared helpers. So the
separation is a change to what pack *writes*, not to what anything
*reads*: same file, same key, same `[]`/missing semantics, and the
old-open-session transition falls out conservative (an include set
read as a forecast over-locks, never under-locks). That's why the
decomposition is three sessions and not six, and why there is no
migration session.

## Surprises and uncertainties

- **The blindness fork (E3) was genuinely not prejudged by the
  constraint.** Once reads stop gating, a generous include can ship
  the checkpoint's bytes to the entity it grades while every gate
  passes clean. I recommended a read-side refusal but the answer
  depends on what board-6 meant by "blind," which I can't settle
  from here.
- **Read-staleness is the real price** and I want it named louder
  than a consequences bullet, so it has its own section (brief I.6)
  and an on-watch entry. Today's model protects read freshness by
  accident; the separation spends that protection deliberately. The
  backstops (gate-guaranteed no-clobber, post-merge validation,
  review) are real but they catch the failure later than the lock
  did.
- **The §5 execution-context contract**: not in context. I designed
  around it (its motivating cost dissolves under separation either
  way) and flagged the wording question upward rather than guessing
  at text I haven't read (brief Q1). If the intent was for me to
  find it in the shipped docs — I searched; nothing shipped carries
  it by that name.
- **Uncertain, flagged in the brief:** whether the desk wants the
  read set persisted registry-side now (Q3) and how much status
  should render (Q4). Defaults chosen lean minimal.

## Proposals

- After E1–E5 ratify: author the session-A brief first
  (decomposition has the seam and scope hints; any planner-side
  slots per TARBALL.md §3.4's placeholder convention).
- Run B and C concurrently as the first deliberate post-separation
  concurrent pair — cheap and diagnostic (decomposition, session C's
  contest point).
- Watch forecast precision from the first post-epoch sittings; it's
  the new calibration signal and it starts accruing immediately.
