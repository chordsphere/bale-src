# bale master-session state — v4 — 2026-07-31

Handoff document for the bale-src master session. Purpose: re-seed a
fresh master-session chat with zero loss. To use: state current
progress against this file and continue. Regenerate at major
milestones. v4 supersedes the v3 (2026-07-25) doc in place; nothing
from it needs to be carried separately — v3 lives in git.

This document lives IN the repo at `claude/MASTER.md`, listed in
`INDEX.md`. Regenerate = edit in place; git keeps the history. It is
a project doc, not a global workflow doc — see §5 for the
categorization contract.

Last landed by: `2026-08-07-sitting-close-deltas-007`.
(This line is edited in place at each landing, never appended to.)

Going-forward convention (recorded once, effective v4): sittings
write `claude/telemetry/` records, board rows, evidence entries, and
§5 contracts; no per-sitting narrative accretes in §2; this header's
last-landed-by line is edited in place.

## 1. Ultimate goal (unchanged, ratified — do not re-litigate)

The architect writes a spec doc for a full-scale application, bales
it to Claude, and Claude decides everything needed to accomplish it —
spawning trusted worker sessions, possibly sub-master sessions — with
the architect worrying about WHAT gets built, not HOW.

**The ratified floor:** human checkpoints converge on four
"what"-shaped controls — ratify decompositions, answer escalations,
review final merges, grant trust expansions. Everything below goes
autonomous per work class as the trust ledger earns it. The dominant
observed failure class is MISUNDERSTANDING, which mechanical
validation structurally cannot catch; these checkpoints are its
control surface. Validation checkpoints are authored blind — by the
planner from the request, never by the worker building against them.

Two independent axes, kept independent: SCHEDULING (sequential vs
concurrent — CLI work, COMPLETE) and TRANSPORT (human-carried
tarballs vs API harness — a separate component that uses bale). The
CLI stays transport-agnostic; the manual path remains fallback and
ground truth.

## 2. Milestones

Per-arc residual summaries. The per-sitting log this section carried
through v3 is condensed out, the v2→v3 precedent executing again:
condensed pre-v4 history lives in git (v3 of this document) and in
`claude/telemetry/` (per-session records; sids cited on the board
rows); contracts from it are §5, evidence is §6, finding
traceability is §8. Sittings no longer accrete narrative here — see
the header convention.

**The concurrency arc — COMPLETE** (v2 milestone, carried). ADRs
0006, 0007, 0008 Accepted and landed: per-sid registry, scope
disjointness (pack-time include-intersection refusal + apply-time
sibling-scope collision rejection), checkout-free integration,
per-sid staging with ownership-by-open-session cleanup — exercised
live with three scope-disjoint sessions before any harness consumed
it (the proven-by-hand model). Condensed pre-v2 history lives in git
and the session archive; contracts from it are §5.

**The global-doc mechanization / worker-toolkit arc — CLOSED**
2026-07-31 (boards 22 + 31; per-phase sids on the board rows).
Where a contract rule is shape it now lives in a worker-shipped
tool — `tools/craft_response.py` (manifest skeletons for all three
response kinds, the probe scaffold, the validation epilogue and
exec-bit assertions) and `tools/response_lint.py` (the §10.1
self-check and the feedback-mechanical emitter) — and TARBALL.md
keeps trigger + tool pointer where reconstruction prose used to be.
The judgment residue (probe-vs-guess, fit estimates, claim
completeness, stay-in-lane) remains prose by design; boards 4/5/6
are its control surface. The ratified pattern is §5's
mechanize-shape contract.

**The lifecycle-telemetry arc — CLOSED** across the 2026-07-28
through 2026-07-31 sittings (boards 24–30; sids on the board rows).
Every session exit now leaves a durable record: the read-only
session shape (empty recorded scope; masters-never-self-land is
mechanical), closure records with reasons on unlock and revert,
split supersession with stamped lineage, rollback/--undo telemetry,
unlock and revert --json parity, and the crafter's injection
consolidated into INJECTED_TOOLS. v0.3.15 → 0.3.19 across the arc.
The telemetry corpus stops being numerator-only (evidence 38's
counter).

**The trust-ledger arc — CLOSED 2026-08-03** (board 5; six sids:
design/orchestration `2026-08-01-board-5-ledger-design-004`
(read-only), `2026-08-01-board-5-telemetry-promotion-005`,
`2026-08-01-board-5-bale-stats-006`,
`2026-08-01-stats-packaging-closeout-007`,
`2026-08-03-stats-residual-bucket-002`,
`2026-08-03-preserved-at-and-retag-003`). Version range 0.3.22 →
0.3.27 across the arc (a claim to verify; per the arc's upward
report — see the §2 version paragraph's check-note for this
sitting's verification). First live run of the ledger: doc work is
the first autonomy-grant candidate; contract-doc is where the noise
concentrates — the misunderstanding-as-dominant-failure-class
corroboration, at the ledger's own surface.

**The blind-checkpoint arc — CLOSED 2026-08-05** (board 6; five
sids: design/orchestration
`2026-08-04-board-6-blind-checkpoint-design-003` (read-only),
`2026-08-04-board-6-checkpoint-core-004`,
`2026-08-04-board-6-superset-gate-005`,
`2026-08-04-board-6-blindness-enforcement-006`,
`2026-08-05-board-6-stats-read-side-001`). Version range 0.3.27 →
0.3.29 across the arc, sessions A and B landed unbumped at 0.3.27
(the first cadence divergence — §6 entry 54 carries it and the open
doc-only ruling). The §1 floor's "validation checkpoints are
authored blind" line now has its implementation — home, execution,
gate, blindness enforcement, and ledger read side (the arc's upward
report, shipped in `claude/context/board-6-arc/`). The 1.0.0 gate's
board-6 dependency is satisfied; the gate now waits on board 10 and
the first exercised autonomy grant (§5's ladder contract, wording
unchanged there).

**Current version:** one home — §7's bin/bale landmark (collapse
ratified 2026-08-07; the standing rule stands: verify with
`bale --version` at each sitting's open).

**v4 regeneration (this compression sitting's record).** The
2026-07-31 doc-compression sitting: the read-only orchestrator
session `2026-07-31-doc-compress-011` read v3 whole and authored the
ratified v4 brief; this session,
`2026-07-31-master-v4-regeneration-012`, landed the regeneration —
the sitting log collapsed to these arc summaries, live state
one-homed, INDEX.md history prose trimmed in the same pass. This
session is the sitting's deltas vehicle; no separate deltas pack
follows unless post-landing ratification changes something. It did,
microscopically: 012 applied clean and its notes were ratified as
shipped in the sitting chat; the ratification closed via
`2026-07-31-master-v4-ratification-microdeltas-013` (this record,
the re-homed registry rides, evidence 46). 012's mid-session
compaction was disclosed and covered both ways — the worker's
post-compaction re-verification per CLAUDE.md §11.6, and the
master's independent full read of v3 at review. [Correction,
2026-07-31: 013 executed the pre-revision micro-deltas brief, not
the revised one, so the board-33 recording ratified in the sitting
chat never reached the tree at 013; it landed at
`2026-07-31-board-33-recovery-015` under the continue-plan-014
sitting (evidence 47).]

## 3. In flight

- **The board-10 tidy-up sitting (2026-08-05/06, master
  `2026-08-05-discuss-harness-011`) is closed.** Bucket A ratified
  in chat: the four ADR flips (0002–0004 and 0009 — all fourteen
  ADRs now Accepted), the cadence ruling (§5), and the
  operator-friction-charter fold-in (state legibility onto board
  10; the charter is closed). Bucket B landed:
  `2026-08-06-handoff-covering-001` and
  `2026-08-06-sweep-json-stats-002` (§6 entries 55–56; the version
  trail is §2's). The sitting-close deltas — this landing — carried
  the cargo.
- **Next, in order:** the sandbox ADR (the ADR-0005 extension),
  then the board-10 spec-intake sitting. Board-35 gaps 3–7 remain
  available as concurrent filler under the new model where
  forecasts stay disjoint.

**Watches** (named re-triggers, no work; the first four carried
verbatim from the board-5 arc's upward report, the next three from
the board-6 arc's, one from `2026-08-05-auto-sweep-009`'s notes,
and the last two from the board-13 arc):

- Emitter-parser reconciliation drift: all three unparsed-
  reconciliation records are 2026-07-31 consolidation-day straddlers;
  everything post-consolidation parses. Re-trigger: any non-zero
  unparsed share in `stats --since 2026-08-01`.
- Drift-guard tag-reuse blindness (fires on tag-ahead, not reuse);
  bit once (002/007 collision, repaired). Re-trigger: third
  occurrence earns the guard a per-session-bump check.
- Mixed `at` provenance in clarification records (pre-0.3.27 read
  via mtime). Re-trigger: a stats consumer comparing per-record `at`.
- Closure-mix membership revisit. Re-trigger: real unlock-closure
  stamp accrual.
- The ledger cannot yet distinguish predicted-grounds claims from
  observed ones (the §5 claim-basis precedent's measurement gap).
  Owner: board 10 — ratified 2026-08-04, master disposition 3, per
  the rev-B brief's D4.3: "board 10 owns it, for three recorded
  reasons" (the reasons live in D4.3; the brief is shipped in
  `claude/context/board-6-arc/`). Re-trigger: board 10's decision
  on the additive claim-basis self-report field. One live datum
  already on that desk: session A's predicted packaging-suite claim,
  graded `agree` at apply.
- Removed-oracle residue: flips log-to-refusal on the first observed
  worker-authored edit to `[validation]` keys in a merged session
  (C's else-branch note makes it ~10 lines).
- `[validation]` layering: the deferred widening re-triggers only on
  a case that answers oracle-by-coincidence (disposition 1's trade,
  recorded in the rev B brief's D1).
- Required-set keyed form: re-triggers on systematic per-class
  `[SKIP]` noise in the ledger's new rows.
- Sweep current-branch commit skip predicate (a two-line change,
  named in `auto-sweep-009`'s notes). Re-trigger: the first
  observed off-target-checkout confusion.
- Plan-less handoff whole-tree refusal friction: a bailout whose
  reading plan cites no files resolves to whole-tree scope, so in a
  checkpoint-configured project every plan-less handoff now
  requires the admission flag. Shape kept deliberately (whole-tree
  really is covering; it mirrors a default whole-tree pack).
  Re-trigger: the first real-world plan-less handoff refusal; then
  decide fallback breadth vs. remedy text.
- Sweep stamp deferral: no telemetry stamp of sweep results, by
  reasoned deferral (§6 entry 56). Re-triggers, either
  independently: demand for longitudinal committed-sweep data
  builds the git-log-derived stats view (no schema change needed);
  demand for sweep-skip rates reopens the stamp question with
  fresh eyes.
- Read-staleness (board-13 design brief I.6; the separation's
  named price): a sibling may land inside an open session's read
  set. Re-trigger: post-epoch HOLDs clustering in the
  opened-before-a-sibling-landed-inside-its-read-set class; remedy
  shape if it fires is a data-gated pack-time warning, never a
  refusal.
- Forecast precision (accruing from the first post-epoch apply):
  drift clustering = forecasts too narrow; imprecision clustering =
  too wide; both packer-side signals. Three reading caveats from
  `2026-08-07-board-13b-epoch-ledger-005`'s archived notes (its
  early-forecast-signal proposal), cited not restated:
  refusal-then-admit double-counts drift; default packs read
  precision 1.0 by construction; per-attempt counting over-weights
  retried sessions.

**Fold-in registry** (one home, this list — the dated block v3
carried inside §2's 07-16 sitting summary is merged in; each entry
below was reconciled against shipped bytes at the v4 regeneration,
with the unverifiable ones carried verbatim and marked):

- run_hook's three placeholder-less f-strings — rides any session
  touching bin/bale section 23. Cosmetic.
- The reconciliation label-column cap (008's proposal, accepted) —
  rides the next session touching tools/craft_response.py. [Carried
  unchanged; unverified this sitting — same MASTER.md-only limit.]
- **`bale handoff --verbose` for its tarball build.** What: a
  `--verbose` flag on handoff passing `verbose=True` into its
  `build_request_tarball` call. Why: the build-trail machinery is
  in place with a default-off kwarg; handoff builds the same quiet
  tarball pack does. Recorded in §5.4's updated bullet as the one
  remaining candidate surface. Scope hints: bin/bale §22, the
  handoff subparser in §26. (Accepted 2026-08-06 from
  `2026-08-06-verbose-thread-close-005`'s Proposals, text verbatim;
  rides the next session touching bin/bale §22 or the handoff
  subparser, §26.)
- `claude/context/bale-internals.md` §2.5 schema-snippet true-up —
  whether the snippet-not-extended precedent ([staging] v0.3.7,
  [identity] v0.3.8, followed consistently by board-6 sessions A–C,
  so the eventual true-up is a single sweep) is policy or accident;
  the question is recorded, not answered. The same carrier gains
  the §4 sweep config row (one internals sweep, same carrier as
  the §2.5 true-up; source: `2026-08-05-auto-sweep-009`'s notes).
  Rides the next small doc session touching that file. (Source:
  session A's notes and the board-6 arc report's on-watch line.)
- The checkpoint exit-2 stats split — an additive
  `checkpoint_errored_attempts` count (stamp `exit_code == 2`)
  beside the HOLD count; v1 folds the planner's-artifact-errored
  case into checkpoint-HOLD, which is right for the
  misunderstanding rate but hides oracle fragility from the ledger;
  the stamp preserves `exit_code`, so the read side can split later
  with no write-side change. Rides board 10, on its harness asking
  the question. (Source: session D's notes proposal.)
- The additive json `sweep` object plus stats read side
  (accepted-recorded from `2026-08-05-auto-sweep-009`'s notes),
  session authorable on request — a natural early customer of the
  board-10 era. Rides board 10. [2026-08-06: the write side landed
  at `2026-08-06-sweep-json-stats-002` (§5's contract, §6 entry
  56); the stats read side deferred with the stamp question per
  the charter's conditional — the deferral is a §3 watch.]
- Pack-json `sweep` key, list-shaped (the read-only sweep can
  close several sids; supersession close rides too). Plumbing
  landed at `2026-08-06-sweep-json-stats-002`
  (`close_session_with_record` 3-tuple; pack's callers currently
  discard). Carrier: the next `bale_pack.py` or pack-json touch,
  or board 10's json-surface enumeration, whichever first.
- Crafter epilogue separable fragments — same carrier as the
  label-column-cap entry above (the next
  tools/craft_response.py touch). Text verbatim from
  `2026-08-07-board-13c-contract-docs-006`'s notes: "The crafted
  validation epilogue emits its `reconcile_claims` call inline at
  the end of the pasted fragment; pasted before the checks per its
  own instruction, that call fires early. I removed the early call
  and kept the end-of-script one. Possibly worth a crafter tweak
  (emit the definitions and the call as separable fragments);
  flagging rather than proposing formally since it may be
  deliberate."
- BALE.md §7/§7.2 includes-as-scope true-up — rides the next
  BALE.md-touching session. Text verbatim from
  `2026-08-07-board-13c-contract-docs-006`'s Proposals: "**What:**
  True up BALE.md's own §7/§7.2 prose wherever it still describes
  includes as the gated scope, if session B's sweep does not
  already cover it. **Why:** This session's sweep was confined to
  its two-file forecast; I could not verify BALE.md (shipped
  read-only, session B's forecast) agrees with the revised
  TARBALL.md §3.4 rows that point into it. **Scope hints:** BALE.md
  §7.2 (`--read-only`, `--supersedes` semantics); only after B
  lands, to avoid restating what it already fixed."
- TARBALL.md §5.2.2 gains a `forecast_departures` sentence — rides
  the next TARBALL.md-touching session. Source:
  `2026-08-07-board-13b-epoch-ledger-005`'s notes, the
  "Coordination with session C" paragraph — TARBALL.md was session
  C's forecast (mechanically refused at B's apply) and C's E1
  charge did not cover §5.2.2, so the feedback-block walk-through
  does not yet mention the field; the schema description carries
  the full contract meanwhile.
- Post-epoch stats-corpus fixtures — rides board 35 (the next
  test_stats_aggregation.py touch). Text verbatim from
  `2026-08-07-board-13b-epoch-ledger-005`'s Proposals: "**What:**
  Add one or two post-epoch fixture records (carrying `scope_kind`,
  a forecast, drift, an admission, and a `forecast_departures`
  block) to `tests/fixtures/stats_corpus/` and extend
  `test_stats_aggregation.py`'s hand-derived assertions to cover
  them. **Why:** The full-corpus test whole-dict-asserts the corpus
  counts, so adding fixtures perturbs nearly every expectation in
  that file — too invasive to ride along this session. My new suite
  seeds its own synthetic corpus instead, which covers the
  semantics but leaves the shared corpus wholly pre-epoch. Folding
  the shapes in when that file's expectations are next touched
  anyway keeps the one-corpus doctrine whole. **Scope hints:**
  `tests/fixtures/stats_corpus/`, `tests/test_stats_aggregation.py`;
  no source changes."

Cleared at this landing (`2026-08-06-sitting-close-deltas-008`),
both from the board-34 arc: the revert staging-row → bale_report
entry — landed at `2026-08-06-verbose-thread-close-005` [2026-08-06:
one addition beyond the accepted shape — the return dict grew
`staging_error`, the rmtree OSError text, internal-only; the
`--json` key contract untouched]; and BALE.md §13's
citation-qualification entry — landed at
`2026-08-06-v04-selftest-audit-006` (the mandated edit plus four
sweep fixes), its one sanctioned exception, the cut-condition
paragraph's bare §7.4, resolved at `2026-08-06-v040-cut-007` by
qualification; the v1.0 "(MASTER.md §1)" reference kept per the
recorded lean, revisit point unchanged (ADR-0009/board-10).

Cleared at this landing (`2026-08-03-master-deltas-005`): the
BALE.md §8.9 outcome-list sentence (`scope-drift-refused`) +
drift-refusal aggregation semantics entry — landed at
`2026-08-01-board-5-telemetry-promotion-005` per the arc's upward
report (a claim; the sentence fold-in is named in the report's
landed list).

Cleared at the v4 regeneration: the board-27 TARBALL.md §3.2
context_included-vs-recorded-scope entry — the injected TARBALL.md
already carries the sentence (§3.2: the tarball ships the flat file
list while the recorded scope lives repo-side in the registry;
verified at line 1108 of the copy injected into this session's
request).

Cleared at this landing (`2026-08-01-master-deltas-002`): the
BALE.md §8.9 retitle entry — verified pre-landed: the shipped
BALE.md heading at line 1575 already read "Telemetry record at
session close" when checked at the 2026-07-31 third sitting
(master verification, `continue-plan-016`).

Landed 2026-08-05, non-board (`2026-08-05-auto-sweep-009`, 0.3.32):
`[apply] sweep`, default-off, the architect opted in at the global
layer beside `archive_dir`; the manual telemetry/archive dance is
retired (standing fact: §7). Ratified judgment calls, one line
each, dated 2026-08-05 at the master desk:

- Rollback and `--undo` joined the trigger set: the first sweep
  makes records tracked, and rollback's append would strand a
  modified-tracked file against the untracked-only carve-out — the
  worker's catch; the carve-out stays conservative.
- Continuing states accumulate into one closure commit, with
  `closure_reason` as the commit event.
- Sweep commits land on the current branch.
- The malformed-key refusal/skip asymmetry is deliberate:
  pre-flight refusal on apply, loud never-fatal skip on post-hoc
  commands.

Ratified judgment calls, one line each, dated 2026-08-06 at the
master desk (the board-34 arc: 005 =
`2026-08-06-verbose-thread-close-005`, 006 =
`2026-08-06-v04-selftest-audit-006`, 007 =
`2026-08-06-v040-cut-007`):

- Unconditional `--verbose` forwarding onto validation.sh's argv on
  the verbose path — loud-and-recoverable over silent probing (005).
- The blind checkpoint stays flagless: no TARBALL.md §7.4 contract
  on its argv (005).
- `staging_error` accepted as an internal machine fact (005).
- The 0.4.0 cut proceeds on the audit alone — the ladder's gate is
  the audit; gaps ride forward recorded (006).
- The BALE.md §7.2 stale "§5 authorship line" pruned (006, landed
  007).
- install.sh joins the suite-run baseline (006).
- The cut-paragraph §7.4 qualified rather than absorbed, and the
  audit sid named in BALE.md §13 per the TARBALL.md §5.5
  retiring-session precedent (007).

Ratified judgment calls, one line each, dated 2026-08-07 at the
master desk (the board-13 arc: 004 =
`2026-08-07-board-13a-forecast-surface-004`, 005 =
`2026-08-07-board-13b-epoch-ledger-005`, 006 =
`2026-08-07-board-13c-contract-docs-006`):

- Status omits the include-set row — the session block answers
  "what is enforced" and includes no longer are (004).
- Typed `--write` skips the wizard's read-only half of the
  session-shape exchange (004).
- The `checkpoint_scope_admitted` description true-up accepted —
  in-scope beyond the pin list, enumerated (004).
- The read-side refusal keys on declared includes, not walked
  files (004).
- No migration code for pre-separation open sessions; the refusal
  text carries the transition (004).
- The bale_stats containment mirror stays, with its subprocess
  drift guard; restructure re-triggers on a third helper home
  (005).
- Rate units as shipped: admission path-granular, precision
  entry-granular, denominators beside rates (005).
- The duplicate gate fires on identical path strings, matching the
  lint's basis; conflicting duplicates refuse earlier at row 32
  (005).
- CLAUDE.md §6 cites ADR-0015 — TARBALL.md's citation convention
  as precedent (006).
- The ratified kernel elaborated, not quoted (006).
- The convention paragraph's bold lead renamed after a citer check
  (006).
- The sweep read the conflation class wider than literal
  concurrency assertions (006).
- "scope" survives as the concept's name (006).

## 4. The board

Ordering is the recommended sequence; small sessions first, the
compression sitting before harness scoping. Item numbers are
identities, not sequence — they are cross-referenced from §5, §6,
and §8, so done items keep their numbers as one-line pointers.

1. **staging-from-target-base — DONE** 2026-07-13/14 sitting
   (pre-telemetry; home: git): target-base strategy landed,
   config-only opt-in, tracked-at-tip guard.

2. **drift-to-contract apply gate — DONE** 2026-07-15 (sid
   `2026-07-15-drift-gate-002`; telemetry): own-scope apply gate
   landed, v0.3.10.

3. **pack no-brief guard — DONE** 2026-07-13/14 sitting (rode
   telemetry B1; pre-telemetry, home: git): the --no-readme
   acknowledgment, TTY/piped split per BALE.md §7. The evidence-11
   failure class now has its mechanical counter.

4. **Feedback telemetry + response lint — DONE** 2026-07-13/14
   sitting, in three sessions (pre-telemetry — B2 itself created the
   corpus; home: git): response-lint (the blind-authored
   lint, injected per request), telemetry B1 (dual-stream feedback
   block + day-one provenance stamping, per the §5 constraints), and
   telemetry B2 (durable records at `claude/telemetry/`, BALE.md
   §8.9). The response-lint prose savings banked in the compression
   sitting (board 7).

5. **bale stats / the trust ledger — DONE** 2026-08-03, closed as
   an arc (design/orchestration
   `2026-08-01-board-5-ledger-design-004` read-only, plus applied
   sids `2026-08-01-board-5-telemetry-promotion-005`,
   `2026-08-01-board-5-bale-stats-006`,
   `2026-08-01-stats-packaging-closeout-007`,
   `2026-08-03-stats-residual-bucket-002`,
   `2026-08-03-preserved-at-and-retag-003`; telemetry; v0.3.22 →
   0.3.27 per the arc's upward report). The ledger is operational and already
   signaling: first live run classed the corpus per work class, doc
   is the first grant candidate, contract-doc concentrates the
   noise (§2's arc summary; consumer surface `stats --json`, key
   contract owned by `format_stats_json`'s docstring — board 6/10
   input). Annotation dispositions: rollback guard — landed at 005,
   disregards untracked claude/telemetry/; reverse lineage — landed
   as the pack-stamped `superseded_by`; evidence-41 stamp — was
   already landed at board 33; §8.9 sentence fold-in — landed at
   005; the deferred HOLD multi-attempt E2E — landed at 005 per the
   report. The bailout-banner telemetry-row rider is
   presumed-landed-with-005 — the ratified "banner-order alignment
   for bailout" strongly implies it but the report never confirms
   it explicitly; unverified from a MASTER.md-only request,
   recorded as inference, not fact. Design constraints and the
   mechanical/self-reported trust split: §5 (ratified 2026-07-13),
   unchanged.

6. **Blind validation checkpoints — doctrine to mechanics — DONE**
   2026-08-05, closed as an arc (design/orchestration
   `2026-08-04-board-6-blind-checkpoint-design-003` read-only, plus
   applied sids `2026-08-04-board-6-checkpoint-core-004`,
   `2026-08-04-board-6-superset-gate-005`,
   `2026-08-04-board-6-blindness-enforcement-006`,
   `2026-08-05-board-6-stats-read-side-001`; telemetry; v0.3.27 →
   0.3.29 per the arc's upward report, sessions A and B landed
   unbumped at 0.3.27 — §6 entry 54). Four sessions landed, none
   reverted; the §1 floor's "validation checkpoints are authored
   blind" line has its implementation — home (`[validation] base`,
   project-only), base-tree blind execution, the step-15 superset
   gate (`[validation] required`), blindness enforcement (pack-side
   covering refusal, provenance stamp, registry-copy verification),
   and the ledger read side. Design ratified 2026-08-04 (rev-B
   brief, shipped in `claude/context/board-6-arc/` with the upward
   report and all four sessions' notes); the sub-master's
   ratified-at-level list reviewed and uncontested by the master
   2026-08-05. Escalations disposed: the execution-context
   amendment landed (`execution-context-amendment-006`; §5's
   amended contract); the TARBALL.md §7 sentence landed this
   vehicle (disposition 2); the §3 watch re-owner landed this
   vehicle (disposition 3); the handoff-covering mechanism ratified
   (§5, this sitting); the operator-friction arc transferred to its
   own read-only master session (§3). Coexistence contract and
   motivating evidence: §5 (ratified 2026-07-13), unchanged.

7. **Doc compression sitting — editorial phase COMPLETE**
   2026-07-15/16, three sessions after a ratified split (sids
   `2026-07-15-tarball-ux-extraction-011`,
   `2026-07-15-tarball-compression-012`,
   `2026-07-16-claude-preflight-compression-001`; telemetry):
   apply-time UX moved to BALE.md §8.10; TARBALL.md −4.9%;
   CLAUDE.md §11.2 −57%. The 35–45% pair target RETIRED as
   mismeasured (evidence 26); injection-tax work moved to board 14
   (since retired → board 10); the doc-gap pile moved to board 15.

8. **shrink-bin/bale arc — CLOSED** 2026-07-16, three sessions
   serialized on bin/ (sids `2026-07-15-docstring-prune-005`
   v0.3.11, `2026-07-15-pack-path-extraction-010` v0.3.12,
   `2026-07-16-apply-path-extraction-002` v0.3.13; telemetry):
   docstring cut to job + index header (version narrative dropped
   per §5), bale_pack and bale_apply extracted, bin/bale 5,981 →
   4,111 lines, sibling lazy-import idiom refined (sibling-owned
   entry points imported from owning modules, not __main__).

9. **Cross-project ADR + implementation** — LINKED sessions, not
   fused. Level 1: --link, shared link id, same interface-contract
   brief into both requests (the seam MUST be named). Level 2:
   cross-repo depends_on. Level 3 (two-phase commit): deferred,
   likely forever.

10. **Harness scoping master-session** — spec-intake ritual
    (decomposition + ambiguity questions + checkpoint plan ratified
    BEFORE anything spawns), escalation contract as schema, promotion
    of the orchestration-doctrine doc; then harness build + phased
    trust rollout; recursion depth earned last. **Named agenda items
    added from the 008 audit:**
    - **Sandbox validation.sh execution** — today it is worker-
      authored code run via bare subprocess in staging with the
      operator's privileges, network on, filesystem open, writes
      self-declared. Fine while a human reads every script; a
      non-negotiable prerequisite for unattended workers (network
      off, FS confined to staging). ADR-0005's hermeticity doctrine
      knows why; it doesn't yet cover this surface.
    - **MASTER.md category promotion** — this doc is a project doc
      today (see §5); when masters multiply, the master-handoff
      category wants the ADR-0009 staging treatment (explainer at
      harness time, global doc when orchestration is real), a pinned
      shape, and eventually a lint.
    - **Injection-model decision gates physical doc splits** —
      system-prompt injection (bytes are tokens; file granularity is
      the only knob) vs tool-access lazy reading (today's economics,
      preserved). Any physical split of the globals, the retired
      board-14 shape included, is decided only after this choice is
      made here; evidence 32 carries the rationale. The 2026-07-21
      packaging reference map lives in v3 of this doc, in git, if a
      physical split is ever revived.
    - **Orchestrated accept spelling for --supersedes** (parked
      2026-07-29) — piped packs can never complete a supersession;
      correct until the authorship contract for worker-emitted
      commands is revisited here.
    **Added at the board-10 tidy-up sitting (2026-08-05/06):**
    - **Operator state legibility** — folded in from the closed
      operator-friction charter (its remainder; evidence 53's
      corrective). With it, the status-rendering observation:
      open-session absence is signaled only by silence — a
      candidate for an explicit open-count line when status
      becomes the orchestrator's ground truth.
    - **ADR-0009 Accepted arms its step-2 trigger** — draft
      `claude/context/orchestration.md` when harness work starts —
      at the spec-intake sitting.
    **Added 2026-08-06 (from the architect, at the board-34
    sitting close):**
    - **The escalation contract subsumes worker→master
      clarification relay** — today intent questions flow worker →
      architect → master → architect → worker via TARBALL.md §5.9's
      clarification response, with the architect as transport; the
      harness-era design should carry that channel with the
      architect moving from transport to overseer.

11. **Deferred/when-ready:** v0.4 selftest harness pins the
    merge/HOLD banner strings (now load-bearing — BALE.md cites
    them); next-prompt.md renderer-tuple + §6.2/§8.1 legacy-note
    removal once pre-retirement archives stop mattering; lift the
    generated-artifacts session's craft_response recipe (init repo →
    pack → craft a §5.2-shaped response programmatically → apply)
    into the ADR-0004 fixture layer when the v0.4 harness lands —
    its response-manifest schema-shape assumption becomes
    mechanically checked at that point. Precondition intact:
    ADR-0002–0005 ratified first.
    Added this sitting, same v0.4-harness bucket: the staging
    session's two assertion clusters + the diverged-checkout E2E;
    response-lint's 17-fixture factory as seed corpus.
    Deferred this sitting: --staging-strategy per-invocation escape
    hatch (need-gated); a between-applies drift check (packaging
    run-2 proposal: a standing hook or convention running build.sh's
    guards between applies); validate.sh layout-rows mechanization
    (recorded deferred in packaging-v2's manifest).
    Added 2026-07-15: per-sid stage-time staging stamp — answers
    what-was-this-HOLD-staged-under; a staging behavior change,
    adjacent to the --staging-strategy escape hatch.
    Added 2026-07-25 (ratified proposal, session 003): extract the
    sandbox harness (make_sandbox_home / make_install / make_repo /
    run_bale) into tests/harness.py when a second suite lands.
    [Trigger spent — extraction done: the shared harness lives at
    tests/harness.py (§7); marked at
    `2026-07-31-board-33-recovery-015`.]
    Added the 2026-07-31 third sitting, same v0.4-harness bucket
    (accepted proposals): a bale-handoff E2E pinning the handoff
    path's resolved_scope stamp through a real bailout fixture
    (017's proposal); a real-apply clarification E2E pinning the
    §8.10.2 handler's preserved-record shape to status detection
    (018's proposal); an exact-key-set pin on format_status_json's
    session object (master disposition of 018's look-closely item).

12. **bale status staging row — DONE** 2026-07-15 (sid
    `2026-07-15-status-staging-row-003`; telemetry): per-session
    staging row in bale status landed, v0.3.11.

13. **read-vs-write separation — DONE** 2026-08-07, closed as an
    arc (design/orchestration
    `2026-08-07-board-13-read-write-design-003` read-only, plus
    applied sids `2026-08-07-board-13a-forecast-surface-004`,
    `2026-08-07-board-13b-epoch-ledger-005`,
    `2026-08-07-board-13c-contract-docs-006`; telemetry; versions
    0.4.1 → 0.4.2 across the arc, C bump-exempt per the cadence
    ruling). ADR-0015 Accepted; ADR-0007 flipped Superseded with
    the evidence-35 reverse-transform assertion. E1–E5 ratified at
    the master desk 2026-08-07, E3 with the read-side
    ships-the-oracle refusal. Doctrine's one home: ADR-0015 (§5
    carries the pointer plus the two desk dispositions). Design
    artifacts committed at `claude/context/board-13-arc/` (commit
    d4874ae). B and C ran as the first deliberate post-separation
    concurrent pair; B's `tools/response_lint.py` embed was the
    first live modified-file per-path admission (§6 entry 60).
    Evidence 25's serialization class is structurally closed — its
    entry carries the closing pointer. This row's motivating
    history (five evidence-25 tallies, the architect's ratified
    design input) lives in git, pre-landing versions of this doc.

14. **Doc-compression sitting, structural phase — RETIRED AS
    MISFRAMED** 2026-07-25 (chat-ratified; evidence 32): the
    physical split's token-savings premise conflated shipped bytes
    with read tokens; the split decision is transport-relative and
    waits on board 10's injection-model agenda item. Replacement
    work: board 22 (since closed). Riders re-homed to 22a and
    landed there. The 2026-07-21 packaging reference map lives in
    v3 of this doc, in git.

15. **7c — doc-gap audit + landing — DONE** 2026-07-21 (sid
    `2026-07-21-doc-gap-landing-002`; telemetry): gaps 2, 5,
    6-schema landed; 3 already landed; 4
    skipped as adequately placed. Closing note: the deliberately
    tripped embedded-schema drift guard was cleared same-sitting by
    the lint-schema-refresh follow-on
    (`2026-07-21-lint-schema-refresh-004`), recorded here rather
    than as its own row, matching how small follow-ons ride their
    parent (cf. board 3).

16. **Transition-branch retirement — DONE** 2026-07-21 (sid
    `2026-07-21-transition-branch-retirement-003`; telemetry):
    no-stamp fallback → refusal, discard switch-only,
    git-decides dirty semantics ratified (§5).

17. **DOCS.md sanctioned-pairs one-liner — DONE** 2026-07-25 (rode
    22a — sid `2026-07-25-tarball-core-first-004`; telemetry): the
    CLAUDE.md §11.2 ↔
    TARBALL.md §3.4 pair appended to the §9 sanctioned-pairs
    registry.

18. **retry flag parity — DONE** 2026-07-21 (sid
    `2026-07-21-retry-flag-parity-005`; telemetry): retry ice-out
    fixed; gate override flags closed across the lifecycle,
    v0.3.14.

19. **retirement cleanup — DONE** 2026-07-21 (sid
    `2026-07-21-retirement-cleanup-007`; telemetry): sid_sha
    short-circuit retired, detached-HEAD pack refusal
    landed; §7.1 renumbering defect caught at master review,
    corrected by board 20.

20. **handoff refusal + numbering restoration — DONE** 2026-07-21,
    applied 2026-07-22 (sid
    `2026-07-21-handoff-refusal-numbering-008`; telemetry): §7.1
    numbering
    restored (interstitial step 4a), detached-HEAD refusal extended
    to handoff.

21. **Extend main()'s install sanity check to handoff — DONE**
    2026-07-25 (sid `2026-07-25-handoff-install-precheck-003`;
    telemetry): gate widened in main()
    to both request-building commands, BALE.md §5.4 rider clause
    landed, first tracked test suite shipped with it.

22. **Global-doc mechanization arc (the worker toolkit) — CLOSED**
    2026-07-31, all four phases DONE. The ratified pattern —
    mechanize shape, keep judgment as prose — is §5's
    mechanize-shape contract; the non-mechanizable residue stays
    prose by design, with boards 4/5/6 as its control surface.
    - **22a — TARBALL.md core-first restructure + riders — DONE**
      2026-07-25 (sid `2026-07-25-tarball-core-first-004`;
      telemetry).
    - **22b — craft tool v1, normal-response shape — DONE**
      2026-07-29 (sid `2026-07-29-craft-tool-v1-007`; telemetry).
    - **22c — bailout + clarification shapes — DONE** 2026-07-31
      (sid `2026-07-31-craft-kinds-v2-003`; telemetry).
    - **22d — probe scaffold + residue audit — DONE** 2026-07-31
      (sid `2026-07-31-probe-scaffold-22d-004`; telemetry; the
      audit's three findings fused as board 31).

23. **test-layout-docs — DONE** 2026-07-28 (sid
    `2026-07-28-test-layout-docs-004`; telemetry; pack re-authored
    after the sesh-002 original was lost — evidence 40). As ratified 2026-07-25 from session 003's
    Proposals: bale-internals.md gains the test layout (tests/ at
    repo root, stdlib unittest, ADR-0005 sandbox rules, harness
    inline for now) and loses the stale deferred-to-v0.4 sentence;
    ADR-0005 flips Proposed → Accepted in the sanctioned diff shape;
    INDEX.md Proposed-set prose swept (0002–0004 stay Proposed).
    Pack and brief authored at the sesh-002 close; serialized after
    22a (claude/INDEX.md collision) and before 22b (the internals
    doc should describe tests/ before 22b's suite lands beside it).
24. **Scopeless packs + the scope wizard question — DONE**
    2026-07-28, v0.3.15 (sid `2026-07-28-scopeless-packs-003`;
    telemetry): the read-only session shape landed —
    masters-never-self-land is mechanical, and the wizard's
    session-shape question covers work-class in the same exchange.
    The shape and its design rationale are documented at BALE.md
    §7.2 and TARBALL.md §3.4's --read-only flag row (the latter
    verified in the injected copy at the v4 regeneration).

25. **Closure telemetry — DONE** 2026-07-29, v0.3.15 → 0.3.16 (sid
    `2026-07-29-closure-telemetry-001`; telemetry): unlock- and
    revert-terminated sessions write
    closure records; closure_reason enum (six reasons, additive) +
    --reason on both commands; closed-read-only inferred from
    recorded scope [].

26. **Split supersession — DONE** 2026-07-29, v0.3.16 → 0.3.17
    (sid `2026-07-29-split-supersession-002`; telemetry): bale pack
    --supersedes landed;
    decline-refuses-on-every-path ratified (evidence 42; piped
    stdin declines — pack has no --no-interact, correcting this
    row's original wording). Complement to board 13, not
    substitute: 13's design remains unprejudged — 26 handles the
    true write-scope splits that remain.

27. **Lifecycle docs close-out — DONE** 2026-07-31 (sid
    `2026-07-31-lifecycle-docs-closeout-007`; telemetry): the
    ADR-0011 follow-up audit closed; BALE.md §11 contract row 25
    landed with five sweep riders.

28. **Rollback telemetry — DONE** 2026-07-29 (fused with 29; sid
    `2026-07-29-lifecycle-telemetry-parity-006`; telemetry —
    the corpus's first live HOLD→retry multi-attempt pair):
    rollback and
    --undo record on clean success; rolled-back/re-applied outcomes
    plus the rollback command enum value, all additive; v0.3.18.

29. **unlock --json parity — DONE** 2026-07-29 (same fused session
    as 28 — sid `2026-07-29-lifecycle-telemetry-parity-006`;
    telemetry): format_unlock_json
    one-homed in bale_report; debris on its own key;
    --integration --json refused; refusals fail()-shaped.

30. **INJECTED_TOOLS consolidation + revert --json + VERSION —
    DONE** 2026-07-29 (sid
    `2026-07-29-injection-consolidation-revert-json-008`; telemetry;
    created and closed within its sitting from accepted proposals):
    the craft tool's temporary guarded injection block replaced by
    the one-source INJECTED_TOOLS entry + main() precheck coverage;
    revert --json to the same one-home contract unlock got;
    v0.3.19. The pack E2E asserting both tools ship with exec bits
    landed here rather than waiting for the v0.4 bucket.

31. **Worker-toolkit residue (from 22d's audit) + VERSION — DONE**
    2026-07-31 (sid `2026-07-31-worker-toolkit-residue-008`;
    telemetry; VERSION 0.3.20): the three fused emissions landed —
    validation epilogue, exec-bit assertions, lint
    feedback-mechanical emitter.

32. **bale status clarification hint — DONE** 2026-07-31 (sid
    `2026-07-31-board-32-status-clarification-hint-018`; telemetry;
    VERSION 0.3.22): clarification-suspended state landed in status
    — precedence held > clarification > packed > orphan (reasoning
    on the classifier docstring); facts row renders whenever
    records exist while the state description + trailer carry the
    suspension framing; json `session.clarification` present when
    rounds > 0, consumers dispatch on the state enum; detection
    persists through the answered-but-unapplied window by design
    (the hint covers both halves).

33. **Read-only session lifecycle — DONE** 2026-07-31 (sid
    `2026-07-31-board-33-readonly-lifecycle-017`; telemetry;
    VERSION 0.3.21): full ratified spec landed — the resolved_scope
    stamp (additive schema key), the read-only sweep
    (accept-default prompt, piped-stdin decline, `closed-read-only`
    / command `pack` through close_session_with_record), the
    close-out banner, the README identity echo (path + first
    heading + sha256, uniform across authoring paths, null-together
    json keys), and the placeholder refusal (sentinel `TODO(brief)`
    — the TARBALL.md §3.4 convention line is the literal's one
    home; re-ratified this sitting after the 009-chat decision
    proved non-durable). Ratified judgment calls, recorded
    compactly: the refusal fires at read time (`--edit` included,
    matching the empty-file refusal's posture); sentinel scope is
    `--readme-file` only (editor-path extension declined — the
    interactive path is human-audited by construction; reopen
    trigger is a live slip-through); the sweep skips HOLD-branched
    read-only sessions with a logged revert remedy; multiple open
    empty-scope sessions prompt per-session in registry order;
    unlock's inference untouched, the value now reachable from two
    commands. Landing retires the evidence-44 brief-carried
    scope-statement convention. [2026-08-03: this row's own spec line
    carries the literal it names inline. Safe today — the read-time
    refusal is scoped to `--readme-file` per this row's ratified
    judgment calls, and MASTER.md ships in `context/`, never as a
    README — but any future widening of the refusal's scope to
    shipped context files must account for this doc tripping it.
    Observed in `2026-08-03-master-deltas-005`'s notes, concurred by
    the master; no scope change made or implied.]

34. **v0.4 cut — DONE** 2026-08-06, closed as an arc (ratified
    2026-08-03; sids `2026-08-06-verbose-thread-close-005` 0.3.35,
    `2026-08-06-v04-selftest-audit-006` doc-only under the cadence
    ruling, `2026-08-06-v040-cut-007` 0.4.0; telemetry): the v0.4
    arc complete, 0.4.0 cut 2026-08-06 — the --verbose thread
    closed, the read-only audit diffed §13's v0.4 selftest
    checklist against the actual suite, and the cut proceeded on
    the audit alone per the ratified call (§3). The ladder's
    deferred-rollback suspect was refuted in its narrow form by the
    audit (real conflict and merge-commit mainline both driven;
    qualifiers in 006's notes); residual gaps moved to board 35.

35. **Selftest gap-closure arc** — seeded 2026-08-06 at the
    board-34 close from that arc's residuals. Owns the 0.4.0
    audit's ranked gap list, verbatim from
    `2026-08-06-v04-selftest-audit-006`'s notes:

    1. **Malformed-tarball apply pre-flight** (sha256 mismatch, path
       safety, artifact denial, empty reason, duplicate path,
       reconciliation mismatch). Largest uncovered contract surface —
       these are the §11 rows the whole trust story leans on. Cost:
       moderate; one suite with a tamper-helper over the existing
       fixture builder, one test per row.
    2. **`apply.sh` real operations** (delete, rename's removal half,
       exec-bit restore + its §7.7 assertion). Cost: small; extend the
       existing fixture builder past the no-op.
    3. **Pack §7.4 caps / `--exclude` / `.baleignore` / `--force`.**
       Cost: moderate (cap tests need controlled tree sizes; the pty
       runner already exists for the `[e]` branch).
    4. **Rollback `--list`** and the **plain-commit** branch. Cost:
       trivial for `--list`; small for plain-commit (fabricate a
       non-merge applied tag).
    5. **`unlock --integration` clear path.** Cost: trivial.
    6. **Worker `validation.sh` exit 2.** Cost: trivial (one more
       fixture exit code).
    7. **Handoff happy path** — adjacent, not in the checklist's
       verbs: `bale handoff` is tested only at its install-precheck
       refusal; the repackaging itself is untested.

    Session 1 — DONE 2026-08-07
    (`2026-08-07-board-35-apply-preflight-002`, tests-only
    bump-exempt per the §5 cadence extension; telemetry): gap 1's
    reject suite plus gap 2's real-operations suite landed as two
    files (ratified layout), the response-tarball builder extracted
    to tests/harness.py (`build_response_dir` /
    `tar_response_dir`), and the coverage/exclusion census — which
    §11 rows are covered, which are excluded and why — is in the
    session's archived notes. The duplicate-path finding's
    disposition — add the check — landed at board-13b as §11 row
    32 (§5's contract). Queue additions, ordering-free within gaps
    3–7: the row-8 dirty-on-target pin and the row-21
    declared-untracked-inputs pin (both from 002's notes), and the
    post-epoch stats-corpus fixtures (fold-in registry carries B's
    proposal verbatim). Gaps 3–7 remain queued, ordering-free.

## 5. Contracts established (do not re-litigate casually)

Carried forward: JSON vocabulary (outcome, sid, tarball, log,
session_dir, context_files; + verdict, validation summary, merge
fields) and stream discipline (json mode: logs to stderr, exactly one
stdout JSON line; human modes byte-identical). bale_report owns
rendering; main-script changes limited to wiring. Proposals = prose
with rationale, never runnable; pre-flight rescope = runnable command
required. Probe = paste-back read-only block, default-to-ask;
clarification = structured intent-gap questions. Extractions pulled
by need, never front-loaded. Staging cleanup =
ownership-by-open-session. Status json: additive sessions/stale keys;
consumers dispatch on stale/sessions, not present. Integration target
is per-session (origin_branch stamped at pack/handoff; retry
preserves it). Narrow pre-flight: refuse only
dirty-AND-on-target-branch; all refusal paths leave the committed
branch and open session recoverable. HOLD commits to bale/<sid>,
never merged; inspection = branch diff + per-sid staging; merge
cleanup = branch -D; merge commit + applied/<sid> tag anchor history.
Unlock = pre-apply abandonment; revert = post-apply discard. Claims
with no project-level checks cover the response's own validation
assertions. Generated artifacts never ship in responses (doc rule +
mechanical deny-list).

New, ratified 2026-07-13 (the 008 meta session and its follow-up
conversation):

- **Handoff reading plans are input, not authority.** TARBALL.md §5.7
  amended (landing via master-doc-landing): the plan is high-value
  input the planner ratifies at bale handoff time; the request
  manifest is authoritative and wins on disagreement. Rationale: a
  worker→worker instruction channel with standing authority is the
  self-oracle shape §3.4 already neutralized for pack commands, one
  level up and with a bigger lever.
- **MASTER.md is a tracked project doc** at `claude/MASTER.md`,
  regenerated by editing in place. `INDEX.md` is its discoverable
  surface. No DOCS.md inventory row yet — the BALE.md
  category-of-one precedent applies (project-local structural peer;
  a project-agnostic global doc doesn't grow bale-src-specific
  rows); global categorization is deferred to ADR-0009's promotion
  triggers (board 10).
- **Telemetry is dual-stream with day-one provenance.** Mechanical
  vs self-reported fields are separated in the schema; autonomy
  grants weight the mechanical stream; every response is stamped
  with model, contract version/hash, packer identity, and work
  class. (Design constraint binding board items 4 and 5; the brief
  fills in the field set.)
- **Blind checkpoints coexist with worker validation.** The planner's
  blind checkpoint is the misunderstanding control; the worker's
  validation.sh is the calibration stream. Neither replaces the
  other; the ledger consumes both. (Binds board 6.)

New, ratified 2026-07-15:

- **Scope-drift override is per-invocation and per-path, flag-only.**
  A standing config opt-out is the rejected shape (self-oracle-
  adjacent silent bypass). Refusals and overrides are
  mechanical-stream telemetry.
- **Status semantics:** bale status reports what the next apply
  would do (effective merged-config resolution); history questions
  belong to per-sid staging inspection. Inert declarations report as
  effective-empty.
- **One-home rule for json key contracts:** the renderer docstring
  owns the key list; BALE.md points at the owner and never
  duplicates it. Mechanically pinned in the reconciliation session's
  validation.
- **The bin/bale version narrative is dropped, not re-homed** —
  git-is-the-changelog reaffirmed as applied; recovery is git
  checkout, and sole-home rationale surfaces via the 8a sweep as
  notes.md proposals.

New, ratified 2026-07-21:

- **Detached-HEAD request-building is refused at pre-flight on both
  paths**, pack and handoff; no override flag exists.
- **Dirty manual checkout of bale/<sid> at discard: git-decides** —
  proceed when git carries WIP safely across the switch, refuse
  loudly when git would refuse; no path ever discards WIP.
- **Scope-override flags are per-invocation across the entire
  session lifecycle:** every lifecycle command that re-runs a gate
  accepts the gate's override flags, re-stated each invocation,
  never carried. (The structural half of board 18's fix.)
- **Numbered-anchor stability:** DOCS.md §6.4's permanence extends
  to any cross-referenced numeric anchor, numbered steps included;
  when immutable citers exist (ADRs, git-history reasons), the only
  remedy is restoring the original numbers — interstitial labels
  (4a) are the sanctioned insertion shape.
- **Execution-context manifest:** any session whose fixtures execute
  bin/bale end to end includes, verbatim: all of bin/, all of
  schemas/, the four global docs under docs/, every tools/ member
  named in bin/bale's INJECTED_TOOLS, and the scripts the test suite
  executes — today scripts/build.sh and install.sh (equivalently:
  all of tools/, scripts/build.sh, install.sh). The set tracks the
  rule, not the enumeration: when INJECTED_TOOLS grows or the suite
  gains an executed script, the set grows with it, no contract edit
  needed. Copied, never re-derived. (Countermeasure for evidence
  30's class; amended 2026-08-05 from the enumerated form after the
  board-6 arc's two include-gap instances — sessions A and B.)
- **ADR-0013 flips to Accepted:** ratified; the flip lands with
  board 14's session (see the fold-in registry). [2026-07-25: board
  14 retired; the flip rides board 22a per the registry.]

New, ratified 2026-07-25 (this master session, in chat):

- **Physical splits of the global docs are transport-relative
  decisions.** Shipped bytes are not read tokens on the
  human-carried path (evidence 32); any physical split of the
  globals is sequenced after board 10's injection-model decision.
  Board 14 retired as misframed under this rule.
- **Mechanize shape; keep judgment as prose.** Where a contract rule
  is shape, it moves into a worker-shipped tool and the doc keeps
  only the trigger; where it is judgment, it stays prose. The
  crafter never validates its own output: construction tooling and
  the blind-authored lint remain separately authored and separately
  maintained (evidence 16's self-oracle test applied at design
  time). (Binds board 22.) Toolkit emissions contribute shape
  only and print only what the tool itself computed: paste-ready
  stdout fragments, never sourced helpers or response artifacts;
  self-reported fields are hand-added by the worker, never
  emitted (evidence-16 applied at the emission surface —
  ratified 2026-07-31 with 008).

New, ratified 2026-07-27 (the detour sitting, in chat):

- **Orchestrator sessions pack scopeless, not narrow.** (Revises
  evidence 36's pending wording before ratification.) A master that
  will spawn packs while open ships its broad read context under an
  *empty* recorded scope: it intersects nothing, so workers pack
  freely alongside it, and the own-scope drift gate refuses anything
  it tries to land — masters-never-self-land becomes mechanical, not
  discipline. Master deltas always arrive via their own narrow
  follow-on pack. A master that spawns nothing while open may
  self-land its deltas (the sesh-001 precedent, now bounded to
  exactly that case). Until board 24 lands the scopeless shape, the
  interim manual form is unlock-before-spawn with deltas via a
  narrow follow-on (the master-deltas-005 shape).
- **The architect's typed surface is bare verbs and verbatim
  pastes.** The architect composes exactly one command from scratch
  — the bare cold-start `bale pack "goal"` — plus bare lifecycle
  verbs (apply, retry, revert, unlock, handoff) at the moments
  bale's banners and refusals name them. Every flagged or scoped
  command is Claude-authored: master-authored worker packs,
  worker-authored rescopes, `--supersedes`, remedy-text copies.
  Corollary design rule: every command names its successor — a flow
  whose next step is not named by tool output at the moment it is
  needed is a design gap in bale, never a memorization gap in the
  architect. (Board 24 closes the one flow with no predecessor to
  name it.)
- **Supersession is worker-authored and split-scoped.**
  `--supersedes` appears only in worker-emitted rescope commands; it
  closes the parent as superseded-by-split and stamps
  `depends_on.superseded_session`. It is never overloaded for master
  continuation or general related-to linkage — if the ledger later
  wants master-deltas lineage, that is a different `depends_on`
  field, deferred until board 5's design asks for it.
- **Session closure is a recorded event.** Every registry close
  leaves a durable record with a reason: apply-terminated sessions
  keep the BALE.md §8.9 shape; unlock- and revert-terminated
  sessions gain closure rows (board 25). The telemetry corpus stops
  being numerator-only (evidence 38).

New, ratified 2026-07-31 (the doc-compression sitting, in chat;
recorded at `2026-07-31-board-33-recovery-015` — evidence 47):

- **The session's shape is manifest-stamped.** Pack stamps the
  recorded scope into the request manifest as `resolved_scope`
  (`[]` for read-only); workers reason from the stamp, never from
  inference over `context_included`.
- **The read-only sweep runs on the next read-only pack only.**
  Worker packs and apply never close a lingering read-only session.
- **The sweep prompt defaults to accept; piped stdin declines.**
  Automation never silently closes a session.
- **The read-only pack's open banner names its own close-out.**
  Board 33's row carries the implementation spec; this block states
  the rules — one home each.

New, ratified 2026-08-03 (this sitting):

- **The claim-basis precedent.** A validation claim of `pass` may
  be grounded in prediction rather than observation when the
  grounds are structural and the basis is fully disclosed in notes;
  a predicted pass presented as observed is a violation. Both are
  graded mechanically at apply — a wrong prediction lands as a
  `disagree` in the ledger, so miscalibration costs the work
  class's agreement rate. (Ratified at the sub-master level in the
  board-5 arc's session 003, flagged upward as precedent-setting,
  and ratified here; the ledger's predicted-vs-observed
  measurement gap is a §3 watch.)
- **Verbatim-proposal shipping.** Constraints or briefs citing a
  prior session's proposal carry the proposal's notes.md text
  verbatim, never a paraphrase — a paraphrase flattened a
  conditional once (evidence 49) and the worker had to reconstruct
  the intent.
- **The version ladder re-coupling** (summary; the normative text
  lands in BALE.md §13 via this sitting's sibling session): 0.4.0 =
  the --verbose thread + the §13 checklist audit, then cut (board
  34). 1.0.0 = contracts become promises — wire format,
  record_version, and --json keys go breaking-change-costs-major —
  gated on boards 6 and 10 landing and the first work class earning
  and exercising a real autonomy grant; explicitly not gated on the
  API-harness transport (separate component per §1) or lifting the
  solo-project assumption (documented scope).

New, ratified 2026-08-05 (this sitting):

- **The handoff-covering disposition** (ratified; implementation
  landed — see the closing note):
  `bale handoff` runs the covering refusal
  (`checkpoint_blindness_preflight`) against its reading-plan
  scope, with a mirroring per-invocation admission flag. Source:
  session C's notes proposal (verbatim text shipped in
  `claude/context/board-6-arc/`) plus the architect's disposition
  relayed 2026-08-05, quoted: "run the covering refusal on the
  handoff path with a mirroring per-invocation admission flag."
  Rationale carried from the arc report's escalation 2: a handoff
  whose reading-plan scope covers the checkpoint silently re-opens
  the layer-1 hole, and the rare legitimate case — a bailed
  checkpoint-maintenance session — was already flag-admitted once
  at pack, so a flat refusal strands exactly that handoff.
  Implementation is a separate worker session, pack authorable from
  either lineage on request. [2026-08-06: implemented at
  `2026-08-06-handoff-covering-001`, with the one-text constraint
  subsequently relaxed for the remedy sentence only — caller-aware
  rendering, landed at `2026-08-06-sweep-json-stats-002`; the
  diagnosis and flag-successor lines stay byte-shared.]

New, ratified at the board-10 tidy-up sitting (2026-08-05/06,
master `2026-08-05-discuss-harness-011`):

- **The cadence ruling** (ratified 2026-08-05): doc-only sessions
  are bump-exempt; the `execution-context-amendment-006` precedent
  is now the rule, not a divergence. (The sitting-close deltas
  session recording this is itself governed by it: doc-only, no
  VERSION bump shipped.)
- **The json `sweep` object** (ratified at the master desk
  2026-08-06): null means no sweep ran — covering both collapsing
  disabled and no-sweep-event, the archive-key posture; the key
  list is owned by `format_apply_json`'s docstring, with the
  unlock and revert docstrings pointing there; `debris.sweep`
  carries the debris record's result.

New, ratified 2026-08-07 (this sitting, master
`2026-08-07-continue-plan-001`):

- **The cadence extension:** tests-only sessions are bump-exempt,
  by the cadence ruling's rationale (no shipped-tool behavior
  change). First exercised by
  `2026-08-07-board-35-apply-preflight-002`.
- **The read-vs-write separation:** ADR-0015 (Accepted) is the one
  home for the doctrine; §5 records only the pointer plus the two
  desk dispositions not in the ADR — no registry-side read set
  (data-gated, Q3), minimal status rendering (Q4). E1–E5 ratified,
  E3 with the read-side ships-the-oracle refusal.
- **Duplicate-path pre-flight:** prose and enforcement agree —
  TARBALL.md §5.2's invalidity is now mechanical at §11 row 32
  (string-identity basis, matching the lint).

## 6. Orchestration-doctrine evidence pile (feeds the doctrine doc at
   harness scoping; each rule earned from live traffic)

1–9 carried forward verbatim from the v1 doc: (1) ship decision
context INTO the request; (2) flagged judgment calls halt for
ratification — reasonable-but-wrong generalizations ship silently
otherwise; (3) workers refusing oversized goals and returning seams
is the happy path, the ORCHESTRATOR weighs split economics
plan-wide; (4) pre-flight guesses about unread code are labeled
guesses; (5) doctrine in docs propagates to workers; (6) packer
errors are a grading signal; (7) an orchestrator may re-derive a
worker's rescope command from the named seam, the human path keeps
the runnable command; (8) scaffold commits need session-grade
hygiene; (9) masters externalize their own state.

10. **Ratified answers can themselves be underspecified; the
    flag-for-ratification duty covers REPAIRS to master decisions.**
    The narrow pre-flight rule presupposed a stable merge target the
    system didn't have; the worker built the origin_branch stamp to
    make the ratified rule coherent and flagged it rather than
    shipping silently. (checkout-free-mechanism, decision 1.)
11. **Briefless pack commands are a recurring failure CLASS, not
    isolated slips** — three occurrences: the first ADR pack, the
    prior master's per-sid command, a worker-authored rescope
    command. Root cause each time: goal + --slug silently skips the
    wizard and its README step. Mechanical guard queued (board item
    3); until it lands, every command review checks for
    --readme-file first.
12. **Compaction recovery works when the discipline is followed:**
    re-read manifest and contract docs, read partial output back
    from disk, recompute every hash and claim from finished files,
    disclose in notes.md. The compacted session's response was
    indistinguishable in quality; the disclosure is what made it
    trustworthy. (checkout-free-mechanism.) [Second successful
    §11.6 recovery: `2026-07-31-master-v4-regeneration-012`, with
    the accounting-written-pre-compaction caveat disclosed in its
    notes and the master's independent full v3 read as the cover.]
13. **Include sets must cover LOAD-TIME IMPORTS whenever the worker
    is expected to execute the tool, not just read it.** The docs
    session shipped bin/bale without its four import siblings; the
    snapshot harness could only skip cleanly worker-side. Packer
    (master) error, worker handled via named-assumption path.
    Second occurrence, packer-attributed: the generated-artifacts-rule
    request shipped without schemas/ and four sibling modules, so the
    worker's sandbox ran functional stubs and one E2E assumption (the
    schema accepts the §5.2 shape) went unverified — handled
    worker-side via the named-assumption path with loud-and-contained
    failure. Two occurrences upgrade this from incident toward class;
    board 4's packer-attributed telemetry field is the counter for
    it. Third occurrence, this sitting: a worker-authored rescope
    command omitted load-time import siblings — the class now spans
    architect, master, and worker as packer. [Next occurrence,
    2026-08-03, sub-master-attributed: the execution-context
    manifest set omitted from the board-5 arc's closeout pack (the
    worker synthesized a partial tree; its prediction held) — the
    class now spans sub-orchestrators as packer. See evidence 49.]
14. **Commands authored from a stale picture of the repo carry
    stale scope statements** — the prior master's per-sid command
    said "out of scope: lifting the multi-open gate" AFTER the gate
    was already lifted, which could have induced single-session
    design assumptions. Master commands are authored against source
    actually read, current as of that session.
15. **Masters end sittings at milestones, deliberately.** Tight fit
    is a non-fit applies to master context too; the state doc
    absorbs open questions rather than a tired context resolving
    them. (This document is that rule executing.)

New from the 008 audit:

16. **Self-oracle shapes recur at every level; test for them by
    default.** validation.sh (worker grades its own work), telemetry
    self-report (worker writes the record its autonomy is judged
    by), handoff reading plans (worker N steers worker N+1's
    context), next-prompt.md (retired for exactly this). The
    standing test for any new mechanism: does the entity under
    evaluation author the input its evaluation rests on? Where it
    does, split mechanical from self-reported and weight the
    mechanical.
17. **Planner-level artifacts get the same inventory treatment as
    worker-level ones.** The gameplan lived outside the repo — the
    one load-bearing artifact in the system that existed only by
    convention, invisible to sessions and the doc inventory, even
    while rule 9 said masters externalize state. Landing MASTER.md
    closes the instance; the rule is the general form.
18. **Contract ingestion is a per-worker tax, and compression is a
    fleet-scaling lever, not tidiness.** ~25K tokens of injected
    contract per tarball session multiplies with every spawned
    worker and eats the budget margin that keeps sessions clear of
    compaction. (Board 7 is this rule executing.)

New from the 2026-07-13/14 sitting:

19. **Masked drift.** The architect's install is refreshed by a hook
    whose mirror set, not its file list, determines coverage;
    omissions were invisible until a deliberate hard-fail made one
    loud. validate.sh rows are the guard class.
20. **Probe for mechanism, not residue.** A state snapshot was read
    as revealing a refresh mechanism and the inference was wrong;
    probes should read the configuration that does the thing (the
    hook line, the script), not the tree it leaves behind.
21. **A wrong fact in a brief is worse than a missing fact.** Missing
    facts trigger probes; wrong facts trigger investigations the
    worker cannot decline, at context prices — two compactions
    resulted. Root cause both times: the master inferred file
    behavior from grep fragments while holding the whole file.
    Corollary for masters: read files whole before making claims
    about them, and pin designs in briefs when the search has
    already been done — open-ended design questions in a brief are
    an invitation to spend the window searching.
22. **Ship-vs-emit.** The mirror contract requires complete copies
    on disk, not retyped through context; now normative in
    TARBALL.md, born from a near-unnecessary split.
23. **Master serialization is a claim.** Ordering constraints the
    master imposes between sessions get stated with their rationale
    so the architect can contest them; one over-serialization was
    caught by the architect this sitting.

New from the 2026-07-15 sitting:

24. **Doc touches pinned in briefs against unread structure are a
    failure class, not a slip** — two same-sitting occurrences (a
    flag row pinned to a section that covers the pack pipeline; a
    status section that did not exist). Both from the master
    inferring BALE.md structure from other docs' pointers.
    Countermeasure now standing: read the target doc's actual
    sections before pinning any doc touch; cite only what was read
    this sitting. The worker-side flag-don't-ship duty caught both.
25. **Read-context includes are concurrency locks.** Includes double
    as scope, so files shipped for read-accuracy (evidence 21) or
    execution capability (evidence 13) exclude every concurrent
    session that wants them — the master discovered this hunting
    for concurrent work while 8a held INDEX.md and meta-sessions.md
    as read context. Board 13 is the structural fix; until it
    lands, packs meant to run alongside others weigh every
    read-context include as the lock it is. Third live instance
    2026-07-25 (sesh-002): the ratified execution-context manifest's
    docs/ include forced boards 21 and 22a to serialize — the
    contract itself is now a lock generator, sharpening board 13's
    priority. [2026-08-07: structurally closed — board 13 landed
    the read-vs-write separation (ADR-0015), includes stopped
    gating concurrency, and the class did not recur in the first
    post-separation concurrent pair (board row 13; §6 entry 60).]

New from the 2026-07-15/16 sitting:

26. **Measure normativity before setting compression targets.**
    Board 7's 35–45% target predated measuring the docs' normative
    fraction; TARBALL.md's honest editorial floor was 4.9% (95%
    normative), and CLAUDE.md §11.2's "~250 normative words"
    estimate landed at 397 because the validation-asserted phrasing
    IS the residual. (Sessions 012 and 001.) Corollary: after
    rationale relocation, remaining wins are structural, not
    editorial.

27. **Paired independent defenses earn their keep on
    one-apply-behind changes.** Session 002's free-name resolution
    audit and its fixture E2E each independently caught the same
    missed lazy import (apply_pipeline's merge-branch
    current_branch) before it shipped into the exact defect class
    one-apply-behind makes silent. Prescribe both shapes for future
    extraction-class sessions.

New from the 2026-07-21 sitting:

28. **Single-line fingerprint greps false-negative on wrapped
    prose.** Normalize (join lines) before matching, and keep
    validation grep anchors on one line deliberately. Nearly landed
    a duplicate rule: doc-gap-landing found gap 3's sentence
    present but wrapped mid-phrase, which is why the
    audit-before-edit step exists. The grep-normalization audit habit's DOCS.md
    one-liner rides board 14.

29. **Flag parity across a session's lifecycle commands is a
    contract surface.** A per-invocation override one lifecycle
    command lacks ices sessions exactly when the override was
    needed — the live case: an apply with --allow-out-of-scope went
    HOLD and retry had no such flag. New gate flags are audited
    across apply/retry/revert at birth. (Board 18 is the fix.)

30. **The include-set completeness class extends beyond import
    siblings to runtime-loaded files** — schemas, global docs,
    injected tools. Occurrences four and five of the evidence-13
    class landed this sitting (retry-flag-parity worked without
    schemas/response-manifest.schema.json; the numbering
    session's fixture leaned on an assumed install layout), both
    packer-attributed to the master. Countermeasure: the §5
    execution-context manifest.

31. **Read-before-cite binds the master citing ADR bodies exactly
    as it binds workers pinning doc touches** (evidence 24's class,
    one artifact over). The master's brief asserted an ADR-0007
    step citation from memory of INDEX.md's entry; the worker's
    read-only verification found the ADR's body carries no step
    citation (it cites only §11 row 3). The restoration decision
    survived, but the assertion was wrong.

New from the 2026-07-25 master session:

32. **Shipped bytes are not read tokens; injection-tax claims are
    transport-relative.** Evidence 18's ~25K-token framing quietly
    equated the two. On the human-carried path the globals arrive
    as files and enter context only when a read-paths trigger
    fires — the 07-25 master session read CLAUDE.md in full,
    TARBALL.md sectionally, and CODE.md not at all. Splitting a
    lazily-read doc into two shipped files saves approximately
    nothing; the calculus flips only under a transport that injects
    doc contents unconditionally. Two sessions had ratified the
    split framing before the architect caught it in chat — a
    misunderstanding-class catch at a human checkpoint, the exact
    class the §1 floor says mechanical validation cannot see.

33. **Mechanization deletes normative prose that editing cannot
    compress.** Editorial compression floors at the normative
    fraction (evidence 26: TARBALL.md ~95% normative); relocating a
    shape rule into a tool removes its prose entirely and upgrades
    enforcement from worker discipline to computed-only values —
    the invented-hash class dies when hashes are only ever
    computed, never recalled. Judgment rules are the residue that
    stays prose: they are read for recognition, not reconstruction.
    (Board 22 is this rule executing.)

New from the 2026-07-25 orchestrator sitting (sesh-002):

34. **Telemetry claim labels name checks, not tracked files.** The
    sesh-002 brief cited retry-flag-parity's "hermetic retry-parity
    E2E" as a tracked precedent to match; the tree had no test files
    at all — the label named a validation.sh check that ran once at
    apply and evaporated with the staging logs (audit finding 3's
    class meeting evidence 21's wrong-fact class, at the master
    level). Cost: one probe round. Standing rule: before the word
    "precedent" enters a brief, the master verifies the artifact is
    tracked — a claim label or telemetry string is evidence a check
    ran, never that a file exists.

35. **The reverse-transform assertion is the reference pattern for
    sanctioned-diff checks.** Session 004 validated the ADR-0013
    flip by reconstructing the pre-change file from the post-change
    bytes (un-flip the Status line, drop the appended note) and
    requiring sha256 equality with the request's shipped copy — no
    git dependency, and any edit outside the sanctioned shape breaks
    the reconstruction. Evidence 33's mechanize-shape rule executed
    worker-side, unprompted. Prescribe for future status flips
    (board 23 first) and for any check of the form "the diff is
    confined to shape X."

36. **The master session's own request scope is the registry's
    biggest lock.** Sesh-002's request shipped whole-tree context,
    so under ADR-0007 every worker pack it authored was inadmissible
    while it stayed open; the architect unlocked it silently to
    proceed, and the unlock stranded the session's self-landed
    deltas response — no open lock for responds_to to match.
    Evidence 25's class at the master level, and the strongest input
    yet for board 13. Standing rule (contract wording proposed in
    this response's notes, pending ratification): an orchestrator
    session that will spawn packs is itself packed narrow —
    MASTER.md plus only what it must read, each include weighed as
    the lock it is — or it ends its session before anything spawns;
    and its close-out deltas always get their own narrow bale pack,
    never a ride on the broad session. The sesh-001 precedent
    (master lands its own deltas) holds only for masters that spawn
    nothing while open. [Revised on ratification 2026-07-27: the
    remedy is scopeless packing — empty recorded scope, with the
    drift gate mechanically enforcing no-self-land (§5, board 24) —
    not narrow packing, which starves the master's read and buys
    probe rounds; the interim manual form until board 24 lands is
    unlock-before-spawn with deltas via a narrow follow-on pack.]

New from the 2026-07-27 detour sitting:

37. **The cold-start pack is the one command with no Claude author.**
    Every other command in the system is authored by a Claude role
    (master-authored worker packs, worker-authored rescopes) or
    named by tool output at the moment it is next (banners, refusal
    remedies). The bootstrap pack alone is composed by the human —
    and it is always the master session, which is exactly where
    broad default scope does the most damage (evidence 36's chain).
    Requiring the human to memorize scope flags there is the
    division of labor failing at its own boundary; the remedy is the
    wizard carrying the question (board 24). Observed corollary:
    this sitting's request stamped work_class "mixed" because the
    human was answering a question the wizard gave no basis to
    answer — the flag existed, the question did not.

38. **The telemetry corpus is structurally apply-only.** All 25
    records at claude/telemetry/ terminate in outcome "applied" —
    not because sessions never end otherwise, but because only apply
    writes records. Sesh-002, the most instructive session close in
    the project's history, has no row at all. Board 5's ledger would
    compute rates over a numerator-only dataset: sessions packed but
    never applied — splits, abandonments, reframes, master
    close-outs — are invisible by construction. (Board 25 is the
    counter.)

39. **Lifecycle exits other than apply are manual, undifferentiated,
    and documented only in refusal text.** `bale unlock` now means
    crash-debris cleanup, genuine abandonment, split-supersession,
    post-clarification reframe, and master close-out,
    indistinguishably — §9.4's cost-visible-naming argument eroded
    by accretion, with the costs genuinely different (a superseded
    parent has successors; an abandonment does not). The split
    flow's only documentation is the ADR-0007 refusal's remedy
    string. Boards 25–27 are the counters; the
    every-command-names-its-successor contract (§5) is the general
    principle the class violates.

40. **Chat-delivered commands are convention-only artifacts; board
    rows are the durable spec.** Board 23's pack command and brief,
    delivered at the sesh-002 close but never run, did not survive
    to the next sitting — the same class as evidence 17 (load-
    bearing artifacts existing outside the repo), one artifact
    smaller. The recovery was cheap precisely because the board row
    carried enough spec to re-author from; the standing rule is
    that it must. Corollary: "authored, not yet packed" is a state
    this doc should record only alongside where the artifact
    durably lives — otherwise record "ratified, packs unauthored"
    and re-author at spawn time. [2026-07-31, third sitting: the
    board-33 spawn confirmed the corollary's boundary — the board
    row re-authored the session fine, but the sentinel form, which
    lived only in the 009 session's chat, did not survive to the
    spawn and was re-ratified at authoring. Chat-only decisions
    inside an otherwise durable row are the residual exposure.]

New from the 2026-07-28/29 sitting:

41. **Workers infer scope from context_included, and the inference
    false-positives on directory includes.** Two same-sitting
    occurrences: both workers predicted the drift gate would refuse
    their new test file, reasoning from the manifest's enumerated
    file list; both packs had included tests/ as a directory, and
    resolved_scope records declared includes precisely so
    directories cover files created under them later — both applies
    ran clean. A visibility gap, not a discipline failure: the
    recorded scope is repo-side and invisible from inside a
    tarball, so the worker's only evidence is the shipped file
    list. Countermeasures: a TARBALL.md §3.2 sentence
    distinguishing the shipped list from the recorded scope (rides
    board 27), and the board-5-radar mechanical fix of stamping the
    declared scope into the request manifest.

42. **Routing an outcome through an existing gate presumes the gate
    fires; state the firing condition or the worker must.** The
    board 26 brief routed a declined supersession into the ADR-0007
    refusal — which only fires when scopes intersect. In the
    disjoint case the design would have admitted a pack that closed
    nothing and stamped no lineage while the command line claimed
    supersession: a silent, materially different outcome. The
    worker verified the presumption, found the hole, and refused
    explicitly on every declined path (ratified). Standing rule for
    briefs: name the condition under which a delegated-to gate
    actually fires; treat "the gate will catch it" as a claim to
    verify.

New from the 2026-07-29/31 sitting:

43. **Predicted refusals are control flow; surprise refusals are
    incidents.** The sitting plan serialized two concurrent applies
    *through* two gate refusals stated in advance — the ADR-0007
    sibling collision on 007's tests/ path while 006 was open, then
    007's own-scope drift on its two ADR-0014 new files — and both
    fired exactly as written, resolved by the pre-stated order and
    the pre-enumerated per-path admissions. Evidence 42's
    name-the-firing-condition rule, run forward: a gate whose
    firing condition the plan names is a sequencing tool the
    operator walks through calmly; the same refusal unstated reads
    as a failure and invites an unlock that throws a session away.

44. **Brief-carried scope statements are the working evidence-41
    countermeasure until the doc sentence and the manifest stamp
    land.** Same sitting, both directions: 007's brief said its
    test file *would* drift (file-granular includes, by design) and
    the worker enumerated it for admission without spending a probe;
    008's brief said tests/ was a directory include and its worker
    reasoned from that statement — hedged with the correct remedy
    rather than predicting a refusal from context_included. The
    recorded scope stays invisible from inside the tarball; a brief
    sentence stating it is cheap and worked twice. Masters state
    the scope shape in every brief until board 27's §3.2 sentence
    and the board-5-radar manifest stamp make it unnecessary. Held
    twice more the 2026-07-31 sitting — both workers reasoned
    new-file scope from the brief's directory-include sentence, zero
    probes spent, both applies clean. [2026-07-31, v4 regeneration:
    board 27's §3.2 sentence has landed — the injected TARBALL.md's
    §3.2 now distinguishes the shipped flat file list from the
    repo-side recorded scope (verified at line 1108 of the copy
    injected into this session's request); the brief-carried
    scope-statement convention remains good practice until the
    board-5-radar manifest stamp exists.] [2026-07-31, third
    sitting: retired as designed — the resolved_scope stamp landed
    at `-017`; from the next pack onward workers reason from the
    stamp. (Board 32's request was the first live stamped pack.)]

New from the 2026-07-31 second sitting:

45. **The brief seam is a transport surface and it failed silently
    at the resolver.** The sitting's deltas pack shipped a stale
    brief: a relative --readme-file resolved (cwd, then
    search_paths) to an old sesh-002 close-out file instead of the
    brief authored hours earlier — the goal named the right
    content, the manifest was coherent against the tree, and only
    the README was wrong. Evidence 40's class (load-bearing
    artifacts living outside the repo) at the resolver: undated
    near-duplicate briefs accumulate in Downloads, and first-match
    resolution picks among them silently. The worker caught it via
    the stop-and-clarify constraint plus a tree conflict, and the
    recovery was the designed §5.9 suspended-session round-trip —
    the base survived byte-identical (hash-confirmed both ends).
    Countermeasures: briefs open by naming the sid and sitting they
    serve (convention, effective this sitting); the operator
    glances at the pack report's resolved README path and first
    heading before shipping (discipline); and the pack report
    echoes the README's first heading line (mechanical — fold-in
    rider on the next bin/bale_pack.py-touching session, §3).

New from the 2026-07-31 doc-compression sitting:

46. **Absence of a gate refusal is mechanism-ambiguous evidence.**
    No ADR-0007 refusal cannot distinguish an empty-scope master
    from one already unlocked, and a doc-carried "ran read-only"
    inference from that absence contradicted the closure record:
    the 07-31 first-sitting master `2026-07-31-continue-plan-002`
    closed `abandoned` with scope `["."]` — whole-tree, unlocked
    pre-spawn, the interim manual form. The first end-to-end
    scopeless sitting was the second
    (`2026-07-31-continue-plan-006`, `closed-read-only`). Third
    consecutive habit-gap occurrence of a master packed without
    --read-only. Closure records are the ground truth; inference
    from refusal-absence never upgrades to a doc claim without the
    record (evidence 20's rule at the sitting level). Board 5's
    aggregation keys on these records either way. [Board 33 is the
    mechanical counter — the manifest scope stamp kills the
    inference-from-absence, and the sweep kills the lingering open
    session. Landed at `2026-07-31-board-33-recovery-015`; the
    sentence was in the unexecuted brief revision (evidence 47).]
    [2026-07-31, third sitting: the master's own-shape verification
    did not complete this sitting — the sitting-open `bale status`
    paste was requested but not relayed, so whether
    `continue-plan-016` was packed --read-only is recorded
    UNVERIFIED; do not infer from the gate's silence — that
    inference is this evidence entry's own subject. Board 33's
    banner + sweep close the class from the next master pack
    onward.]
    [2026-08-03, closing note: the UNVERIFIED item resolves —
    `continue-plan-016`'s closure record shows scope `[]` closed
    `closed-read-only` via command `pack` (ground truth per this
    entry's own rule); the board-33 sweep then worked live twice on
    2026-08-01 (`-016` swept by `continue-plan-001`'s pack, `-001`
    swept by `continue-plan-003`'s). The habit-gap streak is broken
    and the check is now mechanical via the `resolved_scope`
    stamp.]

47. **A same-filename brief revision with an unchanged first heading
    defeats both layers of the evidence-45 identity glance.** The
    revised micro-deltas brief kept the original's resolved path and
    first heading, so the countermeasure was structurally blind, and
    session 013 executed the stale brief correctly and undetectably.
    Second failure in the same incident: master ratification graded
    013's notes against memory of "the brief" without a
    task-coverage check, so the gap survived review and reached the
    next session as a false doc claim. Both misses
    master-attributed — the same-filename overwrite was the master's
    own advice. Countermeasures: brief revisions change their
    visible identity (the heading gains a rev marker) until board
    33's hash echo lands; and master ratification checks notes
    coverage against the current brief's task list, treating
    "executed as written" as a claim about WHICH brief. Recovery was
    cheap because the ratified spec survived verbatim in the revised
    brief file — evidence 40's corollary held.

New from the 2026-08-01→03 sitting (the board-5 arc):

48. **The sentinel-literal collision: the read-time refusal fires
    on any line containing the placeholder literal, by design, and
    an instruction ABOUT the sentinel is such a line.** Rev A of
    the board-5 design brief died at pack because a line
    instructing about the placeholder sentinel contained the
    literal itself. First live firing of the board-33 refusal — and
    it caught a master-authored brief. This was correct behavior,
    not a slip-through: board 33's reopen trigger stays unpulled.
    Standing rule: briefs instructing about the sentinel cite
    TARBALL.md §3.4's convention line (the literal's one home),
    never the literal.

49. **Paraphrase flattening at the packer** (from the board-5 arc's
    process findings, sub-master-attributed): a queued proposal
    transcribed into a constraint flattened a conditional; the
    worker had to reconstruct the original intent from first
    principles (it did, correctly). Corrective adopted and
    exercised same-arc: constraints citing prior proposals ship the
    proposal's notes.md text verbatim — now the §5
    verbatim-proposal contract (ratified 2026-08-03). Same
    finding's sibling: the execution-context manifest set omitted
    from a closeout pack — the evidence-13 include-set class's next
    occurrence, now spanning sub-orchestrators as packer; tallied
    there.

50. **First delegated orchestration arc completed.** A read-only
    design session (`2026-08-01-board-5-ledger-design-004`) ran the
    board-5 split end to end: six applied sessions, ratifications
    at its own level, and a structured upward report partitioned
    landed / ratified / escalated / on-watch. The report shape is
    the escalation-contract prototype for board 10's harness
    scoping. One-line corroboration of evidence 21's class at the
    sub-master level: the arc's own rev-A brief mis-derived the
    closure_reason first-carrier example (`continue-plan-005`;
    actual: `split-supersession-002`, 30 prior lacking), and the
    worker correctly implemented rule over example.

New from the 2026-08-04→05 sitting (the board-6 arc):

51. **One operator command per emission, and phases never share a
    message.** Two instances from the arc: the session-B
    precondition's three-command block, fed to a paste-hostile
    terminal, ran as one line and tar consumed the git commands as
    member names; and a must-run-later command stacked paste-ready
    below a must-run-first one let the operator's tree picture fall
    a session behind (the entry-53 chain). Standing corrective,
    adopted mid-arc: the single-line rule extends from pack
    commands to every operator command emitted — one command per
    block, or an explicit `&&` one-liner when the operator asks for
    one paste — with its pair: commands for different phases never
    share a message. (Arc report, findings 1 and 5.)

52. **When the second instance of a drift appears, fix the class,
    not the file.** Two chmod rounds for exec-bit drift the WSL
    mount re-imported on every copy; the close was at the source —
    `/etc/wsl.conf` automount metadata options, verified 644 on the
    mount — not a third per-file chmod. (Arc report, finding 2.)

53. **The misunderstanding-control doctrine functioned live on a
    redundant pack.** After an entry-51 ordering slip, session D's
    pack command was re-pasted after D had already applied and the
    reinstall hook had installed 0.3.29, so a stale goal rode
    forward against a tree that had moved past it. The receiving
    worker verified the tree against the goal, ran the suite,
    refused to fabricate a change set, and asked — live
    misunderstanding-control evidence, at the cost of one burned
    NNN and one unlock (the redundant
    `2026-08-05-board-6-stats-read-side-003` closed by operator
    unlock, no successor; its telemetry closure record is the
    durable trace). Corrective beyond entry 51's pair: the friction
    session's charter gains operator state legibility — `bale
    status` as the ground truth consulted before any pack when
    state is uncertain, a tooling-surface question as much as a
    discipline one. (Arc report, finding 5.)

54. **The version finding and the open doc-only cadence question.**
    The board-6 arc ran 0.3.27 → 0.3.29 with sessions A and B
    landed unbumped at 0.3.27 — the first cadence divergence,
    recorded in session C's notes. Post-arc,
    `execution-context-amendment-006` (doc-only) landed unbumped,
    then 0.3.30 (`archive-dir-005`) and 0.3.31
    (`pack-tree-echo-007`). A close-out arithmetic expecting 0.3.32
    assumed a bump for the doc-only 006; the live install reads
    0.3.31 (architect-verified 2026-08-05). Attribution: the 0.3.32
    claim originated in that close-out arithmetic — not in the
    arc's upward report (which claims 0.3.29, correct for its date)
    nor at the master desk. **Open ruling, recorded for
    ratification: are doc-only sessions bump-exempt?** If the
    ruling is that they owe bumps, 006 is the second cadence
    divergence and feeds the tag-reuse watch's counter; this entry
    states that conditionally, pending the ruling. Until it lands,
    the `execution-context-amendment-006` precedent (landed
    unbumped) governs doc-only sessions. [2026-08-05/06, closing
    note: the ruling landed — doc-only sessions are bump-exempt
    (§5, ratified 2026-08-05) — so `execution-context-amendment-006`
    is no second divergence; the tag-reuse watch counter stays at
    one.]

New from the 2026-08-05/06 sitting (the board-10 tidy-up):

55. **Handoff covering landed**
    (`2026-08-06-handoff-covering-001`): the covering refusal
    extended to the handoff path pre-sid — the invariant mapped,
    not pack's letter, so no NNN is burned on a refusal; scope
    computation hoisted for one-value; the admission flag mirrors
    pack's spelling and stamps true through the shared builder;
    §11 row 30; a schema description true-up caught in-scope beyond
    the brief's pin list; test home deviated to the session-C suite
    with reasoning. 232 green (session-claimed).

56. **Sweep json landed; the stamp question resolved as reasoned
    deferral** (`2026-08-06-sweep-json-stats-002`): the sweep json
    object landed across apply/unlock/revert. No telemetry stamp
    of sweep results: the next-attempt stamp has near-zero coverage
    (every sweep event is sid-terminal), and a sidecar breaks the
    clean-tree invariant exactly on the skip paths; the stats read
    side deferred with it per the charter's conditional. Both
    handoff-covering riders landed at their exact seams; no
    assertion loosening needed.

57. **The board-10 tidy-up sitting itself**
    (`2026-08-05-discuss-harness-011`): Bucket A ratified in chat,
    Bucket B landed serialized, the sitting-close deltas (this
    landing) carried the cargo. The Bucket B serialization was
    forced by execution-context include intersection over disjoint
    write sets — evidence 25's fourth tally; and this session's own
    bin/bale read-only include (one constant) is the same shape in
    miniature.

New from the 2026-08-07 sitting (the board-13 arc):

58. **The evidence-13 class's next occurrence,
    master-attributed at this desk:** the board-13 design brief's
    question 6 asked the worker to confirm wording of the §5
    execution-context contract — text living only in MASTER.md,
    deliberately unshipped. The worker searched, refused to guess,
    escalated (design brief Q1); the desk disposed it from the
    text's home. The class now includes brief-referenced unshipped
    text alongside unshipped imports and runtime files.

59. **Third successful §11.6 recovery**
    (`2026-08-07-board-13a-forecast-surface-004`): compaction
    after implementation, before validation; re-grounded, every
    hash recomputed at step 10, suite and lint re-run, feedback
    stamp set, apply clean. The
    disclosure-plus-mechanical-recomputation pattern holds for the
    third time (entry 12 carries the first two).

60. **First post-separation concurrent pair ran live** (B ∥ C,
    forecasts disjoint, zero unpredicted gate firings): the one
    out-of-forecast path (B's `tools/response_lint.py`, forced by
    the schema-embed coupling) was pre-enumerated in notes and
    admitted per path at apply — the generalized modified-file
    admission's first live use, same day as its ratification.
    Evidence 25's serialization class did not recur and is
    structurally closed.

## 7. Standing environment facts

- Architect on WSL; Windows Downloads at
  /mnt/c/Users/chord/Downloads/. Files saved via browser may carry
  CRLF: sed -i 's/\r$//' <file> if bale or a worker complains.
- A post_pack hook copies request tarballs to Downloads.
- Response archival is opted in at the global config layer:
  `archive_dir claude/responses` (the `archive_dir` candidate
  landed at 0.3.30). `[apply] sweep` landed default-off
  (`2026-08-05-auto-sweep-009`, 0.3.32), with the architect opted
  in at the global layer beside `archive_dir`; the manual
  telemetry/archive dance is retired. Archives now materialize on
  disk under `claude/responses/` (first landed at the 2026-08-07
  sitting).
- Tests: tests/ at repo root, stdlib unittest, no runner config —
  run python3 -m unittest discover -s tests. Enumerate suites from
  the tree (`ls tests/`), never from this doc; counts stated in
  briefs are claims to verify, and neither counts nor per-file
  lists belong here (both went stale within sittings — the history
  lives in git and telemetry). Named landmarks: shared sandbox
  harness at tests/harness.py (owns run_bale_pty and, as of
  `2026-08-07-board-35-apply-preflight-002`, build_response_dir /
  tar_response_dir; INSTALL_TREES
  copies bin/ docs/ schemas/ tools/ from repo root, but the
  recorded suite-run include baseline is **bin/ docs/ schemas/
  tools/ scripts/ + install.sh at root** — the suite also reads
  scripts/build.sh and install.sh from repo root, outside the
  INSTALL_TREES copy, the misses that cost
  `2026-08-06-verbose-thread-close-005` seven errors and
  `2026-08-06-v04-selftest-audit-006` two, per those sessions'
  includes_missing signals); test_readonly_pack.py
  drives the wizard via pty (likeliest flake site per its session's
  notes); test_apply_preflight.py is the apply reject/operations
  home; the bale_stats containment mirror is pinned by
  ContainmentMirrorTest; the fabricated-suspension helper follows
  test_revert_json.py's make_held_session precedent. ADR-0005
  (Accepted 2026-07-28) governs.
- Repo: ~/bale-src. bin/ modules: bale (4,111 lines after the
  8a/8b/8c arc), bale_pack, bale_apply, bale_config, bale_validate,
  bale_staging, bale_report, bale_rollback, bale_stats (the eighth
  sibling — a claim; landed at `2026-08-01-board-5-bale-stats-006`
  per the arc's upward report), _bale_toml. Load-time
  import set: pre-extraction it was bale_config, bale_validate,
  bale_staging, bale_rollback; the 8b/8c sessions refined the
  sibling lazy-import idiom, so re-verify the current set before
  scoping any include set that must execute bin/bale — evidence 13
  still governs. bin/bale VERSION 0.4.2 (trail: 0.4.0 → 0.4.1 at
  `2026-08-07-board-13a-forecast-surface-004` → 0.4.2 at
  `2026-08-07-board-13b-epoch-ledger-005`;
  `2026-08-07-board-13c-contract-docs-006` doc-only and
  `2026-08-07-board-35-apply-preflight-002` tests-only, both
  bump-exempt per the §5 cadence rulings), read from the constant
  in the copy shipped read-only with this sitting-close deltas
  request, `2026-08-07-sitting-close-deltas-007`, whose pack-time
  provenance stamp agrees (tree state; the live install trails
  one-apply-behind as ever).
- The registry's scope.json records the write forecast as of 0.4.1
  (ADR-0015); pre-separation open sessions read as over-forecasts
  (conservative, self-clearing at close).
- This document: `claude/MASTER.md` in the repo, tracked and listed
  in `INDEX.md`. Include it in any session that needs
  the gameplan; keep it out of sessions that don't (it is master
  context, not worker context, by default).
- Master-session working style: master authors every pack command and
  README brief (briefs delivered as downloadable files for
  --readme-file); architect pastes, runs, relays worker output
  verbatim; kickbacks and judgment calls come to the master for
  ratification. Notes.md is relayed for EVERY session, including
  post-merge (rationale: a v2-era relayed-notes loose end; the
  narrative lives in v3, in git). Worker packs are now authored
  with explicit `--write` forecasts; includes are weighed as
  context, not locks (ADR-0015).
  Session references in this doc use the full sid, or NNN
  qualified by sitting — bare NNN collides across same-day
  sittings (009's proposal, accepted 2026-07-31; going forward
  only, no retroactive sweep).
- One-apply-behind (meta-sessions §2): the apply that lands a change
  to apply-path code runs the OLD code one final time. Recurred four
  times in the v2 sitting; workers now flag it unprompted.

## 8. Foundation-audit findings register (008, 2026-07-13)

Traceability from finding to disposition; the board carries the work.

| # | Finding | Disposition |
|---|---------|-------------|
| 1a | validation.sh is a self-oracle (worker grades own work) | Board 6 (blind checkpoints) + board 4/5 (calibration streams) |
| 1b | validation.sh runs unsandboxed with operator privileges | Board 10 agenda item (harness prerequisite) |
| 2 | Own-scope drift × concurrency = silent clobber; created-collision error is safe but cryptic | Board 2 |
| 3 | Claim/verdict calibration signal evaporates into transient logs | Board 4 (first-class durable field) |
| 4 | No provenance: unversioned contract docs, unattributed responses | Board 4 (day-one stamping, §5 contract) |
| 5 | handoff.md reading plan carried standing authority | Fixed in master-doc-landing (§5 contract) |
| 6 | ~25K-token injected-contract tax per session; justification prose accreted | Board 7 |
| 7 | bin/bale docstring = 41KB changelog-in-code | Board 8 |
| 8 | §10.1 self-check is worker discipline, not mechanics | Board 4 (response lint) |
| 9 | Master state existed only by convention, outside the repo | master-doc-landing; evidence 17 |
