#!/usr/bin/env python3
"""The harness-level slow-test gate (board-50 fold-in, 0.4.16).

Generation-heavy cases gate behind ``BALE_TEST_SLOW=1`` via the
``slow`` decorator in tests/harness.py. This suite pins the helper's
three contract points:

- the env var's spelling is ``BALE_TEST_SLOW``, exactly — a desk
  constraint of the landing session, pinned here so a rename fails
  loud instead of silently orphaning every documented invocation;
- only the literal value ``"1"`` opens the gate — ``yes``, ``true``,
  and the empty string all leave it closed, so a half-set gate skips
  loudly (the skip reason names the exact spelling) rather than
  half-opening;
- the decorator really skips when closed and really runs when open,
  exercised through ``slow_gate()`` (the factory the harness exposes
  precisely so both states are testable without re-importing it).

Hermetic and stdlib-only: nothing runs but synthetic in-memory test
cases; the environment is patched per-case and restored.

Run:  python3 -m unittest tests.test_slow_gate -v
  or: python3 -m unittest discover -s tests -p 'test_slow_gate.py'
"""

from __future__ import annotations

import os
import unittest
from unittest import mock

from harness import SLOW_ENV_VAR, slow_gate


def _run_gated_case(env_value):
    """Build a one-case suite under the given env state; return its result.

    ``env_value`` of None means the variable is absent entirely.
    """
    env = {k: v for k, v in os.environ.items() if k != SLOW_ENV_VAR}
    if env_value is not None:
        env[SLOW_ENV_VAR] = env_value
    with mock.patch.dict(os.environ, env, clear=True):
        gate = slow_gate()

        class Probe(unittest.TestCase):
            ran = False

            @gate
            def test_case(self):
                Probe.ran = True

        result = unittest.TestResult()
        unittest.TestLoader().loadTestsFromTestCase(Probe).run(result)
        return Probe.ran, result


class SlowGateSpellingTest(unittest.TestCase):
    """The env var name is a landing-session constraint, pinned."""

    def test_env_var_is_spelled_exactly(self):
        self.assertEqual(SLOW_ENV_VAR, "BALE_TEST_SLOW")

    def test_skip_reason_names_the_spelling(self):
        """The skip line is the gate's discoverability surface: a
        skipped run must tell the reader the exact variable to set."""
        with mock.patch.dict(os.environ, {}, clear=False):
            os.environ.pop(SLOW_ENV_VAR, None)
            _, result = _run_gated_case(None)
        self.assertEqual(len(result.skipped), 1)
        self.assertIn("BALE_TEST_SLOW=1", result.skipped[0][1])


class SlowGateBehaviorTest(unittest.TestCase):
    """Closed by default; only the literal "1" opens it."""

    def test_absent_var_skips(self):
        ran, result = _run_gated_case(None)
        self.assertFalse(ran)
        self.assertEqual(len(result.skipped), 1)
        self.assertTrue(result.wasSuccessful())

    def test_value_one_runs(self):
        ran, result = _run_gated_case("1")
        self.assertTrue(ran)
        self.assertEqual(result.skipped, [])
        self.assertTrue(result.wasSuccessful())

    def test_other_values_stay_closed(self):
        for value in ("", "0", "yes", "true", "TRUE", " 1"):
            with self.subTest(value=value):
                ran, result = _run_gated_case(value)
                self.assertFalse(ran)
                self.assertEqual(len(result.skipped), 1)


if __name__ == "__main__":
    unittest.main()
