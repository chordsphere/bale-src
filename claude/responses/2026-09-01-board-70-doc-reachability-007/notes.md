# notes.md — 2026-09-01-board-70-doc-reachability-007

All five touched paths are inside the stamped forecast; nothing here
needs per-path admission. Flag-everything applies, so every latitude
call from the brief gets a line below.

## Per-site calls (W2 latitude, flagged per site as asked)

- **Site 2 (bundle passage):** re-pointed at
  `schemas/bundle-manifest.schema.json` (REQUIRED token) plus the
  request-carried crafter's `--bundle` mode and `bale open`'s
  gate-first validation — the worker-facing register: everything the
  passage defers to is now named as a shipped surface.
- **Site 3 (`--no-readme` row):** stated the deferred detail inline
  rather than re-pointing — one clause: unacknowledged omission
  warns-and-proceeds on a TTY, refuses when stdin is piped. I read
  the split out of `bin/bale_pack.py`'s guard itself (the
  `args._readme_body is None` block) rather than paraphrasing the
  brief, so the clause states shipped behavior, not recollection.
- **Site 4 (`--read-only` row):** dropped the deferral clause. The
  row already carries the operative contract at length (forecast
  semantics, sweep behavior, close-out); a re-point would have added
  a pointer with nothing behind it that the row doesn't already say.
  "Bare boolean." stays.
- **Site 5 (`--supersedes` row):** dropped the deferral clause, same
  reasoning — the row states the full worker-facing flow (decline
  default, piped behavior, sid resolution, the one sanctioned
  unsolicited-runnable site).
- **Site 1 (PLANNER.md) and site 6 (crafter docstring):** re-pointed
  per W1/W3 with both REQUIRED tokens; site 1 additionally points at
  CLAUDE.md META's new reachability paragraph rather than restating
  it (one home). Site 6's replacement no longer wraps into the deny
  shape and keeps the docstring's Sections index untouched — the
  crafter suite (122 tests) is green on the edited tool.

## Deviation for ratification: two out-of-inventory pointers fixed

The brief's ratified inventory is six sites under
`(bale )?tool's (own )?documentation`. My normalized sweep found two
more instances of the same disease that the pattern misses because
of one extra word: TARBALL.md §5.6.3 and §5.9.3 (the apply-time-UX
tombstones) read "Moved to the bale tool's own **design**
documentation" — a citation of a doc that ships with no install,
exactly what the manifest constraint bans ("never a doc that does
not ship"), in files the forecast already covers. I fixed both:
each tombstone now reads "Moved out of this contract, to be
maintained beside the bale implementation itself," which keeps the
DOCS.md §6.4 tombstone function (heading retained, relocation
named) without citing an unreachable doc. To pin the fix, the
guard's deny shape carries an optional `design` alternative beyond
the brief's spec ("both spellings, the optional 'own'"). Both edits
and the widened shape are this deviation; revert is a three-line
change if you'd rather hold the tombstones to the ratified six-site
scope. The goal's "re-point every documentation pointer" plus the
constraint is what tipped me to ship rather than only propose.

## Other latitude and judgment calls

- **No version bump.** W3 changes shipped-tool bytes
  (docstring-only, zero behavior change), and the cadence rules the
  brief defers to are project-local — not in this request's context
  — so I took the conservative call: no bump, `bin/VERSION`
  untouched, nothing shipped outside the forecast. If the cadence
  says docstring-byte changes bump, that's a one-line follow-up.
- **Crafter suite green, so no out-of-forecast test fix** was
  needed — the docstring pin hazard the brief warned about did not
  trip (the Sections index and banners are unchanged).
- **W4 wording:** the paragraph landed in META's "Global vs project
  docs," replacing (not duplicating) the old two-line
  self-containment sentence, and deliberately says "bale's own
  repo-local documentation" — not the pointer phrase — so the
  every-session read path doesn't itself match the deny shape. All
  new text says "carries/ships," never the i-word, per the
  vocabulary note; existing uses (including `INJECTED_TOOLS`) are
  untouched as directed.
- **Rider recorded:** the bin/-sanction rationale line sits in the
  guard's module docstring, stated self-standingly per the registry
  entry's text; the deny-shape paragraph around it carries the
  wrap-tolerance rationale and the wrapped-specimen story.
- **Deny scope:** the wrapped deny applies to the docs-and-tools
  group only. The schema group's table is "the purge's ratified
  seven," so I did not widen it unilaterally; the sweep shows zero
  pointer-class hits in the schemas today.
- **Negative run:** validation demonstrates both directions — the
  clean tree is green, and a planted instance wrapped across two
  physical lines (the site-6 shape) goes red in a scratch copy, with
  the failure naming the wrap-start line. The sweep check is a
  second, independent implementation of the scan so a guard bug
  can't self-certify.

## Proposals

- **What:** decide whether the pointer-class deny should join the
  schema group's table (or whether the two per-surface tables should
  converge on it) at the next sitting that touches the guard.
  **Why:** the class is currently a docs-and-tools disease — the
  schemas sweep clean — but the tables' per-surface split is
  ratified doctrine, and adding the shape schema-side without a
  sitting would have been the same unilateral widening I flagged
  above. **Scope hints:** tests/test_global_doc_selfcontainment.py
  only; no ordering dependency.
