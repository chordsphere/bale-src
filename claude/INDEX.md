# INDEX.md

> Drill-down map for this project's documentation.
> Updated whenever the inventory changes.

This is bale-src — the source repo for the bale CLI. The project itself
evolves through bale-on-bale sessions, so the doc inventory is small and
will stay that way for a while.

## Tool design

- `BALE.md` (repo root) — the bale tool's canonical design document.
  Covers purpose, scope, command surface, wire format, pack and apply
  pipelines, rollback/revert/unlock semantics, the bale-enforced
  contract (§11), self-applicability, build phases, and open decisions.
  Pull whenever a session touches `bin/bale`, the pack or apply
  pipeline, the staging or lock lifecycle, the wire format, or the
  bale-enforced contract. `bin/bale` references BALE.md directly
  (section references in comments and docstrings) — legitimate,
  since both live in this repo. The global docs deliberately do
  **not**: a `BALE.md` pointer inside an injected doc dangles in
  every other project, so the global docs describe bale's behavior
  generically and cross-reference only their own sections. Don't
  reintroduce a `BALE.md` citation into `CLAUDE.md`, `TARBALL.md`,
  `DOCS.md`, or `CODE.md`. Not injected into requests for other
  projects — it is bale-src's project documentation, peer in
  structure to the global workflow docs but project-local.

## Architectural decisions

This category and its `context/adr/` directory were introduced with ADRs
0001–0005. BALE.md §14 ("Resolved decisions") already
routes new decisions to `context/adr/` per DOCS.md §5 — that pointer is now
live. ADRs are append-only (DOCS.md §7.2): superseded, never edited or
deleted.

- `context/adr/0001-defer-tests-doc.md` — defer the standalone global
  `TESTS.md`; house testing doctrine in CODE.md §13 until a named promotion
  trigger. Status: Accepted. Pull when touching testing doctrine, deciding
  whether `TESTS.md` should exist yet, or planning the v0.4 selftest.
- `context/adr/0002-test-oracle.md` — what decides selftest pass/fail:
  observable contract state (git/fs/lock), narrow golden, no self-grading.
  Status: Proposed. Pull when designing or reviewing selftest assertions.
- `context/adr/0003-selftest-dogfood-depth.md` — two test tiers (unit on pure
  helpers + CLI E2E via `bin/bale` by absolute path); no recursion into the
  real install. Status: Proposed. Pull when building the v0.4 harness or any
  test that drives the CLI.
- `context/adr/0004-test-fixtures.md` — programmatic factories from the
  documented wire format as primary; narrow pinned fixtures for bad/old
  inputs; no recorded corpus. Status: Proposed. Pull when authoring test
  inputs or the fixture layer.
- `context/adr/0005-test-hermeticity.md` — fully sandboxed suite (temp
  `HOME`/`BALE_INSTALL`, no real reinstall, stubbed `$EDITOR`); hard rules on
  the destructive surfaces. Status: Proposed. Pull when building the test
  harness or touching any path that writes outside the repo.
- `context/adr/0006-session-registry.md` — replace the single
  `current_session` lock with a per-sid registry of open sessions plus one
  repo-level integration lock; single-session behavior preserved. Status:
  Accepted (registry landed in v0.3.0; revert/retry/unlock/handoff sid
  disambiguation landed in v0.3.2). Pull when touching the lock lifecycle,
  pack or apply pre-flight, or any concurrency work. First of the four
  concurrency ADRs; its Context carries the motivating goal for the set.
- `context/adr/0007-scope-disjointness.md` — disjoint session scope as a
  mechanical contract: pack-time intersection refusal (includes as a
  conservative proxy) and apply-time collision rejection (the real guard
  against the whole-file clobber). Status: Accepted (landed in v0.3.1 —
  BALE.md §7.1 step 5, §8.1 step 7, §11 rows 3 and 19). Pull when touching
  pack scope projection, apply pre-flight, or any concurrency work.
- `context/adr/0008-checkout-free-integration.md` — integrate via plumbing
  under the integration lock instead of consuming the user's checkout: the
  session commit is built in a temporary index and the no-ff merge is a
  two-parent commit-tree advanced by compare-and-swap (or a fast-forward
  through a clean on-target checkout); the blanket clean-tree requirement
  becomes the narrow tracked-dirty-on-target refusal; HOLD commits to
  `bale/<sid>` and is inspected via branch diff plus the preserved per-sid
  staging. Status: Accepted (mechanism landed in v0.3.5 — BALE.md §7.6,
  §8.1 step 5, §8.2, §8.5, §8.6, §8.8, §9.1, §11 row 8; the ratified
  follow-up session landed the walkthrough/inspection polish and the
  docs sweep, so §1, §3.4, §5, §6.2, §8.3's fidelity caveat, §8.7, §9's
  unlock-vs-revert line, and §10 now narrate the checkout-free
  pipeline). Pull
  when touching the apply pipeline's commit/merge steps, the HOLD path, or
  revert/retry semantics.
- `context/adr/0009-orchestration-doc-plan.md` — defer a standalone
  ORCHESTRATION.md per the ADR-0001 precedent; the doctrine skeleton (seam
  decomposition, blind checkpoints, HOLD triage, escalation, trust phasing)
  is recorded in the ADR; explainer at harness time, global doc when
  orchestration is real. Status: Proposed. Pull when planning orchestration
  or harness work, or deciding whether an orchestration doc should exist yet.
- `context/adr/0010-paste-back-probes.md` — probes default to a strictly
  read-only paste-back block (sentinels, bounded output, integrity trailer)
  and the engagement doctrine flips to default-to-ask: the worker treats the
  architect's environment as its own, and working around missing context is
  a policy violation. File-based probe-output/ survives as the fallback.
  Status: Accepted (landed in the global docs and the pack help text — the
  TARBALL.md §4 rewrite with its cross-references aligned, CLAUDE.md's
  probe-posture lines, the previous_probe schema description, and the
  --expects-probe help text; no behavioral CLI changes). Pull when touching
  the probe contract, probe posture language in the global docs, or the
  future probe tool-call surface.
- `context/adr/0011-clarification-response-kind.md` — a third distinguished
  response kind for blocking intent gaps: `response_kind: "clarification"`
  with a manifest `questions[]` payload (question / context /
  default_assumption / why_blocked), bailout-sibling shape, apply surfaces
  the questions and retains the lock (the session stays open), records
  preserved under `.bale/clarifications/<sid>/`. Status: Accepted (landed
  in v0.2.10 — TARBALL.md §5.9, the response-manifest schema, the
  clarification-shape validation rules, and the bin/bale apply fork; the
  CLAUDE.md §3 and BALE.md §8/§11 follow-ups named in the ADR remain open).
  Pull when touching response kinds, the apply fork, the response-manifest
  schema, or intent-gap doctrine.
- `context/adr/0012-agent-driven-substrate.md` — the agent-driven
  direction ratified: bale is a substrate an orchestrating Claude can
  drive; standing commitments (transport-agnostic CLI, role-neutral
  planner/worker/operator language, manual workflow as fallback and
  ground truth); explicit that no orchestration harness exists yet.
  Complements ADR-0009, whose doc plan and promotion triggers stand
  unchanged. Status: Accepted. Pull when planning orchestration or
  harness work, or when a session needs the ratified direction rather
  than ADR-0006's motivating context.

ADRs 0002–0005 and 0009 are Proposed pending the architect's
ratification on review; 0001, 0006, 0007, 0008, 0010, 0011, and 0012
are Accepted.
0006 and 0007 landed as the designed pair (the registry in v0.3.0, the
disjointness contract in v0.3.1) and were flipped to Accepted with the
0007 landing; 0008 was ratified for implementation and landed in v0.3.5
(flipped to Accepted with the landing, per the 0006/0007 precedent);
0010 and 0011 each landed in its own session (0010 in the
global docs and the pack help text, 0011 in v0.2.10) and were flipped to
Accepted together on ratification; the 0006/0007 and 0010/0011 status
flips reached the ADR files themselves in the 2026-07-13 audit cleanup
session (0010/0011 on the architect's explicit scope override,
probe-confirmed), which also recorded 0012 (Accepted at creation — the
direction was stated by the architect directly). The remaining
Proposed set is
unimplemented: 0002–0005 precede any test code, and 0009 defers the doc
it is about.

## Explainers

- `context/bale-internals.md` — how `bin/bale` is structured (commands,
  control flow, configurables), the `bale.toml` schema, and the hook
  contract. Pull when a session touches `bin/bale`, the configurables
  mechanism, or a new hook.
- `context/meta-sessions.md` — the recursive properties every bale-src
  session inherits from working on bale itself: the one-apply-behind
  fixed-point, `bin/bale` as both tool and artifact, the reinstall loop
  that closes the recursion. Pull when packing or reviewing a session
  that touches `bin/bale`, the apply or pack pipeline, the staging
  lifecycle, or the `post_apply_pass` hook.

## Notes on this index

The global docs (`CLAUDE.md`, `TARBALL.md`, `DOCS.md`, `CODE.md`) ship from
the bale installation and are injected into every request; they are not
listed here. `BALE.md` is listed because it lives in this repo and is the
canonical design reference for the bale tool — it is project
documentation for bale-src, not a global workflow doc, and is not
injected into requests for other projects.

Routing — when a session is authoring or emitting a `bale pack` command
(a rescope offer per `CLAUDE.md` §11.2, or helping the architect by
request), the canonical flag/format surface is `TARBALL.md` §3.4; cite
it rather than reconstruct the command from `bin/bale`'s pack argparse
parser, which carries a pointer comment to the same section. That
emission is pre-work only: once a session has landed work, follow-up
suggestions are prose Proposals (`TARBALL.md` §5.4.1), never runnable
commands (`TARBALL.md` §5.5). This is a cross-reference into an
injected global doc, not an inventory entry — the global docs are not
listed here (see above).

Per DOCS.md §4.1, INDEX.md is usually introduced once a project has ~3+
findable docs. This one was introduced early, on architect's call so the
scaffolding would be in place when more arrived. The current inventory
is BALE.md, two explainers, and twelve ADRs (0001–0005 the first in the
project — the ADR category was introduced in the same session that added
them, per DOCS.md §4.1/§4.5 — 0006–0009 the concurrency-architecture
set, 0010 the probe-doctrine flip, 0011 the clarification response
kind, and 0012 the agent-driven direction). Testing doctrine itself lives in the global
`CODE.md` §13, not as a project doc; it is not listed here for the same
reason the other global docs aren't (see above). Further explainers will
likely arrive alongside the apply search-paths mechanism, a new hook, or
the v0.4 selftest harness.

BALE.md is a category-of-one for bale-src: structurally peer to the
global workflow docs (own META + INDEX + numbered sections) but
project-local and not injected. DOCS.md's inventory table doesn't get
a new row for it because adding bale-src-specific categories to a
project-agnostic doc would itself be the wrong direction; this hint
here in `INDEX.md` is the discoverable surface.
