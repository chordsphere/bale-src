# notes.md — 2026-08-15-doc-mechanization-002

Everything in the brief landed, plus both fold-in riders. All of it is
in-forecast (docs/DOCS.md, docs/CODE.md, tests, tools/craft_response.py
— the two new test files land under the `tests` directory entry). A
few decisions and assumptions to ratify, roughly in order of how much
I'd want you to look at them.

## Assumptions I proceeded on (check these first)

1. **Label-column cap value: 40, overflow-not-truncate.** The
   registry entry for 008's accepted proposal wasn't shipped in this
   request (MASTER.md isn't in `context/`), so I couldn't read the
   verbatim context. I implemented: `width = min(max_label + 1, 40)`,
   and a label past the cap prints in full — identifiers are verbatim,
   never truncated — with only its own row overflowing the column.
   If the accepted proposal fixed a different constant or truncation
   behavior, the change is one line in `RECONCILE_EPILOGUE` plus the
   `test_label_column_is_capped` threshold.

2. **Exec bits on the four shipped .py files.** All four (the crafter
   and the three test files) carry shebangs and `__main__` blocks, so
   `apply.sh` restores `+x` on all of them and `validation.sh` asserts
   it. If the repo's test files are deliberately non-executable today,
   drop the three `chmod` lines and their assertions at review — the
   suites run through `python3 -m unittest` either way. I judged this
   too small to spend a probe on; say the word if you'd rather I probe
   mode bits in future.

3. **The prune-declaration pattern.** DOCS.md §9 said "matching one of
   the two patterns" without fixing literals. The emission requires a
   deleted entry's reason to contain a word on the `archiv-` or
   `delet-` stem (case-insensitive). Weakest honest mechanization of
   "distinguishes archive from delete"; easy to tighten if you want
   e.g. a leading `archive:`/`delete:` tag convention.

4. **ADR reverse-transform details.** The dated landing-note line is
   recognized as an optional list marker plus an ISO date
   (`- 2026-08-15: …`); the supersession flip tries both `Accepted`
   and `Proposed` as the pre-status. Both are safe to be generous
   about because the check is pre-image sha256 equality — a
   reconstruction either reproduces the exact shipped bytes or it
   doesn't; there is no way for a looser candidate set to sanction a
   diff that isn't one of the two flips plus at most one dated line.

## Design decisions worth a look

- **CLI shape.** `--doc-assertions` is a mode (mutually exclusive
  with the other output modes), with block selectors `--index PATH`,
  `--adr-dir PATH` (+ `--adr-baseline DIR`), `--prune-reasons`, and
  `--index-header PATH` (repeatable). At least one selector is
  required; every selector without the mode is a flag error, matching
  the existing hygiene posture.

- **Where the ADR pre-change hashes come from.** `validation.sh` runs
  post-overlay, so the pre-change bytes aren't in staging. The crafter
  therefore embeds them at craft time: `--adr-baseline` points at a
  local directory holding the pre-change copies (in practice the
  request's `context/` copy), and baseline presence/absence per
  basename is what classifies an ADR file in the mirror as
  modified-vs-created at craft time. At run time the manifest's
  `action` is authoritative: a modified ADR with no embedded hash is
  a loud FAIL telling the worker to re-emit with the baseline.

- **`--fragment` keeps the combined emission byte-identical.** Bare
  `--validation-epilogue` output is unchanged (a test pins that the
  three fragments concatenate to it exactly), so nothing that pasted
  the combined block breaks; the fragments are the new, safe path.
  Per the registry note, the definitions fragment alone provably
  fires nothing (tested by executing it under `set -euo pipefail`).

- **CODE.md §10 got the mechanization note too.** DOCS.md §9's new
  pointer paragraph sits in sanctioned-pair territory with CODE.md
  §10, so the twin got the parallel sentence in the same response,
  and the new drift-pin test pins the shared tail on both sides.

## Deviations from the brief's estimates

- **Retry after checkpoint HOLD (this tarball is the r2).** The
  blind checkpoint asserted `docs/DOCS.md < 24419` bytes; the first
  response landed at 24423 — the pointer paragraphs ate back the
  deleted recipe prose, net −159 against a required −163. The r2
  trims the `(shipped in every request per TARBALL.md §3.1)`
  parenthetical from both twins' mechanization notes — the exact
  trimmable prose the first notes.md named — landing DOCS.md at
  24373 (net −209). No pinned extract was touched, so the
  sanctioned-pair test is byte-identical across the retry; the
  provenance-of-the-crafter fact the parenthetical carried folds
  into the TARBALL.md proposal below. Nothing else changed between
  r1 and r2 beyond the two docs and recomputed hashes.

- **Net byte delta is ~−0.2KB, not −2–4KB.** The compressed cells
  were smaller than the brief estimated (~0.7KB of recipe left
  DOCS.md; the anchor paragraph was ~0.25KB), and the pointer
  sentences plus the two mechanization notes add most of it back.
  The *pattern* held — every recipe detail now lives in the emission
  — but the docs didn't shrink by kilobytes.

- **CODE.md §10's prune row is untouched** (deferred in the
  manifest): it isn't in the brief's five-row enumeration, its
  mechanical residue (non-empty reason) is already bale's own
  contract, and "reason naming its criterion" is judgment.

## Surprises

- The single-line-grep hazard the deleted anchor paragraph described
  bit me inside this very session: my first draft of a session
  assertion grepped a phrase that markdown-wraps differently in the
  two docs. Fitting. The knowledge now lives in the two places that
  execute it (the sanctioned-pair test normalizes whitespace before
  matching; the emissions parse structure, not prose), which is the
  argument for this whole session in miniature.

- `tests/test_doc_crossrefs.py` found zero dangling references in the
  current docs — the discipline has held by hand so far. The suite
  parses 77 cross-doc pointers today and has a self-test that fails
  if the parse count ever collapses (regex rot guard).

## Proposals

### TARBALL.md could name --doc-assertions beside the epilogue

**What:** a one-clause mention of `--doc-assertions` where TARBALL.md
§7.2 item 6 (or the §3.1 tools note) discusses session-specific
assertions.
**Why:** the emission's homes are DOCS.md §9 and CODE.md §10, which
is where a doc-touching session will find it, but a worker reading
only TARBALL.md's validation section won't learn the blocks exist.
Not shipped because TARBALL.md is outside this session's write
forecast.
**Scope hints:** docs/TARBALL.md only; a sentence.

### Consider a `bale stats` cut on claim_basis

**What:** when the eventual stats aggregation lands, split
claim/verdict agreement rates by `claim_basis` (`observed` vs
`predicted`).
**Why:** this session filled six claims, five of them `observed` by
actually rehearsing the staging pipeline locally before packing —
the calibration signal the v0.4.7 carrier exists for is now cheap to
produce, and the split is where it becomes readable.
