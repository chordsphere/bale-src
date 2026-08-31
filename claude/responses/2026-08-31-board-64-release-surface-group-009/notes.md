# Notes — 2026-08-31-board-64-release-surface-group-009

## Out-of-forecast paths (admit per path at apply)

Three `changes[]` paths sit outside the stamped write forecast
(`BALE.md`, `bin/bale_pack.py`, `bin/bale_config.py`, `validate.sh`,
`scripts/build.sh`, `install.sh`). Each below with why the goal
required it:

- **`bin/bale`** (modified) — the `--no-include-group` opt-out flag.
  The brief pins a loud opt-out "naming the group and the flag"; the
  pack argparse surface lives in `bin/bale`, not `bale_pack.py`, so
  any new pack flag lands here. One `add_argument` block, nothing
  else touched.
- **`bale.toml`** (modified) — the configured `release-surface`
  group itself. The brief offers "config-driven group in bale.toml"
  as a sanctioned mechanism and the goal needs the concrete instance
  live in this repo; without this entry the mechanism ships dormant
  and the missing-context class the goal retires stays unretired.
- **`tests/test_include_group.py`** (created) — worker-determined
  new file per the brief's own note ("a module, a test suite" is
  expected drift). 12 hermetic cases; outcome contract 2 asks for
  new coverage in the suite.

Forecast entries not consumed: `validate.sh`, `scripts/build.sh`,
`install.sh` — the packaging-coupling set was priced in advance, and
the group needed no packaging change (no new shipped install files,
no VERSION movement, no schema).

## Design decisions to ratify

- **Mechanism: hybrid, config-driven, one group per project at v1.**
  A generic `[pack]` section in `bale.toml` — three flat keys
  (`include_group`, `include_group_triggers`, `include_group_pulls`)
  read as one validated unit — with the engagement logic in
  `bale_pack.py`. Flat keys rather than `[include_groups.<name>]`
  because the keyed sub-table is the wizard-unwalkable shape the
  `[validation].required` ruling already rejected; the multi-group
  widening is recorded on `PACK_VALUES`. Full trio contract shipped
  (typed accessor, wizard walk, renderer branch), so `bale config
  init` re-runs preserve the group instead of dropping it.
- **Project-layer only**, same rationale as `[validation]` and
  `[sandbox]`: a global include group would engage in every repo the
  install touches and refuse loudly wherever its pulls dangle — the
  every-repo hazard those rulings rejected. `merged_config` never
  inherits `[pack]`.
- **Include-side only; no forecast seeding.** The brief's goal
  sentence is include-side and marks forecast seeding an optional
  flagged extension. I deliberately did not take it: group additions
  join the walk, `context_included`, and the blindness gate's read
  includes, but never any forecast expression — a pack whose
  forecast defaults to its include set records the *user's*
  includes. Reasoning: reads don't lock (ADR-0015), the group is
  reads, and auto-widening a session's lock on engagement would
  silently block siblings — the concurrency cost the separation
  exists to remove. `test_sibling_pack_alongside_pulled_paths` pins
  the consequence: a sibling can forecast a path the group merely
  ships. If the desk wants seeding, it composes cleanly as a fourth
  key later.
- **Dangling configured pull → loud pack refusal at engagement**
  (BALE.md §11 row 35), matching `--include`'s existence posture and
  the no-silent-skips rule; dormant when the group doesn't engage
  (the at-use posture of a configured hook). Half-configured group
  (name without lists, or lists without name) is fatal at config
  read everywhere the merged config is consulted.
- **Opt-out strictness both ways.** `--no-include-group` with no
  configured group, or with a name that isn't the configured group's
  exact spelling, refuses — a typo'd opt-out that silently opts out
  of nothing would be the silent skip the brief forbids. The opt-out
  line is FORCE-prefixed deliberately: it overrides an automatic
  behavior the project config pinned, which is the audit-trail class
  the FORCE queue exists for (and the queue replays it into the
  session journal once the sid opens).
- **Engagement relation is `scope_paths_intersect`** — the existing
  primitive, so "includes cover paths under bin/" means exactly what
  the forecast gates mean by coverage: directory entries cover
  subtrees, `.` covers everything. A whole-tree default pack engages
  with an "already covered" line and adds nothing.

## Places to look closely on review

- `cmd_pack`'s two `read_includes=` sites now carry
  `args.include + group_adds` — the read-half blindness key sees the
  group's additions (they will ship), while every forecast
  expression around them is untouched. Worth a careful diff read
  since the forecast/read split is the load-bearing invariant.
- The engagement block sits pre-wizard (includes are final at
  arg-parse; the wizard never collects them), so both the pre-flight
  and deferred gate sites see one computed value.

## Proposals

- **`include_group` key in pack's `--json` report.** The human
  report carries the durable "include group" row; the JSON report
  can't without a `format_pack_json` change in `bale_report.py` — a
  third out-of-forecast file for one additive key this session, so
  proposed instead, following the session-opener precedent already
  recorded at that call site. Scope: `bin/bale_report.py`,
  `bin/bale_pack.py` (pass-through), a `--json` case in
  `tests/test_include_group.py`.
- **Sweep BALE.md §7.5/§7.7 for a one-line group mention.** §7.2
  carries the full contract and §11 row 35 the refusals; the walk
  (§7.5) and output (§7.7) sections could each name the group in one
  sentence for readers who enter there. Doc-only, low value, rides
  any future BALE.md touch.
