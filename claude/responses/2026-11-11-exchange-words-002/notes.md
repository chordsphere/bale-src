# Notes: 2026-11-11-exchange-words-002 (bale 0.4.58)

Small session, as the brief said. Every outcome landed as pinned. There
are no paths outside the write forecast, no light block was sent, and no
compaction happened.

## Decisions to ratify

- **The relay summary's own next step stays as it is.** That is the line
  after a worker round, `bin/bale_relay.py` `_next_step_trailer`. I went
  with the sitting's guess. The reader of that line is whoever just ran
  bale's relay, so bale's verb is the right one for them. The block is
  different because it travels, and that is where the carrier's relay
  matters. So the rule I followed is: lines bale prints to its own
  operator name bale's verb, and the block, which can leave through
  another tool, names the carrier's verb generically and bale's beside it.
  The new landing trailer follows the same rule. It names bare
  `bale relay`, which outcome 1 asks for anyway. If an office wrapper
  echoes bale's stderr to its own operator, that operator still reads
  `bale relay` in the summary. This session doesn't fix that, and I don't
  think it should: the wrapper owns its own words.
- **The landing trailer carries no round numbers.** The header line puts
  them in ("round 2, answers[] keyed question_round 1"). I could have
  passed the preserved round into `print_clarification_banner`, but the
  trailer points at `bale relay <sid>` alone, and that prints the block
  whose header already carries the exact rounds. One home for those
  numbers seemed better than two. This also leaves the printer's
  signature alone.
- **The trailer is a function now.** `clarification_next_step_trailer(sid)`
  in `bin/bale_report.py` (additive) holds the words. That way the tests
  and `validation.sh` can check them without capturing stdout, and
  `print_clarification_banner` calls it.
- **The retired phrase is gone from the source too.** Outcome 1 only
  binds what bale prints. Still, a checkpoint or reviewer grepping
  `bin/bale_report.py` for "worker's chat" now finds nothing. The
  docstring that explains the history says "the worker's own chat
  session" instead. The two `bin/bale_apply.py` comments the brief named
  are rewritten to describe the thread and `bale relay`.
- **The dry-run's next step is two lines.** "answer the questions as an
  exchange record (from: planner), then", followed by the relay line
  aligned under the value column. The relay line is copy-paste whole on
  its own line, the same as at the landing.

How the landing's trailer reads now, for sid S:

```
  Next step:
    answer the questions as an exchange record (from: planner), then
    bale relay S <answer.json|->
    records it and emits the worker's block; the worker's follow-up
    response then applies against this same session
    (`bale relay S` alone prints the exchange block to carry;
    `bale unlock` and repack if the gap invalidates the request)
```

## Look closely at

- `bin/bale_report.py`, `clarification_next_step_trailer`, and the
  clarification branch of `format_dry_run_report`.
- `bin/bale_relay.py` and `tools/craft_response.py` `format_exchange_block`,
  the one changed string in each. The parity suite
  (`ExchangeBlockParity`) and the new suite both compare the two by
  execution.
- `BALE.md` 8.11 gains one paragraph on the header line. I left
  TARBALL.md alone. Its 5.9.4 already describes the answer path, and
  nothing in it quotes the header's words, so there was no reason to move
  a contract-doc hash.

## Validation

`validation.sh` runs the session assertions and nine targeted unit
modules, about 95 seconds in total. The whole suite runs only with
`--slow`. I ran that whole suite on the changed tree in this sandbox:
2147 tests, 48 skipped, no failures, in about 9 minutes. This request
carried README.md, bale.toml and claude/context/adr, so the six failures
the last session saw for missing files didn't come up. I also ran the
script twice, once on a staged copy with the change applied and once on
the unmodified tree. Every session assertion passes on the first and
fails on the second. The script's only writes are its own
`.validation-logs/` and the tests' scratch dirs under `$TMPDIR`.

## Walkthrough

### What changed

- **The landing's next step** (`bin/bale_report.py`). When `bale apply`
  lands a clarification, the `[CLARIFICATION]` banner's trailer used to
  say "answer the questions in the worker's chat". Now it says to answer
  as an exchange record from the planner, then gives the line
  `bale relay <sid> <answer.json|->` with the real sid. It adds that
  `bale relay <sid>` alone prints the block to carry, and that unlock and
  repack is still the recourse.
- **The dry-run's next step** (same file). `bale apply --dry-run` on a
  clarification says the same, with the same relay line.
- **The block's header** (`bin/bale_relay.py`, `tools/craft_response.py`).
  The planner-facing header line ends "and record it with the relay of
  the tool that carried this block (bale's own:
  `bale relay SID <answer.json|->`)." Both renderers say it byte for
  byte. The worker-facing line didn't change.
- **Comments and the contract** (`bin/bale_apply.py`, `BALE.md` 8.11).
  The two comments that described the old step are rewritten, and 8.11
  says why the header names the carrier's relay.
- **The release.** `bin/VERSION` 0.4.58,
  `claude/changelog/0.4.58.json`, and a new suite,
  `tests/test_exchange_words.py`.

### Why

- The old landing words sent the planner to chat to answer a blocking
  question. TARBALL.md 5.9.1 calls that the breach case: an answer given
  in chat is never recorded on the thread. bale's own docs already said
  the next step is `bale relay`, and `bale status` already said so too,
  so the landing was the odd one out. That was the founding slip.
- The header told every planner to run `bale relay`. A planner who got
  the block through a wrapper (`office relay SID FILE`) was told the
  wrong verb. bale can't know the wrapper's name, so the header says
  "the relay of the tool that carried this block" and keeps bale's own
  for anyone who uses bale directly. That was the occupant's slip of
  2026-11-03.

### How to explain each piece

- The landing: "When a worker asks a question, bale now tells you to
  answer it through bale relay, and gives you the exact line to paste."
- The dry-run: "A rehearsal says the same thing the real landing would."
- The header: "The block you paste somewhere says to use whatever tool
  carried it to you, and still shows the bale command in brackets."
- Nothing else moved. The header isn't part of the checksum, so blocks
  from before and after this release ingest the same way.

### Questions a reviewer will ask

- *Does the header change break pasting old or new blocks?* No. The
  trailer hashes only the body. The new suite feeds a crafter-rendered
  block through `bale relay <sid> FILE` and checks that it's kept as
  round 1.
- *Why not name office's verb?* bale never reads office's consumption
  manifest, so it can't know the name. The brief settled this before the
  session.
- *Why does the relay's own summary still say `bale relay`?* Its reader
  just ran bale's relay. See "Decisions to ratify".
- *Is the exchange block printed at the landing now?* No. That's the
  next session's (clipboard). For now the trailer points at
  `bale relay <sid>` alone, which prints it.

### A hand test

1. In a scratch repo with this bale, pack a session and run
   `bale apply <clarification tarball> --dry-run` for it. The
   "next step:" should name `bale relay <your sid> <answer.json|->` alone
   on its line, and the phrase "worker's chat" should be nowhere.
2. Run the same apply for real. Read the bottom of the output: the
   trailer should show the same relay line, and still no "worker's chat".
3. After the real apply, run `bale relay <your sid>` with no file. Look
   at the block's second line: it should read "... and record it with the
   relay of the tool that carried this block (bale's own:
   `bale relay <your sid> <answer.json|->`)." and end with a period after
   the closing bracket.
4. If office wraps the relay on your machine, check that the paste reads
   sensibly to someone who has only office in front of them.

## Handbook

### bale-src

- Since 0.4.58 a clarification's landing and its `bale apply --dry-run` name the answer step as `bale relay <sid> <answer.json|->` with the real sid; `bale relay <sid>` with no file prints the landed round's exchange block.
- Since 0.4.58 the exchange block's planner-facing header line says to record the answer with the relay of the tool that carried the block, naming bale's own `bale relay <sid> <answer.json|->` beside it; the header is not hashed, so blocks from either side of the release ingest alike.
- A request that carries README.md, bale.toml and claude/context/adr beside bin, tests and tools runs the whole unit suite clean in a worker sandbox: 2147 tests, 48 skipped, about 9 minutes.

#### Front sheet

bale-src is the source of bale, the occupant's command-line tool for
handing work to an agent session and taking the result back. bale packs
a request tarball, carries the worker's questions and the planner's
answers through `bale relay`, checks the response tarball the session
returns, and lands it on a branch in the project only after validation
passes. On 2026-11-11 it stands at 0.4.58 once this session lands, the
second of eleven releases planned in folder 43 for the slips about bale.

## Structure

- title: Fix bale-src for the slips about bale, in eleven sessions
- size: high
- goal: Land the fixes to bale-src for the slips about bale in the office's suggestion box, one release per session, in the ratified order
