# notes.md — 2026-08-06-v04-selftest-audit-006

Two deliverables in this session: the board-34 checklist-vs-suite
audit (below, the bulk of this file) and the riding citation
fold-in (five one-line edits to BALE.md, the session's only change
surface). Gap disposition is yours; I report and don't recommend
myself into any fix.

## How the audit ran

Enumerated from the tree: `ls tests/` gives `harness.py` plus 23
suites (8,729 lines total), with fixtures under
`tests/fixtures/stats_corpus/`. I read every suite's docstring, the
test inventories of the suites the checklist items hang on, and
`bin/bale_rollback.py` where the mapping needed code confirmation.

I also ran the suite (`python3 -m unittest discover -s tests`
against the shipped context tree as repo root): **245 tests, 243
pass, 2 errors, 51.8s**. Both errors are
`test_release_packaging.ReleaseListCoverageTest` reading the real
checkout's `install.sh`, which this request's baseline did not ship
(only `scripts/` came, per the 005 lesson — `install.sh` at repo
root is the same lesson one file wider). A packing artifact, not a
suite or code defect; on a full checkout I have no reason to expect
those two to fail. The run means the coverage map below is against
a live suite, not a static read.

## The coverage map: v0.4 checklist vs the suite

The checklist, item by item. "Covered" means a suite drives the
behavior E2E through real `bale` invocations in the hermetic
sandbox unless noted.

**End-to-end harness. Spin up a temp git repo.** COVERED and
mature. `tests/harness.py` (ADR-0005 doctrine: temp HOME with
sandboxed git identity, scratch install copied from the repo,
scratch git repo, stubbed EDITOR, absolute-path invocation) is the
shared spine; effectively every suite consumes it, plus a pty
runner for prompt-path tests (extracted at its second consumer,
per the board-11 trigger).

**Pack ... through every code path.** SUBSTANTIAL, with named
holes. Covered: the install pre-check refusal and the intact-pack
happy path (test_install_precheck); read-only shape, its sweep
prompt, and sibling admission (test_readonly_pack, test_auto_sweep);
split supersession's full accept/decline/idempotent-re-run matrix
including the wizard-path decline (test_supersession_pack);
`--readme-file` identity echo and the TODO(brief) placeholder
refusal (test_readme_identity); the tree-position echo and pack
`--json` parity (test_tree_position_echo); checkpoint blindness
gate and provenance stamping (test_checkpoint_provenance);
`--verbose` filter-chain drop trail and build trail
(test_verbose_thread). NOT covered: the §7.4 soft caps themselves
(file-count/size/depth prompts, the `[e]` edit-excludes branch,
`--force` past a cap), `--exclude`, `.baleignore`, and the full
wizard walk as such (wizard is touched only where other features'
prompts ride it).

**Apply ... through every code path.** SUBSTANTIAL on the decision
surface, THIN on the reject surface. Covered: PASS/merge and
HOLD/inspect defaults, retry in-session (test_hold_retry_e2e); the
required-check gate's refusal/override/dry-run matrix
(test_required_check_gate); blind-checkpoint execution, both-run
guarantee, HOLD attribution including checkpoint exit 2
(test_blind_checkpoint); own-scope drift refusal for read-only
sessions and sibling-scope interplay (test_readonly_pack);
archive_dir's three faces (test_archive_dir); auto-sweep's rails
(test_auto_sweep); clarification handling and its status/telemetry
trail (test_clarification_status, test_telemetry_promotion). NOT
covered — the malformed-tarball pre-flight rows: no suite ships a
tampered response (sha256/size mismatch, path-safety escape,
generated-artifact denial, empty reason, duplicate path,
`apply.sh`-vs-manifest reconciliation mismatch). Every fixture
tarball is well-formed by construction. Also NOT covered:
`apply.sh` with real operations — every fixture ships the no-op,
so deletes, the removal half of renames, and exec-bit restores
(§5.1.1's whole surface) never run E2E; and apply's inspection
flags (`--show-validator`, `--show-apply-script`, `--dry-run`
beyond the required-check prediction case) ride only where other
suites borrow them.

**Validate ... through every code path.** COVERED for PASS, FAIL,
checkpoint attribution, `--verbose` pass-through onto the script's
argv, and the reconciliation-parse telemetry face (fixtures). NOT
covered: worker-side `validation.sh` exit 2 (script-errored, as
distinct from check-failed) — the checkpoint's exit-2 phrasing is
pinned, the worker script's is not.

**Rollback through every code path. Conflicts.** The ladder's
suspect — "the rollback conflict and merge-commit cases were
explicitly deferred to v0.4 and never picked up" — is **refuted in
its narrow form** by the tree. test_rollback_telemetry drives:

- a **real conflict** (post-merge commit editing the same line,
  forcing the revert into in-progress conflict: exit non-zero,
  conflict headline, no tag, no record); and
- the **merge-commit revert** as the mainline: its
  `make_applied_session` fabricates the exact durable state apply's
  merge path leaves (`--no-ff` merge, second-parent subject,
  `applied/<sid>` tag), so every clean rollback in the suite
  exercises `git revert -m 1 <merge>` (`bin/bale_rollback.py`
  confirms the `-m 1` mainline selection keys on
  `_is_merge_commit`).

Qualifiers for your disposition: the conflict test asserts the
refusal/telemetry face only — nothing exercises the operator's
path out of the in-progress revert (git's territory, but the
walkthrough text around it is unpinned); the fabricated-merge
approach means rollback-after-a-real-`bale-apply`-merge is only
covered transitively (auto_sweep drives rollback after real
applies, telemetry-angled). Also `--undo` (re-applied) and
`--stash` (tracked dirt: stash, revert, pop) are covered; the
dirty-tree refusal is covered.

Remaining rollback holes: `bale rollback --list` is implemented
(`bin/bale_rollback.py` ~§504) and never invoked by any test; the
**plain non-merge commit** branch (`is_merge=False` target — only
reachable on hand-made history, since apply always `--no-ff`
merges) is untested.

**Held states.** COVERED. HOLD via failing validation
(test_hold_retry_e2e), checkpoint-attributed HOLDs in all three
attributions (test_blind_checkpoint), revert of a held branch and
its json contract (test_revert_json), HOLD/refusal telemetry
non-writes.

**Stale locks.** COVERED for session locks: crash-debris sweep
(test_unlock_json, test_closure_telemetry), abandoned-session
unlock across closure reasons. PARTIAL for the integration lock:
`unlock --integration` is tested only in its refusal shapes
(`--json` refused, `--reason` rejected) — the actual
stale-integration-lock clear path is not driven.

**Reverts.** COVERED. Discard path with branch facts and telemetry,
`--reason` threading, already-closed leftovers, json stream
discipline (test_revert_json, test_closure_telemetry).

**Re-apply.** COVERED on both readings: retry re-applies into the
same sid (test_hold_retry_e2e), and rollback `--undo` re-applies a
rolled-back merge with the `re-applied` record
(test_rollback_telemetry, test_auto_sweep's toggle case).

### Gap list, ranked by what covering each costs

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
7. **Handoff happy path** — adjacent, not in the checklist's verbs:
   `bale handoff` is tested only at its install-precheck refusal;
   the repackaging itself is untested.

Whether any of these blocks the cut is your ratification call. For
what it's worth as reporting, not recommendation: items 1–2 are the
only ones that guard the wire contract itself; the rest guard
convenience surfaces.

## The citation fold-in and sweep

**The mandated edit** landed: the v0.3 `--verbose` entry's bare
"§7.4" is now "TARBALL.md §7.4" (qualified against the current
bytes, post-005's touch to that parenthetical).

**The sweep** (every `§N[.M]` in BALE.md, classified against
BALE.md's own heading inventory and the neighboring docs) found
four more unambiguous cross-doc bares, all fixed in this response —
each cites TARBALL.md content while BALE.md's own same-numbered
section is something unrelated (§7.3 wizard flow, §7.5 build the
request), so the unqualified number resolved wrongly in-doc:

- §8.1 step 15: "grading `n/a` (§7.3)" → TARBALL.md §7.3 (the
  `[n/a]` grading lives in the reconciliation contract; the
  adjacent "(TARBALL.md §7.2)" was already qualified — this one
  had drifted).
- §8.5 step 2: "produces no §7.3 claims block" → TARBALL.md §7.3.
- §8.7 walkthrough: "the §7.3-style claims-vs-verdict
  reconciliation" → TARBALL.md §7.3.
- §8.9: "the §7.5 exit code" → TARBALL.md §7.5.

Every other bare reference checked out as a correct self-reference
(the §7.4 soft-cap and piped-refusal cites are BALE.md's own §7.4;
the §5.5/§5.6 cites are BALE.md's own status/stats; §6.2's
next-prompt mentions are BALE.md's own wire-format section, which
carries the legacy artifact; qualified forms — TARBALL.md,
CLAUDE.md, DOCS.md, bale-internals.md, meta-sessions.md — are all
consistent). Rewraps from the insertions stay within each edit's
own sentence span; validation.sh pins the anchors and asserts the
heading inventory is unchanged.

**Reported, not fixed (two items):**

- The **cut-condition paragraph's own bare §7.4** ("plus the §7.4
  pass-through of `--verbose` into `validation.sh` itself") is the
  same cross-doc defect as the mandated edit — but that paragraph
  is byte-stable by this session's constraint; the cut session owns
  rewriting it and can qualify (or drop) the citation there.
  validation.sh treats it as the one sanctioned exception in its
  bare-citation census.
- **Ambiguous, enumerated rather than guessed** (per the brief):
  §7.2's `--supersedes` prose says "By contract (§5 authorship
  line, TARBALL.md §3.4) the flag is worker-authored only." I
  could not resolve what "§5 authorship line" points at: BALE.md's
  own §5 command table carries no authorship line today (the pack
  row defers to §7.2), and no plausible cross-doc §5 fits better
  than the TARBALL.md §3.4 already cited beside it. It reads like
  a reference to a §5 sentence that has since moved or been
  absorbed. Left untouched; your call whether it's a stale
  self-reference to prune or shorthand I'm not seeing.

**The v1.0 "(MASTER.md §1)" reference: kept**, per the recorded
lean. The sweep surfaced nothing that changes the picture — grep
confirms it is still BALE.md's sole reference to MASTER.md
anywhere, and it is fully qualified, so it is not an instance of
the bare-citation defect class this session fixed. Revisit at the
ADR-0009/board-10 categorization decision as recorded.

## Claims notes

`claims` covers the four session-specific assertions in
validation.sh (doc-only session; no project lint/typecheck/build
surface applies). All claimed `pass`; each was exercised against
the finished `files/` before packing. The byte-stability check pins
sha256s over the two constrained spans, computed from the request
baseline and confirmed identical in the edited file.

## Includes note (packing signal)

`install.sh` at repo root: wanted by test_release_packaging's two
list-coverage tests, not shipped — the two suite errors above. If a
future session should run the suite green from the tarball alone,
that one file joins the baseline (the same class as 005's
scripts/build.sh lesson).

## Proposals

**What:** A malformed-tarball apply pre-flight suite (gap 1), with
gap 2's real-operations `apply.sh` fixtures folded in, as the first
v0.4 work once the cut question is disposed.
**Why:** This session's audit shows the reject surface of the
apply contract — the rows §11 enumerates and the trust ledger
presumes — is the one checklist area with no live coverage at all;
everything else on the checklist has at least a partial pin. The
fixture builder in test_hold_retry_e2e already constructs manifests
and hashes programmatically, so a tamper helper is a small step
from existing code.
**Scope hints:** tests/ only, plus harness.py if the tamper helper
lands there; independent of the citation work; ordering-free
against gaps 3–7.
