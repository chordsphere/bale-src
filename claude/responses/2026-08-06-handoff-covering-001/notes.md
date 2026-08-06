# Notes — 2026-08-06-handoff-covering-001

## Siting (the call the brief left to me)

The gate sits in `cmd_handoff` immediately after the reading-plan
resolution (`included_paths` → `resolved_scope`) and immediately
before `next_session_id` — i.e. **pre-sid**, after every existing
handoff pre-flight gate (detached-HEAD, open-sessions, tarball shape,
bailout-kind check, goal inheritance).

Pack's stated precedent — "blindness refusal precedes the disjointness
gate" — can't map onto handoff literally: handoff's analogue of the
disjointness conversation (the open-sessions guard) runs before the
tarball is even extracted, and the scope the gate needs doesn't exist
until the reading plan resolves. So I picked the invariant behind
pack's siting rather than its letter: **the refusal is pre-sid**, so a
refused handoff burns no NNN, opens nothing, and leaves no session
state — the same property pack's pre-sid refusal has, and the property
the new tests pin. A side effect of pre-sid siting: the gate's log
lines land in the unbuffered preamble rather than a session log,
exactly as pack's pre-sid refusal does. To keep "one value" intact,
the `handoff_scope` computation moved up above the gate (it previously
sat just before the manifest build); gate, manifest stamp, and
registry record still read the single computation.

## The `["."]` fallback — where the mirror bends (flagged per the brief)

Handoff's scope resolution differs structurally from pack's in one
place: a reading plan that cites **no** files resolves to `["."]`
(whole tree — the deliberate conservative fallback the persist comment
documents). Whole-tree scope covers any configured checkpoint, so in a
checkpoint-configured project, **every handoff from a plan-less
bailout now requires the flag**. I kept the shape rather than carving
an exception: a whole-tree scope really is covering (the drift gate
would admit checkpoint edits under it), and a default whole-tree
*pack* refuses identically — the mirror is exact on semantics. The
difference is in provenance of the breadth: pack's whole tree is a
packer's choice; handoff's is a degradation fallback from a
Claude-authored doc. If that friction shows up in practice (bailouts
legitimately often ship thin reading plans), the fix belongs in the
fallback's breadth or the refusal's remedy text, not in the gate — the
fourth test (`test_handoff_empty_plan_whole_tree_refuses`) pins
today's deliberate behavior either way.

## Shared refusal and log text — pack-flavored on handoff (accepted residue)

Per the constraint ("one implementation, two callers... refusal text
shared"), `format_checkpoint_scope_refusal` and the preflight's log
lines are untouched. Consequence: a handoff refusal says "pack scope
covers the blind checkpoint" and offers "narrow this pack with
--include paths" — a remedy that isn't literal on handoff (the real
remedies there are the flag, or a reading plan that doesn't cite the
oracle). The load-bearing parts — the covering diagnosis, the
sanctioned-ordinary-path reminder, and the flag as successor, whose
spelling is identical on both commands — are all correct on both
paths. A caller-aware remedy sentence is proposed below rather than
done; today's text honors the one-text constraint.

## A third stale spot (beyond the two pinned)

The brief pinned two comment true-ups in `bin/bale_pack.py`; both are
in. A third became stale with the landing:
`schemas/request-manifest.schema.json`'s `checkpoint_scope_admitted`
description said "false otherwise, including every handoff-built
request". Schemas are in the declared scope and the edit is
description prose only (no structural change, additive-safe), so I
trued it up rather than shipping a manifest that contradicts its own
schema's commentary. Flagging it here since the brief's pin list
didn't name it.

## Test home — deviation from the brief's guess

The brief guessed `tests/test_blind_checkpoint.py` as the likely home.
I put `HandoffBlindnessGateTest` in
`tests/test_checkpoint_provenance.py` instead: that file is the
session-C blindness-enforcement suite — the pack-side covering
refusal, the admission flag, and the `checkpoint_scope_admitted`
stamps all live there, and its module docstring enumerates exactly
this assertion family (now extended with the handoff rows).
`test_blind_checkpoint.py` is session A's execution-semantics suite
(base-tree bytes, HOLD attribution) and imports nothing the new tests
need. Fixture scaffolding follows `tests/harness.py` as pinned; the
bailout-tarball builder mirrors `test_telemetry_promotion.py`'s
(self-contained in the class — the harness has no shared bailout
builder, and extracting one for a second consumer is below the
two-consumer threshold the codebase's own comments use).

## Verifications the brief asked for

- **TARBALL.md**: verified untouched-correct. §3.4 documents pack
  flags only; the only handoff-facing sentences are the `bale handoff
  <response-NNN>` follow-on mentions, none naming a flag surface.
- **BALE.md handoff docs**: there is no dedicated handoff section —
  the §5 command-surface row is the handoff command's documentation,
  and that row gained the flag. §11's new row is 30, appended after
  29 per the appended-row precedent (rows 1–29 byte-stable).
- **The preflight docstring's "defense in depth for the handoff
  path"**: both occurrences (preflight and provenance builder) needed
  rewording, not deletion — the builder's dangling re-check remains
  real defense in depth, now for "any future caller" since both
  request-building paths run the preflight pre-sid.

## Validation shape

`validation.sh` runs the whole suite (232 tests, ~1 min — inside the
§7.6 target), not a scoped subset: the change touches a shared gate
with two callers plus the provenance builder every request-building
path stamps through, so pack-path regression coverage is the point,
not overhead.

## Proposals

- **True up `bale handoff`'s argparse description.** What: the
  subparser description still says handoff "ships its handoff.md as
  the sole context entry". Why: stale since the v0.0.7 reading-plan
  pre-pack (this session read it while adding the flag beside it);
  left alone because it predates this session's change and the
  constraint was additive. One-sentence fix, doc-only. Scope hints:
  `bin/bale`, the `p_handoff` subparser description.
- **Caller-aware remedy line in the shared refusal.** What: an
  optional `caller` parameter on `format_checkpoint_scope_refusal`
  (default `"pack"`) swapping only the remedy sentence — "narrow this
  pack with --include paths" vs. a handoff-flavored "re-bail with a
  reading plan that does not cite the checkpoint". Why: the shared
  text's pack-flavored remedy is the one part that reads wrong on a
  handoff refusal (see the residue note above); the diagnosis and the
  flag successor stay shared. Only if the master wants to relax the
  one-text constraint — this session deliberately did not. Scope
  hints: `bin/bale_report.py` (formatter), both callers pass-through.
