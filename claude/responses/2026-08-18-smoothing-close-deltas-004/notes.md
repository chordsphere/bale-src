# notes.md — 2026-08-18-smoothing-close-deltas-004

Base pin verified before any edit: the shipped `claude/MASTER.md` is
2655 lines, sha256 `c1f190ad…8174b`, exactly the brief's pin. All 13
blocks (A1–A3, B, C, D, E, F, G, H, I, J, K) were extracted
mechanically from the revB brief between their BEGIN/END markers —
never retyped — and landed by script. Landed file: 2805 lines
(+150 net).

## Placement latitude calls (per the brief's flag-everything rule)

1. **Blocks B + D (rows 49–52).** One contiguous run after row 48's
   replaced body, single blank line between rows, before the `## 5`
   heading — the board's existing row-list convention. Block D's
   heading says "rows 50 and 51" but its body carries 50, 51, and 52;
   I read the revB preamble ("Block D gains row 52") as making the
   body authoritative and landed all three.
2. **Block C / E / G brackets.** Appended as the final lines of rows
   39, 47, and 46 respectively, immediately after each row's last
   sentence, no blank line — matching how row 37's and row 46's
   existing brackets sit. Block G lands after row 46's existing
   2026-08-18 bracket, as directed.
3. **Block F.** The two bullets go after the registry's last bullet
   (the Row-33 hazard-bracket entry) and immediately before the
   "Landed 2026-08-05, non-board" closing dated paragraph — my
   reading of "before its closing dated paragraphs."
4. **Block H.** The brief quotes the old clause without the
   sentence-final period, so I replaced the parenthetical only and
   kept the period outside the paren. The splice left the paragraph's
   first line at 122 columns, so the whole **Current version**
   paragraph was re-wrapped to ~70 columns.
5. **Block I.** Lands with its "New from the 2026-08-18 smoothing
   sitting:" header after entry 79, blank-line separated, before the
   `## 7` heading — §6's dated-header convention.
6. **Block J.** Appended blank-line separated after the "Ratified at
   the 2026-08-16/18 cleanup-master sitting" block, before `## 4`,
   per the §3-end accretion convention.
7. **Block K.** Appended blank-line separated after the 2026-08-16
   008-desk block, before `## 6`, with its own dated header as
   shipped in the block text.

## Re-wrap calls

Blocks C, E, and G were re-wrapped from the brief's column-0 wrapping
to the board's 4-space-indent ~70-column convention (long tokens
never broken; none of the three carries a sid or hash). Every other
block landed byte-verbatim as the brief wrapped it — the brief's own
wrapping already matches the file's convention. One cosmetic artifact
of the deterministic re-wrap: row 46's new bracket has a line
beginning with an em dash ("— trigger-fired pruning…"); whitespace
normalization makes it equivalent, but nudge it in review if it
bothers you.

## Validation design worth a close look

The brief's requirement (4) — negative-test the check set against
the unedited base — needs base bytes at validation time, which the
staging tree no longer has as a file. `validation.sh` recovers them
via `git show HEAD:claude/MASTER.md` and **hash-verifies the result
against the brief's base pin before relying on it**: if git is
unavailable or HEAD's copy doesn't match the pin, the negative probe
`[SKIP]`s with a loud reason instead of probing against unverified
bytes. The brief says the tree was clean at sitting-open and the pin
equals HEAD's landed state, so the probe should run; the SKIP path
exists only for a base-drift or gitless-staging surprise. In my
dress rehearsal (temp repo, base committed, changes applied, manifest
staged) all four checks passed, the claims block read `[agree]`
throughout, and the inverse run against the unedited base failed the
three containment-class checks as required.

The block texts inside `validation.sh` were embedded by the same
mechanical extraction (base64-encoded from the brief), so the
containment oracle and the landing share one source and zero
retyping.

## Claims basis

All four claims carry `claim_basis: "observed"` — the full
`validation.sh` ran against a staged copy before shipping, not just
predicted.
