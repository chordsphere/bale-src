# notes.md — 2026-08-15-tarball-riders-003

One thing to ratify, two wording choices to glance at, no drift.

## Rider 3 landed in §3.4, not §3.2 — ratify the placement

The brief says "§3.2's read-only paragraph says an empty-forecast
session is structurally sweep-safe." It doesn't — the phrase
"structurally sweep-safe" appears exactly once in the doc, in §3.4's
`--read-only` table row. §3.2's read-only mention is the
`resolved_scope` bullet's "(forecasts nothing, locks nothing, may
land nothing)", which never says sweep-safe. I took the brief's
section number as a mis-cite (the phrase match is unambiguous) and
put the race-safety clause where the sweep-safety sentence actually
lives, extending it in place: "...structurally sweep-safe, and
race-safe as well: an open `[]`-forecast sibling can be disregarded
in re-landing and race reasoning, because it structurally lands
nothing."

I checked this against the constraint you flagged: the edit sits in
§3.4 but nowhere near the sanctioned-pair pins —
test_sanctioned_pairs pins two §3.4 passages (the
unsolicited-runnable sentence and the split-supersession sentence),
and the `--read-only` row isn't one of them. The pin test passes
byte-untouched, as the brief predicted for the intended placement.
If you actually wanted a *new* sentence in §3.2 instead, kick this
back — but I'd argue against it: stating race-safety away from the
sweep-safety sentence would split one doctrine across two homes.

## Rider 1: §5.9.2 never said "repo"

The brief describes both schema sites as saying "in bale's repo."
Only §5.8 did; §5.9.2 named the schema with no location at all. The
ratified direction (state install-locality at both sites) is
unaffected — §5.8's parenthetical is reworded and expanded slightly
("the schemas tree ships with the install, reachable from any
project the same way the `tools/` pair is"), and §5.9.2 gets a
minimal "(in the bale installation, beside §5.8's)" so the second
site points at the first rather than repeating the class argument.

## Rider 2 placement: §7.2 item 6

The brief offered §7.2 item 6 or the §3.1 tools note. I picked §7.2
item 6, matching the manifest goal's "beside the session-assertion
prose": item 6 already gives "an INDEX entry exists for a new doc"
as an example assertion, so the doc-contract pointer lands where a
worker reading only the validation material would look for it. One
sentence, pointing at `DOCS.md` §9 and `CODE.md` §10 as the full
homes — nothing restated, per the one-home rule.

## Validation

Both checks in `validation.sh` were run against a simulated staging
copy before packing (hence `claim_basis: "observed"`): the three
guard suites (7 tests) pass, and the rider assertions pass. One bug
caught by that dry run and fixed: the `--doc-assertions` grep needle
parsed as a grep option until the `--` separator was added.

No out-of-forecast paths: the change set is exactly the forecast,
`docs/TARBALL.md`.
