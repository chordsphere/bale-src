# notes.md — 2026-09-14-apply-side-81-87-010 (re-attempt)

`corrects` names the first attempt, held at commit b1dc247: its
`validation.sh` ran `bash -n apply.sh validation.sh` inside staging,
where neither script exists (bale runs them from the response
directory and syntax-checks both itself). My rehearsal had copied the
two scripts into the staging-shaped copy, which masked it. The check is
removed — it was redundant with bale's pre-flight — and the rehearsal
now runs `validation.sh` from outside the tree. The blind checkpoint
and every other check agreed on the first attempt; the change set is
byte-identical.

One-apply-behind, as before: the apply that lands this tarball runs
the 0.4.28 apply code one last time. In particular, with your master
session open beside this one, *this* tarball still has to be applied
by name — bare `bale apply` works from the next apply on.

Every `changes[]` path is inside the write forecast. No out-of-forecast
work. `bin/bale` untouched.

## Row 87 — what the resolver does now

`resolve_bare_apply_tarball` treats the open set as the match surface:
a candidate is any `*.tar.gz` (cwd, then each `apply.search_paths`
directory, non-recursive, content-discriminated exactly as board 51
built it) whose `responds_to` names *any* open sid. Newest by
`st_mtime_ns` across the whole set wins; an exact tie still refuses.
The multi-open refusal is gone and its text does not survive
(`validation.sh` greps for it).

Two things widened rather than changed:

- **The tie listing names each path's session.** With every open
  session on the surface, tied paths can answer different sessions;
  `    <path>  (answers <sid>)` is what lets you pick by intent. The
  no-secondary-tie-break decision stands — I did not touch it.
- **The echo says which session, and which were open.** Single-open
  reads byte-for-byte as before (`responds_to: <sid> (the open
  session)`); multi-open reads `(one of N open sessions: a, b)`. The
  no-candidate refusal likewise says `open session <sid>` when one is
  open and `any open session (N open: a, b)` otherwise. The y/N was
  already `Apply this tarball against session <sid>?` — unchanged.

Downstream needed nothing: `cmd_apply`'s multi-open branch already
re-peeks the tarball's `responds_to` to pick the locked sid and the
session log, which is the same fact the scan matched on.

The read-only-session case is deliberately not special-cased, per the
brief: a response answering the master resolves, echoes, and hits the
step-14 drift gate exactly as the argumented form would.

## Row 81 — calls I made (ratify or correct)

- **`remedy` is a required argument on both renderers**, not
  optional-with-template-fallback the way `format_scope_drift_refusal`
  kept it at board 78. "The two template closings must not survive"
  reads as *gone*, and both call sites always have the tarball name.
  The renderer unit tests pin `TypeError` on omission.
- **On the offered flag, every typed value is carried — no-effect ones
  included — then the refused values are appended.** That is the
  brief's wording verbatim ("every admission flag already typed
  carried, the new flag's values appended one per path or name"). It
  differs from board 78's drift line, which composes from
  `drift_paths` and so drops a typed path that was not drifting. The
  difference only shows when the operator typed a flag that had no
  effect; if you want parity with the drift line, it is one
  expression at each site (`base_drift_overridden + base_refused`
  instead of `base_accept_norm + base_refused`, and likewise for
  names).
- **Typed base-drift paths ride the line in normalized form**
  (`scope_path`: `./src/a.txt` → `src/a.txt`), the same call board 78
  made and flagged for the drift line; pinned by a test. Required-check
  names are exact strings and carry verbatim.
- **Drift admissions ride as the gate resolved them** (`overridden_paths`
  — typed and prompt-admitted alike), the shape the sandbox remedy took
  at board 78, so a path admitted at the y/N is on the pasted line
  rather than re-asked. The sibling flag not being offered rides as
  typed (`accept_base_drift` / `allow_missing_required_check` raw),
  matching the two existing compose sites.
- **No prompt at either gate**, and pinned that way under a pty with
  `y` queued: the refusal lands, `overrides` is `[]`, no `[y/N]` in the
  output. The §3 watch's re-trigger is not fired.

## Test structure worth a look

- The **round-trip tests** (one per gate, `@slow`) paste the refusal's
  own line back: `shlex.split`, run from the project with the
  tarball's directory on `apply.search_paths` so the bare filename
  re-resolves — which is exactly the claim `compose_admission_command`'s
  docstring makes for naming by filename. The first shape I wrote
  ran from the tarball's directory instead and fell over on "not in a
  git repo"; the search-path shape is the one that matches how the
  line is actually used.
- `composed_line()` (a helper on each suite's base) asserts *exactly
  one* stripped line begins with `bale ` — a remedy split across
  lines, or printed twice, fails the same way.
- The multi-open resolution test packs the master with `--read-only`
  and the worker with `--write hello.txt`, the desk's own shape, and
  asserts the master stays open after the worker's response merges.

## Claims

- `session assertions` — **observed**.
- `unittest: touched suites` — **observed**: 13 + 22 + 22 tests, slow
  cases included, green here.
- `unittest: full discovery (--slow)` — **predicted**: the 134 shipped
  tests ran green here with `BALE_TEST_SLOW=1` (39 s), but the repo has
  more suites than the request shipped. Anything unshipped that pins
  the two old template strings, the "ambiguous with more than one
  session open" refusal, or the `(the open session)` echo under a
  two-open fixture will fail, and the fix is the assertion.
- `validate.sh (install sanity)` — **predicted**: 88/89 here; the one
  failure is "README.md present" (not shipped), as at board 78.

`validation.sh` rehearsed in a staging-shaped copy (originals overlaid
with `files/`, `apply.sh` run, manifest placed); `--slow` tier included.

## Surprises

- Nothing shipped pinned the two template remedies, so the only
  existing assertion that had to move was board 51's two-open refusal.
- The compose site for the required-check gate sits *before* the
  base-drift gate in the pipeline (steps 15 vs 17), so its line carries
  `--accept-base-drift` only as typed, never as resolved — there is
  nothing resolved yet at that point. Correct, just worth knowing when
  reading a composed line that has both.

## Proposals

- **What:** BALE.md's apply section still describes bare `bale apply`
  as keyed on the single open session and refusing under multi-open
  (board 51's Proposals queued that line). **Why:** the doc lane
  landed the naming half this sitting; the behavior half changed here.
  **Scope hints:** BALE.md only; after this lands.
- **What:** `bin/bale`'s `bale apply` help text for the bare form still
  says it resolves against "the single open session". **Why:** row 83
  owns `bin/bale`; this is the one-string edit that should ride it (out
  of scope here by the request's own list). **Scope hints:** `bin/bale`
  apply parser description; row 83's session.
- **What:** parity decision on the offered flag's no-effect values
  (see the second call above) — one rule for all three composed lines.
  **Why:** today the drift line drops a no-effect typed path and the two
  new lines keep one; harmless, but a reader comparing faces will ask.
  **Scope hints:** three expressions in `bin/bale_apply.py`; trivial.
