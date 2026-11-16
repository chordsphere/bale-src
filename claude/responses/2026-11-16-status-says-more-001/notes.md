# Notes: 2026-11-16-status-says-more-001 (bale 0.4.63)

All eight outcomes in the brief landed. The sitting's guessed key names stand
as written: `config.search_dirs`, `open_sessions` with `responses`, the
attempt outcome `clarification`, `clipboard.encoding`, and the vocabulary
`hold-class`. Every changed path is inside the write forecast, so there is
nothing to admit at apply.

The whole suite ran clean in this sandbox with the change in place: 2247
tests, 48 skipped, about 7.5 minutes. The default `validation.sh` runs 20
targeted modules (437 tests) in about 70 seconds; `--slow` adds the whole
suite. I ran the script on the changed tree (every check passed, both claims
agreed) and on the unchanged tree, where the session assertions and the
targeted modules fail as they should. The exec-bit assertion passes on both,
since it guards `apply.sh`'s chmod rather than testing the change.

## Decisions to ratify

- **Where the new keys sit.** `open_sessions` is the status line's last key,
  after `clipboard`. `search_dirs` is the last key of `config`, and `encoding`
  the last of `clipboard`. The brief pins that every existing key keeps its
  place, and appending is the only way to keep both the key set and its
  order. `STATUS_REPORT_KEYS` now has fourteen entries, and `bale contract
  --json` lists them in that order.
- **How a non-lock session is classified.** I took the sitting's guess. The
  inline reading in `_gather_status` became `_gather_open_session(repo, sid,
  outbox)`, which runs once per open sid. The lock session's `session_*`
  fields are copied from its own entry, so `session` and
  `open_sessions[sid]` can't disagree. One side effect: an unreadable
  clarification record or manifest now logs once for each session that has
  one, not only for the lock session.
- **`responses` lists the plain name and the `(N)` copies, nothing else.** A
  `response-SID-*.tar.gz` variant is left out, for two reasons. The named
  search doesn't resolve it. And a prefix match can catch another session's
  sid: `response-2026-11-16-x-001-...` is a valid name for a session whose
  slug begins `x-001`. Each entry is `{path, name, copy, modified_at}`: copy is
  N, or null for the plain name, and modified_at is UTC to the second.
  Status runs this listing for the directories bale would search from where
  it runs: cwd first, then each search directory, matching the brief.
- **The newer-copy note.** The check lives in `newer_numbered_copy_note` in
  bin/bale, which shares its scan (`numbered_copies`) with the status listing
  and uses `numbered_sibling_parts`' grammar. It doesn't live inside
  `resolve_inbound_path`, because the resolver runs before json mode is
  enabled and `log()` prints to stdout until then. Each verb computes the note
  at resolution and logs it once json mode is set, the way retry already
  defers its sibling note. Under `--json` the note goes to stderr. In human
  mode it goes to stdout like every other `[bale]` line; the brief said
  stderr, but it meant where bale's log lines go. The note covers every
  same-base copy newer than the named file, including the plain name when
  the operator named a `(1)`. It engages only for relative `.tar.gz` names,
  as the outcome says. Retry skips it when `resolve_retry_sibling` already
  replaced a missing name. Handoff has no `--json`, so it logs at once. The
  paste line is indented and has no `[bale]` prefix, like the near-name
  listing's, so it can be copied whole.
- **The clarification attempt.** `command` is the landing verb (`apply`, or
  `retry` if a retry carried a clarification). The attempt carries the
  `--cost-file` block (the sitting's guess). The cost used to be logged as
  "valid, not stamped"; that line is gone, and `tests/test_cost_file_flag.py`
  now pins the stamp instead. The clarification `--json` line now names the
  telemetry record in place of null.
- **Stats counts the attempt as a response attempt**, because its command is
  apply or retry, the same as a bailout's. It is in flight (added to
  `IN_FLIGHT_OUTCOMES`) and never validated, so the agreement, HOLD and
  checkpoint rates don't move. The rates with `response_attempts` as their
  denominator (drift refusal) gain one attempt in the denominator per
  clarification landing. If you'd rather leave it out of response_attempts,
  the change is one condition in `_class_row`. The human renderings show it
  through code that already existed: the dossier prints the outcome word and
  the attempt's `clarification: rounds N` lines, and the stats report doesn't
  list outcomes.
- **`bale relay` still writes no attempt for a round it records.** The
  slip is about the landing. A planner's answer isn't a response that bale
  processed, and the next attempt's clarification summary counts the round
  anyway. BALE.md 8.11 now gives that reason, where it used to say "for the
  same reason a clarification apply writes none".
- **`bale contract` reads HOLD_CLASSES from bale_stats.** There's a
  new `CONTRACT_SIBLING_CODE_HOMES` (`{"bin/bale_stats.py": "bale_stats"}`),
  and `_contract_code_tuple(pointer, home)` imports the sibling lazily and
  reads its constant. The vocabulary is published with home
  `bin/bale_stats.py` and pointer `HOLD_CLASSES`. bale_report holds no copy
  of the words, and a test checks that.
- **The clip.exe row** now ends `every paste block is copied, fed to it as
  UTF-16LE`. Other commands' rows are byte for byte what they were.

## Things I noticed

- As the brief's REH said, `sessions` is sorted by sid, not by the order the
  sessions were opened, though the `format_status_json` docstring still says
  oldest-first. I touched the gather around it but didn't change the order
  or the docstring. `open_sessions` follows `sessions` order. See the
  proposals.
- Before this release a clarification landing printed
  `cost file: valid, not stamped — a clarification writes no attempt`. That
  line no longer exists anywhere. The only "not stamped" lines left are the
  dry-run's and unlock's.
- `tests/test_dossier_says_more.py` pinned `bin/VERSION == 0.4.62`, so it
  would have broken in any later release. I relaxed it to "at or past 0.4.62"
  and kept its check of its own changelog record. The current release pin is
  in `tests/test_status_says_more.py`.

## Proposals

- **What:** Say what order `sessions` is really in. Either fix the
  `format_status_json` docstring's "oldest-first" (and BALE.md's matching
  words) to "sorted by sid", or sort `open_sessions()` by the `opened`
  attempt's time.
  **Why:** REH saw `first, fourth, second, third` for four sessions packed in
  that order, so the lock session `sid` names is the first in sorted order,
  not the oldest. `open_sessions` inherits the same order.
  **Scope hints:** `open_sessions` in bin/bale; the docstring; BALE.md 5.5.
  Sorting by open time changes which session holds the lock, so it's a
  ruling for the planner, not a doc fix.
- **What:** Let the human `bale status` show each open session's state in
  the listing row that appears when two or more are open.
  **Why:** The per-session facts are gathered now (`open_session_facts`),
  but the human block still shows a state only for the lock session. The
  walk-in reads the json, but an operator at a terminal would see a
  suspended non-lock session only through `--json`.
  **Scope hints:** `format_open_sessions_value` in bin/bale_report.py and
  `_render_status`. Human output changes, so pins in tests/test_thread_status
  and test_clarification_status may need updating.
- **What:** Consider the newer-copy note for an absolute name too: copies
  beside the named path in its own directory.
  **Why:** The brief scoped the note to relative names, and I kept that. But
  a browser's `(1)` copy sits beside an absolute path just as often, and the
  near-name listing already scans an absolute name's own directory.
  **Scope hints:** `newer_numbered_copy_note`'s first guard, using the same
  `numbered_copies` scan over `[typed.parent]`.

## Handbook

### bale-src

- Since 0.4.63 `bale status --json` carries a top-level `open_sessions`, appended after `clipboard`: one entry per open session, its keys exactly the `sessions` list, each `{state, goal, expects_probe, clarification, responses}` classified on that session's own facts; `sid` and `session` still describe the lock session only.
- Since 0.4.63 each `open_sessions` entry's `responses` lists the files named `response-SID.tar.gz` or `response-SID (N).tar.gz` in the current directory and each search directory, newest first by mtime, each `{path, name, copy, modified_at}` with an absolute path; a `response-SID-*.tar.gz` variant is not listed, and no file is opened.
- Since 0.4.63 `bale status --json`'s `config.search_dirs` lists the `[apply] search_paths` directories in order as bale uses them (tilde and variables expanded); `config.search_paths` stays their count.
- Since 0.4.63 `bale apply`, `bale retry` and `bale handoff`, given a relative `.tar.gz` name that resolves, log a `[bale]` line naming any newer numbered copy of that name in cwd or a search directory with the word "newer", then an indented `bale <verb> '<path>'` line per copy; they still use the file named, and an older copy is not mentioned.
- Since 0.4.63 a clarification landing appends a telemetry attempt with outcome `clarification`, command `apply` (or `retry`), the clarification summary as it stands after the round, and the `--cost-file` block; `bale stats` reads it as in flight and counts it as a response attempt, and a recorded `bale relay` round still writes no attempt.
- Since 0.4.63 the `bale status` clipboard row for clip.exe ends ", fed to it as UTF-16LE", and `bale status --json`'s `clipboard.encoding` reads `utf-16le` for clip.exe, `utf-8` for any other command, null when nothing is copied.
- Since 0.4.63 `bale contract` publishes the vocabulary `hold-class` (checkpoint-defect, both, checkpoint, validation) with home `bin/bale_stats.py` and pointer `HOLD_CLASSES`, read from bale_stats through `CONTRACT_SIBLING_CODE_HOMES` in bin/bale_report.py.
- The whole unit suite runs clean in a worker sandbox at 0.4.63, with the new tests/test_status_says_more.py: 2247 tests, 48 skipped, about 7.5 minutes; that session's default validation.sh (20 targeted modules, 437 tests) takes about 70 seconds.

#### Front sheet

bale-src is the source of bale, the occupant's command-line tool for
handing work to an agent session and taking the result back. bale packs a
request tarball, carries the worker's questions and the planner's answers
through `bale relay`, checks the response tarball the session returns, and
lands it on a branch in the project only after validation passes. With this
session it stands at 0.4.63, the seventh of eleven releases planned in
folder 43 for the slips about bale. This release makes `bale status` and the
dossier say more about open sessions.

## Walkthrough

### What changed

- **bin/bale, the status gather.** Each open session is now classified by
  `_gather_open_session`, which reads that session's own branch, outbox
  tarball, clarification records and stamped manifest. The lock session's
  entry fills the same fields it always did. `StatusReport` gains
  `search_dirs` and `open_session_facts`, and each session's `responses`
  come from `status_response_files`.
- **bin/bale, the named search.** The new `numbered_copies` lists every
  `<base>.tar.gz` and `<base> (N).tar.gz`, newest first. The new
  `newer_numbered_copy_note` uses it to name newer copies of the file a verb
  was given. Retry and handoff log the note, and apply logs it from
  bin/bale_apply.py.
- **bin/bale_report.py, the status line.** It gains `open_sessions` (last),
  `config.search_dirs` and `clipboard.encoding`. The `session.clarification`
  object and each entry's `clarification` are built by one shared builder.
  The new `clipboard_encoding` returns the encoding word, and the clip.exe
  row says UTF-16LE.
- **bin/bale_report.py, the contract.** `bale contract` gains the
  `hold-class` vocabulary, read from bin/bale_stats.py's `HOLD_CLASSES`.
- **bin/bale_apply.py.** A clarification landing writes a `clarification`
  attempt with the summary and the cost block, and its `--json` line names
  the record.
- **bin/bale_stats.py.** `clarification` is an in-flight outcome.
- **schemas/telemetry-record.schema.json.** `clarification` joins both
  outcome enums, and three descriptions say what a landing now writes.
- **Docs and help.** BALE.md, bale-internals.md and the help texts for
  apply, status, contract and `--cost-file` describe the new behaviour.
- **Tests.** tests/test_status_says_more.py is new. Four existing suites
  were adjusted to the new behaviour.
- **Release.** bin/VERSION is 0.4.63, and claude/changelog/0.4.63.json is
  its record.

### Why

- Slip 1: the walk-in couldn't say where a session's response was, because
  `config.search_paths` was only a count and nothing listed the files.
- Slip 7: status gave a lifecycle state for the lock session only, so the
  in-flight list had to read each session's dossier.
- Slip 5: a browser saves a corrected response as `(1)`, and the named
  search took the old plain file without a word. The sitting's rehearsal
  confirmed it at 0.4.62.
- Slip 3: a clarification left no trace in the dossier, so the round was
  visible only on `bale status`, and only for the lock session.
- The clipboard fold (from 0.4.59): the row never said that clip.exe gets
  UTF-16LE.
- The dossier fold (from 0.4.62): the four HOLD class words were a closed
  list that `bale contract` didn't publish.

### How to explain each piece

- **open_sessions.** "Status now says what every open session is doing, not
  just the first one: packed, held, or waiting on a clarification, with its
  goal and its rounds."
- **responses.** "For each open session, status lists the response files
  `bale apply response-SID.tar.gz` would find from here, newest first. So
  the walk-in can say 'its response is in your downloads'."
- **search_dirs.** "The list of folders bale searches, where the line used
  to give only how many there were."
- **The newer-copy note.** "If you name the old download and a newer `(1)`
  sits in another folder bale searches, bale tells you and gives you the
  line for the newer one. It still applies what you named."
- **The clarification attempt.** "When a clarification lands, the
  session's record now shows it as a step, with its rounds. The session is
  still open, and the real response closes it later."
- **UTF-16LE.** "With clip.exe, the clipboard row now says how bale feeds
  it."
- **hold-class.** "`bale contract` now lists the four HOLD reasons, read
  from where the dossier keeps them."

### Questions a reviewer will ask

- *Why is open_sessions at the end of the line?* So every existing key
  keeps its place. The brief pins that.
- *Does the lock session change?* No. `sid` and `session` are as before,
  and the lock session is still the first sid in `sessions`.
- *Can the newer-copy note change what gets applied?* No. It's a log line
  computed after resolution, and the resolved path is the one applied. A
  test checks the applied bytes.
- *Does `--json` stay one line?* Yes. The note is logged after json mode is
  on, so it goes to stderr. A test checks this.
- *Does a clarification now close the session or move a rate?* It doesn't
  close it: the outcome is in flight. It does add one to `response_attempts`,
  as a bailout does, and that's the only rate denominator it touches.
- *Why doesn't relay write an attempt too?* Its round is the planner's
  answer, not a response bale processed. The next attempt's summary counts
  it.
- *Is HOLD_CLASSES copied into bale_report?* No. It's read from bale_stats
  at run time, and a test checks bale_report has no such name.

### A hand test

1. On the WSL machine with `clip.exe` configured, run `bale status` in
   bale-src. The clipboard row should end "fed to it as UTF-16LE". Run `bale
   status --json | jq .clipboard.encoding` and expect `"utf-16le"`.
2. With a session open, put `response-SID.tar.gz` in Downloads and copy it
   to `response-SID (1).tar.gz`. Touch the copy so it's newer. Run `bale
   status --json | jq '.open_sessions[].responses'`: the `(1)` copy should
   be listed first, with absolute paths.
3. In the same state, run `bale apply response-SID.tar.gz --dry-run`. Read
   the note: it should name the `(1)` file, say "newer", and give a quoted
   `bale apply` line you can paste as is.
4. Land a clarification on a scratch session. Then `bale stats --sid SID`
   should show an attempt `clarification` with `clarification: rounds 1`,
   and `bale status --json | jq '.open_sessions'` should show that session
   as `clarification` even when another session holds the lock.
5. Run `bale contract` and look for `hold-class  bin/bale_stats.py
   HOLD_CLASSES` with the four words under it.

## Structure

- title: Fix bale-src for the slips about bale, in eleven sessions
- size: high
- goal: Land the fixes to bale-src for the slips about bale in the office's suggestion box, one release per session, in the ratified order
