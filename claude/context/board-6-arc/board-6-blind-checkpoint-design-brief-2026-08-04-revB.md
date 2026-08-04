# Board 6 — blind validation checkpoints design brief (rev B, 2026-08-04)

Rev lineage: rev B incorporates the master's ratification
dispositions of 2026-08-04 — the design is **ratified**; the deltas
from rev A are the D1 layering narrowing (project-only at v1,
disposition 1), the exec-bit materialization rule folded into D2 and
its D8 assertion (disposition 5), and D6's landing dispositions
recorded as ratified (dispositions 2–3). The D3 coordination rider
and the A→D serialization were endorsed as written (dispositions
4, 6). Everything else is verbatim rev A.

Authored in the read-only design session
`2026-08-04-board-6-blind-checkpoint-design-003` against the
request's shipped tree, serving the 2026-08-04 sitting (master
`2026-08-04-continue-plan-002`). Every tree claim below was computed
against the shipped `context/` this session, not recalled; cited by
file and line where a disposition turns on it. Ratified 2026-08-04;
this rev ships verbatim via the readme-file flag into the
implementation sessions proposed in D7.

Ratified constraints honored throughout and not re-argued here: the
§1 floor ("validation checkpoints are authored blind — by the
planner from the request, never by the worker building against
them"); the §5 coexistence contract, quoted verbatim because every
disposition below leans on its exact wording:

> **Blind checkpoints coexist with worker validation.** The planner's
> blind checkpoint is the misunderstanding control; the worker's
> validation.sh is the calibration stream. Neither replaces the
> other; the ledger consumes both. (Binds board 6.)

and the §5 override contract (ratified 2026-07-15), likewise load-
bearing verbatim: "Scope-drift override is per-invocation and
per-path, flag-only. A standing config opt-out is the rejected shape
(self-oracle-adjacent silent bypass). Refusals and overrides are
mechanical-stream telemetry."

The worker's validation.sh is kept and unchanged everywhere in this
design. Nothing here alters TARBALL.md §7's authoring contract; the
one worker-visible doc delta is drafted in D6 and **escalated, not
decided** (it is a global-doc contract change).

## D0. Decisions at a glance

| # | Question | Decision |
|---|----------|----------|
| D1 | Checkpoint's home | Script shape: a planner-authored, committed, repo-relative script, config-referenced by a single wizard-walked path key `[validation] base` (the `[hooks]` precedent), **project-only at v1** (ratified disposition 1; the layered form is the recorded deferred widening). Absent = no blind checkpoint (never refuse); configured-but-dangling = loud refusal. The open `[validation] required = [...]` table shape is rejected at v1 (trade recorded in D1) |
| D2 | Additive execution | Both scripts always run, separately invoked and separately captured; checkpoint first. Executed checkpoint bytes come from the **base tree** (`git show <base_sha>:<path>`), never the overlaid staging copy. PASS requires both exit 0; HOLD is attributed per source in log, walkthrough, json, and telemetry. Each script keeps TARBALL.md §7.5's 0/1/2 individually; a checkpoint exit 2 is surfaced as "the planner's checkpoint itself errored" |
| D3 | Superset pre-flight | v1 required set is a whole-project flat list, config key `[validation] required` (wizard-walked list, the `untracked_inputs` walk precedent); path/file-type keying deferred with a named re-trigger. New apply pre-flight step 15: `validation_will_run ⊇ required` when `changes[]` is non-empty; refusal mirrors the drift gate — distinct outcome `required-check-refused`, per-invocation repeatable `--allow-missing-required-check <name>` on apply and retry, refusal/override telemetry rows, dry-run predicts, session stays open |
| D4 | Ledger connection | Additive always-stamp `attempts[].checkpoint` on every validated attempt post-epoch (`configured: false` is the known-zero form — the reconciliation-parsed disambiguation doctrine applied again); blind outcomes never merge into `claim_verdict` (no claims exist for them by construction). Stats keys specced semantically, key list stays owned by `format_stats_json`'s docstring, read side is split session D. The §3 claim-basis watch is **handed to board 10 with recorded reasons** (D4.3) — not left dangling |
| D5 | Blindness enforcement | Discipline rejected; two mechanical layers land: (contract) pack refuses a resolved include set covering the configured checkpoint path, per-invocation override `--allow-checkpoint-in-scope`, use stamped; (provenance) pack stamps `{path, sha256}` of the checkpoint at the target tip into the request manifest (the `contract_docs` precedent), apply verifies the base-tree bytes against the stamp and refuses on divergence with a per-invocation `--accept-checkpoint-change` that executes the current base-tree version. D2's base-tree execution rule is the third, load-bearing layer: in-flight tampering is inert by construction |
| D6 | Escalations | The TARBALL.md §7 worker-facing sentence (drafted, ratification required); nothing touches the §1 floor's wording or the 1.0.0 gate's definition |
| D7 | Split | Four serialized sessions: A = home + execution + attribution + telemetry write; B = superset gate; C = blindness enforcement; D = stats read side. Serialization claims per session, contestable separately |

## D1. The checkpoint's home: a wizard-walked path key to a committed script

**The config-table hazard, verified against the shipped tree.**
bale.toml's own header states the hazard the board row named:
"Re-running the wizard rewrites this file from its walked surface,
so any unrecognized keys you hand-edited in will be dropped"
(`context/bale.toml`, header). And BALE.md hardens it past prudence
into contract: "a configurable that isn't walked by `bale config
init` is a contract violation" (BALE.md ~line 397). So *any* config
shape requires the two-part landing — the `bale_config.py` trio
(typed accessor + `walk_configurables()` block + `render_bale_toml()`
branch, the documented recipe at `bale_config.py` ~175–180, exercised
by the `[identity]` landing) plus the gate/execution. The table shape
does not merely add a second part; it adds a *shape the wizard cannot
reasonably walk* (a dynamic string→list table keyed by file types has
arbitrary keys; every existing walk is a fixed-name value or flat
list). The script shape's config surface, by contrast, is a single
path string — exactly the `[hooks] post_apply_pass =
"scripts/reinstall.sh"` precedent already in the shipped bale.toml.

**Chosen: script shape, config-referenced.**

- `[validation] base = "<repo-relative path>"` — a new wizard-walked
  section with one path key, **project-layer only at v1** (ratified,
  disposition 1). The master's rationale, carried verbatim per the
  verbatim-proposal contract: "the script must be committed per-repo
  regardless (your own dangling rule), so a global `[validation]
  base` never saves more than one config line — while adding a
  dual-resolution rule under which the same global key silently
  names a different oracle in every repo it touches, including repos
  where a file happens to sit at the conventional path without the
  planner ever having ratified it as this repo's checkpoint.
  Oracle-by-coincidence is a worse failure than one line of per-repo
  config." The wizard walks the key at the project layer only; the
  global `bale config init --global` walk does not gain it.
  **Deferred widening, recorded:** the layered form (project
  overrides global per-key, explicit `""` suppress — the
  hooks/packer "empty = unset" contract, `bale_config.py`
  ~204–212) is the additive widening if a future operator baseline
  earns it; project-only breaks nothing on that day, and the
  re-trigger context is exactly the trade above — the widening must
  answer oracle-by-coincidence before it lands.
- **Absent = no blind checkpoint.** A casual project with no pinned
  checkpoint gets today's behavior: worker validation only. Refusing
  on absence would convert board 6 into a breaking change for every
  existing project and contradicts the additive posture the whole
  arc has held (`record_version` stays 1; keys are added, never
  required retroactively). The ledger still distinguishes "no
  checkpoint" from "no data" — that is D4's always-stamp, not a
  refusal's job.
- **Configured-but-dangling = loud refusal at apply pre-flight.**
  Config naming a checkpoint that does not exist at the base tree is
  a broken oracle reference, and a silent skip there is a bug by hard
  rule. Refusal remedy text: commit the checkpoint at the named path,
  or clear the key via `bale config init`. Committed-is-ratified is
  deliberate: a working-tree-only checkpoint the planner has not
  committed is not yet the project's oracle.
- The conventional path the wizard suggests: `scripts/validation.base.sh`
  (beside the hook scripts). The key stores whatever the planner
  picks; no path is hardcoded.

**The script's own contract.** Planner-authored, executable, follows
TARBALL.md §7.2's output conventions (`[PASS]`/`[FAIL]`/`[SKIP]
<reason>` per check, silent skip is a bug) and §7.5's exit codes. It
does **not** produce a §7.3 claims-vs-verdict block: claims are the
worker's predictions, and the checkpoint has no claims by
construction — nothing to reconcile. It prints its write locations
up top like the worker script (§7.1). Runtime shares the §7.6
budget posture: the two scripts together should target the same
wall-time envelope; a slow checkpoint gates slow checks behind the
same convention.

**Rejected: the `[validation] required = [...]` table as the
checkpoint's home.** Beyond the wizard-shape problem above, the
deeper disqualifier is that a table of required *names* cannot
execute anything — the board row's "run unconditionally in staging"
needs runnable planner-authored content, and a name table either
degenerates into a command map (a script in TOML form, with
quoting hazards and no output convention) or leans on the worker's
script to define the named checks, which reintroduces the self-oracle
the board exists to remove. The name-table *idea* survives in
reduced form as D3's required set — a declaration constraint on the
worker's set, a different mechanism with a different job.

## D2. Additive execution

**Both scripts always run.** A checkpoint failure does not skip the
worker's script and a worker failure does not skip the checkpoint.
The §5 contract's "the ledger consumes both" decides this: a
checkpoint FAIL beside a worker PASS is precisely the
misunderstanding-with-calibrated-worker signal the board exists to
surface, and a worker run suppressed on checkpoint failure would
starve the calibration stream on exactly the interesting attempts.
Cost is bounded by the shared §7.6 budget.

**Order: checkpoint first.** Three reasons. The planner's floor
frames what follows in the log — an operator reading top-down sees
the misunderstanding control's verdict before the worker's
self-assessment. Separately-captured invocations keep the §7.3
reconciliation parse untouched: the parser reads the *worker
script's* captured output, and the checkpoint's output never
interleaves with it (each invocation is captured on its own, exactly
as `run_validation_sh` captures today — call shape at
`bale_apply.py:1218`). And a checkpoint that errors (exit 2) is
surfaced before the worker's longer run spends its budget.

**Execution source: the base tree, not the staging overlay.** This
is the load-bearing mechanic of the whole design. Staging is the
current project state *plus the response overlay* (§7.1/§8.3), so
the staged copy of an in-repo checkpoint is the worker's
post-overlay version whenever the response touched it. The executed
checkpoint therefore comes from `git show <base_sha>:<path>` — the
committed version at the target tip the session commit is built
against (`git_head_at_apply`, §8.5/§8.6) — materialized to a
temporary location and executed with `cwd=staging` like the worker
script. **Materialization rule** (ratified nit, disposition 5):
`git show <sha>:<path>` emits blob bytes only — the exec bit lives
in tree metadata and does not survive materialization — so the
runner restores the mode explicitly (from the tree entry's mode, or
`chmod +x` on the temp copy) or invokes via the interpreter; either
is inside this decision, silent non-execution is not. Consequences
of the base-tree rule, each deliberate:

- A response that modifies the checkpoint is *checked against the
  old one* — in-flight self-grading is structurally impossible, not
  policy-refused (D5 leans on this).
- An uncommitted working-tree edit to the checkpoint is not
  honored: committed-is-ratified, matching D1's dangling rule.
- The rule is staging-strategy-independent (default working-tree
  copy or target-base both stage from states that could already
  contain drift; base-tree extraction bypasses both).

**Failure semantics.** The attempt's `state` stays `PASS`/`HOLD` —
the envelope vocabulary is unchanged, the additive posture holds.
`PASS` requires both exit codes 0. Any other combination is `HOLD`,
with **attribution everywhere the outcome renders**:

- Session log: banded sections, e.g. a `=== blind checkpoint
  (<path>, <sha256 prefix>) ===` header before the checkpoint's
  streamed output and a `=== worker validation.sh ===` header before
  the worker's — the existing §8.5 streaming into
  `.bale/logs/<sid>.log`, twice.
- Walkthrough summary: both states named, e.g. `checkpoint: PASS ·
  worker validation: HOLD (exit 1)`; the checkpoint-errored case
  (exit 2) gets its own §8.5-style distinct phrasing — "the
  planner's checkpoint itself errored; inspect the checkpoint
  script" — because the remedy differs (the planner's artifact
  broke, not the worker's).
- `--json`: additive keys on the apply report beside the existing
  validation keys; the key list's home stays the apply renderer's
  docstring (one-home rule; this brief specs semantics — per-source
  state and exit code — not the wire names).
- Telemetry: D4's `checkpoint` stamp.

**Exit-code semantics against §7.5.** Unchanged per script: 0 pass,
1 check failed, 2 script errored, claim/verdict disagreement never
flips an exit code (the checkpoint has no claims, so the last rule
is vacuous for it). The combined PASS/HOLD derivation above is
bale's, outside either script.

**Execution site.** The runner is a sibling of `run_validation_sh`
in `bale_staging.py` (the module `bale_apply.py` imports it from —
import block at `bale_apply.py:746–753`), threaded through the same
caller at `bale_apply.py:1218` with both results carried to §8.6's
state derivation and the terminal actions' telemetry calls.
**Included-set note:** `bale_staging.py` is not in this request's
shipped tree; every internals claim above about it is call-site
level (signature and capture behavior as observed from
`bale_apply.py`). Session A includes it, and its worker verifies the
runner-extraction seam against the real module before building.

## D3. The apply pre-flight superset rule

**What the rule protects.** The worker's `validation_will_run` is
the declaration claims hang off (`claims ⊆ validation_will_run`,
BALE.md §11 row 15, enforced at `bale_validate.py:377–383` and §8.1
step 11). An under-declared set starves the calibration stream on
the checks that matter and is invisible to every current gate. The
superset rule converts a floor of that declaration to contract —
"partially converts," per the board row, because name membership
cannot verify a check's content; that residue stays review policy.

**Required-set resolution: whole-project flat list at v1.**
`[validation] required = ["<check-name>", ...]` — a flat string
list, wizard-walkable with the existing list-walk machinery (the
`untracked_inputs` precedent, `bale_config.py` `_prompt_path_list`
family), landed under the same trio recipe as D1's key. File-type
and path-prefix keying are **deferred**: the keyed-table shape is
the same wizard-unwalkable structure D1 rejected, and the honest
membership rule below makes the whole-project form livable.
Recorded trade: a doc-only session under `required = ["tests"]`
must *declare* tests — but declaring is one manifest line, and the
check may still `[SKIP]` with a reason at runtime (§7.2), grading
`n/a` (§7.3), which is honest and visible rather than forced work.
The named re-trigger for the keyed form: the first project where
whole-project required names produce systematic per-class `[SKIP]`
noise in the ledger (the stats D-session's rows will show it).

**The check.** New §8.1 step 15 (appended; steps 1–14 stay stable
per the numbered-anchor contract), sited in `bale_apply.py` beside
its step-14 neighbor — it needs the merged config
(`bale_config.merged_config(repo)`, already loaded repo-side in
both callers) and the manifest, both in hand there. Semantics:

- Fires only when `[validation] required` resolves non-empty AND
  `manifest.changes[]` is non-empty. Bailout and clarification
  manifests pass vacuously (empty `changes[]`), read-only sessions
  never reach it (the step-14 gate refuses their changes first),
  unconfigured projects are entirely outside its blast radius.
- Rule: every required name ∈ `validation_will_run`. Exact string
  match; the refusal renders both sets so a near-miss is visible.
- Manifest-and-config-only, so it runs under `--dry-run` (same
  report, no telemetry — no outcome occurred), mirroring step 14.

**Refusal — every refusal names its successor.** Mirrors the drift
gate's structure exactly (`bale_apply.py:918–965`): a distinct,
dispatchable outcome, not the generic `fail()` path. Wording shape:

> `[REJECT] required checks missing (BALE.md §11 row <NN>):`
> `validation_will_run` omits required check(s): <names>. Required
> set (`[validation] required`, <layer> layer): <set>. Declared:
> <validation_will_run>. Remedies: regenerate the response with the
> required checks declared — a declared check may still `[SKIP]`
> with a reason at runtime; or admit this response past specific
> names with `--allow-missing-required-check <name>` (per-invocation,
> repeatable); or change the project's required set via `bale config
> init` (planner action).

- Human rendering via a new `bale_report` formatter (wiring only in
  `bale_apply`, the one-home rule); `--json` emits outcome
  `required-check-refused` with a detail object (missing names,
  required set, declared set, overridden names) on the exit-1 path,
  like the drift refusal, so an orchestrator dispatches on the key.
- Session stays open; refusal is pre-staging, no git side effects.

**The override**, bound by the ratified contract quoted in the
header: `--allow-missing-required-check <name>` — per-invocation,
repeatable, per-*name* (the rule's unit is check names, the
per-path clause's analogue), flag-only, deliberately no config key.
Accepted by apply **and retry**, re-stated each invocation, never
carried (the 2026-07-21 lifecycle-wide override contract, and the
existing retry behavior at `bale_apply.py:711–715`). A named-but-
not-missing name logs a no-effect line (the `unused_allow` mirror,
`bale_apply.py:908–918`); every effective use logs a FORCE: line
and stamps telemetry.

**Telemetry rows, mirroring the drift-gate rows.** Refusal writes
an attempt with outcome `required-check-refused` (command apply/
retry, `validation: null` — no validation ran), except under
`--dry-run`. Effective overrides stamp an additive
`attempts[].required_check_overrides: [<name>, ...]` on the attempt
that proceeds (the `overridden_paths` mirror). Two coordination
riders that must land **with the gate, not after it** (session B):
the schema's closed `outcome` enum (verified:
`telemetry-record.schema.json`, both envelope and attempt) gains the
value — additive vocabulary, `record_version` stays 1, the
`scope-drift-refused` precedent at v0.3.10 — and `bale_stats`'s
in-flight membership set (held / scope-drift-refused / rejected,
per the D2 unit model and `bale_stats.py` docstring) gains it, so a
session whose latest outcome is the new refusal is counted in-flight
rather than misclassed. The fuller stats rates wait for session D;
this membership line cannot.

## D4. The ledger connection

**D4.1 The record fields.** Blind-checkpoint outcomes enter
telemetry as a new additive field, distinct from the worker's
claim/verdict rows — never merged into `claim_verdict` (the blind
checkpoint has no claims; a merged row would fabricate a prediction
that was never made). The board-5 brief's D10 anticipated exactly
this surface, quoted for lineage: "when blind-checkpoint outcomes
join validation, they arrive as additional mechanical facts on the
attempt (new additive fields or new check rows); D2's check-level
denominators absorb new checks without redefinition."

`attempts[].checkpoint` (object, additive; attempt schema already
admits additive keys — `additionalProperties: true`, verified):

- **Always-stamped on every validated attempt post-epoch.** Key
  presence = epoch membership; `{"configured": false}` = known-no-
  checkpoint. This is the reconciliation-parsed / clarification
  disambiguation doctrine applied a third time: the ledger must
  never conflate "no checkpoint configured" with "pre-epoch no
  data."
- When configured and executed: `configured: true`, `state`
  (`"PASS"`/`"HOLD"`), `exit_code`, `script: {path, sha256}` — the
  executed base-tree bytes' hash, which is also what makes D5's
  provenance verification auditable after the fact — and
  `stamp_matched` (`bool|null`; null when the request carried no
  stamp, the hand-rolled-request case).
- Per-check line parsing (a `checks{}` map like `claim_verdict`'s
  shape minus claims) is **deferred**: v1's rates need
  state/exit only, and a parse convention added later is additive.
  Re-trigger: the first grant evaluation that wants blind-check
  granularity below whole-script.
- The v0.3.x schema description work is session A's, alongside the
  D3 fields in session B.

**D4.2 The stats keys** — semantics here, key list owned where it
already lives. Quoting the owner's contract verbatim (the surface
this design must honor, `bale_report.py:2029–2031`): "existing keys
are never renamed or removed; new keys may be added — the additive
contract board 10's grant harness pins its reads against." Under
that contract, session D adds, per class row: checkpointed-attempt
count (validated attempts with `checkpoint.configured` true),
checkpoint-HOLD count and rate over that denominator (null on
zero, the module's standing rule), required-check refusal count and
override count beside the drift rows; and corpus-level: a
`checkpoint` coverage sub-epoch row (first record carrying the key,
the key-presence detection the existing coverage rows use). The
wire names are `format_stats_json`'s docstring's to fix at
implementation — this brief deliberately does not freeze them
(the board-5 D6 one-home precedent).

**D4.3 The §3 watch, disposed: handed to board 10, with reasons.**
The watch, verbatim: "The ledger cannot yet distinguish
predicted-grounds claims from observed ones (the §5 claim-basis
precedent's measurement gap). Re-trigger: the board-6/10-era
decision on an additive claim-basis self-report field." Decision:
board 10 owns it, for three recorded reasons. First, its consumer
is the grant harness — the field exists to let per-class agreement
rates be read *conditional on claim basis*, which is a grant-
evaluation question; board 6's checkpoint stream is mechanically
graded regardless and consumes claim basis nowhere. Second, its
authoring surface is the worker-facing claims contract — TARBALL.md
§5.3 and the response-manifest schema — and a new global-doc
contract is exactly what this session's constraints escalate rather
than decide; board 10 sits at the level where that ratification
happens anyway. Third, it is a *self-reported* field, and the §5
dual-stream contract places self-reported design beside the
calibration-target machinery board 10 evaluates, not beside the
mechanical substrate board 6 builds. The watch's re-trigger line
should be updated at the next MASTER.md landing to name board 10 as
the owner (a master edit, escalated with this brief).

## D5. Blindness enforcement

The lens, per the request: the self-oracle doctrine (evidence 16's
class, ADR-0013 — cited by reference; the ADR is not in the shipped
set). The checkpoint is the oracle; any path by which the worker
under evaluation authors or selects its own oracle is the shape to
close. Disposition of the three offered treatments: **discipline is
rejected** — a documented never-include rule is precisely the
doctrine-without-mechanics state board 6 exists to end, and the
board's own motivating evidence is two catches that in-lane checks
missed *by construction*, not by sloppiness. Both remaining
treatments land, because they close different holes, on top of the
structural layer D2 already bought:

**Layer 0 (from D2, restated as the foundation): base-tree
execution.** The executed checkpoint is the committed version at
the target tip. A response that edits the checkpoint is graded
against the pre-edit oracle; in-flight tampering is inert by
construction, not by refusal. Config retargeting is likewise inert
in-flight: apply reads the merged config from the *repo* working
tree (`bale_config.merged_config(repo)`, `bale_apply.py:1119`),
never from the staged overlay, so a response editing bale.toml
cannot redirect or disable this apply's checkpoint. What remains is
the *cross-session* hole — a worker edit to the checkpoint or to
bale.toml that merges under review and becomes the next session's
oracle — which the two treatments below narrow.

**Layer 1 (contract): pack refuses a scope covering the checkpoint
path.** At pack's include-resolution stage (beside the existing
existence refusal, `bale_pack.py:2067`, and before the disjointness
gate), when the merged config names a checkpoint: refuse any
resolved include set that covers its path — the rule that keeps the
checkpoint out of scope, so the step-14 drift gate's existing
refusal does the rest at apply time. The refusal names its
successors: narrow the includes; or, planner authority, re-run with
`--allow-checkpoint-in-scope` (per-invocation, flag-only, no config
key — the ratified override shape), which admits the scope, logs a
FORCE: line, and stamps the admission into the request manifest's
provenance so the session's telemetry carries it. The sanctioned
ordinary update path needs no session at all: the checkpoint is
planner-authored by the §1 floor's own wording, so the planner
edits and commits it directly, exactly as they edit bale.toml —
this is doctrine, not workflow friction. The override exists for
the deliberate exception (a checkpoint-maintenance session the
planner chooses to delegate), and its use is loud and recorded, the
same species as `--allow-out-of-scope`. bale.toml itself is *not*
added to the refusal at v1: it is legitimately session-editable
(hooks, staging), in-flight retargeting is already inert per layer
0, and a merged bale.toml edit is a one-line, review-visible diff;
recorded as the accepted residue, re-trigger: the first observed
worker edit to `[validation]` keys in a merged session.

**Layer 2 (provenance): stamp at pack, verify at apply.** The
`contract_docs` precedent extended (`bale_pack.py:608–661` hashes
the injected globals into `provenance.contract_docs`; the request
schema pins them): pack stamps `provenance.checkpoint = {path,
sha256}` — the configured path and the sha256 of its bytes at the
pack-time target tip — or explicit `null` when no checkpoint is
configured, so absence-of-stamp remains the hand-rolled-request
signal. Pack refuses if config names a checkpoint absent at the
tip (D1's dangling rule, caught earlier). At apply, before
execution: hash the base-tree bytes about to run and compare to the
stamp. Divergence means the oracle changed between pack and apply —
a legitimate planner edit or interference, and either is worth
stopping for. Refusal, with successors: re-pack against the current
tip, or `--accept-checkpoint-change` (per-invocation), which
executes the **current** base-tree version — the planner's latest
committed oracle, never the stale stamped bytes — logs FORCE:, and
records `stamp_matched: false` in the D4 stamp. Schema impact:
`request-manifest.schema.json` is strict (`additionalProperties:
false` at root and inside `provenance`, verified), so the additive
key is a schema edit; `provenance` remains optional as a block, and
apply's verification runs only when the stamp is present, keeping
hand-rolled and pre-board-6 requests valid.

## D6. Escalations (decide nothing here)

1. **The TARBALL.md §7 worker-facing sentence** — a global-doc
   contract change, escalated with proposed wording for
   ratification and landing via the master's doc-landing path.
   Proposed insertion at the end of §7's preamble (after the
   "…`validation.sh` does not duplicate it" paragraph):

   > Some projects additionally pin a planner-authored **blind
   > checkpoint** that bale runs in staging beside `validation.sh`
   > (checkpoint first; both always run). It is authored blind —
   > by the planner from the request, never by the worker building
   > against it — and the worker neither writes, edits, nor
   > declares it: `validation_will_run` and `claims` describe the
   > worker's own script only. A project may also pin required
   > check names the worker's `validation_will_run` must include;
   > apply refuses an omission, and a declared check may still
   > `[SKIP]` with a reason at runtime.

   Rationale for escalating rather than deciding: the constraint
   set names new global-doc contracts as escalate-only, and this
   sentence changes what every worker on every project is promised
   about validation.
   **Ratified 2026-08-04 (disposition 2): wording as drafted;
   landing rides this sitting's master-deltas vehicle sequenced
   after session A applies, so the promise never precedes the
   behavior. It does not fold into A's scope — A's work class stays
   clean for the ledger. No implementation session touches
   TARBALL.md.**
2. **The §3 watch re-owner note** (D4.3): MASTER.md's watch line
   gains board 10 as the named owner — a master edit at the next
   deltas landing. **Ratified 2026-08-04 (disposition 3): accepted,
   same deltas vehicle.**
3. Nothing in this design touches the §1 floor's wording or the
   1.0.0 gate's definition. The gate's dependence on board 6 is
   satisfied by sessions A–C landing (the contract conversion); D
   is inside the gate's spirit but the master may sequence it
   against board 10's needs.

## D7. Proposed implementation split

Four sessions, serialized A → B → C → D. Work class: code, all
four. Each includes this brief verbatim via the readme-file flag.
Sessions A–C's fixtures execute `bin/bale` end to end, so each
carries the execution-context manifest set (ratified 2026-07-21):
all of `bin/`, all of `schemas/`, the four global docs, and
`tools/response_lint.py`, copied verbatim. **A must also include
`bale_staging.py`** (in `bin/`, so the set covers it — named
because this design session could not read it; D2's included-set
note).

**Session A — the checkpoint itself: home, execution, attribution,
telemetry write.** Scope seam: the run side. Touches:
`bin/bale_config.py` (the `[validation] base` trio),
`bin/bale_staging.py` (the checkpoint runner: base-tree
materialization + capture, sibling of `run_validation_sh`),
`bin/bale_apply.py` (threading both results into §8.6 state, the
dangling-checkpoint refusal, telemetry stamp inputs),
`bin/bale_report.py` (walkthrough attribution lines, apply-json
additive keys, telemetry-attempt builder), `bin/bale` (wiring),
`schemas/telemetry-record.schema.json` (the D4 `checkpoint` field +
descriptions), `BALE.md` (§8.5 dual execution, §8.9 field, the
config-surface pointer), `bale.toml`-adjacent docs as the config
recipe requires, `tests/`.

**Session B — the superset gate.** Scope seam: pre-flight step 15.
Touches: `bin/bale_config.py` (the `[validation] required` trio —
landed here, beside its consumer), `bin/bale_apply.py` (the gate,
override flag on apply and retry, telemetry rows),
`bin/bale_report.py` (refusal renderer, json detail),
`bin/bale` (wiring, flags), `schemas/telemetry-record.schema.json`
(outcome enum value + `required_check_overrides`),
`bin/bale_stats.py` (the in-flight membership line **only** — the
coordination rider D3 names), `BALE.md` (§8.1 step 15, §11 row,
§5.4 flags), `tests/`.

**Session C — blindness enforcement.** Scope seam: the pack side
plus apply's stamp verification. Touches: `bin/bale_pack.py`
(scope-covering refusal, `--allow-checkpoint-in-scope`, provenance
stamp), `bin/bale_apply.py` (stamp verification,
`--accept-checkpoint-change`, `stamp_matched` threading),
`schemas/request-manifest.schema.json` (the additive `provenance.
checkpoint` key), `bin/bale_report.py` (refusal texts),
`bin/bale` (flags), `BALE.md` (§7.1/§7.2, §8.1), `tests/`.

**Session D — the stats read side.** Scope seam: the ledger's read
of the new facts. Touches: `bin/bale_stats.py` (checkpointed-
attempt classification, rates, refusal/override counts, coverage
row), `bin/bale_report.py` (`format_stats_json` keys + human rows —
the docstring exercises its ownership), `BALE.md` (§5.6), `tests/`
(fixture-corpus records exercising every new shape: configured-
false stamp, PASS, HOLD-by-checkpoint, HOLD-by-worker,
HOLD-by-both, checkpoint exit 2, `stamp_matched` false,
`required-check-refused` latest-outcome in-flight, overrides
present, pre-epoch key absence).

**Serialization claims, contestable separately.** B after A: B's
config trio lands in the module A just reshaped, and both touch
`bale_apply.py`'s pre-flight region and `BALE.md` — the pack-time
disjointness gate serializes them regardless. C after B: C's apply-
side verification sits in the same pre-flight, and its telemetry
`stamp_matched` threads through the attempt builder A/B shaped;
scopes intersect on `bale_apply.py`, `bale_report.py`, `BALE.md`,
`tests/`. D after A–C: its fixture corpus encodes their additive
fields and enum value — building it against a guessed shape
re-introduces exactly the confidently-wrong risk the workflow
exists to prevent (the board-5 D9 argument, verbatim in spirit).
Each session sizes comfortably alone; A is the largest and was
deliberately relieved of the gate (B) and the pack work (C) so it
is not the tight fit §11.2 treats as not fitting. If A's worker
still judges it tight at pre-flight, the pre-named seam is
config-trio-plus-runner versus attribution-plus-telemetry.

## D8. Tests (oracle doctrine per ADR-0002, cited by reference)

Observable-state assertions against the documented contract; no
golden comparisons. Per session: **A** — checkpoint runs from
base-tree bytes (fixture: response edits the checkpoint; assert the
pre-edit version's marker output ran — the assertion is on
*executed output*, not on the materialized file's presence or
content, so a mode-stripped, never-run checkpoint fails the test
per disposition 5); both-always-run (checkpoint
FAIL still runs worker; worker FAIL still ran checkpoint — assert
both banded sections in the log); PASS requires both; attribution
strings in walkthrough for each HOLD source and the exit-2 phrasing;
dangling-config refusal; absent-config = today's behavior
byte-compatible; telemetry stamp shapes (configured false / true;
script hash equals base-tree hash). **B** — refusal on a missing
required name (session stays open, exit 1, json outcome key, no
staging side effects); vacuous passes (empty changes, bailout,
clarification, unconfigured); `--dry-run` predicts with no
telemetry; override admits exactly the named names, unused-name
no-effect line, retry re-states; telemetry refusal attempt +
`required_check_overrides`; stats in-flight membership for the new
outcome. **C** — pack refusal on covering include set; override
admits + stamps; provenance stamp present/null correctly; apply
divergence refusal; `--accept-checkpoint-change` executes current
base-tree bytes and records `stamp_matched: false`; hand-rolled
request (no stamp) verifies nothing and stamps `stamp_matched:
null`. **D** — the fixture-corpus shapes enumerated in D7's session
D, each asserted into the correct numerator/denominator, rates null
on zero denominators, coverage row keyed on presence.

## D9. Interface notes for later boards (design nothing here)

- **Board 10 (grants):** the checkpoint stream arrives as per-class
  mechanical rows under the additive key contract; the grant
  harness can pin checkpoint-HOLD rate beside agreement rate. The
  claim-basis field is board 10's (D4.3), and its natural first
  consumer is the same harness.
- **Board 13 (read/write includes):** the pack-time covering
  refusal consumes the resolved include set as recorded today; a
  future read/write split would narrow the refusal to write
  includes — additive, like the drift definition note in the
  board-5 brief's D10.
