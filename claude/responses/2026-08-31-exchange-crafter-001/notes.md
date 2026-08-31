# notes.md — 2026-08-31-exchange-crafter-001

Everything landed inside the forecast (`tools/`, `tests/`,
`docs/TARBALL.md`, `bin/VERSION`). No out-of-forecast path to admit at
apply. `bin/` is untouched apart from `VERSION`, and no `bale relay`
change, re-emit path, or extraction of section 29 went near this.

## The four calls you ratified in chat, for the record

Three of these you confirmed before I built; the fourth is the one your
brief's §3 asked me to go looking for. All four are the
flagged-deviation half of the loop — ratify or correct at review.

1. **`record_version: 1` rides the normalized manifest reading.** The
   brief's normalization list (session_id, `from: worker`, `round`,
   `created_at`, `questions[]`) omits it; section 29's
   `_normalize_manifest_to_record` emits it as the first key. Followed
   the bytes. `ExchangeBlockParity.test_normalization_matches_section_29`
   pins both the dict and its key ORDER, because `json.dumps` preserves
   insertion order and the body's bytes — and therefore the trailer's
   sha256 — depend on it.

2. **`--round` asserts on a record, fills on a manifest.** Taking the
   documented default of 1 literally on the record path would make every
   record past round 1 self-contradictory without a flag, which reads as
   a defect rather than a default. Absent `--round` therefore asserts
   nothing about a record's own round; supplied and disagreeing, it
   refuses (`test_absent_round_asserts_nothing_on_a_record` and
   `test_round_asserts_but_never_rewrites_a_record` pin both halves).

3. **`--emit-block` takes no response dir** and refuses every
   response-directory flag loudly, following `--probe` / `--bundle`.

4. **Question rows are checked in-tool, not against a schema file.**
   The brief's "the response-manifest schema it already ships beside"
   does not survive contact with a worker session: `INJECTED_TOOLS`
   ships the five global docs and the two tools, and a project's
   `schemas/` reaches `context/` only if its packer names it — and
   §3.1 permits even that copy to be a partial extract. A lookup would
   work in bale-src and nowhere else, which is worse than no lookup.
   `question_row_problems` reuses `QUESTION_STUB_KEYS` as the required
   half, so the tool cannot seed a stub its own check would reject.

## The byte-level facts parity forced me to learn

Your brief asked for every layout fact that §8.11's "As landed"
paragraph states differently or not at all. Three, all of which the
suite now pins and none of which are stated there:

- **`ensure_ascii` is load-bearing, not incidental.** The body is
  `json.dumps(record, indent=2)` with the default `ensure_ascii=True`,
  so a non-ASCII character in a question escapes to `\uXXXX`. Both
  sides must default the same way or the trailer disagrees. This is the
  one that nearly got past me: every ASCII fixture renders identically
  under either setting, so I added
  `test_non_ascii_body_is_escaped_the_same_way` specifically for it —
  and when I mutation-tested the guard by flipping the crafter to
  `ensure_ascii=False`, that test was the **only** one that went red.
  A corpus of plain-ASCII fixtures would have shipped this drift green.

- **Key insertion order is part of the wire bytes.** Not a property of
  the record as data, and easy to lose to a "tidy up the dict literal"
  edit in either home.

- **`to_side` has a silent fallback.** `format_exchange_block` computes
  the destination as `planner if from == "worker" else worker`, so a
  record with a missing or invented `from` renders "to worker" rather
  than failing. Unreachable through either CLI (both validate first),
  but it is what the renderer does, and I mirrored it rather than
  "fixing" it in the copy — a copy that disagrees with its original on
  an edge is exactly what the parity suite exists to prevent.

I mirrored **both** direction branches of `format_exchange_block` even
though the crafter refuses `from: planner` at the gate. A worker-only
mirror would leave half the layout unpinned and would drift silently
the first time anyone rendered the other direction; the policy belongs
at the gate, not as a hole in the renderer. The corpus covers both
directions for that reason.

`_normalize_manifest_to_record` agreed with the brief's reading in every
respect except item 1 above. Two fields differ in *provenance* and not
in shape, which the docstring says out loud: `round` comes from
`--round` rather than the thread's next NNN, and `created_at` is stamped
at emission rather than copied from the `preserved_at` sidecar — the
worker has no thread directory to count and no preserved copy to read.
Same slots, same spelling, same ISO-8601-seconds format as
`preserve_clarification_record` uses.

## What the parity suite does not cover, deliberately

`exchange_record_problems` mirrors every layer of
`validate_exchange_record` **except** the thread-level half:
`unresolved_answers` resolves each `(question_round, question_index)`
against preserved records, and that needs the thread. A record the
crafter accepts can therefore still be refused by `bale relay` on a
fact this side cannot see. That is correct — relay is the gate — but it
means "the crafter validated it" is not a promise the paste will
ingest. The docstring says so where someone would look for it.

## Verification, and one thing worth knowing about it

The suite goes 99 → 122 tests; the full repo suite is 687, all green.

The parity guard was **mutation-tested rather than trusted**: I injected
five drifts (trailer label, `indent` 2→4, `ensure_ascii=False`, dropping
`record_version` from normalization, loosening the unknown-key row
check) and confirmed each goes red, then restored and re-confirmed
green. I would not have believed the guard on a passing run alone,
since a parity test that imports both homes and compares them can pass
vacuously in more ways than one.

`validation.sh` restates byte parity and verdict parity standalone
(items 3b and 3c) rather than leaning only on the suite, so a staging
run proves the property even if the suite were skipped.

**Claims basis.** All five claims are `observed`, not `predicted` — I
ran each check against a reconstructed staging tree before shipping.
One caveat on the doc-contract guards: they read `docs/*.md` for all
five global docs, and the request ships only `docs/TARBALL.md` under
`context/`. I reconstructed the other four in my scratch tree from the
request's own injected copies, whose sha256s I verified against the
manifest's `provenance.contract_docs` block first. In real staging they
come from the repo, so the claim holds — but it is observed against a
reconstruction, and that is the one place I would look first if the
guards behave differently under apply.

**Release lists: checked, not assumed.** `tools/craft_response.py` is
already in both of `scripts/build.sh`'s lists (RELEASE_FILES and the
install manifest) and in `install.sh`'s file list, and both already
`chmod +x` it. Nothing new ships, so no packaging change was needed —
confirmed by reading the lists, per your brief's instruction not to
take that sentence on faith.

**Exec bits.** `tools/craft_response.py` and
`tests/test_craft_response.py` are both 0755 in the tree and the
`files/` overlay strips mode, so `apply.sh` restores both and
`validation.sh` asserts both (§7.7, generated from the same
`--executable` list).

## Proposals

**What** — add an install-side constant-parity row to `validate.sh` for
the exchange constants, the twin of the existing
`BUNDLE_SUFFIX` / `INTENT_PROMPTS` row.

**Why** — the bundle constants have two guards (CI-side
`BundlePackParity`, install-side `validate.sh`); the exchange constants
now have only the CI-side one, so an install whose `tools/` and `bin/`
came from different releases would not be caught at validate time. Not
shipped here: `validate.sh` is outside this request's `resolved_scope`,
and unlike the bundle row it would need `validate.sh` to load `bin/bale`
by path — a new capability there, not a copied line.

**Scope hints** — `validate.sh` around line 165, beside the existing
crafter rows. Independent of everything else here.

---

**What** — give `tools/craft_response.py` an index header (`CODE.md`
§2.1/§2.2).

**Why** — the file now carries seven banner sections and no navigation
map, past the three-section threshold, and the banners are unnumbered so
they cannot be referenced positionally. I noticed it from inside: adding
my section meant scanning for where the emission modes cluster, which is
exactly the scan an index header exists to remove. Not folded in here
because renumbering or naming seven existing sections is a layout
decision on a file this session already changed substantially, and it
should land as its own reviewable change rather than riding along.

**Scope hints** — `tools/craft_response.py` only; `CODE.md` §2.2 has the
format. Cheapest immediately after this lands, while the section
boundaries are fresh.

---

**What** — consider whether `docs/TARBALL.md` §5.9.2 is now carrying two
audiences.

**Why** — the section was already the manifest-shape spec, the courier
choice, and the exchange-record reference; it now also carries the
worker's four-step operating flow. It is still one subject (the
clarification's shape and how it travels), so I did not split it — but
it is the longest subsection in the doc and the next addition to it is
the one that should trigger the `DOCS.md` §6 seam question rather than
just appending. Flagging the trajectory, not proposing a split today.

**Scope hints** — `docs/TARBALL.md` §5.9.2; `DOCS.md` §6 has the split
criteria. No ordering dependency.
