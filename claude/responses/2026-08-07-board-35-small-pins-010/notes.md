# notes.md — 2026-08-07-board-35-small-pins-010

## The headline: pin 5 was already done

The brief's fifth item — pin the row-32 identical-duplicate refusal —
is already covered by the shipped tree, so this response deliberately
adds nothing for it. What I found:

- The check exists in `bin/bale_apply.py` (the "8.1 step 16 / §11
  row 32" block, v0.4.2, keyed on identical path strings via a
  Counter over `changes[]` — matching the lint's basis, as the
  ratified semantics specify).
- `tests/test_apply_preflight.py` **as shipped in this request**
  already contains `test_row32_duplicate_changes_path` with both
  variants (identical duplicate, conflicting duplicate), and its
  module docstring already lists row 32 as covered, noting the earlier
  behavior pin is "superseded by the row's own test."
- I ran the test against the shipped sources: it passes.

My reading: the board-13b session that ratified the rider and added
the check shipped its pin test in the same response — exactly what the
"tests ship with code" hard rule predicts — and the brief's item 5 was
queued from session 1's notes before that landed. Duplicating the test
would have been worse than noting the finding. **Please confirm this
reading at review**; if the shipped copy of the test file was somehow
ahead of your real tree, the diff for this response still applies
cleanly (my changes don't touch that test), but the row-32 coverage
claim would then rest on the board-13b response landing first.

One small narrative wrinkle I did not touch: the shipped docstring
says the suite's "earlier behavior pin ... documented the
identical-duplicate acceptance," while the brief says session 1
"deliberately did not pin that behavior." Whichever is right, it's a
docstring history note, not load-bearing; flagging it only so the
discrepancy is on the record.

## Judgment calls

- **Row-8 home: a second class in `test_apply_preflight.py`, not a
  new file.** The brief left this my call. The existing file already
  owns the sandbox, pack, and builder plumbing the trio needs, and
  staying in a forecast file avoids drift. But row 8 has proceed-cases
  as well as the refusal, which the reject class's "refuses loudly and
  applies nothing" charter can't carry — so it's its own class
  (`ApplyDirtyOnTargetTest`) with its own setUp, and the module
  docstring's excluded-rows note is updated to point at it.
- **Off-target case choreography**: the third subtest packs on main
  (fixing main as the stamped integration target), then branches to
  `side` and dirties it there. Assertions pin the checkout-free
  contract from both sides: `main`'s ref advanced (`git show
  main:hello.txt`), and the checkout stayed on `side` with the dirty
  edit byte-identical.
- **`make_applied_session` gained a `filename` parameter**
  (test-local, in `test_rollback_telemetry.py` — harness.py untouched
  per the constraint). The `--list` test needs two applied sessions in
  one repo whose reverts don't collide; a parameter with the old
  default keeps every existing call byte-equivalent. A sibling
  `make_applied_plain_commit` fixture fabricates the non-merge tag.
- **Plain-commit proof shape**: `git revert -m 1` on a plain commit is
  a git error, so a clean rollback exit is itself proof the detection
  took the non-merge branch; the test additionally asserts the log's
  "plain commit" line and that the amended subject recovered the
  summary from the commit's own subject (no second parent to read).
- **Exit-2 pin scope**: the pinned behavior is TARBALL.md §7.5's third
  code riding the HOLD path with the exit code preserved verbatim in
  the walkthrough row (`exit=2`) and the telemetry attempt — the two
  places "script errored" stays distinguishable from "check failed"
  after the fact. The fixture is built inline with its own
  validation_sh rather than through the local `build_response_tarball`
  helper, whose FAIL/PASS verdict-line logic encodes exit-1 semantics.
- **`unlock --integration` unparseable-lock variant**: included beyond
  the bare clear path because the rows-only degrade (no `[UNLOCK]`
  headline when the file yields no sid) is a deliberate carve-out in
  the implementation — clearing unreadable debris is the command's
  reason to exist — and a regression here would crash exactly when the
  command is most needed.

## Covered / excluded census (session 1's precedent)

Covered this session:

- rollback `--list`: empty message; applied / reverted / re-applied
  statuses; most-recent-first (topological) ordering; count line; the
  `--list`+sid contradiction refusal.
- rollback plain-commit branch: clean revert without `-m 1`; summary
  from the commit's own subject; `reverted/<sid>` tag; telemetry
  rolled-back.
- `unlock --integration`: held → cleared with holder named, lock file
  removed, `[UNLOCK]` headline, live-apply caveat; not-held benign
  no-op (exit 0); unparseable lock → cleared, "holder unknown,"
  rows-only.
- validation.sh exit 2: HOLD, apply exit 1, `exit=2` in the summary
  row, telemetry `validation.exit_code: 2` / state HOLD / outcome
  held, session open, held branch present, origin untouched.
- §11 row 8: on-target + tracked dirt refuses (loud, names 'main' and
  the dirty path, nothing applied, session open); on-target +
  untracked-only proceeds to merge with the stray file untouched and
  the checkout fast-forwarded; off-target + tracked dirt proceeds with
  the checkout never touched.

Deliberately not covered:

- Row-32: already pinned in the shipped tree (headline above).
- rollback `--list` ordering under rebase/tag-date ties: the
  implementation's topological ordering is pinned via two sessions'
  relative position; fabricating tie-breaking histories felt like
  testing git more than bale.
- `--undo` on a plain-commit rollback: the undo path is
  shape-identical regardless of the original commit's parentage (a
  revert commit is never a merge) and is already pinned by the
  existing toggle tests.
- Row 21 (declared untracked inputs) stays queued per the brief.

## Runtime

Full suite after the additions: 300 tests, ~101s wall in this
environment (baseline was 295 at ~101s — the five new methods cost
about 3s; the wall barely moved). Session 1's environment ran the
baseline at ~80s, so the §7.6 two-minute target has comfortable
margin; no `--slow` gating added. This response's own validation.sh
(syntax + only the four modified suites) runs ~22s.
