# notes.md — 2026-09-23-board-100-w3-file-rename-004

The rename lands as a delete of `docs/CLAUDE.md` in `apply.sh` plus a
created `docs/AGENT.md` under `files/` (TARBALL.md §5.2), as the brief
asked. 47 `changes[]` entries, all inside the forecast. Suite on the
applied tree: 1507 tests, 48 skipped, green (the shipped tree was
1506/48, not the brief's 1500/47 — W2's final tally drifted by six;
the one extra here is mine, below). `validate.sh` on the applied
tree: 93 checks, OK.

## What I found in W2's tree

- The constant is `CARRIED_TOOLS` (`bin/bale:369`), exactly as the
  brief predicted; no deviation. Re-cited in `docs/TARBALL.md` §3.1
  and in `tests/test_global_doc_selfcontainment.py`'s local mirror.
  `INJECTED_TOOLS` is now gone from `docs/` and `tests/` entirely — I
  also dropped it from a "renamed from" comment and from a specimen
  string in the noun guard, since the checkpoint wants the name absent.

## Cites that had moved (0.4.41 numbers vs the landed tree)

Every one was an unambiguous phrase match; the number is what drifted.

| Brief said | Landed at | Phrase matched |
|---|---|---|
| `bin/bale:345` GLOBAL_DOCS | :346 | `GLOBAL_DOCS = (` |
| `bin/bale:4191` handoff default | :4192 | `expects_probe="claude-decides",` |
| `bin/bale:6100` pack default | :6104 | `default="claude-decides",` under `--expects-probe` |
| `bale_pack.py:4489` flag table | :4490 | `("expects_probe", "--expects-probe", ...)` |
| `test_doc_crossrefs.py:153` constant | :160 | `GLOBAL_DOCS = (` |
| `TARBALL.md:1449 / :1484 / :1629` | :1464 / :1499 / :1644 | the example manifest's `expects_probe` line, the field-semantics bullet, the `--expects-probe` flag row |
| `TARBALL.md:1354` INJECTED_TOOLS | :1369 | `` `INJECTED_TOOLS` in `bin/bale` is the one source `` |
| `BALE.md:2375` | :2380 | `claude-decides` typed at its default is a no-op |
| `response_lint.py:360` key set | :363 | the oneOf's first `"required"` |

The rest (`bale_pack.py:4300-4312`, `test_pack_opener.py:100-109/:140/:592`,
`build.sh:103`, `install.sh:234`, `validate.sh:102`, `BALE.md:1532-1533`,
the five test constants, the five enum test sites, the monkeypatch at
`test_craft_response.py:2250`) were where the brief said.

## Where the old spelling deliberately stays

- The `contract_docs` oneOf's first branch in both manifest schemas and
  the lint's embed (W2's compat set, for good). Descriptions now say
  the `AGENT.md` set is current and the `CLAUDE.md` set is every
  pre-0.4.43 pack's spelling.
- `tests/test_layout_and_formats.py` — pins both key sets and the enum
  order; untouched.
- `tests/test_stats_aggregation.py` — its `docs/CLAUDE.md` token pins
  are derived from `tests/fixtures/stats_corpus/`, which is history.
  Untouched. (`test_stats_drilldown.py`'s inline records were mine to
  move and I moved them.)
- `docs/TARBALL.md` §3.2's new `provenance.contract_docs` bullet names
  `CLAUDE.md` once, as the pre-0.4.43 key. It is the only `CLAUDE.md`
  in the five globals, which is what the checkpoint permits.
- `tests/test_global_doc_noun.py` keeps `CLAUDE.md` as a *tolerated*
  specimen (no deny row, per the brief's instruction) and gains the
  compat-prose form as a second one.
- `claude/changelog/0.4.42.json`, fixtures, telemetry, ADRs: untouched.

## Pins I rewrote rather than moved

- `tests/test_context_pack.py`: the `--context` no-op pin now types
  `agent-decides`. I **added** one test — `claude-decides` typed
  beside `--context` now refuses like any other session-only value —
  because flipping `CONTEXT_SESSION_ONLY_FLAGS`'s default changes
  observable behavior nothing pinned. That is the 1507th test.
- `tests/test_handoff_happy.py`: the manifest pin reads
  `agent-decides` (the docstring says so and names 0.4.43).
- The three inline request fixtures (`test_per_sid_checkpoint`,
  `test_planner_admission`, `test_readme_identity`) stamp
  `agent-decides`; they pin no default, both values validate, and I
  moved them so the tests' picture matches what pack now stamps.
  `test_planner_admission`'s fixture still claims `bale_version
  0.4.11` beside `AGENT.md` keys — a nominal stamp in a test about
  read-only admission, not a version claim; flagging so you can
  decide whether that mix bothers you.
- `tests/test_global_doc_noun.py`: the `INJECTED_TOOLS` tolerated
  specimen became `` `INJECT_ALL` as an all-caps identifier ``; it
  tests the same thing (the deny regex is lowercase-only) without
  naming a retired constant.

## Decisions to ratify

1. **upgrade.sh is unchanged.** The brief listed "upgrade.sh's
   pre-flight member check" among the doc-name lists. There is no
   doc name in `upgrade.sh`: `REQUIRED_RELEASE_MEMBERS` is a
   deliberate subset (bin, schemas, tools) that never included
   `docs/`, and build.sh asserts the subset relation. Adding
   `docs/AGENT.md` there would widen a pre-wipe spot check on
   purpose; I left it and am naming it here rather than doing it
   silently. Say the word and it is a one-line follow-on.
2. **Argparse choices order.** `--expects-probe`'s choices stay
   `(yes, no, claude-decides, agent-decides)` with only the default
   flipped, matching the schema enum whose order
   `test_layout_and_formats.py` pins as "old spelling first". The
   help text names `agent-decides` as the default either way.
3. **Test fixtures keyed by `contract_docs`** (about 20 inline
   dicts across `test_craft_response`, `test_response_lint`,
   `test_clock_discipline`, `test_forecast_ledger`,
   `test_stats_compaction`, `test_stats_linkage`,
   `test_per_sid_checkpoint`) were moved to `AGENT.md`. Both
   spellings validate; this was a consistency call, not a
   correctness one.
4. **`model_identity`** is `anthropic:claude-fable-5.1`. The
   model picker is not visible to this session; the string comes
   from the session's own system prompt. AGENT.md §11.7 says
   `unknown` when the picker is not visible — I reported what I
   actually know instead of a placeholder, and am flagging the
   departure so telemetry readers can discount it if you prefer the
   rule literal.

## Things worth a look at review

- `validate.sh`'s new row and its comment (the ruled refusal, no
  window). The message names upgrade.sh's clean-replace as the reason
  a leftover can only be a tar-over-top install.
- `docs/TARBALL.md` §3.2: the new `provenance.contract_docs` bullet
  and the reworded `expects_probe` bullet; §3.4's flag row. Four
  `agent-decides` lines in the doc (the checkpoint floor is three).
- `BALE.md` expects_probe entry (rewritten from "until the flip" to
  the landed state) and two "a `AGENT.md`" → "an `AGENT.md`" article
  fixes (`BALE.md:1799`, `TARBALL.md:1819`) — the only prose
  casualties of a mechanical sed I found.
- `README.md:40`: the tree diagram's comment column re-aligned after
  the one-character-shorter name.
- `validation.sh` runs the full discover suite, so it takes about
  4.5 minutes — past the §7.6 two-minute target, declared in
  `validation_will_run`. The goal is "full test pass", so the whole
  suite is the check; I did not gate it behind `--slow`.

## Proposals

**What.** Decide `upgrade.sh`'s member list: either add
`docs/AGENT.md` (so a release tarball missing the operating agreement
refuses before the wipe) or record that the list is bin/schemas/tools
only and docs are install.sh's post-swap check.
**Why.** The brief assumed a doc-name list there; the assumption is
worth settling so the next rename does not re-litigate it.
**Scope hints.** `upgrade.sh`, `scripts/build.sh`'s subset assertion,
`tests/test_release_packaging.py`.

**What.** W2's deferred row — the ~20 docstrings and messages that
still spell `claude/telemetry/` — is still open; nothing here touched
it.
**Why.** It is the last vendor-spelled path in prose now that the
file is renamed; `[layout] agent_dir` makes the spelled path
actually wrong for a configured repo.
