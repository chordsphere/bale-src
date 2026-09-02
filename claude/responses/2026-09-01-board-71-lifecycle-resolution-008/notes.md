# notes — 2026-09-01-board-71-lifecycle-resolution-008

All seven work items landed; nothing deferred except one test shape
(below). No path outside the write forecast was touched — the
`tests/test_per_sid_checkpoint.py` upload was consumed as a fixture
dependency only and is not in `changes[]`.

## Latitude calls (each pre-ratified by the desk answer; recorded per the flag-everything rule)

- **Stamp key and placement.** `.bale/sessions/<sid>/held_tarball`,
  one line, the tarball's `.resolve()`d absolute path, written in the
  HOLD/inspect terminal action right after the integration lock
  releases and before the telemetry write. Constant `HELD_TARBALL_STAMP`
  in `bale_apply.py`. Per-attempt by construction: retry's
  `_discard_hold_state` wipes the session dir and a re-HOLD re-stamps.
  The write is loud-never-fatal — the HOLD's git work is done by then.
- **Resolve-before-wipe.** `resolve_retry_session` runs before
  `_discard_hold_state`; every refusal (mismatch, closed, unknown,
  unreadable tarball, no manifest member) leaves the held branch,
  `staging_path`, the open marker, and `held_tarball` byte-identical.
  Pinned by `assert_hold_intact` in every refusal test. The old order
  (resolve, discard, then let the pipeline refuse) would have wiped a
  HOLD on a wrong tarball; the desk wanted that closed, so it is.
- **Unknown vs closed.** `describe_non_open_session` in `bin/bale`:
  telemetry record → closed, naming the record's `outcome` (defensive
  read: malformed JSON or a missing/non-string outcome still says
  closed, with "outcome unreadable"/"no readable outcome" and the
  path); session dir without an `open` marker and no record → closed,
  saying which; neither → unknown to this repo, keeping apply's
  "wrong repo, or a stale tarball" framing.
- **Rider.** `bundle_change_paths` in `bale_apply.py` reuses
  `bale_pack.is_bundle_file` (lazy import, the module's convention), so
  rows 33 and 37 cannot disagree on what a bundle is. Sited directly
  after the generated-artifact check as §8.1 step 18 / §11 row 37; the
  §11 header now reads "steps 1–18".
- **Version 0.4.25.**
- **`peek_responds_to`** is the new public spelling of
  `_peek_responds_to` (bin/bale imports it for retry); the underscore
  name is kept as an alias so nothing out of tree breaks. Its refusals
  now name the tarball (basename in the sentence, full path on a second
  line), which apply's multi-open path inherits — a small message
  change on that surface, no behavior change.

## Where to look on review

- `bin/bale` `resolve_retry_session` — the mismatch check runs before
  the open-membership check on purpose: when `--sid B` is given and the
  tarball says `A`, the operator's belief and the artifact disagree, and
  that is the fact to name regardless of which of the two is open.
- `bin/bale` `compose_retry_successor` — the composed path is
  `shlex.quote`d, so a path with spaces still pastes; the test asserts
  the unquoted form because the harness's temp paths have none.
- `bale_apply.py` HOLD branch — the stamp sits between
  `release_integration_lock` and `write_telemetry_record`. If you'd
  rather it went before the lock release (nothing depends on the
  ordering; I put it after so the lock window stays exactly as it was),
  it is a two-line move.
- `BALE.md` §3.4 — I also documented `staging_path` in the session-dir
  listing while adding `held_tarball` beside it. It existed and was
  undocumented there; `held_tarball` would have read oddly as "beside
  `staging_path`" with `staging_path` absent from the listing. Sweep
  territory under W4, but say so if you'd rather that line came out.

## Surprises

- `log()` prints to stdout, not stderr — my first draft of the
  legacy-degrade test looked for the FORCE line on stderr. Test fixed;
  no code change.
- The fixture API I inferred from `test_amend_checkpoint.py`'s usage
  matched the uploaded `test_per_sid_checkpoint.py` exactly — no delta
  to report.
- The sandbox's clock reads 2026-09-02, so sids minted during my runs
  carry that date. Nothing keys on it.

## Claims

All test claims are `observed`: the three suites and a full
`unittest discover` over the shipped `tests/` subset ran green inside
a simulated staging (base tree + `files/` overlay + `apply.sh`), 74
tests, 60s wall. One caveat on "tests: full discover (default gate)":
the request shipped six test files, and the real tree has more, so
the real discover is larger than the one I observed — the suites this
session touched are pinned individually above it either way. If the
real discover pushes validation past the two-minute target, that
check is the one to gate behind `--slow`.

## Deferred (also in the manifest)

- A positive accepted-apply case for a `notes/x.bale-bundle.md` path
  in the preflight reject class: that class asserts nothing was
  applied, which a landing apply can't satisfy. The suffix boundary is
  pinned by the pure `BundleChangePathsUnitTest` instead.

## Proposals

- **What:** the HOLD banner's `retry` row still prints the literal
  `bale retry <new-tarball>`. With the stamp now on disk at the moment
  that row renders, it could print the composed line the same way
  amend-checkpoint does.
  **Why:** the same placeholder-vs-composed friction the brief
  describes, one surface over; the operator reads that row first.
  **Scope hints:** HOLD-card rendering is board 47's charter and this
  session's `out_of_scope`, so review-only here; `bale_apply.py`'s
  inspect branch, one row.
- **What:** `bale handoff <tarball>` and `bale open <bundle>` both hold
  a manifest-bearing artifact; the ADR-0006 note says the pattern
  generalizes. Worth checking whether either still requires `--sid`
  with several open where the artifact already names the session.
  **Why:** the `revert/unlock/handoff resolution semantics` line is
  out of scope this round by the desk's choice, so this is a queue
  item, not an omission.

- **What:** the response-manifest schema's `feedback.mechanical.provenance`
  echo does not admit the request's `base_files` key (the board-41
  stamp), so the "echoed verbatim" instruction in TARBALL.md §5.2.2
  can't be followed literally — I dropped `base_files` from the echo
  to validate.
  **Why:** the request-side schema grew a key the response-side echo
  never learned; either the echo schema gains `base_files` or §5.2.2
  says the echo is minus the stamp. Schema-only fix.
  **Scope hints:** `schemas/response-manifest.schema.json`, the
  provenance sub-object; one line in TARBALL.md §5.2.2.
