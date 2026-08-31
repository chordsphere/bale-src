# notes — 2026-08-31-board-59-relay-extraction-014

## Paths outside the write forecast (admit per path at apply)

- **`bin/bale_relay.py`** — the extraction target itself; a
  worker-determined new file, outside the stamped forecast by
  construction (ADR-0014). The goal names it verbatim.
- **`bin/VERSION`** — `0.4.20` → `0.4.21`. The brief left the bump to
  house practice, and house practice stamps every shipped-file-set
  change (v0.3.12 pack, v0.3.13 apply, v0.3.24 stats, v0.4.13 open).
  The extraction comments in `bin/bale` and `bin/bale_relay.py` say
  "v0.4.21", and the version-tag drift guard requires the constant to
  cover the highest referenced tag — so the stamp and the bump ship
  together or the next release build dies. If you'd rather not bump,
  kick back both this file and the two comment stamps as one unit.

## What the probe established

- The reach-back idiom, verbatim from `bale_rollback.py` and
  `bale_pack.py`: `from __main__ import X  # lazy — see module
  docstring` inside the functions that use it; sibling-owned entry
  points imported lazily from their owning modules (they resolve from
  sys.modules since bin/bale loaded them). `bale_relay.py` follows it
  exactly, including the docstring's public-surface / idiom /
  dependency-direction paragraphs.
- `bin/VERSION` is `0.4.20`.
- Sibling filenames are referenced beyond the packaging lists in
  `BALE.md`, `claude/MASTER.md`, archived notes, and telemetry — all
  outside this session's forecast; see Proposals.

## Decisions to ratify

- **The index header's line numbers were refreshed wholesale**, not
  just shifted for the cut. The shipped listing already carried drift
  well past CODE.md §2.2's ~50-line threshold (section 7 was listed at
  ~1015 and sat at 1269 pre-cut), and the cut moved everything after
  Retry by ~500 lines. Same-file philosophy application (CODE.md §7.1);
  every number now matches the post-extraction actuals.
- **No sibling ordinal in the new module's docstring.** The existing
  docstrings count ordinals ("the fourth sibling", "the eighth"), but I
  could not establish where `bale_sandbox.py` and `bale_open.py` fall
  in that count from the shipped material, so `bale_relay.py` describes
  its provenance (extracted from section 29 in v0.4.21) without
  claiming a number. If you know the ordinal and want it, it's a
  one-line docstring edit.
- **Only `cmd_relay` is bin/bale-facing.** The sentinel constants and
  the pure render/ingest pair stay module-level in `bale_relay.py`
  (one home for the wire shape), but bin/bale imports only `cmd_relay`
  — mirroring how `bale_rollback` exposes a single entry point.

## Claims context

The two claims are `pass (predicted)`, not observed: my build
environment had only the files the request shipped, and the relay /
exchange suites drive `bale relay` through a scratch install that needs
the full sibling set, so they could not run here. What I could run, I
did: the release-packaging suite passed 15/15 against the staged
changes (including the slow E2E build over a synthetic tree), a
stub-hosted smoke test exercised `format_exchange_block` /
`parse_exchange_input` round-trip, tamper-refusal, and the
manifest-normalization and answer-resolvability paths, and a local
drift-guard replica over the release-surface members confirmed the
v0.4.21 equal boundary. `validation.sh` runs the real thing in your
staging: the full fast-lane suite and the real release build.

## Proposals

- **BALE.md relay references.** §8.11 / row §11.34 (and the line-7
  mention of the verb inventory) may still say the relay verb lives in
  `bin/bale` section 29 — BALE.md wasn't shipped, so I couldn't check.
  Worth a doc-touch session once this lands; the design doc is the
  canonical citation target for the moved comments.
- **validate.sh presence rows.** The install-validation presence checks
  stop at `_bale_toml.py` — `bale_open.py`, `bale_sandbox.py` (queued
  since the board-49b notes), and now `bale_relay.py` have no rows.
  build.sh's comment calls the hand-maintained rows deliberately
  deferred (drift yields a missing check, never a broken install), so
  this stays a proposal, not a change: one small session adds all
  three rows.
- **`claude/MASTER.md` mentions** of sibling registration are
  sitting-close-deltas' forecast; nothing to do here beyond noting the
  new module exists when that session runs.

---

# Round 2 — retry after the HOLD (this tarball corrects the held response)

## Root cause of the 17 errors

All 17 were one bug, mine: `tests/test_craft_response.py`'s
`ExchangeBlockParity` loads `bin/bale` as an ordinary module and reads
the section-29 wire symbols off it, byte-comparing the crafter's
re-declared emission against the consumer's. The extraction took those
attributes off `bin/bale`'s module surface, and — the second half —
even a re-export would have died in-process, because my
`parse_exchange_input` did `from __main__ import fail` at entry, and
under the suite `__main__` is the unittest runner. Pre-extraction both
worked because everything was one module.

## The fix (two edits, both inside already-shipped files)

- `bin/bale`: the `bale_relay` import block now re-exports the wire
  surface (sentinels, trailer regex, sides, `_exchange_body_bytes`,
  `format_exchange_block`, `parse_exchange_input`,
  `_normalize_manifest_to_record`), each `# noqa: F401` with a comment
  naming the parity suite as the consumer. Deliberately *not*
  re-exported: the thread/verb machinery (`read_exchange_thread`,
  `unresolved_answers`, `cmd_relay` beyond dispatch) — the suite's
  errors named exactly the wire set, and the narrower surface keeps the
  module boundary honest.
- `bin/bale_relay.py`: `parse_exchange_input` refuses through a new
  module-level `_fail` that prefers `__main__.fail` when bale hosts it
  and otherwise mirrors fail()'s visible shape (`[bale] error:` line on
  stderr, exit 1). **Ratify the duplication**: two lines of fail()'s
  shape now live in the sibling. The alternative (suite loads
  `bale_relay` directly) means editing `test_craft_response.py` — an
  unshipped, out-of-forecast file — and the brief pinned the suite as
  the guard that "must stay green across the move", which reads as:
  don't move the guard.

## What else changed

- `validation.sh`: the unittest step's `tail -5` (which swallowed the
  HOLD's tracebacks — that capture bug was mine) now logs the full run
  to `.validation-logs/unittest.log` and surfaces the failure blocks
  bounded on FAIL; and a new `parity surface` check replicates the
  suite's own mechanism — loads `bin/bale` by file path under a
  non-`__main__` name, getattrs all ten symbols, round-trips
  render/ingest, and exercises a refusal.
- The 2 sandbox findings in the hold-probe output
  (`test_sandbox_wrapper.PrologueUnitTest`) were artifacts of the
  probe's `TMPDIR` override, not of the tree: the real validation run
  had `failures=0` and exactly the 17 parity errors.

## Verified locally this round

Standalone `bale_relay` (unittest-runner `__main__`, no `fail`
attribute): happy-path round trip, tamper refusal with the right stderr
shape and exit 1; hosted preference confirmed (`__main__.fail` wins
when present). The release-packaging suite re-run green against the
updated mirror.

## Apply note

Admission is per-invocation: the retry needs the same two
`--allow-out-of-scope` flags (`bin/bale_relay.py`, `bin/VERSION`)
again.
