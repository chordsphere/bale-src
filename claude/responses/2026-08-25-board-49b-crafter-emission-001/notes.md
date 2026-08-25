# Notes — 2026-08-25-board-49b-crafter-emission-001

The rider landed (it did not need deferring). Every `changes[]` path
is inside the stamped write forecast (`BALE.md`, `bin/VERSION`,
`docs/TARBALL.md`, `tests`, `tools`, `validate.sh` — the directory
entries cover the test and tool files). No probe or clarification
round occurred.

## Latitude decisions (mechanism authority; ratify or correct)

- **Flag surface.** `--bundle STEM` mirrors `--probe`'s posture: no
  response dir, mutually exclusive with the whole response-directory
  surface (both directions tested). Inputs: `--pack-arg TOKEN`
  repeatable in order (dash-leading tokens use the `=`-glued
  spelling, `--pack-arg=--slug` — argparse's constraint, documented
  in help and docstring); `--brief FILE` / `--no-brief` with exactly
  one required (the `--no-readme` deliberate-acknowledgment
  precedent); `--checkpoint FILE` optional, absence = the explicit
  null slot with a loud "oracle-less" log rather than a
  `--no-checkpoint` acknowledgment — pack itself has no such flag
  (the checkpoint requirement is project-config-driven), so I
  mirrored that. Say the word if you want the symmetric
  acknowledgment instead. `--pre-answered PROMPT=SUBJECT`
  repeatable; `--out-dir`; `--force` extended to mean
  "overwrite differing bundle bytes".
- **Member names fixed** at `brief.md` / `checkpoint.sh` (the
  schema's stated conventions) — internal to the container, so no
  knob.
- **Stem hygiene** is slug hygiene (kebab), plus refusals for path
  separators and an already-suffixed stem. §6.7's recommended
  `<date>-<slug>` fits it exactly.
- **Members are LF-normalized at write**, so the archived bytes ARE
  the hashed bytes; transport mangling is then the only CRLF source,
  which is exactly what the consumer's normalization tolerates. The
  one-line rule application mirrors `normalize_bundle_member`
  (bin/bale_open.py); the round-trip tests pin the agreement.
- **Deterministic emission** (fixed tar metadata, zeroed gzip mtime):
  identical inputs → identical bytes. That makes the idempotent
  re-run real — an existing identical bundle is a logged no-op, only
  differing bytes need `--force` — matching `--checkpoint-file`'s
  idempotency posture.
- **Emitter self-validation: by construction, not by import.** The
  brief left this to me. The crafter is pinned standalone (no bale
  imports) and never validates its own output, so it does not call
  `validate_bundle_manifest` at runtime. Instead: the manifest is
  correct by construction (hashes computed, flat names fixed, slots
  uniform), the inputs are refused at the desk where the consumer's
  gate would refuse them later (delivery flags bare and `=`-glued, a
  leading `pack` verb, unknown/duplicate intents, the `TODO(brief)`
  sentinel, hollow member files), and the parity is test-pinned:
  `BundlePackParity` runs the emitted `bundle.json` through the real
  `validate_bundle_manifest`, and `CrafterEmissionRoundTrip` runs an
  emitted bundle through a real `bale open`. One emitter-side rule
  goes past the consumer gate: a stored `--no-readme` is refused
  (the gate would accept it) because member presence is the single
  source and `--no-brief` is this tool's one spelling of no-brief.
  Deferred entry in the manifest records the not-taken runtime
  check; a docstring true-up proposal is below.
- **Rider: the key is `[probe] clipboard_command`** — naming it
  loudly, per the brief: section `probe`, key `clipboard_command`,
  a one-line TOML basic string holding the shell command probe
  output is piped into. The future `bin/bale_config.py` carrier must
  land this exact spelling; the constant block in the crafter says
  so in place. Lookup is `./bale.toml` then `./context/bale.toml`
  (repo-root and request-root layouts; first file found settles it),
  read by a deliberately minimal single-key scan — the crafter has
  no TOML parser standalone on 3.10, and anything past the simple
  quoted-string shape is treated as unset with remedy text (the
  never-fails, never-silently-skips path). Emission-time
  conditioning follows the registry text ("emits ... only when the
  key is set"); the practical consequence — the epilogue reaches
  workers only when the project ships `bale.toml` in `context/` —
  is stated in the remedy text itself.
- **`tests/test_open_verb.py` got a structural, content-preserving
  refactor**: shared fixtures moved to `_OpenVerbBase` (no test
  methods) so `CrafterEmissionRoundTrip` inherits the sandbox
  helpers without unittest re-running the 16 consumer tests under a
  second class. Every pre-existing test is byte-identical in body.
- **Version 0.4.14**: a desk-facing tool feature; neither bump
  exemption applies, per the brief's own read.

## Places to look closely

- The `pack_arg_problem` refusal set vs `validate_bundle_manifest`:
  I match the gate (delivery flags, leading `pack`) and add
  `--no-readme` (emitter hygiene past the gate, flagged above). If
  you'd rather the emitter refuse only what the gate refuses, drop
  that one branch and its two tests.
- The BALE.md §6.7 true-up paragraph — wording was mine to
  determine; it now also names the drift guard's two homes.

## Proposals

- **True up `validate_bundle_manifest`'s docstring on the next
  `bin/bale_validate.py` touch.** What: its line "the crafter's
  emission (49b) self-checks against it" predates this design;
  reality is desk-side input hygiene + construction, with the
  agreement pinned by `BundlePackParity` and the open-verb round
  trip, not a runtime import. Why: the file is outside this
  session's forecast, and one sentence of drift admission wasn't
  worth widening the change set; the sentence is now the only place
  describing a self-check that doesn't exist. Scope hints:
  `bin/bale_validate.py`, docstring only.
- **Add `bin/bale_open.py` and `bin/bale_sandbox.py` presence rows
  to `validate.sh`.** What: the filesystem-layout section predates
  both modules, so a missing one passes silently — the same stale
  inventory the v0.4.12 schema-loop true-up fixed. Why: noticed
  while landing the drift guard in the same file; left out as
  off-goal scope this session. Scope hints: `validate.sh`, two rows.
- **The rider's config-side carrier.** What: the `[probe]`
  `clipboard_command` accessor plus the `bale config init` wizard
  walk, on the next `bin/bale_config.py` touch, spelling exactly as
  above. Why: the registry entry's remaining half; the crafter-side
  landing is complete without it, but discoverability lives in the
  wizard. Scope hints: `bin/bale_config.py` (walk_configurables +
  render_bale_toml + a typed accessor, per its §2.5 contract).
