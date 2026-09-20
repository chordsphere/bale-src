# Notes — 2026-09-20-board-37-compaction-read-side-003

## Baseline, as asked

Checked on the shipped tree before I changed anything. `test_include_group` and
`test_changelog_record` passed (37 tests between them), the install's
`validate.sh` passed 91/91, and the full suite passed 1352 tests with 47 skips.
After the change the full suite passes 1364 tests (the new suite adds 12) with
the same 47 skips, and `validate.sh` is still 91/91.

## The number on the real corpus

`bale stats` over the `claude/telemetry` that ships reads **206 reporting, 7
disclosing**. That is over 276 parseable records; the desk counted 274, because
two records dated 2026-09-20 have landed since. The default membership
exclusions don't move either number, since no discloser is read-only or crash
debris. Any-attempt and latest-carrier agree on every session. The seven
disclosers:

- 2026-07-31-master-v4-regeneration-012
- 2026-08-07-board-13a-forecast-surface-004
- 2026-08-11-board-10-sandbox-wrapper-001
- 2026-08-12-board-10-network-grant-001
- 2026-08-14-bare-pack-oneshot-003
- 2026-08-26-board-53-amend-checkpoint-004
- 2026-08-31-board-44-stats-read-sides-024

The last is dated 08-31 but numbered 024, earlier that day than the ruling's
026, so "all seven predate the ruling" holds.

On the ruling's other eight, the one thing I happened to notice: no record
carries `occurred: false` beside a `disclosure_ref`. Wherever the hand count
found fifteen, it was not in structured telemetry.

## Please ratify: a pre-existing crash I fixed

The budget pressure pass beside the new reader did
`(feedback.get("self_reported") or {}).get("budget_pressure")`. A truthy
non-dict `self_reported` (a string, say) raised `AttributeError` and took the
whole `bale stats` run down. The brief's definition says a malformed shape
"never crashes the run". That could not be true while the loop the new reader
shares could crash first, so I made that read tolerant, the way every other
`self_reported` read in the module already is.

Every value that computed before buckets exactly as before; only the crash case
changes, and it now lands in `unreported`. No real record has that shape, so the
real-corpus output is unaffected. `test_hostile_self_reported_never_crashes`
pins it. It's in the changelog row for `bin/bale_stats.py`. If you'd rather it
rode a separate session, it's one hunk to drop.

## Forecast departure to admit at apply

- `tests/test_stats_compaction.py` (new). The disclosing shapes need a corpus
  that discloses, and none of the shared fixtures does. Adding one there would
  recompute the shared expectations and half-carry the declined post-epoch
  fixtures rider, so I took the own-suite path the brief offered (board 44's).
  The shared suite changed only in its whole-dict `budget` expectation, which
  now includes `compaction: {25, 0}`. The rider's condition is **not** met.

`claude/changelog/0.4.38.json` sits under the forecast's `claude/changelog`
entry, so it needs no admission.

## Decisions worth a look

- **Where the count renders.** It gets its own line directly under the budget
  line (`cross-check compaction: disclosed N of M reporting sessions`) rather
  than being appended to that line. The budget line's text stays byte-stable
  for anyone grepping it. The sid line comes for free: the corpus-members block
  already renders every non-empty `members` bucket.
- **Counts, not a rate.** I didn't add a disclosure rate. It's the least
  checkable field on the manifest, and a percentage would read as more
  calibrated than it is. The two counts keep both halves visible. Easy to add
  later if you want one.
- **Any-attempt semantics.** A HOLD→retry session whose retry says `false`
  still counts as disclosing if its first attempt said `true`. The compaction
  happened in that session. This is the brief's definition, and the docstring
  says why.
- **Paragraph placement.** The single-window paragraph closes PLANNER.md §11
  (Decomposition at Seams). The window is the unit decomposition cuts to, and
  that section already says "each fit a context window". It is not in a
  provisional-until-S6 section, and it cites only CLAUDE.md sections. It
  carries the 08-31 finding in general terms: recovery rather than the reactive
  bail is the de facto primary defense on auto-compacting surfaces, and the
  pre-flight check stands.
- **Step 5 clause.** I checked the code before writing it. Since 0.4.37 the
  fixture rung, built by one composer and printed on both the HOLD card and
  `amend-checkpoint`'s close, re-states the held apply's admissions.
- **Suite pins on BALE.md.** None of the suites I ran pins BALE.md against the
  stats keys (full suite green), so I made no BALE.md edit.

## validation.sh

Nine checks run by default in about 11 seconds in my staging dry run. The full
suite, about 3.5 minutes, is gated behind `--slow`. It passed here, so the claim
is `pass`, but the default run records a skip, which shows as `[n/a]`. The
version invariant is relative: `bin/VERSION` must be the patch successor of the
highest other changelog record, and its own record must exist and name this
session. As a negative control, every session-specific assertion fails against
the unchanged request tree.

## Retry after the HOLD (corrects the held response)

The checkpoint held on "PLANNER.md §5 step 5: the retry clause mentions the
held apply's admissions". It was right. The brief pinned "the word
`admissions` is in it", and my clause said "re-stating every admission the held
apply exercised … already carries them", so the plural never appeared. My own
`validation.sh` checked for the substring `admission`, which the singular
satisfies, so it passed a clause the brief's condition did not.

The fix uses the rider's own words: "re-stating the held apply's admissions
(none carries forward from a failed attempt, and the retry line bale prints
already carries those admissions)". The assertion now requires both `admissions`
and "held apply's admissions" in step 5, with whitespace normalized so a line
break can't hide the phrase. It fails against the held version's step 5.
`docs/PLANNER.md` is the only file whose bytes changed; the rest of this
response is as held.
