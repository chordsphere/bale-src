# notes.md — 2026-08-07-board-35-apply-preflight-002

## The brief's row list vs BALE.md §11 (the verification you asked for)

The brief's gap-1 summary named six rows: sha256 mismatch, path
safety, artifact denial, empty reason, duplicate path, reconciliation
mismatch. Enumerating from §11 itself, as instructed, changed the
picture in both directions:

- **Five of the six map cleanly** to rows 12, 14, 20, 13, and 18.
- **"Duplicate path" is not a §11 reject row.** It is the worker-side
  lint's DUPLICATE_PATH check (TARBALL.md §10.1 step 4). I verified
  empirically: bale's apply pre-flight **accepts a manifest with two
  identical entries for the same path and applies it cleanly** — the
  presence, correspondence, and reconciliation checks all use sets or
  per-entry loops that an identical twin passes. A duplicate with
  *conflicting* hashes is caught incidentally by row 12 (the bytes can
  match at most one hash), and that case is pinned as a test. The
  identical-duplicate acceptance is deliberately *not* pinned — I
  didn't want a test asserting behavior that looks like a contract
  gap. See Proposals.
- **The malformed-tarball surface is wider than six.** The suite
  covers rows 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, and
  25 — one test method per row, several with subtest variants (e.g.
  row 14 covers traversal, `.git/`, `.bale/`, and a `.baleignore`
  match; row 16 covers each missing artifact by name). Rows 7 and 9
  weren't in the brief's list but are squarely "a tarball that cannot
  be trusted" (no open session; responds_to naming a ghost sid) and
  had no coverage, so they're in.

**Rows excluded, and why:** 8 (dirty-on-target — an environment-state
refusal, not tarball malformation; needs its own git choreography),
19/21/22 (sibling-scope collision, declared untracked inputs,
own-scope drift — session-topology and staging-config machinery; row
22's refusal and per-path override are already pinned in
test_readonly_pack.py), 26–29 (required checks and checkpoints — their
own suites: test_required_check_gate, test_blind_checkpoint,
test_checkpoint_provenance), and the pack/handoff-side rows (1–4, 23,
24, 27, 30), which are not apply's surface.

## Layout decisions

- **Two suite files, not one.** The goal says "with the
  real-operations apply.sh fixtures folded in", which I read as
  folded into *this session*, not into one file: the reject suite and
  the accept/operations suite are distinct sub-clusters with different
  readers (CODE.md §13.2 / §4.2), and a session debugging a refusal
  message shouldn't load merge-path fixtures. Fold them into one file
  if you disagree — the seam is clean either way.
- **Builder extracted to tests/harness.py; tamper helper stays in the
  reject suite.** The response-tarball builder gained its second and
  third consumers this session, which is exactly the board-11
  one-harness trigger (the same one that produced harness.py and
  run_bale_pty), so `build_response_dir`/`tar_response_dir` moved
  there and test_hold_retry_e2e.py now consumes them — its fixture
  semantics are unchanged, and the full suite stayed green across the
  refactor. The tamper helper is *not* genuinely shared (only the
  reject suite mutates fixtures), so it lives inside
  test_apply_preflight.py per the brief's either/or.
- **The reject-suite fixture session packs `--include .` on purpose.**
  A whole-tree scope makes the own-scope drift gate (row 22) vacuous,
  so a tampered path like `__pycache__/x.pyc` or `../escape.txt`
  reaches *its* row's check instead of being intercepted by the drift
  refusal — the pipeline runs the drift gate before path safety and
  the artifact denial. This ordering fact is worth knowing at review:
  with a narrow scope, several of these rows are unreachable in
  practice because row 22 fires first.

## Smaller findings

- A per-check `[FAIL]` verdict from validation.sh streams to the
  session log, not stdout — the forgotten-chmod test asserts the HOLD
  headline on stdout and the `[FAIL]` line in
  `.bale/logs/<sid>.log`, which is where a human is pointed anyway.
- The tamper helper writes the manifest back after the mutation
  callback, which would resurrect a deleted manifest.json; row 16
  builds its tarballs directly and the helper's docstring warns about
  the trap.
- Validation runtime: the full suite is ~80s in my environment (the
  20 new tests add ~8s; every test builds its own hermetic sandbox
  per ADR-0005). Under the §7.6 two-minute target, so no `--slow`
  gate.

## Cadence and one-apply-behind

Tests-only, as scoped: nothing outside tests/ is touched, no shipped
tool behavior changes, so the bump-exempt reading ratified at the
master desk holds. The one-apply-behind flag likewise does not
engage — no apply-path code was modified.

## Proposals

- **Decide the identical-duplicate-path question.** Either add a
  duplicate-path check to apply's pre-flight (a ~5-line set/Counter
  pass beside the other manifest checks in apply_pipeline, plus a §11
  row per the appended-row precedent), or explicitly ratify that
  duplicates are lint-territory only and bale tolerates them. Why:
  this session verified the identical-duplicate case applies cleanly
  today; TARBALL.md §5.2 calls a duplicated path invalid ("it makes
  the mirror correspondence ambiguous"), so prose and enforcement
  currently disagree. Scope hints: bin/bale_apply.py's manifest-check
  block, BALE.md §11, and one more test in test_apply_preflight.py
  once the decision lands.
- **Pin row 8 (narrow dirty-on-target) in a small follow-up.** Why:
  after this session it is the last apply pre-flight refusal with no
  live coverage at all, and its carve-outs (untracked never blocks;
  off-target branches never block) are exactly the kind of narrow
  contract a regression would silently widen. Scope hints: a
  three-case test in test_apply_preflight.py or its own small file;
  needs only git choreography in the existing sandbox, no new
  fixtures. Only worth doing as part of gaps 3–7 sequencing, not
  urgent.
- **Row 21 (declared untracked inputs) has no coverage either**, but
  it needs the target-base staging strategy configured; noting it for
  the gaps-3–7 queue rather than proposing a shape now.
