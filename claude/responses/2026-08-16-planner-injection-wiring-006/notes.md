# notes.md — 2026-08-16-planner-injection-wiring-006

## The one thing to expect at apply

Per the brief: the running install is stale — the post-birth
reinstall didn't complete, so the installed `docs/` shows four while
the repo tree carries five. This response fixes both release lists,
and **the post-apply hook runs the merged reinstall script, so the
fix and its first live exercise ride the same apply.** Expect the
reinstall to run and the installed `docs/` to come out at five; until
that hook completes, any `bale pack` against the half-updated install
would fail main()'s missing-docs pre-check (now checking for five) —
which is the fail-loud behavior working, not a defect.

Related: this response's own manifest echoes a **four-key**
`contract_docs` block. That is correct, not a defect — the request
was packed by the four-doc bale (one-apply-behind, exactly the case
the allowed-not-required schema posture exists for).

## Probe findings re-verified against shipped bytes

Everything the brief carried held up, with two confirmations worth
recording:

- `telemetry-record.schema.json` carries **no** `contract_docs` pin —
  the persisted echo rides the response-manifest schema's shape.
  Nothing to change there.
- `tools/craft_response.py` is clean of doc-set pins, as the probe
  found. Untouched.
- `BALE.md` shows **no** four-key `contract_docs` JSON example — the
  §1110 mention is prose about the checkpoint precedent. So the rider
  was exactly the two named sites (§3.1 editable-docs note, §7.5
  injection step), both trued up.
- `scripts/reinstall.sh` derives its list from `RELEASE_FILES` at run
  time — no edit needed; it picks up `docs/PLANNER.md` automatically.
- Line numbers from the probe round were accurate (`GLOBAL_DOCS` at
  250, handoff filter ~2701, missing-docs check ~5544).

## What was verified here, and what only staging can prove

Ran locally, green: the new admission suite (7 tests), the extended
intact-pack E2E (a real pack against the changed `bin/bale` ships
five docs and stamps five provenance keys), the handoff-path suite,
release-list membership + set-equality, schema embeds, the lint's own
suite, the crafter suite — and a **full 481-test sweep, OK**. The
suites whose fixtures carry four-key `contract_docs` blocks
(`test_per_sid_checkpoint`, `test_forecast_ledger`,
`test_checkpoint_provenance`) stay green, which is the
allowed-not-required posture holding against real consumers.

Two caveats on the local runs, both from unshipped files (out of
scope or not included — fine, just declared):

- The E2E harness copies the repo's `docs/` tree; the request doesn't
  ship it. I ran against the request's own injected four docs plus a
  one-line `PLANNER.md` stub. No suite I touched reads PLANNER.md's
  *content* — presence and injection only — so this doesn't weaken
  the observed claims for the touched suites.
- `scripts/build.sh` end-to-end couldn't run here (`upgrade.sh`
  unshipped), so that claim's basis is `predicted` — grounded in the
  synthetic-tree E2E drives in `test_release_packaging`, which drive
  the real build.sh over trees derived from the changed
  `RELEASE_FILES` and passed. The staged run in `validation.sh` is
  the real proof, and it also settles the one assumption I proceeded
  on: that `docs/PLANNER.md` cites no version tag above 0.4.11 (the
  drift guard newly scans it once it's in `RELEASE_FILES`; the bump
  raises the ceiling to 0.4.11, so only a future-dated tag in the doc
  could trip it).

`validation.sh` gates the full test sweep behind `--slow` (the sweep
alone is ~2 minutes, past the §7.6 target); the default run does the
touched suites, the real build.sh, and the wiring assertions in well
under the budget.

## Judgment calls to ratify

- **Exactly-the-set assertions.** The extended pack E2E asserts the
  top-level `.md` set *equals* GLOBAL_DOCS and the provenance keys
  *equal* GLOBAL_DOCS — not membership. Stricter than the old test;
  a stray sixth doc now fails too. Loosen if that's unwanted.
- **Count-free comment phrasing.** The two "beside the four globals"
  comments (bin/bale, bin/bale_pack.py) became "beside the global
  docs" rather than "five" — so the next doc-set change doesn't
  strand them a second time. BALE.md's user-facing sites, by
  contrast, say "five" explicitly, matching the brief's framing.
- **New test file** `tests/test_planner_admission.py` rather than
  extending an existing suite: the admission posture spans both
  schemas and didn't fit `PackInjectionSurface`'s stubbed-`__main__`
  design or `test_schema_embeds`'s equality-only scope. It follows
  the `WaiverSchemaUnitTest` precedent (module-held lint validator).
  In-forecast — it lands under the `tests` directory entry.
- **Schema descriptions carry the rationale.** Both `contract_docs`
  descriptions now explain the allowed-not-required posture inline,
  so the schema alone answers "why isn't PLANNER.md required?".
