# notes.md — 2026-09-10-board-75-sandbox-config-off-002

The feature is small; most of what follows is where the goal sent me
outside the forecast, and why.

## Out-of-forecast paths (admit per path at apply)

Five `changes[]` paths are not in `resolved_scope`. Three were ratified
in the exchange round (the round-2 record is under
`.bale/clarifications/` once relayed; the answers were all
as-recommended); the last two are new and argued here.

- **bin/bale_report.py** — `build_telemetry_attempt` is the only
  writer of `attempts[]`; the REQUIRED `sandbox_confined` /
  `sandbox_off_source` stamps cannot land without it. Ratified (Q1).
- **bin/bale_validate.py** — `sandbox_off_source` is a closed
  vocabulary and the S5 discipline says a single-spot schema enum is
  exactly the defect the record-wide walk prevents. Ratified (Q1).
- **bin/bale_open.py** — the checkpoint dry-run is the one other
  confined leg; a namespace-less host runs `bale open` too. Ratified
  (Q2).
- **bin/bale** — three `--no-sandbox` help strings said "deliberately
  no config key"; strings only, no behavior. Ratified (Q3).
- **bin/bale_staging.py** — *not asked; same argument as Q3.* The
  three per-script lines ("running apply.sh in staging (UNCONFINED —
  --no-sandbox)", and the checkpoint/validation.sh equivalents) name
  the flag as the reason for every unconfined run. Under config-off
  with no flag typed they would have attributed the run to a flag
  nobody passed — three lines contradicting the FORCE line above them,
  in the same log. The constraint is "every sandbox-off apply names
  its source"; a log that names the *wrong* source three times fails
  it in spirit. The strings now read "UNCONFINED — source in the
  FORCE: line above", correct for both escapes; the module docstring
  names both. Strings only. If you'd rather not admit it, the
  behavior is unaffected and only the log wording regresses to
  misattribution under config-off.

## Ruling supersession (for the next sitting-open)

Per the desk's Q3 addition: this feature **supersedes the "deliberately
no config key" clause of the ratified override contract as it applied
to the sandbox escape** (ADR-0016 position 2). The clause still holds
for every other per-invocation flag (`--allow-out-of-scope`,
`--accept-base-drift`, `--allow-missing-required-check`,
`--accept-checkpoint-change`) — nothing here touches those, and the
same phrase survives untouched in their help strings and BALE.md
bullets. Record the supersession as a ruling repair rather than
letting the old ratification linger contradicted: the sandbox escape
now has two documented forms, per-invocation (flag) and per-project
(config), both FORCE-logged, and the config form is the one ADR-0016's
"debugging, not routine convenience" framing did not anticipate — the
namespace-less host is routine, and the fix for routine is config.

## Calls I made (flagged; ratify or correct)

- **Flag shape.** `--no-sandbox` is one-direction (`store_true`). Under
  config-off it is redundant, never contradictory; both FORCE lines
  print when both are present and the config line says "(--no-sandbox
  is redundant beside it)". No `--sandbox` force-on was added (see
  Proposals). A debugging session that needs one confined run on a
  config-off project edits the key.
- **Telemetry semantics** (ratified exactly as proposed in Q1):
  `sandbox_escaped` keeps its flag-only meaning; `sandbox_confined`
  unconditional with `true` as the known-negative; `sandbox_off_source`
  always present, `null` when confined, `"config"` whenever the key
  disabled (even beside the flag), `"flag"` when only the flag did.
- **Resolution point.** The config value is resolved at *pipeline
  start* — a separate `merged_config(repo)` read beside the flag's
  FORCE line, before extraction — rather than at the staging read
  where `network` is resolved. Reason: the FORCE line must precede any
  script and sit beside the flag's line, and the value must be
  identical for the three script runs and the stamps (one read, one
  `sandbox_on`). A malformed `[sandbox]` therefore fails a few lines
  earlier than before; `cmd_apply` already reads the merged config
  before the pipeline, so no new failure class.
- **Wizard.** BALE.md §3.6 says an un-walked configurable is a
  contract violation, so the project wizard walks `sandbox.enabled`.
  The shared `_prompt_bool` printed "effective: (unset — off)" for an
  absent key, which would have told operators an absent key means the
  sandbox is off. It gained an `unset_effective` keyword (default
  unchanged, so every other bool renders as before); this key passes
  "(unset — sandbox ON)". Pinned by
  `test_project_wizard_enter_leaves_sandbox_on`.
- **Dry-run.** `--dry-run` under config-off logs nothing, the same
  exemption the flag has — nothing runs. Pinned by test.
- **Network grant beside config-off.** Not exercised (nothing confined
  ran); the existing "grant is not exercised" note now names whichever
  escape actually bypassed. Pinned by test.
- **Refusal text.** `SandboxUnavailableError` names both bypasses. On a
  namespace-less host with no project key, the apply refuses naming
  the key it should set — the actionable path. Pinned by the
  `test_global_enabled_false_does_not_unconfine_an_apply` branch that
  runs only without namespaces (see below).

## Test structure change worth a look

`SandboxApplyE2ETest` carried a class-level `@skipUnless(USERNS)`, and
that decorator is inherited by subclasses — my first cut of the
config-off class silently skipped everywhere. The fixture (repo, pack,
escape-write validation.sh, grant helper, readers) is now
`_SandboxApplyFixture` with no tests of its own; the gated class and
the new `SandboxOffByConfigE2ETest` both inherit it. The three existing
cases are byte-identical apart from the added posture-pair assertions.

I ran the sandbox suite both ways: with namespaces (54/54) and with
`unshare` removed from `PATH` (54, 9 skipped — the config-off cases
ran and the "global key never unconfines" case took its refusal
branch). That second run is the motivating host in miniature.

## Claims

Every claimed check is `observed`: `validation.sh` was rehearsed in a
staging-shaped copy (files overlaid, `apply.sh` run, manifest placed)
and exited 0. The stale-phrase assertion was checked non-vacuous
against the unmodified request tree (five hits there, none after).

Untested end to end: the `bale open` dry-run path. It compiles, `bale
open --help` renders the new string, and the change is a two-line
mirror of apply's — but no bundle fixture exists in the shipped suites
to drive it. Listed in `deferred`.

## Surprises

- The forecast listed the schema but neither telemetry write-site;
  the desk owns that (Q1 answer). Nothing else surprised me; the
  `[sandbox]` trio contract made the key a mechanical addition.
- BALE.md had no separate config-key catalog for `[sandbox]` — §8.5's
  network-grant paragraph *is* the documentation — so the new
  paragraph sits beside it with the literal example block.

## Proposals

- **What:** a per-invocation force-on flag (`--sandbox`) so a
  config-off project can run one confined attempt without editing
  committed config. **Why:** the brief anticipated a both-directions
  flag; today's is one-direction, and the only way to test that
  confinement works on a project that disabled it is a config edit
  plus commit. **Scope hints:** `bin/bale` (three parsers),
  `bale_apply.apply_pipeline` and `bale_open` (a tri-state instead of
  `no_sandbox: bool`), one E2E case; after this lands.
- **What:** a bundle fixture builder in `tests/harness.py` so `bale
  open` paths get E2E coverage. **Why:** this session's `bale_open.py`
  change is the second sandbox-adjacent edit there without an
  end-to-end test (the S2 grant threading was the first). **Scope
  hints:** `tests/harness.py`, `tools/craft_response.py --bundle` as
  the producer.
- **What:** desk forecast authoring chases REQUIRED-key write-sites.
  **Why:** the Q1 answer already adopted this; recording it here so the
  notes carry it into the sitting.

## Retry (after HOLD on the first attempt)

The blind checkpoint passed 3/3; my `validation.sh` HOLDed on full
discovery because `tests/test_global_doc_selfcontainment.py` — a suite
the request didn't ship, so I never ran it — rejects install-shipped
schemas that cite project docs or board numbers. Two hits, both mine:
a `$comment` citing `BALE.md §8.5` and "board 75" in two descriptions.
Fixed by version-anchoring only (the rule's own idiom); the loudness
sentence stays. `validation.sh` now replicates that scan group's
needles and shapes over the schema, checked against the probe's
reading of the suite's `SCHEMA_DENIED_PATTERNS`.

Two claims corrections. The first attempt claimed full discovery
`pass` as `observed` — wrong basis: I had observed the four shipped
suites, not the 837-test repo. It is `predicted` now. And
`includes_missing` names the suite; a request whose forecast touches
`schemas/` should ship it (or its rules) — noted for the desk.
