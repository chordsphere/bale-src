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

Last landed by: `2026-10-06-sitting-close-deltas-21-004`.
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
- A read-only sid that later packs do not sweep: the
  `2026-09-23-board-100-design-001` record still reads `opened` after
  three later opens under it, W1 to W3, each a `bale open` replay, and
  its file is untracked on the tree because no closure ever committed
  it; the 004 open swept the `2026-09-22-continue-plan-001` master, and
  the successor's own open swept the `2026-09-22-continue-plan-005`
  master (§6 entry 212). Re-trigger: the next read-only session that
  outlives a later pack. Source: the close-18 probe of 2026-09-23T03:15Z
  (record `outcome: opened`, `git status` `??` on the file). (Opened
  2026-09-23 at close 18; a watch, not a defect, by the
  `2026-09-22-continue-plan-005` desk's call.)
  [2026-09-24: fired in wave 11, twice, in shapes the watch did not
  name, by the records at close 19. The `2026-09-23-continue-plan-006`
  master was swept `closed-read-only` at 2026-09-23T22:08:25Z by the
  `2026-09-23-board-45-hostile-repo-design-010` pack, which its
  `swept_by` names, and its desk went on to rule the stemwell arc and
  write close 19's brief on 2026-09-24. The design-010 record closed
  `abandoned` on `command: unlock` at 2026-09-24T00:57:39Z, 41 seconds
  before stemwell's seed v1 was unlocked `abandoned` at 00:58:20Z, and
  its desk then authored the seed v2 and the first wave: a closure
  reason reading `abandoned` over a sitting that went on to deliver. No
  record says whether that unlock was meant for the design sitting
  (close 19's notes.md). In stemwell, `2026-09-24-board-45-close-008`
  still reads `opened` in the snapshot this close read. Re-trigger
  unchanged.]
- WSL `clip.exe` and non-ASCII (from D's notes, through the wave2-004
  desk's brief, §3 "On watch"; the words are the desk's): "D's notes
  flag that `clip.exe` reads stdin in the console codepage, and bale's
  paste blocks carry em dashes ("—"), the session opener included. The
  operator runs WSL. This desk suggested the operator try `iconv -f
  UTF-8 -t UTF-16LE | clip.exe` as the configured command; that is a
  suggestion, untested here. If the operator confirms it mangles, the
  follow-up is for C's WSL alternative to offer the transcoding form.
  Ask the operator for the result before authoring anything on it."
  Re-trigger: the operator's report of the try; a mangled paste makes
  C's WSL alternative offer the transcoding form, and a clean one closes
  this. (Opened 2026-10-05 at close 20, from the 2026-10-03/04 desks.)
- The project-layer absolute WSL path (same source): "C's project-layer
  wizard offers the absolute WSL Downloads path. A pick lands it in a
  committed, team-shared file. A home-relative form may be wanted." C's
  own notes call it "odd in a committed file, but the brief asks for it"
  (decision 7). Re-trigger: a pick landing the path in a committed
  `bale.toml`, or a second operator on the same project. (Opened
  2026-10-05 at close 20.)
- macOS `pbcopy` under `start_new_session` (same source): "D could not
  observe it (Appendix D, "Things I'm unsure of")." D's words: "I
  believe `pbcopy` doesn't care about `setsid`, since the pasteboard
  lookup goes through the bootstrap namespace, not the session. But I
  couldn't run macOS here. If a Mac operator sees "copied" with an
  unchanged clipboard, look at `start_new_session=True` in
  `run_clipboard_command` first." Re-trigger: the first macOS operator's
  report either way. (Opened 2026-10-05 at close 20.)
- A stale open session, `2026-05-14-bale-handoff-008`: the cleanup
  desk's probe of 2026-10-04 lists it under "open sessions" beside the
  desk's own sid, in the registry since May and named nowhere else in
  this document; no record of it shipped to close 20, so what it was and
  why it never closed are not known here. Recorded on watch, not closed,
  by the cleanup desk's call (its brief's §4). Re-trigger: the next
  read-only pack's sweep offer naming it, or a disjointness refusal
  against a forecast it holds; the remedy then is `bale unlock` with a
  reason, by the operator. (Opened 2026-10-05 at close 20, from the
  `2026-10-04-friction-points-cleanup-002` desk's finding.)
- The dotted-key split between bale and the crafter (from the rename's
  notes.md, its decision 2, the second paragraph verbatim): "The one
  known split this leaves (an edge of the pre-existing one): a *dotted*
  `clipboard.command = "x"` beside a readable `[probe] clipboard_command
  = "y"`. bale's parser sees the new key and refuses its spelling (loud,
  nothing copied, `bale status` shows UNREADABLE with the remedy); the
  crafter's scan cannot see dotted keys at all, so its no-bale fallback
  would tee into `y`. bale is loud first, so an operator meets the
  refusal before any probe runs; I did not teach the scan dotted keys.
  Pinned as a refusal case in
  `EffectiveAccessorTest.test_other_unseen_spellings_are_refused`."
  Re-trigger: an operator writing a dotted `clipboard.command`, or a
  probe run on a machine without bale copying the legacy value; the
  remedy then is teaching the crafter's scan dotted keys. The decision
  itself is ratified as shipped (the cleanup desk's light block four,
  [1]). (Opened 2026-10-06 at close 21, from
  `2026-10-05-clipboard-key-rename-002`.)

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
- Whether the release tarball ships BALE.md — today `scripts/build.sh`
  excludes it, the README now points install readers at `bale help
  <command>`, and several `--help` strings still cite `BALE.md §N` an
  install reader cannot open (99a's Proposal 1). Ship it, or keep it
  source-only and qualify the citations in a `bin/bale` string pass.
  [2026-10-05: recounted at close 20 against `BALE_HELP.md` as bale
  0.4.45 carried it in close 20's own request, confirming the cleanup
  desk's figures row by row: 24 `BALE.md` occurrences across 9 of the 19
  help sections (the 19th is D's `clipboard`); 23 cite a section and one
  is a bare mention, "the full tool reference is BALE.md in the bale-src
  repository", in the top-level `bale help`; the citations reach 11
  distinct sections counting only the section right after `BALE.md`, or
  12 counting every section named, §8.7 appearing only as "§5.4/§8.7":
  §5.4, §5.6, §6.7, §7.1, §7.3, §7.8, §8.1, §8.5, §8.7, §8.9, §8.11,
  §11. Board citations: 9 mentions naming 10 board numbers in 5
  sections, pack (boards 6, 64), apply (6, 10, 75), retry (71, twice),
  amend-checkpoint (50), open (68, 122). E's figures at the 2026-10-03
  landing were 24 occurrences across 9 of 18 sections, 22 section
  citations to 11 distinct sections plus 2 bare mentions, and 8 board
  citations; the totals agree, and the classification differs on
  `handoff`'s second mention, `--verbose`'s `(BALE.md §5.4)` wrapped
  across two lines, which E's notes list as a bare mention, by this
  close's reading of both counts. B, C and D added help text and no
  `BALE.md` citation. E's proposal, folding the board citations into the
  same string pass, is agreed by both desks; the ruling stays the
  operator's. The arc's five BALE.md sentence sets for 99b are the
  registry's routing entry of this date.]
- Whether every verb's `[bale]` lines wrap on a terminal, and whether
  checkpoint authors are told that terminal transcripts wrap. log-hold's
  first Proposal, filed here by the operator's "as assumed" to the
  cleanup desk's light block two, [2], because wrapping every verb
  breaks 18 pty assertions and changes all terminal output; log-hold
  itself wraps only pack's pre-walk lines (its decision 3, ratified).
  Text verbatim from `2026-10-04-log-hold-003`'s notes.md, nested
  markers flattened: "**Display wrapping for every verb.** *What:* call
  `set_log_display_wrap(True)` once in `main()`, so every verb's
  `[bale]` lines fit the terminal. Then update the pty pins that read
  fixed decline lines whole: the hook, admission, and sweep decline
  lines in `test_hook_acceptance`, `test_admission_prompts_e2e` and
  `test_readonly_pack`. The `on_terminal` helper this session added to
  `test_supersession_pack` is the pattern; it belongs in
  `tests/harness.py` if a second suite adopts it. *Why:* the same
  80-column friction exists on apply, retry, relay and status. I
  measured the cost: 18 assertions in 4 suites. Any blind checkpoint
  that greps a decline line off a pty would need the same tolerance.
  *Scope hints:* `bin/bale` `main()` plus those three suites. Rule first
  on whether checkpoint authors should be told that terminal transcripts
  wrap." (Queued 2026-10-06 at close 21.)
- Whether the checkpoint picker drops its Unicode-digit read, and
  perhaps its literal-file rule. choice-prompt-convergence's second
  Proposal, filed here by the cleanup desk's light block four, [3]: it
  changes what an answer says and reverses that desk's pin (every answer
  at the picker keeps its meaning). The Proposal drops the first and
  only asks to "consider" the second; the cleanup desk's brief
  summarized both as dropped, and the close desk caught it. Text
  verbatim from `2026-10-06-choice-prompt-convergence-001`'s notes.md,
  flattened: "**Drop two of the picker's three exceptions.** As the
  brief asked, I kept all three. *What:* make the picker read numbers
  with the layer's ASCII `pick_number` and drop the `number` option.
  Also consider dropping the cwd literal-file rule, and with it
  `out_of_range_ok`. Keep `?` as a path, on B's ratified reasoning.
  *Why:* the Unicode-digit pick is an accident of `str.isdigit`, not a
  design. The literal-file rule only serves a checkpoint saved under a
  bare number in cwd, beside a list that already offers numbers, and the
  file stays reachable as `./7`. Dropping both would make the picker's
  number rule exactly config init's. *Scope hints:* `bin/bale_pack.py`
  (`picker_number`, `_wizard_input_checkpoint_file`),
  `bin/bale_wizard.py` (`ask_choice`), and the picker tables in
  `test_pack_wizard_ui`." (Queued 2026-10-06 at close 21.)
- Whether config init's `.baleignore` add prompt moves onto
  `ask_choice`, which changes that screen's prompt text, frozen by
  convergence's constraint. Convergence's fourth Proposal, filed here by
  the same block's [3]; text verbatim, flattened: "**Config init's
  `.baleignore` add prompt.** *What:* move its numbered picks onto
  `ask_choice` (`noun="suggestion"`, `typed="a pattern"`). *Why:* it is
  the last hand-built numbered choice in either wizard. It still runs
  its own "no suggestion N" loop. *Scope hints:* it would change that
  screen's prompt text, which this session's constraint froze, so it
  needs a ruling first." (Queued 2026-10-06 at close 21.)

**Fold-in registry** (one home, this list — the dated block v3
carried inside §2's 07-16 sitting summary is merged in; each entry
below was reconciled against shipped bytes at the v4 regeneration,
with the unverifiable ones carried verbatim and marked):

- run_hook's three placeholder-less f-strings — rides any session
  touching bin/bale section 23. Cosmetic.
  [2026-09-18: carrier now row 110, among its `bin/bale` riders.]
  [2026-09-19: consumed at `2026-09-19-board-110-held-admissions-007`
  (rider 3): the three `print(f"...")` lines are plain strings, output
  unchanged.]
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
  [2026-09-18: carrier now row 104; gains 107's Proposal 1 — the
  stamp sweep's result joins the key.]
  [2026-09-20: row 104 cut in two; this key rides 104b, recorded on the
  `sweep`/`include_group` entry below.]
  [2026-09-20: landed with 104b (0.4.40). The closing bracket, and the
  key's shape, are on the `sweep`/`include_group` entry below.]
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
  [2026-09-17: the fold-in list gains the stats micro's two records,
  `tests/fixtures/stats_corpus/2026-06-30-fx-docs-read-002.json` and
  `tests/fixtures/stats_corpus/2026-06-30-fx-handoff-origin-001.json`
  (`2026-09-17-stats-micro-001`).]
  [2026-09-20: condition not met at 37. It took the own-suite path
  (`tests/test_stats_compaction.py`, admitted at the prompt) and changed
  the shared suite only in its whole-dict `budget` expectation, which
  gains the new `compaction` key; no fixture was added. Its notes.md
  says the condition is not met, and the entry stands.]
- Checkpoint `bash -n` fail-fast: `check_response_shell_syntax`
  gates `apply.sh` and `validation.sh` only; a syntax-errored
  checkpoint surfaces mid-pipeline. Rides board 10 or the next
  session touching that function. (Source:
  `2026-08-07-sandbox-adr-009`'s surprises.)
  [2026-09-18: flagged, not closed — the desk saw a
  `check_checkpoint_shell_syntax` in `bin/bale_staging.py` (line 125)
  and did not read it; the next desk verifies and retires or keeps.]
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
  [2026-09-16: consumed at `2026-09-16-board-pack-ux-micro-004` — the
  prefix attributes by source in both directions; the `ValueError`
  tail still names `.baleignore` — row 106.]
- test_apply_preflight.py module-docstring history true-up: the
  "earlier behavior pin documented the identical-duplicate
  acceptance" line misattributes session 1, which deliberately
  pinned nothing there (`2026-08-07-board-35-small-pins-010`'s
  wrinkle). One line; rides the next touch of that file.
  [2026-09-19: consumed at `2026-09-19-board-110-held-admissions-007`
  (rider 5, found at dispatch by the 006 desk): the docstring now names
  row 32's test as the file's first pin and says session 1 deliberately
  pinned nothing.]
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
  [2026-09-16: consumed at `2026-09-16-board-pack-ux-micro-004` —
  judged against the shipped set after excludes; a warning, never a
  refusal.]
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
  [2026-09-18: closed at `2026-09-18-board-107-supersedes-clean-tree-004`
  as not reproducing as written — the closure record is written before
  its sweep, and the log order is a reporting artifact (the `superseded`
  line prints after `close_session_with_record` returns). The worker's
  inference, from code and version history rather than the sitting log,
  is that the 2026-08-13/14 dirt was row 107's stamp. The tree-clean
  test landed.]
- ADR-0015 disjointness remedy text: "narrow this pack" is the
  wrong remedy against a whole-tree open session — proven live
  this sitting, where a disjoint `--write` still refused (the open
  session's default forecast is `["."]` and intersects
  everything); the honest remedy is close/apply/unlock the open
  session, or narrow ITS forecast. Rides the next gate/report
  touch.
  [2026-09-16: consumed at `2026-09-15-board-68-open-gate-order-012`,
  on handoff too.]
- Wizard checkpoint prompt candidate picker: list search-path
  candidates newest-first with path, mtime, and sha prefix; a
  free-typed path stays accepted. Rides the next pack-UX session.
  [2026-09-16: consumed at `2026-09-16-board-pack-ux-micro-004` —
  every `.sh` in cwd and the search paths, newest first, path + mtime
  + sha prefix; a typed number or a typed path.]
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
  [2026-09-16: consumed at `2026-09-16-board-99a-outward-docs-003` —
  project layer only, with the reason in the prompt.]
  [2026-10-05: the layer rule reversed. By the operator's ruling [1] of
  2026-10-03 (§5, that date) the key is per-machine, global layer with
  project override, since C, `2026-10-03-wizard-defaults-006`:
  `merged_config` inherits `[probe]` per key, the global wizard walks
  it, the project wizard offers `x`, which writes `clipboard_command =
  ""` and suppresses, and `effective_clipboard_command(repo)` is the
  reader. The spelling is unchanged.]
- bale open FORCE-prefix doubling — the --no-sandbox line logs "FORCE:
  FORCE:", observed at the first live open (this sitting's rehearsal and
  spawn); a one-line fix. Rides the next bin/bale_open.py touch.
  [2026-09-16: consumed at `2026-09-15-board-68-open-gate-order-012`.]
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
  [2026-09-16: consumed at `2026-09-15-board-91-82-crafter-pair-011`,
  with the two `_section_29` renames (no name-selecting consumer
  found).]
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
  [2026-09-19: closed as stale: no such identifier remains in
  `tests/test_craft_response.py` (the 006 desk, 111's worker, and the
  009 desk each grepped). The entry above's 2026-09-16 bracket already
  records the renames consumed with the section-29 literal; this entry
  was never bracketed to match.]
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
  [2026-09-16: consumed at
  `2026-09-16-board-47a-hold-card-triage-001`.]
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
  [2026-09-17: consumed at `2026-09-17-stats-micro-001` (row 44's
  wiring; rows 86 and 98 beside it).]
- Release-surface include group, candidate extension: pull tools/
  along with the group (specimen: 002's includes_missing —
  tests/harness.py hard-requires tools/ via INSTALL_TREES, and the
  67 pack didn't ship it). Rides row 68's bin/ touch or the next
  release-surface touch. (Accepted 2026-08-31/09-01 at the
  continue-plan sitting, session 026.)
  [2026-09-16: consumed at `2026-09-15-board-68-open-gate-order-012` —
  the group is project config; this repo's `bale.toml` pulls `tools`,
  pinned by `TestThisRepoGroup`.]
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
  [2026-09-17: carrier now row 109, the harness micro, which holds
  `tests/harness.py`.]
  [2026-09-18: consumed at `2026-09-18-board-109-harness-micro-002` —
  `normalize()` has one home in `tests/harness.py`.]
- `bale config hooks` row in BALE.md §5's command table, and one
  sentence in BALE.md's apply and pack sections that every admission
  y/N names its decline cause — both ride 99b (the BALE.md true-up).
  From boards 90 and 89, 2026-09-15.
- `bin/bale_apply.py`'s module docstring says the module never imports
  `bale_pack`; a lazy `import bale_pack` (~line 1144) contradicts it.
  Drop the sentence or lift the import — rides the next
  `bale_apply.py` touch. From board 101.
  [2026-09-16: consumed at `2026-09-15-board-102-explicit-name-010` —
  the sentence now says what is true; the import stays lazy.]
- `shlex.quote` on the non-TTY bare-apply refusal's
  `bale apply {path}` line, matching the decline's quoted alternative
  — rides row 102. From board 101.
  [2026-09-16: consumed at `2026-09-15-board-102-explicit-name-010`.]
- "request includes" in place of "pack includes" in the shared
  blindness diagnosis, so it reads right on a handoff — only if the
  byte-shared-diagnosis constraint is re-ratified; otherwise stands.
  From board 101.
- BALE.md riders for 99b's true-up, one entry: the `[probe]
  clipboard_command` key (project layer only, with its reason) in
  §3.6 and the `bale.toml` sections; the two pack-time warnings
  (forecast-not-included; included test importing an excluded test
  module) near the §7.4/§6.4 guard prose, with their
  warning-never-refusal posture; and a re-true of the README and
  `bale apply`/`retry` help HOLD wording against 47a's landed card
  (the ruling-keyed next step is the card's lead affordance). Rides
  99b; the last item touches `README.md` and `bin/bale` too.
  [2026-10-05: stale on its first item. "Project layer only, with its
  reason" was true at 99a; since C the key is per-machine at both layers
  (ruling [1] of 2026-10-03, §5), so 99b writes the both-layer rule,
  with `""` at the project suppressing, and C's sentence in the routing
  entry below is the current wording. The two warnings and the HOLD
  re-true stand.]
- `docs/CLAUDE.md`'s INDEX read-paths row for the light tier says
  "authored by hand per TARBALL.md §5.10"; it names
  `tools/craft_response.py --light-block` as the path with
  hand-authoring as the fallback. Rides the next `docs/CLAUDE.md`
  touch (row 105 is one).
  [2026-09-17: consumed at `2026-09-16-board-105-operator-voice-007`.]
- The crafter's `read_clipboard_command` reads only double-quoted
  TOML values; a hand-edited literal string (`'pbcopy'`) parses in
  bale and reads as unset in the crafter. Accept the single-quoted
  form or name it in the treated-as-unset note; a pin belongs in
  `CrafterAgreementTest`. Rides the next `tools/craft_response.py`
  touch (row 69).
  [2026-09-17: consumed at `2026-09-16-board-69-tools-pair-008` — the
  single-quoted form is accepted; the triple-quoted refusal is a new
  entry below.]
- `format_walkthrough_summary` builds its checkpoint attribution
  through `_checkpoint_attribution`, the helper the judge line uses,
  so the vocabulary has one home instead of three (walkthrough, apply
  log line, card); a pure refactor that must keep the walkthrough's
  exit-2 tail. Rides the next `bin/bale_report.py` touch (47b).
  [2026-09-18: consumed at `2026-09-18-board-47b-relay-blocks-003` — the
  walkthrough routes through `_checkpoint_attribution` (a
  `_worker_attribution` beside it), its exit-2 tail byte-identical; the
  apply log line's wording stands as a third home, unscheduled.]
- E2E pin for `bale handoff --verbose` naming a typo'd reading-plan
  path as `verbose: drop <path> (not tracked)` — the case row 92 was
  written for; no source change expected. Rides the next handoff
  suite touch.
- A bale-side consumer for `get_probe_clipboard_command`: a `bale
  status` row ("probe clipboard: <cmd> / unset") so a
  crafter-unreadable hand edit surfaces before a probe falls back to
  remedy text. Rides the next `bale status` touch.
  [2026-10-05: consumed at `2026-10-04-clipboard-paste-blocks-001` (D),
  re-worded for the reshaped key as the 2026-10-03 desk asked: the row
  is labelled `probe clipboard`, four states, `pbcopy (global layer) —
  every paste block is copied` / `suppressed here (…)` / `unset — …;
  bale config init --global sets one…` / `UNREADABLE — nothing is copied
  until it is fixed: <reason>`; status exits 0 in every case; the reader
  is `effective_clipboard_command`, not `get_probe_clipboard_command`,
  which cannot see spelling (C's handoff to D). The relabel to
  `clipboard` rides the key rename (D's Proposal 2, dispatched as
  `2026-10-04-clipboard-key-rename`).]
  [2026-10-06: the relabel consumed at
  `2026-10-05-clipboard-key-rename-002`, by its notes.md and record: the
  row is labelled `clipboard`, its words "byte-identical to D's row
  apart from the label" for a lone `[clipboard] command`, and naming the
  spelling only where a reader would want it (decision 3); `bale status
  --json` gains the `clipboard` object, `command`, `source`, `key`,
  `shadowed`, `problem` (decision 4); the record's assertion "status row
  label and json clipboard object" ran and agreed. The row reads the
  command through `clipboard_command_reading(repo)`, log-hold's
  non-exiting form, by the shipped `claude/context/bale-internals.md`.
  `bin/bale_report.py` itself did not ship to close 21, so the row's
  bytes are not read here.]
- Pack-json `sweep`/`include_group` key: named and deferred at 47a
  (its pass-through half sat in the pack-UX micro's file). Carrier
  unchanged.
  [2026-09-17: carrier now 47b's rider list (row 47).]
  [2026-09-18: moved off 47b at the open — the key spans
  `bin/bale_report.py` (47b) and `bin/bale_pack.py` (107); carrier now
  row 104, gaining 107's Proposal 1.]
  [2026-09-20: carrier now 104b, with the stamp sweep's result:
  dispatched by the `2026-09-20-continue-plan-006` desk as
  `2026-09-20-board-104b-pack-telemetry` beside close 15.]
  [2026-09-20: consumed at `2026-09-20-board-104b-pack-telemetry-008`
  (0.4.40): `bale pack --json` gains two always-present keys, `sweep`
  and `include_group`, additive, with the stamp sweep's result among
  `sweep`'s events (107's Proposal 1) and the older `sweep` entry's list
  shape kept. The six-key entry was ratified at the
  `2026-09-20-continue-plan-009` desk, the brief's pin having been a
  floor. Shapes in §5, "A pack records what it swept, and when it was
  packed"; home BALE.md §7.7 and `format_pack_json`'s docstring.]
- Four sibling precedence sentences — the META "this file wins"
  sentences of TARBALL.md, DOCS.md, CODE.md, and PLANNER.md, siblings
  of CLAUDE.md's reworded one — ride the 100 arc's doc-injection
  sweep. From the 2026-09-16/17 sitting.
- TARBALL.md §5.10's shape-sentence pin in `test_doc_crossrefs` —
  rides the doc sweep. From 105's Proposals.
  [2026-09-18: consumed at `2026-09-18-board-109-harness-micro-002`, as
  a pin on §5.10's own wording (`TARBALL_SHAPE_SENTENCE`), with a third
  test holding both pinned constants to one shared second half; whether
  the three homes converge on one wording is a new entry below.]
- In-process opener constants test. From the 2026-09-16/17 sitting.
  [2026-09-17: consumed at `2026-09-17-board-106-bale-dedup-003`; this
  entry records it.]
- Bale-side refusal of a triple-quoted `clipboard_command` — rides the
  next `bin/bale_config.py` touch; 005/69's disclosure stands
  meanwhile.
  [2026-10-05: consumed at `2026-10-03-wizard-defaults-006` (C), routed
  there rather than to A by the 2026-10-03 desk because C reshapes the
  key. The refusal lives in the reader, `effective_clipboard_command`,
  plus a warning on the key's wizard screen, not in `load_config`, so
  `bale config init` can still open and rewrite such a file; it applies
  at both layers; `bin/` restates the crafter's one-line scan rather
  than importing it, `SpellingTwinTest` pinning the two against one
  corpus (C's decisions 3 and 4, ratified). D wired the reader in, so
  the refusal bites from D; 005/69's disclosure in the crafter's note
  stays true.]
- `from_lines`' stale "at v0.1" marker — rides the next `bin/bale`
  touch.
  [2026-09-18: carrier now row 110.]
  [2026-09-19: consumed at `2026-09-19-board-110-held-admissions-007`
  (rider 2). Its pin moved with it: `tests/test_pack_guards.py` asserted
  the marker verbatim and was edited out of forecast, admitted at the
  prompt.]
- The crafter comment carrying a `board-96-…` sid string — tolerated
  by the guard; look at it in the doc sweep.
- BALE.md §5.6 stats prose (`--sid`, the five new keys) — input to
  99b.
- Proposals of the `2026-09-16-continue-plan-006` sitting's workers
  (105's 1–3; 69, the stats micro, 56+57, 106), dispositions: consumed
  — the in-process opener constants test (106); carried — the four
  precedence sentences and the §5.10 pin (doc sweep), the
  triple-quoted refusal (`bin/bale_config.py`), `from_lines`' marker
  (`bin/bale`), the crafter's sid-string comment (doc sweep), the
  BALE.md stats prose (99b), `_load_cli()` and `normalize()` (row
  109), and 47b's five riders (row 47). Anything not named here or on
  those rows stands as shipped.
- The stale comment on `depends_on.superseded_session` in `cmd_pack`
  ("carries no successor pointer"), stale since v0.3.23's reverse
  stamp — rides the next `bin/bale_pack.py` touch (row 104). From
  `2026-09-18-board-107-supersedes-clean-tree-004`'s notes.
  [2026-09-20: consumed at `2026-09-20-board-104a-context-pack-005`:
  the comment now describes both directions of the supersession lineage,
  with the stamp in the reverse-lineage block above it (104a's
  notes.md).]
- BALE.md §8.8 trigger-list sentence for the stamp sweep — input to
  99b. Text verbatim from
  `2026-09-18-board-107-supersedes-clean-tree-004`'s Proposals:
  "…pack's session closes (the read-only sweep and the supersession
  close, §7.2), including the supersession's reverse-lineage stamp on
  the parent record, swept as its own
  `[bale sweep <parent>] superseded_by <child>`
  commit once the child sid exists…"
- Whether the shape sentence's three homes converge on one wording:
  TARBALL.md §5.10 says "the worker" and carries section pointers;
  CLAUDE.md §3 and the opener say "Claude". Rides row 104's
  kind-conditional rewrite or the doc sweep. From
  `2026-09-18-board-109-harness-micro-002`'s notes.
  [2026-09-19: closed as moot: the shape sentence is retired
  (`2026-09-19-opener-reword-docs-005`), and its fragments are pinned
  absent.]
- The three remaining provenance leftovers in `tools/craft_response.py`
  (lines 108, 359, 544 at that session) — rides the next crafter
  session; and whether `fold-in: <NNN>'s accepted proposal`-style
  citations deserve a deny shape — unscheduled, specimen survey first.
  Both from `2026-09-17-guard-maintenance-006`'s Proposals, ratified at
  the 2026-09-18 sitting.
- A suite-level pin that `tools/craft_response.py` and
  `tools/response_lint.py` stay stdlib-only with no network import,
  since the opener now says so in the operator's voice — 105's Proposal
  2, which close 11 under-recorded, as its worker warned it might (item
  3 of close 11's notes.md). Accepted 2026-09-18; carrier row 104 (a
  guess that 104 will hold `tests/test_pack_opener.py`). This master
  did the check by hand — read the crafter's imports before running it
  — which is the opener's sentence working as written.
  [2026-09-20: row 104 cut in two. The 004 desk's cut put this pin in
  104b; the 006 desk's registry dispatch names three other entries for
  104b and not this one, so whether 104b carries it is for its notes.md
  to say.]
  [2026-09-20: consumed at `2026-09-20-board-104b-pack-telemetry-008`,
  by its item 4, and the carrier question closed with it: the pin
  already existed. By 104b's notes.md, board 69 (d) landed it as
  `ToolsHermeticPin` in `tests/test_craft_response.py`, covering
  non-stdlib and relative imports, network-capable modules, process and
  FFI escape hatches, `__import__`, `import_module`, `exec` and `eval`,
  with a walker self-test; `-k stdlib_only` selected nothing only
  because of its method names. 104b renamed its five methods
  `test_stdlib_only_*` and changed no assertion, rather than write a
  second walker. Accepted at the `2026-09-20-continue-plan-009` desk
  (ruling 4). This entry asked for a pin the tree already had (§6 entry
  188).]
- Proposals of the `2026-09-18-continue-plan-001` sitting's workers
  (107, 109, 47b), dispositions: 107's 1 → the pack-json key (row 104),
  2 → 99b (the §8.8 entry above); 109's 1 → row 111, 2 → row 110, 3 →
  §7 (the include-authoring rule); 47b's 1 → row 110, 2 → row 110's
  riders, 3 → row 111, 4 → §7 (the same rule). Anything not named here
  or on those rows stands as shipped.
- PLANNER.md §5 step 5's retry clause: rides the next `docs/PLANNER.md`
  touch (row 37's rider session is the natural carrier). Text verbatim
  from `2026-09-19-board-110-held-admissions-007`'s Proposals:
  "**What:** PLANNER.md §5 step 5 could say the retry re-states the held
  apply's admissions, and that the line bale prints already carries
  them. **Why:** the step reads as if `--accept-checkpoint-change` is
  the only flag the retry needs. That was the operator-facing gap this
  board closed in code. The sentence isn't wrong, just silent. `docs/`
  is out of scope here, hence a proposal. **Scope hints:**
  `docs/PLANNER.md` §5 step 5 only; one clause."
  [2026-09-20: consumed at `2026-09-20-board-37-compaction-read-side-003`,
  on the retry after its HOLD: step 5 now says the retry re-states "the
  held apply's admissions (none carries forward from a failed attempt,
  and the retry line bale prints already carries those admissions)"
  (37's notes.md).]
- The held admissions beside `held tarball:` in
  `format_hold_relay_planner`: rides the next `bin/bale_report.py`
  touch. Text verbatim from `2026-09-19-board-110-held-admissions-007`'s
  Proposals: "**What:** add the admissions to the planner relay block
  beside `held tarball:`. **Why:** the desk rules on a fixture defect
  without seeing that the held apply needed `--allow-out-of-scope`, and
  that is context the desk might weigh. Out of this goal, and small.
  **Scope hints:** `bin/bale_report.py` `format_hold_relay_planner`; its
  unit pins in `tests/test_apply_preflight.py` `HoldRelayUnitTest`."
  [2026-09-20: ride condition reworded at the
  `2026-09-20-continue-plan-006` desk, which declined the rider again at
  104b for the 001 desk's reason. The entry now "rides the next session
  whose forecast holds both `bin/bale_report.py` and
  `tests/test_apply_preflight.py`, an apply-side session; a pack-side
  touch of `bin/bale_report.py` does not carry it (declined at 37 and at
  104b)".]
  [2026-09-21: a source of wave 10's rider micro too, by the
  `2026-09-21-continue-plan-002` desk's second-job section (§3, the
  continue-plan-005 block's sequencing bullet); the ride condition above
  still binds, so the micro carries it only if its forecast holds both
  files.]
  [2026-09-23: consumed at `2026-09-22-rider-micro-003`, whose forecast
  held both files: the held admissions ride the planner HOLD block
  through `relay_admission_rows`, the worker block byte-identical (Part
  2 of close 18's brief; the record's `change_paths`).]
- The `tests/harness.py` comment above `CLI_PATH`, to the past tense:
  rides the next holder of that file (row 113's session may be it). Text
  verbatim from `2026-09-19-board-111-tests-smalls-008`'s Proposals, its
  nested markers flattened: "**What:** refresh `tests/harness.py`'s
  comment block above `CLI_PATH` (~437–449). It says the shape
  "reconciles the two ad-hoc copies already in the tree" and ends
  "Adopting it in those two suites is left to them — neither is in this
  row." **Why:** after this response those copies are gone, and the
  comment reads as pending work. Its history sentence (what the shape
  reconciled) is still worth keeping, in the past tense. I didn't edit
  it because `harness.py` is not forecast and the goal doesn't require
  it. **Scope hints:** `tests/harness.py` only, comment text only. It
  can ride any later row that holds that file."
  [2026-09-19: consumed at `2026-09-19-board-113-dotted-run-form-011`,
  as a rider on row 113's `tests/harness.py`: the comment is in the past
  tense, keeps its history sentence, and now ends "Both suites adopted
  it at board 111, and the two copies are gone".]
- The lint warning when a request's `readme` key is non-null and
  `docs_read` omits `README.md`: accepted at the 009 open; rides the
  next `tools/` touch. Text verbatim from
  `2026-09-19-opener-reword-code-004`'s Proposals, its nested markers
  flattened: "**What:** Let `tools/response_lint.py` warn when a
  request's `readme` key is non-null but the response's
  `feedback.self_reported.docs_read` doesn't list `README.md`. **Why:**
  The key exists so a worker learns a brief exists. The specimen that
  motivated this session never opened the README, and the lint could
  make that visible in telemetry. **Scope hints:** Touches `tools/`,
  which is out of scope here, and only makes sense after this lands and
  requests carry the key."
  [2026-09-23: consumed at `2026-09-22-tools-micro-002`: under
  `--request` the lint warns `README_NOT_IN_DOCS_READ` (its claim "lint
  --request warns on README.md absent from docs_read", observed and
  `agree`).]
- Consolidate §7's include-authoring bullets into one: rides the next
  MASTER.md regeneration (a rewording, so never an insertions-only
  close). Close 12's Proposal 1, from
  `2026-09-19-sitting-close-deltas-12-001`'s notes.md, ratified at the
  009 open; text verbatim: "**What:** consolidate §7's include-authoring
  rules into one bullet at the next MASTER.md regeneration. Today they
  are spread across three bullets: the four standing, the 09-15
  fixture-consumer rule, and this close's `bale.toml`/`claude/changelog`
  rule. **Why:** the brief counted "the fifth" and the doc holds six. A
  desk that counts from one bullet will miscount again. **Scope hints:**
  `claude/MASTER.md` §7 only. This is a rewording, so it belongs to a
  regeneration rather than an insertions-only close." Close 13 adds a
  fourth such bullet (the repo-root `README.md` rule), which is the
  Proposal's point.
- Proposals of the `2026-09-19-session-fix-002` and
  `2026-09-19-continue-plan-006` sittings' workers (004, 005; 110, 111)
  and of close 12, dispositions: 004's → the lint rider (entry above);
  005, none, its four "please check" items disposed in close 13's first
  block; 110's 1 → the PLANNER.md §5 entry above, 2 → the
  `format_hold_relay_planner` entry above; 111's 1 → the
  `tests/harness.py` entry above, 2 → row 113; close 12's 1 → the
  regeneration entry above, 2 → applied by the 009 desk to close 13's
  checkpoint. Anything not named here or on those rows stands as
  shipped.
- The three redundant `tests/`-on-path guards: accepted at the 009
  sitting and split. The guard in `tests/test_craft_response.py`'s
  `ExchangeBlockParity.setUpClass` rides row 37 if row 37's cut holds
  that file, and the file's next holder otherwise (row 37's re-scope
  makes "otherwise" likely). The guards in `tests/test_doc_crossrefs.py`
  and `tests/test_sanctioned_pairs.py` ride each suite's next touch;
  both suites are 0755, so that session's `apply.sh` needs a
  `chmod +x` for each. Text verbatim from
  `2026-09-19-board-113-dotted-run-form-011`'s Proposals, its nested
  markers flattened: "**What:** drop the now-redundant
  `tests/`-on-path guards in `test_doc_crossrefs.py` and
  `test_sanctioned_pairs.py`, and the one in `test_craft_response.py`'s
  `ExchangeBlockParity.setUpClass`.
  **Why:** the package init does their job in the dotted form, and the
  other two forms never needed them. They're harmless, since each
  inserts only when absent. I left them because all three files are
  outside this forecast, and the brief makes `test_craft_response.py`
  row 37's. **Scope hints:** the craft one rides row 37. The two doc-pin
  suites are 0755, so an `apply.sh` `chmod +x` is needed for each."
  [2026-09-20: row 37's cut did not hold `tests/test_craft_response.py`
  (its forecast, from its record), so the craft guard rides that file's
  next holder.]
  [2026-09-23: the craft third consumed at `2026-09-22-tools-micro-002`:
  the `ExchangeBlockParity` path guard is gone and the class passes
  dotted (its claim of that name, observed and `agree`). The two
  doc-suite guards still ride each suite's next touch; the tools micro's
  Proposal 1 is those two, already here (close 18's dispositions
  entry).]
- `packed_at` on a pack's `opened` telemetry attempt: accepted at the
  009 sitting as a rider on row 104, which holds `bin/bale_pack.py` and
  the schemas. Close 13's Proposal 1; text verbatim from
  `2026-09-19-sitting-close-deltas-13-010`'s notes.md: "**What:** stamp
  `packed_at` into a pack's `opened` telemetry attempt, or into the
  record's top level. **Why:** closes 12 and 13 both had to reason about
  a master's pack second from `created_at`. This sitting showed the gap
  between them is sometimes zero and sometimes one second, so no fixed
  lag recovers it. Worker records carry `packed_at` only inside
  `feedback.mechanical.provenance`, which a read-only master never
  produces. **Scope hints:** `bin/bale_pack.py`'s telemetry open; the
  telemetry record schema. It is additive, and needs a named consumer
  per DOCS.md §9's telemetry rule: the close desk's reconstruction."
  Close 14 adds a third specimen: the 009 master's record reads
  `created_at` 03:12:21Z against a `packed_at` of 03:12:19Z by the 009
  desk's account of its own manifest, a lag of two seconds.
  [2026-09-20: carrier now 104b, dispatched by the
  `2026-09-20-continue-plan-006` desk as
  `2026-09-20-board-104b-pack-telemetry` beside close 15. A fourth
  specimen: 104a's record reads `created_at` 01:24:59Z against a
  `packed_at` of 01:24:58Z in its echoed provenance, one second. On a
  desk's account, the 001 master's record opens at 00:17:08Z against the
  00:17:07Z its brief gives as its `packed_at`; close 14's and 37's are
  equal to theirs.]
  [2026-09-20: consumed at `2026-09-20-board-104b-pack-telemetry-008`
  (0.4.40): `packed_at`, the request manifest's `provenance.packed_at`
  verbatim, rides the `opened` attempt's copy of provenance; the
  registry-side `provenance.json` stays the pair, and a manifest with no
  usable `packed_at` leaves the attempt with the pair alone, logged (its
  notes.md; §5). Named consumer, in the schema's words by 104b's
  notes.md: the close desk's reconstruction of a sitting. Two more
  specimens from before it landed: 104b's own record reads `created_at`
  03:08:02Z against a `packed_at` of 03:08:01Z in its echoed provenance,
  and the `2026-09-20-continue-plan-009` master's 03:08:08Z against the
  03:08:07Z its desk gives. First live records:
  `2026-09-20-board-103-probe-design-010`, three seconds (03:52:14Z
  against 03:52:11Z), and `2026-09-21-board-103-probe-design-001`, one
  second (§6 entry 194).]
- The closing pack's sid on a swept or superseded attempt: accepted at
  the 009 sitting as a rider on row 104. Close 13's Proposal 2; text
  verbatim from `2026-09-19-sitting-close-deltas-13-010`'s notes.md:
  "**What:** when a pack closes a session as a side effect (the
  read-only sweep, a supersession close), stamp the closing pack's own
  sid on the closed attempt. **Why:** 002's and 006's closures are
  attributed to "a pack" in this close, because no record says which.
  The brief's attributions come from desk memory, which is exactly what
  an unrecorded sitting lacks (entry 164). **Scope hints:** the pack
  path's sweep and supersession close (in `bin/bale_pack.py` or
  `bin/bale`; I have not seen the code); one optional field on the
  attempt." The 009 master's closure is a third specimen (§6 entry
  174).
  [2026-09-20: carrier now 104b, dispatched as above. The 006 desk read
  the code: a superseded attempt has carried the child's sid as
  `superseded_by` since 0.3.23, so only the read-only sweep's closure
  lacks it, and that sweep runs before the new sid is minted; 104b's
  brief says so. Two more specimens: the 001 master's closure at
  00:50:20Z and the 004 master's at 02:41:52Z, the latter one second
  before the 006 pack's `packed_at`, as a sweep that runs before the
  mint would read.]
  [2026-09-20: consumed at `2026-09-20-board-104b-pack-telemetry-008`
  (0.4.40), as `swept_by`: the read-only sweep still runs before the sid
  is minted, and once it is minted the pack stamps `swept_by` on each
  swept session's latest `closed-read-only` attempt and commits each
  rewrite as its own sweep event, board 107's fix applied to this sweep.
  The supersession half was already met by `superseded_by`, and 104b
  added nothing beside it. A stamp that fails, or a pack that aborts
  between the sweep and the sid, leaves the field absent, which reads as
  "sweeping pack unrecorded" (its notes.md; §5). The 006 master's
  closure at 03:08:07Z, swept by a 0.4.39 pack, is the last specimen
  without it; the `2026-09-20-continue-plan-009` master's at 03:52:11Z
  is the first with it (§6 entry 194).]
- Proposals of the `2026-09-19-continue-plan-009` sitting's workers
  (close 13; 113), dispositions: close 13's 1 → the `packed_at` entry
  above, 2 → the closing-pack sid entry above, both riding row 104;
  113's 1 → the path-guards entry above, split between row 37 (or the
  craft suite's next holder) and the two doc-pin suites' next touch;
  113's 2 (the dotted run form advertised in every suite docstring) →
  declined as cosmetic, unscheduled. Anything not named here or on
  those rows stands as shipped.
- 104a's Proposals 1 to 3: accepted at the
  `2026-09-20-continue-plan-006` desk ([1]) and riding 104b, which holds
  `bin/bale_pack.py` and `bin/bale_report.py`; 2 is a droppable last
  rider, and `validate.sh` joined 104b's forecast for 3. Proposal 1 was
  written for "after 104b lands"; riding 104b itself is the desks' cut,
  not the worker's. Text verbatim from
  `2026-09-20-board-104a-context-pack-005`'s notes.md, its nested
  markers flattened: "1. **Home the context report in
  `bin/bale_report.py`.** What: once 104b releases the file, move
  `format_context_pack_json` and the `context-packed` outcome word into
  `bin/bale_report.py`. Why: that module's `format_pack_json` docstring
  says the outcome vocabulary is owned there. Today the word lives in
  `bin/bale_pack.py`, which honestly breaks that one-home note; BALE.md
  §7.8 says so. Scope hints: `bin/bale_pack.py`, `bin/bale_report.py`,
  BALE.md §7.8. Only after 104b lands. 2. **Extract the cap/breach
  loop.** What: pull the soft/hard/`--force` breach loop into one helper
  called by both `cmd_pack` and `cmd_pack_context`. Why: it is now
  duplicated in compact form. The copy is faithful today, but two
  copies drift. Scope hints: `bin/bale_pack.py` only. The existing pack
  suites and `tests/test_context_pack.py` cover both callers. 3.
  **`validate.sh` should check `pack --help` mentions `--context`.**
  What: add `--context` to the install self-check's "pack --help
  mentions" list. Why: the list enumerates pack's flags, and
  `validate.sh` was not in this forecast. The suite pins the help
  listing meanwhile. Scope hints: `validate.sh`, one line."
  [2026-09-20: consumed at `2026-09-20-board-104b-pack-telemetry-008`:
  Proposal 1 (`format_context_pack_json` and the `context-packed`
  outcome word now live in `bin/bale_report.py`, output byte-identical,
  BALE.md §7.8 updated) and Proposal 3 (`validate.sh`'s "pack --help
  mentions" list gains `--context`, 92 checks). Proposal 2, the
  droppable rider, was not taken and is back on this list under its own
  entry, at the list's end.]
- A context-pack line in `bale status`: 104a's Proposal 4, unscheduled,
  registry only, by the 004 desk's recommendation as ratified at the 006
  desk. Text verbatim from `2026-09-20-board-104a-context-pack-005`'s
  notes.md, its nested markers flattened: "4. **Consider a context-pack
  line in `bale status`.** What: optionally, have `bale status` mention
  a present `context-*.tar.gz` in the outbox. Why: today it is
  deliberately invisible there. That is right for session state, but an
  operator hunting for "the tarball I made" gets no pointer. Scope
  hints: `bin/bale` status report, `bin/bale_report.py`. Low priority."
- Proposals of the `2026-09-20-continue-plan-001` and
  `2026-09-20-continue-plan-004` sittings' workers (close 14, 37; 104a),
  dispositions: close 14, none; 37, none; 104a's 1 to 3 → the
  Proposals 1 to 3 entry above, riding 104b; 104a's 4 → the `bale status` entry above,
  unscheduled. Anything not named here or on those rows stands as
  shipped.
- A cause on a `rejected` attempt: rides the next apply-side telemetry
  touch (the apply refusal path and the telemetry record schema). Close
  15's Proposal 1, sent here at the `2026-09-20-continue-plan-009` desk
  (ruling 4). Text verbatim from
  `2026-09-20-sitting-close-deltas-15-007`'s notes.md, its nested
  markers flattened: "1. **Stamp a cause on a `rejected` attempt.**
  What: when apply refuses a tarball, record why on the attempt, e.g.
  the refusal's first line or a short code. Why: 37's `rejected` attempt
  carries no cause, admission or validation. Close 15 had to leave it as
  two readings (§6 entry 187), and it is entry 174's gap on the apply
  side. Scope hints: the apply refusal path and the telemetry record
  schema. It is additive. Named consumer: the close desk's
  reconstruction, per DOCS.md §9's telemetry rule. I haven't seen the
  code. It would sit naturally beside 104b's `packed_at` and
  closing-pack-sid riders, but 104b is pack-side, so this probably wants
  an apply-side carrier."
  [2026-09-21: a source of wave 10's rider micro, which the next master
  authors (§3, the continue-plan-005 block's sequencing bullet), beside
  close 16's Proposal 1 and the findings' §8 item 2 (entries below).]
  [2026-09-23: consumed at `2026-09-22-rider-micro-003`, 0.4.41: a
  `rejected` attempt carries `cause`, the first non-blank line of the
  `SystemExit` that `fail()` now raises, `exit_cause` falling back to
  `exit <n>` (Part 2 of close 18's brief).]
- A `swept_by` line in the `bale stats` dossier: rides the next
  `bin/bale_stats.py` holder. 104b's Proposal 1, sent here at the
  `2026-09-20-continue-plan-009` desk (ruling 4). Text verbatim from
  `2026-09-20-board-104b-pack-telemetry-008`'s notes.md, its nested
  markers flattened: "1. **A `bale stats` dossier line for `swept_by`.**
  What: render "swept by <sid>" beside the existing "superseded by" line
  in the per-session dossier, and carry the field in the attempt view.
  Why: `_attempt_view` in `bin/bale_stats.py` already surfaces
  `superseded_by` by name. `swept_by` now has the same meaning for the
  other pack-side close, but the drill-down cannot show it. Scope hints:
  `bin/bale_stats.py`, `bin/bale_report.py` (the dossier renderer), and
  `tests/test_stats_drilldown.py`."
  [2026-09-21: a source of wave 10's rider micro, which the next master
  authors (§3, the continue-plan-005 block's sequencing bullet), beside
  close 16's Proposal 1 and the findings' §8 item 2 (entries below).]
  [2026-09-23: consumed at `2026-09-22-rider-micro-003`: the dossier
  renders `swept by <sid>` with no colon, the 001 desk's pin where the
  sibling line has one (the dossier-colon entry below), and renders
  `cause` and `bundle` too.]
- The cap/breach loop in `bin/bale_pack.py`: 104a's Proposal 2, the
  droppable last rider on 104b, not taken there and back on this list,
  in its worker's words: "The droppable rider (cap-loop extraction) was
  not taken. It goes back to the registry." Rides the next
  `bin/bale_pack.py` holder, still droppable. Its text is verbatim in
  the "104a's Proposals 1 to 3" entry above.
- The `docs/CLAUDE.md` §11.4 pointer: the part of row 37 that was not
  built, since 37 did not hold the file (row 37's DONE bracket). The
  2026-09-19 re-scope asked for a pointer in §11.4 at the crafter's
  bailout kind (the 009 desk's light block of that date, [2], in §3);
  row 37's bracket of the same date found §11.4 already routing to
  TARBALL.md §5.6 for the shape, with §5.6.1 naming
  `tools/craft_response.py --kind bailout --write`, and says the pointer
  "shrinks to at most a clause and may be nothing". Rides the next
  `docs/CLAUDE.md` holder, which decides between the clause and nothing
  and closes this entry either way. No entry carried it until the
  `2026-09-20-continue-plan-009` desk asked for the check and the
  `2026-09-21-continue-plan-002` desk made it.
  [2026-09-21: closed at `2026-09-21-board-103-doc-lane-006` with the
  clause, not with nothing. §11.4's sentence ending at `TARBALL.md`
  §5.6.1 now continues "which also mechanizes the whole artifact set:
  the crafter emits it, so a bailing worker fills judgment, never
  shape." It names no flag, so §5.6.1 stays the one home of
  `--kind bailout --write` (the doc lane's notes.md, "The rider: the
  clause, not nothing"; checked in the landed CLAUDE.md at close 17).]
- A failed oracle control exits 2, for PLANNER.md §4: a rider for the
  next `docs/PLANNER.md` holder, so that §5's contract of 2026-09-20
  gets its doc home. One bullet in §4, Checkpoint Authoring: a
  checkpoint's failed control exits 2, not 1 and not a probe failing by
  name, with the reason the `2026-09-20-continue-plan-009` desk gave
  (bale reads exit 2 as a defective oracle at `bale open` and as the
  checkpoint side on the hold card, and TARBALL.md §7.5 gives 2 to "the
  script itself errored"). Ruled by the operator's "as assumed" to that
  desk's light block one, [2]. PLANNER.md is a global doc, so the bullet
  cites only the five docs, the two tools and bale's own verbs.
  [2026-09-21: landed at `2026-09-21-split-transition-unconditional-007`
  as a bullet in PLANNER.md §4, "**A failed control exits 2.**", its
  three facts verified by that worker against shipped bytes (its
  notes.md, decision 6). It cites TARBALL.md §7.5 and bale's verbs only.
  That §7.5 is written about `validation.sh` and never says it governs
  the checkpoint script too is the worker's Proposal 1, an entry below;
  §5's contract carries a matching bracket.]
- Proposals of the `2026-09-20-continue-plan-006` and
  `2026-09-20-continue-plan-009` sittings' workers (close 15; 104b),
  dispositions, by ruling 4 at the 009 desk: close 15's 1 → the
  `rejected`-cause entry above, riding the next apply-side telemetry
  touch; 104b's 1 → the `swept_by` dossier entry above, riding the next
  `bin/bale_stats.py` holder. Returned with them: 104a's 2 → the
  cap/breach entry above. 104a's 4 stays on the `bale status` entry,
  unscheduled. The 009 sitting dispatched no worker of its own: 103's
  design sitting was read-only, and what it proposes is close 17's.
  Anything not named here or on those rows stands as shipped.
- Close 16's Proposal 1, the bundle on an `opened` attempt: rides wave
  10's rider micro, since it shares the telemetry schema; accepted at
  the `2026-09-21-continue-plan-002` desk (its ruling 7, by light block
  three's [2]). The operator accepted it into that micro on the desk's
  word with no code read, so §6 entry 188's rule binds the desk that
  authors the micro. Text verbatim from
  `2026-09-21-sitting-close-deltas-16-004`'s notes.md, its nested
  markers flattened: "1. **Record the bundle an `opened` attempt came
  from.** What: when a session is opened from a bundle, stamp the
  bundle's stem, or its brief's sha256, on the `opened` attempt. Why:
  row 103's bracket has to say that which revision either open used "is
  in no record". Two revisions and a stray bundle sat side by side at
  the 009 desk, and the two 103 records cannot say which one ran.
  `packed_at` and `swept_by` closed the same kind of gap one wave ago
  and were read at the very next close (entry 194). Scope hints:
  `bale open`'s pack replay and the telemetry record schema. Additive.
  Named consumer: the close desk's reconstruction, per DOCS.md §9's
  telemetry rule. I have not seen the code."
  [2026-09-23: consumed at `2026-09-22-rider-micro-003`, 0.4.41: an
  `opened` attempt from a bundle carries `bundle`, keys `stem`,
  `brief_sha256` (required), `checkpoint_sha256` and `manifest_sha256`,
  `"unreadable"` on a failed re-read. First read at close 18: the 004,
  successor and 005 records carry it, and W1 to W3's; the two micros'
  own `opened` attempts predate it (§3, the continue-plan-001 block).]
- Close 16's Proposal 2, the standing line's place in a master's brief:
  born closed. Accepted at the `2026-09-21-continue-plan-002` desk (its
  ruling 7) as desk practice from its next brief on, with a rider for
  the next `docs/PLANNER.md` holder. The rider landed at
  `2026-09-21-split-transition-unconditional-007`, in PLANNER.md §3,
  "**A master's brief keeps the ratified order inside its sitting
  record.**", said generically; §3 rather than §6 was that worker's call
  (its notes.md, decision 5), ratified at the
  `2026-09-21-continue-plan-008` desk. It had no entry before this one,
  so the `2026-09-21-continue-plan-005` desk recorded it as landed
  rather than close an entry it never had. Text verbatim from
  `2026-09-21-sitting-close-deltas-16-004`'s notes.md, its nested
  markers flattened: "2. **Give the standing line a fixed place in a
  master's brief.** What: a brief convention: a master's brief carries
  the standing line inside its sitting record, not under "Second job".
  Why: two closes running, the byte-for-byte quotation of a
  predecessor's brief has stopped at "the line before its Second job",
  and the standing line sat past it (entry 177's second specimen, and
  this close's 006 block). It cost nothing this time only because the
  line has not changed since 2026-09-19. Scope hints: `docs/PLANNER.md`
  §3 or §6, one sentence, or just the desks' practice. It could ride the
  same `docs/PLANNER.md` holder as the exit-2 rider."
- The findings' §8 items 1 to 4, the two micros' sources: items 1, 3 and
  4 are the tools micro's, and item 2 joins the rider micro, whose
  telemetry schema it shares (merge or serialize). Triaged at the
  `2026-09-21-continue-plan-002` desk and carried in its brief; that
  desk read no code for them, so every file list is a guess until the
  authoring desk reads it (§6 entry 188). Items 5 to 7 are row 119. Text
  verbatim from `board-103-wave1-findings.md` §8 (the operator's file,
  not in this repo), its first four bullets, flattened: item 1,
  "`response_lint.py --emit-feedback-mechanical` exits 1 on a seeded
  block, the input it exists to refresh. A worker chaining with `&&`
  skips the paste."; item 2, "A relay trailer refusal writes no
  telemetry: both Sonnet records read `['opened', 'applied']`. The
  wave's cleanest separator is invisible to stats. The refusal message
  could also say when re-serializing the parsed body with ASCII escaping
  reproduces the trailer, which is a ten-line check and names the fault
  instead of "truncated or was edited"."; item 3, "The lint cannot see
  `resolved_scope`. A `--request` flag would let it warn on a
  `changes[]` path outside the forecast with no `forecast_departures`
  entry."; item 4, "`craft_response.py --validation-epilogue` emits the
  definitions and the call in one stream; sonnet5-b pasted them
  together."
  [2026-09-23: items 1, 3 and 4 consumed at
  `2026-09-22-tools-micro-002`: emit mode exits 0 once it wrote, 1 with
  nothing to paste; the lint's `--request` flag, warning
  `FORECAST_DEPARTURE_UNDECLARED`; the epilogue's stderr log opening
  "COMBINED emission" and naming `--fragment`, stdout unchanged.]
  [2026-09-23: item 2 consumed at `2026-09-22-rider-micro-003`: a
  `relay-refused` attempt, with `cause`, for every refusal of the input
  itself, and the re-escape check naming the carrier's unescaping while
  still refusing.]
- The crafter seeds `forecast_departures`: joins the tools micro's
  sources, by the operator's "as assumed" to the
  `2026-09-21-continue-plan-005` desk's light block four, [1]. Not
  tools-only: TARBALL.md §5.4 now says "The crafter does not seed the
  field, so it is the worker's to add", so the micro holds
  `docs/TARBALL.md` too or leaves that one-line edit to the file's next
  holder. Text verbatim from `2026-09-21-board-103-doc-lane-006`'s
  notes.md, its first Proposal, flattened: "**What:** seed
  `forecast_departures` from the crafter when `--request` is given. It
  already reads the request manifest, which carries `resolved_scope`;
  any `files/` path outside that forecast could be emitted as a
  `{path, why: ""}` stub, invalid until filled, like the other
  sentinels. **Why:** Delta 2 tells workers the field exists; this would
  make it appear on its own exactly when it applies. The docs now say
  "the crafter does not seed the field", which is true at 0.4.40 and
  would need the matching one-line edit in §5.4. **Scope hints:**
  `tools/craft_response.py`, its suite, §5.4's new sentence. A tool
  change, so out of this session's scope by the brief."
  [2026-09-23: consumed at `2026-09-22-tools-micro-002`, with TARBALL.md
  §5.4 reworded in the same session: given `--request`, the crafter
  seeds a `forecast_departures` stub for every `changes[]` path outside
  `resolved_scope`, deletions included. The brief's "files/ path" gave
  way to `changes[]`, the schema's word, a flagged deviation ratified at
  the 001 desk.]
- One statement of what each courier carries, for TARBALL.md §5.9: rides
  the next holder of `docs/TARBALL.md` §5.9, by the same ruling. Text
  verbatim from `2026-09-21-board-103-doc-lane-006`'s notes.md, its
  third Proposal, flattened: "**What:** §5.9.2's first paragraph and the
  exchange-record paragraph could say once, plainly, which artifacts
  each courier carries. Today that is assembled from three places.
  **Why:** writing Delta 6 meant reconstructing it. Small; fits the next
  §5.9 holder."
  [2026-09-23: stays. TARBALL.md §5.9 was hash-pinned byte-identical at
  `2026-09-22-tools-micro-002`; the tools micro's Proposal 3, on §5.2.2,
  rides the same `docs/TARBALL.md` holder (an entry below).]
  [2026-09-24: consumed at
  `2026-09-23-board-43-tarball-s5-compression-008`, bumpless on 0.4.43:
  VERBATIM-2 is §5.9.2's second paragraph and the one place couriers are
  described, its claim observed and `agree`. Retired; the "stays" above
  is closed.]
- TARBALL.md §7.5's exit codes bind the checkpoint script too: rides the
  next `docs/TARBALL.md` holder, by the operator's "as assumed." to the
  `2026-09-21-continue-plan-008` desk's light block one, [2]. It is the
  gap under PLANNER.md §4's exit-2 bullet, which leans on §7.5 while
  §7.5 speaks of `validation.sh` alone. Text verbatim from
  `2026-09-21-split-transition-unconditional-007`'s notes.md, its nested
  markers flattened: "1. **Say once, in TARBALL.md, that §7.5's exit
  codes bind the checkpoint script too.** What: one sentence in §7's
  blind-checkpoint paragraph or in §7.5. Why: `bin/bale_open.py` and the
  hold judge both treat the checkpoint's 0/1/2 as §7.5's table, and
  PLANNER.md §4's new bullet now leans on that reading, but §7.5 as
  written is about `validation.sh` alone. A planner following the
  pointer lands on a section that doesn't mention their script. Scope
  hints: `docs/TARBALL.md` §7 or §7.5, one sentence; no pair involved."
  [2026-09-23: consumed at `2026-09-22-tools-micro-002`, which landed
  its own VERBATIM sentence in TARBALL.md §7.5 (its claim "VERBATIM-1
  lands word for word in TARBALL.md 7.5 after the anchor", observed and
  `agree`).]
- Suite pins for the riders' two phrases: rides the next
  `tests/test_doc_crossrefs.py` holder, by the same ruling; its worker
  allows that the answer may be a deliberate no. Text verbatim from
  `2026-09-21-split-transition-unconditional-007`'s notes.md, its nested
  markers flattened: "2. **Pin the riders' required phrases, if the desk
  wants them held.** What: `exits 2` in PLANNER.md §4 and
  `sitting record` in §3 have no suite pin; only this response's
  `validation.sh` asserts them. Why: `test_doc_crossrefs.py` is where
  single-doc content pins live, and it was out of this forecast.
  Authored wording around a required spelling usually gets no pin there,
  so this may be a deliberate no. Scope hints:
  `tests/test_doc_crossrefs.py`, two constants."
- A fence-aware `top_level_section()`: rides the next
  `tests/test_doc_crossrefs.py` holder, beside the phrase-pins entry
  above, by the `2026-09-23-continue-plan-006` desk's disposition,
  carried in close 19's brief. Text verbatim from
  `2026-09-23-board-43-tarball-s5-compression-008`'s notes.md, its third
  Proposal, its nested markers flattened: "3. **Make
  `top_level_section()` fence-aware.** **What:** make it (and
  `subsection()`) skip `#` lines inside code fences, as `unfenced()` in
  the new class does. **Why:** on the base doc it truncated section 5 at
  the handoff template's `## Original goal`. It is harmless today only
  because no pin read section 5 whole. The next fenced example with a
  markdown heading in any doc repeats the trap."
- Proposals of the `2026-09-21-continue-plan-002` and
  `2026-09-21-continue-plan-005` sittings' workers (close 16; the doc
  lane; the split-transition fix), dispositions: close 16's 1 → the
  `opened`-attempt entry above, riding wave 10's rider micro, 2 → the
  born-closed entry above, landed in PLANNER.md §3; the doc lane's 1 →
  the crafter-seeding entry above, joining the tools micro, 2 → row 120,
  3 → the §5.9 courier entry above; the fix's 1 → the §7.5 entry above,
  2 → the phrase-pins entry above. The findings sitting was read-only;
  its Proposals and code items are disposed on row 103's bracket, rows
  114 to 119 and the §8 entry above. Anything not named here or on those
  rows stands as shipped.
- The cadence, for PLANNER.md §6: a rider for the next `docs/PLANNER.md`
  holder, landing §5's contract of 2026-09-22 in §6's "Sitting practice"
  bullet on masters. Ruled by the operator on 2026-09-22 at the
  `2026-09-22-continue-plan-001` desk, in that desk's rendering, and
  confirmed by his "as assumed" to the `2026-09-22-continue-plan-005`
  desk's light block one, [1]. The two sentences, byte-verbatim, one per
  line:
  More project work, less master grooming: an arc's design sitting authors its own wave's bundles once the operator ratifies the decomposition; no master sits between it and its workers.
  Closes are per wave, not per master. A master's last job is the wave's close, after its project work is dispatched.
  PLANNER.md is a global doc, so the bullet cites only the five docs,
  the two tools and bale's own verbs.
- The lint warns on a declared departure that is not one: rides the next
  `tools/` touch. The tools micro's Proposal 2, ratified at the
  `2026-09-22-continue-plan-001` desk; in that desk's words (Part 2 of
  close 18's brief): "2 (the lint warns on a declared departure that is
  not one: `path` inside `resolved_scope`, or naming no `changes[]`
  path) rides the next `tools/` touch".
  [2026-09-24: consumed at `2026-09-23-board-121-125-code-micro-007`,
  0.4.44, its first registry rider:
  `FORECAST_DEPARTURE_NOT_A_DEPARTURE`, a warning at the entry's own
  path, one code with two headlines, beside
  `FORECAST_DEPARTURE_UNDECLARED` in the `--request` pass. Retired.]
- §5.2.2 on the emitter: rides the next `docs/TARBALL.md` holder, beside
  the §5.9 courier entry above. The tools micro's Proposal 3, same
  ruling, in the same words: "3 (§5.2.2 says the emitter exits 0 once it
  writes, what `--request` enables, and whether `--fragment` becomes
  §7.3's documented default)".
  [2026-09-24: consumed at row 43's session but for its last clause.
  VERBATIM-3 follows §5.2.2's emitter workflow: the emitter exits 0 once
  it has written and 1 when there was nothing to paste, and `--request`
  lets the lint warn on an undeclared departure and the crafter seed the
  stubs. Whether `--fragment` becomes §7.3's documented default was not
  decided there, and row 43's Proposal 2 asks the same question; it
  merges here, by the 006 desk's disposition. The entry stays for that
  clause alone, riding the next holder of `docs/TARBALL.md` §7.3.]
- A `bale stats` read side for the rider micro's fields, and a closed
  cause vocabulary: unscheduled until a consumer is named. The rider
  micro's Proposals 1 and 3, same ruling, in the same words: "1 (a
  `bale stats` read side: `relay-refused` beside the drift refusals, a
  cause histogram keyed on the first-colon prefix) unscheduled until a
  consumer is named" and "3 (a closed `cause_code` vocabulary at the
  major `fail()` sites) unscheduled, beside 1".
- Stamp `handoff` on handoff-side opens: rides the next `bin/bale`
  holder. The rider micro's Proposal 2, same ruling, in the same words:
  "2 (stamp `handoff` on handoff-side opens: `command="handoff"` at
  `bin/bale`'s `persist_pack_session` call, plus
  `tests/test_provenance_at_open.py`) rides the next `bin/bale` holder".
  [2026-09-24: consumed at the micro, its third registry rider. The code
  had already landed and the code won: `cmd_handoff` passes
  `command="handoff"`, wired since rows 63/73 by
  `persist_pack_session`'s docstring. What landed is the test the entry
  names, in `tests/test_provenance_at_open.py`, and the telemetry
  schema's `command` description, which still called handoff reserved.
  Retired.]
- The dossier colon: rides the next `bin/bale_report.py` holder,
  droppable. The 001 desk's own, in its words: "the dossier colon
  (`swept by:` to match `superseded by:`; one character plus
  `RiderMicroDossierTest`), droppable, rides the next
  `bin/bale_report.py` holder".
  [2026-09-24: dropped. The micro held `bin/bale_report.py` for row 124
  and carried its three riders without this one, by the operator's "as
  assumed" to the `2026-09-23-continue-plan-006` desk's light block one,
  [3], which drops the dossier colon; the dossier's `swept by <sid>`
  line keeps no colon. Retired, reading "drops" as the entry's own
  "droppable" taken (close 19's notes.md).]
- The include rule for checkpoints, two halves: the §3.4 sentence rides
  the next `docs/TARBALL.md` holder, the crafter refusal the next
  `tools/` holder. The paired-desk sitting's item 3 [a], placed at the
  005 desk; the item stands verbatim in §3's 004 block. TARBALL.md §3.4
  says in one sentence that an `--include` may not name the checkpoint
  pattern's subtree, broader ancestors being fine and auto-excluded; the
  crafter refuses a `--pack-arg` under `[validation] base`'s prefix,
  extending its existing `bale.toml` read.
  [2026-09-24: both halves consumed. The crafter refusal at the micro,
  its second registry rider: `--bundle` refuses a stored `--include` or
  `--write` value naming the `[validation] base` checkpoint by pack's
  explicit-naming rule (the base, its `{sid}` basis, or a path under
  it), unless the argv carries `--allow-checkpoint-in-scope`; the
  entry's "`--pack-arg`" is those two flags in the stored argv. The §3.4
  sentence at row 43's session: VERBATIM-1, its own one-line paragraph
  directly after §3.4's checkpoint-configured paragraph, a placement
  ratified as made. Retired.]
- Three planner practices, one entry: rides the next `docs/PLANNER.md`
  holder. Item 5 [b; the §2 sentence a]: ledger tagging in §3, each
  ledger line carrying its verifying desk or sid and a file:line,
  re-tagged on re-verification, and the GUESS-label sentence in §2
  beside "a wrong fact is worse than a missing fact": a named unknown is
  not coverage for the unnamed check. Item 8 [a]: transcripts as a
  `--context` tarball beside a superseding request, cross-model pairing
  the follow-on once layers 1 to 4 land. The upward report's Proposal 4:
  a design sitting's `context_included` is its reads. Items 5 and 8
  stand verbatim in §3's 004 block; the report's text did not travel to
  close 18.
- A `light_blocks` count on the read-only closure attempt, prompted at
  sweep or unlock: unscheduled until a consumer is named. The mechanized
  half of the paired-desk sitting's item 6 [a mechanized, b as
  practice]; its practice half landed at W1
  (`2026-09-23-board-100-w1-doc-sweep-002`) as ruling 6's PLANNER.md §6
  bullet, a master's self-report in the sitting-close notes, count and
  disposition per block, and `light_blocks` stays the worker's field.
- Paired desks as a sitting kind: not taken. The paired-desk sitting's
  item 7 [ab] is recorded as evidence only (§6 entry 208), following the
  upward report's Proposal 1: the pattern that worked was a ledger plus
  a successor re-verifying where it builds.
- AGENT.md §11.7's "picker" wording, and W3's stamp mismatch in prose:
  rides the next `docs/AGENT.md` or `docs/TARBALL.md` holder. The upward
  report's follow-on row (d), as close 18's brief places it. §11.7's
  model-string column says the string is shown by the model picker and
  gives `unknown` when the picker is not visible, and W3's worker
  reported the string from its system prompt instead, ratified at the
  design sitting; and W3's `stamp_matched: false`, accepted per
  invocation, owes a prose mention at the next doc landing. The report's
  own text did not travel to close 18.
  [2026-09-24: W3's half recorded. A global doc cannot carry a project
  fact, so the prose mention of W3's `stamp_matched: false` landed in
  `2026-09-23-board-43-tarball-s5-compression-008`'s notes.md, its
  section "W3's stamp mismatch, mentioned", which names close 19 as the
  one to record it from there; this bracket is that record. The "picker"
  half stays, by the 006 desk's disposition. Wave 11 adds specimens:
  records spell one model two ways, the picker's name
  `anthropic:claude-opus-5.5` and the API string
  `anthropic:claude-opus-5-5` (§7).]
- A stable anchor for the registry's end: rides the next MASTER.md
  regeneration. Close 17's Proposal 1, carried standing in the 001
  desk's brief; that close's notes.md did not travel to close 18, so its
  text is not quoted. Close 18 inserted above
  `Landed 2026-08-05, non-board`, the line that ends the list today.
- A trail for planner-desk light blocks: close 17's Proposal 2, not
  quoted for the same reason. The paired-desk sitting gave it a live
  specimen, two blocks under one sid and no record (item 6; §6 entry
  208).
  [2026-09-23: landed at W1 in its practice half, ruling 6's PLANNER.md
  §6 bullet; the mechanized half is the `light_blocks` entry above,
  unscheduled.]
- Proposals of the `2026-09-22-continue-plan-001`,
  `2026-09-22-board-100-design-004`, `2026-09-23-board-100-design-001`
  and `2026-09-22-continue-plan-005` sittings' workers and desks, and
  close 17's, dispositions: the tools micro's 1 → the three-guards entry
  above, already here, 2 → the declared-departure entry above, 3 → the
  §5.2.2 entry above; the rider micro's 1 and 3 → the unscheduled entry
  above, 2 → the handoff-stamp entry above; the 001 desk's dossier colon
  → its entry above; the paired-desk items → §3's 004 block, rows 121 to
  123 and the entries above; the upward report's follow-on rows (a),
  (b), (c), (e) and (f) → rows 124, 126, 127, 125 and 128, (d) → the
  §11.7 entry above, and its Proposals 1 → §6 entry 208, 2 → row 125, 3
  → row 122, 4 → the `docs/PLANNER.md` entry above; close 17's 1 and 2 →
  their entries above. W1 to W3's own Proposals reached this close
  through that report, not first-hand. None of the riders queued at
  2026-09-22 was consumed by W1 to W3, which were authored before they
  were on the registry. Anything not named here or on those rows stands
  as shipped.
- A close brief that asks for a verbatim quote carries the text: rides
  the next `docs/PLANNER.md` holder, one sentence in §3. Close 18's
  Proposal 1, ratified as a §3 rider by the operator's "as assumed" to
  the `2026-09-23-continue-plan-006` desk's light block one, [2]. Text
  verbatim from `2026-09-23-sitting-close-deltas-18-005`'s notes.md, its
  nested markers flattened: "1. **A close brief that asks for a verbatim
  quote carries the text.** What: when a brief tells the close to quote
  something verbatim, the brief carries that text or the request ships
  the file. Why: this close was asked to quote the upward report's
  "Follow-on rows" and to quote row 126's recommendation from it, and
  neither traveled; the 005 desk had the file in hand. The same gap left
  close 17's Proposal texts unquotable. A brief that carries its
  quotations never meets this. Scope hints: `docs/PLANNER.md` §3, one
  sentence, for its next holder. Or just desk practice."
- PLANNER.md §4's rehearsal sentence: rides the next `docs/PLANNER.md`
  holder, two dispositions of the 006 desk that end in one line. Close
  18's call 5, ratified as the worker's alternative by the same block's
  [2]: the paired-desk sitting's item 2 interim doctrine as a one-line
  rider, the item's own words (§3's 004 block):
  Until it lands, PLANNER.md §4 doctrine: a desk with `bin/` in context rehearses the line in a fixture before delivery.
  Row 122 has since landed (0.4.45), so the interim is overtaken, and
  row 122's Proposal 2 retires it; text verbatim from
  `2026-09-23-board-122-rehearsal-verbs-009`'s notes.md, flattened:
  "**What:** Retire PLANNER.md §4's interim "rehearse in a fixture"
  doctrine. Replace it with one sentence: a desk with the operator's
  tree a probe away asks for `bale open --dry-run <bundle>` (or
  `--check` when the oracle is slow) before delivery, and a desk with
  `bin/` in context can still dress-rehearse in a scratch repo. **Why:**
  The row names the doctrine as the interim until this lands, and no
  registry entry carries the fixture rehearsal. The verbs replace it on
  the real tree, which is where the wave's include miss hid. **Scope
  hints:** PLANNER.md §4, one sentence. Only after 0.4.45 applies." The
  holder lands the replacement sentence; the interim sentence is carried
  here as the record of what it replaces.
- A gate's fixture builds its specimen off the forecast: rides the next
  `docs/PLANNER.md` holder, §4, beside the entry above. The micro's HOLD
  lesson, in the 006 desk's words as close 19's brief carries them:
  "Lesson, earned for PLANNER.md §4's next holder: a fixture that
  exercises a gate never builds its specimen through a surface in the
  session's own forecast." (§6 entry 214.)
- `*.pyc` and `*.pyo` basenames in the pack walk: rides the next
  `bin/bale_pack.py` holder, droppable. Text verbatim from
  `2026-09-23-board-121-125-code-micro-007`'s notes.md, its first
  Proposal, flattened: "**The pack walk has no `*.pyc` basename rule.**
  *What:* add `*.pyc`/`*.pyo` basenames to pack's baked-in exclusion.
  *Why:* the walk excludes `__pycache__` directories, but a bare `*.pyc`
  beside sources would ship. The response contract (TARBALL.md §5.1)
  already denies exactly those names on the way back, so the two sides
  are asymmetric. Python 3 does not write such files by default, so I
  left it alone rather than invent a leak. *Scope hints:* `bale_pack.py`
  `is_under_excluded_dir` and the §6.4 set; BALE.md's list."
- Scratch installs without the source tree's cache: rides the next
  `tests/harness.py` holder. The micro's second Proposal, flattened:
  "**The harness copies `bin/__pycache__` into every scratch install.**
  *What:* pass `ignore=shutil.ignore_patterns("__pycache__", "*.pyc")`
  in `tests/harness.py`'s `make_install` copytree. *Why:* scratch
  installs currently inherit whatever cache the source tree holds.
  Harmless today; a one-line fix. *Scope hints:* `tests/harness.py`,
  which was not in my forecast."
- The response schema's top-level description and the lint's vendored
  copy, in one change: rides the next session holding `schemas/` and
  `tools/` together. Row 43's first Proposal, flattened: "1. **Update
  the response schema's top-level description.** **What:** it still says
  "Field semantics live in TARBALL.md; this schema constrains only the
  universal envelope". After this pilot, several semantics live in the
  schema's own descriptions and section 5 points there. **Why:** a
  reader following the schema back to the doc and the doc back to the
  schema finds each deferring to the other. The description also carries
  `v0.`-era archaeology and the B1/B2 session letters. **Scope hints:**
  `schemas/response-manifest.schema.json` plus the vendored copy in
  `tools/response_lint.py`, in one change (the self-containment
  docstring's own warning). Not this session's forecast."
- The rehearsal spellings in TARBALL.md §3.4: rides the next
  `docs/TARBALL.md` holder. Row 122's first Proposal, flattened:
  "**What:** A `--dry-run` row in TARBALL.md §3.4's flag table, and a
  sentence on the two `bale open` rehearsal flags where §3.4 describes
  the bundle line. **Why:** §3.4 is the canonical flag surface, and
  `bale pack --help` points at it. A desk reading §3.4 won't learn the
  rehearsal exists. **Scope hints:** TARBALL.md §3.4 only, for the
  global docs' next holder."
- A machine form of the rehearsal report: parked, no consumer. Row 122's
  third Proposal, flattened: "**What:** Consider making the rehearsal
  report available as a `--json` line (for example `outcome:
  "rehearsed"` plus the rows as keys) if a desk tool ends up parsing it.
  **Why:** I refused the pair rather than invent a contract with no
  consumer. If `craft_response.py --bundle` ever wants to run a check
  itself, it will want a machine form. **Scope hints:**
  `bin/bale_pack.py` (`format_rehearsal_report`), `bin/bale_report.py`,
  and pack's `--json` key list in BALE.md §7.7."
- A staleness flag at reconciliation: consumer S6, row 129. The 45 arc's
  upward report, Proposal 1, filed at close 19 as a row and this entry
  by the operator's "as assumed" to the 006 desk's light block two, [2];
  the row carries the text.
- A "will create" forecast entry: consumer S6, row 130. The report's
  Proposal 2, same ruling; weighed against ADR-0015's existence rule,
  the entry a forecast and not a grant.
- Hot reads in every include set: consumer S6, row 131; PLANNER.md §6's
  second clause applied to runtime reads, for that doc's holder once S6
  takes it. The report's Proposal 3, same ruling.
- Plain-language brief framing: consumer S6, row 132, and a
  `docs/PLANNER.md` §3 rider as well, riding the holder beside close
  18's Proposal 1 above. The report's Proposal 4, same ruling: a brief
  says what a fixture is and why the operator is blind, in plain words.
- Probe timing, two numbers: consumer S6, row 133. The report's Proposal
  5, same ruling.
- The stemwell workers' own Proposals: held until S6, by the arc close's
  own decision (the upward report's "On-watch" and "What S6 receives"),
  and by the same block's [2] not filed singly. By session, from
  stemwell's notes.md: wave1, locale-independent ordering in `report`;
  wave2a, a sweep of stale `*.json.tmp` files; wave2b, one shared state
  reader, `stemwell/state.py`; wave3, `tools/gen_codec.py`'s `tomllib`
  against the declared 3.10 floor; wave5, a one-line failure on
  non-UTF-8 stem files and raw-input labels on `report --from-raw`'s
  errors. Wave5's third, `report`'s `Total: N ` trailing space, is moot:
  wave1 landed the fix. Six live, where the report counts "five" and
  lists six. Their home is stemwell's `claude/responses/`, not bale-src.
- Proposals of the `2026-09-23-continue-plan-006` and
  `2026-09-23-board-45-hostile-repo-design-010` sittings' workers and
  desks, and close 18's, dispositions: close 18's 1 → the verbatim-quote
  entry above, 2 → close practice (§5, 2026-09-24), call 5 → the
  PLANNER.md §4 entry above; the micro's 1 → the `*.pyc` entry, 2 → the
  harness entry, 3 → consumed at row 122's session
  (`pack_argv_preflight` now runs `pack_pre_exchange_gates`), 4 →
  consumed across row 43's §3.4 sentence and row 122's BALE.md §6.7 and
  §8.9 paragraphs; row 43's 1 → the schema-description entry, 2 → the
  §5.2.2 entry's `--fragment` clause, 3 → the fence-aware entry beside
  the phrase pins; row 122's 1 → the §3.4 rehearsal entry, 2 → the
  PLANNER.md §4 entry, 3 → parked above; the 45 arc's upward report's
  Proposals 1 to 5 → rows 129 to 133 and their entries above; the
  stemwell workers' → held for S6. W3's stamp mismatch → recorded on the
  §11.7 entry. Anything not named here or on those rows stands as
  shipped.
- BALE.md sentences for 99b's true-up from the friction-points arc, five
  sets, each verbatim from its session's archived notes.md (nested
  markers flattened), routed to 99b by the 2026-10-03 and 2026-10-03/04
  desks; A's and E's reached the wave2-004 desk only as "verbatim in
  their notes", and the archive is where they were (§7). Rides 99b,
  behind the ruling queue's BALE.md entry.
  A, `2026-10-03-config-wizard-ui-002`: "**What (for the 99b true-up;
  BALE.md is out of scope here):** §3.6 step 2 should mention the review
  before writing and the `?` help. The §2 install-layout block (around
  line 186) lists `bin/bale_config.py` but neither `bin/bale_wizard.py`
  nor the other newer siblings. The command table row for `bale config
  init` (around line 500) could say "reviews the changes, then writes".
  **Why:** they describe the wizard's flow, which now includes a review
  gate. **Scope hints:** BALE.md §2, §3.6, the commands table."
  E, `2026-10-03-bale-cli-reference-003`: "**What.** Sentences for the
  99b BALE.md true-up (BALE.md is out of scope here): §3.3, after its
  first paragraph: "Beside them, every request carries `BALE_HELP.md`,
  the installed bale's `bale help` for every command. It is not an
  install file: `render_cli_reference()` writes it from `build_parser()`
  when the request is built, at a fixed 80 columns, so it is
  version-true by construction and identical from any terminal." §3.3,
  the pin sentence: append "and the generated reference's framing
  (everything outside its code fences) is scanned by the same guard's
  rendered group; the fenced help text is exempt pending the ruling on
  BALE.md citations in help strings." §6.1's shape block: add
  `BALE_HELP.md # generated by bale at build time: bale help for every
  verb`. The block is also missing `PLANNER.md`, which joined at
  v0.4.11; the true-up could add both. §7.5 step 3: append "and the
  generated CLI reference (`CLI_REFERENCE_NAME`), rendered by
  `render_cli_reference()` and written at the request's top level."
  §5.1: add "Every request carries the full set as `BALE_HELP.md`
  (§6.1)." **Why.** BALE.md describes the request shape and the build
  steps. Without these sentences it understates what ships from this
  version on. **Scope hints.** BALE.md only. It needs nothing from this
  session beyond the names above." And E's second: "**What.** Fold the
  ruling's eventual string pass over the 8 board citations too, not just
  the 24 BALE.md ones. **Why.** They travel in every request now and
  dangle just the same. A doc would fail the guard's board shape on
  them. **Scope hints.** `bin/bale`'s help strings. Once the citations
  are gone, the guard's rendered group could tighten to scan the bodies
  as well. `CliReferenceFramingSelfContainment` is where that would
  land."
  B, `2026-10-03-pack-wizard-ui-005`: "**BALE.md §7.3 sentences for the
  99b true-up.** For example: "The goal-less wizard draws through the
  shared wizard layer (`bale_wizard`): one item per question, headed by
  the flag that answers it, with the count re-derived when a read-only
  answer drops the forecast and checkpoint questions." "Enter at the
  slug question takes a slug derived from the goal." "`[bale]` log lines
  from the post-walk gates print after the README question.""
  C, `2026-10-03-wizard-defaults-006`: "**BALE.md sentences for the 99b
  true-up.** What: say that `[probe] clipboard_command` is per-machine
  (both layers, `x` suppresses, `effective_clipboard_command` is the
  reader), and that `bale config init` offers numbered alternatives on
  eight keys and in the `.baleignore` step, with Enter unchanged. Why:
  the brief routes `BALE.md` truing here as a Proposal, and BALE.md
  wasn't in this request."
  D, `2026-10-04-clipboard-paste-blocks-001`: "**What:** BALE.md true-up
  sentences for session 99b (BALE.md was out of scope here). Proposed
  sentences: "When `[probe] clipboard_command` resolves to a command for
  the repo a command runs in (project value, else global; `\"\"` at the
  project suppresses), bale copies every operator-side paste block as it
  prints it: pack's session opener (the lines between the scissor
  lines), `bale open`'s second-desk opener, `bale relay`'s exchange
  block, and `bale apply` / `bale retry`'s HOLD relay block named under
  `send first:` and its APPLIED relay block. Each copy prints one
  `[bale] clipboard:` line on stderr. A missing, failing, slow (10s) or
  unreadable command only skips the copy and never changes output or
  exit codes. Nothing is detected at run time." And: "`bale clipboard
  [--block NAME]` copies standard input the same way (exit 0 copied, 1
  not copied, 2 on a terminal stdin); the probe scaffold pipes its PROBE
  BEGIN/END block into it." And: "`bale status` shows a `probe
  clipboard` row: the command and its layer, suppressed, unset, or
  UNREADABLE with the accessor's reason." **Why:** the brief routes
  BALE.md wording to 99b. **Scope hints:** BALE.md's status and probe
  sections, plus a verb entry for `clipboard`."
  [2026-10-06: three more sets, the cleanup desk's wave, each verbatim
  from its archived notes.md (nested markers flattened), routed to 99b
  by the cleanup desk's brief and recorded at close 21. The key the sets
  above spell `[probe] clipboard_command` is `[clipboard] command` since
  the rename, the old spelling read as a legacy alias; C's and D's
  sentences predate that. log-hold, `2026-10-04-log-hold-003`:
  "**BALE.md true-up sentences** (BALE.md wasn't in this request): Where
  BALE.md describes the goal-less walk's quiet span: "From the walk's
  first question through its README question, bale holds its `[bale]`
  lines (bin/bale's `hold_log`/`release_log`): each line is journaled
  when logged and printed after the README question, in order; a refusal
  prints the held lines before its error line." In §7.7 (the
  tree-position echo) or wherever pack's pre-walk output is described:
  "On a terminal, the `[bale]` lines pack prints before the walk are
  word-wrapped to the terminal's width (80 on an 80-column terminal),
  continuation lines indented under the text; piped output and the
  session log keep each line whole." Where the read-only sweep's prompt
  is described: "On a terminal the sweep's y/N wraps to the terminal's
  width; Enter accepts, y or yes in any case accepts, any other answer
  declines without re-asking, EOF or ^C declines, and piped stdin
  declines without a prompt." Where the paste-block copy's
  unreadable-key behavior is described: "An unreadable key skips the
  copy with one `NOT copied` notice naming the reason; it is not an
  error of the command and is not journaled as one.""
  clipboard-key-rename, `2026-10-05-clipboard-key-rename-002`:
  "**BALE.md true-up sentences** (BALE.md is out of this request; the
  wording belongs wherever it names the key): §5's `clipboard` row and
  §8.9's clipboard notes, if they name `[probe] clipboard_command`: "the
  key is `[clipboard] command` at both layers; `[probe]
  clipboard_command` is read as a legacy alias, `[clipboard] command`
  winning inside one file". The `bale status` row: "labelled
  `clipboard`; `--json` carries it as the `clipboard` object (`command`,
  `source`, `key`, `shadowed`, `problem`)". Why: the brief routes
  BALE.md wording here as Proposals." choice-prompt-convergence,
  `2026-10-06-choice-prompt-convergence-001`: "**BALE.md true-up (out of
  scope here).** *What:* §7.3's description of the session-shape
  exchange and the checkpoint picker should say that both draw config
  init's alternatives. The shape rows are lettered (`[c] code` … `[x]
  mixed (Enter)`, `[r] read-only`), and the prompt offers `? help`,
  which shows the item's description. The picker's numbered candidates
  and prompt (`Enter = none · 1-N picks >`) offer no help, because `?`
  is a path there. Wherever BALE.md describes `bale config init`'s
  `.baleignore` suggestions, it should say they count only files pack's
  filter chain would ship. That means not secrets, not the configured
  checkpoint's subtree, not planner bundles, and not files a kept
  pattern already matches. *Why:* the prose would otherwise describe the
  hand-built rows and the all-files count this session replaced. *Scope
  hints:* `BALE.md` §7.3, and the §6.4 or wizard passage on
  `.baleignore`."]
- An oracle grades a crash in the code under test as the work's failure:
  rides the next `docs/PLANNER.md` holder, §4, beside the fixture
  entries above. The wave2-004 desk's authoring lesson, earned on D's
  oracle (§6 entry 222), proposed for this close to land as practice and
  not as a PLANNER.md edit, its text verbatim from that desk's brief:
  "**An authoring lesson for PLANNER.md §4,** proposed for the
  sitting-close session to land as practice, not to edit here. An oracle
  must grade a crash in the code under test as the work's failure (exit
  1), including inside its own fixture steps. Only failures of the
  oracle's own machinery (its controls, git, file setup) exit 2. And no
  probe that matches a word may see text the fixture itself authored."
  Landed here as practice, 2026-10-05; the holder lands the sentence.
- A non-exiting form of `effective_clipboard_command`, so D's copy path
  stops routing through `fail()`: rider on the log-hold session,
  dispatched by the cleanup desk as `2026-10-04-log-hold` and applied as
  `2026-10-04-log-hold-003` by its relay (the next close records the
  rest). D's words on why: "`resolve_clipboard_command` captures the
  `[bale] error:` line `fail()` prints, so stderr doesn't show it as an
  error of the command. `fail()` still journals that line into an open
  session log. That is an honest record of what bale read, but you'll
  see it in the log above the "NOT copied" notice." Touches
  `bin/bale_config.py`.
  [2026-10-06: consumed at `2026-10-04-log-hold-003`, its decision 5,
  ratified: `clipboard_command_reading(repo)` returns a
  `ClipboardCommandReading(command, source, refusal)` with any refusal
  as a value, no `fail()`, no print and no journal entry, and
  `effective_clipboard_command` stays fatal for other callers as a
  wrapper over it; the "NOT copied" notice and the exit codes are
  unchanged. Its end-to-end test packs with a triple-quoted global key
  and finds the notice in the session log and no `[bale] error:` entry.]
- `("clipboard",)` in `tests/test_cli_help.py`'s `COMMANDS` and a
  `claude/context/bale-internals.md` line for `bale_report`'s copy
  section and `bin/bale` section 30: D's fourth Proposal, rider on the
  same log-hold session by the wave2-004 desk's routing. Text verbatim
  from D's notes.md, flattened: "**What:** add `("clipboard",)` to
  `tests/test_cli_help.py`'s `COMMANDS` tuple, and give
  `claude/context/bale-internals.md` a line on `bale_report`'s copy
  section and `bin/bale` section 30. **Why:** both enumerate surfaces
  this session added. They were outside the forecast and aren't needed
  for the goal (this session's suite covers the verb's help). **Scope
  hints:** a tests-only or docs-only rider on the next session that
  touches either file."
  [2026-10-06: consumed at `2026-10-04-log-hold-003`. Its record's
  `change_paths` carry `tests/test_cli_help.py` and
  `claude/context/bale-internals.md`, and its `validation_will_run`
  lists "assert: session D rider — clipboard in the help suite and the
  internals map", in a run whose state is PASS; its notes.md count the
  `("clipboard",)` help entry among its deliberate no-change pins,
  "which already rendered cleanly". The internals file as shipped to
  close 21 carries both lines: cluster 20, "Clipboard verb",
  `cmd_clipboard` as `bin/bale` banner section 30, and the paragraph on
  `bale_report`'s paste-block copy section.]
- Proposals of the `2026-10-03-friction-points-001` and
  `2026-10-03-friction-points-wave2-004` sittings' workers,
  dispositions, as the two desks routed them and the records bear out:
  A's `upgrade.sh` `REQUIRED_RELEASE_MEMBERS` → B, consumed (B's rider,
  with `bin/VERSION` added beyond the brief and `bale_sandbox` left off,
  pinned by `tests/test_upgrade_required_members.py`); A's seam guidance
  → B, used in part (B took `WizardUI`, `ask` and `ITEM_HEADER_RE`, and
  built `PackWalk` instead of `Walk` and `ui.ask` instead of `confirm`,
  both ratified); A's `ask_choice` → C, consumed; A's
  `bale-internals.md` §1 true-up → C, whose record carries the file
  among its `change_paths` and whose notes.md does not say what changed
  in it, so whether the §1 true-up landed is not recorded here; A's
  `config init` description proposal, addressed to E and carried by both
  desks and by D as E's → D, consumed at D with the project-only section
  list corrected; A's and E's BALE.md sentences → the routing entry
  above; E's board-citation fold → the ruling queue's bracket; B's
  native log hold, its sweep-prompt restyle (ruling 2 [1], width only)
  and its pre-walk `[bale]` lines → the log-hold session; B's
  `bale_wizard` additions → choice-prompt-convergence, C having since
  landed `ask_choice`; B's BALE.md §7.3 sentences → the routing entry;
  C's BALE.md sentence → the routing entry; C's neutral section name →
  clipboard-key-rename; C's `walkthrough_baleignore` filters →
  choice-prompt-convergence; D's BALE.md sentences → the routing entry;
  D's status-row relabel and `bale status --json` `clipboard` object →
  clipboard-key-rename; D's `test_cli_help` and internals line → the
  log-hold rider above; D's `fail()` journaling → the non-exiting-form
  rider above. The three dispatched sessions' own landings, decisions
  and Proposals are the next close's. Anything not named here stands as
  shipped.
  [2026-10-06: recorded at close 21. The three sessions' landings and
  their ratified decisions are §3's wave block of this date; their
  Proposals, with close 20's own two, are dispositioned in the
  registry's entry of this date below.]
- `wrap=True` at the other long y/N prompts, the supersession,
  drift-admission and bare-apply prompts: rides the next session
  touching both `bin/bale_pack.py` and `bin/bale_apply.py`, layout only.
  log-hold's second Proposal, filed as a rider by the operator's "as
  assumed" to the cleanup desk's light block two, [2], the keyword being
  layout-only by construction. Text verbatim from
  `2026-10-04-log-hold-003`'s notes.md, flattened: "**The other long y/N
  prompts.** *What:* pass `wrap=True` at the supersession,
  drift-admission and bare-apply prompts. *Why:* the supersession prompt
  is a pre-walk line in all but name, and it still runs long on an
  80-column terminal. The keyword is layout-only by construction, but
  the operator's ruling covered only the sweep. *Scope hints:* one
  argument per call site, in `bale_pack` and `bale_apply`." Convergence,
  the one later session holding `bin/bale_pack.py`, did not hold
  `bin/bale_apply.py`.
- Accessors for `bin/bale`'s FORCE queue, retiring `bale_pack`'s two
  `__main__` reach-ins: rides the next session holding `bin/bale`
  (section 2) and `bin/bale_pack.py` (`_pending_force_line_count`,
  `_drop_force_lines_queued_since`). log-hold's fourth Proposal, a rider
  by the cleanup desk's brief. Text verbatim, flattened: "**Retire the
  FORCE-queue `__main__` reach-ins.** *What:* give bin/bale's logging
  section two small accessors for its FORCE queue: a count, and a
  drop-since-mark. Then have `bale_pack`'s `_pending_force_line_count`
  and `_drop_force_lines_queued_since` call them instead of reading and
  truncating `__main__._pending_log_lines`. *Why:* B called the
  rebinding "the second bale_pack reach into `__main__` state". With it
  gone, these two are the last, and the second one mutates bin/bale's
  state from outside. *Scope hints:* bin/bale section 2 and those two
  `bale_pack` helpers, a few lines each."
- PackWalk as a configuration of `bale_wizard.Walk`: rides the next
  session holding `bin/bale_wizard.py` and `bin/bale_pack.py`, changing
  nothing visible. Convergence's third Proposal, filed as a rider by the
  cleanup desk's light block four, [3]. Text verbatim from
  `2026-10-06-choice-prompt-convergence-001`'s notes.md, flattened:
  "**PackWalk as a `bale_wizard.Walk` configuration** (B's second
  addition, deferred). *What:* give `Walk` a shrinkable plan (`drop`)
  and plain-word section headings, then make PackWalk a configuration of
  it. *Why:* the choice move did not need it. Today the only differences
  are those two features plus PackWalk's abort-on-EOF `ask` and
  `choose`, which would become a Walk option too. *Scope hints:*
  `bin/bale_wizard.py`, `bin/bale_pack.py`, and `PackWalkTest`."
- `contract-doc` defined where it is named: rides the next session
  holding `bin/bale_pack.py`. The close desk's rider
  (`2026-10-06-friction-points-close-desk-002`), from convergence's
  decision 4, "Nothing that ships defines `contract-doc`, so the help
  names it without explaining it." In the desk's words, from its record
  as close 21's brief carries it: "The cleanup desk left the routing to
  this desk: the `?` help convergence added to the shape question names
  `contract-doc` without defining it, and nothing that ships defines it
  (the schemas list it in the `work_class` enums and name it in a
  description; TARBALL.md §3.4's `--work-class` row lists it). Routed as
  a registry rider on the next session holding `bin/bale_pack.py`:
  define the class in the shape question's help, in words its
  dispatching desk supplies, and the same words in TARBALL.md §3.4's
  `--work-class` row if that session holds `docs/TARBALL.md`. This
  desk's reading of the term's use in `claude/MASTER.md`, a session
  whose change set is the carried contract docs, is a reading, not a
  definition."
- Proposals of the `2026-10-04-friction-points-cleanup-002` sitting's
  workers and close 20, dispositions, thirteen, as the cleanup desk
  routed them (its light blocks two and four, and its brief where they
  name no home) and the close desk checked each against its notes.md.
  log-hold's "Display wrapping for every verb." → the ruling queue's
  entry of this date; "The other long y/N prompts." → the `wrap=True`
  rider above; "BALE.md true-up sentences" → the 99b routing entry's
  bracket of this date; "Retire the FORCE-queue `__main__` reach-ins." →
  the FORCE-queue rider above. Close 20's pack-time include warning →
  row 134; `reconciliation_parsed: false` surfaced → row 135. The
  rename's "A changelog row for this rename, with the version bump." →
  the 0.4.46 bump, dispatched by the close desk as
  `2026-10-06-bump-0-4-46` (§3's close-desk block; §6 entry 224); its
  "BALE.md true-up sentences" → the 99b bracket; its "Drop the legacy
  alias one day, or not." → record only, no work, its text verbatim,
  flattened: "**Drop the legacy alias one day, or not.** What: nothing
  now. If the alias is ever retired, the retirement needs
  `clipboard_command_reading` to refuse `[probe] clipboard_command` with
  a remedy, the crafter's scan to stop reading it, and bale-src's own
  `bale.toml` moved first. Why: every reader walks
  `CLIPBOARD_SPELLINGS`, so the retirement is a one-tuple change plus
  the refusal text; I note it so the pin is visible rather than because
  anything asks for it. `TARBALL.md` §3.2's precedent for
  `claude-decides` is "accepted for good", and that reads right here
  too." Convergence's "BALE.md true-up (out of scope here)." → the 99b
  bracket; "Drop two of the picker's three exceptions." → the ruling
  queue; "PackWalk as a `bale_wizard.Walk` configuration" → the rider
  above; "Config init's `.baleignore` add prompt." → the ruling queue.
  The `contract-doc` rider above is the close desk's own, not a worker's
  Proposal. Anything not named here stands as shipped.
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

Landed 2026-09-16, the continue-plan-009 sitting (master
`2026-09-15-continue-plan-009`, read-only; opened 2026-09-15 UTC on
"continue the plan, take on a little more work, look for disjoint
packing and chunking"; the previous master
`2026-09-15-continue-plan-004` closed at close-9). Eight sessions
landed in two waves of four beside the desk, up from three; this
block carries only what has no row home; close recorded by
`2026-09-16-sitting-close-deltas-10-005`:

- Wave record, wave 1 (all opened beside each other, forecasts
  disjoint by the gate's own judgment; one bumper):
  `2026-09-15-board-102-explicit-name-010` (0.4.33),
  `2026-09-15-board-91-82-crafter-pair-011` (bumpless under 0.4.33),
  `2026-09-15-board-68-open-gate-order-012` (bumpless),
  `2026-09-15-board-96-doc-97-terminal-shapes-013` (bumpless, doc
  lane). All four applied clean on the first attempt.
- Wave record, wave 2 (opened after 20:00 Eastern, so their sids
  date 2026-09-16): `2026-09-16-board-47a-hold-card-triage-001`
  (0.4.34), `2026-09-16-board-96-crafter-85-light-block-002`
  (bumpless), `2026-09-16-board-99a-outward-docs-003` (bumpless;
  re-attempt — the first attempt HELD on its own validation.sh
  asserting the literal `0.4.33` under target-base staging that
  already carried 47a's `0.4.34`, blind checkpoint 5/5, change set
  byte-identical), `2026-09-16-board-pack-ux-micro-004` (bumpless;
  re-attempt — the first attempt HELD two of eight blind checks, both
  the worker's, on an oracle the desk had amended once, v2
  `cc6b44200d8d`).
- Chunking of record: row 96 split in three file-disjoint thirds
  (doc, crafter, pack flag), the flag deferred to the 100 arc's enum
  session; row 47 split into 47a (judge line, labels, forked
  successors, telemetry) and 47b (addressed blocks); 82 rode 91, 97
  rode 96-doc, 85 rode 96-crafter, 92 and 84 and three pack-side
  registry riders rode one pack-UX micro. 102 ran ahead of 47 (small
  first). Two bumpless-unders in one wave is the new normal.
- Desk fixture defect of record: the pack-UX brief's row-92 example
  named an untracked file as a drop; untracked-not-ignored files ship
  (`git ls-files --cached --others --exclude-standard`). The worker's
  light block caught it before the apply; the desk amended the oracle
  (v2) and the first apply used `--accept-checkpoint-change` (§6
  entry 143).
- The light tier's first day: three light blocks from three workers
  in one hour (99a, 96-crafter, 47a), a fourth from pack-UX; every
  one admitted by count, every one answered inline in a minute, no
  thread opened. One answer was "no" (96-crafter's §10.4: the one
  sentence granted was a floor). 96-crafter's own manifest omits the
  two counts it created because apply validates against the installed
  schema — checked, not inferred; the honest one-apply-behind case.
- Sitting-open record: close-9's notes.md ratified wholesale at the
  open (the includes-as-scope entry's second bracket left as landed).
  The sitting-open version check was satisfied by the request's
  provenance stamp, 0.4.32.
- Outside review of record: the operator ran bale against another
  model, which declined the framework on four grounds — a file
  claiming precedence over the model's own instructions, the shape
  rule reading as a prose ban, two opaque tools presented as required,
  and 250 KB of contract around a two-paragraph seed (§6 entry 145).
  Separately, on another project, a read-only discussion session
  returned a tarball because no doc carves out a discussion and the
  shape rule wins by silence (§6 entry 146). Rows 104 and 105 answer
  both.
- Declined at the desk: `bale open --gates-only` (68's Proposal) —
  the pre-flight is a cost ordering, not a verb.
- Ratification debt carried forward, per convention: THIS close's
  notes.md queues to the next sitting's open.
- Board deltas of the close: rows 102, 91, 82, 68, 97, 85, 92, 84
  DONE; rows 96, 47, 99 grown (96 two thirds done, 47a and 99a done);
  rows 98 and 69 grown; rows 104, 105, 106 opened; evidence entries
  141–146 in §6; two contracts dated 2026-09-16 in §5; the version
  landmark 0.4.34, the tests-forecast concurrency clause, the
  scratch-repo checkpoint rules, the target-base validation rule, and
  the install-shipped-schema rule in §7.
- Sequencing for the next desk: wave 3 — 47b, 56+57, 69 (+85's lint
  half if any remains), the stats micro (86 + 98 + the dossier wiring
  + the two self-reported counts' read side), and 106 (the `bin/bale`
  de-dup micro) can all run beside each other; 105 is a doc-lane
  micro that goes first, since it changes what every fresh model
  reads first; then 104 → 37 → 103 (design sitting) → the 100 arc
  (absorbs 77; 99b rides its doc wave; 96's pack flag rides its enum
  session) → 43 → 45 → S6. Row 93 stands until brought forward.

Landed 2026-09-17, the continue-plan-006 sitting (master
`2026-09-16-continue-plan-006`, read-only; opened 2026-09-16T22:17Z;
the UTC date rolled to 09-17 mid-sitting, so sids opened after ~00:00Z
carry 09-17; the previous master `2026-09-15-continue-plan-009` closed
read-only at this sitting's open). Wave 3 landed but for 47b, one fix
split and landed, and three rows opened; this block carries only what
has no row home; close recorded by
`2026-09-17-sitting-close-deltas-11-007`:

- Landing record, in order, all applied clean unless noted:
  `2026-09-16-board-105-operator-voice-007` (bumpless);
  `2026-09-16-board-69-tools-pair-008`; `2026-09-17-stats-micro-001`;
  `2026-09-17-board-56-57-changelog-aborted-002` (HOLD on
  `test_global_doc_selfcontainment` — a base defect, §6 entry 148 —
  retried unchanged after the fix; 0.4.35 bumper);
  `2026-09-17-board-69-selfcontainment-fix-004` (HOLD; closed
  superseded-by-split by 005);
  `2026-09-17-board-69-selfcontainment-fix-both-005`;
  `2026-09-17-board-106-bale-dedup-003` (HOLD, fixture defect: the
  near-name probes pinned a quote character; checkpoint v2 amended,
  retried with `--accept-checkpoint-change`; its telemetry record
  shows three HOLDs and one rejected apply before the landing retry at
  2026-09-17T11:58Z).
- In flight at the brief, closed before this close packed:
  `2026-09-17-guard-maintenance-006` (row 108) applied clean at
  2026-09-17T13:01Z per its telemetry record. Its notes.md was not
  before the desk when the brief was written, so its ratification
  queues to the next open beside this close's.
- Sitting-open record, ratification block A (close-10's notes.md): all
  six disagreements accepted — 97's bracket strike, 143→142, row 99
  verify-only, 106 spans two files, 82 four values, 106 names
  `compose_retry_successor`; both proposals accepted.
- Wave 3 re-cut by file map at the open: 3a = 105, 69, the stats micro
  (with the dossier wiring), the 56+57 bumper; 3b = 106 then 47b —
  corrected mid-sitting: 106 touches neither `bin/bale_apply.py` nor
  `bin/bale_report.py`, so it ran beside 56+57 (§6 entry 150). 47b
  stands, with a rider list (row 47).
- Worker light blocks answered from the desk, all defaults ratified:
  69 (pin home, property-not-inventory, `docs_read` seeded loud with a
  new warning `DOCS_READ_EMPTY_STUB`); the stats micro (latest
  attempt, punctuation-shed tokens, membership totals); 56+57 (CODE.md
  §8.5 home); 106 (fixture ruling). Every worker notes.md judgment
  call is ratified as shipped; the dispositions of their proposals are
  the registry and board entries of this close (§6 entry 149).
- The `--supersedes` dirty-`main` finding: the operator hit it
  2026-09-17T02:41Z and committed by hand; cause and fix on row 107.
- Ratification debt carried forward, per convention: THIS close's
  notes.md queues to the next sitting's open.
- Board deltas of the close: rows 105, 69, 86, 98, 56, 57, 106 DONE;
  row 44's dossier wiring consumed; row 47 grown (47b's rider list and
  the HOLD card's third category); rows 107, 108, 109 opened in §4,
  108 DONE before the close packed; evidence entries 147–154 in §6;
  the heading "New, ratified 2026-09-16" set over close-10's two
  contracts and six contracts dated 2026-09-17 in §5; the version
  landmark 0.4.35.
- Registry deltas of the close: consumed — the `bale stats --sid`
  dossier wiring (stats micro), the light-tier INDEX-row rider (105),
  the crafter's single-quoted `clipboard_command` rider (69); carriers
  moved — `normalize()` to row 109, the pack-json
  `sweep`/`include_group` key to 47b's rider list; the post-epoch
  fixture entry gains the stats micro's two records; seven new
  entries, one recorded consumed at birth (the in-process opener
  constants test, 106), and a dispositions entry for the sitting's
  Proposals.

Landed 2026-09-18, the continue-plan-001 sitting (master
`2026-09-18-continue-plan-001`, read-only; packed 2026-09-18T23:04:16Z;
the previous master `2026-09-16-continue-plan-006` closed
`closed-read-only` at 2026-09-17T15:24:21Z per its record — 34 seconds
after close 11's landing retry, the day before this sitting opened, not
at its open). Wave 4 landed whole — rows 107 and 47 (47b) DONE, row
109's narrowed two thirds DONE, rows 110 and 111 opened; this block
carries only what has no row home; close recorded by
`2026-09-19-sitting-close-deltas-12-001`:

- Landing record, in apply order from telemetry — one apply attempt
  each, worker validation PASS and blind checkpoint PASS on every one,
  no HOLD (the operator's one-word "applied" was the whole story):
  `2026-09-18-board-107-supersedes-clean-tree-004` (bumpless-under;
  2026-09-18T23:52:21Z); `2026-09-18-board-109-harness-micro-002`
  (tests-only, bumpless-under; 23:53:32Z; one out-of-forecast file,
  `tests/test_harness_cli_loader.py`, admitted at apply at the prompt);
  `2026-09-18-board-47b-relay-blocks-003` (the wave's bumper, 0.4.36,
  with `claude/changelog/0.4.36.json`; 2026-09-19T00:01:45Z, past UTC
  midnight). 47b and 107 shipped nothing outside their forecasts. The
  three packed within thirteen seconds of each other
  (23:26:38Z–23:26:51Z) and ran beside the desk together.
- Wave 4 cut by file map at the open, before any bundle: two
  collisions found at the desk rather than at the gate.
  `tests/test_apply_preflight.py` holds both 47b's `HoldCardUnitTest`
  and the class row 109 was to move, so 109 ran narrowed (loader,
  `normalize()`, one rider) and its class move was deferred; the
  pack-json `sweep`/`include_group` rider spans `bin/bale_report.py`
  (47b) and `bin/bale_pack.py` (107), so it moved to row 104. All three
  bundles were dress-rehearsed with `bale open` beside a read-only
  master in one scratch repo before delivery; the gate admitted them
  together (§6 entry 155).
- Sitting-open record: close 11's notes.md ratified wholesale
  (operator: "as assumed"), its item 3 checked against 105's notes —
  proposals 1 and 3 were recorded, proposal 2 was not (registry above;
  carrier row 104). `2026-09-17-guard-maintenance-006`'s notes.md
  ratified wholesale, the token-anchored `board-<digits>` pattern
  included. The sitting-open version check was satisfied by the
  request's provenance stamp, 0.4.35 (the master's own record carries
  no version; the three workers' provenance stamps read 0.4.35).
- Desk light blocks, two (the master asks the operator through the
  same tier). Block one, three questions — the 109 narrowing, the
  rider's move to 104, close 11's ratification — answered "as assumed,
  with one clarification", the clarification being the operator's
  statement of what he needs from the HOLD card, carried verbatim into
  47b's brief. Block two, three questions: the routing rule was
  ratified by exercise (the operator opened the 47b bundle built on
  it); the other two — guard-maintenance's ratification and 105's
  Proposal 2 — were re-asked at the close, and this close is built on
  "yes" to both.
- Worker judgment calls, all ratified as shipped: 107's two sweep
  commits rather than one (the closure sweeps at its event, the stamp
  at its own; a deferred close sweep would regress the accepted-abort
  window); 109's `SourceFileLoader` over `runpy`, its `tests/` path
  guard in the two doc-pin suites, and its pin of §5.10's own wording;
  47b's five decisions — `send first:` as a trailer line, the worker
  block built from in-memory validation output and never the log,
  bands cut by byte offset per attempt, the sentinel guard, the quoted
  closing line — and its base-defect flag finding.
- Ratification debt carried forward, per convention: THIS close's
  notes.md queues to the next sitting's open.
- Board deltas of the close: row 47 DONE (47b; the interim
  planner-first rule retired); row 107 DONE; row 109 two thirds and one
  rider DONE, its class move now row 111's; row 104 grown four riders;
  rows 110 and 111 opened in §4; evidence entries 155–163 in §6; the
  heading "New, ratified 2026-09-18" over four contracts in §5; the
  version landmark 0.4.36 (0.4.35 recorded beside it), an
  include-authoring rule, the untracked-`opened` fact, the log's worker
  band, the harness's two helpers, and 47b's one-apply-behind in §7.
- Registry deltas of the close: consumed — `normalize()` and the §5.10
  shape-sentence pin (109), `format_walkthrough_summary`'s attribution
  (47b); closed as not reproducing — supersession's
  closure-before-sweep (107); carriers moved — both pack-json
  `sweep`/`include_group` entries to row 104 (gaining 107's Proposal
  1), `run_hook`'s f-strings and `from_lines`' marker to row 110;
  flagged for the next desk — checkpoint `bash -n` fail-fast; six new
  entries, the last a dispositions entry for the sitting's Proposals.
- Sequencing for the next desk: rows 110 and 111 are new smalls; both
  want `tests/test_apply_preflight.py` (110 for `HoldCardUnitTest`, 111
  for the class move), so cut them by file map, not by this sentence.
  Row 104 is next in the standing line and now carries four riders
  (registry above); the desk read this sitting that pack's argument
  parser lives in `bin/bale`, so 104 and 110 likely both hold
  `bin/bale` — verify before cutting. Then 37 → 103 (design sitting) →
  the 100 arc (absorbs 77; 99b rides its doc wave; 96's pack flag rides
  its enum session) → 43 → 45 → S6. Row 93 stands until brought
  forward.

Landed 2026-09-19, the unrecorded session-fix-002 sitting — no desk
recorded it; reconstructed at close 13 from telemetry and its two landed
notes.md, its chat and its briefs unseen by the 006 desk and by this one
(master `2026-09-19-session-fix-002`, read-only; opened
2026-09-19T00:22:52Z, `closed-read-only` at 02:09:02Z by a pack two
seconds before the 006 master's record was written; the previous
recorded master `2026-09-18-continue-plan-001` closed `closed-read-only`
at 2026-09-19T00:22:34Z, eighteen seconds before this one opened). The
opener reword landed whole as row 112, DONE at birth; this block carries
only what has no row home; close recorded by
`2026-09-19-sitting-close-deltas-13-010`:
- Landing record, from telemetry.
  `2026-09-19-opener-reword-doc-sweep-r2-003` opened 01:23:39Z and
  closed `superseded-by-split` at 01:26:54Z, `superseded_by`
  `2026-09-19-opener-reword-code-004`; its forecast was exactly the
  union of its two children's (§6 entry 165). Then, in apply order, one
  apply attempt each, worker validation PASS and blind checkpoint PASS
  on both, no HOLD, no admissions, bumpless under 0.4.36:
  `2026-09-19-opener-reword-code-004` (opened 01:36:19Z, applied
  01:54:38Z; `bin/bale_pack.py`, `BALE.md`,
  `schemas/request-manifest.schema.json`, `tests/test_pack_opener.py`,
  `tests/test_readme_identity.py`), then
  `2026-09-19-opener-reword-docs-005` (opened 01:54:54Z, sixteen seconds
  after 004 applied; applied 02:06:58Z; `docs/CLAUDE.md`,
  `docs/PLANNER.md`, `docs/TARBALL.md`, `tests/test_doc_crossrefs.py`).
  The pair ran in series, not beside each other, though their forecasts
  were disjoint; the records do not say why.
- What landed, from the two notes.md: the opener reworded and re-wrapped
  with `textwrap`; the opener closing by session kind, keyed on
  read-only (a worker session owes one response tarball; a planner
  session owes chat plus bundles, never a tarball); the manifest's
  top-level `readme` key (`null`, or `{path, sha256}`); the `$EDITOR`
  scaffold comment never ships; the README written once, from the bytes
  that were hashed; two VERBATIM rulings in the docs (the ask sentence
  in CLAUDE.md §3 and TARBALL.md §5.10; the deliverable sentence in
  CLAUDE.md §3 and TARBALL.md §2; both now §5 contracts); and the
  retired "machine-recognizable shape" sentence pinned absent.
- Worker judgment calls, ratified wholesale at the 009 open (next
  block). 004: the scaffold strip is keyed on the comment's marker, not
  exact bytes, and applies to editor output only (`--readme-file` alone
  still ships verbatim); a scaffold-only buffer means no README; the
  README is written with `write_bytes`, hashed once and written once;
  the defense-in-depth stamp check in `build_request_tarball` skips a
  manifest with no `readme` key, which keeps the crafter's injection
  driver working. 005: TARBALL.md §2 is the deliverable sentence's
  second home, keeping §5.10 about asking; and §3.1's brief delivery is
  aligned with CLAUDE.md §3 and PLANNER.md §2 (a bundle member first,
  `--readme-file` only where the crafter is unreachable).
- 005's four "please check" items, disposed: 1 (brief delivery) and 3
  (sibling behavior described ahead of landing — moot, 004 had landed
  sixteen seconds before 005 packed) ratified as shipped; 2 (the
  scaffold comment is not in the global docs) stands, since BALE.md
  carries it and that is its home; 4 settled in code by the 006 desk:
  `resolve_write_forecast` returns `[]` only under `--read-only` (no
  `--include` defaults to `["."]`), so "`resolved_scope: []` is the
  read-only stamp" needs no qualifier (§5).
- 004's "For the sibling doc session" list (five items) was consumed by
  005. The 009 desk checked the fourth by grep: `OPENER_SHAPE_SENTENCE`
  survives only in `tests/test_pack_opener.py`'s retired-names list.
- Board deltas of this sitting's work: row 112 opened DONE at birth in
  §4; row 104's two consumed parts bracketed (the kind-conditional
  closing sentence, built keyed on read-only; the three-homes rider,
  moot); the first three contracts under "New, ratified 2026-09-19" in
  §5; evidence entries 164, 165 and 170 in §6.
- Registry deltas of this sitting's work: closed as moot, the shape
  sentence's three-homes question (005 retired the sentence); one new
  entry, 004's lint Proposal, accepted at the 009 open and riding the
  next `tools/` touch.

Landed 2026-09-19, the continue-plan-006 sitting (master
`2026-09-19-continue-plan-006`, read-only; opened 2026-09-19T02:09:04Z
per its record, which carries no `packed_at`; sitting-open version
0.4.36 by the request's provenance stamp, and both workers' stamps read
0.4.36; `closed-read-only` at 03:12:18Z by a pack, the 009 pack by the
desk's account). The desk ended its sitting at the wave-5 milestone
rather than author this close on a long context; its brief to the 009
desk is this close's source. Wave 5 landed whole — rows 110 and 111
DONE, row 109's deferred third DONE, row 113 opened; this block carries
only what has no row home; close recorded by
`2026-09-19-sitting-close-deltas-13-010`:
- Landing record, in apply order from telemetry — one apply attempt
  each, worker validation PASS and blind checkpoint PASS on both, no
  HOLD: `2026-09-19-board-111-tests-smalls-008` (packed 02:29:47Z,
  applied 02:57:04Z; tests-only, bumpless; no admissions; changed
  `tests/test_craft_response.py`, `tests/test_doc_crossrefs.py`,
  `tests/test_thread_status.py`; forecast
  `tests/test_sanctioned_pairs.py` and left it untouched), then
  `2026-09-19-board-110-held-admissions-007` (packed 02:29:06Z, applied
  03:04:19Z; the wave's bumper, 0.4.37 with
  `claude/changelog/0.4.37.json`; two out-of-forecast paths admitted at
  the prompt, `tests/test_cli_help.py` and `tests/test_pack_guards.py`;
  forecast `tests/test_hold_retry_e2e.py` and left it untouched). The
  two packed 41 seconds apart and ran beside the desk together.
- Wave 5 cut by file map at the open. Both rows wanted
  `tests/test_apply_preflight.py`; 110 held it and carried the
  `SubcommandHelpLayoutTest` move as a droppable last rider (it landed,
  in `tests/test_cli_help.py`; §6 entry 167); 111 ran narrowed to the
  two `_load_cli()` adoptions and the §7 relay pin. Row 104 could not
  run beside 110 (`bin/bale`, `BALE.md`); row 37 collides with 111 on
  `tests/test_craft_response.py`.
- Desk verification before any bundle: 110's defect reproduced on 0.4.36
  through the real CLI (the printed fixture-defect retry line REJECTED
  at own-forecast drift). Both checkpoints were dry-run three ways: FAIL
  on the base with anchors passing; PASS against a throwaway stub of the
  graded surface; and both bundles dress-rehearsed with `bale open`
  beside a read-only master in one scratch repo — admitted together,
  expected-HOLD proofs fired, oracles ran confined.
- Desk light block, one, three questions. [1] The cut: ratified by
  exercise (the operator opened both bundles). [2] Close 12's notes.md
  wholesale, and [3] 004's and 005's notes.md wholesale with 004's lint
  Proposal queued as a registry rider on the next `tools/` touch: both
  unanswered when the sitting ended, and carried in the 006 desk's brief
  under "Silence is not 'as assumed'" (§6 entry 169).
- Worker judgment calls, ratified as shipped by the 006 desk. 110: the
  `held_admissions` stamp over telemetry (written and wiped with
  `held_tarball`, so "latest HOLD wins" holds by construction; always
  written, so absence means pre-0.4.37 or never held); the card's
  fixture rung composing from the stamp's outcome (47a's rule); the base
  rung staying in-process; the note order; the strict parser; the
  pure-call default; item 7's named-absence degrade shipped as the desk
  ruled it; both twin existence checks retired with proofs (`cmd_retry`,
  `handoff`). 111: `_load_cli` imported inside
  `ExchangeBlockParity.setUpClass` with the path guard, not at module
  top (the dotted run form of a 160-test suite is worth more than
  uniformity; the desk declines the offered two-line move);
  `load_bale_module` inlined; the relay pin in `test_doc_crossrefs.py`,
  against `relay_sentinels` with the constant-level guard
  `test_builder_addresses_the_worker`; the doc-pin suite importing one
  `bin/` module.
- Ratifications at the 009 open, the sitting's last event before this
  close. The operator's message opening `2026-09-19-continue-plan-009`
  ended, verbatim: "As assumed on both." That answers [2] and [3]: close
  12's notes.md is ratified wholesale (its nine brackets, its forecast
  parenthetical, its dropped ordinal, "for weeks"); 004's and 005's
  notes.md are ratified wholesale; 004's lint Proposal is accepted and
  queued as a registry rider on the next `tools/` touch. Close 12's two
  Proposals: the first (consolidate §7's include-authoring bullets)
  waits for the next MASTER.md regeneration and has a registry entry;
  the second (scope row greps to §4) was applied by the 009 desk to
  close 13's checkpoint.
- Ratification debt carried forward, per convention: THIS close's
  notes.md queues to the following open.
- Sequencing for the next desk, verbatim from the 006 desk's brief:
  "Standing line after wave 5: row 104, re-scoped at the desk first (it
  was written before the opener reword; decide what `--kind` still buys
  now that the opener is already kind-conditional on read-only) → 37
  (parts 2–3 and the PLANNER.md rider; it holds
  `tools/craft_response.py` and `tests/test_craft_response.py`) → 103
  (design sitting) → the 100 arc → 43 → 45 → S6. Row 93 stands until the
  ledger shows its case. 104 (`bin/bale`, `bin/bale_pack.py`, schema,
  docs) and 37 (`tools/`, `docs/CLAUDE.md` §11, `docs/PLANNER.md`) both
  want global docs — cut them by file map before calling them disjoint."
  The re-scoping of rows 104 and 37 is the 009 desk's ruling, recorded
  at close 14.
- Board deltas of this sitting's work: rows 110 and 111 DONE; row 109's
  deferred third DONE (at 110, rider 6); row 113 opened in §4; the
  fourth contract under "New, ratified 2026-09-19" in §5; evidence
  entries 166–169 in §6; the version landmark 0.4.37, 110's
  one-apply-behind, the scratch-repo sandbox setting, an
  include-authoring rule, and the grown dispatch check in §7.
- Registry deltas of this sitting's work: consumed at 007 — `run_hook`'s
  f-strings, `from_lines`' marker (its pin moved with it, out of
  forecast), the `test_apply_preflight.py` docstring true-up; closed as
  stale — the two `_section_29` renames; five new entries — 110's two
  Proposals, 111's Proposal 1, close 12's Proposal 1 (the regeneration
  entry), and a dispositions entry covering both sittings' Proposals.

Landed 2026-09-19, the continue-plan-009 sitting (master
`2026-09-19-continue-plan-009`, read-only; bale 0.4.37, and both
workers' provenance stamps read 0.4.37; packed 03:12:19Z by the 009
desk's account of its own manifest's `packed_at`, which no shipped file
carries, and its record's `created_at` reads 03:12:21Z; the previous
master, `2026-09-19-continue-plan-006`, closed `closed-read-only` at
03:12:18Z; `closed-read-only` itself at 2026-09-20T00:17:07Z by a pack,
the `2026-09-20-continue-plan-001` pack by that desk's account). The
desk ended its sitting at the wave-6 milestone rather than author two
code bundles on a long context; its brief to the next master is this
close's source. Wave 6 landed whole — close 13 landed and row 113 DONE;
this block carries only what has no row home; close recorded by
`2026-09-20-sitting-close-deltas-14-002`:
- Landing record, in apply order from telemetry — one apply attempt
  each, worker validation PASS and blind checkpoint PASS with the stamp
  matched on both, no HOLD: `2026-09-19-sitting-close-deltas-13-010`
  (packed 03:28:52Z, equal to its record's `created_at`; applied
  2026-09-19T23:33:30Z; no admissions; changed `claude/MASTER.md` alone,
  407 lines added by its notes.md; its twelve claims went unreconciled
  at apply, §6 entry 176), then
  `2026-09-19-board-113-dotted-run-form-011` (packed 03:29:03Z, equal
  to its record's `created_at`; applied 2026-09-19T23:51:13Z;
  tests-only, bumpless; two out-of-forecast paths admitted at the
  prompt, `tests/__init__.py` and `tests/test_dotted_run_form.py`;
  changed those two and `tests/harness.py`; forecast
  `tests/test_thread_status.py` and left it untouched; six claims
  `agree`, and its two `--slow` claims `n/a`, skipped at apply). The
  two packed 11 seconds apart, and each was applied about twenty hours
  after it was packed; the records give no cause for the gap.
- Ratified at the open: the operator's message opening this sitting
  ended "As assumed on both." Close 13 records it (its second block,
  and §6 entry 169); this block only points at it.
- Row 113 dispatched at birth, in the 009 desk's words: "Row 113 was
  dispatched the sitting it was born, beside the close that wrote it,
  ratified by exercise (the operator opened the bundle). The desk
  measured before cutting: 56 of 68 suites failed the dotted form; a
  five-line `tests/__init__.py` fixed all of them, so a row written as
  a sweep across fifty-odd files ran as a one-new-file session with no
  hot-file collision. The brief offered the experiment as a
  measurement, not the mechanism; the worker verified what the desk had
  not (full discovery, all suites dotted in one process, the harness
  loaders) and shipped it." 113's notes.md calls the desk's init four
  lines, to which the worker added a docstring (§6 entry 172).
- Desk verification before delivery, in the 009 desk's words: "Close
  13's oracle: FAIL on the base with both anchors passing; PASS against
  a landing derived from the brief's bytes — that run caught two
  defects, both in the desk's rehearsal script, none in the oracle.
  113's oracle: FAIL on the base (exit 1, anchor passing), PASS against
  a landing extracted from the brief's fenced block, no bytecode left
  in the tree. Both bundles went through `bin/bale_open.py`'s
  `read_bundle` and `compose_pack_argv` in-process (a two-function
  `log`/`fail` shim in `__main__` is all it needs). NOT done: a
  `bale open` dress rehearsal in a scratch repo, as the 006 desk did.
  Both bundles opened clean at the operator's machine."
- Tool-use pauses, in the 009 desk's words: "Two tool-use pauses at the
  desk, each named as a pause, context intact (entry 163's class). The
  first fell after close 13's bundle was written and before it could be
  presented; the desk said so, asked the operator not to open it until
  the gate check, and ran the check first thing on resume. Close 13's
  worker named a pause of its own the same way." (§6 entry 173.)
- Desk light block, one, in the 009 desk's words: "It was emitted with
  two questions and the operator's next message was the two relays,
  with no reply to it. Silence is not "as assumed". It was re-emitted
  with a third question (the ratifications below), and the operator
  replied to all three" (§6 entry 175). [1] Narrow row 104 to the
  context pack plus its riders, leaving `--kind`, the manifest kind
  field and the light injection to the 100 arc? [2] Re-scope row 37 to
  a stats read side for `compaction_occurred`, a CLAUDE.md §11.4
  pointer at the crafter's bailout kind, and the PLANNER.md paragraph?
  [3] Ratify close 13's and 113's notes.md wholesale, close 13's two
  Proposals riding row 104, 113's Proposal 1 split between row 37 and
  a registry rider, its Proposal 2 declined? Each would assume yes. The
  operator's three replies, verbatim: to [1], "what is 104? can you
  explain this more?"; to [2], "probably fine, I just feel like we
  might be getting into "documentation in bale-src but not covered in
  global docs" so I just want to double check that since BALE.md
  doesn't ship with other projects"; to [3], "whatever makes sense".
  Read by the 009 desk and the 001 desk alike: [3] is ratified as
  assumed; [2] is yes, with a standing condition (row 37's bracket);
  [1] was not answered at this sitting. The 009 desk explained the row
  in chat and asked for the answer beside the next master's open paste;
  it did not come there either. The `2026-09-20-continue-plan-001` desk
  explained the row again at a tool-use pause, and the operator's next
  message, which resumed that desk, was the answer, verbatim: "104:
  narrowed, as the 009 desk recommended; the global-doc constraint on
  the context pack is agreed." So [1] was ruled on 2026-09-20, at that
  desk, before this close packed; no light block was emitted for it
  there, because the answer arrived first. Row 104's bracket carries
  the ruling.
- Close 13's notes.md, ratified wholesale by [3]. Items 1–5, where the
  records won, are accepted: `packed_at` over `created_at` for 110 and
  111; no pack second named for 006; the two sweeps attributed "by the
  desk's account"; the nine-and-a-half-minute gap between 003's close
  and 004's open, stated without a cause; the sitting-open version said
  both ways. Item 6 was a desk miss: "As assumed on both." is four
  words, and the brief said five. Item 7 was a desk miss worth an
  evidence entry (§6 entry 171). Its judgment calls are accepted as
  shipped, and are the convention now: both blocks closing on board
  then registry deltas, with sequencing just before them; the one
  sentence after block B's verbatim sequencing; the split of deltas
  between the blocks; the sandbox bullet beside the scratch-repo note
  and the other four ending §7; row 109's bracket saying only "same
  four tests, same names"; the homes for contracts three and four,
  `docs/TARBALL.md` §3.2 and BALE.md §8.8 (the 009 desk confirmed both
  by grep); "The desk counts 55 suites" left attributed. Row 113's
  "55" is corrected by bracket, not by edit. Its two Proposals → §3
  registry, riding row 104.
- 113's notes.md, ratified wholesale by [3]. Accepted as shipped: the
  init with a docstring naming the one run form that executes it; the
  pin in a new `tests/test_dotted_run_form.py` that does not import
  `harness`, loading each suite in a fresh interpreter;
  `tests/test_thread_status.py` forecast and left untouched because its
  run line now simply works (entry 168's class, second specimen: the
  forecast was the desk's guess); the `tests/harness.py` module
  docstring trued to three forms. Proposal 1 → §3 registry, split;
  Proposal 2 → declined as cosmetic, unscheduled (the dispositions
  entry only).
- Rows 37 and 104 re-scoped: 37 by [2] at this sitting, 104 by [1] on
  2026-09-20. Both rows want `docs/TARBALL.md` (37 its §5.8, 104 its
  §3.1 and §3.4); the 001 desk cut the collision once [1] was ruled:
  104 holds the file, and 37's §5.8 sentence rides 104. Both rows'
  brackets carry the detail.
- Ratification debt carried forward, per convention: THIS close's
  notes.md queues to the following open.
- Sequencing for the next desk, verbatim from the 009 desk's brief:
  "Standing line after them: 103 (design sitting) → the 100 arc → 43 →
  45 → S6. Row 93 stands until the ledger shows its case." "Them" is
  rows 104 and 37.
- Board deltas of this sitting's work: row 113 DONE, with the 56-of-68
  correction; rows 37 and 104 re-scoped; evidence entries 171–176 in
  §6; the unchanged 0.4.37 landmark, `tests/` as a package with the
  dotted form pinned, the one-process double load, and the in-process
  gate check in §7.
- Registry deltas of this sitting's work: consumed at 113 — the
  `tests/harness.py` comment above `CLI_PATH`; four new entries — the
  three redundant `tests/`-on-path guards (113's Proposal 1),
  `packed_at` on a pack's `opened` attempt and the closing pack's sid
  (close 13's two Proposals, riding row 104), and a dispositions entry
  for this sitting's workers.

Landed 2026-09-20, the continue-plan-001 sitting (master
`2026-09-20-continue-plan-001`, read-only; bale 0.4.37; packed
00:17:07Z by that desk's account of its own manifest's `packed_at`, and
its record's `created_at` reads 00:17:08Z, one second later; the
previous master, `2026-09-19-continue-plan-009`, closed
`closed-read-only` at 00:17:07Z; `closed-read-only` itself at 00:50:20Z
by a pack, the `2026-09-20-continue-plan-004` pack by that desk's
account, whose record opens the same second). The sitting ended at
delivery, before its wave landed, so its desk could not close it; its
record reached this close only as a quotation, byte-for-byte, inside
the 004 desk's brief to the 006 desk, carried byte-for-byte again in
this close's brief. Wave 7 landed whole — close 14 and row 37 DONE; this
block carries only what has no row home; close recorded by
`2026-09-20-sitting-close-deltas-15-007`:
- Landing record, in apply order from telemetry, both workers'
  provenance stamps reading 0.4.37:
  `2026-09-20-sitting-close-deltas-14-002` (packed 00:49:57Z, equal to
  its record's `created_at`; applied 01:10:00Z; one apply attempt,
  worker validation PASS and blind checkpoint PASS with the stamp
  matched; no admissions; changed `claude/MASTER.md` alone; ten claims,
  all `agree`, reconciliation parsed, §6 entry 176's bracket), then
  `2026-09-20-board-37-compaction-read-side-003` (packed 00:50:10Z,
  equal to its record's `created_at`; the wave's bumper, 0.4.38 with
  `claude/changelog/0.4.38.json`; four attempts: `held` at 01:10:37Z,
  checkpoint exit 1 with the stamp matched, worker exit 0, one failed
  probe, "PLANNER.md §5 step 5: the retry clause mentions the held
  apply's admissions", `tests/test_stats_compaction.py` admitted at the
  prompt; `rejected` at 01:15:01Z, command `apply`, on a tarball named
  `response-2026-09-20-board-37-compaction-read-side-003 (1).tar.gz`,
  no cause recorded (§6 entry 187); `applied` at 01:16:21Z, command
  `retry`, `corrects` naming its own sid, the same admission restated,
  checkpoint and worker PASS; nine claims on the held and the applied
  attempt alike, eight `agree` and the `--slow` full suite `n/a`,
  reconciliation parsed on both; changed `bin/VERSION`,
  `bin/bale_report.py`, `bin/bale_stats.py`,
  `claude/changelog/0.4.38.json`, `docs/PLANNER.md`,
  `tests/test_stats_aggregation.py` and the admitted suite). The two
  packed 13 seconds apart and ran beside each other; close 14 applied 37
  seconds before 37 held. Every apply attempt of both reads
  `sandbox_confined: true`, so both oracles ran confined.
- The open, from the 001 desk's record: the opening message did not
  answer the 009 desk's light-block question [1]. The first turn read
  the contract in order, authored close 14's brief and oracle,
  rehearsed them, assembled the bundle, and hit the tool-use limit with
  the bundle written but not presentable: entry 163's class, and the
  case the 009 desk left as an evidence candidate. The desk named the
  pause, said there was no file to open yet, explained row 104 in plain
  terms, and said a light block would close the resumed turn. None was
  emitted: the operator's next message was the answer. Close 14 records
  that ruling verbatim (its block and row 104's bracket); this block
  only points at it.
- A ruling between write and presentation (§6 entry 178). The ruling
  made the written close 14 brief false in one place (it said [1]
  stood). The desk derived a revision from the brief's own bytes,
  re-derived the row-104 probe, re-ran every rehearsal, rebuilt the
  bundle, and only then presented it. The `docs/TARBALL.md` cut followed
  once [1] was ruled: row 104 held the file (§3.1, §3.4) and row 37's
  §5.8 sentence rode row 104. Close 14's two brackets say so, and 104a
  landed the sentence (its notes.md).
- Desk verification before delivery, in the 001 desk's words,
  shortened. Close 14's oracle, six anchors and fourteen probes: base
  exit 1 with every anchor and the insertions-only probe passing; a
  landing built from the brief's bytes, exit 0; five negative landings,
  each failing exactly one probe; a HEAD that is not the authored base,
  the insertions-only probe SKIPping by name; a removed heading, exit 2.
  The rehearsal caught one defect, in the desk's rehearsal script (a
  double indent), none in the oracle; two probes were then loosened on
  the desk's reading that a correct worker could phrase past them. 37's
  oracle, one anchor and ten probes, all in-process against a scratch
  copy of `tests/fixtures/stats_corpus` under the staging root: base
  exit 1, anchor passing; a landing from the brief's fenced block, exit
  0; three negative landings bit. Both oracles print the label alone on
  a verdict line and any detail on a following `  detail:` line (§6
  entry 180). Both bundles went through `read_bundle` and
  `compose_pack_argv` in-process. NOT done: a `bale open` dress
  rehearsal in a scratch repo. NOT tested at the desk: either oracle
  under the real sandbox, since retired by exercise (landing record
  above).
- Where the desk departed from the 009 brief: "Derive both; do not
  rewrite" could not be followed, since close 13's brief and checkpoint
  are not in a master's request (packs withhold checkpoint bytes;
  request briefs are archived nowhere). Both of close 14's artifacts
  were authored fresh from close 13's landed block, its notes.md and the
  009 brief's description of its oracle (§6 entry 177).
- What the desk found in the records, beyond what close 14 already
  carries (009's two-second `packed_at` lag, the twenty-hour applies of
  010 and 011, entry 176): compaction disclosures measured by a
  throwaway script over all 274 parseable records, 206 reporting and 7
  disclosing, any-attempt and latest-carrier agreeing, all seven
  predating 2026-08-31, against §5's fifteen on 181 records (§5's
  calibration bracket; §6 entry 181); and the stats fixtures carrying
  `compaction_occurred` as a bare bool (26 records) where the schema and
  every real record carry an object, so 37's brief pinned a read side
  that takes both. The 009 desk's row-37 facts all held on
  re-verification.
- Dispatch-check declines, and how they fell at 37. The held admissions
  in `format_hold_relay_planner` (110's Proposal 2): declined on 37,
  since the rider changes emitted relay text whose pins live in
  `tests/test_apply_preflight.py`; its ride condition is reworded by
  bracket (§3 registry). The post-epoch stats-corpus fixtures: left to
  37's worker to watch, and not met at 37 (its notes.md). 37's new stats
  keys join 99b's BALE.md §5.6 inputs (row 99's bracket). 113's
  craft-suite guard: 37 did not hold `tests/test_craft_response.py`, so
  it rides that file's next holder.
- Ratification debt this sitting carried forward: close 14's and 37's
  notes.md, ruled wholesale at the `2026-09-20-continue-plan-006` desk
  (next block). This desk's own judgment calls are still unruled, and
  are listed in the next block's debt bullet.
- Sequencing for the next desk: the 001 desk's standing line did not
  reach this close. Its brief is quoted here only from its "Wave 7, as
  dispatched" heading to the line before its "Second job" heading, and
  the line is not in that range (§6 entry 177's second specimen). The
  line that did travel, the 009 desk's, verbatim as close 14 records it:
  "Standing line after them: 103 (design sitting) → the 100 arc → 43 →
  45 → S6. Row 93 stands until the ledger shows its case." The 004 desk
  carried the same line forward (next block).
- Board deltas of this sitting's work: row 37 DONE; row 99's 2026-09-20
  bracket, for 37's stats keys; the §5 calibration ruling's hand-count
  bracket, and the second contract under "New, ratified 2026-09-20";
  entry 176's bracket and evidence entries 177–181 in §6 (179 shared
  with the next block); the 0.4.38 landmark and the label-only verdict
  line in §7.
- Registry deltas of this sitting's work: consumed at 37 — 110's
  Proposal 1, the PLANNER.md §5 step 5 clause; the
  `format_hold_relay_planner` entry's ride condition reworded; the
  post-epoch fixtures entry's condition not met at 37; the path-guards
  entry's craft guard sent to the craft suite's next holder; no new
  entries of its own (close 14 and 37 proposed nothing; the dispositions
  entry at the list's end covers both sittings).

Landed 2026-09-20, the continue-plan-004 sitting (master
`2026-09-20-continue-plan-004`, read-only; bale 0.4.37 at its open;
packed 00:50:20Z by that desk's account, equal to its record's
`created_at` and to the second its pack closed the 001 master
`closed-read-only`; `closed-read-only` itself at 02:41:52Z by a pack,
the `2026-09-20-continue-plan-006` pack by that desk's account, whose
manifest's `packed_at` of 02:41:53Z is one second later than the
closure). Two turns. Its one bundle, 104a, applied at 02:35:51Z, six
minutes before this master closed: the desk read 104a's notes.md and
handed the close forward rather than author it, and its brief to the
006 desk is this close's source. 104a landed whole; this block carries
only what has no row home; close recorded by
`2026-09-20-sitting-close-deltas-15-007`:
- Landing record, from telemetry:
  `2026-09-20-board-104a-context-pack-005` (packed 01:24:58Z by its
  echoed provenance, and its record's `created_at` reads 01:24:59Z, one
  second later, a fourth specimen for the §3 registry's `packed_at`
  entry; provenance stamp 0.4.38; applied 02:35:51Z; one apply attempt,
  confined, worker validation PASS and blind checkpoint PASS with the
  stamp matched; no admissions; the bumper, 0.4.39 with
  `claude/changelog/0.4.39.json`; seven `change_paths`, all under its
  forecast: `BALE.md`, `bin/VERSION`, `bin/bale`, `bin/bale_pack.py`,
  the changelog record, `docs/TARBALL.md`, `tests/test_context_pack.py`;
  eleven claims, ten `agree` and the `--slow` full suite `n/a`,
  reconciliation parsed). Its worker paused once on a tool-call limit
  mid-build and resumed on Continue with context intact, and its
  notes.md says so (entry 163's class).
- Turn one. The records showed close 14 opened at 00:49:57Z and 37 at
  00:50:10Z, neither applied, so the 001 brief's first job, close 15,
  could not be built: `claude/MASTER.md` was close 14's forecast, and
  close 15's numbering, its ratification debt and its oracle's base all
  waited on landings. The desk said so and authored nothing for it (§6
  entry 182). Where the 001 brief and the records parted, in the 004
  desk's words: "the brief names one certain collision for 104 with 37
  (`bin/bale_report.py`); the records show two, since 37 also held the
  bump pair (`bin/VERSION`, `claude/changelog`)."
- The 104 cut, by file map, from the code. Read: `build_parser`'s
  `p_pack` block in `bin/bale`; `cmd_pack`'s head in `bin/bale_pack.py`;
  the read-only sweep's docstring. 104a, the context pack: `bin/bale`,
  `bin/bale_pack.py`, `BALE.md`, `docs/TARBALL.md`, `tests` and the
  bump, with two riders in files it already held (the stale
  successor-pointer comment in `cmd_pack`; TARBALL.md §5.8's "eventual
  `bale stats`" sentence). 104b, the pack-side telemetry riders: the
  pack-json `sweep`/`include_group` key with the stamp sweep's result,
  close 13's two Proposals, and 105's Proposal 2 (the tools'
  stdlib-only pin), authored against 104a's landed `cmd_pack`, so after
  it.
- The finding that blocked 104a (§6 entry 183): row 104 says "bare
  `bale pack`" produces the context tarball, but goal-less `bale pack`
  on a TTY is the wizard, and piped it refuses; with `--kind` sent to
  the 100 arc, the context pack had no spelling. The desk's light
  block, one question, hand-authored per TARBALL.md §5.10, verbatim:
  "[1] question: How do you type the context pack:
  `bale pack --context`, or goal-less `bale pack` itself? / while doing:
  cutting 104a; its brief and its oracle both have to invoke the command
  / would assume: the flag, `bale pack --context`; goal-less `bale pack`
  stays the wizard / why blocked: row 104 says "bare `bale pack`", but
  goal-less pack on a TTY is the wizard today". The operator's reply,
  verbatim, in the message that also carried both relays:
  "as assumed, and both applied:".
  Answered first time (§6 entry 179).
- Turn two: 104a authored and delivered. With 37 landed, 104a became
  the wave's bumper rather than bumpless-under, and its forecast gained
  `bin/VERSION` and `claude/changelog`. The oracle was authored after
  the ruling, so PLANNER.md §4's last bullet had nothing to re-verify.
- Desk verification before delivery, in the 004 desk's words,
  shortened. The oracle: one anchor block, one control, twelve probes,
  driving the real CLI in two fresh committed scratch repos under one
  scratch directory beside the tree, isolated `HOME`, `python3 -B`,
  removed on exit; the control proves the detectors the no-sid and
  no-opener probes rely on. Base (the 0.4.37 tree): exit 1, anchors and
  control passing, twelve probes failing, no residue, clean
  `git status`. A landing with the TARBALL.md sentence pulled from the
  brief's bytes and a throwaway `--context` stub: exit 0. Four negative
  landings: three each failed exactly one probe, and a renamed §3.1
  heading exited 2. Verdict lines carry the label alone (§6 entry 180).
  The bundle passed a tar read, member-hash comparison,
  `validate_bundle_manifest` and a token check. NOT done: `read_bundle`
  and `compose_pack_argv` in-process; a `bale open` dress rehearsal; a
  run under the real sandbox, the last since retired by exercise at
  104a's confined apply.
- 104a's notes.md, as the 004 desk read it: the four things the brief
  asked to have stated (landing path and name, layout, non-repo
  behavior, composition) all stated; the flag-partition pin, which fails
  the suite when a new pack flag is left unclassified, past the ask in
  the right direction; decisions 1 to 6 recommended for ratification,
  decision 4 an evidence candidate (§6 entry 186); the subdirectory
  outbox the operator's taste call alone; Proposals 1 and 2 to 104b, 3
  to 104b if `validate.sh` joined its forecast, 4 unscheduled.
- Ratified at the `2026-09-20-continue-plan-006` desk: that desk
  (read-only; packed 02:41:53Z, bale 0.4.39, by its brief) emitted one
  light block, three questions, at a tool-use pause it named as a
  pause, and the operator's next message, whole and verbatim, was "as
  assumed". The three, shortened: [1] ratify close 14's, 37's and 104a's
  notes.md wholesale, as shipped? [2] in a repo subdirectory, land the
  context pack under that subdirectory's `.bale/outbox/`, or the repo
  root's? [3] leave §5's fifteen compaction disclosures standing,
  bracketed as a hand count beside the records' seven? Every default is
  ratified. [1] settles close 14's notes.md (entry 176 taken; entry
  175's rule sentence kept; entry 171's attribution; row 37's bracket
  dated 2026-09-19 with the 2026-09-20 cut dated in its text; its other
  judgment calls), 37's (the pre-existing crash fix kept in the budget
  pressure pass; counts, not a rate; the own-line render; PLANNER.md
  §11 as the paragraph's home; no BALE.md edit), and 104a's decisions 1
  to 6, all as shipped. With it, the 004 desk's recommendation on 104a's
  Proposals is the disposition: 1, 2 and 3 ride 104b (2 as a droppable
  last rider; `validate.sh` joined 104b's forecast for 3), and 4 is
  unscheduled (§3 registry). [2] keeps the subdirectory, as shipped (row
  104's bracket; §5). [3] brackets the fifteen (§5). The judgment calls
  the 001 and 004 desks listed "for the operator" were not put to the
  operator by that desk and are not ratified by this reply; they queue
  on (the debt bullet below).
- Where the records part from the desks' accounts. Found by the 006
  desk: 37 took four attempts, where both accounts give a HOLD and "a
  retry", and neither mentions the `rejected` one (the previous block's
  landing record; §6 entry 187). Found at this close, against this
  close's brief, which says each of the two sittings "ended before its
  wave landed": this one's wave, 104a, landed six minutes before it
  ended, and the desk wrote its brief with 104a's notes.md in hand.
- Ratification debt carried forward. Unruled, the 001 desk's judgment
  calls: dating row 104's bracket 2026-09-20 inside a close that covers
  the 009 sitting; pinning the stats key names
  (`cross_checks.budget.compaction.{reporting_sessions,occurred_sessions}`,
  `members.compaction_occurred`) and the any-attempt definition;
  declining the two riders at 37 (the `format_hold_relay_planner`
  admissions, the post-epoch fixtures); leaving 104 to the next desk.
  Unruled, the 004 desk's: cutting 104 in two and leaving 104b; making
  the stale-comment rider non-droppable and probing it; pinning one
  VERBATIM sentence for TARBALL.md §3.1 (the desk's wording, not the
  operator's); the oracle's reading that "no sid" includes the day
  counter not advancing, and that the tarball lands under the packed
  directory; leaving non-repo behavior to the worker with the desk's
  reading stated; the broad `tests` directory forecast; recommending
  close 15 cover two sittings.
  Ratification debt carried forward, per convention: THIS close's notes.md queues to the following open.
- Sequencing for the next desk, verbatim from the 004 desk's brief:
  "Standing line after 104, verbatim from the 009 desk: "103 (design
  sitting) → the 100 arc → 43 → 45 → S6. Row 93 stands until the ledger
  shows its case." 103's design sitting forecasts nothing and can open
  beside any wave when the operator has the attention for a second
  desk." Its "104" is now 104b, dispatched beside this close.
- Board deltas of this sitting's work: row 104's second 2026-09-20
  bracket (cut in two; 104a DONE at 0.4.39; 104b dispatched; the
  spelling and the subdirectory outbox ruled); row 99's bracket, for the
  context pack's section; the first contract under "New, ratified
  2026-09-20" in §5; evidence entries 182–187 in §6, and 179, shared;
  the 0.4.39 landmark, where the context pack's tarball lands, the
  label-only verdict line and the heading-grep range rule in §7.
- Registry deltas of this sitting's work: consumed at 104a — the stale
  successor-pointer comment in `cmd_pack` (TARBALL.md §5.8's sentence,
  the other in-file rider, had no registry entry); carrier now 104b —
  the pack-json `sweep`/`include_group` key, `packed_at` on a pack's
  `opened` attempt (with its fourth specimen), and the closing pack's
  sid; the older pack-json `sweep` entry pointed at the newer; 105's
  stdlib-only pin bracketed with its carrier unconfirmed; three new
  entries — 104a's Proposals 1 to 3 (riding 104b), a context-pack line
  in `bale status` (104a's Proposal 4, unscheduled), and a dispositions
  entry for both sittings' workers.

Landed 2026-09-20, the continue-plan-006 sitting (master
`2026-09-20-continue-plan-006`, read-only; bale 0.4.39; packed 02:41:53Z
by that desk's account of its own manifest's `packed_at`, equal to its
record's `created_at`, and one second after the 004 master closed
(previous block); `closed-read-only` itself at 03:08:07Z by a pack, the
`2026-09-20-continue-plan-009` pack by that desk's account, whose
manifest's `packed_at` is the same second; the closure carries no
`swept_by`, the pack that swept it having run at 0.4.39). Two turns. The
sitting ended at delivery, so its desk could not close it: by the
records both its bundles were opened in its last thirteen seconds, at
03:07:54Z and 03:08:02Z, and by its own account it knew of neither. Its
record reached this close only as a quotation, byte for byte, inside the
009 desk's brief to the `2026-09-21-continue-plan-002` desk, carried
byte for byte again in this close's brief. Wave 8 landed whole — close
15 landed and 104b DONE; this block carries only what has no row home;
close recorded by `2026-09-21-sitting-close-deltas-16-004`:
- Landing record, in apply order from telemetry, both workers'
  provenance stamps reading 0.4.39:
  `2026-09-20-sitting-close-deltas-15-007` (packed 03:07:54Z by its
  echoed provenance, equal to its record's `created_at`; stamped base
  `77efdd47…`; applied 03:27:13Z; one apply attempt, confined, worker
  validation PASS and blind checkpoint PASS, exit 0, with the stamp
  matched, sha256 `ff44b69b…5a55`, equal to the sha the 006 desk
  published; no admissions; changed `claude/MASTER.md` alone; ten
  claims, all `agree`, reconciliation parsed, its epilogue the crafter's
  by its notes.md, one more data point for §6 entry 176's bracket), then
  `2026-09-20-board-104b-pack-telemetry-008` (packed 03:08:01Z by its
  echoed provenance, and its record's `created_at` reads 03:08:02Z, one
  second later, a fifth specimen for the §3 registry's `packed_at`
  entry; applied 03:45:15Z; one apply attempt, confined, worker
  validation PASS and blind checkpoint PASS, exit 0, with the stamp
  matched, sha256 `f5bb8388…b1ab1`, equal to the published sha; no
  admissions; the wave's bumper, 0.4.40 with
  `claude/changelog/0.4.40.json`, whose `at` reads 03:28:09Z; twelve
  `change_paths`, all under its forecast: `BALE.md`, `bin/VERSION`,
  `bin/bale_pack.py`, `bin/bale_report.py`, the changelog record,
  `schemas/telemetry-record.schema.json`, `validate.sh`, and five suites
  under `tests`, `test_context_pack.py`, `test_craft_response.py`,
  `test_include_group.py`, `test_provenance_at_open.py` and the new
  `test_pack_telemetry_104b.py`; six claims, each annotated
  `claim_basis: observed`, five `agree` and the `--slow` full suite
  `n/a`, reconciliation parsed). The two packed seven seconds apart and
  ran beside each other; close 15 applied eighteen minutes before 104b,
  and neither held. By their notes.md, each worker paused once on a
  tool-call limit and resumed with context intact (entry 163's class),
  and 104b took the suite from 1392 tests to 1419, 48 skipped by the
  slow gate both times, and `validate.sh` from 91 checks to 92. 104b's
  record reports `budget_pressure: tight`, close 15's `none`.
- Wave 8 as dispatched, from the 006 desk's record: two bundles,
  forecast-disjoint, meant to run beside each other.
  `2026-09-20-sitting-close-deltas-15` (close 15, `claude/MASTER.md`
  only, contract-doc, bumpless, covering the 001 and 004 sittings and
  recording that desk's one ruling; brief sha256 `09df1d16…e395f`) and
  `2026-09-20-board-104b-pack-telemetry` (row 104's second half, the
  bumper; forecast `bin/bale_pack.py`, `bin/bale_report.py`,
  `schemas/telemetry-record.schema.json`, `BALE.md`, `tests`,
  `validate.sh`, `bin/VERSION`, `claude/changelog`; brief sha256
  `5289ec80…4bd33`). Both checkpoint shas are in the landing record
  above, and the scope on 008's `opened` attempt is that forecast, path
  for path.
- Turn one, from the 006 desk's record. It read the contract in order,
  reordered its jobs (104b first, because close 15 needed rulings and
  104b did not), drafted 104b's oracle and ran it on the base, and hit
  the tool-use limit with no bundle built. The desk named the pause,
  said no bundle was ready, and closed the turn on one light block,
  three questions; the operator's next message, whole and verbatim, was
  "as assumed". The previous block's "Ratified at" bullet carries the
  three questions and what each settled. A pause with nothing built is
  the plain case beside entry 173's: nothing was caught between its
  write and its gate, and the desk used the pause to ask (§6 entry 179's
  bracket). A background full-suite run started in this turn did not
  survive the pause, 31 tests in. NOT done at the desk: a base suite
  run. 104b's brief attributed its baseline to 104a's notes.md and said
  so, and 104b's worker then ran it: 1392 tests OK, matching 104a's
  numbers (its notes.md). Turn two authored and delivered both bundles
  and the next master's.
- What the desk found in the code and the records, beyond what close 15
  already carries (37's four attempts, entry 187; close 14's parsed
  claims, entry 176's bracket; the one-second lags of 104a and the 001
  master, and the 004 master's closure one second before this desk's
  `packed_at`, all on the §3 registry's two close-13 entries): close
  13's Proposal 2 was half met before it was written, since a superseded
  attempt has carried `superseded_by` since 0.3.23 and only the
  read-only sweep lacked the closing pack's sid; that sweep runs before
  the sid is minted, so board 107's second-sweep lesson applied, and
  104b's brief carried both facts (§6 entry 188). And §5's calibration
  ruling is six lines, not two: the desk's first draft of close 15's pin
  said two, and the oracle's base run caught it (§6 entry 191).
- Desk verification before delivery, in the 006 desk's words, shortened.
  104b's oracle: a control block and fifteen probes, driving the real
  CLI in four fresh scratch repos under one scratch directory beside the
  tree, isolated `HOME`, `python3 -B`, removed on exit; one control
  drives the read-only sweep's accept prompt through a pty on stdin
  only, so the JSON line stays clean; a failed control exits 2 (§5).
  Base: exit 1, two invariant probes passing. A landing whose pinned
  names were pulled from the brief's bytes by regex, over a throwaway
  stub of the feature (the desk's, not the brief's): exit 0. Five
  negative landings each failed exactly one probe. The rehearsal caught
  one oracle defect: the non-stdlib mutation was `import requests`,
  which a network denylist alone catches; it is now `import yaml`. Close
  15's oracle: twenty anchors, twenty-two probes. Base: exit 1, three
  passing (row 113 last, insertions-only, cited sids). A landing built
  from the brief's pinned openings, pulled by regex: exit 0. Seven
  negative landings bit. A HEAD that is not the authored base: the two
  base-relative probes SKIP by name. A removed heading: exit 2. The
  rehearsals caught three oracle defects (the six-line ruling; the sid
  probe cascading off a lost base line; the sid regex taking the row
  number inside 104b's bundle stem for a counter) and none in the brief
  (§6 entry 191). Both bundles were dress-rehearsed with `bale open` in
  one scratch repo beside a read-only master: admitted together,
  expected-HOLD proofs fired (exit 1), and both oracles ran confined
  under the real sandbox, the pty control included; that desk's
  container runs `unshare` (§6 entry 190; §7). Both oracles print the
  label alone on a verdict line and detail on a following `  detail:`
  line (§6 entry 180).
- Ratified at the `2026-09-20-continue-plan-009` desk: this desk's ten
  judgment calls "for the operator", as shipped, after that desk's
  review of them against the tree, by the operator's
  "ratify the outstanding questions" and his "as assumed" to that desk's
  light block one, [1] (next block, ruling 1). The ten, from this desk's
  record: reordering the jobs; 104b as one session rather than two;
  leaving `bin/bale` out of its forecast; riding 104a's Proposals 1 to 3
  on it before the light block was answered (it was answered before
  delivery); pinning the pack-json key names, `sid` on sweep entries and
  the `-k stdlib_only` selector, while leaving `packed_at`'s home and
  the sweeping-pack field's name to the worker; declining the
  `format_hold_relay_planner` rider again and rewording its ride
  condition; a control failure exiting 2 rather than failing by name,
  where the 004 desk chose the other way; close 15 as two blocks; the §5
  contract bullets' wording; and not putting the 001 and 004 desks' own
  judgment calls to the operator. How three of them fell: 104b changed
  nothing in `bin/bale`, which already returned the sweep result its two
  pack call sites discarded (its notes.md); the `-k stdlib_only`
  selector was pinned without `tests/test_craft_response.py` read, and
  the pin it was to select already existed (§6 entry 188); and the
  exit-2 control is now the rule (§5).
- Where the records part from this desk's account. Its brief to close 15
  said each of the 001 and 004 sittings ended before its wave landed;
  close 15 found the 004 sitting did not (previous block), and the 009
  desk's records agree. Its stdlib-only rider asked for a pin the tree
  already had (the §3 registry's bracket on 105's pin). It expected
  0.4.40 and could not know it; the changelog record confirms it.
- Ratification debt this sitting carried forward: close 15's and 104b's
  notes.md, ruled wholesale at the `2026-09-20-continue-plan-009` desk
  (next block, ruling 4); the 001 and 004 desks' judgment calls and this
  desk's own, ruled there too (ruling 1). Nothing of this sitting's
  queues on.
- Sequencing for the next desk: the 006 desk's own sequencing did not
  reach this close. The 009 brief quotes the 006 brief only from its
  "Wave 8, as dispatched" heading to the line before its "Second job"
  heading, the range that lost the 001 desk's line at close 15 (§6 entry
  177). What the range does carry is a condition, verbatim: "If close 15
  has not landed when you open, do not author close 16; that is the 004
  desk's lesson (its first job was unbuildable by construction)." The
  009 desk met exactly that. The standing line that did travel is in the
  next block.
- Board deltas of this sitting's work: row 104's 104b DONE bracket,
  which completes the row as narrowed; the second contract of §5's new
  2026-09-20 block, a pack recording what it swept and when it was
  packed; in §6, evidence entries 190 and 191, entry 188 shared with the
  next block, entry 179's bracket, and entry 194, which reads 104b's two
  fields on their first live records; in §7, the 0.4.40 landmark, what
  `bale pack --json` and a record now carry, the `-k stdlib_only`
  selector, and the real-sandbox rehearsal.
- Registry deltas of this sitting's work: consumed at 104b — the
  pack-json `sweep`/`include_group` key, `packed_at` on a pack's
  `opened` attempt, the closing pack's sid (as `swept_by`), 104a's
  Proposals 1 and 3, and 105's stdlib-only pin, its carrier settled by
  104b's item 4; the older pack-json `sweep` entry pointed at the
  consumed one; three new entries from its two workers — a cause on a
  `rejected` attempt (close 15's Proposal 1), a `swept_by` line in the
  `bale stats` dossier (104b's Proposal 1), and the cap/breach loop
  (104a's Proposal 2, not taken at 104b and back on the list); the
  dispositions entry at the list's end covers both sittings.

Landed 2026-09-20, the continue-plan-009 sitting (master
`2026-09-20-continue-plan-009`, read-only; bale 0.4.39 at its open;
packed 03:08:07Z by that desk's account of its own manifest's
`packed_at`, the second its pack closed the 006 master
`closed-read-only`, and its record's `created_at` reads 03:08:08Z, one
second later; `closed-read-only` itself at 03:52:11Z by a pack, and for
the first time the record says which: the closure's `swept_by` names
`2026-09-20-board-103-probe-design-010`, the pack that opened 103's
design sitting that second, §6 entry 194). Four turns, no tool-use
pause. It packed thirteen seconds after close 15 was packed and six
after 104b; both applied under it, at 03:27:13Z and 03:45:15Z, and its
tarball could show neither (§6 entry 182's bracket). The desk ended its
sitting at the wave-8 landing milestone and handed the close forward;
its brief to the `2026-09-21-continue-plan-002` desk is this close's
source, carried byte for byte in this close's brief, and that desk
authored this close. This block carries only what has no row home; close
recorded by `2026-09-21-sitting-close-deltas-16-004`:
- Turn one. The operator's message beside the opener, whole and
  verbatim: "ratify the outstanding questions". The desk read the
  contract in order, found 007 and 008 `opened` with no apply attempt,
  and did not author close 16 (the 006 desk's condition, previous
  block). It read the message as the operator's ruling, reviewed the 006
  desk's ten judgment calls against the tree, and closed the turn on
  light block one, three questions, verbatim, its rows joined by " / ":
  "[1] question: Does "ratify the outstanding questions" cover the 001,
  004 and 006 desks' judgment calls, and stop short of close 15's and
  104b's notes.md? / while doing: recording your ruling verbatim for
  close 16's brief / would assume: yes; the two notes.md queue to the
  first open after they land / why blocked: neither notes.md exists yet,
  so ratifying them now would be a blank cheque / [2] question: From
  here on, does a failed oracle control exit 2 (the 006 desk's way)
  rather than fail by name (the 004 desk's)? / while doing: ratifying
  both desks' calls as shipped, which leaves the next oracle two
  conventions / would assume: yes, exit 2 / why blocked: bale already
  reads exit 2 as a defective oracle at open and as the checkpoint side
  on the hold card / [3] question: Author 103's design-sitting bundle
  next, to open beside wave 8? / while doing: the brief's second job;
  close 16 waits on close 15 landing / would assume: yes / why blocked:
  this turn asked for the ratification only, and I author sessions on
  your request". The operator's next message, whole and verbatim:
  "as assumed, still waiting on 104b and close 15 to finish". Answered
  first time (§6 entry 179's bracket).
- Rulings at the desk, by its record. 1, by light block one's [1]:
  "ratify the outstanding questions" covers the 001, 004 and 006 desks'
  judgment calls "for the operator", and stops short of the two notes.md
  that did not exist yet. The 006 desk's ten are ratified as shipped
  after this desk's review (previous block). The 001 and 004 desks'
  calls were ratified sight unseen, their text being in no file this
  desk held, and its brief asked this close to cite them from close 15's
  landed blocks or to say they are not there. They are there: the 004
  block's debt bullet lists both desks' calls as unruled, four of the
  001 desk's and seven of the 004 desk's, and ruling 1 ratifies the
  eleven as that bullet lists them. 2, by [2]: from here on a failed
  oracle control exits 2; the desk's reason and the contract are in §5.
  3, by [3]: 103's design sitting authored at this desk. 4, by light
  block two's [1]: close 15's and 104b's notes.md ratified wholesale,
  with the dispositions below. 5, by its [2]: the sitting ends, and the
  next master authors close 16.
- Turn two authored 103's design-sitting bundle, revision 1. Turn three:
  the operator pasted both ratification relays under the one word
  "applied:", each reading PASS on both judgments with no admissions, as
  the records do (previous block). The desk reviewed both notes.md, gave
  its dispositions in chat, and closed the turn on light block two, two
  questions, verbatim, rows joined as above: "[1] question: Ratify close
  15's and 104b's notes.md wholesale, with the dispositions in the reply
  above (three Proposals and riders to the registry, 105's pin consumed
  at 104b, no bracket for the 001 desk's standing line)? / while doing:
  the ratification debt the 006 desk's brief queued to this open, now
  that both have applied / would assume: yes / why blocked: notes.md
  ratification is yours, and silence is not "as assumed" / [2] question:
  End this sitting here, and have the next master author close 16 from
  the landed tree? / while doing: close 16 needs the landed
  claude/MASTER.md and the 007, 008 and 009 records, none of which this
  tarball holds / would assume: yes; on your reply I author the next
  master's bundle, its brief carrying this sitting's record / why
  blocked: a repack ships the landed tree with a fresh budget, and this
  context is already long for a twenty-anchor oracle and its
  rehearsals". The operator's next message, whole and verbatim:
  "i haven't opened the 103 bundle so reauthor, and closing is fine, i'll append my 103 notes to the opening of the next master. Otherwise, as assumed".
  Answered first time, with one inline change and "Otherwise, as
  assumed", the mixed reply TARBALL.md §5.10 draws. The block followed
  the "applied:" paste rather than preceding it, so entry 175's loss had
  no room to happen. Turn four authored 103's revision 2 and the next
  master's bundle.
- Dispositions, ratified by ruling 4, from the desk's record, shortened.
  Close 15's notes.md: both partings accepted, the records having won,
  and no correcting bracket for the 001 desk's standing line, since the
  line that traveled is the same one; entry 187 stays on two readings,
  and its bracket carries this desk's read of 37's record, which does
  not settle it; its Proposal 1 to the §3 registry; the 006 content it
  landed under the manifest's out-of-scope line accepted as shipped, the
  contradiction being the 006 desk's, whose manifest said one thing
  while its brief and oracle pinned another; its four unpinned brackets,
  the entry-179 counter-specimen, the block split, the one-line
  verbatims and the post-epoch bracket accepted as shipped; and row 37's
  unbuilt §11.4 pointer to be checked for a registry home, which it
  lacked and now has. 104b's notes.md: the six-key sweep entry ratified
  at the desk, the pin having been a floor; the kept-but-nulled entry
  under `[apply] sweep` off, the structured `include_group` with `row`
  verbatim, `packed_at` on the attempt's copy of provenance only, and
  `swept_by` stamped after the sid and committed, all accepted as
  shipped (§5); item 4, the rename in place of a second walker,
  accepted, which consumes 105's pin; "desk" and "sitting" stand in the
  two schema descriptions, since PLANNER.md uses both words; its
  Proposal 1 to the registry; 104a's Proposal 2 not taken and back on
  the registry, and 104a's Proposal 4 still unscheduled.
- What the desk found. Row 103 names `cost.model_tier` as its telemetry
  home, and `bin/bale_report.py` at 0.4.39 stamps the cost block
  all-null and reserves it for the harness, in the code's words as the
  desk quotes them, "never a worker self-estimate, never typed by a
  human"; what exists is the self-reported `model_identity` in the
  response manifest's provenance echo. The row's "identical argv" N ways
  meets the pack-time disjointness gate, and the tree moves once any run
  applies. Both went to 103's design desk in its brief (row 103's
  bracket; §6 entry 189). The `format_hold_relay_planner` rider: the
  registry text this desk held still said it "rides the next
  `bin/bale_report.py` touch", 104b held that file, and the desk never
  saw the 006 desk's rewording; the `2026-09-21-continue-plan-002` desk
  read the reworded condition on the landed tree and found that neither
  wave-8 session met it, so the entry stands untouched. And a bundle the
  desk did not write appeared in its outputs directory at 03:25:14Z,
  three minutes before its own 103 bundle (§6 entry 193).
- 103's design sitting, as delivered, by the desk's record: revision 1,
  `2026-09-20-board-103-probe-design`, brief sha256 `23eb1d75…584eb`,
  never opened and stale once wave 8 applied; revision 2,
  `2026-09-20-board-103-probe-design-r2`, the same slug and argv (the
  goal, `--slug board-103-probe-design`, `--read-only`,
  `--work-class meta`, whole-tree includes), checkpoint member null,
  derived from revision 1 by asserted string edits (the wave-8 section
  trued to "landed", find-by-phrase for the row, a line about the
  operator's notes, the sweep paragraph). Its brief's sha256 was given
  in that desk's chat and did not travel. What the records show of the
  sitting being opened is on row 103's bracket.
- The sweep at the next open. The 009 brief told its successor that the
  operator had been told to decline the read-only sweep while 103's
  sitting and the next master were both live. The record shows the
  `2026-09-21-continue-plan-002` pack swept
  `2026-09-21-board-103-probe-design-001` at 02:59:37Z, and its
  `swept_by` says so. By that desk's brief to this close, the operator
  has since ratified, by "as assumed" to a light block there, that the
  sweep was intended and the sitting was over; and his 103 notes,
  promised beside that desk's opener, arrived with his next message.
  Both are recorded as facts, not as findings against anyone.
- Desk verification before delivery, in the 009 desk's words, shortened.
  Both of 103's revisions and the next master's bundle were
  dress-rehearsed with the real `bale open` in a scratch repo built from
  the desk's tarball tree, isolated `HOME`, stdin piped: each packed
  clean, and the report echoed the brief's heading and the published
  sha256. The crafter warns that a checkpoint-configured project refuses
  an oracle-less bundle; under `--read-only` it does not. Revision 2 was
  opened first and the master's bundle second in the same scratch repo:
  the read-only sweep found the 103 session and, stdin not being a TTY,
  declined without a prompt. NOT exercised: the sweep's accept path at a
  TTY, `swept_by`, and anything on the landed tree. No oracle was
  authored at this desk.
- Why the sitting ended here, by the desk's record: close 16 needs the
  landed tree, which a repack ships, and the desk had spent context
  carelessly on two reads, a telemetry dump of all of 2026-09-20's
  records where three were needed, and a heading-to-heading range over
  TARBALL.md from `### 5.10` to `## 6` that printed §7, §3 and §4 as
  well (§6 entry 192).
- Where the briefs and the records part, found at this close. The 009
  desk expected 0.4.40 and could not confirm it;
  `claude/changelog/0.4.40.json` confirms it. It did not know apply
  times, attempt counts or whether either session held; the records say
  one apply attempt each and no hold (previous block). It could not know
  whether revision 2 was opened, and no record names a bundle, so that
  is still in no record (row 103's bracket). Its sweep instruction and
  the record part as the bullet above says. And this close's own brief
  calls the `base_files` map in 008's record a 100-entry map, where the
  record's echo holds 115 (§6 entry 192).
- Ratification debt carried forward. Unruled, the 009 desk's judgment
  calls, from its record: reading "ratify the outstanding questions" as
  a ruling and then asking its reach in a block; ratifying the 001 and
  004 desks' calls sight unseen rather than probing for close 15's
  brief; whole-tree includes for 103's sitting; telling 103's desk it is
  not a master; a `-r2` stem over the same slug; ratifying 104b's
  six-key entry at the desk instead of putting it to the operator;
  ending the sitting instead of asking for the landed `claude/MASTER.md`
  by upload; carrying the 006 record verbatim instead of digesting it.
  Wave 8's two notes.md are ratified and carry nothing forward. The
  `2026-09-21-continue-plan-002` desk's own calls belong to its sitting,
  which is still open, and that sitting's close records them.
  Ratification debt carried forward, per convention: THIS close's notes.md queues to the following open.
- Sequencing for the next desk, verbatim from the 009 desk's brief:
  "Standing line, verbatim from the 2026-09-19 009 desk: "103 (design
  sitting) → the 100 arc → 43 → 45 → S6. Row 93 stands until the ledger
  shows its case."" 103's design sitting has since run (row 103's
  bracket), and what it found is close 17's to record.
- Board deltas of this sitting's work: row 103's bracket; the first
  contract of §5's new 2026-09-20 block, a failed oracle control exiting
  2; in §6, entry 187's bracket, the brackets on entries 174, 179
  (shared) and 182, and evidence entries 188 (shared), 189, 192, 193 and
  194. No new rows: the board still ends at row 113, both wave-8
  Proposals having gone to the registry by ruling 4.
- Registry deltas of this sitting's work: the previous block's five
  consumed brackets and three new entries are this desk's dispositions
  of the 006 desk's wave (ruling 4); two new entries of its own — the
  `docs/CLAUDE.md` §11.4 pointer that row 37 left unbuilt, which no
  entry carried, and a rider for the next `docs/PLANNER.md` holder, so
  that ruling 2's contract gets a home in PLANNER.md §4; the
  `format_hold_relay_planner` entry left as close 15 reworded it; the
  dispositions entry at the list's end covers both sittings.

Landed 2026-09-21, the continue-plan-002 sitting (master
`2026-09-21-continue-plan-002`, read-only, work class meta; bale 0.4.40;
packed 02:59:37Z by its record's `packed_at`, and its `created_at` reads
02:59:38Z, one second later; its pack swept
`2026-09-21-board-103-probe-design-001` that same second, as that
closure's `swept_by` says (row 103's bracket); `closed-read-only` itself
at 12:20:35Z by the `2026-09-21-continue-plan-005` pack, which its
`swept_by` names and whose `packed_at` is the same second). Nine turns,
one tool-use pause, four light blocks, two probes. Its own record was
not in its tarball. During the sitting, earlier tool outputs were
cleared from the desk's context to save space, its own replies staying,
and it told the operator so at turn seven. It authored close 16 in two
revisions and a wave-10 master bundle it then replaced, and handed close
17 on. Its brief to the `2026-09-21-continue-plan-005` desk, carried
byte for byte inside that desk's brief to the
`2026-09-21-continue-plan-008` desk and again in this close's brief, is
this block's source, from its "Wave 9, as landed" heading to the line
before its "First job". This block carries only what has no row home;
close recorded by `2026-09-21-sitting-close-deltas-17-009`:
- Wave 9's landing, from a read-only probe the operator ran on his tree
  at the desk's request and pasted back (its integrity trailer counted
  and matched, 68 lines), each fact checked against the record at this
  close: `2026-09-21-sitting-close-deltas-16-004` opened 11:49:14Z,
  `packed_at` the same second, and applied 12:10:46Z by `apply`, one
  apply attempt, confined, network grant exercised; blind checkpoint
  PASS, exit 0, stamp matched, no failed probes, sha256 `89ae8373…ac32`,
  equal to the sha the desk published; worker validation PASS, ten
  claims, all `agree`, reconciliation parsed; `change_paths`
  `claude/MASTER.md` alone; the relay read "admissions: none". The
  landed file: 9551 lines, sha256 `3cda112d…51ee`, line 14 naming that
  session, 773 lines inserted on the 8778-line base. Its notes.md: 15620
  bytes, sha256 `29847ba4…6201`, which the desk read from bale's relay
  block and did not hash; this close hashed the archived copy under
  `claude/responses/`, and it matches. The bundle opened was revision 2,
  `2026-09-21-sitting-close-deltas-16-r2.bale-bundle` (brief sha256
  `137047a8…4df0`), known only because the notes repeat facts that are
  in revision 2's brief alone; revision 1 (brief `1446b7ce…a529b`, the
  same checkpoint bytes) was delivered a turn earlier and never opened
  (§6 entry 194's bracket). `bale status` at 12:10Z or after, by the
  desk's account: two open sessions, both read-only,
  `2026-09-21-board-103-probe-findings-003` and the desk; 301 applied;
  main with "2 uncommitted change(s)", which the desk could not
  identify. The findings sitting's pack did not close the desk.
- Where the desk's brief to close 16 and the records parted, as close
  16's worker found and the desk owned at turn six: the `base_files` map
  in 008's record, a 100-entry map by the brief and to the operator,
  holds 115 (§6 entry 192); and the 009 brief, carried whole as that
  brief's Part 2, quotes the 006 brief only to the line before its
  "Second job", so the 006 desk's sequencing never reached the worker,
  the third close running to lose a standing line that way (§6 entry
  177; close 16's 006 block). Close 16's Proposal 2 was the remedy and
  has landed (§3 registry).
- Turn one. The desk read the contract in order and the 006, 007, 008,
  009 and both 103 records; authored close 16's brief and oracle;
  rehearsed; built and dress-rehearsed the bundle; and hit the tool-use
  limit before copying it to the outputs directory. It named the pause,
  said the bundle was built and not delivered, and closed on light block
  one, hand-authored per TARBALL.md §5.10 because the crafter was out of
  reach that turn, three questions, verbatim, its rows joined by " / ":
  "[1] question: Was closing 103's design sitting with my pack intended,
  so that sitting is over and its notes and output come to this desk? /
  while doing: the second job; no 103 notes arrived beside my opener,
  and the record shows my pack swept
  2026-09-21-board-103-probe-design-001 / would assume: yes; paste your
  notes and what the sitting produced, and no revision 3 is owed / why
  blocked: the 009 brief said you would decline that sweep, and no
  record says which revision you opened or what came of it / [2]
  question: Should close 16 pin ruling 2 (a failed oracle control exits
  2) as a §5 contract with a PLANNER.md §4 rider, and add no board rows
  for the two wave-8 Proposals? / while doing: the bundle is built and
  rehearsed on these pins; a change means a derived v2 before delivery /
  would assume: yes / why blocked: the 009 brief left the pin to me, and
  it is your contract list / [3] question: Author the apply-side and
  stats-side rider micro (rejected-attempt cause, held admissions in the
  planner relay, swept_by dossier line) at this desk, beside close 16? /
  while doing: packing disjointly; its files would not touch
  claude/MASTER.md (a guess, no code read yet) / would assume: no; close
  16 goes alone, and the next master authors the micro on a fresh budget
  / why blocked: I author sessions on your request, and this context is
  already long for a code oracle and its rehearsals". The operator's
  next message, whole and verbatim: "as assumed, here's the notes:",
  with `board-103-wave1-findings.md` attached (§6 entry 173's bracket).
- Turn two delivered close 16's revision 1, read the findings whole,
  checked two of their "Not verified" items on the tree, gave the
  triage, and closed on light block two, verbatim, rows joined as above:
  "[1] question: Should 103's doc proposals 1 to 6 and 10 land as their
  own doc-lane session now (docs/TARBALL.md, docs/CLAUDE.md), ahead of
  the 100 arc's sweep rather than inside it? / while doing: triaging
  your findings into wave 10 / would assume: yes; 7, 8, 9 and 11 wait as
  rows or as inputs to the arc's design sitting / why blocked: row 100
  says 103's findings feed the sweep, and sequencing is yours / [2]
  question: Does the 100 arc's design sitting open beside 103's wave
  two, with only the arc's doc sweep waiting on wave two's findings? /
  while doing: rewording the standing line for the next desk / would
  assume: yes; both are read-only or out-of-repo, so they are disjoint,
  and only the sweep depends on the findings / why blocked: the standing
  line reads "103 → the 100 arc" as one arrow, and the wave split it in
  two / [3] question: End this sitting here, and on your reply I author
  the next master's bundle, which authors wave 10 beside close 16 and
  close 17 after it lands? / while doing: close 16 is delivered, a
  milestone, and this context is long for three more oracles / would
  assume: yes; its brief carries this sitting's record, the triage and
  your findings' §7 and §8 verbatim (no bait in either), and you attach
  the full findings file beside its opener / why blocked: the findings
  file carries the kit's oracle, so I will not put it whole into a
  request without your say". The operator's reply is the message row
  103's 2026-09-21 bracket quotes whole, which also left close 16, not
  yet packed, open to reauthoring.
- Turn three derived close 16's revision 2 from revision 1 (four
  asserted string edits, the oracle unchanged) and authored the wave-10
  master bundle, `2026-09-21-continue-plan-wave-10.bale-bundle` (brief
  sha256 `b4f34e6b…d4ea`). Turn four: the operator, whole and verbatim:
  "I'm going to return the close 16 notes to you so you can reauthor the continue-plan bundle and we can start fresh instead of needing notes to begin".
  Nothing was attached. The desk said so and closed on a paste-back
  probe, `continue-plan-close-16-landing`, the crafter's skeleton
  filled, rehearsed in a scratch repo and against close 15's applied
  record, for the record facts in the landing bullet above (§6 entry
  195). Turn five: the operator, whole and verbatim:
  "still waiting on close 16 to finish, but I have a quick question. When do we tackle the issues that the 103 test uncovered? Is that next on the docket?".
  The desk answered in prose, with no block: wave 10 is those fixes;
  what waits as rows; what is the kit's and not this repo's.
- Turn six. The operator pasted close 16's ratification relay and the
  probe's output, with no prose. The desk read both, owned the two
  partings above, gave its read of the worker's calls, listed its own,
  and closed on light block three, rendered by the crafter, verbatim:
  "[1] question: Ratify close 16's judgment calls as its notes.md lists
  them, ruling 1 reaching the eleven calls in the 004 block's debt
  bullet, with the six rule sentences in the worker's words left for the
  next master to read on its tree and report? / while doing: clearing
  close 16's ratification debt at this desk, so the next master opens
  owing none; I have not seen the landed text of those sentences / would
  assume: yes / why blocked: the notes put these to you, and the 009
  desk already ratified one set sight unseen, which close 16 had to flag
  / [2] question: Accept both of close 16's Proposals: 1 (stamp the
  bundle on an opened attempt) into wave 10's rider micro, since it
  shares the telemetry schema, and 2 (the standing line inside a
  master's sitting record) as desk practice from the next brief on, with
  a PLANNER.md rider? / while doing: writing dispositions into the next
  master's brief; this close already needed Proposal 1, since I can tell
  revision 2 was opened only from what the notes repeat / would assume:
  yes / why blocked: Proposals are yours to dispose, and 1 adds a file
  to a session I cut without reading the code / [3] question: Ratify
  this desk's own judgment calls as listed above, my reading of your row
  103 message, and the standing line as: wave 10, then the 100 arc with
  its design sitting first, then 43, 45, S6; row 103 ongoing; row 93
  stands? / while doing: the next master's brief states these as ruled
  instead of carrying them as debt / would assume: yes / why blocked:
  sequencing and the board are yours, and a fresh start means none of
  this travels unruled".
- Turn seven. The operator, whole and verbatim, his line breaks shown as
  " / ":
  "1. what are the six sentences? please explain better / 2. yes / 3. yes / can't we just author close 17 here? and what does "carry the standing line inside its sitting record." mean?".
  The desk explained the six sentences, advised against authoring close
  17 at the desk (§6 entry 201), and closed on a second probe,
  `continue-plan-close-16-rule-sentences`, for the six. Turn eight: the
  operator, whole and verbatim:
  "fine with moving close 17 to the next session, and here's the probe:",
  with the probe's output (77 lines, counted and matched; the landed
  sha). The desk quoted the six with a read on each and closed on light
  block four, rendered by the crafter, verbatim: "[1] question: Ratify
  close 16's judgment calls as its notes.md lists them, ruling 1
  reaching the eleven, and all six rule sentences as landed, with close
  17 adding one bracket to entry 191: a negative landing per probe is
  the aim, and this desk ran thirteen for eighteen probes? / while
  doing: finishing block three's [1], which you asked me to explain
  rather than answered; your silence on it is not a yes / would assume:
  yes / why blocked: section 6 is doctrine later desks follow, the
  worker asked for overreach to be struck, and the file is
  insertions-only so a strike is a bracket / [2] question: Cut the work
  as two masters: the next one authors the doc lane (the 103 fixes) and
  close 17, both doc-only oracles, and its successor authors the tools
  micro and the rider micro? / while doing: writing the first-job
  section of the replacement continue-plan bundle / would assume: yes /
  why blocked: the last five desks built one or two oracle bundles a
  sitting, four are queued, and the order is yours". The operator's next
  message, whole and verbatim: "as assumed". Turn nine authored the
  desk's brief to the next master and its bundle. Every block was
  answered first time; block three's [1] was answered with a question,
  which the desk treated as no answer and put again in block four (§6
  entry 179's bracket and entry 197).
- Rulings at the desk, all the operator's, from its record, shortened.
  1, block one's [1]: the sweep of 103's design sitting was intended,
  that sitting is over, and no revision 3 of its bundle is owed. 2,
  block one's [2]: close 16 pins a failed oracle control exiting 2 as a
  §5 contract with a PLANNER.md §4 rider, and adds no rows for wave 8's
  Proposals. 3, block one's [3] and block two's [3]: no micro at the
  desk; the sitting ends at a milestone. 4, block two's [1]: the
  findings' Proposals 1 to 6 and 10 land as their own doc-lane session
  ahead of the 100 arc's sweep, and 7, 8, 9 and 11 wait as rows or as
  inputs to the arc's design sitting (rows 115 to 118). 5, block two's
  [2]: ratified and mooted in one message. 6: the row 103 ruling (row
  103's bracket). 7, block three's [2]: both of close 16's Proposals
  accepted, 1 into wave 10's rider micro and 2 as desk practice with a
  PLANNER.md rider (§3 registry). 8, block three's [3]: the desk's calls
  to that point, its reading of the row 103 message, and the standing
  line. 9, block four's [1]: close 16's judgment calls ratified as its
  notes.md lists them, the 009 desk's ruling 1 reaching "the eleven as
  that bullet lists them", all six rule sentences ratified as landed,
  and one bracket on §6 entry 191. 10, block four's [2]: the two-master
  cut (sequencing, below). 11, in prose at turn eight: close 17 moves to
  the next desk.
- The calls block three's [3] ratified, as the desk listed them to the
  operator: wave 8's landing record in the 006 block; row 103's bracket
  dated 2026-09-20 with 2026-09-21 facts dated in its text; the 009
  brief carried whole as Part 2; close 16 not covering this sitting;
  telling close 16's worker not to write the findings sitting's sid; a
  `-r2` stem over revision 1's checkpoint bytes; loosening the registry
  probe to a floor after rehearsal; embedding only the findings' §7 and
  §8 (§6 entry 200); cutting wave 10 three ways without reading the
  code; reading the row 103 message as mooting block two's [2]; asking
  for a probe rather than waiting on the attachment alone; queueing the
  six rule sentences to the next master, superseded at turn seven when
  the operator asked to see them and they were ruled at the desk.
- What the desk found, beyond what close 16 already carries (the first
  live `swept_by` and `packed_at`, §6 entry 194; 103's design sitting as
  two sessions, row 103's bracket). Row 103 says "`bale validate`, then
  apply or HOLD", and 0.4.40 has no `validate` verb: fifteen in
  `bin/bale`'s parser, with `init` and `hooks` under `config`, so the
  findings desk's "half confirmed" is confirmed whole (row 118; §7). The
  desk first told the operator seventeen, counting those two, and
  corrected it a turn later (§6 entry 198). A pack with no `--include`
  takes the whole tree, `bin/bale_pack.py`'s "whole-tree default", and
  the replaced bundle's dress rehearsal packed 618 files that way. The
  crafter's `--light-block FILE` takes a clarification manifest and
  `--probe SLUG` emits the §4.2 skeleton; both worked first time at the
  desk (§7).
- Desk verification before delivery, in the desk's words, shortened.
  Close 16's oracle: 22 anchors and, as its control, a self-test of the
  session-id pattern; 18 probes; label-only verdict lines; a failed
  control exits 2. Base: exit 1, three passing. A landing built by regex
  from the brief's 25 fenced pins: exit 0, re-run from revision 2's
  final bytes. Thirteen negative runs: eleven each failed exactly the
  one probe mutated (probes 1, 2, 3, 6, 7, 8, 9, 10, 12, 16 and 18), one
  cited bundle stems and stayed exit 0 as it should, and one removed a
  heading and exited 2; probes 4, 5, 11, 13, 14, 15 and 17 never had a
  negative of their own (§6 entry 191's bracket). Beside the thirteen:
  one extra registry entry before the pinned six, exit 0; HEAD not the
  authored base, the two base-relative probes SKIP by name. Rehearsal
  caught two cascade defects in the oracle and none in the brief (§6
  entry 199). Revision 1 went through the real `bale open` in a scratch
  repo, isolated `HOME`, stdin piped, confined with `unshare`: the
  expected-HOLD proof fired, the pack replayed clean, the echoes
  matched. Revision 2 was not dress-rehearsed, having revision 1's argv
  and checkpoint bytes, and neither had an apply-side run of the oracle.
  The desk's own bundle was not dress-rehearsed either; its argv is the
  replaced bundle's, token for token, and that one was (admitted beside
  an open close-16 session, the read-only checkpoint waiver fired, 618
  files, the brief's heading and sha echoed). Not exercised: the sweep's
  accept path. Both probes were rehearsed before they were sent and came
  back whole. Close 16 then landed on a first apply, with no hold.
- Where the desk's brief and the records part, found at this close:
  nowhere. Every record fact it gives that a record on this tree holds
  checks out by key, second for second; the `bale status` counts are its
  word. One fill: the desk's own closure, which it could not see, came
  at 12:20:35Z from the 005 pack, four seconds after that pack closed
  the findings sitting (§6 entry 194's bracket).
- Ratification debt this sitting carried forward. None from close 16,
  whose notes.md was ratified whole at the desk (ruling 9), and none
  from the desk's calls through block three (ruling 8). Its brief named
  two small calls as unruled: entry 191's bracket's eleven-and-seven
  split, which corrects the desk's looser account to the operator, and
  taking close 17's base facts from a worker's notes and two probes
  rather than from the file. The first was ratified at the
  `2026-09-21-continue-plan-008` desk (next block, its "Ratified at"
  bullet); the second went moot when the 005 and 008 desks verified
  those facts on their trees and this close on the file itself. The 009
  desk's eight calls, which close 16's 009 block lists as unruled, were
  not put to the operator at this desk; they too were ratified at the
  008 desk (next block). Nothing of this sitting's queues on.
- Sequencing for the next desk: the standing line, ratified by the
  operator's "yes" to light block three's [3], in the block's words:
  "wave 10, then the 100 arc with its design sitting first, then 43, 45, S6; row 103 ongoing; row 93 stands".
  It replaced the 2026-09-19 line "103 (design sitting) → the 100 arc →
  43 → 45 → S6. Row 93 stands until the ledger shows its case." Wave 10
  was four bundles, cut by block four's [2] across two masters: the next
  desk authors the doc lane and close 17, both doc-only oracles, and its
  successor the tools micro and the rider micro. The 100 arc's design
  sitting waits on nothing but the operator's attention; the arc's doc
  sweep waited on the doc lane, which held the same files. The next
  block records the recut.
- Board deltas of this sitting's work: row 103's 2026-09-21 bracket, the
  operator's ruling and wave one's record; rows 114 to 119, from the
  desk's triage of the findings (ruling 4) and the ruling on row 103; in
  §6, entry 191's bracket, ratified at the desk and its split at the 008
  desk; the brackets on entries 173, 179 and 194, and evidence entries
  195 to 199 and 201, all shared with the next block; and entry 200.
- Registry deltas of this sitting's work: close 16's two Proposals, 1
  riding wave 10's rider micro and 2 born closed; the findings' §8 items
  1 to 4 as the two micros' sources; the dispositions entry at the
  list's end covers both sittings.

Landed 2026-09-21, the continue-plan-005 sitting (master
`2026-09-21-continue-plan-005`, read-only, work class meta; bale 0.4.40;
whole-tree pack; packed 12:20:35Z by its record's `packed_at`, and its
`created_at` reads 12:20:36Z, one second later; its pack swept both open
read-only sessions, `2026-09-21-board-103-probe-findings-003` at
12:20:31Z and the 002 master at 12:20:35Z, as their closures' `swept_by`
say, where the desk's brief says what its pack swept "is not known
here"; `closed-read-only` itself at 13:23:32Z by the
`2026-09-21-continue-plan-008` pack, which its `swept_by` names and
whose `packed_at` reads 13:23:33Z, one second later). Five turns, one
tool-use pause, four light blocks, one hand-authored and three rendered
by the crafter, no probes. It authored and dispatched wave 10's two
landings so far, the doc lane and the split-transition fix, and handed
close 17 on under a stop condition. Its brief to the
`2026-09-21-continue-plan-008` desk, carried byte for byte in this
close's brief, is this block's source, from its "Wave 10 so far, as
landed" heading to the line before its "First job". Wave 10's dispatch
and landing are recorded here, and the fix, a non-board landing with no
row, has its home here beside §5's new contract. This block carries only
what has no row home; close recorded by
`2026-09-21-sitting-close-deltas-17-009`:
- Wave 10 so far as dispatched, from the desk's record: two contract-doc
  bundles, bumpless, each one revision and opened as delivered. The doc
  lane, `2026-09-21-board-103-doc-lane.bale-bundle` (brief sha256
  `de492dd0…c321`, checkpoint sha256 `d409b23a…19a9`), carried the
  findings' Proposals 1 to 6 and 10 and row 37's §11.4 pointer; forecast
  `docs/CLAUDE.md`, `docs/TARBALL.md` and `tests/test_doc_crossrefs.py`.
  The fix (brief sha256 `29c4bdca…41bb`, checkpoint sha256
  `85bf13b5…308b`) carried the operator's split-transition ruling (§5)
  and both waiting `docs/PLANNER.md` riders; forecast `docs/CLAUDE.md`,
  `docs/PLANNER.md`, `docs/TARBALL.md` and
  `tests/test_sanctioned_pairs.py`. The two tools-side micros are the
  next master's.
- Landing record, in apply order from telemetry, both workers'
  provenance stamps reading 0.4.40: `2026-09-21-board-103-doc-lane-006`
  (opened 12:33:28Z, `packed_at` 12:33:27Z; applied 12:47:32Z; one apply
  attempt, confined, network grant exercised; blind checkpoint PASS,
  exit 0, stamp matched, no failed probes, sha256 `d409b23a…19a9`, equal
  to the published sha; worker validation PASS, eight claims, each
  `claim_basis: observed` and all `agree`, reconciliation parsed;
  `change_paths` its three forecast paths; no admissions;
  `budget_pressure: none`), then
  `2026-09-21-split-transition-unconditional-007` (opened 12:59:58Z,
  `packed_at` the same second; applied 13:18:33Z; one apply attempt,
  confined, network grant exercised; blind checkpoint PASS, exit 0,
  stamp matched, no failed probes, sha256 `85bf13b5…308b`, equal to the
  published sha; worker validation PASS, eight claims, each observed and
  all `agree`, reconciliation parsed; `change_paths` its four forecast
  paths; no admissions; `budget_pressure: none`). By their notes.md: the
  doc lane landed all seven deltas and the rider, both VERBATIM
  sentences as written, and `ByteDisciplinePins` in
  `tests/test_doc_crossrefs.py`, five tests, taking the three doc suites
  from 36 to 41; the fix landed its three VERBATIM sentences without
  correction, each checked against the docs and the crafter, and
  `tests/test_sanctioned_pairs.py` went from 2 tests to 4, the three doc
  suites to 43. Row 37's §11.4 pointer closed with the clause, and the
  fix, holding `docs/PLANNER.md`, carried both riders: the exit-2 bullet
  into §4 and close 16's Proposal 2 into §3 (§3 registry).
- Turn one. The desk read the contract in order, PLANNER.md's core, and
  TARBALL.md §3.4, §5.4, §5.9.2, §7 to §7.2 and §10.1 to §10.3; verified
  the manifest's six hashes, `docs/` byte-identical to the injected
  five, and `claude/MASTER.md` at 9551 lines, sha `3cda112d…51ee`. It
  authored the doc lane's brief and oracle, rehearsed, built and
  dress-rehearsed the bundle, and hit the tool-use limit before copying
  it out. It said so, and closed on light block one, hand-authored from
  the three crafter-rendered blocks in the 002 brief because the crafter
  was out of reach that turn and the desk had not yet read TARBALL.md
  §5.10 (§6 entry 173's bracket). The desk's brief gives this block
  RETYPED from its own reply, not read from a file, and says so; this
  close carries the retyped block, verbatim, its rows joined by " / ":
  "[1] question: board-103-wave1-findings.md did not arrive beside the
  opener; will you attach it with your reply? / while doing: the first
  job; only the request tarball is in uploads, and the doc lane is built
  without it / would assume: yes; you attach it, I handle it as its
  header says, and close 17's row 103 text waits on it / why blocked:
  your brief says close 17's row 103 text cannot start without it, and a
  probe cannot carry a 15 KB file / [2] question: Deliver the doc lane
  as built: two VERBATIM sentences, six required phrases, and Proposal 5
  ruled as marking the PLANNER.md §15 pointer planner-side rather than
  inlining? / while doing: the bundle is built and dress-rehearsed but
  not delivered; a change means a derived revision before it goes out /
  would assume: yes / why blocked: VERBATIM doc wording and the choice
  between Proposal 5's two alternatives are desk calls, and the five
  docs are your contract / [3] question: Author close 17 at this desk
  next turn, stopping to hand it to the next master in its brief if the
  budget reads thin once MASTER.md's tails and the findings are read? /
  while doing: packing disjointly; this context is already long from the
  doc lane's reads, oracle and rehearsals / would assume: yes, with that
  stop condition; the doc lane is delivered first either way / why
  blocked: the two-master cut put close 17 here, and the 002 desk
  already moved it once for a tired context". The operator's next
  message, whole and verbatim: "as assumed", with the findings file
  attached.
- Turn two delivered the doc lane and read the findings' header, §3 and
  §9 to §11. After delivery it found that §3.2's second refused paste
  block was a stale trailer on regenerated text, which the brief's Delta
  1 paragraph did not name, and it did not revise (§6 entry 196). It
  verified close 17's five base facts on its tree, invoked block one's
  stop condition, and closed on light block two, verbatim: "[1]
  question: End this sitting at the doc lane's delivery, with close 17
  going to a fresh master whose bundle I author on your reply, and that
  master's successor taking the two code micros? / while doing: invoking
  block one's stop condition; the five base facts your brief listed for
  close 17 are verified on the tree, but the brief, pins, oracle and
  rehearsals are a fresh desk's load, not what this context has left /
  would assume: yes; three masters instead of two, and the next brief
  carries this sitting's record, the verified base facts and the 002
  brief's close-17 and second-job sections derived, not rewritten / why
  blocked: the two-master cut is your ruling from the 002 desk's block
  four, and this changes it / [2] question: Should close 17 cover this
  sitting too (the 005 desk, wave 10's first bundle), beside the 002
  sitting and row 103's arc? / while doing: writing the next master's
  first-job section; a fresh desk is the second reader this sitting
  would otherwise lack, and one close is then owed instead of two /
  would assume: yes / why blocked: your brief scoped close 17 to the 002
  sitting and row 103's arc, and what a close covers is yours / [3]
  question: Leave the delivered doc-lane bundle as it is, now that the
  findings' section 3.2 shows the second refused block was a stale
  trailer on regenerated text and not an escape fault? / while doing:
  read the findings after delivery; VERBATIM-1's file-first and
  never-retype clauses cover that fault without naming it, and the
  brief's Why line is the findings' own words / would assume: yes; no
  revision 2, and the gap goes to close 17 as an evidence candidate /
  why blocked: you ruled deliver as built before I had read section 3.2,
  and a revision means superseding a bundle you may already have
  opened". The operator did not answer it. His next message, whole and
  verbatim:
  "applied, and I also ran into another issue while working on another project. The issue is described in the attached file. Let's tackle this now before the sitting close because it's important, unless you think it folds neatly into a queued session we'll run soon."
  With it came the doc lane's ratification relay and
  `finding-2026-09-21-split-role-transition.md` (sha256
  `88381f6b…ab70`), written by the doc lane's worker at his request.
- Turn three. The desk verified the finding's five carriers and
  PLANNER.md §20.1's sentence on its tree; answered that the fix folds
  into nothing queued and that the waiting PLANNER.md riders fold into
  it; gave its read of the doc lane's calls; treated block two's silence
  as no answer; and put block two's live questions again in light block
  three, verbatim: "[1] question: Rule the finding's Q1 to Q4 as it
  recommends: the transition is owed in every project and a checkpoint
  only adds the children's oracles; the bare line stays the offer's
  content and the bundle is its delivery everywhere; section 11.2 gains
  one clause pointing at PLANNER.md section 20.1's ratification hold;
  the worked example keeps its line and gains one sentence on the
  bundle? / while doing: the fix session's brief; I verified all five
  carriers and the section 20.1 sentence on this desk's tree, and
  PLANNER.md states the transition without condition in META, section 1,
  section 2 and section 20's first paragraph / would assume: yes to all
  four / why blocked: the finding calls these blocking for the brief and
  intent authority is yours; your remark in the other project's chat
  reads as Q1 yes but was not given as a ruling / [2] question: Author
  the fix at this desk on your reply, as its own doc session holding
  docs/CLAUDE.md, docs/TARBALL.md, docs/PLANNER.md and
  tests/test_sanctioned_pairs.py, carrying the two waiting PLANNER.md
  riders, to pack now, ahead of or beside close 17? / while doing:
  answering whether it folds: nothing queued soon holds these files
  (close 17 holds claude/MASTER.md, the micros hold code, the 100 arc's
  sweep waits on a design sitting), so the waiting riders fold into it,
  not it into them / would assume: yes; the finding did the reading, so
  this is well under close 17's load, and I key the oracle to headings
  and phrases because my copies of two of the files predate the doc
  lane's landing / why blocked: I invoked a stop condition on budget
  last turn, so authoring one more oracle here is your call, and the
  riders add PLANNER.md section 4 and section 6 touches to a session
  about section 20 / [3] question: After that bundle, end this sitting,
  with close 17 going to a fresh master and covering the 002 sitting,
  this sitting and row 103's arc, and that master's successor taking the
  two code micros? / while doing: last turn's block went unanswered,
  which I do not read as a yes; its third question is moot, since the
  doc lane applied with both verdicts PASS / would assume: yes; three
  masters instead of two, and the next brief carries this sitting's
  record and the base facts verified last turn / why blocked: the
  two-master cut and what a close covers are your rulings from the 002
  desk's block four and its brief". The operator's next message, whole
  and verbatim: "as assumed".
- Turn four authored, rehearsed, dress-rehearsed and delivered the fix
  bundle, drafted the next brief to disk, and closed on light block
  four. Before sending it the desk had written "six words" and then
  "twelve" for a clause it had not counted; counted, the clause is
  eleven, and the block says eleven (§6 entry 198). Block four,
  verbatim: "[1] question: Ratify the doc lane's judgment calls as its
  notes.md lists them, and dispose its three Proposals as: the crafter
  seeding forecast_departures joins the tools micro's sources, the
  post-validation tree walk becomes a new board row, and the section 5.9
  courier statement goes to the registry for that section's next holder?
  / while doing: clearing the doc lane's ratification debt here, so the
  next master opens owing none; my read of each call is in my last
  reply, and I would keep all of them / would assume: yes / why blocked:
  the notes put those calls to you, and Proposals and board rows are
  yours to dispose / [2] question: Ratify this desk's calls on the fix
  bundle: three VERBATIM sentences derived from carriers A, B and D by
  the smallest edit; Q3's clause worded as a hold plus a pointer to
  PLANNER.md section 20.1; and the finding shipped whole as the brief's
  appendix, incident account included? / while doing: the bundle is
  delivered and dress-rehearsed; a no means a derived revision 2 before
  you open it / would assume: yes / why blocked: VERBATIM contract
  wording is a desk call you may overrule, Q3 asked for a pointer and I
  added an eleven-word statement of the hold, and the incident account
  is from your other project / [3] question: Should I author the next
  master's bundle only after the fix session lands and you paste its
  relay, so that master opens on a clean wave with no notes to chase? /
  while doing: ending the sitting; the next brief is drafted to disk now
  with seven loud unfilled slots, and the fix's landing record fills
  three of them / would assume: yes; you run the fix, paste its relay
  here, and I finish and deliver the bundle in that turn / why blocked:
  you chose exactly this wait at the 002 desk, but it keeps this desk
  open one turn longer on a long context". The operator's next message,
  whole and verbatim: "as assumed", with the fix's ratification relay
  pasted above it. Turn five read the relay, checked one of the fix
  worker's open questions on the desk's tarball (the exec bit, below),
  finished the brief and delivered the next master's bundle, with no
  block: the sitting ended there.
- Rulings at the desk, all the operator's, from its record. 1, block
  one's [1] to [3]: the findings attached; the doc lane delivered as
  built; close 17 attempted at the desk under a stop condition. 2, block
  three's [1]: the finding's Q1 to Q4 as it recommends, the block's own
  words being the ruling's text (§5). 3, block three's [2]: the fix as
  its own doc session, authored at the desk, carrying the two PLANNER.md
  riders. 4, block three's [3]: the sitting ends after that bundle;
  close 17 goes to a fresh master and covers the 002 sitting, this
  sitting and row 103's arc; that master's successor takes the two code
  micros. 5, block four's [1]: the doc lane's judgment calls ratified as
  its notes.md lists them, and its three Proposals disposed: the crafter
  seeding `forecast_departures` joins the tools micro's sources, the
  post-validation tree walk becomes a new row (row 120), and the §5.9
  courier statement goes to the registry for that section's next holder.
  6, block four's [2]: the desk's calls on the fix bundle ratified,
  three VERBATIM sentences derived from carriers A, B and D, Q3's clause
  as a hold plus a pointer, and the finding shipped whole. 7, block
  four's [3]: the next master's bundle authored only after the fix
  landed. Block two went unanswered; its [3], to leave the delivered doc
  lane unrevised, went moot when the doc lane applied.
- What the desk found, shortened: `tests/test_doc_crossrefs.py`'s
  `RelayParagraphPins` asserts TARBALL.md §7's lead does not contain
  "staging directory", so any delta to that lead has to know it; "as a
  file" is a substring of "has a file", so a phrase probe needs a word
  boundary, and the doc lane's oracle has one; TARBALL.md §5.3 says
  "Claude doesn't run validators", which the desk's Delta 7 text ignored
  and the worker caught, making the sentence conditional; a required
  backticked spelling refused a reasonable draft (§6 entry 203); at
  0.4.40 nothing checks an unannounced write made during `validation.sh`
  (row 120); `tests/test_sanctioned_pairs.py` had pinned CLAUDE.md
  §11.2's bundling sentence in its conditional form (§6 entry 202); and
  PLANNER.md §20 sits between §6 and §7 in the file, which a rehearsal
  script of the desk's assumed otherwise (§7).
- Desk verification before delivery, in the desk's words, shortened. The
  doc lane's oracle: fourteen label-only probes, an extractor self-test
  as control, exit 2 on its failure. Base: exit 1, ten failing, four
  passing. A landing built from the brief's twelve fenced blocks: exit
  0, and the three doc suites pass on it. Eighteen negatives, each
  failing exactly one probe, every probe with one of its own; a
  renumbered heading or step fails one probe and SKIPs its dependent. A
  broken control and a no-docs tree: exit 2. Dress-rehearsed twice
  through the real `bale open` in fresh scratch repos, isolated `HOME`,
  stdin piped, confined, network granted: the expected-HOLD proof, the
  pack replayed, exit 0, 138 files, echoes matched. The fix's oracle:
  twelve probes, the same helpers and control. Base: exit 1, nine
  failing, three passing. A landing from the brief's eight fenced
  blocks: exit 0. Thirteen negatives, each failing exactly one probe,
  and one accepted variant, the sequencing sentence in §6 instead of §3.
  On that landing `test_doc_crossrefs` and
  `test_global_doc_selfcontainment` pass and `test_sanctioned_pairs`
  fails on exactly pins 6 and 8, the two the brief told the worker to
  rewrite. Rehearsal caught three defects, all in the desk's rehearsal
  script and none in the oracle or the brief (§6 entry 199).
  Dress-rehearsed once: the same result, echoes matched. Its base for
  `docs/CLAUDE.md` and `docs/TARBALL.md` predated the doc lane's
  landing, and the brief said so (§6 entry 204). Not done for either: an
  apply-side run before delivery, the full suite, the sweep's accept
  path. Both then passed on a first apply.
- The exec bit. The fix's worker shipped a `chmod +x` line for
  `tests/test_sanctioned_pairs.py` because the file arrived mode 755 in
  its request, and asked that it be dropped if the mode was a packing
  artifact (its decision 7). The desk found the file mode 755 in its own
  request tarball, packed before the fix, as are 3 of the 72
  `tests/test_*.py` files, so the bit looks real in the repo and the
  line benign. The operator's tree is the fact; the 008 desk put the
  line to him, and it stands (next bullet but one).
- Where the desk's brief and the records part, found at this close:
  nowhere. The desk saw neither wave-10 record and said so; its account
  came from bale's relay blocks, and every fact it gives holds against
  the records by key: both `packed_at` seconds, both checkpoint shas,
  one apply attempt each, no admissions, the forecast paths as
  `change_paths`. The records add what the relays did not carry: both
  applies ran confined with the network grant exercised, all sixteen
  claims carry `claim_basis: observed`, and both workers report
  `budget_pressure: none`. Two fills: the sweep in the opener, and the
  fix's request, which by its record's provenance echo carried the doc
  lane's landed CLAUDE.md and TARBALL.md, so the staleness the desk
  named was its own tarball's and not the worker's (§6 entry 204).
- Ratified at the `2026-09-21-continue-plan-008` desk: this desk's
  calls, the fix's notes.md, and the debt two earlier desks carried, in
  one light block answered first time. That desk (read-only, `packed_at`
  13:23:33Z, and its record's `created_at` reads 13:23:35Z, two seconds
  later; bale 0.4.40; whole-tree pack; its sitting still open, its close
  being close 18) read the contract in order, PLANNER.md's core,
  TARBALL.md §3.4, §5.10 and §7 to §7.2; verified its manifest's six
  hashes and the base, and the 005 desk's base facts at the same line
  numbers; read the seven records of the day by key and both wave-10
  notes.md; found the findings file absent; built nothing ahead of the
  reply, by TARBALL.md §5.10's "The worker does not idle"; and closed
  its first turn on light block one, rendered by the crafter, verbatim,
  rows joined as above: "[1] question: board-103-wave1-findings.md did
  not arrive beside the opener again; will you attach it with your
  reply? / while doing: close 17's row 103 bracket; uploads held only
  the request tarball, and my brief carries the findings' sections 7 and
  8 but none of wave one's record / would assume: yes; you attach it, I
  handle it as its header says, and none of the kit's task, bait or
  canned answer reaches the brief, the oracle or claude/MASTER.md / why
  blocked: the wave's record exists only in that file and your ledger,
  and a probe cannot carry a 15 KB file / [2] question: Ratify the fix
  session's notes.md: its seven decisions as listed, the chmod line
  kept, CLAUDE.md section 11.2's "stays in conversational mode" sentence
  left alone, and both Proposals to the registry as riders (the section
  7.5 sentence for the next docs/TARBALL.md holder, the two phrase pins
  for the next tests/test_doc_crossrefs.py holder)? / while doing:
  clearing the ratification debt the 005 desk handed me, so close 17
  records it as ruled; I read the notes whole and the landed text of all
  three docs, and I agree with the 005 desk's read of each decision /
  would assume: yes / why blocked: the notes put those calls to you, the
  mode bit is a fact of your tree, and Proposals are yours to dispose /
  [3] question: Ratify the carried desk debt in one word: the 009 desk's
  eight calls as close 16's 009 block lists them, the 002 desk's
  eleven-and-seven split for entry 191's bracket, and the 005 desk's
  calls as I list them above? / while doing: writing the debt bullets of
  close 17's two sitting blocks; the 009 desk's eight have now traveled
  unruled through two desks / would assume: yes; close 17 records all
  three sets as ratified at this desk, and the only debt it carries
  forward is my own calls and its worker's notes.md / why blocked:
  silence is not "as assumed", and each desk left these for you rather
  than for its successor". "The 005 desk's calls as I list them above",
  as that desk listed them in the same reply: hand-authoring block one
  before reading §5.10; not superseding the delivered doc lane after
  reading the findings' §3.2; treating block two's silence as no answer
  and asking again; authoring the fix's oracle against a base it knew
  was stale for two files, keyed to headings and phrases; recording
  close 16's Proposal 2 as landed instead of closing a registry entry it
  never had; reading the mode bit as benign; carrying the 002 brief
  whole as Part 2; reading only the findings' header, §3 and §9 to §11.
  The operator's next message, whole and verbatim: "as assumed.", with
  `board-103-wave1-findings.md` attached, its sha256 matching the
  brief's (§6 entry 195). So ratified: [1], the findings attached and
  handled as the file's header says; [2], the fix's notes.md, all seven
  decisions, the `chmod +x` line kept, CLAUDE.md §11.2's "It stays in
  conversational mode and returns, in chat:" left alone, and both
  Proposals to the registry as riders (§3 registry); [3], the 009 desk's
  eight calls as close 16's 009 block lists them, the 002 desk's
  eleven-and-seven split for §6 entry 191's bracket, and the 005 desk's
  eight calls as listed above. Its second turn read the findings'
  header, §1, §2, §6 and §9 to §11 and authored this close's bundle.
- Ratification debt this sitting carried forward. None from the doc
  lane, ruled at the desk (ruling 5), and none from the desk's calls
  through block four (ruling 6); the fix's notes.md, which reached the
  desk with the operator's last reply, and the desk's calls in its brief
  were ruled at the 008 desk, as was the 009 desk's eight (previous
  bullet). Unruled, and the 008 sitting's to close: that desk's calls in
  this close's brief, as it lists them: the split-transition ruling
  recorded as a §5 contract and not a row; the fix as a non-board
  landing in this block; the findings' §8 items 5 to 7 as one row; the
  seven rows' order; the eight registry labels; each operator message
  unwrapped with a line break read as one space; what of the findings
  may be said in `claude/MASTER.md`; and `--include` of
  `claude/telemetry` whole. They go to the operator at that desk's
  delivery.
  Ratification debt carried forward, per convention: THIS close's notes.md queues to the following open.
- Sequencing for the next desk: the standing line, unchanged from the
  002 desk's ratified words:
  "wave 10, then the 100 arc with its design sitting first, then 43, 45, S6; row 103 ongoing; row 93 stands".
  Wave 10 grew a fifth bundle, the split-transition fix, and is cut
  across three masters by the operator's "as assumed" to the desk's
  light block three, [3]: the 005 desk authored the doc lane and the
  fix; the `2026-09-21-continue-plan-008` desk, the second of the three,
  authored this close; its successor authors the tools micro and the
  rider micro, one bumper per wave, every file list a guess until the
  code is read (§6 entry 188). The 008 sitting is still open, and its
  close is close 18. Rows 114 to 120 are not on the line; their order is
  the operator's and is not ruled.
- Board deltas of this sitting's work: row 103's bracket, whose record
  that the doc lane landed the findings' Proposals 1 to 6 and 10 is this
  sitting's; row 120, from the doc lane's second Proposal (ruling 5); in
  §5, the new 2026-09-21 block, the split as a role transition in every
  project, and the bracket carrying the 2026-09-20 exit-2 contract to
  PLANNER.md §4; in §6, evidence entries 195 to 199 and 201 and the
  brackets on entries 173, 179 and 194, all shared with the previous
  block, and entries 202 to 204; in §7, the 0.4.40 landmark and what the
  two workers and the three desks verified.
- Registry deltas of this sitting's work: the `docs/CLAUDE.md` §11.4
  pointer closed at the doc lane, with the clause; the exit-2 rider
  landed at the fix; the doc lane's first and third Proposals, the
  crafter seeding `forecast_departures` for the tools micro and the §5.9
  courier statement; the fix's two Proposals, the §7.5 sentence and the
  phrase pins, by the 008 desk's [2]; pointer brackets on the three
  rider-micro entries (a cause on a `rejected` attempt, the `swept_by`
  dossier line, and 110's held admissions in
  `format_hold_relay_planner`); the dispositions entry at the list's end
  covers both sittings.

Landed 2026-09-22, the continue-plan-001 sitting (master
`2026-09-22-continue-plan-001`, read-only, work class meta; bale 0.4.40;
whole-tree pack; packed 11:57:53Z by its record's `packed_at`, and its
`created_at` reads 11:57:54Z, one second later; `closed-read-only` at
23:44:23Z by the `2026-09-22-board-100-design-004` pack, which its
`swept_by` names and whose `packed_at` is the same second). Four turns,
four light blocks, all answered "as assumed", none with a question back;
no probe in its account. It authored wave 10's two micros and the 100
arc's design sitting's bundle, ratified both micros' notes.md, and
handed close 18 on. Its brief to the 005 desk (sha256 `aa8d4555…ba9f9`,
the 005 manifest's `readme` sha), carried byte for byte as Part 2 of
this close's brief, is this block's source, beside the two wave-10
records read by key at the 005 desk and again at this close. This block
carries only what has no row home; close recorded by
`2026-09-23-sitting-close-deltas-18-005`:
- Wave 10 as dispatched, from Part 2: two bundles authored at turn two,
  each a brief, a blind checkpoint and a stored argv in a crafter
  bundle. The tools micro, bumpless, five named files, carrying the §7.5
  and §5.4 riders and the lint README rider and leaving the §5.9 courier
  rider to a §5.9 holder; the rider micro, one bumping session at
  0.4.41, merging five riders, with a new `relay-refused` outcome. Both
  cuts by block one's [2] and [3]. The desk read the code every micro
  source named before either brief, the first desk to (§6 entry 206).
  Each oracle was rehearsed against the base (expected HOLD), on a
  throwaway shim landing (all pass), and with negatives for the
  disjointness probes; rehearsal caught two oracle defects before
  delivery, and both micros were dress-rehearsed together through the
  real `bale open` (§6 entry 207).
- Landing record, in apply order from telemetry.
  `2026-09-22-tools-micro-002`: opened 12:35:33Z, `packed_at` the same
  second; `held` at 14:28:01Z, blind checkpoint HOLD, exit 1, stamp
  matched, one failed probe by label,
  `lint-request-flag-silent-inside-forecast`, sha256 `f210af21…`; worker
  validation exit 0 with its fifteen claims each observed and `agree`,
  the attempt's state HOLD with the checkpoint's. Ruled work-defect at
  the 001 desk (§6 entry 205). `applied` at 14:35:07Z on
  `command: retry`, checkpoint PASS, exit 0, the same sha; worker
  validation PASS, fifteen claims, each observed and all `agree`, one
  key grown between attempts to end "; silent when all inside"; five
  `change_paths`; both attempts confined, network grant exercised; no
  admissions; `budget_pressure: none`; `model_identity` "Claude Opus 5
  (claude-opus-5)". Bumpless, its request stamped 0.4.40.
  `2026-09-22-rider-micro-003`: opened 12:36:36Z, `packed_at` 12:36:35Z;
  `applied` at 14:42:50Z, one attempt, confined, grant exercised;
  checkpoint PASS, exit 0, stamp matched, no failed probes, sha256
  `bcd2a6c3…`; worker validation PASS, thirteen claims, each observed
  and all `agree` (nine test-module claims and four session assertions);
  19 `change_paths`; no admissions; `budget_pressure: tight`;
  `model_identity` "Claude Opus 5"; 0.4.41, its `apply.sh` one line,
  `chmod +x bin/bale`. Neither `opened` attempt carries a `bundle` key:
  the tools pack predates 0.4.41, and the rider micro's own `opened`
  attempt was written before the version it introduced.
- What landed, from Part 2's "Wave 10, landed", in short. The tools
  micro: emit mode exits 0 when it wrote; `--request` on the lint, with
  the `FORECAST_DEPARTURE_UNDECLARED` and `README_NOT_IN_DOCS_READ`
  warnings; the crafter seeding `forecast_departures` for every
  `changes[]` path outside `resolved_scope`, deletions included (a
  flagged deviation from the brief's "files/ path", ratified);
  TARBALL.md §5.4 reworded and the micro's own VERBATIM sentence in
  §7.5; the craft path guard dropped; the epilogue's stderr log naming
  `--fragment`; §5.9 hash-pinned byte-identical to the base. The rider
  micro: `cause` on `rejected` attempts; `bundle` on `opened` attempts;
  `relay-refused` written with `cause` for every refusal of the input
  itself; the re-escape check naming the carrier's unescaping; the
  dossier's `swept by <sid>` line, with no colon; held admissions in the
  planner HOLD block; a real envelope-subset guard in
  `test_rollback_telemetry`. Each consumed a registry entry, bracketed
  there.
- The design sitting's bundle, authored at turn three: stem
  `2026-09-22-board-100-design`, brief sha256 `3320ae09…2adf`,
  checkpoint null, by the 004 record's `bundle` key, the first `bundle`
  key on a design sitting's opened attempt, written by 0.4.41.
- Turns and blocks, from Part 2's summary; its blocks are not
  transported verbatim, so none is quoted here. Block one (turn one):
  [1] the caveat reading confirmed; [2] the tools micro cut; [3] the
  rider micro cut. Block two (turn two): [1] open both as delivered; [2]
  author the 100 arc's design sitting at the desk next turn; [3] paste
  the micros' relays there. Block three (turn three): [1] ratify both
  notes.md as listed, six Proposals disposed; [2] open the design
  sitting, authoring its own wave; [3] end the sitting on a successor
  brief. Turn four was that brief. Part 2 counts four blocks and four
  answers, nothing assumed from silence, and names the rows of three.
- Rulings at the desk, all the operator's "as assumed": both micros cut
  and opened as delivered; both notes.md ratified with their six
  Proposals disposed (the registry's 2026-09-22 dispositions, which land
  at this close); the design sitting authoring its own wave; the cadence
  of 2026-09-22 (§5), carried in its brief. The desk's own Proposal, the
  dossier colon, went to the registry.
- Debt the brief handed on, from Part 2's "Debt this brief hands on":
  close 18 itself; close 17's Proposal 1 (a registry entry now); DOCS.md
  and CODE.md unread by the 001 and 008 desks; the findings' packets
  tarball unshipped anywhere; row 117 still waiting on the operator's
  ruling. The wave-10 board rows: the findings' items and the riders
  have no rows of their own, close 17 having landed them as registry
  entries, so close 18 brackets entries and adds no rows for wave 10.
- Sequencing for the next desk: see the continue-plan-005 block below;
  this sitting's own line was the 100 arc next, which ran.
- Board deltas of this sitting's work: none of its own; the design
  sitting it authored is row 100's. In §5, the 2026-09-22 cadence block;
  in §6, entries 205 to 207, and the cadence entry 209 records.
- Registry deltas of this sitting's work: ten brackets on the nine
  entries the wave retired (the findings' §8 entry takes two, one per
  micro); the tools micro's Proposals 2 and 3, the rider micro's 1 to 3
  and the desk's dossier colon as new entries; the cadence rider; the
  dispositions entry at the list's end covers all four sittings.

Landed 2026-09-22, the paired-desk sitting
(`2026-09-22-board-100-design-004`, read-only, work class meta; opened
2026-09-22T23:44:23Z from the 001 desk's bundle, `packed_at` the same
second, its pack sweeping the 001 master that second; closed
`superseded-by-split` at 2026-09-23T00:23:18Z, `superseded_by`
`2026-09-23-board-100-design-001`; two attempts, one `opened` and the
closure, and no `swept_by`). The operator opened it twice under the one
sid, as a trial of paired planner desks; the record carries one `opened`
attempt, so the second desk is in no record (row 123). Its record is the
file the two desks merged and signed,
`board-100-paired-desks-close-18-merged.md`, sha256
`30ddaf6c2b4d0a0bd7678df18b8af282f46df7b3fedab03d161f9fb58cfcb791`, read
whole at the 005 desk and not shipped to this close; it is cited by name
and hash as the operator's carried artifact. This block carries only
what has no row home; close recorded by
`2026-09-23-sitting-close-deltas-18-005`:
- Digest, from close 18's brief: two independent first turns, three
  relayed rounds, one refused paste (`bale pack`'s include gate on
  `--include claude/checkpoints`), and a revc bundle re-derived
  independently by both desks to byte-identical archives, opened as the
  successor. Two light blocks were emitted under the one sid and neither
  was answered, the operator carrying rather than ruling; the successor
  re-asked decisions 1 to 3. By its record the closure is stamped
  00:23:18Z and the successor it names was created at 00:26:04Z, two
  minutes and 46 seconds later (item 1; row 121).
- The nine items both desks signed, verbatim from the merged file's
  head, one per line (origins kept: [a] first desk, [b] second, [ab]
  both):
  1. Argv-only gates run before state-changing exchanges in `cmd_pack`. Tool defect: the refused revb pack had already closed the parent superseded-by-split (`_resolve_supersession`, bale_pack.py:5223) before the include gate fired, so the parent's telemetry carries a closure stamped by a pack that produced no child on its first paste. The idempotent branch recovered it; recovered is not never happened. [ab]
  2. A pack rehearsal path — `bale pack --dry-run` or `bale open --check` — running pre-flight and writing nothing, extending `pack_argv_preflight` to the include gate. Until it lands, PLANNER.md §4 doctrine: a desk with `bin/` in context rehearses the line in a fixture before delivery. [ab]
  3. TARBALL.md §3.4 carries the planner-side include rule in one sentence (an `--include` may not name the checkpoint pattern's subtree; broader ancestors are fine and auto-exclude), and the crafter refuses a `--pack-arg` under `[validation] base`'s prefix, extending its existing `bale.toml` read (the `[probe]` clipboard key, tools lines 372–380). [a]
  4. A desk suffix on a second open of one sid, recorded. Suffix only; refuse would have blocked the experiment that produced the finding. [b]
  5. Ledger tagging in PLANNER.md §3 (verifying desk/sid + file:line, re-tagged on re-verification), plus the GUESS-label sentence in §2 beside "a wrong fact is worse than a missing fact": a named unknown is not coverage for the unnamed check. [b; the §2 sentence a, promoted by b]
  6. A trail for planner-desk light blocks: a `light_blocks` count on the read-only closure attempt, prompted at sweep/unlock; the sitting-record self-report until it lands. Close 17's Proposal 2 with a live specimen: two blocks, one sid, no record. [a mechanized, b as practice]
  7. Paired desks as a trigger-fired sitting kind, two shapes: read-set division for fact ledgers (merge re-reads the other desk's tagged lines); author/adversary for lines and briefs, the adversary's brief being "read the boring gates". Triggers: a brief costed from unverified claims; a bundle the operator will paste blind; an oracle that needs a real second party. [ab]
  8. Transcripts as a `--context` tarball beside a superseding request; cross-model pairing as the follow-on once layers 1–4 land. [a]
  9. (Carry decisions, not proposals.) The include gate's line numbers (bale_pack.py:417–471; a specimen oracle reaches a planner session by probe, never by include) and the parent-telemetry fact in item 1 go into the successor's ledger on its first re-verification. The determinism claim in both reports reads "observed twice under 0.4.41's crafter, for identical inputs", not "proven" — applied by each desk on its own report. [ab]
- Disposition, ruled at the 005 desk's light block one, [3], "as
  assumed": disposed at this close as registry riders and rows, none
  dispatched from that desk. Item 1: row 121. Item 2: row 122's first
  half, its interim PLANNER.md §4 doctrine named on the row. Item 3: two
  registry riders, the §3.4 sentence for the next `docs/TARBALL.md`
  holder and the crafter refusal for the next `tools/` holder. Item 4:
  row 123. Items 5 and 8: one registry entry for the next
  `docs/PLANNER.md` holder, with the upward report's Proposal 4. Item 6:
  a registry entry, its mechanized count unscheduled until a consumer,
  its practice half landed at W1 (ruling 6). Item 7: §6 entry 208 only,
  no sitting kind (the upward report's Proposal 1). Item 9: a carry, not
  a proposal; its home was the successor's ledger, which this close did
  not read. The placements are the 005 desk's, for the operator's
  ratification at delivery (the continue-plan-005 block).
- Light-block trail: two blocks, zero answered, no record. Close 17's
  Proposal 2 with a live specimen (§6 entry 208; the registry's close-17
  entry).
- Sequencing for the next desk: none of its own; its successor carried
  its work.
- Board deltas of this sitting's work: rows 121, 122 (first half) and
  123; §6 entry 208; row 100's bracket names it as the first of the
  design sitting's two opens.
- Registry deltas of this sitting's work: item 3's two riders, items 5
  and 8 in the `docs/PLANNER.md` entry, item 6's entry, item 7 as an
  evidence pointer, and close 17's Proposal 2 bracketed with its
  specimen.

Landed 2026-09-23, the 100 arc's design sitting and its wave
(`2026-09-23-board-100-design-001`, read-only, work class meta; the 004
sitting's successor, by that record's `superseded_by`; bundle stem
`2026-09-23-board-100-design-revc`, brief sha256
`e313b60109e2854534d80011ef553bec48b07e48c3697e59fcc7ad1a310f0ac7`,
equal to `design-brief-board-100-revB.md`'s, checkpoint null, by its
record's `bundle` key; `packed_at` 00:26:03Z, and its `created_at` reads
00:26:04Z, one second later; its pack swept the 005 master
`closed-read-only` at 00:26:02Z, as that closure's `swept_by` says). Its
record still reads `opened`, and the file is untracked on the tree (§3
Watches; §6 entry 212). It made rulings 1 to 9 in four light blocks,
each "as assumed", ran two paste-back probes, both complete (integrity
486 and 196), authored the wave's three bundles, revised W3's brief to
revB after W1 and W2 applied (derived, with a "Landed since revA"
section, checkpoint v1 unchanged), ratified all three notes.md as the
arc's sub-master, and wrote the arc's upward report. The cadence's first
application (§5, 2026-09-22): no master sat between it and its workers
(§6 entry 209). The wave's landings are on row 100's bracket; this block
carries only what has no row home; close recorded by
`2026-09-23-sitting-close-deltas-18-005`:
- The rulings: §5's 2026-09-23 block carries all nine verbatim from the
  decomposition, one bullet each, with their landings.
- Its light-block ledger, in its own words: "Four blocks emitted, four
  answered "as assumed", zero formal, zero unanswered." Two probes, both
  complete.
- Its archive, carried to the operator by ruling 9, three files:
  `design-brief-board-100-revB.md` `e313b601…0ac7` (346 lines),
  `implementation-decomposition-revA.md` `b2573fd4…4054` and
  `upward-report-board-100-design.md` `0b1f8081…d97c`. Their home is
  `claude/context/board-100-arc/`, committed directly by the operator;
  the directory did not exist at the close-18 probe, and this close does
  not create it.
- Ratified at the design sitting, the sub-master's review, from the
  upward report as the 005 desk digested it. W1's engraving of the noun
  rule in TARBALL.md §1, its INDEX row for §11.7, its hat-noun choices
  and the re-pinned STRUCK_PHRASES spelling. W2's `[layout]` at the
  project layer only, `oneOf` and `pattern` in both subset validators,
  the corrected remarks, the `layout_agent_dir` short-circuit, the two
  kept inject senses and the `.baleignore` wizard line. W3's
  `upgrade.sh` unchanged, argparse order kept with the default flipped,
  the inline `contract_docs` fixtures moved to `AGENT.md`, and
  `model_identity` taken from the session's own system prompt rather
  than `unknown`.
- Ledger corrections the report feeds upward, tag [w3]: the doc-name
  sites for the rename were `build.sh`, `install.sh` and `validate.sh`
  only, the brief's "pre-flight member check" in `upgrade.sh` a wrong
  fact inherited from the parent ledger (§6 entry 211; row 126); W2's
  close tally was 1506/48; nine cites drifted 1 to 15 lines and all
  resolved by phrase match.
- W3's hold. The checkpoint exited 1 with no failed-probe label while
  every labeled probe passed and the worker's five claims each came back
  observed and `agree`. The design sitting ruled it a fixture defect
  (PLANNER.md §5 step 6), corrected probe 3 as v2 with every non-probe
  failure route exiting 2, amended it on the tree (commit `9fea009`),
  and asked for no new response: the held tarball applied at 03:07:57Z
  on `bale retry`, `stamp_matched: false` accepted per invocation, the
  prose mention owed by the next doc landing (the registry's report (d)
  entry; §6 entry 210).
- Where the brief and the records part, found at this close: W3's
  `applied` attempt, left by the 005 desk to the record, reads 03:07:57Z
  on `command: retry`, the same tarball name, no admissions; nowhere
  else for this sitting.
- Sequencing for the next desk: none beyond the wave, which landed
  whole; the report's follow-on rows are placed on the board and the
  registry, off the standing line.
- Board deltas of this sitting's work: row 100 DONE with the arc on its
  bracket; rows 77, 116 and 118 DONE; rows 122 (second half) and 124 to
  128 from the report; in §5, the 2026-09-23 block; in §6, entries 209
  to 212 and the brackets on entries 119 and 188; in §7, the 0.4.43
  landmark and the renamed doc.
- Registry deltas of this sitting's work: report (d) for the next
  `docs/AGENT.md` or `docs/TARBALL.md` holder; Proposal 4 in the
  `docs/PLANNER.md` entry; Proposal 1 as an evidence pointer. None of
  the riders queued at 2026-09-22 was consumed by W1 to W3, which were
  authored before they were on the registry.

Landed 2026-09-22, the continue-plan-005 sitting (master
`2026-09-22-continue-plan-005`, read-only, work class meta; bale 0.4.41;
whole-tree pack; bundle stem `2026-09-22-continue-plan-close-18`, brief
sha256 `aa8d4555…ba9f9`, checkpoint null, by its record's `bundle` key;
packed 23:44:40Z by its record's `packed_at`, and its `created_at` reads
23:44:41Z, one second later, seventeen seconds after the design
sitting's open; `closed-read-only` at 2026-09-23T00:26:02Z by the
`2026-09-23-board-100-design-001` pack, which its `swept_by` names). Its
desk was first written to after the design sitting's successor had swept
it and while the 100 wave ran. Three turns, one light block, one probe.
It authored this close; its brief is this close's brief and this block's
source. This block carries only what has no row home; close recorded by
`2026-09-23-sitting-close-deltas-18-005`:
- The operator's opening note, whole and verbatim:
  "I'm currently running 3 packs from the board 100 design (which accidentally closed out this read only session), and I also ran a claude-to-claude experiment that resulted in the file attached. Please orient yourself and organize how this session should go (return the 3 packs notes.md? return an upward report from the board 100 master? focus on the claude-to-claude experiment and sitting deltas?)"
- Turn one read the manifest, CLAUDE.md in full, Part 2, PLANNER.md's
  core (§1 to §3, §6, §20, §7), TARBALL.md §5.10 and §10.2 to §10.4 and
  the crafter's light-block path; verified the six base facts (the five
  `docs/` and both `tools/` byte-identical to the carried copies;
  `claude/MASTER.md` at 10816 lines, `a8bbbeee…70a9`); read both wave-10
  records by key; read the merged file whole; and ended on light block
  one, rendered by the crafter, verbatim, rows joined by " / ":
  "[1] question: Confirm the cadence: closes are per wave, not per
  master; close 18 is this desk's last job, and it waits until the 100
  arc's wave (the three packs now running) has landed and its
  sub-master's upward report is here? / while doing: reading your
  2026-09-22 ruling as the brief and the manifest constraint state it;
  the 100 wave is the design sitting's project work, not this desk's, so
  this desk has nothing of its own to dispatch ahead of the close unless
  you name it / would assume: yes; close 18 covers wave 10, the
  paired-desk sitting 004, its successor design sitting, and the 100
  wave, and is authored here once the wave and its report are in / why
  blocked: the brief asks for this reading in the first block, and the
  brief's own first-job/second-job order reads the other way / [2]
  question: The three packs' notes.md go to the design sitting's desk
  (the arc's sub-master), which ratifies them and writes the arc's
  upward report per PLANNER.md section 20.2; you bring that report here
  with the three relays, and close 18 consumes them? / while doing:
  organizing the session as you asked; the cadence ruling puts no master
  between the design sitting and its workers, and one master per sitting
  means the desk that authored a wave ratifies it / would assume: yes;
  this desk reads the report and the records, never the packs' notes.md
  first-hand / why blocked: you offered to return the notes.md here
  instead, and what a close covers is yours / [3] question: Treat the
  merged paired-desk file as sitting 004's record: its nine signed items
  are disposed at close 18 (registry entries, a section 5 line, section
  6 evidence, rows where a row is earned), and none is dispatched as a
  session from this desk before the close? / while doing: sorting the
  file's carry-over; item 1 is a bale defect and items 4 and 6 are small
  code changes, so each could be a micro, but a dispatch here needs the
  100 wave's forecasts, which this tarball does not carry / would
  assume: yes; disposed at close 18 as registry riders and rows, no
  session from this desk / why blocked: board rows and Proposals are
  yours to dispose, and dispatching one would add project work to a desk
  you sized to a close"
- The operator's next message, whole and verbatim:
  "as assumed. I just received the board 100 reports if you're ready for them as well."
- Turn two ran one paste-back probe, `close-18-records`, built from the
  crafter's scaffold and rehearsed read-only against the request's own
  tree; it came back whole (integrity 1302, trailer present), with the
  three archive files attached. Turn three wrote this close's brief and
  its oracle, rehearsed and dress-rehearsed, and the bundle.
- Rulings at the desk, the operator's "as assumed" to block one: [1] the
  cadence, closes per wave, this desk's last job close 18, waiting on
  the 100 wave and its upward report (§5, 2026-09-22); [2] the three
  packs' notes.md to the design sitting's desk, which ratifies them and
  reports upward, this desk reading the report and the records, never
  the notes first-hand; [3] the merged file as sitting 004's record, its
  nine items disposed at close 18, none dispatched from the desk.
- Light-block ledger (ruling 6's practice), from the 005 desk. This
  desk: one block emitted, one answered "as assumed", zero formal, zero
  unanswered; one probe, complete. The 004 desks: two blocks, zero
  answered, no record. The 001 desk: four blocks, four "as assumed". The
  successor: four, four "as assumed", two probes, complete. This close's
  own count is in its notes.md.
- Desk calls to ratify, the ratification debt this close carries to the
  operator, as the 005 desk lists them: the placements under "Rows" and
  "Registry"; the successor's unswept sid recorded as a watch, not a
  defect; the merged file and the three archive files cited by name and
  hash rather than shipped; W3's `applied` attempt left to the record;
  the nine rulings recorded as a §5 block; the four sitting blocks in
  this order; row 100 closed DONE with the wave on its bracket rather
  than three rows. Nothing else is unruled: the 001 desk's calls and
  wave 10's notes.md were ruled at the 001 desk, the 100 wave's at the
  design sitting.
  Ratification debt carried forward, per convention: THIS close's notes.md queues to the following open.
- Where the brief and the records part, found at this close: the rider
  micro's record carries thirteen claims, each observed and `agree`,
  where the brief says nine, the count of its `tests.*` module claims
  alone; the 004 record carries one `opened` attempt for two desks; W3
  applied on `bale retry` (the design-001 block). The brief asks for the
  upward report's "Follow-on rows" list quoted verbatim on row 100's
  bracket; the list did not travel in this close's request, so the
  bracket cites the report by name and hash and places (a) to (f)
  without quoting them (this close's notes.md).
- Sequencing for the next desk: the standing line after the 100 arc,
  unchanged from the 002 desk's ratified words:
  "43, 45, S6; row 103 ongoing; row 93 stands".
  Rows 121 to 128 are not on the line; their order is the operator's and
  is not ruled. By the cadence, the next master's last job is its wave's
  close, after the wave's project work is dispatched.
- Board deltas of this close: row 100's bracket and DONE on rows 77, 116
  and 118; rows 121 to 128; in §5, the 2026-09-22 and 2026-09-23 blocks;
  in §6, entries 205 to 212 and the brackets on entries 119 and 188; in
  §7, the 0.4.43 landmark and what the 005 desk and this close verified;
  the watch above (§3 Watches).
- Registry deltas of this close: the retirement brackets on the entries
  wave 10 consumed, a stays bracket on the §5.9 courier entry, and the
  new entries in the brief's order, ending on the dispositions entry for
  all four sittings.

Landed 2026-09-23, the continue-plan-006 sitting (master
`2026-09-23-continue-plan-006`, read-only, work class meta; bale 0.4.43
at its pack; bundle stem `2026-09-23-continue-plan-wave-11`, brief
sha256 `1cb4a9b5…362e`, checkpoint null, by its record's `bundle` key;
packed 04:12:09Z by its record's `packed_at`, and its `created_at` reads
04:12:10Z, one second later; `closed-read-only` at 22:08:25Z by the
`2026-09-23-board-45-hostile-repo-design-010` pack, which its `swept_by`
names). Its desk outlived that sweep: it ruled the stemwell arc on
2026-09-24 and wrote close 19's brief there as its last job (§3
Watches). Four light blocks and one probe, all answered "as assumed". It
authored wave 11's three bale-src sessions and row 45's design sitting,
ratified the three notes.md, and handed close 19 on. Its brief to close
19, the request's README.md (sha256 `5d736a64…a8d8`), is this block's
source, beside the five bale-src records and the three notes.md read at
this close. This block carries only what has no row home; close recorded
by `2026-09-24-sitting-close-deltas-19-001`:
- Wave 11 as dispatched, by the records' `bundle` keys. The four-small
  code micro, rows 121, 123, 124 and 125 with three registry riders, one
  bumping session at 0.4.44, the dossier colon dropped (§5, 2026-09-24):
  stem `2026-09-23-board-121-125-code-micro`, brief `282d0693…8b72`,
  checkpoint `9b39a9d7…`, packed 12:03:38Z. Row 43's §5 compression
  pilot, work class contract-doc, bumpless: stem
  `2026-09-23-board-43-tarball-s5-compression`, brief `34974f01…9c49`,
  checkpoint `00988cd5…`, packed 12:04:01Z, 23 seconds after the micro,
  the two forecasts disjoint. Row 122's rehearsal verbs at 0.4.45, after
  the micro landed, since they build on its pass: stem
  `2026-09-23-board-122-rehearsal-verbs`, brief `08aeb3a5…3092`,
  checkpoint `6ec054a2…`, packed 20:11:06Z. Row 45's design sitting,
  read-only: stem `2026-09-23-board-45-hostile-repo-design`, brief
  `b5cb96a0…26f7`, packed 22:08:25Z (the design-010 block below).
- Landing record, in apply order from telemetry.
  `2026-09-23-board-43-tarball-s5-compression-008`: `held` at 12:29:36Z,
  blind checkpoint HOLD, exit 1, stamp matched, one failed probe by
  label, `expects-probe-collision-one-home`, sha256 `00988cd5…`; worker
  validation five claims, all `agree`, the attempt's state HOLD with the
  checkpoint's. Ruled fixture defect at the desk, amended v2 then v3 (§6
  entry 213). `applied` at 12:45:24Z on `command: retry` with the
  worker's corrected tarball, its `corrects` naming its own sid;
  checkpoint PASS, exit 0, sha256 `53a90922…`, `stamp_matched: false`
  accepted; six claims, each observed and all `agree`; two
  `change_paths`; both attempts confined, network grant exercised; no
  admissions; `budget_pressure: none`; `model_identity`
  `anthropic:claude-opus-5.5`. Bumpless on 0.4.43.
  `2026-09-23-board-121-125-code-micro-007`: `held` at 13:11:26Z, blind
  checkpoint HOLD, exit 2, stamp matched, no failed probes, sha256
  `9b39a9d7…`: the oracle errored, a defective oracle and no verdict on
  the work (TARBALL.md §7.5; §6 entry 214); worker validation 23 claims,
  all `agree`. `rejected` at 13:27:11Z on `command: retry`, its `cause`
  the provenance gate: the base tree's checkpoint, sha256 `630f1c93…` at
  `main`'s tip `2838b60`, no longer matched the pack-time stamp, with
  the re-pack and `--accept-checkpoint-change` remedies. `applied` at
  13:37:44Z on `command: retry`, the same tarball, checkpoint v2 PASS,
  exit 0, `stamp_matched: false`; 23 claims, all `agree`; 20
  `change_paths`; confined, grant exercised; no admissions;
  `budget_pressure: none`, two tool-use pauses resumed with context
  intact; `model_identity` `anthropic:claude-opus-5.5`. 0.4.44.
  `2026-09-23-board-122-rehearsal-verbs-009`: `applied` at 21:57:33Z,
  one attempt, first pass; checkpoint PASS, exit 0, stamp matched, no
  failed probes, sha256 `6ec054a2…`; worker validation seven claims,
  each observed and all `agree`; eight `change_paths`; confined, grant
  exercised; no admissions; `budget_pressure: none`, `light_blocks: 0`;
  `model_identity` `anthropic:claude-opus-5-5`. 0.4.45.
- What landed, in short (rows 43 and 121 to 125 carry the detail). The
  micro: an argv-only pre-exchange pass in `cmd_pack`; a desk suffix on
  a second open; the configured `agent_dir` rendered in messages and
  `bale stats --help`; row 125's claim not reproduced, the one cache
  writer a test child, fixed; the three riders; suite 1544 tests, 48
  skipped. Row 43: §5 from 988 to 735 lines and 7,267 to 5,534 words,
  three VERBATIM riders, the four doc-pin suites from 52 to 60 tests.
  Row 122: `bale pack --dry-run`, `bale open --check` and `--dry-run`
  over one gate core, a real open's gate step widened to match, BALE.md
  §5, §6.7, §7.1 and §8.9; `tests/test_rehearsal_verbs.py`, 20 tests.
- Ratified at the desk as made, every notes.md judgment call of the
  three sessions, by the operator's "great, applied" and "as assumed":
  the micro's wider pre-exchange pass, `desk-N` and `command: "open"`,
  the `stats --help` formatter, the reworded log line; row 43's
  VERBATIM-1 beside the checkpoint-configured paragraph, 5.7's template
  as a header list, the schema pointers in 5.2.2, 5.8 and 5.9.2, the
  session-dated tombstones; row 122's cut into helpers, the widened
  real-open gate step, the rehearsal log outside the repo, the predicted
  exchange with the piped no-intent refusal. Each session's Proposals
  are disposed in the registry's close-19 entry.
- Row 45's sitting, re-derived at one light block: the operator ruled
  that the desk designs the messy codebase and a seed session builds it,
  replacing this desk's first mechanism, a context tarball of a repo the
  operator would bring; the bundle already delivered was replaced before
  it opened (§5, 2026-09-24). The design sitting's own record is the
  design-010 block below.
- Turns and blocks, from the brief; its blocks do not travel verbatim,
  so none is quoted here. Four light blocks and one probe, all "as
  assumed". Block one: [1] closes per wave, close 19 this desk's last
  job; [2] close 18 ratified; [3] the micro's cut. Block two, after the
  arc: [1] the report committed and stemwell packed as context; [2] the
  report's Proposals filed as rows and entries, the workers' held; [3]
  gaps by probe. One block re-derived row 45's sitting. The brief
  details three of the four; the fourth's content did not travel, and no
  record holds a planner desk's blocks (the registry's `light_blocks`
  entry).
- On this desk's line, by its own brief: the two defects the arc's
  report puts on the design desk (§6 entry 218), and the HOLD clustering
  across the wave (§6 entry 217). The fixture lesson (entry 214) and the
  include rule (entry 215; §7) are its own findings.
- Where the brief and the records part, found at this close: the micro's
  `rejected` retry at 13:27:11Z, which the brief's "retry, applied"
  passes over; the brief's "three of this desk's oracles held", where
  the records carry two checkpoint HOLDs and the third, row 43's v2, was
  amended away before it ran (entry 217); this desk's own record, swept
  at 22:08:25Z on 2026-09-23, before the arc it later ruled; the
  design-010 record's `abandoned` closure, which the brief's table does
  not give. Everything else the brief states of the bale-src records
  held, including every sid, outcome, version and HOLD cause.
- Sequencing for the next desk: the standing line was "43, 45, S6; row
  103 ongoing; row 93 stands". Row 43 is DONE, and row 45's first wave
  is complete with its second gated on S6; the 006 desk ruled no new
  line, so this close writes none. Rows 121 to 125 and 122 are DONE;
  rows 126 to 128 and 129 to 133 are not on a line.
- Board deltas of this sitting's work: DONE on rows 43, 121, 122, 123,
  124 and 125; row 45's bracket; rows 129 to 133; in §5, the 2026-09-24
  block; in §6, entries 213 to 219; in §7, the 0.4.45 landmark and the
  wave's facts; the watch bracket (§3 Watches).
- Registry deltas of this sitting's work: retirement brackets on the
  §5.9 courier, declared-departure lint, handoff-stamp, dossier-colon
  and include-rule entries; the §5.2.2 entry kept for its `--fragment`
  clause; W3's half of the §11.7 entry recorded; the fence-aware entry
  beside the phrase pins; new entries at the list's end in the brief's
  order, ending on the dispositions entry.

Landed 2026-09-23, row 45's design sitting and its stemwell arc
(`2026-09-23-board-45-hostile-repo-design-010`, read-only, work class
meta; bundle stem `2026-09-23-board-45-hostile-repo-design`, brief
sha256 `b5cb96a0…26f7`, checkpoint null, by its record's `bundle` key;
packed 22:08:25Z, and its `created_at` reads 22:08:26Z, one second
later; its pack swept the 006 master; closed `abandoned` on `command:
unlock` at 2026-09-24T00:57:39Z, no `swept_by`). The desk designed a
small messy codebase, stemwell, and authored its seed and first wave in
stemwell's own repo: bale 0.4.45 installed there, `[validation] base =
"claude/checkpoints/{sid}.sh"`, `[sandbox] network = false`. The arc's
close, `2026-09-24-board-45-close-008` in stemwell (read-only, work
class doc, packed 13:16:32Z, `opened` in the snapshot), wrote the upward
report, committed in bale-src as
`claude/context/board-45-arc/2026-09-24-board-45-close-008-upward-report.md`.
Sources: the report, read whole; stemwell's seven notes.md and nine
telemetry records in the operator's `bale pack --context` snapshot,
`context-stemwell.tar.gz`, sha256 `330b928d…513f`, 39,012 bytes, its
copy fingerprinted by this close's probe; the brief's table. The arc's
records are committed in stemwell, not in bale-src, and are cited here
by sid. This block carries only what has no row home; close recorded by
`2026-09-24-sitting-close-deltas-19-001`:
- The design, by the operator's ruling (the 006 block; §5, 2026-09-24):
  the desk designs and a seed session builds. Stemwell is a small Python
  CLI, `ingest`, `report` and `tally`, with two stem-file parsers, a
  codec table generated from `data/codec.tsv`, three slow or flaky test
  modules and a locale-dependent sort, built to the design's pinned rows
  H, G, E1, F, S, E2, E3, D, A and T (the seed's notes.md).
- Landing record, in open order, from stemwell's telemetry.
  `2026-09-23-seed-stemwell-001`, seed v1: opened 23:17:15Z (stem
  `2026-09-23-seed-stemwell`, brief `2c9594a9…d956`, checkpoint
  `e9a73436…`); unlocked `abandoned` at 2026-09-24T00:58:20Z, 1 h 41 min
  later, no attempt between: the worker surface's safety classifier
  refused the brief's wording before any worker built (the report; §6
  entry 218). `2026-09-24-seed-stemwell-001`, seed v2: opened 00:58:30Z
  (stem `2026-09-23-seed-stemwell-v2`, brief `3505352f…17fd`, the same
  checkpoint), the same design reworded; `applied` at 01:44:22Z, first
  pass, 45 min 52 s; checkpoint PASS, stamp matched; 27 claims, 26
  `agree` and one `n/a` (`E3-dict-order`, its precondition absent in the
  sandbox); 23 `change_paths`.
  The first wave, batch one opened in 17 seconds:
  `2026-09-24-wave1-trailing-space-002`, opened 12:51:21Z, `applied`
  12:58:46Z, four claims `agree`, two `change_paths`, its response
  tarball 7,729 bytes by the operator's probe (the brief), 7 min 25 s;
  `2026-09-24-wave2a-add-prune-003`, opened 12:51:26Z, `held` 12:59:00Z
  with the checkpoint PASS and two of six claims `DISAGREE` (`unittest
  tests/test_prune.py`, `e2e report after prune`), then its worker's
  retry, `corrects` naming its own sid, `applied` 13:02:20Z, six `agree`
  (§6 entry 216); `2026-09-24-wave3-codec-regen-004`, opened 12:51:30Z,
  `applied` 13:02:36Z, five `agree`, one pre-build probe by its
  `linkage`; `2026-09-24-wave5-ingest-gzip-005`, opened 12:51:38Z,
  `applied` 13:02:51Z, two `agree`, four `change_paths` of five
  forecast. Batch two, serialized behind the gate:
  `2026-09-24-wave2b-add-export-006`, opened 13:07:06Z, `applied`
  13:13:32Z, two `agree`; `2026-09-24-wave4-report-json-007`, opened
  13:07:41Z (stem `2026-09-23-wave4-report-json-v2`), `applied`
  13:13:46Z, five `agree`.
  Across the arc: seven sessions applied on eight apply attempts, the
  checkpoint PASS with its stamp matched on all eight; 57 claim rows, 54
  `agree`, one `n/a`, two `DISAGREE`, the report's claims block
  reproduced from the records at this close; every attempt confined with
  no network grant; zero clarification rounds, zero worker light blocks,
  one probe; `budget_pressure: none` and no compaction in every
  self-report. Four admitted out-of-forecast paths: `prune.py` and
  `test_prune.py` at both 2a attempts, `export.py` and `test_export.py`
  at 2b. `model_identity` `anthropic:claude-opus-5-5` on every record
  but wave2a's two, `anthropic:claude-opus-5.5` (§7).
- Rehearsal, row 122's first field use, from the brief: six `bale open
  --dry-run` logs survive under `/tmp/bale-open-rehearsal-*` (seed v1,
  wave1, wave2a, wave3, wave4 v2 and wave5), each an expected HOLD;
  wave2b's `--check` refused at the disjointness gate against wave2a, no
  open spent and no telemetry row; the design desk's own `--write .` on
  the seed refused by the blindness gate at rehearsal, which is why the
  initial commit carries placeholder directories (§6 entry 218).
- The upward report, digested (row 45's bracket carries the findings by
  watch item). Ratified at apply by landing, the flagged worker
  deviations: wave1's edit of `test_report.py` removing two `.rstrip()`
  masks; wave2a's strict not-found rule and unrequested `--dry-run`;
  wave2b's reuse of `report.load_state_records` and direct write of
  dest; wave3's predicted-not-observed tally assertion; wave4's unsorted
  JSON path and `total`-collision error; wave5's gzip helper in
  `commands/ingest.py` and case-sensitive suffix detection. Escalated to
  S6 through its five Proposals, rows 129 to 133. On-watch: the workers'
  parked Proposals (the registry); three slow or flaky tests no wave
  validation ran; `BE`→`beta`, a lowercase label flagged independently
  by wave2b and wave3, a quirk the seed introduced unplanned; wave2b's
  `logging.basicConfig` note; wave2a's `model_identity` spelling. No
  autonomy exercised: every open, paste, apply and answer carried by the
  operator. The report's one placeholder, wave1's response bytes, is
  filled here from the brief: 7,729 bytes.
- Where the report and the records part, found at this close. The report
  says a probe leaves no telemetry row at all, wave3's existing only in
  `judgment_calls` and notes; wave3's applied attempt carries
  `feedback.mechanical.linkage` with `kind: probe`, `point: pre-build`,
  so the probe's existence is recorded and its timing is not (row 133).
  The report's "five parked worker proposals" lists six (the registry).
  It reads wave2a's `anthropic:claude-opus-5.5` as a slip; ruling 4
  applied to the picker's name "Claude Opus 5.5" gives exactly that
  spelling, and the other records carry the API string's, so the two
  spellings have two sources rather than one error (§7). Everything else
  the report and the brief's table state of the arc held against the
  records, every time and count included.
- Light-block ledger, from the report: the arc close emitted two blocks,
  three questions answered inline, one returned as a question and
  re-emitted, and one answered inline (wait for S6); none sent formal,
  none unanswered. The workers: none. The design desk's own blocks are
  in no record this close holds.
- Sequencing for the next desk: row 45's second wave waits for S6, by
  block two's [2].
- Board deltas of this sitting's work: row 45's bracket; rows 129 to
  133; in §6, entries 216, 218 and 219; in §7, stemwell's facts.
  Registry deltas: the five entries naming S6 and the held workers'
  Proposals.

Landed 2026-10-05, the friction-points desk and its first wave
(`2026-10-03-friction-points-001`, read-only, work class meta; bale
0.4.45 at its pack; whole-tree pack from the operator's typed goal, no
`bundle` key on its record; packed 2026-10-03T00:11:18Z by its record's
`packed_at`, and its `created_at` reads 00:11:19Z, one second later;
`closed-read-only` at 03:01:11Z by the
`2026-10-03-friction-points-wave2-004` pack, which its `swept_by`
names). Non-board: the arc began as an operator goal, not a row. The
desk split the goal into five sessions in three waves, made rulings [1]
to [3] in one light block answered "as assumed", authored wave 1 (A and
E) and ratified both notes.md, routed wave 1's Proposals, and wrote the
wave2-004 desk's brief, which carries its record (sections 1 to 5,
verbatim inside the cleanup desk's brief, inside close 20's). Sources:
that record, the two wave-1 records and both archived notes.md. This
block carries only what has no row home; close recorded by
`2026-10-05-sitting-close-deltas-20-001`:
- The operator's goal, whole and verbatim: "I want to tackle a few
  friction items. The bale config init wizard needs to be more helpful
  in general, and the easiest example of that is for the probe hook. I
  developed that to have a clipboard copy command run after a probe, but
  i shouldn't have to memorize the code to run and input it myself. It
  should present a clear default and maybe even offer some alternatives
  for common environments. Additionally, it shouldn't just apply to
  probes but to all paste blocks. Obviously the other wizard items may
  not have as clear of issues, but let's examine for any along the same
  lines. Also, all wizards in general are not displayed well visually at
  all. Something else I've noticed is that other projects, not bale-src,
  will have probes asking for bale --h documentation. Any documentation
  a project needs to use bale should be clearly outlined in the shipped
  docs somewhere, or possibly even slot into a global tool. Please
  tackle these issues, authoring disjointly when possible."
- The decomposition, verbatim from the desk's brief (five sessions,
  three waves, "authoring disjointly when possible"):

  | Wave | Session | What it does | Files it changes |
  |---|---|---|---|
  | 1 | **A** config-wizard-ui | A shared display layer for wizards; moves `config init` (both project and global, including its git-identity and `.baleignore` steps) onto it without changing behavior | `bin/bale_config.py`, plus the two tests that read its `[label]` lines |
  | 1 | **E** bale-cli-reference | The reference for other projects (per question 3) | `bin/bale_pack.py`, `docs/AGENT.md`, `docs/TARBALL.md`, tests |
  | 2 | **B** pack-wizard-ui | Moves the goal-less `bale pack` wizard onto A's display layer, plus the same helpfulness review | `bin/bale_pack.py` |
  | 2 | **C** wizard-defaults | Detected defaults and a short list of alternatives for every setting above, including the clipboard (per question 1) | `bin/bale_config.py` |
  | 3 | **D** clipboard-paste-blocks | Copying at all four paste points (per question 2), the probe copy step, and docs | `bale_pack`, `bale_relay`, `bale_report`, the probe-building tool, TARBALL.md §4.3, the status output in `bin/bale` |

- The findings behind rows C and B, the desk's words: "**2. Other config
  prompts that have the same "no default" problem:**
  `apply.search_paths`: the help text describes `~/Downloads` as the use
  case but doesn't offer it. On WSL the right path is
  `/mnt/c/Users/<you>/Downloads`, which is exactly the kind of thing you
  shouldn't have to remember. `identity.packer`: could default from
  git's `user.name`. `apply.archive_dir`: only mentions
  `claude/responses` in the help text. `staging.strategy`: a choice
  between two values, but you have to type one.
  `staging.untracked_inputs`: could detect an untracked `.venv` or
  `node_modules`. `validation.base`: the help suggests
  `scripts/validation.base.sh`, but your actual convention is
  `claude/checkpoints/{sid}.sh`, and neither is offered as a choice. The
  `.baleignore` step shows syntax examples but never suggests patterns
  based on what's actually in the repo. **Pack wizard:** it uses four
  different prompt styles, mixes log lines in with the questions, and
  prints lines up to 150 characters wide." On the paste points: "There
  are four places where you copy text from your terminal into a chat:
  the session opener `pack` prints, `bale relay`'s exchange block, the
  HOLD relay blocks `apply` prints (two of them: one for the worker, one
  for the planner), and probe output. Only probe output can be copied
  today." The scope reading: ""By "all wizards" I mean `config init`
  (both layers) and the goal-less pack wizard. I'm leaving out the
  apply/retry walkthrough and the yes/no confirmation prompts.""
- Rulings at the desk, the operator's "as assumed" to its one light
  block: [1] the clipboard key per-machine; [2] every operator-side
  paste block copied when a command is configured; [3] every request
  carrying the installed bale's generated help. The block is §5's
  2026-10-03 entry, verbatim; the standing ratification they build on is
  the registry's 2026-08-18 configurable-never-core entry, unchanged.
- Wave 1 as dispatched, by the records' `bundle` keys, both at 0.4.45,
  the two forecasts disjoint. A, `2026-10-03-config-wizard-ui-002`, work
  class code, forecast seven paths (`bin/bale_config.py`,
  `claude/context/bale-internals.md`, `install.sh`, `scripts/build.sh`,
  `validate.sh` and two tests): stem `2026-10-03-config-wizard-ui`,
  brief `66c98f37…7e45`, checkpoint `da309844…874d`, packed 00:47:31Z.
  E, `2026-10-03-bale-cli-reference-003`, work class mixed, forecast
  eight paths (`README.md`, `bin/bale`, `bin/bale_pack.py`,
  `docs/AGENT.md`, `docs/TARBALL.md` and three tests): stem
  `2026-10-03-bale-cli-reference`, brief `c0290cb7…b7cc`, checkpoint
  `919b5ff9…4cb2`, packed 00:48:27Z, 56 seconds after A.
- Landing record, in apply order from telemetry.
  `2026-10-03-bale-cli-reference-003`: `applied` at 01:51:38Z, one
  attempt, first pass; checkpoint PASS, exit 0, stamp matched, no failed
  probes, sha256 `919b5ff9…`; worker validation PASS, exit 0, five
  claims, three observed `pass`, one predicted `pass` (the neighboring
  suites), one `untested` (the `--slow` discover), and no
  `claim_verdict`: the record's `reconciliation_parsed` is false, so no
  claim of E's is paired with a verdict, the only such record in the
  arc; ten `change_paths`; three admissions at the prompt,
  `tests/test_cli_reference.py` (new), `tests/test_craft_response.py`
  and `tests/test_install_precheck.py` (modified out of forecast);
  confined, network grant exercised; `budget_pressure: none`, no
  compaction; `model_identity` `anthropic:claude-opus-5-5`.
  `2026-10-03-config-wizard-ui-002`: `applied` at 01:53:21Z, 1 min 43 s
  after E, one attempt, first pass; checkpoint PASS, exit 0, stamp
  matched, sha256 `da309844…`; worker validation PASS, eight claims,
  seven observed and `agree`, the `--slow` full suite predicted against
  a `skip` verdict, `n/a`; nine `change_paths`; two admissions at the
  prompt, `bin/bale_wizard.py` and `tests/test_wizard_ui.py`, both new;
  confined, grant exercised; `budget_pressure: none`; `model_identity`
  `anthropic:claude-opus-5-5`. Both bumpless on 0.4.45. Both records
  carry the pre-E `docs/AGENT.md` `dd22b82c…` and `docs/TARBALL.md`
  `59ece7fd…` in `contract_docs`; from B on the records carry E's
  `5124250b…` and `004d4389…`.
- What landed, in short (the notes.md carry the detail). A:
  `bin/bale_wizard.py`, a stdlib-only shared presentation layer, and
  `bale config init` drawn through it, both layers, with no semantic
  change, proven by a 6000-case differential against the v0.4.45 module,
  a frozen `SEMANTICS` table in `tests/test_wizard_ui.py` (49 tests) and
  a byte-for-byte piped run in its `validation.sh`; a review gate before
  any write; the suite 1621 tests at A's baseline. E: `BALE_HELP.md` at
  every request's top level, 17 command sections plus the top-level help
  in `bale help`'s order, rendered by `render_cli_reference()` at a
  fixed width of 78 inside `build_request_tarball`, about 77 KB,
  byte-identical from any terminal, with AGENT.md's META paragraph and
  an INDEX row and TARBALL.md §3.1 routing to it, and the
  self-containment guard scanning the file's unfenced framing;
  `tests/test_cli_reference.py` new. E counted the BALE.md citations the
  ruling queue asked for (that entry's bracket).
- Ratified at the desk, every flagged decision of both notes.md, as
  shipped, the desk's words verbatim from its brief (§4, flattened). A:
  "^C at the write gate leaves the file alone; no rewrite when the file
  is unchanged; a bare `?` is the help gesture, never a value; color
  only on a TTY, with `NO_COLOR` unset, and with `TERM` set and not
  `dumb`; `bale_wizard` imported at module top, as a stdlib-only leaf;
  the walk order is declared as data (`WIZARD_WALK_ORDER_*`), and a new
  key must enter it; summaries are new and descriptions untouched; the
  git-identity step is restyled in pack too." E: "Every decision E
  flagged is **ratified as shipped**: the name and placement; no
  provenance key; rendering inside `build_request_tarball`; the guard
  scanning only the unfenced framing; no opener or PLANNER.md change.
  The `stats` section varying with the repo's `[layout] agent_dir` is
  ratified too. The brief's determinism pin meant width-independence,
  and the reference reading as `bale help stats` reads in that repo is
  truthful."
- Routings at the desk (the wave2-004 desk's brief, §5): A's
  `upgrade.sh` proposal and seam guidance to B, "verify both against the
  bytes before citing them"; A's `ask_choice` and `bale-internals.md` §1
  proposals and the triple-quote rider to C, which reshapes the key; E's
  `config init` description proposal and the `bale status` row rider to
  D, "re-word it for the reshaped key"; A's and E's BALE.md sentences to
  99b; a sitting-close-deltas session owed at arc close. Each is
  disposed in the registry's entries of this date.
- Light-block ledger (PLANNER.md §6), from the brief: one block emitted,
  three questions, answered "as assumed"; zero formal, zero unanswered;
  no probe recorded. The workers: `clarification.rounds: 0` on both
  records, and neither record carries a `light_blocks` key.
- Where the brief and the records part, found at this close: the
  wave2-004 desk's table gives A's admissions as `bin/bale_wizard.py`
  alone, where the record carries two, `tests/test_wizard_ui.py` beside
  it; it gives E's as "not recorded at this desk", where the record
  carries three, named above; E's record pairs no claim with a verdict
  (`reconciliation_parsed: false`) while its notes.md describe a
  two-tree run of its `validation.sh`, so the PASS stands on the worker
  state alone. Everything else the brief states of the two records held:
  sids, outcomes, tags, checkpoint and worker states, version.
- Board deltas of this sitting's work: none; the arc is non-board, and
  row 99's bracket of this date carries 99b's grown inputs. Registry
  deltas: the 99b routing entry (A's and E's sets); the reversal bracket
  on the config-side carrier entry. In §5, the 2026-10-03 block; in §6,
  nothing of this desk's.

Landed 2026-10-05, the friction-points wave2-004 desk and its waves 2
and 3 (`2026-10-03-friction-points-wave2-004`, read-only, work class
meta; bale 0.4.45 at its pack; bundle stem
`2026-10-03-friction-points-wave2-desk`, brief sha256 `46e196f0…270f`,
checkpoint null, by its record's `bundle` key; packed 03:01:11Z, and its
`created_at` reads 03:01:12Z, one second later; its pack swept the 001
desk; `closed-read-only` at 2026-10-04T01:58:35Z by the
`2026-10-04-friction-points-cleanup-002` pack, which its `swept_by`
names). Two light blocks, both answered "as assumed", no probe. It
authored B, C and D from the 001 desk's decomposition, ratified the
three notes.md, recorded a brief correction against itself, routed every
Proposal of the arc, and wrote the cleanup desk's brief, the request's
README.md of `2026-10-04-friction-points-cleanup-002` (sha256
`951a114b…305c`), which is this block's source beside the three records
and the three archived notes.md. This block carries only what has no row
home; close recorded by `2026-10-05-sitting-close-deltas-20-001`:
- Waves 2 and 3 as dispatched, by the records' `bundle` keys, all at
  0.4.45, bumpless. B, `2026-10-03-pack-wizard-ui-005`, work class code,
  forecast ten paths (`bin/bale_pack.py`, `upgrade.sh` and eight pack
  suites): stem `2026-10-03-pack-wizard-ui`, brief `c6c80def…f9ff`,
  checkpoint `43f1eb2e…125e`, packed 03:23:17Z, 22 minutes after the
  desk opened. C, `2026-10-03-wizard-defaults-006`, code, forecast six
  paths (`bin/bale_config.py`, `bin/bale_wizard.py`,
  `claude/context/bale-internals.md` and three tests): stem
  `2026-10-03-wizard-defaults`, brief `2f4d1d1e…d463`, checkpoint
  `02eca53c…fa2d`, packed 23:36:23Z, 2 min 45 s after B applied; B and C
  ran serially though their forecasts were disjoint, C owning
  `bin/bale_wizard.py` and B using the layer's existing API only. D,
  `2026-10-04-clipboard-paste-blocks-001`, code, forecast eleven paths
  (`bin/bale`, `bin/bale_apply.py`, `bin/bale_config.py`,
  `bin/bale_open.py`, `bin/bale_pack.py`, `bin/bale_relay.py`,
  `bin/bale_report.py`, `docs/TARBALL.md`, `tools/craft_response.py` and
  two tests): stem `2026-10-04-clipboard-paste-blocks`, brief
  `d0804222…0ddf`, checkpoint `1af313a6…3a79`, packed
  2026-10-04T00:45:32Z, 23 min 29 s after C applied.
- Landing record, in apply order from telemetry, every session one
  attempt, first pass, checkpoint PASS with exit 0, stamp matched and no
  failed probes, worker validation PASS, confined with the network grant
  exercised, `budget_pressure: none`, no compaction,
  `clarification.rounds: 0`, `model_identity`
  `anthropic:claude-opus-5-5`. `2026-10-03-pack-wizard-ui-005`:
  `applied` at 23:33:38Z, 20 h 10 min after its open; checkpoint sha256
  `43f1eb2e…`; five claims, each observed and all `agree`; four
  `change_paths` of ten forecast; two admissions at the prompt,
  `tests/test_pack_wizard_ui.py` and
  `tests/test_upgrade_required_members.py`, both new.
  `2026-10-03-wizard-defaults-006`: `applied` at 2026-10-04T00:22:03Z,
  45 min 40 s after its open; sha256 `02eca53c…`; three claims, each
  observed and all `agree`; five `change_paths` of six forecast
  (`tests/test_layout_and_formats.py` needed nothing); no admissions;
  `includes_missing` filled, the arc's only record to fill it:
  `claude/changelog/0.4.45.json`, `claude/context/adr/0013-*.md`,
  `bale.toml`, the files behind the baseline failures (six; seven in A's
  count) every worker of the arc saw in its partial `context/` tree, and
  the same gap the cleanup desk later repeated (§6 entry 223).
  `2026-10-04-clipboard-paste-blocks-001`: `applied` at 01:51:27Z, 1 h 5
  min 54 s after its open; sha256 `1af313a6…`; nine claims, seven
  observed and `agree`, `unit tests: touched suites` predicted and
  `agree`, the `--slow` discover predicted against `skip`, `n/a`; twelve
  `change_paths` of eleven forecast; one admission,
  `tests/test_clipboard_paste_blocks.py` (new, 35 tests). Across the
  five workers of the arc: five sessions applied on five attempts, zero
  HOLDs, zero retries; 30 claim rows, 23 `agree`, 2 `n/a`, 5
  unreconciled (E); 40 `change_paths`; eight admitted paths, six new
  files and E's two modified tests; the arc 25 h 40 min 8 s from the 001
  desk's open to D's apply.
- What landed, in short (the notes.md carry the detail). B: the
  goal-less pack wizard drawn through `bale_wizard` as `PackWalk`, nine
  items headed by the flag that answers each, every line in 80 columns,
  post-walk `[bale]` log lines held by `WalkLogHold` until the README
  question, a slug derived from the goal on Enter, the resolved forecast
  and checkpoint path shown before Enter; `upgrade.sh`'s
  `REQUIRED_RELEASE_MEMBERS` trued up with `bin/VERSION` added; the
  eight forecast suites byte-identical and passing; 1694 tests. C:
  numbered `[n] value` alternatives on eight `config init` keys and in
  the `.baleignore` step, detected means detected and on PATH, Enter
  unchanged; `[probe] clipboard_command` both-layer through
  `effective_clipboard_command`, `x` suppressing; the triple-quote
  refusal in the reader; 1739 tests, 45 new. D: every operator-side
  paste block copied through `bale_report.copy_paste_block` when a
  command is configured, seven paste points in its table, a new verb
  `bale clipboard` (exit 0 copied, 1 not copied, 2 terminal stdin) that
  the probe scaffold pipes into, a `probe clipboard` row in `bale
  status`, TARBALL.md §4.3 and the help trued up; 1778 tests, 39 more,
  the new suite's 35 among them; the install-side `validate.sh` 94/94.
  Every count is the worker's own, on its partial `context/` tree.
- Rulings at the desk, the operator's "as assumed" to its two light
  blocks: block one, in the desk's words: "On a key with alternatives,
  Enter keeps today's meaning. The detected value is listed first,
  marked, and its number takes it. An Enter-through run writes nothing
  the operator didn't choose. (C built this.)" Block two, [1] the
  read-only sweep's y/N wrapped to 80 columns, width only, riding the
  log hold; [2] the `bin/bale` log hold as its own micro-session after
  D, D staying clipboard-only. Both blocks are §5's 2026-10-03/04 entry;
  block two verbatim there.
- Ratified at the desk as shipped, every notes.md judgment call of the
  three sessions, the desk's words verbatim from its brief (§2,
  flattened). B: "PackWalk instead of `Walk`. WalkLogHold, as an interim
  measure; the native hold is queued. The README question keeps
  `confirm_yn`'s exact answer set. No `?` help on walk prompts. The slug
  derived from the goal, and the other helpfulness changes. Checkpoint
  Enter still means none. The `upgrade.sh` criterion: `bin/VERSION` and
  the four load-time modules added; `bale_sandbox` left out, with the
  reason in the comment; the derived-closure suite pinning it." C: "The
  key kept as `[probe] clipboard_command`, layered like
  `identity.packer`. "Detected" means detected and on PATH. Digits are
  picks on keys that offer alternatives. The triple-quote refusal lives
  in the reader, not the loader. The restated crafter scan, pinned by
  `SpellingTwinTest`. Visible "detection skipped" lines. The
  `.baleignore` signals. The grammar row and the description rewrites."
  D: "Piped and `--json` runs copy too, because the key is an explicit
  per-machine opt-in. The `bale clipboard` verb, with its 0/1/2 exits.
  The request's project key baked in only as the no-bale fallback. No
  nudge when the key is unset. The helper living in `bale_report.py`.
  The `probe clipboard` row and its four states. One trailing newline on
  every copied block. The comment fix in `bale_config.py`, and the
  corrected `config init` description."
- Brief correction recorded against this desk, verbatim: "B's brief said
  "EOF and ^C still abort the pack". At the README question they never
  did: `confirm_yn` declines on both. The desk verified this against
  `bin/bale`. B followed outcome 1 rather than that sentence, and was
  right to."
- On this desk's line (§6 entries 220 to 222): the unverified fact in
  B's brief; a bundle hash typed in chat before it was computed,
  corrected in the same reply; two defects in D's oracle, both caught
  before delivery. Its authoring lesson for PLANNER.md §4 is the
  registry's rider of this date.
- Queued at the desk, as a claim so it could be contested: the log-hold
  micro-session first (B's native hold, the sweep y/N width, the wide
  pre-walk lines, the non-exiting accessor, D's `test_cli_help` and
  internals rider); clipboard-key-rename after it (C's neutral section,
  D's Proposals 2 and 3); choice-prompt-convergence after that (B's
  `bale_wizard` additions onto C's `ask_choice`, C's
  `walkthrough_baleignore` filters); this close beside any of them;
  99b's input held until the operator rules on BALE.md. The cleanup desk
  dispatched the first four in that order (its block below).
- Light-block ledger, from the brief: two blocks emitted, two answered
  "as assumed", zero formal, zero unanswered; no probe. The workers:
  `clarification.rounds: 0` on all three records, none carrying a
  `light_blocks` key; C's notes.md say "No light block, probe or
  clarification was used."
- Where the brief and the records part, found at this close: the brief's
  table says B applied with two admissions and C with none, and both
  hold; it says D's one, and that holds; it does not give the times, and
  the records put B's open-to-apply at 20 h 10 min against C's 45 min
  and D's 66 min, the arc's one long sit. The brief's Appendix A §4
  count for E, "24 `BALE.md` occurrences across 9 of 18 sections", is
  E's and is superseded by the ruling queue's bracket. Everything else
  the brief states of the three records held.
- Board deltas of this sitting's work: none, non-board; row 99's
  bracket. Registry deltas: the two consumption brackets (the `bale
  status` row at D, the triple-quote refusal at C); the stale-key
  bracket on the 99b riders entry; B's, C's and D's sets in the 99b
  routing entry; the PLANNER.md §4 rider; the two log-hold riders; the
  dispositions entry. In §5, the 2026-10-03/04 block; in §6, entries 220
  to 222; the three watches (§3 Watches).

Landed 2026-10-05, the friction-points cleanup desk
(`2026-10-04-friction-points-cleanup-002`, read-only, work class meta;
bale 0.4.45 at its pack; bundle stem
`2026-10-04-friction-points-cleanup`, brief sha256 `951a114b…305c`,
checkpoint null, by its record's `bundle` key; packed 01:58:35Z, and its
`created_at` reads the same second; its pack swept the wave2-004 desk;
`opened` in the snapshot this close read, and listed open by its own
probe beside `2026-05-14-bale-handoff-008`). The arc's third and last
desk. It authored the four sessions the wave2-004 desk queued, each as a
crafter bundle with a blind checkpoint dry-run through `bale open
--dry-run` against a working copy of the shipped tree (exit 1 before the
work, exit 0 on a stub of the outcome; the two later checkpoints also
exit 1 on stubs of the trees they will meet), ran one probe, and wrote
close 20's brief, this block's source with its appendices. Zero light
blocks, one probe (`friction-close-inputs`, 44 lines, answered). This
block carries only what has no row home; close recorded by
`2026-10-05-sitting-close-deltas-20-001`:
- Dispatched, by the brief's table, recorded here as dispatched only;
  the landings, decisions and Proposals of the three code sessions
  belong to the next close. log-hold: stem `2026-10-04-log-hold`, bundle
  `0fa7564b…f129`, brief `46807438…cd22`, checkpoint v1 `f0fba9d3…2d9e`;
  opened and applied before close 20 packed, tag
  `applied/2026-10-04-log-hold-003`, checkpoint PASS, worker PASS, no
  admissions, by its relay as close 20's brief reports it.
  clipboard-key-rename: stem `2026-10-04-clipboard-key-rename-r2`,
  bundle `f213bdfd…218e`, brief `c4cd0d05…ab3d`, checkpoint
  `bc843282…c2c9`. choice-prompt-convergence: stem
  `2026-10-04-choice-prompt-convergence-r2`, bundle `20e1dd59…e54c`,
  brief `61a4f5f3…3eae`, checkpoint `cdf0778f…495e`.
  sitting-close-deltas-20: stem `2026-10-04-sitting-close-deltas-20`,
  checkpoint `bf6dc891…2b71`, this close, whose request stamps the same
  checkpoint sha256. The two `-r2` bundles replace first issues
  (`1f2c9438…af28c` and `9f69062c…eafb0`) that never opened: same briefs
  and checkpoints, with the reads the include miss left out. Order, as
  dispatched: log-hold and this close first, beside each other;
  clipboard-key-rename after log-hold applies (both touch `bin/bale` and
  `bin/bale_config.py`); choice-prompt-convergence after
  clipboard-key-rename applies (both touch `bin/bale_config.py`, and it
  shares `bin/bale_pack.py` with log-hold).
- Desk pins carried in the dispatched briefs, contestable until each
  session packs, in the desk's words. clipboard-key-rename: inside one
  file `[clipboard] command` wins over `[probe] clipboard_command`;
  across files the layer rule is unchanged (the project file decides
  when it sets either spelling, `""` in either spelling suppressing); a
  file setting both is never silent; `bale config init` writes the new
  spelling and carries a legacy value over. choice-prompt-convergence:
  every answer at the shape question and the checkpoint picker keeps its
  meaning, including the picker's out-of-range number taken as a path
  when a file of that name exists in cwd, and `?` as a path answer
  there; `?` help joins the shape question, where it is no answer today.
- Findings at the desk: C's note that `ask_choice`'s out-of-range rule
  follows "the checkpoint picker's rule" is inexact, the picker taking
  an out-of-range number as a path when a file of that name exists in
  cwd, carried into choice-prompt-convergence's brief; response archival
  is on at the global layer (`archive_dir = "claude/responses"`, the
  probe), so A's and E's notes.md, which the wave2-004 brief called
  unreachable, were in the repo all along, and they shipped to this
  close; the registry's 99b riders entry still said "project layer only"
  (its bracket of this date); the stale open session (§3 Watches).
- The probe, `friction-close-inputs`, verbatim in close 20's brief: WSL2
  host, `/home/chordsphere/bale-src` on `main` at `8f0bbc4`, bale
  0.4.45, MASTER.md sha256 prefix `4b45a684a46adf83` with the header
  naming close 19, five applied tags since 2026-10-03, the global
  `[apply]` table with `search_paths`, `archive_dir` and `sweep = true`
  and no project `[apply]` table, five archived notes.md, eight records
  (five `applied`, two `unlocked`, one `opened`), two open sessions.
  Close 20's base matched: 12,476 lines, `4b45a684…3eb8`, before it
  inserted.
- On this desk's line (§6 entry 223): the include miss delivered in
  log-hold's pack, entry 215's class repeated, caught at log-hold's
  relay and corrected in the two `-r2` reissues before either opened;
  and one draft slip caught before its bundle was emitted, log-hold's
  brief first attributing the two pre-walk log lines' pins to the wrong
  suites.
- Light-block ledger, in the desk's words: "light blocks 0; probes 1
  (`friction-close-inputs`, answered)." Close 20's own count is in its
  notes.md.
- Where the brief and the records part, found at this close: the brief's
  registry state lists two open sessions, this desk and the May sid, and
  names log-hold applied since, by relay; close 20's request carries no
  record of log-hold or of the May sid, so neither is verified here
  beyond the brief's word. Everything the brief states of the eight
  records it shipped held.
- Sequencing for the next desk: clipboard-key-rename once log-hold has
  applied (it has, by the brief), then choice-prompt-convergence; the
  next close records the three; 99b waits on the BALE.md ruling; the
  standing line after the 45 arc is unchanged (S6; row 103 ongoing; row
  93 stands). By the cadence, the next master's last job is its wave's
  close.
- Board deltas of this sitting's work: none. Registry deltas: the
  bracket on the 99b riders entry. In §6, entry 223; in §7, the arc's
  facts; the fourth watch (§3 Watches).

Landed 2026-10-06, the friction-points cleanup desk's wave and the
desk's close (`2026-10-04-friction-points-cleanup-002`, its block
above). The desk closed `closed-read-only` at 2026-10-06T19:11:36Z by
the `2026-10-06-friction-points-close-desk-002` pack, which its record's
`swept_by` names, one second before that desk's own `packed_at`,
19:11:37Z by its brief; the attempt is on `command: pack`, and the
record's top-level `outcome` reads `unlocked`; the desk stood open 2 d
17 h 13 min 1 s from its pack. Four sessions, the four it dispatched,
all applied: log-hold, close 20, clipboard-key-rename and
choice-prompt-convergence. Sources: the four records and the cleanup
desk's, the four archived notes.md, and close 21's brief, authored by
the close desk. The tags (`applied/<sid>`) are by each session's relay,
by the cleanup desk's brief; no record carries a tag. This block carries
only what has no row home; close recorded by
`2026-10-06-sitting-close-deltas-21-004`:
- Landing record, in apply order from telemetry. Every session: one
  attempt, first pass; checkpoint PASS, exit 0, stamp matched, no failed
  probes; worker validation PASS, exit 0, `reconciliation_parsed: true`;
  no admissions, `overridden_paths` empty and no required-check or
  base-drift override; confined, the network grant exercised, no sandbox
  escape; `budget_pressure: none`, no compaction; `clarification.rounds:
  0`; `corrects` null. `2026-10-04-log-hold-003`: opened
  2026-10-04T02:33:14Z, its `packed_at` 02:33:13Z, one second earlier;
  `applied` at 2026-10-05T00:12:44Z, 21 h 39 min 30 s later; checkpoint
  sha256 `f0fba9d3…2d9e`; two claims, the scoped suites observed and
  `agree`, the `--slow` full suite predicted against a `skip`, `n/a`;
  ten `change_paths` under a six-entry forecast (`bin/bale`,
  `bin/bale_config.py`, `bin/bale_pack.py`, `bin/bale_report.py`,
  `claude/context/bale-internals.md`, `tests`), five of them suites;
  `model_identity` `anthropic:claude-opus-5-5`.
  `2026-10-05-sitting-close-deltas-20-001`: opened 00:28:56Z, 16 min 12
  s after log-hold applied; `applied` at 01:03:02Z, 34 min 6 s later;
  checkpoint `bf6dc891…2b71`; five claims, each observed and `agree`;
  one `change_paths`, `claude/MASTER.md`, its whole forecast;
  `model_identity` `anthropic:claude-fable-5-1`.
  `2026-10-05-clipboard-key-rename-002`: opened 01:05:59Z from the `-r2`
  bundle, its `packed_at` 01:05:58Z, 2 min 57 s after close 20 applied;
  `applied` at 2026-10-06T15:44:25Z, 38 h 38 min 26 s later, the wave's
  long sit; checkpoint `bc843282…c2c9`; ten claims, nine observed and
  `agree`, the `--slow` full discovery observed against a `skip`, `n/a`;
  thirteen `change_paths` under an eight-entry forecast;
  `model_identity` `anthropic:claude-fable-5-1`; the record carries
  `self_reported.light_blocks: 0`, the arc's first record to carry the
  key. `2026-10-06-choice-prompt-convergence-001`: opened 15:49:59Z from
  its `-r2` bundle, 5 min 34 s after the rename applied; `applied` at
  19:07:41Z, 3 h 17 min 42 s later; checkpoint `cdf0778f…495e`; six
  claims, five observed and `agree`, the `--slow` pack neighbors
  observed against a `skip`, `n/a`; seven `change_paths` under a
  five-entry forecast; `model_identity` `anthropic:claude-opus-5-5`.
  Across the wave: four applies on four attempts, zero HOLDs, zero
  retries; 23 claim rows, 20 `agree`, 3 `n/a`, none unreconciled; 31
  `change_paths`; no admitted path; all four bumpless on 0.4.45.
  `contract_docs` moved once, `docs/TARBALL.md` `f6c3326e…` to
  `32680c8e…` between the rename's request and convergence's, the rename
  having edited it.
- What landed, in short (the notes.md carry the detail; every count is
  the worker's own, on its partial `context/` tree). log-hold:
  `bin/bale`'s native log hold, `hold_log()` / `release_log()` /
  `log_holding()` with a `log_held()` context manager, journaling a held
  line when it is logged and holding only the print, `fail()` releasing
  first and an `atexit` release; `WalkLogHold` deleted; display wrapping
  in `bin/bale` section 2, opt-in and on today only for pack's pre-walk
  lines, piped output byte-identical; the sweep's y/N laid out through
  `confirm_yn_decision(..., wrap=True)`, its only caller; the
  non-exiting clipboard reader; D's `("clipboard",)` and internals
  rider; 1796 tests in discover form, passing but for the seven failures
  the unmodified tree shares, from files the request did not ship. Close
  20: the friction-points arc's record in `claude/MASTER.md`, 829 lines
  inserted and the header line edited, proved by reversal.
  clipboard-key-rename: `[clipboard] command` the key at both layers,
  `[probe] clipboard_command` read as a legacy alias, `[clipboard]
  command` winning inside one file and the file never silent about it;
  the `bale status` row labelled `clipboard` and `--json`'s `clipboard`
  object; the wizard carrying a legacy value into the new spelling and
  the review naming the move; the crafter's scan reading both spellings;
  1834 tests in full discovery, `validate.sh` 94 checks.
  choice-prompt-convergence: the pack walk's shape question, all three
  forms, and its checkpoint picker drawn and asked through
  `bale_wizard`'s `ask_choice`, every answer keeping its meaning and `?`
  help joining the shape question; pack's per-path filter chain moved
  into `bale_pack.pack_drop_reason`, which `walk_for_pack` and config
  init's `.baleignore` suggestions both call, so the suggestions count
  only files pack would ship; no whole-suite count given.
- Ratified at the cleanup desk, as shipped, every flagged decision of
  the four notes.md, by the operator's "as assumed" to its light block
  two, [1] (log-hold's five and close 20's seven, close 20's extra §7
  bullet kept), and light block four, [1] (the rename's eight and
  convergence's seven, convergence moving pack's per-path filter chain
  into `pack_drop_reason` among them); both blocks are §5's entry of
  this date, verbatim. Each decision by its own heading or lead-in,
  verbatim from its notes.md. log-hold: 1, "The hold journals at log
  time; only the print waits."; 2, "`WalkLogHold` is deleted, not
  thinned."; 3, "Display wrapping is opt-in, and today only pack's
  pre-walk lines use it. Look closely here."; 4, "The sweep's y/N: a
  keyword only the sweep passes."; 5, "Clipboard rider:
  `clipboard_command_reading(repo)` → `ClipboardCommandReading(command,
  source, refusal)`.". Close 20: 1, "The stale key is bracketed, not
  edited, in three places."; 2, "Rulings in §5, ratifications in §3.";
  3, "The wave2-004 desk's brief correction is not a §5 line."; 4, "E's
  unreconciled claims are a records finding, not a defect."; 5, "The
  dispositions entry says what the records bear out and no more."; 6,
  "The cleanup sessions are recorded as dispatched only"; 7,
  "`validation.sh` embeds the insertion ledger.". clipboard-key-rename:
  1, "How the two spellings merge."; 2, "An unreadable new key never
  falls through to the legacy one"; 3, "The row's exact words for the
  spelling."; 4, "`bale status --json` says which spelling."; 5, "The
  wizard's carry-over."; 6, "The review names the move."; 7, "D's
  `--block` notice wording."; 8, "Names.". choice-prompt-convergence: 1,
  "The layer grew options, not a sibling primitive."; 2, "What the
  picker's screen now says."; 3, "The picker still reads digits the way
  it did."; 4, "`?` at the shape question."; 5, "One filter chain."; 6,
  "What now stops a file from counting toward a suggestion."; 7, "Three
  edge rulings in the suggestions.". The rename's decision 7 asked
  whether its reading of D's `--block` notice wording was the one meant;
  ratified as shipped, its reading stands.
- Routed at the cleanup desk, by its light blocks two, [2] and [3], and
  four, [2] and [3], and its brief where they name no home, and checked
  against the notes.md by the close desk: thirteen Proposals,
  dispositioned in the registry's entry of this date. Three wait in the
  ruling queue, three ride as registry riders, three BALE.md sets join
  99b's routing entry, two are board rows 134 and 135, one is the 0.4.46
  bump and one is record only. Consumed by the wave, each bracketed in
  the registry: the non-exiting accessor rider and D's `test_cli_help`
  and internals rider at log-hold, the `bale status` row's relabel at
  the rename.
- Light-block ledger (PLANNER.md §6). The cleanup desk, in its brief's
  words as close 21's brief carries them: "four light blocks (two
  answered "as assumed", two replaced without an answer) and one probe,
  answered". Close 20's block for the desk reads "light blocks 0; probes
  1", which was true when the desk wrote close 20's brief: all four
  blocks came after it, during the wave, so the two counts are dated,
  not in conflict. Blocks one and three went unanswered and were
  replaced by two and four, block four's [2] folding block three's
  changelog question in by its own "while doing"; one and three were not
  carried to the close desk, so only two and four are quoted (§5). The
  workers: `clarification.rounds: 0` on all four records; the rename's
  carries `self_reported.light_blocks: 0`, and the other three carry no
  such key.
- Where the brief and the records part, found at this close: nowhere on
  the records. Everything close 21's brief states of the four records
  held: the applied times, checkpoint and worker states, stamps,
  admissions, decision counts and `light_blocks`; so did the cleanup
  desk's closure time and `swept_by`. Two things the brief asks this
  close to check are recorded on other evidence: the `bale status` row's
  relabel on the rename's notes.md and record, `bin/bale_report.py` not
  having shipped (the registry bracket says so); and the close desk's
  own `packed_at`, on the brief's word, no record of that desk having
  shipped.
- Board deltas of this sitting's work: rows 134 and 135; row 99's
  bracket. Ruling queue: three entries. Registry deltas: the three
  consumption brackets (the non-exiting accessor, D's help-suite and
  internals rider, the `bale status` row); the 99b routing entry's
  bracket with three sets; the bracket on close 20's dispositions entry;
  three riders (the close desk's `contract-doc` rider is its own
  block's); the dispositions entry. In §5, the block of this date; in
  §6, entry 224; the dotted-key watch (§3 Watches); in §7, the wave's
  facts.

Landed 2026-10-06, the friction-points close desk
(`2026-10-06-friction-points-close-desk-002`, read-only, work class
meta; bale 0.4.45 at its pack; packer `chordsphere`; packed
2026-10-06T19:11:37Z by its manifest; its pack swept the cleanup desk;
it stays open until the next read-only pack sweeps it or the operator
unlocks it). It succeeded the cleanup desk and authored close 21 and the
0.4.46 bump. Its brief, authored by the cleanup desk, is its request's
README (sha256 `ddb62a74…d540`). No record of the desk shipped to close
21; this block is its record as close 21's brief gives it (Appendix C),
flattened. This block carries only what has no row home; close recorded
by `2026-10-06-sitting-close-deltas-21-004`:
- What it did: verified the cleanup desk's brief against the four
  records and notes.md, every verdict and admission holding, and the
  decision counts, five, seven, eight and seven; verified every
  Proposal's routing (the registry's dispositions entry of this date);
  scoped and authored two sessions, each as a crafter bundle with a
  blind checkpoint, forecast-disjoint and meant to run beside each
  other: this close (`claude/MASTER.md`) and the bump (`bin/VERSION`,
  `claude/changelog`). It ran no probe, so it holds no registry reading
  of its own; the last on record is the cleanup desk's of 2026-10-04.
- The bump, as dispatched only; the next close records its landing. Stem
  `2026-10-06-bump-0-4-46`, bundle sha256
  `7bc43027a8c03232ec24d7cf9268b74d33c72156177de3038017451dc076e345`,
  brief
  `f034bc003da44e372c1408ac1d2ca46958e03a6c284155fa844d71c760b531be`,
  checkpoint v1
  `0623f824126d9b28b0f9bb1a679b6152d4aef37aec54f80bc7c29077476d6303`;
  forecast `bin/VERSION` and `claude/changelog`. Close 21's own identity
  is its request's provenance: checkpoint
  `claude/checkpoints/2026-10-06-sitting-close-deltas-21-004.sh`, sha256
  `bf55c4ee…4dc0`, base `claude/MASTER.md` `b1ed2936…ddf2`.
- Dry-runs: each checkpoint exits 1 on the shipped tree, 0 on a stub
  landing built from its brief's own bytes, 1 on stubs each missing one
  outcome, and 2 when its control breaks. The bump's bundle was also
  rehearsed with `bale open --dry-run` in a scratch git copy of the
  desk's shipped tree (exit 1 from the checkpoint, every argv gate
  passed), placeholder files standing in for the five archived notes.md
  and records its request did not carry.
- Rulings and reads of the desk. The changelog's scope, in its words:
  "Block 4 [2] named four sessions, "C, D, log-hold, the rename". The
  brief asked this desk to read convergence. By the schema's own list
  ("schemas, closed vocabularies, record and manifest shapes,
  CLI-accepted values, the release layout"), A (`bin/bale_wizard.py` in
  the release layout) and E (`BALE_HELP.md` in every request) changed
  surfaces the four-name list leaves out; by the 0.4.44 and 0.4.45
  records' practice of naming each changed `bin/` module, all eight
  sessions of the arc that changed bale's code did. The bump's brief
  asks for rows for all eight, the ratified four pinned and the other
  four the desk's read, flagged to the operator in chat."
  `contract-doc`: routed as the registry's rider of this date.
  Sequencing: the bump and this close run beside each other; rows 134
  and 135 are queued, unscheduled; the three ruling-queue entries and
  the BALE.md ruling wait on the operator; 99b waits on the BALE.md
  ruling.
- Light-block ledger: zero light blocks, zero probes, zero clarification
  rounds.
- Findings at the desk: block four [2]'s four-name list (above; §6 entry
  224); the cleanup desk's summary of convergence's picker Proposal,
  which drops a "consider" (the ruling queue's entry of this date);
  `docs/TARBALL.md` moved from `f6c3326e…` in close 20's request to
  `32680c8e…` in the desk's, the rename having edited it; bale-src's own
  `bale.toml` still on the legacy spelling (§7); the rename's record the
  first of the arc to carry `light_blocks`.
- Board deltas of this sitting's work: none of its own; rows 134 and 135
  are the cleanup desk's ruling, queued at this close. Registry deltas:
  the `contract-doc` rider.

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
    [2026-09-19: re-scoped at the 009 sitting by the operator's reply to
    the desk's light block, [2], verbatim: "probably fine, I just feel
    like we might be getting into "documentation in bale-src but not
    covered in global docs" so I just want to double check that since
    BALE.md doesn't ship with other projects". Read as yes, with a
    standing condition, in the 009 desk's words: "what a worker or an
    operator on ANOTHER project needs must be in the five global docs or
    the two tools, because BALE.md never leaves bale-src." The row
    predates work that has landed; verified on the 0.4.37 tree by the
    009 desk and re-verified by the `2026-09-20-continue-plan-001` desk:
    part 2 is built (the crafter's header documents `--kind bailout`
    and, under `--write`, the full artifact set; `docs/TARBALL.md`
    §5.6.1 names `tools/craft_response.py --kind bailout --write`;
    `docs/CLAUDE.md` §11.4 routes to §5.6 for the shape); part 3 is
    built (`schemas/telemetry-record.schema.json` carries the `bailout`
    outcome; `bin/bale_stats.py` computes `bailout_sessions` and
    `bailout_rate` and reads `budget_pressure`). Not built: the string
    "compaction" does not occur in `bin/bale_stats.py`;
    `docs/TARBALL.md` §5.2.2 documents `compaction_occurred`, and
    nothing reads it (the 08-31 ruling counted its fifteen disclosures
    by hand). What survives: a stats read side for
    `feedback.self_reported.compaction_occurred`; the stale
    `docs/TARBALL.md` §5.8 sentence ("left to the user (jq, notebook,
    eventual `bale stats` command)", though `bale stats` exists and
    reads bailouts) trued up, riding row 104; and the PLANNER.md
    single-window-premise paragraph, with 110's Proposal 1 (the §5 step
    5 retry clause, §3 registry) riding the `docs/PLANNER.md` touch. The
    `docs/CLAUDE.md` §11.4 pointer shrinks to at most a clause and may
    be nothing. The row's BALE.md stats sentence goes to 99b's inputs.
    113's `tests/test_craft_response.py` path guard rides this row if
    its cut holds that file (§3 registry). The `docs/TARBALL.md`
    collision with row 104 (this row's §5.8, 104's §3.1 and §3.4) was
    cut on 2026-09-20 at the 001 desk, once row 104 was ruled: 104
    holds the file, and this row's §5.8 sentence rides it.]
    [2026-09-20: DONE at `2026-09-20-board-37-compaction-read-side-003`
    (0.4.38; held once on a blind probe, one rejected apply, applied on
    retry; §3's close-15 block for the 001 sitting). Built: a stats read
    side for `feedback.self_reported.compaction_occurred`, the keys
    `cross_checks.budget.compaction.{reporting_sessions,occurred_sessions}`
    and `members.compaction_occurred`, any-attempt, counts and no rate,
    on its own line under the budget line, homed in `bin/bale_stats.py`'s
    docstring (§5, "New, ratified 2026-09-20"); the single-window-premise
    paragraph, closing PLANNER.md §11; and 110's Proposal 1 in PLANNER.md
    §5 step 5 (§3 registry). A pre-existing crash in the budget pressure
    pass, fixed on the way, was kept at the 006 desk. On the real corpus:
    206 reporting, 7 disclosing, over 276 parseable records (§5's
    calibration bracket). Not built, as the bracket above allowed: the
    `docs/CLAUDE.md` §11.4 pointer (37 did not hold the file). The §5.8
    sentence landed at 104a. No BALE.md edit; the stats keys are 99b's
    input (row 99). 37 did not hold `tests/test_craft_response.py`, so
    113's craft guard rides that file's next holder (§3 registry).]

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
    [2026-09-17: the dossier wiring (the §3 registry's `bale stats
    --sid` entry) consumed at `2026-09-17-stats-micro-001`, beside
    rows 86 and 98.]
    [2026-09-24: DONE at
    `2026-09-23-board-43-tarball-s5-compression-008`, bumpless on
    0.4.43, applied 2026-09-23T12:45:24Z on the worker's corrected
    tarball after one HOLD (§6 entry 213). Section 5, heading line to
    heading line: 988 → 735 lines, 7,267 → 5,534 words, about a quarter,
    under the brief's "a third to half" estimate; the worker stopped
    where cutting further meant cutting rules, the keep-list's judgment
    prose and the pinned sentences intact. Shape prose the schemas
    already carried now points at `response-manifest.schema.json`,
    `exchange-record.schema.json` and `diagnostics.schema.json`; 5.5,
    5.6.3 and 5.9.3 are one-sentence tombstones dated by session; 5.7's
    template is a header list; the `expects_probe: no` collision is
    homed in §3.3, with one pointer line in 5.9's lead and one in 5.9.1;
    ADR-0013 citations 10 → 9, all keyed; version tokens 5 → 0. The
    three VERBATIM riders landed, retiring the registry's §5.9 courier,
    §5.2.2 emitter and §3.4 include-rule entries (the §5.2.2 entry's
    `--fragment` clause stays). `SectionFiveCompressionPins` adds eight
    tests. Every judgment call ratified as made.]

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
    [2026-09-24: first wave complete; the second wave gated on S6. The
    design sitting `2026-09-23-board-45-hostile-repo-design-010`
    designed stemwell, a small Python CLI in its own repo, and authored
    its seed and first wave: seven sessions applied in stemwell between
    2026-09-24T01:44:22Z and 13:13:46Z, one HOLD, one seed abandoned
    (§3, the design-010 block). The arc close
    `2026-09-24-board-45-close-008` reported upward
    (`claude/context/board-45-arc/`). By watch item, from the report:
    hot-file forecast serialization chafes and the gate is right, 15 min
    40 s from 2a's open to 2b's and 8 min 55 s from wave1's landing to
    wave4's open, with a second cost the row did not name, read-side
    coupling (wave2a's HOLD; row 129); validation budgets chafe quietly,
    met by declared omission, no wave running the three slow modules,
    and the locale test failing on the operator's C-type shell; the
    ceremony floor measured, one character of code carried by a
    six-file, 7,729-byte response in 7 min 25 s, and two admit prompts
    per new file (row 130); misunderstanding did not dominate off doc
    work, zero clarification rounds in seven sessions and wave5's
    designed trap passed unprompted; probe economics, one round trip of
    2 minutes, the design desk's packing causing more probe pressure
    than the environment (rows 131 and 133). Two defects the report puts
    on the design desk are the master desk's (§6 entry 218; row 132).
    The report's Proposals 1 to 5 are rows 129 to 133, S6 as consumer;
    the stemwell workers' Proposals are held until S6 (§3 registry).]

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
    [2026-09-16: split at the desk. 47a DONE at
    `2026-09-16-board-47a-hold-card-triage-001`, 0.4.34: the card's
    `validation:` row is replaced by a judge line (checkpoint, worker,
    or both; exit 2 counts as the checkpoint side), a `failed probes:`
    row from the stamp's captured output, and a trailer of
    ruling-forked successors — fixture defect: `bale amend-checkpoint
    <amendment> --sha256 <hex> --sid <sid>` then `bale retry '<held>'
    --accept-checkpoint-change --sid <sid>`; work defect: `bale retry
    '<held>'` — composed from the `held_tarball` stamp outcome so card
    and amend agree by construction, a literal base rendering a
    commit-directly note. `failed_probes` rides every executed stamp
    and the `--json` key list; the `validation_will_run`/`corrects`
    rider consumed. Seen live by 99a's worker on its own HOLD the same
    hour. 47b (the addressed desk-facing and worker-facing blocks with
    the log bands inlined, the happy-path desk block, the TARBALL.md
    sentence) stands, wave 3.]
    [2026-09-17: 47b stands, and its next open carries a rider list:
    the pack-json `sweep`/`include_group` key (moved here from the §3
    registry); `base_drift_overrides` in
    `format_session_dossier_json`'s docstring;
    `compose_hold_successors`' docstring (now delegated to, since
    106); the `DOCS_READ_EMPTY_STUB` sentence in TARBALL.md §5.2.2;
    removal of `bale_apply.py:~3763`'s post-resolution existence check
    (unreachable since 106). Brief input, the HOLD card's substance:
    its "next step" offers two categories, fixture and work; the
    sitting hit a third twice — a base defect, neither fixture nor
    work (§6 entry 151).]
    [2026-09-18: DONE at `2026-09-18-board-47b-relay-blocks-003`,
    0.4.36. On a HOLD, two sentinel-bracketed blocks print before the
    card, in send order —
    `=== RELAY BEGIN <sid> to planner ===` and
    `=== RELAY BEGIN <sid> to worker ===`,
    each closed by its `RELAY END` twin and each opening with where to
    paste it; the planner block inlines this attempt's checkpoint and
    worker log bands, and the worker block carries the judge line, the
    failed probe labels, the worker's own validation output, and the
    quoted `bale retry` line, nothing else of the checkpoint's. The
    card's trailer opens with the `send first:` line; the successor
    fork gains the third ruling, `base defect`, whose retry rung
    re-states every admission the held apply exercised and carries
    `--sid`. A clean apply prints one planner block (verdict,
    admissions, `notes.md`). TARBALL.md §7 gains the worker-facing
    paragraph. Four riders consumed; the pack-json rider moved to row
    104. The interim operator rule in this row's 2026-09-10 bracket is
    retired — the tool routes (§5, 2026-09-18). Row 47 is complete.]

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
    [2026-09-17: DONE with row 57 at
    `2026-09-17-board-56-57-changelog-aborted-002`, 0.4.35: schema
    `changelog-record`, `validate_changelog_record`,
    `claude/changelog/<version>.json` (the first record is 0.4.35's
    own), the discipline sentence at CODE.md §8.5. First attempt HELD
    on a base defect (§6 entry 148); retried unchanged and landed.]

57. **`aborted`-class closure reason** — queued 2026-08-25 (small;
    from the harness spec-intake sitting, seed D15): the harness
    kill-switch wants a closure vocabulary entry; additive,
    follows the v0.4.7 legacy-tolerant pattern. Ratified as its
    own small board item alongside board 56; sequencing among the
    smalls is the next desk's call.
    [2026-09-17: DONE with row 56 at
    `2026-09-17-board-56-57-changelog-aborted-002`, 0.4.35: `aborted`
    in the telemetry schema's `closure_reason` enum and in
    `CLOSURE_REASONS`, so `bale unlock --reason` and `bale revert
    --reason` accept it.]

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
    [2026-09-16: DONE at `2026-09-15-board-68-open-gate-order-012`,
    bumpless under 0.4.33. `cmd_open` now runs compose → parse →
    pre-flight (existence, then disjointness) before the checkpoint
    leg; the replay re-runs both gates (a cost ordering, not a
    substitute). Ratified: a `pending_supersession` exclusion in the
    pre-flight only (the replay stays authoritative); the five-site
    config-judgment family with one `config_judgment_suffix`; the
    whole-tree remedy lead on handoff too; an unparseable stored argv
    refuses at argparse before any dry-run. Riders consumed: FORCE
    doubling, `tools` in this repo's release-surface pulls, the
    ADR-0015 remedy text, and row 96's opener sentence. Proposals: the
    BALE.md open-order sentence (landed at 47a); `cmd_handoff` →
    `refuse_missing_scope_paths` (row 106); the opener-pin relocation
    (landed at pack-UX); `--gates-only` declined.]

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
    [2026-09-16: 96-crafter touched both tools files this sitting
    (the lint's docstrings no longer say `provenance` is hand-added);
    the crafter's size — bundle, probe, emit-block, light-block modes
    — is now the extraction question this row should answer first.]
    [2026-09-17: DONE at `2026-09-16-board-69-tools-pair-008`
    (bumpless): the `CLAIMS_VALUE` lint row; `docs_read` seeded in the
    crafter's skeleton, loud when unfilled (`DOCS_READ_EMPTY_STUB`);
    the crafter clipboard rider consumed. The extraction question
    answered "not yet; the exchange pair (§5+§6) is the one seam".
    Watch: revisit if §5+§6 passes ~60 KB or sessions touching the
    pair stop touching the rest. The tools' self-containment repair
    landed at `2026-09-17-board-69-selfcontainment-fix-both-005` (§6
    entry 148).]

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
    [2026-09-23: DONE, folded into the 100 arc's wave: the prose sweep
    at W1 (`2026-09-23-board-100-w1-doc-sweep-002`) and the constant at
    W2 (`2026-09-23-board-100-w2-code-surfaces-003`), `INJECTED_TOOLS` →
    `CARRIED_TOOLS` by ruling 8, with the two inject senses W2 kept
    ratified at the design sitting (§5, 2026-09-23; row 100's bracket).]

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
    [2026-09-16: DONE at `2026-09-15-board-91-82-crafter-pair-011`.
    `--request` seeds `feedback.mechanical.provenance` verbatim plus
    `model_identity: ""` in the skeleton's stdout; the four lint-owned
    members seeded `false` and `self_reported` seeded with two
    schema-invalid sentinels so an unfilled block cannot pass, which
    reorders §5.2.2 to fill-before-emit (the clause landed at
    96-crafter); `--request` admitted on all three kinds; the request's
    `session_id` must equal `--sid`. Dogfooded on its own response.]

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
    [2026-09-16: DONE at `2026-09-16-board-pack-ux-micro-004`. Warns,
    never refuses, when an included test's `import tests.x`, `from
    tests.x import`, or bare-sibling `import x`/`from x import`
    resolves to a `tests/<name>.py` absent from the shipped set after
    excludes (this repo's idiom is bare siblings — 49 files); stdlib
    names never fire.]

85. **exchange-carried-outside-relay self-report** — queued
    2026-09-14 (schema + docs + lint): a worker-side field in the
    response manifest recording rounds carried by paste, so
    telemetry stops reading a real round as zero (VERBATIM,
    operator: "There should be a way to note that when the worker
    packs the final tarball"). Three specimens this sitting (§6
    entry 115). The mechanical half of the §3 exchange-adoption
    watch.
    [2026-09-16: DONE at `2026-09-16-board-96-crafter-85-light-block-002`.
    `feedback.self_reported.paste_carried_rounds` (integer, min 0),
    optional; the lint's embed refreshed; §5.2.2 rows for both counts.
    The read side is row 98's.]

86. **stats drill-down row for handoff-origin sessions** — queued
    2026-09-14 (small; bin/bale_stats): `command == "handoff"` at
    persist. From 73A's Proposals; the corpus in this sitting's
    context had zero such sessions.
    [2026-09-17: DONE at `2026-09-17-stats-micro-001`
    (`corpus.handoff_origin_sessions`), beside row 98.]

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
    [2026-09-16: DONE at `2026-09-15-board-91-82-crafter-pair-011`,
    bumpless under 0.4.33. The schema already admitted `origin` by
    `$ref` and bale's validator by the v0.4.24 row check; the refusal
    was the crafter's `QUESTION_OPTIONAL_KEYS` alone. Parity pinned in
    `test_schema_embeds` (`QuestionRowKeyParity`); the exchange-record
    schema left untouched on the one-home rule; both section-29
    registry riders consumed.]

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
    [2026-09-16: DONE at `2026-09-16-board-pack-ux-micro-004`. One rule
    per include entry, printed as typed: it drops when no listed path
    equals it or lies under it (gitignored entries, empty directories,
    and on handoff a nonexistent reading-plan path). An untracked
    file that ships gets no line. The handoff `--verbose` E2E pin is
    a registry rider.]

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
    [2026-09-16: split at the desk into three file-disjoint thirds.
    Doc third DONE at `2026-09-15-board-96-doc-97-terminal-shapes-013`
    (bumpless): the four chat invitations struck plus four more the
    worker found (§4.1, §5.1, §2, INDEX), §5.10 landed format-first
    (sentinels `=== LIGHT BEGIN <sid> ===`/`END`, labels `[n] question
    / while doing / would assume / why blocked` onto the four row
    fields, no integrity trailer, "formal" re-enters through §10.3, a
    §10.4 checklist), PLANNER.md §15's packer half, CLAUDE.md's shapes
    paragraph at five with the every-turn sentence, the §9 pivot
    bullet pointed at the shapes. The opener's closing sentence landed
    at 68 (the one `bin/bale_pack.py` line). Crafter third DONE at
    `2026-09-16-board-96-crafter-85-light-block-002` (bumpless):
    `--light-block FILE [--sid]` renders §5.10 from a clarification
    manifest (four rows refuse; a line break in a field refuses as the
    count rule's one-line half; optional row keys never render, stderr
    names them), `feedback.self_reported.light_blocks` (integer, min
    0), the `--bundle` stem clock sentence in `--help` via
    `CraftHelpFormatter`, §10.4 step 2 names the flag. The pack-flag
    third (force formal on the `expects_probe` pattern) is deferred
    to the 100 arc's enum session. Row 105 rewrites the shape
    sentence's second half; row 104 makes it kind-conditional.]

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
    [2026-09-16: DONE at `2026-09-15-board-96-doc-97-terminal-shapes-013`.
    DOCS.md's spelling won: CLAUDE.md's INDEX row and TARBALL.md §3.1's
    example say `claude/context/adr/`; DOCS.md unchanged (its bare
    `adr/` in §5 read as relative shorthand, left). §3.1's example
    is illustrative under the prefix rule; left.]

98. **Stats read-side `context/` normalization** — queued 2026-09-15
    (bin/bale_stats.py; low). From board 94's Proposals, VERBATIM:
    "Strip a leading `context/` from `docs_read` tokens at read time
    in `bale_stats.py` so the three historical records aggregate with
    the repo spelling, without editing them." Additive doctrine: no
    retroactive record edits. Stands until a stats session brings it
    forward.
    [2026-09-16: grown — the stats micro also reads the two new
    self-reported counts, `light_blocks` and `paste_carried_rounds`
    (a paste-carried round adds to `clarification.rounds` rather than
    hiding under it), and row 86 rides beside it.]
    [2026-09-17: DONE at `2026-09-17-stats-micro-001`, with row 86 and
    row 44's dossier wiring. New stats keys
    `corpus.handoff_origin_sessions`, `corpus.docs_read`,
    `light_blocks_total`, `paste_carried_rounds_total`,
    `clarification_rounds_total`.]

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
    [2026-09-16: 99a DONE at `2026-09-16-board-99a-outward-docs-003`,
    bumpless (re-attempt; see the close block). README rewritten to
    the tree (every verb, every `bin/` module, five docs, ten daily
    flows, no date; install readers pointed at `bale help <command>`
    because `scripts/build.sh` excludes BALE.md — whether the release
    should ship it is in the ruling queue); every `--help` string read
    against behavior, the `bin/bale` flag surface proven unchanged by
    a parser-hash check; the `[probe] clipboard_command` config
    carrier consumed — project layer only, the reason in the prompt,
    the accessor refusing crafter-unreadable values loudly, a new
    suite `tests/test_probe_clipboard_config.py`. 99b stands on the
    100 arc's doc wave, now also carrying: the new key, open's order,
    retry's two rulings, the two pack warnings, and a re-true of the
    README/help HOLD wording against 47a's landed card.]
    [2026-09-20: 99b's inputs grow: 37's stats keys for BALE.md §5.6
    (`cross_checks.budget.compaction.{reporting_sessions,occurred_sessions}`
    and `members.compaction_occurred`; home `bin/bale_stats.py`'s
    docstring, and 37 made no BALE.md edit), and the context pack's
    section, BALE.md §7.8, written at 104a. Its note that the
    `context-packed` outcome word lives in `bin/bale_pack.py` changes if
    104a's Proposal 1 lands at 104b.]
    [2026-10-05: 99b's inputs grow again, and one shrinks to history.
    The friction-points arc routed five BALE.md sentence sets to 99b,
    A's (§2, §3.6, the commands table), E's (§3.3, §5.1, §6.1, §7.5),
    B's (§7.3), C's (the key's layering and the numbered alternatives)
    and D's (status, probe, a `clipboard` verb entry), verbatim in the
    §3 registry's routing entry of this date. The 2026-09-16 bracket's
    "project layer only" is what 99a landed, not the rule now: since C
    (`2026-10-03-wizard-defaults-006`, ruling [1] of 2026-10-03, §5) the
    key is per-machine at both layers. The citation recount 99b waits on
    is the ruling queue's bracket of this date: 24 occurrences, 9 of 19
    sections, 9 board mentions.]
    [2026-10-06: 99b's inputs grow by three more sets, the cleanup
    desk's wave: log-hold's (the goal-less walk's held lines, pack's
    wrapped pre-walk lines, the sweep's y/N, the copy's `NOT copied`
    notice), the rename's (the `[clipboard] command` key and its legacy
    alias, the `bale status` row and its `--json` object) and
    convergence's (§7.3's shape question and checkpoint picker, config
    init's `.baleignore` counts), verbatim in the bracket of this date
    on the §3 registry's routing entry. The key 99a landed as `[probe]
    clipboard_command` is `[clipboard] command` since
    `2026-10-05-clipboard-key-rename-002`, the old spelling a legacy
    alias. 99b still waits on the ruling queue's BALE.md entry.]

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
    [2026-09-23: DONE, closed as an arc at close 18. The design sitting
    ran twice: `2026-09-22-board-100-design-004`, the paired-desk trial,
    closed `superseded-by-split` at 2026-09-23T00:23:18Z, and its
    successor `2026-09-23-board-100-design-001` (bundle stem
    `2026-09-23-board-100-design-revc`, brief sha256 `e313b601…0ac7`),
    which made rulings 1 to 9 (§5, 2026-09-23), authored the wave's
    three bundles and ratified their notes.md (§3, the two blocks).
    Depth: layers 1 to 3 landed, layer 4 as a config key only, renaming
    no existing repo (ruling 2). The wave, in apply order from
    telemetry. W1, `2026-09-23-board-100-w1-doc-sweep-002`:
    contract-doc, bumpless; opened 01:04:36Z, `packed_at` 01:04:35Z;
    forecast `README.md`, `docs`, `tests/test_doc_crossrefs.py` and
    `tests/test_sanctioned_pairs.py`; brief `b81a8d61…b294`, checkpoint
    `058975d0…50e9`; applied 01:45:46Z, one attempt, confined, network
    grant exercised; checkpoint PASS, exit 0, stamp matched, no failed
    probes, sha equal to the published; worker validation PASS, three
    claims each observed, the doc suites `agree`, the full suite (gated
    `--slow`) `skip`, the session assertions `agree`; drift admitted,
    `tests/test_global_doc_noun.py` (source `prompt`); nine
    `change_paths`; `model_identity: anthropic:claude-fable-5.1`;
    `budget_pressure: none`. It landed the noun sweep, rulings 4 to 7 in
    the docs, and the guard. W2,
    `2026-09-23-board-100-w2-code-surfaces-003`: code, 0.4.42; opened
    01:08:10Z, `packed_at` 01:08:11Z, one second later, the reversed
    order; forecast `BALE.md`, `bin`, `claude/changelog`, `schemas`,
    `tools` and seventeen named tests; brief `69cd7805…7d38`, checkpoint
    `7cdc0b62…ddec`; applied 01:54:02Z, one attempt, confined, grant
    exercised; checkpoint PASS, exit 0, stamp matched, sha equal; worker
    validation PASS, two claims observed, the session assertions
    `agree`, the unit suite `skip`; drift admitted,
    `tests/test_forecast_ledger.py` and
    `tests/test_layout_and_formats.py` (`prompt`); 32 `change_paths`. It
    landed `agent-decides` admitted with the emitted value unchanged
    (amendment A), `[layout] agent_dir`, the `contract_docs` `oneOf`,
    the `model_identity` pattern and `CARRIED_TOOLS`. W3,
    `2026-09-23-board-100-w3-file-rename-004`: mixed, 0.4.43; opened
    02:00:12Z, `packed_at` 02:00:11Z; forecast the release surface,
    `BALE.md`, `README.md`, `bin`, `claude/changelog`, `docs`,
    `install.sh`, `schemas`, `scripts/build.sh`, `tests`, `tools`,
    `upgrade.sh` and `validate.sh`; brief `aa426b40…7f78` (revB),
    checkpoint v1 `0ba3d3fd…5917`. HOLD at 02:54:24Z: the checkpoint
    exited 1 with no failed-probe label, stamp matched, every labeled
    probe passing and worker validation exiting 0 on five claims, each
    observed and `agree`. Ruled a fixture defect at the design sitting
    and corrected as v2, sha256
    `b8c69ae841956633ede50639c4b9309a80629e3bb8efe82900b045a9b149bed5`,
    probe 3 only, every non-probe failure route exiting 2, amended on
    the tree (commit `9fea009`); no new response. Applied at 03:07:57Z
    on `bale retry` of the held tarball: checkpoint v2 PASS, exit 0,
    `stamp_matched: false`, accepted per invocation; worker validation
    PASS, five claims `agree`; no admissions; 47 `change_paths`,
    `docs/AGENT.md` created and `docs/CLAUDE.md` deleted among them; the
    suite at 1507 tests, 48 skipped, green, and `validate.sh` at 93
    checks. Git: `7cb52ce` the landing, `a88f85b` the merge, `d855163`
    the sweep. The upward report, `upward-report-board-100-design.md`,
    sha256 `0b1f8081…d97c`, reached the 005 desk with the three relays;
    its partition, claims, consumed and deferred lists and four
    Proposals are this bracket's source as that desk digested them. Its
    six follow-on rows, placed at close 18: (a) → row 124; (b) → row
    126; (c) → row 127; (d) → the registry, the §11.7 entry; (e) → row
    125, with Proposal 2; (f) → row 128. Its Proposals: 1 → §6 entry
    208, no sitting kind; 2 → row 125; 3 → row 122's second half; 4 →
    the registry's `docs/PLANNER.md` entry. The report's own "Follow-on
    rows" text did not travel in close 18's request, only its name and
    hash, so it is not quoted here; a desk holding the archive can
    bracket it in. The archive, `claude/context/board-100-arc/`,
    committed directly by the operator (ruling 9):
    `design-brief-board-100-revB.md` `e313b601…0ac7` (346 lines),
    `implementation-decomposition-revA.md` `b2573fd4…4054` and the
    report; the directory did not exist at the close-18 probe. Row 77
    rode the arc, DONE; rows 116 and 118 were its inputs, DONE.]

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
    [2026-09-16: DONE at `2026-09-15-board-102-explicit-name-010`,
    0.4.33. The bare-name lookup already existed for both verbs; the
    delta was the miss: near-name candidates (typed stem as prefix,
    the `(1)` twins) listed as complete `shlex.quote`d lines for the
    typed verb, newest first; handoff got the listing too; the
    non-TTY line quoted; the docstring rider consumed. BALE.md's
    sentence landed in §8's bare-form paragraph; 47a widened it to
    name handoff. Its Proposal (a shared `fail_not_found` for the
    absolute and no-search-path miss branches) is row 106's.]

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
    [2026-09-20: the design sitting's bundle was authored at the
    `2026-09-20-continue-plan-009` desk, in two revisions:
    `2026-09-20-board-103-probe-design`, never opened and stale once
    wave 8 applied, and `2026-09-20-board-103-probe-design-r2`,
    reauthored at the operator's word (§3's close-16 block for the 009
    sitting). What that desk found about this row's own text, and handed
    to the design desk in the brief: `cost.model_tier` is not a home a
    probe run can fill, since `bin/bale_report.py` at 0.4.39 stamps the
    cost block all-null and reserves it for the harness, and what exists
    is the self-reported `model_identity` in the response manifest's
    provenance echo; and "identical argv" N ways meets the pack-time
    disjointness gate, and the tree moves once any run applies (§6 entry
    189). What the records show of the sitting being opened, the
    2026-09-21 facts dated here in the text, as close 14 dated row 37's:
    `2026-09-20-board-103-probe-design-010` opened 2026-09-20T03:52:14Z,
    read-only, work class meta, its `packed_at` 03:52:11Z, the second
    its pack swept the 009 master; it closed `closed-read-only` at
    2026-09-21T01:18:25Z by command `unlock`, which stamps no
    `swept_by`. `2026-09-21-board-103-probe-design-001` opened
    2026-09-21T01:18:56Z, 31 seconds later (`packed_at` 01:18:55Z), and
    closed `closed-read-only` at 02:59:37Z by a pack, the
    `2026-09-21-continue-plan-002` pack, as its `swept_by` says. Neither
    record names a bundle, so which revision either open used is in no
    record. By the operator's word at the `2026-09-21-continue-plan-002`
    desk, the sitting ran this row's first wave on 2026-09-21, four runs
    in clones of a seed project outside this repo, so the runs have no
    records here; that wave's record belongs to close 17.]
    [2026-09-21: the operator's third message at the
    `2026-09-21-continue-plan-002` desk, his reply to its light block
    two, whole and verbatim:
    "as assumed, and I want to clarify that I want to change board 103 to an ongoing type of test instead of completing the arc with the open weight model. I don't have access to an open weight model just yet and i'm only using claude so let's drop that for now, I just want to eventually formalize this process because it was so effective. A later board for another time, just wanted to clarify all that. Reauthor close 16 if you need, I haven't packed yet".
    The ratified reading, by his "yes" to that desk's light block three,
    [3]: this row does not close on a wave two and becomes a standing
    test; the open-weight run is dropped for now; formalizing the probe
    as a repeatable process is a new row, for later and not sequenced
    (row 114). Light block two's [2], about a wave two, was ratified and
    mooted in the same message, and the standing line now reads "row 103
    ongoing" (§3, close 17's blocks). The arc so far. The design
    sitting's two sessions are above. Wave one ran on 2026-09-21 as four
    runs in clones of a seed project outside this repo, so the runs have
    no records here; the findings file, `board-103-wave1-findings.md`
    (the operator's, not in this repo, 410 lines, sha256
    `7dd87cd1…fbd3`), and his ledger are the only sources, and this
    bracket cites the file by section and carries nothing of the kit's
    task, bait or canned answer (§6 entry 200). The findings sitting was
    `2026-09-21-board-103-probe-findings-003`: opened 03:01:25Z,
    `packed_at` the same second, read-only, work class meta;
    `closed-read-only` at 12:20:31Z, swept by the
    `2026-09-21-continue-plan-005` pack. Its file reached the
    `2026-09-21-continue-plan-002` desk with the operator's first reply
    there. Header: four packets, `fable5-a`, `fable5-b`, `sonnet5-a` and
    `sonnet5-b`, Fable 5.1 and Sonnet 5 at n=2 each; the four requests
    byte-identical bar `packed_at`; the global docs in them CLAUDE.md
    `52c8771d…` and TARBALL.md `b7265475…`, the set close 16's record
    echoes, so the wave ran on the docs as they stood before the doc
    lane. §1: the oracle separated nothing. All four landed trees pass
    the blind checkpoint, 13 of 13, re-run at the findings desk; all
    four `validation.sh` scripts fail on the seed and pass on their own
    landing; the lint is clean on all four final responses. The process
    rows did separate the models, consistently at n=2: four things
    tripped in both Sonnet 5 runs and in neither Fable 5.1 run, and
    three of the four trace to a passage that is missing or buried. The
    rubric's reading-path row tripped in all four runs, and the docs
    caused it, a finding about the docs and the rubric and not about
    either model. §3.2: the paste courier had no delivery instruction,
    which the file calls the wave's cleanest separator, off-rubric; both
    Sonnet 5 runs' first paste blocks were refused at relay, and both
    Fable 5.1 runs' relayed first time (§2). §6: of the design desk's
    six held findings, four confirmed or reproduced, one consistent with
    its mechanism unverified, and the `bale validate` one half confirmed
    there and confirmed whole at the `2026-09-21-continue-plan-002` desk
    (row 118); and every run asked formally where a guess would have
    failed the oracle, so the clarification path carried the wave. §7:
    eleven Proposals; the doc lane, `2026-09-21-board-103-doc-lane-006`,
    landed Proposals 1 to 6 and 10, and 7, 8, 9 and 11 are rows 115 to
    118. §8: seven candidate code items; 1 to 4 are the two micros'
    sources (§3 registry), 5 to 7 are row 119. §9 lists five places
    where the design desk's brief parted from the packets' bytes. §10 is
    the verdict and what a second wave should change, now row 114's
    input. §11: the findings sitting emitted one light block because its
    packets tarball did not arrive with its request, answered by
    attachment, and Proposal 9 came out of it (row 117; §6 entry 195).]

104. **Session kinds, switchable; the context pack** — queued
    2026-09-16 (pack + manifest + opener + docs). A session declares a
    kind at pack time, carried in the manifest and stated in the
    opener's first line: `build` (today's contract — forecast,
    checkpoint, the four terminal shapes, a response tarball);
    `discussion` (chat is the deliverable; no tarball unless asked;
    the shape rule does not apply; a light injection — CLAUDE.md's
    core plus a short discussion section, not the wire contract);
    `master` (the desk sitting: read-only, authoring bundles and
    briefs in chat); `context` (bare `bale pack` in a directory
    produces a session-less tarball of that tree — no sid, no lock,
    no opener, no telemetry — named for the directory, to travel
    beside another project's request as reading material; the
    operator has done this by hand for months). The kind is a
    declared start, not a cage: the architect switches it at will,
    and a session switches itself at named transitions — a worker
    that reaches a split becomes a secondary master to its own fleet;
    a discussion that reaches a solid point becomes a master or a
    build, declaring its forecast at that moment (ADR-0015's
    where-will-changes-land follow-up is the mechanism). `--read-only`
    today conflates an empty-forecast build with a discussion; it
    stays for the former and `--kind` names the rest. The opener's
    closing sentence is kind-conditional (the shape sentence for
    build; "answer in chat; no tarball unless I ask" for discussion).
    Specimen: a read-only discussion on another project returned an
    empty-`changes[]` tarball because the docs carve out no
    discussion and the shape rule wins by silence — the worker's own
    diagnosis, verbatim: "right now the docs don't say, and the shape
    rule's default wins by silence" (§6 entry 146). The doc-injection
    split rides the 100 arc's doc sweep; the rest is its own session
    after row 105.
    [2026-09-18: grown four riders — the pack-json
    `sweep`/`include_group` key, now with the stamp sweep's result
    (107's Proposal 1; moved from 47b, §3 registry); the stale
    `depends_on.superseded_session` comment in `cmd_pack`; 105's
    Proposal 2, the tools' stdlib-only pin; and the three-homes wording
    question for the shape sentence.]
    [2026-09-19: parts consumed by the opener reword (row 112).
    Transported verbatim from the 006 desk's brief: "It consumed parts
    of row 104 — bracket them: the kind-conditional opener closing
    sentence (built, keyed on read-only rather than a `--kind`), and the
    "three-homes wording question for the shape sentence" rider (the
    sentence is retired). What 104 still holds: `--kind` and the
    manifest kind field, the `discussion` and `context` kinds, the light
    injection, the pack-json `sweep`/`include_group` key with the stamp
    sweep's result, the stale `depends_on.superseded_session` comment in
    `cmd_pack`, and 105's Proposal 2." The row is re-scoped at the 009
    desk before it packs; that ruling is close 14's to record, not this
    close's.]
    [2026-09-20: re-scoped. Narrowed by the operator's answer to the 009
    desk's light block, [1], given at the `2026-09-20-continue-plan-001`
    desk, verbatim: "104: narrowed, as the 009 desk recommended; the
    global-doc constraint on the context pack is agreed." What "as the
    009 desk recommended" means, in that desk's words: "narrow 104 to
    the `context` pack plus its riders — the pack-json
    `sweep`/`include_group` key with the stamp sweep's result, the stale
    `depends_on.superseded_session` comment in `cmd_pack`, 105's
    Proposal 2, and close 13's two Proposals — and leave `--kind`, the
    manifest kind field and the light injection to the 100 arc, where
    the row already sends the injection." The agreed constraint, also
    its words: "A `context` pack has a receiving side: a worker on
    another project gets a session-less tarball beside its request.
    What that artifact is, and that it carries no sid, no opener and
    owes nothing back, must be stated in the global docs
    (`docs/TARBALL.md` §3.1 and the §3.4 flag table), not only in
    BALE.md." Two new riders, close 13's two Proposals: `packed_at` on a
    pack's `opened` telemetry attempt, and the closing pack's sid on a
    swept or superseded attempt (§3 registry); the row holds
    `bin/bale_pack.py` and the schemas. It also holds `docs/TARBALL.md`
    against row 37 (cut at the 001 desk once this row was ruled), and
    row 37's §5.8 sentence rides it. Verified for the row by the 009
    desk: read-only already keys the opener's closing and the
    deliverable sentence (row 112); a broad include withholds checkpoint
    bytes loudly rather than refusing, so a bare master pack is safe.
    "NOT read: any code the `context` pack would touch." That stays true
    at the 001 desk.]
    [2026-09-20: cut in two at the `2026-09-20-continue-plan-004` desk,
    by file map, from the code. 104a, the context pack, DONE at
    `2026-09-20-board-104a-context-pack-005` (0.4.39), both in-file riders
    consumed (the stale `depends_on.superseded_session` comment; row 37's
    TARBALL.md §5.8 sentence). 104b, the pack-side telemetry riders,
    dispatched by the `2026-09-20-continue-plan-006` desk as
    `2026-09-20-board-104b-pack-telemetry` beside close 15, forecast
    `bin/bale_pack.py`, `bin/bale_report.py`, the telemetry schema,
    `BALE.md`, `tests`, `validate.sh` and the bump: the pack-json
    `sweep`/`include_group` key with the stamp sweep's result and close
    13's two Proposals (§3 registry), plus 104a's Proposals 1 to 3. 105's
    Proposal 2 was in 104b by the 004 desk's cut, and the 006 desk's
    registry dispatch does not name it. The spelling ruled at the 004
    desk by the operator's reply, "as assumed, and both applied:":
    `bale pack --context`. This row's "bare `bale pack`" wording is
    superseded, and goal-less `bale pack` stays the wizard. The
    subdirectory outbox ruled by [2] at the 006 desk: a context pack in a
    repo subdirectory lands under that subdirectory's `.bale/outbox/`, as
    shipped. `--kind`, the manifest kind field and the light injection
    stay with the 100 arc, per the bracket above.]
    [2026-09-20: 104b DONE at `2026-09-20-board-104b-pack-telemetry-008`
    (0.4.40; one apply attempt, no hold, no admissions; §3's close-16
    block for the 006 sitting). Built: `bale pack --json`'s two
    always-present keys, `sweep` and `include_group`, with the stamp
    sweep's result among `sweep`'s events (107's Proposal 1);
    `packed_at` on a pack's `opened` attempt, and `swept_by` on a
    closure the read-only sweep wrote, stamped once the sid is minted
    and committed as its own sweep event (close 13's two Proposals);
    104a's Proposals 1 and 3 (the context report homed in
    `bin/bale_report.py`; `validate.sh`'s `--context` check). 105's
    Proposal 2 turned out to be built already: by 104b's notes.md, board
    69 (d)'s `ToolsHermeticPin`, which 104b renamed so that
    `-k stdlib_only` selects it, no assertion changed. Not taken: 104a's
    Proposal 2, the cap/breach loop, back on the §3 registry. Shapes in
    §5, the 009 desk's block; homes BALE.md §7.7, §7.8 and §8.9 and the
    telemetry schema. With 104a, that completes this row as narrowed:
    `--kind`, the manifest kind field and the light injection stay with
    the 100 arc, per the brackets above.]

105. **Operator-voice authority framing** — queued 2026-09-16 (doc
    lane with one `bin/bale_pack.py` string). Three edits that change
    what every fresh model reads first: (1) the opener — typed by the
    operator, in chat, the one legitimate channel — says in the first
    person that the docs and tools in the tarball are the operator's,
    written for this workflow, to be read as the operator's
    instructions for the session, and says what the two tools are
    (stdlib-only formatters, no network, read before running,
    conveniences — the doc is the contract and a hand-authored
    response is valid); (2) CLAUDE.md's precedence sentence says what
    it means — this file wins over stale memory of prior bale
    sessions, never over the model's own guidelines; (3) the shape
    sentence gains its second half: explanation in prose is expected
    and welcome; the rule is that a turn that *asks* ends in a block
    so nothing is lost. Specimen: an outside model declined the
    framework on exactly these grounds (§6 entry 145). Goes first in
    the next wave.
    [2026-09-17: DONE at `2026-09-16-board-105-operator-voice-007`
    (bumpless): the opener's operator-voice sentences on both pack
    shapes, CLAUDE.md's precedence sentence, and the shape sentence's
    second half; the light-tier INDEX-row registry rider consumed.]

106. **`bin/bale` de-dup micro** — queued 2026-09-16 (bin/; one
    session, five riders on one file). From this sitting's Proposals:
    a shared `fail_not_found(kind, path, verb)` for the three
    not-found lines so the absolute-path and no-search-path miss
    branches get the near-name listing too (102); `cmd_handoff` calls
    `bale_pack.refuse_missing_scope_paths` — the last copy of that
    gate (68); `compose_retry_successor` delegates to
    `bale_report.compose_hold_successors` so the amend report and the
    card agree structurally, not by test (47a); split
    `BaleignoreMatcher.from_lines`'s error text so it stops naming
    `.baleignore` and each caller prefixes its source (pack-UX);
    `RawDescriptionHelpFormatter` on the subparsers so descriptions
    keep their paragraph breaks and `completion --help` its examples
    (99a). Runs beside wave 3.
    [2026-09-17: DONE at `2026-09-17-board-106-bale-dedup-003`
    (bumpless-under), spanning `bin/bale` and `bin/bale_pack.py`;
    `compose_retry_successor` delegates to `compose_hold_successors`.
    HELD on a fixture defect — the near-name probes pinned a quote
    character; the desk amended the checkpoint (v2) and the landing
    retry used `--accept-checkpoint-change` (§6 entry 152). The
    in-process opener constants test is consumed here (§3 registry).]

107. **`--supersedes` leaves `main` dirty** — queued 2026-09-17 (high;
    `bin/bale_pack.py`). Cause, desk-verified in the bytes: the
    `--checkpoint-file` path commits only the checkpoint (`git commit
    -- <path>`), and `stamp_superseded_by` then modifies the parent's
    tracked telemetry record; the sweep commit that carries other
    telemetry events never sees it. The operator hit it
    2026-09-17T02:41Z and committed by hand. Fix: the stamp lands
    inside the pack's commit (or the sweep's). Blind checkpoint: the
    repro in a scratch repo with a tracked telemetry dir and a
    `[validation] base` pin, a second pack `--supersedes` the first
    (prompt acceptance needs the pty harness; non-TTY declines), then
    `git status --porcelain` empty.
    [2026-09-18: DONE at `2026-09-18-board-107-supersedes-clean-tree-004`
    (bumpless-under): `cmd_pack` calls a new `sweep_superseded_by_stamp`
    right after `stamp_superseded_by`, handing `sweep_commit` the one
    stamped path once the child sid exists, as
    `[bale sweep <parent>] superseded_by <child>`;
    sweep unset or false is byte-identical to before; five tests, three
    failing on the 0.4.35 bytes; `bin/bale` untouched. The row's
    "`git status --porcelain` empty" was one inference off (§6 entry
    156).]

108. **Guard maintenance** — queued 2026-09-17 (in flight when the
    brief was written): `INSTALL_SCHEMAS` + `changelog-record`; the
    hyphenated `board-<digits>` deny shape with a sid-aware anchor;
    the two tolerated tools leftovers rewritten;
    `claude/changelog/<bin/VERSION>.json` must exist (ruling: every
    bump carries a record; §5).
    [2026-09-17: DONE at `2026-09-17-guard-maintenance-006`
    (bumpless), applied clean 2026-09-17T13:01Z per its telemetry
    record — after the brief, before this close packed. Its
    self-report names one light block with three defaults ratified as
    assumed, and further crafter provenance leftovers proposed rather
    than rewritten; its notes.md queues to the next open.]

109. **Harness micro** — queued 2026-09-17 (small; tests):
    `_load_cli()` beside `_load_module` (106's proposal); the queued
    `normalize()` registry rider (rides `tests/harness.py`); and
    `SubcommandHelpLayoutTest` moved to a new `tests/test_cli_help.py`
    with the completion pins.
    [2026-09-18: two thirds and one rider DONE at
    `2026-09-18-board-109-harness-micro-002` (tests-only): `_load_cli()`
    in `tests/harness.py` (a `SourceFileLoader` under `bale_cli`, fresh
    module per call, `sys.path` hygiene, the `__main__` reach-back limit
    documented and pinned); `normalize()` with one home there; the §5.10
    shape pin (§3 registry). The loader's tests landed in a new
    `tests/test_harness_cli_loader.py`, out of forecast and admitted at
    apply. The `SubcommandHelpLayoutTest` move is row 111's now — the
    class shares `tests/test_apply_preflight.py` with 47b's
    `HoldCardUnitTest`.]
    [2026-09-19: its deferred third DONE at
    `2026-09-19-board-110-held-admissions-007`'s session (rider 6), not
    111's: `SubcommandHelpLayoutTest` moved whole to a new
    `tests/test_cli_help.py`, same four tests, same names. The move
    followed `tests/test_apply_preflight.py` to its holder at the wave-5
    cut.]

110. **Held admissions stamped at HOLD** — queued 2026-09-18 (code;
    `bin/bale`, `bin/bale_apply.py`, `bin/bale_report.py`, and tests —
    `HoldCardUnitTest` in `tests/test_apply_preflight.py` among them).
    The defect in one sentence: the fixture-defect retry rung and
    `bale amend-checkpoint`'s report retry the same bytes without
    re-stating admissions, so a held apply that needed
    `--allow-out-of-scope` refuses at the fixture retry — and 109
    shipped an out-of-forecast file this very wave. Text verbatim from
    `2026-09-18-board-47b-relay-blocks-003`'s Proposals: "**Stamp the
    held apply's admissions at HOLD time.** Write them beside
    `held_tarball` (e.g. `.bale/sessions/<sid>/held_admissions`).
    *Why:* the fixture-defect retry rung and `bale amend-checkpoint`'s
    report both retry the same bytes, but neither re-states the
    admissions, so a held apply that needed `--allow-out-of-scope`
    refuses at the fixture retry. The base rung only gets this right
    because the card renders in-process. *Scope hints:* `bin/bale`
    (`compose_retry_successor`, `read_held_tarball_stamp`),
    `bin/bale_apply.py`'s inspect branch, `compose_hold_successors`'
    fixture fork. The card and amend report must change in one session
    to keep their byte agreement." Card and amend report change in one
    session. Riders on `bin/bale`: `cmd_retry`'s twin existence check
    after `resolve_inbound_path(..., verb="retry")` (47b's Proposal 2 —
    prove it unreachable as 47b proved `cmd_apply`'s, and look at
    `handoff`'s); `from_lines`' stale "at v0.1" marker; `run_hook`'s
    three placeholder-less f-strings (both from the §3 registry); and a
    `compose_retry_successor` unit test through `_load_cli()` (109's
    Proposal 2; it needs a scratch repo with held-tarball state).
    [2026-09-19: DONE at `2026-09-19-board-110-held-admissions-007`,
    0.4.37: the stamp `.bale/sessions/<sid>/held_admissions` beside
    `held_tarball`; the card's fixture rung and
    `bale amend-checkpoint`'s last line byte-equal and re-stating every
    admission (the E2E lands the printed line and pins the pre-0.4.37
    bare line REJECTED); riders 1–6 all landed (both twin checks retired
    with proofs; "at v0.1" gone, its pin in `tests/test_pack_guards.py`
    edited out of forecast; `run_hook`'s three f-strings;
    `ComposeRetrySuccessorUnitTest` through `_load_cli()`; the
    `test_apply_preflight.py` docstring true-up;
    `SubcommandHelpLayoutTest` moved whole to a new
    `tests/test_cli_help.py`). Its two Proposals → §3 registry.]

111. **Tests smalls** — queued 2026-09-18 (tests only):
    `SubcommandHelpLayoutTest` from `tests/test_apply_preflight.py` to a
    new `tests/test_cli_help.py` with the completion pins (row 109's
    deferred third); `_load_cli()` adopted in
    `tests/test_thread_status.py` (`load_bale_module`) and
    `tests/test_craft_response.py` (`ExchangeBlockParity.setUpClass`),
    retiring the two ad-hoc loaders (109's Proposal 1); a pin for
    TARBALL.md §7's worker relay paragraph in a doc-pin suite (47b's
    Proposal 3).
    [2026-09-19: DONE at `2026-09-19-board-111-tests-smalls-008`
    (tests-only, bumpless), narrowed at the open to the two
    `_load_cli()` adoptions and the relay pin; the class move went to
    110. Proposal 1 → §3 registry; Proposal 2 → row 113.]

112. **Opener reword; what each session owes back — DONE at birth**
    2026-09-19 at the unrecorded `2026-09-19-session-fix-002` sitting
    (§3, close 13's first block):
    `2026-09-19-opener-reword-doc-sweep-r2-003` (closed
    `superseded-by-split`), `2026-09-19-opener-reword-code-004` and
    `2026-09-19-opener-reword-docs-005`, bumpless under 0.4.36. The
    opener reworded and re-wrapped, closing by session kind keyed on
    read-only; the manifest's top-level `readme` key; the `$EDITOR`
    scaffold comment never ships; the README written once from hashed
    bytes; the ask and deliverable rulings landed VERBATIM in
    `docs/CLAUDE.md` §3, `docs/TARBALL.md` §2 and §5.10 (§5, "New,
    ratified 2026-09-19"). Consumed two of row 104's parts (its
    2026-09-19 bracket).

113. **Every suite's dotted run form** — queued 2026-09-19 (tests only;
    micro). Text verbatim from `2026-09-19-board-111-tests-smalls-008`'s
    Proposals, its nested markers flattened: "**What:** consider giving
    `test_thread_status.py` the same `tests/`-on-path guard the doc-pin
    suites carry, so its docstring's
    `-m unittest tests.test_thread_status` run line works. **Why:** that
    dotted form errors today, both before and after this change. It is a
    module-level `from harness import` without the guard. I didn't add
    the guard here because it's outside the stated goal
    (behavior-preserving adoption). A proposal seemed better than a
    silent scope stretch. **Scope hints:** `tests/test_thread_status.py`
    only. Several other harness-importing suites likely share the same
    stale run line, so a sweep may be the better unit." The desk counts
    55 suites importing `harness` at module scope, so the unit is a
    sweep or a single-point fix, not one file.
    [2026-09-19: DONE at `2026-09-19-board-113-dotted-run-form-011`
    (tests-only, bumpless), dispatched the sitting it was born: a new
    `tests/__init__.py`, the desk's four lines plus a docstring naming
    the one run form that executes it, which puts `tests/` at
    `sys.path[0]` when absent; the pin in a new
    `tests/test_dotted_run_form.py`, which does not import `harness` and
    loads each suite dotted in a fresh interpreter; both admitted at the
    prompt, out of forecast. `tests/harness.py` took the `CLI_PATH`
    comment rider (§3 registry) and a module docstring naming three run
    forms; `tests/test_thread_status.py`, forecast, was left untouched,
    because its dotted run line now works. A correction, by bracket: the
    "55" above is the grep count of module-scope `harness` imports; the
    measured failure count was 56 of 68 suites, confirmed by the
    worker's baseline (its notes.md, "Baseline, before any change"). Its
    two Proposals → §3 registry: 1 split, 2 declined.]

114. **Formalize the capability probe as a repeatable process** — queued
    2026-09-21 (later, not sequenced; born of row 103's ruling). The
    operator's words, from his message on row 103's 2026-09-21 bracket:
    "I just want to eventually formalize this process because it was so
    effective. A later board for another time". Row 103 is now a
    standing test; this row makes it a process a desk can rerun. Its
    inputs: the findings' §10, what a second wave should change (task
    size, a forced HOLD, tool-call capture, a rubric v2, runbook
    additions), cited and not detailed, the file being the operator's.
    The open-weight run was dropped for now by the same message, and
    nothing here revives it.

115. **The opener's tools sentence** — queued 2026-09-21 (code,
    suite-pinned; the operator's own voice). The findings' Proposal 7,
    verbatim: "7. **Rewrite the opener's tools sentence** to say what
    every run did: read each tool's header docstring and the section for
    the mode you run." The opener is bale-emitted and pinned by the
    suite, and it speaks as the operator, so the wording is his to give
    before the session is cut.

116. **Self-reported fields: a format for `model_identity`, and two
    more** — queued 2026-09-21 (an input to the 100 arc's design
    sitting). The findings' Proposal 8, verbatim, its nested markers
    flattened: "8. **Tighten §5.2.2's self-reported fields.**
    `model_identity`: pin a format. `includes_missing`: say whether it
    covers a missing decision as well as a missing file.
    `linkage.depends_on`: say what goes there for a same-session round.
    Three runs wrote their own sid; sonnet5-a wrote `null`." A live
    specimen: the three worker records of 2026-09-21 spell
    `model_identity` three ways,
    `2026-09-21-sitting-close-deltas-16-004` "Claude Fable 5.1,
    self-reported", `2026-09-21-board-103-doc-lane-006` "Claude Fable
    5.1 (self-reported)", and
    `2026-09-21-split-transition-unconditional-007` "Claude (Anthropic);
    exact model string not visible to the session".
    [2026-09-23: DONE, consumed as an input to the 100 arc. Ruling 4
    (§5, 2026-09-23) answers all three: `model_identity` spelled
    `<vendor>:<model>` with a pattern in response-manifest.schema.json
    (W2) and in the docs (W1); `includes_missing` covering a decision as
    a line opening `decision:`; `linkage.depends_on` null for a
    same-session round, a doc pin of the schema's own sentence. Every W
    record since spells it `anthropic:claude-fable-5.1`; the two wave-10
    micros, before the ruling, spelled it "Claude Opus 5
    (claude-opus-5)" and "Claude Opus 5".]

117. **A shape for "an attachment did not arrive"** — queued 2026-09-21
    (docs; needs the operator's ruling first). The findings' Proposal 9,
    verbatim, its nested markers flattened: "9. **Add a shape for "an
    attachment did not arrive".** Why: this sitting's first turn had to
    choose between the brief's light block and §5.10's "a question that
    *blocks* trustworthy work is a clarification response however short
    it reads". A dropped upload blocks, is not pasteable as a probe, and
    is heavy as a clarification." Four live specimens, all of
    2026-09-21: the findings sitting's packets tarball (the findings'
    §11); the `2026-09-21-continue-plan-002` desk's turn four, answered
    with a probe; and the `2026-09-21-continue-plan-005` and
    `2026-09-21-continue-plan-008` desks' openers, each answered in a
    light block, the file arriving on the reply (§6 entry 195).

118. **"Validate before apply" against what `bale apply` does** — queued
    2026-09-21 (docs; small). The findings' Proposal 11, verbatim: "11.
    **Reconcile "Validate before apply, always"** (TARBALL.md §8,
    CLAUDE.md §6) with what `bale apply` does, once the verb list is
    checked." The verb list is checked: 0.4.40's parser has fifteen
    verbs and no `validate` (the `2026-09-21-continue-plan-002` desk's
    read of `bin/bale`; §7), so row 103's own "`bale validate`, then
    apply or HOLD" names a verb that does not exist.
    [2026-09-23: DONE, consumed as an input to the 100 arc. Ruling 5
    (§5, 2026-09-23) rewords "Validate before apply, always" at both
    sites to land only through `bale apply`, which validates and stages
    before it merges, never hand-applying a tarball or bypassing a HOLD;
    the row type stays operator discipline. Landed at W1.]

119. **Three code smalls from the probe's findings** — queued 2026-09-21
    (code; small; one row). The findings' §8 items 5, 6 and 7, verbatim,
    flattened: item 5, "A clarification tarball and the final response
    share a filename within a session (§10.1 step 11). Both Fable runs
    warned about it; the runbook already tells the operator to expect
    `(1)`."; item 6, "Session-log timestamps run backwards (fable5-a:
    `02:41:09` then `02:41:07`; sonnet5-b: `02:45:33` then
    `02:45:31`)."; item 7, "The post-pack hook's `run this hook? [Y/n]`
    prompt stalls `bale open` in a batch (9.2)." Every file list is a
    guess until the authoring desk reads the code (§6 entry 188).

120. **A post-validation tree walk** — queued 2026-09-21 (code; decide
    first). The doc lane's second Proposal, a new row by the operator's
    "as assumed" to the `2026-09-21-continue-plan-005` desk's light
    block four, [1]. At 0.4.40 nothing checks an unannounced write made
    during `validation.sh`: reconciliation runs before the script and
    nothing walks the tree after it (that worker's read of
    `bin/bale_staging.py`), and TARBALL.md §7.1 now says the printed
    list is the whole of the check. Text verbatim from
    `2026-09-21-board-103-doc-lane-006`'s notes.md, flattened:
    "**What:** decide whether an unannounced validation-time write
    should stay review-only. A post-validation tree walk against the
    pre-validation snapshot would turn §7.1's "no surprise writes" into
    a contract rule. **Why:** I found at 0.4.40 that nothing checks it,
    and §7.1 now says so out loud. That is honest, but it is also an
    invitation to decide whether the gap is wanted. **Scope hints:**
    `bin/bale_staging.py` (`run_validation_sh`); `.validation-logs/` and
    `.bale-manifest.json` would need exempting."

121. **Argv-only gates before state-changing exchanges in `cmd_pack`** —
    queued 2026-09-23 (code; a bale defect). The paired-desk sitting's
    item 1 [ab], verbatim in §3's 004 block. A pack whose include gate
    refuses has already closed its `--supersedes` parent:
    `_resolve_supersession` runs before the gate, so the parent's record
    carries a `superseded-by-split` closure stamped by a pack that
    produced no child on its first paste, which the idempotent branch
    later recovered. The 004 record shows it: its closure is stamped
    00:23:18Z and the successor it names was created at 00:26:04Z. Run
    every argv-only gate before any exchange that writes another
    session's state. The item's line numbers (bale_pack.py:5223, the
    gate at 417–471 by item 9) are the desks' reads at 0.4.41; the
    authoring desk reads the code (§6 entry 188).
    [2026-09-24: DONE at `2026-09-23-board-121-125-code-micro-007`,
    0.4.44, applied 2026-09-23T13:37:44Z on `bale retry` after an
    oracle-defect HOLD (§6 entry 214). A new pass,
    `pack_pre_exchange_gates`, runs every argv-only refusal before
    `cmd_pack`'s first state-changing exchange: the two gates the brief
    named and, a flagged deviation ratified as made, slug and goal,
    planner-bundle naming and the `--max-*` values, with the whole
    blindness gate on the non-deferred path. The disjointness gate, the
    declined-supersession refusal and the read-only sweep stay after the
    exchange. The desk's fixture shows the specimen on 0.4.43 and the
    parent untouched on 0.4.44.]

122. **Rehearsal verbs** — queued 2026-09-23 (code; one row, two
    halves). First half, the paired-desk sitting's item 2 [ab]:
    `bale pack --dry-run` or `bale open --check`, running pre-flight and
    writing nothing, extending `pack_argv_preflight` to the include
    gate; the item's interim, until it lands, is PLANNER.md §4 doctrine,
    a desk with `bin/` in context rehearsing the line in a fixture
    before delivery, which no registry entry carries yet (close 18's
    notes.md). Second half, the 100 arc's upward report's Proposal 3:
    `bale open --dry-run` running a bundle's checkpoint against the
    base, so a probe a desk cannot run end to end is exercised before
    delivery (§6 entry 210).
    [2026-09-24: DONE at `2026-09-23-board-122-rehearsal-verbs-009`,
    0.4.45, applied first pass 2026-09-23T21:57:33Z, no admissions. Both
    halves: `bale pack --dry-run`, and `bale open --check` and
    `--dry-run`, argparse-exclusive, each a prefix of the real pipeline
    over one gate core cut from `cmd_pack` into named helpers, writing
    nothing to the repository; a real `bale open` now runs the same gate
    set before its checkpoint dry-run. The micro's Proposal 3 rode along
    (`pack_argv_preflight` calls `pack_pre_exchange_gates`). First field
    use in the stemwell arc (§3, the design-010 block). The item's
    interim doctrine is overtaken; its retirement rides the registry's
    PLANNER.md §4 entry.]

123. **A desk suffix on a second open of one sid** — queued 2026-09-23
    (code; small). The paired-desk sitting's item 4 [b]: a second open
    of one sid records a desk suffix and is not refused, since a refusal
    would have blocked the experiment that produced the finding.
    Specimen: the 004 record carries one `opened` attempt for the two
    desks the operator opened under it (§3, the 004 block).
    [2026-09-24: DONE at the micro, 0.4.44. A second `bale open` of a
    still-open session's bundle, matched on its manifest, brief and
    checkpoint hashes and never its stem, appends an `opened` attempt
    with `command: "open"` and `desk: "desk-N"` and prints an opener
    naming `<sid>@desk-N`; it refuses once the record holds an
    apply-side event. `desk` and the `open` value are additive in the
    telemetry schema, `record_version` unchanged. The scheme and the
    enum value ratified as made.]

124. **Render the configured `agent_dir` in messages** — queued
    2026-09-23 (code; small). The 100 arc's upward report, follow-on row
    (a): about twenty docstrings and messages still spell
    `claude/telemetry/`, which names the wrong path in a repo whose
    `[layout] agent_dir` is set. W2 deferred it and W3 left it open.
    [2026-09-24: DONE at the micro, 0.4.44. All 24 lines the desk
    counted: emitted messages render the configured
    `<agent_dir>/telemetry/` through `telemetry_home_display`, four
    literals remain stating the default, and `bale stats --help` renders
    the home lazily through a formatter reading config non-fatally,
    ratified as made.]

125. **`.baleignore` hygiene** — queued 2026-09-23 (small). The 100
    arc's upward report, follow-on row (e) with its Proposal 2:
    `bin/__pycache__` ships in packs, and the probe scaffold should
    exclude caches.
    [2026-09-24: DONE at the micro, 0.4.44, its claim not reproduced:
    the pack walk drops `__pycache__` by path component, tracked or not.
    The one writer found was a test child process importing the source
    repo's `bin/`, now run with `-B`. The probe skeleton carries a
    one-line cache-excluding listing, and `CacheHygieneTest` pins that
    request and context packs ship no cache member. Its two Proposals
    are registry entries.]

126. **`upgrade.sh`'s member list** — queued 2026-09-23 (decide first).
    The 100 arc's upward report, follow-on row (b). W3's brief said
    `upgrade.sh` carries a pre-flight member check among the rename's
    doc-name sites; its worker found `REQUIRED_RELEASE_MEMBERS` is
    bin/schemas/tools by design, left the file unchanged, and was
    ratified at the design sitting (§6 entry 211). What to decide:
    whether the list names the docs. The report's recommendation did not
    travel in close 18's request; the deciding desk reads it in the
    archive (row 100's bracket).

127. **A `pattern` for `provenance.packer`** — queued 2026-09-23 (decide
    first; needs a format ruling). The 100 arc's upward report,
    follow-on row (c): the other free-text identity beside
    `model_identity`, which ruling 4 pinned; the same mechanism, a
    description and a regex, once the format is ruled.

128. **The arc oracle's mechanical home** — queued 2026-09-23 (decide
    first). The 100 arc's upward report, follow-on row (f): PLANNER.md
    §20.1's queued slot for an arc-level oracle still has no mechanical
    home, and the 100 arc is the third arc to close without one.

129. **A staleness flag at reconciliation** — queued 2026-09-24 (code;
    consumer S6). The 45 arc's upward report, Proposal 1, verbatim, its
    markers flattened: "1. **Staleness flag at reconciliation.** Bale
    holds both timestamps; when a DISAGREE row's failing check touches a
    path landed since the session's `packed_at`, mark the row as
    read-side staleness rather than a bare disagree, and briefs name
    sibling surfaces in motion. Rationale: wave2a's HOLD was two
    DISAGREE rows on one byte that wave1 moved 14 seconds before 2a's
    apply; the retry's `includes_missing` had to carry a *decision* ("is
    `context/report.py` current?") because no field existed for it." (§6
    entry 216.)

130. **A "will create" forecast entry** — queued 2026-09-24 (code and
    docs; decide first; consumer S6). The report's Proposal 2, verbatim:
    "2. **"Will create" forecast entry.** Admit a nonexistent path at
    pack time so new-file sessions stop paying a prompt per path.
    Rationale: 2a and 2b paid two prompts each for files the brief
    itself said could not be forecast. Weigh against ADR-0015's
    existence rule; the entry should still be a forecast, not a grant."

131. **Hot reads in every include set** — queued 2026-09-24 (docs,
    PLANNER.md §6; consumer S6). The report's Proposal 3, verbatim: "3.
    **Hot reads in every include set.** A file the runtime reads
    (`pyproject.toml`, the parser behind a command) ships with every
    pack that exercises the runtime, disjointness or not — PLANNER.md
    §6's second clause, applied to runtime reads rather than imports.
    Rationale: waves 1 and 5 self-reported `pyproject.toml` missing and
    built stand-ins; wave3 self-reported `commands/ingest.py` missing
    and probed for `tally.py`. The design desk's packing caused more
    probe pressure than the environment did." The same class as §6 entry
    215's bale-src misses.

132. **Plain-language brief framing** — queued 2026-09-24 (docs, a
    PLANNER.md §3 rider as well; consumer S6). The report's Proposal 4,
    verbatim: "4. **Plain-language brief framing.** A brief that reads
    as adversarial ("hostile", "planted", "must stay ignorant") is
    refused by the worker surface's safety classifier before any worker
    sees it; state what the fixture is and why the operator is blind.
    Rationale: seed v1 sat 1 h 41 min from pack to abandon; v2, same
    design, reworded, landed in 46 min." The wording came from the 006
    desk's brief for the design sitting (§6 entry 218).

133. **Probe timing, two numbers** — queued 2026-09-24 (code; consumer
    S6). The report's Proposal 5, verbatim: "5. **Probe timing, two
    numbers.** Round trip (post to paste-back) is chat-clock time and
    measures the operator's attention as much as the environment; run
    time belongs in the probe's own paste-back trailer, self-stamped.
    Today a probe leaves no telemetry row at all — wave3's exists only
    in `judgment_calls` and notes — so bale should record the
    post/paste-back pair as a session attempt, and the probe skeleton
    should stamp its own start and end. Rationale: the only source for
    wave3's 2 minutes was the operator's memory." Against the records:
    wave3's applied attempt does carry `feedback.mechanical.linkage`
    (`kind: probe`, `point: pre-build`), so a probe's existence is
    recorded when the worker fills it; its timing is recorded nowhere,
    which is the row's point.

134. **A pack-time include warning** — queued 2026-10-06 (code; decide
    first: a static or a derived seed list; warnings only, never
    refusals). Close 20's first Proposal, made a row by the operator's
    "as assumed" to the cleanup desk's light block two, [3]; verbatim
    from `2026-10-05-sitting-close-deltas-20-001`'s notes.md, flattened:
    "**What:** a board row for a pack-time include warning: when an
    included suite's module imports or fixture reads (`bale.toml`,
    `claude/changelog/`, `claude/context/adr/`, the repo `README.md`)
    fall outside the request's includes, `bale pack` says so, never
    refuses. **Why:** §6 entry 223 is the class's fourth occurrence (215
    had two, row 131 one); every worker of this arc reported the same
    six or seven baseline failures from the same files, and C's record
    put them in `includes_missing`, so the signal was already in the
    telemetry before the cleanup desk repeated the miss. **Scope
    hints:** `bin/bale_pack.py`'s include gate and the
    `includes_missing` corpus as the seed list; a desk decision first on
    whether the list is static or derived from `tests/` imports." This
    is the remedy §6 entry 223 says "has no row yet". The ruling queued
    it after choice-prompt-convergence, which has applied
    (2026-10-06T19:07:41Z); unscheduled.

135. **`reconciliation_parsed: false` surfaced** — queued 2026-10-06
    (code; warnings only, never refusals). Close 20's second Proposal,
    same ruling; verbatim, flattened: "**What:** surface
    `reconciliation_parsed: false` at apply as a warning line beside the
    worker PASS, and in `bale stats`. **Why:** E's record passed with no
    claim paired to a verdict and nothing said so; the calibration
    signal the claims field exists for was lost silently, which is the
    silent-skip class. **Scope hints:** `bin/bale_apply.py` where the
    reconciliation is parsed, `bin/bale_stats.py`'s claim counts; one
    line each." E's record is the specimen (§3's 001-desk block of
    2026-10-05). Queued after choice-prompt-convergence, which has
    applied; unscheduled.

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
  [2026-09-20: the fifteen is a hand count: the records read 7
  disclosing of 206 reporting over 276 parseable records (37's notes.md,
  from `bale stats` on the shipped corpus; the 001 desk read 274, before
  two 2026-09-20 records landed), any-attempt and latest-carrier
  agreeing, all seven predating this ruling. No record carries
  `occurred: false` beside a `disclosure_ref`, so wherever the fifteen
  was counted, it was not in structured telemetry. Ruled at the
  `2026-09-20-continue-plan-006` desk by [3], ratified "as assumed", in
  its default's words:
  "yes, bracket it; nobody chases the other eight".
  The fifteen above stands, read as a hand count.]

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

New, ratified 2026-09-16 (the continue-plan-009 sitting; each a ruling
of record with one home):

- **A session kind is a declared start, switchable.** Every session
  is packed as one of `build`, `discussion`, `master`, or `context`;
  the four terminal shapes bind `build` alone; a discussion answers
  in chat and lands nothing unless asked. The architect switches a
  session's kind at will; a session switches itself at the named
  transitions (a worker at a split becomes a secondary master; a
  discussion at a solid point becomes a master or a build and
  declares its forecast then). Ratified 2026-09-16; lands at row 104.
- **The operator's voice carries the authority.** What makes the
  injected docs instructions is the operator saying so in the
  opener, typed in chat; no file claims precedence over the model's
  own guidelines, and the tools are named as conveniences over a
  doc that is the contract. Ratified 2026-09-16; lands at row 105.

New, ratified 2026-09-17 (the `2026-09-16-continue-plan-006` sitting;
each a ruling of record with one home):

- **Every version bump carries its changelog record.** Every
  `bin/VERSION` bump carries `claude/changelog/<version>.json`; a bump
  without one fails the suite by name. Landed at row 108, over row
  56's record family.
- **A `tools/` forecast ships the self-containment suite.** A forecast
  touching `tools/` ships `test_global_doc_selfcontainment` (the tools
  are injected surfaces), as `schemas/` already does (§6 entry 148).
- **A file named clean says how.** A brief that names a file as clean
  states how that was verified, or forecasts the file anyway (§6 entry
  148).
- **"Bumpless-under", defined.** A desk term, now defined: no
  `bin/VERSION` change and no version tag added or removed; the
  touched files' highest tag stays ≤ `bin/VERSION`. Two workers of
  this sitting flagged the term undefined and read it this way.
- **`board-<digits>` is a citation; a session id is lineage.** For the
  self-containment guard, `board-<digits>` is a board citation; a
  session id (`YYYY-MM-DD-` before `board-`) is lineage and stays
  tolerated. Landed at row 108.
- **The desk verifies a gate rule before writing its paste line.** The
  desk verifies gate rules against `bin/bale`'s own text before
  writing a line the operator will paste — three refusals this
  sitting, each correct: `--write` on a nonexistent path, a pack flag
  on the `open` line, superseding a held session (§6 entry 147).

New, ratified 2026-09-18 (the `2026-09-18-continue-plan-001` sitting;
each a ruling of record with one home):

- **The tool routes HOLD material.** When the checkpoint held (alone
  or with the worker), the planner block goes first and the worker
  block waits for the desk's ruling; when only the worker's validation
  held, the worker block goes first. The worker block carries the
  failed probe labels and the worker's own validation output, nothing
  else of the checkpoint's. Supersedes row 47's interim planner-first
  rule. Landed at row 47.
- **The relay markers are wire format.** The RELAY sentinels, the
  `send first:` line's leading bytes, and the three ruling words
  (`fixture defect`, `work defect`, `base defect`) are wire format.
  Landed at row 47.
- **A retry of held bytes re-states its admissions.** A retry of held
  bytes re-states every admission the held apply exercised; nothing
  carries forward from a failed attempt. Landed on the base-defect rung
  at row 47; the fixture rung is row 110.
- **The supersession stamp sweeps at its own event.** Two sweep commits
  per accepted supersession: the closure at the close, and the stamp
  once the child sid exists. Landed at row 107.

New, ratified 2026-09-19 (the unrecorded `2026-09-19-session-fix-002`
sitting and the `2026-09-19-continue-plan-006` sitting; each a ruling of
record with one home — the first three were ruled at the unrecorded
sitting and are known to the desk only as landed text; the fourth is the
006 sitting's):

- **What a session owes back follows from how it was packed.** A worker
  session (any write forecast) owes one response tarball; a planner
  session (read-only) owes its answer in chat and a crafter bundle per
  session it is asked to author — never a response tarball, not even an
  empty one. Homes: `docs/CLAUDE.md` §3 and `docs/TARBALL.md` §2, pinned
  byte-exact. Closes row 104's specimen (§6 entry 146) on the
  deliverable side. Landed at row 112.
- **A turn that needs something ends in a shape.** A probe block, a
  light question block, or a clarification response; a question asked as
  prose is not a shape; every other turn is ordinary prose. Homes:
  `docs/CLAUDE.md` §3 and `docs/TARBALL.md` §5.10; the retired
  "machine-recognizable shape" sentence is pinned absent. Landed at row
  112.
- **The manifest's `readme` key.** Top-level and additive: `null` when
  no README ships, otherwise exactly `{path: "README.md", sha256}`;
  `bale handoff` stamps `null`. And `resolved_scope: []` is the
  read-only stamp, with no qualifier (close 13's first block, 005's
  fourth check). Home: `docs/TARBALL.md` §3.2. Landed at row 112.
- **Held admissions are a stamp beside `held_tarball`.** Written at
  every HOLD, wiped at every retry, always written, strictly parsed;
  absence means pre-0.4.37 or never held. Completes 2026-09-18's "A
  retry of held bytes re-states its admissions" on the fixture rung.
  Home: BALE.md §8.8. Landed at row 110.

New, ratified 2026-09-20 (the `2026-09-20-continue-plan-004` and
`2026-09-20-continue-plan-006` desks, with the 001 desk's key names; each
a ruling of record with one home; recorded at close 15):

- **The context pack is `bale pack --context`.** A session-less tarball
  of a directory's tree, carrying no sid, no lock, no opener and no
  telemetry, and owing nothing back. It lands at
  `<dir>/.bale/outbox/context-<name>.tar.gz`, under the packed
  directory's own outbox even in a repo subdirectory.
  Goal-less `bale pack` stays the wizard. Ruled at the 004 desk ("as
  assumed, and both applied:"), the outbox at the 006 desk ([2]).
  Homes: `docs/TARBALL.md` §3.1 and §3.4, and BALE.md §7.8. Landed at
  row 104 (104a).
- **`bale stats` counts compaction disclosures.** Two counts,
  `cross_checks.budget.compaction.{reporting_sessions,occurred_sessions}`,
  and a sid bucket, `members.compaction_occurred`; a session discloses
  if any attempt's `feedback.self_reported.compaction_occurred` says it
  occurred. Counts, not a rate, rendered on their own line under the
  budget line. Home: `bin/bale_stats.py`'s docstring; 37 made no
  BALE.md edit (99b's input). Landed at row 37.

New, ratified 2026-09-20 (the `2026-09-20-continue-plan-009` desk, the
second as that desk ratified 104b's landing; each a ruling of record
with one home; recorded at close 16):

- **A failed oracle control exits 2.** A blind checkpoint whose control
  fails, the check that proves its own detectors work, exits 2; it does
  not exit 1, and it does not fail by name among the probes. Ruled at
  the 009 desk by the operator's "as assumed" to its light block one,
  [2], which closed a split between two desks: the 004 desk's control
  failed by name, and the 006 desk's exited 2. The desk's reason: bale
  reads exit 2 as a defective oracle at `bale open` and as the
  checkpoint side on the hold card, and TARBALL.md §7.5 gives 2 to "the
  script itself errored". Home: this section, until a `docs/PLANNER.md`
  holder carries it to §4 (the §3 registry's rider).
  [2026-09-21: carried to PLANNER.md §4 at
  `2026-09-21-split-transition-unconditional-007`, as the bullet "**A
  failed control exits 2.**"; that is its home now, and this contract is
  its record (the §3 registry's bracket).]
- **A pack records what it swept, and when it was packed.**
  `bale pack --json` carries two always-present keys, additive. `sweep`
  is a list, `[]` strictly when the pack closed nothing, with one entry
  per close or post-sid stamp the pack wrote onto another session's
  record: six keys, `sid, event, status, detail, sha, files`, where
  `event` is one of `superseded-by-split`, `closed-read-only`,
  `superseded_by` and `swept_by`, and entries run in event order, every
  pre-sid close before every post-sid stamp. Under `[apply] sweep` off
  an entry is kept and its four sweep keys nulled (`status`, `detail`
  and `sha` null, `files` `[]`), because the write it records did
  happen. `include_group` is null exactly when the human report prints
  no include-group row, and otherwise structured,
  `{name, state, triggers, pulled, row}`, `state` one of `engaged` and
  `opt-out`, `row` the human row verbatim. `packed_at`, the request
  manifest's `provenance.packed_at` verbatim, rides the `opened`
  attempt's copy of provenance only; the registry-side `provenance.json`
  stays the pair. `swept_by` names the sweeping pack on each closure a
  read-only sweep wrote, stamped after the sid is minted and committed
  as its own sweep event, `[bale sweep <swept>] swept_by <sid>`; absent,
  it reads as "sweeping pack unrecorded", and a supersession close
  carries `superseded_by` instead. The brief pinned `sid` plus four
  keys, and the six-key entry was ratified at the 009 desk as a floor
  met (ruling 4). Homes: BALE.md §7.7 and §8.9 and
  `schemas/telemetry-record.schema.json`, by 104b's notes.md. Landed at
  row 104 (104b).

New, ratified 2026-09-21 (the `2026-09-21-continue-plan-005` desk, by
the operator's "as assumed" to its light block three, [1]; a ruling of
record with three homes held as one; recorded at close 17):

- **The split is a role transition in every project.** The ruling's text
  is the block's own question row, verbatim: "Rule the finding's Q1 to
  Q4 as it recommends: the transition is owed in every project and a
  checkpoint only adds the children's oracles; the bare line stays the
  offer's content and the bundle is its delivery everywhere; section
  11.2 gains one clause pointing at PLANNER.md section 20.1's
  ratification hold; the worked example keeps its line and gains one
  sentence on the bundle?" What landed: CLAUDE.md §11.2 says the
  offering session delivers the rescope command "bundled, in every
  project", as the stored pack argv of a crafter bundle beside its
  `bale open` line, the bare line staying the offer's content, and its
  paragraph opening "The split is always a role transition" has the
  sub-master hold its decomposition for the parent's ratification before
  anything spawns (PLANNER.md §20.1). TARBALL.md §3.4 carries the
  paragraph "**The split is a role transition.**", stated "in every
  project", and the worked example's rescope line closes on a sentence
  saying the line travels "in every project" as the stored pack argv of
  a crafter bundle. PLANNER.md §20 names the children's checkpoints only
  "in a checkpoint-configured project" and opens its blindness sentence
  "Where a child has a checkpoint,". A checkpoint adds the children's
  oracles; it is not the condition of the transition. Homes:
  `docs/CLAUDE.md` §11.2, `docs/TARBALL.md` §3.4 and `docs/PLANNER.md`
  §20, held together by `tests/test_sanctioned_pairs.py`, whose
  `RetiredSplitConditions` class pins the three conditional openings
  absent (the fix's notes.md, decision 2). Why it was needed: a
  condition true as written was read as "only", in another project, the
  second report of one symptom; and the suite had pinned CLAUDE.md
  §11.2's bundling sentence in its conditional form, holding in place
  the wording row 79's ruling of 2026-09-14 was meant to replace (the
  finding's §6, by the fix's notes.md; §6 entry 202). Landed at
  `2026-09-21-split-transition-unconditional-007`, non-board (§3, the
  continue-plan-005 block).

New, ratified 2026-09-22 (the operator's ruling at the
`2026-09-22-continue-plan-001` desk, in that desk's rendering, carried
in its brief; confirmed at the `2026-09-22-continue-plan-005` desk by
his "as assumed" to its light block one, [1]; recorded at close 18):

- **Closes are per wave, not per master.** The contract's first sentence
  pair, byte-verbatim:
  Closes are per wave, not per master. A master's last job is the wave's close, after its project work is dispatched.
  A close waits until its wave has landed and, for an arc, until the
  sub-master's upward report is in; the 005 desk's block one asked
  exactly that and was answered "as assumed". Close 18 was the 005
  desk's last job, authored once the 100 wave and its report were in.
- **No master between a design sitting and its workers.** Byte-verbatim:
  More project work, less master grooming: an arc's design sitting authors its own wave's bundles once the operator ratifies the decomposition; no master sits between it and its workers.
  An arc's design sitting ratifies its own wave's notes.md and reports
  upward, one master per sitting, so the desk that authored a wave
  ratifies it (the 005 desk's block one, [2]). First application: the
  100 arc, `2026-09-23-board-100-design-001` authoring W1 to W3 and
  ratifying their notes.md (§3, its block; §6 entry 209). Home: this
  section, until a `docs/PLANNER.md` holder carries both sentences to
  §6's "Sitting practice" bullet on masters (the §3 registry's cadence
  rider).

New, ratified 2026-09-23 (the `2026-09-23-board-100-design-001` desk,
the 100 arc's design sitting and the 004 sitting's successor, by the
operator's "as assumed" to its four light blocks; the rulings verbatim
from `implementation-decomposition-revA.md`, one line each, as close
18's brief carries them; recorded at close 18):

- **Ruling 1.** Landed at W1 (`2026-09-23-board-100-w1-doc-sweep-002`),
  the noun sweep; W1 engraved the rule in TARBALL.md §1 (ratified at the
  design sitting).
  1. Noun: "the agent"; per-hat nouns where a sentence means one hat; "I/me" stays.
- **Ruling 2.** Landed at W3
  (`2026-09-23-board-100-w3-file-rename-004`), `docs/CLAUDE.md` to
  `docs/AGENT.md`; layer 4's key, `[layout] agent_dir`, landed at W2
  under ruling 8's spelling.
  2. Depth: layers 1-3 now (CLAUDE.md -> AGENT.md); 4 as a config key only, defaulting to "claude", renaming no existing repo.
- **Ruling 3.** Landed at W3, `validate.sh` refusing a leftover
  `docs/CLAUDE.md`; the alias and the `contract_docs` `oneOf` it keeps
  for good landed at W2.
  3. Compatibility: no window; enum alias and old contract_docs key set for good; validate.sh refuses a leftover docs/CLAUDE.md.
- **Ruling 4.** Landed at W1 in the docs and at W2 as the
  `model_identity` pattern in the schema (row 116).
  4. model_identity: `<vendor>:<model>`, lowercase, spaces->hyphens, `unknown` model token, no suffix; description + regex in response-manifest.schema.json; the telemetry schema's spelling-consolidation rider retires. includes_missing covers decisions (a path, or a line opening `decision:`); array unchanged. linkage.depends_on: null for a same-session round — a doc pin of the schema's own sentence (response-manifest.schema.json:224), no schema change.
- **Ruling 5.** Landed at W1, at both sites (row 118).
  5. "Validate before apply, always" rewords at both sites to: land only through `bale apply`, which validates and stages before it merges; never hand-apply a tarball or bypass a HOLD. Row type stays operator discipline.
- **Ruling 6.** Landed at W1, the PLANNER.md §6 bullet; the mechanized
  count is a registry entry, unscheduled.
  6. Light-block trail: a master self-report in the sitting-close notes (PLANNER.md §6 bullet: count, disposition per block); `light_blocks` stays the worker's field.
- **Ruling 7.** Landed at W1: AGENT.md §11.7, "Surface notes", one row,
  claude.ai.
  7. Surface notes: CLAUDE.md §11.1 keeps its four surface-agnostic rules; the claude.ai specifics (:516, :527-532, :641-643) move to §11.7 "Surface notes" past the core banner, a table keyed by surface, one row today.
- **Ruling 8.** Landed in part at W2 (`agent-decides` admitted,
  `[layout] agent_dir`, `CARRIED_TOOLS`) and at W3, the default flipped
  to `agent-decides` with the argparse order kept.
  8. Spellings: enum `agent-decides`; `[layout] agent_dir = "claude"`; `INJECTED_TOOLS` -> `CARRIED_TOOLS` (worker may deviate, flagged).
- **Ruling 9.** The operator's to do: `claude/context/board-100-arc/`,
  not on the tree at the close-18 probe.
  9. Archive: this directory, committed directly by the operator as carried artifacts.

New, ratified 2026-09-23/24 (the operator's "as assumed" to the
`2026-09-23-continue-plan-006` desk's four light blocks, in that desk's
rendering, carried in close 19's brief; recorded at close 19):

- **Close 18, ratified.** Calls 1 to 4 and 6 to 10 as made; call 5 as
  the worker's alternative, item 2's interim doctrine as a one-line
  rider for the next `docs/PLANNER.md` holder, since paired with row
  122's Proposal 2; Proposal 1 as a PLANNER.md §3 rider; Proposal 2 as
  close practice from close 19 on. Block one, [2]; the riders are §3
  registry entries.
- **A close proves its insertions by reversal.** From close 19 on, a
  close's `validation.sh` removes its declared additions, restores any
  line it edited in place, and hashes the result to the request's
  `provenance.base_files` sha256 for `claude/MASTER.md`: one exact check
  that nothing outside the additions moved. Close 18's Proposal 2; close
  19 is its first practice (its notes.md).
- **Closes are per wave**, confirmed: close 19 is the 006 desk's last
  job (the 2026-09-22 block). Block one, [1].
- **The micro's cut.** It carries its three riders, drops the dossier
  colon, and bumps to 0.4.44. Block one, [3].
- **Row 45's mechanism.** The desk designs the messy codebase and a seed
  session builds it, replacing the 006 desk's first mechanism, a context
  tarball of a repo the operator would bring; the bundle already
  delivered was replaced before it opened. The re-derivation block.
- **An arc in another repo reaches bale-src as carried artifacts.** Its
  upward report is committed under `claude/context/board-45-arc/`, and
  its repo travels as a `bale pack --context` snapshot beside the
  close's request, read and cited by sid and changed nowhere. Block two,
  [1].
- **An arc report's Proposals are filed, not held whole.** Each becomes
  a board row and a registry entry naming its consumer, S6 for the 45
  arc; the worker Proposals the arc parked stay held until S6, by the
  arc close's own decision. Block two, [2].
- **Gaps are filled by probe, not memory.** Block two, [3]. Close 19's
  own gap, the stemwell snapshot missing from its chat, took one probe
  (its notes.md).

New, ratified 2026-10-03 (the operator's "as assumed" to the
`2026-10-03-friction-points-001` desk's one light block, verbatim as the
wave2-004 desk's brief carries it, rows joined by " / "; recorded at
close 20):

- **The clipboard key is per-machine, global layer with project
  override.** Ruling [1]. Reverses the project-layer-only consumption of
  2026-09-16 (the registry's config-side carrier entry), whose reason
  was the crafter's reach; the reason gave way because bale itself does
  the copy. Landed at C, `2026-10-03-wizard-defaults-006`: `[probe]
  clipboard_command` inherited per key through `merged_config`, walked
  by the global wizard, overridden or suppressed (`""`, the wizard's
  `x`) at the project, read by `effective_clipboard_command(repo)`;
  spelling unchanged, the crafter still reading the project file for the
  no-bale fallback.
- **Bale copies every operator-side paste block when a command is
  configured.** Ruling [2]: automatically, with a one-line notice, and a
  failed copy never fails the command. Landed at D,
  `2026-10-04-clipboard-paste-blocks-001`: pack's opener (and `bale
  open`'s, both desks), relay's exchange block, apply's and retry's HOLD
  block named under `send first:` and their APPLIED block, and the probe
  through `bale clipboard`, one helper (`bale_report.copy_paste_block`),
  one 10 s timeout, one `[bale] clipboard:` notice on stderr, exits and
  stdout unchanged; piped and `--json` runs copy too (D's call,
  ratified). With no command configured nothing changes and nothing is
  detected at run time. The 2026-08-18 configurable-never-core contract
  stands beneath it: copying only when configured, detection a wizard
  suggestion, never runtime behavior.
- **Every request carries `BALE_HELP.md`.** Ruling [3]. Landed at E,
  `2026-10-03-bale-cli-reference-003`: the installed bale's `bale help`
  for every verb, generated at build time inside
  `build_request_tarball`, so it cannot drift from the bale that packed;
  routed from AGENT.md's META paragraph and an INDEX row and TARBALL.md
  §3.1. The reachability model gains a file beside the five docs and two
  tools; context packs carry none. A worker in any project reads a
  verb's syntax instead of probing for `bale --help`.
- The block, verbatim: "[1] question: Should the clipboard command
  become a per-machine setting (global layer, project may override)
  instead of project-only? / while doing: planning the sessions that put
  every paste block on the clipboard / would assume: yes: bale itself
  does the copy, so a probe in any project copies without the request
  shipping bale.toml / why blocked: it reverses the project-layer-only
  ruling on [probe] clipboard_command, whose reason was the crafter's
  reach / [2] question: With a clipboard command configured, should bale
  copy every operator-side paste block automatically? / while doing:
  choosing copy behavior for pack's opener, relay's exchange block,
  apply's HOLD relay blocks, and probe output / would assume: yes,
  automatically, with a one-line notice; a failed copy never fails the
  command / why blocked: automatic copying overwrites your clipboard on
  every pack, relay, and HOLD / [3] question: Should pack carry the
  installed bale's generated help (bale help for every verb) into each
  request as the project-facing reference? / while doing: planning the
  session that stops other projects' workers probing for bale --help /
  would assume: yes: a generated, request-carried reference that cannot
  drift, routed to from AGENT.md and TARBALL.md INDEX rows / why
  blocked: it adds a carried file beside the five docs and two tools,
  changing the reachability model"

New, ratified 2026-10-03/04 (the operator's "as assumed" to the
`2026-10-03-friction-points-wave2-004` desk's two light blocks, in that
desk's rendering, carried in the cleanup desk's brief; recorded at close
20):

- **Enter keeps today's meaning on a key with alternatives.** Block one,
  in the desk's words: "On a key with alternatives, Enter keeps today's
  meaning. The detected value is listed first, marked, and its number
  takes it. An Enter-through run writes nothing the operator didn't
  choose. (C built this.)" Landed at C; B's slug default, Enter taking a
  slug derived from the goal where it used to re-prompt, is the one
  Enter whose meaning moved, sanctioned by B's brief and ratified.
- **The sweep's y/N wraps to 80 columns, width only.** Block two, [1]:
  no change to what an answer means (unknown answers decline, nothing
  re-asks), so it never moves onto the layer's `confirm`, which re-asks;
  it rides the log-hold session.
- **The log hold is its own micro-session after D.** Block two, [2]: B's
  `WalkLogHold` is interim, the native hold in `bin/bale`'s `log()` runs
  as `2026-10-04-log-hold` after D lands, together with the wide
  pre-walk log lines and [1]; D stays clipboard-only. Dispatched so by
  the cleanup desk; applied by the brief's word; recorded by the next
  close.
- Block two, verbatim: "[1] question: Wrap the read-only sweep's y/N
  prompt to 80 columns, keeping its answers exactly (unknown answers
  decline, nothing re-asks)? / while doing: routing session B's
  Proposals after its apply / would assume: yes: width only, no change
  to what an answer means, and it rides the log-hold session in [2] /
  why blocked: your scope reading left the yes/no prompts out, and
  moving it onto the layer's confirm would change what an answer means /
  [2] question: Run the bin/bale log hold (retiring B's WalkLogHold) as
  its own micro-session after D, rather than folding it into D? / while
  doing: sequencing the follow-ups to this arc / would assume: yes: its
  own micro-session after D lands, together with the wide pre-walk log
  lines and [1]; D stays clipboard-only / why blocked: D also touches
  bin/bale and bale_pack.py, so the two must run one after the other,
  and folding them together would make D bigger"

New, ratified by 2026-10-06 (the operator's "as assumed" to the
`2026-10-04-friction-points-cleanup-002` desk's light blocks two and
four, in that desk's rendering, verbatim as the close desk's brief
carries them, rows joined by " / "; block two answered after close 20
applied, 2026-10-05T01:03:02Z, and block four after convergence applied,
2026-10-06T19:07:41Z, the records giving no closer date; blocks one and
three went unanswered and were replaced by two and four; recorded at
close 21):

- **Close 20's two Proposals are board rows, warnings only, never
  refusals.** Block two, [3]: a pack-time include warning for reads a
  shipped suite needs (row 134, the remedy §6 entry 223 said had no row)
  and `reconciliation_parsed: false` surfaced at apply and in `bale
  stats` (row 135). Each adds a warning surface to bale, which is a
  scope decision; both queued after choice-prompt-convergence, which has
  applied.
- **The arc's changelog catch-up is its own version bump.** Block four,
  [2]: `bin/VERSION` plus `claude/changelog/0.4.46.json`, authored by
  the successor desk beside close 21, because CODE.md §8.5 puts the
  entry in the changing session, the arc's sessions skipped it, and
  catching up mints a version. Dispatched by the close desk as
  `2026-10-06-bump-0-4-46`, whose brief asks for rows for all eight
  sessions of the arc that changed bale's code where the block named
  four, the close desk's read, flagged to the operator (§3's close-desk
  block). §6 entry 224 is the defect.
- The rest land where they belong: block two, [1] and block four, [1],
  the ratifications, in §3's wave block of this date; block two, [2] and
  block four, [3], the routings, in the ruling queue and the registry.
- Block two, verbatim: "[1] question: Ratify as shipped every flagged
  decision of log-hold-003 (five) and sitting-close-deltas-20-001
  (seven), keeping close 20's extra section 7 bullet? / while doing:
  reviewing the log-hold and close-20 ratification relays / would
  assume: yes: all twelve as shipped, recorded at close 21 / why
  blocked: ratifying a worker's flagged decisions is yours; log-hold
  narrowed the wrap to pack's pre-walk lines, and close 20 asked about
  the section 7 bullet / [2] question: File log-hold's two wrap
  Proposals as a ruling-queue entry (every verb's [bale] lines) and a
  registry rider (the supersession, drift-admission and bare-apply y/N
  prompts)? / while doing: routing log-hold-003's Proposals / would
  assume: yes: the every-verb wrap waits on a ruling because it breaks
  18 pty assertions; the y/N keyword is layout only and rides the next
  session touching bale_pack.py and bale_apply.py / why blocked: your
  ruling covered only the sweep's prompt, and wrapping every verb
  changes all terminal output / [3] question: Make close 20's two
  Proposals board rows: a pack-time include warning for reads a shipped
  suite needs, and surfacing reconciliation_parsed false at apply and in
  stats? / while doing: routing sitting-close-deltas-20-001's Proposals
  / would assume: yes: two board rows, warnings only, never refusals;
  queued after choice-prompt-convergence / why blocked: each adds a new
  warning surface to bale, which is a scope decision"
- Block four, verbatim: "[1] question: Ratify as shipped
  clipboard-key-rename-002's eight decisions and
  choice-prompt-convergence-001's seven, including convergence moving
  pack's per-path filter chain into pack_drop_reason? / while doing:
  reviewing the rename and convergence ratification relays / would
  assume: yes: all fifteen as shipped, recorded at close 21 / why
  blocked: ratifying a worker's flagged decisions is yours, and the
  filter-chain refactor runs inside every pack / [2] question: Author a
  version-bump micro-session (0.4.46) beside close 21, writing the
  changelog record for the arc's surface changes (C, D, log-hold, the
  rename)? / while doing: routing clipboard-key-rename-002's changelog
  Proposal (light block 3, unanswered, folded in here) / would assume:
  yes: bin/VERSION plus claude/changelog/0.4.46.json, authored by the
  successor desk beside close 21 / why blocked: CODE.md 8.5 puts the
  entry in the changing session, the arc's sessions skipped it, and
  catching up mints a version / [3] question: File convergence's
  remaining Proposals: dropping two picker exceptions and moving the
  .baleignore add prompt onto ask_choice as ruling-queue entries, and
  PackWalk as a Walk configuration as a registry rider? / while doing:
  routing choice-prompt-convergence-001's Proposals / would assume: yes:
  the first two change what an answer or a frozen prompt says, so they
  wait on rulings; the Walk refactor changes nothing visible / why
  blocked: dropping the picker exceptions reverses this desk's pin, and
  the add prompt's text was frozen by the convergence constraint"

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
    [2026-09-23: specimens two and three at the
    `2026-09-22-continue-plan-001` desk, caught before delivery (entry
    207); and the obverse at W3, a probe its desk could not rehearse end
    to end, reaching apply as a hold (entry 210).]

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

141. **Four beside the desk, twice.** Eight sessions in two waves of
    four, every forecast disjoint by the gate's own judgment, one
    bumper per wave and two or three bumpless-unders beside it; every
    pack forecast named suites rather than `tests` and the gate
    admitted all eight beside each other. The tests-forecast rule
    (entry 140) needed its concurrency clause the first time it met
    concurrency (§7). The operator's paste load at four was
    unremarkable.

142. **Absence is not a drop.** The desk rehearsed row 92's "today"
    line, saw no verbose line for an untracked file, and wrote a
    drop into the brief and the oracle; the file ships. Rehearsal
    observed the right output and drew the wrong inference from an
    absence. The worker's light block ("the brief's example actually
    ships today") caught it before the apply — the first time the
    tier paid for a fixture defect rather than a work one — and the
    desk amended (v2) under the bad-oracle protocol with the first
    apply on `--accept-checkpoint-change`. Then the worker's own two
    defects HELD on the amended oracle; the retry landed.

143. **A validation invariant under target-base staging is stated
    relative to the response, never as a literal from the request
    tree.** 99a's validation.sh asserted `bin/VERSION == 0.4.33`
    read off the request; staging carried the sibling bumper's
    `0.4.34`. The corrected check asserts "declares no `bin/VERSION`
    change". Concurrency makes every request-tree literal a stale
    guess (§7).

144. **The card paid for itself the same hour.** 99a's first HOLD
    rendered 47a's card — judge line, failed probes, the
    ruling-keyed next step — because 47a had merged minutes before;
    99a's worker read its own ruling off the card and proposed the
    README re-true. One-apply-behind cut the other way: 47a's own
    HOLD, had it happened, would have shown the old card.

145. **An outside review.** Run against another model, the framework
    was declined on four grounds, quoted from the transcript in
    substance: a file in an upload claiming to win over the model's
    own instructions is indistinguishable from an injection; "a
    question asked as prose is not a shape" reads as a prose ban;
    two opaque 100 KB / 75 KB tools presented as required were not
    run sight-unseen; 250 KB of contract around a two-paragraph seed
    is a mismatch worth noticing. Three are wording, one is
    proportionality; none is model-specific. Rows 105 and 104
    answer them in that order; the transcript is a rarer and more
    useful specimen than a HOLD.

146. **The shape rule wins by silence.** On another project a
    read-only discussion returned an empty-`changes[]` tarball with
    the discussion in notes.md. The worker's reasoning was sound on
    the docs as written: nothing carves out a discussion, and
    "read-only lands nothing" reads as "lands no changes". Silence
    is a rule; row 104 names the kinds.

147. **Gate refusals on desk assumptions.** Three times this sitting a
    `bin/bale` gate refused a line the desk wrote for the operator to
    paste, three different kinds, and each refusal was correct:
    `--write` on a nonexistent path, a pack flag on the `open` line,
    and superseding a held session. The desk wrote from its model of
    the gates rather than from `bin/bale`'s text; the gates did the
    check the desk skipped, one paste later. The 2026-09-17 contract
    moves the check ahead of the paste (§5). (Desk-side, this
    sitting.)

148. **The include-miss chain.** Row 69's brief did not forecast
    `test_global_doc_selfcontainment`, though the tools are injected
    surfaces; 56+57 then HELD on that suite — a base defect, not its
    work. The fix, `2026-09-17-board-69-selfcontainment-fix-004`, was
    briefed on the desk's unverified "crafter is clean", forecast only
    the lint, and HELD in turn; it closed superseded-by-split by
    `2026-09-17-board-69-selfcontainment-fix-both-005`, which landed
    both tools, and 56+57 retried unchanged and landed. 56+57's worker
    had already diagnosed the base drift in its own `validation.sh`
    and SKIPped the tools-only failures by name before the desk ruled.
    Two contracts follow (§5): a `tools/` forecast ships the guard,
    and a file named clean says how it was verified. (Desk-side, this
    sitting; the diagnosis worker-side, 56+57.)

149. **Worker light blocks, four.** Four this sitting — 69, the stats
    micro, 56+57, 106 — all non-blocking, all answered from the desk,
    every default ratified. One was mis-shaped and self-admitted
    (56+57). One diagnosed a blind fixture from the brief text alone
    (106), the question the desk's fixture ruling answered.
    (Worker-side, this sitting.)

150. **Desk file-map errors and their cost.** At the open the desk
    serialized 106 behind 47b; 106 touches neither `bin/bale_apply.py`
    nor `bin/bale_report.py`, and it lost a turn before the correction
    put it beside 56+57. "Different regions of one file" is not a
    forecast: the gate reads paths, and the desk's file map has to
    read them the same way. (Desk-side, this sitting.)

151. **The HOLD card's missing third category.** 47a's card offers two
    next-step categories, fixture defect and work defect. The sitting
    hit a third twice — a base defect, neither fixture nor work (entry
    148) — and the card had no line for it. Input to 47b's brief (row
    47). (Desk-side, this sitting.)

152. **Rehearsal counts.** Fixture defects caught before delivery:
    105: 1, 69: 2, the stats micro: 1, 106: 3, the fix: 1. Escaped:
    106's quote character (a rendering detail), and the fix's crafter
    guess — not rehearsable, because it was a fact about the tree, not
    a behavior (entry 148). (Desk-side, this sitting.)

153. **"As assued."** The desk's answer to the stats micro's light
    block carried a typo, "as assued"; the worker read it as "as
    assumed", ratified all three defaults, and named the reading as an
    assumption in its self-report. The typo was the desk's; the
    reading was correct and said so. (Worker-side, the stats micro.)

154. **Sids date from bale's clock.** The desk's briefs carried a
    stale date until they moved to the `<UTC-date>` form. The sid is
    minted on bale's UTC clock at open, and this sitting straddled UTC
    midnight (opened 2026-09-16T22:17Z; sids after ~00:00Z carry
    09-17), so a date typed from the desk's own day goes stale at UTC
    midnight. (Desk-side, this sitting.)

155. **Collisions found at the desk, not the gate.** Wave 4's two file
    collisions — `tests/test_apply_preflight.py` under 47b and 109, and
    the pack-json rider across 47b's and 107's files — were found by
    the file map at the open, before any bundle, and cut there (§3).
    Entry 150's lesson applied before dispatch. (Desk-side, this
    sitting.)

156. **The row's oracle sentence was one inference off.** Row 107 said
    the tree would be clean; rehearsal showed every pack leaves its own
    `opened` record untracked until its session closes, so the oracle
    graded "no tracked file modified" and "the committed record carries
    `superseded_by`". Entry 142's class, caught by reproducing before
    writing the oracle. (Desk-side, this sitting.)

157. **A rider that no longer reproduced.** The registry entry's
    log-order evidence was a reporting artifact; 107's worker said so
    rather than fixing a non-defect, and marked its inference as
    inference. (Worker-side, 107.)

158. **A sentence verified by fragments.** 109's brief said §5.10
    "carries the sentence today"; the desk had matched three fragments
    of the second half, and the first half differs from CLAUDE.md's.
    The worker pinned §5.10's own wording; the oracle, mutation-shaped
    on the second half only, did not HOLD. A claim about a sentence is
    checked whole. (Desk-side claim, worker-side catch.)

159. **The desk read the writer, not the artifact.** 47b's brief
    called the log's worker band "the worker's own script's output"
    from the write sites in `bin/bale_staging.py`; a real log shows
    apply journaling the checkpoint's exit line, path included, inside
    that band. The worker built the block from in-memory output and
    gave the function no parameter that could carry checkpoint output.
    (Desk-side claim, worker-side catch.)

160. **Thin pins, two outcomes.** 109's oracle accepted attribute or
    mapping access for the loader's return, and the worker's different,
    better mechanism landed without a HOLD. 47b's verbatim `send first:`
    bytes ruled out an aligned card row, because rows pad labels — a
    verbatim marker constrains layout, and the desk did not know the
    renderer's padding when it pinned the bytes. (Desk-side, this
    sitting.)

161. **A habit that contradicted a rule for weeks.** The operator's
    HOLD routine — card plus the whole session log, to the worker
    first — ran against row 47's interim planner-first rule and handed
    workers the checkpoint band; neither side noticed until the
    operator described the routine while asking for it to be
    automated. Rules the tool does not carry are not carried. Row 47
    now carries it. (Desk-side, this sitting.)

162. **The fixture rung's latent gap.** Found by 47b's worker while
    answering the brief's question about the base rung's flags. Row
    110. (Worker-side, 47b.)

163. **A tool-use pause at the open.** The master's first turn hit the
    tool-use limit before any bundle; it named the pause as a pause
    (CLAUDE.md §11.1), ended on a hand-authored light block, and
    resumed with context intact. (Desk-side, this sitting.)

164. **A sitting with no close and no brief.** The 002 sitting landed
    two sessions and left MASTER.md untouched; what the next desk could
    rebuild was exactly what the tool had recorded — telemetry and two
    notes.md — and nothing of its chat. (Desk-side, the 002 sitting;
    reconstruction at the 006 and 009 desks.)

165. **A split three minutes after open.** 003 opened 01:23:39Z and
    closed `superseded-by-split` at 01:26:54Z, its forecast the exact
    union of its two children's. The first child, 004, opened at
    01:36:19Z, nine and a half minutes after the parent closed; the
    records do not say why. (From the records.)

166. **The rider's pin was in `tests/`.** 110's brief verified where
    rider 2's "at v0.1" marker lives and never grepped `tests/` for a
    pin on it; `tests/test_pack_guards.py` pinned it verbatim, and the
    cost was one prompt admission. A rider that changes emitted text is
    verified with a grep of `tests/` for that text, and the pinning
    suite joins the forecast. (Desk-side, the 006 sitting.)

167. **A shared file cut with a holder and a droppable rider.** Both
    rows wanted `tests/test_apply_preflight.py`; 110 held it and carried
    the class move as a droppable last rider, and it landed ("Done, not
    dropped"). Entry 155's practice with one more tool. (Desk-side, the
    006 sitting.)

168. **A forecast file left untouched, with reasons.** 111 forecast
    `tests/test_sanctioned_pairs.py` on the desk's guess at the relay
    pin's home; the worker put the pin in `test_doc_crossrefs.py` (the
    pin is doc↔code, and the other suite is DOCS.md §9's doc↔doc
    enumeration) and said so. (Worker-side, 111.)

169. **Two light-block answers crossed a sitting boundary.** Unanswered
    at the 006 sitting's end, carried in its brief under "Silence is not
    'as assumed'", answered in four words in the message that opened the
    next master. (Desk-side, the 006 and 009 sittings.)

170. **A pause named as a pause, worker-side.** 004's turn was split by
    a tool-use pause mid-build; its notes.md names it a pause, not a
    compaction, and says every hash and claim was recomputed after it.
    Entry 163's class, second specimen. (Worker-side, 004.)

171. **A registry close checked against the tree alone.** Close 13's
    brief closed the `_section_29` renames entry "as stale" on three
    desks' greps of the tree; the neighbouring registry entry already
    carried a 2026-09-16 bracket recording the renames as consumed.
    Three desks grepped the tree and none read the registry around the
    entry. A registry close is checked against the registry, not only
    against the tree. (Desk-side, the 006 and 009 sittings; caught
    worker-side, close 13's item 7.)

172. **Measure before cutting.** Row 113 was written as a sweep across
    fifty-odd files. The desk measured first: 56 of 68 suites failed
    the dotted run form, and a four-line `tests/__init__.py` fixed all
    of them, so the row ran as a one-new-file session beside the close
    that wrote it, with no hot-file collision. The brief offered the
    experiment as a measurement, not as the mechanism, and the worker
    verified what the desk had not (full discovery, every suite dotted
    in one process, the harness loaders). A row whose unit is a guess
    is measured before it is cut; the measurement can change the unit
    from a sweep to one file. (Desk-side, the 009 sitting; worker-side,
    113.)

173. **A bundle written but not yet presentable at a pause.** The 009
    desk's first tool-use pause fell after close 13's bundle was written
    and before it could be presented. The desk named the pause, asked
    the operator not to open the bundle until the gate check had run,
    and ran the check first thing on resume. A bundle caught between
    its write and its gate is not delivered, and the desk says so at
    the pause. Entry 163's class, with more specimens the same sitting:
    the desk's second pause, and close 13's worker's own. (Desk-side,
    the 009 sitting.)
    [2026-09-21: two more, at close 17, each a bundle built and
    dress-rehearsed and not yet copied out when the tool-use limit fell:
    close 16's revision 1 at the `2026-09-21-continue-plan-002` desk's
    turn one, and the doc lane at the `2026-09-21-continue-plan-005`
    desk's turn one. Each desk said the bundle was built and not
    delivered, and used the pause to put its calls to the operator in a
    light block before delivery rather than after. Beside them the
    `2026-09-21-continue-plan-008` desk built nothing ahead of its
    block, as TARBALL.md §5.10's "The worker does not idle" asks.
    (Desk-side, the 002, 005 and 008 sittings.)]

174. **The records do not name the pack that swept a master.** The
    closing attempts of the 002, 006 and 009 masters are each a `pack`
    reading `closed-read-only`, and none names the closing pack. Each
    close has attributed the sweep by a desk's account: 009's closing
    attempt and the 001 desk's own `packed_at` share the second
    2026-09-20T00:17:07Z, which that desk can see and this close cannot.
    Close 13's Proposal 2 is the remedy (§3 registry, riding row 104);
    until it lands, a sweep is attributed only as a desk's account.
    (From the records.)
    [2026-09-20: the remedy landed at 104b as `swept_by` (0.4.40), and
    the next close read it: entry 194.]

175. **A light block unanswered behind an "applied:" paste.** The 009
    desk's light block went out with two questions; the operator's next
    message was the two ratification relays, pasted with "applied:",
    and no reply to the block. The apply report and the block reply are
    two answers, and the second got lost behind the first. The desk
    read the silence as silence, not "as assumed" (entry 169), and
    re-emitted the block with a third question; all three were replied
    to. Its first question then went unanswered twice more, at the
    sitting's end and beside the next master's open paste, and was
    answered only after the 001 desk explained the row again at a
    tool-use pause. A desk that emits a block and gets an apply report
    back re-asks the block. (Desk-side, the 009 sitting and the 001
    desk.)

176. **Close responses whose claims went unreconciled.** Close 13's
    apply attempt reads `reconciliation_parsed: false` and an empty
    `claim_verdict` beside twelve `claims`, and close 11's two attempts
    read the same; close 12's parsed, twelve pairs, and so did 113's in
    the same wave as close 13. Closes 6 to 10 parsed too, by the 001
    desk's read of records this close cannot see. Both unreconciled
    closes landed on a PASS in the end, so what was lost was the
    calibration signal, not the landing. Close 13's rehearsal printed every claim agreeing, and its
    notes.md says it did not run the crafter; close 12's `docs_read`
    lists the crafter. The records do not say why the two did not
    parse. A worker's own rehearsal printing a claims block is not
    evidence that apply parses it; the epilogue comes from
    `tools/craft_response.py --validation-epilogue` (TARBALL.md §7.3).
    (Worker-side, closes 11 and 13; found from the records at the 001
    desk.)
    [2026-09-20: close 14 parsed: its ten claims reconciled at apply
    (`reconciliation_parsed: true`, ten `agree`), and its reconciliation
    block was the crafter's emission pasted unchanged, per its notes.md.
    37 (nine claims, on its held and its applied attempt) and 104a
    (eleven) parsed too. One more data point for the crafter reading,
    not a cause. Close 15's epilogue is the crafter's too.]

177. **A derive instruction pointing at bytes that never travel.** The
    009 brief told the 001 desk to derive close 14's brief and
    checkpoint from close 13's: "Derive both; do not rewrite." Neither
    reaches a master: packs withhold checkpoint bytes, and request briefs
    are archived nowhere. The desk authored both fresh from close 13's
    landed block, its notes.md and the 009 brief's description of the
    oracle, and described its own shapes for the next desk for that
    reason. A second specimen at close 15: its brief asks the 001 block's
    sequencing to quote the 001 desk's standing line, and quotes that
    desk's brief only over a range that does not hold it. An instruction
    to derive or to quote is only as good as the bytes that travel with
    it. (Desk-side, the 009 and 001 sittings; the 006 desk's brief to
    close 15.)

178. **A ruling between a bundle's write and its presentation.** The
    001 desk's first turn wrote close 14's bundle and hit the tool-use
    limit before it could present it; the operator's next message ruled
    row 104, which made the written brief false in one place. The desk
    derived the revision from the brief's own bytes, re-derived the
    row-104 probe, re-ran every rehearsal and rebuilt the bundle before
    presenting it. The pause cost nothing because nothing had been
    delivered. PLANNER.md §4's last bullet, exercised: an oracle
    authored before a ruling is re-verified against every ruling made
    after it. Entry 173's class, seen from the ruling's side.
    (Desk-side, the 001 sitting.)

179. **A question answered first time.** Row 104's [1] went unanswered
    through two light blocks and a chat explanation (entry 175). The 001
    desk explained it again at a tool-use pause, in four sentences that
    led with what the operator already does by hand, and the operator's
    next message was the answer. The 004 desk's block then held one
    question, alone, leading with what the command does today, and was
    answered first time with no pause. The 006 desk's block held three
    questions and was answered first time too, "as assumed", at a named
    pause; so the count alone is not the variable, and the records do
    not say what is. (Desk-side, the 001, 004 and 006 sittings; two
    candidates merged at close 15.)
    [2026-09-20: three more blocks, at close 16. The 006 desk's, already
    counted above, went out at a pause with nothing built: the desk said
    no bundle was ready and used the pause to ask, the plain case beside
    entry 173's. The 009 desk's two, three questions and two, were each
    answered first time, neither at a pause; the second reply made one
    inline change and closed "Otherwise, as assumed", the mixed reply
    TARBALL.md §5.10 draws, and that block followed an "applied:" paste
    where entry 175's preceded one. The 006 desk's record calls its own
    the third sitting running answered first time at a pause; by this
    entry the 004 desk's block had no pause, so the run is of first-time
    answers, not of pauses. Four blocks running, with one question and
    with three, at a pause and away from one; the records still do not
    say what the variable is. (Desk-side, the 006 and 009 sittings; two
    candidates merged at close 16.)]
    [2026-09-21: nine more blocks at close 17. The
    `2026-09-21-continue-plan-002` desk's four were each answered first
    time, block three's [1] with a question that the desk did not read
    as an answer (entry 197). The `2026-09-21-continue-plan-005` desk's
    first, third and fourth were answered first time, "as assumed" each
    time; its second was not answered at all, the operator's next
    message bringing a new issue instead. The
    `2026-09-21-continue-plan-008` desk's one block was answered first
    time. Eight of nine, and the one miss was a block the next message
    stepped over. (Desk-side, the 002, 005 and 008 sittings.)]

180. **Oracle detail kept off verdict lines.** The 001 desk's two
    oracles and the 004 desk's print the label alone on a verdict line
    and any detail on a following `  detail:` line, because labels
    travel to the worker on a HOLD and detail would carry oracle strings
    with them. 37's HOLD exercised it: the worker got one label,
    "PLANNER.md §5 step 5: the retry clause mentions the held apply's
    admissions", and fixed the clause from it without seeing the probe.
    (Desk-side, the 001 and 004 sittings; exercised at 37.)

181. **A hand count in a ruling of record.** §5's calibration ruling
    says fifteen compaction disclosures on 181 records. The 001 desk's
    throwaway script found seven on 274 records, and 37's shipped read
    side seven of 206 reporting on 276; no record carries
    `occurred: false` beside a `disclosure_ref`, so the fifteen was not
    counted in structured telemetry. Ruled at the 006 desk ([3]): the
    number stands, bracketed as a hand count, and nobody chases the
    other eight. A number in a ruling of record says where it was
    counted. (From the records, at the 001 desk and 37; ruled at the 006
    desk.)

182. **A master packed ten seconds after its wave.** The 004 master
    packed at 00:50:20Z, 23 seconds after close 14 opened and ten after
    37 did. Its first job, close 15, was unbuildable by construction:
    `claude/MASTER.md` was close 14's forecast, and close 15's
    numbering, debt and oracle base waited on landings. By its own count
    it was the third desk running to hand close work forward; the 006
    desk, packed after both waves had landed, was the first that could
    author the close. CLAUDE.md §11.5 reads a cluster like that as a
    scoping signal: the close is cheap only for a desk that holds the
    landed tree. (Desk-side, the 004 sitting.)
    [2026-09-20: a second specimen, at close 16. The 009 master packed
    at 03:08:07Z, thirteen seconds after close 15 was packed and six
    after 104b, so close 16 was unbuildable at its open, as the 006
    desk's brief had warned. Both then applied under it, at 03:27:13Z
    and 03:45:15Z, and the desk still could not author the close: a
    master's tarball is a snapshot, and a wave that lands under it is
    invisible to it. It ended the sitting rather than ask for the landed
    `claude/MASTER.md` by upload, and the `2026-09-21-continue-plan-002`
    desk, packed after the landing, authored close 16. By the 009 desk's
    count, the second master in three to end with its first job unbuilt.
    A master opened beside its wave can dispatch; the close falls to the
    desk packed after the landing. (Desk-side, the 009 sitting.)]

183. **A board row that named a command surface nobody had read the
    parser for.** Row 104 said "bare `bale pack`" produces the context
    tarball; goal-less `bale pack` on a TTY is the wizard, and piped it
    refuses. The row was written without the parser read, and the 004
    desk found the gap when it read `build_parser`'s `p_pack` block to
    cut the row. One light-block question ruled the spelling,
    `bale pack --context`. A row that names a command is checked against
    the parser before it is cut. (Desk-side, the 004 sitting; the row,
    2026-09-16.)

184. **The blind probe held what the worker's own check passed.** 37's
    brief pinned the word `admissions` in PLANNER.md §5 step 5. The
    worker's clause said "every admission", and its own `validation.sh`
    checked for the substring `admission`, which the singular satisfies,
    so it passed a clause the brief's condition did not. The blind
    checkpoint held on it; the retry used the rider's own words and
    tightened the worker's assertion to the phrase. The dual stream doing
    its job: a worker's check is its reading of the brief, and the
    oracle is the brief's. (Worker-side, 37; the 001 desk's oracle.)

185. **An `awk` range past the core banner.** The 004 desk wanted
    TARBALL.md §5.10 and bounded an `awk` range by an end pattern that
    sat past the core banner, printing most of the file. Section order
    in the core-first docs is not numeric; a range is bounded by line
    numbers from a heading grep. (Desk-side, the 004 sitting; §7.)

186. **A hole the brief and the oracle both missed, closed by the
    worker.** 104a's decision 4: `bale open` refuses a stored argv
    carrying `--context`, in `pack_argv_preflight`, before the
    checkpoint dry run. Without it the replay would still have refused
    (open injects `--readme-file` or `--no-readme`, which refuse beside
    `--context`), but only after spending the oracle. Neither the 004
    desk's brief nor its oracle saw the path; the worker closed it in a
    file already in its forecast, and the 006 desk ratified it with
    decisions 1 to 6. Mechanism authority as CLAUDE.md §4 engraves it.
    (Worker-side, 104a; named by the 004 desk.)

187. **An attempt no desk's account mentions.** 37's record carries
    four attempts; the desks' accounts carry a HOLD and a retry. The
    third, `rejected` at 01:15:01Z with command `apply`, on a tarball
    named `response-2026-09-20-board-37-compaction-read-side-003 (1).tar.gz`,
    records no cause, no admission and no validation; 80 seconds later
    the same file name applied by `retry`, its admission restated. Two
    readings fit and the record picks neither: a corrected tarball given
    to `apply` where the held session wanted `retry`, or the
    out-of-forecast suite refused for want of an admission. The session
    log the attempt names would say. A close counts attempts from the
    record, not from an account, and a rejection with no recorded cause
    is a gap of entry 174's family. (From the records, found at the 006
    desk.)
    [2026-09-20: the 009 desk's read of 37's record: the same ` (1)`
    tarball was `rejected` under `apply` at 01:15:01Z and `applied`
    under `retry` at 01:16:21Z, and `tests/test_stats_compaction.py` was
    admitted with source `prompt` on both scored attempts, so a missing
    admission looks the less likely reading. It does not settle the
    entry, which stays on two readings (ruling 4's dispositions, §3);
    the session log would, and close 15's Proposal 1 is the remedy (§3
    registry). How the attempt was found, by the 006 desk's record: by a
    script over the attempts, not by reading the accounts, after two
    desk briefs had missed it.]

188. **Text about code or records that nobody had read.** Four specimens
    in one wave. Close 13's Proposal 2 asked for the closing pack's sid
    on a swept or superseded attempt; a superseded attempt had carried
    `superseded_by` since 0.3.23, so half of it was met before it was
    written. Its worker wrote "I have not seen the code", the desk that
    accepted it had not read the code either, and it was carried two
    closes before the 006 desk read the code to dispatch it. The 006
    desk's own stdlib-only rider and its `-k stdlib_only` selector pin
    were written without `tests/test_craft_response.py` read: by 104b's
    notes.md the pin already existed as `ToolsHermeticPin`, and the
    worker renamed five methods rather than write a second walker. The
    registry had carried 105's Proposal 2 since 2026-09-18 on the same
    footing. And the 006 desk's brief to close 15 said both earlier
    sittings ended before their waves landed, where the records show the
    004 sitting did not. Each was cheap to catch for the first session
    that held the file, and each cost a bracket to correct. Entry 183's
    family: a Proposal, a rider or a claim about a surface is read
    against that surface when it is accepted, not only when it is built.
    (Desk-side and worker-side, close 13 and the 006 and 009 sittings;
    two candidates merged at close 16.)
    [2026-09-23: obeyed for a whole wave at the
    `2026-09-22-continue-plan-001` desk, three brief claims corrected by
    the reading and one still imagined (entry 206); and a ledger fact
    nobody had read, which traveled to W3's brief (entry 211).]

189. **A board row naming a home the code reserves for someone else.**
    Row 103 names `cost.model_tier` per attempt as its telemetry home.
    `bin/bale_report.py` at 0.4.39 stamps the cost block all-null and
    reserves it for the harness, "never a worker self-estimate, never
    typed by a human" in the code's words as the 009 desk quotes them,
    and every attempt in the six records this close read carries it
    null. What a probe run can leave behind is the self-reported
    `model_identity` in the response manifest's provenance echo. The
    same row's "identical argv" N ways meets the pack-time disjointness
    gate, and the tree moves once any run applies. The row was written
    without the code read; the desk authoring its design sitting found
    both by reading before it wrote the brief, and handed both to the
    design desk. Entry 183's class on the telemetry side: a row that
    names a field is checked against the code that stamps it, and one
    that names a run shape against the gates the runs must pass.
    (Desk-side, the 009 sitting; the row, 2026-09-15.)

190. **A dress rehearsal under the real sandbox, with a pty inside it.**
    The 006 desk dress-rehearsed both wave-8 bundles with `bale open` in
    one scratch repo beside a read-only master: admitted together,
    expected-HOLD proofs fired, and both oracles ran confined under the
    real sandbox, because that desk's container runs `unshare`; by its
    record the two desks before it could not, or did not try. One of
    104b's controls drives the read-only sweep's accept prompt through a
    pty on stdin only, so the JSON line stays clean, and it ran inside
    the sandbox too. The 001 and 004 desks had each listed the sandboxed
    run as NOT done and left it to be retired by exercise at apply; here
    it was retired before delivery, and both applies then ran confined
    with no hold. The rehearsal ran over the desk's throwaway stub of
    the feature, not the feature: the 009 desk's own rehearsal declined
    the sweep for want of a TTY, and the first real `swept_by` was a
    live one (entry 194). (Desk-side, the 006 sitting.)

191. **Rehearsals that caught the oracle and not the brief.** The 006
    desk's rehearsals caught four defects, all in its oracles and none
    in its briefs. In close 15's: a pin that §5's calibration ruling
    runs two lines, where it runs six, caught by the oracle's base run;
    the sid probe cascading off a lost base line; and the sid regex
    taking the row number inside 104b's bundle stem for a counter. In
    104b's: a non-stdlib mutation, `import requests`, that a network
    denylist alone would catch, now `import yaml`. The first is
    PLANNER.md §4's imagined-surface class in a file the desk had open:
    the ruling was in `claude/MASTER.md`, in the desk's own tarball, and
    the pin was written from memory of it. Both bundles then landed on a
    first apply with no hold. A base run, a landing from the brief's
    bytes and a negative landing per probe find an oracle's defects
    before a worker pays for them; having the file open is not having
    read the line. (Desk-side, the 006 sitting.)
    [2026-09-21: a negative landing per probe is the aim, not what that
    desk ran: at close 16 the `2026-09-21-continue-plan-002` desk ran
    thirteen negative runs for eighteen probes, which gave eleven probes
    a negative of their own and seven none.]

192. **Context spent on a careless read, three desks running.** Entry
    185 was the 004 desk's `awk` range past the core banner. The 009
    desk did it twice: a telemetry dump of all of 2026-09-20's records
    where three were needed, and a heading-to-heading range over
    TARBALL.md from `### 5.10` to `## 6`, which printed §7, §3 and §4 as
    well, because DOCS.md §6.4 keeps section numbers stable while the
    core-first layout moves the sections; it named the two reads among
    its reasons for ending the sitting. The
    `2026-09-21-continue-plan-002` desk, with entry 185 and §7's range
    rule landed in the file it was reading, dumped the `base_files` map
    of 104b's record into its own context: a 100-entry map by its brief,
    115 by the record. The rule that landed was narrower than the
    failure. A read is bounded before it runs: a doc range by line
    numbers from a heading grep, or heading to next heading of any
    level; a record by the keys wanted, its maps counted before they are
    printed; a day's records by name. (Desk-side, the 009 sitting and
    the `2026-09-21-continue-plan-002` desk; two candidates merged at
    close 16.)

193. **A planner bundle nobody wrote.** At 03:25:14Z, three minutes
    before the 009 desk wrote its own 103 bundle, a file appeared in its
    outputs directory:
    `2026-09-20-board-103-capability-probe-design.bale-bundle`, sha256
    `68cc9188…`, its brief (sha256 `0e6666d9…`) claiming that desk as
    author, under a different slug and with an `--include` list. Nothing
    in the desk's conversation produced it; the likeliest cause, by the
    desk's account, is a regenerated reply whose files outlived it. The
    desk told the operator, left the file alone, and did not vouch for
    it. A bundle's claimed author is a string in its brief. What vouches
    for a bundle is the sha256 its desk publishes beside the `bale open`
    line (PLANNER.md §4), and a file without one has not been delivered.
    (Desk-side, the 009 sitting.)

194. **Two record fields read at the first close after they landed.**
    104b applied at 03:45:15Z. Seven minutes later the pack that opened
    103's design sitting swept the 009 master, and the closure's
    `swept_by` names it, `2026-09-20-board-103-probe-design-010`: the
    first live specimen, on a closure that earlier closes could have
    attributed only as a desk's account (entry 174). The 006 master's
    closure, 44 minutes earlier and swept at 0.4.39, is the last without
    the field. The same pack's `opened` attempt carries `packed_at`
    03:52:11Z against a `created_at` of 03:52:14Z, three seconds, the
    widest lag yet, on the field's first live record; the next,
    `2026-09-21-board-103-probe-design-001`, reads one second. Zero,
    one, two and three seconds are all on record now, so close 13's
    reason for the field holds: no fixed lag recovers a pack second from
    `created_at`. What the fields do not cover showed at once too: a
    closure by `unlock` carries no `swept_by` (103's first session), and
    neither record names the bundle it was opened from. Close 13
    proposed both fields with the close desk's reconstruction as their
    named consumer (DOCS.md §9), and that consumer read them one wave
    after they landed. (From the records, at the
    `2026-09-21-continue-plan-002` desk and at this close.)
    [2026-09-21: read again at close 17. The
    `2026-09-21-continue-plan-005` desk's brief said what its own pack
    swept "is not known here"; the records say it swept both open
    read-only sessions, `2026-09-21-board-103-probe-findings-003` at
    12:20:31Z and `2026-09-21-continue-plan-002` at 12:20:35Z, its own
    `packed_at` second, and that the `2026-09-21-continue-plan-008` pack
    swept the 005 master at 13:23:32Z, a second before that pack's
    `packed_at`. A desk's unknown, filled from `swept_by` at the very
    next desk. The gap this entry ends on cost again: the
    `2026-09-21-continue-plan-002` desk knew close 16 ran revision 2 of
    its bundle only from facts the notes repeat, and close 16's Proposal
    1, the bundle on an `opened` attempt, is now a rider-micro source
    (§3 registry). (From the records, at the 008 desk and at close 17.)]

195. **An attachment announced and absent, four times in one day.** On
    2026-09-21 a file a turn needed was announced and did not arrive
    four times running. The findings sitting's packets tarball did not
    come with its request; it emitted a light block and the file came by
    attachment (the findings' §11). At the
    `2026-09-21-continue-plan-002` desk's turn four the operator
    returned close 16's notes and attached nothing; the desk said so and
    closed on a paste-back probe, which can carry record facts and a sha
    but not a file, and bale's relay block then carried the notes. The
    `2026-09-21-continue-plan-005` and `2026-09-21-continue-plan-008`
    desks' openers each lacked the findings file their brief announced;
    each said so in a light block, as its brief instructed, and the file
    arrived on the reply. Answered every time, by a shape chosen afresh
    each time: the findings' Proposal 9 names the choice, and row 117
    waits on the operator's ruling. Until then, an announced attachment
    that did not arrive is said in the turn that finds it, and only the
    file answers it. (Desk-side and at the findings sitting; three
    candidates merged at close 17.)

196. **A bundle superseded on a late fact, and one left standing.** The
    `2026-09-21-continue-plan-002` desk superseded two bundles unopened
    in one sitting, each because a fact or a decision arrived one
    message after delivery: close 16's revision 1, derived into revision
    2 by four asserted string edits once the operator's row 103 ruling
    arrived, and the wave-10 master bundle, replaced when he chose to
    wait for close 16's landing so the next desk could start with no
    notes to chase. The `2026-09-21-continue-plan-005` desk met a late
    fact the other way: after delivering the doc lane it read the
    findings' §3.2, which showed the second refused paste block was a
    stale trailer on regenerated text, a fault the brief did not name.
    It asked to leave the bundle as built, the pinned sentence's
    file-first and never-retype clauses covering the fault without
    naming it; the question went unanswered, and the session applied
    clean on a first apply. A late fact supersedes a delivered bundle
    when it makes pinned text false, not when the text could have been
    fuller. (Desk-side, the 002 and 005 sittings; two candidates merged
    at close 17.)

197. **What a reply ratifies.** Three shapes in one day. At the
    `2026-09-21-continue-plan-002` desk, block three's [1] was answered
    with a question, "what are the six sentences?"; the desk read it as
    no answer, explained, and put it again in block four, where "as
    assumed" ratified it. At the `2026-09-21-continue-plan-005` desk,
    block two went unanswered, the operator's next message raising a new
    issue and ruling nothing; the desk put the block's live questions
    again in block three and said its third was moot once the doc lane
    had applied. At the `2026-09-21-continue-plan-008` desk one question
    row cleared three desks' carried debt: the 009 desk's eight calls,
    unruled through two desks and listed in close 16's landed 009 block,
    the 002 desk's eleven-and-seven split, and the 005 desk's eight
    calls, which the desk enumerated in the reply the block closed, so
    that "as assumed." ratified a list the operator had in front of him
    and not a blank. A reply ratifies what the question enumerated in
    text the operator could see; a question in answer, or silence,
    ratifies nothing, and TARBALL.md §5.10 already says the second.
    (Desk-side, the 002, 005 and 008 sittings; three candidates merged
    at close 17.)

198. **A number stated from memory, three times in one day.** The
    `2026-09-21-continue-plan-002` desk told the operator 0.4.40 has
    seventeen verbs, counting `init` and `hooks`, which sit under
    `config`, and corrected it to fifteen a turn later; and in its last
    reply before its brief it said three never-mutated probes had failed
    by cascade, from memory of a rehearsal whose output had been cleared
    from its context, where its brief states the checked count (entry
    191's bracket). The `2026-09-21-continue-plan-005` desk wrote "six
    words" and then "twelve" for a clause it had not counted, in a block
    about to go out; counted, the clause is eleven, and the block said
    eleven. Entry 181's family, before a ruling rather than inside one.
    A desk whose tool outputs have been cleared re-derives a number or
    does not state it, and a number in a block is counted before the
    block is sent. (Desk-side, the 002 and 005 sittings; two candidates
    merged at close 17.)

199. **Cascades turned into SKIPs.** At the
    `2026-09-21-continue-plan-002` desk, rehearsal caught two defects in
    close 16's oracle and none in its brief, both cascades: a
    block-order fault failing four sibling probes, and a wrong line 14
    failing the sid probe; on a HOLD the worker would have had five
    labels for one mistake. Close 16's worker then caught the same
    cascade in its own `validation.sh`, "recorded in the block I had
    just written", and made the dependent check SKIP by name. The
    `2026-09-21-continue-plan-005` desk built both of wave 10's oracles
    that way from the start: a renumbered heading or step fails one
    probe and SKIPs its dependent, and every negative landing failed
    exactly one probe. Its rehearsals caught three defects in its
    rehearsal script and none in the oracles or the briefs. Entry 191's
    class: a probe that depends on another SKIPs by name when the other
    fails, so one mistake reads as one label. (Desk-side and
    worker-side, the 002 and 005 sittings and close 16; one candidate,
    with the 005 desk's verification, at close 17.)

200. **A findings file that carries an oracle.** Row 103's findings file
    carries the capability probe's oracle: the canned answer's
    substance, the checkpoint's probe labels, the planted bait. Handed
    to the `2026-09-21-continue-plan-002` desk, it met no rule for what
    may travel into a request or land in a file every pack ships. The
    desk made one, ratified with its calls (its light block three, [3]):
    sections without bait travel, so its brief embedded only §7 and §8;
    the rest is the operator's to attach beside an opener, handled as
    the file's own header says; none of it lands in the five global docs
    or in `claude/MASTER.md`. The 005 and 008 desks held to it, the doc
    lane's deltas were written under it, and row 103's bracket cites the
    file by section for that reason. The kit lives outside this repo, so
    the rule is the only fence: a file that carries an oracle travels by
    the operator's hand, never inside a request or a shipped doc.
    (Desk-side, the 002 sitting; held since.)

201. **A close handed on, by advice and by a stop condition.** At the
    `2026-09-21-continue-plan-002` desk's turn seven the operator asked
    whether close 17 could be authored there. The desk said it could and
    advised against, on three grounds: no landed base in hand; a context
    already cleared of tool outputs, with three careless errors behind
    it; and a desk closing its own sitting loses its second reader. He
    moved close 17 on. The `2026-09-21-continue-plan-005` desk took
    close 17 under a stop condition he ruled in advance, stopping "if
    the budget reads thin once MASTER.md's tails and the findings are
    read", measured what its context had left after the doc lane,
    invoked the condition, said so, and handed the close on; when he
    then brought a new issue, it built the fix's smaller oracle at his
    "as assumed", with the stale-base risk named. Entry 182's bracket
    has the first half of the rule: the close falls to the desk packed
    after the landing. The second half: a stop condition ruled before
    the work is invoked on the desk's own measure and said to be
    invoked, and a fresh desk is the close's second reader. (Desk-side,
    the 002 and 005 sittings; two candidates merged at close 17.)

202. **A misreading held in place by its own pin.** From another project
    the operator reported a split that did not transition: a condition
    true as written had been read as "only", the second report of one
    symptom. `tests/test_sanctioned_pairs.py` had pinned CLAUDE.md
    §11.2's bundling sentence in its conditional form, holding in place
    the wording row 79's ruling of 2026-09-14 was meant to replace (the
    finding's §6, by the fix's notes.md). The doc lane's worker wrote
    the finding at his request, carriers, pins and needed rulings laid
    out; the `2026-09-21-continue-plan-005` desk verified all five
    carriers on its tree, shipped the finding whole as the fix brief's
    appendix, and put its four rulings to the operator as one question
    row, a light block admitting three. The fix's worker answered the
    pin with a negative class, `RetiredSplitConditions`, on the ground
    that "a positive pin can't see a condition come back in the sentence
    next to it" (§5, 2026-09-21). A pin holds words, not a reading: a
    condition meant to be gone is pinned absent. (Desk-side and
    worker-side, the 005 sitting and the fix; three candidates merged at
    close 17.)

203. **Required spellings that bit, and VERBATIM sentences that held.**
    The doc lane's worker first wrote the field as one code span,
    `feedback.self_reported.forecast_departures`, which does not contain
    the required spelling with its backticks; its own new pin caught the
    draft before apply, and both homes now name the field alone with the
    stream beside it. A required spelling can refuse a reasonable draft,
    and the worker's own pin is where that is cheapest. Across the doc
    lane and the fix, five VERBATIM sentences landed without correction,
    two and three, each checked by its worker against the code or the
    docs before it was placed. A VERBATIM sentence bound for a global
    doc is checked against what it describes by the session that lands
    it, whoever wrote it. (Worker-side, the doc lane and the fix; one
    candidate at close 17.)

204. **Two doc sessions from one desk, one against a base known stale.**
    The `2026-09-21-continue-plan-005` desk authored the doc lane and
    the fix, and both passed on a first apply, checkpoint and worker
    validation, with no admissions. The fix's oracle was authored
    against the desk's own tarball, packed before the doc lane landed,
    so its copies of `docs/CLAUDE.md` and `docs/TARBALL.md` were stale;
    the desk said so in the brief and keyed the oracle to headings and
    phrases. The staleness was the desk's alone: by its record's
    provenance echo the fix's request carried the doc lane's landed docs
    (CLAUDE.md `214639ce…`, TARBALL.md `29ecbbae…`, where close 16's and
    the doc lane's read `52c8771d…` and `b7265475…`). An oracle keyed to
    stable phrases survives a sibling's rewrite of its files: PLANNER.md
    §3's known-stale rule, exercised from the oracle's side. (Desk-side,
    the 005 sitting; the records read at close 17.)

205. **The silence probe: a blind oracle holding a correct-looking
    response.** The tools micro's first attempt printed a `[PASS]` line
    whose registry description named `forecast_departures` for a path
    inside the forecast. Its worker's tests had checked for the warning
    code, not for whole-output silence, and passed; the blind
    checkpoint's `lint-request-flag-silent-inside-forecast` held it, one
    failed probe by label. Ruled work-defect at the 001 desk; the retry
    (warnings carrying a `headline`, descriptions no longer naming their
    subject word, whole-output silence pinned in the suite) applied
    seven minutes later on `bale retry`, one claim key grown to end ";
    silent when all inside". A probe asserting absence over the whole
    output sees what a presence test cannot. Companion to entry 119's
    class, from the live side. (Worker-side and desk-side, the tools
    micro and the 001 sitting; Part 2's candidate at close 18.)

206. **A desk that read the code for a whole wave.** The
    `2026-09-22-continue-plan-001` desk read the code every micro source
    named before writing either brief, the first desk to obey entry
    188's rule for a whole wave. The reading corrected three brief
    claims before dispatch: `--fragment` already existed, relay wrote no
    telemetry at all, and `stamp_swept_by` already existed. One went out
    imagined anyway: the rider brief said `test_rollback_telemetry` had
    an envelope-subset guard, and the rider's worker wrote a real one.
    Reading the code cut the imagined surfaces from many to one; it did
    not make them zero. (Desk-side, the 001 sitting; Part 2's candidate
    at close 18.)

207. **Rehearsal caught two oracle defects; a dress rehearsal opened two
    sessions together.** At the 001 desk rehearsal caught, before
    delivery, a fixture that declared its own departure once seeding
    landed, and `record_version` imagined as an enum where the schema
    pins `minimum: 1`. Both micros were then opened through the real
    `bale open` in a scratch repo, isolated `HOME` and piped stdin, argv
    replayed, the rider pack admitted by the disjointness gate with the
    tools session open, as entry 190's desk did for wave 8. Entry 119's
    class, specimens two and three; both micros applied with every claim
    `agree`, the tools micro after one work-defect hold (entry 205).
    (Desk-side, the 001 sitting; Part 2's candidate at close 18.)

208. **Paired desks: de-correlated greps, correlated framing.** The
    `2026-09-22-board-100-design-004` sitting ran two planner desks
    under one sid. Their first turns were independent and their greps
    diverged, which is what pairing buys; their framing did not, both
    working from one brief, and neither saw `bale pack`'s include gate
    on `--include claude/checkpoints` until a paste was refused. That
    refused pack had already closed the parent, and the item the desks
    signed says so: "recovered is not never happened" (row 121). Two
    light blocks went out under the one sid, neither was answered, and
    no record holds them: close 17's Proposal 2 with a live specimen.
    Re-derived independently, the revc bundle came out byte-identical on
    both desks, a determinism claim both desks worded as observed twice,
    not proven (item 9). Paired desks are recorded here as evidence, not
    as a sitting kind: the upward report's Proposal 1 reads the pattern
    that worked as a ledger plus a successor re-verifying where it
    builds (§3 registry). (Desk-side, the 004 sitting; its merged file,
    read at the 005 desk.)

209. **The cadence's first application.** The
    `2026-09-23-board-100-design-001` desk authored and ratified its own
    wave with no master between: the successor opened at 00:26:04Z, and
    W1, W2 and W3 applied at 01:45:46Z, 01:54:02Z and 03:07:57Z, three
    sessions and two bumps, 0.4.42 and 0.4.43, landed before the
    close-18 probe at 03:15Z. The one hold was ruled at the desk that
    wrote the oracle, the three notes.md were ratified there, and the
    upward report reached the master's desk with the three relays; the
    close waited for it, per §5's 2026-09-22 block. What it cost: the
    successor's sid went unswept (entry 212), and one oracle probe went
    out that its desk could not dry-run (entry 210). (Desk-side, the
    design-001 sitting; recorded at close 18.)

210. **A probe the desk could not run, and an unlabeled exit 1 read as a
    verdict.** W3's checkpoint v1 exited 1 with no failed-probe label
    while every labeled probe passed and the worker's five claims came
    back observed and `agree`. The design sitting ruled a fixture defect
    (PLANNER.md §5 step 6): a probe piped the pack report into
    `python3 -` while feeding the script by heredoc, so `json.load` read
    nothing and `|| status=1` recorded a defect as a verdict, a probe
    the desk could not dry-run end to end and had flagged on-watch in
    its own report. v2 changed probe 3 only and routed every non-probe
    failure to exit 2 (sha256 `b8c69ae8…`, row 100); it was amended on
    the tree, and the held tarball applied on `bale retry` with no
    worker retry. PLANNER.md §4's fixture-defect watch, exercised: an
    oracle's exit 1 means a check failed only if its own errors route to
    2. Row 122's second half is the proposed rehearsal. (Desk-side, the
    design-001 sitting; W3's record.)

211. **A wrong ledger fact that traveled two desks and a successor.**
    W3's brief listed `upgrade.sh`'s "pre-flight member check" among the
    rename's doc-name sites. It is none: `REQUIRED_RELEASE_MEMBERS` is
    bin/schemas/tools by design. The fact came from the parent ledger,
    crossed the two 004 desks and the successor unverified, and was
    caught by W3's worker reading the file, which it left unchanged and
    named (ratified at the design sitting; row 126). The report's other
    [w3] corrections: the doc-name sites were `build.sh`, `install.sh`
    and `validate.sh` only; W2's close tally was 1506/48; nine cites had
    drifted 1 to 15 lines, all resolved by phrase match. Entry 188's
    family on the ledger side, and the case for item 5's tagging: a
    ledger line that names who verified it can be told from one that
    nobody did. (Worker-side, W3; the upward report as the 005 desk
    digested it.)

212. **An unswept successor sid.** The successor's read-only sid was not
    swept by any of its three children's opens, each a `bale open`
    replay, where the 004 open swept the 001 master and the successor's
    own open swept the 005 master. Its record reads `opened`, and the
    file is untracked because no closure committed it (the close-18
    probe, 03:15Z). A design sitting that authors its own wave outlives
    later packs by the cadence's design, so whether its sid should
    close, and when, is the new watch's question; recorded as a watch,
    not a defect, by the 005 desk's call. (Records, at close 18.)

213. **A count where the outcome was a pointer.** Row 43's checkpoint v1
    held the first attempt on one failed probe,
    `expects-probe-collision-one-home`: it pinned a 12-line floor on
    §5.9.1, a size the brief never gave. The desk ruled fixture defect
    on the worker's pasted bytes and issued v2, zero mentions of the
    flag in §5. The worker, holding the block it was asked to hold,
    found the held §5.9.1 still restating the collision without the
    literal, and its own suite pin green on exactly that defect; it
    shipped a corrected tarball with one pointer line per home naming
    the flag and §3.3, the stricter and better reading, which v2 would
    have held for its two mentions. v3 pinned the shape, every §5 line
    naming `expects_probe` also naming §3.3, and the corrected tarball
    applied under it, `stamp_matched: false` accepted. A count is a
    mechanism; the outcome was "a pointer names its home" (PLANNER.md
    §4, outcome contracts). (Desk-side and worker-side, the 006 desk and
    row 43's session; the brief and the record.)

214. **A fixture that built its specimen through the session's own
    forecast.** The micro's checkpoint v1 built its row-121 specimen
    bundle with the staged crafter, which the micro's own second rider
    taught to refuse that argv: the oracle errored and exited 2, a
    defective oracle and no verdict (TARBALL.md §7.5), while the
    worker's 23 claims all came back `agree`. v2 hand-rolled the bundle
    from the wire format. The first retry was `rejected` at the
    provenance gate because the checkpoint had changed since pack; the
    second applied the same tarball with `stamp_matched: false`. The
    lesson, for PLANNER.md §4's next holder: a fixture that exercises a
    gate never builds its specimen through a surface in the session's
    own forecast (§3 registry). (Desk-side, the 006 desk; the micro's
    record.)

215. **A suite ships with what it reads: two include misses.** Row 43's
    request lacked `bin/`, which `test_doc_crossrefs.RelayParagraphPins`
    loads (`bin/bale_report.py`); the desk caught it before delivery by
    running the suites inside the emitted request. Row 122's request
    lacked `claude/context/adr/`, which row 43's new ADR-0013 key pin
    reads; only the worker's whole-tree run caught it,
    `test_adr_0013_citations_carry_resolving_keys` failing identically
    on the base. The standing fact is §7's: any request shipping `tests`
    ships `claude/context/adr`. The 45 arc met the same class at runtime
    (row 131). (Desk-side, the 006 desk; row 122's notes.md.)

216. **Read-side staleness under disjoint write forecasts.** Stemwell's
    wave1 and wave2a were admitted together, their write forecasts
    disjoint. Wave2a's validation asserted `report`'s Total line byte
    for byte from its packed `context/` copy; wave1 applied at 12:58:46Z
    and moved that byte, and 2a's apply at 12:59:00Z, 14 seconds later,
    held: two `DISAGREE` rows, the checkpoint PASS both times, the
    response correct. The retry's `includes_missing` carried a
    `decision:` line, ruling 4's form, because no field says a packed
    copy went stale. ADR-0015 has no word for this; row 129 is the
    proposed word. (Worker and records, stemwell; the upward report.)

217. **HOLDs that cluster on the desk.** Across wave 11 every bale-src
    HOLD was the 006 desk's: row 43's v1 on a count the brief never gave
    (entry 213) and the micro's v1 on a fixture built through the
    forecast (entry 214), with row 43's v2 amended away before it ran
    against the tarball it would have held, and two include misses of
    its packing (entry 215). None was worker misunderstanding. The brief
    counts three of the desk's oracles held; the records carry two
    checkpoint HOLDs, and this entry lands the records' count.
    PLANNER.md §4's standing watch says that HOLDs clustering on
    checkpoint-fixture defects rather than worker misunderstanding name
    the authoring practice, not the worker, as the defect: here they
    name the 006 desk's. The arc's one HOLD was the worker's validation
    on staleness; its oracles passed all eight attempts. (Desk-side, the
    006 desk, by its own brief; the records.)

218. **Two design-desk defects on the master desk's line.** Stemwell's
    seed v1 was refused by the worker surface's safety classifier on its
    brief's wording before any worker built, and sat 1 h 41 min from
    open to abandon; v2, the same design reworded, applied 45 min 52 s
    after its open. The refused wording came from the 006 desk's brief
    for the design sitting: "hostile", "hazards", "the architect must
    not know", by the brief's list, where the report's Proposal 4 lists
    "hostile", "planted", "must stay ignorant" (row 132). And the design
    desk's own `--write .` on the seed, the self-oracle shape, was
    refused by the blindness gate at rehearsal: a case the 006 brief
    could have named, the wave having just exercised that gate. Both are
    recorded here on the master desk's line, as the 006 desk asked; row
    132 carries the framing rule. (Desk-side, the 006 and design-010
    desks; the upward report and the brief.)

219. **A first wave on a foreign codebase, in numbers.** Seed v2 in 45
    min 52 s; six first-wave sessions in 22 min 25 s wall clock
    (12:51:21Z to 13:13:46Z), four opened in 17 seconds; seven sessions
    applied on eight attempts; 57 claim rows, 54 `agree`; zero
    clarification rounds, one probe, a 2-minute round trip by the
    operator's clock; the ceremony floor six files and 7,729 bytes for
    one character; the serialization gap 15 min 40 s, 4 min 46 s of it
    operator latency after the gate cleared. The designed trap for
    misunderstanding off doc work, wave5's two parsers and five read
    sites with no docs, passed with nothing asked. What chafed was the
    packing and the gates, not the workers' reading of intent. (Records,
    stemwell; the upward report.)

220. **A brief that stated an unverified fact.** B's brief said "EOF and
    ^C still abort the pack" at the README question. They never did:
    `confirm_yn` declines on both. The worker found the sentence false
    against the bytes, followed the brief's outcome 1 (today's meaning
    preserved) rather than the sentence, kept `confirm_yn`'s exact
    answer set, and flagged it as a decision to ratify; the wave2-004
    desk verified against `bin/bale`, ratified the worker, and recorded
    the correction against itself. The
    flagged-deviation-plus-ratification loop (AGENT.md §4) working as
    designed, on a desk fact rather than a worker reading. (Desk-side,
    the wave2-004 desk, by its own brief; B's notes.md.)

221. **A hash typed before it was computed.** In chat, the wave2-004
    desk's file caption for D's bundle carried a sha256 typed before the
    digest was run; it was corrected in the same reply. No artifact
    carried the wrong value and nothing downstream read it. The class is
    TARBALL.md §5.2.1's, a hash transcribed rather than computed, at the
    desk's chat surface where no lint runs; the desk's own correction is
    the only catch that surface has. (Desk-side, the wave2-004 desk, by
    its own brief.)

222. **Two oracle defects caught before delivery, and the exit-code rule
    they taught.** D's checkpoint, as first drafted: a fixture step that
    ran the tree under test raised "oracle broken" (exit 2) when the
    tree crashed, instead of grading FAIL (exit 1); and a word-match
    probe was satisfied by the fixture's own goal text and paths. Both
    were caught at the desk before the bundle shipped, and D's
    checkpoint PASSed first time with its stamp matched. The lesson the
    desk wrote for PLANNER.md §4's next holder is the registry's rider
    of this date: a crash in the code under test is the work's failure,
    exit 1, inside fixture steps too; only the oracle's own machinery
    exits 2 (the §5 "failed oracle control" contract's complement); and
    no word-matching probe may see text the fixture itself authored.
    Entries 214 and 217's family, caught one step earlier. (Desk-side,
    the wave2-004 desk, by its own brief.)

223. **A suite ships with what it reads, repeated: the log-hold include
    miss.** In the cleanup desk's words: "log-hold's pack shipped `bin`,
    `tests`, and the internals doc, but not the four paths seven of the
    suites read: `bale.toml` (test_include_group ×3),
    `claude/changelog/` (test_changelog_record ×2), the ADR-0013 file
    under `claude/context/adr/` (test_doc_crossrefs), and the repo-root
    `README.md` (test_global_doc_noun). The worker could not run them
    and claimed the full suite as `predicted` (its notes, Validation).
    It is §6 entry 215's class, "A suite ships with what it reads",
    repeated by this desk. Caught at log-hold's relay; the two queued
    code bundles were reissued as `-r2` with the reads added before
    either opened." Entry 215 named the class twice at wave 11 and §7
    carries the rule; every worker of this arc had met the same gaps
    (the changelog corpus, ADR-0013, the repo's `bale.toml`; A names the
    repo `README.md` too) as the six baseline failures each notes.md
    reports, seven in A's, and C's record filled `includes_missing` with
    them, so the signal was on the desk's own inputs before it packed.
    The class's fourth occurrence on record, after entry 215's two and
    row 131's; the pack-time remedy, a warning when an included suite's
    imports or fixture reads fall outside the includes, has no row yet.
    (Desk-side, the cleanup desk, by its own brief.)

224. **The changelog obligation, missed across an arc.** `CODE.md` §8.5,
    "Surface changes write their changelog entry": "the session that
    changes a machine-readable surface writes that version's entry in
    the same response, so the record is part of the change rather than a
    later reconstruction of it." No session of the friction-points arc
    that changed bale's code bumped. Their recorded forecasts carry
    neither `bin/VERSION` nor `claude/changelog`: A's seven paths, E's
    eight, B's ten, C's six and D's eleven, in the 001 and wave2-004
    desks' §3 blocks, and log-hold's, the rename's and convergence's, in
    their records; §7 records the arc "bumpless on 0.4.45" as a fact,
    not a gap. In the cleanup desk's words: "None of the desk's three
    code briefs carried CODE.md §8.5: a session that changes a
    machine-readable surface writes that version's changelog entry in
    the same response. None of the forecasts named `bin/VERSION` or
    `claude/changelog/` either. The earlier desks' briefs for C and D
    had the same gap. The rename worker found it and proposed the
    catch-up; it is not yet in MASTER.md." Found by the rename worker,
    who read §8.5, named the gap and proposed the catch-up rather than
    mint a version outside its forecast (its notes.md: it "followed the
    arc rather than mint a version in a session whose forecast does not
    name `bin/VERSION` or `claude/changelog/`"); ruled at the cleanup
    desk, light block four, [2] (§5, 2026-10-06); the catch-up's own
    list named four of the eight sessions of the arc that changed bale's
    code, "C, D, log-hold, the rename", and the close desk's brief for
    the bump asks for all eight (§3's close-desk block); dispatched as
    `2026-10-06-bump-0-4-46`. The worker side held where the desk side
    did not. (Desk-side: the cleanup desk's and the wave2-004 desk's
    briefs, by the cleanup desk's words; the forecasts all three desks
    authored, by the records. The close desk did not read A's, B's or
    E's briefs, so nothing here says what they carried.)

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
- Version landmark: 0.4.34 (`2026-09-16-board-47a-hold-card-triage-001`);
  0.4.33 was 102 the same sitting.
- Tests-forecast rule, concurrency clause (2026-09-16): a session
  running alone forecasts `tests`; sessions running beside each other
  forecast named suites, and a worker's new test file travels
  ship-enumerate-admit. No sibling in a wave forecasts the `tests`
  directory.
- A blind checkpoint that drives `bale` inside a scratch repo sets a
  repo-local git identity (bale's own commits need one under the
  scrubbed environment) and unlocks every session between scenarios
  (a replayed pack leaves a session open, and the next scenario
  collides with it). `/tmp` is a private tmpfs inside the sandbox, so
  `mktemp -d` is safe.
- A blind checkpoint that drives `bale` in a scratch repo also sets
  `[sandbox] enabled = false` in that repo's `bale.toml`, so its inner
  applies do not nest namespaces inside the confined checkpoint; it ran
  clean at 110's real apply (2026-09-19).
- A validation invariant under target-base staging is stated relative
  to the response ("declares no `bin/VERSION` change"), never as a
  literal read off the request tree (§6 entry 143).
- Install-shipped schemas are self-contained: descriptions cite
  versions ("v0.4.34"), never board numbers;
  `test_global_doc_selfcontainment` enforces it. BALE.md is
  repo-local and keeps its board citations.
- The delivery directory and the search path are one place:
  `/mnt/c/Users/chord/Downloads/`; the desk's `bale amend-checkpoint`
  line names the amendment there with `--sid`, always.
- Version landmark: 0.4.36 (`2026-09-18-board-47b-relay-blocks-003`);
  0.4.35 was `2026-09-17-board-56-57-changelog-aborted-002` (close 11's
  Proposal, accepted).
- Include-authoring rule, accreted 2026-09-18: a pack that ships
  `tests/` ships the repo-root `bale.toml` and `claude/changelog` too.
  Without them, inside a request,
  `test_include_group.TestThisRepoGroup` errors three times and
  `test_changelog_record` fails twice (`test_corpus_is_not_empty`,
  `test_current_version_has_a_valid_record`); until a pack carries
  them, the brief's known-baseline sentence names all five (109's
  Proposal 3, 47b's Proposal 4).
- A pack leaves its own `opened` telemetry record untracked until its
  session closes; "tree clean after a pack" means no *tracked* file
  modified (§6 entry 156).
- The session log's worker band is not only the worker's output: apply
  journals the checkpoint's exit line inside it. Nothing worker-facing
  is built from the log (§6 entry 159).
- `tests/harness.py` carries `_load_cli()` (an in-process `bin/bale`
  under the module name `bale_cli`, fresh per call) and `normalize()`
  (row 109).
- One-apply-behind held for 47b: the first HOLD or clean apply after its
  landing is the first to print relay blocks.
- Version landmark: 0.4.37 (`2026-09-19-board-110-held-admissions-007`);
  0.4.36 stood through the unrecorded sitting's two bumpless landings
  (row 112) and 111's.
- One-apply-behind held for 110: its landing apply ran 0.4.36, so a HOLD
  there would have written no admissions stamp, and
  `bale amend-checkpoint` would have printed the degrade line (the
  0.4.37 changelog record's note).
- Include-authoring rule, accreted 2026-09-19: a pack that ships the
  release surface ships the repo-root `README.md` too; inside a request
  the install's `validate.sh` fails `README.md present` without it
  (110's notes).
- Dispatch check, grown: a rider that changes emitted text gets a grep
  of `tests/` for that text before the bundle goes out, and the pinning
  suite joins the forecast (§6 entry 166).
- Version landmark: unchanged at 0.4.37
  (`2026-09-19-board-110-held-admissions-007`); the 009 sitting's two
  landings, close 13 and 113, were both bumpless.
- `tests/` is a package since row 113 (`tests/__init__.py`): the dotted
  form, `python3 -m unittest tests.<suite>` from the repo root, works
  for every suite, pinned by `tests/test_dotted_run_form.py`. A bare
  `python3 -m unittest` from the repo root now discovers the whole
  suite, where before it found nothing; no script runs that form
  (113's worker checked `validate.sh`, `scripts/build.sh`,
  `install.sh`, `upgrade.sh` and `bale.toml`).
- In a one-process dotted run of every suite, the helper suites load
  twice, as `tests.X` and as bare `X`; nothing keys on module identity
  across them. A plain discovery run loads one copy of each (113's
  notes).
- The desk's in-process gate check: a bundle goes through
  `bin/bale_open.py`'s `read_bundle` and `compose_pack_argv`
  in-process, with a two-function `log`/`fail` shim in `__main__`. It
  is not a `bale open` dress rehearsal in a scratch repo, which the 006
  desk ran and the 009 desk did not.
- Version landmark: 0.4.39 (`2026-09-20-board-104a-context-pack-005`);
  37 took 0.4.38 (`2026-09-20-board-37-compaction-read-side-003`) the
  same day. Close 14 and close 15 are bumpless; 104b carries the next
  bump.
- The context pack exists: `bale pack --context` in a directory writes
  `<dir>/.bale/outbox/context-<name>.tar.gz`, a session-less tarball of
  that tree, replaced on a re-run. In a repo subdirectory it lands under
  that subdirectory's `.bale/outbox/`, and the repo root's `.baleignore`
  and the checkpoint exclusion still apply. Outside git, `.gitignore` is
  not consulted. `bale status` does not show it (104a's Proposal 4).
- An oracle's verdict line carries the label alone, and any detail goes
  on a following `  detail:` line: labels travel to the worker on a
  HOLD, and detail never does (§6 entry 180).
- A range in a core-first doc is bounded by line numbers from a heading
  grep, not by section number or an end pattern: section order there is
  not numeric (§6 entry 185).
- Version landmark: 0.4.40 (`2026-09-20-board-104b-pack-telemetry-008`);
  close 15 and close 16 are bumpless. The suite stands at 1419 tests, 48
  skipped by the slow gate, and `validate.sh` at 92 checks, by 104b's
  notes.md.
- `bale pack --json` carries two always-present keys since 0.4.40:
  `sweep`, a list that is `[]` when the pack closed nothing, and
  `include_group`, null when the human report prints no include-group
  row (§5). A desk scripting a pack can read what the pack swept from
  the JSON line.
- In records written since 0.4.40, a pack's `opened` attempt carries
  `provenance.packed_at`, and a closure written by a read-only sweep
  carries `swept_by`, the sweeping pack's sid. Earlier records carry
  neither, a closure by `unlock` carries no `swept_by`, and absence
  reads as unrecorded, not as no sweep. No record names the bundle a
  session was opened from (§6 entry 194).
- `python3 -m unittest -k stdlib_only` selects the tools' stdlib-only,
  no-network pin, `ToolsHermeticPin` in `tests/test_craft_response.py`,
  five tests (104b).
- A desk whose container runs `unshare` can dress-rehearse an oracle
  confined under the real sandbox before delivery, and a control can
  drive a TTY prompt through a pty on stdin only, inside it; the 006
  desk of 2026-09-20 did both. Not every desk's container can (§6 entry
  190).
- A record's `base_files` map can run past a hundred entries. Read a
  record by the keys wanted, and count a map before printing it (§6
  entry 192).
- Version landmark: still 0.4.40
  (`2026-09-20-board-104b-pack-telemetry-008`); close 16, the doc lane,
  the split-transition fix and close 17 are all bumpless. The next bump
  is one of the two code micros, one bumper per wave.
- The three doc suites, `tests/test_doc_crossrefs.py`,
  `tests/test_global_doc_selfcontainment.py` and
  `tests/test_sanctioned_pairs.py`, stand at 43 tests: 36 before wave
  10, 41 at the doc lane's `ByteDisciplinePins`, 43 at the fix, whose
  suite alone holds 4, by the two workers' notes.md.
- 0.4.40's parser has fifteen verbs: pack, apply, retry,
  amend-checkpoint, relay, revert, rollback, unlock, open, handoff,
  config, help, completion, status and stats; `init` and `hooks` sit
  under `config`. There is no `validate` verb (row 118), by the
  `2026-09-21-continue-plan-002` desk's read of `bin/bale`.
- A pack with no `--include` takes the whole tree (`bin/bale_pack.py`,
  "the whole-tree default"); the masters' packs rely on it.
- The crafter's `--light-block FILE` renders a light block from a filled
  clarification manifest (`response_kind`, `session_id`, `questions[]`
  with `question`, `context`, `default_assumption` and `why_blocked`)
  and refuses more than three rows; `--probe SLUG` emits the TARBALL.md
  §4.2 paste-back skeleton. Both worked first time at the 002 desk, and
  the crafter's `--help` at close 17 says the same.
- `tests/test_doc_crossrefs.py`'s `RelayParagraphPins` asserts
  TARBALL.md §7's lead does not contain "staging directory"; a delta to
  that lead has to know it (the 005 desk).
- A phrase probe needs a word boundary: "as a file" is a substring of
  "has a file", which TARBALL.md §10.1 contains (the 005 desk).
- PLANNER.md §20 sits between §6 and §7 in the file, so "the section
  after §6" is §20: core-first order again (§6 entry 185).
- At 0.4.40 nothing checks an unannounced write made during
  `validation.sh`: reconciliation runs before the script and nothing
  walks the tree after it (the doc lane's worker's read of
  `bin/bale_staging.py`), and TARBALL.md §7.1 says the printed list is
  the whole of the check (row 120).
- Version landmark: 0.4.43 (`2026-09-23-board-100-w3-file-rename-004`);
  W2 took 0.4.42 (`2026-09-23-board-100-w2-code-surfaces-003`) and the
  rider micro 0.4.41 (`2026-09-22-rider-micro-003`). The tools micro, W1
  and close 18 are bumpless. The suite stands at 1507 tests, 48 skipped,
  and `validate.sh` at 93 checks, by W3's landing as the 005 desk read
  it.
- `docs/CLAUDE.md` is `docs/AGENT.md` since 0.4.43; the five globals are
  AGENT.md, TARBALL.md, DOCS.md, CODE.md and PLANNER.md, and
  `validate.sh` refuses a leftover `docs/CLAUDE.md` (ruling 3). Earlier
  text in this doc says CLAUDE.md where it was the name at the time.
- `expects_probe` defaults to `agent-decides`, and `claude-decides` is
  accepted for good; `[layout] agent_dir` defaults to `claude`, and no
  existing repo is renamed; `contract_docs` validates under either key
  set; `model_identity` is `<vendor>:<model>`, pinned as a pattern;
  `INJECTED_TOOLS` is `CARRIED_TOOLS` (§5, 2026-09-23).
- At the close-18 probe, 2026-09-23T03:15Z: git `d855163` on `main`,
  bale 0.4.43 by `bin/VERSION`, one untracked file,
  `claude/telemetry/2026-09-23-board-100-design-001.json`; `bale.toml`
  pins `[validation] base = "claude/checkpoints/{sid}.sh"`;
  `claude/context/board-100-arc/` did not exist. The 005 desk verified
  the five `docs/` and both `tools/` byte-identical to its carried
  copies, and `claude/MASTER.md` at 10816 lines, `a8bbbeee…70a9`; close
  18 found the same line count and sha256 on its base before inserting.
- In records written since 0.4.41, an `opened` attempt from a bundle
  carries `bundle` (stem, `brief_sha256`, `checkpoint_sha256`,
  `manifest_sha256`), a `rejected` attempt carries `cause`, and
  `relay-refused` is written for refusals of the input itself; the
  earlier bullet's "no record names the bundle" holds for older records
  only.
- `bale pack`'s include gate refuses an `--include` naming the
  checkpoint pattern's subtree, `claude/checkpoints`; broader ancestors
  are fine and auto-exclude (the paired-desk sitting's item 3). At
  0.4.41 a refused pack carrying `--supersedes` could close the parent
  before the gate fired (row 121).
- Version landmark: 0.4.45 (`2026-09-23-board-122-rehearsal-verbs-009`);
  the micro took 0.4.44 (`2026-09-23-board-121-125-code-micro-007`). Row
  43's session and close 19 are bumpless. The suite stood at 1544 tests,
  48 skipped, at the micro's landing; row 122 added
  `tests/test_rehearsal_verbs.py`, 20 tests, and gave no whole-suite
  count. The four doc-pin suites stand at 60 tests after row 43, 52
  before, by the two workers' notes.md.
- `bale open --check`, `bale open --dry-run` and `bale pack --dry-run`
  exist from 0.4.45. Each is a prefix of the real pipeline and writes
  nothing to the repository; the `--dry-run` open keeps its log under
  `${TMPDIR}/bale-open-rehearsal-*/` and names it in its report;
  `--check` and `--dry-run` on `open` are argparse-exclusive, and
  `--dry-run --json` refuses. From 0.4.45 a real `bale open` runs the
  full argv-gate set before its checkpoint dry-run. From 0.4.44 a second
  `bale open` of a still-open session's bundle records `desk-N` with
  `command: "open"`, and a pack runs every argv-only gate before its
  `--supersedes` exchange.
- A read-only pack stamps `base_files: {}`, so a planner desk has no
  base hash for a file it reads; the 006 desk used its carried copy's
  for `claude/MASTER.md`. Close 19's own request stamped
  `2f64cbff…d879d`, and its base matched, 11,710 lines, before it
  inserted.
- Any request shipping `tests` ships `claude/context/adr`: row 43's
  ADR-0013 key pin reads it (§6 entry 215). A request whose suites load
  `bin/` ships `bin/` for the same reason.
- Model identities in wave 11's records: the micro and row 43's session
  `anthropic:claude-opus-5.5`, row 122's `anthropic:claude-opus-5-5`;
  stemwell's workers `anthropic:claude-opus-5-5`, but wave2a's
  `anthropic:claude-opus-5.5`. The 006 desk's surface showed Claude
  Fable 5.1, `anthropic:claude-fable-5-1` as the brief spells it. Both
  spellings follow ruling 4 from different sources, the picker's name
  ("Claude Opus 5.5") and the API model string (`claude-opus-5-5`);
  AGENT.md §11.7's column names the picker, and the §3 registry's §11.7
  entry carries the question.
- Stemwell, the 45 arc's repo: `/home/chordsphere/stemwell` on the
  operator's WSL2 host, bale 0.4.45, its `bale.toml` setting `[identity]
  packer = "chordsphere"`, `[validation] base =
  "claude/checkpoints/{sid}.sh"` and `[sandbox] network = false`;
  `/usr/bin/python3` is 3.12.3 with `tomllib` and there is no
  `python3.10` (wave3's probe); the operator's shell locale is C-type
  (the upward report). `bale pack --context` wrote its snapshot to
  `.bale/outbox/context-stemwell.tar.gz`, mode 0600 (close 19's probe).
  The arc's notes.md and records are committed in stemwell; bale-src
  holds the upward report alone.
- The friction-points arc (2026-10-03/04) was bumpless on 0.4.45: five
  workers, five first-pass applies, every record `bale_version` 0.4.45.
  The whole-suite counts the workers reported on their partial
  `context/` trees: 1621 at A's baseline, 1694 after B, 1739 after C,
  1778 after D, each with the same baseline failures (six; seven in A's
  count) from files no request shipped (`claude/changelog/`, ADR-0013,
  the repo `bale.toml`, and for A the repo `README.md`); the
  install-side `validate.sh` 94/94 after D. From E every request carries
  `BALE_HELP.md` beside the five docs and two tools, about 77 KB at
  0.4.45, 19 help sections after D's `clipboard` verb; close 20's
  request carries it, and `contract_docs` in the arc's records moved
  twice, `docs/AGENT.md` `dd22b82c…` to `5124250b…` and
  `docs/TARBALL.md` `59ece7fd…` to `004d4389…` at E; close 20's request
  carries TARBALL.md at `f6c3326e…`, D having edited its §4.3. `[probe]
  clipboard_command` is both-layer since C; D copies every operator-side
  paste block when it resolves. Model identities in the arc's five
  records: `anthropic:claude-opus-5-5` on every one. Close 20's base
  `claude/MASTER.md` was 12,476 lines, `4b45a684…3eb8`, matching the
  cleanup desk's probe prefix, before it inserted; the operator's tree
  at that probe was `main` at `8f0bbc4`.
- The cleanup desk's wave (2026-10-04 to 06) was bumpless on 0.4.45,
  every record's `bale_version` 0.4.45; 0.4.46 is dispatched as
  `2026-10-06-bump-0-4-46` beside close 21, not landed. The whole-suite
  counts the workers reported on their partial `context/` trees:
  log-hold 1796 in discover form, seven failing there as on the
  unmodified tree, for `bale.toml`, `claude/changelog/`, the ADR-0013
  file and the repo `README.md`; the rename 1834 in full default
  discovery, 47 slow-gated skips, and 1834 passing with
  `BALE_TEST_SLOW=1`, `validate.sh` 94 checks; convergence and close 20
  none. `docs/TARBALL.md` stands at `32680c8e…` in the close desk's
  request and close 21's, after the rename's edit, from close 20's
  `f6c3326e…`; the other four `contract_docs` are unchanged. bale-src's
  own `bale.toml` still spells `[probe] clipboard_command`, which `bale
  status` reads "via the legacy [probe] clipboard_command" and the
  operator's next `bale config init` moves to `[clipboard] command`.
  Model identities on the wave's four records: log-hold and convergence
  `anthropic:claude-opus-5-5`, close 20 and the rename
  `anthropic:claude-fable-5-1`. Close 21's base `claude/MASTER.md` was
  13,305 lines, `b1ed2936…ddf2`, matching the close desk's carried copy
  and the request's `base_files`, before it inserted.

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
