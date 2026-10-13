# notes — 2026-10-13-cost-mirror-005

The flag landed on all three verbs through one reader
(`bale_report.read_cost_file`) and one front door (`load_cost_file` in
`bin/bale`, which resolves the path like apply's tarball argument and
turns `CostFileError` into `fail()`). Each verb calls it before its first
state change. The block is six keys everywhere, and the schema pins it
with `additionalProperties: false`. Stats, status and the dossier are
untouched.

## Paths outside the write forecast (admit at apply)

All four are under `tests/`, and the brief predicted each one:

- `tests/test_cost_file_flag.py` (new): the suite the brief asks for. It
  has 35 cases: the reader in process, unlock end to end, apply and retry
  through the staging pipeline, and the help pages.
- `tests/test_telemetry_extensions.py`: `CostBlockTest` pinned the
  four-key all-null block and the schema's four properties. It now pins
  six keys and adds two cases: four-key records still validate, and an
  unknown cost key rejects.
- `tests/test_unlock_json.py`: it pins `UNLOCK_REFUSAL_REASONS` by its
  own spelling and wants one CLI case per code. It gains `cost-file` and
  `test_cost_file_refusal_line`.
- `tests/test_refusal_codes.py`: `test_unlock_vocabulary_unmoved` pins
  the same tuple by value.

## Decisions to ratify

1. **Exits that write no attempt.** A clarification, `apply --dry-run`
   and the no-op `bale unlock` (no open session) write no attempt today,
   so the cost has nowhere to land. In each case bale still validates the
   file (a bad file refuses) and logs `cost file …: valid, not stamped —
   <why>`. I picked that over refusing, because refusing a clarification
   would block the round from being ingested, and over a silent drop. The
   brief lists clarification among apply's closing exits, but
   `apply_pipeline` has never written an attempt for one. So **the spend
   of a clarification round is currently lost** unless the harness folds
   it into the next run's file. That would break "per run" semantics, so
   I'd rather not tell twine to do it. See the Proposal below.
2. **Rejected attempts carry the cost.** The brief names "the gate
   refusals". I also stamp `rejected` (bad tarball, pre-flight failure),
   because the worker run behind it really spent that money and the
   rejected attempt is the one attempt that invocation writes. The rule
   is simple: whatever attempt this invocation writes carries the file.
   Walkthrough `reverted` (operator declines after PASS) follows the same
   rule.
3. **`unlock --integration --cost-file` refuses.** This is the twin of
   the `--reason` contradiction. Under `--json` the existing
   `integration-json` check fires first, so the new check only matters in
   human mode.
4. **The builder overlays.** `build_telemetry_attempt(cost=…)` now stamps
   `{**empty_cost_block(), **cost}`, so even a four-key caller produces
   six keys. The old "recorded verbatim" test changed to match.
5. **Stricter than the brief, both directions.** The schema gained
   `minimum: 0` on the counts and `usd`, plus `minLength: 1` on `models`
   items, so the record-side validator agrees with the reader. The reader
   also refuses NaN/Infinity, repeated keys and non-UTF-8 bytes, and
   tolerates a UTF-8 BOM. `model_tier` accepts any string, and `models`
   is recorded as handed (no sorted/unique enforcement). That is ruling 4
   read literally; sorting is the harness's arithmetic per ruling 2.
6. **Where apply validates.** The check sits after the
   `--show-validator`/`--show-apply-script` branch (inspection writes
   nothing, so it ignores the flag) and before the bare-form y/N, the
   session resolution, and the rejected-attempt wrapper. That placement
   is what keeps a bad file from appending a `rejected` attempt.
7. **Executable bit.** `apply.sh` re-asserts `chmod +x bin/bale` (the
   crafter's `--executable`), and `validation.sh` checks it. I wasn't
   sure whether bale's overlay keeps an existing file's mode on a
   `modified` entry, so it's belt and braces.

## What I checked

- Baseline, untouched tree: 2037 tests, OK, 48 skipped.
- Changed tree: 2075 tests (= 2037 + 35 new suite + 2 in
  `test_telemetry_extensions` + 1 in `test_unlock_json`), 48 skipped.
  One failure on my first full run,
  `test_clipboard_paste_blocks…test_global_key_copies_the_sentinel_block`,
  was my own fault: an ad-hoc `python3 -c "import bale_validate"` run
  inside `bin/` without `-B` had left `bin/__pycache__`, and the harness
  copied it into a scratch install. After deleting it, that suite passes
  36/36. The staged rehearsal of `validation.sh` (below) runs the whole
  suite again from a clean tree.
- A staged rehearsal: a copy of the base with `files/` overlaid,
  `apply.sh` run, and the manifest placed as `.bale-manifest.json`. It
  passed every check, the suite at 2075 tests, OK, 48 skipped (610 s).
  Every claim agrees, and no `__pycache__` was left behind.
- On the unmodified tree, the change-testing assertions (schema shape,
  changelog record, VERSION, help text) fail as they should. Two pass on
  both trees by design, because they guard invariants: changelog records
  0.4.35–0.4.53 byte-identical, and no `docs/` path in `changes[]`.
- The new suite fails on the unmodified tree (21 failures, 35 errors) and
  passes on the changed one.
- `validate.sh`: 94 checks, OK. The self-containment guard passes, and
  the schema text cites versions only.

## validation.sh

The whole suite takes about 10 minutes here, which is over TARBALL.md
§7.6's two-minute target. The brief explicitly asks for the suite in
`validation.sh`, so I followed the brief and didn't gate it behind
`--slow`. The `validation_will_run` entry says "~10 min". If you'd rather
have the gate, it's one `case "$1"` away. The docs/ assertion reads the
manifest's `changes[]`, never staged doc bytes. The changelog assertion
compares each existing record's sha256 against the request's pinned
`base_files`. The script never walks the tree, so it never reads
`claude/checkpoints/`.

## One-apply-behind

The apply that lands this runs 0.4.53's apply code, so the landing apply
itself takes no `--cost-file`. That's expected.

## Proposals

- **What:** give a clarification round's spend a home. One option is a
  bale-written `cost` sidecar on the preserved clarification record,
  beside `preserved_at`, summed by the closing attempt's `clarification`
  stamp. Another is a dedicated non-closing attempt outcome.
  **Why:** today a harness-hosted run that ends in a clarification spends
  money that no record can carry. This session logs it as "valid, not
  stamped" so the gap is at least visible. **Scope hints:**
  `bin/bale_apply.py` (`_apply_clarification`),
  `preserve_clarification_record`, `schemas/exchange-record.schema.json`
  or the telemetry outcome enum, and `bale relay`'s ingest path for
  later rounds. Decide this before the `bale stats` read side lands, so
  the aggregate never averages over a numerator with holes.
- **What:** tell twine the field definitions verbatim. The schema's cost
  description now carries them, and `bale contract --json` is the
  natural read, but contract doesn't publish the cost keys yet.
  **Why:** twine's per-session total object (`cost_usd`, `tokens` as
  five classes, `models`) needs a per-run projection: `tokens_in = input
  + cache_read + cache_write`, `tokens_out = output + thinking`, and
  `calls`/`models` from that run's records only. A per-session total
  handed on each attempt would double-count across held → retry.
  **Scope hints:** `bin/bale_report.py` `CONTRACT_VOCABULARIES` could
  publish `COST_KEYS`; the twine side is a doc line.
- **What:** a `docs/` line, for the sibling that owns the global docs.
  `AGENT.md` §11.7's `twine run` row says the exact model string
  "reaches bale's record only mechanically, through `attempts[].cost`".
  That is now true via `cost.models`, and the row could name the field.
  **Why:** it closes the loop the row opened. **Scope hints:**
  `docs/AGENT.md` §11.7 only; out of scope here by the request.
