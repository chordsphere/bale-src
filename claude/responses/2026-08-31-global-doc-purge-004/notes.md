# notes.md — 2026-08-31-global-doc-purge-004

The purge landed as briefed; nothing surprising in the citation
sites themselves. Things worth your eyes:

**The count.** PLANNER.md carried 45 "(evidence N)" parentheticals,
not the brief's ~30 — several lines held two, and a few spanned line
wraps ("(evidence\n69)"). All removed mechanically by one
multi-line-aware pattern; every removal site was then diff-reviewed
by hand. No sentence lost its lesson: every citation was a trailing
parenthetical on prose that already stated the rule.

**Rewrap.** Removing wrapped citations joined some lines past the
docs' ~72-column convention; thirteen affected prose lines were
rewrapped (table rows that were long before the purge were left
alone). If the rewrap makes the diff noisier than you want, the
content-bearing hunks are the ones the manifest reasons name.

**§8 rewrite.** The sanctioning paragraph now reads: doctrine earned
from live traffic, ledger project-side and deliberately not
referenced, every lesson self-contained as written. It replaces the
"cited, not carried" sanction in place — same paragraph, same
section, no renumbering.

**§5 step 5.** `bale amend-checkpoint` verified against the shipped
BALE.md §5.7 before landing: the verb performs exactly steps 4–5's
operator half (published-hash verification + per-sid commit), so the
step names the verb and the hash check and leaves the retry/accept
flow as it stood.

**Verbatim forms.** `PLANNER.md` §15 landed backticked in
TARBALL.md, matching the doc's house style for doc citations (the
brief's rendering was ambiguous on whether the backticks were
formatting). In the schema's JSON descriptions it landed as plain
"PLANNER.md §15", matching the descriptions' unbackticked doc-cite
style. Both spellings are asserted byte-exact in validation.sh, per
the verbatim-assertion corollary.

**Guard extension honesty note.** The test's "literal substrings,
not a heuristic" framing was amended rather than deleted: the
substring half stays literal, and the pattern half is confined to
two word-boundary-anchored digit shapes. The extension bites: run
against the shipped (pre-purge) tree it produces 7 failures —
evidence shapes in PLANNER.md, board shapes in TARBALL.md and both
tools, orchestration.md/BALE.md substrings in the lint. That
negative check can't ride in validation.sh (staging has no pre-purge
bytes), so it's deferred in the manifest and recorded here.

**Schema/embed motion.** The seven description substitutions were
applied by one script to both the schemas/ source and the lint's
embedded constant, so the two sides cannot have diverged by hand;
test_schema_embeds passes in staging. diagnostics.schema.json was
verified clean as the brief claimed — no shapes, no denied
substrings — and is untouched.

**Claims basis.** All four claims are annotated `observed`: the
suites, the byte-exact greps, and the sweep all ran against a
staged copy of the applied tree before packing.

## Proposals

**Genericize bin/-path references in the injected surface.** The
purged surface still references bale implementation files by path:
craft_response.py names bin/bale_pack.py (the constants it
re-declares) and the schema descriptions name bin/bale_validate.py;
TARBALL.md §3.1 names bin/bale for INJECTED_TOOLS. These resolve
only where a bale checkout exists, but unlike doc citations they
describe the tool's own implementation, and TARBALL.md already
carries the bin/bale form — so they read as sanctioned tool-side
facts, not project citations, and the deny shapes deliberately don't
catch them. If the sitting wants the stricter reading, that's a
follow-up row: decide whether bin/ paths are legal in injected
surfaces, and either add a deny entry or record the sanction.

**"S5" residue in the claims description.** The claims description's
"the manifest carrier for S5's record-side shape" was genericized to
"the record-side shape" when its board citation dropped; other
sitting-label residue may exist in the five non-embedded schemas
already queued as their own board row — worth sweeping for
sitting-label shapes (S<digit>, session-letter forms) when that row
runs, not just evidence/board numbers.
