# notes.md — 2026-08-24-sitting-close-deltas-004

Clean landing: all six anchors resolved uniquely in the shipped
base, all edits built mechanically (line-range extraction from the
brief, `<SID-SELF>` substituted in Block A only, token-stream
identity asserted at build time), and `validation.sh` passed
against the built mirror with every claim agreeing — plus a
negative control confirming the same checks fail on the unmodified
base, so the oracle discriminates. The one `changes[]` path is
exactly the forecast; nothing out-of-forecast to enumerate.

Three small mechanical decisions to ratify, none of which change a
token:

- **Block B sits inside the watch list.** The brief says "after the
  watch entry ending `(Rider item 5's deferral.)` and before the
  `**Fold-in registry**` paragraph"; a blank line separates the
  list from that paragraph in the base. I inserted the bullet
  directly after the pre-anchor bullet, keeping the list contiguous
  and the existing blank as the separator.
- **Block E ships with its internal blank and a trailing blank.**
  The lead paragraph and the bullet list keep the brief's blank
  line between them, and one new blank precedes `## 4. The board`,
  matching the doc's section spacing.
- **Re-wrap is greedy at width 72,** so a few line breaks fall
  differently than the brief's own wrapping (e.g. Block B's second
  line). The build asserts whitespace-normalized token-stream
  identity per block, and the validation checks are normalized, so
  the difference is invisible to every assertion the brief
  prescribes. If byte-identical wrapping to the brief was intended,
  say so and I'll re-land.
