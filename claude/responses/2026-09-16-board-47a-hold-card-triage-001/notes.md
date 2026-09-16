# notes — 2026-09-16-board-47a-hold-card-triage-001

## The light question block, and its answers

I emitted one light block (TARBALL.md §5.10) before building. The packer
ratified all three defaults "as assumed", each with a stated reason:

1. **Should the card compose its successors from the stamp outcome or from the
   in-process tarball path?** From the stamp outcome. The card and
   `bale amend-checkpoint`'s report can then never disagree. A stamp that
   failed to write is the one case the card says so rather than papering over.
   - Implemented: `held_tarball` is the stamped path when the write succeeds,
     and `None` plus the reason when it fails.
   - Pinned end to end by planting a directory at the stamp path, which makes
     the loud-never-fatal branch fire without mocking.
2. **Should the amend line carry `--sid`?** Yes, always: four sessions are open
   this wave, so a sid-less amend refuses and is not pasteable. This is a
   deviation from the brief's literal `bale amend-checkpoint <amendment> --sha256
   <hex>`, now ratified.
3. **What renders on a literal `[validation]` base?** A one-line note to commit
   the amended bytes at the path directly, in place of the amend line. The
   composed `--accept-checkpoint-change --sid` retry rung stays beneath it.

## What the card looks like now

This is the specimen, rehearsed in a scratch sandbox with the tarball in a
directory whose name contains a space:

    [HOLD] 2026-09-16-spec-001
    judge:         blind checkpoint — checkpoint: HOLD (exit 1) · worker validation: PASS
    failed probes: oracle-probe-alpha
    branch:        bale/… (committed; `git diff main..bale/…` to inspect — checkout untouched)
    log:           .bale/logs/….log
    staging:       …/.bale/staging/… (preserved)
    telemetry:     recorded claude/telemetry/….json
    discard:       bale revert 2026-09-16-spec-001

    Next step, by the desk's ruling:
    fixture defect (the checkpoint is wrong) — amend at the desk, then retry the held tarball:
      bale amend-checkpoint <amendment> --sha256 <hex> --sid 2026-09-16-spec-001  # <amendment> and <hex> are the desk's published file and sha256 — unknowable when this card renders
      bale retry '/tmp/…/held dir/response-001.tar.gz' --accept-checkpoint-change --sid 2026-09-16-spec-001
    work defect (the response is wrong) — retry the corrected tarball, delivered where the held one is:
      bale retry '/tmp/…/held dir/response-001.tar.gz'

## Decisions to look at on review

- **Successors live in the trailer, not in rows.**
  - `format_summary_block` rows never wrap, but a fork is two commands, and
    the old one-row `retry:` form couldn't carry that.
  - The trailer is emitted verbatim, so each command stays one physical line
    (TARBALL.md §1).
  - The `discard` row stays, so it now sits above the forks rather than below
    a retry row.
  - I kept the fork prose in the trailer on purpose: it is what tells the
    operator which paste belongs to which ruling.
- **The `validation:` row is gone from the card.** The judge line replaces it.
  It carries the worker's exit code in every case, so no information is lost.
- **A checkpoint exit 2 counts as the checkpoint side.**
  - The judge case is `blind checkpoint`, or `both` if the worker also held,
    and the fixture fork renders.
  - The phrasing is the walkthrough's ("the planner's checkpoint itself
    errored"), minus its "; inspect the checkpoint script" tail. That tail is
    advice, not attribution, and the card's forks are the advice now.
- **The label parser lives in `bale_report`; `bale_staging` is untouched.**
  - The parser is `parse_failed_probe_labels`, and apply fills `failed_probes`
    on the checkpoint stamp.
  - It uses the same line-start grammar as `bale_open`'s dry-run echo, with
    leading whitespace tolerated.
  - The labels come from the checkpoint result's captured output, which
    matches the banded log section: stdout, then stderr. A `[FAIL]` line on
    stderr therefore sorts after every stdout line, which is how the log reads
    too.
  - A bare `[FAIL]` line records an empty label rather than being dropped, so
    the list length equals the number of failed lines. The card renders that
    label as `(unlabeled [FAIL] line)`.
- **`failed_probes` reaches two places beyond the HOLD record.**
  - It rides every executed-checkpoint stamp, including PASS attempts and the
    `--json` report's `checkpoint` key, because they share one stamp object.
  - `format_apply_json`'s key list, the key contract's one home, documents it.
- **The work fork carries no `--sid`.** That follows the brief's literal
  `bale retry '<path>'`: retry resolves from `responds_to`. The fixture fork's
  retry line keeps `--sid`, byte-identical to `compose_retry_successor`.
- **Literal-base detection** keeps the unresolved base key as
  `checkpoint_base_raw`. The fixture fork is per-session only when that key
  contains `{sid}`.
- **Schema descriptions cite versions, not boards.** The first full-suite run
  failed `test_global_doc_selfcontainment` on board citations in my three new
  descriptions. Install-shipped schemas must be self-contained, so I anchored
  them to v0.4.34. BALE.md keeps its board citations, since it is repo-local.
- **The `bale open` sentence is in the row, word for word.** I placed it
  directly after the replay sentence. `validation.sh` asserts it byte-exact on
  the row's line. My own-words version in §6.7 sits before the dry-run clause,
  where the order it describes actually happens.

## One-apply-behind

The apply that lands this response still renders the **old** card if it HOLDs:
the running `bale` is 0.4.33 until this merges. The desk won't see a judge line
or composed forks on this session's own HOLD, if there is one. The `failed
probes` label will be in the session log, not on stdout.

## Forecast

Every `changes[]` path is inside the write forecast, and no sibling's path is
touched. I read `tests/test_per_sid_checkpoint.py` and import its fixture into
two of my test files, but I don't modify it.

## Verification

- **Scratch tree:** the request's `context/` rebuilt as a git repo.
- **Baseline full suite:** 1058 tests. The only three errors are
  `test_include_group.TestThisRepoGroup`, which reads the repo-root `bale.toml`
  that the request doesn't ship.
- **After the change:** 1086 tests. The same three errors remain, plus the
  schema-citation failure described above, now fixed; the doc-pin suites pass
  after the fix.
- **Slow cases:** with `BALE_TEST_SLOW=1`, `test_hold_retry_e2e` and
  `test_amend_checkpoint` pass in full.
- **`validation.sh` on the changed tree:** exits 0 in about 52 s.
- **`validation.sh` on the pre-change tree** (with only the new tests copied
  in): exits 1. Nine claimed checks fail and the doc and schema pins pass. That
  is why the claims carry `claim_basis: observed`.

## Proposals

- **What:** make `bin/bale`'s `compose_retry_successor` delegate to
  `bale_report.compose_hold_successors`, taking the fixture fork's retry line.
  **Why:** today the two lines agree because I mirrored the composition and
  pinned equality with `HoldCardAgreementTest`. One function would make that
  agreement structural instead of tested. **Scope hints:** `bin/bale` belongs
  to `board-99a-outward-docs` this wave, so this rides the next `bin/bale`
  touch. The degrade line's wording differs slightly ("substitute the path
  below" versus "substitute the held response's path below"), and a pin on
  either wording would move.
- **What:** have `format_walkthrough_summary` build its checkpoint attribution
  through `_checkpoint_attribution`, the helper the judge line uses. **Why:**
  the vocabulary now lives in three places: the walkthrough, the apply log
  line, and the card. The card copies the walkthrough's phrasing, but nothing
  but review keeps them in step. **Scope hints:** `bin/bale_report.py` and
  `bin/bale_apply.py`'s HOLD log line; a pure refactor, but it would move the
  walkthrough's exit-2 tail if not handled carefully.
