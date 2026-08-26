# Notes — 2026-08-26-board-53-amend-checkpoint-004

## The clarification round (resolved in chat, pre-build)

One blocking gap, raised and ruled before any code was written
(provenance per TARBALL.md §5.9.1: the round happened on the
conversational channel, not the wire, so this section is its durable
record; the manifest's `linkage` member points here).

**The question.** Outcome contract 4 — "never silently replace:
differing committed bytes refuse loudly naming both sides; identical
bytes are the idempotent re-run" — read literally against the
working-tree/HEAD state would refuse *every* amendment, since the whole
point is that the committed bytes differ from the delivered ones. I
offered two readings: (a) the rung binds the working tree only, or (b)
the rung is an *accounting* rung against the session's pack-time
`provenance.checkpoint` stamp — committed == stamp is the amendment
proper, committed == delivered is the idempotent re-run, committed
matching neither refuses. I recommended (b).

**The ruling: (b)-as-adjusted.** The accounting rung is the intended
referent, ratified with one adjustment: the matching-neither refusal
names a **per-invocation accept flag** as its successor, not a desk
direct-commit remedy — because amending-an-amendment is observed
(evidence 66: one board-10 wave-3 session amended its oracle twice),
and refuse-by-default-with-a-named-override is the house pattern for
deliberate exceptions. On accept: proceed, FORCE-logged, naming all
three hashes (committed, pack-time stamp, delivered). Never silent
either way. One covered edge, ruled in the same breath: a stampless
request (key absent, or the explicit-null stamp of a no-checkpoint
pack) leaves the rung nothing to account against — degrade to the
published-hash deliberateness alone, loudly, per the provenance gate's
own "verify nothing, `stamp_matched: null`" precedent (BALE.md §8.5).

All of that is implemented as ruled. Flag spelling (left to me):
`--accept-unaccounted-oracle` — it names exactly what is being
accepted, the replacement of committed oracle bytes the flow cannot
account for. I deliberately did not reuse `--accept-checkpoint-change`:
the events are near-identical but the consequences differ (run current
bytes vs. replace them), and one spelling with two per-verb semantics
seemed like a trap.

## Judgment calls (latitude the ruling accepted; mechanism notes)

- **Module home**: the verb lives in `bin/bale` as new section 28,
  physically between 20 (Retry) and 21 (Unlock), beside the lifecycle
  verbs — a fresh number per the stable-numbering rule the 26/27
  ordering already exercises. Consequence, accepted in the ruling: the
  new-module riders (scripts/build.sh RELEASE_FILES, install.sh
  INSTALL_LAYOUT) do not fire, and those files are untouched.
- **Stamp accounting requires both halves**: committed bytes are
  "accounted as the pack-time oracle" only when the stamp's `path`
  equals the session's resolved path AND its `sha256` equals the
  committed hash — mirroring the provenance gate's own match rule. A
  stamp naming a different path (a post-pack base reconfiguration)
  therefore lands in the unaccounted branch and refuses without the
  flag, which I take to be the conservative side of the ruling.
- **Working-tree rung**: distinct from the accounting rung —
  uncommitted bytes at the resolved path matching neither HEAD nor the
  amendment refuse (local edits are never clobbered); bytes == HEAD is
  the normal checked-out state; bytes == the amendment is a hand-copy
  already in place and proceeds.
- **Idempotence short-circuits accounting**: committed == delivered
  returns success (no commit, successor still emitted) *before* the
  stamp is read — an aborted re-run stays idempotent even if the stamp
  is odd, matching the contract's "identical bytes are the idempotent
  re-run" as stated.
- **Successor pre-composition**: the trailer's last line is the
  complete `bale retry <response-tarball> --accept-checkpoint-change
  --sid <sid>` — ratified deliberately in the ruling (the stamp
  mismatch holds by construction post-amendment; the deliberateness was
  spent at this verb's invocation). The `<response-tarball>`
  placeholder stands; the bare-retry successor-parity item is in
  Proposals below, per the ruling's pointer.
- **Read path**: resolution is the shared `locate_inbound_path` core
  over `apply.search_paths`; the read posture and refusal wording are
  the verb's own (the per-surface split pack's `--checkpoint-file`
  established), with `normalize_crlf` imported from `bale_pack` so the
  two ingest edges share the one board-50 implementation. The
  hash-mismatch refusal names the resolved source path — the
  evidence-45 stale-near-duplicate catch.
- **Hash shape gate**: `--sha256` must be the full 64 hex characters;
  a truncated paste is the transport defect the mandatory hash exists
  to catch, refused before config or registry reads.
- **Resolution rule**: candidates are open sessions whose recorded
  forecast is not the deliberate `[]` — read-only sessions are
  structurally invisible (their pack waived the checkpoint), while a
  missing/malformed scope record reads conservative whole-tree per
  `read_session_scope` and *stays* a candidate. Two-plus candidates
  refuse naming all, oldest first; `--sid` picks, vetted (must be open
  and scoped; naming a read-only session refuses with the waiver
  named).
- **No `--json` on the verb** in v1 — the surface the brief asked for,
  nothing more; parity noted in Proposals.

## Disclosures

- **Index-header true-up**: `bin/bale`'s docstring section listing had
  pre-existing drift well past the 50-line threshold (e.g. section 19
  listed ~1470, actually ~1720) before this session touched the file.
  Adding section 28's row per CODE.md §2.2 while leaving knowingly-off
  neighbors felt wrong, so the listed numbers for sections 19–26 were
  refreshed in the same edit. Docstring-only; no behavior.
- **Sibling docstrings**: `bale_pack.py` and `bale_apply.py` are
  docstring-only edits (each module's stated "public surface consumed
  by bin/bale" gains the one name this verb imports). Flagged so the
  diff reads as intended: no code moved in either file.
- **Validation runtime**: ~100s end to end, dominated by the 601-test
  default-gated suite — inside the §7.6 two-minute target but with
  little headroom. The full suite (rather than a scoped subset) is
  deliberate: the change touches the dispatcher file every verb loads.
- **Compaction**: the assistant-side context was compacted mid-session
  (after implementation and testing, before response assembly), per
  the standing disclosure rule. All build steps and their observed
  results are in the transcript; the response was assembled against
  the on-disk state, with every hash recomputed from bytes at pack
  time, not recalled.

## Riders deliberately not fired

- scripts/build.sh / install.sh: no new `bin/` module (see above).
- The `bale_open.py` FORCE-prefix-doubling nit (its `log("FORCE: ...",
  force=True)` double-prefixes) sits in a file outside this change set
  and stays in the queued-nits registry; section 28's own FORCE lines
  pass bare text to `force=True` and render single-prefixed.

## Proposals (not this session's scope)

- **Bare-retry successor parity** (deliberately-unscheduled registry
  item, per the ruling): a `bale retry` form that resolves the held
  attempt's tarball from session state would let amend-checkpoint emit
  a placeholder-free successor line.
- **`--json` parity for `amend-checkpoint`**, if the verb turns out to
  be scripted against: the summary block is stable, so the usual
  `format_*_json` docstring-owned contract would fit.
