# notes — 2026-08-30-exchange-packaging-001

## upgrade.sh left alone (brief item 3)

I did not add `schemas/exchange-record.schema.json` to
`REQUIRED_RELEASE_MEMBERS`, for two reasons that point the same way:

- **Precedent.** The subset is a pre-wipe spot check, not a layout
  check (build.sh's own comment), and it already omits the two most
  recent schemas — `escalation-record` and `bundle-manifest` are in
  both release lists but not in the subset. `exchange-record` follows
  that lineage exactly; adding it would break the established pattern
  without making any upgrade safer that the tree-coverage and
  list-agreement guards don't already make safe at build time. The
  subset relation the pre-flight asserts (`REQUIRED_RELEASE_MEMBERS ⊆
  RELEASE_FILES`) holds unchanged with the new entry in
  RELEASE_FILES only.
- **Forecast.** `upgrade.sh` sits at repo root and the session's
  write forecast is `install.sh`, `scripts/`, `tests/` — a change
  there would be out-of-forecast drift. Since the precedent says the
  change isn't needed, there is nothing to ship-and-enumerate.

If you read the subset's intent differently — e.g. you want every
schema bale hard-requires at pack/apply time spot-checked pre-wipe —
that's a one-line follow-up, but note the same argument would then
apply to `escalation-record` and `bundle-manifest` too.

## Verification detail worth knowing

- Adding the schema to RELEASE_FILES also adds it to build.sh's
  version-tag-drift scrape surface and its JSON parse pre-flight. I
  checked both against the shipped file: it parses, and its only
  v-prefixed tag is `v0.4.18`, equal to `bin/VERSION` (0.4.18) — the
  boundary that passes. No bump needed, per the constraint.
- The packaging suite's E2E case (`BALE_TEST_SLOW=1`) drives the real,
  modified build.sh over a synthetic tree whose file set is derived
  from the modified RELEASE_FILES, so the new entry is exercised end
  to end (synthesized as a parseable `{}` stub), not just
  list-checked. Observed green: 13/13 with the gate open, 12+1 skip
  with it closed.
- The "full test suite" claim is `predicted`, not `observed`: my copy
  of `tests/` holds only `harness.py` and the packaging suite, so
  discover here can't see the other suites the real checkout has. The
  packaging-suite claim is `observed`. Nothing this session touched
  is read by the other suites as far as the shipped context shows
  (the harness's INSTALL_TREES are bin/docs/schemas/tools — none of
  the three modified files).
