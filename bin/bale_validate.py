"""bale_validate — JSON Schema + manifest/diagnostics validators.

This module owns the wire-format *shape* checks for the three manifests
bale handles: it loads the JSON Schema files shipped under
`<install>/schemas/` (request, response, diagnostics), runs a small
stdlib-only schema validator over a manifest, and layers the cross-field
invariants a per-instance schema can't express (sha256-conditional-on-
action, `claims` ⊆ `validation_will_run`, the bailout-empties and
clarification-shape rules, stripped-non-empty reasons) on top. Extracted from `bin/bale`'s apply-helpers
section in v0.1.2 to apply CODE.md §4.2 to a section that had grown past the
threshold — the extraction sibling of the v0.0.4 `bale_config` move. The
public entry points (`validate_request_manifest`, `validate_response_manifest`,
`validate_diagnostics`) keep the signatures and call sites they had in
`bin/bale`; only their home moved.

Imported by `bin/bale` as a sibling module (the `bin/` directory is on the
import path by virtue of being the script's directory; `bin/bale` also
explicitly prepends its resolved directory to `sys.path` so the import works
when bale is invoked via a symlink on `PATH` — the same mechanism that lets
`bin/bale` import `bale_config`).

The one shared helper this module needs from `bin/bale` — `fail` — is pulled
from `__main__` lazily, i.e. imported inside each function that calls it rather
than at module top, exactly as `bale_config` does. The lazy form sidesteps the
circular-import hazard (bin/bale imports this module at load time, before its
own `fail` is defined) and makes the dependency visible at the call site. Path
constants (`INSTALL_ROOT`, `SCHEMAS_DIR`) are recomputed here independently
rather than imported, so they are available at module-load time; both files
agree by construction — they are siblings and use the same
`.resolve().parent.parent` pattern.

The schemas are canonical for manifest *shape*; TARBALL.md prose stays
canonical for field semantics. Sessions adding a validator keyword or a new
cross-field invariant extend this module (and, for shape, the schema files
under `schemas/`) — see claude/context/bale-internals.md for how this module
sits next to `bin/bale` and `bale_config`.
"""

from __future__ import annotations

import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# bale_validate.py sits next to bin/bale, so the install root is two parents up
# from this file (just like bin/bale's own INSTALL_ROOT computation). Computed
# here independently rather than imported from __main__ so the path constants
# are available at module-load time. Both files agree by construction — they're
# siblings and use the same .resolve().parent.parent pattern.
INSTALL_ROOT = Path(__file__).resolve().parent.parent

# JSON Schema files for the wire-format manifests, siblings of docs/ at
# <install>/schemas/. Resolved off the symlink-followed INSTALL_ROOT so a
# symlinked bale on PATH still finds them. These schemas are canonical for
# manifest *shape*; TARBALL.md prose stays canonical for field semantics, and
# bale's cross-field invariants (sha256-by-action, claims subset, path-safety,
# stripped-non-empty reasons, bailout-shape and clarification-shape rules)
# stay in Python — see the validators below.
SCHEMAS_DIR = INSTALL_ROOT / "schemas"
REQUEST_MANIFEST_SCHEMA = "request-manifest.schema.json"
RESPONSE_MANIFEST_SCHEMA = "response-manifest.schema.json"
DIAGNOSTICS_SCHEMA = "diagnostics.schema.json"


# --- JSON Schema validation (BALE.md §11 rows 6) ----------------------------
#
# bale validates manifest *shape* against the JSON Schema files shipped at
# <install>/schemas/ (request-manifest, response-manifest, diagnostics). The
# schemas are canonical for shape; TARBALL.md prose stays canonical for field
# semantics. Cross-field invariants that a per-instance schema can't express —
# sha256-conditional-on-action, claims ⊆ validation_will_run, stripped-non-
# empty reasons, the bailout-empties and clarification-shape rules,
# path-safety — stay in the Python validators below, layered on top of the
# schema pass.
#
# The validator is a deliberately small subset of JSON Schema Draft 2020-12:
# enough keywords to express our envelopes (type, enum, required, properties,
# additionalProperties, items, minLength, minItems, minimum) and nothing more.
# This is the v0.1 "stdlib only" constraint applied to schema validation: no
# `jsonschema` dependency. The schemas under schemas/ use only these keywords;
# a schema that reaches for an unsupported keyword is a bug we want surfaced
# (the type-name check raises rather than silently passing), not a silent skip.

_SCHEMA_CACHE: dict[str, dict] = {}


def load_schema(name: str) -> dict:
    """Load and cache a JSON Schema from <install>/schemas/<name>.

    A missing or corrupt schema is fatal: without it bale cannot enforce the
    wire-format shape it promises to enforce (BALE.md §11), and silently
    skipping the check would be exactly the silent-skip failure mode CLAUDE.md
    §6 argues against. So a read/parse error stops the run rather than degrading
    to no validation.
    """
    from __main__ import fail

    if name in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[name]
    path = SCHEMAS_DIR / name
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        fail(f"could not read schema {name} at {path}: {e}")
    except json.JSONDecodeError as e:
        fail(f"schema {name} at {path} is not valid JSON: {e}")
    _SCHEMA_CACHE[name] = schema
    return schema


def _describe_json_value(value) -> str:
    """Human-readable type label for a JSON value, used in schema errors.

    Distinguishes booleans from integers explicitly because Python's
    isinstance(True, int) is True — a reader debugging a manifest wants to see
    'boolean (True)' rather than a misleading 'int'.
    """
    if value is None:
        return "null"
    if isinstance(value, bool):
        return f"boolean ({value})"
    if isinstance(value, str):
        return "string"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def _json_type_matches(value, type_name: str) -> bool:
    """True iff `value` is the JSON Schema type `type_name`.

    bool is matched before int because isinstance(True, int) is True in Python
    while JSON Schema treats booleans and integers as distinct types. An
    unrecognized type keyword raises — it means the schema we authored reached
    past this validator's supported subset, which is a schema bug, not a data
    error, and we want it loud.
    """
    if type_name == "null":
        return value is None
    if type_name == "boolean":
        return isinstance(value, bool)
    if type_name == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if type_name == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if type_name == "string":
        return isinstance(value, str)
    if type_name == "array":
        return isinstance(value, list)
    if type_name == "object":
        return isinstance(value, dict)
    raise ValueError(
        f"unsupported JSON Schema type keyword {type_name!r} — the schema has "
        f"outgrown bale's built-in validator subset"
    )


def _child_path(path: str, key) -> str:
    """Build a dotted/bracketed path for error messages (e.g. changes[2].sha256)."""
    if isinstance(key, int):
        return f"{path}[{key}]"
    return f"{path}.{key}" if path else str(key)


def _validate_against_schema(value, schema: dict, path: str,
                             errors: list[str]) -> None:
    """Recursive worker for validate_against_schema. Appends to `errors`."""
    # type — if it fails, skip the rest; downstream checks assume it held.
    if "type" in schema:
        types = schema["type"]
        if isinstance(types, str):
            types = [types]
        if not any(_json_type_matches(value, t) for t in types):
            label = path or "<root>"
            errors.append(
                f"{label}: expected type {schema['type']}, "
                f"got {_describe_json_value(value)}"
            )
            return

    if "enum" in schema and value not in schema["enum"]:
        label = path or "<root>"
        errors.append(f"{label}: {value!r} is not one of {schema['enum']}")

    if isinstance(value, str) and "minLength" in schema:
        if len(value) < schema["minLength"]:
            label = path or "<root>"
            errors.append(
                f"{label}: string is shorter than minLength {schema['minLength']}"
            )

    if (isinstance(value, (int, float)) and not isinstance(value, bool)
            and "minimum" in schema):
        if value < schema["minimum"]:
            label = path or "<root>"
            errors.append(f"{label}: {value} is below minimum {schema['minimum']}")

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            label = path or "<root>"
            errors.append(
                f"{label}: array has fewer than minItems {schema['minItems']}"
            )
        item_schema = schema.get("items")
        if item_schema is not None:
            for i, item in enumerate(value):
                _validate_against_schema(item, item_schema, _child_path(path, i),
                                         errors)

    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                label = path or "<root>"
                errors.append(f"{label}: missing required key {req!r}")
        props = schema.get("properties", {})
        # additionalProperties defaults to True (permit) when absent, matching
        # JSON Schema. False forbids unknown keys; a dict is a sub-schema every
        # non-listed property must satisfy (this is how `claims` constrains its
        # values while leaving its keys free).
        addl = schema.get("additionalProperties", True)
        for k, v in value.items():
            if k in props:
                _validate_against_schema(v, props[k], _child_path(path, k), errors)
            elif addl is False:
                label = path or "<root>"
                errors.append(f"{label}: unknown key {k!r}")
            elif isinstance(addl, dict):
                _validate_against_schema(v, addl, _child_path(path, k), errors)


def validate_against_schema(instance, schema: dict) -> list[str]:
    """Validate `instance` against `schema`, returning a list of error strings.

    Empty list means valid. Errors carry a dotted/bracketed path
    (e.g. 'changes[2].sha256: ...') so a reader can find the offending field
    fast. This covers shape only — callers layer cross-field invariants on top.
    """
    errors: list[str] = []
    _validate_against_schema(instance, schema, "", errors)
    return errors


def validate_manifest_shape(manifest, schema_name: str, label: str) -> None:
    """Schema-validate a manifest, failing with all shape errors at once.

    `label` names the artifact in the error ('request manifest' /
    'response manifest') so the message reads naturally regardless of which
    schema tripped. Reporting every error in one shot (rather than the first)
    saves a fix-one-rerun loop when a manifest is malformed in several places.
    """
    from __main__ import fail

    schema = load_schema(schema_name)
    errors = validate_against_schema(manifest, schema)
    if errors:
        joined = "\n  - ".join(errors)
        fail(f"{label} failed schema validation ({schema_name}):\n  - {joined}")


def validate_request_manifest(manifest: dict) -> None:
    """Validate a request manifest's shape against request-manifest.schema.json.

    Per TARBALL.md section 3.2. Requests are built by bale itself
    (build_request_manifest), so this is primarily a defense-in-depth self-check
    (CODE.md §8.2): it catches a construction bug before the tarball ships,
    and it positions bale to validate hand-rolled or third-party-packed
    requests the same way. There are no request-side cross-field invariants in
    v0.1 beyond shape, so unlike the response validator this is schema-only.
    """
    from __main__ import fail

    if not isinstance(manifest, dict):
        fail("request manifest is not a JSON object")
    validate_manifest_shape(manifest, REQUEST_MANIFEST_SCHEMA, "request manifest")


def validate_diagnostics(diagnostics: dict) -> None:
    """Validate a bailout's diagnostics.json shape against diagnostics.schema.json.

    Per TARBALL.md section 5.8. The schema is intentionally loose
    (additionalProperties: true at the top level) so future additive fields
    don't reject historical aggregation — but the universal envelope
    (session_id, bail_trigger enum, the two verdict-bearing arrays,
    tool_calls_summary, what_would_save_next_time) is enforced. This replaces
    the bare json.loads sanity-check the bailout path used before.
    """
    from __main__ import fail

    if not isinstance(diagnostics, dict):
        fail("diagnostics.json is not a JSON object")
    validate_manifest_shape(diagnostics, DIAGNOSTICS_SCHEMA, "diagnostics.json")


# The response-manifest key set and the action/claim-value/response_kind
# enumerations are no longer duplicated here as Python constants: the
# response-manifest.schema.json `required`, `additionalProperties:false`, and
# `enum` keywords are now the single source of truth for that shape, consumed
# via validate_response_manifest's schema pass. Keeping a parallel set in
# Python would reintroduce exactly the dual-maintenance drift (update the enum
# in one place, forget the other) the schema split is meant to eliminate.


def validate_response_manifest(manifest: dict) -> None:
    """Per TARBALL.md section 5.2 and BALE.md section 8.1 step 3.

    Two layers, in order:

    1. **Shape** — delegated to response-manifest.schema.json via
       validate_manifest_shape: required keys present, no unknown keys
       (additionalProperties:false), correct types, action/claim-value/
       response_kind enums, size_bytes ≥ 0, minLength:1 on the string fields.
       A shape failure stops here with every shape error reported at once.

    2. **Cross-field invariants** — the rules a per-instance schema can't
       express, kept in Python (per this session's constraint that schemas
       cover shape and Python covers invariants):
         - sha256 conditional on action (deleted → null; else → non-empty);
         - claims keys ⊆ validation_will_run (BALE.md §11 row 15);
         - the bailout-empties rules (TARBALL.md §5.6.2) and the
           clarification-shape rules (TARBALL.md §5.9.2), including the
           questions[]-only-on-clarification conditional;
         - stripped-non-empty on summary / reason / deferred text. minLength:1
           in the schema rejects "" but admits whitespace-only "   "; the
           stripped check here is the stronger rule. "non-empty reason" is
           named explicitly in the session constraint as a Python invariant.

    `response_kind` is optional and defaults to "normal" if absent, so
    v0.0.5-shaped manifests pass through untouched; the schema enforces the
    enum when the key is present.

    The schema pass guarantees types before the invariant code runs, so the
    invariant checks below index into the manifest without re-checking shape.
    """
    from __main__ import fail

    if not isinstance(manifest, dict):
        fail("response manifest is not a JSON object")

    # Layer 1: shape. Exits on any shape error.
    validate_manifest_shape(manifest, RESPONSE_MANIFEST_SCHEMA, "response manifest")

    # Layer 2: cross-field invariants. The schema pass guarantees the types
    # these checks assume.

    # Stripped-non-empty on summary (schema's minLength:1 admits whitespace-only).
    if not manifest["summary"].strip():
        fail("manifest.summary must be non-empty after stripping whitespace")

    # Per-change: stripped-non-empty reason, and sha256 conditional on action.
    for i, change in enumerate(manifest["changes"]):
        if not change["reason"].strip():
            fail(f"manifest.changes[{i}].reason must be non-empty after "
                 f"stripping (path={change['path']!r})")
        if change["action"] == "deleted":
            if change["sha256"] is not None:
                fail(f"manifest.changes[{i}]: deleted entries must have sha256=null")
        else:
            if not isinstance(change["sha256"], str) or not change["sha256"]:
                fail(f"manifest.changes[{i}].sha256 required for {change['action']}")

    # Stripped-non-empty on deferred text.
    for i, d in enumerate(manifest["deferred"]):
        for k in ("what", "why"):
            if not d[k].strip():
                fail(f"manifest.deferred[{i}].{k} must be non-empty after stripping")

    # claims keys must be a subset of validation_will_run (BALE.md §11 row 15).
    will_run = set(manifest["validation_will_run"])
    claim_keys = set(manifest["claims"].keys())
    extra_claims = claim_keys - will_run
    if extra_claims:
        fail(f"manifest.claims has keys not in validation_will_run: "
             f"{sorted(extra_claims)}")

    # Bailout-shape rules (TARBALL.md §5.6.2). The bailout's apply path
    # skips staging/validation entirely, so an out-of-shape bailout —
    # claiming changes, deferrals, or check predictions — is a contract
    # violation worth rejecting here rather than letting a stale field
    # quietly mislead a reader of the session log later.
    response_kind = manifest.get("response_kind", "normal")
    if response_kind == "bailout":
        if manifest["changes"]:
            fail("manifest.response_kind=bailout requires changes[] to be empty "
                 "(TARBALL.md §5.6.2): no files are applied for a bailout")
        if manifest["deferred"]:
            fail("manifest.response_kind=bailout requires deferred[] to be empty "
                 "(TARBALL.md §5.6.2): deferrals live in handoff.md, not the manifest")
        if manifest["validation_will_run"]:
            fail("manifest.response_kind=bailout requires validation_will_run[] "
                 "to be empty (TARBALL.md §5.6.2): no validation runs")
        if manifest["claims"]:
            fail("manifest.response_kind=bailout requires claims{} to be empty "
                 "(TARBALL.md §5.6.2): no validation runs, so nothing to claim")

    # Clarification-shape rules (TARBALL.md §5.9.2) — the bailout block's
    # sibling. A clarification's payload is the questions[] block riding in
    # this manifest (there are no extra artifact files, unlike a bailout),
    # so the shape check here is the whole enforcement surface: the apply
    # path branches before staging/validation, and an out-of-shape
    # clarification — claiming changes, or carrying no questions — would
    # otherwise mislead both the walkthrough reader and the aggregation
    # tooling that reads the preserved manifests later.
    questions = manifest.get("questions", [])
    if response_kind == "clarification":
        if manifest["changes"]:
            fail("manifest.response_kind=clarification requires changes[] to be "
                 "empty (TARBALL.md §5.9.2): no files are applied for a "
                 "clarification")
        if manifest["deferred"]:
            fail("manifest.response_kind=clarification requires deferred[] to be "
                 "empty (TARBALL.md §5.9.2): no work was done, so nothing was "
                 "considered-and-deferred")
        if manifest["validation_will_run"]:
            fail("manifest.response_kind=clarification requires "
                 "validation_will_run[] to be empty (TARBALL.md §5.9.2): no "
                 "validation runs")
        if manifest["claims"]:
            fail("manifest.response_kind=clarification requires claims{} to be "
                 "empty (TARBALL.md §5.9.2): no validation runs, so nothing to "
                 "claim")
        if not questions:
            fail("manifest.response_kind=clarification requires a non-empty "
                 "questions[] (TARBALL.md §5.9.2): the questions are the "
                 "payload — a clarification with nothing to ask is a normal "
                 "response")
        # The schema pass guaranteed each entry carries the four required
        # string fields; the stripped-non-empty rule is the stronger check,
        # same as summary/reason/deferred above.
        for i, q in enumerate(questions):
            for k in ("question", "context", "default_assumption", "why_blocked"):
                if not q[k].strip():
                    fail(f"manifest.questions[{i}].{k} must be non-empty after "
                         f"stripping")
    else:
        # questions[] is the clarification's payload and nothing else's. A
        # normal or bailout manifest carrying questions is out of shape —
        # most likely a response_kind that should have been "clarification",
        # which the reader and the apply path would otherwise silently
        # ignore.
        if questions:
            fail(f"manifest.questions is only valid when "
                 f"response_kind=clarification "
                 f"(got response_kind={response_kind!r})")
