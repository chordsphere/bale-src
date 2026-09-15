# notes — 2026-09-15-board-102-explicit-name-010

## What landed, and the three calls you asked me to cite

**The BALE.md paragraph.** Your sentence sits at the end of the §8
"bare form" paragraph — the one that opens `**The bare form** (board
51, v0.4.16; …)` and names "the surface the argumented form's
relative-name resolution searches". I looked at the other two homes
you offered: the "apply/retry/handoff's tarball and pack's
`--readme-file`" paragraph is §3's config-init walkthrough (step 3 of
the deployment list), and §8 has no standalone apply-argument
paragraph — its opening is two sentences about what apply does, with
no mention of resolution at all. The bare-form paragraph is where §8
already talks about the searched directories and the explicit
`bale apply <response-tarball>` form, so the sentence reads as its
closing line rather than a bolt-on. It's one physical line, appended
after "beside the worker." with no reflow of the surrounding text
(byte-exact per your validation.sh needle, `grep -Fx`).

**Handoff got the listing.** Threading the verb was one keyword
argument per caller, so `bale handoff <miss>` now lists candidates as
`bale handoff '<path>'` lines. Your sentence names apply and retry
only — I left it verbatim as instructed; if you want handoff named in
the doc, that's a one-word edit on your side. The tests pin all three
verbs.

**The docstring rider.** The false sentence in `bale_apply.py`'s
module docstring now reads: "`bale_pack` never imports the apply path
(the per-response `validation.sh` asserts that direction), and this
module imports `bale_pack` only lazily, inside `bundle_change_paths`
(for the bundle-suffix recognizer, `is_bundle_file`) — never at module
scope." The lazy import at ~line 1147 is untouched. validation.sh
asserts all three facts: the old claim is gone, the lazy import is
still there, no module-scope import appeared.

## Shape of the listing

```
[bale] error: tarball not found: response-2026-09-15-foo-001.tar.gz
  searched:
    /home/chord/proj  (cwd)
    /mnt/c/Users/chord/Downloads
  near-name candidates (newest first):
    bale apply /mnt/c/Users/chord/Downloads/response-2026-09-15-foo-001-v2.tar.gz
    bale apply '/mnt/c/Users/chord/Downloads/response-2026-09-15-foo-001 (1).tar.gz'
```

Details worth knowing at review:

- Prefix = typed basename minus `.tar.gz`. A typed name without the
  suffix is its own prefix, so `bale apply response-<sid>` (the
  tab-completion-gave-up case) lists `response-<sid>.tar.gz`. An
  empty prefix (typing literally `.tar.gz`) matches nothing.
- A directory component in the typed name (`Downloads/foo.tar.gz`
  relative) narrows the scan to that subdirectory of each consulted
  directory — the same place the exact match was looked for.
- Candidates are resolved absolute paths, deduplicated (cwd is often
  also a configured search path). Sort is `st_mtime_ns` descending,
  name ascending on a tie, so the order is deterministic.
- The helper never opens a file and never raises: an unreadable
  directory contributes nothing, same as an absent one. It runs only
  on the miss path, so the hit path's cost is unchanged.
- `verb=None` (the default) keeps the pre-listing refusal exactly, so
  pack's `--readme-file` and open's bundle argument are untouched.

## One-apply-behind

This change lands apply-path code (`bin/bale`'s resolver and
`cmd_apply` in `bale_apply.py`). The apply that lands it runs the old
resolver one last time: if you mistype this response's own tarball
name, that refusal will not list near-names. The very next apply
will.

## Forecast

All five `changes[]` paths are inside the recorded forecast; nothing
to admit. `tests/test_apply_operations.py` was forecast but is
untouched: the near-miss surface has no operations half, and every
new case lives beside the bare-apply downloads fixture and refusal
helpers in `test_apply_preflight.py` (recorded in `deferred`).

## Where to look

- `bin/bale` ~1433–1570: `resolve_inbound_path`'s new `verb` kwarg and
  the listing branch; `near_name_candidates` directly below it.
- `bin/bale_apply.py` ~650: the quoted non-TTY line. Existing tests
  that assert `str(newest)` in that refusal still pass because
  `shlex.quote` is the identity on a path without metacharacters —
  the new case delivers a `response-twin (1).tar.gz` fixture so the
  quotes actually appear.
- `tests/test_apply_preflight.py`: `ExplicitNameMissTest` at the end
  of the file. All nine cases fail against the 0.4.32 tree except the
  zero-candidate pin, which passes on both by design.

## Assumptions proceeded on

- The listing header wording ("near-name candidates (newest first):")
  and the two-space/four-space indentation mirror the existing
  "searched:" block. Nothing pins the header text but my own tests;
  rename freely.
- The full default suite runs ~145–170 s in this sandbox, over §7.6's
  two-minute target, so validation.sh gates it behind `--slow` and
  runs the two apply suites by default (~15 s). I ran it with
  `--slow` here: 1022 tests, OK, 48 skipped.

## Proposals

**Extend the listing to the other two miss branches.** Today an
absolute path that doesn't exist, and a relative name with no
`apply.search_paths` configured, fail in each caller with the bare
`tarball not found: <path>` — three copies (apply, retry, handoff)
of the same line, none of which see the resolver's listing. The
absolute case matters more than it looks: a shell-completed
`~/Downloads/response-<sid>.tar.gz` that the browser actually saved
as `… (1).tar.gz` is exactly the twin the prefix rule catches, and
`near_name_candidates` already handles it if handed the path's
parent as the sole consulted directory. Scope: `bin/bale` (a small
`fail_not_found(kind, path, verb)` helper the three callers share,
which would also retire the triplicated line), `bin/bale_apply.py`'s
call site, and a few cases in `ExplicitNameMissTest`. Independent of
anything else in the wave.
