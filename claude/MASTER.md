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

Last landed by: `2026-09-15-sitting-close-deltas-9-008`.
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
ratified 2026-08-07; the sitting-open version check is satisfied by
the request's provenance stamp — the paste-form rule retired
2026-08-18, evidence 80).

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
  no action. Second datum accrued 2026-08-25: board 52's unused
  tests/test_tree_position_echo.py forecast entry
  (`2026-08-25-board-52-pack-preamble-006`) — packer-side
  imprecision again, master-authored pack; two accruals, still no
  clustering, watch stands. Third datum accrued 2026-08-26: three
  unused forecast entries in one pack (validate.sh,
  scripts/build.sh, install.sh;
  `2026-08-26-board-53-amend-checkpoint-004`) — packer-side
  imprecision, master-authored pack; three accruals, all
  packer-side on master-authored packs, meeting the crude
  three-event calibration threshold. Desk disposition: the
  calibration question opens the next sitting rather than being
  resolved at a tired close (end-at-milestones); the watch stands
  until that sitting disposes it. Fourth accrual 2026-08-31:
  009's unused validate.sh, scripts/build.sh, install.sh trio
  (`2026-08-31-board-64-release-surface-group-009`) — packer-side
  imprecision, master-authored pack. CLOSED 2026-08-31: the
  continue-plan-012 sitting disposed the calibration question with
  the ratified ruling (also a §5 contract, this date):
  Master-authored forecasts stop pre-seeding the packaging trio; the release-surface include group carries the read side, and a needed packaging change travels ship-enumerate-admit.
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
  [2026-09-10: FIRED at the 2026-09-01/02 sitting — three desk
  fixture defects in one sitting (§6 entry 109; entry 95 had set the
  threshold at a third). The fix landed at the desk as practice, two
  counters: every probe gets a contradiction pass against the brief's
  work items before delivery, and rehearsal landings exercise
  degrade/legacy rungs, not just happy paths. The watch stands
  re-armed at the same threshold; re-trigger unchanged.]
  [2026-09-14: two HOLDs in five sessions at the continue-plan-006
  sitting — one worker-side (the apply-side's first attempt: a
  `bash -n` against scripts bale runs from outside staging; §6
  entry 130), one oracle-shaped (row 83's checkpoint pinned
  `bin/bale` source bytes for an output contract; §6 entry 128).
  One planner-fixture HOLD, no clustering; the watch stands at the
  same threshold. Three fixture defects were caught by dry-running
  before either oracle shipped (§6 entry 129).]
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
  [2026-09-10: two more deliberate accepts on record —
  `2026-09-01-board-70-doc-reachability-007` (v2→v3) and
  `2026-09-01-board-71-lifecycle-resolution-008` (v1→v2); both
  retries PASSed; the prose records are on rows 70 and 71.]
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
  wanted as new surface. (Rider item 5's deferral.) First specimen
  accrued 2026-08-31/09-01 at the 026 sitting: the 67-r1 pack refusal
  at the forecast gate, master desk the offender (§6 entry 103).
- Unconsumed pre-answered intents (ratified 2026-08-24): an intent
  answering a prompt the flow never raised proceeds with a FORCE-line
  report, never a refusal — brief-conformant, ratified with a routing
  note: bundle/argv coherence is enforced upstream, at 49a-ii's
  validate-bundle gate and 49b's emitter, where the incoherence would
  originate. Re-trigger: a genuinely unconsumed intent observed after
  49a-ii lands; revisit refuse-vs-proceed on the live specimen.
- Thin predicted-basis claims: the observed/predicted calibration
  split has almost no predicted data — predicted-basis claims number
  18 against 233 observed in the corpus. Watch whether the predicted
  side stays thin now that the basis field is named; no action
  attached. (From the 2026-08-31 meta-specific sitting.)
- The contract-doc HOLD rate per applied session (6/21) runs
  slightly above code's (12/51) — below any action threshold, worth
  an eye; no action attached. (From the 2026-08-31 meta-specific
  sitting.)
- Admission prompts for `--accept-base-drift` and
  `--allow-missing-required-check`: row 78 landed per-path y/N at
  the scope-drift and sandbox refusals only; the base-drift and
  required-check refusals gain composed remedy lines at row 81
  with no prompts, by desk ruling. Re-trigger: the composed line
  of row 81 still being copied to the desk. (Opened 2026-09-14 at
  the 2026-09-10→14 sitting's close.)
  [2026-09-14: NOT fired — row 81 landed composed lines at both
  refusals with no prompt, pinned under a pty with `y` queued
  (`overrides` stays `[]`); `2026-09-14-apply-side-81-87-010`.
  Re-trigger unchanged.]
- Exchange adoption (§6 entry 112; specimens two and three at
  entry 115): a doc remedy has landed (row 74) and a mechanical
  remedy is queued (row 85, the exchange-carried-outside-relay
  self-report). Re-trigger: a fourth `clarification.rounds: 0`
  against a real round after both have landed. (Opened 2026-09-14
  at the 2026-09-10→14 sitting's close.)
  [2026-09-14: two rounds through `bale relay` at the
  continue-plan-006 sitting (73B and 83, both pre-build; telemetry
  `clarification.rounds: 2` on each — the ask and the answer); one
  chat-first breach, self-reported and corrected into the relayed
  round (83; §6 entry 127). Re-trigger unchanged; row 85 still
  queued.]

**Ruling queue** (desk rulings awaiting a future sitting —
decisions, not work rows; a ruling becomes a doc delta only if it
says so):

- **Bailout-vs-compaction calibration** — a desk ruling at a future
  sitting: whether CLAUDE.md §11's emphasis shifts — accept §11.6
  recovery as the de facto primary defense on auto-compacting
  surfaces, or find a pre-compaction trigger that actually fires.
  Corpus facts of record: zero bailout outcomes in 181 records;
  §11.6 compaction recovery exercised on every one of the 15
  attempt-level compaction disclosures across 7 sessions, done
  properly each time; 13 tight budget_pressure self-reports.
  (Queued 2026-08-31 at the meta-specific sitting.)
  [2026-08-31: DISPOSED — ratified at the continue-plan sitting
  (session 026); the ruling's text of record is §5, this date, and
  the board-37 reshape it directs is bracketed on that row.]

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
  [2026-08-31: merged — 009's pack-json `include_group` key
  proposal rides this same carrier (the next bale_report.py /
  pack-json touch). Text verbatim from
  `2026-08-31-board-64-release-surface-group-009`'s Proposals:
  "**`include_group` key in pack's `--json` report.** The human
  report carries the durable "include group" row; the JSON report
  can't without a `format_pack_json` change in `bale_report.py` — a
  third out-of-forecast file for one additive key this session, so
  proposed instead, following the session-opener precedent already
  recorded at that call site. Scope: `bin/bale_report.py`,
  `bin/bale_pack.py` (pass-through), a `--json` case in
  `tests/test_include_group.py`."]
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
  [2026-08-31: consumed — landed as a rider at
  `2026-08-31-board-60-relay-reemit-017`: six word-level
  substitutions confined to the `--read-only` and `--supersedes`
  bullets (session B's sweep had already fixed the includes bullet;
  §7.1/§7.4 were clean).]
  [2026-09-15: closed at `2026-09-15-board-90-doc-residue-005` —
  §7.2's include bullets already carry ADR-0015's read-set language;
  nothing to fix.]
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
  [2026-08-31: extended — 010's linkage-shapes extension rides
  this same entry when it fires. Text verbatim from
  `2026-08-31-board-65-linkage-rollup-010`'s Proposals: "**What:**
  When the queued fixture fold-in fires (the next session that
  must touch `test_stats_aggregation.py`'s expectations anyway),
  extend its fixture set with linkage shapes the shared corpus
  currently lacks: a probe-kind stamp, and a `point`-keyed stamp
  beside the existing two `surfaced`-keyed ones. **Why:** The
  shared corpus today carries only clarification-kind,
  legacy-spelled stamps; folding both spellings and both kinds in
  keeps the one-corpus doctrine's coverage honest for the rollup
  this session added, at near-zero marginal cost once that file's
  expectations are being recomputed anyway. **Scope hints:**
  `tests/fixtures/stats_corpus/`,
  `tests/test_stats_aggregation.py`; rides the already-queued
  entry, no source changes."]
  [2026-08-31: did not fire at the row-44 landing — neither this
  entry nor its linkage-shapes extension: 024 took the
  separate-suite path and never perturbed the shared-corpus
  expectations (the entry's own firing condition), and this
  registry was not in its context, so a firing would have needed
  a clarification round regardless. Transport lesson, recorded on
  both riders: the next session that perturbs those expectations
  must be shipped this entry's text, extension included.]
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
  [2026-09-10: carrier named — board row 73 (handoff
  fix-or-retire) consumes this rider when it touches the surface.]
  [2026-09-14: premise corrected by 73A's analysis —
  `gather_files_for_pack` has no `verbose` kwarg today (only
  `walk_for_pack` does), so the rider is a three-line threading,
  not a one-kwarg call; the desk ruling on row 73 carries it into
  session B.]
  [2026-09-14: consumed at session B —
  `2026-09-14-board-73b-handoff-modernize-007` threaded
  `walk_for_pack(…, verbose=)` and handoff passes `args.verbose`;
  a tracked candidate the walk skips now prints its reason. The
  residue (an untracked include entry produces no line) is row 92.]
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
  [2026-08-25: consumed — the convention landed harness-level at
  `2026-08-25-pair-close-rider-008` (`BALE_TEST_SLOW`, gate + criterion
  in tests/harness.py, `validate.sh`'s `[INFO]` surface). Criterion
  recorded: cases ≥0.7s gate, fastest-per-class representative stays
  default. §5 contract, §7 fact.]
- Pack-time "forecast/include mismatch" warning — warn when a
  `--write` names an existing file absent from resolved includes.
  Rides the next session touching bin/bale_pack.py. (Source:
  evidence 62's proposed counter.)
- validate.sh's schema presence loop trued up to cover every
  shipped schema. Rides the next validate.sh touch. (Source: the
  S4 notes' proposal, `2026-08-13-board-10-escalation-schemas-002`.)
  [2026-08-24: consumed — the 49a-i session's validate.sh true-up landed
  it (`2026-08-24-board-49a-i-bundle-format-003`); the loop now covers
  every shipped schema, the new bundle-manifest included.]
- Apply-side bundle backstop (accepted 2026-08-24 from the 49a-i
  session's Proposals): apply's pre-flight rejects any changes[] path
  ending in .bale-bundle — a worker landing a bundle is the self-oracle
  shape from the landing direction. Rides the next bin/bale_apply.py
  touch; independent of 49a-ii. (Source:
  `2026-08-24-board-49a-i-bundle-format-003`'s Proposals.)
  [2026-09-10: consumed — landed at board row 71
  (`2026-09-01-board-71-lifecycle-resolution-008`) as BALE.md §11
  row 37 / step 18, reusing `is_bundle_file`.]
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
  [2026-08-18: struck — subsumed, with its §3.4 pair rider, by the
  sub-master landing at the contract-doc session; the landed form is the
  role-transition sentence, K7/K8 of its brief.]
- Wiring-session brief riders (accepted from the birth session's
  Proposals): When the injection wiring lands: sweep BALE.md's two
  remaining "four" sites in the same response (§3.1 editable-docs
  note, §7 pipeline step 3), and true up any four-key
  `contract_docs` provenance example BALE.md shows.
- Row 33 hazard-bracket retirement decision — the bracket's premise is
  stale post-v5 (the sentinel literal no longer appears in this doc).
  Rides the next row-33 touch or sweep; a one-bracket edit. (From the
  v5 session's Proposal 3, accepted 2026-08-18.)

- Probe clipboard epilogue, configurable-never-core (ratified
  2026-08-18): an opt-in config key names the environment's
  clipboard command; the worker-toolkit probe scaffold emits a
  tee-to-clipboard epilogue only when the key is set, and always
  emits begin/end sentinel banners (the dependency-free selection
  aid); the unset or misconfigured path walks the operator through
  setup in remedy text — never fails, never silently skips.
  Carriers: the config key rides the next bin/bale_config.py
  touch; the scaffold epilogue plus a TARBALL.md §4.3 sentence
  ride the next tools/craft_response.py touch.
  [2026-08-25: crafter half consumed —
  `2026-08-25-board-49b-crafter-emission-001` landed the scaffold
  epilogue and the TARBALL.md §4.3 sentence; the key is [probe]
  clipboard_command, and the config-side carrier entry below holds the
  remaining half.]
- validate_bundle_manifest docstring true-up — rides the next
  bin/bale_validate.py touch. Text verbatim from
  `2026-08-25-board-49b-crafter-emission-001`'s Proposals: "What: its
  line "the crafter's emission (49b) self-checks against it" predates
  this design; reality is desk-side input hygiene + construction, with
  the agreement pinned by `BundlePackParity` and the open-verb round
  trip, not a runtime import. Why: the file is outside this session's
  forecast, and one sentence of drift admission wasn't worth widening
  the change set; the sentence is now the only place describing a
  self-check that doesn't exist. Scope hints: `bin/bale_validate.py`,
  docstring only."
- bale_open and bale_sandbox presence rows in validate.sh — rides the
  next validate.sh touch. Text verbatim from the same Proposals: "What:
  the filesystem-layout section predates both modules, so a missing one
  passes silently — the same stale inventory the v0.4.12 schema-loop
  true-up fixed. Why: noticed while landing the drift guard in the same
  file; left out as off-goal scope this session. Scope hints:
  `validate.sh`, two rows."
  [2026-08-31: consumed —
  `2026-08-31-board-58-exchange-constants-parity-016` landed both
  rows plus board 59's bale_relay row from the same proposal
  family, in INSTALL_LAYOUT order (sandbox after staging; open and
  relay after `_bale_toml`).]
- The rider's config-side carrier — rides the next bin/bale_config.py
  touch. Text verbatim from the same Proposals: "What: the `[probe]`
  `clipboard_command` accessor plus the `bale config init` wizard walk,
  on the next `bin/bale_config.py` touch, spelling exactly as above.
  Why: the registry entry's remaining half; the crafter-side landing is
  complete without it, but discoverability lives in the wizard. Scope
  hints: `bin/bale_config.py` (walk_configurables + render_bale_toml + a
  typed accessor, per its §2.5 contract)."
- bale open FORCE-prefix doubling — the --no-sandbox line logs "FORCE:
  FORCE:", observed at the first live open (this sitting's rehearsal and
  spawn); a one-line fix. Rides the next bin/bale_open.py touch.
- Board 10 escalation-charge annotation: the probe paste-back
  transport hop — pure wire both directions, judgment in neither —
  is the first flow the harness transport replaces; the manual
  hop's residual aid is the clipboard configurable above. Rides
  the S6 spec-intake (annotate the escalation-contract item when
  that row is next touched).
- test_sanctioned_pairs fifth-pair pin bump — rides board 49's
  session (tests/ is its expected forecast; accepted from
  `2026-08-18-board-46-doc-deltas-006`'s Proposals, text
  verbatim): "**What:** Update `tests/test_sanctioned_pairs.py`
  for the fifth pair: bump the enumeration-count pin to 5 and add
  a PLANNER.md §10-side extract (e.g. "The ratified floor,
  restated here so this half stands alone for its citers"); the
  project-side twin cannot be pinned by that suite (it reads
  `docs/` only), so the pin is one-sided by construction and the
  comment should say so. **Why:** The suite's count pin and
  DOCS.md §9's enumeration are now deliberately out of step; the
  suite's own docstring says the table must not silently cover
  fewer pairs than the doc. **Scope hints:**
  `tests/test_sanctioned_pairs.py`."
  [2026-08-18: struck — re-routed at the desk from board 49 to the
  sub-master contract-doc session (tests/ in its forecast first) and
  consumed there.]
- Successor-surface parity (deliberately unscheduled) — the opener
  as a structured key in `format_pack_json` (not just the stderr
  copy block); opener emission on handoff's report; bare forms for
  retry and handoff. Three proposals from boards 51/52 cohering as
  one session; a future desk sequences it. (Accepted 2026-08-25 from
  boards 51/52's Proposals; the stderr/one-line-stdout ruling that
  scoped the JSON out of the pair is §5's session-opener contract.)
  [2026-08-26: two motivators accrued from board 53 — a bare-retry
  form would let amend-checkpoint emit a placeholder-free successor
  line, and `--json` parity for the verb is accepted need-gated (if
  it turns out to be scripted against). Both fold here; neither is
  queued as its own item.]
  [2026-09-10: the bare-retry motivator is consumed — row 71's
  stamp-fed, placeholder-free composed retry successor obsoletes
  it. The entry's other parts (the opener as a structured key in
  `format_pack_json`, opener emission on handoff's report, the bare
  handoff form) stand. Handoff's `--sid` generalization, raised at
  71, rides board row 73 rather than here.]
  [2026-09-14: the `--sid` question is disposed — deferred by
  73A's analysis (a vetting-only `--sid` adds nothing to handoff
  or `bale open` until several bailouts sit in the inbox at once);
  consumed from this entry, its record on row 73.]
- The bin/-sanction docstring line — one rationale line in
  tests/test_global_doc_selfcontainment.py's guard docstring
  recording the injected-surface bin/ sanction (§5, the 2026-08-31
  fold-in/purge review block). Rides the next session touching that
  file rather than warranting its own touch. (Ratified 2026-08-31
  at the fold-in/purge review; landed by
  `2026-08-31-sitting-close-deltas-006`.)
  [2026-09-10: consumed — landed at board row 70
  (`2026-09-01-board-70-doc-reachability-007`) in the guard's
  module docstring, self-standing.]
- BALE.md §7.5/§7.7 one-line group mention — rides any future
  BALE.md touch. Text verbatim from
  `2026-08-31-board-64-release-surface-group-009`'s Proposals:
  "**Sweep BALE.md §7.5/§7.7 for a one-line group mention.** §7.2
  carries the full contract and §11 row 35 the refusals; the walk
  (§7.5) and output (§7.7) sections could each name the group in
  one sentence for readers who enter there. Doc-only, low value,
  rides any future BALE.md touch." (Accepted 2026-08-31 at the
  continue-plan-012 sitting.)
  [2026-08-31: consumed — `2026-08-31-board-60-relay-reemit-017`
  landed the §7.5 walk-step sentence; §7.7 already carried its half
  (the include-group row, board 64) — no change there.]
- Provenance-block widening — the planner's call; rides the next
  provenance-stamp touch. Text verbatim from
  `2026-08-31-board-63-provenance-at-open-018`'s Proposals:
  "**What:** consider widening `.bale/sessions/<sid>/provenance.json`
  (or the opened attempt) to the full provenance block. **Why:**
  the manifest copy dies at close, so contract-doc hashes and the
  checkpoint stamp vanish for never-responding sessions the same
  way work_class did; low cost while the seam is open. Not done
  now — the ask was the pair, and block-width is the planner's
  call." (Accepted 2026-08-31 at the continue-plan-012 sitting.)
- Normalize-at-stamp for packer/model_identity — deferred with
  rationale at 018; rides a stamp-time session with a ratified
  canonical map, or board 44 read-time. Text verbatim from
  `2026-08-31-board-63-provenance-at-open-018`'s notes (the
  deferred rider): "normalizing ~10 packer and ~62 model_identity
  spellings without the corpus in hand and a ratified canonical map
  risks silent mis-attribution, and the verbatim stamp loses
  nothing — normalization can land later at read time or as its own
  stamp-time session with the map agreed." (Accepted 2026-08-31 at
  the continue-plan-012 sitting.)
- persist_pack_session's stale command-paragraph docstring — rides
  the next bale_pack.py touch. Text verbatim from
  `2026-08-31-bin-bale-tidy-020`'s Proposals: "**What:** One-line
  docstring touch-up in `bale_pack.py`'s `persist_pack_session`:
  the `command` paragraph still reads "cmd_handoff passing
  "handoff" is proposed but not yet wired (bin/bale is out of
  the board-63 session's scope), so handoff opens stamp "pack"
  until that one-word change lands" — stale the moment this
  response merges. **Why:** The docstring is the parameter's
  contract of record; a reader tracing a `"handoff"` stamp back to
  it would be told the stamp can't exist yet. Noticed while
  confirming the parameter's semantics for item 1; left untouched
  as out of scope ("everything except bin/bale"). **Scope hints:**
  `bin/bale_pack.py` (one docstring paragraph); only after this
  session lands." (Accepted 2026-08-31 at the continue-plan-012
  sitting's wave-3 close.)
  [2026-09-15: consumed at `2026-09-15-board-89-decline-cause-006`.]
- The last section-29 string literal in the parity assertEqual
  message — rides the next behavior-lane test_craft_response.py
  touch. Text verbatim from `2026-08-31-tools-true-up-021`'s
  Proposals: "**Retire the last section-29 string literal.**
  `test_rendering_is_byte_identical`'s `assertEqual` message still
  names `bin/bale` section 29 as the drift source. *Why:* it is
  now the only stale citation left in either file, and it is the
  one a developer reads at the exact moment the guard goes red —
  the worst moment to be pointed at a section that no longer
  exists. *Scope hints:* one string in
  `tests/test_craft_response.py`; a behavior-surface change by
  this session's constraint, so it wants a lane that admits string
  literals. Cheap to fold into whatever session next touches that
  class." (Accepted 2026-08-31 at the continue-plan-012 sitting's
  wave-3 close.)
- The two `_section_29` test-id renames — want a session that
  checks name-selecting consumers. Text verbatim from
  `2026-08-31-tools-true-up-021`'s Proposals: "**Rename the two
  `_section_29` test ids.** `test_constants_match_section_29` and
  `test_normalization_matches_section_29` name a contract by its
  former address. *Why:* their docstrings now have to explain the
  name, which is the tell that the name is doing work the code no
  longer supports; a reader grepping `section 29` after the
  extraction finds test ids and concludes the section still exists
  somewhere. *Scope hints:* `tests/test_craft_response.py` only,
  but it changes test identity — anything selecting these by name
  (CI shards, a `-k` filter, the board's own retry records) moves
  with them, so it wants a session that can check those consumers
  rather than a comment-only lane." (Accepted 2026-08-31 at the
  continue-plan-012 sitting's wave-3 close.)
- The response_lint.py index header — its own micro-session or the
  next lint touch. Text verbatim from
  `2026-08-31-tools-true-up-021`'s Proposals: "**Consider an index
  header for `tools/response_lint.py`.** *Why:* I noticed it while
  confirming the crafter's banner shape — the lint has its own
  multi-section body and no listing, so the rule this session just
  mechanized for one of the two shipped tools is unenforced on the
  other. I did not look closely enough to say how many sections it
  has or whether its banners are numbered; that is the session's
  first job. *Scope hints:* `tools/response_lint.py`; independent
  of anything here, and its `validation.sh` is a one-line change
  to this session's check 2 (add a second `--index-header` path)."
  (Accepted 2026-08-31 at the continue-plan-012 sitting's wave-3
  close.)
- Purge response-manifest.schema.json together with the lint's
  vendored copy, then extend the guard's scan — one change, now
  unblocked (022 has landed, satisfying the entry's own
  sequencing condition). Text verbatim from
  `2026-08-31-guard-deny-shapes-022`'s Proposals: "**Purge
  response-manifest.schema.json together with the lint's vendored
  copy, then extend the scan.** `tools/response_lint.py` line 235
  vendors response-manifest's dirty description verbatim, and
  lines 929/1021/1124 cite B1/B2 free-standing; the lint is
  already in the guard's docs-and-tools scan group. Why: until
  both land in one change, response-manifest can't join the schema
  scan set and the letter-digit shape can never extend toward the
  tools group — the convergence question stays artificially open.
  Scope hints: `schemas/response-manifest.schema.json` +
  `tools/response_lint.py`, descriptions/comments only, then a
  one-line INSTALL_SCHEMAS addition here; only after this session
  lands, to avoid forecast collision on the guard file." (Accepted
  2026-08-31 at the continue-plan-012 sitting's wave-3 close.)
  [2026-09-10: annotated from board row 70 — whether the
  pointer-class deny (the wrap-tolerant "design documentation"
  pattern the guard gained at 70) joins the schema group's table is
  now part of this standing convergence question; rides the next
  guard-touching sitting. Worker proposal accepted at the desk.]
- Promote validation_will_run and corrects into the telemetry
  attempt — two one-line write-side additions; unlocks the literal
  empty-claims cut and live corrects lineage. Rides the next
  bin/bale_report.py touch. Text verbatim from
  `2026-08-31-board-44-stats-read-sides-024`'s Proposals:
  "**What:** two one-line additions in `build_telemetry_attempt`
  (bin/bale_report.py): carry `manifest.validation_will_run`
  inside the attempt's `validation` object, and
  `manifest.corrects` on the attempt, both with the established
  key-presence semantics. **Why:** this session's read sides had
  to ship computable proxies for two of the row's asks
  (assumptions above) because neither field reaches the record.
  Both promotions are additive under the schema's
  `additionalProperties: true` — but they are new fields in
  spirit, and this session's brief cut new fields out of scope, so
  they are proposed rather than made. Once landed, the literal
  empty-claims cut is a two-line read change and the dossier's
  corrects lineage goes live with zero read-side changes (the
  tolerant read already resolves the field). **Scope hints:**
  bin/bale_report.py (build_telemetry_attempt),
  telemetry-record.schema.json descriptions if you want the fields
  documented; independent of everything else here." (Accepted
  2026-08-31 at the continue-plan-012 sitting's wave-3 close.)
- Wire the dossier into `bale stats --sid` — bin/bale is now free
  (the wave's bin/bale-holding siblings closed with it); the
  compute and render halves are done and unit-covered. Text
  verbatim from `2026-08-31-board-44-stats-read-sides-024`'s
  Proposals: "**What:** `bale stats --sid SID` swaps the aggregate
  report for the dossier — call `compute_session_dossier`, render
  via `format_session_dossier_report` /
  `format_session_dossier_json` under the existing `--json` stream
  discipline, fail() on an unusable telemetry dir; the not-found
  case renders the honest miss (already built and tested). Then
  promote the new suite's dossier coverage to E2E. **Why:** the
  compute and render halves are done and unit-covered; only the
  wiring is missing, and it lives in bin/bale — out of scope here
  and inside an open sibling's forecast, so it could not land in
  this response even as admitted drift. **Scope hints:** bin/bale
  (the stats subcommand's argparse and dispatch),
  tests/test_stats_drilldown.py (E2E extension); only after the
  sibling session holding bin/bale closes." [2026-09-10:
  deliberately NOT folded into board row 71 at the 2026-09-01/02
  sitting — desk decision, recorded so the entry stays queued
  rather than lost; still rides the next bin/bale stats touch.]
  (Accepted 2026-08-31
  at the continue-plan-012 sitting's wave-3 close.)
- Release-surface include group, candidate extension: pull tools/
  along with the group (specimen: 002's includes_missing —
  tests/harness.py hard-requires tools/ via INSTALL_TREES, and the
  67 pack didn't ship it). Rides row 68's bin/ touch or the next
  release-surface touch. (Accepted 2026-08-31/09-01 at the
  continue-plan sitting, session 026.)
- `normalize()` from the two doc-pin suites into `tests/harness.py`
  — rides the next session whose forecast holds `tests/harness.py`.
  Text verbatim from `2026-09-14-board-80-tests-only-pins-008`'s
  Proposals: "**What:** Move `normalize()` (the whitespace-collapse
  used by both doc-pin suites) into `tests/harness.py`. **Why:** Two
  identical copies as of this row; the harness's own doctrine is
  one home per helper. **Scope hints:** `tests/harness.py`,
  `tests/test_doc_crossrefs.py`, `tests/test_sanctioned_pairs.py`;
  trivial, any time." (Accepted 2026-09-14 at the continue-plan-006
  sitting's close.)
- `bale config hooks` row in BALE.md §5's command table, and one
  sentence in BALE.md's apply and pack sections that every admission
  y/N names its decline cause — both ride 99b (the BALE.md true-up).
  From boards 90 and 89, 2026-09-15.
- `bin/bale_apply.py`'s module docstring says the module never imports
  `bale_pack`; a lazy `import bale_pack` (~line 1144) contradicts it.
  Drop the sentence or lift the import — rides the next
  `bale_apply.py` touch. From board 101.
- `shlex.quote` on the non-TTY bare-apply refusal's
  `bale apply {path}` line, matching the decline's quoted alternative
  — rides row 102. From board 101.
- "request includes" in place of "pack includes" in the shared
  blindness diagnosis, so it reads right on a handoff — only if the
  byte-shared-diagnosis constraint is re-ratified; otherwise stands.
  From board 101.
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

Ratified at the 2026-08-16/18 cleanup-master sitting (master
`2026-08-16-cleanup-master-009`; recorded at this close):

- `2026-08-16-rider-foldin-deltas-010` ratified as shipped — all
  latitude and placement calls. Its includes_missing is
  packer-attributed: the brief claimed a VERSION file the include set
  never shipped, and the base hash rode the chat instead of the brief
  — both the evidence-21 class, at this desk. The in-brief base pin is
  the standing countermeasure until boards 40 and 41 land.
- The v5 regeneration ratified as landed via the corrected retry
  (`2026-08-18-master-v5-regeneration-001`); its latitude calls
  accepted as shipped — the R5 cutline; the row-33 bracket kept with
  its staleness flagged (the fold-in entry below is the decision's
  carrier); the row-5 inference note traveling to git with its caveat
  attached, not live residue.
- The v5 HOLD attributed as a planner-fixture defect: a connective
  phrase pinned on authored-not-preserved text — the sitting horizon's
  third checkpoint-desk miss (the pytest runner, the wrap-blind grep,
  the phrase-pinned authored text), a specimen for the §5 blindness
  watch's clustering read. Correctives queued: the provenance-split
  probe rule (board 46's grown cargo) and the pack-time dry-run echo
  (board 48).
- Protocol deviation, recorded so the ledger stays honest: the v5 HOLD
  was triaged by disclosing the checkpoint whole to the worker instead
  of the bad-oracle protocol's desk-amendment fork. Harm bounded — the
  sid closed with the retry, so the spent blindness expired with it —
  but HOLD-clustering reads must not score this HOLD against the
  worker.
- Relay specimens recorded for the S6 session-interaction
  mechanization mandate: this sitting's probe rounds, and the
  operator's current HOLD practice — the HOLD card plus the session
  log pasted to the worker, so the failed probe labels reach the one
  actor who cannot adjudicate them and triage routes to the wrong desk
  first. Board 47 is the card-side counter; the ruling-request
  artifact exchange remains the S6 item.

Landed 2026-08-18, the smoothing sitting (master
`2026-08-18-continue-plan-003`, read-only): the sitting's goal was
commandeered from continue-the-plan to friction smoothing on
explicit architect authority — the §3-override rule's second
exercise. The board-46 wave authored at the open (brief revA and
checkpoint v1 delivered, never packed) stands down intact; revB
derives per row 46's bracket. Dispositions, all at the desk:

- Ratified: board 49 (the planner bundle + `bale open`, with the
  36/40/48 absorptions, and the open line desk-emitted rather
  than operator-typed); board 39's world-state growth; rows 50,
  51, and 52; board 47's addressed relay blocks and happy-path
  desk block; the probe clipboard configurable; the §2
  version-rule sweep; evidence entries 80 and 81; board 46's two
  grown cargo entries; the paste-block-surface contract (§5, this
  date).
- Rejected, reasons of record: the notes-relay retirement (the
  relayed-notes conversations are load-bearing ratification
  output, not reporting overhead); the probe clipboard epilogue as
  core behavior (an environment dependency — accepted as
  configurable only); the outbox retention policy (rejected at the
  desk).
- The probe paste-back transport hop routed to S6's
  escalation-contract charge (fold-in annotation).

Landed 2026-08-18, the continue-plan-005 sitting (master
`2026-08-18-continue-plan-005`, read-only): the plan resumed as
packed — no goal commandeering. One landing:
`2026-08-18-board-46-doc-deltas-006` (doc-only, no bump) — the
board-46 cargo, its revB brief derived mechanically from the
never-packed smoothing revA per row 46's bracket, its checkpoint
v2 derived from v1 with two grown-cargo probes, both dry-run at
the desk against real base bytes (all eight probes FAIL at base)
before delivery. Ratified at the desk, recorded here:

- All of 006's latitude calls ratified as shipped: the hooks rule
  at PLANNER.md §2, artifact-voiced; the calibration doctrine kept
  whole in §6 (the brief's offered banner split declined by the
  worker — the better call); the bad-oracle protocol as a §5
  numbered list with one §14 routing sentence; the scopeless-goal
  exemption on §3.2 only, the §3.4 non-touch recorded in deferred;
  the hot-file sentence as §11's closing sentence; every
  genericization, including the stamp_matched concept-landing (a
  schema fact the worker declined to guess, recorded in
  includes_missing — the named-assumption path working);
  forecast_departures landed as mention-not-contract, the schema
  description staying the one home; the fifth-pair registration in
  generic form with the pairs-table desync flagged and left under
  forecast discipline; the verbatim clause on its own unbroken
  line (the unbroken-sid exception class).
- Coverage gap, recorded: item 4's within-DOCS.md placement went
  unflagged in notes — the one latitude call outside the
  flag-everything rule this session. The diff passed review at
  apply; record only.
- Proposal dispositions: the test_sanctioned_pairs pin bump
  accepted, riding board 49's session (registry entry above); the
  bare board-number self-containment sweep rejected, reason of
  record — cited-not-carried is the numeric-pointer precedent's
  ratified cost, and the conceptual dangle in other projects is
  that decision's accepted price.
- Desk miscount corrected for the ledger: the ratification relay
  said three consumed registry strikes; the true count is two (the
  forecast_departures rider and the §9 pair registration), struck
  this landing.
- The stale last-landed-by header (unedited by the 004 landing,
  whose brief's thirteen blocks omitted the header edit) is fixed
  by this landing's own header update; convention unchanged,
  record only.
- Sitting closed at the milestone; board 49 heads the next
  sitting's agenda, carrying the pairs-pin rider and the
  crafter-emission pre-named seam.

Landed 2026-08-18, the sub-master sitting (master
`2026-08-18-continue-plan-008`, read-only): opened on board 49 as
packed; the spawned session `2026-08-18-board-49a-bundle-open-009`
returned a §11.2 rescope offer, and the sitting's goal was then
commandeered from continue-the-plan to friction smoothing on
explicit architect authority — the §3-override rule's third
exercise. Dispositions, all at the desk:

- Ratified: the sub-master doctrine — a split is a role transition; full
  spawn-material authorship for a session's own children; blindness
  restated in TARBALL.md §7's builds-against form; the upward contract
  (required report sections and the arc-level dual-stream); parent
  ratification of the decomposition as the one-remove self-oracle
  control — landed at the sitting's contract-doc session
  `2026-08-18-submaster-doctrine-010`. Also ratified: row 49's three-way
  seam bracket; row 54's intake; the splits-are-cheap desk default; the
  pairs-pin rider's re-route to the contract-doc landing.
- Proposed and withdrawn at the desk, reason of record: a
  pack-time throughput-forecast gate — include mass is not
  consumed budget; the worker decides what it reads, and the
  drill-down doctrine is load-bearing, so mechanizing the fit
  estimate against shipped bytes would grade the wrong quantity.
  The write-out term it aimed at was correctly priced by the
  worker's own §11.2 judgment — the gate that already works.
- HOLD attribution, for the record and any clustering read
  (carry-forward from the continue-plan-005 desk): the
  close-deltas HOLD was a planner-fixture defect, desk-scored,
  never the worker's — the probe's expected string (a token from
  the notes' discussion) was absent by construction from the
  Block-F Proposal text the brief landed. Fourth checkpoint-desk
  miss specimen: the pytest runner, the wrap-blind grep, the
  phrase-pinned authored text, and the notes-region-sourced probe
  token. The correction ran the bad-oracle protocol end to end,
  and stamp_matched false at the accepted retry is the truthful
  double record — this mention completes it.
- The rehearsal rule (the sharpened desk rule from that
  correction) landed as doctrine at the contract-doc session,
  PLANNER.md §4.
- Registry strikes this landing: the CLAUDE.md §11.2
  checkpoint-precondition item with its §3.4 pair rider (subsumed
  by the sub-master landing), and the pairs-pin rider (re-routed;
  consumed at the contract-doc session).
- Ops record: `2026-08-18-board-49a-bundle-open-009` unlocked
  with no successor; its delivered brief revA (sha256 26c894…)
  and checkpoint v1 (sha256 56d578…) retained as derivation
  sources for the resumed arc.
- Sitting closed at the milestone; the resumed 49 arc (49a-i
  first) heads the next sitting's agenda.

Landed 2026-08-24 (the resumed-49 sitting, master
`2026-08-24-continue-plan-002`, read-only):

- 49a-i landed first-try PASS on a desk-authored blind oracle — after
  five miss specimens, the first clean one —
  `2026-08-24-board-49a-i-bundle-format-003`, all ten changes[] paths
  in-forecast. Spawn materials derived, never rewritten, from the 009
  revA brief (sha256 26c894…) and checkpoint v1 (56d578…); the
  re-derived brief published as b4037d…, the re-derived three-probe
  checkpoint as 221e83….
- Ratified, all seven of the worker's flagged decisions, one line each
  in its archived notes' Decisions block: the .bale-bundle suffix as the
  whole recognizer; no bundle admission flag, need-gated; the
  in-process-only intents API; unconsumed intents proceed loudly
  (routing note carried on the §3 watch above); LF-normalization scoped
  to the bundle's own reads; no record-wide prompt-vocabulary walk;
  delivery flags never stored in pack_argv — member presence is the
  single source.
- Fifth checkpoint-desk miss specimen, joining the four the 2026-08-18
  block catalogs: the date-pinned sid pattern — a conforming-sid probe
  regex hardcoded its authoring date and HOLDed the session's own
  correct landing when it packed six days later. Desk-scored per the
  standing attribution rule; the worker's adjudication was the
  protocol's happy path. Standing rule from it: sid patterns in oracles
  are date-agnostic from now on.
- Relay-pattern specimen, second live instance: the HOLD card and the
  probe's failure text pasted to the worker — the one actor that cannot
  adjudicate its own oracle's probe labels — before routing to the desk.
  Grist for board 47 and the S6 escalation contract.
- Release-list follow-on, planner-direct edit (the bale.toml lane):
  schemas/bundle-manifest.schema.json registered in scripts/build.sh
  RELEASE_FILES and install.sh INSTALL_LAYOUT after the tree-coverage
  guard refused the post-apply reinstall — the worker's Look-here-first
  item firing as predicted.
- Transported decisions accepted for the queued sessions, verbatim in
  the 49a-i notes' Proposals: the two 49a-ii format-consumer notes (the
  BALE.md delivery-flag injection contract; the pre_answered namespace
  channel, gated by validate_bundle_manifest before anything else is
  trusted) and the 49b constant-duplication drift guard. 49a-ii packs
  fresh against the applied tree.
- Sitting closed at the milestone; 49a-ii heads the next desk's agenda.

Landed 2026-08-24 (the 49a-ii sitting, master
`2026-08-24-continue-plan-005`, read-only):

- 49a-ii landed first-try PASS on a desk-authored blind oracle — the
  second clean one running — `2026-08-24-board-49a-ii-open-verb-006` at
  0.4.13, all five changes[] paths in-forecast. Spawn materials derived
  from the 009 sources (revA 26c894…, checkpoint v1 56d578…); the
  derived brief published as d4f524…, the re-derived five-probe
  checkpoint as 4970ef…. Re-derivation record: P3 retired (the rider
  consumed at the contract-doc landing), P2 re-suffixed to the landed
  recognizer, P4 re-derived and P5/P6 new after v1's BALE.md probe
  stopped discriminating post-§6.7 — two stale-probe catches at the
  desk's own dry-run, the rehearsal rule working.
- Ratified, the worker's flagged decisions as shipped, one line each in
  its archived notes: the row-48 decision — bundle-only, no standalone
  dry-run echo on the typed pack path (row 48's pointer resolves as
  declined; disposition recorded in BALE.md §6.7, the caller-agnostic
  seam noted); the dry-run exit-code space — 1 the expected-HOLD proof,
  0 loud-vacuous-proceed (revisit only on vacuous-warning clustering),
  all else refused as defective; the flag surface with --json deferred;
  structural read-only via a scratch copy of the working tree as the
  live base; the open- log prefix; repo-required; the
  unconfigured-project pre-check; the sealed-archive hard refusals; the
  0.4.13 bump (a new user-facing verb — owed, neither exemption
  applies).
- Proposals dispositions: the two 49b consumer facts accepted,
  transporting verbatim into 49b's brief; the open --json report
  deferred until after 49b, its sequencing reason of record; the
  unconsumed-intents watch note recorded — the loud-report path is
  implemented and tested, and the refuse-vs-proceed revisit stays
  desk-side on the live specimen.
- Packer-attributed tallies, both this desk's: the write forecast
  omitted scripts/build.sh and install.sh against evidence 67's standing
  packaging-coupling practice — the tree-coverage guard refused the
  post-apply reinstall, second consecutive firing, remedied in the
  planner-direct lane again (bin/bale_open.py registered in both release
  lists, commit cff7455); and the include set omitted upgrade.sh and the
  root README.md, so the shipped-context validate.sh read 76/5 — the
  evidence-13 class, handled worker-side with the identical-counts
  control.
- Paste-surface specimen for the pile: a pasted fix command carried one
  stray trailing quote, stalled the shell in quote-continuation, and ^C
  aborted cleanly — nothing ran, verified by porcelain before the
  re-paste. Grist for the 49b/52 paste-block surfaces.
- Ratified at the sitting open, close-004's three flagged mechanical
  decisions as shipped: Block B seated contiguously inside the watch
  list; Block E's blank handling; greedy re-wrap at 72 under
  token-stream-identity assertions.
- Sitting closed at the milestone; 49b heads the next desk's agenda,
  carrying the two consumer facts and the 49a-i constant-duplication
  drift guard.

Landed 2026-08-25 (the 49b sitting, master
`2026-08-24-continue-plan-008`, read-only): board 49b landed and applied
— `2026-08-25-board-49b-crafter-emission-001` at 0.4.14, the crafter's
emission half; every changes[] path in-forecast; the clipboard rider's
crafter half landed rather than deferred. The board-49 arc is complete:
the paste-block surface is closed at both ends, and this sitting's own
spawn traveled as the first live bundle — desk-assembled mechanically
(computed hashes, deterministic tar, schema-validated, rehearsed end to
end through a real bale open before delivery), consumed on the
operator's machine with the expected-HOLD proof clean.

- Ratified, the worker's flagged decisions as shipped, one line each in
  its archived notes: the --bundle flag surface with the =-glued
  --pack-arg spelling; checkpoint absence as a loud oracle-less log, no
  acknowledgment flag — the offered symmetric acknowledgment declined,
  reason of record: pack's checkpoint requirement is config-driven and
  read-only shapes legitimately carry none; fixed internal member names;
  stem hygiene as slug hygiene; LF-normalization at write; deterministic
  emission with the differing-bytes --force posture; self-validation by
  construction with the parity and round-trip pins, the stored
  --no-readme refusal kept (member presence is the single source); the
  [probe] clipboard_command spelling with the minimal single-key scan
  and its remedy-text path; the _OpenVerbBase refactor; the 0.4.14 bump.
- Proposals dispositions: all three accepted onto the §3 fold-in
  registry, texts verbatim there — the validate_bundle_manifest
  docstring true-up, the bale_open/bale_sandbox presence rows, and the
  rider's config-side carrier with the exact key spelling.
- Sitting-open record: close-007's four latitude calls ratified as
  shipped, its Block E seam resolved as shipped. One paste-back probe
  round established the derivation sources byte-identical to the
  published hashes (revA 26c894…, checkpoint v1 56d578…), HEAD 61dbf52
  clean at 0.4.13, one open session (this read-only master). Spawn
  materials derived, never rewritten, from the 009 sources; the derived
  brief published as 23f434c9…, the three-probe checkpoint as 9dabb869…,
  both dry-run at the desk in both directions — all-FAIL at base,
  all-PASS at a simulated landing — before delivery.
- Desk judgment calls, recorded: the spawn bundle hand-assembled this
  once, computed never typed, the last before the emitter; the drift
  guard's validate.sh home stated in the brief as constraint per the
  accepted proposal text; bin/VERSION and docs/TARBALL.md carried in the
  forecast, both consumed.
- Specimen, cosmetic: the first live bale open printed a doubled FORCE:
  FORCE: prefix on the --no-sandbox line (registry entry below).
- Sitting closed at the milestone; next desk's agenda: the bale open
  --json report, its only-after-49b deferral discharged, then boards 50
  and 53; the apply-side bundle backstop still rides the next
  bin/bale_apply.py touch.

Landed 2026-08-25 (the continue-plan-003 sitting, master
`2026-08-25-continue-plan-003`, read-only): four board sessions
recorded DONE, all first-try PASS on desk-authored blind oracles; a
concurrent pair with a desk-side bump rider, the first post-epoch
concurrency to run scope-disjoint end to end.

- Board 50 landed first-try PASS — `2026-08-25-board-50-crlf-tolerance-004`
  at 0.4.15. One real code change: `--checkpoint-file` ingest
  normalizes CRLF→LF before the empty-check, commit, echo, and stamp.
  Tolerance pins for the already-tolerant surfaces (briefs via
  text-mode reads, config via the TOML spec, baleignore via
  splitlines); read-site survey with per-site dispositions; docs
  trued. Ratified latitude: the working-tree CRLF-twin refusal; the
  legacy CRLF-oracle refusal (committed-is-ratified); installed-doc
  provenance hashes left byte-exact deliberately. Sitting finding,
  recorded with the tally: the desk's pre-pack rehearsal falsified
  half the row's premise — briefs and config were already tolerant —
  and the session was scoped to the truth, not the row.
- Board 52 landed first-try PASS — `2026-08-25-board-52-pack-preamble-006`,
  bumpless per the hot-file ruling (the pair's bump rode the rider).
  `session_opener_block` in `bale_pack.py`; the report ends with the
  sid+goal copy block framed by scissor lines on all three pack
  shapes; `--json` keeps the one-line stdout and the opener rides
  stderr. Ratified: the stderr decision (refusing to smuggle a JSON
  key past the `bale_report.py` hot-file ruling), both BALE.md
  re-points, and wording ownership (the scissor lines are test
  literals).
- Board 51 landed first-try PASS — `2026-08-25-board-51-bare-apply-007`,
  bumpless per the hot-file ruling. Resolution: newest by
  `st_mtime_ns`, no secondary tie-break (an exact tie refuses,
  naming every tied path); content-based candidacy (a
  `response-NNN/manifest.json` member with a non-empty `responds_to`
  — request tarballs are structurally never candidates); identity
  echo (path, sid, sha256, mtime) before a decline-default y/N;
  interactive decline exits 1; `--no-interact` contradicts the bare
  form up front; inspection flags refuse, `--dry-run` composes. All
  ratified, including the flagged ambiguity interpretation — the
  board-row bracket carries it verbatim.
- Board 51/52 pair close (the rider) landed first-try PASS —
  `2026-08-25-pair-close-rider-008`: the shared bump to 0.4.16, board
  51's BALE.md apply paragraph, board 52's §7.7 version tag, the
  `docs/CLAUDE.md` bale-emitted-opener pointer, and the harness-level
  `BALE_TEST_SLOW` convention. Ratified: the gate criterion, the
  `[INFO]` marker class in `validate.sh` (status lines that are not
  checks move no counters), release hygiene, and the predicted-basis
  claim (reconciliation agreed at apply). Board-51 conditional
  resolved moot and folded here rather than the registry: the pair
  landed as 0.4.16, so the shipped description string was already
  correct — there was never a fold-in entry to strike.
- Registry dispositions (texts verbatim in the §3 fold-in registry):
  the `--slow` convention consumed (landed at the rider with the
  criterion recorded); successor-surface parity added as a
  deliberately-unscheduled rider (the opener as a `format_pack_json`
  key, opener emission on handoff, bare retry/handoff forms).
- Desk miss, owned and remedied same day: the `--slow` registry entry
  was not transported in board 50's brief (workers never see
  MASTER.md), so the worker coined a local `--slow` spelling — the
  right call with what it had — and the rider landed the one home. A
  desk-side transport tally, not a worker miss.
- The close's own bundle-stem collision, caught and closed clean:
  this close's first pack collided with the prior desk's close bundle
  on the shared stem `2026-08-25-sitting-close-deltas`; the stale twin
  resolved first and re-packed an already-landed brief as session
  `-009`. The worker's landed-state verification caught it, refused to
  fabricate or duplicate, and closed via unlock — the discipline
  holding where the mechanical gate did not. Specimen at §6 entry 85;
  guard seeded as board 55; NNN not recycled, so this landing is
  `-010`.
- Sitting closed at the milestone. Next desk's agenda, unchanged
  guidance: smalls first (38, 39, 41, 47, 53, 37 remain — board 53
  the next-up candidate), the compression sitting (42→43) before
  harness scoping, board 45 before any harness autonomy, S6 last;
  board 55 joins the smalls.

Landed 2026-08-26 (the board-53 sitting, master
`2026-08-26-continue-plan-003`, read-only): board 53 landed and
applied — `2026-08-26-board-53-amend-checkpoint-004` at 0.4.17,
the checkpoint-amendment verb. One pre-build clarification round on
outcome contract 4, resolved at the desk before any code: the
ruling is (b)-as-adjusted — the accounting rung against the
pack-time stamp, with the matching-neither refusal naming a
per-invocation accept flag as its successor — now §5's contract,
this date. Spawn traveled as a desk-emitted bundle (crafter
emission, member hashes verified, checkpoint dry-run both
directions at the desk before delivery).

- Ratified, the worker's flagged decisions as shipped, one line
  each in its archived notes: the `--accept-unaccounted-oracle`
  spelling — deliberately not reusing `--accept-checkpoint-change`,
  one spelling with two per-verb semantics being a trap; the verb's
  home as bin/bale section 28 between sections 20 and 21, a fresh
  number per the stable-numbering rule, with the new-module riders
  correctly unfired as the consequence; both-halves stamp
  accounting (path AND sha256, a different-path stamp landing
  unaccounted — the conservative side of the ruling); the
  three-state working-tree rung (local edits never clobbered;
  hand-copy-in-place proceeds); idempotence short-circuiting before
  the stamp read; the pre-composed retry successor with its
  placeholder (pre-ratified at the ruling); `normalize_crlf`
  imported from bale_pack so both ingest edges share board 50's one
  implementation, with the two sibling docstring-only edits
  flagged; the 64-hex `--sha256` shape gate refusing before config
  or registry reads; the resolution rule — `[]`-forecast sessions
  structurally invisible, missing/malformed scope records
  conservatively whole-tree and still candidates, two-plus refusing
  naming all, `--sid` vetted; no `--json` in v1; and the
  index-header true-up of bin/bale's sections 19–26 listing —
  in-forecast, docstring-only, flagged, the CODE.md-consistency
  call over leaving knowingly-off neighbors.
- Proposals dispositions: both accepted as annotations on the
  successor-surface parity registry entry (its 2026-08-26
  bracket); neither is queued as its own board item.
- Packer-attributed tally, this desk's: three unused write-forecast
  entries (validate.sh, scripts/build.sh, install.sh — the
  packaging-coupling set, forecast per evidence 67 and unconsumed
  because the worker's ratified module-home call landed the verb in
  bin/bale). Third accrual on the forecast-precision watch (the §3
  watch); all three accruals are packer-side imprecision on
  master-authored packs, which meets the ratified crude calibration
  threshold — nominated at the desk, disposition recorded on the
  watch entry.
- Compaction disclosure, recorded: the worker's context compacted
  mid-session (post-implementation, pre-assembly); recovery per
  CLAUDE.md §11.6 with every hash recomputed from on-disk bytes at
  pack time and the disclosure in notes — §6 entry 86.
- Sitting closed at the milestone; the calibration question (the
  forecast-precision trigger) heads the next sitting's agenda,
  ahead of the remaining smalls (38, 39, 41, 47, 55, 56, 57, 37).

Landed 2026-08-29→31 (the exchange-arc sitting, master
`2026-08-29-formalize-convo-001`, read-only, registered with an
empty write forecast as declared at open): all four arc sessions
applied PASS; the sitting-close deltas the arc deliberately left to
the close landed by `2026-08-31-sitting-close-002` against live
bytes. The arc, one row each:

| session | landed | outcome |
|---|---|---|
| 2026-08-29-exchange-doctrine-002 | ADR-0017; the human/agent forks retired across TARBALL.md, PLANNER.md, CLAUDE.md, BALE.md; exchange vocabulary pinned | PASS |
| 2026-08-29-exchange-relay-003 | exchange-record schema, `validate_exchange_record`, `bale relay` (bin/bale §29), thread-aware status and telemetry; 0.4.18 | PASS |
| 2026-08-30-exchange-packaging-001 | release-list coverage for the schema + pins | PASS (correction session; cause at §6 entry 90, specimen b) |
| 2026-08-31-exchange-crafter-001 | `--emit-block`/`--round`, byte- and verdict-parity suites, TARBALL.md §5.9.2 worker flow; 0.4.19 | PASS on retry after desk checkpoint amendment (bad oracle, §6 entry 88) |

- Live-traffic evidence gathered by the arc itself: one full manual
  thread ran during authoring (worker inquiry → desk answer →
  build), one desk→tree probe ran the reverse direction, and both
  used chat/paste because the mechanism landed one session later —
  the last hand-carried instances of the pattern the arc mechanizes.
- Board deltas of the close: rows 58 (exchange constants,
  install-side parity), 59 (the bin/bale §29 extraction), and 60
  (the `bale relay` re-emit path) opened in §4; the
  routing-reversal narrative lands on board 10's row (its
  2026-08-31 brackets); ledger entries 88–91 land in §6.
- Proposals dispositions (the crafter session's three): the first
  (exchange constants, install-side parity) accepted as board row
  58, scope as written there; the second (crafter index header)
  accepted, its fold-in rule recorded on row 59 — fold in if the
  extraction session's forecast gains `tools/` for any reason, else
  its own micro-session; the third (§5.9.2 two-audiences) recorded
  as trajectory, no action — the next §5.9.2 addition triggers the
  DOCS.md §6 seam question by rule.
- Routing reversal, architect ruling at this sitting: the
  2026-08-25 routing of the clarification-relay subsumption and the
  session-interaction mechanization mandate to the harness project
  is reversed for the worker↔planner leg (ADR-0017 records it; full
  narrative on board 10's 2026-08-31 bracket); the escalation
  record's master→architect leg stays routed to the harness seed.
  Cross-project: the architect carries the D13/D14 annotation to
  `harness-seed.md`, which lives outside this repo and outside any
  bale session here.
- PLANNER.md §4 gains the desk-discipline checklist line (the one
  rule covering §6 entry 90's three specimens); ADR-0017's Notes
  gains the dated implementation-record entry. Both landed by the
  close session.
- Sitting closed at the milestone; sequencing of the new rows among
  the smalls is the next desk's call.

Landed 2026-08-31, wave 2 of the continue-plan-012 sitting (rows
58, 59, 60, 63, and 66 closed on their board brackets — facts of
record, versions, and retry stories live there; this block carries
only what has no row home; close recorded by
`2026-08-31-sitting-close-deltas-2-019`):

- Proposals dispositions, routed to the sitting's wave-3 sessions —
  open siblings at this close, so their landings are the next
  close's facts, not this one's: 016's crafter
  re-declaration-citation true-up → tools-true-up
  (tools/craft_response.py, tests/test_craft_response.py; the
  row-59 index-header rider rides the same session); 017's
  TARBALL.md re-emit mention (§5.9.2 and §5.9.4, one sentence
  each) → tarball-reemit-mention; 017's `bale status` lost-paste
  hint and 018's cmd_handoff `command="handoff"` → bin-bale-tidy;
  018's stats read side (`"opened"` into IN_FLIGHT_OUTCOMES;
  provenance-stamp resolution in session_work_class) → folded into
  board 44 as its first customer (annotated on that row); 015's
  deny-shapes guard extension → guard-deny-shapes
  (tests/test_global_doc_selfcontainment.py).
- Registry deltas of the close: three entries marked consumed in
  place (the BALE.md §7/§7.2 includes-as-scope true-up and the
  §7.5/§7.7 group mention, both landed at 60; the
  bale_open/bale_sandbox presence rows, landed at 58 with board
  59's bale_relay row); two entries added with What/Why verbatim
  from 018's notes (the provenance-block widening proposal, the
  deferred normalize-at-stamp rider).

Landed 2026-08-31, wave 3 of the continue-plan-012 sitting — the
routed destinations of the wave-2 dispositions block above, every
one landed; board 44's landing is its row's bracket, facts of
record there; this block carries only what has no row home; close
recorded by `2026-08-31-sitting-close-deltas-3-025`:

- bin-bale-tidy — `2026-08-31-bin-bale-tidy-020`, applied
  2026-08-31: both one-liners landed (017's `bale status`
  lost-paste hint, 018's cmd_handoff `command="handoff"`). The
  hint's awaiting-worker-branch-only placement ratified as shipped
  (the one state whose hint tells the operator to carry a paste
  block they may no longer have); the negative-run assertion
  discipline — both validation assertions also run against the
  unmodified file to confirm they bite — noted approvingly at the
  desk.
- tools-true-up — `2026-08-31-tools-true-up-021`, applied
  2026-08-31: seven stale section-29 citations retargeted in the
  crafter, not the brief's four — the desk's count was a
  head-truncated grep, corrected in the chat round recorded in its
  notes; the nine-section index header landed; the
  provenance-not-mechanism retarget ruling holds (the vocabulary
  originates in bin/bale_relay.py and reaches the parity suite
  through bin/bale's re-export; the loader stays untouched); test
  ids frozen (the two `_section_29` methods keep their identities,
  their docstrings carrying the moved contract).
  The tools-true-up oracle was amended rev1 to rev2 at the desk; the retry's stamp mismatch was accepted deliberately, and this sentence is its prose record.
  The blind checkpoint had HOLDed on a fixture defect — the index
  probe asserted an imagined surface (wrong anchor word, wrong
  position window) — corrected per the bad-oracle flow, and the
  same response tarball landed on retry.
- guard-deny-shapes — `2026-08-31-guard-deny-shapes-022`, applied
  2026-08-31: landed through a full clarification thread — a
  paste-back probe, a three-question exchange round (the planner's
  record preserved at `.bale/clarifications` under the sid), and a
  desk scope amendment authorizing the telemetry-schema
  description purge, which shipped as admitted drift. Two of the
  worker's three defaults were corrected by the round (the five's
  membership; the seven's reconstruction). The row-tolerant board
  anchor and the hyphenated reword ratified as shipped. The
  ratified deny set's durable home is now the guard itself (the
  015 archive holds only notes.md).
- tarball-reemit-mention —
  `2026-08-31-tarball-reemit-mention-023`, applied 2026-08-31:
  both sentences landed correct, one per section, no notes.md —
  the desk-probe record is the source, and the §5 wave-3 close
  block carries the rescued record. Its predicted guard-suite
  claim resolved to verdict skip at staging — flagged; self-heals
  at the next full-suite run.

Landed 2026-08-31→09-01, the continue-plan sitting (session 026,
read-only, empty forecast; the sitting straddled midnight, so 09-01
sids over the 08-31 sitting are expected provenance). Rows 41, 67,
and 42 closed on their board brackets — facts of record, versions,
ratifications, and retry stories live there; this block carries only
what has no row home; close recorded by
`2026-09-01-sitting-close-deltas-4-004`:

- Wave record: the sitting spawned 027 (row 41), 002 (row 67, after
  one desk re-emit and one refused r1 open — the refusal's specimen
  is §6 entry 103, the sequencing cost §6 entry 102), and 003
  (row 42, one admitted guard-forced path).
- Sitting-open record: the 025-close ratifications — all four of
  close-025's judgment calls ratified as shipped at this sitting.
- Sequencing rider: boards 56+57 deliberately deferred to a fresh
  desk; boards 39, 43, and 47 held as previously ratified; board 37
  now packable under the §5 ruling (this date).
- Dispositions with their own homes, pointed to rather than
  restated: the bailout-vs-compaction calibration ruling (§5,
  disposing the §3 ruling-queue item above); the retry-telemetry
  corpus tolerance note (§7); evidence entries 99–106 (§6); rows
  68–69 opened in §4; the release-surface include-group extension
  in the registry above.

Landed 2026-09-01→09-02, the continue-plan-005 sitting (master
`2026-09-01-continue-plan-005`; opened read-only to continue the
plan, then commandeered twice on explicit architect authority — the
§3-override rule's fourth exercise: first to the shipped-doc
reachability gap, then to the operator's HOLD-friction outline).
Rows 70 and 71 closed on their board brackets — facts of record, the
version, ratifications, and retry stories live there; this block
carries only what has no row home; close recorded by
`2026-09-10-sitting-close-deltas-5-001`, landed 2026-09-10 or later
— eight-plus days after the sitting, so the row brackets carry the
sitting's dates and the bracket stamps carry the close's:

- Wave record: the sitting spawned 007 (row 70, opened and landed
  in-sitting) and 008 (row 71, opened and landed in-sitting). The
  planned wave (68, 56+57, 69, 37) deliberately did not run and
  remains queued. Row 75 was spawned beside this close, after the
  sitting, and is in flight (facts on its row).
- Sitting-open record: close-004's eight flagged calls ratified
  wholesale by the architect at this sitting's open.
- Ratification debt carried forward, per convention: THIS close's
  notes.md and row 75's notes.md are NOT ratified by the retiring
  desk — both queue to the next sitting's open.
- Board deltas of the close: rows 70–71 DONE, 72 born resolved,
  73–77 opened in §4; boards 47 and 68 grown on their rows; the
  registry strikes above (the bin/-sanction line consumed at 70;
  the apply-side bundle backstop consumed at 71; the
  successor-surface parity entry's bare-retry motivator consumed;
  the stats-dossier wiring rider deliberately held back from 71);
  evidence entries 107–112 in §6; the version landmark 0.4.25 and
  the standing desk emission rules in §7; the checkpoint-thinness
  watch above marked FIRED; the amendment-accept watch above grown
  by two stamps.
- Sequencing for the next desk (replaces the pre-commandeering
  plan): row 75 (if not already landed) → row 73 (reproduce-first)
  → board 47 (row 74 riding its doc touch) → the held wave: 68,
  then 56+57 beside it, then 69, then 37 (69 and 37 serialize on
  the crafter) → board 43 with its compare-with-architect step →
  45 before any harness autonomy → S6 last. Boards 9, 10 (S6
  residual), 11, 35's residuals, 38, 39, 54, 55 stand as
  previously recorded.

Landed 2026-09-10→14, the continue-plan-001 sitting (master
`2026-09-11-continue-plan-001`, read-only; opened 2026-09-10 on
the goal "let's continue the plan in claude/MASTER.md"; the sitting
ran across four calendar days, so 09-11 and 09-14 sids over a
09-10 open are expected provenance). Rows 73 (session A), 74, 75,
76, 78, and 79 closed on their board brackets — facts of record,
versions, ratifications, and attempt stories live there; this
block carries only what has no row home; close recorded by
`2026-09-14-sitting-close-deltas-6-005`:

- Wave record: the sitting spawned 73A, 74–76 (one session), 79,
  78, and the s34 rider — five sessions, all landed, up to three
  open beside the desk at once (78, the doc lane, 79 —
  forecast-disjoint by construction; the read-staleness watch was
  probed, not fired: the desk ran the three doc-pin suites on the
  applied tree mid-sitting, green). Zero HOLDs across five
  sessions — a datum for the checkpoint-thinness watch above
  (thin, preserved-token oracles held).
- Sitting-open record: close-5's notes.md ratified in full at this
  open (the VERBATIM-parenthetical question resolved KEEP; the
  version-header override correctly recorded as the retiring
  brief's defect). Row 75's notes.md ratified in full,
  approvingly: the un-asked `bin/bale_staging.py` string drift,
  the `unset_effective` kwarg with its pin, the one-direction
  flag, the pipeline-start resolution point, the fixture
  extraction, the retry's observed→predicted correction, the
  `includes_missing` self-report. The sitting-open version check
  was satisfied by the request's provenance stamp, 0.4.26.
- Ratification debt carried forward, per convention: THIS close's
  notes.md queues to the next sitting's open. Every other notes.md
  of the sitting was ratified in-sitting.
- Board deltas of the close: row 75 DONE; row 73 session A DONE
  with session B queued; rows 74 and 76 DONE; rows 78 and 79
  opened and DONE in-sitting; rows 80–88 opened in §4; row 47's
  carrier clause struck; the registry strikes above (the `--sid`
  question consumed at 73; the `gather_files_for_pack` rider's
  premise corrected); evidence entries 113–122 in §6; six
  contracts dated 2026-09-14 in §5; the version landmark 0.4.27,
  the four include-authoring rules, the extended desk emission
  rule, the bundled-spawn working-style clause, and the hook
  acceptance store in §7; two watches opened above.
- Sequencing for the next desk: row 73 session B (from A's
  archived notes; order 5, 1, 4, 2, 6) → row 80 (tests-only,
  beside B if forecasts allow — B holds the four handoff suites,
  80 holds the doc-pin suites and the harness; check
  `tests/harness.py` isn't both) → 81 and 88 beside → 87 → then
  the held wave as previously recorded: 68, 56+57, 69, 37 → 43 →
  45 → S6.
- Watches opened at this close, both above: prompts for
  `--accept-base-drift` and `--allow-missing-required-check`; the
  exchange-adoption watch, now with a mechanical remedy queued
  (85) and a doc remedy landed (74).

Landed 2026-09-14, the continue-plan-006 sitting (master
`2026-09-14-continue-plan-006`, read-only; opened 2026-09-14 on
"refer to the attached readme" — continue the plan; the previous
master `2026-09-11-continue-plan-001` closed `closed-read-only` at
this session's pack, per the retiring brief — its record did not
ship). Rows 73 (session B), 80, 81, 83, 87, and 88 closed on their
board brackets — facts of record, versions, ratifications, and
attempt stories live there; this block carries only what has no
row home; close recorded by
`2026-09-14-sitting-close-deltas-7-012`:

- Wave record: the sitting spawned, in landing order, row 80
  (`2026-09-14-board-80-tests-only-pins-008`, tests-only, bumpless
  at 0.4.27), 73B (`2026-09-14-board-73b-handoff-modernize-007`,
  0.4.28), the doc lane (`2026-09-14-doc-lane-87-88-009`, rows 88
  and 87's naming half, bumpless at 0.4.28), the apply-side
  session (`2026-09-14-apply-side-81-87-010`, rows 81 and 87's
  resolver half, 0.4.29), and 83
  (`2026-09-14-board-83-hook-store-and-decline-cause-011`,
  bumpless under 0.4.29) — five sessions, five landings, up to two
  open beside the desk at a time (telemetry: 80 and 73B opened
  within five seconds of each other; the doc lane beside 73B; the
  apply-side and 83 together). Two second attempts: the
  apply-side's first attempt HELD on its own `validation.sh` (a
  `bash -n` against `apply.sh`/`validation.sh`, which bale runs
  from outside staging; the blind checkpoint PASSed both attempts;
  the change set byte-identical), and 83's first attempt HELD on
  the blind checkpoint (three of seven assertions grepped
  `bin/bale` for the rendered decline lines the first shape
  assembled at runtime; worker validation PASSed). Two relayed
  exchange rounds (73B's and 83's, each round 1 → 2 through `bale
  relay`, both pre-build; telemetry `clarification.rounds: 2` on
  each); 83's preceded by a chat-first breach the worker
  self-reports (§6 entry 127).
- Sitting-open record: close-6's notes.md ratified wholesale at
  this open, with one strike — its VERBATIM handling kept the
  retiring brief's backslash-escaped quotes on rows 87 and 88;
  those are a close brief's rendering artifact, not keystrokes,
  struck at this close (board deltas below). Every other notes.md
  of the sitting (80, 73B, the doc lane, the apply-side, 83)
  ratified in-sitting, the calls named on their rows. The
  sitting-open version check was satisfied by the request's
  provenance stamp, 0.4.27 (the master's own record carries no
  version; recorded as the retiring brief states it).
- Two desk findings with no row home. **The hook decline event:**
  at close-6's apply the operator's Enter declined a `[Y/n]` hook
  prompt; the prompt waited; the installed `confirm_yn` was
  verified to be the source (`grep -c 'return not default_no'
  "$(command -v bale)"` → 1). The event stays unexplained; row
  83's cause line is the remedy that makes the next one explain
  itself. **Bare apply at the desk:** the master's own read-only
  session counts as open, so board 51's multi-open refusal fired
  at every sitting — the bare form had never worked during a
  sitting until row 87's resolver half (§6 entry 123; §7).
- Ratification debt carried forward, per convention: THIS close's
  notes.md queues to the next sitting's open — including the two
  backslash strikes in the registry's `persist_pack_session`
  entry, flagged there.
- Board deltas of the close: row 73 DONE (session B); rows 80, 81,
  83, 87 (both halves), and 88 DONE; row 87's desk note corrected
  in its bracket (the "naming variance" clause struck — the
  resolver is content-based and naming never defeated it; the
  multi-open refusal was the whole defect); row 84 grown a third
  specimen; row 51's bracket grown (the multi-open clause
  superseded by the operator's ruling; its 2026-09-14 pointer
  corrected); rows 89–93 opened in §4; the backslash-escaped
  quotes struck on rows 87 and 88 (five) and in the registry above
  (two — the same artifact class); evidence entries 123–131 in
  §6; six contracts dated 2026-09-14 (this sitting) in §5; the
  version landmark 0.4.29, the operable hook store, bare apply
  beside an open master, the row-81 extension of the desk emission
  rule, and the install-tracks-the-checkout fact in §7; the three
  watches above stamped (two-prompts NOT fired; exchange-adoption
  two rounds and one breach; checkpoint-thinness two HOLDs).
- Registry deltas of the close: one entry opened — `normalize()`
  from the two doc-pin suites into `tests/harness.py` (row 80's
  proposal), riding the next session whose forecast holds
  `tests/harness.py`; the `gather_files_for_pack` verbose rider
  marked consumed at 73B. Proposals consumed this sitting, none of
  which had a registry entry (they rode rows 78 and 80): board
  78's three (81, 83, and the harness move — all landed); s34's
  pair proposal and 74–76's parity pin (landed at 80); 73A's
  proposal 1 (the `caller` kwarg, landed at 73B) and proposal 3
  (ship `test_per_sid_checkpoint.py` beside
  `test_checkpoint_file_flag.py` — desk practice, exercised at
  73B); 73A's proposal 2 is row 86, unchanged. 73B's three
  proposals became rows 92, 93, and 91; the apply-side's and 83's
  became rows 89 and 90; the doc lane's rides row 90.
- Sequencing for the next desk: rows 89 and 90 beside each other
  (89 holds `bin/bale_apply.py`, `bin/bale_pack.py`,
  `bin/bale_report.py`, `bin/bale_config.py`; 90 holds `BALE.md`,
  `docs/TARBALL.md`, and one string in `bin/bale`) → 91 → the held
  wave as previously recorded: 68, then 56+57 beside it, then 69,
  then 37 (69 and 37 serialize on the crafter) → 43 → 45 → S6.
  Rows 92 and 93 stand until pack's `--verbose` or the ledger
  brings them forward.

Landed 2026-09-15, the continue-plan-001 sitting (master
`2026-09-15-continue-plan-001`, read-only; opened 2026-09-15 UTC —
2026-09-14 on the architect's chat — on "continue the plan, and fix
the date confusion a Sonnet worker kept hitting"; the previous master
`2026-09-14-continue-plan-006` closed at close-7 per the retiring
brief). Row 94 opened, spawned, and applied in one sitting; its
bracket carries the facts of record; this block carries only what has
no row home; close recorded by
`2026-09-15-sitting-close-deltas-8-003`:

- Wave record: one session,
  `2026-09-15-board-94-clock-discipline-002`, 0.4.30, one
  clarification round (round 1 three questions, pre-build; round 2 the
  desk's answers through `bale relay`; telemetry
  `clarification.rounds: 2`), blind checkpoint seven of seven on the
  applied tree, applied 2026-09-15. No second attempt. The desk
  rehearsed the oracle both ways before emission (HOLD on the
  unmodified tree, six of seven; PASS on a scratch tree with the
  outcomes stubbed from the brief's own bytes) and struck one
  imagined-surface probe at rehearsal (§6 entry 132).
- Sitting-open record: close-7's notes.md ratified wholesale at this
  close (the open deferred it to land the clock row first — the
  deferral is recorded, not repeated); its two backslash strikes in
  the registry's `persist_pack_session` entry ratified as landed. The
  sitting-open version check was satisfied by the request's provenance
  stamp, 0.4.29. Board 94's notes.md ratified in-sitting, the calls
  named on its row.
- The clock finding, for the record: three clocks — `date.today()` for
  session ids and their counters, UTC for every ISO stamp, the
  architect's Eastern wall clock on the chat — and no anchor (no pack
  timestamp in the manifest, "per-day" in TARBALL.md §1 without a day,
  no rule for which date a worker writes). The specimen was this
  sitting's own request: sid `2026-09-15-…-001`, packed 00:20Z, chat
  date 09-14. The pack machine (WSL) runs on UTC — `date` and
  `date -u` agree, verified by the architect 2026-09-15 — so the
  machine's local date is the UTC date and the skew is
  chat-versus-bale, four hours a night. Ruled UTC, one clock
  everywhere (§5). This block's own dates are UTC under the ruling.
- The structured-output discussion, held at this sitting and ruled
  (§5): every worker turn in tarball mode ends in one
  machine-recognizable shape — a response tarball, a probe block, a
  light question block, or a formal clarification; prose that asks is
  not a shape. The light tier exists because a sufficiently short
  question set is faster to read and answer in chat than to relay, and
  its audit trail is the eventual response, not the thread. Lands at
  row 96, after row 91.
- Ratification debt carried forward, per convention: THIS close's
  notes.md queues to the next sitting's open.
- Board deltas of the close: row 94 opened and DONE; rows 95–98 opened
  in §4; row 91 grown (board 94 re-found the gap and names the
  crafter's embedded copy); row 84 grown a fourth specimen; evidence
  entries 132–135 in §6; two contracts dated 2026-09-15 in §5; the
  version landmark 0.4.30, the UTC-machine fact, the fixture-consumer
  include rule, and the "applied" report convention in §7.
- Registry deltas of the close: two riders whose ride condition board
  94 satisfied and the desk did not surface — `persist_pack_session`'s
  stale docstring (rides the next `bale_pack.py` touch) and
  `normalize()` into `tests/harness.py` (rides the next forecast
  holding it) — stand unconsumed, and the miss is §6 entry 135; the
  desk consults the registry at dispatch from here on. Proposals
  consumed this sitting: board 94's ADR-location defect became row 97;
  its stats read-side normalization became row 98; its `origin` parity
  finding grew row 91; its crafter bundle-stem clock line rides row 96
  (the crafter is in 96's forecast); its handoff-gate test failures
  became row 95; its midnight-straddle journal line stands as shipped,
  no entry.
- Sequencing for the next desk: rows 89 and 90 beside each other as
  previously recorded → 91 and 95 beside each other (91 holds
  `schemas/` and a pin; 95 holds
  `tests/test_checkpoint_provenance.py`, and `bin/bale_pack.py` only
  if the gate order rather than the tests is wrong — in which case 95
  follows 89) → 96 → 97 → the held wave: 68, then 56+57 beside it,
  then 69, then 37 (69 and 37 serialize on the crafter) → 43 → 45 →
  S6. Rows 92, 93, and 98 stand until brought forward.

Landed 2026-09-15, the continue-plan-004 sitting (master
`2026-09-15-continue-plan-004`, read-only; opened 2026-09-15 UTC on
"continue the plan" with two additions — outward docs three months
stale and a model-agnostic bale, and a bare `bale apply` that opens
every tarball in Downloads; the previous master
`2026-09-15-continue-plan-001` closed at close-8). Three rows opened
and landed in one sitting, three more opened and queued; this block
carries only what has no row home; close recorded by
`2026-09-15-sitting-close-deltas-9-008`:

- Wave record: three sessions. `2026-09-15-board-90-doc-residue-005`
  (bumpless, doc lane with one `bin/bale` string) and
  `2026-09-15-board-89-decline-cause-006` (0.4.31) ran beside each
  other on disjoint forecasts and applied clean, each with a blind
  checkpoint of eleven outcomes rehearsed both ways before emission.
  `2026-09-15-board-101-bare-apply-cap-007` (0.4.32) is a re-attempt:
  the first attempt was HELD with the blind checkpoint seven of seven
  PASS and the worker's own validation exiting 1 on a needle it could
  never see (§6 entry 138); the re-attempt's change set was
  byte-identical. One out-of-forecast drift admitted at 101
  (`bin/bale_report.py`, the handoff branch of the checkpoint-scope
  refusal — the ruling could not be met without it), and seven
  `tests/` paths admitted at 89 that the desk should have forecast (§6
  entry 140).
- Sitting-open record: close-8's notes.md ratified wholesale at the
  open (bullet spacing per the doc, unbracketed growths, block E under
  the 09-14 preamble, the coincidental duplicate paragraph, block G's
  five bullets). The sitting-open version check was satisfied by the
  request's provenance stamp, 0.4.30. Each worker's notes.md ratified
  in-sitting; the calls are named on the rows.
- The bare-apply finding, for the record: the resolver globbed
  `*.tar.gz` and opened every match with `getmembers()`, which
  decompresses the whole gzip stream to find `manifest.json`; cost per
  bare run was the total bytes of every tarball in every search path.
  The operator's rule, VERBATIM: "I should only ever be bare applying
  the latest tarball or second latest that fits the conventions in my
  search paths, it doesn't need to look through more than that." Ruled
  and landed at row 101 (§5).
- Two desk misses of record, both sequencing-side: row 47 dropped out
  of the "sequencing for the next desk" line at the 09-14 close when
  row 74 was decoupled from it, and stayed out until the operator
  asked whether the HOLD paste block was still queued (§6 entry 136);
  and row 95's two handoff-gate test failures were re-found from board
  89's notes and dispatched to 101 as a rider without the desk
  recognizing that row 95 already held them (§6 entry 137). Row 95 is
  DONE by 101; the dispatch check now reads the board's open rows by
  touched file, not only the registry (§7).
- Board 89's worker asked one non-blocking question in chat before
  building and read the operator's "go" as no preference — the third
  light-tier specimen for row 96, and a correct reading of a detail
  call under docs that still have no tier for it.
- Ratification debt carried forward, per convention: THIS close's
  notes.md queues to the next sitting's open.
- Board deltas of the close: rows 89, 90, 101 opened and DONE; row 95
  DONE by 101; rows 99, 100, 102, 103 opened in §4; rows 47, 77 grown;
  evidence entries 136–140 in §6; four contracts dated 2026-09-15 in
  §5; the version landmark 0.4.32, the tests-forecast rule, the
  re-attempt closing line, and the board-by-file dispatch check in §7.
- Registry deltas of the close: consumed — `persist_pack_session`'s
  stale docstring (89) and the BALE.md §7/§7.2 includes-as-scope
  true-up (closed on 90's read: nothing to fix). New entries from the
  three workers' Proposals: the `bale config hooks` row in BALE.md
  §5's command table and the "every admission y/N names its cause"
  sentence (both ride 99b); the `bin/bale_apply.py` module docstring
  that denies the lazy `import bale_pack` it contains; `shlex.quote`
  on the non-TTY bare-apply refusal path (rides row 102); "request
  includes" in the shared blindness diagnosis (only if the
  byte-shared-diagnosis constraint is re-ratified). Board 89's
  `<path>`-remedy proposal was folded into 101 and landed as the
  quoted alternative beneath the decline line.
- Sequencing for the next desk: 91 and 95 were beside each other; 95
  is done, so 91 → 47 → 102 → 96 → 97 → 99a → 103 → the 100 arc
  (design sitting first; absorbs 77; 99b rides its doc wave) → the
  held wave: 68, then 56+57 beside it, then 69, then 37 → 43 → 45 →
  S6. Rows 92, 93, and 98 stand until brought forward.

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
    [2026-08-25: S6 spec-intake substantially DISCHARGED at
    `2026-08-25-harness-discussion-005` — decomposition (the seed's
    rung ladder) and ambiguity questions (five, answered at the
    desk) done; per-arc checkpoint plans ride each arc's own pack
    authoring, per standing practice. The escalation-contract
    producer, the clarification-relay subsumption, and the
    session-interaction mechanization mandate route to the harness
    project (seed D13, D14) — the two that live as items below
    carry their own seed-doc pointers. Outward pointer, architect's
    ruling this sitting: the harness spec lives at the harness
    repo's `harness-seed.md`; MASTER.md carries no harness project
    documentation beyond this row.]
    [2026-08-31: the 2026-08-25 routing of the clarification-relay
    subsumption and the session-interaction mechanization mandate
    to the harness project is REVERSED for the worker↔planner leg
    (architect ruling at the `2026-08-29-formalize-convo-001`
    sitting; ADR-0017 records it) — the exchange arc mechanized
    that leg bale-side (the exchange-record schema, `bale relay`,
    the crafter's paste-block emission; 0.4.18–0.4.19). The
    escalation record's master→architect leg stays routed to the
    harness seed. S6's "session-interaction mechanization" charge
    is discharged on the worker↔planner leg by this arc; what
    remains under S6 is courier automation only. Cross-project: the
    architect carries the D13/D14 annotation to `harness-seed.md`,
    which lives outside this repo and outside any bale session
    here.]
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
      registry).] [2026-08-25: implementation half remains open on
      this board — the mechanism is bale-side — with the note that
      the harness's cage (seed §3) is its first unattended
      consumer; coordinate via board 9 Level 1 when it lands.]
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
      this item exists to make.] [2026-08-25: RESOLVED —
      tool-access lazy reading (seed D10, D11), the side this
      item's own annotation predicted, now with prompt-caching
      economics behind it. Physical doc splits remain decidable
      but unmotivated; the gating this item held over splits is
      released.]
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
      architect moving from transport to overseer. [2026-08-25:
      routes to the harness project — seed D13, D14
      (`harness-seed.md`).] [2026-08-31: reversed for the
      worker↔planner leg — see this row's 2026-08-31 bracket; the
      master→architect leg keeps the routing.]
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
      [2026-08-18: two live specimens accrued at the cleanup-master
      sitting — the v5 fixture-defect relay and the sitting's probe
      rounds; board 47 is the card-side counter; the artifact exchange
      remains this item's charge.]
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
      mechanization queued under it. [2026-08-25: routes to the
      harness project — seed D13, D14 (`harness-seed.md`).]
      [2026-08-31: reversed for the worker↔planner leg, and the
      charge is discharged on that leg by the exchange arc — see
      this row's 2026-08-31 bracket. Courier automation is what
      remains under S6.]
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

36. **`--checkpoint-file` expected-sha argument — ABSORBED**
    2026-08-18 into board 49 (the planner bundle carries
    delivery-time hash verification); pointer only, recorded at the
    smoothing sitting. Queued text in git (v5).

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
    [2026-08-31: reshaped by the §5 bailout-vs-compaction
    calibration ruling (the continue-plan sitting, session 026),
    which disposes the §3 ruling-queue item this row was waiting on:
    part 1 shrinks to what survives the ruling; parts 2–3 and the
    PLANNER.md rider are the surviving work, per the ruling's text
    of record in §5. Now packable per the sitting's sequencing
    rider.]

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
    [2026-08-18: grown at the smoothing sitting — the snapshot widens
    to a sitting world-state digest stamped at pack: open sids +
    forecasts, tree state, latest-applied. With bale_version already
    stamped, a master sitting opens zero-paste — the request answers
    what the desk would have asked. Landing this owes the evidence-80
    sweep: retire or re-point every doctrine line that routes a
    sitting-open status paste through the operator (board 10's
    operator-state-legibility item is the known citer).]

40. **readme/brief transport integrity — ABSORBED** 2026-08-18 into
    board 49 (bundle-manifest hash verification at `bale open`
    covers the brief side); pointer only, recorded at the smoothing
    sitting. Queued text in git (v5).

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
    [2026-09-01: DONE — `2026-08-31-board-41-base-drift-027`,
    applied at the 026 sitting at 0.4.23. Seven determinations
    ratified as shipped: ls-tree-at-HEAD enumeration for directory
    forecast entries; absence-over-null for no-base-bytes paths;
    committed-is-ratified on both ends, the dirty-at-pack residue
    accepted as a recorded property; a stamped file deleted at the
    base refuses; a malformed stamp reads as stampless, loudly;
    gate placement pre-staging with a single dry-run/real code path
    (noted at the desk: better than the checkpoint-stamp precedent
    it copied — no inherited dry-run duplication); handoff stamps
    too. Whole-tree stamp growth recorded as a known property. The
    stats read side floor-matched to the required-check pair's
    launch floor; re-trigger: the first real base-drift-refused
    occurrence in the corpus.]

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
    [2026-09-01: DONE — `2026-09-01-board-42-telemetry-fields-003`,
    applied at the 026 sitting at 0.4.24. docs_read and origin
    landed additive/legacy-tolerant; the one-home delegation
    verified by test — exchange rounds inherit origin with no
    second edit; the retry/open rider doc landed in the telemetry
    schema description, and the doc echo it offered was DECLINED at
    the desk — one home stands, closing the session's deferred
    entry; the write-only floor recorded as a decision (read side
    lands when data accrues); the guard-forced
    tools/response_lint.py embed refresh admitted per path at
    apply.]

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
    [2026-08-31: DONE — `2026-08-31-board-44-stats-read-sides-024`,
    applied 2026-08-31. All four read sides in one session. One
    admission at apply: tests/test_stats_drilldown.py (created —
    the separate-suite pattern test_stats_linkage.py names as
    ratified; admitted per path). Two proxy-form assumptions
    ratified as shipped: the telemetry record carries neither
    validation_will_run nor corrects, so the empty-claims cut and
    the dossier's corrects lineage shipped in computable forms
    with the divergence stated in both doc homes; the write-side
    promotion that unlocks the literal forms is registered in the
    §3 fold-in registry (024's rider), beside its dossier-wiring
    sibling. The brief's two fixture riders did not fire — the
    session never touched the shared-corpus expectations, and the
    fold-in registry was not in its context; the transport lesson
    is annotated on the registry entry: the next session that
    perturbs those expectations must be shipped the registry
    text.]
    [2026-09-01: row-44 true-up at the 026 sitting — 018's folded
    read side landed with 024, verified against shipped bytes at
    the sitting: `"opened"` in IN_FLIGHT_OUTCOMES,
    provenance-stamp-first resolution in session_work_class. The
    stale "until it lands, every stats run warns" fold-in bracket
    (2026-08-31) is struck this landing — the one sanctioned
    retroactive edit of this close.]

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

46. **small doc deltas, one carrier — DONE** 2026-08-18 (sid
    `2026-08-18-board-46-doc-deltas-006`; telemetry; doc-only, no
    bump). All ten cargo items landed: PLANNER.md is now the
    doctrinal home for the calibration-sitting doctrine, the
    bad-oracle correction protocol, the hooks rule, the pruning
    duty, the provenance-split probe rule, and the hot-file
    sentence; TARBALL.md §3.2 carries the scopeless-goal exemption
    and §5.2.2 the forecast_departures mention; DOCS.md carries
    the telemetry disposal policy and the fifth sanctioned pair.
    Queued text and the grown-cargo brackets in git (v5).

47. **HOLD-card triage surface** — queued 2026-08-18 (small; bale code
    + docs): the HOLD card gains a judge line naming which judgment
    held (blind checkpoint, worker validation, or both) and the failed
    probe labels the checkpoint already writes to the session log; and
    the retry line forks by ruling per the bad-oracle protocol —
    fixture defect: amend the checkpoint at the desk and retry the
    same tarball through the provenance gate; work defect: bale retry
    with a new tarball — every successor named on the card. The failed
    probe labels also ride telemetry as an additive field, so the §5
    blindness watch's HOLD-clustering read can split fixture-defect
    HOLDs from worker misunderstanding mechanically. Motivating
    specimens: the two label-blind HOLD relays at the 2026-08-16/18
    sitting — the card names only the worker-retry successor, and the
    operator's card-plus-log paste delivers the labels to the actor
    who cannot rule on them. (Sitting close, 2026-08-18.)
    [2026-08-18: grown at the smoothing sitting — the card emits
    addressed relay blocks: a desk-facing block (judge line, failed
    probe labels, exit codes, stamp state, with the relevant
    session-log bands inlined — the checkpoint band and the worker
    band, replacing the operator's card-plus-cat-log paste) and a
    worker-facing block carrying spec-safe failure context that
    structurally cannot leak oracle mechanics — the addressing
    decision moves from the operator under triage pressure to the
    tool. The happy path gains a desk-facing block too: notes.md +
    verdict + admissions, pre-assembled for the ratification relay.
    Ratified 2026-08-18.]
    [2026-09-10: grown at the 2026-09-01/02 sitting's close, the
    existing ratified cargo kept. Three additions: the retry line on
    the HOLD banner is the stamp-fed composed retry row — the data
    is on disk at render time since row 71's `held_tarball` stamp;
    the banner's successor fork is rendered per ruling class —
    fixture-defect vs work-defect — each line complete (the §7 desk
    emission rules, applied by the tool); and row 74's three
    emission-contract micros ride this row's TARBALL.md touch.
    Interim operator rule until this row lands: HOLD material
    routes to the planner first, never the worker — the addressed
    blocks land that routing mechanically here.]
    [2026-09-14: the "row 74's three emission-contract micros ride
    this row's TARBALL.md touch" clause above is struck — row 74
    landed independently at `2026-09-14-doc-lane-74-76-002` by
    desk ruling this sitting, decoupled from this row's touch; the
    rest of the 2026-09-10 cargo stands.]
    [2026-09-15: resequenced — this row dropped out of the sequencing
    line at the 09-14 close when row 74 was decoupled from it (§6
    entry 136) and is back directly after row 91. Fresh specimen:
    101's HOLD this sitting, relayed by hand as card plus log. The
    composed retry line on the banner is quoted through `shlex.quote`
    per the re-attempt closing-line rule (§7).]

48. **Pack-time checkpoint dry-run echo — ABSORBED** 2026-08-18
    into board 49 (the `bale open` dry-run leg); whether the
    non-bundle pack path keeps a standalone echo is a decision
    recorded inside row 49 for its session. Queued text in git
    (v5).

49. **The planner bundle + `bale open`** — queued 2026-08-18 at the
    smoothing sitting (ratified direction; absorbs boards 36 and
    40, subsumes board 48's dry-run leg). One planner-emitted
    artifact — brief, blind checkpoint, full pack argv, and
    published sha256s in one file with its own manifest — consumed
    by one bare verb: `bale open <bundle>` normalizes line endings,
    verifies both hashes against the bundle's manifest, dry-runs
    the checkpoint read-only against the live base and echoes the
    expected-HOLD proof (named probes executing against real bytes;
    exit 2 refuses as a defective oracle), then packs — the
    operator surface is save one file, paste one emitted line: the
    `bale open` invocation ships beside the bundle, fully composed
    by the authoring desk, never typed from memory (the
    paste-block-surface contract, §5 2026-08-18). The emission
    half rides with it: crafter-side bundle assembly, so the desk
    never hand-composes argv or hash blocks (the paste-surface
    hazards close at both ends). Design constraints engraved at
    ratification: (1) the bundle is oracle-bearing — it contains
    the checkpoint — so it is structurally invisible to workers,
    auto-excluded from packs the way checkpoints are (deny-list
    class, never convention); (2) `bale open` internalizes flows
    that carry deliberate decline-default prompts (supersession's
    y/N), so the bundle carries pre-answered intents explicitly —
    the verb never bypasses a decline-default silently; (3) the
    standalone non-bundle echo question per row 48's pointer. Verb
    ratified `open`; `spawn` noted as the harness-era rename
    candidate. Sequencing: early — every close after it stops
    traveling the old ceremony.
    [2026-08-18: bracketed at the sub-master sitting — the spawned
    session returned a §11.2 rescope offer; its three-way seam ratified
    at the desk: 49a-i (bundle format + pack-side deny-list + the
    pre-answered-intents API through the decline-default exchange) →
    49a-ii (the open verb, bin/bale wiring, both hash verifications, the
    dry-run leg, the row-48 standalone-echo decision) → 49b (crafter
    emission). Session 009 unlocked with no successor; the delivered
    revA brief and v1 checkpoint are derivation sources for the resumed
    arc, never rewrites. The pairs-pin rider re-routed to the sub-master
    contract-doc landing.]
    [2026-08-24: 49a-i DONE —
    `2026-08-24-board-49a-i-bundle-format-003`, first-try PASS. The
    .bale-bundle deny-list and the in-process pre-answered-intents API
    are landed; the format spec's home and the two consumer contracts
    are recorded in its archived notes; seven judgment calls ratified.
    Next: 49a-ii, packed fresh against the applied tree.]
    [2026-08-24, second sitting: 49a-ii DONE —
    `2026-08-24-board-49a-ii-open-verb-006`, first-try PASS at 0.4.13.
    The open verb ships end to end: the validate-bundle gate first, both
    member-hash verifications, the read-only dry-run with the
    expected-HOLD proof, argv replay with delivery-flag injection, the
    intents channel exercised under piped stdin. The row-48 decision
    resolved bundle-only; ratifications and tallies in §3. Next: 49b
    (crafter emission), packed fresh against the applied tree.]
    [2026-08-25: 49b DONE — `2026-08-25-board-49b-crafter-emission-001`
    at 0.4.14, the crafter emits and bale open consumes; the desk types
    neither. Arc complete — boards 36 and 40 discharged with it, 48's
    disposition stands in BALE.md §6.7; ratifications and tallies in
    §3.]

50. **CRLF tolerance at every text-file read** — queued 2026-08-18
    (small): bale tolerates CRLF wherever it reads text files
    (briefs, checkpoints, probe files, config), so the Downloads
    sed ritual stops existing as a concept rather than becoming a
    step something automates. Kills the §7 environment wart at the
    source; sweep §7's CRLF line when this lands (evidence 80's
    rule).
    [2026-08-25: DONE — `2026-08-25-board-50-crlf-tolerance-004` at
    0.4.15. Premise correction: the row's read-site list was half
    stale — briefs and config were already tolerant; the desk's
    pre-pack rehearsal caught it and scoped the session to the truth,
    not the row. §7 CRLF sweep satisfied — the sed line is retired,
    and evidence 80's owe-note is discharged for this board.]

51. **Bare `bale apply` resolution — RATIFIED 2026-08-18, queued**
    (small): apply with no argument resolves the newest response
    tarball matching an open session across the search paths,
    echoes its identity, and takes a y/N; ambiguity — two
    candidates, or two open sessions — refuses loudly, never
    guesses. Save one file, one emitted paste: the apply-side
    floor.
    [2026-08-25: DONE — `2026-08-25-board-51-bare-apply-007`, bumpless
    per the hot-file ruling. Flagged ambiguity interpretation, ratified:
    ambiguity means two candidates the newest-rule **cannot separate**, not any two candidates — the stricter reading would make "resolves the newest" dead text.]
    [2026-09-14: row 87 opened — the naming variance between
    `response-NNN.tar.gz` and `response-<sid>.tar.gz` is what
    defeats this row's matching; the resolver check rides 87.]
    [2026-09-14, at the close: the multi-open-refuses clause ("or
    two open sessions — refuses loudly") is superseded by the
    operator's ruling of this date (§5: bare apply resolves across
    the open set — candidates answer any open session, newest by
    `st_mtime_ns` wins, an exact tie refuses, the echo names the
    resolved session and the open set; landed by
    `2026-09-14-apply-side-81-87-010`, row 87's resolver half).
    Tie refusal, content discrimination, and the non-TTY decline
    stand. The pointer above is corrected: naming variance never
    defeated this row's matching — the resolver is content-based;
    the master's own read-only session counting as open did (§6
    entry 123).]

52. **Pack output emits the chat-opening preamble** — queued
    2026-08-18 (small): the pack report ends with the
    session-opening chat paragraph as a copy block — bale owns,
    versions, and emits the paragraph the architect today
    maintains by hand, and it carries the session's identity (sid,
    goal) so the opener names what was just packed. The
    cross-surface form of every-command-names-its-successor:
    pack's successor is a chat message, so pack emits it. Sweep
    any doctrine describing the hand-carried preamble when this
    lands (evidence 80's rule).
    [2026-08-25: DONE — `2026-08-25-board-52-pack-preamble-006`,
    bumpless per the hot-file ruling (the pair's bump rode the
    rider). Preamble-doctrine sweep discharged at the rider in
    `docs/CLAUDE.md` (bale-emitted since 0.4.16), outside this doc's
    forecast; no in-doc target remained — §5's 2026-08-18 paste-block
    contract already stated the post-52 residual.]

53. **Checkpoint amendment as a first-class verb** — queued
    2026-08-18 (small-to-medium; bale code + docs): the
    bad-oracle correction flow's operator half is today a
    hand-composed chain — copy from Downloads, CRLF strip,
    hash compare, commit at the per-sid path, retry, accept
    flag at the stamp refusal — the exact paste-surface hazard
    class rows 49/51/52 retire elsewhere. A formal surface
    (name open; amend-checkpoint the working spelling)
    resolves the open session, normalizes line endings,
    verifies the delivered file against a desk-published
    sha256, commits at the per-sid checkpoint path
    (bale-prefixed subject, pathspec-limited), and emits the
    retry line as its named successor. The verb mechanizes
    the transport, never the deliberateness: the provenance
    gate still refuses at retry, the accept stays
    per-invocation, and stamp_matched false remains the
    truthful record. Motivating specimen: the
    continue-plan-005 close correction (carry-forward 1).
    Plausible board-49 adjacency — the bundle owns
    checkpoint delivery; amendment is its revision path —
    the sequencing call is the next desk's.
    [2026-08-25: sequencing ruling — rides after the pair (now
    landed), with board 50's ingest normalization now sitting
    underneath the amendment verb for free (CRLF strip is no longer
    the operator's hand step). Next-up candidate among the smalls.]
    [2026-08-26: DONE — `2026-08-26-board-53-amend-checkpoint-004`
    at 0.4.17. `bale amend-checkpoint` lands the bad-oracle
    correction flow's operator half: resolution, mandatory
    published-hash verification, LF-normalized ingest (board 50's
    one implementation, imported), the accounting rung against the
    pack-time `provenance.checkpoint` stamp, the per-sid commit,
    and the paste-ready retry successor. Ratifications and tallies
    in §3; the accounting contract is §5's, this date.]

54. **Arc-level dual-stream mechanics** — queued 2026-08-18
    (medium; bale code + schemas + docs): the sub-master
    doctrine's mechanical half. An arc-oracle home distinct from
    the per-response checkpoint slot — the read-only waiver
    collision on record: a sub-master's own session is read-only
    while its subtree lands plenty — executed read-only against
    the live tree at arc close (board 49's dry-run execution
    shape, expecting PASS); the required upward-report sections
    given a wire home (landed/ratified/escalated/on-watch, the
    arc claims block, consumed-vs-deferred scope, proposals); arc
    claim/verdict telemetry so reconciliation pairs the
    sub-master's summed validation with the arc verdict. Manual
    path first, proven by hand; harness transport rides S6.
    Motivating record: the 2026-08-18 sub-master sitting (§3).

55. **Bundle-stem collision guard** — queued 2026-08-25 (small;
    investigation-first): the open verb's expected-HOLD gate exists
    to refuse a bundle whose oracle passes against the live base, and
    the `-009` open packed a stale twin anyway. Establish why first —
    an oracle-less legacy bundle, or probes that still fail against
    today's tree — before choosing the mechanism: stem-uniqueness
    refusal, a prominent desk/created-at provenance echo, or a
    hardened dry-run gate. Small, evidence-fed by §6 entry 85;
    sequenced by the next desk among the smalls. Interim rule until
    it lands: desk-unique bundle stems (§6 entry 85).

56. **Changelog record family** — queued 2026-08-25 (small; from
    the harness spec-intake sitting, seed D5): schema per existing
    record conventions (loose), a validator row so omission is
    loud, and the same-response discipline sentence in the
    appropriate contract doc — the session that changes a
    machine-readable surface writes the entry. Primarily for
    bale's own version ladder; the harness is its first external
    consumer, and its consumption manifest references the same
    surface list — a natural board-9 Level-1 linked pair with the
    harness side if timed together, not required to be.
    Retroactive backfill explicitly out of scope.

57. **`aborted`-class closure reason** — queued 2026-08-25 (small;
    from the harness spec-intake sitting, seed D15): the harness
    kill-switch wants a closure vocabulary entry; additive,
    follows the v0.4.7 legacy-tolerant pattern. Ratified as its
    own small board item alongside board 56; sequencing among the
    smalls is the next desk's call.

58. **exchange constants, install-side parity** — queued 2026-08-31
    (small; from the exchange arc's close): accepted from the
    crafter session's first Proposal, scope as written there —
    validate.sh beside the crafter rows; needs load-bin/bale-by-path,
    a new capability, hence its own session.
    [2026-08-31: DONE —
    `2026-08-31-board-58-exchange-constants-parity-016`, applied
    2026-08-31. Five-constant parity scope ratified per its notes
    (the five constants both homes declare; the crafter's wider set
    re-declares bale_validate.py's rules, pinned by the byte-parity
    suite); the presence-rows rider (board 59's Proposals, with the
    registry's bale_open/bale_sandbox pair) consumed here — the §3
    registry entry is marked consumed.]

59. **Extract bin/bale §29 into `bin/bale_relay.py`** — queued
    2026-08-31 (from the exchange arc's close): accepted earlier in
    the arc with sequencing "after the crafter lands"; now
    unblocked. Scope per the relay session's Proposal: `bin/`,
    `install.sh`, `scripts/build.sh`, packaging-test coverage list.
    Note for the brief-author: the crafter re-declares rather than
    imports, so extraction changes nothing tools-side; the parity
    suite is the guard that must stay green across the move. Rider
    disposition from the close: the crafter index header (the
    crafter session's second Proposal) folds in here if this
    session's forecast gains `tools/` for any reason, else it runs
    as its own micro-session.
    [2026-08-31: DONE — `2026-08-31-board-59-relay-extraction-014`,
    applied 2026-08-31 at 0.4.21, HOLD-then-retry (worker-side
    parity-suite root cause: the extraction took the wire symbols
    off the entry module's import surface and the refusal path
    assumed the host's fail; fixed by a narrow re-export plus a
    host-preferring fallback, ratified). Two admissions at apply:
    the new relay module, bin/VERSION. The index-header rider
    resolved to its own micro-session — the forecast never gained
    `tools/` — and rides the wave-3 crafter pair (the §3 wave-2
    dispositions block).]

60. **`bale relay` re-emit path** — queued 2026-08-31 (from the
    exchange arc's close; ruling now made): accepted as a board
    item, not yet as surface. The need is real (a planner-side
    block exists only on the stdout that made it) but it widens the
    option surface ADR-0017 closed at `<sid> <file|->`, so the
    landing session's brief must carry the doctrine half — an
    ADR-0017 Notes append recording the widened surface — and the
    shape decision (no-file `bale relay <sid>` reprint vs a
    separate read-only verb) is made there, not here.
    [2026-08-31: DONE — `2026-08-31-board-60-relay-reemit-017`,
    applied 2026-08-31 at 0.4.22, HOLD-then-retry (worker
    validation.sh bugs, not the change set; the blind checkpoint
    passed both rounds). Shape ruling recorded: no new verb, the
    file argument optional, the no-file form re-emits the latest
    recorded round and records nothing; ADR-0017 Notes appended.
    bin/VERSION admitted at apply. Rider dispositions per its
    notes: the BALE.md §7.5/§7.7 group mention landed (§7.5's walk
    step got the sentence; §7.7 already carried its half); the
    §7/§7.2 includes-as-scope true-up landed (six word-level
    substitutions — both registry entries marked consumed); board
    59's section-29 citations true-up — only §8.11's block
    provenance line was stale, now citing bin/bale_relay.py; row
    §11.34 and the §5 verb inventory never cited section 29.]

61. **Global-doc purge** — queued 2026-08-31 at the meta-specific
    sitting (mixed class; first in sequence; packed the same day,
    sid slug `global-doc-purge`). One response: strip or inline
    every evidence-N and board-number citation across the five
    globals; rewrite PLANNER.md §8's sanctioning paragraph; repoint
    TARBALL.md §5.9.2's orchestration-documentation sentence at
    PLANNER.md §15; name the amend-checkpoint verb in PLANNER.md §5
    step 5; fix the injected crafter's dangling design-doc pointer;
    and extend tests/test_global_doc_selfcontainment.py in the same
    response with citation-shape deny patterns plus the injected
    tools in the scan set, so the pin lands with the cleanup it
    pins. Fallback if it runs heavy: docs purge (contract-doc)
    first, guard extension (code) second, the guard depending on
    the purge.
    [2026-08-31: DONE — landed at `2026-08-31-global-doc-purge-004`,
    applied 2026-08-31, reinstall fired. Ratifications from its
    review are §5's fold-in/purge-review block; specimens are §6
    entries 93–94.]

62. **PLANNER.md doctrine additions** — queued 2026-08-31
    (contract-doc class; serializes after board 61 — both forecast
    docs/PLANNER.md). Two additions to the core: the
    bundle-delivery practice (checkpoint-pinning projects deliver
    spawn materials via the crafter's bundle emission plus the
    emitted bale open line; the format itself stays in the bale
    tool's documentation), and a one-sentence §2 prompt to carry a
    narrow `--write` forecast when split sessions should run
    concurrently.
    [2026-08-31: DONE — landed at
    `2026-08-31-board-62-planner-doctrine-008`, applied 2026-08-31
    (contract-doc class; no version claim). Both additions landed;
    placement calls per its archived notes.]

63. **Provenance stamped at open** — queued 2026-08-31 (code
    class): pack writes work_class/packer provenance into the
    registry and telemetry record at session open, so every exit
    path carries it — closes the 49-record blind spot where
    unlocked sessions (27% of the corpus) are invisible to
    per-class and per-packer rates. Candidate rider: closed
    vocabulary or normalize-at-stamp for packer and model_identity
    (ten packer spellings and roughly 62 model_identity spellings
    in the corpus today).
    [2026-08-31: DONE —
    `2026-08-31-board-63-provenance-at-open-018`, applied
    2026-08-31. One paste-back probe round. Ratified per its notes:
    the stamp rides the opened attempt; the write lives in
    persist_pack_session; handoff opens stamp command pack as a
    bounded flagged inaccuracy; the registry stamp carries exactly
    the two fields; the normalize-at-stamp rider deferred with
    rationale (now a §3 registry entry, beside the widening
    proposal). Read-side proposal folded into board 44 (its row's
    bracket).]

64. **Release-surface include group** — queued 2026-08-31 (code
    class): a named include/forecast group (bale.toml or a
    pack-time hint) so bin/, tests/, or schemas/ includes pull
    install.sh, scripts/build.sh, validate.sh, upgrade.sh, docs/,
    and schemas/ along. Retires the corpus's most-repeated
    includes_missing class (8+ recurrences over six weeks), the
    matching overridden_paths admission cluster (14 events on the
    same file family), and the can't-run-locally claim/verdict
    DISAGREEs (all 9 in the corpus) in one fix.
    [2026-08-31: DONE — landed at
    `2026-08-31-board-64-release-surface-group-009`, applied
    2026-08-31 at 0.4.20, reinstall fired. (0.4.20 is the wave's
    close version per the operator's `bale --version` at the
    continue-plan-012 sitting; the desk did not resolve which of
    009/010 rode the bump — strike this attribution at review if
    the desk corrects it, same flag on row 65.) Three
    out-of-forecast admissions at apply (bin/bale, bale.toml,
    tests/test_include_group.py), all admitted; design
    ratifications per its archived notes. The board's BALE.md
    deltas rode the close rider
    `2026-08-31-board-64-65-close-rider-011`, landed as a
    HOLD-then-corrected-retry: the first response HELD on two
    probes, the ruling arrived by chat relay (S2 dropped as
    already-landed, S3 replaced by a desk sentence), and the
    corrected retry landed with `corrects` lineage — the rider's
    archived notes are the durable record of the question and its
    answer per the TARBALL.md §5.9.1 provenance fallback
    (cross-referenced from row 65). Lane reconciliation, ratified
    at the continue-plan-012 sitting, consuming 011's Proposal:
    Board 64's documentation cargo landed at its own session; the close rider's deferred-doc premise was stale, and the drift was the rider brief's, not the board's.
    Basis: 009's forecast named BALE.md and its unconsumed entries
    were only validate.sh, scripts/build.sh, install.sh — BALE.md
    was consumed at 009.]

65. **Linkage rollup** — queued 2026-08-31 (code class): a bale
    stats aggregation over feedback.mechanical.linkage, giving the
    field a consumer — the corpus carries 9 clarification linkages
    and 10 probe linkages, yet every close-time clarification
    stamp reads rounds: 0 — every blocking ask to date resolved
    off-artifact, and the signal lives only in linkage, which
    nothing queries.
    [2026-08-31: DONE — landed at
    `2026-08-31-board-65-linkage-rollup-010`, applied 2026-08-31 at
    0.4.20, reinstall fired (same wave's-close version attribution
    caveat as row 64's bracket — strike at review if the desk
    corrects which of 009/010 rode the bump). Two out-of-forecast
    admissions at apply (bin/bale_report.py,
    tests/test_stats_linkage.py), both admitted; judgment calls
    ratified per its archived notes. Its BALE.md stats line rode
    the close rider `2026-08-31-board-64-65-close-rider-011`; the
    rider's HOLD-then-corrected-retry record and the lane
    reconciliation it prompted live on row 64's bracket.]

66. **Install-surface schema purge** — queued 2026-08-31 (mixed
    class; serializes after board 61): the five non-embedded
    schemas (request-manifest, telemetry-record, escalation-record,
    exchange-record, bundle-manifest) ship with the install and
    their description strings cite BALE.md, orchestration.md, and
    board numbers — dangling from any other project's vantage.
    Resolve to self-standing prose or the doctrine's global home
    (PLANNER.md §15 for the orchestration citations); descriptions
    are inert to validation, so behavior is untouched. Discovered
    at the 2026-08-31 desk rehearsal, which also widened board 61
    to cover the lint-embedded response-manifest schema.
    [2026-08-31: sweep extension, ratified at the fold-in/purge
    review — when this row runs, its purge also sweeps sitting-label shapes
    (S-digit forms and session-letter residue) in the five schemas'
    descriptions, not only evidence and board numbers. The purge
    session found and genericized one such residue ("S5") in the
    response-manifest schema.]
    [2026-08-31: DONE — `2026-08-31-board-66-schema-purge-015`,
    applied 2026-08-31. Five judgment calls ratified per its notes
    (ADR citations stay; sitting labels became version anchors; one
    dated citation rewritten beyond the literal deny set; BALE.md
    pointers resolved to the unnamed form; deliberately broad deny
    sweep in validation — the sweep extension above executed as
    ratified). Deny-shapes guard proposal routed per the §3 wave-2
    dispositions block.]
    [2026-09-10: the unnamed-form call is repaired at row 70 —
    ratified record that resolving BALE.md pointers to an unnamed
    form converted a nameable dangle into an undiagnosable one; the
    durable rule is re-pointing at surfaces that ship.]

67. **Suite repair (the 17 stale tests) — DONE at birth**
    2026-09-01 at the 026 sitting (lineage: spawned from 027's
    Proposals): `2026-09-01-board-67-suite-repair-002`, applied
    2026-09-01. Suite green under both gate positions, unconfined
    and confined; the reversed fail-loud rationale in
    test_sandbox_wrapper ratified as shipped (the grading topology
    broke the docstring's premise — a confined run's staging cwd
    can be /tmp-resident, so the absence is a legitimately missing
    capability, not a broken contract); the constraint-2 retry
    finding and its admitted source fix — retry's re-persist
    appended a spurious mid-session 'opened' telemetry attempt,
    fixed by `open_telemetry=False` on retry's re-persist
    (bin/bale_pack.py + bin/bale, both admitted per path; the
    corpus tolerance this leaves is §7's dated note); the
    writable-non-tmp-base capability identified as the entire
    confined delta's key (all 11 confinement-only ids probe it;
    the guard now prints probe, finding, and run/skip decision);
    the 42-vs-43 skip-count loose end recorded with the worker's
    arithmetic — if the grading oracle ever pins skip counts,
    expect 53, not 54.

68. **bale open gate ordering** — queued 2026-09-01 (small; bin/):
    reorder bale open so arg-inspectable pack gates (forecast
    existence, disjointness) run before the checkpoint dry-run —
    cheap gates before expensive oracle executions. Specimen: this
    sitting's r2 open, where a ~9-minute confined dry-run ran
    before the disjointness gate refused on arg-inspectable
    grounds (§6 entry 102). Carrier note: the registry's
    release-surface tools/ extension rides this row's bin/ touch.
    [2026-09-10: grown at the 2026-09-01/02 sitting's close: open and
    pack refusals name the resolved project root and the config
    files they judged. Live specimen: a `bale open` run from
    `~/yt-mp3` refused on a missing `[validation]` base, and the
    refusal's "this project" cost a probe round that a named path
    would have prevented (§6 entry 111). Supersedes the
    momentarily-queued "committed-vs-dirt config pre-check" idea —
    obsoleted by diagnosis: the dirty file was the master's own
    open-time telemetry record, normal in-flight state.]
    [2026-09-14: this row's principle — cheap gates before
    expensive ones — applied at row 78 to a prompt: drift refuses
    before the sandbox prompt (§6 entry 122). The `bale open`
    reorder itself is still queued here.]

69. **tools pair** — queued 2026-09-01 (one micro session, both
    halves from the 026 sitting): (a) a bare-string claims-value
    check in tools/response_lint.py (a CLAIMS_VALUE finding;
    vocabulary pass|fail|untested|unknown), closing the
    lint/apply parity gap of §6 entry 104; (b) seed docs_read in
    the crafter's self_reported skeleton, text verbatim from 003's
    Proposals: "What: have `tools/craft_response.py`'s manifest
    skeleton include a `docs_read: []` stub (or a commented nudge)
    in the `self_reported` block it emits. Why: grounded in this
    session — the skeleton names only the required self_reported
    keys, and an optional field with no scaffold presence tends to
    go unfilled; the field's value is longitudinal, so early fill
    rates decide whether the read side ever accrues the data it is
    deferred on. Scope hints: tools/craft_response.py (and its
    embed-parity tests if the skeleton is asserted anywhere); only
    after this session lands."

70. **shipped-doc reachability — DONE** 2026-09-01 at the
    continue-plan-005 sitting (opened in-sitting under the first
    commandeering; mixed class):
    `2026-09-01-board-70-doc-reachability-007`, applied
    2026-09-01. Six ratified inventory sites plus two
    out-of-inventory "design documentation" tombstone pointers
    (the TARBALL.md §5.6.3/§5.9.3 tombstones, per the worker's
    record) found and fixed by the worker under an in-scope
    deviation, ratified as shipped (goal text plus the
    never-cites-a-doc-that-does-not-ship constraint read as
    authority; deny shape widened with an optional `design`
    alternative to pin it). CLAUDE.md gained the reachability
    paragraph; the self-containment guard denies the pointer class
    wrap-tolerantly. No version bump — ratified as a reading of the
    doc-only exemption's own rationale (no shipped-tool behavior
    change), recorded as a reading, not a new exemption class.
    Worker proposal accepted: whether the pointer-class deny joins
    the schema group's table — annotated onto the guard tables'
    standing convergence question (the §3 registry), rides the
    next guard-touching sitting. Mid-arc the spawn materials were
    re-issued with neutralized vocabulary (r1 stem
    `…injection-reachability` superseded by r2
    `…doc-reachability`) after the word "injection" primed a
    worker's safety heuristics in a foreign project — §6 entry
    108. Retry story: HOLD on a desk fixture defect (P5 pinned a
    deny pattern's spelling — mechanism over outcome), amended
    v2→v3 with an implementation-agnostic plant-and-red probe;
    then one gate-refused retry (accept flag omitted; the refusal
    named it), then the accepted retry — the predicted sequence.
    The retry's stamp mismatch was accepted deliberately, and this
    sentence is its prose record (telemetry: `stamp_matched:
    false`, PASS, 2026-09-01). Repair of record carried on row 66:
    the purge's unnamed-form resolution converted a nameable
    dangle into an undiagnosable one; re-point at surfaces that
    ship. Registry strike: the bin/-sanction docstring line,
    consumed here.

71. **lifecycle resolution from the artifact in hand — DONE**
    2026-09-02 at the continue-plan-005 sitting (opened 2026-09-01
    in-sitting under the second commandeering, the operator's
    HOLD-friction outline; code class):
    `2026-09-01-board-71-lifecycle-resolution-008`, applied
    2026-09-02 at 0.4.25. Retry resolves its session from the
    tarball's own `responds_to`; `--sid` demoted to a vetting flag
    (mismatch refuses naming both sids and the tarball);
    resolve-before-wipe — every retry refusal now leaves HOLD
    state byte-identical, pinned by `assert_hold_intact` (an
    ordering improvement over the old wipe-then-refuse, explicitly
    desk-wanted and ratified); `bale amend-checkpoint` emits a
    fully composed placeholder-free retry successor from a
    HOLD-time `.bale/sessions/<sid>/held_tarball` stamp (legacy
    HOLDs degrade loudly to the placeholder form); non-open sids
    refuse as closed-naming-last-outcome (defensive telemetry
    read) vs unknown-to-this-repo; the apply-side bundle backstop
    rider landed as §11 row 37 / step 18 (BALE.md; the worker's
    record sites the step at §8.1) reusing `is_bundle_file`;
    ADR-0006 gained the dated artifact-borne-resolution Notes
    append; BALE.md trued up (including documenting the
    previously-undocumented `staging_path` — kept at
    ratification). `peek_responds_to` is the public spelling;
    alias retained. Worker proposals dispositioned: the stamp-fed
    composed retry row on the HOLD banner — accepted onto board 47
    (grown cargo); handoff/open `--sid` generalization — accepted,
    absorbed into new row 73; the response-manifest echo schema
    gap — accepted as new row 76, with the worker's
    drop-`base_files`-to-validate call ratified as the interim
    reading (the echo is verbatim-minus-the-stamp) until 76 lands.
    In-flight correction (telemetry, trued up): the amend suite's
    fixture dependency `tests/test_per_sid_checkpoint.py` did not
    ship and arrived as an upload after an informal ask — the
    record carries it under includes_missing and zero exchange
    rounds (§6 entries 110, 112). Retry story: HOLD on a desk
    fixture defect (P2 contradicted the brief's own W2), amended
    v1→v2 by STRIKING the probe — the first probe-deletion
    amendment; the retry's stamp mismatch was accepted
    deliberately, and this sentence is its prose record
    (telemetry: `stamp_matched: false`, PASS, 2026-09-02).
    Registry: the apply-side bundle backstop consumed here; the
    stats-dossier wiring rider deliberately not folded in.

72. **clarification auto-close — RESOLVED, not a defect** (born
    resolved 2026-09-10, at the sitting's close): the operator
    determined the close was working-as-intended — a default-Y
    close prompt on the previous pack was glossed under triage.
    Recorded with its trail in case it recurs; no code change. The
    surviving half of the report became row 74's dual-transport
    rule.

73. **handoff: fix-or-retire, reproduce-first** — opened
    2026-09-10 (decision-shaped; bin/ + tests/): an operator's
    foreign-project session invoked handoff and it failed — apply
    trouble, no adherence to forecast disjointness, apparently old
    syntax. Original logs lost; the investigation reproduces on a
    harness fixture instead (tests/test_handoff_happy.py exists
    and passes, so the break is in a path the happy test doesn't
    walk — that gap is itself evidence). The surface visibly
    predates the modern gate era. Decision: modernize fully
    (gates, provenance, current argv) or formally retire with a
    tombstone so sessions stop invoking it. Absorbs row 71's
    handoff/open `--sid` generalization question; consumes the
    registry's `gather_files_for_pack` verbose-kwarg rider when
    touched. Sequenced second, after row 75 (§3 close block).
    [2026-09-14: session A DONE, session B queued. Session A
    `2026-09-11-board-73a-handoff-reproduce-002` (reproduce-first;
    code class; pack, brief, and blind checkpoint desk-authored as
    a crafter bundle — the first bundle-delivered spawn of the
    sitting), opened 2026-09-11, applied 2026-09-14 at 0.4.26
    (telemetry; tests-only, no bump). Four new suites, seventeen
    tests, six `expectedFailure` reproductions, discovery green;
    checkpoint PASS on first apply, `stamp_matched: true`.
    Findings, one line each, the worker's numbering: (1) handoff
    refuses on *any* open session where pack runs the ADR-0007
    disjointness gate — reproduced; (2) `{sid}` checkpoint base:
    the resolved-existence refusal names `--checkpoint-file` as
    its first remedy and handoff's argparse rejects the flag — a
    remedy-text defect on top of a design-era gate; (3) literal
    base with a cited plan — not reproduced; (4) a plan-less
    handoff refuses on `forecast_declared=True` where a bare pack
    passes since v0.4.9 — unpredicted; (5) **the forecast swap**:
    handoff records the reading-plan set as the forecast and never
    reads the parent's `scope.json`, so the resumed session is
    graded against a forecast nobody declared — unpredicted, and
    the best fit to the original report; (6) the argv surface
    rejects every pack delivery flag — confirmed; (7) the manifest
    is modern (`base_files` stamped), the argv is old. **Desk
    ruling (2026-09-14): modernize**, in the worker's order 5, 1,
    4, 2, 6, plus the cheap `caller` kwarg on the
    resolved-existence refusal and the three-line
    `gather_files_for_pack` verbose rider (the registry entry's
    premise corrected: no `verbose` kwarg exists on that function
    today); the `--sid` generalization stays deferred (registry
    entry consumed). Session B's brief must say the six
    `expectedFailure`s are its acceptance tests (strip a decorator
    per fix) and that the diagnosis pins asserting today's refusal
    text flip by design. `includes_missing:
    tests/test_per_sid_checkpoint.py` — the desk's authoring
    defect, not the worker's (§6 entry 116). The two unpredicted
    classes trace to one sentence in `cmd_handoff` (§6 entry 117).
    Session A's notes.md ratified in-sitting. Sequenced first for
    the next desk (§3 close block).]
    [2026-09-14: session B DONE — row DONE.
    `2026-09-14-board-73b-handoff-modernize-007` (code class;
    crafter bundle), opened 2026-09-14T21:43Z, applied 22:14Z at
    0.4.28 (`bin/VERSION` in the change set; the apply-side
    request's provenance stamps 0.4.28). Checkpoint PASS on first
    apply, `stamp_matched: true`, after one relayed exchange round
    (round 1 → 2 through `bale relay`, pre-build, three questions;
    telemetry `clarification.rounds: 2`); one enumerated drift
    admitted at apply by prompt — `bin/bale_report.py`, the
    `caller == "handoff"` remedy sentence in
    `format_checkpoint_scope_refusal` and its docstring paragraph
    (ratified in the thread, round 2, question 2). Modernized in
    the desk's order 5, 1, 4, 2, 6: handoff reads the parent's
    `scope.json` and inherits its recorded forecast exactly (`[]`
    included), `--write` overrides, a missing record falls back to
    the reading-plan set undeclared (§5); the registry guard is
    gone — pack's gate is `run_forecast_disjointness_gate` at
    module level in `bale_pack.py`, pack's refusal byte-identical,
    handoff's variant offering `--write` / apply / unlock and never
    `--supersedes`; `forecast_declared` false on the fallback
    branch only; `checkpoint_resolved_preflight` gains `caller=`
    and an inherited or declared `[]` waives (`checkpoint_waived:
    "read-only"`), `--checkpoint-file` on handoff running pack's
    sequence; `--write`, `--read-only`, `--checkpoint-file`
    admitted, the other pack flags still rejected. Riders landed:
    the `caller` kwarg (73A's proposal 1); the `walk_for_pack`
    verbose threading (registry entry consumed); the three
    ADR-0007 sentences deleted, five `bale_pack.py` docstring
    sentences corrected; `BALE.md`'s handoff row rewritten with
    re-basing clauses on the `scope.json` tree comment, the §8.5
    waiver paragraph, and ledger row 30. All six `expectedFailure`s
    stripped (one acceptance test's record assertion moved ahead
    of the apply — a PASS merge wipes the session directory, so
    the body as written could never pass); every test-body rewrite
    is enumerated in its notes. Calls ratified: an inherited
    forecast is *declared* to the blindness gate (conservative — no
    silent renewal of an admission; the residue case gates row
    93); two `bale_pack.py` refusal texts mirrored into `bin/bale`
    rather than lifted; the pre-install
    `checkpoint_file_base_or_refuse` retained once. Surprises of
    record: the plan-less tests and the inheritance rule never met
    in the fixture — the clarification (§6 entry 124); `unittest`
    exits 5 on "NO TESTS RAN" (§6 entry 131);
    `exchange-record.schema.json` lacks the `origin` key (row 91).
    Proposals became rows 92, 93, and 91. Notes.md ratified
    in-sitting.]

74. **emission contract micros (doc lane)** — opened 2026-09-10,
    riding board 47's TARBALL.md touch: three one-sentence rules
    for the request-carried docs. (1) Emitted commands are single
    physical lines, never backslash-continued — continuations do
    not survive chat copy-paste (live specimen: a foreign-project
    pack line mangled by `\ ` sequences). (2) Formal asks always
    ship BOTH transports — the tarball and the paste-block text —
    so the chat route stays first-class (operator-requested; the
    surviving half of row 72's report). (3) TARBALL.md §10.1's
    checklist gains a step naming the crafter's `--emit-block`
    exchange emission as the blocking-ask path — today the
    checklist's own step 1 models informal asking (§6 entry 112).
    [2026-09-14: DONE — `2026-09-14-doc-lane-74-76-002`
    (contract-doc class, bumpless per the doc-only reading; one
    session with row 76), decoupled from board 47's TARBALL.md
    touch by desk ruling this sitting (row 47's carrier clause
    struck). Landed: the single-line rule widened in place in §3.4
    with a §1 Conventions pointer; both transports in §5.9.2 and
    §10.3 step 4 ("either" → "both"; "Never in chat" → "Never
    as a chat aside"); the blocking-ask path as §10.1 step 2's
    second sentence (step count 11 before and after). Notes.md
    ratified in-sitting.]

75. **sandbox-off by config** — DONE 2026-09-11, spawned beside the
    sitting's close (2026-09-10; bundle stem
    `2026-09-10-board-75-sandbox-config-off`, opened as
    `2026-09-10-board-75-sandbox-config-off-002`; mid-build at
    this landing — a round-1 exchange record from its worker was
    answered by the desk 2026-09-10): `[sandbox] enabled = false`
    at the project layer for hosts without namespace privileges;
    loud on every unconfined run naming the config source; posture
    recorded in telemetry. Mid-flight the desk ratified forecast
    drift onto bin/bale_report.py, bin/bale_validate.py,
    bin/bale_open.py, and bin/bale's help strings (telemetry
    write-sites, the open dry-run leg, and three falsified help
    sentences) — the operator admits these per path at apply.
    Landing facts (date, version, ratified calls) true up at the
    next sitting; its notes.md queues for ratification at that
    sitting's open, beside close-001's (§3).
    [2026-09-14: DONE — `2026-09-10-board-75-sandbox-config-off-002`
    (code class), opened 2026-09-10T13:32Z, applied
    2026-09-11T02:45Z, 0.4.25 → 0.4.26 (telemetry: the request
    stamp 0.4.25; the `bin/VERSION reads 0.4.26` assertion PASS).
    Attempt story: first apply `scope-drift-refused` (admission
    flags omitted; the refusal named them) → `held` with
    checkpoint PASS 3/3 and validation.sh HOLD on full discovery
    (board 70's self-containment guard catching two schema
    citations, §6 entry 114) → `retry` `scope-drift-refused` once
    → the retry tarball's apply `applied`. `stamp_matched: true`
    on both graded attempts — no amendment. The applied attempt
    carries `clarification.rounds: 0` against a real exchange
    round: the operator carried the round by copy-paste, `bale
    relay` never ran (§6 entry 115). Five paths admitted beyond
    the forecast, the un-asked `bin/bale_staging.py` string drift
    among them; notes.md ratified in full at the sitting's open,
    approvingly (the §3 close block carries the list). Ruling
    supersession, VERBATIM from the worker's notes, recorded as a
    ruling repair (§5, this date): "this feature supersedes the
    'deliberately no config key' clause of the ratified override
    contract as it applied to the sandbox escape (ADR-0016
    position 2). The clause still holds for every other
    per-invocation flag". The class-decorator inheritance trap the
    fixture extraction caught is §6 entry 113.]

76. **response-manifest echo schema** — opened 2026-09-10 (micro:
    one schema line plus one sentence; from row 71's Proposals):
    the request-side provenance grew `base_files` (board 41); the
    response-side `feedback.mechanical.provenance` echo never
    admitted it, so TARBALL.md §5.2.2's "echoed verbatim" cannot
    be followed literally. Either the echo schema gains
    `base_files` or §5.2.2 says echo-minus-the-stamp. Interim
    reading, ratified at row 71: workers drop `base_files` to
    validate — the echo is verbatim-minus-the-stamp — until this
    lands.
    [2026-09-14: DONE — `2026-09-14-doc-lane-74-76-002` (with row
    74). Desk ruling: the echo schema gains `base_files`
    (verbatim-echo doctrine stands; the doc-side patch would have
    moved the lag). Not required; the lint's schema embed
    refreshed byte-identical; TARBALL.md §5.2.2 gains one clause.
    The session's own echo omitted the key — the one-apply-behind
    bootstrap case, named in its notes (§6 entry 121); from the
    next response on, echoes carry it, and the interim reading
    above is retired. Row 80 pins the key parity.]

77. **vocabulary rename — CANDIDATE** — opened 2026-09-10 (a real
    session, not a tweak: constant rename, guard patterns, doc
    sweep): sweep bale's own "inject/injected/injection"
    vocabulary (the `INJECTED_TOOLS` constant included) toward
    carry/ship terms; the collision with security vocabulary
    primes cautious workers in every foreign project (live
    specimen at row 70; §6 entry 108).
    [2026-09-15: rides the 100 arc — the same sweep shape over the
    same files.]

78. **admission prompts, composed remedies, hook default — DONE**
    2026-09-14, opened and landed in-sitting
    (`2026-09-14-board-78-admission-prompts-001`, code class,
    opened 2026-09-14T20:05Z, applied 2026-09-14T20:38Z at 0.4.27 —
    telemetry: the request stamp 0.4.26 with `bin/VERSION` in the
    change set, and this landing's own request stamps 0.4.27).
    Born from operator friction (VERBATIM): "Every time I get a
    scope drift warning, I end up copying it and pasting to the
    claude session even when I expect it, because it's just faster
    than typing every --allow-out-of-scope file myself." Landed:
    composed remedy lines on the scope-drift and
    sandbox-unavailable refusals (real tarball filename, one flag
    per path, every typed admission flag carried, single physical
    line, zero placeholders); per-path y/N at both refusals in the
    same invocation, default decline,
    non-TTY/`--json`/`--dry-run`/`--no-interact` decline without
    prompting; `overridden_path_sources` (map, `flag|prompt`) and
    `sandbox_off_source` gaining `prompt`; the sandbox self-probe
    moved from post-staging to the seam after every manifest-only
    gate (ordering pinned: drift refuses before the sandbox prompt
    — §6 entry 122); hook confirmation default by layer then by
    bytes — global-layer `[Y/n]`, project and `configured` hooks
    `[y/N]` until one interactive accept of those exact bytes,
    remembered in `<install>/user/hook-acceptances.json` (sha256 →
    script, hook, layer, accepted_at; malformed → warn and decline;
    §7). Ratified as shipped at the desk: unconditional
    single-quoting, normalized path form on the composed line,
    prompt-admitted drift riding the sandbox remedy, all-or-nothing
    at the prompt with the `admission prompt: declined` row, no new
    telemetry outcome. `--accept-checkpoint-change` stays a typed
    flag by desk ruling. Checkpoint PASS on first apply,
    `stamp_matched: true`; `clarification.rounds: 0` against a
    pre-flight asked in chat (§6 entry 115). One-apply-behind: the
    apply that landed this tarball ran the old code; everything
    above is live from the next apply. Verification note (the
    operator's "the global post apply script to have the same
    conditional switch to Y/n as the post pack script" ask, no
    row): covered by the layer default — any global-layer hook is
    `[Y/n]`; the project-layer `post_apply_pass` asked once at the
    s34 apply and is remembered. If a remembered hook still asks
    `[y/N]` at this landing's apply, open a defect row. Proposals
    dispositioned onto rows 80, 81, and 83. Notes.md ratified
    in-sitting.

79. **bundle-delivery doctrine — DONE** 2026-09-14, opened and
    landed in-sitting (`2026-09-14-bundle-delivery-doctrine-003`,
    contract-doc class, bumpless). Born from the operator's report
    (VERBATIM): "I've never had a desk session emit bundles except
    for this project regardless of config." Desk trace:
    `CLAUDE.md` named neither "bundle" nor `bale open`; the only
    planner-facing instruction was one `PLANNER.md` §4 sentence
    gated on a checkpoint-pinning project and on reading §4; the
    practice lived in this document's §7. Ruling (§5, this date):
    the bundle is the delivery form of every planner-authored pack
    in every project; checkpoint member present when the project
    pins a `[validation]` base, explicit null otherwise; the bare
    pack line with `--readme-file` is the fallback only when the
    crafter is unreachable. Landed in `PLANNER.md` §2 (verbatim)
    and §4 (back-pointer), `CLAUDE.md` §3, §4, §11.2 (§11.2's
    sentence gated on checkpoint-configured, ratified as consistent
    with §20). Rider DONE: `2026-09-14-tarball-s34-bundle-clauses-004`
    landed the DOCS.md §9 sanctioned-pair twin in `TARBALL.md` §3.4
    as a new sentence after the pinned one (the pin includes the
    period, §6 entry 120) plus the optional-checkpoint-member
    parenthetical. A rephrase rider for the §4 splice is queued to
    the next `PLANNER.md` touch. Same gap class as row 88 (§6
    entry 118). Both sessions' notes.md ratified in-sitting.

80. **tests-only pin micro** — queued 2026-09-14 (tests/; after 78
    closed — it has): the echo/request provenance key-parity test
    (`request keys ⊆ echo keys` across the two schemas); the
    durable pin on `PLANNER.md` §2's ruling bullet and
    `CLAUDE.md`'s `bale open` mention; the new sanctioned-pair
    extract (CLAUDE §11.2 "delivers that command bundled…" ↔ the
    new §3.4 sentence); `_minimal_record`/`_load_module` moved
    into `tests/harness.py`; `test_apply_operations.py`
    namespace-gated or given the config-off fixture. Sources:
    74-76's, 79's, s34's, and 78's Proposals. Sequenced beside row
    73 session B if forecasts allow (§3 close block).
    [2026-09-14: DONE — `2026-09-14-board-80-tests-only-pins-008`
    (code class, tests-only), opened 2026-09-14T21:43Z beside 73B,
    applied 21:55Z, bumpless at 0.4.27; checkpoint PASS on first
    apply, `stamp_matched: true`, `clarification.rounds: 0`;
    `changes[]` = the seven-file forecast. Two calls ratified: the
    `len(PAIRS) == 5` pin now counts distinct doc-pair
    parentheticals, so the new bundled-delivery key rides the
    already-enumerated CLAUDE.md 11.2 / TARBALL.md 3.4 pair (the
    brief's "no existing pin needs to move" was wrong — §6 entry
    125); the harness took the superset `_load_module` (`bin/` on
    `sys.path`, bare-name registration) and telemetry's
    `_minimal_record` envelope (`StatsToleranceTest` reads
    `closure_mix["unlocked"]`). Coverage move accepted: the
    config-off fixture (`commit_sandbox_off_config()`) on the three
    confined `@slow` cases, so the suite no longer exercises a
    confined `apply.sh` (`test_sandbox_wrapper.py` owns
    confinement). The desk left `bin/` out of the includes to look
    disjoint from 73B; three of seven suites could not run in the
    worker's context and shipped `predicted`, all graded `agree` —
    row 84's third specimen, §6 entry 126. Proposal (`normalize()`
    into `tests/harness.py`) accepted onto the §3 registry.
    Notes.md ratified in-sitting.]

81. **composed remedies for the base-drift and required-check
    refusals** — queued 2026-09-14 (small; bin/):
    `compose_admission_command` already renders both flags;
    `format_base_drift_refusal` and `format_required_check_refusal`
    still close with templates. No prompts (desk ruling; the §3
    watch on those two prompts names its re-trigger). From 78's
    Proposals.
    [2026-09-14: DONE — landed by `2026-09-14-apply-side-81-87-010`
    with row 87's resolver half (attempt story and version on row
    87's bracket). Both renderers take a required `remedy` — no
    template fallback; `TypeError` on omission pinned. On the
    offered flag every typed value is carried, no-effect ones
    included, then the refused values appended; typed base-drift
    paths ride normalized (`scope_path`), required-check names
    verbatim; drift admissions ride as the gate resolved them
    (typed or prompt-admitted), so an admitted path is never
    re-asked; the required-check line carries `--accept-base-drift`
    only as typed, since its gate sits before the base-drift gate.
    No prompt at either gate, pinned under a pty with `y` queued —
    the §3 two-prompts watch NOT fired. Round-trip tests paste the
    composed line back through `apply.search_paths`. The parity
    question (the board-78 drift line drops a no-effect typed path;
    the two new lines keep it) is ruled on row 89: one rule for all
    three lines. Notes.md ratified in-sitting.]

82. **crafter seeds the provenance echo** — queued 2026-09-14
    (tools/): from the request manifest (`--request`),
    `model_identity` empty — mechanizing "echoed verbatim".
    Unblocked now that the echo schema has applied (row 76). From
    74-76's Proposals.

83. **`bale config` view of the hook acceptance store** — queued
    2026-09-14 (small; bin/): list, forget-one. Today "forget" is
    hand-editing the JSON (§7). From 78's Proposals.
    [2026-09-14: DONE —
    `2026-09-14-board-83-hook-store-and-decline-cause-011` (code
    class), opened 2026-09-14T22:21Z beside the apply-side session,
    applied 23:37Z on the second attempt, bumpless under 0.4.29.
    First attempt HELD at 23:30Z on the blind checkpoint (worker
    validation PASS; checkpoint exit 1): three of seven assertions
    grepped `bin/bale` for the rendered decline lines, and the
    first shape assembled them at runtime from constants — the
    terminal output was already correct and pinned (§6 entries 128
    and 130). Retry: the three lines held literally in
    `HOOK_DECLINE_LINES`, keyed by branch, rendered by `run_hook`;
    `bin/bale_config.py` and the suite byte-identical to the held
    response. One relayed exchange round (pre-build, two questions;
    telemetry `clarification.rounds: 2`), preceded by a chat-first
    breach the worker self-reports (§6 entry 127): the desk
    answered `--json` free-text — ship it, one stdout line,
    status-shaped — and the test home as-recommended (extend
    `test_hook_acceptance.py`). Calls ratified: `confirm_yn` keeps
    `bool` beside a new `confirm_yn_decision` returning a frozen
    `ConfirmDecision` whose `.decline_branch` names one of three
    `CONFIRM_BRANCH_*`; EOF and Enter split by the `stdin_closed`
    flag, not the text; `--forget` prompt-free, printing the
    removed entry and the survivors; prefix rules (case-insensitive
    hex, 1–64 chars, no minimum, non-hex refuses as a typo,
    ambiguity names every match, both via `fail()`); listing
    oldest-first by `accepted_at`; malformed entries displayed and
    forgettable, a malformed file keeping the read path's posture;
    `--json` status-shaped (`outcome`, `version`, `store`, `exists`,
    `entries`, `forgotten`) with the renderer
    `format_config_hooks_json` in `bale_config.py` for now (row 89
    moves it); the atomic writer factored to
    `write_hook_acceptances`; no git repo required. Proposals
    dispositioned onto rows 89, 90, and 91. Notes.md ratified
    in-sitting.]

84. **pack warns when an included test imports a repo test module
    outside the include set** — queued 2026-09-14 (bin/): promoted
    from evidence 112's candidate by two live specimens (73A, and
    this desk's own violation — §6 entry 116).
    [2026-09-14: third specimen — row 80. The desk left `bin/` out
    of the includes to make the pack look disjoint from 73B; three
    of seven suites (`test_telemetry_extensions`,
    `test_admission_prompts`, `test_apply_operations`) could not run
    in the worker's context and shipped `predicted`. Same shape as
    73A's and the board-75 retry's, with one difference of record:
    the worker named the gap in its notes ("rightly — it's in row
    73B's forecast") and its telemetry `includes_missing` reads
    `[]`, so the ledger does not carry this one. Disjointness is a
    forecast property; includes gate nothing (§6 entry 126; the doc
    lane landed the sentence in `PLANNER.md` §6).]
    Fourth specimen 2026-09-15: board 94's `includes_missing` named
    the `HandoffFixture` consumer suites (`test_handoff_forecast`,
    `test_handoff_registry_gate`, `test_handoff_checkpoint_gates`,
    `test_handoff_happy`) — the desk chased test imports but not
    fixture consumers, so the `peeked_sid` edit shipped with one test
    exercising it (§7 include rule, §6 entry 133).

85. **exchange-carried-outside-relay self-report** — queued
    2026-09-14 (schema + docs + lint): a worker-side field in the
    response manifest recording rounds carried by paste, so
    telemetry stops reading a real round as zero (VERBATIM,
    operator: "There should be a way to note that when the worker
    packs the final tarball"). Three specimens this sitting (§6
    entry 115). The mechanical half of the §3 exchange-adoption
    watch.

86. **stats drill-down row for handoff-origin sessions** — queued
    2026-09-14 (small; bin/bale_stats): `command == "handoff"` at
    persist. From 73A's Proposals; the corpus in this sitting's
    context had zero such sessions.

87. **response tarball naming standardization + row 51 resolver
    check** — queued 2026-09-14 (tools/ + bin/ + docs). Operator,
    VERBATIM: "I'd like to standardize the response tarball naming
    convention. Sometimes I just get "response-004.tar.gz" and
    sometimes I get the convention
    "response-2026-09-14-tarball-s34-bundle-clauses-004.tar.gz".
    I'd prefer the former for transparency purposes, but I'd like
    to move up the board item that makes a bare "bale apply"
    search through the search paths and see the most recent tarball
    to apply and a y/N wizard option can confirm it." Corrected by
    the operator at the desk, VERBATIM: "you're right, I meant
    "latter" not former." So the standard is the sid-bearing form,
    `response-<sid>.tar.gz`. Desk notes: row 51 is DONE and already
    does the search-and-y/N; `TARBALL.md` §10.1 step 11 says
    `response-NNN.tar.gz` and is the first thing the row changes;
    then the crafter's tar step and 51's resolver align on the
    sid-bearing form.
    [2026-09-14: DONE, both halves. Naming half by
    `2026-09-14-doc-lane-87-88-009` (with row 88; attempt story on
    88's bracket): `TARBALL.md` §10.1 step 11 spells
    `response-<sid>.tar.gz` with its directory-stays-`NNN` note,
    and the request-side line mirrors it (edit 5). Resolver half by
    `2026-09-14-apply-side-81-87-010` (with row 81; code class),
    opened 2026-09-14T22:21Z; first attempt HELD at 22:52Z on its
    own `validation.sh` — a `bash -n apply.sh validation.sh` inside
    staging, where neither exists (bale runs them from the response
    directory and syntax-checks both itself); the rehearsal had
    copied them in (§6 entry 130); the blind checkpoint PASSed both
    attempts, `stamp_matched: true`, the change set byte-identical
    (`corrects` names the first, held at commit b1dc247) — retry
    applied 22:55Z at 0.4.29 (`bin/VERSION` in the change set; this
    close's request stamps 0.4.29), `clarification.rounds: 0`,
    `changes[]` = forecast. `resolve_bare_apply_tarball` now treats
    the open set as the match surface: a candidate is any tarball
    whose `responds_to` names any open sid (cwd, then each
    `apply.search_paths` directory, content-discriminated as board
    51 built it); newest by `st_mtime_ns` wins; an exact tie
    refuses and the listing names each path's session; the echo
    names the resolved session and the open set; the multi-open
    refusal text is gone. The read-only master is not special-cased
    — a response answering it resolves, echoes, and meets the drift
    gate as the argumented form would. Desk-note correction: the
    "naming variance defeats matching" clause is struck above — the
    resolver is content-based and naming never defeated it; the
    multi-open refusal was the whole defect (the
    master's own read-only session counts as open — §6 entry 123).
    One-apply-behind: this tarball was applied by name; bare apply
    works beside an open master from the next apply. The five
    backslash-escaped quotes in the VERBATIM text above are struck
    at this close (a brief's rendering artifact, not keystrokes).
    Doc residue on row 90. Notes.md ratified in-sitting.]

88. **disjoint packing as standing practice in the global docs** —
    queued 2026-09-14 (contract-doc: PLANNER.md + CLAUDE.md).
    Operator, VERBATIM: "I want to double check and make sure that
    disjoint packing is clearly outlined as an option in the global
    docs. I've had some sessions really lean into disjoint packing
    and some ignore it entirely so I'm worried the docs are
    inconsistent like with the "bale open" issue." Desk trace:
    `CLAUDE.md` one clause (§11.2), `PLANNER.md` core one bullet
    conditioned on splits, `DOCS.md` none; `TARBALL.md` §3.4's
    scope-planning paragraph is the fullest and is read only at
    pack authoring; `PLANNER.md` §13 is past the core. The practice
    — a sitting runs forecast-disjoint sessions beside each other
    by default and serializes only on a real dependency — is this
    document's alone. Fix: `PLANNER.md` §6 gains it as sitting
    practice, §2's bullet drops its conditional, `CLAUDE.md` §4's
    "deciding what's next" row points at it. Same gap class as row
    79 (§6 entry 118).
    [2026-09-14: DONE — `2026-09-14-doc-lane-87-88-009`
    (contract-doc class; with row 87's naming half), opened
    2026-09-14T22:06Z beside 73B, applied 22:14Z, bumpless at
    0.4.28; checkpoint PASS on first apply, `stamp_matched: true`,
    `clarification.rounds: 0`; `changes[]` = the three-file
    forecast (`docs/CLAUDE.md`, `docs/PLANNER.md`,
    `docs/TARBALL.md`); the three doc-pin suites untouched and
    green. Calls ratified: the `PLANNER.md` §6 bullet placed
    second, after "One master per sitting"; its lead "Disjoint
    sessions run beside each other."; the two-sentence
    live-traffic anecdote stays in the core, self-standing; §2's
    rewrite names both origins ("split-born or desk-born alike")
    with a pointer at §6; `CLAUDE.md` §4's row restates the
    practice in one clause before the pointer. The practice is a
    §5 contract of this date (cited there, not re-quoted).
    Proposal (`TARBALL.md` §1's "Artifact directories" bullet gains
    the filename convention) rides row 90. The backslash-escaped
    quote in the VERBATIM text above is struck at this close.
    Notes.md ratified in-sitting.]

89. **Decline cause on every prompt, one composed-line rule, and
    the JSON renderer's home** — queued 2026-09-14 (small; bin/):
    three riders from 83's and the apply-side's Proposals. Switch
    the other `confirm_yn` callers — the bare-apply confirmation,
    drift admission, the supersession y/N, the read-only sweep
    (`bin/bale_apply.py` ×3, `bin/bale_pack.py` ×2) — to
    `confirm_yn_decision` with a line per `.decline_branch`. Adopt
    the carry-every-typed-value rule on the board-78 drift line
    (desk ruled: one rule for all three composed lines — a dropped
    flag re-sends the operator through a cleared gate). Move
    `format_config_hooks_json` beside `format_status_json`.
    **Why:** the operator's "Enter did nothing" report is not
    hook-specific — every prompt has the same three silent
    branches; the drift line drops a no-effect typed path where the
    two row-81 lines keep it; the renderers are one family with one
    stability rule, and `bale_config` holds one only because
    `bale_report` was a sibling's forecast this sitting. **Scope
    hints:** `bin/bale_apply.py`, `bin/bale_pack.py`,
    `bin/bale_report.py`, `bin/bale_config.py`; small. Sequenced
    first, beside row 90 (§3 close block).
    [2026-09-15: DONE at `2026-09-15-board-89-decline-cause-006`,
    0.4.31. Five prompts switched to `confirm_yn_decision` with
    literal three-line tables per prompt and one renderer
    (`bale_report.format_decline_line`); the drift line carries every
    typed value (`[*allow_norm, *drift_paths]`);
    `format_config_hooks_json` moved beside `format_status_json`; the
    `persist_pack_session` docstring rider taken. Calls ratified: the
    sweep's unreachable empty-answer line kept for parity; the piped
    supersession path's cause-less line; tables keyed by string
    literals with an `ast` parity test against `bin/bale`'s constants;
    `ValueError` on renderer misuse; the wizard's two `confirm_yn`
    uses left. Seven `tests/` paths admitted out-of-forecast (§6 entry
    140). Its `<path>`-remedy proposal folded into 101; its BALE.md
    sentence rides 99b; its handoff-gate finding was row 95, landed by
    101.]

90. **Doc residue of rows 83 and 87** — queued 2026-09-14 (doc lane
    with a one-string code rider): `BALE.md`'s apply section still
    describes bare apply as keyed on the single open session and
    refusing under multi-open (board 51's queued pair-close rider
    line, now superseded by the §5 ruling) and its hook section
    still describes a file to hand-edit (the store is operable:
    `bale config hooks`, `--forget`); the `bin/bale` apply parser
    description still says "the single open session";
    `TARBALL.md` §1's "Artifact directories" bullet gains the
    filename convention beside the directory one. **Why:** the doc
    lane landed the naming half and the apply-side session changed
    the behavior half; a worker reading only the core meets the
    filename rule only in the triggered §10 checklist. **Scope
    hints:** `BALE.md`, `bin/bale` (one string), `docs/TARBALL.md`;
    ships the doc-pin suites per the include-authoring rules. From
    the apply-side's, 83's, and the doc lane's Proposals. Sequenced
    beside row 89 (§3 close block).
    [2026-09-15: DONE at `2026-09-15-board-90-doc-residue-005`,
    bumpless. The §8 bare-form paragraph rewritten around the ruling
    sentence verbatim; §5.4 names `bale config hooks` and `--forget`;
    the apply parser description brought to the row-87 contract;
    TARBALL.md §1 names `response-<sid>.tar.gz`. Calls ratified: the
    echo's rendering quoted in §8; the tie refusal noting each path's
    session; "modification time" in help text with `st_mtime_ns` in
    BALE.md; the closing why-sentence kept. Registry: §7/§7.2
    includes-as-scope closed on the worker's read. Proposals: the
    positional's two words landed at 101; the `bale config hooks`
    command-table row rides 99b.]

91. **Exchange-record schema parity** — queued 2026-09-14 (schemas/
    + tests/): admit in `exchange-record.schema.json` the optional
    `origin` question-row key that `response-manifest.schema.json`
    admits (or strip it in the crafter's clarification
    normalizer). **Why:** found by 73B, confirmed by 83 — a
    clarification manifest that fills `origin` cannot
    `--emit-block`, so both workers dropped the key to keep one
    manifest feeding both couriers; the two schemas should admit
    the same row. **Scope hints:**
    `schemas/exchange-record.schema.json`, crafter/relay parity
    tests; one line plus a pin; a forecast touching `schemas/`
    ships the self-containment guard. From 73B's and 83's
    Proposals. Sequenced after 89/90 (§3 close block).
    Grown 2026-09-15: board 94 re-found the gap from the other side —
    the response schema admits the v0.4.24 `origin` key, the
    exchange-record schema and the crafter's `--emit-block` embedded
    copy do not, so an `origin`-tagged clarification is tarball-valid
    and paste-block-refused; board 94's round-1 questions shipped
    without the key. Scope grows by the crafter's embedded copy and
    `test_schema_embeds` extended to the pair. Sequenced before row
    96, which makes the paste block the light tier's courier.

92. **`walk_for_pack --verbose` names untracked drops** — queued
    2026-09-14 (bin/). From 73B's Proposals, VERBATIM: "**What:** in
    `walk_for_pack --verbose`, print a `verbose: drop <path> (not
    tracked)` line for each include entry that matched no `git
    ls-files` path. **Why:** it is the one drop reason the rider
    cannot surface, and for a handoff it is the common one (a typo
    in a bailing worker's reading plan). **Scope hints:**
    `bin/bale_pack.py`, the walk; pack's `--verbose` suites."
    Stands until pack's `--verbose` brings it forward (§3 close
    block).

93. **Record a forecast's declaration status beside `scope.json`**
    — queued 2026-09-14 (bin/; gated). From 73B's Proposals,
    VERBATIM: "**What:** record the forecast's declaration status
    beside `scope.json` (or in the session's provenance record) so
    a handoff can inherit *declared-ness* as well as the value.
    **Why:** removes the residue named under judgment calls without
    weakening the no-silent-renewal rule. **Scope hints:**
    `persist_pack_session`, the registry readers, both
    request-building paths; after the ledger shows the case
    occurring." The residue case, from 73B's ratified call (an
    inherited forecast is declared): a parent whose
    include-set-default forecast covered the oracle was admitted at
    pack undeclared, and its plan-less handoff refuses at the
    blindness gate. Gated on the ledger showing it; stands until
    then (§3 close block).

94. **Clock discipline + the `context/` prefix** — DONE. Opened,
    spawned, and applied 2026-09-15 at the continue-plan-001 sitting
    (`2026-09-15-board-94-clock-discipline-002`, 0.4.30, one
    clarification round). **What landed:** `utc_today()` in
    `bin/bale`, `next_session_id`/`peek_session_id` defaulting to it;
    both request-building paths (`cmd_pack`, `bale handoff`;
    `bale open` replays through `cmd_pack`) read one UTC instant and
    pass it to allocation and the stamp, so
    `sid[:10] == packed_at[:10]` holds by construction;
    `provenance.packed_at` stamped unconditionally, admitted never
    required on the request schema, admitted on the response echo, the
    lint's embedded schema refreshed, no telemetry schema edit
    (`attempts[].provenance` is open); the opener carries
    `Packed at <packed_at> (UTC).` and the VERBATIM clock sentence as
    two emitted lines between identity and goal; TARBALL.md §1 names
    the UTC day and carries the clock sentence, §3.1 carries the
    mapping sentence, `context_included` loses "typically"; the lint
    gains a non-gating warning tier (`warnings[]`, `[WARN]`, invisible
    to `ok`, the exit code, and the mechanical block) and two checks —
    `context-prefix` (a `changes[]` path under `context/` is a
    finding; a `docs_read` token under it a warning) and
    `dated-artifacts` (content-keyed on a `- **Date:** YYYY-MM-DD`
    header in the first 20 lines, path-agnostic; created: date equals
    the sid's date or a finding; modified: only a dated line later
    than the sid's date, the header being byte-stable under DOCS.md
    §5's sanctioned shapes); tests predicting sids moved to the UTC
    date; `test_clock_discipline.py` (5) and
    `test_lint_clock_and_prefix.py` (12). **Rulings, round 2:**
    modified-ADR dates as above, with the earlier-but-re-dated case
    deliberately left to the crafter's ADR doc-assertion (the lint has
    no base bytes); content-keyed recognition; the bundle-stem check
    struck — a bundle never rides in a response (TARBALL.md §3.4), the
    brief over-reached (§6 entry 132). **Validation facts of record:**
    two `test_checkpoint_provenance.py` handoff-gate tests fail on the
    unmodified shipped bytes (row 95); `includes_missing` named the
    `HandoffFixture` consumer suites (row 84, §7); the
    self-containment guard caught "board 94" citations in injected
    surfaces, removed. Ratified in-sitting; the two desk brief defects
    recorded at §6 entry 132.

95. **Handoff-gate tests fail on shipped bytes** — queued 2026-09-15
    (tests/, possibly bin/bale_pack.py). From board 94's validation
    facts, VERBATIM: "`tests/test_checkpoint_provenance.py`
    `HandoffBlindnessGateTest.test_handoff_empty_plan_whole_tree_refuses`
    and `test_handoff_refuses_covering_reading_plan` fail on the
    unmodified shipped bytes: the handoff's include-set refusal ("pack
    includes name the blind checkpoint explicitly") fires before the
    forecast refusal wording the tests assert
    (`SCOPE_REFUSAL_PHRASE`), and the empty-plan case now succeeds
    where the test expects a refusal." **Why:** a latent regression no
    prior validation caught — the suite did not ship with the sessions
    that touched the gate (§6 entry 126's class). **Scope hints:**
    read 73B's telemetry for the suite's status at its landing first;
    if the include-set-before-forecast order is intended (73B's
    blindness gate), the tests are stale and this is tests-only; if
    not, the order is the defect and the row follows 89 for
    `bin/bale_pack.py`. Desk guess, labelled: the order is intended.
    [2026-09-15: DONE by `2026-09-15-board-101-bare-apply-cap-007` —
    the desk guess held (the read-includes order is 73b's intended
    routing) with one addition: the read-side refusal's remedies still
    spoke of `--write`, so the remedy was split by which rule fired in
    `bin/bale_report.py`; the empty-plan case pins the
    inherited-forecast contract. Dispatched to 101 as a rider before
    the desk recognized this row held it (§6 entry 137).]

96. **Terminal shapes: the light question tier, and the chat
    invitations struck** — queued 2026-09-15 (docs/CLAUDE.md,
    docs/TARBALL.md, docs/PLANNER.md, bin/bale_pack.py one line,
    tools/craft_response.py, schemas/ additive; after 91). **What:**
    the §5 ruling of 2026-09-15 lands. Strike or rewrite the four
    sanctioned chat invitations — TARBALL.md §3.3 item 1 ("small
    enough to resolve inline", which contradicts §5.9.1's not-size
    test), §5.9.1's "a question in chat as conversation", CLAUDE.md
    §3's one-sentence mode ask (dead since 0.4.16: a bale-emitted
    opener with a sid is tarball mode) and §9's "brief paused question
    in chat"; the opener's closing line becomes the shape rule. New
    TARBALL.md §5.10, the light question block: admitted when the set
    holds at most three questions, none multi-tiered (no options that
    need explaining, no `why_blocked` that needs a paragraph), each
    with a default the packer can ratify by a word or an answer that
    fits on one line — the worker counts, never judges; the block is
    sentinel-bracketed, human-readable in the apply walkthrough's
    `[n] question / while doing / would assume / why blocked` render,
    and ends with the packer's three replies every time: answer
    inline, "as assumed" to ratify every default, "formal" to have the
    same questions returned as a clarification. Its trail is the
    eventual response: notes.md names each question and its answer,
    and an additive `feedback.self_reported` count makes the tier
    visible to stats; no thread record, no telemetry attempt. A pack
    flag on the `expects_probe` pattern lets the packer force formal
    for a session (a harness sets it); the mechanical rule is the
    default and the flag overrides one way only. PLANNER.md §15 gains
    the packer's side. The crafter's `--emit-block` grows the human
    render beside the JSON one so one question row feeds either
    courier, and its `--bundle` docstring names the stem's clock
    (board 94's proposal: the UTC date, i.e. the authoring session's
    own sid date). **Why:** two chat-first breaches on the board-94
    spawn alone; a worker choosing between "the docs say not size" and
    the opener's "ask me if anything is unclear" picks the opener (§6
    entry 134). The harness property — every ending parses — falls out
    of the same rule. **Scope hints:** a contract-doc row with two
    code touches; the four doc-pin suites and the self-containment
    guard ship; sequenced after 91 because an `origin`-tagged question
    is paste-block-refused until 91 lands.

97. **Where ADRs live: one spelling** — queued 2026-09-15 (docs/,
    after 96). From board 94's Proposals, VERBATIM: "Three injected
    docs disagree on where ADRs live: DOCS.md §2's table and §5 say
    `claude/context/adr/NNNN-*.md`; CLAUDE.md's INDEX table says
    `adr/NNNN-*.md`; TARBALL.md §3.1's `context/` example shows
    `decisions/`. The lint's content-keyed recognizer sidesteps it,
    but the desk should queue a doc row so one spelling wins." **Scope
    hints:** the three sites; the doc-pin suites ship; ratify the
    spelling at the desk before dispatch (the desk's read: DOCS.md's,
    since it is the doc that defines the ADR).

98. **Stats read-side `context/` normalization** — queued 2026-09-15
    (bin/bale_stats.py; low). From board 94's Proposals, VERBATIM:
    "Strip a leading `context/` from `docs_read` tokens at read time
    in `bale_stats.py` so the three historical records aggregate with
    the repo spelling, without editing them." Additive doctrine: no
    retroactive record edits. Stands until a stats session brings it
    forward.

99. **Outward-facing doc refresh** — queued 2026-09-15 (docs; two
    sessions on one seam). The root `README.md` is dated 2026-06-03
    and describes a different tool: "four docs in docs/" (five since
    PLANNER.md), two `bin/` modules (twelve), a daily-use section with
    no `open`, `relay`, `handoff`, `stats`, `rollback`,
    `config hooks`, checkpoints, bundles, or bare apply — and it ships
    in the release tarball, so a fresh install reads it first.
    Operator's scope ruling at the sitting: README, the `--help`
    epilogs and `config init` wizard text, and a BALE.md true-up.
    **99a**: `README.md` plus the help and wizard strings (`bin/bale`,
    `bin/bale_config.py`); doc lane with string riders. **99b**: the
    BALE.md true-up, its own session (the doc is ~260 KB), riding the
    100 arc's doc-sweep wave, and carrying the two registry sentences
    that name it. `tests/test_readme_identity.py` pins `--readme-file`
    behavior, not README content.

100. **Model-agnostic bale — ARC** — queued 2026-09-15. Operator's
    goal, VERBATIM: "I want to abstract everything away from claude or
    anthropic specifically so that I can cleanly insert a different
    model." The coupling has four layers with different costs: (1)
    branding prose — "Claude" as the worker's name in the five globals
    (~250 hits), `bin/bale` docstrings, report next-step lines,
    README; (2) the `--expects-probe claude-decides` enum, pinned in
    two schemas and every telemetry record; (3) the `CLAUDE.md` file
    name, one of `GLOBAL_DOCS` and the name the pack opener tells the
    worker to read first; (4) the `claude/` project directory —
    `[validation] base`, `[archive]`, `base/"claude"/"telemetry"`
    hardcoded in stats, ADR paths, every existing telemetry record.
    Also: CLAUDE.md §11 carries claude.ai-surface facts
    (auto-compaction, "press Continue", tool-use limits) that belong
    in a surface-notes subsection. Shape: a read-only design sitting
    first (the worker noun; how deep — layers 1–2, +3, +4, decided
    there by operator ruling; compatibility — enum aliases, a config
    key for the directory defaulting to the old spelling), then a
    wave: doc sweep + guard patterns, code strings + help text, the
    compatibility layer if 3–4 are in. Row 77 (inject→carry) rides the
    arc; row 97's ADR spelling is ratified relative to whatever the
    directory is called. Row 103's findings feed the doc sweep, so 103
    runs before the arc.

101. **Bare `bale apply` bounded resolution — DONE 2026-09-15** at
    `2026-09-15-board-101-bare-apply-cap-007`, 0.4.32 (re-attempt; the
    first attempt HELD on the worker's own validation needle, change
    set byte-identical). The three rules landed (§5): only
    `response-*.tar.gz` is ever opened; the two newest by
    `st_mtime_ns` are examined, one cutoff so a tie at either rank is
    visible in full; the no-candidate refusal names each examined file
    with its reason and counts the unexamined older ones. Also landed:
    the decline's quoted alternative line when the other examined file
    answers an open session (board 89's `<path>` proposal, folded
    here); the apply parser description and the positional's "an open
    session"; both row-95 handoff-gate cases rewritten to the ratified
    contracts (read-includes phrase with a read-side remedy; the empty
    plan inherits the parent's forecast) with the remedy split in
    `bin/bale_report.py` (admitted drift). Calls ratified: un-named
    files uncounted in the refusal; `BARE_APPLY_EXAMINE_CAP = 2` as a
    module constant; "re-bail" as the read-side remedy's verb; the
    diagnosis kept byte-shared across callers.

102. **Explicit-name tarball resolution** — queued 2026-09-15 (small;
    `bin/bale_apply.py`, retry's argument path, BALE.md a sentence). A
    tarball argument with no directory component that does not exist
    relative to cwd is looked up in `apply.search_paths`, for
    `apply <name>` and `retry <name>` alike — a lookup of the name
    given, never the bare search (the operator is content that `retry`
    does not bare-search). With no exact match, refuse and list
    near-names — `response-<sid>*.tar.gz`, the browser's `(1)`
    variants — as complete quoted lines. Carries the `shlex.quote`
    registry entry for the non-TTY refusal path. Motivation, from the
    operator: typing the whole path is annoying, and a second download
    of the same name gets `(1)` appended, so the quotes are
    load-bearing.

103. **Cross-model capability probe** — queued 2026-09-15 (a design
    sitting, then one pack run N ways). Operator's goal, VERBATIM:
    "queue a session where I run the same test pack (intentionally
    tasked to extract model capabilities) with both fable 5 and sonnet
    5 (or also an open weight model) so that we can compare and get a
    deeper understanding of what lesser models miss, and determine if
    we need to edit or improve any documentation or procedures to
    allow weaker models to not trip up as much." Shape: one request
    built to exercise the protocol's tripwires (reading path, verbatim
    landings, blind-checkpoint posture, both-branch validation
    rehearsal, notes.md shape, clarification-versus-detail-call
    judgment, drift enumeration, the crafter, chat-versus-exchange),
    packed once per model with identical argv so each gets its own
    session and otherwise identical bytes; each response through its
    own session's gate (`bale validate`, then apply or HOLD), graded
    by the same blind checkpoint; `cost.model_tier` per attempt is the
    telemetry home. Output: a findings report and doc/procedure deltas
    for weaker models. Runs after 99a and before the 100 arc's design
    sitting so the findings feed the sweep. The desk writes the probe
    request at the design sitting.

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
board 10's queue entry has since condensed to a pointer (the v5
regeneration, `2026-08-18-master-v5-regeneration-001`); the working
copies live in v4, in git):

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
  home: PLANNER.md §5 (landed at `2026-08-18-board-46-doc-deltas-006`);
  this entry is the ratification record and pointer.

New, ratified 2026-08-16 (the 008 desk, dispositions ratified wholesale;
the rider `2026-08-16-multi-discussion-008` is the authored record —
recorded here for re-litigation protection):

- **Telemetry disposal doctrine — telemetry earns its place.** No field
  without a named consumer: a field isn't real until a consumer queries
  it, and every new field names its query at birth (the policy rows
  landed at DOCS.md, `2026-08-18-board-46-doc-deltas-006`; the schema
  descriptions already name consumers de facto). Field retirement: a
  field that stays null across N sessions with no consumer stops being
  stamped and keeps tolerating on read — the legacy-tolerance pattern.
  Completeness over breadth reaffirmed (evidence 38): a narrow field
  stamped on every exit beats a rich one stamped only on applies. The
  pile risk is attention, not disk; the fix is making reading the
  default at moments the architect is already sitting, not collecting
  less.
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
  read side). Doctrinal prose home: PLANNER.md §6 (landed at
  `2026-08-18-board-46-doc-deltas-006`); this entry is the ratification
  record and pointer.
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

New, ratified 2026-08-18 (the smoothing sitting):

- **The paste-block surface.** Refines the 2026-07-27 typed-surface
  contract: the architect composes no commands — every command
  arrives as a paste-ready block emitted by the surface that knows
  it (bale's banners emit terminal successors; the authoring desk
  emits pack and open lines beside their artifacts), and the
  chat-side opener arrives the same way (row 52: pack output emits
  the session preamble as a copy block). Bare verbs survive as the
  content of emitted blocks, never as a memorization surface. The
  cold-start pack — the one command with no author but the human —
  dissolves into the same shape once row 49 lands: the desk
  authors the bundle, the human pastes the emitted line. Residual
  composed surface after rows 49/51/52 land: the first-ever chat
  opener of a brand-new install, and nothing else.

New, ratified 2026-08-25 (the continue-plan-003 sitting):

- **CRLF ingest normalization.** At every transport-facing text
  ingest, replace CRLF with LF and nothing else; published and echoed
  hashes are computed over the normalized bytes; the committed oracle
  is LF, and everything downstream of a commit stays byte-exact. The
  normalization sits before the empty-check, commit, echo, and stamp
  at `--checkpoint-file`; already-tolerant surfaces (text-mode brief
  reads, the TOML config spec, splitlines on baleignore) are pinned,
  not re-plumbed. (Board 50.)
- **The session opener.** Pack's report ends with the sid+goal copy
  block, framed by scissor lines on all three pack shapes; bale owns
  and versions the paragraph. `--json` keeps exactly one JSON line on
  stdout with the opener on stderr — the JSON key was refused past
  the `bale_report.py` hot-file ruling, not smuggled through it. The
  scissor lines are test literals. (Board 52.)
- **Bare `bale apply` resolution.** The full contract as recorded in
  the §3 entry and the board-51 row bracket: newest by `st_mtime_ns`
  with no secondary tie-break (exact ties refuse, naming every tied
  path); content-based candidacy (a `response-NNN/manifest.json`
  member with non-empty `responds_to`; request tarballs never
  candidates); identity echo before a decline-default y/N;
  interactive decline exits 1; `--no-interact` contradicts the bare
  form up front; inspection flags refuse and `--dry-run` composes.
  (Board 51.)
- **`BALE_TEST_SLOW`.** The slow-test gate is harness-level, homed in
  `tests/harness.py`; only the literal `1` opens it. `validate.sh`
  surfaces gated status through an `[INFO]` marker class — status
  lines that are not checks, moving no counters. Gate criterion:
  cases ≥0.7s gate, with the fastest-per-class representative kept in
  the default run. (Board 52's rider.)

New, ratified 2026-08-25 (the harness spec-intake sitting,
`2026-08-25-harness-discussion-005`, read-only; decision texts of
record live in the harness repo's `harness-seed.md`, D1–D24 — the
seed doc is the verbatim home for harness-side decisions, this
section for bale-side contract force):

- **The harness project is born; the seed doc is its spec home.**
  Separate repo (seed D1); bale-version pinning with arc-boundary
  upgrades (D2); narrowest consumption surface (D3) with a
  harness-side consumption manifest (D4); board 9 Level 1 as the
  cross-repo procedure (D6). Bale-side force: bale commits to
  nothing new here — the pin and manifest are harness-side; bale's
  only obligation is the changelog record family (next entry).
- **The changelog record family** (seed D5): loose schema per
  existing record conventions, same-response discipline — the
  session that changes a machine-readable surface writes the entry
  — and a validator row that makes omission loud. Primarily for
  bale's own version ladder; the harness is its first external
  consumer. Implementation queued as board 56, with the
  `aborted`-class closure reason queued beside it as board 57.
- **Autonomy sequencing reaffirmed** (seed D7): board 45 gates
  harness *autonomy*, not harness existence or supervised rungs.
  Recorded to prevent the board ordering being read as gating the
  build.

New, ratified 2026-08-26 (the board-53 sitting):

- **The amendment accounting contract.** `bale amend-checkpoint`
  verifies a delivered oracle against a desk-published sha256
  (mandatory, full 64 hex), LF-normalizes at read, and accounts
  HEAD's bytes at the session's resolved checkpoint path against
  the session's pack-time `provenance.checkpoint` stamp before
  replacing anything: committed == delivered is the idempotent
  re-run (no commit, successor still emitted, decided before the
  stamp is read); committed == stamp is the amendment proper
  (commit, loudly naming both hashes); committed matching neither
  refuses loudly naming committed vs stamped, with a
  per-invocation accept flag (`--accept-unaccounted-oracle`) as
  the named successor — on accept, proceed FORCE-logged naming all
  three hashes. A stampless request (key absent, or the
  explicit-null stamp) degrades to published-hash deliberateness
  alone, loudly — the provenance gate's own verify-nothing
  precedent. Uncommitted differing bytes at the resolved path
  refuse on their own rung: local edits are never clobbered. The
  verb mechanizes transport, never deliberateness: the retry-side
  provenance gate, the per-invocation accept there, and
  `stamp_matched: false` as the truthful record are all unchanged.
  (Board 53; the clarification round's durable record is the
  session's archived notes.)

New, ratified 2026-08-31 (the meta-specific-003 sitting, read-only):

- **Global docs reference no project-specific material — including bale-src's own.**
  No evidence-ledger citations, no board-row citations, no
  telemetry references, no project doc names in any of the five
  injected globals. A lesson a global doc carries is stated
  self-standingly (resolved or inlined); provenance stays
  project-side. Overturns PLANNER.md §8's "cited, not carried"
  sanction, which the purge session (board 61) rewrites rather
  than quietly contradicts.

New, ratified 2026-08-31 (the fold-in/purge review, at the fold-in
(005) and purge (004) responses' review):

- **The fold-in's six-row superset reading is ratified; the brief's five-row header was the defect.**
  The desk amended the brief mid-authoring to add the sixth row
  after the checkpoint rehearsal and left the header's count
  stale; the worker flagged the mismatch in chat before building
  and landed the superset — the only reading that could fail
  neither the land-every-item constraint nor the checkpoint pins.
  No correction shipped or needed. (Specimen: §6 entry 92.)
- **bin/ paths are sanctioned in injected surfaces — they resolve wherever the install exists.**
  BALE.md and MASTER.md exist only in the bale-src checkout, so
  citing them from an injected surface dangles in every other
  project; bin/ ships with the install, so a bin/bale_pack.py or
  bin/bale_validate.py reference is a tool-side fact resolving for
  every project — the same species as naming a bale verb. No deny
  entry is added to the self-containment guard; the sanction's
  durable code-side home is a rationale line in the guard's
  docstring, queued (§3 fold-in registry) to ride the next session
  touching tests/test_global_doc_selfcontainment.py rather than
  warranting its own touch.

New, ratified 2026-08-31 (the continue-plan-012 sitting):

- **Master-authored forecasts stop pre-seeding the packaging trio; the release-surface include group carries the read side, and a needed packaging change travels ship-enumerate-admit.**
  The calibration ruling closing the §3 forecast-precision watch at
  its fourth accrual — all four packer-side imprecision on
  master-authored packs, the last two the packaging trio itself.
  The ruling is bale-src authoring practice; it does not touch the
  global docs. (Accruals and closure: the §3 watch entry.)

New, ratified 2026-08-31 (the continue-plan-012 sitting's wave-3
close):

- **A response carrying anything ratifiable writes notes.md, however short; the archive keeps only notes.**
  TARBALL.md §5.4 already says it; the ruling restates it as
  bale-src practice of record after 023 tucked ratifiable material
  into its manifest, whose bytes the archive drops — established
  by 022's probe (the 015 archive holds notes.md only).
- **023's durable record, probe-rescued.** Beside the ruling, the
  facts the archive would otherwise drop:
  `2026-08-31-tarball-reemit-mention-023` landed the TARBALL.md
  §5.9.2 sentence "Invoked without the file argument, the same
  verb re-emits the paste block for the thread's latest recorded
  round — byte-identical to the original emission — and records
  nothing" and the §5.9.4 recovery-path sentence, and its
  predicted guard-suite claim resolved to verdict skip at staging
  (flagged in the §3 wave-3 block; self-heals at the next
  full-suite run).

New, ratified 2026-08-31 (the continue-plan sitting, session 026 —
the text of record, verbatim, disposing the §3 ruling-queue item):

- **Bailout-vs-compaction calibration ruling (2026-08-31 sitting, session 026): on the corpus of record (zero bailout outcomes in 181 records; §11.6 recovery exercised properly on all 15 compaction disclosures; 13 tight budget-pressure self-reports), §11.6 recovery is accepted as the de facto primary defense on auto-compacting surfaces; the pre-flight half of the bail machinery stands as-is.**
  **Board 37 reshapes accordingly: part 1 shrinks to what survives the ruling; parts 2–3 (crafter --bailout emission, the bail/compaction telemetry marker) are the surviving work; the single-window-premise rider paragraph still lands in PLANNER.md at 37's session.**
  The ruling touches no global doc by itself — CLAUDE.md §11's
  emphasis shift, if any wording follows, is board 37's session's
  cargo. Queue disposition annotated in §3; the reshape bracketed
  on row 37.

New, ratified 2026-09-14 (the continue-plan-001 sitting,
2026-09-10→14; each a ruling of record with one home):

- **The bundle is the delivery form of every planner-authored pack, in every project; the checkpoint member is present when the project pins a `[validation]` base and an explicit null otherwise; the bare pack line with `--readme-file` is the fallback only when the crafter is unreachable.**
  Row 79's ruling, landed verbatim in `PLANNER.md` §2; this
  document's §7 working-style clause follows it.
- **The response-manifest provenance echo admits every key the request block can carry; a request-side stamp lands with its echo.**
  Row 76; row 80 pins the key parity.
- **Admission at a refusal is per path, never blanket; every non-TTY path declines without prompting; the refusal's remedy line is fully composed.**
  Row 78.
- **Hook confirmation trusts by layer, then by bytes.**
  Row 78; the store is a §7 fact.
- **ADR-0016's "deliberately no config key" clause is superseded for the sandbox escape only; a prompt is a per-invocation admission and needs no further supersession.**
  Row 75's ruling repair (the worker's VERBATIM text is on its
  row); the clause still holds for every other per-invocation
  flag.
- **Row 73: modernize, not retire.**
  The desk ruling of 2026-09-14; order and riders on row 73.

New, ratified 2026-09-14 (the continue-plan-006 sitting; each a
ruling of record with one home):

- **Bare apply resolves across the open set.**
  Candidates answer any open session; newest by `st_mtime_ns` wins;
  an exact tie refuses; the echo names the resolved session and the
  open set. Operator's ruling, VERBATIM from the desk: "what's the
  harm in just seeing if the most recent tarball applies to ANY of
  the open sessions, and if for some reason it's more than one (it
  shouldn't ever be more than one right?) then it can refuse or
  provide a wizard option". Supersedes board 51's multi-open
  refusal only; landed at row 87's resolver half.
- **Handoff inherits the parent's recorded forecast exactly**,
  including `[]`; `--write` overrides; a missing record falls back
  to the reading-plan set as an undeclared forecast; an inherited
  forecast is declared.
  Row 73 session B; the read-only-parent decision session A asked
  for.
- **No template closings on admission refusals.**
  Every refusal that names a re-run composes it: real filename, the
  verb used, every typed admission carried, refused values
  appended. Row 81; extends the board-78 rule to all three gates.
- **A prompt's decline names its cause.**
  Three branches, three lines — on the hook prompt now (row 83) and
  every prompt via row 89.
- **`bale config hooks`: bare list, `--forget <sha256|unique prefix>`, no forget-all, `--json` status-shaped.**
  Row 83; the store is a §7 fact.
- **Disjoint by default is standing sitting practice.**
  Row 88's `PLANNER.md` §6 sentence, VERBATIM in the doc — cited
  here, not re-quoted; `CLAUDE.md` §4's "deciding what's next" row
  points at it.
- **One clock (2026-09-15, this sitting).** Every date bale mints —
  the session id, its per-day counter, a handoff re-mint — and every
  timestamp it writes are UTC; a session dates what it writes from the
  session id, never from the date its chat shows. Landed at row 94 as
  the VERBATIM TARBALL.md §1 sentence and the opener line. The pack
  machine's local date is the UTC date (§7). Not re-litigated by a
  chat that shows a different day: the chat is a day behind, by
  design.
- **Terminal shapes (2026-09-15, this sitting; lands at row 96).** A
  worker turn in tarball mode ends in exactly one machine-recognizable
  shape: a response tarball, a probe block, a light question block, or
  a formal clarification. Prose that asks is not a shape. The
  discriminator is where the answer lives — in the environment and
  readable by script, a probe, even when the packer could answer from
  memory; in the packer's intent, a question; both, a probe first.
  Blocking asks are asked; non-blocking gaps are notes.md Proposals or
  named assumptions, unchanged. The light tier is a counted admission,
  not a judgment: at most three questions, none multi-tiered, each
  one-line-answerable or ratifiable by a word; its trail is the
  eventual response, not the thread; the packer's choice to escalate
  to formal rides on every block, and a request-side flag can force
  formal for a session. The formal clarification is unchanged for
  everything the light tier does not admit.

New, ratified 2026-09-15 (the continue-plan-004 sitting; each a ruling
of record with one home):

- **Bare apply is bounded by name and count.** Only files named
  `response-*.tar.gz` are ever opened; the two newest by `st_mtime_ns`
  are examined (one cutoff, so a tie at either rank is examined in
  full and refuses as before); resolution is among the examined files
  only, newest candidate wins; the no-candidate refusal names each
  examined file and its reason. Fixed at two by operator ruling, no
  config key. Supersedes the scan clause of board 51 only; row 87's
  content discrimination, tie refusal, echo, and non-TTY decline
  stand. Landed at row 101.
- **A composed line carries every typed admission value.** Typed
  values as the gate normalized them first, then the refused or
  drifted ones, deduplicated per flag — one rule for the drift,
  required-check, and base-drift lines; a dropped flag re-sends the
  operator through a gate they already cleared. Landed at row 89.
- **Every admission y/N names its decline cause.** Stdin closed, empty
  answer at a decline default, and an explicit answer each render a
  distinct literal line; the wizard's flow prompts are not admission
  gates. Landed at row 89 for the five non-hook prompts; the hook
  prompt landed it at row 83.
- **A re-attempt ends with the quoted retry line.** Any response with
  `corrects` set ends with one paste-ready physical line,
  `bale retry "<delivery dir>/response-<sid>.tar.gz"`, quotes always,
  because a second download of the same name gains a `(1)`; the desk's
  brief names the delivery directory (a §7 fact) so the worker never
  invents a path. Row 102 makes the bare filename resolve on its own.

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

New from the 2026-08-18 smoothing sitting:

80. **Mechanization landings must sweep the doctrine lines that
    made the human the mechanism, in the same motion.** The
    bale_version provenance stamp landed long ago, and the §2
    standing rule directing a sitting-open --version paste
    survived it; the 2026-08-18 sitting opened with the desk
    requesting a paste the request already answered. General form:
    a mechanization is not landed until the doctrine that routed
    the task through the operator is retired or re-pointed —
    otherwise the friction survives its own fix. Swept this
    sitting for the version rule; boards 39 and 50 owe the same
    sweep at their landings. [2026-08-25: board 50 discharged — its
    landing this close swept §7's CRLF/sed line (the sed-ritual
    remedy retired); board 39 still owes at its landing.]

81. **Master-desk packs are the worst digest-over-dump offenders —
    first measured read-precision datum.** This sitting's request
    shipped roughly 1.2MB; the desk's actual read set was roughly
    15% of shipped bytes (manifest, CLAUDE.md, MASTER.md,
    PLANNER.md, two TARBALL.md sections, INDEX.md's head, two
    response notes, bale.toml, targeted bin/ slices) and zero of
    the ~200 shipped telemetry records. Self-reported — exactly
    the stream board 42's docs_read field mechanizes — and a
    priority signal for board 38's stats-digest auto-include.

82. **A flat authorship line routed oracle authoring to the
    operator — the sub-master gap's live specimen.** Session
    009's rescope offer honored derive-don't-rewrite and
    checkpoint-tracks-scope, then addressed the re-derived
    checkpoint to the operator ("append --checkpoint-file with
    your file") — the only actor its read path allowed:
    PLANNER.md META granted "command and brief authorship, never
    oracle authorship," a flat-world line that stops a splitting
    session from authoring oracles for children it never builds
    against. Doctrine-scored, not a worker miss; the correction
    is the sub-master doctrine (this sitting), whose
    builds-against form matches TARBALL.md §7's actual contract.

New from the 2026-08-25 sitting (continue-plan-003):

83. **First post-epoch concurrent pair; hot-file rulings worked as
    pre-assigned lanes.** Boards 51 and 52 ran scope-disjoint with
    the hot files (VERSION, `bale_report.py`, BALE.md) partitioned as
    pre-assigned lanes: the sibling forecasts traveled verbatim in
    both briefs, there were zero lane violations, integration order
    was free, and the shared 0.4.16 bump landed desk-side via a rider
    rather than in either session. Board 45's hot-file forecast watch
    has its first live specimen and its resolution pattern —
    pre-assigned lanes plus a close-side bump rider.
84. **The sitting probe collapsed three status asks into one.** A
    single paste-back probe replaced three separate status asks and
    grounded the rider's oracle on real bytes before the desk
    authored it. Board 39's zero-paste case gains its third specimen
    and is strengthened: the request answers what the desk would
    otherwise have asked, and the one probe that remained was
    read-only and bounded.
85. **Bundle-stem first-match collision — the discipline held where
    the gate did not** (specimen; this close's own first attempt).
    Two consecutive desks' close bundles shared the stem
    `2026-08-25-sitting-close-deltas`; the stale twin resolved first
    and re-packed the prior sitting's already-landed brief as session
    `-009`. The worker's landed-state verification caught it, refused
    to fabricate or duplicate, and closed clean via unlock — the
    discipline holding where the mechanical gate did not. Guard
    seeded as board 55, fed by this entry; the remedy interim rule is
    **desk-unique bundle stems**.

86. **Fourth successful §11.6 recovery, and the first inside a
    bundle-spawned worker.** Compaction landed post-implementation,
    pre-assembly; the session re-grounded from on-disk state,
    recomputed every hash from bytes at pack time, and disclosed in
    notes — the disclosure-plus-mechanical-recomputation pattern
    holding for the fourth time (entries 12, 59 carry the earlier
    three). (`2026-08-26-board-53-amend-checkpoint-004`.)

87. **The pre-build clarification round is the
    questions-arrive-answerable shape, live on the manual path.**
    The board-53 worker surfaced a blocking ambiguity in an outcome
    contract before writing any code, as two coherent readings plus
    a recommendation and a default — the §15 escalation shape
    (options-plus-recommendation, cheapest-answer-available)
    exercised end to end with the architect as transport; the desk
    ruled with one adjustment and the session landed on the ruling.
    Specimen for the escalation-contract's harness-side design
    (seed D13, D14).

New from the 2026-08-29→31 sitting (the exchange arc,
formalize-convo-001):

88. **Bad oracle (crafter v1).** Two manifest-path probes carried
    `--kind clarification`, the desk's pre-ratification invocation
    model; ratified surface refused it; five red lines from one
    refusal. Corrected by desk amendment (`bale amend-checkpoint`,
    v2, passing probes byte-identical, same response bytes on
    retry). Model instance of the diagnosis protocol on the worker
    side: labels → single-shape hypothesis → spec questions, no
    script, no speculative retry.

89. **Vacuous passes, both directions.** An expect-non-zero probe
    cannot distinguish "refused for the right reason" from "never
    ran" (the from-planner probe passed on the flag gate in the
    HOLD run); the worker's suite had the inverted blind spot
    (never tested the combination it designed away). Standing
    watch item for oracle and suite authors both.

90. **Desk discipline — the arc's one repeated defect, three
    specimens.** Unverified claims in briefs about (a) tree state
    ("amend-checkpoint has its own module"), (b) worker reach
    ("the schema it already ships beside" — INJECTED_TOOLS says
    otherwise), (c) the desk's own post-authoring rulings (the v1
    oracle vs the ratified flag surface). One rule covers all
    three, landed on PLANNER.md §4's checklist at this close: **a
    brief or oracle claim about any surface — tree, reach, or
    ruling — is verified against bytes or the sitting record at
    authoring time, and an oracle authored before a ruling is
    re-verified against every ruling made after it.**

91. **Verification exemplar.** The crafter session's
    mutation-tested parity guard (five injected drifts, each red,
    restored green; the `ensure_ascii` drift caught by exactly one
    test that exists because ASCII-only corpora pass under either
    setting). Cite from CODE.md's testing doctrine if a home is
    wanted; recorded here regardless.

92. **The stale-count brief defect.** A desk amending a brief
    mid-authoring added a sixth enumerated row and left the "five
    work rows" header stale — derived edits that add content can
    leave a stale count as easily as a fresh rewrite drops a
    section (the evidence-71 class, inverted). Caught by the
    worker pre-build, flagged in chat, resolved by the superset
    reading (§5, the fold-in/purge-review ratification). (From sid
    `2026-08-31-sitting-decisions-foldin-005`.)

93. **The citation-count correction.** The purge brief estimated
    ~30 evidence citations in PLANNER.md from a per-line grep; the
    worker's multi-line-aware pattern found 45 — doubled-per-line
    and wrap-split citations are invisible to line-based counting.
    A desk stating a count states a claim; count with the same
    class of pattern the work will use. (From sid
    `2026-08-31-global-doc-purge-004`.)

94. **The dual-spelling resolution.** A brief marked a citation
    VERBATIM in a rendering ambiguous about whether its backticks
    were formatting; the worker resolved it per destination house
    style — backticked in the markdown doc, plain in the schema's
    JSON descriptions — and byte-asserted both spellings in
    validation. Verbatim markers should state their exact bytes or
    delegate to house style explicitly. (From sid
    `2026-08-31-global-doc-purge-004`.)

New from the 2026-08-31 continue-plan-012 sitting (waves 2–3):

95. **Two desk fixture defects in one sitting.** The sid-key
    defect caught at the pre-delivery dry-run (board 63's
    oracle), and the index-probe defect that leaked to a live
    HOLD (the tools-true-up checkpoint, corrected rev1→rev2 per
    the bad-oracle flow) — with the masking lesson: the rehearsal
    stubbed content at line 1 instead of where the house format
    places it, so the position assumption went unexercised.
    Practice residue, both recorded: rehearsal content is placed
    per house format, and an artifact with a mechanical format
    checker gets an oracle replicating that checker's detector.
    The checkpoint-thinness watch's threshold reading: two
    desk-side fixture defects, one sitting; a third fires the
    watch.

96. **Predicted-to-observed resolution.** 021's parity-suite
    claim, predicted at build (no bin/ shipped), verified
    observed at real staging — the claim-basis split resolving as
    designed. Feeds the thin-predicted-basis watch. (From sid
    `2026-08-31-tools-true-up-021`.)

97. **Compaction disclosure, done properly.** 024 disclosed a
    mid-session compaction and ran the full §11.6 recovery —
    manifest re-read, pinned kernel re-compared byte-for-byte,
    §10.1 step-10 set re-derived from present bytes. Feeds the
    queued bailout-vs-compaction ruling's corpus. (From sid
    `2026-08-31-board-44-stats-read-sides-024`.)

98. **Same-day citation reintroduction.** Board 63's session
    reintroduced board-number citations into the just-purged
    telemetry schema — the desk's own authoring miss (its brief
    carried no descriptions-stay-clean constraint) and the
    concrete argument that the mechanical guard, not brief
    discipline, is the durable fix. Caught and re-purged by the
    guard session under the exchange-amended scope. (From sid
    `2026-08-31-guard-deny-shapes-022`.)

New from the 2026-08-31→09-01 continue-plan sitting (session 026;
09-01 sids over the 08-31 sitting are expected provenance):

99. **Two falsified desk environment claims.** One sitting, two
    specimens: (a) the desk declared cross-machine environment
    stability from a two-machine sample that excluded the grading
    machine; (b) the desk attributed the delta to WSL when the
    isolated variable was sandbox confinement. Lesson, generalized:
    the grading environment is (machine × confinement), and only
    the dry-run observes it; a suite-shaped oracle must report its
    full failing enumeration, not a sample, and a brief's "green"
    must name the environment it is measured in. PLANNER.md §4
    candidates, recorded here for the doctrine doc: the enumeration
    rule, and the capability-map probe-print pattern (002's guards;
    also its proposal 2 — a per-id oracle stronger than
    exit-plus-enumeration). (From sid
    `2026-09-01-board-67-suite-repair-002`.)

100. **Desk pack-authoring pattern, three specimens in one
    sitting**, each caught by a gate at one round-trip's cost: 67's
    nonexistent forecast path; 42's missing embed sibling; the
    close pack's own out-of-vocabulary work-class value (`docs`
    for `doc`). PLANNER.md §2 candidate lines, the first verbatim:
    before fixing a write forecast, grep for the guards that pin cross-tree equality (embeds, mirrors, vendored copies) — every one names a `guard-forced sibling` the forecast must carry.
    The second, the general form: desk-authored argv is checked
    against the tool's own enumerations, not recalled.

101. **Nested-confinement discovery.** The sandbox wrapper's own
    tests fail inside the wrapper's confinement;
    suite-green-under-confinement is now a standing, enforced
    property (established by 67's oracle). Board-10-adjacent.

102. **Gate-ordering specimen.** bale open ran a ~9-minute
    confined dry-run before the pack's disjointness gate refused
    on arg-inspectable grounds. Candidate row opened: board 68.

103. **Forecast-refusal watch datum.** The 67-r1 pack refusal at
    the forecast gate (a nonexistent --write path) had no
    telemetry home — the first specimen for the deferred per-path
    counter watch (§3, annotated there); the master desk was the
    offender.

104. **The response_lint claims-value parity gap** (operator-found,
    desk-verified this sitting). The embedded schema cannot carry
    the bare-string claims enum (no oneOf in the subset validator;
    the schema text itself says the enum is "enforced in Python
    (validate_response_manifest)"), and the lint, deliberately
    bale-import-free, never replicates that Python check — so a
    bare-string claim value outside pass|fail|untested|unknown
    lints clean and refuses at apply. The annotated object form IS
    enforced (a plain enum inside the object shape).
    Lint-clean-but-apply-refused is the exact friction the lint
    exists to prevent. Counter queued: board 69(a).

105. **Read-precision stream, datum 2.** 003's in-spirit docs_read
    list — its own manifest could not carry the field (the
    request-injected lint predates the landing); the first
    mechanized fill arrives next request.

106. **The 002 exchange round as specimen.** expects-probe
    satisfied by a brief-designated relay courier; the trailer-hash
    verification caught nothing but proved the transport; and the
    answer's guard-print-your-probe instruction became 002's
    shipped behavior.

107. **Stranded-session specimen.** A foreign-project session
    correctly refused to hand-build a bundle against an unreadable
    format and fell back to the documented `--checkpoint-file` path
    — discipline holding — but could not tell
    unreachable-by-design from packing gap. Motivated row 70; the
    diagnosis-ambiguity lesson is the durable part.

108. **Vocabulary collision cost.** Jargon that collides with a
    safety-relevant term ("injection") is a specification-friction
    tax on every worker that reads it: row 70's r1 spawn materials
    primed a worker's safety heuristics in a foreign project and
    were re-issued as r2 with neutralized vocabulary. Candidate fix:
    row 77.

109. **Desk fixture-defect cluster; the thinness watch FIRED.**
    Three in one sitting: a pre-delivery rehearsal catch (an
    imagined `### INDEX` anchor); board 70's P5 (the probe pinned a
    deny pattern's spelling — mechanism over outcome — amended
    v2→v3 with an implementation-agnostic plant-and-red probe);
    board 71's P2 (the probe contradicted the brief's own W2, which
    required the legacy rung to keep the placeholder — a
    spec-contradiction subclass, new to the miss catalog; amended
    by STRIKING the probe, the first probe-deletion amendment,
    precedent noted). Entry 95 set the threshold at a third; the
    third arrived, and the §3 watch is marked FIRED. Two practice
    counters adopted at the desk: every probe gets a contradiction
    pass against the brief's work items before delivery; rehearsal
    landings must exercise degrade/legacy rungs, not just happy
    paths. Also recorded: the desk's own sweep initially
    undercounted its inventory by wrap-blind, variant-blind
    grepping (6 sites, not 3) — entry 93's lesson recurring at the
    desk.

110. **Frame-vs-content respawn boundary.** Mid-flight defects in
    stamped, gate-enforced surfaces (forecast, manifest
    constraints, checkpoint) mean the session's frame is wrong —
    respawn. Prose-level brief defects and read-side context gaps
    are correctable in flight through rulings, uploads, and relay
    — the desk-side rhyme of the fixture/work fork. Exercised at
    row 71: a missing transitive test dependency uploaded; a brief
    sentence that specified while claiming to describe, corrected
    by relayed ruling.

111. **Probe-before-remedy, retraction on record.** The desk
    advised commit-or-stash on an unread dirty file; then a
    wrong-cwd open refusal surfaced; the probe found the pin
    intact, the cwd at fault, and the "dirt" was the master's own
    telemetry record. A stash would have hidden a live record.
    Advice retracted; the remedy-before-probe instinct is what the
    probe discipline checks. The refusal's unnamed "this project"
    is board 68's grown cargo.

112. **Exchange adoption gap.** The formal blocking-ask channel
    exists end-to-end (crafter `--emit-block`, `bale relay`, the
    schema), but TARBALL.md §10.1's checklist never names it and
    its step 1 models informal asking — a well-formed worker
    followed the checklist (row 71's record: zero exchange rounds,
    the fixture dependency arriving by upload). A doc-placement
    gap; the fix rides row 74. Include-list authoring lesson beside
    it: chase test-file imports (the amend suite's fixture
    dependency did not ship); candidate mechanization — pack warns
    when an included test imports a repo test module outside the
    include set.

113. **`@skipUnless` class-decorator inheritance.** A class-level
    `@skipUnless` is inherited by subclasses and silently skips a
    subclass suite everywhere — row 75's first config-off class
    vanished this way. Caught at the fixture extraction: the
    shared fixture now carries no tests and no class-level
    decorators, and 73A's validation asserts the same shape on its
    own fixture module.

114. **Cross-session guard catch, nine days late.** Board 70's
    self-containment guard caught board 75's schema citations (a
    `$comment` citing `BALE.md §8.5`; "board 75" in two
    descriptions) at 75's first apply — a suite the request did
    not ship, HOLDing a session that could not have run it. Fixed
    by version-anchoring only; `includes_missing` named the suite,
    and the third include-authoring rule (§7) is the standing
    answer.

115. **Exchange adoption gap, specimens two and three.** Row 75's
    round carried by paste (`clarification.rounds: 0` against a
    real round); row 78's pre-flight asked in chat from a worker
    whose own brief named `--emit-block`. Row 74 landed the doc
    fix; row 85 is the mechanical one; the §3 watch names the
    fourth specimen as its re-trigger.

116. **Desk include-authoring: adopted and violated in one
    sitting.** "Chase test-file imports" adopted at this sitting's
    open and violated by the desk within the hour (73A's
    `includes_missing: tests/test_per_sid_checkpoint.py`); "chase
    what pins a doc" missed twice and survived by luck (neither
    doc session was shipped `test_sanctioned_pairs.py`; the desk
    probed the applied tree afterwards, green). Four rules now
    (§7).

117. **One stale sentence, two failure classes.** Row 73A: the two
    unpredicted failure classes both trace to one sentence in
    `cmd_handoff` ("the read set and the forecast coincide by
    construction") — true of ADR-0007, false since ADR-0015; and
    the forecast swap corrupts the ledger silently — the finding
    the desk weighted above the worker's own ranking.

118. **The reachable-docs gap class** (rows 79, 88). A desk
    practice that lives only in the project doc never reaches
    another project; the operator's "never anywhere else" report
    was the docs working as written. Test: grep the five injected
    docs for the practice's verb before assuming it travels.

119. **Blind-checkpoint rehearsal catching imagined surfaces.**
    Twice in one sitting the desk's oracle asserted a surface that
    did not exist (a global-layer path keyed off the wrong root; a
    stub anchored on unwrapped text) — the `PLANNER.md` §4
    rehearsal rule paying for itself before either oracle shipped.

120. **A sanctioned-pair pin protecting an in-flight edit.** The
    TARBALL.md §3.4 extract includes its terminal period, so the
    proposed em-dash extension would have broken the pin under a
    sibling's `tests/` forecast; the brief routed the clause to a
    new sentence.

121. **One-apply-behind, schema form.** The session that admits a
    key in the response schema must itself omit the key (the
    installed schema validates the response). Named by 74-76's
    worker; rows 71, 75, and 73A dropped the key for the same
    reason without saying so.

122. **Cheap gates before prompts.** Row 78's ordering pin (drift
    refuses before the sandbox prompt) — board 68's principle
    applied to a prompt.

123. **The master's own session hides a structural refusal.** Bare
    apply was contract-complete for weeks (board 51, 2026-08-25)
    and never worked at the desk, because the desk's read-only
    session counts as open and the multi-open refusal fired at
    every sitting. A feature exercised only between sittings is
    untested at the desk. (Row 87's resolver half; the §5 ruling.)

124. **A ruling the fixture cannot reach.** The desk ruled the
    `["."]` fallback fires only on a missing parent record; every
    fixture parent had a record, so the plan-less tests and the
    inheritance rule never met. The worker stopped (relay round) —
    correctly. Imagined surfaces apply to briefs, not just oracles
    (entry 119's rule, brief-side). (73B.)

125. **Verbatim transport is for decisions, not claims about
    files.** "No existing pin needs to move" travelled from s34's
    proposal into a desk instruction unverified; `len(PAIRS) == 5`
    was waiting in `test_sanctioned_pairs.py`. A claim about bytes
    is verified or omitted. (Row 80.)

126. **Includes narrowed to look disjoint.** Row 80 shipped without
    `bin/`; three suites could not run and shipped `predicted`.
    Disjointness is a forecast property; includes gate nothing.
    Third `includes_missing` specimen (row 84) — the one the ledger
    does not carry, since the worker reported it in prose.

127. **"Your call" costs a round trip.** Three desk-handed choices
    this sitting (73B's fallback — real; 83's `--json` and test
    home — not) became two relay rounds and one chat-first breach.
    When the desk has a preference, the brief states it. (73B, 83.)

128. **An oracle that pins source bytes for an output contract.**
    Row 83's checkpoint grepped `bin/bale` for the rendered decline
    lines; the first response rendered them correctly at runtime
    from constants and was held. Pin what the operator sees when
    the contract is what the operator sees. (83's first attempt.)

129. **Three fixture defects caught by dry-running, none by
    reading.** The dotted-module runner form (no `sys.path` for
    `harness`), a wrapped-phrase grep that passed vacuously, and a
    bumpless probe that would have coupled to apply order.
    `PLANNER.md` §4's rehearsal rule, earned three times in one
    sitting. (Desk-side, this sitting.)

130. **Worker rehearsal that masks its own validation.** The
    apply-side's first attempt copied `apply.sh`/`validation.sh`
    into its staging-shaped copy and passed a `bash -n` that the
    real staging cannot; 83's rehearsal passed a `validation.sh`
    written to its own reading of the brief. The blind checkpoint
    is the second reader for exactly this. (Both HOLDs of the
    sitting.)

131. **`unittest` exits 5 on "NO TESTS RAN" (Python 3.12+).** A
    fixture-defines-no-tests assertion must key on the `Ran 0
    tests` line, not the exit code. (73B.)

132. **A surface named from memory, twice in one sitting.** Board 94's
    desk imagined that `response_lint.py` embeds the request schema
    (it embeds the response and diagnostics schemas) — caught at
    oracle rehearsal, one probe struck; and named "a bundle stem" as a
    dated artifact a response authors (a bundle never rides in a
    response, TARBALL.md §3.4) — caught by the worker, one check
    struck at round 2. Same class as entry 125's: a claim about a
    surface is read or omitted. (Desk-side, row 94.)

133. **Test imports chased, fixture consumers not.** The include rule
    reached the module a suite imports and stopped; the suites that
    consume a shared fixture the forecast touched did not ship, and an
    edit to that fixture landed exercised by one test. Fourth
    `includes_missing` specimen, the first the ledger carries (row
    84). (Row 94.)

134. **Four invitations, one rule.** The doctrine said "chat is never
    a surface for a blocking ask" while four sanctioned surfaces said
    the opposite — §3.3's "small enough", §5.9.1's own conversational
    clause, CLAUDE.md §3's mode ask, and the opener's "ask me if
    anything is unclear", the most-read sentence in the system. A
    worker resolves that conflict in favour of the invitation nearest
    its eyes. Strike the invitations, not the worker. (Two chat-first
    breaches on the row-94 spawn; row 96.)

135. **The registry consulted at close, not at dispatch.** Two riders
    whose ride condition board 94's forecast satisfied went
    unmentioned in its brief and unconsumed in its response; the desk
    read the registry to write this close, after the session that
    should have carried them. The registry is a dispatch-time read.
    (Desk-side, this sitting.)

136. **A row that slid out of the sequence.** Row 47 was sequenced
    ahead of the held wave with row 74 riding its doc touch; when row
    74 was decoupled at the 09-14 close, the sequencing line was
    rewritten without 47 and no reader noticed until the operator
    asked, a sitting later, whether the HOLD paste block was still
    queued. A decoupling edits two places — the carrier row and the
    sequence — and the close checks both. (Desk-side, 2026-09-14/15.)

137. **The board consulted for riders, but by registry only.** Board
    89's notes reported two handoff-gate test failures; the desk read
    them as a fresh finding, ruled on them, and dispatched them to 101
    as a rider — while row 95 already held them verbatim from board
    94, with a scope guess the ruling confirmed. The registry check at
    dispatch (entry 135) is not enough: a finding a worker surfaces
    may already be a row, and a rider's touched file may be an open
    row's home. The dispatch check now reads §4's open rows by touched
    file. (Desk-side, this sitting.)

138. **Rehearsing only the branch the sandbox can produce.** Board
    101's first attempt was HELD with the blind checkpoint seven of
    seven and its own `validation.sh` exiting 1: the script grepped
    `validate.sh`'s output for a pass wording it had never seen,
    because `README.md` is not shipped in a request and so the sandbox
    only ever produced the one-failure branch. Practice residue: a
    needle against a shipped script's output is rehearsed against that
    script's pass branch or asserts its exit code; a branch the
    sandbox cannot reach is a branch the worker has not tested. The
    re-attempt's change set was byte-identical. (Worker-side, board
    101.)

139. **Third light-tier specimen.** Board 89's worker asked one
    non-blocking wording question in chat before building, took the
    operator's "go" as no preference, kept its named default, and
    recorded the aside in notes.md as a detail call rather than an
    intent gap. Under the docs as shipped there is no tier for that
    question; under the 09-15 ruling there is, and the worker's
    reading matched it. Row 96 lands the tier; this is its evidence.
    (Worker-side, board 89.)

140. **"Tests ship with code" without forecasting tests.** Board 89's
    brief said tests ship with code and its forecast named five `bin/`
    paths and no `tests/` entry; seven test files were admitted
    out-of-forecast at apply. The fixture-consumer include rule (entry
    133) covers the read side; the forecast side needs the same: a
    code row that will change or add tests forecasts `tests`. Rows
    101's pack did. (Desk-side, this sitting.)

## 7. Standing environment facts

- Architect on WSL; Windows Downloads at
  /mnt/c/Users/chord/Downloads/.
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
- Slow-test gating (`BALE_TEST_SLOW`, landed at
  `2026-08-25-pair-close-rider-008`): generation-heavy cases are
  gated behind the env var, established harness-level — the gate and
  criterion live in tests/harness.py (only the literal `1` opens it),
  and `validate.sh` surfaces gated status through an `[INFO]` marker
  class (status lines that are not checks; they move no counters).
  Criterion: cases ≥0.7s gate, the fastest-per-class representative
  stays in the default run; the default wall runs ~72% of the full
  run. Dated basis figure, not a standing count: 582 cases at that
  landing, 40 gated across 15 suites (10 representatives) — enumerate
  from the tree, never from this figure. Recency watch:
  if a regression traces to a gated fresh-feature case, **un-decorating is the named first-line remedy**.
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
  report), bale_open (the ninth — landed at
  `2026-08-24-board-49a-ii-open-verb-006`), _bale_toml. Load-time
  import set: pre-extraction it was bale_config, bale_validate,
  bale_staging, bale_rollback; the 8b/8c sessions refined the
  sibling lazy-import idiom, so re-verify the current set before
  scoping any include set that must execute bin/bale — evidence 13
  still governs. bin/bale VERSION 0.4.29 at
  `2026-09-14-apply-side-81-87-010` (0.4.28 rode
  `2026-09-14-board-73b-handoff-modernize-007`; 0.4.27 rode
  `2026-09-14-board-78-admission-prompts-001`; 0.4.26 rode
  `2026-09-10-board-75-sandbox-config-off-002`; 0.4.25 rode
  `2026-09-01-board-71-lifecycle-resolution-008`; the four
  doc/contract-doc sessions of the 2026-09-10→14 sitting landed
  bumpless per the doc-only reading, as did the continue-plan-006
  sitting's row 80 (tests-only), doc lane, and row 83); the
  per-bump trail — every bump's sid and the doc-only / tests-only /
  hot-file bump exemptions — lives in git (prior versions of this
  doc) and in the sessions' telemetry records.
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
  context, not locks (ADR-0015). Spawn materials are crafter
  bundles (`--bundle`) opened with `bale open`, the brief riding as
  a bundle member — `--readme-file` is the fallback only when the
  crafter is unreachable (§5, 2026-09-14; row 79); the
  2026-09-10→14 sitting's five spawns all traveled so.
  Desk emission rules, standing (recorded at the 2026-09-01/02
  sitting's close): every desk-emitted command is fully composed —
  sid included, real filenames quoted, zero placeholders, a single
  physical line (board 47 renders the tool-side successors to the
  same rule; row 74 carries the single-line rule into the docs).
  Extended 2026-09-14: the tool now renders composed remedies at
  the scope-drift and sandbox refusals (row 78); the desk composes
  only what the tool does not yet.
  Extended again 2026-09-14 (the continue-plan-006 sitting): the
  base-drift and required-check refusals render composed lines too
  (row 81) — every admission refusal's remedy is tool-composed.
  Session references in this doc use the full sid, or NNN
  qualified by sitting — bare NNN collides across same-day
  sittings (009's proposal, accepted 2026-07-31; going forward
  only, no retroactive sweep).
- Telemetry corpus tolerance, dated (from the 026 sitting): every
  post-v0.4.21 retry before the
  `2026-09-01-board-67-suite-repair-002` landing appended a
  spurious mid-session 'opened' telemetry attempt — fixed by
  threading `open_telemetry` through persist_pack_session (retry
  passes False). No retroactive record edits, per the additive
  doctrine; attempt-level open-counting consumers need this dated
  tolerance. Outcome-level counts — the §5 bailout-vs-compaction
  ruling's corpus facts included — are unaffected.
- One-apply-behind (meta-sessions §2): the apply that lands a change
  to apply-path code runs the OLD code one final time. Recurred four
  times in the v2 sitting; workers now flag it unprompted.
- Include-authoring rules, standing, now four (recorded at the
  2026-09-10→14 sitting's close; §6 entries 112 and 116): chase
  test-file imports; chase REQUIRED-key write-sites; a forecast
  touching `schemas/` ships the self-containment guard; a forecast
  touching a global doc ships the four doc-pin suites
  (`test_sanctioned_pairs`, `test_doc_crossrefs`,
  `test_global_doc_selfcontainment`, `test_schema_embeds`) to run.
- Hook acceptance store: `<install>/user/hook-acceptances.json`
  (row 78; keyed by sha256 → script, hook, layer, accepted_at),
  never committed; malformed → warn and decline. Operable from
  `2026-09-14-board-83-hook-store-and-decline-cause-011`: `bale
  config hooks` lists (oldest-first), `--forget <sha256|unique
  prefix>` removes one (prompt-free; no forget-all), `--json` is
  status-shaped; the hook prompt's decline line names its cause
  (stdin closed, Enter at a decline default, or the answer given).
- Bare `bale apply` works beside an open master from 0.4.29
  (`2026-09-14-apply-side-81-87-010`, row 87's resolver half):
  candidates answer any open session, newest by `st_mtime_ns`
  wins, an exact tie refuses, the echo names the resolved session
  and the open set (§5, 2026-09-14). Before this the master's own
  read-only session tripped board 51's multi-open refusal at every
  sitting (§6 entry 123).
- Environment: the installed `bin/bale` was verified against source
  at 0.4.27 by `grep -c 'return not default_no' "$(command -v
  bale)"` → 1 (the close-6 hook decline event, §3). `reinstall.sh`
  mirrors the *checkout* into the install and apply is
  checkout-free (ADR-0008), so the install tracks the working tree,
  not the merge.
- Version landmark 0.4.30 (row 94, 2026-09-15).
- Version landmark 0.4.32 (row 101, 2026-09-15); 0.4.31 at row 89 the
  same day.
- Forecast rule: a code row that will change or add tests forecasts
  `tests` (entry 140); the include rule for fixture consumers (entry
  133) is its read-side twin.
- Re-attempt closing line: the desk's brief names the delivery
  directory — `/mnt/c/Users/chord/Downloads/` — and any response with
  `corrects` set ends with
  `bale retry "<delivery dir>/response-<sid>.tar.gz"`, quotes always
  (§5, 2026-09-15).
- Dispatch check, grown: before emitting a bundle the desk reads the
  registry (entry 135) and §4's open rows by touched file (entry 137);
  a decoupling edits the carrier row and the sequencing line both
  (entry 136).
- Bare-apply cost mechanism, for the record: `_peek_bare_candidate`
  reads a whole gzip stream per file (`getmembers()`); the resolver
  bounds how many files reach it (row 101). A directory of many
  tarballs is now two opens per bare run.
- The pack machine's clock: the architect's WSL host runs on UTC —
  `date` and `date -u` agree (verified 2026-09-15). A chat date behind
  a session id by one day, from about 20:00 Eastern, is the expected
  skew, not a defect; the opener says so since 0.4.30.
- Include-authoring rule, accreted 2026-09-15: when a forecast holds a
  shared test fixture module (`tests/harness.py` and its fixture
  classes), the suites that consume that fixture ship with it, found
  by grepping the fixture's class names across `tests/`, not by
  chasing imports (row 84's fourth specimen).
- The "applied" report convention, recorded once: the architect's
  paste of a landed session's notes.md followed by the word "applied"
  is the apply report. A session that lands has passed its blind
  checkpoint and the apply gates by definition; no separate report is
  asked for.
- Registry riders are a dispatch-time read (§6 entry 135): before
  emitting any bundle, the desk checks the §3 registry for entries
  whose ride condition the forecast satisfies and names them in the
  brief.

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
