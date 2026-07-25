# bale master-session state — v3 — 2026-07-25

Handoff document for the bale-src master session. Purpose: re-seed a
fresh master-session chat with zero loss. To use: state current
progress against this file and continue. Regenerate at major
milestones. Supersedes the v2 (2026-07-09) doc entirely; nothing from
it needs to be carried separately. This update (2026-07-22, session
2026-07-22-master-deltas-001) supersedes nothing structurally — same
v3 doc, deltas applied in place. This update (2026-07-25, session
2026-07-25-orchestrator-sesh-001) is likewise deltas-in-place, and is
the first landed by the master session itself rather than a separate
deltas worker. This update (2026-07-25, second sitting)
is deltas-in-place, landed by session 2026-07-25-master-deltas-005 —
a narrow follow-on pack, because the orchestrator session (sesh-002)
could not land its own response; see the second-sitting summary and
evidence 36.

**Home change, effective this version:** this document lives IN the
repo at `claude/MASTER.md`, landed by session `master-doc-landing`
and listed in `INDEX.md`. Regenerate = edit in place; git keeps the
history; the dated-filename-carried-in-Downloads convention is
retired. It is a project doc, not a global workflow doc — see §5 for
the categorization contract.

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

**The concurrency arc is COMPLETE** (v2 milestone, carried). ADRs
0006, 0007, 0008 Accepted and landed: per-sid registry, scope
disjointness (pack-time include-intersection refusal + apply-time
sibling-scope collision rejection), checkout-free integration,
per-sid staging with ownership-by-open-session cleanup. Condensed
pre-v2 history lives in git and the session archive; contracts from
it are §5.

**New since v2 (all 2026-07-13):**

- **The agent-driven direction is RATIFIED as ADR-0012** (Accepted at
  creation): bale is a substrate an orchestrating Claude can drive.
  Standing commitments now citable: transport-agnostic CLI,
  role-neutral planner/worker/operator language, manual workflow as
  fallback and ground truth. Complements ADR-0009 (doc plan and
  promotion triggers unchanged). Durable record of the architect's
  statement: request README of session 2026-07-13-multi-agent-docs-007.
- **Concurrency exercised live:** three scope-disjoint sessions
  packed, built, and applied concurrently on bale 0.3.6 — the
  ADR-0006 registry and both ADR-0007 gates end to end under a human
  operator. This is the "proven by hand before any harness consumes
  it" model executing.
- **Audit cleanup session:** the 0006/0007 and 0010/0011 status flips
  reached the ADR files themselves (0010/0011 on the architect's
  explicit scope override, probe-confirmed); ADR-0012 recorded in the
  same session.
- **Foundation audit (session 2026-07-13-self-aware-008):** a
  discussion-mode meta session audited the system against the §1 goal
  and swept the docs for compression. Verdict: the bones are right;
  the cracks are places where policy-under-one-human doesn't survive
  review bandwidth being the multiplied resource. Findings register
  in §8; every actionable item is absorbed into the board (§4) or the
  landing session.

**Sitting summary, 2026-07-13/14 (this regeneration's deltas):**

- **staging-from-target-base** — landed the target-base staging
  strategy: config-only opt-in, tracked-at-tip guard. (Board item 1,
  now done.)
- **master-state-deltas** — the doc-edit session that landed the
  prior regeneration of this document.
- **response-lint** — `tools/response_lint.py` blind-authored from
  the documented contract, not from bale_validate; 7 doc gaps found
  in the process (feeds board 7's input pile).
- **telemetry B1** — provenance stamping, the dual-stream feedback
  block, the no-readme guard, six doc one-liners.
- **telemetry B2** — durable records at `claude/telemetry/`, bailout
  records included; contract at BALE.md §8.9.
- **packaging-lists** — three runs: two compacted mid-build (both
  notes ratified as design input), the third implemented the
  master-pinned design: canonical RELEASE_FILES, derived and
  asserted copies, tree-coverage guards, tools/ mirror.

Version at sitting close: 0.3.9 per the pack-time provenance stamp,
plus whatever packaging-lists-v2 set in the repo — verify with bale
--version at the next sitting's start rather than trusting this line.

**packaging-lists-v2 notes.md ratification: CLOSED 2026-07-14.** The
notes were relayed and ratified in the closing master chat
(architect-stated at pack time). No carried loose end for the next
master.

**Carried loose end (from v2): CLOSED 2026-07-13.** The
generated-artifacts-rule session's notes.md was relayed to the master
and ratified retroactively — all decisions ratified as shipped. The
pass-path aggregate-line follow-up was declined (byte-identical
output wins); the craft_response fixture-seed proposal is absorbed
into board item 11.

**Sitting summary, 2026-07-15 (landed by master-deltas-015):**

- **drift-gate** — board 2 landed: the apply pre-flight own-scope
  gate, a directional scope_covers_path helper (ADR-0007 intersection
  untouched), a per-path `--allow-out-of-scope` override (flag-only,
  no config key — ratified as the agent-operability shape),
  structured json refusal with dispatchable outcome
  `scope-drift-refused`, override paths stamped to mechanical
  telemetry, and the created-collision message now naming the likely
  sibling cause. v0.3.10.
- **status-staging-row** — board 12 landed: per-session staging
  strategy + declared untracked inputs in `bale status`, human and
  json modes, additive keys, effective-config semantics. v0.3.11.
- **bale-status-reconciliation** — rider from 003's clarification
  round: BALE.md section 5 status row + new §5.5, the §2.2 and
  section 5 no-status assertions narrowed to log/blame/diag, the
  one-home rule mechanically pinned in validation (§5.5 may not
  enumerate the json keys).

Version at sitting close: 0.3.11 as of status-staging-row — verify
with bale --version at the next sitting's start per the standing
rule.

**Sitting summary, 2026-07-15/16 (landed by this deltas session,
2026-07-16-master-deltas-004; sids reconciled against
claude/telemetry):**

- **docstring-prune (8a)** — sid `2026-07-15-docstring-prune-005`,
  applied 2026-07-15, v0.3.11 (telemetry: one minute before the
  prior deltas apply, which is why §3's stale in-flight line existed
  as written). Details on the board 8 row; the arc's opening move.
- **pack-path-extraction (8b)** — sid
  `2026-07-15-pack-path-extraction-010`, applied 2026-07-15,
  v0.3.12. bin/bale_pack.py extracted; details on the board 8 row.
- **tarball-ux-extraction** — sid
  `2026-07-15-tarball-ux-extraction-011`, applied 2026-07-15.
  TARBALL.md §5.6.3/§5.9.3 apply-time UX contracts moved to BALE.md
  §8.10; tombstones left in place; the inbound §5.2 reference
  retargeted.
- **tarball-compression** — sid
  `2026-07-15-tarball-compression-012`, applied 2026-07-15.
  TARBALL.md 75,148 → 71,487 bytes (−4.9%); ADR-0013 created,
  Proposed.
- **claude-preflight-compression** — sid
  `2026-07-16-claude-preflight-compression-001`, applied 2026-07-16.
  CLAUDE.md §11.2 compressed 925 → 397 words (−57%; whole file
  −9.4%); INDEX.md gained the ADR-0013 entry, the shrunk routing
  note, and the coherence-edited Proposed-set prose.
- **apply-path-extraction (8c)** — sid
  `2026-07-16-apply-path-extraction-002`, applied 2026-07-16,
  v0.3.13. bin/bale_apply.py extracted; details on the board 8 row.
  Closes the shrink-bin/bale arc.
- **This deltas session** — sid `2026-07-16-master-deltas-004` —
  lands these deltas into this document. Its apply is the first run
  of the extracted bale_apply pipeline (v0.3.13), deliberately: a
  one-doc session is the low-stakes smoke test session 010 asked
  for; the architect observes, nothing rides on the worker side.

ADR-0013 status at sitting close: **Proposed, with its work already
landed** — the DOCS.md §9 status flip is the architect's to make and
is pending by choice; INDEX.md prose already reflects this state.

Version at sitting close: 0.3.13 as of 2026-07-16
(apply-path-extraction) — verify with bale --version at the next
sitting's start per the standing rule.

**Fold-in registry (2026-07-16):**

- BALE.md §8.9 outcome-list sentence (`scope-drift-refused`) +
  drift-refusal aggregation semantics → board 5's session
  (unchanged).
- INDEX.md's ADR-0013 "Status: Proposed" word flips when 0013 is
  Accepted — per the 2026-07-21 ratification (§5); board 14 retired
  2026-07-25, so the flip now rides board 22a's session alongside
  the ADR's own status line. [Cleared 2026-07-25: landed with 22a.]
- run_hook's three placeholder-less f-strings — rides any session
  touching bin/bale section 23. Cosmetic.

Cleared this sitting: the BALE.md §13 status sentence (rode 8a) and
the bale-internals refresh (rode 8b and 8c).

**Sitting summary, 2026-07-21 (landed by this deltas session,
2026-07-22-master-deltas-001; sids reconciled against
claude/telemetry):**

- **doc-gap-landing (7c)** — sid `2026-07-21-doc-gap-landing-002`,
  applied 2026-07-21. Board 15 DONE. Gaps 2, 5, and 6's schema half
  landed; gap 3 found already landed (the fingerprint grep
  false-negatived on wrapped prose — evidence 28); gap 4 skipped as
  adequately placed (the §10.1 home is the same target the lint's
  DUPLICATE_PATH finding cites). Deliberately tripped the lint's
  embedded-schema drift guard, as designed.
- **transition-branch-retirement (board 16)** — sid
  `2026-07-21-transition-branch-retirement-003`, applied 2026-07-21.
  Board 16 DONE. resolve_target_branch's no-stamp fallback →
  refusal; the discard path is switch-only. Ratified in passing:
  git-decides dirty-checkout semantics (WIP never discarded — §5);
  three in-lane comment updates declared and accepted. The sid_sha
  short-circuit was deliberately deferred (proposed, not swept in);
  retirement-cleanup took it.
- **lint-schema-refresh** — sid `2026-07-21-lint-schema-refresh-004`,
  applied 2026-07-21. Cleared the drift guard doc-gap-landing
  tripped: byte-verbatim embed of the shipped response-manifest
  schema (parsed-JSON *and* byte-level equality asserted); install
  validation confirmed green.
- **retry-flag-parity** — sid `2026-07-21-retry-flag-parity-005`,
  applied 2026-07-21, v0.3.14. The retry ice-out fix, surfaced by a
  live ice-out on another project: an apply with
  `--allow-out-of-scope` went HOLD, and retry had no such flag —
  the session was iced exactly when the override was needed
  (evidence 29). Closed `--allow-out-of-scope`, `--verbose`, and
  `--json` on retry; `--dry-run` and `--show-*` skipped with
  justification. VERSION bumped 0.3.13 → 0.3.14. The override stays
  per-invocation, structurally uncarried (§5).
- **retirement-cleanup** — sid `2026-07-21-retirement-cleanup-007`,
  applied 2026-07-21. The sid_sha short-circuit retired (equal-SHA
  now correctly refuses as merged), stale fallback prose swept, the
  detached-HEAD pack refusal landed, stale pipeline docstring
  sentences corrected. **Master review caught a defect the session's
  own checks could not:** the refusal was inserted as BALE.md §7.1
  step 5, renumbering the scope gate to 6 — but "§7.1 step 5" is
  cross-referenced as the scope gate from INDEX.md and from
  immutable git-history manifest reasons. Applied as shipped;
  corrected by handoff-refusal-numbering. (Feeds the board 6
  annotation and evidence 31.)
- **handoff-refusal-numbering** — sid
  `2026-07-21-handoff-refusal-numbering-008`, applied 2026-07-22.
  Restored §7.1 numbering: the scope gate back to step 5, the
  detached-HEAD refusal relabeled as interstitial step 4a with an
  inline stable-numbering rationale. Extended the detached-HEAD
  refusal to `bale handoff` (§11 row 24), and extended three
  refusal-citing passages to name both request-building pre-flights.
  The worker's read-only verification corrected the master's brief:
  ADR-0007's body carries no step citation — the citation lives in
  INDEX.md's entry (and git history); the ADR cites only §11 row 3,
  unaffected throughout (evidence 31).
- **This deltas session** — sid `2026-07-22-master-deltas-001` —
  lands these deltas into this document.

Version at sitting close: 0.3.14 as of retry-flag-parity; the two
later applies (retirement-cleanup, handoff-refusal-numbering) stamp
0.3.14 provenance with no further bump in telemetry — verify with
bale --version at the next sitting's start per the standing rule.

**Sitting summary, 2026-07-23/25 (landed by this master session,
2026-07-25-orchestrator-sesh-001; sids reconciled against
claude/telemetry):**

- **doc-gap (ADR-0014)** — sid `2026-07-23-doc-gap-001`, applied
  2026-07-23, provenance 0.3.14 (no bump). ADR-0014 created
  (worker-determined new files; Accepted at creation per the
  ADR-0012 precedent), TARBALL.md §3.2/§3.4 and CLAUDE.md §6
  corrected to the mechanical drift-gate reality, BALE.md's three
  stale sites fixed, INDEX.md row added. Loose end CLOSED 2026-07-25:
  the architect ratified Accepted-at-creation in the sesh-002 chat,
  with the rest of that sitting's ratifications.
- **This master session** — sid `2026-07-25-orchestrator-sesh-001` —
  reconciled state (0.3.14 verified; the request's contract-doc
  hashes match the post-doc-gap bytes), then interrogated board 14
  before authoring its pack and retired it as misframed: the
  physical split's token-savings premise conflated shipped bytes
  with read tokens (evidence 32). Ratified in the same chat: the
  global-doc mechanization direction (board 22; contracts §5). This
  deltas edit ships as the session's own response tarball.

Version at sitting close: 0.3.14, unchanged — verify with bale
--version at the next sitting's start per the standing rule.

**Sitting summary, 2026-07-25 second sitting (landed by this master
session, 2026-07-25-orchestrator-sesh-002; applied-state facts
reconciled from the architect-relayed notes.md and apply
confirmations — see this response's notes for the caveat):**

- **handoff-install-precheck (board 21)** — sid
  `2026-07-25-handoff-install-precheck-003`, applied 2026-07-25,
  provenance 0.3.14 (no bump; verify per the standing rule). main()'s
  install sanity check widened in place to both request-building
  commands; byte-for-byte message-parity asserted in the test so a
  future reword forks loudly; BALE.md section 5.4 gained the
  no-force-override clause for the detached-HEAD refusal. **First
  tracked test suite landed:** tests/test_install_precheck.py
  (stdlib unittest, no runner config; ADR-0005 sandbox doctrine;
  harness inline pending a second suite), admitted per ADR-0014 via
  --allow-out-of-scope. Negative control against unmodified bin/bale
  confirmed the suite pins the gap (evidence 27's paired shape).
- **tarball-core-first (board 22a)** — sid
  `2026-07-25-tarball-core-first-004`, applied 2026-07-25. Core =
  sections 1, 2, 5, 7; reference sections past a banner in numeric
  order; zero renumbering, two tombstones, sorted line-set diff as
  the zero-loss proof. ADR-0013 flipped Accepted via the sanctioned
  two-line diff with a reverse-transform hash assertion (evidence
  35); INDEX.md coherence swept; DOCS.md section 9 gained the
  CLAUDE.md 11.2 / TARBALL.md 3.4 sanctioned pair (board 17) and the
  grep-normalization paragraph (evidence 28's rider — section 9
  placement was the worker's call, ratified over the brief's 7.4
  candidate).
- **Ratified in the sesh-002 chat:** ADR-0014 stays
  Accepted-at-creation (the doc-gap loose end, closed above);
  ADR-0005's Accepted flip, riding the queued test-layout-docs
  session (board 23); every worker decision of both sessions, as
  shipped.
- **Master error on the record:** the 003 brief miscast a telemetry
  claim label as a tracked test-file precedent; cost the worker a
  probe round (evidence 34). The reconcile-the-precedent proposal
  closed as nothing-to-find — the new suite is now the first real
  tracked precedent.
- **This master session** — sid `2026-07-25-orchestrator-sesh-002` —
  interrogated 21/22a disjointness and refused it (execution-context
  manifest's docs/ include intersects 22a's doc writes; evidence 25
  annotated), serialized 21 before 22a with rationale stated for
  contest, and authored both packs and briefs plus board 23's.
  **Correction on the close-out:** the session's own whole-tree
  request was the registry's blocking lock — every worker pack it
  authored was inadmissible under ADR-0007 until the architect
  unlocked sesh-002 (friction absorbed silently; the master checked
  the workers against each other and never against its own scope) —
  and the unlock left the session's self-landed deltas response with
  no lock for responds_to to match. These deltas ship instead under
  the narrow follow-on session `2026-07-25-master-deltas-005`
  (evidence 36).

Version at sitting close: 0.3.14 per both requests' pack-time
provenance (sesh-002 and master-deltas-005 alike); verify with bale
--version at the next sitting's start per the standing rule.

## 3. In flight

- **This session** (`2026-07-25-master-deltas-005`) — the narrow
  deltas session landing this edit; every worker session the sitting
  spawned (boards 21 and 22a) is applied. Sesh-002 itself closed by
  unlock, not apply (evidence 36) — abandoned in the registry by
  design, its work carried entirely by the worker sessions and this
  doc.
- **Authored, not yet packed:** board 23 (test-layout-docs) — pack
  command and brief delivered at sitting close; runs before 22b.
- **Open micro-item:** master editorial review of 22a's new
  read-paths trigger rows (sections 3 and 8), deferred because the
  restructured bytes postdate this session's context. Rides the next
  TARBALL.md-touching session (22b's brief authoring reads the doc
  whole anyway) or a quick chat paste, whichever comes first.

## 4. The board

Ordering is the recommended sequence; small sessions first, the
compression sitting before harness scoping. Item numbers are
identities, not sequence — they are cross-referenced from §5, §6,
and §8, so done items keep their numbers as one-line pointers.

1. **staging-from-target-base — DONE** this sitting (§2 summary):
   target-base strategy landed, config-only opt-in, tracked-at-tip
   guard.

2. **drift-to-contract apply gate — DONE** 2026-07-15 (§2 summary):
   own-scope apply gate landed, v0.3.10.

3. **pack no-brief guard — DONE** this sitting (rode telemetry B1;
   §2 summary): the --no-readme acknowledgment, TTY/piped split per
   BALE.md §7. The evidence-11 failure class now has its mechanical
   counter.

4. **Feedback telemetry + response lint — DONE** this sitting, in
   three sessions (§2 summary): response-lint (the blind-authored
   lint, injected per request), telemetry B1 (dual-stream feedback
   block + day-one provenance stamping, per the §5 constraints), and
   telemetry B2 (durable records at `claude/telemetry/`, BALE.md
   §8.9). The response-lint prose savings still bank in the
   compression sitting (board 7).

5. **bale stats / the trust ledger** — aggregates diagnostics,
   clarifications, and telemetry into per-work-class rates; gates all
   autonomy grants. Design constraints (ratified 2026-07-13, §5):
   **autonomy grants weight the MECHANICAL stream; the self-reported
   stream is itself a calibration target**, cross-checked against the
   mechanical one — honest self-reporting is something a work class
   earns trust FOR, never the substrate trust rests on. (The
   self-oracle test, evidence 16, applied to the ledger itself.)
   Notes from this sitting: dataset row one is packaging-lists-v2 —
   the first apply after B2; aggregation should expect attempts[]
   append semantics and reconciliation_parsed disambiguation per
   BALE.md §8.9. Rider: a bailout banner telemetry row (ratified
   trivial).

6. **Blind validation checkpoints — doctrine to mechanics** — the §1
   floor's "validation checkpoints are authored blind" line has no
   implementation; land one: a planner-pinned `validation.base.sh`
   per project (or a `[validation] required = [...]` table in
   bale.toml keyed by touched file types), run unconditionally in
   staging with the worker's script ADDITIVE, plus an apply pre-flight
   rule that validation_will_run ⊇ the required set for the touched
   paths. This partially converts "validation_will_run is honest and
   complete" from policy to contract. **Keep the worker's
   validation.sh** — it is where claims come from and feeds the
   calibration stream; the blind checkpoint is the misunderstanding
   control. They answer different questions (is the worker calibrated
   vs did the worker understand); the ledger consumes both.
   **Motivating evidence, 2026-07-21:** two same-day master-review
   catches — the runtime-loaded include gap and the §7.1
   renumbering — were invisible to in-lane worker checks by
   construction; both are the exact shape a planner-authored blind
   checkpoint exists to catch. Concrete grounding for this item.

7. **Doc compression sitting — editorial phase COMPLETE**
   2026-07-15/16, in three sessions after a ratified split (§2
   sitting summary): tarball-ux-extraction-011 (§5.6.3/§5.9.3 →
   BALE.md §8.10, tombstones + retargeted §5.2 reference),
   tarball-compression-012 (TARBALL.md 75,148 → 71,487 bytes, −4.9%;
   ADR-0013 created, Proposed), and claude-preflight-compression-001
   (CLAUDE.md §11.2 925 → 397 words, −57%; whole file −9.4%;
   INDEX.md updated). The original 35–45% pair target is **RETIRED
   as mismeasured** — see evidence 26. Remaining injection-tax work
   moves to the structural-split item (board 14). The doc-gap input
   pile moves to board 15 (7c).

8. **shrink-bin/bale arc — CLOSED** 2026-07-16, all three sessions
   DONE in the ratified order, serialized on bin/:
   - **8a docstring prune — DONE** (applied 2026-07-15, v0.3.11,
     session 2026-07-15-docstring-prune-005): the 661-line / 41KB
     version narrative dropped per the ratified
     dropped-not-re-homed decision (§5); docstring cut to job +
     index header.
   - **8b pack-path extraction — DONE** (session
     2026-07-15-pack-path-extraction-010, v0.3.12): bin/bale_pack.py
     extracted; sections 11–15 documented banner gap; sibling
     lazy-import idiom refined — sibling-owned entry points imported
     from owning modules, not __main__.
   - **8c apply-path extraction — DONE** (session
     2026-07-16-apply-path-extraction-002, v0.3.13):
     bin/bale_apply.py extracted; bin/bale 5,981 → 4,111 lines;
     straggler helpers homed (git helpers → section 3,
     resolve_inbound_path → section 8, handoff slicers → section 22,
     staging trio → bale_apply); upgrade.sh
     REQUIRED_RELEASE_MEMBERS backfilled including _bale_toml.py.

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
      made here; evidence 32 carries the rationale.

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

12. **bale status staging row — DONE** 2026-07-15 (§2 summary):
    per-session staging row in bale status landed, v0.3.11.

13. **read-vs-write include separation** — a read-only include shape
    that ships context without claiming scope. Motivation:
    includes-as-scope conflates the read set with the write set, so
    read-context includes are concurrency locks AND inflate the
    drift gate's admitted surface; separating them unlocks
    concurrency and tightens the gate to the true write set. Touches
    pack, the registry scope record, both ADR-0007 gates, and the
    drift gate — not small; slot after the compression sitting
    (board 7), before board 5 consumes scope data. (Evidence 25 is
    the observed cost.)

14. **Doc-compression sitting, structural phase — RETIRED AS
    MISFRAMED** 2026-07-25 (this master session, chat-ratified). The
    physical split's premise — a fifth global doc reduces the
    per-session context tax — conflated shipped bytes with read
    tokens; on the human-carried transport the globals are
    lazy-loaded via the read-paths tables and unread bytes cost
    tarball size only (evidence 32). The split decision is
    transport-relative and now waits on board 10's injection-model
    agenda item. Replacement work: board 22. Riders re-homed to
    board 22a (fold-in registry updated): ADR-0013's Accepted flip +
    INDEX.md word flip, the board-17 sanctioned-pairs one-liner, the
    evidence-28 grep-normalization one-liner. The 2026-07-21
    packaging findings (GLOBAL_DOCS tuple at bin/bale 207 with two
    further consumers at ~2135 and ~4426, contract_docs hash set,
    build.sh RELEASE_FILES ~88, install.sh ~229, upgrade.sh
    REQUIRED_RELEASE_MEMBERS ~141, validate.sh doc rows,
    reinstall mirror — re-verified against source 2026-07-25) stand
    as the reference map if board 10 ever revives a physical
    split.

15. **7c — doc-gap audit + landing — DONE** 2026-07-21 (§2 sitting
    summary): gaps 2, 5, 6-schema landed; 3 already landed; 4
    skipped as adequately placed. Closing note: the deliberately
    tripped embedded-schema drift guard was cleared same-sitting by
    the lint-schema-refresh follow-on
    (`2026-07-21-lint-schema-refresh-004`), recorded here rather
    than as its own row, matching how small follow-ons ride their
    parent (cf. board 3).

16. **Transition-branch retirement — DONE** 2026-07-21 (§2 sitting
    summary): no-stamp fallback → refusal, discard switch-only,
    git-decides dirty semantics ratified (§5).

17. **DOCS.md sanctioned-pairs one-liner — DONE** 2026-07-25 (rode
    22a; §2 second-sitting summary): the CLAUDE.md §11.2 ↔
    TARBALL.md §3.4 pair appended to the §9 sanctioned-pairs
    registry.

18. **retry flag parity — DONE** 2026-07-21 (§2 sitting summary):
    retry ice-out fixed; gate override flags closed across the
    lifecycle, v0.3.14.

19. **retirement cleanup — DONE** 2026-07-21 (§2 sitting summary):
    sid_sha short-circuit retired, detached-HEAD pack refusal
    landed; §7.1 renumbering defect caught at master review,
    corrected by board 20.

20. **handoff refusal + numbering restoration — DONE** 2026-07-21,
    applied 2026-07-22 (§2 sitting summary): §7.1 numbering
    restored (interstitial step 4a), detached-HEAD refusal extended
    to handoff.

21. **Extend main()'s install sanity check to handoff — DONE**
    2026-07-25 (§2 second-sitting summary): gate widened in main()
    to both request-building commands, BALE.md §5.4 rider clause
    landed, first tracked test suite shipped with it.

22. **Global-doc mechanization arc (the worker toolkit)** — replace
    instructional prose with shipped tools wherever a rule is shape;
    keep prose only where a rule is judgment. Ratified 2026-07-25
    (contracts §5; evidence 33; the delivery pattern is
    response_lint's — per-request injected, sandbox-run, no install).
    Serialized phases, each its own session:
    - **22a — TARBALL.md internal restructure + riders — DONE**
      2026-07-25 (§2 second-sitting summary): core-first
      ordering under stable section numbers (DOCS.md §6.4 —
      in-file relocation pointers, zero renumbering), a sharpened
      in-doc INDEX read-paths table with a situation-keyed trigger
      sentence per reference section, and a past-the-core banner.
      Doc-only, no code lock. Riders: ADR-0013 Accepted flip +
      INDEX.md word flip, board 17's one-liner, evidence 28's
      one-liner.
    - **22b — craft tool v1, normal-response shape:** a worker-run
      tools/ sibling of response_lint that walks files/, computes
      every size_bytes and sha256, and emits the manifest skeleton
      plus the apply.sh scaffold; TARBALL.md §5.2/§5.2.1 prose then
      collapses to trigger + tool pointer. Board 11's
      craft_response fixture recipe is the seed. Constraints:
      crafter/validator separation — the blind-authored lint stays
      the judge, separately authored and maintained (evidence 16's
      self-oracle test applied at design time); the toolkit is
      self-contained per the §5 execution-context manifest
      (evidence 13/30).
    - **22c — bailout + clarification shapes:** diagnostics.json and
      questions[] emitted from the schemas that already own them;
      §5.6/§5.8/§5.9 shape prose collapses behind the tool.
    - **22d — probe header template and residue:** the §4.2 scaffold,
      then measure what prose remains and stop when the residue is
      judgment. The non-mechanizable residue — probe-vs-guess,
      fit estimates, claim completeness, stay-in-lane — remains
      prose by design; boards 4/5/6 are its control surface, not
      tooling.

23. **test-layout-docs** — ratified 2026-07-25 from session 003's
    Proposals: bale-internals.md gains the test layout (tests/ at
    repo root, stdlib unittest, ADR-0005 sandbox rules, harness
    inline for now) and loses the stale deferred-to-v0.4 sentence;
    ADR-0005 flips Proposed → Accepted in the sanctioned diff shape;
    INDEX.md Proposed-set prose swept (0002–0004 stay Proposed).
    Pack and brief authored at the sesh-002 close; serialized after
    22a (claude/INDEX.md collision) and before 22b (the internals
    doc should describe tests/ before 22b's suite lands beside it).

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
  schemas/, the four global docs under docs/, and
  tools/response_lint.py. Copied, never re-derived. (The
  countermeasure for evidence 30's class.)
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
  time). (Binds board 22.)

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
    trustworthy. (checkout-free-mechanism.)
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
    architect, master, and worker as packer.
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
    priority.

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
    nothing while open.

## 7. Standing environment facts

- Architect on WSL; Windows Downloads at
  /mnt/c/Users/chord/Downloads/. Files saved via browser may carry
  CRLF: sed -i 's/\r$//' <file> if bale or a worker complains.
- A post_pack hook copies request tarballs to Downloads.
- Tests: tests/ at repo root, stdlib unittest, no runner config —
  run python3 -m unittest discover -s tests. First suite
  tests/test_install_precheck.py (2026-07-25); ADR-0005 sandbox
  rules govern; harness inline until a second suite lands (board
  11's deferred extraction).
- Repo: ~/bale-src. bin/ modules: bale (4,111 lines after the
  8a/8b/8c arc), bale_pack, bale_apply, bale_config, bale_validate,
  bale_staging, bale_report, bale_rollback, _bale_toml. Load-time
  import set: pre-extraction it was bale_config, bale_validate,
  bale_staging, bale_rollback; the 8b/8c sessions refined the
  sibling lazy-import idiom, so re-verify the current set before
  scoping any include set that must execute bin/bale — evidence 13
  still governs.
- This document: `claude/MASTER.md` in the repo, tracked and listed
  in `INDEX.md`. Include it in any session that needs
  the gameplan; keep it out of sessions that don't (it is master
  context, not worker context, by default).
- Master-session working style: master authors every pack command and
  README brief (briefs delivered as downloadable files for
  --readme-file); architect pastes, runs, relays worker output
  verbatim; kickbacks and judgment calls come to the master for
  ratification. Notes.md is relayed for EVERY session, including
  post-merge (see the §2 loose end for why this line now exists).
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
