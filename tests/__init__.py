"""Makes ``tests`` a package so every suite runs in the dotted form.

The suites import their shared helpers by bare name (``from harness
import ...``, ``from test_handoff_fixture import ...``), which resolves
only when ``tests/`` itself is on ``sys.path``. The three run forms:

- discovery, ``python3 -m unittest discover -s tests``: unittest puts
  ``tests/`` at ``sys.path[0]`` and imports each suite under its bare
  name. This file is never executed in that form.
- direct execution, ``python3 tests/<suite>.py``: Python puts the
  script's directory, ``tests/``, at ``sys.path[0]``. Nor in this one.
- dotted, ``python3 -m unittest tests.<suite>`` from the repo root:
  only the repo root is on the path, so importing ``tests.<suite>``
  runs this file first, and the insert below gives the suite's bare
  imports the same ``tests/`` entry the other two forms provide.

It is one entry at ``sys.path[0]`` when absent, exactly what discovery
does, so a bare name resolves to the same file in all three forms and
nothing is added twice. No module is imported here and no name is
exported: a suite never imports from ``tests`` itself.

tests/test_dotted_run_form.py pins this for the whole tree: every
``tests/test_*.py`` must load as ``tests.<suite>`` from the repo root.
Board 113, 2026-09-19.
"""

import sys
from pathlib import Path

_TESTS_DIR = str(Path(__file__).resolve().parent)
if _TESTS_DIR not in sys.path:
    sys.path.insert(0, _TESTS_DIR)
