"""upgrade.sh's REQUIRED_RELEASE_MEMBERS against the load-time closure.

The array is upgrade.sh's pre-wipe spot check: "the members whose absence
bricks the install", which its block comment defines as what bin/bale
needs to load at all — the sibling modules it imports at module scope,
the modules those import at module scope in turn, and bin/VERSION, which
bin/bale reads at load and exits without. scripts/build.sh already
asserts the array is a subset of RELEASE_FILES; nothing asserted the
other half, so the array drifted: bin/bale_stats.py, bin/bale_open.py,
bin/bale_relay.py, and bin/bale_wizard.py all became load-time members
without joining it (trued up by session pack-wizard-ui, 2026-10-03).

This suite derives the closure from the sources (module-scope `import`
and `from ... import` statements, including those inside a module-scope
`try`, naming a file in bin/) and pins the array against it, so the next
load-time sibling fails here instead of drifting. bin/bale_sandbox.py is
the documented exception the other way: imported lazily at every site,
it is not a load-time member and stays off the list — pinned below so a
future module-scope import of it shows up as a decision to make.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
BIN_DIR = REPO_ROOT / "bin"
UPGRADE_SH = REPO_ROOT / "upgrade.sh"


def required_release_members() -> list:
    """The array, by upgrade.sh's own format contract (build.sh extracts
    it the same way): "REQUIRED_RELEASE_MEMBERS=(" at column 0, one bare
    path per line, ")" at column 0."""
    text = UPGRADE_SH.read_text(encoding="utf-8")
    m = re.search(r"^REQUIRED_RELEASE_MEMBERS=\(\n(.*?)^\)", text,
                  re.MULTILINE | re.DOTALL)
    if m is None:
        raise AssertionError("REQUIRED_RELEASE_MEMBERS block not found")
    return [ln.strip() for ln in m.group(1).splitlines() if ln.strip()]


def module_scope_imports(path: Path) -> set:
    """Top-level module names imported at module scope of `path`
    (directly, or inside a module-scope try/except)."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    statements = []
    for node in tree.body:
        statements.append(node)
        if isinstance(node, ast.Try):
            statements.extend(node.body)
            for handler in node.handlers:
                statements.extend(handler.body)
    names = set()
    for node in statements:
        if isinstance(node, ast.Import):
            names.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and \
                node.level == 0:
            names.add(node.module.split(".")[0])
    return names


def load_time_closure() -> set:
    """bin/ paths bin/bale needs at load: the sibling-module closure of
    its module-scope imports."""
    seen = set()
    queue = [BIN_DIR / "bale"]
    while queue:
        path = queue.pop()
        for name in module_scope_imports(path):
            sibling = BIN_DIR / f"{name}.py"
            rel = f"bin/{sibling.name}"
            if sibling.is_file() and rel not in seen:
                seen.add(rel)
                queue.append(sibling)
    return seen


class RequiredMembersTest(unittest.TestCase):
    def test_every_load_time_sibling_is_spot_checked(self) -> None:
        missing = sorted(load_time_closure() - set(required_release_members()))
        self.assertEqual(missing, [], "load-time members upgrade.sh's "
                         "pre-wipe spot check does not verify")

    def test_the_closure_reaches_the_known_members(self) -> None:
        # Guards the derivation itself: an AST walk that silently found
        # nothing would make the test above vacuous.
        closure = load_time_closure()
        for rel in ("bin/bale_config.py", "bin/bale_pack.py",
                    "bin/bale_stats.py", "bin/bale_open.py",
                    "bin/bale_relay.py", "bin/bale_wizard.py",
                    "bin/_bale_toml.py"):
            self.assertIn(rel, closure)

    def test_entry_point_and_version_file_are_spot_checked(self) -> None:
        members = required_release_members()
        self.assertIn("bin/bale", members)
        # bin/bale reads bin/VERSION at load and exits without it.
        self.assertIn("_VERSION_FILE", (BIN_DIR / "bale").read_text(
            encoding="utf-8"))
        self.assertIn("bin/VERSION", members)

    def test_sandbox_stays_a_lazy_import(self) -> None:
        self.assertNotIn("bin/bale_sandbox.py", load_time_closure())
        self.assertNotIn("bin/bale_sandbox.py", required_release_members(),
                         "bale_sandbox is lazy-only; upgrade.sh's comment "
                         "says why it stays off — revisit both together")

    def test_no_duplicates(self) -> None:
        members = required_release_members()
        self.assertEqual(len(members), len(set(members)))


if __name__ == "__main__":
    unittest.main()
