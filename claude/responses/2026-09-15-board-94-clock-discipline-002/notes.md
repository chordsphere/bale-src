# notes.md — 2026-09-15-board-94-clock-discipline-002

Normal response after one clarification round (round 1 asked three
questions; round 2 answered — the ruling is applied below and the
record survives under `.bale/clarifications/`).

## What landed, by outcome

1. **One clock.** `bin/bale` gains `utc_today()`; `next_session_id`
   and `peek_session_id` default to it (the only two `date.today()`
   sites; `parse_session_id` never read a clock). Both request-building
   paths — `cmd_pack` and `bale handoff` — read `datetime.now(timezone.utc)`
   once, pass `today=` from it to allocation and the same instant to
   the stamp, so `sid[:10] == packed_at[:10]` by construction rather
   than by luck at a UTC-midnight boundary. The peek keeps its default;
   its rollover desync is already caught downstream. `bale open` replays
   through `cmd_pack`, so the labelled guess in the brief resolves the
   easy way: one stamp site covers everything.
2. **`packed_at`.** `build_provenance_block` stamps it unconditionally
   (`isoformat(timespec="seconds")` on the UTC instant, the `created_at`
   shape `_created_at_problem` accepts). If a caller lets the default
   clock run and it straddles midnight, a journal line names the
   disagreement — loud, not fatal; the sid stays the anchor. Admitted,
   never required, on the request schema; admitted on the response echo
   (the closed block would otherwise reject a verbatim copy). No
   telemetry schema edit: `attempts[].provenance` is open and
   `attempts[].feedback` untyped. This response echoes a block without
   `packed_at` — one-apply-behind, as the brief said.
3. **Opener.** Two lines ride between the identity and the goal:
   `Packed at <packed_at> (UTC).` and the VERBATIM clock sentence
   (`OPENER_CLOCK_SENTENCE`), each one emitted line with no placeholder.
   The goal line's single-line verbatim carriage is untouched; the
   read-only shape carries both lines too.
4. **TARBALL.md.** §1's Session IDs bullet says the counter's day is
   the UTC day and names `packed_at` and the chat-date trap; a new
   **The clock.** bullet carries the VERBATIM clock sentence. §3.1
   carries the VERBATIM mapping sentence directly under the layout
   block, followed by which manifest fields spell which path and the
   lint's role. `context_included`'s description drops "typically".
   Nothing in PLANNER.md, CLAUDE.md, or DOCS.md.
5. **Lint.** Two checks, one new tier.
   - `context-prefix`: a `changes[]` path equal to `context` or
     starting `context/` → `CONTEXT_PREFIXED_PATH`, a **finding** (exit
     1) — `files/` mirrors the repo root, so bale would land it at
     `<repo>/context/<p>`. A `docs_read` entry with any
     whitespace-delimited token beginning `context/` (surrounding
     punctuation stripped) → `CONTEXT_PREFIXED_DOCS_READ`, a
     **warning**. Entries are free text, so the test is token-based.
   - `dated-artifacts`: per the round-2 ruling. Recognition is
     content-keyed and path-agnostic — any created or modified `.md`
     whose first 20 lines carry `- **Date:** YYYY-MM-DD`. Created: the
     date must equal the sid's date → `WRONG_CLOCK_DATE`, a
     **finding**. Modified: the header is byte-stable under DOCS.md §5's
     two sanctioned diff shapes (the crafter's ADR doc-assertion proves
     that by reverse transform), so the lint never judges it; it flags
     only a dated line (the `DATED` shape, restated from
     `craft_response.py` so the lint stays standalone) whose date is
     later than the sid's — wrong under every clock. **The
     earlier-but-re-dated case is deliberately outside the lint's
     reach:** it has no base bytes, and the doc-assertion is the gate
     that catches it. An unparseable sid date files
     `SID_DATE_UNPARSEABLE` as a warning and the check does not run —
     said, not silent. The **bundle-stem check is dropped entirely, no
     code shipped** (ruling: a bundle never rides inside a response;
     TARBALL.md §3.4 makes it structurally invisible to workers).
   - Warning tier: `finding(..., severity="warning")` / `warning()`;
     the runner partitions into `findings[]` and `warnings[]`
     (`warning_count`), a check whose only output is warnings reports
     `warn` / `[WARN]`, the human verdict appends `(N warning(s),
     non-gating)`, and neither `ok` nor the exit code nor
     `_recompute_mechanical` ever sees a warning.
6. **Version** 0.4.30; the lint's embedded schema refreshed
   (`test_schema_embeds` green).
7. **Tests.** `test_handoff_fixture.py` and `test_per_sid_checkpoint.py`
   predict on the UTC date. `test_pack_opener.py` +2 cases.
   `test_clock_discipline.py` (5): `TZ=Etc/GMT-14` vs `TZ=Etc/GMT+12`
   packs mint the same date — under a local mint those zones never
   agree, so the pin is deterministic at any hour; stamp shape,
   bracketing, sid agreement, and counter keying on pack; the same on
   handoff via `HandoffFixture`; schema additivity.
   `test_lint_clock_and_prefix.py` (12) covers both checks and the tier.

## Validation facts

- **Pre-existing failures, not mine.** `tests/test_checkpoint_provenance.py`
  `HandoffBlindnessGateTest.test_handoff_empty_plan_whole_tree_refuses`
  and `test_handoff_refuses_covering_reading_plan` fail on the unmodified
  shipped bytes: the handoff's include-set refusal ("pack includes name
  the blind checkpoint explicitly") fires before the forecast refusal
  wording the tests assert (`SCOPE_REFUSAL_PHRASE`), and the empty-plan
  case now succeeds where the test expects a refusal. With this
  response applied they remain the only two failures in 226; the
  validation.sh assertion pins exactly that set.
- The self-containment guard (`test_global_doc_selfcontainment`) caught
  "board 94" citations I had put in the lint and schemas — injected
  surfaces must not cite bale-src boards. Removed; a validation.sh
  check keeps them out.
- `validate.sh` on a release-shaped install of the working tree: 83
  pass; the 5 failures are `upgrade.sh` / install `README.md` presence
  and help checks — files the request tarball does not ship, unrelated
  to this change.
- `includes_missing`: the `HandoffFixture` consumer suites
  (`test_handoff_forecast`, `test_handoff_registry_gate`,
  `test_handoff_checkpoint_gates`, `test_handoff_happy`) did not ship,
  so the `peeked_sid` edit is exercised only through
  `HandoffClockTest` here.

## Proposals

- **ADR location doc defect** (ruling: record, do not fix). Three
  injected docs disagree on where ADRs live: DOCS.md §2's table and §5
  say `claude/context/adr/NNNN-*.md`; CLAUDE.md's INDEX table says
  `adr/NNNN-*.md`; TARBALL.md §3.1's `context/` example shows
  `decisions/`. The lint's content-keyed recognizer sidesteps it, but
  the desk should queue a doc row so one spelling wins.
- **Brief over-reach: bundle stems** (ruling: note the strike). Outcome
  5 named "a bundle stem" as a dated artifact the response authors; a
  bundle never rides in a response (TARBALL.md §3.4), so there is no
  surface and the check was dropped. The blind checkpoint carries no
  probe on it.
- **Crafter bundle-stem clock** (out of scope). `--bundle`'s docstring
  recommends `<date>-<slug>` without naming a clock; now that TARBALL.md
  §1 carries the rule, one line can point at it: the date is the UTC
  date, i.e. the authoring session's own sid date.
- **`origin` parity gap** (found in round 1). `response-manifest.schema.json`
  admits the v0.4.24 question key `origin`, but
  `exchange-record.schema.json` and the crafter's `--emit-block`
  validator do not, so an `origin`-tagged clarification is
  tarball-valid and paste-block-refused. The round-1 questions shipped
  without the key. The exchange schema and the crafter's embedded copy
  should admit it, with `test_schema_embeds` extended to the pair.
- **Stats read-side normalisation** (out of scope). Strip a leading
  `context/` from `docs_read` tokens at read time in `bale_stats.py` so
  the three historical records aggregate with the repo spelling, without
  editing them.
- **Retire the loud journal line?** `build_provenance_block`'s
  midnight-straddle log fires only for a caller that lets the default
  clock run after allocating; both shipped callers pass the instant.
  Keep it as defence in depth, or drop it once no third caller exists.
