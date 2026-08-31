# notes — 2026-08-31-sitting-close-deltas-3-025

One file changed, everything inside the forecast. All six brief items
landed; both kernels are byte-exact, contiguous, and unwrapped, and
validation asserts them that way (grep count AND single-line count,
so a wrapped landing fails — the wrap lesson applied from the
assertion side). The close assertions were also run negatively
against the unedited doc: 37 FAILs, exit 1, so they bite. Four
judgment calls to ratify and two flags below.

## Judgment calls to ratify

1. **"Annotate both registry entries" read as one bracket naming
   both riders.** The two fixture riders (the post-epoch fixtures
   entry and 010's linkage-shapes extension) live in one physical
   registry bullet — the extension was merged into the entry at the
   wave-2 close. So the did-not-fire annotation is one dated bracket
   at that bullet's end, explicitly covering "neither this entry nor
   its linkage-shapes extension" and carrying the transport lesson
   for both. If the desk meant two separate physical annotations
   (say, one inside the extension's own bracket), say so — it's a
   two-minute edit.

2. **The wave-3 block's shape.** Item 2 says "extend 019's §3
   routings block," and 019's block explicitly defers the landings
   to "the next close's facts." Appending this close's facts under
   019's own recorded-by header would misattribute them, so the
   extension is a sibling block immediately after it — same shape as
   the wave-2 precedent, opening with "the routed destinations of
   the wave-2 dispositions block above, every one landed," and
   restating the carries-only-what-has-no-row-home rule so it
   doesn't read as narrative accretion. Board 44's landing points at
   its row rather than being restated in the block.

3. **Kernel 1's placement inside the tools-true-up bullet.** "Where
   the tools-true-up landing is recorded" resolved to the wave-3
   block's tools-true-up bullet (the landing's only home — the
   session has no board row). The kernel sits as its own unwrapped
   line mid-bullet, after the landed-facts sentences and before the
   HOLD story, so the amendment record reads in sequence: what
   landed, the amendment sentence, why the amendment happened. The
   HOLD surrounding-facts phrasing is mine per the brief's "yours to
   phrase."

4. **Registry acceptance stamps.** Each new rider entry closes with
   "(Accepted 2026-08-31 at the continue-plan-012 sitting's wave-3
   close.)" — following the existing entries' "(Accepted …)"
   convention, on the reading that registering at the close is the
   desk's acceptance. The 022 entry also notes its "only after this
   session lands" condition is now satisfied ("one change, now
   unblocked," per the brief). The verbatim quotes preserve each
   source's own markers (020/024's **What/Why/Scope hints**
   paragraphs; 021's bold-lead bullets with italic *Why/Scope
   hints*; 022's unbolded Why/Scope hints) — verbatim means their
   bytes, not a normalized template.

## Flags, no action taken

- **Row 44's earlier bracket may now carry a stale conditional.**
  The 018 fold-in bracket says "Until it lands, every `bale stats`
  run warns once per open session." Neither the brief nor 024's
  notes says whether 018's folded read side (`"opened"` into
  IN_FLIGHT_OUTCOMES; the session_work_class provenance resolution)
  landed with 024 — the brief says "all four read sides," and the
  fold-in isn't clearly one of the four. The DONE bracket therefore
  carries only facts of record and stays silent on the fold-in; if
  the desk confirms it landed, the earlier bracket's "until it
  lands" clause wants a one-line true-up (also in the manifest's
  deferred list).

- **Check 4 (diff confinement) may SKIP in the operator's staging.**
  It needs a reachable pre-change copy of the doc; the script tries
  the real tree at `../../` and `../../../` from the staging cwd
  (per-sid staging under `.bale/staging/`) plus two script-relative
  fallbacks, and skips with a reason otherwise. Its claim is
  `observed` because the exact comparison ran here against the
  request's shipped base bytes (3 lines removed, 254 added, nothing
  else); a staging SKIP reconciles as [n/a], not a disagreement. An
  already-applied base (identical bytes) also resolves to SKIP, not
  a confusing FAIL.

## Verbatim-quote provenance

All seven rider quotes come from the shipped archive copies under
`context/claude/responses/…/notes.md` in this request — 020's and
022's Proposals sections, 021's three Proposals bullets, 024's two
Proposals subsections. Kernel bytes, the §5.9.2 rescued sentence,
and the 023 facts come from the brief itself (023 shipped no
notes.md; the brief is the desk-probe record's carrier, as its item
5 states).
