#!/usr/bin/env python3
"""Hermetic E2E for board 50: CRLF tolerance at every text-file read.

One rule, verbatim at every ingest site (the session's constraint):
replace CRLF with LF and nothing else — bare CR is never touched.
Published and echoed hashes are over LF-normalized bytes; everything
downstream of the checkpoint commit stays byte-exact.

Two species of test live here, deliberately in one file so the
repo-wide contract has one home:

- **The code change** (``--checkpoint-file`` ingest normalization,
  ``locate_and_read_checkpoint_file`` in ``bin/bale_pack.py``): a
  CRLF-mangled delivery commits the LF oracle the planner published,
  the echoed/stamped sha256 is the LF-bytes hash the desk's published
  hash compares against, and install's identical-bytes idempotency
  treats LF and CRLF twins of one oracle as the same delivery — the
  aborted-pack re-run posture survives transport. Genuinely different
  bytes still refuse: normalization never widens what counts as
  "identical" beyond line endings.
- **Pin-as-contract tests** for the surfaces the board-50 sitting
  found already tolerant by implementation accident (``read_text``
  universal-newline translation; the TOML spec's own CRLF rule):
  ``--readme-file``, ``bale.toml``, and ``.baleignore``. Tolerance by
  accident is exactly what a test exists to make deliberate — a
  future refactor from text-mode reads to ``read_bytes`` fails here
  instead of regressing silently.

Out of this rule's reach, asserted nowhere and deliberately so:
response-tarball members are hash-pinned worker bytes, not
transport-mangled prose, and stay byte-exact by design (BALE.md's
normalization paragraph carries the scoping).

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness
in ``tests/harness.py`` carries it; the checkpoint fixtures come from
``tests/test_per_sid_checkpoint.py`` / ``test_checkpoint_file_flag.py``
and the walk fixture from ``tests/test_pack_guards.py`` (each a
test-less base or a module-level helper, so nothing re-runs).

Run directly::

    python3 tests/test_crlf_tolerance.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import hashlib
import json
import tarfile
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
from test_per_sid_checkpoint import CP_PATTERN, checkpoint_script
from test_checkpoint_file_flag import (
    CheckpointFileFixture,
    DIFFERING_BYTES_PHRASE,
    IDEMPOTENT_PHRASE,
)
from test_pack_guards import PackGuardsBase


def crlf(text: str) -> bytes:
    """The transport-mangled twin: `text`'s UTF-8 bytes with every LF
    rewritten as CRLF — what a mail client, a chat download, or a
    Windows checkout does to an LF file."""
    return text.encode("utf-8").replace(b"\n", b"\r\n")


class CheckpointCrlfIngestTest(CheckpointFileFixture):
    """The code change: --checkpoint-file normalizes at read, before
    the commit, the echo, and the stamp."""

    def write_source_bytes(self, data: bytes, name: str = "cp.sh") -> Path:
        """Byte-exact source writer — write_bytes, never write_text,
        so the CRLF bytes under test reach the disk untranslated."""
        p = self.tmp / name
        p.write_bytes(data)
        return p

    def test_crlf_delivery_commits_lf_oracle_with_lf_hashes(self) -> None:
        """A CRLF-mangled checkpoint delivery commits LF bytes at the
        resolved path, and the echo (--json keys) and the provenance
        stamp both carry the LF-bytes sha256 — the hash the desk
        published over LF bytes matches across a mangling transport."""
        self.configure_base(CP_PATTERN)
        lf_body = checkpoint_script("crlf-ingest-cp")
        lf_bytes = lf_body.encode("utf-8")
        crlf_bytes = crlf(lf_body)
        self.assertNotEqual(lf_bytes, crlf_bytes,
                            msg="fixture sanity: the twins must differ "
                                "on the wire")
        source = self.write_source_bytes(crlf_bytes)
        sid = self.predicted_sid("crlfing")
        resolved = self.resolved_for(sid)

        result = self.flag_pack("crlfing", source, "--json")
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")

        committed = self.head_bytes(resolved)
        self.assertEqual(committed, lf_bytes,
                         msg="the committed oracle is the LF twin, exact")
        self.assertNotIn(b"\r\n", committed)

        lf_sha = hashlib.sha256(lf_bytes).hexdigest()
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(payload["checkpoint_file_sha256"], lf_sha,
                         msg="the echo is the LF-bytes hash, not the "
                             "raw file's")
        manifest = self.persisted_manifest(payload["sid"])
        self.assertEqual(manifest["provenance"]["checkpoint"], {
            "path": resolved,
            "sha256": lf_sha,
        }, msg="echo, stamp, and committed bytes carry one LF identity")

    def test_bare_cr_is_never_touched(self) -> None:
        """The rule is CRLF→LF and nothing else: a lone CR inside the
        script body survives ingest byte-for-byte."""
        self.configure_base(CP_PATTERN)
        body = ("#!/usr/bin/env bash\n"
                "echo \"[PASS] bare\rcr-marker\"\n"
                "exit 0\n")
        source = self.write_source_bytes(body.encode("utf-8"))
        sid = self.predicted_sid("barecr")

        result = self.flag_pack("barecr", source)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        committed = self.head_bytes(self.resolved_for(sid))
        self.assertEqual(committed, body.encode("utf-8"),
                         msg="bare CR bytes pass through untouched")
        self.assertIn(b"\r", committed)

    def test_crlf_twin_of_committed_lf_oracle_is_idempotent(self) -> None:
        """The aborted-pack re-run posture survives transport: the LF
        oracle is committed, the re-delivered file arrives CRLF-mangled,
        and install's identical-bytes comparison — running on normalized
        bytes — takes the idempotent branch, no second commit."""
        self.configure_base(CP_PATTERN)
        lf_body = checkpoint_script("twin-cp")
        sid = self.predicted_sid("twin")
        resolved = self.resolved_for(sid)
        self.commit_files({resolved: lf_body},
                          "pin the LF oracle (the aborted pack's "
                          "leftover commit)")
        source = self.write_source_bytes(crlf(lf_body))

        result = self.flag_pack("twin", source)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn(IDEMPOTENT_PHRASE, result.stdout + result.stderr)
        self.assertEqual(len(self.commit_subjects(resolved)), 1,
                         msg="no second commit for the path")
        self.assertEqual(self.open_sids(), [sid])

    def test_genuinely_different_crlf_bytes_still_refuse(self) -> None:
        """Normalization widens 'identical' by line endings only: a
        CRLF file whose content differs from the ratified oracle still
        refuses loudly — committed-is-ratified is untouched."""
        self.configure_base(CP_PATTERN)
        sid = self.predicted_sid("clash")
        resolved = self.resolved_for(sid)
        self.commit_files({resolved: checkpoint_script("ratified-cp")},
                          "pin the ratified oracle")
        source = self.write_source_bytes(crlf(checkpoint_script("other-cp")))

        result = self.flag_pack("clash", source)
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn(DIFFERING_BYTES_PHRASE,
                      result.stdout + result.stderr)
        self.assertEqual(self.open_sids(), [],
                         msg="the refusal is pre-sid: no session state")


class ReadmeCrlfPinTest(unittest.TestCase):
    """Pin: --readme-file's tolerance (today an accident of
    Path.read_text universal-newline translation) is contract. The
    shipped README is CR-free and the echoed sha256 is the LF-bytes
    hash, for a brief that traveled a mangling transport."""

    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory(prefix="bale-crlf-")
        self.tmp = Path(self._tmpdir.name)
        self.home = make_sandbox_home(self.tmp)
        self.install = make_install(self.tmp)
        self.repo = make_repo(self.tmp, self.home)
        self.env = bale_env(self.home, self.tmp)

    def tearDown(self) -> None:
        self._tmpdir.cleanup()

    def shipped_readme_bytes(self, sid: str) -> bytes:
        tb = self.repo / ".bale" / "outbox" / f"request-{sid}.tar.gz"
        self.assertTrue(tb.is_file(), msg=f"no outbox tarball at {tb}")
        nnn = sid.rsplit("-", 1)[-1]
        with tarfile.open(tb, "r:gz") as tf:
            member = tf.extractfile(f"request-{nnn}/README.md")
            self.assertIsNotNone(member, msg="tarball ships no README.md")
            return member.read()

    def test_crlf_brief_ships_lf_and_echoes_lf_hash(self) -> None:
        lf_body = ("# Brief — CRLF pin fixture\n"
                   "\n"
                   "Prose that crossed a mangling transport.\n")
        brief = self.tmp / "brief.md"
        brief.write_bytes(crlf(lf_body))

        result = run_bale(
            self.install,
            ["pack", "crlf readme pin goal", "--slug", "crlfreadme",
             "--include", "hello.txt", "--readme-file", str(brief),
             "--json"],
            cwd=self.repo, env=self.env,
        )
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        payload = json.loads(result.stdout.strip().splitlines()[-1])

        shipped = self.shipped_readme_bytes(payload["sid"])
        self.assertNotIn(b"\r", shipped,
                         msg="the shipped request README is CR-free")
        self.assertEqual(shipped, lf_body.encode("utf-8"),
                         msg="the shipped body is the LF twin, exact")
        self.assertEqual(
            payload["readme_sha256"],
            hashlib.sha256(lf_body.encode("utf-8")).hexdigest(),
            msg="the echoed sha256 is the LF-bytes hash")
        self.assertNotEqual(
            payload["readme_sha256"],
            hashlib.sha256(brief.read_bytes()).hexdigest(),
            msg="fixture sanity: the raw CRLF file hashes differently, "
                "so the assertion above actually pins normalization")


class ConfigCrlfPinTest(CheckpointFileFixture):
    """Pin: bale.toml's tolerance (the vendored TOML reader normalizes
    CRLF per spec, _bale_toml.py) is contract. A CRLF config drives a
    real pack — parsed [validation] base and all — clean."""

    def test_crlf_config_parses_and_resolves_the_base(self) -> None:
        # configure_base's exact content, CRLF on the wire.
        (self.repo / "bale.toml").write_bytes(
            crlf(f"[validation]\nbase = \"{CP_PATTERN}\"\n"))
        sid = self.predicted_sid("crlftoml")
        resolved = self.resolved_for(sid)
        self.commit_files({resolved: checkpoint_script("toml-cp")},
                          "pin the checkpoint the CRLF config points at")

        result = self.pack("crlftoml", "--include", "hello.txt")
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertEqual(self.open_sids(), [sid],
                         msg="the pack read the CRLF config, resolved "
                             "the {sid} base, and found the oracle — "
                             "config tolerance exercised end to end")


class BaleignoreCrlfPinTest(PackGuardsBase):
    """Pin: .baleignore's tolerance (read_text + splitlines today) is
    contract. CRLF pattern lines prune the walk exactly like their LF
    twins."""

    def test_crlf_patterns_prune_the_walk(self) -> None:
        self.write_payload({
            "payload/keep.py": "print()\n",
            "payload/drop.log": "log\n",
        })
        (self.repo / ".baleignore").write_bytes(crlf("*.log\n"))

        r = self.pack()
        self.assertEqual(r.returncode, 0,
                         msg=f"stdout:\n{r.stdout}\nstderr:\n{r.stderr}")
        included, members = self.shipped_context()
        self.assertEqual(
            included, ["context/.baleignore", "context/payload/keep.py"],
            msg="the CRLF pattern pruned drop.log and the file itself "
                "still ships")
        self.assertFalse(
            any(m.endswith("payload/drop.log") for m in members),
            msg=f"ignored file shipped anyway: {members}")


if __name__ == "__main__":
    unittest.main()
