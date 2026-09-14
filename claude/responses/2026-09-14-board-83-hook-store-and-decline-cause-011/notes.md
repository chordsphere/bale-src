# notes.md — 2026-09-14-board-83-hook-store-and-decline-cause-011 (retry)

## Why this is a retry

The first response HELD: worker validation passed, the blind
checkpoint failed three of its seven assertions — `bin/bale lacks:
declined (stdin closed or interrupted); not invoking.` and its two
siblings. The checkpoint greps `bin/bale` for the three *rendered*
decline lines; I had shipped the parenthetical wording as constants
and assembled `declined (…); not invoking.` at runtime, so the
literal lines were not in the file. The terminal output was already
correct (the suite pinned it), which is exactly the case a blind
checkpoint exists to catch: my `validation.sh` was written to my own
reading of "the three cause phrases exist in bin/bale" and passed
against it.

The fix is structural, not a string swap: `ConfirmDecision` now
reports `decline_branch` (one of three `CONFIRM_BRANCH_*` names) and
the hook section owns `HOOK_DECLINE_LINES`, the three lines held
literally and keyed by branch; `run_hook` renders from that map. Other
callers get the branch and phrase their own line (a bare-apply confirm
would not say "not invoking"), which is the same division the first
shape had, minus the assembled-at-runtime wording. `validation.sh`
now asserts the rendered lines, the way the checkpoint does. Nothing
else changed; `bin/bale_config.py` and the test suite ship the same
bytes as the held response.


Bumpless: `bin/VERSION` untouched, the apply-side session carries
0.4.29. Every `changes[]` path is inside the write forecast — no
out-of-forecast work, no drift to admit. Nothing shipped onto
`bin/bale_apply.py`, `bin/bale_report.py`, or `bin/VERSION`
(`validation.sh` asserts that from the staged manifest).

## The process breach, first

I did not use the clarification path when I should have. With the
reading done and two decisions left that the brief hands to the desk
— `--json` on the verb, and where its tests live — I put both in
chat as a two-button question and only produced the clarification
tarball when you sent me back for it.

Why: I read them as preference-shaped rather than blocking. The brief
gave a default for each ("plain text is fine and says so"; "a new
suite is your call"), so I reached for the lightweight §5.9.1 path —
a question in chat, proceed on the named assumption. That reading was
wrong on its own terms: the test is *blocking*, not *size*, and both
answers change the shipped surface (a public CLI flag; which file
carries the coverage, with different admission consequences at
apply). I even wrote "the brief explicitly hands the choice to the
desk" in the `why_blocked` field once I did build the artifact —
which is the tell that I knew it was the desk's decision and asked
in chat anyway. §10.1 step 2 is explicit that asking in chat leaves
the session's `clarification.rounds` telemetry reading zero against
a real round; that is the concrete cost, and it is why the record
below exists.

The exchange, for the record (§5.9.1's fallback rule): round 1 asked
the two questions above with recommendations "plain text" and
"extend `test_hook_acceptance.py`"; round 2 answered `free-text` on
the first — **ship `--json`**, one line on stdout with the rest on
stderr, status-shaped, because the discipline that matters is
bale_report's process-wide one — and `as-recommended` on the second.
Both are what shipped. Since the thread did go through `bale relay`
in the end, the telemetry should carry one round; the breach is that
it nearly carried none.

## What landed, and the calls I made (flagged; ratify or correct)

- **`confirm_yn` keeps its bare `bool`.** `bale_pack.py` stores the
  result in `accepted` and feeds it onward, and `bale_apply.py` is
  the sibling session's file, so changing the return type was never
  on the table. The shape is a new `confirm_yn_decision()` returning
  a frozen `ConfirmDecision` (accepted, answer, stdin_closed,
  default_no; `.decline_branch` names the branch), with `confirm_yn`
  reduced to `.accepted` over it. Every existing caller is
  byte-for-byte unchanged in behavior; only `run_hook` reads the
  cause. The other callers — bare-apply confirm, drift admission,
  supersession y/N, read-only sweep — can adopt it when their owners
  want the cause (Proposals).
- **The three lines are literal** in `HOOK_DECLINE_LINES` (see the
  retry note above). The third is a template over the operator's
  stripped, lowercased answer, rendered with explicit single quotes
  — not `!r`, which would switch to double quotes on an answer
  containing `'`. A stray `  NO ` therefore logs as `answered 'no'`
  (pinned).
- **The EOF branch is `stdin_closed`, not an empty answer.** The two
  empty-answer cases (EOF vs Enter) are distinguished by that flag,
  not by the text, which is what makes "Enter at a decline default"
  and "stdin closed" two branches rather than one.
- **`--forget` does not prompt.** The operator named the hash; the
  verb prints what it removed (full sha256, hook, layer, accepted-at,
  script path) and then the survivors under `remaining:`.
- **Prefix resolution.** Input is case-insensitive hex, 1–64 chars;
  anything else refuses as a typo (`ValueError`) rather than as a
  missing key, so `--forget not-a-hash` doesn't read as "nothing
  remembered". No minimum prefix length — a one-character prefix that
  matches exactly one key is a legitimate unique prefix. Ambiguity
  names every match with its hook and script; missing points at the
  bare listing. Both refuse via `fail()` — stderr, exit 1, nothing on
  stdout — so a `--json` consumer never sees a half-report.
- **The listing is oldest-first** by `accepted_at` (missing timestamp
  sorts first, then key order), so it reads as a history.
- **Hand-edited stores are displayed, not dropped.** An entry whose
  value isn't an object shows as `(malformed entry …)` on the listing
  and `malformed: true` in JSON, and `--forget` can remove it. A
  malformed *file* keeps the read path's posture exactly: the
  `[bale]` warning, an empty listing that says the file exists but
  reads empty, and a `--forget` that refuses as missing beneath the
  warning without touching the file.
- **`--json` shape.** `outcome` (`listed` | `forgotten`), `version`,
  `store`, `exists`, `entries` (the store *after* the run — whole on a
  list, survivors on a forget), `forgotten` (null or the removed entry
  in the same object shape). The renderer
  (`format_config_hooks_json`) lives in `bale_config.py` because
  `bale_report.py` is the sibling session's file this sitting; it
  follows the siblings' vocabulary (outcome first, then version) and
  their stability rule. Moving it beside `format_status_json` later
  is a one-function cut (Proposals).
- **No git repo required.** The verb refuses system dirs for cwd
  parity with `config init --global` and otherwise never looks at
  cwd; the E2E tests run it from the scratch tmp dir, not the repo,
  to pin that.
- **The atomic writer is now `write_hook_acceptances`**, factored
  out of `record_hook_acceptance` and shared with forget, so the
  on-disk shape has one home. After the last forget the file stays,
  as `{}` — a present-but-empty store is a state the read path
  already understood.
- **Help/completion needed nothing.** The parser is the registry;
  `bale help config hooks` and `bale completion bash` picked the verb
  and both flags up on their own (validation checks the help
  rendering live).
- **The `response-NNN/` error message at bin/bale:3583** — the
  top-level *directory* name inside a response tarball — is not one
  of the two help strings and is correct as written (TARBALL.md §1:
  the directory stays `response-NNN/`; only the filename carries the
  sid). Left alone.
- **Section 23's header comment** no longer says "decline is silent";
  it says decline is not an error but never silent about why.

## Claims

- `session assertions` — **observed**, rehearsed in a staging-shaped
  copy of the shipped context with `files/` overlaid, `apply.sh` run,
  and the manifest placed as `.bale-manifest.json`.
- `unittest: test_hook_acceptance` — **observed**: 34 tests, ~6s.
- `unittest: full discovery (--slow)` — **predicted**: 69 tests green
  here (the three shipped suites plus harness-adjacent discovery),
  but the repo has more. Anything that pins the bare
  `declined; not invoking` line elsewhere would fail — the shipped
  set had it only in the suite I touched, and the fix would be the
  assertion.
- `validate.sh (install sanity)` — **predicted**: 88/89 here, the one
  failure is "README.md present" (README not shipped in the request —
  same as board 78 reported). Green in your tree.

## Surprises

- The exchange-record schema does not admit the optional `origin` key
  on a question row that `response-manifest.schema.json` does, so a
  clarification manifest that fills `origin` cannot `--emit-block`.
  I dropped the key to keep one manifest feeding both couriers. The
  fix is one line in `exchange-record.schema.json` (or the crafter's
  normalizer); out of scope, noted for the desk.
- `craft_response.py --executable` wants the repo-relative path, not
  the `files/`-prefixed one; the error says so clearly. Not a bug,
  just worth knowing on first use.
- `validate.sh` checks `apply --help mentions .bale/staging` and
  `search_paths` but nothing about the positional's help, so the
  `response-<sid>` rename had no install-sanity coverage; the session
  assertions carry it instead.

## Proposals

- **What:** thread the decline cause through the other `confirm_yn`
  callers — the bare-apply confirmation, drift admission, the
  supersession y/N, the read-only sweep — by switching each to
  `confirm_yn_decision` and phrasing a line per `.decline_branch`. **Why:** the
  operator's "Enter did nothing" report is not hook-specific; every
  prompt has the same three silent branches. **Scope hints:**
  `bin/bale_apply.py` (three call sites) and `bin/bale_pack.py`
  (two); after the apply-side session lands, since the first file is
  its forecast now.
- **What:** move `format_config_hooks_json` beside
  `format_status_json` in `bale_report.py`. **Why:** the renderers
  are one family with one stability rule; it lives in `bale_config`
  only because `bale_report` was frozen this sitting. **Scope hints:**
  `bin/bale_report.py`, `bin/bale_config.py`; trivial, after the
  apply-side session lands.
- **What:** one sentence in `BALE.md`'s hook section naming
  `bale config hooks` and `--forget`. **Why:** the store is now
  operable and the doc still describes it as a file to hand-edit.
  **Scope hints:** `BALE.md`; the brief anticipated this as
  enumerated drift.
- **What:** admit the optional `origin` question-row key in
  `exchange-record.schema.json` (or strip it in the crafter's
  normalizer). **Why:** see Surprises — a filled `origin` currently
  blocks the paste courier. **Scope hints:** one schema line, or a
  few in `tools/craft_response.py`'s clarification normalizer.
