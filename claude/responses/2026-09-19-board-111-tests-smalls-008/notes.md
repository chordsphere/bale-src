# Notes — 2026-09-19-board-111-tests-smalls-008

Tests only, bumpless. All three changed paths are in the forecast.
`tests/test_sanctioned_pairs.py` is forecast but untouched: the relay
pin went to `test_doc_crossrefs.py` (reasoning below). `docs/`,
`tests/harness.py`, `tests/test_apply_preflight.py` and every path the
sibling forecasts are untouched.

The bumpless invariant, stated relative to this response: `changes[]`
holds three `tests/` paths and nothing else, with no `bin/VERSION` and
no `claude/changelog/` record. `validation.sh` asserts it against the
staged manifest rather than against the tree's `VERSION`, because the
sibling may bump `VERSION` in this same wave.

Baseline: before I changed anything, `test_include_group` and
`test_changelog_record` were green in the shipped tree, along with the
four in-scope suites and `test_harness_cli_loader`. So no packing
defect. After the change the full `unittest discover -s tests` run is
1330 tests OK (48 skipped).

## Decisions to ratify

**Craft suite: `_load_cli` is imported inside `ExchangeBlockParity.setUpClass`, not at module top.**
- Why this was a real question:
  - The suite's module docstring opens with "no tests/harness.py, stdlib only".
  - Unlike `test_thread_status`, it currently runs under all three forms: discovery, direct, and the dotted `-m unittest tests.test_craft_response`.
  - A module-level `from harness import` would have broken the dotted form for all 160 tests.
- What I did instead:
  - The import is deferred to the one class that needs it.
  - It is preceded by the same `tests/`-on-path-when-absent guard the two doc-pin suites use.
  - The docstring names that one exception.
- If you'd rather the suite simply join the harness at module scope, it's a two-line move plus the path guard.
- The old explicit `sys.path.insert(0, bin/)` is gone too. `_load_cli` adds `bin/` when absent and keeps it, which is what the bare `import bale_validate` resolves through.

**Docstring sentence.** "…so the loader stays as it is" now reads "…so bin/bale stays the module loaded. How it loads is tests/harness.py's _load_cli(), the one home for that loader." That keeps its point (which module, for the re-exports) and drops the claim about how.

**Thread-status: inlined, no thin wrapper.** `load_bale_module` had one caller, so a wrapper would have been a fourth name for the same thing.
- The brief says `_load_cli`'s reach-back limit does not bite either suite today, and I checked that claim function by function.
- `_session_state_and_hint` is bin/bale's own function.
- `format_clarification_value` lives in `bin/bale_report.py` and is re-exported, not defined in bin/bale. Its body has no `from __main__ import`, so it is safe.
- The comment at the call site says exactly this.

**Measured hygiene.** Two `setUpClass` rounds of each class with the old loaders took the `bin/` entries on `sys.path` from 1 to 7. With `_load_cli` it stays at 1. `validation.sh` asserts the "unchanged" form of that, and also that `bale_parity` / `bale_under_test` no longer register in `sys.modules`.

**Relay pin home: `test_doc_crossrefs.py`.**
- Why not `test_sanctioned_pairs`: that suite is DOCS.md §9's enumeration of doc↔doc twin passages. This pin is doc↔code, so putting it there would make the suite's own docstring untrue.
- Why `test_doc_crossrefs`: it already carries "the ruling stays stated where the docs say it is" pins, with the same `normalize()` and section-body discipline.

**Relay pin shape: against the code's builder, not a constant.**
- How the check is built: the sentinels come from `bale_report.relay_sentinels("<sid>", RELAY_TO_WORKER)`.
- Where it looks: they are matched as whole backticked spans, BEGIN before END, in the §7 *lead* only (body up to `### 7.1`, via a new `section_lead()` with its own self-test). A copy elsewhere in §7 therefore can't satisfy the pin.
- Prose pinned alongside: two narrow clauses of the same paragraph (the whole-line-sentinels lead clause and the whole-of-the-failure-context sentence).
- Constant-level guard: `test_builder_addresses_the_worker` fixes the builder's output to the literal `to worker` pair. Without it, a code change making both sides agree on some other wording would pass silently. So when the addressing changes, that test is the one place to update, deliberately.
- The trade-off: the doc-pin suite now imports one `bin/` module. The docstring's "nothing runs" line was amended to say so. `bale_report` is stdlib-only at module scope and the builder is pure.

**The pin bites, shown twice.**
- In the suite: `test_pin_bites` runs four mutations of the real lead and each must produce gaps: paragraph struck, re-addressed to planner, BEGIN/END swapped, sentinel unbackticked. It also asserts the unmutated lead has none.
- In `validation.sh`: scratch copies of `bin/ docs/ tests/` are mutated for real (doc re-addressed, paragraph struck, and `relay_sentinels` changed from `to` to `for`). Each must fail the pin, and an unmutated control must pass it.

**Registry rider.** The `_section_29` test-id rename in `test_craft_response.py` is confirmed stale on my side too: no such identifier remains. Nothing was done.

## Exec bits

`test_craft_response.py` and `test_doc_crossrefs.py` are `0755` in the repo, and the `files/` overlay strips mode. `apply.sh` restores both with `chmod +x`, and `validation.sh` asserts them (TARBALL.md §7.7). `test_thread_status.py` is `0644` and stays so.

## Proposals

- **What:** refresh `tests/harness.py`'s comment block above `CLI_PATH` (~437–449). It says the shape "reconciles the two ad-hoc copies already in the tree" and ends "Adopting it in those two suites is left to them — neither is in this row."
  - **Why:** after this response those copies are gone, and the comment reads as pending work. Its history sentence (what the shape reconciled) is still worth keeping, in the past tense. I didn't edit it because `harness.py` is not forecast and the goal doesn't require it.
  - **Scope hints:** `tests/harness.py` only, comment text only. It can ride any later row that holds that file.
- **What:** consider giving `test_thread_status.py` the same `tests/`-on-path guard the doc-pin suites carry, so its docstring's `-m unittest tests.test_thread_status` run line works.
  - **Why:** that dotted form errors today, both before and after this change. It is a module-level `from harness import` without the guard. I didn't add the guard here because it's outside the stated goal (behavior-preserving adoption). A proposal seemed better than a silent scope stretch.
  - **Scope hints:** `tests/test_thread_status.py` only. Several other harness-importing suites likely share the same stale run line, so a sweep may be the better unit.
