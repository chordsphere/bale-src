# Notes — 2026-09-17-board-56-57-changelog-aborted-002

Rows 56 and 57 landed with the 0.4.35 bump. Below: the two
out-of-forecast paths to admit, the light-block trail, where I read the
desk's landing shape differently, what surprised me, and proposals.

## Paths outside the write forecast (admit at apply)

Both were pre-authorized as ship-enumerate-admit by the brief and the
constraints; nothing else lands outside the forecast.

- `claude/changelog/0.4.35.json` — the family's first record, this
  version's own. `claude/changelog/` did not exist at pack, so no
  forecast entry could name it.
- `tests/test_changelog_record.py` — the suite for
  `validate_changelog_record`, the schema's parity, and the
  `claude/changelog/` corpus. No forecast test file has that subject.

Everything else is inside the forecast. `schemas/changelog-record.schema.json`
is covered by the `schemas` entry, and `docs/CODE.md` is named.

## Light question block — the trail

Last turn ended on a light block with two questions, answered
**"as assumed"**. Both defaults are ratified:

1. *Resume and pack the response tarball?* — ratified: yes.
2. *Keep the discipline sentence in `docs/CODE.md` §8.5 rather than
   withhold it as a TARBALL.md rider?* — ratified: yes, it stays in
   CODE.md.

I owe you three admissions about that block. First, it was not
§5.10-shaped: no `=== LIGHT BEGIN/END <sid> ===` sentinels and none of
the four row labels. I had not re-read §5.10 before writing it; I did
this turn. Second, question 1 was not a real intent question. The turn
had simply hit the tool-call limit before packing, and Continue would
have resumed it. Third, the build was already done when I emitted the
block, which is the reverse of §5.10's "nothing is built ahead of the
reply." Question 2 was the one real ask, and nothing hinged on it.
`feedback.self_reported.light_blocks` records the one block.

## The desk's landing shape — ratified, with these corrections

- **Schema.** Ratified as described, with these choices of mine:
  - the row key is named `change`;
  - `surfaces` has `minItems: 1` — a version that changed no
    machine-readable surface writes no record, so an empty list is an
    error;
  - optional `updated_at` and `notes` fields;
  - each row takes an optional **`session_id`**.

  That last one is the real addition. One file per version meets waves
  with more than one writer: if the stats micro, or any later
  same-version session, changes a surface, it appends a row naming
  itself instead of overwriting the record's `session_id`. Absent reads
  as the record's own.
- **Validator.** Mirrors `validate_escalation_record`: shape pass, then
  the rules the schema subset can't express (X.Y.Z version, UTC `at` and
  `updated_at`, repo-relative surface paths). Instead of copying
  exchange's timestamp check, I gave `_created_at_problem` a `field`
  parameter. The default keeps exchange's messages byte-identical, and a
  test pins that.
- **What "loud" covers — please read.** The validator makes a missing
  *field* loud. It does not make a missing *record* loud: a future
  surface change with no record fails nothing. The corpus test only
  checks the records that exist, plus the presence of 0.4.35.json.
  Proposal 2 would close that gap; it's your call because it binds every
  future bumper.
- **Discipline sentence.** CODE.md has no release-list rules for it to
  sit beside, so it's a new **§8.5** under Meta Code (§13.3 is the
  precedent for a same-response rule living in CODE.md). It is one
  sentence, scoped to "when a meta-code project keeps changelog
  records." It names the schema, which ships with the install, rather
  than `claude/changelog/`, which is project-local. It explicitly says a
  structured surface list is not the narrative log `CLAUDE.md` §7 rules
  out: CLAUDE.md §5 and §7 both say "no master changelog", and I didn't
  want the new family to read as contradicting them. I don't judge
  TARBALL.md the only right home, so nothing is proposed there.
- **Inventory.** `scripts/build.sh` RELEASE_FILES, `install.sh`
  INSTALL_LAYOUT, and `validate.sh`'s schema loop each gained the
  schema. `upgrade.sh`'s REQUIRED_RELEASE_MEMBERS is untouched: it is a
  deliberate brick-check subset, and the exchange-record packaging
  precedent didn't extend it either.
- **The record's surfaces.** Five rows: the new schema,
  `bin/bale_validate.py`, the telemetry schema, `bin/bale_report.py`,
  and `scripts/build.sh` (whose row notes that install.sh and
  validate.sh follow). `bin/VERSION` is the record's `version` key, not
  a surface row.

## Row 57

`aborted` is added in both homes; the schema enum and `CLOSURE_REASONS`
are pinned as equal sets. A real `bale unlock --reason aborted` round
trip stamps it, and the written record passes
`validate_telemetry_record`. So the `choices=CLOSURE_REASONS` wiring
needed no `bin/bale` edit, as the desk said. I did not open
`bin/bale_stats.py`; "no stats change" rests on the desk's verification.

The `bin/bale_report.py` touch is exactly three inserted lines in the
tuple: the value plus a two-line comment. `validation.sh` proves it by
reverse-transforming the file to its `base_files` stamp, so your merge
with the stats micro is mechanical. One oddity I left alone: the
tuple's long explanatory comment block sits about 150 lines above it,
over `SANDBOX_OFF_SOURCES`. Moving it would have widened the touch.

## Look closely on review

- **The CLOSURE_REASONS parity suite wasn't in the request.**
  `bin/bale_validate.py` says parity "is pinned separately by test"; my
  guess is `tests/test_telemetry_extensions.py`. If it compares the
  schema enum to the tuple, it still passes, because both moved
  together. If it lists the vocabulary literally, it will fail on
  `aborted`. It's recorded in `includes_missing`. My own set-equality
  pin in `test_closure_telemetry` covers the property either way.
- **Pre-existing guard failure.** `tests/test_global_doc_selfcontainment.py`
  already fails on the request's own tree: `tools/craft_response.py`
  and `tools/response_lint.py` carry "board 69" citations, probably
  from row 69's landing. Both files are outside my forecast. In
  `validation.sh`, the full suite reports **SKIP** when every failure is
  in those two files, and FAIL otherwise. Separately, a claimed check
  runs the guard's own deny tables over the five docs and six schemas,
  the new one included. I claimed the full suite `unknown` because I
  can't see your tree's `tools/` bytes (no `base_files` stamp covers
  them).
- **The blind checkpoint** runs beside my script and I haven't seen it.
  Nothing here was shaped around it.

## Verification basis

Every `pass` claim is `observed`. I ran `validation.sh` in a simulated
staging tree: the request's base copies (every `base_files` stamp
matched), `files/` overlaid with modes stripped, `apply.sh` run, and
the manifest placed at `.bale-manifest.json`. Result: exit 0, twelve
claims `[agree]`, and no writes outside `.validation-logs/`. That run
covers the real `scripts/build.sh` and a sandboxed install of the built
0.4.35 release, whose `validate.sh` checks the new schema. It does not
cover suites the request didn't ship.

The request-carried tools: before running them I read their CLI
surfaces, module docs, imports, and every file-write site (stdlib only,
no network, no subprocess), not all ~5,000 lines.

## Proposals

- **Scan the new schema in the self-containment guard.**
  - *What:* add `changelog-record` to `INSTALL_SCHEMAS` in
    `tests/test_global_doc_selfcontainment.py`.
  - *Why:* the guard's docstring says to update it alongside the
    schemas tree. The new schema ships with every install but isn't
    scanned yet. This session's validation.sh scanned it clean once.
  - *Scope:* one tuple entry.
- **Make a missing record loud.**
  - *What:* a pin that `claude/changelog/<bin/VERSION>.json` exists.
  - *Why:* the validator makes an omitted field loud, not an omitted
    record; with this pin, a bump that forgets its record fails the
    suite by name.
  - *Scope:* `tests/test_changelog_record.py`. Decide first whether
    every bump must carry a record, or only bumps that change a surface;
    the pin enforces the former.
- **Purge the tools/ citations.**
  - *What:* reword the "board 69" citations out of
    `tools/craft_response.py` and `tools/response_lint.py`.
  - *Why:* they fail the self-containment guard on the base tree, and
    every session running the full suite inherits the red.
  - *Scope:* prose-only edits to docstrings and help text in two
    request-injected files, with no schema embed touched; one small
    doc-lane session.
