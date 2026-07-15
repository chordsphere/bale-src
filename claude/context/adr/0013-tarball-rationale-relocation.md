# ADR-0013: TARBALL.md carries normative content; displaced rationale lives here

- **Status:** Proposed
- **Date:** 2026-07-15
- **Supersedes:** —
- **Superseded by:** —

## Context

`TARBALL.md` is injected into every request (§3.1), so every session
pays its size as context-budget overhead before any work starts —
the same budget `CLAUDE.md` §11 defends. The doc had accumulated
rationale prose alongside its normative content: cost-benefit
arguments, failure analyses, design justifications. Rationale is
what ADRs are for (DOCS.md §5); a wire-format contract read every
session needs the rules, the shapes, and pointers to the *why*.

Some of that rationale already had ADR homes — the probe doctrine's
in ADR-0010, the clarification design's in ADR-0011 — and stating it
again in `TARBALL.md` violated the one-home rule (DOCS.md §9). The
rest had `TARBALL.md` prose as its only home and needed one before
it could leave.

## Decision

1. **Compress `TARBALL.md` in place with zero normative loss.**
   Every rule, artifact shape, field semantic, enum value, and
   procedural step stays. Only rationale prose moves.
2. **Section numbers and headings are stable** (DOCS.md §6.4).
   Every external reference into `TARBALL.md` — from `CLAUDE.md`,
   `DOCS.md`, `CODE.md`, ADRs, the schema, and the lint — resolves
   unchanged.
3. **One home per fact.** Rationale already homed in an ADR becomes
   a pointer to that ADR (ADR-0010 for probe doctrine, ADR-0011 for
   the clarification design). Rationale with no prior home relocates
   into this ADR's "Displaced rationale" section below, and the
   compressed text points here.

## Displaced rationale

Keyed by the `TARBALL.md` section each pointer lives in.

### META — pause on a missing contract doc

A hand-rolled request missing `TARBALL.md` gets a pause and a
question rather than a best-effort response because a malformed
tarball is more expensive than a paused session: the malformed case
costs a review, a rejection, and a re-attempt; the pause costs one
chat turn.

### §3.2 — why `out_of_scope` is an explicit list

Absence is harder to reason about than presence. A worker can check
a change against a named exclusion in one step; inferring what a
silent request *didn't* mean invites exactly the confident scope
drift the field exists to prevent.

### §3.4 / §5.5 — why unsolicited runnable commands are confined to the rescope offer

A runnable command arriving *inside a response tarball* has two
hazards. It invites blind firing — it surfaces in the apply
walkthrough beside a diff and a PASS banner, exactly the moment a
satisfied reviewer is primed to paste and go. And it lets the entity
under review frame the scope and includes of the follow-up that
extends or judges its own work — a soft version of the self-oracle
problem (ADR-0002's shape, at the workflow level). The rescope offer
has neither hazard: it is pre-work, so the session has built nothing
the command could frame, and it arrives as the whole point of a
conversational reply, so the planner cannot fire it without reading
it. This is also why `next-prompt.md` was retired (§5.5, session
`2026-07-06-retire-next-prompt-006`): it was an unsolicited,
post-work runnable command, the exact shape both hazards describe.

### §5.1 — why `files/` never carries generated artifacts

Generated artifacts are products of the project's toolchain — the
receiving side rebuilds them. Shipping them bloats the tarball and
plants stale-artifact bugs the content checks can't see past apply
time. The deny list is deliberately short and obvious rather than a
heuristic so that a legitimate source file that merely resembles a
generated one still passes; false rejection of real source would
cost more than the occasional manual catch of an unlisted artifact.

### §5.1 — why file changes never ride in chat beside the tarball

Pasted files aren't applicable: the planner can't `cp` from a chat
snippet into the project, and the tarball has to be extracted to
compare anyway, so the duplicate is pure friction — two copies to
reconcile, one of which can silently drift.

### §5.1.1 / §7.7 — the forgotten-chmod failure analysis

Forgetting the exec-bit restore is a confidently silent breakage:
content lands correct, validation that only inspects content passes
straight past it, and the next invocation of the script meets
`Permission denied`. The responsibility sits on the worker because
the overlay can't infer intent — a script and a config file look the
same to a copy. The §7.7 assertion exists to turn that silence into
a `[FAIL]`.

### §5.2.1 — why hashes are computed, never transcribed

A hand-written hash is wrong with near-certainty, and bale's
pre-flight rejects any manifest sha256 that disagrees with the bytes
under `files/` — so a guessed value doesn't save a step, it
guarantees a bounced tarball.

### §5.2.2 — why the feedback block splits by trust level

The split *is* the design: values the lint can recompute are
trustworthy as data; worker-authored judgment is valuable but
unverifiable, and mixing the two in one stream would launder the
second into the first. The mechanical stream's worth is that it was
computed; a transcribed guess poisons the calibration data the
telemetry record exists to collect, which is why a lint mismatch is
fixed by re-running, never by adjusting values until the check goes
quiet.

### §5.3 — what the claim/verdict disagreement pattern is for

The pattern of disagreements over time is the signal worth catching:
it shows where the worker's calibration is off and which checks the
planner should be tightening. A single disagreement is diagnostic
noise; a cluster is a finding.

### §5.4.1 — why Proposals exist

Workers discover things at completion that a top-down planner cannot
know: a seam visible only from inside the code, an out-of-scope fix
worth doing, a test deferred and exactly why. Proposals are the
channel that carries that vantage point upward without ceding
sequencing authority (which stays with the planner, per §3.4 and
`CLAUDE.md` §4).

### §5.8 — why the `bail_trigger` enum stays small

A small enum keeps longitudinal filtering clean across sessions;
the narrative field is searchable when a finer cut is needed (e.g.,
`jq 'select(.bail_narrative | test("test"))'`). Minting a new enum
value per bail flavor would fragment the aggregate the field exists
to build.

## Consequences

- `TARBALL.md` reads as pure contract; every session's injected
  overhead shrinks with no rule lost. The *why* is one drill-down
  away — here, or in ADR-0010/0011 where it already lived.
- Rationale edits now happen in the ADR layer, where they're
  append-only history, instead of accreting in a doc re-read every
  session.
- Future contract changes should land their rationale in the ADR
  that decides them and their rules in `TARBALL.md`, keeping the
  compression from regressing.
- Pointers in `TARBALL.md` of the form "(rationale: ADR-0013)" bind
  this ADR's section keys above; a future session that relocates any
  of this content must update those pointers in the same response.

## Notes

Rationale that already had an ADR home (probe doctrine → ADR-0010,
clarification design → ADR-0011) was pointed at that home, not
copied here — one home per fact (DOCS.md §9).
