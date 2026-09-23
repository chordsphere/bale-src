# notes — 2026-09-23-board-122-rehearsal-verbs-009 (bale 0.4.45)

Row 122 is landed as the three spellings the brief pinned. They all share
one gate core, and each stops at a fixed point along the real pipeline.

## How it's built, and why that way

**One gate core, not a copy.** `cmd_pack` ran its argv gates as inline
stanzas. A rehearsal that re-typed them would drift from the pack it
claims to predict. So I cut each stanza into a named helper and left
`cmd_pack` calling it at the same site, with the moved code only
re-indented:

- `refuse_contradictory_pack_flags`
- `read_pack_delivery_files`
- `refuse_detached_head`
- `resolve_pack_include_group`
- `refuse_piped_wizard`
- `guard_readme_absence`
- `supersession_guards`, the part of `_resolve_supersession` above its
  exchange

A script did the cut and aborted on any non-unique anchor. Before any new
behavior went in, the eight pack/open/supersession/include-group suites
passed unchanged: 211 tests.

**`pack_argv_preflight` grows, as the micro's Proposal 3 asked.** After
the `--context` guard it now runs, in order:

1. the include group, for its read-side additions;
2. `pack_pre_exchange_gates`, fed `read_includes` (with the group's
   additions) and `gate_deferred` exactly as `cmd_pack` feeds it;
3. the pre-answered-intents parse;
4. the supersession guards;
5. the disjointness gate, with the parent still treated as pending.

`run_pack_argv_gates` wraps it with the front gates (flag pairs, the
brief and checkpoint reads, the home-directory check at the root,
detached HEAD) and the tail gates (the piped-wizard refusal and the
piped no-README refusal).

**The rehearsals are prefixes.**
- `bale open --check` stops after `run_pack_argv_gates`.
- `bale open --dry-run` stops after the checkpoint leg.
- `bale pack --dry-run` stops after `run_pack_argv_gates`.

Nothing past the stop point runs, so nothing past it can write.

## Deviations and decisions to ratify

1. **A real `bale open` changed too, deliberately.** Its gate step before
   the oracle is now `run_pack_argv_gates`, the same step `--check` runs,
   instead of the narrower 0.4.43 pre-flight. The upside is that "what
   `--check` passes, the open's gates pass" is true by construction. The
   visible effect: a `TODO(brief)` placeholder, a flag contradiction, an
   unresolvable `--supersedes`, and the include-naming checkpoint gate
   now refuse before the checkpoint dry-run instead of inside the replay.
   `OpenGatesBeforeOracleTest` pins the placeholder case. The replay
   still re-runs every gate at its own site.

2. **The `[validation]`-base refusal moved ahead of the argv gates in
   `cmd_open`.** The text is the same. Without the move,
   `read_pack_delivery_files` would refuse first with
   `checkpoint_file_base_or_refuse`'s wording and break
   `test_checkpoint_member_without_config_refuses_pre_dry_run`. It is a
   bundle-level check, so it belongs before the argv.

3. **The `--dry-run` log lives outside the repository.** A real open
   writes `.bale/logs/open-<stem>.log`, and the sandbox self-probe
   scratch goes beside it. `.bale/` is gitignored, so `git status` would
   have stayed clean either way. I held the literal constraint instead:
   a rehearsal puts both under `${TMPDIR}/bale-open-rehearsal-*/`, keeps
   them, and names the log in the report. The members' extraction
   tempdir was already outside the repo.

4. **The supersession exchange is predicted, never run.** The report
   says what the exchange would do, from the facts it would read:
   - a matching `supersede` intent: would accept, parent stays open now;
   - a TTY: would prompt;
   - piped stdin with no intent: **refuses**.

   The refusal is the one judgment call. The real pack would take the
   decline default and then refuse, either at the disjointness gate or
   at the declined-supersession refusal. A rehearsal that exits 0 there
   would be wrong. Unmatched intents are reported loudly, the way the
   replay reports them.

5. **The read-only sweep is previewed.** The report lists the open
   `[]`-scope sessions the sweep would offer to close. Nothing closes.

6. **Second desk under a rehearsal.** The brief didn't cover this case,
   where the bundle's session is still open. A real open records a desk
   and runs no gates, so the rehearsal reports "would record desk-N on
   <sid>", or raises the same refusal when the record holds an
   apply-side event, and records nothing. `second_desk_refusal` and
   `next_desk_name` are now pure helpers `open_second_desk` shares.

7. **Pairs.**
   - `--dry-run --json` is refused loudly. The brief allowed that, and
     pack's `--json` line describes a pack that ran.
   - `--dry-run --context` refuses through the context pack's
     session-only table, like every session flag. So `dry_run` joins
     `CONTEXT_SESSION_ONLY_FLAGS`, and `tests/test_context_pack.py`'s
     partition pin gains the example.
   - `--check` and `--dry-run` on `open` are argparse-exclusive.
   - A rehearsal outside a git repository refuses, because pack would
     run the git-init walkthrough, which writes.

8. **The wizard path is reported, not rehearsed.** On a TTY with the goal
   or `--slug` missing, the forecast depends on answers a rehearsal can't
   collect. The gates that can run do run (the pre-exchange pass
   includes the read half of the blindness gate), and the report says in
   words that the forecast-dependent gates were not rehearsed. Piped, it
   refuses like the pack.

9. **FORCE lines are not journaled twice.** In a real open, the extended
   pre-flight runs the blindness gate, whose `--allow-checkpoint-in-scope`
   admission FORCE-logs, before the replay runs it again. Every FORCE
   line the pre-flight queues is dropped from bin/bale's pending queue
   once the pre-flight ends, and the include group's lines are quieted
   (`announce=False`). The terminal still shows the pre-flight's FORCE
   line once. The session journal gets the replay's copy only.

10. **`pack_argv_preflight` returns a dict now, not None.** Its only
    in-tree caller was `bale_open`, and the one test that drives it
    directly (`test_open_preflight_refuses_a_context_argv`) only
    exercises the refusal. The `resolved_scope` import sits after the
    `--context` guard, because that test's child process carries only
    `fail` on `__main__`.

## Where the brief and the code disagreed

None of substance. The micro's notes held against the code:
`pack_argv_preflight` was byte-for-byte 0.4.43's, and
`pack_pre_exchange_gates` needed exactly `read_includes` and
`gate_deferred`. One pre-0.4.45 docstring line in
`pack_pre_exchange_gates` ("row 122 extends it next") is updated to say
it happened.

## BALE.md

- §5's `bale pack` and `bale open` rows name the spellings.
- §6.7 gains two paragraphs: the second desk (Proposal 4) and rehearsing
  a bundle.
- §7.1 gains the `pack --dry-run` paragraph, after step 6, which it
  skips.
- §8.9's pack-side-stamps paragraph now covers the second-desk attempt:
  `command: "open"` (a first open still stamps `pack`) and `desk`.

The schema's own description of `command` already said this. The prose
now agrees with it.

## Validation

`validation.sh` runs `tests.test_rehearsal_verbs` (20 tests, new) and a
regression group: the open, context, pack-opener, supersession,
include-group, guards, read-only, checkpoint-file, CLI-help, changelog
and release suites. Then come five scenario assertions, written fresh
and not shared with the suite. Each drives the staged `bin/bale` in a
hermetic sandbox and compares a byte snapshot of the scratch repo before
and after: every file outside `.git` by sha256, HEAD, every ref, and
`git status --porcelain --ignored`. They cover:

- `pack --dry-run` writes nothing;
- `open --check` writes nothing;
- `open --dry-run` writes nothing, with an expected HOLD;
- the `--supersedes` parent stays open, with its record byte-identical
  after both an `open --check` with an intent and a refused piped
  `pack --dry-run`;
- VERSION and the changelog.

Every claim is `observed`. I ran the script as bale will: the shipped
base tree, the `files/` overlay, `apply.sh`, and the manifest as
`.bale-manifest.json`, with cwd at that root. Every check passed, every
claim reconciled `[agree]`, and the staging tree was byte-identical
afterwards. Runtime was a few minutes; the regression group dominates.

That run caught a bug in my own first draft of the script, not in the
verbs. It pinned a `[validation]` base for every scenario, so the
parent scenario's real scoped pack refused for lacking its own
checkpoint. The base is now pinned only in the two checkpoint
scenarios.

Per §7.2 I also ran the assertions against the unmodified tree. The
new suite fails there: 25 failures across 20 tests with subtests. All
five scenarios fail there too, as does the version check.

**The whole test tree.** I ran every module on the final tree, one at a
time: 73 of 75 pass.
- `test_handoff_fixture` is a helper module with no tests (unittest's
  exit 5).
- `test_doc_crossrefs` has one failure,
  `test_adr_0013_citations_carry_resolving_keys`. It needs
  `claude/context/adr/0013-*.md`, which the request didn't ship, and it
  fails identically on the untouched base. That's environmental and
  unrelated to this change; on your tree it should pass as before.

The whole tree is not in `validation.sh`, because it runs far past the
two-minute target.

## Proposals

- **What:** A `--dry-run` row in TARBALL.md §3.4's flag table, and a
  sentence on the two `bale open` rehearsal flags where §3.4 describes
  the bundle line.
  **Why:** §3.4 is the canonical flag surface, and `bale pack --help`
  points at it. A desk reading §3.4 won't learn the rehearsal exists.
  **Scope hints:** TARBALL.md §3.4 only, for the global docs' next
  holder.

- **What:** Retire PLANNER.md §4's interim "rehearse in a fixture"
  doctrine. Replace it with one sentence: a desk with the operator's
  tree a probe away asks for `bale open --dry-run <bundle>` (or
  `--check` when the oracle is slow) before delivery, and a desk with
  `bin/` in context can still dress-rehearse in a scratch repo.
  **Why:** The row names the doctrine as the interim until this lands,
  and no registry entry carries the fixture rehearsal. The verbs
  replace it on the real tree, which is where the wave's include miss
  hid.
  **Scope hints:** PLANNER.md §4, one sentence. Only after 0.4.45
  applies.

- **What:** Consider making the rehearsal report available as a `--json`
  line (for example `outcome: "rehearsed"` plus the rows as keys) if a
  desk tool ends up parsing it.
  **Why:** I refused the pair rather than invent a contract with no
  consumer. If `craft_response.py --bundle` ever wants to run a check
  itself, it will want a machine form.
  **Scope hints:** `bin/bale_pack.py` (`format_rehearsal_report`),
  `bin/bale_report.py`, and pack's `--json` key list in BALE.md §7.7.
