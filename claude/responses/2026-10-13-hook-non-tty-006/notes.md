# Notes — 2026-10-13-hook-non-tty-006

## What changed, in one breath

`run_hook` gained a third path between apply's configured decision and the
terminal prompt: when the hook is pack-side and stdin is not a terminal, it
prints the banner, skips the `default:` line and the prompt, and logs

```text
[hook post_pack] declined (stdin is not a terminal; the prompt was not offered); not invoking.
```

No caller changed. The session pack, `bale handoff`, the context pack and
the pack replayed inside `bale open` all reach it through `run_hook`. Each
of the four is now pinned piped, and the open replay is pinned in both
`--json` (stdout exactly one line) and human mode.

## Decisions to ratify

1. **How `run_hook` knows it is on the pack side.** I gate on the hook's
   name: a new `PACK_SIDE_HOOKS = frozenset({"post_pack"})`. The only
   other hook, `post_apply_pass`, belongs to the apply side. I did not
   gate on "`no_interact` is False", because `bale apply` without
   `--no-interact` also passes `no_interact=False`. Gating on that would
   have quietly changed a piped apply's `post_apply_pass` too. The brief
   speaks of "the apply path (`no_interact`)" as if apply always ran in
   that mode. It doesn't, so the name is the honest test. As a result, a
   piped `bale apply` with no `--no-interact` still prints
   `run this hook? [y/N]` to nobody and declines with the EOF line.
   `ApplySideUnchangedTest` pins that this is unchanged. See Proposals.
2. **The fixed line sits beside `HOOK_DECLINE_LINES`, not in it.** That
   mapping is keyed by `ConfirmDecision.decline_branch`, the branches of a
   prompt that *was* offered. This decline happens because no prompt was
   offered, so a fourth key would have had no branch behind it. The
   constant is `HOOK_DECLINE_LINE_NOT_A_TERMINAL`, on one physical line.
3. **The stdin test is a small helper, `stdin_is_terminal()`.** It treats
   `sys.stdin is None`, a non-TTY stream and a closed stream (where
   `isatty()` raises `ValueError`) all as "not a terminal". It never
   errors, since its answer only decides whether to offer a prompt.
4. **Wizard wording (`bin/bale_config.py`).** The `config init` text for
   `hooks.post_pack` used to say "Bale prompts before running it" with no
   condition. Both the summary and the description now say bale asks on a
   terminal and declines without asking otherwise. Wording only: no key,
   default or behaviour changed.

## Paths outside the write forecast

The forecast was `BALE.md`, `bin/VERSION`, `bin/bale`, `claude/changelog`
and `claude/context/bale-internals.md`. These four paths sit outside it.
Each is recorded in `feedback.self_reported.forecast_departures` too:

- `bin/bale_config.py` (modified). The brief's surface list names "the
  `config init` wizard's hook wording if it promises a prompt
  unconditionally". It did, and that wording lives in this file, not in
  `bin/bale`.
- `tests/test_hook_non_tty.py` (created). The new suite the brief asks
  for: the four piped pack-side paths, the pty contract, the apply side,
  the constants.
- `tests/test_context_pack.py` (modified).
  `ContextPackHookTest`'s two piped cases asserted the old EOF decline
  (`run this hook? [Y/n]`, then "stdin closed or interrupted"). That is
  exactly the behaviour this session removes, so they would fail. They
  now pin the non-terminal decline, and the first is renamed to match.
- `tests/test_hook_acceptance.py` (modified).
  `PostPackTarballTest.test_session_pack_prompt_shows_bale_tarball`
  asserted the same old line for a piped session pack. Same reason. Its
  class docstring now points at the new suite.

## Where to look closely

- `bin/bale`, the `elif name in PACK_SIDE_HOOKS and not stdin_is_terminal():`
  branch in `run_hook`. It comes after the banner and before the prompt
  branch. The banner block and the `else:` branch are byte-identical to
  0.4.54.
- `BALE.md` §5.4 gains one (long) sentence after the `BALE_TARBALL`
  sentence. The context-pack paragraph in §7.8 gains a clause, because it
  promised "the same prompt" and should say the non-terminal case comes
  along. The fixed line is quoted in §5.4. The 70-column wrap splits it
  across two lines there, which is fine for prose. The byte-exact copy is
  the one in `bin/bale`.
- `claude/context/bale-internals.md` §3.2 used to say pack-side
  invocations "always prompt". It now describes the three paths.

## Tests

I ran `python3 -B -m unittest discover -s tests` from the repo root,
with `BALE_TEST_SLOW` unset, on Python 3.13 and git 2.43:

- Untouched 0.4.54 tree: 2075 tests, OK, 48 skipped (828 s).
- With this response: 2093 tests, OK, 48 skipped (825 s). That is the
  same 48 skips (the slow gate plus host-capability skips) and the 18
  new cases. No missing-file baseline failures, as the brief expected.

The new suite has 18 cases. Before shipping I ran it, plus the two
edited suites, against the *unmodified* 0.4.54 code. Every case that
pins the change failed there: 12 failures and 3 errors (the three
errors are the missing constants). The terminal-contract and apply-side
cases passed on both trees, as they should. They are regression pins,
not change pins. The same holds for two of `validation.sh`'s session
assertions. "Board-83 lines unchanged" guards against regression, and
"no docs/ change" reads the manifest, as the brief specifies. Both pass
on either tree by design.

The pty cases (`TerminalStillPromptsTest`) drive a session pack. I did
not add a pty-driven `bale open` case: on a terminal the open replay
reaches the same `run_hook` with the same stdin, and the piped open
cases already prove the replay goes through it.

`validation.sh` runs the whole suite because the brief asks for it. Here
it took over ten minutes, well past TARBALL.md §7.6's two-minute target.
I put the fast checks first (the new suite and the two edited suites) so
a real break shows early, and I did not gate the whole-suite run behind
`--slow`, because the brief names the suite as part of validation. If
you would rather gate it, it's the one `run_check` line near the end.

## Proposals

- **What.** Decide whether a piped `bale apply` *without*
  `--no-interact` should also stop offering `post_apply_pass`'s prompt
  to nobody.
  **Why.** It has the same symptom this session fixed on the pack side:
  banner, `run this hook? [y/N]`, then "stdin closed or interrupted".
  `ApplySideUnchangedTest.test_piped_apply_still_offers_post_apply_pass`
  pins it as-is. The apply pipeline's non-interactive mode is out of
  scope here, and apply already has a configured answer for automation
  (`--no-interact` / `apply.no_interact`), so it is a real choice, not an
  obvious fix. Either extend `PACK_SIDE_HOOKS`' test to every hook
  outside `no_interact`, or leave apply's EOF line as the signal that the
  operator forgot `--no-interact`.
  **Scope hints.** `bin/bale` `run_hook` (renaming the constant if the
  test stops being pack-only), `tests/test_hook_non_tty.py`'s apply case,
  `tests/test_hook_acceptance.py`'s `test_piped_stdin_declines_regardless_of_memory`.
- **What.** The global docs could mention that a piped pack-side hook is
  declined without a prompt, wherever `PLANNER.md` §2 or `TARBALL.md`
  talk about hooks being non-load-bearing.
  **Why.** A planner reading why a hosted run's hook never fired would
  find the answer in BALE.md, but not in the docs a session carries.
  `docs/` is a sibling session's scope, so this is only a suggestion. I
  did not check whether those docs mention hook prompting at all, since
  reading them past the triggers was not this session's work.
