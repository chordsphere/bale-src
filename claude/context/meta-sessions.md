# meta-sessions.md

> What it means for a session that the project under management is bale
> itself. Pull when packing or reviewing a session that touches `bin/bale`,
> the apply or pack pipeline, the staging lifecycle, or the
> `post_apply_pass` hook — in practice, most bale-src sessions. For the
> mechanism behind any of this, see `bale-internals.md`; this file is
> about the consequences.

---

## 1. The recursive premise

bale-src is the source repo for the bale CLI, so every session here is
also a change to the tool that ran the session. The request was packed
by some version of bale, the response is applied by the same version,
and — assuming `post_apply_pass` fires — the *next* session runs under
the modified version. CLAUDE.md's META section calls this out obliquely
(the four global docs "evolve only via bale sessions targeting the bale
tool's own repository"); this doc is the longer form.

bale-src has a few properties no normal project has as a result, and the
protocol's mechanics interact with the recursion in ways worth
understanding before working in here.

---

## 2. The one-apply-behind fixed-point

Any change that affects bale's apply pipeline or pack pipeline takes
effect on the *next* apply, not the apply that lands it. The session
itself is operating under the pre-change code; only its successor sees
the new behavior.

Two concrete examples from the sessions where this surfaced:

- **Session 004 (exec-bit fix).** The fix swapped `shutil.copyfile` for
  `shutil.copy2(follow_symlinks=False)` in `apply_changes_to_worktree`
  and `build_request_tarball`. The very apply that landed the fix
  copied `bin/bale` via the *old*, exec-bit-stripping `copyfile`. The
  reinstall hook's `[install] ensured executable bits` line was
  silently rescuing the mode bit until the next session.

- **Session 005 (staging auto-clean).** The fix removed the
  "remove staging or die" check at the start of `cmd_apply`. But the
  apply that landed the fix used the *old* `cmd_apply`, which is why
  the user had to `rm -rf .bale/staging` manually one last time before
  applying session 005. The first apply free of the manual step was
  session 006.

Both sessions' `validation.sh` ran in staging under the *new* code and
gave clean PASSes — that's fine, since `validation.sh` is a hypothesis
test on the changes, not a test of the as-running binary. But PASS is
one apply ahead of "the user no longer feels the bug." Sessions
modifying apply-path or pack-path code should expect a final dose of
the old behavior on the way out.

The reverse — a session that *introduces* a bug into apply or pack —
has the same shape: the breakage shows up in session N+1, not session N.
A clean PASS on session N is not evidence that session N+1's apply will
succeed; the only test for that is running session N+1.

---

## 3. `bin/bale` is both tool and artifact

In a normal project the files Claude ships are content — components,
modules, configs — and the tool that delivers them is separate. In
bale-src they are the same file. `bin/bale` is the CLI entry point and,
on most sessions, also the primary thing in `files/` of the response
tarball. The change rides through pack → response → apply → reinstall.

Two consequences:

- **Mode-bit regressions hit harder.** Session 004 existed because a
  request-time `copyfile` was stripping `bin/bale`'s exec bit before
  the file even reached Claude. In a normal project that bug would
  have meant some user scripts arrived non-executable — irritating. In
  bale-src it meant *the tool itself* arrived non-executable, which
  would have broken the reinstall on the spot. The reinstall script's
  chmod step caught it (defense-in-depth, since `install.sh` enforces
  `755` on a known set of paths), but relying on a downstream chmod
  to rescue a stripped mode bit is exactly the silent-correction
  failure mode CLAUDE.md §6 argues against. Sessions touching the
  copy/staging paths should include exec-bit assertions in
  `validation.sh` regardless of whether the change is "about" mode
  bits.

- **The file is partially self-validating.** A malformed `bin/bale`
  fails the very next `bale pack` invocation. The reinstall hook also
  runs `install.sh && validate.sh` as a side effect, which exercises
  the freshly merged binary's CLI surface (subcommand discovery,
  `--help`, `--version`) end-to-end. A PASS that survives reinstall is
  thus a session-level integration test, not just a unit-level
  `validation.sh` check. This is a happy accident of bale-src's setup,
  not a substitute for thoughtful per-session assertions.

---

## 4. The reinstall loop is what closes the recursion

`bale-internals.md` §3.6 and §5 cover the mechanism: `post_apply_pass`
fires after a PASS, the hook resolves to `scripts/reinstall.sh`, and
the script mirrors `bin/` and `docs/` into the bale install dir, then
runs `install.sh && validate.sh`. What that doc puts in passing is the
load-bearing fact for meta-sessions: without the hook, every PASS
commits to bale-src but the bale on `$PATH` keeps running the old code.
The next session is then packed by the old tool against the up-to-date
repo, and the divergence compounds.

Three things worth keeping in mind that bale-internals doesn't draw out:

- **Declining the prompt is a one-session decision, not a habit.**
  Bale prompts before invoking any hook (bale-internals §3.2) and a
  decline is silent and non-fatal — correct as a safety floor, but
  every skipped reinstall leaves the running tool one session behind
  the repo. Catch it back up by the next pack, or the gap compounds.

- **`bale revert` does not fire the hook.** Revert undoes the merge
  but does not reinstall, because at that point the running tool is
  correct: it's still the pre-session version. Worth knowing if you
  ever land-then-revert mid-debug — the install dir is fine, no
  catch-up needed.

- **A reinstall failure is non-fatal, by design.** The hook contract
  (bale-internals §3.4) makes a non-zero hook exit advisory: the
  session is already merged and tagged by the time the hook runs;
  unwinding the merge because reinstall errored would be the wrong
  move. The user sees a non-zero log line and can fix the script. The
  meta-session-relevant implication is that a failed reinstall leaves
  bale-src and the install dir desynchronized, and the next session
  will be packed by the stale tool until someone runs the reinstall
  by hand or lands a follow-up.
