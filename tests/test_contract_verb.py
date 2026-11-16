#!/usr/bin/env python3
"""The `bale contract` suite (v0.4.53, session contract-verb).

`bale contract [--json]` publishes bale's machine contract in one read:
every closed vocabulary, the refusal-reason sets of open, relay, unlock
and revert, and the ordered top-level keys of every --json line, each
with its home in the install and a pointer into it. The key contract is
format_contract_json's docstring in bin/bale_report.py; this suite pins
the behavior around it:

- ``ContractCliTest`` runs the real verb from a scratch install, in a
  directory that is not a git repository: one parseable line on stdout,
  its keys, ``outcome`` and ``bale_version``, determinism across runs and
  across working directories, no absolute paths, no writes, and the
  human mode's exit 0.
- ``ContractValuesTest`` checks every published value against its home:
  the telemetry schema's enums read here from the schema file (never a
  copy of the list), every code-homed entry against the module constant
  its pointer names, and the refusal sets in tuple order.
- ``JsonKeysMatchRenderedLinesTest`` renders one line per surface with
  stub inputs (``bale status --json`` through the real CLI, the rest
  in-process) and compares its keys, in order, with the surface's
  ``json_keys`` entry — so a renderer whose line drifts from its tuple
  fails here, and a ``format_*_json`` renderer the contract does not
  publish fails the coverage test.
- ``KeyedLineTest`` pins the lifted tuples' seam: ``_keyed_line`` refuses
  a value set that is not its tuple, and the renderers that gained an
  outcome check (apply, unlock) refuse an off-vocabulary word.

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; see its module docstring.

Run directly::

    python3 tests/test_contract_verb.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import inspect
import json
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

from harness import (
    REPO_ROOT,
    _load_module,
    bale_env,
    git_env,
    make_install,
    make_repo,
    make_sandbox_home,
    run_bale,
)

TELEMETRY_SCHEMA = "schemas/telemetry-record.schema.json"
FIXTURE_CORPUS = REPO_ROOT / "tests" / "fixtures" / "stats_corpus"

# The five keys the session's brief pins as the line's floor.
BRIEF_KEYS = ("outcome", "bale_version", "vocabularies", "refusal_reasons",
              "json_keys")

# The surfaces the brief requires by name.
REQUIRED_SURFACES = ("pack", "open", "apply", "relay", "unlock", "revert",
                     "status", "stats", "open-refused", "relay-refused",
                     "unlock-refused", "revert-refused")

# The nine apply outcome words, as the brief names them in the order
# format_apply_json's docstring lists them.
APPLY_WORDS = ("applied", "held", "reverted", "bailout", "clarification",
               "dry-run", "scope-drift-refused", "required-check-refused",
               "base-drift-refused")

# format_*_json functions that build a value INSIDE a line rather than a
# line: they have no surface of their own.
SUB_OBJECT_RENDERERS = {"format_sweep_json", "format_include_group_json"}


def _fresh_dir(path: Path) -> Path:
    """Make `path` (it must not exist yet) and return it."""
    path.mkdir()
    return path


def _schema() -> dict:
    return json.loads((REPO_ROOT / TELEMETRY_SCHEMA).read_text(
        encoding="utf-8"))


def _schemas(report) -> dict:
    return {home: json.loads((REPO_ROOT / home).read_text(encoding="utf-8"))
            for home in report.contract_schema_homes()}


class ContractCliTest(unittest.TestCase):
    """The real verb, run from a scratch install in a non-repo cwd."""

    @classmethod
    def setUpClass(cls) -> None:
        cls._tmpdir = tempfile.TemporaryDirectory(prefix="bale-contract-")
        cls.tmp = Path(cls._tmpdir.name)
        cls.home = make_sandbox_home(cls.tmp)
        cls.install = make_install(cls.tmp)
        cls.env = bale_env(cls.home, cls.tmp)
        cls.cwd = cls.tmp / "not-a-repo"
        cls.cwd.mkdir()
        cls.first = run_bale(cls.install, ["contract", "--json"],
                             cwd=cls.cwd, env=cls.env)
        cls.second = run_bale(cls.install, ["contract", "--json"],
                              cwd=cls.cwd, env=cls.env)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmpdir.cleanup()

    def line(self) -> dict:
        self.assertEqual(self.first.returncode, 0, msg=self.first.stderr)
        return json.loads(self.first.stdout)

    def test_cwd_is_not_a_repository(self) -> None:
        """The premise of the repo-free tests: git sees no repo here."""
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"],
                           cwd=self.cwd, env=git_env(self.home),
                           capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0, msg=r.stdout)

    def test_exits_zero_with_exactly_one_line_on_stdout(self) -> None:
        self.assertEqual(self.first.returncode, 0, msg=self.first.stderr)
        self.assertTrue(self.first.stdout.endswith("\n"))
        self.assertEqual(len(self.first.stdout.splitlines()), 1)
        self.assertEqual(self.first.stderr, "")

    def test_line_parses_and_carries_the_pinned_keys(self) -> None:
        line = self.line()
        for key in BRIEF_KEYS:
            with self.subTest(key=key):
                self.assertIn(key, line)
        report = _load_module("bale_report")
        self.assertEqual(list(line), list(report.CONTRACT_REPORT_KEYS))

    def test_outcome_is_contract(self) -> None:
        self.assertEqual(self.line()["outcome"], "contract")

    def test_bale_version_is_bin_version(self) -> None:
        version = (self.install / "bin" / "VERSION").read_text(
            encoding="utf-8").strip()
        self.assertEqual(self.line()["bale_version"], version)

    def test_two_runs_print_one_stdout(self) -> None:
        self.assertEqual(self.first.stdout, self.second.stdout)

    def test_stdout_does_not_depend_on_the_working_directory(self) -> None:
        repo = make_repo(_fresh_dir(self.tmp / "elsewhere"), self.home)
        from_repo = run_bale(self.install, ["contract", "--json"],
                             cwd=repo, env=self.env)
        self.assertEqual(from_repo.returncode, 0, msg=from_repo.stderr)
        self.assertEqual(from_repo.stdout, self.first.stdout)

    def test_no_absolute_paths_or_timestamps(self) -> None:
        out = self.first.stdout
        for path in (self.install, self.tmp, self.home, REPO_ROOT):
            with self.subTest(path=str(path)):
                self.assertNotIn(str(path), out)
        self.assertNotRegex(out, r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}")

        # Only a schema `pointer` (a JSON pointer) may start with "/";
        # every `home` is install-relative.
        def walk(node, key=None):
            if isinstance(node, dict):
                for k, v in node.items():
                    yield from walk(v, k)
            elif isinstance(node, list):
                for v in node:
                    yield from walk(v, key)
            elif isinstance(node, str):
                yield key, node

        for key, value in walk(json.loads(out)):
            with self.subTest(key=key, value=value):
                if key == "home":
                    self.assertFalse(Path(value).is_absolute())
                    self.assertNotIn("..", Path(value).parts)
                elif key != "pointer":
                    self.assertFalse(value.startswith("/"))

    def test_writes_nothing(self) -> None:
        before = sorted(p.name for p in self.cwd.iterdir())
        run_bale(self.install, ["contract", "--json"], cwd=self.cwd,
                 env=self.env)
        run_bale(self.install, ["contract"], cwd=self.cwd, env=self.env)
        self.assertEqual(sorted(p.name for p in self.cwd.iterdir()), before)
        self.assertEqual(before, [])
        self.assertFalse((self.tmp / "bale-install-sandbox").exists())

    def test_human_mode_exits_zero_and_lists_every_entry(self) -> None:
        human = run_bale(self.install, ["contract"], cwd=self.cwd,
                         env=self.env)
        self.assertEqual(human.returncode, 0, msg=human.stderr)
        line = self.line()
        for section in ("vocabularies", "refusal_reasons", "json_keys"):
            for name in line[section]:
                with self.subTest(section=section, name=name):
                    self.assertIn(f"  {name}  ", human.stdout)
        self.assertIn("contract", human.stdout.splitlines()[0])

    def test_verb_is_listed_by_help_and_completion(self) -> None:
        listing = run_bale(self.install, ["help"], cwd=self.cwd,
                           env=self.env)
        self.assertRegex(listing.stdout, r"(?m)^\s+contract\s")
        completion = run_bale(self.install, ["completion", "bash"],
                              cwd=self.cwd, env=self.env)
        self.assertEqual(completion.returncode, 0, msg=completion.stderr)
        self.assertIn("contract", completion.stdout)

    def test_unreadable_schema_fails_loud_with_nothing_on_stdout(
            self) -> None:
        with tempfile.TemporaryDirectory(prefix="bale-contract-broken-") as d:
            broken = make_install(Path(d))
            (broken / TELEMETRY_SCHEMA).write_text("{", encoding="utf-8")
            r = run_bale(broken, ["contract", "--json"], cwd=self.cwd,
                         env=self.env)
        self.assertEqual(r.returncode, 1)
        self.assertEqual(r.stdout, "")
        self.assertIn(TELEMETRY_SCHEMA, r.stderr)


class ContractValuesTest(unittest.TestCase):
    """Every published value equals its home's, read independently."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = _load_module("bale_report")
        cls.line = json.loads(cls.report.format_contract_json(
            version="9.9.9", schemas=_schemas(cls.report)))

    def test_telemetry_outcome_is_the_schema_enum_in_order(self) -> None:
        entry = self.line["vocabularies"]["telemetry-outcome"]
        self.assertEqual(entry["home"], TELEMETRY_SCHEMA)
        self.assertEqual(entry["pointer"], "/properties/outcome")
        self.assertEqual(entry["values"],
                         _schema()["properties"]["outcome"]["enum"])

    def test_closure_reason_is_the_schema_enum_without_null(self) -> None:
        entry = self.line["vocabularies"]["closure-reason"]
        self.assertEqual(entry["home"], TELEMETRY_SCHEMA)
        self.assertEqual(
            entry["pointer"],
            "/properties/attempts/items/properties/closure_reason")
        enum = (_schema()["properties"]["attempts"]["items"]["properties"]
                ["closure_reason"]["enum"])
        self.assertIn(None, enum)
        self.assertEqual(entry["values"], [v for v in enum if v is not None])

    def test_apply_outcome_is_the_lifted_tuple(self) -> None:
        entry = self.line["vocabularies"]["apply-outcome"]
        self.assertEqual(entry, {"home": "bin/bale_report.py",
                                 "pointer": "APPLY_OUTCOMES",
                                 "values": list(APPLY_WORDS)})
        self.assertEqual(self.report.APPLY_OUTCOMES, APPLY_WORDS)

    def test_apply_docstring_cites_the_tuple_and_lists_every_word(
            self) -> None:
        doc = self.report.format_apply_json.__doc__
        self.assertIn("APPLY_OUTCOMES", doc)
        listed = re.findall(r'^\s+"([a-z-]+)"', doc.split("sid      the")[0],
                            re.MULTILINE)
        self.assertEqual(tuple(listed), APPLY_WORDS)

    def test_every_vocabulary_value_comes_from_its_home(self) -> None:
        schema_docs = _schemas(self.report)
        for name, entry in self.line["vocabularies"].items():
            with self.subTest(vocabulary=name):
                self.assertTrue((REPO_ROOT / entry["home"]).is_file())
                if entry["pointer"].startswith("/"):
                    node = schema_docs[entry["home"]]
                    for token in entry["pointer"][1:].split("/"):
                        node = node[token]
                    self.assertEqual(entry["values"],
                                     [v for v in node["enum"]
                                      if v is not None])
                else:
                    # A code home is this module, or (0.4.63) the bin/
                    # sibling the entry names — bale_stats for
                    # hold-class — read from that module's own constant.
                    homes = {"bin/bale_report.py": self.report,
                             "bin/bale_stats.py": _load_module("bale_stats")}
                    self.assertIn(entry["home"], homes)
                    self.assertEqual(
                        entry["values"],
                        list(getattr(homes[entry["home"]],
                                     entry["pointer"])))
                self.assertTrue(entry["values"])
                self.assertEqual(len(entry["values"]),
                                 len(set(entry["values"])))

    def test_vocabulary_names_are_kebab_case(self) -> None:
        for name in self.line["vocabularies"]:
            with self.subTest(name=name):
                self.assertRegex(name, r"^[a-z]+(-[a-z]+)*$")

    def test_refusal_reasons_are_the_four_tuples_in_order(self) -> None:
        expected = {"open": "OPEN_REFUSAL_REASONS",
                    "relay": "RELAY_REFUSAL_REASONS",
                    "unlock": "UNLOCK_REFUSAL_REASONS",
                    "revert": "REVERT_REFUSAL_REASONS"}
        self.assertEqual(list(self.line["refusal_reasons"]), list(expected))
        for verb, pointer in expected.items():
            with self.subTest(verb=verb):
                self.assertEqual(
                    self.line["refusal_reasons"][verb],
                    {"home": "bin/bale_report.py", "pointer": pointer,
                     "values": list(getattr(self.report, pointer))})
        self.assertEqual(self.line["refusal_reasons"]["open"]["values"][-1],
                         "unclassified")
        self.assertEqual(len(self.line["refusal_reasons"]["open"]["values"]),
                         15)

    def test_required_surfaces_and_pack_keys(self) -> None:
        for surface in REQUIRED_SURFACES:
            with self.subTest(surface=surface):
                self.assertIn(surface, self.line["json_keys"])
        self.assertEqual(self.line["json_keys"]["pack"],
                         list(self.report.PACK_REPORT_KEYS))
        self.assertEqual(len(self.line["json_keys"]["pack"]), 16)

    def test_open_keys_are_pack_keys_then_its_own(self) -> None:
        keys = self.line["json_keys"]["open"]
        self.assertEqual(keys[:16], list(self.report.PACK_REPORT_KEYS))
        for key in ("outcome", "sid", "tarball", "opener", "desk", "bundle",
                    "reason", "cause"):
            with self.subTest(key=key):
                self.assertIn(key, keys)

    def test_json_key_homes_name_the_tuples(self) -> None:
        self.assertEqual(list(self.line["json_key_homes"]),
                         list(self.line["json_keys"]))
        for surface, home in self.line["json_key_homes"].items():
            with self.subTest(surface=surface):
                self.assertEqual(home["home"], "bin/bale_report.py")
                self.assertEqual(self.line["json_keys"][surface],
                                 list(getattr(self.report, home["pointer"])))

    def test_every_key_tuple_is_duplicate_free(self) -> None:
        for surface, keys in self.line["json_keys"].items():
            with self.subTest(surface=surface):
                self.assertEqual(len(keys), len(set(keys)))
                self.assertEqual(keys[0], "outcome")

    def test_a_stale_pointer_fails_loud(self) -> None:
        saved = self.report.CONTRACT_REFUSAL_REASONS
        try:
            self.report.CONTRACT_REFUSAL_REASONS = (("open", "NO_SUCH"),)
            with self.assertRaises(ValueError):
                self.report.format_contract_json(
                    version="x", schemas=_schemas(self.report))
        finally:
            self.report.CONTRACT_REFUSAL_REASONS = saved
        with self.assertRaises(ValueError):
            self.report.format_contract_json(version="x", schemas={})

    def test_resolve_json_pointer_unescapes(self) -> None:
        doc = {"a/b": {"m~n": [10, 20]}}
        self.assertEqual(
            self.report.resolve_json_pointer(doc, "/a~1b/m~0n/1"), 20)
        self.assertIs(self.report.resolve_json_pointer(doc, ""), doc)
        with self.assertRaises(ValueError):
            self.report.resolve_json_pointer(doc, "/missing")
        with self.assertRaises(ValueError):
            self.report.resolve_json_pointer(doc, "a")


class JsonKeysMatchRenderedLinesTest(unittest.TestCase):
    """Each json_keys entry equals the keys its renderer actually emits."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = _load_module("bale_report")
        cls.stats = _load_module("bale_stats")
        cls.json_keys = json.loads(cls.report.format_contract_json(
            version="x", schemas=_schemas(cls.report)))["json_keys"]
        cls._tmpdir = tempfile.TemporaryDirectory(prefix="bale-contract-keys-")
        cls.tmp = Path(cls._tmpdir.name)

    @classmethod
    def tearDownClass(cls) -> None:
        cls._tmpdir.cleanup()

    def rendered(self) -> dict:
        """surface -> (renderer name, one rendered line), stub inputs."""
        r = self.report
        pack_kw = dict(sid="2026-10-13-x-001", tarball=Path("/t"),
                       log_path=Path("/l"), session_dir=Path("/s"),
                       context_files=1, opener="o\n")
        pack_line = r.format_pack_json(**pack_kw)
        return {
            "pack": ("format_pack_json", pack_line),
            "context-pack": ("format_context_pack_json",
                             r.format_context_pack_json(
                                 tarball=Path("/t"), directory=Path("/d"),
                                 tree_name="d", context_files=1,
                                 total_bytes=1, in_git=False)),
            "open": ("format_open_json", r.format_open_json(
                outcome="opened", bundle={}, members={},
                pack_report=json.loads(pack_line))),
            "open-refused": ("format_open_refusal_json",
                             r.format_open_refusal_json(
                                 reason="not-found", cause="c", bundle=None,
                                 members=None)),
            "relay": ("format_relay_json", r.format_relay_json(
                outcome="relayed", sid="s", round_no=1, side="worker")),
            "relay-refused": ("format_relay_refusal_json",
                              r.format_relay_refusal_json(
                                  sid="s", reason="schema", cause="c",
                                  log_path=None, telemetry=None)),
            "apply": ("format_apply_json", r.format_apply_json(
                outcome="applied", sid="s", log_path=Path("/l"),
                state="PASS", exit_code=0, action="merge")),
            "retry": ("format_apply_json", r.format_apply_json(
                outcome="held", sid="s", log_path=Path("/l"),
                state="HOLD", exit_code=1, action="inspect")),
            "unlock": ("format_unlock_json",
                       r.format_unlock_json(outcome="unlocked", sid="s")),
            "unlock-refused": ("format_unlock_refusal_json",
                               r.format_unlock_refusal_json(
                                   reason="not-open", message="m", sid="s",
                                   open_sessions=[])),
            "revert": ("format_revert_json",
                       r.format_revert_json(sid="s", log_path="/l")),
            "revert-refused": ("format_revert_refusal_json",
                               r.format_revert_refusal_json(
                                   reason="no-git", cause="c", sid=None)),
            "stats": ("format_stats_json", r.format_stats_json(
                self.stats.compute_stats(self.tmp / "no-corpus"))),
            "stats-dossier": ("format_session_dossier_json",
                              r.format_session_dossier_json(
                                  self.stats.compute_session_dossier(
                                      FIXTURE_CORPUS,
                                      "2026-06-05-fx-applied-001"))),
            "stats-dossier-miss": ("format_session_dossier_json",
                                   r.format_session_dossier_json(
                                       self.stats.compute_session_dossier(
                                           self.tmp / "no-corpus", "nope"))),
            "config-hooks": ("format_config_hooks_json",
                             r.format_config_hooks_json(
                                 outcome="listed", version="v",
                                 store=self.tmp / "acceptances.json",
                                 entries=[], forgotten=None)),
            "contract": ("format_contract_json", r.format_contract_json(
                version="x", schemas=_schemas(r))),
        }

    def test_each_surface_line_has_exactly_its_published_keys(self) -> None:
        rendered = self.rendered()
        for surface, (_name, line) in rendered.items():
            with self.subTest(surface=surface):
                self.assertEqual(len(line.splitlines()), 1)
                self.assertEqual(list(json.loads(line)),
                                 self.json_keys[surface])

    def test_status_line_through_the_real_cli(self) -> None:
        base = _fresh_dir(self.tmp / "status")
        home = make_sandbox_home(base)
        install = make_install(base)
        env = bale_env(home, base)
        outside = _fresh_dir(base / "outside")
        repo = make_repo(base, home)
        for cwd in (outside, repo):
            with self.subTest(cwd=cwd.name):
                r = run_bale(install, ["status", "--json"], cwd=cwd, env=env)
                self.assertEqual(r.returncode, 0, msg=r.stderr)
                self.assertEqual(list(json.loads(r.stdout)),
                                 self.json_keys["status"])

    def test_every_surface_is_covered_and_every_line_renderer_published(
            self) -> None:
        rendered = self.rendered()
        self.assertEqual(sorted(set(rendered) | {"status"}),
                         sorted(self.json_keys))
        line_renderers = {
            name for name, fn in inspect.getmembers(self.report,
                                                    inspect.isfunction)
            if re.fullmatch(r"format_\w+_json", name)
            and name not in SUB_OBJECT_RENDERERS}
        exercised = {name for name, _line in rendered.values()}
        exercised.add("format_status_json")
        self.assertEqual(sorted(line_renderers), sorted(exercised),
                         msg="a format_*_json line renderer the contract "
                             "does not publish (or a stale entry here)")


class KeyedLineTest(unittest.TestCase):
    """The lifted tuples' seam and the two new outcome checks."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.report = _load_module("bale_report")

    def test_keyed_line_emits_in_tuple_order(self) -> None:
        line = self.report._keyed_line(("b", "a"), {"a": 1, "b": 2},
                                       surface="t")
        self.assertEqual(line, '{"b": 2, "a": 1}')

    def test_keyed_line_refuses_a_missing_or_extra_key(self) -> None:
        with self.assertRaisesRegex(ValueError, "missing \\['b'\\]"):
            self.report._keyed_line(("a", "b"), {"a": 1}, surface="t")
        with self.assertRaisesRegex(ValueError, "unexpected \\['c'\\]"):
            self.report._keyed_line(("a",), {"a": 1, "c": 2}, surface="t")

    def test_stats_line_refuses_an_unpublished_key(self) -> None:
        with self.assertRaises(ValueError):
            self.report.format_stats_json({"epoch": None})

    def test_apply_refuses_an_unknown_outcome(self) -> None:
        for word in self.report.APPLY_OUTCOMES:
            with self.subTest(word=word):
                self.report.format_apply_json(outcome=word, sid="s",
                                              log_path=Path("/l"))
        with self.assertRaises(ValueError):
            self.report.format_apply_json(outcome="packed", sid="s",
                                          log_path=Path("/l"))

    def test_unlock_refuses_an_unknown_outcome(self) -> None:
        self.assertEqual(self.report.UNLOCK_OUTCOMES,
                         ("unlocked", "no-op", "unlock-refused"))
        with self.assertRaises(ValueError):
            self.report.format_unlock_json(outcome="closed")

    def test_include_group_state_reads_its_tuple(self) -> None:
        for state in self.report.INCLUDE_GROUP_STATES:
            self.report.format_include_group_json(
                name="g", state=state, triggers=[], pulled=[], row="r")
        with self.assertRaises(ValueError):
            self.report.format_include_group_json(
                name="g", state="off", triggers=[], pulled=[], row="r")

    def test_outcome_constants_are_the_rendered_words(self) -> None:
        r = self.report
        self.assertEqual(r.PACK_OUTCOMES, ("packed",))
        self.assertEqual(r.CONTEXT_PACK_OUTCOMES, ("context-packed",))
        self.assertEqual(r.STATUS_OUTCOMES, ("status",))
        self.assertEqual(r.STATS_OUTCOMES, ("stats",))
        self.assertEqual(r.STATS_DOSSIER_OUTCOMES, ("dossier",))
        self.assertEqual(r.CONTRACT_OUTCOMES, ("contract",))


if __name__ == "__main__":
    unittest.main(verbosity=2)
