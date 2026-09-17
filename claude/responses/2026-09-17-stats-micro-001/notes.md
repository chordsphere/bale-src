# Notes — 2026-09-17-stats-micro-001

All four parts landed. The dossier wiring needed no renderer change.
`bin/VERSION` stays 0.4.34, and `validation.sh` asserts that against
this response's own `changes[]`.

## The light question block, and your answer

I ended one turn on a light question block with three rows. You
replied "as assued". I read that as "as assumed", which ratifies all
three defaults. If you meant something else, all three are one-helper
swaps.

1. **Retried sessions count once.** `light_blocks`, `paste_carried_rounds`
   and `docs_read` each read the latest attempt carrying them per
   session. They are not summed across attempts. A HOLD→retry session
   restates its counts on the retry manifest, so summing would count
   them twice.
   - Answer: latest (as assumed).
2. **Tokens shed surrounding punctuation.** The character set comes from
   the lint tokenizer, mirrored in `bale_stats.py` rather than imported.
   After that, one leading `context/` strips. Empty tokens drop, and
   counts are occurrences.
   - Example: `"context/docs/TARBALL.md (sections 5, 7)"` yields
     `docs/TARBALL.md`, `sections`, `5`, and `7`.
   - Answer: strip (as assumed).
3. **Totals follow filtered membership.** The five new corpus totals
   honor `--work-class` and `--since` and exclude read-only and
   crash-debris sessions, the same as `sessions` and the attempt totals
   beside them.
   - Answer: membership (as assumed).

## Decisions to ratify (beyond the three above)

- **`--sid` with `--work-class` or `--since` is refused.** It goes
  through `fail()`: stderr, non-zero exit, nothing on stdout. Those
  flags filter aggregate membership, and a dossier is one record
  rendered whole. Silently ignoring a typed filter would misreport what
  was read.
- **Unusable telemetry dir.** This means the path exists but is not a
  directory, or it cannot be listed (`bale_stats.telemetry_dir_problem`).
  - An absent `claude/telemetry/` is not an error. It is the honest
    empty corpus, so every sid gets `found: false` at exit 0, matching
    the aggregate's empty-report posture.
  - Only the "not a directory" case is tested end to end. The
    cannot-list case isn't, because permission bits don't bind in a
    root sandbox; the code path is the same `OSError` catch.
- **Bad sid.** Only a blank or whitespace-only `--sid` is refused. Any
  other string is looked up, so a malformed-but-nonblank sid is an
  honest miss, never a refusal. I didn't add a shape check, because
  it would turn a checkpoint's "unknown sid" into an error.
- **Handoff origin keys on `outcome == "opened"` and
  `command == "handoff"`.** A `handoff` command on any other attempt
  does not count. A pre-v0.4.21 handoff session reads as not
  handoff-origin, which is the honest pre-epoch unknown.
- **`clarification_rounds_total` per session.** It is the closing
  stamp's `rounds` (0 when absent or malformed) plus that session's
  `paste_carried_rounds`. An in-flight session with a paste-carried
  round therefore contributes that round even though it has no stamp.
- **Malformed counts.** `true`, negative, and string values read as no
  report (0). No record fails to aggregate over them.
- **Human rows.** A `docs read:` body line renders when any session
  reported; tokens are most-read first. Three summary rows are always
  rendered, and `filters` stays last, which an existing assertion reads:
  - `handoff-origin`
  - `clarification rounds: N (S stamped + P paste-carried)`
  - `light blocks`

## Fixtures (inside the forecast's `tests/fixtures/stats_corpus/` entry)

The brief says new fixture files travel ship-enumerate-admit, so here
they are by path:

- **`tests/fixtures/stats_corpus/2026-06-30-fx-handoff-origin-001.json`**
  - An `opened`/`handoff` attempt prepended to an applied code session.
  - A `context/`-prefixed docs_read.
  - `light_blocks: 2` and `paste_carried_rounds: 1`.
  - A promoted `rounds: 1` stamp, beside a self-reported clarification
    linkage. The linkage keeps the cross-check agreeing in both
    directions instead of adding a promoted-only disagreement.
- **`tests/fixtures/stats_corpus/2026-06-30-fx-docs-read-002.json`**
  - The repo-relative `docs/CLAUDE.md` sibling.
  - Carries neither count, which exercises the absence case.

Both validate under `validate_telemetry_record`, and
`test_telemetry_extensions.py` passes unchanged over them.

- **Why 2026-06-30:** it is inside every existing window, before the
  `2026-07-01` `--since` fixture, and moves no coverage `first_sid`.
- **What the opened attempt omits:** the post-epoch stamps
  `build_telemetry_attempt` writes (`scope_kind`, `cost`, …). Carrying
  `scope_kind` would start that sub-epoch inside the whole-corpus
  expectations, which belongs to the queued post-epoch fixture fold-in,
  not here.

Every perturbed count in `test_stats_aggregation.py` carries a comment
saying why it moved. I derived them by hand first and then confirmed
the run agreed.

## Surprises

- `format_session_dossier_json`'s docstring lists the attempt view's
  keys but omits `base_drift_overrides`, which `_dossier_attempt` emits.
  I left it alone, because the ask was wiring and the dossier line's
  contract is its own surface. It is proposed below.
- The dossier tests' mutation check: against the pre-change `bin/bale`,
  6 of the 7 new E2E tests fail. The blank-sid refusal passes either
  way, because argparse's unknown-argument error is also fail-shaped.

## Proposals

- **What:** Add `base_drift_overrides` to the attempts key list in
  `format_session_dossier_json`'s docstring.
  **Why:** the computed view emits it (board 41), and the docstring owns
  the dossier line's key contract, so the contract is one key short.
  **Scope hints:** `bin/bale_report.py`, docstring only. The file is
  shared with 56+57 and 47b, so the fix should ride whichever holds it
  next.
- **What:** Document `bale stats --sid` and the five new corpus keys in
  BALE.md §5.6's stats prose.
  **Why:** the CLI help and `format_stats_json`'s docstring now carry
  them, but the user-facing section does not.
  **Scope hints:** row 99b, already queued; this is input for its brief.
- **What:** Fold the post-epoch attempt stamps (`scope_kind`, `cost`,
  sandbox posture) into the fixture corpus, including the new handoff
  record's opened attempt.
  **Why:** this session dated and shaped its two records to stay out of
  those sub-epochs. The whole-corpus expectations still predate them,
  and the drilldown suite's docstring already names that fold-in as
  queued.
  **Scope hints:** `tests/fixtures/stats_corpus/` and
  `tests/test_stats_aggregation.py`. It must re-derive the coverage and
  forecast rows.
- **What:** Row 106 can take `bin/bale` once this response applies.
  **Why:** this session's `bin/bale` change is confined to the stats
  subcommand (`cmd_stats`, `_stats_dossier`, the `p_stats` flag, and two
  import lines).
