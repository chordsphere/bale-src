# Notes — 2026-09-22-rider-micro-003 (bale 0.4.41)

All five riders landed in one additive bump. Every changed path is in the
forecast, so nothing needs admitting at apply. `claude/changelog/0.4.41.json`
is a new file, but it sits under the forecast's `claude/changelog/`
directory entry. `validate.sh` did not change, because no `--help` list
moved. `apply.sh` has one line, `chmod +x bin/bale`: the file is 0755 in
the tree and the overlay strips the exec bit. `validation.sh` asserts it.

I ran every suite in the tree (72) on the changed copy. 71 pass.
`test_handoff_fixture` collects no tests, and it does the same on the
untouched tree; it is a fixture module, not a suite.

## Judgment calls to ratify

**How the cause is captured (rider 1).** Neither of your guesses. `fail()`
now raises the `SystemExit` itself and attaches `bale_cause`, the message's
first non-blank line (`failure_cause`). `exit_cause` reads it back and
falls back to `exit <n>` for an exit that bypassed `fail()`. A
`sys.exit("<text>")` gives its text's first line instead.

I chose this over a module-level last-failure slot because the cause
travels with the exception that is actually being handled. A slot can
outlive its exit, or be overwritten by a nested `fail()` inside a
`try/except SystemExit` somewhere in the pipeline (`bin/bale` has at
least one, the status path). Reading the log's last line would depend on
a log file being open. Exit codes, stderr and the session log are
byte-for-byte unchanged.

A multi-line refusal gives its headline, for example `sha256 mismatch for
hello.txt: manifest=000000000000..., actual=7f8b...`. For the schema gate
the headline ends in "nothing preserved:" and the detail rows stay in the
log.

**How open reaches the opened attempt (rider 2).** Through the in-process
namespace channel `pre_answered` already uses. `cmd_open` sets
`pack_args.open_bundle`, and `cmd_pack` reads it with
`getattr(args, "open_bundle", None)` and passes it through
`persist_pack_session`. There is no environment variable, which cannot
leak into a nested process, and no post-sid stamp, which would need open
to parse pack's `--json` line. It is one write, in the same writer as
`provenance`.

**The `bundle` object's keys.**

- `stem`: the file name minus `.bale-bundle`.
- `brief_sha256`: the bundle manifest's published member hash, which
  `read_bundle` has just verified; null for a no-brief bundle.
- `checkpoint_sha256`: the same, for the checkpoint member.
- `manifest_sha256`: the sha256 of `bundle.json`'s LF-normalized bytes.

`stem` and `brief_sha256` are required. I added the checkpoint hash
because two revisions can share a brief and differ only in their oracle.
I added the manifest hash because they can also differ only in `pack_argv`
or intents.

`read_bundle` returns the parsed manifest, not its bytes, so
`bundle_identity` re-reads `bundle.json` from the tar. I chose that over
changing `read_bundle`'s return shape. If the re-read fails (the file
changed underneath), the field reads `"unreadable"` with a loud log line.
A telemetry stamp is not worth refusing an open over. The schema
description says so.

**Which relay refusals record (rider 3).** Every refusal of the input
itself writes `relay-refused` with `cause`: parse, trailer, sentinel sid,
not-an-object, schema, sequencing, round-one-is-worker-only, and answer
resolvability (steps 2–5). Three kinds record nothing:

- The session gates (sid not open, `bale/<sid>` branch present). A bogus
  sid would otherwise grow a record, and a held session's envelope would
  flip from `held` to `relay-refused`.
- A missing input file. It never reached relay.
- A successful relay, which stays silent as before. The thread's
  preserved records and the closing `clarification` summary already carry
  every round. I found no reason to add an attempt; see Proposals.

To wrap exactly steps 2–5, I split them out of `cmd_relay` as
`_ingest_and_gate`, and steps 6–7 as `_preserve_and_emit`. The logic
moved unchanged, and all 27 pre-existing relay tests still pass.

**The re-escape check.** It runs only after the plain hash has
disagreed. `reescaped_body_matches` parses the body, re-renders it
through `_exchange_body_bytes` (the emitter's own renderer, so the two
cannot drift) and compares. On a match, the refusal names the fault: the
carrier unescaped the `\uXXXX` escapes, the content is intact, re-carry
the block byte-for-byte. It still refuses. I did not make relay accept
the recovered body, because that would soften the integrity gate.

**Where `relay-refused` counts.** It joins `IN_FLIGHT_OUTCOMES`. Its
command `relay` is outside `RESPONSE_COMMANDS`, so it adds no response
attempt and gets no per-class row. The changelog entry says this.

**Dossier spelling (rider 4).** The line is literally `    swept by <sid>`,
with no colon, as the brief pins it. The line above it is
`    superseded by: <sid>`, with a colon. If you meant the sibling's shape,
it is a one-character change in `format_session_dossier_report` plus
`RiderMicroDossierTest`.

I also surfaced `cause` (`    cause: …`) and `bundle` (`    opened from
bundle: <stem> (brief <sha12>…)`) in both renderings. They are cheap, the
close desk is their consumer, and the dossier is where it reads a
session. The JSON key contract in `format_session_dossier_json`'s
docstring lists all three.

**Held admissions (rider 5).** I extracted the clean-apply relay's
admission renderer as `relay_admission_rows`. The HOLD planner block uses
the same words: `admissions:` with indented rows, or `admissions: none`,
directly after `held tarball:`. It covers admitted paths with their
sources, required-check and base-drift overrides, and an accepted
checkpoint change. `--no-sandbox` is not listed, matching the apply
relay. The worker block is byte-identical, and a test pins that. A caller
that passes no `admissions` gets no line; apply's HOLD path always passes
the dict.

## Things the brief had slightly off

- `tests/test_rollback_telemetry.py` did not pin the envelope's outcomes
  as a subset of the attempt's; it checked two values one by one. I added
  a real `assertLessEqual` subset guard, plus every 0.4.40 outcome and
  command by name.
- The attempt enum and the envelope enum are separate literal lists in
  the schema. They agree, and the new guard keeps them agreeing.

## Things to look at on review

- `fail()` now ends with `raise exit_exc` instead of `sys.exit(code)`.
  These are equivalent, since `sys.exit` just raises `SystemExit(code)`,
  and nothing in the suites patches `sys.exit`.
- The changelog `at` is the pack instant, `2026-09-22T12:36:35+00:00`. I
  have no better clock for when this response was authored; the date
  follows the session id.
- `validation.sh`'s two scratch-repo assertions duplicate a little of the
  new suite coverage on purpose. They are the brief's named assertions,
  and they run against the staged install. Before shipping, I checked
  that both fail on the untouched tree and pass on the changed one; so
  does the live-specimen dossier assertion.

## Proposals

1. **A `bale stats` read side for the three new fields.**
   - What: a `relay-refused` count beside the drift refusals, and a
     cause histogram for `rejected` attempts, keyed on the cause's text
     before the first colon.
   - Why: the refusals are now distinguishable in the record, but
     aggregate stats still says only "rejected N". The first-colon prefix
     is a natural gate key: "sha256 mismatch", "tarball is unreadable",
     "exchange record fails …".
   - Scope hints: `bin/bale_stats.py` `_class_row` and the membership
     buckets, `format_stats_json`'s docstring, and
     `tests/test_stats_aggregation.py`. Wait until a consumer is named,
     per DOCS.md §9.
2. **Stamp `handoff` on handoff-side opens.**
   - What: the command enum's own description says handoff opens still
     stamp `pack`, pending a one-word `bin/bale` change.
   - Why: I was in `persist_pack_session`'s signature this session and
     saw that the fix is to pass `command="handoff"` at `bin/bale`'s
     handoff call site. It was out of this goal, so I did not make it.
   - Scope hints: `bin/bale` near its `persist_pack_session(repo,
     new_sid, …)` call, and `tests/test_provenance_at_open.py`.
3. **A short cause code beside the first line.**
   - What: a closed `cause_code` vocabulary (`sha-mismatch`,
     `scope-drift`, `trailer-mismatch`, …) set at the major `fail()`
     sites.
   - Why: first-line text is exact but wording drifts across versions,
     which would fracture a histogram. A code is stable, but it means
     touching many `fail()` sites, and the brief allowed either form.
   - Scope hints: `bin/bale_apply.py` pre-flight, `bin/bale_relay.py`
     `parse_exchange_input`, and the schema.
