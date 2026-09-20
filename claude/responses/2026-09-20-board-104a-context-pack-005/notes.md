# notes — 2026-09-20-board-104a-context-pack-005

## Baseline, before any change

On the 0.4.38 tree as shipped: the full suite (`python3 -m unittest
discover -s tests -t .`) ran 1364 tests, OK, 48 skipped by the slow gate,
in about 200 s. `validate.sh`: 91 checks passed. After this session:
1392 tests OK (the same 48 skips; +28 from the new suite), `validate.sh`
still 91/91.

One process note: the session paused once on a tool-call limit mid-build
and resumed on Continue with context intact. That is not a compaction
(CLAUDE.md §11.1), so `compaction_occurred` is false.

## What you asked me to state

**Where it lands, and its name.** `<dir>/.bale/outbox/context-<name>.tar.gz`.
`<name>` is the directory's basename made filename-safe: runs of
characters outside `[A-Za-z0-9._-]` become one hyphen, leading and
trailing dots and hyphens are stripped, and `tree` is the fallback. For an
ordinary name like `bale-src` it is the name unchanged.

- `.bale/` is a baked-in excluded directory, so a second context pack
  never ships the first.
- `bale status` globs only `request-*.tar.gz`, so a context tarball never
  appears as a session's outbox entry.
- A re-run replaces the file; the report says `replaced`. It is built at
  a temporary name and moved into place, so a failed build never leaves a
  truncated tarball under the real name.
- Inside a repo subdirectory it lands under *that subdirectory's*
  `.bale/outbox/`, per "somewhere under that directory". If you'd rather
  it went to the repo root's outbox, that is a one-line change.

**Layout.** One top-level `<name>/` folder holding the surviving files at
their directory-relative paths, i.e. what `tar czf foo.tar.gz foo/`
gives. Regular files keep their bytes and mode, and symlinks travel as
symlinks (the request build's `copy2(follow_symlinks=False)` semantics).
There is no marker file: I kept the tarball exactly the tree, and the
receiving side recognizes it by name and by the TARBALL.md §3.1 passage.

**A directory that is not a git repo.** I agree with your reading, and it
was cheap. No git-init walkthrough runs; the tree is packed from a
filesystem walk that prunes the baked-in directories and does not follow
directory symlinks.
- What you lose outside git is `.gitignore`: there is no git to ask.
- `.baleignore`, `--exclude`, and the secret and bundle filters still apply.
- Inside a work tree the listing is `git ls-files -z` run from the
  directory, which honors every `.gitignore`, the repo root's included.

**Composition.** Every pack flag is classified:
- **Compose with `--context`:** `--include` (paths relative to the
  directory; absolute or `..` refuses; missing refuses; naming a bundle
  refuses), `--exclude`, `--max-files`/`--max-size`/`--max-depth`,
  `--force`, `--verbose`, `--json`.
- **Refuse, fail-fast, as you leaned:** everything else, with every
  offender named in one message.

The two tables live in `bin/bale_pack.py`. `tests/test_context_pack.py`
pins that together they partition the pack parser *and* that their
defaults match the parser's. A flag someone adds to pack later fails the
suite until it is classified.

Detection is "value differs from default", so `--expects-probe
claude-decides` typed at its default is a harmless no-op. It is
indistinguishable from absent without changing the parser default, which
would have touched normal packs.

## Decisions to ratify

1. **Subdirectory packs honor the enclosing repo's exclusions.** In a
   subdirectory, the repo root's `.baleignore` also applies, evaluated on
   the repo-relative path, and so does the configured blind checkpoint.
   - Without this, a `docs/` context pack would skip exclusions the
     project set at its root. That is exactly the "leaks a `.env`" class
     you flagged.
   - The directory's own `.baleignore` applies too.
2. **The checkpoint is always auto-excluded.** Loudly, at the walk's
   one-line/summary grain. `--allow-checkpoint-in-scope` refuses beside
   `--context`: reading material has no deliberate path for oracle bytes.
   Hand-tar if you ever genuinely want one.
3. **`--no-include-group` refuses.** The include group is a session
   read-side pull; a context pack is the tree, not an include set.
4. **`bale open` refuses a stored argv with `--context`.** It is refused
   in `pack_argv_preflight`, before the checkpoint dry-run.
   - Without this, the replay would have refused anyway (open injects
     `--readme-file`/`--no-readme`, which refuse beside `--context`), but
     only after spending the oracle.
   - `bin/bale_pack.py` was in forecast, so this cost nothing.
5. **Untracked-tarball note, no `.gitignore` edit.** Where `.bale/` is not
   gitignored (a repo bale never packed in), the tarball shows as
   untracked. The report says so; `--context` never edits `.gitignore`,
   since it touches nothing tracked.
6. **The cap loop is a compact copy of `cmd_pack`'s, not an extraction.**
   Same y/e/n on a TTY, refusal piped, and FORCE logs. Extracting it would
   have edited the normal path, and the brief wants that untouched.
   Proposal 2 below.

## Look closely at

- `cmd_pack` dispatches to `cmd_pack_context` right after `enable_json_mode`
  and `refuse_system_dir`. Those are the only two things the paths share.
  Everything else in `cmd_pack` is unreachable from `--context`, which is
  how "no sid / lock / telemetry / sweep / opener" holds by construction.
  The suite checks it too: no counter advance, no `.bale/sessions`, no
  telemetry, no commit, `.gitignore` byte-identical, no opener. It also
  runs a context pack on a pty beside an open read-only session, feeding
  Enter to prove there's no sweep prompt to accept.
- `walk_for_pack(listed=...)` is the only edit on the shared path. When
  `listed` is `None` (every existing caller), the function is unchanged.
- The stale-comment rider now describes both directions of the
  supersession lineage, with the stamp in the reverse-lineage block above
  it.
- TARBALL.md §3.1: the passage is appended after the "Tar with:" line,
  with no neighbour rewritten. `validation.sh` asserts the verbatim
  sentence byte-exact after whitespace collapse, exactly once, inside
  §3.1. It also pins the expected literal's own sha256, so a typo in the
  script can't make the check vacuous.
- The §3.4 row sits between `--read-only` and `--supersedes`. The §5.8
  sentence names `bale stats` without listing what it reads. I checked
  that it's true: apply embeds bailout diagnostics in the telemetry
  record, and the stats dossier reads them.

## Out-of-forecast paths

None. All seven `changes[]` paths are under the stamped forecast.
`bin/bale_report.py` is untouched.

## Proposals

1. **Home the context report in `bin/bale_report.py`.**
   - What: once 104b releases the file, move `format_context_pack_json`
     and the `context-packed` outcome word into `bin/bale_report.py`.
   - Why: that module's `format_pack_json` docstring says the outcome
     vocabulary is owned there. Today the word lives in `bin/bale_pack.py`,
     which honestly breaks that one-home note; BALE.md §7.8 says so.
   - Scope hints: `bin/bale_pack.py`, `bin/bale_report.py`, BALE.md §7.8.
     Only after 104b lands.
2. **Extract the cap/breach loop.**
   - What: pull the soft/hard/`--force` breach loop into one helper
     called by both `cmd_pack` and `cmd_pack_context`.
   - Why: it is now duplicated in compact form. The copy is faithful
     today, but two copies drift.
   - Scope hints: `bin/bale_pack.py` only. The existing pack suites and
     `tests/test_context_pack.py` cover both callers.
3. **`validate.sh` should check `pack --help` mentions `--context`.**
   - What: add `--context` to the install self-check's "pack --help
     mentions" list.
   - Why: the list enumerates pack's flags, and `validate.sh` was not in
     this forecast. The suite pins the help listing meanwhile.
   - Scope hints: `validate.sh`, one line.
4. **Consider a context-pack line in `bale status`.**
   - What: optionally, have `bale status` mention a present
     `context-*.tar.gz` in the outbox.
   - Why: today it is deliberately invisible there. That is right for
     session state, but an operator hunting for "the tarball I made" gets
     no pointer.
   - Scope hints: `bin/bale` status report, `bin/bale_report.py`.
     Low priority.
