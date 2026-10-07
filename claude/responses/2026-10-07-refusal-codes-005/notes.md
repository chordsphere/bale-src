# notes — 2026-10-07-refusal-codes-005 (bale 0.4.50)

`bin/VERSION` read `0.4.49` before I built anything (the brief's §8 gate). Every
`changes[]` path is inside the write forecast, so there are no departures to
admit. Unlock's bytes don't move: its suite passes unchanged, and validation
compares two of its `--json` refusal lines byte for byte against 0.4.49.

## Decisions to ratify

**The seam.** `fail(msg, code=1, *, reason=None)`. The code rides the exit as
`bale_reason`, beside `bale_cause`, and is `None` when the site passes nothing.
The accessor is `exit_reason(exc, vocabulary, fallback)`. It sits next to
`exit_cause` and takes the verb's vocabulary, so a code that isn't in it falls
back to `unclassified`. That case is logged, never crashes, and never gives a
bare line. I added one more piece the brief didn't name:
`refusal_reason(code, *, override=False)`, a context manager that attaches a
code to a refusal raised inside a call whose `fail()` sites live in another
module. It keys on which call refused, never on text. I use it in four places:

- `bale_config` accessor reads (`config-invalid`) in open and relay.
- `run_pack_argv_gates` in open (`gate-refused`, `override=True`).
- The pack replay in open (`pack-refused`, `override=True`).

`override` exists because the gates and the replay are one refusal site from
open's side, while the helpers inside them now name their own codes. A brief
file's `fail_not_found` says `not-found`, which in open's vocabulary would
misname the refusal as "the bundle is missing". Without `override`, a site's
own code always wins.

**The fallback.** One code, `unclassified`, shared by all three vocabularies
(`REFUSAL_REASON_FALLBACK`). Two things keep it honest:

- A structural pin in `tests/test_refusal_codes.py` walks the AST and requires
  `reason=` on every `fail()`/`_fail()` call in `bale_open.py`, `bale_relay.py`,
  `_cmd_revert`, and the shared helpers revert reaches.
- No known site reaches the fallback.

**Codes I added beyond the brief's lists** (the brief asked me to flag these):

- **open**
  - `sandbox-failed`: `SandboxUnavailableError`, or the prologue failing.
  - `pack-refused`: any `cmd_pack` refusal during the replay, plus its
    interactive threshold abort. That abort returns 1 without a `fail()`, so
    the wrapper prints the line with cause `"exit 1"`.
  - `config-invalid`
  - `no-git`
  - `internal-fault`: the sink-length check.
- **relay**
  - `malformed-block`: BEGIN with no sid, no END, a header with no body, or no
    trailer line.
  - `thread-changed`
  - `unreadable-input`: the stdin or file read hits `OSError`.
  - `no-sid`
  - `not-a-repo`
  - `system-dir`
  - `config-invalid`
  - `no-git`
- **revert**
  - `already-merged`
  - `checkout-refused`
  - `system-dir`
  - `no-git`

The `system-dir` and `no-git` codes are attached once, in `refuse_system_dir`
and `repo_root`. Unlock's context manager ignores them, so its 0.4.47 ruling
(no line for those two) stands.

**Relay site assignment where the brief's names overlap:**

- `not-an-object`: empty input, bare non-JSON, a block whose body isn't JSON,
  and a non-dict record.
- `trailer-mismatch`: both trailer-disagreement sites, including the
  carrier-unescaped one.
- `wrong-session`: the block sentinel, the manifest `session_id`, and the
  record `session_id`.
- `schema`: `validate_exchange_record` and the clarification question-row gate.
- `unreadable-record`: the no-file form's unreadable or non-object latest round,
  and the read-back after preserving. The brief's wording ("cannot be read
  back") fits both.
- `not-found`: the search-miss listing and the not-a-file case.

**Open's `bundle` and `members` at each refusal.**

- Both are null for `not-a-repo`, `not-found`, `not-a-bundle`, `config-invalid`
  (search paths) and `no-git`.
- `bundle` is filled (path, file sha256, stem) from the moment the open is
  about to read the file. That makes every archive or manifest refusal carry it.
- `members` (the published hashes) is filled the moment `bundle.json` passes
  `validate_bundle_manifest`. Undeclared, missing and `member-mismatch` carry
  it; a validator failure doesn't.
- Every later refusal carries both.

The facts are computed under `--json` only, so human mode reads nothing new.

**Key placement.** I appended the new keys at the end of each line:

- open: `reason`, then `cause`, after `desk`.
- relay: `reason`, after `telemetry`.
- revert: `reason`, then `cause`, after `sweep`.

Every earlier key keeps its position. If you'd rather have relay's `reason`
next to its `cause`, it's a two-line move plus the pins.

**Revert's refused line.** `sid` is the sid asked for, or the resolved one once
resolution ran. Every other key is null, `lock_cleared` false, as the brief
says. That includes `log`, even after the sid is known. Revert's stream
discipline now engages first, ahead of the system-directory guard as well as
not-a-repo.

**Open prints only on exit 1.** Argparse's exit 2 on the stored argv prints no
line. Relay keeps 0.4.48's "any non-zero" test, since its argparse errors never
reach the verb.

**`cmd_unlock` is not on the seam.** Moving it would need an opt-out list for
the two guards that must print no line. The change would be churn without a
behavior gain, so I left it (also in `deferred`).

**Help wording.** Each of the three `--json` help strings names its refusal
outcome in quotes, says the line carries "the refusal's reason code (a closed
vocabulary)", and keeps the owner docstring. `test_refusal_codes` pins those
three facts. `test_cli_reference` and `test_cli_help` pass on the regenerated
rendering.

**The sentinel rider.** It turned out `bale_report.py` had no
`EXCHANGE_BLOCK_*` constants, only the `"BALE EXCHANGE "` prefix inside
`_SHAPE_SENTINEL_PREFIXES`. So I declared `EXCHANGE_BLOCK_BEGIN` and
`EXCHANGE_BLOCK_END` there, derived from one `_EXCHANGE_SENTINEL_PREFIX` that
the tuple now uses too, with the tuple's values unchanged. `bale_relay.py`
imports them at module level, and bin/bale's re-export for the crafter parity
suite reads through unchanged. The crafter's own copy is untouched. Its parity
test passes, and a new pin asserts the relay names are the report's objects
(`is`).

## Look closely at

- **`_cmd_open`'s config reads.** `get_validation_base` is still read only when
  a checkpoint member ships, as before. An unconditional read would let a
  malformed `[validation] base` refuse an oracle-less bundle. `get_sandbox_network`
  and `get_sandbox_enabled` are now read in one block, in the same order as
  before.
- **`second-desk`'s `tarball`.** The row and the fact share one `is_file()`.
  The path is `tarball.resolve()`, which matches the `opened` line's pack path.

## Validation

- **Runtime.** About 2m15s on my machine, a little over the 2-minute target.
  `--slow` adds the rehearsal and crafter suites and the whole suite in
  discover form; the whole suite takes about 9.5 minutes here.
- **What the session assertions do.**
  - They drive the staged `bin/bale` in scratch repositories for each code the
    brief lists, plus the three success lines and second-desk's `tarball`
    (both branches), and parse every line.
  - Human-mode bytes are compared for every exercised refusal, against a
    0.4.49 install built from `git show HEAD:` in the staging tree. Each file
    is verified against the request's base sha256, and the check skips if any
    doesn't match.
  - A control asserts that the base install's `revert --json` refusal prints
    nothing, so the comparison can't pass vacuously.
  - Only two success paths are compared with ISO-UTC timestamps normalized:
    the second desk (its opener prints the pack instant) and a real revert.
    The refusals compare exact.
- **Run twice.**
  - On 0.4.50, everything passes, and every claim agrees.
  - On the unmodified 0.4.49 tree, these fail:
    - python and json syntax for the two new files (absent);
    - the `bin/VERSION` cmp;
    - `tests/test_refusal_codes.py` (absent; unittest exits 5);
    - all 20 `--json` session assertions (open and revert print nothing,
      relay's line has no `reason`, the success lines have no `reason` key,
      and second-desk's `tarball` is null);
    - the comparison's control (base against base).
  - On 0.4.49, the older suites pass, since they're 0.4.49's own.
- **Full suite** in discover form on the finished tree: 1966 tests, OK (48 skipped), 9m43s — the 52 new ones among them.

`model_identity` reads `anthropic:claude-opus-5-5`, the model ID this surface
reported for the serving model. The session was configured as
`claude-fable-5-1`, so if those differ in your records, trust the platform's
log over mine.

## Proposals

- **Unlock on the seam.**
  - What: put `cmd_unlock`'s session-shaped refusals on
    `fail(reason=...)` + `exit_reason`, with the verb wrapper skipping the
    `system-dir`/`no-git` codes, and retire `_unlock_refusal`.
  - Why: the four refused lines would share one mechanism.
  - Scope: `bin/bale` only, bytes pinned by `tests/test_unlock_json.py`.
- **A reason code for `bale pack --json` refusals.**
  - What: give pack's refusals a closed vocabulary too.
  - Why: they still print nothing on stdout. twine's courier sees an empty
    stdout for pack while open, relay, revert and unlock now all speak, and the
    open replay's `pack-refused` hides which pack check refused.
  - Scope: `bin/bale_pack.py` sites passing `reason=`, a `PACK_REFUSAL_REASONS`
    in `bale_report`, and open's replay dropping `override=True` so pack's own
    code can show through (or nesting it, say a `pack_reason` key).
- **A test seam for `sandbox-failed`.**
  - What: an environment hook (or `bale_sandbox` monkeypatch point) that makes
    `ensure_verified` raise.
  - Why: the code is reachable only on a host whose namespaces fail; COVERAGE
    names it unreachable today.
- **0.4.48's Proposal 4 still stands.** `bale pack --dry-run --json` reporting
  `rehearsed` is out of scope here, as the brief says. Nothing in this session
  changed its shape.
