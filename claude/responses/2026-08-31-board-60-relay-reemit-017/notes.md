# notes — 2026-08-31-board-60-relay-reemit-017

## This is the retry (corrects the first response-017)

The first attempt HOLDed on two validation.sh bugs of mine, not on
the change set (the blind checkpoint passed; the diff is unchanged
in this retry): `assert_grep`/`assert_absent` referenced `$label`
without assigning it, so `set -u` killed the script at the first
assertion; and the unittest invocation used the `tests.test_relay_verb`
form, whose import of the suite's top-level `harness` module doesn't
resolve from the staging root — the discover form (`-m unittest
discover -s tests -p 'test_relay_verb.py'`), the suite docstring's
second run line, puts `tests/` on sys.path and is what validation.sh
now runs. `manifest.corrects` names the replaced response; the
claims key follows the renamed check identifier. This retry's
validation.sh was smoke-run end to end against an assembled staging
copy before packing (assertions, exec-bit, epilogue all exercised;
only the test run itself still needs the full tree's sibling
modules).

## Out-of-forecast paths (admit at apply)

- **`bin/VERSION`** — 0.4.21 → 0.4.22. The goal ships a behavior
  change to a released verb, and the brief said to take the bump if
  house practice calls for it; it does (board 59 bumped for a
  behavior-*preserving* extraction, so a behavior change clearly
  qualifies). The file wasn't in the forecast or the shipped context;
  admit it with `--allow-out-of-scope bin/VERSION`. I wrote it as
  `0.4.22\n` on the assumption the live file reads `0.4.21` (the
  request's provenance says so). If the live version has moved past
  that, kick this path back and I'll re-stamp.

## The one assumption to check first

**Re-emit byte-identity assumes `preserve_clarification_record`
preserves key order.** For an exchange-record round, re-emit
re-serializes the preserved `NNN.json` (minus the `preserved_at`
sidecar) through the same renderer the original emission used.
That's byte-identical iff the preserved file's key order matches the
ingested record's — `bin/bale_apply.py` wasn't in the shipped
context, so I couldn't read the write side. The shipped test
`test_reemit_record_round_is_byte_identical` pins exactly this
end-to-end, so if the preservation write sorts or reorders keys,
validation fails there rather than shipping a silent mismatch.
(Manifest rounds are immune: their re-emit re-normalizes through
`_normalize_manifest_to_record`, whose key order is fixed in code.)

## Judgment calls

- **The contract sentence landed in §5.8**, the relay verb's usage
  section — my reading of "the relay verb's documentation in
  BALE.md". §8.11 (the contract) got its own re-emit paragraph in
  contract voice rather than a second copy of the sentence. Move it
  if you meant §8.11.
- **Session gates stay on the no-file form.** The ruling was "the
  existing relay verb's file argument becomes optional", so the
  no-file form runs the same open-and-unbranched gates before
  re-emitting; a closed session's thread stays history. The brief's
  only specified refusal (no recorded rounds, naming the sid) is
  additional to those, not a replacement.
- **No new §11 row.** The no-rounds refusal rides as a sentence
  appended to row 34 (the relay pre-flight row) rather than a row
  36 — the re-emit form ingests nothing, so a separate ingest-gate
  row felt wrong. Strike the sentence and mint a row if you want it
  mechanically enumerated on its own.
- **`[RE-EMITTED]` status.** The re-emit summary uses a distinct
  status string so a transcript never reads as if a round was
  recorded. I'm assuming `format_summary_block` accepts an arbitrary
  status label (its call surface suggests so; `bale_report.py`
  wasn't shipped). The new tests assert the string, so a stricter
  renderer surfaces at validation.

## Rider dispositions

1. **Include-group mention (board 64):** §7.5's walk step got the
   one sentence. §7.7 already carried its mention ("The
   include-group row", board 64) — no change there.
2. **§7.2 forecast true-up (fold-in registry):** six word-level
   substitutions confined to the `--read-only` and `--supersedes`
   bullets ("empty recorded scope" → "empty write forecast",
   "scope locks nothing"/"own-scope drift" → forecast vocabulary,
   "recorded scope `[]`" → "recorded forecast `[]`", "scope
   collides"/"scopes … disjoint" → forecast). Session B's sweep had
   already fixed the includes bullet, and §7.1/§7.4 were clean. This
   is more than two *edits* but no sentence was restructured; I
   judged it inside the rider's "small" and shipped it rather than
   deferring — say so if you'd rather it had been split out.
3. **Section-29 citations (board 59):** only §8.11's block
   provenance line was stale; it now cites `bin/bale_relay.py`
   (extracted v0.4.21). Row §11.34 and the §5 verb inventory never
   cited section 29 — nothing to true up there.

## Proposals

- **What:** A TARBALL.md doc-touch mentioning the re-emit form where
  §5.9.2/§5.9.4 describe `bale relay <sid> <file|->`.
  **Why:** The global docs were out of scope this session, and their
  relay mentions, while still accurate for the recording flow, now
  under-describe the verb; a lost-paste worker or planner reading
  only TARBALL.md won't learn re-emit exists.
  **Scope hints:** global docs, so a bale-repo session per CLAUDE.md
  META; TARBALL.md §5.9.2 and §5.9.4, one sentence each.
- **What:** Teach `bale status`'s clarification next-step hint to
  mention `bale relay <sid>` as the lost-paste recovery.
  **Why:** The hint currently only names the recording invocation;
  the re-emit form is precisely for the operator staring at status
  wondering how to regenerate a block. Noticed while checking the
  status-hint strings in `bin/bale` (§ around `lock_sid` hints);
  left untouched as outside the goal.
  **Scope hints:** `bin/bale` status/report strings; tiny.
