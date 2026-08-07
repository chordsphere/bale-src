# board-13 read-vs-write include separation — design brief — revA

Session: `2026-08-07-board-13-read-write-design-003`. Read-only
design session; nothing here lands. Partitioned per the board-5/6
precedent: decisions ratified at this level / questions for the
master desk / escalations. The ratified constraint (MASTER.md
board-13 row, chat-ratified 2026-08-06) is the anchor throughout;
where a decision below instantiates it, I say so; where a decision
would extend or revise a contract, it is escalated, not decided.

## 0. The design in one paragraph

`--include` stops carrying scope. It returns to meaning exactly what
it ships: read context, generous by default, locking nothing. A new
declaration — the **write forecast** — carries what the include set
carried into the gates: it is recorded in the registry as
`sessions/<sid>/scope.json` (same file, same JSON shape, reinterpreted
meaning), stamped into the request manifest as `resolved_scope` (same
key, same one-source rule), and read by the same three gates through
the same helpers. The pack-time disjointness gate intersects write
forecasts only. The apply-time sibling-collision gate — the one
mechanical refusal the constraint reserves — rejects `changes[]`
paths contended by another open session's forecast. The own-scope
drift gate re-bases onto the forecast and its posture generalizes per
ADR-0014: out-of-forecast edits, modified files now included, ship
enumerated and are admitted per path at apply, graded by the ledger.
`--read-only` becomes the degenerate case: an empty forecast. The
wire and record changes are additive end to end; the single largest
implementation delta is in what pack writes, not in what the gates
read.

---

## Part I — Decisions ratified at this level

These instantiate the ratified constraint or make implementation
choices inside it. Each is contestable at review; none sets
precedent beyond the constraint already ratified.

### I.1 Declaration surface (design question 1)

**A new flag family: `--write PATH...`** — repeatable or
space-separated, exactly the `--include` grammar; directory entries
cover their subtrees, the same containment semantics
`scope_path`/`scope_paths_intersect`/`scope_covers_path` already
implement. The architect's-typed-surface concern is covered by the
existing contract: every flagged pack command is Claude-authored, so
the flag family costs the human operator nothing on the authored
path.

Rejected spellings: `--write-scope` (reintroduces the word "scope"
into a surface whose whole point is that shipping and scope are no
longer the same thing), `--forecast` (says the epistemics but not
the subject), `--scope` (the ambiguity itself).

**Semantics:**

- `--write` entries name existing paths — files or directories. The
  ADR-0014 rule ("includes name existing context only; nobody
  pre-names the files") holds on this surface too, for the same
  reason: forecasting the response's file layout is the worker's
  job. A packer who knows new files will land in one area forecasts
  the directory. One rule across both flag families, no exceptions
  to memorize.
- `--write` requires at least one path. The empty forecast has
  exactly one spelling: `--read-only` (see I.4). `--write` and
  `--read-only` together refuse as contradictory, at arg-parse time,
  before any prompt.
- `--write` entries need not be a subset of `--include`. A session
  can be shown one thing and forecast landing another (rare, but
  nothing in the model forbids it, and requiring the subset would
  re-couple the two surfaces for no gate's benefit).

**Default when `--write` is absent: the forecast is the resolved
include set.** This is the load-bearing compatibility decision. A
pack with no `--write` behaves byte-for-byte as today: narrow
includes → narrow forecast, default whole-tree includes → whole-tree
forecast, broad packs stay concurrency-exclusive. Separation is
opt-in per pack, engaged by typing the flag; nothing that works
today changes meaning underneath anyone. The alternative default
(absent `--write` → whole-tree forecast) was rejected because it
would make today's narrow-include packs suddenly lock the whole
tree — strictly worse than the disease.

**Wizard behavior (evidence 37 — the cold-start pack is the one
command with no Claude author).** The session-shape question
(v0.3.15) already asks lands-changes vs read-only. It gains one
follow-up on the lands-changes branch: *"Where will changes land?
[Enter = same as the includes]"* — accepting a space-separated path
list, defaulting to today's behavior on a bare Enter. The cold-start
user who has never heard of the separation presses Enter and gets
exactly the pre-separation pack. The prompt names its own semantics
in one line (a forecast, not a wall — out-of-forecast work surfaces
at apply for per-path admission). No other wizard step changes.

### I.2 Record and stamp shape (design question 2)

**The registry record: `sessions/<sid>/scope.json` is reinterpreted,
not replaced.** Same filename, same JSON shape (a flat list; `[]`
still the read-only shape; missing/malformed still degrades to
conservative whole-tree). What changes is what pack writes into it:
the resolved write forecast instead of the resolved include set.
`persist_session_scope` and `read_session_scope` are untouched.

Why reinterpretation is safe, and specifically why the transition
window is safe: an open session packed under the old model has
`scope.json` = its include set, which the new gates read as its
forecast. That is an **over-forecast** — the failure direction is
over-locking, never under-locking, exactly the direction
`read_session_scope`'s docstring already commits to for unreadable
scopes. Old open sessions keep every protection they had; the cost
is that they keep their old lock breadth until they close, which is
self-clearing and needs no migration step.

**No second registry file at v1 of this design.** Nothing mechanical
reads the resolved include set post-separation — no gate, no
sweep, no closure inference. The include set survives where it
already lives: the request manifest's `context_included`, the pack
log's filter trail, and the shipped `context/` tree itself. If the
ledger later wants the read set registry-side (see Part II, Q3), the
addition is a sibling file, additive by construction.

**The manifest stamp: `resolved_scope` keeps its name and keeps its
contract.** The key's meaning to the worker — "the authoritative
read of what the own-scope drift gate will enforce; one source with
the registry record, never a re-derivation" — survives verbatim.
What the value *is* changes underneath the contract (forecast, not
includes), and the schema description is edited to say so. This is
the additive move the 1.0.0 ladder wants: zero new required keys,
zero renamed keys, old manifests valid, the documented fallback for
stampless manifests (infer from `context_included`) unchanged and
now conservative in the same over-forecast direction as the registry
transition.

Rejected alternative: a new `write_forecast` manifest key with
`resolved_scope` deprecated. Cleaner naming, but it breaks the
workers-reason-from-the-stamp contract for zero mechanical gain, and
the cost lands exactly where the 1.0.0 ladder says shape changes get
expensive. Named here so the master desk can contest it; my
recommendation is firm.

Provenance: no change. `work_class`, `packer`, checkpoint stamps all
orthogonal.

### I.3 Gate semantics, with firing conditions named (design question 3; per evidence 42)

Every gate below states its exact firing condition and what happens
on every path, including declines.

**G1 — pack-time disjointness (§7.1 step 5, §11 row 3).**
*Fires iff:* the new pack's resolved write forecast intersects at
least one open session's recorded `scope.json`, under the existing
containment semantics (directories cover subtrees, `.` covers
everything, `[]` intersects nothing). Read includes participate in
nothing. *On fire:* refuse pre-sid, naming the colliding session(s)
and entries; remedies unchanged — narrow the forecast, apply or
unlock the colliding session, or `--supersedes <sid>` for a split,
whose accept/decline flow (decline default, piped-stdin declines,
idempotent re-run) is untouched. *On pass:* proceed; the gate
evaluated against every open session, supersession clearing exactly
one. *Deliberate consequence:* the ADR-0007 sentence "includes are a
conservative proxy for change scope" retires. Broad *reading* and
concurrency stop being mutually exclusive; broad *forecasting* and
concurrency remain so. A default pack (no `--write`) still
whole-tree-forecasts per I.1 and still excludes concurrency — no
behavior change for anyone not using the new flag.

**G2 — apply-time sibling collision (§8.1 step 7, §11 row 19).**
*Fires iff:* any `changes[]` path intersects **another** open
session's recorded forecast. This is the one mechanical refusal the
constraint reserves — finding 2's failure class, the whole-file
clobber. *On fire:* `[REJECT]`, pre-staging, no git side effects,
session stays open. *No override flag*, deliberately: G2 has none
today and gains none. The remedy is sequencing (apply or close the
sibling, or supersede), not admission — a per-path override here
would let the operator hand-wave the exact hazard the gate exists
for. Note the interaction with G3: a path the operator admits past
the *own* gate with `--allow-out-of-scope` still refuses at G2 if a
sibling's forecast claims it. Pipeline order (step 7 before step 14)
already guarantees this; the design makes it doctrine: **admission
never crosses a sibling's forecast.**

**G3 — own-forecast drift (§8.1 step 14, §11 row 22).**
*Fires iff:* a `changes[]` path lies outside this session's own
recorded forecast and is not named by a per-invocation
`--allow-out-of-scope`. Mechanics are byte-for-byte today's gate —
refusal names every offending path and the declared set,
pre-staging, session stays open, outcome `scope-drift-refused`,
`--json` contract unchanged, partial overrides admit named paths
while other drift still refuses, retry re-states the override, no
config key ever. Created and modified paths were already treated
identically here since v0.3.10. What changes is the **doctrine
around the gate**, which is the constraint's core: an out-of-forecast
edit — to an existing file, not just a new one — is no longer a
policy violation to be proposed-never-made; it is worker judgment
past the ask, shipped, **enumerated in notes.md with why**, admitted
per path by the operator, and graded by the ledger (I.5). ADR-0014's
admission flow, generalized from created to modified. The
stay-in-the-lane rule's *value* survives as a default — the forecast
is still the ask, and drift is still the exception that must argue
for itself in the enumeration — but its "never made" clause for
modifications is revised. That clause lives in CLAUDE.md §6 and
TARBALL.md §3.2: contract revisions, escalated (Part III, E1). An
empty forecast covers nothing, so G3 refuses everything a read-only
session ships — masters-never-self-land stays mechanical (I.4).

**G4 — required-check superset (step 15, row 26).** Unchanged; keys
on `changes[]` and config, not scope.

**G5 — checkpoint blindness, pack side (step 4b, row 27).** The
covering refusal re-bases: *fires iff the resolved write forecast
covers the configured checkpoint's path* (drift-gate containment; an
empty forecast covers nothing and passes vacuously). Same override
(`--allow-checkpoint-in-scope`, per-invocation, flag-only,
FORCE-logged, `checkpoint_scope_admitted` stamped), same handoff
mirror against the reading-plan-derived forecast. But separation
opens a fork the conflated model never had to face: a generous read
include can now **ship the checkpoint's bytes** to the worker while
the forecast excludes it — mechanically clean at every gate, and
arguably the self-oracle hazard the blindness contract exists to
prevent (the graded entity reading the oracle). My recommendation:
add a read-side check — pack refuses when the resolved include set
would ship the configured checkpoint's content, same override flag,
same stamp. But whether blindness means *cannot land edits to the
oracle* or *cannot see the oracle* is a board-6 contract semantic,
so the recommendation is escalated, not decided (Part III, E3).
Dangling-at-tip refusal (rows 27's other half, 29): unchanged.

**G6 — the read-only sweep and closure inference.** Unchanged
mechanically; see I.4.

*What no gate does:* nothing checks `changes[]` or forecasts against
any session's **read set** — not the sibling's, not its own. Read
sets are shipping manifests, not claims. The one hazard this admits
is read-staleness, treated honestly in I.6.

### I.4 Read-only subsumption (design question 4)

**Yes — `--read-only` is now the degenerate case: the empty write
forecast. The flag survives as the spelling.** It remains the only
spelling (`--write` with zero paths is refused, I.1), because the
flag carries more than the empty set: it is the wizard answer, the
sweep trigger, the open banner's close-out naming, and the
`closed-read-only` inference key — ergonomics worth a dedicated
spelling.

Everything downstream keys on the recorded `[]`, and `[]` means
after the separation exactly what it meant before — locks nothing
(G1/G2 intersect nothing), may land nothing (G3 covers nothing) — so
**the sweep, the accept-default prompt, the piped-stdin decline, the
open banner, and unlock's `closed-read-only` inference all survive
untouched**, not by compatibility shimming but because the state
they key on didn't change meaning. One generalization falls out for
free and is worth a sentence in the landing docs: any session whose
forecast is `[]` is structurally sweep-safe (the drift gate refuses
everything it could ship), which is the same argument the sweep's
accept-default already rests on. Board 24's degenerate slice is
subsumed, not collided with.

### I.5 Ledger grading (design question 5)

Per the dual-stream contract, split mechanical from self-reported:

**Mechanical (bale-computed, no worker input):**
- `attempts[].scope` continues to record the session's recorded
  `scope.json` raw — post-separation, that is the forecast. The
  drift the aggregation computes from `scope` vs `change_paths`
  becomes *judgment past the ask*, which is precisely the rate the
  constraint says the ledger grades.
- `overridden_paths` (admitted drift) and outcome
  `scope-drift-refused` (unadmitted drift): unchanged, and both now
  measure the generalized posture.
- **Epoch disambiguation** — the `reconciliation_parsed` doctrine,
  applied a fourth time: an additive per-attempt key, proposed
  spelling `scope_kind: "write-forecast"`, present on every
  post-epoch attempt and absent before. Without it, aggregation
  conflates old conflated-scope drift rates (structurally near zero:
  changes rarely left the include set) with forecast drift rates
  (expected nonzero by design), and the trend line lies. Key
  presence is epoch membership; `record_version` stays 1 (additive).
- A new derivable rate worth a `bale stats` row: **forecast
  precision** — forecast entries never touched by `changes[]`. High
  imprecision is the over-locking signal, the mirror of ADR-0014's
  "admissions clustering means seams drawn too narrow": drift
  clustering means forecasts drawn too narrow; imprecision
  clustering means drawn too wide. Both are scoping signals about
  the packer, not discipline signals about the worker.

**Self-reported (worker-authored, persisted verbatim):**
- The notes.md enumeration stays the human-facing account and the
  apply-time walkthrough input, per ADR-0014 — prose, deliberately
  unparsed.
- The feedback block (TARBALL.md §5.2.2) gains an additive optional
  field, proposed spelling `forecast_departures: [{path, why}]` —
  the worker's own structured account of judgment past the ask.
  Apply already persists feedback verbatim into telemetry, so the
  cross-check becomes mechanical at stats time: departures declared
  vs paths admitted/refused. An admitted path with no declared
  departure is the ADR-0014 audit smell, now computable instead of
  eyeballed. This touches the response-manifest schema — §5-class —
  so the field's *addition* is escalated (Part III, E2); the design
  here is what it should look like when ratified.

### I.6 The accepted residue: read-staleness, named

Today's conflation accidentally protects read freshness: a sibling
cannot land changes to anything an open session was *shown*, because
shown-and-scoped are the same set. The separation deliberately gives
that up — that is what "generous whole-tree shipping without lock
cost" costs. Concretely: session S is shown file F (read include,
not forecast); a sibling lands changes to F mid-S; S's shipped copy
of F is now stale, and S's response was authored against a snapshot.

Why this is acceptable rather than a new finding-2: S's own writes
are confined to S's forecast, which is disjoint from the sibling's
landed paths (G1/G2), so nothing S ships clobbers anything —
the failure mode is *semantic* (S reasoned from stale context), not
silent whole-file overwrite. And the semantic failure has a
mechanical backstop already in place: S's `validation.sh` runs
against the post-merge staging tree at S's apply, so an
incompatibility surfaces as a HOLD, in front of the operator, not as
a clean merge. Review remains the last line, as it is for every
semantic property.

On-watch, not on-gate: the ledger can see this class (a HOLD whose
session opened before a sibling's apply landed inside its read set)
once the epochs are stamped. If HOLDs cluster there, the answer is
probably a pack-time *warning* (never a refusal) naming the overlap
— proposed only if the data asks for it.

---

## Part II — Questions for the master desk

**Q1 — The §5 execution-context manifest contract's wording (design
question 6).** The contract's text is not in this request's context
— nothing shipped carries it, and I will not confirm or amend
wording I have not read. What the design determines regardless: under
separation, an include set carried to satisfy validation's execution
needs is read context and stops locking, so the contract's
*motivating cost* (the lock generator the brief names) dissolves
while its *requirement* (ship what validation will execute against)
survives on the read side untouched. If the contract's wording binds
its include set to "scope" or to the disjointness gates, it needs a
one-line amendment re-basing that reference onto the read set; if it
only obligates shipping, it survives unchanged. Please paste the
contract text (or include it in the implementation session's
context) and I'll return the confirmation or the amendment line.

**Q2 — ADR numbering and INDEX state.** The next ADR number is not
determinable from this context (0014 is the highest shipped; the
project's INDEX.md was not included). The ADR draft carries a
placeholder number to be assigned at landing.

**Q3 — Does the ledger want the read set registry-side?** I.2
records no read set in the registry because nothing mechanical reads
it. If the master desk wants read-staleness watching (I.6) sooner
rather than data-driven, the registry needs the resolved include set
persisted (a sibling file beside scope.json, additive). Default
recommendation: not yet; the manifest and pack log carry it, and the
watch can start from telemetry epochs.

**Q4 — `bale status` rendering depth.** The session row should label
the recorded set "write forecast" post-epoch and keep rendering `[]`
as read-only. Whether status should *also* render the include set
(from the session manifest it already persists) is a legibility
call, not a contract one — cheap either way; I've left it to the
implementation session's judgment unless the desk has a preference.

---

## Part III — Escalations (precedent-setting; ratify before landing)

**E1 — Contract-doc revisions: CLAUDE.md §6 and TARBALL.md §3.2/§3.4.**
The lane rule's split-by-file-existence (ADR-0014's clause 5)
revises again: out-of-forecast *modifications* join creations on the
ship-enumerate-admit path; the proposed-never-made clause narrows to
paths a sibling's forecast claims (where G2 makes it mechanical) and
to the prose `out_of_scope` field (unchanged, review-only).
TARBALL.md §3.2's scope narrative and §3.4's flag table gain the
`--write` family and the forecast doctrine. Global docs evolve only
via bale sessions on bale-src; the wording lands in the
implementation arc after ratification here. Proposed replacement
wording for the CLAUDE.md §6 bullet is in the ADR draft's
Consequences.

**E2 — Response-manifest schema addition (`feedback.forecast_departures`,
I.5).** §5-class wire change, additive and optional. Design settled;
addition ratified upward.

**E3 — Blindness semantics fork (I.3 G5).** Recommendation: the
covering refusal re-bases to the forecast AND a read-side
ships-the-oracle refusal is added under the same override. The
choice keys on what board-6's blindness contract means, which is the
master desk's to say.

**E4 — ADR-0007 status flip.** The draft supersedes ADR-0007 (see
the ADR draft's Notes for why stand-beside — the ADR-0014 precedent
— is the wrong shape here: 0007's *decision text* defines scope as
the resolved include set, and a superseded decision sentence left
Accepted is exactly the stale-contract trap ADR-0014's Context
documents). The flip itself is ratified at the master desk.

**E5 — This design as a whole.** Per the brief: implementation packs
are authored only after the design is ratified upward. The
decomposition (companion document) is staged and waiting on this.
