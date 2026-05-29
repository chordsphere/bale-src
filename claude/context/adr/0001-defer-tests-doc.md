# ADR-0001: Defer the standalone TESTS.md; house testing doctrine in CODE.md until promotion

- **Status:** Accepted
- **Date:** 2026-05-29
- **Supersedes:** —
- **Superseded by:** —

## Context

bale-src has reached the point where testing is a real, named topic: the
v0.4 selftest phase is on the build map (BALE.md §13), every v0.1–v0.3
session has been shipping a `notes.md` deferral ("tests deferred to v0.4,
harness lands there"), and the meta-session properties that make bale hard
to test (the one-apply-behind fixed-point, `bin/bale` as both tool and
artifact) are now written down. There is doctrine worth capturing *before*
the first test is written.

The question this ADR answers is **where that doctrine lives**, not what it
says. Two shapes were on the table:

- **(a)** A new standalone global workflow doc, `TESTS.md` — a fifth
  peer to `CLAUDE.md`, `TARBALL.md`, `DOCS.md`, `CODE.md`, injected into
  every request.
- **(b)** A section inside an existing global doc, with promotion to a
  standalone file deferred until it earns the split.

DOCS.md §4.1 (introduce a category when the threshold is crossed), §4.2
(a new file is right only when the content has distinct readers / a
distinct lifecycle / would bury its host), §6.1 (split signals), and §11
(*"write it as a section first; whether it deserves its own file can wait
until it's been read a few times"*) all point the same direction: testing
doctrine has not yet accumulated enough distinct-reader content to justify
a standalone doc. There is no harness, no fixture API, no selftest-authoring
guide to document — only philosophy, which shares readers with the
code-layout philosophy already in CODE.md.

There is also a cost asymmetric to bale specifically: `TESTS.md` as a global
doc means bale injects *five* docs instead of four, which is a change to
`GLOBAL_DOCS` and the pack-time injection in `bin/bale` — a code change, a
separate session, and a one-apply-behind risk surface. Creating the doc
prematurely pays that cost before the content justifies it.

## Decision

Do **not** create a standalone `TESTS.md` now. House testing doctrine as a
provisional section of CODE.md (§13, "Testing"), covering the layout half
of the *tests-ship-with-code* value, and defer the standalone doc until a
named promotion trigger fires.

**Promotion trigger:** promote §13 to a standalone global `TESTS.md` when
the section crosses DOCS.md §6.1's split signals — when it covers multiple
distinct topics that don't share readers (testing *philosophy* +
*harness mechanics* + *reference*), such that a CODE.md reader there for
code layout scrolls past testing machinery. In practice that threshold is
reached when the v0.4 selftest *harness* lands and its mechanics (how to
author a selftest, the sandbox and fixture-factory API) need documenting:
at that point the doctrine has a distinct reader (someone writing tests)
and a distinct lifecycle (it tracks the harness, not code-layout
philosophy).

The promotion is a documentation split (DOCS.md §6.2) **plus** the
`bin/bale` injection change (`GLOBAL_DOCS` gains `TESTS.md`, pack injects
five docs), done in one dedicated session.

The per-project testing *strategy* choices — oracle, dogfood depth,
fixtures, hermeticity — are out of this ADR's scope; they are captured
separately in ADRs 0002–0005 (Status: Proposed) for ratification.

## Consequences

- CODE.md §13 is the single home for testing doctrine until promotion.
  A session adding testing doctrine adds it there; INDEX.md does not get a
  testing-doc entry yet (there is no testing doc — the global docs aren't
  listed in INDEX.md anyway, per DOCS.md §2.2).
- The promotion trigger is observable, not a vibe: "the v0.4 harness landed
  and its mechanics need a home" is a concrete event a future session can
  recognize. Until then, the answer to *"should TESTS.md exist?"* is no.
- Promotion is now a known, scoped future session with a named extra cost
  (the `GLOBAL_DOCS` / injection change). It will not be a surprise.
- §13 is placed last in CODE.md (after the Meta-Principle) specifically so
  the future lift-out renumbers nothing — the extraction is a pure cut.
- This ADR decides *housing and deferral only*. If the architect later
  wants TESTS.md created early (as INDEX.md itself was, on an architect's
  call), that is a new decision and a superseding ADR, not a reinterpretation
  of this one.

## Notes

This mirrors the project's own precedent for introducing structure ahead of
strict need only when the architect calls for it (INDEX.md was introduced
early, by the architect, so the scaffolding was in place). Here the call
goes the other way: the scaffolding (the growth *path*) is put in place, but
the file itself waits for the trigger. The path is scaffolded; the doc is
deferred.
