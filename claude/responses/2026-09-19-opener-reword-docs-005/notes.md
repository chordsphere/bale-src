# Notes — 2026-09-19-opener-reword-docs-005

The doc half of the opener reword. Four forecast files, no drift, bumpless.

## Where the two VERBATIM rulings landed

DOC_ASK replaces the "Every turn … machine-recognizable shape" sentence and
its board-105 second half in both homes: `docs/CLAUDE.md` §3 and
`docs/TARBALL.md` §5.10. In §5.10 the §4.2 / §5.9 pointers moved to the
next sentence, as the brief allowed.

DOC_DELIVERABLE lands in `docs/CLAUDE.md` §3 and in `docs/TARBALL.md` §2.
The brief left the TARBALL.md home to me. I chose §2 over §5.10's opening
because §2 is where the exchanges and their directions are defined, and it
keeps §5.10 about asking. §2's exchange-table row for the response tarball
is re-scoped to match: once per worker session, none from a read-only pack.

Both rulings carry byte-exact, whitespace-collapsed pins in
`tests/test_doc_crossrefs.py`, each checked against its section body
alone. `validation.sh` carries its own independent byte-for-byte copies
and checks them the same way.

## The README and the `readme` key

- **`docs/CLAUDE.md`.** META's reading order and the INDEX "Every session"
  row name `README.md` third, as the session's brief. Both say the
  manifest's `readme` key is how a reader knows whether one ships. "The
  session prompt" is gone from all three places it appeared.
- **`docs/TARBALL.md` §3.2.** It documents the key exactly as the brief's
  Part 3 pins it:
  - `null` when no README ships;
  - otherwise an object with exactly `"path": "README.md"` and `"sha256"`;
  - top-level rather than under `provenance`;
  - additive and not required by the schema;
  - `bale handoff` stamps `null`.
- **`docs/TARBALL.md` §3.1.** It drops "Most sessions skip the README" and
  describes the README as the brief the opener names.

## Sweep for read-only sessions

I swept each place a reader could still conclude that a read-only session
owes a response tarball:

- `docs/TARBALL.md`: §3.4's `--read-only` row, the scope-planning
  paragraph, the INDEX row, and a line atop §10.1.
- `docs/PLANNER.md`: §2's bundle bullet (the pinned lead phrase is
  untouched) and §8's scopeless-orchestrator bullet.
- `docs/PLANNER.md` §1 and §3 now name the brief as the worker's third
  read.

## Please check

- **Brief delivery.** I aligned `docs/TARBALL.md` §3.1's description of
  how a worker-authored brief is delivered with `docs/CLAUDE.md` §3 and
  `docs/PLANNER.md` §2: as a bundle member first, and by `--readme-file`
  only where the crafter is unreachable. §3.1 previously said
  `--readme-file` only. This is a small consistency fix inside the swept
  paragraph.
- **The scaffold comment is not documented.** The r2 brief's Part 2 (the
  `$EDITOR` scaffold comment not shipping) is not carried in this brief.
  The global docs therefore say nothing about it; it is deferred in the
  manifest.
- **Sibling behavior described ahead of landing.** The docs describe the
  opener naming the brief and closing by session kind, as Part 1 pins
  them. They do this without waiting for the code, per the brief.
- **How a session's kind is identified.** Both deliverable homes tell the
  reader that `resolved_scope: []` is the read-only stamp. That rests on
  §3.4's statement that `--read-only` is the empty forecast's only
  spelling. If a scoped pack with no includes can also stamp `[]`, that
  sentence needs a qualifier.

## Pins, beyond the brief's minimum

- **Pins moved with the text.** The retired shape sentence's fragments
  are now pinned absent, in both docs.
- **Core clause held.** A constant-level check keeps the ruling's core
  clause ("a question asked as prose is not a shape") inside DOC_ASK.
- **New README pins.** A `ReadmeBriefPins` class pins the README sweep.
  It checks that the reading order's first three items are the manifest,
  `CLAUDE.md` and `README.md`, and that both CLAUDE.md homes name the
  `readme` key. It also checks the §3.2 example and bullet, and that the
  two retired phrasings stay absent.
- **Pins verified to bite.** Every new pin fails against the base docs.
- **Stale messages reworded.** The messages that said the doc sentence
  must agree with the opener are reworded, since the opener now carries
  its own ask sentence.
- **Light-tier pins untouched.** The admission and three-replies pins are
  unchanged.

## Suites

The following pass here, in all three run forms:

- `test_doc_crossrefs`
- `test_global_doc_selfcontainment`
- `test_sanctioned_pairs`

Full discovery ran 1326 tests with 2 failures. Both are in
`test_changelog_record` (`test_corpus_is_not_empty` and
`test_current_version_has_a_valid_record`), and both fail identically on
the untouched base. The request doesn't ship `claude/changelog/`, so this
is not caused by this change and forces no bump. `validation.sh` gates
full discovery behind `--slow` (about 3.5 minutes) and claims it
`untested`.
