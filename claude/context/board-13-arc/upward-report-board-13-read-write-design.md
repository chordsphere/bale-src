# Upward report — board-13 read-vs-write design arc — 2026-08-07

Session `2026-08-07-board-13-read-write-design-003`, read-only,
`resolved_scope: []`. Reporting to the master desk
(`2026-08-07-continue-plan-001`) per the board-5/6 precedent.
Partitioned landed / ratified / escalated / on-watch.

## Landed

Nothing in-tree — read-only session, by design and by gate. Four
prose artifacts delivered as files: the design brief (revA,
partitioned), the implementation decomposition (revA, three sessions
plus explicit non-sessions), the ADR draft (supersedes-0007 shape,
number placeholder), and this report. notes.md relayed alongside per
standing style.

## Ratified at this level

All within the chat-ratified board-13 constraint; contestable at
review:

- **Surface:** `--write PATH...` as the forecast family; requires ≥1
  path; contradicts `--read-only`; entries name existing paths
  (ADR-0014's rule held on both families). Absent `--write`, the
  forecast defaults to the resolved include set — separation is
  opt-in per pack, and untouched workflows keep today's behavior
  byte-for-byte. Wizard: one follow-up on the lands-changes branch,
  Enter = same-as-includes, so the cold-start pack (evidence 37)
  needs no new understanding.
- **Record/stamp:** `scope.json` and `resolved_scope` reinterpreted
  as the forecast — same file, same key, same shapes, one source
  preserved, zero new required keys. Transition safety: old open
  sessions read as over-forecasts (conservative direction),
  self-clearing, no migration session.
- **Gates:** pack-time disjointness intersects forecasts only;
  apply-time sibling collision is the one reserved mechanical
  refusal (no override; admission never crosses a sibling's
  forecast); own-forecast drift keeps v0.3.10/ADR-0014 mechanics
  verbatim with the enforced set re-based and the doctrine
  generalized to modified files. Firing conditions named per
  evidence 42 in brief I.3, declines included.
- **Read-only subsumption:** `--read-only` = empty forecast, flag
  survives as the spelling; sweep, accept-default, banner, and
  `closed-read-only` inference untouched because `[]`'s meaning is
  unchanged. Board 24's slice subsumed.
- **Ledger:** `scope`/`change_paths`/`overridden_paths` carry the
  grading unchanged; `scope_kind` epoch key (fourth application of
  the disambiguation doctrine); stats rows for forecast drift,
  admission, and precision — drift = forecasts too narrow, precision
  loss = too wide, both packer-side signals.
- **Ordering:** A (pack surface + record + ADR) → B (telemetry epoch
  + stats), serialized on a real dependency (epoch must postdate the
  record change) and on shared-file contention; C (contract docs)
  after E1 ratifies, concurrently with B as the first deliberate
  post-separation concurrent pair.

## Escalated (ratify before any implementation pack is authored)

- **E1** — CLAUDE.md §6 / TARBALL.md §3.2, §3.4 contract revisions
  (lane rule generalized to modified files; flag table; doctrine).
- **E2** — response-manifest schema addition
  `feedback.forecast_departures` (§5-class, additive-optional).
- **E3** — blindness semantics fork: covering refusal re-bases to
  the forecast; recommended additional read-side refusal when
  includes would ship the oracle's bytes; the choice keys on
  board-6's contract meaning.
- **E4** — ADR-0007 status flip to Superseded (rationale in the
  draft's Notes: the decision text, not a forecast, is overturned —
  the ADR-0014 stand-beside precedent doesn't fit).
- **E5** — the design as a whole; implementation packs wait on it.

## Questions carried up

- The §5 execution-context manifest contract's text was not in
  context; the design determines its motivating cost dissolves
  either way, but confirming or amending wording needs the wording
  (brief Q1).
- Next ADR number / INDEX state (Q2); whether the registry should
  persist the read set now for staleness-watching or wait for data
  (Q3); status-rendering depth preference (Q4).

## On-watch

- **Read-staleness** (brief I.6): the one protection the conflation
  gave for free and the separation deliberately spends. Clobber-proof
  by gates; semantically backstopped by post-merge validation and
  review; ledger-watchable once epochs stamp. Remedy if it clusters:
  a data-gated pack-time warning, never a refusal.
- **Forecast precision** as a new longitudinal rate: worth watching
  from the first post-epoch sittings to calibrate how forecasts get
  drawn.
- **One-apply-behind:** session A itself packs and lands under the
  old conflated model — expect one final broad lock while it is
  open.
