# notes — 2026-09-15-board-68-open-gate-order-012

Everything the brief asked for landed, bumpless, on six of the seven
forecast paths (`tests/test_bundle_manifest.py` turned out not to
need touching — the gate-first order never reaches the validator's
pins). 1028 tests pass, 15 of them new. A few things worth your eye.

## One-apply-behind

The apply that lands this runs the *old* `bale open` / `bale pack`
code one last time — the gate order, the `FORCE: FORCE:` line, and
the old opener sentence are all still in force for this very apply.
The staging validation runs the new code (from staging), so the
verdicts are about the shipped bytes, not the tool applying them.

## Decisions to ratify

**The supersession hazard, and `pending_supersession`.** The brief's
desk read didn't mention it, but `cmd_pack` runs the `--supersedes`
exchange *before* its disjointness gate: an accepted supersession
closes the parent, which is exactly what clears the collision. An
early gate in `open` that didn't account for this would falsely
refuse every split-supersession bundle — the existing
`test_supersede_intent_accepts_under_piped_stdin` packs a child
whose forecast intersects its parent's, and it would have broken.
So `run_forecast_disjointness_gate` grew an optional
`pending_supersession` sid that the pre-flight excludes from the
conflict set. The replay's own gate (which runs after the exchange)
stays authoritative: a declined supersession still refuses there,
exactly as today. `cmd_pack` never passes the parameter. This is the
one place the pre-flight is deliberately more permissive than the
replay; it can never refuse something the replay would admit.

**Gate order inside the pre-flight: existence, then disjointness.**
`cmd_pack` runs them the other way round on the fully-specified path
(disjointness in pre-flight, existence post-wizard). I put existence
first in `pack_argv_preflight` because a forecast entry that doesn't
exist is an argv defect in its own right, and a collision computed
over a phantom path names something you can't reason about. The
practical consequence: a bundle that would fail *both* refuses with
the existence text via `open` but with the disjointness text via a
hand-typed `pack`. Admit/refuse is identical either way; only the
text differs. Easy to flip if you'd rather mirror pack's order.

**The "config-judging refusal family" — five sites.** The brief
named the open-side no-base refusal and "the `[validation] base …
not resolved` refusal on pack". That second phrase matches a *log*
line (the read-only waiver), not a refusal, so I took the family to
be every refusal whose judgment is about `[validation] base`:

1. open: bundle ships a checkpoint, project pins no base;
2. pack `--checkpoint-file`: no base configured;
3. pack `--checkpoint-file`: base is a literal path (v1 scope);
4. pack per-sid resolved-existence pre-flight: base resolves to a
   path absent at HEAD;
5. `build_provenance_block`'s two defense-in-depth refusals (same
   condition as 4, caught late).

All five append the same tail from one helper,
`bale_pack.config_judgment_suffix(repo)`:

    Project root: /abs/repo; config judged: /abs/repo/bale.toml
    (read|absent), /install/user/bale.toml (read|absent).

Two wording choices inside it: the global file, when it *does* exist,
is marked "(read; [validation] is project-layer only, so this file
does not supply the base)" — without that, a `[validation]` table in
the global file would look consulted when `get_validation_base`
ignores it. And on the pre-git-init path (`repo is None`, reachable
from `checkpoint_file_base_or_refuse`) the tail says "Project root:
none (not inside a git repository, …)" rather than naming a root
that doesn't exist. Tests pin sites 1–4; site 5 is defense in depth
behind 4 and unreachable through the CLI without desyncing the
peek/allocate pair, so it carries no test.

**The whole-tree remedy lead also applies to `handoff`.** The gate is
shared, so a handoff colliding with a `["."]` session now reads
"narrowing this handoff with --write cannot clear it. Remedies that
can: apply that session's response first, run `bale unlock <sid>` …,
or narrow ITS forecast …". The handoff suite's collision case is a
partial overlap, so its "Narrow this handoff's forecast" pin is
untouched and passes. The `--supersedes` alternative still trails
the lead on the pack caller, as before.

**A bonus behavior from moving the parse.** `build_parser().parse_args`
now runs before the dry-run, so a stored argv the CLI can't parse
refuses at argparse (exit 2, usage text) with no oracle spent. Today
that error also fired, but after the ~minutes of dry-run. Pinned in
`test_unparseable_stored_argv_refuses_before_the_dry_run`.

**The replay re-runs both gates.** `pack_argv_preflight` is a cost
ordering, not a substitute: `cmd_pack` still evaluates existence and
disjointness at its own sites during the replay (cheap; pack's
contract stays whole; the blindness gate runs only there, per the
brief). The pre-flight discards the gate's journal tuple — the
replay's run is the one that journals once the session log opens.

## Where to look on review

- `bin/bale_pack.py`, the block between `run_forecast_disjointness_gate`
  and `checkpoint_blindness_preflight`: the four extracted helpers
  and `config_judgment_suffix`. `cmd_pack`'s three edited sites are
  pure call-swaps (`resolve_write_forecast` ×2,
  `refuse_missing_scope_paths` ×1, `forecast_final_at_parse` for
  `gate_deferred`); the expressions they replaced were duplicated
  inline before, so this is a small de-duplication inside `cmd_pack`
  too.
- `bin/bale_open.py` `cmd_open`: compose → parse → pre-flight now
  sits between member extraction and the checkpoint leg; the replay
  reuses the parsed namespace. Both `log(force=True)` calls lost
  their literal `FORCE: ` prefix.
- The opener pin lives in `tests/test_pack_guards.py`
  (`OpenerShapeSentenceTest`) rather than `test_pack_opener.py`,
  because the latter is outside the forecast — see Proposals. The
  sentence is mirrored as a constant in the test (the suites never
  import bale), whitespace-collapsed for the compare, and the test
  also asserts the sentence is the last thing before the closing
  scissor line and that "Ask me if anything is unclear" is gone.
- `tests/test_include_group.py` gained `TestThisRepoGroup`, the one
  class in that suite that reads the real `bale.toml` off disk rather
  than a scratch one; it pins `tools` in the pulls, that every pull
  exists, and that every harness `INSTALL_TREES` entry rides the
  group as a pull or a trigger.

## Proposals

**BALE.md: describe open's new pipeline order.** *What:* one sentence
in the `bale open` row of §5's command table and in §6.7 saying the
arg-inspectable pack gates (and the argv parse) run before the
checkpoint dry-run. *Why:* §6.7 currently describes the pre-68 order
(verify → dry-run → replay), which this session made stale. *Scope:*
`BALE.md`, held this wave by `board-102-explicit-name`.

**`bale handoff` should call `refuse_missing_scope_paths`.** *What:*
`bin/bale` `cmd_handoff` (around line 3524) carries its own copy of
the `--write path does not exist` loop with identical wording. Now
that the gate is a module-level helper in `bale_pack`, handoff can
call it and the two copies collapse to one. *Why:* the brief's
one-implementation-per-gate constraint; this is the last remaining
copy. *Scope:* `bin/bale`, held this wave by `board-102`.

**Relocate the opener shape-sentence pin.** *What:* move
`OpenerShapeSentenceTest` from `tests/test_pack_guards.py` into
`tests/test_pack_opener.py`, which already pins identity carriage and
the clock sentence with the same scissor-line helpers. *Why:* one
suite per surface; the mirrored `OPENER_BEGIN`/`OPENER_END` constants
now exist in two test files. *Scope:* both test files; trivially
independent of everything else.

**A `bale open --gates-only` (or `--dry-run`-less) spelling.** *What:*
an open-side flag that runs the pre-flight and stops, for a desk
that wants to check a bundle's argv against the registry without
spending the oracle. *Why:* the pre-flight is now a clean seam and
would cost one flag; the specimen's ~9 minutes were the motivation
for the whole row. *Scope:* `bin/bale_open.py`; only if the desk
actually wants it — not something this row asked for.
