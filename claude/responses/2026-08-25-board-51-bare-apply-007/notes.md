# notes — 2026-08-25-board-51-bare-apply-007

## Decisions the brief asked me to state

**"Newest" semantics.** Newest is file modification time at nanosecond
stat granularity (`st_mtime_ns`), which makes "the download that
arrived last" win — the re-delivery case I take the feature to exist
for. There is deliberately **no secondary tie-break**: an exact
`st_mtime_ns` tie refuses, naming every tied path. I read the ratified
contract's "ambiguity — two candidates ... refuses" as *two candidates
the newest-rule cannot separate*, not as *two candidates at all* —
otherwise "resolves the newest" would never have work to do. If you
meant the stricter reading (any second candidate refuses), the change
is one conditional in `resolve_bare_apply_tarball` and two test edits;
say so and I'll re-deliver.

**Response/request discrimination.** Content-based, never
filename-based: a candidate must be a readable gzip tar containing a
`response-NNN/manifest.json` member whose `responds_to` is a non-empty
string naming the open session. A request tarball's single top-level
directory is `request-NNN/`, so it has no such member and is
structurally never a candidate — however new it is, and whatever a
browser renamed it to. The peek (`_peek_bare_candidate`) is a
non-fatal sibling of `_peek_responds_to` rather than a parameterization
of it, because the two callers want opposite failure postures: the
argumented multi-open path holds exactly the file the user named
(unreadable = fatal), while the bare scan walks a Downloads directory
where clutter is a skip with a reason, never an exit. Skips are
reported per-file under `--verbose` and always in aggregate — folded
into the refusal message itself on the no-candidate path, so stderr
alone tells the whole story.

**The y/N.** Follows the decline-default precedent (`--supersedes`,
v0.3.17) exactly: TTY gets `confirm_yn` with decline as default; piped
stdin takes the decline without a prompt and refuses with the
explicit-form remedy. Two adjacent decisions worth ratifying:

- **An interactive decline exits 1** (via `fail()`), matching the
  declined-supersession posture — a bare apply that resolved something
  the operator rejected did not do what was asked, and exit 0 would
  let automation mistake it for success. If you'd rather a decline be
  a clean 0, it's a two-line change.
- **`--no-interact` (flag or config) contradicts the bare form and
  refuses up front**, before any scanning. The identity echo + y/N is
  what makes argument-less resolution safe; a mode whose point is
  skipping prompts would turn bare apply into "apply whatever is
  newest," which is the guess the contract forbids. The explicit form
  is the non-interactive spelling.

## Other judgment calls

- **Inspection flags refuse the bare form.** `--show-validator` /
  `--show-apply-script` are deliberately session-independent, and bare
  resolution is keyed on the open session, so the two don't compose;
  the refusal names the explicit spelling. **`--dry-run` composes**
  with the bare form: it already requires the open session, and it
  runs through the same echo + y/N before the read-only pipeline — the
  confirmation is about identity, which matters for a dry-run's report
  too. (No dedicated test for bare+--dry-run; the shared resolution
  path is fully covered and the dry-run half is pre-existing. Flag if
  you want the pin.)
- **Scan surface is non-recursive `*.tar.gz`** in cwd plus each
  configured directory, cwd first — the same directory set and order
  `resolve_inbound_path` searches. Directories and candidate files are
  deduped by resolved path so a cwd that is also configured, or a
  symlinked twin, counts once.
- **Ordering inside `cmd_apply`:** the bare branch resolves after the
  inspection-flag refusal and after `--json` enables its stream swap,
  so the echo and prompt land on stderr under `--json`. The argumented
  path is byte-for-byte the previous code (the resolution block gained
  only an `if args.tarball is not None:` indent); the new test class
  pins that naming the tarball still applies with no bare-resolution
  output.
- **Refusal-before-scan order** in the bare resolver: no-interact
  contradiction → zero open sessions → multiple open sessions → scan.
  So `bale apply --no-interact` (bare) reports the contradiction even
  when no session is open — the contradiction is the operator's
  actionable mistake either way.

## Staleness caveat, applied

The brief flagged section-numbered citations for verification against
the applied tree. The ones I relied on I matched by stable phrase:
the decline-default precedent ("piped stdin takes the decline default
without a prompt", `_resolve_supersession` in `bin/bale_pack.py`), the
stream discipline ("stdout is reserved for the one-line report",
`cmd_apply`), and the exec-bit restore/assert pair (TARBALL.md §5.1.1
/ §7.7 — both phrases present in the shipped doc). No mismatches
found.

## Forecast

All three `changes[]` paths are inside the stamped `resolved_scope`;
no out-of-forecast work, no new files (extending the forecast test
file was cleaner than a new suite — the class reuses its refusal
doctrine and the harness builders). `bin/VERSION`, `bin/bale_report.py`,
and `BALE.md` are untouched per the desk rulings; the sibling's three
forecast paths are untouched.

## Proposals

### Version bump (desk-landed per the hot-file ruling)

**What:** `bin/VERSION` bump for the pair — the description text I
shipped names the bare form as v0.4.16; if the desk lands the pair
under a different number, that one string in `bin/bale`'s apply
description should ride the rider session's edit.
**Why:** the pair shares one bump landed by the desk after both apply;
enumerating it here is the ruling's prescribed path.

### BALE.md apply-side documentation line (pair-close rider)

**What:** one paragraph in BALE.md's apply section: bare `bale apply`
resolves the newest response tarball answering the single open session
across cwd + `apply.search_paths` (content-discriminated, request
tarballs never candidates), echoes path/sid/sha256/mtime, and takes a
decline-default y/N; no-candidate, tie, no-open, multi-open, and
non-interactive outcomes refuse with remedies.
**Why:** BALE.md rides the sibling per the desk ruling; the behavior
landed here needs its contract-doc line at the rider.
**Scope hints:** BALE.md only; after both siblings apply.

### Bare forms for `bale retry` and `bale handoff`

**What:** the same argument-less resolution for retry (newest tarball
answering the sid being retried) and handoff (newest bailout tarball).
**Why:** both resolve their positional through the identical
`resolve_inbound_path` surface, and the save-one-file/one-paste floor
argues the same way; but retry's re-attempt semantics and handoff's
bailout-kind filter each need their own candidacy rule, which the
goal's apply-only wording kept me off.
**Scope hints:** `bin/bale` (two positionals), `bin/bale_apply.py`
(retry shares `resolve_bare_apply_tarball` with a sid parameter),
`bin/bale`'s cmd_handoff; only after this session lands.
