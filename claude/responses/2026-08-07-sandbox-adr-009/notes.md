# notes.md — 2026-08-07-sandbox-adr-009

## What landed

ADR-0016 (`claude/context/adr/0016-response-script-sandbox.md`),
Status Proposed, plus the INDEX.md entry and inventory-count updates
in the same response. The ratified floor is carried verbatim in
spirit (sandbox required for unattended execution; network off;
writes confined to staging plus the bale-owned log path); everything
on top is flagged for the master desk.

## Positions taken — the ratification checklist

Each of these is an accept-or-strike at the sitting:

1. **Uniform confinement** across all three scripts, checkpoint
   included. The argument I leaned on hardest: the checkpoint's
   planner provenance is only one merge deep — base-tree bytes are
   whatever the last apply admitted — so the trust gradient is
   shallower than "planner-authored" suggests. Plus one code path
   beats two, and confinement forbids nothing the contract permits.
2. **Attended path default-on** with a loud per-invocation escape.
   Grounded in the manual-path-is-ground-truth commitment (ADR-0012):
   a sandbox only the harness exercises is never proven by hand.
3. **Network hatch: planner-granted, per-project, contract only**,
   and scoped — it relaxes network, never filesystem confinement.
4. **Mechanism deferred to board 10**, with the WSL constraint
   recorded as the one thing the implementation inherits.
5. **Beyond the floor: environment scrubbing** (allowlist the child
   env). I flagged this separately inside the ADR so it can be
   struck without touching the rest. See the surprise below for why
   I raised it at all.

## Proposed MASTER.md deltas (for the master to land)

- **Board-10 bullet annotation:** the "Sandbox validation.sh
  execution" bullet's doctrine half is closed — ADR-0016 authored
  Proposed 2026-08-07 (2026-08-07-sandbox-adr-009), awaiting
  ratification. The implementation half (mechanism selection under
  the WSL constraint, the invocation wrapper, the per-invocation
  escape flag, the per-project network-grant config surface) remains
  on board 10, gated on ratification.
- **§3 next-step advance:** the sandbox ADR item is done; the
  board-10 spec-intake sitting moves to the head of "Next, in
  order." The sitting's agenda picks up the ADR-0016 ratification
  (four positions plus the env-scrubbing extension, each
  accept-or-strike) alongside the spec intake.

## Surprises from the execution surface (verified in bale_staging.py)

- **Full environment inheritance.** All three invocations are bare
  `subprocess` with no `env=` argument — worker-authored scripts see
  every variable in the operator's environment, secrets included,
  today. This is why the env-scrubbing proposal exists; it felt
  wrong to write the sandbox doctrine and leave it unmentioned.
- **The `bash -n` pre-flight doesn't cover the checkpoint.**
  `check_response_shell_syntax` gates `apply.sh` and `validation.sh`
  only; a checkpoint with a syntax error surfaces mid-pipeline. Not
  a confinement issue, but board 10 may want the same fail-fast for
  the checkpoint while it's in there.
- **Invocation asymmetries the sandbox must preserve:**
  `validation.sh` gets the `--verbose` pass-through, the checkpoint
  deliberately does not; and the checkpoint script executes from a
  bale-owned tempdir *outside* staging, so filesystem confinement
  has to be writes-only (bale-materialized read inputs stay
  readable). Both are called out in the ADR's Consequences so the
  implementation doesn't regress them.
- Bale's own staging writes (`validation.sh` copied in,
  `.bale-manifest.json` placed) happen after reconciliation and are
  bale's, not the script's — no interaction with the sandbox
  contract beyond the log path the floor already names.

## Numbering basis

The request ships only ADRs 0003 and 0005 in `context/`, so "verify
against the shipped adr/ listing" resolved to the shipped INDEX.md,
whose current-status paragraph (updated with 0015's landing,
2026-08-07) enumerates 0001–0015 with 0015 as max — agreeing with
the goal's own "as ADR-0016." validation.sh re-verifies against the
real staging tree (0016 = max existing + 1), so a stale INDEX would
surface as a FAIL at apply rather than a silently wrong number.

## Scope

Both changed paths sit inside the resolved scope (`claude/INDEX.md`,
`claude/context/adr`). No out-of-forecast paths, no deferrals, no
source changes, no MASTER.md edits.
