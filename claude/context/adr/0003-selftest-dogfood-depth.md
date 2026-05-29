# ADR-0003: Selftest dogfood depth — two tiers, no recursion into the real install

- **Status:** Proposed
- **Date:** 2026-05-29
- **Supersedes:** —
- **Superseded by:** —

## Context

bale is meta code (CODE.md §8): it is its own primary artifact, and a change
takes effect one apply later (§8.1, meta-sessions §2). "Dogfood depth" is
how much the selftest exercises bale *through its own surface* versus by
calling internal functions directly. Three depths were considered:

- **(a) Shallow / unit.** Import functions from `bin/bale` and the sibling
  modules (`bale_config`, `bale_validate`, `bale_staging`, `bale_rollback`)
  and test them in isolation with constructed inputs.
- **(b) Deep / CLI end-to-end.** Drive `bale pack`, `bale apply`,
  `bale rollback`, etc. as subprocesses against ephemeral temp git repos —
  what BALE.md §13 v0.4 describes ("spin up a temp git repo; pack, apply,
  validate, rollback through every code path; held states; conflicts; stale
  locks; reverts; re-apply").
- **(c) Full recursion.** Use bale to pack/apply the selftest's own changes,
  firing `post_apply_pass` and re-entering the reinstall loop inside tests.

The hazards are specific to bale. The one-apply-behind property means a deep
E2E test that invokes the *installed* `bale` on `$PATH` would exercise *last
session's* code, not the working tree under test. And full recursion (c)
would fire the reinstall hook, whose job is to overwrite the developer's
real bale install — a test doing that is a footgun, not coverage.

## Decision (proposed — for ratification)

Adopt **two tiers**, and explicitly reject the third:

1. **Unit tier (from (a)) — broad and fast.** Cover the pure, well-bounded
   helpers directly: `sha256_*`, slug validation, `BaleignoreMatcher`, the
   `bale_validate` schema walkers and manifest validators, `merged_config`
   layering, session-id allocation. These are deterministic and have no
   environment coupling; they are the cheap base of the pyramid.

2. **E2E tier (from (b)) — focused, on the v0.4 path list.** Drive the CLI as
   subprocesses against ephemeral temp git repos, covering the full
   pack → apply → validate → rollback arc plus held states, conflicts, stale
   locks, reverts, and re-apply. **The E2E tier invokes `bin/bale` from the
   working tree by absolute path, never the `bale` on `$PATH`** — this is the
   direct application of the hot-swap guidance in BALE.md §12.1 and is what
   makes the tier test *this* code rather than the installed code.

3. **Reject (c) full recursion in the harness.** No test fires
   `post_apply_pass` against a real install. The reinstall recursion is
   covered operationally by the reinstall loop (meta-sessions §4); it does
   not need to be re-entered inside tests, and doing so risks clobbering the
   developer's bale. Where a test must exercise the hook contract itself, it
   points `post_apply_pass` at a temp no-op script inside the sandbox
   (ties to ADR-0005).

## Consequences

- The unit tier gives fast feedback on the logic most amenable to it; the
  E2E tier gives confidence on exactly the integration paths the
  one-apply-behind property makes most dangerous (apply/pack/staging).
- Subprocess E2E is slower than unit tests. Per TARBALL.md §7.6 (target
  under 2 minutes) the slow E2E paths gate behind `--slow`, so the default
  run stays fast and the full arc runs on demand / in CI.
- "Invoke `bin/bale` by absolute path" must be a harness invariant, not a
  per-test choice — a single runner helper that resolves the working-tree
  `bin/bale` and refuses to fall back to `$PATH`.
- The two-tier split is itself a §13.2 layout boundary: fast unit checks and
  slow E2E paths are distinct sub-clusters that don't share readers, and will
  likely live in separate test files from the start.

## Notes

This is the dogfood-depth answer shaped by meta code that CODE.md §13.5
anticipates: an ordinary library would not need the "by absolute path,
never `$PATH`" invariant, and would have no reinstall-recursion footgun to
rule out. Coupled tightly with ADR-0005 (the sandbox that makes the E2E
tier safe) and ADR-0004 (the factories that build its temp repos).
