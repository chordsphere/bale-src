# notes.md — 2026-08-04-board-6-blindness-enforcement-006

## The two sanctioned constraints, honored

- **VERSION is 0.3.28, tagged "board 6 session C."** Per the master's
  version-ladder disposition relayed with this pack — and recording,
  as the constraint asks: **sessions A and B landed unbumped at
  0.3.27** (the shipped tree read 0.3.27 with A's and B's surfaces
  tagged by session name, per B's notes). New session-C surfaces are
  tagged `v0.3.28, board 6 session C` in comments, help text, and
  schema descriptions.
- **The section 11 header rider landed**, text change exactly as the
  session-B notes proposed: "steps 1–13 of section 8.1" → "steps 1–15
  of section 8.1". Header sentence only; no row was reworded by the
  rider.

## Decisions to ratify

- **Stamp-verification siting: §8.5 prose, not a §8.1 numbered step.**
  The brief's D7 touch list says "BALE.md (§7.1/§7.2, §8.1)", but the
  verification needs `base_sha`, which §8.1's numbered steps do not
  have in hand — it runs at §8.2's base resolution, exactly like
  session A's dangling refusal, which A documented in §8.5. I followed
  A's precedent: the contract prose sits in §8.5 beside its dangling
  sibling, and §11 row 28 carries the mechanical-contract entry. If
  you want a numbered interstitial step instead, say the word.
- **§11 rows 27–28 were added although the brief named no rows for C.**
  Session B's precedent (row 26) plus §11's own "full list" claim
  argued for them; the code comments and refusal docstrings
  cross-reference the rows. The asymmetry this creates — session A's
  apply-side dangling refusal still has no row — is proposed below
  rather than backfilled from C's lane.
- **Divergence is one refusal covering three shapes**: hash mismatch,
  a retargeted stamp path, and a null stamp beside a now-configured
  checkpoint. All three are "the oracle changed between pack and
  apply"; the refusal text names which 'before' it saw.
- **The removed-oracle case logs loudly, does not refuse.** An object
  stamp beside a now-unconfigured project has no about-to-run bytes to
  verify — the brief's verification is defined on "the base-tree bytes
  about to run" — and disabling the oracle via config is exactly the
  bale.toml residue D5 accepts at v1 (in-flight removal is impossible;
  apply reads config from the repo working tree). The attempt
  validates worker-only with a loud note naming the removal. If you
  read the residue narrower than I did, flipping this to a refusal is
  a ~10-line change in the resolution block's else-branch.
- **The stamp is read from the registry copy**
  (`.bale/sessions/<sid>/manifest.json`), never from anything the
  response tarball carries — a doctored response cannot forge a stamp.
  A missing/unreadable registry manifest degrades to the stampless
  path with a logged note (defense in depth; pack always writes it).
- **`checkpoint_scope_admitted` is a provenance sibling boolean**,
  stamped unconditionally on bale-built blocks (the uniform-shape
  doctrine, `packer="unconfigured"` precedent), rather than a third
  key inside the ratified `{path, sha256}` stamp object. Handoff-built
  requests stamp `false` (no flag surface there, deliberately).
- **The pack-side dangling refusal fires at pack pre-flight, pre-sid**
  — reading D5's "caught earlier" at the earliest sensible point, so a
  broken oracle reference never opens a session doomed to refuse at
  apply. The provenance builder re-checks at stamp time as defense in
  depth for the handoff path.
- **The dry-run rider was extended to predict the divergence refusal**
  (and, with `--accept-checkpoint-change`, to log the would-be
  admission). Same pattern as B's sanctioned dangling prediction; the
  verification is manifest-and-git-read-only, so a dry-run can
  honestly predict it. Gated on a configured checkpoint, so
  unconfigured projects' dry-run stays byte-identical.
- **One coordination rider landed with the schema change** (the
  session-B "with the gate, not after it" species): the response
  manifest's `feedback.mechanical.provenance` echo is
  `additionalProperties: false`, so without widening it, every post-C
  response echoing a stamped request's provenance verbatim — as the
  contract instructs — fails schema validation. The echo (and the
  lint's embedded copy, kept JSON-equal per the embed guard) gained
  the same two optional keys.

## Look closely on review

- `bin/bale_apply.py`, the checkpoint resolution block: the
  verification's three-way outcome (`checkpoint_stamp_matched`
  true/false/None) and its threading into the D4 stamp. The
  no-checkpoint and no-stamp paths are behavior-preserving by
  construction (the new branches fire only when a stamp key exists) —
  worth a glance to confirm you read it the same way.
- `bin/bale_pack.py`, the two `checkpoint_blindness_preflight` call
  sites: the non-deferred path now names its scope in a local
  (`_early_scope`) so the gate and the blindness check share one
  value; the deferred path runs both post-wizard. Confirm the
  ordering reads as §7.1 step 4b describes (blindness before
  disjointness on both paths).
- Sessions A's and B's fixture edits (`test_blind_checkpoint.py`,
  `test_required_check_gate.py`): the dangling fixtures now configure
  the broken key *after* packing, and the tamper fixture packs with
  `--allow-checkpoint-in-scope` and asserts `stamp_matched is True`.
  These are C-driven contract updates to prior sessions' suites, not
  behavior drift — the docstrings say why.
- Schema diffs: all three schema edits (and the lint embed) are
  targeted text insertions per A's json.dump lesson; the diffs should
  render as insertion-only plus the one stamp_matched description
  replacement.

## Environment notes

- Full baseline ran green in my sandbox before any edit: 192 tests
  (the pack adopted both prior include proposals —
  build.sh/install.sh and tools/craft_response.py — so, unlike A and
  B, nothing was baseline-red and no claim this session is a
  prediction). Final tree: 203 tests green (192 + the new 11-test
  suite). Every claim in the manifest was observed in-sandbox,
  including a full rehearsal of this response's validation.sh.
- `bale.toml` is absent from the shipped tree, as in A and B —
  harmless again; the smoke and test fixtures write their own.

## Proposals

- **A §11 row for session A's apply-side dangling refusal.** What:
  add the missing row for the configured-but-dangling refusal (BALE.md
  §8.5, session A). Why: §11 claims to be the full list of
  mechanically enforced contract; C's rows 27–28 now sit beside an
  undocumented sibling from A, and the asymmetry will read as an
  omission to anyone auditing the table. Scope hints: BALE.md §11
  only; one appended row per the appended-row precedent.
- **Decide the handoff-path covering question.** What: whether `bale
  handoff` should run the covering refusal against its reading-plan
  scope the way pack does (it already gets the dangling refusal and
  the stamp via the shared provenance builder). Why: a handoff whose
  reading-plan set covers the checkpoint re-opens the same self-oracle
  hole layer 1 closes at pack; today it is admitted silently. Rare —
  a bailed session with the oracle in scope must already have been
  admitted once by the flag — but the gap is visible from inside this
  session and worth a deliberate disposition rather than an accident.
  Scope hints: `bin/bale` (cmd_handoff), reusing
  `checkpoint_blindness_preflight`; only after the master decides
  whether handoff should take an admission flag at all.
- **A retry-path E2E for `--accept-checkpoint-change`.** What: a
  fixture that HOLDs an attempt, diverges the oracle, and asserts
  retry refuses without the flag and re-states it with. Why: the flag
  is wired through cmd_retry and the pipeline is shared, so I tested
  the apply side only; the retry wiring is exercised by no test, and
  the lifecycle-wide re-state contract deserves its own pin. Scope
  hints: `tests/test_checkpoint_provenance.py`, following
  test_hold_retry_e2e's HOLD-then-retry scaffolding.
