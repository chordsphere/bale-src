# Notes — 2026-10-07-open-relay-json-003 (bale 0.4.48), retry

This is the re-attempt after the HOLD. The one failed probe was "open
--json on a still-open bundle: outcome second-desk, desk named": the
second-desk line printed `log` where §2.2 requires null. Decision 2
below says what changed. Nothing else in the response changed.

`bin/VERSION` read `0.4.47` on arrival, as §8 of the brief required, so I
built. No probe, no clarification, no light block. Every path I changed is
inside the write forecast; there are no forecast departures.

## What landed, in one breath

- `bale pack --json` gains `opener` as the last key: `opener_paste_text` of
  the same block the run prints on stderr. `PACK_REPORT_KEYS` in
  `bin/bale_report.py` declares the key order once, so open can fold the
  keys in without keeping a second copy of the list.
- `bale open --json` runs `enable_json_mode()` before anything else, then
  prints one `format_open_json` line on each path that exits 0: `opened`,
  `second-desk`, `rehearsed`. Refusals still go through `fail()` and print
  nothing on stdout.
- `bale relay --json` prints one `format_relay_json` line on every path:
  `relayed`, `re-emitted`, `relay-refused`. The block rides inside it.
  A thin wrapper (`cmd_relay` → `_cmd_relay`) catches the `SystemExit` that
  each `fail()` raises and prints the refused line next to the unchanged
  `[bale] error:`. That way none of the twelve refusal sites had to change.
- Human mode is byte-identical for all three verbs. `validation.sh` checks
  this directly: it extracts the base install from `git HEAD`, runs the
  same human scenarios against both installs, normalizes timestamps, hex
  digests, the temp root and the version string, and runs `diff -r`.

## Decisions to ratify

1. **How the pack line folds into open's.** I added a new in-process
   namespace attribute, `json_report_sink` (a list), next to `open_bundle`
   and `pre_answered`. No CLI flag can set it. When it is set, `cmd_pack`
   renders its line exactly as `--json` would and appends it to the sink
   instead of calling `emit_json_line`. `cmd_open` then parses that line and
   folds every key except `outcome` into its own line, verbatim. I did not
   set `pack_args.json = True`, because `args.json` also gates
   `cmd_pack_dry_run` and `cmd_pack_context`. Keying only on the sink also
   means a stored argv that happens to carry `--json` behaves the same under
   `open --json`.
   One consequence: under `open --json` the pack's human summary rows are
   not printed on stderr, exactly as under `pack --json`. The scissor block
   and every `[bale]` line still go to stderr. If the pack returns 0 but the
   sink does not hold exactly one line, open refuses as an internal fault.
   That cannot happen today; I chose a refusal over a silent empty line.
2. **`log` on a second desk is `null` (retry; this corrects the held
   attempt).** The first attempt reported the session log's absolute path
   there. That departed from §2.2, which says every pack-report key except
   `sid` and `opener` is null on `second-desk`. My reasoning was that §10
   listed "what `log` is on each path" as mine to decide, and that the
   desk path does journal to `.bale/logs/<sid>.log`. The blind
   checkpoint held on it, and your ruling is that the outcome contract
   wins. On reflection the contract reads better too: on this line the
   pack keys report a pack's facts, and no pack ran on a second desk.
   `log` is now null on that path only. `opened` still carries the
   replayed pack's own `log`, verbatim, and `rehearsed` stays all-null.
   The fix is in `format_open_json` (its `log_path` parameter is gone, so
   the line can't carry a value there) and in `open_second_desk`, which no
   longer reports a log. `test_second_desk_json` now pins every pack key
   except `sid` and `opener` to null, `log` named explicitly. A new
   renderer test pins the same nulls in process, and `validation.sh` has a
   matching driver assertion. Both end-to-end pins fail against the held
   attempt's tree and pass here. If a consumer wants the desk's log later,
   a separate additive key is the way to add it, and Proposal 3 covers
   `tarball` the same way.
3. **The second desk's `desk` value** is `next_desk_name(record)`, the same
   `desk-N` the attempt records and the human summary prints. A rehearsal of
   a second-desk bundle reports `rehearsed` with `desk` and `sid` null,
   because nothing is recorded and `desk` means "the desk recorded". The
   prediction ("would record desk-2") stays in the stderr report.
4. **`kind` on re-emit stays `null`, as written.** The key means "what was
   ingested", and a re-emit ingests nothing. `from` and `round` already say
   which record it is. If twine wants the recorded kind, I'd suggest a new
   key rather than overloading this one.
5. **Help wording.** Both flags' help strings follow unlock's pattern: they
   state the stream discipline and the outcome words and name the owner
   docstring. The new `BALE_HELP.md` sections render from the parser
   (`test_cli_reference` / `test_cli_help` pass).
6. **The pack/open rehearsal asymmetry (brief §3).** `bale pack --dry-run
   --json` still refuses: a pack rehearsal has no sid or session to report.
   `bale open --check/--dry-run --json` reports `rehearsed`, because an open
   rehearsal does have facts to report: the bundle it verified, the member
   hashes, and the dry-run verdict. I kept the contract as written and
   stated the asymmetry once, in BALE.md §6.7.
7. **`sid` on relay lines is `args.sid` as given**, on every outcome,
   including refusals before the sid is stripped.
8. **`bundle.sha256` is the hash of the file's bytes**, re-read once after
   `read_bundle` accepted it, and only under `--json`. It differs on purpose
   from `members`, which holds the LF-normalized member hashes the manifest
   publishes. If the re-read fails, the line still prints with
   `"unreadable"` and a FORCE log line, following `bundle_identity`'s
   fallback.
9. **Missing input file and empty-thread refusals** also print
   `relay-refused`, with `telemetry: null`: they record nothing today.
   argparse usage errors (exit 2) never reach the verb and print no line;
   a test pins that.
10. **bale-internals.md.** The brief mentions "the `bale_open` /
    `bale_relay` entries", but the file has none. I added one sentence for
    each verb in cluster 16's flag-wiring paragraph, and the formatter list
    in the `bale_report` paragraph now includes them.
11. **One existing pin moved.** `test_pack_telemetry_104b`'s
    `test_pack_json_existing_keys_unchanged` asserted `list(payload)[13:] ==
    ["sweep", "include_group"]`, which an additive trailing key necessarily
    breaks. It now asserts `[13:15]` for those two and `[15:] ==
    ["opener"]`. Every earlier key and position is still pinned.
12. **BALE.md wording changes beyond the brief's list.** §5.4's "landed per
    command" list and its refused-outcome sentence now name open/relay and
    `relay-refused`. The relay table row and module docstring say
    "positional surface is exactly `<sid> [<file|->]`" where they said
    "option surface", because a flag now exists. I did not touch §8.11's
    stream-discipline sentences, as the brief directed. Its step 5 ("emits
    the block to stdout") is still true in human mode, and §5.8 now covers
    `--json`.

## Places to look closely

- `bin/bale_relay.py` `cmd_relay`: the wrapper only prints the refused line
  when `code not in (None, 0)`, and it always re-raises, so the exit code
  is unchanged. `report["log"]` is filled right after `set_log_file`, so a
  "not open" refusal reports `log: null` and a held-branch refusal reports
  the path.
- `bin/bale_open.py`: `emit_open_line` is a no-op outside `--json`. On a
  real open with `--json`, the emit is the last thing before `return 0`,
  after the pack's own clipboard copy.

## Validation, run twice

On a simulated target-base staging (base committed as HEAD, `files/`
overlaid, `apply.sh` run, `.bale-manifest.json` placed), every check passed
and every claim agrees. The full discover is gated behind `--slow`. I ran
it separately on the edited tree: 1906 tests, OK (48 skipped), about 9 minutes.
The two "normalized" checks would read as `[SKIP]` with a reason on a
staging without the 0.4.47 HEAD.

On the unmodified base, these failed by name: `python syntax (changed
modules)` (the new suite file is absent), `json syntax
(claude/changelog/0.4.48.json)`, `bin/VERSION reads 0.4.48 (cmp)`,
`tests: test_open_relay_json`, `session: --json outcome assertions (open,
relay, pack opener)` (every one of the 12 sub-assertions that ran failed; the opened path's six detail checks do not run when no line parses), and `session: relay
--json block equals human-mode stdout (cmp)`. These passed on both runs by
construction, because they are invariants rather than tests of the change:
`bin/bale is executable`, the eight pre-existing suites, `validate.sh`, and
the human-identity diff (base against itself). Within the new suite,
20 of 23 tests fail on the base. The 3 that pass are the human-mode and
argparse invariants.

For the retry I also ran a third time, against the held attempt's tree
(base plus the first `files/`). Exactly one check failed there:
`test_second_desk_json` in the suite, and the driver's new `open --json
second-desk: every pack key but sid and opener null (log included)`
assertion. It printed the offending `log` value. Everything else passed,
so the retry changes only what the HOLD named.

In my sandbox, git refused the simulated repos as "dubious ownership"
because the file owner differed from root. I ran the simulation with
`safe.directory=*` set through `GIT_CONFIG_*` environment variables. This
cannot happen on your machine, but on a host where it does, the HEAD check
reads "no HEAD" and SKIPs rather than failing.

## Not carried (the registry riders, brief §6)

Two riders whose ride condition this forecast satisfies were declined at
this holder and stay on the registry:

- the FORCE-queue accessors for `bin/bale` section 2 and
  `bin/bale_pack.py`'s two `__main__` reach-ins (log-hold's fourth
  Proposal);
- the cap/breach loop extraction in `bin/bale_pack.py` (104a's Proposal 2,
  droppable).

## Proposals

1. **Reason-coded refusal lines for `bale open --json`.** This is the
   unlock 0.4.47 shape: an `open-refused` outcome with a closed `reason`
   vocabulary, printed beside the unchanged stderr error. The gates already
   give natural codes: `not-a-repo`, `not-found`, `not-a-bundle` (suffix),
   `manifest-invalid`, `member-mismatch`, `no-validation-base`,
   `gate-refused` (any `run_pack_argv_gates` refusal, carrying the gate's
   cause), `defective-oracle`, `desk-refused`. **Why:** twine's courier
   currently has to tell "refused" from "crashed" by exit code and stderr
   text. `relay --json` now gives it a line on refusal; open is the
   remaining gap. **Scope:** the refusal sites are spread across
   `cmd_open`, `read_bundle` and the pack gates, so a wrapper like relay's
   (catch the `SystemExit`, map the cause) is cheaper than per-site codes.
   Mapping causes to codes by text would be brittle, though. A `fail()`
   keyword that attaches a code to the `SystemExit` is the cleaner seam.
2. **Refusal codes for `relay --json` beyond `cause`.** These would be
   `not-open`, `held-branch`, `not-found`, `trailer-mismatch`,
   `wrong-session`, `schema`, `stale-round`, `skipped-round`,
   `planner-round-one`, `unresolved-answer`, `no-rounds`. **Why:** `cause`
   is stderr wording and the docstring says not to dispatch on it. A
   courier that wants to re-request a truncated block automatically needs
   `trailer-mismatch` as data. **Scope:** `bin/bale_relay.py` plus a
   vocabulary tuple next to `RELAY_OUTCOMES`. This is additive.
3. **`tarball` on `second-desk` lines.** The second desk's human summary
   already names the outbox tarball, which twine row 3 needs ("the request
   tarball path and opener"). The JSON line nulls it, per the brief. Making
   it non-null is additive and only touches `open_second_desk`'s facts dict.
4. **`bale pack --dry-run --json`.** If the asymmetry in Decision 6 grates,
   a `rehearsed` line for pack (null pack keys plus the gate facts) would
   close it. The renderer pattern here already handles a mostly-null line.
   Low priority.
