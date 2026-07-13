# bale master-session state — v3 — 2026-07-13

Handoff document for the bale-src master session. Purpose: re-seed a
fresh master-session chat with zero loss. To use: state current
progress against this file and continue. Regenerate at major
milestones. Supersedes the v2 (2026-07-09) doc entirely; nothing from
it needs to be carried separately. This regeneration (2026-07-13,
session master-state-deltas) supersedes nothing structurally — same
v3 doc, deltas applied in place.

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

Version at sitting close: 0.3.6 — verify with bale --version at the
next sitting's start rather than trusting this line.

**Carried loose end (from v2): CLOSED 2026-07-13.** The
generated-artifacts-rule session's notes.md was relayed to the master
and ratified retroactively — all decisions ratified as shipped. The
pass-path aggregate-line follow-up was declined (byte-identical
output wins); the craft_response fixture-seed proposal is absorbed
into board item 11.

## 3. In flight

Session `master-doc-landing` has APPLIED — verified against the
repo: `claude/MASTER.md` present with its `INDEX.md` entry, the
TARBALL.md §5.7 amendment in place, bale 0.3.6.

Currently open — scope-disjoint and running concurrently, the second
live concurrency exercise:

- `staging-from-target-base` (board item 1) — packed and building.
- `master-state-deltas` (this session) — the doc-edit session that
  landed this regeneration.

## 4. The board

Ordering is the recommended sequence; small sessions first, the
compression sitting before harness scoping.

1. **staging-from-target-base** (small; good first session of the
   next sitting) — opt-in staging strategy materializing the target
   tip's tree (git archive) plus declared untracked inputs, closing
   the validation-fidelity gap: staging copies the WORKING TREE while
   commit/merge build against the TARGET TIP, so a diverged checkout
   means validation exercised different content (apply already logs a
   note when HEAD != target tip). Scope: bale_staging.stage_response,
   BALE.md §8.3. Worker-proposed, master-ratified.

2. **drift-to-contract apply gate** (small; second session) — apply
   pre-flight rejects any changes[] path outside the session's OWN
   scope by default, with an explicit operator override for
   legitimate cases. Converts stay-in-the-lane from policy to
   contract exactly where trust starts depending on it. Rationale
   (008 audit): own-scope drift × concurrency = silent clobber — two
   sessions drifting into the same unclaimed file pass every ADR-0007
   gate and the second whole-file overlay clobbers the first under a
   clean no-ff merge. This is the one hole in an otherwise mechanical
   fence; close it before the trust ledger grants merge autonomy.
   Ride-along: the created-collision rejection ("declared created but
   existed pre-apply") should name the likely sibling cause in its
   message — today it is safe but cryptic.

3. **pack no-brief guard** (small UX) — bale pack should warn or
   require an explicit --no-readme when neither the wizard nor
   --readme-file supplies prose context. Rationale: briefless packs
   are a recurring failure class (evidence 11). Could ride with
   telemetry or stand alone.

4. **Feedback telemetry + response lint** (prerequisite to stats;
   design constraints ratified 2026-07-13, §5) — EVERY response
   carries a structured feedback block, and the schema is
   DUAL-STREAM from day one:
   - **Mechanical stream** — derivable by bale or the lint from
     artifacts it already has: response kind; probe/clarification
     occurred and at what point; **claim/verdict agreement per check
     (promoted from `.bale/logs/` to a first-class, durable field —
     today the richest calibration signal in the system evaporates
     into transient logs)**; includes shipped vs actually touched;
     validation exit state.
   - **Self-reported stream** — worker-authored: assumptions
     proceeded on, judgment calls awaiting ratification, budget
     pressure, includes missing.
   - **Provenance stamped on every response from day one:** model
     identity, contract-docs version/hash (bale stamps the injected
     globals at pack time — they are unversioned today and
     longitudinal data can't be re-segmented retroactively), packer
     identity (the telemetry grades PACKERS as well as workers —
     evidence 11 and 14 are packer-attributed), and work class.
   - **Companion deliverable: `tools/response_lint.py`**, injected
     into every request beside the four global docs. Runs TARBALL.md
     §10.1 step 10 mechanically before pack: recompute size/sha256
     against files/, verify files/ ↔ changes[] both directions, check
     claims ⊆ validation_will_run verbatim, schema-validate the
     manifest. The invariants already exist in bale_validate.py; this
     is a repackaging so the WORKER can run them without bale
     installed. It computes the mechanical stream, catches
     compaction-corrupted manifests at the source, and gives a future
     orchestrator a machine-checkable artifact to demand before
     apply. TARBALL.md prose (§5.2.1, most of §10.1, half of
     CLAUDE.md §11.6) then shrinks to "run the lint" — bank that in
     the compression sitting (board 7).
   This sitting's incident list (evidence 11–14) is the founding
   evidence for the field set. Master writes the brief when reached.

5. **bale stats / the trust ledger** — aggregates diagnostics,
   clarifications, and telemetry into per-work-class rates; gates all
   autonomy grants. Design constraints (ratified 2026-07-13, §5):
   **autonomy grants weight the MECHANICAL stream; the self-reported
   stream is itself a calibration target**, cross-checked against the
   mechanical one — honest self-reporting is something a work class
   earns trust FOR, never the substrate trust rests on. (The
   self-oracle test, evidence 16, applied to the ledger itself.)

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

7. **Doc compression sitting** (dedicated; before harness scoping) —
   the injected globals total ~155KB; the every-tarball-session tax
   (CLAUDE.md + TARBALL.md) is ~105KB ≈ 25K tokens of contract
   ingestion per worker, a per-worker cost that scales linearly with
   the fleet and is itself a compaction driver. Organizing principle:
   split each doc into NORMATIVE (rules, shapes, triggers — stays
   injected) and JUSTIFICATORY (the why — moves to ADRs or a project
   explainer, reachable by drill-down when a rule is challenged).
   Named targets from the 008 sweep:
   - CLAUDE.md §11.2: ~950 words defending the pre-flight check, the
     throughput argument made twice; normative content is ~250 words.
   - The expects_probe:no collision logic stated in TARBALL.md §3.3,
     §4.1, §5.9, §5.9.1, §10.2, §10.3 — one home (§3.3), bare
     pointers elsewhere.
   - The self-oracle / no-runnable-commands rationale argued in full
     in §3.4, §5.4.1, §5.5, and INDEX.md's routing note — one home
     (likely an ADR), rule stated flat elsewhere; §5.5's tombstone
     shrinks to three lines.
   - §5.6.3 and §5.9.3 are apply-time UX contracts FOR BALE that the
     worker reads every session and can never act on — move to
     BALE.md §8/§11; one line each stays in TARBALL.md.
   - Bank the response-lint prose savings from board 4.
   Target: 35–45% reduction of CLAUDE.md + TARBALL.md with zero
   normative loss. Section numbers are stable per DOCS.md §6.4 —
   compress in place, tombstone what moves.

8. **bin/bale docstring prune** (small) — the top docstring is a
   661-line / 41KB append-only version narrative: a changelog living
   in code, 11% of the file, in direct violation of CLAUDE.md §7
   ("git is the changelog") and CODE.md §2 (docstring = job + index).
   Every bale-src request that includes bin/bale pays ~10K tokens for
   history no session drills into. Cut to job + index header;
   narrative to a CHANGELOG.md or nothing (it already exists in git
   and session notes). Dedicated small session, or rides a
   bin/bale-touching session as a declared opportunistic prune.

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
    it.
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

## 7. Standing environment facts

- Architect on WSL; Windows Downloads at
  /mnt/c/Users/chord/Downloads/. Files saved via browser may carry
  CRLF: sed -i 's/\r$//' <file> if bale or a worker complains.
- A post_pack hook copies request tarballs to Downloads.
- Repo: ~/bale-src. bin/ modules: bale (monolith, shrinking),
  bale_config, bale_validate, bale_staging, bale_report,
  bale_rollback, _bale_toml. bin/bale imports bale_config,
  bale_validate, bale_staging, bale_rollback at LOAD — see evidence
  pile 13 before scoping any include set that must execute it.
- This document: `claude/MASTER.md` in the repo once
  master-doc-landing applies. Include it in any session that needs
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
