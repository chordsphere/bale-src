# notes.md — 2026-08-25-board-50-crlf-tolerance-004

The brief's rehearsal held up: one real code change, the rest pins,
survey, and true-ups. Nothing out of forecast — every `changes[]`
path lands under `bin`, `tests`, `BALE.md`, or `docs/TARBALL.md`.

## The read-site survey (decision 5), one-line dispositions

Grepped `read_text` / `read_bytes` / `.open(` / `splitlines` across
`bin/bale` and every `bin/*.py`; each site verified in source, not
recalled. Grouped where the disposition is identical:

- `--checkpoint-file` ingest (`bale_pack.py`) — **the change**:
  `read_bytes` now normalized via `normalize_crlf` before the empty
  check, the commit, the echo, and the stamp.
- `--readme-file` (`bale_pack.py:~3022`) — tolerant via
  `read_text(encoding="utf-8")` universal-newline translation;
  **pinned** (`ReadmeCrlfPinTest`). Verified myself per the brief:
  the shipped README is the LF body and the echoed sha256 is the
  LF-bytes hash.
- `bale.toml` (`bale_config.py` → `_bale_toml.py:341`) — the vendored
  TOML reader replaces CRLF with LF per spec; **pinned**
  (`ConfigCrlfPinTest`, exercised end-to-end through a real pack that
  resolves a `{sid}` base out of a CRLF config).
- `.baleignore` (`bin/bale:~1700`) — `read_text().splitlines()`;
  the brief flagged this unexercised at the desk, so the pin is E2E:
  a CRLF `*.log` pattern prunes the walk (`BaleignoreCrlfPinTest`).
- Bundle members (`bale_open.py`) — already normalized (board 49);
  untouched, and its docstring's stale forward reference to board 50
  trued up.
- Response-tarball members (`bale_apply.py`/`bale_staging.py` tarfile
  reads) — hash-pinned worker bytes, **byte-exact by design**, out of
  this rule's reach per the brief; no change, deliberately.
- Probe files — **no bale-side probe-file read exists** (the brief
  asked for this finding explicitly): `bale_open.py:281`'s
  `output.splitlines()` is captured subprocess output of the
  checkpoint dry-run, not a file read; paste-back probes ride chat
  and the fallback ships in `context/` as ordinary includes. Nothing
  to normalize; recorded rather than invented.
- Everything else — internal state bale itself writes (counters,
  stamps, locks under `.bale/`), JSON manifests/telemetry
  (`read_text` universal newlines, and JSON tolerates CRLF as
  whitespace regardless), `.gitignore`/handoff/report display reads
  (`read_text`/`splitlines`), the editor temp file, `bin/VERSION` —
  all tolerant already or never transported; no change.
- `bale_pack.py:966` hashes the *installed* global docs via
  `read_bytes` for the provenance block — install-local, not
  transport-facing; left byte-exact on purpose (normalizing there
  would silently change published contract-doc hashes).

## Two edges I reviewed and left as-is (worth a glance at review)

- **Working-tree collision in `install_checkpoint_file`**: the
  absent-from-HEAD branch compares the raw working-tree file at the
  resolved path against the *normalized* delivery. A CRLF
  working-tree twin therefore refuses ("bytes differ") rather than
  proceeding. That's the correct posture: on match, that branch
  stages the *working-tree* bytes, so accepting a CRLF twin would
  commit a CRLF oracle and break the committed-oracle-is-LF
  invariant. The refusal is loud and names the remedy.
- **Legacy CRLF-committed oracle**: if a pre-board-50 project ever
  committed a CRLF oracle at a `{sid}` path, a re-delivery of the
  same file now refuses (normalized delivery ≠ committed CRLF)
  instead of taking the idempotent branch. Loud, correct
  (committed-is-ratified; the planner recommits deliberately), and
  vanishingly rare — the pre-board-50 flag would have had to ingest
  CRLF bytes that the desk's own dress rehearsal (per the brief)
  showed mismatching hashes anyway.

## Doc lines swept (decision 6's enumeration)

1. `BALE.md` bundle-normalization paragraph — "repo-wide CRLF
   tolerance is board 50's, not absorbed here" → points at the
   landed behavior (ingest normalization + test-pinned tolerant
   reads + response members byte-exact).
2. `docs/TARBALL.md` §3.4 `--readme-file` row — normalization
   sentence added where the row states the echoed sha256.
3. `docs/TARBALL.md` §3.4 `--checkpoint-file` row — "commits the
   file's bytes" now states CRLF-normalization at read, LF hashes at
   echo/stamp, normalized idempotency, byte-exact downstream.
4. `bin/bale_open.py` `normalize_bundle_member` docstring — the
   survey proved its "this is not board 50's" forward reference
   stale the moment this session lands; trued up while keeping the
   bundle-only scoping intact.

No other stale line surfaced: `test_doc_crossrefs` and
`test_global_doc_selfcontainment` pass against the edited docs.

## Test validity, verified both directions

The two normalization tests (`test_crlf_delivery_commits_lf_oracle_
with_lf_hashes`, `test_crlf_twin_of_committed_lf_oracle_is_
idempotent`) **fail against the unpatched tree** and pass against
the patched one — they pin the change, not the weather. The bare-CR
and differing-bytes tests pass on both trees by design (those
behaviors were already true; they pin the rule's boundaries). Fixture
files are written with `write_bytes` throughout — `write_text` would
retranslate newlines and quietly test nothing.

## Validation notes

- The full-suite check is gated behind `--slow` (it alone runs
  ~2 min, past the §7.6 target); the default run covers the board-50
  suite plus nine touched-surface suites in well under a minute. A
  default run therefore reconciles the full-suite claim as `[n/a]`
  (verdict=skip) — expected, not a gap; I ran `--slow` in rehearsal
  and it passed (567 tests).
- One invocation subtlety baked into `validation.sh`: suites run as
  `python3 tests/<suite>.py`, never `python3 -m unittest
  tests.<suite>` — the dotted form leaves `tests/` off `sys.path`
  and breaks the harness's bare-name import (its docstring names the
  two supported run modes).

## Proposals

### claude/MASTER.md §7 CRLF-line sweep

- **What**: retire §7's standing-wart line about the Downloads sed
  ritual now that board 50 lands the tolerance it describes.
- **Why**: the request names it out of scope for this session — it
  rides the sitting-close deltas after ratification per the
  masters-land-it convention — but the line goes stale the moment
  this response applies, so it belongs near the top of the close's
  delta list.
- **Scope hints**: `claude/MASTER.md` §7 only; after this response
  is ratified.
