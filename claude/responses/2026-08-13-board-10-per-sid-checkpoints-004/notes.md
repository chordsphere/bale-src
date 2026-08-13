# notes — 2026-08-13-board-10-per-sid-checkpoints-004

All seven `changes[]` paths sit inside the write forecast (`BALE.md`,
`bin`, `tests`) — no out-of-forecast work to enumerate. The
packaging-list coupling the brief warned about didn't bite: no files
added to the install trees, so `install.sh` and `scripts/build.sh`
stay untouched, and no test names a surface that dragged a coupled
file in.

## The one real design problem, and the call I made

The brief pins resolution at pack, but both request-building paths run
the checkpoint gates **pre-sid** — the session id a `{sid}` base
resolves against doesn't exist when the blindness preflight fires. And
the naive fix (refuse post-allocation, in the provenance stamp
builder) has a nasty failure mode: `next_session_id` consumes the
per-day counter, so a refused pack burns an NNN, and the planner's
remedy — commit the checkpoint the refusal named, repack — would
allocate NNN+1 and resolve to a *different* path than the one just
named. An infinite counter chase.

What I built instead, in three parts:

1. **The blindness preflight goes pattern-aware.** For `{sid}`-bearing
   bases it checks coverage against the *unresolved pattern* —
   `scope_covers_path` is per-component containment, so a directory
   entry covering the pattern's parent covers every possible
   resolution identically, and a forecast entry equal to the literal
   pattern string is caught too. The existence probe is *deferred*
   (logged, never silent) because it can't run pre-sid.
2. **`peek_session_id`** (new, beside `next_session_id` in
   `bin/bale`) computes the sid the next allocation would mint without
   writing the counter.
3. **`checkpoint_resolved_preflight`** (new, in `bale_pack.py`, called
   by both cmd_pack and cmd_handoff immediately before their
   `next_session_id` call) resolves against the peeked sid and refuses
   a resolved path absent from HEAD while the pack has consumed
   nothing. The refusal names the resolved path and the remedy, and
   because the counter is untouched, the re-run pack after committing
   allocates the *same* sid. The test suite pins this no-chase
   property directly
   (`test_missing_resolved_refuses_preallocation_no_counter_chase`).

The provenance stamp builder still re-checks against the *allocated*
sid — its existing defense-in-depth posture — which also covers the
date-rollover race where peek and allocation straddle midnight. Ratify
the peek approach specifically: it shares the single-operator TOCTOU
posture the scope gates already hold (no cross-process lock between
peek and allocate), and I judged that acceptable because nothing
counter-touching runs between the two calls in-process and the
existing gates accept the same concurrent-process exposure.

## Unknown-brace-token handling (the craft call the brief left open)

I chose **reject loudly** over pass-through-literally, and sited the
rejection in `get_validation_base` — config read — rather than in the
resolver. Rationale: config read fires at pack *and* apply *and* every
other reader, so a `{date}` or `{SID}` typo is loud everywhere instead
of becoming a literal path that dangles forever; and it keeps
`resolve_checkpoint_path` trivially pure (unknown tokens never reach
it, so substitution is total and half-substitution is impossible by
construction). Braces that don't form a well-formed `{token}` pass
through as literal path characters. Documented in BALE.md's paragraph;
pinned by `test_unknown_token_refuses_at_pack_with_no_session_state`
and the pass-through unit test.

## Accepted residue worth knowing about

The pattern-coverage check at the pre-sid blindness gate can't catch
an *exact-file* forecast entry that textually equals a future
resolution — a packer typing the full resolved path by predicting the
unallocated NNN. Directory-shaped self-oracle forecasts (the realistic
shape) are caught. I judged the residue acceptable and documented it
in the preflight's comment: the checkpoint a session executes is
base-tree bytes regardless, and the stamp verification still gates a
changed oracle at apply. Flag if you want the gate to also
pattern-match scope entries against the resolved shape.

## Telemetry shape

The brief asked me to flag if the shape disagreed — it doesn't. The
checkpoint stamp's `path`/`script.path` fields are opaque strings in
`telemetry-record.schema.json` and `request-manifest.schema.json`;
resolved paths ride through unchanged, the E2Es assert the recorded
values, and no schema edit was needed (schemas are out of scope
anyway, which is consistent).

## Validation observations

- Full suite: 413 tests (405 baseline + 8 new), green, one
  pre-existing skip, in both my baseline run of the pristine context
  and the post-change run. Suite wall time was ~119–165s in my
  container against your 61–63s baseline — container speed, not new
  test weight; the new suite adds ~4s.
- `validate.sh` reports 5 failures in the shipped context
  (`upgrade.sh` and install `README.md` weren't included in the
  request) — byte-identical before and after my changes, so not a
  regression; your real tree should be unaffected.
- Both claims are `observed` (`claim_basis`): I ran `validation.sh`
  end-to-end against the changed tree with the manifest in place and
  watched both checks pass and reconcile `[agree]`.

## Deferred

A handoff-path E2E under a `{sid}` base (also in the manifest's
`deferred`): cmd_handoff's wiring is two lines around the shared,
pack-tested helper, its no-op branch is exercised by the existing
handoff and checkpoint-provenance suites, and a full bailout→handoff
fixture under a pattern base is a heavy fixture for low marginal
coverage in this session's budget.

## Proposals

### Handoff-under-pattern E2E

**What.** One E2E driving bailout → `bale handoff` on a project whose
`[validation] base` carries `{sid}`, asserting the handoff's
pre-allocation refusal (missing resolved file for the *new* sid) and
the stamped resolved path in the child request.

**Why.** It's the one lifecycle edge this session wired but did not
pin with its own test; the existing suites cover the literal branch
only. Cheap once a reusable bailout fixture exists —
`test_handoff_happy.py` already builds one that could be lifted into
`harness.py` on the same one-harness doctrine that produced
`build_response_dir`.

**Scope hints.** `tests/` only (plus a possible `harness.py`
extraction); no bin changes expected; independent of the bale.toml
migration.
