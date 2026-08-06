# ADR-0002: Test oracle for bale — assert against observable contract state

- **Status:** Accepted
- **Date:** 2026-05-29
- **Supersedes:** —
- **Superseded by:** —

## Context

When the v0.4 selftest drives a bale operation, something has to decide
whether the result was correct. That decision procedure is the *oracle*.
bale's behavior is defined in BALE.md as a set of observable state
transitions — the §9.5 lock lifecycle, the §8.6 per-manifest-entry commit,
the §8.8 terminal actions (branch created at HEAD, `--no-ff` merge,
`applied/<sid>` tag, session dir wiped, lock cleared), and the §11
rejection conditions. Three oracle shapes were considered:

- **(a) Observable-state oracle.** Assert on exit code, the git state
  produced (HEAD, branches, tags, commit messages/count), the filesystem
  state (`.bale/` contents, staging cleaned, outbox), the lock state, and
  documented stdout/stderr markers. The source of truth is the contract
  in BALE.md, encoded as assertions.
- **(b) Golden-file oracle.** Compare produced artifacts (tarballs,
  manifests, trees) byte-for-byte against checked-in golden outputs.
- **(c) Self-oracle / differential.** Use bale's own validators
  (`bale_validate`) to judge bale's own output, and/or diff against a
  reference implementation.

## Decision (proposed — for ratification)

Use **(a) the observable-state oracle as primary.** Tests assert that a
bale operation produced the git/filesystem/lock state its contract
prescribes, reading the contract from BALE.md §§8–9 and §11.

Reserve **(b) golden comparison for a narrow set of structural artifacts**
only — e.g. the *shape* of a generated manifest or a generated `bale.toml`
header — and always with volatile fields (sha256, timestamps, absolute
paths, session ids) masked before comparison. Golden comparison is not the
default because the wire format is still evolving at v0.x and a broad golden
corpus turns every intended format tweak into a fixture-regeneration chore
that silently rots.

**Reject (c) as a primary oracle.** Judging bale's output with bale's own
`bale_validate` couples the test's notion of "correct" to the very code
under test: a bug in a validator would hide the matching bug in the
producer. `bale_validate` may be used only as a *secondary* cross-check,
never as the sole arbiter of a path's correctness.

## Consequences

- The oracle tracks the contract docs, so a deliberate contract change
  requires updating assertions — intended, since BALE.md is the spec.
- The harness needs a small assertion vocabulary for git state (tag exists,
  branch absent, commit subject matches `[bale <sid>] ...`, merge is
  `--no-ff`), lock state (`.bale/current_session` present/absent), and
  staging cleanliness. This vocabulary is shared infrastructure — it ties
  to the fixtures decision (ADR-0004).
- State assertions are robust to incidental output churn (log wording,
  ordering) in a way string-matching stdout is not; stdout markers are
  asserted only where they are part of the documented contract (e.g. the
  §8.8 final-line guidance).
- Couples cleanly with the deep-E2E tier (ADR-0003): the E2E tier is exactly
  what produces the observable state this oracle reads.

## Notes

bale is already *partially* self-validating operationally (meta-sessions
§3: a malformed `bin/bale` fails the next pack; reinstall runs
`install.sh && validate.sh`). That is a happy property, not an oracle —
this ADR is about the harness's deliberate checks, which should not lean on
the producer to grade itself.
2026-08-05: ratified at the board-10 tidy-up sitting (2026-08-05-discuss-harness-011), recognizing exercised practice.
