# Notes — 2026-09-19-board-113-dotted-run-form-011

Tests only, bumpless. `changes[]` holds three `tests/` paths and nothing
else: no `bin/VERSION`, no `claude/changelog/` record. `validation.sh`
asserts that against the staged manifest, not the tree's VERSION.
Nothing under `bin/`, `docs/` or `tools/` is touched, and neither is
`tests/test_craft_response.py`.

## Admit these two paths at apply

Both are new files outside the forecast (`tests/harness.py`,
`tests/test_thread_status.py`):

- `tests/__init__.py` — the single-point fix. The dotted form only puts
  the repo root on `sys.path`, so the only place that can add `tests/`
  for every suite at once is the package init.
- `tests/test_dotted_run_form.py` — the pin the goal asks for. Neither
  forecast file is a fitting home: the pin covers the whole tree, and it
  must not import harness, so that it still runs if harness breaks.

```
bale apply response-2026-09-19-board-113-dotted-run-form-011.tar.gz --allow-out-of-scope tests/__init__.py --allow-out-of-scope tests/test_dotted_run_form.py
```

Both are also listed in `feedback.self_reported.forecast_departures`.

## Baseline, before any change

- `test_include_group` and `test_changelog_record` were green on the
  shipped tree, so there's no packing defect.
- Full `discover -s tests` ran 1349 tests OK (48 skipped).
- In the dotted form from the repo root, 56 of 68 suites failed to load,
  all on the bare `harness` import, and 12 loaded. Same as the desk
  measured.

## What the fix does, and what I checked

`tests/__init__.py` is the desk's four lines plus a docstring saying
which run form executes it (only the dotted one).

- It inserts `tests/` at `sys.path[0]` when absent. That is the same
  entry discovery adds, so a bare name resolves to the same file in all
  three forms.
- It imports nothing and exports nothing.

Measured with it in place:

- **Every suite dotted, one process each:** 67 exit 0.
  `test_handoff_fixture` exits 5 ("no tests ran"): it's a fixture module
  with no tests, and it loads cleanly. The per-suite counts sum to 1349,
  exactly the discovery count.
- **All 69 suites dotted in one process:** 1352 OK (48 skipped).
  - This was the real risk. Helper suites such as
    `test_per_sid_checkpoint`, `test_handoff_fixture` and
    `test_pack_guards` load twice in that run, once as `tests.X` and
    once as bare `X`.
  - Nothing keys on module identity across them, so it is clean.
  - A plain `discover` has one copy of each, as before.
- **Full discovery with the package present:** 1352 OK (48 skipped). The
  extra three are the pin suite's tests. Discovery never executes the
  init, because the start dir and the top-level dir are the same.
- **`test_thread_status` in all three forms:** passes. That's why it is
  untouched: its docstring's `-m unittest tests.test_thread_status` run
  line simply works now.

The desk's open questions:

- **`_load_module` and `_load_cli`:** unaffected. They compute
  `REPO_ROOT` and `BIN_DIR` from `__file__` and register under bare
  names. `test_harness_cli_loader` passes dotted.
- **Suites computing paths from `__file__`:** same file, same path.
- **Anything enumerating `tests/`:** none does.
- **Why the tree went without an init:** I found nothing that says.
  - The only `__init__.py` references are synthetic fixtures in
    `test_pack_guards` and `bin/bale_pack.py`'s row-84 scan.
  - That scan still reads the new init correctly: its imports are
    stdlib, and no suite writes `from tests import`.

One behavioural change to know about: a bare `python3 -m unittest` with
no arguments, run from the repo root, now discovers the whole suite,
where before it found nothing. None of `validate.sh`,
`scripts/build.sh`, `install.sh`, `upgrade.sh` or `bale.toml` runs that
form, so I proceeded. It's recorded under `assumptions`.

## The pin

`tests/test_dotted_run_form.py` loads each `tests/test_*.py` as
`tests.<suite>` the way `-m unittest` does (`loadTestsFromName`, then
`loader.errors`).

- **Isolation.** Each load runs in a fresh interpreter, with the repo
  root as cwd and `PYTHONPATH` cleared. That way no suite can pass on a
  path entry that something else left behind.
- **Load only.** It does not run the suites' tests; discovery does that.
- **Speed.** It takes about 12 s, in 8 parallel workers.
- **Coverage.** The glob is the discovery default, so the next new suite
  is covered with no edit. The sweep asserts it saw itself, so an empty
  glob can't pass vacuously.
- **It bites, twice:**
  - In the suite: a scratch tree with a bare-importing suite fails
    without the real init and loads with it.
  - In `validation.sh`: a scratch copy of the real tree with
    `tests/__init__.py` removed must fail the sweep on
    `No module named 'harness'`, and the restored copy must pass. By
    hand, the mutant reports "56 of 69", one line per suite.
- **Mode.** The file is 0644, like `test_thread_status`, so `apply.sh`
  is the no-op.

## harness.py

- **Rider.** The comment above `CLI_PATH` is now in the past tense and
  keeps its history sentence. It ends "Both suites adopted it at board
  111, and the two copies are gone". I grepped first to confirm no
  `load_bale_module` or ad-hoc `SourceFileLoader` remains.
- **Module docstring.** I also changed it, because it said "both run
  modes" and named only direct execution and discovery. It now names
  the three forms and points at the pin. This is inside the forecast,
  and it is docstring text only.

## Claims

All `observed`:

- The seven fast checks passed in a simulated staging copy: the shipped
  tree plus the `files/` overlay, with the manifest placed as
  `.bale-manifest.json`.
- The two `--slow` checks (full discovery, and every suite dotted in its
  own process) were run with `--slow` on the final bytes in a second
  staging copy: all nine checks PASS, exit 0, every claim `[agree]`.
  Discovery ran 1352 tests OK (48 skipped); the gated run takes about
  eight minutes in total.
- Before that, both whole-tree forms were observed green on the
  near-final tree. The later edits were a failure-message reformat in
  the pin suite and harness comment text.

## Proposals

- **What:** drop the now-redundant `tests/`-on-path guards in
  `test_doc_crossrefs.py` and `test_sanctioned_pairs.py`, and the one in
  `test_craft_response.py`'s `ExchangeBlockParity.setUpClass`.
  - **Why:** the package init does their job in the dotted form, and
    the other two forms never needed them. They're harmless, since each
    inserts only when absent. I left them because all three files are
    outside this forecast, and the brief makes `test_craft_response.py`
    row 37's.
  - **Scope hints:** the craft one rides row 37. The two doc-pin suites
    are 0755, so an `apply.sh` `chmod +x` is needed for each.
- **What:** refresh the run lines in suite docstrings that name only
  discovery or direct execution, if you want the dotted form advertised
  everywhere.
  - **Why:** every suite runs dotted now, but most docstrings still
    offer one form. This is cosmetic, and a sweep across many files.
  - **Scope hints:** many `tests/` files. It is low priority.
