#!/usr/bin/env python3
"""Hermetic E2E for the one-command checkpoint install (v0.4.10, revG).

Covers the bare-pack-oneshot Change C contract and its two riders —
the wizard checkpoint prompt and the pack-report identity echo —
against real pack runs (ADR-0002 oracle doctrine: observable state,
never golden comparisons):

- **The flag's happy path**: `bale pack --checkpoint-file <file>` on a
  `{sid}` base with no prior checkpoint succeeds in a single
  invocation; the file's bytes are committed at the resolved path as
  their own pathspec-limited commit on the current branch (subject
  naming the sid, other dirty work untouched), and the provenance
  stamp's path and sha256 match the file's bytes — the flag moves the
  planner's file into place before the resolved-existence pre-flight
  probes, so the two-run refusal loop never engages.
- **Idempotence and its refusal edge**: a resolved path already
  committed with identical bytes proceeds without a new commit (the
  re-run of an aborted pack); differing bytes refuse loudly — the flag
  never silently replaces a ratified oracle.
- **v1 scope refusals**: a literal base refuses (the planner commits
  the literal path directly), an unconfigured base refuses rather than
  ignoring the flag, and `--read-only` contradicts the flag at
  arg-parse time, before any prompt — the 0.4.9 waiver means there is
  nothing to install.
- **Read refusals**, mirroring `--readme-file`'s posture: a missing
  file and an empty file both refuse loudly, pre-sid.
- **Search-path resolution**: a bare filename resolves through
  `apply.search_paths` exactly like `--readme-file`, so a
  planner-downloaded checkpoint packs by name.
- **The identity echo** (evidence 45's class, applied to the strictly
  worse exposure — a stale oracle HOLDs a good session): the human
  summary rows and the `--json` keys `checkpoint_file_path` /
  `checkpoint_file_sha256` carry the resolved source path and the
  sha256 of the read bytes; both keys are null together on a
  flag-less pack (additive keys, uniform shape).
- **The wizard prompt** (pty, per the existing precedent): a bare
  scoped wizard walk under a `{sid}` base prompts for the checkpoint
  file and completes without a refusal; a read-only answer skips the
  prompt entirely; an empty answer falls through to the named
  resolved-existence refusal; a typed `--checkpoint-file` skips the
  prompt (the typed `--write` precedent, board-13a).

Sandbox doctrine per ADR-0005 (fully hermetic) — the shared harness in
``tests/harness.py`` carries it; the per-sid fixture base comes from
``tests/test_per_sid_checkpoint.py`` (its stated purpose).

Run directly::

    python3 tests/test_checkpoint_file_flag.py

or via ``python3 -m unittest discover -s tests``.
"""

from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from harness import run_bale_pty
from test_per_sid_checkpoint import (
    CP_PATTERN,
    FLAG_REMEDY_PHRASE,
    MISSING_RESOLVED_PHRASE,
    PerSidFixture,
    checkpoint_script,
)

# Sentinels for the surfaces this file pins (one place per message).
CONTRADICTION_PHRASE = "--checkpoint-file and --read-only are contradictory"
LITERAL_BASE_PHRASE = "per-session ({sid} bases) only"
UNCONFIGURED_PHRASE = "pins no [validation] base"
DIFFERING_BYTES_PHRASE = "refuses to replace the committed oracle"
IDEMPOTENT_PHRASE = "already committed with identical bytes"
EMPTY_FILE_PHRASE = "is empty"
PROMPT_MARKER = "Checkpoint file to commit for this session?"
COMMIT_SUBJECT_PREFIX = "bale: per-session checkpoint for "
ECHO_ROW_MARKER = "checkpoint file sha256:"


class CheckpointFileFixture(PerSidFixture):
    """PerSidFixture plus the flag-specific helpers: a source-file
    writer and a flag-carrying pack runner."""

    def write_source(self, body: str, name: str = "cp.sh") -> Path:
        """Write a planner's checkpoint file OUTSIDE the repo (the
        downloads-directory shape the search-path resolution serves)."""
        p = self.tmp / name
        p.write_text(body, encoding="utf-8")
        return p

    def flag_pack(self, slug: str, source: Path, *extra: str):
        return self.pack(slug, "--include", "hello.txt",
                         "--checkpoint-file", str(source), *extra)

    def resolved_for(self, sid: str) -> str:
        return f"claude/checkpoints/{sid}.sh"

    def head_bytes(self, rel: str) -> bytes:
        import subprocess
        r = subprocess.run(["git", "show", f"HEAD:{rel}"],
                           cwd=self.repo, capture_output=True)
        self.assertEqual(r.returncode, 0,
                         msg=f"expected {rel} committed at HEAD")
        return r.stdout

    def commit_subjects(self, rel: str) -> list:
        import subprocess
        r = subprocess.run(["git", "log", "--format=%s", "--", rel],
                           cwd=self.repo, capture_output=True, text=True)
        return [ln for ln in r.stdout.splitlines() if ln]


class CheckpointFileFlagTest(CheckpointFileFixture):
    """Change C proper: the commit-and-pack flag and its refusals."""

    def test_happy_path_commits_and_packs_in_one_run(self) -> None:
        """A {sid} base, no prior checkpoint, one invocation: the pack
        succeeds; the resolved path holds the file's bytes at HEAD as
        its own pathspec-limited commit (subject naming the sid, the
        dirty bale.toml untouched); the provenance stamp records the
        resolved path and the bytes' sha256."""
        self.configure_base(CP_PATTERN)
        body = checkpoint_script("oneshot-cp")
        source = self.write_source(body)
        sid = self.predicted_sid("oneshot")
        resolved = self.resolved_for(sid)

        result = self.flag_pack("oneshot", source)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertEqual(self.open_sids(), [sid])

        committed = self.head_bytes(resolved)
        self.assertEqual(committed, body.encode("utf-8"),
                         msg="the committed bytes are the file's, exact")
        subjects = self.commit_subjects(resolved)
        self.assertEqual(subjects, [f"{COMMIT_SUBJECT_PREFIX}{sid}"],
                         msg="one commit, its subject naming the sid")
        # Pathspec-limited: the uncommitted bale.toml stays uncommitted.
        import subprocess
        status = subprocess.run(["git", "status", "--porcelain"],
                                cwd=self.repo, capture_output=True,
                                text=True)
        self.assertIn("bale.toml", status.stdout,
                      msg="the checkpoint commit swept nothing else in")

        manifest = self.persisted_manifest(sid)
        self.assertEqual(manifest["provenance"]["checkpoint"], {
            "path": resolved,
            "sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        }, msg="the stamp records the resolved path and the file's "
               "bytes — install and stamp agree")

    def test_identical_bytes_rerun_is_idempotent(self) -> None:
        """The aborted-pack re-run: the resolved path already committed
        with identical bytes proceeds — logged as the idempotent
        branch, with no second commit for the path."""
        self.configure_base(CP_PATTERN)
        body = checkpoint_script("idem-cp")
        source = self.write_source(body)
        sid = self.predicted_sid("idem")
        resolved = self.resolved_for(sid)
        self.commit_files({resolved: body},
                          "pin the checkpoint (simulating the aborted "
                          "pack's leftover commit)")

        result = self.flag_pack("idem", source)
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertIn(IDEMPOTENT_PHRASE,
                      result.stdout + result.stderr)
        self.assertEqual(len(self.commit_subjects(resolved)), 1,
                         msg="no second commit for the path")
        self.assertEqual(self.open_sids(), [sid])

    def test_differing_bytes_refuse_loudly(self) -> None:
        """Committed-is-ratified: the flag never silently replaces a
        ratified oracle. Differing bytes refuse, naming both hashes and
        the deliberate-replacement remedy, pre-sid."""
        self.configure_base(CP_PATTERN)
        sid = self.predicted_sid("clash")
        resolved = self.resolved_for(sid)
        self.commit_files({resolved: checkpoint_script("ratified-cp")},
                          "pin the ratified oracle")
        source = self.write_source(checkpoint_script("different-cp"))

        result = self.flag_pack("clash", source)
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        combined = result.stdout + result.stderr
        self.assertIn(DIFFERING_BYTES_PHRASE, combined)
        self.assertIn(resolved, combined)
        self.assertEqual(self.open_sids(), [],
                         msg="the refusal is pre-sid: no session state")
        self.assertEqual(
            self.head_bytes(resolved),
            checkpoint_script("ratified-cp").encode("utf-8"),
            msg="the ratified oracle is untouched")

    def test_literal_base_refuses_with_direct_commit_remedy(self) -> None:
        """v1 scope is {sid} bases only: a literal base refuses,
        naming the commit-the-literal-path-directly remedy."""
        self.configure_base("scripts/validation.base.sh")
        self.commit_files(
            {"scripts/validation.base.sh": checkpoint_script("lit")},
            "pin literal oracle")
        source = self.write_source(checkpoint_script("flag-cp"))

        result = self.flag_pack("literal", source)
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        combined = result.stdout + result.stderr
        self.assertIn(LITERAL_BASE_PHRASE, combined)
        self.assertIn("scripts/validation.base.sh", combined,
                      msg="the refusal names the literal path to "
                          "commit directly")
        self.assertEqual(self.open_sids(), [])

    def test_unconfigured_base_refuses_never_ignores(self) -> None:
        """No [validation] base: the flag refuses rather than being
        silently ignored — an oracle nothing reads must not look
        installed."""
        source = self.write_source(checkpoint_script("orphan-cp"))
        result = self.flag_pack("orphan", source)
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn(UNCONFIGURED_PHRASE,
                      result.stdout + result.stderr)
        self.assertEqual(self.open_sids(), [])

    def test_read_only_contradiction_at_arg_parse(self) -> None:
        """--read-only + --checkpoint-file refuse as contradictory at
        the fail-fast flag-validation site — before any prompt, before
        the file is even read (a doomed combination costs zero
        keystrokes)."""
        self.configure_base(CP_PATTERN)
        # Deliberately a nonexistent source: the contradiction fires
        # before the read, so no not-found error may surface instead.
        result = self.flag_pack("contra", self.tmp / "never-written.sh",
                                "--read-only")
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        combined = result.stdout + result.stderr
        self.assertIn(CONTRADICTION_PHRASE, combined)
        self.assertNotIn("not found", combined,
                         msg="the contradiction precedes the file read")
        self.assertEqual(self.open_sids(), [])

    def test_missing_file_refuses_loudly(self) -> None:
        """A missing source refuses loudly, mirroring --readme-file's
        posture, pre-sid."""
        self.configure_base(CP_PATTERN)
        result = self.flag_pack("missing", self.tmp / "no-such-file.sh")
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        self.assertIn("could not read --checkpoint-file",
                      result.stdout + result.stderr)
        self.assertEqual(self.open_sids(), [])

    def test_empty_file_refuses_loudly(self) -> None:
        """An empty source refuses loudly — an upstream failure, never
        a silent omit; deliberate omission is spelled 'drop the
        flag'."""
        self.configure_base(CP_PATTERN)
        source = self.write_source("")
        result = self.flag_pack("empty", source)
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        combined = result.stdout + result.stderr
        self.assertIn("--checkpoint-file", combined)
        self.assertIn(EMPTY_FILE_PHRASE, combined)
        self.assertEqual(self.open_sids(), [])

    def test_bare_name_resolves_through_search_paths(self) -> None:
        """A bare filename resolves through apply.search_paths exactly
        like --readme-file — the planner's downloads directory works by
        name."""
        inbox = self.tmp / "inbox"
        inbox.mkdir()
        body = checkpoint_script("inbox-cp")
        (inbox / "session-cp.sh").write_text(body, encoding="utf-8")
        (self.repo / "bale.toml").write_text(
            f"[validation]\nbase = \"{CP_PATTERN}\"\n\n"
            f"[apply]\nsearch_paths = [\"{inbox}\"]\n",
            encoding="utf-8")
        sid = self.predicted_sid("inbox")

        result = self.pack("inbox", "--include", "hello.txt",
                           "--checkpoint-file", "session-cp.sh")
        self.assertEqual(
            result.returncode, 0,
            msg=f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}")
        self.assertEqual(self.head_bytes(self.resolved_for(sid)),
                         body.encode("utf-8"))

    def test_flagless_refusal_names_the_flag_first(self) -> None:
        """The flag's own suite pins the refusal-text half of Change C
        too: a flag-less scoped pack under a {sid} base with no
        committed checkpoint refuses naming --checkpoint-file as the
        primary remedy (the ordering and planner-attribution details
        are test_per_sid_checkpoint.py's assertions)."""
        self.configure_base(CP_PATTERN)
        result = self.pack("flagless", "--include", "hello.txt")
        self.assertNotEqual(result.returncode, 0, msg=result.stdout)
        combined = result.stdout + result.stderr
        self.assertIn(MISSING_RESOLVED_PHRASE, combined)
        self.assertIn(FLAG_REMEDY_PHRASE, combined)


class CheckpointIdentityEchoTest(CheckpointFileFixture):
    """The pack-report identity echo: human rows and --json keys."""

    def test_summary_echoes_source_path_and_sha256(self) -> None:
        self.configure_base(CP_PATTERN)
        body = checkpoint_script("echo-cp")
        source = self.write_source(body)
        result = self.flag_pack("echo", source)
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        self.assertIn(str(source), result.stdout,
                      msg="the resolved source path is the identity "
                          "the search-path resolution made ambiguous")
        self.assertIn(hashlib.sha256(body.encode("utf-8")).hexdigest(),
                      result.stdout,
                      msg="the echoed sha256 is the read bytes' — and "
                          "by the install contract, the committed "
                          "blob's and the stamp's")

    def test_json_carries_identity_keys(self) -> None:
        self.configure_base(CP_PATTERN)
        body = checkpoint_script("json-cp")
        source = self.write_source(body)
        result = self.flag_pack("jsonecho", source, "--json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertEqual(payload["checkpoint_file_path"], str(source))
        self.assertEqual(
            payload["checkpoint_file_sha256"],
            hashlib.sha256(body.encode("utf-8")).hexdigest())
        # The stamp agrees — one identity across echo and provenance.
        manifest = self.persisted_manifest(payload["sid"])
        self.assertEqual(manifest["provenance"]["checkpoint"]["sha256"],
                         payload["checkpoint_file_sha256"])

    def test_json_keys_null_together_without_the_flag(self) -> None:
        """Additive keys, uniform shape: a flag-less pack carries both
        keys, null together."""
        # No base configured: a plain pack with no checkpoint at all.
        result = self.pack("plain", "--include", "hello.txt", "--json")
        self.assertEqual(result.returncode, 0, msg=result.stderr)
        payload = json.loads(result.stdout.strip().splitlines()[-1])
        self.assertIn("checkpoint_file_path", payload)
        self.assertIn("checkpoint_file_sha256", payload)
        self.assertIsNone(payload["checkpoint_file_path"])
        self.assertIsNone(payload["checkpoint_file_sha256"])
        # And the human report ships no echo rows.
        self.assertNotIn(ECHO_ROW_MARKER, result.stdout)


class CheckpointWizardPromptTest(CheckpointFileFixture):
    """The wizard half (ratified 2026-08-13, sitting chat), driven
    through a real pty like the forecast-prompt suite."""

    def wizard_pack(self, answers: str, *extra: str):
        return run_bale_pty(
            self.install, ["pack", *extra],
            cwd=self.repo, env=self.env, answers=answers)

    def test_bare_scoped_walk_prompts_and_completes(self) -> None:
        """The ratified happy path: a bare wizard pack in a {sid}-based
        project prompts for the checkpoint file and completes without a
        refusal — no two-run loop."""
        self.configure_base(CP_PATTERN)
        body = checkpoint_script("wiz-cp")
        source = self.write_source(body)
        sid = self.predicted_sid("wiz-happy")
        answers = (
            "wizard checkpoint happy goal\n"   # goal
            "wiz-happy\n"                      # slug
            "c\n"                              # session shape: code
            "\n"                               # forecast: Enter
            f"{source}\n"                      # checkpoint file
            "\n" "\n" "\n"                     # excludes, constraints, oos
            "n\n"                              # README prompt: no
        )
        code, output = self.wizard_pack(answers)
        self.assertEqual(code, 0, msg=output)
        self.assertIn(PROMPT_MARKER, output)
        self.assertEqual(self.open_sids(), [sid])
        self.assertEqual(self.head_bytes(self.resolved_for(sid)),
                         body.encode("utf-8"))

    def test_read_only_answer_skips_the_prompt(self) -> None:
        """The [r] answer rides the 0.4.9 waiver: nothing to install,
        so the prompt never appears and the pack completes."""
        self.configure_base(CP_PATTERN)
        answers = (
            "wizard checkpoint read-only goal\n"
            "wiz-ro\n"
            "r\n"                              # session shape: read-only
            "\n" "\n" "\n"
            "n\n"
        )
        code, output = self.wizard_pack(answers)
        self.assertEqual(code, 0, msg=output)
        self.assertNotIn(PROMPT_MARKER, output)
        self.assertEqual(self.scope_json_of_only_session(), [])

    def test_empty_answer_reaches_the_named_refusal(self) -> None:
        """An empty answer is the operator declining: the pack falls
        through to the resolved-existence refusal — loud, with the
        --checkpoint-file remedy — and no session state exists."""
        self.configure_base(CP_PATTERN)
        answers = (
            "wizard checkpoint decline goal\n"
            "wiz-decline\n"
            "c\n"
            "\n"                               # forecast: Enter
            "\n"                               # checkpoint file: Enter
            "\n" "\n" "\n"
            "n\n"
        )
        code, output = self.wizard_pack(answers)
        self.assertNotEqual(code, 0, msg=output)
        self.assertIn(PROMPT_MARKER, output)
        self.assertIn(MISSING_RESOLVED_PHRASE, output)
        self.assertIn(FLAG_REMEDY_PHRASE, output)
        self.assertEqual(self.open_sids(), [])

    def test_typed_flag_skips_the_prompt(self) -> None:
        """The typed --write precedent (board-13a): a typed
        --checkpoint-file answers the question, so the wizard never
        asks it — and the install still runs."""
        self.configure_base(CP_PATTERN)
        body = checkpoint_script("wiz-typed-cp")
        source = self.write_source(body)
        sid = self.predicted_sid("wiz-typed")
        answers = (
            "wizard checkpoint typed goal\n"
            "wiz-typed\n"
            "c\n"
            "\n"                               # forecast: Enter
            "\n" "\n" "\n"
            "n\n"
        )
        code, output = self.wizard_pack(
            answers, "--checkpoint-file", str(source))
        self.assertEqual(code, 0, msg=output)
        self.assertNotIn(PROMPT_MARKER, output)
        self.assertEqual(self.head_bytes(self.resolved_for(sid)),
                         body.encode("utf-8"))

    def test_nonresolving_answer_reprompts(self) -> None:
        """A miss re-prompts interactively rather than failing the
        whole pack after the answers are in — the forecast prompt's
        posture."""
        self.configure_base(CP_PATTERN)
        body = checkpoint_script("wiz-retry-cp")
        source = self.write_source(body)
        answers = (
            "wizard checkpoint reprompt goal\n"
            "wiz-retry\n"
            "c\n"
            "\n"
            "no-such-file.sh\n"                # checkpoint: miss, re-ask
            f"{source}\n"                      # checkpoint: accepted
            "\n" "\n" "\n"
            "n\n"
        )
        code, output = self.wizard_pack(answers)
        self.assertEqual(code, 0, msg=output)
        self.assertIn("could not read --checkpoint-file", output)
        sid = self.predicted_sid("wiz-retry")
        self.assertEqual(self.head_bytes(self.resolved_for(sid)),
                         body.encode("utf-8"))

    # -- fixture ---------------------------------------------------------

    def scope_json_of_only_session(self) -> list:
        sids = self.open_sids()
        self.assertEqual(len(sids), 1)
        p = (self.repo / ".bale" / "sessions" / sids[0] / "scope.json")
        self.assertTrue(p.is_file(), msg=f"expected scope record {p}")
        return json.loads(p.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
