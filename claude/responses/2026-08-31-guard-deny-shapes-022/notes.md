# notes.md — 2026-08-31-guard-deny-shapes-022

## Out-of-forecast drift to admit at apply

One path, authorized in advance:

- **`schemas/telemetry-record.schema.json`** — outside the stamped
  forecast (`tests/test_global_doc_selfcontainment.py`) and inside
  the request's original `out_of_scope` line, which the planner
  amended for exactly this in the exchange thread (round 2, answer
  2, preserved at `.bale/clarifications/…-022/002.json`): the new
  guard correctly fails the current tree on this file's post-purge
  drift, and I was authorized to reword it, descriptions only, under
  the purge's structure-identity discipline. Five rewrites: the
  three `board 63` citations became bare `(v0.4.21)` version
  anchors; `is board 44's` became `lands when data accrues` (the
  cost block's own deferral idiom, line 217); and the hyphenated
  `board-63 session notes` became `the landing session's notes`.
  Structure verified: with every `description` key stripped, the
  edited file is deep-equal to the shipped original, and
  `validation.sh` re-asserts that against a pinned hash of the
  canonicalized remainder in staging.

## What the probe and the exchange established (§4.5 provenance)

- The 015 archive holds only `notes.md` — the paste-ready seven and
  the purge manifest are gone from the environment; the ratified
  deny set now has its durable home in the guard itself.
- The five: request-manifest, telemetry-record, escalation-record,
  exchange-record, bundle-manifest ("the five non-embedded schemas",
  board row 66's own text). diagnostics and response-manifest are
  embedded-family, out.
- The seven: board/evidence numbered forms, the `BALE.md` and
  `orchestration.md` literals, `\bS[0-9]\b`, `session [A-D]\b`, and
  the standalone letter-digit token. No dated-citation shape —
  deliberate, it would collide with `created_at` and session-id
  examples. ADR-number and PLANNER.md-section citations are exempt
  house style (no shape matches them, by design).
- The board 63/44 citations in telemetry-record are post-purge
  reintroductions by the board-63 session, same day — drift, not
  purge exemptions. My clarification's bytes-evidence reasoning was
  sound but keyed on history I didn't have; resolved.

## Judgment calls to ratify

1. **Row-tolerant board anchor.** The ratified text reads "board
   followed by digits"; the shipped pattern is the docs group's
   `\bboard(?: row)? \d`. Strictly wider — but `board row 66` is the
   purge's own citation form, and a narrow anchor would wave exactly
   that shape through. Flagged in the docstring too. Narrow it if
   you meant the literal reading.
2. **The hyphenated `board-63` reword.** Invisible to the ratified
   pattern, so formally beyond the literal deny set — the same
   posture as purge notes item 3, and it sat inside a description
   string already under edit. Kick it back if you want
   pattern-visible drift only.
3. **Verdict-recording checks are all claimed.** Both non-tautological
   checks carry `claim_basis: observed`: the guard suite and the
   structure-identity assertion were actually run in-session against
   a replica tree assembled from this request's own bytes (and the
   guard was additionally run against the pre-clean drift state to
   confirm it fails — the pin bites). The syntax check stays
   unclaimed as tautological.

## Collision inventory (carried per round-2 answer 3)

Why the two deny tables stay per-surface, as of this tree:
schema-side, the board form correctly fails telemetry-record's
reintroduced citations (now purged, but the direction stands);
docs-and-tools-side, `PLANNER.md` carries `S6`
provisional-doctrine markers (×4), `tools/response_lint.py` carries
`B1`/`B2` session letters, and `TARBALL.md`'s session-id examples
sit adjacent to any loosely anchored date shape. A merged table
fails in both directions. The guard's docstring carries the same
inventory so the future convergence sitting inherits it without
this file.

## Proposals

- **Purge response-manifest.schema.json together with the lint's
  vendored copy, then extend the scan.** `tools/response_lint.py`
  line 235 vendors response-manifest's dirty description verbatim,
  and lines 929/1021/1124 cite B1/B2 free-standing; the lint is
  already in the guard's docs-and-tools scan group. Why: until both
  land in one change, response-manifest can't join the schema scan
  set and the letter-digit shape can never extend toward the tools
  group — the convergence question stays artificially open. Scope
  hints: `schemas/response-manifest.schema.json` +
  `tools/response_lint.py`, descriptions/comments only, then a
  one-line INSTALL_SCHEMAS addition here; only after this session
  lands, to avoid forecast collision on the guard file.
