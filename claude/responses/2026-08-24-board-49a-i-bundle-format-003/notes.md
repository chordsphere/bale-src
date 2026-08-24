# notes.md — 2026-08-24-board-49a-i-bundle-format-003

## What the probe established (TARBALL.md §4.5)

One paste-back probe ran before building: the repo's `docs/TARBALL.md`
at HEAD (b2de146, branch main, porcelain-clean for that path) is
**byte-identical** to the injected `TARBALL.md` (sha256 `e2408ba6…`,
matching the request's provenance stamp). The doc modification was
therefore built on the injected bytes as the base. Environment:
WSL2 Linux, bash 5.2.

## Out-of-forecast paths

None. All ten `changes[]` paths sit inside the stamped forecast
(`BALE.md`, `bin`, `docs/TARBALL.md`, `schemas`, `tests`,
`validate.sh`).

## Look here first on review

**The new schema is not yet release-registered.** Adding
`schemas/bundle-manifest.schema.json` means `scripts/build.sh`
(`RELEASE_FILES`) and `install.sh` (`INSTALL_LAYOUT`) each need its
one-line row — and per `test_release_packaging`'s description of the
build's tree-coverage guard, the **next release build will refuse
until they land**. I could not ship those edits: both files are
outside the write forecast and were not in `context/`, so I had no
modification base (and a probe round for two one-liners the planner
can type felt like the wrong trade). This is the same
planner-direct-edit path as `bale.toml`. Do it before the next
`scripts/build.sh` run. Relatedly: my trued-up `validate.sh` loop now
also checks `escalation-record` and `telemetry-record` presence — I
believe both are already release-registered (they ship in installs),
but I could not verify from the shipped context; if either is
missing from `RELEASE_FILES`, the same two-line fix covers it.

## Decisions to ratify

- **Suffix as the whole recognizer.** `.bale-bundle` (constant
  `BUNDLE_SUFFIX`) is reserved by the format spec, and the deny-list
  keys on nothing else — no config key, no directory convention, so
  nothing dangles and the exclusion is unconditional. Consequence: a
  file merely *named* into the suffix is treated as a bundle (the
  refusal message offers the rename remedy), and a directory entry
  ending in the suffix refuses as explicit naming too — perverse
  namings land on the cautious side. Tests pin the exact-suffix
  boundary (`about.bale-bundle.md` ships).
- **No admission flag, either half.** The checkpoint has
  `--allow-checkpoint-in-scope` for delegated oracle maintenance; I
  gave bundles no analog. A real bundle contains the checkpoint, and
  a bundle-handling session works from synthetic fixtures — I
  couldn't construct a legitimate case for shipping or landing a real
  one. If you want the symmetric escape hatch anyway, it's a small
  follow-up.
- **In-process-only intents API.** No CLI flag feeds
  `pre_answered`; the channel is a namespace attribute the
  bundle-composing caller (49a-ii's verb) sets, parsed by
  `parse_pre_answered_intents` at the one consumption site. This is
  deliberate: no typed command line can spell a pre-answered accept,
  blanket or otherwise, which I read as the strongest execution of
  constraint (2)'s "never a blanket yes". Cost: the accept path is
  pinned by direct-call tests at the function seam (with stubbed
  `__main__` helpers — see the suite docstring for the discipline),
  not by a subprocess e2e; the e2e closes when 49a-ii's verb exists.
  The pinned `test_supersession_pack.py` suite is green, unmodified.
- **Unconsumed intents proceed, loudly.** Per the brief's pin ("an
  intent that answers a prompt the flow never raised behaves exactly
  as today's decline default does"), an unconsumed intent changes
  nothing and the pack proceeds, with a FORCE-line report naming it.
  I'll flag the tension I saw: bale's culture elsewhere refuses
  materially-different outcomes (the disjoint-decline rule). I
  followed the brief; if you'd rather an unconsumed intent refuse the
  pack outright, it's a three-line change at the report site, and
  49a-ii/49b can alternatively enforce bundle/argv coherence before
  pack ever runs.
- **LF-normalization scope.** Member hashes are published over, and
  verified against, CRLF→LF-normalized bytes — scoped to the
  bundle's own reads exactly as briefed; lone CR is untouched (board
  50's territory).
- **Schema looseness and the prompt vocabulary.** The schema follows
  the sibling additive-fields posture. I deliberately did *not* add a
  record-wide closed-vocabulary walk for `prompt` (the
  escalation-`priority` precedent): "prompt" is too generic a key
  name to claim record-wide, and the named-spot enum plus the
  parser's refusal at the consumption site cover both ends. Say the
  word if you want the walk anyway.
- **Delivery flags are never stored in `pack_argv`.** Member presence
  is the single source: the consumer injects `--readme-file` /
  `--checkpoint-file` at the extracted paths (`--no-readme` on a null
  brief), so the stored argv can never disagree with shipped bytes.
  `validate_bundle_manifest` refuses a stored delivery flag and a
  stored `pack` verb.

## Proposals

- **Register the schema in the release lists.** What: one row each in
  `scripts/build.sh` `RELEASE_FILES` and `install.sh`
  `INSTALL_LAYOUT` for `schemas/bundle-manifest.schema.json`. Why:
  the tree-coverage guard will refuse the next release build without
  it (see "Look here first"). Scope hints: planner direct edit;
  blocks any release, not this apply.
- **Apply-side bundle backstop.** What: apply's pre-flight rejects
  any `changes[]` path ending in `.bale-bundle` (a worker landing a
  bundle is the self-oracle shape from the other direction). Why:
  this session closed the pack side; the apply side is the natural
  sibling, cheap next to row 20's deny-list machinery. Scope hints:
  `bin/bale_apply.py` + a contract-table row; independent of 49a-ii.
- **For 49a-ii (the open verb), two format-consumer notes.** What:
  (1) the verb's delivery-flag injection contract and the
  `--no-readme`-on-null-brief rule are specified in BALE.md §6.7 —
  consume them as written; (2) the intents channel expects the
  parsed `pre_answered` array set on the pack namespace before
  `cmd_pack` runs, and `validate_bundle_manifest` should gate the
  bundle before anything else is trusted. Why: both are contracts
  this session landed that only 49a-ii exercises end-to-end. Scope
  hints: `bin/bale` wiring; queued next in the bracket.
- **For 49b (crafter emission), the constant-duplication guard.**
  What: the crafter cannot import `bale_pack`, so it will re-declare
  the suffix and intent vocabulary; give the duplication a drift
  guard (the lint's embedded-schema JSON-equality precedent in
  `validate.sh`). Why: two homes without a pin is how the
  self-containment citations drifted. Scope hints:
  `tools/craft_response.py` + `validate.sh`; after 49a-ii.
