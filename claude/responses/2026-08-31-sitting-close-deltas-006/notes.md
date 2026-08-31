# notes — 2026-08-31-sitting-close-deltas-006

All four dispositions landed in `claude/MASTER.md`, house formats
matched, every VERBATIM string byte-exact and contiguous on one
unwrapped line (asserted in validation.sh). Judgment calls to
ratify at review:

1. **Two edits beyond the brief's four items, both the doc's own
   conventions rather than new substance.** First, the header's
   last-landed-by line is edited in place to this sid — the header
   says that happens "at each landing," so skipping it would have
   left the doc self-inconsistent. Second, I added a fold-in
   registry entry for the queued guard-docstring sanction line. The
   brief records the queueing only inside the §5 entry's prose, but
   the registry declares itself the "one home" for
   rides-a-future-session items, and an item findable only from
   inside a contract entry is exactly what the registry exists to
   prevent. Both edits are inside the forecast (claude/MASTER.md);
   strike the registry entry at review if you'd rather the §5 prose
   carry it alone. The sanction line itself did not land anywhere —
   tests/ is untouched, per out_of_scope.

2. **Board hygiene ran (brief item 4's conditional).** Rows do
   carry status — "queued <date>" in the row head, closure as a
   dated bracketed block ("[<date>: DONE — <sid> ...]", the rows
   49–53 style). Row 61 got that bracket: DONE, landed at
   `2026-08-31-global-doc-purge-004`, applied 2026-08-31, reinstall
   fired. I did not condense the row's queued substance to a
   one-line pointer the way ancient rows 1–4 read; the recent DONE
   rows all keep their substance, and condensing is a sweep-shaped
   call for a future desk.

3. **No version claim on the row-61 bracket.** Recent DONE
   brackets usually say "at 0.4.x"; the brief gave me applied-date
   and reinstall-fired but no version, and the purge was
   doc+test-side, so I didn't guess one. Add it at review if the
   purge rode a bump.

4. **Kernel placement in §5.** Both kernels are the entries' bolded
   leads — matching the block style the meta-specific-003 entry set
   — with the pinned bytes contiguous inside the `**…**` markers
   (the markers sit outside the pinned string, so a grep for the
   kernel still matches). The evidence phrases got the same
   treatment via a "The …" prefix (e.g. "**The stale-count brief
   defect.**"), keeping the pin bytes intact while reading as house
   leads.

5. **Row 66's bracket wraps around its pin.** To keep
   "sitting-label shapes" contiguous, its line runs a few
   characters past the doc's usual wrap column. Deliberate — the
   constraint outranks the gutter.
