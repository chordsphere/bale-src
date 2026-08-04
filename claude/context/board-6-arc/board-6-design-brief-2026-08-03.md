# Board 6 — blind validation checkpoints, design brief (rev A, 2026-08-03)

Serves: the 2026-08-03 sitting, master `2026-08-03-continue-plan-007`
(read-only). Session shape: read-only design session, the board-5
`ledger-design-004` precedent — you produce a ratification-candidate
design brief; on ratification it ships verbatim via the readme-file
flag into the implementation session(s) you propose, and you run the
split end to end in the delegated-orchestration shape, closing with a
partitioned upward report (landed / ratified at your level / escalated
/ on-watch — the board-5 report in `context/claude/context/
board-5-arc/` is the prototype).

Sitting-open check: `bale --version` is expected `0.3.27`; the master
verified this against the live install on 2026-08-03. Treat any
divergence in your own request's provenance stamp as a flag, not a
fact to force.

## The doctrine being mechanized

MASTER.md §1's ratified floor: "validation checkpoints are authored
blind — by the planner from the request, never by the worker building
against them." Board 6's row carries the motivating evidence (two
2026-07-21 master-review catches invisible to in-lane worker checks by
construction) and the binding §5 contract (ratified 2026-07-13):
blind checkpoints coexist with worker validation — the planner's
checkpoint is the misunderstanding control, the worker's
validation.sh is the calibration stream, neither replaces the other,
and the ledger consumes both. None of that is re-litigated here; the
design's job is the mechanics.

Sequencing context, not pressure: the 1.0.0 gate (BALE.md §13, §5's
ladder contract) waits on boards 6 and 10. Board 6 is on the critical
path; it should still be designed right, not fast.

## Source material, in reading order

1. `claude/context/board-5-arc/upward-report-2026-08-03.md` — the arc
   report, verbatim, master's correction note included.
2. `claude/context/board-5-arc/implementation-brief-2026-08-01-revB.md`
   — D6 is the exact consumer-surface language the ledger connection
   below must honor; rev A is present for lineage.
3. MASTER.md board row 6, the §5 blocks ratified 2026-07-13,
   2026-07-15 (per-invocation overrides), and 2026-08-03 (claim-basis
   precedent), and the §3 watch on the claim-basis field.
4. The code surfaces in `context/bin/` named per question below.

## Design questions to dispose (D-numbered, board-5 style)

**D1 — the checkpoint's home.** Board 6's row offers two shapes: a
planner-pinned `validation.base.sh` per project, or a `[validation]
required = [...]` table in bale.toml keyed by touched file types.
Named hazard for the config shape, verified against the shipped tree:
bale.toml's own header states `bale config init` rewrites the file
from its walked surface and drops unrecognized hand-edited keys, so a
`[validation]` table is unsafe until the wizard learns it — a
two-part landing (bale_config.py + the gate) versus the script
shape's one. Weigh also: global-vs-repo config layering, and what a
casual project with no pinned checkpoint gets (absent = no blind
checkpoint, or absent = refuse?). Decide, with the trade recorded.

**D2 — additive execution.** The worker's validation.sh is kept and
unchanged — it is where claims come from and feeds the calibration
stream. Decide: run order (blind base first or worker first, and
why); whether a base-checkpoint failure and a worker-script failure
produce the same HOLD or distinguishable ones; output attribution in
the session log and at the walkthrough; exit-code semantics against
TARBALL.md §7.5. The execution site is `run_validation_sh` and its
callers in bale_apply.py.

**D3 — the apply pre-flight superset rule.** `validation_will_run ⊇
required-set-for-the-touched-paths`, checked where `changes[]` is
known. The `claims ⊆ validation_will_run` check in bale_validate.py
(BALE.md §11 row 15) is the same family and the natural neighbor.
Decide: how the required set resolves (file-type keys, path-prefix
keys, or whole-project); the refusal's wording and remedy text
(every refusal names its successor); the override flag, bound by the
ratified per-invocation-per-path, flag-only, never-config contract;
and the refusal/override telemetry rows (mechanical stream), mirroring
the drift-gate rows.

**D4 — the ledger connection.** Blind-checkpoint outcomes enter
telemetry distinct from worker claim/verdict rows — the §5 contract
says the ledger consumes both, which means `stats --json` eventually
distinguishes them under the additive key contract owned by
`format_stats_json`'s docstring (one-home rule; rev B's D6 carries
the surface). Decide the record fields and the stats keys, or
explicitly scope them to a follow-on. In the same breath, dispose the
§3 watch: the additive claim-basis self-report field (predicted vs
observed grounds, per the 2026-08-03 precedent) is named as "the
board-6/10-era decision" — decide it here, or hand it to board 10
with a recorded reason. Leaving the watch dangling is the one
non-answer.

**D5 — blindness enforcement.** The base script lives in the repo, so
a worker whose scope covered it could edit the checkpoint it is being
checked against. The drift gate already refuses out-of-scope edits;
what is missing is the rule that keeps the checkpoint *out of scope* —
today that would be packer discipline. Decide whether it stays
discipline (a documented never-include rule), becomes contract (pack
refuses a scope covering the pinned checkpoint path), or gets a
provenance treatment (checkpoint hash stamped into the request
manifest at pack, verified at apply). The self-oracle doctrine
(evidence 16's class, ADR-0013) is the lens.

## Constraints

- Read-only session: nothing lands under this sid. The deliverables
  are the ratification-candidate brief (downloadable, shipped forward
  via the readme-file flag on the implementation packs) and the
  proposed split.
- Corpus or tree claims are computed against the request's shipped
  tree, never recalled — the board-5 brief precedent. Facts the
  included set cannot verify are written as claims with sid citations.
- The verbatim-proposal contract applies to everything you carry
  forward: quote, never paraphrase, where a disposition turns on
  wording.
- If your brief needs to instruct about unfilled-placeholder
  conventions, cite TARBALL.md §3.4's convention line by reference —
  never write the marker literal into an instructional line; the
  pack-time refusal fires on any line containing it, by design
  (evidence: the board-5 rev-A pack failure).
- Escalate, do not decide: anything touching the ratified floor's
  wording, the 1.0.0 gate's definition, or a new global-doc contract.
