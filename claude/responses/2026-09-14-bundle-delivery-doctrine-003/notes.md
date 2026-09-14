# notes.md — 2026-09-14-bundle-delivery-doctrine-003

Six sentence-level edits across two files, no section added, nothing
renumbered. The ruling landed in `PLANNER.md` §2 word-for-word from
the brief (I diffed it whitespace-normalized against the README's
text, and `validation.sh` pins the wrapped bullet byte-exact per §2's
own verbatim-content rule). Both shipped suites pass on the staged
tree; the claims are marked `observed` because I ran them against a
copy laid out like the repo (`docs/`, `tests/`, `schemas/`, `tools/`).

## Where to look on review

- **`CLAUDE.md` §11.2 item 2.** This is the one place the touch and
  the ruling read differently on the surface. The ruling says *every
  project*; the sentence I added is gated on *a checkpoint-configured
  project*, exactly as the brief specified. I read the two as
  consistent rather than in tension: in a non-checkpoint project the
  offer's command is worker-emitted content the planner re-derives
  from (`TARBALL.md` §3.4) — not a planner-authored pack — and the
  bundle attaches when the planner authors from it; in a
  checkpoint-configured project the offering session *is* the planner
  (`PLANNER.md` §20) and so delivers bundled. If the desk wants
  §11.2 to say the offering session bundles in every project, that is
  a one-clause change to the sentence I added, but it would also
  widen `PLANNER.md` §20's checkpoint-configured framing — so I left
  it as the brief wrote it and flag it here.
- **`CLAUDE.md` §3 transition paragraph.** I kept `--readme-file` in
  the sentence as the named fallback ("only when the crafter is
  unreachable") rather than deleting it, so the ruling's fallback
  clause reaches the every-read core in one place. The sentence
  grew by two lines; it is still one sentence.
- **`PLANNER.md` §4.** The back-pointer is spliced into the existing
  "In a checkpoint-pinning project…" sentence ("the bundle §2 makes
  every pack's delivery form carries the checkpoint member too"),
  keeping the hash-publication and gate-first-validation detail as
  the checkpoint-specific tail. Read it once aloud; if the splice
  reads awkwardly I'd rather it be rephrased than restated.

## Sanctioned-pair note (DOCS.md §9)

`DOCS.md` §9 registers `CLAUDE.md` §11.2's rescope-offer prose and
`TARBALL.md` §3.4's pack-flag surface as a sanctioned parallel pair
whose sides change together "or the parallelism has become drift."
This session changed the §11.2 side and could not touch §3.4
(`docs/TARBALL.md` is doc-lane-74-76's). The parallelism is not
broken today — §3.4 already says the offering session authors the
children as sub-master and the operator delivers, never authors —
but §3.4 does not yet name the bundle as the form that delivery
takes. The first proposal below closes that gap; until it lands the
pair is one sentence apart, not contradictory.

## Proposals

**TARBALL.md §3.4 — name the bundle in the checkpoint-configured
paragraph.**
*What:* Extend the last sentence of the "Checkpoint-configured
projects" paragraph so "the offering session authors them as
sub-master (PLANNER.md carries the doctrine), and the operator
delivers, never authors" continues "— delivered as one crafter
bundle per child beside its `bale open` line (`PLANNER.md` §2)."
*Why:* Keeps the DOCS.md §9 sanctioned pair with `CLAUDE.md` §11.2
in step now that §11.2 names the bundled delivery; §3.4 is the
pack-flag end of the same command and currently stops at "delivers."
*Scope hints:* `docs/TARBALL.md` only; one clause; for
doc-lane-74-76's ratification.

**TARBALL.md §3.4 — make the bundle's checkpoint member optional in
the planner-bundle paragraph.**
*What:* In "Planner bundles are oracle-bearing and never ship,"
extend "packaging a session's brief, its blind checkpoint (§7), and
its full pack invocation" with "(the checkpoint member present when
the project pins a `[validation]` base, an explicit null otherwise)."
*Why:* The paragraph's worker-facing rules hold either way, but as
written it implies every bundle carries a checkpoint, which is the
pre-ruling picture; `PLANNER.md` §2 now says otherwise, and the
crafter's `--bundle` accepts `--checkpoint` absent. One clause
aligns the wire-format doc with the doctrine it carries.
*Scope hints:* `docs/TARBALL.md` only; same paragraph the first
proposal leaves alone; for doc-lane-74-76.

**tests/ — pin the ruling bullet durably.**
*What:* A stdlib-only assertion (in `test_doc_crossrefs.py`'s style)
that `docs/PLANNER.md` §2 contains the bold lead phrase "The bundle
is the delivery form of every planner-authored pack" before the
"Commands are single-line" bullet, and that `docs/CLAUDE.md`
mentions `bale open` at least once.
*Why:* This response's `validation.sh` carries the byte-exact check
for one apply; a later doc session that rewraps §2 or prunes the
bullet would pass both current suites, since neither reads prose
content. The operator's original report — "no project other than
bale-src has ever emitted a planner bundle" — was a docs-as-written
outcome; a durable pin is what stops it recurring silently.
*Scope hints:* `tests/` — board 78's forecast; only after that
session closes.
