# notes — 2026-08-06-verbose-thread-close-005

The thread closed cleanly; three decisions below want your ratification,
and one environment gap shaped how far validation could run here.

## What pack's --verbose actually covers (the brief left this to me)

Pack's captured-or-quiet surfaces, determined from the code:

- **The filter-chain walk** (`walk_for_pack`) — every dropped path was
  invisible everywhere: not on the terminal, not in any log. Under
  `--verbose` each drop now prints a line naming the path AND the
  filter that took it (baked-in dir / secret pattern /
  .baleignore-or-session-exclude / outside `--include` / not a regular
  file). This is the flag's highest-value surface: it answers "why
  isn't file X in my pack" directly. Walk lines run pre-sid, so they
  reach the terminal only, like every other pre-sid line; on the
  soft-breach `[e]` re-walk loop they re-print against the updated
  matcher, which is honest.
- **The tarball build** (`build_request_tarball`) — the quiet stretch
  between "selected N files" and "wrote <tarball>". Under `--verbose`
  it streams the injected docs and tools, the manifest/README writes,
  each context copy, and the tar step. These run post-sid, so they land
  in the session log too.
- **Hook output already streams live** with or without the flag —
  `run_hook` deliberately doesn't capture. So the flag adds nothing
  there, bin/bale section 23 was not touched, and the conditional
  run_hook f-string fold-in does not ride this session.

Under `--json`, verbose lines follow the stream discipline to stderr
automatically (they go through `print()`/`log()`, which
`enable_json_mode`'s sys-level swap reroutes); the smoke run and the
suite both confirm stdout stays exactly the one JSON line.

## The §7.4 pass-through: forwarded unconditionally — ratify this

When the operator passes `--verbose` to apply or retry, `validation.sh`
is now invoked as `bash validation.sh --verbose`, so TARBALL.md §7.4's
own verbose mode engages inside the script. I chose **unconditional
forwarding on the verbose path** over tolerate-rejection probing:

- the contract doc has specified the flag since §7.4 was written, so a
  conforming script already handles it;
- a script that ignores its argv entirely — the overwhelmingly common
  shape — is unaffected;
- a strict script that rejects unknown arguments fails **loudly, in
  verbose mode only**, with the streamed output showing exactly why,
  and re-running without `--verbose` restores the bare invocation.
  That's a visible, recoverable failure, which beats a silent
  capability probe.

The default invocation stays byte-for-byte `bash validation.sh`. Retry
inherits the pass-through for free (same `run_validation_sh` path). The
**blind checkpoint does not receive the flag**: it's planner-authored
with no §7.4 contract on its argv, and its invocation stays stable —
second decision to ratify.

## The riding fold-in landed — with one new machine fact

`_discard_hold_state` no longer renders anything: it returns machine
facts only, and `bale_report.format_staging_row` projects the human
staging row at both discard consumers (cmd_revert's summary block and
the apply walkthrough's revert branch — the latter had to move too,
since the `staging_status` key is gone from the dict). One addition you
should look at: the return dict grew **`staging_error`** (the rmtree
OSError text, "unremovable" only), because the old inline
"left in place (path: error)" row couldn't be projected from the
v0.3.19 state/path pair alone. It's an internal dict key — the
`--json` key contract is untouched (`format_revert_json`'s set is
unchanged). The projection is byte-identical for all four states,
unit-pinned in the new suite.

## Where to look closely on review

- `bin/bale_pack.py`: the verbose `log` imports are **guarded inside
  the verbose branch**, not at function top. That's deliberate — the
  craft_response injection-surface suite drives
  `build_request_tarball` from a synthetic `__main__` that stubs only
  the four constants, and an unconditional `log` import broke it (I
  hit this; the guarded form keeps the quiet path's import surface
  exactly pre-flag).
- `bin/bale` §19: the `_echo_git` helper and the three echo sites.
- The default-surface byte-parity claims are pinned by two dedicated
  no-verbose-lines tests, not just asserted.

## The suite, honestly

245 tests; 238 pass here. The 7 errors are all
`tests/test_release_packaging.py` failing on
`FileNotFoundError: scripts/build.sh` — **the request shipped no
`scripts/` tree**, and that suite reads it from repo root. I confirmed
the identical 7 errors on the pristine shipped tree before any edit,
so they are an environment gap of this sandbox, not a regression. The
manifest's suite claim is `pass` predicated on `scripts/build.sh`
existing in your real repo (where `validation.sh` runs in staging); if
it somehow doesn't, the claim/verdict reconciliation will flag exactly
that disagreement. Packing signal recorded in
`feedback.self_reported.includes_missing`: ship `scripts/` whenever
`tests/` rides as the suite-run baseline.

## One-apply-behind

This session touches pack- and apply-path code, so the apply that lands
it runs the **old** code one last time: no verbose forwarding into
validation.sh on this apply even if you pass `--verbose`, and the old
inline staging row if you end up on the walkthrough's revert branch.
First post-merge invocation behaves new.

## Doc-side restraint, as instructed

BALE.md §13: only the v0.3 `--verbose` entry's "remain open"
parenthetical changed. The ladder's cut-condition paragraph and every
bare "§7.4" byte are untouched — the citation-qualification fold-in
rides the audit session.

## Proposals

- **Thread `--verbose` into the other two `_discard_hold_state`
  callers.** What: pass the already-present `args.verbose` through from
  `bale retry` and from the apply walkthrough's revert action. Why:
  the helper's verbose streaming exists now with a keyword default;
  both callers already hold a verbose flag, so the wiring is two
  one-line changes — this session kept them byte-identical only
  because the goal named pack and revert. Scope hints: bin/bale §20
  (retry's call), bin/bale_apply.py's walkthrough revert branch.
- **`bale handoff --verbose` for its tarball build.** What: a
  `--verbose` flag on handoff passing `verbose=True` into its
  `build_request_tarball` call. Why: the build-trail machinery is in
  place with a default-off kwarg; handoff builds the same quiet tarball
  pack does. Recorded in §5.4's updated bullet as the one remaining
  candidate surface. Scope hints: bin/bale §22, the handoff subparser
  in §26.
