# notes.md — 2026-09-14-tarball-s34-bundle-clauses-004

Both clauses landed in `docs/TARBALL.md` §3.4; nothing else in the
file moved. The diff is six added lines and two rewrapped ones, all
inside the two named paragraphs. No edit under `tests/`, no VERSION
bump.

## Decisions to ratify

- **Clause 1 wording.** The brief left the sentence to me. I wrote:
  *"Each child's command is delivered as one crafter bundle emitted
  beside its `bale open` line (`PLANNER.md` §2)."* — "delivered"
  deliberately echoes "delivers" in the pinned sentence so the
  operator's delivery and the bundle form read as the same act, and
  "crafter bundle … emitted beside its `bale open` line" mirrors the
  phrasing CLAUDE.md §11.2 and §4 already use, so the pair reads
  parallel from both ends. The pinned sentence's bytes, including its
  terminal period and its line wrap, are untouched.
- **The pointer sits on one physical line.** `test_doc_crossrefs.py`
  scans line by line, so a `PLANNER.md` / `§2` split across a wrap
  would silently escape resolution rather than fail. I wrapped the
  sentence so `(`PLANNER.md` §2).` is one line, and `validation.sh`
  asserts that stays true.
- **Clause 2 placement.** The transported parenthetical goes directly
  after "its full pack invocation" and before ", so the operator
  saves one file". That pushed the tail of the same sentence over
  the wrap, so two lines of that one sentence rewrapped — same
  paragraph, same sentence, no words changed beyond the insertion.
- **`validation.sh` runs the three shipped suites in staging.** The
  brief says they ship to run; each is its own `validation_will_run`
  entry so a pin break would surface as its own row. Claims are
  annotated `observed`: I ran the script against a staging-shaped
  copy of the shipped tree (docs/, tests/, tools/, schemas/, bin/)
  with the edited doc and all checks passed; I also confirmed the
  session assertion fails on the unedited doc, so it is not
  tautological.

## Where to look on review

The two hunks at `docs/TARBALL.md` lines ~1449 and ~1456. The
"Checkpoint-configured projects" paragraph now ends one sentence
later; the "Planner bundles are oracle-bearing" paragraph's first
sentence is longer by the parenthetical.

## Proposals

- **What:** add the new pair sentence to the sanctioned-pair pins —
  CLAUDE.md §11.2's "delivers that command bundled — as the stored
  pack argv of a crafter bundle emitted beside its `bale open` line"
  paired with the new TARBALL.md §3.4 sentence.
- **Why:** the pair contract (DOCS.md §9) is that twins change
  together, and the pin suite is the mechanical half of that. The
  bundle sentence is now stated from both ends but pinned from
  neither, so a future edit to either side would not trip anything.
  No existing pin needs to move — this is an addition.
- **Scope hints:** `tests/test_sanctioned_pairs.py` only; it sits
  under board 78's open forecast, so only after that session closes.
