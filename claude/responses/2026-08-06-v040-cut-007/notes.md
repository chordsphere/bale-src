# notes.md — 2026-08-06-v040-cut-007

Relaying to the master per the brief. The cut went clean; everything
below is color, judgment calls, and the flags the brief asked for.

## The §7.4 call

Qualified, not absorbed-and-dropped: the rewritten cut record keeps
the pass-through citation and writes it as **TARBALL.md §7.4** ("plus
the TARBALL.md §7.4 pass-through of `--verbose` into `validation.sh`
itself"). The bare form is gone from §13; validation pins both the
qualified presence and the bare absence.

## The v0.3 --verbose parenthetical

Already read "closed in v0.3.35" from 005's edit — consistent with
the brief's "closes as landed" — so I left it byte-untouched. The
only §13 bytes changed are the cut-condition paragraph itself
(from "The counter and this phase model decoupled..." I kept the
decoupling-history opening sentence verbatim and rewrote from the
re-coupling onward into the record). The v0.4 phase heading and its
checklist text are untouched, as instructed.

I named the audit session id (`2026-08-06-v04-selftest-audit-006`)
in the doc so "that session's notes" resolves for a later reader —
same precedent as TARBALL.md §5.5 naming its retiring session. No
test counts in the doc, per the brief.

## One-apply-behind (flagged per the brief)

Rider 1 touches `bin/bale_apply.py`'s walkthrough revert branch, so
**this session's own apply runs the old, unthreaded walkthrough code
one last time**. Concretely: if you choose the revert action at this
apply's walkthrough, the discard runs quiet even under `--verbose`.
The retry half is the same shape (`bin/bale`'s cmd_retry). From the
next session on, both stream.

## Suite report (enumerated from the tree)

Baseline, pre-change, on the assembled tree (bin/ docs/ schemas/
tools/ scripts/ tests/ + install.sh + BALE.md): **245 tests, all
green** — matching 006's expectation; the baseline shipped complete
this time. Post-change: **249 green** (the 4 new parity pins in
`tests/test_verbose_thread.py`, pinned-behavior section 5).
`validation.sh` re-runs the full suite in staging (~70s, inside the
§7.6 budget) alongside the pinned-span, wiring, version, and
exec-bit assertions.

## Judgment calls worth finding without the diff

- **Pins live in the 005 suite, not a new file.** The rider completes
  the thread that suite pins, and its fixtures (`make_held_session`,
  `build_response_tarball`, the pty runner) are exactly what the new
  tests need. Docstring updated to say so.
- **The walkthrough-revert pins drive the prompt over a pty**
  (`run_bale_pty`, answering `r`), since the piped path takes the
  inspect/merge default and can never reach the revert action.
- **Comment style at both call sites** mirrors cmd_revert's existing
  threaded-call comment, tagged v0.4.0 and naming the rider.

## Scope

Every `changes[]` path (BALE.md, bin/bale, bin/bale_apply.py,
tests/test_verbose_thread.py) sits inside the declared scope — no
drift to admit at apply.

## Proposals

- **What:** Prune the other stale span in BALE.md §7.2's closing
  paragraph: "This is overridable via `.bale.toml` in v0.5+" (the
  `manifest.project` note, ~line 1080).
- **Why:** Seen while locating this session's §7.2 span. It's stale
  twice over — the filename is `bale.toml` everywhere else in the
  doc, and the config subsystem the sentence defers to v0.5+ has
  existed since v0.0.3 (`bale config init`, the walk_configurables
  contract). Whether a project-name key should actually exist is a
  separate call; the sentence misstates today's state either way.
  Out of this session's byte-scope by the constraint, so proposed
  rather than done.
- **Scope hints:** BALE.md §7.2 only (one sentence); pairs naturally
  with the first post-cut doc session rather than a code session.
