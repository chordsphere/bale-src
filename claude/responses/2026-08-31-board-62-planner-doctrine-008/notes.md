# notes.md — 2026-08-31-board-62-planner-doctrine-008

Both VERBATIM sentences landed byte-exact modulo the file's ≤72-col
hard wrap; validation asserts each whitespace-normalized. The two
placement calls the brief left to me:

- **Addition 1** went in as its own §2 bullet rather than folded into
  an existing close, with the bold lead "Concurrent splits forecast
  narrowly." — every §2 bullet carries a bold lead, and the forecast
  rule is a distinct practice (concurrency mechanics), not a
  corollary of the smaller-sessions default. It sits directly after
  that default's bullet, since the split the default produces is what
  makes sessions concurrent in the first place.
- **Addition 2** went to §4's delivery-practice bullet
  ("Version-suffixed filenames; publish the hash; compare the echo."),
  appended after "One file, one identity, verified at both ends." —
  the brief's named natural neighborhood. It reads as the bundled
  generalization of the single-file delivery practice above it, and
  needed no connective clause at all. The one pre-existing line that
  shows as modified in the diff is that bullet's former closing line
  gaining the appended sentence's first words; its own tokens are
  unchanged.

Self-containment: my connective prose adds no board numbers,
evidence citations, project-local doc names, or sitting labels; the
guard suite confirms on the shipped bytes.

One caveat on the `claims` basis: all three are marked `observed`,
but the runs happened against a repo tree reconstructed from the
request's `context/` (docs/, tests/, tools/ at their repo-relative
paths) — the same bytes, not the desk's working tree. If the real
tree diverges from the shipped context in ways the suites read,
staging will say so; the desk-verified-green-at-base note in the
brief makes that unlikely.

No out-of-forecast paths: the change set is exactly
`docs/PLANNER.md`. No deferred work.
