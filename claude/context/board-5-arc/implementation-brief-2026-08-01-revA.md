# Board 5 — bale stats / trust ledger implementation brief (rev A, 2026-08-01)

Authored in the read-only design session
`2026-08-01-board-5-ledger-design-004` against the request's shipped
tree. Every corpus claim below was computed against the 58 records
under `context/claude/telemetry/` this session, not recalled. This
brief is the ratification candidate; on ratification it ships
verbatim via `--readme-file` into the implementation sessions
proposed in D8.

Ratified constraints honored throughout and not re-argued here:
dual-stream weighting (mechanical is the substrate; self-reported is
a calibration target), mechanize-shape/judgment-as-prose, one-home
rendering in `bale_report`, stream discipline, additive status json,
closure-as-recorded-event, and read-only detection keyed on
`closure_reason`, never on scope.

## D0. Decisions at a glance

| # | Question | Decision |
|---|----------|----------|
| D1 | Transient inputs | Promote at the event: bailout attempts embed `diagnostics` verbatim; every post-epoch closing event stamps a bale-computed `clarification` summary read from `.bale/clarifications/<sid>/` at close time. `bale stats` reads `claude/telemetry/` only — never `.bale/` |
| D2 | Rate definitions | Attempt/session unit model with explicit denominators per rate; work_class resolved from the latest feedback-bearing attempt, `unclassed` bucket otherwise; read-only and crash-debris excluded from trust rates and reported as context rows |
| D3 | Drift-refusal semantics | Attempt-level mechanical event; rate over response attempts; overrides counted separately; §8.9 sentence amended (verbatim text in D3) |
| D4 | Reverse lineage | Parent's superseded-by-split closure attempt gains additive `superseded_by: <child-sid>`, stamped by pack at the close it already writes. No post-hoc appends by apply; no backfill |
| D5 | Commit cadence / guard | Stats reads the filesystem, so no functional coupling to commit timing; prompt commits remain the durability discipline. Rollback's dirty-tree guard disregards *untracked* paths under `claude/telemetry/` only |
| D6 | Command surface | `bale stats [--work-class CLS] [--since DATE] [--json]`, read-only, exits 0 on successful read. Aggregation in new sibling `bin/bale_stats.py`; rendering (human + json) in `bale_report`; `format_stats_json`'s docstring owns the key list |
| D7 | Riders | Bailout banner telemetry row; rollback guard change; §8.9 sentence fold-in; schema additive fields |
| D8 | Split | Two serialized sessions: A = telemetry promotion + guard + riders; B = `bale stats` + fixture corpus + the deferred HOLD E2E riding whichever session owns the E2E harness touchpoints (A; see D8) |

## D1. Transient inputs: promote at the event

The charter says the ledger aggregates diagnostics, clarifications,
and telemetry. Only telemetry is tracked. The three options weighed:

**Read-if-present with honest absent-input reporting — rejected as
the primary path.** The disqualifier is not the reporting, which is
fine, but that the same command would compute *different rates on
different checkouts* of the same repo. A fresh clone has no `.bale/`;
the original machine does. The ledger's entire value is being the
trustworthy substrate autonomy grants are judged against; an input
that varies by checkout poisons every rate it feeds, and an
"inputs were absent" footnote does not un-poison the number above it.

**Promote the files themselves to the tracked side — rejected.**
`.bale/` is gitignored by construction (BALE.md §7.1 step 6) and
transient by convention; moving clarification manifests or
diagnostics files wholesale reverses that architecture for marginal
gain, and full clarification manifests carry request prose the ledger
has no use for. It also creates a second tracked telemetry home,
against the one-file-per-sid shape §8.9 already established.

**Promote key fields into the telemetry record at the event —
chosen.** The record already embeds the feedback block verbatim; the
precedent extends naturally:

- **Bailout.** The bailout apply-close (`_apply_bailout`) already
  writes a telemetry attempt with outcome `bailout` and already holds
  the parsed, schema-validated diagnostics in hand (it validated them
  two steps earlier). The attempt gains an additive
  `diagnostics` key (`object|null`): the diagnostics.json content
  verbatim, symmetric with `feedback`. The bounded envelope
  (one-paragraph narrative, verdict lists) is small; verbatim beats a
  lossy summary, exactly as it did for feedback. `.bale/sessions/<sid>/`
  preservation is unchanged — it remains the local, human-inspectable
  copy the next handoff session chases.
- **Clarification.** §8.10.2's "a clarification writes no telemetry
  record" stays true *at clarification time* — the session is
  suspended, not closed, and a record there would be a closure claim.
  Instead, every **closing** event (apply/retry terminal outcomes,
  and unlock) stamps an additive `clarification` key on its attempt,
  computed by bale from `.bale/clarifications/<sid>/` at close time:
  `{"rounds": N, "records": [{"n": NNN, "at": ..., "blocking_questions": K}, ...]}`,
  and `{"rounds": 0, "records": []}` when the directory is absent.
  The always-stamp rule matters: post-epoch, key presence with
  `rounds: 0` means *known zero*; key absence means *pre-epoch
  unknown*. That is the `reconciliation_parsed` disambiguation
  doctrine applied to a new field — the ledger must never conflate
  "no clarifications" with "no data."
  Timing is safe under the solo-project assumption (BALE.md §3.5):
  the clarification directory outlives the session by design
  (§8.10.2 step 3) and the close happens on the machine that holds it.
  The residual loss — a clarified session whose close happens on a
  different checkout — is accepted and self-announcing (the stamp
  reads `rounds: 0` on that checkout's honest view).

**Clone / fresh-checkout story:** everything `bale stats` consumes is
under tracked `claude/telemetry/`; a fresh clone computes the same
rates as the original machine, minus only records not yet committed
there (D5). `.bale/` keeps its role as transient local enrichment
for humans, never a stats input.

Schema impact (all additive; `record_version` stays 1; descriptions
updated in `telemetry-record.schema.json`):
`attempts[].diagnostics`, `attempts[].clarification`,
`attempts[].superseded_by` (D4).

## D2. The unit model and the rates

### Units

- **session** — one record file (one sid).
- **response attempt** — an `attempts[]` entry with `command` ∈
  {`apply`, `retry`}: a response was processed. Excludes `unlock`,
  `pack`, and `rollback` events.
- **validated attempt** — a response attempt with `validation`
  non-null. (Drift-refused, rejected, and bailout attempts are
  response attempts but not validated attempts.)
- **check** — one `claim_verdict` entry on a validated attempt whose
  `reconciliation_parsed` is true.
- **closed session** — latest outcome ∈ {`applied`, `reverted`,
  `bailout`, `unlocked`, `rolled-back`, `re-applied`} (the last two
  are post-close history on an applied close). Latest outcome ∈
  {`held`, `scope-drift-refused`, `rejected`} = **in-flight**,
  reported as a count and excluded from closure mix. Stats reads only
  the corpus, never the `.bale/` registry — in-flight is the corpus's
  honest view, not a lock-state claim.

### work_class resolution

The class lives in `feedback.mechanical.provenance.work_class` and is
present on every attempt that carried a validated-enough manifest
(verified: all 49 applied, all held, and both drift-refused attempts
in the corpus carry it; the one rejected attempt and all 9
unlock/pack closures do not). Resolution: a session's class is the
value on its **latest feedback-bearing attempt**; sessions with none
(pure unlock closures, rejected-only) fall in an **`unclassed`**
bucket, reported, never silently dropped or guessed. Attempt-level
rates inherit the session's resolved class (this classes the rejected
first attempt of a session whose later attempts carry the class —
the `craft-tool-v1-007` shape in the corpus).

### Membership exclusions, each with rationale

- **Read-only sessions** — any attempt with
  `closure_reason == "closed-read-only"` (never scope `[]`; the
  overload is real in the corpus: pre-ADR-0007 records also read
  `[]`). Excluded from every trust rate: they land nothing by
  construction, so there is nothing to be calibrated on. Reported as
  a corpus-context count (7 in today's corpus).
- **crash-debris** — excluded from rates, counted in a hygiene row.
  None in today's corpus; the enum exists.
- **Rejected attempts** — counted (mechanical friction) but excluded
  from claim/verdict and HOLD denominators: no validation ran, so
  their absence from those rates is fact, not forgiveness.
- **Rolled-back sessions** — the applied attempt **stays** in every
  mechanical denominator: the claims, verdicts, and PASS were real
  events. The rollback itself lands in a post-close-churn row
  (`rolled-back` / `re-applied` counts). v1 deliberately does not
  reinterpret a rollback as a defect signal — a rollback can be
  strategic — and equally does not hide it. Whether post-merge
  reversal becomes a first-class defect rate is a future board's
  question, raised when the churn row has data.
- **Superseded-by-split parents** — included in closure mix under
  their reason (that mix is exactly where the split economics show);
  their zero landed work is already honest in every other rate.

### The rates, per class

| Rate | Numerator | Denominator |
|------|-----------|-------------|
| claim/verdict agreement | checks with `agreement == "agree"` (disagree count also reported) | all checks — validated attempts with `reconciliation_parsed` true, superseded HOLD attempts included (attempt history is the point) |
| unparsed-reconciliation share | validated attempts with `reconciliation_parsed` false | validated attempts — **never** folded into agreement; a parse miss is a tooling fact, not worker disagreement |
| HOLD rate | attempts with outcome `held` | validated attempts |
| drift-refusal rate | attempts with outcome `scope-drift-refused` | response attempts (refusal precedes validation, so the wider base) |
| override incidence | attempts with `overridden_paths ≠ []` | reported as a count beside drift refusals, not a rate — an override is an operator act, recorded because refusals and overrides are mechanical-stream telemetry (ratified 2026-07-15) |
| rejection count | attempts with outcome `rejected` | count only at v1 (n=1 today; a rate over this base would be noise dressed as signal) |
| bailout rate | sessions with latest outcome `bailout` | sessions with ≥1 response attempt |
| clarification rate | sessions with promoted `clarification.rounds ≥ 1` | closed sessions **within the clarification epoch** (key present); pre-epoch sessions are a named coverage gap, not a zero |
| closure mix | — | distribution over closed sessions: applied / reverted / bailout / unlocked-by-reason; in-flight and open counted beside, not inside |

### The dual-stream cross-checks (v1 set, deliberately minimal)

The self-reported stream is a calibration target, so v1 reports two
cross-checks beside the mechanical rates, never blended into them:

1. **Clarification:** sessions whose any attempt has
   `feedback.mechanical.linkage.kind == "clarification"`
   (self-reported placement) vs sessions with promoted
   `clarification.rounds ≥ 1` (bale-computed). Agreement here is the
   worker honestly reporting its own recourse history.
2. **Budget:** `feedback.self_reported.budget_pressure` distribution
   vs bailout outcomes — a `budget_pressure: "none"` on a session
   that bailed is exactly the miscalibration the stream exists to
   surface.

### Epoch reporting

The corpus begins at `2026-07-14-packaging-lists-v2-004` (min
`created_at`; verified). `bale stats` states the epoch as a report
row — first sid and date — and states that pre-epoch sessions exist
only in git and are not counted. It does **not** mine git for
pre-epoch session counts at v1: a second, differently-shaped input
would undermine the one-substrate property D1 just bought, and the
pre-epoch population is fixed and shrinking in relevance.
Sub-epochs are detected by key presence and reported as coverage
rows: `closure_reason` (first record carrying the key —
`2026-07-29-continue-plan-005` in today's corpus; 29 earlier records
lack it) and `clarification` (will begin with session A's landing).
Key-presence detection means the coverage rows need no version table
and stay correct as the corpus grows.

### Corrupt and future-versioned records

A record that fails to parse is skipped, counted in a
`parse_failures` row, and named on stderr — never a crash, never a
silent skip (hard rule). A record with `record_version > 1` is
filtered and counted under a `filtered_record_versions` row —
consumers branch on the version, as the schema instructs.

## D3. Drift-refusal semantics and the §8.9 sentence

**Semantics.** A `scope-drift-refused` attempt is an attempt-level
mechanical-stream event: the gate fired, the session stayed open, a
later attempt supersedes it exactly as a HOLD's does. The ledger
therefore counts refusals at attempt level (rate per D2), keeps them
in the record's history after the session eventually applies (both
corpus instances follow this shape), and reports override incidence
beside them. The refused path set is derivable when wanted:
`change_paths − scope − overridden_paths`, all three recorded raw —
the ledger computes, the record stores.

**The sentence** (doc fold-in, lands with session A). §8.9's "Every
terminal outcome records." paragraph currently enumerates `applied`,
`held`, `reverted`, `rejected`, `bailout`, `unlocked` — verified this
sitting; the schema enum has carried `scope-drift-refused` since
v0.3.10. Amend the paragraph by inserting, between the `rejected`
and `bailout` items:

> `scope-drift-refused` (the own-scope drift gate's refusal at apply
> pre-flight, §8.1 step 14 — the session stays open, so a later
> attempt supersedes it the way a HOLD's does),

The rollback pair (`rolled-back` / `re-applied`) is deliberately not
added to this list: §8.9's own schema description and §9.2 already
document them as post-close history events, not terminal outcomes of
an apply close, and the paragraph is about apply-close recording.

## D4. Reverse lineage: stamp at the close, by pack

The ledger's v1 rates need no lineage — a superseded parent is
honest in every rate without knowing its child. But the do-nothing
baseline ("jq over stamped manifests") quietly fails long-term: the
child's `depends_on.superseded_session` lives only in the request
manifest, whose tarball is transient outbox content, and the
telemetry `linkage` field covers probe/clarification rounds, not
supersession (verified against the response-manifest schema). Once
the outbox rotates, the parent→child edge is gone everywhere.

Session 26's proposal was apply appending a successor note to the
parent's record. The variant chosen here is cheaper and
single-writer: **pack stamps it**. The `--supersedes` accept path
already writes the parent's closure attempt
(`superseded-by-split`, command `pack`) at the exact moment it knows
the child sid; that attempt gains an additive
`superseded_by: "<child-sid>"` key. No cross-session write timing,
no apply reaching into another sid's record, no backfill of the one
existing split record (`2026-07-29-split-supersession-002` — its
edge survives in git history and MASTER.md). Rejected: apply-side
appends (a second writer for the same fact, later, with the same
information pack already had).

## D5. Commit cadence and the rollback guard

**Cadence.** `bale stats` reads record files from the working tree,
committed or not — git history is the corpus's *timeline*, but the
*reader* is the filesystem, matching §8.9's write-to-working-tree
posture. So the ledger has no functional dependency on prompt
commits. Durability does: an uncommitted record dies with a hard
reset or lives only on one checkout. The discipline stays as §8.9
states it — the record rides the next ordinary commit — and stats
adds no nag beyond its own honest output.

**The guard.** Given that, the rollback dirty-tree guard's refusal
on the untracked record bale itself just wrote is friction with no
protective value, and the change is safe by construction:
`git revert` rewrites tracked content only; the one collision case
(a revert that would materialize a file at an untracked path) is
refused loudly by git itself. Spec: in `_guard_dirty_tree`, filter
the `git status --porcelain` output — drop `?? ` (untracked) entries
whose path is under `claude/telemetry/` before judging cleanliness;
when entries were dropped and the remainder is clean, proceed with a
log line naming the disregarded paths. Modified *tracked* files under
`claude/telemetry/` still refuse (that is a real conflict surface).
`--stash` and `--force` behavior unchanged. This unblocks the
rollback → `--undo` toggle without an interleaved commit. Rides
session A.

## D6. Command surface

### Invocation

`bale stats [--work-class CLS] [--since DATE] [--json]`

- Read-only: no lock, no writes, no clean-tree requirement, exits 0
  on a successful read (the `bale status` posture); degrades
  gracefully when `claude/telemetry/` is absent or empty — an honest
  empty report, exit 0, not an error.
- `--work-class CLS` — filter to one class (enum: code, doc,
  contract-doc, meta, mixed, plus `unclassed`). Reader: board 10's
  per-class grant evaluation; this is the flag the whole feature
  exists for.
- `--since DATE` (ISO date, inclusive, against `created_at`) —
  reader: trend checks against the recent corpus once it is large
  enough that lifetime rates go stale. Included at v1 on that
  argument; flagged below as the surface item most worth contesting.
- `--json` — one line on stdout under the standard stream
  discipline; everything else to stderr.
- Deliberately absent at v1 (no reader): `--until`, per-sid drilldown
  (that is `bale status` / per-sid inspection territory), outcome
  filters (the report already breaks outcomes out), any output-format
  knob beyond `--json`.

### Homes (one-home rule applied)

- **`bin/bale_stats.py`** (new sibling module, lazy-import idiom of
  the other five): corpus loading, parsing tolerances, unit
  classification, rate computation. Extraction-by-need — this is a
  new need, and neither `bale_report` (rendering) nor `bin/bale`
  (wiring) is its home.
- **`bale_report.py`**: `format_stats_json` and the human renderer
  join the renderer family. The `format_stats_json` docstring owns
  the json key list — this brief specs the *semantic content*
  (D2's units, rates, coverage, epoch, filters echo, corpus counts)
  and deliberately does not freeze a key list here; one home, and it
  is the docstring. Keys are a stable additive contract from v1.
- **`bin/bale`**: wiring only — the subcommand, arg parsing,
  `enable_json_mode` on `--json`.
- **BALE.md**: a new command-surface subsection under §5 describing
  behavior and pointing at the docstring for the key contract, plus
  the §8.9 sentence (D3) and the §9.2 guard note (D5).

### Human rendering

Follows the report rule: bulky reference first, summary block last.
The per-class rate table (one row per class present in the filtered
corpus, columns per D2's headline rates) and the coverage/epoch rows
render as the reference body; the trailing summary block carries
corpus totals (records, sessions, attempts, parse failures, read-only
count, in-flight count) and the filters in effect. No trailing
next-step hint — stats is terminal, not a lifecycle step. Layout
specifics are the implementation session's, inside these rules.

## D7. Riders

1. **Bailout banner telemetry row** (ratified trivial): the bailout
   terminal banner gains the same `telemetry: recorded <path>` /
   `write failed — see log` row every other terminal banner carries
   per §8.9's rendering rule. `print_bailout_banner` / its caller in
   the bailout branch; rides session A alongside the `diagnostics`
   embed it will sit next to.
2. **Rollback guard change** (D5) — session A.
3. **§8.9 sentence** (D3) and the D1/D4 schema-description updates —
   session A.
4. **The deferred HOLD-shaped multi-attempt E2E** (session 25's
   deferral) — this board's tests; assigned to session A, whose
   write-path work is what the E2E exercises (apply HOLD → retry
   PASS, asserting appended `attempts[]` and envelope mirroring).

## D8. Tests

Oracle doctrine per ADR-0002: observable-state assertions against
the documented contract; golden comparison nowhere (the json line is
asserted key-by-key, not byte-by-byte). Hermeticity per ADR-0005.

**Session A (write paths):**
- clarification stamp: apply-close and unlock-close (each closure
  reason) stamp `{rounds, records[]}` correctly from a fixture
  `.bale/clarifications/<sid>/` with multiple NNN records; absent dir
  stamps `rounds: 0`; the stamp appears on the closing attempt only.
- bailout embed: `diagnostics` lands verbatim on the bailout attempt;
  the existing missing/invalid-diagnostics failure paths are
  unchanged.
- `superseded_by`: stamped on the `--supersedes` accept path; absent
  on decline; idempotent re-run does not double-stamp.
- guard: untracked telemetry disregarded (rollback proceeds, log line
  present); modified tracked file still refuses; `--stash` path
  unchanged; the rollback → `--undo` toggle completes with no
  interleaved commit.
- bailout banner row: the documented telemetry row appears (stdout
  marker is part of the documented contract, so string-asserting it
  is within ADR-0002's lines).
- the HOLD multi-attempt E2E (D7.4).

**Session B (aggregation), over a checked-in fixture corpus that
encodes every shape the real corpus and the schemas admit:**
single-attempt applied; HOLD→retry; drift-refused→applied;
rejected→applied (class inheritance to the feedback-less attempt);
unlock `abandoned`; unlock `closed-read-only` with `[]` scope; the
overload case — `[]` scope, *no* `closure_reason` key — asserted NOT
read-only; pre-v0.3.16 shape (no `closure_reason` key anywhere);
`reconciliation_parsed` false (asserted counted in unparsed share and
absent from agreement denominators); corrupt JSON (skipped, counted,
named on stderr, exit still 0); `record_version: 2` (filtered,
counted); bailout with embedded diagnostics; clarification
`rounds: 2` with matching and mismatching `linkage` (both cross-check
directions); missing work_class → `unclassed`; post-close
`rolled-back` (applied attempt still in mechanical denominators;
churn row incremented); epoch and coverage rows against the fixture's
dates and key presence; `--work-class` and `--since` filter echo and
effect; empty-corpus honest report; json stream discipline
(one stdout line, logs on stderr).

## D9. Session split

Two sessions, serialized:

**Session A — telemetry promotion, guard, riders** (work class:
code). Scope seam: the write side of the ledger.
Touches: `bin/bale_apply.py` (bailout embed, clarification stamp on
apply-close), `bin/bale_pack.py` (`superseded_by`),
`bin/bale_rollback.py` (guard), `bin/bale_report.py` (bailout banner
row; the telemetry-attempt builder if the stamp threads through it),
`bin/bale` (wiring/unlock-close stamp), `schemas/telemetry-record.schema.json`
(additive fields + description updates), `BALE.md` (§8.9 sentence,
§8.10.2 note, §9.2 guard note), `tests/`.

**Session B — `bale stats`** (work class: code). Scope seam: the
read side. Touches: `bin/bale_stats.py` (new; in scope under a
`bin/` directory include), `bin/bale_report.py` (renderers),
`bin/bale` (wiring), `BALE.md` (§5 command subsection), `tests/`
(fixture corpus + aggregation suite).

**Serialization claim:** B follows A, for two independent reasons the
master can contest separately. First, B's fixture corpus encodes A's
additive fields (`diagnostics`, `clarification`, `superseded_by`) and
its cross-check tests read them; building B against a guessed shape
of A's output re-introduces exactly the confidently-wrong risk the
workflow exists to prevent. Second, the scopes intersect on
`bin/bale_report.py`, `bin/bale`, `BALE.md`, and `tests/`, so the
pack-time disjointness gate serializes them regardless — a seam that
made them concurrent would have to split `bale_report` and `BALE.md`
ownership artificially, which the one-home rule argues against.
Each session sizes comfortably within a window: A is five bounded
write-path changes plus tests; B is one new module, two renderers,
wiring, and a fixture corpus. A single combined session is the tight
fit §11.2 says to treat as not fitting.

Both sessions include the execution-context manifest set (ratified
2026-07-21) since their fixtures execute `bin/bale` end to end: all
of `bin/`, all of `schemas/`, the four global docs, and
`tools/response_lint.py`, copied verbatim.

## D10. Interface notes for later boards (design nothing here)

- **Board 10 (grants):** `bale stats --json` is the consumer surface;
  per-class mechanical rates are the substrate, the D2 cross-check
  rows are the calibration view of the self-reported stream, and the
  additive key contract means the grant harness can pin the keys it
  reads. Nothing is reserved for it.
- **Board 6 (blind checkpoints):** when blind-checkpoint outcomes
  join validation, they arrive as additional mechanical facts on the
  attempt (new additive fields or new check rows); D2's check-level
  denominators absorb new checks without redefinition. The
  worker-vs-blind distinction, if the ledger later wants it, is a new
  field on the check entry — additive again.
- **Board 13 (read/write includes):** the ledger consumes `scope` and
  `change_paths` as recorded today; a future split of includes would
  arrive as additive attempt fields and a new drift definition,
  versioned by key presence like every coverage row here.
