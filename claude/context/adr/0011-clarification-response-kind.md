# ADR-0011: The clarification response kind for blocking intent gaps

- **Status:** Accepted
- **Date:** 2026-07-07
- **Supersedes:** —
- **Superseded by:** —

## Context

The workflow distinguished two kinds of blocking gap and gave each a
recourse: an **environment gap** (a fact about the architect's machine
or repo) takes a probe (TARBALL.md §4, reworked by ADR-0010), and a
**budget gap** (the goal won't fit the context window) takes a bailout
(TARBALL.md §5.6). A third kind had no wire shape: the **intent gap**,
where the request itself is ambiguous, contradictory, or assumes
knowledge the worker was never given — an undefined term in the goal, a
constraint conflicting with an included file, a decision the packer
made but did not transport.

The contract routed intent gaps to "a conversation in chat." That works
when a human reads the chat; it has no programmatic analog. In the
orchestrated workflow (ADR-0009's horizon), a downstream worker whose
master packed the request badly needs structured recourse, not a dead
end or a guess. Precedent from practice: the first concurrency-ADR
session correctly refused to fabricate rationale it was never given —
the right behavior, with no artifact to carry it.

## Decision

1. **A third distinguished response kind:** `response_kind:
   "clarification"`, structurally the bailout's sibling — empty change
   surfaces, no-op scripts, nothing applied. Contract: TARBALL.md §5.9.

2. **The payload rides in the manifest** as a `questions[]` block, not
   in companion files (a bailout needs `handoff.md`/`diagnostics.json`
   because its content is prose for the next session; a clarification's
   content is structured questions the courier must parse). Per
   question, four required fields: `question` (answerable in one short
   paragraph or less), `context` (what the worker was doing),
   `default_assumption` (what it would have assumed absent an answer),
   and `why_blocked` (why it declined to proceed on that assumption).
   The stated assumption is load-bearing: it lets the planner answer
   "your assumption is correct" and surfaces the worker's reasoning
   for audit.

3. **Questions must be blocking.** Nice-to-know flows through
   `notes.md` Proposals on a full response (TARBALL.md §5.4.1). A
   clarification asserts the session cannot produce trustworthy work
   without the answers.

4. **Apply behavior mirrors the bailout with one deliberate
   divergence: the session stays open.** Bale's apply forks on the
   kind before staging, verifies shape (schema pass plus Python
   cross-field rules: empty change surfaces; `questions[]` required
   non-empty on a clarification and forbidden on every other kind),
   prints the questions banner inline in the walkthrough, preserves
   the manifest, and **retains the lock**. A bailout consumes its
   session; a clarification suspends it — the architect answers in
   the worker's chat and the same sid receives the follow-up normal
   response. `bale unlock` + repack is the escape hatch when the gap
   invalidates the request's framing.

5. **The record lives at `.bale/clarifications/<sid>/NNN.json`**, not
   under `.bale/sessions/<sid>/` — the normal-PASS merge wipes the
   session dir, and the clarification record must outlive the session
   it suspended, since its longitudinal value is aggregation across
   *completed* sessions. `NNN` increments across repeat clarifications
   within one session.

6. **`expects_probe: no` does not forbid a clarification.** The flag
   governs probes against the environment; questions about the
   request are a different recourse.

## Consequences

- Intent gaps now have the same respectable, structured recourse
  environment gaps got in ADR-0010: asking beats guessing, in a shape
  a programmatic courier can carry. More clarifications are expected;
  as with probes, wrong-response frequency is the minimization target,
  not question frequency.
- Clarifications are a signal about the *request*: clustering against
  one packer or one kind of request indicates a packing or
  decomposition problem. The preserved manifests are the aggregation
  surface (jq across `.bale/clarifications/*/*.json`), parallel to
  `diagnostics.json` for bail triggers. A counter field in the bailout
  diagnostics schema was considered and deferred — diagnostics ships
  only with bailouts, so it is the wrong home for a signal about
  sessions that mostly end in a normal PASS.
- Surfaces updated in the session that lands this ADR: TARBALL.md
  (new §5.9, read-paths row, §4.1/§5.1/§5.2/§10.3 cross-references),
  response-manifest.schema.json (enum + `questions` block),
  `bale_validate.validate_response_manifest` (clarification-shape
  rules), `bin/bale` (`_apply_clarification`, the pipeline fork,
  v0.2.10), `bale_report.py` (`print_clarification_banner`,
  `format_dry_run_report` kind-aware signature, the "clarification"
  json outcome).
- Known follow-ups, out of this session's scope: CLAUDE.md §3 still
  says "three response shapes" (now four) and its read-paths table has
  no clarification row; BALE.md's apply-pipeline and contract sections
  (§8, §11) need the parallel design-doc update; `bale status`'s
  "packed" hint could acknowledge an outstanding clarification.
- Foreclosed: treating an unanswerable request as something to guess
  through. A worker that proceeds on invented intent, where a
  clarification was available, is violating policy, not showing
  initiative.

## Notes

The orchestrated answer path (orchestrator answers from its own
context or escalates to the human, then re-prompts the worker) is
doctrine for when an orchestrator exists — ADR-0009's plan — not a
change to the human path. The artifact is identical in both worlds;
only the courier changes, the same courier-agnostic framing as the
probe's TARBALL.md §4.6.

2026-07-13 — implemented in bin/bale by v0.2.10; probe-confirmed 2026-07-13 on bale 0.3.6 (apply fork, .bale/clarifications/ records, banner, lock retention, questions[] schema rules); recorded per the audit cleanup session (2026-07-13-multi-agent-docs-007).
