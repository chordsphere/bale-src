# notes.md — 2026-09-15-board-90-doc-residue-005

Four edits, three files, all inside the write forecast. Bumpless per
the desk ruling: `bin/VERSION` untouched. `changes[]` is exactly the
forecast (`validation.sh` asserts that from the staged manifest), so
there is no drift to admit.

## The four edits

1. **`BALE.md` §8, "The bare form".** Rewritten around the ruling of
   record, which sits in the paragraph VERBATIM (wrapped; the words
   are the desk's). The paragraph now walks the scan surface (cwd,
   then each `apply.search_paths` directory, non-recursive,
   content-discriminated, request tarballs never candidates), the
   ruling, the echo (`the open session` / `one of N open sessions:
   …`, as the resolver renders it), the decline-default y/N, and the
   four refusals that remain — no candidate, an exact mtime tie, no
   open session, non-interactive stdin. The multi-open refusal is
   gone; the closing sentence says *why* several open sessions is not
   a refusal (`responds_to` is one string; the only genuine ambiguity
   is the tie) and names the case that motivated it — the read-only
   master always open beside the worker. Cut that last sentence if you
   want the paragraph to carry only the contract; the verbatim check
   does not depend on it.
2. **`BALE.md` §5.4, the `--no-interact` bullet.** One sentence
   appended after the store's shape: `bale config hooks` lists
   oldest-first, `--forget <sha256 or unique prefix>` removes exactly
   one (prompt-free, says what it removed, refuses ambiguity or a
   miss, no forget-all), `--json` is status-shaped. Tagged
   `(board 83)` with no version, since row 83 landed bumpless.
3. **`bin/bale`, the apply parser's `description=`.** The bare-form
   sentence no longer says "with exactly one session open" and the
   refusal list no longer includes "more than one open session"; it
   states the contract condensed from the §8 paragraph (any open
   session; newest mtime wins; exact tie refuses; the echo names the
   session and the open set; the four remaining refusals). Tagged
   `v0.4.16; widened v0.4.29`. This is the only `bin/bale` edit — the
   `revert` and `unlock` parsers are untouched, and
   `validation.sh`'s assertion reads only the apply subparser's
   description span.
4. **`docs/TARBALL.md` §1, "Artifact directories".** One clause after
   "zero-padded to three digits": the tarball that carries each is
   named by the full session id — `request-<sid>.tar.gz`,
   `response-<sid>.tar.gz` — with pointers at §3.1 and §10.1 step 11.
   The rest of the bullet is preserved text. No board or evidence
   citation (the self-containment guard; also asserted locally).

## The verbatim landing and its self-check

`validation.sh` extracts the bare-form paragraph alone (from
`**The bare form**` to "The pipeline below describes a normal
response."), whitespace-normalizes it, and asserts the ruling
sentence byte-exact inside that span — a hit elsewhere in the file
would not count. A sibling check asserts the board-51 phrases are
gone from the same span and the current elements are present. I ran
the script against the unedited context: the verbatim check, its
sibling, the §5.4 check, the `bin/bale` check, the §1 check, and the
`apply --help` wording check all fail there, and pass on the edited
tree. The four doc-pin suites are green on both, as the doc lane's
note predicted — no pin touches these passages.

## Registry rider — §7 / §7.2 includes-as-scope true-up

I read §7 while in the file. §7.2's includes bullet already says the
include set is the read set and participates in no gate; the write
forecast bullet carries ADR-0015's language; §7.1 step 5 says "Read
includes participate in nothing here." The remaining places §7
mentions the include set as a forecast are all the absent-`--write`
compatibility default (forecast = resolved include set), which is
correct, not residue. Nothing to fix; the entry can close at this
sitting's close.

## Calls I made (ratify or correct)

- **The echo's rendering is quoted in §8** (`the open session`, `one
  of N open sessions: …`) rather than described abstractly, so the
  paragraph and the terminal read the same. It couples the doc to
  two literal strings in `bale_apply.py`; if you would rather the doc
  stay one level up, replace the parenthetical with "alone when one
  is open, beside the full open set otherwise".
- **§8's tie refusal notes that each tied path is listed with the
  session it answers** — the widening row 87's notes flagged. Small,
  but it is the one visible face of "any open session" an operator
  meets, so I named it.
- **The `bin/bale` description says "newest by modification time"**
  rather than `st_mtime_ns`: help text is operator-facing and the
  stat field name belongs in BALE.md. The words "an exact tie
  refuses" ride verbatim.

## Where to look at review

- `BALE.md` §8's paragraph — the one place with prose of my own past
  the ruling sentence.
- `bin/bale` line ~5895: confirm the condensed string reads well in
  `bale apply --help` (the scratch-install check only asserts exit 0
  and the wording's presence/absence).

## Claims

- `session assertions` — **observed**: rehearsed in a staging-shaped
  copy of the shipped context with `files/` overlaid, `apply.sh` run
  (exec bit stripped first, then restored), manifest placed as
  `.bale-manifest.json`, `validation.sh` run from outside the tree.
- `bale apply --help (scratch install)` — **observed**: exit 0 via
  `tests/harness.py`'s `make_install` in a mktemp dir.
- `unittest: doc-pin suites` — **observed**: 4 suites green.

## Proposals

- **What:** the apply positional's own help string still reads
  "resolve the newest response tarball answering the open session
  across cwd and apply.search_paths" — singular. **Why:** not wrong
  under single-open and not a refusal claim, so it sat outside the
  brief's one-string scope; but beside the rewritten description it
  is the last board-51 phrasing in the parser, and it is two words
  (`an open session`). **Scope hints:** `bin/bale`, the `tarball`
  positional's `help=`; trivial, next `bin/bale`-touching session.
- **What:** a `bale config hooks` row in `BALE.md` §5's command
  table. **Why:** §5.4 now points at the verb, but the table — the
  surface that claims to be "the full target surface" — has rows for
  `config init` only. **Scope hints:** `BALE.md` §5, one row; a doc
  lane.
