# notes.md — 2026-10-07-inline-sentinels-and-crafter-b-004

Both fixes landed as the brief drew them, plus the mint. Nothing
surprising in the code; two things worth your eye are the rider's
third comment (left in place, deliberately) and the shape of the
probe-emission pin in `validation.sh`. `bin/VERSION` read `0.4.48`
before I started, so §8's gate was clear.

## Decisions to ratify

- **The tuple's name and placement.** `_SHAPE_SENTINEL_PREFIXES`, a
  four-member tuple directly under `_RELAY_SENTINEL_PREFIX`, in this
  order: `_RELAY_SENTINEL_PREFIX` (the name, not a second spelling of
  `"=== RELAY "`), `"=== PROBE "`, `"=== LIGHT "`, `"BALE EXCHANGE "`.
  Each literal is spelled once in the file; `validation.sh` and the
  unit test both pin that. The comment above it says why the exchange
  prefix covers both `BEGIN` and the bare `BALE EXCHANGE END` line.
  `_inline_lines` is the only consumer; the change there is the
  `startswith` argument and the docstring. The relay prefix,
  `relay_sentinels`, and the four callers are byte-identical to
  0.4.48 (`validation.sh` compares the two declarations' bytes).
- **The exchange prefix is a literal here, not an import.**
  `bale_relay.py` and the crafter each declare `EXCHANGE_BLOCK_BEGIN`;
  `bale_report.py` is the leaf module the others import, and
  `bin/bale_relay.py` is out of scope, so a third spelling it is. See
  Proposals for folding them.
- **BALE.md §8.8 wording.** The sentence now reads: "An inlined line
  that would read as any of bale's four shapes' sentinels — one
  starting `=== RELAY `, `=== PROBE `, `=== LIGHT ` or `BALE EXCHANGE `
  — is indented two spaces, so no output can close a block early or
  read as a probe, light or exchange block of its own to a reader that
  is not span-aware." Rewrapped at the paragraph's width; nothing
  else in the paragraph moved.
- **`-B` only, no `-I`.** The desk's pin, twine's ask verbatim. Both
  emitted invocations are `python3 -B -` with their arguments and
  heredoc delimiters unchanged; the epilogue emission differs from
  0.4.48's in exactly one line and the four-block `--doc-assertions`
  emission in exactly four, which I diffed here against the request's
  context copy of the crafter. `--probe`, `--bundle`, `--emit-block`,
  `--light-block`, the manifest skeleton, `--changes-only` and
  `--apply-only` emit byte-identical output. A why-comment sits
  beside `RECONCILE_EPILOGUE` and in `_doc_assert_block`'s docstring
  (source comments; nothing emitted).
- **The rider: two of three, and the third stays.** The probe-mode
  docstring (your line 116) and the clipboard-key banner (line 374)
  are reworded to say the rule — the key is configurable, never core;
  a machine without one loses only the copy — without the registry
  citation. The third, `# Label column is capped (fold-in: 008's
  accepted proposal)`, is *not* a source comment: it is a line inside
  the `RECONCILE_EPILOGUE` string, i.e. a line of the emitted
  `validation.sh` fragment. Rewording it would change emitted bytes
  and break §2.2's "otherwise byte-identical", so it stays, listed in
  `deferred` and proposed below. The brief said to drop what does not
  fit and say so; this is that.
- **The full suite is gated behind `--slow`.** `validation.sh` runs
  `tests.test_craft_response`, `tests.test_apply_preflight` (the home
  of the `_inline_lines` cases) and `tests.test_changelog_record`
  unconditionally (~85 s here) and the discover-form run only under
  `--slow` (1913 tests, 10–13 min here, green — see Validation below).
  The claim on the `--slow` entry is `pass`/observed from that run;
  without the flag it reconciles `[n/a]`.
- **The probe pin's working directory.** The `--probe` emission reads
  `./bale.toml` or `./context/bale.toml` for the clipboard key, so its
  bytes depend on cwd. The pin in `validation.sh` runs the crafter from
  a config-free directory under the log dir, where the fallback remedy
  text emits, and checks the sha256 against the value the request's
  0.4.48 crafter produces from the same kind of directory. I also
  compared base vs tree from a cwd carrying the staged `bale.toml`
  (identical) but did not pin that one, since it would break on any
  machine whose live `bale.toml` clipboard key differs from the packed
  copy.

## Places to look

- `bin/bale_report.py` lines 895–910: the relay prefix, the tuple and
  its comment; `_inline_lines` at 934.
- `tools/craft_response.py`: the two `-B` lines (`RECONCILE_EPILOGUE`'s
  `python3 -B - "$manifest" …` and `_doc_assert_block`'s f-string),
  and the two reworded comments.
- `tests/test_apply_preflight.py`, `HoldRelayUnitTest`: five new
  methods after `test_inlined_sentinel_lookalike_cannot_close_a_block`.
  Six of the seven new tests across the two suites fail on the 0.4.48
  tree (I ran them against it); the seventh,
  `test_inline_lines_leaves_every_other_line_verbatim`, pins the
  behaviour the brief asked to stay unchanged, so it passes on both.
- `claude/changelog/0.4.49.json`: five surface rows (the three the
  brief names plus the two touched suites, as 0.4.48's record did),
  `at` stamped from bale's UTC clock.

## Validation

Run twice from a staging-shaped copy, cwd at the repo root, with the
filled manifest at `.bale-manifest.json`:

- **Staged (change applied):** exit 0; every check `[PASS]`, the
  `--slow` entry `[SKIP]`; every claim `[agree]`, the skip `[n/a]`.
  No `__pycache__` anywhere afterwards (every Python under `-B`,
  `PYTHONDONTWRITEBYTECODE=1` exported for the suites' subprocesses).
- **Unmodified 0.4.48 base:** exit 1. Failed, as they should: `file
  syntax (py, json)` (no `claude/changelog/0.4.49.json`), `assert:
  bin/VERSION is 0.4.49`, `assert: changelog record 0.4.49`, `assert:
  _inline_lines indents every shape sentinel`, `assert: crafter
  epilogue emits python3 -B -`, `assert: crafter doc-assertions emit
  python3 -B -`, `assert: BALE.md 8.8 names the four prefixes`. Passed
  on both, by design: the three suites (the base runs its own, older
  tests), `assert: relay prefix and relay_sentinels untouched`, and
  `assert: crafter --probe emission byte-identical` — the two
  untouched-surface pins the brief asks for.
- **Whole suite, discover form, on the modified tree:** 1913 tests,
  48 skipped, green, with cache suppression exported. One lesson from
  the first attempt: a discover run *without* `PYTHONDONTWRITEBYTECODE`
  leaves `bin/__pycache__` behind (the suites spawn `bin/bale`
  without `-B`), and `tests.test_clipboard_paste_blocks` then fails
  because it copies `bin/` into a scratch install and asserts no
  caches there. Not this change — the same test is green on a clean
  tree — but it is why `validation.sh` exports the variable rather
  than relying on `-B` alone.

The one-line write announcement at the top of `validation.sh` names
its single write location, `.validation-logs/<stamp>/` under the
staging root (per-check logs plus the crafter emissions under test).

## Proposals

- **Reword the epilogue's in-emission provenance comment.** *What:*
  change `# Label column is capped (fold-in: 008's accepted proposal):`
  in `RECONCILE_EPILOGUE` to state the rule without the citation
  (e.g. `# Label column is capped: one pathological label must not …`),
  and move `tests/test_craft_response.py`'s expectations with it.
  *Why:* it is the last registry citation the carried crafter emits
  into every project's `validation.sh`; this session could not touch
  it under the byte-identical pin. *Scope:* `tools/craft_response.py`,
  `tests/test_craft_response.py`; a session whose brief allows the
  epilogue's bytes to move.
- **`-I` beside `-B` in the emitted heredocs.** *What:* `python3 -I -B -`
  at the same two sites. *Why:* the fragments run from the staging
  root, where a planted `json.py` would shadow the stdlib for the
  reconciliation script; `-I` closes that. The desk pinned `-B` only,
  so this is a follow-up, not a deviation. *Scope:* the same two
  lines and their pins.
- **One home for the exchange prefix.** *What:* have `bin/bale_relay.py`
  read the exchange sentinel words from `bale_report` (or a small
  shared constants module) instead of declaring `EXCHANGE_BLOCK_BEGIN`
  /`_END` itself. *Why:* after this session the repo spells `BALE
  EXCHANGE ` in three places (`bale_relay.py`, the carried crafter,
  and `bale_report.py`'s tuple); the crafter cannot import bale, but
  the two `bin/` modules can share. *Scope:* `bin/bale_relay.py`,
  `bin/bale_report.py`; after this session lands.
