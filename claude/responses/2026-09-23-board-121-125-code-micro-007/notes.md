# Notes — 2026-09-23-board-121-125-code-micro-007 (bale 0.4.44)

All four rows and the three riders landed. Every changed path is inside the
write forecast, so there are no forecast departures and no admissions to
make at apply. `bin/VERSION` is 0.4.44 and `claude/changelog/0.4.44.json`
ships beside it. The brief's line numbers had drifted a little (for example,
`_resolve_supersession`'s call is at :5224 and the blindness call at :5301);
the phrases all matched.

Test counts: the full suite ran 1544 tests (1507 baseline + 37 new). On
the first full run there was one failure, which my own new log line caused
(the wording collision under "Other things to know"). It is fixed, and the
rerun result is recorded at the end of these notes.

## Row 121: argv-only gates before the supersession exchange

**Where it lives (row 122 should read this):** a new pre-exchange pass,
`bale_pack.pack_pre_exchange_gates`, called in `cmd_pack` immediately before
`_resolve_supersession`. Because the read-only sweep runs later still, the
pass precedes both state-writing exchanges. `pack_argv_preflight` is
byte-for-byte unchanged. `bale open` replays through `cmd_pack`, so the open
path gets the same protection without touching the preflight.

**Deviation, flagged: more gates moved than the brief named.** The brief
named two gates (the read-side include-naming half of the blindness gate,
and the missing-path refusal). Reading the code, these can also refuse on
argv alone and also used to fire after the close:

- slug shape and empty goal, when typed;
- planner-bundle naming;
- the `--max-files`, `--max-size` and `--max-depth` values.

All of them now run first. Their original sites stay, because the wizard can
fill slug, goal and `--write` later and those sites are cheap. The
bundle-naming refusal text is now one helper, so the two sites cannot
drift apart.

**Deviation, flagged: the whole blindness gate moved on the non-deferred
path, not only its read half.** When the forecast is final at parse, the
forecast half is argv-decidable too. Moving the whole call keeps one call
site and one admission stamp. It still runs ahead of the disjointness gate,
as its docstring requires.

On the wizard (deferred) path, only the read half runs early, and only
without `--allow-checkpoint-in-scope`, because an admitted read half refuses
nothing. The full gate stays post-wizard.

**Left where the exchange leaves them, as the brief asked:**

- the disjointness gate, which must see the post-close registry;
- the declined-supersession refusal, which is a verdict on the exchange;
- the read-only sweep.

**The desk's fixture is reproduced exactly** in
`test_open_verb.OpenVerbTest.test_include_naming_checkpoint_refuses_before_supersession`.
On the 0.4.43 code it shows the specimen: the parent closes
superseded-by-split, then the refusal fires. On this code the open refuses
and the parent's record is still the lone `opened` attempt.

## Row 123: a desk suffix on a second open of one sid

**What happens now.** `bale open` checks the verified bundle's identity
against the `bundle` stamp on every open session's `opened` attempts. The
check runs after the bundle verifies and before the pre-flight, dry-run,
sweep and replay. On a match it:

- appends an `opened` attempt to that session's record, carrying the same
  bundle stamp, the provenance stamp re-read from the session's stamped
  manifest, and `desk: "desk-N"`;
- journals the event to the session log;
- prints a summary whose opener names the chat `<sid>@desk-N`;
- exits 0 with one session open.

A closed session is not in the registry, so its bundle opens a new session
exactly as before.

**Choices you should ratify:**

- **Desk value scheme.** The value is `desk-N`, where N counts the record's
  `opened` attempts including the new one. The first open carries no key and
  reads as desk-1. The qualified name uses `@` because `@` cannot occur in a
  sid, so the name can never be pasted as one.
- **`command: "open"` (deviation: an additive enum value the brief didn't
  name).** No pack runs on the desk path, so stamping `pack` would break the
  schema's honest-command posture. I added `open` to the enum and described
  it. `record_version` is unchanged.
- **Identity match ignores the stem.** The match uses the manifest, brief
  and checkpoint hashes only. A renamed copy such as `plan (1).bale-bundle`
  is the same bundle; its stem still rides the desk attempt's stamp. An
  `unreadable` manifest hash never matches, so recognition happens only on a
  real hash, never a guess.
- **Deviation: refusal after an apply-side event.** Once the record holds
  any non-`opened` event, a further desk refuses and names that event
  (e.g. `latest: held`). The schema defines `opened` as "no close or apply
  event has landed yet", so appending one after a HOLD would contradict the
  record. The specimen (a read-only planner session) never hits this case.
- **Sweep only a tracked record.** Pack leaves an open-time record untracked
  until close, and the desk path doesn't change that. If you've committed
  the record, the append goes through `sweep_commit` (the board-107 lesson)
  so the tree isn't left dirty.

`desk` is in the schema beside `bundle`, with its consumer named: the close
desk's reconstruction, per §6 entry 208's specimen. The desk test validates
the three-desk record against the updated schema, and that assertion fails
against the 0.4.43 schema.

## Row 124: the configured `agent_dir` in messages

All 24 lines the desk counted are handled.

**Emitted messages** now render the configured directory through a new
`bale_report.telemetry_home_display(repo)`. That covers:

- the dossier miss;
- the empty-corpus epoch row;
- the supersession close journal line;
- the read-only sweep journal line.

The two stats renderers take the home as a keyword that defaults to the
default agent_dir's rendering, so in-process callers without a repo keep the
old text.

**Docstrings** say `<agent_dir>/telemetry/`. Four literals remain, each
stating the default, and `validation.sh` pins exactly that.

**`bale stats --help`, a flagged mechanism choice.** The parser is built on
every invocation before any repo is resolved, and `load_config` calls
`fail()` on bad TOML. Rendering the configured directory at parser build
would have made `bale --help` read, and possibly die on, `bale.toml`. Instead:

- a formatter subclass substitutes the directory only when the stats help
  actually renders;
- it reads through a new non-fatal reader,
  `bale_config.layout_agent_dir_for_display`;
- an unreadable config renders the default plus a note saying so.

The top-level `bale --help` one-liner now names no path at all, because that
formatter has no repo to render one from.

## Row 125: cache hygiene

**The report's claim did not reproduce.** I found no site where a pack ships
a cache. The pack walk drops `__pycache__` by path component, whether the
cache is untracked or committed. I didn't invent a leak.

**I did find a real writer.** In `tests/test_context_pack.py`,
`test_open_preflight_refuses_a_context_argv` spawned a child Python under the
harness's scrubbed env. That env lacks `PYTHONDONTWRITEBYTECODE`, and the
child imports the source repo's own `bin/` modules, not a scratch install's.
Every suite run therefore left an untracked `bin/__pycache__` in the repo. I
reproduced it here even with the variable set in my own shell. The child now
runs with `-B`.

This is my best read of where the report's observation came from: a
`bin/__pycache__` visible in the tree. It is a writer, not a pack leak.

**The requested outcome landed regardless:**

- `--probe`'s skeleton carries a worked, single-line, cache-excluding tree
  listing that names `__pycache__`, plus the `git ls-files` alternative.
  `TARBALL.md` §1 forbids backslash continuations, so it is one physical
  line.
- `CacheHygieneTest` pins that a request pack and a context pack of a repo
  with no `.gitignore` ship no cache member. The fixture has two caches: one
  untracked, and one committed, which git lists and no ignore rule can hide.

**Flag for the §7.2 before/after rule:** the pack-side pin passes on the
0.4.43 tree too. That is inherent: it is a regression guard for a leak that
doesn't exist today. The scaffold assertion does fail on the old tree.

## The riders

1. **Lint.** `FORECAST_DEPARTURE_NOT_A_DEPARTURE` is a warning at the entry's
   own path, `feedback.self_reported.forecast_departures[j].path`. It fires
   for a declared path inside `resolved_scope`, or for a declared path that
   matches no `changes[]` entry. It is one code with two headlines, in the
   `--request` pass beside `FORECAST_DEPARTURE_UNDECLARED`.
2. **Crafter.** `--bundle` refuses an `--include` or `--write` value that
   names the `[validation] base` checkpoint. "Names" follows pack's own
   explicit-naming rule (`include_names_checkpoint`): the base itself, its
   `{sid}` basis, or a path under the basis. A broader ancestor (`.`,
   `claude`) passes, being incidental. An argv carrying
   `--allow-checkpoint-in-scope` passes, since that is the planner's stated
   delegation.

   To extend the existing `bale.toml` read as the rider asked, I factored the
   `[probe]` clipboard scan into a shared `scan_bale_toml_key`. The clipboard
   reader's notes are unchanged, and `test_probe_clipboard_config` is green.
   The doc sentence (TARBALL.md §3.4) is row 43's.
3. **Handoff stamp: the code had already landed; the code wins.**
   `cmd_handoff` already passes `command="handoff"`, as
   `persist_pack_session`'s docstring says ("wired since rows 63/73"). Two
   things were missing, and both are now done:
   - the test the rider names, now in `test_provenance_at_open.py`;
   - the schema's `command` description, which still called handoff "reserved
     … until that one-word bin/bale change lands".

## Other things to know

- **A wording collision, fixed on my side.** My row-121 "gates passed" log
  line first said "planner-bundle naming". `tests/test_bundle_denylist.py`,
  outside my forecast, pins that a clean pack prints "planner-bundle"
  nowhere. I reworded my line to "bundle-file naming" rather than touch that
  suite. The pack function carries a comment saying why.
- **Out-of-forecast suites.** `validation.sh` also runs these unchanged
  suites because my changes can reach them: `test_changelog_record`,
  `test_global_doc_selfcontainment` (tools touched, per the brief),
  `test_probe_clipboard_config` (the scan refactor) and
  `test_rollback_telemetry` (it pins the command enum's membership). None of
  them is shipped.
- **Budget.** The session paused twice on the tool-use limit. Each time it
  resumed with context intact; no compaction occurred.

## Proposals

- **The pack walk has no `*.pyc` basename rule.**
  - *What:* add `*.pyc`/`*.pyo` basenames to pack's baked-in exclusion.
  - *Why:* the walk excludes `__pycache__` directories, but a bare `*.pyc`
    beside sources would ship. The response contract (TARBALL.md §5.1)
    already denies exactly those names on the way back, so the two sides are
    asymmetric. Python 3 does not write such files by default, so I left it
    alone rather than invent a leak.
  - *Scope hints:* `bale_pack.py` `is_under_excluded_dir` and the §6.4 set;
    BALE.md's list.
- **The harness copies `bin/__pycache__` into every scratch install.**
  - *What:* pass `ignore=shutil.ignore_patterns("__pycache__", "*.pyc")` in
    `tests/harness.py`'s `make_install` copytree.
  - *Why:* scratch installs currently inherit whatever cache the source tree
    holds. Harmless today; a one-line fix.
  - *Scope hints:* `tests/harness.py`, which was not in my forecast.
- **Row 122 could put the new pass in the preflight.**
  - *What:* when row 122 grows `pack_argv_preflight`, have it call
    `pack_pre_exchange_gates`.
  - *Why:* `bale open` would then refuse these argv defects before the
    checkpoint dry-run rather than at replay. It's safe: the pass writes
    nothing.
  - *Scope hints:* the pass needs `read_includes` (with the include group's
    additions) and `gate_deferred`, which `cmd_pack` computes today.
- **Docs to follow this version (row 43 or a later doc session).**
  - *What:*
    - BALE.md's `bale open` section should describe the second-desk path, the
      `<sid>@desk-N` name and the refusal after an apply-side event.
    - The telemetry prose should mention `desk` and `command: "open"`.
    - TARBALL.md §3.4 should carry the crafter refusal's sentence, which is
      already row 43's.
  - *Why:* the docs were out of scope here.

## Final results

- **Full suite, rerun after the wording fix:** 1544 tests OK, with the same
  48 skips as the baseline. The tree held no `__pycache__` afterwards; the
  baseline run left `bin/__pycache__` behind.
- **`validation.sh` in a staging-shaped copy** (files overlaid, `apply.sh`
  run, manifest at `.bale-manifest.json`): every check passed, and all 23
  claims reconcile `[agree]`.
- **`validation.sh` on the unmodified 0.4.43 tree:** all ten outcome
  assertions fail, plus the syntax check (the 0.4.44 changelog record is
  absent there). The exec-bit checks and the row 125 pack pin pass there too,
  as explained above.
- **`tools/response_lint.py --request`:** clean, with no findings and no
  warnings.

