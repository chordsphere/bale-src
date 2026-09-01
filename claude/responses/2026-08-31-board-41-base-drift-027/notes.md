# Notes — 2026-08-31-board-41-base-drift-027

The pattern transplanted cleanly: the checkpoint stamp
(`build_provenance_block` → `read_request_checkpoint_stamp` → the
§8.5 verification → `--accept-checkpoint-change`) really is the whole
shape, one level wider. Everything below is either a determination
the brief left to me (flagged, per the working agreement) or
something I found on the way.

## Determinations made and flagged

**Directory forecast entries enumerate committed files at pack HEAD.**
The stamp resolves each forecast entry with
`git ls-tree -r --name-only -z HEAD -- <entry>` — a file entry
resolves to itself, a directory entry to the committed files under
it, one uniform command. Per-file granularity is therefore exact for
directory forecasts (the ratified default), and enumeration happens
at pack time as the brief prescribed.

**No-base-bytes paths are absent from the stamp, and absence never
refuses.** The pinned edge case (a forecast entry naming a file that
is new in the response) falls out by construction rather than by a
null sentinel: an untracked or not-yet-existing path enumerates
nothing under `ls-tree`, so it has no map entry, and the gate
compares only the `changes[] ∩ stamp` intersection. I chose
absence-over-explicit-null deliberately — a null would need its own
"never refuse" branch and its own schema shape; absence needs
neither, and the "intersection" wording in the board row reads as
exactly this design.

**Committed-is-ratified on both ends.** The stamp hashes HEAD bytes
at pack; the gate hashes target-tip bytes at apply — mirroring the
checkpoint stamp byte-for-byte (same `git show` binary-exact
extraction on both sides). One accepted residue follows: the shipped
`context/` carries *working-tree* bytes, so a file dirty at pack time
stamps its committed version, not the version the worker read. That
is the same committed-vs-shipped split the checkpoint stamp already
lives with, and the drift the stamp exists to catch (an *intervening
commit* moving the base under the session) is committed-side by
definition. If the desk wants working-tree stamping instead, it is a
one-line change in the extraction — but it would desync the stamp
from what apply can compare against (apply compares the target tip).

**A stamped file deleted at the base is drift.** `base_tree_sha256`
returns None for a missing blob, which can never equal a stamped
hash, so deletion/rename of a stamped file between pack and apply
refuses like any other move; the report renders that case in words
("missing at the base tree") rather than as a hash.

**A malformed stamp value skips loudly.** A `base_files` that is
present but not an object logs and reads as stampless — the same
never-guess posture as the unreadable-manifest branches beside it.

**Gate placement.** The gate sits after the step-8–10 file
verification and *before* the dry-run exit, so dry-run and real
apply run the identical code once (the checkpoint verification, by
contrast, has a duplicated dry-run prediction — I did not inherit
that duplication). It is manifest-and-git-read-only
(resolve_target_branch + rev-parse + git show), pre-staging, and
writes no session-dir stamps, so a refusal on either path leaves the
session open with no git side effects. Bailout/clarification
manifests fork earlier and never reach it.

**Handoff stamps too.** The brief says "stamped at pack"; handoff is
the second request-building path through the same provenance builder,
and a handed-off session has the identical lost-update exposure, so I
threaded its reading-plan forecast through as well (one keyword at
the existing call site). Ratify or trim.

## The brief's open question, answered

Both schemas enumerate the widened surfaces, and both were extended
additively:

- `request-manifest.schema.json` — the provenance block is
  `additionalProperties: false`, so extending it was *mandatory*, not
  optional: an unextended schema would have failed pack's own
  pre-flight on every stamped manifest. `base_files` is typed as an
  object of non-empty strings (the stdlib validator supports
  additionalProperties-as-subschema; no patternProperties needed).
- `telemetry-record.schema.json` — both closed outcome enums
  (envelope and attempts) gained `base-drift-refused`, and attempts
  gained the `base_drift_overrides` list mirroring
  `required_check_overrides`.

One consequence worth eyes: `tests/test_global_doc_selfcontainment`
forbids board citations and `BALE.md` references inside schema files
(the 2026-08-31 schema purge). My first drafts cited "board 41" and
tripped it; the shipped descriptions cite **v0.4.23** instead, and I
bumped `bin/VERSION` 0.4.22 → 0.4.23 to make that citation true.
The bump is my inference from the per-feature version precedent in
the docstrings — ratify it, or tell me the real landing version and
I'll re-spin the two description strings.

## Found on the way

**The shipped tree has 17 pre-existing test failures**, none mine:
mostly assertions stale against the v0.4.21 open-time telemetry
record (e.g. `test_required_check_gate`'s dry-run case asserts no
telemetry *file* exists, but pack now writes the `opened` record at
open; `test_hold_retry_e2e` and `test_checkpoint_provenance` index
`attempts[0]` or assert `len(attempts) == 1`, both off-by-one now
that every record opens with an `opened` attempt), plus pty/e2e cases
in `test_relay_verb`, `test_readonly_pack`, `test_supersession_pack`,
`test_auto_sweep`, `test_forecast_ledger`. Fifteen fail in a default
discovery run; two more only wake under `BALE_TEST_SLOW=1` (the
harness's slow gate) — I first baselined with the gate closed, saw
those two surface as "new" when my own no-regression check ran with
the gate open, and verified both fail **identically on the pristine
shipped tree** before widening the allowed set. I held this change to
**no new failures**: `validation.sh`'s `--slow` check runs full
discovery with the slow gate open and diffs the failing set against
the enumerated 17-id allowed list — pre-existing ids may pass or fail
freely (some look environment-sensitive), anything outside the list
fails the check. The allowed set was captured in my build
environment; if your environment produces a *different* pre-existing
failure, the check will name it as "new" — that's the check being
honest about a fixed baseline, not necessarily a regression from this
change.

**Whole-tree stamps are proportional to the forecast.** A default
pack (forecast = include set) or an explicit `.` forecast stamps
every committed file it covers — per-file granularity applied
honestly. On this repo that's harmless; on a 10k-file repo a
whole-tree pack would grow the manifest by roughly a hundred bytes
per file. I did not add a cap or elision (nothing in the ask, and
whole-tree packs are already concurrency-exclusive); flagging so the
growth is a known property, not a surprise.

**Slow-gating.** The new suite's two full-merge cases
(override-lands-bytes, retry-reruns-the-gate) sit behind the
harness's `BALE_TEST_SLOW` gate; the remaining 12 run in ~3s in the
default discovery pass.

**Registry state matched the desk's claim** — my hermetic sandboxes
aside, no scoped session collided with this pack's forecast; nothing
to relay.

No out-of-forecast paths: all ten `changes[]` entries sit inside the
declared forecast (`BALE.md`, `bin`, `schemas`, `tests`).

## Proposals

**Repair the 17 stale tests.** What: one session updating the
assertions that predate the v0.4.21 open-time telemetry record (the
`attempts[0]` / `len(attempts)` off-by-ones and the no-record
assumptions), and triaging the pty cases, which may need environment
guards. Why: every future session's full-suite validation now needs a
baseline-diff workaround like this one's, and a permanently-red suite
trains everyone to stop reading it — the silent-skip failure mode
applied to CI. Scope hints: `tests/test_required_check_gate.py`,
`test_relay_verb.py`, `test_readonly_pack.py`,
`test_supersession_pack.py`, `test_auto_sweep.py`,
`test_forecast_ledger.py`, `test_hold_retry_e2e.py`,
`test_checkpoint_provenance.py`; independent of this session's work.

**Stats read side for the base-drift pair, when data accrues.** What:
per-packer / per-class drilldowns already exist for the
scope-drift pair; the base-drift counts I added render in the extras
line and the members bucket, which is the same floor the
required-check pair launched with. Nothing more is needed until the
outcome actually occurs in a real corpus — this is a deliberate
match-the-precedent stop, recorded so the stop is visible.
