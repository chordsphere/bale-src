# Notes — 2026-09-23-board-43-tarball-s5-compression-008

## Re-attempt: the HOLD on expects-probe-collision-one-home

This response corrects the held one (`corrects` names the same sid).
The checkpoint held on one probe, `expects-probe-collision-one-home`,
and my validation passed. Diagnosed from the label against the
brief's line, "the one home for that collision is §3.3; §5.9 and
§5.9.1 keep a pointer", the held doc was wrong twice:

- **§5.9.1 restated the collision.** It kept "`expects_probe`
  governs probes (§3.2), never questions about the request, so it
  never forbids a clarification". That is the third base mention's
  content with the flag value dropped. It no longer matched the
  literal token, but it was still the collision living outside its
  one home.
- **Neither pointer named the collision.** The §5.9 lead said "the
  edge case where probing is forbidden", and §5.9.1 said "under a
  probe ban". They pointed at §3.3 without saying *what* lives
  there.

My own suite pin (`test_probe_ban_collision_has_one_home`) pinned the
wrong reading: that no `expects_probe: no` may appear in §5 at all. It
went green on exactly the defect.

**The fix:** each site is now one physical line that names the
collision and its home, and nothing else:

> A gap met under `expects_probe: no` is §3.3's: its one home.

That line appears once in §5.9's lead and once in §5.9.1. Section 5
names `expects_probe` exactly twice, and never anywhere else.

The dropped clause carries no loss. §3.3's item 2 already returns a
clarification under the ban, and §3.2's bullet already scopes the flag
to probing.

**Pins and checks:**

- The suite pin now asserts the pointer reading. That is one line per
  home naming both the flag and §3.3, and two mentions in the span in
  total. It fails on the held doc and passes on this one.
- `validation.sh` gains the same check as its own claimed line, run
  on both docs with the same result.

**Also fixed:** `validation.sh`'s awk start and stop patterns spelled
`\.`, which mawk warned about and treated as "any character". They
are now `[.]`. The checks were right before and are exact now.


Section 5 is rewritten, the three doc riders are in, and the fourth
rider is the paragraph below. Everything outside section 5 and the
one 3.4 line is byte-identical to the base, and `validation.sh`
proves that by reversal rather than by a diff you have to read.

## The numbers

Section 5, bounded by the `## 5. Response Tarball` and
`## 7. Validation` heading lines: **988 → 735 lines, 7,267 → 5,534
words**, about a quarter. That is under the brief's "a third to half"
estimate for the record, and I stopped there on purpose. What is left
is mostly what the keep-list says stays as judgment prose (5.3, 5.4,
5.4.1, the 5.9 recourse table, the 5.9.1 blocking test), the pinned
sentences (5.9.2's paste-block sentence; 5.10's ask rule, admission
test and three replies), and the fixed examples (the shape tree, the
manifest JSON, the light block): about 80 lines of examples alone.
Cutting further meant cutting rules. Plainer style rode along
wherever I was already rewriting, never as its own yield.

## Section by section (lines before → after)

- **5.1 (73 → 62).** The shape tree, the generated-artifact deny
  rule, and the in-tarball rule all stay. The tarball-mode-is-not-
  only-tarballs paragraph keeps the probe / light block /
  clarification selection as prose. The two distinguished-kind
  paragraphs merged into one that points at 5.9's recourse table as
  the chooser. ADR-0013 → `ADR-0013 §5.1` twice.
- **5.1.1 (53 → 34).** Delete, rename, and chmod rules and the
  staging reconciliation stay. The delete example left: the crafter
  emits it, and the verbatim no-op block stays because the crafter
  and the lint cite it. → `ADR-0013 §5.1.1`.
- **5.2 (110 → 86).** The example manifest stays whole. The crafter
  paragraph moved up to lead the field list. `session_id`,
  `responds_to`, `corrects`, and `response_kind` now point at
  `response-manifest.schema.json`'s descriptions, which already
  carried them nearly word for word. The crafter fills the first two
  and the last from `--sid` and `--kind`. The judgment fields keep
  their bullets. Removed: the `v0.3.8+` token, and the note that a
  replaced response's tarball stays in `claude/responses/`, which is
  project archival rather than a worker rule.
- **5.2.1 (18 → 12).** Same rule, one paragraph.
  → `ADR-0013 §5.2.1`.
- **5.2.2 (90 → 43).** The biggest relocation. The member-by-member
  walk through `mechanical` and `self_reported` duplicated the
  schema's descriptions, and the field contract now points there.
  This covers `linkage` and its `depends_on`, the provenance echo's
  keys, `model_identity`'s spelling rules, `includes_missing`'s
  `decision:` form, `compaction_occurred`, `light_blocks`, and
  `paste_carried_rounds`. It also removes the paragraph that existed
  only to say the schema was `forecast_departures`' sole home.
  What stays is what the schema does not carry:
  - the trust split, with its rationale pointer;
  - `<vendor>:<model>` and `AGENT.md` §11.7's table, which §11.7
    points back at;
  - the `docs_read` stub exception and `DOCS_READ_EMPTY_STUB`;
  - the fill-by-running-the-lint workflow.

  The two ADR-0013 pointers became one, `ADR-0013 §5.2.2`, since the
  ADR's one key covers both. VERBATIM-3 is its own paragraph,
  directly after the workflow. The `v0.3.8` tokens went: the live
  rule ("a manifest without the block still validates; a new
  response includes it") stays, unversioned.
- **5.3 (61 → 49).** Keep-list: the four values, the scoping rule,
  the canonical-identifier rule, and the subset relation are all
  intact. The annotated-object paragraph shrank to what a worker
  needs, with the shape pointed at the schema. "(v0.4.7)" and "every
  earlier manifest keeps validating" became "the bare string stays
  valid". → `ADR-0013 §5.3`.
- **5.4 (36 → 36) and 5.4.1 (27 → 25).** Keep-list: what earns a
  `notes.md`, the out-of-forecast enumeration with its
  `forecast_departures` twin, and deferred-vs-Proposals. Wording is
  tightened only; the crafter's stub-seeding sentence stays because
  VERBATIM-3 points at it ("the departure stubs §5.4 names").
  → `ADR-0013 §5.4.1`.
- **5.5 (17 → 6).** One-sentence tombstone, dated by session. It
  keeps apply's legacy-archive tolerance as a clause: a live
  tolerance rule, no version. → `ADR-0013 §5.5`, which the ADR keys
  as `§3.4 / §5.5`.
- **5.6 (6 → 6), 5.6.1 (24 → 18), 5.6.2 (16 → 12).** The mechanized
  set, `README.md` absent (the lint cites 5.6.1 for it), the marker,
  and the judgment halves all stay. Wording only.
- **5.6.3 (7 → 5) and 5.9.3 (8 → 5).** One-sentence tombstones.
- **5.7 (73 → 42).** The fenced template became a bullet list of the
  same seven headers, in the same order, with the same guidance per
  header. The crafter's `HANDOFF_SCAFFOLD` owns the headers; what
  goes under each is judgment and stays. A side effect worth
  knowing: the old fence held `## Original goal` and friends, so
  `test_doc_crossrefs.top_level_section(text, 5)` stopped at the
  first of them on the base doc. It no longer does, but see
  Proposal 3.
- **5.8 (38 → 17).** The judgment-field bullets duplicated
  `diagnostics.schema.json`'s descriptions (`bail_trigger`,
  `bail_narrative`, `what_would_save_next_time`) and now point
  there. Two notes the schema lacks stay: architect-requested →
  `"other"` (with `→ ADR-0013 §5.8`), and verdicts are qualitative.
- **5.9 (20 → 17).** The recourse table stays. The
  `expects_probe: no` edge case collapsed to one pointer line naming
  the flag and 3.3, and the ADR-0011 rationale pointer stays beside
  it.
- **5.9.1 (51 → 41).** Triggers, the blocking test, default-to-ask,
  the two non-blocking paths, the Proposals route, the artifact
  rule, and the breach fallback all stay. The converse-admission
  sentence and the "`expects_probe: no` does not forbid a
  clarification" clause both collapsed to the one pointer line (see
  the re-attempt section above). §3.3's item 2 carries the
  clarification route under the ban.
- **5.9.2 (117 → 85).** The payload paragraph shed its courier
  sentences, and VERBATIM-2 is now the second paragraph and the one
  place couriers are described. The exchange-record paragraph now
  points at `exchange-record.schema.json`: `answers[]`,
  `disposition`, `amendment_target`, and the at-least-one rule are
  all in its descriptions. The optional row fields keep their
  names, a pointer to the schema and to `PLANNER.md` §15, and the
  batched/blocking consequence, with no `v0.4.7` token. The
  paste-block sentence stays byte-exact; parity is one sentence now.
- **5.9.4 (29 → 26) and 5.10 (91 → 86).** Wording only. Every
  pinned sentence is untouched.

**ADR-0013 citations:** ten became nine, all keyed. The pin reads the
ADR's own headings, so a key that stops resolving goes red.

**Version tokens in section 5:** five became zero.

## The riders

- **VERBATIM-1** is its own one-line paragraph directly after 3.4's
  `**Checkpoint-configured projects.**` paragraph. Inside a table
  row or mid-paragraph the line could not stay whole for `grep -Fx`.
  `test_sanctioned_pairs.RetiredSplitConditions` also keeps that
  paragraph's own text about checkpoints only, which this sentence
  would not break. Still, beside it rather than in it seemed the
  cleaner reading of "include-rule position".
- **VERBATIM-2** is 5.9.2's second paragraph.
- **VERBATIM-3** follows 5.2.2's emitter workflow.

`validation.sh` checks each rider with `grep -Fxc` (exactly one
whole-line match in the file) and again inside its home section.

## W3's stamp mismatch, mentioned

W3's blind checkpoint was amended at the desk, v1 to v2, and its
held tarball was applied on `bale retry` with `stamp_matched: false`
accepted per invocation. `PLANNER.md` §5 owes a prose mention of that at the next doc
landing, and since a global doc cannot carry a project fact, this
paragraph is the mention; close 19 records it from here.

## Pins

Only `tests/test_doc_crossrefs.py` changed. The other three suites
pin nothing that section 5 moved:

- the sanctioned-pair extracts are all in 3.4;
- `test_schema_embeds` reads schemas;
- the self-containment scan passes on the new text.

The existing pins that sit in section 5 all still hold, byte-exact:
5.10's ask rule, admission test, and replies; 5.9.2's paste-block
sentence and `--emit-block`; 5.4's head with `forecast_departures`,
`path`, and `why`.

The new `SectionFiveCompressionPins` class adds eight tests (52 → 60
across the four suites):

- the three riders, each in its home, with 5.9.2's among the first
  two paragraphs;
- the section-5 heading inventory, which is a regression pin and
  passes on the base too;
- no `v0.` token in section 5;
- the `expects_probe: no` collision homed in 3.3, with section 5
  keeping one pointer line in 5.9's lead and one in 5.9.1;
- every ADR-0013 citation keyed to a heading the ADR carries;
- a mutation self-test.

Every test in the class except the heading inventory fails on the
base doc. I checked that, the same way §7.2 asks for the script.

No sanctioned pair (DOCS.md §9) touches section 5, so none was
collapsed.

## Validation

`validation.sh` runs six checks, each claimed `observed`: I ran the
script on the changed tree (all pass) and on the base tree (the
rider and reversal checks fail).

- **The four suites.**
- **The three riders**, byte-exact.
- **The probe-ban collision:** exactly one pointer line naming the
  flag and §3.3 in each of 5.9's lead and 5.9.1, two mentions in the
  span, and 3.3 present.
- **The reversal.** It embeds the base section-5 span as a
  sha256-checked gzip/base64 blob and swaps it back in, bounded by
  the heading lines. It then drops the rider line and its trailing
  blank line, and hashes the result to the request's stamped
  `7f355f39…`. I also mutated one character of 4.1's heading to
  confirm the reversal check catches an edit outside section 5.

The script writes only a `mktemp` directory and suppresses bytecode.

## Named for the pilot

The crafter-to-lint loop now carries more weight. Shape prose that
left section 5 (the feedback members, the exchange-record fields,
the diagnostics fields) is found through the schema or through a
lint finding's section/expected/got. That trade was accepted in the
brief, and nothing here changes it.

## Proposals

1. **Update the response schema's top-level description.**
   - **What:** it still says "Field semantics live in TARBALL.md;
     this schema constrains only the universal envelope". After this
     pilot, several semantics live in the schema's own descriptions
     and section 5 points there.
   - **Why:** a reader following the schema back to the doc and the
     doc back to the schema finds each deferring to the other. The
     description also carries `v0.`-era archaeology and the
     B1/B2 session letters.
   - **Scope hints:** `schemas/response-manifest.schema.json` plus
     the vendored copy in `tools/response_lint.py`, in one change
     (the self-containment docstring's own warning). Not this
     session's forecast.
2. **Decide `--fragment` as 7.3's documented default.**
   - **What:** whether `--fragment` becomes 7.3's documented default
     (the brief's open question).
   - **Why:** the combined emission's own stderr tells the worker to
     prefer one part per call, and I did exactly that here. The
     wording change is 7.3's and was out of scope.
3. **Make `top_level_section()` fence-aware.**
   - **What:** make it (and `subsection()`) skip `#` lines inside
     code fences, as `unfenced()` in the new class does.
   - **Why:** on the base doc it truncated section 5 at the handoff
     template's `## Original goal`. It is harmless today only
     because no pin read section 5 whole. The next fenced example
     with a markdown heading in any doc repeats the trap.
