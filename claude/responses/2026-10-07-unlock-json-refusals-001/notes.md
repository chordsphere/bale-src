# Notes — 2026-10-07-unlock-json-refusals-001

The one line twine wanted is there: `bale unlock <sid> --reason aborted
--json` on a HOLD session now exits 1 with the same stderr as 0.4.46 and
prints

```
{"outcome": "unlock-refused", "sid": "<sid>", "log": null, "closure_reason": null, "session_dir_wiped": null, "branch_preserved": false, "telemetry": null, "debris": null, "sweep": null, "reason": "hold-branch", "message": "branch bale/<sid> exists — this session reached HOLD. Use `bale revert <sid>` …", "open_sessions": ["<sid>", …]}
```

on stdout (the em dash goes out as `—`, `json.dumps`' default, like
every other line). `bin/VERSION` read 0.4.46 before I built, as §8 asked;
the context tree's bytes match the request's `base_files` hashes.

## Decisions to ratify

1. **Where `--json` engages (§2.3).** `enable_json_mode()` is now the
   first statement of `cmd_unlock`, ahead of `refuse_system_dir` and
   `repo_root`. Nothing printed to stdout before the old call site, so no
   success path changes; it just puts the not-a-repo and `--integration`
   refusals under the same stream discipline as the rest.
2. **How the line is produced.** A verb-local context manager,
   `_unlock_refusal(args, reason, sid=, repo=)`, wraps each refusing
   block. `fail()` runs exactly as for every other verb (stderr line,
   session-log journal, `SystemExit` with `bale_cause`). Then, only under
   `--json`, the line is emitted with `message = exit_cause(exc)`, which is
   `failure_cause` of the fail text, and the *same* exception is
   re-raised. `resolve_open_session` and `fail()` are untouched, so the
   shared helpers stay unaware of unlock's vocabulary. The code is
   chosen by which check refused, never parsed from the message.
3. **`several-open` vs `not-open` from the resolver.** These are keyed on
   the input: an explicit sid can only be refused as not open. With no
   sid, the resolver's zero-open arm can't be reached from unlock
   because the no-op pre-check takes it, so the only refusal left is
   several open. If a concurrent close ever hit that arm between the two
   registry reads, the line would say `several-open` with the real
   `open_sessions` beside it. I judged that race not worth a sixth code.
4. **`sid` on `not-a-repo`.** The brief lists `not-a-repo` among the
   null-sid codes, but it also defines `sid` as "the one asked for". I
   read "(… without a sid)" as covering both: `bale unlock X --json`
   outside a repo echoes `"sid": "X"`, and a bare `bale unlock --json`
   gives null. `integration-json` follows the same rule: with a sid
   (`--integration X --json`) the sid is echoed. If you want
   `not-a-repo` always null, it's a one-argument change at the call
   site.
5. **`open_sessions` on `unlocked`/`no-op` stays null.** The manifest's
   constraint pins this. On a refusal it's the registry read at refusal
   time (`open_sessions()`, sorted, oldest first). It's `[]` when nothing
   is open and null for `not-a-repo`. A registry read that raises
   `OSError` while the refusal's exit is in flight is logged and gives
   null rather than replacing the exit.
6. **`refuse_system_dir` stays a bare refusal.** This follows your ruling,
   with no line. I put `repo_root`'s "git not found on PATH" `fail()` in
   the same bucket: it's environmental, not session-shaped, and has no
   code. The docstring says both explicitly.
7. **Renderer guard rails.** The outcome word `"unlock-refused"` is
   spelled once, in `bin/bale_report.py` (`UNLOCK_REFUSED_OUTCOME`,
   used by the new `format_unlock_refusal_json`). `format_unlock_json`
   raises `ValueError` for a reason outside `UNLOCK_REFUSAL_REASONS`, or
   for any of the three keys on another outcome. That's the same posture
   as `format_pack_sweep_entry`.
8. **Key position.** The three keys are appended after `sweep`, so the
   `unlocked` and `no-op` lines are their 0.4.46 bytes plus three trailing
   nulls (pinned in `test_earlier_keys_render_unchanged`).
9. **Help wording.** The `--json` help now reads "…and on a
   session-shaped refusal as outcome 'unlock-refused' with a reason
   code, still exiting 1 with the error on stderr; the key contract and
   the reason codes are owned by format_unlock_json's docstring in
   bin/bale_report.py." The `BALE_HELP.md` in this request is 0.4.46's,
   and the next request carries this text.
10. **BALE.md §5.4 got a second touch.** Its `--json` bullet said refusal
    paths print "nothing on stdout", which was already untrue of apply's
    `*-refused` outcomes. It now names that exception and unlock's.
    §9.3 got its one sentence.
11. **bale-internals.md.** The `cmd_unlock` entry got its one sentence.
    The `bale_report` paragraph lists pack/apply/status keys only, not
    unlock's, so per "if it does" I left it alone.
12. **No telemetry for refusals, and no proposal for it either.** twine
    now gets the code on stdout. A `relay-refused`-style attempt record
    would add an unlock attempt that isn't a closure to a record whose
    unlock entries are all closures, and `bale stats` would need to learn
    to skip it. I don't see a consumer asking.

## One thing the brief states that the tree doesn't do

§2.2 says "without `--json`, no refusal prints anything on stdout". The
HOLD refusal does, and did in 0.4.46: `log(f"unlock: {sid}")` runs once
the sid resolves, and in human mode `[bale] ` log lines go to stdout. So
a human-mode HOLD refusal prints `[bale] unlock: <sid>` on stdout and the
error on stderr. That's byte-identical to 0.4.46 and pinned as such
(`test_human_mode_refusals_print_no_json`, and the human-mode validation
group compares those stdout bytes too). Under `--json` that log line goes
to stderr, so twine's stdout is the JSON line alone.

## The test rewrite (deliberate, not a deletion)

`tests/test_unlock_json.py`'s two 0.4.45 pins asserted an empty stdout on
refusal. They are rewritten, and renamed because their old names now say
the opposite:

- `test_refusal_emits_nothing_on_stdout` → `test_several_open_refusal_line`
- `test_integration_json_refused` → `test_integration_json_refusal_line`
  (now also covers `--integration <sid> --json` and
  `--integration --reason … --json`)

New cases:
- one per remaining code (`hold-branch`, `not-open`, `not-a-repo`);
- `--force` still unlocking;
- human-mode refusals;
- argparse exit 2;
- the three keys null on `unlocked`/`no-op`;
- the help text;
- a coverage pin that every vocabulary code has its case;
- an in-process `UnlockRefusalVocabularyTest`.

The `not-a-repo` case sets `GIT_CEILING_DIRECTORIES` to the test's temp
root so git can't walk out of the sandbox (ADR-0005). 23 tests, green.

## Validation, run twice

There are no required check names to include: `bale.toml`'s
`[validation]` carries only `base`. I ran `validation.sh` in a simulated
staging (base copy, `files/` overlay, `apply.sh`, the manifest at
`.bale-manifest.json`), then on the unmodified base:

- **Staged:** exit 0, every check `[PASS]` and every claim `[agree]`. The
  full suite is `[SKIP]`, gated behind `--slow`.
- **Base:** exit 1. These fail by name:
  - `file syntax …` (the changelog record doesn't exist yet);
  - `session: unlock-refused line for each reason code (parsed JSON)`;
  - `session: unlocked and no-op lines carry reason/message/open_sessions as null`;
  - `session: claude/changelog/0.4.47.json validates`;
  - `session: bin/VERSION bytes are 0.4.47 (cmp)`.
- **Pass on both, by design:**
  - `session: human-mode refusals byte-identical to 0.4.46 (stdout, stderr)`
    and `session: argparse exit 2 with empty stdout; refusal writes no
    telemetry; --force unlocks` are the brief's preservation pins.
    Passing on the base is what "unchanged" means, so they guard the
    change rather than test it.
  - The four `unit suite:` checks run whichever tree's tests are present.

The human-mode expected bytes in the script are the 0.4.46 stderr I
captured from the request tree's own `bin/bale`. They are compared
file-to-file, never through `$(...)`.

Write locations are announced at the top: the `.validation-logs/` dir,
a `mktemp -d` scratch under `$TMPDIR` (removed on exit), and the suites'
own tempfile dirs. `PYTHONDONTWRITEBYTECODE=1` is exported, so the
crafted epilogue's `python3 -` heredoc writes no `__pycache__`; that was
the brief's §7 caveat. After both runs I diffed the trees: nothing but
the logs dir appeared.

The whole suite in discover form (`python3 -B -m unittest discover -s tests`, `BALE_TEST_SLOW` unset) ran on the modified tree before shipping: 1881 tests, OK (48 skipped), about 12 minutes here, which is why `validation.sh` gates it behind `--slow`. Its claim is `pass`, observed, and reads `[n/a]` unless you pass the flag. On the unmodified request tree the same command ran 1866 tests, OK (48 skipped); the difference of 15 is this session's net new cases. None of the baseline failures earlier arcs reported recurred: no suite wanted `bale.toml`, `claude/changelog/`, ADR-0013 or `README.md`.

`model_identity` is `anthropic:claude-opus-5-5`, the identifier this
session is configured with. The serving model isn't independently
visible to me.

## Proposals

- **What:** twine's desk moves its consumption pin to 0.4.47 and keys
  `twine kill`'s hand line on `reason == "hold-branch"` instead of the
  stderr prefix.
  **Why:** the `[[wanted]]` entry's status says twine reads the stderr
  text "until the pin carries the code". The code exists now, and
  `message` is documented as for reading, not dispatch.
  **Scope hints:** twine-src's `share/bale-consumption.toml` (third
  `[[wanted]]`) and the kill-switch's refusal branch. Only after this
  applies.

- **What:** `bale revert --json` gets the same treatment, a
  `revert-refused` line with its own closed codes.
  **Why:** the hold-branch remedy twine reaches for is `bale revert
  <sid>`. Its refusals (dirty tree, metadata gate, already merged)
  still exit through bare `fail()` under `--json`, so the next link in
  the same chain is still keyed on stderr wording.
  **Scope hints:** `cmd_revert` in `bin/bale` and `format_revert_json`
  in `bin/bale_report.py`. The `_unlock_refusal` shape would carry over
  as a shared helper if a second verb adopts it. It shares
  `bin/bale_report.py` with the queued `open-relay-json` and
  `inline-sentinels-and-crafter-b` sessions, so it serializes behind
  them.
