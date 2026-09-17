# Notes — 2026-09-16-board-69-tools-pair-008

Board 69 on the tools pair, bumpless: all four halves, one light block,
and the extraction answer in Proposals. Every `changes[]` path is inside
the forecast. No new file was shipped (the pin's home is
`tests/test_craft_response.py` — see [1] below), so there is nothing to
admit at apply.

## The light question block (the trail, §5.10)

I emitted one light block mid-session (hit a tool-use limit mid-build;
the block carried three real judgment calls rather than a prose pause).
Questions and answers:

- **[1] Pin home inside `tests/test_craft_response.py`?** — *yes, as
  assumed.* `ToolsHermeticPin` lives there.
- **[2] Keep an exact-import-set baseline beside the property checks?** —
  *no.* Ruling: assert the property, not the inventory. The pin asserts
  stdlib-only, no network-capable module, no dynamic import; 105's
  import set is recorded as a comment beside the class, never asserted.
  I had written the baseline test; it is removed.
- **[3] Seed `docs_read: []`?** — *yes, and make the unfilled stub loud.*
  Ruling: a warning-tier lint finding when `feedback.self_reported.docs_read`
  is present and exactly `[]`, message "fill it or delete the key";
  omission stays silent. Landed as its own registry row,
  **`docs-read-stub`**, code **`DOCS_READ_EMPTY_STUB`**, at
  `manifest.json:$.feedback.self_reported.docs_read`, the
  `CONTEXT_PREFIXED_DOCS_READ` tier (exit 0, `[WARN]`, `warnings[]`).
  The message carries the ruling's phrase verbatim plus why a present
  `[]` misleads.

## What landed

- **(a) `CLAIMS_VALUE`.** `CLAIM_VALUES` is restated in the lint with a
  comment naming `bin/bale_validate.py`'s `CLAIM_VALUES` as the mirror,
  in the style of the `GENERATED_ARTIFACT_DIRS` mirror. The check files
  one error per offending bare-string value at `manifest.json:$.claims.<key>`.
  It skips dicts and non-strings, so the object form (the embedded
  schema's enum) and type errors are never double-filed. The mirror is
  pinned twice in `ClaimsValueCheck`, by AST read rather than import: to
  the schema's object-form enum always, to `bin/bale_validate.py` where
  `bin/` ships.
- **(b) `docs_read: []`** in `FEEDBACK_SELF_REPORTED_STUB`, same inline
  comment style, plus the warning above.
- **(c) Single-quoted rider** — resolved by *accepting* the form: for
  `clipboard_command = 'pbcopy'` the reader returns `pbcopy`.
- **(d) `ToolsHermeticPin`** — a pure AST walk (nothing imported or run)
  over both tools, with a walker self-test so a broken detector fails
  instead of passing the tools vacuously.

## Judgment calls worth a look

- **`claims-value` is its own registry row.** Folding it into
  `manifest-schema` would flip `feedback.mechanical.schema_valid` to false
  on a manifest that *is* schema-conformant; folding it into
  `claims-subset` would do the same to `claims_subset`. A separate row
  keeps both derivations meaning what they say, and the bale side agrees
  in spirit (the enum is a cross-field Python invariant there, beside
  the subset rule, not part of the shape pass).
  `test_mechanical_derivations_are_unchanged` pins it.
- **The clipboard reader now applies bale's content refusals in both
  quote forms** (backslash, double quote, control characters), through
  one helper, `one_line_quoted_value`. This also closes a small
  pre-existing split the rider didn't name: a raw tab inside a *basic*
  string is legal TOML, bale's accessor refuses it, and the old scan
  returned it. Now both read it as unset.
- **One split remains, disclosed rather than parsed:** triple-quoted
  strings (`'''pbcopy'''`, `"""pbcopy"""`, and a `'''` opener followed by
  a newline). I confirmed `bin/_bale_toml.py` reads all three as `pbcopy`;
  the crafter's one-line scan reads them as unset, and its
  treated-as-unset note now says "triple-quoted multi-line forms are
  not read". Pinned in `CrafterAgreementTest`. The refusal side would
  live in `bin/bale_config.py` (out of scope) — proposed below.
- **`--probe`'s bash emission with a single-quoted value** needs nothing:
  the value is the command *inside* the quotes, and that command
  (`pbcopy`) is already what the double-quoted path produced.

## Surprise: a shallow copy in `build_feedback`

`build_feedback` seeded `self_reported` with `dict(FEEDBACK_SELF_REPORTED_STUB)`,
a shallow copy: every seed shared the stub's `assumptions`,
`judgment_calls`, `includes_missing`, and `compaction_occurred` objects
with the module constant and with each other. One CLI run builds one
seed, so nothing visible broke. But any in-process caller — the test
suites load the crafter as a module — would leak mutations across
builds. `CraftDocsReadStub.test_seeds_are_independent_copies` found it
on its first run. The fix copies each container per build, no new import,
and the test now covers every container key, not just `docs_read`.

## Where to look closely

- `tools/craft_response.py`: `one_line_quoted_value` (the whole rider)
  and the `build_feedback` comprehension.
- `tools/response_lint.py`: `check_claims_value`, `check_docs_read_stub`,
  and the two new registry rows (placed after `claims-subset` and
  `context-prefix` respectively; `feedback-block` still runs last).
- The crafter's index header line numbers were refreshed; later sections
  had drifted about 48 lines, near `CODE.md` §2.2's threshold.

## Validation, claims, and the bumpless constraint

- Claims are the annotated form, `claim_basis: "observed"`. I ran
  `validation.sh` in a simulated staging (the request's `context/` tree,
  `files/` overlaid with modes stripped, `apply.sh` run, the manifest
  placed at `.bale-manifest.json`): exit 0, 9/9 `[agree]`, about 23 s.
  The first dry run failed my own docs_read assertion on a thin fixture
  provenance (the echo schema requires four `contract_docs` keys); the
  fixture is fixed, the tools were right.
- **Negative control:** the same script against the unchanged tree fails
  the three board-69 outcome assertions, so they are not vacuous.
- **Bumpless** is asserted relative to the response: the check reads the
  staged `.bale-manifest.json` and fails if any `changes[]` path is under
  `bin/`. No `bin/VERSION` literal from the request tree appears anywhere.
- **Environment assumption:** `test_probe_clipboard_config`'s wizard tier
  needs git and a pty in staging. It `[SKIP]`s by name without git; in my
  sandbox both were present.
- `apply.sh` restores the exec bit on the three changed files that ship
  executable (`tools/craft_response.py`, `tools/response_lint.py`,
  `tests/test_craft_response.py`), and `validation.sh` asserts them (the
  crafter's epilogue, one `--executable` list).

## Proposals

### Answer to row 69's extraction question: not yet — one seam if ever

- **What.** Leave `tools/craft_response.py` whole. If a later session
  splits it anyway, the one real seam is the **exchange pair**: §5
  (`--emit-block`) together with §6 (`--light-block`) and their two CLI
  branches, as a second request-carried tool. Everything else stays.
- **Why.**
  - *Per-mode sizes*, measured on the shipped bytes (154 198 B, 3196
    lines; about 43 KB gzipped — the lint is 79 552 B, about 21 KB
    gzipped). Each figure is the mode's own section, its constants, and
    its CLI branch; each mode also carries a share of the 18 KB module
    docstring and the 10.5 KB `parse_args`:

    | Mode | Section | Constants | CLI branch | Total |
    |---|---|---|---|---|
    | `--emit-block` | §5, 27.9 KB | — | 3.3 KB | ~31 KB |
    | `--light-block` | §6, 9.6 KB | — | 3.5 KB | ~13 KB |
    | `--bundle` | §4, 7.4 KB | 1.8 KB | 7.1 KB | ~16 KB |
    | `--probe` | §3, 4.1 KB | 3.3 KB (scaffold, clipboard) | 3.4 KB | ~11 KB |

    The response-directory core (skeleton, paths, doc assertions,
    epilogue, the main CLI flow) is the remaining ~80 KB.
  - *The seam is real only for the exchange pair.* `build_light_block`
    calls §5's `question_row_problems`, and `ExchangeBlockParity` pins
    §5 against `bin/bale_relay.py` / `bin/bale_validate.py` as one unit.
    Splitting §6 from §5 would duplicate the row check or import across
    tools. `--probe` and `--bundle` are too small and too tangled in the
    shared slug/path helpers to earn their own files (`CODE.md` §4.5's
    thin-unit rule).
  - *A split saves no bytes per request.* Every mode is used from inside
    a request: workers emit probes, light blocks, exchange blocks, and
    (for pack offers, `PLANNER.md` §2) bundles. The request still ships
    all of it, in two files instead of one. The only gain is
    navigability, and the index header plus banner sections already
    provide it (`CODE.md` §5.1 condition 2 is not met).
  - *The cost is doctrinal, not mechanical.* `CLAUDE.md` META's
    reachability model names the two request-carried tools, every
    `§3.1` mention and the pack injection surface would move, and the
    lint and crafter's "share no code" guard would need a third party
    to the rule.
- **Scope hints.** Revisit if §5 plus §6 grows past about 60 KB, or if
  sessions touching the exchange pair stop touching the rest (`CODE.md`
  §4.2's "typical sessions touch the section without its neighbours").
  A split is a dedicated session: docs (`CLAUDE.md` META, `TARBALL.md`
  §3.1), `bin/bale_pack.py`'s injection list, and both test suites move
  together.

### Refuse triple-quoted `clipboard_command` values bale-side

- **What.** Have `bin/bale_config.py`'s `get_probe_clipboard_command`
  refuse, or the renderer normalize, a value that came from a
  triple-quoted string. The accessor sees only the parsed string, so this
  likely needs a raw-line check at read time.
- **Why.** Grounded here: bale's parser reads `'''pbcopy'''` as `pbcopy`
  and reports the opt-in configured, while the crafter reads it as unset
  and emits remedy text. That is the "right or loud, never split"
  disagreement the accessor exists to refuse. Today it is only named in
  the crafter's note.
- **Scope hints.** `bin/bale_config.py`,
  `tests/test_probe_clipboard_config.py`. Flip
  `test_unread_triple_quoted_forms_are_named_in_the_note` into an
  agreement test when it lands.

### Document `DOCS_READ_EMPTY_STUB` where the stub is taught

- **What.** One sentence in `TARBALL.md` §5.2.2's `self_reported` walk:
  the crafter seeds `docs_read: []`, the lint warns on it unfilled, fill
  it or delete the key.
- **Why.** The schema description says omission means "reported
  nothing". Before this session, nothing said a *present* `[]` is read as
  "read nothing", and the global docs are the contract workers read
  before they see the lint's warning.
- **Scope hints.** `docs/TARBALL.md` only, a doc-lane session; ride the
  next §5.2.2 touch.
