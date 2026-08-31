# notes — 2026-08-31-sitting-decisions-foldin-005

## Assumption proceeded on (flagged in chat before building)

The brief's §2 header says "five work rows" but enumerates six bolded
row titles — the sixth (Install-surface schema purge) says in its own
body it was discovered at the 2026-08-31 desk rehearsal, i.e. after
the count was likely written. I landed all six: "the substance of
every item must land" and the checkpoint pins each title, so the
six-row superset is the only reading that can't fail either
constraint. If "five" was deliberate, tell me which row to drop and
I'll ship a correction.

## Placement calls (the brief delegated placement)

- **Ruling queue is a new named list in §3**, seated between the
  Watches list and the Fold-in registry. MASTER.md had no existing
  home for queued desk rulings — they've historically ridden
  sitting-close bullets ("X heads the next sitting's agenda") and
  watch dispositions. The brief names "the sitting/ruling queue" as
  a destination, so I gave it the one home rather than burying the
  item in a narrative bullet. Surfacing per DOCS.md's
  don't-invent-categories-silently rule: this is a new list-level
  structure inside an existing doc, not a new doc category, but the
  spirit applies. Rename or relocate freely at review.
- **Board rows landed as 61–66**, continuing §4's numbering, with
  "queued 2026-08-31" datelines matching rows 55–60's house style.
  Row order follows the brief's order; sequencing among the smalls
  stays the next desk's call per standing practice.
- **The ratification is a new dated §5 block** ("New, ratified
  2026-08-31 (the meta-specific-003 sitting, read-only)") with the
  VERBATIM kernel sentence as the bullet's bold lead, kept on a
  single unwrapped line so a fixed-string grep matches it. The
  expansion cites board 61 as "the purge session".
- **Watch entries** appended at the end of the §3 Watches list, each
  with its phrase-pin kept contiguous on one line (which forced the
  bullets to open lowercase-neutral: "Thin predicted-basis claims"
  and "The contract-doc HOLD rate…").
- **The header's "Last landed by:" line** edited in place to this
  session's sid, per the doc's own stated convention. Not named in
  the brief's inventory, but it is the doc's landing rule and the
  edit is inside the forecast.

## Wording notes

- Row 61 says "sid slug `global-doc-purge`" — the brief gave the slug
  only, and I didn't invent the full YYYY-MM-DD-…-NNN form.
- Row 65: the brief's "stamp reads rounds: 0: every blocking ask…"
  double-colon rewritten as "rounds: 0 — every blocking ask…"; row
  bodies are mine to phrase per the brief.
- Row 66 cites "board 61" where the brief said "the purge session",
  now that the row has a number.

## Validation shape

Doc-only session: no project-level lint/build surface applies, so
claims cover the session-specific assertions (TARBALL.md §5.3's
no-surface rule). The utf-8 parse check runs unclaimed as
near-mechanical. All ten checkpoint-pinned strings are asserted via
fixed-string grep against the staged doc, plus structural checks
(rows 61–66 present, ruling queue seated between Watches and the
Fold-in registry, header line updated, 8 top-level sections
unchanged). Rehearsed here against the mirror: all agree, exit 0.
