# Board 6 arc — upward report (2026-08-05, from the board-6 design/orchestration session)

Session `2026-08-04-board-6-blind-checkpoint-design-003` (read-only),
reporting on the split it handled. Board 6 is complete and closeable
on the record: the §1 floor's "validation checkpoints are authored
blind" line now has its implementation — home, execution, gate,
blindness enforcement, and ledger read side. Version moved 0.3.27 →
0.3.29 across the arc (sessions A and B landed unbumped at 0.3.27;
cadence resumed at C per your disposition, recorded in C's notes —
version claims below are from session notes, not tree-verified from
this seat). Everything below is landed, ratified at this level,
escalated to you, or on watch with a named re-trigger.

## What landed (four sessions, all applied, none reverted)

1. `2026-08-04-board-6-checkpoint-core-004` — the checkpoint core:
   `[validation] base` (project-only per disposition 1, full wizard
   trio), base-tree blind execution (`git show` at the target tip;
   both materialization halves — mode restore AND interpreter
   invocation), attribution across log bands / walkthrough / json /
   telemetry, the always-stamp `checkpoint` field homed in the
   telemetry builder, schema additive field. `bin/bale` untouched
   (module layout already satisfied the D7 wiring forecast).
2. `2026-08-04-board-6-superset-gate-005` — `[validation] required`
   (flat list, canonical list walk), §8.1 step 15 with
   `--allow-missing-required-check` on apply and retry, the
   `required-check-refused` outcome + the stats in-flight membership
   line riding together (the endorsed coordination rider),
   refusal/override telemetry rows, dry-run prediction including the
   sanctioned dangling-refusal rider from A's notes.
3. `2026-08-04-board-6-blindness-enforcement-006` — pack-side
   covering refusal at pre-sid pre-flight with
   `--allow-checkpoint-in-scope`, the provenance stamp
   `{path, sha256}` with `checkpoint_scope_admitted` as a
   uniform-shape sibling, apply-side verification reading the
   **registry copy** of the stamp (a doctored response cannot forge
   the oracle's identity), three divergence shapes under one refusal
   naming which 'before' it saw, removed-oracle log-not-refuse,
   the response-manifest provenance-echo widening (load-bearing
   schema coordination rider — without it every post-C response
   fails validation), §11 rows 27–28, the §11 header true-up rider,
   VERSION 0.3.28.
4. `2026-08-05-board-6-stats-read-side-001` — per-class checkpoint
   keys and coverage row with names fixed in their one home
   (`format_stats_json`'s docstring), required-check surfaces as
   counts per the drift precedent, nine-record fixture extension
   exercising every D7 shape, both session-C riders (§11 row 29 for
   A's dangling refusal; the retry-path E2E pinning the
   rejected-retry telemetry shape), VERSION 0.3.29.

## Ratified at this level (contest any)

Grouped by kind. **Siting:** A's dangling refusal at §8.2's base
resolution, documented in §8.5 (needs `base_sha`; §8.1's steps don't
have it) — C's stamp verification followed the same precedent, with
§11 row 28 carrying the contract entry; B's step 15 sits logically
after 14, physically where the anchors-are-logical posture allows.
**Vocabulary and homes:** apply-json `checkpoint` mirrors the
telemetry stamp's vocabulary rather than minting a third; the
always-stamp epoch semantics live in the telemetry builder; every
wire-name list stayed in its owning docstring. **Behavior calls:**
both materialization halves so neither can rot silently; the worker
band written by the checkpoint runner (unconfigured logs
byte-identical, suite-pinned); strict-shape/tolerant-duplicates
config accessors; the rider blast radius including the honest
degenerate-state dry-run refusals on checkpoint-configured projects;
the double `merged_config` read (stage-time re-resolution is
documented structure); removed-oracle logs loudly rather than
refusing (the D5 residue read as written — re-trigger below);
checkpoint exit-2 folds into checkpoint-HOLD at the stats v1.
**Recorded limitations:** colon-bearing check names can't enter via
the wizard's list walk (hand-edit works; no existing convention
collides); `bale-internals.md` §2.5 untouched per the
[staging]/[identity] snippet precedent (policy-or-accident question
queued below). One live instance of the claim-basis precedent
occurred: session A's packaging-suite claim was predicted on
disclosed structural grounds (its sandbox lacked the suite's
scripts), split out for attribution, and graded `agree` at apply —
the precedent working as ratified, and one more datum for the
measurement gap now on board 10's desk.

## Escalated to you

1. **The execution-context contract amendment, amended form.** Two
   include-gap instances of the same species (A: `scripts/build.sh`
   + `install.sh`; B: `tools/craft_response.py`) show the ratified
   set's enumeration is the bug. Proposed wording tracks the rule:
   the set covers every `INJECTED_TOOLS` member plus the scripts the
   suite executes (or: all of `tools/`, `scripts/build.sh`,
   `install.sh`). Evidence: A was forced into a predicted claim;
   B–D, packed with the per-pack adoption, ran fully observed.
2. **The handoff covering question** (from C's notes, verbatim text
   in the arc directory). A handoff whose reading-plan scope covers
   the checkpoint silently re-opens the layer-1 hole. My lean: run
   `checkpoint_blindness_preflight` on the handoff path with a
   mirroring per-invocation admission flag — the rare legitimate
   case (a bailed checkpoint-maintenance session) was already
   flag-admitted once at pack, and a flat refusal strands exactly
   that handoff. The flag question is yours under the typed-surface
   contract.
3. **Two doc deltas awaiting the master-deltas vehicle**, both
   ratified 2026-08-04: the TARBALL.md §7 blind-checkpoint sentence
   (wording as drafted in the rev B brief; sequenced after A, which
   has landed — the vehicle can carry it now) and the MASTER.md §3
   watch re-owner note (claim-basis → board 10).
4. **The operator-friction arc** — the architect has directed a
   dedicated read-only master session to dispose it in discussion
   before delegation; the authored-and-shelved archival pack
   command's disposition transfers to that session. Findings feeding
   it are below.

## On watch (named re-triggers, no work)

- Removed-oracle residue: flips log-to-refusal on the first observed
  worker-authored edit to `[validation]` keys in a merged session
  (C's else-branch note makes it ~10 lines).
- `[validation]` layering: the deferred widening re-triggers only on
  a case that answers oracle-by-coincidence (disposition 1's trade,
  recorded in the rev B brief's D1).
- Required-set keyed form: re-triggers on systematic per-class
  `[SKIP]` noise in the ledger's new rows.
- Claim-basis measurement gap: board 10's, per the rev B brief's
  D4.3 reasons; the exit-2 split proposal (D's notes) rides the
  same desk.
- `bale-internals.md` §2.5 true-up: whether the
  snippet-not-extended precedent is policy or accident — a small
  doc session's question; B and C followed it consistently in the
  meantime, so the eventual true-up is a single sweep.

## Process findings against my own orchestration (five; two closed in-arc)

1. **Multi-line command blocks fed to a paste-hostile terminal.**
   The session-B precondition's three-command block ran as one line
   and tar consumed the git commands as member names. Corrective,
   adopted mid-arc: the single-line rule extends from pack commands
   to every operator command I emit — one command per block, or an
   explicit `&&` one-liner when the operator asks for one paste.
2. **The mode-bit chase: instances of a class problem.** Two chmod
   rounds for drift the WSL mount re-imports on every copy.
   Corrective, closed at the source: `/etc/wsl.conf` automount
   metadata options, verified 644 on the mount. Lesson recorded:
   when the second instance of a drift appears, fix the class, not
   the file.
3. **The git dance itself.** Three extract-rename-commit rounds per
   arc to land worker notes as pack context. The extraction half is
   bale's to absorb — the `archive_dir` candidate already designed
   in BALE.md's v0.5 list is the fix; the commit half is the
   operator's by design and folds into the telemetry sweep.
   Disposition transferred to the new master session at the
   architect's direction.
4. **D7's execution-context sentence named sessions A–C; D needed
   the set too** (its E2E riders execute `bin/bale`). Caught at
   pack authoring, cost nothing — but the amended contract wording
   in escalation 1 is what prevents the class, tracking the rule
   rather than the enumeration.
5. **A redundant session was packed against a tree that had moved
   past its goal.** After an instruction-ordering slip (a
   must-run-later command stacked paste-ready below a
   must-run-first one — my emission), the operator's picture of
   the tree fell one session behind the tree itself, and session
   D's pack command was re-pasted after D had already applied and
   the reinstall hook had installed 0.3.29. The stale goal rode
   forward; the worker receiving it verified the tree against the
   goal, ran the suite, refused to fabricate a change set, and
   asked — the misunderstanding-control doctrine functioning live,
   at the cost of one burned NNN and one unlock. Correctives: the
   single-paste rule gains its pair — commands for different
   phases never share a message — and the friction session's
   charter gains operator state legibility (`bale status` as the
   ground truth consulted before any pack when state is uncertain,
   which is a tooling-surface question as much as a discipline
   one).

## Residual close-out

This design session closes read-only at the next read-only pack's
sweep — the architect's new master pack will trigger it; accept the
default — or `bale unlock 2026-08-04-board-6-blind-checkpoint-design-003`
now. The redundant `2026-08-05-board-6-stats-read-side-003` session
(finding 5) closes by operator unlock with no successor and nothing
landed; its telemetry closure record is the durable trace. After
both: board 6 closeable on the record; the MASTER.md board-6 row
update rides your next deltas landing per the v4 convention,
consuming this report; the two ratified doc deltas await the same
vehicle. Nothing else is open or queued from this desk.
