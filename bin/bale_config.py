"""bale_config — configurables loader/merger + `bale config init` wizard.

This module owns the `bale.toml` subsystem at both layers (project:
`<repo>/bale.toml`; global: `<install>/user/bale.toml`). It bundles the
read-side (load/merge/typed accessors) with the write-side (the
`bale config init` wizard) because the wizard is the canonical writer
for the schema the read-side reads — they evolve together. Sections
adding a new configurable extend BOTH halves in the same response, by
the bale-internals.md §2.5 contract.

Imported by `bin/bale` as a sibling module (the `bin/` directory is on
the import path by virtue of being the script's directory; `bin/bale`
also explicitly prepends its resolved directory to `sys.path` so the
import works when bale is invoked via a symlink on `PATH`).

The few shared helpers (`log`, `fail`, `git`, `repo_root`,
`refuse_system_dir`) live in `bin/bale` and are pulled from
`__main__` lazily — i.e. imported inside each function that needs
them, not at module top. The lazy form sidesteps the circular-import
hazard (bin/bale and bale_config reference each other) and makes the
dependency visible at the call site. The cost is repetition of a
short `from __main__ import` line at the head of a handful of
functions; the benefit is that this module's top-level imports stay
clean and the module loads regardless of where `bin/bale`'s own
top-level execution is at the moment of import.

Sections:
  1. Imports + constants                              (~line  60)
  2. Configurables: load and merge                    (~line 140)
  3. `bale config init` wizard                        (~line 430)

Constants exported for `bin/bale`'s use (referenced by `run_hook` for
layer detection, and by `build_parser` for command dispatch):
  - GLOBAL_USER_DIR — absolute path to <install>/user/, the user-owned
    subtree where global config and global hook scripts live.
  - cmd_config_init — argparse-bound entry point for `bale config init`.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Optional

# TOML parsing goes through the in-tree shim rather than stdlib `tomllib`
# directly: `tomllib` is stdlib only on Python 3.11+, and bale supports 3.10
# (which has no stdlib TOML parser). `_bale_toml` exposes the same
# load/loads/TOMLDecodeError surface, backed by stdlib `tomllib` on 3.11+ and a
# vendored pure-Python parser on 3.10. Imported by bare name because `bin/` is
# on sys.path (bin/bale prepends it; see this module's top docstring). Aliased
# to `tomllib` so the call sites below read as ordinary tomllib usage.
import _bale_toml as tomllib


# ---------------------------------------------------------------------------
# 1. Imports + constants
# ---------------------------------------------------------------------------

# bale_config.py sits next to bin/bale, so the install root is two parents up
# from this file (just like bin/bale's own INSTALL_ROOT computation). We
# compute it here independently rather than importing from __main__ so the
# constant is available at module-load time (no lazy/late binding for paths
# that downstream tuples depend on). Both files agree by construction —
# they're siblings and use the same .resolve().parent.parent pattern.
INSTALL_ROOT = Path(__file__).resolve().parent.parent

# Configurables file name. Used at two layers:
#   - <repo>/bale.toml — per-repo, committed and team-shared.
#   - <install>/user/bale.toml — per-install global, user-owned, never in the
#     release tarball. The user/ subtree is bale's only user-owned location;
#     everything else under <install>/ is replaced on upgrade.
# Absent file (or absent key within it) = silent skip at that layer. Project
# layer overrides global per-key. The `bale config init` wizard is the canonical
# interface for both; `--global` targets the install-layer file. Schema and
# layering rules live in claude/context/bale-internals.md.
BALE_CONFIG = "bale.toml"

# Subdirectory of the install that bale never owns: it's where the user's
# global config and global hook scripts live. The release tarball ships nothing
# under here; `bale config init --global` creates the directory on first write.
# Hook paths in <install>/user/bale.toml resolve relative to this directory
# (parallel to project hooks resolving relative to <repo>/).
GLOBAL_USER_DIR_NAME = "user"
GLOBAL_USER_DIR = INSTALL_ROOT / GLOBAL_USER_DIR_NAME
GLOBAL_CONFIG_PATH = GLOBAL_USER_DIR / BALE_CONFIG

# Hooks bale knows how to invoke. Sessions adding a new hook extend this
# tuple AND walk_configurables() AND render_bale_toml() in the same
# response — the wizard is the single source of truth for the
# discoverable surface, so a hook that's invoked but not in the wizard
# is a contract violation.
HOOK_NAMES = (
    # Triggered after `bale pack` successfully writes the request tarball
    # and acquires the session lock. The session is durable on disk by the
    # time this fires; per the hook contract, a non-zero exit is logged
    # but does not unwind pack. Order in this tuple is lifecycle order
    # (pack before apply); the same order is the wizard's prompt order
    # and the rendered bale.toml's key order.
    "post_pack",
    # Triggered after `bale apply` succeeds (PASS path, post-merge).
    # Used by bale-src itself to reinstall bale into the install location
    # after each PASS session.
    "post_apply_pass",
)

# Value-shaped configurables under the [apply] section. Parallels HOOK_NAMES
# in spirit (a tuple of declared keys; the wizard is the source of truth for
# the discoverable surface) but the *shape* is different: hooks are single
# script paths, these are richer typed values. Each entry here has:
#   - a typed accessor (e.g. get_apply_search_paths) that loads + validates
#   - a walk_configurables() block that prompts for it
#   - a render_bale_toml() branch that serializes it
# Currently just `search_paths` (a list of directories). The lesson the
# bale.toml format generalizes by adding sections + typed accessors, not by
# abstracting away the difference between section types.
APPLY_VALUES = (
    # List of directories to search when a command receives a relative
    # inbound-file argument: the tarball for `bale apply` / `bale retry` /
    # `bale handoff`, and (v0.3.6) the prose file for `bale pack
    # --readme-file`. Tried in order; first match wins; cwd is always
    # tried first implicitly. Absolute paths bypass search entirely. The
    # key keeps its historical `apply.` spelling — it named the tarball
    # resolver first — but semantically it is "the machine's inbound
    # directories", one key consulted by every inbound-file surface.
    "search_paths",
    # Bool. Per-config opt-in to non-interactive apply mode (BALE.md §5.4 /
    # §8.7) — the same mode `bale apply --no-interact` / `bale retry
    # --no-interact` enable per invocation. In the mode, the walkthrough
    # takes its default action and the pre-hook confirmation resolves from
    # hook_auto_accept below; every bypassed prompt logs the decision taken
    # and its source. Absent/false = prompt normally.
    "no_interact",
    # Bool. Consulted only when non-interactive mode is active: true =
    # accept the pre-hook confirmation without prompting; absent/false =
    # decline, matching the interactive prompt's decline default.
    # Interactive runs always prompt regardless of this key.
    "hook_auto_accept",
)

# The two admissible values of staging.strategy (BALE.md §8.3 step 2).
# "working-tree" is the default and the documented fallback/ground truth;
# "target-base" is the opt-in validation-fidelity strategy. The tuple is
# the single source of truth the typed accessor and the wizard both
# validate against.
STAGING_STRATEGIES = ("working-tree", "target-base")

# Value-shaped configurables under the [staging] section — the opt-in
# surface for the apply pipeline's staging strategy (BALE.md §8.3 step 2).
# Same trio contract as APPLY_VALUES: each key has a typed accessor, a
# walk_configurables() block, and a render_bale_toml() branch.
STAGING_VALUES = (
    # String enum, one of STAGING_STRATEGIES. Absent/empty = "working-tree"
    # (byte-identical to the historical behavior). "target-base"
    # materializes the target tip's tree into staging plus the declared
    # untracked_inputs below, so validation exercises exactly the content
    # the session commit lands. Config-only by design: the strategy is a
    # property of the project's validation posture, not of one invocation,
    # and because apply and retry both re-resolve it from the merged
    # config at stage time, a retry re-stages under the same strategy —
    # no per-session stamp needed.
    "strategy",
    # List of repo-relative paths (files or directories; no globs, no
    # tilde/env expansion — entries are repo-relative literals). Only
    # meaningful with strategy = "target-base": each entry is untracked
    # build or dependency state that must ride into staging for
    # validation to run (a pure git-archive tree carries none). Entries
    # must exist in the working tree and be untracked at the target tip
    # at stage time; violations fail the stage loudly.
    "untracked_inputs",
)

# Value-shaped configurables under the [identity] section — pack-time
# provenance (v0.3.8, session B1). Same trio contract as APPLY_VALUES /
# STAGING_VALUES: each key has a typed accessor, a walk_configurables()
# block, and a render_bale_toml() branch. Wizard-walked and
# renderer-preserved per the [staging] precedent, so `bale config init`
# re-runs keep the key rather than dropping it.
IDENTITY_VALUES = (
    # String. Who authors packs from this repo (project layer) or this
    # install (global layer). Stamped into request manifests as
    # provenance.packer; a --packer flag on `bale pack` overrides per
    # invocation (flag > project > global). Set once; empty string at
    # the project layer is the suppress form (collapses to the global
    # value being ignored, same as hooks).
    "packer",
)


# ---------------------------------------------------------------------------
# 2. Configurables: load and merge
# ---------------------------------------------------------------------------
#
# Two files share the same TOML schema:
#
#   - <install>/user/bale.toml — global. User-owned, lives inside the install
#     so the whole install dir stays portable as a unit. Created by
#     `bale config init --global`. Never in the release tarball.
#   - <repo>/bale.toml — project. Committed and team-shared. Created by
#     `bale config init`.
#
# Absent file (or absent key within it) = silent skip at that layer. The
# project layer overrides the global layer per-key: a key set in project wins;
# a key absent in project inherits global; a key explicitly set to "" (or to
# [] for list-shaped configs) at the project layer suppresses any inherited
# global value (via the typed accessors' existing "empty = unset" contract).
#
# Hook script paths resolve relative to whichever layer owns them: project
# hooks against the repo, global hooks against <install>/user/. After
# merged_config(), get_hook() returns an absolute filesystem path string and
# callers don't track layer provenance.
#
# The discoverable surface is owned by walk_configurables() below; both files
# just point back at the wizard. Schema and layering live in
# claude/context/bale-internals.md.

def load_config(repo: Path) -> dict:
    """Return parsed <repo>/bale.toml as a dict, or {} if the file is absent.

    Project layer only — for the layered effective config, use merged_config().

    A missing file is the canonical opt-out — the project's behavior collapses
    to no-config (or, in the layered model, to whatever the global layer
    supplies). A malformed file is fatal: we never want a typo to silently
    disable a configured hook the user thought was wired up.
    """
    from __main__ import fail

    cfg_path = repo / BALE_CONFIG
    if not cfg_path.is_file():
        return {}
    try:
        with cfg_path.open("rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        fail(f"{cfg_path} is malformed TOML: {e}")
    except OSError as e:
        fail(f"could not read {cfg_path}: {e}")


def load_global_config() -> dict:
    """Return parsed <install>/user/bale.toml as a dict, or {} if absent.

    Global layer only — for the layered effective config, use merged_config().

    Same contract as load_config: absent = silent {}, malformed = fatal. The
    file lives inside the install so the install dir stays portable as a unit;
    `bale config init --global` is the canonical writer.
    """
    from __main__ import fail

    if not GLOBAL_CONFIG_PATH.is_file():
        return {}
    try:
        with GLOBAL_CONFIG_PATH.open("rb") as f:
            return tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        fail(f"{GLOBAL_CONFIG_PATH} is malformed TOML: {e}")
    except OSError as e:
        fail(f"could not read {GLOBAL_CONFIG_PATH}: {e}")


def merged_config(repo: Path) -> dict:
    """Return the effective config, layering global under project.

    Layering rules:
      - Per-key replacement. A key set at the project layer wins; absent at
        the project layer means inherit from global.
      - Hook scripts (string scalars) resolve to absolute filesystem paths at
        merge time, against their owning layer's root: <repo>/ for project,
        <install>/user/ for global. Downstream callers see absolute paths and
        don't need to track provenance.
      - List-shaped configs (currently just apply.search_paths) use replace
        semantics: when the project sets the key, its list wins fully
        (including the empty-list case). Append semantics aren't well-defined
        across all future list configs, so each list-shaped key's typed
        accessor decides.
      - Empty-string scalars and empty lists at the project layer pass through
        as-is. The typed accessors (get_hook, get_apply_search_paths) treat
        empty as "unset" — so an empty value at the project layer effectively
        suppresses any inherited global value. This is the suppression contract
        bale-internals.md describes; no special handling needed here.

    Malformed shapes at either layer (e.g. [hooks] as a list) are tolerated
    here — strict validation lives in the typed accessors, which the call
    sites already invoke. This function's job is shape-preserving layering,
    not validation.
    """
    g = load_global_config()
    p = load_config(repo)
    merged: dict = {}

    # [hooks] — scalar string keys.
    g_hooks = g.get("hooks") if isinstance(g.get("hooks"), dict) else {}
    p_hooks = p.get("hooks") if isinstance(p.get("hooks"), dict) else {}
    out_hooks: dict = {}
    for key in HOOK_NAMES:
        if key in p_hooks:
            # Project layer owns the key — resolve relative to repo.
            v = p_hooks[key]
            if isinstance(v, str):
                s = v.strip()
                if s:
                    out_hooks[key] = str((repo / s).resolve())
                else:
                    # Explicit suppress: pass through empty string. get_hook()
                    # treats this as None (no hook runs), and crucially, the
                    # global value is NOT inherited because the project key is
                    # present.
                    out_hooks[key] = ""
        elif key in g_hooks:
            v = g_hooks[key]
            if isinstance(v, str):
                s = v.strip()
                if s:
                    out_hooks[key] = str((GLOBAL_USER_DIR / s).resolve())
    if out_hooks:
        merged["hooks"] = out_hooks

    # [apply] — value-shaped keys, per-key replacement (lists replace fully;
    # bools have no empty-suppress form because `false` at the project layer
    # is itself the override for an inherited `true`). Pass values through
    # untouched; the typed accessors (get_apply_search_paths, the bool
    # readers) handle expansion + strict shape checking at read time.
    g_apply = g.get("apply") if isinstance(g.get("apply"), dict) else {}
    p_apply = p.get("apply") if isinstance(p.get("apply"), dict) else {}
    out_apply: dict = {}
    for key in APPLY_VALUES:
        if key in p_apply:
            out_apply[key] = p_apply[key]
        elif key in g_apply:
            out_apply[key] = g_apply[key]
    if out_apply:
        merged["apply"] = out_apply

    # [staging] — same per-key replacement as [apply]: a key set at the
    # project layer wins; absent inherits global; the empty-string /
    # empty-list forms pass through and read as "unset" in the typed
    # accessors, giving the project layer its suppress form.
    g_staging = g.get("staging") if isinstance(g.get("staging"), dict) else {}
    p_staging = p.get("staging") if isinstance(p.get("staging"), dict) else {}
    out_staging: dict = {}
    for key in STAGING_VALUES:
        if key in p_staging:
            out_staging[key] = p_staging[key]
        elif key in g_staging:
            out_staging[key] = g_staging[key]
    if out_staging:
        merged["staging"] = out_staging

    # [identity] — same per-key replacement as [apply]/[staging]: a key
    # set at the project layer wins; absent inherits global; the
    # empty-string form passes through and reads as "unset" in the typed
    # accessor, giving the project layer its suppress form.
    g_identity = g.get("identity") if isinstance(g.get("identity"), dict) else {}
    p_identity = p.get("identity") if isinstance(p.get("identity"), dict) else {}
    out_identity: dict = {}
    for key in IDENTITY_VALUES:
        if key in p_identity:
            out_identity[key] = p_identity[key]
        elif key in g_identity:
            out_identity[key] = g_identity[key]
    if out_identity:
        merged["identity"] = out_identity

    return merged


def get_hook(cfg: dict, name: str) -> Optional[str]:
    """Return the configured hook script path, or None if unset/empty.

    Expects the merged config (from merged_config). After merging, hook values
    are absolute filesystem paths resolved against their owning layer's root
    — so this returns an absolute path string, never a relative one.

    Empty strings are treated as unset so the wizard can write `key = ""` for
    "I considered this and chose to skip" without a separate delete path. In
    the layered model an empty string at the project layer is also the
    suppression mechanism: merged_config preserves it, and this accessor
    returns None, so run_hook does nothing — overriding any inherited global.

    Raises ValueError when called with a name bale doesn't know about —
    catches typos at the call site rather than silently doing nothing.
    """
    if name not in HOOK_NAMES:
        raise ValueError(f"unknown hook name: {name!r}")
    hooks = cfg.get("hooks", {})
    if not isinstance(hooks, dict):
        return None
    val = hooks.get(name)
    if not isinstance(val, str):
        return None
    val = val.strip()
    return val or None


def get_apply_search_paths(cfg: dict) -> list[str]:
    """Return the configured [apply].search_paths, expanded.

    Consumed by every inbound-file resolution surface — the tarball
    argument of `bale apply` / `bale retry` / `bale handoff`, and (since
    v0.3.6) `bale pack --readme-file` — all through bin/bale's
    resolve_inbound_path. The key keeps its historical `apply.` spelling;
    see APPLY_VALUES above.

    Absent section or absent key returns []. Malformed shape is fatal —
    same contract as load_config's "typo shouldn't silently disable a
    configured behavior the user thought was wired up." A misshapen
    search_paths is exactly that class of bug.

    Expansion: every entry is run through expandvars then expanduser at
    read time. Persistence keeps the literal user-typed string (so a
    committed bale.toml with `~/Downloads` works on any machine where
    `~` resolves); expansion happens here, at the boundary between the
    config file and the code that consumes the paths.

    Empty-string entries are dropped silently — they're an artifact of
    sloppy hand-edits (e.g. trailing colons in wizard input) and the
    user's intent is clearly to omit them.
    """
    from __main__ import fail

    apply_section = cfg.get("apply")
    if apply_section is None:
        return []
    if not isinstance(apply_section, dict):
        fail(f"{BALE_CONFIG}: [apply] must be a table, got {type(apply_section).__name__}")

    raw = apply_section.get("search_paths")
    if raw is None:
        return []
    if not isinstance(raw, list):
        fail(f"{BALE_CONFIG}: apply.search_paths must be an array of strings, "
             f"got {type(raw).__name__}")
    for i, entry in enumerate(raw):
        if not isinstance(entry, str):
            fail(f"{BALE_CONFIG}: apply.search_paths[{i}] must be a string, "
                 f"got {type(entry).__name__}")

    expanded: list[str] = []
    for entry in raw:
        e = entry.strip()
        if not e:
            continue
        # expandvars first so a $VAR pointing at a path containing ~ still
        # gets the ~ expanded by the second step.
        expanded.append(os.path.expanduser(os.path.expandvars(e)))
    return expanded


def _get_apply_bool(cfg: dict, key: str) -> Optional[bool]:
    """Shared strict reader for bool-shaped [apply] keys.

    Absent section or absent key returns None (unset). A TOML boolean
    returns as-is. Any other shape is fatal — same contract as
    get_apply_search_paths: a typo must not silently disable (or, worse
    here, silently *enable*) a behavior the user thought they configured.
    A string like "true" is a typo in TOML terms, not a boolean.
    """
    from __main__ import fail

    apply_section = cfg.get("apply")
    if apply_section is None:
        return None
    if not isinstance(apply_section, dict):
        fail(f"{BALE_CONFIG}: [apply] must be a table, got {type(apply_section).__name__}")
    raw = apply_section.get(key)
    if raw is None:
        return None
    if not isinstance(raw, bool):
        fail(f"{BALE_CONFIG}: apply.{key} must be a boolean (true/false), "
             f"got {type(raw).__name__}")
    return raw


def get_apply_no_interact(cfg: dict) -> bool:
    """Return [apply].no_interact from the merged config; absent → False.

    True opts every `bale apply` / `bale retry` into non-interactive mode
    without the per-invocation --no-interact flag. Bool-shaped, so there is
    no empty-suppress form: an explicit `false` at the project layer is the
    override for an inherited global `true` (per-key replacement covers it).
    """
    return bool(_get_apply_bool(cfg, "no_interact"))


def get_apply_hook_auto_accept(cfg: dict) -> bool:
    """Return [apply].hook_auto_accept from the merged config; absent → False.

    Consulted only when non-interactive mode is active: True means run_hook
    accepts the pre-hook confirmation without prompting; False/absent means
    it declines, matching the interactive prompt's decline default.
    Interactive runs never consult this key — they always prompt.
    """
    return bool(_get_apply_bool(cfg, "hook_auto_accept"))


def apply_bool_source(repo: Path, key: str) -> Optional[str]:
    """Return "project" or "global" — the layer whose bale.toml supplies
    [apply].<key> under the per-key merge — or None if neither layer sets it.

    Logging/display helper for the non-interactive apply mode: merged_config
    deliberately erases provenance, but the mode's contract is that every
    bypassed prompt logs the decision taken *and its source*, which needs the
    layer back. Re-reads the two config files; both loads are cheap and
    already validated fatal-on-malformed by the time any caller here runs.
    """
    p = load_config(repo)
    g = load_global_config()
    p_apply = p.get("apply") if isinstance(p.get("apply"), dict) else {}
    g_apply = g.get("apply") if isinstance(g.get("apply"), dict) else {}
    if key in p_apply:
        return "project"
    if key in g_apply:
        return "global"
    return None


def _staging_section(cfg: dict) -> dict:
    """Return cfg's [staging] table as a dict, failing on a non-table shape.

    Shared strict reader for the two [staging] accessors below, matching
    the [apply] readers' posture: a hand-edited misshape is fatal, never a
    silent fallback to defaults — a typo must not silently flip the
    staging strategy back to the default the user thought they'd left.
    """
    from __main__ import fail

    staging_section = cfg.get("staging")
    if staging_section is None:
        return {}
    if not isinstance(staging_section, dict):
        fail(f"{BALE_CONFIG}: [staging] must be a table, "
             f"got {type(staging_section).__name__}")
    return staging_section


def get_staging_strategy(cfg: dict) -> str:
    """Return [staging].strategy from the merged config; absent → the
    "working-tree" default (byte-identical to the historical staging
    behavior, BALE.md §8.3 step 2).

    Empty string reads as unset (the wizard's suppress form at the
    project layer — collapse to the default, overriding any inherited
    global value). Any other value must be one of STAGING_STRATEGIES;
    a typo is fatal, not a silent fallback — the whole point of the
    opt-in is that the user knows which content validation exercised.
    """
    from __main__ import fail

    raw = _staging_section(cfg).get("strategy")
    if raw is None:
        return "working-tree"
    if not isinstance(raw, str):
        fail(f"{BALE_CONFIG}: staging.strategy must be a string, "
             f"got {type(raw).__name__}")
    val = raw.strip()
    if not val:
        return "working-tree"
    if val not in STAGING_STRATEGIES:
        fail(f"{BALE_CONFIG}: staging.strategy must be one of "
             f"{', '.join(repr(s) for s in STAGING_STRATEGIES)}; "
             f"got {val!r}")
    return val


def get_staging_untracked_inputs(cfg: dict) -> list[str]:
    """Return [staging].untracked_inputs from the merged config; absent or
    empty → [].

    Strict shape check, same posture as get_apply_search_paths: the list
    must be strings, and a blank entry is fatal rather than dropped — a
    declared input that silently disappears is exactly the silent skip
    the declaration mechanism exists to prevent. Unlike search_paths, no
    tilde or env-var expansion: entries are repo-relative literals
    resolved against the repo at stage time (bale_staging validates
    path safety, existence, and untracked-at-target there).
    """
    from __main__ import fail

    raw = _staging_section(cfg).get("untracked_inputs")
    if raw is None:
        return []
    if not isinstance(raw, list):
        fail(f"{BALE_CONFIG}: staging.untracked_inputs must be an array "
             f"of strings, got {type(raw).__name__}")
    out: list[str] = []
    for i, entry in enumerate(raw):
        if not isinstance(entry, str):
            fail(f"{BALE_CONFIG}: staging.untracked_inputs[{i}] must be a "
                 f"string, got {type(entry).__name__}")
        s = entry.strip()
        if not s:
            fail(f"{BALE_CONFIG}: staging.untracked_inputs[{i}] is empty; "
                 f"remove the entry or name a repo-relative path")
        out.append(s)
    return out


def get_identity_packer(cfg: dict) -> Optional[str]:
    """Return [identity].packer from the merged config, or None if unset.

    Consumed by `bale pack` / `bale handoff` when stamping the request
    manifest's provenance block (v0.3.8): the flag > project > global
    precedence puts this accessor behind the --packer flag. Empty string
    reads as unset (the wizard's suppress form at the project layer —
    overriding an inherited global value with "no configured identity").
    A non-string shape is fatal, matching the [apply]/[staging] readers'
    posture: a typo must not silently mis-attribute every pack from this
    repo — provenance the packer thought was configured has to be either
    right or loud.
    """
    from __main__ import fail

    identity_section = cfg.get("identity")
    if identity_section is None:
        return None
    if not isinstance(identity_section, dict):
        fail(f"{BALE_CONFIG}: [identity] must be a table, "
             f"got {type(identity_section).__name__}")
    raw = identity_section.get("packer")
    if raw is None:
        return None
    if not isinstance(raw, str):
        fail(f"{BALE_CONFIG}: identity.packer must be a string, "
             f"got {type(raw).__name__}")
    val = raw.strip()
    return val or None


# ---------------------------------------------------------------------------
# 3. `bale config init` wizard
# ---------------------------------------------------------------------------
#
# The canonical way to opt in to bale's configurables mechanism. Walks every
# configurable bale knows about; runs against either the project layer
# (`<repo>/bale.toml`, default) or the global layer (`<install>/user/bale.toml`,
# via `--global`). Both modes use the same walk_configurables() function —
# the layer differs only in destination file, header text, whether git
# identity is walked, and whether inherited (global → project) values are
# displayed.
#
# Idempotent at both layers: re-running shows current values and lets the
# user re-confirm, change, or clear each one. The wizard is the single source
# of truth for the discoverable surface — a configurable bale invokes but
# the wizard doesn't walk is a contract violation.

def _prompt_value(label: str, *, current: Optional[str],
                  inherited: Optional[str] = None,
                  description: list[str]) -> Optional[str]:
    """Generic value-prompt for the wizard.

    Three states the wizard recognizes at this layer:
      - None       — key absent at this layer. Means "inherit" if a lower
                     layer has a value; "no value at all" otherwise.
      - ""         — key present, empty. Explicit suppression: at the project
                     layer this overrides any inherited global value with "no
                     hook runs"; at the global layer it's redundant with
                     absence (no lower layer to suppress) but harmless.
      - "value"    — key set to a value.

    Input semantics:
      - Enter (empty input) → keep current (returns whatever was passed in,
        including None or "").
      - '-'                 → return None (clear at this layer).
      - 'x'                 → return "" (explicit suppress). Only offered when
                              `inherited` is set; otherwise treated as a typo
                              and rejected with a hint.
      - any other text      → return that text (set value).
      - EOF/^C              → keep current (safer than clearing).

    Display shows current AND inherited AND the effective value the merge
    would produce, so the user sees at a glance what they're about to keep,
    change, or override.
    """
    print(f"[{label}]")
    for line in description:
        print(f"  {line}")

    # Display current state at this layer.
    if current is None:
        print(f"  current at this layer: (unset)")
    elif current == "":
        print(f"  current at this layer: (suppressed — no hook runs at this layer)")
    else:
        print(f"  current at this layer: {current}")

    # Display inherited (only present when this is the project layer and the
    # global layer has a value).
    if inherited:
        print(f"  inherited from global: {inherited}")

    # Effective value the merge would produce given current state.
    if current is None:
        effective = inherited
    elif current == "":
        effective = None
    else:
        effective = current
    if effective:
        print(f"  effective: {effective}")
    else:
        print(f"  effective: (no hook will run)")

    # Prompt instructions. Suppress option only appears when there's something
    # to suppress; that keeps the wording minimal in the common case (global
    # walk, or project walk with no inherited value).
    print(f"  Enter to keep. Type a value to set. Type '-' to clear (unset at this layer).")
    if inherited:
        print(f"  Type 'x' to suppress (write empty string — no hook regardless of inherited).")

    try:
        raw = input(f"  > ")
    except (EOFError, KeyboardInterrupt):
        print()
        return current
    val = raw.strip()
    if val == "":
        return current
    if val == "-":
        return None
    if val == "x":
        if inherited:
            return ""
        # No inherited value to suppress — 'x' is meaningless here. Don't
        # silently treat it as a literal value (the user almost certainly
        # meant the suppress sigil). Ask again would mean recursing; the
        # cheaper move is to keep current and surface the mistake.
        print(f"  '{val}' is the suppression sigil, only meaningful when a global "
              f"value is inherited. No global value is set for this key; keeping current.")
        return current
    return val


def _prompt_bool(label: str, *, current: Optional[bool],
                 inherited: Optional[bool] = None,
                 description: list[str]) -> Optional[bool]:
    """Boolean prompt for the wizard, mirroring `_prompt_value` semantics.

    States at this layer:
      - None  — key absent. Inherit if a lower layer sets it; unset otherwise.
      - True / False — key set.

    No 'x' suppress sigil: booleans have no empty form, and an explicit
    `false` at the project layer already overrides an inherited `true`
    (per-key replacement). The prompt says so when an inherited value shows.

    Input semantics:
      - Enter               → keep current (None/True/False as passed in).
      - true/t/yes/y/1      → True.
      - false/f/no/n/0      → False.
      - '-'                 → None (clear at this layer).
      - anything else       → keep current, with a hint.
      - EOF/^C              → keep current (safer than clearing).
    """
    def _show(v: Optional[bool]) -> str:
        return "(unset)" if v is None else ("true" if v else "false")

    print(f"[{label}]")
    for line in description:
        print(f"  {line}")

    print(f"  current at this layer: {_show(current)}")
    if inherited is not None:
        print(f"  inherited from global: {_show(inherited)}")

    effective = current if current is not None else inherited
    print(f"  effective: {'(unset — off)' if effective is None else _show(effective)}")

    print(f"  Enter to keep. Type true or false to set. Type '-' to clear "
          f"(unset at this layer).")
    if inherited is not None:
        print(f"  (No 'x' sigil for booleans — an explicit 'false' here already "
              f"overrides the inherited value.)")

    try:
        raw = input(f"  > ")
    except (EOFError, KeyboardInterrupt):
        print()
        return current
    val = raw.strip().lower()
    if val == "":
        return current
    if val == "-":
        return None
    if val in ("true", "t", "yes", "y", "1"):
        return True
    if val in ("false", "f", "no", "n", "0"):
        return False
    print(f"  '{raw.strip()}' is not a boolean; expected true/false (or Enter "
          f"to keep, '-' to clear). Keeping current.")
    return current


def _prompt_path_list(label: str, *, current: Optional[list[str]],
                      inherited: Optional[list[str]] = None,
                      description: list[str]) -> Optional[list[str]]:
    """List-of-paths prompt for the wizard, mirroring `_prompt_value` semantics.

    Three states at this layer:
      - None        — key absent.
      - []          — key present, empty list. Explicit suppression (the
                      accessor returns [], no extra search paths).
      - [x, y, ...] — value set.

    Input semantics:
      - Enter (empty input)                  → keep current.
      - '-'                                  → return None (clear).
      - 'x'                                  → return [] (explicit suppress).
                                               Only offered when `inherited`
                                               is non-empty.
      - colon-separated paths                → return parsed list (empties
                                               dropped — stray colons in input
                                               shouldn't introduce ""-entries).
      - EOF/^C                               → keep current.

    The display format prefers one path per line — colon-joined lists are
    unreadable at length. This is the canonical wizard interface for list-
    shaped configurables; future list-shaped configurables should reuse this.
    """
    print(f"[{label}]")
    for line in description:
        print(f"  {line}")

    # Display current at this layer.
    if current is None:
        print(f"  current at this layer: (unset)")
    elif current == []:
        print(f"  current at this layer: (suppressed — empty list)")
    else:
        print(f"  current at this layer:")
        for p in current:
            print(f"    {p}")

    # Display inherited.
    if inherited:
        print(f"  inherited from global:")
        for p in inherited:
            print(f"    {p}")

    # Effective.
    if current is None:
        effective = inherited
    elif current == []:
        effective = None
    else:
        effective = current
    if effective:
        print(f"  effective:")
        for p in effective:
            print(f"    {p}")
    else:
        print(f"  effective: (no extra search paths)")

    print(f"  Enter to keep. Type colon-separated paths to set. Type '-' to clear.")
    if inherited:
        print(f"  Type 'x' to suppress (write empty list — overrides inherited).")

    try:
        raw = input(f"  > ")
    except (EOFError, KeyboardInterrupt):
        print()
        return current
    val = raw.strip()
    if val == "":
        return current
    if val == "-":
        return None
    if val == "x":
        if inherited:
            return []
        print(f"  '{val}' is the suppression sigil, only meaningful when a global "
              f"value is inherited. No global value is set for this key; keeping current.")
        return current
    # Drop empties — stray colons in input shouldn't introduce ""-entries
    # that then survive into bale.toml.
    parts = [p.strip() for p in val.split(":")]
    parts = [p for p in parts if p]
    return parts or None


def walkthrough_git_identity(repo: Path) -> None:
    """Per constraint: check git user.name and user.email; if either is
    unset, prompt and write to the repo-local git config (never --global).

    Idempotent: already-set values (from any scope, repo-local or global)
    are reported and left alone. The constraint says "if unset, prompt
    and write to local" — already-set anywhere counts as set.
    """
    from __main__ import git

    print()
    print("Git identity (used for commit attribution on bale apply)")
    for key, label in (("user.name", "name"), ("user.email", "email")):
        result = git(["config", "--get", key], cwd=repo, check=False)
        current = result.stdout.strip() if result.returncode == 0 else ""
        if current:
            print(f"  git {key}: {current}  (set)")
            continue
        print(f"  git {key}: (unset)")
        try:
            val = input(f"  enter your {label} (Enter to skip): ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            val = ""
        if val:
            # Repo-local. Never --global per the constraint.
            git(["config", key, val], cwd=repo)
            print(f"  wrote {key} = {val} to repo-local git config")
        else:
            print(f"  skipped; commits during this session may be attributed")
            print(f"  to a fallback identity until {key} is set.")


def walk_configurables(existing: dict, *, layer: str,
                       inherited: Optional[dict] = None) -> dict:
    """Walk every configurable; return the new dict for the layer being edited.

    `existing` is the current contents of the file being written. `layer` is
    "project" or "global". `inherited` is the lower layer (the global config)
    when walking the project layer, or None when walking global (no layer
    below to inherit from).

    The presence of a key in the returned dict, including the empty-string /
    empty-list "suppress" form, determines what render_bale_toml emits.

    Sessions adding new configurables extend this function in the same
    response. The wizard is the discoverable surface; if a configurable isn't
    here, there's no canonical way to opt in to it.
    """
    if layer not in ("project", "global"):
        raise ValueError(f"unknown layer: {layer!r}")
    inherited = inherited or {}

    # Layer-specific phrasing for hook descriptions. The mechanics are the
    # same at both layers; what differs is where paths resolve to and where
    # the file lives.
    if layer == "project":
        path_hint = (
            "Path relative to <repo>/, the repo root. Must be executable.")
    else:
        path_hint = (
            "Path relative to <install>/user/, the global hook-script "
            "directory inside this bale install. Must be executable. "
            "Place the script under <install>/user/scripts/ and reference "
            "it here.")

    new: dict = {}

    # ---- [hooks].post_pack ------------------------------------------------
    existing_hooks = existing.get("hooks") or {}
    inherited_hooks = inherited.get("hooks") or {}

    # current at this layer: None | "" | "value"
    raw_cur = existing_hooks.get("post_pack")
    current = raw_cur if isinstance(raw_cur, str) else None

    # inherited (only meaningful in project layer): None | "value"
    raw_inh = inherited_hooks.get("post_pack")
    inh = raw_inh.strip() if isinstance(raw_inh, str) and raw_inh.strip() else None

    val = _prompt_value(
        "hooks.post_pack",
        current=current,
        inherited=inh,
        description=[
            "Optional. Enter to skip; you can wire one up later.",
            "Script invoked after `bale pack` successfully writes the",
            "request tarball and acquires the session lock. Bale prompts",
            "before running it. Use cases: copying the tarball path to",
            "the clipboard, opening the outbox in a file manager,",
            "uploading the tarball somewhere, pinging chat — anything",
            "you'd run on a fresh request landing on disk.",
            path_hint,
        ],
    )
    if val is not None:
        # Includes the explicit-suppress case ("" goes into the dict so the
        # renderer emits `post_pack = ""`).
        new.setdefault("hooks", {})["post_pack"] = val

    # ---- [hooks].post_apply_pass ------------------------------------------
    raw_cur = existing_hooks.get("post_apply_pass")
    current = raw_cur if isinstance(raw_cur, str) else None
    raw_inh = inherited_hooks.get("post_apply_pass")
    inh = raw_inh.strip() if isinstance(raw_inh, str) and raw_inh.strip() else None

    val = _prompt_value(
        "hooks.post_apply_pass",
        current=current,
        inherited=inh,
        description=[
            "Optional. Enter to skip; you can wire one up later.",
            "Script invoked after `bale apply` succeeds (PASS path,",
            "post-merge). Bale prompts before running it. Use cases:",
            "reinstalling bale on bale-src, syncing artifacts, notifying",
            "chat — anything you'd run on commit-and-merge.",
            path_hint,
        ],
    )
    if val is not None:
        new.setdefault("hooks", {})["post_apply_pass"] = val

    # ---- [apply].search_paths ---------------------------------------------
    # Read both layers defensively — if a file was hand-edited into a
    # misshapen state, we don't want to crash the wizard before it can
    # rewrite the file. The strict typed accessor (get_apply_search_paths)
    # is used at apply time; the wizard reads raw and tolerates oddness.
    def _coerce_path_list(raw) -> Optional[list[str]]:
        if not isinstance(raw, list):
            return None
        if not all(isinstance(p, str) for p in raw):
            return None
        clean = [p for p in raw if p]
        # Distinguish "key present with empty list" (suppress) from "key
        # absent." If raw was [] originally, return [] — keep the suppress
        # form. If raw was non-empty but all entries were filtered to empty,
        # treat as None (no usable content) so the wizard can re-prompt.
        if not raw:
            return []
        return clean if clean else None

    existing_apply = existing.get("apply") if isinstance(existing.get("apply"), dict) else {}
    inherited_apply = inherited.get("apply") if isinstance(inherited.get("apply"), dict) else {}

    raw_cur_list = existing_apply.get("search_paths") if "search_paths" in existing_apply else None
    current_list = _coerce_path_list(raw_cur_list) if raw_cur_list is not None else None

    raw_inh_list = inherited_apply.get("search_paths") if "search_paths" in inherited_apply else None
    inh_list = _coerce_path_list(raw_inh_list) if raw_inh_list is not None else None
    # Drop empty inherited (an empty list inherited from global isn't a usable
    # default to show).
    if inh_list == []:
        inh_list = None

    val_list = _prompt_path_list(
        "apply.search_paths",
        current=current_list,
        inherited=inh_list,
        description=[
            "Optional. Enter to skip; you can wire one up later.",
            "Directories bale searches when a command is given a relative",
            "inbound-file name: the tarball for `bale apply` / `bale",
            "retry` / `bale handoff`, and the prose file for `bale pack",
            "--readme-file`. Tried in order; first match wins. An",
            "absolute path argument bypasses search. Cwd is always tried",
            "first implicitly — you don't need to list it.",
            "Tilde (~/Downloads) and env vars ($HOME/Downloads) expand at",
            "use time, so the committed file stays portable across machines.",
            "Use case: worker files land in ~/Downloads; with ~/Downloads",
            "here, `bale apply request-NNN.tar.gz` and `bale pack ...",
            "--readme-file brief.md` both work from anywhere in the repo.",
        ],
    )
    if val_list is not None:
        # Both the value-set case and the empty-list (suppress) case go in;
        # the renderer emits search_paths = [...] either way.
        new.setdefault("apply", {})["search_paths"] = val_list

    # ---- [apply].no_interact -----------------------------------------------
    # Bool keys read defensively like the list above: a hand-edited
    # non-boolean shows as "unset" here rather than crashing the wizard; the
    # strict typed accessor is what apply-time reads go through.
    raw_cur_b = existing_apply.get("no_interact")
    current_b = raw_cur_b if isinstance(raw_cur_b, bool) else None
    raw_inh_b = inherited_apply.get("no_interact")
    inh_b = raw_inh_b if isinstance(raw_inh_b, bool) else None

    val_b = _prompt_bool(
        "apply.no_interact",
        current=current_b,
        inherited=inh_b,
        description=[
            "Optional. Enter to skip.",
            "true = `bale apply` and `bale retry` run non-interactively",
            "by default: the walkthrough takes its default action (merge",
            "on PASS; hold for inspection on HOLD) and the pre-hook",
            "confirmation is decided by apply.hook_auto_accept below.",
            "Every bypassed prompt logs the decision taken and its source.",
            "Same effect as passing --no-interact per invocation.",
            "false/unset = prompt normally (false also overrides an",
            "inherited true).",
        ],
    )
    if val_b is not None:
        new.setdefault("apply", {})["no_interact"] = val_b

    # ---- [apply].hook_auto_accept ------------------------------------------
    raw_cur_b = existing_apply.get("hook_auto_accept")
    current_b = raw_cur_b if isinstance(raw_cur_b, bool) else None
    raw_inh_b = inherited_apply.get("hook_auto_accept")
    inh_b = raw_inh_b if isinstance(raw_inh_b, bool) else None

    val_b = _prompt_bool(
        "apply.hook_auto_accept",
        current=current_b,
        inherited=inh_b,
        description=[
            "Optional. Enter to skip.",
            "Consulted only in non-interactive mode (--no-interact or",
            "apply.no_interact = true). true = hooks run without their",
            "confirmation prompt; false/unset = hooks are declined,",
            "matching the interactive prompt's decline default. Interactive",
            "runs always prompt regardless. The decision and its source",
            "are logged either way. Only opt in if you trust every hook",
            "wired in bale.toml — the per-run prompt is the safety net",
            "this trades away.",
        ],
    )
    if val_b is not None:
        new.setdefault("apply", {})["hook_auto_accept"] = val_b

    # ---- [staging].strategy -------------------------------------------------
    # A string enum rather than a free value; _prompt_value is generic, so
    # the enum check runs after the prompt, keeping current on an invalid
    # entry with a hint (the same reject-with-hint posture _prompt_bool
    # takes for a non-boolean).
    existing_staging = existing.get("staging") if isinstance(existing.get("staging"), dict) else {}
    inherited_staging = inherited.get("staging") if isinstance(inherited.get("staging"), dict) else {}

    raw_cur = existing_staging.get("strategy")
    current = raw_cur if isinstance(raw_cur, str) else None
    raw_inh = inherited_staging.get("strategy")
    inh = raw_inh.strip() if isinstance(raw_inh, str) and raw_inh.strip() else None

    val = _prompt_value(
        "staging.strategy",
        current=current,
        inherited=inh,
        description=[
            "Optional. Enter to skip (default: working-tree).",
            "How `bale apply` builds the staging tree validation.sh runs",
            "in (BALE.md 8.3). 'working-tree' (default) copies the",
            "checkout as-is — untracked state rides in for free, but if",
            "the checkout has diverged from the session's target branch,",
            "validation exercises the checkout's content, not what the",
            "commit lands. 'target-base' materializes the target tip's",
            "tree plus the declared staging.untracked_inputs below, so",
            "validation exercises exactly the content the commit lands.",
        ],
    )
    if val not in (None, "") and val.strip() not in STAGING_STRATEGIES:
        print(f"  '{val}' is not a staging strategy; expected one of: "
              f"{', '.join(STAGING_STRATEGIES)}. Keeping current.")
        val = current
    if val is not None:
        new.setdefault("staging", {})["strategy"] = val

    # ---- [staging].untracked_inputs ------------------------------------------
    raw_cur_list = existing_staging.get("untracked_inputs") if "untracked_inputs" in existing_staging else None
    current_list = _coerce_path_list(raw_cur_list) if raw_cur_list is not None else None

    raw_inh_list = inherited_staging.get("untracked_inputs") if "untracked_inputs" in inherited_staging else None
    inh_list = _coerce_path_list(raw_inh_list) if raw_inh_list is not None else None
    if inh_list == []:
        inh_list = None

    val_list = _prompt_path_list(
        "staging.untracked_inputs",
        current=current_list,
        inherited=inh_list,
        description=[
            "Optional. Enter to skip. Only used when staging.strategy is",
            "'target-base'. Repo-relative paths (files or directories, no",
            "globs) of UNTRACKED build or dependency state that must ride",
            "into staging for validation to run — e.g. .venv or",
            "node_modules. Each entry must exist in the working tree and",
            "be untracked on the session's target branch at apply time;",
            "a missing or tracked entry fails the apply loudly rather",
            "than being skipped.",
        ],
    )
    if val_list is not None:
        new.setdefault("staging", {})["untracked_inputs"] = val_list

    # ---- [identity].packer ---------------------------------------------------
    # Same _prompt_value mechanics as the hook keys: string value, ""
    # suppress form when a global value is inherited. Walked at both
    # layers (identity is meaningful install-wide AND per-repo), and
    # renderer-preserved: a re-run of the wizard shows the current value
    # and keeps it on Enter — the [staging] precedent, applied so
    # `bale config init` re-runs never drop a set-once identity.
    existing_identity = existing.get("identity") if isinstance(existing.get("identity"), dict) else {}
    inherited_identity = inherited.get("identity") if isinstance(inherited.get("identity"), dict) else {}

    raw_cur = existing_identity.get("packer")
    current = raw_cur if isinstance(raw_cur, str) else None
    raw_inh = inherited_identity.get("packer")
    inh = raw_inh.strip() if isinstance(raw_inh, str) and raw_inh.strip() else None

    val = _prompt_value(
        "identity.packer",
        current=current,
        inherited=inh,
        description=[
            "Optional. Enter to skip; you can set it later.",
            "Who authors packs here. Stamped into every request",
            "manifest's provenance block (provenance.packer) so",
            "longitudinal telemetry can attribute requests. A --packer",
            "flag on `bale pack` overrides per invocation (flag >",
            "project > global). Unset everywhere = requests stamp",
            "'unconfigured' and pack logs a hint.",
        ],
    )
    if val is not None:
        new.setdefault("identity", {})["packer"] = val

    return new


# The wizard is canonical, so the generated file points back at it rather
# than duplicating per-key descriptions. Hand-edits work but the wizard
# doesn't preserve unknown keys on re-run; document that here. Two headers
# because the layer is part of the file's identity: someone opening the
# global file should immediately know it isn't the project file.
_PROJECT_TOML_HEADER = """\
# bale.toml — per-repo configurables for this bale-managed project.
# Committed and team-shared. Layered ON TOP OF the global config at
# <install>/user/bale.toml: keys set here override globals per-key.
# Absent file or absent key = silent skip at this layer (and fall back to
# global if it sets the key).
#
# Run `bale config init` to set up, review, or change. The wizard is
# the canonical interface; hand-edits work but the wizard knows only
# about the configurables it walks through. Re-running the wizard
# rewrites this file from its walked surface, so any unrecognized
# keys you hand-edited in will be dropped. At v0.0.x there are no
# escape hatches for this — set/get/edit subcommands land later.
"""

_GLOBAL_TOML_HEADER = """\
# bale.toml — global (per-install) configurables for this bale install.
# Lives at <install>/user/bale.toml; sibling project files at
# <repo>/bale.toml override these per-key. User-owned, never in the
# release tarball — survives `upgrade.sh` and stays portable as a unit
# with the rest of the install.
#
# Run `bale config init --global` to set up, review, or change. The
# wizard is the canonical interface; hand-edits work but the wizard
# knows only about the configurables it walks through. Re-running
# rewrites this file from its walked surface, so unrecognized keys
# you hand-edited will be dropped.
#
# Hook paths in this file resolve relative to <install>/user/ (typically
# place scripts under <install>/user/scripts/).
"""


def render_bale_toml(cfg: dict, *, layer: str = "project") -> str:
    """Render the wizard's config dict into a TOML file body.

    `layer` controls the header comment ("project" or "global"). Both layers
    share the same TOML schema; the header is the only difference.

    Only emits sections the user opted in to. Sections with no set keys are
    omitted — an empty [hooks] block would be noise. Keys whose value is the
    empty string (or empty list for list-shaped keys) ARE emitted, because
    those carry meaning: `post_pack = ""` is an explicit-suppress at the
    project layer.

    New hooks (or new top-level sections in future sessions) get a branch here.
    """
    if layer == "project":
        header = _PROJECT_TOML_HEADER
    elif layer == "global":
        header = _GLOBAL_TOML_HEADER
    else:
        raise ValueError(f"unknown layer: {layer!r}")

    parts = [header]
    hooks = cfg.get("hooks") or {}
    if hooks:
        parts.append("[hooks]")
        for key in HOOK_NAMES:
            if key in hooks:
                v = hooks[key]
                # All current hook values are strings (possibly empty for
                # the explicit-suppress case). When future hooks introduce
                # non-string scalars, add a branch here.
                parts.append(f"{key} = {json.dumps(v)}")
        parts.append("")

    # [apply] section. Currently just search_paths; future value-shaped
    # configurables under [apply] each get their own branch here (and a
    # walk_configurables block, and a typed accessor — the trio scales).
    apply_section = cfg.get("apply") or {}
    if apply_section:
        parts.append("[apply]")
        if "search_paths" in apply_section:
            paths = apply_section["search_paths"]
            # Emit as a TOML array literal. json.dumps produces a valid TOML
            # array of strings for the list-of-strings case (the only one
            # we currently support, including the empty-list suppress form).
            # Persisted literally — no expansion at write time, so the
            # committed file is portable across machines.
            rendered_array = "[" + ", ".join(json.dumps(p) for p in paths) + "]"
            parts.append(f"search_paths = {rendered_array}")
        # Bool keys, in APPLY_VALUES order. json.dumps(True) == "true" — a
        # valid TOML boolean literal, so the same serializer covers them.
        for key in ("no_interact", "hook_auto_accept"):
            if key in apply_section:
                parts.append(f"{key} = {json.dumps(apply_section[key])}")
        parts.append("")

    # [staging] section (BALE.md §8.3 step 2). Same serialization shapes
    # the [apply] section already covers: json.dumps for the string
    # scalar (including the empty-string suppress form), the TOML-array
    # rendering for the path list (including the empty-list suppress
    # form). Emitted in STAGING_VALUES order.
    staging_section = cfg.get("staging") or {}
    if staging_section:
        parts.append("[staging]")
        if "strategy" in staging_section:
            parts.append(f"strategy = {json.dumps(staging_section['strategy'])}")
        if "untracked_inputs" in staging_section:
            inputs = staging_section["untracked_inputs"]
            rendered_array = "[" + ", ".join(json.dumps(p) for p in inputs) + "]"
            parts.append(f"untracked_inputs = {rendered_array}")
        parts.append("")

    # [identity] section (v0.3.8, pack-time provenance). Single string
    # key; json.dumps covers it, including the empty-string suppress
    # form. Emitted in IDENTITY_VALUES order. Renderer-preserved by
    # construction: walk_configurables carries the existing value
    # through on Enter, so a re-run never drops a set-once identity —
    # the [staging] precedent.
    identity_section = cfg.get("identity") or {}
    if identity_section:
        parts.append("[identity]")
        for key in IDENTITY_VALUES:
            if key in identity_section:
                parts.append(f"{key} = {json.dumps(identity_section[key])}")
        parts.append("")

    return "\n".join(parts)


def walkthrough_baleignore(repo: Path) -> None:
    """Walk the user through `<repo>/.baleignore` — the user-managed
    exclusion file the pack/apply pipelines read at BALE.md §6.4 / §11
    rule 14. Project-mode only; called from _cmd_config_init_project
    after the bale.toml is written.

    The walk has three phases, each idempotent:

      1. If a `.baleignore` exists, walk its lines one at a time and
         ask "keep this pattern?" — default is keep (Enter).
      2. Prompt for additions, one per line, blank to finish.
      3. Write the file (or remove it, if the keep+add net is empty).

    The file format: one pattern per line, blank lines and `#`-comments
    permitted. The walk preserves user-authored comments by passing them
    through verbatim in phase 1 (we show them inline, but don't ask
    keep/remove — they're orientation for the patterns near them, and
    asking the user 'keep this comment?' for every comment would be
    noise). New patterns from phase 2 don't get auto-comments; the user
    is the canonical author of comments in this file.

    Syntax explanation is inline at the top of phase 2 so the user
    doesn't need to read BALE.md §6.4 to fill in a pattern. The phrasing
    matches what bin/bale's BaleignoreMatcher actually does — a single
    place where the supported subset is described to the user.

    The function does not import bale (or its matcher) — keeps this
    module's circular-import surface minimal, and any pattern the user
    types here will be validated when pack/apply next loads the file.
    The cost of late validation is an error message at pack time
    instead of inline; the cost of a typo here is one re-run of
    `bale config init`, which is acceptable.
    """
    from __main__ import log

    BALEIGNORE = ".baleignore"
    path = repo / BALEIGNORE

    print()
    print(".baleignore — files and patterns to exclude from request tarballs")
    print(f"  file: {path}")
    print(f"  applies on top of bale's baked-in exclusions and your .gitignore.")
    print(f"  Claude reads this file when packing, and apply rejects a")
    print(f"  response whose changes touch a matched path (BALE.md §11 rule 14).")

    existing_lines: list[str] = []
    if path.is_file():
        try:
            existing_lines = path.read_text(encoding="utf-8").splitlines()
        except OSError as e:
            print(f"  could not read {path}: {e} — skipping .baleignore step.")
            return
        print(f"  (existing file; walk each pattern to keep or remove,")
        print(f"  then add more if you like.)")
    else:
        print(f"  (no file yet; pressing Enter through skips creation.)")

    # Phase 1: walk existing lines. Comments and blanks pass through
    # verbatim; pattern lines get a y/n. EOF/^C at any prompt is
    # interpreted as "keep" (consistent with the wizard's general bias
    # toward preservation on accidental aborts — the file is rewritten
    # only after the user finishes the walk).
    kept_lines: list[str] = []
    for line in existing_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            # Pass through verbatim — these are the user's comments and
            # spacing, not patterns we walk.
            kept_lines.append(line)
            continue
        print()
        print(f"  pattern: {stripped}")
        try:
            raw = input(f"  keep this pattern? [Y/n] ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print()
            raw = ""
        if raw in ("n", "no"):
            # Drop this line. Adjacent comment lines are preserved
            # above; the user may want to clean them up next run.
            continue
        kept_lines.append(line)

    # Phase 2: prompt for additions. Show a brief syntax reminder so the
    # user doesn't need to read the spec.
    print()
    print("  Add new patterns? (one per line, blank to finish)")
    print("  Syntax (subset of gitignore):")
    print("    data/         — directory named 'data' anywhere")
    print("    /build/       — directory named 'build' at repo root only")
    print("    *.parquet     — files ending in .parquet, any depth")
    print("    src/legacy/   — that exact dir and everything under it")
    print("    src/legacy/*.vue — .vue files directly in src/legacy/")
    print("  Patterns starting with '!' (negation) are not supported.")
    added: list[str] = []
    while True:
        try:
            raw = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not raw:
            break
        if raw.startswith("!"):
            print(f"  (negation patterns aren't supported; skipping {raw!r})")
            continue
        added.append(raw)

    # Compose the new file body. If the user dropped every existing
    # pattern AND added nothing, remove the file rather than write a
    # noisy "all-comment" leftover. If only comments survived in the
    # kept-from-existing set and the user added nothing, also remove —
    # comments without patterns aren't load-bearing and a missing file
    # is the canonical "no .baleignore" state.
    new_pattern_lines = [
        ln for ln in kept_lines
        if ln.strip() and not ln.strip().startswith("#")
    ] + added
    if not new_pattern_lines:
        if path.is_file():
            try:
                path.unlink()
                log(f"removed {path} (no patterns kept or added)")
                print(f"  removed {BALEIGNORE} — no patterns active.")
            except OSError as e:
                # Surface the failure but don't abort the wizard — the
                # bale.toml has already been written by this point.
                print(f"  could not remove {path}: {e}")
        else:
            print(f"  no .baleignore created — no patterns to write.")
        return

    # Write the file. Compose by stitching together the kept lines (in
    # original order, comments and patterns intermingled) and then the
    # additions at the end. A trailing newline is appended so the file
    # is a clean text file rather than missing-newline-EOF.
    body_lines: list[str] = list(kept_lines)
    if added:
        # Visually separate user-added patterns from any existing block,
        # but only if the existing content didn't end with a blank line
        # already. The separator is a single blank line; that's enough
        # to let a future re-run-of-the-wizard recognize the boundary
        # without it being load-bearing for the matcher (blank lines
        # are stripped at parse time).
        if body_lines and body_lines[-1].strip():
            body_lines.append("")
        body_lines.extend(added)

    body = "\n".join(body_lines) + "\n"
    try:
        path.write_text(body, encoding="utf-8")
    except OSError as e:
        # Same not-aborting reasoning as the unlink branch above.
        print(f"  could not write {path}: {e}")
        return

    pattern_count = sum(
        1 for ln in body_lines
        if ln.strip() and not ln.strip().startswith("#")
    )
    log(f"wrote {path} ({pattern_count} pattern(s))")
    print(f"  wrote {BALEIGNORE} ({pattern_count} pattern(s) active).")


def cmd_config_init(args: argparse.Namespace) -> int:
    """Walk the wizard against either the project layer (<repo>/bale.toml) or
    the global layer (<install>/user/bale.toml).

    The wizard walks the same configurables in both modes — that's the
    contract from bale-internals.md §4.1: a single discoverable surface for
    every configurable bale knows about. What differs:

      - Where the file is written.
      - Whether git identity is walked (project only — identity is a per-repo
        concern; bale's global config has nothing to do with git).
      - Whether inherited values are displayed (project mode shows global as
        inherited; global mode has no lower layer).
      - The header comment in the rendered file and the description text in
        a few prompts.
    """
    if getattr(args, "global_layer", False):
        return _cmd_config_init_global()
    return _cmd_config_init_project()


def _cmd_config_init_project() -> int:
    from __main__ import fail, log, refuse_system_dir, repo_root

    cwd = Path.cwd().resolve()
    refuse_system_dir(cwd)

    repo = repo_root(cwd)
    if repo is None:
        fail("not in a git repo. `bale config init` configures bale for one "
             "project at a time, and that project must be a git repo. "
             "`cd` into the project you want to use bale with, then re-run. "
             "(No git repo yet? `git init && git add -A && git commit -m initial`.)"
             "\n\n"
             "If you meant to configure the install-level global config, "
             "use `bale config init --global` instead — that doesn't require "
             "a repo.")
    refuse_system_dir(repo)

    cfg_path = repo / BALE_CONFIG
    existing = load_config(repo)
    inherited = load_global_config()
    is_existing = cfg_path.is_file()

    print()
    print("bale config init (project layer)")
    print("  Canonical setup walkthrough for using bale on this repo.")
    print("  Idempotent — re-run any time to review or change. Everything")
    print("  past git identity is optional; pressing Enter through the rest")
    print("  leaves the repo in a perfectly usable state.")

    walkthrough_git_identity(repo)

    print()
    print("Configurables (project layer)")
    new_cfg = walk_configurables(existing, layer="project", inherited=inherited)

    rendered = render_bale_toml(new_cfg, layer="project")
    cfg_path.write_text(rendered, encoding="utf-8")
    log(f"wrote {cfg_path}")

    # .baleignore walkthrough — project-mode only. The file lives at the
    # repo root and is the user-facing exclusion surface that pack and
    # apply consume (BALE.md §6.4, §11 rule 14). Visibility lives here
    # rather than in bin/bale's pack wizard because `bale config init` is
    # the canonical "set up bale for this project" surface — the user
    # who never runs `bale pack` interactively still configures here.
    walkthrough_baleignore(repo)

    # Key information last: the paths touched, what was written, and how to
    # re-run — the summary sits nearest the prompt (the main-CLI output idiom).
    print()
    print("bale config init — done (project layer)")
    print(f"  repo:    {repo}")
    print(f"  config:  {cfg_path} ({'updated' if is_existing else 'created'})")
    if GLOBAL_CONFIG_PATH.is_file():
        print(f"  global:  {GLOBAL_CONFIG_PATH} (inherited)")
    else:
        print(f"  global:  {GLOBAL_CONFIG_PATH} (not configured)")
    print("  Re-run `bale config init` any time to review or change.")
    return 0


def _cmd_config_init_global() -> int:
    """Configure the global (install-layer) file at <install>/user/bale.toml.

    No git-identity walk: identity is a per-repo concern. No repo lookup:
    global config exists independently of any project; running this from
    outside any git repo is fine. Refuses system dirs out of caution
    (cwd parity with project mode), even though we don't read cwd otherwise.
    """
    from __main__ import log, refuse_system_dir

    cwd = Path.cwd().resolve()
    refuse_system_dir(cwd)

    cfg_path = GLOBAL_CONFIG_PATH
    existing = load_global_config()
    is_existing = cfg_path.is_file()

    # Create the user/ subtree on first write. Idempotent: exist_ok=True.
    # parents=True covers the (theoretical) case where install root exists
    # but user/ has been deleted manually.
    GLOBAL_USER_DIR.mkdir(parents=True, exist_ok=True)

    print()
    print("bale config init --global")
    print("  Configures the install-wide global layer for this bale install.")
    print("  Every project that runs this bale inherits these defaults; each")
    print("  project's own bale.toml can override per-key. Hook scripts")
    print("  referenced here live under <install>/user/scripts/ and are")
    print("  preserved across upgrades (via `upgrade.sh`). Idempotent —")
    print("  re-run any time to review or change.")

    print()
    print("Configurables (global layer)")
    # No inherited layer below global.
    new_cfg = walk_configurables(existing, layer="global", inherited=None)

    rendered = render_bale_toml(new_cfg, layer="global")
    cfg_path.write_text(rendered, encoding="utf-8")
    log(f"wrote {cfg_path}")

    # Key information last (same idiom as project mode): install + config
    # paths, what was written, the scripts dir, and how to re-run.
    print()
    print("bale config init --global — done")
    print(f"  install:      {INSTALL_ROOT}")
    print(f"  config:       {cfg_path} ({'updated' if is_existing else 'created'})")
    print(f"  scripts dir:  {GLOBAL_USER_DIR / 'scripts'} (place global hook scripts here)")
    print("  Re-run `bale config init --global` any time to review or change.")
    return 0
