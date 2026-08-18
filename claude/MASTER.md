# bale master-session state — v5 — 2026-08-16

Handoff document for the bale-src master session. Purpose: re-seed a
fresh master-session chat with zero loss. To use: state current
progress against this file and continue. Regenerate at major
milestones. v5 supersedes the v4 (2026-07-31) doc in place; nothing
from it needs to be carried separately — v4 lives in git.

This document lives IN the repo at `claude/MASTER.md`, listed in
`INDEX.md`. Regenerate = edit in place; git keeps the history. It is
a project doc, not a global workflow doc — see §5 for the
categorization contract.

Last landed by: `2026-08-18-master-v5-regeneration-001`.
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

**Regeneration record (v4 + v5, condensed).** v4, 2026-07-31: the
read-only orchestrator session `2026-07-31-doc-compress-011`
authored the ratified brief and
`2026-07-31-master-v4-regeneration-012` landed the regeneration,
ratified via `2026-07-31-master-v4-ratification-microdeltas-013`
with the board-33 correction at `2026-07-31-board-33-recovery-015`.
v5, this document: authored at the 2026-08-16 cleanup-master
sitting, landed by this session, `2026-08-18-master-v5-regeneration-001`.
Full narratives in git.

## 3. In flight

- **Board-10 arc build is complete** (sitting
  `2026-08-10-continue-plan-001`, the spec-intake; the wave record
  and the remaining S6-only close live on the board 10 row).
  Latest applied: `2026-08-11-board-10-sandbox-wrapper-001` (S1),
  `2026-08-10-board-10-orchestration-doc-003` (S3),
  `2026-08-12-board-10-network-grant-001` (S2),
  `2026-08-12-board-10-wave1-deltas-002` (the wave-1 deltas),
  `2026-08-13-board-10-telemetry-extensions-001` (S5),
  `2026-08-13-board-10-escalation-schemas-002` (S4), and
  `2026-08-13-board-10-per-sid-checkpoints-004` (S7); the version
  position is §7's, its one home. The escalation contract is wire
  format now (schemas + validators live; the producer is S6's).
- Orchestration doctrine now lives at
  `claude/context/orchestration.md` (ADR-0009 step 2 done; step-3
  promotion trigger unchanged).

**Watches** (named re-triggers, no work; each entry names its own
source):

- Emitter-parser reconciliation drift: all three unparsed-
  reconciliation records are 2026-07-31 consolidation-day straddlers;
  everything post-consolidation parses. Re-trigger: any non-zero
  unparsed share in `stats --since 2026-08-01`. (Carried verbatim
  from the board-5 arc's upward report.)
- Drift-guard tag-reuse blindness (fires on tag-ahead, not reuse);
  bit once (002/007 collision, repaired). Re-trigger: third
  occurrence earns the guard a per-session-bump check. (Carried
  verbatim from the board-5 arc's upward report.)
- Mixed `at` provenance in clarification records (pre-0.3.27 read
  via mtime). Re-trigger: a stats consumer comparing per-record `at`.
  (Carried verbatim from the board-5 arc's upward report.)
- Closure-mix membership revisit. Re-trigger: real unlock-closure
  stamp accrual. (Carried verbatim from the board-5 arc's upward
  report.)
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
  (C's else-branch note makes it ~10 lines). (From the board-6
  arc's report.)
- `[validation]` layering: the deferred widening re-triggers only on
  a case that answers oracle-by-coincidence (disposition 1's trade,
  recorded in the rev B brief's D1). (From the board-6 arc's
  report.)
- Required-set keyed form: re-triggers on systematic per-class
  `[SKIP]` noise in the ledger's new rows. (From the board-6 arc's
  report.)
- Sweep current-branch commit skip predicate (a two-line change,
  named in `auto-sweep-009`'s notes). Re-trigger: the first
  observed off-target-checkout confusion.
- Plan-less handoff whole-tree refusal friction: a bailout whose
  reading plan cites no files resolves to whole-tree scope, so in a
  checkpoint-configured project every plan-less handoff now
  requires the admission flag. Shape kept deliberately (whole-tree
  really is covering; it mirrors a default whole-tree pack).
  Re-trigger: the first real-world plan-less handoff refusal; then
  decide fallback breadth vs. remedy text. (From the
  handoff-covering landing, `2026-08-06-handoff-covering-001`.)
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
  retried sessions. First datum accrued 2026-08-07: 011's unused
  tests/test_install_precheck.py forecast entry
  (`2026-08-07-board-35-handoff-happy-011`) — packer-side
  imprecision, master-authored pack; one accrual, no clustering,
  no action.
- Drift-gate residue on default-forecast checkpoint edits: a
  default pack's recorded forecast is `["."]`, so the apply-side
  drift gate would not catch a response landing an edit under the
  checkpoint directory in such a session — accepted and named at
  ratification (2026-08-13/14), not hardened; the per-sid stamp
  verification still gates a changed oracle for the session's own
  sid, and the executing checkpoint is base-tree bytes regardless.
  Re-trigger: the first observed landed checkpoint edit riding a
  default-forecast session; the remedy then is drift-gate
  hardening as its own session, never a quiet extension. (From
  `2026-08-14-bare-pack-excl-waiver-002`'s notes, §1.)
- Checkpoint-thinness HOLD clustering (the §5 reaffirmation's
  named watch): thinness — outcome-only oracles — is the pinned
  authoring lever. Re-trigger: HOLDs clustering on planner-fixture
  defects rather than worker misunderstanding; that clustering
  means authoring practice is the defect, and the fix is at the
  planner's desk, not the workers'.
- Dead ceremony checkpoint files (`current.sh`,
  `continue-plan-005.sh`, `restoration-006.sh`, `core-001.sh`
  under `claude/checkpoints/`) are inert clutter. Cleanup may ride
  any future sweep session; no urgency, no dedicated session.
- Amendment-accept stamps in HOLD-clustering reads: the two
  deliberate `stamp_matched: false` amendment accepts (board 10
  wave 3, `2026-08-13-board-10-telemetry-extensions-001`) must not
  read as oracle overrides in HOLD-clustering stats. Re-trigger:
  any HOLD-clustering read over the amendment stamps. (Routed from
  the improvement sitting's opening README, item 3.)
- `claude/INDEX.md` substring-pin false positives: the guard test's
  deny-list entry was accepted 2026-08-14/15 with its
  self-announcing false-positive profile — if
  `tests/test_global_doc_selfcontainment.py` fails on legitimate
  generic prose producing the substring, reword the prose or drop
  the entry; the failure announces itself, never silent.
  Re-trigger: the guard failing on prose that isn't a project-local
  citation. (From `2026-08-14-global-doc-selfcontainment-006`'s
  notes, ratified at the improvement sitting.)
- Forecast-refusal per-path counter (deferred at the 008 desk,
  2026-08-16): a pack refused at the forecast gate never receives a sid,
  so per-path refusal counts have no durable home today. Re-trigger: the
  harness observing refusals as control flow, or a pack-side refusal log
  wanted as new surface. (Rider item 5's deferral.)

**Fold-in registry** (one home, this list — the dated block v3
carried inside §2's 07-16 sitting summary is merged in; each entry
below was reconciled against shipped bytes at the v4 regeneration,
with the unverifiable ones carried verbatim and marked):

- run_hook's three placeholder-less f-strings — rides any session
  touching bin/bale section 23. Cosmetic.
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
- Checkpoint `bash -n` fail-fast: `check_response_shell_syntax`
  gates `apply.sh` and `validation.sh` only; a syntax-errored
  checkpoint surfaces mid-pipeline. Rides board 10 or the next
  session touching that function. (Source:
  `2026-08-07-sandbox-adr-009`'s surprises.)
- gather_files_for_pack verbose kwarg in cmd_handoff — rides the
  next session touching bin/bale's handoff surface. Text verbatim
  from `2026-08-07-board-35-handoff-happy-011`'s Proposals:
  "**What:** `cmd_handoff` calls `gather_files_for_pack(repo,
  extracted_paths)` without the `verbose` kwarg the function
  already carries, so `handoff --verbose` streams the build trail
  but not the filter-chain drop narration pack streams.
  **Why:** The accepted fold-in's text scoped this session to the
  `build_request_tarball` call, so I stayed in that lane — but the
  asymmetry is visible to a user: a reading-plan file silently
  dropped by the filter chain (typo, gitignored) is exactly what
  `--verbose` exists to narrate, and the dropped-candidates line
  in the session log is a coarser signal.
  **Scope hints:** `bin/bale` cmd_handoff (one kwarg), plus one
  assertion in `tests/test_handoff_happy.py`. Trivial rider for
  the next session touching that surface."
- Negation-refusal wording split — "Name the pattern's source in
  the negation refusal", rides the next bin/bale_pack.py touch
  (carrier restated 2026-08-14; its former co-rider, the
  build_request_tarball docstring stale sentence, was consumed at
  `2026-08-14-bare-pack-oneshot-003`, 0.4.10). What/Why
  verbatim from `2026-08-07-board-35-pack-guards-013`'s Proposals:
  "**What:** When `build_pack_matcher`'s combined parse trips the
  negation guard, the failure message says "invalid session
  exclude pattern" regardless of whether the offending line came
  from `--exclude` or from `.baleignore`. On the wizard path the
  file was pre-validated by `load_baleignore`, so the wording
  holds there; on the fully-specified CLI path a negation line in
  `.baleignore` reaches this branch and gets attributed to the
  session. Split the message by source, or re-validate the file
  lines separately before composing. **Why:** Observed while
  enumerating the composition surface this session (the code
  comment at the `fail()` assumes the file "was already validated
  by load_baleignore in any surface that called it", which the
  fully-specified path doesn't). A user who typed no `--exclude`
  and is told their session exclude pattern is invalid will look
  in the wrong place. I deliberately did not pin this wording in
  the suite so the fix isn't fighting a test."
- test_apply_preflight.py module-docstring history true-up: the
  "earlier behavior pin documented the identical-duplicate
  acceptance" line misattributes session 1, which deliberately
  pinned nothing there (`2026-08-07-board-35-small-pins-010`'s
  wrinkle). One line; rides the next touch of that file.
- A `--slow` convention for the test tree — conditional,
  deliberately unscheduled: the re-trigger is the first session
  whose additions would cross the §7.6 two-minute target, and
  that session builds the gate harness-level (tests/harness.py,
  validate.sh, a docs line) rather than per-suite. Current
  margin: ~111s scaled of 120s after board-35 session 4. What/Why
  verbatim from `2026-08-07-board-35-pack-guards-013`'s
  Proposals: "**What:** An opt-in env-var gate (e.g.
  `BALE_TEST_SLOW=1` + `skipUnless`) for generation-heavy cases,
  established once as a harness-level helper rather than
  per-suite. **Why:** This session brought the scaled wall to
  ~111s of the 120s target with nothing left to trim that doesn't
  cost audit-named coverage. The *next* generation-heavy suite
  won't have that luxury; better to introduce the convention
  deliberately (with `validate.sh` and the docs knowing about it)
  than as a side effect of whichever session first overruns."
- Pack-time "forecast/include mismatch" warning — warn when a
  `--write` names an existing file absent from resolved includes.
  Rides the next session touching bin/bale_pack.py. (Source:
  evidence 62's proposed counter.)
- DOCS.md §9 sanctioned-parallelism registration: MASTER.md §1
  four-controls floor ↔ orchestration.md §3 restatement (S3's
  ratified call 3). Rides the next DOCS.md-touching session.
- validate.sh's schema presence loop trued up to cover every
  shipped schema. Rides the next validate.sh touch. (Source: the
  S4 notes' proposal, `2026-08-13-board-10-escalation-schemas-002`.)
- Supersession writes its closure record BEFORE the sweep (or
  inside the sweep's commit set), plus one test pinning
  tree-clean-after-supersession. Evidence: in both of the
  2026-08-13/14 sitting's supersessions the sweep-commit line
  precedes the closure-record line in the session log, so bale
  created the very dirt its own dirty-target guard then punished —
  surfacing at the next apply's pre-flight, twice at once
  (transcript-ordered proof in the sitting log; §6 entry 74).
  Rides the next session touching the supersession close/sweep
  path.
- ADR-0015 disjointness remedy text: "narrow this pack" is the
  wrong remedy against a whole-tree open session — proven live
  this sitting, where a disjoint `--write` still refused (the open
  session's default forecast is `["."]` and intersects
  everything); the honest remedy is close/apply/unlock the open
  session, or narrow ITS forecast. Rides the next gate/report
  touch.
- Wizard checkpoint prompt candidate picker: list search-path
  candidates newest-first with path, mtime, and sha prefix; a
  free-typed path stays accepted. Rides the next pack-UX session.
- Handoff read-side parity — back on the registry after riding as
  the oneshot session's dropped stretch item (its §11.2 pre-flight:
  the core plus wizard and echo fit, the stretch did not earn the
  margin). Proposal text verbatim from
  `2026-08-14-bare-pack-excl-waiver-002`'s Proposals: "**What**:
  extend the read-side explicit-naming key (or a variant of
  auto-exclusion) to `bale handoff`, whose reading-plan forecast
  currently refuses on plain containment — a bailed bare-pack
  session's handoff with a whole-tree fallback plan still requires
  the flag. **Why**: this session restored the bare *pack*; the
  handoff path keeps the pre-v0.4.9 posture (deliberately
  untouched — it is both read set and forecast there, and changing
  it was not in the goal). If bare-shaped sessions start bailing,
  their handoffs will hit the same friction the master's own
  request did. **Scope hints**: `bin/bale` (cmd_handoff), the
  shared gate; only after A+B land, and probably alongside Change
  C's session since the refusal-text surface overlaps." [The
  "alongside C" window passed with the drop — C landed at 0.4.10
  without it.] Rides the next handoff-gate touch.
- CLAUDE.md §11.2 rescope-offer prose: decide/land the
  checkpoint-precondition sentence — whether §11.2 should set the
  expectation that checkpoint-configured projects put a checkpoint
  precondition in front of any scoped pack a pasted rescope command
  creates (source: `2026-08-15-claude-core-first-001`'s Proposals,
  second entry). Carrier: the next docs/CLAUDE.md touch; rider: the
  §11.2 ↔ §3.4 pair pin moves in the same session.
- Wiring-session brief riders (accepted from the birth session's
  Proposals): When the injection wiring lands: sweep BALE.md's two
  remaining "four" sites in the same response (§3.1 editable-docs
  note, §7 pipeline step 3), and true up any four-key
  `contract_docs` provenance example BALE.md shows.

Landed 2026-08-05, non-board (`2026-08-05-auto-sweep-009`):
calls recorded in v4 of this doc (git) and the sessions' archived
notes.

Ratified judgment calls dated 2026-08-06 at the master desk
(`2026-08-06-verbose-thread-close-005`,
`2026-08-06-v04-selftest-audit-006`, `2026-08-06-v040-cut-007`):
calls recorded in v4 of this doc (git) and the sessions' archived
notes.

Ratified judgment calls dated 2026-08-07 at the master desk
(`2026-08-07-board-13a-forecast-surface-004`,
`2026-08-07-board-13b-epoch-ledger-005`,
`2026-08-07-board-13c-contract-docs-006`):
calls recorded in v4 of this doc (git) and the sessions' archived
notes.

Ratified judgment calls dated 2026-08-07 at the master desk
(`2026-08-07-sandbox-adr-009`,
`2026-08-07-board-35-small-pins-010`,
`2026-08-07-board-35-handoff-happy-011`):
calls recorded in v4 of this doc (git) and the sessions' archived
notes.

Ratified judgment calls dated 2026-08-07 at the master desk
(`2026-08-07-sitting-close-deltas-012`,
`2026-08-07-board-35-pack-guards-013`):
calls recorded in v4 of this doc (git) and the sessions' archived
notes.

Landed 2026-08-13/14, non-board (the friction-removal sitting,
master `2026-08-13-continue-plan-005`): the sitting's goal was
commandeered from "continue the plan" to friction removal, on
explicit architect authority — the §3-override rule exercised as
designed (ratification 1 of the sitting). Two landings:
`2026-08-14-bare-pack-excl-waiver-002` (0.4.9 — Changes A+B:
checkpoint auto-exclusion with the explicit-naming read-side key;
the read-only checkpoint waiver stamping `checkpoint: null` +
`checkpoint_waived`) and `2026-08-14-bare-pack-oneshot-003`
(0.4.10 — Change C: `--checkpoint-file` commit-and-pack, the
wizard checkpoint prompt, the checkpoint identity echo, drop-log
summarization, the refusal-text updates, and the
`build_request_tarball` docstring rider consumed). Supersession
chain, recorded with its rationale: revC's session
`2026-08-13-bare-pack-restoration-006` was superseded by
`2026-08-14-bare-pack-core-001` (worker split: wizard + echo out),
itself superseded by `2026-08-14-bare-pack-excl-waiver-002`
(worker §11.2 pre-flight split: Change C out). Cost accounting:
the split cost two extra two-run-loop walks, accepted against the
mid-build-bail risk on Change C's edge matrix. Contract-level
ratifications: §5's 2026-08-13/14 block.

Ratified judgment calls, one line each, dated 2026-08-14 at the
master desk (002 = `2026-08-14-bare-pack-excl-waiver-002`, 003 =
`2026-08-14-bare-pack-oneshot-003`):

- The `bin/bale_report.py` out-of-forecast admission,
  planner-attributed: the every-refusal-names-its-real-remedy
  constraint forced it; the forecast missed it (002).
- Literal-base read-only packs keep stamping `{path, sha256}`; the
  waiver is `{sid}`-bearing bases only (002).
- The degenerate root-level `{sid}` base keeps the containment
  refusal — no root-file wildcard (002).
- The `locate_inbound_path` split: one non-failing resolution
  core, `resolve_inbound_path` a thin failing wrapper; every
  existing caller byte-identical in behavior (003).
- Never-silently-replace extended one rung earlier to uncommitted
  files at the resolved path: identical bytes proceed, differing
  bytes refuse loudly naming both sides (003).
- The post-wizard `[r]` contradiction refuses with the arg-parse
  message plus a remedy naming the wizard answer (003).
- The wizard checkpoint prompt always asks — no already-committed
  special case, so idempotent re-runs see one question sequence
  (003).
- The identity echo's path is the resolved SOURCE path; the
  in-repo resolved path already rides the provenance stamp line
  (003).
- Drop-log summarization threshold strictly >1 — a single drop
  keeps the 0.4.9 per-file line verbatim, sentinels intact (003).
- Commit subject `bale:`-prefixed and pathspec-limited — a dirty
  tree's other staged work untouched (003).

Landed 2026-08-14/15, non-board (the improvement sitting, read-only
master pack `2026-08-14-improve-bale-005` — the bare read-only
waiver's live debut, worked as designed: forecast `[]`, nothing
landed under its sid). Produced: the doc-efficiency audit, the
self-containment ruling, four sessions, all applied —
`2026-08-14-global-doc-selfcontainment-006`,
`2026-08-15-claude-core-first-001` (r3 after the first live
cross-session race — §6 entry 76),
`2026-08-15-doc-mechanization-002` (r2 after a size-floor
checkpoint HOLD), and the tarball-riders micro-session
`2026-08-15-tarball-riders-003` — and the grown PLANNER.md brief
(board 10's queue entry; inputs grown at this landing, charter
resolved — see the entry). Carry-forward item 5 from the
sitting-opening README: the registry-attribution correction
ratified — record only, no registry change.

Ratified judgment calls, one line each, dated 2026-08-14/15 at the
master desk (006 = `2026-08-14-global-doc-selfcontainment-006`,
001 = `2026-08-15-claude-core-first-001`, 002 =
`2026-08-15-doc-mechanization-002`):

- The thirteenth citation site (the §5.9.2 orchestration.md
  deferral) genericized — goal-over-enumeration precedence
  affirmed (006).
- orchestration.md added to the guard test's deny list (006).
- The `claude/INDEX.md` substring pin accepted with its
  self-announcing false-positive profile; the §3 watch above is
  its record (006).
- The §5.3 telemetry-record path dropped as
  implementation-contract (006).
- Tombstone content-loss verification accepted (006).
- The no-propagation pair judgment ratified — §11.2's side of the
  sanctioned pair is by-reference, and every referent survived the
  sibling's rewrite (001).
- The §11.6 re-read prescription deliberately kept (001).
- The label-column cap ratified DE NOVO at 40,
  overflow-not-truncate — the registry entry's own "unverified"
  bracket was accurate; the implementation plus
  `test_label_column_is_capped` are the constant's first durable
  home (002).
- Exec bits on the four shipped .py files ratified (002).
- Prune stems ratified as weakest-honest; the `archive:`/`delete:`
  tag convention noted, unqueued (002).
- ADR reverse-transform generosity ratified — the quotable
  reasoning on record: candidate-set looseness is free because
  pre-image sha256 equality either reproduces the shipped bytes or
  fails, so a looser recognizer cannot sanction a third diff
  shape (002).
- CODE.md §10 prune-row deferral ratified (002).

Ratified 2026-08-16 at the master desk, by exercise: the desk
pasted and applied `2026-08-16-planner-birth-003` ahead of S6,
discharging the sitting-close-001 "ratify at next sitting open"
carry in the act. The injection-wiring follow-up rides ahead of S6
with it. No renumbering; board 10's bracket annotation below is
the record.

Judgment calls, dated 2026-08-16 at the master desk:

- Master-desk oracle authorship affirmed: the charter's
  never-oracle-authorship clause binds the worker→planner
  mid-session transition, not the sitting desk; checkpoint
  authoring is part of pack authoring, and punting one to the
  architect is a §1 friction violation, not blindness discipline.
- Paste-surface hazard observed (live specimen): chat prose
  framing a paste-ready command carried backticks that left the
  shell in an open command substitution after the pack ran; the
  pack itself was unaffected (identity echoes byte-matched).
  Practice: framing prose around command blocks stays
  backtick-light; the block ends the message section. Evidence-pile
  entry; eventual home PLANNER.md's brief-practice section at S6
  churn.
- Checkpoint-runner lesson (checkpoint desk's miss): the
  planner-birth checkpoint invoked pytest; the guard suites are
  stdlib-unittest and the probes SKIPped blind on the target box.
  Future checkpoints on this repo invoke python3 -m unittest.
- Birth-session flagged calls, all nine ratified as shipped:
  read-path row merged not stacked; selfcontainment deny-list
  entry kept (tombstone is still project-local); evidence-N
  markers kept (numeric-ADR-pointer precedent); tombstone carries
  the 12-row section map (DOCS.md §6.4 applied to whole-doc
  relocation); four→five true-ups beyond the brief's list accepted
  (self-consistent doc set beats one-apply-behind description;
  inertness pre-ratified); BALE.md's two current-behavior "four"
  sites deliberately deferred to the wiring session (rider
  accepted); provisional-until-S6 placement as shipped, ratified
  pieces unmarked; PLANNER.md §7 Hard Rules table kept; the §3.4
  migration question noted-not-engraved.

Landed 2026-08-16, the sitting-close-deltas-005 response, with one
HOLD→correction. Ratified at the desk, recorded here:

- Close-005's placement and formatting calls, all ratified as shipped:
  §3-end accretion for the relayed sections, chronological bracket
  ordering (ratified, then EXECUTED), scaffolding headings dropped with
  body text byte-verbatim after whitespace normalization, re-wrap to
  file conventions.
- The brief-transport chain closed end to end: shipped brief was stale
  (search path resolved an old download); sections supplied by desk
  relay; worker verified landed-vs-relay mechanically; desk attests
  relay-vs-authored (mechanically extracted from the file hashing
  ffa09e5298e2, byte-verbatim by construction).
- The close checkpoint HOLDed on a fixture defect — a wrap-blind grep:
  the engraved clause hard-wraps in this file, so the probe counted zero
  at base and would have held any response. Second checkpoint-desk miss
  of the sitting (the pytest runner was the first). New desk rules,
  ratified: probe phrases are matched wrap-tolerant (this file's column
  convention guarantees long phrases split), and every checkpoint is
  dry-run against real bytes before delivery — the amendment that fixed
  this HOLD ate both rules first.
- The correction ran under the board-6 provenance gate as designed:
  retry refused on the stamp mismatch, the desk accepted deliberately
  per the wave-3 precedent, and stamp_matched false is the truthful
  mechanical record of a planner amendment landing after pack.
- Closure-kind blemish, recorded so the ledger stays honest: the first
  wiring session closed by hand-run unlock where superseded-by-split was
  the intent (the informal recipe the supersession flow retired), so the
  day's telemetry undercounts supersessions by one and overcounts
  abandonments by one. Record only; the trust ledger aggregates on
  closure kinds, and a silent miscount is the failure shape this system
  exists to prevent.

Landed 2026-08-16, `2026-08-16-planner-injection-wiring-006` at 0.4.11 —
the five-doc era: GLOBAL_DOCS, the provenance stamp, both schema pins
(allowed-not-required, rationale carried in the schema descriptions),
both release lists, the lint embed, and BALE.md's two deferred sites, in
one response. The post-apply hook ran the merged reinstall and the
install caught up, closing the stale-install window the birth apply
opened. Full 481-test sweep green; the response's own four-key echo was
the admission posture's first live case, by design. Probe-verified
negatives are recorded in the session's notes (telemetry schema
unpinned, reinstall list runtime-derived at run time, no four-key JSON
example in BALE.md); the notes are the record.

Ratified judgment calls, one line each, dated 2026-08-16 at the master
desk (006 = `2026-08-16-planner-injection-wiring-006`):

- Exactly-the-set assertions ratified — the pack E2E's doc set and the
  provenance keys equal GLOBAL_DOCS, not membership; a stray sixth doc
  fails loudly (006).
- Count-free internal comments ("beside the global docs") with explicit
  "five" at BALE.md's user-facing sites — internals count-immune, user
  docs current (006).
- New tests/test_planner_admission.py over extending existing suites —
  the posture spans both schemas; WaiverSchemaUnitTest precedent
  followed (006).
- Schema descriptions carry the allowed-not-required rationale inline —
  the schema alone answers the why (006).
- validation.sh gates the full sweep behind a slow flag; the default run
  stays under the section 7.6 target (006).
- Predicted-basis claims accepted as declared (build.sh end-to-end,
  upgrade.sh unshipped); the staged run was the proof (006).

## 4. The board

Ordering is the recommended sequence; small sessions first, the
compression sitting before harness scoping. Item numbers are
identities, not sequence — they are cross-referenced from §5, §6,
and §8, so done items keep their numbers as one-line pointers.

1. **staging-from-target-base — DONE** 2026-07-13/14 sitting
   (pre-telemetry; home: git).

2. **drift-to-contract apply gate — DONE** 2026-07-15 (sid
   `2026-07-15-drift-gate-002`; telemetry).

3. **pack no-brief guard — DONE** 2026-07-13/14 sitting
   (pre-telemetry; home: git).

4. **Feedback telemetry + response lint — DONE** 2026-07-13/14
   sitting, three sessions (pre-telemetry; home: git).

5. **bale stats / the trust ledger — DONE** 2026-08-03, closed as
   an arc (sids `2026-08-01-board-5-ledger-design-004` read-only,
   `2026-08-01-board-5-telemetry-promotion-005`,
   `2026-08-01-board-5-bale-stats-006`,
   `2026-08-01-stats-packaging-closeout-007`,
   `2026-08-03-stats-residual-bucket-002`,
   `2026-08-03-preserved-at-and-retag-003`; telemetry; the arc's
   upward report).

6. **Blind validation checkpoints — doctrine to mechanics — DONE**
   2026-08-05, closed as an arc (sids
   `2026-08-04-board-6-blind-checkpoint-design-003` read-only,
   `2026-08-04-board-6-checkpoint-core-004`,
   `2026-08-04-board-6-superset-gate-005`,
   `2026-08-04-board-6-blindness-enforcement-006`,
   `2026-08-05-board-6-stats-read-side-001`; telemetry; arc report
   and briefs at `claude/context/board-6-arc/`).

7. **Doc compression sitting — editorial phase COMPLETE**
   2026-07-15/16 (sids `2026-07-15-tarball-ux-extraction-011`,
   `2026-07-15-tarball-compression-012`,
   `2026-07-16-claude-preflight-compression-001`; telemetry).

8. **shrink-bin/bale arc — CLOSED** 2026-07-16 (sids
   `2026-07-15-docstring-prune-005`,
   `2026-07-15-pack-path-extraction-010`,
   `2026-07-16-apply-path-extraction-002`; telemetry).

9. **Cross-project ADR + implementation** — LINKED sessions, not
   fused. Level 1: --link, shared link id, same interface-contract
   brief into both requests (the seam MUST be named). Level 2:
   cross-repo depends_on. Level 3 (two-phase commit): deferred,
   likely forever.

10. **Harness scoping master-session — spec-intake DONE,
    "arc build complete"** 2026-08-10/13: sitting
    `2026-08-10-continue-plan-001` (repack of spec-intake-015)
    ratified the S1–S6 decomposition, the three additions, and the
    specification-friction principle. Wave 1 — S1 sandbox at 0.4.4
    (`2026-08-11-board-10-sandbox-wrapper-001`, HOLD→retry, root
    cause recorded in evidence), S3 orchestration.md
    (`2026-08-10-board-10-orchestration-doc-003`, six judgment
    calls ratified per its notes). Wave 2 — network grant + sandbox
    telemetry + VERSION extraction at 0.4.5
    (`2026-08-12-board-10-network-grant-001`, HOLD→correction:
    nested-namespace phantom-mount fix; first exercised grant on
    record) and the wave-1 deltas landing
    (`2026-08-12-board-10-wave1-deltas-002`, chat-resolved item-2
    mapping ratified). Wave 3 — telemetry extensions at 0.4.6
    (`2026-08-13-board-10-telemetry-extensions-001`,
    HOLD→correction with two planner checkpoint amendments;
    stamp_matched false recorded deliberately). Wave 4 — escalation
    schemas at 0.4.7
    (`2026-08-13-board-10-escalation-schemas-002`, four
    packaging-coupling admissions). Judgment calls for all four:
    ratified per their notes. Wave 5 — per-sid checkpoints at
    0.4.8 (`2026-08-13-board-10-per-sid-checkpoints-004`, S7:
    `[validation] base` gains the `{sid}` placeholder so sessions
    stop sharing one oracle file; the pattern-aware pre-sid
    blindness gate, `peek_session_id`, and the pre-allocation
    resolved-existence refusal per its archived notes; its
    handoff-under-pattern E2E proposal queued onto board 35).
    Remaining: S6 only (harness spec-intake, packed fresh).
    Charter: spec-intake ritual (decomposition + ambiguity
    questions + checkpoint plan ratified BEFORE anything spawns),
    escalation contract as schema, promotion of the
    orchestration-doctrine doc; then harness build + phased trust
    rollout; recursion depth earned last. **Named agenda items
    added from the 008 audit:**
    - **Sandbox validation.sh execution** — today it is worker-
      authored code run via bare subprocess in staging with the
      operator's privileges, network on, filesystem open, writes
      self-declared. Fine while a human reads every script; a
      non-negotiable prerequisite for unattended workers (network
      off, FS confined to staging). ADR-0005's hermeticity doctrine
      knows why; it doesn't yet cover this surface. [2026-08-07:
      doctrine half closed — ADR-0016 Accepted (ratified
      2026-08-07 at the master desk; flip landed this vehicle);
      the implementation half remains here, now unblocked:
      mechanism selection under the WSL constraint, the invocation
      wrapper, the per-invocation escape flag, the per-project
      network-grant config surface, the env allowlist, and the
      checkpoint bash -n fail-fast candidate (§3 fold-in
      registry).]
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
      physical split is ever revived. [2026-08-14/15:
      considered-and-parked — work-class-keyed gating of
      DOCS.md/CODE.md was proposed and rejected at the improvement
      sitting on the audience principle (doc-rides-code makes the
      straddle rate structurally high; a stranded worker has no
      fetch path); re-decidable only after the transport decision
      this item exists to make.]
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
    **Added at the wave-1 landing (2026-08-12), for S6:**
    - **Per-session blind checkpoints** — the single-path
      `[validation] base` mechanism shares one committed checkpoint
      across concurrent sessions (wave 1 finding); the harness era
      needs per-sid checkpoint binding.
    **Added at the close-out landing (2026-08-13), for S6:**
    - **The `subsumes` entry notation is fixed by the producer** —
      deliberately unpinned today.
    - **"stats read sides deferred" pending accrued data** (sandbox
      stamps, cost fields, claim_basis). Re-trigger: harness
      telemetry accruing. [2026-08-15: add the claim_basis cut —
      split claim/verdict agreement rates by `claim_basis`
      (observed vs predicted); `2026-08-15-doc-mechanization-002`
      filled five of six claims observed, the calibration stream
      arriving (the cut proposal is in its Proposals).]
    **Added at the 2026-08-13/14 friction-removal sitting, feeds
    S6:**
    - **Planner-doctrine extraction — EXECUTED** (working name
      became `docs/PLANNER.md`; both charter rulings lifted to §5,
      their one home): `2026-08-16-planner-birth-003` —
      docs/PLANNER.md born, S6 inherits ratify-and-churn of the
      orchestration half — and
      `2026-08-16-planner-injection-wiring-006` — injection wiring
      landed, the five-doc era live at 0.4.11. Pre-execution
      inputs and the charter's working copies live in v4 of this
      doc, in git.
    **Added at the 2026-08-14/15 improvement sitting, feeds S6:**
    - **HOLD-triage / ruling-request artifact exchange** — ranked
      high on the S6 agenda. (Routed from the sitting-opening
      README, item 2.)
    - **Orchestration.md promotion — DISCHARGED EARLY** by chat
      ratification (2026-08-15, third round), deliberate: the
      planner doc is ONE doc, PLANNER.md, core-first — authoring
      doctrine as core, orchestration doctrine past the banner
      with harness-era sections marked provisional-until-S6
      inline; orchestration.md merges in at the extraction session
      (relocation + tombstone per standing conventions; its six
      ratified judgment calls keep their status). Rationale,
      quotable: planner-vs-orchestrator is a topic boundary inside
      one injection audience, and the gate-by-audience principle
      plus the one-doctrine-one-home rule (ratified at
      tarball-riders, sentence scale) forbid splitting one
      conditional layer across two files. ADR-0009's ladder
      corrects to: explainer → section of the conditional-layer
      doc; any physical re-split defers to this board's
      injection-model decision like every other split, with the
      banner as the pre-marked seam. S6 inherits "ratify and
      churn the orchestration half of PLANNER.md" in place of
      the promotion item.
      [2026-08-16: lifted to §5.]
    **Added 2026-08-16, from the architect, at the master sitting:**
    - **Session-interaction mechanization mandate** — ratified
      direction: the relay surfaces exercised this sitting all route
      through the architect as transport (probe paste-backs,
      clarification relays, HOLD reveal and correction relays, brief and
      checkpoint transport, stale-copy detection by eye), and the
      direction is to mechanize worker↔planner artifact exchange well
      beyond the current state; this sitting's transcript is the
      evidence corpus. Feeds S6's harness spec-intake and the
      escalation-contract item; the readme-hash row below is the first
      mechanization queued under it.
    **Added 2026-08-16, from the 008 rider, for S6:**
    - **Who audits thin checkpoints at scale** — once
      checkpoint-authoring is the bottleneck, checkpoint quality needs
      an audit surface; PLANNER.md §4's standing watch covers false-HOLD
      clustering (quality-in-the-negative), and the positive half is an
      open S6 question. (Rider item 6.)
    - **The hostile-foreign-repo arc's findings feed the harness spec**
      (board 45). (Rider item 4.)

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
    `2026-07-15-status-staging-row-003`; telemetry).

13. **read-vs-write separation — DONE** 2026-08-07, closed as an
    arc (sids `2026-08-07-board-13-read-write-design-003`
    read-only, `2026-08-07-board-13a-forecast-surface-004`,
    `2026-08-07-board-13b-epoch-ledger-005`,
    `2026-08-07-board-13c-contract-docs-006`; telemetry; design
    artifacts at `claude/context/board-13-arc/`).

14. **Doc-compression sitting, structural phase — RETIRED AS
    MISFRAMED** 2026-07-25 (chat-ratified; evidence 32; home:
    git).

15. **7c — doc-gap audit + landing — DONE** 2026-07-21 (sids
    `2026-07-21-doc-gap-landing-002` and the same-sitting
    follow-on `2026-07-21-lint-schema-refresh-004`; telemetry).

16. **Transition-branch retirement — DONE** 2026-07-21 (sid
    `2026-07-21-transition-branch-retirement-003`; telemetry).

17. **DOCS.md sanctioned-pairs one-liner — DONE** 2026-07-25 (rode
    22a — sid `2026-07-25-tarball-core-first-004`; telemetry).

18. **retry flag parity — DONE** 2026-07-21 (sid
    `2026-07-21-retry-flag-parity-005`; telemetry).

19. **retirement cleanup — DONE** 2026-07-21 (sid
    `2026-07-21-retirement-cleanup-007`; telemetry).

20. **handoff refusal + numbering restoration — DONE** 2026-07-21,
    applied 2026-07-22 (sid
    `2026-07-21-handoff-refusal-numbering-008`; telemetry).

21. **Extend main()'s install sanity check to handoff — DONE**
    2026-07-25 (sid `2026-07-25-handoff-install-precheck-003`;
    telemetry).

22. **Global-doc mechanization arc (the worker toolkit) — CLOSED**
    2026-07-31, all four phases DONE (22a
    `2026-07-25-tarball-core-first-004`, 22b
    `2026-07-29-craft-tool-v1-007`, 22c
    `2026-07-31-craft-kinds-v2-003`, 22d
    `2026-07-31-probe-scaffold-22d-004`; telemetry; the ratified
    mechanize-shape pattern: §5).

23. **test-layout-docs — DONE** 2026-07-28 (sid
    `2026-07-28-test-layout-docs-004`; telemetry).
24. **Scopeless packs + the scope wizard question — DONE**
    2026-07-28 (sid `2026-07-28-scopeless-packs-003`; telemetry).

25. **Closure telemetry — DONE** 2026-07-29 (sid
    `2026-07-29-closure-telemetry-001`; telemetry).

26. **Split supersession — DONE** 2026-07-29 (sid
    `2026-07-29-split-supersession-002`; telemetry).

27. **Lifecycle docs close-out — DONE** 2026-07-31 (sid
    `2026-07-31-lifecycle-docs-closeout-007`; telemetry).

28. **Rollback telemetry — DONE** 2026-07-29 (fused with 29; sid
    `2026-07-29-lifecycle-telemetry-parity-006`; telemetry).

29. **unlock --json parity — DONE** 2026-07-29 (fused with 28 —
    sid `2026-07-29-lifecycle-telemetry-parity-006`; telemetry).

30. **INJECTED_TOOLS consolidation + revert --json + VERSION —
    DONE** 2026-07-29 (sid
    `2026-07-29-injection-consolidation-revert-json-008`;
    telemetry).

31. **Worker-toolkit residue (from 22d's audit) + VERSION — DONE**
    2026-07-31 (sid `2026-07-31-worker-toolkit-residue-008`;
    telemetry).

32. **bale status clarification hint — DONE** 2026-07-31 (sid
    `2026-07-31-board-32-status-clarification-hint-018`;
    telemetry).

33. **Read-only session lifecycle — DONE** 2026-07-31 (sid
    `2026-07-31-board-33-readonly-lifecycle-017`; telemetry).
    [2026-08-03: this row's own spec line
    carries the literal it names inline. Safe today — the read-time
    refusal is scoped to `--readme-file` per this row's ratified
    judgment calls, and MASTER.md ships in `context/`, never as a
    README — but any future widening of the refusal's scope to
    shipped context files must account for this doc tripping it.
    Observed in `2026-08-03-master-deltas-005`'s notes, concurred by
    the master; no scope change made or implied.]

34. **v0.4 cut — DONE** 2026-08-06, closed as an arc (sids
    `2026-08-06-verbose-thread-close-005`,
    `2026-08-06-v04-selftest-audit-006`,
    `2026-08-06-v040-cut-007`; telemetry).

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
    (`2026-08-07-board-35-apply-preflight-002`; telemetry).

    Session 2 — DONE 2026-08-07
    (`2026-08-07-board-35-small-pins-010`; telemetry).

    Session 3 — DONE 2026-08-07
    (`2026-08-07-board-35-handoff-happy-011`; telemetry).

    Session 4 — DONE 2026-08-07
    (`2026-08-07-board-35-pack-guards-013`; telemetry).

    Remaining queue: the ranked gap list 1–7 is complete. The row
    stays open owning three queued residuals with named carriers:
    the row-21 declared-untracked-inputs pin (needs target-base
    choreography), the post-epoch stats-corpus fixtures (rides
    the next test_stats_aggregation.py touch), and the
    handoff-under-pattern E2E (queued 2026-08-14 from
    `2026-08-13-board-10-per-sid-checkpoints-004`'s Proposals:
    bailout → `bale handoff` on a `{sid}`-base project, asserting
    the pre-allocation refusal for the new sid and the stamped
    resolved path; cheap once test_handoff_happy.py's bailout
    fixture lifts into harness.py per the one-harness doctrine).

36. **`--checkpoint-file` expected-sha argument** — queued
    2026-08-14/15 (small, timing open): an optional expected-sha
    argument so delivery verifies the checkpoint bytes against the
    planner's published hash — the mechanical half of the
    Evidence-45-class practices (version-suffixed checkpoint
    filenames, publish the sha256 with delivery, compare the echo)
    now in board 10's PLANNER.md inputs. (Routed from the
    improvement sitting's opening README, item 1.)

37. **Bail-mechanism recalibration** — queued 2026-08-14/15,
    ratified direction: the CLAUDE.md §11.3–§11.5 bail mechanism
    has zero live firings against observed compaction events —
    recalibrate rather than prune. Three parts: (1) re-ground
    §11.3's triggers in observable signals (cleared tool results
    in context, compaction markers, request-size-vs-remaining-work
    arithmetic at pre-flight) instead of introspective budget
    perception; (2) crafter `--bailout` emission so the crisis
    procedure is a command, not a reading assignment (carrier: the
    next tools/craft_response.py touch, or this entry's own
    session); (3) a bail marker in notes/telemetry so bail
    frequency is measurable — silence indistinguishable from
    refusal is not evidence of health. Mitigating fact for the
    record: the §11.2 pre-flight catches unfittable scope at
    session open (the improvement sitting's opener included), so
    some upstream silence is by design. Motivating datum: §6
    entry 79.
    [2026-08-16: gains the single-window-premise paragraph as a rider —
    one paragraph in PLANNER.md's orchestration half naming the
    everything-fits-one-window premise a revisitable bet with softening
    conditions (window growth, caching economics, session persistence);
    carrier ratified at the 008 desk — the bail machinery is the
    premise's machinery, so the conditions-to-soften paragraph rides
    naturally here. ADR appends kept as the fallback, not the plan.
    (Rider item 9.)]

38. **Stats-digest auto-include for planner-shaped packs** — queued
    2026-08-14/15 (small, timing open): mechanizes and then deletes
    the "master packs prefer a digest" practice line from board
    10's PLANNER.md inputs, per the mechanize-first rule.

39. **Open-forecasts snapshot in pack provenance** — queued
    2026-08-14/15 (small, timing open): open sids plus their
    forecasts stamped at pack time; motivated by the core-first
    race, where the worker priced risk against a sibling whose
    `[]` forecast made it structurally zero (§6 entry 76);
    candidate scope is all scoped requests.

40. **readme/brief transport integrity** — mechanize the
    publish-the-sha/compare-the-echo practice for briefs: a
    --readme-sha256 companion to --readme-file that refuses the pack
    when the resolved file's hash disagrees, and/or fold README
    candidates into the queued candidate-picker rider's newest-first
    listing (path, mtime, sha prefix). Motivating specimen: the
    close-005 stale-brief transport failure — the echoed sha256 was
    available and nothing compared it; the miss cost a clarification
    round. Proposal source: close-005's notes, accepted at the desk
    2026-08-16. Scope hints from the proposer: the readme-file
    resolution in the pack path, the pack report echo; adjacent to the
    wizard checkpoint candidate-picker rider, possibly the same carrier.

41. **base-drift stamp + gate** — queued 2026-08-16 (small, well-shaped;
    adjacent to board 39, plausibly the same carrier): per-file base
    sha256s of resolved forecast paths stamped into request provenance
    at pack; apply compares for the intersection of changes[] with the
    stamp; refuse by default with a per-path override flag (the
    allow-out-of-scope admission pattern); refusal is a distinct,
    dispatchable outcome with a telemetry row (the scope-drift-refused
    precedent); retry needs nothing special — a repack restamps against
    the current base by construction. Ratified defaults (008 desk):
    per-file granularity, not whole-tree (a tree hash would
    false-positive on every sibling landing anywhere); refuse-not-warn
    (warn-and-proceed is the silent-skip bug CLAUDE.md §6 names). Hazard
    on record, sharper than the originating critique stated: files/ is a
    whole-file mirror, so applying against a moved base silently reverts
    intervening edits to the same file — a lost-update that validation
    can pass right over. The fix's exact pattern already ships: the
    checkpoint provenance stamp (pack-time sha256, apply-time
    comparison, refuse with a named override). (Rider item 3.)

42. **telemetry field additions, wave 1** — queued 2026-08-16 (small;
    documentation + schema): a self-reported docs_read field in the
    feedback block's self-reported stream — the list of docs and
    sections the session actually read, weighted as self-report like
    everything else there; and an optional origin enum on the
    clarification question row, values intent-gap or
    probe-forbidden-environment, following the v0.4.7
    additive/legacy-tolerant pattern (legacy rows keep validating).
    Consumers named at birth per the disposal doctrine (§5, 2026-08-16).
    Doctrine carried with the origin tag: both origins still indict
    packing — a probe-forbidden environment gap is an
    include-completeness failure under a probe ban — so the tag does not
    de-noise the packing signal; it splits it into two different fixes
    (brief/decomposition vs include completeness), which is the value.
    Sequencing: before or with board 43. (Rider items 1 and 7.)

43. **TARBALL.md section-5 compression pilot** — queued 2026-08-16 (one
    session; gated on or riding alongside board 42's docs_read so the
    before/after comparison is honest): mechanize-relocate per the
    ratified keep-list — the four claim values and the subset rule,
    deferred-vs-Proposals, what earns a notes.md, out-of-forecast drift
    enumeration, probe-vs-clarification-vs-bailout selection stays as
    judgment prose; one-home reconciliation with the schema description
    strings, which already duplicate TARBALL.md prose in places (schemas
    live in the installation, never in the every-session read path, so
    relocation wins under both transport models); version-history
    clauses split — live tolerance rules stay, rephrased without version
    numbers, pure archaeology relocates to the ADR/changelog layer;
    tombstone one-liner compliance per DOCS.md §6.4 (compliance, not a
    change needing ratification); §5.9 and §5.9.1 collapse to a pointer
    with §3.3 as the one home; ADR-0013 citations gain their section key
    so drill-down lands instead of scanning; plainer style as a rider
    only, never a standalone yield source. Compare the rewritten section
    5 with the architect before touching anything else. The two-thirds
    reduction target is explicitly not adopted (evidence 26); 008 sizing
    estimate for the record: mechanization-relocation plausibly takes a
    third to half of section 5. Standing caution: DOCS.md §9 sanctioned
    pairs collapse only by explicit desk decision, never as cleanup in
    passing. Named for the pilot's notes: the crafter-to-lint loop
    becomes more load-bearing once shape prose leaves — acceptable,
    since lint findings cite section, expected, and got. (Rider item 2.)

44. **stats drill-down read sides** — queued 2026-08-16 (one or two
    sessions; the worker may split at a §11.2 seam): level 1, bucket sid
    membership — anomalous rates name the sids composing them (the sets
    are computed internally already, just not emitted); level 2, the
    session dossier — one sid rendered whole: record, claim/verdict
    pairs, checkpoint outcome, clarification records, and the corrects
    lineage chain so a HOLD-to-retry arc reads end to end, replacing
    hand-jq across three directories with one command. Plus the queued
    no-new-fields cuts: claim-coverage aggregates
    (claims-per-validated-attempt ratio;
    empty-claims-with-nonempty-validation_will_run counts, cut per work
    class and per packer — gaming shows in aggregate trends, which is
    where the trust ledger already looks); checkpoint catch rates per
    work class; the claim_basis observed-vs-predicted split (already
    queued on board 10); and outcome rates per contract-doc-hash epoch —
    the read side that makes doc changes A/B-able, worth a docs
    paragraph naming it as an intended use. Binding constraints: the
    renderer never owns the numbers (PLANNER.md §17 — every drill
    surface stays a read side over the records, exercisable by jq); and
    nominate, never curate (§5, 2026-08-16). (Rider item 6 and rider
    §2.3.)

45. **hostile-foreign-repo arc** — queued 2026-08-16 (multi-session arc;
    feeds S6; sequenced before any harness autonomy): deliberately run
    arcs on an ugly foreign codebase — flaky tests, generated code, a
    hot package.json, no doc discipline — to find where the contract
    chafes before autonomous spawning. Watch: hot-file forecast
    serialization, validation runtime budgets, the ceremony floor on
    tiny changes, whether misunderstanding-dominates holds outside
    doc-shaped work, and (008 addition) probe round-trip economics on a
    project where the architect cannot answer environment questions from
    memory. This is §18's proven-by-hand commitment applied to project
    diversity, not just trust rungs. (Rider item 4.)

46. **small doc deltas, one carrier** — queued 2026-08-16 (one doc
    session): PLANNER.md §11 gains the hot-file sentence —
    file-granularity forecasts serialize hot files; decompositions route
    around them or serialize through them deliberately (rider item 5);
    TARBALL.md §3.2 gains the scopeless-sitting goal exemption line,
    ratified phrasing direction: the goal is one sentence per unit of
    forecasted work; a scopeless sitting's goal names its agenda (rider
    item 8; 008's own multi-sentence goal is the live specimen);
    PLANNER.md gains the calibration-sitting doctrine paragraph (§5's
    2026-08-16 block is the contract of record until this lands); and
    the telemetry disposal policy rows land at the home the worker
    determines — DOCS.md's policy surface or the schema conventions are
    scope hints, not pins. (Rider items 5 and 8; rider §§2.1–2.2.)

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
  schemas/, the five global docs under docs/, every tools/ member
  named in bin/bale's INJECTED_TOOLS, and the scripts the test suite
  executes — today scripts/build.sh and install.sh (equivalently:
  all of tools/, scripts/build.sh, install.sh). The set tracks the
  rule, not the enumeration: when INJECTED_TOOLS grows or the suite
  gains an executed script, the set grows with it, no contract edit
  needed. Copied, never re-derived. (Countermeasure for evidence
  30's class; amended 2026-08-05 from the enumerated form after the
  board-6 arc's two include-gap instances — sessions A and B.)
  (trued up 2026-08-16 to the five-doc era — PLANNER.md joined the
  global set at 0.4.11.)
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

New, ratified 2026-08-13/14 (the friction-removal sitting, master
`2026-08-13-continue-plan-005`):

- **The bare-pack restoration mechanism.** Grounded in the
  architect-typed-surface contract (ratified 2026-07-27: the bare
  cold-start `bale pack "goal"` is the one command the human
  composes from scratch), the bare default pack works again in a
  checkpoint-configured project. Mechanism, ratified 2026-08-13/14:
  walk-time checkpoint auto-exclusion with an explicit-naming
  read-side key (a checkpoint ships only when an include names it
  explicitly; a typed `--write` covering it still refuses without
  the flag); the read-only checkpoint waiver (`checkpoint: null` +
  `checkpoint_waived`, `{sid}`-bearing bases only); and
  `--checkpoint-file` commit-and-pack as the oneshot authoring
  path. Forecast-declared reconciliation, ratified with it: the
  forecast half's containment refusal applies to **declared**
  forecasts — a typed `--write` set, or handoff's reading-plan
  forecast — never to the include-set default, which the read-side
  explicit-naming rule already governs; the drift-gate residue
  this leaves on default-forecast checkpoint edits is an accepted,
  named §3 watch, not hardened.
- **The mechanism-authority principle — engraved; one home:
  `docs/CLAUDE.md` §4.** Ratified 2026-08-14 and landed verbatim,
  one physical line, in the global doc's division-of-labor
  section, framed there as the complement of the blindness
  doctrine — detail authority to the worker (it has the code),
  intent authority to the planner (it has the ask), the
  flagged-deviation-plus-ratification loop the joint. This entry
  is the ratification record and the pointer, deliberately not a
  second copy; the principle is identified by its opening clause,
  "Mechanism authority sits with the session that has the code in
  context". It is globally injected doctrine for every project,
  which is why it does not live in this project-local doc.
- **The blindness doctrine reaffirmed, with checkpoint thinness
  pinned as the lever.** After full discussion: checkpoints bound
  evaluation, not the builder — reaffirmed unchanged. Thinness is
  the pinned authoring lever: outcome-only oracles, never
  mechanism assertions. Named watch (§3): HOLDs clustering on
  planner-fixture defects rather than worker misunderstanding
  means authoring practice is the defect.

New, ratified 2026-08-16 (this sitting, master
`2026-08-16-master-sitting-002`; both rulings resolved in chat
2026-08-15 at the improvement sitting — lifted here for
re-litigation protection, the one home for their contract force;
board 10's queue entry keeps the working copies, bracket-annotated
as lifted):

- **PLANNER.md is the fifth global doc.** Same class as the four in
  every mechanical property: shipped in every request (the
  drill-down premise; §6 entry 32), self-containment-bound, cites
  the global set and is cited by it, guard-scanned, crossref-parsed,
  pair-pin-eligible, subject to all doc conventions — the global
  set becomes five. Its read-path row is parallel to DOCS.md's and
  CODE.md's, not a new kind: it triggers when authoring is the work
  (a pack, brief, oracle, rescope offer, or sitting), so a worker's
  mandatory read is zero and a mid-session authoring arrival is an
  ordinary §11.2 pre-flight event — the case that killed the same
  chat's earlier conditional-injection framing, which this final
  form supersedes. Discarded as category residue: any special
  authority clause (per-doc scoping already covers it) and any
  deny-list entry. Consequences, all ratified: the worker→planner
  transition grants command and brief authorship, never oracle
  authorship (blind-checkpoint doctrine unchanged); injection
  differentiation, if a byte-costed transport ever wants it, is
  harness-external and parks with board 10's injection-model item;
  the birth session inherits the two four→five true-ups (CLAUDE.md's
  META self-containment sentence, BALE.md's doctrine section).
- **One doc: orchestration.md merges into PLANNER.md, core-first.**
  Ratified 2026-08-15 (third chat round), discharging the
  orchestration.md-promotion item early, deliberately. Authoring
  doctrine is the core; orchestration doctrine rides past the
  banner with harness-era sections marked provisional-until-S6
  inline; the merge happens at the extraction session by relocation
  plus tombstone, and orchestration.md's six ratified judgment
  calls keep their status. Rationale, quotable: planner-vs-
  orchestrator is a topic boundary inside one injection audience,
  and the gate-by-audience principle plus the one-doctrine-one-home
  rule (ratified at tarball-riders, sentence scale) forbid
  splitting one conditional layer across two files. ADR-0009's
  ladder corrects to explainer → section of the conditional-layer
  doc (recorded by dated Notes append at the birth session); any
  physical re-split defers to board 10's injection-model decision,
  with the banner as the pre-marked seam. S6 inherits "ratify and
  churn the orchestration half of PLANNER.md" in place of the
  promotion item.

New, ratified 2026-08-16 (the master sitting, recorded at this
microdeltas landing):

- **The bad-oracle correction protocol.** When a blind checkpoint HOLDs
  and the worker's evidence points at the fixture, the flow exercised
  and ratified this sitting is the contract: (1) the worker diagnoses
  from the reveal label alone, verifies the intended invariant
  mechanically on its own side, and requests the spec —
  reveal-spec-not-script: target, scope, expected value, never the
  script. (2) The desk re-verifies mechanically against real bytes
  before ruling — never from memory. (3) The ruling forks: fixture
  defect means an amendment at the desk, HOLD→correction, no retry
  tarball from the worker; a real violation means the worker fixes and
  ships a retry tarball; and a fix that would override the request's own
  brief needs an explicit desk ruling either way. (4) Amendment
  discipline: minimal — only the failing probe changes, passing probes
  are empirically validated anchors and stay byte-identical; the
  amendment is version-suffixed, dry-run against real bytes before
  delivery, its sha256 published, and the operator compares the echo.
  (5) The operator commits the amended bytes at the per-sid checkpoint
  path and retries the same response tarball; the board-6 provenance
  gate refuses on the stamp mismatch, the operator accepts deliberately
  with the per-invocation flag, and stamp_matched false plus a prose
  mention at the next deltas landing is the truthful double record. (6)
  Every fixture defect is a ledger specimen feeding the §5 blindness
  watch and PLANNER.md's checkpoint-authoring practice. Doctrinal prose
  home: PLANNER.md at its next churn; this entry is the contract of
  record until then.

New, ratified 2026-08-16 (the 008 desk, dispositions ratified wholesale;
the rider `2026-08-16-multi-discussion-008` is the authored record —
recorded here for re-litigation protection):

- **Telemetry disposal doctrine — telemetry earns its place.** No field
  without a named consumer: a field isn't real until a consumer queries
  it, and every new field names its query at birth (the policy row lands
  via board 46; the schema descriptions already name consumers de
  facto). Field retirement: a field that stays null across N sessions
  with no consumer stops being stamped and keeps tolerating on read —
  the legacy-tolerance pattern. Completeness over breadth reaffirmed
  (evidence 38): a narrow field stamped on every exit beats a rich one
  stamped only on applies. The pile risk is attention, not disk; the fix
  is making reading the default at moments the architect is already
  sitting, not collecting less.
- **Calibration sittings are trigger-fired, never calendar-fired.**
  Session kind named: the calibration sitting — the existing sitting
  machinery (sitting-close deltas, ratification microdeltas,
  evidence-ledger curation, the trust grant as a stats-reading judgment
  point), no new ceremony; a calendar cadence is rejected as the
  over-formalization CLAUDE.md §7 warns against. Triggers: clarification
  clustering against one packer crossing threshold; DISAGREE clusters on
  one check class; HOLD clustering per work class; a pending trust
  grant; N sessions since the ledger was last read. Default threshold,
  deliberately crude and ratified as a starting point: three same-class
  events inside a rolling window; the first calibration sitting
  recalibrates its own trigger. Input side: the stats digest at
  sitting-open (board 38 is the queued machinery). Output constraint,
  the teaching half: workers are stateless, so the only teaching channel
  is the injected docs and the request — a calibration sitting's outputs
  are constrained by construction to durable artifacts: a doc delta, a
  mechanical gate, a board item, an evidence entry, or a grant (evidence
  40; PLANNER.md §6). The loop closes measurably: every record pins
  contract_docs hashes, so the next calibration sitting can check
  whether the previous one's doc delta moved the rates (board 44's epoch
  read side). Doctrinal prose home: PLANNER.md via board 46; this entry
  is the contract of record until then.
- **Nominate, never curate.** Stats may flag mechanical-stream
  nominations — "these sessions form a DISAGREE cluster, candidate
  evidence entry" — but deciding it means something and writing the
  ledger entry stays at the master desk; stats writing its own
  conclusions into the ledger would be a soft self-oracle grading the
  workflow that produced it. (Renderer-never-owns is PLANNER.md §17's;
  pointer, not a second copy.)
- **Rejected at the 008 desk, reasons of record:** the redirect-table
  tombstone replacement (a DOCS.md §6.4 amendment for modest bytes); the
  ADR-0013 split (a junk drawer by design — the keyed
  displaced-rationale appendix the relocation ADR itself created;
  section-key citations instead); the lint-side per-session
  claim-coverage check (confounded — validation_will_run deliberately
  mixes claimable and mechanical entries, run-but-unclaimed is correct
  per TARBALL.md §5.3, and check names are freeform); calendar-cadence
  calibration sessions (trigger-fired only); the two-thirds compression
  target (evidence 26). Deferred with its reason: the per-path
  forecast-refusal counter — a pack refused at the forecast gate never
  receives a sid, so the counts have no durable home today; the §3 watch
  is its record.

## 6. Orchestration-doctrine evidence pile (feeds the doctrine doc at
   harness scoping; each rule earned from live traffic)

planner-facing doctrine derived from entries 15, 45, 49, 65,
69–72, 75, 78 now lives in docs/PLANNER.md §§1–7; ledger entries
unchanged

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

New from the 2026-08-07 sitting (the board-35 sessions):

61. **Queue staleness is real under concurrency; the drill-down
    doctrine caught it at zero cost.** The row-32 near-duplication
    miss: an item queued from session 1's notes was closed by an
    intervening session (board-13b) before its carrier ran; caught
    because the worker verified the shipped tree before building
    rather than trusting the queue. Sids:
    `2026-08-07-board-35-small-pins-010`,
    `2026-08-07-board-13b-epoch-ledger-005`.

New from the board-10 wave-1 sittings (2026-08-10/11):

62. **The packer-error class gains a forecast/manifest-mismatch
    shape, twice in one wave:** a `--write` naming a nonexistent
    path; a `--write` naming a file absent from includes.
    Master-attributed; the mechanical counter is proposed in the
    §3 fold-in registry.

63. **The "probe-salvage" pattern:** an abandoned session's probe
    answers (environment trial, mount table) compounded into the
    repack brief as ratified salvage; S1's retry landed clean on
    the first environment it never saw. Repack-over-rescue
    validated for probe-heavy stalls.

64. **Brief wording is a hazard surface:** revC's salvage phrase
    "preserving each mount's existing VFS flags" was implemented
    literally and caused the HOLD (locked-flag EPERM on overmount
    topology; libmount already merges). Salvage descriptions are
    design authority — word them as contracts on outcomes, not
    mechanisms.

New from the board-10 wave 2–4 sittings (2026-08-12/13):

65. **The blind-checkpoint chapter:** first real-defect catch (S5's
    single-spot enum vs record-wide walk); three planner fixture
    defects from one root — surfaces imagined instead of read from
    the wire format; and the standing practice that ended it:
    checkpoint fixture paths are "dry-run" against the corpus with
    the graded surface stubbed before first commit, which caught
    defect three pre-ship. Split verdicts (checkpoint HOLD × worker
    PASS) attributed cleanly every time.

66. **Provenance in anger:** the oracle amended mid-session twice,
    each retry gated, accepted per-invocation, stamp divergence
    recorded — the board-6 contract exercised end to end.

67. **"packaging-list coupling":** schemas/bin-touching sessions
    repeatedly needed install.sh, scripts/build.sh, and tools/
    admissions (S2 ×3, S4 ×4); planner forecasting practice now
    includes that coupling set up front for code sessions on those
    surfaces.

New from the 2026-08-13/14 sitting (the friction-removal sitting):

68. **The first-live-exercise class: mechanical validation cannot
    see operator flow.** S7 shipped mechanically green — suite,
    checkpoint, apply all clean — and the first operator sitting on
    top of it surfaced every seam: three frictions in one day. A
    feature's mechanical greenness says nothing about its operator
    ergonomics; the first live sitting is part of the validation
    surface.

69. **Misrouted authorship.** The resolved-existence refusal's
    "author and commit" wording sent the architect — not the
    master — to hand-write an oracle, and a sibling session
    compounded the miss. Two correctives, both standing: refusals
    name their real actor (wording fixed in 0.4.10), and one
    master per sitting authors commands, briefs, and checkpoints.

70. **Checkpoint tracks scope.** A split invalidated the authored
    oracle — anchor 3 and the flag E2E fell out of the narrowed
    scope — so the checkpoint HOLDs a good session unless
    re-derived. Standing rule: re-derive the checkpoint whenever
    scope changes.

71. **Derive-don't-rewrite.** Briefs revA–revE, each derived
    mechanically from its predecessor, preserved the anchors
    section five revisions running; revF, rewritten fresh, dropped
    it and caused the anchor HOLD. The worker's corrective added a
    `grep -Fx` self-assertion on the landed line — the
    countermeasure generalizes: verbatim-marked content gets a
    byte-exact assertion wherever it lands.

72. **Per-scenario fixture isolation is mandatory for blind
    checkpoints.** The v3 oracle shared one sandbox repo across
    scenarios; an open whole-tree session left behind by one
    scenario tripped the ADR-0015 gate on the next. Blind
    checkpoints exercising future features cannot be dry-run, so
    fixture hygiene is conservative by construction: one fresh
    repo per scenario.

73. **The amendment valve confirmed at the names-its-successor
    bar.** The board-6 stamp-pin REJECT names
    `--accept-checkpoint-change`, FORCE-logs, runs the latest
    committed oracle, and records `stamp_matched: false`; the
    architect recovered from a mid-session oracle amendment purely
    from tool output — no doc lookup, no master round-trip.

74. **Supersession sweep-order defect: bale created dirt its own
    dirty-target guard then punished.** In both of this sitting's
    supersessions the sweep commit preceded the closure-record
    write, leaving the record as tree dirt that surfaced at the
    next apply's pre-flight — twice at once; transcript-ordered
    proof in the sitting log. The mechanical counter is a §3
    fold-in rider (closure record before the sweep, or inside its
    commit set, plus a tree-clean-after-supersession test).

75. **The post-HOLD reveal precedent: reveal the SPEC, never the
    oracle.** When a HOLD traces to content the worker never
    received, the retry gets the missing brief contract prose —
    never the checkpoint's mechanics. The retry must not be taught
    to the test.

New from the 2026-08-14/15 sitting (the improvement sitting):

76. **First live cross-session race; every mechanism in the chain
    held under real contention** (claude-core-first r1→r3): the
    forecast gates held (docs/CLAUDE.md diff 0 across bases), the
    blind checkpoint HOLDed correctly on the sibling's rewrite of
    the co-read file, the claims split flagged exactly the one
    unobservable claim (the r2 `[DISAGREE]` was the predicted
    row), the probe ran under explicit chat override of
    `expects_probe: no`, and the remedy was a one-line
    re-baseline. Corollary recorded: the feared open sibling had
    forecast `[]` and could not land — the priced risk was
    structurally zero; the race-safety doctrine line landed via
    `2026-08-15-tarball-riders-003`.

77. **Mechanization byte-accounting: the payoff is drift-immunity,
    not bytes.** Net doc delta ~−0.2KB against a −2..4KB estimate;
    every recipe relocated to executable homes; evidence 33
    numerically confirmed. Self-demonstrating incident: the
    single-line-grep hazard bit the very session deleting its
    warning paragraph, and the knowledge now lives only in code
    that executes it.

78. **Planner practice keeps living in ephemeral chats until a
    gate refuses** (second data point after Evidence-45): the
    checkpoint precondition was absent from the §3.4 authoring
    read-path and surfaced only via pack refusal; fixed durably by
    the §3.4 row (`--checkpoint-file` plus the
    checkpoint-configured-projects paragraph, landed at
    `2026-08-14-global-doc-selfcontainment-006`).

79. **First live §11.6 compaction recoveries, this sitting's
    master session:** disk-as-ground-truth surfaced a complete
    brief authored in a compacted stretch (adopted after
    verification rather than overwritten), and a compacted board
    read was re-pulled from the shipped MASTER.md before
    answering. Recovery doctrine held; the bail evaluation never
    ran because its triggers are introspective — the motivating
    datum for board 37.

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
- Operator-side WSL2 suite runtime, measured at the 2026-08-13
  apply paste: 60.8–63.1s across three runs (376 tests at
  measurement — a dated figure, not a standing count; container-side
  88–89s remains the sandbox-side figure). Clears the §3 watch.
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
- Repo: ~/bale-src. bin/ modules: bale, bale_pack, bale_apply,
  bale_config, bale_validate, bale_staging, bale_report,
  bale_rollback, bale_stats (the eighth sibling — a claim; landed
  at `2026-08-01-board-5-bale-stats-006` per the arc's upward
  report), _bale_toml. Load-time
  import set: pre-extraction it was bale_config, bale_validate,
  bale_staging, bale_rollback; the 8b/8c sessions refined the
  sibling lazy-import idiom, so re-verify the current set before
  scoping any include set that must execute bin/bale — evidence 13
  still governs. bin/bale VERSION 0.4.11 at
  `2026-08-16-planner-injection-wiring-006` (the five-doc
  injection wiring, the current landmark); the per-bump trail —
  every bump's sid and the doc-only / tests-only bump exemptions —
  lives in git (prior versions of this doc) and in the sessions'
  telemetry records.
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
| 1b | validation.sh runs unsandboxed with operator privileges | Doctrine: ADR-0016 (Accepted 2026-08-07). Implementation: board 10 (harness prerequisite) |
| 2 | Own-scope drift × concurrency = silent clobber; created-collision error is safe but cryptic | Board 2 |
| 3 | Claim/verdict calibration signal evaporates into transient logs | Board 4 (first-class durable field) |
| 4 | No provenance: unversioned contract docs, unattributed responses | Board 4 (day-one stamping, §5 contract) |
| 5 | handoff.md reading plan carried standing authority | Fixed in master-doc-landing (§5 contract) |
| 6 | ~25K-token injected-contract tax per session; justification prose accreted | Board 7 |
| 7 | bin/bale docstring = 41KB changelog-in-code | Board 8 |
| 8 | §10.1 self-check is worker discipline, not mechanics | Board 4 (response lint) |
| 9 | Master state existed only by convention, outside the repo | master-doc-landing; evidence 17 |
