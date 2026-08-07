# Notes — 2026-08-07-board-13a-forecast-surface-004

## Compaction disclosure (CLAUDE.md §11.6)

A context compaction occurred mid-build, after the implementation and
test run were complete and the manifest's judgment fields were filled,
before validation.sh/notes/lint. Per §11.6 I re-grounded from the
durable artifacts (the request manifest, TARBALL.md, the partial
response on disk), recomputed every size and sha256 in the manifest
from the actual `files/` bytes during the §10.1 step-10 self-check
rather than trusting any pre-compaction value, and re-ran the full
suite and the response lint after the break. `feedback.self_reported.
compaction_occurred` is `true` with `disclosure_ref` pointing here.

## What landed

The full Session A slice of the ratified board-13 design: the
`--write` surface, the forecast record/stamp, the re-based pack-time
gates (disjointness + both blindness halves), the wizard follow-up,
the ADR pair (0015 Accepted, 0007 Superseded), BALE.md rows including
new row 31, schema descriptions, `bale status` labeling, VERSION
0.4.1, and a 20-test suite. 289 tests pass. All E1–E5 ratifications
implemented as ratified, including E3's read-side refusal.

## ADR-0007 flip: reverse-transform assertion shipped

Per the README's ask: yes, the evidence-35 reverse-transform pattern
was workable here, and validation.sh carries it. The staged 0007 is
reverse-transformed (strip the appended dated note, un-flip the Status
and Superseded-by lines) and asserted byte-identical — by sha256 —
to the pre-flip file. The flip is therefore provably *exactly* the
ratified edit; any other drift in that file fails validation.

## Judgment calls

- **Status rendering (Q4)**: the ratified answer was "label only, no
  new keys". I additionally chose NOT to render the include set as a
  second row: status's session block answers "what is enforced", the
  includes are no longer enforced anywhere, and a second row would
  imply they are. The `--json` `scopes` key is untouched.
- **Wizard: typed `--write` skips the read-only half** of the
  session-shape exchange, not just the follow-up. A non-empty forecast
  IS the lands-changes declaration (and `--write --read-only` is
  already an arg-parse contradiction), so offering `[r]` there would
  offer an answer the command line has ruled out. The prompt says why:
  "This session lands changes (--write given)."
- **`checkpoint_scope_admitted` description edit** (schema): not named
  in the decomposition's file list, but E3's one-flag-one-stamp
  ruling makes the old description (which said the *scope covered* the
  checkpoint) false for a read-side admission. Description-only, no
  shape change. Enumerated here since it goes beyond the
  `resolved_scope` description edit the brief names explicitly.
- **Read-side check is conservative containment** on the *resolved
  include set*: an `--include` covering the checkpoint refuses even if
  an exclude pattern would drop the file at walk time. Deliberate —
  same semantics as every other gate (declared entries, not walked
  files), cheap remedies, and no new walk dependency in pre-flight.
  Noted in the gate's docstring; flagging it here because it is the
  one place the refusal can fire where no oracle byte would actually
  have shipped.
- **Pre-separation open sessions** read their recorded include set as
  an over-forecast (conservative, self-clearing at close). No
  migration code; the refusal text says so.

## Scope

All changes[] paths fall under the request's shipped includes (bin/,
tests/, BALE.md, schemas/, claude/INDEX.md, claude/context/adr/). The
two created files (the 0015 ADR, the new test suite) land under
directory includes per ADR-0014. Predicted gate firings at apply:
zero.

## For the desk / sibling sessions (proposals, prose only)

- **Session B seams are ready**: the apply-side drift-gate refusal
  text still says "scope" vocabulary (deliberately untouched — B's
  lane per the decomposition), and the telemetry `attempts[].scope`
  key now carries a forecast for post-epoch sessions, which is
  exactly the epoch-marking problem B owns. Stats rows likewise
  untouched.
- **Session C (contract-doc propagation per E1)**: CLAUDE.md/
  TARBALL.md wording that says includes gate concurrency is now stale
  against this landing; C's lane.
- The desk's queued duplicate-path pre-flight check (from the design
  session's small-finding list) remains unclaimed by any session.
- Watch forecast precision in the first post-epoch sittings: the
  interesting early signal is whether workers' drift rates fall when
  packs start typing `--write` narrower than their includes.
