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
TELEMETRY_RECORD_SCHEMA = "telemetry-record.schema.json"
ESCALATION_RECORD_SCHEMA = "escalation-record.schema.json"
BUNDLE_MANIFEST_SCHEMA = "bundle-manifest.schema.json"


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


# --- Telemetry record validation (v0.4.6, board 10 S5) ----------------------
#
# Unlike the three fail()-driven manifest validators above, the telemetry
# validator is a LIBRARY entry point: it returns error strings instead of
# exiting, and it never touches __main__. The blind-checkpoint use case is
# the reason — a planner-authored checkpoint imports this module directly
# (`import bale_validate`) and calls validate_telemetry_record per record,
# where `from __main__ import fail` would ImportError because bin/bale is
# not the running program. The same property makes it usable from tests,
# notebooks, and jq-adjacent one-off scripts over the corpus.

# The claim-basis vocabulary (telemetry-record.schema.json, v0.4.6): the
# self-reported basis of a claim — predicted from structural grounds, or
# observed from a real run before shipping. One home, mirrored into the
# schema's two claim_basis enum spots; a third spelling anywhere is drift.
CLAIM_BASES = ("predicted", "observed")

# The claim vocabulary (TARBALL.md section 5.3): what a manifest's claims
# value may predict per check. Historically enforced by the response-manifest
# schema's enum alone; since the v0.4.7 annotated carrier a claims value is
# a string OR an object, and bale's schema-validator subset has no oneOf, so
# the bare-string enum moved here (validate_response_manifest) while the
# schema keeps the object form's `value` enum at its named spot. One home
# for the Python side; the schema's two enum spots mirror it.
CLAIM_VALUES = ("pass", "fail", "untested", "unknown")

# The escalation priority vocabulary (v0.4.7, board 10 S4): orchestration.md
# section 8's two classes — only critical-path blockers interrupt the
# architect; everything else batches. One home, mirrored into the two
# priority enum spots (escalation-record.schema.json and the response
# manifest's questions rows); a third spelling anywhere is drift.
ESCALATION_PRIORITIES = ("blocking", "batched")


def _load_schema_lib(name: str) -> dict:
    """Load and cache a schema WITHOUT the __main__.fail dependency.

    load_schema() above is the CLI-context loader: it imports `fail` from
    __main__ unconditionally, which is correct when bin/bale is the
    program but breaks under library import (checkpoints, tests). This
    loader shares the cache and raises RuntimeError on a missing or
    corrupt schema instead — a broken install is loud either way, but a
    library caller gets an exception it can handle rather than a
    sys.exit it can't. A schema-load failure is an install problem, never
    a record problem, so it must not masquerade as a validation error
    string.
    """
    if name in _SCHEMA_CACHE:
        return _SCHEMA_CACHE[name]
    path = SCHEMAS_DIR / name
    try:
        schema = json.loads(path.read_text(encoding="utf-8"))
    except OSError as e:
        raise RuntimeError(
            f"could not read schema {name} at {path}: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(
            f"schema {name} at {path} is not valid JSON: {e}") from e
    _SCHEMA_CACHE[name] = schema
    return schema


def _claim_basis_check(v) -> str | None:
    """Closed-vocabulary checker for a claim_basis key (v0.4.6, S5)."""
    if v not in CLAIM_BASES:
        return (f"{v!r} is not one of {list(CLAIM_BASES)} — "
                f"claim_basis, wherever it appears, is exactly "
                f"'predicted' or 'observed' (omit the key when the "
                f"basis is unknown)")
    return None


def _closure_reason_check(closure_vocab: frozenset):
    """Closed-vocabulary checker factory for a closure_reason key.

    The allowed set is derived from the schema's own
    attempts[].closure_reason enum so the vocabulary keeps its one home —
    bin/bale_report's CLOSURE_REASONS mirrors the same enum and the
    parity test pins all the homes together.
    """
    def check(v) -> str | None:
        if v not in closure_vocab:
            allowed = sorted(x for x in closure_vocab if x is not None)
            return (f"{v!r} is not one of {allowed} (or null) — "
                    f"the closure vocabulary is closed, wherever the key "
                    f"rides in the record")
        return None
    return check


def _priority_check(v) -> str | None:
    """Closed-vocabulary checker for a priority key (v0.4.7, board 10 S4)."""
    if v not in ESCALATION_PRIORITIES:
        return (f"{v!r} is not one of {list(ESCALATION_PRIORITIES)} — "
                f"the escalation priority vocabulary "
                f"(orchestration.md section 8's two classes) is closed, "
                f"wherever the key appears")
    return None


def _walk_closed_vocabularies(value, path: str,
                              checks: dict,
                              errors: list[str]) -> None:
    """Recursively enforce closed vocabularies anywhere their keys appear.

    `checks` maps a key name to a checker callable; the checker returns
    an error message for a bad value or None for a good one. Each record
    family passes the vocabulary table it owns: the telemetry record
    checks claim_basis and closure_reason (v0.4.6, S5); the escalation
    record and the clarification question rows check priority (v0.4.7,
    S4). Generalized from S5's two-hardcoded-keys form when the third
    vocabulary arrived — the walk is the shared pattern, the table is
    the per-family part.

    Why a walk and not the schema's named spots alone: the contract for
    these vocabularies is 'optional everywhere' for the key and 'unknown
    values must reject'. A schema's enums catch the spots it can name;
    this walk is the record-wide backstop, so an invented value rejects
    at ANY depth rather than slipping through additionalProperties:true
    at a spot the schema didn't enumerate — a blind consumer mutating
    the record at its own choice of placement gets the same verdict the
    schema-named spots give. S5's HOLD history (a worker defect from a
    single-spot enum) is the precedent this discipline encodes; trusting
    single schema spots is exactly the defect it prevents.

    The vocabularies keep their asymmetries in their own checkers:
    claim_basis rejects null (an unknowable basis is spelled by OMITTING
    the key, never by inventing a third value); closure_reason accepts
    null (apply/retry attempts record an honest null); priority follows
    claim_basis (both classes are real classifications — omit the key on
    a row that predates the vocabulary, never null it).
    """
    if isinstance(value, dict):
        for k, v in value.items():
            child = _child_path(path, k)
            check = checks.get(k)
            if check is not None:
                message = check(v)
                if message is not None:
                    errors.append(f"{child}: {message}")
            _walk_closed_vocabularies(v, child, checks, errors)
    elif isinstance(value, list):
        for i, item in enumerate(value):
            _walk_closed_vocabularies(item, _child_path(path, i),
                                      checks, errors)


def validate_telemetry_record(record: dict) -> list:
    """Validate one telemetry record; [] = valid, else human-readable errors.

    The per-record entry point (v0.4.6, board 10 S5) over
    telemetry-record.schema.json — importable as a library from
    bin/bale_validate.py, no bale process required. Previously the shape
    was exercised only corpus-wise through consumers (`bale stats`, the
    suite's per-fixture schema reads); this is the one-record surface a
    blind checkpoint, a test, or an ad-hoc corpus sweep calls directly:

        errors = validate_telemetry_record(json.loads(path.read_text()))
        if errors: ...

    Two layers, mirroring validate_response_manifest's split:

    1. **Shape** — the schema pass (validate_against_schema against
       telemetry-record.schema.json). The schema is intentionally loose
       (additionalProperties: true at the envelope and inside attempts),
       so legacy records without the v0.4.6 fields — or without any
       later additive field — keep validating; what it does pin, it
       pins: the outcome / command / closure_reason enums (including
       no_response and malformed_response, v0.4.6), the required
       envelope, and the typed sub-objects.
    2. **The closed-vocabulary invariants** — the record-wide walk
       (_walk_closed_vocabularies): any claim_basis key at any depth
       must be exactly 'predicted' or 'observed', and any closure_reason
       key at any depth must be a schema-vocabulary reason or null. This
       is the strictness the brief demands ('unknown closure reasons and
       unknown claim_basis values must reject') made placement-robust:
       the loose schema constrains the spots it names, and the walk
       gives every other spot the same verdict, so a consumer mutating
       the record at its own choice of placement — a blind checkpoint
       included — cannot land an invented value anywhere.

    Returns a list of error strings with dotted/bracketed paths
    (e.g. 'attempts[0].closure_reason: ...'); empty list means valid.
    A non-dict argument is reported as an error, not raised — the caller
    handed us data, and data problems are return values here. A missing
    or corrupt schema file raises RuntimeError: that is an install
    problem, not a record problem (_load_schema_lib).
    """
    if not isinstance(record, dict):
        return [f"telemetry record is not a JSON object "
                f"(got {_describe_json_value(record)})"]
    schema = _load_schema_lib(TELEMETRY_RECORD_SCHEMA)
    errors = validate_against_schema(record, schema)
    # The closure vocabulary's one home is the schema's own enum at its
    # named spot; derive the walk's allowed set from it so the two layers
    # cannot drift (CLOSURE_REASONS parity is pinned separately by test).
    closure_vocab = frozenset(
        schema["properties"]["attempts"]["items"]
              ["properties"]["closure_reason"]["enum"])
    _walk_closed_vocabularies(record, "", {
        "claim_basis": _claim_basis_check,
        "closure_reason": _closure_reason_check(closure_vocab),
    }, errors)
    return errors


# --- Escalation-contract validation (v0.4.7, board 10 S4) -------------------
#
# Two more LIBRARY entry points in the validate_telemetry_record posture:
# empty list = valid, strings = errors, no __main__ dependency, importable
# by a planner-authored blind checkpoint, a test, or an ad-hoc sweep. They
# are the validation surface for the escalation contract's two wire shapes
# (doctrine home: claude/context/orchestration.md section 8): the
# escalation record (schemas/escalation-record.schema.json — no producer
# yet; the schema is the contract landing first) and the clarification
# response's extended question rows (response-manifest.schema.json's
# questions items, the same rows validate_response_manifest checks inside
# a full manifest, exposed here row-wise for callers holding rows alone).


def validate_escalation_record(record: dict) -> list:
    """Validate one escalation record; [] = valid, else human-readable errors.

    The per-record entry point over escalation-record.schema.json,
    importable as a library from bin/bale_validate.py, no bale process
    required — the validate_telemetry_record posture exactly:

        errors = validate_escalation_record(json.loads(path.read_text()))
        if errors: ...

    Two layers, mirroring validate_telemetry_record's split:

    1. **Shape** — the schema pass. The schema is intentionally loose
       (additionalProperties: true at the envelope, matching the
       telemetry record), so future additive fields keep old records
       validating; what it does pin, it pins: the six-field required
       core (question, options, recommendation, priority, subsumes,
       amendment_target), options non-empty, subsumes an array, and
       the enums at their named spots.
    2. **The closed-vocabulary invariant** — the record-wide walk
       (_walk_closed_vocabularies, its docstring for why): a priority
       key at ANY depth must be exactly 'blocking' or 'batched'
       (ESCALATION_PRIORITIES), so an invented class rejects wherever
       a consumer put it, not only at the schema-named spot.

    A non-dict argument is reported as an error, not raised — the
    caller handed us data, and data problems are return values here. A
    missing or corrupt schema file raises RuntimeError: an install
    problem, not a record problem (_load_schema_lib).
    """
    if not isinstance(record, dict):
        return [f"escalation record is not a JSON object "
                f"(got {_describe_json_value(record)})"]
    schema = _load_schema_lib(ESCALATION_RECORD_SCHEMA)
    errors = validate_against_schema(record, schema)
    _walk_closed_vocabularies(record, "", {"priority": _priority_check},
                              errors)
    return errors


def validate_bundle_manifest(record: dict) -> list:
    """Validate one planner-bundle manifest; [] = valid, else errors.

    The per-record entry point over bundle-manifest.schema.json
    (v0.4.12, board 49a-i; format home BALE.md §6.7), importable as a
    library from bin/bale_validate.py, no bale process required — the
    validate_telemetry_record posture exactly. This is the validation
    surface landing with the format, ahead of its consumers (the
    §6.6 schema-first precedent): the open verb (49a-ii) calls it on
    the extracted, line-ending-normalized bundle.json before trusting
    anything else in the bundle, and the crafter's emission (49b)
    self-checks against it.

    Two layers, mirroring validate_escalation_record's split:

    1. **Shape** — the schema pass. The schema is intentionally loose
       (additionalProperties: true at the envelope and inside
       entries), so future additive fields keep old bundles
       validating; what it does pin, it pins: the four-key required
       envelope (bundle_format, pack_argv, members, pre_answered),
       bundle_format exactly 1, the two named member slots (each an
       object or an explicit null — uniform shape, the depends_on
       precedent), and the closed intent-prompt vocabulary at its
       named spot.
    2. **Cross-field invariants** the schema subset can't express:

       - each present member's `sha256` is exactly 64 lowercase hex
         characters (the published hash of the member's
         LF-normalized bytes — the normalization rule is the
         format's, §6.7; this function sees only the manifest);
       - each present member's `path` is a flat archive-member name:
         no path separators, not `.` or `..` — the bundle's members
         sit beside bundle.json at the archive root;
       - the two member paths are distinct when both are present;
       - `pack_argv` carries neither delivery flag
         (`--readme-file` / `--checkpoint-file`, bare or `=`-glued):
         the open verb injects those pointing at the extracted
         members, so a stored one could only disagree with the
         shipped bytes — the member's presence is the single source
         for the flag's injection;
       - `pack_argv` does not name the pack subcommand itself as its
         first token: the array is the argument vector AFTER `pack`.

    Duplicate (prompt, subject) intent pairs are NOT re-checked here;
    parse_pre_answered_intents (bin/bale_pack.py) owns that refusal
    at the consumption site, and this validator stays a shape-and-
    invariant surface over one JSON document.

    A non-dict argument is reported as an error, not raised — the
    caller handed us data, and data problems are return values here.
    A missing or corrupt schema file raises RuntimeError: an install
    problem, not a record problem (_load_schema_lib).
    """
    if not isinstance(record, dict):
        return [f"bundle manifest is not a JSON object "
                f"(got {_describe_json_value(record)})"]
    schema = _load_schema_lib(BUNDLE_MANIFEST_SCHEMA)
    errors = validate_against_schema(record, schema)

    hex_digits = set("0123456789abcdef")
    members = record.get("members")
    member_paths: list[str] = []
    if isinstance(members, dict):
        for slot in ("brief", "checkpoint"):
            member = members.get(slot)
            if not isinstance(member, dict):
                continue  # null slot, or shape errors already reported
            sha = member.get("sha256")
            if isinstance(sha, str) and not (
                    len(sha) == 64 and set(sha) <= hex_digits):
                errors.append(
                    f"members.{slot}.sha256: must be exactly 64 "
                    f"lowercase hex characters")
            path = member.get("path")
            if isinstance(path, str):
                if ("/" in path or "\\" in path
                        or path in (".", "..") or not path.strip()):
                    errors.append(
                        f"members.{slot}.path: must be a flat archive-"
                        f"member name beside bundle.json (no path "
                        f"separators, not '.' or '..'), got {path!r}")
                else:
                    member_paths.append(path)
    if len(member_paths) == 2 and member_paths[0] == member_paths[1]:
        errors.append(
            f"members: brief and checkpoint name the same archive "
            f"member {member_paths[0]!r}; the two must be distinct")

    argv = record.get("pack_argv")
    if isinstance(argv, list):
        for i, arg in enumerate(argv):
            if not isinstance(arg, str):
                continue  # schema pass already reported the type
            for banned in ("--readme-file", "--checkpoint-file"):
                if arg == banned or arg.startswith(banned + "="):
                    errors.append(
                        f"pack_argv[{i}]: {banned} is injected by the "
                        f"consumer from the bundle's own members and "
                        f"must not be stored in the argv — the "
                        f"member's presence is the single source")
        if argv and isinstance(argv[0], str) and argv[0] == "pack":
            errors.append(
                "pack_argv[0]: the array is the argument vector AFTER "
                "the pack subcommand; do not store the verb itself")
    return errors


def validate_clarification_questions(rows: list) -> list:
    """Validate clarification question rows; [] = valid, else errors.

    The row-wise entry point over the response manifest's questions[]
    item shape — the schema of record stays
    response-manifest.schema.json's questions items (one home; this
    function derives the sub-schema from it rather than duplicating
    it), so a row that validates here validates inside a full
    clarification manifest and vice versa. Library posture per
    validate_telemetry_record: no bale process, no __main__.

    Rows are the legacy four-field shape (question, context,
    default_assumption, why_blocked) or the v0.4.7 extended shape
    adding any of options (non-empty when present), recommendation,
    and priority (enum exactly 'blocking' | 'batched') — everything
    additive, so every legacy row keeps validating. The priority
    vocabulary is additionally enforced row-wide by the closed-
    vocabulary walk (its docstring for why), matching
    validate_escalation_record's discipline so the two surfaces give
    one verdict for an invented class.

    A non-list argument is reported as an error, not raised; error
    strings carry questions[i]-prefixed paths. A missing or corrupt
    schema file raises RuntimeError (_load_schema_lib).
    """
    if not isinstance(rows, list):
        return [f"clarification questions are not a JSON array "
                f"(got {_describe_json_value(rows)})"]
    schema = _load_schema_lib(RESPONSE_MANIFEST_SCHEMA)
    questions_schema = schema["properties"]["questions"]
    errors: list[str] = []
    _validate_against_schema(rows, questions_schema, "questions", errors)
    _walk_closed_vocabularies(rows, "questions",
                              {"priority": _priority_check}, errors)
    return errors


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

    # Bare-string claim values must be in the claim vocabulary. Until the
    # v0.4.7 annotated carrier the schema's enum enforced this; a claims
    # value is now a string OR an object and the schema-validator subset
    # has no oneOf, so the schema pins the object form's shape (value
    # enum, claim_basis enum, no unknown keys) and the bare-string enum
    # moved here. Same vocabulary either way (CLAIM_VALUES).
    for key, value in manifest["claims"].items():
        if isinstance(value, str) and value not in CLAIM_VALUES:
            fail(f"manifest.claims[{key!r}]: {value!r} is not one of "
                 f"{list(CLAIM_VALUES)}")

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
            # The v0.4.7 optional fields get the same stronger-than-
            # minLength rule when present (priority is enum-checked by
            # the schema and needs no stripping).
            if "recommendation" in q and not q["recommendation"].strip():
                fail(f"manifest.questions[{i}].recommendation must be "
                     f"non-empty after stripping when present")
            for j, option in enumerate(q.get("options", [])):
                if not option.strip():
                    fail(f"manifest.questions[{i}].options[{j}] must be "
                         f"non-empty after stripping")
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
