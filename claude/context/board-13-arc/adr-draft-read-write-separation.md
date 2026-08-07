# ADR-NNNN: Separate the read set from the write forecast; scope is what a session forecasts landing, not what it was shown

- **Status:** Proposed
- **Date:** 2026-08-07
- **Supersedes:** ADR-0007
- **Superseded by:** —

*(Number assigned at landing — the next in sequence was not
determinable from the design session's context. The status flip on
ADR-0007 is ratified at the master desk, per the escalation in the
board-13 design brief.)*

## Context

ADR-0007 made scope disjointness a mechanical contract with two
gates, and defined a session's scope as its resolved include set —
"includes are a proxy for change scope," deliberately conservative.
The proxy was honest about its false positives and cheap to accept
when sessions were serial by default.

Under the concurrency the ADR-0006/0007 pair unlocked, the proxy's
cost compounded into a recorded pattern: MASTER.md evidence entry 25
carries five tallies (2026-07-15, 2026-07-25, 2026-07-31, and twice
on 2026-08-06) of sessions with disjoint *write* intents serialized
because their *read* context intersected — near-whole-tree locks
carried for write sets of one to five files, including includes
carried purely to satisfy validation's execution needs. The
conflation makes generous context shipping and concurrency mutually
exclusive, which inverts the workflow's economics: context is cheap
and the drill-down doctrine wants it generous; locks are expensive
and the forecast wants them narrow. One declaration cannot serve
both masters.

Meanwhile ADR-0014 had already established, for new files, the
posture that resolves the tension: a declaration about where work
lands is the packer's *forecast*, worker determinations past it
surface at apply and are admitted per path, and clustering in the
admissions is a scoping signal, not a discipline one.

The architect's ratified design input (chat-ratified at the master
desk 2026-08-06, carried verbatim on the MASTER.md board-13 row):

> the separation's value is freeing the read side (generous
> whole-tree shipping without lock cost), not walling the write
> side. The write-set declaration is a concurrency forecast, not a
> permission wall — worker edits outside the declared write set
> surface at apply as drift and are admitted per path, ADR-0014's
> posture generalized from new files to modified ones; mechanical
> refusal is reserved for paths contended by another open session's
> write set (finding 2 is the failure class it guards); worker
> judgment past the ask is graded by the ledger, not prevented by
> scope.

## Decision

1. **Two declarations, two meanings.** The include set (`--include`)
   is the read set: what ships in `context/`, generous by default,
   participating in no gate. The **write forecast** (`--write`,
   repeatable; directory entries cover subtrees; entries name
   existing paths per ADR-0014's rule) is the session's declared
   scope: recorded in the registry, stamped in the manifest, read by
   the gates. Absent `--write`, the forecast defaults to the
   resolved include set — pre-separation behavior, byte-for-byte, so
   separation is opt-in per pack. The wizard's session-shape
   exchange asks where changes will land, defaulting to the includes
   on a bare Enter.

2. **The record and the stamp are reinterpreted, not reshaped.**
   `sessions/<sid>/scope.json` holds the forecast — same file, same
   JSON shape, same `[]`/missing/malformed semantics. The manifest's
   `resolved_scope` stamps the same value from the same source; its
   worker-facing contract ("what the drift gate will enforce") is
   unchanged. Zero new required keys. Open sessions packed before
   this ADR read as over-forecasts — conservative, self-clearing, no
   migration.

3. **ADR-0007's two gates survive, re-based onto forecasts.**
   Pack-time: refuse a pack whose forecast intersects an open
   session's forecast. Apply-time: reject a response whose
   `changes[]` paths intersect **another** open session's forecast —
   the whole-file-clobber guard, and the one mechanical refusal this
   model reserves; it takes no override, and paths admitted past the
   own-forecast gate still refuse here. Read sets participate in
   neither gate.

4. **The forecast is a forecast, not a wall — ADR-0014 generalized
   to modified files.** A `changes[]` path outside the session's own
   forecast — created *or modified* — is worker judgment past the
   ask: shipped, enumerated in `notes.md` with why, refused at the
   own-forecast gate unless the operator admits it per path per
   invocation, and graded by the ledger (drift and admission rates
   per work class; the worker's self-reported departures
   cross-checked against admissions per the dual-stream contract).
   The proposed-never-made rule narrows to paths a sibling's
   forecast claims and to the prose `out_of_scope` field.

5. **Read-only is the degenerate case.** `--read-only` remains the
   spelling of the empty forecast; the sweep, its accept-default
   prompt, the open banner's close-out naming, and the
   `closed-read-only` inference all key on the recorded `[]`, whose
   meaning is unchanged.

## Consequences

- Generous read shipping stops costing locks: the recorded
  serialization class (evidence 25) becomes structurally impossible
  for sessions with disjoint forecasts, including execution-context
  includes carried for validation.
- ADR-0007's "include-everything packs intersect everything"
  consequence dissolves for reads and survives for forecasts; a
  default pack still whole-tree-forecasts and remains
  concurrency-exclusive, so nothing changes under anyone who never
  types `--write`.
- Read-staleness becomes possible by design: a sibling may land
  changes inside an open session's read set. Accepted residue —
  the session's own writes stay clobber-proof via the gates, the
  semantic risk surfaces at the session's own validation against
  the post-merge tree, and the ledger watches the class (a
  data-gated pack-time warning is the forecast remedy if it
  clusters). This is the deliberate trade the ratified constraint
  names.
- CLAUDE.md §6's stay-in-the-lane rule revises (ratified wording
  landing with the contract-doc session): the forecast is the ask
  and staying inside it the default; work the goal genuinely
  requires outside it is made visibly — shipped, enumerated,
  admitted per path — never silently, and never onto a path a
  sibling's forecast claims. TARBALL.md §3.2/§3.4 gain the flag
  family and the doctrine.
- Telemetry gains an epoch key (`scope_kind`) so forecast-era drift
  rates never aggregate against conflation-era ones; `bale stats`
  gains forecast drift, admission, and precision rows. Drift
  clustering reads as forecasts drawn too narrow; precision
  clustering as drawn too wide — both packer-side scoping signals,
  per ADR-0014's doctrine.
- The checkpoint blindness covering refusal keys on the forecast;
  whether a read include may ship the oracle's bytes is a board-6
  semantic resolved at ratification (design brief E3).

## Notes

**Why supersede rather than stand beside.** ADR-0014 stood beside
ADR-0007 because only a Consequences *forecast* had been overtaken;
the decision text held. Here the decision text itself — "a session's
scope is its resolved include set" — is overturned, and DOCS.md §5
says an overturned decision gets a superseding ADR, never an edit
and not an Accepted ghost. Leaving 0007 Accepted while the gates
read a different declaration is precisely the docs-assert-the-
opposite-of-the-tool trap ADR-0014's Context records. ADR-0007's
gates live on inside this ADR's clause 3, restated so this document
is the single current reference; 0007 remains in the record as
append-only history, per DOCS.md §7.2.
