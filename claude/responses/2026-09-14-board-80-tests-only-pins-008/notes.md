# notes.md — 2026-09-14-board-80-tests-only-pins-008

Five items, seven files, all under `tests/`. Nothing in `bin/`, no
docs, no VERSION bump. Four of the five went exactly as the brief
sketched; two carry judgment calls you should ratify or correct.

## Ratify: the pair count in test_sanctioned_pairs.py

The brief said "no existing pin needs to move — this is an addition."
One did, and the brief couldn't have seen it without opening the
file: `test_pairs_match_the_docs_enumeration` pinned `len(PAIRS) == 5`
against DOCS.md §9's enumeration, and the new key would have made the
table six entries long while DOCS.md still enumerates five pairs —
the bundled-delivery rider lives on the *same* CLAUDE.md 11.2 /
TARBALL.md 3.4 pair the rescope-offer group already pins.

Two ways out: change the literal to 6 (and the message would then
misstate DOCS.md), or count what DOCS.md actually enumerates. I did
the latter: every key ends in a `(X / Y)` parenthetical naming its
doc pair, so the test now counts distinct parentheticals and still
compares against five. I checked that a bogus sixth doc pair still
trips it. The key string itself is exactly the one the brief gives,
so whatever the checkpoint greps for is there verbatim.

If you'd rather the table stay one-key-per-pair, the alternative is
folding the two extracts into the existing "rescope offer" group and
dropping the new key — but that loses the key the brief pinned, so I
didn't.

## Ratify: which copy of each helper won

The proposal called test_admission_prompts.py "the second copy." It
was a *drifted* copy, in both helpers:

- `_load_module`: the telemetry version loaded unregistered under a
  `<name>_under_test` alias with no `sys.path` change; the
  admission-prompts version puts `bin/` on `sys.path` and registers
  under the bare name. The latter is the superset — `bale_apply`'s
  sibling imports need `bin/` importable, and the telemetry modules
  don't care either way — so it's what landed in the harness. The
  telemetry suite's modules now register in `sys.modules` under
  their bare names where they didn't before; nothing in that suite
  reads `__name__` or `sys.modules`, so I don't expect it to notice.
- `_minimal_record`: the two envelopes differed (`unlocked`/`unlock`
  dated 2026-08-13 vs `applied`/`apply` dated 2026-09-14). Telemetry's
  `StatsToleranceTest` reads `closure_mix["unlocked"]` from records
  built by this helper, so the telemetry envelope had to win. I read
  every `_minimal_record` call in test_admission_prompts.py and none
  depends on the outcome or date; the schema puts no conditional on
  `outcome` either. But I could not *run* that suite here — see
  below — so this is the one place a surprise could hide.

Both rationales are in the harness's banner comment for the next
reader.

## The host gate: config-off, applied via a helper

Your call was either; I took the config-off fixture, for the reason
the brief gave (it keeps the cases testing) plus one more: a
namespace probe of my own could disagree with `bin/bale`'s detection
on some host, and I can't see `bin/bale` to match it. The board-75
case's three fixture lines became `commit_sandbox_off_config()`, and
the three confined `@slow` cases call it first. The board-75 case
keeps its extra FORCE / UNCONFINED log assertions, so it still earns
its separate existence.

Trade-off stated plainly: this suite no longer exercises a *confined*
apply.sh run anywhere. The sandbox wrapper has its own suite
(`tests/test_sandbox_wrapper.py`, out of this row), and this suite's
subject is the operation landing, so I think that's the right split
— but it is a coverage move, not just a fix.

I left `test_forgotten_chmod_is_caught_by_assertion` untouched. It is
ungated and, per your authoring-time verification, green at the
default tier on the namespace-less host; I couldn't reproduce that
run here and didn't want to change the posture of a passing case.
If that observation turns out to have been skip-driven, the fix is
the same one-line helper call.

## What I observed vs. what I predicted

`bin/` isn't in the request (rightly — it's in row 73B's forecast), so
I assembled a partial tree (`docs/`, `schemas/`, `tools/`, `tests/`)
and ran what could run: `test_schema_embeds`, `test_doc_crossrefs`,
`test_sanctioned_pairs`, `test_slow_gate` all pass — those four claims
are `observed`. I also mutated copies of the docs and schemas to check
that each new pin fails, with a readable message, when its subject
moves; they all do.

`test_telemetry_extensions`, `test_admission_prompts`, and
`test_apply_operations` import from `bin/` and are `predicted`. Every
failure in my partial-tree discover traces to the absent `bin/`
tree, none to the edits. The `BALE_TEST_SLOW=1` apply-operations run
and full discovery are behind `--slow` in validation.sh, per the
brief's verification expectations; the slow run additionally asserts
zero skips, since the whole point of item 5 is that tier passing.

## Small things

- `test_telemetry_extensions.py` has an unused `import copy` that
  predates this row. Left alone; not the row's business.
- `test_doc_crossrefs.py` grew `normalize()` and `top_level_section()`
  — the first is a duplicate of test_sanctioned_pairs.py's three-line
  normalizer. Two copies is tolerable; a third would be the harness's
  cue.
- validation.sh's tests-only check reads `.bale-manifest.json` and
  asserts every `changes[]` path starts with `tests/` — a cheap
  backstop for the row's first constraint, `[SKIP]` outside staging.

## Proposals

- **What:** Move `normalize()` (the whitespace-collapse used by both
  doc-pin suites) into `tests/harness.py`.
  **Why:** Two identical copies as of this row; the harness's own
  doctrine is one home per helper.
  **Scope hints:** `tests/harness.py`, `tests/test_doc_crossrefs.py`,
  `tests/test_sanctioned_pairs.py`; trivial, any time.
