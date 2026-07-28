# ADR-0005: Test hermeticity — fully sandboxed, hard rules on the dangerous surfaces

- **Status:** Accepted
- **Date:** 2026-05-29
- **Supersedes:** —
- **Superseded by:** —

## Context

bale reaches well outside the repo it operates on. It writes `.bale/`,
staging, and the outbox; it can write a repo-local *and* a global
(`<install>/user/bale.toml`) config; the `bale config init` wizard can run
`git config` (repo-local) and reads `git config --global`; the
`post_apply_pass` hook reinstalls bale into `$BALE_INSTALL` (default
`~/bale`); `open_in_editor` launches `$EDITOR`. No network. "Hermeticity"
is how far the suite is isolated from the developer's real environment.
Three levels were considered:

- **(a) Fully hermetic.** Temp `HOME`, temp git identity, temp
  `BALE_INSTALL`, temp cwd; hooks disabled or pointed at temp scripts;
  `$EDITOR` stubbed; nothing touches the developer's real `~/.gitconfig`,
  `~/bale`, or repos.
- **(b) Partially hermetic.** Temp repos and temp `.bale/`, but the real git
  binary with possibly-real global git config.
- **(c) An integration tier allowed to touch the real install.**

The sharpest hazard is the reinstall hook. A test that fires
`post_apply_pass` against a real `$BALE_INSTALL` would overwrite the
developer's working bale with whatever the test built — the single most
destructive thing the suite could do. The global-config write is the second:
a test that runs `bale config init --global` or any `git config --global`
against a real `HOME` mutates the developer's machine.

## Decision (proposed — for ratification)

Adopt **(a) fully hermetic as the default, and as a hard rule on the
dangerous surfaces.** Specifically, every test runs in a sandbox that:

- points **`HOME` at a temp dir**, so every `git config --global` read/write
  and the `<install>/user/bale.toml` global-config path resolve inside the
  sandbox, never the developer's real config;
- points **`BALE_INSTALL` at a temp dir**, so any reinstall-shaped operation
  lands in the sandbox;
- **never invokes `post_apply_pass` against a real install** — the hook is
  either unset for the test or wired to a temp no-op script inside the
  sandbox (this is the harness side of ADR-0003's "reject full recursion");
- **stubs `$EDITOR`** to a non-interactive script (write canned content,
  exit 0), so editor-driven paths run unattended;
- runs in a **temp repo** with a sandboxed git identity (the `make_repo()`
  factory, ADR-0004).

The **git binary itself is real** — it is a hard dependency, and stubbing it
would test a fiction. Only git's *config and state* are sandboxed (temp
`HOME` + temp repos). No network is required by bale, so a network guard is
cheap insurance worth adding, but it guards against accident, not against a
real dependency.

**Reject (c).** No test writes to the real install dir or the real global
config. There is no "integration tier touches my machine" exception.

## Consequences

- The suite is safe to run on a whim — it cannot mutate the developer's git
  config or clobber their bale install. This mirrors the wizard's idempotency
  ethos (bale-internals.md §4.5): tooling you can run without fear.
- The sandbox (temp `HOME` + `BALE_INSTALL` + repo + stub `$EDITOR`) is a
  per-test setup cost and shared infrastructure — it is the same layer the
  fixture factories live in (ADR-0004) and what the E2E tier (ADR-0003) runs
  inside. The three Proposed ADRs converge on one harness module.
- Sandboxing `HOME` is load-bearing, not cosmetic: without it the global-config
  and `git config --global` paths cannot be tested at all without risking the
  developer's machine. With it, they become ordinary tested paths.
- A test that needs the *real* `$PATH` bale (none should, per ADR-0003) would
  break the sandbox guarantee; the absolute-path-to-`bin/bale` invariant keeps
  that from arising.

## Notes

The hermeticity answer is sharp here precisely because bale is a tool that
operates on the developer's own environment — exactly the case CODE.md §13.5
flags as needing a stricter rule than a pure library. The clobber risk is not
hypothetical: the reinstall hook's entire purpose is to overwrite an install,
so "don't point it at the real one" is the difference between a safe suite and
a destructive one.
2026-07-25: ratified at the 2026-07-25 sitting; first suite landed under its rules the same day.
