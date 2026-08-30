# notes — 2026-08-29-exchange-relay-003

Everything the brief asked for is in, plus the five sitting rulings as
you gave them. Below: where the brief and the tree disagreed, the
choices I made past D4, the one out-of-forecast path, what I could not
observe, and two proposals.

## Where the brief and the bytes disagreed

- **"amend-checkpoint has its own module."** It does not — in the
  shipped tree it is `bin/bale` section 28, inline, with `bale_open.py`
  the most recent *module* precedent. I followed the bytes: relay is
  section 29 of `bin/bale`, physically after 28 and before 21, fresh
  number, header listing updated. The deciding fact was not doctrine
  but reach: a new `bin/*.py` must join `install.sh`'s
  `INSTALL_LAYOUT` and `build.sh`'s `RELEASE_FILES`
  (`test_release_packaging` pins that coverage), and neither file was
  shipped. Extracting later is mechanical — see Proposals.
- **"validate.sh already walks schemas/*.json."** It walks an explicit
  list, not a glob, and its own comment says a session adding a schema
  extends the list in the same change. That is the `validate.sh` line
  below.
- **"INDEX.md lists the schema in the Schemas category."** There was no
  Schemas category and none of the six existing schemas were listed.
  Per your ruling: a `## Schemas` category now lists all seven via
  `../schemas/…` paths, with a one-line note that bale-src keeps them at
  the repo root (the installed tool loads them) rather than under
  `claude/context/schemas/` as DOCS.md's default would have it.
- **§8.11 vs the brief:** no conflicts of substance. §8.11 was silent
  on the block's exact layout, on bare-JSON ingest, on CRLF, and on
  what to emit after a manifest ingest; D3–D5 and the sitting decided
  each, and §8.11 now records what landed (the "As landed" paragraph
  and the two additions to step 2). Row 34's wording was trued to the
  landed gate; rows 1–33 untouched.
- **BALE.md §2.2** carries the same "Claude returns a script, the user
  runs it, the user pastes" sentence §6.5 did. I swept both to
  role-only (worker / courier); the brief named §6.5 only. Content
  unchanged either place.

## Choices beyond D4 (each testable, each tested)

- **Round one gate scope.** "Open sid, no `bale/<sid>` branch" is
  enforced before the input is read: a sid not open refuses naming the
  open ones; a held branch refuses naming the retry/revert path.
- **Two gates in the library validator that the schema cannot
  express** beyond the ones D3 names: `created_at` must parse as ISO
  8601 *with a zero UTC offset* (`Z` accepted; naive and non-UTC
  refused — the thread is compared across machines), and an answer's
  `question_round` must be earlier than the record's own round (it can
  never resolve otherwise). The thread-level resolvability check you
  ratified lives in relay, where the thread is.
- **What a manifest ingest preserves and emits.** Preserved: the
  manifest untouched plus `preserved_at` — byte-shape identical to
  apply's handler, because both now call
  `bale_apply.preserve_clarification_record`. Emitted: the normalized
  record (your item 5), which the E2E test re-validates.
- **Stream discipline.** stdout is exactly the block, always;
  `[bale] ` lines and the `[RELAYED]` summary go to stderr via the
  existing `enable_json_mode` rebinding, with a new `emit_stdout_block`
  beside `emit_json_line`. There is no `--json` on relay (the option
  surface is closed); if you want a machine report line later, the
  mechanism is already in place.
- **Block layout.** `BALE EXCHANGE BEGIN <sid>`, three `#` header
  lines (direction+round; what the record carries and what the reader
  does next; body/trailer note), the record's JSON (indent 2, ASCII-
  escaped so no transport can mangle it), `# sha256 <hex>` over the body
  bytes, `BALE EXCHANGE END`. Ingest CRLF-normalizes, reads only the
  sentinel span (fence lines and chat prose around it are ignored —
  tested), refuses a BEGIN sentinel naming another sid before parsing
  the body, and accepts bare JSON when no sentinel is present.
- **Status wording.** The row keeps the v0.3.22 substrings the existing
  test pins (`round N`, `N blocking question(s)`) and adds
  `from <side>: … ; awaiting <side>`; the hints keep "answer the
  questions" and "bale apply" on the planner-side state so
  `test_clarification_status` still passes unchanged. The
  unreadable-latest case gets its own description and a hint that still
  names relay and apply — never the orphan reading.
- **Telemetry `answers`** is null (not 0) when a record carries no
  `answers[]` at all, so every pre-thread manifest stamps null and
  aggregation can tell "asked only" from "answered nothing".
- **`from`'s closed-vocabulary walk** is record-wide like `priority`'s.
  A consequence worth knowing: a question row or answer text is a
  string, so nothing legitimate nests a `from` key — but a future
  additive object field named `from` would trip it. Same trade the
  escalation record already makes.

## Out of forecast — please admit at apply

- **`validate.sh`** (repo root) — one token added to the schema list
  (`exchange-record`). Reason above; ratified at the sitting (item 2).
  Also declared in `feedback.self_reported.forecast_departures`.

Nothing else left the forecast (`BALE.md`, `bin/`, `claude/INDEX.md`,
`schemas/`, `tests/`). `tools/` and `docs/` untouched.

## What I could not observe

- **The full suite.** 662 tests, 41 skipped (slow gate), and exactly
  the 10 `test_release_packaging` errors that come from `install.sh` /
  `build.sh` not being in the shipped context — every one of them is
  the file-read, none is an assertion. No new `bin/*.py` was added, so
  the lists those tests read are unaffected. Claim: `pass`,
  `predicted`.
- **INDEX coherence.** The crafted `--index claude/INDEX.md` block
  passes only if `claude/MASTER.md` and the three explainers exist in
  the tree; they weren't shipped, so I observed the pass with them
  stubbed. Claim: `pass`, `predicted`.
- The schema walk and the session assertions were observed passing in
  a staging simulation (files overlaid, apply.sh run, manifest at
  `.bale-manifest.json`).

## Test inventory

- `tests/test_exchange_record.py` — 30 tests: the library validator
  and the schema/constant/`$ref`/validate.sh parity.
- `tests/test_relay_verb.py` — 22 tests: the verb end to end, one
  fixture per refusal, plus the round-trip of relay's own block.
- `tests/test_thread_status.py` — 9 tests: status after each side,
  the unreadable-latest degradation, the close-time summary through a
  real `bale unlock` (validated under the telemetry schema), and the
  pure classifier/formatter.

Existing suites are untouched and green; `test_clarification_status`'s
pinned substrings still hold against the new wording by design.

## Proposals

- **Extract section 29 into `bin/bale_relay.py`.** What: move
  `format_exchange_block`, `parse_exchange_input`,
  `read_exchange_thread`, `unresolved_answers`, and `cmd_relay` out of
  `bin/bale` into a sibling module on the `bale_open.py` pattern. Why:
  `bin/bale` is past 6,400 lines and section 29 is a self-contained
  subject with one caller; the only reason it is inline is that
  `install.sh` and `build.sh` were out of reach this session. Scope
  hints: `bin/`, `install.sh`, `build.sh`, and
  `tests/test_release_packaging.py`'s coverage list — one session, and
  only after the crafter sibling lands, since it will import
  `format_exchange_block`'s layout (or duplicate it, which is the
  drift this extraction would prevent).
- **Give `bale relay` a re-emit path.** What: a way to reprint the
  latest round's block without re-ingesting (a courier who lost the
  block today has to reconstruct it from `NNN.json` by hand). Why: the
  status hint after a planner record says "carry the block", and the
  block exists only on the stdout of the relay that made it. Scope
  hints: this widens the option surface ADR-0017 closed at
  `<sid> <file|->`, so it needs a doctrine ruling before code — a
  candidate is reading `round`-only input, or a separate read-only
  verb. Not started.
