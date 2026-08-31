# notes — 2026-08-31-board-58-exchange-constants-parity-016

Two judgment calls worth ratifying, one subtlety, one proposal.

**Which constants the parity row compares.** bale_relay.py's docstring
names its shared vocabulary as exactly five module-level constants —
`EXCHANGE_BLOCK_BEGIN`, `EXCHANGE_BLOCK_END`, `EXCHANGE_TRAILER_LABEL`,
`EXCHANGE_SIDE_WORKER`, `EXCHANGE_SIDE_PLANNER` — and those are the only
exchange constants both homes declare. The crafter's wider set
(`EXCHANGE_SIDES`, `EXCHANGE_RECORD_VERSION`, `EXCHANGE_BODY_INDENT`,
`EXCHANGE_ENVELOPE_KEYS`, the answer/question vocabularies) has no
module-level counterpart in bale_relay.py — those re-declare
bale_validate.py's structural rules and the body-serialization
parameters, which the bale-src byte-parity suite pins. So the row
compares the five, mirroring how the existing bundle-constants row
compares exactly the pair both homes carry. If you wanted the row to
also reach into bale_validate.py's vocabularies, say so and I'll extend
it in a follow-up.

**Row placement.** The three presence rows sit in INSTALL_LAYOUT order
(sandbox after staging; open and relay after `_bale_toml`), with a
true-up comment in the same voice as the v0.4.12 schema-loop comment
above them. The parity row sits inside the existing
`tools/craft_response.py` block, immediately after the bundle-constants
guard it generalizes.

**A stale-bytecode subtlety in validation.sh's fixture check.** The
drift half of the fixture check edits `sha256` → `sha512` — a
same-length change — and Python's pyc invalidation keys on source mtime
and size. Two fixture runs inside the same second with a same-size edit
between them reimported the stale bytecode and the drift went unseen, so
the fixture drops its `__pycache__` after the edit. The shipped
validate.sh row itself is not affected in practice (a real install's
craft/relay files don't get same-second same-size rewrites between
validate runs), but I flag it since you'll see the `rm -rf` line and
wonder.

## Proposals

**True up craft_response.py's re-declaration citation.** The comment
block above its exchange constants still says the vocabulary is
"RE-DECLARED from `bin/bale` section 29", but the v0.4.21 extraction
(bale_relay.py's own docstring) moved section 29 into
`bin/bale_relay.py`. Why: this session added an install-side check whose
remedy text points at bin/bale_relay.py, so the two prose homes now name
different sources for the same constants; a reader following the
crafter's citation lands in a bin/bale section that no longer exists.
Scope hints: `tools/craft_response.py` comments only (and possibly the
matching citation in tests/test_craft_response.py); out of this
session's forecast, which is validate.sh alone.
