# notes.md — bare-pack-excl-waiver-002

Both changes landed and the full 423-test suite is green (observed,
staged state). Three things need your eyes before anything else.

## 1. Ratify: how I reconciled "the forecast half is untouched" with the bare-pack goal

The brief pins both of these: the forecast half of the blindness gate
stays containment-keyed, and the bare default pack must pass the gate.
They collide on one fact: a pack with no `--write` *defaults its
forecast to the resolved include set*, and a bare pack's include set is
`["."]`, which covers any checkpoint by containment. Held literally,
"untouched" would refuse every bare pack forever — the exact behavior
this session exists to retire.

The reconciliation I shipped: the forecast half's containment refusal
applies to a **declared** forecast — a typed `--write` set, or
handoff's reading-plan forecast — via a new `forecast_declared`
parameter. The include-set *default* forecast is not treated as a
declaration; it IS the include set, and the read-side explicit-naming
rule already governs that value. Evaluating one value twice under two
keys would just re-create the retired refusal under a different name.
Every behavior the brief names explicitly survives intact: a typed
`--write` covering the checkpoint refuses without the flag, and the
brief's own phrasing ("A `--write` covering the checkpoint still
refuses") consistently describes the typed form.

Residue worth knowing: a default pack's recorded forecast is still
`["."]`, so the apply-side drift gate would not catch a response that
lands an edit under `claude/checkpoints/` in such a session. The
per-sid stamp verification still catches tampering with the session's
*own* oracle, and the checkpoint that executes is base-tree bytes,
never the staged copy — so the residue is a *reviewable landed edit*,
the same species bale accepts for `bale.toml` itself (the accepted
residue noted on the gate). If you want the drift gate hardened here,
that's a follow-on, not a quiet extension of this session.

## 2. Admit: one out-of-forecast path

- **`bin/bale_report.py`** (modified) — the read-side blindness
  refusal's diagnosis and remedy live in
  `format_checkpoint_scope_refusal`, and the old text told the user to
  "narrow this pack with --include paths that do not cover the
  checkpoint." Under explicit-naming semantics that remedy is wrong
  (broad coverage no longer refuses — it auto-excludes), and the
  session constraint says every refusal names its real remedy. I
  considered building the read-side string in `bale_pack.py` instead
  to stay in forecast, but that splits one message across two homes.
  The diff is confined to that one formatter (docstring, read-side
  diagnosis, read-side remedy sentence).

Everything else in `changes[]` is inside the recorded forecast
(`BALE.md`, `bin/VERSION`, `bin/bale_pack.py`, `schemas`, `tests`,
`tools/response_lint.py`).

## 3. Look closely at

- **The admission asymmetry** in `checkpoint_blindness_preflight`:
  flag-less refusal keys on explicit naming; under the flag, the
  read-half admission keys on **containment** — because the flag
  disables walk auto-exclusion, so any covering include set actually
  ships the bytes and must stamp. This is what keeps "the admission
  stamps exactly as today" true for the broad-include maintenance
  pack (`--include claude/checkpoints --allow-checkpoint-in-scope`
  ships the subtree with `checkpoint_scope_admitted: true`).
- **The waiver's scope**: `checkpoint: null` + `checkpoint_waived`
  stamps only for `{sid}`-bearing bases. A read-only pack under a
  *literal* base keeps stamping `{path, sha256}` exactly as since
  v0.3.28 (the existing test pins it; the committed oracle exists and
  stamping costs nothing). The waiver removes the per-session
  authoring ceremony only `{sid}` bases impose. If you wanted literal
  bases to stamp null-plus-waived too, say so and it's a three-line
  follow-up plus one test flip.
- **The degenerate `{sid}` shape**: a base with no static directory
  prefix (`{sid}.sh` at repo root) has no computable auto-exclusion
  basis, so it keeps the pre-v0.4.9 containment refusal on the read
  side (logged when it engages) rather than gaining a root-file
  wildcard. The oracle can't ship silently; the pathological config
  just doesn't get the new convenience.

## Verifications the brief asked for

- **Handoff never waives**: confirmed in the wiring —
  `cmd_handoff`'s forecast is `resolved_scope(included_paths)` with a
  `["."]` fallback when the reading plan cites no files, so it is
  never empty; its `checkpoint_resolved_preflight` call passes no
  forecast and keeps v0.4.8 behavior byte-for-byte. No `bin/bale`
  edit was needed anywhere (all new parameters default to the old
  behavior).
- **Telemetry echo**: the telemetry record's `feedback` field is a
  loose object (verbatim embed, no `additionalProperties`), so no
  telemetry-schema change was needed. The **response** manifest's
  `feedback.mechanical.provenance` echo, however, is
  `additionalProperties: false` — a waived request's verbatim echo
  would have failed it — so that schema gained the same additive
  optional key, and the lint's embedded copy was refreshed
  (`test_schema_embeds` guards the equality).

## Claims basis

Every `pass` claim except none is `observed`: validation.sh was run
against a faithful staging simulation (original context + `files/`
overlay with modes stripped + `apply.sh`), default leg and `--slow`
leg both, every reconciliation row `[agree]`. The full suite runs
~105s, which is why it sits behind `--slow` (TARBALL.md §7.6); the
default leg is ~40s.

## Test-suite note

The new per-sid classes inherit a `PerSidFixture` base split out of
`PerSidCheckpointE2ETest` — without the split, subclassing the E2E
class re-ran all eight S7 tests once per new class. One real bug was
caught during this work in my own first draft of the schema unit
tests: assigning `module.schema_validate` as a class attribute binds
it as a method, silently feeding `self` as the instance under
validation and passing vacuously. The shipped test holds the module
instead, and a comment marks the trap.

## Proposals

- **What**: extend the read-side explicit-naming key (or a variant of
  auto-exclusion) to `bale handoff`, whose reading-plan forecast
  currently refuses on plain containment — a bailed bare-pack
  session's handoff with a whole-tree fallback plan still requires
  the flag.
  **Why**: this session restored the bare *pack*; the handoff path
  keeps the pre-v0.4.9 posture (deliberately untouched — it is both
  read set and forecast there, and changing it was not in the goal).
  If bare-shaped sessions start bailing, their handoffs will hit the
  same friction the master's own request did.
  **Scope hints**: `bin/bale` (cmd_handoff), the shared gate; only
  after A+B land, and probably alongside Change C's session since the
  refusal-text surface overlaps.
