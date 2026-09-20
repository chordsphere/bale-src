# notes — 2026-09-20-board-104b-pack-telemetry-008

## Baseline and after

On the 0.4.39 tree as shipped, the full suite (`python3 -m unittest
discover -s tests -t .`) ran 1392 tests OK, with 48 skipped by the slow
gate, in about 250 s. `validate.sh` passed 91 of 91. Both match 104a's
numbers.

After this session the suite runs 1419 tests OK with the same 48 skips.
The 27 new tests are 20 in the new suite, 6 in `test_include_group.py`
and 1 in `test_context_pack.py`. `validate.sh` passes 92 of 92.

The session paused once on a tool-call limit and resumed on Continue
with context intact. That was not a compaction.

## What you asked me to state

**Where `packed_at` lives, and why.** It lives in the `opened` attempt's
`provenance` block, as the desk leaned.

What pinned that block to exactly two keys was not the schema: its
`additionalProperties` was already true. Two things did:

- `test_provenance_at_open`'s exact-pair assertion on the attempt.
- `_persist_open_provenance` handing one dict to both writes. The
  registry's `provenance.json` and the attempt shared it.

So the attempt now gets a copy with `packed_at` added. `provenance.json`
stays exactly the pair, and its own test still pins that. I updated the
attempt assertion to expect the manifest's `packed_at`.

`bale stats` passes the block through as `provenance` in the dossier, so
`stats --json` shows the extra key there too. That is additive, and no
stats test pinned the exact dict. The schema description names the
close desk's reconstruction as the consumer, and there is no stats read
side.

If a manifest has no usable `packed_at` (a hand-rolled request), the
attempt carries the pair alone. The omission is logged.

**The sweeping-pack field.** The field is `swept_by`.

- **How it is written.** `_run_readonly_sweep` still runs before the sid
  exists and closes the sessions as before. Once the sid is minted,
  `cmd_pack` calls `stamp_swept_by(repo, swept, sid)` for each swept
  sid. That call enriches the latest `closed-read-only` attempt in
  place, without a new attempt or an envelope change.
- **How it is committed.** `sweep_swept_by_stamp` then commits each
  rewrite as `[bale sweep <swept>] swept_by <sid>`. That is board 107's
  fix, applied to the read-only sweep.
- **Tests.** The new suite pins a clean tracked tree with the sweep on,
  and pins HEAD and the working tree agreeing on the swept record. It
  also covers several swept sessions in one pack, each stamped.
- **When the stamp fails.** The stamper logs loudly (force) and returns
  None. The sweep then commits nothing ("nothing to commit"), the pack
  stands, and the attempt simply lacks the field. Absent reads as
  "sweeping pack unrecorded", exactly as on every earlier
  `closed-read-only` attempt.
- **When the pack aborts.** A pack that aborts after the sweep but
  before the sid (a cap refusal, or the no-readme guard) never stamps.
  This is the same window the supersession close already has, and the
  schema says so.

`stamp_superseded_by` and `stamp_swept_by` now share one writer,
`_stamp_closure_attempt`. The `superseded_by` log wording is unchanged
character for character.

**The three `sweep`/`include_group` shape decisions.**

1. *Close sweep vs stamp sweep.* Each entry carries an `event` key: one
   of `superseded-by-split`, `closed-read-only`, `superseded_by`,
   `swept_by`, owned as `PACK_SWEEP_EVENTS` in `bale_report.py`.
   - Please look at this one. Your pin says each entry carries `sid`
     "plus the four keys". I read that as a floor, so the entry has six
     keys, in the order `sid, event, status, detail, sha, files`.
   - If you meant exactly five, the alternative is to encode the event
     in `detail`. I think that would be worse, because `detail` is
     `sweep_commit`'s human string.
   - Entries are in event order. That puts every pre-sid close before
     every post-sid stamp: a parent reads `superseded-by-split`, then
     `superseded_by`.
2. *`[apply] sweep` off.* The entry stays, and its four sweep keys are
   nulled: `status`, `detail` and `sha` null, `files` `[]`.
   - That is apply's own null meaning, "the sweep did not run", carried
     per entry.
   - I kept the entry because the write it records did happen. A
     consumer can still see what the pack closed and stamped when no
     commit ran.
   - So `[]` means strictly "closed nothing", which matches your pin.
3. *Non-null `include_group`.* The object is structured:
   `{name, state: "engaged"|"opt-out", triggers, pulled, row}`.
   - `triggers` are the configured trigger entries the includes hit, and
     are `[]` on opt-out.
   - `pulled` is the paths added, and is `[]` when already covered or on
     opt-out.
   - `row` is the human row's string verbatim. A test pins that it
     matches the printed row.
   - The key is null exactly when the human report prints no row.

**The supersession half of item 3 was already met, as you read it.**
`stamp_superseded_by` is called from `cmd_pack` right after the sid is
minted, and the attempt carries the child's sid. I added nothing beside
it. `test_supersession_parent_appears_twice` asserts `superseded_by`
names the child and that no `swept_by` lands on that attempt.

**The droppable rider (cap-loop extraction) was not taken.** It goes
back to the registry.

**Out-of-forecast paths: none.** All twelve paths sit under
`bin/bale_pack.py`, `bin/bale_report.py`, the schema, `BALE.md`,
`tests`, `validate.sh`, `bin/VERSION` or `claude/changelog`. `bin/bale`
is untouched: `close_session_with_record` already returned the sweep
result as its third element, which the two pack call sites had been
discarding.

## Item 4: a deviation to ratify

The standing pin already exists. Board 69 (d) landed it as
`ToolsHermeticPin` in `tests/test_craft_response.py`, and it covers all
three failure shapes and more:

- non-stdlib imports, and relative imports;
- network-capable modules, plus process and FFI escape hatches;
- `__import__`, `import_module`, `exec` and `eval`;
- a walker self-test, so it cannot pass vacuously.

`-k stdlib_only` selected nothing only because of its method names. So I
renamed its five methods `test_stdlib_only_*` and changed no assertion.
`-k stdlib_only` now runs those 5 tests, and they pass.

Writing a second walker in a new file would have put two copies of one
rule side by side. If you would rather have the new file anyway, it is a
move rather than a rewrite.

## Riders

- **Context report home.** `format_context_pack_json` moved into
  `bale_report.py`, next to `format_pack_json`. Its docstring and the
  outcome-vocabulary sentence both name `context-packed` now.
  `cmd_pack_context` imports it from there.
  - The output is byte-identical, including the compact separators.
  - `test_context_pack` now pins the exact line and asserts the pack
    module no longer defines the renderer.
  - BALE.md §7.8 is updated to match.
- **`validate.sh`.** Added one check, `pack --help mentions --context`,
  with a comment line.

## Look closely at

- **Self-containment guard.** It caught my first schema draft citing
  "board 104b" in descriptions, and I removed those citations. The
  consumer is still named, but by what it does ("the close desk's
  reconstruction of a sitting"), not by board. If "desk" or "sitting"
  also reads as project-local to you, that is a wording change inside
  the two descriptions.
- **The unit test's `__main__.log` patch.** `stamp_swept_by`'s failure
  path imports `log` from `__main__`, as the siblings do. The unit test
  patches `__main__.log` and restores it in `tearDown`.
- **BALE.md section numbers.** Your §7.7, §7.8 and §8.9 numbers held.
  - §7.7: the include-group paragraph grew, and a new "sweep ledger"
    paragraph sits right after it.
  - §8.9: a "Pack-side stamps" paragraph sits between closure_reason
    and update semantics. It names the schema as the fields' home.
  - Nothing was touched in 99b's queued true-ups.

## Proposals

1. **A `bale stats` dossier line for `swept_by`.**
   - What: render "swept by <sid>" beside the existing "superseded by"
     line in the per-session dossier, and carry the field in the attempt
     view.
   - Why: `_attempt_view` in `bin/bale_stats.py` already surfaces
     `superseded_by` by name. `swept_by` now has the same meaning for
     the other pack-side close, but the drill-down cannot show it.
   - Scope hints: `bin/bale_stats.py`, `bin/bale_report.py` (the dossier
     renderer), and `tests/test_stats_drilldown.py`.
