# notes.md — 2026-08-31-sitting-close-deltas-013

All five brief items landed in `claude/MASTER.md`; both VERBATIM
kernels are byte-exact and contiguous on one unwrapped line, asserted
in validation.sh with count pins (kernel 1: one home, row 64's
bracket; kernel 2: two homes, the §3 watch closure and the §5 bolded
lead — the §5 home's `**` delimiters sit outside the pinned bytes,
which run contiguous between them).

## Decisions to ratify

- **The 011 rider record went on row 64** (item 2's "whichever reads
  more naturally"). Reasoning: the rider's HOLD story — S2 dropped
  because board 64's doc cargo had already landed — and item 3's
  lane-reconciliation kernel both center on row 64, so the rider
  narrative and the ruling read as one arc there. Row 65's bracket
  carries the cross-reference plus its own fact (the BALE.md stats
  line rode the rider). Swap the direction at review if you'd rather
  anchor on 65.
- **The closed forecast-precision watch stays in place**, its entry
  ending in the fourth accrual and a CLOSED sentence carrying the
  kernel — the keep-queued-substance posture, condensing left to a
  future sweep. If you'd rather closed watches leave the list
  entirely (STATE.md-style edit-don't-annotate), that's a one-entry
  deletion, but it would also delete kernel 2's §3 home.
- **The new BALE.md §7.5/§7.7 registry entry is appended at the
  registry's end** (accretion order, matching how recent entries
  accrued) rather than beside the older BALE.md §7/§7.2 true-up
  entry. Both orderings are defensible; move it if you prefer
  carrier-grouping.
- **Verbatim carries are word-verbatim, rewrapped.** The three
  Proposals texts carried into the registry keep every word and all
  emphasis but re-break lines at the registry's wrap width — the same
  treatment every existing "Text verbatim from …" entry shows. Only
  the two pinned kernels are byte-exact-one-line; that's how I read
  the brief's constraint, which names the kernels specifically.
- **Row 64/65 version phrasing**: both brackets say "at 0.4.20" and
  carry the strike-at-review flag inline ("the desk did not resolve
  which of 009/010 rode the bump"), stated once in full on 64 and by
  reference on 65.

## Check before accepting: the moved base

This is a whole-file mirror of the shipped `context/claude/MASTER.md`.
If the tree's copy moved after packing, apply overwrites that change
silently — reconciliation won't flag it because the manifest
legitimately declares the file modified. `git diff` on
`claude/MASTER.md` since pack time settles it in seconds; if anything
landed there, stop and tell me and I'll rebuild against current
bytes. (Same caveat 011 raised; same reason.)

## Claims basis

Both claims are marked `observed`: validation.sh ran green (exit 0,
both reconciliation rows `[agree]`) against a local staging
simulation — the mirror's bytes at the repo-relative path with the
manifest at `.bale-manifest.json`. Since the response is a whole-file
mirror and the checks read only that file, bale's real staging run
sees the same bytes; the moved-base note above is the one way this
could differ.

## Forecast

No out-of-forecast paths: the change set is exactly
`claude/MASTER.md`, the forecast's one entry. Nothing deferred.
