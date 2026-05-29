# ADR-0004: Test fixtures — programmatic factories from the documented format

- **Status:** Proposed
- **Date:** 2026-05-29
- **Supersedes:** —
- **Superseded by:** —

## Context

The selftest needs inputs: temp git repos, request and response tarballs,
manifests, `bale.toml` files, `.baleignore` files. "Fixtures" is how those
inputs are created and kept current. Three approaches were considered:

- **(a) Checked-in golden fixtures.** Store sample tarballs / repos /
  manifests as files in the repo.
- **(b) Programmatic factories.** Build fixtures at test time in temp dirs
  via helpers — `make_repo()`, `make_request_tarball(goal, files=...)`,
  `make_response(changes=...)`, `make_manifest(...)`.
- **(c) Recorded fixtures.** Capture real request/response tarballs from
  actual bale-src sessions and replay them.

The deciding pressure is that the wire format is still at v0.x and changes
session to session. A checked-in fixture (a) drifts silently from the format
the code now produces, and a fixture that must be regenerated on every
format tweak is friction that rots. A factory (b) that constructs inputs to
the *documented* format stays in lockstep with intent and regenerates for
free on each run.

## Decision (proposed — for ratification)

Use **(b) programmatic factories as the primary fixture mechanism.** Tests
build their inputs in temp dirs through a small factory layer.

Crucially, the factories are built from the **documented wire format**
(TARBALL.md §3.1 / §5.1) and the schema files under `schemas/`, **not** by
calling bale's own pack/response code. This keeps the factory an
*independent second implementation* of the format on the paths where that
independence matters — a producer test whose fixture was built by the
producer proves only that the code agrees with itself. (Where a test's
subject genuinely *is* "bale produces a well-formed tarball," it drives the
real `bale pack` and asserts on the output per ADR-0002; that is a producer
test, not a fixture.)

Keep a **narrow set of (a) checked-in fixtures** only for inputs whose whole
point is to *not* track the current code: a deliberately-malformed manifest,
an old-format tarball for backward-compat / rejection tests, a known-bad
`apply.sh`. These are pinned artifacts where drift would defeat the test.

**Reject (c) recorded fixtures as a maintained tier** — they bloat the repo
and carry session-specific noise. A one-off capture from a real session is
fine as *raw material* when authoring a factory, but the captured file is
not committed as a fixture.

## Consequences

- Fixtures regenerate every run, so they never drift from the documented
  format; a format change surfaces as a factory update in one place.
- The factory layer is shared infrastructure with the sandbox harness
  (ADR-0005) — `make_repo()` produces the temp git repo the sandbox isolates,
  and the git/lock-state assertion helpers (ADR-0002) read what the factories
  set up.
- Risk to flag for ratification: a factory can share a bug with the code and
  pass spuriously. The mitigation — build factories from the docs/schema,
  independently of bale's own construction code — only holds if that
  discipline is kept; a factory that quietly starts calling `cmd_pack` to
  build a request tarball has silently become approach (c)-via-(b) and loses
  the independence. This is a review-time policy, not mechanically enforced.
- The pinned (a) fixtures need a comment stating *why* each is frozen, so a
  later session doesn't "helpfully" regenerate them and erase the point.

## Notes

The factory-first stance matches the repo's broader "stay in lockstep with
the current surface" instinct — the same reason the config wizard owns the
single discoverable surface for configurables (bale-internals.md §2.5). A
fixture corpus that has to be hand-maintained against an evolving format is
the testing analogue of a parallel command registry: duplicated bookkeeping
that drifts.
