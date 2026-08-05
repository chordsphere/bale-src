#!/usr/bin/env python3
"""Hermetic E2E for `bale stats` — the board 5 read side (v0.3.24).

Drives `bin/bale stats` end to end over the checked-in fixture corpus at
``tests/fixtures/stats_corpus/`` — one record per shape the real corpus
and the schemas admit (brief D8): single-attempt applied; HOLD→retry
(whose retry also carries an ``[n/a]`` check — claim ``unknown``,
verdict ``skip`` — the named agreement residual);
drift-refused→applied with an override; rejected→applied (class
inheritance to the feedback-less attempt); unlock ``abandoned``; unlock
``closed-read-only`` with ``[]`` scope; the overload case — ``[]``
scope, *no* ``closure_reason`` key — asserted NOT read-only; the
pre-v0.3.16 shape (no ``closure_reason`` key anywhere);
``reconciliation_parsed`` false; corrupt JSON; ``record_version: 2``; a
bailout with embedded diagnostics; clarification stamps in both
cross-check directions (including a null ``records[].at``); a
pack-closed ``unlocked`` session carrying a ``rounds: 0`` stamp (inside
the epoch denominator, per the close-keyed rule); a missing work_class
(→ ``unclassed``); post-close ``rolled-back``; crash-debris; and a
recent record for the ``--since`` window. The board 6 session D
extension (v0.3.29) adds one record per new shape the checkpoint and
required-check surfaces admit: the known-zero ``configured: false``
stamp; checkpoint PASS with a verified stamp; HOLD attributed to the
checkpoint alone, to the worker alone, and to both; the checkpoint
itself erroring (exit 2 — still a checkpoint-attributed HOLD in the
stamp's own state); an admitted divergence (``stamp_matched: false``);
a ``required-check-refused`` latest outcome (in-flight, validation
null, therefore no checkpoint key — the always-stamp rule's other
half); and an effective ``required_check_overrides`` entry on an
applied attempt. Pre-epoch key absence is the original eighteen
records, which the ``checkpoint`` coverage row counts as lacking.

Oracle doctrine per ADR-0002: observable-state assertions against the
documented contract — the ``--json`` line is asserted key-by-key from
hand-derived expectations, never compared byte-for-byte to a golden
copy. The key contract itself is owned by ``format_stats_json``'s
docstring in ``bin/bale_report.py``.

The fixtures are copied into the scratch repo's ``claude/telemetry/``
UNCOMMITTED, which doubles as the D5 posture check: the reader is the
filesystem, so stats needs no commit to see a record.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_stats_aggregation.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from harness import (
    bale_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "stats_corpus"

# The two loader-diagnostic sentinels (named-on-stderr rule). Kept in one
# place so a message rewording breaks one line, not several assertions.
CORRUPT_NAME = "corrupt-record.json"
FILTERED_NAME = "2026-06-20-fx-vfuture-001.json"


class StatsAggregationTest(unittest.TestCase):
    """`bale stats` aggregates the fixture corpus per the D2 contract."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-stats-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    # -- helpers ---------------------------------------------------------

    def seed_corpus(self) -> None:
        """Copy the checked-in fixtures into claude/telemetry/, uncommitted
        (the D5 filesystem-reader posture)."""
        shutil.copytree(FIXTURES, self.repo / "claude" / "telemetry")

    def stats_json(self, *args: str) -> tuple[dict, str]:
        """Run `bale stats --json [args]`; assert exit 0 and exactly one
        stdout line (the stream discipline); return (payload, stderr)."""
        result = run_bale(self.install, ["stats", "--json", *args],
                          cwd=self.repo, env=self.env)
        self.assertEqual(result.returncode, 0,
                         msg=f"stats must exit 0 on a successful read\n"
                             f"stdout:\n{result.stdout}\n"
                             f"stderr:\n{result.stderr}")
        lines = [ln for ln in result.stdout.splitlines() if ln.strip()]
        self.assertEqual(len(lines), 1,
                         msg="json stream discipline: stdout carries "
                             "exactly one line; diagnostics go to stderr\n"
                             f"stdout:\n{result.stdout}")
        return json.loads(lines[0]), result.stderr

    # -- the full-corpus aggregation -------------------------------------

    def test_full_corpus_json(self) -> None:
        self.seed_corpus()
        stats, stderr = self.stats_json()

        self.assertEqual(stats["outcome"], "stats")

        # Corpus context: 29 files = 27 records + 1 parse failure + 1
        # filtered future version; one read-only and one crash-debris
        # session leave 25 classed members, six of them in-flight (the
        # original held session, the four checkpoint-HOLD shapes, and
        # the required-check-refused session).
        self.assertEqual(stats["corpus"], {
            "records": 27,
            "parse_failures": 1,
            "filtered_record_versions": 1,
            "read_only_sessions": 1,
            "crash_debris_sessions": 1,
            "sessions": 25,
            "in_flight_sessions": 6,
            "response_attempts": 26,
            "validated_attempts": 22,
            "checks": 27,
        })

        # Epoch: minimum created_at, and the pre-epoch statement is the
        # renderer's; here the row itself.
        self.assertEqual(stats["epoch"], {
            "first_sid": "2026-06-01-fx-pre-cr-001",
            "first_created_at": "2026-06-01T10:00:00+00:00",
        })

        # Coverage by key presence: the two earliest records lack the
        # closure_reason key (pre-v0.3.16 shapes); eleven records carry
        # a clarification stamp (seven original + the four session-D
        # applied closes), so sixteen of twenty-seven lack it.
        self.assertEqual(stats["coverage"]["closure_reason"], {
            "first_sid": "2026-06-05-fx-applied-001",
            "records_lacking": 2,
        })
        self.assertEqual(stats["coverage"]["clarification"], {
            "first_sid": "2026-06-12-fx-bailout-001",
            "records_lacking": 11 + 5,
        })
        # The board 6 sub-epoch (v0.3.29, session D): eight records
        # carry the checkpoint stamp somewhere — every session-D
        # fixture with a validated attempt. The required-check-refused
        # record does NOT carry it (validation never ran; the
        # always-stamp rule's other half), so it counts among the
        # nineteen lacking, beside the eighteen pre-epoch originals.
        self.assertEqual(stats["coverage"]["checkpoint"], {
            "first_sid": "2026-06-21-fx-ckpt-zero-001",
            "records_lacking": 19,
        })

        # The scopeless overload: [] scope with NO closure_reason key is
        # NOT read-only (detection keys on closure_reason, never scope) —
        # exactly one session (the swept unlock) is the read-only count,
        # and the scopeless-applied session's class row proves it landed
        # in the rates (its check is part of code's 13).
        self.assertEqual(stats["corpus"]["read_only_sessions"], 1)

        code = stats["classes"]["code"]
        self.assertEqual(code["sessions"], 18)
        self.assertEqual(code["closed_sessions"], 12)
        self.assertEqual(code["response_attempts"], 20)
        self.assertEqual(code["validated_attempts"], 17)
        # checks: superseded HOLD attempts included (attempt history is
        # the point) and the rolled-back session's applied attempt stays
        # in every mechanical denominator; each session-D fixture adds
        # one check.
        self.assertEqual(code["checks"], 22)
        self.assertEqual(code["checks_agree"], 18)
        self.assertEqual(code["checks_disagree"], 3)
        # The named residual: the hold-retry session's [n/a] check
        # (claim "unknown", verdict "skip") lands in checks_na — every
        # schema agreement value has its own count, no catch-all
        # bucket — and STAYS in agreement_rate's all-checks denominator
        # (D2: naming the residual does not redefine the rate).
        self.assertEqual(code["checks_na"], 1)
        self.assertAlmostEqual(code["agreement_rate"], 18 / 22)
        self.assertEqual(code["unparsed_validated_attempts"], 0)
        self.assertEqual(code["held_attempts"], 6)
        self.assertAlmostEqual(code["hold_rate"], 6 / 17)
        self.assertEqual(code["drift_refused_attempts"], 1)
        self.assertAlmostEqual(code["drift_refusal_rate"], 1 / 20)
        self.assertEqual(code["override_attempts"], 1,
                         msg="override incidence is a count beside the "
                             "drift refusals, not a rate")
        self.assertEqual(code["bailout_sessions"], 1)
        self.assertEqual(code["sessions_with_response_attempt"], 18)
        self.assertAlmostEqual(code["bailout_rate"], 1 / 18)
        # Clarification epoch: only closed sessions whose closing attempt
        # carries the stamp; rounds >= 1 clarifies. The four session-D
        # applied closes carry the known-zero stamp, widening the epoch
        # denominator without clarifying.
        self.assertEqual(code["clarified_sessions"], 1)
        self.assertEqual(code["clarification_epoch_sessions"], 8)
        self.assertAlmostEqual(code["clarification_rate"], 1 / 8)

        # -- board 6 session D: the checkpoint rows (D4.2) ------------
        # The denominator is validated attempts whose stamp reads
        # configured: true — six fixtures (PASS, three HOLD
        # attributions, exit 2, accepted divergence). The two
        # configured: false stamps (known-zero) and every pre-epoch
        # attempt (no key) stay outside it, for different reasons the
        # ledger never conflates.
        self.assertEqual(code["checkpointed_attempts"], 6)
        # The numerator keys on the stamp's OWN state — the per-source
        # attribution: checkpoint-alone HOLD, both-HOLD, and the exit-2
        # error all count; the worker-alone HOLD (checkpoint PASS) does
        # not, whatever the attempt's envelope state was.
        self.assertEqual(code["checkpoint_hold_attempts"], 3)
        self.assertAlmostEqual(code["checkpoint_hold_rate"], 3 / 6)
        # The step-15 gate's pair, counts beside the drift pair.
        self.assertEqual(code["required_check_refused_attempts"], 1)
        self.assertEqual(code["required_check_override_attempts"], 1)

        doc = stats["classes"]["doc"]
        self.assertEqual(doc["sessions"], 4)
        # The parse miss is a tooling fact — its own share, NEVER folded
        # into agreement: doc's agreement stays 4/4 while the unparsed
        # attempt shows in its own row.
        self.assertEqual(doc["checks"], 4)
        self.assertEqual(doc["checks_agree"], 4)
        self.assertEqual(doc["unparsed_validated_attempts"], 1)
        self.assertAlmostEqual(doc["unparsed_share"], 1 / 4)
        self.assertEqual(doc["checks_na"], 0,
                         msg="an honest zero: doc has no [n/a] checks")
        self.assertAlmostEqual(doc["agreement_rate"], 1.0)
        # Pre-epoch key absence (session D): every doc record predates
        # board 6, so the class has no checkpointed attempts at all —
        # counts are honest zeros and the rate is null on the zero
        # denominator, never a fabricated 0%.
        self.assertEqual(doc["checkpointed_attempts"], 0)
        self.assertEqual(doc["checkpoint_hold_attempts"], 0)
        self.assertIsNone(doc["checkpoint_hold_rate"])
        self.assertEqual(doc["required_check_refused_attempts"], 0)
        self.assertEqual(doc["required_check_override_attempts"], 0)

        # The per-enum-value counts partition checks: over a corpus
        # whose agreement values all come from the schema vocabulary
        # (agree / disagree / n/a — this fixture corpus does), the
        # three named counts sum to checks in every class row.
        for cls, row in stats["classes"].items():
            self.assertEqual(
                row["checks_agree"] + row["checks_disagree"]
                + row["checks_na"],
                row["checks"],
                msg=f"class {cls}: per-agreement-value counts must "
                    f"sum to checks — an unnamed residual is exactly "
                    f"what checks_na exists to eliminate")
        self.assertEqual(doc["clarified_sessions"], 1)
        self.assertEqual(doc["clarification_epoch_sessions"], 2)

        # Class inheritance: the rejected feedback-less first attempt
        # inherits the session's class from the later applied attempt.
        mixed = stats["classes"]["mixed"]
        self.assertEqual(mixed["sessions"], 1)
        self.assertEqual(mixed["response_attempts"], 2)
        self.assertEqual(mixed["rejected_attempts"], 1,
                         msg="rejection is a count at v1, and the "
                             "rejected attempt is absent from the "
                             "claim/verdict and HOLD denominators")
        self.assertEqual(mixed["validated_attempts"], 1)

        # unclassed: no feedback-bearing attempt anywhere — reported,
        # never dropped or guessed; zero denominators render null.
        unclassed = stats["classes"]["unclassed"]
        self.assertEqual(unclassed["sessions"], 2)
        self.assertIsNone(unclassed["bailout_rate"])
        self.assertIsNone(unclassed["agreement_rate"])
        # The pack-closed unlocked session carries a rounds:0 stamp: the
        # close-keyed rule puts it INSIDE the epoch denominator.
        self.assertEqual(unclassed["clarification_epoch_sessions"], 1)
        self.assertEqual(unclassed["clarification_rate"], 0.0)

        # Closure mix over closed membership sessions: the rolled-back
        # envelope counts as applied (post-close history lives in churn),
        # read-only and crash-debris never appear, the superseded parent
        # shows under its reason, in-flight sits beside the mix.
        self.assertEqual(stats["closure_mix"], {
            "applied": 16,
            "reverted": 0,
            "bailout": 1,
            "unlocked": {"abandoned": 1, "superseded-by-split": 1},
        })
        self.assertEqual(stats["churn"], {"rolled_back": 1, "re_applied": 0})

        # Dual-stream cross-checks, beside the mechanical rates: one
        # session agrees in both directions, one is self-reported-only,
        # one promoted-only; and the bailed session that self-reported
        # budget_pressure "none" is exactly the miscalibration the
        # stream exists to surface.
        self.assertEqual(stats["cross_checks"]["clarification"], {
            "self_reported_sessions": 2,
            "promoted_sessions": 2,
            "both": 1,
            "self_only": 1,
            "promoted_only": 1,
        })
        self.assertEqual(stats["cross_checks"]["budget"], {
            "pressure": {"none": 21, "tight": 2, "unreported": 2},
            "bailed_with_pressure_none": 1,
        })

        # Loader diagnostics: skipped and filtered files are counted AND
        # named on stderr — never a crash, never a silent skip.
        self.assertIn(CORRUPT_NAME, stderr)
        self.assertIn(FILTERED_NAME, stderr)

    # -- filters ----------------------------------------------------------

    def test_work_class_filter(self) -> None:
        self.seed_corpus()
        stats, _ = self.stats_json("--work-class", "doc")
        self.assertEqual(stats["filters"],
                         {"work_class": "doc", "since": None})
        self.assertEqual(sorted(stats["classes"]), ["doc"])
        self.assertEqual(stats["classes"]["doc"]["sessions"], 4)
        self.assertEqual(stats["corpus"]["sessions"], 4)
        # Context counts are class-independent (excluded sessions are
        # never classed): the read-only count survives the class filter.
        self.assertEqual(stats["corpus"]["read_only_sessions"], 1)
        # The mix follows the filtered membership.
        self.assertEqual(stats["closure_mix"]["applied"], 4)
        self.assertEqual(stats["closure_mix"]["unlocked"], {})

    def test_work_class_unclassed(self) -> None:
        self.seed_corpus()
        stats, _ = self.stats_json("--work-class", "unclassed")
        self.assertEqual(sorted(stats["classes"]), ["unclassed"])
        self.assertEqual(stats["classes"]["unclassed"]["sessions"], 2)

    def test_since_filter(self) -> None:
        self.seed_corpus()
        stats, _ = self.stats_json("--since", "2026-07-01")
        self.assertEqual(stats["filters"],
                         {"work_class": None, "since": "2026-07-01"})
        # Membership: only the one recent record is in the window…
        self.assertEqual(stats["corpus"]["sessions"], 1)
        self.assertEqual(sorted(stats["classes"]), ["code"])
        self.assertEqual(stats["classes"]["code"]["sessions"], 1)
        self.assertEqual(stats["classes"]["code"]["checks"], 1)
        self.assertEqual(stats["corpus"]["read_only_sessions"], 0,
                         msg="context counts honor the since-window")
        # …while the whole-corpus facts stay corpus facts: the epoch is
        # the corpus's true start and records counts every loaded file.
        self.assertEqual(stats["corpus"]["records"], 27)
        self.assertEqual(stats["epoch"]["first_sid"],
                         "2026-06-01-fx-pre-cr-001")

    def test_bad_since_refused(self) -> None:
        self.seed_corpus()
        result = run_bale(self.install,
                          ["stats", "--json", "--since", "not-a-date"],
                          cwd=self.repo, env=self.env)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "",
                         msg="refusal paths are fail()-shaped: stderr, "
                             "non-zero, nothing on stdout")
        self.assertIn("--since", result.stderr)

    # -- degradation -------------------------------------------------------

    def test_empty_corpus_honest_report(self) -> None:
        # No claude/telemetry/ at all: an honest empty report, exit 0.
        stats, _ = self.stats_json()
        self.assertEqual(stats["corpus"]["records"], 0)
        self.assertEqual(stats["corpus"]["sessions"], 0)
        self.assertIsNone(stats["epoch"])
        self.assertIsNone(stats["coverage"]["closure_reason"])
        self.assertIsNone(stats["coverage"]["checkpoint"],
                          msg="the session-D coverage row degrades the "
                              "same honest way: no carrier, no sub-epoch")
        self.assertEqual(stats["classes"], {})
        # Human mode degrades the same way.
        result = run_bale(self.install, ["stats"], cwd=self.repo,
                          env=self.env)
        self.assertEqual(result.returncode, 0)
        self.assertIn("empty corpus", result.stdout)

    # -- human report -------------------------------------------------------

    def test_human_report_shape(self) -> None:
        self.seed_corpus()
        result = run_bale(self.install, ["stats"], cwd=self.repo,
                          env=self.env)
        self.assertEqual(result.returncode, 0)
        out = result.stdout
        # Reference body first: the per-class table and the corpus rows.
        self.assertIn("class", out)
        self.assertIn("agree", out)
        # The named-residual annotation row: code's [n/a] check shows
        # under the table beside disagree, by its schema name.
        self.assertIn("n/a 1", out)
        # Session D surfaces: the ckpt column renders the
        # checkpoint-HOLD rate over checkpointed attempts for code and
        # the honest dash for the pre-epoch classes; the step-15 pair
        # shows in the extras line by name; the checkpoint coverage
        # row sits beside its two siblings.
        self.assertIn("ckpt", out)
        self.assertIn("3/6 (50%)", out)
        self.assertIn("0/0 (—)", out)
        self.assertIn("required-check refused 1", out)
        self.assertIn("required-check overrides 1", out)
        self.assertIn("coverage: checkpoint key since "
                      "2026-06-21-fx-ckpt-zero-001", out)
        self.assertIn("epoch: corpus begins 2026-06-01T10:00:00+00:00", out)
        self.assertIn("closure mix:", out)
        # Trailing summary block last, and NO next-step hint after it —
        # stats is terminal, not a lifecycle step. The last non-empty
        # line is therefore a summary row, not a hint sentence.
        last = [ln for ln in out.splitlines() if ln.strip()][-1]
        self.assertIn("filters:", last)
        # Diagnostics stay on stderr in human mode too.
        self.assertIn(CORRUPT_NAME, result.stderr)
        self.assertNotIn(CORRUPT_NAME, out)


if __name__ == "__main__":
    unittest.main()
