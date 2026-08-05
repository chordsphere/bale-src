# notes.md — 2026-08-05-ratification-microdeltas-010

All five deltas landed from the brief's wording; the diff is
confined to the header line, the §2 version paragraph, §3, and the
§7 archival bullet, and validation asserts that confinement by
hashing the untouched sections (1, 4, 5, 6, 8) against the shipped
original. A few calls worth your eyes:

- **Version stamp check (delta 2).** The brief's 0.3.32 agrees with
  this request's own pack-time provenance stamp
  (`provenance.bale_version: "0.3.32"`), so I recorded 0.3.32 with
  no divergence to flag. Per the deltas-005 precedent I worded the
  §2 verification sentence around the stamp rather than a live
  `bale --version` read, since the stamp is what this session can
  actually observe.
- **The §3/§7 seam siting (delta 4).** I read "the §3/§7 seam" as
  the record straddling both homes: the landing narrative plus the
  four ratified judgment calls sit as a compact block at §3's tail
  (beside the existing "Cleared at this landing" blocks, which
  seemed the established pattern for done-work records there), and
  the standing fact — sweep opted in beside `archive_dir`, manual
  dance retired — went into §7's archival bullet. If you meant a
  different siting, the block moves cheaply.
- **Sid expansions.** The brief's short references were expanded to
  full sids per the doc's own bare-NNN collision rule:
  `design-003` → `2026-08-04-board-6-blind-checkpoint-design-003`
  (the board-6 read-only design session, per §2's arc record) and
  `continue-plan-002` → `2026-08-04-continue-plan-002` (the sitting
  master, per this request's provenance.packer). `archive-dir-005`
  I left in the short form §2's trail already uses, qualified as
  "the 0.3.30 landing, §2's trail" rather than guessing its date.
- **Dropped sentence in the §3 charter bullet.** The old bullet's
  finding-3 status sentence (`archive_dir` landed at 0.3.30,
  architect opted in, archives materialize on future applies) does
  not survive the narrowing — the brief's replacement wording
  doesn't include it, and §7 now carries the same facts as the
  standing-fact home. Nothing was lost, but flagging since it is a
  removal inside an otherwise additive posture.
- **Watches preamble attribution.** Appending the sweep watch made
  the preamble's "the last three from the board-6 arc's" count
  wrong, so it now reads "the next three from the board-6 arc's,
  the last from `2026-08-05-auto-sweep-009`'s notes". A two-word
  consequence of the append, not a delta of its own.

## Untouched, possibly stale (observed, not changed)

Two lines the brief did not name and I therefore left alone,
recorded here so they're a decision rather than an oversight:

- §7's repo landmark still reads "bin/bale VERSION 0.3.31,
  architect-verified against the live install 2026-08-05" — now one
  landing behind §2's 0.3.32. A MASTER.md-only request can't verify
  the live install, and delta 2 named only the current-version
  line.
- §7's "Archives materialize on future applies — none on disk at
  this writing" — with `auto-sweep-009` applied and the sweep
  opted in, archives (and sweep commits) may now exist on disk;
  unverifiable from this request.

## Proposals

- **True up §7's VERSION landmark next deltas pack.** What: move
  the §7 "bin/bale VERSION" line to 0.3.32 (or whatever the sitting
  open verifies) and re-date its verification. Why: §2 and §7 now
  state different versions for the same binary; the divergence is
  mechanical fallout of delta 2's deliberately narrow wording, and
  the next sitting's standing `bale --version` check produces the
  observed value for free. Scope hints: `claude/MASTER.md` §7 only;
  rides the next master-deltas or sitting-open pack.
