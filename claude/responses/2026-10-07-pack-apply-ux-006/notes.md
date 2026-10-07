# Notes — 2026-10-07-pack-apply-ux-006 (bale 0.4.51)

Checked first, per §8 of the brief: `bin/VERSION` read `0.4.50`.
No probe and no question block. Every path I changed is inside the
write forecast. `bin/bale_apply.py` is unchanged, so it has no
changelog row.

## What landed, in one breath

- **(a) The retry line names the next numbered sibling.**
  `bale_report.next_numbered_sibling(stamp)` is the only place this is
  composed. `compose_hold_successors` (all three forks) and
  `format_hold_relay_worker`'s closing line both call it, and
  `bale amend-checkpoint` reaches it through `compose_retry_successor`,
  so the card, the worker block and the amend report give the same
  answer. The brief describes `compose_hold_successors` as the one home
  the worker block already read. It wasn't: the worker block spelled
  its own `bale retry` with `_always_quoted`. It now calls the same
  helper and keeps its always-quoted style. The stamp, the planner
  block's `held tarball:` row, `--sid` and the admission tokens are
  unchanged.
- **(b) `bale retry` resolves a missing numbered name.**
  `resolve_retry_sibling` in `bin/bale` runs before
  `resolve_inbound_path`:
  - A path that exists is used as given.
  - A name that isn't `response-<sid>[ (N)].tar.gz` passes through
    unchanged.
  - Otherwise it takes the newest such sibling in the named path's own
    directory by `st_mtime_ns`.
  - An exact tie refuses and names each tied file as a paste-ready
    quoted `bale retry` line.
  - If there's no sibling, it falls through to today's not-found
    refusal, byte for byte.
- **(c) `BALE_TARBALL` and the context pack's offer.** `run_hook` takes
  `tarball=`. Every post_pack caller passes it: the session pack, the
  handoff pack and the context pack. `post_apply_pass` passes nothing,
  so its prompt is unchanged. `cmd_pack_context` calls
  `run_hook(config_root, merged_config(config_root), "post_pack", "",
  tarball=out_path)` after the `.gitignore` note and before the report.

## Decisions to ratify

1. **The sibling grammar.** A name is `<base>[ (N)]<suffix>`:
   - The counter is one space, then `(N)` where N is a positive integer
     with no leading zero. `r (0)` and `r (01)` aren't counters.
   - `<suffix>` is `.tar.gz` when the name ends with it. Otherwise it's
     the last extension, possibly empty.
   - The regex is `^(?P<base>.+?) \((?P<n>[1-9][0-9]*)\)$`, applied to
     the stem once the suffix is removed.

   **The stem rule.** The stamp's own counter is split off and counts.
   A stamp of `x (1).tar.gz` with nothing else beside it composes
   `x (2).tar.gz`, which is your "(1) → (2)". The line names
   `<base> (M+1)<suffix>`, where M is the highest counter among the
   stamp and its directory's siblings. The plain name counts as 0.

2. **Unlistable directory** — a small deviation from the brief. You
   said a stamp whose directory can't be listed composes `(1)`. I kept
   the stamp's own counter in play there too: a `(5)` stamp in an
   unlistable directory composes `(6)`, not `(1)`. For a plain stamp
   (the case the brief had in mind) the result is still `(1)`.

3. **Max+1, not lowest free.** I followed the brief's "N+1". Browsers
   in my experience take the lowest free number. So if you delete the
   plain-named held tarball, the next download can land under the
   plain name while the line says `(2)`. Retry's resolution covers
   that: `(2)` is missing, so it picks the newest sibling, which is the
   file that just arrived, and logs it. Firefox's spacing (`name(1).tar.gz`,
   with no space) is not recognised. I matched the brief's form only.

4. **All three forks name the sibling.** That includes the fixture and
   base forks, which retry the *same bytes*. I read the constraint ("in
   the worker block, the HOLD card and amend-checkpoint alike") as all
   of them, and amend-checkpoint prints the fixture rung. Nothing new
   arrives at `(N+1)` for those rulings, so retry resolves the missing
   name to the newest sibling, normally the held tarball.

   `test_amend_checkpoint`'s `test_card_and_amend_line_are_one_line_that_lands`
   proves this end to end: the pasted fixture line lands through the
   resolution. One edge to know: if a worker's re-attempt has also
   arrived in that directory, the fixture and base lines would pick it
   up instead, because it's newer. The log line names the file it took,
   so it can't happen silently. If you'd rather the same-bytes forks
   keep naming the stamp verbatim, that's a two-line change in
   `compose_hold_successors`.

5. **Retry's candidate set is narrower than the brief's glob.** I take
   exactly `response-<sid>.tar.gz` and `response-<sid> (N).tar.gz` for
   the typed sid, not `response-<sid>*.tar.gz`. Newest-by-mtime would
   otherwise pick a `response-<sid>-old.tar.gz` or a hand-renamed
   variant, and a `-*` variant is already one paste away in the
   near-name listing.

   The base check (`^response-[^\s()/]+$`) also admits the legacy
   `response-NNN.tar.gz`. The test fixtures use that shape, so it gets
   exercised.

6. **Log line wording.**
   `[bale] retry: <asked> is not there; resolved <found> (newest sibling by mtime in <dir>)`.
   `<asked>` is the argument as typed and `<found>` is absolute. It
   prints after json mode engages, so `--json` stdout stays one line
   (the line goes to stderr there). It isn't journaled to the session
   log, because no session log is open yet at that point. The next
   journaled line, `retrying session X with <name>`, names the file.

7. **Tie refusal.** `retry: <asked> is not there, and its newest
   siblings in <dir> share one modification time, so bale will not
   guess between them:`, then one quoted `bale retry <path>` line per
   tied file, then `Name the one to retry.` It fires before any session
   gate, so the HOLD state is untouched.

8. **`BALE_SESSION_ID` on a context pack** is the empty string. It's
   printed as `BALE_SESSION_ID=` and exported empty, not unset. A hook
   that branches on the sid can test `-z`.

   **`BALE_REPO_ROOT` and cwd on a context pack** are the config root
   the walk already reads: the git work-tree root inside one, the packed
   directory outside one. The hook layer is detected the same way, so a
   project hook in the enclosing repo shows as `(project)`. A pack from
   `docs/` inside a repo therefore runs the hook with cwd at the repo
   root, not `docs/`. `BALE_TARBALL` is the one thing pointing at
   `docs/.bale/outbox/`.

9. **Where `BALE_TARBALL` prints:** between `BALE_SESSION_ID` and
   `BALE_REPO_ROOT`, as an absolute path (`os.path.abspath`, not
   `resolve()`, so a symlinked repo shows the path bale used).

10. **The riders.**
    - The cap/breach loop extraction (104a's Proposal 2) is **dropped**.
      The context pack's loop and the session pack's differ in refusal
      text and prompt wiring, so a faithful extraction is a
      byte-identity job of its own. It would have doubled this
      session's review surface for no user-visible gain. Proposed below.
    - The FORCE-queue accessors are **left on the registry**. My
      `bin/bale` edits are in banner sections 1 (one import), 8
      (inbound path), 20 (retry), 22 (handoff's call), 23 (hooks) and
      26 (CLI help), never section 2 (logging).

11. **A pre-existing pin changed meaning.** In
    `test_apply_preflight.ExplicitNameMissTest`, two cases pinned
    `bale retry /dir/response-X.tar.gz`, with `response-X (1).tar.gz`
    beside it, as a not-found refusal that lists the twin. That is now
    exactly §2.2's resolution, so the retry subcases pin the resolution
    instead. The apply and handoff subcases still pin the listing, and
    the relative-with-search-paths case is unchanged, because the twin
    sits in the search directory, which resolution never consults. I
    also added a sentence to BALE.md §7.1's near-name paragraph.

12. **Hermetic unit pins.** `HoldCardUnitTest`, `HoldRelayUnitTest` and
    `ComposeRetrySuccessorUnitTest` used `HELD = "/tmp/held dir/…"`. The
    composer now lists the stamp's directory, so a stray `/tmp/held dir`
    on a dev machine would have changed the pins. `HELD` now lives in a
    directory that doesn't exist, under a fresh temp root, so the
    listing is empty by construction and the pins read `RETRY` (the
    `(1)`). The space in `held dir` is still there, so quoting is still
    exercised.

## Where to look closely

- The quoting in the composed line. Every retry line now carries
  ` (1)`, so `shlex.quote` always wraps it in single quotes. The
  worker block was already always-quoted. On the card it's new. All
  the e2e pins round-trip through `shlex.split`.
- `resolve_retry_sibling`'s existence test uses `locate_inbound_path`,
  the same lookup the verb uses. A relative name found through a
  search path counts as existing and is used as given. A relative name
  that misses everywhere is resolved against cwd's directory only.
- The fixture/base edge in decision 4.

## Validation, run twice

On the staged tree, all 14 checks pass in about 2 minutes. The whole
suite in discover form (what `--slow` adds) also passes, observed:
1990 tests, OK, 48 skipped, about 9 minutes. The base is 1966 tests,
OK, 48 skipped; the skips are the same slow-gated set.

On the unmodified base, these fail as intended:
- `file syntax`: the changelog record doesn't exist there.
- `bin/VERSION (cmp)`.
- `composer names the next numbered sibling`.
- `retry resolves the newest sibling`.
- `post_pack prompts carry BALE_TARBALL`.

These pass on base too:
- **The nine suite checks.** These are the base's own suites on the
  base code, not the new tests, which only exist in the staged tree.
- **`context pack with no hook prints today's output`.** By design, it
  pins today's output.

Every hook in validation.sh is offered on closed stdin and asserted
not to have run. Two suite cases accept a hook under a pty to prove the
export (`test_hook_acceptance.PostPackTarballTest`,
`test_context_pack.ContextPackHookTest`). They write a marker under the
sandbox HOME.

## Proposals

- **What:** let `bale apply <missing numbered name>` share
  `resolve_retry_sibling`.
  **Why:** the same browser twin bites there: a corrected *fresh*
  response downloaded twice. The function is verb-neutral apart from
  its log wording and the `bale retry` lines in its tie refusal. I
  didn't land it, because apply already has the near-name listing and
  bare apply's own resolver. Two resolution postures on one verb
  deserves a ruling.
  **Scope hints:** `bin/bale` `cmd_apply` beside its
  `resolve_inbound_path` call; parameterize the verb in the tie lines.

- **What:** the cap/breach loop extraction (104a's Proposal 2) as its
  own small session.
  **Why:** `cmd_pack_context` and the session pack carry two copies of
  the hard-cap / `--force` / soft-breach y/e/n loop. They have already
  drifted in wording ("for this context pack only").
  **Scope hints:** `bin/bale_pack.py` only; `test_context_pack` and
  `test_pack_guards` pin the texts.

- **What:** a one-line `bale status` hint when a HOLD's composed
  sibling already exists, i.e. the worker's re-attempt has arrived.
  **Why:** since this change the operator's next step after a delivery
  is predictable from the stamp. Status could say
  "`response-X (1).tar.gz` is here — `bale retry` it", where today it
  says nothing.
  **Scope hints:** `bin/bale` status, `bale_report.next_numbered_sibling`.
