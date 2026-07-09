# ADR-0008: Checkout-free integration — merge without touching the user's working tree

- **Status:** Accepted (implemented in bale v0.3.5, session
  2026-07-09-checkout-free-mechanism-001)
- **Date:** 2026-07-06
- **Supersedes:** —
- **Superseded by:** —

## Context

Third of the four concurrency ADRs (see ADR-0006's Context for the
motivating goal).

`bale apply` currently integrates *through* the user's checkout: it
requires a clean working tree (BALE.md §8.1 step 5, §11 row 8), checks
out `bale/<sid>`, copies each manifest entry into the working tree and
commits, checks out the origin branch, merges `--no-ff`, and tags
(§8.5–§8.8). Two consequences follow. Applies cannot overlap even in
their non-git phases, because each owns the working tree for its
duration. And the user cannot touch the repo while any apply runs — the
working tree is hostage to the pipeline, and the clean-tree requirement
means even an unrelated scratch edit blocks integration.

## Decision (proposed — for ratification)

Integrate **without touching the user's checkout**: build and merge the
session branch via a temporary git worktree or plumbing (`commit-tree` +
`update-ref`), under the integration lock from ADR-0006. Integration
stays serialized — it is seconds of git work, and ADR-0006 deliberately
keeps one integration at a time — it just stops holding the user's
working tree hostage while it runs. Revert and retry semantics are
preserved: the same session states remain reachable and the same
commands resolve them.

**Timing (architect-approved):** separable from ADRs 0006–0007. It also
improves single-session life on its own — the clean-tree requirement for
integration goes away — so it may run in-sequence with the concurrency
work or be parked until concurrency is actually enabled. The
implementing-order call is the architect's at ratification.

## Consequences

- The clean-tree pre-flight (§11 row 8) stops being a mechanical
  requirement of integration. What replaces it is narrower: a rule for
  the one genuinely entangled case, below.
- **The checked-out-target case needs an explicit answer at
  implementation.** Moving the origin branch's ref while that branch is
  checked out with local modifications would desynchronize the user's
  working tree from its own branch (git would report the inverse diff as
  local changes). The decision constrains the answer — the user's
  checkout is not consumed by the pipeline — but does not pick between
  the candidates (fast-forward the checkout when the tree is clean; hold
  the ref-update or warn-and-instruct when dirty). This is the sharpest
  open edge of the ADR and is flagged for the implementing session, not
  silently resolved here.
- **The HOLD inspection surface moves.** Today's HOLD path checks out
  `bale/<sid>` with staged, uncommitted changes for inspection in the
  user's working tree (§8.6). Checkout-free integration relocates
  inspection to surfaces the pipeline owns — the staging copy and/or the
  temporary worktree — with the walkthrough naming where to look.
  `bale revert <sid>` keeps its job (discard the held session) with less
  to undo, since the user's checkout was never switched.
- git refuses to check out a branch that is already checked out in
  another worktree, which is a constraint on the temp-worktree variant
  when the target branch is the user's current branch — one more input to
  the implementation choice between worktree and plumbing.
- One-apply-behind (meta-sessions §2): this rewires the apply pipeline's
  terminal steps, so the session landing it integrates *itself* through
  the old checkout-consuming path, and the first checkout-free
  integration is its successor's.

## Notes

The staging copy (§8.3) already isolates validation from the working
tree; this ADR extends the same isolation to the commit/merge phase,
which is the last place the pipeline still borrows the user's checkout.
Out of scope: any change to what integration *produces* — the branch,
the `--no-ff` merge, the `applied/<sid>` tag, and the rollback story
over them (§9) are all unchanged; only the mechanism that produces them
moves off the checkout.

## Landing note (2026-07-09, appended at acceptance)

Implemented in bale v0.3.5 (session
2026-07-09-checkout-free-mechanism-001) with both open edges resolved
by architect ratification: the checked-out-target case takes the
narrow rule (refuse tracked-dirty-on-target at pre-flight;
fast-forward a clean on-target checkout at merge; never touch any
other checkout state), and HOLD commits to `bale/<sid>` — inspection
identical in UX to PASS inspection, `bale revert` unchanged with less
to undo. Mechanism as implemented: the session commit is built in a
temporary index (`GIT_INDEX_FILE` + read-tree/hash-object/
update-index/write-tree/commit-tree) rather than a temp worktree, and
the merge is a two-parent `commit-tree` advanced by compare-and-swap
`update-ref` (or `merge --ff-only` through the clean on-target
checkout) — plumbing throughout, for the uniform failure story: a
refused advance leaves refs unmoved, the checkout untouched, and the
session recoverable. One consequence the implementation forced into
the open: the merge target is now fixed per session (`origin_branch`
stamped at pack, current-branch fallback for pre-stamp sessions),
since "the branch checked out at apply time" stops being well-defined
once applies run from arbitrary checkouts. Walkthrough/inspection
polish and the full docs sweep are the ratified follow-up session's.
