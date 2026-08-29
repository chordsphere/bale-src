# ADR-0017: Exchange shape is independent of the counterparty

- **Status:** Accepted
- **Date:** 2026-08-29
- **Supersedes:** —
- **Superseded by:** —

## Context

The worker↔planner conversation had a wire shape for its opening
move and none for what followed. ADR-0011 gave a blocking intent gap
the clarification response; the doctrine around it then forked on
who was at the other end. TARBALL.md §5.9.1 made chat the default
ask surface "in a human-attended session" and the artifact the
default only "in an orchestrated session"; §5.9.4 described the
answer path as "manual today … programmatic later"; TARBALL.md §1
defined the planner as "today the human architect" and the operator
as "later possibly a harness"; PLANNER.md §8 wrote everything
harness-dependent in the future tense and §15 described the
clarification flow as worker → architect → master → architect →
worker with the architect as transport; ADR-0012 said "anything
harness-dependent stays future-tense until the harness exists."

In live traffic that fork routed every blocking intent gap to the
operator's chat. The operator hand-carried the question to the
master session and hand-carried the answer back; nothing recorded
the answer; the mechanized shape never fired, because a human was
always present, and the manual path — declared ground truth by
ADR-0012's commitment 3 — never proved it. The clarification
response was a dead end, not a round.

The design was ratified at the read-only sitting
`2026-08-29-formalize-convo-001` (the sub-master transition,
PLANNER.md §20). This session lands its doctrine half; two code
siblings under the same arc land the schema plus the `bale relay`
verb, and the crafter's paste-block emission.

## Decision

1. **The principle.** The shape of a worker↔planner exchange never
   depends on who is at the other end. Every fork on
   "human-attended vs orchestrated", "manual today vs programmatic
   later", or "the harness era" that gates a *shape* is retired.
   Language is role-only: **planner** (intent authority), **worker**
   (mechanism authority), **operator** (runs pack/apply), and
   **courier** (carries pastes between sessions — the operator by
   hand, or a harness in its stead). Any role can be held by a human
   or a session, and no doctrine keys on which. The worker always
   emits the formal shape; bale always records it and emits the next
   paste block; a harness, where one exists, only stops the operator
   from being the one who pastes.

2. **The inquiry shape is the clarification response, unchanged.**
   `response_kind: "clarification"` and its `questions[]` rows
   (`response-manifest.schema.json`, TARBALL.md §5.9.2) stay the
   worker's ask shape. Questions must still be blocking; the tarball
   courier stays valid. The tarball is no longer the *only* courier —
   the same manifest travels as a paste block (clause 5) — and the
   artifact is the default on every path, never chat. Chat carries
   conversation, never a blocking ask; a blocking ask that resolves
   in chat anyway is a breach whose provenance `notes.md` records,
   not a sanctioned path.

3. **The exchange record.** One schema for both directions of the
   thread, `schemas/exchange-record.schema.json`, landing with the
   sibling code session: `record_version` (1), `session_id`, `round`
   (≥ 1), `from` (exactly `worker` | `planner`), `created_at` (ISO
   8601 UTC); `questions[]` by reference to
   `response-manifest.schema.json`'s `questions.items` (one home);
   `answers[]` of `{question_round, question_index, answer,
   disposition}` with `disposition` exactly `as-recommended` |
   `option` | `free-text`, plus optional `amendment_target` (the
   escalation record's field, same meaning). At least one array is
   non-empty; a record may carry both. The **thread** is the ordered
   records under `.bale/clarifications/<sid>/`, continuing the
   existing `NNN` numbering; a preserved clarification manifest
   reads as a `from: worker` record with `round` = its `NNN` — no
   migration, no second directory.

4. **The verb: `bale relay <sid> <file|->`.** Ingests one exchange —
   a clarification manifest, an exchange record, or the paste block
   wrapping either — from either side; validates it; preserves it as
   the next `NNN`; retains the lock; emits the counterpart-facing
   paste block. Direction is read from the record's `from`, never
   from a flag. `bale status`'s clarification-suspended row grows to
   show which side the thread waits on. Apply's ingest of a
   clarification *tarball* (BALE.md §8.10.2) is unchanged and is now
   one of two ingest paths for the same round-one record. Contract:
   BALE.md §8.11, contract row §11.34.

5. **The paste block.** A fenced, self-delimited block with the
   probe's four properties (TARBALL.md §4.2): sentinel lines
   `BALE EXCHANGE BEGIN <sid>` / `BALE EXCHANGE END`; the record's
   JSON as the body; a purpose header stating direction and round;
   an integrity trailer carrying the body's sha256, so a truncated
   paste is detected and re-requested instead of reasoned from. The
   worker-side emission (crafter) and the planner-side emission
   (`bale relay`) land in the sibling sessions; the docs describe the
   properties, not any tool flag.

6. **What stays exactly as it is.** The probe: still a read-only
   paste-back script, still no wire format (ADR-0010, BALE.md §6.5)
   — only the language around it changes per clause 1. The
   escalation record (`escalation-record.schema.json`): the
   master→architect distillation stays with the harness project per
   the 2026-08-25 routing (seed D13/D14); this arc reverses that
   routing for the worker↔planner leg only, and the two records
   coexist, sharing `amendment_target`'s meaning. Non-blocking
   mid-work inquiry is not in this arc; `priority: batched` keeps
   its doctrine — proceed on the named assumption.

## Consequences

- Three prior records are overridden without being edited (ADRs are
  append-only, DOCS.md §7.2); this ADR carries every override:
  - **ADR-0010** decision 2's "no `claude/probes/` directory, no bale
    subcommand, no artifact in the project tree" narrows to the
    probe *script*. The exchange has both a subcommand and a
    project-tree record; the probe still has neither.
  - **ADR-0011**'s Notes — the orchestrated answer path is "doctrine
    for when an orchestrator exists … not a change to the human
    path" — retires. There is one path; the clarification response
    is round one of a thread, not a dead end. Its decision 4's "the
    architect answers in the worker's chat" is superseded by clause
    4's answer path.
  - **ADR-0012**'s "anything harness-dependent stays future-tense
    until the harness exists" retires in favor of *present tense on
    the manual path; the harness inherits* — which is what its own
    commitment 3 (the manual path defines and verifies contract
    behavior) already required. Commitments 1–3 stand.
- The 2026-08-25 routing of the clarification-relay subsumption and
  the session-interaction mechanization mandate to the harness seed
  is reversed for the worker↔planner leg, by architect ruling at the
  authoring sitting. The master→architect leg keeps its routing.
- Doc surfaces updated in the session that lands this ADR:
  TARBALL.md §1, §2, §3.4, §4.2–4.4 (language only), §4.6, §5.1,
  §5.4.1, §5.9.1, §5.9.2, §5.9.4, §10.3; PLANNER.md META, §8, §15,
  §18; CLAUDE.md read-paths, §3, §4; BALE.md §5, §5.5, §6.6,
  §8.10.2, new §8.11, §11 row 34. No bin, schema, or version change.
- Two verbatim tokens the code siblings build against are pinned in
  TARBALL.md: `bale relay` and `exchange-record.schema.json`.
- Foreclosed: any doctrine that gates an exchange shape on the
  counterparty's species, and any language that softens the
  artifact to "preferred" — it is the shape. Also foreclosed: a
  `bale relay` option surface beyond `<sid> <file|->` described in
  the docs ahead of the sibling that owns it.
- Expected: more threads, and threads with more than one round.
  As with ADR-0010 and ADR-0011, wrong-response frequency is the
  minimization target, not question frequency; the thread length
  reaching the close-time `clarification` summary is what makes
  that measurable.

## Notes

Status is Accepted at creation — the direction was stated by the
architect directly at the authoring sitting; review at apply is the
check. Ratified at `2026-08-29-formalize-convo-001`; recorded by the
doctrine session packed from it.
