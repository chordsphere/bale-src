# ADR-0014: New files are worker-determined; admit them at apply, never pre-include them

- **Status:** Accepted
- **Date:** 2026-07-23
- **Supersedes:** —
- **Superseded by:** —

## Context

Two things drifted apart after ADR-0007. That ADR (v0.3.1/v0.3.6)
mechanized *sibling*-scope enforcement and explicitly left own-scope
drift as "stay-in-the-lane policy, caught at review, unchanged."
Then v0.3.10 converted own-scope drift to a mechanical apply
pre-flight gate (BALE.md §8.1 step 14, §11 row 22) with a
per-invocation `--allow-out-of-scope <path>` override, extended to
`bale retry` in v0.3.14. The injected global docs never caught up:
`TARBALL.md` §3.2 still called own-scope drift "not a mechanical
check," and `BALE.md` §2.2 / §8.1 step 7 / the §11 postscript still
described it as review-only policy (with a pointer at "TARBALL.md
§8's stay-in-the-lane rule" — a rule that actually lives in
`CLAUDE.md` §6).

The observed failure mode, reported from a live worker session: a
0.3.13 apply refused own-scope drift citing BALE.md §11 row 22 — a
document the worker is deliberately never shown, since `BALE.md` is
bale-src project documentation, not an injected global (INDEX.md's
"Tool design" note). The worker had no way to read the rule that
fired, and the docs it *was* shown asserted the opposite of the
tool's behavior.

A second, compounding pattern: workers began compensating for the
gate by suggesting `--include` flags for files that did not exist
yet, so that planned new files would fall inside the declared
scope. The architect judges this backward — an include ships
existing context, and forecasting the response's file layout is the
worker's job during the session, not the packer's job before it.

## Decision

1. **`BALE.md` stays uninjected.** The fix for "the worker can't
   read the rule that fired" is not to ship the tool's design doc
   into every request; it is for the injected globals to describe
   the gates accurately and generically. (Direction stated by the
   architect directly in the request goal; Accepted at creation per
   the ADR-0012 precedent.)
2. **Includes name existing context only.** Neither party authors
   or suggests an `--include` for a path that does not yet exist.
   A packer who knows new work will land in one area widens the
   seam with a directory include (directory scope entries cover
   subtrees); nobody pre-names the files.
3. **New files are the worker's determination.** Deciding what
   files the goal requires happens inside the session. A new file
   under an included directory is in scope. A new file outside the
   declared scope is shipped anyway, declared in the manifest, and
   **enumerated in `notes.md`** with why it had to exist.
4. **Admission happens at apply, per path, per invocation.** The
   operator reads the enumeration and passes
   `--allow-out-of-scope <path>` (repeatable; retry parity as of
   v0.3.14) for each path they accept. There is deliberately no
   config key: an override never becomes standing policy, and every
   use is logged and stamped into the session's telemetry record.
5. **The lane rule splits by file existence.** `CLAUDE.md` §6's
   stay-in-the-lane rule now reads: modifications to existing
   out-of-scope files are still proposed in `notes.md`, never made;
   new-file creation is the sanctioned exception, landing through
   the enumeration-plus-admission path above.

## Consequences

- Doc updates landed with this ADR: `TARBALL.md` §3.2 (three gates,
  override, new-file landing path), §3.4 (the includes-name-
  existing-context rule), §5.4 (the enumeration bullet), §8 (scope
  gates added to the bale-enforced contract enumeration);
  `CLAUDE.md` §6 (the lane-rule split); `BALE.md` §2.2, §8.1 step 7,
  and the §11 postscript (stale policy-only language and the wrong
  stay-in-the-lane pointer fixed, prose `out_of_scope` disambiguated
  from mechanical own-scope path drift).
- ADR-0007 is not superseded: its disjointness gates stand
  untouched. Only its Consequences forecast that own-scope drift
  would "remain policy" was overtaken by v0.3.10; per DOCS.md §7.2
  the old ADR is left as written and this ADR records the
  evolution.
- Workers stop kicking new-file work back to the planner for a
  repack, and stop proposing includes for nonexistent paths.
  Refusals at the own-scope gate should now cluster only around
  *unenumerated* drift — which is the signal the gate exists to
  produce.
- The enumeration in `notes.md` becomes the audit surface: an
  admitted path with no enumeration entry is an operator-discipline
  smell worth flagging at review.

## Notes

The telemetry stamp of admitted paths (`overridden_paths`, BALE.md
§8.9) plus this doctrine gives the longitudinal view: if admissions
cluster around a packer or a work class, the seams are being drawn
too narrow — a scoping signal, not a worker-discipline one.
