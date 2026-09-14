# notes.md — 2026-09-14-doc-lane-87-88-009

Five edits, three files, all under `docs/`. The three doc-pin suites
stayed green without a line changed, so `changes[]` is exactly the
forecast and there is no drift to admit. Both VERBATIM passages
landed byte-exact (wrapped) and each has its own whitespace-normalized
self-check in `validation.sh`; I also ran the script against the
unedited docs to confirm those two checks actually fail there.

## Decisions to ratify

- **Where the §6 bullet sits.** Second, right after "One master per
  sitting" — the desk authors, then how it runs what it authored —
  rather than appended at the end. Move it if you read §6's order as
  chronological-by-birth.
- **The bold lead** is "Disjoint sessions run beside each other."
  Cheap to rename.
- **The lesson behind the second clause** ("includes gate nothing,
  and a suite ships with the modules it imports") is stated in the
  bullet, self-standingly: a desk narrowed a tests-only pack's reads
  to look disjoint and three of seven suites could not run. No board
  or session citation, per the self-containment guard. If you would
  rather the core carry only the rule and leave the anecdote to the
  desk, cut the two sentences after the VERBATIM one; the assertion
  still holds.
- **§2's rewrite** names both origins ("split-born or desk-born
  alike") so the generalization is visible rather than implied, and
  the bullet gains a one-clause pointer at §6 so the authoring form
  and the sitting practice cite each other. The bundle-ruling pin in
  `test_doc_crossrefs` (bundle bullet precedes the single-line
  bullet) is unaffected.
- **CLAUDE.md §4's row** restates the practice in one clause before
  the `PLANNER.md` §6 pointer. A bare pointer would have been shorter,
  but the row is in the every-read core and the worker never reads
  `PLANNER.md` unless authoring is the work — so the pointer alone
  would name a practice the worker never learns. The row is one
  physical line.
- **Edit 5's "in the same style."** I read it as: mirror step 11's
  spelling *and* its one-clause note (filename carries the sid, the
  directory stays `request-NNN/`), not a bare command swap. The clause
  says the filename is what `bale pack` emits, which the brief
  verified against `bin/bale`.

## Where to look at review

- `docs/PLANNER.md` §6, the new bullet — it is the longest of the
  five edits and the one carrying prose of my own.
- `docs/TARBALL.md` §10.1 step 11 — the wrapped continuation lines
  are indented four spaces to sit inside the numbered item.

## Not touched, on purpose

`TARBALL.md` §1's "Artifact directories" bullet and `DOCS.md` §8's
"Session artifacts" entry both speak of `request-NNN` / `response-NNN`
as *directory* names, which is still true — the directory is wire
format and did not change. The `bin/` remedy strings that spell
`<response-NNN.tar.gz>` ride the apply-side session.

## Proposals

- **What:** `TARBALL.md` §1's "Artifact directories" convention
  bullet could gain one clause naming the tarball filename convention
  beside the directory one, so the two names are stated together in
  the core rather than only at §3.1 and §10.1 step 11.
  **Why:** the row 87 operator report was about inconsistency; a
  worker reading only the core (sections 1, 2, 5, 7) still meets the
  filename rule only in the triggered §10 checklist. Low cost, and
  §1 is where the `NNN` convention already lives.
  **Scope hints:** `docs/TARBALL.md` only; no pin touches §1's text.
