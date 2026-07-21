#!/usr/bin/env python3
"""response_lint.py — mechanical self-check for a bale response directory.

A WORKER runs this against its own response-NNN/ directory before
packing, without bale installed. It executes the TARBALL.md §10.1
step-10 self-check as code instead of discipline, and it is the tool
that catches compaction-corrupted manifests at the source (CLAUDE.md
§11.6's re-derivation duty, mechanized).

Checks are authored from the DOCUMENTED contract — TARBALL.md §5.2,
§5.2.1, §5.3, §5.6.1, §5.9.2, §10.1 — and the two schema files under
schemas/, NOT from bale_validate. This is a deliberately independent
second implementation of the written contract (ADR-0002's rejection
of the self-oracle, applied to pre-pack linting).

Usage:
    response_lint.py <response-dir> [--json] [--schema-dir DIR]

Exit codes:
    0  clean — every check passed
    1  findings — at least one contract violation, all of them named
    2  the lint itself errored (bad usage, unreadable dir)

Output:
    Default: human-readable report on stdout, every failure named
    with path, expected, and got — never first-failure-only.
    --json:  one JSON line on stdout (stable keys for an orchestrator);
    the human-readable findings move to stderr.

Schemas:
    Verbatim copies of schemas/response-manifest.schema.json and
    schemas/diagnostics.schema.json are embedded below so the file is
    standalone. If the project's schema files evolve, refresh the
    embedded copies (they are JSON-equal to the source files), or
    point --schema-dir at a directory containing the two files to
    override the embedded copies at runtime. validate.sh asserts the
    JSON-equality on every run, so a schema edit that forgets the
    refresh fails install validation loudly rather than drifting.

Stdlib only. Python 3.10+. No network. No bale imports.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

EXIT_CLEAN = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2

VALID_KINDS = ("normal", "bailout", "clarification")

# ---------------------------------------------------------------------------
# Embedded schemas — verbatim copies of the files named in the header.
# ---------------------------------------------------------------------------

RESPONSE_MANIFEST_SCHEMA_JSON = r"""
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/anthropics/bale/schemas/response-manifest.schema.json",
  "title": "bale response manifest",
  "description": "Shape of response-NNN/manifest.json per TARBALL.md sections 5.2, 5.6.2, and 5.9.2. Field semantics live in TARBALL.md; this schema constrains only the universal envelope. Cross-field invariants (sha256 file match, path-safety, claims subset of validation_will_run, stripped-non-empty reasons, bailout-shape and clarification-shape rules) stay in bale's Python validators.",
  "type": "object",
  "additionalProperties": false,
  "required": [
    "session_id",
    "responds_to",
    "corrects",
    "summary",
    "changes",
    "deferred",
    "validation_will_run",
    "claims"
  ],
  "properties": {
    "session_id": {
      "type": "string",
      "minLength": 1,
      "description": "YYYY-MM-DD-<slug>-NNN per TARBALL.md section 1. For a normal response this equals responds_to; for a bailout it equals responds_to too, since the bailout is the answer to the same request; and for a clarification as well, since a clarification suspends rather than consumes its session (TARBALL.md section 5.9) and carries the same sid the eventual normal response will."
    },
    "responds_to": {
      "type": "string",
      "minLength": 1,
      "description": "Session ID of the request this response answers. Bale verifies it matches the locked session."
    },
    "corrects": {
      "type": ["string", "null"],
      "description": "Session ID of a prior response this re-attempts, or null."
    },
    "response_kind": {
      "type": "string",
      "enum": ["normal", "bailout", "clarification"],
      "description": "Optional, defaults to 'normal' if absent so v0.0.5-shaped manifests pass through. 'bailout' triggers TARBALL.md section 5.6's distinct shape; 'clarification' triggers section 5.9's (both enforced in Python)."
    },
    "summary": {
      "type": "string",
      "minLength": 1,
      "description": "One paragraph: what this response delivers."
    },
    "changes": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["path", "action", "reason", "size_bytes", "sha256"],
        "properties": {
          "path": {
            "type": "string",
            "minLength": 1,
            "description": "Repo-relative path. Path-safety (no traversal, no .git/.bale, no .baleignore match) is enforced in Python."
          },
          "action": {
            "type": "string",
            "enum": ["created", "modified", "deleted"]
          },
          "reason": {
            "type": "string",
            "minLength": 1,
            "description": "Non-empty. The stripped-non-empty rule is enforced in Python; this schema only catches the empty-string case."
          },
          "size_bytes": {
            "type": "integer",
            "minimum": 0
          },
          "sha256": {
            "type": ["string", "null"],
            "description": "Required string for created/modified; required null for deleted. The conditional rule is enforced in Python — this schema admits either."
          }
        }
      }
    },
    "deferred": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["what", "why"],
        "properties": {
          "what": { "type": "string", "minLength": 1 },
          "why":  { "type": "string", "minLength": 1 }
        }
      }
    },
    "validation_will_run": {
      "type": "array",
      "items": { "type": "string", "minLength": 1 },
      "description": "Declarative list of what validation.sh is configured to do. Strings are freeform — they're labels the user reads, not commands bale invokes."
    },
    "claims": {
      "type": "object",
      "description": "Claude's predictions for each project-level check. Keys are freeform check names (must be a subset of validation_will_run; enforced in Python). Values are constrained to the enum.",
      "additionalProperties": {
        "type": "string",
        "enum": ["pass", "fail", "untested", "unknown"]
      }
    },
    "questions": {
      "type": "array",
      "description": "Blocking intent-gap questions per TARBALL.md section 5.9.2. Required and non-empty when response_kind='clarification'; on every other kind the block is absent or an EMPTY array (an empty array is tolerated, matching the doc's 'Forbidden (or empty)' wording — the doc is the contract of record; the conditional rule is enforced in Python — this schema only constrains entry shape).",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["question", "context", "default_assumption", "why_blocked"],
        "properties": {
          "question": {
            "type": "string",
            "minLength": 1,
            "description": "The question itself, stated so it can be answered in one short paragraph or less."
          },
          "context": {
            "type": "string",
            "minLength": 1,
            "description": "What the worker was trying to do when it hit the gap."
          },
          "default_assumption": {
            "type": "string",
            "minLength": 1,
            "description": "What the worker would have assumed absent an answer. Load-bearing: lets the planner answer with a single 'your assumption is correct'."
          },
          "why_blocked": {
            "type": "string",
            "minLength": 1,
            "description": "Why the worker declined to proceed on that assumption."
          }
        }
      }
    },
    "feedback": {
      "type": "object",
      "additionalProperties": false,
      "required": ["mechanical", "self_reported"],
      "description": "Dual-stream session feedback (v0.3.8+, session B1). Optional so pre-B1 manifests validate; apply persists the block verbatim (the B2 telemetry record builds on it). Two streams by trust level: 'mechanical' holds values the lint (tools/response_lint.py) can recompute and verify; 'self_reported' holds worker-authored judgment the lint cannot check.",
      "properties": {
        "mechanical": {
          "type": "object",
          "additionalProperties": false,
          "required": ["response_kind", "schema_valid", "mirror_agreement", "claims_subset"],
          "description": "Lint-computable results. The worker fills these by running the lint; the lint's feedback-block check recomputes each and flags any disagreement — a mismatch is the tell of a hand-filled or stale block.",
          "properties": {
            "response_kind": {
              "type": "string",
              "enum": ["normal", "bailout", "clarification"],
              "description": "Echo of the manifest's effective response_kind (defaulted 'normal' when the top-level key is absent)."
            },
            "schema_valid": {
              "type": "boolean",
              "description": "Whether the manifest validates against this schema, as found by the lint's manifest-schema check."
            },
            "mirror_agreement": {
              "type": "object",
              "additionalProperties": false,
              "required": ["changes_to_files", "files_to_changes"],
              "description": "The TARBALL.md section 10.1 both-directions mirror result, split by direction.",
              "properties": {
                "changes_to_files": {
                  "type": "boolean",
                  "description": "Every created/modified entry has its files/ member with matching size and recomputed sha256; deleted entries follow the section 5.2 shape. Vacuously true on kinds that ship no files/."
                },
                "files_to_changes": {
                  "type": "boolean",
                  "description": "Nothing under files/ is undeclared in changes[]. Vacuously true on kinds that ship no files/."
                }
              }
            },
            "claims_subset": {
              "type": "boolean",
              "description": "set(claims) is a verbatim subset of validation_will_run (TARBALL.md section 5.3)."
            },
            "linkage": {
              "type": ["object", "null"],
              "additionalProperties": false,
              "required": ["kind", "point"],
              "description": "Present when the session went through a probe or clarification round on the way to this response; null or absent otherwise. Self-reported placement data riding in mechanical because its shape is fixed even though the lint cannot verify it.",
              "properties": {
                "kind": {
                  "type": "string",
                  "enum": ["probe", "clarification"],
                  "description": "Which recourse the session used (TARBALL.md section 5.9's taxonomy)."
                },
                "point": {
                  "type": "string",
                  "enum": ["pre-read", "pre-build", "mid-build"],
                  "description": "When in the session the gap surfaced: before any triggered drill-down reading, after reading but before building, or mid-build."
                },
                "depends_on": {
                  "type": ["string", "null"],
                  "description": "Session ID of the linked round when it exists as a durable artifact (a file-based probe or a shipped clarification response); null for a paste-back probe or an in-chat ask, which resolve within the session (TARBALL.md sections 4.5, 5.9.1)."
                }
              }
            },
            "provenance": {
              "type": ["object", "null"],
              "additionalProperties": false,
              "required": ["bale_version", "contract_docs", "packer", "work_class", "model_identity"],
              "description": "The request manifest's provenance block echoed verbatim, plus model_identity. Null when the request carried no provenance (packed by a pre-0.3.8 bale — the one-apply-behind bootstrap case).",
              "properties": {
                "bale_version": { "type": "string", "minLength": 1 },
                "contract_docs": {
                  "type": "object",
                  "additionalProperties": false,
                  "required": ["CLAUDE.md", "TARBALL.md", "DOCS.md", "CODE.md"],
                  "properties": {
                    "CLAUDE.md":  { "type": "string", "minLength": 1 },
                    "TARBALL.md": { "type": "string", "minLength": 1 },
                    "DOCS.md":    { "type": "string", "minLength": 1 },
                    "CODE.md":    { "type": "string", "minLength": 1 }
                  }
                },
                "packer": { "type": "string", "minLength": 1 },
                "work_class": {
                  "type": "string",
                  "enum": ["code", "doc", "contract-doc", "meta", "mixed"]
                },
                "model_identity": {
                  "type": "string",
                  "minLength": 1,
                  "description": "SELF-REPORTED AND UNVERIFIABLE TODAY: the worker states its own model identity; no mechanism attests it. Recorded for longitudinal aggregation, read with that caveat."
                }
              }
            }
          }
        },
        "self_reported": {
          "type": "object",
          "additionalProperties": false,
          "required": ["assumptions", "judgment_calls", "budget_pressure", "includes_missing", "compaction_occurred"],
          "description": "Worker-authored stream. Honest empties are meaningful ([] = none arose); the lint checks shape only, never content.",
          "properties": {
            "assumptions": {
              "type": "array",
              "items": { "type": "string", "minLength": 1 },
              "description": "Assumptions the session proceeded on without confirmation (the recoverable-risk posture of TARBALL.md section 3.3 / 5.9.1), one per entry."
            },
            "judgment_calls": {
              "type": "array",
              "items": { "type": "string", "minLength": 1 },
              "description": "Decisions the worker made that the planner should be able to find without reading the diff — design choices, tie-breaks, interpretations."
            },
            "budget_pressure": {
              "type": "string",
              "enum": ["none", "tight", "bailed"],
              "description": "The session's own read of its context budget: comfortable throughout, felt the CLAUDE.md section 11.3 pressure without bailing, or this response is a bailout."
            },
            "includes_missing": {
              "type": "array",
              "items": { "type": "string", "minLength": 1 },
              "description": "Files or docs the session wanted but the request did not include — packing signal for the planner, one path or description per entry."
            },
            "compaction_occurred": {
              "type": "object",
              "additionalProperties": false,
              "required": ["occurred"],
              "description": "Whether the runtime compacted mid-session (CLAUDE.md section 11.6). When true, disclosure_ref points at where the disclosure lives.",
              "properties": {
                "occurred": { "type": "boolean" },
                "disclosure_ref": {
                  "type": ["string", "null"],
                  "description": "Where the compaction disclosure was recorded (e.g. 'notes.md' or a chat pointer); null when occurred is false."
                }
              }
            }
          }
        }
      }
    }
  }
}
"""

DIAGNOSTICS_SCHEMA_JSON = r"""
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "https://github.com/anthropics/bale/schemas/diagnostics.schema.json",
  "title": "bale bailout diagnostics",
  "description": "Shape of response-NNN/diagnostics.json (bailout responses only) per TARBALL.md section 5.8. INTENTIONALLY LOOSE: additionalProperties is true at the top level so future fields can be added without breaking earlier aggregation across sessions. The required keys below are the universal envelope; the values inside (tool_calls_summary keys, what_would_save_next_time strings) are deliberately freeform.",
  "type": "object",
  "additionalProperties": true,
  "required": [
    "session_id",
    "bail_trigger",
    "bail_narrative",
    "context_loaded",
    "exploration_paths",
    "tool_calls_summary",
    "what_would_save_next_time"
  ],
  "properties": {
    "session_id": {
      "type": "string",
      "minLength": 1,
      "description": "The bailing session's ID. Matches the manifest's session_id field."
    },
    "bail_trigger": {
      "type": "string",
      "enum": [
        "reading-path-inflation",
        "mid-build-budget-panic",
        "other"
      ],
      "description": "Per CLAUDE.md section 11.2. The first two are Claude-detected; 'other' covers architect-requested bailouts with specifics in bail_narrative."
    },
    "bail_narrative": {
      "type": "string",
      "minLength": 1,
      "description": "One paragraph: what was noticed, when, why bailing beat pushing through. Searchable across sessions when bail_trigger's enum is too coarse."
    },
    "context_loaded": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": true,
        "required": ["path", "verdict", "note"],
        "properties": {
          "path": { "type": "string", "minLength": 1 },
          "verdict": {
            "type": "string",
            "enum": ["necessary", "wasted", "partial"]
          },
          "note": { "type": "string" }
        }
      }
    },
    "exploration_paths": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": true,
        "required": ["what", "verdict", "note"],
        "properties": {
          "what": { "type": "string", "minLength": 1 },
          "verdict": {
            "type": "string",
            "enum": ["productive", "dead_end", "inconclusive"]
          },
          "note": { "type": "string" }
        }
      }
    },
    "tool_calls_summary": {
      "type": "object",
      "description": "Map of tool name to call count. Keys are freeform tool names; values are non-negative counts.",
      "additionalProperties": {
        "type": "integer",
        "minimum": 0
      }
    },
    "what_would_save_next_time": {
      "type": "array",
      "items": { "type": "string", "minLength": 1 },
      "description": "Concrete prescriptions for the next session. Overlaps with handoff.md's 'What I learned' by design."
    }
  }
}
"""


# ---------------------------------------------------------------------------
# Minimal JSON-Schema validator.
#
# Implements exactly the keyword subset the two schemas above use:
#   type (string or list), required, properties, additionalProperties
#   (boolean or schema), enum, minLength, minimum, items.
# Collects every violation rather than stopping at the first, matching
# the lint's never-first-failure-only output contract.
# ---------------------------------------------------------------------------

def _type_matches(value, type_name: str) -> bool:
    """True when value matches a JSON-Schema primitive type name.

    bool is a subclass of int in Python, so 'integer' and 'number'
    explicitly exclude it — JSON booleans are not JSON numbers.
    """
    if type_name == "object":
        return isinstance(value, dict)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "null":
        return value is None
    return False  # unknown type name in schema: treat as non-match, loudly wrong


def _json_type_name(value) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if value is None:
        return "null"
    return type(value).__name__


def schema_validate(instance, schema: dict, loc: str = "$") -> list[str]:
    """Validate instance against the supported schema subset.

    Returns a list of human-readable violation strings ("<loc>: <what>");
    empty list means valid. Never raises on instance content.
    """
    errors: list[str] = []
    _schema_walk(instance, schema, loc, errors)
    return errors


def _schema_walk(instance, schema: dict, loc: str, errors: list[str]) -> None:
    # -- type --
    declared = schema.get("type")
    if declared is not None:
        allowed = declared if isinstance(declared, list) else [declared]
        if not any(_type_matches(instance, t) for t in allowed):
            errors.append(
                f"{loc}: expected type {' or '.join(allowed)}, "
                f"got {_json_type_name(instance)}"
            )
            return  # deeper keywords assume the right type; stop this branch

    # -- enum --
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(
            f"{loc}: value {json.dumps(instance)} not in enum "
            f"{json.dumps(schema['enum'])}"
        )

    # -- string keywords --
    if isinstance(instance, str) and "minLength" in schema:
        if len(instance) < schema["minLength"]:
            errors.append(
                f"{loc}: string shorter than minLength "
                f"{schema['minLength']} (got length {len(instance)})"
            )

    # -- numeric keywords --
    if isinstance(instance, (int, float)) and not isinstance(instance, bool):
        if "minimum" in schema and instance < schema["minimum"]:
            errors.append(
                f"{loc}: {instance} below minimum {schema['minimum']}"
            )

    # -- object keywords --
    if isinstance(instance, dict):
        props = schema.get("properties", {})
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{loc}: missing required property '{key}'")
        addl = schema.get("additionalProperties", True)
        for key, value in instance.items():
            child_loc = f"{loc}.{key}"
            if key in props:
                _schema_walk(value, props[key], child_loc, errors)
            elif addl is False:
                errors.append(f"{loc}: additional property '{key}' not allowed")
            elif isinstance(addl, dict):
                _schema_walk(value, addl, child_loc, errors)
            # addl is True: unconstrained, accept

    # -- array keywords --
    if isinstance(instance, list) and "items" in schema:
        for i, item in enumerate(instance):
            _schema_walk(item, schema["items"], f"{loc}[{i}]", errors)


# ---------------------------------------------------------------------------
# Findings
# ---------------------------------------------------------------------------

def finding(code: str, path, expected, got, message: str) -> dict:
    """One named failure: stable code + path + expected + got + prose."""
    return {
        "code": code,
        "path": str(path),
        "expected": expected,
        "got": got,
        "message": message,
    }


def _sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def _is_unsafe_relpath(path_str: str) -> bool:
    """True when a changes[].path can't be safely joined under files/.

    Full path-safety (.git/.bale exclusion, .baleignore) is bale's
    pre-flight job; this lint rejects only what would make its own
    mirror lookup dangerous or meaningless.
    """
    if path_str.startswith("/") or path_str.startswith("\\"):
        return True
    parts = path_str.replace("\\", "/").split("/")
    return ".." in parts or "" == path_str


def _list_mirror_files(files_root: Path) -> list[str]:
    if not files_root.is_dir():
        return []
    return sorted(
        p.relative_to(files_root).as_posix()
        for p in files_root.rglob("*")
        if p.is_file()
    )


# ---------------------------------------------------------------------------
# Checks. Each takes the shared context dict and returns a findings list.
#
# The registry at the bottom of this section is the extension surface:
# session B (feedback block, provenance stamping) adds rows here, it
# does not rewrite the runner.
# ---------------------------------------------------------------------------

def check_manifest_parse(ctx: dict) -> list[dict]:
    """manifest.json exists and parses as JSON (TARBALL.md §5.1: required)."""
    rdir: Path = ctx["rdir"]
    mpath = rdir / "manifest.json"
    if not mpath.is_file():
        return [finding(
            "MANIFEST_MISSING", "manifest.json",
            "manifest.json present in the response directory", "absent",
            "TARBALL.md section 5.1 lists manifest.json as required",
        )]
    try:
        ctx["manifest"] = json.loads(mpath.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [finding(
            "MANIFEST_UNPARSEABLE", "manifest.json",
            "valid UTF-8 JSON", f"parse error: {exc}",
            "manifest.json did not parse; every downstream check is skipped",
        )]
    if not isinstance(ctx["manifest"], dict):
        got = _json_type_name(ctx["manifest"])
        ctx["manifest"] = None
        return [finding(
            "MANIFEST_UNPARSEABLE", "manifest.json",
            "a JSON object at the top level", got,
            "manifest.json parsed but is not an object; downstream checks skipped",
        )]
    return []


def check_manifest_schema(ctx: dict) -> list[dict]:
    """Manifest validates against response-manifest.schema.json."""
    manifest = ctx["manifest"]
    out = []
    for err in schema_validate(manifest, ctx["manifest_schema"]):
        loc, _, what = err.partition(": ")
        out.append(finding(
            "SCHEMA_VIOLATION", f"manifest.json:{loc}",
            "conformance to response-manifest.schema.json", what,
            f"schema violation at {loc}: {what}",
        ))
    kind = manifest.get("response_kind", "normal")
    ctx["kind"] = kind if kind in VALID_KINDS else None  # enum error already filed
    return out


def check_required_artifacts(ctx: dict) -> list[dict]:
    """apply.sh and validation.sh exist (§5.1: required on every kind)."""
    out = []
    for name in ("apply.sh", "validation.sh"):
        if not (ctx["rdir"] / name).is_file():
            out.append(finding(
                "ARTIFACT_MISSING", name,
                f"{name} present (a no-op script when there is nothing to do)",
                "absent",
                f"TARBALL.md section 5.1 lists {name} as required for every "
                "response kind, including bailout (5.6.1) and clarification (5.9.2)",
            ))
    return out


def check_changes_mirror(ctx: dict) -> list[dict]:
    """changes[] <-> files/ correspondence, both directions, hashes recomputed.

    Covers TARBALL.md §5.2 (field rules per action), §5.2.1 (computed,
    never transcribed — the lint recomputes from bytes and never trusts
    the manifest), and §10.1's both-directions mirror bullet. Runs for
    the normal kind only; bailout/clarification file surfaces belong to
    check_kind_shape.
    """
    if ctx["kind"] != "normal":
        return []
    manifest = ctx["manifest"]
    changes = manifest.get("changes")
    if not isinstance(changes, list):
        return []  # schema check already filed the type violation
    rdir: Path = ctx["rdir"]
    files_root = rdir / "files"
    out: list[dict] = []

    entries = [c for c in changes if isinstance(c, dict)]

    # Duplicate paths make the mirror correspondence ambiguous.
    dupes = [p for p, n in Counter(
        c.get("path") for c in entries if isinstance(c.get("path"), str)
    ).items() if n > 1]
    for p in sorted(dupes):
        out.append(finding(
            "DUPLICATE_PATH", p,
            "each path appearing in changes[] at most once", f"{p} appears more than once",
            "duplicate changes[] entries make the files/ <-> changes[] "
            "correspondence of section 10.1 ambiguous",
        ))

    declared_present: set[str] = set()   # created/modified paths
    declared_deleted: set[str] = set()

    for i, ch in enumerate(entries):
        path_str = ch.get("path")
        action = ch.get("action")
        if not isinstance(path_str, str) or action not in ("created", "modified", "deleted"):
            continue  # schema check already filed these
        if _is_unsafe_relpath(path_str):
            out.append(finding(
                "PATH_UNSAFE", path_str,
                "a repo-relative path with no traversal", path_str,
                f"changes[{i}].path cannot be safely resolved under files/; "
                "full path-safety remains bale's pre-flight, but the mirror "
                "check needs a joinable path",
            ))
            continue

        if action == "deleted":
            declared_deleted.add(path_str)
            # §5.2: deleted entries have size_bytes 0, sha256 null, no files/ member.
            if (files_root / path_str).exists():
                out.append(finding(
                    "DELETED_IN_FILES", path_str,
                    "no files/ entry for a deleted path (removal happens in apply.sh)",
                    f"files/{path_str} exists",
                    f"changes[{i}] is action=deleted but the path is present "
                    "under files/ (TARBALL.md section 5.2)",
                ))
            if ch.get("size_bytes") != 0:
                out.append(finding(
                    "DELETED_SIZE_NONZERO", path_str,
                    "size_bytes: 0", repr(ch.get("size_bytes")),
                    f"changes[{i}] is action=deleted; section 5.2 fixes "
                    "size_bytes at 0",
                ))
            if ch.get("sha256") is not None:
                out.append(finding(
                    "DELETED_SHA_NOT_NULL", path_str,
                    "sha256: null", repr(ch.get("sha256")),
                    f"changes[{i}] is action=deleted; section 5.2 fixes "
                    "sha256 at null",
                ))
            continue

        # created / modified
        declared_present.add(path_str)
        fpath = files_root / path_str
        if not fpath.is_file():
            out.append(finding(
                "MIRROR_MISSING", path_str,
                f"files/{path_str} present", "absent",
                f"changes[{i}] declares action={action} but the files/ "
                "mirror has no such file (section 10.1, declared-but-absent)",
            ))
            continue
        if not isinstance(ch.get("sha256"), str):
            out.append(finding(
                "SHA256_NOT_STRING", path_str,
                "a sha256 hex string for created/modified entries",
                repr(ch.get("sha256")),
                f"changes[{i}] is action={action}; section 5.2 requires a "
                "computed sha256 string (null is reserved for deleted)",
            ))
        else:
            actual_sha = _sha256_of(fpath)
            if ch["sha256"] != actual_sha:
                out.append(finding(
                    "SHA256_MISMATCH", path_str,
                    f"sha256 {actual_sha} (recomputed from files/{path_str})",
                    ch["sha256"],
                    f"changes[{i}].sha256 disagrees with the bytes under "
                    "files/ — hashes are computed, never transcribed "
                    "(section 5.2.1); a remembered hash is an invented hash "
                    "(CLAUDE.md section 11.6)",
                ))
        actual_size = fpath.stat().st_size
        if ch.get("size_bytes") != actual_size:
            out.append(finding(
                "SIZE_MISMATCH", path_str,
                f"size_bytes {actual_size} (measured from files/{path_str})",
                repr(ch.get("size_bytes")),
                f"changes[{i}].size_bytes disagrees with the file on disk "
                "(section 5.2.1)",
            ))

    # Reverse direction: nothing under files/ may be undeclared (§10.1).
    for rel in ctx["mirror_files"]:
        if rel not in declared_present and rel not in declared_deleted:
            out.append(finding(
                "MIRROR_UNDECLARED", rel,
                "a matching created/modified entry in changes[]", "no entry",
                f"files/{rel} exists but changes[] never declares it "
                "(section 10.1, undeclared file)",
            ))
    return out


def check_claims_subset(ctx: dict) -> list[dict]:
    """set(claims) ⊆ set(validation_will_run), matched verbatim (§5.3, §10.1)."""
    manifest = ctx["manifest"]
    claims = manifest.get("claims")
    will_run = manifest.get("validation_will_run")
    if not isinstance(claims, dict) or not isinstance(will_run, list):
        return []  # schema check already filed the type violations
    out = []
    will_run_set = {w for w in will_run if isinstance(w, str)}
    for key in claims:
        if key not in will_run_set:
            out.append(finding(
                "CLAIMS_UNPAIRABLE", f"claims.{key}",
                "a verbatim match in validation_will_run (same characters, same spacing)",
                f"no entry equal to {key!r}",
                "section 5.3: a claims key with no verbatim "
                "validation_will_run match is unpairable — the tell of a "
                "renamed or paraphrased check; the fix is the key, not a "
                "new entry",
            ))
    return out


def _empty_surface_findings(manifest: dict, kind: str, section: str) -> list[dict]:
    """The empty change surfaces bailout (§5.6.2) and clarification (§5.9.2) share."""
    out = []
    expectations = (
        ("changes", list, []),
        ("deferred", list, []),
        ("validation_will_run", list, []),
        ("claims", dict, {}),
    )
    for field, typ, empty in expectations:
        value = manifest.get(field)
        if isinstance(value, typ) and value != empty:
            out.append(finding(
                "KIND_EMPTY_SURFACE", f"manifest.json:$.{field}",
                f"{field} empty on a {kind} response",
                f"{len(value)} entr{'y' if len(value) == 1 else 'ies'}",
                f"TARBALL.md {section} requires {field} to be empty when "
                f"response_kind is '{kind}'",
            ))
    return out


def _files_surface_finding(ctx: dict, kind: str, section: str) -> list[dict]:
    if ctx["mirror_files"]:
        return [finding(
            "KIND_FILES_PRESENT", "files/",
            f"files/ absent or empty on a {kind} response",
            f"{len(ctx['mirror_files'])} file(s) under files/",
            f"TARBALL.md {section}: a {kind} response ships no file changes",
        )]
    return []


def check_kind_shape(ctx: dict) -> list[dict]:
    """Per-kind shape rules: §5.6.1/§5.6.2 (bailout), §5.9.2 (clarification),
    and the questions-block placement rule for every kind.

    §5.9.2 reads 'Forbidden (or empty) on every other response kind', so an
    empty questions array on a non-clarification kind passes; a non-empty
    one fails. (The schema file's description was aligned to this wording
    in session B1 — the doc is the contract of record, and the lint
    implements TARBALL.md.)
    """
    manifest = ctx["manifest"]
    kind = ctx["kind"]
    rdir: Path = ctx["rdir"]
    if kind is None:
        return []  # invalid enum value; schema check filed it, shape undefined
    out: list[dict] = []
    questions = manifest.get("questions")

    if kind in ("normal", "bailout"):
        if isinstance(questions, list) and len(questions) > 0:
            out.append(finding(
                "QUESTIONS_FORBIDDEN", "manifest.json:$.questions",
                f"no non-empty questions[] on a {kind} response",
                f"{len(questions)} question(s)",
                "TARBALL.md section 5.9.2: questions[] is required on "
                "clarification responses and forbidden (or empty) on every "
                "other kind",
            ))

    if kind == "bailout":
        out.extend(_empty_surface_findings(manifest, kind, "section 5.6.2"))
        out.extend(_files_surface_finding(ctx, kind, "section 5.6.1"))
        if not (rdir / "handoff.md").is_file():
            out.append(finding(
                "ARTIFACT_MISSING", "handoff.md",
                "handoff.md present", "absent",
                "TARBALL.md section 5.6.1: handoff.md is required in bailout "
                "responses",
            ))
        if (rdir / "README.md").is_file():
            out.append(finding(
                "README_FORBIDDEN", "README.md",
                "no README.md in a bailout response", "README.md present",
                "TARBALL.md section 5.6.1: README.md is absent in bailouts — "
                "handoff.md carries the forward-looking content",
            ))
        out.extend(_check_diagnostics(ctx))

    if kind == "clarification":
        out.extend(_empty_surface_findings(manifest, kind, "section 5.9.2"))
        out.extend(_files_surface_finding(ctx, kind, "section 5.9.2"))
        if (rdir / "README.md").is_file():
            out.append(finding(
                "README_FORBIDDEN", "README.md",
                "no README.md in a clarification response", "README.md present",
                "TARBALL.md section 5.9.2: README.md is absent on a "
                "clarification — the questions[] block is the payload and "
                "notes.md is the optional prose channel",
            ))
        if not (isinstance(questions, list) and len(questions) > 0):
            out.append(finding(
                "QUESTIONS_REQUIRED", "manifest.json:$.questions",
                "a non-empty questions[] block",
                "absent" if questions is None else repr(questions),
                "TARBALL.md section 5.9.2: questions[] is required and "
                "non-empty on a clarification response — it is the payload",
            ))
    return out


def _check_diagnostics(ctx: dict) -> list[dict]:
    """diagnostics.json: required in bailouts, parses, schema-validates (§5.8)."""
    dpath = ctx["rdir"] / "diagnostics.json"
    if not dpath.is_file():
        return [finding(
            "ARTIFACT_MISSING", "diagnostics.json",
            "diagnostics.json present", "absent",
            "TARBALL.md section 5.6.1: diagnostics.json is required in "
            "bailout responses",
        )]
    try:
        diag = json.loads(dpath.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        return [finding(
            "DIAGNOSTICS_UNPARSEABLE", "diagnostics.json",
            "valid UTF-8 JSON", f"parse error: {exc}",
            "diagnostics.json did not parse",
        )]
    out = []
    for err in schema_validate(diag, ctx["diagnostics_schema"]):
        loc, _, what = err.partition(": ")
        out.append(finding(
            "DIAGNOSTICS_SCHEMA_VIOLATION", f"diagnostics.json:{loc}",
            "conformance to diagnostics.schema.json", what,
            f"schema violation at {loc}: {what}",
        ))
    return out


# Session B1 checks: generated-artifact deny list, retired next-prompt.md,
# and the feedback-block verification.

# Mirror of bin/bale's deny list (BALE.md section 11 row 20; TARBALL.md
# section 5.1 carries the builder-side rule). Deliberately duplicated
# rather than imported: this lint is a standalone second implementation
# of the WRITTEN contract, never a bale import (see module docstring).
GENERATED_ARTIFACT_DIRS = frozenset({
    "__pycache__", "node_modules", "dist", "build",
})
GENERATED_ARTIFACT_FILE_SUFFIXES = (".pyc", ".pyo")


def check_generated_artifacts(ctx: dict) -> list[dict]:
    """No changes[] path names a generated artifact (TARBALL.md §5.1).

    A path offends when any NON-FINAL component is one of the deny-list
    directory names, or its basename ends in .pyc/.pyo. A source file
    merely named like one (`scripts/build`, `pyc_utils.py`) passes —
    the conservative side of the line, matching bale's apply pre-flight
    (BALE.md §11 row 20) so the worker catches the rejection pre-pack.
    """
    manifest = ctx["manifest"]
    changes = manifest.get("changes")
    if not isinstance(changes, list):
        return []  # schema check already filed the type violation
    out = []
    for i, ch in enumerate(changes):
        p = ch.get("path") if isinstance(ch, dict) else None
        if not isinstance(p, str) or not p:
            continue  # schema check already filed these
        parts = p.replace("\\", "/").split("/")
        offends = any(part in GENERATED_ARTIFACT_DIRS for part in parts[:-1])
        if not offends and parts:
            offends = any(parts[-1].endswith(sfx)
                          for sfx in GENERATED_ARTIFACT_FILE_SUFFIXES)
        if offends:
            out.append(finding(
                "GENERATED_ARTIFACT", p,
                "no generated-artifact paths in changes[] (no "
                "__pycache__/node_modules/dist/build directory component, "
                "no *.pyc/*.pyo basename)", p,
                f"changes[{i}] names a generated artifact — files/ carries "
                "source, never toolchain products (TARBALL.md section 5.1); "
                "bale's apply pre-flight rejects this tarball (BALE.md "
                "section 11 row 20)",
            ))
    return out


def check_next_prompt_retired(ctx: dict) -> list[dict]:
    """No next-prompt.md in the response (retired, TARBALL.md §5.5)."""
    if (ctx["rdir"] / "next-prompt.md").is_file():
        return [finding(
            "NEXT_PROMPT_RETIRED", "next-prompt.md",
            "no next-prompt.md (retired as of "
            "2026-07-06-retire-next-prompt-006)", "next-prompt.md present",
            "TARBALL.md section 5.5: responses do not ship next-prompt.md; "
            "follow-up suggestions go in the Proposals section of notes.md "
            "(section 5.4.1)",
        )]
    return []


def check_feedback_block(ctx: dict) -> list[dict]:
    """feedback.mechanical agrees with this lint's own recomputation.

    Shape is the schema check's job (the feedback block is in
    response-manifest.schema.json); this check verifies the four
    lint-computable values against what the earlier checks actually
    found in THIS run — a disagreement is the tell of a hand-filled or
    stale block (e.g. carried across an edit, or across a compaction,
    CLAUDE.md section 11.6). Absent block = nothing to verify: the
    field is optional in B1, apply persists it verbatim, and B2 builds
    the telemetry record on it. linkage and provenance are
    self-reported placement/echo data the lint cannot verify, so they
    are schema-checked only.

    Runs last in the registry so ctx["findings"] (the shared list the
    runner accumulates into) already holds every earlier check's
    findings.
    """
    manifest = ctx["manifest"]
    fb = manifest.get("feedback")
    if not isinstance(fb, dict):
        return []  # absent, or schema check already filed the type violation
    mech = fb.get("mechanical")
    if not isinstance(mech, dict):
        return []  # schema check already filed it
    prior = ctx.get("findings", [])
    out = []

    def _mismatch(field: str, expected, got) -> dict:
        return finding(
            "FEEDBACK_MECHANICAL_MISMATCH",
            f"manifest.json:$.feedback.mechanical.{field}",
            f"{expected!r} (recomputed by this lint run)", repr(got),
            f"feedback.mechanical.{field} disagrees with what this lint "
            "run found — mechanical values are computed, never "
            "transcribed; refresh the block by re-running the lint "
            "against the current response directory",
        )

    # response_kind echo.
    effective_kind = manifest.get("response_kind", "normal")
    got_kind = mech.get("response_kind")
    if isinstance(got_kind, str) and got_kind != effective_kind:
        out.append(_mismatch("response_kind", effective_kind, got_kind))

    # schema_valid: no findings from the manifest-schema check.
    expected_schema_valid = not any(
        f.get("check") == "manifest-schema" for f in prior)
    got_sv = mech.get("schema_valid")
    if isinstance(got_sv, bool) and got_sv != expected_schema_valid:
        out.append(_mismatch("schema_valid", expected_schema_valid, got_sv))

    # mirror_agreement, split by direction: files_to_changes fails on
    # MIRROR_UNDECLARED; changes_to_files fails on every other
    # changes-mirror finding. Kinds that ship no files/ are vacuously
    # true in both directions (the mirror check returns [] for them and
    # kind-shape owns their file surfaces).
    mirror_findings = [f for f in prior if f.get("check") == "changes-mirror"]
    expected_f2c = not any(
        f.get("code") == "MIRROR_UNDECLARED" for f in mirror_findings)
    expected_c2f = not any(
        f.get("code") != "MIRROR_UNDECLARED" for f in mirror_findings)
    ma = mech.get("mirror_agreement")
    if isinstance(ma, dict):
        got_c2f = ma.get("changes_to_files")
        if isinstance(got_c2f, bool) and got_c2f != expected_c2f:
            out.append(_mismatch("mirror_agreement.changes_to_files",
                                 expected_c2f, got_c2f))
        got_f2c = ma.get("files_to_changes")
        if isinstance(got_f2c, bool) and got_f2c != expected_f2c:
            out.append(_mismatch("mirror_agreement.files_to_changes",
                                 expected_f2c, got_f2c))

    # claims_subset: no findings from the claims-subset check.
    expected_cs = not any(f.get("check") == "claims-subset" for f in prior)
    got_cs = mech.get("claims_subset")
    if isinstance(got_cs, bool) and got_cs != expected_cs:
        out.append(_mismatch("claims_subset", expected_cs, got_cs))

    return out


# The check registry. Session B adds rows (feedback block, provenance
# stamping), it does not restructure the runner. Order matters only in
# that manifest-parse gates everything after it, and that feedback-block
# runs last (it reads the shared findings list the earlier checks fed).
CHECKS: tuple[tuple[str, str, object], ...] = (
    ("manifest-parse",
     "manifest.json exists and parses (TARBALL.md 5.1)",
     check_manifest_parse),
    ("manifest-schema",
     "manifest validates against response-manifest.schema.json",
     check_manifest_schema),
    ("required-artifacts",
     "apply.sh and validation.sh present (TARBALL.md 5.1)",
     check_required_artifacts),
    ("changes-mirror",
     "changes[] <-> files/ both directions; sizes and sha256s recomputed "
     "(TARBALL.md 5.2, 5.2.1, 10.1)",
     check_changes_mirror),
    ("claims-subset",
     "set(claims) is a verbatim subset of validation_will_run "
     "(TARBALL.md 5.3, 10.1)",
     check_claims_subset),
    ("kind-shape",
     "response-kind shape rules: bailout 5.6.1/5.6.2, clarification 5.9.2, "
     "questions placement",
     check_kind_shape),
    ("generated-artifacts",
     "no changes[] path names a generated artifact (TARBALL.md 5.1 deny "
     "list; BALE.md 11 row 20)",
     check_generated_artifacts),
    ("next-prompt-retired",
     "no next-prompt.md in the response (retired, TARBALL.md 5.5)",
     check_next_prompt_retired),
    ("feedback-block",
     "feedback.mechanical agrees with this run's recomputed results "
     "(response_kind, schema_valid, mirror_agreement, claims_subset)",
     check_feedback_block),
)


# ---------------------------------------------------------------------------
# Runner and reporting
# ---------------------------------------------------------------------------

def lint_response_dir(rdir: Path, manifest_schema: dict,
                      diagnostics_schema: dict) -> dict:
    """Run every check; return the full report dict."""
    checks_report = []
    findings: list[dict] = []
    ctx = {
        "rdir": rdir,
        "manifest": None,
        "kind": None,
        "manifest_schema": manifest_schema,
        "diagnostics_schema": diagnostics_schema,
        "mirror_files": _list_mirror_files(rdir / "files"),
        # The same list object the runner extends below — later checks
        # (feedback-block) read earlier checks' findings through it.
        "findings": findings,
    }
    for check_id, description, fn in CHECKS:
        if check_id != "manifest-parse" and ctx["manifest"] is None:
            checks_report.append({
                "id": check_id, "status": "skip",
                "detail": "manifest.json unavailable",
            })
            continue
        got = fn(ctx)
        for f in got:
            f["check"] = check_id
        findings.extend(got)
        checks_report.append({
            "id": check_id,
            "status": "pass" if not got else "fail",
            "detail": description if not got else f"{len(got)} finding(s)",
        })
    return {
        "ok": not findings,
        "response_dir": str(rdir),
        "response_kind": (
            ctx["manifest"].get("response_kind", "normal")
            if isinstance(ctx["manifest"], dict) else None
        ),
        "checks": checks_report,
        "findings": findings,
        "finding_count": len(findings),
    }


def render_human(report: dict, stream) -> None:
    print(f"response-lint: {report['response_dir']} "
          f"(response_kind={report['response_kind']!r})", file=stream)
    for chk in report["checks"]:
        tag = {"pass": "[PASS]", "fail": "[FAIL]", "skip": "[SKIP]"}[chk["status"]]
        print(f"{tag} {chk['id']} — {chk['detail']}", file=stream)
    for f in report["findings"]:
        print(f"  - {f['code']} {f['path']}: {f['message']}", file=stream)
        print(f"      expected: {f['expected']}", file=stream)
        print(f"      got:      {f['got']}", file=stream)
    verdict = "CLEAN" if report["ok"] else f"FAIL — {report['finding_count']} finding(s)"
    print(f"result: {verdict}", file=stream)


def _load_schemas(schema_dir: Path | None) -> tuple[dict, dict]:
    if schema_dir is not None:
        m = json.loads((schema_dir / "response-manifest.schema.json")
                       .read_text(encoding="utf-8"))
        d = json.loads((schema_dir / "diagnostics.schema.json")
                       .read_text(encoding="utf-8"))
        return m, d
    return (json.loads(RESPONSE_MANIFEST_SCHEMA_JSON),
            json.loads(DIAGNOSTICS_SCHEMA_JSON))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="response_lint.py",
        description="Mechanical TARBALL.md section 10.1 self-check for a "
                    "bale response directory. Exit 0 clean, 1 with every "
                    "failure named, 2 on lint error.",
    )
    parser.add_argument("response_dir", help="path to the response-NNN directory")
    parser.add_argument("--json", action="store_true",
                        help="emit one JSON report line on stdout; "
                             "human-readable findings go to stderr")
    parser.add_argument("--schema-dir", default=None,
                        help="directory holding response-manifest.schema.json "
                             "and diagnostics.schema.json to override the "
                             "embedded copies")
    args = parser.parse_args(argv)

    rdir = Path(args.response_dir)
    if not rdir.is_dir():
        print(f"response_lint: error: not a directory: {rdir}", file=sys.stderr)
        return EXIT_ERROR
    try:
        schemas = _load_schemas(Path(args.schema_dir) if args.schema_dir else None)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"response_lint: error: cannot load schemas from "
              f"{args.schema_dir}: {exc}", file=sys.stderr)
        return EXIT_ERROR

    try:
        report = lint_response_dir(rdir, *schemas)
    except OSError as exc:
        print(f"response_lint: error: {exc}", file=sys.stderr)
        return EXIT_ERROR

    if args.json:
        print(json.dumps(report, separators=(",", ":"), sort_keys=True))
        render_human(report, sys.stderr)
    else:
        render_human(report, sys.stdout)
    return EXIT_CLEAN if report["ok"] else EXIT_FINDINGS


if __name__ == "__main__":
    sys.exit(main())
