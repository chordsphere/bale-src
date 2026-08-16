# notes.md — 2026-08-16-planner-birth-003 (r2, post-HOLD)

## HOLD diagnosis (r2 delta)

The blind checkpoint held on one probe: "provisional-until-S6
marking present." Diagnosis from the reveal label alone: the charter
bound the literal hyphenated token — "marked provisional-until-S6
inline" — and I paraphrased it at all five marker sites as
"provisional until S6" (spaces). That is a worker miss against a
byte-exact charter phrase, not a fixture defect; the probe tracked
the charter faithfully. The r2 fix rewrites all five sites (the §8
general rule and the four inline section markers) to carry the
literal token, with prose adjusted to read naturally around it, and
adds a validation.sh probe asserting the token at 5+ sites so the
claim now covers what the checkpoint checks. No other file changed
between r1 and r2. One fixture observation from the reveal, for the
checkpoint desk: the guard-suite probe SKIPped with "pytest not
found" on the target box — the suites are stdlib-unittest and ran
green under `python3 -m unittest` in validation; a future checkpoint
that wants them blind should invoke unittest, not pytest.


The doc is born. Both guard suites run green on the changed tree
(observed, not predicted — I ran them; the claims carry
`claim_basis: observed`). Everything below is a call you asked me to
flag, or one I made and you should ratify.

## Flagged calls, in the order the brief raised them

**The CLAUDE.md read-path row reconciliation.** I *merged* rather
than stacked: the old pack-command row ("Authoring a `bale pack`
command … → TARBALL.md §3.4") is subsumed into one authoring row —
trigger "Authoring is the work — a pack command, a request brief, a
checkpoint oracle, a rescope offer, or a sitting", read
`PLANNER.md`, with the pack-command case additionally re-reading
`TARBALL.md` §3.4 as the flag surface. Rationale: two side-by-side
rows would both fire on every pack authoring, and the
solicited/unsolicited parenthetical the old row carried is preserved
inside the merged row, so nothing the old trigger said is lost. If
you prefer the two-row shape, the split is a two-line edit.

**The selfcontainment deny-list entry for orchestration.md: kept.**
The tombstone is still a project-local file; a global citing it
dangles in every other project exactly as before. I updated the
deny-list docstring to say the file is now a tombstone and why that
changes nothing. Consequence I accepted knowingly: PLANNER.md cannot
name its own source file, so the relocated half's §8 describes the
relocation generically ("the project explainer that was their
working home") and the tombstone carries the precise pointer in the
other direction — which is the direction citers actually travel.

**Evidence citations kept as "(evidence N)" markers.** The brief
binds self-containment, and the ledger stays in MASTER.md. I kept
the numeric markers in the relocated half (and used them sparingly
in the core) with a self-contained explanation in PLANNER.md §8:
they point at "the live-traffic evidence ledger … a project-side
record, deliberately not restated here." This mirrors the already-
sanctioned practice of numeric ADR pointers in TARBALL.md — opaque
but harmless in other projects, load-bearing in this one. If you
want the markers stripped instead, it is a mechanical pass; the
prose stands without them.

**Tombstone carries a 12-row section map** (old §N → PLANNER.md
§N+7). orchestration.md's header promised its anchors were stable
("future work — the escalation-record schemas first — cites this doc
by section"), and a bare pointer tombstone would have broken every
such cite. The map is the DOCS.md §6.4 tombstone obligation applied
to a whole-doc relocation. Old §1 maps to §8 "rewritten as the
half's standing" — its promotion-path content was consumed by the
event it predicted.

**Four→five true-ups beyond the brief's named list.** All under the
`docs` forecast entry, so in-forecast, but beyond what the brief
enumerated: TARBALL.md's §3.1 request shape (five injected docs, six
reserved slots) and §10.1 step-1 globals check; DOCS.md's Workflow
row, §2.2 exclusion list, and §8 parenthetical; CODE.md §13.4's
"adding a fifth one" reworded count-immune ("growing the set") since
the fifth slot is now taken. Rationale: leaving them would ship a
doc set that disagrees with itself about its own size — CLAUDE.md
saying five while TARBALL.md's shape shows four — and no queued
session owns those lines. The honest caveat: these docs now describe
the five-doc contract one session before the injection wiring
implements it. That is the same one-apply-behind lag every doc edit
in this repo lives with, and the brief pre-ratified the inertness
("PLANNER.md exists in-repo but is not yet injected, which is inert
and safe").

**Two "four" sites in BALE.md deliberately left** (also in the
manifest's `deferred`): §3.1's "the four global docs are real files
you can edit" and §7's pipeline step "Inject all four global docs".
Both describe `bin/bale`'s *current* behavior, which the out-of-scope
wiring session changes; truing them up now would document behavior
that doesn't exist yet. Proposed below for that session. The
doctrine section (§3.3) the brief named is fully trued up.

**Provisional-until-S6 markers.** Placed inline on the wholly
harness-era sections — §15 (escalation queue), §16 (worker refresh),
§17 (cost governance) — plus the sandbox-prerequisite paragraph
inside §12, with the general rule stated once in §8 ("future tense =
harness-era = provisional until S6"). The ratified pieces — the
specification-friction principle, the four controls, the shipping
gates, blind-checkpoint coexistence, the trust ladder — keep their
ratified standing unmarked, per "the six ratified judgment calls
keep their status."

**PLANNER.md grew a §7 Hard Rules table.** Not in the charter's
shape list, but every conditional-layer global (DOCS.md §9, CODE.md
§10) carries one, and CLAUDE.md §6's policy-tables sentence
enumerates them — it now reads "…and `PLANNER.md` §7." All rows are
policy (no mechanical gate reads craft); the enforcement column
points at the longitudinal signals — HOLD and clarification
clustering per packer — which is also where the S6 churn can harden
them. Cut it if you think the doc should stay leaner.

**The §3.4 migration question is noted, not engraved**, as the brief
directed: one sentence at the end of PLANNER.md §2 marking it an
open charter-widening question for a future sitting.

## One thing that surprised me

The crossref suite passed first try with PLANNER in the regex — 
including the brand-new `PLANNER.md §7` pointer in CLAUDE.md — which
means the citation graph across five docs was consistent on first
assembly. I'd budgeted a repair loop for dangling §-cites in the
relocated half and didn't need it: the +7 offset renumbering touched
only internal references, which the suite deliberately doesn't
parse, and every cross-doc cite in the relocated content already
named TARBALL.md/CLAUDE.md sections that exist.

## Proposals

**Wiring-session riders (for the already-queued injection session).**
When `GLOBAL_DOCS`/injection lands, sweep BALE.md's two remaining
"four" sites in the same response (§3.1 editable-docs note, §7
pipeline step 3), since they describe exactly the behavior that
session changes. Also worth folding in: the provenance
`contract_docs` stamp example anywhere BALE.md shows a four-key
block.
*Why:* this session left them stale on purpose (they document
current behavior); the wiring session is the one response where
truing them up and changing the behavior are the same diff.

**Master-desk delta wording (you asked for a draft).** For the
MASTER.md ledger pointers, a one-line form that keeps the entries
in place: append to the board-10 PLANNER.md queue entry —
"[2026-08-16: EXECUTED at `2026-08-16-planner-birth-003` —
docs/PLANNER.md born, orchestration.md merged past the banner with a
tombstone section map, four→five true-ups landed; S6 inherits
ratify-and-churn of the orchestration half; injection wiring is the
queued follow-up.]" — and, if you want per-evidence pointers, a
single line at the top of §6 ("planner-facing doctrine derived from
entries 15, 45, 49, 65, 69–72, 75, 78 now lives in docs/PLANNER.md
§§1–7; ledger entries unchanged") rather than touching each entry.
*Why:* the brief invited proposed wording; one accretion point beats
scattering edit markers through an append-heavy ledger.
